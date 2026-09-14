# Diseño — Biblioteca de Catálogos Oficiales y Configuración del Sistema

## Visión general

Se añaden cuatro piezas sobre la base existente, sin migración de esquema mayor:

1. **Formato de catálogo hospedado en el repo**: `catalogs/manifest.json` + un
   archivo JSON por catálogo, con envelope `entity_type: "catalog"`.
2. **Generadores offline** (`scripts/`) que consultan Wikidata/Wikipedia por API y
   escriben los archivos de catálogo de NES y Genesis, commiteados al repo.
3. **Loader en la app**: servicio + endpoints que bajan el manifest/archivo por
   HTTP, validan y hacen import idempotente reutilizando `BatchImportResult`.
4. **Rework de navegación**: separar "Colección" de "Configuración del sistema".

## Anclaje al código existente (verificado)

- `backend/api/models/catalog.py`: `Catalog` (con `sub_category_id` FK
  obligatorio, `version`, `source_type/name/url`, `is_official`, `is_public`) y
  `CatalogItem` (ya trae `alternate_titles`, `region`, `language_codes`,
  `manufacturer/publisher/developer`, `release_date`, `rarity`, `production_run`,
  `is_prototype`, `related_items_group`, `custom_fields` JSON no-null). → El
  catálogo mapea a estos campos tal cual; no hace falta migración de columnas.
- `backend/api/routes/import_data.py` + `services/json_import_service.py`: el
  import actual es `POST /import/preview` y `/import/execute`, envelope
  `{schema_version:"1.0", entity_type:"collection", collection, items[]}`. → El
  loader de catálogo es **un flujo hermano**, no una modificación de éste: nuevo
  `entity_type:"catalog"` y su propio servicio/rutas.
- `frontend/src/App.tsx`: rutas planas; `settings/backups` es la única bajo
  `settings/`. `Navigation.tsx`: lista plana de 11 links. → El rework agrupa bajo
  `/settings/*` y parte la navegación en dos áreas.
- i18n: 5 locales en `frontend/public/locales/*/translation.json`, con `lint:i18n`
  chequeando paridad.

## Formato de catálogo del repo

### Ubicación

```
catalogs/
  manifest.json
  nes.v1.json
  genesis.v1.json
```

### manifest.json

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-09-14T00:00:00Z",
  "catalogs": [
    {
      "id": "nes",
      "name": "Nintendo Entertainment System / Famicom",
      "description": "Juegos licenciados de NES/Famicom en cartucho",
      "system": "nes",
      "version": "1.0.0",
      "item_count": 1370,
      "updated_at": "2026-09-14T00:00:00Z",
      "path": "nes.v1.json",
      "checksum": "sha256:...."
    },
    { "id": "genesis", "system": "genesis", "path": "genesis.v1.json", "...": "..." }
  ]
}
```

### Archivo de catálogo (`nes.v1.json`)

```json
{
  "schema_version": "1.0",
  "entity_type": "catalog",
  "catalog": {
    "id": "nes",
    "name": "Nintendo Entertainment System / Famicom",
    "system": "nes",
    "version": "1.0.0",
    "source_type": "wikidata",
    "source_name": "Wikipedia/Wikidata — List of NES games",
    "source_url": "https://www.wikidata.org/...",
    "target_sub_category": { "category": "Video Games", "sub_category": "NES" }
  },
  "items": [
    {
      "external_id": "wikidata:Q12345",
      "title": "Castlevania",
      "alternate_titles": ["Akumajō Dracula (JP)"],
      "region": "JP",
      "language_codes": ["ja"],
      "developer": "Konami",
      "publisher": "Konami",
      "release_date": "1986-09-26",
      "related_items_group": "castlevania-1986",
      "is_prototype": false,
      "custom_fields": {
        "released_regions": ["JP", "NA", "PAL"],
        "planned_regions": [],
        "unreleased_in": [],
        "country_of_manufacture": null,
        "per_region_release": { "JP": "1986-09-26", "NA": "1987-05-01", "PAL": "1988-12-19" }
      }
    }
  ]
}
```

Notas de diseño:
- Cada variante regional relevante es un `CatalogItem` propio con su `region`,
  agrupadas por `related_items_group` (Req 1.5). Para juegos sin variantes
  regionales significativas se emite un único ítem con `custom_fields.released_regions`.
- "Planeado pero no salió" vive en `custom_fields.planned_regions` +
  `unreleased_in` (Req 1.6). Nunca se fabrica una `release_date` falsa.
- Grados de condición y precios **no** aparecen aquí (son del ejemplar).

## Generadores (scripts/)

```
scripts/
  gen_catalog/
    __init__.py
    wikidata.py        # cliente SPARQL/MediaWiki API (sin HTML scraping)
    map_nes.py         # mapea filas -> items del catálogo NES
    map_genesis.py     # idem Genesis, intenta country_of_manufacture
    build.py           # CLI: python -m scripts.gen_catalog.build --system nes
    README.md          # términos de uso, fragilidad, versiones fijadas
```

- **Fuente**: Wikidata vía SPARQL (`query.wikidata.org`) para propiedades
  estructuradas (plataforma, desarrollador, editor, fecha de publicación por
  región, país de origen), con la API de MediaWiki como respaldo para listas.
  Se evita parsear el HTML renderizado (Req 2.1).
- **Determinismo** (Req 2.6): ordenar ítems por `(title, region)`, claves JSON
  ordenadas, `ensure_ascii=false`, indent fijo. Así el diff del PR es legible.
- **Campos faltantes** (Req 2.5): se dejan nulos y se listan en un reporte
  `scripts/gen_catalog/out/<system>.report.txt` (no commiteado).
- **Ejecución**: local/Unraid, nunca en runtime de la app (Req 2.2).
- Tras generar, `build.py` recalcula el `checksum` y actualiza `manifest.json`.

## Backend — loader de catálogos oficiales

### Esquemas (`api/schemas/catalog_import.py`)

- `CatalogEnvelope` (Pydantic): `schema_version`, `entity_type` (fijo
  `"catalog"`), `catalog`, `items[]`.
- Reutiliza `ImportPreview` y `BatchImportResult` existentes para la salida.

### Servicio (`api/services/catalog_import_service.py`)

Análogo a `JsonImportService` pero para `entity_type:"catalog"`:
- `_parse_envelope`: valida tamaño, JSON, `schema_version`, `entity_type=="catalog"`.
- `_resolve_sub_category`: dado `target_sub_category`, resuelve o crea la
  sub-categoría (porque `Catalog.sub_category_id` es obligatorio — Req 3.4).
- `_plan`: resuelve `Catalog` por clave natural (system+version o name), y cada
  `CatalogItem` por clave natural (`catalog_id` + `external_id`/`title`+`region`);
  create/update/skip idempotente (Req 3.3).
- `execute`: setea `is_official`, `source_type/name/url`, `version` en `Catalog`
  (Req 3.7); commit atómico.

### Endpoints (`api/routes/catalog_library.py`)

- `GET  /catalog-library/manifest` — proxy/caché opcional del manifest (o el
  front lo baja directo por HTTP; ver decisión abajo).
- `POST /catalog-library/load` — body `{catalog_id, manifest_url?}`: baja el
  archivo, valida checksum (Req 3.2/3.5), corre `preview` o `execute`.
- `POST /catalog-import/preview` y `/catalog-import/execute` — import desde
  archivo subido (Req 4.2), mismo servicio.

**Decisión (descarga HTTP):** el **backend** hace la descarga del repo (server-side
fetch) para poder validar checksum y evitar problemas de CORS con `raw.githubusercontent`.
La `manifest_url` por defecto apunta a la versión fijada del repo del proyecto
(rama/tag), configurable (Req 3.6).

## Frontend — Configuración del sistema

### Navegación (Req 5)

- Nueva página `SettingsPage` en `/settings` con sub-secciones:
  - **General**: idioma (mover `LanguageSelector`), tema (mover `ThemeToggle`).
  - **Catálogos**: "Catálogos oficiales" (lista del manifest + botón Cargar),
    "Crear catálogo" (reusa `CatalogManagementPage`), "Importar catálogo"
    (archivo), y una tarjeta informativa "Generar catálogos" (explica que se
    generan offline vía `scripts/`, sin acción en runtime).
  - **Datos**: Import (colección), Export, Backups.
- `Navigation.tsx` se parte en:
  - Nav principal (Colección): Home, Colecciones, Catálogos, Wishlist, Búsqueda,
    Stats, Accesorios.
  - Acceso a **Configuración** (icono/engranaje) que lleva a `/settings`.
- Rutas: se agregan `/settings`, `/settings/catalogs`, `/settings/catalogs/official`,
  `/settings/data`. Las rutas viejas (`/import`, `/export`, `/settings/backups`,
  `/catalogs/manage`) se **redirigen** a sus nuevas ubicaciones bajo `/settings`
  para no romper enlaces (Req 5.4). Header conserva accesos rápidos de tema/idioma
  (Req 5.3), pero el canónico vive en Configuración.

### Componentes/hook nuevos

- `useOfficialCatalogs()` (React Query): `GET manifest` → lista.
- `OfficialCatalogList` + `LoadCatalogButton`: dispara `POST /catalog-library/load`,
  muestra preview (create/update/skip) y confirma; maneja error de red/checksum
  (Req 3.5, 6.2).

### i18n (Req 5.5)

- Nuevas claves bajo `settings.*`, `catalogLibrary.*`, `navigation.settings`, en
  los 5 locales, con script Python `object_pairs_hook=collections.OrderedDict`
  para mantener orden y paridad; `lint:i18n` debe pasar.

## Manejo de errores

- Parser: JSON inválido / `schema_version` no soportado / `entity_type` incorrecto
  → 400 con mensaje claro (Req 1.8, 4.3).
- Loader: fallo de descarga o checksum mismatch → abortar, sin escritura parcial
  (Req 3.5). Import atómico por transacción.
- Generador: campo irresoluble → nulo + entrada en el reporte (Req 2.5).

## Estrategia de testing (Req 6)

- **Backend unit**: `catalog_import_service` (parse/validate, resolve sub-category,
  create/update/skip idempotente, checksum mismatch). Fixtures con envelopes
  mínimos de NES y Genesis (incluyendo un caso "planned but unreleased" y uno con
  `country_of_manufacture`).
- **Generadores**: test con una respuesta SPARQL fija (grabada) → verifica mapeo
  determinista y que campos faltantes quedan nulos, sin red en el test.
- **Frontend**: test de `OfficialCatalogList` (render del manifest) y del flujo de
  carga con mock de red exitoso y con error/checksum.
- **Gate local**: `tsc --noEmit`, `lint`, `lint:i18n`, unit; E2E existentes en
  local/Unraid (skill `run-playwright-e2e-on-unraid-selfhosted`). Sin Actions.

## Decisiones y trade-offs

- **Manifest + archivo por catálogo** (elegido) en vez de un único JSON: escala a
  muchos catálogos y permite listar/elegir antes de bajar el archivo grande.
- **Wikidata/API** (elegido) en vez de scrapear HTML: más estable y respeta ToS;
  costo: no todos los campos (p.ej. país de fabricación por ejemplar) existen en
  la fuente — se dejan nulos por diseño.
- **Descarga server-side** en vez de fetch directo del browser: habilita validar
  checksum y evita CORS; costo: el backend necesita salida HTTP al repo.
- **Flujo de import de catálogo separado** del de colección: evita romper el
  contrato `entity_type:"collection"` existente y sus tests.
