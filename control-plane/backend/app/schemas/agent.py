"""Subset of the real /node/snapshot contract consumed by the Control Plane."""

from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.models.enums import MinecraftStatus


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="ignore")


Percent = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Bytes = Annotated[int, Field(strict=True, ge=0)]


class AgentInfo(AgentContract):
    version: Annotated[str, Field(min_length=1, max_length=100)]
    uptime_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None


class AgentCapacity(AgentContract):
    max_active_instances: Annotated[int, Field(strict=True, ge=0)] | None = None
    active_instances: Annotated[int, Field(strict=True, ge=0)] | None = None
    occupied_runtime_slots: Annotated[int, Field(strict=True, ge=0)] | None = None
    available_slots: Annotated[int, Field(strict=True, ge=0)] | None = None


class AgentComponentHealth(AgentContract):
    healthy: Annotated[bool, Field(strict=True)] | None = None
    detail: Annotated[str, Field(max_length=16384)] | None = None


class AgentNodeHealth(AgentContract):
    status: Literal["healthy", "degraded", "unhealthy"] | None = None
    ready: Annotated[bool, Field(strict=True)] | None = None
    capacity: AgentCapacity | None = None
    libvirt: AgentComponentHealth | None = None
    network: AgentComponentHealth | None = None
    storage: AgentComponentHealth | None = None
    invariants: AgentComponentHealth | None = None


class AgentCpu(AgentContract):
    usage_percent: Percent | None = None


class AgentMemory(AgentContract):
    total_bytes: Bytes | None = None
    used_bytes: Bytes | None = None
    available_bytes: Bytes | None = None
    usage_percent: Percent | None = None


class AgentDisk(AgentContract):
    total_bytes: Bytes | None = None
    used_bytes: Bytes | None = None
    free_bytes: Bytes | None = None
    usage_percent: Percent | None = None


class AgentMetrics(AgentContract):
    cpu: AgentCpu | None = None
    memory: AgentMemory | None = None
    mc_iaas_disk: AgentDisk | None = None


class AgentRuntime(AgentContract):
    slot: Annotated[int, Field(strict=True, ge=0)] | None = None
    ip: Annotated[str, Field(max_length=45)] | None = None
    external_port: Annotated[int, Field(strict=True, ge=1, le=65535)] | None = None


class AgentInstance(AgentContract):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    state: str
    runtime: AgentRuntime | None = None
    # Older Agents omit this field; preserve the last observation in that case.
    minecraft_status: MinecraftStatus | None = None


class AgentSnapshot(AgentContract):
    generated_at: AwareDatetime
    agent: AgentInfo
    node_health: AgentNodeHealth | None = None
    node_metrics: AgentMetrics | None = None
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
