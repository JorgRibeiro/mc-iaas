from enum import Enum

from pydantic import BaseModel, Field, SecretStr, field_validator


RESERVED_USERNAMES = {
    "root",
    "minecraft",
    "libvirt-qemu",
}


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

    vm_username: str = Field(
        min_length=1,
        max_length=32,
        pattern=r"^[a-z_][a-z0-9_-]*$",
    )

    vm_password: SecretStr | None = None

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

    @field_validator("vm_username")
    @classmethod
    def validate_vm_username(cls, username: str) -> str:
        if username in RESERVED_USERNAMES:
            raise ValueError(
                f"username '{username}' is reserved by the platform"
            )

        return username

    @field_validator("vm_password")
    @classmethod
    def validate_vm_password(
        cls,
        password: SecretStr | None,
    ) -> SecretStr | None:
        if password is None:
            return None

        raw_password = password.get_secret_value()

        if len(raw_password) < 12:
            raise ValueError(
                "password must contain at least 12 characters"
            )

        return password


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


class InstanceCreateResponse(BaseModel):
    name: str
    state: InstanceState

    vm_username: str
    memory_mb: int
    vcpus: int
    minecraft_version: str

    runtime: RuntimeAllocation | None = None

    # Só é preenchido quando o agente gera a senha.
    generated_password: str | None = None

class InstanceActionResponse(BaseModel):
    name: str
    state: InstanceState
    runtime: RuntimeAllocation | None = None

class InstanceDeleteResponse(BaseModel):
    name: str
    deleted: bool
    data_preserved: bool
    data_volume: str | None = None

class InstanceDetailResponse(BaseModel):
    name: str
    state: InstanceState

    vm_username: str
    memory_mb: int
    vcpus: int
    minecraft_version: str

    runtime: RuntimeAllocation | None = None