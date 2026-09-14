"""SQLAlchemy models for wishlist items and sightings."""

from __future__ import annotations

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


class WishlistItem(UUIDMixin, TimestampMixin, Base):
    """An item the user wants to acquire for a collection."""

    __tablename__ = "wishlist_items"

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

    # Desired condition
    desired_condition: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )
    desired_condition_min: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )

    # Completeness
    must_be_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    desired_completeness_description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # Budget
    max_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Variant
    specific_variant_required: Mapped[bool] = mapped_column(
        Boolean, default=False,
    )
    variant_description: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
    )

    # Priority & urgency
    priority: Mapped[int] = mapped_column(Integer, default=3)
    urgency: Mapped[str] = mapped_column(String(50), default="medium")

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_acquired: Mapped[bool] = mapped_column(Boolean, default=False)
    acquired_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    acquired_collection_item_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("collection_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    collection: Mapped[Collection] = relationship()
    catalog_item: Mapped[CatalogItem] = relationship()
    acquired_collection_item: Mapped[CollectionItem | None] = relationship(
        foreign_keys=[acquired_collection_item_id],
    )
    sightings: Mapped[list[WishlistSighting]] = relationship(
        back_populates="wishlist_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<WishlistItem(id={self.id!r}, collection_id={self.collection_id!r})>"


class WishlistSighting(UUIDMixin, Base):
    """A sighting of a wishlist item at a supplier or location."""

    __tablename__ = "wishlist_sightings"

    wishlist_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("wishlist_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    sighted_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True,
    )

    # Source
    supplier_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    location_description: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Price & condition
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_complete: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    quantity_available: Mapped[int] = mapped_column(Integer, default=1)
    last_checked_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True,
    )

    # Contact
    contacted: Mapped[bool] = mapped_column(Boolean, default=False)
    contacted_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True,
    )
    contact_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )
    response_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Decision
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_date: Mapped[str | None] = mapped_column(Date, nullable=True)

    # Timestamp
    created_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True,
    )

    # Relationships
    wishlist_item: Mapped[WishlistItem] = relationship(
        back_populates="sightings",
    )
    supplier: Mapped[Supplier | None] = relationship(
        back_populates="sightings",
    )

    def __repr__(self) -> str:
        return (
            f"<WishlistSighting(id={self.id!r}, "
            f"wishlist_item_id={self.wishlist_item_id!r})>"
        )
