"""REST endpoints for image uploads and management.

Images are nested under collection items for upload/listing, and have
standalone endpoints for deletion.

Requirements: REQ-009
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, UploadFile

from api.dependencies import get_image_service
from api.schemas.image import ImageUploadResponse, ItemImageResponse
from api.services.image_service import ImageService

# ------------------------------------------------------------------
# Images nested under items: POST/GET /items/{item_id}/images
# ------------------------------------------------------------------

item_images_router = APIRouter(prefix="/items", tags=["images"])


@item_images_router.post(
    "/{item_id}/images",
    response_model=ImageUploadResponse,
    status_code=201,
)
async def upload_image(
    item_id: str,
    file: UploadFile,
    service: ImageService = Depends(get_image_service),
) -> ImageUploadResponse:
    """Upload an image for a collection item."""
    return await service.upload(item_id, file)


@item_images_router.get(
    "/{item_id}/images",
    response_model=list[ItemImageResponse],
)
async def list_item_images(
    item_id: str,
    service: ImageService = Depends(get_image_service),
) -> list[ItemImageResponse]:
    """List all images for a collection item."""
    return await service.list_by_item(item_id)


# ------------------------------------------------------------------
# Standalone image endpoints: DELETE /images/{image_id}
# ------------------------------------------------------------------

images_router = APIRouter(prefix="/images", tags=["images"])


@images_router.delete(
    "/{image_id}", status_code=204, response_class=Response,
)
async def delete_image(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> None:
    """Delete an image by id."""
    await service.delete(image_id)
