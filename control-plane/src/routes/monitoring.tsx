import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Boxes,
  Cpu,
  Database,
  Gauge,
  MemoryStick,
  Server,
  ShieldAlert,
} from "lucide-react";

import { MetricBar } from "@/components/MetricBar";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/StateViews";
import {
  InstanceStateBadge,
  NodeStatusBadge,
  SeverityBadge,
} from "@/components/StatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { UsageChart } from "@/features/monitoring/UsageChart";
import {
  formatGb,
  formatMb,
  formatPercent,
  formatTimestamp,
  percentOf,
} from "@/lib/format";
import {
  instancesQuery,
  nodesQuery,
  overviewQuery,
  timeseriesQuery,
} from "@/services/queries";
import type { InstanceState } from "@/types";

export const Route = createFileRoute("/monitoring")({
  component: MonitoringPage,
});

function MonitoringPage() {
  const overview = useQuery(overviewQuery);
  const nodes = useQuery(nodesQuery);
  const instances = useQuery(instancesQuery);
  const timeseries = useQuery(timeseriesQuery);
  const error =
    overview.error ?? nodes.error ?? instances.error ?? timeseries.error;
  const summary = overview.data;
  const nodeList = nodes.data;
  const instanceList = instances.data;
  const timeseriesData = timeseries.data;

  if (error)
    return (
      <ErrorState
        message={error.message}
        onRetry={() =>
          void Promise.all([
            overview.refetch(),
            nodes.refetch(),
            instances.refetch(),
            timeseries.refetch(),
          ])
        }
      />
    );

  const invariants = (nodeList ?? [])
    .flatMap((node) =>
      node.invariants.map((invariant) => ({
        ...invariant,
        nodeId: node.id,
        nodeName: node.name,
      })),
    )
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  const distribution = (
    [
      "running",
      "stopped",
      "starting",
      "unavailable",
      "deleting",
    ] as InstanceState[]
  ).map((state) => ({
    state,
    count:
      instanceList?.filter((instance) => instance.state === state).length ?? 0,
  }));

  return (
    <>
      <PageHeader
        title="Monitoring"
        description="Aggregated health, utilization and invariant signals across the mock infrastructure."
      />

      {!summary ? (
        <CardsSkeleton count={4} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Infrastructure health"
            value={
              summary.status === "operational"
                ? "Operational"
                : summary.status === "degraded"
                  ? "Degraded"
                  : "Down"
            }
            icon={Gauge}
            caption={`${summary.nodesOnline}/${summary.nodesTotal} nodes online`}
          />
          <StatCard
            label="Aggregate capacity"
            value={`${summary.slotsUsed}/${summary.slotsTotal}`}
            icon={Server}
            bar={{
              used: summary.slotsUsed,
              total: summary.slotsTotal,
            }}
            caption="Runtime slots occupied"
          />
          <StatCard
            label="Memory pressure"
            value={formatPercent(
              percentOf(summary.memoryUsedMb, summary.memoryTotalMb),
            )}
            icon={MemoryStick}
            bar={{
              used: summary.memoryUsedMb,
              total: summary.memoryTotalMb,
            }}
            caption={`${formatMb(summary.memoryUsedMb)} used`}
          />
          <StatCard
            label="Storage pressure"
            value={formatPercent(
              percentOf(summary.storageUsedGb, summary.storageTotalGb),
            )}
            icon={Database}
            bar={{
              used: summary.storageUsedGb,
              total: summary.storageTotalGb,
            }}
            caption={`${formatGb(summary.storageUsedGb)} used`}
          />
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        {!timeseriesData ? (
          <CardsSkeleton count={2} />
        ) : (
          <>
            <UsageChart
              data={timeseriesData}
              metric="cpu"
              title="Aggregate CPU"
              subtitle="Recent utilization across reachable nodes"
            />
            <UsageChart
              data={timeseriesData}
              metric="memory"
              title="Aggregate memory"
              subtitle="Recent working-set utilization"
            />
          </>
        )}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="panel p-4">
          <div className="mb-4">
            <h2 className="text-sm font-medium">Node health</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Current reachability and key resource pressure.
            </p>
          </div>
          {!nodeList ? (
            <CardsSkeleton count={2} />
          ) : (
            <div className="space-y-4">
              {nodeList.map((node) => (
                <div
                  key={node.id}
                  className="rounded-md border border-border p-3"
                >
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <Link
                      to="/nodes/$nodeId"
                      params={{ nodeId: node.id }}
                      className="text-sm font-medium hover:text-primary"
                    >
                      {node.name}
                    </Link>
                    <NodeStatusBadge status={node.status} />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
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
                      hint={formatPercent(
                        percentOf(
                          node.metrics.memory.usedMb,
                          node.metrics.memory.totalMb,
                        ),
                      )}
                    />
                    <MetricBar
                      label="Storage"
                      used={node.metrics.mcIaasDisk.usedGb}
                      total={node.metrics.mcIaasDisk.totalGb}
                      hint={formatPercent(
                        percentOf(
                          node.metrics.mcIaasDisk.usedGb,
                          node.metrics.mcIaasDisk.totalGb,
                        ),
                      )}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="panel p-4">
          <div className="mb-4">
            <h2 className="text-sm font-medium">Instance state distribution</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Workload inventory grouped by lifecycle state.
            </p>
          </div>
          <div className="space-y-3">
            {distribution.map(({ state, count }) => (
              <div
                key={state}
                className="flex items-center gap-4 rounded-md border border-border px-3 py-2.5"
              >
                <InstanceStateBadge state={state} />
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{
                      width: `${instanceList?.length ? (count / instanceList.length) * 100 : 0}%`,
                    }}
                  />
                </div>
                <span className="tabular w-6 text-right text-sm font-semibold">
                  {count}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 border-t border-border pt-4">
            <SmallStat
              icon={Boxes}
              label="Total"
              value={instanceList?.length ?? 0}
            />
            <SmallStat
              icon={Cpu}
              label="Running"
              value={
                distribution.find((item) => item.state === "running")?.count ??
                0
              }
            />
            <SmallStat
              icon={ShieldAlert}
              label="Unavailable"
              value={
                distribution.find((item) => item.state === "unavailable")
                  ?.count ?? 0
              }
            />
          </div>
        </section>
      </div>

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold">Recent invariants</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Consistency violations reported by compute agents.
          </p>
        </div>
        {invariants.length === 0 ? (
          <EmptyState
            title="No invariant violations"
            description="All reachable nodes report internally consistent state."
          />
        ) : (
          <div className="panel overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Severity</TableHead>
                  <TableHead>Node</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Detail</TableHead>
                  <TableHead className="text-right">Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invariants.map((invariant) => (
                  <TableRow key={invariant.id}>
                    <TableCell>
                      <SeverityBadge severity={invariant.severity} />
                    </TableCell>
                    <TableCell>
                      <Link
                        to="/nodes/$nodeId"
                        params={{ nodeId: invariant.nodeId }}
                        className="text-sm font-medium hover:text-primary"
                      >
                        {invariant.nodeName}
                      </Link>
                    </TableCell>
                    <TableCell className="tabular text-xs">
                      {invariant.code}
                    </TableCell>
                    <TableCell className="max-w-2xl text-xs text-muted-foreground">
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
      </section>
    </>
  );
}

function SmallStat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Boxes;
  label: string;
  value: number;
}) {
  return (
    <div>
      <Icon className="mb-2 h-4 w-4 text-muted-foreground" />
      <p className="metric-label">{label}</p>
      <p className="tabular mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
