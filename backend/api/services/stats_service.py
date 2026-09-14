"""Business logic for aggregate statistics across the collection."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog, CatalogItem
from api.models.category import SubCategory
from api.models.collection import Collection, CollectionItem
from api.models.transaction import ItemTransaction
from api.schemas.stats import (
    CategoryStatsEntry,
    CollectionStatsEntry,
    DashboardStats,
    TimelineEntry,
    TimelinePeriod,
    ValuationStats,
)
from api.services.transaction_service import INFLOW_TYPES
from utils.computations import roi_percentage


class StatsService:
    """Aggregate statistics with transaction-aware investment."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _invested_by_item(self) -> dict[str, Decimal]:
        """Return per-collection-item real investment.

        Uses transaction outflow-minus-inflow when the item has transactions,
        otherwise purchase_price. Items with neither are omitted.
        """
        invested: dict[str, Decimal] = {}

        # Items with transactions -> net outflow.
        tx_result = await self._db.execute(
            select(
                ItemTransaction.collection_item_id,
                ItemTransaction.transaction_type,
                ItemTransaction.total_amount,
            )
        )
        tx_items: set[str] = set()
        for item_id, ttype, total in tx_result.all():
            tx_items.add(item_id)
            amt = Decimal(str(total or 0))
            signed = -amt if ttype in INFLOW_TYPES else amt
            invested[item_id] = invested.get(item_id, Decimal("0")) + signed

        # Items without transactions -> purchase_price.
        pp_result = await self._db.execute(
            select(CollectionItem.id, CollectionItem.purchase_price).where(
                CollectionItem.purchase_price.isnot(None)
            )
        )
        for item_id, pp in pp_result.all():
            if item_id not in tx_items:
                invested[item_id] = Decimal(str(pp))

        return invested

    async def _market_value_total(
        self, collection_id: str | None = None
    ) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(CollectionItem.current_market_value), 0)
        )
        if collection_id is not None:
            stmt = stmt.where(CollectionItem.collection_id == collection_id)
        result = await self._db.execute(stmt)
        return Decimal(str(result.scalar() or 0))

    async def get_dashboard(self) -> DashboardStats:
        collections = (
            await self._db.execute(select(func.count(Collection.id)))
        ).scalar() or 0
        total_items = (
            await self._db.execute(select(func.count(CollectionItem.id)))
        ).scalar() or 0
        complete_items = (
            await self._db.execute(
                select(func.count(CollectionItem.id)).where(
                    CollectionItem.is_complete.is_(True)
                )
            )
        ).scalar() or 0
        graded_items = (
            await self._db.execute(
                select(func.count(CollectionItem.id)).where(
                    CollectionItem.is_graded.is_(True)
                )
            )
        ).scalar() or 0

        invested_map = await self._invested_by_item()
        total_invested = sum(invested_map.values(), Decimal("0"))
        current_value = await self._market_value_total()
        value_gain = current_value - total_invested
        roi = roi_percentage(total_invested, current_value)

        return DashboardStats(
            total_collections=collections,
            total_items=total_items,
            total_invested=total_invested,
            current_value=current_value,
            value_gain=value_gain,
            roi_percentage=roi,
            complete_items=complete_items,
            graded_items=graded_items,
        )

    async def get_valuation(self) -> ValuationStats:
        invested_map = await self._invested_by_item()
        total_invested = sum(invested_map.values(), Decimal("0"))
        current_value = await self._market_value_total()
        return ValuationStats(
            total_invested=total_invested,
            current_value=current_value,
            value_gain=current_value - total_invested,
            roi_percentage=roi_percentage(total_invested, current_value),
        )

    async def get_by_collection(self) -> list[CollectionStatsEntry]:
        invested_map = await self._invested_by_item()

        result = await self._db.execute(
            select(Collection.id, Collection.name).where(
                Collection.is_active.is_(True)
            )
        )
        entries: list[CollectionStatsEntry] = []
        for coll_id, name in result.all():
            items = (
                await self._db.execute(
                    select(CollectionItem.id).where(
                        CollectionItem.collection_id == coll_id
                    )
                )
            ).scalars().all()
            invested = sum(
                (invested_map.get(i, Decimal("0")) for i in items), Decimal("0")
            )
            current_value = await self._market_value_total(coll_id)
            entries.append(
                CollectionStatsEntry(
                    collection_id=coll_id,
                    collection_name=name,
                    total_items=len(items),
                    total_invested=invested,
                    current_value=current_value,
                    roi_percentage=roi_percentage(invested, current_value),
                )
            )
        return entries

    async def get_by_category(self) -> list[CategoryStatsEntry]:
        result = await self._db.execute(
            select(
                Catalog.sub_category_id,
                SubCategory.name,
                func.count(CollectionItem.id),
                func.coalesce(
                    func.sum(CollectionItem.current_market_value), 0
                ),
            )
            .select_from(CollectionItem)
            .join(CatalogItem, CollectionItem.catalog_item_id == CatalogItem.id)
            .join(Catalog, CatalogItem.catalog_id == Catalog.id)
            .join(SubCategory, Catalog.sub_category_id == SubCategory.id)
            .group_by(Catalog.sub_category_id, SubCategory.name)
        )
        return [
            CategoryStatsEntry(
                sub_category_id=sub_id,
                sub_category_name=name,
                item_count=count,
                current_value=Decimal(str(value or 0)),
            )
            for sub_id, name, count, value in result.all()
        ]

    async def get_timeline(
        self, period: TimelinePeriod
    ) -> list[TimelineEntry]:
        result = await self._db.execute(
            select(
                CollectionItem.id,
                CollectionItem.acquisition_date,
                CollectionItem.purchase_price,
            ).where(CollectionItem.acquisition_date.isnot(None))
        )
        buckets: dict[str, dict[str, Decimal | int]] = {}
        for _item_id, acq_date, pp in result.all():
            key = self._period_key(str(acq_date), period)
            b = buckets.setdefault(
                key, {"item_count": 0, "invested": Decimal("0")}
            )
            b["item_count"] = int(b["item_count"]) + 1
            b["invested"] = Decimal(str(b["invested"])) + (
                Decimal(str(pp)) if pp is not None else Decimal("0")
            )
        return [
            TimelineEntry(
                period=k,
                item_count=int(v["item_count"]),
                invested=Decimal(str(v["invested"])),
            )
            for k, v in sorted(buckets.items())
        ]

    @staticmethod
    def _period_key(date_str: str, period: TimelinePeriod) -> str:
        # date_str is ISO YYYY-MM-DD
        year = date_str[:4]
        month = int(date_str[5:7]) if len(date_str) >= 7 else 1
        if period is TimelinePeriod.YEAR:
            return year
        if period is TimelinePeriod.QUARTER:
            q = (month - 1) // 3 + 1
            return f"{year}-Q{q}"
        return date_str[:7]  # YYYY-MM
