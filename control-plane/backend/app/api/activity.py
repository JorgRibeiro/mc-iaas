"""Activity and current-state infrastructure views."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.enums import EventLevel
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventResponse
from app.schemas.monitoring import MonitoringResponse, OverviewResponse
from app.services.read_service import ReadService

router = APIRouter(tags=["activity", "monitoring"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    session: Session,
    level: EventLevel | None = None,
    node_id: UUID | None = None,
    instance_id: UUID | None = None,
    operation_id: UUID | None = None,
    event_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    return await EventRepository(session).list(
        level=level,
        node_id=node_id,
        instance_id=instance_id,
        operation_id=operation_id,
        event_type=event_type,
        limit=limit,
    )


@router.get("/overview", response_model=OverviewResponse)
async def overview(session: Session):
    return (await ReadService(session).summary())["overview"]


@router.get("/monitoring/summary", response_model=MonitoringResponse)
async def monitoring(session: Session):
    return await ReadService(session).summary()
