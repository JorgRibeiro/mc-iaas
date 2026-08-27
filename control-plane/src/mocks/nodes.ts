import type { ComputeNode } from "@/types";

export const mockNodes: ComputeNode[] = [
  {
    id: "node-jorge",
    name: "JORGE",
    status: "healthy",
    ready: true,
    agentVersion: "0.4.2",
    uptimeSeconds: 412_530,
    lastSeen: "2026-08-27T21:04:12Z",
    region: "lab-a",
    capacity: {
      maxActiveInstances: 4,
      activeInstances: 1,
      occupiedRuntimeSlots: 1,
      availableSlots: 3,
    },
    health: { libvirt: "ok", network: "ok", storage: "ok", invariants: "ok" },
    metrics: {
      cpu: { usagePercent: 31.4, cores: 8, load1m: 0.82, load5m: 0.64, load15m: 0.51 },
      memory: { totalMb: 32_768, usedMb: 11_264, availableMb: 21_504 },
      rootDisk: { label: "root", totalGb: 240, usedGb: 78 },
      mcIaasDisk: { label: "mc-iaas", totalGb: 500, usedGb: 143 },
    },
    invariants: [],
  },
  {
    id: "node-raylandson",
    name: "RAYLANDSON-COMPUTE",
    status: "offline",
    ready: false,
    agentVersion: "0.4.0",
    uptimeSeconds: 0,
    lastSeen: "2026-08-26T09:41:55Z",
    region: "lab-b",
    capacity: {
      maxActiveInstances: 4,
      activeInstances: 0,
      occupiedRuntimeSlots: 0,
      availableSlots: 0,
    },
    health: {
      libvirt: "unknown",
      network: "error",
      storage: "unknown",
      invariants: "unknown",
    },
    metrics: {
      cpu: { usagePercent: 0, cores: 4, load1m: 0, load5m: 0, load15m: 0 },
      memory: { totalMb: 16_384, usedMb: 0, availableMb: 0 },
      rootDisk: { label: "root", totalGb: 120, usedGb: 0 },
      mcIaasDisk: { label: "mc-iaas", totalGb: 250, usedGb: 0 },
    },
    invariants: [
      {
        id: "inv-1",
        severity: "critical",
        code: "AGENT_UNREACHABLE",
        detail: "Compute agent heartbeat missing for more than 15 minutes.",
        timestamp: "2026-08-26T09:56:00Z",
      },
      {
        id: "inv-2",
        severity: "warning",
        code: "RUNTIME_SLOTS_UNVERIFIED",
        detail: "Runtime slot allocation table could not be reconciled while node is offline.",
        timestamp: "2026-08-26T10:02:11Z",
      },
    ],
  },
];
