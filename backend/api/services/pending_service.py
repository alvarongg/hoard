"""Business logic for pending data-completion tasks."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.pending import (
    ENTITY_TYPES,
    STATUS_OPEN,
    STATUS_RESOLVED,
    PendingCompletion,
)
from core.exceptions import NotFoundError, ValidationError


class PendingService:
    """Creates, lists and resolves PendingCompletion records."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def open(
        self,
        entity_type: str,
        entity_id: str,
        missing_fields: list[str],
        *,
        commit: bool = True,
    ) -> PendingCompletion | None:
        """Open a pending record for an entity's missing fields.

        No-op (returns None) when missing_fields is empty. When called as
        part of a larger transaction, pass commit=False.
        """
        if entity_type not in ENTITY_TYPES:
            raise ValidationError(f"Unknown entity_type '{entity_type}'")
        if not missing_fields:
            return None
        pending = PendingCompletion(
            entity_type=entity_type,
            entity_id=entity_id,
            missing_fields=list(missing_fields),
            status=STATUS_OPEN,
        )
        self._db.add(pending)
        if commit:
            await self._db.commit()
            await self._db.refresh(pending)
        else:
            await self._db.flush()
        return pending

    async def list(
        self, status: str = STATUS_OPEN, entity_type: str | None = None
    ) -> list[PendingCompletion]:
        stmt = select(PendingCompletion).where(
            PendingCompletion.status == status
        )
        if entity_type is not None:
            stmt = stmt.where(PendingCompletion.entity_type == entity_type)
        stmt = stmt.order_by(PendingCompletion.created_at.desc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def resolve(
        self, pending_id: str, completed_fields: list[str]
    ) -> PendingCompletion:
        """Remove completed fields; auto-close when none remain."""
        pending = await self._db.get(PendingCompletion, pending_id)
        if pending is None:
            raise NotFoundError(f"Pending '{pending_id}' not found")
        remaining = [
            f for f in pending.missing_fields if f not in set(completed_fields)
        ]
        pending.missing_fields = remaining
        if not remaining:
            pending.status = STATUS_RESOLVED
            pending.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self._db.commit()
        await self._db.refresh(pending)
        return pending
