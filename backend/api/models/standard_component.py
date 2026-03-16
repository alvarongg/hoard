"""SQLAlchemy model for standard components per sub-category."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import DBUUID, Base, UUIDMixin


class StandardComponent(UUIDMixin, Base):
    """Standard component for a sub-category (box, manual, cartridge, etc.)."""

    __tablename__ = "standard_components"
    __table_args__ = (
        UniqueConstraint(
            "sub_category_id", "component_name",
            name="uq_standard_component_sub_name",
        ),
    )

    sub_category_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("sub_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    component_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<StandardComponent(id={self.id!r}, "
            f"component_name={self.component_name!r})>"
        )
