"""Conservative decisions from persisted observations; never calls an Agent."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import DesiredInstanceState as Desired
from app.models.enums import ObservedInstanceState as Observed
from app.models.enums import OperationStatus as Status
from app.models.enums import OperationType as Kind
from app.models.operation import Operation
from app.repositories.instance_repository import InstanceRepository
from app.repositories.node_repository import NodeRepository
from app.services.event_service import EventService
from app.services.lifecycle_errors import LifecycleError
from app.services.operation_service import ACTIVE, MUTATIONS, OperationService
from app.services.scheduler import Scheduler


class Reconciler:
    def __init__(
        self,
        session: AsyncSession,
        *,
        observed_after: datetime | None = None,
        retry_limit: int | None = None,
    ) -> None:
        self.session = session
        self.instances = InstanceRepository(session)
        self.nodes = NodeRepository(session)
        self.operations = OperationService(session)
        self.events = EventService(session)
        self.scheduler = Scheduler(session)
        self.observed_after = observed_after
        self.retry_limit = (
            get_settings().reconciliation_retry_limit if retry_limit is None else retry_limit
        )

    def block(self, instance, reason: str, operation=None) -> None:
        message = "reconciliation: " + reason
        if instance.last_error != message:
            instance.last_error = message
            self.events.emit(
                "reconciliation.blocked",
                instance_id=instance.id,
                node_id=instance.compute_node_id,
                operation_id=operation.id if operation else None,
            )

    @staticmethod
    def clear_condition(instance) -> None:
        if instance.last_error and instance.last_error.startswith("reconciliation: "):
            instance.last_error = None

    async def reconcile(self, instance_id: UUID) -> None:
        try:
            initial = await self.instances.get_by_id(instance_id)
            if initial is None or initial.compute_node_id is None:
                return
            node = await self.nodes.get_by_id(
                initial.compute_node_id, for_update=True, skip_locked=True
            )
            if node is None:
                return
            instance = await self.instances.get_by_id(instance_id, for_update=True)
            if instance is None or instance.compute_node_id != node.id:
                return
            # Node/Instance locks serialize resolution with dispatch. Do not lock the queue
            # row here: a concurrent claim may be inserting an Event referencing this Node.
            # Pending and in_progress are both treated as active, so a concurrent claim is safe.
            active = await self.session.scalar(
                select(Operation)
                .where(
                    Operation.instance_id == instance.id,
                    Operation.status.in_(ACTIVE),
                    Operation.type.in_(MUTATIONS),
                )
            )
            now = datetime.now(UTC)
            fresh = (
                instance.last_observed_at is not None
                and 0 <= (now - instance.last_observed_at).total_seconds() <= self.scheduler.max_age
                and (self.observed_after is None or instance.last_observed_at > self.observed_after)
            )
            if not self.scheduler.usable(node) or not fresh:
                return
            if active is not None:
                if active.status == Status.UNCERTAIN:
                    self.resolve_uncertain(instance, active)
                    await self.session.commit()
                return
            try:
                await self.operations.ensure_owned(instance.id)
            except LifecycleError:
                self.block(instance, "CREATE ownership is not confirmed")
                await self.session.commit()
                return
            latest_completion = await self.session.scalar(
                select(Operation.completed_at)
                .where(
                    Operation.instance_id == instance.id,
                    Operation.type.in_(MUTATIONS),
                    Operation.status.in_((Status.SUCCEEDED, Status.FAILED)),
                    Operation.completed_at.is_not(None),
                )
                .order_by(Operation.completed_at.desc())
                .limit(1)
            )
            if latest_completion is not None and instance.last_observed_at <= latest_completion:
                return  # Observe after the previous attempt before considering another command.
            desired, observed = instance.desired_state, instance.observed_state
            if (
                (desired == Desired.RUNNING and observed == Observed.RUNNING)
                or (desired == Desired.STOPPED and observed == Observed.STOPPED)
                or (desired == Desired.ABSENT and observed == Observed.MISSING)
            ):
                self.clear_condition(instance)
            elif observed == Observed.UNKNOWN:
                return
            else:
                kind = {
                    (Desired.RUNNING, Observed.STOPPED): Kind.START,
                    (Desired.STOPPED, Observed.RUNNING): Kind.STOP,
                    (Desired.ABSENT, Observed.STOPPED): Kind.DELETE,
                }.get((desired, observed))
                if kind is None:
                    self.block(
                        instance, "Unsafe divergence; no automatic recreation or stop-delete"
                    )
                else:
                    await self.enqueue(instance, node, kind)
            await self.session.commit()
        except BaseException:
            await self.session.rollback()
            raise

    def resolve_uncertain(self, instance, operation) -> None:
        boundary = operation.completed_at or operation.started_at or operation.requested_at
        if instance.last_observed_at <= boundary:
            return
        if operation.type == Kind.RESTART:
            self.block(instance, "RESTART outcome cannot be proven by running state", operation)
            return
        success = (
            (
                operation.type == Kind.START
                and instance.desired_state == Desired.RUNNING
                and instance.observed_state == Observed.RUNNING
            )
            or (operation.type == Kind.STOP and instance.observed_state == Observed.STOPPED)
            or (
                operation.type == Kind.CREATE
                and instance.observed_state in (Observed.STOPPED, Observed.RUNNING)
            )
            or (operation.type == Kind.DELETE and instance.observed_state == Observed.MISSING)
        )
        failed = operation.type == Kind.START and instance.observed_state == Observed.STOPPED
        if not success and not failed:
            return
        operation.status = Status.SUCCEEDED if success else Status.FAILED
        operation.completed_at = datetime.now(UTC)
        operation.error_code = None if success else "ObservedStopped"
        operation.error_message = None if success else "Subsequent inventory confirms stopped"
        if success and operation.type == Kind.DELETE:
            instance.deleted_at = operation.completed_at
        self.clear_condition(instance)
        self.events.emit(
            "operation.resolved",
            node_id=instance.compute_node_id,
            instance_id=instance.id,
            operation_id=operation.id,
        )

    async def enqueue(self, instance, node, kind: Kind) -> None:
        used = await self.session.scalar(
            select(func.count())
            .select_from(Operation)
            .where(
                Operation.instance_id == instance.id,
                Operation.type == kind,
                Operation.operation_metadata["source"].astext == "reconciler",
            )
        )
        if used >= self.retry_limit:
            self.block(instance, "Automatic retry budget exhausted")
            return
        if kind == Kind.START:
            try:
                self.scheduler.validate_start(node)
            except LifecycleError:
                self.block(instance, "Assigned Node cannot currently start workload")
                return
        self.clear_condition(instance)
        operation = await self.operations.create(
            instance.id, node.id, kind, {"source": "reconciler"}
        )
        self.events.emit(
            "reconciliation.action_created",
            node_id=node.id,
            instance_id=instance.id,
            operation_id=operation.id,
        )
