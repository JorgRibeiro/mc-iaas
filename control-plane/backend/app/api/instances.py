"""Asynchronous Instance lifecycle API."""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.enums import OperationType
from app.schemas.instance import InstanceCreate, InstanceResponse
from app.schemas.operation import OperationAccepted
from app.services.instance_service import InstanceService
from app.services.lifecycle_errors import (
    InstanceNotFoundError,
    LifecycleError,
    NoSchedulableNodeError,
)

router = APIRouter(prefix="/instances", tags=["instances"])


async def get_instance_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[InstanceService]:
    try:
        yield InstanceService(session)
    except InstanceNotFoundError as error:
        raise HTTPException(404, error.message) from None
    except NoSchedulableNodeError as error:
        raise HTTPException(503, error.message) from None
    except LifecycleError as error:
        raise HTTPException(409, error.message) from None


Service = Annotated[InstanceService, Depends(get_instance_service)]


@router.get("", response_model=list[InstanceResponse])
async def list_instances(service: Service):
    return await service.list_all()


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(instance_id: UUID, service: Service):
    return await service.get(instance_id)


@router.post("", response_model=OperationAccepted, status_code=202)
async def create_instance(data: InstanceCreate, service: Service):
    return OperationAccepted.model_validate(await service.create(data))


@router.post("/{instance_id}/start", response_model=OperationAccepted, status_code=202)
async def start_instance(instance_id: UUID, service: Service):
    return OperationAccepted.model_validate(await service.request(instance_id, OperationType.START))


@router.post("/{instance_id}/stop", response_model=OperationAccepted, status_code=202)
async def stop_instance(instance_id: UUID, service: Service):
    return OperationAccepted.model_validate(await service.request(instance_id, OperationType.STOP))


@router.post("/{instance_id}/restart", response_model=OperationAccepted, status_code=202)
async def restart_instance(instance_id: UUID, service: Service):
    return OperationAccepted.model_validate(
        await service.request(instance_id, OperationType.RESTART)
    )


@router.delete("/{instance_id}", response_model=OperationAccepted, status_code=202)
async def delete_instance(instance_id: UUID, service: Service):
    return OperationAccepted.model_validate(
        await service.request(instance_id, OperationType.DELETE)
    )
