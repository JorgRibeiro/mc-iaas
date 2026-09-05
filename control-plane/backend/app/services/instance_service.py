"""Transactional lifecycle requests. HTTP dispatch is performed only by the runner."""

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DesiredInstanceState as Desired
from app.models.enums import ObservedInstanceState as Observed
from app.models.enums import OperationType
from app.models.instance import Instance
from app.models.operation import Operation
from app.repositories.instance_repository import InstanceRepository
from app.repositories.node_repository import NodeRepository
from app.schemas.instance import InstanceCreate
from app.services.lifecycle_errors import (
    ActiveOperationError,
    InstanceAlreadyExistsError,
    InstanceNotFoundError,
    LifecycleError,
    NodeNotUsableError,
)
from app.services.operation_service import OperationService
from app.services.scheduler import Scheduler

logger = logging.getLogger(__name__)


def translate_integrity(error: IntegrityError) -> None:
    original = error.orig
    driver = original.__cause__ or original
    if getattr(original, "sqlstate", None) == "23505":
        constraint = getattr(driver, "constraint_name", None)
        if constraint == "uq_instances_name":
            raise InstanceAlreadyExistsError() from None
        if constraint == "uq_operations_active_mutation_per_instance":
            raise ActiveOperationError() from None
    raise error


def validate_lifecycle(instance: Instance, kind: OperationType) -> None:
    allowed = {
        OperationType.START: {Observed.STOPPED},
        OperationType.STOP: {Observed.RUNNING, Observed.PAUSED, Observed.STOPPED},
        OperationType.RESTART: {Observed.RUNNING},
        OperationType.DELETE: {Observed.STOPPED},
    }
    if kind == OperationType.RESTART and instance.desired_state != Desired.RUNNING:
        raise LifecycleError()
    if kind not in allowed or instance.observed_state not in allowed[kind]:
        raise LifecycleError()


class InstanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InstanceRepository(session)
        self.nodes = NodeRepository(session)
        self.scheduler = Scheduler(session)
        self.operations = OperationService(session)

    async def get(self, instance_id: UUID) -> Instance:
        instance = await self.repository.get_by_id(instance_id)
        if instance is None:
            raise InstanceNotFoundError()
        return instance

    async def list_all(self) -> list[Instance]:
        return await self.repository.list_all()

    async def create(self, data: InstanceCreate) -> Operation:
        try:
            if await self.repository.get_by_name(data.name, include_deleted=True) is not None:
                raise InstanceAlreadyExistsError()
            node = await self.scheduler.select_node()
            instance = await self.repository.create(
                name=data.name,
                memory_mb=data.memory_mb,
                vcpus=data.vcpus,
                minecraft_version=data.minecraft_version,
                compute_node_id=node.id,
                desired_state=Desired.STOPPED,
                observed_state=Observed.UNKNOWN,
            )
            operation = await self.operations.create(
                instance.id, node.id, OperationType.CREATE, data.model_dump()
            )
            await self.session.commit()
            logger.info("instance.create.requested instance_id=%s", instance.id)
            return operation
        except BaseException as error:
            await self.session.rollback()
            if isinstance(error, IntegrityError):
                translate_integrity(error)
            raise

    async def request(self, instance_id: UUID, kind: OperationType) -> Operation:
        try:
            initial = await self.get(instance_id)
            if initial.compute_node_id is None:
                raise NodeNotUsableError()
            await self.operations.ensure_idle(instance_id)
            await self.operations.ensure_owned(instance_id)
            # Same lock order as observation/runner: Node, then Instance.
            node = await self.nodes.get_by_id(
                initial.compute_node_id, for_update=True, skip_locked=True
            )
            if node is None:
                raise NodeNotUsableError()
            instance = await self.repository.get_by_id(instance_id, for_update=True)
            if instance is None:
                raise InstanceNotFoundError()
            if node is None or instance.compute_node_id != node.id:
                raise NodeNotUsableError()
            await self.operations.ensure_idle(instance.id)
            validate_lifecycle(instance, kind)
            if kind == OperationType.START:
                self.scheduler.validate_start(node)
            if kind == OperationType.START:
                instance.desired_state = Desired.RUNNING
            elif kind == OperationType.STOP:
                instance.desired_state = Desired.STOPPED
            elif kind == OperationType.DELETE:
                instance.desired_state = Desired.ABSENT
            operation = await self.operations.create(instance.id, node.id, kind)
            await self.session.commit()
            return operation
        except BaseException as error:
            await self.session.rollback()
            if isinstance(error, IntegrityError):
                translate_integrity(error)
            raise
