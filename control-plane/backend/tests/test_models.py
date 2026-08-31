"""Unit tests for the persistent domain model metadata."""

from pathlib import Path

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers

import app.models  # noqa: F401
from app.db.base import Base
from app.models.compute_node import ComputeNode
from app.models.enums import (
    DesiredInstanceState,
    EventLevel,
    MinecraftStatus,
    NodeHealth,
    NodeReachability,
    ObservedInstanceState,
    OperationStatus,
    OperationType,
)
from app.models.instance import Instance
from app.models.operation import Operation


def enum_values(enum_class) -> list[str]:
    return [member.value for member in enum_class]


def constraint_names(table_name: str) -> set[str | None]:
    return {
        constraint.name
        for constraint in Base.metadata.tables[table_name].constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_metadata_contains_all_domain_tables() -> None:
    assert set(Base.metadata.tables) == {
        "compute_nodes",
        "instances",
        "operations",
        "events",
    }


def test_models_configure_without_circular_imports() -> None:
    configure_mappers()

    assert ComputeNode.instances.property.mapper.class_.__name__ == "Instance"
    assert Instance.compute_node.property.mapper.class_.__name__ == "ComputeNode"
    assert Operation.events.property.mapper.class_.__name__ == "Event"


def test_domain_enum_values_are_stable() -> None:
    assert enum_values(NodeReachability) == ["unknown", "online", "offline"]
    assert enum_values(NodeHealth) == ["unknown", "healthy", "degraded", "unhealthy"]
    assert enum_values(DesiredInstanceState) == ["stopped", "running", "absent"]
    assert enum_values(ObservedInstanceState) == [
        "unknown",
        "missing",
        "stopped",
        "running",
        "paused",
    ]
    assert enum_values(MinecraftStatus) == ["unknown", "online", "offline", "unavailable"]
    assert enum_values(OperationType) == [
        "create",
        "start",
        "stop",
        "restart",
        "delete",
        "reconcile",
    ]
    assert enum_values(OperationStatus) == [
        "pending",
        "in_progress",
        "succeeded",
        "failed",
        "uncertain",
    ]
    assert enum_values(EventLevel) == ["info", "warning", "error"]


def test_fundamental_model_defaults() -> None:
    assert ComputeNode.__table__.c.enabled.default.arg is True
    assert ComputeNode.__table__.c.reachability.default.arg is NodeReachability.UNKNOWN
    assert ComputeNode.__table__.c.observed_health.default.arg is NodeHealth.UNKNOWN
    assert Instance.__table__.c.desired_state.default.arg is DesiredInstanceState.STOPPED
    assert Instance.__table__.c.observed_state.default.arg is ObservedInstanceState.UNKNOWN
    assert Instance.__table__.c.memory_mb.default.arg == 2048
    assert Instance.__table__.c.vcpus.default.arg == 1
    assert Operation.__table__.c.status.default.arg is OperationStatus.PENDING
    assert Operation.__table__.c.attempt_count.default.arg == 0


def test_capacity_and_instance_constraints_are_present() -> None:
    assert constraint_names("compute_nodes") == {
        "ck_compute_nodes_max_active_instances_non_negative",
        "ck_compute_nodes_active_instances_non_negative",
        "ck_compute_nodes_occupied_runtime_slots_non_negative",
        "ck_compute_nodes_available_slots_non_negative",
        "ck_compute_nodes_consecutive_failures_non_negative",
    }
    assert constraint_names("instances") == {
        "ck_instances_memory_mb_minimum",
        "ck_instances_memory_mb_maximum",
        "ck_instances_vcpus_one",
    }
    assert constraint_names("operations") == {
        "ck_operations_attempt_count_non_negative",
    }


def test_active_mutation_partial_unique_index_is_present() -> None:
    index = next(
        candidate
        for candidate in Operation.__table__.indexes
        if candidate.name == "uq_operations_active_mutation_per_instance"
    )
    predicate = index.dialect_options["postgresql"]["where"].compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )

    assert index.unique
    assert [column.name for column in index.columns] == ["instance_id"]
    assert "instance_id IS NOT NULL" in str(predicate)
    for value in ("pending", "in_progress", "uncertain"):
        assert value in str(predicate)
    for value in ("create", "start", "stop", "restart", "delete"):
        assert value in str(predicate)
    assert "reconcile" not in str(predicate)


def test_migration_contains_postgresql_partial_index() -> None:
    migrations = list((Path(__file__).parents[1] / "migrations" / "versions").glob("*.py"))
    migration_source = migrations[0].read_text(encoding="utf-8")

    assert len(migrations) == 1
    assert "uq_operations_active_mutation_per_instance" in migration_source
    assert "postgresql_where" in migration_source
