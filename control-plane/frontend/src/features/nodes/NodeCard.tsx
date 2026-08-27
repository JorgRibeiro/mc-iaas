import { Link } from "@tanstack/react-router";
import { ArrowUpRight, Clock } from "lucide-react";

import { MetricBar } from "@/components/MetricBar";
import { NodeStatusBadge, ReadyBadge } from "@/components/StatusBadge";
import { formatGb, formatMb, formatPercent, formatUptime } from "@/lib/format";
import type { ComputeNode } from "@/types";

export function NodeCard({ node }: { node: ComputeNode }) {
  return (
    <div className="panel flex flex-col gap-4 p-4 transition-colors hover:border-border-strong">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1.5">
          <Link
            to="/nodes/$nodeId"
            params={{ nodeId: node.id }}
            className="group inline-flex items-center gap-1.5 font-medium tracking-tight"
          >
            {node.name}
            <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
          </Link>
          <div className="flex flex-wrap items-center gap-1.5">
            <NodeStatusBadge status={node.status} />
            <ReadyBadge ready={node.ready} />
          </div>
        </div>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3.5 w-3.5" aria-hidden />
          {formatUptime(node.uptimeSeconds)}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 border-y border-border py-3">
        <Stat label="Active" value={node.capacity.activeInstances} />
        <Stat label="Slots used" value={node.capacity.occupiedRuntimeSlots} />
        <Stat label="Available" value={node.capacity.availableSlots} />
      </div>

      <div className="space-y-2.5">
        <MetricBar
          label="CPU"
          used={node.metrics.cpu.usagePercent}
          total={100}
          hint={formatPercent(node.metrics.cpu.usagePercent)}
        />
        <MetricBar
          label="Memory"
          used={node.metrics.memory.usedMb}
          total={node.metrics.memory.totalMb}
          hint={`${formatMb(node.metrics.memory.usedMb)} / ${formatMb(node.metrics.memory.totalMb)}`}
        />
        <MetricBar
          label="MC-IaaS disk"
          used={node.metrics.mcIaasDisk.usedGb}
          total={node.metrics.mcIaasDisk.totalGb}
          hint={`${formatGb(node.metrics.mcIaasDisk.usedGb)} / ${formatGb(node.metrics.mcIaasDisk.totalGb)}`}
        />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-0.5">
      <p className="metric-label">{label}</p>
      <p className="tabular text-lg leading-none font-semibold">{value}</p>
    </div>
  );
}
