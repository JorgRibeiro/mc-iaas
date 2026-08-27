import { i as __toESM } from "./_runtime.mjs";
import { u as require_react } from "./_libs/@floating-ui/react-dom+[...].mjs";
import { F as require_jsx_runtime } from "./_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "./_libs/tanstack__react-query.mjs";
import { a as eventsQuery, c as nodeQuery, h as useReconcileNode, l as nodesQuery, s as instancesQuery, t as Button } from "./_ssr/queries-D6pnQp7P.mjs";
import { h as Link } from "./_libs/@tanstack/react-router+[...].mjs";
import { E as Cpu, T as Database, U as Activity, d as RotateCw, l as Server, o as ShieldCheck, v as MemoryStick } from "./_libs/lucide-react.mjs";
import { a as TableSkeleton, i as PageHeader, n as EmptyState, r as ErrorState } from "./_ssr/StateViews-CO8w9HyP.mjs";
import { a as TableHeader, c as formatMb, d as formatUptime, i as TableHead, l as formatPercent, n as TableBody, o as TableRow, p as relativeTime, r as TableCell, s as formatGb, t as Table, u as formatTimestamp } from "./_ssr/format-Bdjq67dT.mjs";
import { t as EventsTable } from "./_ssr/EventsTable-BIcR367i.mjs";
import { n as StatCard, t as MetricBar } from "./_ssr/StatCard-VB2AFQE5.mjs";
import { a as ReadyBadge, i as NodeStatusBadge, o as SeverityBadge, t as HealthBadge } from "./_ssr/StatusBadge-K-Qktd-I.mjs";
import { i as TabsTrigger, n as TabsContent, r as TabsList, t as Tabs } from "./_ssr/tabs-DBCPkxut.mjs";
import { a as AlertDialogDescription, c as AlertDialogTitle, i as AlertDialogContent, n as AlertDialogAction, o as AlertDialogFooter, r as AlertDialogCancel, s as AlertDialogHeader, t as AlertDialog } from "./_ssr/InstanceActions-COGtl8tO.mjs";
import { t as Route } from "./_nodeId-C9GPYovG.mjs";
import { t as InstancesTable } from "./_ssr/InstancesTable-MRTh1GPM.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/_nodeId-lq1yorkc.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function NodeDetailPage() {
	const { nodeId } = Route.useParams();
	const node = useQuery(nodeQuery(nodeId));
	const nodes = useQuery(nodesQuery);
	const instances = useQuery(instancesQuery);
	const events = useQuery(eventsQuery);
	const reconcile = useReconcileNode();
	const [confirmOpen, setConfirmOpen] = (0, import_react.useState)(false);
	if (node.isPending) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 7 });
	if (node.isError) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: node.error.message,
		onRetry: () => void node.refetch()
	});
	const hostInstances = instances.data?.filter((instance) => instance.computeNodeId === node.data.id) ?? [];
	const targets = /* @__PURE__ */ new Set([node.data.name, ...hostInstances.map((instance) => instance.name)]);
	const hostEvents = events.data?.filter((event) => targets.has(event.target)) ?? [];
	const memoryPct = node.data.metrics.memory.totalMb ? node.data.metrics.memory.usedMb / node.data.metrics.memory.totalMb * 100 : 0;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "text-xs text-muted-foreground",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
					to: "/nodes",
					className: "hover:text-foreground",
					children: "Compute nodes"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "px-2",
					children: "/"
				}),
				node.data.name
			]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: node.data.name,
			description: `Agent v${node.data.agentVersion} · ${node.data.region} · last seen ${relativeTime(node.data.lastSeen)}`,
			actions: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(NodeStatusBadge, { status: node.data.status }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReadyBadge, { ready: node.data.ready }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					variant: "outline",
					size: "sm",
					disabled: reconcile.isPending || !node.data.ready,
					onClick: () => setConfirmOpen(true),
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RotateCw, { className: reconcile.isPending ? "h-4 w-4 animate-spin" : "h-4 w-4" }),
						" ",
						"Reconcile node"
					]
				})
			] })
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
			defaultValue: "overview",
			className: "space-y-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, {
					className: "max-w-full justify-start overflow-x-auto",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
							value: "overview",
							children: "Overview"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
							value: "instances",
							children: "Instances"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
							value: "metrics",
							children: "Metrics"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
							value: "invariants",
							children: "Invariants"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
							value: "events",
							children: "Events"
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
					value: "overview",
					className: "space-y-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-2 xl:grid-cols-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Agent uptime",
								value: formatUptime(node.data.uptimeSeconds),
								icon: Activity,
								caption: `Last heartbeat ${formatTimestamp(node.data.lastSeen)}`
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Active instances",
								value: `${node.data.capacity.activeInstances}/${node.data.capacity.maxActiveInstances}`,
								icon: Server,
								bar: {
									used: node.data.capacity.activeInstances,
									total: node.data.capacity.maxActiveInstances
								}
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Occupied slots",
								value: node.data.capacity.occupiedRuntimeSlots,
								icon: Cpu,
								caption: `${node.data.capacity.availableSlots} slots available`
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Open invariants",
								value: node.data.invariants.length,
								icon: ShieldCheck,
								caption: node.data.invariants.length ? "Review required" : "Node consistent"
							})
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-4 xl:grid-cols-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
							title: "Component health",
							description: "Readiness reported by the node agent.",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "divide-y divide-border",
								children: Object.entries(node.data.health).map(([name, state]) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-center justify-between py-3 first:pt-0 last:pb-0",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "text-sm capitalize",
										children: name
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(HealthBadge, { state })]
								}, name))
							})
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
							title: "Capacity",
							description: "Runtime scheduling limits and current allocation.",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "grid grid-cols-2 gap-4",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
										label: "Maximum active",
										value: node.data.capacity.maxActiveInstances
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
										label: "Active instances",
										value: node.data.capacity.activeInstances
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
										label: "Occupied slots",
										value: node.data.capacity.occupiedRuntimeSlots
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
										label: "Available slots",
										value: node.data.capacity.availableSlots
									})
								]
							})
						})]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
					value: "instances",
					children: instances.isPending || nodes.isPending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 4 }) : hostInstances.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstancesTable, {
						instances: hostInstances,
						nodes: nodes.data ?? []
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
						title: "No instances on this node",
						description: "This node has no scheduled workloads."
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
					value: "metrics",
					className: "space-y-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-4 xl:grid-cols-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
								title: "CPU",
								description: `${node.data.metrics.cpu.cores} logical cores`,
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
									label: "Usage",
									used: node.data.metrics.cpu.usagePercent,
									total: 100,
									hint: formatPercent(node.data.metrics.cpu.usagePercent)
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "mt-5 grid grid-cols-3 gap-3",
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
											label: "Load 1m",
											value: node.data.metrics.cpu.load1m
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
											label: "Load 5m",
											value: node.data.metrics.cpu.load5m
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
											label: "Load 15m",
											value: node.data.metrics.cpu.load15m
										})
									]
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
								title: "Memory",
								description: `${formatMb(node.data.metrics.memory.availableMb)} available`,
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
									label: "Used",
									used: node.data.metrics.memory.usedMb,
									total: node.data.metrics.memory.totalMb,
									hint: formatPercent(memoryPct)
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "mt-5 grid grid-cols-3 gap-3",
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
											label: "Used",
											value: formatMb(node.data.metrics.memory.usedMb)
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
											label: "Available",
											value: formatMb(node.data.metrics.memory.availableMb)
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Value, {
											label: "Total",
											value: formatMb(node.data.metrics.memory.totalMb)
										})
									]
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
								title: "Storage",
								description: "Host filesystem utilization",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
										label: "Root disk",
										used: node.data.metrics.rootDisk.usedGb,
										total: node.data.metrics.rootDisk.totalGb,
										hint: `${formatGb(node.data.metrics.rootDisk.usedGb)} / ${formatGb(node.data.metrics.rootDisk.totalGb)}`
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
										label: "MC-IaaS disk",
										used: node.data.metrics.mcIaasDisk.usedGb,
										total: node.data.metrics.mcIaasDisk.totalGb,
										hint: `${formatGb(node.data.metrics.mcIaasDisk.usedGb)} / ${formatGb(node.data.metrics.mcIaasDisk.totalGb)}`
									})]
								})
							})
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "CPU usage",
								value: formatPercent(node.data.metrics.cpu.usagePercent),
								icon: Cpu
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Memory used",
								value: formatMb(node.data.metrics.memory.usedMb),
								icon: MemoryStick
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "MC-IaaS storage",
								value: formatGb(node.data.metrics.mcIaasDisk.usedGb),
								icon: Database
							})
						]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
					value: "invariants",
					children: node.data.invariants.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
						title: "No invariant violations",
						description: "The agent reports that infrastructure state is internally consistent.",
						icon: ShieldCheck
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "panel overflow-x-auto",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Table, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, {
							className: "hover:bg-transparent",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Severity" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Code" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Detail" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
									className: "text-right",
									children: "Timestamp"
								})
							]
						}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableBody, { children: node.data.invariants.map((invariant) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, { children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SeverityBadge, { severity: invariant.severity }) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
								className: "tabular text-xs",
								children: invariant.code
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
								className: "max-w-xl text-xs text-muted-foreground",
								children: invariant.detail
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
								className: "tabular text-right text-xs whitespace-nowrap",
								children: formatTimestamp(invariant.timestamp)
							})
						] }, invariant.id)) })] })
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
					value: "events",
					children: events.isPending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 5 }) : hostEvents.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EventsTable, { events: hostEvents }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, { title: "No events for this node" })
				})
			]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialog, {
			open: confirmOpen,
			onOpenChange: setConfirmOpen,
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogTitle, { children: [
				"Reconcile ",
				node.data.name,
				"?"
			] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogDescription, { children: "This will simulate a recovery pass and append mock events. No compute node or agent will be contacted." })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogCancel, { children: "Cancel" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogAction, {
				onClick: () => reconcile.mutate({
					id: node.data.id,
					name: node.data.name
				}),
				children: "Run reconciliation"
			})] })] })
		})
	] });
}
function Panel({ title, description, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
		className: "panel p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mb-4",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
				className: "text-sm font-medium",
				children: title
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-0.5 text-xs text-muted-foreground",
				children: description
			})]
		}), children]
	});
}
function Value({ label, value }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "metric-label",
		children: label
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "tabular mt-1 text-sm font-medium",
		children: value
	})] });
}
//#endregion
export { NodeDetailPage as component };
