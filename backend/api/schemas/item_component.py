"""Pydantic v2 schemas for Item Components."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

ComponentType = Literal[
    "required",
    "optional",
    "accessory",
    "packaging",
    "documentation",
    "media",
    "hardware",
    "other",
]


# ---------------------------------------------------------------------------
# ItemComponent schemas
# ---------------------------------------------------------------------------


class ItemComponentBase(BaseModel):
    """Shared fields for ItemComponent create/read operations."""

    standard_component_id: StrUUID | None = Field(
        None,
        description="UUID of the standard component this is based on",
    )
    component_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the component (e.g., 'Box', 'Manual', 'Cartridge')",
    )
    component_type: ComponentType | None = Field(
        None,
        description="Type of component: required, optional, accessory, etc.",
    )
    is_present: bool = Field(
        True,
        description="Whether this component is present with the item",
    )
    condition: str | None = Field(
        None,
        max_length=50,
        description="Condition of this specific component",
    )
    condition_notes: str | None = Field(
        None,
        description="Notes about the condition of this component",
    )
    variant_description: str | None = Field(
        None,
        max_length=200,
        description="Description of variant (e.g., 'Greatest Hits version')",
    )

    @model_validator(mode="after")
    def _name_or_standard_required(self) -> "ItemComponentBase":
        """Validate that either standard_component_id or component_name is provided.

        component_name is required when standard_component_id is None.
        """
        # component_name is always required (min_length=1 handles this)
        # This validator is for documentation and future extensibility
        return self


class ItemComponentCreate(ItemComponentBase):
    """Schema for creating a new item component."""

    pass


class ItemComponentUpdate(BaseModel):
    """Schema for partially updating an item component.

    All fields are optional so callers can send only the fields they
    want to change.
    """

    standard_component_id: StrUUID | None = Field(
        None,
        description="UUID of the standard component this is based on",
    )
    component_name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name of the component",
    )
    component_type: ComponentType | None = Field(
        None,
        description="Type of component",
    )
    is_present: bool | None = Field(
        None,
        description="Whether this component is present",
    )
    condition: str | None = Field(
        None,
        max_length=50,
        description="Condition of this specific component",
    )
    condition_notes: str | None = Field(
        None,
        description="Notes about the condition",
    )
    variant_description: str | None = Field(
        None,
        max_length=200,
        description="Description of variant",
    )


class ItemComponentResponse(ItemComponentBase):
    """Schema returned when reading an item component."""

    id: StrUUID = Field(..., description="UUID primary key")
    collection_item_id: StrUUID = Field(
        ...,
        description="UUID of the collection item this component belongs to",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Component template entry
# ---------------------------------------------------------------------------


class ComponentTemplateEntry(BaseModel):
    """A template entry from standard components for a sub-category.

    This represents a standard component that should be checked off
    for items in a given sub-category.
    """

    standard_component_id: StrUUID = Field(
        ...,
        description="UUID of the standard component",
    )
    component_name: str = Field(
        ...,
        description="Name of the component",
    )
    component_type: ComponentType | None = Field(
        None,
        description="Type of component (required, optional, etc.)",
    )
    description: str | None = Field(
        None,
        description="Description of the component",
    )
    sort_order: int = Field(
        0,
        description="Sort order for display",
    )
    is_present: bool = Field(
        False,
        description="Whether this component has been recorded as present",
    )
    recorded_component_id: StrUUID | None = Field(
        None,
        description="UUID of the recorded ItemComponent if it exists",
    )

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Completeness result
# ---------------------------------------------------------------------------


class CompletenessResult(BaseModel):
    """Result of a completeness check after component changes.

    Returned after operations that may affect item completeness
    (create, update, delete components).
    """

    is_complete: bool = Field(
        ...,
        description="Whether the item is now complete (all required components present)",
    )
    required_count: int = Field(
        ...,
        description="Total number of required components for this item's sub-category",
    )
    present_count: int = Field(
        ...,
        description="Number of required components currently present",
    )
    missing_names: list[str] = Field(
        default_factory=list,
        description="Names of missing required components",
    )
