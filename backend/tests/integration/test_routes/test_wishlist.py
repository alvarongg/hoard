"""Integration tests for wishlist routes."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.wishlist import WishlistItem
from main import app


# ------------------------------------------------------------------
# Database setup
# ------------------------------------------------------------------


_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
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


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
async def sample_collection(db_session: AsyncSession) -> Collection:
    """Create and return a sample collection."""
    collection = Collection(
        id=str(uuid4()),
        name="Test Collection",
        collection_type="single_category",
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection


@pytest.fixture
async def sample_catalog_item(db_session: AsyncSession) -> CatalogItem:
    """Create and return a sample catalog item."""
    # Create main category
    main_category = MainCategory(
        id=str(uuid4()),
        name="Test Main Category",
        slug="test-main-category",
    )
    db_session.add(main_category)
    await db_session.commit()
    await db_session.refresh(main_category)

    # Create sub category
    sub_category = SubCategory(
        id=str(uuid4()),
        main_category_id=main_category.id,
        name="Test Sub Category",
        slug="test-sub-category",
    )
    db_session.add(sub_category)
    await db_session.commit()
    await db_session.refresh(sub_category)

    # Create catalog
    catalog = Catalog(
        id=str(uuid4()),
        sub_category_id=sub_category.id,
        name="Test Catalog",
    )
    db_session.add(catalog)
    await db_session.commit()
    await db_session.refresh(catalog)

    item = CatalogItem(
        id=str(uuid4()),
        catalog_id=catalog.id,
        title="Test Catalog Item",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def sample_wishlist_item(
    db_session: AsyncSession,
    sample_collection: Collection,
    sample_catalog_item: CatalogItem,
) -> WishlistItem:
    """Create and return a sample wishlist item."""
    item = WishlistItem(
        id=str(uuid4()),
        collection_id=sample_collection.id,
        catalog_item_id=sample_catalog_item.id,
        priority=3,
        urgency="medium",
        max_price=Decimal("100.00"),
        currency="USD",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


# ------------------------------------------------------------------
# Wishlist CRUD tests
# ------------------------------------------------------------------


class TestWishlistRoutes:
    """Tests for wishlist routes."""

    async def test_list_wishlist_items_returns_200(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """GET /wishlist returns 200 with list."""
        response = await client.get("/api/wishlist")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    async def test_create_wishlist_item_returns_201(
        self,
        client: AsyncClient,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """POST /wishlist returns 201 with created item."""
        payload = {
            "collection_id": sample_collection.id,
            "catalog_item_id": sample_catalog_item.id,
            "priority": 2,
            "urgency": "high",
            "max_price": "75.00",
            "currency": "USD",
        }

        response = await client.post("/api/wishlist", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == 2
        assert data["urgency"] == "high"
        assert data["max_price"] == "75.00"

    async def test_create_wishlist_item_with_invalid_urgency_returns_422(
        self,
        client: AsyncClient,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """POST /wishlist with invalid urgency returns 422."""
        payload = {
            "collection_id": sample_collection.id,
            "catalog_item_id": sample_catalog_item.id,
            "urgency": "invalid_urgency",
        }

        response = await client.post("/api/wishlist", json=payload)

        assert response.status_code == 422

    async def test_get_wishlist_item_returns_200(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """GET /wishlist/{id} returns 200 with item details."""
        response = await client.get(f"/api/wishlist/{sample_wishlist_item.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_wishlist_item.id
        assert "price_aggregates" in data

    async def test_get_wishlist_item_not_found_returns_404(
        self, client: AsyncClient
    ) -> None:
        """GET /wishlist/{id} with nonexistent id returns 404."""
        response = await client.get(
            "/api/wishlist/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404

    async def test_update_wishlist_item_returns_200(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """PUT /wishlist/{id} returns 200 with updated item."""
        payload = {
            "priority": 1,
            "urgency": "critical",
            "notes": "Updated notes",
        }

        response = await client.put(
            f"/api/wishlist/{sample_wishlist_item.id}", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 1
        assert data["urgency"] == "critical"
        assert data["notes"] == "Updated notes"

    async def test_delete_wishlist_item_returns_204(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """DELETE /wishlist/{id} returns 204."""
        response = await client.delete(f"/api/wishlist/{sample_wishlist_item.id}")

        assert response.status_code == 204

    async def test_list_filters_by_collection(
        self,
        client: AsyncClient,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """GET /wishlist filters by collection_id."""
        # Create another collection and wishlist item
        other_collection = Collection(
            name="Other Collection",
            collection_type="single_category",
        )
        db_session.add(other_collection)
        await db_session.commit()
        await db_session.refresh(other_collection)

        other_item = WishlistItem(
            collection_id=other_collection.id,
            catalog_item_id=sample_catalog_item.id,
        )
        db_session.add(other_item)
        await db_session.commit()

        response = await client.get(
            "/api/wishlist", params={"collection_id": sample_collection.id}
        )

        assert response.status_code == 200
        data = response.json()
        # Should only return items for sample_collection
        for item in data:
            assert item["collection_id"] == sample_collection.id


class TestWishlistAcquireRoutes:
    """Tests for wishlist acquisition routes."""

    async def test_acquire_wishlist_item_returns_200(
        self,
        client: AsyncClient,
        sample_wishlist_item: WishlistItem,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """POST /wishlist/{id}/acquire returns 200."""
        # Create a collection item
        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()
        await db_session.refresh(collection_item)

        payload = {"acquired_collection_item_id": collection_item.id}

        response = await client.post(
            f"/api/wishlist/{sample_wishlist_item.id}/acquire", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_acquired"] is True
        assert data["acquired_collection_item_id"] == collection_item.id

    async def test_acquire_already_acquired_returns_409(
        self,
        client: AsyncClient,
        sample_wishlist_item: WishlistItem,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """POST /wishlist/{id}/acquire twice returns 409."""
        # Create a collection item
        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()
        await db_session.refresh(collection_item)

        payload = {"acquired_collection_item_id": collection_item.id}

        # First acquisition
        await client.post(
            f"/api/wishlist/{sample_wishlist_item.id}/acquire", json=payload
        )

        # Second acquisition attempt
        response = await client.post(
            f"/api/wishlist/{sample_wishlist_item.id}/acquire", json=payload
        )

        assert response.status_code == 409


class TestSightingRoutes:
    """Tests for sighting routes."""

    async def test_list_sightings_returns_200(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """GET /wishlist/{id}/sightings returns 200."""
        response = await client.get(
            f"/api/wishlist/{sample_wishlist_item.id}/sightings"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_sighting_returns_201(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """POST /wishlist/{id}/sightings returns 201."""
        payload = {
            "price": "45.00",
            "currency": "USD",
            "condition": "good",
            "is_available": True,
        }

        response = await client.post(
            f"/api/wishlist/{sample_wishlist_item.id}/sightings", json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["price"] == "45.00"
        assert data["condition"] == "good"

    async def test_update_sighting_returns_200(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """PUT /sightings/{id} returns 200."""
        # Create a sighting first
        create_payload = {
            "price": "45.00",
        }
        create_response = await client.post(
            f"/api/wishlist/{sample_wishlist_item.id}/sightings",
            json=create_payload,
        )
        sighting_id = create_response.json()["id"]

        # Update the sighting
        update_payload = {
            "price": "50.00",
            "decision": "buy",
        }

        response = await client.put(f"/api/sightings/{sighting_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["price"] == "50.00"
        assert data["decision"] == "buy"

    async def test_delete_sighting_returns_204(
        self, client: AsyncClient, sample_wishlist_item: WishlistItem
    ) -> None:
        """DELETE /sightings/{id} returns 204."""
        # Create a sighting first
        create_payload = {
            "price": "45.00",
        }
        create_response = await client.post(
            f"/api/wishlist/{sample_wishlist_item.id}/sightings",
            json=create_payload,
        )
        sighting_id = create_response.json()["id"]

        response = await client.delete(f"/api/sightings/{sighting_id}")

        assert response.status_code == 204
