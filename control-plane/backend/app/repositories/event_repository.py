"""Append-only event persistence; commits belong to the domain transaction."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventLevel
from app.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def create(self, **fields) -> Event:
        event = Event(**fields)
        self.session.add(event)
        return event

    async def list(
        self,
        *,
        level: EventLevel | None = None,
        node_id: UUID | None = None,
        instance_id: UUID | None = None,
        operation_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        query = select(Event)
        for field, value in {
            "level": level,
            "node_id": node_id,
            "instance_id": instance_id,
            "operation_id": operation_id,
            "event_type": event_type,
        }.items():
            if value is not None:
                query = query.where(getattr(Event, field) == value)
        return list(
            (
                await self.session.scalars(
                    query.order_by(Event.timestamp.desc(), Event.id.desc()).limit(limit)
                )
            ).all()
        )
