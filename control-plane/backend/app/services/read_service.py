"""Current-state projections; no invented telemetry or UI state persistence."""

from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.operation import Operation
from app.repositories.instance_repository import InstanceRepository
from app.repositories.node_repository import NodeRepository
from app.schemas.instance import ActiveOperationSummary, InstanceResponse
from app.schemas.node import ComputeNodeResponse
from app.services.operation_service import ACTIVE, MUTATIONS


def unavailable(node) -> bool:
    if node is None or node.reachability != "online" or node.last_seen_at is None:
        return True
    return (
        datetime.now(UTC) - node.last_seen_at
    ).total_seconds() > get_settings().node_observation_max_age


def display_state(instance, node, operation=None) -> str:
    if unavailable(node):
        return "unavailable"
    if operation is not None:
        if operation.status == "uncertain":
            return "uncertain"
        return {
            "create": "creating",
            "start": "starting",
            "stop": "stopping",
            "restart": "restarting",
            "delete": "deleting",
        }.get(operation.type, "unknown")
    return str(instance.observed_state)


class ReadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def render_instances(self, instances) -> list[InstanceResponse]:
        if not instances:
            return []
        node_map = {node.id: node for node in await NodeRepository(self.session).list_all()}
        operations = await self.session.scalars(
            select(Operation).where(
                Operation.instance_id.in_([instance.id for instance in instances]),
                or_(
                    and_(Operation.status.in_(ACTIVE), Operation.type.in_(MUTATIONS)),
                    Operation.type == "create",
                ),
            )
        )
        operations = list(operations.all())
        active = {
            operation.instance_id: operation
            for operation in operations
            if operation.status in ACTIVE
        }
        usernames = {
            operation.instance_id: operation.operation_metadata.get("vm_username")
            for operation in operations
            if operation.type == "create"
        }
        result = []
        for instance in instances:
            operation = active.get(instance.id)
            response = InstanceResponse.model_validate(instance)
            response.vm_username = usernames.get(instance.id)
            response.display_state = display_state(
                instance, node_map.get(instance.compute_node_id), operation
            )
            response.active_operation = (
                ActiveOperationSummary.model_validate(operation) if operation else None
            )
            result.append(response)
        return result

    async def summary(self) -> dict:
        nodes = await NodeRepository(self.session).list_all()
        instances = await InstanceRepository(self.session).list_all()
        node_map = {node.id: node for node in nodes}
        conditions = []
        for node in nodes:
            if unavailable(node) or node.observed_health == "unhealthy":
                conditions.append(
                    {
                        "code": "node.unavailable_or_unhealthy",
                        "node_id": node.id,
                        "instance_id": None,
                    }
                )
        for instance in instances:
            if instance.last_error and instance.last_error.startswith("reconciliation: "):
                conditions.append(
                    {
                        "code": "reconciliation.blocked",
                        "node_id": instance.compute_node_id,
                        "instance_id": instance.id,
                    }
                )

        uncertain = await self.session.scalars(
            select(Operation).where(Operation.status == "uncertain")
        )
        for operation in uncertain.all():
            conditions.append(
                {
                    "code": "operation.uncertain",
                    "node_id": operation.node_id,
                    "instance_id": operation.instance_id,
                }
            )

        def total(field):
            values = [getattr(node, field) for node in nodes]
            return sum(values) if all(value is not None for value in values) else None

        online = sum(node.reachability == "online" for node in nodes)
        usable_count = sum(not unavailable(node) for node in nodes)
        status = (
            "down"
            if not usable_count
            else "degraded"
            if (conditions or any(node.observed_health != "healthy" for node in nodes))
            else "operational"
        )
        capacity = {
            "total_runtime_slots": total("max_active_instances"),
            "occupied_runtime_slots": total("occupied_runtime_slots"),
            "available_runtime_slots": total("available_slots"),
        }
        now = datetime.now(UTC)
        metric_nodes = [
            node
            for node in nodes
            if not unavailable(node)
            and node.metrics_observed_at is not None
            and (now - node.metrics_observed_at).total_seconds()
            <= get_settings().node_observation_max_age
        ]
        cpu = [
            node.cpu_usage_percent for node in metric_nodes if node.cpu_usage_percent is not None
        ]
        metrics = {"cpu_usage_percent": sum(cpu) / len(cpu) if cpu else None}
        for resource in ("memory", "storage"):
            # Sum matched used/total pairs, never a partial denominator.
            pairs = [
                (getattr(node, f"{resource}_used_bytes"), getattr(node, f"{resource}_total_bytes"))
                for node in metric_nodes
            ]
            pairs = [
                (used, total) for used, total in pairs if used is not None and total is not None
            ]
            metrics[f"{resource}_used_bytes"] = sum(p[0] for p in pairs) if pairs else None
            metrics[f"{resource}_total_bytes"] = sum(p[1] for p in pairs) if pairs else None
        overview = {
            **metrics,
            "infrastructure_status": status,
            "total_nodes": len(nodes),
            "online_nodes": online,
            "healthy_nodes": sum(node.observed_health == "healthy" for node in nodes),
            "total_instances": len(instances),
            "running_instances": sum(
                instance.observed_state == "running" for instance in instances
            ),
            "stopped_instances": sum(
                instance.observed_state == "stopped" for instance in instances
            ),
            "unavailable_instances": sum(
                unavailable(node_map.get(instance.compute_node_id)) for instance in instances
            ),
            **capacity,
            "open_critical_conditions": len(conditions),
        }
        return {
            "overview": overview,
            "node_health_distribution": dict(Counter(str(node.observed_health) for node in nodes)),
            "instance_state_distribution": dict(
                Counter(str(instance.observed_state) for instance in instances)
            ),
            "capacity": capacity,
            "conditions": conditions,
            "nodes": [ComputeNodeResponse.from_node(node) for node in nodes],
            "historical_metrics_available": False,
            "timeseries": [],
        }
