"""REST endpoints for wishlist items."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_wishlist_service
from api.schemas.wishlist import (
    PriceAggregates,
    SightingBody,
    SightingCreate,
    SightingResponse,
    SightingUpdate,
    WishlistAcquire,
    WishlistItemCreate,
    WishlistItemDetail,
    WishlistItemResponse,
    WishlistItemUpdate,
)
from api.services.wishlist_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


# ------------------------------------------------------------------
# Wishlist items CRUD
# ------------------------------------------------------------------


@router.get("", response_model=list[WishlistItemResponse])
async def list_wishlist_items(
    collection_id: str | None = Query(None, description="Filter by collection"),
    priority: int | None = Query(None, ge=1, le=5, description="Filter by priority"),
    urgency: str | None = Query(None, description="Filter by urgency"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    include_acquired: bool = Query(
        False, description="Include acquired items in results"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: WishlistService = Depends(get_wishlist_service),
) -> list[WishlistItemResponse]:
    """List wishlist items with optional filters and pagination."""
    return await service.list(
        collection_id=collection_id,
        priority=priority,
        urgency=urgency,
        is_active=is_active,
        include_acquired=include_acquired,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=WishlistItemResponse, status_code=201)
async def create_wishlist_item(
    data: WishlistItemCreate,
    service: WishlistService = Depends(get_wishlist_service),
) -> WishlistItemResponse:
    """Create a new wishlist item."""
    return await service.create(data)


@router.get("/{wishlist_item_id}", response_model=WishlistItemDetail)
async def get_wishlist_item(
    wishlist_item_id: str,
    service: WishlistService = Depends(get_wishlist_service),
) -> WishlistItemDetail:
    """Get a single wishlist item with price aggregates."""
    return await service.get_with_price_aggregates(wishlist_item_id)


@router.put("/{wishlist_item_id}", response_model=WishlistItemResponse)
async def update_wishlist_item(
    wishlist_item_id: str,
    data: WishlistItemUpdate,
    service: WishlistService = Depends(get_wishlist_service),
) -> WishlistItemResponse:
    """Update a wishlist item."""
    return await service.update(wishlist_item_id, data)


@router.delete("/{wishlist_item_id}", status_code=204, response_class=Response)
async def delete_wishlist_item(
    wishlist_item_id: str,
    service: WishlistService = Depends(get_wishlist_service),
) -> None:
    """Delete a wishlist item."""
    await service.delete(wishlist_item_id)


# ------------------------------------------------------------------
# Acquisition endpoint
# ------------------------------------------------------------------


@router.post("/{wishlist_item_id}/acquire", response_model=WishlistItemResponse)
async def mark_wishlist_item_acquired(
    wishlist_item_id: str,
    data: WishlistAcquire,
    service: WishlistService = Depends(get_wishlist_service),
) -> WishlistItemResponse:
    """Mark a wishlist item as acquired.

    Links the wishlist item to a collection item representing the purchase.
    """
    return await service.mark_acquired(wishlist_item_id, data)


# ------------------------------------------------------------------
# Sightings endpoints
# ------------------------------------------------------------------


@router.get(
    "/{wishlist_item_id}/sightings",
    response_model=list[SightingResponse],
)
async def list_sightings(
    wishlist_item_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: WishlistService = Depends(get_wishlist_service),
) -> list[SightingResponse]:
    """List sightings for a wishlist item."""
    return await service.list_sightings(
        wishlist_item_id, skip=skip, limit=limit
    )


@router.post(
    "/{wishlist_item_id}/sightings",
    response_model=SightingResponse,
    status_code=201,
)
async def create_sighting(
    wishlist_item_id: str,
    data: SightingBody,
    service: WishlistService = Depends(get_wishlist_service),
) -> SightingResponse:
    """Create a new sighting for a wishlist item."""
    # Combine body with path parameter
    sighting_create = SightingCreate(
        wishlist_item_id=wishlist_item_id,
        **data.model_dump(),
    )
    return await service.create_sighting(sighting_create)
