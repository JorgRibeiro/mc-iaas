import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { a as eventsQuery, l as nodesQuery, s as instancesQuery, t as Button, u as overviewQuery } from "./queries-D6pnQp7P.mjs";
import { h as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { C as Gauge, D as Clock, E as Cpu, H as ArrowUpRight, T as Database, U as Activity, V as Boxes, l as Server, s as ShieldAlert, v as MemoryStick } from "../_libs/lucide-react.mjs";
import { a as TableSkeleton, i as PageHeader, r as ErrorState, t as CardsSkeleton } from "./StateViews-CO8w9HyP.mjs";
import { a as TableHeader, c as formatMb, d as formatUptime, i as TableHead, l as formatPercent, n as TableBody, o as TableRow, r as TableCell, s as formatGb, t as Table } from "./format-Bdjq67dT.mjs";
import { t as EventsTable } from "./EventsTable-BIcR367i.mjs";
import { n as StatCard, t as MetricBar } from "./StatCard-VB2AFQE5.mjs";
import { a as ReadyBadge, i as NodeStatusBadge, n as InstanceStateBadge } from "./StatusBadge-K-Qktd-I.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-CJzqQR_5.js
var import_jsx_runtime = require_jsx_runtime();
function NodeCard({ node }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "panel flex flex-col gap-4 p-4 transition-colors hover:border-border-strong",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-start justify-between gap-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Link, {
						to: "/nodes/$nodeId",
						params: { nodeId: node.id },
						className: "group inline-flex items-center gap-1.5 font-medium tracking-tight",
						children: [node.name, /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowUpRight, { className: "h-3.5 w-3.5 text-muted-foreground transition-transform group-hover:translate-x-0.5" })]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex flex-wrap items-center gap-1.5",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(NodeStatusBadge, { status: node.status }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReadyBadge, { ready: node.ready })]
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: "flex items-center gap-1 text-xs text-muted-foreground",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Clock, {
						className: "h-3.5 w-3.5",
						"aria-hidden": true
					}), formatUptime(node.uptimeSeconds)]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid grid-cols-3 gap-3 border-y border-border py-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
						label: "Active",
						value: node.capacity.activeInstances
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
						label: "Slots used",
						value: node.capacity.occupiedRuntimeSlots
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
						label: "Available",
						value: node.capacity.availableSlots
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2.5",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
						label: "CPU",
						used: node.metrics.cpu.usagePercent,
						total: 100,
						hint: formatPercent(node.metrics.cpu.usagePercent)
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
						label: "Memory",
						used: node.metrics.memory.usedMb,
						total: node.metrics.memory.totalMb,
						hint: `${formatMb(node.metrics.memory.usedMb)} / ${formatMb(node.metrics.memory.totalMb)}`
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
						label: "MC-IaaS disk",
						used: node.metrics.mcIaasDisk.usedGb,
						total: node.metrics.mcIaasDisk.totalGb,
						hint: `${formatGb(node.metrics.mcIaasDisk.usedGb)} / ${formatGb(node.metrics.mcIaasDisk.totalGb)}`
					})
				]
			})
		]
	});
}
function Stat({ label, value }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-0.5",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "metric-label",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "tabular text-lg leading-none font-semibold",
			children: value
		})]
	});
}
function OverviewPage() {
	const overview = useQuery(overviewQuery);
	const nodes = useQuery(nodesQuery);
	const instances = useQuery(instancesQuery);
	const events = useQuery(eventsQuery);
	const error = overview.error ?? nodes.error ?? instances.error ?? events.error;
	const summary = overview.data;
	const nodeList = nodes.data;
	const instanceList = instances.data;
	const eventList = events.data;
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: error.message,
		onRetry: () => void Promise.all([
			overview.refetch(),
			nodes.refetch(),
			instances.refetch(),
			events.refetch()
		])
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: "Infrastructure overview",
			description: "Fleet health, workload capacity and recent control plane activity. All values are supplied by the in-memory mock adapter."
		}),
		!summary ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardsSkeleton, { count: 8 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid gap-3 sm:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-8",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Infrastructure",
					value: summary.status === "operational" ? "Operational" : summary.status === "degraded" ? "Degraded" : "Down",
					icon: Gauge,
					caption: `${summary.alerts} open invariants`,
					className: "2xl:col-span-2"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Compute nodes",
					value: `${summary.nodesOnline}/${summary.nodesTotal}`,
					icon: Server,
					caption: "Online / registered"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Active workloads",
					value: summary.activeWorkloads,
					icon: Boxes,
					caption: "Running instances"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Runtime slots",
					value: `${summary.slotsUsed}/${summary.slotsTotal}`,
					icon: Activity,
					bar: {
						used: summary.slotsUsed,
						total: summary.slotsTotal
					}
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "CPU usage",
					value: formatPercent(summary.cpuUsagePercent),
					icon: Cpu,
					bar: {
						used: summary.cpuUsagePercent,
						total: 100
					},
					tooltip: "Average usage across online compute nodes."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Memory usage",
					value: formatMb(summary.memoryUsedMb),
					icon: MemoryStick,
					bar: {
						used: summary.memoryUsedMb,
						total: summary.memoryTotalMb
					},
					caption: `of ${formatMb(summary.memoryTotalMb)}`
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Storage usage",
					value: formatGb(summary.storageUsedGb),
					icon: Database,
					bar: {
						used: summary.storageUsedGb,
						total: summary.storageTotalGb
					},
					caption: `of ${formatGb(summary.storageTotalGb)}`
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Open invariants",
					value: summary.alerts,
					icon: ShieldAlert,
					caption: summary.alerts ? "Requires review" : "No violations"
				})
			]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionHeader, {
			title: "Compute nodes",
			description: "Health and resource pressure by host.",
			to: "/nodes"
		}),
		!nodeList ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardsSkeleton, { count: 2 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "grid gap-3 lg:grid-cols-2",
			children: nodeList.map((node) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NodeCard, { node }, node.id))
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid gap-6 2xl:grid-cols-2",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "min-w-0 space-y-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionHeader, {
					title: "Recent instances",
					description: "Latest workload definitions and runtime state.",
					to: "/instances"
				}), !instanceList ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 3 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "panel overflow-x-auto",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Table, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, {
						className: "hover:bg-transparent",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Name" }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Node" }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "State" }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
								className: "text-right",
								children: "Public port"
							})
						]
					}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableBody, { children: instanceList.slice(0, 5).map((instance) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/instances/$instanceId",
							params: { instanceId: instance.id },
							className: "font-medium hover:text-primary",
							children: instance.name
						}) }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
							className: "text-xs text-muted-foreground",
							children: nodeList?.find((node) => node.id === instance.computeNodeId)?.name ?? "Unassigned"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstanceStateBadge, { state: instance.state }) }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
							className: "tabular text-right text-xs",
							children: instance.runtime?.externalPort ?? "—"
						})
					] }, instance.id)) })] })
				})]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "min-w-0 space-y-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionHeader, {
					title: "Recent events",
					description: "Lifecycle and recovery activity.",
					to: "/activity"
				}), !eventList ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 5 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EventsTable, {
					events: eventList.slice(0, 5),
					compact: true
				})]
			})]
		})
	] });
}
function SectionHeader({ title, description, to }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-end justify-between gap-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
			className: "text-sm font-semibold",
			children: title
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "mt-0.5 text-xs text-muted-foreground",
			children: description
		})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			asChild: true,
			variant: "ghost",
			size: "sm",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
				to,
				children: "View all"
			})
		})]
	});
}
//#endregion
export { OverviewPage as component };
