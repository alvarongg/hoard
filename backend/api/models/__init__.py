"""SQLAlchemy models."""

from api.models.accessory import AccessoryStock, ItemAccessory, ItemComponent
from api.models.app_setting import AppSetting
from api.models.base import Base, TimestampMixin, UUIDMixin
from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.models.category_field_schema import CategoryFieldSchema
from api.models.collection import (
    Collection,
    CollectionCatalog,
    CollectionItem,
)
from api.models.image import ItemImage
from api.models.maintenance import MaintenanceSchedule
from api.models.pending import PendingCompletion
from api.models.price_history import CatalogPriceHistory
from api.models.standard_component import StandardComponent
from api.models.supplier import Supplier
from api.models.transaction import ItemTransaction
from api.models.wishlist import WishlistItem, WishlistSighting

__all__ = [
    "AccessoryStock",
    "AppSetting",
    "Base",
    "Catalog",
    "CatalogItem",
    "CatalogPriceHistory",
    "CategoryFieldSchema",
    "Collection",
    "CollectionCatalog",
    "CollectionItem",
    "ItemAccessory",
    "ItemComponent",
    "ItemImage",
    "ItemTransaction",
    "MainCategory",
    "MaintenanceSchedule",
    "PendingCompletion",
    "StandardComponent",
    "SubCategory",
    "Supplier",
    "TimestampMixin",
    "UUIDMixin",
    "WishlistItem",
    "WishlistSighting",
]
