import type {
  ComputeNode,
  Instance,
  OverviewSummary,
  PlatformEvent,
  MonitoringSummary,
  Operation,
} from "../types/index.ts";

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
    uptimeSeconds: null,
    region: "—",
    capacity: {
      maxActiveInstances: dto.capacity.max_active_instances,
      activeInstances: dto.capacity.active_instances,
      occupiedRuntimeSlots: dto.capacity.occupied_runtime_slots,
      availableSlots: dto.capacity.available_slots,
    },
    health: {
      libvirt: "unknown",
      network: "unknown",
      storage: "unknown",
      invariants: "unknown",
    },
    metrics: null,
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
    cpuUsagePercent: null,
    memoryUsedMb: null,
    memoryTotalMb: null,
    storageUsedGb: null,
    storageTotalGb: null,
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
