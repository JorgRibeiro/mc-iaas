"""Durable runner transitions without PostgreSQL or an Agent."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.errors import AgentConflictError, AgentTimeoutError
from app.models.enums import OperationStatus as Status
from app.models.enums import OperationType as Kind
from app.schemas.agent import AgentActionResult, AgentDeleteResult
from app.workers.operation_runner import OperationRunner


@pytest.fixture
def runner(monkeypatch):
    from app.workers import operation_runner as module

    session = AsyncMock(spec=AsyncSession)
    session.__aenter__.return_value = session
    client = AsyncMock()
    secrets = Mock()
    secrets.get_agent_token.return_value = "private-token"
    runner = OperationRunner(Mock(return_value=session), client, secrets)
    now = datetime.now(UTC)
    instance = SimpleNamespace(
        id=uuid4(),
        name="test-vm",
        compute_node_id=uuid4(),
        observed_state="stopped",
        desired_state="running",
        observed_runtime_slot=2,
        observed_runtime_ip="10.0.0.2",
        observed_external_port=25566,
        deleted_at=None,
    )
    node = SimpleNamespace(
        id=instance.compute_node_id,
        enabled=True,
        reachability="online",
        observed_ready=True,
        last_seen_at=now,
        last_observed_at=now,
        available_slots=2,
        endpoint="http://agent.test",
        credential_ref="ref",
    )
    operation = SimpleNamespace(
        id=uuid4(),
        instance_id=instance.id,
        node_id=node.id,
        status=Status.PENDING,
        type=Kind.CREATE,
        attempt_count=0,
        operation_metadata={"name": "test-vm", "vm_username": "operator", "accept_eula": True},
    )
    session.scalar.return_value = operation
    session.get.return_value = operation
    nodes = AsyncMock()
    nodes.get_by_id.return_value = node
    instances = AsyncMock()
    instances.get_by_id.return_value = instance
    monkeypatch.setattr(module, "NodeRepository", Mock(return_value=nodes))
    monkeypatch.setattr(module, "InstanceRepository", Mock(return_value=instances))
    return runner, session, client, operation, instance


@pytest.mark.parametrize(
    ("kind", "state"),
    [
        (Kind.CREATE, "stopped"),
        (Kind.START, "running"),
        (Kind.STOP, "stopped"),
        (Kind.RESTART, "running"),
        (Kind.DELETE, "missing"),
    ],
)
async def test_claim_dispatch_success(runner, kind, state):
    worker, session, client, operation, instance = runner
    operation.type = kind
    if kind in (Kind.RESTART, Kind.STOP):
        instance.observed_state = "running"
    if kind == Kind.DELETE:
        result = AgentDeleteResult(name=instance.name, deleted=True, data_preserved=True)
    else:
        result = AgentActionResult(
            name=instance.name,
            state=state,
            runtime={"slot": 1, "ip": "10.0.0.1", "external_port": 25565},
        )

    async def response(*args):
        assert operation.status == Status.IN_PROGRESS
        assert session.commit.await_count == 1
        return result

    getattr(client, kind.value + "_instance").side_effect = response
    assert await worker.run_once()
    assert operation.status == Status.SUCCEEDED
    assert operation.attempt_count == 1
    assert instance.observed_state.value == state
    assert instance.desired_state == "running"
    assert instance.observed_runtime_slot == (1 if state == "running" else None)
    assert (instance.deleted_at is not None) == (kind == Kind.DELETE)
    query = session.scalar.call_args.args[0].compile(dialect=postgresql.dialect())
    assert "FOR UPDATE SKIP LOCKED" in str(query)
    assert session.commit.await_count == 2


@pytest.mark.parametrize(
    ("error", "status"),
    [(AgentTimeoutError(), Status.UNCERTAIN), (AgentConflictError(), Status.FAILED)],
)
async def test_dispatch_errors_preserve_desired_and_observed(runner, error, status):
    worker, _, client, operation, instance = runner
    client.create_instance.side_effect = error
    await worker.run_once()
    assert operation.status == status
    assert instance.observed_state == "stopped"
    assert instance.desired_state == "running"
    assert "private-token" not in operation.error_message
    client.create_instance.assert_awaited_once()


async def test_interrupted_dispatch_marks_uncertain(runner):
    worker, _, _, operation, _ = runner
    worker.execute = AsyncMock(side_effect=asyncio.CancelledError())
    worker.mark_uncertain = AsyncMock()
    with pytest.raises(asyncio.CancelledError):
        await worker.run_once()
    worker.mark_uncertain.assert_awaited_once_with(operation.id)


async def test_startup_recovers_only_in_progress(runner):
    worker, session, *_ = runner
    await worker.recover_interrupted()
    query = session.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    assert Status.IN_PROGRESS in query.params.values()
    assert Status.UNCERTAIN in query.params.values()
    session.commit.assert_awaited_once()


async def test_runner_stop_does_not_leave_task(runner):
    worker, *_ = runner
    started = asyncio.Event()

    async def blocked():
        started.set()
        await asyncio.Event().wait()

    worker.recover_interrupted = AsyncMock()
    worker.run_once = blocked
    worker.start()
    task = worker._task
    await asyncio.wait_for(started.wait(), 1)
    await asyncio.wait_for(worker.stop(), 1)
    assert task.done()
