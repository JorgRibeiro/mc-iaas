import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/StateViews";
import { Button } from "@/components/ui/button";
import { EventsTable } from "@/features/events/EventsTable";
import { eventsQuery } from "@/services/queries";
import type { EventLevel } from "@/types";

type Filter = "all" | EventLevel;

export const Route = createFileRoute("/activity")({ component: ActivityPage });

function ActivityPage() {
  const events = useQuery(eventsQuery);
  const [filter, setFilter] = useState<Filter>("all");
  const filtered =
    events.data?.filter(
      (event) => filter === "all" || event.level === filter,
    ) ?? [];

  return (
    <>
      <PageHeader
        title="Activity"
        description="Chronological lifecycle, runtime, recovery and security events emitted by the mock Control Plane."
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
