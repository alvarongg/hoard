"""Pydantic v2 schemas for Catalog and CatalogItem validation."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# Catalog schemas
# ---------------------------------------------------------------------------


class CatalogBase(BaseModel):
    """Shared fields for Catalog create/update operations."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the catalog",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the catalog",
    )
    is_active: bool = Field(
        True,
        description="Whether the catalog is active",
    )


class CatalogCreate(CatalogBase):
    """Schema for creating a new catalog."""

    sub_category_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="UUID of the parent sub-category",
    )


class CatalogUpdate(BaseModel):
    """Schema for partially updating a catalog.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Display name of the catalog",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the catalog",
    )
    is_active: bool | None = Field(
        None,
        description="Whether the catalog is active",
    )


class CatalogResponse(CatalogBase):
    """Schema returned when reading a catalog."""

    id: StrUUID = Field(..., description="UUID primary key")
    sub_category_id: StrUUID = Field(
        ..., description="UUID of the parent sub-category"
    )
    total_items: int = Field(0, description="Number of items in the catalog")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CatalogItem schemas
# ---------------------------------------------------------------------------


class CatalogItemBase(BaseModel):
    """Shared fields for CatalogItem create/update operations."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title of the catalog item",
    )
    subtitle: str | None = Field(
        None,
        max_length=500,
        description="Optional subtitle",
    )
    description: str | None = Field(
        None,
        max_length=10000,
        description="Optional detailed description",
    )
    release_date: date | None = Field(
        None,
        description="Release or publication date",
    )
    manufacturer: str | None = Field(
        None,
        max_length=200,
        description="Manufacturer name",
    )
    publisher: str | None = Field(
        None,
        max_length=200,
        description="Publisher name",
    )
    developer: str | None = Field(
        None,
        max_length=200,
        description="Developer name",
    )
    brand: str | None = Field(
        None,
        max_length=200,
        description="Brand name",
    )
    language: str | None = Field(
        None,
        max_length=50,
        description="Primary language",
    )
    region: str | None = Field(
        None,
        max_length=50,
        description="Region code (e.g., NTSC, PAL)",
    )
    rarity: str | None = Field(
        None,
        max_length=50,
        description="Rarity classification",
    )
    custom_fields: dict = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata",
    )
    cover_image_url: str | None = Field(
        None,
        max_length=1000,
        description="URL to the cover image",
    )

    @field_validator("title")
    @classmethod
    def _title_must_not_be_blank(cls, value: str) -> str:
        """Reject titles made only of whitespace characters."""
        if not value.strip():
            raise ValueError("title must not be empty or whitespace-only")
        return value


class CatalogItemCreate(CatalogItemBase):
    """Schema for creating a new catalog item."""

    catalog_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="UUID of the parent catalog",
    )


class CatalogItemUpdate(BaseModel):
    """Schema for partially updating a catalog item.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    title: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description="Title of the catalog item",
    )
    subtitle: str | None = Field(
        None,
        max_length=500,
        description="Optional subtitle",
    )
    description: str | None = Field(
        None,
        max_length=10000,
        description="Optional detailed description",
    )
    release_date: date | None = Field(
        None,
        description="Release or publication date",
    )
    manufacturer: str | None = Field(
        None,
        max_length=200,
        description="Manufacturer name",
    )
    publisher: str | None = Field(
        None,
        max_length=200,
        description="Publisher name",
    )
    developer: str | None = Field(
        None,
        max_length=200,
        description="Developer name",
    )
    brand: str | None = Field(
        None,
        max_length=200,
        description="Brand name",
    )
    language: str | None = Field(
        None,
        max_length=50,
        description="Primary language",
    )
    region: str | None = Field(
        None,
        max_length=50,
        description="Region code (e.g., NTSC, PAL)",
    )
    rarity: str | None = Field(
        None,
        max_length=50,
        description="Rarity classification",
    )
    custom_fields: dict | None = Field(
        None,
        description="Arbitrary key-value metadata",
    )
    cover_image_url: str | None = Field(
        None,
        max_length=1000,
        description="URL to the cover image",
    )


class CatalogItemResponse(CatalogItemBase):
    """Schema returned when reading a catalog item."""

    id: StrUUID = Field(..., description="UUID primary key")
    catalog_id: StrUUID = Field(
        ..., description="UUID of the parent catalog"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
