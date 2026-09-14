"""Dialect detection and feature support utilities.

This module provides helpers to detect the current database dialect
(PostgreSQL or SQLite) and query which features are available. This is
essential because production uses PostgreSQL 14+ with tsvector, pg_trgm,
GENERATED columns, triggers, and views, while tests use SQLite in-memory
where these features are not available.

The safe default is SQLite when the session's bind is None (e.g., during
testing or when the engine hasn't been attached yet).
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession


class Dialect(str, Enum):
    """Supported database dialects."""

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


def current_dialect(db: AsyncSession) -> Dialect:
    """Return the dialect of the session's bind.

    Falls back to SQLite when the bind is None, providing a safe default
    for testing environments.

    Args:
        db: An async database session.

    Returns:
        The detected Dialect (POSTGRESQL or SQLITE).
    """
    if db.bind is None:
        return Dialect.SQLITE
    name = db.bind.dialect.name
    return Dialect.POSTGRESQL if name == "postgresql" else Dialect.SQLITE


def supports_full_text(db: AsyncSession) -> bool:
    """Check if the dialect supports full-text search.

    PostgreSQL supports tsvector and ts_query for full-text search.
    SQLite does not have native full-text support in this project's context.

    Args:
        db: An async database session.

    Returns:
        True if the dialect supports full-text search, False otherwise.
    """
    return current_dialect(db) is Dialect.POSTGRESQL


def supports_generated_columns(db: AsyncSession) -> bool:
    """Check if the dialect supports GENERATED columns.

    PostgreSQL supports GENERATED (computed) columns natively.
    SQLite requires manual calculation in the service layer.

    Args:
        db: An async database session.

    Returns:
        True if the dialect supports GENERATED columns, False otherwise.
    """
    return current_dialect(db) is Dialect.POSTGRESQL


def supports_views(db: AsyncSession) -> bool:
    """Check if the dialect supports pre-defined views.

    PostgreSQL has views defined in migrations (e.g., v_collection_stats).
    SQLite in-memory databases don't have these views; queries must be
    computed in the service layer.

    Args:
        db: An async database session.

    Returns:
        True if the dialect supports pre-defined views, False otherwise.
    """
    return current_dialect(db) is Dialect.POSTGRESQL
