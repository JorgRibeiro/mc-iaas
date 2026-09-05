"""Single-process reconciliation loop with a startup observation barrier."""

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime

from app.repositories.instance_repository import InstanceRepository
from app.services.reconciler import Reconciler

logger = logging.getLogger(__name__)


class ReconciliationLoop:
    def __init__(self, sessions, settings) -> None:
        self.sessions = sessions
        self.settings = settings
        self.started_at = datetime.now(UTC)
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self.run(), name="reconciliation-loop")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def run(self) -> None:
        while True:
            try:
                await self.run_once()
            except Exception as error:
                logger.warning("reconciliation.cycle_failed error=%s", type(error).__name__)
            await asyncio.sleep(self.settings.reconciliation_interval)

    async def run_once(self) -> None:
        async with self.sessions() as session:
            ids = [instance.id for instance in await InstanceRepository(session).list_all()]
        for instance_id in ids:
            try:
                async with self.sessions() as session:
                    await Reconciler(
                        session,
                        observed_after=self.started_at,
                        retry_limit=self.settings.reconciliation_retry_limit,
                    ).reconcile(instance_id)
            except Exception as error:
                logger.warning(
                    "reconciliation.failed instance_id=%s error=%s",
                    instance_id,
                    type(error).__name__,
                )
