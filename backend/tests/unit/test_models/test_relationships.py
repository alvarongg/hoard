"""Unit tests for SQLAlchemy model relationships.

Validates: Requirements 2.10, 19.10

Relationships tested:
- SubCategory.field_schemas and SubCategory.standard_components (bidirectional, cascade)
- Supplier.collection_items, Supplier.sightings, Supplier.accessories (bidirectional)
- WishlistItem.acquired_collection_item (bidirectional)
- CatalogItem.price_history (bidirectional, cascade)
- CollectionItem.components, .transactions, .accessories, .supplier (bidirectional, cascade)
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.category_field_schema import CategoryFieldSchema
from api.models.collection import Collection, CollectionItem
from api.models.price_history import CatalogPriceHistory
from api.models.supplier import Supplier
from api.models.accessory import AccessoryStock, ItemAccessory, ItemComponent
from api.models.transaction import ItemTransaction
from api.models.wishlist import WishlistItem, WishlistSighting
from api.models.standard_component import StandardComponent


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        # Enable foreign key support for SQLite (required for CASCADE to work)
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def session(_engine):
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as s:
        # Ensure foreign keys are enabled for this session
        await s.execute(text("PRAGMA foreign_keys=ON"))
        yield s


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


async def _create_main_category(session: AsyncSession) -> MainCategory:
    """Helper to create a MainCategory."""
    uid = str(uuid.uuid4())[:8]
    main = MainCategory(name=f"Category {uid}", slug=f"cat-{uid}", sort_order=0)
    session.add(main)
    await session.commit()
    await session.refresh(main)
    return main


async def _create_sub_category(session: AsyncSession) -> SubCategory:
    """Helper to create a MainCategory + SubCategory for FK references."""
    main = await _create_main_category(session)
    uid = str(uuid.uuid4())[:8]
    sub = SubCategory(
        main_category_id=main.id,
        name=f"SubCat {uid}",
        slug=f"subcat-{uid}",
        sort_order=0,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


async def _create_catalog_item(session: AsyncSession) -> CatalogItem:
    """Helper to create a CatalogItem for FK references."""
    sub = await _create_sub_category(session)

    uid = str(uuid.uuid4())[:8]
    catalog = Catalog(sub_category_id=sub.id, name=f"Catalog {uid}")
    session.add(catalog)
    await session.commit()
    await session.refresh(catalog)

    uid2 = str(uuid.uuid4())[:8]
    item = CatalogItem(
        catalog_id=catalog.id,
        title=f"Item {uid2}",
        custom_fields={},
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def _create_collection_item(session: AsyncSession) -> CollectionItem:
    """Helper to create a CollectionItem for FK references."""
    cat_item = await _create_catalog_item(session)

    uid = str(uuid.uuid4())[:8]
    collection = Collection(name=f"Collection {uid}", collection_type="multi_category")
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


async def _create_supplier(session: AsyncSession) -> Supplier:
    """Helper to create a Supplier for FK references."""
    uid = str(uuid.uuid4())[:8]
    supplier = Supplier(name=f"Supplier {uid}")
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return supplier


async def _create_accessory(session: AsyncSession) -> AccessoryStock:
    """Helper to create an AccessoryStock for FK references."""
    uid = str(uuid.uuid4())[:8]
    acc = AccessoryStock(name=f"Accessory {uid}")
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc


# ---------------------------------------------------------------------------
# SubCategory.field_schemas relationship tests
# ---------------------------------------------------------------------------


class TestSubCategoryFieldSchemasRelationship:
    """Verify SubCategory.field_schemas bidirectional navigation and cascade."""

    @pytest.mark.asyncio
    async def test_sub_category_has_field_schemas_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify SubCategory has field_schemas relationship defined."""
        mapper = inspect(SubCategory)
        rel_names = {r.key for r in mapper.relationships}
        assert "field_schemas" in rel_names

    @pytest.mark.asyncio
    async def test_category_field_schema_has_sub_category_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CategoryFieldSchema has sub_category relationship defined."""
        mapper = inspect(CategoryFieldSchema)
        rel_names = {r.key for r in mapper.relationships}
        assert "sub_category" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_sub_category_to_field_schemas(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from SubCategory to field_schemas works."""
        sub = await _create_sub_category(session)

        schema1 = CategoryFieldSchema(
            sub_category_id=sub.id,
            field_name="platform",
            field_label="Platform",
            field_type="select",
        )
        schema2 = CategoryFieldSchema(
            sub_category_id=sub.id,
            field_name="region",
            field_label="Region",
            field_type="select",
        )
        session.add_all([schema1, schema2])
        await session.commit()

        # Refresh and navigate
        await session.refresh(sub, ["field_schemas"])
        assert len(sub.field_schemas) == 2
        field_names = {fs.field_name for fs in sub.field_schemas}
        assert field_names == {"platform", "region"}

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_field_schema_to_sub_category(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CategoryFieldSchema to sub_category works."""
        sub = await _create_sub_category(session)

        schema = CategoryFieldSchema(
            sub_category_id=sub.id,
            field_name="platform",
            field_label="Platform",
            field_type="select",
        )
        session.add(schema)
        await session.commit()
        await session.refresh(schema, ["sub_category"])

        assert schema.sub_category is not None
        assert schema.sub_category.id == sub.id
        assert schema.sub_category.name == sub.name

    @pytest.mark.asyncio
    async def test_cascade_delete_sub_category_deletes_field_schemas(
        self, session: AsyncSession
    ) -> None:
        """Verify that deleting SubCategory cascades to field_schemas."""
        sub = await _create_sub_category(session)

        schema = CategoryFieldSchema(
            sub_category_id=sub.id,
            field_name="platform",
            field_label="Platform",
            field_type="select",
        )
        session.add(schema)
        await session.commit()
        schema_id = schema.id

        # Verify cascade is configured
        mapper = inspect(SubCategory)
        rel = mapper.relationships["field_schemas"]
        assert rel.cascade.delete is True
        assert rel.cascade.delete_orphan is True
        assert rel.passive_deletes is True

        # Delete the sub_category
        await session.delete(sub)
        await session.commit()

        # Verify the schema was deleted
        result = await session.execute(
            select(CategoryFieldSchema).where(CategoryFieldSchema.id == schema_id)
        )
        assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# SubCategory.standard_components relationship tests
# ---------------------------------------------------------------------------


class TestSubCategoryStandardComponentsRelationship:
    """Verify SubCategory.standard_components bidirectional navigation and cascade."""

    @pytest.mark.asyncio
    async def test_sub_category_has_standard_components_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify SubCategory has standard_components relationship defined."""
        mapper = inspect(SubCategory)
        rel_names = {r.key for r in mapper.relationships}
        assert "standard_components" in rel_names

    @pytest.mark.asyncio
    async def test_standard_component_has_sub_category_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify StandardComponent has sub_category relationship defined."""
        mapper = inspect(StandardComponent)
        rel_names = {r.key for r in mapper.relationships}
        assert "sub_category" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_sub_category_to_standard_components(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from SubCategory to standard_components works."""
        sub = await _create_sub_category(session)

        comp1 = StandardComponent(
            sub_category_id=sub.id,
            component_name="Box",
            component_type="required",
        )
        comp2 = StandardComponent(
            sub_category_id=sub.id,
            component_name="Manual",
            component_type="required",
        )
        session.add_all([comp1, comp2])
        await session.commit()

        # Refresh and navigate
        await session.refresh(sub, ["standard_components"])
        assert len(sub.standard_components) == 2
        comp_names = {c.component_name for c in sub.standard_components}
        assert comp_names == {"Box", "Manual"}

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_standard_component_to_sub_category(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from StandardComponent to sub_category works."""
        sub = await _create_sub_category(session)

        comp = StandardComponent(
            sub_category_id=sub.id,
            component_name="Box",
            component_type="required",
        )
        session.add(comp)
        await session.commit()
        await session.refresh(comp, ["sub_category"])

        assert comp.sub_category is not None
        assert comp.sub_category.id == sub.id

    @pytest.mark.asyncio
    async def test_cascade_delete_sub_category_deletes_standard_components(
        self, session: AsyncSession
    ) -> None:
        """Verify that deleting SubCategory cascades to standard_components."""
        sub = await _create_sub_category(session)

        comp = StandardComponent(
            sub_category_id=sub.id,
            component_name="Box",
            component_type="required",
        )
        session.add(comp)
        await session.commit()
        comp_id = comp.id

        # Verify cascade is configured
        mapper = inspect(SubCategory)
        rel = mapper.relationships["standard_components"]
        assert rel.cascade.delete is True
        assert rel.cascade.delete_orphan is True
        assert rel.passive_deletes is True

        # Delete the sub_category
        await session.delete(sub)
        await session.commit()

        # Verify the component was deleted
        result = await session.execute(
            select(StandardComponent).where(StandardComponent.id == comp_id)
        )
        assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# Supplier relationships tests (collection_items, sightings, accessories)
# ---------------------------------------------------------------------------


class TestSupplierRelationships:
    """Verify Supplier exposes the three reference sets.

    Requirements: 2.10
    """

    @pytest.mark.asyncio
    async def test_supplier_has_collection_items_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify Supplier has collection_items relationship defined."""
        mapper = inspect(Supplier)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection_items" in rel_names

    @pytest.mark.asyncio
    async def test_supplier_has_sightings_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify Supplier has sightings relationship defined."""
        mapper = inspect(Supplier)
        rel_names = {r.key for r in mapper.relationships}
        assert "sightings" in rel_names

    @pytest.mark.asyncio
    async def test_supplier_has_accessories_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify Supplier has accessories relationship defined."""
        mapper = inspect(Supplier)
        rel_names = {r.key for r in mapper.relationships}
        assert "accessories" in rel_names

    @pytest.mark.asyncio
    async def test_supplier_exposes_three_reference_sets(
        self, session: AsyncSession
    ) -> None:
        """Verify Supplier exposes collection_items, sightings, and accessories."""
        supplier = await _create_supplier(session)

        # Create collection item referencing supplier
        ci = await _create_collection_item(session)
        ci.supplier_id = supplier.id
        await session.commit()
        await session.refresh(ci)

        # Create wishlist item with sighting referencing supplier
        cat_item = await _create_catalog_item(session)

        # Create a collection for the wishlist item
        uid = str(uuid.uuid4())[:8]
        collection = Collection(name=f"Collection {uid}", collection_type="multi_category")
        session.add(collection)
        await session.commit()
        await session.refresh(collection)

        wishlist = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
            priority=3,
            urgency="medium",
        )
        session.add(wishlist)
        await session.commit()
        await session.refresh(wishlist)

        sighting = WishlistSighting(
            wishlist_item_id=wishlist.id,
            price=Decimal("50.00"),
            supplier_id=supplier.id,
        )
        session.add(sighting)
        await session.commit()

        # Create accessory referencing supplier
        acc = AccessoryStock(name="Test Case", supplier_id=supplier.id)
        session.add(acc)
        await session.commit()

        # Refresh and verify all three reference sets
        await session.refresh(supplier, ["collection_items", "sightings", "accessories"])

        assert len(supplier.collection_items) == 1
        assert supplier.collection_items[0].id == ci.id

        assert len(supplier.sightings) == 1
        assert supplier.sightings[0].id == sighting.id

        assert len(supplier.accessories) == 1
        assert supplier.accessories[0].id == acc.id

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_collection_item_to_supplier(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CollectionItem to supplier works."""
        supplier = await _create_supplier(session)
        ci = await _create_collection_item(session)
        ci.supplier_id = supplier.id
        await session.commit()
        await session.refresh(ci, ["supplier"])

        assert ci.supplier is not None
        assert ci.supplier.id == supplier.id

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_sighting_to_supplier(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from WishlistSighting to supplier works."""
        supplier = await _create_supplier(session)

        # Create a fresh catalog item and collection for this test
        cat_item = await _create_catalog_item(session)

        # Create a collection for the wishlist item
        uid = str(uuid.uuid4())[:8]
        collection = Collection(name=f"Collection {uid}", collection_type="multi_category")
        session.add(collection)
        await session.commit()
        await session.refresh(collection)

        wishlist = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
            priority=3,
            urgency="medium",
        )
        session.add(wishlist)
        await session.commit()
        await session.refresh(wishlist)

        sighting = WishlistSighting(
            wishlist_item_id=wishlist.id,
            price=Decimal("50.00"),
            supplier_id=supplier.id,
        )
        session.add(sighting)
        await session.commit()
        await session.refresh(sighting, ["supplier"])

        assert sighting.supplier is not None
        assert sighting.supplier.id == supplier.id

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_accessory_to_supplier(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from AccessoryStock to supplier works."""
        supplier = await _create_supplier(session)
        acc = AccessoryStock(name="Test Case", supplier_id=supplier.id)
        session.add(acc)
        await session.commit()
        await session.refresh(acc, ["supplier"])

        assert acc.supplier is not None
        assert acc.supplier.id == supplier.id


# ---------------------------------------------------------------------------
# WishlistItem.acquired_collection_item relationship tests
# ---------------------------------------------------------------------------


class TestWishlistItemAcquiredCollectionItemRelationship:
    """Verify WishlistItem.acquired_collection_item bidirectional navigation."""

    @pytest.mark.asyncio
    async def test_wishlist_item_has_acquired_collection_item_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify WishlistItem has acquired_collection_item relationship defined."""
        mapper = inspect(WishlistItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "acquired_collection_item" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_wishlist_item_to_acquired_collection_item(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from WishlistItem to acquired_collection_item works."""
        ci = await _create_collection_item(session)
        cat_item = await session.execute(select(CatalogItem))
        cat_item = cat_item.scalars().first()
        collection = await session.execute(select(Collection))
        collection = collection.scalars().first()

        wishlist = WishlistItem(
            collection_id=collection.id,
            catalog_item_id=cat_item.id,
            priority=3,
            urgency="medium",
            is_acquired=True,
            acquired_collection_item_id=ci.id,
        )
        session.add(wishlist)
        await session.commit()
        await session.refresh(wishlist, ["acquired_collection_item"])

        assert wishlist.acquired_collection_item is not None
        assert wishlist.acquired_collection_item.id == ci.id


# ---------------------------------------------------------------------------
# CatalogItem.price_history relationship tests
# ---------------------------------------------------------------------------


class TestCatalogItemPriceHistoryRelationship:
    """Verify CatalogItem.price_history bidirectional navigation and cascade."""

    @pytest.mark.asyncio
    async def test_catalog_item_has_price_history_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CatalogItem has price_history relationship defined."""
        mapper = inspect(CatalogItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "price_history" in rel_names

    @pytest.mark.asyncio
    async def test_price_history_has_catalog_item_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CatalogPriceHistory has catalog_item relationship defined."""
        mapper = inspect(CatalogPriceHistory)
        rel_names = {r.key for r in mapper.relationships}
        assert "catalog_item" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_catalog_item_to_price_history(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CatalogItem to price_history works."""
        cat_item = await _create_catalog_item(session)

        price1 = CatalogPriceHistory(
            catalog_item_id=cat_item.id,
            condition="mint",
            is_complete=True,
            price=Decimal("50.00"),
            price_date=date(2024, 1, 1),
        )
        price2 = CatalogPriceHistory(
            catalog_item_id=cat_item.id,
            condition="good",
            is_complete=True,
            price=Decimal("35.00"),
            price_date=date(2024, 2, 1),
        )
        session.add_all([price1, price2])
        await session.commit()

        # Refresh and navigate
        await session.refresh(cat_item, ["price_history"])
        assert len(cat_item.price_history) == 2
        prices = {p.price for p in cat_item.price_history}
        assert prices == {Decimal("50.00"), Decimal("35.00")}

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_price_history_to_catalog_item(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CatalogPriceHistory to catalog_item works."""
        cat_item = await _create_catalog_item(session)

        price = CatalogPriceHistory(
            catalog_item_id=cat_item.id,
            condition="mint",
            is_complete=True,
            price=Decimal("50.00"),
            price_date=date(2024, 1, 1),
        )
        session.add(price)
        await session.commit()
        await session.refresh(price, ["catalog_item"])

        assert price.catalog_item is not None
        assert price.catalog_item.id == cat_item.id

    @pytest.mark.asyncio
    async def test_cascade_delete_catalog_item_deletes_price_history(
        self, session: AsyncSession
    ) -> None:
        """Verify that deleting CatalogItem cascades to price_history."""
        cat_item = await _create_catalog_item(session)

        price = CatalogPriceHistory(
            catalog_item_id=cat_item.id,
            condition="mint",
            is_complete=True,
            price=Decimal("50.00"),
            price_date=date(2024, 1, 1),
        )
        session.add(price)
        await session.commit()
        price_id = price.id

        # Verify cascade is configured
        mapper = inspect(CatalogItem)
        rel = mapper.relationships["price_history"]
        assert rel.cascade.delete is True
        assert rel.cascade.delete_orphan is True
        assert rel.passive_deletes is True

        # Delete the catalog_item
        await session.delete(cat_item)
        await session.commit()

        # Verify the price history was deleted
        result = await session.execute(
            select(CatalogPriceHistory).where(CatalogPriceHistory.id == price_id)
        )
        assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# CollectionItem relationships tests (components, transactions, accessories, supplier)
# ---------------------------------------------------------------------------


class TestCollectionItemComponentsRelationship:
    """Verify CollectionItem.components bidirectional navigation and cascade."""

    @pytest.mark.asyncio
    async def test_collection_item_has_components_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CollectionItem has components relationship defined."""
        mapper = inspect(CollectionItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "components" in rel_names

    @pytest.mark.asyncio
    async def test_item_component_has_collection_item_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify ItemComponent has collection_item relationship defined."""
        mapper = inspect(ItemComponent)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection_item" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_collection_item_to_components(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CollectionItem to components works."""
        ci = await _create_collection_item(session)

        comp1 = ItemComponent(
            collection_item_id=ci.id,
            component_name="Box",
            component_type="required",
            is_present=True,
        )
        comp2 = ItemComponent(
            collection_item_id=ci.id,
            component_name="Manual",
            component_type="required",
            is_present=False,
        )
        session.add_all([comp1, comp2])
        await session.commit()

        # Refresh and navigate
        await session.refresh(ci, ["components"])
        assert len(ci.components) == 2
        comp_names = {c.component_name for c in ci.components}
        assert comp_names == {"Box", "Manual"}

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_component_to_collection_item(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from ItemComponent to collection_item works."""
        ci = await _create_collection_item(session)

        comp = ItemComponent(
            collection_item_id=ci.id,
            component_name="Box",
            component_type="required",
            is_present=True,
        )
        session.add(comp)
        await session.commit()
        await session.refresh(comp, ["collection_item"])

        assert comp.collection_item is not None
        assert comp.collection_item.id == ci.id

    @pytest.mark.asyncio
    async def test_cascade_delete_collection_item_deletes_components(
        self, session: AsyncSession
    ) -> None:
        """Verify that deleting CollectionItem cascades to components."""
        ci = await _create_collection_item(session)

        comp = ItemComponent(
            collection_item_id=ci.id,
            component_name="Box",
            component_type="required",
            is_present=True,
        )
        session.add(comp)
        await session.commit()
        comp_id = comp.id

        # Verify cascade is configured
        mapper = inspect(CollectionItem)
        rel = mapper.relationships["components"]
        assert rel.cascade.delete is True
        assert rel.cascade.delete_orphan is True
        assert rel.passive_deletes is True

        # Delete the collection_item
        await session.delete(ci)
        await session.commit()

        # Verify the component was deleted
        result = await session.execute(
            select(ItemComponent).where(ItemComponent.id == comp_id)
        )
        assert result.scalar_one_or_none() is None


class TestCollectionItemTransactionsRelationship:
    """Verify CollectionItem.transactions bidirectional navigation and cascade."""

    @pytest.mark.asyncio
    async def test_collection_item_has_transactions_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CollectionItem has transactions relationship defined."""
        mapper = inspect(CollectionItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "transactions" in rel_names

    @pytest.mark.asyncio
    async def test_item_transaction_has_collection_item_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify ItemTransaction has collection_item relationship defined."""
        mapper = inspect(ItemTransaction)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection_item" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_collection_item_to_transactions(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CollectionItem to transactions works."""
        ci = await _create_collection_item(session)

        tx1 = ItemTransaction(
            collection_item_id=ci.id,
            transaction_type="purchase",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("50.00"),
        )
        tx2 = ItemTransaction(
            collection_item_id=ci.id,
            transaction_type="grading",
            transaction_date=date(2024, 2, 1),
            amount=Decimal("20.00"),
        )
        session.add_all([tx1, tx2])
        await session.commit()

        # Refresh and navigate
        await session.refresh(ci, ["transactions"])
        assert len(ci.transactions) == 2
        tx_types = {t.transaction_type for t in ci.transactions}
        assert tx_types == {"purchase", "grading"}

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_transaction_to_collection_item(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from ItemTransaction to collection_item works."""
        ci = await _create_collection_item(session)

        tx = ItemTransaction(
            collection_item_id=ci.id,
            transaction_type="purchase",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("50.00"),
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx, ["collection_item"])

        assert tx.collection_item is not None
        assert tx.collection_item.id == ci.id

    @pytest.mark.asyncio
    async def test_cascade_delete_collection_item_deletes_transactions(
        self, session: AsyncSession
    ) -> None:
        """Verify that deleting CollectionItem cascades to transactions."""
        ci = await _create_collection_item(session)

        tx = ItemTransaction(
            collection_item_id=ci.id,
            transaction_type="purchase",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("50.00"),
        )
        session.add(tx)
        await session.commit()
        tx_id = tx.id

        # Verify cascade is configured
        mapper = inspect(CollectionItem)
        rel = mapper.relationships["transactions"]
        assert rel.cascade.delete is True
        assert rel.cascade.delete_orphan is True
        assert rel.passive_deletes is True

        # Delete the collection_item
        await session.delete(ci)
        await session.commit()

        # Verify the transaction was deleted
        result = await session.execute(
            select(ItemTransaction).where(ItemTransaction.id == tx_id)
        )
        assert result.scalar_one_or_none() is None


class TestCollectionItemAccessoriesRelationship:
    """Verify CollectionItem.accessories bidirectional navigation and cascade."""

    @pytest.mark.asyncio
    async def test_collection_item_has_accessories_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CollectionItem has accessories relationship defined."""
        mapper = inspect(CollectionItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "accessories" in rel_names

    @pytest.mark.asyncio
    async def test_item_accessory_has_collection_item_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify ItemAccessory has collection_item relationship defined."""
        mapper = inspect(ItemAccessory)
        rel_names = {r.key for r in mapper.relationships}
        assert "collection_item" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_collection_item_to_accessories(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CollectionItem to accessories works."""
        ci = await _create_collection_item(session)
        acc = await _create_accessory(session)

        ia1 = ItemAccessory(
            collection_item_id=ci.id,
            accessory_id=acc.id,
            quantity_used=1,
        )
        session.add(ia1)
        await session.commit()

        # Refresh and navigate
        await session.refresh(ci, ["accessories"])
        assert len(ci.accessories) == 1
        assert ci.accessories[0].accessory_id == acc.id

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_item_accessory_to_collection_item(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from ItemAccessory to collection_item works."""
        ci = await _create_collection_item(session)
        acc = await _create_accessory(session)

        ia = ItemAccessory(
            collection_item_id=ci.id,
            accessory_id=acc.id,
            quantity_used=1,
        )
        session.add(ia)
        await session.commit()
        await session.refresh(ia, ["collection_item"])

        assert ia.collection_item is not None
        assert ia.collection_item.id == ci.id

    @pytest.mark.asyncio
    async def test_cascade_delete_collection_item_deletes_item_accessories(
        self, session: AsyncSession
    ) -> None:
        """Verify that deleting CollectionItem cascades to item_accessories."""
        ci = await _create_collection_item(session)
        acc = await _create_accessory(session)

        ia = ItemAccessory(
            collection_item_id=ci.id,
            accessory_id=acc.id,
            quantity_used=1,
        )
        session.add(ia)
        await session.commit()
        ia_id = ia.id

        # Verify cascade is configured
        mapper = inspect(CollectionItem)
        rel = mapper.relationships["accessories"]
        assert rel.cascade.delete is True
        assert rel.cascade.delete_orphan is True
        assert rel.passive_deletes is True

        # Delete the collection_item
        await session.delete(ci)
        await session.commit()

        # Verify the item_accessory was deleted
        result = await session.execute(
            select(ItemAccessory).where(ItemAccessory.id == ia_id)
        )
        assert result.scalar_one_or_none() is None


class TestCollectionItemSupplierRelationship:
    """Verify CollectionItem.supplier bidirectional navigation."""

    @pytest.mark.asyncio
    async def test_collection_item_has_supplier_relationship(
        self, session: AsyncSession
    ) -> None:
        """Verify CollectionItem has supplier relationship defined."""
        mapper = inspect(CollectionItem)
        rel_names = {r.key for r in mapper.relationships}
        assert "supplier" in rel_names

    @pytest.mark.asyncio
    async def test_bidirectional_navigation_collection_item_to_supplier(
        self, session: AsyncSession
    ) -> None:
        """Verify navigating from CollectionItem to supplier works."""
        supplier = await _create_supplier(session)
        ci = await _create_collection_item(session)
        ci.supplier_id = supplier.id
        await session.commit()
        await session.refresh(ci, ["supplier"])

        assert ci.supplier is not None
        assert ci.supplier.id == supplier.id

    @pytest.mark.asyncio
    async def test_supplier_can_have_multiple_collection_items(
        self, session: AsyncSession
    ) -> None:
        """Verify a supplier can reference multiple collection items."""
        supplier = await _create_supplier(session)

        ci1 = await _create_collection_item(session)
        ci1.supplier_id = supplier.id
        await session.commit()

        ci2 = await _create_collection_item(session)
        ci2.supplier_id = supplier.id
        await session.commit()

        await session.refresh(supplier, ["collection_items"])
        assert len(supplier.collection_items) == 2
