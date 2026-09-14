"""REST endpoints for item components."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_item_component_service
from api.schemas.item_component import (
    CompletenessResult,
    ComponentTemplateEntry,
    ItemComponentCreate,
    ItemComponentResponse,
    ItemComponentUpdate,
)
from api.services.item_component_service import ItemComponentService
from core.exceptions import NotFoundError

# Router for collection-item-scoped endpoints
collection_items_router = APIRouter(
    prefix="/collection-items",
    tags=["item-components"],
)

# Router for item-components-scoped endpoints
item_components_router = APIRouter(
    prefix="/item-components",
    tags=["item-components"],
)


@collection_items_router.get(
    "/{collection_item_id}/components/template",
    response_model=list[ComponentTemplateEntry],
    summary="Get component template for a collection item",
)
async def get_component_template(
    collection_item_id: str,
    service: ItemComponentService = Depends(get_item_component_service),
) -> list[ComponentTemplateEntry]:
    """Get the component template for a collection item's sub-category.

    Returns the standard components defined for the item's sub-category,
    along with any recorded presence.
    """
    try:
        return await service.get_template(collection_item_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@collection_items_router.get(
    "/{collection_item_id}/components",
    response_model=list[ItemComponentResponse],
    summary="List components for a collection item",
)
async def list_item_components(
    collection_item_id: str,
    service: ItemComponentService = Depends(get_item_component_service),
) -> list[ItemComponentResponse]:
    """List all components for a collection item."""
    try:
        return await service.list(collection_item_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@collection_items_router.post(
    "/{collection_item_id}/components",
    response_model=ItemComponentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a component",
)
async def upsert_item_component(
    collection_item_id: str,
    data: ItemComponentCreate,
    service: ItemComponentService = Depends(get_item_component_service),
) -> ItemComponentResponse:
    """Create or update an item component.

    If a component with the same standard_component_id exists for this
    collection item, it will be updated. Otherwise, a new component is created.

    The response includes the updated completeness status via the
    X-Completeness-Result header.
    """
    try:
        component, _completeness = await service.upsert(collection_item_id, data)
        return component  # type: ignore
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@item_components_router.put(
    "/{component_id}",
    response_model=ItemComponentResponse,
    summary="Update a component",
)
async def update_item_component(
    component_id: str,
    data: ItemComponentUpdate,
    service: ItemComponentService = Depends(get_item_component_service),
) -> ItemComponentResponse:
    """Partially update an item component.

    Only the provided fields will be updated.
    """
    try:
        component, _completeness = await service.update(component_id, data)
        return component  # type: ignore
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@item_components_router.delete(
    "/{component_id}",
    response_model=CompletenessResult,
    summary="Delete a component",
)
async def delete_item_component(
    component_id: str,
    service: ItemComponentService = Depends(get_item_component_service),
) -> CompletenessResult:
    """Delete an item component.

    Returns the updated completeness status for the parent collection item.
    """
    try:
        return await service.delete(component_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
