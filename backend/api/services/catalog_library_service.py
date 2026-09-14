"""Official catalog library: list the manifest and load a catalog by id.

To keep the app fully offline (no outbound HTTP, no SSRF surface), the library
is read from a local directory (``CATALOG_LIBRARY_DIR``) that ships with the
repo/image and contains ``manifest.json`` plus one file per catalog. Loading a
catalog validates its checksum against the manifest, then applies it through
CatalogImportService (idempotent create/update/skip).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from api.schemas.csv_import import BatchImportResult
from api.schemas.import_data import ImportPreview
from api.services.catalog_import_service import CatalogImportService
from core.exceptions import NotFoundError, ValidationError

MANIFEST_NAME = "manifest.json"


class CatalogLibraryService:
    """Reads the local catalog library and loads catalogs into the DB."""

    def __init__(
        self, import_service: CatalogImportService, library_dir: str
    ) -> None:
        self._import = import_service
        self._dir = Path(library_dir)

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------

    def read_manifest(self) -> dict:
        """Return the parsed manifest, or an empty manifest when absent."""
        path = self._dir / MANIFEST_NAME
        if not path.is_file():
            return {"schema_version": "1.0", "catalogs": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Invalid catalog manifest: {exc}") from exc
        if not isinstance(data, dict) or "catalogs" not in data:
            raise ValidationError("Catalog manifest is malformed")
        return data

    def _find_entry(self, catalog_id: str) -> dict:
        manifest = self.read_manifest()
        for entry in manifest.get("catalogs", []):
            if entry.get("id") == catalog_id:
                return entry
        raise NotFoundError(
            f"Catalog '{catalog_id}' is not in the library manifest"
        )

    def _read_catalog_bytes(self, entry: dict) -> bytes:
        rel = entry.get("path")
        if not rel:
            raise ValidationError(
                f"Manifest entry '{entry.get('id')}' has no path"
            )
        # Prevent path traversal outside the library dir.
        candidate = (self._dir / rel).resolve()
        if not str(candidate).startswith(str(self._dir.resolve())):
            raise ValidationError("Catalog path escapes the library directory")
        if not candidate.is_file():
            raise NotFoundError(f"Catalog file '{rel}' not found")
        content = candidate.read_bytes()

        expected = entry.get("checksum")
        if expected:
            digest = "sha256:" + hashlib.sha256(content).hexdigest()
            if digest != expected:
                raise ValidationError(
                    f"Checksum mismatch for '{entry.get('id')}': "
                    f"expected {expected}, got {digest}"
                )
        return content

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    async def preview(self, catalog_id: str) -> ImportPreview:
        entry = self._find_entry(catalog_id)
        content = self._read_catalog_bytes(entry)
        return await self._import.preview(content)

    async def load(self, catalog_id: str) -> BatchImportResult:
        entry = self._find_entry(catalog_id)
        content = self._read_catalog_bytes(entry)
        # Catalogs from the official library are marked official.
        return await self._import.execute(content, is_official=True)
