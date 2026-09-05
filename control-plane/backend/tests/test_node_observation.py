"""Observation rules and transaction handling with no external dependencies."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.compute_agent import ComputeAgentClient
from app.clients.errors import (
    AgentAuthenticationError,
    AgentCredentialUnavailableError,
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
)
from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability
from app.schemas.agent import AgentSnapshot
from app.secrets.provider import SecretProvider
from app.services.node_observation_service import NodeObservationService
from app.services.node_service import NodeNotFoundError


@pytest.fixture
def observation():
    old_time = datetime(2026, 1, 1, tzinfo=UTC)
    node = ComputeNode(
        id=uuid4(),
        name="test",
        endpoint="http://agent.test",
        credential_ref="test-agent",
        enabled=True,
        reachability=NodeReachability.ONLINE,
        observed_health=NodeHealth.DEGRADED,
        observed_ready=False,
        max_active_instances=4,
        active_instances=2,
        occupied_runtime_slots=3,
        available_slots=1,
        consecutive_failures=3,
        last_seen_at=old_time,
        last_observed_at=old_time,
        agent_version="old",
        last_error="previous failure",
        created_at=old_time,
        updated_at=old_time,
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = node
    client = AsyncMock(spec=ComputeAgentClient)
    client.get_snapshot.return_value = AgentSnapshot.model_validate(
        {
            "generated_at": "2026-09-05T12:00:00Z",
            "agent": {"version": "0.1.0"},
            "node_health": {
                "status": "healthy",
                "ready": True,
                "capacity": {
                    "max_active_instances": 4,
                    "active_instances": 1,
                    "occupied_runtime_slots": 1,
                    "available_slots": 3,
                },
            },
            "errors": {},
        }
    )
    secrets = Mock(spec=SecretProvider)
    secrets.get_agent_token.return_value = "test-secret"
    return NodeObservationService(session, client, secrets, offline_threshold=30), node


async def test_complete_snapshot_and_lock(observation):
    service, node = observation
    before = datetime.now(UTC)
    assert await service.refresh_node(node.id) is node
    assert node.reachability == NodeReachability.ONLINE
    assert node.observed_health == NodeHealth.HEALTHY
    assert node.observed_ready is True
    assert (
        node.max_active_instances,
        node.active_instances,
        node.occupied_runtime_slots,
        node.available_slots,
    ) == (4, 1, 1, 3)
    assert node.last_seen_at >= before
    assert node.last_observed_at == node.last_seen_at
    assert node.agent_version == "0.1.0"
    assert node.consecutive_failures == 0
    assert node.last_error is None
    service.secrets.get_agent_token.assert_called_once_with("test-agent")
    service.client.get_snapshot.assert_awaited_once_with(node.endpoint, "test-secret")
    service.session.commit.assert_awaited_once()
    statement = service.session.scalar.call_args.args[0]
    assert str(statement.compile(dialect=postgresql.dialect())).endswith("FOR UPDATE")


async def test_partial_preserves_known_health(observation):
    service, node = observation
    snapshot = service.client.get_snapshot.return_value
    snapshot.node_health = None
    snapshot.errors = {"node_health": "test-secret sensitive remote error"}
    old_observation = node.last_observed_at
    await service.refresh_node(node.id)
    assert node.reachability == NodeReachability.ONLINE
    assert node.observed_health == NodeHealth.DEGRADED
    assert node.observed_ready is False
    assert (
        node.max_active_instances,
        node.active_instances,
        node.occupied_runtime_slots,
        node.available_slots,
    ) == (4, 2, 3, 1)
    assert node.last_observed_at == old_observation
    assert node.last_seen_at > old_observation
    assert node.agent_version == "0.1.0"
    assert node.consecutive_failures == 0
    assert node.last_error == "Partial Agent snapshot"


@pytest.mark.parametrize("section", ["node_metrics", "instances"])
async def test_other_partial_sections_do_not_prevent_health_update(observation, section):
    service, node = observation
    service.client.get_snapshot.return_value.errors = {section: "private error"}
    await service.refresh_node(node.id)
    assert node.reachability == NodeReachability.ONLINE
    assert node.observed_health == NodeHealth.HEALTHY
    assert node.available_slots == 3
    assert node.last_error == "Partial Agent snapshot"


@pytest.mark.parametrize(
    "error",
    [
        AgentTimeoutError,
        AgentUnavailableError,
        AgentAuthenticationError,
        AgentResponseError,
        AgentCredentialUnavailableError,
    ],
)
async def test_failed_refresh_persists_error_and_preserves_state(observation, error, caplog):
    service, node = observation
    before = {
        field: getattr(node, field)
        for field in [
            "reachability",
            "observed_health",
            "observed_ready",
            "max_active_instances",
            "active_instances",
            "occupied_runtime_slots",
            "available_slots",
            "last_seen_at",
            "last_observed_at",
            "agent_version",
        ]
    }
    if error is AgentCredentialUnavailableError:
        service.secrets.get_agent_token.side_effect = error()
    else:
        service.client.get_snapshot.side_effect = error()
    with pytest.raises(error):
        await service.refresh_node(node.id)
    assert before == {field: getattr(node, field) for field in before}
    assert node.consecutive_failures == 4
    assert node.last_error == error.message
    assert "test-secret" not in caplog.text
    service.session.commit.assert_awaited_once()
    service.session.rollback.assert_not_awaited()
    if error is AgentCredentialUnavailableError:
        service.client.get_snapshot.assert_not_awaited()


async def test_missing_node_does_not_contact_agent(observation):
    service, _ = observation
    service.session.scalar.return_value = None
    with pytest.raises(NodeNotFoundError):
        await service.refresh_node(uuid4())
    service.client.get_snapshot.assert_not_awaited()
    service.secrets.get_agent_token.assert_not_called()
    service.session.commit.assert_not_awaited()


async def test_disabled_node_can_be_probed_manually(observation):
    service, node = observation
    node.enabled = False
    await service.refresh_node(node.id)
    assert node.enabled is False
    assert node.observed_health == NodeHealth.HEALTHY


async def test_database_failure_rolls_back(observation):
    service, node = observation
    service.session.commit.side_effect = RuntimeError("database write failed")
    with pytest.raises(RuntimeError):
        await service.refresh_node(node.id)
    service.session.rollback.assert_awaited_once()


async def test_offline_threshold_and_recovery_preserve_observations(observation, caplog):
    service, node = observation
    service.offline_threshold = 2
    node.consecutive_failures = 0
    old_time = node.last_seen_at
    service.client.get_snapshot.side_effect = AgentTimeoutError()
    with caplog.at_level("INFO"):
        for count in (1, 2, 3):
            with pytest.raises(AgentTimeoutError):
                await service.refresh_node(node.id)
            assert node.consecutive_failures == count
            assert node.reachability == (
                NodeReachability.ONLINE if count == 1 else NodeReachability.OFFLINE
            )
            assert node.observed_health == NodeHealth.DEGRADED
            assert node.observed_ready is False
            assert node.available_slots == 1
            assert node.last_seen_at == old_time
        service.client.get_snapshot.side_effect = None
        await service.refresh_node(node.id)
        await service.refresh_node(node.id)
    assert node.reachability == NodeReachability.ONLINE
    assert node.consecutive_failures == 0
    assert node.last_error is None
    assert sum(record.message.startswith("node.offline ") for record in caplog.records) == 1
    assert sum(record.message.startswith("node.online ") for record in caplog.records) == 1


async def test_disabled_after_discovery_is_not_polled(observation):
    service, node = observation
    node.enabled = False
    await service.refresh_node(node.id, enabled_only=True)
    service.client.get_snapshot.assert_not_awaited()
    service.session.commit.assert_not_awaited()


async def test_cancelled_observation_rolls_back(observation):
    import asyncio

    service, node = observation
    service.client.get_snapshot.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await service.refresh_node(node.id)
    service.session.rollback.assert_awaited_once()
    service.session.commit.assert_not_awaited()


@pytest.fixture
def instance_sync(observation):
    from app.models.enums import DesiredInstanceState, MinecraftStatus, ObservedInstanceState
    from app.models.instance import Instance
    from app.repositories.instance_repository import InstanceRepository

    service, node = observation
    instance = Instance(
        id=uuid4(),
        name="known",
        compute_node_id=node.id,
        desired_state=DesiredInstanceState.STOPPED,
        observed_state=ObservedInstanceState.RUNNING,
        observed_runtime_slot=2,
        observed_runtime_ip="10.0.0.2",
        observed_external_port=25566,
        minecraft_status=MinecraftStatus.ONLINE,
        last_observed_at=node.last_observed_at,
        last_error="unrelated lifecycle error",
    )
    service.instances = AsyncMock(spec=InstanceRepository)
    service.instances.list_by_node.return_value = [instance]
    return service, node, instance


@pytest.mark.parametrize(
    "state",
    [
        "running",
        "stopped",
        "paused",
        "missing",
        "unknown",
        "starting",
        "stopping",
        "error",
        "future-state",
    ],
)
async def test_instance_state_runtime_and_desired_state(instance_sync, state):
    from app.schemas.agent import AgentInstance

    service, node, instance = instance_sync
    service.client.get_snapshot.return_value.instances = [
        AgentInstance.model_validate(
            {
                "name": "known",
                "state": state,
                "runtime": {"slot": 1, "ip": "10.0.0.1", "external_port": 25565},
                "minecraft_status": "offline",
            }
        )
    ]
    await service.refresh_node(node.id)
    assert instance.observed_state.value == (
        state if state in {"running", "stopped", "paused", "missing", "unknown"} else "unknown"
    )
    assert instance.desired_state.value == "stopped"
    assert instance.observed_runtime_slot == 1
    assert instance.observed_runtime_ip == "10.0.0.1"
    assert instance.observed_external_port == 25565
    assert instance.minecraft_status.value == "offline"
    assert instance.last_observed_at == node.last_seen_at
    assert instance.last_error == "unrelated lifecycle error"
    service.instances.flush.assert_awaited_once()


async def test_missing_in_complete_inventory(instance_sync):
    service, node, instance = instance_sync
    service.client.get_snapshot.return_value.instances = []
    await service.refresh_node(node.id)
    assert instance.observed_state.value == "missing"
    assert instance.observed_runtime_slot is None
    assert instance.observed_runtime_ip is None
    assert instance.observed_external_port is None
    assert instance.desired_state.value == "stopped"
    assert instance.last_observed_at == node.last_seen_at


@pytest.mark.parametrize("inventory", [None, []])
async def test_partial_inventory_preserves_instances(instance_sync, inventory):
    service, node, instance = instance_sync
    before = instance.last_observed_at
    snapshot = service.client.get_snapshot.return_value
    snapshot.instances = inventory
    snapshot.errors = {"instances": "private remote error"}
    await service.refresh_node(node.id)
    assert instance.observed_state.value == "running"
    assert instance.observed_runtime_slot == 2
    assert instance.last_observed_at == before
    service.instances.list_by_node.assert_not_awaited()


async def test_health_partial_still_syncs_instances_and_detects_orphan(instance_sync, caplog):
    from app.schemas.agent import AgentInstance

    service, node, instance = instance_sync
    snapshot = service.client.get_snapshot.return_value
    snapshot.node_health = None
    snapshot.errors = {"node_health": "private error"}
    snapshot.instances = [
        AgentInstance(name="known", state="stopped"),
        AgentInstance(name="private-orphan-name", state="running"),
    ]
    await service.refresh_node(node.id)
    assert node.reachability == NodeReachability.ONLINE
    assert node.observed_health == NodeHealth.DEGRADED
    assert instance.observed_state.value == "stopped"
    assert instance.observed_runtime_slot is None
    assert instance.minecraft_status.value == "online"  # No Minecraft status in real summary.
    assert "node.orphan_instance.detected" in caplog.text
    assert "private-orphan-name" not in caplog.text
    from app.models.event import Event

    assert all(isinstance(call.args[0], Event) for call in service.session.add.call_args_list)


async def test_offline_does_not_erase_instance_state(instance_sync):
    service, node, instance = instance_sync
    service.offline_threshold = 1
    service.client.get_snapshot.side_effect = AgentUnavailableError()
    before = instance.last_observed_at
    with pytest.raises(AgentUnavailableError):
        await service.refresh_node(node.id)
    assert node.reachability == NodeReachability.OFFLINE
    assert instance.observed_state.value == "running"
    assert instance.last_observed_at == before
    service.instances.list_by_node.assert_not_awaited()
