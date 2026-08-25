import hashlib
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from functools import partial

import libvirt

from jorge_agent.config import (
    LIBVIRT,
    NETWORK,
    RUNTIME_SLOTS,
    RuntimeSlot,
)
from jorge_agent.schemas.instance import RuntimeAllocation


DHCP_UPDATE_FLAGS = (
    libvirt.VIR_NETWORK_UPDATE_AFFECT_LIVE
    | libvirt.VIR_NETWORK_UPDATE_AFFECT_CONFIG
)
PORT_FORWARD_HEADER = (
    "# PORTA_EXTERNA  IP_INTERNO   PORTA_INTERNA"
)


class RuntimeCleanupError(RuntimeError):
    def __init__(
        self,
        name: str,
        errors: list[str],
    ):
        self.name = name
        self.errors = errors

        super().__init__(
            f"Runtime cleanup failed for {name}: "
            + "; ".join(errors)
        )


@contextmanager
def _open_connection() -> Iterator[libvirt.virConnect]:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError("Could not connect to libvirt")

    try:
        yield conn
    finally:
        conn.close()


def _lookup_network(conn: libvirt.virConnect):
    return conn.networkLookupByName(LIBVIRT.network_name)


def instance_mac(name: str) -> str:
    digest = hashlib.sha256(name.encode("utf-8")).digest()

    return (
        "52:54:00:"
        f"{digest[0]:02x}:"
        f"{digest[1]:02x}:"
        f"{digest[2]:02x}"
    )


def _dhcp_hosts(network) -> list[ET.Element]:
    root = ET.fromstring(network.XMLDesc(0))
    return root.findall(".//dhcp/host")


def _find_dhcp_host(
    network,
    name: str,
    mac: str,
) -> ET.Element | None:
    return next(
        (
            host
            for host in _dhcp_hosts(network)
            if host.get("name") == name
            or host.get("mac") == mac
        ),
        None,
    )


def _get_reserved_ips(network) -> set[str]:
    return {
        ip
        for host in _dhcp_hosts(network)
        if (ip := host.get("ip"))
    }


def _get_leased_ips(network) -> set[str]:
    return {
        ip
        for lease in network.DHCPLeases()
        if (ip := lease.get("ipaddr"))
        and ":" not in ip
    }


def _port_forward_parts(raw_line: str) -> list[str] | None:
    line = raw_line.strip()

    if not line or line.startswith("#"):
        return None

    return line.split()


def _read_port_forward_lines() -> list[str]:
    config_path = NETWORK.port_forward_config

    if not config_path.exists():
        return []

    return config_path.read_text(
        encoding="utf-8",
    ).splitlines()


def _write_port_forward_lines(lines: list[str]) -> None:
    NETWORK.port_forward_config.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _get_forwarded_ports() -> set[int]:
    ports = set()

    for raw_line in _read_port_forward_lines():
        parts = _port_forward_parts(raw_line)

        if parts is None or len(parts) < 3:
            continue

        try:
            ports.add(int(parts[0]))
        except ValueError:
            continue

    return ports


def _available_runtime_slots(network) -> list[RuntimeSlot]:
    occupied_ips = (
        _get_reserved_ips(network)
        | _get_leased_ips(network)
    )
    forwarded_ports = _get_forwarded_ports()

    return [
        slot
        for slot in RUNTIME_SLOTS
        if slot.ip not in occupied_ips
        and slot.external_port not in forwarded_ports
    ]


def available_runtime_slots() -> list[RuntimeSlot]:
    with _open_connection() as conn:
        return _available_runtime_slots(
            _lookup_network(conn)
        )


def _allocate_runtime_slot(network) -> RuntimeSlot:
    available = _available_runtime_slots(network)

    if not available:
        raise RuntimeError("No runtime slots available")

    return available[0]


def allocate_runtime_slot() -> RuntimeSlot:
    with _open_connection() as conn:
        return _allocate_runtime_slot(
            _lookup_network(conn)
        )


def _find_domain(
    conn: libvirt.virConnect,
    name: str,
) -> libvirt.virDomain | None:
    return next(
        (
            domain
            for domain in conn.listAllDomains()
            if domain.name() == name
        ),
        None,
    )


def _require_inactive_domain(
    conn: libvirt.virConnect,
    name: str,
    active_error: str,
) -> libvirt.virDomain:
    domain = _find_domain(conn, name)

    if domain is None:
        raise FileNotFoundError(
            f"Instance not found: {name}"
        )

    if domain.isActive():
        raise RuntimeError(active_error)

    return domain


def _interface_xml(mac: str) -> str:
    return (
        "<interface type='network'>"
        f"<mac address='{mac}'/>"
        f"<source network='{LIBVIRT.network_name}'/>"
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

    return ET.tostring(host, encoding="unicode")


def _update_dhcp_host(
    network,
    command: int,
    host_xml: str,
) -> None:
    network.update(
        command,
        libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST,
        -1,
        host_xml,
        DHCP_UPDATE_FLAGS,
    )


def _add_port_forward(slot: RuntimeSlot) -> None:
    lines = _read_port_forward_lines()

    for raw_line in lines:
        parts = _port_forward_parts(raw_line)

        if parts and parts[0] == str(slot.external_port):
            raise RuntimeError(
                f"Port {slot.external_port} is already published"
            )

    if not lines:
        lines.append(PORT_FORWARD_HEADER)

    lines.append(
        f"{slot.external_port} "
        f"{slot.ip} "
        f"{NETWORK.internal_minecraft_port}"
    )
    _write_port_forward_lines(lines)


def _remove_port_forward(slot: RuntimeSlot) -> None:
    config_path = NETWORK.port_forward_config

    if not config_path.exists():
        return

    external_port = str(slot.external_port)
    remaining_lines = [
        raw_line
        for raw_line in _read_port_forward_lines()
        if not (
            (parts := _port_forward_parts(raw_line))
            and parts[0] == external_port
        )
    ]
    _write_port_forward_lines(remaining_lines)


def _apply_firewall() -> None:
    result = subprocess.run(
        [
            "sudo",
            "-n",
            str(NETWORK.firewall_script),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Firewall update failed: "
            + result.stderr.strip()
        )


def _remove_port_forward_and_apply_firewall(
    slot: RuntimeSlot,
) -> None:
    _remove_port_forward(slot)
    _apply_firewall()


def _release_dhcp_leases(network, mac: str) -> None:
    for lease in network.DHCPLeases(mac):
        ip = lease.get("ipaddr")

        if not ip or ":" in ip:
            continue

        subprocess.run(
            [
                "sudo",
                "-n",
                str(NETWORK.dhcp_release_script),
                ip,
                mac,
            ],
            check=True,
        )


def _slot_for_ip(ip: str | None) -> RuntimeSlot | None:
    return next(
        (
            slot
            for slot in RUNTIME_SLOTS
            if slot.ip == ip
        ),
        None,
    )


def _runtime_allocation(slot: RuntimeSlot) -> RuntimeAllocation:
    return RuntimeAllocation(
        slot=slot.slot,
        ip=slot.ip,
        external_port=slot.external_port,
    )


def _has_interface(domain: libvirt.virDomain, mac: str) -> bool:
    root = ET.fromstring(domain.XMLDesc(0))

    for interface in root.findall("./devices/interface"):
        mac_element = interface.find("mac")

        if (
            mac_element is not None
            and mac_element.get("address") == mac
        ):
            return True

    return False


def _capture_cleanup_error(
    errors: list[str],
    label: str,
    cleanup: Callable[[], None],
) -> None:
    try:
        cleanup()
    except Exception as exc:
        errors.append(f"{label} failed: {exc}")


def prepare_instance_runtime(name: str) -> RuntimeAllocation:
    with _open_connection() as conn:
        domain = _require_inactive_domain(
            conn,
            name,
            f"Instance is already active: {name}",
        )
        network = _lookup_network(conn)
        slot = _allocate_runtime_slot(network)
        mac = instance_mac(name)
        interface_xml = _interface_xml(mac)
        host_xml = _dhcp_host_xml(name, mac, slot.ip)
        rollback_actions: list[Callable[[], None]] = []

        try:
            domain.attachDeviceFlags(
                interface_xml,
                libvirt.VIR_DOMAIN_AFFECT_CONFIG,
            )
            rollback_actions.append(
                partial(
                    domain.detachDeviceFlags,
                    interface_xml,
                    libvirt.VIR_DOMAIN_AFFECT_CONFIG,
                )
            )

            _update_dhcp_host(
                network,
                libvirt.VIR_NETWORK_UPDATE_COMMAND_ADD_LAST,
                host_xml,
            )
            rollback_actions.append(
                partial(
                    _update_dhcp_host,
                    network,
                    libvirt.VIR_NETWORK_UPDATE_COMMAND_DELETE,
                    host_xml,
                )
            )

            _add_port_forward(slot)
            rollback_actions.append(
                partial(
                    _remove_port_forward_and_apply_firewall,
                    slot,
                )
            )

            _apply_firewall()
            return _runtime_allocation(slot)

        except Exception:
            for rollback in reversed(rollback_actions):
                with suppress(Exception):
                    rollback()

            raise


def release_instance_runtime(name: str) -> None:
    with _open_connection() as conn:
        domain = _require_inactive_domain(
            conn,
            name,
            "Runtime cannot be released "
            "while instance is active",
        )
        network = _lookup_network(conn)
        mac = instance_mac(name)
        host = _find_dhcp_host(network, name, mac)
        slot = (
            _slot_for_ip(host.get("ip"))
            if host is not None
            else None
        )
        errors: list[str] = []

        _capture_cleanup_error(
            errors,
            "DHCP lease release",
            partial(_release_dhcp_leases, network, mac),
        )

        if slot is not None:
            _capture_cleanup_error(
                errors,
                "Port-forward cleanup",
                partial(
                    _remove_port_forward_and_apply_firewall,
                    slot,
                ),
            )

        if host is not None:
            host_xml = ET.tostring(host, encoding="unicode")
            _capture_cleanup_error(
                errors,
                "DHCP reservation cleanup",
                partial(
                    _update_dhcp_host,
                    network,
                    libvirt.VIR_NETWORK_UPDATE_COMMAND_DELETE,
                    host_xml,
                ),
            )

        if _has_interface(domain, mac):
            _capture_cleanup_error(
                errors,
                "Interface cleanup",
                partial(
                    domain.detachDeviceFlags,
                    _interface_xml(mac),
                    libvirt.VIR_DOMAIN_AFFECT_CONFIG,
                ),
            )

        if errors:
            raise RuntimeCleanupError(name, errors)


def get_instance_runtime(
    name: str,
) -> RuntimeAllocation | None:
    mac = instance_mac(name)

    with _open_connection() as conn:
        network = _lookup_network(conn)
        host = _find_dhcp_host(network, name, mac)

        if host is None:
            return None

        slot = _slot_for_ip(host.get("ip"))
        return (
            _runtime_allocation(slot)
            if slot is not None
            else None
        )
