"""Tests for ItemImage Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.schemas.image import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_SIZE,
    ImageUploadResponse,
    ItemImageResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now()


def _uuid() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# ItemImageResponse tests
# ---------------------------------------------------------------------------


class TestItemImageResponse:
    """Validate ItemImageResponse schema."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = ItemImageResponse(
            id=_uuid(),
            collection_item_id=_uuid(),
            file_path="/uploads/abc/image.jpg",
            file_name="image.jpg",
            file_size=204800,
            mime_type="image/jpeg",
            image_type="front",
            description="Front cover photo",
            is_primary=True,
            uploaded_at=now,
        )
        assert schema.file_name == "image.jpg"
        assert schema.file_size == 204800
        assert schema.mime_type == "image/jpeg"
        assert schema.image_type == "front"
        assert schema.is_primary is True

    def test_response_from_attributes_dict(self) -> None:
        now = _now()
        uid = _uuid()
        item_id = _uuid()
        data = {
            "id": uid,
            "collection_item_id": item_id,
            "file_path": "/uploads/item1/photo.png",
            "file_name": "photo.png",
            "file_size": 512000,
            "mime_type": "image/png",
            "image_type": "back",
            "description": "Back of the box",
            "is_primary": False,
            "uploaded_at": now,
        }
        schema = ItemImageResponse.model_validate(data)
        assert schema.id == uid
        assert schema.collection_item_id == item_id
        assert schema.file_path == "/uploads/item1/photo.png"
        assert schema.description == "Back of the box"

    def test_response_round_trip_serialization(self) -> None:
        now = _now()
        original = ItemImageResponse(
            id=_uuid(),
            collection_item_id=_uuid(),
            file_path="/uploads/x/img.webp",
            file_name="img.webp",
            file_size=1048576,
            mime_type="image/webp",
            image_type="detail",
            description="Close-up detail",
            is_primary=False,
            uploaded_at=now,
        )
        dumped = original.model_dump()
        recreated = ItemImageResponse.model_validate(dumped)
        assert recreated == original

    def test_response_with_nullable_fields_as_none(self) -> None:
        now = _now()
        schema = ItemImageResponse(
            id=_uuid(),
            collection_item_id=_uuid(),
            file_path="/uploads/y/pic.jpg",
            file_name="pic.jpg",
            file_size=None,
            mime_type=None,
            image_type=None,
            description=None,
            is_primary=False,
            uploaded_at=now,
        )
        assert schema.file_size is None
        assert schema.mime_type is None
        assert schema.image_type is None
        assert schema.description is None

    def test_response_missing_required_fields_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ItemImageResponse()  # type: ignore[call-arg]

    def test_response_missing_file_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ItemImageResponse(
                id=_uuid(),
                collection_item_id=_uuid(),
                file_name="img.jpg",
                is_primary=True,
                uploaded_at=_now(),
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ImageUploadResponse tests
# ---------------------------------------------------------------------------


class TestImageUploadResponse:
    """Validate ImageUploadResponse schema."""

    def test_upload_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = ImageUploadResponse(
            id=_uuid(),
            file_name="uploaded.jpg",
            file_size=300000,
            mime_type="image/jpeg",
            is_primary=True,
            uploaded_at=now,
        )
        assert schema.file_name == "uploaded.jpg"
        assert schema.is_primary is True

    def test_upload_response_round_trip_serialization(self) -> None:
        now = _now()
        original = ImageUploadResponse(
            id=_uuid(),
            file_name="photo.png",
            file_size=500000,
            mime_type="image/png",
            is_primary=False,
            uploaded_at=now,
        )
        dumped = original.model_dump()
        recreated = ImageUploadResponse.model_validate(dumped)
        assert recreated == original


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestImageConstants:
    """Validate image-related constants."""

    def test_allowed_image_types_contains_jpeg(self) -> None:
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES

    def test_allowed_image_types_contains_png(self) -> None:
        assert "image/png" in ALLOWED_IMAGE_TYPES

    def test_allowed_image_types_contains_webp(self) -> None:
        assert "image/webp" in ALLOWED_IMAGE_TYPES

    def test_allowed_image_types_has_exactly_three_entries(self) -> None:
        assert len(ALLOWED_IMAGE_TYPES) == 3

    def test_max_image_size_equals_10mb(self) -> None:
        assert MAX_IMAGE_SIZE == 10 * 1024 * 1024
