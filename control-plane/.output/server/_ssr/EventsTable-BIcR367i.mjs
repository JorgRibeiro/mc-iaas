import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { i as cn } from "./queries-D6pnQp7P.mjs";
import { k as CircleX, n as TriangleAlert, x as Info } from "../_libs/lucide-react.mjs";
import { a as TableHeader, i as TableHead, n as TableBody, o as TableRow, p as relativeTime, r as TableCell, t as Table, u as formatTimestamp } from "./format-Bdjq67dT.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/EventsTable-BIcR367i.js
var import_jsx_runtime = require_jsx_runtime();
function LevelTag({ level }) {
	const conf = {
		info: {
			icon: Info,
			cls: "border-border-strong bg-muted/60 text-muted-foreground",
			label: "Info"
		},
		warning: {
			icon: TriangleAlert,
			cls: "border-warning/35 bg-warning/10 text-warning",
			label: "Warning"
		},
		error: {
			icon: CircleX,
			cls: "border-destructive/35 bg-destructive/10 text-destructive",
			label: "Error"
		}
	}[level];
	const Icon = conf.icon;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
		className: cn("inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium", conf.cls),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Icon, {
			className: "h-3.5 w-3.5",
			"aria-hidden": true
		}), conf.label]
	});
}
function EventsTable({ events, compact }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "panel overflow-x-auto",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Table, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, {
			className: "hover:bg-transparent",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "w-48",
					children: "Timestamp"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "w-28",
					children: "Level"
				}),
				!compact && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "w-28",
					children: "Component"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Event" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, {
					className: "w-44",
					children: "Target"
				}),
				!compact && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableHead, { children: "Message" })
			]
		}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableBody, { children: events.map((event) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TableRow, { children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-xs whitespace-nowrap text-muted-foreground",
				children: compact ? relativeTime(event.timestamp) : formatTimestamp(event.timestamp)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LevelTag, { level: event.level }) }),
			!compact && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "text-xs text-muted-foreground",
				children: event.component
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "tabular text-xs",
				children: event.event
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "text-xs",
				children: event.target
			}),
			!compact && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableCell, {
				className: "max-w-md text-xs text-muted-foreground",
				children: event.message
			})
		] }, event.id)) })] })
	});
}
//#endregion
export { EventsTable as t };
