"""REST endpoints for accessories stock and assignments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_accessory_service
from api.models.accessory import AccessoryStock
from api.schemas.accessory import (
    AccessoryCreate,
    AccessoryResponse,
    AccessoryUpdate,
    ItemAccessoryCreate,
    ItemAccessoryResponse,
    LowStockEntry,
)
from api.services.accessory_service import AccessoryService

router = APIRouter(tags=["accessories"])


def _to_response(
    acc: AccessoryStock, service: AccessoryService
) -> AccessoryResponse:
    available = service._available(acc)  # noqa: SLF001 (route-local helper)
    return AccessoryResponse(
        id=acc.id,
        name=acc.name,
        category=acc.category,
        subcategory=acc.subcategory,
        compatible_sub_categories=acc.compatible_sub_categories,
        size_specifications=acc.size_specifications,
        quantity_total=acc.quantity_total,
        minimum_stock_alert=acc.minimum_stock_alert,
        reorder_quantity=acc.reorder_quantity,
        unit_cost=acc.unit_cost,
        currency=acc.currency,
        supplier_id=acc.supplier_id,
        supplier_sku=acc.supplier_sku,
        supplier_url=acc.supplier_url,
        notes=acc.notes,
        quantity_in_use=acc.quantity_in_use,
        quantity_available=available,
        is_low_stock=available <= acc.minimum_stock_alert,
    )


@router.get("/accessories", response_model=list[AccessoryResponse])
async def list_accessories(
    category: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: AccessoryService = Depends(get_accessory_service),
) -> list[AccessoryResponse]:
    """List accessories with optional category filter and pagination."""
    accs = await service.list(category=category, skip=skip, limit=limit)
    return [_to_response(a, service) for a in accs]


@router.get("/accessories/low-stock", response_model=list[LowStockEntry])
async def low_stock(
    service: AccessoryService = Depends(get_accessory_service),
) -> list[LowStockEntry]:
    """List accessories at or below their minimum-stock threshold."""
    accs = await service.list_low_stock()
    return [
        LowStockEntry(
            id=a.id,
            name=a.name,
            quantity_available=service._available(a),  # noqa: SLF001
            minimum_stock_alert=a.minimum_stock_alert,
            reorder_quantity=a.reorder_quantity,
        )
        for a in accs
    ]


@router.post("/accessories", response_model=AccessoryResponse, status_code=201)
async def create_accessory(
    data: AccessoryCreate,
    service: AccessoryService = Depends(get_accessory_service),
) -> AccessoryResponse:
    """Create an accessory."""
    acc = await service.create(data)
    return _to_response(acc, service)


@router.get("/accessories/{accessory_id}", response_model=AccessoryResponse)
async def get_accessory(
    accessory_id: str,
    service: AccessoryService = Depends(get_accessory_service),
) -> AccessoryResponse:
    """Get an accessory by id."""
    acc = await service.get(accessory_id)
    return _to_response(acc, service)


@router.put("/accessories/{accessory_id}", response_model=AccessoryResponse)
async def update_accessory(
    accessory_id: str,
    data: AccessoryUpdate,
    service: AccessoryService = Depends(get_accessory_service),
) -> AccessoryResponse:
    """Update an accessory."""
    acc = await service.update(accessory_id, data)
    return _to_response(acc, service)


@router.delete(
    "/accessories/{accessory_id}", status_code=204, response_class=Response
)
async def delete_accessory(
    accessory_id: str,
    service: AccessoryService = Depends(get_accessory_service),
) -> None:
    """Delete an accessory with no assignments."""
    await service.delete(accessory_id)


@router.get(
    "/collection-items/{collection_item_id}/accessories",
    response_model=list[ItemAccessoryResponse],
)
async def list_item_accessories(
    collection_item_id: str,
    service: AccessoryService = Depends(get_accessory_service),
) -> list[ItemAccessoryResponse]:
    """List accessories assigned to a collection item."""
    return await service.list_assignments(collection_item_id)


@router.post(
    "/collection-items/{collection_item_id}/accessories",
    response_model=ItemAccessoryResponse,
    status_code=201,
)
async def assign_accessory(
    collection_item_id: str,
    data: ItemAccessoryCreate,
    service: AccessoryService = Depends(get_accessory_service),
) -> ItemAccessoryResponse:
    """Assign an accessory to a collection item."""
    return await service.assign(
        collection_item_id,
        data.accessory_id,
        data.quantity_used,
        data.notes,
    )


@router.delete(
    "/item-accessories/{item_accessory_id}",
    status_code=204,
    response_class=Response,
)
async def unassign_accessory(
    item_accessory_id: str,
    service: AccessoryService = Depends(get_accessory_service),
) -> None:
    """Remove an accessory assignment."""
    await service.unassign(item_accessory_id)
