"""Tests for Collection and CollectionItem Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.schemas.collection import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
)
from api.schemas.collection_item import (
    CollectionItemCreate,
    CollectionItemResponse,
    CollectionItemUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now()


def _uuid() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# CollectionCreate tests
# ---------------------------------------------------------------------------


class TestCollectionCreate:
    """Validate CollectionCreate schema."""

    def test_create_single_category_without_sub_category_id_raises_validation_error(
        self,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionCreate(
                name="My N64 Collection",
                collection_type="single_category",
            )
        assert "restricted_to_sub_category_id" in str(exc_info.value)

    def test_create_single_category_with_sub_category_id_succeeds(self) -> None:
        sub_id = _uuid()
        schema = CollectionCreate(
            name="My N64 Collection",
            collection_type="single_category",
            restricted_to_sub_category_id=sub_id,
        )
        assert schema.name == "My N64 Collection"
        assert schema.collection_type == "single_category"
        assert schema.restricted_to_sub_category_id == sub_id

    def test_create_multi_category_without_sub_category_id_succeeds(self) -> None:
        schema = CollectionCreate(
            name="Mixed Gaming",
            collection_type="multi_category",
        )
        assert schema.collection_type == "multi_category"
        assert schema.restricted_to_sub_category_id is None

    def test_create_mixed_without_sub_category_id_succeeds(self) -> None:
        schema = CollectionCreate(
            name="Everything",
            collection_type="mixed",
        )
        assert schema.collection_type == "mixed"
        assert schema.restricted_to_sub_category_id is None

    def test_create_defaults_to_single_category(self) -> None:
        sub_id = _uuid()
        schema = CollectionCreate(
            name="Default Type",
            restricted_to_sub_category_id=sub_id,
        )
        assert schema.collection_type == "single_category"

    def test_create_with_all_fields_returns_schema(self) -> None:
        sub_id = _uuid()
        schema = CollectionCreate(
            name="Complete Collection",
            description="A fully specified collection",
            collection_type="single_category",
            theme="Retro Gaming",
            restricted_to_sub_category_id=sub_id,
            goal_description="Collect all N64 games",
            goal_items_count=296,
            display_order="alphabetical",
            is_public=True,
        )
        assert schema.description == "A fully specified collection"
        assert schema.theme == "Retro Gaming"
        assert schema.goal_items_count == 296
        assert schema.display_order == "alphabetical"
        assert schema.is_public is True

    def test_create_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionCreate(
                name="",
                collection_type="multi_category",
            )
        assert "name" in str(exc_info.value)

    def test_create_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionCreate(
                name="x" * 201,
                collection_type="multi_category",
            )
        assert "name" in str(exc_info.value)

    def test_create_with_invalid_collection_type_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionCreate(
                name="Bad Type",
                collection_type="invalid_type",  # type: ignore[arg-type]
            )
        assert "collection_type" in str(exc_info.value)

    def test_create_with_negative_goal_items_count_raises_validation_error(
        self,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionCreate(
                name="Negative Goal",
                collection_type="multi_category",
                goal_items_count=-1,
            )
        assert "goal_items_count" in str(exc_info.value)


# ---------------------------------------------------------------------------
# CollectionUpdate tests
# ---------------------------------------------------------------------------


class TestCollectionUpdate:
    """Validate CollectionUpdate schema (partial updates)."""

    def test_update_with_no_fields_returns_schema(self) -> None:
        schema = CollectionUpdate()
        assert schema.name is None
        assert schema.description is None
        assert schema.is_public is None
        assert schema.is_active is None

    def test_update_with_name_only_returns_schema(self) -> None:
        schema = CollectionUpdate(name="Renamed Collection")
        assert schema.name == "Renamed Collection"
        assert schema.description is None

    def test_update_partial_fields_returns_schema(self) -> None:
        schema = CollectionUpdate(
            name="Updated",
            is_public=True,
            is_active=False,
        )
        assert schema.name == "Updated"
        assert schema.is_public is True
        assert schema.is_active is False
        assert schema.theme is None
        assert schema.goal_description is None

    def test_update_with_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CollectionUpdate(name="")

    def test_update_with_name_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CollectionUpdate(name="x" * 201)

    def test_update_with_negative_goal_items_count_raises_validation_error(
        self,
    ) -> None:
        with pytest.raises(ValidationError):
            CollectionUpdate(goal_items_count=-5)


# ---------------------------------------------------------------------------
# CollectionResponse tests
# ---------------------------------------------------------------------------


class TestCollectionResponse:
    """Validate CollectionResponse schema and from_attributes."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        sub_id = _uuid()
        schema = CollectionResponse(
            id=_uuid(),
            name="N64 Games",
            collection_type="single_category",
            restricted_to_sub_category_id=sub_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert schema.name == "N64 Games"
        assert schema.is_active is True

    def test_response_from_attributes_dict(self) -> None:
        now = _now()
        uid = _uuid()
        sub_id = _uuid()
        data = {
            "id": uid,
            "name": "Vinyl Records",
            "description": "My vinyl collection",
            "collection_type": "multi_category",
            "theme": None,
            "restricted_to_sub_category_id": None,
            "goal_description": None,
            "goal_items_count": None,
            "display_order": "custom",
            "is_public": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        schema = CollectionResponse.model_validate(data)
        assert schema.id == uid
        assert schema.description == "My vinyl collection"

    def test_response_round_trip_serialization(self) -> None:
        now = _now()
        sub_id = _uuid()
        original = CollectionResponse(
            id=_uuid(),
            name="Complete Collection",
            description="Full description",
            collection_type="single_category",
            theme="Retro",
            restricted_to_sub_category_id=sub_id,
            goal_description="Collect them all",
            goal_items_count=100,
            display_order="alphabetical",
            is_public=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        dumped = original.model_dump()
        recreated = CollectionResponse.model_validate(dumped)
        assert recreated == original


# ---------------------------------------------------------------------------
# CollectionItemCreate tests
# ---------------------------------------------------------------------------


class TestCollectionItemCreate:
    """Validate CollectionItemCreate schema."""

    def test_create_with_valid_data_returns_schema(self) -> None:
        schema = CollectionItemCreate(
            catalog_item_id=_uuid(),
            condition="excellent",
        )
        assert schema.condition == "excellent"
        assert schema.is_complete is False
        assert schema.purchase_currency == "USD"

    def test_create_with_all_fields_returns_schema(self) -> None:
        cat_id = _uuid()
        schema = CollectionItemCreate(
            catalog_item_id=cat_id,
            condition="mint",
            is_complete=True,
            notes="Sealed in original packaging",
            purchase_price=Decimal("45.99"),
            purchase_currency="EUR",
            purchase_date=date(2024, 1, 15),
            acquisition_type="purchase",
            storage_location="Shelf A3",
        )
        assert schema.catalog_item_id == cat_id
        assert schema.condition == "mint"
        assert schema.is_complete is True
        assert schema.purchase_price == Decimal("45.99")
        assert schema.purchase_currency == "EUR"
        assert schema.purchase_date == date(2024, 1, 15)
        assert schema.acquisition_type == "purchase"
        assert schema.storage_location == "Shelf A3"

    def test_create_with_all_valid_conditions_succeeds(self) -> None:
        valid_conditions = ["mint", "near_mint", "excellent", "good", "fair", "poor"]
        for cond in valid_conditions:
            schema = CollectionItemCreate(
                catalog_item_id=_uuid(),
                condition=cond,  # type: ignore[arg-type]
            )
            assert schema.condition == cond

    def test_create_with_invalid_condition_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionItemCreate(
                catalog_item_id=_uuid(),
                condition="broken",  # type: ignore[arg-type]
            )
        assert "condition" in str(exc_info.value)

    def test_create_with_negative_purchase_price_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionItemCreate(
                catalog_item_id=_uuid(),
                condition="good",
                purchase_price=Decimal("-10.00"),
            )
        assert "purchase_price" in str(exc_info.value)

    def test_create_with_zero_purchase_price_succeeds(self) -> None:
        schema = CollectionItemCreate(
            catalog_item_id=_uuid(),
            condition="good",
            purchase_price=Decimal("0"),
        )
        assert schema.purchase_price == Decimal("0")

    def test_create_with_all_valid_acquisition_types_succeeds(self) -> None:
        valid_types = ["purchase", "gift", "trade", "found", "inherited"]
        for acq_type in valid_types:
            schema = CollectionItemCreate(
                catalog_item_id=_uuid(),
                condition="good",
                acquisition_type=acq_type,  # type: ignore[arg-type]
            )
            assert schema.acquisition_type == acq_type

    def test_create_with_invalid_acquisition_type_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CollectionItemCreate(
                catalog_item_id=_uuid(),
                condition="good",
                acquisition_type="stolen",  # type: ignore[arg-type]
            )
        assert "acquisition_type" in str(exc_info.value)

    def test_create_without_catalog_item_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CollectionItemCreate(condition="good")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# CollectionItemUpdate tests
# ---------------------------------------------------------------------------


class TestCollectionItemUpdate:
    """Validate CollectionItemUpdate schema (partial updates)."""

    def test_update_with_no_fields_returns_schema(self) -> None:
        schema = CollectionItemUpdate()
        assert schema.condition is None
        assert schema.is_complete is None
        assert schema.notes is None
        assert schema.purchase_price is None

    def test_update_with_condition_only_returns_schema(self) -> None:
        schema = CollectionItemUpdate(condition="mint")
        assert schema.condition == "mint"
        assert schema.notes is None

    def test_update_with_invalid_condition_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CollectionItemUpdate(condition="destroyed")  # type: ignore[arg-type]

    def test_update_with_negative_purchase_price_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CollectionItemUpdate(purchase_price=Decimal("-5.00"))


# ---------------------------------------------------------------------------
# CollectionItemResponse tests
# ---------------------------------------------------------------------------


class TestCollectionItemResponse:
    """Validate CollectionItemResponse schema and from_attributes."""

    def test_response_with_valid_data_returns_schema(self) -> None:
        now = _now()
        schema = CollectionItemResponse(
            id=_uuid(),
            collection_id=_uuid(),
            catalog_item_id=_uuid(),
            condition="excellent",
            is_complete=True,
            created_at=now,
            updated_at=now,
        )
        assert schema.condition == "excellent"
        assert schema.is_complete is True

    def test_response_from_attributes_dict(self) -> None:
        now = _now()
        uid = _uuid()
        col_id = _uuid()
        cat_id = _uuid()
        data = {
            "id": uid,
            "collection_id": col_id,
            "catalog_item_id": cat_id,
            "condition": "good",
            "is_complete": False,
            "notes": "Minor scratch on label",
            "purchase_price": Decimal("25.50"),
            "purchase_currency": "USD",
            "purchase_date": date(2023, 6, 15),
            "acquisition_type": "purchase",
            "storage_location": "Box 7",
            "created_at": now,
            "updated_at": now,
        }
        schema = CollectionItemResponse.model_validate(data)
        assert schema.id == uid
        assert schema.collection_id == col_id
        assert schema.notes == "Minor scratch on label"
        assert schema.purchase_price == Decimal("25.50")

    def test_response_round_trip_serialization(self) -> None:
        now = _now()
        original = CollectionItemResponse(
            id=_uuid(),
            collection_id=_uuid(),
            catalog_item_id=_uuid(),
            condition="mint",
            is_complete=True,
            notes="Perfect condition",
            purchase_price=Decimal("99.99"),
            purchase_currency="EUR",
            purchase_date=date(2024, 3, 1),
            acquisition_type="gift",
            storage_location="Display Case",
            created_at=now,
            updated_at=now,
        )
        dumped = original.model_dump()
        recreated = CollectionItemResponse.model_validate(dumped)
        assert recreated == original
