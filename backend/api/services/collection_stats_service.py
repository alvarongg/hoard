"""Business logic for collection statistics."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import CatalogItem
from api.models.category import SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.collection import CollectionStats
from core.dialect import supports_views
from utils.computations import roi_percentage


class CollectionStatsService:
    """Handles statistics calculations for collections."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_collection_stats(
        self, collection_id: str
    ) -> CollectionStats:
        """Return statistics for a collection.

        Args:
            collection_id: UUID of the collection.

        Returns:
            CollectionStats with total_items, categories, investment, value, ROI.

        Raises:
            NotFoundError: If the collection does not exist.
        """
        # Verify collection exists
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            from core.exceptions import NotFoundError
            raise NotFoundError(f"Collection '{collection_id}' not found")

        if supports_views(self._db):
            return await self._stats_from_view(collection_id)
        else:
            return await self._stats_from_queries(collection_id)

    async def _stats_from_view(self, collection_id: str) -> CollectionStats:
        """Get stats from v_collection_stats view (PostgreSQL)."""
        # For now, fall back to queries since view may not exist
        return await self._stats_from_queries(collection_id)

    async def _stats_from_queries(self, collection_id: str) -> CollectionStats:
        """Calculate stats from direct queries (SQLite fallback)."""
        # Total items
        total_stmt = select(func.count(CollectionItem.id)).where(
            CollectionItem.collection_id == collection_id
        )
        total_result = await self._db.execute(total_stmt)
        total_items = total_result.scalar() or 0

        # Distinct categories (via Catalog -> SubCategory)
        from api.models.catalog import Catalog

        cat_stmt = (
            select(func.count(func.distinct(Catalog.sub_category_id)))
            .select_from(CollectionItem)
            .join(CatalogItem, CollectionItem.catalog_item_id == CatalogItem.id)
            .join(Catalog, CatalogItem.catalog_id == Catalog.id)
            .where(CollectionItem.collection_id == collection_id)
        )
        cat_result = await self._db.execute(cat_stmt)
        different_categories_count = cat_result.scalar() or 0

        # Total invested (sum of purchase_price)
        invest_stmt = select(
            func.coalesce(func.sum(CollectionItem.purchase_price), 0)
        ).where(CollectionItem.collection_id == collection_id)
        invest_result = await self._db.execute(invest_stmt)
        total_invested_raw = invest_result.scalar() or 0
        total_invested = float(total_invested_raw) if total_invested_raw else None

        # Current value (sum of current_market_value)
        value_stmt = select(
            func.coalesce(func.sum(CollectionItem.current_market_value), 0)
        ).where(CollectionItem.collection_id == collection_id)
        value_result = await self._db.execute(value_stmt)
        current_value_raw = value_result.scalar() or 0
        current_value = float(current_value_raw) if current_value_raw else None

        # Value gain
        value_gain: float | None = None
        if total_invested is not None and current_value is not None:
            value_gain = current_value - total_invested

        # ROI percentage
        roi: float | None = None
        if total_invested is not None and current_value is not None:
            roi = roi_percentage(Decimal(str(total_invested)), Decimal(str(current_value)))
            roi = float(roi) if roi is not None else None

        # Complete items
        complete_stmt = select(func.count(CollectionItem.id)).where(
            CollectionItem.collection_id == collection_id,
            CollectionItem.is_complete.is_(True),
        )
        complete_result = await self._db.execute(complete_stmt)
        complete_items = complete_result.scalar() or 0

        # Graded items
        graded_stmt = select(func.count(CollectionItem.id)).where(
            CollectionItem.collection_id == collection_id,
            CollectionItem.is_graded.is_(True),
        )
        graded_result = await self._db.execute(graded_stmt)
        graded_items = graded_result.scalar() or 0

        return CollectionStats(
            total_items=total_items,
            different_categories_count=different_categories_count,
            total_invested=total_invested,
            current_value=current_value,
            value_gain=value_gain,
            roi_percentage=roi,
            complete_items=complete_items,
            graded_items=graded_items,
        )
