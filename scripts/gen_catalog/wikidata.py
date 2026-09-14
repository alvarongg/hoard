"""Wikidata SPARQL client for catalog generation.

Queries the Wikidata Query Service (structured data via SPARQL), NOT the
rendered HTML of Wikipedia pages. Results are cached to disk so re-runs are
offline and deterministic. The app never calls this at runtime — it is a
build-time tool only.
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

WDQS_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = (
    "HoardCatalogBuilder/1.0 (https://github.com/alvarongg/hoard; "
    "offline catalog generation)"
)


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


def run_query(
    query: str,
    *,
    cache_dir: str | Path,
    use_network: bool = True,
    timeout: int = 60,
) -> dict:
    """Run a SPARQL query, returning the parsed JSON bindings.

    Reads from the on-disk cache when present. When ``use_network`` is False
    and there is no cache hit, raises FileNotFoundError instead of hitting the
    network — this is what tests use to stay offline.
    """
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    cache_file = cache / f"{_cache_key(query)}.json"

    if cache_file.is_file():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if not use_network:
        raise FileNotFoundError(
            f"No cached SPARQL result and network disabled: {cache_file}"
        )

    params = urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(
        f"{WDQS_ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))

    cache_file.write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    return data


def bindings(result: dict) -> list[dict]:
    """Extract the list of binding rows from a SPARQL JSON result."""
    return result.get("results", {}).get("bindings", [])
