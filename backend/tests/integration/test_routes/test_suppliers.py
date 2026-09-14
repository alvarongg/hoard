"""Integration tests for suppliers REST endpoints.

Tests cover:
- Status codes 201/200/204/404/409/422 by endpoint
- Response format validation
- Error body format
- DELETE with references returns 409 with detail
- Filters and pagination via query params
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


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests that need direct DB access."""
    async with _TestSessionFactory() as session:
        yield session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateSupplier:
    """Tests for POST /api/suppliers endpoint."""

    @pytest.mark.asyncio
    async def test_create_returns_201_with_valid_data(
        self, client: AsyncClient
    ) -> None:
        """Creating a supplier with valid data returns 201."""
        payload = {
            "name": "GameStop",
            "type": "physical_store",
            "country": "US",
            "city": "Austin",
        }
        response = await client.post("/api/suppliers", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "GameStop"
        assert data["type"] == "physical_store"
        assert data["country"] == "US"
        assert data["city"] == "Austin"
        assert data["is_favorite"] is False
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_returns_422_with_empty_name(
        self, client: AsyncClient
    ) -> None:
        """Creating a supplier with empty name returns 422."""
        payload = {"name": ""}
        response = await client.post("/api/suppliers", json=payload)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(e["loc"] == ["body", "name"] for e in errors)

    @pytest.mark.asyncio
    async def test_create_returns_422_with_whitespace_name(
        self, client: AsyncClient
    ) -> None:
        """Creating a supplier with whitespace-only name returns 422."""
        payload = {"name": "   "}
        response = await client.post("/api/suppliers", json=payload)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("empty or whitespace-only" in str(e).lower() for e in errors)

    @pytest.mark.asyncio
    async def test_create_returns_422_with_invalid_type(
        self, client: AsyncClient
    ) -> None:
        """Creating a supplier with invalid type returns 422."""
        payload = {"name": "Test", "type": "invalid_type"}
        response = await client.post("/api/suppliers", json=payload)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("type must be one of" in str(e).lower() for e in errors)


class TestGetSupplier:
    """Tests for GET /api/suppliers/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_returns_200_for_existing_supplier(
        self, client: AsyncClient
    ) -> None:
        """Getting an existing supplier returns 200 with the data."""
        # Create a supplier first
        create_response = await client.post(
            "/api/suppliers", json={"name": "Test Supplier"}
        )
        supplier_id = create_response.json()["id"]

        response = await client.get(f"/api/suppliers/{supplier_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == supplier_id
        assert data["name"] == "Test Supplier"

    @pytest.mark.asyncio
    async def test_get_returns_404_for_nonexistent_supplier(
        self, client: AsyncClient
    ) -> None:
        """Getting a non-existent supplier returns 404."""
        response = await client.get("/api/suppliers/nonexistent-uuid")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestListSuppliers:
    """Tests for GET /api/suppliers endpoint."""

    @pytest.mark.asyncio
    async def test_list_returns_200_with_suppliers(
        self, client: AsyncClient
    ) -> None:
        """Listing suppliers returns 200 with a list."""
        # Create some suppliers
        await client.post("/api/suppliers", json={"name": "Supplier A"})
        await client.post("/api/suppliers", json={"name": "Supplier B"})

        response = await client.get("/api/suppliers")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_list_filters_by_type(
        self, client: AsyncClient
    ) -> None:
        """Filtering by type returns only matching suppliers."""
        await client.post(
            "/api/suppliers", json={"name": "Online Shop", "type": "online"}
        )
        await client.post(
            "/api/suppliers", json={"name": "Local Store", "type": "physical_store"}
        )

        response = await client.get("/api/suppliers?type=online")

        assert response.status_code == 200
        data = response.json()
        assert all(s["type"] == "online" for s in data)

    @pytest.mark.asyncio
    async def test_list_filters_by_country(
        self, client: AsyncClient
    ) -> None:
        """Filtering by country returns only matching suppliers."""
        await client.post(
            "/api/suppliers", json={"name": "US Shop", "country": "US"}
        )
        await client.post(
            "/api/suppliers", json={"name": "GB Shop", "country": "GB"}
        )

        response = await client.get("/api/suppliers?country=US")

        assert response.status_code == 200
        data = response.json()
        assert all(s["country"] == "US" for s in data)

    @pytest.mark.asyncio
    async def test_list_pagination_skip_and_limit(
        self, client: AsyncClient
    ) -> None:
        """Pagination parameters work correctly."""
        for i in range(5):
            await client.post("/api/suppliers", json={"name": f"Supplier {i}"})

        response = await client.get("/api/suppliers?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestUpdateSupplier:
    """Tests for PUT /api/suppliers/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_returns_200_with_updated_data(
        self, client: AsyncClient
    ) -> None:
        """Updating a supplier returns 200 with the updated data."""
        create_response = await client.post(
            "/api/suppliers", json={"name": "Original Name"}
        )
        supplier_id = create_response.json()["id"]

        update_response = await client.put(
            f"/api/suppliers/{supplier_id}",
            json={"name": "Updated Name", "is_favorite": True},
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"
        assert data["is_favorite"] is True

    @pytest.mark.asyncio
    async def test_update_returns_404_for_nonexistent_supplier(
        self, client: AsyncClient
    ) -> None:
        """Updating a non-existent supplier returns 404."""
        response = await client.put(
            "/api/suppliers/nonexistent-uuid", json={"name": "New Name"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_returns_422_with_invalid_type(
        self, client: AsyncClient
    ) -> None:
        """Updating with invalid type returns 422."""
        create_response = await client.post(
            "/api/suppliers", json={"name": "Test"}
        )
        supplier_id = create_response.json()["id"]

        response = await client.put(
            f"/api/suppliers/{supplier_id}", json={"type": "invalid_type"}
        )

        assert response.status_code == 422


class TestDeleteSupplier:
    """Tests for DELETE /api/suppliers/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_returns_204_for_existing_supplier(
        self, client: AsyncClient
    ) -> None:
        """Deleting an existing supplier returns 204."""
        create_response = await client.post(
            "/api/suppliers", json={"name": "To Delete"}
        )
        supplier_id = create_response.json()["id"]

        delete_response = await client.delete(f"/api/suppliers/{supplier_id}")

        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/suppliers/{supplier_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_returns_404_for_nonexistent_supplier(
        self, client: AsyncClient
    ) -> None:
        """Deleting a non-existent supplier returns 404."""
        response = await client.delete("/api/suppliers/nonexistent-uuid")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_returns_409_when_referenced_by_collection_item(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Deleting a supplier referenced by collection items returns 409."""
        from api.models.catalog import Catalog, CatalogItem
        from api.models.category import MainCategory, SubCategory
        from api.models.collection import Collection, CollectionItem

        # Create supplier via API
        create_response = await client.post(
            "/api/suppliers", json={"name": "Referenced Supplier"}
        )
        supplier_id = create_response.json()["id"]

        # Create the chain of dependencies directly in DB
        main = MainCategory(name="Games", slug="games")
        db_session.add(main)
        await db_session.flush()

        sub = SubCategory(main_category_id=main.id, name="N64", slug="n64")
        db_session.add(sub)
        await db_session.flush()

        catalog = Catalog(sub_category_id=sub.id, name="N64 Catalog")
        db_session.add(catalog)
        await db_session.flush()

        catalog_item = CatalogItem(catalog_id=catalog.id, title="Zelda")
        db_session.add(catalog_item)
        await db_session.flush()

        collection = Collection(
            id=str(uuid4()),
            name="My Collection",
            collection_type="multi_category",
        )
        db_session.add(collection)
        await db_session.flush()

        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=collection.id,
            catalog_item_id=catalog_item.id,
            supplier_id=supplier_id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()

        # Try to delete
        response = await client.delete(f"/api/suppliers/{supplier_id}")

        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "referenced" in detail.lower()


class TestSupplierPurchases:
    """Tests for GET /api/suppliers/{id}/purchases endpoint."""

    @pytest.mark.asyncio
    async def test_purchases_returns_200_with_empty_list(
        self, client: AsyncClient
    ) -> None:
        """Getting purchases for a supplier without purchases returns empty list."""
        create_response = await client.post(
            "/api/suppliers", json={"name": "No Purchases"}
        )
        supplier_id = create_response.json()["id"]

        response = await client.get(f"/api/suppliers/{supplier_id}/purchases")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_purchases_returns_404_for_nonexistent_supplier(
        self, client: AsyncClient
    ) -> None:
        """Getting purchases for non-existent supplier returns 404."""
        response = await client.get("/api/suppliers/nonexistent-uuid/purchases")

        assert response.status_code == 404
