"""Business logic for accessories stock and item assignments."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.accessory import AccessoryStock, ItemAccessory
from api.models.collection import CollectionItem
from api.schemas.accessory import AccessoryCreate, AccessoryUpdate
from core.dialect import supports_generated_columns
from core.exceptions import DuplicateError, NotFoundError, ValidationError
from utils.computations import available_stock


class AccessoryService:
    """CRUD + assignment logic for accessories, with stock invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def list(
        self, *, category: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[AccessoryStock]:
        query = select(AccessoryStock)
        if category is not None:
            query = query.where(AccessoryStock.category == category)
        query = query.order_by(AccessoryStock.name).offset(skip).limit(limit)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def get(self, accessory_id: str) -> AccessoryStock:
        acc = await self._db.get(AccessoryStock, accessory_id)
        if acc is None:
            raise NotFoundError(f"Accessory '{accessory_id}' not found")
        return acc

    async def create(self, data: AccessoryCreate) -> AccessoryStock:
        acc = AccessoryStock(**data.model_dump())
        self._db.add(acc)
        await self._db.commit()
        await self._db.refresh(acc)
        return acc

    async def update(
        self, accessory_id: str, data: AccessoryUpdate
    ) -> AccessoryStock:
        acc = await self.get(accessory_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(acc, field, value)
        await self._db.commit()
        await self._db.refresh(acc)
        return acc

    async def delete(self, accessory_id: str) -> None:
        """Delete an accessory that has no active assignments.

        Raises:
            NotFoundError: If the accessory does not exist.
            DuplicateError: If it still has assignments (409).
        """
        acc = await self.get(accessory_id)
        count = (
            await self._db.execute(
                select(func.count())
                .select_from(ItemAccessory)
                .where(ItemAccessory.accessory_id == accessory_id)
            )
        ).scalar() or 0
        if count > 0:
            raise DuplicateError(
                f"Cannot delete accessory '{accessory_id}': "
                f"it has {count} active assignment(s)"
            )
        await self._db.delete(acc)
        await self._db.commit()

    async def list_low_stock(self) -> list[AccessoryStock]:
        """Return accessories at or below their minimum-stock threshold."""
        result = await self._db.execute(select(AccessoryStock))
        accessories = list(result.scalars().all())
        return [
            a
            for a in accessories
            if self._available(a) <= a.minimum_stock_alert
        ]

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------

    async def list_assignments(
        self, collection_item_id: str
    ) -> list[ItemAccessory]:
        await self._ensure_collection_item(collection_item_id)
        result = await self._db.execute(
            select(ItemAccessory).where(
                ItemAccessory.collection_item_id == collection_item_id
            )
        )
        return list(result.scalars().all())

    async def assign(
        self,
        collection_item_id: str,
        accessory_id: str,
        quantity_used: int,
        notes: str | None = None,
    ) -> ItemAccessory:
        """Assign an accessory to a collection item.

        Validates stock and uniqueness BEFORE the insert on both dialects.

        Raises:
            NotFoundError: If the item or accessory does not exist.
            ValidationError: If quantity exceeds available stock.
            DuplicateError: If already assigned to this item.
        """
        await self._ensure_collection_item(collection_item_id)
        acc = await self.get(accessory_id)

        existing = (
            await self._db.execute(
                select(ItemAccessory)
                .where(ItemAccessory.collection_item_id == collection_item_id)
                .where(ItemAccessory.accessory_id == accessory_id)
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise DuplicateError(
                "This accessory is already assigned to the item"
            )

        available = self._available(acc)
        if quantity_used > available:
            raise ValidationError(
                f"Requested {quantity_used} exceeds available stock {available}"
            )

        assignment = ItemAccessory(
            collection_item_id=collection_item_id,
            accessory_id=accessory_id,
            quantity_used=quantity_used,
            notes=notes,
        )
        self._db.add(assignment)

        # On PostgreSQL a trigger keeps quantity_in_use; on SQLite adjust here.
        if not supports_generated_columns(self._db):
            acc.quantity_in_use = acc.quantity_in_use + quantity_used

        await self._db.commit()
        await self._db.refresh(assignment)
        return assignment

    async def unassign(self, item_accessory_id: str) -> None:
        """Remove an assignment and restore stock (SQLite).

        Raises:
            NotFoundError: If the assignment does not exist.
        """
        assignment = await self._db.get(ItemAccessory, item_accessory_id)
        if assignment is None:
            raise NotFoundError(
                f"Assignment '{item_accessory_id}' not found"
            )
        if not supports_generated_columns(self._db):
            acc = await self._db.get(AccessoryStock, assignment.accessory_id)
            if acc is not None:
                acc.quantity_in_use = max(
                    0, acc.quantity_in_use - assignment.quantity_used
                )
        await self._db.delete(assignment)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _available(self, acc: AccessoryStock) -> int:
        """Read the GENERATED column on PostgreSQL, compute on SQLite."""
        if supports_generated_columns(self._db) and acc.quantity_available is not None:
            return acc.quantity_available
        return available_stock(acc.quantity_total, acc.quantity_in_use)

    async def _ensure_collection_item(self, collection_item_id: str) -> None:
        item = await self._db.get(CollectionItem, collection_item_id)
        if item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )
