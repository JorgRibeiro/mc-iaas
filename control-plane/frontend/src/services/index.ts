import type { ControlPlaneClient } from "@/services/client";
import { mockControlPlaneClient } from "@/services/mockClient";
import { HttpControlPlaneClient } from "@/services/httpClient";

export const isHttpMode = import.meta.env["VITE_CONTROL_PLANE_MODE"] !== "mock";
export const apiUrl =
  import.meta.env["VITE_CONTROL_PLANE_API_URL"] || "http://127.0.0.1:8001";
const acceptedListeners = new Set<() => void>();
export function subscribeAccepted(listener: () => void) {
  acceptedListeners.add(listener);
  return () => {
    acceptedListeners.delete(listener);
  };
}
export const controlPlane: ControlPlaneClient = isHttpMode
  ? new HttpControlPlaneClient(apiUrl, globalThis.fetch.bind(globalThis), () =>
      acceptedListeners.forEach((listener) => listener()),
    )
  : mockControlPlaneClient;
export type { ControlPlaneClient };
