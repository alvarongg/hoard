"""Integration tests for catalog and catalog-item REST endpoints.

Tests verify that routes delegate correctly to the service layer and
return proper HTTP status codes and response bodies.

Requirements: REQ-005, REQ-006, REQ-015
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False,
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionFactory() as session:
        yield session


@pytest.fixture(autouse=True)
async def _setup_db():
    """Create all tables before each test and drop them after."""
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_subcategory(client: AsyncClient) -> str:
    """Create a main category + sub-category and return the sub-category id."""
    main = await client.post(
        "/api/categories",
        json={"name": "Videojuegos", "slug": "videojuegos"},
    )
    cat_id = main.json()["id"]
    sub = await client.post(
        f"/api/categories/{cat_id}/subcategories",
        json={
            "name": "Consolas",
            "slug": "consolas",
            "main_category_id": cat_id,
        },
    )
    return sub.json()["id"]


def _catalog_payload(sub_category_id: str, **overrides: object) -> dict:
    defaults: dict = {
        "name": "N64 Games",
        "sub_category_id": sub_category_id,
    }
    defaults.update(overrides)
    return defaults


def _catalog_item_payload(catalog_id: str, **overrides: object) -> dict:
    defaults: dict = {
        "title": "The Legend of Zelda: Ocarina of Time",
        "catalog_id": catalog_id,
    }
    defaults.update(overrides)
    return defaults


async def _create_catalog(
    client: AsyncClient, sub_category_id: str, **overrides: object,
) -> dict:
    """Helper to create a catalog and return its JSON body."""
    resp = await client.post(
        "/api/catalogs",
        json=_catalog_payload(sub_category_id, **overrides),
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_catalog_item(
    client: AsyncClient, catalog_id: str, **overrides: object,
) -> dict:
    """Helper to create a catalog item and return its JSON body."""
    resp = await client.post(
        f"/api/catalogs/{catalog_id}/items",
        json=_catalog_item_payload(catalog_id, **overrides),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Catalog endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListCatalogs:
    async def test_get_catalogs_returns_200(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/catalogs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_catalogs_with_pagination(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        for i in range(3):
            await _create_catalog(client, sub_id, name=f"Catalog {i}")
        response = await client.get("/api/catalogs?skip=1&limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1


@pytest.mark.asyncio
class TestCreateCatalog:
    async def test_create_catalog_returns_201(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        response = await client.post(
            "/api/catalogs",
            json=_catalog_payload(sub_id),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "N64 Games"
        assert body["sub_category_id"] == sub_id
        assert "id" in body

    async def test_create_catalog_without_name_returns_422(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        response = await client.post(
            "/api/catalogs",
            json={"sub_category_id": sub_id},
        )
        assert response.status_code == 422

    async def test_create_catalog_invalid_subcategory_returns_422(
        self, client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/catalogs",
            json=_catalog_payload("nonexistent-sub-id"),
        )
        assert response.status_code == 422

    async def test_create_catalog_duplicate_name_returns_409(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        await _create_catalog(client, sub_id)
        response = await client.post(
            "/api/catalogs",
            json=_catalog_payload(sub_id),
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestGetCatalog:
    async def test_get_catalog_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        response = await client.get(f"/api/catalogs/{catalog['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == catalog["id"]

    async def test_get_nonexistent_catalog_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/catalogs/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCatalog:
    async def test_update_catalog_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        response = await client.put(
            f"/api/catalogs/{catalog['id']}",
            json={"name": "SNES Games"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "SNES Games"


@pytest.mark.asyncio
class TestDeleteCatalog:
    async def test_delete_catalog_returns_204(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        response = await client.delete(f"/api/catalogs/{catalog['id']}")
        assert response.status_code == 204

    async def test_delete_nonexistent_catalog_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/catalogs/nonexistent-id")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Catalog item endpoint tests (nested under catalog)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListCatalogItems:
    async def test_list_catalog_items_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        response = await client.get(f"/api/catalogs/{catalog['id']}/items")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestCreateCatalogItem:
    async def test_create_catalog_item_returns_201(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        response = await client.post(
            f"/api/catalogs/{catalog['id']}/items",
            json=_catalog_item_payload(catalog["id"]),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "The Legend of Zelda: Ocarina of Time"
        assert body["catalog_id"] == catalog["id"]
        assert "id" in body

    async def test_create_catalog_item_without_title_returns_422(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        response = await client.post(
            f"/api/catalogs/{catalog['id']}/items",
            json={"catalog_id": catalog["id"]},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Catalog item standalone endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetCatalogItem:
    async def test_get_catalog_item_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        item = await _create_catalog_item(client, catalog["id"])
        response = await client.get(f"/api/catalog-items/{item['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == item["id"]

    async def test_get_nonexistent_catalog_item_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/catalog-items/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCatalogItem:
    async def test_update_catalog_item_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        item = await _create_catalog_item(client, catalog["id"])
        response = await client.put(
            f"/api/catalog-items/{item['id']}",
            json={"title": "Super Mario 64"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Super Mario 64"


@pytest.mark.asyncio
class TestDeleteCatalogItem:
    async def test_delete_catalog_item_returns_204(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        item = await _create_catalog_item(client, catalog["id"])
        response = await client.delete(f"/api/catalog-items/{item['id']}")
        assert response.status_code == 204

    async def test_delete_nonexistent_catalog_item_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/catalog-items/nonexistent-id")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Search endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSearchCatalogItems:
    async def test_search_catalog_items_returns_filtered_results(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        await _create_catalog_item(
            client, catalog["id"], title="Zelda Ocarina of Time",
        )
        await _create_catalog_item(
            client, catalog["id"], title="Super Mario 64",
        )
        response = await client.get("/api/catalog-items/search?q=Zelda")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert "Zelda" in results[0]["title"]

    async def test_search_catalog_items_no_results_returns_empty_list(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/catalog-items/search?q=nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    async def test_search_catalog_items_empty_query_returns_all(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog = await _create_catalog(client, sub_id)
        await _create_catalog_item(client, catalog["id"], title="Item A")
        await _create_catalog_item(client, catalog["id"], title="Item B")
        response = await client.get("/api/catalog-items/search?q=")
        assert response.status_code == 200
        assert len(response.json()) == 2
