import {
  AlertTriangle,
  CheckCircle2,
  CircleDashed,
  CircleSlash,
  HelpCircle,
  Loader2,
  Pause,
  Play,
  Trash2,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type {
  HealthState,
  InstanceState,
  InvariantSeverity,
  MinecraftStatus,
  NodeStatus,
} from "@/types";

type Tone = "ok" | "warn" | "bad" | "neutral" | "info";

const toneClass: Record<Tone, string> = {
  ok: "border-success/35 bg-success/10 text-success",
  warn: "border-warning/35 bg-warning/10 text-warning",
  bad: "border-destructive/35 bg-destructive/10 text-destructive",
  info: "border-primary/35 bg-primary/10 text-primary",
  neutral: "border-border-strong bg-muted/60 text-muted-foreground",
};

function Pill({
  tone,
  icon: Icon,
  label,
  className,
  spin,
}: {
  tone: Tone;
  icon: LucideIcon;
  label: string;
  className?: string | undefined;
  spin?: boolean | undefined;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        toneClass[tone],
        className,
      )}
    >
      <Icon className={cn("h-3.5 w-3.5", spin && "animate-spin")} aria-hidden />
      {label}
    </span>
  );
}

const nodeMap: Record<
  NodeStatus,
  { tone: Tone; icon: LucideIcon; label: string }
> = {
  unknown: { tone: "neutral", icon: HelpCircle, label: "Unknown" },
  healthy: { tone: "ok", icon: CheckCircle2, label: "Healthy" },
  degraded: { tone: "warn", icon: AlertTriangle, label: "Degraded" },
  unhealthy: { tone: "bad", icon: XCircle, label: "Unhealthy" },
  offline: { tone: "neutral", icon: CircleSlash, label: "Offline" },
};

export function NodeStatusBadge({
  status,
  className,
}: {
  status: NodeStatus;
  className?: string;
}) {
  const conf = nodeMap[status];
  return <Pill {...conf} className={className} />;
}

const instanceMap: Record<
  InstanceState,
  { tone: Tone; icon: LucideIcon; label: string; spin?: boolean }
> = {
  creating: { tone: "info", icon: Loader2, label: "Creating", spin: true },
  stopping: { tone: "info", icon: Loader2, label: "Stopping", spin: true },
  restarting: { tone: "info", icon: Loader2, label: "Restarting", spin: true },
  uncertain: { tone: "warn", icon: HelpCircle, label: "Uncertain" },
  missing: { tone: "bad", icon: CircleSlash, label: "Missing" },
  unknown: { tone: "neutral", icon: HelpCircle, label: "Unknown" },
  paused: { tone: "neutral", icon: Pause, label: "Paused" },
  running: { tone: "ok", icon: Play, label: "Running" },
  stopped: { tone: "neutral", icon: Pause, label: "Stopped" },
  starting: { tone: "info", icon: Loader2, label: "Starting", spin: true },
  unavailable: { tone: "bad", icon: CircleSlash, label: "Unavailable" },
  deleting: { tone: "warn", icon: Trash2, label: "Deleting" },
};

export function InstanceStateBadge({
  state,
  className,
}: {
  state: InstanceState;
  className?: string | undefined;
}) {
  return <Pill {...instanceMap[state]} className={className} />;
}

const mcMap: Record<
  MinecraftStatus,
  { tone: Tone; icon: LucideIcon; label: string; spin?: boolean }
> = {
  unavailable: { tone: "neutral", icon: CircleSlash, label: "Unavailable" },
  online: { tone: "ok", icon: CheckCircle2, label: "Online" },
  offline: { tone: "neutral", icon: CircleDashed, label: "Offline" },
  starting: { tone: "info", icon: Loader2, label: "Starting", spin: true },
  unknown: { tone: "neutral", icon: HelpCircle, label: "Unknown" },
};

export function MinecraftStatusBadge({
  status,
  className,
}: {
  status: MinecraftStatus;
  className?: string | undefined;
}) {
  return <Pill {...mcMap[status]} className={className} />;
}

const healthMap: Record<
  HealthState,
  { tone: Tone; icon: LucideIcon; label: string }
> = {
  ok: { tone: "ok", icon: CheckCircle2, label: "OK" },
  warning: { tone: "warn", icon: AlertTriangle, label: "Warning" },
  error: { tone: "bad", icon: XCircle, label: "Error" },
  unknown: { tone: "neutral", icon: HelpCircle, label: "Unknown" },
};

export function HealthBadge({
  state,
  className,
}: {
  state: HealthState;
  className?: string;
}) {
  return <Pill {...healthMap[state]} className={className} />;
}

export function ReadyBadge({
  ready,
  className,
}: {
  ready: boolean | null;
  className?: string;
}) {
  return (
    <Pill
      tone={ready ? "ok" : "neutral"}
      icon={ready ? CheckCircle2 : CircleSlash}
      label={
        ready === null
          ? "Ready: unknown"
          : ready
            ? "Ready: true"
            : "Ready: false"
      }
      className={className}
    />
  );
}

export function SeverityBadge({ severity }: { severity: InvariantSeverity }) {
  return severity === "critical" ? (
    <Pill tone="bad" icon={XCircle} label="Critical" />
  ) : (
    <Pill tone="warn" icon={AlertTriangle} label="Warning" />
  );
}
