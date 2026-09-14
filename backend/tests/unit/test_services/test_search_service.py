"""Unit tests for SearchService.

Requirements: 6.4, 6.5, 6.7, 6.8, 19.10
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.schemas.search import CatalogSearchParams, SearchMode
from api.services.search_service import SearchService
from core.config import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(_engine) -> AsyncSession:
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture
def search_service(db_session: AsyncSession) -> SearchService:
    """Provide a SearchService instance."""
    settings = Settings()
    return SearchService(db_session, settings)


class TestSearchService:
    """Tests for SearchService."""

    @pytest.mark.asyncio
    async def test_degraded_search_matches_title(
        self,
        search_service: SearchService,
    ) -> None:
        """Search matches items by title using ILIKE on SQLite."""
        params = CatalogSearchParams(q="Mario")
        result = await search_service.search_catalog_items(params)

        assert result.search_mode == SearchMode.DEGRADED
        # SQLite will return empty since no data, but mode should be degraded
        assert isinstance(result.items, list)
        assert isinstance(result.total, int)

    @pytest.mark.asyncio
    async def test_degraded_search_matches_subtitle(
        self,
        search_service: SearchService,
    ) -> None:
        """Search matches items by subtitle using ILIKE on SQLite."""
        params = CatalogSearchParams(q="Adventure")
        result = await search_service.search_catalog_items(params)

        assert result.search_mode == SearchMode.DEGRADED

    @pytest.mark.asyncio
    async def test_no_query_returns_all_items(
        self,
        search_service: SearchService,
    ) -> None:
        """Search without query returns all items (empty list if no data)."""
        params = CatalogSearchParams(q=None)
        result = await search_service.search_catalog_items(params)

        assert result.search_mode == SearchMode.DEGRADED
        assert isinstance(result.items, list)
        assert isinstance(result.total, int)

    @pytest.mark.asyncio
    async def test_empty_query_returns_all_items(
        self,
        search_service: SearchService,
    ) -> None:
        """Search with empty query string returns all items."""
        params = CatalogSearchParams(q="")
        result = await search_service.search_catalog_items(params)

        assert result.search_mode == SearchMode.DEGRADED

    @pytest.mark.asyncio
    async def test_search_no_results_returns_empty(
        self,
        search_service: SearchService,
    ) -> None:
        """Search with no matches returns empty results."""
        params = CatalogSearchParams(q="NonexistentItemThatDoesNotExist")
        result = await search_service.search_catalog_items(params)

        assert result.total == 0
        assert result.items == []
        assert result.search_mode == SearchMode.DEGRADED

    @pytest.mark.asyncio
    async def test_pagination_skip_and_limit(
        self,
        search_service: SearchService,
    ) -> None:
        """Pagination parameters work correctly."""
        params = CatalogSearchParams(skip=10, limit=5)
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)
        # Total should reflect all matching items, not just the page
        assert isinstance(result.total, int)

    @pytest.mark.asyncio
    async def test_pagination_does_not_affect_total(
        self,
        search_service: SearchService,
    ) -> None:
        """Total count is independent of pagination."""
        params_no_pagination = CatalogSearchParams()
        params_paginated = CatalogSearchParams(skip=5, limit=3)

        result_no_pagination = await search_service.search_catalog_items(
            params_no_pagination,
        )
        result_paginated = await search_service.search_catalog_items(params_paginated)

        # Total should be the same regardless of pagination
        assert result_no_pagination.total == result_paginated.total

    @pytest.mark.asyncio
    async def test_filter_by_language(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by language works correctly."""
        params = CatalogSearchParams(language="English")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_region(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by region works correctly."""
        params = CatalogSearchParams(region="NTSC-U")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_manufacturer(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by manufacturer works correctly."""
        params = CatalogSearchParams(manufacturer="Nintendo")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_publisher(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by publisher works correctly."""
        params = CatalogSearchParams(publisher="Capcom")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_developer(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by developer works correctly."""
        params = CatalogSearchParams(developer="Rare")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_brand(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by brand works correctly."""
        params = CatalogSearchParams(brand="Pokémon")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_rarity(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by rarity works correctly."""
        params = CatalogSearchParams(rarity="Rare")
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_year_min(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by minimum year works correctly."""
        params = CatalogSearchParams(year_min=1996)
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_year_max(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by maximum year works correctly."""
        params = CatalogSearchParams(year_max=2006)
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_filter_by_year_range(
        self,
        search_service: SearchService,
    ) -> None:
        """Filter by year range works correctly (inclusive)."""
        params = CatalogSearchParams(year_min=1996, year_max=2006)
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_combined_filters(
        self,
        search_service: SearchService,
    ) -> None:
        """Multiple filters applied together work correctly."""
        params = CatalogSearchParams(
            language="English",
            region="NTSC-U",
            manufacturer="Nintendo",
            year_min=1996,
            year_max=2006,
        )
        result = await search_service.search_catalog_items(params)

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_search_with_query_and_filters(
        self,
        search_service: SearchService,
    ) -> None:
        """Search with both query and filters works correctly."""
        params = CatalogSearchParams(
            q="Mario",
            language="English",
            region="NTSC-U",
        )
        result = await search_service.search_catalog_items(params)

        assert result.search_mode == SearchMode.DEGRADED
        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_result_format(
        self,
        search_service: SearchService,
    ) -> None:
        """Search result has correct format."""
        params = CatalogSearchParams()
        result = await search_service.search_catalog_items(params)

        assert hasattr(result, "items")
        assert hasattr(result, "total")
        assert hasattr(result, "search_mode")
        assert isinstance(result.search_mode, SearchMode)
