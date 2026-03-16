"""Tests for ItemImage SQLAlchemy model."""

import uuid

import pytest
from sqlalchemy import Boolean, DateTime, Integer, String, Text, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.image import ItemImage


# ---------------------------------------------------------------------------
# Column tests
# ---------------------------------------------------------------------------


class TestItemImageColumns:
    """Verify ItemImage has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert ItemImage.__tablename__ == "item_images"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(ItemImage)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "collection_item_id", "file_path", "file_name",
            "file_size", "mime_type", "width", "height", "image_type",
            "description", "sort_order", "is_primary", "uploaded_at",
        }
        assert expected.issubset(col_names)

    def test_collection_item_id_is_foreign_key(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["collection_item_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "collection_items.id" in fk_targets

    def test_collection_item_id_not_nullable(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["collection_item_id"]
        assert col.nullable is False

    def test_file_path_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["file_path"]
        assert isinstance(col.type, String)
        assert col.type.length == 1000
        assert col.nullable is False

    def test_file_name_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["file_name"]
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False

    def test_file_size_column_is_nullable_integer(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["file_size"]
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_mime_type_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["mime_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_width_and_height_columns(self) -> None:
        mapper = inspect(ItemImage)
        for name in ("width", "height"):
            col = mapper.columns[name]
            assert isinstance(col.type, Integer)
            assert col.nullable is True

    def test_image_type_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["image_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_description_column_is_nullable_text(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["description"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_sort_order_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["sort_order"]
        assert isinstance(col.type, Integer)

    def test_is_primary_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["is_primary"]
        assert isinstance(col.type, Boolean)

    def test_uploaded_at_column_properties(self) -> None:
        mapper = inspect(ItemImage)
        col = mapper.columns["uploaded_at"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is False

    def test_does_not_have_created_at_updated_at(self) -> None:
        """ItemImage uses uploaded_at instead of TimestampMixin."""
        mapper = inspect(ItemImage)
        col_names = {col.name for col in mapper.columns}
        assert "updated_at" not in col_names


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestItemImageRelationships:
    """Verify ItemImage relationships."""

    def test_has_collection_item_relationship(self) -> None:
        mapper = inspect(ItemImage)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection_item" in rel_names


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _image_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def image_session(_image_engine):
    factory = async_sessionmaker(
        _image_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


async def _create_collection_item(session: AsyncSession) -> CollectionItem:
    """Helper to create prerequisite objects for an ItemImage."""
    main = MainCategory(name="Videojuegos", slug="videojuegos", sort_order=0)
    session.add(main)
    await session.commit()
    await session.refresh(main)

    sub = SubCategory(
        main_category_id=main.id, name="Consolas", slug="consolas", sort_order=0,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    catalog = Catalog(sub_category_id=sub.id, name="N64 Games")
    session.add(catalog)
    await session.commit()
    await session.refresh(catalog)

    cat_item = CatalogItem(
        catalog_id=catalog.id, title="Super Mario 64", custom_fields={},
    )
    session.add(cat_item)
    await session.commit()
    await session.refresh(cat_item)

    collection = Collection(name="My Collection", collection_type="multi_category")
    session.add(collection)
    await session.commit()
    await session.refresh(collection)

    ci = CollectionItem(
        collection_id=collection.id,
        catalog_item_id=cat_item.id,
        condition="mint",
        custom_fields={},
    )
    session.add(ci)
    await session.commit()
    await session.refresh(ci)
    return ci


class TestItemImagePersistence:
    """Integration-style tests for persisting item images."""

    @pytest.mark.asyncio
    async def test_create_image_persists(self, image_session: AsyncSession) -> None:
        ci = await _create_collection_item(image_session)

        image = ItemImage(
            collection_item_id=ci.id,
            file_path="/uploads/test/img.jpg",
            file_name="img.jpg",
            file_size=12345,
            mime_type="image/jpeg",
        )
        image_session.add(image)
        await image_session.commit()
        await image_session.refresh(image)

        assert image.id is not None
        assert len(image.id) == 36
        uuid.UUID(image.id)
        assert image.file_name == "img.jpg"
        assert image.uploaded_at is not None

    @pytest.mark.asyncio
    async def test_is_primary_defaults_to_false(
        self, image_session: AsyncSession,
    ) -> None:
        ci = await _create_collection_item(image_session)

        image = ItemImage(
            collection_item_id=ci.id,
            file_path="/uploads/test/img.png",
            file_name="img.png",
        )
        image_session.add(image)
        await image_session.commit()
        await image_session.refresh(image)

        assert image.is_primary is False
        assert image.sort_order == 0

    @pytest.mark.asyncio
    async def test_repr_method(self) -> None:
        image = ItemImage(file_name="test.jpg")
        assert "ItemImage" in repr(image)
        assert "test.jpg" in repr(image)
