"""Business logic for collections."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.category import SubCategory
from api.models.collection import Collection
from api.schemas.collection import CollectionCreate, CollectionUpdate
from core.exceptions import DuplicateError, NotFoundError, ValidationError


class CollectionService:
    """Handles CRUD operations and business rules for collections."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self, skip: int = 0, limit: int = 100
    ) -> list[Collection]:
        """Return active collections ordered by name, with pagination."""
        result = await self._db.execute(
            select(Collection)
            .where(Collection.is_active.is_(True))
            .order_by(Collection.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, collection_id: str) -> Collection:
        """Return a single collection by id.

        Raises:
            NotFoundError: If the collection does not exist.
        """
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            raise NotFoundError(f"Collection '{collection_id}' not found")
        return collection

    async def create(self, data: CollectionCreate) -> Collection:
        """Create a new collection.

        Raises:
            DuplicateError: If an active collection with the same name exists.
            ValidationError: If single_category and the sub-category does not exist.
        """
        await self._check_name_unique(data.name)

        if data.collection_type == "single_category":
            sub_cat = await self._db.get(
                SubCategory, data.restricted_to_sub_category_id
            )
            if sub_cat is None:
                raise ValidationError(
                    f"Sub-category '{data.restricted_to_sub_category_id}' does not exist"
                )

        collection = Collection(**data.model_dump())
        self._db.add(collection)
        await self._db.commit()
        await self._db.refresh(collection)
        return collection

    async def update(
        self, collection_id: str, data: CollectionUpdate
    ) -> Collection:
        """Partially update a collection.

        Raises:
            NotFoundError: If the collection does not exist.
            DuplicateError: If the new name conflicts with another active collection.
        """
        collection = await self.get_by_id(collection_id)
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != collection.name:
            await self._check_name_unique(
                update_data["name"], exclude_id=collection_id
            )

        for field, value in update_data.items():
            setattr(collection, field, value)

        await self._db.commit()
        await self._db.refresh(collection)
        return collection

    async def delete(self, collection_id: str) -> None:
        """Delete a collection (hard delete, cascade handles items).

        Raises:
            NotFoundError: If the collection does not exist.
        """
        collection = await self.get_by_id(collection_id)
        await self._db.delete(collection)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _check_name_unique(
        self, name: str, *, exclude_id: str | None = None
    ) -> None:
        """Raise DuplicateError if an active collection with this name exists."""
        query = select(Collection).where(
            Collection.name == name,
            Collection.is_active.is_(True),
        )
        if exclude_id is not None:
            query = query.where(Collection.id != exclude_id)

        result = await self._db.execute(query)
        if result.scalar_one_or_none() is not None:
            raise DuplicateError(
                f"An active collection named '{name}' already exists"
            )
