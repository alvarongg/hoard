"""SQLAlchemy models for collections and collection items."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from api.models.accessory import ItemAccessory, ItemComponent
    from api.models.catalog import CatalogItem
    from api.models.supplier import Supplier
    from api.models.transaction import ItemTransaction


class Collection(UUIDMixin, TimestampMixin, Base):
    """Personal collection model — single_category, multi_category, or mixed."""

    __tablename__ = "collections"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    collection_type: Mapped[str] = mapped_column(
        String(50), default="single_category",
    )
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    theme_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    restricted_to_sub_category_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("sub_categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    goal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_items_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_order: Mapped[str] = mapped_column(String(50), default="custom")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    items: Mapped[list[CollectionItem]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    restricted_sub_category: Mapped[SubCategory | None] = relationship()

    def __repr__(self) -> str:
        return f"<Collection(id={self.id!r}, name={self.name!r})>"


class CollectionItem(UUIDMixin, TimestampMixin, Base):
    """Collection item model — a real item the user owns in a collection."""

    __tablename__ = "collection_items"

    collection_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    catalog_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("catalog_items.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Override / notes
    title_override: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Condition
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Completeness
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    completeness_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Variant
    variant_description: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
    )

    # Authenticity
    is_authentic: Mapped[bool] = mapped_column(Boolean, default=True)
    authenticity_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Storage
    storage_location: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
    )
    storage_position: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )

    # Purchase / value
    purchase_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    purchase_currency: Mapped[str] = mapped_column(
        String(3), default="USD",
    )
    purchase_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    current_market_value: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    current_value_currency: Mapped[str] = mapped_column(
        String(3), default="USD",
    )
    last_value_update: Mapped[str | None] = mapped_column(
        DateTime, nullable=True,
    )
    value_source: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Acquisition
    acquisition_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    acquisition_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )
    supplier_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Grading
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    grading_company: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    certification_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    grading_date: Mapped[str | None] = mapped_column(Date, nullable=True)

    # Insurance
    is_insured: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_value: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    insurance_company: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
    )

    # Custom / tags / sale
    custom_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    for_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    asking_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )

    # Relationships
    collection: Mapped[Collection] = relationship(back_populates="items")
    catalog_item: Mapped[CatalogItem] = relationship()
    supplier: Mapped[Supplier | None] = relationship(back_populates="collection_items")
    components: Mapped[list[ItemComponent]] = relationship(
        back_populates="collection_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    transactions: Mapped[list[ItemTransaction]] = relationship(
        back_populates="collection_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    accessories: Mapped[list[ItemAccessory]] = relationship(
        back_populates="collection_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<CollectionItem(id={self.id!r}, collection_id={self.collection_id!r})>"
