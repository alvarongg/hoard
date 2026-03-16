"""Tests for Supplier SQLAlchemy model."""

import uuid

import pytest
from sqlalchemy import Boolean, Numeric, String, Text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON

from api.models.base import Base
from api.models.supplier import Supplier


# ---------------------------------------------------------------------------
# Column tests
# ---------------------------------------------------------------------------


class TestSupplierColumns:
    """Verify Supplier has the correct columns and constraints."""

    def test_tablename(self) -> None:
        assert Supplier.__tablename__ == "suppliers"

    def test_has_expected_columns(self) -> None:
        mapper = inspect(Supplier)
        col_names = {col.name for col in mapper.columns}
        expected = {
            "id", "name", "type", "country", "state_province", "city",
            "address", "postal_code", "website", "email", "phone",
            "marketplace_url", "social_media", "rating", "notes",
            "is_favorite", "is_active", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_name_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is False

    def test_type_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["type"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_country_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["country"]
        assert isinstance(col.type, String)
        assert col.type.length == 2
        assert col.nullable is True

    def test_state_province_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["state_province"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_city_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["city"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    def test_address_column_is_nullable_text(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["address"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_postal_code_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["postal_code"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.nullable is True

    def test_website_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["website"]
        assert isinstance(col.type, String)
        assert col.type.length == 500
        assert col.nullable is True

    def test_email_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["email"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is True

    def test_phone_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["phone"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_marketplace_url_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["marketplace_url"]
        assert isinstance(col.type, String)
        assert col.type.length == 500
        assert col.nullable is True

    def test_social_media_column_is_json(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["social_media"]
        assert isinstance(col.type, JSON)

    def test_rating_column_is_numeric(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["rating"]
        assert isinstance(col.type, Numeric)
        assert col.nullable is True

    def test_notes_column_is_nullable_text(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["notes"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_is_favorite_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["is_favorite"]
        assert isinstance(col.type, Boolean)

    def test_is_active_column_properties(self) -> None:
        mapper = inspect(Supplier)
        col = mapper.columns["is_active"]
        assert isinstance(col.type, Boolean)


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


@pytest.fixture()
async def _supplier_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def supplier_session(_supplier_engine):
    factory = async_sessionmaker(
        _supplier_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session


class TestSupplierPersistence:
    """Integration-style tests for persisting suppliers."""

    @pytest.mark.asyncio
    async def test_create_supplier_persists(
        self, supplier_session: AsyncSession,
    ) -> None:
        supplier = Supplier(
            name="RetroGames Store",
            type="online",
            country="US",
            website="https://retrogames.example.com",
        )
        supplier_session.add(supplier)
        await supplier_session.commit()
        await supplier_session.refresh(supplier)

        assert supplier.id is not None
        assert len(supplier.id) == 36
        uuid.UUID(supplier.id)
        assert supplier.name == "RetroGames Store"
        assert supplier.type == "online"
        assert supplier.country == "US"
        assert supplier.created_at is not None

    @pytest.mark.asyncio
    async def test_supplier_defaults_applied(
        self, supplier_session: AsyncSession,
    ) -> None:
        supplier = Supplier(name="Defaults Test")
        supplier_session.add(supplier)
        await supplier_session.commit()
        await supplier_session.refresh(supplier)

        assert supplier.is_favorite is False
        assert supplier.is_active is True

    @pytest.mark.asyncio
    async def test_repr_method(self) -> None:
        supplier = Supplier(name="Test Supplier")
        assert "Supplier" in repr(supplier)
        assert "Test Supplier" in repr(supplier)
