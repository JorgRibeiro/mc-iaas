import hashlib
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from pathlib import Path

import libvirt


LIBVIRT_URI = "qemu:///system"
NETWORK_NAME = "mc-net"

PORT_FORWARD_CONFIG = Path(
    "/srv/mc-iaas/config/port-forwards.conf"
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


def instance_mac(name: str) -> str:
    digest = hashlib.sha256(
        name.encode("utf-8")
    ).digest()

    return (
        "52:54:00:"
        f"{digest[0]:02x}:"
        f"{digest[1]:02x}:"
        f"{digest[2]:02x}"
    )


def _get_reserved_ips() -> set[str]:
    conn = libvirt.open(LIBVIRT_URI)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        network = conn.networkLookupByName(
            NETWORK_NAME
        )

        root = ET.fromstring(
            network.XMLDesc(0)
        )

        reserved_ips = set()

        for host in root.findall(".//dhcp/host"):
            ip = host.get("ip")

            if ip:
                reserved_ips.add(ip)

        return reserved_ips

    finally:
        conn.close()


def _get_forwarded_ports() -> set[int]:
    if not PORT_FORWARD_CONFIG.exists():
        return set()

    ports = set()

    for raw_line in PORT_FORWARD_CONFIG.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        try:
            ports.add(int(parts[0]))

        except ValueError:
            continue

    return ports


def available_runtime_slots() -> list[RuntimeSlot]:
    reserved_ips = _get_reserved_ips()
    forwarded_ports = _get_forwarded_ports()

    available = []

    for slot in RUNTIME_SLOTS:
        if slot.ip in reserved_ips:
            continue

        if slot.external_port in forwarded_ports:
            continue

        available.append(slot)

    return available


def allocate_runtime_slot() -> RuntimeSlot:
    available = available_runtime_slots()

    if not available:
        raise RuntimeError(
            "No runtime slots available"
        )

    return available[0]
