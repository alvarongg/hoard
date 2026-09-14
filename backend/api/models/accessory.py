"""SQLAlchemy models for accessories stock and item components."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Computed, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, DateTime

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from api.models.collection import CollectionItem
    from api.models.supplier import Supplier


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
    quantity_available: Mapped[int] = mapped_column(
        Integer,
        Computed("quantity_total - quantity_in_use", persisted=True),
        nullable=True,
    )
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
    supplier: Mapped[Supplier | None] = relationship(
        back_populates="accessories",
    )
    assignments: Mapped[list["ItemAccessory"]] = relationship(
        back_populates="accessory",
        passive_deletes=True,
    )

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
    collection_item: Mapped[CollectionItem] = relationship(
        back_populates="components",
    )

    def __repr__(self) -> str:
        return (
            f"<ItemComponent(id={self.id!r}, "
            f"component_name={self.component_name!r})>"
        )


class ItemAccessory(UUIDMixin, Base):
    """Association between collection items and the accessories they use."""

    __tablename__ = "item_accessories"
    __table_args__ = (
        UniqueConstraint(
            "collection_item_id",
            "accessory_id",
            name="uq_item_accessory",
        ),
    )

    collection_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    accessory_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("accessories_stock.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_used: Mapped[int] = mapped_column(Integer, default=1)
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        server_default=func.now(),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    accessory: Mapped[AccessoryStock] = relationship(
        back_populates="assignments",
    )
    collection_item: Mapped[CollectionItem] = relationship(
        back_populates="accessories",
    )

    def __repr__(self) -> str:
        return (
            f"<ItemAccessory(id={self.id!r}, "
            f"accessory_id={self.accessory_id!r})>"
        )
