export type NodeStatus = "healthy" | "degraded" | "unhealthy" | "offline";

export type HealthState = "ok" | "warning" | "error" | "unknown";

export type InstanceState =
  "running" | "stopped" | "starting" | "unavailable" | "deleting";

export type MinecraftStatus = "online" | "offline" | "starting" | "unknown";

export type EventLevel = "info" | "warning" | "error";

export type InvariantSeverity = "warning" | "critical";

export interface CapacityInfo {
  maxActiveInstances: number;
  activeInstances: number;
  occupiedRuntimeSlots: number;
  availableSlots: number;
}

export interface NodeHealth {
  libvirt: HealthState;
  network: HealthState;
  storage: HealthState;
  invariants: HealthState;
}

export interface CpuMetric {
  usagePercent: number;
  cores: number;
  load1m: number;
  load5m: number;
  load15m: number;
}

export interface MemoryMetric {
  totalMb: number;
  usedMb: number;
  availableMb: number;
}

export interface DiskMetric {
  label: string;
  totalGb: number;
  usedGb: number;
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
  ready: boolean;
  agentVersion: string;
  uptimeSeconds: number;
  lastSeen: string;
  region: string;
  capacity: CapacityInfo;
  health: NodeHealth;
  metrics: NodeMetrics;
  invariants: Invariant[];
}

export interface InstanceRuntime {
  slot: number;
  ip: string;
  externalPort: number;
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
  computeNodeId: string;
  state: InstanceState;
  vmUsername: string;
  memoryMb: number;
  vcpus: number;
  minecraftVersion: string;
  runtime: InstanceRuntime | null;
  minecraftStatus: MinecraftStatus;
  createdAt: string;
  persistentStorage: "attached" | "detached" | "provisioning";
  metrics: InstanceMetrics;
}

export interface PlatformEvent {
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
  slotsUsed: number;
  slotsTotal: number;
  cpuUsagePercent: number;
  memoryUsedMb: number;
  memoryTotalMb: number;
  storageUsedGb: number;
  storageTotalGb: number;
  alerts: number;
}

export interface CreateInstanceInput {
  name: string;
  vmUsername: string;
  memoryMb: number;
  vcpus: number;
  minecraftVersion: string;
  acceptEula: boolean;
  autogeneratePassword: boolean;
  computeNodeId: string;
}

export interface ControlPlaneSettings {
  controlPlaneName: string;
  refreshIntervalSeconds: number;
  environment: "development" | "staging" | "production";
  defaultMemoryMb: number;
  defaultVcpus: number;
  maxInstancesPerNode: number;
}
