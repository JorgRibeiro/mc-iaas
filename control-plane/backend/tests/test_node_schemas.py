"""Administrative input validation, without a database."""

import pytest
from pydantic import ValidationError

from app.schemas.node import ComputeNodeCreate, ComputeNodeUpdate

PAYLOAD = {"name": "JORGE", "endpoint": "http://127.0.0.1:8000", "credential_ref": "jorge-agent"}


@pytest.mark.parametrize("schema", [ComputeNodeCreate, ComputeNodeUpdate])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", "  "),
        ("name", "n" * 256),
        ("credential_ref", " "),
        ("credential_ref", "r" * 256),
        ("endpoint", "invalid"),
        ("endpoint", "ftp://localhost"),
        ("endpoint", "http://"),
        ("endpoint", "http://user:password@localhost"),
        ("endpoint", "http://localhost?token=secret"),
        ("endpoint", "http://localhost/#secret"),
        ("endpoint", "http://localhost/" + "a" * 2048),
        ("name", None),
        ("endpoint", None),
        ("credential_ref", None),
        ("enabled", None),
    ],
)
def test_invalid_inputs(schema, field, value):
    with pytest.raises(ValidationError):
        schema.model_validate({**PAYLOAD, field: value})


@pytest.mark.parametrize("schema", [ComputeNodeCreate, ComputeNodeUpdate])
@pytest.mark.parametrize(
    "field",
    [
        "reachability",
        "observed_health",
        "observed_ready",
        "last_seen_at",
        "last_observed_at",
        "agent_version",
        "capacities",
        "capacity",
        "max_active_instances",
        "active_instances",
        "occupied_runtime_slots",
        "available_slots",
        "consecutive_failures",
        "last_error",
        "id",
        "created_at",
        "updated_at",
    ],
)
def test_observed_and_other_extra_fields_are_forbidden(schema, field):
    with pytest.raises(ValidationError):
        schema.model_validate({**PAYLOAD, field: "unexpected"})


def test_normalization_and_partial_update():
    node = ComputeNodeCreate(
        name=" JORGE ", endpoint="http://127.0.0.1:8000/", credential_ref=" jorge-agent "
    )
    assert node.model_dump() == {**PAYLOAD, "enabled": True}
    assert ComputeNodeUpdate().model_dump(exclude_unset=True) == {}
    assert ComputeNodeUpdate(enabled=False).model_dump(exclude_unset=True) == {"enabled": False}
    assert ComputeNodeUpdate(endpoint="https://localhost/").endpoint == "https://localhost"


@pytest.mark.parametrize("field", ["name", "endpoint", "credential_ref"])
def test_create_requires_fields(field):
    with pytest.raises(ValidationError):
        ComputeNodeCreate.model_validate({k: v for k, v in PAYLOAD.items() if k != field})
