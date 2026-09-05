import type { ControlPlaneClient } from "./client.ts";
import type {
  ControlPlaneSettings,
  CreateInstanceInput,
  Operation,
  EventLevel,
} from "../types/index.ts";
import {
  adaptNode,
  adaptInstance,
  adaptOverview,
  adaptEvent,
  adaptMonitoring,
} from "./adapters.ts";
import type {
  NodeDto,
  InstanceDto,
  OverviewDto,
  EventDto,
  MonitoringDto,
} from "./adapters.ts";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}
export class OperationUncertainError extends Error {}
export class OperationPendingError extends Error {}

export async function waitForOperation(
  read: () => Promise<Operation>,
  {
    attempts = 120,
    intervalMs = 1000,
    timeoutMs = 120_000,
    sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms)),
  } = {},
): Promise<Operation> {
  const deadline = Date.now() + timeoutMs;
  for (
    let attempt = 0;
    attempt < attempts && Date.now() < deadline;
    attempt++
  ) {
    const operation = await read();
    if (operation.status === "succeeded") return operation;
    if (operation.status === "failed")
      throw new Error(operation.error_message ?? "Operation failed.");
    if (operation.status === "uncertain")
      throw new OperationUncertainError(
        `Operation ${operation.id} has an unconfirmed outcome. Do not submit it again; the Control Plane will evaluate its observations.`,
      );
    if (attempt + 1 < attempts) await sleep(intervalMs);
  }
  throw new OperationPendingError(
    "Operation accepted and still pending. Automatic tracking has ended; inspect the instance before submitting another action.",
  );
}

export class HttpControlPlaneClient implements ControlPlaneClient {
  private baseUrl: string;
  private fetcher: typeof fetch;
  private onAccepted: () => void;
  private settings: ControlPlaneSettings = {
    controlPlaneName: "MC-IaaS Control Plane",
    environment: "development",
    refreshIntervalSeconds: 3,
    defaultMemoryMb: 2048,
    defaultVcpus: 1,
    maxInstancesPerNode: 4,
  };
  constructor(
    baseUrl: string,
    fetcher: typeof fetch = fetch,
    onAccepted: () => void = () => {},
  ) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.fetcher = fetcher.bind(globalThis);
    this.onAccepted = onAccepted;
  }
  private async request<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    let response: Response;
    try {
      response = await this.fetcher(this.baseUrl + path, {
        method,
        signal: AbortSignal.timeout(10_000),
        headers:
          body === undefined ? {} : { "Content-Type": "application/json" },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch (error) {
      console.error("[ControlPlane fetch failed]", {
        method,
        url: this.baseUrl + path,
        error,
      });
      throw new ApiError(
        method === "GET"
          ? "Cannot reach the Control Plane. Check the API URL and connection."
          : "Request outcome is unknown. Check the instance before submitting again.",
        0,
      );
    }
    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      throw new ApiError(
        typeof payload?.detail === "string"
          ? payload.detail
          : response.status === 422
            ? "Invalid request. Check the workload parameters."
            : `Control Plane request failed (${response.status}).`,
        response.status,
      );
    }
    return response.json() as Promise<T>;
  }
  async getOverview() {
    return adaptOverview(await this.request<OverviewDto>("/api/v1/overview"));
  }
  async listNodes() {
    return (await this.request<NodeDto[]>("/api/v1/nodes")).map(adaptNode);
  }
  async getNode(id: string) {
    return adaptNode(
      await this.request<NodeDto>(`/api/v1/nodes/${encodeURIComponent(id)}`),
    );
  }
  async reconcileNode(id: string) {
    await this.request(
      `/api/v1/nodes/${encodeURIComponent(id)}/refresh`,
      "POST",
    );
  }
  async listInstances() {
    return (await this.request<InstanceDto[]>("/api/v1/instances")).map(
      adaptInstance,
    );
  }
  async getInstance(id: string) {
    return adaptInstance(
      await this.request<InstanceDto>(
        `/api/v1/instances/${encodeURIComponent(id)}`,
      ),
    );
  }
  async getOperation(id: string) {
    return this.request<Operation>(
      `/api/v1/operations/${encodeURIComponent(id)}`,
    );
  }
  private async mutate(path: string, method: string, payload?: unknown) {
    const accepted = await this.request<{
      operation_id: string;
      instance_id: string;
    }>(path, method, payload);
    this.onAccepted();
    try {
      await waitForOperation(() => this.getOperation(accepted.operation_id));
    } catch (error) {
      if (error instanceof ApiError)
        throw new OperationPendingError(
          `Operation ${accepted.operation_id} was accepted but tracking is unavailable. Check its outcome before submitting again.`,
        );
      throw error;
    }
    return accepted;
  }
  async createInstance(input: CreateInstanceInput) {
    const accepted = await this.mutate("/api/v1/instances", "POST", {
      name: input.name,
      memory_mb: input.memoryMb,
      vcpus: input.vcpus,
      minecraft_version: input.minecraftVersion,
      vm_username: input.vmUsername,
      accept_eula: input.acceptEula,
    });
    return this.getInstance(accepted.instance_id);
  }
  async startInstance(id: string) {
    await this.mutate(
      `/api/v1/instances/${encodeURIComponent(id)}/start`,
      "POST",
    );
  }
  async stopInstance(id: string) {
    await this.mutate(
      `/api/v1/instances/${encodeURIComponent(id)}/stop`,
      "POST",
    );
  }
  async restartInstance(id: string) {
    await this.mutate(
      `/api/v1/instances/${encodeURIComponent(id)}/restart`,
      "POST",
    );
  }
  async deleteInstance(id: string) {
    await this.mutate(`/api/v1/instances/${encodeURIComponent(id)}`, "DELETE");
  }
  async listEvents(level?: EventLevel) {
    return (
      await this.request<EventDto[]>(
        `/api/v1/events?limit=100${level ? `&level=${level}` : ""}`,
      )
    ).map(adaptEvent);
  }
  async getMonitoringSummary() {
    return adaptMonitoring(
      await this.request<MonitoringDto>("/api/v1/monitoring/summary"),
    );
  }
  async getUsageTimeseries() {
    return (await this.getMonitoringSummary()).timeseries;
  }
  async getConnectionStatus() {
    await this.request("/health");
    await this.request("/ready");
    return "connected" as const;
  }
  async getSettings() {
    return structuredClone(this.settings);
  }
  async updateSettings(settings: ControlPlaneSettings) {
    this.settings = structuredClone(settings);
    return this.getSettings();
  }
}
