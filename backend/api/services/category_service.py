"""Business logic for main categories and sub-categories."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog
from api.models.category import MainCategory, SubCategory
from api.schemas.category import (
    MainCategoryCreate,
    MainCategoryUpdate,
    SubCategoryCreate,
    SubCategoryUpdate,
)
from core.exceptions import DuplicateError, NotFoundError, ValidationError


class CategoryService:
    """Handles CRUD operations and business rules for categories."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Main categories
    # ------------------------------------------------------------------

    async def list_main(
        self, skip: int = 0, limit: int = 100
    ) -> list[MainCategory]:
        """Return main categories ordered by sort_order."""
        result = await self._db.execute(
            select(MainCategory)
            .order_by(MainCategory.sort_order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_main(self, category_id: str) -> MainCategory:
        """Return a single main category by id.

        Raises:
            NotFoundError: If the category does not exist.
        """
        category = await self._db.get(MainCategory, category_id)
        if category is None:
            raise NotFoundError(
                f"Main category '{category_id}' not found"
            )
        return category

    async def create_main(
        self, data: MainCategoryCreate
    ) -> MainCategory:
        """Create a new main category.

        Raises:
            DuplicateError: If a category with the same name exists.
        """
        await self._check_main_name_unique(data.name)
        category = MainCategory(**data.model_dump())
        self._db.add(category)
        await self._db.commit()
        await self._db.refresh(category)
        return category

    async def update_main(
        self, category_id: str, data: MainCategoryUpdate
    ) -> MainCategory:
        """Partially update a main category.

        Raises:
            NotFoundError: If the category does not exist.
            DuplicateError: If the new name conflicts with another.
        """
        category = await self.get_main(category_id)
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != category.name:
            await self._check_main_name_unique(update_data["name"])

        for field, value in update_data.items():
            setattr(category, field, value)

        await self._db.commit()
        await self._db.refresh(category)
        return category

    async def delete_main(self, category_id: str) -> None:
        """Delete a main category.

        Raises:
            NotFoundError: If the category does not exist.
            ValidationError: If the category has sub-categories.
        """
        category = await self.get_main(category_id)

        sub_count = await self._db.scalar(
            select(func.count())
            .select_from(SubCategory)
            .where(SubCategory.main_category_id == category_id)
        )
        if sub_count and sub_count > 0:
            raise ValidationError(
                "Cannot delete main category with existing "
                "sub-categories. Remove them first."
            )

        await self._db.delete(category)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Sub-categories
    # ------------------------------------------------------------------

    async def list_sub(
        self,
        main_category_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SubCategory]:
        """Return sub-categories for a main category, ordered by sort_order."""
        result = await self._db.execute(
            select(SubCategory)
            .where(SubCategory.main_category_id == main_category_id)
            .order_by(SubCategory.sort_order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_sub(self, sub_category_id: str) -> SubCategory:
        """Return a single sub-category by id.

        Raises:
            NotFoundError: If the sub-category does not exist.
        """
        sub = await self._db.get(SubCategory, sub_category_id)
        if sub is None:
            raise NotFoundError(
                f"Sub-category '{sub_category_id}' not found"
            )
        return sub

    async def create_sub(self, data: SubCategoryCreate) -> SubCategory:
        """Create a new sub-category.

        Raises:
            NotFoundError: If the parent main category does not exist.
            DuplicateError: If a sub-category with the same name exists
                under the same main category.
        """
        await self.get_main(data.main_category_id)
        await self._check_sub_name_unique(
            data.main_category_id, data.name
        )
        sub = SubCategory(**data.model_dump())
        self._db.add(sub)
        await self._db.commit()
        await self._db.refresh(sub)
        return sub

    async def update_sub(
        self, sub_category_id: str, data: SubCategoryUpdate
    ) -> SubCategory:
        """Partially update a sub-category.

        Raises:
            NotFoundError: If the sub-category does not exist.
            DuplicateError: If the new name conflicts with another
                sub-category under the same parent.
        """
        sub = await self.get_sub(sub_category_id)
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != sub.name:
            await self._check_sub_name_unique(
                sub.main_category_id, update_data["name"]
            )

        for field, value in update_data.items():
            setattr(sub, field, value)

        await self._db.commit()
        await self._db.refresh(sub)
        return sub

    async def delete_sub(self, sub_category_id: str) -> None:
        """Delete a sub-category.

        Raises:
            NotFoundError: If the sub-category does not exist.
            ValidationError: If the sub-category has catalogs associated.
        """
        sub = await self.get_sub(sub_category_id)

        catalog_count = await self._db.scalar(
            select(func.count())
            .select_from(Catalog)
            .where(Catalog.sub_category_id == sub_category_id)
        )
        if catalog_count and catalog_count > 0:
            raise ValidationError(
                "Cannot delete sub-category with existing "
                "catalogs. Remove them first."
            )

        await self._db.delete(sub)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _check_main_name_unique(self, name: str) -> None:
        """Raise DuplicateError if a main category with this name exists."""
        result = await self._db.execute(
            select(MainCategory).where(MainCategory.name == name)
        )
        if result.scalar_one_or_none() is not None:
            raise DuplicateError(
                f"A main category named '{name}' already exists"
            )

    async def _check_sub_name_unique(
        self, main_category_id: str, name: str
    ) -> None:
        """Raise DuplicateError if a sub-category with this name exists
        under the same main category."""
        result = await self._db.execute(
            select(SubCategory).where(
                SubCategory.main_category_id == main_category_id,
                SubCategory.name == name,
            )
        )
        if result.scalar_one_or_none() is not None:
            raise DuplicateError(
                f"A sub-category named '{name}' already exists "
                "in this main category"
            )
