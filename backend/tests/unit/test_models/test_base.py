"""Tests for SQLAlchemy base model and mixins."""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import DateTime, String, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from api.models.base import Base, DBUUID, TimestampMixin, UUIDMixin, _generate_uuid_str


class TestBase:
    """Tests for the Base declarative base class."""

    def test_base_is_declarative_base(self) -> None:
        assert issubclass(Base, DeclarativeBase)

    def test_base_has_metadata(self) -> None:
        assert Base.metadata is not None

    def test_base_has_registry(self) -> None:
        assert Base.registry is not None


class TestUUIDMixin:
    """Tests for the UUIDMixin."""

    def test_uuid_mixin_has_id_attribute(self) -> None:
        assert hasattr(UUIDMixin, "id")

    def test_uuid_mixin_id_is_primary_key(self) -> None:
        """Create a concrete model using UUIDMixin and verify id is a PK."""

        class _UUIDModel(UUIDMixin, Base):
            __tablename__ = "_test_uuid_model"

        mapper = inspect(_UUIDModel)
        pk_cols = [col.name for col in mapper.primary_key]
        assert "id" in pk_cols

    def test_uuid_mixin_generates_uuid_string_default(self) -> None:
        """Verify the default callable produces a valid UUID string."""
        generated = _generate_uuid_str()
        assert isinstance(generated, str)
        assert len(generated) == 36
        # Validate it's a proper UUID format
        parsed = uuid.UUID(generated)
        assert str(parsed) == generated

    def test_uuid_mixin_id_uses_dbuuid_type(self) -> None:
        """The column type should be DBUUID for cross-DB compatibility."""

        class _UUIDModel3(UUIDMixin, Base):
            __tablename__ = "_test_uuid_model3"

        mapper = inspect(_UUIDModel3)
        id_col = mapper.columns["id"]
        assert isinstance(id_col.type, DBUUID)


class TestTimestampMixin:
    """Tests for the TimestampMixin."""

    def test_timestamp_mixin_has_created_at(self) -> None:
        assert hasattr(TimestampMixin, "created_at")

    def test_timestamp_mixin_has_updated_at(self) -> None:
        assert hasattr(TimestampMixin, "updated_at")

    def test_timestamp_columns_are_datetime_type(self) -> None:
        """Verify both columns use DateTime type."""

        class _TSModel(TimestampMixin, Base):
            __tablename__ = "_test_ts_model"
            id: Mapped[int] = mapped_column(primary_key=True)

        mapper = inspect(_TSModel)
        for col_name in ("created_at", "updated_at"):
            col = mapper.columns[col_name]
            assert isinstance(col.type, DateTime)

    def test_timestamp_columns_are_not_nullable(self) -> None:
        """Both timestamp columns must be non-nullable."""

        class _TSModel2(TimestampMixin, Base):
            __tablename__ = "_test_ts_model2"
            id: Mapped[int] = mapped_column(primary_key=True)

        mapper = inspect(_TSModel2)
        for col_name in ("created_at", "updated_at"):
            col = mapper.columns[col_name]
            assert col.nullable is False

    def test_timestamp_columns_have_server_default(self) -> None:
        """Both columns should have a server_default set."""

        class _TSModel3(TimestampMixin, Base):
            __tablename__ = "_test_ts_model3"
            id: Mapped[int] = mapped_column(primary_key=True)

        mapper = inspect(_TSModel3)
        for col_name in ("created_at", "updated_at"):
            col = mapper.columns[col_name]
            assert col.server_default is not None

    def test_updated_at_has_onupdate(self) -> None:
        """updated_at should have an onupdate trigger."""

        class _TSModel4(TimestampMixin, Base):
            __tablename__ = "_test_ts_model4"
            id: Mapped[int] = mapped_column(primary_key=True)

        mapper = inspect(_TSModel4)
        updated_col = mapper.columns["updated_at"]
        assert updated_col.onupdate is not None


class TestCombinedMixins:
    """Tests for a model using both UUIDMixin and TimestampMixin together."""

    def test_combined_model_has_all_columns(self) -> None:
        """A model using both mixins should have id, created_at, updated_at."""

        class _CombinedModel(UUIDMixin, TimestampMixin, Base):
            __tablename__ = "_test_combined_model"

        mapper = inspect(_CombinedModel)
        col_names = {col.name for col in mapper.columns}
        assert {"id", "created_at", "updated_at"}.issubset(col_names)

    @pytest.mark.asyncio
    async def test_combined_model_persists_with_defaults(self) -> None:
        """Verify a model with both mixins can be persisted and gets defaults."""

        class _PersistModel(UUIDMixin, TimestampMixin, Base):
            __tablename__ = "_test_persist_model"

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            obj = _PersistModel()
            session.add(obj)
            await session.commit()
            await session.refresh(obj)

            assert obj.id is not None
            assert isinstance(obj.id, str)
            assert len(obj.id) == 36
            # Validate it's a proper UUID
            uuid.UUID(obj.id)
            assert obj.created_at is not None
            assert obj.updated_at is not None

        await engine.dispose()
