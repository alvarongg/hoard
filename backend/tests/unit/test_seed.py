"""Tests for the database seed script."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.models.base import Base
from api.models.category import MainCategory, SubCategory
from seed import SEED_DATA, _is_postgres, seed_database


@pytest.fixture
async def seed_engine():
    """Create a fresh in-memory engine for seed tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def seed_session(seed_engine):
    """Create a session bound to the seed engine."""
    async_session = sessionmaker(
        seed_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


class TestSeedData:
    def test_seed_data_has_five_categories(self) -> None:
        assert len(SEED_DATA) == 5

    def test_each_category_has_subcategories(self) -> None:
        for name, data in SEED_DATA.items():
            subs = data.get("subcategories", [])
            assert isinstance(subs, list), f"{name} missing subcategories"
            assert len(subs) > 0, f"{name} has no subcategories"

    def test_each_category_has_required_fields(self) -> None:
        for name, data in SEED_DATA.items():
            assert "slug" in data, f"{name} missing slug"
            assert "description" in data, f"{name} missing description"

    def test_total_subcategories_count(self) -> None:
        total = sum(len(d["subcategories"]) for d in SEED_DATA.values())
        assert total == 20


class TestIsPostgres:
    def test_detects_postgresql_url(self) -> None:
        assert _is_postgres("postgresql+asyncpg://user:pass@host/db") is True

    def test_detects_sqlite_url(self) -> None:
        assert _is_postgres("sqlite+aiosqlite:///:memory:") is False


class TestSeedDatabase:
    @pytest.mark.asyncio
    async def test_seed_creates_main_categories(
        self, seed_engine, seed_session: AsyncSession,
    ) -> None:
        await seed_database(engine=seed_engine)

        result = await seed_session.execute(select(MainCategory))
        categories = result.scalars().all()
        assert len(categories) == len(SEED_DATA)

    @pytest.mark.asyncio
    async def test_seed_creates_subcategories(
        self, seed_engine, seed_session: AsyncSession,
    ) -> None:
        await seed_database(engine=seed_engine)

        result = await seed_session.execute(select(SubCategory))
        subcategories = result.scalars().all()
        expected_count = sum(
            len(d.get("subcategories", []))
            for d in SEED_DATA.values()
        )
        assert len(subcategories) == expected_count

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(
        self, seed_engine, seed_session: AsyncSession,
    ) -> None:
        await seed_database(engine=seed_engine)
        await seed_database(engine=seed_engine)

        result = await seed_session.execute(select(MainCategory))
        categories = result.scalars().all()
        assert len(categories) == len(SEED_DATA)

    @pytest.mark.asyncio
    async def test_seed_category_names_match(
        self, seed_engine, seed_session: AsyncSession,
    ) -> None:
        await seed_database(engine=seed_engine)

        result = await seed_session.execute(select(MainCategory.name))
        names = {row[0] for row in result.all()}
        assert names == set(SEED_DATA.keys())

    @pytest.mark.asyncio
    async def test_seed_subcategories_linked_to_parent(
        self, seed_engine, seed_session: AsyncSession,
    ) -> None:
        await seed_database(engine=seed_engine)

        result = await seed_session.execute(
            select(SubCategory).where(SubCategory.main_category_id.isnot(None))
        )
        subcategories = result.scalars().all()
        expected_count = sum(
            len(d.get("subcategories", []))
            for d in SEED_DATA.values()
        )
        assert len(subcategories) == expected_count

    @pytest.mark.asyncio
    async def test_seed_inserts_subcategories_when_categories_exist(
        self, seed_engine, seed_session: AsyncSession,
    ) -> None:
        """If main categories exist but subcategories don't, seed fills them in."""
        from sqlalchemy import text

        # Insert only main categories (simulating a partial seed)
        for sort_order, (name, data) in enumerate(SEED_DATA.items()):
            import uuid
            cat_id = str(uuid.uuid4())
            await seed_session.execute(
                text(
                    "INSERT INTO main_categories (id, name, slug, description, icon, sort_order, created_at, updated_at) "
                    "VALUES (:id, :name, :slug, :description, :icon, :sort_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {
                    "id": cat_id,
                    "name": name,
                    "slug": data["slug"],
                    "description": data["description"],
                    "icon": data.get("icon", ""),
                    "sort_order": sort_order,
                },
            )
        await seed_session.commit()

        # Verify no subcategories yet
        result = await seed_session.execute(select(SubCategory))
        assert len(result.scalars().all()) == 0

        # Run seed — should detect missing subcategories and insert them
        await seed_database(engine=seed_engine)

        result = await seed_session.execute(select(SubCategory))
        subcategories = result.scalars().all()
        expected_count = sum(
            len(d.get("subcategories", []))
            for d in SEED_DATA.values()
        )
        assert len(subcategories) == expected_count

