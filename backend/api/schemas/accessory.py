"""Pydantic v2 schemas for accessories stock and assignments."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


class AccessoryBase(BaseModel):
    """Shared fields for accessory create/read."""

    name: str = Field(..., min_length=1, max_length=200)
    category: str | None = Field(None, max_length=100)
    subcategory: str | None = Field(None, max_length=100)
    compatible_sub_categories: list[str] | None = Field(None)
    size_specifications: dict | None = Field(None)
    quantity_total: int = Field(0, ge=0)
    minimum_stock_alert: int = Field(5, ge=0)
    reorder_quantity: int | None = Field(None, ge=0)
    unit_cost: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    currency: str = Field("USD", min_length=3, max_length=3)
    supplier_id: StrUUID | None = Field(None)
    supplier_sku: str | None = Field(None, max_length=100)
    supplier_url: str | None = Field(None, max_length=500)
    notes: str | None = Field(None)


class AccessoryCreate(AccessoryBase):
    """Schema for creating an accessory."""


class AccessoryUpdate(BaseModel):
    """Schema for updating an accessory (all optional)."""

    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = Field(None, max_length=100)
    subcategory: str | None = Field(None, max_length=100)
    compatible_sub_categories: list[str] | None = Field(None)
    size_specifications: dict | None = Field(None)
    quantity_total: int | None = Field(None, ge=0)
    minimum_stock_alert: int | None = Field(None, ge=0)
    reorder_quantity: int | None = Field(None, ge=0)
    unit_cost: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    currency: str | None = Field(None, min_length=3, max_length=3)
    supplier_id: StrUUID | None = Field(None)
    supplier_sku: str | None = Field(None, max_length=100)
    supplier_url: str | None = Field(None, max_length=500)
    notes: str | None = Field(None)


class AccessoryResponse(AccessoryBase):
    """Schema for reading an accessory with derived stock figures."""

    model_config = ConfigDict(from_attributes=True)

    id: StrUUID
    quantity_in_use: int
    quantity_available: int
    is_low_stock: bool


class LowStockEntry(BaseModel):
    """An accessory below its minimum-stock threshold."""

    id: StrUUID
    name: str
    quantity_available: int
    minimum_stock_alert: int
    reorder_quantity: int | None = None


class ItemAccessoryCreate(BaseModel):
    """Schema for assigning an accessory to a collection item."""

    accessory_id: StrUUID
    quantity_used: int = Field(1, ge=1)
    notes: str | None = Field(None)


class ItemAccessoryResponse(BaseModel):
    """Schema for reading an item-accessory assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: StrUUID
    collection_item_id: StrUUID
    accessory_id: StrUUID
    quantity_used: int
    assigned_at: datetime | None = None
    notes: str | None = None
