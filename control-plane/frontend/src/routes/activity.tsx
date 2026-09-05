import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/StateViews";
import { Button } from "@/components/ui/button";
import { EventsTable } from "@/features/events/EventsTable";
import { filteredEventsQuery } from "@/services/queries";
import type { EventLevel } from "@/types";

type Filter = "all" | EventLevel;

export const Route = createFileRoute("/activity")({ component: ActivityPage });

function ActivityPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const events = useQuery(
    filteredEventsQuery(filter === "all" ? undefined : filter),
  );
  const filtered =
    events.data?.filter(
      (event) => filter === "all" || event.level === filter,
    ) ?? [];

  return (
    <>
      <PageHeader
        title="Activity"
        description="Chronological lifecycle, runtime, recovery and security events recorded by the Control Plane (latest 100 matching events)."
        actions={
          <div className="flex rounded-md border border-border bg-muted/40 p-1">
            {(["all", "info", "warning", "error"] as Filter[]).map((level) => (
              <Button
                key={level}
                variant={filter === level ? "secondary" : "ghost"}
                size="sm"
                className="h-7 capitalize"
                onClick={() => setFilter(level)}
              >
                {level}
              </Button>
            ))}
          </div>
        }
      />
      {events.isPending ? (
        <TableSkeleton rows={8} />
      ) : events.isError ? (
        <ErrorState
          message={events.error.message}
          onRetry={() => void events.refetch()}
        />
      ) : filtered.length ? (
        <EventsTable events={filtered} />
      ) : (
        <EmptyState
          title={`No ${filter} events`}
          description="Try a different severity filter."
        />
      )}
    </>
  );
}
