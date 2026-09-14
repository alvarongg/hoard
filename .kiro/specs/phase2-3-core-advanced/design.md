# Design Document

_Fase 2 (Core) y Fase 3 (Advanced) — H.O.A.R.D._

## Overview

Este spec cierra las Fases 2 y 3 del roadmap sobre la base ya construida en la Fase 1: `CategoryService`, `CatalogService`, `CollectionService`, `CollectionItemService`, `CsvImportService` e `ImageService`, con routes finas en `api/routes/` y un frontend React 18 de 6 páginas con componentes UI base y traducciones es/en.

La migración `001_initial_schema.py` ya creó las 17 tablas, los 4 triggers y las 4 vistas, así que **no se crean tablas nuevas salvo `app_settings` para la configuración de backups (una migración nueva)**. El trabajo se reparte en tres frentes:

1. **Completar el mapeo ORM**: 4 modelos SQLAlchemy faltantes (`CategoryFieldSchema`, `CatalogPriceHistory`, `ItemTransaction`, `ItemAccessory`) más el modelo `AppSetting` que acompaña a la migración `002_app_settings.py` — 5 modelos nuevos en total — y las relaciones que faltan en modelos existentes.
2. **Exponer los dominios que ya tienen modelo pero no tienen capa de aplicación**: suppliers, wishlist + sightings, item components, accessories stock.
3. **Construir los dominios nuevos**: búsqueda avanzada, estadísticas, historial de precios, transacciones, export, import JSON, backups + scheduler, dark mode, idiomas pt/fr/de, gráficos, PWA/offline y la auditoría de accesibilidad.

**Advertencia de alcance.** Este es un spec grande (19 requirements) y se divide en dos bloques con dependencias entre sí:

- **Bloque Fase 2 Core** (Requirements 1–9): multi-category, suppliers, wishlist, sightings, componentes, búsqueda, estadísticas, dark mode, i18n. Coverage exigido >80%.
- **Bloque Fase 3 Advanced** (Requirements 10–18): price history, transacciones, accesorios, export, import, backups, gráficos, PWA/offline, accesibilidad avanzada. Coverage exigido >85%.

El bloque Advanced depende del Core en tres puntos concretos: los gráficos (R16) consumen los endpoints de estadísticas (R7); las transacciones (R11) y el historial de precios (R10) redefinen cómo se calculan la inversión y el ROI que R7 expone; y el import (R14) necesita que existan los services de wishlist y suppliers para poder importar esas entidades. El Requirement 19 es transversal y aplica a todo lo anterior.

El eje técnico que atraviesa el spec completo es la **divergencia PostgreSQL/SQLite**: producción usa PostgreSQL 14+ con `tsvector`, `pg_trgm`, columnas `GENERATED`, triggers y vistas; los tests usan SQLite in-memory con tablas creadas por `Base.metadata.create_all`, donde ninguna de esas piezas existe. La solución se define una sola vez en `## Architecture` y se reutiliza en todos los dominios afectados.

## Architecture

### Capas backend

```
backend/
├── api/
│   ├── routes/          # HTTP: validación de entrada, delegación, traducción de errores
│   ├── schemas/         # Pydantic v2: Base / Create / Update / Response
│   ├── services/        # TODA la lógica de negocio (AsyncSession por constructor)
│   ├── models/          # SQLAlchemy 2.0 declarativo
│   └── dependencies.py  # Factories get_x_service(db=Depends(get_db))
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── exceptions.py    # NotFoundError / DuplicateError / ValidationError / FileValidationError
│   ├── exception_handlers.py
│   ├── dialect.py       # NUEVO: capa de estrategia por dialecto
│   └── scheduler.py     # NUEVO: scheduler de backups
└── utils/
    └── computations.py  # NUEVO: reglas de cálculo compartidas (totales, stock, ROI)
```

Ninguna regla de negocio nueva vive en `routes/`. Las routes solo validan entrada (Pydantic + `Query`), delegan al service y dejan que los exception handlers globales de `main.py` traduzcan las excepciones de dominio a HTTP.

### Capas frontend

```
frontend/src/
├── components/
│   ├── ui/              # Button, Card, EmptyState, ErrorMessage, Input, LoadingSpinner, Modal, Select
│   │                    # + NUEVOS: Badge, Table, Tooltip, LiveRegion, SkipLink, ThemeToggle
│   ├── suppliers/ wishlist/ accessories/ components/ search/ stats/ charts/
│   ├── backups/ transfer/ offline/
│   └── layout/
├── pages/               # Composición + hooks de datos
├── hooks/               # useX: React Query + lógica de estado
├── services/            # Clientes HTTP sobre fetchApi
├── types/               # Un archivo por dominio
├── i18n/                # config.ts + public/locales/{es,en,pt,fr,de}/translation.json
├── offline/             # NUEVO: cola de sincronización (IndexedDB)
└── theme/               # NUEVO: ThemeProvider + useTheme
```

### Estrategia de compatibilidad PostgreSQL / SQLite

Este es el patrón central y reutilizable del spec. Se compone de dos piezas separadas por responsabilidad:

**1. `backend/utils/computations.py` — reglas de cálculo puras, una sola definición.**

Funciones sin dependencia de base de datos que definen la aritmética del dominio. Son la única fuente de verdad de esas reglas y se testean con Hypothesis de forma aislada:

```python
def transaction_total(
    amount: Decimal | None,
    shipping_cost: Decimal | None,
    tax_amount: Decimal | None,
    other_fees: Decimal | None,
) -> Decimal:
    """Replica la columna GENERATED item_transactions.total_amount."""


def available_stock(quantity_total: int, quantity_in_use: int) -> int:
    """Replica la columna GENERATED accessories_stock.quantity_available."""


def roi_percentage(invested: Decimal, current_value: Decimal) -> Decimal | None:
    """Retorna None cuando invested == 0 en lugar de dividir por cero."""


def is_item_complete(
    required_names: set[str], present_names: set[str]
) -> bool:
    """Un item es completo cuando todos los componentes required están presentes."""
```

En PostgreSQL estas funciones sirven de especificación (el valor lo produce la base). En SQLite producen el valor. Los tests de propiedades verifican que ambos caminos coinciden.

**2. `backend/core/dialect.py` — selección de implementación por dialecto.**

```python
class Dialect(str, Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


def current_dialect(db: AsyncSession) -> Dialect:
    """Return the dialect of the session's bind."""
    name = db.bind.dialect.name if db.bind is not None else "sqlite"
    return Dialect.POSTGRESQL if name == "postgresql" else Dialect.SQLITE


def supports_full_text(db: AsyncSession) -> bool:
    return current_dialect(db) is Dialect.POSTGRESQL


def supports_generated_columns(db: AsyncSession) -> bool:
    return current_dialect(db) is Dialect.POSTGRESQL


def supports_views(db: AsyncSession) -> bool:
    return current_dialect(db) is Dialect.POSTGRESQL
```

Los services que dependen del dialecto exponen **un método público y dos privados**, para que la ramificación quede en un único punto por operación y no se disperse:

```python
class CollectionStatsService:
    async def get_collection_stats(self, collection_id: str) -> CollectionStats:
        if supports_views(self._db):
            return await self._stats_from_view(collection_id)
        return await self._stats_from_queries(collection_id)
```

Aplicación por caso:

| Funcionalidad Postgres | Camino Postgres | Camino SQLite (test) | Dónde |
|---|---|---|---|
| `search_vector` (tsvector, pesos A/B/C) | `to_tsquery` + `ts_rank` sobre `search_vector` | `ILIKE` sobre `title`, `subtitle`, `alternate_titles`, con `search_mode="degraded"` en la respuesta | `SearchService` |
| `pg_trgm` (fuzzy) | `similarity(title, q) >= threshold` | omitido; el modo degradado no promete fuzzy | `SearchService` |
| `item_transactions.total_amount` GENERATED | se lee de la columna tras `refresh()` | `transaction_total(...)` asignado antes del `flush` | `TransactionService` |
| `accessories_stock.quantity_available` GENERATED | se lee de la columna | `available_stock(...)` calculado en el schema de respuesta | `AccessoryService` |
| `update_accessory_stock_trigger` | el trigger ajusta `quantity_in_use` | el service ajusta `quantity_in_use` explícitamente | `AccessoryService` |
| `v_collection_stats` | `SELECT` sobre la vista | agregaciones equivalentes con `func.sum` / `func.count` | `StatsService` |
| `v_wishlist_with_avg_price` | `SELECT` sobre la vista | `func.avg/min/max/count` sobre `wishlist_sightings` | `WishlistService` |
| `update_updated_at_column` | trigger | `TimestampMixin.onupdate` ya lo cubre | `models/base.py` |

**Regla de oro:** el camino SQLite nunca duplica la *regla*, solo la *ejecución*. La regla vive en `utils/computations.py`. Cuando `quantity_available` se lee en Postgres, el schema de respuesta usa el valor de la columna; cuando se lee en SQLite, usa `available_stock()`. Ambos se comparan en un test de propiedad.

Para que los tests puedan ejercitar el camino Postgres se agrega una marca `@pytest.mark.postgres`, desactivada por defecto y habilitable con `HOARD_TEST_DATABASE_URL` apuntando a un PostgreSQL real. Es la única forma honesta de verificar triggers, vistas y `GENERATED`.

### Mapa Requirement → componentes

| Req | Backend | Frontend |
|---|---|---|
| 1 Multi-category | `CollectionService` (validación de tipo), `CollectionStatsService` | `CollectionForm`, `CollectionDetailPage` (agrupado), `useCollectionStats` |
| 2 Suppliers | `SupplierService`, `routes/suppliers.py`, `schemas/supplier.py` | `suppliersApi`, `useSuppliers`, `SupplierCard`, `SupplierForm`, `SuppliersPage` |
| 3 Wishlist | `WishlistService`, `routes/wishlist.py`, `schemas/wishlist.py` | `wishlistApi`, `useWishlist`, `WishlistCard`, `WishlistForm`, `WishlistPage` |
| 4 Sightings | `WishlistService` (sightings + agregados) | `SightingList`, `SightingForm`, `WishlistDetailPage` |
| 5 Componentes | `ItemComponentService`, `routes/item_components.py` | `useItemComponents`, `ComponentChecklist`, `CompletenessBadge` |
| 6 Búsqueda | `SearchService`, `routes/search.py` | `useSearch` (debounce), `SearchBar`, `SearchFilters`, `SearchPage` |
| 7 Estadísticas | `StatsService`, `routes/stats.py` | `useStats`, `StatsPage`, `MetricCard` |
| 8 Dark mode | — | `ThemeProvider`, `useTheme`, `ThemeToggle`, tokens Tailwind `dark:` |
| 9 i18n pt/fr/de | — | `i18n/config.ts`, 3 `translation.json`, `LanguageSelector` |
| 10 Price history | `CatalogPriceHistory`, `PriceHistoryService` | `usePriceHistory`, `PriceHistoryTable`, `PriceHistoryForm` |
| 11 Transacciones | `ItemTransaction`, `TransactionService` | `useTransactions`, `TransactionList`, `TransactionForm` |
| 12 Accesorios | `ItemAccessory`, `AccessoryService` | `useAccessories`, `AccessoryCard`, `AccessoriesPage`, `LowStockList` |
| 13 Export | `ExportService`, `routes/export.py` | `useExport`, `ExportPage` |
| 14 Import | `JsonImportService`, `routes/import_data.py` | `useJsonImport`, `ImportWizard`, `ImportPage` |
| 15 Backups | `BackupService`, `core/scheduler.py`, `routes/backups.py` | `useBackups`, `BackupsPage` |
| 16 Gráficos | reutiliza `StatsService` | `charts/*` + `ChartDataTable` (alternativa textual) |
| 17 PWA/offline | — | `vite-plugin-pwa`, `offline/queue.ts`, `useSyncQueue`, `OfflineBanner`, `SyncStatusPanel` |
| 18 A11y avanzada | — | `LiveRegion`, `Tooltip`, `SkipLink`, `useReducedMotion`, auditoría axe por página |
| 19 Transversales | tests + coverage | tests + coverage + i18n + strict TS |

### Routers nuevos a registrar en `main.py`

```python
app.include_router(suppliers_router, prefix="/api")        # /api/suppliers
app.include_router(wishlist_router, prefix="/api")         # /api/wishlist
app.include_router(sightings_router, prefix="/api")        # /api/sightings
app.include_router(item_components_router, prefix="/api")  # /api/collection-items/{id}/components
app.include_router(accessories_router, prefix="/api")      # /api/accessories
app.include_router(search_router, prefix="/api")           # /api/search
app.include_router(stats_router, prefix="/api")            # /api/stats
app.include_router(price_history_router, prefix="/api")    # /api/catalog-items/{id}/price-history
app.include_router(transactions_router, prefix="/api")     # /api/collection-items/{id}/transactions
app.include_router(export_router, prefix="/api")           # /api/export
app.include_router(import_router, prefix="/api")           # /api/import
app.include_router(backups_router, prefix="/api")          # /api/backups
```

### Rutas nuevas en el frontend

`/suppliers`, `/wishlist`, `/wishlist/:id`, `/accessories`, `/search`, `/stats`, `/export`, `/import`, `/settings/backups`. Se agregan a `appRoutes` en `App.tsx` como hijos de `AppLayout`.

## Components and Interfaces

### 1. Colecciones multi-category (R1)

**Backend.** Se extiende `CollectionService` con la validación de tipo y se extrae la estadística a un service propio para no engordar el existente.

```python
# backend/api/services/collection_service.py  (extensión)
class CollectionService:
    VALID_TYPES = frozenset({"single_category", "multi_category", "mixed"})

    async def create(self, data: CollectionCreate) -> Collection: ...
    async def update(self, collection_id: str, data: CollectionUpdate) -> Collection: ...
    def _validate_type_and_restriction(
        self, collection_type: str, restricted_to_sub_category_id: str | None
    ) -> None:
        """Exige restricted_to_sub_category_id sólo para single_category."""

    async def list_items_grouped(
        self, collection_id: str
    ) -> list[CollectionItemGroup]:
        """Agrupa los items por main_category / sub_category con su conteo."""
```

```python
# backend/api/services/collection_stats_service.py  (nuevo)
class CollectionStatsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_collection_stats(self, collection_id: str) -> CollectionStats: ...
    async def _stats_from_view(self, collection_id: str) -> CollectionStats: ...
    async def _stats_from_queries(self, collection_id: str) -> CollectionStats: ...
```

**Endpoints** (en `routes/collections.py`):

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/collections/{id}/items/grouped` | 200, 404 |
| GET | `/api/collections/{id}/stats` | 200, 404 |

**Schemas** (`schemas/collection.py`, extensión):

```python
class CollectionStats(BaseModel):
    total_items: int
    different_categories_count: int
    total_invested: Decimal
    current_value: Decimal
    value_gain: Decimal
    roi_percentage: Decimal | None
    complete_items: int
    graded_items: int


class CollectionItemGroup(BaseModel):
    main_category_id: StrUUID
    main_category_name: str
    sub_category_id: StrUUID
    sub_category_name: str
    items_count: int
    items: list[CollectionItemResponse]
```

**Frontend.** `hooks/useCollectionStats.ts`, `hooks/useCollectionItemsGrouped.ts`; `components/collections/CollectionStatsPanel.tsx`, `components/collections/GroupedItemList.tsx`. `CollectionForm.tsx` agrega los campos `theme`, `themeDescription`, `goalDescription`, `goalItemsCount`, `displayOrder`, `isPublic`, `isActive` y muestra el selector de sub-categoría sólo cuando `collectionType === "single_category"`.

```typescript
interface GroupedItemListProps {
  groups: CollectionItemGroup[];
  onEditItem: (id: string) => void;
}
```

### 2. Proveedores (R2)

```python
# backend/api/services/supplier_service.py
class SupplierService:
    VALID_TYPES = frozenset(
        {"online", "physical_store", "marketplace", "private_seller", "auction"}
    )

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        type: str | None = None,
        country: str | None = None,
        is_favorite: bool | None = None,
        is_active: bool | None = None,
    ) -> list[Supplier]: ...
    async def get(self, supplier_id: str) -> Supplier: ...
    async def create(self, data: SupplierCreate) -> Supplier: ...
    async def update(self, supplier_id: str, data: SupplierUpdate) -> Supplier: ...
    async def delete(self, supplier_id: str) -> None:
        """Raises ValidationError si el proveedor está referenciado."""
    async def get_purchase_history(
        self, supplier_id: str, skip: int = 0, limit: int = 100
    ) -> list[SupplierPurchase]: ...
    async def _count_references(self, supplier_id: str) -> SupplierReferences: ...
```

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/suppliers` | 200 |
| POST | `/api/suppliers` | 201, 422 |
| GET | `/api/suppliers/{id}` | 200, 404 |
| PUT | `/api/suppliers/{id}` | 200, 404, 422 |
| DELETE | `/api/suppliers/{id}` | 204, 404, 409 |
| GET | `/api/suppliers/{id}/purchases` | 200, 404 |

```python
# backend/api/schemas/supplier.py
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=2)
    state_province: str | None = None
    city: str | None = None
    address: str | None = None
    postal_code: str | None = None
    website: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    marketplace_url: str | None = None
    social_media: dict | None = None
    rating: Decimal | None = Field(None, ge=0, le=5, decimal_places=2)
    notes: str | None = None
    is_favorite: bool = False
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str: ...

    @field_validator("type")
    @classmethod
    def _type_allowed(cls, v: str | None) -> str | None: ...


class SupplierCreate(SupplierBase): ...
class SupplierUpdate(BaseModel):  # todos opcionales
class SupplierResponse(SupplierBase):
    id: StrUUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupplierPurchase(BaseModel):
    collection_item_id: StrUUID
    title: str
    purchase_date: date | None
    purchase_price: Decimal | None
    purchase_currency: str


class SupplierReferences(BaseModel):
    collection_items: int
    wishlist_sightings: int
    accessories: int

    @property
    def total(self) -> int: ...
```

**Frontend.** `types/supplier.ts`, `services/suppliersApi.ts`, `hooks/useSuppliers.ts` (+ `useSupplier`, `useSupplierPurchases`), `components/suppliers/SupplierCard.tsx`, `SupplierForm.tsx`, `SupplierFilters.tsx`, `FavoriteToggle.tsx`, `pages/SuppliersPage.tsx`.

```typescript
interface SupplierCardProps {
  supplier: Supplier;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onToggleFavorite: (id: string, isFavorite: boolean) => void;
}
```

El toggle de favorito usa una mutación optimista de React Query (`onMutate` actualiza la cache, `onError` la revierte) para cumplir "sin recargar la página".

### 3 y 4. Wishlist y avistamientos (R3, R4)

Un solo service cubre ambos: los sightings no tienen ciclo de vida independiente del wishlist item.

```python
# backend/api/services/wishlist_service.py
class WishlistService:
    VALID_URGENCY = frozenset({"low", "medium", "high", "critical"})
    VALID_DECISIONS = frozenset(
        {"interested", "pass", "waiting", "negotiating", "purchased", "lost"}
    )

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # Wishlist items
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        collection_id: str | None = None,
        priority: int | None = None,
        urgency: str | None = None,
        is_active: bool | None = None,
        include_acquired: bool = False,
    ) -> list[WishlistItem]: ...
    async def get(self, item_id: str) -> WishlistItem: ...
    async def get_with_price_aggregates(self, item_id: str) -> WishlistItemDetail: ...
    async def create(self, data: WishlistItemCreate) -> WishlistItem: ...
    async def update(self, item_id: str, data: WishlistItemUpdate) -> WishlistItem: ...
    async def delete(self, item_id: str) -> None: ...
    async def mark_acquired(
        self, item_id: str, data: WishlistAcquire
    ) -> WishlistItem:
        """Raises ValidationError si ya está adquirido."""

    # Sightings
    async def list_sightings(self, item_id: str) -> list[WishlistSighting]: ...
    async def create_sighting(
        self, item_id: str, data: SightingCreate
    ) -> WishlistSighting: ...
    async def update_sighting(
        self, sighting_id: str, data: SightingUpdate
    ) -> WishlistSighting: ...
    async def delete_sighting(self, sighting_id: str) -> None: ...

    # Agregados (dialecto)
    async def _aggregates_from_view(self, item_id: str) -> PriceAggregates: ...
    async def _aggregates_from_queries(self, item_id: str) -> PriceAggregates: ...
```

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/wishlist` | 200 |
| POST | `/api/wishlist` | 201, 404, 422 |
| GET | `/api/wishlist/{id}` | 200, 404 |
| PUT | `/api/wishlist/{id}` | 200, 404, 422 |
| DELETE | `/api/wishlist/{id}` | 204, 404 |
| POST | `/api/wishlist/{id}/acquire` | 200, 404, 409 |
| GET | `/api/wishlist/{id}/sightings` | 200, 404 |
| POST | `/api/wishlist/{id}/sightings` | 201, 404, 422 |
| PUT | `/api/sightings/{id}` | 200, 404, 422 |
| DELETE | `/api/sightings/{id}` | 204, 404 |

`GET /api/wishlist` excluye por defecto los adquiridos; `?include_acquired=true` los incluye.

```python
# backend/api/schemas/wishlist.py
class WishlistItemBase(BaseModel):
    desired_condition: str | None = None
    desired_condition_min: str | None = None
    must_be_complete: bool = True
    desired_completeness_description: str | None = None
    max_price: Decimal | None = Field(None, ge=0)
    currency: str = "USD"
    specific_variant_required: bool = False
    variant_description: str | None = None
    priority: int = Field(3, ge=1, le=5)
    urgency: str = Field("medium")
    notes: str | None = None
    search_notes: str | None = None
    tags: list[str] | None = None
    is_active: bool = True


class WishlistItemCreate(WishlistItemBase):
    collection_id: str
    catalog_item_id: str


class WishlistItemUpdate(BaseModel): ...          # todos opcionales
class WishlistItemResponse(WishlistItemBase):
    id: StrUUID
    collection_id: StrUUID
    catalog_item_id: StrUUID
    is_acquired: bool
    acquired_date: date | None
    acquired_collection_item_id: StrUUID | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PriceAggregates(BaseModel):
    avg_price: Decimal | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    total_sightings: int = 0
    available_sightings: int = 0


class WishlistItemDetail(WishlistItemResponse):
    price_aggregates: PriceAggregates


class WishlistAcquire(BaseModel):
    collection_item_id: str
    acquired_date: date | None = None


class SightingBase(BaseModel):
    price: Decimal = Field(..., ge=0)
    sighted_at: datetime | None = None
    supplier_id: str | None = None
    location_description: str | None = None
    url: str | None = None
    currency: str = "USD"
    condition: str | None = None
    is_complete: bool | None = None
    description: str | None = None
    image_urls: list[str] | None = None
    is_available: bool = True
    quantity_available: int = Field(1, ge=0)
    last_checked_at: datetime | None = None
    contacted: bool = False
    contacted_at: datetime | None = None
    contact_method: str | None = None
    response_notes: str | None = None
    decision: str | None = None
    decision_notes: str | None = None
    decision_date: date | None = None
```

**Frontend.** `types/wishlist.ts`, `services/wishlistApi.ts`, `hooks/useWishlist.ts`, `hooks/useWishlistItem.ts`, `hooks/useSightings.ts`; `components/wishlist/WishlistCard.tsx`, `WishlistForm.tsx`, `WishlistFilters.tsx`, `PriorityBadge.tsx`, `UrgencyBadge.tsx`, `AcquireDialog.tsx`, `SightingList.tsx`, `SightingForm.tsx`, `PriceAggregatesPanel.tsx`; `pages/WishlistPage.tsx`, `pages/WishlistDetailPage.tsx`.

`PriorityBadge` y `UrgencyBadge` codifican el nivel con texto + icono además de color (no sólo color, R16.3 aplicado por coherencia).

### 5. Componentes de items (R5)

```python
# backend/api/services/item_component_service.py
class ItemComponentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_template(self, collection_item_id: str) -> list[ComponentTemplateEntry]:
        """standard_components de la sub-categoría del item, con el estado
        registrado en item_components si existe."""
    async def list(self, collection_item_id: str) -> list[ItemComponent]: ...
    async def upsert(
        self, collection_item_id: str, data: ItemComponentCreate
    ) -> ItemComponentResponse: ...
    async def update(
        self, component_id: str, data: ItemComponentUpdate
    ) -> ItemComponentResponse: ...
    async def delete(self, component_id: str) -> CompletenessResult: ...
    async def recalculate_completeness(
        self, collection_item_id: str
    ) -> CompletenessResult:
        """Escribe collection_items.is_complete usando is_item_complete()."""
```

La completitud se evalúa sólo sobre los `standard_components` con `component_type == "required"` de la sub-categoría del item. Cada mutación de componente termina llamando `recalculate_completeness`, que persiste `collection_items.is_complete` y devuelve el resultado para que el frontend actualice el badge sin refetch adicional.

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/collection-items/{id}/components/template` | 200, 404 |
| GET | `/api/collection-items/{id}/components` | 200, 404 |
| POST | `/api/collection-items/{id}/components` | 201, 404, 422 |
| PUT | `/api/item-components/{id}` | 200, 404, 422 |
| DELETE | `/api/item-components/{id}` | 200, 404 |

`DELETE` devuelve 200 con `CompletenessResult` (no 204) porque el borrado cambia la completitud y el cliente necesita el nuevo valor.

```python
class ItemComponentBase(BaseModel):
    standard_component_id: str | None = None
    component_name: str | None = None
    component_type: str | None = None
    is_present: bool = True
    condition: str | None = None
    condition_notes: str | None = None
    variant_description: str | None = None

    @model_validator(mode="after")
    def _name_or_standard_required(self) -> "ItemComponentBase":
        """component_name es obligatorio cuando standard_component_id es None."""


class CompletenessResult(BaseModel):
    collection_item_id: StrUUID
    is_complete: bool
    required_total: int
    required_present: int
```

**Frontend.** `types/itemComponent.ts`, `services/itemComponentsApi.ts`, `hooks/useItemComponents.ts`; `components/components/ComponentChecklist.tsx`, `ComponentRow.tsx`, `CompletenessBadge.tsx`.

```typescript
interface ComponentChecklistProps {
  collectionItemId: string;
  onCompletenessChange: (result: CompletenessResult) => void;
}
```

### 6. Búsqueda avanzada (R6)

```python
# backend/api/services/search_service.py
class SearchService:
    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self._db = db
        self._similarity_threshold = settings.SEARCH_SIMILARITY_THRESHOLD

    async def search_catalog_items(
        self, params: CatalogSearchParams
    ) -> CatalogSearchResult: ...
    async def _full_text_search(
        self, params: CatalogSearchParams
    ) -> tuple[list[CatalogItem], int]:
        """to_tsquery sobre search_vector + ts_rank; fallback a
        similarity() de pg_trgm cuando el ts_query no arroja resultados."""
    async def _degraded_search(
        self, params: CatalogSearchParams
    ) -> tuple[list[CatalogItem], int]:
        """ILIKE sobre title, subtitle y alternate_titles."""
    def _apply_filters(self, stmt: Select, params: CatalogSearchParams) -> Select:
        """Filtros compartidos por ambos caminos: se aplican sobre el
        statement de texto, preservando su orden."""
```

Los filtros se aplican con el mismo helper en ambos caminos, lo que garantiza por construcción que el resultado filtrado es un subconjunto del no filtrado y que el orden por relevancia se conserva (R6.6).

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/search/catalog-items` | 200 |

Query params: `q`, `main_category_id`, `sub_category_id`, `language`, `region`, `manufacturer`, `publisher`, `developer`, `brand`, `rarity`, `year_min`, `year_max`, `skip`, `limit`.

```python
class CatalogSearchParams(BaseModel):
    q: str = ""
    main_category_id: str | None = None
    sub_category_id: str | None = None
    language: str | None = None
    region: str | None = None
    manufacturer: str | None = None
    publisher: str | None = None
    developer: str | None = None
    brand: str | None = None
    rarity: str | None = None
    year_min: int | None = Field(None, ge=1800, le=2200)
    year_max: int | None = Field(None, ge=1800, le=2200)
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


class SearchMode(str, Enum):
    FULL_TEXT = "full_text"
    FUZZY = "fuzzy"
    DEGRADED = "degraded"


class CatalogSearchResult(BaseModel):
    items: list[CatalogItemResponse]
    total: int
    search_mode: SearchMode
```

`SEARCH_SIMILARITY_THRESHOLD: float = 0.3` se agrega a `core/config.py` (variable de entorno, no constante hardcodeada).

**Frontend.** `services/searchApi.ts`, `hooks/useSearch.ts` (debounce 300 ms con `useDeferredValue` + timer propio, sin dependencia nueva), `hooks/useDebouncedValue.ts`; `components/search/SearchBar.tsx`, `SearchFilters.tsx`, `SearchResultList.tsx`, `SearchModeNotice.tsx`; `pages/SearchPage.tsx`.

```typescript
interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  resultCount: number;
  isLoading: boolean;
}
```

El conteo de resultados se anuncia con `LiveRegion` (`aria-live="polite"`) al cambiar filtros o al limpiarlos (R6.10).

### 7. Estadísticas (R7)

```python
# backend/api/services/stats_service.py
class StatsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_dashboard(self) -> DashboardStats: ...
    async def get_by_collection(self) -> list[CollectionStatsEntry]: ...
    async def get_valuation(self) -> ValuationStats: ...
    async def get_by_category(self) -> list[CategoryStatsEntry]: ...
    async def get_timeline(self, period: TimelinePeriod) -> list[TimelineEntry]: ...
    async def _invested_expression(self) -> ColumnElement:
        """Suma de inversión real: transacciones si existen, purchase_price
        si no. Los items sin ninguna de las dos se excluyen."""
```

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/stats/dashboard` | 200 |
| GET | `/api/stats/collections` | 200 |
| GET | `/api/stats/valuation` | 200 |
| GET | `/api/stats/categories` | 200 |
| GET | `/api/stats/timeline?period=month\|quarter\|year` | 200, 422 |

```python
class ValuationStats(BaseModel):
    total_invested: Decimal
    current_value: Decimal
    value_gain: Decimal
    roi_percentage: Decimal | None   # None si total_invested == 0


class DashboardStats(BaseModel):
    total_items: int
    total_value: Decimal
    roi_percentage: Decimal | None
    recent_acquisitions: list[CollectionItemSummary]
    most_valuable_items: list[CollectionItemSummary]
    high_priority_wishlist: list[WishlistItemResponse]


class CategoryStatsEntry(BaseModel):
    main_category_id: StrUUID
    main_category_name: str
    items_count: int
    total_value: Decimal


class TimelineEntry(BaseModel):
    period: str        # "2024-03", "2024-Q1", "2024"
    items_count: int
    amount_invested: Decimal
```

**Frontend.** `services/statsApi.ts`, `hooks/useStats.ts` (un hook por endpoint: `useDashboardStats`, `useValuationStats`, `useCategoryStats`, `useTimelineStats`); `components/stats/MetricCard.tsx`, `CollectionStatsTable.tsx`, `CategoryStatsTable.tsx`; `pages/StatsPage.tsx`.

Cada bloque de `StatsPage` maneja su propio estado de error para que la falla de una consulta no vacíe la página entera (R7.10 y R16.7).

### 8. Dark mode (R8)

```typescript
// frontend/src/theme/ThemeProvider.tsx
export type ThemePreference = "light" | "dark" | "auto";

interface ThemeContextValue {
  preference: ThemePreference;
  resolvedTheme: "light" | "dark";
  setPreference: (preference: ThemePreference) => void;
}

// frontend/src/theme/useTheme.ts
export function useTheme(): ThemeContextValue;

// frontend/src/theme/storage.ts
const STORAGE_KEY = "hoard.theme";
export function readPreference(): ThemePreference;   // "auto" ante valor inválido o localStorage no disponible
export function writePreference(preference: ThemePreference): void;
export function clearPreference(): void;             // usado por "auto"
```

Implementación: Tailwind con `darkMode: "class"`; el provider escribe o quita `class="dark"` en `document.documentElement` y escucha `matchMedia("(prefers-color-scheme: dark)")` cuando la preferencia es `auto`. `readPreference` envuelve el acceso a `localStorage` en `try/catch` y devuelve `"auto"` ante cualquier fallo (R8.5). Se agrega un script inline mínimo en `index.html` que aplica la clase antes del primer paint para evitar el flash de tema claro.

`components/ui/ThemeToggle.tsx` es un grupo de radio de 3 opciones (claro / oscuro / automático) con `role="radiogroup"`, `aria-checked` y navegación por flechas usando `react-aria`.

Los colores se definen como tokens semánticos en `tailwind.config.js` (`surface`, `surface-muted`, `content`, `content-muted`, `border`, `accent`, `danger`), cada uno con su variante `dark:`, verificados contra el ratio 4.5:1 de WCAG AA.

### 9. Idiomas pt, fr, de (R9)

`i18n/config.ts` pasa a `supportedLngs: ["es", "en", "pt", "fr", "de"]` y `detection.order: ["localStorage", "navigator", "htmlTag"]` (la preferencia explícita gana sobre el navegador, R9.4). Se agrega un listener `i18n.on("languageChanged", lng => document.documentElement.lang = lng)` para R9.6.

Se crean `public/locales/{pt,fr,de}/translation.json` con exactamente el mismo conjunto de claves que `es` y `en`.

`components/layout/LanguageSelector.tsx`: `<select>` accesible con `aria-label` traducido, opción activa marcada y el nombre de cada idioma en su propio idioma.

Se agrega `frontend/scripts/check-i18n-keys.ts`, ejecutable como `npm run lint:i18n`, que compara los 5 archivos y falla listando claves faltantes y sobrantes. El mismo chequeo se cubre además con un test de propiedad (Property 11).

### 10. Historial de precios (R10)

```python
# backend/api/services/price_history_service.py
class PriceHistoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        catalog_item_id: str,
        condition: str | None = None,
        is_complete: bool | None = None,
        region: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[CatalogPriceHistory]: ...
    async def create(
        self, catalog_item_id: str, data: PriceHistoryCreate
    ) -> CatalogPriceHistory:
        """Raises DuplicateError si la clave natural ya existe."""
    async def delete(self, price_id: str) -> None: ...
    async def latest_by_condition(
        self, catalog_item_id: str
    ) -> list[LatestPriceEntry]: ...
    async def refresh_item_market_value(
        self, collection_item_id: str
    ) -> ValueUpdateResult:
        """Toma el precio más reciente compatible con la condición y
        completitud del item y escribe current_market_value,
        current_value_currency, last_value_update y value_source."""
```

La unicidad `(catalog_item_id, condition, is_complete, price_date, source)` existe como constraint en Postgres; el service la verifica con un `SELECT` previo para poder lanzar `DuplicateError` con un mensaje útil y para que el comportamiento sea idéntico en SQLite.

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/catalog-items/{id}/price-history` | 200, 404 |
| POST | `/api/catalog-items/{id}/price-history` | 201, 404, 409, 422 |
| GET | `/api/catalog-items/{id}/price-history/latest` | 200, 404 |
| DELETE | `/api/price-history/{id}` | 204, 404 |
| POST | `/api/collection-items/{id}/refresh-value` | 200, 404 |

```python
class PriceHistoryBase(BaseModel):
    condition: str = Field(..., max_length=50)
    is_complete: bool = True
    completeness_description: str | None = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = "USD"
    source: str | None = None
    source_url: str | None = None
    price_date: date
    region: str | None = None
    notes: str | None = None


class ValueUpdateResult(BaseModel):
    collection_item_id: StrUUID
    updated: bool
    current_market_value: Decimal | None
    value_source: str | None
    reason: str | None = None   # motivo cuando updated es False
```

**Frontend.** `types/priceHistory.ts`, `services/priceHistoryApi.ts`, `hooks/usePriceHistory.ts`, `hooks/useRefreshMarketValue.ts`; `components/priceHistory/PriceHistoryTable.tsx`, `PriceHistoryForm.tsx`, `LatestPriceSummary.tsx`, integrados en `CatalogItemDetail`.

### 11. Transacciones (R11)

```python
# backend/api/services/transaction_service.py
class TransactionService:
    OUTFLOW_TYPES = frozenset(
        {"purchase", "trade_in", "repair", "appraisal", "grading", "insurance_claim"}
    )
    INFLOW_TYPES = frozenset({"sale", "trade_out", "gift_received", "gift_given"})
    VALID_TYPES = OUTFLOW_TYPES | INFLOW_TYPES

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, collection_item_id: str) -> list[ItemTransaction]: ...
    async def create(
        self, collection_item_id: str, data: TransactionCreate
    ) -> ItemTransaction:
        """En SQLite asigna total_amount con transaction_total();
        en PostgreSQL lo lee de la columna GENERATED tras refresh()."""
    async def update(
        self, transaction_id: str, data: TransactionUpdate
    ) -> ItemTransaction: ...
    async def delete(self, transaction_id: str) -> ItemInvestment: ...
    async def get_investment(self, collection_item_id: str) -> ItemInvestment:
        """real_invested = Σ total_amount(egresos) − Σ total_amount(ingresos)."""
```

`gift_received` y `gift_given` se clasifican como ingresos porque su `amount` habitual es cero o simbólico; el criterio queda documentado en la constante y no dispersado en el código.

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/collection-items/{id}/transactions` | 200, 404 |
| POST | `/api/collection-items/{id}/transactions` | 201, 404, 422 |
| PUT | `/api/transactions/{id}` | 200, 404, 422 |
| DELETE | `/api/transactions/{id}` | 200, 404 |
| GET | `/api/collection-items/{id}/investment` | 200, 404 |

```python
class TransactionBase(BaseModel):
    transaction_type: str
    transaction_date: date
    amount: Decimal | None = Field(None, decimal_places=2)
    currency: str = "USD"
    shipping_cost: Decimal | None = None
    tax_amount: Decimal | None = None
    other_fees: Decimal | None = None
    supplier_id: str | None = None
    counterpart_name: str | None = None
    invoice_number: str | None = None
    receipt_path: str | None = None
    payment_method: str | None = None
    notes: str | None = None

    @field_validator("transaction_type")
    @classmethod
    def _type_allowed(cls, v: str) -> str: ...


class TransactionResponse(TransactionBase):
    id: StrUUID
    collection_item_id: StrUUID
    total_amount: Decimal        # solo lectura: GENERATED en PostgreSQL
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ItemInvestment(BaseModel):
    collection_item_id: StrUUID
    real_invested: Decimal
    total_outflow: Decimal
    total_inflow: Decimal
    current_market_value: Decimal | None
    roi_percentage: Decimal | None
    source: Literal["transactions", "purchase_price"]
```

**Frontend.** `types/transaction.ts`, `services/transactionsApi.ts`, `hooks/useTransactions.ts`, `hooks/useItemInvestment.ts`; `components/transactions/TransactionList.tsx`, `TransactionForm.tsx`, `InvestmentSummary.tsx`. `totalAmount` se muestra como campo derivado de solo lectura, calculado en vivo en el formulario para dar feedback antes de enviar.

### 12. Accesorios y stock (R12)

```python
# backend/api/services/accessory_service.py
class AccessoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self, skip: int = 0, limit: int = 100, category: str | None = None
    ) -> list[AccessoryResponse]: ...
    async def get(self, accessory_id: str) -> AccessoryResponse: ...
    async def create(self, data: AccessoryCreate) -> AccessoryResponse: ...
    async def update(
        self, accessory_id: str, data: AccessoryUpdate
    ) -> AccessoryResponse: ...
    async def delete(self, accessory_id: str) -> None:
        """Raises ValidationError si tiene asignaciones vigentes."""
    async def list_low_stock(self) -> list[LowStockEntry]: ...

    # Asignaciones
    async def list_assignments(self, collection_item_id: str) -> list[ItemAccessory]: ...
    async def assign(
        self, data: ItemAccessoryCreate
    ) -> ItemAccessoryResponse:
        """Valida stock disponible y unicidad antes de insertar.
        En SQLite ajusta quantity_in_use; en PostgreSQL lo hace el trigger."""
    async def unassign(self, assignment_id: str) -> None: ...
    def _resolve_available(self, accessory: AccessoryStock) -> int:
        """Lee la columna GENERATED en PostgreSQL,
        available_stock() en SQLite."""
```

En PostgreSQL el trigger `update_accessory_stock_trigger` ajusta `quantity_in_use`; el service **no** lo toca en ese dialecto para no duplicar el incremento. La validación de stock disponible sí se hace en el service en ambos dialectos, antes del insert, porque es una regla de negocio y no una consecuencia de la escritura.

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/accessories` | 200 |
| POST | `/api/accessories` | 201, 422 |
| GET | `/api/accessories/{id}` | 200, 404 |
| PUT | `/api/accessories/{id}` | 200, 404, 422 |
| DELETE | `/api/accessories/{id}` | 204, 404, 409 |
| GET | `/api/accessories/low-stock` | 200 |
| GET | `/api/collection-items/{id}/accessories` | 200, 404 |
| POST | `/api/collection-items/{id}/accessories` | 201, 404, 409, 422 |
| DELETE | `/api/item-accessories/{id}` | 204, 404 |

```python
class AccessoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str | None = None
    subcategory: str | None = None
    compatible_sub_categories: list[str] | None = None
    size_specifications: dict | None = None
    quantity_total: int = Field(0, ge=0)
    minimum_stock_alert: int = Field(5, ge=0)
    reorder_quantity: int | None = Field(None, ge=0)
    unit_cost: Decimal | None = Field(None, ge=0)
    currency: str = "USD"
    supplier_id: str | None = None
    supplier_sku: str | None = None
    supplier_url: str | None = None
    notes: str | None = None


class AccessoryResponse(AccessoryBase):
    id: StrUUID
    quantity_in_use: int         # solo lectura: mantenido por trigger en PostgreSQL
    quantity_available: int      # solo lectura: GENERATED en PostgreSQL
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LowStockEntry(BaseModel):
    accessory_id: StrUUID
    name: str
    quantity_available: int
    minimum_stock_alert: int
    suggested_reorder_quantity: int


class ItemAccessoryCreate(BaseModel):
    accessory_id: str
    quantity_used: int = Field(1, ge=1)
    notes: str | None = None
```

**Frontend.** `types/accessory.ts`, `services/accessoriesApi.ts`, `hooks/useAccessories.ts`, `hooks/useItemAccessories.ts`; `components/accessories/AccessoryCard.tsx`, `AccessoryForm.tsx`, `LowStockList.tsx`, `StockBadge.tsx`, `AssignAccessoryDialog.tsx`; `pages/AccessoriesPage.tsx`.

`StockBadge` marca el stock bajo con color **y** con texto explícito ("Stock bajo") además de `aria-label`, cumpliendo R12.11.

### 13. Exportación (R13)

```python
# backend/api/services/export_service.py
class ExportService:
    SCHEMA_VERSION = "1.0"

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def export_collection(self, collection_id: str) -> CollectionExport: ...
    async def export_catalog_json(self, catalog_id: str) -> CatalogExport: ...
    async def export_catalog_csv(self, catalog_id: str) -> str:
        """Header idéntico a CsvImportService.REQUIRED_COLUMNS |
        OPTIONAL_COLUMNS, en orden estable."""
    async def export_wishlist(self, collection_id: str | None) -> WishlistExport: ...
```

El header CSV se deriva de las constantes de `CsvImportService`, no se escribe a mano: eso hace imposible que el export y el import se desincronicen (R13.3).

| Método | Path | Content-Type |
|---|---|---|
| GET | `/api/export/collections/{id}` | `application/json` + `Content-Disposition: attachment` |
| GET | `/api/export/catalogs/{id}?format=json` | `application/json` |
| GET | `/api/export/catalogs/{id}?format=csv` | `text/csv` |
| GET | `/api/export/wishlist` | `application/json` |

Todos: 200 en éxito, 404 si la entidad no existe, 422 si el `format` no es soportado.

```python
class ExportEnvelope(BaseModel):
    """Sobre común de todos los exports."""
    schema_version: str
    entity_type: Literal["collection", "catalog", "wishlist"]
    exported_at: datetime
    source: str = "hoard"


class CollectionExport(ExportEnvelope):
    collection: CollectionResponse
    items: list[CollectionItemExport]
    catalog_items: list[CatalogItemResponse]   # referencias resueltas


class CollectionItemExport(CollectionItemResponse):
    components: list[ItemComponentResponse]
```

**Frontend.** `services/exportApi.ts` (usa `fetch` directo + `URL.createObjectURL` para disparar la descarga, ya que `fetchApi` parsea JSON), `hooks/useExport.ts`; `components/transfer/ExportPanel.tsx`; `pages/ExportPage.tsx`.

### 14. Importación JSON (R14)

```python
# backend/api/services/json_import_service.py
class JsonImportService:
    MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
    SUPPORTED_VERSIONS = frozenset({"1.0"})

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def preview(
        self, file_content: bytes, filename: str
    ) -> ImportPreview:
        """Valida y resuelve claves naturales SIN escribir en la base."""
    async def execute(
        self, file_content: bytes, filename: str
    ) -> BatchImportResult: ...
    def _parse_envelope(self, file_content: bytes, filename: str) -> ExportEnvelope: ...
    def _plan(self, envelope: ExportEnvelope) -> ImportPlan:
        """Clasifica cada entidad en create / update / skip y acumula errores."""
    async def _resolve_existing(self, entity: BaseModel) -> str | None:
        """Busca la entidad existente por su clave natural."""
```

`preview` y `execute` comparten `_plan`: la vista previa es exactamente el plan que se va a ejecutar, no una estimación aparte. `preview` nunca hace `commit`; corre dentro de una transacción que se descarta.

**Claves naturales de merge** (una por entidad, decisión cerrada en `## Decisiones de Diseño`):

| Entidad | Clave natural |
|---|---|
| `Catalog` | `(sub_category_id, name)` |
| `CatalogItem` | `(catalog_id, title, region, variant)`; si viene `sku` o `upc` no vacío, ese valor gana |
| `Collection` | `(name)` |
| `CollectionItem` | `(collection_id, catalog_item_id, variant_description, certification_number)` |
| `WishlistItem` | `(collection_id, catalog_item_id)` |
| `Supplier` | `(name, type)` |
| `ItemComponent` | `(collection_item_id, component_name)` |

| Método | Path | Códigos |
|---|---|---|
| POST | `/api/import/preview` | 200, 413, 422 |
| POST | `/api/import/execute` | 200, 413, 422 |

```python
class ImportEntityChange(BaseModel):
    entity_type: str
    identifier: str
    action: Literal["create", "update", "skip"]
    reason: str | None = None


class ImportPreview(BaseModel):
    schema_version: str
    to_create: int
    to_update: int
    to_skip: int
    changes: list[ImportEntityChange]
    errors: list[BatchImportError]
```

`execute` reutiliza `BatchImportResult` (`created_count`, `error_count`, `errors`) del importador CSV, ampliado con `updated_count` y `skipped_count` como campos nuevos con default 0 para no romper al cliente CSV existente.

**Frontend.** `types/import.ts`, `services/importApi.ts`, `hooks/useJsonImport.ts`; `components/transfer/ImportWizard.tsx` (4 pasos: subir → vista previa → confirmar → reporte), `ImportPreviewTable.tsx`, `ImportReport.tsx`; `pages/ImportPage.tsx`. Cancelar en el paso de vista previa simplemente no llama `execute`: no hay estado que revertir en el servidor.

### 15. Backups y scheduler (R15)

```python
# backend/api/services/backup_service.py
class BackupService:
    MANIFEST_NAME = "manifest.json"
    VALID_FREQUENCIES = frozenset({"daily", "weekly", "monthly"})

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self._db = db
        self._backup_dir = Path(settings.BACKUP_DIR)
        self._upload_dir = Path(settings.UPLOAD_DIR)

    async def create(self, trigger: Literal["manual", "scheduled"]) -> BackupInfo: ...
    async def list(self) -> list[BackupInfo]: ...
    async def get_path(self, backup_id: str) -> Path:
        """Raises NotFoundError si el archivo no existe."""
    async def restore(self, backup_id: str) -> RestoreResult: ...
    async def delete(self, backup_id: str) -> None: ...
    async def get_config(self) -> BackupConfig: ...
    async def update_config(self, data: BackupConfigUpdate) -> BackupConfig: ...
    async def apply_retention(self) -> list[str]:
        """Elimina los más antiguos hasta cumplir la retención.
        Sólo se invoca después de un backup exitoso."""
    def _verify(self, archive: Path) -> BackupVerification:
        """Valida el tar.gz, el manifest y el checksum del dump."""
    def _dump_database(self, target: Path) -> None:
        """pg_dump -Fc vía subprocess. Raises ValidationError si el
        binario no está disponible."""
```

**Formato del archivo.** `hoard-backup-{YYYYMMDD-HHMMSS}-{shortid}.tar.gz` con:

```
manifest.json          # schema_version, created_at, trigger, db_dump_sha256,
                       #  image_count, app_version, postgres_version, sizes
database.dump          # pg_dump -Fc (formato custom, restaurable con pg_restore)
uploads/               # copia literal de UPLOAD_DIR
config.json            # settings no sensibles (nunca SECRET_KEY ni DATABASE_URL)
```

**Verificación antes de restaurar** (R15.7), en tres pasos, todos antes de tocar los datos:

1. El tar.gz se abre y se listan sus miembros; si falla, `ValidationError`.
2. `manifest.json` existe, es JSON válido y su `schema_version` es soportada.
3. El SHA-256 de `database.dump` extraído coincide con `db_dump_sha256` del manifest.

Sólo si los tres pasan se ejecuta `pg_restore --clean --if-exists`. La extracción se hace a un directorio temporal, y los miembros del tar se validan contra path traversal (`..`, rutas absolutas) antes de extraerse.

**Si `pg_dump` no está disponible** (por ejemplo, contenedor backend sin el cliente de PostgreSQL): `create` lanza `ValidationError` con un mensaje que nombra el binario faltante, y el endpoint responde 503 en lugar de generar un backup silenciosamente incompleto. Se documenta en `docs/DOCKER_ARCHITECTURE.md` que la imagen del backend debe incluir `postgresql-client`. La detección se hace con `shutil.which("pg_dump")` al inicio de `create`.

**Scheduler.** `backend/core/scheduler.py` con **APScheduler 3.10** (`AsyncIOScheduler`), arrancado desde el `lifespan` de FastAPI.

Elección y justificación: `cron` del contenedor obligaría a duplicar la configuración fuera de la aplicación y a exponer un CLI aparte; una tarea `asyncio` propia requeriría reimplementar parsing de frecuencias, persistencia del próximo disparo y manejo de errores. APScheduler ya resuelve eso, corre en el mismo event loop que uvicorn y no agrega ningún proceso.

**Doble ejecución con múltiples workers.** Un scheduler in-process se instancia una vez por worker de uvicorn. Se resuelve con un **advisory lock de PostgreSQL** tomado por el job antes de ejecutar:

```python
async def _run_scheduled_backup(service_factory: ServiceFactory) -> None:
    async with service_factory() as service:
        acquired = await service.try_acquire_backup_lock()   # pg_try_advisory_lock(hashtext('hoard.backup'))
        if not acquired:
            return
        try:
            await service.create(trigger="scheduled")
        finally:
            await service.release_backup_lock()
```

Sólo un worker obtiene el lock; los demás salen sin hacer nada. Además se documenta que el despliegue por defecto usa `--workers 1`, y el lock cubre el caso de que se aumente.

| Método | Path | Códigos |
|---|---|---|
| GET | `/api/backups` | 200 |
| POST | `/api/backups` | 201, 503 |
| GET | `/api/backups/{id}/download` | 200, 404 |
| POST | `/api/backups/{id}/restore` | 200, 404, 422 |
| DELETE | `/api/backups/{id}` | 204, 404 |
| GET | `/api/backups/config` | 200 |
| PUT | `/api/backups/config` | 200, 422 |

```python
class BackupInfo(BaseModel):
    id: str
    filename: str
    created_at: datetime
    size_bytes: int
    trigger: Literal["manual", "scheduled"]
    includes_database: bool
    includes_images: bool
    includes_config: bool
    image_count: int


class BackupConfig(BaseModel):
    frequency: Literal["daily", "weekly", "monthly"]
    retention_count: int = Field(..., ge=1, le=365)
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_run_status: Literal["success", "failed"] | None


class RestoreResult(BaseModel):
    backup_id: str
    restored_database: bool
    restored_images: int
    restored_config: bool
    warnings: list[str]
```

**La configuración de backups necesita persistencia nueva.** El schema actual tiene exactamente 17 tablas y ninguna de configuración: no existe `app_settings`. La frecuencia, la retención, el último resultado y la próxima ejecución no tienen dónde vivir hoy, así que se crea la tabla `app_settings` mediante una **nueva migración Alembic** (`backend/alembic/versions/002_app_settings.py`), con columnas `key VARCHAR(100) PRIMARY KEY`, `value JSONB` (`JSON` en SQLite) y `updated_at TIMESTAMP`. La configuración se persiste ahí como pares clave/valor, no en un archivo suelto.

Es la **única** tabla nueva de todo el spec, y es el costo explícito de esta decisión: obliga a sumar una migración al pipeline y un modelo SQLAlchemy `AppSetting` que la mapea, con lo cual los modelos nuevos del spec pasan de 4 a 5.

**Frontend.** `types/backup.ts`, `services/backupsApi.ts`, `hooks/useBackups.ts`, `hooks/useBackupConfig.ts`; `components/backups/BackupList.tsx`, `BackupConfigForm.tsx`, `RestoreConfirmDialog.tsx`; `pages/BackupsPage.tsx`. El diálogo de restauración exige escribir la palabra de confirmación antes de habilitar el botón, dado que la operación es destructiva e irreversible.

### 16. Gráficos (R16)

**Librería elegida: Recharts 2.13.** Comparación:

| Opción | Peso | Accesibilidad | Encaje |
|---|---|---|---|
| **Recharts** | ~100 kB gzip | SVG declarativo; se puede inyectar `role`, `aria-label` y `<desc>` en cada serie; expone los datos como props React, lo que permite derivar la tabla equivalente del mismo array | Componentes React puros, integra directo con los tipos de `statsApi` |
| Chart.js | ~70 kB gzip | Renderiza en `<canvas>`: el contenido es opaco para lectores de pantalla y exige duplicar los datos a mano | Requiere wrapper y refs imperativos |
| visx | modular, el más liviano | Máximo control, mejor accesibilidad posible | Es un conjunto de primitivas: habría que construir ejes, leyendas y tooltips a mano, mucho código propio |

Recharts gana por el balance: SVG accesible sin construir la librería desde cero. Chart.js queda descartado por el canvas, que choca de frente con R16.2 y R16.5. visx queda descartado por costo de implementación desproporcionado para 4 gráficos.

```typescript
// frontend/src/components/charts/ChartContainer.tsx
interface ChartContainerProps {
  title: string;
  description: string;
  data: ChartSeries[];
  isLoading: boolean;
  error: Error | null;
  children: ReactNode;      // el gráfico Recharts
}
```

`ChartContainer` es el patrón único que resuelve R16.2 a R16.7 en un solo lugar:

- envuelve el gráfico en `<figure>` con `<figcaption>`;
- marca el SVG con `aria-hidden="true"` (es decorativo, los datos están en la tabla);
- renderiza `<ChartDataTable data={data} />` dentro de un `<details>` con `<summary>` alcanzable por teclado y etiquetado ("Ver datos en tabla");
- muestra `EmptyState` cuando `data` está vacío, `LoadingSpinner` mientras carga y `ErrorMessage` por gráfico ante error, sin afectar a los demás;
- respeta `prefers-reduced-motion` desactivando `isAnimationActive` de Recharts.

```typescript
// frontend/src/components/charts/ChartDataTable.tsx
interface ChartSeries {
  key: string;
  label: string;
  marker: "circle" | "square" | "triangle" | "diamond";   // forma, no sólo color
  dashArray?: string;                                      // patrón de línea
  points: { x: string; y: number }[];
}
```

Cada serie lleva `marker` y opcionalmente `dashArray`, de modo que la distinción no depende del color (R16.3).

Gráficos concretos: `ValuationOverTimeChart` (línea), `InvestmentVsValueChart` (barras agrupadas), `CategoryDistributionChart` (barras horizontales, no torta: más legible y más fácil de etiquetar), `AcquisitionTimelineChart` (área). Todos consumen `statsApi` sin endpoints nuevos.

### 17. PWA y modo sin conexión (R17)

**Plugin elegido: `vite-plugin-pwa` 0.21 con Workbox** (`registerType: "prompt"`). Es el estándar del ecosistema Vite, genera el manifest y el service worker en el build y expone `virtual:pwa-register/react` para el aviso de actualización. `injectManifest` no es necesario: `generateSW` con `runtimeCaching` alcanza para las estrategias que se necesitan.

Estrategias de cache por tipo de recurso:

| Recurso | Estrategia | Justificación |
|---|---|---|
| App shell (JS, CSS, HTML) | precache + `CacheFirst` | Versionado por hash, inmutable |
| `/locales/*/translation.json` | `StaleWhileRevalidate` | Cambian entre releases pero deben estar offline |
| `/uploads/*` (imágenes) | `CacheFirst`, máximo 200 entradas, 30 días | Inmutables por URL, ocupan espacio |
| `GET /api/collections`, `/api/collection-items`, `/api/stats/*` | `NetworkFirst` con timeout 3 s | Frescas con red, disponibles sin red (R17.3) |
| `GET /api/search/*` | `NetworkFirst` | La búsqueda offline se resuelve sobre la cache de React Query, no sobre la red |
| `POST` / `PUT` / `DELETE` a `/api/*` | sin cache; interceptadas por la cola | Las mutaciones no se cachean, se encolan |

**Cola de sincronización.** `frontend/src/offline/queue.ts` con **IndexedDB vía `idb` 8.0** (wrapper tipado de ~2 kB; se elige sobre `localStorage` por capacidad y sobre Dexie por peso).

```typescript
// frontend/src/offline/types.ts
export type QueuedStatus = "pending" | "applied" | "conflict" | "failed";

export interface QueuedOperation {
  id: number;                 // autoincremental: define el orden FIFO
  createdAt: string;
  method: "POST" | "PUT" | "DELETE";
  endpoint: string;
  body: unknown | null;
  entityType: string;
  entityId: string | null;
  entityUpdatedAt: string | null;   // para detectar conflicto
  status: QueuedStatus;
  attempts: number;
  error: string | null;
}

// frontend/src/offline/queue.ts
export async function enqueue(op: NewQueuedOperation): Promise<QueuedOperation>;
export async function listByStatus(status: QueuedStatus): Promise<QueuedOperation[]>;
export async function markApplied(id: number): Promise<void>;
export async function markConflict(id: number, serverUpdatedAt: string): Promise<void>;
export async function markFailed(id: number, error: string): Promise<void>;
export async function counts(): Promise<Record<QueuedStatus, number>>;

// frontend/src/offline/sync.ts
export async function drainQueue(): Promise<SyncSummary>;
```

`drainQueue` procesa las operaciones `pending` **estrictamente en orden ascendente de `id`** y se detiene ante un error de red (deja el resto pendiente para el siguiente intento). No hay concurrencia: un `Promise` secuencial, protegido por un flag de "sync en curso" para que dos disparos simultáneos no dupliquen envíos.

**Detección de conflicto** (R17.8): cada operación guarda el `updatedAt` de la entidad tal como la conocía el cliente. Antes de enviar un `PUT`/`DELETE`, `drainQueue` hace un `GET` de la entidad; si el `updatedAt` del servidor es posterior, la operación se marca `conflict`, **no se envía**, y el cambio del servidor se conserva. El usuario resuelve desde `SyncStatusPanel`.

**Errores de validación** (R17.9): un 4xx distinto de 409 marca la operación `failed` con el detalle y no se reintenta. Sólo los errores de red incrementan `attempts` y se reintentan, con un máximo de 5.

**Interacción con la cache de React Query.** Son dos capas separadas con roles distintos:

- React Query mantiene el estado de lectura en memoria, con `persistQueryClient` sobre IndexedDB (`@tanstack/query-sync-storage-persister` no sirve por el tamaño; se usa un persister propio sobre `idb`), para que las lecturas sobrevivan a un reload sin red.
- La cola sólo maneja escrituras. Cuando `drainQueue` aplica una operación, invalida las query keys del `entityType` afectado; cuando la marca `conflict`, invalida igual, porque el estado del servidor es el que gana.
- Las mutaciones offline hacen actualización optimista de la cache de React Query para que la UI refleje el cambio de inmediato, y `SyncStatusPanel` deja claro que está pendiente.

```typescript
// frontend/src/hooks/useOnlineStatus.ts
export function useOnlineStatus(): boolean;

// frontend/src/hooks/useSyncQueue.ts
export function useSyncQueue(): {
  counts: Record<QueuedStatus, number>;
  conflicts: QueuedOperation[];
  failed: QueuedOperation[];
  isSyncing: boolean;
  retry: (id: number) => Promise<void>;
  resolveConflict: (id: number, keep: "server" | "local") => Promise<void>;
};
```

`components/offline/OfflineBanner.tsx` usa `role="status"` + `aria-live="polite"` para anunciar el modo sin conexión (R17.5). `components/offline/SyncStatusPanel.tsx` muestra pendientes, aplicadas y en conflicto (R17.10). `components/offline/ConflictResolver.tsx` presenta el diff y deja elegir.

Manifest: nombre "H.O.A.R.D.", `short_name` "HOARD", iconos 192/512 más maskable, `theme_color` alineado con el token `accent`, `display: "standalone"`.

### 18. Accesibilidad avanzada (R18)

Componentes transversales nuevos en `components/ui/`:

```typescript
// LiveRegion.tsx — punto único de anuncios
interface LiveRegionProps {
  message: string;
  politeness?: "polite" | "assertive";
}

// Tooltip.tsx — visible por foco y por puntero, con aria-describedby
interface TooltipProps {
  content: string;
  children: ReactElement;
}

// SkipLink.tsx — primer elemento focusable del AppLayout
interface SkipLinkProps {
  targetId: string;
}

// Table.tsx — tabla accesible con caption, scope y sort anunciado
interface TableProps<T> {
  caption: string;
  columns: TableColumn<T>[];
  rows: T[];
}
```

```typescript
// hooks/useReducedMotion.ts
export function useReducedMotion(): boolean;

// hooks/useAnnouncement.ts — API imperativa sobre LiveRegion
export function useAnnouncement(): (message: string, politeness?: "polite" | "assertive") => void;
```

`Modal.tsx` existente se refuerza con `FocusScope` de react-aria (`contain` + `restoreFocus`) y cierre con Escape. Se agregan utilidades CSS globales: `:focus-visible` con outline de 2 px y contraste 3:1, y una regla `@media (prefers-reduced-motion: reduce)` que anula `transition` y `animation` no esenciales.

El zoom al 200% (R18.4) se aborda con layout fluido: contenedores con `max-width` en `rem`, sin anchos fijos en px, tablas envueltas en un contenedor con scroll horizontal propio (el scroll de una tabla ancha es aceptable; el de la página entera no).

La declaración de R18.8 (la auditoría automatizada no sustituye pruebas manuales con tecnologías asistivas ni revisión experta) se escribe en `docs/ACCESSIBILITY.md` y se enlaza desde el README.

### 19. Estándares transversales (R19)

No aporta componentes propios: se materializa en los tests, el chequeo de claves i18n, los umbrales de coverage en `pyproject.toml` / `vitest.config.ts` y la disciplina de mantener la lógica en services y el TypeScript en modo estricto sin `any`.

## Data Models

### Modelos SQLAlchemy nuevos

Son cinco modelos. De los cuatro primeros, las tablas ya existen en la migración `001_initial_schema.py` y lo único que falta es el mapeo; el quinto, `AppSetting`, requiere además la migración nueva `002_app_settings.py`. Los modelos se declaran con el mismo estilo que los existentes (`UUIDMixin`, `DBUUID`, `Mapped[...]`).

#### `CategoryFieldSchema` — `category_field_schemas`

Archivo: `backend/api/models/category_field_schema.py`

| Columna | Tipo SQLAlchemy | Notas |
|---|---|---|
| `id` | `DBUUID` PK | `UUIDMixin` |
| `sub_category_id` | `DBUUID` FK `sub_categories.id` ON DELETE CASCADE | not null |
| `field_name` | `String(100)` | not null, único junto a `sub_category_id` |
| `field_label` | `String(200)` | not null |
| `field_type` | `String(50)` | `text`, `number`, `date`, `select`, `multiselect`, `boolean`, `textarea` |
| `field_options` | `JSON` | `{"values": [...]}` para select/multiselect |
| `is_required` | `Boolean` default `False` | |
| `is_searchable` | `Boolean` default `True` | |
| `default_value` | `Text` | |
| `help_text` | `Text` | |
| `sort_order` | `Integer` default `0` | |
| `created_at` | `DateTime` server_default `now()` | sin `updated_at` en la tabla |

`__table_args__`: `UniqueConstraint("sub_category_id", "field_name", name="uq_category_field_sub_name")`.

#### `CatalogPriceHistory` — `catalog_price_history`

Archivo: `backend/api/models/price_history.py`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `DBUUID` PK | |
| `catalog_item_id` | `DBUUID` FK `catalog_items.id` CASCADE | not null |
| `condition` | `String(50)` | not null |
| `is_complete` | `Boolean` default `True` | not null |
| `completeness_description` | `String(200)` | |
| `price` | `Numeric(10, 2)` | not null |
| `currency` | `String(3)` default `"USD"` | |
| `source` | `String(200)` | |
| `source_url` | `String(500)` | |
| `price_date` | `Date` | not null |
| `region` | `String(10)` | |
| `notes` | `Text` | |
| `recorded_at` | `DateTime` server_default `now()` | |

`__table_args__`: `UniqueConstraint("catalog_item_id", "condition", "is_complete", "price_date", "source", name="unique_price_record")`.

Relación: `catalog_item: Mapped[CatalogItem] = relationship(back_populates="price_history")`.

#### `ItemTransaction` — `item_transactions`

Archivo: `backend/api/models/transaction.py`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `DBUUID` PK | |
| `collection_item_id` | `DBUUID` FK `collection_items.id` CASCADE | not null |
| `transaction_type` | `String(50)` | not null |
| `transaction_date` | `Date` | not null |
| `amount` | `Numeric(10, 2)` | nullable |
| `currency` | `String(3)` default `"USD"` | |
| `shipping_cost` | `Numeric(10, 2)` | nullable |
| `tax_amount` | `Numeric(10, 2)` | nullable |
| `other_fees` | `Numeric(10, 2)` | nullable |
| **`total_amount`** | `Numeric(10, 2)` | **solo lectura**: `GENERATED ALWAYS ... STORED` en PostgreSQL |
| `supplier_id` | `DBUUID` FK `suppliers.id` SET NULL | nullable |
| `counterpart_name` | `String(200)` | |
| `invoice_number` | `String(100)` | |
| `receipt_path` | `String(500)` | |
| `payment_method` | `String(50)` | |
| `notes` | `Text` | |
| `created_at` | `DateTime` server_default `now()` | |

`total_amount` se declara con `Computed` para que SQLAlchemy no lo incluya en los INSERT bajo PostgreSQL:

```python
from sqlalchemy import Computed

total_amount: Mapped[Decimal | None] = mapped_column(
    Numeric(10, 2),
    Computed(
        "COALESCE(amount, 0) + COALESCE(shipping_cost, 0) "
        "+ COALESCE(tax_amount, 0) + COALESCE(other_fees, 0)",
        persisted=True,
    ),
    nullable=True,
)
```

Bajo SQLite, `Base.metadata.create_all` traduce `Computed` a una columna `GENERATED ALWAYS AS (...) STORED`, que SQLite 3.31+ soporta. Si el runtime de SQLite no la soporta, `TransactionService` cae al camino de `transaction_total()`; la decisión se toma en `create` verificando `supports_generated_columns`. El campo es de solo lectura en todos los schemas: no aparece en `TransactionCreate` ni en `TransactionUpdate`.

#### `ItemAccessory` — `item_accessories`

Archivo: `backend/api/models/accessory.py` (se agrega al módulo existente)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `DBUUID` PK | |
| `collection_item_id` | `DBUUID` FK `collection_items.id` CASCADE | not null |
| `accessory_id` | `DBUUID` FK `accessories_stock.id` RESTRICT | not null |
| `quantity_used` | `Integer` default `1` | |
| `assigned_at` | `DateTime` server_default `now()` | |
| `notes` | `Text` | |

`__table_args__`: `UniqueConstraint("collection_item_id", "accessory_id", name="uq_item_accessory")`.

#### `AppSetting` — `app_settings` (tabla nueva)

Archivo: `backend/api/models/app_setting.py`. Es la única tabla que este spec crea, y viene con la migración `002_app_settings.py`. No usa `UUIDMixin`: la clave textual es la PK.

| Columna | Tipo SQLAlchemy | Notas |
|---|---|---|
| `key` | `String(100)` PK | clave del ajuste, p. ej. `backups.config` |
| `value` | `JSONB` en PostgreSQL, `JSON` en SQLite | payload del ajuste; se resuelve con `JSONB().with_variant(JSON(), "sqlite")` |
| `updated_at` | `DateTime` server_default `now()`, `onupdate=now()` | |

Consumida por el service de backups para leer y escribir frecuencia, retención, `last_run_at`, `last_run_status` y `next_run_at` bajo una sola clave.

### Campos de solo lectura por venir de columnas GENERATED

| Modelo | Campo | Origen en PostgreSQL | Fallback |
|---|---|---|---|
| `ItemTransaction` | `total_amount` | `GENERATED ... STORED` | `transaction_total()` |
| `AccessoryStock` | `quantity_available` | `GENERATED ... STORED` | `available_stock()` |
| `AccessoryStock` | `quantity_in_use` | mantenido por `update_accessory_stock_trigger` | ajuste explícito en `AccessoryService` |
| `Catalog` | `total_items` | mantenido por `update_catalog_total_items` | ya lo ajusta `CatalogService` |
| `CatalogItem` | `search_vector` | `catalog_items_search_vector_update` | ausente en SQLite; el modo degradado no lo usa |

`quantity_available` se agrega al modelo `AccessoryStock` como columna `Computed("quantity_total - quantity_in_use", persisted=True)` y nunca se escribe desde Python.

### Relaciones a agregar en modelos existentes

```python
# api/models/catalog.py — CatalogItem
price_history: Mapped[list[CatalogPriceHistory]] = relationship(
    back_populates="catalog_item",
    cascade="all, delete-orphan",
    passive_deletes=True,
)

# api/models/collection.py — CollectionItem
components: Mapped[list[ItemComponent]] = relationship(
    back_populates="collection_item",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
transactions: Mapped[list[ItemTransaction]] = relationship(
    back_populates="collection_item",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
accessories: Mapped[list[ItemAccessory]] = relationship(
    back_populates="collection_item",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
supplier: Mapped[Supplier | None] = relationship(back_populates="collection_items")

# api/models/category.py — SubCategory
field_schemas: Mapped[list[CategoryFieldSchema]] = relationship(
    back_populates="sub_category",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
standard_components: Mapped[list[StandardComponent]] = relationship(
    cascade="all, delete-orphan",
    passive_deletes=True,
)

# api/models/supplier.py — Supplier (necesarias para contar referencias antes de borrar)
collection_items: Mapped[list[CollectionItem]] = relationship(back_populates="supplier")
sightings: Mapped[list[WishlistSighting]] = relationship(back_populates="supplier")
accessories: Mapped[list[AccessoryStock]] = relationship(back_populates="supplier")

# api/models/accessory.py — AccessoryStock
assignments: Mapped[list[ItemAccessory]] = relationship(
    back_populates="accessory", passive_deletes=True
)

# api/models/wishlist.py — WishlistItem
acquired_collection_item: Mapped[CollectionItem | None] = relationship(
    foreign_keys=[acquired_collection_item_id]
)
```

`ItemComponent.collection_item` pasa a declarar `back_populates="components"`; hoy no lo tiene.

### Tipos TypeScript nuevos

Un archivo por dominio en `frontend/src/types/`:

```typescript
// supplier.ts
export type SupplierType =
  | "online" | "physical_store" | "marketplace" | "private_seller" | "auction";

export interface Supplier {
  id: string;
  name: string;
  type: SupplierType | null;
  country: string | null;
  stateProvince: string | null;
  city: string | null;
  address: string | null;
  postalCode: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  marketplaceUrl: string | null;
  socialMedia: Record<string, string> | null;
  rating: number | null;
  notes: string | null;
  isFavorite: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}
export interface SupplierCreate { /* sin id, createdAt, updatedAt */ }
export interface SupplierUpdate extends Partial<SupplierCreate> {}
export interface SupplierPurchase {
  collectionItemId: string;
  title: string;
  purchaseDate: string | null;
  purchasePrice: number | null;
  purchaseCurrency: string;
}
```

```typescript
// wishlist.ts
export type Urgency = "low" | "medium" | "high" | "critical";
export type Priority = 1 | 2 | 3 | 4 | 5;
export type SightingDecision =
  | "interested" | "pass" | "waiting" | "negotiating" | "purchased" | "lost";

export interface WishlistItem { /* ... */ isAcquired: boolean; }
export interface WishlistItemDetail extends WishlistItem {
  priceAggregates: PriceAggregates;
}
export interface PriceAggregates {
  avgPrice: number | null;
  minPrice: number | null;
  maxPrice: number | null;
  totalSightings: number;
  availableSightings: number;
}
export interface Sighting { /* ... */ }
```

```typescript
// itemComponent.ts
export type ComponentType = "required" | "common" | "optional" | "variant_specific";

export interface ItemComponent {
  id: string;
  collectionItemId: string;
  standardComponentId: string | null;
  componentName: string;
  componentType: ComponentType | null;
  isPresent: boolean;
  condition: string | null;
  conditionNotes: string | null;
  variantDescription: string | null;
}
export interface CompletenessResult {
  collectionItemId: string;
  isComplete: boolean;
  requiredTotal: number;
  requiredPresent: number;
}
```

```typescript
// search.ts
export type SearchMode = "full_text" | "fuzzy" | "degraded";
export interface CatalogSearchFilters {
  q: string;
  mainCategoryId?: string;
  subCategoryId?: string;
  language?: string;
  region?: string;
  manufacturer?: string;
  publisher?: string;
  developer?: string;
  brand?: string;
  rarity?: string;
  yearMin?: number;
  yearMax?: number;
}
export interface CatalogSearchResult {
  items: CatalogItem[];
  total: number;
  searchMode: SearchMode;
}
```

```typescript
// stats.ts
export interface ValuationStats {
  totalInvested: number;
  currentValue: number;
  valueGain: number;
  roiPercentage: number | null;   // null cuando la inversión es cero
}
export interface DashboardStats { /* ... */ }
export interface CategoryStatsEntry { /* ... */ }
export interface TimelineEntry { period: string; itemsCount: number; amountInvested: number }
export type TimelinePeriod = "month" | "quarter" | "year";
```

```typescript
// transaction.ts
export type TransactionType =
  | "purchase" | "sale" | "trade_in" | "trade_out" | "gift_received"
  | "gift_given" | "repair" | "appraisal" | "grading" | "insurance_claim";

export interface Transaction {
  id: string;
  collectionItemId: string;
  transactionType: TransactionType;
  transactionDate: string;
  amount: number | null;
  currency: string;
  shippingCost: number | null;
  taxAmount: number | null;
  otherFees: number | null;
  readonly totalAmount: number;   // GENERATED en el backend
  supplierId: string | null;
  counterpartName: string | null;
  invoiceNumber: string | null;
  receiptPath: string | null;
  paymentMethod: string | null;
  notes: string | null;
  createdAt: string;
}
export interface ItemInvestment {
  collectionItemId: string;
  realInvested: number;
  totalOutflow: number;
  totalInflow: number;
  currentMarketValue: number | null;
  roiPercentage: number | null;
  source: "transactions" | "purchase_price";
}
```

```typescript
// accessory.ts
export interface Accessory {
  id: string;
  name: string;
  category: string | null;
  subcategory: string | null;
  compatibleSubCategories: string[] | null;
  sizeSpecifications: Record<string, unknown> | null;
  quantityTotal: number;
  readonly quantityInUse: number;      // trigger en PostgreSQL
  readonly quantityAvailable: number;  // GENERATED en PostgreSQL
  readonly isLowStock: boolean;
  minimumStockAlert: number;
  reorderQuantity: number | null;
  unitCost: number | null;
  currency: string;
  supplierId: string | null;
  supplierSku: string | null;
  supplierUrl: string | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
}
export interface ItemAccessoryAssignment {
  id: string;
  collectionItemId: string;
  accessoryId: string;
  quantityUsed: number;
  assignedAt: string;
  notes: string | null;
}
```

```typescript
// priceHistory.ts, backup.ts, transfer.ts, offline.ts, chart.ts
// (PriceHistoryEntry, ValueUpdateResult, BackupInfo, BackupConfig, RestoreResult,
//  ImportPreview, ImportEntityChange, BatchImportResult ampliado,
//  QueuedOperation, QueuedStatus, ChartSeries)
```

Ningún tipo usa `any`. Donde el backend devuelve JSON libre (`customFields`, `sizeSpecifications`, `socialMedia`) se usa `Record<string, unknown>` y se hace narrowing en el punto de consumo.

## Error Handling

### Backend — escenario → excepción → HTTP

| Escenario | Excepción de dominio | HTTP | Clave i18n del mensaje |
|---|---|---|---|
| Colección `single_category` sin `restricted_to_sub_category_id` | `ValidationError` | 422 | `errors.collection.subCategoryRequired` |
| `collection_type` no permitido | Pydantic | 422 | `errors.collection.invalidType` |
| Item cuya sub-categoría no coincide con la restricción | `ValidationError` | 422 | `errors.collection.subCategoryMismatch` |
| Proveedor con `name` vacío o solo espacios | Pydantic | 422 | `errors.supplier.nameRequired` |
| Proveedor con `type` no permitido | Pydantic | 422 | `errors.supplier.invalidType` |
| `rating` fuera de 0.00–5.00 | Pydantic | 422 | `errors.supplier.ratingRange` |
| **Proveedor referenciado que se intenta borrar** | `DuplicateError` | 409 | `errors.supplier.hasReferences` |
| Proveedor inexistente | `NotFoundError` | 404 | `errors.supplier.notFound` |
| Wishlist con `catalog_item_id` o `collection_id` inexistente | `NotFoundError` | 404 | `errors.wishlist.referenceNotFound` |
| `priority` fuera de 1–5 | Pydantic | 422 | `errors.wishlist.priorityRange` |
| `urgency` no permitida | Pydantic | 422 | `errors.wishlist.invalidUrgency` |
| Wishlist ya adquirido que se intenta adquirir de nuevo | `DuplicateError` | 409 | `errors.wishlist.alreadyAcquired` |
| Avistamiento sin `price` | Pydantic | 422 | `errors.sighting.priceRequired` |
| `decision` no permitida | Pydantic | 422 | `errors.sighting.invalidDecision` |
| Componente sin `component_name` y sin `standard_component_id` | Pydantic | 422 | `errors.component.nameRequired` |
| Precio histórico duplicado en la clave natural | `DuplicateError` | 409 | `errors.priceHistory.duplicate` |
| Precio histórico con `price` negativo | Pydantic | 422 | `errors.priceHistory.negativePrice` |
| Sin precio compatible al refrescar valor | ninguna: `ValueUpdateResult.updated = False` | 200 | `priceHistory.noCompatiblePrice` |
| `transaction_type` no permitido | Pydantic | 422 | `errors.transaction.invalidType` |
| Accesorio con `quantity_total` negativo o `name` vacío | Pydantic | 422 | `errors.accessory.invalidStock` |
| **Asignación de accesorio sin stock suficiente** | `ValidationError` | 422 | `errors.accessory.insufficientStock` |
| Accesorio ya asignado al mismo item | `DuplicateError` | 409 | `errors.accessory.alreadyAssigned` |
| Accesorio con asignaciones vigentes que se intenta borrar | `DuplicateError` | 409 | `errors.accessory.hasAssignments` |
| Export de entidad inexistente | `NotFoundError` | 404 | `errors.export.notFound` |
| Formato de export no soportado | Pydantic | 422 | `errors.export.invalidFormat` |
| **Import: JSON inválido o estructura no reconocida** | `ValidationError` | 422 | `errors.import.invalidStructure` |
| Import: `schema_version` no soportada | `ValidationError` | 422 | `errors.import.unsupportedVersion` |
| Import: archivo mayor a 10 MB | `FileValidationError` | 413 | `errors.import.fileTooLarge` |
| Import: entidades inválidas dentro de un archivo válido | ninguna: entran en `errors[]` | 200 | `import.partialErrors` |
| Backup inexistente (descarga o restauración) | `NotFoundError` | 404 | `errors.backup.notFound` |
| **Backup corrupto o incompleto** | `ValidationError` | 422 | `errors.backup.corrupted` |
| `pg_dump` no disponible | `ValidationError` → handler dedicado | 503 | `errors.backup.toolUnavailable` |
| Frecuencia de backup no permitida | Pydantic | 422 | `errors.backup.invalidFrequency` |
| Retención fuera de 1–365 | Pydantic | 422 | `errors.backup.invalidRetention` |
| Fallo de backup automático | ninguna: se registra en `last_run_status` | — | `backup.lastRunFailed` |

Se agrega un handler para `DuplicateError` que ya existe (mapea a 409) y uno nuevo `service_unavailable_handler` para la subclase `ToolUnavailableError(DomainError)` → 503, para no forzar 422 en un fallo de entorno.

**Política de borrado de proveedor (R2.10 — decisión cerrada): rechazo con 409.**

Justificación: la desvinculación silenciosa destruye información histórica que el usuario no puede recuperar. Un `collection_item` que pierde su `supplier_id` deja de aparecer en el historial de compras y no hay forma de saber a quién se le compró. El rechazo es reversible por el usuario (puede desactivar el proveedor con `is_active = false`, que es lo que realmente quiere en el 90% de los casos), la desvinculación no lo es. El error 409 incluye el conteo de referencias por tipo (`SupplierReferences`) para que el frontend explique exactamente qué bloquea el borrado y ofrezca desactivar en su lugar.

### Frontend

| Escenario | Manejo |
|---|---|
| Validación local falla | Error inline junto al campo, `aria-invalid` + `aria-describedby`, no se llama a la API |
| 404 | `ErrorMessage` con la clave i18n del dominio y navegación de vuelta al listado |
| 409 (conflicto de negocio) | `ErrorMessage` con el detalle del backend y, cuando aplica, acción alternativa (desactivar proveedor en lugar de borrar) |
| 422 | Se muestra el `detail` del backend; si trae `loc`, se resalta el campo |
| 413 | Mensaje local antes de subir cuando el tamaño se puede medir en el cliente |
| 503 (backup sin `pg_dump`) | Mensaje explicativo con la indicación de instalar el cliente de PostgreSQL |
| Error de red con conexión | `ErrorMessage` con botón de reintento (`refetch` de React Query) |
| Error de red sin conexión | La mutación se encola; toast de "pendiente de sincronización" |
| Mutación en curso | Botón submit deshabilitado + `LoadingSpinner`, `aria-busy` en el contenedor |
| Falla de un gráfico | `ErrorMessage` dentro de ese `ChartContainer`; los demás gráficos siguen visibles |
| **Conflicto de sincronización offline** | La operación se marca `conflict`, el cambio del servidor se conserva, `SyncStatusPanel` la lista y `ConflictResolver` deja elegir entre descartar el cambio local o reaplicarlo sobre el estado nuevo |
| Operación offline rechazada por validación | Se marca `failed` con el motivo, no se reintenta, queda visible en `SyncStatusPanel` con acción de descartar |
| `localStorage` no disponible (tema, idioma) | Se cae al valor por defecto sin error visible |

Todos los mensajes de estado y error se anuncian a través de `LiveRegion`: los errores con `politeness="assertive"`, los éxitos con `"polite"` (R18.2).

## Testing Strategy

### Enfoque

Tres niveles complementarios, más una capa de accesibilidad obligatoria:

- **Unit tests**: ejemplos concretos, casos límite y condiciones de error. Backend con pytest, frontend con Vitest + Testing Library.
- **Property tests**: propiedades universales, mínimo 100 iteraciones. Backend con Hypothesis, frontend con fast-check.
- **Integration tests**: endpoints completos con `AsyncClient` sobre SQLite in-memory; códigos de estado, formato de respuesta y manejo de errores.
- **E2E**: Playwright sobre los flujos de usuario completos.
- **A11y**: axe-core (`jest-axe`) en cada componente React nuevo, sin excepción.

### Backend por dominio

| Dominio | Unit (`tests/unit/test_services/`) | Integration (`tests/integration/test_routes/`) |
|---|---|---|
| Colecciones multi-category | `test_collection_service.py` (ampliado), `test_collection_stats_service.py` | `test_collections.py` (ampliado) |
| Suppliers | `test_supplier_service.py` | `test_suppliers.py` |
| Wishlist + sightings | `test_wishlist_service.py` | `test_wishlist.py`, `test_sightings.py` |
| Componentes | `test_item_component_service.py` | `test_item_components.py` |
| Búsqueda | `test_search_service.py` | `test_search.py` |
| Estadísticas | `test_stats_service.py` | `test_stats.py` |
| Price history | `test_price_history_service.py` | `test_price_history.py` |
| Transacciones | `test_transaction_service.py` | `test_transactions.py` |
| Accesorios | `test_accessory_service.py` | `test_accessories.py` |
| Export | `test_export_service.py` | `test_export.py` |
| Import | `test_json_import_service.py` | `test_import.py` |
| Backups | `test_backup_service.py`, `test_scheduler.py` | `test_backups.py` |
| Cálculos compartidos | `tests/unit/test_utils/test_computations.py` | — |

Casos límite que cada suite debe cubrir de forma explícita: valores nulos en los campos monetarios, colecciones e items sin datos (agregados nulos, conteos en cero), inversión total cero (ROI nulo, no división por cero), y las combinaciones de filtros vacías.

### Cómo se testea lo que depende de PostgreSQL

Tres mecanismos, en orden de preferencia:

1. **Lógica extraída y testeada aislada.** `utils/computations.py` no toca la base: se testea con Hypothesis al 100%. Es donde vive la regla, así que testearla ahí cubre la semántica en ambos dialectos.
2. **Tests de paridad.** Para cada operación con ramificación por dialecto se escribe un test que ejecuta el camino SQLite y compara su resultado contra el valor que produce `computations`. `conftest.py` gana un fixture `dialect_name` para poder parametrizar.
3. **Suite Postgres opt-in.** `@pytest.mark.postgres`, desactivada por defecto en `pyproject.toml` (`addopts = "-m 'not postgres'"`), habilitable con `HOARD_TEST_DATABASE_URL`. Cubre lo que sólo existe en Postgres: los pesos A/B/C del `search_vector`, `pg_trgm`, las columnas `GENERATED`, los triggers y las 4 vistas. Se documenta que sin correr esta suite esas piezas quedan sin verificación real, y se agrega al CI como job separado con un servicio PostgreSQL.

Lo que **no** se pretende: simular `tsvector` en SQLite. La búsqueda en SQLite se verifica como lo que es, un modo degradado, comprobando que la respuesta declara `search_mode = "degraded"`.

### Frontend por dominio

Cada componente nuevo lleva `{Component}.test.tsx` junto al archivo, con:

- renderizado y contenido (queries accesibles: `getByRole`, `getByLabelText`, `getByText`);
- interacciones con `userEvent`;
- estados loading / error / empty;
- operación por teclado (Tab, Enter, Escape, flechas donde aplique);
- roles y etiquetas ARIA;
- **test axe-core obligatorio** (`expect(await axe(container)).toHaveNoViolations()`).

Cada hook nuevo lleva `{hook}.test.ts` con MSW 2 interceptando las llamadas: éxito, error, estado de carga e invalidación de cache.

**Dark mode.** `theme/ThemeProvider.test.tsx`: sin preferencia sigue `prefers-color-scheme` (matchMedia mockeado), preferencia explícita gana, `auto` limpia el storage, valor inválido cae al default, `localStorage` que lanza no rompe. Y una suite `tests/accessibility/theme.a11y.test.tsx` que corre axe sobre cada página en tema claro **y** oscuro, ya que las violaciones de contraste dependen del tema (R8.6).

**i18n.** Se extiende `pages/i18n.property.test.ts` a los 5 idiomas: paridad exacta de claves y ningún valor vacío. Es el mismo chequeo que `npm run lint:i18n`, duplicado a propósito para que falle en la suite y no sólo en el lint.

### Cómo se testean los gráficos

No se testea el SVG que produce Recharts: es implementación de un tercero y no es lo que el usuario asistido consume. Se testea **la alternativa textual**, que es lo que la accesibilidad exige:

- `ChartDataTable.test.tsx`: para un conjunto de series dado, la tabla contiene una fila por punto y los valores coinciden con los datos de entrada.
- `ChartContainer.test.tsx`: hay `<figure>` con `<figcaption>`; el `<summary>` de la tabla es alcanzable por teclado y la abre con Enter; el SVG está `aria-hidden`; sin datos se muestra `EmptyState`; con error se muestra `ErrorMessage` sólo en ese contenedor; con `prefers-reduced-motion` la animación está desactivada.
- `{Chart}.test.tsx` por gráfico: la tabla equivalente refleja los datos del endpoint mockeado con MSW.
- `tests/accessibility/charts.a11y.test.tsx`: axe sobre la sección completa de gráficos en ambos temas.
- Property test: para cualquier arreglo de series, cada serie tiene un `marker` distinto de las demás (la distinción no depende del color, R16.3).

### Cómo se testea el service worker y la cola offline

El service worker no se ejecuta en jsdom. Se separan las responsabilidades:

- **Cola (`offline/queue.ts`)**: se testea con `fake-indexeddb` 6.0 contra una IndexedDB real en memoria. Unit tests de `enqueue`, `listByStatus`, transiciones de estado y conteos. Property test del orden FIFO (Property 9).
- **Sincronización (`offline/sync.ts`)**: MSW simula el backend. Casos: cola vacía; todas aplicadas; error de red a mitad de la cola (las restantes quedan `pending`); 422 → `failed` sin reintento; entidad con `updatedAt` más nuevo en el servidor → `conflict` sin enviar la operación; dos `drainQueue` simultáneos no duplican envíos.
- **Estado de conexión**: `useOnlineStatus.test.ts` disparando los eventos `online`/`offline` de `window`.
- **Configuración del plugin PWA**: se verifica el `vite.config.ts` con un test que valida la forma del objeto de configuración (manifest presente, estrategia por patrón de URL). No se testea Workbox en sí.
- **Comportamiento real del service worker**: E2E con Playwright, que sí corre un navegador real. `tests/e2e/offline.spec.ts` usa `context.setOffline(true)`: se verifica que las páginas cacheadas siguen navegables, que el banner de offline aparece, que una creación queda encolada, y que al volver la conexión la operación se aplica y la cola se vacía.

### E2E (Playwright)

`tests/e2e/`: `suppliers.spec.ts`, `wishlist.spec.ts`, `components.spec.ts`, `search.spec.ts`, `stats.spec.ts`, `theme.spec.ts`, `i18n.spec.ts`, `accessories.spec.ts`, `transfer.spec.ts` (export → import round-trip), `backups.spec.ts`, `charts.spec.ts`, `offline.spec.ts`, `a11y-keyboard.spec.ts` (recorrido completo por teclado, skip link, focus trap en modales, zoom al 200%).

### Coverage

| Bloque | Umbral | Configuración |
|---|---|---|
| Requirements 1–9 (Fase 2 Core) | >80% | `pyproject.toml` `[tool.coverage.report] fail_under = 80` en el job Core; `vitest --coverage` con `thresholds.lines = 80` |
| Requirements 10–18 (Fase 3 Advanced) | >85% | mismo mecanismo elevado a 85 al cerrar el bloque |

El umbral global del repositorio se sube a 80 al terminar el bloque Core y a 85 al terminar el Advanced, en un único paso por bloque, para que el gate no bloquee tareas intermedias. Los archivos de configuración, migraciones y `main.py` se excluyen del cómputo.

## Correctness Properties

_Propiedades de corrección para property-based testing._

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema — una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven de puente entre las especificaciones legibles por humanos y las garantías de corrección verificables por máquina.*

### Property 1: `total_amount` es la suma con nulos como cero

*For any* combinación de `amount`, `shipping_cost`, `tax_amount` y `other_fees`, donde cada valor es un decimal no negativo o nulo, el `total_amount` de la transacción persistida debe ser exactamente igual a la suma de los cuatro valores tratando cada nulo como cero. El resultado debe ser idéntico en el camino PostgreSQL y en el camino SQLite.

**Validates: Requirements 11.4, 11.5**

### Property 2: El stock disponible nunca es negativo y siempre es total menos en uso

*For any* accesorio y cualquier secuencia de asignaciones y desasignaciones válidas, después de cada operación debe cumplirse que `quantity_available == quantity_total - quantity_in_use` y que `quantity_available >= 0`. Cualquier asignación que violaría esa condición debe ser rechazada dejando `quantity_in_use` sin modificar.

**Validates: Requirements 12.8, 12.9**

### Property 3: La importación es idempotente

*For any* documento de exportación válido, importarlo dos veces consecutivas debe producir el mismo estado final que importarlo una sola vez: el conteo de entidades de cada tipo tras la segunda importación debe ser igual al conteo tras la primera.

**Validates: Requirements 14.6, 14.8**

### Property 4: El round-trip export → import preserva las entidades

*For any* colección con sus items y componentes, exportarla a JSON e importar ese documento en una base vacía debe producir un conjunto de entidades equivalente al original en todos los campos exportados.

**Validates: Requirements 13.6, 14.5**

### Property 5: Los resultados filtrados son un subconjunto de los no filtrados

*For any* término de búsqueda y cualquier combinación de filtros, el conjunto de identificadores devuelto con filtros aplicados debe ser un subconjunto del conjunto devuelto con el mismo término y sin filtros, y el orden relativo de los elementos comunes debe conservarse.

**Validates: Requirements 6.5, 6.6**

### Property 6: El ROI es nulo si y sólo si la inversión es cero

*For any* conjunto de collection items con precios de compra y valores de mercado arbitrarios, el `roi_percentage` devuelto debe ser nulo exactamente cuando la inversión total computada es cero, y en cualquier otro caso debe ser igual a `(current_value - total_invested) / total_invested * 100`. Los items sin precio de compra quedan excluidos del cómputo de inversión sin producir error.

**Validates: Requirements 7.3, 7.6, 7.7**

### Property 7: La rotación de backups conserva exactamente min(N, creados)

*For any* retención configurada N ≥ 1 y cualquier cantidad K de backups creados secuencialmente, tras aplicar la retención deben quedar exactamente `min(N, K)` backups, y los que quedan deben ser los de fecha de creación más reciente.

**Validates: Requirements 15.10**

### Property 8: Paridad de claves i18n entre los cinco idiomas

*For any* clave de traducción presente en cualquiera de los cinco archivos de idioma (es, en, pt, fr, de), esa clave debe existir en los otros cuatro y resolver a un string no vacío en todos ellos.

**Validates: Requirements 9.2, 19.1**

### Property 9: La cola offline preserva el orden FIFO de las operaciones aplicadas

*For any* secuencia de operaciones encoladas sin conexión, la secuencia de operaciones enviadas al backend al restablecerse la conexión debe respetar el orden de creación, y la cola sólo debe vaciarse de aquellas operaciones que el backend aceptó correctamente.

**Validates: Requirements 17.6, 17.7**

### Property 10: La completitud del item equivale a la presencia de todos los requeridos

*For any* collection item y cualquier conjunto de componentes registrados, el valor de `is_complete` del item debe ser verdadero exactamente cuando todos los `standard_components` con `component_type == "required"` de su sub-categoría tienen un registro con `is_present` verdadero.

**Validates: Requirements 5.5, 5.6, 5.8**

### Property 11: Marcar como adquirido es una transición de una sola vía

*For any* wishlist item, el primer intento de marcarlo como adquirido debe tener éxito y fijar `acquired_collection_item_id`; cualquier intento posterior debe ser rechazado y dejar `acquired_collection_item_id` con su valor original. Tras la adquisición, el item no debe aparecer en el listado por defecto de deseos pendientes.

**Validates: Requirements 3.7, 3.8, 3.9**

### Property 12: Los agregados de precio son consistentes con los avistamientos

*For any* wishlist item y cualquier conjunto de avistamientos, los agregados devueltos deben cumplir que `min_price <= avg_price <= max_price`, que `total_sightings` es igual a la cantidad de avistamientos y que `available_sightings` es igual a la cantidad con `is_available` verdadero. Sin avistamientos, los tres precios deben ser nulos y ambos conteos cero.

**Validates: Requirements 4.7, 4.8, 4.9**

## Decisiones de Diseño

**1. Política de borrado de proveedor: rechazo con 409 (R2.10).**
La desvinculación destruye información histórica de forma irreversible; el rechazo no destruye nada y el usuario tiene una alternativa mejor a mano (`is_active = false`). El error incluye el conteo de referencias por tipo para que el frontend pueda explicar el bloqueo y ofrecer desactivar.

**2. Claves naturales de merge en el import (R14.6).**
Cada entidad tiene una clave explícita y cerrada, listada en la sección de import. El criterio general: la clave es el conjunto mínimo de campos que un humano usaría para decir "esto es la misma pieza". Para `CatalogItem`, un `sku` o `upc` no vacío tiene prioridad sobre la tupla de título/región/variante, porque es un identificador de fabricante y es más confiable. Los `id` UUID del documento importado **se ignoran** para el matching: importar en otra instancia no debe depender de que los UUID coincidan.

**3. Umbral de similitud fuzzy: 0.3, configurable por entorno (R6.3).**
`SEARCH_SIMILARITY_THRESHOLD` vive en `core/config.py` como variable de entorno, no como constante en el service. 0.3 es el valor por defecto de `pg_trgm` y funciona bien para títulos cortos; el catálogo de cada usuario tiene características distintas, así que debe poder ajustarse sin recompilar. El fuzzy sólo se activa cuando la búsqueda de texto completo no devuelve resultados: correrlo siempre degradaría la precisión de las búsquedas que ya funcionan.

**4. Resolución de conflictos offline: server-wins con marcado (R17.8).**
Ante conflicto, el cambio del servidor se conserva y la operación local se marca `conflict` sin enviarse. Se elige por dos razones: es la única política que nunca pierde datos sin que el usuario lo sepa, y last-write-wins sobre una cola que puede tener horas de antigüedad produciría sobrescrituras silenciosas de cambios más recientes. La detección usa `updatedAt`: es un mecanismo aproximado (no es un ETag), pero suficiente para una instancia self-hosted de un solo usuario, donde el conflicto real es "edité desde el móvil offline y desde el escritorio online".

**5. Definición de "item completo" (R5.5).**
Un collection item es completo cuando **todos** los `standard_components` con `component_type == "required"` de su sub-categoría tienen un `item_component` con `is_present = true`. Los tipos `common`, `optional` y `variant_specific` no afectan la completitud: `common` describe lo habitual, no lo obligatorio, y `variant_specific` depende de la variante concreta, que el modelo actual no vincula a la definición del componente. Un item cuya sub-categoría no define ningún componente `required` se considera completo (cuantificación universal sobre conjunto vacío), que es el comportamiento correcto para categorías donde la completitud no aplica.

**6. Un solo service para wishlist y sightings.**
Los sightings no tienen ciclo de vida independiente: nacen y mueren con su wishlist item, y sus agregados son parte de la lectura del item. Separarlos obligaría a coordinar dos services para una sola operación de lectura.

**7. `CollectionStatsService` separado de `CollectionService`.**
`CollectionService` ya maneja el CRUD; las estadísticas tienen su propia ramificación por dialecto y sus propias consultas de agregación. Mantenerlas aparte respeta la responsabilidad única y evita un archivo de más de 200 líneas.

**8. Recharts para gráficos.**
SVG accesible sin construir la librería a mano. Chart.js queda descartado por renderizar en canvas, opaco para lectores de pantalla; visx por requerir construir ejes, leyendas y tooltips desde primitivas para sólo 4 gráficos.

**9. APScheduler in-process con advisory lock de PostgreSQL.**
Corre en el event loop de uvicorn sin agregar procesos ni configuración externa. El advisory lock resuelve la duplicación con múltiples workers sin depender de que el despliegue use exactamente uno.

**10. Backups con `pg_dump -Fc` en tar.gz con manifest y checksum.**
El formato custom de `pg_dump` permite restaurar selectivamente y comprime mejor que SQL plano. El manifest hace el archivo autodescriptivo y el SHA-256 permite detectar corrupción **antes** de tocar los datos actuales. Si `pg_dump` no está disponible se falla con 503 explícito en lugar de generar un backup incompleto que daría falsa seguridad.

**11. `barras horizontales` en lugar de torta para la distribución por categoría.**
Las tortas son difíciles de etiquetar de forma accesible y de comparar visualmente cuando hay más de 5 segmentos. Las barras horizontales admiten etiquetas de texto completas y se leen igual de bien en la tabla equivalente.

**12. `DELETE` de componente devuelve 200 con el nuevo estado de completitud.**
Un 204 obligaría al cliente a hacer un refetch para conocer un valor que el servidor ya calculó en esa misma operación. Devolver `CompletenessResult` evita el round-trip extra y cumple R5.7 sin recargar la página.

**13. `preview` y `execute` del import comparten el planificador.**
La vista previa no es una estimación separada: es exactamente el plan que se va a ejecutar, computado con el mismo código. Eso hace estructuralmente imposible que la vista previa mienta sobre lo que va a pasar.

**14. El header del CSV exportado se deriva de las constantes del importador.**
`ExportService` lee `CsvImportService.REQUIRED_COLUMNS | OPTIONAL_COLUMNS` en lugar de declarar su propia lista. Así el round-trip CSV no puede romperse por una columna agregada en un lado y no en el otro.

**15. `gift_received` y `gift_given` se clasifican como ingresos en el cálculo de inversión.**
Su `amount` habitual es cero o simbólico y no representan un desembolso. El criterio está en la constante `INFLOW_TYPES`, no repartido por el código, de modo que revisarlo sea un cambio de una línea.

## Dependencias Nuevas

### Backend (`backend/requirements.txt`)

| Dependencia | Versión | Motivo |
|---|---|---|
| `apscheduler` | `==3.10.4` | Scheduler in-process para los backups automáticos (R15.8, R15.9) |
| `email-validator` | `==2.2.0` | Requerido por `EmailStr` en `SupplierBase` |
| `pytest-postgresql` | `==6.1.1` | Sólo dev: levanta el PostgreSQL de la suite `@pytest.mark.postgres` |

**Observación sobre dependencias ya presentes.** `hypothesis` y `aiosqlite` no son nuevas: `backend/requirements-dev.txt` ya las declara (`hypothesis>=6.92`, `aiosqlite>=0.19`), junto con `pytest>=7.4`, `pytest-asyncio>=0.23`, `httpx>=0.25` y `pytest-cov>=4.1`. Todas están con rangos abiertos; lo único que este spec propone sobre ellas es pinearlas a versiones exactas (`hypothesis==6.122.3`, `aiosqlite==0.20.0`) para que la suite sea reproducible. No es una instalación nueva.

No se agrega ninguna librería de dump/restore: `pg_dump` y `pg_restore` se invocan por `subprocess`, y `tarfile`, `hashlib`, `shutil` y `json` son de la biblioteca estándar. La imagen del backend debe incluir `postgresql-client` (cambio en `backend/Dockerfile`, no una dependencia de Python).

### Frontend (`frontend/package.json`)

| Dependencia | Versión | Tipo | Motivo |
|---|---|---|---|
| `recharts` | `2.13.3` | prod | Gráficos SVG accesibles (R16) |
| `idb` | `8.0.0` | prod | Wrapper tipado de IndexedDB para la cola offline y el persister de React Query (R17.6) |
| `@tanstack/react-query-persist-client` | `5.62.0` | prod | Persistencia de la cache de lectura para el modo sin conexión (R17.3, R17.4) |
| `vite-plugin-pwa` | `0.21.1` | dev | Manifest + service worker con Workbox (R17.1, R17.2) |
| `workbox-window` | `7.3.0` | prod | Aviso de actualización del service worker |
| `fake-indexeddb` | `6.0.0` | dev | IndexedDB en memoria para testear la cola en jsdom |
| `@vitest/coverage-v8` | `2.1.8` | dev | Requerido por `vitest --coverage` para los umbrales de R19.4 y R19.5 |

Total agregado al bundle de producción: aproximadamente 115 kB gzip, dominado por Recharts. `idb` y `workbox-window` suman menos de 5 kB. Recharts se carga con `React.lazy` en la sección de gráficos para no penalizar el primer render de las páginas que no la usan.

## Orden de Implementación Sugerido

El orden responde a dependencias reales entre dominios, no a la numeración de los requirements.

**Bloque 0 — Cimientos (habilita todo lo demás)**
1. Los 4 modelos SQLAlchemy faltantes y las relaciones en modelos existentes. Sin el mapeo ORM no se puede escribir ningún service de Fase 3. Aquí también va la migración `002_app_settings.py` con su modelo `AppSetting`: es la única tabla nueva del spec y conviene tenerla en los cimientos para que el pipeline de migraciones quede resuelto de entrada, aunque su primer consumidor (backups, R15) aparezca recién en el paso 17.
2. `utils/computations.py` y `core/dialect.py`, con sus tests de propiedades. Todo lo que ramifica por dialecto depende de esta capa; construirla después significaría reescribir services.
3. Componentes UI transversales: `LiveRegion`, `Table`, `Tooltip`, `SkipLink`, `Badge`. Los usan todas las páginas nuevas.

**Bloque 1 — Fase 2 Core**
4. **Suppliers** (R2). Va primero porque los sightings, los accesorios y las transacciones referencian `supplier_id`, y el historial de compras necesita el modelo mapeado.
5. **Wishlist + sightings** (R3, R4). Depende de suppliers para el campo `supplier_id` de los avistamientos y de su UI para el selector.
6. **Componentes de items** (R5). Define `is_complete`, que las estadísticas consumen como `complete_items`.
7. **Colecciones multi-category** (R1). El agrupado por categoría y las estadísticas de colección dependen de la completitud del paso anterior.
8. **Búsqueda avanzada** (R6). Independiente de los anteriores, pero necesita la capa de dialecto del bloque 0.
9. **Dark mode** (R8) e **idiomas pt/fr/de** (R9). Antes de los gráficos y de la auditoría final: agregar temas y claves después obligaría a revisitar cada componente construido en el medio.

**Bloque 2 — Fase 3 Advanced**
10. **Price history** (R10). Alimenta `current_market_value`, que la valorización necesita.
11. **Transacciones** (R11). Redefine la inversión real y el ROI del item. Debe estar antes de estadísticas, porque `StatsService` decide entre transacciones y `purchase_price`.
12. **Estadísticas** (R7). Aquí, no en el bloque Core, porque sus cifras dependen de 10 y 11. Si se construyera antes habría que reescribir los cálculos.
13. **Gráficos** (R16). Consumen exclusivamente los endpoints de estadísticas: sin 12 no hay nada que graficar.
14. **Accesorios y stock** (R12). Independiente de los anteriores; depende de suppliers (paso 4).
15. **Export** (R13). Antes del import: sin export no hay forma de generar los documentos con los que testear el round-trip.
16. **Import** (R14). Necesita export (15) para el round-trip y los services de wishlist (5) y suppliers (4) para poder importar esas entidades.
17. **Backups + scheduler** (R15). Va después del import porque reutiliza el patrón de validación de archivo subido y porque su restauración es la operación más destructiva del sistema: conviene construirla cuando el resto ya es estable.
18. **PWA y modo sin conexión** (R17). Último de los dominios funcionales: la cola debe interceptar mutaciones de todos los dominios anteriores, así que necesita que existan.
19. **Accesibilidad avanzada y auditoría** (R18) y cierre de **estándares transversales** (R19). La auditoría completa se corre al final, sobre la superficie total, en ambos temas y en los cinco idiomas, y ahí se elevan los umbrales de coverage a 80 y 85.

Dependencias criticas resumidas: `modelos + computations` → todo; `suppliers` → `wishlist/sightings`, `accesorios`, `transacciones`; `componentes` → `stats.complete_items`; `transacciones + price history` → `stats` → `gráficos`; `export` → `import`; todos los dominios → `offline`; todo → `auditoría a11y`.
