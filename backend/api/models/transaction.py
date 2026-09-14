"""SQLAlchemy model for item transactions."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Computed, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin


class ItemTransaction(UUIDMixin, Base):
    """Transaction record for a collection item.

    Tracks purchases, sales, grading, repairs, appraisals, and other
    financial movements related to a collection item.
    """

    __tablename__ = "item_transactions"

    collection_item_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    shipping_cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    tax_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    other_fees: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        Computed(
            "COALESCE(amount,0)+COALESCE(shipping_cost,0)+COALESCE(tax_amount,0)+COALESCE(other_fees,0)",
            persisted=True,
        ),
        nullable=False,
    )
    supplier_id: Mapped[str | None] = mapped_column(
        DBUUID(),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    counterpart_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    collection_item: Mapped[CollectionItem] = relationship(
        back_populates="transactions",
    )
    supplier: Mapped[Supplier | None] = relationship()

    def __repr__(self) -> str:
        return f"<ItemTransaction(id={self.id!r}, type={self.transaction_type!r})>"


# Import these here to avoid circular imports at module level
# The relationships need forward references
from api.models.collection import CollectionItem  # noqa: E402, F401
from api.models.supplier import Supplier  # noqa: E402, F401
