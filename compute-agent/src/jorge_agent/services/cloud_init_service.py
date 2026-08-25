import shutil
import subprocess
from dataclasses import dataclass

import yaml
from passlib.hash import sha512_crypt

from jorge_agent.config import NETWORK, PATHS
from jorge_agent.schemas.instance import InstanceCreate
from jorge_agent.services.credential_service import ResolvedCredential


MINECRAFT_SERVER_URLS = {
    "26.2": {
        "url": (
            "https://piston-data.mojang.com/v1/objects/"
            "823e2250d24b3ddac457a60c92a6a941943fcd6a/server.jar"
        ),
        "sha1": "823e2250d24b3ddac457a60c92a6a941943fcd6a",
    }
}

@dataclass(frozen=True)
class CloudInitArtifacts:
    directory: str
    user_data: str
    meta_data: str
    seed: str


def _hash_password(password: str) -> str:
    return sha512_crypt.hash(password)

def _minecraft_bootstrap_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

CONF="/etc/mc-iaas-minecraft.conf"
DATA_DIR="/srv/minecraft"

source "$CONF"

if [ "$EULA_ACCEPTED" != "true" ]; then
    echo "Minecraft EULA was not accepted."
    exit 1
fi

mkdir -p "$DATA_DIR"

if [ -f "$DATA_DIR/server.jar" ]; then
    if ! echo "${SERVER_JAR_SHA1}  ${DATA_DIR}/server.jar" | sha1sum -c - >/dev/null 2>&1; then
        rm -f "$DATA_DIR/server.jar"
    fi
fi

if [ ! -f "$DATA_DIR/server.jar" ]; then
    curl -fL "$SERVER_JAR_URL" -o "$DATA_DIR/server.jar"
    echo "${SERVER_JAR_SHA1}  ${DATA_DIR}/server.jar" | sha1sum -c -
fi

echo "eula=true" > "$DATA_DIR/eula.txt"

PROPERTIES="$DATA_DIR/server.properties"

touch "$PROPERTIES"

sed -i \
    -e '/^enable-rcon=/d' \
    -e '/^rcon\.port=/d' \
    -e '/^rcon\.password=/d' \
    -e '/^broadcast-rcon-to-ops=/d' \
    "$PROPERTIES"

{
    echo "enable-rcon=true"
    echo "rcon.port={rcon_port}"
    printf 'rcon.password=%s\n' "$RCON_PASSWORD"
    echo "broadcast-rcon-to-ops=false"
} >> "$PROPERTIES"

chmod 600 "$PROPERTIES"

chown -R 2000:2000 "$DATA_DIR"
""".replace(
        "{rcon_port}",
        str(NETWORK.rcon_port),
    )


def _minecraft_systemd_service() -> str:
    return """[Unit]
Description=MC-IaaS Minecraft Server
Wants=network-online.target
After=network-online.target
RequiresMountsFor=/srv/minecraft

[Service]
Type=simple
User=minecraft
Group=minecraft
WorkingDirectory=/srv/minecraft
EnvironmentFile=/etc/mc-iaas-minecraft.conf
ExecStartPre=+/usr/local/sbin/bootstrap-minecraft
ExecStart=/usr/bin/java -Xms512M -Xmx1500M -jar /srv/minecraft/server.jar nogui
Restart=on-failure
RestartSec=10
SuccessExitStatus=0 143

[Install]
WantedBy=multi-user.target
"""

def _build_user_data(
    instance: InstanceCreate,
    credential: ResolvedCredential,
    rcon_password: str,
) -> dict:
    password_hash = _hash_password(credential.password)

    minecraft_release = MINECRAFT_SERVER_URLS.get(
        instance.minecraft_version
    )

    if minecraft_release is None:
        raise ValueError(
            f"Unsupported Minecraft version: "
            f"{instance.minecraft_version}"
        )

    minecraft_config = (
        f'MINECRAFT_VERSION="{instance.minecraft_version}"\n'
        f'SERVER_JAR_URL="{minecraft_release["url"]}"\n'
        f'SERVER_JAR_SHA1="{minecraft_release["sha1"]}"\n'
        f'EULA_ACCEPTED="{str(instance.accept_eula).lower()}"\n'
        f'RCON_PASSWORD="{rcon_password}"\n'
    )

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

        "write_files": [
            {
                "path": "/etc/mc-iaas-minecraft.conf",
                "permissions": "0600",
                "content": minecraft_config,
            },
            {
                "path": "/usr/local/sbin/bootstrap-minecraft",
                "permissions": "0755",
                "content": _minecraft_bootstrap_script(),
            },
            {
                "path": "/etc/systemd/system/minecraft.service",
                "permissions": "0644",
                "content": _minecraft_systemd_service(),
            },
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

            [
                "sh",
                "-c",
                "mkdir -p /srv/minecraft",
            ],

            [
                "sh",
                "-c",
                "blkid /dev/vdc >/dev/null 2>&1 "
                "|| mkfs.ext4 -F -L minecraft-data /dev/vdc",
            ],

            [
                "sh",
                "-c",
                'UUID="$(blkid -s UUID -o value /dev/vdc)" && '
                'grep -q "$UUID" /etc/fstab '
                '|| echo "UUID=$UUID /srv/minecraft ext4 defaults,nofail 0 2" '
                ">> /etc/fstab",
            ],

            [
                "sh",
                "-c",
                "mountpoint -q /srv/minecraft "
                "|| mount /srv/minecraft",
            ],

            [
                "sh",
                "-c",
                "chown 2000:2000 /srv/minecraft",
            ],

            [
                "systemctl",
                "daemon-reload",
            ],

            [
                "systemctl",
                "enable",
                "--now",
                "minecraft.service",
            ],
        ],

        "final_message": "MC-IaaS Minecraft bootstrap completed",
    }


def create_cloud_init_artifacts(
    instance: InstanceCreate,
    credential: ResolvedCredential,
    rcon_password: str,
) -> CloudInitArtifacts:
    if shutil.which("cloud-localds") is None:
        raise RuntimeError(
            "cloud-localds is not installed"
        )

    instance_dir = PATHS.cloud_init_root / instance.name

    if instance_dir.exists():
        raise FileExistsError(
            f"Cloud-init directory already exists: {instance_dir}"
        )

    instance_dir.mkdir(
    parents=True,
    mode=0o755,
    )

    instance_dir.chmod(0o755)

    user_data_path = instance_dir / "user-data"
    meta_data_path = instance_dir / "meta-data"
    seed_path = instance_dir / "seed.img"

    try:
        user_data = _build_user_data(
            instance,
            credential,
            rcon_password,
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
    instance_dir = PATHS.cloud_init_root / name

    if instance_dir.exists():
        shutil.rmtree(instance_dir)
