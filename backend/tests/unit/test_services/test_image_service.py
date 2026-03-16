"""Unit tests for ImageService business logic.

Tests cover image upload (validation, primary flag, file persistence),
listing by item, and deletion (record + file cleanup).

Requirements: REQ-009, REQ-015
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.image import ItemImage
from api.services.image_service import ImageService
from core.exceptions import FileValidationError, NotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(_engine) -> AsyncSession:
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture()
def upload_dir(tmp_path: Path) -> str:
    """Provide a temporary upload directory."""
    return str(tmp_path / "uploads")


@pytest.fixture()
def service(db_session: AsyncSession, upload_dir: str) -> ImageService:
    """Provide an ImageService wired to the test session."""
    return ImageService(db_session, upload_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_collection_item(db_session: AsyncSession) -> CollectionItem:
    """Create the full chain: MainCategory → SubCategory → Catalog →
    CatalogItem → Collection → CollectionItem and return the CollectionItem.
    """
    main = MainCategory(name="Videogames", slug="videogames")
    db_session.add(main)
    await db_session.flush()

    sub = SubCategory(main_category_id=main.id, name="N64", slug="n64")
    db_session.add(sub)
    await db_session.flush()

    catalog = Catalog(sub_category_id=sub.id, name="N64 Games")
    db_session.add(catalog)
    await db_session.flush()

    catalog_item = CatalogItem(catalog_id=catalog.id, title="Zelda OoT")
    db_session.add(catalog_item)
    await db_session.flush()

    collection = Collection(
        name="My N64",
        collection_type="single_category",
        restricted_to_sub_category_id=sub.id,
    )
    db_session.add(collection)
    await db_session.flush()

    item = CollectionItem(
        collection_id=collection.id,
        catalog_item_id=catalog_item.id,
        condition="excellent",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


def _make_upload_file(
    filename: str = "photo.jpg",
    content_type: str = "image/jpeg",
    content: bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100,
) -> AsyncMock:
    """Build a mock UploadFile with the given attributes."""
    mock = AsyncMock()
    mock.filename = filename
    mock.content_type = content_type
    mock.read = AsyncMock(return_value=content)
    return mock


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------


class TestUpload:
    """Tests for ImageService.upload."""

    @pytest.mark.asyncio
    async def test_upload_valid_image_returns_image_record(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)
        file = _make_upload_file()

        result = await service.upload(item.id, file)

        assert result.id is not None
        assert result.collection_item_id == item.id
        assert result.file_name == "photo.jpg"
        assert result.mime_type == "image/jpeg"
        assert result.file_size > 0

    @pytest.mark.asyncio
    async def test_upload_invalid_mime_type_raises_file_validation_error(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)
        file = _make_upload_file(
            filename="doc.pdf",
            content_type="application/pdf",
        )

        with pytest.raises(FileValidationError, match="not allowed"):
            await service.upload(item.id, file)

    @pytest.mark.asyncio
    async def test_upload_oversized_file_raises_file_validation_error(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)
        big_content = b"\x00" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        file = _make_upload_file(content=big_content)

        with pytest.raises(FileValidationError, match="exceeds"):
            await service.upload(item.id, file)

    @pytest.mark.asyncio
    async def test_first_image_is_primary(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)
        file = _make_upload_file()

        result = await service.upload(item.id, file)

        assert result.is_primary is True

    @pytest.mark.asyncio
    async def test_second_image_is_not_primary(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)

        first = await service.upload(item.id, _make_upload_file())
        second = await service.upload(
            item.id,
            _make_upload_file(filename="back.png", content_type="image/png"),
        )

        assert first.is_primary is True
        assert second.is_primary is False

    @pytest.mark.asyncio
    async def test_upload_saves_file_to_disk(
        self,
        service: ImageService,
        db_session: AsyncSession,
        upload_dir: str,
    ) -> None:
        item = await _seed_collection_item(db_session)
        file = _make_upload_file()

        result = await service.upload(item.id, file)

        full_path = Path(upload_dir) / result.file_path
        assert full_path.exists()

    @pytest.mark.asyncio
    async def test_upload_to_nonexistent_item_raises_not_found(
        self,
        service: ImageService,
    ) -> None:
        file = _make_upload_file()

        with pytest.raises(NotFoundError, match="Collection item"):
            await service.upload("nonexistent-id", file)

    @pytest.mark.asyncio
    async def test_upload_webp_image_succeeds(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)
        file = _make_upload_file(
            filename="art.webp", content_type="image/webp",
        )

        result = await service.upload(item.id, file)

        assert result.mime_type == "image/webp"


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------


class TestListByItem:
    """Tests for ImageService.list_by_item."""

    @pytest.mark.asyncio
    async def test_list_returns_images_for_item(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)
        await service.upload(item.id, _make_upload_file(filename="a.jpg"))
        await service.upload(
            item.id,
            _make_upload_file(filename="b.png", content_type="image/png"),
        )

        images = await service.list_by_item(item.id)

        assert len(images) == 2

    @pytest.mark.asyncio
    async def test_list_empty_returns_empty_list(
        self,
        service: ImageService,
        db_session: AsyncSession,
    ) -> None:
        item = await _seed_collection_item(db_session)

        images = await service.list_by_item(item.id)

        assert images == []


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


class TestDelete:
    """Tests for ImageService.delete."""

    @pytest.mark.asyncio
    async def test_delete_image_removes_file_and_record(
        self,
        service: ImageService,
        db_session: AsyncSession,
        upload_dir: str,
    ) -> None:
        item = await _seed_collection_item(db_session)
        image = await service.upload(item.id, _make_upload_file())
        full_path = Path(upload_dir) / image.file_path
        assert full_path.exists()

        await service.delete(image.id)

        assert not full_path.exists()
        images = await service.list_by_item(item.id)
        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_not_found(
        self,
        service: ImageService,
    ) -> None:
        with pytest.raises(NotFoundError, match="Image"):
            await service.delete("nonexistent-id")

    @pytest.mark.asyncio
    async def test_delete_with_missing_file_does_not_error(
        self,
        service: ImageService,
        db_session: AsyncSession,
        upload_dir: str,
    ) -> None:
        """Deleting an image whose file was already removed should not raise."""
        item = await _seed_collection_item(db_session)
        image = await service.upload(item.id, _make_upload_file())

        # Manually remove the file before calling delete
        full_path = Path(upload_dir) / image.file_path
        full_path.unlink()

        await service.delete(image.id)

        images = await service.list_by_item(item.id)
        assert len(images) == 0
