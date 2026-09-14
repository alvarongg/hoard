"""REST endpoints for catalogs and catalog items."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile

from api.dependencies import get_catalog_service, get_csv_import_service
from api.schemas.catalog import (
    CatalogCreate,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogItemUpdate,
    CatalogResponse,
    CatalogUpdate,
)
from api.schemas.csv_import import BatchImportResult
from api.services.catalog_service import CatalogService
from api.services.csv_import_service import CsvImportService

router = APIRouter(prefix="/catalogs", tags=["catalogs"])

#: MIME types accepted for CSV uploads (browsers and Excel differ).
ALLOWED_CSV_TYPES = frozenset(
    {"text/csv", "application/vnd.ms-excel"}
)


# ------------------------------------------------------------------
# Catalogs
# ------------------------------------------------------------------


@router.get("", response_model=list[CatalogResponse])
async def list_catalogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CatalogService = Depends(get_catalog_service),
) -> list[CatalogResponse]:
    """List all catalogs with pagination."""
    return await service.list_catalogs(skip=skip, limit=limit)


@router.post("", response_model=CatalogResponse, status_code=201)
async def create_catalog(
    data: CatalogCreate,
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogResponse:
    """Create a new catalog."""
    return await service.create_catalog(data)


@router.get("/{catalog_id}", response_model=CatalogResponse)
async def get_catalog(
    catalog_id: str,
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogResponse:
    """Get a single catalog by id."""
    return await service.get_catalog(catalog_id)


@router.put("/{catalog_id}", response_model=CatalogResponse)
async def update_catalog(
    catalog_id: str,
    data: CatalogUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogResponse:
    """Update a catalog."""
    return await service.update_catalog(catalog_id, data)


@router.delete("/{catalog_id}", status_code=204, response_class=Response)
async def delete_catalog(
    catalog_id: str,
    service: CatalogService = Depends(get_catalog_service),
) -> None:
    """Delete a catalog."""
    await service.delete_catalog(catalog_id)


# ------------------------------------------------------------------
# Catalog items (nested under catalog)
# ------------------------------------------------------------------


@router.get("/{catalog_id}/items", response_model=list[CatalogItemResponse])
async def list_catalog_items(
    catalog_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CatalogService = Depends(get_catalog_service),
) -> list[CatalogItemResponse]:
    """List items for a catalog with pagination."""
    return await service.list_items(catalog_id, skip=skip, limit=limit)


@router.post(
    "/{catalog_id}/items",
    response_model=CatalogItemResponse,
    status_code=201,
)
async def create_catalog_item(
    catalog_id: str,
    data: CatalogItemCreate,
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogItemResponse:
    """Create a new item in a catalog."""
    return await service.create_item(catalog_id, data)


def _validate_csv_content_type(file: UploadFile) -> None:
    """Reject uploads whose declared MIME type is not a CSV type.

    Raises:
        HTTPException: 422 if the content type is not accepted.
    """
    media_type = (file.content_type or "").split(";")[0].strip().lower()
    if media_type not in ALLOWED_CSV_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Content type '{file.content_type}' is not allowed. "
                f"Allowed types: {', '.join(sorted(ALLOWED_CSV_TYPES))}"
            ),
        )


def _validate_csv_size(content: bytes, filename: str) -> None:
    """Reject uploads larger than the import service limit.

    Raises:
        HTTPException: 413 if the file exceeds the maximum size.
    """
    if len(content) > CsvImportService.MAX_FILE_SIZE:
        limit_mb = CsvImportService.MAX_FILE_SIZE // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"File '{filename}' exceeds the maximum "
                f"size of {limit_mb} MB"
            ),
        )


@router.post("/{catalog_id}/import-csv", response_model=BatchImportResult)
async def import_catalog_items_csv(
    catalog_id: str,
    file: UploadFile,
    service: CsvImportService = Depends(get_csv_import_service),
) -> BatchImportResult:
    """Import catalog items from an uploaded CSV file."""
    _validate_csv_content_type(file)
    content = await file.read()
    filename = file.filename or "upload.csv"
    _validate_csv_size(content, filename)
    return await service.import_catalog_items(catalog_id, content, filename)


# ------------------------------------------------------------------
# Catalog items (standalone endpoints)
# ------------------------------------------------------------------

catalog_items_router = APIRouter(
    prefix="/catalog-items", tags=["catalog-items"]
)


@catalog_items_router.get("/search", response_model=list[CatalogItemResponse])
async def search_catalog_items(
    q: str = Query("", description="Search query for item titles"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CatalogService = Depends(get_catalog_service),
) -> list[CatalogItemResponse]:
    """Search catalog items by title."""
    return await service.search_items(q, skip=skip, limit=limit)


@catalog_items_router.get("/{item_id}", response_model=CatalogItemResponse)
async def get_catalog_item(
    item_id: str,
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogItemResponse:
    """Get a single catalog item by id."""
    return await service.get_item(item_id)


@catalog_items_router.put("/{item_id}", response_model=CatalogItemResponse)
async def update_catalog_item(
    item_id: str,
    data: CatalogItemUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogItemResponse:
    """Update a catalog item."""
    return await service.update_item(item_id, data)


@catalog_items_router.delete(
    "/{item_id}", status_code=204, response_class=Response
)
async def delete_catalog_item(
    item_id: str,
    service: CatalogService = Depends(get_catalog_service),
) -> None:
    """Delete a catalog item."""
    await service.delete_item(item_id)
