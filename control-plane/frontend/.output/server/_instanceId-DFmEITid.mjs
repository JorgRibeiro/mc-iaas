import { F as require_jsx_runtime } from "./_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "./_libs/tanstack__react-query.mjs";
import { a as eventsQuery, l as nodesQuery, o as instanceQuery } from "./_ssr/queries-D6pnQp7P.mjs";
import { h as Link } from "./_libs/@tanstack/react-router+[...].mjs";
import { t as Route } from "./_instanceId-Chz7j0aH.mjs";
import { E as Cpu, T as Database, a as SquareTerminal, g as Network, v as MemoryStick } from "./_libs/lucide-react.mjs";
import { a as TableSkeleton, i as PageHeader, n as EmptyState, r as ErrorState } from "./_ssr/StateViews-CO8w9HyP.mjs";
import { c as formatMb, l as formatPercent, s as formatGb, u as formatTimestamp } from "./_ssr/format-Bdjq67dT.mjs";
import { t as EventsTable } from "./_ssr/EventsTable-BIcR367i.mjs";
import { n as StatCard, t as MetricBar } from "./_ssr/StatCard-VB2AFQE5.mjs";
import { n as InstanceStateBadge, r as MinecraftStatusBadge } from "./_ssr/StatusBadge-K-Qktd-I.mjs";
import { i as TabsTrigger, n as TabsContent, r as TabsList, t as Tabs } from "./_ssr/tabs-DBCPkxut.mjs";
import { l as InstanceActions } from "./_ssr/InstanceActions-COGtl8tO.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/_instanceId-DFmEITid.js
var import_jsx_runtime = require_jsx_runtime();
function InstanceDetailPage() {
	const { instanceId } = Route.useParams();
	const instance = useQuery(instanceQuery(instanceId));
	const nodes = useQuery(nodesQuery);
	const events = useQuery(eventsQuery);
	if (instance.isPending) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 7 });
	if (instance.isError) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: instance.error.message,
		onRetry: () => void instance.refetch()
	});
	const node = nodes.data?.find((candidate) => candidate.id === instance.data.computeNodeId);
	const instanceEvents = events.data?.filter((event) => event.target === instance.data.name) ?? [];
	const metrics = instance.data.metrics;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "text-xs text-muted-foreground",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
					to: "/instances",
					className: "hover:text-foreground",
					children: "Instances"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "px-2",
					children: "/"
				}),
				instance.data.name
			]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: instance.data.name,
			description: `Minecraft ${instance.data.minecraftVersion} workload · ${node?.name ?? "Unassigned node"}`,
			actions: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstanceStateBadge, { state: instance.data.state }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MinecraftStatusBadge, { status: instance.data.minecraftStatus })] })
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "flex justify-end",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstanceActions, {
				instance: instance.data,
				variant: "buttons"
			})
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
			defaultValue: "overview",
			className: "space-y-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "overview",
						children: "Overview"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "metrics",
						children: "Metrics"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "console",
						children: "Console"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "events",
						children: "Events"
					})
				] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
					value: "overview",
					className: "grid gap-4 xl:grid-cols-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
							title: "VM configuration",
							description: "Provisioned compute profile.",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "VM username",
									value: instance.data.vmUsername
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Memory",
									value: formatMb(instance.data.memoryMb)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "vCPU",
									value: instance.data.vcpus
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Minecraft version",
									value: instance.data.minecraftVersion
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
							title: "Runtime allocation",
							description: "Ephemeral resources only present while active.",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Compute node",
									value: node?.name ?? "Unavailable"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Runtime slot",
									value: instance.data.runtime?.slot ?? "Not allocated"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Internal IP",
									value: instance.data.runtime?.ip ?? "Not allocated"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Public endpoint",
									value: instance.data.runtime ? `example.invalid:${instance.data.runtime.externalPort}` : "Not allocated",
									mono: true
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
							title: "Persistence",
							description: "Lifecycle and attached data volume.",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Persistent storage",
									value: instance.data.persistentStorage
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "System disk",
									value: formatGb(metrics.systemStorageGb.totalGb)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Data disk",
									value: formatGb(metrics.dataStorageGb.totalGb)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Definition, {
									label: "Created at",
									value: formatTimestamp(instance.data.createdAt),
									mono: true
								})
							]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
					value: "metrics",
					className: "space-y-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-2 xl:grid-cols-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "CPU usage",
								value: formatPercent(metrics.cpuUsagePercent),
								icon: Cpu,
								bar: {
									used: metrics.cpuUsagePercent,
									total: 100
								},
								caption: `${metrics.cpuTimeSeconds.toLocaleString()} seconds CPU time`
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Current memory",
								value: formatMb(metrics.memoryCurrentMb),
								icon: MemoryStick,
								bar: {
									used: metrics.memoryCurrentMb,
									total: metrics.memoryConfiguredMb
								},
								caption: `${formatMb(metrics.memoryConfiguredMb)} configured`
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Resident memory",
								value: formatMb(metrics.memoryRssMb),
								icon: MemoryStick,
								caption: "RSS reported by the hypervisor"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatCard, {
								label: "Network transfer",
								value: formatMb(metrics.networkRxMb + metrics.networkTxMb),
								icon: Network,
								caption: `${formatMb(metrics.networkRxMb)} RX · ${formatMb(metrics.networkTxMb)} TX`
							})
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-4 lg:grid-cols-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StoragePanel, {
							label: "System disk",
							used: metrics.systemStorageGb.usedGb,
							total: metrics.systemStorageGb.totalGb
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StoragePanel, {
							label: "Persistent data disk",
							used: metrics.dataStorageGb.usedGb,
							total: metrics.dataStorageGb.totalGb
						})]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
					value: "console",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "panel overflow-hidden",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SquareTerminal, { className: "h-4 w-4 text-muted-foreground" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-sm font-medium",
								children: "Console access"
							})]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
							defaultValue: "vm",
							className: "p-4",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
									value: "vm",
									children: "VM Console"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
									value: "minecraft",
									children: "Minecraft Console"
								})] }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
									value: "vm",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MockTerminal, {
										title: "VM serial console",
										instanceName: instance.data.name
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
									value: "minecraft",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MockTerminal, {
										title: "Minecraft RCON console",
										instanceName: instance.data.name
									})
								})
							]
						})]
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
					value: "events",
					children: events.isPending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 5 }) : instanceEvents.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EventsTable, { events: instanceEvents }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
						title: "No lifecycle events",
						description: "No activity has been recorded for this instance."
					})
				})
			]
		})
	] });
}
function Panel({ title, description, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
		className: "panel p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mb-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
				className: "text-sm font-medium",
				children: title
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-0.5 text-xs text-muted-foreground",
				children: description
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dl", {
			className: "divide-y divide-border",
			children
		})]
	});
}
function Definition({ label, value, mono }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
			className: "text-xs text-muted-foreground",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
			className: mono ? "tabular text-right text-xs" : "text-right text-sm font-medium capitalize",
			children: value
		})]
	});
}
function StoragePanel({ label, used, total }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
		className: "panel p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mb-4 flex items-center gap-2",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Database, { className: "h-4 w-4 text-muted-foreground" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
				className: "text-sm font-medium",
				children: label
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
			used,
			total,
			label: "Used capacity",
			hint: `${formatGb(used)} / ${formatGb(total)}`
		})]
	});
}
function MockTerminal({ title, instanceName }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "mt-4 min-h-64 rounded-md border border-border bg-background p-4 font-mono text-xs",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "text-muted-foreground",
				children: [
					"# ",
					title,
					" · ",
					instanceName
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-5 text-warning",
				children: "Mock console — backend integration pending"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-2 text-muted-foreground",
				children: "No connection has been opened. Interactive output will become available through the future Control Plane API."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-6 inline-block h-4 w-2 animate-pulse bg-primary/70",
				"aria-hidden": true
			})
		]
	});
}
//#endregion
export { InstanceDetailPage as component };
