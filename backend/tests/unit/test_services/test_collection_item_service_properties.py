"""Property-based tests for CollectionItemService using hypothesis.

**Validates: Requirements REQ-008.3, REQ-008.1**

Property 2: Compatibilidad de categoría en items —
    agregar item de categoría incorrecta a single_category ⟹ ValidationError.

Property 7: Paginación acotada —
    ∀ request con skip,limit: len(response) <= limit.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.collection import Collection, CollectionItem
from api.schemas.collection_item import CollectionItemCreate
from api.services.collection_item_service import CollectionItemService
from core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

valid_conditions = st.sampled_from(
    ["mint", "near_mint", "excellent", "good", "fair", "poor"],
)


class TestCategoryCompatibilityProperty:
    """Property 2: Category compatibility in items.

    **Validates: Requirements REQ-008.3**

    For any catalog item belonging to a different sub-category than the
    collection's restricted sub-category, adding it to a single_category
    collection must raise ValidationError.
    """

    @given(condition=valid_conditions)
    @settings(max_examples=10, deadline=None)
    @pytest.mark.asyncio
    async def test_wrong_category_always_raises_validation_error(
        self, condition: str,
    ) -> None:
        """Adding an item from the wrong sub-category always raises."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False,
        )
        async with factory() as session:
            service = CollectionItemService(session)

            # Create two different sub-categories
            main = MainCategory(name="Main", slug="main")
            session.add(main)
            await session.flush()

            sub_a = SubCategory(
                main_category_id=main.id, name="Sub A", slug="sub-a",
            )
            sub_b = SubCategory(
                main_category_id=main.id, name="Sub B", slug="sub-b",
            )
            session.add_all([sub_a, sub_b])
            await session.flush()

            # Collection restricted to sub_a
            collection = Collection(
                name="Test",
                collection_type="single_category",
                restricted_to_sub_category_id=sub_a.id,
            )
            session.add(collection)

            # Catalog item in sub_b (wrong category)
            catalog = Catalog(sub_category_id=sub_b.id, name="Wrong Cat")
            session.add(catalog)
            await session.flush()

            catalog_item = CatalogItem(catalog_id=catalog.id, title="Wrong Item")
            session.add(catalog_item)
            await session.commit()
            await session.refresh(catalog_item)
            await session.refresh(collection)

            data = CollectionItemCreate(
                catalog_item_id=catalog_item.id, condition=condition,
            )
            with pytest.raises(ValidationError):
                await service.add_item(collection.id, data)

        await engine.dispose()


class TestPaginationBoundedProperty:
    """Property 7: Pagination bounded.

    **Validates: Requirements REQ-008.1**

    For any valid skip and limit values, the number of items returned
    must be less than or equal to limit.
    """

    @given(
        limit=st.integers(min_value=1, max_value=50),
        skip=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=15, deadline=None)
    @pytest.mark.asyncio
    async def test_pagination_result_bounded_by_limit(
        self, limit: int, skip: int,
    ) -> None:
        """len(result) is always <= limit regardless of skip/limit values."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False,
        )
        async with factory() as session:
            service = CollectionItemService(session)

            # Seed a main category, sub-category, catalog, and collection
            main = MainCategory(name="Main", slug="main")
            session.add(main)
            await session.flush()

            sub = SubCategory(
                main_category_id=main.id, name="Sub", slug="sub",
            )
            session.add(sub)
            await session.flush()

            catalog = Catalog(sub_category_id=sub.id, name="Catalog")
            session.add(catalog)
            await session.flush()

            collection = Collection(
                name="Test Collection",
                collection_type="multi_category",
            )
            session.add(collection)
            await session.flush()

            # Seed 10 items so pagination has data to work with
            for i in range(10):
                ci = CatalogItem(catalog_id=catalog.id, title=f"Item {i}")
                session.add(ci)
                await session.flush()

                item = CollectionItem(
                    collection_id=collection.id,
                    catalog_item_id=ci.id,
                    condition="good",
                )
                session.add(item)

            await session.commit()
            await session.refresh(collection)

            result = await service.list_by_collection(
                collection.id, skip=skip, limit=limit,
            )

            assert len(result) <= limit

        await engine.dispose()
