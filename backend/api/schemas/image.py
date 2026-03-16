"""Pydantic v2 schemas for ItemImage validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import StrUUID


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# ItemImage schemas
# ---------------------------------------------------------------------------


class ItemImageResponse(BaseModel):
    """Schema returned when reading an item image."""

    id: StrUUID = Field(..., description="UUID primary key")
    collection_item_id: StrUUID = Field(
        ..., description="UUID of the parent collection item"
    )
    file_path: str = Field(..., description="Path to the image file on disk")
    file_name: str = Field(..., description="Original file name")
    file_size: int | None = Field(None, description="File size in bytes")
    mime_type: str | None = Field(None, description="MIME type of the image")
    image_type: str | None = Field(
        None, description="Image category, e.g. front, back, detail"
    )
    description: str | None = Field(None, description="Optional image description")
    is_primary: bool = Field(..., description="Whether this is the primary image")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class ImageUploadResponse(BaseModel):
    """Lightweight response returned after a successful image upload."""

    id: StrUUID = Field(..., description="UUID of the newly created image")
    file_name: str = Field(..., description="Original file name")
    file_size: int | None = Field(None, description="File size in bytes")
    mime_type: str | None = Field(None, description="MIME type of the image")
    is_primary: bool = Field(..., description="Whether this is the primary image")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)
