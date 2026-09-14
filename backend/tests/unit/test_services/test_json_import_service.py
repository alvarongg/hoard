"""Unit tests for JsonImportService."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.services.json_import_service import JsonImportService
from core.exceptions import ValidationError


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
def service(db_session: AsyncSession) -> JsonImportService:
    return JsonImportService(db_session)


@pytest.fixture
async def catalog_item_id(db_session: AsyncSession) -> str:
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
    return ci.id


def _envelope(cat_item_id: str, name: str = "My Collection") -> bytes:
    return json.dumps(
        {
            "schema_version": "1.0",
            "entity_type": "collection",
            "exported_at": "2026-01-01T00:00:00Z",
            "collection": {"name": name, "collection_type": "mixed"},
            "items": [
                {
                    "id": str(uuid4()),
                    "catalog_item_id": cat_item_id,
                    "condition": "good",
                    "is_complete": True,
                    "purchase_price": "50.00",
                }
            ],
        }
    ).encode("utf-8")


async def _count(db, model) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar()


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


async def test_invalid_json_rejected(service):
    with pytest.raises(ValidationError):
        await service.preview(b"{not json")


async def test_unsupported_version_rejected(service):
    payload = json.dumps(
        {"schema_version": "9.9", "entity_type": "collection", "collection": {}}
    ).encode()
    with pytest.raises(ValidationError):
        await service.preview(payload)


async def test_bad_structure_rejected(service):
    payload = json.dumps(
        {"schema_version": "1.0", "entity_type": "collection"}
    ).encode()
    with pytest.raises(ValidationError):
        await service.preview(payload)


async def test_oversize_rejected(service):
    big = b'{"schema_version":"1.0"}' + b" " * (11 * 1024 * 1024)
    with pytest.raises(ValidationError):
        await service.preview(big)


# ---------------------------------------------------------------------------
# preview does not write
# ---------------------------------------------------------------------------


async def test_preview_writes_nothing(service, db_session, catalog_item_id):
    before = await _count(db_session, Collection)
    preview = await service.preview(_envelope(catalog_item_id))
    after = await _count(db_session, Collection)
    assert before == after
    assert preview.to_create >= 1


# ---------------------------------------------------------------------------
# execute + idempotency
# ---------------------------------------------------------------------------


async def test_execute_creates(service, db_session, catalog_item_id):
    result = await service.execute(_envelope(catalog_item_id))
    assert result.created_count == 2  # collection + item
    assert await _count(db_session, Collection) == 1
    assert await _count(db_session, CollectionItem) == 1


async def test_execute_idempotent(service, db_session, catalog_item_id):
    env = _envelope(catalog_item_id)
    await service.execute(env)
    result2 = await service.execute(env)
    # second run updates the collection and skips the existing item
    assert result2.updated_count == 1
    assert result2.skipped_count == 1
    assert await _count(db_session, Collection) == 1
    assert await _count(db_session, CollectionItem) == 1


async def test_preview_and_execute_same_counts(service, catalog_item_id):
    env = _envelope(catalog_item_id)
    preview = await service.preview(env)
    result = await service.execute(env)
    assert result.created_count == preview.to_create


async def test_partial_errors_reported(service, db_session):
    # item without catalog_item_id is an error, collection still valid
    payload = json.dumps(
        {
            "schema_version": "1.0",
            "entity_type": "collection",
            "collection": {"name": "C", "collection_type": "mixed"},
            "items": [{"id": "x", "condition": "good"}],
        }
    ).encode()
    result = await service.execute(payload)
    assert result.error_count == 1
    assert result.created_count == 1  # the collection
