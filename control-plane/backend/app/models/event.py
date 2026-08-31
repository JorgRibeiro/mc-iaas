"""Append-only domain Event persistence model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now
from app.models.enums import EventLevel
from app.models.types import domain_enum

if TYPE_CHECKING:
    from app.models.compute_node import ComputeNode
    from app.models.instance import Instance
    from app.models.operation import Operation


class Event(Base):
    """Historical fact emitted by a Control Plane component."""

    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    level: Mapped[EventLevel] = mapped_column(
        domain_enum(EventLevel, "event_level"), nullable=False
    )
    component: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_id: Mapped[UUID | None] = mapped_column(ForeignKey("compute_nodes.id"), index=True)
    instance_id: Mapped[UUID | None] = mapped_column(ForeignKey("instances.id"), index=True)
    operation_id: Mapped[UUID | None] = mapped_column(ForeignKey("operations.id"), index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=False
    )

    node: Mapped["ComputeNode | None"] = relationship(back_populates="events")
    instance: Mapped["Instance | None"] = relationship(back_populates="events")
    operation: Mapped["Operation | None"] = relationship(back_populates="events")
