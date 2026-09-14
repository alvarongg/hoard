"""Shared test fixtures for the H.O.A.R.D. backend test suite."""

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.database import get_async_session
from main import app

# ---------------------------------------------------------------------------
# Database fixtures (SQLite in-memory via aiosqlite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# PostgreSQL test database URL (opt-in via environment variable)
HOARD_TEST_DATABASE_URL = os.environ.get("HOARD_TEST_DATABASE_URL")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionFactory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async database session backed by SQLite in-memory.

    Tables are created before each test and dropped afterwards so every
    test runs in complete isolation.
    """
    from sqlalchemy import text

    async with test_engine.begin() as conn:
        # Enable WAL mode for better concurrency in SQLite
        await conn.execute(text("PRAGMA journal_mode=WAL"))

    async with TestSessionFactory() as session:
        yield session

    # Dispose connections after each test
    await test_engine.dispose()


# ---------------------------------------------------------------------------
# Dialect fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def dialect_name(db_session: AsyncSession) -> str:
    """Return the dialect name of the current database session.

    Used by tests that need to branch behavior between PostgreSQL and SQLite.
    """
    if db_session.bind is None:
        return "sqlite"
    return db_session.bind.dialect.name


# ---------------------------------------------------------------------------
# PostgreSQL fixtures (opt-in via HOARD_TEST_DATABASE_URL)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a PostgreSQL session for tests that require a real database.

    This fixture is opt-in and requires the HOARD_TEST_DATABASE_URL environment
    variable to be set. Tests using this fixture must be marked with
    @pytest.mark.postgres.

    If HOARD_TEST_DATABASE_URL is not set, the test is skipped.
    """
    if HOARD_TEST_DATABASE_URL is None:
        pytest.skip("HOARD_TEST_DATABASE_URL is not set")

    pg_engine = create_async_engine(
        HOARD_TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    PgSessionFactory = async_sessionmaker(
        pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with PgSessionFactory() as session:
        yield session

    await pg_engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------


async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override that yields a test database session."""
    async with TestSessionFactory() as session:
        yield session


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the FastAPI test app.

    The database dependency is overridden so all requests use the
    in-memory SQLite test database.
    """
    app.dependency_overrides[get_async_session] = _override_get_async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def make_uuid() -> str:
    """Return a new UUID4 string for use in test data."""
    return str(uuid4())


def build_collection_data(**overrides: object) -> dict:
    """Return a dictionary with sensible defaults for creating a collection.

    Any key can be overridden via keyword arguments.
    """
    defaults: dict = {
        "name": f"Test Collection {make_uuid()[:8]}",
        "description": "A test collection",
        "collection_type": "multi_category",
        "theme": None,
        "restricted_to_sub_category_id": None,
        "goal_description": None,
        "goal_items_count": None,
        "display_order": "custom",
        "is_public": False,
    }
    defaults.update(overrides)
    return defaults


def build_catalog_item_data(**overrides: object) -> dict:
    """Return a dictionary with sensible defaults for a catalog item.

    Any key can be overridden via keyword arguments.
    """
    defaults: dict = {
        "title": f"Test Item {make_uuid()[:8]}",
        "subtitle": None,
        "description": "A test catalog item",
        "release_date": None,
        "manufacturer": None,
        "publisher": None,
        "developer": None,
        "brand": None,
        "language": None,
        "region": None,
        "rarity": None,
        "custom_fields": {},
        "cover_image_url": None,
    }
    defaults.update(overrides)
    return defaults
