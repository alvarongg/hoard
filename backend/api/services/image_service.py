"""Business logic for image uploads and management."""

from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.collection import CollectionItem
from api.models.image import ItemImage
from api.schemas.image import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE
from core.exceptions import FileValidationError, NotFoundError

# UploadFile is used as a data container type only (no FastAPI coupling)
from fastapi import UploadFile


class ImageService:
    """Handles image upload, listing, and deletion for collection items."""

    def __init__(self, db: AsyncSession, upload_dir: str) -> None:
        self._db = db
        self._upload_dir = upload_dir

    async def upload(
        self, collection_item_id: str, file: UploadFile
    ) -> ItemImage:
        """Upload an image for a collection item.

        Validates that the item exists, the file type is allowed, and
        the file size does not exceed the maximum. The first image
        uploaded for an item is automatically marked as primary.

        Raises:
            NotFoundError: If the collection item does not exist.
            FileValidationError: If the file type or size is invalid.
        """
        await self._get_collection_item(collection_item_id)
        self._validate_file(file)

        content = await file.read()
        self._validate_content_size(content)

        file_path, relative_path = self._generate_path(
            collection_item_id, file.filename or "image",
        )
        await self._save_file(file_path, content)

        is_primary = await self._is_first_image(collection_item_id)

        image = ItemImage(
            collection_item_id=collection_item_id,
            file_path=relative_path,
            file_name=file.filename or "image",
            file_size=len(content),
            mime_type=file.content_type,
            is_primary=is_primary,
        )
        self._db.add(image)
        await self._db.commit()
        await self._db.refresh(image)
        return image

    async def list_by_item(
        self, collection_item_id: str
    ) -> list[ItemImage]:
        """Return all images for a collection item, ordered by upload date."""
        result = await self._db.execute(
            select(ItemImage)
            .where(ItemImage.collection_item_id == collection_item_id)
            .order_by(ItemImage.uploaded_at)
        )
        return list(result.scalars().all())

    async def delete(self, image_id: str) -> None:
        """Delete an image record and its file from disk.

        Raises:
            NotFoundError: If the image does not exist.
        """
        image = await self._db.get(ItemImage, image_id)
        if image is None:
            raise NotFoundError(f"Image '{image_id}' not found")

        self._delete_file_from_disk(image.file_path)

        await self._db.delete(image)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_file(self, file: UploadFile) -> None:
        """Validate file MIME type.

        Raises:
            FileValidationError: If the MIME type is not allowed.
        """
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise FileValidationError(
                f"File type '{file.content_type}' is not allowed. "
                f"Allowed types: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
            )

    def _validate_content_size(self, content: bytes) -> None:
        """Validate that file content does not exceed the maximum size.

        Raises:
            FileValidationError: If the content exceeds MAX_IMAGE_SIZE.
        """
        if len(content) > MAX_IMAGE_SIZE:
            max_mb = MAX_IMAGE_SIZE // (1024 * 1024)
            raise FileValidationError(
                f"File size exceeds the maximum allowed ({max_mb}MB)"
            )

    def _generate_path(
        self, item_id: str, filename: str
    ) -> tuple[Path, str]:
        """Generate a unique file path for the upload.

        Returns:
            A tuple of (absolute_path, relative_path_string).
        """
        ext = Path(filename).suffix.lower() or ".bin"
        unique_name = f"{uuid.uuid4()}{ext}"
        relative = str(Path(item_id) / unique_name)
        absolute = Path(self._upload_dir) / relative
        return absolute, relative

    async def _save_file(self, path: Path, content: bytes) -> None:
        """Write content to disk, creating directories as needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

    async def _is_first_image(self, collection_item_id: str) -> bool:
        """Return True if no images exist yet for the given item."""
        count = await self._db.scalar(
            select(func.count())
            .select_from(ItemImage)
            .where(ItemImage.collection_item_id == collection_item_id)
        )
        return count == 0

    async def _get_collection_item(
        self, collection_item_id: str
    ) -> CollectionItem:
        """Fetch a collection item or raise NotFoundError."""
        item = await self._db.get(CollectionItem, collection_item_id)
        if item is None:
            raise NotFoundError(
                f"Collection item '{collection_item_id}' not found"
            )
        return item

    def _delete_file_from_disk(self, file_path: str) -> None:
        """Remove a file from disk if it exists. Silently ignores missing files."""
        full_path = Path(self._upload_dir) / file_path
        full_path.unlink(missing_ok=True)
