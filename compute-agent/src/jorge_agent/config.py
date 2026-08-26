from dataclasses import dataclass
from pathlib import Path


_ROOT = Path(
    "/srv/mc-iaas"
)


@dataclass(frozen=True)
class LibvirtConfig:
    uri: str = "qemu:///system"

    network_name: str = "mc-net"

    image_pool: str = "mc-images"
    instance_pool: str = "mc-instances"
    volume_pool: str = "mc-volumes"


@dataclass(frozen=True)
class StorageConfig:
    root: Path = _ROOT

    base_image: Path = (
        _ROOT
        / "storage/images/ubuntu-24.04-minimal-base.qcow2"
    )

    system_disk_bytes: int = (
        10 * 1024**3
    )

    data_disk_bytes: int = (
        5 * 1024**3
    )

@dataclass(frozen=True)
class QuotaConfig:
    min_memory_mb: int = 512
    default_memory_mb: int = 2048
    max_memory_mb: int = 2048

    min_vcpus: int = 1
    default_vcpus: int = 1
    max_vcpus: int = 1

@dataclass(frozen=True)
class NetworkConfig:
    internal_minecraft_port: int = 25565
    rcon_port: int = 25575

    port_forward_config: Path = (
        _ROOT
        / "config/port-forwards.conf"
    )

    firewall_script: Path = (
        _ROOT
        / "scripts/apply-firewall.sh"
    )

    dhcp_release_script: Path = (
        _ROOT
        / "scripts/release-dhcp-lease.sh"
    )


@dataclass(frozen=True)
class PathsConfig:
    cloud_init_root: Path = (
        _ROOT / "cloud-init"
    )

    metadata_dir: Path = (
        _ROOT / "metadata"
    )

    secrets_dir: Path = (
        _ROOT / "secrets"
    )

    run_dir: Path = (
        _ROOT / "run"
    )

    lock_dir: Path = (
        _ROOT / "run/locks"
    )


@dataclass(frozen=True)
class RuntimeSlot:
    slot: int
    ip: str
    external_port: int


RUNTIME_SLOTS = (
    RuntimeSlot(
        slot=1,
        ip="10.50.0.10",
        external_port=25565,
    ),
    RuntimeSlot(
        slot=2,
        ip="10.50.0.11",
        external_port=25566,
    ),
    RuntimeSlot(
        slot=3,
        ip="10.50.0.12",
        external_port=25567,
    ),
    RuntimeSlot(
        slot=4,
        ip="10.50.0.13",
        external_port=25568,
    ),
)

MAX_ACTIVE_INSTANCES = len(RUNTIME_SLOTS)

LIBVIRT = LibvirtConfig()
STORAGE = StorageConfig()
NETWORK = NetworkConfig()
PATHS = PathsConfig()
QUOTAS = QuotaConfig()