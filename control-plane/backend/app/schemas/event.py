"""Stable activity response, without arbitrary details JSON."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import EventLevel


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    timestamp: datetime
    level: EventLevel
    component: str
    event_type: str
    node_id: UUID | None
    instance_id: UUID | None
    operation_id: UUID | None
    message: str
