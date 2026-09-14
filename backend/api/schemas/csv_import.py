"""Pydantic v2 schemas for CSV batch import results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BatchImportError(BaseModel):
    """A single row that could not be imported."""

    row: int = Field(
        ...,
        ge=1,
        description="1-based line number in the CSV file (header is line 1)",
    )
    message: str = Field(
        ...,
        description="Human readable reason why the row was rejected",
    )

    model_config = ConfigDict(from_attributes=True)


class BatchImportResult(BaseModel):
    """Outcome of a CSV batch import operation."""

    created_count: int = Field(
        0,
        ge=0,
        description="Number of catalog items created successfully",
    )
    error_count: int = Field(
        0,
        ge=0,
        description="Number of data rows rejected during import",
    )
    updated_count: int = Field(
        0,
        ge=0,
        description="Number of existing entities updated during import",
    )
    skipped_count: int = Field(
        0,
        ge=0,
        description="Number of entities skipped during import",
    )
    errors: list[BatchImportError] = Field(
        default_factory=list,
        description="Detail of every rejected row",
    )

    model_config = ConfigDict(from_attributes=True)
