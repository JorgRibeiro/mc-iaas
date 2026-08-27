import { mockEvents, mockTimeseries } from "@/mocks/events";
import { mockInstances } from "@/mocks/instances";
import { mockNodes } from "@/mocks/nodes";
import type { ControlPlaneClient } from "@/services/client";
import type {
  ComputeNode,
  ControlPlaneSettings,
  CreateInstanceInput,
  Instance,
  InstanceState,
  OverviewSummary,
  PlatformEvent,
  TimeseriesPoint,
} from "@/types";

const LATENCY_MS = 320;

/** In-memory mutable state so the mock UI feels alive across navigation. */
const state = {
  nodes: structuredClone(mockNodes) as ComputeNode[],
  instances: structuredClone(mockInstances) as Instance[],
  events: structuredClone(mockEvents) as PlatformEvent[],
  settings: {
    controlPlaneName: "MC-IaaS Control Plane",
    refreshIntervalSeconds: 30,
    environment: "development",
    defaultMemoryMb: 2048,
    defaultVcpus: 1,
    maxInstancesPerNode: 4,
  } as ControlPlaneSettings,
};

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), LATENCY_MS));
}

function nowIso() {
  return new Date().toISOString();
}

function pushEvent(e: Omit<PlatformEvent, "id" | "timestamp">) {
  state.events = [
    { ...e, id: `evt-${Math.random().toString(36).slice(2, 9)}`, timestamp: nowIso() },
    ...state.events,
  ];
}

function recomputeCapacity() {
  for (const node of state.nodes) {
    if (node.status === "offline") {
      node.capacity.activeInstances = 0;
      node.capacity.occupiedRuntimeSlots = 0;
      node.capacity.availableSlots = 0;
      continue;
    }
    const active = state.instances.filter(
      (i) => i.computeNodeId === node.id && (i.state === "running" || i.state === "starting"),
    );
    node.capacity.activeInstances = active.length;
    node.capacity.occupiedRuntimeSlots = active.filter((i) => i.runtime).length;
    node.capacity.availableSlots = Math.max(
      0,
      node.capacity.maxActiveInstances - node.capacity.activeInstances,
    );
  }
}

function requireInstance(id: string): Instance {
  const instance = state.instances.find((i) => i.id === id);
  if (!instance) throw new Error(`Instance ${id} not found`);
  return instance;
}

function setState(instance: Instance, next: InstanceState) {
  instance.state = next;
  if (next === "running") {
    instance.minecraftStatus = "online";
    instance.runtime ??= {
      slot: (state.instances.filter((i) => i.runtime).length % 8) + 1,
      ip: `10.50.0.${10 + state.instances.indexOf(instance)}`,
      externalPort: 25565 + state.instances.indexOf(instance),
    };
    instance.metrics.memoryCurrentMb = instance.memoryMb;
    instance.metrics.memoryRssMb = Math.round(instance.memoryMb * 0.82);
    instance.metrics.cpuUsagePercent = 24.6;
  }
  if (next === "stopped") {
    instance.minecraftStatus = "offline";
    instance.runtime = null;
    instance.metrics.memoryCurrentMb = 0;
    instance.metrics.memoryRssMb = 0;
    instance.metrics.cpuUsagePercent = 0;
  }
  recomputeCapacity();
}

export const mockControlPlaneClient: ControlPlaneClient = {
  async getOverview(): Promise<OverviewSummary> {
    recomputeCapacity();
    const online = state.nodes.filter((n) => n.status !== "offline");
    const slotsTotal = state.nodes.reduce((acc, n) => acc + n.capacity.maxActiveInstances, 0);
    const slotsUsed = state.nodes.reduce((acc, n) => acc + n.capacity.occupiedRuntimeSlots, 0);
    const memoryTotalMb = online.reduce((acc, n) => acc + n.metrics.memory.totalMb, 0);
    const memoryUsedMb = online.reduce((acc, n) => acc + n.metrics.memory.usedMb, 0);
    const storageTotalGb = state.nodes.reduce((acc, n) => acc + n.metrics.mcIaasDisk.totalGb, 0);
    const storageUsedGb = state.nodes.reduce((acc, n) => acc + n.metrics.mcIaasDisk.usedGb, 0);
    const cpu = online.length
      ? online.reduce((acc, n) => acc + n.metrics.cpu.usagePercent, 0) / online.length
      : 0;
    const alerts = state.nodes.reduce((acc, n) => acc + n.invariants.length, 0);

    return delay({
      status: alerts === 0 ? "operational" : online.length ? "degraded" : "down",
      nodesOnline: online.length,
      nodesTotal: state.nodes.length,
      activeWorkloads: state.instances.filter((i) => i.state === "running").length,
      slotsUsed,
      slotsTotal,
      cpuUsagePercent: Number(cpu.toFixed(1)),
      memoryUsedMb,
      memoryTotalMb,
      storageUsedGb,
      storageTotalGb,
      alerts,
    });
  },

  listNodes() {
    recomputeCapacity();
    return delay(structuredClone(state.nodes));
  },

  async getNode(id) {
    recomputeCapacity();
    const node = state.nodes.find((n) => n.id === id);
    if (!node) throw new Error(`Compute node ${id} not found`);
    return delay(structuredClone(node));
  },

  async reconcileNode(id) {
    const node = state.nodes.find((n) => n.id === id);
    if (!node) throw new Error(`Compute node ${id} not found`);
    pushEvent({
      level: "warning",
      component: "recovery",
      event: "recovery.started",
      target: node.name,
      message: "Reconciliation requested from control plane console (mock).",
    });
    pushEvent({
      level: "info",
      component: "recovery",
      event: "recovery.completed",
      target: node.name,
      message: "Mock reconciliation finished, no state changes applied.",
    });
    return delay(undefined);
  },

  listInstances() {
    return delay(structuredClone(state.instances));
  },

  async getInstance(id) {
    return delay(structuredClone(requireInstance(id)));
  },

  async createInstance(input: CreateInstanceInput) {
    const instance: Instance = {
      id: `inst-${input.name}`,
      name: input.name,
      computeNodeId: input.computeNodeId,
      state: "starting",
      vmUsername: input.vmUsername,
      memoryMb: input.memoryMb,
      vcpus: input.vcpus,
      minecraftVersion: input.minecraftVersion,
      runtime: null,
      minecraftStatus: "starting",
      createdAt: nowIso(),
      persistentStorage: "provisioning",
      metrics: {
        cpuUsagePercent: 0,
        cpuTimeSeconds: 0,
        memoryConfiguredMb: input.memoryMb,
        memoryCurrentMb: 0,
        memoryRssMb: 0,
        systemStorageGb: { usedGb: 0, totalGb: 10 },
        dataStorageGb: { usedGb: 0, totalGb: 20 },
        networkRxMb: 0,
        networkTxMb: 0,
      },
    };
    state.instances = [instance, ...state.instances];
    pushEvent({
      level: "info",
      component: "lifecycle",
      event: "instance.created",
      target: instance.name,
      message: "Instance definition accepted and scheduled to compute node (mock).",
    });
    recomputeCapacity();
    return delay(structuredClone(instance));
  },

  async startInstance(id) {
    const instance = requireInstance(id);
    pushEvent({
      level: "info",
      component: "lifecycle",
      event: "instance.start.requested",
      target: instance.name,
      message: "Start requested from control plane console.",
    });
    setState(instance, "running");
    pushEvent({
      level: "info",
      component: "runtime",
      event: "instance.start.runtime_allocated",
      target: instance.name,
      message: "Runtime slot allocated with internal address and external port mapping.",
    });
    pushEvent({
      level: "info",
      component: "lifecycle",
      event: "instance.start.completed",
      target: instance.name,
      message: "Instance reached running state (mock).",
    });
    return delay(undefined);
  },

  async stopInstance(id) {
    const instance = requireInstance(id);
    setState(instance, "stopped");
    pushEvent({
      level: "info",
      component: "lifecycle",
      event: "instance.stop.completed",
      target: instance.name,
      message: "Instance stopped, runtime slot released (mock).",
    });
    return delay(undefined);
  },

  async restartInstance(id) {
    const instance = requireInstance(id);
    setState(instance, "running");
    pushEvent({
      level: "info",
      component: "lifecycle",
      event: "instance.restart.completed",
      target: instance.name,
      message: "Instance restarted (mock).",
    });
    return delay(undefined);
  },

  async deleteInstance(id) {
    const instance = requireInstance(id);
    state.instances = state.instances.filter((i) => i.id !== id);
    pushEvent({
      level: "warning",
      component: "lifecycle",
      event: "instance.delete.completed",
      target: instance.name,
      message: "Instance and persistent storage removed (mock).",
    });
    recomputeCapacity();
    return delay(undefined);
  },

  listEvents(): Promise<PlatformEvent[]> {
    return delay(structuredClone(state.events));
  },

  getUsageTimeseries(): Promise<TimeseriesPoint[]> {
    return delay(structuredClone(mockTimeseries));
  },

  getSettings() {
    return delay(structuredClone(state.settings));
  },

  updateSettings(settings) {
    state.settings = { ...settings };
    return delay(structuredClone(state.settings));
  },
};
