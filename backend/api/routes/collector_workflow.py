"""REST endpoints for the collector-workflow feature."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from api.dependencies import (
    get_collection_catalog_service,
    get_maintenance_service,
    get_ownership_service,
    get_pending_service,
    get_price_lookup_service,
    get_quick_add_service,
)
from api.schemas.catalog import CatalogResponse
from api.schemas.collection_item import CollectionItemResponse
from api.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from api.schemas.pending import PendingResolve, PendingResponse
from api.schemas.price_history import PriceHistoryResponse
from api.schemas.quick_add import (
    CatalogItemQuickAdd,
    CatalogQuickAdd,
    SupplierQuickAdd,
)
from api.schemas.supplier import SupplierResponse
from api.services.collection_catalog_service import CollectionCatalogService
from api.services.maintenance_service import MaintenanceService
from api.services.ownership_service import OwnershipService
from api.services.pending_service import PendingService
from api.services.price_lookup_service import PriceLookupService
from api.services.quick_add_service import QuickAddService

# Collection <-> catalog association + quick-adds live under /collections.
collections_router = APIRouter(prefix="/collections", tags=["collection-catalogs"])
# Ownership + price lookup live under /catalog-items.
catalog_items_router = APIRouter(prefix="/catalog-items", tags=["ownership"])
# Maintenance under /collection-items and /maintenance.
maintenance_router = APIRouter(tags=["maintenance"])
# Suppliers quick-add.
suppliers_router = APIRouter(prefix="/suppliers", tags=["suppliers"])
# Pending completions.
pending_router = APIRouter(prefix="/pending", tags=["pending"])


# ---------------------------------------------------------------------------
# Collection <-> catalog (N:M)
# ---------------------------------------------------------------------------


class AssociateCatalogRequest(BaseModel):
    catalog_id: str
    is_primary: bool = False


@collections_router.get(
    "/{collection_id}/catalogs", response_model=list[CatalogResponse]
)
async def list_collection_catalogs(
    collection_id: str,
    service: CollectionCatalogService = Depends(get_collection_catalog_service),
) -> list[CatalogResponse]:
    return await service.list_for_collection(collection_id)


@collections_router.post(
    "/{collection_id}/catalogs", response_model=CatalogResponse, status_code=201
)
async def associate_catalog(
    collection_id: str,
    body: AssociateCatalogRequest,
    service: CollectionCatalogService = Depends(get_collection_catalog_service),
) -> CatalogResponse:
    await service.associate(collection_id, body.catalog_id, body.is_primary)
    catalogs = await service.list_for_collection(collection_id)
    return next(c for c in catalogs if c.id == body.catalog_id)


@collections_router.delete(
    "/{collection_id}/catalogs/{catalog_id}",
    status_code=204,
    response_class=Response,
)
async def dissociate_catalog(
    collection_id: str,
    catalog_id: str,
    service: CollectionCatalogService = Depends(get_collection_catalog_service),
) -> Response:
    await service.dissociate(collection_id, catalog_id)
    return Response(status_code=204)


@collections_router.post(
    "/{collection_id}/catalogs/quick",
    response_model=CatalogResponse,
    status_code=201,
)
async def quick_add_catalog(
    collection_id: str,
    body: CatalogQuickAdd,
    service: QuickAddService = Depends(get_quick_add_service),
) -> CatalogResponse:
    return await service.quick_add_catalog(collection_id, body)


@collections_router.post(
    "/{collection_id}/items/quick",
    response_model=CollectionItemResponse,
    status_code=201,
)
async def quick_add_item(
    collection_id: str,
    body: CatalogItemQuickAdd,
    service: QuickAddService = Depends(get_quick_add_service),
) -> CollectionItemResponse:
    return await service.quick_add_catalog_item_and_collection_item(
        collection_id, body
    )


# ---------------------------------------------------------------------------
# Supplier quick-add
# ---------------------------------------------------------------------------


@suppliers_router.post(
    "/quick", response_model=SupplierResponse, status_code=201
)
async def quick_add_supplier(
    body: SupplierQuickAdd,
    service: QuickAddService = Depends(get_quick_add_service),
) -> SupplierResponse:
    return await service.quick_add_supplier(body)


# ---------------------------------------------------------------------------
# Ownership + price lookup
# ---------------------------------------------------------------------------


class PriceLookupRequest(BaseModel):
    url: str


@catalog_items_router.get("/{catalog_item_id}/ownership")
async def get_ownership(
    catalog_item_id: str,
    service: OwnershipService = Depends(get_ownership_service),
) -> dict:
    return await service.for_catalog_item(catalog_item_id)


@catalog_items_router.post(
    "/{catalog_item_id}/price-lookup",
    response_model=list[PriceHistoryResponse],
)
async def price_lookup(
    catalog_item_id: str,
    body: PriceLookupRequest,
    service: PriceLookupService = Depends(get_price_lookup_service),
) -> list[PriceHistoryResponse]:
    return await service.lookup(catalog_item_id, body.url)


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


@maintenance_router.get(
    "/collection-items/{collection_item_id}/maintenance",
    response_model=list[MaintenanceResponse],
)
async def list_maintenance(
    collection_item_id: str,
    service: MaintenanceService = Depends(get_maintenance_service),
) -> list[MaintenanceResponse]:
    return await service.list_for_item(collection_item_id)


@maintenance_router.post(
    "/collection-items/{collection_item_id}/maintenance",
    response_model=MaintenanceResponse,
    status_code=201,
)
async def create_maintenance(
    collection_item_id: str,
    body: MaintenanceCreate,
    service: MaintenanceService = Depends(get_maintenance_service),
) -> MaintenanceResponse:
    return await service.create(collection_item_id, body)


@maintenance_router.put(
    "/maintenance/{schedule_id}", response_model=MaintenanceResponse
)
async def update_maintenance(
    schedule_id: str,
    body: MaintenanceUpdate,
    service: MaintenanceService = Depends(get_maintenance_service),
) -> MaintenanceResponse:
    return await service.update(schedule_id, body)


@maintenance_router.delete(
    "/maintenance/{schedule_id}", status_code=204, response_class=Response
)
async def delete_maintenance(
    schedule_id: str,
    service: MaintenanceService = Depends(get_maintenance_service),
) -> Response:
    await service.delete(schedule_id)
    return Response(status_code=204)


@maintenance_router.get(
    "/maintenance/due", response_model=list[MaintenanceResponse]
)
async def list_due_maintenance(
    before: date | None = Query(None),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> list[MaintenanceResponse]:
    return await service.list_due(before)


# ---------------------------------------------------------------------------
# Pending completions
# ---------------------------------------------------------------------------


@pending_router.get("", response_model=list[PendingResponse])
async def list_pending(
    status: str = Query("open"),
    entity_type: str | None = Query(None),
    service: PendingService = Depends(get_pending_service),
) -> list[PendingResponse]:
    return await service.list(status=status, entity_type=entity_type)


@pending_router.put("/{pending_id}/resolve", response_model=PendingResponse)
async def resolve_pending(
    pending_id: str,
    body: PendingResolve,
    service: PendingService = Depends(get_pending_service),
) -> PendingResponse:
    return await service.resolve(pending_id, body.completed_fields)
