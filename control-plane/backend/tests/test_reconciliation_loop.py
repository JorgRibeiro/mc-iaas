"""Worker shutdown and startup barrier wiring."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app.workers.reconciliation_loop import ReconciliationLoop


async def test_shutdown_cancels_cleanly():
    loop = ReconciliationLoop(Mock(), SimpleNamespace(reconciliation_interval=1))
    entered = asyncio.Event()

    async def blocked():
        entered.set()
        await asyncio.Event().wait()

    loop.run_once = blocked
    loop.start()
    task = loop._task
    await asyncio.wait_for(entered.wait(), 1)
    await loop.stop()
    assert task.done()


async def test_loop_passes_startup_barrier(monkeypatch):
    from app.workers import reconciliation_loop as module

    session = AsyncMock()
    session.__aenter__.return_value = session
    instance = SimpleNamespace(id="instance-id")
    repository = AsyncMock()
    repository.list_all.return_value = [instance]
    monkeypatch.setattr(module, "InstanceRepository", Mock(return_value=repository))
    factory = Mock(return_value=AsyncMock())
    monkeypatch.setattr(module, "Reconciler", factory)
    loop = ReconciliationLoop(
        Mock(return_value=session), SimpleNamespace(reconciliation_retry_limit=3)
    )
    await loop.run_once()
    assert factory.call_args.kwargs["observed_after"] == loop.started_at
    factory.return_value.reconcile.assert_awaited_once_with(instance.id)
