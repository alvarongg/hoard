"""Property-based tests for WishlistService.

These tests use Hypothesis to verify universal properties of the wishlist service
across a wide range of inputs.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.catalog import CatalogItem
from api.models.collection import Collection, CollectionItem
from api.models.wishlist import WishlistItem, WishlistSighting
from api.schemas.wishlist import (
    SightingCreate,
    WishlistAcquire,
    WishlistItemCreate,
)
from api.services.wishlist_service import WishlistService
from core.exceptions import DuplicateError

# ---------------------------------------------------------------------------
# Strategies for property-based testing
# ---------------------------------------------------------------------------

# Strategy for non-negative decimals (0.00 to 9999.99, with 2 decimal places)
# Limited range to avoid SQLite floating point precision issues
non_negative_decimal = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("9999.99"),
    places=2,
)

# Strategy for positive integers (1-5 for priority)
priority_strategy = st.integers(min_value=1, max_value=5)

# Strategy for urgency values
urgency_strategy = st.sampled_from(["low", "medium", "high", "critical"])

# Strategy for decision values
decision_strategy = st.sampled_from(["buy", "pass", "wait", "negotiate"])

# Strategy for non-empty strings
non_empty_string = st.text(min_size=1, max_size=100)

# Strategy for booleans
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


@pytest.fixture
def wishlist_service(db_session: AsyncSession) -> WishlistService:
    """Return a WishlistService instance."""
    return WishlistService(db_session)


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
async def sample_catalog_item(db_session: AsyncSession) -> CatalogItem:
    """Create and return a sample catalog item."""
    from api.models.catalog import Catalog
    from api.models.category import MainCategory, SubCategory

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

    item = CatalogItem(
        id=str(uuid4()),
        catalog_id=catalog.id,
        title="Test Catalog Item",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def sample_wishlist_item(
    db_session: AsyncSession,
    sample_collection: Collection,
    sample_catalog_item: CatalogItem,
) -> WishlistItem:
    """Create and return a sample wishlist item."""
    item = WishlistItem(
        id=str(uuid4()),
        collection_id=sample_collection.id,
        catalog_item_id=sample_catalog_item.id,
        priority=3,
        urgency="medium",
        max_price=Decimal("100.00"),
        currency="USD",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


class TestAcquisitionTransitionProperties:
    """Property-based tests for the acquisition transition.

    Validates: Requirements 3.7, 3.8, 3.9
    """

    @given(
        attempts=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_acquisition_is_one_way_transition(
        self,
        attempts: int,
        db_session: AsyncSession,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Property 11: Marking as acquired is a one-way transition.

        Validates: Requirements 3.7, 3.8, 3.9

        Once a wishlist item is marked as acquired:
        - is_acquired is True
        - acquired_date is set
        - acquired_collection_item_id is set
        - Subsequent acquisition attempts raise DuplicateError
        - The original acquired_collection_item_id is preserved
        """
        wishlist_service = WishlistService(db_session)

        # Create a wishlist item
        wishlist_item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
            urgency="medium",
        )
        db_session.add(wishlist_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)

        # Create collection items for acquisition attempts
        collection_items = []
        for i in range(attempts):
            collection_item = CollectionItem(
                id=str(uuid4()),
                collection_id=sample_collection.id,
                catalog_item_id=sample_catalog_item.id,
                condition="good",
            )
            db_session.add(collection_item)
            collection_items.append(collection_item)
        await db_session.commit()

        # First acquisition should succeed
        first_collection_item_id = collection_items[0].id
        result = await wishlist_service.mark_acquired(
            wishlist_item.id,
            WishlistAcquire(acquired_collection_item_id=first_collection_item_id),
        )

        assert result.is_acquired is True
        assert result.acquired_date is not None
        assert result.acquired_collection_item_id == first_collection_item_id

        # Subsequent acquisition attempts should fail
        for i in range(1, attempts):
            with pytest.raises(DuplicateError, match="already acquired"):
                await wishlist_service.mark_acquired(
                    wishlist_item.id,
                    WishlistAcquire(acquired_collection_item_id=collection_items[i].id),
                )

        # Verify the original acquired_collection_item_id is preserved
        await db_session.refresh(wishlist_item)
        assert wishlist_item.acquired_collection_item_id == first_collection_item_id

    @given(
        is_acquired_initial=boolean_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_acquisition_state_consistency(
        self,
        is_acquired_initial: bool,
        db_session: AsyncSession,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Property: Acquisition state is consistent after operations.

        Validates: Requirements 3.7, 3.8, 3.9

        If an item starts as acquired, any acquisition attempt should fail.
        If an item starts as not acquired, the first acquisition should succeed.
        """
        wishlist_service = WishlistService(db_session)

        # Create a wishlist item with optional initial acquired state
        wishlist_item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
            urgency="medium",
            is_acquired=is_acquired_initial,
        )
        db_session.add(wishlist_item)

        # Create a collection item for acquisition
        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)
        await db_session.refresh(collection_item)

        if is_acquired_initial:
            # Acquisition should fail
            with pytest.raises(DuplicateError, match="already acquired"):
                await wishlist_service.mark_acquired(
                    wishlist_item.id,
                    WishlistAcquire(acquired_collection_item_id=collection_item.id),
                )
        else:
            # Acquisition should succeed
            result = await wishlist_service.mark_acquired(
                wishlist_item.id,
                WishlistAcquire(acquired_collection_item_id=collection_item.id),
            )
            assert result.is_acquired is True


class TestPriceAggregatesProperties:
    """Property-based tests for price aggregates.

    Validates: Requirements 4.7, 4.8, 4.9
    """

    @given(
        prices=st.lists(
            non_negative_decimal,
            min_size=0,
            max_size=20,
        ),
        available_flags=st.lists(
            boolean_strategy,
            min_size=0,
            max_size=20,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_aggregates_are_consistent_with_sightings(
        self,
        prices: list[Decimal],
        available_flags: list[bool],
        db_session: AsyncSession,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Property 12: Price aggregates are consistent with sightings.

        Validates: Requirements 4.7, 4.8, 4.9

        The aggregates should match what we get from manual calculation:
        - avg_price is the mean of all sighting prices
        - min_price is the minimum price
        - max_price is the maximum price
        - total_sightings is the count
        - available_sightings is the count where is_available is True
        """
        # Ensure lists have same length by using minimum length
        list_length = min(len(prices), len(available_flags))
        if list_length == 0:
            # Handle empty case
            prices = []
            available_flags = []
        else:
            prices = prices[:list_length]
            available_flags = available_flags[:list_length]

        wishlist_service = WishlistService(db_session)

        # Create a wishlist item
        wishlist_item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
            urgency="medium",
        )
        db_session.add(wishlist_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)

        # Create sightings
        for price, is_available in zip(prices, available_flags, strict=False):
            sighting = WishlistSighting(
                id=str(uuid4()),
                wishlist_item_id=wishlist_item.id,
                price=price,
                currency="USD",
                is_available=is_available,
            )
            db_session.add(sighting)
        await db_session.commit()

        # Get aggregates
        result = await wishlist_service.get_with_price_aggregates(wishlist_item.id)
        aggregates = result.price_aggregates

        # Verify consistency
        assert aggregates.total_sightings == len(prices)
        assert aggregates.available_sightings == sum(available_flags)

        if len(prices) == 0:
            # Empty case
            assert aggregates.avg_price is None
            assert aggregates.min_price is None
            assert aggregates.max_price is None
        else:
            # Non-empty case
            expected_avg = sum(prices) / len(prices)
            # Use quantize for comparison to handle precision differences from database
            from decimal import ROUND_HALF_UP

            if aggregates.avg_price is not None:
                # Compare with 2 decimal places of precision
                actual_avg = aggregates.avg_price.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                expected_quantized = expected_avg.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                # Allow a small tolerance for SQLite floating point differences
                diff = abs(actual_avg - expected_quantized)
                assert diff <= Decimal("0.02"), (
                    f"avg_price mismatch: {actual_avg} != {expected_quantized} (diff={diff})"
                )
            # For min and max, also use quantized comparison
            min_quantized = aggregates.min_price.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            max_quantized = aggregates.max_price.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            expected_min = min(prices).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            expected_max = max(prices).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            assert min_quantized == expected_min, (
                f"min_price mismatch: {min_quantized} != {expected_min}"
            )
            assert max_quantized == expected_max, (
                f"max_price mismatch: {max_quantized} != {expected_max}"
            )

    @given(
        prices=st.lists(
            non_negative_decimal,
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_aggregates_monotonicity(
        self,
        prices: list[Decimal],
        db_session: AsyncSession,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Property: min_price <= avg_price <= max_price.

        Validates: Requirements 4.7, 4.8, 4.9

        For any non-empty set of prices:
        - min_price is the smallest price
        - max_price is the largest price
        - avg_price falls between min and max (inclusive)
        """
        wishlist_service = WishlistService(db_session)

        # Create a wishlist item
        wishlist_item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
            urgency="medium",
        )
        db_session.add(wishlist_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)

        # Create sightings
        for price in prices:
            sighting = WishlistSighting(
                id=str(uuid4()),
                wishlist_item_id=wishlist_item.id,
                price=price,
                currency="USD",
            )
            db_session.add(sighting)
        await db_session.commit()

        # Get aggregates
        result = await wishlist_service.get_with_price_aggregates(wishlist_item.id)
        aggregates = result.price_aggregates

        # Verify monotonicity
        assert aggregates.min_price is not None
        assert aggregates.max_price is not None
        assert aggregates.avg_price is not None

        # Use quantize for comparison to handle precision differences from database
        from decimal import ROUND_HALF_UP

        min_quantized = aggregates.min_price.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        max_quantized = aggregates.max_price.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        avg_quantized = aggregates.avg_price.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        assert min_quantized <= avg_quantized, (
            f"min_price ({min_quantized}) > avg_price ({avg_quantized})"
        )
        assert avg_quantized <= max_quantized, (
            f"avg_price ({avg_quantized}) > max_price ({max_quantized})"
        )

    @given(
        price=non_negative_decimal,
        is_available=boolean_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_single_sighting_aggregates(
        self,
        price: Decimal,
        is_available: bool,
        db_session: AsyncSession,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Property: Single sighting has min=max=avg=price.

        Validates: Requirements 4.7, 4.8, 4.9
        """
        wishlist_service = WishlistService(db_session)

        # Create a wishlist item
        wishlist_item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
            urgency="medium",
        )
        db_session.add(wishlist_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)

        # Create single sighting
        sighting = WishlistSighting(
            id=str(uuid4()),
            wishlist_item_id=wishlist_item.id,
            price=price,
            currency="USD",
            is_available=is_available,
        )
        db_session.add(sighting)
        await db_session.commit()

        # Get aggregates
        result = await wishlist_service.get_with_price_aggregates(wishlist_item.id)
        aggregates = result.price_aggregates

        # Single sighting: min=max=avg
        assert aggregates.total_sightings == 1
        assert aggregates.available_sightings == (1 if is_available else 0)
        assert aggregates.avg_price == price
        assert aggregates.min_price == price
        assert aggregates.max_price == price

    @given(
        sighting_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_aggregates_count_matches_created_sightings(
        self,
        sighting_count: int,
        db_session: AsyncSession,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Property: total_sightings equals the number of created sightings.

        Validates: Requirements 4.7, 4.8, 4.9
        """
        wishlist_service = WishlistService(db_session)

        # Create a wishlist item
        wishlist_item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
            urgency="medium",
        )
        db_session.add(wishlist_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)

        # Create sightings
        for i in range(sighting_count):
            sighting = WishlistSighting(
                id=str(uuid4()),
                wishlist_item_id=wishlist_item.id,
                price=Decimal("10.00") + Decimal(str(i)),
                currency="USD",
            )
            db_session.add(sighting)
        await db_session.commit()

        # Get aggregates
        result = await wishlist_service.get_with_price_aggregates(wishlist_item.id)
        aggregates = result.price_aggregates

        assert aggregates.total_sightings == sighting_count

        if sighting_count == 0:
            assert aggregates.avg_price is None
            assert aggregates.min_price is None
            assert aggregates.max_price is None
