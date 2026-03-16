# Implementation Plan: Creación Inline de Catalog Items

## Overview

Implementar tres funcionalidades relacionadas con la gestión de catálogos:

1. **Creación inline de CatalogItem** (Tasks 1-10): Formulario inline dentro de `ItemForm` para crear ítems de catálogo sin abandonar el flujo de agregar items a colecciones. Componente `InlineCatalogItemForm` reutilizable.
2. **Backend CSV import** (Tasks 11-14): Incremento de `total_items`, servicio de importación CSV con validación, y endpoint `POST /catalogs/{id}/import-csv`.
3. **Catalog Management Page + CSV upload UI** (Tasks 15-18): Página dedicada para gestionar catálogos con creación manual (reutilizando `InlineCatalogItemForm`) e importación masiva desde CSV.

## Tasks

- [ ] 1. Agregar tipo `CatalogItemCreate` y método `createItem` en la capa de servicios frontend
  - [ ] 1.1 Agregar interface `CatalogItemCreate` en `frontend/src/types/item.ts`
    - Campos: `title` (obligatorio), `subtitle?`, `description?`, `manufacturer?`, `publisher?`, `developer?`, `brand?`, `language?`, `region?`, `rarity?`, `customFields?`, `coverImageUrl?`
    - _Requirements: 1.1, 1.3_
  - [ ] 1.2 Agregar método `createItem` en `frontend/src/services/catalogsApi.ts`
    - Firma: `createItem(catalogId: string, data: CatalogItemCreate): Promise<CatalogItem>`
    - Usa `fetchApi` con POST, convierte body a snake_case con `toSnakeCase`
    - _Requirements: 1.1_
  - [ ]* 1.3 Escribir unit tests para `catalogsApi.createItem` en `frontend/src/services/catalogsApi.test.ts`
    - Verificar que llama a `fetchApi` con URL y método correctos
    - Verificar conversión a snake_case del body
    - _Requirements: 1.1_

- [ ] 2. Crear hook `useCreateCatalogItem`
  - [ ] 2.1 Crear `frontend/src/hooks/useCreateCatalogItem.ts`
    - Usa `useMutation` de React Query con `catalogsApi.createItem`
    - Invalida query key `["catalogs", catalogId, "items"]` en `onSuccess`
    - Recibe `catalogId: string` como parámetro
    - _Requirements: 1.1, 2.3_
  - [ ]* 2.2 Escribir unit tests para `useCreateCatalogItem` en `frontend/src/hooks/useCreateCatalogItem.test.ts`
    - Verificar que mutation llama a `catalogsApi.createItem` con datos correctos
    - Verificar invalidación de queries en onSuccess
    - _Requirements: 1.1, 2.3_

- [ ] 3. Crear componente `InlineCatalogItemForm`
  - [ ] 3.1 Crear `frontend/src/components/items/InlineCatalogItemForm.tsx`
    - Props: `onCreated(item: CatalogItem)`, `onCancel()`, `catalogId: string`, `isLoading: boolean`
    - Campo título obligatorio con validación local (no vacío, no solo whitespace)
    - Campos opcionales colapsados por defecto (subtítulo, descripción, fabricante, etc.)
    - Auto-focus en campo título al montar
    - Botón submit deshabilitado durante carga (`isLoading`)
    - Escape cierra el formulario llamando `onCancel()`
    - Usa `useTranslation` para todos los textos
    - Accesibilidad: labels, roles, aria-attributes según react-aria
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 3.1_
  - [ ]* 3.2 Escribir unit tests para `InlineCatalogItemForm` en `frontend/src/components/items/InlineCatalogItemForm.test.tsx`
    - Renderiza campo título con label correcto
    - Muestra error cuando título está vacío al submit
    - Muestra error cuando título es solo whitespace al submit
    - Auto-focus en campo título al montar
    - Botón submit deshabilitado cuando `isLoading=true`
    - Escape llama `onCancel`
    - Submit con datos válidos llama `onCreated` (mock)
    - Test de accesibilidad con axe-core (obligatorio)
    - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 3.1_
  - [ ]* 3.3 Escribir property test: Cancelar preserva estado del formulario padre
    - **Property 3: Cancelar creación inline preserva estado del formulario padre**
    - **Validates: Requirements 2.2**
    - Usar `fast-check` para generar combinaciones arbitrarias de condition, notes, purchasePrice
    - Verificar que al abrir y cancelar el inline form, los valores del formulario padre no cambian
    - Archivo: `frontend/src/components/items/InlineCatalogItemForm.property.test.tsx`

- [ ] 4. Checkpoint - Verificar componente inline y hook
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Integrar `InlineCatalogItemForm` en `ItemForm`
  - [ ] 5.1 Modificar `frontend/src/components/items/ItemForm.tsx`
    - Agregar nueva prop `catalogId: string` a `ItemFormProps`
    - Agregar estado `showInlineForm: boolean`
    - Agregar botón "Crear nuevo ítem de catálogo" junto al selector de catalog items
    - Cuando `showInlineForm=true`, mostrar `InlineCatalogItemForm` debajo del selector
    - Integrar `useCreateCatalogItem` hook para manejar la mutation
    - Al recibir `onCreated(item)`, setear `catalogItemId = item.id` y ocultar formulario inline
    - Al recibir `onCancel`, ocultar formulario inline sin perder datos del formulario padre
    - _Requirements: 1.1, 2.1, 2.2, 2.3_
  - [ ]* 5.2 Actualizar tests de `ItemForm` en `frontend/src/components/items/ItemForm.test.tsx`
    - Muestra botón "Crear nuevo ítem de catálogo"
    - Click en botón muestra formulario inline
    - Crear item inline selecciona el nuevo item en el selector y oculta formulario inline
    - Cancelar formulario inline no pierde datos del formulario padre
    - Test de accesibilidad con axe-core
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 6. Agregar traducciones i18n para el formulario inline
  - [ ] 6.1 Agregar claves de traducción en `frontend/public/locales/es/translation.json`
    - Agregar sección `items.inline` con: `createNew`, `title`, `titleRequired`, `titleWhitespace`, `optionalFields`, `showOptional`, `hideOptional`, `subtitle`, `description`, `manufacturer`, `publisher`, `developer`, `brand`, `language`, `region`, `rarity`, `creating`, `createSuccess`, `createError`
    - _Requirements: 5.1_
  - [ ] 6.2 Agregar claves de traducción en `frontend/public/locales/en/translation.json`
    - Mismas claves que en español con textos en inglés
    - _Requirements: 5.1_
  - [ ]* 6.3 Escribir property test: Completitud de traducciones i18n
    - **Property 4: Completitud de traducciones i18n**
    - **Validates: Requirements 5.1**
    - Usar `fast-check` para iterar sobre todos los locales soportados (es, en)
    - Verificar que cada clave usada por `InlineCatalogItemForm` resuelve a un string no vacío
    - Archivo: `frontend/src/components/items/InlineCatalogItemForm.i18n.property.test.ts`

- [ ] 7. Checkpoint - Verificar integración completa del formulario inline
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Actualizar páginas que usan `ItemForm` para pasar `catalogId`
  - [ ] 8.1 Modificar `CollectionDetailPage` para pasar `catalogId` a `ItemForm`
    - Identificar de dónde obtener el `catalogId` en el contexto de la página
    - Pasar `catalogId` como prop al componente `ItemForm`
    - _Requirements: 2.1_
  - [ ]* 8.2 Actualizar tests de `CollectionDetailPage` para verificar que `catalogId` se pasa correctamente
    - Verificar que `ItemForm` recibe `catalogId` como prop
    - _Requirements: 2.1_

- [ ] 9. Backend - Escribir property tests para validación de creación de catalog items
  - [ ]* 9.1 Escribir property test: Validación de título determina éxito de creación
    - **Property 1: Validación de título determina éxito de creación**
    - **Validates: Requirements 1.3, 1.4, 3.1**
    - Usar `hypothesis` para generar strings arbitrarios
    - Verificar que `create_item` tiene éxito sii título no vacío, no solo whitespace, y ≤500 chars
    - Archivo: `backend/tests/unit/test_services/test_catalog_item_creation_properties.py`
  - [ ]* 9.2 Escribir property test: Catálogo inexistente rechaza creación
    - **Property 2: Catálogo inexistente rechaza creación**
    - **Validates: Requirements 3.2**
    - Usar `hypothesis` para generar UUIDs arbitrarios que no existen en DB
    - Verificar que `create_item` lanza `NotFoundError`
    - Archivo: `backend/tests/unit/test_services/test_catalog_item_creation_properties.py`

- [ ] 10. Checkpoint - Verificar integración inline completa
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Backend - Incrementar `total_items` al crear CatalogItem
  - [ ] 11.1 Modificar `CatalogService.create_item` en `backend/api/services/catalog_service.py`
    - Después de crear el item, incrementar `catalog.total_items += 1` y commit
    - _Requirements: 2.5, 1.6_
  - [ ] 11.2 Escribir tests para incremento de `total_items` en `backend/tests/unit/test_services/test_catalog_service.py`
    - Verificar que `total_items` se incrementa en 1 después de crear un item
    - Verificar que `total_items` refleja el conteo correcto después de múltiples inserciones
    - _Requirements: 2.5_

- [ ] 12. Backend - Crear servicio de importación CSV
  - [ ] 12.1 Crear `backend/api/services/csv_import_service.py`
    - Clase `CsvImportService` con dependencia de `AsyncSession`
    - Método `import_catalog_items(catalog_id: str, file_content: bytes, filename: str) -> BatchImportResult`
    - Validar tamaño máximo 5 MB antes de procesar
    - Validar que el archivo es CSV válido con codificación UTF-8
    - Requerir columna `title` como obligatoria
    - Mapear columnas opcionales: subtitle, description, manufacturer, publisher, developer, brand, language, region, rarity, sku, upc
    - Ignorar columnas no reconocidas
    - Procesar filas válidas e inválidas por separado: crear items válidos, reportar errores con número de fila y motivo
    - Actualizar `total_items` del catálogo con la cantidad de items creados
    - Retornar `BatchImportResult` con: `created_count`, `error_count`, `errors` (lista de `{row, message}`)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_
  - [ ] 12.2 Crear schemas en `backend/api/schemas/csv_import.py`
    - `BatchImportError`: `row: int`, `message: str`
    - `BatchImportResult`: `created_count: int`, `error_count: int`, `errors: list[BatchImportError]`
    - _Requirements: 5.5_
  - [ ] 12.3 Escribir unit tests para `CsvImportService` en `backend/tests/unit/test_services/test_csv_import_service.py`
    - CSV válido con todas las columnas crea items correctamente
    - CSV con filas válidas e inválidas crea los válidos y reporta errores
    - CSV sin columna `title` es rechazado
    - CSV vacío (solo headers) retorna error de archivo sin datos
    - CSV con columnas no reconocidas las ignora
    - Archivo que excede 5 MB es rechazado
    - Archivo con codificación no UTF-8 es rechazado
    - Catálogo inexistente lanza NotFoundError
    - `total_items` se actualiza correctamente después de importación
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_
  - [ ]* 12.4 Escribir property test: Consistencia de BatchImportResult
    - **Property 5: created_count + error_count == total de filas de datos del CSV**
    - **Validates: Requirements 5.4, 5.5**
    - Usar `hypothesis` para generar CSVs arbitrarios con filas válidas e inválidas
    - Verificar que `created_count + error_count` siempre iguala el número de filas de datos
    - Archivo: `backend/tests/unit/test_services/test_csv_import_properties.py`

- [ ] 13. Backend - Crear endpoint de importación CSV
  - [ ] 13.1 Agregar endpoint en `backend/api/routes/catalogs.py`
    - `POST /catalogs/{catalog_id}/import-csv` con `UploadFile`
    - Validar Content-Type: `text/csv` o `application/vnd.ms-excel`
    - Validar tamaño del archivo (413 si excede 5 MB)
    - Delegar procesamiento a `CsvImportService`
    - Retornar 200 con `BatchImportResult`
    - Retornar 404 si catálogo no existe
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  - [ ] 13.2 Agregar dependency `get_csv_import_service` en `backend/api/dependencies.py`
    - Factory function para `CsvImportService`
    - _Requirements: 6.1_
  - [ ] 13.3 Escribir integration tests para endpoint CSV en `backend/tests/integration/test_routes/test_catalog_csv_import.py`
    - POST con CSV válido retorna 200 y BatchImportResult correcto
    - POST con catálogo inexistente retorna 404
    - POST con archivo > 5 MB retorna 413
    - POST con Content-Type inválido retorna 422
    - POST con CSV sin columna title retorna error descriptivo
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.6_

- [ ] 14. Checkpoint - Verificar backend CSV import completo
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Frontend - Crear página de gestión de catálogos (Catalog Management Page)
  - [ ] 15.1 Agregar método `importCsv` en `frontend/src/services/catalogsApi.ts`
    - Firma: `importCsv(catalogId: string, file: File): Promise<BatchImportResult>`
    - Usa `fetchApi` con POST y `FormData` (no JSON)
    - _Requirements: 6.1_
  - [ ] 15.2 Agregar tipos `BatchImportError` y `BatchImportResult` en `frontend/src/types/catalog.ts`
    - `BatchImportError`: `{ row: number; message: string }`
    - `BatchImportResult`: `{ createdCount: number; errorCount: number; errors: BatchImportError[] }`
    - _Requirements: 5.5_
  - [ ] 15.3 Crear hook `useCsvImport` en `frontend/src/hooks/useCsvImport.ts`
    - Usa `useMutation` con `catalogsApi.importCsv`
    - Invalida query keys de catálogo en `onSuccess`
    - _Requirements: 5.5, 6.1_
  - [ ] 15.4 Crear componente `CsvUploadForm` en `frontend/src/components/catalogs/CsvUploadForm.tsx`
    - Props: `catalogId: string`, `onImportComplete(result: BatchImportResult)`, `onCancel()`
    - Input de archivo con accept=".csv"
    - Validación local: solo archivos .csv, máximo 5 MB
    - Muestra progreso durante importación
    - Muestra resumen de resultados (creados, errores) al finalizar
    - Muestra detalle de errores por fila si los hay
    - Accesibilidad: labels, roles ARIA, navegación por teclado
    - _Requirements: 5.1, 5.4, 5.5, 5.6_
  - [ ] 15.5 Crear página `CatalogManagementPage` en `frontend/src/pages/CatalogManagementPage.tsx`
    - Selector de catálogo (dropdown con catálogos disponibles)
    - Lista paginada de items del catálogo seleccionado
    - Botón "Agregar item" que muestra `InlineCatalogItemForm` con catálogo pre-seleccionado
    - Botón "Importar CSV" que muestra `CsvUploadForm`
    - Estado vacío cuando no hay catálogos disponibles
    - Estado vacío cuando el catálogo seleccionado no tiene items
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - [ ]* 15.6 Escribir unit tests para `CsvUploadForm` en `frontend/src/components/catalogs/CsvUploadForm.test.tsx`
    - Renderiza input de archivo con label correcto
    - Rechaza archivos no-CSV
    - Rechaza archivos > 5 MB
    - Muestra resumen de resultados después de importación exitosa
    - Muestra errores por fila cuando hay errores
    - Test de accesibilidad con axe-core
    - _Requirements: 5.1, 5.4, 5.5, 5.6_
  - [ ]* 15.7 Escribir unit tests para `CatalogManagementPage` en `frontend/src/pages/CatalogManagementPage.test.tsx`
    - Muestra selector de catálogos
    - Muestra lista de items del catálogo seleccionado
    - Muestra estado vacío cuando no hay catálogos
    - Muestra estado vacío cuando catálogo no tiene items
    - Botón "Agregar item" muestra InlineCatalogItemForm
    - Botón "Importar CSV" muestra CsvUploadForm
    - Item creado inline se agrega a la lista sin recargar
    - Test de accesibilidad con axe-core
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 16. Agregar traducciones i18n para gestión de catálogos y CSV import
  - [ ] 16.1 Agregar claves de traducción en `frontend/public/locales/es/translation.json`
    - Sección `catalogs.management`: `title`, `selectCatalog`, `noCatalogs`, `noItems`, `addItem`, `importCsv`, `itemCount`
    - Sección `catalogs.csv`: `upload`, `selectFile`, `importing`, `importComplete`, `createdCount`, `errorCount`, `errorDetail`, `fileTooLarge`, `invalidFileType`, `noData`
    - _Requirements: 3.6, 4.5, 4.6_
  - [ ] 16.2 Agregar claves de traducción en `frontend/public/locales/en/translation.json`
    - Mismas claves que en español con textos en inglés
    - _Requirements: 3.6_

- [ ] 17. Agregar ruta de navegación para Catalog Management Page
  - [ ] 17.1 Agregar ruta `/catalogs` en el router de la aplicación
    - Importar `CatalogManagementPage` y registrar la ruta
    - _Requirements: 4.1_
  - [ ] 17.2 Agregar enlace de navegación en el menú/sidebar
    - Agregar link a "Gestión de Catálogos" en la navegación principal
    - _Requirements: 4.1_

- [ ] 18. Final checkpoint - Verificar todos los tests y la integración completa
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- El backend ya tiene el endpoint `POST /catalogs/{catalog_id}/items` y el schema `CatalogItemCreate` funcionando — no se requieren cambios backend para creación individual (excepto incremento de `total_items`)
- Tasks 1-10: Creación inline de CatalogItem desde ItemForm
- Task 11: Fix de `total_items` increment (backend)
- Tasks 12-14: Importación CSV (backend service + endpoint + tests)
- Tasks 15-17: Catalog Management Page + CSV upload UI (frontend)
- Task 18: Checkpoint final
- Cada task referencia requirements específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Property tests validan propiedades universales de corrección
- Unit tests validan ejemplos específicos y edge cases
- Tests de accesibilidad con axe-core son obligatorios en cada componente React nuevo
