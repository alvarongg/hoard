"""SQLAlchemy model for scheduled maintenance of collection items."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from api.models.collection import CollectionItem


class MaintenanceSchedule(UUIDMixin, TimestampMixin, Base):
    """A scheduled maintenance review for a collection item.

    Created only when the collector marks that an item requires maintenance
    (e.g. replacing the battery of an NES/Famicom/Game Boy cartridge).
    """

    __tablename__ = "maintenance_schedules"

    collection_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    done_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    collection_item: Mapped[CollectionItem] = relationship(
        back_populates="maintenance_schedules",
    )

    def __repr__(self) -> str:
        return (
            f"<MaintenanceSchedule(id={self.id!r}, "
            f"type={self.maintenance_type!r}, due={self.due_date!r})>"
        )
