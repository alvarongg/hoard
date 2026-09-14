"""REST endpoints for catalog price history and market value refresh."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_price_history_service
from api.schemas.price_history import (
    LatestPriceEntry,
    PriceHistoryCreate,
    PriceHistoryResponse,
    ValueUpdateResult,
)
from api.services.price_history_service import PriceHistoryService

router = APIRouter(tags=["price-history"])


@router.get(
    "/catalog-items/{catalog_item_id}/price-history",
    response_model=list[PriceHistoryResponse],
)
async def list_price_history(
    catalog_item_id: str,
    condition: str | None = Query(None),
    is_complete: bool | None = Query(None),
    region: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    service: PriceHistoryService = Depends(get_price_history_service),
) -> list[PriceHistoryResponse]:
    """List price records for a catalog item, newest first."""
    return await service.list(
        catalog_item_id,
        condition=condition,
        is_complete=is_complete,
        region=region,
        date_from=date_from,
        date_to=date_to,
    )


@router.post(
    "/catalog-items/{catalog_item_id}/price-history",
    response_model=PriceHistoryResponse,
    status_code=201,
)
async def create_price_history(
    catalog_item_id: str,
    data: PriceHistoryCreate,
    service: PriceHistoryService = Depends(get_price_history_service),
) -> PriceHistoryResponse:
    """Create a price record for a catalog item."""
    return await service.create(catalog_item_id, data)


@router.get(
    "/catalog-items/{catalog_item_id}/price-history/latest",
    response_model=list[LatestPriceEntry],
)
async def latest_price_history(
    catalog_item_id: str,
    service: PriceHistoryService = Depends(get_price_history_service),
) -> list[LatestPriceEntry]:
    """Return the latest price record per condition for a catalog item."""
    records = await service.latest_by_condition(catalog_item_id)
    return [
        LatestPriceEntry(
            condition=r.condition,
            is_complete=r.is_complete,
            price=r.price,
            currency=r.currency,
            price_date=r.price_date,
            source=r.source,
        )
        for r in records
    ]


@router.delete(
    "/price-history/{price_history_id}",
    status_code=204,
    response_class=Response,
)
async def delete_price_history(
    price_history_id: str,
    service: PriceHistoryService = Depends(get_price_history_service),
) -> None:
    """Delete a price record."""
    await service.delete(price_history_id)


@router.post(
    "/collection-items/{collection_item_id}/refresh-value",
    response_model=ValueUpdateResult,
)
async def refresh_collection_item_value(
    collection_item_id: str,
    service: PriceHistoryService = Depends(get_price_history_service),
) -> ValueUpdateResult:
    """Refresh a collection item's market value from the latest compatible price."""
    updated, item, reason = await service.refresh_item_market_value(
        collection_item_id
    )
    if not updated:
        return ValueUpdateResult(updated=False, reason=reason)
    return ValueUpdateResult(
        updated=True,
        current_market_value=item.current_market_value,
        value_source=item.value_source,
    )
