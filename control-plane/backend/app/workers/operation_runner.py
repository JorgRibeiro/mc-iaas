"""Durable mutation dispatch. No automatic retry of ambiguous Agent operations."""

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update

from app.clients.errors import (
    AgentAuthenticationError,
    AgentConflictError,
    AgentCredentialUnavailableError,
    AgentNotFoundError,
    AgentResponseError,
    AgentValidationError,
)
from app.models.compute_node import ComputeNode
from app.models.enums import ObservedInstanceState as Observed
from app.models.enums import OperationStatus as Status
from app.models.enums import OperationType as Kind
from app.models.operation import Operation
from app.repositories.instance_repository import InstanceRepository
from app.repositories.node_repository import NodeRepository
from app.schemas.instance import InstanceCreate
from app.services.event_service import EventService
from app.services.instance_service import validate_lifecycle
from app.services.lifecycle_errors import LifecycleError, NodeNotUsableError
from app.services.operation_service import MUTATIONS
from app.services.scheduler import Scheduler

logger = logging.getLogger(__name__)

KNOWN_FAILURES = (
    AgentAuthenticationError,
    AgentConflictError,
    AgentNotFoundError,
    AgentValidationError,
    AgentCredentialUnavailableError,
    LifecycleError,
)


class OperationRunner:
    def __init__(self, sessions, client, secrets) -> None:
        self.sessions = sessions
        self.client = client
        self.secrets = secrets
        self._task: asyncio.Task | None = None
        self.observed_after: datetime | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run(), name="operation-runner")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def recover_interrupted(self) -> None:
        # Single worker only. Never redispatch an operation left claimed by a previous process.
        async with self.sessions() as session:
            result = await session.execute(
                update(Operation)
                .where(Operation.status == Status.IN_PROGRESS, Operation.type.in_(MUTATIONS))
                .values(
                    status=Status.UNCERTAIN,
                    completed_at=datetime.now(UTC),
                    error_code="WorkerInterrupted",
                    error_message="Worker interrupted; outcome unknown",
                )
                .returning(Operation.id, Operation.node_id, Operation.instance_id)
            )
            for row in result.all():
                EventService(session).emit(
                    "operation.uncertain",
                    operation_id=row.id,
                    node_id=row.node_id,
                    instance_id=row.instance_id,
                )
            await session.commit()

    async def run(self) -> None:
        self.observed_after = datetime.now(UTC)
        recovered = False
        while True:
            try:
                if not recovered:
                    await self.recover_interrupted()
                    recovered = True
                worked = await self.run_once()
            except Exception as error:
                logger.warning("operation.worker.failed error=%s", type(error).__name__)
                worked = False
            if not worked:
                await asyncio.sleep(1)

    async def claim(self) -> UUID | None:
        async with self.sessions() as session:
            query = select(Operation).where(
                Operation.status == Status.PENDING, Operation.type.in_(MUTATIONS)
            )
            if self.observed_after is not None:
                query = query.join(ComputeNode, Operation.node_id == ComputeNode.id).where(
                    ComputeNode.last_seen_at > self.observed_after
                )
            operation = await session.scalar(
                query.order_by(Operation.requested_at, Operation.id).with_for_update(
                    skip_locked=True, of=Operation
                )
            )
            if operation is None:
                return None
            operation.status = Status.IN_PROGRESS
            operation.started_at = datetime.now(UTC)
            operation.attempt_count += 1
            operation_id = operation.id
            EventService(session).emit(
                "operation.started",
                operation_id=operation.id,
                node_id=operation.node_id,
                instance_id=operation.instance_id,
            )
            await session.commit()
            return operation_id

    async def run_once(self) -> bool:
        operation_id = await self.claim()
        if operation_id is None:
            return False
        logger.info("operation.started operation_id=%s", operation_id)
        try:
            await self.execute(operation_id)
        except BaseException as error:
            # The claim is durable. A cancelled/failed dispatch must never become pending again.
            await self.mark_uncertain(operation_id)
            if isinstance(error, asyncio.CancelledError):
                raise
            logger.warning(
                "operation.dispatch.failed operation_id=%s error=%s",
                operation_id,
                type(error).__name__,
            )
        return True

    async def mark_uncertain(self, operation_id: UUID) -> None:
        async with self.sessions() as session:
            result = await session.execute(
                update(Operation)
                .where(Operation.id == operation_id, Operation.status == Status.IN_PROGRESS)
                .values(
                    status=Status.UNCERTAIN,
                    completed_at=datetime.now(UTC),
                    error_code="DispatchInterrupted",
                    error_message="Dispatch outcome unknown",
                )
                .returning(Operation.id, Operation.node_id, Operation.instance_id)
            )
            for row in result.all():
                EventService(session).emit(
                    "operation.uncertain",
                    operation_id=row.id,
                    node_id=row.node_id,
                    instance_id=row.instance_id,
                )
            await session.commit()
        logger.warning("operation.uncertain operation_id=%s", operation_id)

    async def execute(self, operation_id: UUID) -> None:
        async with self.sessions() as session:
            operation = await session.get(Operation, operation_id)
            if operation is None or operation.status != Status.IN_PROGRESS:
                return
            node = await NodeRepository(session).get_by_id(operation.node_id, for_update=True)
            instance = await InstanceRepository(session).get_by_id(
                operation.instance_id, for_update=True
            )
            try:
                if node is None or instance is None or instance.compute_node_id != node.id:
                    raise NodeNotUsableError()
                if operation.type == Kind.CREATE:
                    if not Scheduler(session).usable(node):
                        raise NodeNotUsableError()
                else:
                    validate_lifecycle(instance, operation.type)
                    if operation.type == Kind.START:
                        Scheduler(session).validate_start(node)
                token = self.secrets.get_agent_token(node.credential_ref)
                if operation.type == Kind.CREATE:
                    payload = InstanceCreate.model_validate(
                        operation.operation_metadata
                    ).model_dump()
                    result = await self.client.create_instance(node.endpoint, token, payload)
                else:
                    method = getattr(self.client, operation.type.value + "_instance")
                    result = await method(node.endpoint, token, instance.name)
                if result.name != instance.name:
                    raise AgentResponseError()
                now = datetime.now(UTC)
                if operation.type == Kind.DELETE:
                    if not result.deleted or not result.data_preserved:
                        raise AgentResponseError()
                    instance.observed_state = Observed.MISSING
                    instance.deleted_at = now
                    runtime = None
                else:
                    expected = (
                        Observed.STOPPED
                        if operation.type in (Kind.CREATE, Kind.STOP)
                        else Observed.RUNNING
                    )
                    if result.state != expected.value:
                        raise AgentResponseError()
                    instance.observed_state = expected
                    runtime = result.runtime if expected == Observed.RUNNING else None
                if runtime is not None or instance.observed_state != Observed.RUNNING:
                    instance.observed_runtime_slot = runtime.slot if runtime else None
                    instance.observed_runtime_ip = runtime.ip if runtime else None
                    instance.observed_external_port = runtime.external_port if runtime else None
                instance.last_observed_at = now
                operation.status = Status.SUCCEEDED
                operation.error_code = None
                operation.error_message = None
            except KNOWN_FAILURES as error:
                operation.status = Status.FAILED
                operation.error_code = type(error).__name__
                operation.error_message = error.message
            except Exception:
                # 5xx, invalid replies and all transport errors can follow remote side effects.
                operation.status = Status.UNCERTAIN
                operation.error_code = "AgentOutcomeUnknown"
                operation.error_message = "Agent outcome unknown; automatic retry disabled"
            operation.completed_at = datetime.now(UTC)
            EventService(session).emit(
                f"operation.{operation.status.value}",
                operation_id=operation.id,
                node_id=operation.node_id,
                instance_id=operation.instance_id,
            )
            await session.commit()
            logger.info("operation.%s operation_id=%s", operation.status.value, operation_id)
