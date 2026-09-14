"""Pydantic v2 schemas for Collection validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# Collection schemas
# ---------------------------------------------------------------------------


class CollectionBase(BaseModel):
    """Shared fields for Collection create/read operations."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the collection",
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Optional description of the collection",
    )
    collection_type: Literal["single_category", "multi_category", "mixed"] = Field(
        "single_category",
        description="Type of collection",
    )
    theme: str | None = Field(
        None,
        max_length=100,
        description="Optional theme for the collection",
    )
    restricted_to_sub_category_id: str | None = Field(
        None,
        description="UUID of the restricted sub-category (required for single_category)",
    )
    goal_description: str | None = Field(
        None,
        description="Optional goal description",
    )
    goal_items_count: int | None = Field(
        None,
        ge=0,
        description="Target number of items in the collection",
    )
    display_order: str = Field(
        "custom",
        description="Display order strategy",
    )
    is_public: bool = Field(
        False,
        description="Whether the collection is publicly visible",
    )

    @model_validator(mode="after")
    def validate_single_category_restriction(self) -> CollectionBase:
        """If type=single_category, restricted_to_sub_category_id is required."""
        if (
            self.collection_type == "single_category"
            and self.restricted_to_sub_category_id is None
        ):
            raise ValueError(
                "restricted_to_sub_category_id is required for single_category collections"
            )
        return self


class CollectionCreate(CollectionBase):
    """Schema for creating a new collection."""

    pass


class CollectionUpdate(BaseModel):
    """Schema for partially updating a collection.

    All fields are optional so callers can send only the fields they
    want to change. No model_validator since partial updates should not
    enforce the single_category constraint.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Display name of the collection",
    )
    description: str | None = Field(
        None,
        description="Optional description of the collection",
    )
    theme: str | None = Field(
        None,
        max_length=100,
        description="Optional theme for the collection",
    )
    goal_description: str | None = Field(
        None,
        description="Optional goal description",
    )
    goal_items_count: int | None = Field(
        None,
        ge=0,
        description="Target number of items in the collection",
    )
    display_order: str | None = Field(
        None,
        description="Display order strategy",
    )
    is_public: bool | None = Field(
        None,
        description="Whether the collection is publicly visible",
    )
    is_active: bool | None = Field(
        None,
        description="Whether the collection is active",
    )


class CollectionResponse(CollectionBase):
    """Schema returned when reading a collection."""

    id: StrUUID = Field(..., description="UUID primary key")
    is_active: bool = Field(..., description="Whether the collection is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Collection stats and grouping schemas
# ---------------------------------------------------------------------------


class CollectionItemGroup(BaseModel):
    """Group of collection items by category."""

    main_category_id: str | None = Field(
        None, description="UUID of the main category"
    )
    main_category_name: str | None = Field(
        None, description="Name of the main category"
    )
    sub_category_id: str | None = Field(
        None, description="UUID of the sub category"
    )
    sub_category_name: str | None = Field(
        None, description="Name of the sub category"
    )
    item_count: int = Field(..., description="Number of items in this group")

    model_config = ConfigDict(from_attributes=True)


class CollectionStats(BaseModel):
    """Statistics for a collection."""

    total_items: int = Field(..., description="Total number of items")
    different_categories_count: int = Field(
        ..., description="Number of distinct categories"
    )
    total_invested: float | None = Field(
        None, description="Total amount invested"
    )
    current_value: float | None = Field(
        None, description="Current market value"
    )
    value_gain: float | None = Field(
        None, description="Difference between current value and investment"
    )
    roi_percentage: float | None = Field(
        None, description="Return on investment percentage"
    )
    complete_items: int = Field(
        ..., description="Number of complete items"
    )
    graded_items: int = Field(
        ..., description="Number of graded items"
    )

    model_config = ConfigDict(from_attributes=True)
