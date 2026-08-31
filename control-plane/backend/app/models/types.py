"""Reusable SQLAlchemy domain column types."""

from enum import Enum as PythonEnum

from sqlalchemy import Enum as SqlEnum


def domain_enum(enum_class: type[PythonEnum], name: str) -> SqlEnum:
    """Build a PostgreSQL enum that persists Python enum values, not member names."""
    return SqlEnum(
        enum_class,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
