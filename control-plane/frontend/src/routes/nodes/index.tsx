import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/StateViews";
import { NodesTable } from "@/features/nodes/NodesTable";
import { nodesQuery } from "@/services/queries";

export const Route = createFileRoute("/nodes/")({ component: NodesPage });

function NodesPage() {
  const nodes = useQuery(nodesQuery);

  return (
    <>
      <PageHeader
        title="Compute nodes"
        description="Registered hosts, agent reachability and available workload capacity. RAYLANDSON-COMPUTE is an offline visual mock."
      />
      {nodes.isPending ? (
        <TableSkeleton rows={4} />
      ) : nodes.isError ? (
        <ErrorState
          message={nodes.error.message}
          onRetry={() => void nodes.refetch()}
        />
      ) : nodes.data.length === 0 ? (
        <EmptyState
          title="No compute nodes registered"
          description="Nodes will appear after the Control Plane API is connected."
        />
      ) : (
        <NodesTable nodes={nodes.data} />
      )}
    </>
  );
}
