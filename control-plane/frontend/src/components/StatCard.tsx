import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { MetricBar } from "@/components/MetricBar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Info } from "lucide-react";

export function StatCard({
  label,
  value,
  unit,
  caption,
  icon: Icon,
  tooltip,
  bar,
  children,
  className,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  caption?: string;
  icon?: LucideIcon;
  tooltip?: string;
  bar?: { used: number | null | undefined; total: number | null | undefined };
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("panel flex flex-col gap-3 p-4", className)}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="metric-label">{label}</span>
          {tooltip && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  aria-label={`About ${label}`}
                  className="text-muted-foreground/70 transition-colors hover:text-foreground"
                >
                  <Info className="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent className="max-w-64">{tooltip}</TooltipContent>
            </Tooltip>
          )}
        </div>
        {Icon && (
          <Icon className="h-4 w-4 text-muted-foreground/70" aria-hidden />
        )}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className="tabular text-2xl leading-none font-semibold">
          {value ?? "—"}
        </span>
        {unit && <span className="text-xs text-muted-foreground">{unit}</span>}
      </div>

      {bar && <MetricBar used={bar.used} total={bar.total} />}
      {caption && <p className="text-xs text-muted-foreground">{caption}</p>}
      {children}
    </div>
  );
}
