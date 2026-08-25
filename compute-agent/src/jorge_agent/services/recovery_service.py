import json

from dataclasses import dataclass, field
from pathlib import Path

import libvirt

from jorge_agent.services.runtime_service import (
    get_instance_runtime,
    release_instance_runtime,
)


LIBVIRT_URI = "qemu:///system"

METADATA_DIR = Path(
    "/srv/mc-iaas/metadata"
)


@dataclass
class RecoveryReport:
    recovered: list[str] = field(
        default_factory=list
    )

    unchanged: list[str] = field(
        default_factory=list
    )

    errors: dict[str, str] = field(
        default_factory=dict
    )


def reconcile_instance_runtimes() -> RecoveryReport:
    report = RecoveryReport()

    conn = libvirt.open(
        LIBVIRT_URI
    )

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domains = {
            domain.name(): domain
            for domain
            in conn.listAllDomains()
        }

        if not METADATA_DIR.exists():
            return report

        for metadata_path in (
            METADATA_DIR.glob("*.json")
        ):
            try:
                metadata = json.loads(
                    metadata_path.read_text(
                        encoding="utf-8"
                    )
                )

                # Mundo preservado após DELETE.
                if metadata.get("deleted"):
                    continue

                name = metadata.get("name")

                if not name:
                    continue

                domain = domains.get(name)

                if domain is None:
                    continue

                runtime = get_instance_runtime(
                    name
                )

                if domain.isActive():
                    report.unchanged.append(
                        name
                    )

                    continue

                if runtime is None:
                    report.unchanged.append(
                        name
                    )

                    continue

                release_instance_runtime(
                    name
                )

                report.recovered.append(
                    name
                )

            except Exception as exc:
                report.errors[
                    metadata_path.stem
                ] = str(exc)

        return report

    finally:
        conn.close()
