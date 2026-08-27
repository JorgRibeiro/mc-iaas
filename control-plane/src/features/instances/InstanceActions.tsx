import { useNavigate } from "@tanstack/react-router";
import { MoreHorizontal, Play, RotateCcw, Square, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useInstanceAction } from "@/services/queries";
import type { Instance } from "@/types";

type Destructive = "restart" | "delete" | null;

export function InstanceActions({
  instance,
  variant = "menu",
}: {
  instance: Instance;
  variant?: "menu" | "buttons";
}) {
  const action = useInstanceAction();
  const navigate = useNavigate();
  const [confirm, setConfirm] = useState<Destructive>(null);

  const disabled = action.isPending || instance.state === "deleting";
  const canStart = instance.state === "stopped";
  const canStop = instance.state === "running" || instance.state === "starting";

  function run(kind: "start" | "stop" | "restart" | "delete") {
    action.mutate({ action: kind, id: instance.id, name: instance.name });
  }

  const confirmCopy =
    confirm === "delete"
      ? {
          title: `Delete ${instance.name}?`,
          description:
            "The instance, its runtime allocation and persistent storage would be removed permanently. This is simulated in the mock adapter.",
          cta: "Delete instance",
        }
      : {
          title: `Restart ${instance.name}?`,
          description:
            "Players connected to this workload would be disconnected while the instance restarts.",
          cta: "Restart instance",
        };

  return (
    <>
      {variant === "buttons" ? (
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="outline" disabled={disabled || !canStart} onClick={() => run("start")}>
            <Play className="h-3.5 w-3.5" /> Start
          </Button>
          <Button size="sm" variant="outline" disabled={disabled || !canStop} onClick={() => run("stop")}>
            <Square className="h-3.5 w-3.5" /> Stop
          </Button>
          <Button size="sm" variant="outline" disabled={disabled} onClick={() => setConfirm("restart")}>
            <RotateCcw className="h-3.5 w-3.5" /> Restart
          </Button>
          <Button size="sm" variant="destructive" disabled={disabled} onClick={() => setConfirm("delete")}>
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </Button>
        </div>
      ) : (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label={`Actions for ${instance.name}`}>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem
              onClick={() =>
                void navigate({ to: "/instances/$instanceId", params: { instanceId: instance.id } })
              }
            >
              Open details
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem disabled={disabled || !canStart} onClick={() => run("start")}>
              <Play className="h-3.5 w-3.5" /> Start
            </DropdownMenuItem>
            <DropdownMenuItem disabled={disabled || !canStop} onClick={() => run("stop")}>
              <Square className="h-3.5 w-3.5" /> Stop
            </DropdownMenuItem>
            <DropdownMenuItem disabled={disabled} onClick={() => setConfirm("restart")}>
              <RotateCcw className="h-3.5 w-3.5" /> Restart
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              disabled={disabled}
              onClick={() => setConfirm("delete")}
            >
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      <AlertDialog open={confirm !== null} onOpenChange={(open) => !open && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmCopy.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmCopy.description}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (confirm) run(confirm);
                setConfirm(null);
              }}
            >
              {confirmCopy.cta}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
