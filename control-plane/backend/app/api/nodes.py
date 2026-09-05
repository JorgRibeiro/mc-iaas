"""Versioned Compute Node administration endpoints."""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.errors import (
    AgentAuthenticationError,
    AgentError,
    AgentResponseError,
)
from app.db.session import get_session
from app.schemas.node import ComputeNodeCreate, ComputeNodeResponse, ComputeNodeUpdate
from app.services.node_observation_service import NodeObservationService
from app.services.node_service import NodeAlreadyExistsError, NodeNotFoundError, NodeService

router = APIRouter(prefix="/nodes", tags=["nodes"])


async def get_node_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[NodeService]:
    try:
        yield NodeService(session)
    except NodeNotFoundError as error:
        raise HTTPException(status_code=404, detail="Node not found") from error
    except NodeAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail="Node name already exists") from error


NodeServiceDependency = Annotated[NodeService, Depends(get_node_service)]


@router.post("", response_model=ComputeNodeResponse, status_code=201)
async def create_node(
    data: ComputeNodeCreate, service: NodeServiceDependency
) -> ComputeNodeResponse:
    return ComputeNodeResponse.from_node(await service.create_node(data))


@router.get("", response_model=list[ComputeNodeResponse])
async def list_nodes(service: NodeServiceDependency) -> list[ComputeNodeResponse]:
    return [ComputeNodeResponse.from_node(node) for node in await service.list_nodes()]


@router.get("/{node_id}", response_model=ComputeNodeResponse)
async def get_node(node_id: UUID, service: NodeServiceDependency) -> ComputeNodeResponse:
    return ComputeNodeResponse.from_node(await service.get_node(node_id))


@router.patch("/{node_id}", response_model=ComputeNodeResponse)
async def update_node(
    node_id: UUID, data: ComputeNodeUpdate, service: NodeServiceDependency
) -> ComputeNodeResponse:
    return ComputeNodeResponse.from_node(await service.update_node(node_id, data))


async def get_node_observation_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> NodeObservationService:
    return NodeObservationService(
        session, request.app.state.agent_client, request.app.state.secret_provider
    )


@router.post("/{node_id}/refresh", response_model=ComputeNodeResponse)
async def refresh_node(
    node_id: UUID,
    service: Annotated[NodeObservationService, Depends(get_node_observation_service)],
) -> ComputeNodeResponse:
    try:
        node = await service.refresh_node(node_id)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail="Node not found") from None
    except AgentError as error:
        status_code = (
            502 if isinstance(error, (AgentAuthenticationError, AgentResponseError)) else 503
        )
        raise HTTPException(status_code=status_code, detail=error.message) from None
    return ComputeNodeResponse.from_node(node)
