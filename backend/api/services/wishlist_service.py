"""Business logic for wishlist items and sightings."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.catalog import CatalogItem
from api.models.collection import Collection, CollectionItem
from api.models.wishlist import WishlistItem, WishlistSighting
from api.schemas.wishlist import (
    PriceAggregates,
    SightingCreate,
    SightingUpdate,
    WishlistAcquire,
    WishlistAcquireAndAdd,
    WishlistItemCreate,
    WishlistItemDetail,
    WishlistItemUpdate,
)
from api.services.collection_item_service import CollectionItemService
from core.dialect import supports_views
from core.exceptions import DuplicateError, NotFoundError, ValidationError

VALID_URGENCY = frozenset({"low", "medium", "high", "critical"})
VALID_DECISIONS = frozenset({"buy", "pass", "wait", "negotiate"})


class WishlistService:
    """Handles CRUD operations and business rules for wishlist items."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # WishlistItem operations
    # ------------------------------------------------------------------

    async def list(
        self,
        *,
        collection_id: str | None = None,
        priority: int | None = None,
        urgency: str | None = None,
        is_active: bool | None = None,
        include_acquired: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WishlistItem]:
        """Return wishlist items filtered by optional criteria, with pagination."""
        query = select(WishlistItem)

        if collection_id is not None:
            query = query.where(WishlistItem.collection_id == collection_id)
        if priority is not None:
            query = query.where(WishlistItem.priority == priority)
        if urgency is not None:
            query = query.where(WishlistItem.urgency == urgency)
        if is_active is not None:
            query = query.where(WishlistItem.is_active.is_(is_active))
        if not include_acquired:
            query = query.where(WishlistItem.is_acquired.is_(False))

        query = (
            query.order_by(WishlistItem.priority, WishlistItem.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def get(self, wishlist_item_id: str) -> WishlistItem:
        """Return a single wishlist item by id.

        Raises:
            NotFoundError: If the wishlist item does not exist.
        """
        item = await self._db.get(WishlistItem, wishlist_item_id)
        if item is None:
            raise NotFoundError(f"Wishlist item '{wishlist_item_id}' not found")
        return item

    async def get_with_price_aggregates(
        self, wishlist_item_id: str
    ) -> WishlistItemDetail:
        """Return a wishlist item with price aggregates.

        Raises:
            NotFoundError: If the wishlist item does not exist.
        """
        item = await self.get(wishlist_item_id)
        aggregates = await self._get_price_aggregates(wishlist_item_id)
        return WishlistItemDetail(
            **{
                "id": item.id,
                "collection_id": item.collection_id,
                "catalog_item_id": item.catalog_item_id,
                "desired_condition": item.desired_condition,
                "desired_condition_min": item.desired_condition_min,
                "must_be_complete": item.must_be_complete,
                "desired_completeness_description": item.desired_completeness_description,
                "max_price": item.max_price,
                "currency": item.currency,
                "specific_variant_required": item.specific_variant_required,
                "variant_description": item.variant_description,
                "priority": item.priority,
                "urgency": item.urgency,
                "notes": item.notes,
                "search_notes": item.search_notes,
                "tags": item.tags,
                "is_active": item.is_active,
                "is_acquired": item.is_acquired,
                "acquired_date": item.acquired_date,
                "acquired_collection_item_id": item.acquired_collection_item_id,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "price_aggregates": aggregates,
            }
        )

    async def create(self, data: WishlistItemCreate) -> WishlistItem:
        """Create a new wishlist item.

        Raises:
            NotFoundError: If the collection or catalog item does not exist.
            ValidationError: If urgency is not one of the allowed values.
        """
        # Validate references exist
        collection = await self._db.get(Collection, data.collection_id)
        if collection is None:
            raise NotFoundError(f"Collection '{data.collection_id}' not found")

        catalog_item = await self._db.get(CatalogItem, data.catalog_item_id)
        if catalog_item is None:
            raise NotFoundError(f"Catalog item '{data.catalog_item_id}' not found")

        # Validate urgency
        if data.urgency not in VALID_URGENCY:
            allowed = ", ".join(sorted(VALID_URGENCY))
            raise ValidationError(f"urgency must be one of: {allowed}")

        item = WishlistItem(**data.model_dump())
        self._db.add(item)
        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def update(
        self, wishlist_item_id: str, data: WishlistItemUpdate
    ) -> WishlistItem:
        """Partially update a wishlist item.

        Raises:
            NotFoundError: If the wishlist item does not exist.
            ValidationError: If urgency is not one of the allowed values.
        """
        item = await self.get(wishlist_item_id)
        update_data = data.model_dump(exclude_unset=True)

        if "urgency" in update_data and update_data["urgency"] is not None:
            if update_data["urgency"] not in VALID_URGENCY:
                allowed = ", ".join(sorted(VALID_URGENCY))
                raise ValidationError(f"urgency must be one of: {allowed}")

        for field, value in update_data.items():
            setattr(item, field, value)

        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def delete(self, wishlist_item_id: str) -> None:
        """Delete a wishlist item.

        Raises:
            NotFoundError: If the wishlist item does not exist.
        """
        item = await self.get(wishlist_item_id)
        await self._db.delete(item)
        await self._db.commit()

    async def mark_acquired(
        self, wishlist_item_id: str, data: WishlistAcquire
    ) -> WishlistItem:
        """Mark a wishlist item as acquired.

        Raises:
            NotFoundError: If the wishlist item or collection item does not exist.
            DuplicateError: If the item is already acquired.
        """
        item = await self.get(wishlist_item_id)

        # Check if already acquired
        if item.is_acquired:
            raise DuplicateError(
                f"Wishlist item '{wishlist_item_id}' is already acquired"
            )

        # Validate collection item exists
        collection_item = await self._db.get(CollectionItem, data.acquired_collection_item_id)
        if collection_item is None:
            raise NotFoundError(
                f"Collection item '{data.acquired_collection_item_id}' not found"
            )

        item.is_acquired = True
        item.acquired_date = date.today()
        item.acquired_collection_item_id = data.acquired_collection_item_id

        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def acquire_and_create(
        self, wishlist_item_id: str, data: WishlistAcquireAndAdd
    ) -> WishlistItem:
        """"Ya lo conseguí": create a collection item from the wishlist item.

        Creates a CollectionItem in the wishlist item's collection using its
        catalog item, marks the wishlist item acquired, and optionally
        deactivates it.

        Raises:
            NotFoundError: If the wishlist item does not exist.
            DuplicateError: If the wishlist item is already acquired.
        """
        item = await self.get(wishlist_item_id)
        if item.is_acquired:
            raise DuplicateError(
                f"Wishlist item '{wishlist_item_id}' is already acquired"
            )

        # Force the catalog item + collection from the wishlist item.
        create = data.collection_item.model_copy(
            update={"catalog_item_id": item.catalog_item_id}
        )
        collection_item = await CollectionItemService(self._db).add_item(
            item.collection_id, create
        )

        item.is_acquired = True
        item.acquired_date = date.today()
        item.acquired_collection_item_id = collection_item.id
        if data.remove_from_wishlist:
            item.is_active = False

        await self._db.commit()
        await self._db.refresh(item)
        return item

    # ------------------------------------------------------------------
    # Sighting operations
    # ------------------------------------------------------------------

    async def list_sightings(
        self,
        wishlist_item_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WishlistSighting]:
        """Return sightings for a wishlist item, ordered by sighted_at desc."""
        await self.get(wishlist_item_id)  # Ensure wishlist item exists

        result = await self._db.execute(
            select(WishlistSighting)
            .where(WishlistSighting.wishlist_item_id == wishlist_item_id)
            .order_by(WishlistSighting.sighted_at.desc().nulls_last())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_sighting(self, data: SightingCreate) -> WishlistSighting:
        """Create a new sighting.

        Raises:
            NotFoundError: If the wishlist item does not exist.
            ValidationError: If decision is not one of the allowed values.
        """
        await self.get(data.wishlist_item_id)  # Ensure wishlist item exists

        # Validate decision
        if data.decision is not None and data.decision not in VALID_DECISIONS:
            allowed = ", ".join(sorted(VALID_DECISIONS))
            raise ValidationError(f"decision must be one of: {allowed}")

        sighting_data = data.model_dump()
        sighting_data["created_at"] = datetime.now()
        sighting = WishlistSighting(**sighting_data)
        self._db.add(sighting)
        await self._db.commit()
        await self._db.refresh(sighting)
        return sighting

    async def update_sighting(
        self, sighting_id: str, data: SightingUpdate
    ) -> WishlistSighting:
        """Partially update a sighting.

        Raises:
            NotFoundError: If the sighting does not exist.
            ValidationError: If decision is not one of the allowed values.
        """
        sighting = await self._db.get(WishlistSighting, sighting_id)
        if sighting is None:
            raise NotFoundError(f"Sighting '{sighting_id}' not found")

        update_data = data.model_dump(exclude_unset=True)

        if "decision" in update_data and update_data["decision"] is not None:
            if update_data["decision"] not in VALID_DECISIONS:
                allowed = ", ".join(sorted(VALID_DECISIONS))
                raise ValidationError(f"decision must be one of: {allowed}")

        for field, value in update_data.items():
            setattr(sighting, field, value)

        await self._db.commit()
        await self._db.refresh(sighting)
        return sighting

    async def delete_sighting(self, sighting_id: str) -> None:
        """Delete a sighting.

        Raises:
            NotFoundError: If the sighting does not exist.
        """
        sighting = await self._db.get(WishlistSighting, sighting_id)
        if sighting is None:
            raise NotFoundError(f"Sighting '{sighting_id}' not found")

        await self._db.delete(sighting)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Price aggregates
    # ------------------------------------------------------------------

    async def _get_price_aggregates(
        self, wishlist_item_id: str
    ) -> PriceAggregates:
        """Calculate price aggregates for a wishlist item.

        Uses a view if PostgreSQL, otherwise falls back to queries.
        """
        if supports_views(self._db):
            return await self._aggregates_from_view(wishlist_item_id)
        return await self._aggregates_from_queries(wishlist_item_id)

    async def _aggregates_from_view(
        self, wishlist_item_id: str
    ) -> PriceAggregates:
        """Get aggregates from the v_wishlist_with_avg_price view.

        Note: This is a placeholder for PostgreSQL view-based queries.
        Falls back to query-based approach for SQLite compatibility.
        """
        return await self._aggregates_from_queries(wishlist_item_id)

    async def _aggregates_from_queries(
        self, wishlist_item_id: str
    ) -> PriceAggregates:
        """Calculate aggregates using standard queries."""
        # Get aggregates
        result = await self._db.execute(
            select(
                func.avg(WishlistSighting.price).label("avg_price"),
                func.min(WishlistSighting.price).label("min_price"),
                func.max(WishlistSighting.price).label("max_price"),
                func.count(WishlistSighting.id).label("total_sightings"),
            ).where(WishlistSighting.wishlist_item_id == wishlist_item_id)
        )
        row = result.one()

        # Count available sightings
        available_result = await self._db.execute(
            select(func.count())
            .select_from(WishlistSighting)
            .where(WishlistSighting.wishlist_item_id == wishlist_item_id)
            .where(WishlistSighting.is_available.is_(True))
        )
        available_sightings = available_result.scalar() or 0

        return PriceAggregates(
            avg_price=row.avg_price,
            min_price=row.min_price,
            max_price=row.max_price,
            total_sightings=row.total_sightings or 0,
            available_sightings=available_sightings,
        )
