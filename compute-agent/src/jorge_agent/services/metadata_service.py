import json
from pathlib import Path

from jorge_agent.schemas.instance import InstanceCreate


METADATA_DIR = Path("/srv/mc-iaas/metadata")


def metadata_path(name: str) -> Path:
    return METADATA_DIR / f"{name}.json"


def metadata_exists(name: str) -> bool:
    return metadata_path(name).exists()


def save_instance_metadata(instance: InstanceCreate, data_volume: str) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "name": instance.name,
        "minecraft_version": instance.minecraft_version,
        "memory_mb": instance.memory_mb,
        "vcpus": instance.vcpus,
        "data_volume": data_volume,
    }

    path = metadata_path(instance.name)

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def load_instance_metadata(name: str) -> dict:
    path = metadata_path(name)

    if not path.exists():
        raise FileNotFoundError(
            f"Metadata da instância '{name}' não encontrada"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def delete_instance_metadata(name: str) -> None:
    path = metadata_path(name)

    if path.exists():
        path.unlink()
