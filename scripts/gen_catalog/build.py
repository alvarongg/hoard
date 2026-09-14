"""CLI to generate a catalog JSON from Wikidata and update the manifest.

Usage (offline/local; never runs in the app):

    python -m scripts.gen_catalog.build --system nes
    python -m scripts.gen_catalog.build --system genesis

Add --no-network to build only from the on-disk SPARQL cache.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

from scripts.gen_catalog.mapper import map_rows, sparql_query
from scripts.gen_catalog.wikidata import run_query

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGS_DIR = REPO_ROOT / "catalogs"
CACHE_DIR = Path(__file__).resolve().parent / ".cache"

SYSTEMS = {
    "nes": {
        "platform_qid": "Q172742",
        "name": "Nintendo Entertainment System / Famicom",
        "description": "Juegos de NES/Famicom (Wikidata)",
        "sub_category": "NES",
        "file": "nes.v1.json",
        "version": "1.0.0",
    },
    "genesis": {
        "platform_qid": "Q10677",
        "name": "Sega Genesis / Mega Drive",
        "description": "Juegos de Sega Genesis/Mega Drive (Wikidata)",
        "sub_category": "Genesis",
        "file": "genesis.v1.json",
        "version": "1.0.0",
    },
}


def _dump(obj: object) -> str:
    """Deterministic JSON: sorted keys, UTF-8, stable indent."""
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_system(system: str, *, use_network: bool = True) -> dict:
    cfg = SYSTEMS[system]
    report: list[str] = []
    result = run_query(
        sparql_query(cfg["platform_qid"]),
        cache_dir=CACHE_DIR,
        use_network=use_network,
    )
    items = map_rows(result, report=report)

    envelope = {
        "schema_version": "1.0",
        "entity_type": "catalog",
        "catalog": {
            "id": system,
            "name": cfg["name"],
            "system": system,
            "version": cfg["version"],
            "description": cfg["description"],
            "source_type": "wikidata",
            "source_name": f"Wikidata — {cfg['name']}",
            "source_url": "https://query.wikidata.org/",
            "target_sub_category": {
                "category": "Video Games",
                "sub_category": cfg["sub_category"],
            },
        },
        "items": items,
    }

    CATALOGS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = CATALOGS_DIR / cfg["file"]
    content = _dump(envelope)
    out_file.write_text(content, encoding="utf-8")

    if report:
        report_file = CACHE_DIR / f"{system}.report.txt"
        report_file.write_text("\n".join(report), encoding="utf-8")

    _update_manifest(system, cfg, len(items), content)
    return {"system": system, "items": len(items), "gaps": len(report)}


def _update_manifest(
    system: str, cfg: dict, item_count: int, content: str
) -> None:
    manifest_path = CATALOGS_DIR / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {"schema_version": "1.0", "catalogs": []}

    checksum = "sha256:" + hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "id": system,
        "name": cfg["name"],
        "description": cfg["description"],
        "system": system,
        "version": cfg["version"],
        "item_count": item_count,
        "updated_at": now,
        "path": cfg["file"],
        "checksum": checksum,
    }

    catalogs = [c for c in manifest.get("catalogs", []) if c.get("id") != system]
    catalogs.append(entry)
    catalogs.sort(key=lambda c: c["id"])
    manifest["catalogs"] = catalogs
    manifest["generated_at"] = now
    manifest_path.write_text(_dump(manifest), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a catalog JSON.")
    parser.add_argument("--system", required=True, choices=sorted(SYSTEMS))
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    summary = build_system(args.system, use_network=not args.no_network)
    print(
        f"[{summary['system']}] wrote {summary['items']} items, "
        f"{summary['gaps']} gaps logged."
    )


if __name__ == "__main__":
    main()
