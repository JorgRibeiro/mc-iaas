import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { F as require_jsx_runtime, j as Slot } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { a as useQueryClient, n as queryOptions, t as useMutation } from "../_libs/tanstack__react-query.mjs";
import { n as clsx, t as cva } from "../_libs/class-variance-authority+clsx.mjs";
import { t as twMerge } from "../_libs/tailwind-merge.mjs";
import { n as toast } from "../_libs/sonner.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/queries-D6pnQp7P.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function cn(...inputs) {
	return twMerge(clsx(inputs));
}
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
			destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
			outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
			secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
			ghost: "hover:bg-accent hover:text-accent-foreground",
			link: "text-primary underline-offset-4 hover:underline"
		},
		size: {
			default: "h-9 px-4 py-2",
			sm: "h-8 rounded-md px-3 text-xs",
			lg: "h-10 rounded-md px-8",
			icon: "h-9 w-9"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var Button = import_react.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		ref,
		...props
	});
});
Button.displayName = "Button";
var CURRENT_MINECRAFT_VERSION = "26.2";
var mockInstances = [
	{
		id: "inst-survival-01",
		name: "survival-01",
		computeNodeId: "node-jorge",
		state: "running",
		vmUsername: "mcadmin",
		memoryMb: 2048,
		vcpus: 1,
		minecraftVersion: "26.2",
		runtime: {
			slot: 1,
			ip: "10.50.0.10",
			externalPort: 25565
		},
		minecraftStatus: "online",
		createdAt: "2026-08-14T13:22:09Z",
		persistentStorage: "attached",
		metrics: {
			cpuUsagePercent: 27.8,
			cpuTimeSeconds: 18942,
			memoryConfiguredMb: 2048,
			memoryCurrentMb: 2048,
			memoryRssMb: 1712,
			systemStorageGb: {
				usedGb: 4.1,
				totalGb: 10
			},
			dataStorageGb: {
				usedGb: 2.7,
				totalGb: 20
			},
			networkRxMb: 812.4,
			networkTxMb: 1340.9
		}
	},
	{
		id: "inst-creative-01",
		name: "creative-01",
		computeNodeId: "node-jorge",
		state: "stopped",
		vmUsername: "mcadmin",
		memoryMb: 2048,
		vcpus: 1,
		minecraftVersion: "26.2",
		runtime: null,
		minecraftStatus: "offline",
		createdAt: "2026-08-19T08:05:41Z",
		persistentStorage: "attached",
		metrics: {
			cpuUsagePercent: 0,
			cpuTimeSeconds: 6421,
			memoryConfiguredMb: 2048,
			memoryCurrentMb: 0,
			memoryRssMb: 0,
			systemStorageGb: {
				usedGb: 3.8,
				totalGb: 10
			},
			dataStorageGb: {
				usedGb: 1.2,
				totalGb: 20
			},
			networkRxMb: 210.5,
			networkTxMb: 322.1
		}
	},
	{
		id: "inst-hardcore-lab",
		name: "hardcore-lab",
		computeNodeId: "node-raylandson",
		state: "unavailable",
		vmUsername: "mcadmin",
		memoryMb: 1024,
		vcpus: 1,
		minecraftVersion: "26.2",
		runtime: null,
		minecraftStatus: "unknown",
		createdAt: "2026-08-21T17:48:30Z",
		persistentStorage: "detached",
		metrics: {
			cpuUsagePercent: 0,
			cpuTimeSeconds: 0,
			memoryConfiguredMb: 1024,
			memoryCurrentMb: 0,
			memoryRssMb: 0,
			systemStorageGb: {
				usedGb: 3.1,
				totalGb: 10
			},
			dataStorageGb: {
				usedGb: .4,
				totalGb: 20
			},
			networkRxMb: 0,
			networkTxMb: 0
		}
	}
];
var mockEvents = [
	{
		id: "evt-01",
		timestamp: "2026-08-27T21:02:44Z",
		level: "info",
		component: "lifecycle",
		event: "instance.start.completed",
		target: "survival-01",
		message: "Instance reached running state and Minecraft service reported online."
	},
	{
		id: "evt-02",
		timestamp: "2026-08-27T21:02:11Z",
		level: "info",
		component: "runtime",
		event: "instance.start.runtime_allocated",
		target: "survival-01",
		message: "Runtime slot 1 allocated with internal address and external port mapping."
	},
	{
		id: "evt-03",
		timestamp: "2026-08-27T21:01:58Z",
		level: "info",
		component: "lifecycle",
		event: "instance.start.requested",
		target: "survival-01",
		message: "Start requested from control plane console."
	},
	{
		id: "evt-04",
		timestamp: "2026-08-27T18:40:02Z",
		level: "info",
		component: "lifecycle",
		event: "instance.stop.completed",
		target: "creative-01",
		message: "Instance stopped gracefully, runtime slot released."
	},
	{
		id: "evt-05",
		timestamp: "2026-08-26T10:12:37Z",
		level: "info",
		component: "recovery",
		event: "recovery.completed",
		target: "JORGE",
		message: "Recovery routine finished, node invariants back to consistent state."
	},
	{
		id: "evt-06",
		timestamp: "2026-08-26T10:11:04Z",
		level: "info",
		component: "recovery",
		event: "recovery.runtime_released",
		target: "JORGE",
		message: "Stale runtime slot released during reconciliation."
	},
	{
		id: "evt-07",
		timestamp: "2026-08-26T10:09:50Z",
		level: "warning",
		component: "recovery",
		event: "recovery.started",
		target: "JORGE",
		message: "Divergence detected between declared and observed instances."
	},
	{
		id: "evt-08",
		timestamp: "2026-08-26T09:57:12Z",
		level: "error",
		component: "agent",
		event: "node.heartbeat.missed",
		target: "RAYLANDSON-COMPUTE",
		message: "Three consecutive heartbeats missed, node marked offline."
	},
	{
		id: "evt-09",
		timestamp: "2026-08-26T09:12:44Z",
		level: "warning",
		component: "auth",
		event: "auth.failed",
		target: "control-plane",
		message: "Rejected agent handshake due to invalid credential fingerprint."
	},
	{
		id: "evt-10",
		timestamp: "2026-08-25T22:31:19Z",
		level: "info",
		component: "lifecycle",
		event: "instance.created",
		target: "hardcore-lab",
		message: "Instance definition persisted and scheduled to compute node."
	}
];
var mockTimeseries = [
	{
		t: "20:10",
		cpu: 22,
		memory: 30
	},
	{
		t: "20:20",
		cpu: 26,
		memory: 32
	},
	{
		t: "20:30",
		cpu: 24,
		memory: 33
	},
	{
		t: "20:40",
		cpu: 35,
		memory: 34
	},
	{
		t: "20:50",
		cpu: 31,
		memory: 34
	},
	{
		t: "21:00",
		cpu: 29,
		memory: 35
	},
	{
		t: "21:10",
		cpu: 33,
		memory: 34
	},
	{
		t: "21:20",
		cpu: 31,
		memory: 34
	}
];
var mockNodes = [{
	id: "node-jorge",
	name: "JORGE",
	status: "healthy",
	ready: true,
	agentVersion: "0.4.2",
	uptimeSeconds: 412530,
	lastSeen: "2026-08-27T21:04:12Z",
	region: "lab-a",
	capacity: {
		maxActiveInstances: 4,
		activeInstances: 1,
		occupiedRuntimeSlots: 1,
		availableSlots: 3
	},
	health: {
		libvirt: "ok",
		network: "ok",
		storage: "ok",
		invariants: "ok"
	},
	metrics: {
		cpu: {
			usagePercent: 31.4,
			cores: 8,
			load1m: .82,
			load5m: .64,
			load15m: .51
		},
		memory: {
			totalMb: 32768,
			usedMb: 11264,
			availableMb: 21504
		},
		rootDisk: {
			label: "root",
			totalGb: 240,
			usedGb: 78
		},
		mcIaasDisk: {
			label: "mc-iaas",
			totalGb: 500,
			usedGb: 143
		}
	},
	invariants: []
}, {
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
		availableSlots: 0
	},
	health: {
		libvirt: "unknown",
		network: "error",
		storage: "unknown",
		invariants: "unknown"
	},
	metrics: {
		cpu: {
			usagePercent: 0,
			cores: 4,
			load1m: 0,
			load5m: 0,
			load15m: 0
		},
		memory: {
			totalMb: 16384,
			usedMb: 0,
			availableMb: 0
		},
		rootDisk: {
			label: "root",
			totalGb: 120,
			usedGb: 0
		},
		mcIaasDisk: {
			label: "mc-iaas",
			totalGb: 250,
			usedGb: 0
		}
	},
	invariants: [{
		id: "inv-1",
		severity: "critical",
		code: "AGENT_UNREACHABLE",
		detail: "Compute agent heartbeat missing for more than 15 minutes.",
		timestamp: "2026-08-26T09:56:00Z"
	}, {
		id: "inv-2",
		severity: "warning",
		code: "RUNTIME_SLOTS_UNVERIFIED",
		detail: "Runtime slot allocation table could not be reconciled while node is offline.",
		timestamp: "2026-08-26T10:02:11Z"
	}]
}];
var LATENCY_MS = 320;
/** In-memory mutable state so the mock UI feels alive across navigation. */
var state = {
	nodes: structuredClone(mockNodes),
	instances: structuredClone(mockInstances),
	events: structuredClone(mockEvents),
	settings: {
		controlPlaneName: "MC-IaaS Control Plane",
		refreshIntervalSeconds: 30,
		environment: "development",
		defaultMemoryMb: 2048,
		defaultVcpus: 1,
		maxInstancesPerNode: 4
	}
};
function delay(value) {
	return new Promise((resolve) => setTimeout(() => resolve(value), LATENCY_MS));
}
function nowIso() {
	return (/* @__PURE__ */ new Date()).toISOString();
}
function pushEvent(e) {
	state.events = [{
		...e,
		id: `evt-${Math.random().toString(36).slice(2, 9)}`,
		timestamp: nowIso()
	}, ...state.events];
}
function recomputeCapacity() {
	for (const node of state.nodes) {
		if (node.status === "offline") {
			node.capacity.activeInstances = 0;
			node.capacity.occupiedRuntimeSlots = 0;
			node.capacity.availableSlots = 0;
			continue;
		}
		const active = state.instances.filter((i) => i.computeNodeId === node.id && (i.state === "running" || i.state === "starting"));
		node.capacity.activeInstances = active.length;
		node.capacity.occupiedRuntimeSlots = active.filter((i) => i.runtime).length;
		node.capacity.availableSlots = Math.max(0, node.capacity.maxActiveInstances - node.capacity.activeInstances);
	}
}
function requireInstance(id) {
	const instance = state.instances.find((i) => i.id === id);
	if (!instance) throw new Error(`Instance ${id} not found`);
	return instance;
}
function setState(instance, next) {
	instance.state = next;
	if (next === "running") {
		instance.minecraftStatus = "online";
		instance.runtime ??= {
			slot: state.instances.filter((i) => i.runtime).length % 8 + 1,
			ip: `10.50.0.${10 + state.instances.indexOf(instance)}`,
			externalPort: 25565 + state.instances.indexOf(instance)
		};
		instance.metrics.memoryCurrentMb = instance.memoryMb;
		instance.metrics.memoryRssMb = Math.round(instance.memoryMb * .82);
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
/**
* Single injection point for the Control Plane transport.
* Swap this for an HTTP adapter when the real API is available.
*/
var controlPlane = {
	async getOverview() {
		recomputeCapacity();
		const online = state.nodes.filter((n) => n.status !== "offline");
		const slotsTotal = state.nodes.reduce((acc, n) => acc + n.capacity.maxActiveInstances, 0);
		const slotsUsed = state.nodes.reduce((acc, n) => acc + n.capacity.occupiedRuntimeSlots, 0);
		const memoryTotalMb = online.reduce((acc, n) => acc + n.metrics.memory.totalMb, 0);
		const memoryUsedMb = online.reduce((acc, n) => acc + n.metrics.memory.usedMb, 0);
		const storageTotalGb = state.nodes.reduce((acc, n) => acc + n.metrics.mcIaasDisk.totalGb, 0);
		const storageUsedGb = state.nodes.reduce((acc, n) => acc + n.metrics.mcIaasDisk.usedGb, 0);
		const cpu = online.length ? online.reduce((acc, n) => acc + n.metrics.cpu.usagePercent, 0) / online.length : 0;
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
			alerts
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
			message: "Reconciliation requested from control plane console (mock)."
		});
		pushEvent({
			level: "info",
			component: "recovery",
			event: "recovery.completed",
			target: node.name,
			message: "Mock reconciliation finished, no state changes applied."
		});
		return delay(void 0);
	},
	listInstances() {
		return delay(structuredClone(state.instances));
	},
	async getInstance(id) {
		return delay(structuredClone(requireInstance(id)));
	},
	async createInstance(input) {
		const instance = {
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
				systemStorageGb: {
					usedGb: 0,
					totalGb: 10
				},
				dataStorageGb: {
					usedGb: 0,
					totalGb: 20
				},
				networkRxMb: 0,
				networkTxMb: 0
			}
		};
		state.instances = [instance, ...state.instances];
		pushEvent({
			level: "info",
			component: "lifecycle",
			event: "instance.created",
			target: instance.name,
			message: "Instance definition accepted and scheduled to compute node (mock)."
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
			message: "Start requested from control plane console."
		});
		setState(instance, "running");
		pushEvent({
			level: "info",
			component: "runtime",
			event: "instance.start.runtime_allocated",
			target: instance.name,
			message: "Runtime slot allocated with internal address and external port mapping."
		});
		pushEvent({
			level: "info",
			component: "lifecycle",
			event: "instance.start.completed",
			target: instance.name,
			message: "Instance reached running state (mock)."
		});
		return delay(void 0);
	},
	async stopInstance(id) {
		const instance = requireInstance(id);
		setState(instance, "stopped");
		pushEvent({
			level: "info",
			component: "lifecycle",
			event: "instance.stop.completed",
			target: instance.name,
			message: "Instance stopped, runtime slot released (mock)."
		});
		return delay(void 0);
	},
	async restartInstance(id) {
		const instance = requireInstance(id);
		setState(instance, "running");
		pushEvent({
			level: "info",
			component: "lifecycle",
			event: "instance.restart.completed",
			target: instance.name,
			message: "Instance restarted (mock)."
		});
		return delay(void 0);
	},
	async deleteInstance(id) {
		const instance = requireInstance(id);
		state.instances = state.instances.filter((i) => i.id !== id);
		pushEvent({
			level: "warning",
			component: "lifecycle",
			event: "instance.delete.completed",
			target: instance.name,
			message: "Instance and persistent storage removed (mock)."
		});
		recomputeCapacity();
		return delay(void 0);
	},
	listEvents() {
		return delay(structuredClone(state.events));
	},
	getUsageTimeseries() {
		return delay(structuredClone(mockTimeseries));
	},
	getSettings() {
		return delay(structuredClone(state.settings));
	},
	updateSettings(settings) {
		state.settings = { ...settings };
		return delay(structuredClone(state.settings));
	}
};
var queryKeys = {
	overview: ["overview"],
	nodes: ["nodes"],
	node: (id) => ["nodes", id],
	instances: ["instances"],
	instance: (id) => ["instances", id],
	events: ["events"],
	timeseries: ["timeseries"],
	settings: ["settings"]
};
var overviewQuery = queryOptions({
	queryKey: queryKeys.overview,
	queryFn: () => controlPlane.getOverview()
});
var nodesQuery = queryOptions({
	queryKey: queryKeys.nodes,
	queryFn: () => controlPlane.listNodes()
});
var nodeQuery = (id) => queryOptions({
	queryKey: queryKeys.node(id),
	queryFn: () => controlPlane.getNode(id)
});
var instancesQuery = queryOptions({
	queryKey: queryKeys.instances,
	queryFn: () => controlPlane.listInstances()
});
var instanceQuery = (id) => queryOptions({
	queryKey: queryKeys.instance(id),
	queryFn: () => controlPlane.getInstance(id)
});
var eventsQuery = queryOptions({
	queryKey: queryKeys.events,
	queryFn: () => controlPlane.listEvents()
});
var timeseriesQuery = queryOptions({
	queryKey: queryKeys.timeseries,
	queryFn: () => controlPlane.getUsageTimeseries()
});
var settingsQuery = queryOptions({
	queryKey: queryKeys.settings,
	queryFn: () => controlPlane.getSettings()
});
function useInvalidateAll() {
	const queryClient = useQueryClient();
	return () => {
		queryClient.invalidateQueries();
	};
}
function useInstanceAction() {
	const invalidate = useInvalidateAll();
	return useMutation({
		mutationFn: async ({ action, id }) => {
			if (action === "start") return controlPlane.startInstance(id);
			if (action === "stop") return controlPlane.stopInstance(id);
			if (action === "restart") return controlPlane.restartInstance(id);
			return controlPlane.deleteInstance(id);
		},
		onSuccess: (_data, variables) => {
			invalidate();
			toast.success(`Instance ${variables.name} ${{
				start: "started",
				stop: "stopped",
				restart: "restarted",
				delete: "deleted"
			}[variables.action]}`, { description: "Mock lifecycle transition — no compute node was contacted." });
		},
		onError: (error) => toast.error("Lifecycle action failed", { description: error.message })
	});
}
function useCreateInstance() {
	const invalidate = useInvalidateAll();
	return useMutation({
		mutationFn: (input) => controlPlane.createInstance(input),
		onSuccess: (instance) => {
			invalidate();
			toast.success(`Instance ${instance.name} scheduled`, { description: "Provisioning simulated locally. Control Plane API not connected yet." });
		},
		onError: (error) => toast.error("Creation failed", { description: error.message })
	});
}
function useReconcileNode() {
	const invalidate = useInvalidateAll();
	return useMutation({
		mutationFn: ({ id }) => controlPlane.reconcileNode(id),
		onSuccess: (_data, variables) => {
			invalidate();
			toast.success(`Reconcile requested for ${variables.name}`, { description: "Simulated reconciliation, recovery events appended to the activity log." });
		}
	});
}
function useUpdateSettings() {
	const invalidate = useInvalidateAll();
	return useMutation({
		mutationFn: (settings) => controlPlane.updateSettings(settings),
		onSuccess: () => {
			invalidate();
			toast.success("Settings saved locally", { description: "Stored in memory only until the Control Plane API is connected." });
		}
	});
}
//#endregion
export { eventsQuery as a, nodeQuery as c, settingsQuery as d, timeseriesQuery as f, useUpdateSettings as g, useReconcileNode as h, cn as i, nodesQuery as l, useInstanceAction as m, CURRENT_MINECRAFT_VERSION as n, instanceQuery as o, useCreateInstance as p, buttonVariants as r, instancesQuery as s, Button as t, overviewQuery as u };
