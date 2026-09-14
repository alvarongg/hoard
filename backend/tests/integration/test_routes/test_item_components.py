"""Integration tests for item components routes.

Tests cover:
- Status codes 200/201/404/422 by endpoint
- Response format validation
- Template endpoint
- Completeness calculation on delete

Requirements: REQ-013
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from api.models.standard_component import StandardComponent
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)

# Shared session for tests
_current_session: AsyncSession | None = None


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override that yields the current test session."""
    if _current_session is not None:
        yield _current_session
    else:
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
    global _current_session
    async with _TestSessionFactory() as session:
        _current_session = session
        yield session
        _current_session = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_category_chain(client: AsyncClient) -> tuple[str, str]:
    """Create main category, sub-category, catalog, and catalog item.
    
    Returns (catalog_item_id, sub_category_id).
    """
    # Create main category
    main = await client.post(
        "/api/categories",
        json={"name": "Videojuegos", "slug": "videojuegos"},
    )
    main_id = main.json()["id"]

    # Create sub-category
    sub = await client.post(
        f"/api/categories/{main_id}/subcategories",
        json={"name": "N64", "slug": "n64", "main_category_id": main_id},
    )
    sub_id = sub.json()["id"]

    # Create catalog
    catalog = await client.post(
        "/api/catalogs",
        json={"name": "N64 Games", "sub_category_id": sub_id},
    )
    catalog_id = catalog.json()["id"]

    # Create catalog item
    item = await client.post(
        f"/api/catalogs/{catalog_id}/items",
        json={"title": "Zelda OoT", "catalog_id": catalog_id},
    )
    return item.json()["id"], sub_id


async def _seed_collection(client: AsyncClient, sub_category_id: str) -> str:
    """Create a collection and return its id."""
    collection = await client.post(
        "/api/collections",
        json={
            "name": "Test Collection",
            "collection_type": "single_category",
            "restricted_to_sub_category_id": sub_category_id,
        },
    )
    return collection.json()["id"]


async def _seed_collection_item(
    client: AsyncClient, collection_id: str, catalog_item_id: str
) -> str:
    """Create a collection item and return its id."""
    item = await client.post(
        f"/api/collections/{collection_id}/items",
        json={
            "catalog_item_id": catalog_item_id,
            "condition": "good",
        },
    )
    return item.json()["id"]


async def _setup_full_item_chain(client: AsyncClient) -> tuple[str, str]:
    """Setup complete chain: category -> catalog item -> collection -> collection item.
    
    Returns (collection_item_id, sub_category_id).
    """
    catalog_item_id, sub_category_id = await _seed_category_chain(client)
    collection_id = await _seed_collection(client, sub_category_id)
    collection_item_id = await _seed_collection_item(
        client, collection_id, catalog_item_id
    )
    return collection_item_id, sub_category_id


# ---------------------------------------------------------------------------
# Template endpoint tests
# ---------------------------------------------------------------------------


class TestGetComponentTemplate:
    """Tests for GET /collection-items/{id}/components/template."""

    @pytest.mark.asyncio
    async def test_returns_200_with_template(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Returns 200 with component template."""
        collection_item_id, sub_category_id = await _setup_full_item_chain(client)

        # Create standard component directly in DB (no API endpoint exists)
        sc = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category_id,
            component_name="Box",
            component_type="required",
        )
        db_session.add(sc)
        await db_session.commit()

        response = await client.get(
            f"/api/collection-items/{collection_item_id}/components/template"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["component_name"] == "Box"
        assert data[0]["is_present"] is False

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_item(self, client: AsyncClient) -> None:
        """Returns 404 for nonexistent collection item."""
        response = await client.get(
            "/api/collection-items/00000000-0000-0000-0000-000000000000/components/template"
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# List endpoint tests
# ---------------------------------------------------------------------------


class TestListItemComponents:
    """Tests for GET /collection-items/{id}/components."""

    @pytest.mark.asyncio
    async def test_returns_200_with_components(self, client: AsyncClient) -> None:
        """Returns 200 with components list."""
        collection_item_id, _sub_category_id = await _setup_full_item_chain(client)

        # Create component via API
        await client.post(
            f"/api/collection-items/{collection_item_id}/components",
            json={"component_name": "Box", "is_present": True},
        )

        response = await client.get(
            f"/api/collection-items/{collection_item_id}/components"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["component_name"] == "Box"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_components(
        self, client: AsyncClient
    ) -> None:
        """Returns empty list when no components."""
        collection_item_id, _sub_category_id = await _setup_full_item_chain(client)

        response = await client.get(
            f"/api/collection-items/{collection_item_id}/components"
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_item(self, client: AsyncClient) -> None:
        """Returns 404 for nonexistent collection item."""
        response = await client.get(
            "/api/collection-items/00000000-0000-0000-0000-000000000000/components"
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Upsert endpoint tests
# ---------------------------------------------------------------------------


class TestUpsertItemComponent:
    """Tests for POST /collection-items/{id}/components."""

    @pytest.mark.asyncio
    async def test_returns_201_with_created_component(self, client: AsyncClient) -> None:
        """Returns 201 with created component."""
        collection_item_id, _sub_category_id = await _setup_full_item_chain(client)

        response = await client.post(
            f"/api/collection-items/{collection_item_id}/components",
            json={
                "component_name": "Box",
                "component_type": "required",
                "is_present": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["component_name"] == "Box"
        assert data["is_present"] is True
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_item(self, client: AsyncClient) -> None:
        """Returns 404 for nonexistent collection item."""
        response = await client.post(
            "/api/collection-items/00000000-0000-0000-0000-000000000000/components",
            json={"component_name": "Box"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_422_for_missing_name(self, client: AsyncClient) -> None:
        """Returns 422 for missing component_name."""
        collection_item_id, _sub_category_id = await _setup_full_item_chain(client)

        response = await client.post(
            f"/api/collection-items/{collection_item_id}/components",
            json={},
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update endpoint tests
# ---------------------------------------------------------------------------


class TestUpdateItemComponent:
    """Tests for PUT /item-components/{id}."""

    @pytest.mark.asyncio
    async def test_returns_200_with_updated_component(self, client: AsyncClient) -> None:
        """Returns 200 with updated component."""
        collection_item_id, _sub_category_id = await _setup_full_item_chain(client)

        # Create component
        create_response = await client.post(
            f"/api/collection-items/{collection_item_id}/components",
            json={"component_name": "Box", "is_present": False},
        )
        component_id = create_response.json()["id"]

        response = await client.put(
            f"/api/item-components/{component_id}",
            json={"is_present": True, "condition": "good"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_present"] is True
        assert data["condition"] == "good"

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_component(self, client: AsyncClient) -> None:
        """Returns 404 for nonexistent component."""
        response = await client.put(
            "/api/item-components/00000000-0000-0000-0000-000000000000",
            json={"is_present": True},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete endpoint tests
# ---------------------------------------------------------------------------


class TestDeleteItemComponent:
    """Tests for DELETE /api/item-components/{id}."""

    @pytest.mark.asyncio
    async def test_returns_200_with_completeness_result(
        self, client: AsyncClient
    ) -> None:
        """Returns 200 with completeness result."""
        collection_item_id, _sub_category_id = await _setup_full_item_chain(client)

        # Create component
        create_response = await client.post(
            f"/api/collection-items/{collection_item_id}/components",
            json={"component_name": "Box"},
        )
        component_id = create_response.json()["id"]

        response = await client.delete(f"/api/item-components/{component_id}")

        assert response.status_code == 200
        data = response.json()
        assert "is_complete" in data
        assert "required_count" in data
        assert "present_count" in data
        assert "missing_names" in data

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_component(self, client: AsyncClient) -> None:
        """Returns 404 for nonexistent component."""
        response = await client.delete(
            "/api/item-components/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404
