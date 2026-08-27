import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { h as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { a as TableHeader, c as formatMb, i as TableHead, n as TableBody, o as TableRow, r as TableCell, t as Table } from "./format-Bdjq67dT.mjs";
import { n as InstanceStateBadge, r as MinecraftStatusBadge } from "./StatusBadge-K-Qktd-I.mjs";
import { l as InstanceActions } from "./InstanceActions-COGtl8tO.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/InstancesTable-MRTh1GPM.js
var import_jsx_runtime = require_jsx_runtime();
function InstancesTable({ instances, nodes }) {
	const nodeName = (id) => nodes.find((n) => n.id === id)?.name ?? "unassigned";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "panel overflow-x-auto",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Table, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, {
			className: "hover:bg-transparent",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Name" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "State" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Compute node" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Version" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "Memory"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "vCPU"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Runtime IP" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "text-right",
					children: "Public port"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Minecraft" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "w-12 text-right",
					children: "Actions"
				})
			]
		}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableBody, { children: instances.map((instance) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, { children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableCell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
				to: "/instances/$instanceId",
				params: { instanceId: instance.id },
				className: "font-medium hover:text-primary",
				children: instance.name
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
				className: "block text-xs text-muted-foreground",
				children: ["user ", instance.vmUsername]
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstanceStateBadge, { state: instance.state }) }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "text-sm",
				children: nodeName(instance.computeNodeId)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableCell, {
				className: "tabular text-xs",
				children: ["MC ", instance.minecraftVersion]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-right text-xs",
				children: formatMb(instance.memoryMb)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-right text-xs",
				children: instance.vcpus
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-xs",
				children: instance.runtime?.ip ?? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "text-muted-foreground",
					children: "—"
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-right text-xs",
				children: instance.runtime?.externalPort ?? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "text-muted-foreground",
					children: "—"
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MinecraftStatusBadge, { status: instance.minecraftStatus }) }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "text-right",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstanceActions, { instance })
			})
		] }, instance.id)) })] })
	});
}
//#endregion
export { InstancesTable as t };
