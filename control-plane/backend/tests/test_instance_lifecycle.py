"""Scheduler and lifecycle requests with fake persistence."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DesiredInstanceState as Desired
from app.models.enums import ObservedInstanceState as Observed
from app.models.enums import OperationStatus
from app.models.enums import OperationType as Kind
from app.models.instance import Instance
from app.schemas.instance import InstanceCreate
from app.services.instance_service import InstanceService, translate_integrity
from app.services.lifecycle_errors import (
    ActiveOperationError,
    InstanceAlreadyExistsError,
    LifecycleError,
    NodeCapacityError,
    NoSchedulableNodeError,
)
from app.services.scheduler import Scheduler


def node(**overrides):
    return SimpleNamespace(
        **{
            **dict(
                id=uuid4(),
                name="node",
                enabled=True,
                reachability="online",
                observed_ready=True,
                last_seen_at=datetime.now(UTC),
                last_observed_at=datetime.now(UTC),
                available_slots=1,
            ),
            **overrides,
        }
    )


@pytest.mark.parametrize(
    "overrides",
    [
        dict(enabled=False),
        dict(reachability="offline"),
        dict(observed_ready=False),
        dict(last_observed_at=None),
        dict(last_observed_at=datetime.now(UTC) - timedelta(hours=1)),
    ],
)
async def test_scheduler_rejects_ineligible(overrides):
    scheduler = Scheduler(AsyncMock(), max_age=60)
    scheduler.nodes = AsyncMock()
    scheduler.nodes.list_enabled.return_value = [node(**overrides)]
    with pytest.raises(NoSchedulableNodeError):
        await scheduler.select_node()


async def test_scheduler_ranking_and_zero_capacity_create():
    scheduler = Scheduler(AsyncMock(), max_age=60)
    scheduler.nodes = AsyncMock()
    nodes = [
        node(name="Z", available_slots=2),
        node(name="A", available_slots=2),
        node(name="unknown", available_slots=None),
    ]
    scheduler.nodes.list_enabled.return_value = nodes
    scheduler.nodes.get_by_id.side_effect = lambda key, **kw: next(n for n in nodes if n.id == key)
    assert (await scheduler.select_node()).name == "A"
    nodes[:] = [node(available_slots=0)]
    assert await scheduler.select_node() is nodes[0]
    with pytest.raises(NodeCapacityError):
        scheduler.validate_start(nodes[0])
    nodes.clear()
    with pytest.raises(NoSchedulableNodeError):
        await scheduler.select_node()


@pytest.fixture
def data():
    return InstanceCreate(name="test-vm", vm_username="operator", accept_eula=True)


@pytest.fixture
def lifecycle():
    session = AsyncMock(spec=AsyncSession)
    service = InstanceService(session)
    service.repository = AsyncMock()
    service.operations = AsyncMock()
    service.nodes = AsyncMock()
    selected = node()
    service.scheduler.select_node = AsyncMock(return_value=selected)
    service.nodes.get_by_id.return_value = selected
    instance = Instance(
        id=uuid4(),
        name="test-vm",
        compute_node_id=selected.id,
        desired_state=Desired.STOPPED,
        observed_state=Observed.STOPPED,
    )
    service.repository.get_by_id.return_value = instance
    service.repository.get_by_name.return_value = None
    service.repository.create.return_value = instance
    service.operations.create.return_value = SimpleNamespace(
        id=uuid4(), instance_id=instance.id, status=OperationStatus.PENDING
    )
    return service, instance


async def test_create_stopped_unknown_pending(lifecycle, data):
    service, instance = lifecycle
    result = await service.create(data)
    fields = service.repository.create.call_args.kwargs
    assert fields["desired_state"] == Desired.STOPPED
    assert fields["observed_state"] == Observed.UNKNOWN
    assert fields["compute_node_id"] == instance.compute_node_id
    assert result.status == OperationStatus.PENDING
    assert service.operations.create.call_args.args[2] == Kind.CREATE
    assert "password" not in str(service.operations.create.call_args)
    service.session.commit.assert_awaited_once()


async def test_duplicate_name_including_tombstone(lifecycle, data):
    service, instance = lifecycle
    service.repository.get_by_name.return_value = instance
    with pytest.raises(InstanceAlreadyExistsError):
        await service.create(data)
    service.scheduler.select_node.assert_not_awaited()
    service.session.rollback.assert_awaited_once()


@pytest.mark.parametrize(
    ("kind", "observed", "desired", "expected"),
    [
        (Kind.START, Observed.STOPPED, Desired.STOPPED, Desired.RUNNING),
        (Kind.STOP, Observed.RUNNING, Desired.RUNNING, Desired.STOPPED),
        (Kind.STOP, Observed.STOPPED, Desired.STOPPED, Desired.STOPPED),
        (Kind.RESTART, Observed.RUNNING, Desired.RUNNING, Desired.RUNNING),
        (Kind.DELETE, Observed.STOPPED, Desired.STOPPED, Desired.ABSENT),
    ],
)
async def test_requests_keep_placement_and_observed_state(
    lifecycle, kind, observed, desired, expected
):
    service, instance = lifecycle
    instance.observed_state, instance.desired_state = observed, desired
    placement = instance.compute_node_id
    await service.request(instance.id, kind)
    assert instance.desired_state == expected
    assert instance.observed_state == observed
    assert instance.compute_node_id == placement
    service.scheduler.select_node.assert_not_awaited()
    service.session.commit.assert_awaited_once()


@pytest.mark.parametrize("kind", [Kind.DELETE, Kind.START])
async def test_running_disallows_delete_and_start(lifecycle, kind):
    service, instance = lifecycle
    instance.observed_state = Observed.RUNNING
    with pytest.raises(LifecycleError):
        await service.request(instance.id, kind)
    service.operations.create.assert_not_awaited()


async def test_active_operation_blocks_before_node_lock(lifecycle):
    service, instance = lifecycle
    service.operations.ensure_idle.side_effect = ActiveOperationError()
    with pytest.raises(ActiveOperationError):
        await service.request(instance.id, Kind.START)
    service.nodes.get_by_id.assert_not_awaited()


@pytest.mark.parametrize(
    "fields",
    [
        dict(memory_mb=511),
        dict(memory_mb=2049),
        dict(vcpus=2),
        dict(name="bad/name"),
        dict(vm_username="root"),
        dict(accept_eula=False),
        dict(compute_node_id=str(uuid4())),
        dict(vm_password="secret"),
        dict(desired_state="running"),
    ],
)
def test_create_schema_rejects_invalid_or_private_fields(fields):
    with pytest.raises(ValidationError):
        InstanceCreate.model_validate(
            dict(name="test-vm", vm_username="operator", accept_eula=True) | fields
        )


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        ("uq_instances_name", InstanceAlreadyExistsError),
        ("uq_operations_active_mutation_per_instance", ActiveOperationError),
        ("unrelated", None),
    ],
)
def test_race_errors_are_specific(constraint, expected):
    from sqlalchemy.exc import IntegrityError

    original = Exception("private database details")
    original.sqlstate = "23505"
    original.constraint_name = constraint
    error = IntegrityError("sql", {}, original)
    with pytest.raises(expected or IntegrityError):
        translate_integrity(error)
