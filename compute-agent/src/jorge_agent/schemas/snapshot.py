from datetime import datetime

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


class NodeSnapshotResponse(BaseModel):
    generated_at: datetime

    agent: AgentStatusResponse

    node_health: NodeHealthResponse | None = None
    node_metrics: HostMetricsResponse | None = None

    instances: list[InstanceSummaryResponse] | None = None

    errors: dict[str, str]
