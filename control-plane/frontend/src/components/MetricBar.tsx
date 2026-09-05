import { cn } from "@/lib/utils";
import { percentOf } from "@/lib/format";

export function MetricBar({
  used,
  total,
  label,
  hint,
  className,
}: {
  used: number | null | undefined;
  total: number | null | undefined;
  label?: string;
  hint?: string;
  className?: string;
}) {
  const pct = percentOf(used, total);
  if (pct === null)
    return (
      <p className="text-xs text-muted-foreground">
        {label ?? "Metric"}: unavailable
      </p>
    );
  const tone =
    pct >= 90 ? "bg-destructive" : pct >= 70 ? "bg-warning" : "bg-primary";

  return (
    <div className={cn("space-y-1.5", className)}>
      {(label || hint) && (
        <div className="flex items-baseline justify-between gap-3">
          {label && <span className="metric-label">{label}</span>}
          {hint && (
            <span className="tabular text-xs text-muted-foreground">
              {hint}
            </span>
          )}
        </div>
      )}
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
        role="meter"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? "usage"}
      >
        <div
          className={cn("h-full rounded-full transition-all", tone)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
