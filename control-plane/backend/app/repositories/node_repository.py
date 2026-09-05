"""Compute Node persistence; the caller owns the transaction."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compute_node import ComputeNode


class NodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, name: str, endpoint: str, credential_ref: str, enabled: bool
    ) -> ComputeNode:
        node = ComputeNode(
            name=name, endpoint=endpoint, credential_ref=credential_ref, enabled=enabled
        )
        self.session.add(node)
        await self.session.flush()
        return node

    async def get_by_id(self, node_id: UUID) -> ComputeNode | None:
        return await self.session.scalar(select(ComputeNode).where(ComputeNode.id == node_id))

    async def get_by_name(self, name: str) -> ComputeNode | None:
        return await self.session.scalar(select(ComputeNode).where(ComputeNode.name == name))

    async def list_all(self) -> list[ComputeNode]:
        result = await self.session.scalars(select(ComputeNode).order_by(ComputeNode.name))
        return list(result.all())

    async def update(
        self,
        node: ComputeNode,
        *,
        name: str | None = None,
        endpoint: str | None = None,
        credential_ref: str | None = None,
        enabled: bool | None = None,
    ) -> ComputeNode:
        for field, value in {
            "name": name,
            "endpoint": endpoint,
            "credential_ref": credential_ref,
            "enabled": enabled,
        }.items():
            if value is not None:
                setattr(node, field, value)
        await self.session.flush()
        return node
