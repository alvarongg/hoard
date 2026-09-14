"""H.O.A.R.D. API — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.catalogs import catalog_items_router
from api.routes.accessories import router as accessories_router
from api.routes.catalogs import router as catalogs_router
from api.routes.categories import router as categories_router
from api.routes.categories import subcategories_router
from api.routes.collections import items_router as collection_items_router
from api.routes.collections import router as collections_router
from api.routes.images import images_router, item_images_router
from api.routes.item_components import (
    collection_items_router as item_components_collection_router,
)
from api.routes.item_components import item_components_router
from api.routes.price_history import router as price_history_router
from api.routes.search import router as search_router
from api.routes.stats import router as stats_router
from api.routes.sightings import router as sightings_router
from api.routes.suppliers import router as suppliers_router
from api.routes.transactions import router as transactions_router
from api.routes.wishlist import router as wishlist_router
from core.config import get_settings
from core.exception_handlers import (
    duplicate_handler,
    file_validation_handler,
    not_found_handler,
    validation_handler,
)
from core.exceptions import (
    DuplicateError,
    FileValidationError,
    NotFoundError,
    ValidationError,
)

settings = get_settings()

app = FastAPI(
    title="H.O.A.R.D. API",
    version="0.1.0",
    description="Hobby Organization, Archive & Registry Database",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register domain exception handlers
app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(DuplicateError, duplicate_handler)
app.add_exception_handler(ValidationError, validation_handler)
app.add_exception_handler(FileValidationError, file_validation_handler)


# Register routers
app.include_router(categories_router, prefix="/api")
app.include_router(subcategories_router, prefix="/api")
app.include_router(catalogs_router, prefix="/api")
app.include_router(catalog_items_router, prefix="/api")
app.include_router(collections_router, prefix="/api")
app.include_router(collection_items_router, prefix="/api")
app.include_router(item_images_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(suppliers_router, prefix="/api")
app.include_router(wishlist_router, prefix="/api")
app.include_router(sightings_router, prefix="/api")
app.include_router(item_components_collection_router, prefix="/api")
app.include_router(item_components_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(price_history_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(accessories_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a simple health check response."""
    return {"status": "ok"}


# Serve uploaded images via StaticFiles (Nginx handles this in production)
_upload_path = Path(settings.UPLOAD_DIR)
if _upload_path.is_dir():
    app.mount("/uploads", StaticFiles(directory=str(_upload_path)), name="uploads")
