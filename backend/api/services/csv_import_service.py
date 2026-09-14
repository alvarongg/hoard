"""Business logic for importing catalog items from CSV files."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ValidationError as SchemaValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog, CatalogItem
from api.schemas.catalog import CatalogItemCreate
from api.schemas.csv_import import BatchImportError, BatchImportResult
from core.exceptions import NotFoundError, ValidationError


class CsvImportService:
    """Parses CSV uploads and creates the catalog items they describe.

    Rows are processed independently: valid rows are inserted and invalid
    rows are reported, so a partially malformed file still imports what
    it can.
    """

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    REQUIRED_COLUMNS = frozenset({"title"})
    #: Optional columns accepted by :class:`CatalogItemCreate`.
    SCHEMA_COLUMNS = frozenset(
        {
            "subtitle", "description", "manufacturer", "publisher",
            "developer", "brand", "language", "region", "rarity",
        }
    )
    #: Optional columns that exist on the model but not on the schema.
    MODEL_COLUMNS = frozenset({"sku", "upc"})
    OPTIONAL_COLUMNS = SCHEMA_COLUMNS | MODEL_COLUMNS

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def import_catalog_items(
        self, catalog_id: str, file_content: bytes, filename: str
    ) -> BatchImportResult:
        """Create catalog items from the rows of a CSV file.

        Args:
            catalog_id: UUID of the catalog receiving the items.
            file_content: Raw bytes of the uploaded CSV file.
            filename: Original file name, used in error messages.

        Returns:
            A summary with the number of created items and per-row errors.

        Raises:
            NotFoundError: If the catalog does not exist.
            ValidationError: If the file is too large, is not UTF-8, lacks
                the ``title`` column, or has no data rows.
        """
        self._validate_size(file_content, filename)
        catalog = await self._get_catalog(catalog_id)
        rows = self._parse_rows(file_content, filename)

        items, errors = self._build_items(catalog_id, rows)
        await self._persist(catalog, items)

        return BatchImportResult(
            created_count=len(items),
            error_count=len(errors),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # File level validation
    # ------------------------------------------------------------------

    def _validate_size(self, file_content: bytes, filename: str) -> None:
        """Raise ValidationError if the file exceeds MAX_FILE_SIZE."""
        if len(file_content) > self.MAX_FILE_SIZE:
            limit_mb = self.MAX_FILE_SIZE // (1024 * 1024)
            raise ValidationError(
                f"File '{filename}' exceeds the maximum size of {limit_mb} MB"
            )

    def _decode(self, file_content: bytes, filename: str) -> str:
        """Decode the file as UTF-8, raising ValidationError otherwise."""
        try:
            return file_content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValidationError(
                f"File '{filename}' is not valid UTF-8 encoded text"
            ) from exc

    def _parse_rows(
        self, file_content: bytes, filename: str
    ) -> list[tuple[int, dict[str, str | None]]]:
        """Return the data rows of the CSV file with their line numbers.

        Raises:
            ValidationError: If the header lacks required columns or the
                file contains no data rows.
        """
        reader = csv.DictReader(StringIO(self._decode(file_content, filename)))
        self._validate_headers(reader.fieldnames, filename)

        rows = [(reader.line_num, row) for row in reader]
        if not rows:
            raise ValidationError(f"File '{filename}' contains no data rows")
        return rows

    def _validate_headers(
        self, fieldnames: list[str] | None, filename: str
    ) -> None:
        """Raise ValidationError if a required column is absent."""
        headers = {(name or "").strip().lower() for name in fieldnames or []}
        missing = self.REQUIRED_COLUMNS - headers
        if missing:
            raise ValidationError(
                f"File '{filename}' is missing required "
                f"column(s): {', '.join(sorted(missing))}"
            )

    # ------------------------------------------------------------------
    # Row level processing
    # ------------------------------------------------------------------

    def _build_items(
        self, catalog_id: str, rows: list[tuple[int, dict[str, str | None]]]
    ) -> tuple[list[CatalogItem], list[BatchImportError]]:
        """Split rows into ready-to-insert items and per-row errors."""
        items: list[CatalogItem] = []
        errors: list[BatchImportError] = []

        for line, row in rows:
            try:
                items.append(self._build_item(catalog_id, row))
            except SchemaValidationError as exc:
                errors.append(
                    BatchImportError(row=line, message=self._format(exc))
                )

        return items, errors

    def _build_item(
        self, catalog_id: str, row: dict[str, str | None]
    ) -> CatalogItem:
        """Validate a single row and turn it into a CatalogItem.

        Raises:
            pydantic.ValidationError: If the row fails schema validation.
        """
        values = self._recognized_values(row)
        extra = {
            key: values.pop(key)
            for key in self.MODEL_COLUMNS & values.keys()
        }
        data = CatalogItemCreate(catalog_id=catalog_id, **values)
        return CatalogItem(**data.model_dump(), **extra)

    def _recognized_values(self, row: dict[str, str | None]) -> dict[str, str]:
        """Keep only known, non-empty columns, normalizing their names."""
        allowed = self.REQUIRED_COLUMNS | self.OPTIONAL_COLUMNS
        values: dict[str, str] = {}
        for name, value in row.items():
            key = (name or "").strip().lower()
            if key in allowed and (value or "").strip():
                values[key] = value.strip()  # type: ignore[union-attr]
        return values

    @staticmethod
    def _format(exc: SchemaValidationError) -> str:
        """Render a schema validation error as a single readable line."""
        return "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'row'}: "
            f"{error['msg']}"
            for error in exc.errors()
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    async def _get_catalog(self, catalog_id: str) -> Catalog:
        """Return the target catalog, or raise NotFoundError."""
        catalog = await self._db.get(Catalog, catalog_id)
        if catalog is None:
            raise NotFoundError(f"Catalog '{catalog_id}' not found")
        return catalog

    async def _persist(
        self, catalog: Catalog, items: list[CatalogItem]
    ) -> None:
        """Insert the items and bump the catalog counter in one transaction."""
        if not items:
            return
        self._db.add_all(items)
        catalog.total_items = (catalog.total_items or 0) + len(items)
        await self._db.commit()
