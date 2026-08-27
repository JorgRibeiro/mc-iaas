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

    available_slots = (
        len(available_runtime_slots())
        if invariant_report.healthy
        else 0
    )

    active_instances = (
        MAX_ACTIVE_INSTANCES
        - available_slots
    )

    capacity = NodeCapacity(
        max_active_instances=MAX_ACTIVE_INSTANCES,
        active_instances=active_instances,
        available_slots=available_slots,
    )

    ready = invariant_report.healthy

    node_status = (
        NodeStatus.HEALTHY
        if ready
        else NodeStatus.UNHEALTHY
    )

    return NodeHealthResponse(
        status=node_status,
        ready=ready,
        libvirt=libvirt,
        network=network,
        storage=storage,
        invariants=invariants,
        capacity=capacity,
    )
