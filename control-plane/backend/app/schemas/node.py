"""Administrative Node inputs and public representation."""

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
    field_validator,
)

from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability

NonEmptyName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]
_http_url = TypeAdapter(HttpUrl)


def normalize_endpoint(value: object) -> str:
    url = _http_url.validate_python(value)
    if url.username is not None or url.password is not None or url.query or url.fragment:
        raise ValueError("endpoint must not contain credentials, query parameters or fragments")
    endpoint = str(url).rstrip("/")
    if len(endpoint) > 2048:
        raise ValueError("endpoint must be at most 2048 characters")
    return endpoint


Endpoint = Annotated[str, BeforeValidator(normalize_endpoint)]


class ComputeNodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyName
    endpoint: Endpoint
    credential_ref: NonEmptyName
    enabled: bool = True


class ComputeNodeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyName | None = None
    endpoint: Endpoint | None = None
    credential_ref: NonEmptyName | None = None
    enabled: bool | None = None

    @field_validator("name", "endpoint", "credential_ref", "enabled", mode="before")
    @classmethod
    def reject_explicit_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null; omit it to leave it unchanged")
        return value


class NodeCapacity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    max_active_instances: int | None
    active_instances: int | None
    occupied_runtime_slots: int | None
    available_slots: int | None


class CpuMetrics(BaseModel):
    usage_percent: float | None


class ResourceMetrics(BaseModel):
    total_bytes: int | None
    used_bytes: int | None
    available_bytes: int | None
    usage_percent: float | None


class NodeMetrics(BaseModel):
    cpu: CpuMetrics
    memory: ResourceMetrics
    storage: ResourceMetrics


class ComponentHealth(BaseModel):
    libvirt: bool | None
    network: bool | None
    storage: bool | None
    invariants: bool | None


class ComputeNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    endpoint: str
    enabled: bool
    reachability: NodeReachability
    observed_health: NodeHealth
    observed_ready: bool | None
    last_seen_at: datetime | None
    last_observed_at: datetime | None
    agent_version: str | None
    agent_uptime_seconds: float | None
    metrics_observed_at: datetime | None
    metrics: NodeMetrics
    health: ComponentHealth
    invariants_details: str | None
    capacity: NodeCapacity
    consecutive_failures: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_node(cls, node: ComputeNode) -> Self:
        values = {
            name: getattr(node, name)
            for name in cls.model_fields
            if name not in {"capacity", "metrics", "health"}
        }
        return cls.model_validate(
            {
                **values,
                "capacity": NodeCapacity.model_validate(node),
                "health": {
                    c: getattr(node, f"{c}_health")
                    for c in ("libvirt", "network", "storage", "invariants")
                },
                "metrics": {
                    "cpu": {"usage_percent": node.cpu_usage_percent},
                    **{
                        group: {
                            field: getattr(node, f"{group}_{field}")
                            for field in (
                                "total_bytes",
                                "used_bytes",
                                "available_bytes",
                                "usage_percent",
                            )
                        }
                        for group in ("memory", "storage")
                    },
                },
            }
        )
