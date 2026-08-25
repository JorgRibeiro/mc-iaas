import json
from pathlib import Path

from jorge_agent.config import PATHS
from jorge_agent.schemas.instance import InstanceCreate
from datetime import datetime, timezone

def metadata_path(name: str) -> Path:
    return PATHS.metadata_dir / f"{name}.json"


def metadata_exists(name: str) -> bool:
    return metadata_path(name).exists()


def save_instance_metadata(instance: InstanceCreate, data_volume: str) -> None:
    PATHS.metadata_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "name": instance.name,
        "vm_username": instance.vm_username,
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

def mark_instance_deleted(name: str) -> None:
    data = load_instance_metadata(name)

    data["deleted"] = True
    data["data_preserved"] = True
    data["deleted_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    metadata_path(name).write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
