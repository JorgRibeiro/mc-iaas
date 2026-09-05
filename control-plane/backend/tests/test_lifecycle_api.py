"""HTTP lifecycle contracts with service fakes; no remote mutations."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import instances as api
from app.db.session import get_session
from app.main import app
from app.services.lifecycle_errors import (
    ActiveOperationError,
    InstanceNotFoundError,
    LifecycleError,
    NoSchedulableNodeError,
)


@pytest.fixture
def client(monkeypatch):
    service = AsyncMock()
    monkeypatch.setattr(api, "InstanceService", lambda session: service)
    app.dependency_overrides[get_session] = lambda: AsyncMock()
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (InstanceNotFoundError, 404),
        (LifecycleError, 409),
        (ActiveOperationError, 409),
        (NoSchedulableNodeError, 503),
    ],
)
def test_lifecycle_error_mapping(client, error, status):
    http, service = client
    service.request.side_effect = error()
    response = http.post(f"/api/v1/instances/{uuid4()}/start")
    assert response.status_code == status
    assert response.json() == {"detail": error.message}


@pytest.mark.parametrize("action", ["create", "start", "stop", "restart", "delete"])
def test_accepted_operation(client, action):
    http, service = client
    operation = SimpleNamespace(id=uuid4(), instance_id=uuid4(), status="pending")
    service.create.return_value = service.request.return_value = operation
    path = "/api/v1/instances"
    if action == "create":
        response = http.post(
            path, json={"name": "test-vm", "vm_username": "operator", "accept_eula": True}
        )
    elif action == "delete":
        response = http.delete(f"{path}/{operation.instance_id}")
    else:
        response = http.post(f"{path}/{operation.instance_id}/{action}")
    assert response.status_code == 202
    assert response.json() == {
        "operation_id": str(operation.id),
        "instance_id": str(operation.instance_id),
        "status": "pending",
    }


def test_invalid_uuid_does_not_dispatch(client):
    http, service = client
    assert http.post("/api/v1/instances/not-a-uuid/start").status_code == 422
    service.request.assert_not_awaited()


def test_operation_not_found():
    session = AsyncMock()
    session.get.return_value = None
    app.dependency_overrides[get_session] = lambda: session
    try:
        with TestClient(app) as client:
            assert client.get(f"/api/v1/operations/{uuid4()}").status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)
