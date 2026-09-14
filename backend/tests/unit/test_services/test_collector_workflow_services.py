"""Unit tests for collector-workflow services."""

from __future__ import annotations

from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.models import (
    Base,
    Catalog,
    CatalogItem,
    Collection,
    CollectionCatalog,
    CollectionItem,
    MainCategory,
    SubCategory,
    WishlistItem,
)
from api.schemas.collection_item import CollectionItemCreate
from api.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from api.schemas.quick_add import (
    CatalogItemQuickAdd,
    CatalogQuickAdd,
    SupplierQuickAdd,
)
from api.schemas.wishlist import WishlistAcquireAndAdd
from api.services.collection_catalog_service import CollectionCatalogService
from api.services.maintenance_service import MaintenanceService
from api.services.ownership_service import OwnershipService
from api.services.pending_service import PendingService
from api.services.quick_add_service import QuickAddService
from api.services.wishlist_service import WishlistService
from core.exceptions import NotFoundError, ValidationError

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    session = AsyncSession(engine, expire_on_commit=False)
    async with session:
        yield session
    await engine.dispose()


async def _seed(db: AsyncSession) -> tuple[Collection, Catalog, CatalogItem]:
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db.add(main)
    await db.flush()
    sub = SubCategory(main_category_id=main.id, name="Famicom", slug="famicom")
    db.add(sub)
    await db.flush()
    catalog = Catalog(sub_category_id=sub.id, name="Famicom Games")
    collection = Collection(name="Mi Famicom", collection_type="mixed")
    db.add_all([catalog, collection])
    await db.flush()
    item = CatalogItem(catalog_id=catalog.id, title="Dennou Kyusei Uranai")
    db.add(item)
    await db.commit()
    return collection, catalog, item


# --- Pending ---------------------------------------------------------------


async def test_pending_open_and_resolve(db: AsyncSession) -> None:
    svc = PendingService(db)
    p = await svc.open("supplier", "00000000-0000-0000-0000-000000000009",
                       ["type", "city"])
    assert p is not None and p.status == "open"
    opened = await svc.list()
    assert len(opened) == 1
    resolved = await svc.resolve(p.id, ["type"])
    assert resolved.missing_fields == ["city"]
    assert resolved.status == "open"
    resolved2 = await svc.resolve(p.id, ["city"])
    assert resolved2.status == "resolved"
    assert await svc.list() == []


async def test_pending_open_noop_when_no_missing(db: AsyncSession) -> None:
    svc = PendingService(db)
    assert await svc.open("catalog", "x", []) is None


# --- Collection <-> catalog N:M --------------------------------------------


async def test_associate_and_dissociate_catalog(db: AsyncSession) -> None:
    collection, catalog, _ = await _seed(db)
    svc = CollectionCatalogService(db)
    await svc.associate(collection.id, catalog.id, is_primary=True)
    assert [c.id for c in await svc.list_for_collection(collection.id)] == [
        catalog.id
    ]
    await svc.dissociate(collection.id, catalog.id)
    assert await svc.list_for_collection(collection.id) == []


# --- Quick-adds ------------------------------------------------------------


async def test_quick_add_supplier_opens_pending(db: AsyncSession) -> None:
    svc = QuickAddService(db)
    supplier = await svc.quick_add_supplier(
        SupplierQuickAdd(name="Suruga-ya")
    )
    assert supplier.id is not None
    pendings = await PendingService(db).list(entity_type="supplier")
    assert len(pendings) == 1
    assert "country" in pendings[0].missing_fields


async def test_quick_add_catalog_creates_and_links(db: AsyncSession) -> None:
    collection, _, _ = await _seed(db)
    svc = QuickAddService(db)
    catalog = await svc.quick_add_catalog(
        collection.id, CatalogQuickAdd(name="Zelda stuff", tematica="Zelda")
    )
    links = (
        await db.execute(
            select(CollectionCatalog).where(
                CollectionCatalog.collection_id == collection.id
            )
        )
    ).scalars().all()
    assert any(link.catalog_id == catalog.id for link in links)


async def test_quick_add_item_creates_catalog_and_collection_item(
    db: AsyncSession,
) -> None:
    collection, catalog, _ = await _seed(db)
    await CollectionCatalogService(db).associate(collection.id, catalog.id)
    svc = QuickAddService(db)
    ci = await svc.quick_add_catalog_item_and_collection_item(
        collection.id,
        CatalogItemQuickAdd(
            catalog_id=catalog.id,
            title="Un juego sin catalogar",
            collection_item=CollectionItemCreate(
                catalog_item_id="ignored", condition="good"
            ),
        ),
    )
    assert ci.id is not None
    # A pending for the new catalog item exists.
    pendings = await PendingService(db).list(entity_type="catalog_item")
    assert len(pendings) == 1


async def test_quick_add_item_requires_linked_catalog(db: AsyncSession) -> None:
    collection, catalog, _ = await _seed(db)
    svc = QuickAddService(db)
    with pytest.raises(ValidationError):
        await svc.quick_add_catalog_item_and_collection_item(
            collection.id,
            CatalogItemQuickAdd(
                catalog_id=catalog.id,
                title="X",
                collection_item=CollectionItemCreate(
                    catalog_item_id="ignored", condition="good"
                ),
            ),
        )


# --- Ownership -------------------------------------------------------------


async def test_ownership_reports_collections(db: AsyncSession) -> None:
    collection, _, item = await _seed(db)
    db.add(
        CollectionItem(
            collection_id=collection.id,
            catalog_item_id=item.id,
            condition="good",
        )
    )
    await db.commit()
    result = await OwnershipService(db).for_catalog_item(item.id)
    assert result["owned"] is True
    assert result["count"] == 1
    assert result["entries"][0]["collection_name"] == "Mi Famicom"


async def test_ownership_false_when_not_owned(db: AsyncSession) -> None:
    _, _, item = await _seed(db)
    result = await OwnershipService(db).for_catalog_item(item.id)
    assert result["owned"] is False


# --- Wishlist acquire-and-add ----------------------------------------------


async def test_acquire_and_create_from_wishlist(db: AsyncSession) -> None:
    collection, _, item = await _seed(db)
    wl = WishlistItem(collection_id=collection.id, catalog_item_id=item.id)
    db.add(wl)
    await db.commit()

    svc = WishlistService(db)
    updated = await svc.acquire_and_create(
        wl.id,
        WishlistAcquireAndAdd(
            collection_item=CollectionItemCreate(
                catalog_item_id="ignored", condition="near_mint"
            ),
            remove_from_wishlist=True,
        ),
    )
    assert updated.is_acquired is True
    assert updated.acquired_collection_item_id is not None
    assert updated.is_active is False
    # The collection item was created with the wishlist's catalog item.
    ci = (
        await db.execute(
            select(CollectionItem).where(
                CollectionItem.id == updated.acquired_collection_item_id
            )
        )
    ).scalar_one()
    assert ci.catalog_item_id == item.id
    assert ci.condition == "near_mint"


# --- Maintenance -----------------------------------------------------------


async def test_maintenance_create_list_due(db: AsyncSession) -> None:
    collection, _, item = await _seed(db)
    ci = CollectionItem(
        collection_id=collection.id, catalog_item_id=item.id, condition="good"
    )
    db.add(ci)
    await db.commit()

    svc = MaintenanceService(db)
    sched = await svc.create(
        ci.id,
        MaintenanceCreate(
            maintenance_type="battery",
            due_date=date(2020, 1, 1),
            notes="Cambiar pila",
        ),
    )
    due = await svc.list_due(before=date(2021, 1, 1))
    assert [s.id for s in due] == [sched.id]
    done = await svc.update(sched.id, MaintenanceUpdate(is_done=True))
    assert done.is_done is True
    assert await svc.list_due(before=date(2021, 1, 1)) == []
