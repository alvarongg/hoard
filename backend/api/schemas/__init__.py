"""Pydantic schemas for request/response validation."""

from api.schemas._types import StrUUID
from api.schemas.catalog import (
    CatalogCreate,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogItemUpdate,
    CatalogResponse,
    CatalogUpdate,
)
from api.schemas.category import (
    MainCategoryCreate,
    MainCategoryResponse,
    MainCategoryUpdate,
    SubCategoryCreate,
    SubCategoryResponse,
    SubCategoryUpdate,
)
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
from api.schemas.image import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_SIZE,
    ImageUploadResponse,
    ItemImageResponse,
)

__all__ = [
    # Shared types
    "StrUUID",
    # Category schemas
    "MainCategoryCreate",
    "MainCategoryUpdate",
    "MainCategoryResponse",
    "SubCategoryCreate",
    "SubCategoryUpdate",
    "SubCategoryResponse",
    # Catalog schemas
    "CatalogCreate",
    "CatalogUpdate",
    "CatalogResponse",
    "CatalogItemCreate",
    "CatalogItemUpdate",
    "CatalogItemResponse",
    # Collection schemas
    "CollectionCreate",
    "CollectionUpdate",
    "CollectionResponse",
    # CollectionItem schemas
    "CollectionItemCreate",
    "CollectionItemUpdate",
    "CollectionItemResponse",
    # Image schemas
    "ItemImageResponse",
    "ImageUploadResponse",
    "ALLOWED_IMAGE_TYPES",
    "MAX_IMAGE_SIZE",
]
