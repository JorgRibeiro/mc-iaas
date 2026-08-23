import hashlib
import xml.etree.ElementTree as ET
import subprocess

from jorge_agent.schemas.instance import RuntimeAllocation
from dataclasses import dataclass
from pathlib import Path

import libvirt


LIBVIRT_URI = "qemu:///system"
NETWORK_NAME = "mc-net"

PORT_FORWARD_CONFIG = Path(
    "/srv/mc-iaas/config/port-forwards.conf"
)

FIREWALL_SCRIPT = Path(
    "/srv/mc-iaas/scripts/apply-firewall.sh"
)

MINECRAFT_INTERNAL_PORT = 25565

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

def _find_domain(
    conn: libvirt.virConnect,
    name: str,
) -> libvirt.virDomain | None:
    for domain in conn.listAllDomains():
        if domain.name() == name:
            return domain

    return None


def _interface_xml(mac: str) -> str:
    return (
        "<interface type='network'>"
        f"<mac address='{mac}'/>"
        f"<source network='{NETWORK_NAME}'/>"
        "<model type='virtio'/>"
        "</interface>"
    )


def _dhcp_host_xml(
    name: str,
    mac: str,
    ip: str,
) -> str:
    host = ET.Element(
        "host",
        {
            "mac": mac,
            "name": name,
            "ip": ip,
        },
    )

    return ET.tostring(
        host,
        encoding="unicode",
    )


def _add_port_forward(slot: RuntimeSlot) -> None:
    if PORT_FORWARD_CONFIG.exists():
        lines = PORT_FORWARD_CONFIG.read_text(
            encoding="utf-8"
        ).splitlines()
    else:
        lines = [
            "# PORTA_EXTERNA  IP_INTERNO   PORTA_INTERNA"
        ]

    for raw_line in lines:
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split()

        if parts[0] == str(slot.external_port):
            raise RuntimeError(
                f"Port {slot.external_port} is already published"
            )

    lines.append(
        f"{slot.external_port} "
        f"{slot.ip} "
        f"{MINECRAFT_INTERNAL_PORT}"
    )

    PORT_FORWARD_CONFIG.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _remove_port_forward(slot: RuntimeSlot) -> None:
    if not PORT_FORWARD_CONFIG.exists():
        return

    result = []

    for raw_line in PORT_FORWARD_CONFIG.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if line and not line.startswith("#"):
            parts = line.split()

            if (
                len(parts) >= 1
                and parts[0] == str(slot.external_port)
            ):
                continue

        result.append(raw_line)

    PORT_FORWARD_CONFIG.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8",
    )


def _apply_firewall() -> None:
    result = subprocess.run(
        [
            "sudo",
            "-n",
            str(FIREWALL_SCRIPT),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Firewall update failed: "
            + result.stderr.strip()
        )


def prepare_instance_runtime(
    name: str,
) -> RuntimeAllocation:
    conn = libvirt.open(LIBVIRT_URI)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    interface_attached = False
    dhcp_added = False
    forward_added = False

    slot = None
    network = None
    domain = None
    interface_xml = None
    host_xml = None

    try:
        domain = _find_domain(conn, name)

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        if domain.isActive():
            raise RuntimeError(
                f"Instance is already active: {name}"
            )

        slot = allocate_runtime_slot()
        mac = instance_mac(name)

        network = conn.networkLookupByName(
            NETWORK_NAME
        )

        interface_xml = _interface_xml(mac)

        host_xml = _dhcp_host_xml(
            name,
            mac,
            slot.ip,
        )

        domain.attachDeviceFlags(
            interface_xml,
            libvirt.VIR_DOMAIN_AFFECT_CONFIG,
        )
        interface_attached = True

        network.update(
            libvirt.VIR_NETWORK_UPDATE_COMMAND_ADD_LAST,
            libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST,
            -1,
            host_xml,
            (
                libvirt.VIR_NETWORK_UPDATE_AFFECT_LIVE
                | libvirt.VIR_NETWORK_UPDATE_AFFECT_CONFIG
            ),
        )
        dhcp_added = True

        _add_port_forward(slot)
        forward_added = True

        _apply_firewall()

        return RuntimeAllocation(
            slot=slot.slot,
            ip=slot.ip,
            external_port=slot.external_port,
        )

    except Exception:
        if forward_added and slot is not None:
            try:
                _remove_port_forward(slot)
                _apply_firewall()
            except Exception:
                pass

        if (
            dhcp_added
            and network is not None
            and host_xml is not None
        ):
            try:
                network.update(
                    libvirt.VIR_NETWORK_UPDATE_COMMAND_DELETE,
                    libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST,
                    -1,
                    host_xml,
                    (
                        libvirt.VIR_NETWORK_UPDATE_AFFECT_LIVE
                        | libvirt.VIR_NETWORK_UPDATE_AFFECT_CONFIG
                    ),
                )
            except Exception:
                pass

        if (
            interface_attached
            and domain is not None
            and interface_xml is not None
        ):
            try:
                domain.detachDeviceFlags(
                    interface_xml,
                    libvirt.VIR_DOMAIN_AFFECT_CONFIG,
                )
            except Exception:
                pass

        raise

    finally:
        conn.close()

def release_instance_runtime(name: str) -> None:
    conn = libvirt.open(LIBVIRT_URI)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domain = _find_domain(conn, name)

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        if domain.isActive():
            raise RuntimeError(
                "Runtime cannot be released "
                "while instance is active"
            )

        mac = instance_mac(name)

        network = conn.networkLookupByName(
            NETWORK_NAME
        )

        root = ET.fromstring(
            network.XMLDesc(0)
        )

        host_element = None

        for host in root.findall(".//dhcp/host"):
            if (
                host.get("name") == name
                or host.get("mac") == mac
            ):
                host_element = host
                break

        if host_element is not None:
            ip = host_element.get("ip")

            slot = next(
                (
                    candidate
                    for candidate in RUNTIME_SLOTS
                    if candidate.ip == ip
                ),
                None,
            )

            if slot is not None:
                _remove_port_forward(slot)
                _apply_firewall()

            host_xml = ET.tostring(
                host_element,
                encoding="unicode",
            )

            network.update(
                libvirt.VIR_NETWORK_UPDATE_COMMAND_DELETE,
                libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST,
                -1,
                host_xml,
                (
                    libvirt.VIR_NETWORK_UPDATE_AFFECT_LIVE
                    | libvirt.VIR_NETWORK_UPDATE_AFFECT_CONFIG
                ),
            )

        domain_xml = ET.fromstring(
            domain.XMLDesc(0)
        )

        has_interface = any(
            interface.find("mac") is not None
            and interface.find("mac").get("address") == mac
            for interface in domain_xml.findall(
                "./devices/interface"
            )
        )

        if has_interface:
            domain.detachDeviceFlags(
                _interface_xml(mac),
                libvirt.VIR_DOMAIN_AFFECT_CONFIG,
            )

    finally:
        conn.close()