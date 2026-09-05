"""Current state aggregations, with nullable unknown capacity."""

from uuid import UUID

from pydantic import BaseModel

from app.schemas.node import ComputeNodeResponse


class CapacitySummary(BaseModel):
    total_runtime_slots: int | None
    occupied_runtime_slots: int | None
    available_runtime_slots: int | None


class OverviewResponse(CapacitySummary):
    infrastructure_status: str
    total_nodes: int
    online_nodes: int
    healthy_nodes: int
    total_instances: int
    running_instances: int
    stopped_instances: int
    unavailable_instances: int
    open_critical_conditions: int


class Condition(BaseModel):
    code: str
    node_id: UUID | None
    instance_id: UUID | None


class MonitoringResponse(BaseModel):
    overview: OverviewResponse
    node_health_distribution: dict[str, int]
    instance_state_distribution: dict[str, int]
    capacity: CapacitySummary
    conditions: list[Condition]
    nodes: list[ComputeNodeResponse]
    historical_metrics_available: bool
    timeseries: list = []
