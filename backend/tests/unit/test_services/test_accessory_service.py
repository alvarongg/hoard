"""Unit tests for AccessoryService (SQLite path)."""

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

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.accessory import AccessoryCreate, AccessoryUpdate
from api.services.accessory_service import AccessoryService
from core.exceptions import DuplicateError, NotFoundError, ValidationError


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
def service(db_session: AsyncSession) -> AccessoryService:
    return AccessoryService(db_session)


@pytest.fixture
async def collection_item(db_session: AsyncSession) -> CollectionItem:
    mc = MainCategory(id=str(uuid4()), name="MC", slug=f"mc-{uuid4().hex[:8]}")
    db_session.add(mc)
    await db_session.commit()
    sub = SubCategory(
        id=str(uuid4()), main_category_id=mc.id, name="SC", slug=f"sc-{uuid4().hex[:8]}"
    )
    db_session.add(sub)
    await db_session.commit()
    cat = Catalog(id=str(uuid4()), sub_category_id=sub.id, name="Cat")
    db_session.add(cat)
    await db_session.commit()
    ci = CatalogItem(id=str(uuid4()), catalog_id=cat.id, title="Item")
    db_session.add(ci)
    await db_session.commit()
    coll = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
    db_session.add(coll)
    await db_session.commit()
    item = CollectionItem(
        id=str(uuid4()),
        collection_id=coll.id,
        catalog_item_id=ci.id,
        condition="good",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


def _acc(**overrides: object) -> AccessoryCreate:
    defaults: dict = {"name": "Case", "quantity_total": 10, "minimum_stock_alert": 3}
    defaults.update(overrides)
    return AccessoryCreate(**defaults)


# ---------------------------------------------------------------------------
# CRUD + validation
# ---------------------------------------------------------------------------


async def test_create_valid(service):
    acc = await service.create(_acc())
    assert acc.id is not None
    await service._db.refresh(acc)
    assert acc.quantity_available == 10


async def test_create_blank_name_rejected():
    with pytest.raises(Exception):
        _acc(name="")


async def test_create_negative_total_rejected():
    with pytest.raises(Exception):
        _acc(quantity_total=-1)


async def test_update_fields(service):
    acc = await service.create(_acc())
    updated = await service.update(
        acc.id, AccessoryUpdate(unit_cost=Decimal("9.99"))
    )
    assert updated.unit_cost == Decimal("9.99")


# ---------------------------------------------------------------------------
# assign / unassign
# ---------------------------------------------------------------------------


async def test_assign_reduces_available(service, collection_item):
    acc = await service.create(_acc(quantity_total=10))
    await service.assign(collection_item.id, acc.id, 3)
    await service._db.refresh(acc)
    assert acc.quantity_in_use == 3
    assert service._available(acc) == 7


async def test_unassign_restores_available(service, collection_item):
    acc = await service.create(_acc(quantity_total=10))
    assignment = await service.assign(collection_item.id, acc.id, 3)
    await service.unassign(assignment.id)
    await service._db.refresh(acc)
    assert acc.quantity_in_use == 0


async def test_assign_duplicate_rejected(service, collection_item):
    acc = await service.create(_acc(quantity_total=10))
    await service.assign(collection_item.id, acc.id, 1)
    with pytest.raises(DuplicateError):
        await service.assign(collection_item.id, acc.id, 1)


async def test_assign_over_available_rejected_and_stock_intact(
    service, collection_item
):
    acc = await service.create(_acc(quantity_total=2))
    with pytest.raises(ValidationError):
        await service.assign(collection_item.id, acc.id, 5)
    await service._db.refresh(acc)
    assert acc.quantity_in_use == 0


# ---------------------------------------------------------------------------
# low stock + delete
# ---------------------------------------------------------------------------


async def test_low_stock_thresholds(service):
    below = await service.create(_acc(name="Below", quantity_total=2, minimum_stock_alert=5))
    equal = await service.create(_acc(name="Equal", quantity_total=5, minimum_stock_alert=5))
    above = await service.create(_acc(name="Above", quantity_total=20, minimum_stock_alert=5))
    low = await service.list_low_stock()
    ids = {a.id for a in low}
    assert below.id in ids
    assert equal.id in ids
    assert above.id not in ids


async def test_delete_with_assignments_rejected(service, collection_item):
    acc = await service.create(_acc())
    await service.assign(collection_item.id, acc.id, 1)
    with pytest.raises(DuplicateError):
        await service.delete(acc.id)


async def test_delete_without_assignments(service):
    acc = await service.create(_acc())
    await service.delete(acc.id)
    with pytest.raises(NotFoundError):
        await service.get(acc.id)


async def test_assign_unknown_item_raises(service):
    acc = await service.create(_acc())
    with pytest.raises(NotFoundError):
        await service.assign(str(uuid4()), acc.id, 1)
