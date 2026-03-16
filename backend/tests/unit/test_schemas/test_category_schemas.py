"""Tests for MainCategory and SubCategory Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.schemas.category import (
    MainCategoryBase,
    MainCategoryCreate,
    MainCategoryResponse,
    MainCategoryUpdate,
    SubCategoryBase,
    SubCategoryCreate,
    SubCategoryResponse,
    SubCategoryUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now()


def _uuid() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# MainCategoryCreate tests
# ---------------------------------------------------------------------------


class TestMainCategoryCreate:
    """Validate MainCategoryCreate schema."""

    def test_create_with_valid_data_returns_schema(self) -> None:
        schema = MainCategoryCreate(name="Videojuegos", slug="videojuegos")
        assert schema.name == "Videojuegos"
        assert schema.slug == "videojuegos"
        assert schema.description is None
        assert schema.icon is None
        assert schema.sort_order == 0

    def test_create_with_all_fields_returns_schema(self) -> None:
        schema = MainCategoryCreate(
            name="Música",
            slug="musica",
            description="Colecciones musicales",
            icon="🎵",
            sort_order=5,
        )
        assert schema.name == "Música"
        assert schema.description == "Colecciones musicales"
        assert schema.icon == "🎵"
        assert schema.sort_order == 5

    def test_create_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MainCategoryCreate(name="", slug="empty")
        assert "name" in str(exc_info.value)

    def test_create_without_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MainCategoryCreate(slug="no-name")  # type: ignore[call-arg]

    def test_create_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MainCategoryCreate(name="x" * 101, slug="too-long")
        assert "name" in str(exc_info.value)

    def test_create_with_name_at_max_length_succeeds(self) -> None:
        schema = MainCategoryCreate(name="x" * 100, slug="max")
        assert len(schema.name) == 100

    def test_create_with_empty_slug_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MainCategoryCreate(name="Valid", slug="")
        assert "slug" in str(exc_info.value)

    def test_create_with_negative_sort_order_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MainCategoryCreate(name="Test", slug="test", sort_order=-1)
        assert "sort_order" in str(exc_info.value)


# ---------------------------------------------------------------------------
# MainCategoryUpdate tests
# ---------------------------------------------------------------------------


class TestMainCategoryUpdate:
    """Validate MainCategoryUpdate schema (partial updates)."""

    def test_update_with_no_fields_returns_schema(self) -> None:
        schema = MainCategoryUpdate()
        assert schema.name is None
        assert schema.slug is None
        assert schema.description is None
        assert schema.icon is None
        assert schema.sort_order is None

    def test_update_with_name_only_returns_schema(self) -> None:
        schema = MainCategoryUpdate(name="Nuevo Nombre")
        assert schema.name == "Nuevo Nombre"
        assert schema.slug is None

    def test_update_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MainCategoryUpdate(name="")

    def test_update_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MainCategoryUpdate(name="x" * 101)


# ---------------------------------------------------------------------------
# MainCategoryResponse tests
# ---------------------------------------------------------------------------


class TestMainCategoryResponse:
    """Validate MainCategoryResponse schema and from_attributes."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = MainCategoryResponse(
            id=_uuid(),
            name="Videojuegos",
            slug="videojuegos",
            created_at=now,
            updated_at=now,
        )
        assert schema.name == "Videojuegos"
        assert schema.created_at == now

    def test_response_from_attributes_dict(self) -> None:
        """Simulate ORM-like object via dict."""
        now = _now()
        uid = _uuid()
        data = {
            "id": uid,
            "name": "TCG",
            "slug": "tcg",
            "description": None,
            "icon": "🃏",
            "sort_order": 2,
            "created_at": now,
            "updated_at": now,
        }
        schema = MainCategoryResponse.model_validate(data)
        assert schema.id == uid
        assert schema.icon == "🃏"

    def test_response_round_trip_serialization(self) -> None:
        """Create → dump → recreate produces identical data."""
        now = _now()
        uid = _uuid()
        original = MainCategoryResponse(
            id=uid,
            name="Libros",
            slug="libros",
            description="Colección de libros",
            icon="📚",
            sort_order=3,
            created_at=now,
            updated_at=now,
        )
        dumped = original.model_dump()
        recreated = MainCategoryResponse.model_validate(dumped)
        assert recreated == original

    def test_response_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MainCategoryResponse(
                name="No ID",
                slug="no-id",
                created_at=_now(),
                updated_at=_now(),
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# SubCategoryCreate tests
# ---------------------------------------------------------------------------


class TestSubCategoryCreate:
    """Validate SubCategoryCreate schema."""

    def test_create_with_valid_data_returns_schema(self) -> None:
        uid = _uuid()
        schema = SubCategoryCreate(
            main_category_id=uid,
            name="Consolas",
            slug="consolas",
        )
        assert schema.main_category_id == uid
        assert schema.name == "Consolas"
        assert schema.sort_order == 0

    def test_create_with_all_fields_returns_schema(self) -> None:
        schema = SubCategoryCreate(
            main_category_id=_uuid(),
            name="Juegos",
            slug="juegos",
            description="Juegos de la categoría",
            sort_order=1,
        )
        assert schema.description == "Juegos de la categoría"
        assert schema.sort_order == 1

    def test_create_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SubCategoryCreate(main_category_id=_uuid(), name="", slug="empty")
        assert "name" in str(exc_info.value)

    def test_create_without_main_category_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SubCategoryCreate(name="Orphan", slug="orphan")  # type: ignore[call-arg]

    def test_create_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SubCategoryCreate(
                main_category_id=_uuid(),
                name="x" * 101,
                slug="too-long",
            )

    def test_create_with_name_at_max_length_succeeds(self) -> None:
        schema = SubCategoryCreate(
            main_category_id=_uuid(),
            name="x" * 100,
            slug="max",
        )
        assert len(schema.name) == 100


# ---------------------------------------------------------------------------
# SubCategoryUpdate tests
# ---------------------------------------------------------------------------


class TestSubCategoryUpdate:
    """Validate SubCategoryUpdate schema (partial updates)."""

    def test_update_with_no_fields_returns_schema(self) -> None:
        schema = SubCategoryUpdate()
        assert schema.name is None
        assert schema.slug is None

    def test_update_with_name_only_returns_schema(self) -> None:
        schema = SubCategoryUpdate(name="Renamed")
        assert schema.name == "Renamed"

    def test_update_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SubCategoryUpdate(name="")


# ---------------------------------------------------------------------------
# SubCategoryResponse tests
# ---------------------------------------------------------------------------


class TestSubCategoryResponse:
    """Validate SubCategoryResponse schema and from_attributes."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = SubCategoryResponse(
            id=_uuid(),
            main_category_id=_uuid(),
            name="Vinilos",
            slug="vinilos",
            created_at=now,
            updated_at=now,
        )
        assert schema.name == "Vinilos"

    def test_response_from_attributes_dict(self) -> None:
        now = _now()
        uid = _uuid()
        parent_id = _uuid()
        data = {
            "id": uid,
            "main_category_id": parent_id,
            "name": "CDs",
            "slug": "cds",
            "description": "Compact discs",
            "sort_order": 1,
            "created_at": now,
            "updated_at": now,
        }
        schema = SubCategoryResponse.model_validate(data)
        assert schema.id == uid
        assert schema.main_category_id == parent_id

    def test_response_round_trip_serialization(self) -> None:
        now = _now()
        original = SubCategoryResponse(
            id=_uuid(),
            main_category_id=_uuid(),
            name="Pokemon",
            slug="pokemon",
            description="Pokemon TCG",
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
        dumped = original.model_dump()
        recreated = SubCategoryResponse.model_validate(dumped)
        assert recreated == original

    def test_response_missing_main_category_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SubCategoryResponse(
                id=_uuid(),
                name="Orphan",
                slug="orphan",
                created_at=_now(),
                updated_at=_now(),
            )  # type: ignore[call-arg]
