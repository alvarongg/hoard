"""Pydantic v2 schemas for Supplier validation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

SUPPLIER_TYPES = frozenset(
    {"online", "physical_store", "marketplace", "private_seller", "auction"}
)


# ---------------------------------------------------------------------------
# Supplier schemas
# ---------------------------------------------------------------------------


class SupplierBase(BaseModel):
    """Shared fields for Supplier create/read operations."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the supplier",
    )
    type: str | None = Field(
        None,
        max_length=50,
        description="Type of supplier (online, physical_store, marketplace, private_seller, auction)",
    )
    country: str | None = Field(
        None,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
    )
    state_province: str | None = Field(
        None,
        max_length=100,
        description="State or province name",
    )
    city: str | None = Field(
        None,
        max_length=100,
        description="City name",
    )
    address: str | None = Field(
        None,
        description="Full street address",
    )
    postal_code: str | None = Field(
        None,
        max_length=20,
        description="Postal or ZIP code",
    )
    website: str | None = Field(
        None,
        max_length=500,
        description="Website URL",
    )
    email: EmailStr | None = Field(
        None,
        description="Contact email address",
    )
    phone: str | None = Field(
        None,
        max_length=50,
        description="Contact phone number",
    )
    marketplace_url: str | None = Field(
        None,
        max_length=500,
        description="URL to supplier's marketplace profile",
    )
    social_media: dict | None = Field(
        None,
        description="Social media handles and links",
    )
    rating: Decimal | None = Field(
        None,
        ge=0,
        le=5,
        decimal_places=2,
        description="Supplier rating from 0.00 to 5.00",
    )
    notes: str | None = Field(
        None,
        description="Free-form notes about the supplier",
    )
    is_favorite: bool = Field(
        False,
        description="Whether the supplier is marked as favorite",
    )
    is_active: bool = Field(
        True,
        description="Whether the supplier is active",
    )

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        """Reject names made only of whitespace characters."""
        if not value.strip():
            raise ValueError("name must not be empty or whitespace-only")
        return value

    @field_validator("type")
    @classmethod
    def _type_allowed(cls, value: str | None) -> str | None:
        """Validate that supplier type is one of the allowed values."""
        if value is not None and value not in SUPPLIER_TYPES:
            allowed = ", ".join(sorted(SUPPLIER_TYPES))
            raise ValueError(f"type must be one of: {allowed}")
        return value


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier."""

    pass


class SupplierUpdate(BaseModel):
    """Schema for partially updating a supplier.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Display name of the supplier",
    )
    type: str | None = Field(
        None,
        max_length=50,
        description="Type of supplier",
    )
    country: str | None = Field(
        None,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
    )
    state_province: str | None = Field(
        None,
        max_length=100,
        description="State or province name",
    )
    city: str | None = Field(
        None,
        max_length=100,
        description="City name",
    )
    address: str | None = Field(
        None,
        description="Full street address",
    )
    postal_code: str | None = Field(
        None,
        max_length=20,
        description="Postal or ZIP code",
    )
    website: str | None = Field(
        None,
        max_length=500,
        description="Website URL",
    )
    email: EmailStr | None = Field(
        None,
        description="Contact email address",
    )
    phone: str | None = Field(
        None,
        max_length=50,
        description="Contact phone number",
    )
    marketplace_url: str | None = Field(
        None,
        max_length=500,
        description="URL to supplier's marketplace profile",
    )
    social_media: dict | None = Field(
        None,
        description="Social media handles and links",
    )
    rating: Decimal | None = Field(
        None,
        ge=0,
        le=5,
        decimal_places=2,
        description="Supplier rating from 0.00 to 5.00",
    )
    notes: str | None = Field(
        None,
        description="Free-form notes about the supplier",
    )
    is_favorite: bool | None = Field(
        None,
        description="Whether the supplier is marked as favorite",
    )
    is_active: bool | None = Field(
        None,
        description="Whether the supplier is active",
    )

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str | None) -> str | None:
        """Reject names made only of whitespace characters."""
        if value is not None and not value.strip():
            raise ValueError("name must not be empty or whitespace-only")
        return value

    @field_validator("type")
    @classmethod
    def _type_allowed(cls, value: str | None) -> str | None:
        """Validate that supplier type is one of the allowed values."""
        if value is not None and value not in SUPPLIER_TYPES:
            allowed = ", ".join(sorted(SUPPLIER_TYPES))
            raise ValueError(f"type must be one of: {allowed}")
        return value


class SupplierResponse(SupplierBase):
    """Schema returned when reading a supplier."""

    id: StrUUID = Field(..., description="UUID primary key")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Purchase history schema
# ---------------------------------------------------------------------------


class SupplierPurchase(BaseModel):
    """Schema for a purchase made from a supplier."""

    collection_item_id: StrUUID = Field(
        ..., description="UUID of the purchased collection item"
    )
    title: str = Field(..., description="Title of the purchased item")
    purchase_date: date | None = Field(
        None, description="Date of purchase"
    )
    purchase_price: Decimal | None = Field(
        None, description="Purchase price"
    )
    purchase_currency: str = Field(
        "USD", description="Currency of the purchase price"
    )

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# References schema
# ---------------------------------------------------------------------------


class SupplierReferences(BaseModel):
    """Schema for counting supplier references across entities."""

    collection_items: int = Field(
        0, description="Number of collection items referencing this supplier"
    )
    wishlist_sightings: int = Field(
        0, description="Number of wishlist sightings referencing this supplier"
    )
    accessories: int = Field(
        0, description="Number of accessories referencing this supplier"
    )

    @property
    def total(self) -> int:
        """Total number of references across all entities."""
        return self.collection_items + self.wishlist_sightings + self.accessories
