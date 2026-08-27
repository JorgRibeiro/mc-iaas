import { Link } from "@tanstack/react-router";

import { InstanceStateBadge, MinecraftStatusBadge } from "@/components/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { InstanceActions } from "@/features/instances/InstanceActions";
import { formatMb } from "@/lib/format";
import type { ComputeNode, Instance } from "@/types";

export function InstancesTable({
  instances,
  nodes,
}: {
  instances: Instance[];
  nodes: ComputeNode[];
}) {
  const nodeName = (id: string) => nodes.find((n) => n.id === id)?.name ?? "unassigned";

  return (
    <div className="panel overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Name</TableHead>
            <TableHead>State</TableHead>
            <TableHead>Compute node</TableHead>
            <TableHead>Version</TableHead>
            <TableHead className="text-right">Memory</TableHead>
            <TableHead className="text-right">vCPU</TableHead>
            <TableHead>Runtime IP</TableHead>
            <TableHead className="text-right">Public port</TableHead>
            <TableHead>Minecraft</TableHead>
            <TableHead className="w-12 text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {instances.map((instance) => (
            <TableRow key={instance.id}>
              <TableCell>
                <Link
                  to="/instances/$instanceId"
                  params={{ instanceId: instance.id }}
                  className="font-medium hover:text-primary"
                >
                  {instance.name}
                </Link>
                <span className="block text-xs text-muted-foreground">user {instance.vmUsername}</span>
              </TableCell>
              <TableCell>
                <InstanceStateBadge state={instance.state} />
              </TableCell>
              <TableCell className="text-sm">{nodeName(instance.computeNodeId)}</TableCell>
              <TableCell className="tabular text-xs">MC {instance.minecraftVersion}</TableCell>
              <TableCell className="tabular text-right text-xs">{formatMb(instance.memoryMb)}</TableCell>
              <TableCell className="tabular text-right text-xs">{instance.vcpus}</TableCell>
              <TableCell className="tabular text-xs">
                {instance.runtime?.ip ?? <span className="text-muted-foreground">—</span>}
              </TableCell>
              <TableCell className="tabular text-right text-xs">
                {instance.runtime?.externalPort ?? <span className="text-muted-foreground">—</span>}
              </TableCell>
              <TableCell>
                <MinecraftStatusBadge status={instance.minecraftStatus} />
              </TableCell>
              <TableCell className="text-right">
                <InstanceActions instance={instance} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
