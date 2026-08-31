"""Minecraft Instance persistence model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import DesiredInstanceState, MinecraftStatus, ObservedInstanceState
from app.models.types import domain_enum

if TYPE_CHECKING:
    from app.models.compute_node import ComputeNode
    from app.models.event import Event
    from app.models.operation import Operation


class Instance(TimestampMixin, Base):
    """Desired Minecraft VM and the Agent state last observed for it."""

    __tablename__ = "instances"
    __table_args__ = (
        CheckConstraint("memory_mb >= 512", name="memory_mb_minimum"),
        CheckConstraint("memory_mb <= 2048", name="memory_mb_maximum"),
        CheckConstraint("vcpus = 1", name="vcpus_one"),
        Index("uq_instances_name", "name", unique=True),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    compute_node_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("compute_nodes.id"), index=True
    )
    desired_state: Mapped[DesiredInstanceState] = mapped_column(
        domain_enum(DesiredInstanceState, "desired_instance_state"),
        default=DesiredInstanceState.STOPPED,
        server_default=DesiredInstanceState.STOPPED.value,
        nullable=False,
    )
    observed_state: Mapped[ObservedInstanceState] = mapped_column(
        domain_enum(ObservedInstanceState, "observed_instance_state"),
        default=ObservedInstanceState.UNKNOWN,
        server_default=ObservedInstanceState.UNKNOWN.value,
        nullable=False,
    )
    memory_mb: Mapped[int] = mapped_column(Integer, default=2048, server_default="2048")
    vcpus: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    minecraft_version: Mapped[str] = mapped_column(String(100), nullable=False)
    observed_runtime_slot: Mapped[int | None] = mapped_column(Integer)
    observed_runtime_ip: Mapped[str | None] = mapped_column(String(45))
    observed_external_port: Mapped[int | None] = mapped_column(Integer)
    minecraft_status: Mapped[MinecraftStatus] = mapped_column(
        domain_enum(MinecraftStatus, "minecraft_status"),
        default=MinecraftStatus.UNKNOWN,
        server_default=MinecraftStatus.UNKNOWN.value,
        nullable=False,
    )
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    compute_node: Mapped["ComputeNode | None"] = relationship(back_populates="instances")
    operations: Mapped[list["Operation"]] = relationship(back_populates="instance")
    events: Mapped[list["Event"]] = relationship(back_populates="instance")
