import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { t as cva } from "../_libs/class-variance-authority+clsx.mjs";
import { d as settingsQuery, g as useUpdateSettings, i as cn, t as Button } from "./queries-D6pnQp7P.mjs";
import { B as Cable, u as Save } from "../_libs/lucide-react.mjs";
import { a as TableSkeleton, i as PageHeader, r as ErrorState } from "./StateViews-CO8w9HyP.mjs";
import { a as SelectItem, i as SelectContent, n as Label, o as SelectTrigger, r as Select, s as SelectValue, t as Input } from "./select-DzQ3G0Ie.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/settings-CHl6T9lc.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var badgeVariants = cva("inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", {
	variants: { variant: {
		default: "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
		secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
		destructive: "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
		outline: "text-foreground"
	} },
	defaultVariants: { variant: "default" }
});
function Badge({ className, variant, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn(badgeVariants({ variant }), className),
		...props
	});
}
function SettingsPage() {
	const settings = useQuery(settingsQuery);
	const update = useUpdateSettings();
	const [form, setForm] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		if (settings.data) setForm(settings.data);
	}, [settings.data]);
	if (settings.isError) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorState, {
		message: settings.error.message,
		onRetry: () => void settings.refetch()
	});
	if (settings.isPending || !form) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TableSkeleton, { rows: 6 });
	function set(key, value) {
		setForm((current) => current ? {
			...current,
			[key]: value
		} : current);
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
		title: "Settings",
		description: "Local defaults for this development console. Changes remain in memory for the current process only.",
		actions: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
			size: "sm",
			disabled: update.isPending,
			onClick: () => update.mutate(form),
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Save, { className: "h-4 w-4" }), update.isPending ? "Saving…" : "Save settings"]
		})
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(20rem,1fr)]",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "panel p-5",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mb-5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "text-sm font-medium",
					children: "Control Plane defaults"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-1 text-xs text-muted-foreground",
					children: "Values used to preconfigure future scheduling and creation flows."
				})]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-5 sm:grid-cols-2",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Control Plane name",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							value: form.controlPlaneName,
							onChange: (event) => set("controlPlaneName", event.target.value)
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Environment",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: form.environment,
							onValueChange: (value) => set("environment", value),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "development",
									children: "Development"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "staging",
									children: "Staging"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "production",
									children: "Production"
								})
							] })]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(NumberField, {
						label: "Refresh interval (seconds)",
						value: form.refreshIntervalSeconds,
						min: 5,
						step: 5,
						onChange: (value) => set("refreshIntervalSeconds", value)
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(NumberField, {
						label: "Default memory (MiB)",
						value: form.defaultMemoryMb,
						min: 512,
						max: 2048,
						step: 512,
						onChange: (value) => set("defaultMemoryMb", value)
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(NumberField, {
						label: "Default vCPU",
						value: form.defaultVcpus,
						min: 1,
						max: 1,
						onChange: (value) => set("defaultVcpus", value)
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(NumberField, {
						label: "Max instances per node",
						value: form.maxInstancesPerNode,
						min: 1,
						max: 4,
						onChange: (value) => set("maxInstancesPerNode", value)
					})
				]
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "panel self-start p-5",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-start gap-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "rounded-md border border-border bg-muted p-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Cable, { className: "h-4 w-4 text-muted-foreground" })
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex flex-wrap items-center gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "text-sm font-medium",
						children: "API Integration"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						variant: "outline",
						className: "text-muted-foreground",
						children: "Not configured"
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "The Control Plane backend has not been connected yet."
				})] })]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mt-5 rounded-md border border-dashed border-border p-3 text-xs leading-relaxed text-muted-foreground",
				children: [
					"The UI currently uses",
					" ",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "font-mono text-foreground",
						children: "MockControlPlaneClient"
					}),
					". A future HTTP adapter can replace it at the existing service injection point."
				]
			})]
		})]
	})] });
}
function Field({ label, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-1.5",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: label }), children]
	});
}
function NumberField({ label, value, min, max, step, onChange }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
		label,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
			type: "number",
			value,
			min,
			...max === void 0 ? {} : { max },
			...step === void 0 ? {} : { step },
			onChange: (event) => onChange(Number(event.target.value))
		})
	});
}
//#endregion
export { SettingsPage as component };
