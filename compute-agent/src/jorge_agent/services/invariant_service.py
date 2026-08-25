import json

from dataclasses import dataclass
from pathlib import Path

import libvirt

from jorge_agent.services.runtime_service import (
    get_instance_runtime,
)


LIBVIRT_URI = "qemu:///system"

NETWORK_NAME = "mc-net"

INSTANCE_POOL = "mc-instances"
DATA_POOL = "mc-volumes"

BASE_IMAGE = Path(
    "/srv/mc-iaas/storage/images/"
    "ubuntu-24.04-minimal-base.qcow2"
)

METADATA_DIR = Path(
    "/srv/mc-iaas/metadata"
)

PORT_FORWARD_CONFIG = Path(
    "/srv/mc-iaas/config/"
    "port-forwards.conf"
)

FIREWALL_SCRIPT = Path(
    "/srv/mc-iaas/scripts/"
    "apply-firewall.sh"
)

DHCP_RELEASE_SCRIPT = Path(
    "/srv/mc-iaas/scripts/"
    "release-dhcp-lease.sh"
)


@dataclass(frozen=True)
class InvariantIssue:
    code: str
    detail: str
    instance: str | None = None


@dataclass(frozen=True)
class InvariantReport:
    healthy: bool
    issues: list[InvariantIssue]


def _check_network(
    conn: libvirt.virConnect,
    issues: list[InvariantIssue],
) -> None:
    try:
        network = conn.networkLookupByName(
            NETWORK_NAME
        )

        if not network.isActive():
            issues.append(
                InvariantIssue(
                    code="network_inactive",
                    detail=(
                        f"Network {NETWORK_NAME} "
                        "is not active"
                    ),
                )
            )

    except libvirt.libvirtError:
        issues.append(
            InvariantIssue(
                code="network_missing",
                detail=(
                    f"Network {NETWORK_NAME} "
                    "does not exist"
                ),
            )
        )


def _check_pool(
    conn: libvirt.virConnect,
    name: str,
    issues: list[InvariantIssue],
) -> None:
    try:
        pool = conn.storagePoolLookupByName(
            name
        )

        if not pool.isActive():
            issues.append(
                InvariantIssue(
                    code="pool_inactive",
                    detail=(
                        f"Storage pool {name} "
                        "is not active"
                    ),
                )
            )

    except libvirt.libvirtError:
        issues.append(
            InvariantIssue(
                code="pool_missing",
                detail=(
                    f"Storage pool {name} "
                    "does not exist"
                ),
            )
        )


def _check_base_image(
    issues: list[InvariantIssue],
) -> None:
    if not BASE_IMAGE.exists():
        issues.append(
            InvariantIssue(
                code="base_image_missing",
                detail=(
                    f"Base image missing: "
                    f"{BASE_IMAGE}"
                ),
            )
        )

        return

    if BASE_IMAGE.stat().st_mode & 0o222:
        issues.append(
            InvariantIssue(
                code="base_image_writable",
                detail=(
                    "Base image must be "
                    "read-only"
                ),
            )
        )


def _check_scripts(
    issues: list[InvariantIssue],
) -> None:
    for script in (
        FIREWALL_SCRIPT,
        DHCP_RELEASE_SCRIPT,
    ):
        if not script.exists():
            issues.append(
                InvariantIssue(
                    code="script_missing",
                    detail=(
                        f"Required script "
                        f"missing: {script}"
                    ),
                )
            )


def _check_rcon_not_public(
    issues: list[InvariantIssue],
) -> None:
    if not PORT_FORWARD_CONFIG.exists():
        return

    for raw_line in (
        PORT_FORWARD_CONFIG
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    ):
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
        ):
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        try:
            internal_port = int(
                parts[2]
            )

        except ValueError:
            continue

        if internal_port == 25575:
            issues.append(
                InvariantIssue(
                    code="rcon_public",
                    detail=(
                        "RCON port 25575 "
                        "must never be "
                        "publicly forwarded"
                    ),
                )
            )


def _check_instances(
    conn: libvirt.virConnect,
    issues: list[InvariantIssue],
) -> None:
    if not METADATA_DIR.exists():
        return

    domains = {
        domain.name(): domain
        for domain
        in conn.listAllDomains()
    }

    for metadata_path in (
        METADATA_DIR.glob("*.json")
    ):
        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        # DELETE com mundo preservado.
        if metadata.get("deleted"):
            continue

        name = metadata.get("name")

        if not name:
            issues.append(
                InvariantIssue(
                    code="invalid_metadata",
                    detail=(
                        f"Metadata without "
                        f"name: {metadata_path}"
                    ),
                )
            )

            continue

        domain = domains.get(name)

        if domain is None:
            issues.append(
                InvariantIssue(
                    code="domain_missing",
                    detail=(
                        "Managed instance has "
                        "metadata but no "
                        "libvirt domain"
                    ),
                    instance=name,
                )
            )

            continue

        active = bool(
            domain.isActive()
        )

        runtime = get_instance_runtime(
            name
        )

        if active and runtime is None:
            issues.append(
                InvariantIssue(
                    code="running_without_runtime",
                    detail=(
                        "Running instance has "
                        "no runtime allocation"
                    ),
                    instance=name,
                )
            )

        if (
            not active
            and runtime is not None
        ):
            issues.append(
                InvariantIssue(
                    code="stopped_with_runtime",
                    detail=(
                        "Stopped instance still "
                        "has runtime allocation"
                    ),
                    instance=name,
                )
            )


def check_invariants() -> InvariantReport:
    issues: list[InvariantIssue] = []

    conn = libvirt.open(
        LIBVIRT_URI
    )

    if conn is None:
        return InvariantReport(
            healthy=False,
            issues=[
                InvariantIssue(
                    code="libvirt_unavailable",
                    detail=(
                        "Could not connect "
                        "to libvirt"
                    ),
                )
            ],
        )

    try:
        _check_network(
            conn,
            issues,
        )

        _check_pool(
            conn,
            INSTANCE_POOL,
            issues,
        )

        _check_pool(
            conn,
            DATA_POOL,
            issues,
        )

        _check_base_image(
            issues
        )

        _check_scripts(
            issues
        )

        _check_rcon_not_public(
            issues
        )

        _check_instances(
            conn,
            issues,
        )

    finally:
        conn.close()

    return InvariantReport(
        healthy=not issues,
        issues=issues,
    )
