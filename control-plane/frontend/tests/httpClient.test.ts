import assert from "node:assert/strict";
import test from "node:test";
import {
  HttpControlPlaneClient,
  ApiError,
  OperationPendingError,
  OperationUncertainError,
  waitForOperation,
} from "../src/services/httpClient.ts";
import {
  adaptNode,
  adaptOverview,
  adaptInstance,
} from "../src/services/adapters.ts";

const instance = {
  id: "instance-id",
  name: "test-vm",
  compute_node_id: "node-id",
  desired_state: "stopped",
  observed_state: "stopped",
  display_state: "stopped" as const,
  memory_mb: 2048,
  vcpus: 1,
  minecraft_version: "26.2",
  vm_username: "operator",
  runtime: null,
  minecraft_status: "unknown" as const,
  created_at: "2026-09-05T12:00:00Z",
  last_observed_at: null,
  last_error: null,
  active_operation: null,
};
const operation = {
  id: "operation-id",
  instance_id: instance.id,
  type: "create",
  status: "succeeded" as const,
};

function reply(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status });
}

test("adapters preserve unknowns, runtime and display states", () => {
  const node = adaptNode({
    id: "node",
    name: "JORGE",
    enabled: true,
    reachability: "offline",
    observed_health: "healthy",
    observed_ready: null,
    agent_version: null,
    last_seen_at: null,
    last_observed_at: null,
    last_error: "Agent unavailable",
    capacity: {
      max_active_instances: 4,
      active_instances: 1,
      occupied_runtime_slots: 1,
      available_slots: null,
    },
  });
  assert.equal(node.status, "offline");
  assert.equal(node.capacity.availableSlots, null);
  assert.equal(node.metrics, null);
  assert.equal(node.ready, null);
  assert.equal(node.health.libvirt, "unknown");
  const mapped = adaptInstance({
    ...instance,
    display_state: "uncertain",
    runtime: {
      slot: 1,
      ip: "10.0.0.1",
      external_port: 25565,
    },
  });
  assert.equal(mapped.state, "uncertain");
  assert.equal(mapped.runtime?.externalPort, 25565);
  assert.equal(mapped.minecraftStatus, "unknown");
  assert.equal(mapped.metrics, null);
  const overview = adaptOverview({
    infrastructure_status: "operational",
    total_nodes: 1,
    online_nodes: 1,
    running_instances: 2,
    occupied_runtime_slots: 2,
    total_runtime_slots: 4,
    open_critical_conditions: 0,
  });
  assert.equal(overview.slotsUsed, 2);
  assert.equal(overview.memoryUsedMb, null);
});

test("CREATE sends real fields, tracks operation and then reads Instance", async () => {
  const calls: string[] = [];
  let notified = false;
  const fake: typeof fetch = async (url, options) => {
    calls.push(String(url));
    if (String(url).endsWith("/instances")) {
      assert.equal(options?.method, "POST");
      assert.deepEqual(JSON.parse(String(options?.body)), {
        name: "test-vm",
        memory_mb: 2048,
        vcpus: 1,
        minecraft_version: "26.2",
        vm_username: "operator",
        accept_eula: true,
      });
      return reply(
        {
          operation_id: operation.id,
          instance_id: instance.id,
          status: "pending",
        },
        202,
      );
    }
    assert.equal(notified, true);
    return reply(String(url).includes("/operations/") ? operation : instance);
  };
  const client = new HttpControlPlaneClient(
    "http://control.test/",
    fake,
    () => {
      notified = true;
    },
  );
  const input = {
    name: "test-vm",
    memoryMb: 2048,
    vcpus: 1,
    minecraftVersion: "26.2",
    vmUsername: "operator",
    acceptEula: true,
    computeNodeId: "must-not-send",
    password: "must-not-send",
  };
  assert.equal((await client.createInstance(input)).id, instance.id);
  assert.deepEqual(calls, [
    "http://control.test/api/v1/instances",
    "http://control.test/api/v1/operations/operation-id",
    "http://control.test/api/v1/instances/instance-id",
  ]);
});

for (const action of ["start", "stop", "restart", "delete"] as const) {
  test(`${action} uses correct endpoint and waits for confirmation`, async () => {
    const calls: [string, string | undefined][] = [];
    const fake: typeof fetch = async (url, options) => {
      calls.push([String(url), options?.method]);
      return reply(
        String(url).includes("/operations/")
          ? operation
          : { operation_id: operation.id },
      );
    };
    const client = new HttpControlPlaneClient("http://control.test", fake);
    await client[`${action}Instance`](instance.id);
    assert.equal(
      calls[0]?.[0],
      `http://control.test/api/v1/instances/${instance.id}${action === "delete" ? "" : "/" + action}`,
    );
    assert.equal(calls[0]?.[1], action === "delete" ? "DELETE" : "POST");
    assert.equal(calls.length, 2);
  });
}

test("polling handles progress and each terminal state", async () => {
  let reads = 0;
  const sleep = async () => {};
  await waitForOperation(
    async () => ({
      ...operation,
      status: ++reads < 3 ? "in_progress" : "succeeded",
    }),
    { sleep },
  );
  assert.equal(reads, 3);
  await assert.rejects(
    waitForOperation(async () => ({ ...operation, status: "uncertain" }), {
      sleep,
    }),
    OperationUncertainError,
  );
  await assert.rejects(
    waitForOperation(
      async () => ({
        ...operation,
        status: "failed",
        error_message: "Capacity conflict",
      }),
      { sleep },
    ),
    /Capacity conflict/,
  );
});

test("operation tracking is bounded and does not resend mutations", async () => {
  let reads = 0;
  await assert.rejects(
    waitForOperation(
      async () => {
        reads++;
        return { ...operation, status: "pending" };
      },
      { attempts: 3, sleep: async () => {} },
    ),
    OperationPendingError,
  );
  assert.equal(reads, 3);
});

test("network failure after acceptance reports tracking loss without retry", async () => {
  let mutations = 0;
  const fake: typeof fetch = async (_url, options) => {
    if (options?.method === "POST") {
      mutations++;
      return reply({ operation_id: operation.id });
    }
    throw new Error("connection reset");
  };
  const client = new HttpControlPlaneClient("http://control.test", fake);
  await assert.rejects(
    client.startInstance(instance.id),
    OperationPendingError,
  );
  assert.equal(mutations, 1);
});

test("HTTP errors and readiness use Control Plane routes", async () => {
  const client = new HttpControlPlaneClient("http://control.test", async () =>
    reply({ detail: "Conflict" }, 409),
  );
  await assert.rejects(
    client.startInstance(instance.id),
    (error: ApiError) => error.status === 409,
  );
  const calls: string[] = [];
  const connected = new HttpControlPlaneClient(
    "http://control.test",
    async (url) => {
      calls.push(String(url));
      return reply({ status: "ok" });
    },
  );
  assert.equal(await connected.getConnectionStatus(), "connected");
  assert.deepEqual(calls, [
    "http://control.test/health",
    "http://control.test/ready",
  ]);
});

test("node refresh and event filters use real API", async () => {
  const calls: string[] = [];
  const client = new HttpControlPlaneClient(
    "http://control.test",
    async (url) => {
      calls.push(String(url));
      return reply([]);
    },
  );
  await client.reconcileNode("node-id");
  await client.listEvents("warning");
  assert.deepEqual(calls, [
    "http://control.test/api/v1/nodes/node-id/refresh",
    "http://control.test/api/v1/events?limit=100&level=warning",
  ]);
});

const liveNode = {
  id: "live",
  name: "JORGE",
  enabled: true,
  reachability: "online" as const,
  observed_health: "healthy" as const,
  observed_ready: true,
  agent_version: "0.1.0",
  agent_uptime_seconds: 1234.5,
  last_seen_at: "2026-09-05T12:00:00Z",
  last_observed_at: "2026-09-05T12:00:00Z",
  metrics_observed_at: "2026-09-05T12:00:00Z",
  last_error: null,
  health: { libvirt: true, network: false, storage: true, invariants: null },
  capacity: {
    max_active_instances: 4,
    active_instances: 0,
    occupied_runtime_slots: 0,
    available_slots: 4,
  },
  metrics: {
    cpu: { usage_percent: 7.8 },
    memory: {
      total_bytes: 16 * 1024 ** 3,
      used_bytes: 3 * 1024 ** 3,
      available_bytes: 13 * 1024 ** 3,
      usage_percent: 18.75,
    },
    storage: {
      total_bytes: 115e9,
      used_bytes: 18.2e9,
      available_bytes: 96.8e9,
      usage_percent: 15.8,
    },
  },
};
test("live node maps bytes, health, uptime and preserves offline values", () => {
  const node = adaptNode(liveNode);
  assert.equal(node.metrics?.cpu.usagePercent, 7.8);
  assert.equal(node.metrics?.memory.usedMb, 3072);
  assert.equal(node.metrics?.mcIaasDisk.usedGb, 18.2);
  assert.equal(node.metrics?.rootDisk.usedGb, null);
  assert.equal(node.uptimeSeconds, 1234.5);
  assert.deepEqual(node.health, {
    libvirt: "ok",
    network: "error",
    storage: "ok",
    invariants: "unknown",
  });
  const offline = adaptNode({ ...liveNode, reachability: "offline" });
  assert.equal(offline.status, "offline");
  assert.deepEqual(offline.metrics, node.metrics);
  assert.equal(offline.metricsObservedAt, liveNode.metrics_observed_at);
});
test("live overview metrics use real units and keep null fallbacks", () => {
  const dto = {
    infrastructure_status: "operational" as const,
    total_nodes: 1,
    online_nodes: 1,
    running_instances: 0,
    occupied_runtime_slots: 0,
    total_runtime_slots: 4,
    open_critical_conditions: 0,
    cpu_usage_percent: 0,
    memory_used_bytes: 3 * 1024 ** 3,
    memory_total_bytes: 16 * 1024 ** 3,
    storage_used_bytes: 18.2e9,
    storage_total_bytes: 115e9,
  };
  const overview = adaptOverview(dto);
  assert.equal(overview.cpuUsagePercent, 0);
  assert.equal(overview.memoryUsedMb, 3072);
  assert.equal(overview.storageUsedGb, 18.2);
  assert.equal(
    adaptOverview({ ...dto, memory_used_bytes: null }).memoryUsedMb,
    null,
  );
  const node = adaptNode({
    ...liveNode,
    metrics: null,
    health: null,
    agent_uptime_seconds: null,
  });
  assert.equal(node.metrics, null);
  assert.equal(node.health.storage, "unknown");
  assert.equal(node.uptimeSeconds, null);
});
for (const status of ["offline", "online", "unavailable", "unknown"] as const) {
  test(`Minecraft ${status} is mapped without deriving it from VM state`, () => {
    const mapped = adaptInstance({ ...instance, minecraft_status: status });
    assert.equal(mapped.minecraftStatus, status);
    assert.equal(mapped.state, "stopped");
  });
}
