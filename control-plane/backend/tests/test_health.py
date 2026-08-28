"""Tests for service health endpoints."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api import health as health_module
from app.main import app


def test_health_does_not_depend_on_database(monkeypatch) -> None:
    check_database = AsyncMock(
        side_effect=RuntimeError("database unavailable")
    )
    monkeypatch.setattr(
        health_module.db_session,
        "check_database_connectivity",
        check_database,
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mc-iaas-control-plane",
    }
    check_database.assert_not_awaited()


def test_ready_when_database_is_available(monkeypatch) -> None:
    check_database = AsyncMock(return_value=None)
    monkeypatch.setattr(
        health_module.db_session,
        "check_database_connectivity",
        check_database,
    )

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}
    check_database.assert_awaited_once_with()


def test_ready_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        health_module.db_session,
        "check_database_connectivity",
        AsyncMock(side_effect=RuntimeError("sensitive connection details")),
    )

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
    }
    assert "sensitive" not in response.text
