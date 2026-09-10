"""Authorship from the CMS author fields: PERSON -AUTHORED-> this document.

The CMS states authors outright for thousands of documents and the graph held
none of it. These cover the extraction contract: authoritative fields only, no
invented entities, one edge per author per document, and the project rules
(FUNDED_BY / LED_BY) left exactly as they were.
"""
from __future__ import annotations

import json

from app.knowledge.claims import extract_cms
from app.knowledge.claims import types as t

DOC = "11111111-2222-3333-4444-555555555555"
ALICE = "person-alice"
BOB = "person-bob"


class _Index:
    """The two lookups CmsClaimContext is built from."""

    def __init__(self, entities):
        self.entities = entities


def _context(**extra):
    entities = {
        ALICE: {"entity_type": "PERSON", "normalized_name": "alice smith",
                "canonical_name": "Dr Alice Smith"},
        BOB: {"entity_type": "PERSON", "normalized_name": "bob jones",
              "canonical_name": "Mr Bob Jones"},
        "org-worldbank": {"entity_type": "ORGANIZATION",
                          "normalized_name": "world bank",
                          "canonical_name": "The World Bank"},
    }
    entities.update(extra)
    return extract_cms.CmsClaimContext.from_index(_Index(entities))


def _authors(meta, context=None):
    return extract_cms.authorship_from_meta(
        DOC, json.dumps(meta), context=context or _context()
    )


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #

def test_an_author_becomes_an_authored_claim():
    claims = _authors({"field_authors": ["Dr Alice Smith"]})
    assert len(claims) == 1
    c = claims[0]
    assert c.subject_entity_id == ALICE
    assert c.predicate == "AUTHORED"
    assert c.document_id == DOC
    assert c.evidence_kind == t.EVIDENCE_CMS_FIELD
    assert c.extraction_method == "cms_field"
    assert c.confidence == extract_cms.CMS_CONFIDENCE


def test_the_object_identifies_the_document():
    """A document is not an entity type here, so the object is the document id
    as a literal. The readable title stays on the Document node, which the
    claim reaches through its own provenance."""
    c = _authors({"field_authors": ["Dr Alice Smith"]})[0]
    assert c.object_literal == DOC
    assert c.object_entity_id is None


def test_provenance_names_the_field_and_the_value():
    c = _authors({"field_rpaper_author": ["Dr Alice Smith"]})[0]
    assert c.source_field == "field_rpaper_author"
    assert c.source_value == "Dr Alice Smith"
    assert c.source_value_hash


def test_several_authors_each_get_a_claim():
    claims = _authors({"field_authors": ["Dr Alice Smith", "Mr Bob Jones"]})
    assert {c.subject_entity_id for c in claims} == {ALICE, BOB}


def test_every_declared_author_field_is_read():
    for field in extract_cms._AUTHOR_FIELDS:
        claims = _authors({field: ["Dr Alice Smith"]})
        assert len(claims) == 1, field
        assert claims[0].source_field == field


def test_no_temporal_window_is_invented():
    """A person authored a document, permanently. Borrowing the document's date
    as a validity period would assert something the CMS never said."""
    c = _authors({"field_authors": ["Dr Alice Smith"]})[0]
    assert c.valid_from is None and c.valid_until is None
    assert c.temporal_basis == t.BASIS_UNKNOWN


# --------------------------------------------------------------------------- #
# Safety: no invented entities, no duplicate edges
# --------------------------------------------------------------------------- #

def test_an_unknown_author_is_skipped_not_created():
    claims = _authors({"field_authors": ["Someone Nobody Knows"]})
    assert claims == []


def test_an_unknown_author_does_not_stop_the_known_ones():
    """The document still indexes and its resolvable authors still land."""
    claims = _authors({"field_authors": ["Someone Nobody Knows", "Mr Bob Jones"]})
    assert [c.subject_entity_id for c in claims] == [BOB]


def test_an_organization_in_an_author_field_is_not_recorded_as_a_person():
    """`field_external_authors` mixes people and organizations. Only the PERSON
    lookup is consulted, so an organization simply does not resolve."""
    assert _authors({"field_external_authors": ["The World Bank"]}) == []


def test_one_author_named_twice_in_a_field_yields_one_claim():
    claims = _authors({"field_authors": ["Dr Alice Smith", "Dr Alice Smith"]})
    assert len(claims) == 1


def test_one_author_in_two_fields_yields_one_claim():
    """The real duplicate risk: 179 documents carry more than one author field
    and 35 (person, document) pairs appear twice. `claim_id` includes
    `source_field`, so without this dedupe one fact would become two edges."""
    claims = _authors({
        "field_authors": ["Dr Alice Smith"],
        "field_article_authors": ["Dr Alice Smith"],
    })
    assert len(claims) == 1
    # The first field in the declared order is the one recorded.
    assert claims[0].source_field == "field_authors"


def test_identical_input_produces_an_identical_claim_id():
    """Re-ingesting a document must update its edge, not add another."""
    first = _authors({"field_authors": ["Dr Alice Smith"]})[0]
    second = _authors({"field_authors": ["Dr Alice Smith"]})[0]
    assert first.claim_id == second.claim_id


def test_missing_or_empty_metadata_is_not_an_error():
    for meta in (None, "", "null", "{}", "not json"):
        assert extract_cms.authorship_from_meta(
            DOC, meta, context=_context()) == []


# --------------------------------------------------------------------------- #
# The cheap gate
# --------------------------------------------------------------------------- #

def test_has_author_fields_detects_them():
    assert extract_cms.has_author_fields(json.dumps(
        {"field_policybrief_authors": ["Dr Alice Smith"]})) is True


def test_has_author_fields_is_false_without_one():
    """It is what lets the pipeline skip building an extraction context — which
    walks every entity in the store — for documents that name no author."""
    assert extract_cms.has_author_fields(json.dumps({"title": "x"})) is False
    assert extract_cms.has_author_fields(None) is False
    assert extract_cms.has_author_fields(json.dumps(
        {"field_authors": []})) is False


# --------------------------------------------------------------------------- #
# The existing rules are untouched
# --------------------------------------------------------------------------- #

def test_the_project_rules_are_unchanged():
    assert extract_cms._FIELD_RULES[:4] == (
        ("field_completed_sponsors", "FUNDED_BY", "ORGANIZATION"),
        ("field_ongoing_sponsors", "FUNDED_BY", "ORGANIZATION"),
        ("field_completed_pi_name", "LED_BY", "PERSON"),
        ("field_ongoing_pi_name", "LED_BY", "PERSON"),
    )


def test_authorship_needs_no_project_subject():
    """The reason it is a separate function: `claims_from_meta` returns nothing
    for a document that is not a seeded project, and most authored documents —
    feature articles, policy briefs, research papers — never are."""
    context = _context()
    assert context.subject_for(DOC) is None
    assert len(_authors({"field_authors": ["Dr Alice Smith"]}, context)) == 1
