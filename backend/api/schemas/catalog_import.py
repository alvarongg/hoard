"""Pydantic v2 schemas for catalog import (entity_type='catalog').

This is a sibling flow to the collection JSON import. The envelope carries a
master product catalog and its items, distinct from a user's collection export.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CatalogTargetSubCategory(BaseModel):
    """Where the catalog should be filed. Resolved or created on import."""

    category: str = Field(..., description="Main category name")
    sub_category: str = Field(..., description="Sub-category name")


class CatalogMeta(BaseModel):
    """The `catalog` object inside the envelope."""

    id: str
    name: str
    system: str | None = None
    version: str | None = None
    description: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    target_sub_category: CatalogTargetSubCategory

    model_config = ConfigDict(extra="ignore")


class CatalogItemPayload(BaseModel):
    """A single catalog item in the envelope.

    Maps onto the existing CatalogItem columns; unknown keys are ignored so the
    format can carry forward-compatible extras inside custom_fields.
    """

    external_id: str | None = None
    title: str
    subtitle: str | None = None
    alternate_titles: list[str] | None = None
    region: str | None = None
    language: str | None = None
    language_codes: list[str] | None = None
    developer: str | None = None
    publisher: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    release_date: str | None = None
    related_items_group: str | None = None
    rarity: str | None = None
    production_run: int | None = None
    is_prototype: bool = False
    is_limited_edition: bool = False
    is_promotional: bool = False
    cover_image_url: str | None = None
    custom_fields: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class CatalogEnvelope(BaseModel):
    """Top-level catalog import envelope."""

    schema_version: str
    entity_type: str
    catalog: CatalogMeta
    items: list[CatalogItemPayload] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
