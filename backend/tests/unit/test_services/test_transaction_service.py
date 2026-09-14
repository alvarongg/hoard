"""Unit tests for TransactionService (SQLite path + dialect parity)."""

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
from api.schemas.transaction import TransactionCreate, TransactionUpdate
from api.services.transaction_service import TransactionService
from core.exceptions import NotFoundError, ValidationError
from utils.computations import transaction_total


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
def service(db_session: AsyncSession) -> TransactionService:
    return TransactionService(db_session)


@pytest.fixture
async def collection_item(db_session: AsyncSession) -> CollectionItem:
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
    citem = CatalogItem(id=str(uuid4()), catalog_id=catalog.id, title="Item")
    db_session.add(citem)
    await db_session.commit()
    coll = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
    db_session.add(coll)
    await db_session.commit()
    item = CollectionItem(
        id=str(uuid4()),
        collection_id=coll.id,
        catalog_item_id=citem.id,
        condition="good",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


def _tx(**overrides: object) -> TransactionCreate:
    defaults: dict = {
        "transaction_type": "purchase",
        "transaction_date": date(2026, 1, 1),
        "amount": Decimal("100.00"),
        "currency": "USD",
    }
    defaults.update(overrides)
    return TransactionCreate(**defaults)


# ---------------------------------------------------------------------------
# create / validation
# ---------------------------------------------------------------------------


async def test_create_valid(service, collection_item):
    tx = await service.create(collection_item.id, _tx())
    assert tx.id is not None
    assert tx.total_amount == Decimal("100.00")


async def test_create_all_valid_types(service, collection_item):
    types = [
        "purchase",
        "sale",
        "trade_in",
        "trade_out",
        "gift_received",
        "gift_given",
        "grading_fee",
        "repair",
        "appraisal",
        "other",
    ]
    for i, tt in enumerate(types):
        tx = await service.create(
            collection_item.id,
            _tx(transaction_type=tt, transaction_date=date(2026, 1, i + 1)),
        )
        assert tx.transaction_type == tt


async def test_create_invalid_type_rejected_by_schema():
    with pytest.raises(Exception):
        _tx(transaction_type="bogus")


async def test_create_unknown_item_raises(service):
    with pytest.raises(NotFoundError):
        await service.create(str(uuid4()), _tx())


# ---------------------------------------------------------------------------
# total_amount computation + parity
# ---------------------------------------------------------------------------


async def test_total_amount_with_all_fields(service, collection_item):
    tx = await service.create(
        collection_item.id,
        _tx(
            amount=Decimal("100.00"),
            shipping_cost=Decimal("10.00"),
            tax_amount=Decimal("5.00"),
            other_fees=Decimal("2.00"),
        ),
    )
    assert tx.total_amount == Decimal("117.00")


async def test_total_amount_partial_nulls(service, collection_item):
    tx = await service.create(
        collection_item.id,
        _tx(amount=Decimal("100.00"), shipping_cost=Decimal("10.00")),
    )
    assert tx.total_amount == Decimal("110.00")


async def test_total_amount_all_nulls(service, collection_item):
    tx = await service.create(
        collection_item.id,
        _tx(amount=None),
    )
    assert tx.total_amount == Decimal("0")


async def test_dialect_parity_total_matches_computation(service, collection_item):
    amount, shipping, tax, fees = (
        Decimal("42.50"),
        Decimal("7.00"),
        Decimal("3.25"),
        None,
    )
    tx = await service.create(
        collection_item.id,
        _tx(amount=amount, shipping_cost=shipping, tax_amount=tax, other_fees=fees),
    )
    assert tx.total_amount == transaction_total(amount, shipping, tax, fees)


# ---------------------------------------------------------------------------
# list / update / delete
# ---------------------------------------------------------------------------


async def test_list_orders_desc(service, collection_item):
    await service.create(
        collection_item.id, _tx(transaction_date=date(2026, 1, 1))
    )
    await service.create(
        collection_item.id, _tx(transaction_date=date(2026, 3, 1))
    )
    txs = await service.list(collection_item.id)
    assert [t.transaction_date for t in txs] == [date(2026, 3, 1), date(2026, 1, 1)]


async def test_update(service, collection_item):
    tx = await service.create(collection_item.id, _tx())
    updated = await service.update(
        tx.id, TransactionUpdate(amount=Decimal("200.00"))
    )
    assert updated.amount == Decimal("200.00")
    assert updated.total_amount == Decimal("200.00")


async def test_update_unknown_raises(service):
    with pytest.raises(NotFoundError):
        await service.update(str(uuid4()), TransactionUpdate(amount=Decimal("1")))


# ---------------------------------------------------------------------------
# investment
# ---------------------------------------------------------------------------


async def test_investment_only_outflows(service, collection_item):
    await service.create(
        collection_item.id, _tx(transaction_type="purchase", amount=Decimal("100"))
    )
    await service.create(
        collection_item.id,
        _tx(transaction_type="repair", amount=Decimal("20"),
            transaction_date=date(2026, 2, 1)),
    )
    inv = await service.get_investment(collection_item.id)
    assert inv.real_invested == Decimal("120.00")
    assert inv.total_inflow == Decimal("0")
    assert inv.source == "transactions"


async def test_investment_with_inflows(service, collection_item):
    await service.create(
        collection_item.id, _tx(transaction_type="purchase", amount=Decimal("100"))
    )
    await service.create(
        collection_item.id,
        _tx(transaction_type="sale", amount=Decimal("30"),
            transaction_date=date(2026, 2, 1)),
    )
    inv = await service.get_investment(collection_item.id)
    assert inv.real_invested == Decimal("70.00")
    assert inv.total_inflow == Decimal("30.00")


async def test_investment_fallback_to_purchase_price(
    service, collection_item, db_session
):
    collection_item.purchase_price = Decimal("55.00")
    await db_session.commit()
    inv = await service.get_investment(collection_item.id)
    assert inv.source == "purchase_price"
    assert inv.real_invested == Decimal("55.00")


async def test_investment_roi_none_when_zero_investment(
    service, collection_item, db_session
):
    collection_item.current_market_value = Decimal("100.00")
    await db_session.commit()
    # purchase 100, sale 100 -> real_invested 0 -> ROI None
    await service.create(
        collection_item.id, _tx(transaction_type="purchase", amount=Decimal("100"))
    )
    await service.create(
        collection_item.id,
        _tx(transaction_type="sale", amount=Decimal("100"),
            transaction_date=date(2026, 2, 1)),
    )
    inv = await service.get_investment(collection_item.id)
    assert inv.real_invested == Decimal("0")
    assert inv.roi_percentage is None


async def test_delete_returns_recomputed_investment(service, collection_item):
    tx1 = await service.create(
        collection_item.id, _tx(transaction_type="purchase", amount=Decimal("100"))
    )
    await service.create(
        collection_item.id,
        _tx(transaction_type="repair", amount=Decimal("20"),
            transaction_date=date(2026, 2, 1)),
    )
    inv = await service.delete(tx1.id)
    assert inv.real_invested == Decimal("20.00")


async def test_delete_unknown_raises(service):
    with pytest.raises(NotFoundError):
        await service.delete(str(uuid4()))
