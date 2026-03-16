"""FastAPI dependency injection factories for services."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.catalog_service import CatalogService
from api.services.category_service import CategoryService
from api.services.collection_item_service import CollectionItemService
from api.services.collection_service import CollectionService
from api.services.image_service import ImageService
from core.config import Settings, get_settings
from core.database import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session."""
    async for session in get_async_session():
        yield session


def get_category_service(
    db: AsyncSession = Depends(get_db),
) -> CategoryService:
    """Provide a CategoryService instance."""
    return CategoryService(db)


def get_catalog_service(
    db: AsyncSession = Depends(get_db),
) -> CatalogService:
    """Provide a CatalogService instance."""
    return CatalogService(db)


def get_collection_service(
    db: AsyncSession = Depends(get_db),
) -> CollectionService:
    """Provide a CollectionService instance."""
    return CollectionService(db)


def get_collection_item_service(
    db: AsyncSession = Depends(get_db),
) -> CollectionItemService:
    """Provide a CollectionItemService instance."""
    return CollectionItemService(db)


def get_image_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImageService:
    """Provide an ImageService instance."""
    return ImageService(db, settings.UPLOAD_DIR)
