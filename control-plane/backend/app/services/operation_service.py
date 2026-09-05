"""Durable operation queue and read access; writes participate in caller transactions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OperationStatus, OperationType
from app.models.operation import Operation
from app.services.event_service import EventService
from app.services.lifecycle_errors import (
    ActiveOperationError,
    LifecycleError,
    OperationNotFoundError,
)

ACTIVE = (OperationStatus.PENDING, OperationStatus.IN_PROGRESS, OperationStatus.UNCERTAIN)
MUTATIONS = (
    OperationType.CREATE,
    OperationType.START,
    OperationType.STOP,
    OperationType.RESTART,
    OperationType.DELETE,
)


class OperationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_idle(self, instance_id: UUID) -> None:
        active = await self.session.scalar(
            select(Operation.id).where(
                Operation.instance_id == instance_id,
                Operation.status.in_(ACTIVE),
                Operation.type.in_(MUTATIONS),
            )
        )
        if active is not None:
            raise ActiveOperationError()

    async def ensure_owned(self, instance_id: UUID) -> None:
        # A failed CREATE does not establish ownership of a same-name remote workload.
        failed_create = await self.session.scalar(
            select(Operation.id).where(
                Operation.instance_id == instance_id,
                Operation.type == OperationType.CREATE,
                Operation.status == OperationStatus.FAILED,
            )
        )
        if failed_create is not None:
            raise LifecycleError()

    async def create(
        self, instance_id: UUID, node_id: UUID, kind: OperationType, metadata: dict | None = None
    ) -> Operation:
        await self.ensure_idle(instance_id)
        operation = Operation(
            instance_id=instance_id,
            node_id=node_id,
            type=kind,
            status=OperationStatus.PENDING,
            operation_metadata=metadata or {},
        )
        self.session.add(operation)
        await self.session.flush()
        EventService(self.session).emit(
            f"instance.{kind.value}.requested",
            node_id=node_id,
            instance_id=instance_id,
            operation_id=operation.id,
        )
        return operation

    async def get(self, operation_id: UUID) -> Operation:
        operation = await self.session.get(Operation, operation_id)
        if operation is None:
            raise OperationNotFoundError()
        return operation

    async def list_all(
        self,
        instance_id: UUID | None = None,
        *,
        node_id: UUID | None = None,
        status: OperationStatus | None = None,
        type: OperationType | None = None,
    ) -> list[Operation]:
        query = select(Operation).order_by(Operation.requested_at, Operation.id)
        if instance_id is not None:
            query = query.where(Operation.instance_id == instance_id)
        for field, value in {"node_id": node_id, "status": status, "type": type}.items():
            if value is not None:
                query = query.where(getattr(Operation, field) == value)
        return list((await self.session.scalars(query)).all())
