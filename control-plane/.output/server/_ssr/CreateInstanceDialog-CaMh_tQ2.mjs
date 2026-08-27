import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { F as require_jsx_runtime, d as DialogContent$1, f as DialogDescription$1, h as DialogTitle$1, l as Dialog$1, m as DialogPortal$1, p as DialogOverlay$1, u as DialogClose } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { r as useQuery } from "../_libs/tanstack__react-query.mjs";
import { i as cn, l as nodesQuery, n as CURRENT_MINECRAFT_VERSION, p as useCreateInstance, t as Button } from "./queries-D6pnQp7P.mjs";
import { R as Check, t as X } from "../_libs/lucide-react.mjs";
import { n as CheckboxIndicator, t as Checkbox$1 } from "../_libs/@radix-ui/react-checkbox+[...].mjs";
import { a as SelectItem, i as SelectContent, n as Label, o as SelectTrigger, r as Select, s as SelectValue, t as Input } from "./select-DzQ3G0Ie.mjs";
import { t as Root } from "../_libs/radix-ui__react-separator.mjs";
import { n as SwitchThumb, t as Switch$1 } from "../_libs/radix-ui__react-switch.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/CreateInstanceDialog-CaMh_tQ2.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var Checkbox = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Checkbox$1, {
	ref,
	className: cn("grid place-content-center peer h-4 w-4 shrink-0 rounded-sm border border-primary shadow cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground", className),
	...props,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CheckboxIndicator, {
		className: cn("grid place-content-center text-current"),
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "h-4 w-4" })
	})
}));
Checkbox.displayName = Checkbox$1.displayName;
var Dialog = Dialog$1;
var DialogPortal = DialogPortal$1;
var DialogOverlay = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogOverlay$1, {
	ref,
	className: cn("fixed inset-0 z-50 bg-black/80  data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0", className),
	...props
}));
DialogOverlay.displayName = DialogOverlay$1.displayName;
var DialogContent = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogPortal, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogOverlay, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent$1, {
	ref,
	className: cn("fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 sm:rounded-lg", className),
	...props,
	children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogClose, {
		className: "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background cursor-pointer transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-4 w-4" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "sr-only",
			children: "Close"
		})]
	})]
})] }));
DialogContent.displayName = DialogContent$1.displayName;
var DialogHeader = ({ className, ...props }) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
	className: cn("flex flex-col space-y-1.5 text-center sm:text-left", className),
	...props
});
DialogHeader.displayName = "DialogHeader";
var DialogFooter = ({ className, ...props }) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
	className: cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className),
	...props
});
DialogFooter.displayName = "DialogFooter";
var DialogTitle = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle$1, {
	ref,
	className: cn("text-lg font-semibold leading-none tracking-tight", className),
	...props
}));
DialogTitle.displayName = DialogTitle$1.displayName;
var DialogDescription = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription$1, {
	ref,
	className: cn("text-sm text-muted-foreground", className),
	...props
}));
DialogDescription.displayName = DialogDescription$1.displayName;
var Separator = import_react.forwardRef(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Root, {
	ref,
	decorative,
	orientation,
	className: cn("shrink-0 bg-border", orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]", className),
	...props
}));
Separator.displayName = Root.displayName;
var Switch = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch$1, {
	className: cn("peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input", className),
	...props,
	ref,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SwitchThumb, { className: cn("pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0") })
}));
Switch.displayName = Switch$1.displayName;
var MIN_MEMORY = 512;
var MAX_MEMORY = 2048;
function CreateInstanceDialog({ open, onOpenChange }) {
	const { data: nodes = [] } = useQuery(nodesQuery);
	const createInstance = useCreateInstance();
	const [name, setName] = (0, import_react.useState)("");
	const [vmUsername, setVmUsername] = (0, import_react.useState)("mcadmin");
	const [memoryMb, setMemoryMb] = (0, import_react.useState)(MAX_MEMORY);
	const [computeNodeId, setComputeNodeId] = (0, import_react.useState)("");
	const [acceptEula, setAcceptEula] = (0, import_react.useState)(false);
	const [autoPassword, setAutoPassword] = (0, import_react.useState)(true);
	const eligibleNodes = nodes.filter((n) => n.ready);
	const selectedNode = computeNodeId || eligibleNodes[0]?.id || "";
	const nameError = name.length > 0 && !/^[a-z0-9][a-z0-9-]{1,30}$/.test(name) ? "Use lowercase letters, digits and dashes (2–31 chars)." : null;
	const memoryError = memoryMb < MIN_MEMORY || memoryMb > MAX_MEMORY ? `Memory must be between ${MIN_MEMORY} and ${MAX_MEMORY} MiB.` : null;
	const canSubmit = name.length > 1 && !nameError && !memoryError && acceptEula && !!selectedNode && !createInstance.isPending;
	function reset() {
		setName("");
		setVmUsername("mcadmin");
		setMemoryMb(MAX_MEMORY);
		setComputeNodeId("");
		setAcceptEula(false);
		setAutoPassword(true);
	}
	function submit() {
		if (!canSubmit) return;
		createInstance.mutate({
			name,
			vmUsername,
			memoryMb,
			vcpus: 1,
			minecraftVersion: CURRENT_MINECRAFT_VERSION,
			acceptEula,
			autogeneratePassword: autoPassword,
			computeNodeId: selectedNode
		}, { onSuccess: () => {
			reset();
			onOpenChange(false);
		} });
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open,
		onOpenChange: (next) => {
			if (!next) reset();
			onOpenChange(next);
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "sm:max-w-lg",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Create instance" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription, { children: "Provisions a Minecraft workload on an available compute node. This build simulates creation locally." })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-4",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "inst-name",
									children: "Instance name"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									id: "inst-name",
									placeholder: "survival-02",
									value: name,
									onChange: (e) => setName(e.target.value.toLowerCase()),
									"aria-invalid": !!nameError
								}),
								nameError && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xs text-destructive",
									children: nameError
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid gap-4 sm:grid-cols-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "vm-user",
									children: "VM username"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									id: "vm-user",
									value: vmUsername,
									onChange: (e) => setVmUsername(e.target.value)
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "node",
									children: "Compute node"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: selectedNode,
									onValueChange: setComputeNodeId,
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
										id: "node",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: "Select node" })
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: eligibleNodes.map((node) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectItem, {
										value: node.id,
										children: [
											node.name,
											" · ",
											node.capacity.availableSlots,
											" slots free"
										]
									}, node.id)) })]
								})]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid gap-4 sm:grid-cols-3",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5 sm:col-span-1",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "memory",
										children: "Memory (MiB)"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										id: "memory",
										type: "number",
										min: MIN_MEMORY,
										max: MAX_MEMORY,
										step: 512,
										value: memoryMb,
										onChange: (e) => setMemoryMb(Number(e.target.value)),
										"aria-invalid": !!memoryError
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "vcpu",
										children: "vCPU"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										id: "vcpu",
										value: 1,
										readOnly: true,
										disabled: true
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "mcv",
										children: "Minecraft version"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										id: "mcv",
										value: CURRENT_MINECRAFT_VERSION,
										readOnly: true,
										disabled: true
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-xs text-muted-foreground",
							children: [
								"Limits in this environment: ",
								MIN_MEMORY,
								"–",
								MAX_MEMORY,
								" MiB memory, exactly 1 vCPU, Minecraft ",
								CURRENT_MINECRAFT_VERSION,
								"."
							]
						}),
						memoryError && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-destructive",
							children: memoryError
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Separator, {}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center justify-between gap-4 rounded-md border border-border bg-surface/60 px-3 py-2.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-0.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "autopass",
									className: "text-sm",
									children: "Autogenerated VM password"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xs text-muted-foreground",
									children: "Credentials are never displayed or stored by the console."
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch, {
								id: "autopass",
								checked: autoPassword,
								onCheckedChange: setAutoPassword
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
							className: "flex cursor-pointer items-start gap-2.5 rounded-md border border-border px-3 py-2.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Checkbox, {
								id: "eula",
								checked: acceptEula,
								onCheckedChange: (v) => setAcceptEula(v === true),
								className: "mt-0.5"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: "text-sm",
								children: ["Accept the Minecraft EULA", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "block text-xs text-muted-foreground",
									children: "Required before the workload can be provisioned."
								})]
							})]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "ghost",
					onClick: () => onOpenChange(false),
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: submit,
					disabled: !canSubmit,
					children: createInstance.isPending ? "Creating…" : "Create instance"
				})] })
			]
		})
	});
}
//#endregion
export { CreateInstanceDialog as t };
