import type { ControlPlaneClient } from "@/services/client";
import { mockControlPlaneClient } from "@/services/mockClient";

/**
 * Single injection point for the Control Plane transport.
 * Swap this for an HTTP adapter when the real API is available.
 */
export const controlPlane: ControlPlaneClient = mockControlPlaneClient;

export type { ControlPlaneClient };
