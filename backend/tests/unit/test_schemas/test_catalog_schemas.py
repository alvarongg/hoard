"""Tests for Catalog and CatalogItem Pydantic schemas."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.schemas.catalog import (
    CatalogCreate,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogItemUpdate,
    CatalogResponse,
    CatalogUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now()


def _uuid() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# CatalogCreate tests
# ---------------------------------------------------------------------------


class TestCatalogCreate:
    """Validate CatalogCreate schema."""

    def test_create_with_valid_data_returns_schema(self) -> None:
        schema = CatalogCreate(
            name="All N64 Games",
            sub_category_id=_uuid(),
        )
        assert schema.name == "All N64 Games"
        assert schema.description is None
        assert schema.is_active is True

    def test_create_with_all_fields_returns_schema(self) -> None:
        uid = _uuid()
        schema = CatalogCreate(
            name="SNES Collection",
            sub_category_id=uid,
            description="Complete SNES catalog",
            is_active=False,
        )
        assert schema.name == "SNES Collection"
        assert schema.sub_category_id == uid
        assert schema.description == "Complete SNES catalog"
        assert schema.is_active is False

    def test_create_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CatalogCreate(name="", sub_category_id=_uuid())
        assert "name" in str(exc_info.value)

    def test_create_without_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogCreate(sub_category_id=_uuid())  # type: ignore[call-arg]

    def test_create_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CatalogCreate(name="x" * 201, sub_category_id=_uuid())
        assert "name" in str(exc_info.value)

    def test_create_with_name_at_max_length_succeeds(self) -> None:
        schema = CatalogCreate(name="x" * 200, sub_category_id=_uuid())
        assert len(schema.name) == 200

    def test_create_without_sub_category_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogCreate(name="Valid")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# CatalogUpdate tests
# ---------------------------------------------------------------------------


class TestCatalogUpdate:
    """Validate CatalogUpdate schema (partial updates)."""

    def test_update_with_no_fields_returns_schema(self) -> None:
        schema = CatalogUpdate()
        assert schema.name is None
        assert schema.description is None
        assert schema.is_active is None

    def test_update_with_name_only_returns_schema(self) -> None:
        schema = CatalogUpdate(name="Renamed Catalog")
        assert schema.name == "Renamed Catalog"
        assert schema.description is None

    def test_update_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogUpdate(name="")

    def test_update_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogUpdate(name="x" * 201)


# ---------------------------------------------------------------------------
# CatalogResponse tests
# ---------------------------------------------------------------------------


class TestCatalogResponse:
    """Validate CatalogResponse schema and from_attributes."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = CatalogResponse(
            id=_uuid(),
            sub_category_id=_uuid(),
            name="N64 Games",
            total_items=42,
            created_at=now,
            updated_at=now,
        )
        assert schema.name == "N64 Games"
        assert schema.total_items == 42

    def test_response_from_attributes_dict(self) -> None:
        now = _now()
        uid = _uuid()
        sub_id = _uuid()
        data = {
            "id": uid,
            "sub_category_id": sub_id,
            "name": "GameBoy Catalog",
            "description": "All GB games",
            "is_active": True,
            "total_items": 10,
            "created_at": now,
            "updated_at": now,
        }
        schema = CatalogResponse.model_validate(data)
        assert schema.id == uid
        assert schema.sub_category_id == sub_id
        assert schema.description == "All GB games"

    def test_response_round_trip_serialization(self) -> None:
        now = _now()
        original = CatalogResponse(
            id=_uuid(),
            sub_category_id=_uuid(),
            name="Vinyl Records",
            description="Complete vinyl catalog",
            is_active=True,
            total_items=100,
            created_at=now,
            updated_at=now,
        )
        dumped = original.model_dump()
        recreated = CatalogResponse.model_validate(dumped)
        assert recreated == original

    def test_response_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogResponse(
                sub_category_id=_uuid(),
                name="No ID",
                created_at=_now(),
                updated_at=_now(),
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# CatalogItemCreate tests
# ---------------------------------------------------------------------------


class TestCatalogItemCreate:
    """Validate CatalogItemCreate schema."""

    def test_create_with_valid_data_returns_schema(self) -> None:
        schema = CatalogItemCreate(
            title="Super Mario 64",
            catalog_id=_uuid(),
        )
        assert schema.title == "Super Mario 64"
        assert schema.subtitle is None
        assert schema.custom_fields == {}

    def test_create_with_all_fields_returns_schema(self) -> None:
        uid = _uuid()
        schema = CatalogItemCreate(
            catalog_id=uid,
            title="The Legend of Zelda: Ocarina of Time",
            subtitle="Gold Cartridge Edition",
            description="Classic N64 adventure game",
            release_date=date(1998, 11, 21),
            manufacturer="Nintendo",
            publisher="Nintendo",
            developer="Nintendo EAD",
            brand="Nintendo",
            language="English",
            region="NTSC",
            rarity="Uncommon",
            custom_fields={"players": 1, "genre": "Action-Adventure"},
            cover_image_url="https://example.com/zelda.jpg",
        )
        assert schema.catalog_id == uid
        assert schema.release_date == date(1998, 11, 21)
        assert schema.custom_fields["players"] == 1
        assert schema.region == "NTSC"

    def test_create_with_empty_title_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CatalogItemCreate(title="", catalog_id=_uuid())
        assert "title" in str(exc_info.value)

    def test_create_without_title_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogItemCreate(catalog_id=_uuid())  # type: ignore[call-arg]

    def test_create_with_title_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CatalogItemCreate(title="x" * 501, catalog_id=_uuid())
        assert "title" in str(exc_info.value)

    def test_create_with_title_at_max_length_succeeds(self) -> None:
        schema = CatalogItemCreate(title="x" * 500, catalog_id=_uuid())
        assert len(schema.title) == 500

    def test_create_without_catalog_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogItemCreate(title="Valid Title")  # type: ignore[call-arg]

    def test_create_custom_fields_accepts_dict(self) -> None:
        schema = CatalogItemCreate(
            title="Test Item",
            catalog_id=_uuid(),
            custom_fields={"key": "value", "nested": {"a": 1}},
        )
        assert schema.custom_fields["key"] == "value"
        assert schema.custom_fields["nested"]["a"] == 1

    def test_create_custom_fields_defaults_to_empty_dict(self) -> None:
        schema = CatalogItemCreate(title="Test", catalog_id=_uuid())
        assert schema.custom_fields == {}


# ---------------------------------------------------------------------------
# CatalogItemUpdate tests
# ---------------------------------------------------------------------------


class TestCatalogItemUpdate:
    """Validate CatalogItemUpdate schema (partial updates)."""

    def test_update_with_no_fields_returns_schema(self) -> None:
        schema = CatalogItemUpdate()
        assert schema.title is None
        assert schema.subtitle is None
        assert schema.custom_fields is None

    def test_update_with_title_only_returns_schema(self) -> None:
        schema = CatalogItemUpdate(title="Updated Title")
        assert schema.title == "Updated Title"
        assert schema.description is None

    def test_update_with_empty_title_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogItemUpdate(title="")

    def test_update_with_title_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogItemUpdate(title="x" * 501)

    def test_update_custom_fields_accepts_dict(self) -> None:
        schema = CatalogItemUpdate(custom_fields={"updated": True})
        assert schema.custom_fields == {"updated": True}


# ---------------------------------------------------------------------------
# CatalogItemResponse tests
# ---------------------------------------------------------------------------


class TestCatalogItemResponse:
    """Validate CatalogItemResponse schema and from_attributes."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = CatalogItemResponse(
            id=_uuid(),
            catalog_id=_uuid(),
            title="Super Mario 64",
            created_at=now,
            updated_at=now,
        )
        assert schema.title == "Super Mario 64"
        assert schema.custom_fields == {}

    def test_response_from_attributes_dict(self) -> None:
        now = _now()
        uid = _uuid()
        cat_id = _uuid()
        data = {
            "id": uid,
            "catalog_id": cat_id,
            "title": "GoldenEye 007",
            "subtitle": None,
            "description": "FPS classic",
            "release_date": date(1997, 8, 25),
            "manufacturer": "Rare",
            "publisher": "Nintendo",
            "developer": "Rare",
            "brand": None,
            "language": "English",
            "region": "NTSC",
            "rarity": "Common",
            "custom_fields": {"multiplayer": True},
            "cover_image_url": "https://example.com/goldeneye.jpg",
            "created_at": now,
            "updated_at": now,
        }
        schema = CatalogItemResponse.model_validate(data)
        assert schema.id == uid
        assert schema.catalog_id == cat_id
        assert schema.custom_fields["multiplayer"] is True

    def test_response_round_trip_serialization(self) -> None:
        now = _now()
        original = CatalogItemResponse(
            id=_uuid(),
            catalog_id=_uuid(),
            title="Banjo-Kazooie",
            subtitle="Collector's Edition",
            description="3D platformer",
            release_date=date(1998, 6, 29),
            manufacturer="Rare",
            publisher="Nintendo",
            developer="Rare",
            brand="Rare",
            language="English",
            region="PAL",
            rarity="Rare",
            custom_fields={"genre": "Platformer"},
            cover_image_url="https://example.com/banjo.jpg",
            created_at=now,
            updated_at=now,
        )
        dumped = original.model_dump()
        recreated = CatalogItemResponse.model_validate(dumped)
        assert recreated == original

    def test_response_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CatalogItemResponse(
                catalog_id=_uuid(),
                title="No ID",
                created_at=_now(),
                updated_at=_now(),
            )  # type: ignore[call-arg]
