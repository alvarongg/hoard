"""Integration tests for collection and collection-item REST endpoints.

Tests verify that routes delegate correctly to the service layer and
return proper HTTP status codes and response bodies.

Requirements: REQ-007, REQ-008, REQ-015
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from api.models.collection import CollectionItem
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


async def _seed_second_subcategory(client: AsyncClient) -> str:
    """Create a second main category + sub-category, return sub-category id."""
    main = await client.post(
        "/api/categories",
        json={"name": "Música", "slug": "musica"},
    )
    cat_id = main.json()["id"]
    sub = await client.post(
        f"/api/categories/{cat_id}/subcategories",
        json={
            "name": "Vinilos",
            "slug": "vinilos",
            "main_category_id": cat_id,
        },
    )
    return sub.json()["id"]


async def _seed_catalog_item(
    client: AsyncClient, sub_category_id: str,
) -> str:
    """Create a catalog + catalog item and return the catalog item id."""
    catalog = await client.post(
        "/api/catalogs",
        json={"name": "N64 Games", "sub_category_id": sub_category_id},
    )
    catalog_id = catalog.json()["id"]
    item = await client.post(
        f"/api/catalogs/{catalog_id}/items",
        json={"title": "Zelda OoT", "catalog_id": catalog_id},
    )
    return item.json()["id"]


def _collection_payload(sub_category_id: str, **overrides: object) -> dict:
    defaults: dict = {
        "name": "Mi Colección N64",
        "collection_type": "single_category",
        "restricted_to_sub_category_id": sub_category_id,
    }
    defaults.update(overrides)
    return defaults


def _collection_item_payload(
    catalog_item_id: str, **overrides: object,
) -> dict:
    defaults: dict = {
        "catalog_item_id": catalog_item_id,
        "condition": "excellent",
    }
    defaults.update(overrides)
    return defaults


async def _create_collection(
    client: AsyncClient, sub_category_id: str, **overrides: object,
) -> dict:
    """Helper to create a collection and return its JSON body."""
    resp = await client.post(
        "/api/collections",
        json=_collection_payload(sub_category_id, **overrides),
    )
    assert resp.status_code == 201
    return resp.json()


async def _add_item_to_collection(
    client: AsyncClient,
    collection_id: str,
    catalog_item_id: str,
    **overrides: object,
) -> dict:
    """Helper to add an item to a collection and return its JSON body."""
    resp = await client.post(
        f"/api/collections/{collection_id}/items",
        json=_collection_item_payload(catalog_item_id, **overrides),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Collection endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListCollections:
    async def test_get_collections_returns_200_with_list(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/collections")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_collections_with_pagination(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        for i in range(3):
            await _create_collection(
                client, sub_id, name=f"Collection {i}",
            )
        response = await client.get("/api/collections?skip=1&limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1


@pytest.mark.asyncio
class TestCreateCollection:
    async def test_create_collection_returns_201(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        response = await client.post(
            "/api/collections",
            json=_collection_payload(sub_id),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Mi Colección N64"
        assert body["collection_type"] == "single_category"
        assert "id" in body

    async def test_create_collection_duplicate_name_returns_409(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        await _create_collection(client, sub_id)
        response = await client.post(
            "/api/collections",
            json=_collection_payload(sub_id),
        )
        assert response.status_code == 409

    async def test_create_collection_without_name_returns_422(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        response = await client.post(
            "/api/collections",
            json={
                "collection_type": "single_category",
                "restricted_to_sub_category_id": sub_id,
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetCollection:
    async def test_get_collection_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)
        response = await client.get(
            f"/api/collections/{collection['id']}",
        )
        assert response.status_code == 200
        assert response.json()["id"] == collection["id"]

    async def test_get_nonexistent_collection_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/collections/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCollection:
    async def test_update_collection_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)
        response = await client.put(
            f"/api/collections/{collection['id']}",
            json={"name": "Renamed Collection"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Collection"


@pytest.mark.asyncio
class TestDeleteCollection:
    async def test_delete_collection_returns_204(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)
        response = await client.delete(
            f"/api/collections/{collection['id']}",
        )
        assert response.status_code == 204

    async def test_delete_nonexistent_collection_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete(
            "/api/collections/nonexistent-id",
        )
        assert response.status_code == 404

    async def test_delete_collection_cascades_items_returns_204(
        self, client: AsyncClient,
    ) -> None:
        """Deleting a collection also removes its items."""
        sub_id = await _seed_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        collection = await _create_collection(client, sub_id)
        item = await _add_item_to_collection(
            client, collection["id"], catalog_item_id,
        )

        # Delete the collection
        resp = await client.delete(
            f"/api/collections/{collection['id']}",
        )
        assert resp.status_code == 204

        # The item should be gone too
        resp = await client.get(f"/api/items/{item['id']}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Collection item endpoint tests (nested under collection)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAddCollectionItem:
    async def test_add_item_to_collection_returns_201(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        collection = await _create_collection(client, sub_id)
        response = await client.post(
            f"/api/collections/{collection['id']}/items",
            json=_collection_item_payload(catalog_item_id),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["catalog_item_id"] == catalog_item_id
        assert body["condition"] == "excellent"
        assert "id" in body

    async def test_add_item_wrong_category_returns_422(
        self, client: AsyncClient,
    ) -> None:
        """Adding an item from a different sub-category to a
        single_category collection should fail with 422."""
        sub_id_a = await _seed_subcategory(client)
        sub_id_b = await _seed_second_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id_b)
        collection = await _create_collection(client, sub_id_a)
        response = await client.post(
            f"/api/collections/{collection['id']}/items",
            json=_collection_item_payload(catalog_item_id),
        )
        assert response.status_code == 422

    async def test_add_item_to_nonexistent_collection_returns_404(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        response = await client.post(
            "/api/collections/nonexistent-id/items",
            json=_collection_item_payload(catalog_item_id),
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestListCollectionItems:
    async def test_get_collection_items_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)
        response = await client.get(
            f"/api/collections/{collection['id']}/items",
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_collection_items_with_pagination_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)

        # Create 3 catalog items and add them
        catalog = await client.post(
            "/api/catalogs",
            json={"name": "Test Catalog", "sub_category_id": sub_id},
        )
        catalog_id = catalog.json()["id"]
        for i in range(3):
            ci = await client.post(
                f"/api/catalogs/{catalog_id}/items",
                json={"title": f"Item {i}", "catalog_id": catalog_id},
            )
            await _add_item_to_collection(
                client, collection["id"], ci.json()["id"],
            )

        response = await client.get(
            f"/api/collections/{collection['id']}/items?skip=0&limit=2",
        )
        assert response.status_code == 200
        assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Collection item standalone endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetCollectionItem:
    async def test_get_collection_item_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        collection = await _create_collection(client, sub_id)
        item = await _add_item_to_collection(
            client, collection["id"], catalog_item_id,
        )
        response = await client.get(f"/api/items/{item['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == item["id"]

    async def test_get_nonexistent_item_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/items/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCollectionItem:
    async def test_update_collection_item_returns_200(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        collection = await _create_collection(client, sub_id)
        item = await _add_item_to_collection(
            client, collection["id"], catalog_item_id,
        )
        response = await client.put(
            f"/api/items/{item['id']}",
            json={"condition": "mint", "notes": "Perfect condition"},
        )
        assert response.status_code == 200
        assert response.json()["condition"] == "mint"
        assert response.json()["notes"] == "Perfect condition"


@pytest.mark.asyncio
class TestDeleteCollectionItem:
    async def test_delete_collection_item_returns_204(
        self, client: AsyncClient,
    ) -> None:
        sub_id = await _seed_subcategory(client)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        collection = await _create_collection(client, sub_id)
        item = await _add_item_to_collection(
            client, collection["id"], catalog_item_id,
        )
        response = await client.delete(f"/api/items/{item['id']}")
        assert response.status_code == 204

    async def test_delete_nonexistent_item_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/items/nonexistent-id")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Property 8: Cascade deletion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCascadeDeletionProperty:
    """**Validates: Requirements REQ-007.5, REQ-008**

    Property 8: Cascada de eliminación — deleting a collection removes
    all its collection_items as well.
    """

    async def test_cascade_deletion_removes_all_items(
        self, client: AsyncClient,
    ) -> None:
        """Create a collection with multiple items, delete the collection,
        and verify every item is gone."""
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)

        # Seed a catalog with several items
        catalog = await client.post(
            "/api/catalogs",
            json={"name": "Cascade Catalog", "sub_category_id": sub_id},
        )
        catalog_id = catalog.json()["id"]

        item_ids: list[str] = []
        for i in range(5):
            ci = await client.post(
                f"/api/catalogs/{catalog_id}/items",
                json={"title": f"Game {i}", "catalog_id": catalog_id},
            )
            added = await _add_item_to_collection(
                client, collection["id"], ci.json()["id"],
            )
            item_ids.append(added["id"])

        # Verify items exist before deletion
        for iid in item_ids:
            resp = await client.get(f"/api/items/{iid}")
            assert resp.status_code == 200

        # Delete the collection
        resp = await client.delete(
            f"/api/collections/{collection['id']}",
        )
        assert resp.status_code == 204

        # All items must be gone
        for iid in item_ids:
            resp = await client.get(f"/api/items/{iid}")
            assert resp.status_code == 404

    async def test_cascade_deletion_db_level(
        self, client: AsyncClient,
    ) -> None:
        """Verify at the DB level that no orphan rows remain after
        deleting a collection."""
        sub_id = await _seed_subcategory(client)
        collection = await _create_collection(client, sub_id)
        catalog_item_id = await _seed_catalog_item(client, sub_id)
        await _add_item_to_collection(
            client, collection["id"], catalog_item_id,
        )

        # Delete the collection via API
        resp = await client.delete(
            f"/api/collections/{collection['id']}",
        )
        assert resp.status_code == 204

        # Query the DB directly — no items should reference this collection
        async with _TestSessionFactory() as session:
            result = await session.execute(
                select(CollectionItem).where(
                    CollectionItem.collection_id == collection["id"],
                )
            )
            orphans = result.scalars().all()
            assert len(orphans) == 0
