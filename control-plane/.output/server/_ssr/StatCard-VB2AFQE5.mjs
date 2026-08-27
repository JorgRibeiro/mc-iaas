import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { i as cn } from "./queries-D6pnQp7P.mjs";
import { x as Info } from "../_libs/lucide-react.mjs";
import { f as percentOf } from "./format-Bdjq67dT.mjs";
import { i as TooltipTrigger, n as TooltipContent, t as Tooltip } from "./tooltip-CtC4e8zj.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/StatCard-VB2AFQE5.js
var import_jsx_runtime = require_jsx_runtime();
function MetricBar({ used, total, label, hint, className }) {
	const pct = percentOf(used, total);
	const tone = pct >= 90 ? "bg-destructive" : pct >= 70 ? "bg-warning" : "bg-primary";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: cn("space-y-1.5", className),
		children: [(label || hint) && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex items-baseline justify-between gap-3",
			children: [label && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "metric-label",
				children: label
			}), hint && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "tabular text-xs text-muted-foreground",
				children: hint
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "h-1.5 w-full overflow-hidden rounded-full bg-muted",
			role: "meter",
			"aria-valuenow": Math.round(pct),
			"aria-valuemin": 0,
			"aria-valuemax": 100,
			"aria-label": label ?? "usage",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: cn("h-full rounded-full transition-all", tone),
				style: { width: `${pct}%` }
			})
		})]
	});
}
function StatCard({ label, value, unit, caption, icon: Icon, tooltip, bar, children, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: cn("panel flex flex-col gap-3 p-4", className),
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between gap-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "metric-label",
						children: label
					}), tooltip && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tooltip, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TooltipTrigger, {
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							"aria-label": `About ${label}`,
							className: "text-muted-foreground/70 transition-colors hover:text-foreground",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Info, { className: "h-3.5 w-3.5" })
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TooltipContent, {
						className: "max-w-64",
						children: tooltip
					})] })]
				}), Icon && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Icon, {
					className: "h-4 w-4 text-muted-foreground/70",
					"aria-hidden": true
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-baseline gap-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "tabular text-2xl leading-none font-semibold",
					children: value
				}), unit && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "text-xs text-muted-foreground",
					children: unit
				})]
			}),
			bar && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MetricBar, {
				used: bar.used,
				total: bar.total
			}),
			caption && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-muted-foreground",
				children: caption
			}),
			children
		]
	});
}
//#endregion
export { StatCard as n, MetricBar as t };
