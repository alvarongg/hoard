"""Property-based tests for ImageService using hypothesis.

**Validates: Requirements REQ-009.4, REQ-009.2**

Property 5: Imagen primaria única —
    ∀ item: COUNT(images WHERE is_primary=True) <= 1

Property 6: Integridad de archivos de imagen —
    mime_type ∈ {image/jpeg, image/png, image/webp}
"""

from __future__ import annotations

import tempfile
from unittest.mock import AsyncMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.image import ALLOWED_IMAGE_TYPES
from api.services.image_service import ImageService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


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


async def _seed_collection_item(session: AsyncSession) -> CollectionItem:
    """Create full chain: MainCategory → SubCategory → Catalog →
    CatalogItem → Collection → CollectionItem and return the CollectionItem.
    """
    main = MainCategory(name="Videogames", slug="videogames")
    session.add(main)
    await session.flush()

    sub = SubCategory(main_category_id=main.id, name="N64", slug="n64")
    session.add(sub)
    await session.flush()

    catalog = Catalog(sub_category_id=sub.id, name="N64 Games")
    session.add(catalog)
    await session.flush()

    catalog_item = CatalogItem(catalog_id=catalog.id, title="Zelda OoT")
    session.add(catalog_item)
    await session.flush()

    collection = Collection(
        name="My N64",
        collection_type="single_category",
        restricted_to_sub_category_id=sub.id,
    )
    session.add(collection)
    await session.flush()

    item = CollectionItem(
        collection_id=collection.id,
        catalog_item_id=catalog_item.id,
        condition="excellent",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

allowed_mime_types = st.sampled_from(sorted(ALLOWED_IMAGE_TYPES))

mime_type_lists = st.lists(allowed_mime_types, min_size=1, max_size=5)


# ---------------------------------------------------------------------------
# Property 5: Imagen primaria única
# ---------------------------------------------------------------------------


class TestUniquePrimaryImageProperty:
    """Property 5: Unique primary image per item.

    **Validates: Requirements REQ-009.4**

    For any item, after uploading N images (N >= 1), at most one image
    should have is_primary=True.
    """

    @given(mime_types=mime_type_lists)
    @settings(max_examples=15, deadline=None)
    @pytest.mark.asyncio
    async def test_at_most_one_primary_image_per_item(
        self, mime_types: list[str],
    ) -> None:
        """After uploading multiple images, COUNT(is_primary=True) <= 1."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:", echo=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False,
        )

        with tempfile.TemporaryDirectory() as upload_dir:
            async with factory() as session:
                item = await _seed_collection_item(session)
                service = ImageService(session, upload_dir)

                for i, mime in enumerate(mime_types):
                    ext = MIME_TO_EXT[mime]
                    file = _make_upload_file(
                        filename=f"img_{i}{ext}",
                        content_type=mime,
                    )
                    await service.upload(item.id, file)

                images = await service.list_by_item(item.id)
                primary_count = sum(1 for img in images if img.is_primary)

                assert primary_count <= 1
                assert len(images) == len(mime_types)

        await engine.dispose()


# ---------------------------------------------------------------------------
# Property 6: Integridad de archivos de imagen
# ---------------------------------------------------------------------------


class TestImageMimeTypeIntegrityProperty:
    """Property 6: Image file integrity — mime_type ∈ ALLOWED_IMAGE_TYPES.

    **Validates: Requirements REQ-009.2**

    For any allowed MIME type, uploading an image with that type must
    succeed and the stored mime_type must be in the allowed set.
    """

    @given(mime_type=allowed_mime_types)
    @settings(max_examples=15, deadline=None)
    @pytest.mark.asyncio
    async def test_uploaded_image_mime_type_in_allowed_set(
        self, mime_type: str,
    ) -> None:
        """Every uploaded image has its mime_type within ALLOWED_IMAGE_TYPES."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:", echo=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False,
        )

        with tempfile.TemporaryDirectory() as upload_dir:
            async with factory() as session:
                item = await _seed_collection_item(session)
                service = ImageService(session, upload_dir)

                ext = MIME_TO_EXT[mime_type]
                file = _make_upload_file(
                    filename=f"test{ext}",
                    content_type=mime_type,
                )
                result = await service.upload(item.id, file)

                assert result.mime_type in ALLOWED_IMAGE_TYPES
                assert result.mime_type == mime_type

        await engine.dispose()
