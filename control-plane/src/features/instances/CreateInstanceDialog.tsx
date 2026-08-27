import { useQuery } from "@tanstack/react-query";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { CURRENT_MINECRAFT_VERSION } from "@/mocks/instances";
import { nodesQuery, useCreateInstance } from "@/services/queries";

const MIN_MEMORY = 512;
const MAX_MEMORY = 2048;

export function CreateInstanceDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: nodes = [] } = useQuery(nodesQuery);
  const createInstance = useCreateInstance();

  const [name, setName] = useState("");
  const [vmUsername, setVmUsername] = useState("mcadmin");
  const [memoryMb, setMemoryMb] = useState(MAX_MEMORY);
  const [computeNodeId, setComputeNodeId] = useState("");
  const [acceptEula, setAcceptEula] = useState(false);
  const [autoPassword, setAutoPassword] = useState(true);

  const eligibleNodes = nodes.filter((n) => n.ready);
  const selectedNode = computeNodeId || eligibleNodes[0]?.id || "";

  const nameError =
    name.length > 0 && !/^[a-z0-9][a-z0-9-]{1,30}$/.test(name)
      ? "Use lowercase letters, digits and dashes (2–31 chars)."
      : null;
  const memoryError =
    memoryMb < MIN_MEMORY || memoryMb > MAX_MEMORY
      ? `Memory must be between ${MIN_MEMORY} and ${MAX_MEMORY} MiB.`
      : null;

  const canSubmit =
    name.length > 1 && !nameError && !memoryError && acceptEula && !!selectedNode && !createInstance.isPending;

  function reset() {
    setName("");
    setVmUsername("mcadmin");
    setMemoryMb(MAX_MEMORY);
    setComputeNodeId("");
    setAcceptEula(false);
    setAutoPassword(true);
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
        autogeneratePassword: autoPassword,
        computeNodeId: selectedNode,
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
            Provisions a Minecraft workload on an available compute node. This build simulates
            creation locally.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="inst-name">Instance name</Label>
            <Input
              id="inst-name"
              placeholder="survival-02"
              value={name}
              onChange={(e) => setName(e.target.value.toLowerCase())}
              aria-invalid={!!nameError}
            />
            {nameError && <p className="text-xs text-destructive">{nameError}</p>}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="vm-user">VM username</Label>
              <Input id="vm-user" value={vmUsername} onChange={(e) => setVmUsername(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="node">Compute node</Label>
              <Select value={selectedNode} onValueChange={setComputeNodeId}>
                <SelectTrigger id="node">
                  <SelectValue placeholder="Select node" />
                </SelectTrigger>
                <SelectContent>
                  {eligibleNodes.map((node) => (
                    <SelectItem key={node.id} value={node.id}>
                      {node.name} · {node.capacity.availableSlots} slots free
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

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
              <Input id="mcv" value={CURRENT_MINECRAFT_VERSION} readOnly disabled />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Limits in this environment: {MIN_MEMORY}–{MAX_MEMORY} MiB memory, exactly 1 vCPU, Minecraft{" "}
            {CURRENT_MINECRAFT_VERSION}.
          </p>
          {memoryError && <p className="text-xs text-destructive">{memoryError}</p>}

          <Separator />

          <div className="flex items-center justify-between gap-4 rounded-md border border-border bg-surface/60 px-3 py-2.5">
            <div className="space-y-0.5">
              <Label htmlFor="autopass" className="text-sm">
                Autogenerated VM password
              </Label>
              <p className="text-xs text-muted-foreground">
                Credentials are never displayed or stored by the console.
              </p>
            </div>
            <Switch id="autopass" checked={autoPassword} onCheckedChange={setAutoPassword} />
          </div>

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
