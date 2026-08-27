import json

from dataclasses import dataclass
from enum import Enum

import libvirt

from jorge_agent.config import (
    LIBVIRT,
    NETWORK,
    PATHS,
    STORAGE,
)
from jorge_agent.services.runtime_service import (
    get_instance_runtime,
)

class InvariantSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass(frozen=True)
class InvariantIssue:
    code: str
    detail: str
    severity: InvariantSeverity = (
        InvariantSeverity.CRITICAL
    )
    instance: str | None = None


@dataclass(frozen=True)
class InvariantReport:
    healthy: bool
    issues: list[InvariantIssue]

    @property
    def has_critical(self) -> bool:
        return any(
            issue.severity
            == InvariantSeverity.CRITICAL
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        return any(
            issue.severity
            == InvariantSeverity.WARNING
            for issue in self.issues
        )


def _check_network(
    conn: libvirt.virConnect,
    issues: list[InvariantIssue],
) -> None:
    try:
        network = conn.networkLookupByName(
            LIBVIRT.network_name
        )

        if not network.isActive():
            issues.append(
                InvariantIssue(
                    code="network_inactive",
                    detail=(
                        f"Network {LIBVIRT.network_name} "
                        "is not active"
                    ),
                )
            )

    except libvirt.libvirtError:
        issues.append(
            InvariantIssue(
                code="network_missing",
                detail=(
                    f"Network {LIBVIRT.network_name} "
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
    if not STORAGE.base_image.exists():
        issues.append(
            InvariantIssue(
                code="base_image_missing",
                detail=(
                    f"Base image missing: "
                    f"{STORAGE.base_image}"
                ),
            )
        )

        return

    if STORAGE.base_image.stat().st_mode & 0o222:
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
        NETWORK.firewall_script,
        NETWORK.dhcp_release_script,
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
    if not NETWORK.port_forward_config.exists():
        return

    for raw_line in (
        NETWORK.port_forward_config
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

        if internal_port == NETWORK.rcon_port:
            issues.append(
                InvariantIssue(
                    code="rcon_public",
                    detail=(
                        f"RCON port {NETWORK.rcon_port} "
                        "must never be "
                        "publicly forwarded"
                    ),
                )
            )


def _check_instances(
    conn: libvirt.virConnect,
    issues: list[InvariantIssue],
) -> None:
    if not PATHS.metadata_dir.exists():
        return

    domains = {
        domain.name(): domain
        for domain
        in conn.listAllDomains()
    }

    for metadata_path in (
        PATHS.metadata_dir.glob("*.json")
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


def _has_critical_issues(
    issues: list[InvariantIssue],
) -> bool:
    return any(
        issue.severity
        == InvariantSeverity.CRITICAL
        for issue in issues
    )


def _has_warning_issues(
    issues: list[InvariantIssue],
) -> bool:
    return any(
        issue.severity
        == InvariantSeverity.WARNING
        for issue in issues
    )


def check_invariants() -> InvariantReport:
    issues: list[InvariantIssue] = []

    conn = libvirt.open(
        LIBVIRT.uri
    )

    if conn is None:
        return InvariantReport(
                healthy=not any(
                    issue.severity
                    == InvariantSeverity.CRITICAL
                    for issue in issues
                ),
                issues=issues,
            )

    try:
        _check_network(
            conn,
            issues,
        )

        _check_pool(
            conn,
            LIBVIRT.instance_pool,
            issues,
        )

        _check_pool(
            conn,
            LIBVIRT.volume_pool,
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
    healthy=not _has_critical_issues(
        issues
    ),
    issues=issues,
    )