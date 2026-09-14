"""Schemas for advanced catalog search.

Requirements: 6.4, 6.5, 6.8
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    """Search mode used for the query."""

    FULL_TEXT = "full_text"
    FUZZY = "fuzzy"
    DEGRADED = "degraded"


class CatalogSearchParams(BaseModel):
    """Parameters for catalog item search."""

    q: Optional[str] = Field(None, description="Search query string")
    main_category_id: Optional[str] = Field(None, description="Filter by main category UUID")
    sub_category_id: Optional[str] = Field(None, description="Filter by sub-category UUID")
    language: Optional[str] = Field(None, description="Filter by language")
    region: Optional[str] = Field(None, description="Filter by region")
    manufacturer: Optional[str] = Field(None, description="Filter by manufacturer")
    publisher: Optional[str] = Field(None, description="Filter by publisher")
    developer: Optional[str] = Field(None, description="Filter by developer")
    brand: Optional[str] = Field(None, description="Filter by brand")
    rarity: Optional[str] = Field(None, description="Filter by rarity")
    year_min: Optional[int] = Field(
        None,
        ge=1800,
        le=2200,
        description="Minimum release year (inclusive)",
    )
    year_max: Optional[int] = Field(
        None,
        ge=1800,
        le=2200,
        description="Maximum release year (inclusive)",
    )
    skip: int = Field(0, ge=0, description="Number of results to skip")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of results")


class CatalogSearchResultItem(BaseModel):
    """A single catalog item in search results."""

    id: str
    title: str
    subtitle: Optional[str] = None
    catalog_id: str


class CatalogSearchResult(BaseModel):
    """Result of a catalog search."""

    items: list[CatalogSearchResultItem]
    total: int
    search_mode: SearchMode
