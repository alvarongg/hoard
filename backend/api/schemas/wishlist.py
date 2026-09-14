"""Pydantic v2 schemas for Wishlist items and Sightings."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from api.schemas._types import StrUUID
from api.schemas.collection_item import CollectionItemCreate


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

VALID_URGENCY = frozenset({"low", "medium", "high", "critical"})
VALID_DECISIONS = frozenset({"buy", "pass", "wait", "negotiate"})


# ---------------------------------------------------------------------------
# WishlistItem schemas
# ---------------------------------------------------------------------------


class WishlistItemBase(BaseModel):
    """Shared fields for WishlistItem create/read operations."""

    desired_condition: str | None = Field(
        None,
        max_length=50,
        description="Desired condition (e.g., 'new', 'like_new', 'good', 'acceptable')",
    )
    desired_condition_min: str | None = Field(
        None,
        max_length=50,
        description="Minimum acceptable condition",
    )
    must_be_complete: bool = Field(
        True,
        description="Whether the item must be complete",
    )
    desired_completeness_description: str | None = Field(
        None,
        description="Description of desired completeness requirements",
    )
    max_price: Decimal | None = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Maximum price willing to pay",
    )
    currency: str = Field(
        "USD",
        max_length=3,
        description="ISO 4217 currency code",
    )
    specific_variant_required: bool = Field(
        False,
        description="Whether a specific variant is required",
    )
    variant_description: str | None = Field(
        None,
        max_length=200,
        description="Description of the required variant",
    )
    priority: int = Field(
        3,
        ge=1,
        le=5,
        description="Priority from 1 (highest) to 5 (lowest)",
    )
    urgency: str = Field(
        "medium",
        max_length=50,
        description="Urgency level: low, medium, high, or critical",
    )
    notes: str | None = Field(
        None,
        description="General notes about the wishlist item",
    )
    search_notes: str | None = Field(
        None,
        description="Notes to help with searching",
    )
    tags: list[str] | None = Field(
        None,
        description="Tags for categorization and filtering",
    )
    is_active: bool = Field(
        True,
        description="Whether this wishlist item is actively being sought",
    )

    @field_validator("urgency")
    @classmethod
    def _validate_urgency(cls, value: str) -> str:
        """Validate urgency is one of the allowed values."""
        if value not in VALID_URGENCY:
            allowed = ", ".join(sorted(VALID_URGENCY))
            raise ValueError(f"urgency must be one of: {allowed}")
        return value


class WishlistItemCreate(WishlistItemBase):
    """Schema for creating a new wishlist item."""

    collection_id: StrUUID = Field(
        ...,
        description="UUID of the collection this item is for",
    )
    catalog_item_id: StrUUID = Field(
        ...,
        description="UUID of the catalog item being wished for",
    )


class WishlistItemUpdate(BaseModel):
    """Schema for partially updating a wishlist item.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    desired_condition: str | None = Field(
        None,
        max_length=50,
        description="Desired condition",
    )
    desired_condition_min: str | None = Field(
        None,
        max_length=50,
        description="Minimum acceptable condition",
    )
    must_be_complete: bool | None = Field(
        None,
        description="Whether the item must be complete",
    )
    desired_completeness_description: str | None = Field(
        None,
        description="Description of desired completeness requirements",
    )
    max_price: Decimal | None = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Maximum price willing to pay",
    )
    currency: str | None = Field(
        None,
        max_length=3,
        description="ISO 4217 currency code",
    )
    specific_variant_required: bool | None = Field(
        None,
        description="Whether a specific variant is required",
    )
    variant_description: str | None = Field(
        None,
        max_length=200,
        description="Description of the required variant",
    )
    priority: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Priority from 1 (highest) to 5 (lowest)",
    )
    urgency: str | None = Field(
        None,
        max_length=50,
        description="Urgency level",
    )
    notes: str | None = Field(
        None,
        description="General notes",
    )
    search_notes: str | None = Field(
        None,
        description="Notes to help with searching",
    )
    tags: list[str] | None = Field(
        None,
        description="Tags for categorization",
    )
    is_active: bool | None = Field(
        None,
        description="Whether this item is actively being sought",
    )

    @field_validator("urgency")
    @classmethod
    def _validate_urgency(cls, value: str | None) -> str | None:
        """Validate urgency is one of the allowed values."""
        if value is not None and value not in VALID_URGENCY:
            allowed = ", ".join(sorted(VALID_URGENCY))
            raise ValueError(f"urgency must be one of: {allowed}")
        return value


class WishlistItemResponse(WishlistItemBase):
    """Schema returned when reading a wishlist item."""

    id: StrUUID = Field(..., description="UUID primary key")
    collection_id: StrUUID = Field(..., description="UUID of the collection")
    catalog_item_id: StrUUID = Field(..., description="UUID of the catalog item")
    is_acquired: bool = Field(False, description="Whether the item has been acquired")
    acquired_date: date | None = Field(None, description="Date the item was acquired")
    acquired_collection_item_id: StrUUID | None = Field(
        None, description="UUID of the resulting collection item"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Price aggregates schema
# ---------------------------------------------------------------------------


class PriceAggregates(BaseModel):
    """Aggregated price statistics from sightings."""

    avg_price: Decimal | None = Field(None, description="Average price from sightings")
    min_price: Decimal | None = Field(None, description="Minimum price seen")
    max_price: Decimal | None = Field(None, description="Maximum price seen")
    total_sightings: int = Field(0, description="Total number of sightings")
    available_sightings: int = Field(
        0, description="Number of sightings with items available"
    )


# ---------------------------------------------------------------------------
# WishlistItem detail with aggregates
# ---------------------------------------------------------------------------


class WishlistItemDetail(WishlistItemResponse):
    """Wishlist item response with price aggregates."""

    price_aggregates: PriceAggregates = Field(
        default_factory=PriceAggregates,
        description="Aggregated price statistics",
    )


# ---------------------------------------------------------------------------
# Wishlist acquire schema
# ---------------------------------------------------------------------------


class WishlistAcquire(BaseModel):
    """Schema for marking a wishlist item as acquired."""

    acquired_collection_item_id: StrUUID = Field(
        ...,
        description="UUID of the collection item created from this acquisition",
    )


class WishlistAcquireAndAdd(BaseModel):
    """Create a collection item from a wishlist item ("ya lo conseguí").

    The collection and catalog item are taken from the wishlist item; the
    collection_item payload's catalog_item_id is ignored/overridden.
    """

    collection_item: "CollectionItemCreate" = Field(
        ..., description="Collection-item data to create"
    )
    remove_from_wishlist: bool = Field(
        False,
        description="If true, deactivate the wishlist item after acquiring",
    )


# ---------------------------------------------------------------------------
# Sighting schemas
# ---------------------------------------------------------------------------


class SightingBase(BaseModel):
    """Shared fields for Sighting create/read operations."""

    sighted_at: datetime | None = Field(
        None,
        description="When the item was sighted",
    )
    supplier_id: StrUUID | None = Field(
        None,
        description="UUID of the supplier where sighted",
    )
    location_description: str | None = Field(
        None,
        max_length=500,
        description="Description of the location",
    )
    url: str | None = Field(
        None,
        max_length=1000,
        description="URL to the listing",
    )
    price: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Price of the item at sighting",
    )
    currency: str = Field(
        "USD",
        max_length=3,
        description="ISO 4217 currency code",
    )
    condition: str | None = Field(
        None,
        max_length=50,
        description="Condition of the item",
    )
    is_complete: bool | None = Field(
        None,
        description="Whether the item is complete",
    )
    description: str | None = Field(
        None,
        description="Description of the sighting",
    )
    image_urls: list[str] | None = Field(
        None,
        description="URLs to images of the item",
    )
    is_available: bool = Field(
        True,
        description="Whether the item is still available",
    )
    quantity_available: int = Field(
        1,
        ge=0,
        description="Number of items available",
    )
    last_checked_at: datetime | None = Field(
        None,
        description="When availability was last checked",
    )
    contacted: bool = Field(
        False,
        description="Whether the seller has been contacted",
    )
    contacted_at: datetime | None = Field(
        None,
        description="When the seller was contacted",
    )
    contact_method: str | None = Field(
        None,
        max_length=50,
        description="Method of contact",
    )
    response_notes: str | None = Field(
        None,
        description="Notes from seller response",
    )
    decision: str | None = Field(
        None,
        max_length=50,
        description="Decision: buy, pass, wait, negotiate",
    )
    decision_notes: str | None = Field(
        None,
        description="Notes about the decision",
    )
    decision_date: date | None = Field(
        None,
        description="Date the decision was made",
    )

    @field_validator("decision")
    @classmethod
    def _validate_decision(cls, value: str | None) -> str | None:
        """Validate decision is one of the allowed values."""
        if value is not None and value not in VALID_DECISIONS:
            allowed = ", ".join(sorted(VALID_DECISIONS))
            raise ValueError(f"decision must be one of: {allowed}")
        return value


class SightingCreate(SightingBase):
    """Schema for creating a new sighting."""

    wishlist_item_id: StrUUID = Field(
        ...,
        description="UUID of the wishlist item being sighted",
    )


class SightingBody(SightingBase):
    """Schema for sighting creation body (without wishlist_item_id in body)."""

    pass


class SightingUpdate(BaseModel):
    """Schema for partially updating a sighting.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    sighted_at: datetime | None = Field(None, description="When the item was sighted")
    supplier_id: StrUUID | None = Field(
        None, description="UUID of the supplier where sighted"
    )
    location_description: str | None = Field(
        None, max_length=500, description="Description of the location"
    )
    url: str | None = Field(None, max_length=1000, description="URL to the listing")
    price: Decimal | None = Field(
        None, ge=0, decimal_places=2, description="Price of the item"
    )
    currency: str | None = Field(
        None, max_length=3, description="ISO 4217 currency code"
    )
    condition: str | None = Field(None, max_length=50, description="Condition")
    is_complete: bool | None = Field(None, description="Whether complete")
    description: str | None = Field(None, description="Description")
    image_urls: list[str] | None = Field(None, description="Image URLs")
    is_available: bool | None = Field(None, description="Whether available")
    quantity_available: int | None = Field(
        None, ge=0, description="Number available"
    )
    last_checked_at: datetime | None = Field(
        None, description="When last checked"
    )
    contacted: bool | None = Field(None, description="Whether contacted")
    contacted_at: datetime | None = Field(None, description="When contacted")
    contact_method: str | None = Field(None, max_length=50, description="Contact method")
    response_notes: str | None = Field(None, description="Response notes")
    decision: str | None = Field(None, max_length=50, description="Decision")
    decision_notes: str | None = Field(None, description="Decision notes")
    decision_date: date | None = Field(None, description="Decision date")

    @field_validator("decision")
    @classmethod
    def _validate_decision(cls, value: str | None) -> str | None:
        """Validate decision is one of the allowed values."""
        if value is not None and value not in VALID_DECISIONS:
            allowed = ", ".join(sorted(VALID_DECISIONS))
            raise ValueError(f"decision must be one of: {allowed}")
        return value


class SightingResponse(SightingBase):
    """Schema returned when reading a sighting."""

    id: StrUUID = Field(..., description="UUID primary key")
    wishlist_item_id: StrUUID = Field(
        ..., description="UUID of the wishlist item"
    )
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)
