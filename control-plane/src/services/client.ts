import type {
  ComputeNode,
  ControlPlaneSettings,
  CreateInstanceInput,
  Instance,
  OverviewSummary,
  PlatformEvent,
  TimeseriesPoint,
} from "@/types";

/**
 * Abstract Control Plane client contract.
 *
 * The UI only talks to this interface. Today it is fulfilled by an in-memory
 * mock adapter; later it will be fulfilled by an HTTP client pointing at the
 * real MC-IaaS Control Plane API. No component should fetch directly.
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

  listEvents(): Promise<PlatformEvent[]>;
  getUsageTimeseries(): Promise<TimeseriesPoint[]>;

  getSettings(): Promise<ControlPlaneSettings>;
  updateSettings(settings: ControlPlaneSettings): Promise<ControlPlaneSettings>;
}
