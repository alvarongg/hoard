"""REST endpoints for the official catalog library and catalog file import."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from api.dependencies import (
    get_catalog_import_service,
    get_catalog_library_service,
)
from api.schemas.csv_import import BatchImportResult
from api.schemas.import_data import ImportPreview
from api.services.catalog_import_service import (
    MAX_FILE_SIZE,
    CatalogImportService,
)
from api.services.catalog_library_service import CatalogLibraryService

router = APIRouter(prefix="/catalog-library", tags=["catalog-library"])
import_router = APIRouter(prefix="/catalog-import", tags=["catalog-import"])


class LoadCatalogRequest(BaseModel):
    catalog_id: str


@router.get("/manifest")
async def get_manifest(
    service: CatalogLibraryService = Depends(get_catalog_library_service),
) -> dict:
    """List the official catalogs available in the local library."""
    return service.read_manifest()


@router.post("/preview", response_model=ImportPreview)
async def preview_official(
    body: LoadCatalogRequest,
    service: CatalogLibraryService = Depends(get_catalog_library_service),
) -> ImportPreview:
    """Dry-run loading an official catalog by id."""
    return await service.preview(body.catalog_id)


@router.post("/load", response_model=BatchImportResult)
async def load_official(
    body: LoadCatalogRequest,
    service: CatalogLibraryService = Depends(get_catalog_library_service),
) -> BatchImportResult:
    """Load an official catalog from the library into the database."""
    return await service.load(body.catalog_id)


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")
    return content


@import_router.post("/preview", response_model=ImportPreview)
async def import_catalog_preview(
    file: UploadFile,
    service: CatalogImportService = Depends(get_catalog_import_service),
) -> ImportPreview:
    """Dry-run importing a catalog file (entity_type='catalog')."""
    content = await _read_upload(file)
    return await service.preview(content)


@import_router.post("/execute", response_model=BatchImportResult)
async def import_catalog_execute(
    file: UploadFile,
    service: CatalogImportService = Depends(get_catalog_import_service),
) -> BatchImportResult:
    """Import a catalog file. Not marked official (external source)."""
    content = await _read_upload(file)
    return await service.execute(content, is_official=False)
