"""Conservative reconciliation, freshness evidence and bounded automatic attempts."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reconciler import Reconciler


@pytest.fixture
def reconciliation():
    session = AsyncMock(spec=AsyncSession)
    service = Reconciler(session, retry_limit=2)
    service.instances = AsyncMock()
    service.nodes = AsyncMock()
    service.operations = AsyncMock()
    service.events = Mock()
    now = datetime.now(UTC)
    node = SimpleNamespace(
        id=uuid4(),
        enabled=True,
        reachability="online",
        observed_ready=True,
        last_seen_at=now,
        last_observed_at=now,
        available_slots=1,
    )
    instance = SimpleNamespace(
        id=uuid4(),
        compute_node_id=node.id,
        desired_state="running",
        observed_state="stopped",
        last_observed_at=now,
        last_error=None,
        deleted_at=None,
    )
    service.instances.get_by_id.return_value = instance
    service.nodes.get_by_id.return_value = node
    session.scalar.side_effect = [None, None, 0]  # active operation, automatic attempt count
    return service, session, instance, node


@pytest.mark.parametrize(
    ("desired", "observed", "kind"),
    [
        ("running", "running", None),
        ("stopped", "stopped", None),
        ("absent", "missing", None),
        ("running", "stopped", "start"),
        ("stopped", "running", "stop"),
        ("absent", "stopped", "delete"),
    ],
)
async def test_matrix(reconciliation, desired, observed, kind):
    service, _, instance, _ = reconciliation
    instance.desired_state, instance.observed_state = desired, observed
    await service.reconcile(instance.id)
    if kind:
        assert service.operations.create.call_args.args[2] == kind
        assert service.operations.create.call_args.args[3] == {"source": "reconciler"}
    else:
        service.operations.create.assert_not_awaited()
    assert instance.desired_state == desired
    assert instance.observed_state == observed


@pytest.mark.parametrize(
    ("desired", "observed"),
    [("absent", "running"), ("running", "missing"), ("stopped", "missing"), ("running", "paused")],
)
async def test_unsafe_divergence_blocks_once(reconciliation, desired, observed):
    service, session, instance, _ = reconciliation
    instance.desired_state, instance.observed_state = desired, observed
    session.scalar.side_effect = None
    session.scalar.return_value = None
    await service.reconcile(instance.id)
    await service.reconcile(instance.id)
    service.operations.create.assert_not_awaited()
    assert instance.last_error.startswith("reconciliation:")
    assert service.events.emit.call_count == 1


@pytest.mark.parametrize("reason", ["offline", "not_ready", "unknown", "old", "startup"])
async def test_waits_for_safe_observation(reconciliation, reason):
    service, _, instance, node = reconciliation
    if reason == "offline":
        node.reachability = "offline"
    elif reason == "not_ready":
        node.observed_ready = False
    elif reason == "unknown":
        instance.observed_state = "unknown"
    elif reason == "old":
        instance.last_observed_at -= timedelta(hours=1)
    else:
        service.observed_after = instance.last_observed_at + timedelta(seconds=1)
    await service.reconcile(instance.id)
    service.operations.create.assert_not_awaited()


@pytest.mark.parametrize("status", ["pending", "in_progress"])
async def test_active_prevents_second_command(reconciliation, status):
    service, session, instance, _ = reconciliation
    session.scalar.side_effect = None
    session.scalar.return_value = SimpleNamespace(status=status)
    await service.reconcile(instance.id)
    service.operations.create.assert_not_awaited()


async def test_retry_budget_exhaustion(reconciliation):
    service, session, instance, _ = reconciliation
    session.scalar.side_effect = [None, None, 2]
    await service.reconcile(instance.id)
    service.operations.create.assert_not_awaited()
    assert instance.last_error == "reconciliation: Automatic retry budget exhausted"
    session.commit.assert_awaited_once()


@pytest.mark.parametrize(
    ("kind", "observed", "expected"),
    [
        ("start", "running", "succeeded"),
        ("start", "stopped", "failed"),
        ("stop", "stopped", "succeeded"),
        ("delete", "missing", "succeeded"),
        ("create", "stopped", "succeeded"),
        ("create", "running", "succeeded"),
        ("restart", "running", "uncertain"),
    ],
)
async def test_uncertain_evidence(reconciliation, kind, observed, expected):
    service, session, instance, _ = reconciliation
    instance.observed_state = observed
    operation = SimpleNamespace(
        id=uuid4(),
        type=kind,
        status="uncertain",
        completed_at=instance.last_observed_at - timedelta(seconds=1),
    )
    session.scalar.side_effect = None
    session.scalar.return_value = operation
    await service.reconcile(instance.id)
    assert operation.status == expected
    service.operations.create.assert_not_awaited()
    if kind == "delete":
        assert instance.deleted_at is not None
    if kind == "restart":
        assert "cannot be proven" in instance.last_error


async def test_old_evidence_cannot_resolve_uncertain(reconciliation):
    service, session, instance, _ = reconciliation
    instance.observed_state = "running"
    operation = SimpleNamespace(
        id=uuid4(),
        type="start",
        status="uncertain",
        completed_at=instance.last_observed_at + timedelta(seconds=1),
    )
    session.scalar.side_effect = None
    session.scalar.return_value = operation
    await service.reconcile(instance.id)
    assert operation.status == "uncertain"
    service.events.emit.assert_not_called()


async def test_failed_create_is_not_adopted(reconciliation):
    from app.services.lifecycle_errors import LifecycleError

    service, _, instance, _ = reconciliation
    service.operations.ensure_owned.side_effect = LifecycleError()
    await service.reconcile(instance.id)
    service.operations.create.assert_not_awaited()
    assert "ownership" in instance.last_error


async def test_new_attempt_requires_new_observation(reconciliation):
    service, session, instance, _ = reconciliation
    session.scalar.side_effect = [None, instance.last_observed_at + timedelta(seconds=1)]
    await service.reconcile(instance.id)
    service.operations.create.assert_not_awaited()
