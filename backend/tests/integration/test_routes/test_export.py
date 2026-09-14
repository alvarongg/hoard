"""Integration tests for export REST endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

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


async def _seed_catalog() -> str:
    from api.models.catalog import Catalog, CatalogItem
    from api.models.category import MainCategory, SubCategory

    async with _TestSessionFactory() as s:
        mc = MainCategory(id=str(uuid4()), name="MC", slug=f"mc-{uuid4().hex[:8]}")
        s.add(mc)
        await s.commit()
        sub = SubCategory(
            id=str(uuid4()), main_category_id=mc.id, name="SC", slug=f"sc-{uuid4().hex[:8]}"
        )
        s.add(sub)
        await s.commit()
        cat = Catalog(id=str(uuid4()), sub_category_id=sub.id, name="Cat")
        s.add(cat)
        await s.commit()
        ci = CatalogItem(id=str(uuid4()), catalog_id=cat.id, title="Item")
        s.add(ci)
        await s.commit()
        return cat.id


@pytest.mark.asyncio
async def test_catalog_json_200_headers(client: AsyncClient) -> None:
    cat_id = await _seed_catalog()
    resp = await client.get(f"/api/export/catalogs/{cat_id}?format=json")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert "attachment" in resp.headers["content-disposition"]


@pytest.mark.asyncio
async def test_catalog_csv_200_headers(client: AsyncClient) -> None:
    cat_id = await _seed_catalog()
    resp = await client.get(f"/api/export/catalogs/{cat_id}?format=csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")


@pytest.mark.asyncio
async def test_catalog_unknown_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/export/catalogs/{uuid4()}?format=json")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_catalog_bad_format_422(client: AsyncClient) -> None:
    cat_id = await _seed_catalog()
    resp = await client.get(f"/api/export/catalogs/{cat_id}?format=xml")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_wishlist_200(client: AsyncClient) -> None:
    resp = await client.get("/api/export/wishlist")
    assert resp.status_code == 200
