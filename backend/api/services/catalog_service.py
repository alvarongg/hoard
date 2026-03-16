"""Business logic for catalogs and catalog items."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog, CatalogItem
from api.models.category import SubCategory
from api.schemas.catalog import (
    CatalogCreate,
    CatalogItemCreate,
    CatalogItemUpdate,
    CatalogUpdate,
)
from core.exceptions import DuplicateError, NotFoundError, ValidationError


class CatalogService:
    """Handles CRUD operations and business rules for catalogs and catalog items."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Catalogs
    # ------------------------------------------------------------------

    async def list_catalogs(
        self, skip: int = 0, limit: int = 100
    ) -> list[Catalog]:
        """Return all catalogs ordered by name, with pagination."""
        result = await self._db.execute(
            select(Catalog)
            .order_by(Catalog.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_catalog(self, catalog_id: str) -> Catalog:
        """Return a single catalog by id.

        Raises:
            NotFoundError: If the catalog does not exist.
        """
        catalog = await self._db.get(Catalog, catalog_id)
        if catalog is None:
            raise NotFoundError(f"Catalog '{catalog_id}' not found")
        return catalog

    async def create_catalog(self, data: CatalogCreate) -> Catalog:
        """Create a new catalog.

        Raises:
            ValidationError: If the sub_category_id does not exist.
            DuplicateError: If a catalog with the same name exists
                for the same sub-category.
        """
        sub_category = await self._db.get(SubCategory, data.sub_category_id)
        if sub_category is None:
            raise ValidationError(
                f"Sub-category '{data.sub_category_id}' does not exist"
            )

        await self._check_catalog_name_unique(
            data.sub_category_id, data.name
        )

        catalog = Catalog(**data.model_dump())
        self._db.add(catalog)
        await self._db.commit()
        await self._db.refresh(catalog)
        return catalog

    async def update_catalog(
        self, catalog_id: str, data: CatalogUpdate
    ) -> Catalog:
        """Partially update a catalog.

        Raises:
            NotFoundError: If the catalog does not exist.
            DuplicateError: If the new name conflicts with another
                catalog under the same sub-category.
        """
        catalog = await self.get_catalog(catalog_id)
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != catalog.name:
            await self._check_catalog_name_unique(
                catalog.sub_category_id, update_data["name"]
            )

        for field, value in update_data.items():
            setattr(catalog, field, value)

        await self._db.commit()
        await self._db.refresh(catalog)
        return catalog

    async def delete_catalog(self, catalog_id: str) -> None:
        """Delete a catalog and its items (cascade).

        Raises:
            NotFoundError: If the catalog does not exist.
        """
        catalog = await self.get_catalog(catalog_id)
        await self._db.delete(catalog)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Catalog Items
    # ------------------------------------------------------------------

    async def list_items(
        self, catalog_id: str, skip: int = 0, limit: int = 100
    ) -> list[CatalogItem]:
        """Return items for a catalog, ordered by title, with pagination."""
        result = await self._db.execute(
            select(CatalogItem)
            .where(CatalogItem.catalog_id == catalog_id)
            .order_by(CatalogItem.title)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_item(self, item_id: str) -> CatalogItem:
        """Return a single catalog item by id.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self._db.get(CatalogItem, item_id)
        if item is None:
            raise NotFoundError(f"Catalog item '{item_id}' not found")
        return item

    async def create_item(
        self, catalog_id: str, data: CatalogItemCreate
    ) -> CatalogItem:
        """Create a new catalog item in the given catalog.

        Raises:
            NotFoundError: If the catalog does not exist.
        """
        await self.get_catalog(catalog_id)

        item_data = data.model_dump()
        item_data["catalog_id"] = catalog_id
        item = CatalogItem(**item_data)
        self._db.add(item)
        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def update_item(
        self, item_id: str, data: CatalogItemUpdate
    ) -> CatalogItem:
        """Partially update a catalog item.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self.get_item(item_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(item, field, value)

        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def delete_item(self, item_id: str) -> None:
        """Delete a catalog item.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self.get_item(item_id)
        await self._db.delete(item)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_items(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> list[CatalogItem]:
        """Search catalog items by title using case-insensitive matching."""
        result = await self._db.execute(
            select(CatalogItem)
            .where(CatalogItem.title.ilike(f"%{query}%"))
            .order_by(CatalogItem.title)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _check_catalog_name_unique(
        self, sub_category_id: str, name: str
    ) -> None:
        """Raise DuplicateError if a catalog with this name exists
        under the same sub-category."""
        result = await self._db.execute(
            select(Catalog).where(
                Catalog.sub_category_id == sub_category_id,
                Catalog.name == name,
            )
        )
        if result.scalar_one_or_none() is not None:
            raise DuplicateError(
                f"A catalog named '{name}' already exists "
                "in this sub-category"
            )
