"""Manual refresh HTTP mapping and application-owned HTTP pool lifecycle."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.nodes import get_node_observation_service
from app.clients.errors import (
    AgentAuthenticationError,
    AgentCredentialUnavailableError,
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
)
from app.core.config import get_settings
from app.main import app
from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability
from app.services.node_observation_service import NodeObservationService
from app.services.node_service import NodeNotFoundError


@pytest.fixture
def api():
    service = AsyncMock(spec=NodeObservationService)
    app.dependency_overrides[get_node_observation_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.pop(get_node_observation_service, None)


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (NodeNotFoundError, 404, "Node not found"),
        (AgentUnavailableError, 503, AgentUnavailableError.message),
        (AgentTimeoutError, 503, AgentTimeoutError.message),
        (AgentCredentialUnavailableError, 503, AgentCredentialUnavailableError.message),
        (AgentAuthenticationError, 502, AgentAuthenticationError.message),
        (AgentResponseError, 502, AgentResponseError.message),
    ],
)
def test_refresh_error_mapping(api, error, status, detail):
    client, service = api
    failure = error()
    # Error text must not become the public detail, even if a caller adds private context.
    failure.args = ("test-secret Authorization Bearer internal details",)
    service.refresh_node.side_effect = failure
    response = client.post(f"/api/v1/nodes/{uuid4()}/refresh")
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_refresh_public_response(api):
    client, service = api
    now = datetime.now(UTC)
    node = ComputeNode(
        id=uuid4(),
        name="test",
        endpoint="https://agent.test",
        credential_ref="private-ref",
        enabled=True,
        reachability=NodeReachability.ONLINE,
        observed_health=NodeHealth.HEALTHY,
        observed_ready=True,
        agent_version="0.1.0",
        max_active_instances=4,
        active_instances=1,
        occupied_runtime_slots=1,
        available_slots=3,
        consecutive_failures=0,
        last_seen_at=now,
        last_observed_at=now,
        created_at=now,
        updated_at=now,
    )
    service.refresh_node.return_value = node
    response = client.post(f"/api/v1/nodes/{node.id}/refresh")
    assert response.status_code == 200
    body = response.json()
    assert body["reachability"] == "online"
    assert body["observed_health"] == "healthy"
    assert body["capacity"]["available_slots"] == 3
    assert "credential_ref" not in body
    assert "private-ref" not in response.text
    service.refresh_node.assert_awaited_once_with(node.id)


def test_refresh_invalid_uuid(api):
    client, service = api
    assert client.post("/api/v1/nodes/invalid/refresh").status_code == 422
    service.refresh_node.assert_not_awaited()


def test_shared_http_client_lifespan_and_timeouts():
    with TestClient(app) as client:
        adapter = app.state.agent_client
        http_client = adapter._http_client
        assert not http_client.is_closed
        assert http_client.timeout.connect == get_settings().agent_connect_timeout
        assert http_client.timeout.read == get_settings().agent_read_timeout
        assert "authorization" not in http_client.headers
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200
        assert app.state.agent_client is adapter
    assert http_client.is_closed
