import json
import os
import secrets

from dataclasses import dataclass
from pathlib import Path

from jorge_agent.config import PATHS


@dataclass(frozen=True)
class InstanceSecrets:
    rcon_password: str


def secret_path(name: str) -> Path:
    return PATHS.secrets_dir / f"{name}.json"


def create_instance_secrets(
    name: str,
) -> InstanceSecrets:
    PATHS.secrets_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    PATHS.secrets_dir.chmod(0o700)

    path = secret_path(name)

    if path.exists():
        raise FileExistsError(
            f"Secrets already exist: {name}"
        )

    rcon_password = secrets.token_urlsafe(24)

    data = {
        "rcon_password": rcon_password,
    }

    fd = os.open(
        path,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL,
        0o600,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
            )

    except Exception:
        path.unlink(
            missing_ok=True
        )
        raise

    return InstanceSecrets(
        rcon_password=rcon_password,
    )


def load_instance_secrets(
    name: str,
) -> InstanceSecrets:
    path = secret_path(name)

    if not path.exists():
        raise FileNotFoundError(
            f"Secrets not found: {name}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return InstanceSecrets(
        rcon_password=data[
            "rcon_password"
        ],
    )


def delete_instance_secrets(
    name: str,
) -> None:
    secret_path(name).unlink(
        missing_ok=True
    )
