"""Instance persistence. Tombstones are hidden by default; caller owns commit."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instance import Instance


class InstanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **fields) -> Instance:
        instance = Instance(**fields)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(
        self, instance_id: UUID, *, include_deleted: bool = False, for_update: bool = False
    ) -> Instance | None:
        query = select(Instance).where(Instance.id == instance_id)
        if not include_deleted:
            query = query.where(Instance.deleted_at.is_(None))
        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    async def get_by_name(self, name: str, *, include_deleted: bool = False) -> Instance | None:
        query = select(Instance).where(Instance.name == name)
        if not include_deleted:
            query = query.where(Instance.deleted_at.is_(None))
        return await self.session.scalar(query)

    async def list_all(self) -> list[Instance]:
        result = await self.session.scalars(
            select(Instance)
            .where(Instance.deleted_at.is_(None))
            .order_by(Instance.name, Instance.id)
        )
        return list(result.all())

    async def list_by_node(self, node_id: UUID) -> list[Instance]:
        result = await self.session.scalars(
            select(Instance)
            .where(Instance.compute_node_id == node_id, Instance.deleted_at.is_(None))
            .order_by(Instance.name)
        )
        return list(result.all())

    async def flush(self) -> None:
        await self.session.flush()
