# Diseño — Flujo del coleccionista (collector-workflow)

## Alcance y anclaje al código actual

Todo se ancla a los archivos existentes. Puntos de partida verificados:

- `CollectionItem` (`backend/api/models/collection.py`): modelo RICO — ya tiene `condition`, `condition_notes`, `is_authentic`/`authenticity_notes` (original/bootleg), `purchase_price`/`purchase_currency`, `supplier_id`, `storage_location`, `custom_fields` (JSON). **Falta**: `country_of_origin` (no existe en ninguna capa).
- Alta de ítem: `CollectionItemService.add_item(collection_id, CollectionItemCreate)` → `POST /collections/{id}/items`. Los schemas `CollectionItemCreate/Update/Response` (`backend/api/schemas/collection_item.py`) exponen un SUBCONJUNTO pobre del modelo (no incluyen `supplier_id`, `is_authentic`, `condition_notes`, país).
- `Supplier` (`backend/api/models/supplier.py`, `services/supplier_service.py`): creable con solo `name`; tiene `country` (ISO-2). `create(SupplierCreate)`.
- `Catalog` (`backend/api/models/catalog.py`, `services/catalog_service.py`): exige `sub_category_id` válido; unicidad por sub-categoría; NO tiene campo `system`/`tematica`. `create_catalog(CatalogCreate)`, `create_item(catalog_id, CatalogItemCreate)`.
- `WishlistItem` (`backend/api/models/wishlist.py`): YA tiene `collection_id`, `catalog_item_id`, `is_acquired`, `acquired_date`, `acquired_collection_item_id`, `is_active`. El flujo "ya lo conseguí" reusa estos campos.
- Price history (`backend/api/models/price_history.py`, `services/price_history_service.py`): `CatalogPriceHistory` sobre `catalog_item`, con `source`, `source_url`, `price_date`. NO hay cliente externo. `create()`, `list()`, `latest_by_condition()`, `refresh_item_market_value()`.
- Frontend búsqueda: `SearchPage` navega a `/catalogs/:id/items/:itemId` — **ruta inexistente** (link roto). `CatalogDetailPage` (`catalogs/:id`) no linkea a ítems. `CollectionDetailPage` lista ítems con `ItemForm`.

## Modelo de datos — cambios

### 1. `CollectionItem`: nuevo campo país
- Agregar columna `country_of_origin: str | None` `String(2)` (ISO-2), nullable, en el modelo.
- Migración Alembic aditiva.

### 2. Relación N:M colección ↔ catálogos: `collection_catalogs`
- Nueva tabla asociativa `collection_catalogs(collection_id FK CASCADE, catalog_id FK CASCADE, is_primary bool default False, created_at)`, PK compuesta `(collection_id, catalog_id)`.
- Modelo `CollectionCatalog` + relaciones: `Collection.catalogs` (secondary) y helper para listar/asociar/desasociar.
- Regla de negocio (servicio, no constraint DB): al **agregar un ítem** a una colección, debe existir ≥1 catálogo asociado; si no, el servicio devuelve un error accionable ("asociá o creá un catálogo primero").

### 3. `MaintenanceSchedule` (nuevo)
- Tabla `maintenance_schedules(id, collection_item_id FK CASCADE, maintenance_type str(50), due_date date, notes text?, is_done bool=False, done_date date?, done_notes text?, created_at, updated_at)`.
- Relación `CollectionItem.maintenance_schedules` (cascade delete-orphan).
- Solo se crea si el coleccionista marcó "requiere mantenimiento".

### 4. `PendingCompletion` (nuevo) — solapa de Pendientes
- Tabla `pending_completions(id, entity_type str(30) [collection_item|catalog|catalog_item|supplier], entity_id str(uuid), missing_fields JSON [lista de nombres], status str(20)=open|resolved, created_at, resolved_at date?)`.
- No usa FK polimórfica dura (entity_type + entity_id); índice sobre `(status, entity_type)`.
- Servicio central `PendingService` crea/resuelve/cierra pendientes; las altas rápidas lo invocan.

### 5. Price history: consulta on-demand PriceCharting
- El historial sigue en `CatalogPriceHistory` (sin cambios de esquema).
- Nuevo `PriceLookupService` con un `PriceChartingClient` (stdlib `urllib`, allowlist de host `pricecharting.com`, solo https, timeout, límite de tamaño — mismo patrón que `RemoteCatalogSource`). Parsea el precio del HTML de la URL del ítem (selector estable; si cambia, error controlado). Config: `PRICE_LOOKUP_ENABLED`, `PRICE_LOOKUP_ALLOWED_HOSTS="pricecharting.com,www.pricecharting.com"`.
- Devuelve un `PriceHistoryCreate` que se inserta vía `PriceHistoryService.create` con `source="PriceCharting"`, `source_url`, `price_date=hoy`.

## Backend — servicios y schemas

### Schemas ampliados (`collection_item.py`)
- `CollectionItemBase` gana (todos opcionales salvo los ya requeridos): `supplier_id`, `is_authentic`, `authenticity_notes`, `country_of_origin`, `condition_notes`, `storage_location` (ya está), `custom_fields`. `CollectionItemResponse` refleja los nuevos campos. `CollectionItemUpdate` los acepta también.

### Servicios nuevos / modificados
- `CollectionItemService.add_item`: persistir los campos nuevos; validar `country_of_origin` ISO-2 si viene.
- `QuickAddService` (nuevo, orquestador): 
  - `quick_add_supplier(name, country)` → crea Supplier + Pending.
  - `quick_add_catalog(collection_id, name, tematica)` → resuelve/crea sub-categoría desde `tematica` (bajo main category adecuada), crea Catalog, lo asocia a la colección (N:M), crea Pending.
  - `quick_add_catalog_item_and_collection_item(collection_id, catalog_id, minimal_item, collection_item_data)` → crea CatalogItem (title mínimo) + CollectionItem en una transacción + Pending del CatalogItem.
- `CollectionCatalogService` (nuevo): `associate(collection_id, catalog_id, is_primary)`, `dissociate(...)`, `list_for_collection(...)`.
- `WishlistService`: método `acquire(wishlist_id, CollectionItemCreate, remove_from_wishlist: bool)` → crea CollectionItem, setea `is_acquired/acquired_date/acquired_collection_item_id`; si `remove_from_wishlist` → `is_active=False` (o delete). Reusa `CollectionItemService`.
- `MaintenanceService` (nuevo): CRUD de `MaintenanceSchedule` + `list_due(before)`.
- `PendingService` (nuevo): `open(entity_type, entity_id, missing_fields)`, `list(status)`, `resolve(pending_id, patch)`, auto-close.
- `PriceLookupService` (nuevo): `lookup(catalog_item_id, url)` → inserta price history.

### Rutas nuevas
- `POST /collections/{id}/catalogs` / `DELETE /collections/{id}/catalogs/{catalog_id}` / `GET /collections/{id}/catalogs`.
- `POST /suppliers/quick`, `POST /collections/{id}/catalogs/quick`, `POST /collections/{id}/items/quick` (crea catalog_item + collection_item).
- `POST /wishlist/{id}/acquire`.
- `GET /catalog-items/{id}/ownership` (¿en qué colecciones lo tengo?).
- `GET/POST/PUT /collection-items/{id}/maintenance`, `GET /maintenance/due`.
- `GET /pending`, `PUT /pending/{id}/resolve`.
- `POST /catalog-items/{id}/price-lookup` (on-demand PriceCharting).

## Frontend

- **Ruta nueva** `catalogs/:catalogId/items/:itemId` → `CatalogItemDetailPage` (arregla el link roto de `SearchPage`). Muestra toda la info del CatalogItem + badge "Ya lo tenés en: <colección>" (via `/ownership`) + botones "Agregar a colección" / "Agregar a wishlist" / "Buscar precio".
- **`AddToCollectionForm`** (modal/página): elige colección, condición, original/bootleg, país, precio+moneda, proveedor (con `SupplierQuickAdd` inline), ubicación física, y toggle "requiere mantenimiento" → sub-form de revisión. Reusable desde detalle de ítem y desde wishlist "Ya lo conseguí".
- **Búsqueda**: `SearchFilters` gana filtro por catálogo/sistema; la navegación integra Catálogos dentro del buscador (entrada de menú/tab).
- **CollectionDetailPage**: sección de catálogos asociados (asociar/desasociar + `CatalogQuickAdd`); `ItemForm` usa `quick` cuando el ítem no existe.
- **Wishlist**: en el detalle del ítem de wishlist, botón "Ya lo conseguí" → `AddToCollectionForm` pre-cargado; al final, checkbox "Quitar de la wishlist".
- **Pendientes**: nueva página/tab `PendingPage` que lista pendientes por tipo y abre un editor para completarlos.
- **Precio**: botón "Buscar precio (PriceCharting)" en el detalle del ítem; agrega una fila al `PriceHistoryTable`.

## Desviaciones documentadas
- `tematica` → se mapea a la jerarquía existente main_category → sub_category (no se agrega un campo `system` libre al Catalog; se resuelve/crea la sub-categoría). El nombre temático libre se guarda además en `custom_fields`/descripción para no perder la intención del usuario.
- PriceCharting parsea HTML público de la URL del propio ítem que el usuario provee/confirma; es on-demand y single-item por diseño. Si el layout cambia, el lookup falla de forma controlada (no rompe el alta).

## Testing
- Backend: unit por servicio nuevo (QuickAdd, CollectionCatalog, Wishlist.acquire, Maintenance, Pending, PriceLookup con red mockeada + allowlist), integración de rutas. Mantener suite verde y cobertura ≥ umbral.
- Frontend: componentes nuevos con Testing Library + axe (AddToCollectionForm, CatalogItemDetailPage, PendingPage, quick-adds); hooks. i18n 5 locales. E2E: agregar-desde-búsqueda, wishlist→conseguí, quick-add catálogo/proveedor, pendientes.
- Verificación real en Unraid (Postgres) como en specs previos.
