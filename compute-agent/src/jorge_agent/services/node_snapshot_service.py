from datetime import (
    datetime,
    timezone,
)

from jorge_agent.schemas.snapshot import (
    NodeSnapshotResponse,
    SnapshotInstanceResponse,
)

from jorge_agent.services.agent_status_service import (
    get_agent_status,
)

from jorge_agent.services.host_metrics_service import (
    get_host_metrics,
)

from jorge_agent.services.libvirt_service import (
    list_instances,
)

from jorge_agent.services.node_health_service import (
    get_node_health,
)


from jorge_agent.services.health_service import observe_minecraft_status


def get_node_snapshot() -> NodeSnapshotResponse:
    errors: dict[str, str] = {}

    agent = get_agent_status()

    node_health = None
    node_metrics = None
    instances = None

    try:
        node_health = get_node_health()

    except Exception as exc:
        errors["node_health"] = (
            f"{type(exc).__name__}: {exc}"
        )

    try:
        node_metrics = get_host_metrics()

    except Exception as exc:
        errors["node_metrics"] = (
            f"{type(exc).__name__}: {exc}"
        )

    try:
        instances = []
        for instance in list_instances():
            try:
                minecraft_status = observe_minecraft_status(instance.state, instance.runtime)
            except Exception:
                # A health probe must not discard an otherwise authoritative inventory.
                minecraft_status = "unknown"
            instances.append(SnapshotInstanceResponse(
                **instance.model_dump(), minecraft_status=minecraft_status
            ))

    except Exception as exc:
        errors["instances"] = (
            f"{type(exc).__name__}: {exc}"
        )

    return NodeSnapshotResponse(
        generated_at=datetime.now(
            timezone.utc
        ),
        agent=agent,
        node_health=node_health,
        node_metrics=node_metrics,
        instances=instances,
        errors=errors,
    )
