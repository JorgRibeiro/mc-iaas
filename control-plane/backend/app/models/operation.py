"""Control Plane Operation persistence model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    and_,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now
from app.models.enums import OperationStatus, OperationType
from app.models.types import domain_enum

if TYPE_CHECKING:
    from app.models.compute_node import ComputeNode
    from app.models.event import Event
    from app.models.instance import Instance


class Operation(Base):
    """A durable request to mutate or reconcile infrastructure state."""

    __tablename__ = "operations"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    type: Mapped[OperationType] = mapped_column(
        domain_enum(OperationType, "operation_type"), nullable=False
    )
    status: Mapped[OperationStatus] = mapped_column(
        domain_enum(OperationStatus, "operation_status"),
        default=OperationStatus.PENDING,
        server_default=OperationStatus.PENDING.value,
        nullable=False,
    )
    instance_id: Mapped[UUID | None] = mapped_column(ForeignKey("instances.id"), index=True)
    node_id: Mapped[UUID | None] = mapped_column(ForeignKey("compute_nodes.id"), index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    idempotency_key: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), default=uuid4, nullable=False
    )
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    operation_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}", nullable=False
    )

    instance: Mapped["Instance | None"] = relationship(back_populates="operations")
    node: Mapped["ComputeNode | None"] = relationship(back_populates="operations")
    events: Mapped[list["Event"]] = relationship(back_populates="operation")


Operation.__table__.append_constraint(
    CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative")
)
Index("uq_operations_idempotency_key", Operation.idempotency_key, unique=True)
Index(
    "uq_operations_active_mutation_per_instance",
    Operation.instance_id,
    unique=True,
    postgresql_where=and_(
        Operation.instance_id.is_not(None),
        Operation.status.in_(
            [
                OperationStatus.PENDING,
                OperationStatus.IN_PROGRESS,
                OperationStatus.UNCERTAIN,
            ]
        ),
        Operation.type.in_(
            [
                OperationType.CREATE,
                OperationType.START,
                OperationType.STOP,
                OperationType.RESTART,
                OperationType.DELETE,
            ]
        ),
    ),
)
