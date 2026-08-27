import { F as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { i as cn } from "./queries-D6pnQp7P.mjs";
import { A as CircleSlash, M as CircleDashed, N as CircleCheck, h as Pause, j as CircleQuestionMark, k as CircleX, m as Play, n as TriangleAlert, r as Trash2, y as LoaderCircle } from "../_libs/lucide-react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/StatusBadge-K-Qktd-I.js
var import_jsx_runtime = require_jsx_runtime();
var toneClass = {
	ok: "border-success/35 bg-success/10 text-success",
	warn: "border-warning/35 bg-warning/10 text-warning",
	bad: "border-destructive/35 bg-destructive/10 text-destructive",
	info: "border-primary/35 bg-primary/10 text-primary",
	neutral: "border-border-strong bg-muted/60 text-muted-foreground"
};
function Pill({ tone, icon: Icon, label, className, spin }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
		className: cn("inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium whitespace-nowrap", toneClass[tone], className),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Icon, {
			className: cn("h-3.5 w-3.5", spin && "animate-spin"),
			"aria-hidden": true
		}), label]
	});
}
var nodeMap = {
	healthy: {
		tone: "ok",
		icon: CircleCheck,
		label: "Healthy"
	},
	degraded: {
		tone: "warn",
		icon: TriangleAlert,
		label: "Degraded"
	},
	unhealthy: {
		tone: "bad",
		icon: CircleX,
		label: "Unhealthy"
	},
	offline: {
		tone: "neutral",
		icon: CircleSlash,
		label: "Offline"
	}
};
function NodeStatusBadge({ status, className }) {
	const conf = nodeMap[status];
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		...conf,
		className
	});
}
var instanceMap = {
	running: {
		tone: "ok",
		icon: Play,
		label: "Running"
	},
	stopped: {
		tone: "neutral",
		icon: Pause,
		label: "Stopped"
	},
	starting: {
		tone: "info",
		icon: LoaderCircle,
		label: "Starting",
		spin: true
	},
	unavailable: {
		tone: "bad",
		icon: CircleSlash,
		label: "Unavailable"
	},
	deleting: {
		tone: "warn",
		icon: Trash2,
		label: "Deleting"
	}
};
function InstanceStateBadge({ state, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		...instanceMap[state],
		className
	});
}
var mcMap = {
	online: {
		tone: "ok",
		icon: CircleCheck,
		label: "Online"
	},
	offline: {
		tone: "neutral",
		icon: CircleDashed,
		label: "Offline"
	},
	starting: {
		tone: "info",
		icon: LoaderCircle,
		label: "Starting",
		spin: true
	},
	unknown: {
		tone: "neutral",
		icon: CircleQuestionMark,
		label: "Unknown"
	}
};
function MinecraftStatusBadge({ status, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		...mcMap[status],
		className
	});
}
var healthMap = {
	ok: {
		tone: "ok",
		icon: CircleCheck,
		label: "OK"
	},
	warning: {
		tone: "warn",
		icon: TriangleAlert,
		label: "Warning"
	},
	error: {
		tone: "bad",
		icon: CircleX,
		label: "Error"
	},
	unknown: {
		tone: "neutral",
		icon: CircleQuestionMark,
		label: "Unknown"
	}
};
function HealthBadge({ state, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		...healthMap[state],
		className
	});
}
function ReadyBadge({ ready, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		tone: ready ? "ok" : "neutral",
		icon: ready ? CircleCheck : CircleSlash,
		label: ready ? "Ready: true" : "Ready: false",
		className
	});
}
function SeverityBadge({ severity }) {
	return severity === "critical" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		tone: "bad",
		icon: CircleX,
		label: "Critical"
	}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pill, {
		tone: "warn",
		icon: TriangleAlert,
		label: "Warning"
	});
}
//#endregion
export { ReadyBadge as a, NodeStatusBadge as i, InstanceStateBadge as n, SeverityBadge as o, MinecraftStatusBadge as r, HealthBadge as t };
