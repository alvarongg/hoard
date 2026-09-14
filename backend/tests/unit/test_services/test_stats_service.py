"""Unit tests for StatsService."""

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
from api.models.transaction import ItemTransaction
from api.schemas.stats import TimelinePeriod
from api.services.stats_service import StatsService


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
def service(db_session: AsyncSession) -> StatsService:
    return StatsService(db_session)


async def _make_catalog_item(db: AsyncSession) -> str:
    mc = MainCategory(id=str(uuid4()), name="MC", slug=f"mc-{uuid4().hex[:8]}")
    db.add(mc)
    await db.commit()
    sub = SubCategory(
        id=str(uuid4()), main_category_id=mc.id, name="SC", slug=f"sc-{uuid4().hex[:8]}"
    )
    db.add(sub)
    await db.commit()
    cat = Catalog(id=str(uuid4()), sub_category_id=sub.id, name="Cat")
    db.add(cat)
    await db.commit()
    ci = CatalogItem(id=str(uuid4()), catalog_id=cat.id, title="Item")
    db.add(ci)
    await db.commit()
    return ci.id


async def _make_collection(db: AsyncSession) -> str:
    coll = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
    db.add(coll)
    await db.commit()
    return coll.id


async def _add_item(db, coll_id, cat_item_id, **kw) -> CollectionItem:
    item = CollectionItem(
        id=str(uuid4()),
        collection_id=coll_id,
        catalog_item_id=cat_item_id,
        condition="good",
        **kw,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# empty DB
# ---------------------------------------------------------------------------


async def test_dashboard_empty(service):
    dash = await service.get_dashboard()
    assert dash.total_collections == 0
    assert dash.total_items == 0
    assert dash.total_invested == Decimal("0")
    assert dash.roi_percentage is None


async def test_valuation_empty(service):
    val = await service.get_valuation()
    assert val.total_invested == Decimal("0")
    assert val.roi_percentage is None


# ---------------------------------------------------------------------------
# purchase_price vs transactions
# ---------------------------------------------------------------------------


async def test_item_without_purchase_price_excluded_from_investment(
    service, db_session
):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(db_session, coll, ci)  # no purchase_price
    val = await service.get_valuation()
    assert val.total_invested == Decimal("0")


async def test_investment_uses_purchase_price(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(db_session, coll, ci, purchase_price=Decimal("40.00"))
    val = await service.get_valuation()
    assert val.total_invested == Decimal("40.00")


async def test_investment_uses_transactions_when_present(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    item = await _add_item(
        db_session, coll, ci, purchase_price=Decimal("40.00")
    )
    # transaction outflow overrides purchase_price fallback
    db_session.add(
        ItemTransaction(
            id=str(uuid4()),
            collection_item_id=item.id,
            transaction_type="purchase",
            transaction_date=date(2026, 1, 1),
            amount=Decimal("100.00"),
        )
    )
    await db_session.commit()
    val = await service.get_valuation()
    assert val.total_invested == Decimal("100.00")


async def test_zero_investment_roi_none(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(
        db_session, coll, ci, current_market_value=Decimal("100.00")
    )
    dash = await service.get_dashboard()
    assert dash.total_invested == Decimal("0")
    assert dash.roi_percentage is None


# ---------------------------------------------------------------------------
# breakdowns
# ---------------------------------------------------------------------------


async def test_by_collection(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(db_session, coll, ci, purchase_price=Decimal("10.00"))
    entries = await service.get_by_collection()
    assert len(entries) == 1
    assert entries[0].total_items == 1
    assert entries[0].total_invested == Decimal("10.00")


async def test_by_category(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(
        db_session, coll, ci, current_market_value=Decimal("25.00")
    )
    entries = await service.get_by_category()
    assert len(entries) == 1
    assert entries[0].item_count == 1
    assert entries[0].current_value == Decimal("25.00")


async def test_timeline_month(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(
        db_session,
        coll,
        ci,
        acquisition_date=date(2026, 3, 15),
        purchase_price=Decimal("10.00"),
    )
    entries = await service.get_timeline(TimelinePeriod.MONTH)
    assert entries[0].period == "2026-03"
    assert entries[0].item_count == 1


async def test_timeline_quarter_and_year(service, db_session):
    coll = await _make_collection(db_session)
    ci = await _make_catalog_item(db_session)
    await _add_item(
        db_session, coll, ci, acquisition_date=date(2026, 5, 1)
    )
    q = await service.get_timeline(TimelinePeriod.QUARTER)
    assert q[0].period == "2026-Q2"
    y = await service.get_timeline(TimelinePeriod.YEAR)
    assert y[0].period == "2026"
