"""Sticky placement selection from recent observed Node state. No HTTP or secrets."""

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.compute_node import ComputeNode
from app.models.enums import NodeReachability
from app.repositories.node_repository import NodeRepository
from app.services.lifecycle_errors import (
    NodeCapacityError,
    NodeNotUsableError,
    NoSchedulableNodeError,
)

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, session: AsyncSession, max_age: float | None = None) -> None:
        self.nodes = NodeRepository(session)
        self.max_age = get_settings().node_observation_max_age if max_age is None else max_age

    def usable(self, node: ComputeNode) -> bool:
        now = datetime.now(UTC)
        return bool(
            node.enabled
            and node.reachability == NodeReachability.ONLINE
            and node.observed_ready is True
            and all(
                timestamp is not None and 0 <= (now - timestamp).total_seconds() <= self.max_age
                for timestamp in (node.last_seen_at, node.last_observed_at)
            )
        )

    def validate_start(self, node: ComputeNode) -> None:
        if not self.usable(node):
            raise NodeNotUsableError()
        if node.available_slots is not None and node.available_slots <= 0:
            raise NodeCapacityError()

    async def select_node(self) -> ComputeNode:
        candidates = sorted(
            (node for node in await self.nodes.list_enabled() if self.usable(node)),
            key=lambda node: (
                -(node.available_slots if node.available_slots is not None else -1),
                node.name,
                str(node.id),
            ),
        )
        for candidate in candidates:
            node = await self.nodes.get_by_id(candidate.id, for_update=True, skip_locked=True)
            if node is not None and self.usable(node):
                logger.info("scheduler.node_selected node_id=%s", node.id)
                return node
        raise NoSchedulableNodeError()
