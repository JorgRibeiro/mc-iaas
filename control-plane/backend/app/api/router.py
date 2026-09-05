"""Top-level API router."""

from fastapi import APIRouter

from app.api.activity import router as activity_router
from app.api.health import router as health_router
from app.api.instances import router as instances_router
from app.api.nodes import router as nodes_router
from app.api.operations import router as operations_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(nodes_router)
v1_router.include_router(activity_router)
v1_router.include_router(instances_router)
v1_router.include_router(operations_router)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router)
