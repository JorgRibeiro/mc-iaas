"""create_control_plane_domain

Revision ID: 59e3e9bc94f7
Revises:
Create Date: 2026-08-28 12:47:33.580923
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "59e3e9bc94f7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "compute_nodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("endpoint", sa.String(length=2048), nullable=False),
        sa.Column("credential_ref", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "reachability",
            sa.Enum("unknown", "online", "offline", name="node_reachability"),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column(
            "observed_health",
            sa.Enum("unknown", "healthy", "degraded", "unhealthy", name="node_health"),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("observed_ready", sa.Boolean(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agent_version", sa.String(length=100), nullable=True),
        sa.Column("max_active_instances", sa.Integer(), nullable=True),
        sa.Column("active_instances", sa.Integer(), nullable=True),
        sa.Column("occupied_runtime_slots", sa.Integer(), nullable=True),
        sa.Column("available_slots", sa.Integer(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "active_instances IS NULL OR active_instances >= 0",
            name=op.f("ck_compute_nodes_active_instances_non_negative"),
        ),
        sa.CheckConstraint(
            "available_slots IS NULL OR available_slots >= 0",
            name=op.f("ck_compute_nodes_available_slots_non_negative"),
        ),
        sa.CheckConstraint(
            "consecutive_failures >= 0",
            name=op.f("ck_compute_nodes_consecutive_failures_non_negative"),
        ),
        sa.CheckConstraint(
            "max_active_instances IS NULL OR max_active_instances >= 0",
            name=op.f("ck_compute_nodes_max_active_instances_non_negative"),
        ),
        sa.CheckConstraint(
            "occupied_runtime_slots IS NULL OR occupied_runtime_slots >= 0",
            name=op.f("ck_compute_nodes_occupied_runtime_slots_non_negative"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compute_nodes")),
    )
    op.create_index("uq_compute_nodes_name", "compute_nodes", ["name"], unique=True)
    op.create_table(
        "instances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("compute_node_id", sa.UUID(), nullable=True),
        sa.Column(
            "desired_state",
            sa.Enum("stopped", "running", "absent", name="desired_instance_state"),
            server_default="stopped",
            nullable=False,
        ),
        sa.Column(
            "observed_state",
            sa.Enum(
                "unknown", "missing", "stopped", "running", "paused", name="observed_instance_state"
            ),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("memory_mb", sa.Integer(), server_default="2048", nullable=False),
        sa.Column("vcpus", sa.Integer(), server_default="1", nullable=False),
        sa.Column("minecraft_version", sa.String(length=100), nullable=False),
        sa.Column("observed_runtime_slot", sa.Integer(), nullable=True),
        sa.Column("observed_runtime_ip", sa.String(length=45), nullable=True),
        sa.Column("observed_external_port", sa.Integer(), nullable=True),
        sa.Column(
            "minecraft_status",
            sa.Enum("unknown", "online", "offline", "unavailable", name="minecraft_status"),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("memory_mb <= 2048", name=op.f("ck_instances_memory_mb_maximum")),
        sa.CheckConstraint("memory_mb >= 512", name=op.f("ck_instances_memory_mb_minimum")),
        sa.CheckConstraint("vcpus = 1", name=op.f("ck_instances_vcpus_one")),
        sa.ForeignKeyConstraint(
            ["compute_node_id"],
            ["compute_nodes.id"],
            name=op.f("fk_instances_compute_node_id_compute_nodes"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instances")),
    )
    op.create_index(
        op.f("ix_instances_compute_node_id"), "instances", ["compute_node_id"], unique=False
    )
    op.create_index("uq_instances_name", "instances", ["name"], unique=True)
    op.create_table(
        "operations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "create", "start", "stop", "restart", "delete", "reconcile", name="operation_type"
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "succeeded",
                "failed",
                "uncertain",
                name="operation_status",
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("instance_id", sa.UUID(), nullable=True),
        sa.Column("node_id", sa.UUID(), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("idempotency_key", sa.UUID(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.CheckConstraint(
            "attempt_count >= 0", name=op.f("ck_operations_attempt_count_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["instance_id"], ["instances.id"], name=op.f("fk_operations_instance_id_instances")
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["compute_nodes.id"], name=op.f("fk_operations_node_id_compute_nodes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_operations")),
    )
    op.create_index(op.f("ix_operations_instance_id"), "operations", ["instance_id"], unique=False)
    op.create_index(op.f("ix_operations_node_id"), "operations", ["node_id"], unique=False)
    op.create_index(
        "uq_operations_active_mutation_per_instance",
        "operations",
        ["instance_id"],
        unique=True,
        postgresql_where=sa.text(
            "instance_id IS NOT NULL AND status IN ('pending', 'in_progress', 'uncertain') AND type IN ('create', 'start', 'stop', 'restart', 'delete')"
        ),
    )
    op.create_index("uq_operations_idempotency_key", "operations", ["idempotency_key"], unique=True)
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("level", sa.Enum("info", "warning", "error", name="event_level"), nullable=False),
        sa.Column("component", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("node_id", sa.UUID(), nullable=True),
        sa.Column("instance_id", sa.UUID(), nullable=True),
        sa.Column("operation_id", sa.UUID(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["instance_id"], ["instances.id"], name=op.f("fk_events_instance_id_instances")
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["compute_nodes.id"], name=op.f("fk_events_node_id_compute_nodes")
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["operations.id"], name=op.f("fk_events_operation_id_operations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_instance_id"), "events", ["instance_id"], unique=False)
    op.create_index(op.f("ix_events_node_id"), "events", ["node_id"], unique=False)
    op.create_index(op.f("ix_events_operation_id"), "events", ["operation_id"], unique=False)
    op.create_index(op.f("ix_events_timestamp"), "events", ["timestamp"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_events_timestamp"), table_name="events")
    op.drop_index(op.f("ix_events_operation_id"), table_name="events")
    op.drop_index(op.f("ix_events_node_id"), table_name="events")
    op.drop_index(op.f("ix_events_instance_id"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_table("events")
    op.drop_index("uq_operations_idempotency_key", table_name="operations")
    op.drop_index(
        "uq_operations_active_mutation_per_instance",
        table_name="operations",
        postgresql_where=sa.text(
            "instance_id IS NOT NULL AND status IN ('pending', 'in_progress', 'uncertain') AND type IN ('create', 'start', 'stop', 'restart', 'delete')"
        ),
    )
    op.drop_index(op.f("ix_operations_node_id"), table_name="operations")
    op.drop_index(op.f("ix_operations_instance_id"), table_name="operations")
    op.drop_table("operations")
    op.drop_index("uq_instances_name", table_name="instances")
    op.drop_index(op.f("ix_instances_compute_node_id"), table_name="instances")
    op.drop_table("instances")
    op.drop_index("uq_compute_nodes_name", table_name="compute_nodes")
    op.drop_table("compute_nodes")

    # PostgreSQL enum types outlive their tables unless explicitly removed.
    for enum_name in (
        "event_level",
        "operation_status",
        "operation_type",
        "minecraft_status",
        "observed_instance_state",
        "desired_instance_state",
        "node_health",
        "node_reachability",
    ):
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
