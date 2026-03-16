"""REST endpoints for main categories and sub-categories."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_category_service
from api.schemas.category import (
    MainCategoryCreate,
    MainCategoryResponse,
    MainCategoryUpdate,
    SubCategoryCreate,
    SubCategoryResponse,
    SubCategoryUpdate,
)
from api.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


# ------------------------------------------------------------------
# Main categories
# ------------------------------------------------------------------


@router.get("", response_model=list[MainCategoryResponse])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CategoryService = Depends(get_category_service),
) -> list[MainCategoryResponse]:
    """List all main categories with pagination."""
    return await service.list_main(skip=skip, limit=limit)


@router.post("", response_model=MainCategoryResponse, status_code=201)
async def create_category(
    data: MainCategoryCreate,
    service: CategoryService = Depends(get_category_service),
) -> MainCategoryResponse:
    """Create a new main category."""
    return await service.create_main(data)


@router.get("/{category_id}", response_model=MainCategoryResponse)
async def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
) -> MainCategoryResponse:
    """Get a single main category by id."""
    return await service.get_main(category_id)


@router.put("/{category_id}", response_model=MainCategoryResponse)
async def update_category(
    category_id: str,
    data: MainCategoryUpdate,
    service: CategoryService = Depends(get_category_service),
) -> MainCategoryResponse:
    """Update a main category."""
    return await service.update_main(category_id, data)


@router.delete(
    "/{category_id}", status_code=204, response_class=Response
)
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
) -> None:
    """Delete a main category."""
    await service.delete_main(category_id)


# ------------------------------------------------------------------
# Sub-categories (nested under main category)
# ------------------------------------------------------------------


@router.get(
    "/{category_id}/subcategories",
    response_model=list[SubCategoryResponse],
)
async def list_subcategories(
    category_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CategoryService = Depends(get_category_service),
) -> list[SubCategoryResponse]:
    """List sub-categories for a main category with pagination."""
    return await service.list_sub(
        main_category_id=category_id, skip=skip, limit=limit
    )


@router.post(
    "/{category_id}/subcategories",
    response_model=SubCategoryResponse,
    status_code=201,
)
async def create_subcategory(
    category_id: str,
    data: SubCategoryCreate,
    service: CategoryService = Depends(get_category_service),
) -> SubCategoryResponse:
    """Create a new sub-category under a main category."""
    return await service.create_sub(data)


# ------------------------------------------------------------------
# Sub-categories (standalone endpoints)
# ------------------------------------------------------------------

subcategories_router = APIRouter(
    prefix="/subcategories", tags=["subcategories"]
)


@subcategories_router.get(
    "/{sub_category_id}", response_model=SubCategoryResponse
)
async def get_subcategory(
    sub_category_id: str,
    service: CategoryService = Depends(get_category_service),
) -> SubCategoryResponse:
    """Get a single sub-category by id."""
    return await service.get_sub(sub_category_id)


@subcategories_router.put(
    "/{sub_category_id}", response_model=SubCategoryResponse
)
async def update_subcategory(
    sub_category_id: str,
    data: SubCategoryUpdate,
    service: CategoryService = Depends(get_category_service),
) -> SubCategoryResponse:
    """Update a sub-category."""
    return await service.update_sub(sub_category_id, data)


@subcategories_router.delete(
    "/{sub_category_id}", status_code=204, response_class=Response
)
async def delete_subcategory(
    sub_category_id: str,
    service: CategoryService = Depends(get_category_service),
) -> None:
    """Delete a sub-category."""
    await service.delete_sub(sub_category_id)
