"""SQLAlchemy models for catalogs and catalog items."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin


class Catalog(UUIDMixin, TimestampMixin, Base):
    """Catalog model — master product catalog (e.g., 'All N64 Games')."""

    __tablename__ = "catalogs"

    sub_category_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("sub_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    sub_category: Mapped[SubCategory] = relationship()
    items: Mapped[list[CatalogItem]] = relationship(
        back_populates="catalog",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Catalog(id={self.id!r}, name={self.name!r})>"


class CatalogItem(UUIDMixin, TimestampMixin, Base):
    """Catalog item model — each version/language/variation is a unique record."""

    __tablename__ = "catalog_items"

    catalog_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("catalogs.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alternate_titles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ean: Mapped[str | None] = mapped_column(String(50), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    version_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    variation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    variation_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_items_group: Mapped[str | None] = mapped_column(
        DBUUID(), nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    developer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    standard_components_included: Mapped[list | None] = mapped_column(
        JSON, nullable=True,
    )
    cover_image_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True,
    )
    images: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rarity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    production_run: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_limited_edition: Mapped[bool] = mapped_column(Boolean, default=False)
    is_promotional: Mapped[bool] = mapped_column(Boolean, default=False)
    is_prototype: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    catalog: Mapped[Catalog] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<CatalogItem(id={self.id!r}, title={self.title!r})>"
