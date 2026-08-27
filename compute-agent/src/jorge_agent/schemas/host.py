from pydantic import BaseModel


class HostCpuMetrics(BaseModel):
    usage_percent: float
    load_1m: float
    load_5m: float
    load_15m: float


class HostMemoryMetrics(BaseModel):
    total_bytes: int
    used_bytes: int
    available_bytes: int
    usage_percent: float


class HostDiskMetrics(BaseModel):
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


class HostMetricsResponse(BaseModel):
    cpu: HostCpuMetrics
    memory: HostMemoryMetrics
    root_disk: HostDiskMetrics
    mc_iaas_disk: HostDiskMetrics
