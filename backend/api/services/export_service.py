"""Business logic for exporting collections, catalogs, and wishlist."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.catalog import Catalog, CatalogItem
from api.models.collection import Collection, CollectionItem
from api.models.wishlist import WishlistItem
from api.schemas.export import (
    CatalogExport,
    CollectionExport,
    CollectionItemExport,
    WishlistExport,
)
from api.services.csv_import_service import CsvImportService
from core.exceptions import NotFoundError

SCHEMA_VERSION = "1.0"


class ExportService:
    """Produces JSON/CSV export payloads."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    async def export_collection(self, collection_id: str) -> CollectionExport:
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            raise NotFoundError(f"Collection '{collection_id}' not found")

        items_result = await self._db.execute(
            select(CollectionItem)
            .where(CollectionItem.collection_id == collection_id)
            .options(selectinload(CollectionItem.components))
        )
        items = list(items_result.scalars().all())

        item_exports: list[CollectionItemExport] = []
        catalog_item_ids: set[str] = set()
        for item in items:
            catalog_item_ids.add(item.catalog_item_id)
            item_exports.append(
                CollectionItemExport(
                    id=item.id,
                    catalog_item_id=item.catalog_item_id,
                    condition=item.condition,
                    is_complete=item.is_complete,
                    purchase_price=(
                        str(item.purchase_price)
                        if item.purchase_price is not None
                        else None
                    ),
                    components=[
                        {
                            "component_name": c.component_name,
                            "component_type": c.component_type,
                            "is_present": c.is_present,
                            "condition": c.condition,
                        }
                        for c in item.components
                    ],
                )
            )

        catalog_items: list[dict] = []
        if catalog_item_ids:
            ci_result = await self._db.execute(
                select(CatalogItem).where(CatalogItem.id.in_(catalog_item_ids))
            )
            for ci in ci_result.scalars().all():
                catalog_items.append(
                    {"id": ci.id, "catalog_id": ci.catalog_id, "title": ci.title}
                )

        return CollectionExport(
            schema_version=SCHEMA_VERSION,
            entity_type="collection",
            exported_at=self._now(),
            collection={
                "id": collection.id,
                "name": collection.name,
                "collection_type": collection.collection_type,
            },
            items=item_exports,
            catalog_items=catalog_items,
        )

    async def export_catalog_json(self, catalog_id: str) -> CatalogExport:
        catalog = await self._db.get(Catalog, catalog_id)
        if catalog is None:
            raise NotFoundError(f"Catalog '{catalog_id}' not found")
        items_result = await self._db.execute(
            select(CatalogItem).where(CatalogItem.catalog_id == catalog_id)
        )
        items = [
            {"id": ci.id, "title": ci.title, "region": ci.region}
            for ci in items_result.scalars().all()
        ]
        return CatalogExport(
            schema_version=SCHEMA_VERSION,
            entity_type="catalog",
            exported_at=self._now(),
            catalog={"id": catalog.id, "name": catalog.name},
            items=items,
        )

    async def export_catalog_csv(self, catalog_id: str) -> str:
        catalog = await self._db.get(Catalog, catalog_id)
        if catalog is None:
            raise NotFoundError(f"Catalog '{catalog_id}' not found")

        # Header derived from the importer's columns, in a stable order.
        header = ["title", *sorted(CsvImportService.OPTIONAL_COLUMNS)]

        items_result = await self._db.execute(
            select(CatalogItem).where(CatalogItem.catalog_id == catalog_id)
        )
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for ci in items_result.scalars().all():
            writer.writerow(
                {
                    "title": ci.title,
                    "subtitle": ci.subtitle,
                    "description": ci.description,
                    "manufacturer": ci.manufacturer,
                    "publisher": ci.publisher,
                    "developer": ci.developer,
                    "brand": ci.brand,
                    "language": ci.language,
                    "region": ci.region,
                    "rarity": ci.rarity,
                    "sku": ci.sku,
                    "upc": ci.upc,
                }
            )
        return buffer.getvalue()

    async def export_wishlist(self) -> WishlistExport:
        result = await self._db.execute(select(WishlistItem))
        items = [
            {
                "id": w.id,
                "collection_id": w.collection_id,
                "catalog_item_id": w.catalog_item_id,
                "priority": w.priority,
            }
            for w in result.scalars().all()
        ]
        return WishlistExport(
            schema_version=SCHEMA_VERSION,
            entity_type="wishlist",
            exported_at=self._now(),
            items=items,
        )
