"""Unit tests for ExportService."""

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
from api.services.csv_import_service import CsvImportService
from api.services.export_service import ExportService
from core.exceptions import NotFoundError


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
def service(db_session: AsyncSession) -> ExportService:
    return ExportService(db_session)


async def _catalog(db) -> tuple[str, str]:
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
    ci = CatalogItem(id=str(uuid4()), catalog_id=cat.id, title="Item", region="US")
    db.add(ci)
    await db.commit()
    return cat.id, ci.id


async def test_export_collection_with_items_and_components(service, db_session):
    cat_id, ci_id = await _catalog(db_session)
    coll = Collection(id=str(uuid4()), name="Coll", collection_type="mixed")
    db_session.add(coll)
    await db_session.commit()
    item = CollectionItem(
        id=str(uuid4()),
        collection_id=coll.id,
        catalog_item_id=ci_id,
        condition="good",
        purchase_price=Decimal("50.00"),
    )
    db_session.add(item)
    await db_session.commit()
    db_session.add(
        ItemComponent(
            id=str(uuid4()),
            collection_item_id=item.id,
            component_name="box",
            is_present=True,
        )
    )
    await db_session.commit()

    export = await service.export_collection(coll.id)
    assert export.schema_version == "1.0"
    assert len(export.items) == 1
    assert export.items[0].components[0]["component_name"] == "box"
    assert len(export.catalog_items) == 1


async def test_export_empty_collection(service, db_session):
    coll = Collection(id=str(uuid4()), name="Empty", collection_type="mixed")
    db_session.add(coll)
    await db_session.commit()
    export = await service.export_collection(coll.id)
    assert export.items == []


async def test_export_catalog_json(service, db_session):
    cat_id, _ = await _catalog(db_session)
    export = await service.export_catalog_json(cat_id)
    assert export.entity_type == "catalog"
    assert len(export.items) == 1


async def test_export_catalog_csv_header_matches_importer(service, db_session):
    cat_id, _ = await _catalog(db_session)
    csv_text = await service.export_catalog_csv(cat_id)
    header = csv_text.splitlines()[0].split(",")
    expected = ["title", *sorted(CsvImportService.OPTIONAL_COLUMNS)]
    assert header == expected


async def test_export_unknown_raises(service):
    with pytest.raises(NotFoundError):
        await service.export_collection(str(uuid4()))
    with pytest.raises(NotFoundError):
        await service.export_catalog_json(str(uuid4()))
