import { Link } from "@tanstack/react-router";

import { NodeStatusBadge, ReadyBadge } from "@/components/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatGb, formatMb, formatPercent, formatUptime, relativeTime } from "@/lib/format";
import type { ComputeNode } from "@/types";

export function NodesTable({ nodes }: { nodes: ComputeNode[] }) {
  return (
    <div className="panel overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Ready</TableHead>
            <TableHead className="text-right">Active</TableHead>
            <TableHead className="text-right">Runtime slots</TableHead>
            <TableHead className="text-right">CPU</TableHead>
            <TableHead>Memory</TableHead>
            <TableHead>Disk</TableHead>
            <TableHead className="text-right">Agent uptime</TableHead>
            <TableHead className="text-right">Last seen</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {nodes.map((node) => (
            <TableRow key={node.id}>
              <TableCell>
                <Link
                  to="/nodes/$nodeId"
                  params={{ nodeId: node.id }}
                  className="font-medium hover:text-primary"
                >
                  {node.name}
                </Link>
                <span className="block text-xs text-muted-foreground">
                  agent v{node.agentVersion} · {node.region}
                </span>
              </TableCell>
              <TableCell>
                <NodeStatusBadge status={node.status} />
              </TableCell>
              <TableCell>
                <ReadyBadge ready={node.ready} />
              </TableCell>
              <TableCell className="tabular text-right">{node.capacity.activeInstances}</TableCell>
              <TableCell className="tabular text-right">
                {node.capacity.occupiedRuntimeSlots}/{node.capacity.maxActiveInstances}
              </TableCell>
              <TableCell className="tabular text-right">
                {formatPercent(node.metrics.cpu.usagePercent)}
              </TableCell>
              <TableCell className="tabular text-xs">
                {formatMb(node.metrics.memory.usedMb)} / {formatMb(node.metrics.memory.totalMb)}
              </TableCell>
              <TableCell className="tabular text-xs">
                {formatGb(node.metrics.mcIaasDisk.usedGb)} / {formatGb(node.metrics.mcIaasDisk.totalGb)}
              </TableCell>
              <TableCell className="tabular text-right">{formatUptime(node.uptimeSeconds)}</TableCell>
              <TableCell className="text-right text-xs text-muted-foreground">
                {relativeTime(node.lastSeen)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
