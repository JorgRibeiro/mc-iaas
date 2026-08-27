import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { a as eventsQuery, t as Button } from "./queries-D6pnQp7P.mjs";
import { a as TableSkeleton, i as PageHeader, n as EmptyState, r as ErrorState } from "./StateViews-CO8w9HyP.mjs";
import { t as EventsTable } from "./EventsTable-BIcR367i.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/activity-DaxA7Lph.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function ActivityPage() {
	const events = useQuery(eventsQuery);
	const [filter, setFilter] = (0, import_react.useState)("all");
	const filtered = events.data?.filter((event) => filter === "all" || event.level === filter) ?? [];
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
		title: "Activity",
		description: "Chronological lifecycle, runtime, recovery and security events emitted by the mock Control Plane.",
		actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "flex rounded-md border border-border bg-muted/40 p-1",
			children: [
				"all",
				"info",
				"warning",
				"error"
			].map((level) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				variant: filter === level ? "secondary" : "ghost",
				size: "sm",
				className: "h-7 capitalize",
				onClick: () => setFilter(level),
				children: level
			}, level))
		})
	}), events.isPending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 8 }) : events.isError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: events.error.message,
		onRetry: () => void events.refetch()
	}) : filtered.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EventsTable, { events: filtered }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: `No ${filter} events`,
		description: "Try a different severity filter."
	})] });
}
//#endregion
export { ActivityPage as component };
