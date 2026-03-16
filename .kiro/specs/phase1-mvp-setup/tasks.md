# Plan de Implementación: Phase 1 - MVP Setup de H.O.A.R.D.

## Resumen

Implementación incremental del MVP de H.O.A.R.D.: infraestructura Docker, modelos SQLAlchemy para 17 tablas, endpoints CRUD (categorías, catálogos, colecciones, items, imágenes), frontend React con i18n (ES/EN), y suite de testing con >70% coverage. Cada tarea integra sus tests correspondientes.

## Tareas

- [x] 1. Infraestructura Docker y configuración base del proyecto
  - [x] 1.1 Crear estructura de directorios del proyecto
    - Crear `backend/`, `frontend/`, `nginx/` con sus subdirectorios según PROJECT_STRUCTURE.md
    - Crear `backend/core/`, `backend/api/routes/`, `backend/api/models/`, `backend/api/schemas/`, `backend/api/services/`
    - Crear `backend/tests/`, `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/factories/`
    - _Requirements: REQ-001_

  - [x] 1.2 Crear Docker Compose y Dockerfiles
    - `docker-compose.yml` con 4 servicios: `db` (PostgreSQL 14-alpine), `backend` (FastAPI), `frontend` (React+Vite), `nginx` (alpine)
    - `backend/Dockerfile` con Python 3.11, usuario no-root `hoard` (UID 1000)
    - `frontend/Dockerfile` con Node 20, multi-stage build
    - `nginx/nginx.conf` con proxy reverso: `/` → frontend:3000, `/api/` → backend:8000
    - Volúmenes: `postgres_data`, `uploads`
    - _Requirements: REQ-001_

  - [x] 1.3 Configurar backend FastAPI base
    - `backend/core/config.py`: clase `Settings` con pydantic-settings (DB_URL, SECRET_KEY, CORS_ORIGINS, UPLOAD_DIR)
    - `backend/core/database.py`: engine async con asyncpg, `get_async_session` generator
    - `backend/main.py`: app FastAPI con CORS, exception handlers, router includes, health endpoint `/health`
    - `backend/requirements.txt` con todas las dependencias (fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pydantic, aiofiles, etc.)
    - `backend/requirements-dev.txt` con dependencias de testing (pytest, pytest-asyncio, httpx, hypothesis, pytest-cov)
    - _Requirements: REQ-001, REQ-017, REQ-018_

  - [x] 1.4 Configurar Alembic para migraciones
    - `backend/alembic.ini` y `backend/alembic/env.py` con soporte async
    - Migración inicial que ejecuta `database/schema.sql` (17 tablas)
    - Configurar `alembic/versions/` para migraciones incrementales
    - _Requirements: REQ-017_

  - [x] 1.5 Configurar testing backend (pytest)
    - `backend/tests/conftest.py` con fixtures: `db_session` (AsyncSession con PostgreSQL de test o SQLite in-memory), `client` (httpx AsyncClient), factories base
    - `backend/pytest.ini` o `pyproject.toml` con configuración de pytest-asyncio y coverage
    - Verificar que `pytest --cov` ejecuta correctamente con 0 tests
    - _Requirements: REQ-015_

  - [x] 1.6 Configurar excepciones de dominio y exception handlers globales
    - `backend/core/exceptions.py`: `DomainError`, `NotFoundError`, `DuplicateError`, `ValidationError`, `FileValidationError`
    - `backend/core/exception_handlers.py`: mapeo de excepciones de dominio a HTTP responses (404, 409, 422)
    - Registrar handlers en `main.py`
    - _Requirements: REQ-018_

- [x] 2. Checkpoint - Verificar infraestructura base
  - Ensure all tests pass, ask the user if questions arise.
  - Verificar que `docker-compose up` levanta los 4 contenedores
  - Verificar que `/health` responde 200

- [x] 3. Modelos SQLAlchemy y schemas Pydantic
  - [x] 3.1 Crear modelo base y mixins
    - `backend/api/models/base.py`: `Base` (DeclarativeBase), `UUIDMixin` (id UUID), `TimestampMixin` (created_at, updated_at)
    - `backend/api/models/__init__.py` exportando todos los modelos
    - _Requirements: REQ-002_

  - [x] 3.2 Implementar modelos de categorías
    - `backend/api/models/category.py`: `MainCategory` y `SubCategory` con relaciones
    - Campos según `database/schema.sql`: name, description, icon, display_order, is_active
    - Relación: MainCategory → SubCategory (one-to-many, cascade delete-orphan)
    - _Requirements: REQ-002, REQ-004_

  - [x] 3.3 Implementar modelos de catálogos
    - `backend/api/models/catalog.py`: `Catalog` y `CatalogItem`
    - Catalog: sub_category_id (FK), name, description, total_items, is_active
    - CatalogItem: catalog_id (FK), title, subtitle, description, release_date, manufacturer, publisher, developer, brand, language, region, rarity, custom_fields (JSONB), cover_image_url
    - Relaciones: Catalog → CatalogItem (one-to-many, cascade), Catalog → SubCategory
    - _Requirements: REQ-002, REQ-005, REQ-006_

  - [x] 3.4 Implementar modelos de colecciones
    - `backend/api/models/collection.py`: `Collection` y `CollectionItem`
    - Collection: name, description, collection_type (CHECK: single_category/multi_category/mixed), theme, restricted_to_sub_category_id (FK), goal_description, goal_items_count, display_order, is_public, is_active
    - CollectionItem: collection_id (FK), catalog_item_id (FK), condition, is_complete, notes, purchase_price, purchase_currency, purchase_date, acquisition_type, storage_location
    - Relaciones: Collection → CollectionItem (cascade delete-orphan), Collection → SubCategory, CollectionItem → CatalogItem
    - _Requirements: REQ-002, REQ-007, REQ-008_

  - [x] 3.5 Implementar modelos restantes (imágenes, wishlist, suppliers, accessories)
    - `backend/api/models/image.py`: `ItemImage` con collection_item_id (FK), file_path, file_name, file_size, mime_type, image_type, description, is_primary
    - `backend/api/models/wishlist.py`: `WishlistItem`, `WishlistSighting`
    - `backend/api/models/supplier.py`: `Supplier`
    - `backend/api/models/accessory.py`: `AccessoryStock`, `ItemComponent`
    - _Requirements: REQ-002, REQ-009_

  - [x] 3.6 Write property tests para modelos y validadores
    - **Property 1: Integridad de tipo de colección** — ∀ collection con type="single_category" ⟹ restricted_to_sub_category_id IS NOT NULL
    - **Validates: REQ-007.1, REQ-003**
    - **Property 4: Validez de condición** — ∀ item ⟹ condition ∈ {mint, near_mint, excellent, good, fair, poor}
    - **Validates: REQ-008, REQ-003**
    - Usar hypothesis para generar datos aleatorios y verificar constraints de Pydantic schemas

  - [x] 3.7 Implementar schemas Pydantic para categorías
    - `backend/api/schemas/category.py`: MainCategoryBase, MainCategoryCreate, MainCategoryUpdate, MainCategoryResponse, SubCategoryBase, SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse
    - Validaciones: name min_length=1, max_length=200
    - ConfigDict(from_attributes=True) en Response schemas
    - _Requirements: REQ-003, REQ-004_

  - [x] 3.8 Implementar schemas Pydantic para catálogos
    - `backend/api/schemas/catalog.py`: CatalogBase, CatalogCreate, CatalogUpdate, CatalogResponse, CatalogItemBase, CatalogItemCreate, CatalogItemUpdate, CatalogItemResponse
    - Validaciones: title min_length=1, max_length=500, custom_fields como dict
    - _Requirements: REQ-003, REQ-005, REQ-006_

  - [x] 3.9 Implementar schemas Pydantic para colecciones e items
    - `backend/api/schemas/collection.py`: CollectionBase, CollectionCreate, CollectionUpdate, CollectionResponse con model_validator para single_category
    - `backend/api/schemas/collection_item.py`: CollectionItemCreate, CollectionItemUpdate, CollectionItemResponse
    - Validaciones: collection_type Literal, condition Literal, purchase_price ge=0
    - _Requirements: REQ-003, REQ-007, REQ-008_

  - [x] 3.10 Implementar schemas Pydantic para imágenes
    - `backend/api/schemas/image.py`: ItemImageResponse, ImageUploadResponse
    - Validaciones: mime_type en tipos permitidos
    - _Requirements: REQ-003, REQ-009_

  - [x] 3.11 Write unit tests para schemas Pydantic
    - Test validación de CollectionCreate con single_category sin sub_category_id → ValidationError
    - Test validación de condition con valor inválido → ValidationError
    - Test validación de purchase_price negativo → ValidationError
    - Test round-trip: crear schema → model_dump → recrear schema
    - Naming: `test_{schema}_{scenario}_{expected}`
    - _Requirements: REQ-003, REQ-015_

- [x] 4. Checkpoint - Verificar modelos y schemas
  - Ensure all tests pass, ask the user if questions arise.
  - Verificar que Alembic genera migración correctamente
  - Verificar que todos los schemas validan correctamente

- [x] 5. Services y lógica de negocio backend
  - [x] 5.1 Implementar CategoryService
    - `backend/api/services/category_service.py`: list_main, get_main, create_main, update_main, delete_main, list_sub, get_sub, create_sub, update_sub, delete_sub
    - Validación: no eliminar categoría con catálogos asociados
    - Inyección de dependencias en `backend/api/dependencies.py`
    - _Requirements: REQ-004_

  - [x] 5.2 Write unit tests para CategoryService
    - test_create_main_category_with_valid_data_returns_category
    - test_create_sub_category_linked_to_main_returns_sub_category
    - test_delete_category_with_catalogs_raises_error
    - test_list_categories_returns_only_active
    - _Requirements: REQ-004, REQ-015_

  - [x] 5.3 Implementar CatalogService
    - `backend/api/services/catalog_service.py`: list_catalogs, get_catalog, create_catalog, update_catalog, delete_catalog, list_items, get_item, create_item, update_item, delete_item
    - Validación: sub_category_id debe existir al crear catálogo
    - Full-text search en catalog_items (title, description) usando PostgreSQL `ilike` o `to_tsvector`
    - _Requirements: REQ-005, REQ-006_

  - [x] 5.4 Write unit tests para CatalogService
    - test_create_catalog_with_valid_subcategory_returns_catalog
    - test_create_catalog_item_increments_total_items
    - test_search_catalog_items_by_title_returns_matches
    - test_search_catalog_items_no_match_returns_empty
    - _Requirements: REQ-005, REQ-006, REQ-015_

  - [x] 5.5 Implementar CollectionService
    - `backend/api/services/collection_service.py`: list, get_by_id, create, update, delete
    - Validación de negocio: nombre único entre colecciones activas, sub_category existe si single_category
    - Soft delete (is_active=False) o hard delete con cascade según diseño
    - _Requirements: REQ-007_

  - [x] 5.6 Write property tests para CollectionService
    - **Property 3: Unicidad de nombre de colección activa** — crear dos colecciones con mismo nombre ⟹ DuplicateError en la segunda
    - **Validates: REQ-007.2**
    - Usar hypothesis para generar nombres aleatorios y verificar unicidad

  - [x] 5.7 Write unit tests para CollectionService
    - test_create_collection_with_valid_data_returns_collection
    - test_create_collection_with_duplicate_name_raises_duplicate_error
    - test_create_single_category_without_subcategory_raises_validation_error
    - test_update_collection_partial_fields_updates_only_provided
    - test_delete_collection_removes_collection
    - test_get_nonexistent_collection_raises_not_found
    - _Requirements: REQ-007, REQ-015_

  - [x] 5.8 Implementar CollectionItemService
    - `backend/api/services/collection_item_service.py`: list_by_collection, get_by_id, add_item, update, delete
    - Validación: colección existe, catalog_item existe, compatibilidad de categoría para single_category
    - Paginación con skip/limit
    - _Requirements: REQ-008_

  - [x] 5.9 Write property tests para CollectionItemService
    - **Property 2: Compatibilidad de categoría en items** — agregar item de categoría incorrecta a single_category ⟹ ValidationError
    - **Validates: REQ-008.3**
    - **Property 7: Paginación acotada** — ∀ request con skip,limit: len(response) <= limit
    - **Validates: REQ-008.1**

  - [x] 5.10 Write unit tests para CollectionItemService
    - test_add_item_to_collection_returns_item
    - test_add_item_to_wrong_category_raises_validation_error
    - test_add_item_to_nonexistent_collection_raises_not_found
    - test_list_items_with_pagination_returns_correct_count
    - test_delete_item_removes_from_collection
    - _Requirements: REQ-008, REQ-015_

  - [x] 5.11 Implementar ImageService
    - `backend/api/services/image_service.py`: upload, list_by_item, delete
    - Validación de archivo: mime_type en {image/jpeg, image/png, image/webp}, tamaño <= 10MB
    - Generar nombre único con UUID, guardar en /uploads/{item_id}/
    - Primera imagen del item → is_primary=True
    - Al eliminar: borrar archivo de disco + registro de BD
    - _Requirements: REQ-009_

  - [x] 5.12 Write property tests para ImageService
    - **Property 5: Imagen primaria única** — ∀ item: COUNT(images WHERE is_primary=True) <= 1
    - **Validates: REQ-009.4**
    - **Property 6: Integridad de archivos de imagen** — mime_type ∈ {image/jpeg, image/png, image/webp}
    - **Validates: REQ-009.2**

  - [x] 5.13 Write unit tests para ImageService
    - test_upload_valid_image_returns_image_record
    - test_upload_invalid_mime_type_raises_file_validation_error
    - test_upload_oversized_file_raises_file_validation_error
    - test_first_image_is_primary
    - test_second_image_is_not_primary
    - test_delete_image_removes_file_and_record
    - _Requirements: REQ-009, REQ-015_

- [x] 6. Checkpoint - Verificar services y lógica de negocio
  - Ensure all tests pass, ask the user if questions arise.
  - Verificar coverage backend >70% con `pytest --cov`

- [x] 7. Routes (endpoints REST) backend
  - [x] 7.1 Implementar routes de categorías
    - `backend/api/routes/categories.py`: GET /api/categories (list main), POST /api/categories, GET /api/categories/{id}, PUT /api/categories/{id}, DELETE /api/categories/{id}
    - Sub-categorías: GET /api/categories/{id}/subcategories, POST /api/categories/{id}/subcategories, GET /api/subcategories/{id}, PUT /api/subcategories/{id}, DELETE /api/subcategories/{id}
    - Paginación con skip/limit en listados
    - Registrar router en `main.py`
    - _Requirements: REQ-004_

  - [x] 7.2 Write integration tests para routes de categorías
    - test_get_categories_returns_200_with_list
    - test_create_category_returns_201
    - test_create_category_without_name_returns_422
    - test_get_nonexistent_category_returns_404
    - test_delete_category_returns_204
    - Usar httpx AsyncClient contra la app FastAPI de test
    - _Requirements: REQ-004, REQ-015_

  - [x] 7.3 Implementar routes de catálogos
    - `backend/api/routes/catalogs.py`: GET /api/catalogs, POST /api/catalogs, GET /api/catalogs/{id}, PUT /api/catalogs/{id}, DELETE /api/catalogs/{id}
    - Items: GET /api/catalogs/{id}/items, POST /api/catalogs/{id}/items, GET /api/catalog-items/{id}, PUT /api/catalog-items/{id}, DELETE /api/catalog-items/{id}
    - Query param `search` para full-text search en items
    - _Requirements: REQ-005, REQ-006_

  - [x] 7.4 Write integration tests para routes de catálogos
    - test_get_catalogs_returns_200
    - test_create_catalog_returns_201
    - test_create_catalog_item_returns_201
    - test_search_catalog_items_returns_filtered_results
    - test_search_catalog_items_no_results_returns_empty_list
    - _Requirements: REQ-005, REQ-006, REQ-015_

  - [x] 7.5 Implementar routes de colecciones
    - `backend/api/routes/collections.py`: GET /api/collections, POST /api/collections, GET /api/collections/{id}, PUT /api/collections/{id}, DELETE /api/collections/{id}
    - Items: GET /api/collections/{id}/items, POST /api/collections/{id}/items
    - Item individual: GET /api/items/{id}, PUT /api/items/{id}, DELETE /api/items/{id}
    - _Requirements: REQ-007, REQ-008_

  - [x] 7.6 Write integration tests para routes de colecciones
    - test_create_collection_returns_201
    - test_create_collection_duplicate_name_returns_409
    - test_add_item_to_collection_returns_201
    - test_add_item_wrong_category_returns_422
    - test_get_collection_items_with_pagination_returns_200
    - test_delete_collection_cascades_items_returns_204
    - **Property 8: Cascada de eliminación** — eliminar colección → sus items también se eliminan
    - **Validates: REQ-007.5, REQ-008**
    - _Requirements: REQ-007, REQ-008, REQ-015_

  - [x] 7.7 Implementar routes de imágenes
    - `backend/api/routes/images.py`: POST /api/items/{id}/images (multipart/form-data), GET /api/items/{id}/images, DELETE /api/images/{id}
    - Servir imágenes estáticas desde /uploads/ via Nginx o StaticFiles
    - _Requirements: REQ-009_

  - [x] 7.8 Write integration tests para routes de imágenes
    - test_upload_image_returns_201
    - test_upload_invalid_type_returns_422
    - test_upload_oversized_file_returns_422
    - test_list_images_returns_200
    - test_delete_image_returns_204
    - _Requirements: REQ-009, REQ-015_

- [x] 8. Checkpoint - Verificar API backend completa
  - Ensure all tests pass, ask the user if questions arise.
  - Verificar que todos los endpoints responden correctamente
  - Verificar coverage backend >70% con `pytest --cov`

- [x] 9. Frontend - Setup y configuración base
  - [x] 9.1 Inicializar proyecto React con Vite y TypeScript
    - `frontend/` con Vite + React 18 + TypeScript strict mode
    - Configurar `tsconfig.json` con strict: true, paths aliases
    - Instalar dependencias: tailwindcss, @tanstack/react-query, react-router-dom, i18next, react-i18next, react-aria
    - Configurar TailwindCSS con `tailwind.config.ts` y `postcss.config.js`
    - _Requirements: REQ-010_

  - [x] 9.2 Configurar i18n (ES/EN)
    - `frontend/src/i18n/config.ts`: configuración de i18next con detección de idioma del browser
    - `frontend/public/locales/es/translation.json`: traducciones en español
    - `frontend/public/locales/en/translation.json`: traducciones en inglés
    - Incluir keys para: common (loading, error, save, cancel, delete, edit, create), collections, catalogs, categories, items, images, errors, navigation
    - _Requirements: REQ-014_

  - [x] 9.3 Configurar React Router y layout base
    - `frontend/src/App.tsx`: QueryClientProvider + RouterProvider + I18nextProvider
    - `frontend/src/components/layout/AppLayout.tsx`: header con navegación, selector de idioma, main content area
    - Rutas: `/` (Home), `/collections` (lista), `/collections/:id` (detalle), `/catalogs` (lista), `/catalogs/:id` (detalle)
    - _Requirements: REQ-010, REQ-012_

  - [x] 9.4 Configurar testing frontend (Vitest + Testing Library)
    - `frontend/vitest.config.ts` con jsdom environment
    - `frontend/src/test/setup.ts` con jest-axe matchers y MSW setup
    - Instalar: vitest, @testing-library/react, @testing-library/user-event, jest-axe, msw, fast-check
    - Configurar MSW handlers base para mock de API
    - _Requirements: REQ-016_

- [x] 10. Frontend - Tipos, servicios API y componentes base
  - [x] 10.1 Definir tipos TypeScript
    - `frontend/src/types/collection.ts`: Collection, CollectionCreate, CollectionUpdate, CollectionType, DisplayOrder
    - `frontend/src/types/item.ts`: CollectionItem, CollectionItemCreate, CatalogItem, ItemCondition, AcquisitionType
    - `frontend/src/types/category.ts`: MainCategory, SubCategory
    - `frontend/src/types/catalog.ts`: Catalog, CatalogCreate
    - `frontend/src/types/image.ts`: ItemImage
    - Usar camelCase para propiedades (transformar desde snake_case del backend)
    - _Requirements: REQ-013_

  - [x] 10.2 Implementar servicio API base (fetch client)
    - `frontend/src/services/api.ts`: función `fetchApi<T>` genérica con manejo de errores, headers JSON, base URL desde env
    - `frontend/src/services/collectionsApi.ts`: list, getById, create, update, delete
    - `frontend/src/services/collectionItemsApi.ts`: list, add, update, delete
    - `frontend/src/services/catalogsApi.ts`: list, getById, create, listItems, searchItems
    - `frontend/src/services/categoriesApi.ts`: listMain, listSub, create
    - `frontend/src/services/imagesApi.ts`: list, upload (multipart/form-data), delete
    - _Requirements: REQ-013_

  - [x] 10.3 Write unit tests para servicios API
    - Usar MSW para interceptar requests
    - test fetchApi maneja 200, 404, 422, 500 correctamente
    - test collectionsApi.list retorna array de colecciones
    - test collectionsApi.create envía POST con body correcto
    - _Requirements: REQ-013, REQ-016_

  - [x] 10.4 Implementar componentes UI base con accesibilidad
    - `frontend/src/components/ui/Button.tsx`: variantes (primary, secondary, danger), estados (loading, disabled), aria-label
    - `frontend/src/components/ui/Input.tsx`: label asociado, error message, aria-describedby
    - `frontend/src/components/ui/Select.tsx`: opciones accesibles con react-aria
    - `frontend/src/components/ui/Card.tsx`: contenedor semántico con article
    - `frontend/src/components/ui/Modal.tsx`: focus trap, Escape para cerrar, aria-modal
    - `frontend/src/components/ui/EmptyState.tsx`: mensaje cuando no hay datos
    - `frontend/src/components/ui/ErrorMessage.tsx`: role="alert" para errores
    - `frontend/src/components/ui/LoadingSpinner.tsx`: role="status" con aria-label
    - _Requirements: REQ-011_

  - [x] 10.5 Write unit tests + accessibility tests para componentes UI base
    - Cada componente: test de renderizado, test de interacción, test axe-core
    - test Button renderiza variantes correctamente
    - test Input asocia label con input via htmlFor/id
    - test Modal atrapa focus y cierra con Escape
    - test todos los componentes pasan axe-core sin violaciones
    - **Property 10: Accesibilidad de componentes** — ∀ componente interactivo: tiene aria-label o aria-labelledby ∧ pasa axe-core
    - **Validates: REQ-011.1, REQ-011.2**
    - _Requirements: REQ-011, REQ-016_

- [x] 11. Frontend - Hooks y componentes de dominio
  - [x] 11.1 Implementar hooks de datos con React Query
    - `frontend/src/hooks/useCollections.ts`: query list, mutations create/update/delete con invalidación de cache
    - `frontend/src/hooks/useCollection.ts`: query getById para detalle
    - `frontend/src/hooks/useCollectionItems.ts`: query list por collectionId, mutations add/update/delete
    - `frontend/src/hooks/useCatalogs.ts`: query list, search
    - `frontend/src/hooks/useCategories.ts`: query listMain, listSub
    - `frontend/src/hooks/useImages.ts`: query list por itemId, mutation upload/delete
    - Cada hook maneja estados: loading, error, success
    - _Requirements: REQ-013_

  - [x] 11.2 Write unit tests para hooks
    - Usar MSW + renderHook de Testing Library
    - test useCollections retorna lista y estados loading/success/error
    - test useCollections.create invalida cache tras mutación exitosa
    - test useCollectionItems filtra por collectionId
    - **Property 9: Estados mutuamente excluyentes** — exactamente uno de {isLoading, isError, isSuccess} es true
    - **Validates: REQ-013**
    - **Property 12: Invalidación de cache** — ∀ mutación exitosa: query correspondiente es invalidado
    - **Validates: REQ-013**
    - _Requirements: REQ-013, REQ-016_

  - [x] 11.3 Implementar componentes de colecciones
    - `frontend/src/components/collections/CollectionCard.tsx`: muestra nombre, tipo, conteo items, acciones edit/delete
    - `frontend/src/components/collections/CollectionList.tsx`: grid de CollectionCard con estados loading/error/empty
    - `frontend/src/components/collections/CollectionForm.tsx`: formulario crear/editar con validación, selector de tipo y sub-categoría
    - Todos los textos via `t()` de i18next
    - Todos los elementos interactivos con aria-labels
    - _Requirements: REQ-012, REQ-014_

  - [x] 11.4 Write unit tests + accessibility tests para componentes de colecciones
    - test CollectionCard renderiza nombre y tipo
    - test CollectionCard llama onEdit/onDelete al hacer click
    - test CollectionList muestra loading spinner, error message, empty state
    - test CollectionForm valida campos requeridos
    - test CollectionForm muestra selector de sub-categoría solo para single_category
    - test todos pasan axe-core sin violaciones
    - _Requirements: REQ-012, REQ-016_

  - [x] 11.5 Implementar componentes de items
    - `frontend/src/components/items/ItemCard.tsx`: muestra título, condición, precio, imagen principal
    - `frontend/src/components/items/ItemList.tsx`: lista de items con estados
    - `frontend/src/components/items/ItemForm.tsx`: formulario agregar/editar item con selección de catalog_item
    - `frontend/src/components/items/ImageUpload.tsx`: drag & drop o file picker, preview, validación client-side (tipo, tamaño)
    - `frontend/src/components/items/ImageGallery.tsx`: grid de imágenes con lightbox básico
    - _Requirements: REQ-012, REQ-009_

  - [x] 11.6 Write unit tests + accessibility tests para componentes de items
    - test ItemCard renderiza información del item
    - test ImageUpload valida tipo de archivo antes de enviar
    - test ImageUpload muestra preview de imagen seleccionada
    - test ImageGallery renderiza grid de imágenes
    - test todos pasan axe-core sin violaciones
    - _Requirements: REQ-012, REQ-009, REQ-016_

- [x] 12. Frontend - Páginas y navegación
  - [x] 12.1 Implementar páginas principales
    - `frontend/src/pages/HomePage.tsx`: dashboard con resumen de colecciones, accesos rápidos
    - `frontend/src/pages/CollectionsPage.tsx`: lista de colecciones con botón crear, usa useCollections hook
    - `frontend/src/pages/CollectionDetailPage.tsx`: detalle de colección con lista de items, botón agregar item
    - `frontend/src/pages/CatalogsPage.tsx`: lista de catálogos con búsqueda
    - `frontend/src/pages/CatalogDetailPage.tsx`: detalle de catálogo con items
    - Cada página maneja estados loading/error/empty con componentes UI base
    - _Requirements: REQ-012_

  - [x] 12.2 Implementar selector de idioma y navegación
    - `frontend/src/components/layout/LanguageSelector.tsx`: toggle ES/EN con i18next.changeLanguage
    - `frontend/src/components/layout/Navigation.tsx`: nav con links a Home, Collections, Catalogs
    - Navegación accesible por teclado con aria-current="page"
    - _Requirements: REQ-014, REQ-011_

  - [x] 12.3 Write unit tests para páginas
    - test CollectionsPage renderiza lista de colecciones (mock API con MSW)
    - test CollectionDetailPage muestra items de la colección
    - test HomePage muestra resumen
    - test LanguageSelector cambia idioma al hacer click
    - **Property 11: i18n completo** — ∀ string visible: proviene de t() y existe en es/ y en/
    - **Validates: REQ-014.1, REQ-014.2**
    - _Requirements: REQ-012, REQ-014, REQ-016_

- [x] 13. Checkpoint - Verificar frontend completo
  - Ensure all tests pass, ask the user if questions arise.
  - Verificar que todos los componentes pasan axe-core
  - Verificar que i18n funciona en ES y EN

- [x] 14. Integración end-to-end y wiring final
  - [x] 14.1 Conectar frontend con backend via Nginx proxy
    - Verificar que `frontend/src/services/api.ts` usa `/api/` como base URL (proxy via Nginx)
    - Configurar `frontend/.env` y `frontend/.env.development` con VITE_API_URL
    - Verificar CORS en backend permite origen del frontend
    - Actualizar `docker-compose.yml` si es necesario para networking entre contenedores
    - _Requirements: REQ-001, REQ-013_

  - [x] 14.2 Configurar Playwright para E2E
    - `frontend/playwright.config.ts` con baseURL apuntando a Nginx
    - `frontend/tests/e2e/` directorio con configuración base
    - _Requirements: REQ-016_

  - [x] 14.3 Write E2E tests con Playwright
    - `frontend/tests/e2e/collections.spec.ts`: flujo crear colección → verificar en lista → editar → eliminar
    - `frontend/tests/e2e/items.spec.ts`: flujo agregar item a colección → subir imagen → verificar
    - `frontend/tests/e2e/i18n.spec.ts`: cambiar idioma ES ↔ EN y verificar que toda la UI cambia
    - `frontend/tests/e2e/navigation.spec.ts`: navegar toda la app con teclado (Tab, Enter)
    - _Requirements: REQ-016_

- [x] 15. Checkpoint final - Verificar MVP completo
  - Ensure all tests pass, ask the user if questions arise.
  - Verificar backend coverage >70% con `pytest --cov`
  - Verificar que todos los componentes frontend pasan axe-core
  - Verificar que `docker-compose up` levanta todo el stack correctamente
  - Verificar flujos E2E principales funcionan

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requirements específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Property tests validan propiedades universales de correctitud del diseño
- Unit tests validan ejemplos específicos y edge cases
- Testing de accesibilidad con axe-core es obligatorio en cada componente React
- Backend usa Python (pytest + hypothesis), frontend usa TypeScript (Vitest + fast-check)
