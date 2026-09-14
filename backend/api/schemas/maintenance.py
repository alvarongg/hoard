"""Pydantic schemas for maintenance schedules."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


class MaintenanceCreate(BaseModel):
    """Schedule a maintenance review for a collection item."""

    maintenance_type: str = Field(..., min_length=1, max_length=50)
    due_date: date = Field(..., description="When the review is due")
    notes: str | None = Field(None, description="Optional notes")


class MaintenanceUpdate(BaseModel):
    """Update a maintenance schedule (e.g. mark done, reschedule)."""

    maintenance_type: str | None = Field(None, max_length=50)
    due_date: date | None = None
    notes: str | None = None
    is_done: bool | None = None
    done_date: date | None = None
    done_notes: str | None = None


class MaintenanceResponse(BaseModel):
    id: StrUUID
    collection_item_id: StrUUID
    maintenance_type: str
    due_date: date
    notes: str | None = None
    is_done: bool
    done_date: date | None = None
    done_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
