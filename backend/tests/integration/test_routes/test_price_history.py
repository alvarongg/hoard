"""Integration tests for price history REST endpoints.

Covers status codes 200/201/204/404/409/422, response format, and the
refresh-value endpoint for both updated and not-updated outcomes.
"""

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


async def _seed_catalog_item() -> str:
    from api.models.catalog import Catalog, CatalogItem
    from api.models.category import MainCategory, SubCategory

    async with _TestSessionFactory() as session:
        main = MainCategory(id=str(uuid4()), name="MC", slug=f"mc-{uuid4().hex[:8]}")
        session.add(main)
        await session.commit()
        sub = SubCategory(
            id=str(uuid4()),
            main_category_id=main.id,
            name="SC",
            slug=f"sc-{uuid4().hex[:8]}",
        )
        session.add(sub)
        await session.commit()
        catalog = Catalog(id=str(uuid4()), sub_category_id=sub.id, name="Cat")
        session.add(catalog)
        await session.commit()
        item = CatalogItem(id=str(uuid4()), catalog_id=catalog.id, title="Item")
        session.add(item)
        await session.commit()
        return item.id


async def _seed_collection_item(catalog_item_id: str) -> str:
    from api.models.collection import Collection, CollectionItem

    async with _TestSessionFactory() as session:
        coll = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
        session.add(coll)
        await session.commit()
        ci = CollectionItem(
            id=str(uuid4()),
            collection_id=coll.id,
            catalog_item_id=catalog_item_id,
            condition="good",
            is_complete=True,
        )
        session.add(ci)
        await session.commit()
        return ci.id


def _payload(**overrides: object) -> dict:
    p: dict = {
        "condition": "good",
        "is_complete": True,
        "price": "50.00",
        "currency": "USD",
        "source": "eBay",
        "price_date": "2026-01-01",
    }
    p.update(overrides)
    return p


@pytest.mark.asyncio
async def test_create_returns_201(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    resp = await client.post(
        f"/api/catalog-items/{cid}/price-history", json=_payload()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["price"] == "50.00"
    assert data["catalog_item_id"] == cid


@pytest.mark.asyncio
async def test_create_unknown_item_returns_404(client: AsyncClient) -> None:
    resp = await client.post(
        f"/api/catalog-items/{uuid4()}/price-history", json=_payload()
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_returns_409(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    await client.post(f"/api/catalog-items/{cid}/price-history", json=_payload())
    resp = await client.post(
        f"/api/catalog-items/{cid}/price-history", json=_payload()
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_negative_price_returns_422(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    resp = await client.post(
        f"/api/catalog-items/{cid}/price-history",
        json=_payload(price="-1.00"),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_returns_200_desc(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    await client.post(
        f"/api/catalog-items/{cid}/price-history",
        json=_payload(price_date="2026-01-01", source="a"),
    )
    await client.post(
        f"/api/catalog-items/{cid}/price-history",
        json=_payload(price_date="2026-03-01", source="b"),
    )
    resp = await client.get(f"/api/catalog-items/{cid}/price-history")
    assert resp.status_code == 200
    dates = [r["price_date"] for r in resp.json()]
    assert dates == ["2026-03-01", "2026-01-01"]


@pytest.mark.asyncio
async def test_latest_returns_200(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    await client.post(f"/api/catalog-items/{cid}/price-history", json=_payload())
    resp = await client.get(f"/api/catalog-items/{cid}/price-history/latest")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_delete_returns_204(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    created = await client.post(
        f"/api/catalog-items/{cid}/price-history", json=_payload()
    )
    rec_id = created.json()["id"]
    resp = await client.delete(f"/api/price-history/{rec_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_unknown_returns_404(client: AsyncClient) -> None:
    resp = await client.delete(f"/api/price-history/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refresh_value_updates(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    coll_item = await _seed_collection_item(cid)
    await client.post(
        f"/api/catalog-items/{cid}/price-history",
        json=_payload(price="75.00"),
    )
    resp = await client.post(f"/api/collection-items/{coll_item}/refresh-value")
    assert resp.status_code == 200
    data = resp.json()
    assert data["updated"] is True
    assert data["current_market_value"] == "75.00"


@pytest.mark.asyncio
async def test_refresh_value_no_compatible_price(client: AsyncClient) -> None:
    cid = await _seed_catalog_item()
    coll_item = await _seed_collection_item(cid)
    await client.post(
        f"/api/catalog-items/{cid}/price-history",
        json=_payload(condition="poor"),
    )
    resp = await client.post(f"/api/collection-items/{coll_item}/refresh-value")
    assert resp.status_code == 200
    data = resp.json()
    assert data["updated"] is False
    assert data["reason"] is not None
