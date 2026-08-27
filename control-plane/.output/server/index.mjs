globalThis.__nitro_main__ = import.meta.url;
import { i as HTTPError, n as defineLazyEventHandler, t as H3Core } from "./_libs/h3+rou3+srvx.mjs";
import { t as HookableCore } from "./_libs/hookable.mjs";
import { r as FastResponse } from "./_libs/h3-v2+rou3+srvx.mjs";
//#region #nitro-vite-setup
function lazyService(loader) {
	let promise, mod;
	return { fetch(req) {
		if (mod) return mod.fetch(req);
		if (!promise) promise = loader().then((_mod) => mod = _mod.default || _mod);
		return promise.then((mod) => mod.fetch(req));
	} };
}
var services = { ["ssr"]: lazyService(() => import("./_ssr/ssr.mjs")) };
globalThis.__nitro_vite_envs__ = services;
//#endregion
//#region #nitro/virtual/public-assets-data
var public_assets_data_default = {
	"/robots.txt": {
		"type": "text/plain; charset=utf-8",
		"etag": "\"a0-CKGXSIe7TSsqDTmGm/nY1t/o5d0\"",
		"mtime": "2026-08-27T21:43:11.947Z",
		"size": 160,
		"path": "../public/robots.txt"
	},
	"/assets/CreateInstanceDialog-Ipu1AIpS.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"3c39-jaqzbbJSOqmquaO/0O/H8UHsTzk\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 15417,
		"path": "../public/assets/CreateInstanceDialog-Ipu1AIpS.js"
	},
	"/assets/EventsTable-C7Rtn-Nc.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"6d3-cRDBXwQ9fhNOsWHTXQLbGPhvUO4\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 1747,
		"path": "../public/assets/EventsTable-C7Rtn-Nc.js"
	},
	"/assets/InstanceActions-CEScnApU.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"788d-d0raPSRnA9NsE/N6LcjAKzFth4Q\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 30861,
		"path": "../public/assets/InstanceActions-CEScnApU.js"
	},
	"/assets/InstancesTable-DloHz-da.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"826-WuzZINGHrxWLterImUdGModv100\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 2086,
		"path": "../public/assets/InstancesTable-DloHz-da.js"
	},
	"/assets/StatCard-D7kY1qyg.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"ce3-HLdKRVJkVwtZA4I6WfiE7KOq1VY\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 3299,
		"path": "../public/assets/StatCard-D7kY1qyg.js"
	},
	"/assets/StateViews-BhOTRsRb.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"b41-W96ZPx0pPZLZboy6YKkpyYbT5Tk\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 2881,
		"path": "../public/assets/StateViews-BhOTRsRb.js"
	},
	"/assets/StatusBadge-Cc595qDU.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"e85-uTBqKNpq0/jcnGveuDUnlTrtxq0\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 3717,
		"path": "../public/assets/StatusBadge-Cc595qDU.js"
	},
	"/assets/_instanceId-BJ_S6Y6f.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"2f7-VB2HtDm5+tuBg83yHOorIQv1TFw\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 759,
		"path": "../public/assets/_instanceId-BJ_S6Y6f.js"
	},
	"/assets/_instanceId-DFb5o0dW.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"1c6c-f+58KQZsHOAQAmLYt0Tgk9bg8Q4\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 7276,
		"path": "../public/assets/_instanceId-DFb5o0dW.js"
	},
	"/assets/_nodeId-A2-tRdqw.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"2285-0mnEuTGWH0Csd2t6Uq0A550c46Q\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 8837,
		"path": "../public/assets/_nodeId-A2-tRdqw.js"
	},
	"/assets/_nodeId-D7NLPIwB.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"34e-I7WiTJBIIs5o+fZi8FcesBPYwtk\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 846,
		"path": "../public/assets/_nodeId-D7NLPIwB.js"
	},
	"/assets/activity-Bvo-0ewD.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"e1-hUTag4djksgK/TSwFqlrEMvIy9w\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 225,
		"path": "../public/assets/activity-Bvo-0ewD.js"
	},
	"/assets/activity-pU4EMRS2.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"3ed-VTOhIl45Sm9r5CHszfAYm7QI8CY\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 1005,
		"path": "../public/assets/activity-pU4EMRS2.js"
	},
	"/assets/dist-B--ub5sL.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"5e56-xjklnIJjQnbceVw6H9PJusvDpp0\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 24150,
		"path": "../public/assets/dist-B--ub5sL.js"
	},
	"/assets/dist-BzJcDI-8.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"9be2-Af0l4mJvoL8v7mxVe7UqKu9UF/M\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 39906,
		"path": "../public/assets/dist-BzJcDI-8.js"
	},
	"/assets/dist-CHCPzABd.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"132e-IgWijBfZC8OXI6Wkixx2MHbKARo\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 4910,
		"path": "../public/assets/dist-CHCPzABd.js"
	},
	"/assets/format-1KNE3ham.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"ac1-/Jxh9dkf9XMOdCwBRUcpcAsnJk0\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 2753,
		"path": "../public/assets/format-1KNE3ham.js"
	},
	"/assets/gauge-Dt5Kf4TI.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"a7-T54vhS4Jpm1iCFeIva8Vr8jtVbc\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 167,
		"path": "../public/assets/gauge-Dt5Kf4TI.js"
	},
	"/assets/info-BWqdnMLR.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"c3-5iHcYdtNPc/0MXB+nIt2DlLtHfM\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 195,
		"path": "../public/assets/info-BWqdnMLR.js"
	},
	"/assets/instances-B6BLTlO_.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"451-nailR0StJ+II7fy6z15w645fj3o\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 1105,
		"path": "../public/assets/instances-B6BLTlO_.js"
	},
	"/assets/link-BF4FuP3W.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"5b20-rO8Md+VziJCEeywuvIXunDvgvQI\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 23328,
		"path": "../public/assets/link-BF4FuP3W.js"
	},
	"/assets/index-BX_RBkQw.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"49124-Xz4Q+jh107F1SBBSqPeWaBibYDc\"",
		"mtime": "2026-08-27T21:43:11.694Z",
		"size": 299300,
		"path": "../public/assets/index-BX_RBkQw.js"
	},
	"/assets/monitoring-BMkKcexD.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"5e371-rqUeZWl3yhMnUIaLTdGzEhKLMzo\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 385905,
		"path": "../public/assets/monitoring-BMkKcexD.js"
	},
	"/favicon.ico": {
		"type": "image/vnd.microsoft.icon",
		"etag": "\"4f95-3RXc3p2mhEAs1WBwaIvE0Y0uu0Y\"",
		"mtime": "2026-08-27T21:43:11.947Z",
		"size": 20373,
		"path": "../public/favicon.ico"
	},
	"/assets/nodes-C_Tl1GfC.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"a6b-Hcrvf2ZJyrI2CDnsJHGiw7KtDfg\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 2667,
		"path": "../public/assets/nodes-C_Tl1GfC.js"
	},
	"/assets/preload-helper-CjuJUFCT.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"181c-8j6vzUWPRfbxVpm4UB8aY8IR/Po\"",
		"mtime": "2026-08-27T21:43:11.695Z",
		"size": 6172,
		"path": "../public/assets/preload-helper-CjuJUFCT.js"
	},
	"/assets/queries-BbAJyXCg.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"1d2a2-WECFMeCoQry4T23c2J101KNf6bU\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 119458,
		"path": "../public/assets/queries-BbAJyXCg.js"
	},
	"/assets/routes-BjpOyYjH.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"191d-4X6bsfrdou2tCvPVPSiFKkoQluI\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 6429,
		"path": "../public/assets/routes-BjpOyYjH.js"
	},
	"/assets/server-ClgkJEZs.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"149-52BJQcTDHYOqJo3AgiTLKAf/XOE\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 329,
		"path": "../public/assets/server-ClgkJEZs.js"
	},
	"/assets/select-CsbNUin_.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"5aa4-soQc4n6jrWc9iApGddTOWskwcyQ\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 23204,
		"path": "../public/assets/select-CsbNUin_.js"
	},
	"/assets/settings-CbZSMv0W.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"1408-2SYNuUROR7zuk11JzCWQEajlrjE\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 5128,
		"path": "../public/assets/settings-CbZSMv0W.js"
	},
	"/assets/shield-alert-CmU4cynX.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"476-aQgQORM3t592ale5IIK3HLwNbxQ\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 1142,
		"path": "../public/assets/shield-alert-CmU4cynX.js"
	},
	"/assets/styles-CcH1nooa.css": {
		"type": "text/css; charset=utf-8",
		"etag": "\"14207-LQ1vEhkszdi7DDqw8Vou2JDngkY\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 82439,
		"path": "../public/assets/styles-CcH1nooa.css"
	},
	"/assets/tabs-CzX6Uqsl.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"dc1-qjetEfqbUcnw3TU+RYemIxUdJHQ\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 3521,
		"path": "../public/assets/tabs-CzX6Uqsl.js"
	},
	"/assets/tooltip-J-Oy-VdC.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"212d-6tW67OZABKLS4f2kGE/Ordo18eQ\"",
		"mtime": "2026-08-27T21:43:11.696Z",
		"size": 8493,
		"path": "../public/assets/tooltip-J-Oy-VdC.js"
	}
};
//#endregion
//#region #nitro/virtual/public-assets
var publicAssetBases = {};
function isPublicAssetURL(id = "") {
	if (public_assets_data_default[id]) return true;
	for (const base in publicAssetBases) if (id.startsWith(base)) return true;
	return false;
}
//#endregion
//#region node_modules/nitro/dist/runtime/internal/route-rules.mjs
var headers = ((m) => function headersRouteRule(event) {
	for (const [key, value] of Object.entries(m.options || {})) event.res.headers.set(key, value);
});
//#endregion
//#region #nitro/virtual/routing
var findRouteRules = /* @__PURE__ */ (() => {
	const $0 = [{
		name: "headers",
		route: "/assets/**",
		handler: headers,
		options: { "cache-control": "public, max-age=31536000, immutable" }
	}];
	return (m, p) => {
		let r = [];
		if (p.charCodeAt(p.length - 1) === 47) p = p.slice(0, -1) || "/";
		let s = p.split("/");
		if (s.length > 1) {
			if (s[1] === "assets") r.unshift({
				data: $0,
				params: { "_": s.slice(2).join("/") }
			});
		}
		return r;
	};
})();
var _lazy_cuK3PE = defineLazyEventHandler(() => import("./_chunks/ssr-renderer.mjs"));
var findRoute = /* @__PURE__ */ (() => {
	const data = {
		route: "/**",
		handler: _lazy_cuK3PE
	};
	return ((_m, p) => {
		return {
			data,
			params: { "_": p.slice(1) }
		};
	});
})();
[].filter(Boolean);
//#endregion
//#region node_modules/nitro/dist/runtime/internal/error/prod.mjs
var errorHandler = (error, event) => {
	const res = defaultHandler(error, event);
	return new FastResponse(typeof res.body === "string" ? res.body : JSON.stringify(res.body, null, 2), res);
};
function defaultHandler(error, event) {
	const unhandled = error.unhandled ?? !HTTPError.isError(error);
	const { status = 500, statusText = "" } = unhandled ? {} : error;
	if (status === 404) {
		const url = event.url || new URL(event.req.url);
		const baseURL = "/";
		if (/^\/[^/]/.test(baseURL) && !url.pathname.startsWith(baseURL)) return {
			status: 302,
			headers: new Headers({ location: `${baseURL}${url.pathname.slice(1)}${url.search}` })
		};
	}
	const headers = new Headers(unhandled ? {} : error.headers);
	headers.set("content-type", "application/json; charset=utf-8");
	return {
		status,
		statusText,
		headers,
		body: {
			error: true,
			...unhandled ? {
				status,
				unhandled: true
			} : typeof error.toJSON === "function" ? error.toJSON() : {
				status,
				statusText,
				message: error.message
			}
		}
	};
}
//#endregion
//#region #nitro/virtual/error-handler
var errorHandlers = [errorHandler];
async function error_handler_default(error, event) {
	for (const handler of errorHandlers) try {
		const response = await handler(error, event, { defaultHandler });
		if (response) return response;
	} catch (error) {
		console.error(error);
	}
}
//#endregion
//#region #nitro/virtual/app
function createNitroApp() {
	const captureError = (error, errorCtx) => {
		if (errorCtx?.event) {
			const errors = errorCtx.event.req.context?.nitro?.errors;
			if (errors) errors.push({
				error,
				context: errorCtx
			});
		}
	};
	const h3App = createH3App({ onError(error, event) {
		return error_handler_default(error, event);
	} });
	let appHandler = (req) => {
		req.context ||= {};
		req.context.nitro = req.context.nitro || { errors: [] };
		return h3App.fetch(req);
	};
	return {
		fetch: appHandler,
		h3: h3App,
		hooks: void 0,
		captureError
	};
}
function createH3App(config) {
	const h3App = new H3Core(config);
	h3App["~findRoute"] = (event) => findRoute(event.req.method, event.url.pathname);
	h3App["~getMiddleware"] = (event, route) => {
		const pathname = event.url.pathname;
		const method = event.req.method;
		const middleware = [];
		const routeRules = getRouteRules(method, pathname);
		event.context.routeRules = routeRules?.routeRules;
		if (routeRules?.routeRuleMiddleware.length) middleware.push(...routeRules.routeRuleMiddleware);
		if (route?.data?.middleware?.length) middleware.push(...route.data.middleware);
		return middleware;
	};
	return h3App;
}
//#endregion
//#region node_modules/nitro/dist/runtime/internal/app.mjs
var APP_ID = "default";
function useNitroApp() {
	let instance = useNitroApp._instance;
	if (instance) return instance;
	instance = useNitroApp._instance = createNitroApp();
	globalThis.__nitro__ = globalThis.__nitro__ || {};
	globalThis.__nitro__[APP_ID] = instance;
	return instance;
}
function useNitroHooks() {
	const nitroApp = useNitroApp();
	const hooks = nitroApp.hooks;
	if (hooks) return hooks;
	return nitroApp.hooks = new HookableCore();
}
function getRouteRules(method, pathname) {
	const m = findRouteRules(method, pathname);
	if (!m?.length) return { routeRuleMiddleware: [] };
	const routeRules = {};
	for (const layer of m) for (const rule of layer.data) {
		const currentRule = routeRules[rule.name];
		if (currentRule) {
			if (rule.options === false) {
				delete routeRules[rule.name];
				continue;
			}
			if (typeof currentRule.options === "object" && typeof rule.options === "object") currentRule.options = {
				...currentRule.options,
				...rule.options
			};
			else currentRule.options = rule.options;
			currentRule.route = rule.route;
			currentRule.params = {
				...currentRule.params,
				...layer.params
			};
		} else if (rule.options !== false) routeRules[rule.name] = {
			...rule,
			params: layer.params
		};
	}
	const middleware = [];
	const orderedRules = Object.values(routeRules).sort((a, b) => (a.handler?.order || 0) - (b.handler?.order || 0));
	for (const rule of orderedRules) {
		if (rule.options === false || !rule.handler) continue;
		middleware.push(rule.handler(rule));
	}
	return {
		routeRules,
		routeRuleMiddleware: middleware
	};
}
//#endregion
//#region node_modules/nitro/dist/presets/cloudflare/runtime/_module-handler.mjs
function createHandler(hooks) {
	const nitroApp = useNitroApp();
	const nitroHooks = useNitroHooks();
	return {
		async fetch(request, env, context) {
			globalThis.__env__ = env;
			augmentReq(request, {
				env,
				context
			});
			const ctxExt = {};
			const url = new URL(request.url);
			if (hooks.fetch) {
				const res = await hooks.fetch(request, env, context, url, ctxExt);
				if (res) return res;
			}
			return await nitroApp.fetch(request);
		},
		scheduled(controller, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:scheduled", {
				controller,
				env,
				context
			}) || Promise.resolve());
		},
		email(message, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:email", {
				message,
				event: message,
				env,
				context
			}) || Promise.resolve());
		},
		queue(batch, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:queue", {
				batch,
				event: batch,
				env,
				context
			}) || Promise.resolve());
		},
		tail(traces, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:tail", {
				traces,
				env,
				context
			}) || Promise.resolve());
		},
		trace(traces, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:trace", {
				traces,
				env,
				context
			}) || Promise.resolve());
		}
	};
}
function augmentReq(cfReq, ctx) {
	const req = cfReq;
	req.ip = cfReq.headers.get("cf-connecting-ip") || void 0;
	req.runtime ??= { name: "cloudflare" };
	req.runtime.cloudflare = {
		...req.runtime.cloudflare,
		...ctx
	};
	req.waitUntil = ctx.context?.waitUntil.bind(ctx.context);
}
//#endregion
//#region node_modules/nitro/dist/presets/cloudflare/runtime/cloudflare-module.mjs
var cloudflare_module_default = createHandler({ fetch(cfRequest, env, context, url) {
	if (env.ASSETS && isPublicAssetURL(url.pathname)) return env.ASSETS.fetch(cfRequest);
} });
//#endregion
export { cloudflare_module_default as default };
