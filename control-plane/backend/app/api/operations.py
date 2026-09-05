"""Read-only operation progress endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.operation import OperationResponse
from app.services.lifecycle_errors import OperationNotFoundError
from app.services.operation_service import OperationService

router = APIRouter(prefix="/operations", tags=["operations"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[OperationResponse])
async def list_operations(session: Session, instance_id: UUID | None = None):
    return await OperationService(session).list_all(instance_id)


@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(operation_id: UUID, session: Session):
    try:
        return await OperationService(session).get(operation_id)
    except OperationNotFoundError as error:
        raise HTTPException(404, error.message) from None
