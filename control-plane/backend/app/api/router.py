"""Top-level API router."""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.nodes import router as nodes_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(nodes_router)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router)
