"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application-wide resources."""
    yield
    await engine.dispose()


app = FastAPI(
    title="MC-IaaS Control Plane",
    description="Control Plane API for the MC-IaaS distributed infrastructure platform",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router)
