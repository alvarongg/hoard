"""Pydantic v2 schemas for CollectionItem validation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# CollectionItem schemas
# ---------------------------------------------------------------------------

VALID_CONDITIONS = Literal["mint", "near_mint", "excellent", "good", "fair", "poor"]
VALID_ACQUISITION_TYPES = Literal["purchase", "gift", "trade", "found", "inherited"]


class CollectionItemBase(BaseModel):
    """Shared fields for CollectionItem create operations."""

    catalog_item_id: str = Field(
        ...,
        description="UUID of the catalog item being added to the collection",
    )
    condition: VALID_CONDITIONS = Field(
        ...,
        description="Physical condition of the item",
    )
    is_complete: bool = Field(
        False,
        description="Whether the item is complete with all parts",
    )
    notes: str | None = Field(
        None,
        description="Optional notes about the item",
    )
    purchase_price: Decimal | None = Field(
        None,
        ge=0,
        description="Purchase price of the item",
    )
    purchase_currency: str = Field(
        "USD",
        max_length=3,
        description="Currency code for the purchase price",
    )
    purchase_date: date | None = Field(
        None,
        description="Date the item was purchased",
    )
    acquisition_type: VALID_ACQUISITION_TYPES | None = Field(
        None,
        description="How the item was acquired",
    )
    storage_location: str | None = Field(
        None,
        max_length=200,
        description="Where the item is stored",
    )


class CollectionItemCreate(CollectionItemBase):
    """Schema for adding an item to a collection."""

    pass


class CollectionItemUpdate(BaseModel):
    """Schema for partially updating a collection item.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    condition: VALID_CONDITIONS | None = Field(
        None,
        description="Physical condition of the item",
    )
    is_complete: bool | None = Field(
        None,
        description="Whether the item is complete with all parts",
    )
    notes: str | None = Field(
        None,
        description="Optional notes about the item",
    )
    purchase_price: Decimal | None = Field(
        None,
        ge=0,
        description="Purchase price of the item",
    )
    purchase_currency: str | None = Field(
        None,
        max_length=3,
        description="Currency code for the purchase price",
    )
    purchase_date: date | None = Field(
        None,
        description="Date the item was purchased",
    )
    acquisition_type: VALID_ACQUISITION_TYPES | None = Field(
        None,
        description="How the item was acquired",
    )
    storage_location: str | None = Field(
        None,
        max_length=200,
        description="Where the item is stored",
    )


class CollectionItemResponse(BaseModel):
    """Schema returned when reading a collection item."""

    id: StrUUID = Field(..., description="UUID primary key")
    collection_id: StrUUID = Field(..., description="UUID of the parent collection")
    catalog_item_id: StrUUID = Field(..., description="UUID of the catalog item")
    condition: str = Field(..., description="Physical condition of the item")
    is_complete: bool = Field(..., description="Whether the item is complete")
    notes: str | None = Field(None, description="Optional notes")
    purchase_price: Decimal | None = Field(None, description="Purchase price")
    purchase_currency: str = Field("USD", description="Currency code")
    purchase_date: date | None = Field(None, description="Purchase date")
    acquisition_type: str | None = Field(None, description="Acquisition type")
    storage_location: str | None = Field(None, description="Storage location")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
