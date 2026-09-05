"""Manual Node observation, preserving last-known state on partial or failed probes."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.compute_agent import ComputeAgentClient
from app.clients.errors import AgentError
from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability
from app.repositories.node_repository import NodeRepository
from app.secrets.provider import SecretProvider
from app.services.node_service import NodeNotFoundError

logger = logging.getLogger(__name__)


class NodeObservationService:
    def __init__(
        self, session: AsyncSession, client: ComputeAgentClient, secrets: SecretProvider
    ) -> None:
        self.session = session
        self.repository = NodeRepository(session)
        self.client = client
        self.secrets = secrets

    async def refresh_node(self, node_id: UUID) -> ComputeNode:
        failure: AgentError | None = None
        try:
            # Serialize manual refreshes for this Node, including failure increments.
            node = await self.repository.get_by_id(node_id, for_update=True)
            if node is None:
                raise NodeNotFoundError()
            logger.info("node.refresh.started node_id=%s", node_id)
            try:
                token = self.secrets.get_agent_token(node.credential_ref)
                snapshot = await self.client.get_snapshot(node.endpoint, token)
            except AgentError as error:
                node.consecutive_failures += 1
                node.last_error = error.message
                failure = error
            else:
                now = datetime.now(UTC)
                node.reachability = NodeReachability.ONLINE
                node.last_seen_at = now
                node.consecutive_failures = 0
                node.agent_version = snapshot.agent.version
                if snapshot.node_health is not None:
                    health = snapshot.node_health
                    node.observed_health = NodeHealth(health.status)
                    node.observed_ready = health.ready
                    for field, value in health.capacity.model_dump().items():
                        setattr(node, field, value)
                    # Local receipt time avoids depending on clock alignment with the Agent.
                    node.last_observed_at = now
                node.last_error = (
                    "Partial Agent snapshot"
                    if snapshot.errors or snapshot.node_health is None
                    else None
                )
            # Persist failures before translating them into an unsuccessful HTTP response.
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        if failure is not None:
            logger.warning(
                "node.refresh.failed node_id=%s error=%s", node_id, type(failure).__name__
            )
            raise failure
        logger.info("node.refresh.completed node_id=%s", node_id)
        return node
