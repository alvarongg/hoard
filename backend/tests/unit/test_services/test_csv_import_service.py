"""Unit tests for CsvImportService business logic.

Tests cover file level validation (size, encoding, headers, empty files),
row level processing (valid rows, invalid rows, unrecognized columns) and
the side effects of a successful import (persisted items, total_items).

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.services.csv_import_service import CsvImportService
from core.exceptions import NotFoundError, ValidationError

FILENAME = "items.csv"
ALL_COLUMNS_HEADER = (
    "title,subtitle,description,manufacturer,publisher,developer,"
    "brand,language,region,rarity,sku,upc"
)


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
def service(db_session: AsyncSession) -> CsvImportService:
    """Provide a CsvImportService wired to the test session."""
    return CsvImportService(db_session)


@pytest.fixture()
async def catalog(db_session: AsyncSession) -> Catalog:
    """Provide a persisted catalog ready to receive imported items."""
    return await _seed_catalog(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_catalog(
    db_session: AsyncSession, name: str = "N64 Games",
) -> Catalog:
    """Create the category chain and return a persisted Catalog."""
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db_session.add(main)
    await db_session.commit()

    sub = SubCategory(
        main_category_id=main.id, name="Consolas", slug="consolas",
    )
    db_session.add(sub)
    await db_session.commit()

    catalog = Catalog(sub_category_id=sub.id, name=name, total_items=0)
    db_session.add(catalog)
    await db_session.commit()
    await db_session.refresh(catalog)
    return catalog


def _csv(*lines: str) -> bytes:
    """Encode CSV lines as UTF-8 bytes."""
    return "\n".join(lines).encode("utf-8")


async def _stored_items(
    db_session: AsyncSession, catalog_id: str,
) -> list[CatalogItem]:
    """Return every persisted item of a catalog ordered by title."""
    result = await db_session.execute(
        select(CatalogItem)
        .where(CatalogItem.catalog_id == catalog_id)
        .order_by(CatalogItem.title),
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Valid imports
# ---------------------------------------------------------------------------


class TestImportValidCsv:
    """Tests for CsvImportService.import_catalog_items with valid files."""

    @pytest.mark.asyncio
    async def test_import_csv_with_all_columns_creates_items(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv(
            ALL_COLUMNS_HEADER,
            "Super Mario 64,Nintendo Classic,A platformer,Nintendo,"
            "Nintendo,Nintendo EAD,Nintendo,English,NTSC,Common,"
            "NUS-NSME,045496870010",
        )

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        assert result.created_count == 1
        assert result.error_count == 0
        assert result.errors == []

        items = await _stored_items(db_session, catalog.id)
        assert len(items) == 1
        item = items[0]
        assert item.title == "Super Mario 64"
        assert item.subtitle == "Nintendo Classic"
        assert item.description == "A platformer"
        assert item.manufacturer == "Nintendo"
        assert item.publisher == "Nintendo"
        assert item.developer == "Nintendo EAD"
        assert item.brand == "Nintendo"
        assert item.language == "English"
        assert item.region == "NTSC"
        assert item.rarity == "Common"
        assert item.sku == "NUS-NSME"
        assert item.upc == "045496870010"
        assert item.catalog_id == catalog.id

    @pytest.mark.asyncio
    async def test_import_csv_with_only_title_column_creates_items(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv("title", "GoldenEye 007", "Perfect Dark", "F-Zero X")

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        assert result.created_count == 3
        assert result.error_count == 0

        items = await _stored_items(db_session, catalog.id)
        assert [i.title for i in items] == [
            "F-Zero X", "GoldenEye 007", "Perfect Dark",
        ]

    @pytest.mark.asyncio
    async def test_import_csv_ignores_unrecognized_columns(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv(
            "title,unknown_column,price,is_prototype",
            "Banjo-Kazooie,ignored value,49.99,yes",
        )

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        assert result.created_count == 1
        assert result.error_count == 0

        items = await _stored_items(db_session, catalog.id)
        assert items[0].title == "Banjo-Kazooie"
        assert items[0].is_prototype is False
        assert not hasattr(items[0], "price")

    @pytest.mark.asyncio
    async def test_import_csv_updates_catalog_total_items(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv("title", "Star Fox 64", "Wave Race 64", "Mario Party")

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        await db_session.refresh(catalog)
        assert result.created_count == 3
        assert catalog.total_items == 3

    @pytest.mark.asyncio
    async def test_import_csv_total_items_counts_only_created_rows(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv(
            "title",
            "Diddy Kong Racing",
            "   ",  # invalid: whitespace-only title
            "Mario Kart 64",
        )

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        await db_session.refresh(catalog)
        assert result.created_count == 2
        assert result.error_count == 1
        assert catalog.total_items == 2


# ---------------------------------------------------------------------------
# Partially invalid files
# ---------------------------------------------------------------------------


class TestImportPartiallyInvalidCsv:
    """Tests for per-row error reporting during import."""

    @pytest.mark.asyncio
    async def test_import_csv_with_mixed_rows_creates_valid_and_reports_errors(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv(
            "title,region",
            "Valid Item,NTSC",  # line 2 - ok
            "   ,PAL",  # line 3 - whitespace-only title
            f"{'x' * 501},NTSC",  # line 4 - title too long
            "Another Valid Item,PAL",  # line 5 - ok
        )

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        assert result.created_count == 2
        assert result.error_count == 2
        assert [error.row for error in result.errors] == [3, 4]
        assert all(error.message for error in result.errors)

        items = await _stored_items(db_session, catalog.id)
        assert [i.title for i in items] == ["Another Valid Item", "Valid Item"]

    @pytest.mark.asyncio
    async def test_import_csv_error_reports_row_number_and_reason(
        self, service: CsvImportService, catalog: Catalog,
    ) -> None:
        content = _csv("title,region", "Valid Item,NTSC", ",PAL")

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        assert result.error_count == 1
        error = result.errors[0]
        assert error.row == 3
        assert "title" in error.message.lower()

    @pytest.mark.asyncio
    async def test_import_csv_with_all_rows_invalid_creates_nothing(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
    ) -> None:
        content = _csv("title", "   ", "\t")

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        await db_session.refresh(catalog)
        assert result.created_count == 0
        assert result.error_count == 2
        assert await _stored_items(db_session, catalog.id) == []
        assert catalog.total_items == 0


# ---------------------------------------------------------------------------
# File level validation
# ---------------------------------------------------------------------------


class TestImportFileValidation:
    """Tests for file level rejections before any row is processed."""

    @pytest.mark.asyncio
    async def test_import_csv_without_title_column_raises_validation_error(
        self, service: CsvImportService, catalog: Catalog,
    ) -> None:
        content = _csv("name,region", "Super Mario 64,NTSC")

        with pytest.raises(ValidationError, match="title"):
            await service.import_catalog_items(catalog.id, content, FILENAME)

    @pytest.mark.asyncio
    async def test_import_csv_with_only_headers_raises_no_data_rows_error(
        self, service: CsvImportService, catalog: Catalog,
    ) -> None:
        content = _csv("title,region")

        with pytest.raises(ValidationError, match="no data rows"):
            await service.import_catalog_items(catalog.id, content, FILENAME)

    @pytest.mark.asyncio
    async def test_import_csv_exceeding_max_size_raises_validation_error(
        self, service: CsvImportService, catalog: Catalog,
    ) -> None:
        oversized = b"title\n" + b"a" * CsvImportService.MAX_FILE_SIZE

        with pytest.raises(ValidationError, match="maximum size"):
            await service.import_catalog_items(catalog.id, oversized, FILENAME)

    @pytest.mark.asyncio
    async def test_import_csv_with_non_utf8_encoding_raises_validation_error(
        self, service: CsvImportService, catalog: Catalog,
    ) -> None:
        content = "title\nCafé Latino".encode("latin-1")

        with pytest.raises(ValidationError, match="UTF-8"):
            await service.import_catalog_items(catalog.id, content, FILENAME)

    @pytest.mark.asyncio
    async def test_import_csv_with_nonexistent_catalog_raises_not_found(
        self, service: CsvImportService,
    ) -> None:
        content = _csv("title", "Orphan Item")

        with pytest.raises(NotFoundError, match="not found"):
            await service.import_catalog_items(
                "nonexistent-uuid", content, FILENAME,
            )
