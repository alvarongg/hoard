"""Integration tests for the catalog CSV import endpoint.

Covers ``POST /api/catalogs/{catalog_id}/import-csv``: successful imports,
missing catalogs, oversized uploads, rejected content types and CSV files
that lack the required ``title`` column.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.6
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.dependencies import get_db
from api.models.base import Base
from api.services.csv_import_service import CsvImportService
from main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CSV_CONTENT_TYPE = "text/csv"
EXCEL_CONTENT_TYPE = "application/vnd.ms-excel"

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False,
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionFactory() as session:
        yield session


@pytest.fixture(autouse=True)
async def _setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test and drop them after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_catalog(client: AsyncClient) -> str:
    """Create category, sub-category and catalog; return the catalog id."""
    main = await client.post(
        "/api/categories",
        json={"name": "Videojuegos", "slug": "videojuegos"},
    )
    main_id = main.json()["id"]
    sub = await client.post(
        f"/api/categories/{main_id}/subcategories",
        json={
            "name": "Consolas",
            "slug": "consolas",
            "main_category_id": main_id,
        },
    )
    catalog = await client.post(
        "/api/catalogs",
        json={"name": "N64 Games", "sub_category_id": sub.json()["id"]},
    )
    assert catalog.status_code == 201
    return catalog.json()["id"]


async def _post_csv(
    client: AsyncClient,
    catalog_id: str,
    content: bytes,
    *,
    filename: str = "items.csv",
    content_type: str = CSV_CONTENT_TYPE,
):
    """POST a CSV upload to the import endpoint."""
    return await client.post(
        f"/api/catalogs/{catalog_id}/import-csv",
        files={"file": (filename, content, content_type)},
    )


# ---------------------------------------------------------------------------
# Successful import
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestImportCsvSuccess:
    async def test_import_valid_csv_returns_200_with_result(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)
        csv_bytes = (
            b"title,subtitle,manufacturer\n"
            b"Super Mario 64,Launch title,Nintendo\n"
            b"Ocarina of Time,,Nintendo\n"
        )

        response = await _post_csv(client, catalog_id, csv_bytes)

        assert response.status_code == 200
        body = response.json()
        assert body == {"created_count": 2, "error_count": 0, "errors": []}

    async def test_import_valid_csv_persists_items(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)
        csv_bytes = b"title\nSuper Mario 64\nOcarina of Time\n"

        await _post_csv(client, catalog_id, csv_bytes)

        items = await client.get(f"/api/catalogs/{catalog_id}/items")
        assert items.status_code == 200
        titles = {item["title"] for item in items.json()}
        assert titles == {"Super Mario 64", "Ocarina of Time"}

    async def test_import_accepts_excel_content_type(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)

        response = await _post_csv(
            client,
            catalog_id,
            b"title\nSuper Mario 64\n",
            content_type=EXCEL_CONTENT_TYPE,
        )

        assert response.status_code == 200
        assert response.json()["created_count"] == 1

    async def test_import_reports_invalid_rows_with_row_numbers(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)
        long_title = "x" * 501
        csv_bytes = (
            "title,subtitle\n"
            "Super Mario 64,Launch title\n"
            ",Missing title\n"
            f"{long_title},Too long\n"
        ).encode()

        response = await _post_csv(client, catalog_id, csv_bytes)

        assert response.status_code == 200
        body = response.json()
        assert body["created_count"] == 1
        assert body["error_count"] == 2
        assert all(error["row"] > 1 for error in body["errors"])
        assert all(error["message"] for error in body["errors"])


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestImportCsvErrors:
    async def test_import_into_nonexistent_catalog_returns_404(
        self, client: AsyncClient,
    ) -> None:
        response = await _post_csv(
            client, "nonexistent-catalog-id", b"title\nSuper Mario 64\n",
        )

        assert response.status_code == 404
        assert "nonexistent-catalog-id" in response.json()["detail"]

    async def test_import_file_larger_than_limit_returns_413(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)
        header = b"title\n"
        padding = b"a" * (CsvImportService.MAX_FILE_SIZE + 1 - len(header))
        oversized = header + padding

        response = await _post_csv(
            client, catalog_id, oversized, filename="big.csv",
        )

        assert response.status_code == 413
        assert "big.csv" in response.json()["detail"]

    async def test_import_invalid_content_type_returns_422(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)

        response = await _post_csv(
            client,
            catalog_id,
            b"title\nSuper Mario 64\n",
            filename="items.json",
            content_type="application/json",
        )

        assert response.status_code == 422
        assert "application/json" in response.json()["detail"]

    async def test_import_without_file_returns_422(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)

        response = await client.post(
            f"/api/catalogs/{catalog_id}/import-csv",
        )

        assert response.status_code == 422

    async def test_import_csv_without_title_column_returns_descriptive_error(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)
        csv_bytes = b"name,manufacturer\nSuper Mario 64,Nintendo\n"

        response = await _post_csv(
            client, catalog_id, csv_bytes, filename="no-title.csv",
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "no-title.csv" in detail
        assert "title" in detail

    async def test_import_csv_with_only_headers_returns_422(
        self, client: AsyncClient,
    ) -> None:
        catalog_id = await _seed_catalog(client)

        response = await _post_csv(
            client, catalog_id, b"title\n", filename="empty.csv",
        )

        assert response.status_code == 422
        assert "empty.csv" in response.json()["detail"]
