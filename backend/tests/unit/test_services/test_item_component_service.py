"""Unit tests for ItemComponentService."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.accessory import ItemComponent
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.standard_component import StandardComponent
from api.schemas.item_component import ItemComponentCreate, ItemComponentUpdate
from api.services.item_component_service import ItemComponentService
from core.exceptions import NotFoundError


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


@pytest.fixture()
async def engine():
    """Create an in-memory SQLite engine for each test."""
    from api.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        # Enable foreign key support for SQLite
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async database session."""
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def item_component_service(db_session: AsyncSession) -> ItemComponentService:
    """Return an ItemComponentService instance."""
    return ItemComponentService(db_session)


@pytest.fixture
async def sample_collection(db_session: AsyncSession) -> Collection:
    """Create and return a sample collection."""
    collection = Collection(
        id=str(uuid4()),
        name="Test Collection",
        collection_type="single_category",
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection


@pytest.fixture
async def sample_catalog_item_with_subcategory(
    db_session: AsyncSession,
) -> tuple[CatalogItem, SubCategory]:
    """Create and return a sample catalog item with sub-category."""
    # Create main category
    main_category = MainCategory(
        id=str(uuid4()),
        name="Test Main Category",
        slug="test-main-category",
    )
    db_session.add(main_category)
    await db_session.commit()
    await db_session.refresh(main_category)

    # Create sub category
    sub_category = SubCategory(
        id=str(uuid4()),
        main_category_id=main_category.id,
        name="Test Sub Category",
        slug="test-sub-category",
    )
    db_session.add(sub_category)
    await db_session.commit()
    await db_session.refresh(sub_category)

    # Create catalog
    catalog = Catalog(
        id=str(uuid4()),
        sub_category_id=sub_category.id,
        name="Test Catalog",
    )
    db_session.add(catalog)
    await db_session.commit()
    await db_session.refresh(catalog)

    # Create catalog item
    item = CatalogItem(
        id=str(uuid4()),
        catalog_id=catalog.id,
        title="Test Catalog Item",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item, sub_category


@pytest.fixture
async def sample_collection_item(
    db_session: AsyncSession,
    sample_collection: Collection,
    sample_catalog_item_with_subcategory: tuple[CatalogItem, SubCategory],
) -> CollectionItem:
    """Create and return a sample collection item."""
    catalog_item, _sub_category = sample_catalog_item_with_subcategory
    item = CollectionItem(
        id=str(uuid4()),
        collection_id=sample_collection.id,
        catalog_item_id=catalog_item.id,
        condition="good",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


# ------------------------------------------------------------------
# Template tests
# ------------------------------------------------------------------


class TestItemComponentServiceTemplate:
    """Tests for ItemComponentService.get_template."""

    async def test_template_returns_standard_components(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        sample_catalog_item_with_subcategory: tuple[CatalogItem, SubCategory],
        db_session: AsyncSession,
    ) -> None:
        """Template returns standard components for sub-category."""
        _catalog_item, sub_category = sample_catalog_item_with_subcategory

        # Create standard components
        sc1 = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Box",
            component_type="required",
            sort_order=1,
        )
        sc2 = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Manual",
            component_type="required",
            sort_order=2,
        )
        db_session.add_all([sc1, sc2])
        await db_session.commit()

        result = await item_component_service.get_template(sample_collection_item.id)

        assert len(result) == 2
        assert result[0].component_name == "Box"
        assert result[0].is_present is False
        assert result[1].component_name == "Manual"
        assert result[1].is_present is False

    async def test_template_without_standard_components_returns_empty(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
    ) -> None:
        """Template for sub-category without standard components returns empty list."""
        result = await item_component_service.get_template(sample_collection_item.id)

        assert result == []

    async def test_template_nonexistent_collection_item_raises_error(
        self,
        item_component_service: ItemComponentService,
    ) -> None:
        """Template for nonexistent collection item raises NotFoundError."""
        with pytest.raises(NotFoundError, match="not found"):
            await item_component_service.get_template("00000000-0000-0000-0000-000000000000")


# ------------------------------------------------------------------
# List tests
# ------------------------------------------------------------------


class TestItemComponentServiceList:
    """Tests for ItemComponentService.list."""

    async def test_list_returns_components(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        db_session: AsyncSession,
    ) -> None:
        """Listing returns components for collection item."""
        # Create components
        comp1 = ItemComponent(
            id=str(uuid4()),
            collection_item_id=sample_collection_item.id,
            component_name="Box",
            is_present=True,
        )
        comp2 = ItemComponent(
            id=str(uuid4()),
            collection_item_id=sample_collection_item.id,
            component_name="Manual",
            is_present=False,
        )
        db_session.add_all([comp1, comp2])
        await db_session.commit()

        result = await item_component_service.list(sample_collection_item.id)

        assert len(result) == 2
        assert result[0].component_name == "Box"
        assert result[1].component_name == "Manual"

    async def test_list_nonexistent_collection_item_raises_error(
        self,
        item_component_service: ItemComponentService,
    ) -> None:
        """Listing for nonexistent collection item raises NotFoundError."""
        with pytest.raises(NotFoundError, match="not found"):
            await item_component_service.list("00000000-0000-0000-0000-000000000000")


# ------------------------------------------------------------------
# Upsert tests
# ------------------------------------------------------------------


class TestItemComponentServiceUpsert:
    """Tests for ItemComponentService.upsert."""

    async def test_upsert_creates_new_component(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
    ) -> None:
        """Upsert creates a new component."""
        data = ItemComponentCreate(
            component_name="Box",
            component_type="required",
            is_present=True,
        )

        component, completeness = await item_component_service.upsert(
            sample_collection_item.id, data
        )

        assert component.id is not None
        assert component.component_name == "Box"
        assert component.is_present is True
        # Item with no required components is complete
        assert completeness.is_complete is True

    async def test_upsert_updates_existing_component(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        sample_catalog_item_with_subcategory: tuple[CatalogItem, SubCategory],
        db_session: AsyncSession,
    ) -> None:
        """Upsert updates existing component with same standard_component_id."""
        _catalog_item, sub_category = sample_catalog_item_with_subcategory

        # Create standard component
        sc = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Box",
            component_type="required",
        )
        db_session.add(sc)
        await db_session.commit()

        # First upsert
        data1 = ItemComponentCreate(
            standard_component_id=sc.id,
            component_name="Box",
            is_present=False,
        )
        component1, _ = await item_component_service.upsert(
            sample_collection_item.id, data1
        )
        assert component1.is_present is False

        # Second upsert with same standard_component_id
        data2 = ItemComponentCreate(
            standard_component_id=sc.id,
            component_name="Box",
            is_present=True,
        )
        component2, _ = await item_component_service.upsert(
            sample_collection_item.id, data2
        )
        assert component2.id == component1.id  # Same component, updated
        assert component2.is_present is True

    async def test_upsert_adhoc_component_without_standard_id(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
    ) -> None:
        """Upssert creates ad-hoc component with component_name but no standard_id."""
        data = ItemComponentCreate(
            component_name="Custom Item",
            component_type="optional",
            is_present=True,
        )

        component, completeness = await item_component_service.upsert(
            sample_collection_item.id, data
        )

        assert component.standard_component_id is None
        assert component.component_name == "Custom Item"

    async def test_upsert_nonexistent_collection_item_raises_error(
        self,
        item_component_service: ItemComponentService,
    ) -> None:
        """Upsert for nonexistent collection item raises NotFoundError."""
        data = ItemComponentCreate(component_name="Box")

        with pytest.raises(NotFoundError, match="not found"):
            await item_component_service.upsert(
                "00000000-0000-0000-0000-000000000000", data
            )


# ------------------------------------------------------------------
# Update tests
# ------------------------------------------------------------------


class TestItemComponentServiceUpdate:
    """Tests for ItemComponentService.update."""

    async def test_update_changes_fields(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        db_session: AsyncSession,
    ) -> None:
        """Updating changes specified fields."""
        # Create component
        comp = ItemComponent(
            id=str(uuid4()),
            collection_item_id=sample_collection_item.id,
            component_name="Box",
            is_present=False,
        )
        db_session.add(comp)
        await db_session.commit()

        data = ItemComponentUpdate(is_present=True, condition="good")

        updated, completeness = await item_component_service.update(comp.id, data)

        assert updated.is_present is True
        assert updated.condition == "good"

    async def test_update_nonexistent_raises_error(
        self,
        item_component_service: ItemComponentService,
    ) -> None:
        """Updating nonexistent component raises NotFoundError."""
        data = ItemComponentUpdate(is_present=True)

        with pytest.raises(NotFoundError, match="not found"):
            await item_component_service.update(
                "00000000-0000-0000-0000-000000000000", data
            )


# ------------------------------------------------------------------
# Delete tests
# ------------------------------------------------------------------


class TestItemComponentServiceDelete:
    """Tests for ItemComponentService.delete."""

    async def test_delete_removes_component(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        db_session: AsyncSession,
    ) -> None:
        """Deleting removes the component."""
        # Create component
        comp = ItemComponent(
            id=str(uuid4()),
            collection_item_id=sample_collection_item.id,
            component_name="Box",
        )
        db_session.add(comp)
        await db_session.commit()

        completeness = await item_component_service.delete(comp.id)

        # Verify deleted
        result = await db_session.get(ItemComponent, comp.id)
        assert result is None

        # Returns completeness
        assert completeness.is_complete is True

    async def test_delete_nonexistent_raises_error(
        self,
        item_component_service: ItemComponentService,
    ) -> None:
        """Deleting nonexistent component raises NotFoundError."""
        with pytest.raises(NotFoundError, match="not found"):
            await item_component_service.delete("00000000-0000-0000-0000-000000000000")


# ------------------------------------------------------------------
# Completeness tests
# ------------------------------------------------------------------


class TestItemComponentServiceCompleteness:
    """Tests for completeness calculation."""

    async def test_item_with_all_required_is_complete(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        sample_catalog_item_with_subcategory: tuple[CatalogItem, SubCategory],
        db_session: AsyncSession,
    ) -> None:
        """Item with all required components is marked complete."""
        _catalog_item, sub_category = sample_catalog_item_with_subcategory

        # Create required standard components
        sc1 = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Box",
            component_type="required",
        )
        sc2 = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Manual",
            component_type="required",
        )
        db_session.add_all([sc1, sc2])
        await db_session.commit()

        # Add both required components as present
        await item_component_service.upsert(
            sample_collection_item.id,
            ItemComponentCreate(
                standard_component_id=sc1.id,
                component_name="Box",
                is_present=True,
            ),
        )
        _, completeness = await item_component_service.upsert(
            sample_collection_item.id,
            ItemComponentCreate(
                standard_component_id=sc2.id,
                component_name="Manual",
                is_present=True,
            ),
        )

        assert completeness.is_complete is True
        assert completeness.required_count == 2
        assert completeness.present_count == 2
        assert completeness.missing_names == []

        # Verify collection item is updated
        await db_session.refresh(sample_collection_item)
        assert sample_collection_item.is_complete is True

    async def test_item_with_missing_required_is_incomplete(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        sample_catalog_item_with_subcategory: tuple[CatalogItem, SubCategory],
        db_session: AsyncSession,
    ) -> None:
        """Item with missing required components is marked incomplete."""
        _catalog_item, sub_category = sample_catalog_item_with_subcategory

        # Create required standard components
        sc1 = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Box",
            component_type="required",
        )
        sc2 = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Manual",
            component_type="required",
        )
        db_session.add_all([sc1, sc2])
        await db_session.commit()

        # Add only one required component
        _, completeness = await item_component_service.upsert(
            sample_collection_item.id,
            ItemComponentCreate(
                standard_component_id=sc1.id,
                component_name="Box",
                is_present=True,
            ),
        )

        assert completeness.is_complete is False
        assert completeness.required_count == 2
        assert completeness.present_count == 1
        assert "Manual" in completeness.missing_names

        # Verify collection item is updated
        await db_session.refresh(sample_collection_item)
        assert sample_collection_item.is_complete is False

    async def test_item_without_required_is_complete(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
    ) -> None:
        """Item whose sub-category defines no required components is complete."""
        _, completeness = await item_component_service.upsert(
            sample_collection_item.id,
            ItemComponentCreate(component_name="Custom Item", is_present=True),
        )

        assert completeness.is_complete is True
        assert completeness.required_count == 0
        assert completeness.present_count == 0

    async def test_delete_recalculates_completeness(
        self,
        item_component_service: ItemComponentService,
        sample_collection_item: CollectionItem,
        sample_catalog_item_with_subcategory: tuple[CatalogItem, SubCategory],
        db_session: AsyncSession,
    ) -> None:
        """Deleting a component recalculates completeness."""
        _catalog_item, sub_category = sample_catalog_item_with_subcategory

        # Create required standard component
        sc = StandardComponent(
            id=str(uuid4()),
            sub_category_id=sub_category.id,
            component_name="Box",
            component_type="required",
        )
        db_session.add(sc)
        await db_session.commit()

        # Add required component
        component, _ = await item_component_service.upsert(
            sample_collection_item.id,
            ItemComponentCreate(
                standard_component_id=sc.id,
                component_name="Box",
                is_present=True,
            ),
        )

        # Verify complete
        await db_session.refresh(sample_collection_item)
        assert sample_collection_item.is_complete is True

        # Delete the component
        completeness = await item_component_service.delete(component.id)

        assert completeness.is_complete is False
        assert "Box" in completeness.missing_names

        # Verify collection item is updated
        await db_session.refresh(sample_collection_item)
        assert sample_collection_item.is_complete is False
