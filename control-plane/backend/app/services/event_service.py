"""Domain audit with fixed messages, never Agent payloads or exception strings."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventLevel
from app.models.event import Event
from app.repositories.event_repository import EventRepository

MESSAGES = {
    "node.online": "Node became online",
    "node.offline": "Node became offline",
    "node.orphan_instance.detected": "Unmanaged workloads observed on Node",
    "instance.scheduled": "Instance placement selected",
    "reconciliation.action_created": "Automatic corrective operation queued",
    "reconciliation.blocked": "Reconciliation requires attention",
    "operation.resolved": "Uncertain operation resolved from a subsequent observation",
}
for action in ("create", "start", "stop", "restart", "delete"):
    MESSAGES[f"instance.{action}.requested"] = f"Instance {action} requested"
for state in ("started", "succeeded", "failed", "uncertain"):
    MESSAGES[f"operation.{state}"] = f"Operation {state}"
for state in ("running", "stopped", "missing"):
    MESSAGES[f"instance.observed.{state}"] = f"Instance observed {state}"


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = EventRepository(session)

    def emit(
        self,
        event_type: str,
        *,
        node_id: UUID | None = None,
        instance_id: UUID | None = None,
        operation_id: UUID | None = None,
    ) -> Event:
        message = MESSAGES[event_type]  # Only catalogued events are accepted.
        level = (
            EventLevel.WARNING
            if event_type
            in {
                "node.offline",
                "node.orphan_instance.detected",
                "operation.uncertain",
                "reconciliation.blocked",
            }
            else EventLevel.ERROR
            if event_type == "operation.failed"
            else EventLevel.INFO
        )
        return self.repository.create(
            event_type=event_type,
            component=event_type.split(".")[0],
            level=level,
            message=message,
            node_id=node_id,
            instance_id=instance_id,
            operation_id=operation_id,
        )
