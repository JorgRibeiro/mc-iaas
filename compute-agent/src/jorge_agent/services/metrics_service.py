import time
import xml.etree.ElementTree as ET

import libvirt

from jorge_agent.schemas.instance import (
    CpuMetrics,
    DiskMetrics,
    InstanceMetricsResponse,
    MemoryMetrics,
    NetworkMetrics,
    StorageMetrics,
)

from jorge_agent.services.libvirt_service import (
    LIBVIRT_URI,
    map_domain_state,
)


INSTANCE_POOL = "mc-instances"
VOLUME_POOL = "mc-volumes"


def _find_domain(
    conn: libvirt.virConnect,
    name: str,
) -> libvirt.virDomain | None:
    for domain in conn.listAllDomains():
        if domain.name() == name:
            return domain

    return None


def _get_cpu_metrics(
    domain: libvirt.virDomain,
) -> CpuMetrics:
    info_before = domain.info()

    state = map_domain_state(info_before[0])
    vcpus = max(info_before[3], 1)

    cpu_time_seconds = (
        info_before[4] / 1_000_000_000
    )

    if state.value != "running":
        return CpuMetrics(
            usage_percent=None,
            cpu_time_seconds=cpu_time_seconds,
            vcpus=vcpus,
        )

    cpu_before = info_before[4]
    start = time.monotonic()

    time.sleep(0.5)

    info_after = domain.info()

    elapsed = time.monotonic() - start
    cpu_after = info_after[4]

    cpu_delta = cpu_after - cpu_before

    usage_percent = (
        cpu_delta
        / (elapsed * 1_000_000_000 * vcpus)
        * 100
    )

    usage_percent = max(
        0.0,
        min(usage_percent, 100.0),
    )

    return CpuMetrics(
        usage_percent=round(
            usage_percent,
            2,
        ),
        cpu_time_seconds=round(
            cpu_after / 1_000_000_000,
            2,
        ),
        vcpus=vcpus,
    )


def _get_memory_metrics(
    domain: libvirt.virDomain,
) -> MemoryMetrics:
    info = domain.info()

    configured_mb = info[1] // 1024
    current_mb = info[2] // 1024

    rss_mb = None

    if domain.isActive():
        memory_stats = domain.memoryStats()

        rss_kib = memory_stats.get("rss")

        if rss_kib is not None:
            rss_mb = round(
                rss_kib / 1024,
                2,
            )

    return MemoryMetrics(
        configured_mb=configured_mb,
        current_mb=current_mb,
        rss_mb=rss_mb,
    )


def _volume_metrics(
    conn: libvirt.virConnect,
    pool_name: str,
    volume_name: str,
) -> DiskMetrics | None:
    pool = conn.storagePoolLookupByName(
        pool_name
    )

    try:
        volume = pool.storageVolLookupByName(
            volume_name
        )

    except libvirt.libvirtError:
        return None

    info = volume.info()

    return DiskMetrics(
        capacity_bytes=info[1],
        allocation_bytes=info[2],
    )


def _get_storage_metrics(
    conn: libvirt.virConnect,
    name: str,
) -> StorageMetrics:
    system = _volume_metrics(
        conn,
        INSTANCE_POOL,
        f"{name}.qcow2",
    )

    data = _volume_metrics(
        conn,
        VOLUME_POOL,
        f"{name}-data.raw",
    )

    return StorageMetrics(
        system=system,
        data=data,
    )


def _get_network_metrics(
    domain: libvirt.virDomain,
) -> NetworkMetrics | None:
    if not domain.isActive():
        return None

    root = ET.fromstring(
        domain.XMLDesc(0)
    )

    rx_bytes = 0
    tx_bytes = 0
    interfaces_found = 0

    for interface in root.findall(
        "./devices/interface"
    ):
        target = interface.find("target")

        if target is None:
            continue

        device = target.get("dev")

        if not device:
            continue

        stats = domain.interfaceStats(
            device
        )

        rx_bytes += stats[0]
        tx_bytes += stats[4]
        interfaces_found += 1

    if interfaces_found == 0:
        return None

    return NetworkMetrics(
        rx_bytes=rx_bytes,
        tx_bytes=tx_bytes,
    )


def get_instance_metrics(
    name: str,
) -> InstanceMetricsResponse:
    conn = libvirt.open(LIBVIRT_URI)

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

        state = map_domain_state(
            domain.info()[0]
        )

        return InstanceMetricsResponse(
            name=name,
            state=state,
            cpu=_get_cpu_metrics(domain),
            memory=_get_memory_metrics(
                domain
            ),
            storage=_get_storage_metrics(
                conn,
                name,
            ),
            network=_get_network_metrics(
                domain
            ),
        )

    finally:
        conn.close()
