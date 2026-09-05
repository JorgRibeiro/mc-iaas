"""HTTP contracts using service fakes and the real domain-error mapping."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import nodes
from app.db.session import get_session
from app.main import app
from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability
from app.services.node_service import NodeAlreadyExistsError, NodeNotFoundError, NodeService

PAYLOAD = {"name": "JORGE", "endpoint": "http://127.0.0.1:8000", "credential_ref": "private-ref"}


@pytest.fixture
def api(monkeypatch):
    service = AsyncMock(spec=NodeService)
    monkeypatch.setattr(nodes, "NodeService", lambda session: service)
    app.dependency_overrides[get_session] = lambda: None
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def node():
    return ComputeNode(
        id=uuid4(),
        **PAYLOAD,
        enabled=True,
        reachability=NodeReachability.UNKNOWN,
        observed_health=NodeHealth.UNKNOWN,
        consecutive_failures=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("method", "path", "operation", "error", "status"),
    [
        ("get", "/{id}", "get_node", NodeNotFoundError, 404),
        ("patch", "/{id}", "update_node", NodeNotFoundError, 404),
        ("post", "", "create_node", NodeAlreadyExistsError, 409),
        ("patch", "/{id}", "update_node", NodeAlreadyExistsError, 409),
    ],
)
def test_domain_error_mapping(api, method, path, operation, error, status):
    client, service = api
    getattr(service, operation).side_effect = error("sensitive details")
    kwargs = {"json": PAYLOAD} if method in {"post", "patch"} else {}
    response = client.request(method, "/api/v1/nodes" + path.format(id=uuid4()), **kwargs)
    assert response.status_code == status
    assert "sensitive" not in response.text


def test_create_list_get_patch_public_response(api, node):
    client, service = api
    service.create_node.return_value = node
    service.get_node.return_value = node
    service.update_node.return_value = node
    service.list_nodes.return_value = [node]
    created = client.post("/api/v1/nodes", json=PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == str(node.id)
    assert "credential_ref" not in body
    assert "private-ref" not in created.text
    assert body["capacity"] == {
        "max_active_instances": None,
        "active_instances": None,
        "occupied_runtime_slots": None,
        "available_slots": None,
    }
    assert body["reachability"] == body["observed_health"] == "unknown"
    assert body["observed_ready"] is None
    assert body["consecutive_failures"] == 0
    listed = client.get("/api/v1/nodes")
    assert listed.status_code == 200
    assert listed.json() == [body]
    fetched = client.get(f"/api/v1/nodes/{node.id}")
    assert fetched.status_code == 200
    assert fetched.json() == body
    patched = client.patch(f"/api/v1/nodes/{node.id}", json={"enabled": False})
    assert patched.status_code == 200
    assert service.update_node.call_args.args[1].model_dump(exclude_unset=True) == {
        "enabled": False
    }


@pytest.mark.parametrize("method", ["get", "patch"])
def test_invalid_uuid(api, method):
    client, service = api
    kwargs = {"json": {}} if method == "patch" else {}
    assert client.request(method, "/api/v1/nodes/not-a-uuid", **kwargs).status_code == 422
    service.get_node.assert_not_awaited()
    service.update_node.assert_not_awaited()


@pytest.mark.parametrize("method", ["post", "patch"])
def test_observed_fields_rejected_at_http_boundary(api, method):
    client, service = api
    path = "/api/v1/nodes" + (f"/{uuid4()}" if method == "patch" else "")
    response = client.request(method, path, json={**PAYLOAD, "reachability": "online"})
    assert response.status_code == 422
    service.create_node.assert_not_awaited()
    service.update_node.assert_not_awaited()


def test_empty_list_and_no_delete_or_unversioned_nodes(api):
    client, service = api
    service.list_nodes.return_value = []
    assert client.get("/api/v1/nodes").json() == []
    assert client.delete(f"/api/v1/nodes/{uuid4()}").status_code == 405
    assert client.get("/nodes").status_code == 404
    assert client.get("/api/v1/health").status_code == 404
