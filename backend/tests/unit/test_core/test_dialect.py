"""Tests for core.dialect dialect detection utilities.

Validates: Requirements 11.5, 12.9, 7.7, 5.5, 19.10 (dialect-aware behavior)
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.dialect import (
    Dialect,
    current_dialect,
    supports_full_text,
    supports_generated_columns,
    supports_views,
)


class TestCurrentDialect:
    """Tests for current_dialect detection."""

    def test_sqlite_session_returns_sqlite(self) -> None:
        """SQLite session should return Dialect.SQLITE."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        mock_session.bind = mock_bind

        result = current_dialect(mock_session)

        assert result == Dialect.SQLITE

    def test_postgresql_session_returns_postgresql(self) -> None:
        """PostgreSQL session should return Dialect.POSTGRESQL."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        mock_session.bind = mock_bind

        result = current_dialect(mock_session)

        assert result == Dialect.POSTGRESQL

    def test_session_without_bind_falls_back_to_sqlite(self) -> None:
        """Session with None bind (testing environment) falls back to SQLite."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.bind = None

        result = current_dialect(mock_session)

        assert result == Dialect.SQLITE

    def test_unknown_dialect_returns_sqlite(self) -> None:
        """Unknown dialect names default to SQLite for safety."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "mysql"  # Unknown dialect
        mock_session.bind = mock_bind

        result = current_dialect(mock_session)

        assert result == Dialect.SQLITE


class TestSupportsFullText:
    """Tests for supports_full_text feature detection."""

    def test_postgresql_supports_full_text(self) -> None:
        """PostgreSQL supports tsvector and ts_query."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        mock_session.bind = mock_bind

        result = supports_full_text(mock_session)

        assert result is True

    def test_sqlite_does_not_support_full_text(self) -> None:
        """SQLite does not have native full-text support in this project."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        mock_session.bind = mock_bind

        result = supports_full_text(mock_session)

        assert result is False

    def test_session_without_bind_returns_false(self) -> None:
        """Fallback to SQLite returns False for full-text support."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.bind = None

        result = supports_full_text(mock_session)

        assert result is False


class TestSupportsGeneratedColumns:
    """Tests for supports_generated_columns feature detection."""

    def test_postgresql_supports_generated_columns(self) -> None:
        """PostgreSQL supports GENERATED columns natively."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        mock_session.bind = mock_bind

        result = supports_generated_columns(mock_session)

        assert result is True

    def test_sqlite_does_not_support_generated_columns(self) -> None:
        """SQLite requires manual calculation in service layer."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        mock_session.bind = mock_bind

        result = supports_generated_columns(mock_session)

        assert result is False

    def test_session_without_bind_returns_false(self) -> None:
        """Fallback to SQLite returns False for GENERATED columns."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.bind = None

        result = supports_generated_columns(mock_session)

        assert result is False


class TestSupportsViews:
    """Tests for supports_views feature detection."""

    def test_postgresql_supports_views(self) -> None:
        """PostgreSQL has views defined in migrations."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        mock_session.bind = mock_bind

        result = supports_views(mock_session)

        assert result is True

    def test_sqlite_does_not_support_views(self) -> None:
        """SQLite in-memory doesn't have pre-defined views."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        mock_session.bind = mock_bind

        result = supports_views(mock_session)

        assert result is False

    def test_session_without_bind_returns_false(self) -> None:
        """Fallback to SQLite returns False for views."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.bind = None

        result = supports_views(mock_session)

        assert result is False


class TestDialectEnum:
    """Tests for Dialect enum values."""

    def test_postgresql_value(self) -> None:
        assert Dialect.POSTGRESQL.value == "postgresql"

    def test_sqlite_value(self) -> None:
        assert Dialect.SQLITE.value == "sqlite"

    def test_dialect_is_string_enum(self) -> None:
        """Dialect should be a string enum for easy comparison."""
        assert isinstance(Dialect.POSTGRESQL, str)
        assert isinstance(Dialect.SQLITE, str)
