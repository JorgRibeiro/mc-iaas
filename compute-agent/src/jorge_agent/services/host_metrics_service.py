import os
import shutil
import time

from pathlib import Path

from jorge_agent.schemas.host import (
    HostCpuMetrics,
    HostDiskMetrics,
    HostMemoryMetrics,
    HostMetricsResponse,
)


CPU_SAMPLE_SECONDS = 0.5
MC_IAAS_ROOT = Path("/srv/mc-iaas")


def _read_cpu_times() -> tuple[int, int]:
    with Path("/proc/stat").open(
        encoding="utf-8"
    ) as stat_file:
        first_line = stat_file.readline()

    parts = first_line.split()

    if not parts or parts[0] != "cpu":
        raise RuntimeError(
            "Could not read aggregate CPU statistics"
        )

    values = [
        int(value)
        for value in parts[1:]
    ]

    if len(values) < 4:
        raise RuntimeError(
            "Incomplete CPU statistics"
        )

    idle = values[3]

    if len(values) > 4:
        idle += values[4]

    total = sum(values)

    return total, idle


def _get_cpu_metrics() -> HostCpuMetrics:
    total_before, idle_before = (
        _read_cpu_times()
    )

    time.sleep(CPU_SAMPLE_SECONDS)

    total_after, idle_after = (
        _read_cpu_times()
    )

    total_delta = (
        total_after - total_before
    )

    idle_delta = (
        idle_after - idle_before
    )

    if total_delta <= 0:
        usage_percent = 0.0
    else:
        busy_delta = (
            total_delta - idle_delta
        )

        usage_percent = (
            busy_delta
            / total_delta
            * 100
        )

    load_1m, load_5m, load_15m = (
        os.getloadavg()
    )

    return HostCpuMetrics(
        usage_percent=round(
            max(
                0.0,
                min(usage_percent, 100.0),
            ),
            2,
        ),
        load_1m=round(load_1m, 2),
        load_5m=round(load_5m, 2),
        load_15m=round(load_15m, 2),
    )


def _read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}

    with Path("/proc/meminfo").open(
        encoding="utf-8"
    ) as meminfo:
        for line in meminfo:
            key, raw_value = line.split(
                ":",
                1,
            )

            parts = raw_value.strip().split()

            if not parts:
                continue

            # /proc/meminfo usa KiB.
            values[key] = (
                int(parts[0]) * 1024
            )

    return values


def _get_memory_metrics() -> HostMemoryMetrics:
    meminfo = _read_meminfo()

    total = meminfo.get("MemTotal")
    available = meminfo.get(
        "MemAvailable"
    )

    if total is None or available is None:
        raise RuntimeError(
            "Could not read host memory statistics"
        )

    used = total - available

    usage_percent = (
        used / total * 100
        if total
        else 0.0
    )

    return HostMemoryMetrics(
        total_bytes=total,
        used_bytes=used,
        available_bytes=available,
        usage_percent=round(
            usage_percent,
            2,
        ),
    )


def _get_disk_metrics(
    path: Path,
) -> HostDiskMetrics:
    usage = shutil.disk_usage(path)

    usage_percent = (
        usage.used
        / usage.total
        * 100
        if usage.total
        else 0.0
    )

    return HostDiskMetrics(
        path=str(path),
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        usage_percent=round(
            usage_percent,
            2,
        ),
    )


def get_host_metrics() -> HostMetricsResponse:
    return HostMetricsResponse(
        cpu=_get_cpu_metrics(),
        memory=_get_memory_metrics(),
        root_disk=_get_disk_metrics(
            Path("/")
        ),
        mc_iaas_disk=_get_disk_metrics(
            MC_IAAS_ROOT
        ),
    )
