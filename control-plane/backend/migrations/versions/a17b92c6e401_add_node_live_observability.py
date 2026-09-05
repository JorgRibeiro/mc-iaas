"""Add latest Node observability (no metric history).

Revision ID: a17b92c6e401
Revises: 59e3e9bc94f7
"""

from alembic import op
import sqlalchemy as sa

revision = "a17b92c6e401"
down_revision = "59e3e9bc94f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("compute_nodes", sa.Column("agent_uptime_seconds", sa.Float(), nullable=True))
    op.add_column("compute_nodes", sa.Column("cpu_usage_percent", sa.Float(), nullable=True))
    op.add_column("compute_nodes", sa.Column("memory_total_bytes", sa.BigInteger(), nullable=True))
    op.add_column("compute_nodes", sa.Column("memory_used_bytes", sa.BigInteger(), nullable=True))
    op.add_column(
        "compute_nodes", sa.Column("memory_available_bytes", sa.BigInteger(), nullable=True)
    )
    op.add_column("compute_nodes", sa.Column("storage_total_bytes", sa.BigInteger(), nullable=True))
    op.add_column("compute_nodes", sa.Column("storage_used_bytes", sa.BigInteger(), nullable=True))
    op.add_column(
        "compute_nodes", sa.Column("storage_available_bytes", sa.BigInteger(), nullable=True)
    )
    op.add_column("compute_nodes", sa.Column("memory_usage_percent", sa.Float(), nullable=True))
    op.add_column("compute_nodes", sa.Column("storage_usage_percent", sa.Float(), nullable=True))
    op.add_column("compute_nodes", sa.Column("libvirt_health", sa.Boolean(), nullable=True))
    op.add_column("compute_nodes", sa.Column("network_health", sa.Boolean(), nullable=True))
    op.add_column("compute_nodes", sa.Column("storage_health", sa.Boolean(), nullable=True))
    op.add_column("compute_nodes", sa.Column("invariants_health", sa.Boolean(), nullable=True))
    op.add_column("compute_nodes", sa.Column("invariants_details", sa.Text(), nullable=True))
    op.add_column(
        "compute_nodes", sa.Column("metrics_observed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("compute_nodes", "metrics_observed_at")
    op.drop_column("compute_nodes", "invariants_details")
    op.drop_column("compute_nodes", "invariants_health")
    op.drop_column("compute_nodes", "storage_health")
    op.drop_column("compute_nodes", "network_health")
    op.drop_column("compute_nodes", "libvirt_health")
    op.drop_column("compute_nodes", "storage_usage_percent")
    op.drop_column("compute_nodes", "memory_usage_percent")
    op.drop_column("compute_nodes", "storage_available_bytes")
    op.drop_column("compute_nodes", "storage_used_bytes")
    op.drop_column("compute_nodes", "storage_total_bytes")
    op.drop_column("compute_nodes", "memory_available_bytes")
    op.drop_column("compute_nodes", "memory_used_bytes")
    op.drop_column("compute_nodes", "memory_total_bytes")
    op.drop_column("compute_nodes", "cpu_usage_percent")
    op.drop_column("compute_nodes", "agent_uptime_seconds")
