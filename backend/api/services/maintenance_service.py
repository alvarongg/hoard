"""Business logic for collection-item maintenance schedules."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.collection import CollectionItem
from api.models.maintenance import MaintenanceSchedule
from api.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from core.exceptions import NotFoundError


class MaintenanceService:
    """CRUD + due listing for maintenance schedules."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_item(
        self, collection_item_id: str
    ) -> list[MaintenanceSchedule]:
        await self._get_item(collection_item_id)
        result = await self._db.execute(
            select(MaintenanceSchedule)
            .where(
                MaintenanceSchedule.collection_item_id == collection_item_id
            )
            .order_by(MaintenanceSchedule.due_date)
        )
        return list(result.scalars().all())

    async def create(
        self, collection_item_id: str, data: MaintenanceCreate
    ) -> MaintenanceSchedule:
        await self._get_item(collection_item_id)
        sched = MaintenanceSchedule(
            collection_item_id=collection_item_id, **data.model_dump()
        )
        self._db.add(sched)
        await self._db.commit()
        await self._db.refresh(sched)
        return sched

    async def update(
        self, schedule_id: str, data: MaintenanceUpdate
    ) -> MaintenanceSchedule:
        sched = await self._db.get(MaintenanceSchedule, schedule_id)
        if sched is None:
            raise NotFoundError(f"Maintenance '{schedule_id}' not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(sched, field, value)
        await self._db.commit()
        await self._db.refresh(sched)
        return sched

    async def delete(self, schedule_id: str) -> None:
        sched = await self._db.get(MaintenanceSchedule, schedule_id)
        if sched is None:
            raise NotFoundError(f"Maintenance '{schedule_id}' not found")
        await self._db.delete(sched)
        await self._db.commit()

    async def list_due(
        self, before: date | None = None
    ) -> list[MaintenanceSchedule]:
        """List pending (not done) reviews, optionally due on/before a date."""
        stmt = select(MaintenanceSchedule).where(
            MaintenanceSchedule.is_done.is_(False)
        )
        if before is not None:
            stmt = stmt.where(MaintenanceSchedule.due_date <= before)
        stmt = stmt.order_by(MaintenanceSchedule.due_date)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _get_item(self, collection_item_id: str) -> CollectionItem:
        item = await self._db.get(CollectionItem, collection_item_id)
        if item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )
        return item
