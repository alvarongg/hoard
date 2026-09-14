"""SQLAlchemy model for catalog price history."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UniqueConstraint

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin


class CatalogPriceHistory(UUIDMixin, Base):
    """Price history model — market price records for catalog items."""

    __tablename__ = "catalog_price_history"
    __table_args__ = (
        UniqueConstraint(
            "catalog_item_id",
            "condition",
            "is_complete",
            "price_date",
            "source",
            name="unique_price_record",
        ),
    )

    catalog_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    completeness_description: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    catalog_item: Mapped["CatalogItem"] = relationship(back_populates="price_history")

    def __repr__(self) -> str:
        return f"<CatalogPriceHistory(id={self.id!r}, price={self.price!r}, price_date={self.price_date!r})>"
