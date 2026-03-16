"""Tests for MainCategory and SubCategory SQLAlchemy models."""

import uuid

import pytest
from sqlalchemy import ForeignKey, Integer, String, Text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.category import MainCategory, SubCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_slug(name: str) -> str:
    return name.lower().replace(" ", "-")


# ---------------------------------------------------------------------------
# MainCategory column tests
# ---------------------------------------------------------------------------


class TestMainCategoryColumns:
    """Verify MainCategory has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert MainCategory.__tablename__ == "main_categories"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(MainCategory)
        col_names = {col.name for col in mapper.columns}
        expected = {"id", "name", "slug", "description", "icon", "sort_order", "created_at", "updated_at"}
        assert expected.issubset(col_names)

    def test_name_column_properties(self) -> None:
        mapper = inspect(MainCategory)
        col = mapper.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False
        assert col.unique is True

    def test_slug_column_properties(self) -> None:
        mapper = inspect(MainCategory)
        col = mapper.columns["slug"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False
        assert col.unique is True

    def test_description_column_is_nullable_text(self) -> None:
        mapper = inspect(MainCategory)
        col = mapper.columns["description"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_icon_column_properties(self) -> None:
        mapper = inspect(MainCategory)
        col = mapper.columns["icon"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_sort_order_column_properties(self) -> None:
        mapper = inspect(MainCategory)
        col = mapper.columns["sort_order"]
        assert isinstance(col.type, Integer)


# ---------------------------------------------------------------------------
# SubCategory column tests
# ---------------------------------------------------------------------------


class TestSubCategoryColumns:
    """Verify SubCategory has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert SubCategory.__tablename__ == "sub_categories"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(SubCategory)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "main_category_id", "name", "slug",
            "description", "sort_order", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_main_category_id_is_foreign_key(self) -> None:
        mapper = inspect(SubCategory)
        col = mapper.columns["main_category_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "main_categories.id" in fk_targets

    def test_main_category_id_not_nullable(self) -> None:
        mapper = inspect(SubCategory)
        col = mapper.columns["main_category_id"]
        assert col.nullable is False

    def test_name_column_properties(self) -> None:
        mapper = inspect(SubCategory)
        col = mapper.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False

    def test_slug_column_properties(self) -> None:
        mapper = inspect(SubCategory)
        col = mapper.columns["slug"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False

    def test_has_unique_constraint_on_main_category_and_slug(self) -> None:
        """The pair (main_category_id, slug) must be unique."""
        table = SubCategory.__table__
        unique_constraints = [
            c for c in table.constraints
            if hasattr(c, "columns")
            and {col.name for col in c.columns} == {"main_category_id", "slug"}
        ]
        assert len(unique_constraints) == 1


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestCategoryRelationships:
    """Verify the one-to-many relationship between MainCategory and SubCategory."""

    def test_main_category_has_sub_categories_relationship(self) -> None:
        mapper = inspect(MainCategory)
        rel_names = {r.key for r in mapper.relationships}
        assert "sub_categories" in rel_names

    def test_sub_category_has_main_category_relationship(self) -> None:
        mapper = inspect(SubCategory)
        rel_names = {r.key for r in mapper.relationships}
        assert "main_category" in rel_names

    def test_relationship_cascade_includes_delete_orphan(self) -> None:
        mapper = inspect(MainCategory)
        rel = mapper.relationships["sub_categories"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True


# ---------------------------------------------------------------------------
# Persistence / cascade tests (async with in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _category_engine():
    """Create an in-memory SQLite engine with category tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def category_session(_category_engine):
    """Provide a session bound to the in-memory engine."""
    factory = async_sessionmaker(
        _category_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


class TestCategoryPersistence:
    """Integration-style tests for persisting categories."""

    @pytest.mark.asyncio
    async def test_create_main_category_persists(self, category_session: AsyncSession) -> None:
        cat = MainCategory(name="Videojuegos", slug="videojuegos", icon="🎮", sort_order=1)
        category_session.add(cat)
        await category_session.commit()
        await category_session.refresh(cat)

        assert cat.id is not None
        assert len(cat.id) == 36
        uuid.UUID(cat.id)  # validates format
        assert cat.name == "Videojuegos"
        assert cat.created_at is not None

    @pytest.mark.asyncio
    async def test_create_sub_category_linked_to_main(self, category_session: AsyncSession) -> None:
        main = MainCategory(name="Música", slug="musica", sort_order=0)
        category_session.add(main)
        await category_session.commit()
        await category_session.refresh(main)

        sub = SubCategory(
            main_category_id=main.id,
            name="Vinilos",
            slug="vinilos",
            sort_order=0,
        )
        category_session.add(sub)
        await category_session.commit()
        await category_session.refresh(sub)

        assert sub.id is not None
        assert sub.main_category_id == main.id

    @pytest.mark.asyncio
    async def test_cascade_delete_removes_sub_categories(self, category_session: AsyncSession) -> None:
        main = MainCategory(name="TCG", slug="tcg", sort_order=0)
        sub1 = SubCategory(name="Pokemon", slug="pokemon", sort_order=0)
        sub2 = SubCategory(name="MTG", slug="mtg", sort_order=1)
        main.sub_categories = [sub1, sub2]

        category_session.add(main)
        await category_session.commit()

        # Delete the main category
        await category_session.delete(main)
        await category_session.commit()

        # Verify sub-categories are gone
        from sqlalchemy import select
        result = await category_session.execute(select(SubCategory))
        remaining = result.scalars().all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_relationship_back_populates(self, category_session: AsyncSession) -> None:
        main = MainCategory(name="Libros", slug="libros", sort_order=0)
        sub = SubCategory(name="Novelas", slug="novelas", sort_order=0)
        main.sub_categories.append(sub)

        category_session.add(main)
        await category_session.commit()
        await category_session.refresh(sub)

        assert sub.main_category is not None
        assert sub.main_category.id == main.id

    @pytest.mark.asyncio
    async def test_repr_methods(self) -> None:
        main = MainCategory(name="Test", slug="test")
        sub = SubCategory(name="Sub", slug="sub")
        assert "MainCategory" in repr(main)
        assert "SubCategory" in repr(sub)
