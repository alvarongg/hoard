"""Pydantic v2 schemas for catalog price history validation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# Price history schemas
# ---------------------------------------------------------------------------


class PriceHistoryBase(BaseModel):
    """Shared fields for price history create/read operations."""

    condition: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Condition the price applies to (e.g. mint, good, poor)",
    )
    is_complete: bool = Field(
        default=True,
        description="Whether the price is for a complete item",
    )
    completeness_description: str | None = Field(
        None,
        max_length=200,
        description="Free-text description of completeness",
    )
    price: Decimal = Field(
        ...,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Recorded market price",
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code",
    )
    source: str | None = Field(
        None,
        max_length=200,
        description="Where the price came from (e.g. eBay, PriceCharting)",
    )
    source_url: str | None = Field(
        None,
        max_length=500,
        description="URL of the source",
    )
    price_date: date = Field(
        ...,
        description="Date the price was observed",
    )
    region: str | None = Field(
        None,
        max_length=10,
        description="Region the price applies to",
    )
    notes: str | None = Field(
        None,
        description="Optional free-text notes",
    )


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating a price history record."""


class PriceHistoryResponse(PriceHistoryBase):
    """Schema for reading a price history record."""

    model_config = ConfigDict(from_attributes=True)

    id: StrUUID
    catalog_item_id: StrUUID
    recorded_at: datetime


class LatestPriceEntry(BaseModel):
    """Latest recorded price for a given condition."""

    condition: str
    is_complete: bool
    price: Decimal
    currency: str
    price_date: date
    source: str | None = None


class ValueUpdateResult(BaseModel):
    """Result of refreshing a collection item's market value."""

    updated: bool
    current_market_value: Decimal | None = None
    value_source: str | None = None
    reason: str | None = None
