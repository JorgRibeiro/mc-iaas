import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
const CURRENT_MINECRAFT_VERSION = "26.2";
import { useCreateInstance } from "@/services/queries";

const MIN_MEMORY = 512;
const MAX_MEMORY = 2048;

export function CreateInstanceDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const createInstance = useCreateInstance();

  const [name, setName] = useState("");
  const [vmUsername, setVmUsername] = useState("mcadmin");
  const [memoryMb, setMemoryMb] = useState(MAX_MEMORY);
  const [acceptEula, setAcceptEula] = useState(false);

  const nameError =
    name.length > 0 && !/^[a-zA-Z0-9][a-zA-Z0-9_-]{2,49}$/.test(name)
      ? "Use letters, digits, underscores and dashes (3–50 chars)."
      : null;
  const memoryError =
    !Number.isInteger(memoryMb) ||
    memoryMb < MIN_MEMORY ||
    memoryMb > MAX_MEMORY
      ? `Memory must be between ${MIN_MEMORY} and ${MAX_MEMORY} MiB.`
      : null;

  const usernameError =
    !/^[a-z_][a-z0-9_-]{0,31}$/.test(vmUsername) ||
    ["root", "minecraft", "libvirt-qemu"].includes(vmUsername);
  const canSubmit =
    name.length >= 3 &&
    !nameError &&
    !memoryError &&
    acceptEula &&
    !usernameError &&
    !createInstance.isPending;

  function reset() {
    setName("");
    setVmUsername("mcadmin");
    setMemoryMb(MAX_MEMORY);
    setAcceptEula(false);
  }

  function submit() {
    if (!canSubmit) return;
    createInstance.mutate(
      {
        name,
        vmUsername,
        memoryMb,
        vcpus: 1,
        minecraftVersion: CURRENT_MINECRAFT_VERSION,
        acceptEula,
      },
      {
        onSuccess: () => {
          reset();
          onOpenChange(false);
        },
      },
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) reset();
        onOpenChange(next);
      }}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Create instance</DialogTitle>
          <DialogDescription>
            Provisions a Minecraft workload on an available compute node. The
            workload is created stopped; placement is selected automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="inst-name">Instance name</Label>
            <Input
              id="inst-name"
              placeholder="survival-02"
              value={name}
              onChange={(e) => setName(e.target.value)}
              aria-invalid={!!nameError}
            />
            {nameError && (
              <p className="text-xs text-destructive">{nameError}</p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="vm-user">VM username</Label>
              <Input
                id="vm-user"
                value={vmUsername}
                onChange={(e) => setVmUsername(e.target.value)}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Compute node selected automatically by the Scheduler.
            </p>
          </div>
          {usernameError && (
            <p className="text-xs text-destructive">
              Use a valid, non-reserved Linux username (1–32 characters).
            </p>
          )}

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5 sm:col-span-1">
              <Label htmlFor="memory">Memory (MiB)</Label>
              <Input
                id="memory"
                type="number"
                min={MIN_MEMORY}
                max={MAX_MEMORY}
                step={512}
                value={memoryMb}
                onChange={(e) => setMemoryMb(Number(e.target.value))}
                aria-invalid={!!memoryError}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="vcpu">vCPU</Label>
              <Input id="vcpu" value={1} readOnly disabled />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="mcv">Minecraft version</Label>
              <Input
                id="mcv"
                value={CURRENT_MINECRAFT_VERSION}
                readOnly
                disabled
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Limits in this environment: {MIN_MEMORY}–{MAX_MEMORY} MiB memory,
            exactly 1 vCPU, Minecraft {CURRENT_MINECRAFT_VERSION}.
          </p>
          {memoryError && (
            <p className="text-xs text-destructive">{memoryError}</p>
          )}

          <Separator />

          <label className="flex cursor-pointer items-start gap-2.5 rounded-md border border-border px-3 py-2.5">
            <Checkbox
              id="eula"
              checked={acceptEula}
              onCheckedChange={(v) => setAcceptEula(v === true)}
              className="mt-0.5"
            />
            <span className="text-sm">
              Accept the Minecraft EULA
              <span className="block text-xs text-muted-foreground">
                Required before the workload can be provisioned.
              </span>
            </span>
          </label>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!canSubmit}>
            {createInstance.isPending ? "Creating…" : "Create instance"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
