import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Cable, Save } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { ErrorState, TableSkeleton } from "@/components/StateViews";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { settingsQuery, useUpdateSettings } from "@/services/queries";
import type { ControlPlaneSettings } from "@/types";

export const Route = createFileRoute("/settings")({ component: SettingsPage });

function SettingsPage() {
  const settings = useQuery(settingsQuery);
  const update = useUpdateSettings();
  const [form, setForm] = useState<ControlPlaneSettings | null>(null);

  useEffect(() => {
    if (settings.data) setForm(settings.data);
  }, [settings.data]);

  if (settings.isError)
    return (
      <ErrorState
        message={settings.error.message}
        onRetry={() => void settings.refetch()}
      />
    );
  if (settings.isPending || !form) return <TableSkeleton rows={6} />;

  function set<K extends keyof ControlPlaneSettings>(
    key: K,
    value: ControlPlaneSettings[K],
  ) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
  }

  return (
    <>
      <PageHeader
        title="Settings"
        description="Local defaults for this development console. Changes remain in memory for the current process only."
        actions={
          <Button
            size="sm"
            disabled={update.isPending}
            onClick={() => update.mutate(form)}
          >
            <Save className="h-4 w-4" />
            {update.isPending ? "Saving…" : "Save settings"}
          </Button>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(20rem,1fr)]">
        <section className="panel p-5">
          <div className="mb-5">
            <h2 className="text-sm font-medium">Control Plane defaults</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Values used to preconfigure future scheduling and creation flows.
            </p>
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Control Plane name">
              <Input
                value={form.controlPlaneName}
                onChange={(event) =>
                  set("controlPlaneName", event.target.value)
                }
              />
            </Field>
            <Field label="Environment">
              <Select
                value={form.environment}
                onValueChange={(value) =>
                  set(
                    "environment",
                    value as ControlPlaneSettings["environment"],
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="development">Development</SelectItem>
                  <SelectItem value="staging">Staging</SelectItem>
                  <SelectItem value="production">Production</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <NumberField
              label="Refresh interval (seconds)"
              value={form.refreshIntervalSeconds}
              min={5}
              step={5}
              onChange={(value) => set("refreshIntervalSeconds", value)}
            />
            <NumberField
              label="Default memory (MiB)"
              value={form.defaultMemoryMb}
              min={512}
              max={2048}
              step={512}
              onChange={(value) => set("defaultMemoryMb", value)}
            />
            <NumberField
              label="Default vCPU"
              value={form.defaultVcpus}
              min={1}
              max={1}
              onChange={(value) => set("defaultVcpus", value)}
            />
            <NumberField
              label="Max instances per node"
              value={form.maxInstancesPerNode}
              min={1}
              max={4}
              onChange={(value) => set("maxInstancesPerNode", value)}
            />
          </div>
        </section>

        <section className="panel self-start p-5">
          <div className="flex items-start gap-3">
            <span className="rounded-md border border-border bg-muted p-2">
              <Cable className="h-4 w-4 text-muted-foreground" />
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-sm font-medium">API Integration</h2>
                <Badge variant="outline" className="text-muted-foreground">
                  Not configured
                </Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                The Control Plane backend has not been connected yet.
              </p>
            </div>
          </div>
          <div className="mt-5 rounded-md border border-dashed border-border p-3 text-xs leading-relaxed text-muted-foreground">
            The UI currently uses{" "}
            <span className="font-mono text-foreground">
              MockControlPlaneClient
            </span>
            . A future HTTP adapter can replace it at the existing service
            injection point.
          </div>
        </section>
      </div>
    </>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}) {
  return (
    <Field label={label}>
      <Input
        type="number"
        value={value}
        min={min}
        {...(max === undefined ? {} : { max })}
        {...(step === undefined ? {} : { step })}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </Field>
  );
}
