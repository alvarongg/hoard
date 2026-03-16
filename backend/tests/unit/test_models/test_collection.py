"""Tests for Collection and CollectionItem SQLAlchemy models."""

import uuid

import pytest
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.supplier import Supplier  # noqa: F401 — needed for FK resolution


# ---------------------------------------------------------------------------
# Collection column tests
# ---------------------------------------------------------------------------


class TestCollectionColumns:
    """Verify Collection has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert Collection.__tablename__ == "collections"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(Collection)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "name", "description", "collection_type", "theme",
            "theme_description", "restricted_to_sub_category_id",
            "goal_description", "goal_items_count", "display_order",
            "is_public", "is_active", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_name_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is False

    def test_description_column_is_nullable_text(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["description"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_collection_type_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["collection_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 50

    def test_theme_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["theme"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_restricted_to_sub_category_id_is_foreign_key(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["restricted_to_sub_category_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "sub_categories.id" in fk_targets

    def test_restricted_to_sub_category_id_is_nullable(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["restricted_to_sub_category_id"]
        assert col.nullable is True

    def test_goal_items_count_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["goal_items_count"]
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_display_order_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["display_order"]
        assert isinstance(col.type, String)
        assert col.type.length == 50

    def test_is_public_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["is_public"]
        assert isinstance(col.type, Boolean)

    def test_is_active_column_properties(self) -> None:
        mapper = inspect(Collection)
        col = mapper.columns["is_active"]
        assert isinstance(col.type, Boolean)


# ---------------------------------------------------------------------------
# CollectionItem column tests
# ---------------------------------------------------------------------------


class TestCollectionItemColumns:
    """Verify CollectionItem has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert CollectionItem.__tablename__ == "collection_items"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(CollectionItem)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "collection_id", "catalog_item_id", "title_override",
            "notes", "condition", "condition_notes", "is_complete",
            "completeness_notes", "variant_description", "is_authentic",
            "authenticity_notes", "storage_location", "storage_position",
            "purchase_price", "purchase_currency", "purchase_date",
            "current_market_value", "current_value_currency",
            "last_value_update", "value_source", "acquisition_date",
            "acquisition_type", "supplier_id", "is_graded",
            "grading_company", "grade", "certification_number",
            "grading_date", "is_insured", "insurance_value",
            "insurance_company", "custom_fields", "tags", "for_sale",
            "asking_price", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_collection_id_is_foreign_key(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["collection_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "collections.id" in fk_targets

    def test_collection_id_not_nullable(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["collection_id"]
        assert col.nullable is False

    def test_catalog_item_id_is_foreign_key(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["catalog_item_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "catalog_items.id" in fk_targets

    def test_catalog_item_id_not_nullable(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["catalog_item_id"]
        assert col.nullable is False

    def test_condition_column_properties(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["condition"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is False

    def test_purchase_price_column_is_numeric(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["purchase_price"]
        assert isinstance(col.type, Numeric)
        assert col.nullable is True

    def test_purchase_currency_column_properties(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["purchase_currency"]
        assert isinstance(col.type, String)
        assert col.type.length == 3

    def test_purchase_date_column_properties(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["purchase_date"]
        assert isinstance(col.type, Date)
        assert col.nullable is True

    def test_custom_fields_column_is_json(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["custom_fields"]
        assert isinstance(col.type, JSON)
        assert col.nullable is False

    def test_tags_column_is_json(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["tags"]
        assert isinstance(col.type, JSON)

    def test_supplier_id_is_foreign_key(self) -> None:
        mapper = inspect(CollectionItem)
        col = mapper.columns["supplier_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "suppliers.id" in fk_targets


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestCollectionRelationships:
    """Verify relationships between Collection, CollectionItem, and related models."""

    def test_collection_has_items_relationship(self) -> None:
        mapper = inspect(Collection)
        rel_names = {r.key for r in mapper.relationships}
        assert "items" in rel_names

    def test_collection_has_restricted_sub_category_relationship(self) -> None:
        mapper = inspect(Collection)
        rel_names = {r.key for r in mapper.relationships}
        assert "restricted_sub_category" in rel_names

    def test_collection_item_has_collection_relationship(self) -> None:
        mapper = inspect(CollectionItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection" in rel_names

    def test_collection_item_has_catalog_item_relationship(self) -> None:
        mapper = inspect(CollectionItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "catalog_item" in rel_names

    def test_items_relationship_cascade_includes_delete_orphan(self) -> None:
        mapper = inspect(Collection)
        rel = mapper.relationships["items"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True


# ---------------------------------------------------------------------------
# Persistence / cascade tests (async with in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _collection_engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def collection_session(_collection_engine):
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _collection_engine, class_=AsyncSession, expire_on_commit=False,
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


async def _create_catalog_item(
    session: AsyncSession, sub: SubCategory,
) -> CatalogItem:
    """Helper to create a Catalog + CatalogItem for FK references."""
    catalog = Catalog(sub_category_id=sub.id, name="N64 Games")
    session.add(catalog)
    await session.commit()
    await session.refresh(catalog)

    item = CatalogItem(
        catalog_id=catalog.id,
        title="Super Mario 64",
        custom_fields={},
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


class TestCollectionPersistence:
    """Integration-style tests for persisting collections and collection items."""

    @pytest.mark.asyncio
    async def test_create_collection_persists(
        self, collection_session: AsyncSession,
    ) -> None:
        collection = Collection(
            name="My N64 Collection",
            description="All my N64 stuff",
            collection_type="multi_category",
        )
        collection_session.add(collection)
        await collection_session.commit()
        await collection_session.refresh(collection)

        assert collection.id is not None
        assert len(collection.id) == 36
        uuid.UUID(collection.id)  # validates UUID format
        assert collection.name == "My N64 Collection"
        assert collection.created_at is not None

    @pytest.mark.asyncio
    async def test_collection_defaults_applied(
        self, collection_session: AsyncSession,
    ) -> None:
        collection = Collection(
            name="Defaults Test",
            collection_type="mixed",
        )
        collection_session.add(collection)
        await collection_session.commit()
        await collection_session.refresh(collection)

        assert collection.display_order == "custom"
        assert collection.is_public is False
        assert collection.is_active is True
        assert collection.collection_type == "mixed"

    @pytest.mark.asyncio
    async def test_create_collection_item_linked_to_collection(
        self, collection_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(collection_session)
        catalog_item = await _create_catalog_item(collection_session, sub)

        collection = Collection(
            name="Test Collection",
            collection_type="multi_category",
        )
        collection_session.add(collection)
        await collection_session.commit()
        await collection_session.refresh(collection)

        ci = CollectionItem(
            collection_id=collection.id,
            catalog_item_id=catalog_item.id,
            condition="mint",
            custom_fields={},
        )
        collection_session.add(ci)
        await collection_session.commit()
        await collection_session.refresh(ci)

        assert ci.id is not None
        assert ci.collection_id == collection.id
        assert ci.catalog_item_id == catalog_item.id
        assert ci.condition == "mint"

    @pytest.mark.asyncio
    async def test_collection_item_defaults_applied(
        self, collection_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(collection_session)
        catalog_item = await _create_catalog_item(collection_session, sub)

        collection = Collection(
            name="Defaults Collection",
            collection_type="mixed",
        )
        collection_session.add(collection)
        await collection_session.commit()
        await collection_session.refresh(collection)

        ci = CollectionItem(
            collection_id=collection.id,
            catalog_item_id=catalog_item.id,
            condition="good",
            custom_fields={},
        )
        collection_session.add(ci)
        await collection_session.commit()
        await collection_session.refresh(ci)

        assert ci.is_complete is False
        assert ci.is_authentic is True
        assert ci.purchase_currency == "USD"
        assert ci.is_graded is False
        assert ci.is_insured is False
        assert ci.for_sale is False
        assert ci.custom_fields == {}

    @pytest.mark.asyncio
    async def test_cascade_delete_removes_collection_items(
        self, collection_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(collection_session)
        catalog_item = await _create_catalog_item(collection_session, sub)

        collection = Collection(
            name="Cascade Test",
            collection_type="mixed",
        )
        ci1 = CollectionItem(
            catalog_item_id=catalog_item.id,
            condition="mint",
            custom_fields={},
        )
        ci2 = CollectionItem(
            catalog_item_id=catalog_item.id,
            condition="good",
            custom_fields={},
        )
        collection.items = [ci1, ci2]

        collection_session.add(collection)
        await collection_session.commit()

        # Delete the collection
        await collection_session.delete(collection)
        await collection_session.commit()

        # Verify collection items are gone
        result = await collection_session.execute(select(CollectionItem))
        remaining = result.scalars().all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_relationship_back_populates(
        self, collection_session: AsyncSession,
    ) -> None:
        sub = await _create_sub_category(collection_session)
        catalog_item = await _create_catalog_item(collection_session, sub)

        collection = Collection(
            name="Back Pop Test",
            collection_type="mixed",
        )
        ci = CollectionItem(
            catalog_item_id=catalog_item.id,
            condition="excellent",
            custom_fields={},
        )
        collection.items.append(ci)

        collection_session.add(collection)
        await collection_session.commit()
        await collection_session.refresh(ci)

        assert ci.collection is not None
        assert ci.collection.id == collection.id

    @pytest.mark.asyncio
    async def test_repr_methods(self) -> None:
        collection = Collection(name="Test Collection")
        ci = CollectionItem(collection_id="fake-id")
        assert "Collection" in repr(collection)
        assert "CollectionItem" in repr(ci)
