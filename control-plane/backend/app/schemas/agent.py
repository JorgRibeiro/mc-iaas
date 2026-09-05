"""Subset of the real /node/snapshot contract consumed by the Control Plane."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="ignore")


class AgentInfo(AgentContract):
    version: Annotated[str, Field(min_length=1, max_length=100)]


class AgentCapacity(AgentContract):
    max_active_instances: Annotated[int, Field(strict=True, ge=0)]
    active_instances: Annotated[int, Field(strict=True, ge=0)]
    occupied_runtime_slots: Annotated[int, Field(strict=True, ge=0)]
    available_slots: Annotated[int, Field(strict=True, ge=0)]


class AgentNodeHealth(AgentContract):
    status: Literal["healthy", "degraded", "unhealthy"]
    ready: Annotated[bool, Field(strict=True)]
    capacity: AgentCapacity


class AgentSnapshot(AgentContract):
    generated_at: AwareDatetime
    agent: AgentInfo
    node_health: AgentNodeHealth | None = None
    errors: dict[str, str] = Field(default_factory=dict)
