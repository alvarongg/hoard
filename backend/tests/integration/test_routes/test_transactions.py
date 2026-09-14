"""Integration tests for transaction REST endpoints."""

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
            id=str(uuid4()),
            main_category_id=mc.id,
            name="SC",
            slug=f"sc-{uuid4().hex[:8]}",
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
            id=str(uuid4()),
            collection_id=coll.id,
            catalog_item_id=ci.id,
            condition="good",
        )
        s.add(item)
        await s.commit()
        return item.id


def _payload(**overrides: object) -> dict:
    p: dict = {
        "transaction_type": "purchase",
        "transaction_date": "2026-01-01",
        "amount": "100.00",
        "shipping_cost": "10.00",
        "currency": "USD",
    }
    p.update(overrides)
    return p


@pytest.mark.asyncio
async def test_create_returns_201_with_total(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    resp = await client.post(
        f"/api/collection-items/{item}/transactions", json=_payload()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_amount"] == "110.00"
    assert "total_amount" not in _payload()


@pytest.mark.asyncio
async def test_create_unknown_item_404(client: AsyncClient) -> None:
    resp = await client.post(
        f"/api/collection-items/{uuid4()}/transactions", json=_payload()
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_invalid_type_422(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    resp = await client.post(
        f"/api/collection-items/{item}/transactions",
        json=_payload(transaction_type="bogus"),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_desc(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    await client.post(
        f"/api/collection-items/{item}/transactions",
        json=_payload(transaction_date="2026-01-01"),
    )
    await client.post(
        f"/api/collection-items/{item}/transactions",
        json=_payload(transaction_date="2026-03-01"),
    )
    resp = await client.get(f"/api/collection-items/{item}/transactions")
    assert resp.status_code == 200
    dates = [t["transaction_date"] for t in resp.json()]
    assert dates == ["2026-03-01", "2026-01-01"]


@pytest.mark.asyncio
async def test_delete_returns_investment(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    created = await client.post(
        f"/api/collection-items/{item}/transactions", json=_payload()
    )
    tx_id = created.json()["id"]
    resp = await client.delete(f"/api/transactions/{tx_id}")
    assert resp.status_code == 200
    assert "real_invested" in resp.json()


@pytest.mark.asyncio
async def test_investment_endpoint(client: AsyncClient) -> None:
    item = await _seed_collection_item()
    await client.post(
        f"/api/collection-items/{item}/transactions", json=_payload()
    )
    resp = await client.get(f"/api/collection-items/{item}/investment")
    assert resp.status_code == 200
    assert resp.json()["source"] == "transactions"
