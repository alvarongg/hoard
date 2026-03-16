"""Shared Pydantic type aliases for schema definitions."""

from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator

# Coerce PostgreSQL native UUID objects to str for cross-DB compatibility.
# PostgreSQL schema.sql uses native UUID columns, but ORM models use
# String(36). When reading from PostgreSQL, SQLAlchemy returns Python
# UUID objects that Pydantic's `str` type rejects. This validator
# converts any value to str before validation.
StrUUID = Annotated[str, BeforeValidator(str)]
