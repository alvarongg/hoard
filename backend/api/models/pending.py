"""SQLAlchemy model for pending data-completion tasks.

When an entity (collection item, catalog, catalog item, supplier) is created
via a quick-add flow with only minimal data, a PendingCompletion is opened so
the collector can fill in the missing fields later from a "Pending" tab.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from api.models.base import DBUUID, Base, UUIDMixin

# Valid entity types a pending record can point at.
ENTITY_TYPES = (
    "collection_item",
    "catalog",
    "catalog_item",
    "supplier",
)
STATUS_OPEN = "open"
STATUS_RESOLVED = "resolved"


class PendingCompletion(UUIDMixin, Base):
    """A record of missing fields on some entity, to complete later."""

    __tablename__ = "pending_completions"

    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[str] = mapped_column(DBUUID(), nullable=False)
    missing_fields: Mapped[list] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=STATUS_OPEN,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<PendingCompletion(id={self.id!r}, "
            f"entity_type={self.entity_type!r}, status={self.status!r})>"
        )
