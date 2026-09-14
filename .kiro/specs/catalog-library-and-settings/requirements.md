# Requisitos — Biblioteca de Catálogos Oficiales y Configuración del Sistema

## Introducción

Hoard hoy permite crear catálogos y colecciones manualmente e importar/exportar
datos del usuario. Faltan tres capacidades: (1) **catálogos "oficiales"
versionados hospedados en el propio repositorio** que cualquier instalación de
la app pueda listar y cargar por HTTP; (2) **generadores de datos reproducibles**
que produzcan esos catálogos a partir de fuentes públicas (empezando por
**Famicom/NES** y **Sega Genesis/Mega Drive**), obteniendo los datos vía la
**API/dumps estructurados de Wikipedia/Wikidata** en vez de scrapear HTML; y
(3) una **separación explícita entre la UI de "Colección" (operar la colección)
y la UI de "Configuración del sistema"** (idioma, tema claro/oscuro, y toda la
gestión de catálogos: cargar/crear/importar/generar).

Este spec cubre las tres cosas en una sola entrega.

### Distinción conceptual clave (catálogo maestro vs ejemplar)

- El **catálogo maestro** describe el *producto*: título, títulos alternativos por
  región, regiones donde salió / regiones donde se planeó pero no salió,
  desarrollador, publisher (por región), fabricante, país de fabricación,
  fecha de lanzamiento, tirada, flags (prototipo, no lanzado).
- El **estado del ejemplar** (condición CIB/mint, precio pagado, valor estimado,
  aditamentos que YO tengo) pertenece a `collection_items`, NO al catálogo. El
  catálogo no almacena grados de condición ni precios; esos son atributos del
  ejemplar poseído por el usuario.

### Hallazgos de origen de datos (verificados)

- La tabla de juegos licenciados de Wikipedia expone, por fila: `Title(s)` con
  títulos alternativos por región inline, `Developer(s)`, `Publisher(s)` con
  etiquetas de región (p.ej. `Taito^{JP}`, `Nintendo^{NA/PAL}`), `First released`
  y fechas por región **JP / NA / PAL**, donde `Unreleased` marca las regiones a
  las que un juego nunca llegó. Hay secciones separadas para juegos **no
  lanzados** (con la región prevista), **no licenciados**, **solo-Famicom** y
  **compilaciones**. De ahí se deriva "salió en" y "planeado pero no salió".
- Wikipedia/Wikidata **no** contienen grados de condición, precios ni país de
  fabricación por ejemplar — coherente con la distinción de arriba. El país de
  fabricación (clave para diferencias de precio, p.ej. cartuchos brasileños de
  Genesis) se modela como campo del catálogo cuando se conoce a nivel producto,
  o queda para el ejemplar cuando es específico de la copia.

### Restricciones del entorno (vigentes)

- **Sin nube / sin minutos de GitHub Actions**: los generadores corren local o en
  Unraid; cualquier workflow de Actions queda `workflow_dispatch` manual.
- Push sólo a rama feature nombrada; PR con `gh`; nunca push a `main`.
- Responder e escribir specs en **español**.

## Requisitos

### Requisito 1 — Formato de catálogo hospedable en el repo

**Historia:** Como mantenedor del proyecto, quiero un formato de archivo de
catálogo versionado y un índice en el repositorio, para que cualquier instalación
de la app pueda descubrir y cargar catálogos oficiales por HTTP sin depender de un
backend central.

#### Criterios de aceptación

1. CUANDO se define el formato de catálogo ENTONCES DEBERÁ existir un
   `manifest.json` en una ruta fija del repo (p.ej. `catalogs/manifest.json`) que
   liste cada catálogo disponible con: `id/slug`, `name`, `description`,
   `system` (p.ej. `nes`, `genesis`), `version` (semver), `item_count`,
   `updated_at`, la ruta relativa del archivo del catálogo, y un `checksum`
   (sha256) del archivo.
2. CUANDO se define el formato de catálogo ENTONCES cada catálogo DEBERÁ vivir en
   su propio archivo JSON (p.ej. `catalogs/nes.v1.json`), separado del manifest.
3. CUANDO se diseña el envelope del catálogo ENTONCES DEBERÁ declarar
   `schema_version` y `entity_type: "catalog"` (distinto del import de colección
   existente, cuyo `entity_type` es `"collection"`), para que ambos flujos no se
   confundan.
4. CUANDO un ítem del catálogo se serializa ENTONCES DEBERÁ mapear a los campos
   existentes de `CatalogItem` (`title`, `alternate_titles`, `region`,
   `language`/`language_codes`, `manufacturer`, `publisher`, `developer`,
   `release_date`, `rarity`, `production_run`, `is_prototype`,
   `related_items_group`, `cover_image_url`, `custom_fields`) sin requerir una
   migración de esquema mayor.
5. CUANDO un juego salió en varias regiones ENTONCES sus variantes regionales
   DEBERÁN compartir un mismo `related_items_group` para poder agruparlas.
6. CUANDO un juego se planeó para una región pero no salió allí ENTONCES el
   catálogo DEBERÁ registrarlo en `custom_fields` con al menos
   `planned_regions` y un flag `unreleased_in` (o equivalente), sin inventar una
   fecha de lanzamiento.
7. CUANDO se conoce el país de fabricación a nivel producto ENTONCES DEBERÁ
   guardarse en `custom_fields.country_of_manufacture`; los tiers de precio por
   región/país NO se guardan en el catálogo (son del ejemplar).
8. CUANDO el manifest o un archivo de catálogo se validan ENTONCES un JSON mal
   formado, un `schema_version` no soportado o un `entity_type` incorrecto
   DEBERÁN ser rechazados con un error claro.

### Requisito 2 — Generadores de datos (NES/Famicom y Genesis/Mega Drive)

**Historia:** Como mantenedor, quiero scripts reproducibles que generen los
archivos de catálogo a partir de fuentes públicas estructuradas, para poder
revisar los datos en el PR y regenerarlos sin scraping frágil de HTML.

#### Criterios de aceptación

1. CUANDO se generan los catálogos ENTONCES los datos DEBERÁN obtenerse vía la
   **API/dumps estructurados de Wikipedia/Wikidata** (p.ej. la API de MediaWiki o
   SPARQL de Wikidata), NO parseando el HTML renderizado de la página.
2. CUANDO corre un generador ENTONCES DEBERÁ ejecutarse **offline/local** (script
   en el repo bajo `scripts/`), producir el archivo de catálogo JSON, y dejarlo
   commiteado; la app NUNCA scrapea ni consulta la fuente en runtime.
3. CUANDO el generador mapea una fila ENTONCES DEBERÁ extraer título +
   títulos alternativos por región, developer, publisher(s) por región, fechas
   por región (JP/NA/PAL), y marcar como no lanzadas las regiones con
   `Unreleased`.
4. CUANDO el generador procesa Genesis/Mega Drive ENTONCES DEBERÁ además intentar
   poblar `country_of_manufacture` cuando la fuente lo exponga, y dejarlo vacío
   (no adivinado) cuando no.
5. CUANDO un generador falla al resolver un campo ENTONCES DEBERÁ omitir ese campo
   (dejarlo nulo) en vez de inventar un valor, y registrar el caso para revisión.
6. CUANDO se regenera un catálogo existente ENTONCES el generador DEBERÁ producir
   una salida determinista (mismo orden, mismas claves) para que los diffs del PR
   sean revisables.
7. CUANDO se documenta el generador ENTONCES DEBERÁ advertirse sobre los términos
   de uso de la fuente y el riesgo de fragilidad, y fijarse las versiones exactas
   de dependencias nuevas.

### Requisito 3 — Loader de catálogos oficiales en la app

**Historia:** Como usuario, quiero ver la lista de catálogos oficiales publicados
en el repo y cargar uno en mi instalación con un clic, para no tener que crear los
ítems a mano.

#### Criterios de aceptación

1. CUANDO abro la sección de catálogos oficiales ENTONCES la app DEBERÁ descargar
   el `manifest.json` por HTTP y listar los catálogos disponibles con nombre,
   sistema, versión y cantidad de ítems.
2. CUANDO elijo cargar un catálogo ENTONCES la app DEBERÁ descargar su archivo,
   validar `schema_version`/`entity_type`/`checksum`, y luego importarlo.
3. CUANDO importo un catálogo ya presente ENTONCES la operación DEBERÁ ser
   idempotente y deduplicar por clave natural, reportando conteos
   creados/actualizados/omitidos (reutilizando el patrón `BatchImportResult`).
4. CUANDO un catálogo oficial requiere una sub-categoría ENTONCES la app DEBERÁ
   resolver o crear la sub-categoría destino de forma explícita (dado que
   `Catalog.sub_category_id` es obligatorio), sin dejar el catálogo huérfano.
5. CUANDO la descarga HTTP falla o el checksum no coincide ENTONCES la app DEBERÁ
   abortar la importación y mostrar un error accionable, sin dejar datos a medias.
6. CUANDO la fuente del manifest se configura ENTONCES DEBERÁ poder apuntar a la
   URL raw del repo (rama/tag), y por defecto usar la versión fijada del propio
   repo del proyecto.
7. CUANDO un catálogo se importa correctamente ENTONCES DEBERÁ marcarse
   `is_official = true` y registrarse `source_type`/`source_name`/`source_url` y
   `version` en el registro `Catalog`.

### Requisito 4 — Creación manual e importación externa de catálogos

**Historia:** Como usuario, quiero crear catálogos nuevos a mano e importar
catálogos externos desde un archivo, además de los oficiales del repo.

#### Criterios de aceptación

1. CUANDO creo un catálogo manualmente ENTONCES DEBERÁ poder hacerlo desde la
   sección de Configuración, reutilizando la gestión de catálogos existente.
2. CUANDO importo un catálogo desde archivo ENTONCES el sistema DEBERÁ aceptar el
   mismo formato de envelope `entity_type: "catalog"` definido en el Requisito 1,
   con preview (dry-run) y execute, análogo al import de colección actual.
3. CUANDO un archivo de catálogo importado es inválido ENTONCES DEBERÁ rechazarse
   con errores por ítem, sin escribir nada (preview) o de forma atómica (execute).
4. CUANDO importo un catálogo que NO es oficial ENTONCES `is_official` DEBERÁ
   permanecer en `false`.

### Requisito 5 — Separación Colección vs Configuración del sistema

**Historia:** Como usuario, quiero que la app separe claramente "operar mi
colección" de "configurar el sistema", para que la navegación no mezcle tareas de
uso diario con ajustes y gestión de datos.

#### Criterios de aceptación

1. CUANDO navego la app ENTONCES DEBERÁ existir un área de **Configuración del
   sistema** que agrupe: idioma, tema (claro/oscuro), gestión de catálogos
   (oficiales/crear/importar/generar-info), import, export y backups.
2. CUANDO estoy en la vista de Colección ENTONCES la navegación principal DEBERÁ
   contener sólo tareas de operar la colección (colecciones, catálogos de
   consulta, wishlist, búsqueda, stats, accesorios), sin los ajustes del sistema.
3. CUANDO cambio idioma o tema ENTONCES DEBERÁ poder hacerse desde Configuración;
   el acceso rápido en el header PUEDE conservarse, pero el punto canónico DEBERÁ
   estar en Configuración.
4. CUANDO se reorganiza la navegación ENTONCES las rutas existentes
   (`/export`, `/import`, `/settings/backups`, gestión de catálogos) DEBERÁN
   seguir accesibles (redirigidas o reubicadas bajo `/settings`), sin romper
   enlaces existentes.
5. CUANDO se agregan textos de UI ENTONCES DEBERÁN añadirse claves i18n a los
   **5 locales** (`es, en, pt, fr, de`) manteniendo paridad, y `lint:i18n` DEBERÁ
   pasar.
6. CUANDO se reorganiza la navegación ENTONCES la accesibilidad DEBERÁ preservarse
   (roles/labels de nav, foco, skip-link) y los tests a11y/E2E existentes DEBERÁN
   seguir pasando.

### Requisito 6 — Calidad, verificación y entrega

**Historia:** Como mantenedor, quiero que la entrega esté verificada localmente y
llegue como PR revisable, respetando las restricciones del entorno.

#### Criterios de aceptación

1. CUANDO se implementa el backend ENTONCES DEBERÁ tener tests unitarios del
   parser/validador de catálogo y del loader idempotente (create/update/skip).
2. CUANDO se implementa el frontend ENTONCES DEBERÁ tener cobertura de la lista de
   catálogos oficiales y del flujo de carga (incluyendo error de red/checksum).
3. CUANDO se corre el gate local ENTONCES tsc, lint, `lint:i18n`, tests unitarios
   y los E2E existentes DEBERÁN pasar (E2E en local/Unraid, sin Actions).
4. CUANDO la entrega está lista ENTONCES DEBERÁ ir en una rama feature nombrada y
   abrirse un PR con `gh`; NO se hará push a `main`.
5. CUANDO se agregue algún workflow de CI ENTONCES DEBERÁ ser `workflow_dispatch`
   manual, nunca disparado automáticamente.
