import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/StateViews";
import { Button } from "@/components/ui/button";
import { CreateInstanceDialog } from "@/features/instances/CreateInstanceDialog";
import { InstancesTable } from "@/features/instances/InstancesTable";
import { instancesQuery, nodesQuery } from "@/services/queries";

export const Route = createFileRoute("/instances/")({
  component: InstancesPage,
});

function InstancesPage() {
  const instances = useQuery(instancesQuery);
  const nodes = useQuery(nodesQuery);
  const [createOpen, setCreateOpen] = useState(false);
  const error = instances.error ?? nodes.error;
  const instanceList = instances.data;
  const nodeList = nodes.data;

  return (
    <>
      <PageHeader
        title="Instances"
        description="Minecraft workloads managed as virtual-machine instances across the compute fleet."
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" /> Create instance
          </Button>
        }
      />
      {error ? (
        <ErrorState
          message={error.message}
          onRetry={() =>
            void Promise.all([instances.refetch(), nodes.refetch()])
          }
        />
      ) : !instanceList || !nodeList ? (
        <TableSkeleton rows={5} />
      ) : instanceList.length === 0 ? (
        <EmptyState
          title="No instances provisioned"
          description="Create a workload to populate the control plane inventory."
          action={
            <Button
              size="sm"
              className="mt-2"
              onClick={() => setCreateOpen(true)}
            >
              Create instance
            </Button>
          }
        />
      ) : (
        <InstancesTable instances={instanceList} nodes={nodeList} />
      )}
      <CreateInstanceDialog open={createOpen} onOpenChange={setCreateOpen} />
    </>
  );
}
