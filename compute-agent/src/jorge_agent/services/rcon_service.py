import socket
import struct

from jorge_agent.config import NETWORK
from jorge_agent.services.runtime_service import (
    get_instance_runtime,
)
from jorge_agent.services.secret_service import (
    load_instance_secrets,
)


SERVERDATA_RESPONSE_VALUE = 0
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_AUTH = 3


class RconError(RuntimeError):
    pass


def _recv_exact(
    sock: socket.socket,
    size: int,
) -> bytes:
    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(
            size - len(data)
        )

        if not chunk:
            raise RconError(
                "RCON connection closed unexpectedly"
            )

        data.extend(chunk)

    return bytes(data)


def _send_packet(
    sock: socket.socket,
    request_id: int,
    packet_type: int,
    payload: str,
) -> None:
    body = (
        struct.pack(
            "<ii",
            request_id,
            packet_type,
        )
        + payload.encode("utf-8")
        + b"\x00\x00"
    )

    packet = (
        struct.pack(
            "<i",
            len(body),
        )
        + body
    )

    sock.sendall(packet)


def _receive_packet(
    sock: socket.socket,
) -> tuple[int, int, str]:
    raw_length = _recv_exact(
        sock,
        4,
    )

    length = struct.unpack(
        "<i",
        raw_length,
    )[0]

    if length < 10:
        raise RconError(
            "Invalid RCON packet length"
        )

    body = _recv_exact(
        sock,
        length,
    )

    request_id, packet_type = (
        struct.unpack(
            "<ii",
            body[:8],
        )
    )

    payload = body[8:-2].decode(
        "utf-8",
        errors="replace",
    )

    return (
        request_id,
        packet_type,
        payload,
    )


def execute_rcon_command(
    name: str,
    command: str,
) -> str:
    runtime = get_instance_runtime(
        name
    )

    if runtime is None or runtime.ip is None:
        raise RconError(
            f"Instance has no active runtime: {name}"
        )

    secrets = load_instance_secrets(
        name
    )

    with socket.create_connection(
        (
            runtime.ip,
            NETWORK.rcon_port,
        ),
        timeout=3,
    ) as sock:
        sock.settimeout(3)

        auth_id = 1

        _send_packet(
            sock,
            auth_id,
            SERVERDATA_AUTH,
            secrets.rcon_password,
        )

        (
            response_id,
            response_type,
            _,
        ) = _receive_packet(sock)

        if response_id == -1:
            raise RconError(
                "RCON authentication failed"
            )

        if (
            response_id != auth_id
            or response_type
            != SERVERDATA_AUTH_RESPONSE
        ):
            raise RconError(
                "Unexpected RCON authentication response"
            )

        command_id = 2

        _send_packet(
            sock,
            command_id,
            SERVERDATA_EXECCOMMAND,
            command,
        )

        (
            response_id,
            _,
            response,
        ) = _receive_packet(sock)

        if response_id != command_id:
            raise RconError(
                "Unexpected RCON command response"
            )

        return response
