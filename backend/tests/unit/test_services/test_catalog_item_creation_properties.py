"""Property-based tests for inline catalog item creation.

# Feature: inline-catalog-item-creation, Property 1: Validación de título determina éxito de creación
# Feature: inline-catalog-item-creation, Property 2: Catálogo inexistente rechaza creación

Requirements: 1.3, 1.4, 3.1, 3.2
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, example, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.base import Base
from api.models.catalog import Catalog
from api.models.category import MainCategory, SubCategory
from api.schemas.catalog import CatalogCreate, CatalogItemCreate
from api.services.catalog_service import CatalogService
from core.exceptions import NotFoundError

MAX_TITLE_LENGTH = 500
PROPERTY_ITERATIONS = 100

# Hypothesis reuses the same function-scoped fixtures for every generated
# example, which is safe here: each example only appends rows to an isolated
# in-memory database, so examples cannot influence each other's outcome.
property_settings = settings(
    max_examples=PROPERTY_ITERATIONS,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


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


@pytest.fixture()
async def catalog(service: CatalogService, db_session: AsyncSession) -> Catalog:
    """Provide a persisted catalog to create items into."""
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db_session.add(main)
    await db_session.commit()
    await db_session.refresh(main)

    sub = SubCategory(
        main_category_id=main.id, name="Consolas", slug="consolas",
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    return await service.create_catalog(
        CatalogCreate(name="Property Catalog", sub_category_id=sub.id),
    )


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

WHITESPACE = " \t\n\r\v\f\u00a0\u2003"

# Constrain generation to the interesting regions of the input space:
# clearly valid titles, empty/whitespace-only titles, and over-long titles.
titles = st.one_of(
    st.text(min_size=1, max_size=80).filter(lambda s: s.strip() != ""),
    st.text(alphabet=WHITESPACE, min_size=0, max_size=6),
    st.text(min_size=MAX_TITLE_LENGTH + 1, max_size=MAX_TITLE_LENGTH + 40),
    st.text(min_size=0, max_size=MAX_TITLE_LENGTH + 5),
)


def _is_valid_title(title: str) -> bool:
    """Return True when the title satisfies the documented creation rules."""
    return title.strip() != "" and len(title) <= MAX_TITLE_LENGTH


# ---------------------------------------------------------------------------
# Property 1
# ---------------------------------------------------------------------------


class TestTitleValidationProperty:
    """Property 1: Validación de título determina éxito de creación."""

    # Feature: inline-catalog-item-creation,
    # Property 1: Validación de título determina éxito de creación
    # Validates: Requirements 1.3, 1.4, 3.1
    @given(title=titles)
    @example(title="")
    @example(title="   ")
    @example(title="\t\n")
    @example(title="a")
    @example(title="a" * MAX_TITLE_LENGTH)
    @example(title="a" * (MAX_TITLE_LENGTH + 1))
    @property_settings
    async def test_create_item_succeeds_iff_title_is_valid(
        self, service: CatalogService, catalog: Catalog, title: str,
    ) -> None:
        expected_success = _is_valid_title(title)

        try:
            data = CatalogItemCreate(catalog_id=catalog.id, title=title)
            item = await service.create_item(catalog.id, data)
        except PydanticValidationError:
            assert not expected_success, (
                f"creation was rejected for a valid title {title!r}"
            )
            return

        assert expected_success, (
            f"creation succeeded for an invalid title {title!r}"
        )
        assert item.id is not None
        assert item.catalog_id == catalog.id
        assert item.title.strip() != ""


# ---------------------------------------------------------------------------
# Property 2
# ---------------------------------------------------------------------------


class TestMissingCatalogProperty:
    """Property 2: Catálogo inexistente rechaza creación."""

    # Feature: inline-catalog-item-creation,
    # Property 2: Catálogo inexistente rechaza creación
    # Validates: Requirements 3.2
    @given(missing_catalog_id=st.uuids().map(str))
    @property_settings
    async def test_create_item_with_unknown_catalog_raises_not_found(
        self, service: CatalogService, catalog: Catalog, missing_catalog_id: str,
    ) -> None:
        assume(missing_catalog_id != catalog.id)

        data = CatalogItemCreate(
            catalog_id=missing_catalog_id, title="Valid Title",
        )

        with pytest.raises(NotFoundError, match="not found"):
            await service.create_item(missing_catalog_id, data)
