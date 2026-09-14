"""Pydantic v2 schemas for backups and their configuration."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BackupFrequency = Literal["daily", "weekly", "monthly"]
BackupTrigger = Literal["manual", "scheduled"]


class BackupInfo(BaseModel):
    """Metadata for a stored backup archive."""

    id: str
    filename: str
    created_at: datetime
    size_bytes: int
    trigger: str


class BackupConfig(BaseModel):
    """Scheduler configuration for automatic backups."""

    frequency: BackupFrequency = "weekly"
    retention_count: int = Field(7, ge=1, le=365)
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_run_status: str | None = None


class BackupConfigUpdate(BaseModel):
    """Partial update of backup configuration."""

    frequency: BackupFrequency | None = None
    retention_count: int | None = Field(None, ge=1, le=365)


class RestoreResult(BaseModel):
    """Outcome of a restore operation."""

    restored: bool
    filename: str
    message: str | None = None


class BackupVerification(BaseModel):
    """Result of verifying a backup archive."""

    valid: bool
    reason: str | None = None
