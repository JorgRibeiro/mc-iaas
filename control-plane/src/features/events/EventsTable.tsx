import { AlertTriangle, Info, XCircle } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatTimestamp, relativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { EventLevel, PlatformEvent } from "@/types";

function LevelTag({ level }: { level: EventLevel }) {
  const conf = {
    info: { icon: Info, cls: "border-border-strong bg-muted/60 text-muted-foreground", label: "Info" },
    warning: { icon: AlertTriangle, cls: "border-warning/35 bg-warning/10 text-warning", label: "Warning" },
    error: { icon: XCircle, cls: "border-destructive/35 bg-destructive/10 text-destructive", label: "Error" },
  }[level];
  const Icon = conf.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium",
        conf.cls,
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {conf.label}
    </span>
  );
}

export function EventsTable({ events, compact }: { events: PlatformEvent[]; compact?: boolean }) {
  return (
    <div className="panel overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-48">Timestamp</TableHead>
            <TableHead className="w-28">Level</TableHead>
            {!compact && <TableHead className="w-28">Component</TableHead>}
            <TableHead>Event</TableHead>
            <TableHead className="w-44">Target</TableHead>
            {!compact && <TableHead>Message</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id}>
              <TableCell className="tabular text-xs whitespace-nowrap text-muted-foreground">
                {compact ? relativeTime(event.timestamp) : formatTimestamp(event.timestamp)}
              </TableCell>
              <TableCell>
                <LevelTag level={event.level} />
              </TableCell>
              {!compact && (
                <TableCell className="text-xs text-muted-foreground">{event.component}</TableCell>
              )}
              <TableCell className="tabular text-xs">{event.event}</TableCell>
              <TableCell className="text-xs">{event.target}</TableCell>
              {!compact && (
                <TableCell className="max-w-md text-xs text-muted-foreground">{event.message}</TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
