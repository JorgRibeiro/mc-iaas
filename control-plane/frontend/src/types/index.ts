export type NodeStatus =
  "healthy" | "degraded" | "unhealthy" | "offline" | "unknown";

export type HealthState = "ok" | "warning" | "error" | "unknown";

export type InstanceState =
  | "running"
  | "stopped"
  | "starting"
  | "unavailable"
  | "deleting"
  | "creating"
  | "stopping"
  | "restarting"
  | "uncertain"
  | "missing"
  | "unknown"
  | "paused";

export type MinecraftStatus =
  "online" | "offline" | "starting" | "unknown" | "unavailable";

export type EventLevel = "info" | "warning" | "error";

export type InvariantSeverity = "warning" | "critical";

export interface CapacityInfo {
  maxActiveInstances: number | null;
  activeInstances: number | null;
  occupiedRuntimeSlots: number | null;
  availableSlots: number | null;
}

export interface NodeHealth {
  libvirt: HealthState;
  network: HealthState;
  storage: HealthState;
  invariants: HealthState;
}

export interface CpuMetric {
  usagePercent: number | null;
  cores: number | null;
  load1m: number | null;
  load5m: number | null;
  load15m: number | null;
}

export interface MemoryMetric {
  totalMb: number | null;
  usedMb: number | null;
  availableMb: number | null;
}

export interface DiskMetric {
  label: string;
  totalGb: number | null;
  usedGb: number | null;
}

export interface NodeMetrics {
  cpu: CpuMetric;
  memory: MemoryMetric;
  rootDisk: DiskMetric;
  mcIaasDisk: DiskMetric;
}

export interface Invariant {
  id: string;
  severity: InvariantSeverity;
  code: string;
  detail: string;
  timestamp: string;
}

export interface ComputeNode {
  id: string;
  name: string;
  status: NodeStatus;
  ready: boolean | null;
  agentVersion: string | null;
  uptimeSeconds: number | null;
  lastSeen: string | null;
  region: string;
  enabled?: boolean;
  lastError?: string | null;
  lastObservedAt?: string | null;
  invariantsAvailable?: boolean;
  invariantsDetails?: string | null;
  metricsObservedAt?: string | null;
  capacity: CapacityInfo;
  health: NodeHealth;
  metrics: NodeMetrics | null;
  invariants: Invariant[];
}

export interface InstanceRuntime {
  slot: number | null;
  ip: string | null;
  externalPort: number | null;
}

export interface InstanceMetrics {
  cpuUsagePercent: number;
  cpuTimeSeconds: number;
  memoryConfiguredMb: number;
  memoryCurrentMb: number;
  memoryRssMb: number;
  systemStorageGb: { usedGb: number; totalGb: number };
  dataStorageGb: { usedGb: number; totalGb: number };
  networkRxMb: number;
  networkTxMb: number;
}

export interface Instance {
  id: string;
  name: string;
  computeNodeId: string | null;
  state: InstanceState;
  vmUsername: string | null;
  memoryMb: number;
  vcpus: number;
  minecraftVersion: string;
  runtime: InstanceRuntime | null;
  minecraftStatus: MinecraftStatus;
  createdAt: string;
  desiredState?: string;
  observedState?: string;
  lastObservedAt?: string | null;
  lastError?: string | null;
  activeOperation?: Pick<Operation, "id" | "type" | "status"> | null;
  persistentStorage: "attached" | "detached" | "provisioning" | "unknown";
  metrics: InstanceMetrics | null;
}

export interface PlatformEvent {
  nodeId?: string | null;
  instanceId?: string | null;
  operationId?: string | null;
  id: string;
  timestamp: string;
  level: EventLevel;
  component: string;
  event: string;
  target: string;
  message: string;
}

export interface TimeseriesPoint {
  t: string;
  cpu: number;
  memory: number;
}

export interface OverviewSummary {
  status: "operational" | "degraded" | "down";
  nodesOnline: number;
  nodesTotal: number;
  activeWorkloads: number;
  slotsUsed: number | null;
  slotsTotal: number | null;
  cpuUsagePercent: number | null;
  memoryUsedMb: number | null;
  memoryTotalMb: number | null;
  storageUsedGb: number | null;
  storageTotalGb: number | null;
  alerts: number;
}

export interface CreateInstanceInput {
  name: string;
  vmUsername: string;
  memoryMb: number;
  vcpus: number;
  minecraftVersion: string;
  acceptEula: boolean;
}

export interface ControlPlaneSettings {
  controlPlaneName: string;
  refreshIntervalSeconds: number;
  environment: "development" | "staging" | "production";
  defaultMemoryMb: number;
  defaultVcpus: number;
  maxInstancesPerNode: number;
}

export interface Operation {
  id: string;
  instance_id: string;
  type: string;
  status: "pending" | "in_progress" | "succeeded" | "failed" | "uncertain";
  error_message?: string | null;
}

export interface MonitoringSummary {
  overview: OverviewSummary;
  nodes: ComputeNode[];
  nodeHealthDistribution: Record<string, number>;
  instanceStateDistribution: Record<string, number>;
  conditions: {
    code: string;
    node_id: string | null;
    instance_id: string | null;
  }[];
  historicalMetricsAvailable: boolean;
  timeseries: TimeseriesPoint[];
}
