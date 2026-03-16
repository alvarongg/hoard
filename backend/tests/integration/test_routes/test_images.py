"""Integration tests for image upload, listing, and deletion endpoints.

Tests verify that routes delegate correctly to the ImageService and
return proper HTTP status codes and response bodies.

Requirements: REQ-009, REQ-015
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.dependencies import get_db, get_image_service
from api.models.base import Base
from api.services.image_service import ImageService
from main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", echo=False,
)


@event.listens_for(_test_engine.sync_engine, "connect")
def _enable_sqlite_fks(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
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
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with image service pointing to a temp upload dir."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    def _make_image_service_override(upload_directory: str):
        async def _override(
            db: AsyncSession = next(iter([])),  # placeholder
        ) -> ImageService:
            # This won't be called — we use the factory below
            ...  # pragma: no cover

        return _override

    # Override get_image_service to inject temp upload dir
    _upload_str = str(upload_dir)

    from fastapi import Depends

    async def _override_image_service(
        db: AsyncSession = Depends(_override_get_db),
    ) -> ImageService:
        return ImageService(db, _upload_str)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_image_service] = _override_image_service

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TINY_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01"
    b"\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06"
    b"\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b"
    b"\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0"
    b"\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4"
    b"\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
    b"\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03"
    b"\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02"
    b"\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81"
    b"\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16"
    b"\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghij"
    b"stuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94"
    b"\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8"
    b"\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3"
    b"\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7"
    b"\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea"
    b"\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00"
    b"\x08\x01\x01\x00\x00?\x00\xfb\xd2\x8a+\xff\xd9"
)


async def _seed_collection_item(client: AsyncClient) -> str:
    """Create the full chain and return a collection_item id.

    MainCategory → SubCategory → Catalog → CatalogItem →
    Collection → CollectionItem
    """
    # Main category
    main = await client.post(
        "/api/categories",
        json={"name": "Videojuegos", "slug": "videojuegos"},
    )
    cat_id = main.json()["id"]

    # Sub category
    sub = await client.post(
        f"/api/categories/{cat_id}/subcategories",
        json={
            "name": "Consolas",
            "slug": "consolas",
            "main_category_id": cat_id,
        },
    )
    sub_id = sub.json()["id"]

    # Catalog + catalog item
    catalog = await client.post(
        "/api/catalogs",
        json={"name": "N64 Games", "sub_category_id": sub_id},
    )
    catalog_id = catalog.json()["id"]
    ci = await client.post(
        f"/api/catalogs/{catalog_id}/items",
        json={"title": "Zelda OoT", "catalog_id": catalog_id},
    )
    catalog_item_id = ci.json()["id"]

    # Collection
    col = await client.post(
        "/api/collections",
        json={
            "name": "Mi Colección N64",
            "collection_type": "single_category",
            "restricted_to_sub_category_id": sub_id,
        },
    )
    col_id = col.json()["id"]

    # Collection item
    item = await client.post(
        f"/api/collections/{col_id}/items",
        json={
            "catalog_item_id": catalog_item_id,
            "condition": "excellent",
        },
    )
    return item.json()["id"]


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestUploadImage:
    async def test_upload_image_returns_201(
        self, client: AsyncClient,
    ) -> None:
        item_id = await _seed_collection_item(client)
        response = await client.post(
            f"/api/items/{item_id}/images",
            files={"file": ("photo.jpg", TINY_JPEG, "image/jpeg")},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["file_name"] == "photo.jpg"
        assert body["mime_type"] == "image/jpeg"
        assert body["is_primary"] is True
        assert "id" in body

    async def test_upload_invalid_type_returns_422(
        self, client: AsyncClient,
    ) -> None:
        item_id = await _seed_collection_item(client)
        response = await client.post(
            f"/api/items/{item_id}/images",
            files={
                "file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf"),
            },
        )
        assert response.status_code == 422

    async def test_upload_oversized_file_returns_422(
        self, client: AsyncClient,
    ) -> None:
        item_id = await _seed_collection_item(client)
        # 11 MB of zeros — exceeds the 10 MB limit
        oversized = b"\x00" * (11 * 1024 * 1024)
        response = await client.post(
            f"/api/items/{item_id}/images",
            files={"file": ("big.jpg", oversized, "image/jpeg")},
        )
        assert response.status_code == 422

    async def test_upload_to_nonexistent_item_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/items/nonexistent-id/images",
            files={"file": ("photo.jpg", TINY_JPEG, "image/jpeg")},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListImages:
    async def test_list_images_returns_200(
        self, client: AsyncClient,
    ) -> None:
        item_id = await _seed_collection_item(client)

        # Upload two images
        await client.post(
            f"/api/items/{item_id}/images",
            files={"file": ("a.jpg", TINY_JPEG, "image/jpeg")},
        )
        await client.post(
            f"/api/items/{item_id}/images",
            files={"file": ("b.png", TINY_JPEG, "image/png")},
        )

        response = await client.get(f"/api/items/{item_id}/images")
        assert response.status_code == 200
        images = response.json()
        assert len(images) == 2
        assert images[0]["is_primary"] is True
        assert images[1]["is_primary"] is False

    async def test_list_images_empty_returns_200(
        self, client: AsyncClient,
    ) -> None:
        item_id = await _seed_collection_item(client)
        response = await client.get(f"/api/items/{item_id}/images")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDeleteImage:
    async def test_delete_image_returns_204(
        self, client: AsyncClient,
    ) -> None:
        item_id = await _seed_collection_item(client)
        upload = await client.post(
            f"/api/items/{item_id}/images",
            files={"file": ("photo.jpg", TINY_JPEG, "image/jpeg")},
        )
        image_id = upload.json()["id"]

        response = await client.delete(f"/api/images/{image_id}")
        assert response.status_code == 204

        # Verify it's gone
        listing = await client.get(f"/api/items/{item_id}/images")
        assert len(listing.json()) == 0

    async def test_delete_nonexistent_image_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/images/nonexistent-id")
        assert response.status_code == 404
