"""Business logic for suppliers."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.accessory import AccessoryStock
from api.models.collection import CollectionItem
from api.models.supplier import Supplier
from api.models.wishlist import WishlistSighting
from api.schemas.supplier import SupplierCreate, SupplierReferences, SupplierUpdate
from core.exceptions import DuplicateError, NotFoundError, ValidationError

VALID_TYPES = frozenset(
    {"online", "physical_store", "marketplace", "private_seller", "auction"}
)


class SupplierService:
    """Handles CRUD operations and business rules for suppliers."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        *,
        type: str | None = None,
        country: str | None = None,
        is_favorite: bool | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Supplier]:
        """Return suppliers filtered by optional criteria, with pagination."""
        query = select(Supplier)

        if type is not None:
            query = query.where(Supplier.type == type)
        if country is not None:
            query = query.where(Supplier.country == country)
        if is_favorite is not None:
            query = query.where(Supplier.is_favorite.is_(is_favorite))
        if is_active is not None:
            query = query.where(Supplier.is_active.is_(is_active))

        query = query.order_by(Supplier.name).offset(skip).limit(limit)

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def get(self, supplier_id: str) -> Supplier:
        """Return a single supplier by id.

        Raises:
            NotFoundError: If the supplier does not exist.
        """
        supplier = await self._db.get(Supplier, supplier_id)
        if supplier is None:
            raise NotFoundError(f"Supplier '{supplier_id}' not found")
        return supplier

    async def create(self, data: SupplierCreate) -> Supplier:
        """Create a new supplier.

        Raises:
            ValidationError: If type is not one of the allowed values.
        """
        if data.type is not None and data.type not in VALID_TYPES:
            allowed = ", ".join(sorted(VALID_TYPES))
            raise ValidationError(f"type must be one of: {allowed}")

        supplier = Supplier(**data.model_dump())
        self._db.add(supplier)
        await self._db.commit()
        await self._db.refresh(supplier)
        return supplier

    async def update(self, supplier_id: str, data: SupplierUpdate) -> Supplier:
        """Partially update a supplier.

        Raises:
            NotFoundError: If the supplier does not exist.
            ValidationError: If type is not one of the allowed values.
        """
        supplier = await self.get(supplier_id)
        update_data = data.model_dump(exclude_unset=True)

        if "type" in update_data and update_data["type"] is not None:
            if update_data["type"] not in VALID_TYPES:
                allowed = ", ".join(sorted(VALID_TYPES))
                raise ValidationError(f"type must be one of: {allowed}")

        for field, value in update_data.items():
            setattr(supplier, field, value)

        await self._db.commit()
        await self._db.refresh(supplier)
        return supplier

    async def delete(self, supplier_id: str) -> None:
        """Delete a supplier if it has no references.

        Raises:
            NotFoundError: If the supplier does not exist.
            DuplicateError: If the supplier is referenced by other entities.
        """
        supplier = await self.get(supplier_id)
        references = await self._count_references(supplier_id)

        if references.total > 0:
            detail_parts = []
            if references.collection_items > 0:
                detail_parts.append(f"{references.collection_items} collection item(s)")
            if references.wishlist_sightings > 0:
                detail_parts.append(f"{references.wishlist_sightings} wishlist sighting(s)")
            if references.accessories > 0:
                detail_parts.append(f"{references.accessories} accessor(y/ies)")
            detail = ", ".join(detail_parts)
            raise DuplicateError(
                f"Cannot delete supplier '{supplier_id}': it is referenced by {detail}"
            )

        await self._db.delete(supplier)
        await self._db.commit()

    async def get_purchase_history(self, supplier_id: str) -> list[CollectionItem]:
        """Return collection items purchased from this supplier.

        Only returns items that have a purchase_date set.
        """
        await self.get(supplier_id)  # Ensure supplier exists

        result = await self._db.execute(
            select(CollectionItem)
            .where(CollectionItem.supplier_id == supplier_id)
            .where(CollectionItem.purchase_date.isnot(None))
            .order_by(CollectionItem.purchase_date.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _count_references(self, supplier_id: str) -> SupplierReferences:
        """Count how many entities reference this supplier."""
        # Count collection items
        ci_result = await self._db.execute(
            select(func.count())
            .select_from(CollectionItem)
            .where(CollectionItem.supplier_id == supplier_id)
        )
        collection_items = ci_result.scalar() or 0

        # Count wishlist sightings
        ws_result = await self._db.execute(
            select(func.count())
            .select_from(WishlistSighting)
            .where(WishlistSighting.supplier_id == supplier_id)
        )
        wishlist_sightings = ws_result.scalar() or 0

        # Count accessories
        acc_result = await self._db.execute(
            select(func.count())
            .select_from(AccessoryStock)
            .where(AccessoryStock.supplier_id == supplier_id)
        )
        accessories = acc_result.scalar() or 0

        return SupplierReferences(
            collection_items=collection_items,
            wishlist_sightings=wishlist_sightings,
            accessories=accessories,
        )
