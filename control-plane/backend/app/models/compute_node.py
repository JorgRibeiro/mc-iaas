"""Compute Node persistence model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, true
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import NodeHealth, NodeReachability
from app.models.types import domain_enum

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.instance import Instance
    from app.models.operation import Operation


class ComputeNode(TimestampMixin, Base):
    """Registered Compute Agent and its latest observed capacity."""

    __tablename__ = "compute_nodes"
    __table_args__ = (
        CheckConstraint(
            "max_active_instances IS NULL OR max_active_instances >= 0",
            name="max_active_instances_non_negative",
        ),
        CheckConstraint(
            "active_instances IS NULL OR active_instances >= 0",
            name="active_instances_non_negative",
        ),
        CheckConstraint(
            "occupied_runtime_slots IS NULL OR occupied_runtime_slots >= 0",
            name="occupied_runtime_slots_non_negative",
        ),
        CheckConstraint(
            "available_slots IS NULL OR available_slots >= 0",
            name="available_slots_non_negative",
        ),
        CheckConstraint("consecutive_failures >= 0", name="consecutive_failures_non_negative"),
        Index("uq_compute_nodes_name", "name", unique=True),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False)
    credential_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    reachability: Mapped[NodeReachability] = mapped_column(
        domain_enum(NodeReachability, "node_reachability"),
        default=NodeReachability.UNKNOWN,
        server_default=NodeReachability.UNKNOWN.value,
        nullable=False,
    )
    observed_health: Mapped[NodeHealth] = mapped_column(
        domain_enum(NodeHealth, "node_health"),
        default=NodeHealth.UNKNOWN,
        server_default=NodeHealth.UNKNOWN.value,
        nullable=False,
    )
    observed_ready: Mapped[bool | None] = mapped_column(Boolean)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    agent_version: Mapped[str | None] = mapped_column(String(100))
    max_active_instances: Mapped[int | None] = mapped_column(Integer)
    active_instances: Mapped[int | None] = mapped_column(Integer)
    occupied_runtime_slots: Mapped[int | None] = mapped_column(Integer)
    available_slots: Mapped[int | None] = mapped_column(Integer)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text)

    instances: Mapped[list["Instance"]] = relationship(back_populates="compute_node")
    operations: Mapped[list["Operation"]] = relationship(back_populates="node")
    events: Mapped[list["Event"]] = relationship(back_populates="node")
