import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { l as nodesQuery } from "./queries-D6pnQp7P.mjs";
import { h as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { a as TableSkeleton, i as PageHeader, n as EmptyState, r as ErrorState } from "./StateViews-CO8w9HyP.mjs";
import { a as TableHeader, c as formatMb, d as formatUptime, i as TableHead, l as formatPercent, n as TableBody, o as TableRow, p as relativeTime, r as TableCell, s as formatGb, t as Table } from "./format-Bdjq67dT.mjs";
import { a as ReadyBadge, i as NodeStatusBadge } from "./StatusBadge-K-Qktd-I.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/nodes-C7wWUg47.js
var import_jsx_runtime = require_jsx_runtime();
function NodesTable({ nodes }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "panel overflow-x-auto",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Table, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, {
			className: "hover:bg-transparent",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Name" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Status" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Ready" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "Active"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "Runtime slots"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "CPU"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Memory" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Disk" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "Agent uptime"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "Last seen"
				})
			]
		}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableBody, { children: nodes.map((node) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, { children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableCell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
				to: "/nodes/$nodeId",
				params: { nodeId: node.id },
				className: "font-medium hover:text-primary",
				children: node.name
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
				className: "block text-xs text-muted-foreground",
				children: [
					"agent v",
					node.agentVersion,
					" · ",
					node.region
				]
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NodeStatusBadge, { status: node.status }) }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReadyBadge, { ready: node.ready }) }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-right",
				children: node.capacity.activeInstances
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableCell, {
				className: "tabular text-right",
				children: [
					node.capacity.occupiedRuntimeSlots,
					"/",
					node.capacity.maxActiveInstances
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-right",
				children: formatPercent(node.metrics.cpu.usagePercent)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableCell, {
				className: "tabular text-xs",
				children: [
					formatMb(node.metrics.memory.usedMb),
					" /",
					" ",
					formatMb(node.metrics.memory.totalMb)
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableCell, {
				className: "tabular text-xs",
				children: [
					formatGb(node.metrics.mcIaasDisk.usedGb),
					" /",
					" ",
					formatGb(node.metrics.mcIaasDisk.totalGb)
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-right",
				children: formatUptime(node.uptimeSeconds)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "text-right text-xs text-muted-foreground",
				children: relativeTime(node.lastSeen)
			})
		] }, node.id)) })] })
	});
}
function NodesPage() {
	const nodes = useQuery(nodesQuery);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
		title: "Compute nodes",
		description: "Registered hosts, agent reachability and available workload capacity. RAYLANDSON-COMPUTE is an offline visual mock."
	}), nodes.isPending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 4 }) : nodes.isError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: nodes.error.message,
		onRetry: () => void nodes.refetch()
	}) : nodes.data.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "No compute nodes registered",
		description: "Nodes will appear after the Control Plane API is connected."
	}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NodesTable, { nodes: nodes.data })] });
}
//#endregion
export { NodesPage as component };
