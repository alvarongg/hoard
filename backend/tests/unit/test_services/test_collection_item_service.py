"""Unit tests for CollectionItemService business logic.

Tests cover all CRUD operations for CollectionItem, including category
compatibility validation for single_category collections, pagination,
and proper error handling.

Requirements: REQ-008, REQ-015
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.collection_item import CollectionItemCreate, CollectionItemUpdate
from api.services.collection_item_service import CollectionItemService
from core.exceptions import NotFoundError, ValidationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _engine():
    """Create an in-memory SQLite engine with all required tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(_engine) -> AsyncSession:
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture()
def service(db_session: AsyncSession) -> CollectionItemService:
    """Provide a CollectionItemService wired to the test session."""
    return CollectionItemService(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_sub_category(
    db_session: AsyncSession,
    name: str = "Consolas",
    slug: str = "consolas",
) -> SubCategory:
    """Create a MainCategory + SubCategory and return the SubCategory."""
    main = MainCategory(name=f"Main-{name}", slug=f"main-{slug}")
    db_session.add(main)
    await db_session.flush()

    sub = SubCategory(main_category_id=main.id, name=name, slug=slug)
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)
    return sub


async def _seed_catalog_and_item(
    db_session: AsyncSession,
    sub_category: SubCategory,
    title: str = "Zelda OoT",
) -> CatalogItem:
    """Create a Catalog + CatalogItem linked to the given sub-category."""
    catalog = Catalog(
        sub_category_id=sub_category.id,
        name=f"Catalog for {sub_category.name}",
    )
    db_session.add(catalog)
    await db_session.flush()

    item = CatalogItem(catalog_id=catalog.id, title=title)
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _seed_collection(
    db_session: AsyncSession,
    name: str = "My Collection",
    collection_type: str = "multi_category",
    sub_category_id: str | None = None,
) -> Collection:
    """Create a Collection directly via the model."""
    collection = Collection(
        name=name,
        collection_type=collection_type,
        restricted_to_sub_category_id=sub_category_id,
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection


def _item_create(
    catalog_item_id: str,
    condition: str = "good",
    **kwargs: object,
) -> CollectionItemCreate:
    """Build a CollectionItemCreate with sensible defaults."""
    return CollectionItemCreate(
        catalog_item_id=catalog_item_id,
        condition=condition,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Add item tests
# ---------------------------------------------------------------------------


class TestAddItem:
    """Tests for CollectionItemService.add_item."""

    @pytest.mark.asyncio
    async def test_add_item_to_collection_returns_item(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        catalog_item = await _seed_catalog_and_item(db_session, sub)
        collection = await _seed_collection(db_session)

        data = _item_create(catalog_item.id, condition="excellent")
        result = await service.add_item(collection.id, data)

        assert result.id is not None
        assert result.collection_id == collection.id
        assert result.catalog_item_id == catalog_item.id
        assert result.condition == "excellent"

    @pytest.mark.asyncio
    async def test_add_item_to_single_category_with_matching_sub_succeeds(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        catalog_item = await _seed_catalog_and_item(db_session, sub)
        collection = await _seed_collection(
            db_session,
            collection_type="single_category",
            sub_category_id=sub.id,
        )

        data = _item_create(catalog_item.id)
        result = await service.add_item(collection.id, data)

        assert result.collection_id == collection.id

    @pytest.mark.asyncio
    async def test_add_item_to_wrong_category_raises_validation_error(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub_a = await _seed_sub_category(db_session, name="Games", slug="games")
        sub_b = await _seed_sub_category(db_session, name="Music", slug="music")
        catalog_item = await _seed_catalog_and_item(db_session, sub_b)
        collection = await _seed_collection(
            db_session,
            collection_type="single_category",
            sub_category_id=sub_a.id,
        )

        data = _item_create(catalog_item.id)

        with pytest.raises(ValidationError, match="sub-categoría"):
            await service.add_item(collection.id, data)

    @pytest.mark.asyncio
    async def test_add_item_to_nonexistent_collection_raises_not_found(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        catalog_item = await _seed_catalog_and_item(db_session, sub)
        data = _item_create(catalog_item.id)

        with pytest.raises(NotFoundError, match="Collection"):
            await service.add_item("nonexistent-uuid", data)

    @pytest.mark.asyncio
    async def test_add_item_with_nonexistent_catalog_item_raises_not_found(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        collection = await _seed_collection(db_session)
        data = _item_create("nonexistent-catalog-item-id")

        with pytest.raises(NotFoundError, match="Catalog item"):
            await service.add_item(collection.id, data)


# ---------------------------------------------------------------------------
# Get by id tests
# ---------------------------------------------------------------------------


class TestGetById:
    """Tests for CollectionItemService.get_by_id."""

    @pytest.mark.asyncio
    async def test_get_existing_item_returns_item(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        catalog_item = await _seed_catalog_and_item(db_session, sub)
        collection = await _seed_collection(db_session)
        created = await service.add_item(
            collection.id, _item_create(catalog_item.id),
        )

        fetched = await service.get_by_id(created.id)

        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_item_raises_not_found(
        self,
        service: CollectionItemService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_by_id("nonexistent-uuid")


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------


class TestUpdateItem:
    """Tests for CollectionItemService.update."""

    @pytest.mark.asyncio
    async def test_update_partial_fields_updates_only_provided(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        catalog_item = await _seed_catalog_and_item(db_session, sub)
        collection = await _seed_collection(db_session)
        created = await service.add_item(
            collection.id,
            _item_create(catalog_item.id, condition="good", notes="original"),
        )

        updated = await service.update(
            created.id, CollectionItemUpdate(condition="mint"),
        )

        assert updated.condition == "mint"
        assert updated.notes == "original"  # unchanged

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises_not_found(
        self,
        service: CollectionItemService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.update(
                "nonexistent-uuid",
                CollectionItemUpdate(condition="mint"),
            )


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


class TestDeleteItem:
    """Tests for CollectionItemService.delete."""

    @pytest.mark.asyncio
    async def test_delete_item_removes_from_collection(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        catalog_item = await _seed_catalog_and_item(db_session, sub)
        collection = await _seed_collection(db_session)
        created = await service.add_item(
            collection.id, _item_create(catalog_item.id),
        )

        await service.delete(created.id)

        with pytest.raises(NotFoundError):
            await service.get_by_id(created.id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_not_found(
        self,
        service: CollectionItemService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-uuid")


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------


class TestListByCollection:
    """Tests for CollectionItemService.list_by_collection."""

    @pytest.mark.asyncio
    async def test_list_items_with_pagination_returns_correct_count(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        collection = await _seed_collection(db_session)

        for i in range(5):
            ci = await _seed_catalog_and_item(db_session, sub, title=f"Item {i}")
            await service.add_item(collection.id, _item_create(ci.id))

        result = await service.list_by_collection(
            collection.id, skip=1, limit=2,
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_empty_collection_returns_empty_list(
        self,
        service: CollectionItemService,
        db_session: AsyncSession,
    ) -> None:
        collection = await _seed_collection(db_session)

        result = await service.list_by_collection(collection.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_nonexistent_collection_raises_not_found(
        self,
        service: CollectionItemService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.list_by_collection("nonexistent-uuid")
