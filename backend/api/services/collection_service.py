"""Business logic for collections."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.category import SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.collection import CollectionCreate, CollectionUpdate
from core.exceptions import DuplicateError, NotFoundError, ValidationError


class CollectionService:
    """Handles CRUD operations and business rules for collections."""

    VALID_TYPES: frozenset[str] = frozenset({
        "single_category", "multi_category", "mixed"
    })

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
        self._validate_type_and_restriction(
            data.collection_type, data.restricted_to_sub_category_id
        )

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

    async def list_items_grouped(self, collection_id: str) -> list[dict]:
        """Return collection items grouped by main/sub category.

        Args:
            collection_id: UUID of the collection.

        Returns:
            List of dicts with main_category_id, main_category_name,
            sub_category_id, sub_category_name, and item_count.

        Raises:
            NotFoundError: If the collection does not exist.
        """
        collection = await self.get_by_id(collection_id)

        # Query items grouped by category (via Catalog -> SubCategory)
        from api.models.catalog import Catalog, CatalogItem

        stmt = (
            select(
                SubCategory.main_category_id.label("main_category_id"),
                SubCategory.id.label("sub_category_id"),
                func.count(CollectionItem.id).label("item_count"),
            )
            .select_from(CollectionItem)
            .join(CatalogItem, CollectionItem.catalog_item_id == CatalogItem.id)
            .join(Catalog, CatalogItem.catalog_id == Catalog.id)
            .join(SubCategory, Catalog.sub_category_id == SubCategory.id)
            .where(CollectionItem.collection_id == collection_id)
            .group_by(SubCategory.main_category_id, SubCategory.id)
        )

        result = await self._db.execute(stmt)
        rows = result.all()

        # Fetch category names
        from api.models.category import MainCategory

        groups = []
        for row in rows:
            main_cat = await self._db.get(MainCategory, row.main_category_id)
            sub_cat = await self._db.get(SubCategory, row.sub_category_id)
            groups.append({
                "main_category_id": str(row.main_category_id) if row.main_category_id else None,
                "main_category_name": main_cat.name if main_cat else None,
                "sub_category_id": str(row.sub_category_id) if row.sub_category_id else None,
                "sub_category_name": sub_cat.name if sub_cat else None,
                "item_count": row.item_count,
            })

        return groups

    async def validate_item_sub_category(
        self, collection_id: str, sub_category_id: str
    ) -> None:
        """Validate that an item's sub-category matches collection restriction.

        Raises:
            ValidationError: If the collection is single_category and the
                sub-category doesn't match the restriction.
        """
        collection = await self.get_by_id(collection_id)

        if collection.collection_type == "single_category":
            if str(collection.restricted_to_sub_category_id) != str(sub_category_id):
                raise ValidationError(
                    f"Item sub-category '{sub_category_id}' does not match "
                    f"collection restriction '{collection.restricted_to_sub_category_id}'"
                )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_type_and_restriction(
        self, collection_type: str, restricted_to_sub_category_id: str | None
    ) -> None:
        """Validate collection type and sub-category restriction.

        Raises:
            ValidationError: If single_category without restriction, or
                if non-single_category with restriction.
        """
        if collection_type not in self.VALID_TYPES:
            raise ValidationError(
                f"Invalid collection type '{collection_type}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_TYPES))}"
            )

        if collection_type == "single_category":
            if restricted_to_sub_category_id is None:
                raise ValidationError(
                    "restricted_to_sub_category_id is required for single_category collections"
                )
        # Note: We allow restricted_to_sub_category_id to be None for other types

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
