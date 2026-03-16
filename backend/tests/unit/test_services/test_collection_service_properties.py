"""Property-based tests for CollectionService using hypothesis.

**Validates: Requirements REQ-007.2**

Property 3: Unicidad de nombre de colección activa —
    crear dos colecciones con mismo nombre ⟹ DuplicateError en la segunda.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.models.base import Base
from api.schemas.collection import CollectionCreate
from api.services.collection_service import CollectionService
from core.exceptions import DuplicateError

# Strategy for valid collection names: letters, numbers, punctuation, spaces.
# Filtered to exclude whitespace-only strings.
valid_names = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
).filter(lambda s: s.strip())


class TestCollectionNameUniquenessProperty:
    """Property 3: Active collection name uniqueness.

    **Validates: Requirements REQ-007.2**

    For any valid name, creating two collections with the same name
    must raise DuplicateError on the second attempt.
    """

    @given(name=valid_names)
    @settings(max_examples=20, deadline=None)
    @pytest.mark.asyncio
    async def test_duplicate_name_always_raises_error(self, name: str) -> None:
        """Creating two active collections with the same name raises DuplicateError."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False,
        )
        async with factory() as session:
            service = CollectionService(session)

            data = CollectionCreate(
                name=name, collection_type="multi_category",
            )
            await service.create(data)

            with pytest.raises(DuplicateError):
                await service.create(
                    CollectionCreate(
                        name=name, collection_type="multi_category",
                    )
                )

        await engine.dispose()
