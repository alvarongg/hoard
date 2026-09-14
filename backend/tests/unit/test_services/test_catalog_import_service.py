"""Unit tests for CatalogImportService and CatalogLibraryService."""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.services.catalog_import_service import CatalogImportService
from api.services.catalog_library_service import CatalogLibraryService
from core.exceptions import NotFoundError, ValidationError


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
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


@pytest.fixture
def service(db_session: AsyncSession) -> CatalogImportService:
    return CatalogImportService(db_session)


def _envelope(items: list[dict] | None = None, name: str = "NES") -> bytes:
    payload = {
        "schema_version": "1.0",
        "entity_type": "catalog",
        "catalog": {
            "id": "nes",
            "name": name,
            "system": "nes",
            "version": "1.0.0",
            "source_type": "wikidata",
            "source_name": "Wikidata",
            "source_url": "https://www.wikidata.org/",
            "target_sub_category": {
                "category": "Video Games",
                "sub_category": "NES",
            },
        },
        "items": items
        if items is not None
        else [
            {
                "external_id": "wikidata:Q1",
                "title": "Castlevania",
                "region": "JP",
                "developer": "Konami",
                "publisher": "Konami",
                "release_date": "1986-09-26",
                "custom_fields": {
                    "released_regions": ["JP", "NA", "PAL"],
                    "planned_regions": [],
                    "unreleased_in": [],
                },
            },
            {
                "external_id": "wikidata:Q2",
                "title": "Devil World",
                "region": "JP",
                "developer": "Nintendo R&D1",
                "publisher": "Nintendo",
                "release_date": "1984-10-05",
                "custom_fields": {
                    "released_regions": ["JP", "PAL"],
                    "planned_regions": ["NA"],
                    "unreleased_in": ["NA"],
                },
            },
        ],
    }
    return json.dumps(payload).encode("utf-8")


# ---------------------------------------------------------------------------
# Parsing / validation
# ---------------------------------------------------------------------------


async def test_rejects_bad_json(service: CatalogImportService) -> None:
    with pytest.raises(ValidationError):
        await service.preview(b"{not json")


async def test_rejects_wrong_entity_type(service: CatalogImportService) -> None:
    bad = json.dumps(
        {"schema_version": "1.0", "entity_type": "collection", "catalog": {}}
    ).encode()
    with pytest.raises(ValidationError):
        await service.preview(bad)


async def test_rejects_unsupported_version(
    service: CatalogImportService,
) -> None:
    bad = json.dumps(
        {"schema_version": "9.9", "entity_type": "catalog"}
    ).encode()
    with pytest.raises(ValidationError):
        await service.preview(bad)


# ---------------------------------------------------------------------------
# Preview / execute idempotency
# ---------------------------------------------------------------------------


async def test_preview_counts_creates(service: CatalogImportService) -> None:
    plan = await service.preview(_envelope())
    assert plan.to_create == 2
    assert plan.to_update == 0
    assert plan.to_skip == 0


async def test_execute_creates_catalog_and_items(
    service: CatalogImportService, db_session: AsyncSession
) -> None:
    result = await service.execute(_envelope(), is_official=True)
    assert result.created_count == 2

    catalog = (
        await db_session.execute(select(Catalog))
    ).scalar_one()
    assert catalog.is_official is True
    assert catalog.source_type == "wikidata"
    assert catalog.version == "1.0.0"

    item_count = await db_session.scalar(
        select(func.count()).select_from(CatalogItem)
    )
    assert item_count == 2

    # Sub-category + main category were created.
    assert await db_session.scalar(
        select(func.count()).select_from(SubCategory)
    ) == 1
    assert await db_session.scalar(
        select(func.count()).select_from(MainCategory)
    ) == 1


async def test_reimport_is_idempotent(
    service: CatalogImportService, db_session: AsyncSession
) -> None:
    await service.execute(_envelope(), is_official=True)
    result = await service.execute(_envelope(), is_official=True)
    assert result.created_count == 0
    assert result.skipped_count == 2
    # Still only two items.
    assert await db_session.scalar(
        select(func.count()).select_from(CatalogItem)
    ) == 2


async def test_reimport_updates_changed_field(
    service: CatalogImportService, db_session: AsyncSession
) -> None:
    await service.execute(_envelope(), is_official=True)
    changed = _envelope(
        items=[
            {
                "external_id": "wikidata:Q1",
                "title": "Castlevania",
                "region": "JP",
                "developer": "Konami",
                "publisher": "Konami (JP)",  # changed
                "release_date": "1986-09-26",
                "custom_fields": {
                    "released_regions": ["JP", "NA", "PAL"],
                    "planned_regions": [],
                    "unreleased_in": [],
                },
            },
            {
                "external_id": "wikidata:Q2",
                "title": "Devil World",
                "region": "JP",
                "developer": "Nintendo R&D1",
                "publisher": "Nintendo",
                "release_date": "1984-10-05",
                "custom_fields": {
                    "released_regions": ["JP", "PAL"],
                    "planned_regions": ["NA"],
                    "unreleased_in": ["NA"],
                },
            },
        ]
    )
    result = await service.execute(changed, is_official=True)
    assert result.updated_count == 1
    assert result.skipped_count == 1


async def test_unparseable_release_date_becomes_null(
    service: CatalogImportService, db_session: AsyncSession
) -> None:
    env = _envelope(
        items=[
            {
                "external_id": "wikidata:Q3",
                "title": "Mystery",
                "region": "NA",
                "release_date": "circa 1990",
            }
        ]
    )
    await service.execute(env)
    item = (await db_session.execute(select(CatalogItem))).scalar_one()
    assert item.release_date is None
    assert item.custom_fields["external_id"] == "wikidata:Q3"


async def test_planned_but_unreleased_preserved(
    service: CatalogImportService, db_session: AsyncSession
) -> None:
    await service.execute(_envelope())
    devil = (
        await db_session.execute(
            select(CatalogItem).where(CatalogItem.title == "Devil World")
        )
    ).scalar_one()
    assert devil.custom_fields["unreleased_in"] == ["NA"]
    assert devil.custom_fields["planned_regions"] == ["NA"]


# ---------------------------------------------------------------------------
# Library service (manifest + checksum)
# ---------------------------------------------------------------------------


@pytest.fixture
def library_dir(tmp_path):
    catalog_bytes = _envelope()
    (tmp_path / "nes.v1.json").write_bytes(catalog_bytes)
    checksum = "sha256:" + hashlib.sha256(catalog_bytes).hexdigest()
    manifest = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "nes",
                "name": "NES",
                "system": "nes",
                "version": "1.0.0",
                "item_count": 2,
                "path": "nes.v1.json",
                "checksum": checksum,
            }
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return tmp_path


async def test_library_lists_manifest(
    db_session: AsyncSession, library_dir
) -> None:
    svc = CatalogLibraryService(
        CatalogImportService(db_session), str(library_dir)
    )
    manifest = svc.read_manifest()
    assert manifest["catalogs"][0]["id"] == "nes"


async def test_library_load_marks_official(
    db_session: AsyncSession, library_dir
) -> None:
    svc = CatalogLibraryService(
        CatalogImportService(db_session), str(library_dir)
    )
    result = await svc.load("nes")
    assert result.created_count == 2
    catalog = (await db_session.execute(select(Catalog))).scalar_one()
    assert catalog.is_official is True


async def test_library_unknown_id_raises(
    db_session: AsyncSession, library_dir
) -> None:
    svc = CatalogLibraryService(
        CatalogImportService(db_session), str(library_dir)
    )
    with pytest.raises(NotFoundError):
        await svc.load("does-not-exist")


async def test_library_checksum_mismatch_aborts(
    db_session: AsyncSession, tmp_path
) -> None:
    (tmp_path / "nes.v1.json").write_bytes(_envelope())
    manifest = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "nes",
                "path": "nes.v1.json",
                "checksum": "sha256:deadbeef",
            }
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    svc = CatalogLibraryService(
        CatalogImportService(db_session), str(tmp_path)
    )
    with pytest.raises(ValidationError):
        await svc.load("nes")
    # Nothing written.
    assert await db_session.scalar(
        select(func.count()).select_from(Catalog)
    ) == 0


async def test_library_missing_manifest_returns_empty(
    db_session: AsyncSession, tmp_path
) -> None:
    svc = CatalogLibraryService(
        CatalogImportService(db_session), str(tmp_path)
    )
    assert svc.read_manifest()["catalogs"] == []
