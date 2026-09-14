"""Official catalog library: list the manifest and load a catalog by id.

Two sources are supported:

* **Local** (default): read ``manifest.json`` + one file per catalog from a
  directory (``CATALOG_LIBRARY_DIR``) that ships with the repo/image.
* **Remote**: when ``CATALOG_LIBRARY_URL`` is set, fetch the manifest and each
  catalog file over HTTPS from that base URL (e.g. a repo's raw.githubusercontent
  path). An allowlist of hosts (``CATALOG_LIBRARY_ALLOWED_HOSTS``) is enforced to
  avoid SSRF, only https:// is allowed, and every downloaded file is validated
  against the checksum declared in the manifest.

Loading applies the catalog through CatalogImportService (idempotent
create/update/skip) and marks it official.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Protocol

from api.schemas.csv_import import BatchImportResult
from api.schemas.import_data import ImportPreview
from api.services.catalog_import_service import CatalogImportService
from core.exceptions import NotFoundError, ToolUnavailableError, ValidationError

MANIFEST_NAME = "manifest.json"
_HTTP_TIMEOUT = 30
_MAX_DOWNLOAD = 10 * 1024 * 1024  # 10 MB per file


class CatalogSource(Protocol):
    """A place the library can be read from."""

    kind: str

    def describe(self) -> str: ...

    def read_manifest(self) -> dict: ...

    def read_catalog(self, path: str) -> bytes: ...


class LocalCatalogSource:
    """Reads the library from a local directory."""

    kind = "local"

    def __init__(self, library_dir: str) -> None:
        self._dir = Path(library_dir)

    def describe(self) -> str:
        return str(self._dir)

    def read_manifest(self) -> dict:
        path = self._dir / MANIFEST_NAME
        if not path.is_file():
            return {"schema_version": "1.0", "catalogs": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Invalid catalog manifest: {exc}") from exc

    def read_catalog(self, path: str) -> bytes:
        candidate = (self._dir / path).resolve()
        if not str(candidate).startswith(str(self._dir.resolve())):
            raise ValidationError("Catalog path escapes the library directory")
        if not candidate.is_file():
            raise NotFoundError(f"Catalog file '{path}' not found")
        return candidate.read_bytes()


class RemoteCatalogSource:
    """Fetches the library over HTTPS from a base URL, with an SSRF allowlist."""

    kind = "remote"

    def __init__(self, base_url: str, allowed_hosts: list[str]) -> None:
        self._base = base_url.rstrip("/")
        self._allowed = {h.strip().lower() for h in allowed_hosts if h.strip()}

    def describe(self) -> str:
        return self._base

    def _build_url(self, rel: str) -> str:
        url = f"{self._base}/{rel.lstrip('/')}"
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            raise ValidationError(
                "Catalog library URL must use https"
            )
        host = (parsed.hostname or "").lower()
        if host not in self._allowed:
            raise ValidationError(
                f"Host '{host}' is not in the catalog library allowlist"
            )
        return url

    def _fetch(self, rel: str) -> bytes:
        url = self._build_url(rel)
        req = urllib.request.Request(
            url, headers={"User-Agent": "HoardCatalogLibrary/1.0"}
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - scheme/host checked
                req, timeout=_HTTP_TIMEOUT
            ) as resp:
                data = resp.read(_MAX_DOWNLOAD + 1)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise NotFoundError(f"'{rel}' not found at library URL") from exc
            raise ToolUnavailableError(
                f"Failed to fetch '{rel}': HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ToolUnavailableError(
                f"Could not reach catalog library: {exc.reason}"
            ) from exc
        if len(data) > _MAX_DOWNLOAD:
            raise ValidationError(f"'{rel}' exceeds the 10 MB limit")
        return data

    def read_manifest(self) -> dict:
        try:
            return json.loads(self._fetch(MANIFEST_NAME).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Invalid remote manifest: {exc}") from exc

    def read_catalog(self, path: str) -> bytes:
        return self._fetch(path)


class CatalogLibraryService:
    """Lists the catalog library and loads catalogs into the DB."""

    def __init__(
        self, import_service: CatalogImportService, source: CatalogSource
    ) -> None:
        self._import = import_service
        self._source = source

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------

    def read_manifest(self) -> dict:
        data = self._source.read_manifest()
        if not isinstance(data, dict) or "catalogs" not in data:
            raise ValidationError("Catalog manifest is malformed")
        data["source"] = {
            "kind": self._source.kind,
            "location": self._source.describe(),
        }
        return data

    def _find_entry(self, catalog_id: str) -> dict:
        for entry in self.read_manifest().get("catalogs", []):
            if entry.get("id") == catalog_id:
                return entry
        raise NotFoundError(
            f"Catalog '{catalog_id}' is not in the library manifest"
        )

    def _load_bytes(self, entry: dict) -> bytes:
        rel = entry.get("path")
        if not rel:
            raise ValidationError(
                f"Manifest entry '{entry.get('id')}' has no path"
            )
        content = self._source.read_catalog(rel)

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
        content = self._load_bytes(self._find_entry(catalog_id))
        return await self._import.preview(content)

    async def load(self, catalog_id: str) -> BatchImportResult:
        content = self._load_bytes(self._find_entry(catalog_id))
        return await self._import.execute(content, is_official=True)
