"""Pydantic v2 schemas for JSON import preview and execution."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImportEntityChange(BaseModel):
    """A single planned change for one entity."""

    entity_type: str
    identifier: str
    action: str  # create | update | skip
    reason: str | None = None


class ImportError(BaseModel):
    """An entity that could not be planned."""

    entity_type: str
    identifier: str
    message: str


class ImportPreview(BaseModel):
    """The dry-run plan of a JSON import."""

    schema_version: str
    to_create: int = Field(0, ge=0)
    to_update: int = Field(0, ge=0)
    to_skip: int = Field(0, ge=0)
    changes: list[ImportEntityChange] = Field(default_factory=list)
    errors: list[ImportError] = Field(default_factory=list)
