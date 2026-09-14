"""Ownership lookup: which collections already contain a catalog item."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import CatalogItem
from api.models.collection import Collection, CollectionItem
from core.exceptions import NotFoundError


class OwnershipService:
    """Answers "do I already own this catalog item?"."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def for_catalog_item(self, catalog_item_id: str) -> dict:
        catalog_item = await self._db.get(CatalogItem, catalog_item_id)
        if catalog_item is None:
            raise NotFoundError(
                f"Catalog item '{catalog_item_id}' not found"
            )
        rows = (
            await self._db.execute(
                select(CollectionItem, Collection.name)
                .join(Collection, CollectionItem.collection_id == Collection.id)
                .where(CollectionItem.catalog_item_id == catalog_item_id)
                .order_by(CollectionItem.created_at.desc())
            )
        ).all()
        entries = [
            {
                "collection_item_id": ci.id,
                "collection_id": ci.collection_id,
                "collection_name": name,
                "condition": ci.condition,
            }
            for ci, name in rows
        ]
        return {
            "catalog_item_id": catalog_item_id,
            "owned": len(entries) > 0,
            "count": len(entries),
            "entries": entries,
        }
