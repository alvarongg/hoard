"""SQLAlchemy declarative base and common mixins for all models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class DBUUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native UUID on PostgreSQL, CHAR(36) on other
    backends (e.g. SQLite for tests). Values are always stored and
    returned as strings.
    """

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return value
        return str(value)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def _generate_uuid_str() -> str:
    """Generate a UUID4 as a string for cross-database compatibility."""
    return str(uuid.uuid4())


class UUIDMixin:
    """Mixin that adds a UUID primary key column.

    Uses DBUUID for cross-database compatibility (native UUID on
    PostgreSQL, CHAR(36) on SQLite).
    """

    id: Mapped[str] = mapped_column(
        DBUUID(),
        primary_key=True,
        default=_generate_uuid_str,
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
