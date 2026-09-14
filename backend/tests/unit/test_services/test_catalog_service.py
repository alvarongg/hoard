"""Unit tests for CatalogService business logic.

Tests cover all CRUD operations for Catalog and CatalogItem,
including validation rules, duplicate detection, search, and deletion.

Requirements: REQ-005, REQ-006, REQ-015
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.schemas.catalog import (
    CatalogCreate,
    CatalogItemCreate,
    CatalogItemUpdate,
    CatalogUpdate,
)
from api.services.catalog_service import CatalogService
from core.exceptions import DuplicateError, NotFoundError, ValidationError


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
def service(db_session: AsyncSession) -> CatalogService:
    """Provide a CatalogService wired to the test session."""
    return CatalogService(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_main(db_session: AsyncSession, name: str = "Videojuegos") -> MainCategory:
    """Create and return a MainCategory."""
    main = MainCategory(name=name, slug=name.lower().replace(" ", "-"))
    db_session.add(main)
    await db_session.commit()
    await db_session.refresh(main)
    return main


async def _seed_sub(
    db_session: AsyncSession,
    main_id: str,
    name: str = "Consolas",
) -> SubCategory:
    """Create and return a SubCategory linked to a MainCategory."""
    sub = SubCategory(
        main_category_id=main_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)
    return sub


async def _seed_catalog(
    service: CatalogService,
    sub_category_id: str,
    name: str = "N64 Games",
) -> Catalog:
    """Create and return a Catalog via the service."""
    data = CatalogCreate(
        name=name,
        sub_category_id=sub_category_id,
    )
    return await service.create_catalog(data)


async def _seed_item(
    service: CatalogService,
    catalog_id: str,
    title: str = "Super Mario 64",
) -> CatalogItem:
    """Create and return a CatalogItem via the service."""
    data = CatalogItemCreate(
        catalog_id=catalog_id,
        title=title,
    )
    return await service.create_item(catalog_id, data)


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------


class TestListCatalogs:
    """Tests for CatalogService.list_catalogs."""

    @pytest.mark.asyncio
    async def test_list_catalogs_returns_ordered_by_name(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)

        await _seed_catalog(service, sub.id, name="Zelda Catalog")
        await _seed_catalog(service, sub.id, name="Atari Catalog")
        await _seed_catalog(service, sub.id, name="Mario Catalog")

        result = await service.list_catalogs()

        assert len(result) == 3
        assert [c.name for c in result] == [
            "Atari Catalog", "Mario Catalog", "Zelda Catalog",
        ]

    @pytest.mark.asyncio
    async def test_list_catalogs_empty_returns_empty_list(
        self, service: CatalogService,
    ) -> None:
        result = await service.list_catalogs()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_catalogs_respects_pagination(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)

        for i in range(5):
            await _seed_catalog(service, sub.id, name=f"Cat{i:02d}")

        result = await service.list_catalogs(skip=1, limit=2)
        assert len(result) == 2
        assert result[0].name == "Cat01"
        assert result[1].name == "Cat02"


class TestGetCatalog:
    """Tests for CatalogService.get_catalog."""

    @pytest.mark.asyncio
    async def test_get_catalog_nonexistent_raises_not_found(
        self, service: CatalogService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_catalog("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_get_catalog_existing_returns_catalog(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        created = await _seed_catalog(service, sub.id)

        fetched = await service.get_catalog(created.id)
        assert fetched.id == created.id
        assert fetched.name == created.name


class TestCreateCatalog:
    """Tests for CatalogService.create_catalog."""

    @pytest.mark.asyncio
    async def test_create_catalog_with_valid_subcategory_returns_catalog(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)

        data = CatalogCreate(
            name="SNES Games",
            sub_category_id=sub.id,
            description="All SNES titles",
        )
        result = await service.create_catalog(data)

        assert result.id is not None
        assert result.name == "SNES Games"
        assert result.sub_category_id == sub.id
        assert result.description == "All SNES titles"

    @pytest.mark.asyncio
    async def test_create_catalog_with_nonexistent_subcategory_raises_validation_error(
        self, service: CatalogService,
    ) -> None:
        data = CatalogCreate(
            name="Orphan Catalog",
            sub_category_id="nonexistent-uuid",
        )
        with pytest.raises(ValidationError, match="does not exist"):
            await service.create_catalog(data)

    @pytest.mark.asyncio
    async def test_create_catalog_duplicate_name_same_subcategory_raises_duplicate_error(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        await _seed_catalog(service, sub.id, name="Duplicated")

        with pytest.raises(DuplicateError, match="Duplicated"):
            await _seed_catalog(service, sub.id, name="Duplicated")

    @pytest.mark.asyncio
    async def test_create_catalog_same_name_different_subcategory_succeeds(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub_a = await _seed_sub(db_session, main.id, name="Sub A")
        sub_b = await _seed_sub(db_session, main.id, name="Sub B")

        await _seed_catalog(service, sub_a.id, name="Same Name")
        result = await _seed_catalog(service, sub_b.id, name="Same Name")

        assert result.name == "Same Name"
        assert result.sub_category_id == sub_b.id


class TestUpdateCatalog:
    """Tests for CatalogService.update_catalog."""

    @pytest.mark.asyncio
    async def test_update_catalog_with_valid_data_returns_updated(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        created = await _seed_catalog(service, sub.id, name="Old Name")

        updated = await service.update_catalog(
            created.id, CatalogUpdate(name="New Name", description="Updated"),
        )

        assert updated.name == "New Name"
        assert updated.description == "Updated"
        assert updated.id == created.id

    @pytest.mark.asyncio
    async def test_update_catalog_duplicate_name_raises_duplicate_error(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        await _seed_catalog(service, sub.id, name="Existing")
        target = await _seed_catalog(service, sub.id, name="Target")

        with pytest.raises(DuplicateError, match="Existing"):
            await service.update_catalog(
                target.id, CatalogUpdate(name="Existing"),
            )

    @pytest.mark.asyncio
    async def test_update_catalog_same_name_no_error(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        created = await _seed_catalog(service, sub.id, name="Keep")

        updated = await service.update_catalog(
            created.id, CatalogUpdate(name="Keep"),
        )
        assert updated.name == "Keep"


class TestDeleteCatalog:
    """Tests for CatalogService.delete_catalog."""

    @pytest.mark.asyncio
    async def test_delete_catalog_succeeds(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        created = await _seed_catalog(service, sub.id)

        await service.delete_catalog(created.id)

        with pytest.raises(NotFoundError):
            await service.get_catalog(created.id)

    @pytest.mark.asyncio
    async def test_delete_catalog_nonexistent_raises_not_found(
        self, service: CatalogService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.delete_catalog("nonexistent-uuid")


# ---------------------------------------------------------------------------
# CatalogItem tests
# ---------------------------------------------------------------------------


class TestListItems:
    """Tests for CatalogService.list_items."""

    @pytest.mark.asyncio
    async def test_list_items_filters_by_catalog_id(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat_a = await _seed_catalog(service, sub.id, name="Catalog A")
        cat_b = await _seed_catalog(service, sub.id, name="Catalog B")

        await _seed_item(service, cat_a.id, title="Item A1")
        await _seed_item(service, cat_a.id, title="Item A2")
        await _seed_item(service, cat_b.id, title="Item B1")

        result_a = await service.list_items(cat_a.id)
        result_b = await service.list_items(cat_b.id)

        assert len(result_a) == 2
        assert all(i.catalog_id == cat_a.id for i in result_a)
        assert len(result_b) == 1
        assert result_b[0].catalog_id == cat_b.id

    @pytest.mark.asyncio
    async def test_list_items_returns_ordered_by_title(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)

        await _seed_item(service, cat.id, title="Zelda")
        await _seed_item(service, cat.id, title="Asteroids")
        await _seed_item(service, cat.id, title="Mario")

        result = await service.list_items(cat.id)

        assert [i.title for i in result] == ["Asteroids", "Mario", "Zelda"]


class TestGetItem:
    """Tests for CatalogService.get_item."""

    @pytest.mark.asyncio
    async def test_get_item_nonexistent_raises_not_found(
        self, service: CatalogService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_item("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_get_item_existing_returns_item(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        created = await _seed_item(service, cat.id)

        fetched = await service.get_item(created.id)
        assert fetched.id == created.id
        assert fetched.title == created.title


class TestCreateItem:
    """Tests for CatalogService.create_item."""

    @pytest.mark.asyncio
    async def test_create_item_with_valid_catalog_returns_item(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)

        data = CatalogItemCreate(
            catalog_id=cat.id,
            title="GoldenEye 007",
            manufacturer="Rare",
            region="NTSC",
        )
        result = await service.create_item(cat.id, data)

        assert result.id is not None
        assert result.title == "GoldenEye 007"
        assert result.catalog_id == cat.id
        assert result.manufacturer == "Rare"
        assert result.region == "NTSC"

    @pytest.mark.asyncio
    async def test_create_item_with_nonexistent_catalog_raises_not_found(
        self, service: CatalogService,
    ) -> None:
        data = CatalogItemCreate(
            catalog_id="nonexistent-uuid",
            title="Orphan Item",
        )
        with pytest.raises(NotFoundError, match="not found"):
            await service.create_item("nonexistent-uuid", data)

    @pytest.mark.asyncio
    async def test_create_catalog_item_works_correctly(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        """Verify create_item returns a properly persisted item."""
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)

        item = await _seed_item(service, cat.id, title="Banjo-Kazooie")

        fetched = await service.get_item(item.id)
        assert fetched.title == "Banjo-Kazooie"
        assert fetched.catalog_id == cat.id

    @pytest.mark.asyncio
    async def test_create_item_increments_catalog_total_items_by_one(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        """Creating a single item bumps the parent catalog counter by one."""
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        initial_total = cat.total_items or 0

        await _seed_item(service, cat.id, title="Diddy Kong Racing")

        refreshed = await service.get_catalog(cat.id)
        await db_session.refresh(refreshed)
        assert refreshed.total_items == initial_total + 1

    @pytest.mark.asyncio
    async def test_create_item_multiple_times_reflects_correct_total_items(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        """total_items matches the real item count after several inserts."""
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        initial_total = cat.total_items or 0

        titles = ["Perfect Dark", "Star Fox 64", "F-Zero X", "Wave Race 64"]
        for title in titles:
            await _seed_item(service, cat.id, title=title)

        refreshed = await service.get_catalog(cat.id)
        await db_session.refresh(refreshed)
        items = await service.list_items(cat.id)

        assert refreshed.total_items == initial_total + len(titles)
        assert refreshed.total_items == len(items)

    @pytest.mark.asyncio
    async def test_create_item_does_not_affect_other_catalog_total_items(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        """Only the target catalog counter changes."""
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        target = await _seed_catalog(service, sub.id, name="Target Catalog")
        other = await _seed_catalog(service, sub.id, name="Other Catalog")
        other_initial = other.total_items or 0

        await _seed_item(service, target.id, title="Mario Party")

        refreshed_other = await service.get_catalog(other.id)
        await db_session.refresh(refreshed_other)
        assert refreshed_other.total_items == other_initial


class TestUpdateItem:
    """Tests for CatalogService.update_item."""

    @pytest.mark.asyncio
    async def test_update_item_partial_fields(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        item = await _seed_item(service, cat.id, title="Original Title")

        updated = await service.update_item(
            item.id,
            CatalogItemUpdate(manufacturer="Nintendo", rarity="Rare"),
        )

        assert updated.manufacturer == "Nintendo"
        assert updated.rarity == "Rare"
        assert updated.title == "Original Title"  # unchanged


class TestDeleteItem:
    """Tests for CatalogService.delete_item."""

    @pytest.mark.asyncio
    async def test_delete_item_succeeds(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        item = await _seed_item(service, cat.id)

        await service.delete_item(item.id)

        with pytest.raises(NotFoundError):
            await service.get_item(item.id)

    @pytest.mark.asyncio
    async def test_delete_item_nonexistent_raises_not_found(
        self, service: CatalogService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.delete_item("nonexistent-uuid")


# ---------------------------------------------------------------------------
# Search tests
# ---------------------------------------------------------------------------


class TestSearchItems:
    """Tests for CatalogService.search_items."""

    @pytest.mark.asyncio
    async def test_search_catalog_items_by_title_returns_matches(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)

        await _seed_item(service, cat.id, title="Super Mario 64")
        await _seed_item(service, cat.id, title="Mario Kart 64")
        await _seed_item(service, cat.id, title="GoldenEye 007")

        result = await service.search_items("Mario")

        assert len(result) == 2
        titles = {i.title for i in result}
        assert "Super Mario 64" in titles
        assert "Mario Kart 64" in titles

    @pytest.mark.asyncio
    async def test_search_catalog_items_no_match_returns_empty(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        await _seed_item(service, cat.id, title="Super Mario 64")

        result = await service.search_items("Zelda")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_items_case_insensitive(
        self, service: CatalogService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(db_session)
        sub = await _seed_sub(db_session, main.id)
        cat = await _seed_catalog(service, sub.id)
        await _seed_item(service, cat.id, title="Super Mario 64")

        result = await service.search_items("super mario")
        assert len(result) == 1
        assert result[0].title == "Super Mario 64"
