"""Tests for AccessoryStock and ItemComponent SQLAlchemy models."""

import uuid

import pytest
from sqlalchemy import Boolean, Integer, Numeric, String, Text, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.standard_component import StandardComponent
from api.models.supplier import Supplier
from api.models.accessory import AccessoryStock, ItemComponent


# ---------------------------------------------------------------------------
# AccessoryStock column tests
# ---------------------------------------------------------------------------


class TestAccessoryStockColumns:
    """Verify AccessoryStock has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert AccessoryStock.__tablename__ == "accessories_stock"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(AccessoryStock)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "name", "category", "subcategory",
            "compatible_sub_categories", "size_specifications",
            "quantity_total", "quantity_in_use",
            "minimum_stock_alert", "reorder_quantity",
            "unit_cost", "currency",
            "supplier_id", "supplier_sku", "supplier_url",
            "notes", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_name_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is False

    def test_category_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["category"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_subcategory_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["subcategory"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_compatible_sub_categories_is_json(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["compatible_sub_categories"]
        assert isinstance(col.type, JSON)

    def test_size_specifications_is_json(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["size_specifications"]
        assert isinstance(col.type, JSON)

    def test_quantity_total_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["quantity_total"]
        assert isinstance(col.type, Integer)

    def test_quantity_in_use_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["quantity_in_use"]
        assert isinstance(col.type, Integer)

    def test_minimum_stock_alert_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["minimum_stock_alert"]
        assert isinstance(col.type, Integer)

    def test_unit_cost_column_is_numeric(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["unit_cost"]
        assert isinstance(col.type, Numeric)
        assert col.nullable is True

    def test_currency_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["currency"]
        assert isinstance(col.type, String)
        assert col.type.length == 3

    def test_supplier_id_is_foreign_key(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["supplier_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "suppliers.id" in fk_targets

    def test_supplier_sku_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["supplier_sku"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_supplier_url_column_properties(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["supplier_url"]
        assert isinstance(col.type, String)
        assert col.type.length == 500
        assert col.nullable is True

    def test_notes_column_is_nullable_text(self) -> None:
        mapper = inspect(AccessoryStock)
        col = mapper.columns["notes"]
        assert isinstance(col.type, Text)
        assert col.nullable is True


# ---------------------------------------------------------------------------
# ItemComponent column tests
# ---------------------------------------------------------------------------


class TestItemComponentColumns:
    """Verify ItemComponent has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert ItemComponent.__tablename__ == "item_components"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(ItemComponent)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "collection_item_id", "standard_component_id",
            "component_name", "component_type",
            "is_present", "condition", "condition_notes",
            "variant_description",
            "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_collection_item_id_is_foreign_key(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["collection_item_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "collection_items.id" in fk_targets

    def test_collection_item_id_not_nullable(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["collection_item_id"]
        assert col.nullable is False

    def test_standard_component_id_is_foreign_key(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["standard_component_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "standard_components.id" in fk_targets

    def test_standard_component_id_is_nullable(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["standard_component_id"]
        assert col.nullable is True

    def test_component_name_column_properties(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["component_name"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False

    def test_component_type_column_properties(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["component_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_is_present_column_properties(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["is_present"]
        assert isinstance(col.type, Boolean)

    def test_condition_column_properties(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["condition"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_condition_notes_column_is_nullable_text(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["condition_notes"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_variant_description_column_properties(self) -> None:
        mapper = inspect(ItemComponent)
        col = mapper.columns["variant_description"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is True


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestAccessoryRelationships:
    """Verify relationships on accessory models."""

    def test_accessory_stock_has_supplier_relationship(self) -> None:
        mapper = inspect(AccessoryStock)
        rel_names = {r.key for r in mapper.relationships}
        assert "supplier" in rel_names

    def test_item_component_has_collection_item_relationship(self) -> None:
        mapper = inspect(ItemComponent)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection_item" in rel_names


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _accessory_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def accessory_session(_accessory_engine):
    factory = async_sessionmaker(
        _accessory_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


async def _create_collection_item(session: AsyncSession) -> CollectionItem:
    """Helper to create prerequisite objects for an ItemComponent."""
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


class TestAccessoryStockPersistence:
    """Integration-style tests for persisting accessory stock."""

    @pytest.mark.asyncio
    async def test_create_accessory_stock_persists(
        self, accessory_session: AsyncSession,
    ) -> None:
        acc = AccessoryStock(
            name="N64 Cartridge Protector",
            category="protectors",
            subcategory="cartridge",
        )
        accessory_session.add(acc)
        await accessory_session.commit()
        await accessory_session.refresh(acc)

        assert acc.id is not None
        assert len(acc.id) == 36
        uuid.UUID(acc.id)
        assert acc.name == "N64 Cartridge Protector"
        assert acc.created_at is not None

    @pytest.mark.asyncio
    async def test_accessory_stock_defaults_applied(
        self, accessory_session: AsyncSession,
    ) -> None:
        acc = AccessoryStock(name="Defaults Test")
        accessory_session.add(acc)
        await accessory_session.commit()
        await accessory_session.refresh(acc)

        assert acc.quantity_total == 0
        assert acc.quantity_in_use == 0
        assert acc.minimum_stock_alert == 5
        assert acc.currency == "USD"


class TestItemComponentPersistence:
    """Integration-style tests for persisting item components."""

    @pytest.mark.asyncio
    async def test_create_item_component_persists(
        self, accessory_session: AsyncSession,
    ) -> None:
        ci = await _create_collection_item(accessory_session)

        comp = ItemComponent(
            collection_item_id=ci.id,
            component_name="Box",
            component_type="required",
        )
        accessory_session.add(comp)
        await accessory_session.commit()
        await accessory_session.refresh(comp)

        assert comp.id is not None
        assert len(comp.id) == 36
        uuid.UUID(comp.id)
        assert comp.component_name == "Box"
        assert comp.collection_item_id == ci.id

    @pytest.mark.asyncio
    async def test_item_component_defaults_applied(
        self, accessory_session: AsyncSession,
    ) -> None:
        ci = await _create_collection_item(accessory_session)

        comp = ItemComponent(
            collection_item_id=ci.id,
            component_name="Manual",
        )
        accessory_session.add(comp)
        await accessory_session.commit()
        await accessory_session.refresh(comp)

        assert comp.is_present is True

    @pytest.mark.asyncio
    async def test_repr_methods(self) -> None:
        acc = AccessoryStock(name="Test Accessory")
        comp = ItemComponent(component_name="Box")
        assert "AccessoryStock" in repr(acc)
        assert "ItemComponent" in repr(comp)
        assert "Box" in repr(comp)
