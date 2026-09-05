"""Snapshot health probes without libvirt, real VMs or network access."""

from datetime import datetime, timezone
import sys
from unittest.mock import Mock, MagicMock

# libvirt is an optional compute dependency, unnecessary for these isolated probes.
if "libvirt" not in sys.modules:
    try:
        import libvirt  # noqa: F401
    except ImportError:
        sys.modules["libvirt"] = MagicMock()

import pytest
from jorge_agent.schemas.instance import InstanceSummaryResponse, RuntimeAllocation
from jorge_agent.services import health_service, node_snapshot_service
from jorge_agent.schemas.agent import AgentStatusResponse


@pytest.mark.parametrize(
    ("state", "runtime", "responds", "expected"),
    [
        ("stopped", None, False, "offline"),
        ("running", RuntimeAllocation(ip="10.0.0.1"), True, "online"),
        ("running", RuntimeAllocation(ip="10.0.0.1"), False, "unavailable"),
        ("running", None, False, "unknown"),
        ("unknown", None, False, "unknown"),
        ("paused", None, False, "unknown"),
    ],
)
def test_minecraft_probe(monkeypatch, state, runtime, responds, expected):
    probe = Mock(return_value=responds)
    monkeypatch.setattr(health_service, "_minecraft_port_open", probe)
    assert health_service.observe_minecraft_status(state, runtime) == expected
    assert probe.call_count == (1 if state == "running" and runtime else 0)


def test_snapshot_keeps_inventory_when_probe_fails(monkeypatch):
    instance = InstanceSummaryResponse(
        name="test",
        state="running",
        vm_username="operator",
        memory_mb=512,
        vcpus=1,
        minecraft_version="26.2",
    )
    # Avoid host sampling or any libvirt call, while exercising real serialization.
    monkeypatch.setattr(
        node_snapshot_service,
        "get_agent_status",
        lambda: AgentStatusResponse(
            status="ok",
            service="test",
            version="0.1.0",
            started_at=datetime.now(timezone.utc),
            uptime_seconds=1.5,
        ),
    )
    monkeypatch.setattr(node_snapshot_service, "get_node_health", lambda: None)
    monkeypatch.setattr(node_snapshot_service, "get_host_metrics", lambda: None)
    monkeypatch.setattr(node_snapshot_service, "list_instances", lambda: [instance])
    monkeypatch.setattr(
        node_snapshot_service,
        "observe_minecraft_status",
        Mock(side_effect=OSError("probe failed")),
    )
    snapshot = node_snapshot_service.get_node_snapshot()
    assert snapshot.instances[0].name == "test"
    assert snapshot.instances[0].minecraft_status == "unknown"
    assert snapshot.errors == {}
