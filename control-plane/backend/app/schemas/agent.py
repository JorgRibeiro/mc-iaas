"""Subset of the real /node/snapshot contract consumed by the Control Plane."""

from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.models.enums import MinecraftStatus


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


class AgentRuntime(AgentContract):
    slot: Annotated[int, Field(strict=True, ge=0)] | None = None
    ip: Annotated[str, Field(max_length=45)] | None = None
    external_port: Annotated[int, Field(strict=True, ge=1, le=65535)] | None = None


class AgentInstance(AgentContract):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    state: str
    runtime: AgentRuntime | None = None
    # Not currently sent by InstanceSummaryResponse; preserve it when absent.
    minecraft_status: MinecraftStatus | None = None


class AgentSnapshot(AgentContract):
    generated_at: AwareDatetime
    agent: AgentInfo
    node_health: AgentNodeHealth | None = None
    errors: dict[str, str] = Field(default_factory=dict)

    instances: list[AgentInstance] | None = None

    @model_validator(mode="after")
    def reject_ambiguous_inventory(self) -> Self:
        if self.instances is not None:
            names = [instance.name for instance in self.instances]
            if len(names) != len(set(names)):
                self.instances = None
                self.errors = {**self.errors, "instances": "Ambiguous instance inventory"}
        return self


class AgentActionResult(AgentContract):
    name: str
    state: Literal["running", "stopped", "paused", "starting", "stopping", "error", "unknown"]
    runtime: AgentRuntime | None = None


class AgentDeleteResult(AgentContract):
    name: str
    deleted: Annotated[bool, Field(strict=True)]
    data_preserved: Annotated[bool, Field(strict=True)]
