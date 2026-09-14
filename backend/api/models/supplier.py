"""SQLAlchemy model for suppliers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from api.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from api.models.accessory import AccessoryStock
    from api.models.collection import CollectionItem
    from api.models.wishlist import WishlistSighting


class Supplier(UUIDMixin, TimestampMixin, Base):
    """Supplier model — stores, sellers, marketplaces."""

    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Location
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    state_province: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
    )

    # Contact
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Social / Marketplace
    marketplace_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )
    social_media: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    rating: Mapped[float | None] = mapped_column(
        Numeric(3, 2), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    collection_items: Mapped[list[CollectionItem]] = relationship(
        back_populates="supplier",
    )
    sightings: Mapped[list[WishlistSighting]] = relationship(
        back_populates="supplier",
    )
    accessories: Mapped[list[AccessoryStock]] = relationship(
        back_populates="supplier",
    )

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id!r}, name={self.name!r})>"
