"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import session as db_session

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Liveness response payload."""

    status: Literal["ok"]
    service: str


class ReadinessResponse(BaseModel):
    """Readiness response payload."""

    status: Literal["ready"]
    database: Literal["ok"]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report process liveness without checking external dependencies."""
    return HealthResponse(status="ok", service="mc-iaas-control-plane")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}},
)
async def ready() -> ReadinessResponse | JSONResponse:
    """Report whether the application can reach PostgreSQL."""
    try:
        await db_session.check_database_connectivity()
    except Exception:  # The HTTP boundary must not leak driver or connection details.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "unavailable"},
        )

    return ReadinessResponse(status="ready", database="ok")
