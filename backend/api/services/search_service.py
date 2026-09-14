"""Service for advanced catalog search.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 19.6
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from api.models.catalog import CatalogItem
from api.schemas.search import (
    CatalogSearchResult,
    CatalogSearchResultItem,
    CatalogSearchParams,
    SearchMode,
)
from core.config import Settings
from core.dialect import supports_full_text


class SearchService:
    """Service for searching catalog items."""

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        """Initialize the search service.

        Args:
            db: Async database session.
            settings: Application settings.
        """
        self._db = db
        self._settings = settings

    async def search_catalog_items(
        self,
        params: CatalogSearchParams,
    ) -> CatalogSearchResult:
        """Search catalog items with optional filters.

        On PostgreSQL, uses full-text search (tsvector) and falls back to
        fuzzy search (pg_trgm similarity) if no results.
        On SQLite, uses ILIKE pattern matching.

        Args:
            params: Search parameters.

        Returns:
            Search result with items, total count, and search mode.
        """
        if supports_full_text(self._db) and params.q:
            return await self._full_text_search(params)
        else:
            return await self._degraded_search(params)

    async def _full_text_search(
        self,
        params: CatalogSearchParams,
    ) -> CatalogSearchResult:
        """Perform full-text search using PostgreSQL tsvector.

        Falls back to fuzzy search (pg_trgm) if no results.

        Args:
            params: Search parameters.

        Returns:
            Search result with items, total, and search mode.
        """
        # Build the full-text search query
        search_term = params.q or ""
        # Convert to tsquery format (handle special chars)
        tsquery_term = " & ".join(search_term.split())

        # Select with ts_rank for relevance ordering
        stmt = select(CatalogItem).where(
            CatalogItem.search_vector.op("@@")(func.to_tsquery("english", tsquery_term)),
        ).order_by(
            func.ts_rank(CatalogItem.search_vector, func.to_tsquery("english", tsquery_term)).desc(),
        )

        # Apply filters
        stmt = self._apply_filters(stmt, params)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar() or 0

        if total == 0:
            # Fall back to fuzzy search with pg_trgm
            return await self._fuzzy_search(params)

        # Apply pagination
        stmt = stmt.offset(params.skip).limit(params.limit)

        result = await self._db.execute(stmt)
        items = [self._item_to_result_item(item) for item in result.scalars().all()]

        return CatalogSearchResult(
            items=items,
            total=total,
            search_mode=SearchMode.FULL_TEXT,
        )

    async def _fuzzy_search(
        self,
        params: CatalogSearchParams,
    ) -> CatalogSearchResult:
        """Perform fuzzy search using pg_trgm similarity.

        Args:
            params: Search parameters.

        Returns:
            Search result with items, total, and search mode.
        """
        search_term = params.q or ""
        threshold = self._settings.SEARCH_SIMILARITY_THRESHOLD

        # Use similarity function from pg_trgm
        stmt = select(CatalogItem).where(
            func.similarity(CatalogItem.title, search_term) >= threshold,
        ).order_by(
            func.similarity(CatalogItem.title, search_term).desc(),
        )

        # Apply filters
        stmt = self._apply_filters(stmt, params)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar() or 0

        # Apply pagination
        stmt = stmt.offset(params.skip).limit(params.limit)

        result = await self._db.execute(stmt)
        items = [self._item_to_result_item(item) for item in result.scalars().all()]

        return CatalogSearchResult(
            items=items,
            total=total,
            search_mode=SearchMode.FUZZY,
        )

    async def _degraded_search(
        self,
        params: CatalogSearchParams,
    ) -> CatalogSearchResult:
        """Perform degraded search using ILIKE pattern matching.

        Used on SQLite where tsvector and pg_trgm are not available.

        Args:
            params: Search parameters.

        Returns:
            Search result with items, total, and search mode.
        """
        search_term = params.q or ""
        pattern = f"%{search_term}%"

        # Use ILIKE for case-insensitive pattern matching
        # Only search on title and subtitle (alternate_titles is JSON, harder to search)
        stmt = select(CatalogItem)
        if search_term:
            stmt = stmt.where(
                or_(
                    CatalogItem.title.ilike(pattern),
                    CatalogItem.subtitle.ilike(pattern),
                ),
            )

        # Apply filters
        stmt = self._apply_filters(stmt, params)

        # Get total count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar() or 0

        # Apply pagination
        stmt = stmt.offset(params.skip).limit(params.limit)

        result = await self._db.execute(stmt)
        items = [self._item_to_result_item(item) for item in result.scalars().all()]

        return CatalogSearchResult(
            items=items,
            total=total,
            search_mode=SearchMode.DEGRADED,
        )

    def _apply_filters(
        self,
        stmt: Any,
        params: CatalogSearchParams,
    ) -> Any:
        """Apply filters to the search query.

        Args:
            stmt: SQLAlchemy select statement.
            params: Search parameters with filters.

        Returns:
            Modified select statement with filters applied.
        """
        if params.main_category_id:
            # Join through catalog to filter by main category
            stmt = stmt.where(
                CatalogItem.catalog.has(main_category_id=params.main_category_id),
            )
        if params.sub_category_id:
            stmt = stmt.where(
                CatalogItem.catalog.has(sub_category_id=params.sub_category_id),
            )
        if params.language:
            stmt = stmt.where(CatalogItem.language == params.language)
        if params.region:
            stmt = stmt.where(CatalogItem.region == params.region)
        if params.manufacturer:
            stmt = stmt.where(CatalogItem.manufacturer == params.manufacturer)
        if params.publisher:
            stmt = stmt.where(CatalogItem.publisher == params.publisher)
        if params.developer:
            stmt = stmt.where(CatalogItem.developer == params.developer)
        if params.brand:
            stmt = stmt.where(CatalogItem.brand == params.brand)
        if params.rarity:
            stmt = stmt.where(CatalogItem.rarity == params.rarity)
        if params.year_min is not None:
            stmt = stmt.where(
                func.extract("year", CatalogItem.release_date) >= params.year_min,
            )
        if params.year_max is not None:
            stmt = stmt.where(
                func.extract("year", CatalogItem.release_date) <= params.year_max,
            )

        return stmt

    def _item_to_result_item(self, item: CatalogItem) -> CatalogSearchResultItem:
        """Convert a CatalogItem ORM instance to a result schema.

        Args:
            item: CatalogItem instance.

        Returns:
            CatalogSearchResultItem schema instance.
        """
        return CatalogSearchResultItem(
            id=item.id,
            title=item.title,
            subtitle=item.subtitle,
            catalog_id=item.catalog_id,
        )
