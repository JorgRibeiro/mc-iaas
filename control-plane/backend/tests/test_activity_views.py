"""Audit filters, projections and read-only API contracts."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import activity
from app.db.session import get_session
from app.main import app
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventResponse
from app.services.event_service import EventService
from app.services.read_service import ReadService, display_state


def test_events_fixed_message_and_hidden_details():
    session = Mock()
    event = EventService(session).emit("operation.failed", instance_id=uuid4())
    session.add.assert_called_once_with(event)
    assert event.message == "Operation failed"
    event.id, event.timestamp, event.details = uuid4(), datetime.now(UTC), {"token": "private"}
    response = EventResponse.model_validate(event).model_dump_json()
    assert "private" not in response
    assert "details" not in response
    with pytest.raises(KeyError):
        EventService(session).emit("arbitrary secret")


async def test_event_filters_and_order():
    session = AsyncMock(spec=AsyncSession)
    session.scalars.return_value = Mock(all=Mock(return_value=[]))
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    assert (
        await EventRepository(session).list(
            level="warning",
            node_id=node_id,
            instance_id=instance_id,
            operation_id=operation_id,
            event_type="operation.uncertain",
            limit=5,
        )
        == []
    )
    query = session.scalars.call_args.args[0].compile(dialect=postgresql.dialect())
    assert "ORDER BY events.timestamp DESC, events.id DESC" in str(query)
    for value in (node_id, instance_id, operation_id, "warning", "operation.uncertain", 5):
        assert value in query.params.values()
    session.commit.assert_not_awaited()


@pytest.mark.parametrize(
    ("status", "kind", "expected"),
    [
        ("pending", "start", "starting"),
        ("in_progress", "stop", "stopping"),
        ("pending", "delete", "deleting"),
        ("uncertain", "restart", "uncertain"),
    ],
)
def test_derived_display(status, kind, expected):
    node = SimpleNamespace(reachability="online", last_seen_at=datetime.now(UTC))
    instance = SimpleNamespace(observed_state="running")
    operation = SimpleNamespace(status=status, type=kind)
    assert display_state(instance, node, operation) == expected
    node.reachability = "offline"
    assert display_state(instance, node, operation) == "unavailable"
    assert instance.observed_state == "running"


@pytest.fixture
def summary(monkeypatch):
    from app.models.compute_node import ComputeNode
    from app.services import read_service as module

    now = datetime.now(UTC)
    nodes = [
        ComputeNode(
            id=uuid4(),
            name=str(i),
            endpoint="http://agent.test",
            enabled=True,
            reachability="online" if i == 0 else "offline",
            observed_health="healthy",
            observed_ready=True,
            max_active_instances=4,
            active_instances=1,
            occupied_runtime_slots=1,
            available_slots=3,
            last_seen_at=now,
            consecutive_failures=0,
            created_at=now,
            updated_at=now,
        )
        for i in range(2)
    ]
    instances = [
        SimpleNamespace(id=uuid4(), compute_node_id=n.id, observed_state="running", last_error=None)
        for n in nodes
    ]
    repository = AsyncMock()
    repository.list_all.return_value = nodes
    monkeypatch.setattr(module, "NodeRepository", Mock(return_value=repository))
    instance_repo = AsyncMock()
    instance_repo.list_all.return_value = instances
    monkeypatch.setattr(module, "InstanceRepository", Mock(return_value=instance_repo))
    session = AsyncMock()
    session.scalars.return_value = Mock(all=Mock(return_value=[]))
    return ReadService(session), nodes


async def test_real_aggregation_and_unknown_capacity(summary):
    service, nodes = summary
    result = await service.summary()
    overview = result["overview"]
    assert overview["total_nodes"] == 2
    assert overview["online_nodes"] == 1
    assert overview["healthy_nodes"] == 2
    assert overview["total_instances"] == overview["running_instances"] == 2
    assert overview["unavailable_instances"] == 1
    assert overview["total_runtime_slots"] == 8
    assert overview["occupied_runtime_slots"] == 2
    assert overview["available_runtime_slots"] == 6
    assert overview["infrastructure_status"] == "degraded"
    assert result["timeseries"] == []
    nodes[0].available_slots = None
    assert (await service.summary())["capacity"]["available_runtime_slots"] is None


async def test_activity_apis(summary, monkeypatch):
    service, _ = summary
    data = await service.summary()
    mock_read = AsyncMock()
    mock_read.summary.return_value = data
    monkeypatch.setattr(activity, "ReadService", Mock(return_value=mock_read))
    repo = AsyncMock()
    repo.list.return_value = []
    monkeypatch.setattr(activity, "EventRepository", Mock(return_value=repo))
    app.dependency_overrides[get_session] = lambda: None
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/overview").json()["total_nodes"] == 2
            response = client.get("/api/v1/monitoring/summary")
            assert response.status_code == 200
            assert response.json()["historical_metrics_available"] is False
            assert client.get("/api/v1/events?limit=5&level=warning").json() == []
            assert client.get("/api/v1/events?limit=501").status_code == 422
            assert client.get("/api/v1/events?node_id=invalid").status_code == 422
    finally:
        app.dependency_overrides.pop(get_session, None)


async def test_live_overview_and_monitoring_aggregate_online_metrics(summary):
    service, nodes = summary
    for i, node in enumerate(nodes):
        node.metrics_observed_at = datetime.now(UTC)
        node.cpu_usage_percent = 10 + 20 * i
        node.memory_used_bytes = 2_000_000_000 * (i + 1)
        node.memory_total_bytes = 8_000_000_000 * (i + 1)
        node.storage_used_bytes = 20_000_000_000 * (i + 1)
        node.storage_total_bytes = 80_000_000_000 * (i + 1)
        node.libvirt_health = True
    data = await service.summary()
    assert data["overview"]["cpu_usage_percent"] == 10
    assert data["overview"]["memory_used_bytes"] == 2_000_000_000
    assert data["overview"]["storage_used_bytes"] == 20_000_000_000
    nodes[1].reachability = "online"
    data = await service.summary()
    assert data["overview"]["cpu_usage_percent"] == 20
    assert data["overview"]["memory_used_bytes"] == 6_000_000_000
    assert data["overview"]["memory_total_bytes"] == 24_000_000_000
    assert data["overview"]["storage_used_bytes"] == 60_000_000_000
    assert data["overview"]["storage_total_bytes"] == 240_000_000_000
    assert data["nodes"][0].metrics.cpu.usage_percent == 10
    assert data["nodes"][0].health.libvirt is True
    assert data["timeseries"] == []
    assert data["historical_metrics_available"] is False


async def test_live_aggregation_null_and_stale(summary):
    from datetime import timedelta

    service, nodes = summary
    data = await service.summary()
    assert data["overview"]["cpu_usage_percent"] is None
    assert data["overview"]["memory_used_bytes"] is None
    assert data["overview"]["storage_total_bytes"] is None
    nodes[0].cpu_usage_percent = 50
    nodes[0].metrics_observed_at = datetime.now(UTC) - timedelta(days=1)
    assert (await service.summary())["overview"]["cpu_usage_percent"] is None
    nodes[0].metrics_observed_at = datetime.now(UTC)
    nodes[0].memory_used_bytes = 100
    assert (await service.summary())["overview"]["memory_used_bytes"] is None
