"""Business logic for catalog price history and market value refresh."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import CatalogItem
from api.models.collection import CollectionItem
from api.models.price_history import CatalogPriceHistory
from api.schemas.price_history import PriceHistoryCreate
from core.exceptions import DuplicateError, NotFoundError


class PriceHistoryService:
    """Handles price history records and market value refresh."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        catalog_item_id: str,
        *,
        condition: str | None = None,
        is_complete: bool | None = None,
        region: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[CatalogPriceHistory]:
        """Return price records for a catalog item, newest first."""
        await self._ensure_catalog_item(catalog_item_id)

        query = select(CatalogPriceHistory).where(
            CatalogPriceHistory.catalog_item_id == catalog_item_id
        )
        if condition is not None:
            query = query.where(CatalogPriceHistory.condition == condition)
        if is_complete is not None:
            query = query.where(CatalogPriceHistory.is_complete.is_(is_complete))
        if region is not None:
            query = query.where(CatalogPriceHistory.region == region)
        if date_from is not None:
            query = query.where(CatalogPriceHistory.price_date >= date_from)
        if date_to is not None:
            query = query.where(CatalogPriceHistory.price_date <= date_to)

        query = query.order_by(CatalogPriceHistory.price_date.desc())
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def create(
        self, catalog_item_id: str, data: PriceHistoryCreate
    ) -> CatalogPriceHistory:
        """Create a price record, rejecting duplicates on the natural key.

        Raises:
            NotFoundError: If the catalog item does not exist.
            DuplicateError: If a record with the same natural key exists.
        """
        await self._ensure_catalog_item(catalog_item_id)

        existing = await self._db.execute(
            select(CatalogPriceHistory)
            .where(CatalogPriceHistory.catalog_item_id == catalog_item_id)
            .where(CatalogPriceHistory.condition == data.condition)
            .where(CatalogPriceHistory.is_complete.is_(data.is_complete))
            .where(CatalogPriceHistory.price_date == data.price_date)
            .where(CatalogPriceHistory.source == data.source)
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateError(
                "A price record for this item, condition, completeness, "
                "date and source already exists"
            )

        record = CatalogPriceHistory(
            catalog_item_id=catalog_item_id, **data.model_dump()
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def delete(self, price_history_id: str) -> None:
        """Delete a price record.

        Raises:
            NotFoundError: If the record does not exist.
        """
        record = await self._db.get(CatalogPriceHistory, price_history_id)
        if record is None:
            raise NotFoundError(f"Price record '{price_history_id}' not found")
        await self._db.delete(record)
        await self._db.commit()

    async def latest_by_condition(
        self, catalog_item_id: str
    ) -> list[CatalogPriceHistory]:
        """Return the most recent price record for each condition."""
        await self._ensure_catalog_item(catalog_item_id)

        result = await self._db.execute(
            select(CatalogPriceHistory)
            .where(CatalogPriceHistory.catalog_item_id == catalog_item_id)
            .order_by(CatalogPriceHistory.price_date.desc())
        )
        records = list(result.scalars().all())

        latest: dict[str, CatalogPriceHistory] = {}
        for record in records:
            if record.condition not in latest:
                latest[record.condition] = record
        return list(latest.values())

    async def refresh_item_market_value(
        self, collection_item_id: str
    ) -> tuple[bool, CollectionItem | None, str | None]:
        """Set a collection item's market value from the latest compatible price.

        Uses the most recent price record matching the item's condition and
        completeness. If none exists, nothing is changed.

        Returns:
            (updated, item, reason)

        Raises:
            NotFoundError: If the collection item does not exist.
        """
        item = await self._db.get(CollectionItem, collection_item_id)
        if item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )

        result = await self._db.execute(
            select(CatalogPriceHistory)
            .where(CatalogPriceHistory.catalog_item_id == item.catalog_item_id)
            .where(CatalogPriceHistory.condition == item.condition)
            .where(CatalogPriceHistory.is_complete.is_(item.is_complete))
            .order_by(CatalogPriceHistory.price_date.desc())
            .limit(1)
        )
        price = result.scalar_one_or_none()

        if price is None:
            return (
                False,
                item,
                "No compatible price record found for this item's "
                "condition and completeness",
            )

        item.current_market_value = price.price
        item.current_value_currency = price.currency
        item.last_value_update = datetime.now(UTC).replace(tzinfo=None)
        item.value_source = price.source or "price_history"
        await self._db.commit()
        await self._db.refresh(item)
        return (True, item, None)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _ensure_catalog_item(self, catalog_item_id: str) -> None:
        item = await self._db.get(CatalogItem, catalog_item_id)
        if item is None:
            raise NotFoundError(f"Catalog item '{catalog_item_id}' not found")
