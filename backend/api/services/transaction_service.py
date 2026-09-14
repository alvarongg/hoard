"""Business logic for item transactions and investment calculations."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.collection import CollectionItem
from api.models.transaction import ItemTransaction
from api.schemas.transaction import (
    ItemInvestment,
    TransactionCreate,
    TransactionUpdate,
)
from core.exceptions import NotFoundError, ValidationError
from utils.computations import roi_percentage

# Transaction types classified by cash-flow direction.
# gift_received / gift_given are treated as inflows (they carry no cost to
# the collector but represent value moving in/out).
OUTFLOW_TYPES = frozenset(
    {"purchase", "trade_in", "grading_fee", "repair", "appraisal"}
)
INFLOW_TYPES = frozenset(
    {"sale", "trade_out", "gift_received", "gift_given"}
)
VALID_TYPES = OUTFLOW_TYPES | INFLOW_TYPES | frozenset({"other"})


class TransactionService:
    """Handles CRUD and investment aggregation for item transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, collection_item_id: str) -> list[ItemTransaction]:
        """Return transactions for a collection item, newest first."""
        await self._ensure_collection_item(collection_item_id)
        result = await self._db.execute(
            select(ItemTransaction)
            .where(ItemTransaction.collection_item_id == collection_item_id)
            .order_by(ItemTransaction.transaction_date.desc())
        )
        return list(result.scalars().all())

    async def create(
        self, collection_item_id: str, data: TransactionCreate
    ) -> ItemTransaction:
        """Create a transaction.

        total_amount is computed by the database (GENERATED/Computed column)
        on both PostgreSQL and SQLite, so it is never assigned here.

        Raises:
            NotFoundError: If the collection item does not exist.
            ValidationError: If the transaction type is not allowed.
        """
        await self._ensure_collection_item(collection_item_id)
        if data.transaction_type not in VALID_TYPES:
            allowed = ", ".join(sorted(VALID_TYPES))
            raise ValidationError(f"transaction_type must be one of: {allowed}")

        record = ItemTransaction(
            collection_item_id=collection_item_id, **data.model_dump()
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def update(
        self, transaction_id: str, data: TransactionUpdate
    ) -> ItemTransaction:
        """Update a transaction.

        Raises:
            NotFoundError: If the transaction does not exist.
        """
        record = await self._db.get(ItemTransaction, transaction_id)
        if record is None:
            raise NotFoundError(f"Transaction '{transaction_id}' not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def delete(self, transaction_id: str) -> ItemInvestment:
        """Delete a transaction and return the recomputed investment.

        Raises:
            NotFoundError: If the transaction does not exist.
        """
        record = await self._db.get(ItemTransaction, transaction_id)
        if record is None:
            raise NotFoundError(f"Transaction '{transaction_id}' not found")
        collection_item_id = record.collection_item_id
        await self._db.delete(record)
        await self._db.commit()
        return await self.get_investment(collection_item_id)

    async def get_investment(self, collection_item_id: str) -> ItemInvestment:
        """Compute the investment summary for a collection item.

        real_invested = sum(total_amount of outflows) - sum(total_amount of
        inflows). When there are no transactions, falls back to the item's
        purchase_price.

        Raises:
            NotFoundError: If the collection item does not exist.
        """
        item = await self._ensure_collection_item(collection_item_id)
        transactions = await self.list(collection_item_id)

        market_value = (
            Decimal(str(item.current_market_value))
            if item.current_market_value is not None
            else None
        )

        if not transactions:
            purchase = (
                Decimal(str(item.purchase_price))
                if item.purchase_price is not None
                else Decimal("0")
            )
            roi = (
                roi_percentage(purchase, market_value)
                if market_value is not None
                else None
            )
            return ItemInvestment(
                real_invested=purchase,
                total_outflow=purchase,
                total_inflow=Decimal("0"),
                current_market_value=market_value,
                roi_percentage=roi,
                source="purchase_price",
            )

        total_outflow = Decimal("0")
        total_inflow = Decimal("0")
        for tx in transactions:
            total = Decimal(str(tx.total_amount or 0))
            if tx.transaction_type in INFLOW_TYPES:
                total_inflow += total
            else:
                total_outflow += total

        real_invested = total_outflow - total_inflow
        roi = (
            roi_percentage(real_invested, market_value)
            if market_value is not None
            else None
        )
        return ItemInvestment(
            real_invested=real_invested,
            total_outflow=total_outflow,
            total_inflow=total_inflow,
            current_market_value=market_value,
            roi_percentage=roi,
            source="transactions",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _ensure_collection_item(
        self, collection_item_id: str
    ) -> CollectionItem:
        item = await self._db.get(CollectionItem, collection_item_id)
        if item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )
        return item
