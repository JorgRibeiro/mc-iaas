"""Deterministic worker tests; no database, real Agent or timing sleeps."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.errors import AgentTimeoutError
from app.repositories.instance_repository import InstanceRepository
from app.repositories.node_repository import NodeRepository
from app.workers import node_poller as worker
from app.workers.node_poller import NodePoller, polling_delay


@pytest.fixture
def polling(monkeypatch):
    session = AsyncMock(spec=AsyncSession)
    session.__aenter__.return_value = session
    sessions = Mock(return_value=session)
    settings = SimpleNamespace(node_poll_interval=10, node_max_backoff=40, node_offline_threshold=3)
    poller = NodePoller(sessions, Mock(), Mock(), settings)
    repo = AsyncMock(spec=NodeRepository)
    monkeypatch.setattr(worker, "NodeRepository", Mock(return_value=repo))
    service = AsyncMock()
    factory = Mock(return_value=service)
    monkeypatch.setattr(worker, "NodeObservationService", factory)
    clock = Mock(return_value=100)
    monkeypatch.setattr(worker, "monotonic", clock)
    return poller, repo, service, factory, clock


async def test_discovery_and_reuse_observation_service(polling):
    poller, repo, service, factory, _ = polling
    node = SimpleNamespace(id=uuid4(), consecutive_failures=0)
    repo.list_enabled.return_value = [node]
    service.refresh_node.return_value = node
    await poller.poll_once()
    repo.list_enabled.assert_awaited_once()
    repo.list_all.assert_not_awaited()
    service.refresh_node.assert_awaited_once_with(node.id, enabled_only=True)
    assert factory.call_args.kwargs == {"offline_threshold": 3}
    assert poller._due[node.id] == 110


async def test_backoff_is_per_node_and_removed_when_disabled(polling):
    poller, repo, service, _, clock = polling
    failed = SimpleNamespace(id=uuid4(), consecutive_failures=3)
    healthy = SimpleNamespace(id=uuid4(), consecutive_failures=0)
    repo.list_enabled.return_value = [failed, healthy]
    repo.get_by_id.return_value = failed
    service.refresh_node.side_effect = [AgentTimeoutError(), healthy]
    await poller.poll_once()
    assert poller._due == {failed.id: 140, healthy.id: 110}
    clock.return_value = 110
    service.refresh_node.side_effect = None
    service.refresh_node.return_value = healthy
    service.refresh_node.reset_mock()
    await poller.poll_once()
    service.refresh_node.assert_awaited_once_with(healthy.id, enabled_only=True)
    repo.list_enabled.return_value = [healthy]
    await poller.poll_once()
    assert failed.id not in poller._due


@pytest.mark.parametrize(
    ("failures", "delay"), [(0, 10), (1, 10), (2, 20), (3, 40), (4, 40), (1000000, 40)]
)
def test_backoff_cap(failures, delay):
    assert polling_delay(10, 40, failures) == delay


async def test_one_node_database_failure_does_not_stop_others(polling, caplog):
    poller, repo, service, _, _ = polling
    first = SimpleNamespace(id=uuid4(), consecutive_failures=0)
    second = SimpleNamespace(id=uuid4(), consecutive_failures=0)
    repo.list_enabled.return_value = [first, second]
    service.refresh_node.side_effect = [RuntimeError("private database url"), second]
    await poller.poll_once()
    assert service.refresh_node.await_count == 2
    assert "private database url" not in caplog.text


async def test_start_stop_cancels_inflight_work_without_leak(polling):
    poller, *_ = polling
    started = asyncio.Event()
    cleaned_up = asyncio.Event()

    async def in_flight():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned_up.set()

    poller.poll_once = in_flight
    poller.start()
    task = poller._task
    poller.start()
    assert poller._task is task
    await asyncio.wait_for(started.wait(), timeout=1)
    await asyncio.wait_for(poller.stop(), timeout=1)
    assert task.done()
    assert cleaned_up.is_set()
    await poller.stop()


async def test_cycle_failure_is_retried(polling, monkeypatch):
    poller, *_ = polling
    retried = asyncio.Event()
    calls = 0

    async def cycle():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("private details")
        retried.set()
        await asyncio.Event().wait()

    async def no_delay(_):
        return None

    poller.poll_once = cycle
    monkeypatch.setattr(worker.asyncio, "sleep", no_delay)
    poller.start()
    await asyncio.wait_for(retried.wait(), timeout=1)
    await poller.stop()
    assert calls == 2


async def test_repository_enabled_filter_and_instance_node_scope():
    session = AsyncMock(spec=AsyncSession)
    session.scalars.return_value = Mock(all=Mock(return_value=[]))
    await NodeRepository(session).list_enabled()
    sql = str(session.scalars.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "WHERE compute_nodes.enabled IS true" in sql
    assert "ORDER BY compute_nodes.name" in sql
    node_id = uuid4()
    await InstanceRepository(session).list_by_node(node_id)
    query = session.scalars.call_args.args[0].compile(dialect=postgresql.dialect())
    assert "WHERE instances.compute_node_id =" in str(query)
    assert node_id in query.params.values()
    session.commit.assert_not_awaited()


def test_lifespan_starts_and_stops_worker(lifespan_poller):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app):
        lifespan_poller.start.assert_called_once()
        lifespan_poller.stop.assert_not_awaited()
    lifespan_poller.stop.assert_awaited_once()
