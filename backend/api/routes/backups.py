"""REST endpoints for backups and their configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse

from api.dependencies import get_backup_service
from api.schemas.backup import (
    BackupConfig,
    BackupConfigUpdate,
    BackupInfo,
    RestoreResult,
)
from api.services.backup_service import BackupService

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("", response_model=list[BackupInfo])
async def list_backups(
    service: BackupService = Depends(get_backup_service),
) -> list[BackupInfo]:
    """List stored backups, newest first."""
    return service.list()


@router.post("", response_model=BackupInfo, status_code=201)
async def create_backup(
    service: BackupService = Depends(get_backup_service),
) -> BackupInfo:
    """Create a backup (503 if pg_dump is unavailable)."""
    return await service.create(trigger="manual")


@router.get("/config", response_model=BackupConfig)
async def get_backup_config(
    service: BackupService = Depends(get_backup_service),
) -> BackupConfig:
    """Read the backup scheduler configuration."""
    return await service.get_config()


@router.put("/config", response_model=BackupConfig)
async def update_backup_config(
    data: BackupConfigUpdate,
    service: BackupService = Depends(get_backup_service),
) -> BackupConfig:
    """Update the backup scheduler configuration."""
    return await service.update_config(data)


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: str,
    service: BackupService = Depends(get_backup_service),
) -> FileResponse:
    """Download a backup archive."""
    path = service.get_path(backup_id)
    return FileResponse(
        path,
        media_type="application/gzip",
        filename=backup_id,
    )


@router.post("/{backup_id}/restore", response_model=RestoreResult)
async def restore_backup(
    backup_id: str,
    service: BackupService = Depends(get_backup_service),
) -> RestoreResult:
    """Restore from a backup (verifies before touching data)."""
    return service.restore(backup_id)


@router.delete("/{backup_id}", status_code=204, response_class=Response)
async def delete_backup(
    backup_id: str,
    service: BackupService = Depends(get_backup_service),
) -> None:
    """Delete a backup archive."""
    service.delete(backup_id)
