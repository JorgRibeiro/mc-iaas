import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from pathlib import Path

import httpx
import pytest


RUN_E2E = os.getenv("MC_IAAS_RUN_E2E") == "1"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not RUN_E2E,
        reason=(
            "destructive E2E disabled; "
            "set MC_IAAS_RUN_E2E=1 to enable"
        ),
    ),
]

# Keep libvirt-dependent imports out of collection on development
# machines unless destructive E2E execution was explicitly enabled.
if RUN_E2E:
    import libvirt

    from jorge_agent.config import LIBVIRT, NETWORK, PATHS, STORAGE
    from jorge_agent.services.invariant_service import (
        check_invariants,
    )
    from jorge_agent.services.runtime_service import (
        available_runtime_slots,
        get_instance_runtime,
    )


API_URL = os.getenv(
    "MC_IAAS_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

API_TOKEN_FILE = Path(
    os.getenv(
        "MC_IAAS_API_TOKEN_FILE",
        "/srv/mc-iaas/secrets/agent-api-token",
    )
)

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv(
        "MC_IAAS_REQUEST_TIMEOUT_SECONDS",
        "90",
    )
)
MINECRAFT_TIMEOUT_SECONDS = float(
    os.getenv(
        "MC_IAAS_MINECRAFT_TIMEOUT_SECONDS",
        "300",
    )
)
RCON_TIMEOUT_SECONDS = float(
    os.getenv(
        "MC_IAAS_RCON_TIMEOUT_SECONDS",
        "60",
    )
)
POLL_INTERVAL_SECONDS = float(
    os.getenv(
        "MC_IAAS_POLL_INTERVAL_SECONDS",
        "2",
    )
)

SENSITIVE_KEYS = {
    "generated_password",
    "password",
    "password_hash",
    "rcon_password",
    "vm_password",
}


def _load_api_token() -> str:
    env_token = os.getenv(
        "MC_IAAS_API_TOKEN"
    )

    if env_token:
        return env_token

    try:
        token = API_TOKEN_FILE.read_text(
            encoding="utf-8",
        ).strip()
    except OSError as exc:
        pytest.fail(
            "Could not load Compute Agent API token "
            f"from {API_TOKEN_FILE}: {exc}",
            pytrace=False,
        )

    if not token:
        pytest.fail(
            "Compute Agent API token is empty",
            pytrace=False,
        )

    return token


@dataclass
class E2EContext:
    client: httpx.Client
    name: str
    create_attempted: bool = False


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                "<redacted>"
                if key in SENSITIVE_KEYS
                else _redact(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_redact(item) for item in value]

    return value


def _response_detail(response: httpx.Response) -> str:
    try:
        return repr(_redact(response.json()))
    except ValueError:
        return repr(response.text[:500])


def _assert_status(
    response: httpx.Response,
    expected_status: int,
    operation: str,
) -> None:
    assert response.status_code == expected_status, (
        f"{operation} returned HTTP {response.status_code}; "
        f"expected {expected_status}. "
        f"Response: {_response_detail(response)}"
    )


def _json_response(
    response: httpx.Response,
    expected_status: int,
    operation: str,
) -> dict[str, Any]:
    _assert_status(
        response,
        expected_status,
        operation,
    )

    data = response.json()
    assert isinstance(data, dict), (
        f"{operation} did not return a JSON object"
    )
    return data


def _runtime_fields(runtime: Any) -> dict[str, Any]:
    assert isinstance(runtime, dict), (
        f"Expected runtime allocation, got: {runtime!r}"
    )

    allocation = {
        "slot": runtime.get("slot"),
        "ip": runtime.get("ip"),
        "external_port": runtime.get("external_port"),
    }
    assert all(value is not None for value in allocation.values()), (
        f"Incomplete runtime allocation: {allocation!r}"
    )
    return allocation


def _wait_for_minecraft_online(
    client: httpx.Client,
    name: str,
) -> dict[str, Any]:
    deadline = time.monotonic() + MINECRAFT_TIMEOUT_SECONDS
    last_observation: Any = None

    while True:
        response = client.get(
            f"/instances/{name}/health"
        )

        if response.status_code == 200:
            health = response.json()
            last_observation = health

            if (
                health.get("instance_state") == "running"
                and health.get("minecraft_state") == "online"
            ):
                return health
        else:
            last_observation = {
                "status_code": response.status_code,
                "response": _response_detail(response),
            }

        if time.monotonic() >= deadline:
            pytest.fail(
                f"Minecraft for {name} did not become online "
                f"within {MINECRAFT_TIMEOUT_SECONDS}s. "
                f"Last health: {last_observation!r}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)


def _wait_for_rcon(
    client: httpx.Client,
    name: str,
) -> dict[str, Any]:
    deadline = time.monotonic() + RCON_TIMEOUT_SECONDS
    last_observation: Any = None

    while True:
        response = client.post(
            f"/instances/{name}/minecraft/command",
            json={"command": "list"},
        )

        if response.status_code == 200:
            result = response.json()
            assert result.get("name") == name
            assert result.get("command") == "list"
            assert isinstance(result.get("response"), str)
            return result

        last_observation = {
            "status_code": response.status_code,
            "response": _response_detail(response),
        }

        if response.status_code not in {409, 503}:
            _assert_status(
                response,
                200,
                "RCON command",
            )

        if time.monotonic() >= deadline:
            pytest.fail(
                f"RCON for {name} did not become ready "
                f"within {RCON_TIMEOUT_SECONDS}s. "
                f"Last response: {last_observation!r}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)


def _cleanup_instance(context: E2EContext) -> list[str]:
    if not context.create_attempted:
        return []

    errors = []

    try:
        response = context.client.get(
            f"/instances/{context.name}"
        )
    except Exception as exc:
        errors.append(f"GET before cleanup failed: {exc}")
        response = None

    if response is not None and response.status_code == 404:
        return errors

    should_stop = True

    if response is not None and response.status_code == 200:
        try:
            should_stop = (
                response.json().get("state") != "stopped"
            )
        except ValueError as exc:
            errors.append(
                f"GET before cleanup returned invalid JSON: {exc}"
            )
    elif response is not None:
        errors.append(
            "GET before cleanup returned HTTP "
            f"{response.status_code}: {_response_detail(response)}"
        )

    if should_stop:
        try:
            stop_response = context.client.post(
                f"/instances/{context.name}/stop"
            )

            if stop_response.status_code not in {200, 404}:
                errors.append(
                    "STOP during cleanup returned HTTP "
                    f"{stop_response.status_code}: "
                    f"{_response_detail(stop_response)}"
                )
        except Exception as exc:
            errors.append(f"STOP during cleanup failed: {exc}")

    try:
        delete_response = context.client.delete(
            f"/instances/{context.name}",
            params={"delete_data": "true"},
        )

        if delete_response.status_code not in {200, 404}:
            errors.append(
                "DELETE during cleanup returned HTTP "
                f"{delete_response.status_code}: "
                f"{_response_detail(delete_response)}"
            )
    except Exception as exc:
        errors.append(f"DELETE during cleanup failed: {exc}")

    return errors


@pytest.fixture
def e2e_context() -> E2EContext:
    name = f"e2e-{uuid.uuid4().hex[:8]}"

    with httpx.Client(
        base_url=API_URL,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={
            "Authorization": (
                f"Bearer {_load_api_token()}"
            ),
        },
    ) as client:
        context = E2EContext(
            client=client,
            name=name,
        )

        yield context

        cleanup_errors = _cleanup_instance(context)

        if cleanup_errors:
            pytest.fail(
                "Best-effort E2E cleanup failed: "
                + "; ".join(cleanup_errors),
                pytrace=False,
            )


def _assert_artifacts_removed(name: str) -> None:
    paths = {
        "cloud-init directory": PATHS.cloud_init_root / name,
        "secret JSON": PATHS.secrets_dir / f"{name}.json",
        "metadata JSON": PATHS.metadata_dir / f"{name}.json",
    }
    remaining_paths = [
        f"{label}: {path}"
        for label, path in paths.items()
        if path.exists()
    ]
    assert not remaining_paths, (
        "Filesystem artifacts remain after DELETE: "
        + "; ".join(remaining_paths)
    )

    conn = libvirt.open(LIBVIRT.uri)
    assert conn is not None, (
        "Could not connect to libvirt while checking cleanup"
    )

    try:
        domains = {
            domain.name()
            for domain in conn.listAllDomains()
        }
        instance_volumes = set(
            conn.storagePoolLookupByName(
                LIBVIRT.instance_pool
            ).listVolumes()
        )
        data_volumes = set(
            conn.storagePoolLookupByName(
                LIBVIRT.volume_pool
            ).listVolumes()
        )
    finally:
        conn.close()

    assert name not in domains, (
        f"libvirt domain still exists: {name}"
    )
    assert f"{name}.qcow2" not in instance_volumes, (
        f"System disk still exists: {name}.qcow2"
    )
    assert f"{name}-data.raw" not in data_volumes, (
        f"Data volume still exists: {name}-data.raw"
    )


@pytest.mark.e2e
def test_full_instance_lifecycle(
    e2e_context: E2EContext,
) -> None:
    client = e2e_context.client
    name = e2e_context.name

    # 1. API health must pass before any destructive request.
    api_health = _json_response(
        client.get("/health"),
        200,
        "API health",
    )
    assert api_health.get("status") == "ok"
    assert api_health.get("service") == "jorge-agent"

    # 2. Refuse to create a VM on an inconsistent baseline.
    baseline = check_invariants()
    assert baseline.healthy, (
        f"Unhealthy invariant baseline: {baseline.issues!r}"
    )

    unique_name = client.get(f"/instances/{name}")
    _assert_status(
        unique_name,
        404,
        "unique E2E instance name precondition",
    )

    # 3. CREATE must not allocate runtime resources.
    e2e_context.create_attempted = True
    created = _json_response(
        client.post(
            "/instances",
            json={
                "name": name,
                "vm_username": "teste",
                "memory_mb": 2048,
                "vcpus": 1,
                "minecraft_version": "26.2",
                "accept_eula": True,
            },
        ),
        201,
        "CREATE",
    )
    created.pop("generated_password", None)
    assert created.get("name") == name
    assert created.get("state") == "stopped"
    assert created.get("runtime") is None
    assert created.get("memory_mb") == 2048
    assert created.get("vcpus") == 1
    assert created.get("minecraft_version") == "26.2"

    # 4-6. GET, LIST and direct runtime inspection after CREATE.
    instance = _json_response(
        client.get(f"/instances/{name}"),
        200,
        "GET after CREATE",
    )
    assert instance.get("state") == "stopped"
    assert instance.get("runtime") is None

    instances = client.get("/instances")
    _assert_status(instances, 200, "LIST after CREATE")
    assert any(
        item.get("name") == name
        for item in instances.json()
    ), f"Created instance {name} is absent from LIST"
    assert get_instance_runtime(name) is None

    # 7-11. START, Minecraft readiness, health, metrics and RCON.
    started = _json_response(
        client.post(f"/instances/{name}/start"),
        200,
        "START",
    )
    assert started.get("state") == "running"
    first_runtime = _runtime_fields(started.get("runtime"))

    _wait_for_minecraft_online(client, name)

    instance_health = _json_response(
        client.get(f"/instances/{name}/health"),
        200,
        "instance health",
    )
    assert instance_health.get("instance_state") == "running"
    assert instance_health.get("minecraft_state") == "online"
    assert instance_health.get("minecraft_port") == (
        NETWORK.internal_minecraft_port
    )
    assert _runtime_fields(
        instance_health.get("runtime")
    ) == first_runtime

    metrics = _json_response(
        client.get(f"/instances/{name}/metrics"),
        200,
        "metrics",
    )
    assert metrics.get("name") == name
    assert metrics.get("state") == "running"
    assert metrics["cpu"].get("vcpus") == 1
    assert metrics["memory"].get("configured_mb") == 2048
    assert metrics["storage"].get("system") is not None
    assert metrics["storage"].get("data") is not None
    assert metrics["storage"]["system"].get(
        "capacity_bytes"
    ) == STORAGE.system_disk_bytes
    assert metrics["storage"]["data"].get(
        "capacity_bytes"
    ) == STORAGE.data_disk_bytes
    assert metrics.get("network") is not None

    _wait_for_rcon(client, name)

    # 12-13. RESTART preserves runtime and restores readiness.
    restarted = _json_response(
        client.post(f"/instances/{name}/restart"),
        200,
        "RESTART",
    )
    assert restarted.get("state") == "running"
    assert _runtime_fields(
        restarted.get("runtime")
    ) == first_runtime

    _wait_for_minecraft_online(client, name)
    _wait_for_rcon(client, name)

    # 14-15. STOP releases runtime and makes its old slot available.
    stopped = _json_response(
        client.post(f"/instances/{name}/stop"),
        200,
        "STOP",
    )
    assert stopped.get("state") == "stopped"
    assert stopped.get("runtime") is None

    stopped_instance = _json_response(
        client.get(f"/instances/{name}"),
        200,
        "GET after STOP",
    )
    assert stopped_instance.get("state") == "stopped"
    assert stopped_instance.get("runtime") is None
    assert get_instance_runtime(name) is None
    assert any(
        slot.slot == first_runtime["slot"]
        for slot in available_runtime_slots()
    ), (
        f"Released slot {first_runtime['slot']} "
        "is not available after STOP"
    )

    # 16-18. A second START/STOP cycle may use any valid slot.
    started_again = _json_response(
        client.post(f"/instances/{name}/start"),
        200,
        "second START",
    )
    assert started_again.get("state") == "running"
    _runtime_fields(started_again.get("runtime"))

    _wait_for_minecraft_online(client, name)
    _wait_for_rcon(client, name)

    stopped_again = _json_response(
        client.post(f"/instances/{name}/stop"),
        200,
        "final STOP",
    )
    assert stopped_again.get("state") == "stopped"
    assert stopped_again.get("runtime") is None

    # 19-21. Destructive DELETE removes API and host artifacts.
    deleted = _json_response(
        client.delete(
            f"/instances/{name}",
            params={"delete_data": "true"},
        ),
        200,
        "destructive DELETE",
    )
    assert deleted.get("name") == name
    assert deleted.get("deleted") is True
    assert deleted.get("data_preserved") is False
    assert deleted.get("data_volume") is None

    missing = client.get(f"/instances/{name}")
    _assert_status(missing, 404, "GET after DELETE")

    remaining_instances = client.get("/instances")
    _assert_status(
        remaining_instances,
        200,
        "LIST after DELETE",
    )
    assert all(
        item.get("name") != name
        for item in remaining_instances.json()
    ), f"Deleted instance {name} is still present in LIST"

    _assert_artifacts_removed(name)

    # 22. The Compute Node must return to a healthy baseline.
    final_invariants = check_invariants()
    assert final_invariants.healthy, (
        f"Unhealthy final invariants: {final_invariants.issues!r}"
    )
