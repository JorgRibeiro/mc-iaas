"""Real Agent route/payload contracts and sanitized semantic errors."""

import json

import httpx
import pytest

from app.clients.compute_agent import ComputeAgentClient
from app.clients.errors import (
    AgentAuthenticationError,
    AgentConflictError,
    AgentNotFoundError,
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
    AgentValidationError,
)


@pytest.mark.parametrize("action", ["create", "start", "stop", "restart", "delete"])
async def test_real_routes_and_safe_response(action):
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-token"
        if action == "create":
            assert request.url.path == "/base/instances"
            assert request.method == "POST"
            assert json.loads(request.content) == {
                "name": "test-vm",
                "vm_username": "operator",
                "accept_eula": True,
            }
        else:
            suffix = "" if action == "delete" else "/" + action
            assert request.url.path == "/base/instances/test-vm" + suffix
            assert request.method == ("DELETE" if action == "delete" else "POST")
        if action == "delete":
            assert request.url.params["delete_data"] == "false"
            return httpx.Response(
                200, json={"name": "test-vm", "deleted": True, "data_preserved": True}
            )
        return httpx.Response(
            201 if action == "create" else 200,
            json={
                "name": "test-vm",
                "state": "stopped",
                "generated_password": "private-password",
                "runtime": None,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = ComputeAgentClient(http)
        argument = (
            {"name": "test-vm", "vm_username": "operator", "accept_eula": True}
            if action == "create"
            else "test-vm"
        )
        result = await getattr(client, action + "_instance")(
            "http://agent.test/base/", "test-token", argument
        )
    assert "private-password" not in repr(result) + str(result.model_dump())


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AgentAuthenticationError),
        (403, AgentAuthenticationError),
        (404, AgentNotFoundError),
        (409, AgentConflictError),
        (400, AgentValidationError),
        (422, AgentValidationError),
        (500, AgentResponseError),
        (504, AgentTimeoutError),
        (302, AgentResponseError),
    ],
)
async def test_semantic_mutation_status_errors(status, expected):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, text="private body"))
    ) as http:
        with pytest.raises(expected) as caught:
            await ComputeAgentClient(http).start_instance("http://agent.test", "token", "test-vm")
    assert "private body" not in str(caught.value)


@pytest.mark.parametrize(
    ("error", "expected"),
    [(httpx.ReadTimeout, AgentTimeoutError), (httpx.ConnectError, AgentUnavailableError)],
)
async def test_mutation_transport_errors(error, expected):
    def handler(request):
        raise error("private transport detail", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(expected):
            await ComputeAgentClient(http).stop_instance("http://agent.test", "token", "test-vm")
