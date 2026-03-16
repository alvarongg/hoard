"""Integration tests for category and sub-category REST endpoints.

Tests verify that routes delegate correctly to the service layer and
return proper HTTP status codes and response bodies.

Requirements: REQ-004, REQ-015
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


def _category_payload(**overrides: object) -> dict:
    defaults: dict = {"name": "Videojuegos", "slug": "videojuegos"}
    defaults.update(overrides)
    return defaults


def _subcategory_payload(main_category_id: str, **overrides: object) -> dict:
    defaults: dict = {
        "name": "Consolas",
        "slug": "consolas",
        "main_category_id": main_category_id,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Main category endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListCategories:
    async def test_get_categories_returns_200_with_list(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_categories_with_pagination(
        self, client: AsyncClient,
    ) -> None:
        for i in range(3):
            await client.post(
                "/api/categories",
                json=_category_payload(name=f"Cat{i}", slug=f"cat{i}", sort_order=i),
            )
        response = await client.get("/api/categories?skip=1&limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1


@pytest.mark.asyncio
class TestCreateCategory:
    async def test_create_category_returns_201(
        self, client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/categories", json=_category_payload(),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Videojuegos"
        assert body["slug"] == "videojuegos"
        assert "id" in body

    async def test_create_category_without_name_returns_422(
        self, client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/categories", json={"slug": "no-name"},
        )
        assert response.status_code == 422

    async def test_create_category_duplicate_name_returns_409(
        self, client: AsyncClient,
    ) -> None:
        await client.post("/api/categories", json=_category_payload())
        response = await client.post(
            "/api/categories",
            json=_category_payload(slug="videojuegos-2"),
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestGetCategory:
    async def test_get_category_returns_200(
        self, client: AsyncClient,
    ) -> None:
        created = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = created.json()["id"]
        response = await client.get(f"/api/categories/{cat_id}")
        assert response.status_code == 200
        assert response.json()["id"] == cat_id

    async def test_get_nonexistent_category_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/categories/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCategory:
    async def test_update_category_returns_200(
        self, client: AsyncClient,
    ) -> None:
        created = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = created.json()["id"]
        response = await client.put(
            f"/api/categories/{cat_id}",
            json={"name": "Música", "slug": "musica"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Música"


@pytest.mark.asyncio
class TestDeleteCategory:
    async def test_delete_category_returns_204(
        self, client: AsyncClient,
    ) -> None:
        created = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = created.json()["id"]
        response = await client.delete(f"/api/categories/{cat_id}")
        assert response.status_code == 204

    async def test_delete_nonexistent_category_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/categories/nonexistent-id")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Sub-category endpoint tests (nested under main category)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListSubcategories:
    async def test_list_subcategories_returns_200(
        self, client: AsyncClient,
    ) -> None:
        created = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = created.json()["id"]
        response = await client.get(f"/api/categories/{cat_id}/subcategories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestCreateSubcategory:
    async def test_create_subcategory_returns_201(
        self, client: AsyncClient,
    ) -> None:
        main = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = main.json()["id"]
        response = await client.post(
            f"/api/categories/{cat_id}/subcategories",
            json=_subcategory_payload(cat_id),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Consolas"
        assert body["main_category_id"] == cat_id


# ---------------------------------------------------------------------------
# Sub-category standalone endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetSubcategory:
    async def test_get_subcategory_returns_200(
        self, client: AsyncClient,
    ) -> None:
        main = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = main.json()["id"]
        sub = await client.post(
            f"/api/categories/{cat_id}/subcategories",
            json=_subcategory_payload(cat_id),
        )
        sub_id = sub.json()["id"]
        response = await client.get(f"/api/subcategories/{sub_id}")
        assert response.status_code == 200
        assert response.json()["id"] == sub_id

    async def test_get_nonexistent_subcategory_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.get("/api/subcategories/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateSubcategory:
    async def test_update_subcategory_returns_200(
        self, client: AsyncClient,
    ) -> None:
        main = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = main.json()["id"]
        sub = await client.post(
            f"/api/categories/{cat_id}/subcategories",
            json=_subcategory_payload(cat_id),
        )
        sub_id = sub.json()["id"]
        response = await client.put(
            f"/api/subcategories/{sub_id}",
            json={"name": "Juegos", "slug": "juegos"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Juegos"


@pytest.mark.asyncio
class TestDeleteSubcategory:
    async def test_delete_subcategory_returns_204(
        self, client: AsyncClient,
    ) -> None:
        main = await client.post(
            "/api/categories", json=_category_payload(),
        )
        cat_id = main.json()["id"]
        sub = await client.post(
            f"/api/categories/{cat_id}/subcategories",
            json=_subcategory_payload(cat_id),
        )
        sub_id = sub.json()["id"]
        response = await client.delete(f"/api/subcategories/{sub_id}")
        assert response.status_code == 204

    async def test_delete_nonexistent_subcategory_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/subcategories/nonexistent-id")
        assert response.status_code == 404
