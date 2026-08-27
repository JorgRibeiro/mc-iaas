import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  Cpu,
  Database,
  MemoryStick,
  RotateCw,
  Server,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";

import { MetricBar } from "@/components/MetricBar";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/StateViews";
import {
  HealthBadge,
  NodeStatusBadge,
  ReadyBadge,
  SeverityBadge,
} from "@/components/StatusBadge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EventsTable } from "@/features/events/EventsTable";
import { InstancesTable } from "@/features/instances/InstancesTable";
import {
  formatGb,
  formatMb,
  formatPercent,
  formatTimestamp,
  formatUptime,
  relativeTime,
} from "@/lib/format";
import {
  eventsQuery,
  instancesQuery,
  nodeQuery,
  nodesQuery,
  useReconcileNode,
} from "@/services/queries";

export const Route = createFileRoute("/nodes/$nodeId")({
  component: NodeDetailPage,
});

function NodeDetailPage() {
  const { nodeId } = Route.useParams();
  const node = useQuery(nodeQuery(nodeId));
  const nodes = useQuery(nodesQuery);
  const instances = useQuery(instancesQuery);
  const events = useQuery(eventsQuery);
  const reconcile = useReconcileNode();
  const [confirmOpen, setConfirmOpen] = useState(false);

  if (node.isPending) return <TableSkeleton rows={7} />;
  if (node.isError)
    return (
      <ErrorState
        message={node.error.message}
        onRetry={() => void node.refetch()}
      />
    );

  const hostInstances =
    instances.data?.filter(
      (instance) => instance.computeNodeId === node.data.id,
    ) ?? [];
  const targets = new Set([
    node.data.name,
    ...hostInstances.map((instance) => instance.name),
  ]);
  const hostEvents =
    events.data?.filter((event) => targets.has(event.target)) ?? [];
  const memoryPct = node.data.metrics.memory.totalMb
    ? (node.data.metrics.memory.usedMb / node.data.metrics.memory.totalMb) * 100
    : 0;

  return (
    <>
      <div className="text-xs text-muted-foreground">
        <Link to="/nodes" className="hover:text-foreground">
          Compute nodes
        </Link>
        <span className="px-2">/</span>
        {node.data.name}
      </div>
      <PageHeader
        title={node.data.name}
        description={`Agent v${node.data.agentVersion} · ${node.data.region} · last seen ${relativeTime(node.data.lastSeen)}`}
        actions={
          <>
            <NodeStatusBadge status={node.data.status} />
            <ReadyBadge ready={node.data.ready} />
            <Button
              variant="outline"
              size="sm"
              disabled={reconcile.isPending || !node.data.ready}
              onClick={() => setConfirmOpen(true)}
            >
              <RotateCw
                className={
                  reconcile.isPending ? "h-4 w-4 animate-spin" : "h-4 w-4"
                }
              />{" "}
              Reconcile node
            </Button>
          </>
        }
      />

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="max-w-full justify-start overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="instances">Instances</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="invariants">Invariants</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Agent uptime"
              value={formatUptime(node.data.uptimeSeconds)}
              icon={Activity}
              caption={`Last heartbeat ${formatTimestamp(node.data.lastSeen)}`}
            />
            <StatCard
              label="Active instances"
              value={`${node.data.capacity.activeInstances}/${node.data.capacity.maxActiveInstances}`}
              icon={Server}
              bar={{
                used: node.data.capacity.activeInstances,
                total: node.data.capacity.maxActiveInstances,
              }}
            />
            <StatCard
              label="Occupied slots"
              value={node.data.capacity.occupiedRuntimeSlots}
              icon={Cpu}
              caption={`${node.data.capacity.availableSlots} slots available`}
            />
            <StatCard
              label="Open invariants"
              value={node.data.invariants.length}
              icon={ShieldCheck}
              caption={
                node.data.invariants.length
                  ? "Review required"
                  : "Node consistent"
              }
            />
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            <Panel
              title="Component health"
              description="Readiness reported by the node agent."
            >
              <div className="divide-y divide-border">
                {Object.entries(node.data.health).map(([name, state]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between py-3 first:pt-0 last:pb-0"
                  >
                    <span className="text-sm capitalize">{name}</span>
                    <HealthBadge state={state} />
                  </div>
                ))}
              </div>
            </Panel>
            <Panel
              title="Capacity"
              description="Runtime scheduling limits and current allocation."
            >
              <div className="grid grid-cols-2 gap-4">
                <Value
                  label="Maximum active"
                  value={node.data.capacity.maxActiveInstances}
                />
                <Value
                  label="Active instances"
                  value={node.data.capacity.activeInstances}
                />
                <Value
                  label="Occupied slots"
                  value={node.data.capacity.occupiedRuntimeSlots}
                />
                <Value
                  label="Available slots"
                  value={node.data.capacity.availableSlots}
                />
              </div>
            </Panel>
          </div>
        </TabsContent>

        <TabsContent value="instances">
          {instances.isPending || nodes.isPending ? (
            <TableSkeleton rows={4} />
          ) : hostInstances.length ? (
            <InstancesTable
              instances={hostInstances}
              nodes={nodes.data ?? []}
            />
          ) : (
            <EmptyState
              title="No instances on this node"
              description="This node has no scheduled workloads."
            />
          )}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-3">
            <Panel
              title="CPU"
              description={`${node.data.metrics.cpu.cores} logical cores`}
            >
              <MetricBar
                label="Usage"
                used={node.data.metrics.cpu.usagePercent}
                total={100}
                hint={formatPercent(node.data.metrics.cpu.usagePercent)}
              />
              <div className="mt-5 grid grid-cols-3 gap-3">
                <Value label="Load 1m" value={node.data.metrics.cpu.load1m} />
                <Value label="Load 5m" value={node.data.metrics.cpu.load5m} />
                <Value label="Load 15m" value={node.data.metrics.cpu.load15m} />
              </div>
            </Panel>
            <Panel
              title="Memory"
              description={`${formatMb(node.data.metrics.memory.availableMb)} available`}
            >
              <MetricBar
                label="Used"
                used={node.data.metrics.memory.usedMb}
                total={node.data.metrics.memory.totalMb}
                hint={formatPercent(memoryPct)}
              />
              <div className="mt-5 grid grid-cols-3 gap-3">
                <Value
                  label="Used"
                  value={formatMb(node.data.metrics.memory.usedMb)}
                />
                <Value
                  label="Available"
                  value={formatMb(node.data.metrics.memory.availableMb)}
                />
                <Value
                  label="Total"
                  value={formatMb(node.data.metrics.memory.totalMb)}
                />
              </div>
            </Panel>
            <Panel title="Storage" description="Host filesystem utilization">
              <div className="space-y-5">
                <MetricBar
                  label="Root disk"
                  used={node.data.metrics.rootDisk.usedGb}
                  total={node.data.metrics.rootDisk.totalGb}
                  hint={`${formatGb(node.data.metrics.rootDisk.usedGb)} / ${formatGb(node.data.metrics.rootDisk.totalGb)}`}
                />
                <MetricBar
                  label="MC-IaaS disk"
                  used={node.data.metrics.mcIaasDisk.usedGb}
                  total={node.data.metrics.mcIaasDisk.totalGb}
                  hint={`${formatGb(node.data.metrics.mcIaasDisk.usedGb)} / ${formatGb(node.data.metrics.mcIaasDisk.totalGb)}`}
                />
              </div>
            </Panel>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard
              label="CPU usage"
              value={formatPercent(node.data.metrics.cpu.usagePercent)}
              icon={Cpu}
            />
            <StatCard
              label="Memory used"
              value={formatMb(node.data.metrics.memory.usedMb)}
              icon={MemoryStick}
            />
            <StatCard
              label="MC-IaaS storage"
              value={formatGb(node.data.metrics.mcIaasDisk.usedGb)}
              icon={Database}
            />
          </div>
        </TabsContent>

        <TabsContent value="invariants">
          {node.data.invariants.length === 0 ? (
            <EmptyState
              title="No invariant violations"
              description="The agent reports that infrastructure state is internally consistent."
              icon={ShieldCheck}
            />
          ) : (
            <div className="panel overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Severity</TableHead>
                    <TableHead>Code</TableHead>
                    <TableHead>Detail</TableHead>
                    <TableHead className="text-right">Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {node.data.invariants.map((invariant) => (
                    <TableRow key={invariant.id}>
                      <TableCell>
                        <SeverityBadge severity={invariant.severity} />
                      </TableCell>
                      <TableCell className="tabular text-xs">
                        {invariant.code}
                      </TableCell>
                      <TableCell className="max-w-xl text-xs text-muted-foreground">
                        {invariant.detail}
                      </TableCell>
                      <TableCell className="tabular text-right text-xs whitespace-nowrap">
                        {formatTimestamp(invariant.timestamp)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="events">
          {events.isPending ? (
            <TableSkeleton rows={5} />
          ) : hostEvents.length ? (
            <EventsTable events={hostEvents} />
          ) : (
            <EmptyState title="No events for this node" />
          )}
        </TabsContent>
      </Tabs>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reconcile {node.data.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              This will simulate a recovery pass and append mock events. No
              compute node or agent will be contacted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                reconcile.mutate({ id: node.data.id, name: node.data.name })
              }
            >
              Run reconciliation
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel p-4">
      <div className="mb-4">
        <h2 className="text-sm font-medium">{title}</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  );
}

function Value({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="metric-label">{label}</p>
      <p className="tabular mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}
