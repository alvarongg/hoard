"""Tests for WishlistItem and WishlistSighting SQLAlchemy models."""

import uuid

import pytest
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.supplier import Supplier
from api.models.wishlist import WishlistItem, WishlistSighting


# ---------------------------------------------------------------------------
# WishlistItem column tests
# ---------------------------------------------------------------------------


class TestWishlistItemColumns:
    """Verify WishlistItem has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert WishlistItem.__tablename__ == "wishlist_items"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(WishlistItem)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "collection_id", "catalog_item_id",
            "desired_condition", "desired_condition_min",
            "must_be_complete", "desired_completeness_description",
            "max_price", "currency", "specific_variant_required",
            "variant_description", "priority", "urgency",
            "notes", "search_notes", "tags",
            "is_active", "is_acquired", "acquired_date",
            "acquired_collection_item_id",
            "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_collection_id_is_foreign_key(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["collection_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "collections.id" in fk_targets

    def test_collection_id_not_nullable(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["collection_id"]
        assert col.nullable is False

    def test_catalog_item_id_is_foreign_key(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["catalog_item_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "catalog_items.id" in fk_targets

    def test_catalog_item_id_not_nullable(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["catalog_item_id"]
        assert col.nullable is False

    def test_acquired_collection_item_id_is_foreign_key(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["acquired_collection_item_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "collection_items.id" in fk_targets

    def test_max_price_column_is_numeric(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["max_price"]
        assert isinstance(col.type, Numeric)
        assert col.nullable is True

    def test_currency_column_properties(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["currency"]
        assert isinstance(col.type, String)
        assert col.type.length == 3

    def test_priority_column_properties(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["priority"]
        assert isinstance(col.type, Integer)

    def test_urgency_column_properties(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["urgency"]
        assert isinstance(col.type, String)
        assert col.type.length == 50

    def test_tags_column_is_json(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["tags"]
        assert isinstance(col.type, JSON)

    def test_is_active_column_properties(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["is_active"]
        assert isinstance(col.type, Boolean)

    def test_is_acquired_column_properties(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["is_acquired"]
        assert isinstance(col.type, Boolean)

    def test_acquired_date_column_properties(self) -> None:
        mapper = inspect(WishlistItem)
        col = mapper.columns["acquired_date"]
        assert isinstance(col.type, Date)
        assert col.nullable is True


# ---------------------------------------------------------------------------
# WishlistSighting column tests
# ---------------------------------------------------------------------------


class TestWishlistSightingColumns:
    """Verify WishlistSighting has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert WishlistSighting.__tablename__ == "wishlist_sightings"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(WishlistSighting)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "wishlist_item_id", "sighted_at",
            "supplier_id", "location_description", "url",
            "price", "currency", "condition", "is_complete",
            "description", "image_urls",
            "is_available", "quantity_available", "last_checked_at",
            "contacted", "contacted_at", "contact_method", "response_notes",
            "decision", "decision_notes", "decision_date",
            "created_at",
        }
        assert expected.issubset(col_names)

    def test_wishlist_item_id_is_foreign_key(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["wishlist_item_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "wishlist_items.id" in fk_targets

    def test_wishlist_item_id_not_nullable(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["wishlist_item_id"]
        assert col.nullable is False

    def test_supplier_id_is_foreign_key(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["supplier_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "suppliers.id" in fk_targets

    def test_price_column_is_numeric_not_nullable(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["price"]
        assert isinstance(col.type, Numeric)
        assert col.nullable is False

    def test_image_urls_column_is_json(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["image_urls"]
        assert isinstance(col.type, JSON)

    def test_quantity_available_column_properties(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["quantity_available"]
        assert isinstance(col.type, Integer)

    def test_decision_column_properties(self) -> None:
        mapper = inspect(WishlistSighting)
        col = mapper.columns["decision"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestWishlistRelationships:
    """Verify relationships on wishlist models."""

    def test_wishlist_item_has_sightings_relationship(self) -> None:
        mapper = inspect(WishlistItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "sightings" in rel_names

    def test_wishlist_item_has_collection_relationship(self) -> None:
        mapper = inspect(WishlistItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection" in rel_names

    def test_wishlist_item_has_catalog_item_relationship(self) -> None:
        mapper = inspect(WishlistItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "catalog_item" in rel_names

    def test_sighting_has_wishlist_item_relationship(self) -> None:
        mapper = inspect(WishlistSighting)
        rel_names = {r.key for r in mapper.relationships}
        assert "wishlist_item" in rel_names

    def test_sighting_has_supplier_relationship(self) -> None:
        mapper = inspect(WishlistSighting)
        rel_names = {r.key for r in mapper.relationships}
        assert "supplier" in rel_names

    def test_sightings_cascade_includes_delete_orphan(self) -> None:
        mapper = inspect(WishlistItem)
        rel = mapper.relationships["sightings"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _wishlist_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def wishlist_session(_wishlist_engine):
    factory = async_sessionmaker(
        _wishlist_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


async def _create_prerequisites(session: AsyncSession) -> tuple:
    """Create MainCategory → SubCategory → Catalog → CatalogItem → Collection."""
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

    collection = Collection(name="My N64", collection_type="multi_category")
    session.add(collection)
    await session.commit()
    await session.refresh(collection)

    return collection, cat_item


class TestWishlistPersistence:
    """Integration-style tests for persisting wishlist items and sightings."""

    @pytest.mark.asyncio
    async def test_create_wishlist_item_persists(
        self, wishlist_session: AsyncSession,
    ) -> None:
        collection, cat_item = await _create_prerequisites(wishlist_session)

        wi = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
            desired_condition="good",
            max_price=50.00,
        )
        wishlist_session.add(wi)
        await wishlist_session.commit()
        await wishlist_session.refresh(wi)

        assert wi.id is not None
        assert len(wi.id) == 36
        uuid.UUID(wi.id)
        assert wi.collection_id == collection.id
        assert wi.catalog_item_id == cat_item.id
        assert wi.created_at is not None

    @pytest.mark.asyncio
    async def test_wishlist_item_defaults_applied(
        self, wishlist_session: AsyncSession,
    ) -> None:
        collection, cat_item = await _create_prerequisites(wishlist_session)

        wi = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
        )
        wishlist_session.add(wi)
        await wishlist_session.commit()
        await wishlist_session.refresh(wi)

        assert wi.must_be_complete is True
        assert wi.currency == "USD"
        assert wi.specific_variant_required is False
        assert wi.priority == 3
        assert wi.urgency == "medium"
        assert wi.is_active is True
        assert wi.is_acquired is False

    @pytest.mark.asyncio
    async def test_create_sighting_linked_to_wishlist_item(
        self, wishlist_session: AsyncSession,
    ) -> None:
        collection, cat_item = await _create_prerequisites(wishlist_session)

        wi = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
        )
        wishlist_session.add(wi)
        await wishlist_session.commit()
        await wishlist_session.refresh(wi)

        sighting = WishlistSighting(
            wishlist_item_id=wi.id,
            price=35.99,
            location_description="eBay listing",
            url="https://ebay.example.com/item/123",
        )
        wishlist_session.add(sighting)
        await wishlist_session.commit()
        await wishlist_session.refresh(sighting)

        assert sighting.id is not None
        assert sighting.wishlist_item_id == wi.id
        assert float(sighting.price) == 35.99

    @pytest.mark.asyncio
    async def test_sighting_defaults_applied(
        self, wishlist_session: AsyncSession,
    ) -> None:
        collection, cat_item = await _create_prerequisites(wishlist_session)

        wi = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
        )
        wishlist_session.add(wi)
        await wishlist_session.commit()
        await wishlist_session.refresh(wi)

        sighting = WishlistSighting(
            wishlist_item_id=wi.id,
            price=20.00,
        )
        wishlist_session.add(sighting)
        await wishlist_session.commit()
        await wishlist_session.refresh(sighting)

        assert sighting.is_available is True
        assert sighting.quantity_available == 1
        assert sighting.contacted is False
        assert sighting.currency == "USD"

    @pytest.mark.asyncio
    async def test_cascade_delete_removes_sightings(
        self, wishlist_session: AsyncSession,
    ) -> None:
        collection, cat_item = await _create_prerequisites(wishlist_session)

        wi = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
        )
        s1 = WishlistSighting(price=10.00)
        s2 = WishlistSighting(price=20.00)
        wi.sightings = [s1, s2]

        wishlist_session.add(wi)
        await wishlist_session.commit()

        await wishlist_session.delete(wi)
        await wishlist_session.commit()

        result = await wishlist_session.execute(select(WishlistSighting))
        remaining = result.scalars().all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_repr_methods(self) -> None:
        wi = WishlistItem(collection_id="fake-id")
        ws = WishlistSighting(wishlist_item_id="fake-id")
        assert "WishlistItem" in repr(wi)
        assert "WishlistSighting" in repr(ws)
