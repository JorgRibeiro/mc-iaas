"""Administrative Node rules and transaction boundary."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compute_node import ComputeNode
from app.repositories.node_repository import NodeRepository
from app.schemas.node import ComputeNodeCreate, ComputeNodeUpdate


class NodeNotFoundError(Exception):
    """The requested Node does not exist."""


class NodeAlreadyExistsError(Exception):
    """A Node already owns the requested name."""


def is_node_name_conflict(error: IntegrityError) -> bool:
    # SQLAlchemy's asyncpg adapter wraps the driver exception as its cause.
    original = error.orig
    driver_error = original.__cause__ or original
    return (
        getattr(original, "sqlstate", None) == "23505"
        and getattr(driver_error, "constraint_name", None) == "uq_compute_nodes_name"
    )


class NodeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = NodeRepository(session)

    async def create_node(self, data: ComputeNodeCreate) -> ComputeNode:
        try:
            if await self.repository.get_by_name(data.name) is not None:
                raise NodeAlreadyExistsError()
            node = await self.repository.create(**data.model_dump())
            await self.session.commit()
            return node
        except Exception as error:
            await self.session.rollback()
            if isinstance(error, IntegrityError) and is_node_name_conflict(error):
                raise NodeAlreadyExistsError() from error
            raise

    async def get_node(self, node_id: UUID) -> ComputeNode:
        node = await self.repository.get_by_id(node_id)
        if node is None:
            raise NodeNotFoundError()
        return node

    async def list_nodes(self) -> list[ComputeNode]:
        return await self.repository.list_all()

    async def update_node(self, node_id: UUID, data: ComputeNodeUpdate) -> ComputeNode:
        try:
            node = await self.get_node(node_id)
            if data.name is not None and data.name != node.name:
                existing = await self.repository.get_by_name(data.name)
                if existing is not None and existing.id != node_id:
                    raise NodeAlreadyExistsError()
            node = await self.repository.update(node, **data.model_dump(exclude_unset=True))
            await self.session.commit()
            return node
        except Exception as error:
            await self.session.rollback()
            if isinstance(error, IntegrityError) and is_node_name_conflict(error):
                raise NodeAlreadyExistsError() from error
            raise
