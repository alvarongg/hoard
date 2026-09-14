"""Pydantic schemas for pending data-completion tasks."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


class PendingResponse(BaseModel):
    """A pending completion record."""

    id: StrUUID
    entity_type: str
    entity_id: StrUUID
    missing_fields: list[str]
    status: str
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PendingResolve(BaseModel):
    """Payload to resolve a pending: fields now completed."""

    completed_fields: list[str] = Field(
        default_factory=list,
        description="Field names that have now been filled in",
    )
