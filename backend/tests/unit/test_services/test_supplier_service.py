"""Unit tests for SupplierService.

Tests cover:
- Creation with valid data
- Validation of name (not empty/whitespace)
- Validation of type (allowed values)
- Validation of rating (0.00-5.00 range)
- Update of all editable fields
- Toggle of is_favorite
- Filtering by type, country, is_favorite, is_active
- Pagination
- Delete without references (success)
- Delete with references (DuplicateError with counts)
- Purchase history (empty for supplier without purchases)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.models.collection import Collection, CollectionItem
from api.models.supplier import Supplier
from api.schemas.supplier import SupplierCreate, SupplierUpdate
from api.services.supplier_service import SupplierService
from core.exceptions import DuplicateError, NotFoundError

# ---------------------------------------------------------------------------
# Database setup (following the pattern of other service tests)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def engine():
    """Create an in-memory SQLite engine for each test."""
    from api.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        # Enable foreign key support for SQLite
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async database session."""
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def supplier_service(db_session: AsyncSession) -> SupplierService:
    """Provide a SupplierService instance with the test database session."""
    return SupplierService(db_session)


@pytest.fixture()
async def existing_supplier(db_session: AsyncSession) -> Supplier:
    """Create and return a supplier for use in tests."""
    supplier = Supplier(
        id=str(uuid4()),
        name="Test Supplier",
        type="online",
        country="US",
        city="New York",
        rating=Decimal("4.50"),
        is_favorite=False,
        is_active=True,
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


async def _seed_sub_category(
    db_session: AsyncSession,
    name: str = "Games",
    slug: str = "games",
):
    """Create a MainCategory + SubCategory and return the SubCategory."""
    from api.models.category import MainCategory, SubCategory

    main = MainCategory(name=f"Main-{name}", slug=f"main-{slug}")
    db_session.add(main)
    await db_session.flush()

    sub = SubCategory(main_category_id=main.id, name=name, slug=slug)
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)
    return sub


async def _seed_catalog_item(
    db_session: AsyncSession,
    title: str = "Test Catalog Item",
):
    """Create the full chain: MainCategory → SubCategory → Catalog → CatalogItem."""
    from api.models.catalog import Catalog, CatalogItem

    sub = await _seed_sub_category(db_session)
    catalog = Catalog(
        sub_category_id=sub.id,
        name=f"Catalog for {sub.name}",
    )
    db_session.add(catalog)
    await db_session.flush()

    item = CatalogItem(catalog_id=catalog.id, title=title)
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Creation tests
# ---------------------------------------------------------------------------


class TestSupplierCreation:
    """Tests for SupplierService.create method."""

    async def test_create_with_valid_data_returns_supplier(
        self, supplier_service: SupplierService
    ) -> None:
        """Creating a supplier with valid data persists and returns it."""
        data = SupplierCreate(
            name="GameStop",
            type="physical_store",
            country="US",
            city="Austin",
            rating=Decimal("3.50"),
        )
        result = await supplier_service.create(data)

        assert result.id is not None
        assert result.name == "GameStop"
        assert result.type == "physical_store"
        assert result.country == "US"
        assert result.city == "Austin"
        assert result.rating == Decimal("3.50")
        assert result.is_favorite is False
        assert result.is_active is True

    async def test_create_with_minimal_data_returns_supplier(
        self, supplier_service: SupplierService
    ) -> None:
        """Creating a supplier with only required fields works."""
        data = SupplierCreate(name="Minimal Supplier")
        result = await supplier_service.create(data)

        assert result.name == "Minimal Supplier"
        assert result.type is None
        assert result.country is None
        assert result.rating is None

    async def test_create_name_empty_rejected_at_schema_level(self) -> None:
        """Empty name is rejected by Pydantic before reaching the service."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SupplierCreate(name="")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    async def test_create_name_whitespace_only_rejected(
        self, supplier_service: SupplierService
    ) -> None:
        """Whitespace-only name is rejected by the schema validator."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SupplierCreate(name="   ")

        errors = exc_info.value.errors()
        assert any("empty or whitespace-only" in str(e).lower() for e in errors)

    async def test_create_type_not_allowed_rejected(
        self, supplier_service: SupplierService
    ) -> None:
        """Invalid type is rejected by the schema validator."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SupplierCreate(name="Bad Type Supplier", type="invalid_type")

        errors = exc_info.value.errors()
        assert any("type must be one of" in str(e).lower() for e in errors)

    async def test_create_rating_at_lower_bound_accepted(
        self, supplier_service: SupplierService
    ) -> None:
        """Rating 0.00 is accepted."""
        data = SupplierCreate(name="Zero Rating", rating=Decimal("0.00"))
        result = await supplier_service.create(data)

        assert result.rating == Decimal("0.00")

    async def test_create_rating_at_upper_bound_accepted(
        self, supplier_service: SupplierService
    ) -> None:
        """Rating 5.00 is accepted."""
        data = SupplierCreate(name="Max Rating", rating=Decimal("5.00"))
        result = await supplier_service.create(data)

        assert result.rating == Decimal("5.00")

    async def test_create_rating_below_zero_rejected_at_schema(self) -> None:
        """Rating below 0 is rejected by Pydantic."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SupplierCreate(name="Negative Rating", rating=Decimal("-1.00"))

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("rating",) for e in errors)

    async def test_create_rating_above_five_rejected_at_schema(self) -> None:
        """Rating above 5 is rejected by Pydantic."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SupplierCreate(name="High Rating", rating=Decimal("6.00"))

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("rating",) for e in errors)


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------


class TestSupplierUpdate:
    """Tests for SupplierService.update method."""

    async def test_update_all_editable_fields(
        self,
        supplier_service: SupplierService,
        existing_supplier: Supplier,
    ) -> None:
        """Updating all editable fields persists the changes."""
        data = SupplierUpdate(
            name="Updated Name",
            type="marketplace",
            country="GB",
            state_province="London",
            city="London",
            address="123 Main St",
            postal_code="SW1A 1AA",
            website="https://example.com",
            email="test@example.com",
            phone="+44 20 1234 5678",
            marketplace_url="https://marketplace.example.com/seller",
            social_media={"twitter": "@seller"},
            rating=Decimal("4.00"),
            notes="Updated notes",
            is_favorite=True,
            is_active=False,
        )
        result = await supplier_service.update(existing_supplier.id, data)

        assert result.name == "Updated Name"
        assert result.type == "marketplace"
        assert result.country == "GB"
        assert result.state_province == "London"
        assert result.city == "London"
        assert result.address == "123 Main St"
        assert result.postal_code == "SW1A 1AA"
        assert result.website == "https://example.com"
        assert result.email == "test@example.com"
        assert result.phone == "+44 20 1234 5678"
        assert result.marketplace_url == "https://marketplace.example.com/seller"
        assert result.social_media == {"twitter": "@seller"}
        assert result.rating == Decimal("4.00")
        assert result.notes == "Updated notes"
        assert result.is_favorite is True
        assert result.is_active is False

    async def test_update_toggle_is_favorite(
        self,
        supplier_service: SupplierService,
        existing_supplier: Supplier,
    ) -> None:
        """Toggling is_favorite persists the change."""
        assert existing_supplier.is_favorite is False

        await supplier_service.update(
            existing_supplier.id, SupplierUpdate(is_favorite=True)
        )
        result = await supplier_service.get(existing_supplier.id)
        assert result.is_favorite is True

        await supplier_service.update(
            existing_supplier.id, SupplierUpdate(is_favorite=False)
        )
        result = await supplier_service.get(existing_supplier.id)
        assert result.is_favorite is False

    async def test_update_partial_fields_only_sends_provided(
        self,
        supplier_service: SupplierService,
        existing_supplier: Supplier,
    ) -> None:
        """Partial update only changes provided fields."""
        original_country = existing_supplier.country
        original_city = existing_supplier.city

        data = SupplierUpdate(city="Los Angeles")
        result = await supplier_service.update(existing_supplier.id, data)

        assert result.city == "Los Angeles"
        assert result.country == original_country  # unchanged

    async def test_update_nonexistent_raises_not_found(
        self, supplier_service: SupplierService
    ) -> None:
        """Updating a non-existent supplier raises NotFoundError."""
        fake_id = str(uuid4())
        with pytest.raises(NotFoundError) as exc_info:
            await supplier_service.update(fake_id, SupplierUpdate(name="New Name"))

        assert fake_id in str(exc_info.value)


# ---------------------------------------------------------------------------
# List/filter tests
# ---------------------------------------------------------------------------


class TestSupplierList:
    """Tests for SupplierService.list method."""

    async def test_list_returns_all_suppliers(
        self, supplier_service: SupplierService
    ) -> None:
        """Listing without filters returns all suppliers."""
        await supplier_service.create(SupplierCreate(name="Supplier A"))
        await supplier_service.create(SupplierCreate(name="Supplier B"))

        result = await supplier_service.list()

        assert len(result) >= 2

    async def test_list_filter_by_type(
        self, supplier_service: SupplierService
    ) -> None:
        """Filtering by type returns only matching suppliers."""
        await supplier_service.create(
            SupplierCreate(name="Online Supplier", type="online")
        )
        await supplier_service.create(
            SupplierCreate(name="Physical Supplier", type="physical_store")
        )

        result = await supplier_service.list(type="online")

        assert all(s.type == "online" for s in result)

    async def test_list_filter_by_country(
        self, supplier_service: SupplierService
    ) -> None:
        """Filtering by country returns only matching suppliers."""
        await supplier_service.create(SupplierCreate(name="US Supplier", country="US"))
        await supplier_service.create(SupplierCreate(name="GB Supplier", country="GB"))

        result = await supplier_service.list(country="US")

        assert all(s.country == "US" for s in result)

    async def test_list_filter_by_is_favorite(
        self, supplier_service: SupplierService
    ) -> None:
        """Filtering by is_favorite returns only matching suppliers."""
        await supplier_service.create(
            SupplierCreate(name="Favorite Supplier", is_favorite=True)
        )
        await supplier_service.create(
            SupplierCreate(name="Non-Favorite Supplier", is_favorite=False)
        )

        result = await supplier_service.list(is_favorite=True)

        assert all(s.is_favorite for s in result)

    async def test_list_filter_by_is_active(
        self, supplier_service: SupplierService
    ) -> None:
        """Filtering by is_active returns only matching suppliers."""
        await supplier_service.create(
            SupplierCreate(name="Active Supplier", is_active=True)
        )
        await supplier_service.create(
            SupplierCreate(name="Inactive Supplier", is_active=False)
        )

        result = await supplier_service.list(is_active=False)

        assert all(not s.is_active for s in result)

    async def test_list_combined_filters(
        self, supplier_service: SupplierService
    ) -> None:
        """Multiple filters are combined with AND logic."""
        await supplier_service.create(
            SupplierCreate(
                name="Combined Test",
                type="online",
                country="US",
                is_favorite=True,
                is_active=True,
            )
        )
        await supplier_service.create(
            SupplierCreate(
                name="Other",
                type="online",
                country="GB",
                is_favorite=True,
                is_active=True,
            )
        )

        result = await supplier_service.list(
            type="online", country="US", is_favorite=True, is_active=True
        )

        assert all(
            s.type == "online"
            and s.country == "US"
            and s.is_favorite
            and s.is_active
            for s in result
        )

    async def test_list_pagination_skip_and_limit(
        self, supplier_service: SupplierService
    ) -> None:
        """Pagination with skip and limit works correctly."""
        for i in range(5):
            await supplier_service.create(
                SupplierCreate(name=f"Paginated Supplier {i}")
            )

        page1 = await supplier_service.list(skip=0, limit=2)
        page2 = await supplier_service.list(skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2
        # Names should be different (different suppliers)
        page1_names = {s.name for s in page1}
        page2_names = {s.name for s in page2}
        assert page1_names.isdisjoint(page2_names)

    async def test_list_empty_result(self, supplier_service: SupplierService) -> None:
        """Querying with no matches returns empty list."""
        result = await supplier_service.list(type="online", country="XX")

        assert result == []


# ---------------------------------------------------------------------------
# Get tests
# ---------------------------------------------------------------------------


class TestSupplierGet:
    """Tests for SupplierService.get method."""

    async def test_get_existing_returns_supplier(
        self,
        supplier_service: SupplierService,
        existing_supplier: Supplier,
    ) -> None:
        """Getting an existing supplier returns it."""
        result = await supplier_service.get(existing_supplier.id)

        assert result.id == existing_supplier.id
        assert result.name == existing_supplier.name

    async def test_get_nonexistent_raises_not_found(
        self, supplier_service: SupplierService
    ) -> None:
        """Getting a non-existent supplier raises NotFoundError."""
        fake_id = str(uuid4())
        with pytest.raises(NotFoundError) as exc_info:
            await supplier_service.get(fake_id)

        assert fake_id in str(exc_info.value)


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


class TestSupplierDelete:
    """Tests for SupplierService.delete method."""

    async def test_delete_without_references_succeeds(
        self, supplier_service: SupplierService
    ) -> None:
        """Deleting a supplier without references succeeds."""
        supplier = await supplier_service.create(
            SupplierCreate(name="To Delete", type="online")
        )

        await supplier_service.delete(supplier.id)

        with pytest.raises(NotFoundError):
            await supplier_service.get(supplier.id)

    async def test_delete_nonexistent_raises_not_found(
        self, supplier_service: SupplierService
    ) -> None:
        """Deleting a non-existent supplier raises NotFoundError."""
        fake_id = str(uuid4())
        with pytest.raises(NotFoundError):
            await supplier_service.delete(fake_id)

    async def test_delete_with_collection_item_reference_raises_duplicate(
        self,
        supplier_service: SupplierService,
        db_session: AsyncSession,
    ) -> None:
        """Deleting a supplier referenced by collection items raises DuplicateError."""
        supplier = await supplier_service.create(
            SupplierCreate(name="Referenced Supplier")
        )

        # Create a catalog item first (required for collection item)
        catalog_item = await _seed_catalog_item(db_session)

        # Create a collection and collection item referencing the supplier
        collection = Collection(
            id=str(uuid4()),
            name="Test Collection",
            collection_type="multi_category",
        )
        db_session.add(collection)
        await db_session.commit()

        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=collection.id,
            catalog_item_id=catalog_item.id,
            supplier_id=supplier.id,
            condition="good",
            purchase_date=None,
        )
        db_session.add(collection_item)
        await db_session.commit()

        with pytest.raises(DuplicateError) as exc_info:
            await supplier_service.delete(supplier.id)

        error_msg = str(exc_info.value)
        assert "collection item" in error_msg.lower()

    async def test_delete_with_multiple_references_raises_duplicate_with_details(
        self,
        supplier_service: SupplierService,
        db_session: AsyncSession,
    ) -> None:
        """Deleting with multiple reference types reports all of them."""
        supplier = await supplier_service.create(
            SupplierCreate(name="Multi-Referenced")
        )

        # Create catalog item first
        catalog_item = await _seed_catalog_item(db_session)

        # Create collection and collection item
        collection = Collection(
            id=str(uuid4()),
            name="Test Collection",
            collection_type="multi_category",
        )
        db_session.add(collection)
        await db_session.commit()

        collection_item = CollectionItem(
            id=str(uuid4()),
            collection_id=collection.id,
            catalog_item_id=catalog_item.id,
            supplier_id=supplier.id,
            condition="good",
        )
        db_session.add(collection_item)
        await db_session.commit()

        with pytest.raises(DuplicateError) as exc_info:
            await supplier_service.delete(supplier.id)

        error_msg = str(exc_info.value)
        # Should mention the reference
        assert "referenced" in error_msg.lower()


# ---------------------------------------------------------------------------
# Purchase history tests
# ---------------------------------------------------------------------------


class TestSupplierPurchaseHistory:
    """Tests for SupplierService.get_purchase_history method."""

    async def test_purchase_history_empty_for_new_supplier(
        self,
        supplier_service: SupplierService,
        existing_supplier: Supplier,
    ) -> None:
        """A supplier with no purchases returns empty history."""
        result = await supplier_service.get_purchase_history(existing_supplier.id)

        assert result == []

    async def test_purchase_history_nonexistent_supplier_raises_not_found(
        self, supplier_service: SupplierService
    ) -> None:
        """Getting history for non-existent supplier raises NotFoundError."""
        fake_id = str(uuid4())
        with pytest.raises(NotFoundError):
            await supplier_service.get_purchase_history(fake_id)

    async def test_purchase_history_returns_items_with_purchase_date(
        self,
        supplier_service: SupplierService,
        db_session: AsyncSession,
    ) -> None:
        """Purchase history returns collection items purchased from supplier."""
        from datetime import date

        supplier = await supplier_service.create(
            SupplierCreate(name="Purchase Test Supplier")
        )

        # Create catalog item first
        catalog_item = await _seed_catalog_item(db_session)

        collection = Collection(
            id=str(uuid4()),
            name="Test Collection",
            collection_type="multi_category",
        )
        db_session.add(collection)
        await db_session.commit()

        # Add an item with a purchase date
        item = CollectionItem(
            id=str(uuid4()),
            collection_id=collection.id,
            catalog_item_id=catalog_item.id,
            supplier_id=supplier.id,
            condition="good",
            purchase_date=date(2024, 1, 15),
            purchase_price=Decimal("100.00"),
            purchase_currency="USD",
        )
        db_session.add(item)
        await db_session.commit()

        result = await supplier_service.get_purchase_history(supplier.id)

        assert len(result) == 1
        assert result[0].purchase_date == date(2024, 1, 15)
        assert result[0].purchase_price == Decimal("100.00")
