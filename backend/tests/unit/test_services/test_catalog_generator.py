"""Tests for the catalog generator mapper (offline, recorded SPARQL)."""

from __future__ import annotations

import sys
from pathlib import Path

# Make the repo root importable so `scripts.gen_catalog` resolves.
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.gen_catalog.mapper import map_rows, sparql_query  # noqa: E402


def _binding(game, label, dev=None, pub=None, date=None, country=None):
    row = {
        "game": {"type": "uri", "value": f"http://www.wikidata.org/entity/{game}"},
        "gameLabel": {"type": "literal", "value": label},
    }
    if dev:
        row["developerLabel"] = {"type": "literal", "value": dev}
    if pub:
        row["publisherLabel"] = {"type": "literal", "value": pub}
    if date:
        row["pubdate"] = {"type": "literal", "value": date}
    if country:
        row["country"] = {
            "type": "uri",
            "value": f"http://www.wikidata.org/entity/{country}",
        }
    return row


# A recorded-style SPARQL result: two games, multiple regions, some gaps.
RECORDED = {
    "results": {
        "bindings": [
            _binding("Q1", "Castlevania", "Konami", "Konami",
                     "1986-09-26T00:00:00Z", "Q17"),
            _binding("Q1", "Castlevania", "Konami", "Konami",
                     "1987-05-01T00:00:00Z", "Q30"),
            _binding("Q2", "Devil World", "Nintendo", None,
                     "1984-10-05T00:00:00Z", "Q17"),
        ]
    }
}


def test_sparql_query_includes_platform():
    q = sparql_query("Q172742")
    assert "wd:Q172742" in q
    assert "P400" in q  # platform property


def test_map_groups_by_game_and_regions():
    items = map_rows(RECORDED)
    assert len(items) == 2  # two distinct games, not three rows
    castlevania = next(i for i in items if i["title"] == "Castlevania")
    assert castlevania["custom_fields"]["released_regions"] == ["JP", "NA"]
    assert castlevania["custom_fields"]["per_region_release"] == {
        "JP": "1986-09-26",
        "NA": "1987-05-01",
    }
    assert castlevania["release_date"] == "1986-09-26"
    assert castlevania["external_id"] == "wikidata:Q1"


def test_missing_fields_stay_null_and_reported():
    report: list[str] = []
    items = map_rows(RECORDED, report=report)
    devil = next(i for i in items if i["title"] == "Devil World")
    assert devil["publisher"] is None
    assert devil["custom_fields"]["country_of_manufacture"] is None
    assert any("missing publisher" in line for line in report)


def test_deterministic_order():
    items_a = map_rows(RECORDED)
    items_b = map_rows(RECORDED)
    assert [i["title"] for i in items_a] == [i["title"] for i in items_b]
    # Alphabetical by title.
    assert [i["title"] for i in items_a] == ["Castlevania", "Devil World"]
