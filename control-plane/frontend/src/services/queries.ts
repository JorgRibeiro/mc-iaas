import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";

import { controlPlane } from "@/services";
import type { CreateInstanceInput, ControlPlaneSettings } from "@/types";

export const queryKeys = {
  overview: ["overview"] as const,
  nodes: ["nodes"] as const,
  node: (id: string) => ["nodes", id] as const,
  instances: ["instances"] as const,
  instance: (id: string) => ["instances", id] as const,
  events: ["events"] as const,
  timeseries: ["timeseries"] as const,
  settings: ["settings"] as const,
};

export const overviewQuery = queryOptions({
  queryKey: queryKeys.overview,
  queryFn: () => controlPlane.getOverview(),
});

export const nodesQuery = queryOptions({
  queryKey: queryKeys.nodes,
  queryFn: () => controlPlane.listNodes(),
});

export const nodeQuery = (id: string) =>
  queryOptions({
    queryKey: queryKeys.node(id),
    queryFn: () => controlPlane.getNode(id),
  });

export const instancesQuery = queryOptions({
  queryKey: queryKeys.instances,
  queryFn: () => controlPlane.listInstances(),
});

export const instanceQuery = (id: string) =>
  queryOptions({
    queryKey: queryKeys.instance(id),
    queryFn: () => controlPlane.getInstance(id),
  });

export const eventsQuery = queryOptions({
  queryKey: queryKeys.events,
  queryFn: () => controlPlane.listEvents(),
});

export const timeseriesQuery = queryOptions({
  queryKey: queryKeys.timeseries,
  queryFn: () => controlPlane.getUsageTimeseries(),
});

export const settingsQuery = queryOptions({
  queryKey: queryKeys.settings,
  queryFn: () => controlPlane.getSettings(),
});

function useInvalidateAll() {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries();
  };
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
    onSuccess: (_data, variables) => {
      invalidate();
      const labels: Record<string, string> = {
        start: "started",
        stop: "stopped",
        restart: "restarted",
        delete: "deleted",
      };
      toast.success(`Instance ${variables.name} ${labels[variables.action]}`, {
        description:
          "Mock lifecycle transition — no compute node was contacted.",
      });
    },
    onError: (error: Error) =>
      toast.error("Lifecycle action failed", { description: error.message }),
  });
}

export function useCreateInstance() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (input: CreateInstanceInput) =>
      controlPlane.createInstance(input),
    onSuccess: (instance) => {
      invalidate();
      toast.success(`Instance ${instance.name} scheduled`, {
        description:
          "Provisioning simulated locally. Control Plane API not connected yet.",
      });
    },
    onError: (error: Error) =>
      toast.error("Creation failed", { description: error.message }),
  });
}

export function useReconcileNode() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: ({ id }: { id: string; name: string }) =>
      controlPlane.reconcileNode(id),
    onSuccess: (_data, variables) => {
      invalidate();
      toast.success(`Reconcile requested for ${variables.name}`, {
        description:
          "Simulated reconciliation, recovery events appended to the activity log.",
      });
    },
  });
}

export function useUpdateSettings() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (settings: ControlPlaneSettings) =>
      controlPlane.updateSettings(settings),
    onSuccess: () => {
      invalidate();
      toast.success("Settings saved locally", {
        description:
          "Stored in memory only until the Control Plane API is connected.",
      });
    },
  });
}
