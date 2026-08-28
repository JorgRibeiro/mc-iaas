import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import {
  Activity,
  Boxes,
  LayoutDashboard,
  LineChart,
  Menu,
  Plus,
  Server,
  Settings as SettingsIcon,
  ShieldAlert,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { BrandMark } from "@/components/BrandMark";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { CreateInstanceDialog } from "@/features/instances/CreateInstanceDialog";
import { cn } from "@/lib/utils";
import { overviewQuery } from "@/services/queries";

const navItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/nodes", label: "Compute Nodes", icon: Server },
  { to: "/instances", label: "Instances", icon: Boxes },
  { to: "/monitoring", label: "Monitoring", icon: LineChart },
  { to: "/activity", label: "Activity", icon: Activity },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
] as const;

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-0.5 px-2">
      {navItems.map(({ to, label, icon: Icon }) => (
        <Link
          key={to}
          to={to}
          onClick={onNavigate}
          activeOptions={{ exact: to === "/" }}
          className="flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-sidebar-foreground/75 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          activeProps={{
            className:
              "bg-sidebar-accent text-sidebar-accent-foreground font-medium border-l-2 border-l-primary",
          }}
        >
          <Icon className="h-4 w-4 shrink-0" aria-hidden />
          {label}
        </Link>
      ))}
    </nav>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col gap-6 py-5">
      <div className="px-4">
        <Link to="/" className="flex items-center gap-2.5" onClick={onNavigate}>
          <BrandMark className="h-9 w-9 drop-shadow-[0_0_12px_color-mix(in_oklch,var(--color-primary)_20%,transparent)]" />
          <span className="leading-tight">
            <span className="block text-sm font-semibold tracking-tight">
              MC-IaaS
            </span>
            <span className="block text-[10px] tracking-widest text-muted-foreground uppercase">
              Control Plane
            </span>
          </span>
        </Link>
      </div>

      <NavLinks {...(onNavigate ? { onNavigate } : {})} />

      <div className="mt-auto px-4">
        <div className="rounded-md border border-sidebar-border bg-sidebar-accent/40 p-3">
          <p className="text-xs font-medium">Mock data mode</p>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
            All values are simulated. Control Plane API integration pending.
          </p>
        </div>
      </div>
    </div>
  );
}

function GlobalIndicator() {
  const { data, isPending } = useQuery(overviewQuery);

  const status = data?.status ?? "operational";
  const tone =
    status === "operational"
      ? "border-success/35 bg-success/10 text-success"
      : status === "degraded"
        ? "border-warning/35 bg-warning/10 text-warning"
        : "border-destructive/35 bg-destructive/10 text-destructive";
  const label =
    status === "operational"
      ? "All systems operational"
      : status === "degraded"
        ? "Infrastructure degraded"
        : "Infrastructure down";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "hidden items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-medium sm:inline-flex",
            tone,
          )}
        >
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-current" />
          </span>
          {isPending ? "Checking…" : label}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        {data
          ? `${data.nodesOnline}/${data.nodesTotal} compute nodes online · ${data.alerts} open invariants`
          : "Aggregating node health"}
      </TooltipContent>
    </Tooltip>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [createOpen, setCreateOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data } = useQuery(overviewQuery);

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-60 shrink-0 border-r border-sidebar-border bg-sidebar lg:block">
        <div className="sticky top-0 h-screen">
          <SidebarContent />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur md:px-6">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                aria-label="Open navigation"
              >
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 bg-sidebar p-0">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <SidebarContent onNavigate={() => setMobileOpen(false)} />
            </SheetContent>
          </Sheet>

          <span className="flex items-center gap-2 text-sm font-semibold tracking-tight lg:hidden">
            <BrandMark className="h-6 w-6" /> MC-IaaS
          </span>

          <div className="ml-auto flex items-center gap-2">
            {!!data?.alerts && (
              <Link
                to="/monitoring"
                className="inline-flex items-center gap-1.5 rounded-md border border-warning/35 bg-warning/10 px-2.5 py-1 text-xs font-medium text-warning"
              >
                <ShieldAlert className="h-3.5 w-3.5" aria-hidden />
                {data.alerts} invariants
              </Link>
            )}
            <GlobalIndicator />
            <span className="hidden items-center gap-1.5 rounded-md border border-border-strong bg-muted/60 px-2.5 py-1 text-xs font-medium text-muted-foreground md:inline-flex">
              <span className="h-1.5 w-1.5 rounded-full bg-info" />
              Development
            </span>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" aria-hidden />
              Create Instance
            </Button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] flex-1 space-y-6 px-4 py-6 md:px-6 md:py-8">
          {children}
        </main>
      </div>

      <CreateInstanceDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
