# Generadores de catálogos (offline)

Generan los archivos de `catalogs/` a partir de **Wikidata vía SPARQL**
(datos estructurados), no scrapeando el HTML de Wikipedia. Corren **local o en
Unraid**; la app nunca consulta la fuente en runtime.

## Uso

```bash
# Desde la raíz del repo
python -m scripts.gen_catalog.build --system nes
python -m scripts.gen_catalog.build --system genesis

# Reconstruir sólo desde la caché en disco (sin red)
python -m scripts.gen_catalog.build --system nes --no-network
```

Cada corrida:
- Consulta el Wikidata Query Service (con caché en `scripts/gen_catalog/.cache/`).
- Escribe `catalogs/<system>.v1.json` de forma **determinista** (claves ordenadas,
  UTF-8, orden estable por `(title, region)`) para diffs revisables.
- Recalcula el `checksum` y actualiza `catalogs/manifest.json`.
- Registra campos faltantes en `scripts/gen_catalog/.cache/<system>.report.txt`.

## Diseño de datos

- Regiones: se derivan del país de "place of publication" (P291) de cada fecha de
  publicación (P577). Mapa país→región en `mapper.py` (`JP`, `NA`, `PAL`, `BR`).
- Campos irresolubles quedan **nulos** (nunca inventados) y van al reporte.
- Condición (CIB/mint) y precios NO se generan: son del ejemplar, no del catálogo.

## Advertencias

- **Términos de uso**: respetar la [política de WDQS](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service).
  El User-Agent identifica al proyecto; no abusar del endpoint.
- **Fragilidad**: la cobertura de Wikidata para consolas retro es **parcial** y
  cambia con el tiempo. El resultado puede tener menos ítems que la lista
  completa de Wikipedia y faltar regiones. La caché fija el resultado para que el
  PR sea reproducible; regenerá conscientemente.
- Dependencias: sólo stdlib (`urllib`). Sin librerías nuevas de runtime.
