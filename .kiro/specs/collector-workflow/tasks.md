# Tareas — Flujo del coleccionista (collector-workflow)

Ejecución dominio-por-dominio, verify-then-commit, marcado honesto de checkboxes. Backend con `-p no:postgresql` local + verificación en Unraid (Postgres). Frontend tsc/eslint/lint:i18n/vitest; E2E en Unraid.

## 1. Modelo de datos y migraciones
- [ ] 1.1 Agregar `country_of_origin` (String(2), nullable) a `CollectionItem`; migración Alembic aditiva. Tests de modelo.
- [ ] 1.2 Crear tabla/modelo `CollectionCatalog` (N:M) + relación `Collection.catalogs`; migración. Tests.
- [ ] 1.3 Crear modelo `MaintenanceSchedule` + relación en `CollectionItem`; migración. Tests.
- [ ] 1.4 Crear modelo `PendingCompletion` (entity_type, entity_id, missing_fields, status); migración + índice. Tests.

## 2. Schemas y alta completa de CollectionItem
- [ ] 2.1 Ampliar `CollectionItemBase/Update/Response`: `supplier_id`, `is_authentic`, `authenticity_notes`, `country_of_origin`, `condition_notes`, `custom_fields`. Validación ISO-2. Tests.
- [ ] 2.2 `CollectionItemService.add_item`/`update`: persistir campos nuevos + regla "colección necesita ≥1 catálogo asociado". Tests unit + integración de ruta.

## 3. Catálogos asociados (N:M) + alta rápida
- [ ] 3.1 `CollectionCatalogService` (associate/dissociate/list) + rutas `/collections/{id}/catalogs`. Tests.
- [ ] 3.2 `QuickAddService.quick_add_catalog` (resuelve/crea sub-categoría desde `tematica`, crea Catalog, asocia, Pending) + ruta `/collections/{id}/catalogs/quick`. Tests.

## 4. Proveedores rápidos
- [ ] 4.1 `QuickAddService.quick_add_supplier(name, country)` + ruta `POST /suppliers/quick` + Pending. Tests.

## 5. CatalogItem rápido + CollectionItem en una operación
- [ ] 5.1 `QuickAddService.quick_add_catalog_item_and_collection_item` + ruta `POST /collections/{id}/items/quick` (transacción, Pending del catalog_item). Tests.

## 6. Ownership ("¿ya lo tengo?")
- [ ] 6.1 Endpoint `GET /catalog-items/{id}/ownership` (colecciones + collection_items que lo contienen). Service + tests.

## 7. Wishlist → "ya lo conseguí"
- [ ] 7.1 `WishlistService.acquire(wishlist_id, data, remove_from_wishlist)` + ruta `POST /wishlist/{id}/acquire` (crea CollectionItem, marca adquirido, quita/conserva). Tests unit + integración.

## 8. Mantenimiento
- [ ] 8.1 `MaintenanceService` (CRUD + list_due) + rutas `/collection-items/{id}/maintenance` y `/maintenance/due`. Tests.

## 9. Pendientes
- [ ] 9.1 `PendingService` (open/list/resolve/auto-close) + rutas `GET /pending`, `PUT /pending/{id}/resolve`. Cablear altas rápidas a `open()`. Tests.

## 10. Precio on-demand PriceCharting
- [ ] 10.1 Config (`PRICE_LOOKUP_*`) + `PriceChartingClient` (urllib, allowlist, https, timeout, size cap) + `PriceLookupService.lookup`. Tests con HTML grabado (sin red) + allowlist/https-only.
- [ ] 10.2 Ruta `POST /catalog-items/{id}/price-lookup` (inserta price history source=PriceCharting). Tests integración.

## 11. Frontend — detalle de ítem y agregar a colección
- [ ] 11.1 Ruta+página `CatalogItemDetailPage` (`catalogs/:catalogId/items/:itemId`); arreglar link de `SearchPage`. Muestra info + ownership + acciones. Tests + axe.
- [ ] 11.2 `AddToCollectionForm` (colección, original/bootleg, país, estado, precio+moneda, proveedor con quick-add, ubicación física, toggle mantenimiento). Hook + service. Tests + axe.
- [ ] 11.3 `SupplierQuickAdd` inline. Tests.

## 12. Frontend — búsqueda + catálogos + colección
- [ ] 12.1 Filtro por catálogo/sistema en `SearchFilters`; integrar Catálogos en la navegación del buscador. Tests.
- [ ] 12.2 `CollectionDetailPage`: sección catálogos asociados + `CatalogQuickAdd`; ítem inexistente → alta rápida. Tests.
- [ ] 12.3 Resolver título del ítem en `ItemCard` (mostrar título del catálogo, no el UUID). Tests.

## 13. Frontend — wishlist, pendientes, precio
- [ ] 13.1 Botón "Agregar a wishlist" en detalle de ítem (elige colección). Tests.
- [ ] 13.2 Detalle de wishlist: "Ya lo conseguí" → `AddToCollectionForm` pre-cargado + checkbox "Quitar de la wishlist". Tests + axe.
- [ ] 13.3 `PendingPage` (lista por tipo + editor de completado). Ruta + nav. Tests + axe.
- [ ] 13.4 Botón "Buscar precio (PriceCharting)" en detalle de ítem → fila en historial. Tests.

## 14. i18n y verificación integral
- [ ] 14.1 Agregar todas las claves nuevas a los 5 locales; `lint:i18n` verde.
- [ ] 14.2 tsc + eslint + vitest verdes; backend suite completa + cobertura ≥ umbral.
- [ ] 14.3 Deploy en Unraid (Postgres) y E2E de los flujos nuevos; carga real y smoke de rutas.

## 15. Entrega
- [ ] 15.1 Commits incrementales por dominio; push a `feat/collector-workflow`; PR a `main` con resumen y evidencia de pruebas.
