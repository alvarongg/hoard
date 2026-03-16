"""SQLAlchemy models for accessories stock and item components."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin


class AccessoryStock(UUIDMixin, TimestampMixin, Base):
    """Inventory of accessories, cases, protectors, etc."""

    __tablename__ = "accessories_stock"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    compatible_sub_categories: Mapped[list | None] = mapped_column(
        JSON, nullable=True,
    )
    size_specifications: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
    )

    # Stock
    quantity_total: Mapped[int] = mapped_column(Integer, default=0)
    quantity_in_use: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock_alert: Mapped[int] = mapped_column(Integer, default=5)
    reorder_quantity: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )

    # Cost
    unit_cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Supplier
    supplier_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    supplier_sku: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    supplier_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    supplier: Mapped[Supplier | None] = relationship()

    def __repr__(self) -> str:
        return f"<AccessoryStock(id={self.id!r}, name={self.name!r})>"


class ItemComponent(UUIDMixin, TimestampMixin, Base):
    """Tracks individual components of a collection item (box, manual, etc.)."""

    __tablename__ = "item_components"

    collection_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    standard_component_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("standard_components.id", ondelete="SET NULL"),
        nullable=True,
    )
    component_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    component_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )
    is_present: Mapped[bool] = mapped_column(Boolean, default=True)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    variant_description: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
    )

    # Relationships
    collection_item: Mapped[CollectionItem] = relationship()

    def __repr__(self) -> str:
        return (
            f"<ItemComponent(id={self.id!r}, "
            f"component_name={self.component_name!r})>"
        )
