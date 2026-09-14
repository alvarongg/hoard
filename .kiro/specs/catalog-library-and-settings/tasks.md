# Tareas — Biblioteca de Catálogos Oficiales y Configuración del Sistema

- [ ] 1. Definir el formato de catálogo del repo
  - [ ] 1.1 Crear `catalogs/` con `manifest.json` de ejemplo y un `nes.v1.json`
    mínimo (2-3 ítems, incluyendo uno "planned but unreleased" y uno con
    `country_of_manufacture`) para fijar el contrato.
  - [ ] 1.2 Documentar el envelope `entity_type:"catalog"` y las claves de
    `custom_fields` (`released_regions`, `planned_regions`, `unreleased_in`,
    `country_of_manufacture`, `per_region_release`) en `catalogs/README.md`.
  - _Requisitos: 1.1–1.8_

- [ ] 2. Esquemas y validación backend
  - [ ] 2.1 Crear `api/schemas/catalog_import.py` con `CatalogEnvelope` y modelos
    de ítem (Pydantic), reutilizando `ImportPreview`/`BatchImportResult`.
  - [ ] 2.2 Tests unitarios del parser: JSON inválido, `schema_version` no
    soportado, `entity_type` != "catalog".
  - _Requisitos: 1.3, 1.8, 4.3, 6.1_

- [ ] 3. Servicio de import de catálogo
  - [ ] 3.1 `api/services/catalog_import_service.py`: `preview`/`execute` con
    resolución/creación de sub-categoría y create/update/skip idempotente por
    clave natural.
  - [ ] 3.2 Setear `is_official`, `source_type/name/url`, `version` en `Catalog`
    al ejecutar.
  - [ ] 3.3 Tests unitarios: create/update/skip, resolución de sub-categoría,
    atomicidad.
  - _Requisitos: 3.3, 3.4, 3.7, 4.2, 4.4, 6.1_

- [ ] 4. Endpoints de biblioteca e import de catálogo
  - [ ] 4.1 `api/routes/catalog_library.py`: `GET /catalog-library/manifest`,
    `POST /catalog-library/load` (descarga server-side + validación de checksum).
  - [ ] 4.2 `POST /catalog-import/preview` y `/catalog-import/execute` para import
    desde archivo, con guard de tamaño (10 MB) como el import existente.
  - [ ] 4.3 Registrar rutas en el router principal y dependencias.
  - [ ] 4.4 Tests de endpoints: carga exitosa, checksum mismatch, fallo de red.
  - _Requisitos: 3.1, 3.2, 3.5, 3.6, 4.2, 6.1_

- [ ] 5. Generadores offline (scripts/)
  - [ ] 5.1 `scripts/gen_catalog/wikidata.py`: cliente SPARQL/MediaWiki API (sin
    HTML), con dependencias fijadas.
  - [ ] 5.2 `scripts/gen_catalog/map_nes.py`: mapear filas a ítems (título +
    alternos por región, dev/publisher por región, fechas JP/NA/PAL, unreleased).
  - [ ] 5.3 `scripts/gen_catalog/map_genesis.py`: idem + intento de
    `country_of_manufacture` (nulo si no se conoce).
  - [ ] 5.4 `scripts/gen_catalog/build.py`: CLI determinista que escribe el JSON,
    recalcula checksum y actualiza `manifest.json`; reporte de campos faltantes.
  - [ ] 5.5 `scripts/gen_catalog/README.md`: términos de uso, fragilidad, cómo
    correrlo local/Unraid.
  - [ ] 5.6 Test de mapeo con respuesta SPARQL grabada (sin red), verifica
    determinismo y nulos.
  - _Requisitos: 2.1–2.7, 6.1_

- [ ] 6. Generar los catálogos iniciales y commitearlos
  - [ ] 6.1 Correr el generador de NES/Famicom → `catalogs/nes.v1.json` + manifest.
  - [ ] 6.2 Correr el generador de Genesis/Mega Drive → `catalogs/genesis.v1.json`
    + manifest.
  - [ ] 6.3 Revisar el diff de datos (spot-check de regiones/no-lanzados/país).
  - _Requisitos: 1.1, 1.4–1.7, 2.3, 2.4_

- [ ] 7. Frontend — hook y componentes de catálogos oficiales
  - [ ] 7.1 `useOfficialCatalogs()` (React Query) contra el endpoint de manifest.
  - [ ] 7.2 `OfficialCatalogList` + `LoadCatalogButton` con preview
    (create/update/skip) y manejo de error de red/checksum.
  - [ ] 7.3 Tests de render de la lista y del flujo de carga (éxito + error).
  - _Requisitos: 3.1, 3.2, 3.3, 3.5, 6.2_

- [ ] 8. Frontend — sección Configuración del sistema y rework de navegación
  - [ ] 8.1 Crear `SettingsPage` con sub-secciones General / Catálogos / Datos.
  - [ ] 8.2 Mover `LanguageSelector` y `ThemeToggle` a General (dejar acceso
    rápido opcional en el header).
  - [ ] 8.3 Reubicar bajo Configuración: catálogos oficiales, crear catálogo
    (reusar `CatalogManagementPage`), importar catálogo, import/export, backups.
  - [ ] 8.4 Partir `Navigation.tsx` en nav principal (Colección) + entrada a
    Configuración; agregar rutas `/settings/*` en `App.tsx` y **redirects** desde
    las rutas viejas.
  - [ ] 8.5 Preservar a11y (roles/labels de nav, foco, skip-link).
  - _Requisitos: 4.1, 5.1–5.4, 5.6_

- [ ] 9. i18n
  - [ ] 9.1 Agregar claves `settings.*`, `catalogLibrary.*`, `navigation.settings`
    a los 5 locales (es/en/pt/fr/de) manteniendo orden y paridad.
  - [ ] 9.2 Verificar que `lint:i18n` pasa.
  - _Requisitos: 5.5_

- [ ] 10. Verificación y entrega
  - [ ] 10.1 Gate local: `tsc --noEmit`, `lint`, `lint:i18n`, tests unitarios.
  - [ ] 10.2 Correr los E2E existentes en local/Unraid (sin Actions); ajustar
    selectores si la nav cambió.
  - [ ] 10.3 Crear rama feature nombrada, commit, y abrir PR con `gh` (no push a
    `main`). Cualquier workflow nuevo queda `workflow_dispatch`.
  - _Requisitos: 6.1–6.5_
