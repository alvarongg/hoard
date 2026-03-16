"""SQLAlchemy model for item images."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import DBUUID, Base, UUIDMixin


class ItemImage(UUIDMixin, Base):
    """Image attached to a collection item."""

    __tablename__ = "item_images"

    collection_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    # Relationships
    collection_item: Mapped[CollectionItem] = relationship()

    def __repr__(self) -> str:
        return f"<ItemImage(id={self.id!r}, file_name={self.file_name!r})>"
