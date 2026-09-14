"""Unit tests for CollectionStatsService business logic.

Tests cover statistics calculations for collections, including
total items, categories, investment, value, and ROI.

Requirements: REQ-001, REQ-007
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.services.collection_stats_service import CollectionStatsService
from core.exceptions import NotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(_engine) -> AsyncSession:
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture()
def service(db_session: AsyncSession) -> CollectionStatsService:
    """Provide a CollectionStatsService wired to the test session."""
    return CollectionStatsService(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_category_hierarchy(
    db_session: AsyncSession,
) -> tuple[MainCategory, SubCategory]:
    """Create a MainCategory + SubCategory and return both."""
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db_session.add(main)
    await db_session.flush()

    sub = SubCategory(
        main_category_id=main.id, name="Consolas", slug="consolas",
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)
    return main, sub


async def _seed_catalog(
    db_session: AsyncSession,
    sub_category: SubCategory,
    name: str = "Test Catalog",
) -> Catalog:
    """Create a catalog and return it."""
    catalog = Catalog(
        sub_category_id=sub_category.id,
        name=name,
    )
    db_session.add(catalog)
    await db_session.commit()
    await db_session.refresh(catalog)
    return catalog


async def _seed_catalog_item(
    db_session: AsyncSession,
    catalog: Catalog,
    title: str = "Nintendo 64",
) -> CatalogItem:
    """Create a catalog item and return it."""
    item = CatalogItem(
        catalog_id=catalog.id,
        title=title,
        region="NTSC",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _seed_collection(
    db_session: AsyncSession,
    name: str = "Test Collection",
) -> Collection:
    """Create a collection and return it."""
    collection = Collection(name=name, collection_type="multi_category")
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection


async def _seed_collection_item(
    db_session: AsyncSession,
    collection: Collection,
    catalog_item: CatalogItem,
    condition: str = "good",
    purchase_price: float | None = None,
    current_market_value: float | None = None,
    is_complete: bool = False,
    is_graded: bool = False,
) -> CollectionItem:
    """Create a collection item and return it."""
    item = CollectionItem(
        collection_id=collection.id,
        catalog_item_id=catalog_item.id,
        condition=condition,
        purchase_price=purchase_price,
        current_market_value=current_market_value,
        is_complete=is_complete,
        is_graded=is_graded,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Get collection stats tests
# ---------------------------------------------------------------------------


class TestGetCollectionStats:
    """Tests for CollectionStatsService.get_collection_stats."""

    @pytest.mark.asyncio
    async def test_nonexistent_collection_raises_not_found(
        self, service: CollectionStatsService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_collection_stats("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_empty_collection_returns_zero_counts(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        collection = await _seed_collection(db_session, name="Empty")

        stats = await service.get_collection_stats(collection.id)

        assert stats.total_items == 0
        assert stats.different_categories_count == 0
        assert stats.total_invested is None
        assert stats.current_value is None
        assert stats.value_gain is None
        assert stats.roi_percentage is None
        assert stats.complete_items == 0
        assert stats.graded_items == 0

    @pytest.mark.asyncio
    async def test_items_without_purchase_price_excluded_from_investment(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        _, sub = await _seed_category_hierarchy(db_session)
        catalog = await _seed_catalog(db_session, sub, "Test Catalog")
        catalog_item = await _seed_catalog_item(db_session, catalog, "N64")
        collection = await _seed_collection(db_session, name="No Price")
        await _seed_collection_item(
            db_session, collection, catalog_item,
            purchase_price=None,  # No purchase price
        )

        stats = await service.get_collection_stats(collection.id)

        assert stats.total_items == 1
        assert stats.total_invested is None or stats.total_invested == 0

    @pytest.mark.asyncio
    async def test_items_with_purchase_price_included_in_investment(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        _, sub = await _seed_category_hierarchy(db_session)
        catalog = await _seed_catalog(db_session, sub, "Test Catalog")
        catalog_item = await _seed_catalog_item(db_session, catalog, "N64")
        collection = await _seed_collection(db_session, name="With Price")
        await _seed_collection_item(
            db_session, collection, catalog_item,
            purchase_price=100.00,
        )

        stats = await service.get_collection_stats(collection.id)

        assert stats.total_items == 1
        assert stats.total_invested == 100.0

    @pytest.mark.asyncio
    async def test_current_value_and_gain_calculated(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        _, sub = await _seed_category_hierarchy(db_session)
        catalog = await _seed_catalog(db_session, sub, "Test Catalog")
        catalog_item = await _seed_catalog_item(db_session, catalog, "N64")
        collection = await _seed_collection(db_session, name="Value Test")
        await _seed_collection_item(
            db_session, collection, catalog_item,
            purchase_price=100.00,
            current_market_value=150.00,
        )

        stats = await service.get_collection_stats(collection.id)

        assert stats.total_invested == 100.0
        assert stats.current_value == 150.0
        assert stats.value_gain == 50.0

    @pytest.mark.asyncio
    async def test_roi_zero_investment_returns_none(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        """When total investment is zero, ROI is None (not a division error)."""
        _, sub = await _seed_category_hierarchy(db_session)
        catalog = await _seed_catalog(db_session, sub, "Test Catalog")
        catalog_item = await _seed_catalog_item(db_session, catalog, "N64")
        collection = await _seed_collection(db_session, name="Zero Invested")
        await _seed_collection_item(
            db_session, collection, catalog_item,
            purchase_price=None,
            current_market_value=150.00,
        )

        stats = await service.get_collection_stats(collection.id)

        # ROI should be None when there's no investment
        assert stats.roi_percentage is None

    @pytest.mark.asyncio
    async def test_complete_items_counted(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        _, sub = await _seed_category_hierarchy(db_session)
        catalog = await _seed_catalog(db_session, sub, "Test Catalog")
        catalog_item = await _seed_catalog_item(db_session, catalog, "N64")
        collection = await _seed_collection(db_session, name="Complete Test")
        await _seed_collection_item(
            db_session, collection, catalog_item,
            is_complete=True,
        )
        await _seed_collection_item(
            db_session, collection, catalog_item,
            is_complete=False,
        )

        stats = await service.get_collection_stats(collection.id)

        assert stats.complete_items == 1

    @pytest.mark.asyncio
    async def test_graded_items_counted(
        self, service: CollectionStatsService, db_session: AsyncSession,
    ) -> None:
        _, sub = await _seed_category_hierarchy(db_session)
        catalog = await _seed_catalog(db_session, sub, "Test Catalog")
        catalog_item = await _seed_catalog_item(db_session, catalog, "N64")
        collection = await _seed_collection(db_session, name="Graded Test")
        await _seed_collection_item(
            db_session, collection, catalog_item,
            is_graded=True,
        )
        await _seed_collection_item(
            db_session, collection, catalog_item,
            is_graded=False,
        )

        stats = await service.get_collection_stats(collection.id)

        assert stats.graded_items == 1
