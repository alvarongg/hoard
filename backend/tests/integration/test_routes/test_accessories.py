"""Integration tests for accessories REST endpoints."""

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


async def _seed_collection_item() -> str:
    from api.models.catalog import Catalog, CatalogItem
    from api.models.category import MainCategory, SubCategory
    from api.models.collection import Collection, CollectionItem

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
        coll = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
        s.add(coll)
        await s.commit()
        item = CollectionItem(
            id=str(uuid4()), collection_id=coll.id, catalog_item_id=ci.id, condition="good"
        )
        s.add(item)
        await s.commit()
        return item.id


@pytest.mark.asyncio
async def test_create_and_get_200(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/accessories", json={"name": "Case", "quantity_total": 10}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity_available"] == 10
    assert data["is_low_stock"] is False


@pytest.mark.asyncio
async def test_create_invalid_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/accessories", json={"name": "", "quantity_total": 5}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_and_conflict(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    acc = (
        await client.post(
            "/api/accessories", json={"name": "Case", "quantity_total": 10}
        )
    ).json()
    r1 = await client.post(
        f"/api/collection-items/{item}/accessories",
        json={"accessory_id": acc["id"], "quantity_used": 2},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        f"/api/collection-items/{item}/accessories",
        json={"accessory_id": acc["id"], "quantity_used": 1},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_assign_insufficient_422(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    acc = (
        await client.post(
            "/api/accessories", json={"name": "Case", "quantity_total": 1}
        )
    ).json()
    resp = await client.post(
        f"/api/collection-items/{item}/accessories",
        json={"accessory_id": acc["id"], "quantity_used": 5},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_with_assignments_409(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    acc = (
        await client.post(
            "/api/accessories", json={"name": "Case", "quantity_total": 10}
        )
    ).json()
    await client.post(
        f"/api/collection-items/{item}/accessories",
        json={"accessory_id": acc["id"], "quantity_used": 1},
    )
    resp = await client.delete(f"/api/accessories/{acc['id']}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_low_stock_endpoint(client: AsyncClient) -> None:
    await client.post(
        "/api/accessories",
        json={"name": "Low", "quantity_total": 1, "minimum_stock_alert": 5},
    )
    resp = await client.get("/api/accessories/low-stock")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_unknown_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/accessories/{uuid4()}")
    assert resp.status_code == 404
