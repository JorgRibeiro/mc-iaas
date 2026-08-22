import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml
from passlib.hash import sha512_crypt

from jorge_agent.schemas.instance import InstanceCreate
from jorge_agent.services.credential_service import ResolvedCredential


CLOUD_INIT_ROOT = Path("/srv/mc-iaas/cloud-init")


@dataclass(frozen=True)
class CloudInitArtifacts:
    directory: str
    user_data: str
    meta_data: str
    seed: str


def _hash_password(password: str) -> str:
    return sha512_crypt.hash(password)


def _build_user_data(
    instance: InstanceCreate,
    credential: ResolvedCredential,
) -> dict:
    password_hash = _hash_password(credential.password)

    return {
        "hostname": instance.name,
        "manage_etc_hosts": True,
        "disable_root": True,
        "ssh_pwauth": True,
        "users": [
            {
                "name": credential.username,
                "groups": "adm,sudo",
                "shell": "/bin/bash",
                "sudo": "ALL=(ALL) ALL",
                "lock_passwd": False,
                "passwd": password_hash,
            }
        ],
        "packages": [
            "openjdk-25-jre-headless",
            "curl",
        ],
        "runcmd": [
            [
                "sh",
                "-c",
                "getent group minecraft >/dev/null "
                "|| groupadd -g 2000 minecraft",
            ],
            [
                "sh",
                "-c",
                "id minecraft >/dev/null 2>&1 "
                "|| useradd -u 2000 -g 2000 "
                "-d /srv/minecraft "
                "-s /usr/sbin/nologin "
                "-M minecraft",
            ],
        ],
        "final_message": "MC-IaaS cloud-init completed",
    }


def create_cloud_init_artifacts(
    instance: InstanceCreate,
    credential: ResolvedCredential,
) -> CloudInitArtifacts:
    if shutil.which("cloud-localds") is None:
        raise RuntimeError(
            "cloud-localds is not installed"
        )

    instance_dir = CLOUD_INIT_ROOT / instance.name

    if instance_dir.exists():
        raise FileExistsError(
            f"Cloud-init directory already exists: {instance_dir}"
        )

    instance_dir.mkdir(
        parents=True,
        mode=0o750,
    )

    user_data_path = instance_dir / "user-data"
    meta_data_path = instance_dir / "meta-data"
    seed_path = instance_dir / "seed.img"

    try:
        user_data = _build_user_data(
            instance,
            credential,
        )

        user_data_text = (
            "#cloud-config\n"
            + yaml.safe_dump(
                user_data,
                sort_keys=False,
                allow_unicode=True,
            )
        )

        meta_data = {
            "instance-id": instance.name,
            "local-hostname": instance.name,
        }

        meta_data_text = yaml.safe_dump(
            meta_data,
            sort_keys=False,
        )

        user_data_path.write_text(
            user_data_text,
            encoding="utf-8",
        )

        meta_data_path.write_text(
            meta_data_text,
            encoding="utf-8",
        )

        subprocess.run(
            [
                "cloud-localds",
                str(seed_path),
                str(user_data_path),
                str(meta_data_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        user_data_path.chmod(0o600)
        meta_data_path.chmod(0o644)
        seed_path.chmod(0o644)

        return CloudInitArtifacts(
            directory=str(instance_dir),
            user_data=str(user_data_path),
            meta_data=str(meta_data_path),
            seed=str(seed_path),
        )

    except Exception:
        shutil.rmtree(
            instance_dir,
            ignore_errors=True,
        )
        raise


def delete_cloud_init_artifacts(name: str) -> None:
    instance_dir = CLOUD_INIT_ROOT / name

    if instance_dir.exists():
        shutil.rmtree(instance_dir)
