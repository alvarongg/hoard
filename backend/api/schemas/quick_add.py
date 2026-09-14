"""Schemas for quick-add flows (supplier, catalog, catalog item)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from api.schemas.collection_item import CollectionItemCreate


class SupplierQuickAdd(BaseModel):
    """Minimal supplier creation: name (+ optional country)."""

    name: str = Field(..., min_length=1, max_length=200)
    country: str | None = Field(
        None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2"
    )


class CatalogQuickAdd(BaseModel):
    """Minimal catalog creation: name + tematica (theme)."""

    name: str = Field(..., min_length=1, max_length=200)
    tematica: str = Field(
        ..., min_length=1, max_length=100, description="Theme / topic"
    )
    is_primary: bool = Field(
        False, description="Mark as the collection's primary catalog"
    )


class CatalogItemQuickAdd(BaseModel):
    """Create a minimal catalog item AND a collection item in one call."""

    catalog_id: str = Field(
        ..., description="Catalog (already associated) to create the item in"
    )
    title: str = Field(..., min_length=1, max_length=500)
    collection_item: CollectionItemCreate = Field(
        ...,
        description="Collection-item data; its catalog_item_id is ignored "
        "and replaced by the newly created catalog item",
    )
