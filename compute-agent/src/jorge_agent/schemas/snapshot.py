from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from jorge_agent.schemas.agent import (
    AgentStatusResponse,
)
from jorge_agent.schemas.host import (
    HostMetricsResponse,
)
from jorge_agent.schemas.instance import (
    InstanceSummaryResponse,
)
from jorge_agent.schemas.node import (
    NodeHealthResponse,
)


class SnapshotInstanceResponse(InstanceSummaryResponse):
    minecraft_status: Literal["online", "offline", "unavailable", "unknown"] = "unknown"


class NodeSnapshotResponse(BaseModel):
    generated_at: datetime

    agent: AgentStatusResponse

    node_health: NodeHealthResponse | None = None
    node_metrics: HostMetricsResponse | None = None

    instances: list[SnapshotInstanceResponse] | None = None

    errors: dict[str, str]
