"""REST endpoints for data export."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_export_service
from api.schemas.export import CollectionExport, WishlistExport
from api.services.export_service import ExportService
from core.exceptions import ValidationError

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/collections/{collection_id}", response_model=CollectionExport)
async def export_collection(
    collection_id: str,
    service: ExportService = Depends(get_export_service),
) -> Response:
    payload = await service.export_collection(collection_id)
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="collection-{collection_id}.json"'
            )
        },
    )


@router.get("/catalogs/{catalog_id}")
async def export_catalog(
    catalog_id: str,
    format: str = Query("json"),
    service: ExportService = Depends(get_export_service),
) -> Response:
    if format == "json":
        payload = await service.export_catalog_json(catalog_id)
        return Response(
            content=payload.model_dump_json(),
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="catalog-{catalog_id}.json"'
                )
            },
        )
    if format == "csv":
        content = await service.export_catalog_csv(catalog_id)
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="catalog-{catalog_id}.csv"'
                )
            },
        )
    raise ValidationError(f"Unsupported export format: {format}")


@router.get("/wishlist", response_model=WishlistExport)
async def export_wishlist(
    service: ExportService = Depends(get_export_service),
) -> Response:
    payload = await service.export_wishlist()
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="wishlist.json"'
        },
    )
