"""Unit tests for CollectionService business logic.

Tests cover all CRUD operations for Collection, including validation rules,
duplicate name detection, single_category sub-category enforcement,
partial updates, pagination, and deletion.

Requirements: REQ-007, REQ-015
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection
from api.schemas.collection import CollectionCreate, CollectionUpdate
from api.services.collection_service import CollectionService
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
def service(db_session: AsyncSession) -> CollectionService:
    """Provide a CollectionService wired to the test session."""
    return CollectionService(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_sub_category(db_session: AsyncSession) -> SubCategory:
    """Create a MainCategory + SubCategory and return the SubCategory."""
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db_session.add(main)
    await db_session.flush()

    sub = SubCategory(
        main_category_id=main.id, name="Consolas", slug="consolas",
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)
    return sub


def _single_create(
    sub_category_id: str,
    name: str = "Mi Colección N64",
    **kwargs: object,
) -> CollectionCreate:
    """Build a CollectionCreate for a single_category collection."""
    return CollectionCreate(
        name=name,
        collection_type="single_category",
        restricted_to_sub_category_id=sub_category_id,
        **kwargs,
    )


def _multi_create(name: str = "Multi Collection", **kwargs: object) -> CollectionCreate:
    """Build a CollectionCreate for a multi_category collection."""
    return CollectionCreate(
        name=name,
        collection_type="multi_category",
        **kwargs,
    )


async def _seed_collection(
    service: CollectionService,
    db_session: AsyncSession,
    name: str = "Mi Colección N64",
    collection_type: str = "multi_category",
    sub_category_id: str | None = None,
) -> Collection:
    """Helper to quickly create and return a collection."""
    if collection_type == "single_category" and sub_category_id is None:
        sub = await _seed_sub_category(db_session)
        sub_category_id = sub.id

    if collection_type == "single_category":
        data = _single_create(sub_category_id, name=name)
    else:
        data = _multi_create(name=name)
    return await service.create(data)


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------


class TestCreateCollection:
    """Tests for CollectionService.create."""

    @pytest.mark.asyncio
    async def test_create_collection_with_valid_data_returns_collection(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        data = _single_create(sub.id, name="Nintendo 64 Games")

        result = await service.create(data)

        assert result.id is not None
        assert result.name == "Nintendo 64 Games"
        assert result.collection_type == "single_category"
        assert result.restricted_to_sub_category_id == sub.id
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_create_collection_with_duplicate_name_raises_duplicate_error(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        await _seed_collection(service, db_session, name="Duplicada")

        with pytest.raises(DuplicateError, match="Duplicada"):
            await _seed_collection(service, db_session, name="Duplicada")

    @pytest.mark.asyncio
    async def test_create_single_category_without_subcategory_raises_validation_error(
        self, service: CollectionService,
    ) -> None:
        data = CollectionCreate(
            name="Bad Collection",
            collection_type="single_category",
            restricted_to_sub_category_id="nonexistent-uuid",
        )

        with pytest.raises(ValidationError, match="does not exist"):
            await service.create(data)

    @pytest.mark.asyncio
    async def test_create_multi_category_without_subcategory_succeeds(
        self, service: CollectionService,
    ) -> None:
        data = _multi_create(name="Mixed Stuff")

        result = await service.create(data)

        assert result.id is not None
        assert result.name == "Mixed Stuff"
        assert result.collection_type == "multi_category"
        assert result.restricted_to_sub_category_id is None

    @pytest.mark.asyncio
    async def test_create_single_category_with_valid_subcategory_succeeds(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        sub = await _seed_sub_category(db_session)
        data = _single_create(sub.id, name="Retro Games")

        result = await service.create(data)

        assert result.collection_type == "single_category"
        assert result.restricted_to_sub_category_id == sub.id


# ---------------------------------------------------------------------------
# Get tests
# ---------------------------------------------------------------------------


class TestGetCollection:
    """Tests for CollectionService.get_by_id."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_collection_raises_not_found(
        self, service: CollectionService,
    ) -> None:
        with pytest.raises(NotFoundError, match="not found"):
            await service.get_by_id("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_get_existing_collection_returns_collection(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        created = await _seed_collection(service, db_session, name="Fetch Me")
        fetched = await service.get_by_id(created.id)

        assert fetched.id == created.id
        assert fetched.name == "Fetch Me"


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------


class TestUpdateCollection:
    """Tests for CollectionService.update."""

    @pytest.mark.asyncio
    async def test_update_collection_partial_fields_updates_only_provided(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        created = await _seed_collection(
            service, db_session, name="Original",
        )
        update = CollectionUpdate(description="New description")

        updated = await service.update(created.id, update)

        assert updated.description == "New description"
        assert updated.name == "Original"  # unchanged

    @pytest.mark.asyncio
    async def test_update_with_duplicate_name_raises_duplicate_error(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        await _seed_collection(service, db_session, name="Existing")
        target = await _seed_collection(service, db_session, name="Target")

        with pytest.raises(DuplicateError, match="Existing"):
            await service.update(target.id, CollectionUpdate(name="Existing"))

    @pytest.mark.asyncio
    async def test_update_same_name_no_error(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        created = await _seed_collection(service, db_session, name="Keep")

        updated = await service.update(
            created.id, CollectionUpdate(name="Keep"),
        )

        assert updated.name == "Keep"

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises_not_found(
        self, service: CollectionService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.update(
                "nonexistent-uuid", CollectionUpdate(name="Nope"),
            )


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


class TestDeleteCollection:
    """Tests for CollectionService.delete."""

    @pytest.mark.asyncio
    async def test_delete_collection_removes_collection(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        created = await _seed_collection(service, db_session, name="Bye")

        await service.delete(created.id)

        with pytest.raises(NotFoundError):
            await service.get_by_id(created.id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_not_found(
        self, service: CollectionService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-uuid")


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------


class TestListCollections:
    """Tests for CollectionService.list."""

    @pytest.mark.asyncio
    async def test_list_returns_only_active_collections(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        active = await _seed_collection(service, db_session, name="Active")
        inactive = await _seed_collection(service, db_session, name="Inactive")

        # Deactivate one via direct model update
        inactive.is_active = False
        await db_session.commit()

        result = await service.list()

        assert len(result) == 1
        assert result[0].id == active.id

    @pytest.mark.asyncio
    async def test_list_returns_ordered_by_name(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        await _seed_collection(service, db_session, name="Charlie")
        await _seed_collection(service, db_session, name="Alpha")
        await _seed_collection(service, db_session, name="Bravo")

        result = await service.list()

        assert [c.name for c in result] == ["Alpha", "Bravo", "Charlie"]

    @pytest.mark.asyncio
    async def test_list_respects_pagination(
        self, service: CollectionService, db_session: AsyncSession,
    ) -> None:
        for i in range(5):
            await _seed_collection(
                service, db_session, name=f"Col-{i:02d}",
            )

        result = await service.list(skip=1, limit=2)

        assert len(result) == 2
        assert result[0].name == "Col-01"
        assert result[1].name == "Col-02"

    @pytest.mark.asyncio
    async def test_list_empty_returns_empty_list(
        self, service: CollectionService,
    ) -> None:
        result = await service.list()
        assert result == []
