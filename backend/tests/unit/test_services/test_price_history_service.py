"""Unit tests for PriceHistoryService."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.price_history import PriceHistoryCreate
from api.services.price_history_service import PriceHistoryService
from core.exceptions import DuplicateError, NotFoundError


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


@pytest.fixture()
async def engine():
    from api.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def service(db_session: AsyncSession) -> PriceHistoryService:
    return PriceHistoryService(db_session)


@pytest.fixture
async def sample_catalog_item(db_session: AsyncSession) -> CatalogItem:
    main = MainCategory(id=str(uuid4()), name="MC", slug=f"mc-{uuid4().hex[:8]}")
    db_session.add(main)
    await db_session.commit()
    sub = SubCategory(
        id=str(uuid4()),
        main_category_id=main.id,
        name="SC",
        slug=f"sc-{uuid4().hex[:8]}",
    )
    db_session.add(sub)
    await db_session.commit()
    catalog = Catalog(id=str(uuid4()), sub_category_id=sub.id, name="Cat")
    db_session.add(catalog)
    await db_session.commit()
    item = CatalogItem(id=str(uuid4()), catalog_id=catalog.id, title="Item")
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def sample_collection_item(
    db_session: AsyncSession, sample_catalog_item: CatalogItem
) -> CollectionItem:
    collection = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
    db_session.add(collection)
    await db_session.commit()
    item = CollectionItem(
        id=str(uuid4()),
        collection_id=collection.id,
        catalog_item_id=sample_catalog_item.id,
        condition="good",
        is_complete=True,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


def _price(**overrides: object) -> PriceHistoryCreate:
    defaults: dict = {
        "condition": "good",
        "is_complete": True,
        "price": Decimal("50.00"),
        "currency": "USD",
        "source": "eBay",
        "price_date": date(2026, 1, 1),
    }
    defaults.update(overrides)
    return PriceHistoryCreate(**defaults)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


async def test_create_valid(service, sample_catalog_item):
    record = await service.create(sample_catalog_item.id, _price())
    assert record.id is not None
    assert record.price == Decimal("50.00")
    assert record.catalog_item_id == sample_catalog_item.id


async def test_create_unknown_catalog_item_raises(service):
    with pytest.raises(NotFoundError):
        await service.create(str(uuid4()), _price())


async def test_create_duplicate_natural_key_raises(service, sample_catalog_item):
    await service.create(sample_catalog_item.id, _price())
    with pytest.raises(DuplicateError):
        await service.create(sample_catalog_item.id, _price())


async def test_create_differing_source_is_not_duplicate(service, sample_catalog_item):
    await service.create(sample_catalog_item.id, _price(source="eBay"))
    record = await service.create(
        sample_catalog_item.id, _price(source="PriceCharting")
    )
    assert record.id is not None


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


async def test_list_orders_by_price_date_desc(service, sample_catalog_item):
    await service.create(
        sample_catalog_item.id, _price(price_date=date(2026, 1, 1), source="a")
    )
    await service.create(
        sample_catalog_item.id, _price(price_date=date(2026, 3, 1), source="b")
    )
    records = await service.list(sample_catalog_item.id)
    assert [r.price_date for r in records] == [date(2026, 3, 1), date(2026, 1, 1)]


async def test_list_filters(service, sample_catalog_item):
    await service.create(
        sample_catalog_item.id, _price(condition="good", region="US", source="a")
    )
    await service.create(
        sample_catalog_item.id, _price(condition="mint", region="EU", source="b")
    )
    good = await service.list(sample_catalog_item.id, condition="good")
    assert len(good) == 1 and good[0].condition == "good"
    eu = await service.list(sample_catalog_item.id, region="EU")
    assert len(eu) == 1 and eu[0].region == "EU"


async def test_list_empty(service, sample_catalog_item):
    assert await service.list(sample_catalog_item.id) == []


async def test_list_date_range(service, sample_catalog_item):
    await service.create(
        sample_catalog_item.id, _price(price_date=date(2025, 1, 1), source="a")
    )
    await service.create(
        sample_catalog_item.id, _price(price_date=date(2026, 6, 1), source="b")
    )
    result = await service.list(sample_catalog_item.id, date_from=date(2026, 1, 1))
    assert len(result) == 1 and result[0].price_date == date(2026, 6, 1)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


async def test_delete(service, sample_catalog_item):
    record = await service.create(sample_catalog_item.id, _price())
    await service.delete(record.id)
    assert await service.list(sample_catalog_item.id) == []


async def test_delete_unknown_raises(service):
    with pytest.raises(NotFoundError):
        await service.delete(str(uuid4()))


# ---------------------------------------------------------------------------
# latest_by_condition
# ---------------------------------------------------------------------------


async def test_latest_by_condition(service, sample_catalog_item):
    await service.create(
        sample_catalog_item.id,
        _price(condition="good", price_date=date(2026, 1, 1), source="a"),
    )
    await service.create(
        sample_catalog_item.id,
        _price(condition="good", price_date=date(2026, 5, 1), source="b"),
    )
    await service.create(
        sample_catalog_item.id,
        _price(condition="mint", price_date=date(2026, 2, 1), source="c"),
    )
    latest = await service.latest_by_condition(sample_catalog_item.id)
    by_cond = {r.condition: r for r in latest}
    assert by_cond["good"].price_date == date(2026, 5, 1)
    assert by_cond["mint"].price_date == date(2026, 2, 1)


# ---------------------------------------------------------------------------
# refresh_item_market_value
# ---------------------------------------------------------------------------


async def test_refresh_with_compatible_price(
    service, sample_catalog_item, sample_collection_item
):
    await service.create(
        sample_catalog_item.id,
        _price(condition="good", is_complete=True, price=Decimal("75.00")),
    )
    updated, item, reason = await service.refresh_item_market_value(
        sample_collection_item.id
    )
    assert updated is True
    assert reason is None
    assert item.current_market_value == Decimal("75.00")
    assert item.value_source is not None
    assert item.last_value_update is not None


async def test_refresh_without_compatible_price_leaves_value(
    service, sample_catalog_item, sample_collection_item
):
    # Only an incompatible-condition price exists.
    await service.create(
        sample_catalog_item.id,
        _price(condition="poor", is_complete=True, price=Decimal("10.00")),
    )
    updated, item, reason = await service.refresh_item_market_value(
        sample_collection_item.id
    )
    assert updated is False
    assert reason is not None
    assert item.current_market_value is None


async def test_refresh_unknown_collection_item_raises(service):
    with pytest.raises(NotFoundError):
        await service.refresh_item_market_value(str(uuid4()))
