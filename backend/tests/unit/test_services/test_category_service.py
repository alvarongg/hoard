"""Unit tests for CategoryService business logic.

Tests cover all CRUD operations for MainCategory and SubCategory,
including validation rules, duplicate detection, and deletion constraints.

Requirements: REQ-004, REQ-015
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog
from api.models.category import MainCategory, SubCategory
from api.schemas.category import (
    MainCategoryCreate,
    MainCategoryUpdate,
    SubCategoryCreate,
    SubCategoryUpdate,
)
from api.services.category_service import CategoryService
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
def service(db_session: AsyncSession) -> CategoryService:
    """Provide a CategoryService wired to the test session."""
    return CategoryService(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _main_create(
    name: str = "Videojuegos",
    slug: str = "videojuegos",
    **kwargs: object,
) -> MainCategoryCreate:
    return MainCategoryCreate(name=name, slug=slug, **kwargs)


def _sub_create(
    main_category_id: str,
    name: str = "Consolas",
    slug: str = "consolas",
    **kwargs: object,
) -> SubCategoryCreate:
    return SubCategoryCreate(
        main_category_id=main_category_id,
        name=name,
        slug=slug,
        **kwargs,
    )


async def _seed_main(
    service: CategoryService,
    name: str = "Videojuegos",
    slug: str = "videojuegos",
    **kwargs: object,
) -> MainCategory:
    """Helper to quickly create and return a main category."""
    return await service.create_main(_main_create(name=name, slug=slug, **kwargs))


async def _seed_sub(
    service: CategoryService,
    main_id: str,
    name: str = "Consolas",
    slug: str = "consolas",
    **kwargs: object,
) -> SubCategory:
    """Helper to quickly create and return a sub-category."""
    return await service.create_sub(
        _sub_create(main_category_id=main_id, name=name, slug=slug, **kwargs)
    )


# ---------------------------------------------------------------------------
# MainCategory tests
# ---------------------------------------------------------------------------


class TestCreateMainCategory:
    """Tests for CategoryService.create_main."""

    @pytest.mark.asyncio
    async def test_create_main_category_with_valid_data_returns_category(
        self, service: CategoryService,
    ) -> None:
        data = _main_create(name="Música", slug="musica", icon="🎵", sort_order=1)
        result = await service.create_main(data)

        assert result.id is not None
        assert result.name == "Música"
        assert result.slug == "musica"
        assert result.icon == "🎵"
        assert result.sort_order == 1

    @pytest.mark.asyncio
    async def test_create_main_duplicate_name_raises_duplicate_error(
        self, service: CategoryService,
    ) -> None:
        await _seed_main(service, name="Libros", slug="libros")

        with pytest.raises(DuplicateError, match="Libros"):
            await service.create_main(
                _main_create(name="Libros", slug="libros-2")
            )


class TestGetMainCategory:
    """Tests for CategoryService.get_main."""

    @pytest.mark.asyncio
    async def test_get_main_nonexistent_raises_not_found(
        self, service: CategoryService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_main("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_get_main_existing_returns_category(
        self, service: CategoryService,
    ) -> None:
        created = await _seed_main(service)
        fetched = await service.get_main(created.id)
        assert fetched.id == created.id
        assert fetched.name == created.name


class TestUpdateMainCategory:
    """Tests for CategoryService.update_main."""

    @pytest.mark.asyncio
    async def test_update_main_with_valid_data_returns_updated(
        self, service: CategoryService,
    ) -> None:
        created = await _seed_main(service, name="Old Name", slug="old-name")
        update = MainCategoryUpdate(name="New Name", slug="new-name")

        updated = await service.update_main(created.id, update)

        assert updated.name == "New Name"
        assert updated.slug == "new-name"
        assert updated.id == created.id

    @pytest.mark.asyncio
    async def test_update_main_with_duplicate_name_raises_duplicate_error(
        self, service: CategoryService,
    ) -> None:
        await _seed_main(service, name="Existing", slug="existing")
        target = await _seed_main(service, name="Target", slug="target")

        with pytest.raises(DuplicateError, match="Existing"):
            await service.update_main(
                target.id, MainCategoryUpdate(name="Existing")
            )

    @pytest.mark.asyncio
    async def test_update_main_same_name_no_error(
        self, service: CategoryService,
    ) -> None:
        """Updating with the same name should not raise DuplicateError."""
        created = await _seed_main(service, name="Keep", slug="keep")
        updated = await service.update_main(
            created.id, MainCategoryUpdate(name="Keep")
        )
        assert updated.name == "Keep"

    @pytest.mark.asyncio
    async def test_update_main_partial_fields(
        self, service: CategoryService,
    ) -> None:
        created = await _seed_main(service, name="Partial", slug="partial")
        updated = await service.update_main(
            created.id, MainCategoryUpdate(icon="🎮")
        )
        assert updated.icon == "🎮"
        assert updated.name == "Partial"  # unchanged


class TestDeleteMainCategory:
    """Tests for CategoryService.delete_main."""

    @pytest.mark.asyncio
    async def test_delete_main_with_sub_categories_raises_validation_error(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        await _seed_sub(service, main.id)

        with pytest.raises(ValidationError, match="sub-categories"):
            await service.delete_main(main.id)

    @pytest.mark.asyncio
    async def test_delete_main_without_sub_categories_succeeds(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        await service.delete_main(main.id)

        with pytest.raises(NotFoundError):
            await service.get_main(main.id)

    @pytest.mark.asyncio
    async def test_delete_main_nonexistent_raises_not_found(
        self, service: CategoryService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.delete_main("nonexistent-uuid")


class TestListMainCategories:
    """Tests for CategoryService.list_main."""

    @pytest.mark.asyncio
    async def test_list_categories_returns_ordered_by_sort_order(
        self, service: CategoryService,
    ) -> None:
        await _seed_main(service, name="C", slug="c", sort_order=3)
        await _seed_main(service, name="A", slug="a", sort_order=1)
        await _seed_main(service, name="B", slug="b", sort_order=2)

        result = await service.list_main()

        assert len(result) == 3
        assert [c.name for c in result] == ["A", "B", "C"]

    @pytest.mark.asyncio
    async def test_list_categories_empty_returns_empty_list(
        self, service: CategoryService,
    ) -> None:
        result = await service.list_main()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_categories_respects_pagination(
        self, service: CategoryService,
    ) -> None:
        for i in range(5):
            await _seed_main(
                service, name=f"Cat{i}", slug=f"cat{i}", sort_order=i,
            )

        result = await service.list_main(skip=1, limit=2)
        assert len(result) == 2
        assert result[0].name == "Cat1"
        assert result[1].name == "Cat2"


# ---------------------------------------------------------------------------
# SubCategory tests
# ---------------------------------------------------------------------------


class TestCreateSubCategory:
    """Tests for CategoryService.create_sub."""

    @pytest.mark.asyncio
    async def test_create_sub_category_linked_to_main_returns_sub_category(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        data = _sub_create(main.id, name="Juegos", slug="juegos", sort_order=1)

        result = await service.create_sub(data)

        assert result.id is not None
        assert result.name == "Juegos"
        assert result.slug == "juegos"
        assert result.main_category_id == main.id
        assert result.sort_order == 1

    @pytest.mark.asyncio
    async def test_create_sub_with_nonexistent_main_raises_not_found(
        self, service: CategoryService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.create_sub(
                _sub_create("nonexistent-uuid", name="Orphan", slug="orphan")
            )

    @pytest.mark.asyncio
    async def test_create_sub_duplicate_name_in_same_main_raises_duplicate_error(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        await _seed_sub(service, main.id, name="Juegos", slug="juegos")

        with pytest.raises(DuplicateError, match="Juegos"):
            await service.create_sub(
                _sub_create(main.id, name="Juegos", slug="juegos-2")
            )

    @pytest.mark.asyncio
    async def test_create_sub_same_name_different_main_succeeds(
        self, service: CategoryService,
    ) -> None:
        main_a = await _seed_main(service, name="A", slug="a")
        main_b = await _seed_main(service, name="B", slug="b")
        await _seed_sub(service, main_a.id, name="Items", slug="items-a")

        result = await service.create_sub(
            _sub_create(main_b.id, name="Items", slug="items-b")
        )
        assert result.name == "Items"
        assert result.main_category_id == main_b.id


class TestGetSubCategory:
    """Tests for CategoryService.get_sub."""

    @pytest.mark.asyncio
    async def test_get_sub_nonexistent_raises_not_found(
        self, service: CategoryService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_sub("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_get_sub_existing_returns_sub_category(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        created = await _seed_sub(service, main.id)
        fetched = await service.get_sub(created.id)
        assert fetched.id == created.id
        assert fetched.name == created.name


class TestUpdateSubCategory:
    """Tests for CategoryService.update_sub."""

    @pytest.mark.asyncio
    async def test_update_sub_with_valid_data_returns_updated(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        sub = await _seed_sub(service, main.id, name="Old", slug="old")

        updated = await service.update_sub(
            sub.id, SubCategoryUpdate(name="New", slug="new")
        )

        assert updated.name == "New"
        assert updated.slug == "new"
        assert updated.id == sub.id

    @pytest.mark.asyncio
    async def test_update_sub_duplicate_name_raises_duplicate_error(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        await _seed_sub(service, main.id, name="Existing", slug="existing")
        target = await _seed_sub(service, main.id, name="Target", slug="target")

        with pytest.raises(DuplicateError, match="Existing"):
            await service.update_sub(
                target.id, SubCategoryUpdate(name="Existing")
            )

    @pytest.mark.asyncio
    async def test_update_sub_same_name_no_error(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        sub = await _seed_sub(service, main.id, name="Keep", slug="keep")

        updated = await service.update_sub(
            sub.id, SubCategoryUpdate(name="Keep")
        )
        assert updated.name == "Keep"


class TestDeleteSubCategory:
    """Tests for CategoryService.delete_sub."""

    @pytest.mark.asyncio
    async def test_delete_sub_with_catalogs_raises_validation_error(
        self, service: CategoryService, db_session: AsyncSession,
    ) -> None:
        main = await _seed_main(service)
        sub = await _seed_sub(service, main.id)

        # Create a catalog linked to this sub-category
        catalog = Catalog(
            sub_category_id=sub.id,
            name="Test Catalog",
        )
        db_session.add(catalog)
        await db_session.commit()

        with pytest.raises(ValidationError, match="catalogs"):
            await service.delete_sub(sub.id)

    @pytest.mark.asyncio
    async def test_delete_sub_without_catalogs_succeeds(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        sub = await _seed_sub(service, main.id)

        await service.delete_sub(sub.id)

        with pytest.raises(NotFoundError):
            await service.get_sub(sub.id)

    @pytest.mark.asyncio
    async def test_delete_sub_nonexistent_raises_not_found(
        self, service: CategoryService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.delete_sub("nonexistent-uuid")


class TestListSubCategories:
    """Tests for CategoryService.list_sub."""

    @pytest.mark.asyncio
    async def test_list_sub_filters_by_main_category_id(
        self, service: CategoryService,
    ) -> None:
        main_a = await _seed_main(service, name="A", slug="a")
        main_b = await _seed_main(service, name="B", slug="b")

        await _seed_sub(service, main_a.id, name="Sub-A1", slug="sub-a1")
        await _seed_sub(service, main_a.id, name="Sub-A2", slug="sub-a2")
        await _seed_sub(service, main_b.id, name="Sub-B1", slug="sub-b1")

        result_a = await service.list_sub(main_a.id)
        result_b = await service.list_sub(main_b.id)

        assert len(result_a) == 2
        assert all(s.main_category_id == main_a.id for s in result_a)
        assert len(result_b) == 1
        assert result_b[0].main_category_id == main_b.id

    @pytest.mark.asyncio
    async def test_list_sub_returns_ordered_by_sort_order(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        await _seed_sub(service, main.id, name="C", slug="c", sort_order=3)
        await _seed_sub(service, main.id, name="A", slug="a", sort_order=1)
        await _seed_sub(service, main.id, name="B", slug="b", sort_order=2)

        result = await service.list_sub(main.id)

        assert [s.name for s in result] == ["A", "B", "C"]

    @pytest.mark.asyncio
    async def test_list_sub_empty_returns_empty_list(
        self, service: CategoryService,
    ) -> None:
        main = await _seed_main(service)
        result = await service.list_sub(main.id)
        assert result == []
