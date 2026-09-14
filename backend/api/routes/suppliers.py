"""REST endpoints for suppliers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_supplier_service
from api.schemas.supplier import (
    SupplierCreate,
    SupplierPurchase,
    SupplierResponse,
    SupplierUpdate,
)
from api.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


# ------------------------------------------------------------------
# Suppliers CRUD
# ------------------------------------------------------------------


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(
    type: str | None = Query(None, description="Filter by supplier type"),
    country: str | None = Query(None, description="Filter by country code"),
    is_favorite: bool | None = Query(None, description="Filter by favorite status"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: SupplierService = Depends(get_supplier_service),
) -> list[SupplierResponse]:
    """List all suppliers with optional filters and pagination."""
    return await service.list(
        type=type,
        country=country,
        is_favorite=is_favorite,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    data: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierResponse:
    """Create a new supplier."""
    return await service.create(data)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierResponse:
    """Get a single supplier by id."""
    return await service.get(supplier_id)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierResponse:
    """Update a supplier."""
    return await service.update(supplier_id, data)


@router.delete("/{supplier_id}", status_code=204, response_class=Response)
async def delete_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
) -> None:
    """Delete a supplier."""
    await service.delete(supplier_id)


# ------------------------------------------------------------------
# Supplier purchase history
# ------------------------------------------------------------------


@router.get(
    "/{supplier_id}/purchases",
    response_model=list[SupplierPurchase],
)
async def get_supplier_purchases(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
) -> list[SupplierPurchase]:
    """Get purchase history for a supplier."""
    items = await service.get_purchase_history(supplier_id)
    return [
        SupplierPurchase(
            collection_item_id=item.id,
            title=item.title,
            purchase_date=item.purchase_date,
            purchase_price=item.purchase_price,
            purchase_currency=item.purchase_currency,
        )
        for item in items
    ]
