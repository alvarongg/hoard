"""Business logic for collection items."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.catalog import CatalogItem
from api.models.collection import Collection, CollectionCatalog, CollectionItem
from api.schemas.collection_item import CollectionItemCreate, CollectionItemUpdate
from core.exceptions import NotFoundError, ValidationError


class CollectionItemService:
    """Handles CRUD operations and business rules for collection items."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_collection(
        self,
        collection_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CollectionItem]:
        """Return items for a collection ordered by created_at desc, with pagination.

        Raises:
            NotFoundError: If the collection does not exist.
        """
        await self._get_collection(collection_id)

        result = await self._db.execute(
            select(CollectionItem)
            .where(CollectionItem.collection_id == collection_id)
            .order_by(CollectionItem.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, item_id: str) -> CollectionItem:
        """Return a single collection item by id.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self._db.get(CollectionItem, item_id)
        if item is None:
            raise NotFoundError(f"Collection item '{item_id}' not found")
        return item

    async def add_item(
        self,
        collection_id: str,
        data: CollectionItemCreate,
    ) -> CollectionItem:
        """Add a catalog item to a collection.

        Validates that the collection and catalog item exist, and that
        the catalog item's sub-category matches the collection's
        restricted sub-category for single_category collections.

        Raises:
            NotFoundError: If the collection or catalog item does not exist.
            ValidationError: If the item's category is incompatible.
        """
        collection = await self._get_collection(collection_id)
        catalog_item = await self._get_catalog_item(data.catalog_item_id)

        self._validate_category_compatibility(collection, catalog_item)

        payload = data.model_dump()
        # custom_fields defaults to a dict at the model level; drop None.
        if payload.get("custom_fields") is None:
            payload.pop("custom_fields", None)

        item = CollectionItem(
            collection_id=collection_id,
            **payload,
        )
        self._db.add(item)
        # Ensure the collection is linked to this item's catalog (N:M),
        # so every collection ends up with at least one associated catalog.
        await self._ensure_catalog_linked(
            collection_id, catalog_item.catalog_id
        )
        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def update(
        self,
        item_id: str,
        data: CollectionItemUpdate,
    ) -> CollectionItem:
        """Partially update a collection item.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self.get_by_id(item_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(item, field, value)

        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def delete(self, item_id: str) -> None:
        """Delete a collection item (hard delete).

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self.get_by_id(item_id)
        await self._db.delete(item)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_collection(self, collection_id: str) -> Collection:
        """Fetch a collection or raise NotFoundError."""
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            raise NotFoundError(
                f"Collection '{collection_id}' not found"
            )
        return collection

    async def _ensure_catalog_linked(
        self, collection_id: str, catalog_id: str
    ) -> None:
        """Idempotently link a catalog to a collection (N:M)."""
        existing = await self._db.get(
            CollectionCatalog, (collection_id, catalog_id)
        )
        if existing is None:
            self._db.add(
                CollectionCatalog(
                    collection_id=collection_id, catalog_id=catalog_id
                )
            )

    async def _get_catalog_item(self, catalog_item_id: str) -> CatalogItem:
        """Fetch a catalog item with its catalog relationship loaded."""
        result = await self._db.execute(
            select(CatalogItem)
            .options(selectinload(CatalogItem.catalog))
            .where(CatalogItem.id == catalog_item_id)
        )
        catalog_item = result.scalar_one_or_none()
        if catalog_item is None:
            raise NotFoundError(
                f"Catalog item '{catalog_item_id}' not found"
            )
        return catalog_item

    @staticmethod
    def _validate_category_compatibility(
        collection: Collection,
        catalog_item: CatalogItem,
    ) -> None:
        """Ensure the catalog item belongs to the collection's restricted sub-category."""
        if collection.collection_type != "single_category":
            return

        if catalog_item.catalog.sub_category_id != collection.restricted_to_sub_category_id:
            raise ValidationError(
                "El item no pertenece a la sub-categoría de esta colección"
            )
