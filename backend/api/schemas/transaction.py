"""Pydantic v2 schemas for item transaction validation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.schemas._types import StrUUID


TRANSACTION_TYPES = frozenset(
    {
        "purchase",
        "sale",
        "trade_in",
        "trade_out",
        "gift_received",
        "gift_given",
        "grading_fee",
        "repair",
        "appraisal",
        "other",
    }
)


class TransactionBase(BaseModel):
    """Shared fields for transaction create/read operations."""

    transaction_type: str = Field(..., max_length=50)
    transaction_date: date = Field(...)
    amount: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    shipping_cost: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    tax_amount: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    other_fees: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    supplier_id: StrUUID | None = Field(None)
    counterpart_name: str | None = Field(None, max_length=200)
    invoice_number: str | None = Field(None, max_length=100)
    receipt_path: str | None = Field(None, max_length=500)
    payment_method: str | None = Field(None, max_length=50)
    notes: str | None = Field(None)

    @field_validator("transaction_type")
    @classmethod
    def _type_allowed(cls, v: str) -> str:
        if v not in TRANSACTION_TYPES:
            allowed = ", ".join(sorted(TRANSACTION_TYPES))
            raise ValueError(f"transaction_type must be one of: {allowed}")
        return v


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction (no total_amount)."""


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction (all optional, no total_amount)."""

    transaction_type: str | None = Field(None, max_length=50)
    transaction_date: date | None = Field(None)
    amount: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    currency: str | None = Field(None, min_length=3, max_length=3)
    shipping_cost: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    tax_amount: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    other_fees: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    supplier_id: StrUUID | None = Field(None)
    counterpart_name: str | None = Field(None, max_length=200)
    invoice_number: str | None = Field(None, max_length=100)
    receipt_path: str | None = Field(None, max_length=500)
    payment_method: str | None = Field(None, max_length=50)
    notes: str | None = Field(None)

    @field_validator("transaction_type")
    @classmethod
    def _type_allowed(cls, v: str | None) -> str | None:
        if v is not None and v not in TRANSACTION_TYPES:
            allowed = ", ".join(sorted(TRANSACTION_TYPES))
            raise ValueError(f"transaction_type must be one of: {allowed}")
        return v


class TransactionResponse(TransactionBase):
    """Schema for reading a transaction, with read-only total_amount."""

    model_config = ConfigDict(from_attributes=True)

    id: StrUUID
    collection_item_id: StrUUID
    total_amount: Decimal
    created_at: datetime


class ItemInvestment(BaseModel):
    """Investment summary for a collection item."""

    real_invested: Decimal
    total_outflow: Decimal
    total_inflow: Decimal
    current_market_value: Decimal | None = None
    roi_percentage: Decimal | None = None
    source: str
