"""Sequential polling with per-Node backoff, for a single API process."""

import asyncio
import logging
import math
from contextlib import suppress
from time import monotonic
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clients.compute_agent import ComputeAgentClient
from app.clients.errors import AgentError
from app.core.config import Settings
from app.repositories.node_repository import NodeRepository
from app.secrets.provider import SecretProvider
from app.services.node_observation_service import NodeObservationService
from app.services.node_service import NodeNotFoundError

logger = logging.getLogger(__name__)


def polling_delay(interval: float, maximum: float, failures: int) -> float:
    if failures <= 0:
        return interval
    # Bound the exponent before evaluation, even after arbitrarily many failures.
    exponent = min(max(failures - 1, 0), max(0, math.ceil(math.log2(maximum / interval))))
    return min(maximum, interval * 2**exponent)


class NodePoller:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        client: ComputeAgentClient,
        secrets: SecretProvider,
        settings: Settings,
    ) -> None:
        self.sessions = sessions
        self.client = client
        self.secrets = secrets
        self.settings = settings
        self._due: dict[UUID, float] = {}
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run(), name="node-poller")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def run(self) -> None:
        while True:
            try:
                await self.poll_once()
            except Exception as error:
                # Database/driver exception strings can contain credentials.
                logger.warning("node.poll.cycle_failed error=%s", type(error).__name__)
                delay = self.settings.node_poll_interval
            else:
                next_due = min(
                    self._due.values(), default=monotonic() + self.settings.node_poll_interval
                )
                delay = min(self.settings.node_poll_interval, max(0, next_due - monotonic()))
            await asyncio.sleep(delay)

    async def poll_once(self) -> None:
        async with self.sessions() as session:
            nodes = await NodeRepository(session).list_enabled()
            node_ids = [node.id for node in nodes]
        self._due = {key: value for key, value in self._due.items() if key in node_ids}
        for node_id in node_ids:
            if monotonic() < self._due.get(node_id, 0):
                continue
            delay = self.settings.node_poll_interval
            try:
                async with self.sessions() as session:
                    service = NodeObservationService(
                        session,
                        self.client,
                        self.secrets,
                        offline_threshold=self.settings.node_offline_threshold,
                    )
                    try:
                        node = await service.refresh_node(node_id, enabled_only=True)
                    except AgentError:
                        # The service has committed the failed observation already.
                        node = await NodeRepository(session).get_by_id(node_id)
                    if node is not None:
                        delay = polling_delay(
                            self.settings.node_poll_interval,
                            self.settings.node_max_backoff,
                            node.consecutive_failures,
                        )
            except NodeNotFoundError:
                self._due.pop(node_id, None)
                continue
            except Exception as error:
                logger.warning(
                    "node.poll.failed node_id=%s error=%s", node_id, type(error).__name__
                )
            self._due[node_id] = monotonic() + delay
