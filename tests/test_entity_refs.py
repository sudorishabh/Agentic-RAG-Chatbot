"""Unit tests for entity-reference extraction and canonical routing.

Covers ``_resolve_relationships`` (labels stay shape-compatible, refs carry
UUIDs, placeholders and files skipped), ``EntityRef.vocabulary``, and the
canonical mapping: vocabulary-driven categories, entity_refs / raw_meta
carried onto the document, and payload isolation (new fields must not leak
into chunk payloads before the schema step lands). No network or datastores.
"""

from __future__ import annotations

from app.core.models import EntityRef
from app.ingestion.canonical import from_drupal_record
from app.ingestion.chunker import chunk_canonical
from app.ingestion.extractors.drupal_extractor import DrupalRecord, _resolve_relationships


def _included() -> dict:
    return {
        ("taxonomy_term--themes", "t-climate"): {
            "attributes": {"name": "Climate"}
        },
        ("node--people", "p-jane"): {
            "attributes": {"title": "Jane Doe"}
        },
    }


def _node() -> dict:
    return {
        "relationships": {
            "field_focus": {  # no CATEGORY_HINTS substring in the name
                "data": [{"type": "taxonomy_term--themes", "id": "t-climate"}]
            },
            "field_author": {
                "data": [{"type": "node--people", "id": "p-jane"}]
            },
            "field_unresolved": {  # not embedded in `included`
                "data": [{"type": "taxonomy_term--themes", "id": "t-missing"}]
            },
            "parent": {
                "data": [{"type": "taxonomy_term--themes", "id": "virtual"}]
            },
            "field_file": {
                "data": [{"type": "file--file", "id": "f1"}]
            },
            "node_type": {
                "data": {"type": "node_type--node_type", "id": "x"}
            },
        }
    }


# --------------------------------------------------------------------------- #
# Extractor: labels unchanged, refs carry identity.
# --------------------------------------------------------------------------- #

def test_resolve_relationships_labels_and_refs():
    meta, refs = _resolve_relationships(_node(), _included())

    assert meta == {"field_focus": ["Climate"], "field_author": ["Jane Doe"]}

    by_field = {r.field_name: r for r in refs}
    assert by_field["field_focus"].uuid == "t-climate"
    assert by_field["field_focus"].entity_type == "taxonomy_term--themes"
    assert by_field["field_focus"].label == "Climate"
    # Unresolved entities keep their identity; only the label is unknown.
    assert by_field["field_unresolved"].uuid == "t-missing"
    assert by_field["field_unresolved"].label is None
    # Placeholder parents, files, and non-content relationships never become refs.
    assert "parent" not in by_field
    assert "field_file" not in by_field
    assert "node_type" not in by_field


def test_vocabulary_property():
    ref = EntityRef(field_name="f", uuid="u", entity_type="taxonomy_term--themes")
    assert ref.vocabulary == "themes"
    assert EntityRef(field_name="f", uuid="u", entity_type="node--people").vocabulary is None


# --------------------------------------------------------------------------- #
# Canonical: vocabulary routing + refs/raw_meta carried through.
# --------------------------------------------------------------------------- #

def _record() -> DrupalRecord:
    meta, refs = _resolve_relationships(_node(), _included())
    meta["field_isbn"] = "978-81-7993"
    return DrupalRecord(
        uuid="doc-1",
        bundle="policy_brief",
        nid=42,
        title="A brief",
        url="https://example.org/brief",
        body=" ".join(f"Sentence {i} about climate policy and mitigation." for i in range(80)),
        created="2024-01-01T00:00:00+00:00",
        changed="2024-02-01T00:00:00+00:00",
        metadata=meta,
        refs=refs,
    )


def test_from_drupal_record_routes_theme_ref_by_vocabulary():
    doc = from_drupal_record(_record())
    # "field_focus" matches no name hint; the vocabulary routes it anyway.
    assert doc.categories == ["Climate"]
    assert doc.authors == ["Jane Doe"]


def test_from_drupal_record_preserves_refs_and_raw_meta():
    doc = from_drupal_record(_record())
    assert {r.uuid for r in doc.entity_refs} == {"t-climate", "p-jane", "t-missing"}
    # raw_meta keeps everything, including fields no facet routes today.
    assert doc.raw_meta["field_isbn"] == "978-81-7993"
    assert doc.raw_meta["field_focus"] == ["Climate"]


def test_new_fields_do_not_leak_into_chunk_payloads():
    doc = from_drupal_record(_record())
    payloads = [c.to_payload() for c in chunk_canonical(doc)]
    assert payloads
    for payload in payloads:
        assert "entity_refs" not in payload
        assert "raw_meta" not in payload
        assert "field_isbn" not in payload


def test_chunk_payloads_carry_term_uuid_filters():
    doc = from_drupal_record(_record())
    payloads = [c.to_payload() for c in chunk_canonical(doc)]
    assert payloads
    for payload in payloads:
        # Taxonomy UUIDs only — the people ref is not a term.
        assert payload["term_ids"] == ["t-climate", "t-missing"]
        assert payload["theme_ids"] == ["t-climate", "t-missing"]
        assert "p-jane" not in payload["term_ids"]
