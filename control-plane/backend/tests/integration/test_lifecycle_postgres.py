"""Opt-in PostgreSQL lifecycle test in a temporary, rolled-back schema.

Run with RUN_POSTGRES_LIFECYCLE_TESTS=1 .venv/bin/python -m pytest tests/integration.
All Agent requests use MockTransport. Existing Nodes/Operations are never selected.
"""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.clients.compute_agent import ComputeAgentClient
from app.db.base import Base
from app.db.session import engine, get_session
from app.main import app
from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability, OperationType
from app.schemas.instance import InstanceCreate
from app.services.instance_service import InstanceService
from app.services.lifecycle_errors import ActiveOperationError, InstanceAlreadyExistsError
from app.workers.operation_runner import OperationRunner

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_LIFECYCLE_TESTS") != "1", reason="opt-in PostgreSQL integration"
)


async def test_durable_lifecycle_and_constraints():
    phase = "normal"
    requests = []

    def agent(request):
        requests.append(request)
        assert request.url.host == "synthetic-agent.test"
        assert request.headers["Authorization"] == "Bearer synthetic-token"
        if phase == "timeout":
            raise httpx.ReadTimeout("private diagnostic", request=request)
        path = request.url.path
        if request.method == "DELETE":
            assert request.url.params["delete_data"] == "false"
            return httpx.Response(
                200, json={"name": "test-vm", "deleted": True, "data_preserved": True}
            )
        state = "running" if path.endswith(("/start", "/restart")) else "stopped"
        return httpx.Response(
            200,
            json={
                "name": "test-vm",
                "state": state,
                "runtime": {"slot": 1, "ip": "10.0.0.1", "external_port": 25565}
                if state == "running"
                else None,
                "generated_password": "discarded-secret",
            },
        )

    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            schema = "lifecycle_test_" + uuid4().hex
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            await connection.run_sync(Base.metadata.create_all)
            sessions = async_sessionmaker(
                bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
            )

            async def session_override():
                async with sessions() as session:
                    yield session

            app.dependency_overrides[get_session] = session_override
            async with sessions() as session:
                now = datetime.now(UTC)
                session.add(
                    ComputeNode(
                        name="synthetic",
                        endpoint="http://synthetic-agent.test",
                        credential_ref="synthetic",
                        enabled=True,
                        reachability=NodeReachability.ONLINE,
                        observed_health=NodeHealth.HEALTHY,
                        observed_ready=True,
                        last_seen_at=now,
                        last_observed_at=now,
                        available_slots=1,
                    )
                )
                await session.commit()
            secrets = Mock()
            secrets.get_agent_token.return_value = "synthetic-token"
            async with httpx.AsyncClient(transport=httpx.MockTransport(agent)) as http:
                runner = OperationRunner(sessions, ComputeAgentClient(http), secrets)
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://control.test"
                ) as client:
                    payload = dict(name="test-vm", vm_username="operator", accept_eula=True)
                    response = await client.post("/api/v1/instances", json=payload)
                    assert response.status_code == 202, response.text
                    instance_id = response.json()["instance_id"]
                    url = "/api/v1/instances/" + instance_id
                    assert not requests  # Queueing never dispatches inline.
                    assert (await client.post(url + "/start")).status_code == 409
                    assert await runner.run_once()
                    saved = (await client.get(url)).json()
                    assert saved["desired_state"] == saved["observed_state"] == "stopped"
                    assert "discarded-secret" not in str(saved)
                    # Duplicate name race, bypassing the preliminary query.
                    async with sessions() as session:
                        service = InstanceService(session)
                        service.repository.get_by_name = AsyncMock(return_value=None)
                        with pytest.raises(InstanceAlreadyExistsError):
                            await service.create(InstanceCreate(**payload))
                    for action, expected in [
                        ("start", "running"),
                        ("stop", "stopped"),
                        ("start", "running"),
                        ("restart", "running"),
                        ("stop", "stopped"),
                    ]:
                        response = await client.post(url + "/" + action)
                        assert response.status_code == 202, response.text
                        if action == "stop":
                            # Active operation UNIQUE race, bypassing both service prechecks.
                            async with sessions() as session:
                                service = InstanceService(session)
                                service.operations.ensure_idle = AsyncMock()
                                from uuid import UUID

                                with pytest.raises(ActiveOperationError):
                                    await service.request(UUID(instance_id), OperationType.STOP)
                        operation_url = "/api/v1/operations/" + response.json()["operation_id"]
                        assert (await client.get(operation_url)).json()["status"] == "pending"
                        await runner.run_once()
                        operation = (await client.get(operation_url)).json()
                        assert operation["status"] == "succeeded", operation
                        assert "operation_metadata" not in operation
                        assert (await client.get(url)).json()["observed_state"] == expected
                    # Ambiguous mutation is durable, blocks further operations and is never retried.
                    phase = "timeout"
                    response = await client.post(url + "/start")
                    await runner.run_once()
                    operation_url = "/api/v1/operations/" + response.json()["operation_id"]
                    assert (await client.get(operation_url)).json()["status"] == "uncertain"
                    assert (await client.post(url + "/stop")).status_code == 409
                    assert not await runner.run_once()
                    # Separate synthetic workload for DELETE, leaving uncertain one untouched.
                    from app.models.instance import Instance

                    async with sessions() as session:
                        removable = Instance(
                            name="removable",
                            compute_node_id=None,
                            minecraft_version="test",
                            observed_state="stopped",
                        )
                        # Reuse placement solely within this isolated test schema.
                        from uuid import UUID

                        original = await session.get(Instance, UUID(instance_id))
                        removable.compute_node_id = original.compute_node_id
                        session.add(removable)
                        await session.commit()
                        remove_id = str(removable.id)
                    phase = "normal"

                    # Agent's result name follows the request for this second workload.
                    def deletion(request):
                        assert request.url.params["delete_data"] == "false"
                        return httpx.Response(
                            200, json={"name": "removable", "deleted": True, "data_preserved": True}
                        )

                    async with httpx.AsyncClient(
                        transport=httpx.MockTransport(deletion)
                    ) as delete_http:
                        runner.client = ComputeAgentClient(delete_http)
                        response = await client.delete("/api/v1/instances/" + remove_id)
                        assert response.status_code == 202
                        await runner.run_once()
                    assert (await client.get("/api/v1/instances/" + remove_id)).status_code == 404
                    listed = (await client.get("/api/v1/instances")).json()
                    assert all(item["id"] != remove_id for item in listed)
                    operations = (
                        await client.get("/api/v1/operations", params={"instance_id": remove_id})
                    ).json()
                    assert operations[0]["status"] == "succeeded"
        finally:
            app.dependency_overrides.pop(get_session, None)
            await transaction.rollback()
    await engine.dispose()
