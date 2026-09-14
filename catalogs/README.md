# Catálogos oficiales de H.O.A.R.D.

Esta carpeta hospeda **catálogos maestros versionados** que la app puede
descubrir y cargar por HTTP. Un `manifest.json` indexa los catálogos; cada
catálogo vive en su propio archivo JSON.

## Índice: `manifest.json`

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
      "item_count": 3,
      "updated_at": "2026-09-14T00:00:00Z",
      "path": "nes.v1.json",
      "checksum": "sha256:<hex>"
    }
  ]
}
```

## Archivo de catálogo (`<system>.v1.json`)

Envelope con `entity_type: "catalog"` (distinto del import de colección, cuyo
`entity_type` es `"collection"`).

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
    "source_url": "https://www.wikidata.org/",
    "target_sub_category": { "category": "Video Games", "sub_category": "NES" }
  },
  "items": [ /* ver abajo */ ]
}
```

### Ítem

Cada ítem mapea a los campos existentes de `CatalogItem`. Campos relevantes:

| Campo | Significado |
| --- | --- |
| `external_id` | Clave natural estable (p.ej. `wikidata:Q12345`). Usada para dedup. |
| `title` | Título canónico. |
| `alternate_titles` | Títulos alternativos por región (lista). |
| `region` | Región de esta variante (`JP`/`NA`/`PAL`/…). |
| `language_codes` | Códigos de idioma (lista). |
| `developer` / `publisher` | Desarrollador / editor. |
| `release_date` | Fecha de lanzamiento (ISO `YYYY-MM-DD`) o nula. **Nunca inventada.** |
| `related_items_group` | Agrupa variantes regionales del mismo juego. |
| `is_prototype` | Flag de prototipo. |
| `custom_fields` | Ver abajo. |

### `custom_fields` (convención)

| Clave | Significado |
| --- | --- |
| `released_regions` | Regiones donde SÍ salió (lista). |
| `planned_regions` | Regiones donde se planeó. |
| `unreleased_in` | Regiones donde se planeó pero NO salió. |
| `country_of_manufacture` | País de fabricación a nivel producto (o `null`). |
| `per_region_release` | Mapa región → fecha (`{"JP": "1986-09-26"}`). |

**Lo que NO va en el catálogo:** grados de condición (CIB, mint), precios y valor.
Eso es estado del **ejemplar** y vive en `collection_items` del usuario. El
catálogo describe el producto; la condición y el precio describen tu copia.

## Regenerar

Los catálogos se generan **offline** con los scripts de `scripts/gen_catalog/`
(Wikidata vía SPARQL, sin scraping de HTML). La app nunca consulta la fuente en
runtime. Ver `scripts/gen_catalog/README.md`.
