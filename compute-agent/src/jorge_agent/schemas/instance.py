from enum import Enum

from pydantic import BaseModel, Field

class InstanceState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class InstanceCreate(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )

    memory_mb: int = Field(
        default=2048,
        ge=512,
        le=2048,
    )

    vcpus: int = Field(
        default=1,
        ge=1,
        le=1,
    )

    minecraft_version: str = "26.2"

    accept_eula: bool = False


class RuntimeAllocation(BaseModel):
    slot: int | None = None
    ip: str | None = None
    external_port: int | None = None


class InstanceResponse(BaseModel):
    name: str
    state: InstanceState

    memory_mb: int
    vcpus: int

    runtime: RuntimeAllocation | None = None
