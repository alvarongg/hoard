"""Pydantic v2 schemas for statistics."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from api.schemas._types import StrUUID


class TimelinePeriod(str, Enum):
    """Grouping period for timeline stats."""

    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ValuationStats(BaseModel):
    """Aggregate valuation figures."""

    total_invested: Decimal
    current_value: Decimal
    value_gain: Decimal
    roi_percentage: Decimal | None = None


class CollectionItemSummary(BaseModel):
    """Lightweight summary of a collection item."""

    id: StrUUID
    collection_id: StrUUID
    condition: str
    current_market_value: Decimal | None = None


class DashboardStats(BaseModel):
    """Top-level dashboard figures."""

    total_collections: int
    total_items: int
    total_invested: Decimal
    current_value: Decimal
    value_gain: Decimal
    roi_percentage: Decimal | None = None
    complete_items: int
    graded_items: int


class CollectionStatsEntry(BaseModel):
    """Per-collection breakdown entry."""

    collection_id: StrUUID
    collection_name: str
    total_items: int
    total_invested: Decimal
    current_value: Decimal
    roi_percentage: Decimal | None = None


class CategoryStatsEntry(BaseModel):
    """Per-category breakdown entry."""

    sub_category_id: StrUUID | None = None
    sub_category_name: str
    item_count: int
    current_value: Decimal


class TimelineEntry(BaseModel):
    """Acquisition timeline bucket."""

    period: str
    item_count: int
    invested: Decimal
