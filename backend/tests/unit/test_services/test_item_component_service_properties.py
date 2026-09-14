"""Property-based tests for ItemComponentService completeness.

These tests use Hypothesis to verify universal properties of the completeness
calculation across a wide range of inputs.

Validates: Requirements 5.5, 5.6, 5.8
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.standard_component import StandardComponent
from api.schemas.item_component import ItemComponentCreate
from api.services.item_component_service import ItemComponentService
from utils.computations import is_item_complete

# ---------------------------------------------------------------------------
# Strategies for property-based testing
# ---------------------------------------------------------------------------

# Strategy for component names
component_name_strategy = st.sampled_from(
    ["Box", "Manual", "Cartridge", "Disc", "Case", "Insert", "Map", "Manual 2"]
)

# Strategy for component type
component_type_strategy = st.sampled_from(["required", "optional", "accessory"])

# Strategy for boolean
boolean_strategy = st.booleans()


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


@pytest.fixture()
async def engine():
    """Create an in-memory SQLite engine for each test."""
    from api.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
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


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


async def _create_catalog_item_with_subcategory(
    db_session: AsyncSession,
) -> tuple[CatalogItem, SubCategory]:
    """Create a catalog item with its sub-category and return both."""
    # Use unique identifiers to avoid constraint violations
    unique_id = str(uuid4())[:8]
    
    main_category = MainCategory(
        id=str(uuid4()),
        name=f"Main Category {unique_id}",
        slug=f"main-{unique_id}",
    )
    db_session.add(main_category)
    await db_session.commit()
    await db_session.refresh(main_category)

    sub_category = SubCategory(
        id=str(uuid4()),
        main_category_id=main_category.id,
        name=f"Sub Category {unique_id}",
        slug=f"sub-{unique_id}",
    )
    db_session.add(sub_category)
    await db_session.commit()
    await db_session.refresh(sub_category)

    catalog = Catalog(
        id=str(uuid4()),
        sub_category_id=sub_category.id,
        name=f"Catalog {unique_id}",
    )
    db_session.add(catalog)
    await db_session.commit()
    await db_session.refresh(catalog)

    catalog_item = CatalogItem(
        id=str(uuid4()),
        catalog_id=catalog.id,
        title=f"Catalog Item {unique_id}",
    )
    db_session.add(catalog_item)
    await db_session.commit()
    await db_session.refresh(catalog_item)

    return catalog_item, sub_category


async def _create_collection_item(
    db_session: AsyncSession,
    catalog_item: CatalogItem,
) -> CollectionItem:
    """Create a collection item and return it."""
    unique_id = str(uuid4())[:8]
    
    collection = Collection(
        id=str(uuid4()),
        name=f"Collection {unique_id}",
        collection_type="single_category",
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    collection_item = CollectionItem(
        id=str(uuid4()),
        collection_id=collection.id,
        catalog_item_id=catalog_item.id,
        condition="good",
    )
    db_session.add(collection_item)
    await db_session.commit()
    await db_session.refresh(collection_item)

    return collection_item


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestCompletenessProperties:
    """Property-based tests for item completeness.

    Validates: Requirements 5.5, 5.6, 5.8
    """

    @given(
        required_components=st.sets(
            component_name_strategy,
            min_size=0,
            max_size=5,
        ),
        present_components=st.sets(
            component_name_strategy,
            min_size=0,
            max_size=5,
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,  # Disable deadline for async tests with DB operations
    )
    async def test_completeness_equals_presence_of_all_required(
        self,
        required_components: set[str],
        present_components: set[str],
        db_session: AsyncSession,
    ) -> None:
        """Property 10: The item is complete iff all required components are present.

        Validates: Requirements 5.5, 5.6, 5.8

        This test verifies that:
        - When all required components are present, is_complete = True
        - When any required component is missing, is_complete = False
        - When there are no required components, is_complete = True
        """
        catalog_item, sub_category = await _create_catalog_item_with_subcategory(
            db_session
        )
        collection_item = await _create_collection_item(db_session, catalog_item)

        # Create standard components for required ones
        for i, name in enumerate(required_components):
            standard = StandardComponent(
                id=str(uuid4()),
                sub_category_id=sub_category.id,
                component_name=name,
                component_type="required",
                sort_order=i,
            )
            db_session.add(standard)
        await db_session.commit()

        # Create item components for present ones
        service = ItemComponentService(db_session)
        for name in present_components:
            await service.upsert(
                collection_item.id,
                ItemComponentCreate(
                    component_name=name,
                    component_type="required",
                    is_present=True,
                ),
            )

        # If no components were added and no required, trigger recalculation
        if not present_components:
            await service._recalculate_completeness(collection_item.id)

        # Calculate expected completeness
        expected_complete = is_item_complete(required_components, present_components)

        # Verify the collection item's is_complete matches
        await db_session.refresh(collection_item)
        assert collection_item.is_complete == expected_complete, (
            f"Expected is_complete={expected_complete} "
            f"for required={required_components}, present={present_components}, "
            f"got {collection_item.is_complete}"
        )

    @given(
        required_names=st.sets(
            component_name_strategy,
            min_size=1,
            max_size=4,
        ),
        present_names=st.sets(
            component_name_strategy,
            min_size=0,
            max_size=4,
        ),
        extra_present=st.sets(
            component_name_strategy,
            min_size=0,
            max_size=3,
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,  # Disable deadline for async tests with DB operations
    )
    async def test_completeness_with_mixed_components(
        self,
        required_names: set[str],
        present_names: set[str],
        extra_present: set[str],
        db_session: AsyncSession,
    ) -> None:
        """Property: Optional and extra components don't affect completeness.

        Validates: Requirements 5.5, 5.6, 5.8

        Only required components determine completeness. Optional, accessory,
        and other component types do not affect the is_complete flag.
        """
        # Ensure no overlap between required and extra
        extra_present = extra_present - required_names - present_names

        catalog_item, sub_category = await _create_catalog_item_with_subcategory(
            db_session
        )
        collection_item = await _create_collection_item(db_session, catalog_item)

        # Create standard components for required ones
        for i, name in enumerate(required_names):
            standard = StandardComponent(
                id=str(uuid4()),
                sub_category_id=sub_category.id,
                component_name=name,
                component_type="required",
                sort_order=i,
            )
            db_session.add(standard)

        # Create standard components for optional ones (using extra_present names)
        for i, name in enumerate(extra_present):
            standard = StandardComponent(
                id=str(uuid4()),
                sub_category_id=sub_category.id,
                component_name=name,
                component_type="optional",
                sort_order=i + 10,
            )
            db_session.add(standard)
        await db_session.commit()

        service = ItemComponentService(db_session)

        # Add present required components
        for name in present_names:
            await service.upsert(
                collection_item.id,
                ItemComponentCreate(
                    component_name=name,
                    component_type="required",
                    is_present=True,
                ),
            )

        # Add present optional components
        for name in extra_present:
            await service.upsert(
                collection_item.id,
                ItemComponentCreate(
                    component_name=name,
                    component_type="optional",
                    is_present=True,
                ),
            )

        # Calculate expected completeness (only required matter)
        expected_complete = is_item_complete(required_names, present_names)

        await db_session.refresh(collection_item)
        assert collection_item.is_complete == expected_complete, (
            f"Expected is_complete={expected_complete} "
            f"for required={required_names}, present={present_names}, "
            f"extra={extra_present}, got {collection_item.is_complete}"
        )

    @given(
        component_names=st.lists(
            component_name_strategy,
            min_size=0,
            max_size=5,
            unique=True,
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,  # Disable deadline for async tests with DB operations
    )
    async def test_completeness_with_no_required_components(
        self,
        component_names: list[str],
        db_session: AsyncSession,
    ) -> None:
        """Property: Items with no required components are always complete.

        Validates: Requirements 5.5, 5.6, 5.8

        When the sub-category doesn't define any required components,
        the item should always be considered complete.
        """
        catalog_item, sub_category = await _create_catalog_item_with_subcategory(
            db_session
        )
        collection_item = await _create_collection_item(db_session, catalog_item)

        # Don't create any required standard components

        service = ItemComponentService(db_session)

        # Add some components (none are required since we didn't create standards)
        for name in component_names:
            await service.upsert(
                collection_item.id,
                ItemComponentCreate(
                    component_name=name,
                    component_type="optional",
                    is_present=True,
                ),
            )

        # If we added components, the upsert should have recalculated completeness
        # If we didn't add any components, manually trigger recalculation
        if not component_names:
            await service._recalculate_completeness(collection_item.id)

        # Should be complete since there are no required components
        await db_session.refresh(collection_item)
        assert collection_item.is_complete is True, (
            f"Item with no required components should be complete, "
            f"got {collection_item.is_complete}"
        )

    @given(
        required_components=st.sets(
            component_name_strategy,
            min_size=1,
            max_size=3,
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,  # Disable deadline for async tests with DB operations
    )
    async def test_deleting_component_updates_completeness(
        self,
        required_components: set[str],
        db_session: AsyncSession,
    ) -> None:
        """Property: Deleting a component recalculates completeness.

        Validates: Requirements 5.5, 5.8

        When a component is deleted, the completeness should be
        recalculated based on the remaining components.
        """
        catalog_item, sub_category = await _create_catalog_item_with_subcategory(
            db_session
        )
        collection_item = await _create_collection_item(db_session, catalog_item)

        # Create standard components
        for i, name in enumerate(required_components):
            standard = StandardComponent(
                id=str(uuid4()),
                sub_category_id=sub_category.id,
                component_name=name,
                component_type="required",
                sort_order=i,
            )
            db_session.add(standard)
        await db_session.commit()

        service = ItemComponentService(db_session)

        # Add all required components
        component_ids = []
        for name in required_components:
            component, _ = await service.upsert(
                collection_item.id,
                ItemComponentCreate(
                    component_name=name,
                    component_type="required",
                    is_present=True,
                ),
            )
            component_ids.append(component.id)

        # Should be complete now
        await db_session.refresh(collection_item)
        assert collection_item.is_complete is True

        # Delete each component one by one
        for component_id in component_ids:
            await service.delete(component_id)

        # Should be incomplete after deleting all required components
        await db_session.refresh(collection_item)
        assert collection_item.is_complete is False, (
            f"Item should be incomplete after deleting all {len(required_components)} "
            f"required components"
        )
