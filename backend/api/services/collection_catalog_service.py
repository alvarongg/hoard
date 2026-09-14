"""Business logic for the collection<->catalog N:M association."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog
from api.models.collection import Collection, CollectionCatalog
from core.exceptions import NotFoundError


class CollectionCatalogService:
    """Associate, dissociate and list catalogs linked to a collection."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_collection(self, collection_id: str) -> list[Catalog]:
        await self._get_collection(collection_id)
        result = await self._db.execute(
            select(Catalog)
            .join(
                CollectionCatalog,
                CollectionCatalog.catalog_id == Catalog.id,
            )
            .where(CollectionCatalog.collection_id == collection_id)
            .order_by(Catalog.name)
        )
        return list(result.scalars().all())

    async def associate(
        self, collection_id: str, catalog_id: str, is_primary: bool = False
    ) -> CollectionCatalog:
        await self._get_collection(collection_id)
        await self._get_catalog(catalog_id)
        existing = await self._db.get(
            CollectionCatalog, (collection_id, catalog_id)
        )
        if existing is not None:
            if is_primary and not existing.is_primary:
                existing.is_primary = True
                await self._db.commit()
                await self._db.refresh(existing)
            return existing
        link = CollectionCatalog(
            collection_id=collection_id,
            catalog_id=catalog_id,
            is_primary=is_primary,
        )
        self._db.add(link)
        await self._db.commit()
        await self._db.refresh(link)
        return link

    async def dissociate(self, collection_id: str, catalog_id: str) -> None:
        link = await self._db.get(
            CollectionCatalog, (collection_id, catalog_id)
        )
        if link is None:
            raise NotFoundError(
                f"Catalog '{catalog_id}' is not linked to collection "
                f"'{collection_id}'"
            )
        await self._db.delete(link)
        await self._db.commit()

    async def _get_collection(self, collection_id: str) -> Collection:
        collection = await self._db.get(Collection, collection_id)
        if collection is None:
            raise NotFoundError(f"Collection '{collection_id}' not found")
        return collection

    async def _get_catalog(self, catalog_id: str) -> Catalog:
        catalog = await self._db.get(Catalog, catalog_id)
        if catalog is None:
            raise NotFoundError(f"Catalog '{catalog_id}' not found")
        return catalog
