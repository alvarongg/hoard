"""Quick-add orchestration: supplier, catalog, and catalog-item+collection-item.

Each quick-add creates an entity with minimal data and opens a
PendingCompletion listing the recommended fields still missing, so the
collector can complete them later from the Pending tab.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionCatalog, CollectionItem
from api.models.supplier import Supplier
from api.schemas.quick_add import (
    CatalogItemQuickAdd,
    CatalogQuickAdd,
    SupplierQuickAdd,
)
from api.services.pending_service import PendingService
from core.exceptions import NotFoundError, ValidationError

# Main category under which quick-created themed catalogs are filed.
_QUICK_MAIN_CATEGORY_NAME = "General"
_QUICK_MAIN_CATEGORY_SLUG = "general"

_SUPPLIER_PENDING_FIELDS = ["type", "city", "website", "email"]
_CATALOG_ITEM_PENDING_FIELDS = [
    "region",
    "manufacturer",
    "publisher",
    "release_date",
]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


class QuickAddService:
    """Orchestrates minimal-data creation flows."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._pending = PendingService(db)

    # ------------------------------------------------------------------
    # Supplier
    # ------------------------------------------------------------------

    async def quick_add_supplier(self, data: SupplierQuickAdd) -> Supplier:
        supplier = Supplier(name=data.name, country=data.country)
        self._db.add(supplier)
        await self._db.flush()
        missing = [f for f in _SUPPLIER_PENDING_FIELDS]
        if not data.country:
            missing.append("country")
        await self._pending.open(
            "supplier", supplier.id, missing, commit=False
        )
        await self._db.commit()
        await self._db.refresh(supplier)
        return supplier

    # ------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------

    async def _resolve_quick_sub_category(self, tematica: str) -> SubCategory:
        """Find or create a sub-category for the given theme."""
        main = (
            await self._db.execute(
                select(MainCategory).where(
                    MainCategory.slug == _QUICK_MAIN_CATEGORY_SLUG
                )
            )
        ).scalar_one_or_none()
        if main is None:
            main = MainCategory(
                name=_QUICK_MAIN_CATEGORY_NAME,
                slug=_QUICK_MAIN_CATEGORY_SLUG,
            )
            self._db.add(main)
            await self._db.flush()

        slug = _slugify(tematica)
        sub = (
            await self._db.execute(
                select(SubCategory).where(
                    SubCategory.main_category_id == main.id,
                    SubCategory.slug == slug,
                )
            )
        ).scalar_one_or_none()
        if sub is None:
            sub = SubCategory(
                main_category_id=main.id, name=tematica, slug=slug
            )
            self._db.add(sub)
            await self._db.flush()
        return sub

    async def quick_add_catalog(
        self, collection_id: str, data: CatalogQuickAdd
    ) -> Catalog:
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            raise NotFoundError(f"Collection '{collection_id}' not found")

        sub = await self._resolve_quick_sub_category(data.tematica)
        # Enforce catalog name uniqueness within the sub-category.
        existing = (
            await self._db.execute(
                select(Catalog).where(
                    Catalog.sub_category_id == sub.id,
                    Catalog.name == data.name,
                )
            )
        ).scalar_one_or_none()
        catalog = existing or Catalog(
            sub_category_id=sub.id,
            name=data.name,
            description=f"Temática: {data.tematica}",
        )
        if existing is None:
            self._db.add(catalog)
            await self._db.flush()

        # Link to the collection (idempotent).
        link = await self._db.get(
            CollectionCatalog, (collection_id, catalog.id)
        )
        if link is None:
            self._db.add(
                CollectionCatalog(
                    collection_id=collection_id,
                    catalog_id=catalog.id,
                    is_primary=data.is_primary,
                )
            )
        await self._pending.open(
            "catalog", catalog.id, ["description", "source_url"], commit=False
        )
        await self._db.commit()
        await self._db.refresh(catalog)
        return catalog

    # ------------------------------------------------------------------
    # Catalog item + collection item (one operation)
    # ------------------------------------------------------------------

    async def quick_add_catalog_item_and_collection_item(
        self, collection_id: str, data: CatalogItemQuickAdd
    ) -> CollectionItem:
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            raise NotFoundError(f"Collection '{collection_id}' not found")
        catalog = await self._db.get(Catalog, data.catalog_id)
        if catalog is None:
            raise NotFoundError(f"Catalog '{data.catalog_id}' not found")
        # The catalog must be associated with the collection.
        link = await self._db.get(
            CollectionCatalog, (collection_id, data.catalog_id)
        )
        if link is None:
            raise ValidationError(
                "El catálogo no está asociado a la colección; "
                "asocialo o creá uno rápido primero"
            )

        catalog_item = CatalogItem(catalog_id=catalog.id, title=data.title)
        self._db.add(catalog_item)
        await self._db.flush()
        catalog.total_items = (catalog.total_items or 0) + 1

        ci_payload = data.collection_item.model_dump()
        ci_payload["catalog_item_id"] = catalog_item.id
        if ci_payload.get("custom_fields") is None:
            ci_payload.pop("custom_fields", None)
        collection_item = CollectionItem(
            collection_id=collection_id, **ci_payload
        )
        self._db.add(collection_item)

        await self._pending.open(
            "catalog_item",
            catalog_item.id,
            list(_CATALOG_ITEM_PENDING_FIELDS),
            commit=False,
        )
        await self._db.commit()
        await self._db.refresh(collection_item)
        return collection_item
