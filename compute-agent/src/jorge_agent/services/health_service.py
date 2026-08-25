import socket

import libvirt

from jorge_agent.config import LIBVIRT, NETWORK
from jorge_agent.schemas.instance import (
    InstanceHealthResponse,
    MinecraftState,
)

from jorge_agent.services.libvirt_service import (
    map_domain_state,
)

from jorge_agent.services.runtime_service import (
    get_instance_runtime,
)


TCP_TIMEOUT_SECONDS = 1.0


def _find_domain(
    conn: libvirt.virConnect,
    name: str,
) -> libvirt.virDomain | None:
    for domain in conn.listAllDomains():
        if domain.name() == name:
            return domain

    return None


def _minecraft_port_open(
    ip: str,
) -> bool:
    try:
        with socket.create_connection(
            (ip, NETWORK.internal_minecraft_port),
            timeout=TCP_TIMEOUT_SECONDS,
        ):
            return True

    except (
        TimeoutError,
        ConnectionRefusedError,
        OSError,
    ):
        return False


def get_instance_health(
    name: str,
) -> InstanceHealthResponse:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domain = _find_domain(
            conn,
            name,
        )

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        instance_state = map_domain_state(
            domain.info()[0]
        )

        runtime = get_instance_runtime(name)

        if not domain.isActive():
            return InstanceHealthResponse(
                name=name,
                instance_state=instance_state,
                minecraft_state=MinecraftState.STOPPED,
                runtime=None,
            )

        if runtime is None:
            return InstanceHealthResponse(
                name=name,
                instance_state=instance_state,
                minecraft_state=MinecraftState.UNAVAILABLE,
                runtime=None,
            )

        minecraft_online = _minecraft_port_open(
            runtime.ip
        )

        minecraft_state = (
            MinecraftState.ONLINE
            if minecraft_online
            else MinecraftState.UNAVAILABLE
        )

        return InstanceHealthResponse(
            name=name,
            instance_state=instance_state,
            minecraft_state=minecraft_state,
            runtime=runtime,
        )

    finally:
        conn.close()
