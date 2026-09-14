# Implementation Plan: Fase 2 (Core) y Fase 3 (Advanced)

## Overview

Este plan implementa los 19 requirements del spec siguiendo el `## Orden de Implementación Sugerido` del design, que responde a dependencias reales entre dominios y no a la numeración de los requirements.

El trabajo se organiza en tres bloques:

- **Bloque 0 — Cimientos (Tasks 1-7)**: los 5 modelos SQLAlchemy nuevos (4 de tablas existentes + `AppSetting` con su migración `002_app_settings.py`), las relaciones faltantes en modelos existentes, la capa de cálculo compartida `utils/computations.py`, la capa de dialecto `core/dialect.py`, los componentes UI transversales (`LiveRegion`, `Table`, `Tooltip`, `SkipLink`, `Badge`) y las dependencias nuevas de backend y frontend. Nada de lo que sigue se puede construir sin esto.
- **Bloque 1 — Fase 2 Core (Tasks 8-23)**: Suppliers (R2) → Wishlist + sightings (R3, R4) → Componentes de items (R5) → Colecciones multi-category (R1) → Búsqueda avanzada (R6) → Dark mode (R8) → Idiomas pt/fr/de (R9). Coverage exigido >80% al cerrar el bloque.
- **Bloque 2 — Fase 3 Advanced (Tasks 24-48)**: Price history (R10) → Transacciones (R11) → Estadísticas (R7) → Gráficos (R16) → Accesorios y stock (R12) → Export (R13) → Import (R14) → Backups + scheduler (R15) → PWA/offline (R17) → Accesibilidad avanzada y auditoría (R18) → cierre de estándares transversales (R19). Coverage exigido >85% al cerrar el bloque.

Cada dominio backend sigue el patrón del proyecto: schemas Pydantic → service → dependency factory → routes → registro del router en `backend/main.py` → tests unitarios del service → tests de integración del endpoint. Cada dominio frontend: tipos TypeScript → cliente API → hooks → componentes → página → ruta en `App.tsx` → enlace de navegación → claves i18n → tests con axe-core.

**Nota de orden sobre i18n**: los idiomas pt, fr y de se crean en la Task 22 (final del Bloque 1). Las tareas anteriores a la 22 agregan claves solo a `es` y `en`; la Task 22.2 porta todas las claves existentes hasta ese momento a los tres idiomas nuevos; las tareas posteriores a la 22 agregan sus claves a los 5 archivos.

## Tasks

- [x] 1. Bloque 0 - Instalar dependencias nuevas y configuración base
  - [x] 1.1 Agregar dependencias backend en `backend/requirements.txt` y `backend/requirements-dev.txt`
    - `backend/requirements.txt`: `apscheduler==3.10.4`, `email-validator==2.2.0`
    - `backend/requirements-dev.txt`: `pytest-postgresql==6.1.1`; pinear `hypothesis==6.122.3` y `aiosqlite==0.20.0` (hoy con rangos abiertos)
    - Verificar que `pip install -r requirements.txt -r requirements-dev.txt` resuelve sin conflictos
    - _Requirements: 15.8, 2.5, 19.8_
  - [x] 1.2 Configurar la marca `postgres` opt-in en `backend/pyproject.toml`
    - Registrar `markers = ["postgres: requiere un PostgreSQL real (opt-in)"]`
    - Agregar `addopts = "-m 'not postgres'"` para que la suite quede desactivada por defecto
    - Agregar el fixture `dialect_name` y el fixture de sesión PostgreSQL (leído de `HOARD_TEST_DATABASE_URL`) en `backend/tests/conftest.py`, con `pytest.skip` cuando la variable no está definida
    - _Requirements: 19.8_
  - [x] 1.3 Agregar `SEARCH_SIMILARITY_THRESHOLD` en `backend/core/config.py`
    - `SEARCH_SIMILARITY_THRESHOLD: float = 0.3` como variable de entorno de `Settings`
    - Actualizar `.env.example` con la variable y un comentario sobre su rango útil
    - Actualizar `backend/tests/unit/test_config.py` verificando el default y la sobrescritura por entorno
    - _Requirements: 6.3_
  - [x] 1.4 Agregar `postgresql-client` en `backend/Dockerfile`
    - Instalar el paquete en la etapa de runtime para que `pg_dump` y `pg_restore` estén disponibles
    - Documentar el motivo en `docs/DOCKER_ARCHITECTURE.md` (backups requieren los binarios del cliente)
    - _Requirements: 15.1, 15.6_
  - [x] 1.5 Agregar dependencias frontend en `frontend/package.json`
    - prod: `recharts@2.13.3`, `idb@8.0.0`, `@tanstack/react-query-persist-client@5.62.0`, `workbox-window@7.3.0`
    - dev: `vite-plugin-pwa@0.21.1`, `fake-indexeddb@6.0.0`, `@vitest/coverage-v8@2.1.8`
    - Verificar que `npm run build` y `npx tsc --noEmit` siguen pasando
    - _Requirements: 16.1, 17.1, 17.6, 19.4, 19.5_
  - [x] 1.6 Configurar umbrales iniciales de coverage
    - `backend/pyproject.toml`: sección `[tool.coverage.report]` con `fail_under = 70`, excluyendo `alembic/*`, `main.py` y archivos de configuración
    - `frontend/vitest.config.ts`: `coverage.provider = "v8"`, `coverage.thresholds.lines = 70`, mismas exclusiones
    - Los umbrales se elevan a 80 en la Task 23 y a 85 en la Task 47
    - _Requirements: 19.4, 19.5_

- [x] 2. Bloque 0 - Crear los 4 modelos SQLAlchemy faltantes
  - [x] 2.1 Crear `backend/api/models/category_field_schema.py` con el modelo `CategoryFieldSchema`
    - Mapear `category_field_schemas`: `sub_category_id` (FK CASCADE), `field_name`, `field_label`, `field_type`, `field_options` (JSON), `is_required`, `is_searchable`, `default_value`, `help_text`, `sort_order`, `created_at`
    - `__table_args__` con `UniqueConstraint("sub_category_id", "field_name", name="uq_category_field_sub_name")`
    - Usar `UUIDMixin` y `DBUUID` como los modelos existentes; sin `updated_at` (la tabla no lo tiene)
    - Exportar en `backend/api/models/__init__.py`
    - _Requirements: 19.6_
  - [x] 2.2 Crear `backend/api/models/price_history.py` con el modelo `CatalogPriceHistory`
    - Mapear `catalog_price_history`: `catalog_item_id` (FK CASCADE), `condition`, `is_complete`, `completeness_description`, `price` (Numeric 10,2), `currency`, `source`, `source_url`, `price_date`, `region`, `notes`, `recorded_at`
    - `UniqueConstraint("catalog_item_id", "condition", "is_complete", "price_date", "source", name="unique_price_record")`
    - Relación `catalog_item` con `back_populates="price_history"`
    - Exportar en `backend/api/models/__init__.py`
    - _Requirements: 10.1, 10.3_
  - [x] 2.3 Crear `backend/api/models/transaction.py` con el modelo `ItemTransaction`
    - Mapear `item_transactions`: `collection_item_id` (FK CASCADE), `transaction_type`, `transaction_date`, `amount`, `currency`, `shipping_cost`, `tax_amount`, `other_fees`, `supplier_id` (FK SET NULL), `counterpart_name`, `invoice_number`, `receipt_path`, `payment_method`, `notes`, `created_at`
    - `total_amount` declarado con `Computed("COALESCE(amount,0)+COALESCE(shipping_cost,0)+COALESCE(tax_amount,0)+COALESCE(other_fees,0)", persisted=True)` para que no entre en los INSERT
    - Relación `collection_item` con `back_populates="transactions"`
    - Exportar en `backend/api/models/__init__.py`
    - _Requirements: 11.1, 11.4_
  - [x] 2.4 Agregar el modelo `ItemAccessory` y la columna `quantity_available` en `backend/api/models/accessory.py`
    - `ItemAccessory` mapea `item_accessories`: `collection_item_id` (FK CASCADE), `accessory_id` (FK RESTRICT), `quantity_used`, `assigned_at`, `notes`, con `UniqueConstraint("collection_item_id", "accessory_id", name="uq_item_accessory")`
    - En `AccessoryStock` agregar `quantity_available` como `Computed("quantity_total - quantity_in_use", persisted=True)`, nunca escrita desde Python
    - Relación `assignments` en `AccessoryStock` con `back_populates="accessory"` y `passive_deletes=True`
    - Exportar `ItemAccessory` en `backend/api/models/__init__.py`
    - _Requirements: 12.4, 12.9_
  - [x] 2.5 Escribir unit tests de los modelos nuevos en `backend/tests/unit/test_models/test_new_models.py`
    - Crear y consultar una instancia de cada modelo sobre SQLite in-memory
    - Verificar que las `UniqueConstraint` rechazan duplicados
    - Verificar que `ItemTransaction.total_amount` y `AccessoryStock.quantity_available` se leen y no se escriben
    - Verificar el borrado en cascada desde `catalog_items` y `collection_items`
    - _Requirements: 10.1, 11.1, 12.4, 19.10_

- [x] 3. Bloque 0 - Agregar relaciones faltantes en modelos existentes
  - [x] 3.1 Agregar relaciones en `backend/api/models/catalog.py` y `backend/api/models/collection.py`
    - `CatalogItem.price_history` → `CatalogPriceHistory`, cascade `all, delete-orphan`, `passive_deletes=True`
    - `CollectionItem.components`, `.transactions`, `.accessories` con el mismo cascade
    - `CollectionItem.supplier` con `back_populates="collection_items"`
    - _Requirements: 10.1, 11.1, 12.4, 5.2_
  - [x] 3.2 Agregar relaciones en `backend/api/models/category.py`, `supplier.py`, `wishlist.py` y `standard_component.py`
    - `SubCategory.field_schemas` y `SubCategory.standard_components` con cascade y `passive_deletes=True`
    - `Supplier.collection_items`, `Supplier.sightings`, `Supplier.accessories` (necesarias para contar referencias antes de borrar)
    - `WishlistItem.acquired_collection_item` con `foreign_keys=[acquired_collection_item_id]`
    - `ItemComponent.collection_item` pasa a declarar `back_populates="components"`
    - _Requirements: 2.10, 3.7, 5.1_
  - [x] 3.3 Escribir unit tests de relaciones en `backend/tests/unit/test_models/test_relationships.py`
    - Verificar navegación bidireccional en cada relación nueva
    - Verificar que el borrado del padre elimina los hijos con cascade
    - Verificar que `Supplier` expone los tres conjuntos de referencias
    - _Requirements: 2.10, 19.10_

- [x] 4. Bloque 0 - Crear la migración `002_app_settings.py` y el modelo `AppSetting`
  - [x] 4.1 Crear `backend/alembic/versions/002_app_settings.py`
    - `down_revision = "001"`; crear la tabla `app_settings` con `key VARCHAR(100) PRIMARY KEY`, `value JSONB` (variant `JSON` en SQLite) y `updated_at TIMESTAMP` con `server_default=now()`
    - `downgrade()` elimina la tabla
    - _Requirements: 15.8, 15.9_
  - [x] 4.2 Crear `backend/api/models/app_setting.py` con el modelo `AppSetting`
    - PK textual `key` (sin `UUIDMixin`), `value` con `JSONB().with_variant(JSON(), "sqlite")`, `updated_at` con `server_default` y `onupdate`
    - Exportar en `backend/api/models/__init__.py`
    - _Requirements: 15.8, 15.9_
  - [x] 4.3 Escribir tests de la migración y del modelo en `backend/tests/unit/test_models/test_app_setting.py`
    - Upsert de una clave y lectura del payload JSON
    - `updated_at` se refresca al modificar el valor
    - `alembic upgrade head` y `alembic downgrade -1` corren limpio (test marcado `@pytest.mark.postgres`)
    - _Requirements: 15.8, 19.10_

- [x] 5. Bloque 0 - Crear la capa de cálculo compartida y la capa de dialecto
  - [x] 5.1 Crear `backend/utils/computations.py`
    - `transaction_total(amount, shipping_cost, tax_amount, other_fees) -> Decimal` tratando nulos como cero
    - `available_stock(quantity_total, quantity_in_use) -> int`
    - `roi_percentage(invested, current_value) -> Decimal | None` devolviendo `None` cuando `invested == 0`
    - `is_item_complete(required_names, present_names) -> bool`
    - Funciones puras, sin dependencia de base de datos, con type hints y docstrings Google style
    - _Requirements: 11.4, 11.5, 12.9, 7.7, 5.5_
  - [x] 5.2 Crear `backend/core/dialect.py`
    - `Dialect` enum (`POSTGRESQL`, `SQLITE`), `current_dialect(db)`, `supports_full_text(db)`, `supports_generated_columns(db)`, `supports_views(db)`
    - Default seguro a SQLite cuando `db.bind` es `None`
    - _Requirements: 19.8_
  - [x] 5.3 Escribir unit tests en `backend/tests/unit/test_utils/test_computations.py` y `backend/tests/unit/test_core/test_dialect.py`
    - `computations`: casos con todos los campos, con nulos parciales, con todos nulos, stock en cero, ROI con inversión cero, completitud con conjunto de requeridos vacío
    - `dialect`: sesión SQLite devuelve `SQLITE` y `supports_*` en `False`; sesión sin bind cae a `SQLITE`
    - _Requirements: 11.5, 12.9, 7.7, 5.5, 19.10_
  - [x] 5.4 Escribir property test de `transaction_total`
    - **Property 1: `total_amount` es la suma con nulos como cero**
    - **Validates: Requirements 11.4, 11.5**
    - Usar `hypothesis` (mínimo 100 iteraciones) generando decimales no negativos y nulos en los 4 campos
    - Archivo: `backend/tests/unit/test_utils/test_computations_properties.py`
  - [x] 5.5 Escribir property test de `roi_percentage`
    - **Property 6: El ROI es nulo si y sólo si la inversión es cero**
    - **Validates: Requirements 7.3, 7.6, 7.7**
    - Usar `hypothesis` (mínimo 100 iteraciones) con inversión y valor de mercado arbitrarios, verificando la equivalencia exacta y la fórmula en el resto de los casos
    - Archivo: `backend/tests/unit/test_utils/test_computations_properties.py`

- [x] 6. Bloque 0 - Crear los componentes UI transversales
  - [x] 6.1 Crear `frontend/src/components/ui/LiveRegion.tsx`
    - Props `{ message: string; politeness?: "polite" | "assertive" }`
    - Renderiza un contenedor `role="status"` con `aria-live` según `politeness` y `aria-atomic="true"`, visualmente oculto pero disponible para lectores de pantalla
    - _Requirements: 18.2_
  - [x] 6.2 Crear `frontend/src/components/ui/Badge.tsx`
    - Props `{ label: string; tone: "neutral" | "success" | "warning" | "danger"; icon?: ReactNode }`
    - El significado se transmite con texto e icono además del color, nunca solo con color
    - _Requirements: 16.3, 12.11_
  - [x] 6.3 Crear `frontend/src/components/ui/Table.tsx`
    - Props genéricas `{ caption: string; columns: TableColumn<T>[]; rows: T[] }`
    - `<caption>` obligatorio, `scope="col"` en encabezados, orden anunciado con `aria-sort`, contenedor con scroll horizontal propio para no romper el zoom al 200%
    - _Requirements: 18.4, 16.2_
  - [x] 6.4 Crear `frontend/src/components/ui/Tooltip.tsx`
    - Props `{ content: string; children: ReactElement }`
    - Visible por foco de teclado y por puntero, asociado con `aria-describedby`, se cierra con Escape
    - _Requirements: 18.3_
  - [x] 6.5 Crear `frontend/src/components/ui/SkipLink.tsx` e integrarlo en `AppLayout`
    - Props `{ targetId: string }`; primer elemento focusable, visible al recibir foco
    - Modificar `frontend/src/components/layout/AppLayout.tsx` para renderizar `SkipLink` y dar `id="main-content"` al `<main>`
    - _Requirements: 18.5_
  - [x] 6.6 Crear `frontend/src/hooks/useReducedMotion.ts` y `frontend/src/hooks/useAnnouncement.ts`
    - `useReducedMotion()` lee `matchMedia("(prefers-reduced-motion: reduce)")` y reacciona a cambios
    - `useAnnouncement()` expone `(message, politeness?) => void` sobre una `LiveRegion` montada en `AppLayout`
    - _Requirements: 18.1, 18.2_
  - [x] 6.7 Escribir tests de los componentes transversales
    - `frontend/src/components/ui/LiveRegion.test.tsx`, `Badge.test.tsx`, `Table.test.tsx`, `Tooltip.test.tsx`, `SkipLink.test.tsx`
    - Cada uno: renderizado con queries accesibles, roles y atributos ARIA, operación por teclado (Tab, Enter, Escape, flechas donde aplique) y test axe-core obligatorio
    - `frontend/src/hooks/useReducedMotion.test.ts` con `matchMedia` mockeado; `useAnnouncement.test.tsx` verificando que el mensaje llega a la live region
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 19.2, 19.3_
  - [x] 6.8 Agregar claves i18n de los componentes transversales en `es` y `en`
    - `frontend/public/locales/es/translation.json` y `frontend/public/locales/en/translation.json`: sección `a11y` con `skipToContent`, `sortAscending`, `sortDescending`, `tableCaptionFallback`, `closeTooltip`
    - _Requirements: 19.1_

- [x] 7. Checkpoint - Cimientos del Bloque 0 completos
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Bloque 1 - Suppliers backend (R2)
  - [x] 8.1 Crear `backend/api/schemas/supplier.py`
    - `SupplierBase` con `name` (min_length 1), `type`, `country`, `state_province`, `city`, `address`, `postal_code`, `website`, `email` (`EmailStr`), `phone`, `marketplace_url`, `social_media`, `rating` (ge 0, le 5, 2 decimales), `notes`, `is_favorite`, `is_active`
    - `field_validator` `_name_not_blank` (rechaza vacío y solo espacios) y `_type_allowed` (online, physical_store, marketplace, private_seller, auction)
    - `SupplierCreate`, `SupplierUpdate` (todos opcionales), `SupplierResponse` (`from_attributes`), `SupplierPurchase`, `SupplierReferences` con propiedad `total`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.9, 2.10_
  - [x] 8.2 Crear `backend/api/services/supplier_service.py`
    - `SupplierService` con `VALID_TYPES` como `frozenset`, `AsyncSession` por constructor
    - `list` con filtros `type`, `country`, `is_favorite`, `is_active` y paginación `skip`/`limit`; `get`, `create`, `update`
    - `delete` que llama `_count_references` y lanza `DuplicateError` (→ 409) si hay referencias, con el detalle por tipo
    - `get_purchase_history` que devuelve los collection items del proveedor con `purchase_date`, `purchase_price`, `purchase_currency`
    - _Requirements: 2.1, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 19.6_
  - [x] 8.3 Agregar `get_supplier_service` en `backend/api/dependencies.py`
    - Factory `get_supplier_service(db: AsyncSession = Depends(get_db)) -> SupplierService`
    - _Requirements: 19.6_
  - [x] 8.4 Crear `backend/api/routes/suppliers.py` y registrar el router en `backend/main.py`
    - `GET /suppliers` (200), `POST /suppliers` (201, 422), `GET /suppliers/{id}` (200, 404), `PUT /suppliers/{id}` (200, 404, 422), `DELETE /suppliers/{id}` (204, 404, 409), `GET /suppliers/{id}/purchases` (200, 404)
    - Routes finas: validación con Pydantic y `Query`, delegación al service, sin lógica de negocio
    - `app.include_router(suppliers_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 2.1, 2.7, 2.8, 2.9, 2.10, 19.6_
  - [x] 8.5 Escribir unit tests del service en `backend/tests/unit/test_services/test_supplier_service.py`
    - Creación válida; `name` vacío y solo espacios rechazados; `type` no permitido rechazado; `rating` en los límites 0.00 y 5.00 aceptado y fuera rechazado
    - Update de todos los campos editables; toggle de `is_favorite`
    - Cada filtro por separado y combinados; paginación; listado vacío
    - `delete` sin referencias elimina; con referencias en collection items, sightings o accesorios lanza `DuplicateError` con los conteos
    - `get_purchase_history` de proveedor sin compras devuelve lista vacía
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 19.10_
  - [x] 8.6 Escribir integration tests en `backend/tests/integration/test_routes/test_suppliers.py`
    - Códigos 201/200/204/404/409/422 por endpoint, formato de respuesta y cuerpo de error
    - `DELETE` de proveedor referenciado devuelve 409 con el detalle de referencias
    - Filtros y paginación vía query params
    - _Requirements: 2.1, 2.2, 2.3, 2.7, 2.8, 2.10, 19.9_

- [x] 9. Bloque 1 - Suppliers frontend (R2)
  - [x] 9.1 Crear `frontend/src/types/supplier.ts` y `frontend/src/services/suppliersApi.ts`
    - `SupplierType`, `Supplier`, `SupplierCreate`, `SupplierUpdate`, `SupplierPurchase`, `SupplierReferences`; sin `any`
    - `suppliersApi` con `list(filters)`, `get(id)`, `create`, `update`, `remove`, `purchases(id)` sobre `fetchApi`, con conversión camelCase/snake_case
    - _Requirements: 2.1, 2.7, 2.9, 19.7_
  - [x] 9.2 Crear `frontend/src/hooks/useSuppliers.ts`, `useSupplier.ts` y `useSupplierPurchases.ts`
    - React Query con invalidación de `["suppliers"]`; mutación optimista en el toggle de favorito (`onMutate` actualiza cache, `onError` revierte)
    - _Requirements: 2.6, 2.7_
  - [x] 9.3 Crear los componentes de suppliers en `frontend/src/components/suppliers/`
    - `SupplierCard.tsx` (props `supplier`, `onEdit`, `onDelete`, `onToggleFavorite`), `SupplierForm.tsx`, `SupplierFilters.tsx`, `FavoriteToggle.tsx`
    - `SupplierForm` valida localmente `name` no vacío y `rating` en rango, con `aria-invalid` y `aria-describedby`
    - `FavoriteToggle` es un botón con `aria-pressed` y etiqueta traducida
    - _Requirements: 2.1, 2.4, 2.5, 2.6, 2.7_
  - [x] 9.4 Crear `frontend/src/pages/SuppliersPage.tsx` y registrar la ruta y la navegación
    - Listado con filtros, formulario en `Modal`, historial de compras del proveedor seleccionado, estados loading / error / empty
    - Ruta `/suppliers` en `appRoutes` de `frontend/src/App.tsx` como hija de `AppLayout`
    - Enlace en `frontend/src/components/layout/Navigation.tsx`
    - _Requirements: 2.6, 2.7, 2.9_
  - [x] 9.5 Escribir tests de hooks y componentes de suppliers
    - `useSuppliers.test.ts`, `useSupplier.test.ts`, `useSupplierPurchases.test.ts` con MSW: éxito, error, loading, invalidación; el toggle optimista revierte ante error
    - `SupplierCard.test.tsx`, `SupplierForm.test.tsx`, `SupplierFilters.test.tsx`, `FavoriteToggle.test.tsx`, `SuppliersPage.test.tsx`: renderizado, interacciones con `userEvent`, estados, teclado, ARIA y test axe-core obligatorio
    - Actualizar `frontend/src/components/layout/Navigation.test.tsx` con el enlace nuevo
    - _Requirements: 2.6, 2.7, 19.2, 19.3_
  - [x] 9.6 Agregar claves i18n de suppliers en `es` y `en`
    - Sección `suppliers` (`title`, `create`, `edit`, `delete`, `name`, `type`, `typeOptions.*`, `country`, `city`, `rating`, `favorite`, `unfavorite`, `filters.*`, `purchases.*`, `empty`, `deleteBlocked`) y `errors.supplier.*` (`nameRequired`, `invalidType`, `ratingRange`, `hasReferences`, `notFound`)
    - Archivos: `frontend/public/locales/es/translation.json`, `frontend/public/locales/en/translation.json`
    - _Requirements: 19.1_

- [x] 10. Bloque 1 - Wishlist y sightings backend (R3, R4)
  - [x] 10.1 Crear `backend/api/schemas/wishlist.py`
    - `WishlistItemBase` (`desired_condition`, `desired_condition_min`, `must_be_complete`, `desired_completeness_description`, `max_price` ge 0, `currency`, `specific_variant_required`, `variant_description`, `priority` ge 1 le 5, `urgency`, `notes`, `search_notes`, `tags`, `is_active`), `WishlistItemCreate` (con `collection_id` y `catalog_item_id`), `WishlistItemUpdate`, `WishlistItemResponse`
    - `PriceAggregates`, `WishlistItemDetail`, `WishlistAcquire`
    - `SightingBase` con `price` obligatorio (ge 0) y el resto de campos de seguimiento y decisión; `SightingCreate`, `SightingUpdate`, `SightingResponse`
    - Validators de `urgency` y `decision` contra los conjuntos permitidos
    - _Requirements: 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.7_
  - [x] 10.2 Crear `backend/api/services/wishlist_service.py`
    - `WishlistService` con `VALID_URGENCY` y `VALID_DECISIONS`; `list` (filtros `collection_id`, `priority`, `urgency`, `is_active`, `include_acquired=False`), `get`, `get_with_price_aggregates`, `create` (valida existencia de `catalog_item_id` y `collection_id` → `NotFoundError`), `update`, `delete`
    - `mark_acquired` que fija `is_acquired`, `acquired_date` y `acquired_collection_item_id`, y lanza `DuplicateError` si ya estaba adquirido conservando el valor original
    - Sightings: `list_sightings`, `create_sighting`, `update_sighting`, `delete_sighting`
    - Agregados por dialecto: método público que ramifica con `supports_views` entre `_aggregates_from_view` (`v_wishlist_with_avg_price`) y `_aggregates_from_queries` (`func.avg/min/max/count`)
    - _Requirements: 3.1, 3.2, 3.6, 3.7, 3.8, 3.9, 4.1, 4.6, 4.7, 4.8, 4.9, 19.6_
  - [x] 10.3 Agregar `get_wishlist_service` en `backend/api/dependencies.py`
    - Factory para `WishlistService`
    - _Requirements: 19.6_
  - [x] 10.4 Crear `backend/api/routes/wishlist.py` y `backend/api/routes/sightings.py`, y registrar los routers en `backend/main.py`
    - `GET/POST /wishlist`, `GET/PUT/DELETE /wishlist/{id}`, `POST /wishlist/{id}/acquire` (200, 404, 409), `GET/POST /wishlist/{id}/sightings`, `PUT/DELETE /sightings/{id}`
    - `GET /wishlist` excluye adquiridos salvo `?include_acquired=true`
    - `app.include_router(wishlist_router, prefix="/api")` y `app.include_router(sightings_router, prefix="/api")`
    - _Requirements: 3.1, 3.6, 3.7, 3.8, 4.1, 4.6, 19.6_
  - [x] 10.5 Escribir unit tests del service en `backend/tests/unit/test_services/test_wishlist_service.py`
    - Creación válida; referencias inexistentes → `NotFoundError`; `priority` 0 y 6 rechazados, 1 y 5 aceptados; `urgency` inválida rechazada
    - Cada filtro y sus combinaciones; adquiridos excluidos por defecto e incluidos con el flag
    - `mark_acquired` primera vez tiene éxito; segunda vez lanza error y conserva `acquired_collection_item_id`
    - Sightings: creación sin `price` rechazada, seguimiento de contacto, `decision` inválida rechazada, borrado
    - Agregados sin avistamientos → precios nulos y conteos en cero; con avistamientos → avg/min/max/total/available correctos
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.2, 4.4, 4.5, 4.7, 4.8, 4.9, 19.10_
  - [x] 10.6 Escribir integration tests en `backend/tests/integration/test_routes/test_wishlist.py` y `test_sightings.py`
    - Códigos 201/200/204/404/409/422 por endpoint, formato de respuesta, orden de sightings por `sighted_at` descendente
    - `POST /wishlist/{id}/acquire` dos veces devuelve 200 y luego 409
    - _Requirements: 3.1, 3.2, 3.9, 4.1, 4.2, 4.6, 19.9_
  - [x] 10.7 Escribir property test de la transición de adquisición
    - **Property 11: Marcar como adquirido es una transición de una sola vía**
    - **Validates: Requirements 3.7, 3.8, 3.9**
    - Usar `hypothesis` (mínimo 100 iteraciones) con secuencias arbitrarias de intentos de adquisición sobre wishlist items generados
    - Archivo: `backend/tests/unit/test_services/test_wishlist_service_properties.py`
  - [x] 10.8 Escribir property test de los agregados de precio
    - **Property 12: Los agregados de precio son consistentes con los avistamientos**
    - **Validates: Requirements 4.7, 4.8, 4.9**
    - Usar `hypothesis` (mínimo 100 iteraciones) generando conjuntos arbitrarios de avistamientos, incluido el conjunto vacío
    - Archivo: `backend/tests/unit/test_services/test_wishlist_service_properties.py`

- [x] 11. Bloque 1 - Wishlist y sightings frontend (R3, R4)
  - [x] 11.1 Crear `frontend/src/types/wishlist.ts` y `frontend/src/services/wishlistApi.ts`
    - `Urgency`, `Priority`, `SightingDecision`, `WishlistItem`, `WishlistItemDetail`, `PriceAggregates`, `Sighting`, y sus `Create`/`Update`
    - `wishlistApi` con `list`, `get`, `create`, `update`, `remove`, `acquire`, `listSightings`, `createSighting`, `updateSighting`, `removeSighting`
    - _Requirements: 3.1, 3.6, 4.1, 19.7_
  - [x] 11.2 Crear `frontend/src/hooks/useWishlist.ts`, `useWishlistItem.ts` y `useSightings.ts`
    - Invalidación cruzada: crear o borrar un sighting invalida el detalle del wishlist item para refrescar los agregados
    - _Requirements: 3.6, 4.7, 4.10_
  - [x] 11.3 Crear los componentes de wishlist en `frontend/src/components/wishlist/`
    - `WishlistCard.tsx`, `WishlistForm.tsx`, `WishlistFilters.tsx`, `PriorityBadge.tsx`, `UrgencyBadge.tsx`, `AcquireDialog.tsx`, `SightingList.tsx`, `SightingForm.tsx`, `PriceAggregatesPanel.tsx`
    - `PriorityBadge` y `UrgencyBadge` sobre `Badge`: codifican el nivel con texto e icono además de color
    - `SightingForm` exige `price`; `AcquireDialog` pide el collection item resultante y confirma
    - _Requirements: 3.3, 3.4, 3.5, 3.7, 3.10, 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 11.4 Crear `frontend/src/pages/WishlistPage.tsx` y `frontend/src/pages/WishlistDetailPage.tsx`, con rutas y navegación
    - `WishlistPage`: listado con prioridad, urgencia, presupuesto máximo y estado, filtros y estado vacío
    - `WishlistDetailPage`: sightings ordenados por `sighted_at` descendente más `PriceAggregatesPanel`
    - Rutas `/wishlist` y `/wishlist/:id` en `frontend/src/App.tsx`; enlace en `Navigation.tsx`
    - _Requirements: 3.10, 4.10_
  - [x] 11.5 Escribir tests de hooks y componentes de wishlist
    - Hooks con MSW: éxito, error, loading, invalidación cruzada tras mutar sightings
    - Un `.test.tsx` por componente y por página: renderizado, interacciones, estados loading / error / empty, teclado, ARIA y test axe-core obligatorio
    - `AcquireDialog.test.tsx` verifica focus trap, cierre con Escape y retorno del foco
    - _Requirements: 3.10, 4.10, 18.6, 19.2, 19.3_
  - [x] 11.6 Agregar claves i18n de wishlist y sightings en `es` y `en`
    - Secciones `wishlist.*` (incluye `priority.*`, `urgency.*`, `acquire.*`, `filters.*`, `empty`) y `sightings.*` (incluye `decision.*`, `contact.*`, `aggregates.*`)
    - `errors.wishlist.*` (`referenceNotFound`, `priorityRange`, `invalidUrgency`, `alreadyAcquired`) y `errors.sighting.*` (`priceRequired`, `invalidDecision`)
    - Archivos: `frontend/public/locales/{es,en}/translation.json`
    - _Requirements: 19.1_

- [x] 12. Checkpoint - Suppliers y wishlist completos
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Bloque 1 - Componentes de items backend (R5)
  - [x] 13.1 Crear `backend/api/schemas/item_component.py`
    - `ItemComponentBase` con `standard_component_id`, `component_name`, `component_type`, `is_present`, `condition`, `condition_notes`, `variant_description`
    - `model_validator(mode="after")` `_name_or_standard_required`: `component_name` obligatorio cuando `standard_component_id` es `None`
    - `ItemComponentCreate`, `ItemComponentUpdate`, `ItemComponentResponse`, `ComponentTemplateEntry`, `CompletenessResult`
    - _Requirements: 5.2, 5.3, 5.4_
  - [x] 13.2 Crear `backend/api/services/item_component_service.py`
    - `get_template` devuelve los `standard_components` de la sub-categoría del item con el estado registrado si existe
    - `list`, `upsert`, `update`, `delete` (devuelve `CompletenessResult`)
    - `recalculate_completeness` usa `is_item_complete()` de `utils/computations.py` sobre los componentes `required` y persiste `collection_items.is_complete`; se invoca al final de cada mutación
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.6, 5.8, 19.6_
  - [x] 13.3 Agregar `get_item_component_service` en `backend/api/dependencies.py`
    - Factory para `ItemComponentService`
    - _Requirements: 19.6_
  - [x] 13.4 Crear `backend/api/routes/item_components.py` y registrar el router en `backend/main.py`
    - `GET /collection-items/{id}/components/template`, `GET /collection-items/{id}/components`, `POST /collection-items/{id}/components` (201), `PUT /item-components/{id}`, `DELETE /item-components/{id}` (200 con `CompletenessResult`, no 204)
    - `app.include_router(item_components_router, prefix="/api")`
    - _Requirements: 5.1, 5.2, 5.7, 5.8, 19.6_
  - [x] 13.5 Escribir unit tests del service en `backend/tests/unit/test_services/test_item_component_service.py`
    - Template de una sub-categoría con componentes y de una sin componentes
    - Componente ad-hoc con `standard_component_id` nulo y `component_name` presente aceptado; sin ninguno de los dos rechazado
    - Item con todos los `required` presentes es completo; con uno ausente es incompleto
    - Item cuya sub-categoría no define `required` se considera completo
    - Borrado recalcula completitud y devuelve el nuevo estado
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8, 19.10_
  - [x] 13.6 Escribir integration tests en `backend/tests/integration/test_routes/test_item_components.py`
    - Códigos 200/201/404/422; `DELETE` devuelve 200 con `CompletenessResult`; item inexistente devuelve 404
    - _Requirements: 5.1, 5.4, 5.8, 19.9_
  - [x] 13.7 Escribir property test de la completitud del item
    - **Property 10: La completitud del item equivale a la presencia de todos los requeridos**
    - **Validates: Requirements 5.5, 5.6, 5.8**
    - Usar `hypothesis` (mínimo 100 iteraciones) generando conjuntos arbitrarios de standard components y de registros de presencia, incluido el conjunto vacío de requeridos
    - Archivo: `backend/tests/unit/test_services/test_item_component_service_properties.py`

- [x] 14. Bloque 1 - Componentes de items frontend (R5)
  - [x] 14.1 Crear `frontend/src/types/itemComponent.ts` y `frontend/src/services/itemComponentsApi.ts`
    - `ComponentType`, `ItemComponent`, `ComponentTemplateEntry`, `CompletenessResult` y los `Create`/`Update`
    - `itemComponentsApi` con `template`, `list`, `upsert`, `update`, `remove`
    - _Requirements: 5.1, 5.2, 19.7_
  - [x] 14.2 Crear `frontend/src/hooks/useItemComponents.ts`
    - Mutaciones que consumen el `CompletenessResult` de la respuesta para actualizar el badge sin refetch adicional
    - _Requirements: 5.7, 5.8_
  - [x] 14.3 Crear los componentes en `frontend/src/components/components/`
    - `ComponentChecklist.tsx` (props `collectionItemId`, `onCompletenessChange`), `ComponentRow.tsx`, `CompletenessBadge.tsx` sobre `Badge`
    - Cada fila es un checkbox etiquetado con `condition` y notas opcionales; el checklist anuncia el cambio de completitud vía `useAnnouncement`
    - Integrar `ComponentChecklist` y `CompletenessBadge` en el detalle de collection item de `frontend/src/pages/CollectionDetailPage.tsx`
    - _Requirements: 5.1, 5.2, 5.3, 5.7_
  - [x] 14.4 Escribir tests de hook y componentes de item components
    - `useItemComponents.test.ts` con MSW; `ComponentChecklist.test.tsx`, `ComponentRow.test.tsx`, `CompletenessBadge.test.tsx`: renderizado, toggle con `userEvent`, actualización del badge sin recarga, teclado, ARIA y test axe-core obligatorio
    - Actualizar `frontend/src/pages/CollectionDetailPage.test.tsx` con la integración del checklist
    - _Requirements: 5.7, 19.2, 19.3_
  - [x] 14.5 Agregar claves i18n de componentes en `es` y `en`
    - Sección `components.*` (`title`, `template`, `present`, `absent`, `addCustom`, `componentName`, `componentType.*`, `condition`, `conditionNotes`, `variantDescription`, `complete`, `incomplete`, `completenessAnnouncement`) y `errors.component.nameRequired`
    - Archivos: `frontend/public/locales/{es,en}/translation.json`
    - _Requirements: 19.1_

- [x] 15. Bloque 1 - Colecciones multi-category backend (R1)
  - [x] 15.1 Extender `backend/api/schemas/collection.py`
    - Agregar `theme`, `theme_description`, `goal_description`, `goal_items_count`, `display_order`, `is_public`, `is_active` a `CollectionBase` si faltan
    - Restringir `collection_type` a `single_category | multi_category | mixed` con validator
    - Agregar `CollectionStats` y `CollectionItemGroup`
    - _Requirements: 1.1, 1.5, 1.6, 1.7_
  - [x] 15.2 Extender `backend/api/services/collection_service.py`
    - `VALID_TYPES` como `frozenset`; `_validate_type_and_restriction` exige `restricted_to_sub_category_id` solo para `single_category` y lo acepta nulo en el resto
    - Invocar la validación en `create` y en `update`
    - `list_items_grouped` agrupa los items por main/sub categoría con su conteo
    - Validar en la adición de collection items que la sub-categoría coincide con la restricción en colecciones `single_category` (`ValidationError`)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 19.6_
  - [x] 15.3 Crear `backend/api/services/collection_stats_service.py`
    - `get_collection_stats` ramifica con `supports_views` entre `_stats_from_view` (`v_collection_stats`) y `_stats_from_queries`
    - Devuelve `total_items`, `different_categories_count`, `total_invested`, `current_value`, `value_gain`, `roi_percentage` (vía `roi_percentage()` de computations), `complete_items`, `graded_items`
    - _Requirements: 1.7, 1.9, 19.6_
  - [x] 15.4 Agregar `get_collection_stats_service` en `backend/api/dependencies.py` y los endpoints en `backend/api/routes/collections.py`
    - `GET /collections/{id}/items/grouped` (200, 404) y `GET /collections/{id}/stats` (200, 404)
    - _Requirements: 1.6, 1.7, 19.6_
  - [x] 15.5 Ampliar unit tests en `backend/tests/unit/test_services/test_collection_service.py` y crear `test_collection_stats_service.py`
    - Los tres tipos válidos aceptados y cualquier otro rechazado; `single_category` sin restricción rechazado; otros tipos con restricción nula aceptados
    - Item con sub-categoría no coincidente rechazado en `single_category`
    - `list_items_grouped` con items de varias categorías y con colección vacía
    - Stats: colección vacía (conteos en cero, ROI nulo), items sin `purchase_price` excluidos de la inversión, `complete_items` refleja la completitud calculada en la Task 13
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7, 1.9, 19.10_
  - [x] 15.6 Ampliar integration tests en `backend/tests/integration/test_routes/test_collections.py`
    - `GET /collections/{id}/stats` y `/items/grouped` devuelven 200 con el formato esperado y 404 para colección inexistente
    - `POST` de colección `single_category` sin restricción devuelve 422 identificando el campo faltante
    - _Requirements: 1.2, 1.6, 1.7, 19.9_

- [x] 16. Bloque 1 - Colecciones multi-category frontend (R1)
  - [x] 16.1 Extender `frontend/src/types/collection.ts` y `frontend/src/services/collectionsApi.ts`
    - Agregar `CollectionStats`, `CollectionItemGroup` y los campos nuevos de `Collection`
    - `collectionsApi.stats(id)` y `collectionsApi.itemsGrouped(id)`
    - _Requirements: 1.5, 1.6, 1.7, 19.7_
  - [x] 16.2 Crear `frontend/src/hooks/useCollectionStats.ts` y `frontend/src/hooks/useCollectionItemsGrouped.ts`
    - React Query por colección, con invalidación al mutar items o componentes
    - _Requirements: 1.6, 1.7_
  - [x] 16.3 Crear `frontend/src/components/collections/CollectionStatsPanel.tsx` y `GroupedItemList.tsx`
    - `CollectionStatsPanel` muestra los 8 campos de `CollectionStats` con ROI nulo representado como "sin datos", no como 0
    - `GroupedItemList` (props `groups`, `onEditItem`) agrupa por categoría con encabezado y conteo por grupo
    - _Requirements: 1.6, 1.7_
  - [x] 16.4 Extender `frontend/src/components/collections/CollectionForm.tsx`
    - Campos `theme`, `themeDescription`, `goalDescription`, `goalItemsCount`, `displayOrder`, `isPublic`, `isActive`
    - El selector de sub-categoría se muestra y se exige solo cuando `collectionType === "single_category"`
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
  - [x] 16.5 Integrar en `frontend/src/pages/CollectionDetailPage.tsx`
    - Renderizar `CollectionStatsPanel` y, para colecciones `multi_category` y `mixed`, `GroupedItemList`
    - Estado vacío con acción para agregar el primer item cuando la colección no tiene items
    - _Requirements: 1.6, 1.8_
  - [x] 16.6 Escribir tests de hooks, componentes y página de colecciones
    - `useCollectionStats.test.ts`, `useCollectionItemsGrouped.test.ts` con MSW
    - `CollectionStatsPanel.test.tsx`, `GroupedItemList.test.tsx`: renderizado, conteos por grupo, ROI nulo, teclado, ARIA y test axe-core obligatorio
    - Actualizar `CollectionForm.test.tsx` (campos nuevos, selector condicional) y `CollectionDetailPage.test.tsx` (agrupado y estado vacío)
    - _Requirements: 1.5, 1.6, 1.7, 1.8, 19.2, 19.3_
  - [x] 16.7 Agregar claves i18n de colecciones multi-category en `es` y `en`
    - Ampliar `collections.*` con `theme`, `themeDescription`, `goalDescription`, `goalItemsCount`, `displayOrder`, `isPublic`, `isActive`, `types.*`, `grouped.*`, `stats.*`, `emptyFirstItem`
    - `errors.collection.*` (`subCategoryRequired`, `invalidType`, `subCategoryMismatch`)
    - Archivos: `frontend/public/locales/{es,en}/translation.json`
    - _Requirements: 19.1_

- [x] 17. Checkpoint - Componentes y colecciones multi-category completos
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Bloque 1 - Búsqueda avanzada backend (R6)
  - [x] 18.1 Crear `backend/api/schemas/search.py`
    - `CatalogSearchParams` con `q`, los 9 filtros, `year_min`/`year_max` (ge 1800, le 2200), `skip` (ge 0), `limit` (ge 1, le 200)
    - `SearchMode` enum (`full_text`, `fuzzy`, `degraded`) y `CatalogSearchResult` con `items`, `total`, `search_mode`
    - _Requirements: 6.4, 6.5, 6.8_
  - [x] 18.2 Crear `backend/api/services/search_service.py`
    - Constructor recibe `AsyncSession` y `Settings`; lee `SEARCH_SIMILARITY_THRESHOLD`
    - `search_catalog_items` ramifica con `supports_full_text` entre `_full_text_search` y `_degraded_search`
    - `_full_text_search`: `to_tsquery` + `ts_rank` sobre `search_vector`; si no hay resultados cae a `similarity(title, q) >= threshold` de `pg_trgm` y marca `search_mode = "fuzzy"`
    - `_degraded_search`: `ILIKE` sobre `title`, `subtitle` y `alternate_titles`, con `search_mode = "degraded"`
    - `_apply_filters(stmt, params)` compartido por ambos caminos, aplicado sobre el statement de texto para preservar el orden por relevancia
    - Devolver siempre el total de coincidencias junto a la página
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 19.6_
  - [x] 18.3 Agregar `get_search_service` en `backend/api/dependencies.py` y crear `backend/api/routes/search.py`
    - `GET /search/catalog-items` (200) con los query params de `CatalogSearchParams`
    - Registrar `app.include_router(search_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 6.5, 6.8, 19.6_
  - [x] 18.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_search_service.py`
    - Camino SQLite: coincidencias por `title`, `subtitle` y `alternate_titles`; respuesta declara `search_mode = "degraded"`
    - Cada filtro por separado y todos combinados; `year_min`/`year_max` como rango inclusivo
    - Búsqueda sin resultados devuelve lista vacía y `total = 0`
    - Paginación: `skip`/`limit` no alteran el `total`
    - _Requirements: 6.4, 6.5, 6.7, 6.8, 19.10_
  - [x] 18.5 Escribir tests marcados `@pytest.mark.postgres` en `backend/tests/integration/test_postgres/test_search_postgres.py`
    - Orden por relevancia según los pesos A/B/C: coincidencia en `title` antes que en `description`
    - `search_mode = "full_text"` con resultados y `"fuzzy"` con término mal escrito por encima del umbral
    - _Requirements: 6.1, 6.2, 6.3, 19.8_
  - [x] 18.6 Escribir integration tests en `backend/tests/integration/test_routes/test_search.py`
    - 200 con formato `CatalogSearchResult`; `limit` fuera de rango devuelve 422; combinación de `q` y filtros
    - _Requirements: 6.5, 6.6, 6.8, 19.9_
  - [x] 18.7 Escribir property test del subconjunto filtrado
    - **Property 5: Los resultados filtrados son un subconjunto de los no filtrados**
    - **Validates: Requirements 6.5, 6.6**
    - Usar `hypothesis` (mínimo 100 iteraciones) generando catálogos, términos y combinaciones de filtros; verificar inclusión de identificadores y conservación del orden relativo de los comunes
    - Archivo: `backend/tests/unit/test_services/test_search_service_properties.py`

- [x] 19. Bloque 1 - Búsqueda avanzada frontend (R6)
  - [x] 19.1 Crear `frontend/src/types/search.ts` y `frontend/src/services/searchApi.ts`
    - `SearchMode`, `CatalogSearchFilters`, `CatalogSearchResult`
    - `searchApi.catalogItems(filters, skip, limit)` serializando solo los filtros definidos
    - _Requirements: 6.5, 6.8, 19.7_
  - [x] 19.2 Crear `frontend/src/hooks/useDebouncedValue.ts` y `frontend/src/hooks/useSearch.ts`
    - `useDebouncedValue(value, delayMs)` con timer propio, sin dependencias nuevas; debounce de 300 ms
    - `useSearch` consulta con el valor debounced y mantiene `keepPreviousData` para evitar parpadeo
    - _Requirements: 6.9_
  - [x] 19.3 Crear los componentes en `frontend/src/components/search/`
    - `SearchBar.tsx` (props `value`, `onChange`, `resultCount`, `isLoading`), `SearchFilters.tsx`, `SearchResultList.tsx`, `SearchModeNotice.tsx`
    - `SearchModeNotice` explica el modo degradado cuando `searchMode === "degraded"`
    - El conteo de resultados se anuncia con `LiveRegion` (`polite`) al cambiar o limpiar filtros
    - Estado vacío con sugerencia de ampliar o quitar filtros; botón de limpiar filtros
    - _Requirements: 6.4, 6.7, 6.9, 6.10_
  - [x] 19.4 Crear `frontend/src/pages/SearchPage.tsx` con ruta y navegación
    - Composición de barra, filtros y resultados paginados con el total de coincidencias
    - Ruta `/search` en `frontend/src/App.tsx`; enlace en `Navigation.tsx`
    - _Requirements: 6.7, 6.8_
  - [x] 19.5 Escribir tests de hooks, componentes y página de búsqueda
    - `useDebouncedValue.test.ts` con timers falsos; `useSearch.test.ts` con MSW verificando que no se emite consulta por cada pulsación
    - `SearchBar.test.tsx`, `SearchFilters.test.tsx`, `SearchResultList.test.tsx`, `SearchModeNotice.test.tsx`, `SearchPage.test.tsx`: estado vacío, limpiar filtros, anuncio del conteo, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 6.7, 6.9, 6.10, 19.2, 19.3_
  - [x] 19.6 Agregar claves i18n de búsqueda en `es` y `en`
    - Sección `search.*` (`title`, `placeholder`, `filters.*`, `results`, `resultCount`, `noResults`, `clearFilters`, `degradedMode`, `fuzzyMode`, `yearRange`)
    - Archivos: `frontend/public/locales/{es,en}/translation.json`
    - _Requirements: 19.1_

- [x] 20. Checkpoint - Búsqueda avanzada completa
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Bloque 1 - Dark mode: tokens y proveedor de tema (R8)
  - [x] 21.1 Configurar `darkMode: "class"` y tokens semánticos en `frontend/tailwind.config.ts`
    - `darkMode: "class"`; tokens `surface`, `surface-muted`, `content`, `content-muted`, `border`, `accent`, `danger`, cada uno con su valor claro y su variante oscura
    - Todos los pares texto/fondo con ratio mínimo 4.5:1 para WCAG AA
    - Agregar en `frontend/src/index.css` la regla `@media (prefers-reduced-motion: reduce)` que anula `transition` y `animation` no esenciales, y `:focus-visible` con outline de 2 px y contraste 3:1
    - _Requirements: 8.6, 18.1, 18.5_
  - [x] 21.2 Crear `frontend/src/theme/storage.ts`
    - `STORAGE_KEY = "hoard.theme"`; `readPreference()` devuelve `"auto"` ante valor inválido o `localStorage` inaccesible (envuelto en `try/catch`), `writePreference()`, `clearPreference()`
    - _Requirements: 8.2, 8.4, 8.5_
  - [x] 21.3 Crear `frontend/src/theme/ThemeProvider.tsx` y `frontend/src/theme/useTheme.ts`
    - `ThemePreference = "light" | "dark" | "auto"`; contexto con `preference`, `resolvedTheme`, `setPreference`
    - Escribe o quita `class="dark"` en `document.documentElement`; escucha `matchMedia("(prefers-color-scheme: dark)")` cuando la preferencia es `auto`
    - Montar el provider en `frontend/src/main.tsx` por encima de `App`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [x] 21.4 Agregar el script inline de tema en `frontend/index.html`
    - Aplica la clase antes del primer paint leyendo `hoard.theme` y `prefers-color-scheme`, dentro de `try/catch`
    - _Requirements: 8.1, 8.2, 8.5_
  - [x] 21.5 Crear `frontend/src/components/ui/ThemeToggle.tsx` e integrarlo en `AppLayout`
    - Grupo de radio de 3 opciones (claro / oscuro / automático) con `role="radiogroup"`, `aria-checked` y navegación por flechas usando `react-aria`
    - Renderizarlo en `frontend/src/components/layout/AppLayout.tsx` junto al `LanguageSelector`
    - _Requirements: 8.3, 8.7_
  - [x] 21.6 Escribir tests de tema
    - `frontend/src/theme/storage.test.ts`: valor inválido cae a `auto`, `localStorage` que lanza no rompe
    - `frontend/src/theme/ThemeProvider.test.tsx` con `matchMedia` mockeado: sin preferencia sigue el sistema, preferencia explícita gana, `auto` limpia el storage, alternar actualiza la clase sin recargar
    - `frontend/src/components/ui/ThemeToggle.test.tsx`: `aria-checked`, navegación por flechas, activación con teclado y test axe-core obligatorio
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7, 19.2, 19.3_
  - [x] 21.7 Crear la suite de contraste en ambos temas en `frontend/tests/accessibility/theme.a11y.test.tsx`
    - Corre axe-core sobre cada página existente en tema claro y en tema oscuro, exigiendo cero violaciones de contraste WCAG 2.1 AA
    - _Requirements: 8.6, 18.7_
  - [x] 21.8 Agregar claves i18n del selector de tema en `es` y `en`
    - Sección `theme.*` (`label`, `light`, `dark`, `auto`, `currentTheme`)
    - Archivos: `frontend/public/locales/{es,en}/translation.json`
    - _Requirements: 19.1_

- [x] 22. Bloque 1 - Idiomas pt, fr y de (R9)
  - [x] 22.1 Extender `frontend/src/i18n/config.ts`
    - `supportedLngs: ["es", "en", "pt", "fr", "de"]`, `detection.order: ["localStorage", "navigator", "htmlTag"]`, `fallbackLng` explícito
    - Listener `i18n.on("languageChanged", lng => { document.documentElement.lang = lng })`
    - _Requirements: 9.1, 9.3, 9.4, 9.6_
  - [x] 22.2 Crear los tres archivos de traducción portando todas las claves existentes
    - Crear `frontend/public/locales/pt/translation.json`, `frontend/public/locales/fr/translation.json` y `frontend/public/locales/de/translation.json`
    - Portar el conjunto completo de claves acumulado hasta este punto (Fase 1 más las Tasks 6, 9, 11, 14, 16, 19 y 21), con exactamente el mismo conjunto que `es` y `en` y sin valores vacíos
    - A partir de esta task, toda clave nueva se agrega a los 5 archivos
    - _Requirements: 9.1, 9.2, 9.3, 19.1_
  - [x] 22.3 Actualizar `frontend/src/components/layout/LanguageSelector.tsx`
    - Las 5 opciones con el nombre de cada idioma en su propio idioma, `aria-label` traducido y opción activa marcada, operable con teclado
    - _Requirements: 9.1, 9.4, 9.5_
  - [x] 22.4 Crear el chequeo de paridad de claves `frontend/scripts/check-i18n-keys.ts` y el script `lint:i18n`
    - Compara los 5 archivos y falla listando claves faltantes y sobrantes y valores vacíos
    - Agregar `"lint:i18n": "tsx scripts/check-i18n-keys.ts"` en `frontend/package.json`
    - _Requirements: 9.2, 19.1_
  - [x] 22.5 Actualizar tests de i18n
    - `frontend/src/components/layout/LanguageSelector.test.tsx`: las 5 opciones, cambio de idioma, `document.documentElement.lang` actualizado, persistencia, teclado, ARIA y test axe-core
    - Extender `frontend/src/pages/i18n.property.test.ts` a los 5 idiomas
    - _Requirements: 9.1, 9.4, 9.5, 9.6, 19.2, 19.3_
  - [x] 22.6 Escribir property test de paridad de claves i18n
    - **Property 8: Paridad de claves i18n entre los cinco idiomas**
    - **Validates: Requirements 9.2, 19.1**
    - Usar `fast-check` (mínimo 100 iteraciones) sobre el conjunto unión de claves de los 5 archivos, verificando existencia y valor no vacío en todos
    - Archivo: `frontend/src/i18n/i18nParity.property.test.ts`

- [x] 23. Checkpoint - Cierre del Bloque 1 (Fase 2 Core) y subida de coverage a 80%
  - Elevar `fail_under = 80` en `backend/pyproject.toml` y `coverage.thresholds.lines = 80` en `frontend/vitest.config.ts`
  - Ensure all tests pass, ask the user if questions arise.

- [x] 24. Bloque 2 - Historial de precios backend (R10)
  - [x] 24.1 Crear `backend/api/schemas/price_history.py`
    - `PriceHistoryBase` con `condition` (obligatorio), `is_complete`, `completeness_description`, `price` (ge 0, 2 decimales), `currency`, `source`, `source_url`, `price_date` (obligatorio), `region`, `notes`
    - `PriceHistoryCreate`, `PriceHistoryResponse`, `LatestPriceEntry`, `ValueUpdateResult` (`updated`, `current_market_value`, `value_source`, `reason`)
    - _Requirements: 10.2, 10.4, 10.6, 10.7_
  - [x] 24.2 Crear `backend/api/services/price_history_service.py`
    - `list` con filtros `condition`, `is_complete`, `region`, `date_from`, `date_to`, ordenado por `price_date` descendente
    - `create` verifica la clave natural con un `SELECT` previo y lanza `DuplicateError` con mensaje útil; `delete`
    - `latest_by_condition` devuelve el último precio por condición
    - `refresh_item_market_value` toma el precio más reciente compatible con la condición y completitud del item y escribe `current_market_value`, `current_value_currency`, `last_value_update`, `value_source`; si no hay precio compatible devuelve `updated=False` con `reason` y no modifica nada
    - _Requirements: 10.2, 10.3, 10.5, 10.6, 10.7, 10.8, 19.6_
  - [x] 24.3 Agregar `get_price_history_service` en `backend/api/dependencies.py` y crear `backend/api/routes/price_history.py`
    - `GET/POST /catalog-items/{id}/price-history`, `GET /catalog-items/{id}/price-history/latest`, `DELETE /price-history/{id}` (204), `POST /collection-items/{id}/refresh-value` (200)
    - Registrar `app.include_router(price_history_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 10.2, 10.5, 10.6, 19.6_
  - [x] 24.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_price_history_service.py`
    - Creación válida; duplicado de clave natural lanza `DuplicateError`; `price` negativo rechazado; catalog item inexistente → `NotFoundError`
    - Cada filtro y sus combinaciones; orden descendente por `price_date`; historial vacío
    - `refresh_item_market_value` con precio compatible actualiza los 4 campos; sin precio compatible devuelve `updated=False` y deja el valor previo intacto
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 19.10_
  - [x] 24.5 Escribir integration tests en `backend/tests/integration/test_routes/test_price_history.py`
    - Códigos 200/201/204/404/409/422 por endpoint y formato de respuesta
    - `POST /collection-items/{id}/refresh-value` devuelve 200 con `ValueUpdateResult` tanto cuando actualiza como cuando no
    - _Requirements: 10.2, 10.3, 10.6, 10.7, 19.9_

- [ ] 25. Bloque 2 - Historial de precios frontend (R10)
  - [~] 25.1 Crear `frontend/src/types/priceHistory.ts` y `frontend/src/services/priceHistoryApi.ts`
    - `PriceHistoryEntry`, `PriceHistoryCreate`, `LatestPriceEntry`, `ValueUpdateResult`
    - `priceHistoryApi` con `list(catalogItemId, filters)`, `create`, `remove`, `latest`, `refreshValue(collectionItemId)`
    - _Requirements: 10.5, 10.6, 19.7_
  - [~] 25.2 Crear `frontend/src/hooks/usePriceHistory.ts` y `frontend/src/hooks/useRefreshMarketValue.ts`
    - `useRefreshMarketValue` invalida el detalle del collection item y las stats al actualizar
    - _Requirements: 10.6, 10.8_
  - [~] 25.3 Crear los componentes en `frontend/src/components/priceHistory/`
    - `PriceHistoryTable.tsx` sobre el componente `Table`, `PriceHistoryForm.tsx`, `LatestPriceSummary.tsx`
    - Integrarlos en el detalle de catalog item de `frontend/src/pages/CatalogDetailPage.tsx`
    - _Requirements: 10.9_
  - [~] 25.4 Escribir tests de hooks y componentes de price history
    - Hooks con MSW; `PriceHistoryTable.test.tsx`, `PriceHistoryForm.test.tsx`, `LatestPriceSummary.test.tsx`: renderizado, orden descendente, historial vacío, mensaje cuando no hubo actualización de valor, teclado, ARIA y test axe-core obligatorio
    - Actualizar `frontend/src/pages/CatalogDetailPage.test.tsx`
    - _Requirements: 10.7, 10.9, 19.2, 19.3_
  - [~] 25.5 Agregar claves i18n de price history en los 5 idiomas
    - Sección `priceHistory.*` (`title`, `add`, `condition`, `isComplete`, `price`, `source`, `priceDate`, `region`, `latest`, `refreshValue`, `noCompatiblePrice`, `empty`, `filters.*`) y `errors.priceHistory.*` (`duplicate`, `negativePrice`)
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [ ] 26. Bloque 2 - Transacciones backend (R11)
  - [~] 26.1 Crear `backend/api/schemas/transaction.py`
    - `TransactionBase` con `transaction_type` (validator contra los 10 valores permitidos), `transaction_date`, `amount`, `currency`, `shipping_cost`, `tax_amount`, `other_fees`, `supplier_id`, `counterpart_name`, `invoice_number`, `receipt_path`, `payment_method`, `notes`
    - `TransactionCreate` y `TransactionUpdate` **sin** `total_amount`; `TransactionResponse` con `total_amount` de solo lectura
    - `ItemInvestment` con `real_invested`, `total_outflow`, `total_inflow`, `current_market_value`, `roi_percentage`, `source`
    - _Requirements: 11.2, 11.3, 11.4, 11.6, 11.7, 11.8_
  - [~] 26.2 Crear `backend/api/services/transaction_service.py`
    - `OUTFLOW_TYPES`, `INFLOW_TYPES` y `VALID_TYPES` como constantes documentadas (`gift_received` y `gift_given` clasificados como ingresos)
    - `create` ramifica con `supports_generated_columns`: en PostgreSQL lee `total_amount` tras `refresh()`, en SQLite lo asigna con `transaction_total()` antes del flush
    - `list` ordenado por `transaction_date` descendente; `update`; `delete` devuelve el `ItemInvestment` recalculado
    - `get_investment` calcula `real_invested = Σ total_amount(egresos) − Σ total_amount(ingresos)` y el ROI a partir de esa inversión, con `source = "transactions"`; sin transacciones cae a `purchase_price` con `source = "purchase_price"`
    - _Requirements: 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 19.6_
  - [~] 26.3 Agregar `get_transaction_service` en `backend/api/dependencies.py` y crear `backend/api/routes/transactions.py`
    - `GET/POST /collection-items/{id}/transactions`, `PUT /transactions/{id}`, `DELETE /transactions/{id}` (200 con `ItemInvestment`), `GET /collection-items/{id}/investment`
    - Registrar `app.include_router(transactions_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 11.2, 11.6, 11.7, 11.9, 19.6_
  - [~] 26.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_transaction_service.py`
    - Los 10 tipos válidos aceptados y un tipo inválido rechazado
    - `total_amount` con todos los campos, con nulos parciales y con todos nulos
    - Orden descendente por `transaction_date`; inversión real con solo egresos, con egresos e ingresos y sin transacciones (fallback a `purchase_price`)
    - Borrado recalcula inversión y ROI; ROI nulo cuando la inversión resultante es cero
    - _Requirements: 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 19.10_
  - [~] 26.5 Escribir el test de paridad de dialecto y el test `@pytest.mark.postgres` de `total_amount`
    - Test de paridad en `backend/tests/unit/test_services/test_transaction_service.py`: el `total_amount` del camino SQLite coincide con `transaction_total()`
    - `backend/tests/integration/test_postgres/test_transactions_postgres.py` marcado `@pytest.mark.postgres`: el valor lo produce la columna `GENERATED` y coincide con `transaction_total()`
    - _Requirements: 11.4, 19.8_
  - [~] 26.6 Escribir integration tests en `backend/tests/integration/test_routes/test_transactions.py`
    - Códigos 200/201/404/422; `DELETE` devuelve 200 con `ItemInvestment`; `total_amount` presente en la respuesta y ausente del payload aceptado
    - _Requirements: 11.2, 11.3, 11.6, 11.9, 19.9_

- [ ] 27. Bloque 2 - Transacciones frontend (R11)
  - [~] 27.1 Crear `frontend/src/types/transaction.ts` y `frontend/src/services/transactionsApi.ts`
    - `TransactionType`, `Transaction` (con `readonly totalAmount`), `TransactionCreate`, `TransactionUpdate`, `ItemInvestment`
    - `transactionsApi` con `list`, `create`, `update`, `remove`, `investment`
    - _Requirements: 11.6, 11.7, 19.7_
  - [~] 27.2 Crear `frontend/src/hooks/useTransactions.ts` y `frontend/src/hooks/useItemInvestment.ts`
    - Mutar transacciones invalida la inversión del item y las stats
    - _Requirements: 11.6, 11.8, 11.9_
  - [~] 27.3 Crear los componentes en `frontend/src/components/transactions/`
    - `TransactionList.tsx` sobre `Table`, `TransactionForm.tsx`, `InvestmentSummary.tsx`
    - `TransactionForm` muestra `totalAmount` como campo derivado de solo lectura, calculado en vivo en el cliente para dar feedback antes de enviar
    - Integrar en el detalle de collection item de `frontend/src/pages/CollectionDetailPage.tsx`
    - _Requirements: 11.4, 11.6, 11.7_
  - [~] 27.4 Escribir tests de hooks y componentes de transacciones
    - Hooks con MSW; `TransactionList.test.tsx`, `TransactionForm.test.tsx`, `InvestmentSummary.test.tsx`: orden descendente, total derivado en vivo, campo de total no editable, ROI nulo representado sin ambigüedad, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 11.4, 11.6, 11.7, 19.2, 19.3_
  - [~] 27.5 Agregar claves i18n de transacciones en los 5 idiomas
    - Sección `transactions.*` (`title`, `add`, `type.*` con los 10 tipos, `date`, `amount`, `shippingCost`, `taxAmount`, `otherFees`, `totalAmount`, `supplier`, `counterpart`, `invoiceNumber`, `paymentMethod`, `investment.*`, `empty`) y `errors.transaction.invalidType`
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [~] 28. Checkpoint - Price history y transacciones completos
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 29. Bloque 2 - Estadísticas backend (R7)
  - [~] 29.1 Crear `backend/api/schemas/stats.py`
    - `ValuationStats`, `DashboardStats`, `CollectionStatsEntry`, `CategoryStatsEntry`, `TimelineEntry`, `TimelinePeriod` enum (`month`, `quarter`, `year`), `CollectionItemSummary`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [~] 29.2 Crear `backend/api/services/stats_service.py`
    - `get_dashboard`, `get_by_collection`, `get_valuation`, `get_by_category`, `get_timeline(period)`
    - `_invested_expression` usa la inversión real derivada de transacciones cuando existen y `purchase_price` cuando no; los items sin ninguna de las dos se excluyen sin error
    - El ROI se calcula con `roi_percentage()` de `utils/computations.py`, devolviendo `None` cuando la inversión es cero
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 11.8, 19.6_
  - [~] 29.3 Agregar `get_stats_service` en `backend/api/dependencies.py` y crear `backend/api/routes/stats.py`
    - `GET /stats/dashboard`, `/stats/collections`, `/stats/valuation`, `/stats/categories`, `/stats/timeline?period=month|quarter|year` (422 si el período no es válido)
    - Registrar `app.include_router(stats_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 19.6_
  - [~] 29.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_stats_service.py`
    - Base vacía: conteos en cero, ROI nulo, listas vacías
    - Items sin `purchase_price` excluidos de la inversión; items con transacciones usan la inversión real
    - Inversión total cero devuelve ROI nulo, no error de división
    - Timeline agrupado por mes, trimestre y año con el formato de período esperado
    - Categorías con conteo y valor acumulado; colecciones inactivas excluidas del desglose por colección
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 19.10_
  - [~] 29.5 Escribir integration tests en `backend/tests/integration/test_routes/test_stats.py`
    - 200 y formato por endpoint; `period` inválido devuelve 422; base vacía devuelve 200 con estructura completa
    - _Requirements: 7.1, 7.5, 7.7, 19.9_

- [ ] 30. Bloque 2 - Estadísticas frontend (R7)
  - [~] 30.1 Crear `frontend/src/types/stats.ts` y `frontend/src/services/statsApi.ts`
    - `ValuationStats`, `DashboardStats`, `CollectionStatsEntry`, `CategoryStatsEntry`, `TimelineEntry`, `TimelinePeriod`
    - `statsApi` con `dashboard`, `collections`, `valuation`, `categories`, `timeline(period)`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 19.7_
  - [~] 30.2 Crear `frontend/src/hooks/useStats.ts` con un hook por endpoint
    - `useDashboardStats`, `useCollectionStatsList`, `useValuationStats`, `useCategoryStats`, `useTimelineStats`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [~] 30.3 Crear los componentes en `frontend/src/components/stats/`
    - `MetricCard.tsx`, `CollectionStatsTable.tsx`, `CategoryStatsTable.tsx` sobre `Table`
    - `MetricCard` representa el ROI nulo como texto explicativo, no como 0%
    - _Requirements: 7.2, 7.4, 7.7_
  - [~] 30.4 Crear `frontend/src/pages/StatsPage.tsx` con ruta y navegación
    - Cada bloque maneja su propio estado de error con `ErrorMessage` y botón de reintento (`refetch`), sin vaciar la página
    - Estado vacío global cuando no hay colecciones ni items
    - Ruta `/stats` en `frontend/src/App.tsx`; enlace en `Navigation.tsx`
    - _Requirements: 7.8, 7.9, 7.10_
  - [~] 30.5 Escribir tests de hooks, componentes y página de estadísticas
    - Hooks con MSW: éxito, error, loading
    - `MetricCard.test.tsx`, `CollectionStatsTable.test.tsx`, `CategoryStatsTable.test.tsx`, `StatsPage.test.tsx`: estado vacío, error por bloque con reintento sin afectar a los demás, ROI nulo, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 7.8, 7.9, 7.10, 19.2, 19.3_
  - [~] 30.6 Agregar claves i18n de estadísticas en los 5 idiomas
    - Sección `stats.*` (`title`, `totalItems`, `totalValue`, `totalInvested`, `valueGain`, `roi`, `roiUnavailable`, `recentAcquisitions`, `mostValuable`, `highPriorityWishlist`, `byCollection`, `byCategory`, `timeline`, `period.*`, `empty`, `retry`)
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [ ] 31. Bloque 2 - Gráficos accesibles (R16)
  - [~] 31.1 Crear `frontend/src/types/chart.ts` y `frontend/src/components/charts/ChartDataTable.tsx`
    - `ChartSeries` con `key`, `label`, `marker` (`circle | square | triangle | diamond`), `dashArray?`, `points`
    - `ChartDataTable` renderiza sobre `Table` una fila por punto con los valores exactos de las series
    - _Requirements: 16.2, 16.3_
  - [~] 31.2 Crear `frontend/src/components/charts/ChartContainer.tsx`
    - Props `{ title, description, data, isLoading, error, children }`
    - `<figure>` con `<figcaption>`; SVG del gráfico con `aria-hidden="true"`; `ChartDataTable` dentro de un `<details>` con `<summary>` etiquetado y alcanzable por teclado
    - `EmptyState` cuando `data` está vacío, `LoadingSpinner` mientras carga, `ErrorMessage` propio ante error
    - Desactiva `isAnimationActive` cuando `useReducedMotion()` es verdadero
    - _Requirements: 16.2, 16.4, 16.5, 16.7, 18.1_
  - [~] 31.3 Crear los 4 gráficos en `frontend/src/components/charts/`
    - `ValuationOverTimeChart.tsx` (línea), `InvestmentVsValueChart.tsx` (barras agrupadas), `CategoryDistributionChart.tsx` (barras horizontales), `AcquisitionTimelineChart.tsx` (área)
    - Todos consumen `statsApi` mediante los hooks de la Task 30, envueltos en `ChartContainer`, con `marker` distinto por serie
    - Cargar Recharts con `React.lazy` para no penalizar el primer render de las páginas que no lo usan
    - _Requirements: 16.1, 16.3_
  - [~] 31.4 Integrar la sección de gráficos en `frontend/src/pages/StatsPage.tsx`
    - Sección de gráficos debajo de las métricas, con cada gráfico aislado en su propio contenedor de error
    - _Requirements: 16.1, 16.7_
  - [~] 31.5 Escribir tests de gráficos
    - `ChartDataTable.test.tsx`: una fila por punto y valores coincidentes con la entrada
    - `ChartContainer.test.tsx`: `<figure>`/`<figcaption>` presentes, `<summary>` alcanzable por teclado y abre la tabla con Enter, SVG `aria-hidden`, estado vacío, error aislado, animación desactivada con `prefers-reduced-motion`
    - Un `.test.tsx` por gráfico verificando que la tabla equivalente refleja los datos del endpoint mockeado con MSW y que cada serie tiene un `marker` distinto
    - `frontend/tests/accessibility/charts.a11y.test.tsx`: axe sobre la sección completa en tema claro y oscuro
    - _Requirements: 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 19.2, 19.3_
  - [~] 31.6 Agregar claves i18n de gráficos en los 5 idiomas
    - Sección `charts.*` (`valuationOverTime`, `investmentVsValue`, `categoryDistribution`, `acquisitionTimeline`, `viewDataTable`, `series.*`, `noData`, `loadError`, `descriptions.*`)
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [~] 32. Checkpoint - Estadísticas y gráficos completos
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 33. Bloque 2 - Accesorios y stock backend (R12)
  - [~] 33.1 Crear `backend/api/schemas/accessory.py`
    - `AccessoryBase` con `name` (min_length 1), `category`, `subcategory`, `compatible_sub_categories`, `size_specifications`, `quantity_total` (ge 0), `minimum_stock_alert` (ge 0), `reorder_quantity`, `unit_cost`, `currency`, `supplier_id`, `supplier_sku`, `supplier_url`, `notes`
    - `AccessoryResponse` con `quantity_in_use`, `quantity_available` e `is_low_stock` de solo lectura; `LowStockEntry`; `ItemAccessoryCreate` (`accessory_id`, `quantity_used` ge 1, `notes`); `ItemAccessoryResponse`
    - _Requirements: 12.1, 12.2, 12.3, 12.5, 12.10_
  - [~] 33.2 Crear `backend/api/services/accessory_service.py`
    - CRUD `list` (filtro `category`, paginación), `get`, `create`, `update`, `delete` (lanza `DuplicateError` → 409 si tiene asignaciones vigentes)
    - `list_low_stock` devuelve los accesorios con `quantity_available <= minimum_stock_alert` y la `reorder_quantity` sugerida
    - `assign` valida stock disponible (`ValidationError` si excede) y unicidad (`DuplicateError` si ya está asignado) **antes** del insert, en ambos dialectos; ajusta `quantity_in_use` solo en SQLite (en PostgreSQL lo hace el trigger)
    - `unassign` elimina el registro y decrementa `quantity_in_use` en SQLite
    - `_resolve_available` lee la columna `GENERATED` en PostgreSQL y usa `available_stock()` en SQLite
    - _Requirements: 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 19.6_
  - [~] 33.3 Agregar `get_accessory_service` en `backend/api/dependencies.py` y crear `backend/api/routes/accessories.py`
    - `GET/POST /accessories`, `GET/PUT/DELETE /accessories/{id}`, `GET /accessories/low-stock`, `GET/POST /collection-items/{id}/accessories`, `DELETE /item-accessories/{id}`
    - Registrar `app.include_router(accessories_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 12.1, 12.5, 12.6, 12.10, 19.6_
  - [~] 33.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_accessory_service.py`
    - Creación válida; `name` vacío y `quantity_total` negativo rechazados; campos opcionales persistidos
    - `assign` incrementa `quantity_in_use` y reduce `quantity_available`; `unassign` los revierte
    - Asignación duplicada al mismo item rechazada; asignación por encima del disponible rechazada dejando `quantity_in_use` intacto
    - `list_low_stock` con stock por debajo, igual y por encima del umbral
    - `delete` con asignaciones vigentes rechazado
    - _Requirements: 12.1, 12.2, 12.3, 12.5, 12.6, 12.7, 12.8, 12.10, 19.10_
  - [~] 33.5 Escribir el test `@pytest.mark.postgres` del trigger y la columna GENERATED
    - `backend/tests/integration/test_postgres/test_accessories_postgres.py`: `update_accessory_stock_trigger` ajusta `quantity_in_use` sin intervención del service y `quantity_available` coincide con `available_stock()`
    - _Requirements: 12.9, 19.8_
  - [~] 33.6 Escribir integration tests en `backend/tests/integration/test_routes/test_accessories.py`
    - Códigos 200/201/204/404/409/422; asignación sin stock devuelve 422; asignación duplicada devuelve 409; borrado con asignaciones devuelve 409
    - _Requirements: 12.1, 12.2, 12.7, 12.8, 12.10, 19.9_
  - [~] 33.7 Escribir property test del stock disponible
    - **Property 2: El stock disponible nunca es negativo y siempre es total menos en uso**
    - **Validates: Requirements 12.8, 12.9**
    - Usar `hypothesis` (mínimo 100 iteraciones) con secuencias arbitrarias de asignaciones y desasignaciones, verificando la invariante tras cada operación y que las asignaciones inválidas no modifican `quantity_in_use`
    - Archivo: `backend/tests/unit/test_services/test_accessory_service_properties.py`

- [ ] 34. Bloque 2 - Accesorios y stock frontend (R12)
  - [~] 34.1 Crear `frontend/src/types/accessory.ts` y `frontend/src/services/accessoriesApi.ts`
    - `Accessory` (con `readonly quantityInUse`, `quantityAvailable`, `isLowStock`), `AccessoryCreate`, `AccessoryUpdate`, `LowStockEntry`, `ItemAccessoryAssignment`
    - `accessoriesApi` con `list`, `get`, `create`, `update`, `remove`, `lowStock`, `listAssignments`, `assign`, `unassign`
    - _Requirements: 12.1, 12.5, 12.10, 19.7_
  - [~] 34.2 Crear `frontend/src/hooks/useAccessories.ts` y `frontend/src/hooks/useItemAccessories.ts`
    - Asignar o desasignar invalida el listado de accesorios y el de stock bajo
    - _Requirements: 12.5, 12.6, 12.10_
  - [~] 34.3 Crear los componentes en `frontend/src/components/accessories/`
    - `AccessoryCard.tsx`, `AccessoryForm.tsx`, `LowStockList.tsx`, `StockBadge.tsx`, `AssignAccessoryDialog.tsx`
    - `StockBadge` sobre `Badge`: marca el stock bajo con color, texto explícito y `aria-label`
    - `AssignAccessoryDialog` valida localmente la cantidad contra el disponible antes de enviar
    - _Requirements: 12.5, 12.8, 12.11_
  - [~] 34.4 Crear `frontend/src/pages/AccessoriesPage.tsx` con ruta y navegación
    - Listado con total, en uso y disponible, sección de stock bajo, estado vacío
    - Ruta `/accessories` en `frontend/src/App.tsx`; enlace en `Navigation.tsx`
    - Integrar `AssignAccessoryDialog` en el detalle de collection item de `frontend/src/pages/CollectionDetailPage.tsx`
    - _Requirements: 12.5, 12.11_
  - [~] 34.5 Escribir tests de hooks, componentes y página de accesorios
    - Hooks con MSW; un `.test.tsx` por componente y por página: stock bajo destacado con texto además de color, error de stock insuficiente, focus trap del diálogo, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 12.8, 12.11, 18.6, 19.2, 19.3_
  - [~] 34.6 Agregar claves i18n de accesorios en los 5 idiomas
    - Sección `accessories.*` (`title`, `add`, `name`, `category`, `quantityTotal`, `quantityInUse`, `quantityAvailable`, `minimumStockAlert`, `reorderQuantity`, `unitCost`, `supplier`, `lowStock`, `lowStockTitle`, `suggestedReorder`, `assign`, `unassign`, `quantityUsed`, `empty`)
    - `errors.accessory.*` (`invalidStock`, `insufficientStock`, `alreadyAssigned`, `hasAssignments`)
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [ ] 35. Bloque 2 - Exportación backend (R13)
  - [~] 35.1 Crear `backend/api/schemas/export.py`
    - `ExportEnvelope` (`schema_version`, `entity_type`, `exported_at`, `source`), `CollectionExport`, `CollectionItemExport` (con `components`), `CatalogExport`, `WishlistExport`
    - _Requirements: 13.1, 13.2, 13.6_
  - [~] 35.2 Crear `backend/api/services/export_service.py`
    - `SCHEMA_VERSION = "1.0"`; `export_collection` (colección, items, componentes y catalog items referenciados), `export_catalog_json`, `export_catalog_csv`, `export_wishlist`
    - El header CSV se deriva de `CsvImportService.REQUIRED_COLUMNS | OPTIONAL_COLUMNS` en orden estable, nunca escrito a mano
    - `NotFoundError` para entidades inexistentes
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.6, 19.6_
  - [~] 35.3 Agregar `get_export_service` en `backend/api/dependencies.py` y crear `backend/api/routes/export.py`
    - `GET /export/collections/{id}`, `GET /export/catalogs/{id}?format=json|csv`, `GET /export/wishlist`
    - Encabezados `Content-Type` y `Content-Disposition: attachment` con nombre de archivo; 404 para entidad inexistente, 422 para formato no soportado
    - Registrar `app.include_router(export_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 13.2, 13.3, 13.4, 13.5, 19.6_
  - [~] 35.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_export_service.py`
    - Export de colección con items y componentes; colección vacía; catálogo con y sin items
    - El header del CSV coincide exactamente con las constantes del importador
    - Entidad inexistente lanza `NotFoundError`
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 19.10_
  - [~] 35.5 Escribir integration tests en `backend/tests/integration/test_routes/test_export.py`
    - 200 con `Content-Type` y `Content-Disposition` correctos por formato; 404 y 422
    - _Requirements: 13.2, 13.3, 13.4, 13.5, 19.9_

- [ ] 36. Bloque 2 - Importación JSON backend (R14)
  - [~] 36.1 Crear `backend/api/schemas/import_data.py` y ampliar `backend/api/schemas/csv_import.py`
    - `ImportEntityChange` (`entity_type`, `identifier`, `action`, `reason`), `ImportPreview` (`schema_version`, `to_create`, `to_update`, `to_skip`, `changes`, `errors`)
    - Ampliar `BatchImportResult` con `updated_count` y `skipped_count` con default 0, sin romper al cliente CSV existente
    - _Requirements: 14.3, 14.4, 14.5, 14.7_
  - [~] 36.2 Crear `backend/api/services/json_import_service.py`
    - `MAX_FILE_SIZE = 10 MB`, `SUPPORTED_VERSIONS = {"1.0"}`
    - `_parse_envelope` valida JSON, estructura y `schema_version`; `_plan` clasifica cada entidad en create / update / skip y acumula errores por entidad con identificador y motivo
    - `_resolve_existing` busca por clave natural según la tabla del design: `Catalog(sub_category_id, name)`, `CatalogItem(catalog_id, title, region, variant)` con prioridad a `sku`/`upc` no vacío, `Collection(name)`, `CollectionItem(collection_id, catalog_item_id, variant_description, certification_number)`, `WishlistItem(collection_id, catalog_item_id)`, `Supplier(name, type)`, `ItemComponent(collection_item_id, component_name)`; los UUID del documento se ignoran para el matching
    - `preview` corre `_plan` dentro de una transacción que se descarta, sin `commit`; `execute` usa el mismo `_plan` y devuelve `BatchImportResult`
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 19.6_
  - [~] 36.3 Agregar `get_json_import_service` en `backend/api/dependencies.py` y crear `backend/api/routes/import_data.py`
    - `POST /import/preview` y `POST /import/execute` con `UploadFile`; 413 si excede 10 MB, 422 si el JSON o la estructura son inválidos
    - Registrar `app.include_router(import_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 14.1, 14.2, 14.3, 19.6_
  - [~] 36.4 Escribir unit tests del service en `backend/tests/unit/test_services/test_json_import_service.py`
    - JSON inválido y estructura no reconocida rechazados; `schema_version` no soportada rechazada; archivo mayor a 10 MB rechazado
    - `preview` no escribe nada en la base (conteos idénticos antes y después)
    - Entidades coincidentes por clave natural se actualizan en lugar de duplicarse
    - Archivo con entidades válidas e inválidas persiste las válidas y reporta ambas cantidades
    - `preview` y `execute` producen los mismos conteos para el mismo archivo
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.6, 14.7, 19.10_
  - [~] 36.5 Escribir integration tests en `backend/tests/integration/test_routes/test_import.py`
    - Códigos 200/413/422; `preview` seguido de no llamar a `execute` deja la base intacta
    - _Requirements: 14.1, 14.2, 14.3, 14.10, 19.9_
  - [~] 36.6 Escribir property test de idempotencia del import
    - **Property 3: La importación es idempotente**
    - **Validates: Requirements 14.6, 14.8**
    - Usar `hypothesis` (mínimo 100 iteraciones) generando documentos de exportación válidos e importándolos dos veces; comparar el conteo por tipo de entidad
    - Archivo: `backend/tests/unit/test_services/test_json_import_service_properties.py`
  - [~] 36.7 Escribir property test del round-trip export → import
    - **Property 4: El round-trip export → import preserva las entidades**
    - **Validates: Requirements 13.6, 14.5**
    - Usar `hypothesis` (mínimo 100 iteraciones) generando colecciones con items y componentes, exportando e importando en una base vacía y comparando los campos exportados
    - Archivo: `backend/tests/unit/test_services/test_transfer_roundtrip_properties.py`

- [ ] 37. Bloque 2 - Export e import frontend (R13, R14)
  - [~] 37.1 Crear `frontend/src/types/transfer.ts`, `frontend/src/services/exportApi.ts` y `frontend/src/services/importApi.ts`
    - `ImportPreview`, `ImportEntityChange`, `BatchImportResult` ampliado con `updatedCount` y `skippedCount`, `ExportFormat`
    - `exportApi` usa `fetch` directo más `URL.createObjectURL` para disparar la descarga (no `fetchApi`, que parsea JSON); `importApi` con `preview(file)` y `execute(file)` sobre `FormData`
    - _Requirements: 13.5, 13.7, 14.3, 14.5, 19.7_
  - [~] 37.2 Crear `frontend/src/hooks/useExport.ts` y `frontend/src/hooks/useJsonImport.ts`
    - `useExport` expone estado de progreso y error; `useJsonImport` mantiene el paso del asistente y el resultado, e invalida todas las query keys afectadas tras `execute`
    - _Requirements: 13.7, 13.8, 14.9_
  - [~] 37.3 Crear los componentes en `frontend/src/components/transfer/`
    - `ExportPanel.tsx` (selección de entidad y formato, indicador de progreso, error con reintento)
    - `ImportWizard.tsx` con 4 pasos (subir → vista previa → confirmar → reporte), `ImportPreviewTable.tsx` sobre `Table`, `ImportReport.tsx`
    - Cancelar en la vista previa simplemente no llama a `execute`; el asistente lo indica explícitamente
    - _Requirements: 13.7, 13.8, 14.9, 14.10_
  - [~] 37.4 Crear `frontend/src/pages/ExportPage.tsx` y `frontend/src/pages/ImportPage.tsx` con rutas y navegación
    - Rutas `/export` e `/import` en `frontend/src/App.tsx`; enlaces en `Navigation.tsx`
    - _Requirements: 13.7, 14.9_
  - [~] 37.5 Escribir tests de hooks, componentes y páginas de transferencia
    - Hooks con MSW: descarga exitosa, error con reintento, preview seguido de execute
    - `ExportPanel.test.tsx`, `ImportWizard.test.tsx`, `ImportPreviewTable.test.tsx`, `ImportReport.test.tsx`, `ExportPage.test.tsx`, `ImportPage.test.tsx`: avance y retroceso entre pasos, cancelación sin llamar a `execute`, reporte con errores por entidad, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 13.7, 13.8, 14.9, 14.10, 19.2, 19.3_
  - [~] 37.6 Agregar claves i18n de export e import en los 5 idiomas
    - Sección `export.*` (`title`, `entity`, `format`, `download`, `inProgress`, `retry`) e `import.*` (`title`, `steps.*`, `selectFile`, `preview`, `toCreate`, `toUpdate`, `toSkip`, `confirm`, `cancel`, `report`, `partialErrors`, `empty`)
    - `errors.export.*` (`notFound`, `invalidFormat`) y `errors.import.*` (`invalidStructure`, `unsupportedVersion`, `fileTooLarge`)
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [~] 38. Checkpoint - Accesorios, export e import completos
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 39. Bloque 2 - Backups backend (R15)
  - [~] 39.1 Crear `backend/api/schemas/backup.py`
    - `BackupInfo`, `BackupConfig` (`frequency` literal, `retention_count` ge 1 le 365, `next_run_at`, `last_run_at`, `last_run_status`), `BackupConfigUpdate`, `RestoreResult`, `BackupVerification`
    - _Requirements: 15.2, 15.3, 15.6, 15.8, 15.9_
  - [~] 39.2 Agregar `ToolUnavailableError` y su handler
    - `ToolUnavailableError(DomainError)` en `backend/core/exceptions.py`
    - `service_unavailable_handler` (→ 503) registrado en `backend/core/exception_handlers.py` y en `backend/main.py`
    - _Requirements: 15.1_
  - [~] 39.3 Crear `backend/api/services/backup_service.py`
    - `create(trigger)` genera `hoard-backup-{YYYYMMDD-HHMMSS}-{shortid}.tar.gz` en `BACKUP_DIR` con `manifest.json`, `database.dump` (`pg_dump -Fc` vía `subprocess`), `uploads/` (copia de `UPLOAD_DIR`) y `config.json` con ajustes no sensibles (nunca `SECRET_KEY` ni `DATABASE_URL`)
    - `shutil.which("pg_dump")` al inicio de `create`; si falta lanza `ToolUnavailableError` nombrando el binario
    - `list` ordenado por fecha descendente, `get_path`, `delete`, `apply_retention` (solo tras un backup exitoso)
    - `_verify` en tres pasos antes de tocar datos: tar legible, `manifest.json` válido con `schema_version` soportada, SHA-256 de `database.dump` coincidente; validación de path traversal en los miembros del tar; extracción a directorio temporal
    - `restore` ejecuta `pg_restore --clean --if-exists` solo si `_verify` pasa; devuelve `RestoreResult`
    - `get_config` / `update_config` persisten en `app_settings` bajo la clave `backups.config`
    - `try_acquire_backup_lock` / `release_backup_lock` con `pg_try_advisory_lock(hashtext('hoard.backup'))`
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10, 15.11, 19.6_
  - [~] 39.4 Crear `backend/core/scheduler.py` y arrancarlo desde el `lifespan` de `backend/main.py`
    - `AsyncIOScheduler` de APScheduler; job que toma el advisory lock antes de ejecutar y sale sin hacer nada si no lo obtiene
    - Reprograma según la frecuencia persistida y actualiza `last_run_at`, `last_run_status` y `next_run_at`
    - Un fallo registra el error y conserva los backups existentes sin aplicar retención
    - _Requirements: 15.8, 15.9, 15.10, 15.11_
  - [~] 39.5 Agregar `get_backup_service` en `backend/api/dependencies.py` y crear `backend/api/routes/backups.py`
    - `GET/POST /backups` (201, 503), `GET /backups/{id}/download` (200, 404), `POST /backups/{id}/restore` (200, 404, 422), `DELETE /backups/{id}` (204, 404), `GET/PUT /backups/config` (200, 422)
    - Registrar `app.include_router(backups_router, prefix="/api")` en `backend/main.py`
    - _Requirements: 15.1, 15.3, 15.4, 15.5, 15.6, 15.8, 15.9, 19.6_
  - [~] 39.6 Escribir unit tests en `backend/tests/unit/test_services/test_backup_service.py` y `backend/tests/unit/test_core/test_scheduler.py`
    - `create` con `pg_dump` mockeado produce el tar con los 4 miembros y el manifest correcto; sin `pg_dump` lanza `ToolUnavailableError`
    - `_verify` rechaza tar corrupto, manifest ausente, `schema_version` no soportada, checksum incorrecto y miembros con path traversal
    - `restore` con archivo inválido no modifica datos; con archivo válido devuelve `RestoreResult`
    - `get_config`/`update_config` persisten en `app_settings`; frecuencia inválida y retención fuera de rango rechazadas
    - Scheduler: sin lock no ejecuta; fallo registra `last_run_status = "failed"` y no aplica retención
    - _Requirements: 15.1, 15.2, 15.5, 15.6, 15.7, 15.8, 15.9, 15.11, 19.10_
  - [~] 39.7 Escribir integration tests en `backend/tests/integration/test_routes/test_backups.py`
    - Códigos 200/201/204/404/422/503; `download` devuelve el archivo con `Content-Disposition`; `restore` de backup inexistente devuelve 404 y de backup corrupto 422
    - _Requirements: 15.4, 15.5, 15.6, 15.7, 19.9_
  - [~] 39.8 Escribir property test de la rotación de backups
    - **Property 7: La rotación de backups conserva exactamente min(N, creados)**
    - **Validates: Requirements 15.10**
    - Usar `hypothesis` (mínimo 100 iteraciones) con retención N ≥ 1 y K backups creados secuencialmente; verificar la cantidad restante y que son los más recientes
    - Archivo: `backend/tests/unit/test_services/test_backup_service_properties.py`

- [ ] 40. Bloque 2 - Backups frontend (R15)
  - [~] 40.1 Crear `frontend/src/types/backup.ts` y `frontend/src/services/backupsApi.ts`
    - `BackupInfo`, `BackupConfig`, `BackupConfigUpdate`, `RestoreResult`, `BackupFrequency`
    - `backupsApi` con `list`, `create`, `download`, `restore`, `remove`, `getConfig`, `updateConfig`
    - _Requirements: 15.3, 15.4, 15.6, 15.9, 19.7_
  - [~] 40.2 Crear `frontend/src/hooks/useBackups.ts` y `frontend/src/hooks/useBackupConfig.ts`
    - Crear o borrar invalida el listado; restaurar invalida todas las query keys de datos
    - _Requirements: 15.3, 15.6, 15.9_
  - [~] 40.3 Crear los componentes en `frontend/src/components/backups/`
    - `BackupList.tsx` sobre `Table` con acciones de descarga, restauración y borrado
    - `BackupConfigForm.tsx` con frecuencia (daily/weekly/monthly), retención y la próxima ejecución programada
    - `RestoreConfirmDialog.tsx`: exige escribir la palabra de confirmación para habilitar el botón, dado que la operación es destructiva e irreversible
    - _Requirements: 15.3, 15.4, 15.6, 15.8, 15.9, 15.12_
  - [~] 40.4 Crear `frontend/src/pages/BackupsPage.tsx` con ruta y navegación
    - Ruta `/settings/backups` en `frontend/src/App.tsx`; enlace en `Navigation.tsx`
    - Mensaje explicativo dedicado ante 503 (falta el cliente de PostgreSQL)
    - _Requirements: 15.12_
  - [~] 40.5 Escribir tests de hooks, componentes y página de backups
    - Hooks con MSW incluyendo el caso 503
    - `BackupList.test.tsx`, `BackupConfigForm.test.tsx`, `RestoreConfirmDialog.test.tsx`, `BackupsPage.test.tsx`: botón de restaurar deshabilitado hasta escribir la confirmación, focus trap y Escape en el diálogo, estado vacío, error 503, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 15.12, 18.6, 19.2, 19.3_
  - [~] 40.6 Agregar claves i18n de backups en los 5 idiomas
    - Sección `backups.*` (`title`, `create`, `download`, `restore`, `delete`, `createdAt`, `size`, `trigger.*`, `contents.*`, `config.*`, `frequency.*`, `retention`, `nextRun`, `lastRun`, `lastRunFailed`, `restoreWarning`, `restoreConfirmWord`, `empty`)
    - `errors.backup.*` (`notFound`, `corrupted`, `toolUnavailable`, `invalidFrequency`, `invalidRetention`)
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1_

- [~] 41. Checkpoint - Backups y scheduler completos
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 42. Bloque 2 - PWA: manifest y service worker (R17)
  - [~] 42.1 Configurar `vite-plugin-pwa` en `frontend/vite.config.ts`
    - `registerType: "prompt"`, `generateSW` con manifest ("H.O.A.R.D.", short_name "HOARD", iconos 192/512 más maskable, `theme_color` alineado al token `accent`, `display: "standalone"`)
    - `runtimeCaching`: precache + CacheFirst del app shell, StaleWhileRevalidate para `/locales/*/translation.json`, CacheFirst para `/uploads/*` (máx. 200 entradas, 30 días), NetworkFirst con timeout 3 s para `GET /api/collections`, `/api/collection-items`, `/api/stats/*` y `/api/search/*`; sin cache para POST/PUT/DELETE
    - _Requirements: 17.1, 17.2, 17.3, 17.4_
  - [~] 42.2 Agregar los iconos de la PWA y el registro del service worker
    - Iconos en `frontend/public/` (192, 512 y maskable)
    - Registro con `virtual:pwa-register/react` y aviso de actualización en `frontend/src/main.tsx`, usando `workbox-window`
    - _Requirements: 17.1, 17.2_
  - [~] 42.3 Escribir el test de configuración del plugin en `frontend/tests/pwa/viteConfig.test.ts`
    - Valida la forma del objeto de configuración: manifest presente con los campos requeridos y una estrategia declarada por patrón de URL. No testea Workbox en sí
    - _Requirements: 17.1, 17.2_

- [ ] 43. Bloque 2 - Cola de sincronización offline (R17)
  - [~] 43.1 Crear `frontend/src/offline/types.ts` y `frontend/src/offline/queue.ts`
    - `QueuedStatus`, `QueuedOperation` (`id` autoincremental que define el orden FIFO, `entityUpdatedAt` para detectar conflicto, `attempts`, `error`), `NewQueuedOperation`
    - `enqueue`, `listByStatus`, `markApplied`, `markConflict`, `markFailed`, `counts` sobre IndexedDB con `idb`
    - _Requirements: 17.6, 17.9, 17.10_
  - [~] 43.2 Crear `frontend/src/offline/sync.ts`
    - `drainQueue()` procesa las `pending` estrictamente por `id` ascendente, protegido por un flag de sincronización en curso para que dos disparos no dupliquen envíos
    - Antes de `PUT`/`DELETE` hace un `GET` de la entidad: si el `updatedAt` del servidor es posterior, marca `conflict` y no envía
    - 4xx distinto de 409 marca `failed` con el detalle y no reintenta; los errores de red incrementan `attempts` (máximo 5) y detienen el drenaje dejando el resto `pending`
    - Al aplicar o marcar conflicto invalida las query keys del `entityType` afectado
    - _Requirements: 17.7, 17.8, 17.9_
  - [~] 43.3 Crear el persister de React Query sobre IndexedDB
    - `frontend/src/offline/queryPersister.ts` con un persister propio sobre `idb`; conectar `persistQueryClient` en `frontend/src/main.tsx`
    - _Requirements: 17.3, 17.4_
  - [~] 43.4 Crear `frontend/src/hooks/useOnlineStatus.ts` y `frontend/src/hooks/useSyncQueue.ts`
    - `useOnlineStatus()` sobre los eventos `online`/`offline`; `useSyncQueue()` expone `counts`, `conflicts`, `failed`, `isSyncing`, `retry(id)`, `resolveConflict(id, keep)`
    - Disparar `drainQueue` al recuperar la conexión
    - _Requirements: 17.5, 17.7, 17.8, 17.9, 17.10_
  - [~] 43.5 Integrar el encolado en las mutaciones sin conexión
    - Envolver `fetchApi` (o su capa de mutación) en `frontend/src/services/` para que, sin conexión, las mutaciones se encolen, se aplique la actualización optimista en la cache de React Query y se confirme al usuario que quedó pendiente
    - _Requirements: 17.6_
  - [~] 43.6 Crear los componentes en `frontend/src/components/offline/`
    - `OfflineBanner.tsx` con `role="status"` y `aria-live="polite"`; `SyncStatusPanel.tsx` con pendientes, aplicadas, en conflicto y fallidas; `ConflictResolver.tsx` que muestra el diff y deja elegir entre descartar el cambio local o reaplicarlo
    - Renderizar `OfflineBanner` y el acceso a `SyncStatusPanel` en `frontend/src/components/layout/AppLayout.tsx`
    - _Requirements: 17.5, 17.8, 17.9, 17.10_
  - [~] 43.7 Escribir tests de la cola y la sincronización
    - `frontend/src/offline/queue.test.ts` con `fake-indexeddb`: `enqueue`, `listByStatus`, transiciones de estado, conteos
    - `frontend/src/offline/sync.test.ts` con MSW: cola vacía; todas aplicadas; error de red a mitad deja el resto `pending`; 422 marca `failed` sin reintento; `updatedAt` más nuevo en el servidor marca `conflict` sin enviar; dos `drainQueue` simultáneos no duplican envíos
    - `frontend/src/hooks/useOnlineStatus.test.ts` disparando los eventos de `window`; `useSyncQueue.test.ts` con MSW
    - _Requirements: 17.6, 17.7, 17.8, 17.9, 17.10_
  - [~] 43.8 Escribir tests de los componentes offline
    - `OfflineBanner.test.tsx`, `SyncStatusPanel.test.tsx`, `ConflictResolver.test.tsx`: anuncio del modo sin conexión, conteos, resolución de conflicto, teclado, ARIA y test axe-core obligatorio
    - _Requirements: 17.5, 17.8, 17.10, 19.2, 19.3_
  - [~] 43.9 Escribir property test del orden FIFO de la cola
    - **Property 9: La cola offline preserva el orden FIFO de las operaciones aplicadas**
    - **Validates: Requirements 17.6, 17.7**
    - Usar `fast-check` (mínimo 100 iteraciones) con secuencias arbitrarias de operaciones encoladas; verificar el orden de envío y que solo se vacían las aceptadas
    - Archivo: `frontend/src/offline/queue.property.test.ts`
  - [~] 43.10 Escribir el E2E de offline y agregar claves i18n en los 5 idiomas
    - `frontend/tests/e2e/offline.spec.ts` con `context.setOffline(true)`: páginas cacheadas navegables, banner visible, creación encolada y, al volver la conexión, operación aplicada y cola vacía
    - Sección `offline.*` (`banner`, `pendingOperation`, `sync.*`, `conflict.*`, `failed.*`, `retry`, `discard`) en `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 17.3, 17.5, 17.6, 17.7, 19.1_

- [~] 44. Checkpoint - PWA y modo sin conexión completos
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 45. Bloque 2 - Accesibilidad avanzada y auditoría (R18)
  - [~] 45.1 Reforzar `frontend/src/components/ui/Modal.tsx`
    - `FocusScope` de react-aria con `contain` y `restoreFocus`, cierre con Escape y retorno del foco al elemento que abrió el diálogo
    - Actualizar `frontend/src/components/ui/Modal.test.tsx` con focus trap, Escape y retorno del foco
    - _Requirements: 18.6_
  - [~] 45.2 Ajustar el layout para zoom al 200% en `frontend/src/components/layout/AppLayout.tsx` y `frontend/src/index.css`
    - Contenedores con `max-width` en `rem` y sin anchos fijos en px; tablas envueltas en un contenedor con scroll horizontal propio para evitar el scroll bidimensional de la página
    - _Requirements: 18.4_
  - [~] 45.3 Aplicar `useReducedMotion` y `useAnnouncement` en los flujos ya construidos
    - Sustituir los mensajes de éxito y error dispersos por anuncios vía `LiveRegion` (`assertive` para errores, `polite` para éxitos) en los formularios y páginas de las Tasks 9 a 43
    - Desactivar animaciones y transiciones no esenciales cuando `useReducedMotion()` es verdadero
    - _Requirements: 18.1, 18.2_
  - [~] 45.4 Crear la suite de auditoría por página en `frontend/tests/accessibility/pages.a11y.test.tsx`
    - axe-core sobre todas las páginas (las 6 de Fase 1 más las 9 nuevas) en tema claro y oscuro, exigiendo cero violaciones WCAG 2.1 AA
    - _Requirements: 18.7, 8.6, 16.6_
  - [~] 45.5 Crear el E2E de teclado en `frontend/tests/e2e/a11y-keyboard.spec.ts`
    - Recorrido completo por teclado, skip link operativo, focus trap en modales, zoom al 200% sin pérdida de funcionalidad ni scroll horizontal de página
    - _Requirements: 18.4, 18.5, 18.6_
  - [~] 45.6 Crear `docs/ACCESSIBILITY.md` y enlazarlo desde el README
    - Documentar el alcance de la auditoría automatizada, los componentes y páginas cubiertos, y la declaración explícita de que la validación completa de conformidad WCAG 2.1 AA requiere pruebas manuales con tecnologías asistivas y revisión experta, que la auditoría automatizada no sustituye
    - Agregar el enlace en `README.md`
    - _Requirements: 18.8_

- [ ] 46. Bloque 2 - Cierre de estándares transversales (R19)
  - [~] 46.1 Verificar y cerrar la paridad i18n de los 5 idiomas
    - Ejecutar `npm run lint:i18n` y completar cualquier clave faltante o sobrante acumulada en las Tasks 24 a 45
    - Archivos: `frontend/public/locales/{es,en,pt,fr,de}/translation.json`
    - _Requirements: 19.1, 9.2_
  - [~] 46.2 Verificar el modo estricto de TypeScript sin `any`
    - `npx tsc --noEmit` limpio; eliminar cualquier `any` introducido, usando `unknown` con narrowing donde el backend devuelve JSON libre
    - Archivos: `frontend/tsconfig.json` y los módulos señalados por el compilador
    - _Requirements: 19.7_
  - [~] 46.3 Auditar la separación de capas del backend
    - Revisar `backend/api/routes/*.py`: ninguna regla de negocio en las routes; toda validación de dominio en los services y toda traducción de error vía exception handlers
    - Mover a `services/` cualquier lógica que haya quedado en routes
    - _Requirements: 19.6_
  - [~] 46.4 Completar los E2E faltantes en `frontend/tests/e2e/`
    - `suppliers.spec.ts`, `wishlist.spec.ts`, `components.spec.ts`, `search.spec.ts`, `stats.spec.ts`, `theme.spec.ts`, `i18n.spec.ts`, `accessories.spec.ts`, `transfer.spec.ts` (export → import round-trip), `backups.spec.ts`, `charts.spec.ts`
    - _Requirements: 19.9_

- [~] 47. Checkpoint - Cierre del Bloque 2 (Fase 3 Advanced) y subida de coverage a 85%
  - Elevar `fail_under = 85` en `backend/pyproject.toml` y `coverage.thresholds.lines = 85` en `frontend/vitest.config.ts`
  - Ensure all tests pass, ask the user if questions arise.

- [~] 48. Final checkpoint - Suite completa, auditoría y umbrales verificados
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- **División en bloques.** El Bloque 0 (Tasks 1-7) son cimientos y no entregan funcionalidad de usuario por sí solos. El Bloque 1 (Tasks 8-23, Fase 2 Core) es entregable y usable de forma independiente: cierra suppliers, wishlist, sightings, componentes, colecciones multi-category, búsqueda, dark mode y los 5 idiomas, con coverage >80%. El Bloque 2 (Tasks 24-48, Fase 3 Advanced) suma price history, transacciones, estadísticas, gráficos, accesorios, export, import, backups, PWA/offline y la auditoría final, con coverage >85%. Se puede detener el trabajo al terminar la Task 23 y tener un producto coherente.
- **Orden de i18n.** Los idiomas pt, fr y de se crean en la Task 22. Las tareas anteriores agregan claves solo a `es` y `en`; la Task 22.2 porta el conjunto completo acumulado a los tres idiomas nuevos; de la Task 24 en adelante toda clave se agrega a los 5 archivos. La Task 46.1 verifica la paridad final con `npm run lint:i18n`.
- **La suite `@pytest.mark.postgres` es opt-in.** Está desactivada por defecto (`addopts = "-m 'not postgres'"`) y se habilita definiendo `HOARD_TEST_DATABASE_URL` contra un PostgreSQL real. Si no se corre, quedan **sin verificación real**: los pesos A/B/C del `search_vector`, la similitud de `pg_trgm`, las columnas `GENERATED` (`item_transactions.total_amount`, `accessories_stock.quantity_available`), el trigger `update_accessory_stock_trigger`, las 4 vistas (`v_collection_items_full`, `v_collection_items_by_category`, `v_wishlist_with_avg_price`, `v_collection_stats`) y el `upgrade`/`downgrade` de la migración `002_app_settings.py`. La suite SQLite verifica el camino degradado y la paridad contra `utils/computations.py`, no el comportamiento de PostgreSQL.
- **La restauración de backups es destructiva.** `POST /backups/{id}/restore` ejecuta `pg_restore --clean --if-exists` y sobrescribe la base de datos, las imágenes y la configuración actuales. La verificación en tres pasos (tar legible, manifest válido, checksum del dump) corre **antes** de tocar cualquier dato, y el diálogo del frontend exige escribir la palabra de confirmación. Cualquier prueba manual de restauración debe hacerse sobre una instancia desechable.
- **`app_settings` es la única tabla nueva de todo el spec.** Las 17 tablas restantes ya existen en `001_initial_schema.py`; los 4 primeros modelos SQLAlchemy nuevos solo agregan el mapeo ORM. La migración `002_app_settings.py` es la única que altera el schema.
- Cada sub-task nombra los archivos concretos a crear o modificar y referencia los requirements que cubre, para trazabilidad.
- Las sub-tasks marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido; son los property tests de las 12 propiedades de corrección del design.
- Los tests unitarios, de integración y de accesibilidad **no** están marcados como opcionales: son obligatorios en este proyecto.
- Todo componente React nuevo lleva test axe-core. Todo service nuevo lleva unit tests de casos válidos, límite y error. Todo endpoint nuevo lleva integration tests de códigos de estado, formato y errores.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "4.1", "5.1", "5.2", "6.1", "6.2", "6.3", "6.4"] },
    { "id": 2, "tasks": ["2.5", "3.1", "3.2", "4.2", "5.3", "5.4", "5.5", "6.5", "6.6"] },
    { "id": 3, "tasks": ["3.3", "4.3", "6.7", "6.8", "8.1"] },
    { "id": 4, "tasks": ["8.2", "9.1"] },
    { "id": 5, "tasks": ["8.3", "9.2"] },
    { "id": 6, "tasks": ["8.4", "9.3", "9.6"] },
    { "id": 7, "tasks": ["8.5", "8.6", "9.4"] },
    { "id": 8, "tasks": ["9.5", "10.1"] },
    { "id": 9, "tasks": ["10.2", "11.1"] },
    { "id": 10, "tasks": ["10.3", "11.2"] },
    { "id": 11, "tasks": ["10.4", "11.3", "11.6"] },
    { "id": 12, "tasks": ["10.5", "10.6", "10.7", "10.8", "11.4"] },
    { "id": 13, "tasks": ["11.5", "13.1"] },
    { "id": 14, "tasks": ["13.2", "14.1"] },
    { "id": 15, "tasks": ["13.3", "14.2"] },
    { "id": 16, "tasks": ["13.4", "14.3", "14.5"] },
    { "id": 17, "tasks": ["13.5", "13.6", "13.7", "14.4"] },
    { "id": 18, "tasks": ["15.1", "16.1"] },
    { "id": 19, "tasks": ["15.2", "15.3", "16.2"] },
    { "id": 20, "tasks": ["15.4", "16.3", "16.4", "16.7"] },
    { "id": 21, "tasks": ["15.5", "15.6", "16.5"] },
    { "id": 22, "tasks": ["16.6", "18.1"] },
    { "id": 23, "tasks": ["18.2", "19.1"] },
    { "id": 24, "tasks": ["18.3", "19.2"] },
    { "id": 25, "tasks": ["18.4", "18.5", "18.6", "18.7", "19.3", "19.6"] },
    { "id": 26, "tasks": ["19.4", "21.1"] },
    { "id": 27, "tasks": ["19.5", "21.2", "21.4"] },
    { "id": 28, "tasks": ["21.3", "21.8"] },
    { "id": 29, "tasks": ["21.5"] },
    { "id": 30, "tasks": ["21.6", "21.7", "22.1"] },
    { "id": 31, "tasks": ["22.2", "22.3", "22.4"] },
    { "id": 32, "tasks": ["22.5", "22.6", "24.1"] },
    { "id": 33, "tasks": ["24.2", "25.1"] },
    { "id": 34, "tasks": ["24.3", "25.2"] },
    { "id": 35, "tasks": ["24.4", "24.5", "25.3", "25.5"] },
    { "id": 36, "tasks": ["25.4", "26.1"] },
    { "id": 37, "tasks": ["26.2", "27.1"] },
    { "id": 38, "tasks": ["26.3", "27.2"] },
    { "id": 39, "tasks": ["26.4", "26.5", "26.6", "27.3", "27.5"] },
    { "id": 40, "tasks": ["27.4", "29.1"] },
    { "id": 41, "tasks": ["29.2", "30.1"] },
    { "id": 42, "tasks": ["29.3", "30.2"] },
    { "id": 43, "tasks": ["29.4", "29.5", "30.3", "30.6"] },
    { "id": 44, "tasks": ["30.4", "31.1"] },
    { "id": 45, "tasks": ["30.5", "31.2", "31.6"] },
    { "id": 46, "tasks": ["31.3"] },
    { "id": 47, "tasks": ["31.4", "33.1"] },
    { "id": 48, "tasks": ["31.5", "33.2", "34.1"] },
    { "id": 49, "tasks": ["33.3", "34.2"] },
    { "id": 50, "tasks": ["33.4", "33.5", "33.6", "33.7", "34.3", "34.6"] },
    { "id": 51, "tasks": ["34.4", "35.1"] },
    { "id": 52, "tasks": ["34.5", "35.2"] },
    { "id": 53, "tasks": ["35.3"] },
    { "id": 54, "tasks": ["35.4", "35.5", "36.1"] },
    { "id": 55, "tasks": ["36.2", "37.1"] },
    { "id": 56, "tasks": ["36.3", "37.2"] },
    { "id": 57, "tasks": ["36.4", "36.5", "36.6", "36.7", "37.3", "37.6"] },
    { "id": 58, "tasks": ["37.4", "39.1", "39.2"] },
    { "id": 59, "tasks": ["37.5", "39.3", "40.1"] },
    { "id": 60, "tasks": ["39.4", "39.5", "40.2"] },
    { "id": 61, "tasks": ["39.6", "39.7", "39.8", "40.3", "40.6"] },
    { "id": 62, "tasks": ["40.4", "42.1"] },
    { "id": 63, "tasks": ["40.5", "42.2", "43.1"] },
    { "id": 64, "tasks": ["42.3", "43.2", "43.3"] },
    { "id": 65, "tasks": ["43.4", "43.5"] },
    { "id": 66, "tasks": ["43.6"] },
    { "id": 67, "tasks": ["43.7", "43.8", "43.9", "45.1"] },
    { "id": 68, "tasks": ["43.10", "45.2", "45.6"] },
    { "id": 69, "tasks": ["45.3"] },
    { "id": 70, "tasks": ["45.4", "45.5", "46.1", "46.3"] },
    { "id": 71, "tasks": ["46.2", "46.4"] }
  ]
}
```
