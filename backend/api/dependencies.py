"""FastAPI dependency injection factories for services."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.catalog_service import CatalogService
from api.services.catalog_import_service import CatalogImportService
from api.services.catalog_library_service import CatalogLibraryService
from api.services.accessory_service import AccessoryService
from api.services.backup_service import BackupService
from api.services.category_service import CategoryService
from api.services.collection_item_service import CollectionItemService
from api.services.collection_service import CollectionService
from api.services.collection_stats_service import CollectionStatsService
from api.services.csv_import_service import CsvImportService
from api.services.export_service import ExportService
from api.services.image_service import ImageService
from api.services.item_component_service import ItemComponentService
from api.services.json_import_service import JsonImportService
from api.services.price_history_service import PriceHistoryService
from api.services.search_service import SearchService
from api.services.stats_service import StatsService
from api.services.supplier_service import SupplierService
from api.services.transaction_service import TransactionService
from api.services.wishlist_service import WishlistService
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


def get_collection_stats_service(
    db: AsyncSession = Depends(get_db),
) -> CollectionStatsService:
    """Provide a CollectionStatsService instance."""
    return CollectionStatsService(db)


def get_collection_item_service(
    db: AsyncSession = Depends(get_db),
) -> CollectionItemService:
    """Provide a CollectionItemService instance."""
    return CollectionItemService(db)


def get_csv_import_service(
    db: AsyncSession = Depends(get_db),
) -> CsvImportService:
    """Provide a CsvImportService instance."""
    return CsvImportService(db)


def get_image_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImageService:
    """Provide an ImageService instance."""
    return ImageService(db, settings.UPLOAD_DIR)


def get_supplier_service(
    db: AsyncSession = Depends(get_db),
) -> SupplierService:
    """Provide a SupplierService instance."""
    return SupplierService(db)


def get_wishlist_service(
    db: AsyncSession = Depends(get_db),
) -> WishlistService:
    """Provide a WishlistService instance."""
    return WishlistService(db)


def get_item_component_service(
    db: AsyncSession = Depends(get_db),
) -> ItemComponentService:
    """Provide an ItemComponentService instance."""
    return ItemComponentService(db)


def get_search_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SearchService:
    """Provide a SearchService instance."""
    return SearchService(db, settings)


def get_price_history_service(
    db: AsyncSession = Depends(get_db),
) -> PriceHistoryService:
    """Provide a PriceHistoryService instance."""
    return PriceHistoryService(db)


def get_transaction_service(
    db: AsyncSession = Depends(get_db),
) -> TransactionService:
    """Provide a TransactionService instance."""
    return TransactionService(db)


def get_stats_service(
    db: AsyncSession = Depends(get_db),
) -> StatsService:
    """Provide a StatsService instance."""
    return StatsService(db)


def get_accessory_service(
    db: AsyncSession = Depends(get_db),
) -> AccessoryService:
    """Provide an AccessoryService instance."""
    return AccessoryService(db)


def get_export_service(
    db: AsyncSession = Depends(get_db),
) -> ExportService:
    """Provide an ExportService instance."""
    return ExportService(db)


def get_json_import_service(
    db: AsyncSession = Depends(get_db),
) -> JsonImportService:
    """Provide a JsonImportService instance."""
    return JsonImportService(db)


def get_catalog_import_service(
    db: AsyncSession = Depends(get_db),
) -> CatalogImportService:
    """Provide a CatalogImportService instance."""
    return CatalogImportService(db)


def get_catalog_library_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CatalogLibraryService:
    """Provide a CatalogLibraryService backed by the local library dir."""
    return CatalogLibraryService(
        CatalogImportService(db), settings.CATALOG_LIBRARY_DIR
    )


def get_backup_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BackupService:
    """Provide a BackupService instance."""
    return BackupService(db, settings.BACKUP_DIR, settings.DATABASE_URL)
