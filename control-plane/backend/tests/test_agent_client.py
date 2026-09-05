"""Agent contract and transport handling without a real Agent."""

import logging

import httpx
import pytest

from app.clients.compute_agent import ComputeAgentClient
from app.clients.errors import (
    AgentAuthenticationError,
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
)


@pytest.fixture
def snapshot_payload():
    return {
        "generated_at": "2026-09-05T12:00:00Z",
        "agent": {"version": "0.1.0", "service": "compute-agent", "status": "ok"},
        "node_health": {
            "status": "healthy",
            "ready": True,
            "capacity": {
                "max_active_instances": 4,
                "active_instances": 1,
                "occupied_runtime_slots": 2,
                "available_slots": 2,
            },
            "libvirt": {"healthy": True},
        },
        "node_metrics": {"unused": "field"},
        "instances": [],
        "errors": {},
        "future_field": True,
    }


async def test_bearer_and_path_normalization(snapshot_payload):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer test-secret"
        assert str(request.url) == "https://agent.example/base/node/snapshot"
        assert not request.url.query
        return httpx.Response(200, json=snapshot_payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = ComputeAgentClient(http_client)
        for endpoint in ["https://agent.example/base", "https://agent.example/base///"]:
            snapshot = await client.get_snapshot(endpoint, "test-secret")
            assert snapshot.agent.version == "0.1.0"
            assert snapshot.node_health.capacity.available_slots == 2
    assert len(requests) == 2


@pytest.mark.parametrize(
    ("transport_error", "expected"),
    [
        (httpx.ConnectTimeout, AgentTimeoutError),
        (httpx.ReadTimeout, AgentTimeoutError),
        (httpx.PoolTimeout, AgentTimeoutError),
        (httpx.ConnectError, AgentUnavailableError),
        (httpx.ReadError, AgentUnavailableError),
    ],
)
async def test_transport_errors_are_safe(transport_error, expected, caplog):
    def handler(request):
        raise transport_error("test-secret internal details", request=request)

    with caplog.at_level(logging.WARNING):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            with pytest.raises(expected) as caught:
                await ComputeAgentClient(http_client).get_snapshot("https://agent.example", "token")
    assert "test-secret" not in str(caught.value) + caplog.text
    assert caught.value.__suppress_context__


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AgentAuthenticationError),
        (403, AgentAuthenticationError),
        (500, AgentResponseError),
        (503, AgentResponseError),
        (404, AgentResponseError),
        (302, AgentResponseError),
    ],
)
async def test_status_errors_and_no_redirect(status, expected, caplog):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            status, text="test-secret", headers={"Location": "https://other.test"}
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as http_client:
        with pytest.raises(expected) as caught:
            await ComputeAgentClient(http_client).get_snapshot("https://agent.example", "token")
    assert len(requests) == 1
    assert "test-secret" not in str(caught.value) + caplog.text


@pytest.mark.parametrize("content", [b"not JSON test-secret", b"{}", b"[]", b"null"])
async def test_bad_contract(content):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content))
    ) as http_client:
        with pytest.raises(AgentResponseError) as caught:
            await ComputeAgentClient(http_client).get_snapshot("https://agent.example", "token")
    assert "test-secret" not in str(caught.value)


@pytest.mark.parametrize("section", ["node_health", "node_metrics", "instances"])
async def test_partial_snapshot_accepts_null_or_missing(snapshot_payload, section):
    snapshot_payload.pop(section)
    snapshot_payload["errors"] = {section: "private details"}
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=snapshot_payload))
    ) as http_client:
        snapshot = await ComputeAgentClient(http_client).get_snapshot(
            "https://agent.example", "token"
        )
    assert snapshot.agent.version == "0.1.0"
    if section == "node_health":
        assert snapshot.node_health is None


@pytest.mark.parametrize("value", [-1, True, "4"])
async def test_invalid_capacity_is_protocol_failure(snapshot_payload, value):
    snapshot_payload["node_health"]["capacity"]["available_slots"] = value
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=snapshot_payload))
    ) as http_client:
        with pytest.raises(AgentResponseError):
            await ComputeAgentClient(http_client).get_snapshot("https://agent.example", "token")


async def test_duplicate_inventory_is_partial_not_authoritative(snapshot_payload):
    snapshot_payload["instances"] = [
        {"name": "duplicate", "state": "running"},
        {"name": "duplicate", "state": "stopped"},
    ]
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=snapshot_payload))
    ) as http_client:
        snapshot = await ComputeAgentClient(http_client).get_snapshot("https://agent.test", "token")
    assert snapshot.instances is None
    assert "instances" in snapshot.errors
    assert snapshot.node_health.status == "healthy"


async def test_null_capacity_is_partial(snapshot_payload):
    snapshot_payload["node_health"]["capacity"]["available_slots"] = None
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=snapshot_payload))
    ) as http_client:
        snapshot = await ComputeAgentClient(http_client).get_snapshot(
            "https://agent.example", "token"
        )
    assert snapshot.node_health.capacity.available_slots is None
