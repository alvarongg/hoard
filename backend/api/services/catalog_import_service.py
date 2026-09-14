"""Business logic for catalog import (entity_type='catalog').

Sibling to JsonImportService (which handles collection exports). Parses a
catalog envelope, resolves or creates the target sub-category, and applies the
catalog + its items idempotently (create / update / skip by natural key).
"""

from __future__ import annotations

import json
import re
from datetime import date

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import Catalog, CatalogItem
from api.models.category import MainCategory, SubCategory
from api.schemas.catalog_import import (
    CatalogEnvelope,
    CatalogItemPayload,
    CatalogMeta,
)
from api.schemas.csv_import import BatchImportResult
from api.schemas.import_data import (
    ImportEntityChange,
    ImportError as ImportErrorEntry,
    ImportPreview,
)
from core.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
SUPPORTED_VERSIONS = frozenset({"1.0"})

# Columns that a payload item may set directly on CatalogItem.
_ITEM_DIRECT_FIELDS = (
    "title",
    "subtitle",
    "alternate_titles",
    "region",
    "language",
    "language_codes",
    "developer",
    "publisher",
    "manufacturer",
    "brand",
    "related_items_group",
    "rarity",
    "production_run",
    "is_prototype",
    "is_limited_edition",
    "is_promotional",
    "cover_image_url",
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _parse_release_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        # Never fabricate a date; drop unparseable values.
        return None


class CatalogImportService:
    """Imports a catalog envelope idempotently."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def preview(self, file_content: bytes) -> ImportPreview:
        envelope = self._parse_envelope(file_content)
        plan, _ = await self._plan(envelope, is_official=False)
        return plan

    async def execute(
        self, file_content: bytes, *, is_official: bool = False
    ) -> BatchImportResult:
        envelope = self._parse_envelope(file_content)
        plan, actions = await self._plan(envelope, is_official=is_official)

        created = updated = skipped = 0
        for action in actions:
            op = action["op"]
            if op in ("create_sub_category", "create_main_category",
                      "create_catalog", "create_item"):
                self._db.add(action["obj"])
                if op == "create_item":
                    created += 1
            elif op == "update_catalog":
                for k, v in action["fields"].items():
                    setattr(action["obj"], k, v)
            elif op == "update_item":
                for k, v in action["fields"].items():
                    setattr(action["obj"], k, v)
                updated += 1
            elif op == "skip":
                skipped += 1

        await self._db.commit()
        return BatchImportResult(
            created_count=created,
            updated_count=updated,
            skipped_count=skipped,
            error_count=len(plan.errors),
        )

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_envelope(self, file_content: bytes) -> CatalogEnvelope:
        if len(file_content) > MAX_FILE_SIZE:
            raise ValidationError("Import file exceeds the 10 MB limit")
        try:
            data = json.loads(file_content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValidationError("Import payload must be a JSON object")
        if data.get("schema_version") not in SUPPORTED_VERSIONS:
            raise ValidationError(
                f"Unsupported schema_version: {data.get('schema_version')!r}"
            )
        if data.get("entity_type") != "catalog":
            raise ValidationError(
                "Only catalog envelopes are supported here "
                "(entity_type must be 'catalog')"
            )
        try:
            return CatalogEnvelope.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(f"Invalid catalog envelope: {exc}") from exc

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    async def _plan(
        self, envelope: CatalogEnvelope, *, is_official: bool
    ) -> tuple[ImportPreview, list[dict]]:
        changes: list[ImportEntityChange] = []
        errors: list[ImportErrorEntry] = []
        actions: list[dict] = []
        to_create = to_update = to_skip = 0

        # Resolve or create the target sub-category.
        sub_category, sub_actions = await self._resolve_sub_category(
            envelope.catalog
        )
        actions.extend(sub_actions)

        # Resolve or create the catalog by natural key (sub_category, name).
        catalog, catalog_action, catalog_change = await self._resolve_catalog(
            envelope.catalog, sub_category, is_official=is_official
        )
        actions.append(catalog_action)
        if catalog_change is not None:
            changes.append(catalog_change)

        # Plan items by natural key (catalog, external_id) or (catalog, title, region).
        for payload in envelope.items:
            try:
                existing_item = await self._find_existing_item(
                    catalog, payload
                )
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(
                    ImportErrorEntry(
                        entity_type="catalog_item",
                        identifier=payload.external_id or payload.title,
                        message=str(exc),
                    )
                )
                continue

            fields = self._payload_to_fields(payload)
            if existing_item is None:
                new_item = CatalogItem(catalog=catalog, **fields)
                actions.append({"op": "create_item", "obj": new_item})
                changes.append(
                    ImportEntityChange(
                        entity_type="catalog_item",
                        identifier=payload.external_id or payload.title,
                        action="create",
                    )
                )
                to_create += 1
            elif self._item_needs_update(existing_item, fields):
                actions.append(
                    {"op": "update_item", "obj": existing_item,
                     "fields": fields}
                )
                changes.append(
                    ImportEntityChange(
                        entity_type="catalog_item",
                        identifier=payload.external_id or payload.title,
                        action="update",
                    )
                )
                to_update += 1
            else:
                actions.append({"op": "skip"})
                changes.append(
                    ImportEntityChange(
                        entity_type="catalog_item",
                        identifier=payload.external_id or payload.title,
                        action="skip",
                        reason="already present",
                    )
                )
                to_skip += 1

        preview = ImportPreview(
            schema_version=envelope.schema_version,
            to_create=to_create,
            to_update=to_update,
            to_skip=to_skip,
            changes=changes,
            errors=errors,
        )
        return preview, actions

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    async def _resolve_sub_category(
        self, meta: CatalogMeta
    ) -> tuple[SubCategory, list[dict]]:
        actions: list[dict] = []
        target = meta.target_sub_category

        main = (
            await self._db.execute(
                select(MainCategory).where(
                    MainCategory.name == target.category
                )
            )
        ).scalar_one_or_none()
        main_is_new = main is None
        if main is None:
            main = MainCategory(
                name=target.category, slug=_slugify(target.category)
            )
            actions.append({"op": "create_main_category", "obj": main})

        # Only look for an existing sub-category when the parent already
        # existed; a brand-new main category can have no children yet, and
        # querying against an unflushed parent (no id) fails.
        sub = None
        if not main_is_new:
            sub = (
                await self._db.execute(
                    select(SubCategory).where(
                        SubCategory.name == target.sub_category,
                        SubCategory.main_category_id == main.id,
                    )
                )
            ).scalar_one_or_none()
        if sub is None:
            sub = SubCategory(
                name=target.sub_category,
                slug=_slugify(target.sub_category),
                main_category=main,
            )
            actions.append({"op": "create_sub_category", "obj": sub})

        return sub, actions

    async def _resolve_catalog(
        self, meta: CatalogMeta, sub_category: SubCategory, *,
        is_official: bool,
    ) -> tuple[Catalog, dict, ImportEntityChange | None]:
        existing = None
        if sub_category.id is not None:
            existing = (
                await self._db.execute(
                    select(Catalog).where(
                        Catalog.sub_category_id == sub_category.id,
                        Catalog.name == meta.name,
                    )
                )
            ).scalar_one_or_none()

        meta_fields = {
            "version": meta.version,
            "source_type": meta.source_type,
            "source_name": meta.source_name,
            "source_url": meta.source_url,
            "description": meta.description,
            "is_official": is_official,
        }

        if existing is None:
            catalog = Catalog(
                name=meta.name,
                sub_category=sub_category,
                **meta_fields,
            )
            change = ImportEntityChange(
                entity_type="catalog", identifier=meta.name, action="create"
            )
            return catalog, {"op": "create_catalog", "obj": catalog}, change

        return (
            existing,
            {"op": "update_catalog", "obj": existing, "fields": meta_fields},
            ImportEntityChange(
                entity_type="catalog", identifier=meta.name, action="update"
            ),
        )

    async def _find_existing_item(
        self, catalog: Catalog, payload: CatalogItemPayload
    ) -> CatalogItem | None:
        # A freshly-created catalog has no persisted id yet -> no existing items.
        if catalog.id is None:
            return None

        stmt = select(CatalogItem).where(CatalogItem.catalog_id == catalog.id)
        if payload.external_id:
            # Cross-dialect JSON key comparison (works on SQLite + PostgreSQL).
            stmt = stmt.where(
                CatalogItem.custom_fields["external_id"].as_string()
                == payload.external_id
            )
        else:
            stmt = stmt.where(CatalogItem.title == payload.title)
            if payload.region is not None:
                stmt = stmt.where(CatalogItem.region == payload.region)
        return (await self._db.execute(stmt)).scalars().first()

    # ------------------------------------------------------------------
    # Field mapping
    # ------------------------------------------------------------------

    def _payload_to_fields(self, payload: CatalogItemPayload) -> dict:
        fields: dict = {}
        for name in _ITEM_DIRECT_FIELDS:
            fields[name] = getattr(payload, name)
        fields["release_date"] = _parse_release_date(payload.release_date)

        custom = dict(payload.custom_fields or {})
        if payload.external_id:
            custom.setdefault("external_id", payload.external_id)
        fields["custom_fields"] = custom
        return fields

    def _item_needs_update(
        self, item: CatalogItem, fields: dict
    ) -> bool:
        for key, value in fields.items():
            if getattr(item, key) != value:
                return True
        return False
