"""Integration tests for stats REST endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from main import app


_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionFactory() as session:
        yield session


@pytest.fixture(autouse=True)
async def _setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_empty_200(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 0
    assert data["roi_percentage"] is None


@pytest.mark.asyncio
async def test_valuation_200(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/valuation")
    assert resp.status_code == 200
    assert "total_invested" in resp.json()


@pytest.mark.asyncio
async def test_collections_200(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/collections")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_categories_200(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_timeline_default_month_200(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/timeline")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_timeline_invalid_period_422(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/timeline?period=weekly")
    assert resp.status_code == 422
