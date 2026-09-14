"""Unit tests for collector-workflow models."""

from __future__ import annotations

from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from api.models import (
    Base,
    Catalog,
    CatalogItem,
    Collection,
    CollectionCatalog,
    CollectionItem,
    MainCategory,
    MaintenanceSchedule,
    PendingCompletion,
    SubCategory,
)

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = AsyncSession(engine, expire_on_commit=False)
    async with sessionmaker as session:
        yield session
    await engine.dispose()


async def _seed_catalog(session: AsyncSession) -> tuple[Collection, Catalog]:
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    session.add(main)
    await session.flush()
    sub = SubCategory(main_category_id=main.id, name="Famicom", slug="famicom")
    session.add(sub)
    await session.flush()
    catalog = Catalog(sub_category_id=sub.id, name="Famicom Games")
    collection = Collection(
        name="Mi Famicom",
        collection_type="single_category",
        restricted_to_sub_category_id=sub.id,
    )
    session.add_all([catalog, collection])
    await session.flush()
    return collection, catalog


async def test_collection_catalog_association(db_session: AsyncSession) -> None:
    collection, catalog = await _seed_catalog(db_session)
    db_session.add(
        CollectionCatalog(
            collection_id=collection.id, catalog_id=catalog.id, is_primary=True
        )
    )
    await db_session.commit()

    loaded = (
        await db_session.execute(
            select(Collection)
            .options(selectinload(Collection.catalogs))
            .where(Collection.id == collection.id)
        )
    ).scalar_one()
    assert [c.id for c in loaded.catalogs] == [catalog.id]


async def test_country_of_origin_persists(db_session: AsyncSession) -> None:
    collection, catalog = await _seed_catalog(db_session)
    ci_catalog = CatalogItem(catalog_id=catalog.id, title="Dennou Kyusei Uranai")
    db_session.add(ci_catalog)
    await db_session.flush()
    item = CollectionItem(
        collection_id=collection.id,
        catalog_item_id=ci_catalog.id,
        condition="good",
        country_of_origin="JP",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    assert item.country_of_origin == "JP"


async def test_maintenance_schedule_cascade(db_session: AsyncSession) -> None:
    collection, catalog = await _seed_catalog(db_session)
    ci_catalog = CatalogItem(catalog_id=catalog.id, title="Zelda no Densetsu")
    db_session.add(ci_catalog)
    await db_session.flush()
    item = CollectionItem(
        collection_id=collection.id,
        catalog_item_id=ci_catalog.id,
        condition="good",
    )
    db_session.add(item)
    await db_session.flush()
    sched = MaintenanceSchedule(
        collection_item_id=item.id,
        maintenance_type="battery",
        due_date=date(2027, 1, 1),
        notes="Cambiar pila CR2032",
    )
    db_session.add(sched)
    await db_session.commit()

    # Deleting the item cascades to its maintenance schedules.
    await db_session.delete(item)
    await db_session.commit()
    remaining = (
        await db_session.execute(select(MaintenanceSchedule))
    ).scalars().all()
    assert remaining == []


async def test_pending_completion_defaults(db_session: AsyncSession) -> None:
    pending = PendingCompletion(
        entity_type="supplier",
        entity_id="00000000-0000-0000-0000-000000000001",
        missing_fields=["type", "city"],
    )
    db_session.add(pending)
    await db_session.commit()
    await db_session.refresh(pending)
    assert pending.status == "open"
    assert pending.missing_fields == ["type", "city"]
    assert pending.resolved_at is None
