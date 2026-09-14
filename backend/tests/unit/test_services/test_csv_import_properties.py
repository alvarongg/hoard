"""Property-based tests for CSV import of catalog items.

# Feature: inline-catalog-item-creation, Property 5: Consistencia de BatchImportResult

Requirements: 5.4, 5.5

Definition of "data row": a record yielded by :class:`csv.DictReader` for the
file, i.e. every line after the header **except** truly blank lines, which the
``csv`` module skips and which therefore never reach the service. The service
uses the same reader, so this is the only count both sides can agree on.
"""

from __future__ import annotations

import csv
from io import StringIO

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.services.csv_import_service import CsvImportService
from core.exceptions import ValidationError

FILENAME = "items.csv"
MAX_TITLE_LENGTH = 500
PROPERTY_ITERATIONS = 100

# Hypothesis reuses the same function-scoped fixtures for every generated
# example, which is safe here: each example only appends rows to an isolated
# in-memory database, and the property is expressed as a delta, so examples
# cannot influence each other's outcome.
property_settings = settings(
    max_examples=PROPERTY_ITERATIONS,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
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
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db_session.add(main)
    await db_session.commit()

    sub = SubCategory(
        main_category_id=main.id, name="Consolas", slug="consolas",
    )
    db_session.add(sub)
    await db_session.commit()

    catalog = Catalog(
        sub_category_id=sub.id, name="Property Catalog", total_items=0,
    )
    db_session.add(catalog)
    await db_session.commit()
    await db_session.refresh(catalog)
    return catalog


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Characters that exercise CSV quoting (delimiters, quotes, embedded newlines)
# and non-ASCII text. ``\r`` is left out on purpose: the csv module treats a
# lone carriage return as a line ending on read, so a round trip through
# writer/reader is not character preserving and the generated file would no
# longer describe the row count we intend to generate.
CELL_ALPHABET = "abZ019 áñ\t,\"';|\n"

WHITESPACE = " \t\n\v\f\u00a0\u2003"

OPTIONAL_COLUMNS = [
    "subtitle", "description", "manufacturer", "publisher", "developer",
    "brand", "language", "region", "rarity", "sku", "upc",
]
UNKNOWN_COLUMNS = ["price", "unknown_column", "is_prototype"]

cells = st.text(alphabet=CELL_ALPHABET, min_size=0, max_size=12)

# Titles are drawn from the regions that decide a row's fate: clearly valid,
# empty/whitespace-only (rejected) and over-long (rejected).
titles = st.one_of(
    st.text(alphabet=CELL_ALPHABET, min_size=1, max_size=20).filter(
        lambda s: s.strip() != ""
    ),
    st.text(alphabet=WHITESPACE, min_size=0, max_size=4),
    st.text(alphabet="ab", min_size=MAX_TITLE_LENGTH + 1,
            max_size=MAX_TITLE_LENGTH + 5),
)

# Rows are deliberately ragged: shorter rows leave columns unset, longer rows
# overflow into csv's restkey, and empty rows render as blank lines.
rows = st.lists(
    st.one_of(
        st.builds(
            lambda title, rest: [title, *rest],
            titles,
            st.lists(cells, max_size=4),
        ),
        st.lists(cells, max_size=4),
        st.just([]),
    ),
    min_size=0,
    max_size=8,
)

headers = st.builds(
    lambda extra: ["title", *extra],
    st.lists(
        st.sampled_from(OPTIONAL_COLUMNS + UNKNOWN_COLUMNS),
        max_size=5,
        unique=True,
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_csv(header: list[str], data_rows: list[list[str]]) -> str:
    """Render a header and its rows as CSV text with proper quoting."""
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(data_rows)
    return buffer.getvalue()


def _data_row_count(csv_text: str) -> int:
    """Return how many data rows the CSV file actually contains.

    Uses the same reader as the service, so blank lines (which ``csv``
    skips) are not counted as data rows.
    """
    return sum(1 for _ in csv.DictReader(StringIO(csv_text)))


async def _stored_item_count(db_session: AsyncSession, catalog_id: str) -> int:
    """Return how many items are persisted for a catalog."""
    result = await db_session.execute(
        select(func.count())
        .select_from(CatalogItem)
        .where(CatalogItem.catalog_id == catalog_id),
    )
    return int(result.scalar_one())


# ---------------------------------------------------------------------------
# Property 5
# ---------------------------------------------------------------------------


class TestBatchImportResultConsistencyProperty:
    """Property 5: Consistencia de BatchImportResult."""

    # Feature: inline-catalog-item-creation,
    # Property 5: Consistencia de BatchImportResult
    # Validates: Requirements 5.4, 5.5
    @given(header=headers, data_rows=rows)
    @example(header=["title"], data_rows=[["Valid"], [], ["Also valid"]])
    @example(header=["title"], data_rows=[[""]])
    @example(header=["title", "region"], data_rows=[["   ", "PAL"]])
    @example(header=["title"], data_rows=[["a" * (MAX_TITLE_LENGTH + 1)]])
    @example(
        header=["title", "sku", "price"],
        data_rows=[["Valid", "SKU-1", "9.99", "overflow"]],
    )
    @example(header=["title"], data_rows=[])
    @property_settings
    async def test_created_plus_error_count_equals_data_row_count(
        self,
        service: CsvImportService,
        db_session: AsyncSession,
        catalog: Catalog,
        header: list[str],
        data_rows: list[list[str]],
    ) -> None:
        csv_text = _render_csv(header, data_rows)
        content = csv_text.encode("utf-8")
        expected_rows = _data_row_count(csv_text)
        items_before = await _stored_item_count(db_session, catalog.id)

        if expected_rows == 0:
            with pytest.raises(ValidationError, match="no data rows"):
                await service.import_catalog_items(
                    catalog.id, content, FILENAME,
                )
            return

        result = await service.import_catalog_items(
            catalog.id, content, FILENAME,
        )

        assert result.created_count + result.error_count == expected_rows, (
            f"{result.created_count} created + {result.error_count} failed "
            f"!= {expected_rows} data rows for CSV {csv_text!r}"
        )
        assert result.error_count == len(result.errors)
        assert result.created_count >= 0

        # No row may vanish or be duplicated on the way to the database.
        items_after = await _stored_item_count(db_session, catalog.id)
        assert items_after - items_before == result.created_count
