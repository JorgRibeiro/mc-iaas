"""Manual Node observation, preserving last-known state on partial or failed probes."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.compute_agent import ComputeAgentClient
from app.clients.errors import AgentError
from app.core.config import get_settings
from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability, ObservedInstanceState
from app.repositories.instance_repository import InstanceRepository
from app.repositories.node_repository import NodeRepository
from app.schemas.agent import AgentSnapshot
from app.secrets.provider import SecretProvider
from app.services.event_service import EventService
from app.services.node_service import NodeNotFoundError

logger = logging.getLogger(__name__)


class NodeObservationService:
    def __init__(
        self,
        session: AsyncSession,
        client: ComputeAgentClient,
        secrets: SecretProvider,
        *,
        offline_threshold: int | None = None,
    ) -> None:
        self.session = session
        self.repository = NodeRepository(session)
        self.client = client
        self.secrets = secrets
        self.instances = InstanceRepository(session)
        self.offline_threshold = (
            get_settings().node_offline_threshold
            if offline_threshold is None
            else offline_threshold
        )

    async def refresh_node(self, node_id: UUID, *, enabled_only: bool = False) -> ComputeNode:
        failure: AgentError | None = None
        try:
            # Serialize manual refreshes for this Node, including failure increments.
            node = await self.repository.get_by_id(node_id, for_update=True)
            if node is None:
                raise NodeNotFoundError()
            if enabled_only and not node.enabled:
                return node
            previous_reachability = node.reachability
            logger.info("node.refresh.started node_id=%s", node_id)
            try:
                token = self.secrets.get_agent_token(node.credential_ref)
                snapshot = await self.client.get_snapshot(node.endpoint, token)
            except AgentError as error:
                node.consecutive_failures += 1
                node.last_error = error.message
                if node.consecutive_failures >= self.offline_threshold:
                    node.reachability = NodeReachability.OFFLINE
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
                await self._sync_instances(node_id, snapshot, now)
                node.last_error = (
                    "Partial Agent snapshot"
                    if snapshot.errors or snapshot.node_health is None
                    else None
                )
            if node.reachability != previous_reachability:
                EventService(self.session).emit(f"node.{node.reachability.value}", node_id=node_id)
            # Persist failures before translating them into an unsuccessful HTTP response.
            await self.session.commit()
        except BaseException:
            await self.session.rollback()
            raise
        if node.reachability != previous_reachability:
            logger.info("node.%s node_id=%s", node.reachability.value, node_id)
        if failure is not None:
            logger.warning(
                "node.refresh.failed node_id=%s error=%s", node_id, type(failure).__name__
            )
            raise failure
        logger.info("node.refresh.completed node_id=%s", node_id)
        return node

    async def _sync_instances(
        self, node_id: UUID, snapshot: AgentSnapshot, observed_at: datetime
    ) -> None:
        if snapshot.instances is None or "instances" in snapshot.errors:
            return
        known = await self.instances.list_by_node(node_id)
        inventory = {instance.name: instance for instance in snapshot.instances}
        known_names = {instance.name for instance in known}
        orphan_count = len(inventory.keys() - known_names)
        if orphan_count:
            # Count only: arbitrary remote workload names must not leak into logs.
            logger.warning(
                "node.orphan_instance.detected node_id=%s count=%s", node_id, orphan_count
            )
        states = {state.value: state for state in ObservedInstanceState}
        for instance in known:
            previous_state = instance.observed_state
            reported = inventory.get(instance.name)
            if reported is None:
                instance.observed_state = ObservedInstanceState.MISSING
                instance.observed_runtime_slot = None
                instance.observed_runtime_ip = None
                instance.observed_external_port = None
            else:
                instance.observed_state = states.get(reported.state, ObservedInstanceState.UNKNOWN)
                runtime = reported.runtime
                instance.observed_runtime_slot = runtime.slot if runtime else None
                instance.observed_runtime_ip = runtime.ip if runtime else None
                instance.observed_external_port = runtime.external_port if runtime else None
                if reported.minecraft_status is not None:
                    instance.minecraft_status = reported.minecraft_status
            if instance.observed_state != previous_state and instance.observed_state.value in {
                "running",
                "stopped",
                "missing",
            }:
                EventService(self.session).emit(
                    f"instance.observed.{instance.observed_state.value}",
                    node_id=node_id,
                    instance_id=instance.id,
                )
            instance.last_observed_at = observed_at
            # No observation errors are currently written on Instances. Preserve errors
            # owned by other operations until their provenance is defined.
        await self.instances.flush()
