"""Unit tests for WishlistService."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
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
    PriceAggregates,
    SightingCreate,
    SightingUpdate,
    WishlistAcquire,
    WishlistItemCreate,
    WishlistItemUpdate,
)
from api.services.wishlist_service import WishlistService
from core.exceptions import DuplicateError, NotFoundError, ValidationError


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


# ------------------------------------------------------------------
# WishlistItem tests
# ------------------------------------------------------------------


class TestWishlistServiceCreate:
    """Tests for WishlistService.create."""

    async def test_create_with_valid_data_returns_item(
        self,
        wishlist_service: WishlistService,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Creating with valid data returns a wishlist item."""
        data = WishlistItemCreate(
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=2,
            urgency="high",
            max_price=Decimal("50.00"),
            currency="EUR",
        )

        result = await wishlist_service.create(data)

        assert result.id is not None
        assert result.collection_id == sample_collection.id
        assert result.catalog_item_id == sample_catalog_item.id
        assert result.priority == 2
        assert result.urgency == "high"
        assert result.max_price == Decimal("50.00")
        assert result.currency == "EUR"

    async def test_create_with_invalid_urgency_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Creating with an invalid urgency raises ValidationError at schema level."""
        import pydantic

        with pytest.raises(pydantic.ValidationError, match="urgency must be one of"):
            WishlistItemCreate(
                collection_id=sample_collection.id,
                catalog_item_id=sample_catalog_item.id,
                urgency="invalid_urgency",
            )

    async def test_create_with_nonexistent_collection_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_catalog_item: CatalogItem,
    ) -> None:
        """Creating with a nonexistent collection raises NotFoundError."""
        data = WishlistItemCreate(
            collection_id="00000000-0000-0000-0000-000000000000",
            catalog_item_id=sample_catalog_item.id,
        )

        with pytest.raises(NotFoundError, match="Collection .* not found"):
            await wishlist_service.create(data)

    async def test_create_with_nonexistent_catalog_item_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_collection: Collection,
    ) -> None:
        """Creating with a nonexistent catalog item raises NotFoundError."""
        data = WishlistItemCreate(
            collection_id=sample_collection.id,
            catalog_item_id="00000000-0000-0000-0000-000000000000",
        )

        with pytest.raises(NotFoundError, match="Catalog item .* not found"):
            await wishlist_service.create(data)


class TestWishlistServiceList:
    """Tests for WishlistService.list."""

    async def test_list_returns_items(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Listing returns wishlist items."""
        result = await wishlist_service.list()

        assert len(result) == 1
        assert result[0].id == sample_wishlist_item.id

    async def test_list_filters_by_collection(
        self,
        wishlist_service: WishlistService,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """Listing filters by collection_id."""
        # Create a wishlist item for sample_collection
        item = WishlistItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=3,
        )
        db_session.add(item)
        await db_session.commit()

        result = await wishlist_service.list(collection_id=sample_collection.id)

        assert len(result) == 1
        assert result[0].collection_id == sample_collection.id

    async def test_list_filters_by_priority(
        self,
        wishlist_service: WishlistService,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """Listing filters by priority."""
        # Create item with different priority
        high_priority_item = WishlistItem(
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            priority=1,
        )
        db_session.add(high_priority_item)
        await db_session.commit()

        result = await wishlist_service.list(priority=1)

        assert len(result) == 1
        assert result[0].priority == 1

    async def test_list_excludes_acquired_by_default(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
        db_session: AsyncSession,
    ) -> None:
        """Listing excludes acquired items by default."""
        # Mark item as acquired
        sample_wishlist_item.is_acquired = True
        await db_session.commit()

        result = await wishlist_service.list()

        assert len(result) == 0

    async def test_list_includes_acquired_when_requested(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
        db_session: AsyncSession,
    ) -> None:
        """Listing includes acquired items when flag is set."""
        # Mark item as acquired
        sample_wishlist_item.is_acquired = True
        await db_session.commit()

        result = await wishlist_service.list(include_acquired=True)

        assert len(result) == 1

    async def test_list_empty_returns_empty_list(
        self, wishlist_service: WishlistService
    ) -> None:
        """Listing with no items returns empty list."""
        result = await wishlist_service.list()

        assert result == []


class TestWishlistServiceGet:
    """Tests for WishlistService.get."""

    async def test_get_returns_item(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Getting an existing item returns it."""
        result = await wishlist_service.get(sample_wishlist_item.id)

        assert result.id == sample_wishlist_item.id

    async def test_get_nonexistent_raises_error(
        self, wishlist_service: WishlistService
    ) -> None:
        """Getting a nonexistent item raises NotFoundError."""
        with pytest.raises(NotFoundError, match="not found"):
            await wishlist_service.get("00000000-0000-0000-0000-000000000000")


class TestWishlistServiceUpdate:
    """Tests for WishlistService.update."""

    async def test_update_changes_fields(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Updating changes the specified fields."""
        data = WishlistItemUpdate(
            priority=1,
            urgency="critical",
            notes="Updated notes",
        )

        result = await wishlist_service.update(sample_wishlist_item.id, data)

        assert result.priority == 1
        assert result.urgency == "critical"
        assert result.notes == "Updated notes"

    async def test_update_with_invalid_urgency_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Updating with invalid urgency raises ValidationError at schema level."""
        import pydantic

        with pytest.raises(pydantic.ValidationError, match="urgency must be one of"):
            WishlistItemUpdate(urgency="invalid")


class TestWishlistServiceDelete:
    """Tests for WishlistService.delete."""

    async def test_delete_removes_item(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Deleting removes the item."""
        item_id = sample_wishlist_item.id

        await wishlist_service.delete(item_id)

        with pytest.raises(NotFoundError):
            await wishlist_service.get(item_id)

    async def test_delete_nonexistent_raises_error(
        self, wishlist_service: WishlistService
    ) -> None:
        """Deleting a nonexistent item raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await wishlist_service.delete("00000000-0000-0000-0000-000000000000")


class TestWishlistServiceMarkAcquired:
    """Tests for WishlistService.mark_acquired."""

    async def test_mark_acquired_sets_fields(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """Marking acquired sets is_acquired and acquired_collection_item_id."""
        # Create a collection item to link
        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()
        await db_session.refresh(collection_item)

        data = WishlistAcquire(
            acquired_collection_item_id=collection_item.id,
        )

        result = await wishlist_service.mark_acquired(sample_wishlist_item.id, data)

        assert result.is_acquired is True
        assert result.acquired_date is not None
        assert result.acquired_collection_item_id == collection_item.id

    async def test_mark_acquired_already_acquired_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
        sample_collection: Collection,
        sample_catalog_item: CatalogItem,
        db_session: AsyncSession,
    ) -> None:
        """Marking already acquired item raises DuplicateError."""
        # Create a collection item
        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=sample_collection.id,
            catalog_item_id=sample_catalog_item.id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()
        await db_session.refresh(collection_item)

        # First acquisition
        data = WishlistAcquire(acquired_collection_item_id=collection_item.id)
        await wishlist_service.mark_acquired(sample_wishlist_item.id, data)

        # Second acquisition attempt
        with pytest.raises(DuplicateError, match="already acquired"):
            await wishlist_service.mark_acquired(sample_wishlist_item.id, data)

    async def test_mark_acquired_nonexistent_collection_item_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Marking acquired with nonexistent collection item raises NotFoundError."""
        data = WishlistAcquire(
            acquired_collection_item_id="00000000-0000-0000-0000-000000000000",
        )

        with pytest.raises(NotFoundError, match="Collection item .* not found"):
            await wishlist_service.mark_acquired(sample_wishlist_item.id, data)


# ------------------------------------------------------------------
# Sighting tests
# ------------------------------------------------------------------


class TestWishlistServiceSightings:
    """Tests for sighting operations."""

    async def test_create_sighting(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Creating a sighting works."""
        data = SightingCreate(
            wishlist_item_id=sample_wishlist_item.id,
            price=Decimal("45.00"),
            currency="USD",
            condition="good",
        )

        result = await wishlist_service.create_sighting(data)

        assert result.id is not None
        assert result.price == Decimal("45.00")
        assert result.condition == "good"

    async def test_create_sighting_with_invalid_decision_raises_error(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Creating a sighting with invalid decision raises ValidationError at schema level."""
        import pydantic

        with pytest.raises(pydantic.ValidationError, match="decision must be one of"):
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("45.00"),
                decision="invalid_decision",
            )

    async def test_list_sightings(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Listing sightings returns them in order."""
        # Create two sightings
        await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("40.00"),
                sighted_at=datetime(2024, 1, 1, 12, 0),
            )
        )
        await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("50.00"),
                sighted_at=datetime(2024, 1, 2, 12, 0),
            )
        )

        result = await wishlist_service.list_sightings(sample_wishlist_item.id)

        assert len(result) == 2
        # Ordered by sighted_at desc
        assert result[0].price == Decimal("50.00")
        assert result[1].price == Decimal("40.00")

    async def test_update_sighting(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Updating a sighting works."""
        sighting = await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("45.00"),
            )
        )

        data = SightingUpdate(price=Decimal("55.00"), decision="buy")

        result = await wishlist_service.update_sighting(sighting.id, data)

        assert result.price == Decimal("55.00")
        assert result.decision == "buy"

    async def test_delete_sighting(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Deleting a sighting works."""
        sighting = await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("45.00"),
            )
        )

        await wishlist_service.delete_sighting(sighting.id)

        with pytest.raises(NotFoundError):
            await wishlist_service.update_sighting(
                sighting.id, SightingUpdate(price=Decimal("50.00"))
            )


class TestWishlistServicePriceAggregates:
    """Tests for price aggregate calculations."""

    async def test_aggregates_without_sightings_returns_zeros(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Aggregates with no sightings return zeros and nulls."""
        result = await wishlist_service.get_with_price_aggregates(
            sample_wishlist_item.id
        )

        assert result.price_aggregates.total_sightings == 0
        assert result.price_aggregates.available_sightings == 0
        assert result.price_aggregates.avg_price is None
        assert result.price_aggregates.min_price is None
        assert result.price_aggregates.max_price is None

    async def test_aggregates_with_sightings_returns_correct_values(
        self,
        wishlist_service: WishlistService,
        sample_wishlist_item: WishlistItem,
    ) -> None:
        """Aggregates with sightings return correct calculated values."""
        # Create three sightings
        await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("30.00"),
                is_available=True,
            )
        )
        await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("40.00"),
                is_available=True,
            )
        )
        await wishlist_service.create_sighting(
            SightingCreate(
                wishlist_item_id=sample_wishlist_item.id,
                price=Decimal("50.00"),
                is_available=False,
            )
        )

        result = await wishlist_service.get_with_price_aggregates(
            sample_wishlist_item.id
        )

        assert result.price_aggregates.total_sightings == 3
        assert result.price_aggregates.available_sightings == 2
        assert result.price_aggregates.avg_price == Decimal("40.00")
        assert result.price_aggregates.min_price == Decimal("30.00")
        assert result.price_aggregates.max_price == Decimal("50.00")
