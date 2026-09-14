"""Pydantic v2 schemas for data export envelopes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportEnvelope(BaseModel):
    """Common metadata wrapping every export payload."""

    schema_version: str
    entity_type: str
    exported_at: datetime
    source: str = "hoard"


class CollectionItemExport(BaseModel):
    """A collection item with its components, for export."""

    id: str
    catalog_item_id: str
    condition: str
    is_complete: bool
    purchase_price: str | None = None
    components: list[dict[str, Any]] = Field(default_factory=list)


class CollectionExport(ExportEnvelope):
    """Full export of a collection."""

    collection: dict[str, Any]
    items: list[CollectionItemExport] = Field(default_factory=list)
    catalog_items: list[dict[str, Any]] = Field(default_factory=list)


class CatalogExport(ExportEnvelope):
    """Full export of a catalog."""

    catalog: dict[str, Any]
    items: list[dict[str, Any]] = Field(default_factory=list)


class WishlistExport(ExportEnvelope):
    """Full export of the wishlist."""

    items: list[dict[str, Any]] = Field(default_factory=list)
