"""Unit tests for the field-audit classification logic.

Covers the deterministic pieces: attribute partitioning (body / metadata /
core / ignored), canonical facet routing (by field-name hint and by target
vocabulary, plus file--file attachments), per-record observation, and the
dropped-field report. No Drupal, network, or datastores needed.
"""

from __future__ import annotations

from app.ingestion import field_audit as fa


# --------------------------------------------------------------------------- #
# Attribute classification — must mirror _partition_attributes exactly.
# --------------------------------------------------------------------------- #

def test_classify_attribute_buckets():
    rich_text = {"value": "<p>Hello</p>", "processed": "<p>Hello</p>"}
    assert fa._classify_attribute("body", rich_text) == "body"
    assert fa._classify_attribute("field_isbn", "978-81-7993") == "metadata"
    assert fa._classify_attribute("field_summary", "x" * 300) == "body"  # long text
    assert fa._classify_attribute("title", "Some title") == "core"
    assert fa._classify_attribute("langcode", "en") == "ignored"


# --------------------------------------------------------------------------- #
# Canonical facet routing.
# --------------------------------------------------------------------------- #

def test_destinations_match_current_heuristics():
    assert fa._destinations("field_theme") == ["categories"]
    assert fa._destinations("field_tags") == ["tags"]
    assert fa._destinations("field_author_name") == ["authors"]
    assert fa._destinations("field_publication_date") == []  # dropped today


def test_destinations_route_theme_vocabulary_refs_whatever_the_field_is_called():
    """drupal_facets routes on the target vocabulary, so a field the name hints
    miss still reaches categories — a taxonomy term's `parent` included."""
    themes = {"taxonomy_term--themes"}
    assert fa._destinations("field_focus", themes) == ["categories"]
    assert fa._destinations("parent", themes) == ["categories"]


def test_destinations_ignore_refs_into_non_theme_vocabularies():
    """division / area / region terms are dimensions of their own; folding them
    into themes is what put non-themes in a document's theme rows."""
    assert fa._destinations("field_division", {"taxonomy_term--division"}) == []
    assert fa._destinations("parent", {"taxonomy_term--division_areas"}) == []
    assert fa._destinations("field_owner", {"node--people"}) == []
    # Name hints still win on their own, with no targets at all.
    assert fa._destinations("parent") == []


def test_field_row_flags_dropped_and_attachments():
    dropped = fa._FieldStats(kind="attribute", seen=9, partition="metadata")
    row = fa._field_row("field_isbn", dropped, records=10)
    assert row["canonical"] == [] and row["fill_rate"] == 0.9

    files = fa._FieldStats(kind="relationship", seen=5, targets={"file--file"})
    assert fa._field_row("field_upload", files, records=10)["canonical"] == ["attachments"]

    themes = fa._FieldStats(
        kind="relationship", seen=5, targets={"taxonomy_term--themes"}
    )
    assert fa._field_row("field_theme", themes, records=10)["canonical"] == ["categories"]


# --------------------------------------------------------------------------- #
# Observation over raw JSON:API nodes.
# --------------------------------------------------------------------------- #

def _node() -> dict:
    return {
        "attributes": {
            "title": "A policy brief",
            "field_isbn": "978-81-7993",
            "field_empty": "",
            "body": {"value": "<p>text</p>", "processed": "<p>text</p>"},
        },
        "relationships": {
            "field_theme": {"data": [{"type": "taxonomy_term--themes", "id": "t1"}]},
            "parent": {"data": [{"type": "taxonomy_term--themes", "id": "virtual"}]},
            "node_type": {"data": {"type": "node_type--node_type", "id": "x"}},
        },
    }


def test_observe_counts_fill_and_skips_placeholders():
    stats: dict[str, fa._FieldStats] = {}
    fa._observe(_node(), stats)
    fa._observe(_node(), stats)

    assert stats["field_isbn"].seen == 2
    assert stats["field_empty"].seen == 0          # present but empty
    assert stats["field_theme"].targets == {"taxonomy_term--themes"}
    assert stats["parent"].seen == 0               # "virtual" root placeholder
    assert "node_type" not in stats                # not a content relationship


def test_dropped_report_lists_only_populated_unrouted_fields():
    source = {
        "fields": [
            {"field": "field_isbn", "canonical": [], "fill_rate": 0.9},
            {"field": "field_theme", "canonical": ["categories"], "fill_rate": 1.0},
            {"field": "field_unused", "canonical": [], "fill_rate": 0.0},
            {"field": "body", "fill_rate": 1.0},   # body fields carry no routing
        ]
    }
    assert [f["field"] for f in fa._dropped(source)] == ["field_isbn"]
