"""Search routes for catalog items.

Requirements: 6.5, 6.8, 19.6
"""

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_search_service
from api.schemas.search import (
    CatalogSearchResult,
    CatalogSearchParams,
    SearchMode,
)
from api.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/catalog-items", response_model=CatalogSearchResult)
async def search_catalog_items(
    q: str | None = Query(None, description="Search query string"),
    main_category_id: str | None = Query(None, description="Filter by main category UUID"),
    sub_category_id: str | None = Query(None, description="Filter by sub-category UUID"),
    language: str | None = Query(None, description="Filter by language"),
    region: str | None = Query(None, description="Filter by region"),
    manufacturer: str | None = Query(None, description="Filter by manufacturer"),
    publisher: str | None = Query(None, description="Filter by publisher"),
    developer: str | None = Query(None, description="Filter by developer"),
    brand: str | None = Query(None, description="Filter by brand"),
    rarity: str | None = Query(None, description="Filter by rarity"),
    year_min: int | None = Query(None, ge=1800, le=2200, description="Minimum release year"),
    year_max: int | None = Query(None, ge=1800, le=2200, description="Maximum release year"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of results"),
    service: SearchService = Depends(get_search_service),
) -> CatalogSearchResult:
    """Search catalog items with optional filters.

    Returns paginated results with the total count and search mode used.
    """
    params = CatalogSearchParams(
        q=q,
        main_category_id=main_category_id,
        sub_category_id=sub_category_id,
        language=language,
        region=region,
        manufacturer=manufacturer,
        publisher=publisher,
        developer=developer,
        brand=brand,
        rarity=rarity,
        year_min=year_min,
        year_max=year_max,
        skip=skip,
        limit=limit,
    )
    return await service.search_catalog_items(params)
