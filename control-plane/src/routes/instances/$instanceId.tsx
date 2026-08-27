import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Cpu,
  Database,
  MemoryStick,
  Network,
  TerminalSquare,
} from "lucide-react";

import { MetricBar } from "@/components/MetricBar";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/StateViews";
import {
  InstanceStateBadge,
  MinecraftStatusBadge,
} from "@/components/StatusBadge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EventsTable } from "@/features/events/EventsTable";
import { InstanceActions } from "@/features/instances/InstanceActions";
import {
  formatGb,
  formatMb,
  formatPercent,
  formatTimestamp,
} from "@/lib/format";
import { eventsQuery, instanceQuery, nodesQuery } from "@/services/queries";

export const Route = createFileRoute("/instances/$instanceId")({
  component: InstanceDetailPage,
});

function InstanceDetailPage() {
  const { instanceId } = Route.useParams();
  const instance = useQuery(instanceQuery(instanceId));
  const nodes = useQuery(nodesQuery);
  const events = useQuery(eventsQuery);

  if (instance.isPending) return <TableSkeleton rows={7} />;
  if (instance.isError)
    return (
      <ErrorState
        message={instance.error.message}
        onRetry={() => void instance.refetch()}
      />
    );

  const node = nodes.data?.find(
    (candidate) => candidate.id === instance.data.computeNodeId,
  );
  const instanceEvents =
    events.data?.filter((event) => event.target === instance.data.name) ?? [];
  const metrics = instance.data.metrics;

  return (
    <>
      <div className="text-xs text-muted-foreground">
        <Link to="/instances" className="hover:text-foreground">
          Instances
        </Link>
        <span className="px-2">/</span>
        {instance.data.name}
      </div>
      <PageHeader
        title={instance.data.name}
        description={`Minecraft ${instance.data.minecraftVersion} workload · ${node?.name ?? "Unassigned node"}`}
        actions={
          <>
            <InstanceStateBadge state={instance.data.state} />
            <MinecraftStatusBadge status={instance.data.minecraftStatus} />
          </>
        }
      />

      <div className="flex justify-end">
        <InstanceActions instance={instance.data} variant="buttons" />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="console">Console</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="grid gap-4 xl:grid-cols-3">
          <Panel
            title="VM configuration"
            description="Provisioned compute profile."
          >
            <Definition label="VM username" value={instance.data.vmUsername} />
            <Definition
              label="Memory"
              value={formatMb(instance.data.memoryMb)}
            />
            <Definition label="vCPU" value={instance.data.vcpus} />
            <Definition
              label="Minecraft version"
              value={instance.data.minecraftVersion}
            />
          </Panel>
          <Panel
            title="Runtime allocation"
            description="Ephemeral resources only present while active."
          >
            <Definition
              label="Compute node"
              value={node?.name ?? "Unavailable"}
            />
            <Definition
              label="Runtime slot"
              value={instance.data.runtime?.slot ?? "Not allocated"}
            />
            <Definition
              label="Internal IP"
              value={instance.data.runtime?.ip ?? "Not allocated"}
            />
            <Definition
              label="Public endpoint"
              value={
                instance.data.runtime
                  ? `example.invalid:${instance.data.runtime.externalPort}`
                  : "Not allocated"
              }
              mono
            />
          </Panel>
          <Panel
            title="Persistence"
            description="Lifecycle and attached data volume."
          >
            <Definition
              label="Persistent storage"
              value={instance.data.persistentStorage}
            />
            <Definition
              label="System disk"
              value={formatGb(metrics.systemStorageGb.totalGb)}
            />
            <Definition
              label="Data disk"
              value={formatGb(metrics.dataStorageGb.totalGb)}
            />
            <Definition
              label="Created at"
              value={formatTimestamp(instance.data.createdAt)}
              mono
            />
          </Panel>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="CPU usage"
              value={formatPercent(metrics.cpuUsagePercent)}
              icon={Cpu}
              bar={{ used: metrics.cpuUsagePercent, total: 100 }}
              caption={`${metrics.cpuTimeSeconds.toLocaleString()} seconds CPU time`}
            />
            <StatCard
              label="Current memory"
              value={formatMb(metrics.memoryCurrentMb)}
              icon={MemoryStick}
              bar={{
                used: metrics.memoryCurrentMb,
                total: metrics.memoryConfiguredMb,
              }}
              caption={`${formatMb(metrics.memoryConfiguredMb)} configured`}
            />
            <StatCard
              label="Resident memory"
              value={formatMb(metrics.memoryRssMb)}
              icon={MemoryStick}
              caption="RSS reported by the hypervisor"
            />
            <StatCard
              label="Network transfer"
              value={formatMb(metrics.networkRxMb + metrics.networkTxMb)}
              icon={Network}
              caption={`${formatMb(metrics.networkRxMb)} RX · ${formatMb(metrics.networkTxMb)} TX`}
            />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <StoragePanel
              label="System disk"
              used={metrics.systemStorageGb.usedGb}
              total={metrics.systemStorageGb.totalGb}
            />
            <StoragePanel
              label="Persistent data disk"
              used={metrics.dataStorageGb.usedGb}
              total={metrics.dataStorageGb.totalGb}
            />
          </div>
        </TabsContent>

        <TabsContent value="console">
          <div className="panel overflow-hidden">
            <div className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-3">
              <TerminalSquare className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Console access</span>
            </div>
            <Tabs defaultValue="vm" className="p-4">
              <TabsList>
                <TabsTrigger value="vm">VM Console</TabsTrigger>
                <TabsTrigger value="minecraft">Minecraft Console</TabsTrigger>
              </TabsList>
              <TabsContent value="vm">
                <MockTerminal
                  title="VM serial console"
                  instanceName={instance.data.name}
                />
              </TabsContent>
              <TabsContent value="minecraft">
                <MockTerminal
                  title="Minecraft RCON console"
                  instanceName={instance.data.name}
                />
              </TabsContent>
            </Tabs>
          </div>
        </TabsContent>

        <TabsContent value="events">
          {events.isPending ? (
            <TableSkeleton rows={5} />
          ) : instanceEvents.length ? (
            <EventsTable events={instanceEvents} />
          ) : (
            <EmptyState
              title="No lifecycle events"
              description="No activity has been recorded for this instance."
            />
          )}
        </TabsContent>
      </Tabs>
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
      <div className="mb-3">
        <h2 className="text-sm font-medium">{title}</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
      <dl className="divide-y divide-border">{children}</dl>
    </section>
  );
}

function Definition({
  label,
  value,
  mono,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd
        className={
          mono
            ? "tabular text-right text-xs"
            : "text-right text-sm font-medium capitalize"
        }
      >
        {value}
      </dd>
    </div>
  );
}

function StoragePanel({
  label,
  used,
  total,
}: {
  label: string;
  used: number;
  total: number;
}) {
  return (
    <section className="panel p-4">
      <div className="mb-4 flex items-center gap-2">
        <Database className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-sm font-medium">{label}</h2>
      </div>
      <MetricBar
        used={used}
        total={total}
        label="Used capacity"
        hint={`${formatGb(used)} / ${formatGb(total)}`}
      />
    </section>
  );
}

function MockTerminal({
  title,
  instanceName,
}: {
  title: string;
  instanceName: string;
}) {
  return (
    <div className="mt-4 min-h-64 rounded-md border border-border bg-background p-4 font-mono text-xs">
      <div className="text-muted-foreground">
        # {title} · {instanceName}
      </div>
      <div className="mt-5 text-warning">
        Mock console — backend integration pending
      </div>
      <div className="mt-2 text-muted-foreground">
        No connection has been opened. Interactive output will become available
        through the future Control Plane API.
      </div>
      <div
        className="mt-6 inline-block h-4 w-2 animate-pulse bg-primary/70"
        aria-hidden
      />
    </div>
  );
}
