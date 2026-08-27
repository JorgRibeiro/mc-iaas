from jorge_agent.config import (
    MAX_ACTIVE_INSTANCES,
)

from jorge_agent.schemas.node import (
    NodeCapacity,
    NodeComponentHealth,
    NodeHealthResponse,
    NodeStatus,
)

from jorge_agent.services.invariant_service import (
    InvariantIssue,
    check_invariants,
)

from jorge_agent.schemas.instance import (
    InstanceState,
)

from jorge_agent.services.libvirt_service import (
    list_instances,
)

from jorge_agent.services.runtime_service import (
    available_runtime_slots,
)


def _issues_for_prefixes(
    issues: list[InvariantIssue],
    prefixes: tuple[str, ...],
) -> list[InvariantIssue]:
    return [
        issue
        for issue in issues
        if issue.code.startswith(prefixes)
    ]


def _component_from_issues(
    issues: list[InvariantIssue],
) -> NodeComponentHealth:
    if not issues:
        return NodeComponentHealth(
            healthy=True,
            detail=None,
        )

    detail = "; ".join(
        f"{issue.code}: {issue.detail}"
        for issue in issues
    )

    return NodeComponentHealth(
        healthy=False,
        detail=detail,
    )


def get_node_health() -> NodeHealthResponse:
    invariant_report = check_invariants()

    issues = invariant_report.issues

    libvirt_issues = _issues_for_prefixes(
        issues,
        (
            "libvirt_",
        ),
    )

    network_issues = _issues_for_prefixes(
        issues,
        (
            "network_",
            "rcon_",
        ),
    )

    storage_issues = _issues_for_prefixes(
        issues,
        (
            "pool_",
            "base_image_",
        ),
    )

    libvirt = _component_from_issues(
        libvirt_issues
    )

    network = _component_from_issues(
        network_issues
    )

    storage = _component_from_issues(
        storage_issues
    )

    invariants = _component_from_issues(
        issues
    )

    ready = not invariant_report.has_critical

    # Capacidade física observada no runtime.
    actual_available_slots = len(
        available_runtime_slots()
    )

    occupied_runtime_slots = (
        MAX_ACTIVE_INSTANCES
        - actual_available_slots
    )

    # Quantidade real de instâncias ativas.
    instances = list_instances()

    active_instances = sum(
        1
        for instance in instances
        if instance.state
        in {
            InstanceState.RUNNING,
            InstanceState.PAUSED,
        }
    )

    # Se o nó estiver inconsistente, não anunciamos
    # capacidade utilizável ao scheduler, mesmo que
    # fisicamente ainda existam slots livres.
    available_slots = (
        actual_available_slots
        if ready
        else 0
    )

    capacity = NodeCapacity(
        max_active_instances=MAX_ACTIVE_INSTANCES,
        active_instances=active_instances,
        occupied_runtime_slots=occupied_runtime_slots,
        available_slots=available_slots,
    )

    if invariant_report.has_critical:
        node_status = NodeStatus.UNHEALTHY

    elif invariant_report.has_warnings:
        node_status = NodeStatus.DEGRADED

    else:
        node_status = NodeStatus.HEALTHY

    return NodeHealthResponse(
        status=node_status,
        ready=ready,
        libvirt=libvirt,
        network=network,
        storage=storage,
        invariants=invariants,
        capacity=capacity,
    )
