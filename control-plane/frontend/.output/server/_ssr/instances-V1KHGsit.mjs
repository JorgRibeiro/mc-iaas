import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { l as nodesQuery, s as instancesQuery, t as Button } from "./queries-D6pnQp7P.mjs";
import { p as Plus } from "../_libs/lucide-react.mjs";
import { a as TableSkeleton, i as PageHeader, n as EmptyState, r as ErrorState } from "./StateViews-CO8w9HyP.mjs";
import { t as InstancesTable } from "./InstancesTable-MRTh1GPM.mjs";
import { t as CreateInstanceDialog } from "./CreateInstanceDialog-CaMh_tQ2.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/instances-V1KHGsit.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function InstancesPage() {
	const instances = useQuery(instancesQuery);
	const nodes = useQuery(nodesQuery);
	const [createOpen, setCreateOpen] = (0, import_react.useState)(false);
	const error = instances.error ?? nodes.error;
	const instanceList = instances.data;
	const nodeList = nodes.data;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: "Instances",
			description: "Minecraft workloads managed as virtual-machine instances across the compute fleet.",
			actions: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
				size: "sm",
				onClick: () => setCreateOpen(true),
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "h-4 w-4" }), " Create instance"]
			})
		}),
		error ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
			message: error.message,
			onRetry: () => void Promise.all([instances.refetch(), nodes.refetch()])
		}) : !instanceList || !nodeList ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 5 }) : instanceList.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
			title: "No instances provisioned",
			description: "Create a workload to populate the control plane inventory.",
			action: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				size: "sm",
				className: "mt-2",
				onClick: () => setCreateOpen(true),
				children: "Create instance"
			})
		}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InstancesTable, {
			instances: instanceList,
			nodes: nodeList
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CreateInstanceDialog, {
			open: createOpen,
			onOpenChange: setCreateOpen
		})
	] });
}
//#endregion
export { InstancesPage as component };
