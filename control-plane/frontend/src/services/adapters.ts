import type {
  ComputeNode,
  Instance,
  OverviewSummary,
  PlatformEvent,
  MonitoringSummary,
  Operation,
} from "../types/index.ts";

interface ResourceMetricsDto {
  total_bytes: number | null;
  used_bytes: number | null;
  available_bytes: number | null;
  usage_percent: number | null;
}
const mib = (bytes: number | null | undefined) =>
  bytes == null ? null : bytes / 1024 ** 2;
const gb = (bytes: number | null | undefined) =>
  bytes == null ? null : bytes / 1e9;
const componentHealth = (healthy: boolean | null | undefined) =>
  healthy == null
    ? ("unknown" as const)
    : healthy
      ? ("ok" as const)
      : ("error" as const);

export interface NodeDto {
  id: string;
  name: string;
  enabled: boolean;
  reachability: "online" | "offline" | "unknown";
  observed_health: "healthy" | "degraded" | "unhealthy" | "unknown";
  observed_ready: boolean | null;
  agent_version: string | null;
  last_seen_at: string | null;
  last_observed_at: string | null;
  last_error: string | null;
  agent_uptime_seconds?: number | null;
  metrics_observed_at?: string | null;
  health?: {
    libvirt: boolean | null;
    network: boolean | null;
    storage: boolean | null;
    invariants: boolean | null;
  } | null;
  invariants_details?: string | null;
  metrics?: {
    cpu: { usage_percent: number | null };
    memory: ResourceMetricsDto;
    storage: ResourceMetricsDto;
  } | null;
  capacity: {
    max_active_instances: number | null;
    active_instances: number | null;
    occupied_runtime_slots: number | null;
    available_slots: number | null;
  };
}
export interface InstanceDto {
  id: string;
  name: string;
  compute_node_id: string | null;
  desired_state: string;
  observed_state: string;
  display_state: Instance["state"];
  memory_mb: number;
  vcpus: number;
  minecraft_version: string;
  vm_username: string | null;
  runtime: {
    slot: number | null;
    ip: string | null;
    external_port: number | null;
  } | null;
  minecraft_status: Instance["minecraftStatus"];
  created_at: string;
  last_observed_at: string | null;
  last_error: string | null;
  active_operation: Pick<Operation, "id" | "type" | "status"> | null;
}
export interface OverviewDto {
  cpu_usage_percent?: number | null;
  memory_used_bytes?: number | null;
  memory_total_bytes?: number | null;
  storage_used_bytes?: number | null;
  storage_total_bytes?: number | null;
  infrastructure_status: OverviewSummary["status"];
  total_nodes: number;
  online_nodes: number;
  running_instances: number;
  occupied_runtime_slots: number | null;
  total_runtime_slots: number | null;
  open_critical_conditions: number;
}
export interface EventDto {
  id: string;
  timestamp: string;
  level: PlatformEvent["level"];
  component: string;
  event_type: string;
  node_id: string | null;
  instance_id: string | null;
  operation_id: string | null;
  message: string;
}
export interface MonitoringDto {
  overview: OverviewDto;
  nodes: NodeDto[];
  node_health_distribution: Record<string, number>;
  instance_state_distribution: Record<string, number>;
  conditions: MonitoringSummary["conditions"];
  historical_metrics_available: boolean;
  timeseries: MonitoringSummary["timeseries"];
}
export function adaptNode(dto: NodeDto): ComputeNode {
  return {
    id: dto.id,
    name: dto.name,
    enabled: dto.enabled,
    status:
      dto.reachability === "online" ? dto.observed_health : dto.reachability,
    ready: dto.observed_ready,
    agentVersion: dto.agent_version,
    lastSeen: dto.last_seen_at,
    lastObservedAt: dto.last_observed_at,
    lastError: dto.last_error,
    uptimeSeconds: dto.agent_uptime_seconds ?? null,
    metricsObservedAt: dto.metrics_observed_at ?? null,
    invariantsDetails: dto.invariants_details ?? null,
    region: "—",
    capacity: {
      maxActiveInstances: dto.capacity.max_active_instances,
      activeInstances: dto.capacity.active_instances,
      occupiedRuntimeSlots: dto.capacity.occupied_runtime_slots,
      availableSlots: dto.capacity.available_slots,
    },
    health: {
      libvirt: componentHealth(dto.health?.libvirt),
      network: componentHealth(dto.health?.network),
      storage: componentHealth(dto.health?.storage),
      invariants: componentHealth(dto.health?.invariants),
    },
    metrics: dto.metrics
      ? {
          cpu: {
            usagePercent: dto.metrics.cpu.usage_percent,
            cores: null,
            load1m: null,
            load5m: null,
            load15m: null,
          },
          memory: {
            totalMb: mib(dto.metrics.memory.total_bytes),
            usedMb: mib(dto.metrics.memory.used_bytes),
            availableMb: mib(dto.metrics.memory.available_bytes),
          },
          mcIaasDisk: {
            label: "MC-IaaS",
            totalGb: gb(dto.metrics.storage.total_bytes),
            usedGb: gb(dto.metrics.storage.used_bytes),
          },
          rootDisk: { label: "Root", totalGb: null, usedGb: null },
        }
      : null,
    invariants: [],
    invariantsAvailable: false,
  };
}
export function adaptInstance(dto: InstanceDto): Instance {
  return {
    id: dto.id,
    name: dto.name,
    computeNodeId: dto.compute_node_id,
    state: dto.display_state,
    desiredState: dto.desired_state,
    observedState: dto.observed_state,
    vmUsername: dto.vm_username,
    memoryMb: dto.memory_mb,
    vcpus: dto.vcpus,
    minecraftVersion: dto.minecraft_version,
    runtime: dto.runtime
      ? {
          slot: dto.runtime.slot,
          ip: dto.runtime.ip,
          externalPort: dto.runtime.external_port,
        }
      : null,
    minecraftStatus: dto.minecraft_status,
    createdAt: dto.created_at,
    metrics: null,
    persistentStorage: "unknown",
    lastObservedAt: dto.last_observed_at,
    lastError: dto.last_error,
    activeOperation: dto.active_operation,
  };
}
export function adaptOverview(dto: OverviewDto): OverviewSummary {
  return {
    status: dto.infrastructure_status,
    nodesOnline: dto.online_nodes,
    nodesTotal: dto.total_nodes,
    activeWorkloads: dto.running_instances,
    slotsUsed: dto.occupied_runtime_slots,
    slotsTotal: dto.total_runtime_slots,
    alerts: dto.open_critical_conditions,
    cpuUsagePercent: dto.cpu_usage_percent ?? null,
    memoryUsedMb: mib(dto.memory_used_bytes),
    memoryTotalMb: mib(dto.memory_total_bytes),
    storageUsedGb: gb(dto.storage_used_bytes),
    storageTotalGb: gb(dto.storage_total_bytes),
  };
}
export function adaptEvent(dto: EventDto): PlatformEvent {
  return {
    id: dto.id,
    timestamp: dto.timestamp,
    level: dto.level,
    component: dto.component,
    event: dto.event_type,
    target:
      dto.instance_id ?? dto.node_id ?? dto.operation_id ?? "Control Plane",
    message: dto.message,
    nodeId: dto.node_id,
    instanceId: dto.instance_id,
    operationId: dto.operation_id,
  };
}
export function adaptMonitoring(dto: MonitoringDto): MonitoringSummary {
  return {
    overview: adaptOverview(dto.overview),
    nodes: dto.nodes.map(adaptNode),
    nodeHealthDistribution: dto.node_health_distribution,
    instanceStateDistribution: dto.instance_state_distribution,
    conditions: dto.conditions,
    historicalMetricsAvailable: dto.historical_metrics_available,
    timeseries: dto.timeseries,
  };
}
