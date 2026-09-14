"""Map Wikidata SPARQL rows into catalog items.

One SPARQL query per platform pulls: game QID, label, developer, publisher,
publication date and place-of-publication (region). Rows are grouped by game
into catalog items; regions where the game shipped go into
``custom_fields.released_regions``. Missing fields are left null (never
fabricated) and recorded in a report.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict

from scripts.gen_catalog.wikidata import bindings

# Wikidata country QIDs -> catalog region codes.
_COUNTRY_TO_REGION = {
    "Q17": "JP",    # Japan
    "Q30": "NA",    # United States
    "Q16": "NA",    # Canada
    "Q145": "PAL",  # United Kingdom
    "Q183": "PAL",  # Germany
    "Q142": "PAL",  # France
    "Q408": "PAL",  # Australia
    "Q155": "BR",   # Brazil
}


def _val(row: dict, key: str) -> str | None:
    node = row.get(key)
    if not node:
        return None
    v = node.get("value")
    return v if v else None


def _qid(uri: str | None) -> str | None:
    if not uri:
        return None
    return uri.rstrip("/").rsplit("/", 1)[-1]


def sparql_query(platform_qid: str) -> str:
    """Build a SPARQL query for all games of a given platform."""
    return f"""
SELECT ?game ?gameLabel ?developerLabel ?publisherLabel ?pubdate ?country
WHERE {{
  ?game wdt:P31 wd:Q7889 ;          # instance of video game
        wdt:P400 wd:{platform_qid} . # platform
  OPTIONAL {{ ?game wdt:P178 ?developer . }}
  OPTIONAL {{ ?game wdt:P123 ?publisher . }}
  OPTIONAL {{ ?game p:P577 ?ps . ?ps ps:P577 ?pubdate .
             OPTIONAL {{ ?ps pq:P291 ?country . }} }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ja". }}
}}
""".strip()


def map_rows(
    result: dict, *, report: list[str] | None = None
) -> list[dict]:
    """Group SPARQL rows into deterministic catalog items."""
    report = report if report is not None else []
    games: dict[str, dict] = OrderedDict()
    regions: dict[str, set[str]] = defaultdict(set)
    per_region_date: dict[str, dict[str, str]] = defaultdict(dict)

    for row in bindings(result):
        qid = _qid(_val(row, "game"))
        if not qid:
            continue
        title = _val(row, "gameLabel") or qid
        if qid not in games:
            games[qid] = {
                "external_id": f"wikidata:{qid}",
                "title": title,
                "developer": _val(row, "developerLabel"),
                "publisher": _val(row, "publisherLabel"),
                "release_date": _val(row, "pubdate"),
            }
        country_qid = _qid(_val(row, "country"))
        region = _COUNTRY_TO_REGION.get(country_qid) if country_qid else None
        pubdate = _val(row, "pubdate")
        if region:
            regions[qid].add(region)
            if pubdate:
                per_region_date[qid][region] = pubdate[:10]
        elif country_qid:
            report.append(f"{qid}: unmapped country {country_qid}")

    items: list[dict] = []
    for qid, base in games.items():
        released = sorted(regions.get(qid, set()))
        raw_date = base.get("release_date")
        item = {
            "external_id": base["external_id"],
            "title": base["title"],
            "region": released[0] if released else None,
            "developer": base.get("developer"),
            "publisher": base.get("publisher"),
            "release_date": raw_date[:10] if raw_date else None,
            "custom_fields": {
                "released_regions": released,
                "planned_regions": [],
                "unreleased_in": [],
                "country_of_manufacture": None,
                "per_region_release": dict(
                    sorted(per_region_date.get(qid, {}).items())
                ),
            },
        }
        if not base.get("developer"):
            report.append(f"{qid}: missing developer")
        if not base.get("publisher"):
            report.append(f"{qid}: missing publisher")
        items.append(item)

    # Deterministic order: (title, region).
    items.sort(key=lambda i: (i["title"].lower(), i["region"] or ""))
    return items
