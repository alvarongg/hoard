"""Integration tests for search routes.

Requirements: 6.5, 6.6, 6.8, 19.9
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)


@event.listens_for(_test_engine.sync_engine, "connect")
def _enable_sqlite_fks(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
    """Enable foreign key enforcement for SQLite (required for CASCADE)."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False,
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionFactory() as session:
        yield session


@pytest.fixture(autouse=True)
async def _setup_db():
    """Create all tables before each test and drop them afterwards."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the FastAPI test app."""
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestSearchRoutes:
    """Tests for search API routes."""

    @pytest.mark.asyncio
    async def test_search_catalog_items_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Search endpoint returns 200 with correct format."""
        response = await client.get("/api/search/catalog-items")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "search_mode" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["search_mode"] in ["full_text", "fuzzy", "degraded"]

    @pytest.mark.asyncio
    async def test_search_with_query_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Search with query returns 200."""
        response = await client.get("/api/search/catalog-items?q=Mario")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_search_with_filters_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Search with filters returns 200."""
        response = await client.get(
            "/api/search/catalog-items?language=English&region=NTSC-U",
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_search_with_pagination_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Search with pagination returns 200."""
        response = await client.get("/api/search/catalog-items?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_search_limit_exceeds_max_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Limit exceeding 200 returns 422 validation error."""
        response = await client.get("/api/search/catalog-items?limit=500")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_limit_below_min_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Limit below 1 returns 422 validation error."""
        response = await client.get("/api/search/catalog-items?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_skip_negative_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Negative skip returns 422 validation error."""
        response = await client.get("/api/search/catalog-items?skip=-1")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_year_min_out_of_range_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Year min out of range returns 422 validation error."""
        response = await client.get("/api/search/catalog-items?year_min=1500")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_year_max_out_of_range_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Year max out of range returns 422 validation error."""
        response = await client.get("/api/search/catalog-items?year_max=3000")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_combined_query_and_filters_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Search with both query and filters returns 200."""
        response = await client.get(
            "/api/search/catalog-items?q=Mario&language=English&year_min=1996&year_max=2006",
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "search_mode" in data

    @pytest.mark.asyncio
    async def test_search_empty_results(
        self,
        client: AsyncClient,
    ) -> None:
        """Search with no matches returns empty list with 200."""
        response = await client.get(
            "/api/search/catalog-items?q=NonexistentItemThatDoesNotExist12345",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
