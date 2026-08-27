import json
import logging

from dataclasses import dataclass, field

import libvirt

from jorge_agent.config import LIBVIRT, PATHS
from jorge_agent.services.runtime_service import (
    get_instance_runtime,
    release_instance_runtime,
)

from jorge_agent.services.lock_service import (
    instance_lock,
    runtime_lock,
)

logger = logging.getLogger(__name__)

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

    logger.info("event=recovery.started")
    
    report = RecoveryReport()

    conn = libvirt.open(
        LIBVIRT.uri
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

        if not PATHS.metadata_dir.exists():
            return report

        for metadata_path in (
            PATHS.metadata_dir.glob("*.json")
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

                # Recovery pode ser executado enquanto
                # a API está recebendo operações.
                #
                # A ordem oficial dos locks é:
                #
                # instance -> runtime
                #
                # Isso impede que a reconciliação
                # concorra com START, STOP ou DELETE
                # da mesma instância.
                with instance_lock(name):
                    with runtime_lock():

                        # O estado precisa ser
                        # confirmado novamente dentro
                        # do lock. A observação feita
                        # antes dele pode ter ficado
                        # desatualizada.
                        if domain.isActive():
                            report.unchanged.append(
                                name
                            )

                            continue

                        runtime = get_instance_runtime(
                            name
                        )

                        if runtime is None:
                            report.unchanged.append(
                                name
                            )

                            continue

                        # Nesse ponto temos:
                        #
                        # domínio parado
                        # +
                        # runtime residual
                        #
                        # Portanto é seguro liberar
                        # NIC, DHCP, lease e forward.
                        release_instance_runtime(
                            name
                        )

                report.recovered.append(
                    name
                )
                logger.warning(
                            "event=recovery.runtime_released "
                            "name=%s",
                             name,
                )

            except Exception as exc:
                report.errors[
                    metadata_path.stem
                ] = str(exc)
                logger.error(
                    "event=recovery.failed "
                    "name=%s error_type=%s",
                    metadata_path.stem,
                    type(exc).__name__,
                )
        logger.info(
            "event=recovery.completed "
            "recovered=%s unchanged=%s errors=%s",
            len(report.recovered),
            len(report.unchanged),
            len(report.errors),
        )

        return report

    finally:
        logger.info(
            "event=recovery.completed "
            "recovered=%s unchanged=%s errors=%s",
            len(report.recovered),
            len(report.unchanged),
            len(report.errors),
        )
        conn.close()
