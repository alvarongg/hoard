"""SQLAlchemy model for custom field schemas per sub-category."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from api.models.base import DBUUID, Base, UUIDMixin


class CategoryFieldSchema(UUIDMixin, Base):
    """Custom field definition for a sub-category.

    Defines the structure of custom fields that items in a sub-category
    can have (e.g., "Platform" for video games, "Format" for music).
    """

    __tablename__ = "category_field_schemas"
    __table_args__ = (
        UniqueConstraint(
            "sub_category_id",
            "field_name",
            name="uq_category_field_sub_name",
        ),
    )

    sub_category_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("sub_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    field_label: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    field_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # JSONB on PostgreSQL, JSON on SQLite for tests
    field_options: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_searchable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    default_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    help_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    sub_category: Mapped[SubCategory] = relationship(
        back_populates="field_schemas",
    )

    def __repr__(self) -> str:
        return (
            f"<CategoryFieldSchema(id={self.id!r}, "
            f"field_name={self.field_name!r})>"
        )
