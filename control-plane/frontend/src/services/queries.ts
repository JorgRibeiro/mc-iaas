import { useEffect } from "react";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";

import { controlPlane, isHttpMode, subscribeAccepted } from "@/services";
import {
  ApiError,
  OperationPendingError,
  OperationUncertainError,
} from "@/services/httpClient";
import type {
  CreateInstanceInput,
  ControlPlaneSettings,
  EventLevel,
} from "@/types";

export const queryKeys = {
  overview: ["overview"] as const,
  nodes: ["nodes"] as const,
  node: (id: string) => ["nodes", id] as const,
  instances: ["instances"] as const,
  instance: (id: string) => ["instances", id] as const,
  events: ["events"] as const,
  timeseries: ["timeseries"] as const,
  monitoring: ["monitoring"] as const,
  settings: ["settings"] as const,
};
const isBrowser = typeof window !== "undefined";
const live = {
  enabled: isBrowser,
  refetchInterval: isHttpMode && isBrowser ? 3000 : false,
  retry: (failures: number, error: Error) =>
    !(error instanceof ApiError && error.status === 404) && failures < 1,
} as const;
export const overviewQuery = queryOptions({
  queryKey: queryKeys.overview,
  queryFn: () => controlPlane.getOverview(),
  ...live,
});
export const nodesQuery = queryOptions({
  queryKey: queryKeys.nodes,
  queryFn: () => controlPlane.listNodes(),
  ...live,
});
export const nodeQuery = (id: string) =>
  queryOptions({
    queryKey: queryKeys.node(id),
    queryFn: () => controlPlane.getNode(id),
    ...live,
  });
export const instancesQuery = queryOptions({
  queryKey: queryKeys.instances,
  queryFn: () => controlPlane.listInstances(),
  ...live,
});
export const instanceQuery = (id: string) =>
  queryOptions({
    queryKey: queryKeys.instance(id),
    queryFn: () => controlPlane.getInstance(id),
    ...live,
    refetchInterval: (query) =>
      query.state.error instanceof ApiError && query.state.error.status === 404
        ? false
        : live.refetchInterval,
  });
export const eventsQuery = queryOptions({
  queryKey: queryKeys.events,
  queryFn: () => controlPlane.listEvents(),
  ...live,
});
export const filteredEventsQuery = (level?: EventLevel) =>
  queryOptions({
    queryKey: [...queryKeys.events, level ?? "all"],
    queryFn: () => controlPlane.listEvents(level),
    ...live,
  });
export const timeseriesQuery = queryOptions({
  queryKey: queryKeys.timeseries,
  queryFn: () => controlPlane.getUsageTimeseries(),
  ...live,
});
export const monitoringQuery = queryOptions({
  queryKey: queryKeys.monitoring,
  queryFn: () => controlPlane.getMonitoringSummary(),
  ...live,
});
export const connectionQuery = queryOptions({
  queryKey: ["connection"],
  queryFn: () => controlPlane.getConnectionStatus(),
  enabled: isBrowser,
  refetchInterval: isBrowser ? 10_000 : false,
  retry: false,
});
export const settingsQuery = queryOptions({
  queryKey: queryKeys.settings,
  queryFn: () => controlPlane.getSettings(),
});

function useInvalidateAll() {
  const queryClient = useQueryClient();
  useEffect(
    () =>
      subscribeAccepted(() => {
        void queryClient.invalidateQueries();
      }),
    [queryClient],
  );
  return () => {
    void queryClient.invalidateQueries();
  };
}
function showMutationError(error: Error) {
  if (
    error instanceof OperationUncertainError ||
    error instanceof OperationPendingError
  )
    toast.warning("Operation needs attention", {
      description: error.message,
      duration: 15_000,
    });
  else toast.error("Request failed", { description: error.message });
}
export function useInstanceAction() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: async ({
      action,
      id,
    }: {
      action: "start" | "stop" | "restart" | "delete";
      id: string;
      name: string;
    }) => {
      if (action === "start") return controlPlane.startInstance(id);
      if (action === "stop") return controlPlane.stopInstance(id);
      if (action === "restart") return controlPlane.restartInstance(id);
      return controlPlane.deleteInstance(id);
    },
    onMutate: () => {
      toast.info("Submitting operation", {
        description: "Completion will be confirmed by the Control Plane.",
      });
    },
    onSuccess: (_data, variables) => {
      const labels = {
        start: "started",
        stop: "stopped",
        restart: "restarted",
        delete: "deleted",
      };
      toast.success(`Instance ${variables.name} ${labels[variables.action]}`, {
        description: isHttpMode
          ? "Operation confirmed."
          : "Simulated in mock mode.",
      });
    },
    onError: showMutationError,
    onSettled: invalidate,
  });
}
export function useCreateInstance() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (input: CreateInstanceInput) =>
      controlPlane.createInstance(input),
    onMutate: () => {
      toast.info("Submitting workload", {
        description: "Placement and creation will be confirmed asynchronously.",
      });
    },
    onSuccess: (instance) =>
      toast.success(`Instance ${instance.name} created`, {
        description: "Workload is stopped. Start it when ready.",
      }),
    onError: showMutationError,
    onSettled: invalidate,
  });
}
export function useReconcileNode() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: ({ id }: { id: string; name: string }) =>
      controlPlane.reconcileNode(id),
    onSuccess: (_data, variables) =>
      toast.success(`Snapshot refreshed for ${variables.name}`),
    onError: showMutationError,
    onSettled: invalidate,
  });
}
export function useUpdateSettings() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (settings: ControlPlaneSettings) =>
      controlPlane.updateSettings(settings),
    onSuccess: () =>
      toast.success("Local settings saved", {
        description: "In memory only; server configuration is unchanged.",
      }),
    onSettled: invalidate,
  });
}
