"""Public operation status; internal metadata is never returned."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OperationStatus, OperationType


class OperationAccepted(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operation_id: UUID = Field(validation_alias="id")
    instance_id: UUID
    status: OperationStatus


class OperationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instance_id: UUID | None
    node_id: UUID | None
    type: OperationType
    status: OperationStatus
    requested_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    attempt_count: int
    error_code: str | None
    error_message: str | None
