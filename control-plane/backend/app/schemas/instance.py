"""Public Instance contracts; no credentials or caller-controlled placement."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

from app.models.enums import DesiredInstanceState, MinecraftStatus, ObservedInstanceState


class InstanceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        str, StringConstraints(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    ]
    memory_mb: Annotated[int, Field(strict=True, ge=512, le=2048)] = 2048
    vcpus: Annotated[int, Field(strict=True, ge=1, le=1)] = 1
    minecraft_version: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ] = "26.2"
    vm_username: Annotated[
        str, StringConstraints(min_length=1, max_length=32, pattern=r"^[a-z_][a-z0-9_-]*$")
    ]
    accept_eula: Annotated[bool, Field(strict=True)]

    @field_validator("vm_username")
    @classmethod
    def non_reserved_username(cls, value: str) -> str:
        if value in {"root", "minecraft", "libvirt-qemu"}:
            raise ValueError("Reserved VM username")
        return value

    @field_validator("accept_eula")
    @classmethod
    def explicit_eula(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Minecraft EULA must be explicitly accepted")
        return value


class InstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    compute_node_id: UUID | None
    desired_state: DesiredInstanceState
    observed_state: ObservedInstanceState
    memory_mb: int
    vcpus: int
    minecraft_version: str
    vm_username: str | None = None
    observed_runtime_slot: int | None
    observed_runtime_ip: str | None
    observed_external_port: int | None
    minecraft_status: MinecraftStatus
    last_observed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    display_state: str = "unknown"
    active_operation: "ActiveOperationSummary | None" = None

    @computed_field
    @property
    def resources(self) -> dict[str, int]:
        return {"memory_mb": self.memory_mb, "vcpus": self.vcpus}

    @computed_field
    @property
    def runtime(self) -> dict | None:
        if all(
            value is None
            for value in (
                self.observed_runtime_slot,
                self.observed_runtime_ip,
                self.observed_external_port,
            )
        ):
            return None
        return {
            "slot": self.observed_runtime_slot,
            "ip": self.observed_runtime_ip,
            "external_port": self.observed_external_port,
        }


class ActiveOperationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    type: str
    status: str


InstanceResponse.model_rebuild()
