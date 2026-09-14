"""Integration tests for collector-workflow REST endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.dependencies import get_db
from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection
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


async def _seed() -> tuple[str, str, str]:
    async with _TestSessionFactory() as s:
        main = MainCategory(name="Videojuegos", slug="videojuegos")
        s.add(main)
        await s.flush()
        sub = SubCategory(main_category_id=main.id, name="Famicom", slug="famicom")
        s.add(sub)
        await s.flush()
        catalog = Catalog(sub_category_id=sub.id, name="Famicom Games")
        collection = Collection(name="Mi Famicom", collection_type="mixed")
        s.add_all([catalog, collection])
        await s.flush()
        item = CatalogItem(catalog_id=catalog.id, title="Dennou Kyusei Uranai")
        s.add(item)
        await s.commit()
        return collection.id, catalog.id, item.id


class TestQuickAddSupplier:
    @pytest.mark.asyncio
    async def test_quick_supplier_returns_201(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/suppliers/quick", json={"name": "Suruga-ya", "country": "JP"}
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Suruga-ya"


class TestCollectionCatalogs:
    @pytest.mark.asyncio
    async def test_associate_list_dissociate(self, client: AsyncClient) -> None:
        collection_id, catalog_id, _ = await _seed()
        assoc = await client.post(
            f"/api/collections/{collection_id}/catalogs",
            json={"catalog_id": catalog_id, "is_primary": True},
        )
        assert assoc.status_code == 201
        listed = await client.get(f"/api/collections/{collection_id}/catalogs")
        assert listed.status_code == 200
        assert [c["id"] for c in listed.json()] == [catalog_id]
        removed = await client.delete(
            f"/api/collections/{collection_id}/catalogs/{catalog_id}"
        )
        assert removed.status_code == 204
        listed2 = await client.get(f"/api/collections/{collection_id}/catalogs")
        assert listed2.json() == []

    @pytest.mark.asyncio
    async def test_quick_catalog_returns_201(self, client: AsyncClient) -> None:
        collection_id, _, _ = await _seed()
        resp = await client.post(
            f"/api/collections/{collection_id}/catalogs/quick",
            json={"name": "Zelda", "tematica": "Zelda"},
        )
        assert resp.status_code == 201


class TestQuickAddItem:
    @pytest.mark.asyncio
    async def test_quick_item_creates_catalog_and_collection_item(
        self, client: AsyncClient
    ) -> None:
        collection_id, catalog_id, _ = await _seed()
        await client.post(
            f"/api/collections/{collection_id}/catalogs",
            json={"catalog_id": catalog_id},
        )
        resp = await client.post(
            f"/api/collections/{collection_id}/items/quick",
            json={
                "catalog_id": catalog_id,
                "title": "Sin catalogar",
                "collection_item": {
                    "catalog_item_id": "ignored",
                    "condition": "good",
                    "country_of_origin": "BR",
                },
            },
        )
        assert resp.status_code == 201
        assert resp.json()["country_of_origin"] == "BR"


class TestOwnershipAndPending:
    @pytest.mark.asyncio
    async def test_ownership_false_then_pending_list(
        self, client: AsyncClient
    ) -> None:
        _, _, item_id = await _seed()
        own = await client.get(f"/api/catalog-items/{item_id}/ownership")
        assert own.status_code == 200
        assert own.json()["owned"] is False

        # A quick supplier opens a pending; verify it lists.
        await client.post("/api/suppliers/quick", json={"name": "X"})
        pend = await client.get("/api/pending")
        assert pend.status_code == 200
        assert any(p["entity_type"] == "supplier" for p in pend.json())


class TestMaintenance:
    @pytest.mark.asyncio
    async def test_create_and_list_due(self, client: AsyncClient) -> None:
        collection_id, catalog_id, item_id = await _seed()
        # Create a collection item to attach maintenance to.
        ci = await client.post(
            f"/api/collections/{collection_id}/items",
            json={"catalog_item_id": item_id, "condition": "good"},
        )
        assert ci.status_code == 201
        ci_id = ci.json()["id"]
        m = await client.post(
            f"/api/collection-items/{ci_id}/maintenance",
            json={
                "maintenance_type": "battery",
                "due_date": "2020-01-01",
                "notes": "pila",
            },
        )
        assert m.status_code == 201
        due = await client.get("/api/maintenance/due?before=2021-01-01")
        assert due.status_code == 200
        assert len(due.json()) == 1
