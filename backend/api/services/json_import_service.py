"""Business logic for JSON import with preview/execute and dedup."""

from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.collection import Collection, CollectionItem
from api.schemas.csv_import import BatchImportResult
from api.schemas.import_data import (
    ImportEntityChange,
    ImportError as ImportErrorEntry,
    ImportPreview,
)
from core.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
SUPPORTED_VERSIONS = frozenset({"1.0"})


class JsonImportService:
    """Imports a collection-export JSON envelope idempotently."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def preview(self, file_content: bytes) -> ImportPreview:
        envelope = self._parse_envelope(file_content)
        plan, _ = await self._plan(envelope)
        return plan

    async def execute(self, file_content: bytes) -> BatchImportResult:
        envelope = self._parse_envelope(file_content)
        plan, actions = await self._plan(envelope)

        created = updated = skipped = 0
        for action in actions:
            if action["op"] == "create_collection":
                self._db.add(action["obj"])
                created += 1
            elif action["op"] == "update_collection":
                for k, v in action["fields"].items():
                    setattr(action["obj"], k, v)
                updated += 1
            elif action["op"] == "create_item":
                self._db.add(action["obj"])
                created += 1
            elif action["op"] == "skip":
                skipped += 1

        await self._db.commit()
        return BatchImportResult(
            created_count=created,
            updated_count=updated,
            skipped_count=skipped,
            error_count=len(plan.errors),
        )

    # ------------------------------------------------------------------
    # Parsing + planning
    # ------------------------------------------------------------------

    def _parse_envelope(self, file_content: bytes) -> dict:
        if len(file_content) > MAX_FILE_SIZE:
            raise ValidationError("Import file exceeds the 10 MB limit")
        try:
            data = json.loads(file_content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValidationError("Import payload must be a JSON object")
        version = data.get("schema_version")
        if version not in SUPPORTED_VERSIONS:
            raise ValidationError(
                f"Unsupported schema_version: {version!r}"
            )
        if data.get("entity_type") != "collection":
            raise ValidationError(
                "Only collection exports are supported for import"
            )
        if "collection" not in data or not isinstance(
            data["collection"], dict
        ):
            raise ValidationError("Missing or invalid 'collection' object")
        return data

    async def _plan(
        self, envelope: dict
    ) -> tuple[ImportPreview, list[dict]]:
        changes: list[ImportEntityChange] = []
        errors: list[ImportErrorEntry] = []
        actions: list[dict] = []
        to_create = to_update = to_skip = 0

        coll_data = envelope["collection"]
        name = coll_data.get("name")
        if not name:
            errors.append(
                ImportErrorEntry(
                    entity_type="collection",
                    identifier="(unnamed)",
                    message="collection.name is required",
                )
            )
            return (
                ImportPreview(
                    schema_version=envelope["schema_version"],
                    to_create=0,
                    to_update=0,
                    to_skip=0,
                    changes=changes,
                    errors=errors,
                ),
                actions,
            )

        # Resolve collection by natural key (name).
        existing = (
            await self._db.execute(
                select(Collection).where(Collection.name == name)
            )
        ).scalar_one_or_none()

        if existing is None:
            collection = Collection(
                name=name,
                collection_type=coll_data.get("collection_type", "mixed"),
            )
            actions.append({"op": "create_collection", "obj": collection})
            changes.append(
                ImportEntityChange(
                    entity_type="collection", identifier=name, action="create"
                )
            )
            to_create += 1
            target_collection = collection
        else:
            actions.append(
                {
                    "op": "update_collection",
                    "obj": existing,
                    "fields": {
                        "collection_type": coll_data.get(
                            "collection_type", existing.collection_type
                        )
                    },
                }
            )
            changes.append(
                ImportEntityChange(
                    entity_type="collection", identifier=name, action="update"
                )
            )
            to_update += 1
            target_collection = existing

        # Plan collection items by natural key
        # (collection, catalog_item, variant, certification).
        for item in envelope.get("items", []):
            cat_item_id = item.get("catalog_item_id")
            if not cat_item_id:
                errors.append(
                    ImportErrorEntry(
                        entity_type="collection_item",
                        identifier=item.get("id", "(unknown)"),
                        message="catalog_item_id is required",
                    )
                )
                continue

            existing_item = None
            if existing is not None:
                existing_item = (
                    await self._db.execute(
                        select(CollectionItem)
                        .where(CollectionItem.collection_id == existing.id)
                        .where(CollectionItem.catalog_item_id == cat_item_id)
                    )
                ).scalar_one_or_none()

            if existing_item is not None:
                actions.append({"op": "skip"})
                changes.append(
                    ImportEntityChange(
                        entity_type="collection_item",
                        identifier=cat_item_id,
                        action="skip",
                        reason="already present",
                    )
                )
                to_skip += 1
            else:
                pp = item.get("purchase_price")
                new_item = CollectionItem(
                    collection=target_collection,
                    catalog_item_id=cat_item_id,
                    condition=item.get("condition", "good"),
                    is_complete=item.get("is_complete", False),
                    purchase_price=Decimal(str(pp)) if pp is not None else None,
                )
                actions.append({"op": "create_item", "obj": new_item})
                changes.append(
                    ImportEntityChange(
                        entity_type="collection_item",
                        identifier=cat_item_id,
                        action="create",
                    )
                )
                to_create += 1

        preview = ImportPreview(
            schema_version=envelope["schema_version"],
            to_create=to_create,
            to_update=to_update,
            to_skip=to_skip,
            changes=changes,
            errors=errors,
        )
        return preview, actions
