"""REST endpoints for JSON import (preview + execute)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from api.dependencies import get_json_import_service
from api.schemas.csv_import import BatchImportResult
from api.schemas.import_data import ImportPreview
from api.services.json_import_service import MAX_FILE_SIZE, JsonImportService

router = APIRouter(prefix="/import", tags=["import"])


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")
    return content


@router.post("/preview", response_model=ImportPreview)
async def import_preview(
    file: UploadFile,
    service: JsonImportService = Depends(get_json_import_service),
) -> ImportPreview:
    """Dry-run: report the planned changes without writing anything."""
    content = await _read_upload(file)
    return await service.preview(content)


@router.post("/execute", response_model=BatchImportResult)
async def import_execute(
    file: UploadFile,
    service: JsonImportService = Depends(get_json_import_service),
) -> BatchImportResult:
    """Apply the import and return the create/update/skip counts."""
    content = await _read_upload(file)
    return await service.execute(content)
