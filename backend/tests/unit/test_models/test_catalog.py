"""Tests for Catalog and CatalogItem SQLAlchemy models."""

import uuid

import pytest
from sqlalchemy import Boolean, Date, Integer, String, Text, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory


# ---------------------------------------------------------------------------
# Catalog column tests
# ---------------------------------------------------------------------------


class TestCatalogColumns:
    """Verify Catalog has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert Catalog.__tablename__ == "catalogs"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(Catalog)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "sub_category_id", "name", "description", "version",
            "source_type", "source_name", "source_url", "total_items",
            "is_official", "is_active", "is_public", "created_by",
            "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_sub_category_id_is_foreign_key(self) -> None:
        mapper = inspect(Catalog)
        col = mapper.columns["sub_category_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "sub_categories.id" in fk_targets

    def test_sub_category_id_not_nullable(self) -> None:
        mapper = inspect(Catalog)
        col = mapper.columns["sub_category_id"]
        assert col.nullable is False

    def test_name_column_properties(self) -> None:
        mapper = inspect(Catalog)
        col = mapper.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is False

    def test_description_column_is_nullable_text(self) -> None:
        mapper = inspect(Catalog)
        col = mapper.columns["description"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_total_items_column_properties(self) -> None:
        mapper = inspect(Catalog)
        col = mapper.columns["total_items"]
        assert isinstance(col.type, Integer)

    def test_is_active_column_properties(self) -> None:
        mapper = inspect(Catalog)
        col = mapper.columns["is_active"]
        assert isinstance(col.type, Boolean)


# ---------------------------------------------------------------------------
# CatalogItem column tests
# ---------------------------------------------------------------------------


class TestCatalogItemColumns:
    """Verify CatalogItem has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert CatalogItem.__tablename__ == "catalog_items"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(CatalogItem)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "catalog_id", "title", "subtitle", "description",
            "release_date", "manufacturer", "publisher", "developer",
            "brand", "language", "region", "rarity", "custom_fields",
            "cover_image_url", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_catalog_id_is_foreign_key(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["catalog_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "catalogs.id" in fk_targets

    def test_catalog_id_not_nullable(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["catalog_id"]
        assert col.nullable is False

    def test_title_column_properties(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["title"]
        assert isinstance(col.type, String)
        assert col.type.length == 500
        assert col.nullable is False

    def test_subtitle_column_is_nullable(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["subtitle"]
        assert isinstance(col.type, String)
        assert col.type.length == 500
        assert col.nullable is True

    def test_release_date_column_properties(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["release_date"]
        assert isinstance(col.type, Date)
        assert col.nullable is True

    def test_custom_fields_column_is_json(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["custom_fields"]
        assert isinstance(col.type, JSON)
        assert col.nullable is False

    def test_cover_image_url_column_properties(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["cover_image_url"]
        assert isinstance(col.type, String)
        assert col.type.length == 1000
        assert col.nullable is True

    def test_rarity_column_properties(self) -> None:
        mapper = inspect(CatalogItem)
        col = mapper.columns["rarity"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestCatalogRelationships:
    """Verify relationships between Catalog, CatalogItem, and SubCategory."""

    def test_catalog_has_items_relationship(self) -> None:
        mapper = inspect(Catalog)
        rel_names = {r.key for r in mapper.relationships}
        assert "items" in rel_names

    def test_catalog_has_sub_category_relationship(self) -> None:
        mapper = inspect(Catalog)
        rel_names = {r.key for r in mapper.relationships}
        assert "sub_category" in rel_names

    def test_catalog_item_has_catalog_relationship(self) -> None:
        mapper = inspect(CatalogItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "catalog" in rel_names

    def test_items_relationship_cascade_includes_delete_orphan(self) -> None:
        mapper = inspect(Catalog)
        rel = mapper.relationships["items"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True


# ---------------------------------------------------------------------------
# Persistence / cascade tests (async with in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _catalog_engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def catalog_session(_catalog_engine):
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _catalog_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


async def _create_sub_category(session: AsyncSession) -> SubCategory:
    """Helper to create a MainCategory + SubCategory for FK references."""
    main = MainCategory(name="Videojuegos", slug="videojuegos", sort_order=0)
    session.add(main)
    await session.commit()
    await session.refresh(main)

    sub = SubCategory(
        main_category_id=main.id,
        name="Consolas",
        slug="consolas",
        sort_order=0,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


class TestCatalogPersistence:
    """Integration-style tests for persisting catalogs and catalog items."""

    @pytest.mark.asyncio
    async def test_create_catalog_persists(self, catalog_session: AsyncSession) -> None:
        sub = await _create_sub_category(catalog_session)

        catalog = Catalog(
            sub_category_id=sub.id,
            name="N64 Games",
            description="All Nintendo 64 games",
        )
        catalog_session.add(catalog)
        await catalog_session.commit()
        await catalog_session.refresh(catalog)

        assert catalog.id is not None
        assert len(catalog.id) == 36
        uuid.UUID(catalog.id)  # validates UUID format
        assert catalog.name == "N64 Games"
        assert catalog.total_items == 0
        assert catalog.is_active is True
        assert catalog.created_at is not None

    @pytest.mark.asyncio
    async def test_create_catalog_item_linked_to_catalog(
        self, catalog_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(catalog_session)
        catalog = Catalog(sub_category_id=sub.id, name="SNES Games")
        catalog_session.add(catalog)
        await catalog_session.commit()
        await catalog_session.refresh(catalog)

        item = CatalogItem(
            catalog_id=catalog.id,
            title="Super Mario World",
            custom_fields={"genre": "platformer"},
        )
        catalog_session.add(item)
        await catalog_session.commit()
        await catalog_session.refresh(item)

        assert item.id is not None
        assert item.catalog_id == catalog.id
        assert item.title == "Super Mario World"
        assert item.custom_fields == {"genre": "platformer"}

    @pytest.mark.asyncio
    async def test_cascade_delete_removes_catalog_items(
        self, catalog_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(catalog_session)
        catalog = Catalog(sub_category_id=sub.id, name="PS1 Games")
        item1 = CatalogItem(title="Final Fantasy VII", custom_fields={})
        item2 = CatalogItem(title="Crash Bandicoot", custom_fields={})
        catalog.items = [item1, item2]

        catalog_session.add(catalog)
        await catalog_session.commit()

        # Delete the catalog
        await catalog_session.delete(catalog)
        await catalog_session.commit()

        # Verify catalog items are gone
        result = await catalog_session.execute(select(CatalogItem))
        remaining = result.scalars().all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_catalog_defaults_applied(
        self, catalog_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(catalog_session)
        catalog = Catalog(sub_category_id=sub.id, name="Defaults Test")
        catalog_session.add(catalog)
        await catalog_session.commit()
        await catalog_session.refresh(catalog)

        assert catalog.total_items == 0
        assert catalog.is_active is True
        assert catalog.is_official is False
        assert catalog.is_public is False

    @pytest.mark.asyncio
    async def test_catalog_item_defaults_applied(
        self, catalog_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(catalog_session)
        catalog = Catalog(sub_category_id=sub.id, name="Defaults Catalog")
        catalog_session.add(catalog)
        await catalog_session.commit()
        await catalog_session.refresh(catalog)

        item = CatalogItem(
            catalog_id=catalog.id,
            title="Test Item",
            custom_fields={},
        )
        catalog_session.add(item)
        await catalog_session.commit()
        await catalog_session.refresh(item)

        assert item.is_limited_edition is False
        assert item.is_promotional is False
        assert item.is_prototype is False
        assert item.custom_fields == {}

    @pytest.mark.asyncio
    async def test_relationship_back_populates(
        self, catalog_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(catalog_session)
        catalog = Catalog(sub_category_id=sub.id, name="Back Pop Test")
        item = CatalogItem(title="Test Item", custom_fields={})
        catalog.items.append(item)

        catalog_session.add(catalog)
        await catalog_session.commit()
        await catalog_session.refresh(item)

        assert item.catalog is not None
        assert item.catalog.id == catalog.id

    @pytest.mark.asyncio
    async def test_repr_methods(self) -> None:
        catalog = Catalog(name="Test Catalog")
        item = CatalogItem(title="Test Item")
        assert "Catalog" in repr(catalog)
        assert "CatalogItem" in repr(item)
