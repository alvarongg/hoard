"""Pydantic v2 schemas for MainCategory and SubCategory validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# MainCategory schemas
# ---------------------------------------------------------------------------


class MainCategoryBase(BaseModel):
    """Shared fields for MainCategory create/update operations."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the main category",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the category",
    )
    icon: str | None = Field(
        None,
        max_length=50,
        description="Icon identifier or emoji",
    )
    sort_order: int = Field(
        0,
        ge=0,
        description="Display order (lower values appear first)",
    )


class MainCategoryCreate(MainCategoryBase):
    """Schema for creating a new main category."""

    pass


class MainCategoryUpdate(BaseModel):
    """Schema for partially updating a main category.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Display name of the main category",
    )
    slug: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the category",
    )
    icon: str | None = Field(
        None,
        max_length=50,
        description="Icon identifier or emoji",
    )
    sort_order: int | None = Field(
        None,
        ge=0,
        description="Display order (lower values appear first)",
    )


class MainCategoryResponse(MainCategoryBase):
    """Schema returned when reading a main category."""

    id: StrUUID = Field(..., description="UUID primary key")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# SubCategory schemas
# ---------------------------------------------------------------------------


class SubCategoryBase(BaseModel):
    """Shared fields for SubCategory create/update operations."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the sub-category",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the sub-category",
    )
    sort_order: int = Field(
        0,
        ge=0,
        description="Display order (lower values appear first)",
    )


class SubCategoryCreate(SubCategoryBase):
    """Schema for creating a new sub-category."""

    main_category_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="UUID of the parent main category",
    )


class SubCategoryUpdate(BaseModel):
    """Schema for partially updating a sub-category.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Display name of the sub-category",
    )
    slug: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the sub-category",
    )
    sort_order: int | None = Field(
        None,
        ge=0,
        description="Display order (lower values appear first)",
    )


class SubCategoryResponse(SubCategoryBase):
    """Schema returned when reading a sub-category."""

    id: StrUUID = Field(..., description="UUID primary key")
    main_category_id: StrUUID = Field(
        ..., description="UUID of the parent main category"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
