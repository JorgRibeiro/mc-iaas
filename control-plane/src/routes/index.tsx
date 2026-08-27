import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  Boxes,
  Cpu,
  Database,
  Gauge,
  MemoryStick,
  Server,
  ShieldAlert,
} from "lucide-react";

import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import {
  CardsSkeleton,
  ErrorState,
  TableSkeleton,
} from "@/components/StateViews";
import { InstanceStateBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EventsTable } from "@/features/events/EventsTable";
import { NodeCard } from "@/features/nodes/NodeCard";
import { formatGb, formatMb, formatPercent } from "@/lib/format";
import {
  eventsQuery,
  instancesQuery,
  nodesQuery,
  overviewQuery,
} from "@/services/queries";

export const Route = createFileRoute("/")({ component: OverviewPage });

function OverviewPage() {
  const overview = useQuery(overviewQuery);
  const nodes = useQuery(nodesQuery);
  const instances = useQuery(instancesQuery);
  const events = useQuery(eventsQuery);
  const error =
    overview.error ?? nodes.error ?? instances.error ?? events.error;
  const summary = overview.data;
  const nodeList = nodes.data;
  const instanceList = instances.data;
  const eventList = events.data;

  if (error) {
    return (
      <ErrorState
        message={error.message}
        onRetry={() =>
          void Promise.all([
            overview.refetch(),
            nodes.refetch(),
            instances.refetch(),
            events.refetch(),
          ])
        }
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Infrastructure overview"
        description="Fleet health, workload capacity and recent control plane activity. All values are supplied by the in-memory mock adapter."
      />

      {!summary ? (
        <CardsSkeleton count={8} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-8">
          <StatCard
            label="Infrastructure"
            value={
              summary.status === "operational"
                ? "Operational"
                : summary.status === "degraded"
                  ? "Degraded"
                  : "Down"
            }
            icon={Gauge}
            caption={`${summary.alerts} open invariants`}
            className="2xl:col-span-2"
          />
          <StatCard
            label="Compute nodes"
            value={`${summary.nodesOnline}/${summary.nodesTotal}`}
            icon={Server}
            caption="Online / registered"
          />
          <StatCard
            label="Active workloads"
            value={summary.activeWorkloads}
            icon={Boxes}
            caption="Running instances"
          />
          <StatCard
            label="Runtime slots"
            value={`${summary.slotsUsed}/${summary.slotsTotal}`}
            icon={Activity}
            bar={{
              used: summary.slotsUsed,
              total: summary.slotsTotal,
            }}
          />
          <StatCard
            label="CPU usage"
            value={formatPercent(summary.cpuUsagePercent)}
            icon={Cpu}
            bar={{ used: summary.cpuUsagePercent, total: 100 }}
            tooltip="Average usage across online compute nodes."
          />
          <StatCard
            label="Memory usage"
            value={formatMb(summary.memoryUsedMb)}
            icon={MemoryStick}
            bar={{
              used: summary.memoryUsedMb,
              total: summary.memoryTotalMb,
            }}
            caption={`of ${formatMb(summary.memoryTotalMb)}`}
          />
          <StatCard
            label="Storage usage"
            value={formatGb(summary.storageUsedGb)}
            icon={Database}
            bar={{
              used: summary.storageUsedGb,
              total: summary.storageTotalGb,
            }}
            caption={`of ${formatGb(summary.storageTotalGb)}`}
          />
          <StatCard
            label="Open invariants"
            value={summary.alerts}
            icon={ShieldAlert}
            caption={summary.alerts ? "Requires review" : "No violations"}
          />
        </div>
      )}

      <SectionHeader
        title="Compute nodes"
        description="Health and resource pressure by host."
        to="/nodes"
      />
      {!nodeList ? (
        <CardsSkeleton count={2} />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {nodeList.map((node) => (
            <NodeCard key={node.id} node={node} />
          ))}
        </div>
      )}

      <div className="grid gap-6 2xl:grid-cols-2">
        <section className="min-w-0 space-y-3">
          <SectionHeader
            title="Recent instances"
            description="Latest workload definitions and runtime state."
            to="/instances"
          />
          {!instanceList ? (
            <TableSkeleton rows={3} />
          ) : (
            <div className="panel overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Name</TableHead>
                    <TableHead>Node</TableHead>
                    <TableHead>State</TableHead>
                    <TableHead className="text-right">Public port</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {instanceList.slice(0, 5).map((instance) => (
                    <TableRow key={instance.id}>
                      <TableCell>
                        <Link
                          to="/instances/$instanceId"
                          params={{ instanceId: instance.id }}
                          className="font-medium hover:text-primary"
                        >
                          {instance.name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {nodeList?.find(
                          (node) => node.id === instance.computeNodeId,
                        )?.name ?? "Unassigned"}
                      </TableCell>
                      <TableCell>
                        <InstanceStateBadge state={instance.state} />
                      </TableCell>
                      <TableCell className="tabular text-right text-xs">
                        {instance.runtime?.externalPort ?? "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </section>

        <section className="min-w-0 space-y-3">
          <SectionHeader
            title="Recent events"
            description="Lifecycle and recovery activity."
            to="/activity"
          />
          {!eventList ? (
            <TableSkeleton rows={5} />
          ) : (
            <EventsTable events={eventList.slice(0, 5)} compact />
          )}
        </section>
      </div>
    </>
  );
}

function SectionHeader({
  title,
  description,
  to,
}: {
  title: string;
  description: string;
  to: "/nodes" | "/instances" | "/activity";
}) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div>
        <h2 className="text-sm font-semibold">{title}</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
      <Button asChild variant="ghost" size="sm">
        <Link to={to}>View all</Link>
      </Button>
    </div>
  );
}
