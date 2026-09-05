import type {
  ComputeNode,
  ControlPlaneSettings,
  CreateInstanceInput,
  Instance,
  OverviewSummary,
  PlatformEvent,
  TimeseriesPoint,
  MonitoringSummary,
  EventLevel,
} from "@/types";

/**
 * Abstract Control Plane client contract.
 *
 * The UI only talks to this interface, implemented by the HTTP client or the
 * in-memory mock adapter. No component should fetch directly.
 */
export interface ControlPlaneClient {
  getOverview(): Promise<OverviewSummary>;
  listNodes(): Promise<ComputeNode[]>;
  getNode(id: string): Promise<ComputeNode>;
  reconcileNode(id: string): Promise<void>;

  listInstances(): Promise<Instance[]>;
  getInstance(id: string): Promise<Instance>;
  createInstance(input: CreateInstanceInput): Promise<Instance>;
  startInstance(id: string): Promise<void>;
  stopInstance(id: string): Promise<void>;
  restartInstance(id: string): Promise<void>;
  deleteInstance(id: string): Promise<void>;

  listEvents(level?: EventLevel): Promise<PlatformEvent[]>;
  getUsageTimeseries(): Promise<TimeseriesPoint[]>;

  getMonitoringSummary(): Promise<MonitoringSummary>;
  getConnectionStatus(): Promise<"connected" | "mock">;

  getSettings(): Promise<ControlPlaneSettings>;
  updateSettings(settings: ControlPlaneSettings): Promise<ControlPlaneSettings>;
}
