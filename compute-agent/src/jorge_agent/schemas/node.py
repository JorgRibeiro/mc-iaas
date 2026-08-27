from enum import Enum

from pydantic import BaseModel


class NodeStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class NodeComponentHealth(BaseModel):
    healthy: bool
    detail: str | None = None


class NodeCapacity(BaseModel):
    max_active_instances: int
    active_instances: int
    occupied_runtime_slots: int
    available_slots: int


class NodeHealthResponse(BaseModel):
    status: NodeStatus
    ready: bool

    libvirt: NodeComponentHealth
    network: NodeComponentHealth
    storage: NodeComponentHealth
    invariants: NodeComponentHealth

    capacity: NodeCapacity
