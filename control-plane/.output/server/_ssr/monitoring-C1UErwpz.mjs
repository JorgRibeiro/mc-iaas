import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { f as timeseriesQuery, l as nodesQuery, s as instancesQuery, u as overviewQuery } from "./queries-D6pnQp7P.mjs";
import { h as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { C as Gauge, E as Cpu, T as Database, V as Boxes, l as Server, s as ShieldAlert, v as MemoryStick } from "../_libs/lucide-react.mjs";
import { i as PageHeader, n as EmptyState, r as ErrorState, t as CardsSkeleton } from "./StateViews-CO8w9HyP.mjs";
import { a as TableHeader, c as formatMb, f as percentOf, i as TableHead, l as formatPercent, n as TableBody, o as TableRow, r as TableCell, s as formatGb, t as Table, u as formatTimestamp } from "./format-Bdjq67dT.mjs";
import { n as StatCard, t as MetricBar } from "./StatCard-VB2AFQE5.mjs";
import { i as NodeStatusBadge, n as InstanceStateBadge, o as SeverityBadge } from "./StatusBadge-K-Qktd-I.mjs";
import { a as CartesianGrid, i as Area, n as YAxis, o as ResponsiveContainer, r as XAxis, s as Tooltip, t as AreaChart } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/monitoring-C1UErwpz.js
var import_jsx_runtime = require_jsx_runtime();
function UsageChart({ data, metric, title, subtitle }) {
	const color = metric === "cpu" ? "var(--color-chart-1)" : "var(--color-chart-2)";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "panel p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mb-3 space-y-0.5",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
				className: "text-sm font-medium",
				children: title
			}), subtitle && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-muted-foreground",
				children: subtitle
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "h-44 w-full",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
				width: "100%",
				height: "100%",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AreaChart, {
					data,
					margin: {
						top: 4,
						right: 4,
						bottom: 0,
						left: -18
					},
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("defs", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("linearGradient", {
							id: `grad-${metric}`,
							x1: "0",
							y1: "0",
							x2: "0",
							y2: "1",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("stop", {
								offset: "0%",
								stopColor: color,
								stopOpacity: .35
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("stop", {
								offset: "100%",
								stopColor: color,
								stopOpacity: .02
							})]
						}) }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
							stroke: "var(--color-border)",
							vertical: false
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
							dataKey: "t",
							tick: {
								fontSize: 11,
								fill: "var(--color-muted-foreground)"
							},
							stroke: "var(--color-border)"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(YAxis, {
							domain: [0, 100],
							tick: {
								fontSize: 11,
								fill: "var(--color-muted-foreground)"
							},
							stroke: "var(--color-border)",
							unit: "%"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tooltip, {
							contentStyle: {
								background: "var(--color-popover)",
								border: "1px solid var(--color-border)",
								borderRadius: 8,
								fontSize: 12
							},
							labelStyle: { color: "var(--color-muted-foreground)" },
							formatter: (value) => [`${value}%`, metric === "cpu" ? "CPU" : "Memory"]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Area, {
							type: "monotone",
							dataKey: metric,
							stroke: color,
							strokeWidth: 2,
							fill: `url(#grad-${metric})`
						})
					]
				})
			})
		})]
	});
}
function MonitoringPage() {
	const overview = useQuery(overviewQuery);
	const nodes = useQuery(nodesQuery);
	const instances = useQuery(instancesQuery);
	const timeseries = useQuery(timeseriesQuery);
	const error = overview.error ?? nodes.error ?? instances.error ?? timeseries.error;
	const summary = overview.data;
	const nodeList = nodes.data;
	const instanceList = instances.data;
	const timeseriesData = timeseries.data;
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: error.message,
		onRetry: () => void Promise.all([
			overview.refetch(),
			nodes.refetch(),
			instances.refetch(),
			timeseries.refetch()
		])
	});
	const invariants = (nodeList ?? []).flatMap((node) => node.invariants.map((invariant) => ({
		...invariant,
		nodeId: node.id,
		nodeName: node.name
	}))).sort((a, b) => b.timestamp.localeCompare(a.timestamp));
	const distribution = [
		"running",
		"stopped",
		"starting",
		"unavailable",
		"deleting"
	].map((state) => ({
		state,
		count: instanceList?.filter((instance) => instance.state === state).length ?? 0
	}));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: "Monitoring",
			description: "Aggregated health, utilization and invariant signals across the mock infrastructure."
		}),
		!summary ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardsSkeleton, { count: 4 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid gap-3 sm:grid-cols-2 xl:grid-cols-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Infrastructure health",
					value: summary.status === "operational" ? "Operational" : summary.status === "degraded" ? "Degraded" : "Down",
					icon: Gauge,
					caption: `${summary.nodesOnline}/${summary.nodesTotal} nodes online`
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Aggregate capacity",
					value: `${summary.slotsUsed}/${summary.slotsTotal}`,
					icon: Server,
					bar: {
						used: summary.slotsUsed,
						total: summary.slotsTotal
					},
					caption: "Runtime slots occupied"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Memory pressure",
					value: formatPercent(percentOf(summary.memoryUsedMb, summary.memoryTotalMb)),
					icon: MemoryStick,
					bar: {
						used: summary.memoryUsedMb,
						total: summary.memoryTotalMb
					},
					caption: `${formatMb(summary.memoryUsedMb)} used`
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
					label: "Storage pressure",
					value: formatPercent(percentOf(summary.storageUsedGb, summary.storageTotalGb)),
					icon: Database,
					bar: {
						used: summary.storageUsedGb,
						total: summary.storageTotalGb
					},
					caption: `${formatGb(summary.storageUsedGb)} used`
				})
			]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "grid gap-4 xl:grid-cols-2",
			children: !timeseriesData ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardsSkeleton, { count: 2 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(UsageChart, {
				data: timeseriesData,
				metric: "cpu",
				title: "Aggregate CPU",
				subtitle: "Recent utilization across reachable nodes"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(UsageChart, {
				data: timeseriesData,
				metric: "memory",
				title: "Aggregate memory",
				subtitle: "Recent working-set utilization"
			})] })
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid gap-4 xl:grid-cols-2",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "panel p-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mb-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "text-sm font-medium",
						children: "Node health"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-0.5 text-xs text-muted-foreground",
						children: "Current reachability and key resource pressure."
					})]
				}), !nodeList ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardsSkeleton, { count: 2 }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "space-y-4",
					children: nodeList.map((node) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-md border border-border p-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "mb-3 flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
								to: "/nodes/$nodeId",
								params: { nodeId: node.id },
								className: "text-sm font-medium hover:text-primary",
								children: node.name
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NodeStatusBadge, { status: node.status })]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid gap-3 sm:grid-cols-3",
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
									hint: formatPercent(percentOf(node.metrics.memory.usedMb, node.metrics.memory.totalMb))
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
									label: "Storage",
									used: node.metrics.mcIaasDisk.usedGb,
									total: node.metrics.mcIaasDisk.totalGb,
									hint: formatPercent(percentOf(node.metrics.mcIaasDisk.usedGb, node.metrics.mcIaasDisk.totalGb))
								})
							]
						})]
					}, node.id))
				})]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "panel p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "mb-4",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "text-sm font-medium",
							children: "Instance state distribution"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-0.5 text-xs text-muted-foreground",
							children: "Workload inventory grouped by lifecycle state."
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "space-y-3",
						children: distribution.map(({ state, count }) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center gap-4 rounded-md border border-border px-3 py-2.5",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstanceStateBadge, { state }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "h-1.5 flex-1 overflow-hidden rounded-full bg-muted",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "h-full rounded-full bg-primary",
										style: { width: `${instanceList?.length ? count / instanceList.length * 100 : 0}%` }
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "tabular w-6 text-right text-sm font-semibold",
									children: count
								})
							]
						}, state))
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "mt-4 grid grid-cols-3 gap-3 border-t border-border pt-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SmallStat, {
								icon: Boxes,
								label: "Total",
								value: instanceList?.length ?? 0
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SmallStat, {
								icon: Cpu,
								label: "Running",
								value: distribution.find((item) => item.state === "running")?.count ?? 0
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SmallStat, {
								icon: ShieldAlert,
								label: "Unavailable",
								value: distribution.find((item) => item.state === "unavailable")?.count ?? 0
							})
						]
					})
				]
			})]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "space-y-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
				className: "text-sm font-semibold",
				children: "Recent invariants"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-0.5 text-xs text-muted-foreground",
				children: "Consistency violations reported by compute agents."
			})] }), invariants.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
				title: "No invariant violations",
				description: "All reachable nodes report internally consistent state."
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "panel overflow-x-auto",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Table, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, {
					className: "hover:bg-transparent",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Severity" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Node" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Code" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Detail" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
							className: "text-right",
							children: "Timestamp"
						})
					]
				}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableBody, { children: invariants.map((invariant) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SeverityBadge, { severity: invariant.severity }) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
						to: "/nodes/$nodeId",
						params: { nodeId: invariant.nodeId },
						className: "text-sm font-medium hover:text-primary",
						children: invariant.nodeName
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
						className: "tabular text-xs",
						children: invariant.code
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
						className: "max-w-2xl text-xs text-muted-foreground",
						children: invariant.detail
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
						className: "tabular text-right text-xs whitespace-nowrap",
						children: formatTimestamp(invariant.timestamp)
					})
				] }, invariant.id)) })] })
			})]
		})
	] });
}
function SmallStat({ icon: Icon, label, value }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Icon, { className: "mb-2 h-4 w-4 text-muted-foreground" }),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "metric-label",
			children: label
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "tabular mt-1 text-lg font-semibold",
			children: value
		})
	] });
}
//#endregion
export { MonitoringPage as component };
