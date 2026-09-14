"""Business logic for item components."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.accessory import ItemComponent
from api.models.catalog import CatalogItem
from api.models.category import SubCategory
from api.models.collection import CollectionItem
from api.models.standard_component import StandardComponent
from api.schemas.item_component import (
    CompletenessResult,
    ComponentTemplateEntry,
    ItemComponentCreate,
    ItemComponentUpdate,
)
from core.exceptions import NotFoundError
from utils.computations import is_item_complete


class ItemComponentService:
    """Handles CRUD operations and completeness tracking for item components."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Template operations
    # ------------------------------------------------------------------

    async def get_template(self, collection_item_id: str) -> list[ComponentTemplateEntry]:
        """Get the component template for a collection item's sub-category.

        Returns the standard components defined for the sub-category of the
        collection item's catalog item, along with any recorded presence.

        Args:
            collection_item_id: UUID of the collection item.

        Returns:
            List of ComponentTemplateEntry objects.

        Raises:
            NotFoundError: If the collection item doesn't exist.
        """
        # Get collection item with catalog item and sub-category
        collection_item = await self._db.get(CollectionItem, collection_item_id)
        if collection_item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )

        # Get catalog item to find sub_category_id
        catalog_item = await self._db.get(CatalogItem, collection_item.catalog_item_id)
        if catalog_item is None:
            raise NotFoundError(
                f"Catalog item '{collection_item.catalog_item_id}' not found"
            )

        # Get the catalog to find sub_category_id
        from api.models.catalog import Catalog

        catalog = await self._db.get(Catalog, catalog_item.catalog_id)
        if catalog is None:
            return []  # No catalog means no template

        sub_category_id = catalog.sub_category_id

        # Get standard components for this sub-category
        standard_components_result = await self._db.execute(
            select(StandardComponent)
            .where(StandardComponent.sub_category_id == sub_category_id)
            .order_by(StandardComponent.sort_order)
        )
        standard_components = list(standard_components_result.scalars().all())

        # Get existing item components for this collection item
        existing_components_result = await self._db.execute(
            select(ItemComponent).where(
                ItemComponent.collection_item_id == collection_item_id
            )
        )
        existing_components = list(existing_components_result.scalars().all())

        # Create a lookup by standard_component_id
        existing_by_standard_id: dict[str, ItemComponent] = {}
        for comp in existing_components:
            if comp.standard_component_id:
                existing_by_standard_id[comp.standard_component_id] = comp

        # Build template entries
        entries: list[ComponentTemplateEntry] = []
        for sc in standard_components:
            existing = existing_by_standard_id.get(sc.id)
            entries.append(
                ComponentTemplateEntry(
                    standard_component_id=sc.id,
                    component_name=sc.component_name,
                    component_type=sc.component_type,  # type: ignore
                    description=sc.description,
                    sort_order=sc.sort_order,
                    is_present=existing.is_present if existing else False,
                    recorded_component_id=existing.id if existing else None,
                )
            )

        return entries

    # ------------------------------------------------------------------
    # Component CRUD
    # ------------------------------------------------------------------

    async def list(self, collection_item_id: str) -> list[ItemComponent]:
        """List all components for a collection item.

        Args:
            collection_item_id: UUID of the collection item.

        Returns:
            List of ItemComponent objects.

        Raises:
            NotFoundError: If the collection item doesn't exist.
        """
        # Verify collection item exists
        collection_item = await self._db.get(CollectionItem, collection_item_id)
        if collection_item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )

        result = await self._db.execute(
            select(ItemComponent)
            .where(ItemComponent.collection_item_id == collection_item_id)
            .order_by(ItemComponent.created_at)
        )
        return list(result.scalars().all())

    async def upsert(
        self, collection_item_id: str, data: ItemComponentCreate
    ) -> tuple[ItemComponent, CompletenessResult]:
        """Create or update an item component.

        If a component with the same standard_component_id exists, it will be
        updated. Otherwise, a new component is created.

        Args:
            collection_item_id: UUID of the collection item.
            data: Component creation data.

        Returns:
            Tuple of (created/updated component, completeness result).

        Raises:
            NotFoundError: If the collection item doesn't exist.
        """
        # Verify collection item exists
        collection_item = await self._db.get(CollectionItem, collection_item_id)
        if collection_item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )

        # Check if component exists for this standard_component_id
        existing: ItemComponent | None = None
        if data.standard_component_id:
            result = await self._db.execute(
                select(ItemComponent)
                .where(ItemComponent.collection_item_id == collection_item_id)
                .where(ItemComponent.standard_component_id == data.standard_component_id)
            )
            existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            update_data = data.model_dump()
            for field, value in update_data.items():
                setattr(existing, field, value)
            await self._db.commit()
            await self._db.refresh(existing)
            component = existing
        else:
            # Create new
            component = ItemComponent(
                collection_item_id=collection_item_id,
                **data.model_dump(),
            )
            self._db.add(component)
            await self._db.commit()
            await self._db.refresh(component)

        # Recalculate completeness
        completeness = await self._recalculate_completeness(collection_item_id)

        return component, completeness

    async def update(
        self, component_id: str, data: ItemComponentUpdate
    ) -> tuple[ItemComponent, CompletenessResult]:
        """Partially update an item component.

        Args:
            component_id: UUID of the component to update.
            data: Component update data.

        Returns:
            Tuple of (updated component, completeness result).

        Raises:
            NotFoundError: If the component doesn't exist.
        """
        component = await self._db.get(ItemComponent, component_id)
        if component is None:
            raise NotFoundError(f"Component '{component_id}' not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)

        await self._db.commit()
        await self._db.refresh(component)

        # Recalculate completeness
        completeness = await self._recalculate_completeness(
            component.collection_item_id
        )

        return component, completeness

    async def delete(self, component_id: str) -> CompletenessResult:
        """Delete an item component.

        Args:
            component_id: UUID of the component to delete.

        Returns:
            Completeness result for the parent collection item.

        Raises:
            NotFoundError: If the component doesn't exist.
        """
        component = await self._db.get(ItemComponent, component_id)
        if component is None:
            raise NotFoundError(f"Component '{component_id}' not found")

        collection_item_id = component.collection_item_id

        await self._db.delete(component)
        await self._db.commit()

        # Recalculate completeness
        completeness = await self._recalculate_completeness(collection_item_id)

        return completeness

    # ------------------------------------------------------------------
    # Completeness calculation
    # ------------------------------------------------------------------

    async def _recalculate_completeness(self, collection_item_id: str) -> CompletenessResult:
        """Recalculate and persist completeness for a collection item.

        Uses is_item_complete from utils.computations to determine if all
        required components are present, then updates the collection item's
        is_complete field.

        Args:
            collection_item_id: UUID of the collection item.

        Returns:
            CompletenessResult with the new completeness state.
        """
        # Get collection item
        collection_item = await self._db.get(CollectionItem, collection_item_id)
        if collection_item is None:
            # Item was deleted, return empty result
            return CompletenessResult(
                is_complete=True,
                required_count=0,
                present_count=0,
                missing_names=[],
            )

        # Get the catalog to find sub_category_id
        catalog_item = await self._db.get(CatalogItem, collection_item.catalog_item_id)
        if catalog_item is None:
            return CompletenessResult(
                is_complete=True,
                required_count=0,
                present_count=0,
                missing_names=[],
            )

        from api.models.catalog import Catalog

        catalog = await self._db.get(Catalog, catalog_item.catalog_id)
        if catalog is None:
            return CompletenessResult(
                is_complete=True,
                required_count=0,
                present_count=0,
                missing_names=[],
            )

        sub_category_id = catalog.sub_category_id

        # Get required component names from standard components
        required_result = await self._db.execute(
            select(StandardComponent.component_name)
            .where(StandardComponent.sub_category_id == sub_category_id)
            .where(StandardComponent.component_type == "required")
        )
        required_names = set(row[0] for row in required_result.all())

        # Get present component names
        present_result = await self._db.execute(
            select(ItemComponent.component_name)
            .where(ItemComponent.collection_item_id == collection_item_id)
            .where(ItemComponent.is_present.is_(True))
        )
        present_names = set(row[0] for row in present_result.all())

        # Calculate completeness
        is_complete = is_item_complete(required_names, present_names)

        # Update collection item
        collection_item.is_complete = is_complete
        await self._db.commit()

        # Build result
        missing_names = required_names - present_names
        present_required_count = len(required_names & present_names)

        return CompletenessResult(
            is_complete=is_complete,
            required_count=len(required_names),
            present_count=present_required_count,
            missing_names=sorted(missing_names),
        )
