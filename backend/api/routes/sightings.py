"""REST endpoints for wishlist sightings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from api.dependencies import get_wishlist_service
from api.schemas.wishlist import SightingResponse, SightingUpdate
from api.services.wishlist_service import WishlistService

router = APIRouter(prefix="/sightings", tags=["sightings"])


@router.put("/{sighting_id}", response_model=SightingResponse)
async def update_sighting(
    sighting_id: str,
    data: SightingUpdate,
    service: WishlistService = Depends(get_wishlist_service),
) -> SightingResponse:
    """Update a sighting."""
    return await service.update_sighting(sighting_id, data)


@router.delete("/{sighting_id}", status_code=204, response_class=Response)
async def delete_sighting(
    sighting_id: str,
    service: WishlistService = Depends(get_wishlist_service),
) -> None:
    """Delete a sighting."""
    await service.delete_sighting(sighting_id)
