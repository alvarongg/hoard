"""REST endpoints for collections and collection items."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import (
    get_collection_item_service,
    get_collection_service,
    get_collection_stats_service,
)
from api.schemas.collection import (
    CollectionCreate,
    CollectionItemGroup,
    CollectionResponse,
    CollectionStats,
    CollectionUpdate,
)
from api.schemas.collection_item import (
    CollectionItemCreate,
    CollectionItemResponse,
    CollectionItemUpdate,
)
from api.services.collection_item_service import CollectionItemService
from api.services.collection_service import CollectionService
from api.services.collection_stats_service import CollectionStatsService

router = APIRouter(prefix="/collections", tags=["collections"])


# ------------------------------------------------------------------
# Collections
# ------------------------------------------------------------------


@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CollectionService = Depends(get_collection_service),
) -> list[CollectionResponse]:
    """List all active collections with pagination."""
    return await service.list(skip=skip, limit=limit)


@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(
    data: CollectionCreate,
    service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    """Create a new collection."""
    return await service.create(data)


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    """Get a single collection by id."""
    return await service.get_by_id(collection_id)


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    data: CollectionUpdate,
    service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    """Update a collection."""
    return await service.update(collection_id, data)


@router.delete("/{collection_id}", status_code=204, response_class=Response)
async def delete_collection(
    collection_id: str,
    service: CollectionService = Depends(get_collection_service),
) -> None:
    """Delete a collection."""
    await service.delete(collection_id)


@router.get(
    "/{collection_id}/items/grouped",
    response_model=list[CollectionItemGroup],
)
async def list_collection_items_grouped(
    collection_id: str,
    service: CollectionService = Depends(get_collection_service),
) -> list[CollectionItemGroup]:
    """List collection items grouped by main/sub category."""
    groups = await service.list_items_grouped(collection_id)
    return [CollectionItemGroup(**g) for g in groups]


@router.get(
    "/{collection_id}/stats",
    response_model=CollectionStats,
)
async def get_collection_stats(
    collection_id: str,
    service: CollectionStatsService = Depends(get_collection_stats_service),
) -> CollectionStats:
    """Get statistics for a collection."""
    return await service.get_collection_stats(collection_id)


# ------------------------------------------------------------------
# Collection items (nested under collection)
# ------------------------------------------------------------------


@router.get(
    "/{collection_id}/items",
    response_model=list[CollectionItemResponse],
)
async def list_collection_items(
    collection_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CollectionItemService = Depends(get_collection_item_service),
) -> list[CollectionItemResponse]:
    """List items for a collection with pagination."""
    return await service.list_by_collection(
        collection_id, skip=skip, limit=limit,
    )


@router.post(
    "/{collection_id}/items",
    response_model=CollectionItemResponse,
    status_code=201,
)
async def add_collection_item(
    collection_id: str,
    data: CollectionItemCreate,
    service: CollectionItemService = Depends(get_collection_item_service),
) -> CollectionItemResponse:
    """Add an item to a collection."""
    return await service.add_item(collection_id, data)


# ------------------------------------------------------------------
# Collection items (standalone endpoints)
# ------------------------------------------------------------------

items_router = APIRouter(prefix="/items", tags=["collection-items"])


@items_router.get("/{item_id}", response_model=CollectionItemResponse)
async def get_collection_item(
    item_id: str,
    service: CollectionItemService = Depends(get_collection_item_service),
) -> CollectionItemResponse:
    """Get a single collection item by id."""
    return await service.get_by_id(item_id)


@items_router.put("/{item_id}", response_model=CollectionItemResponse)
async def update_collection_item(
    item_id: str,
    data: CollectionItemUpdate,
    service: CollectionItemService = Depends(get_collection_item_service),
) -> CollectionItemResponse:
    """Update a collection item."""
    return await service.update(item_id, data)


@items_router.delete("/{item_id}", status_code=204, response_class=Response)
async def delete_collection_item(
    item_id: str,
    service: CollectionItemService = Depends(get_collection_item_service),
) -> None:
    """Delete a collection item."""
    await service.delete(item_id)
