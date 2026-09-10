"""Partners from the CMS partner fields: PROJECT -PARTNER_OF-> ORGANIZATION.

`PARTNER_OF` already declared exactly this shape and the graph held zero such
edges, because the two partner fields were never added to the rule table. 287
projects name their partners in structured metadata — The World Bank, GIZ, UNDP,
IIT Delhi — and none of it reached Neo4j.

No new predicate, no model, and the sponsor and PI rules untouched.
"""
from __future__ import annotations

import json

from app.knowledge.claims import extract_cms
from app.knowledge.claims import predicates as vocab
from app.knowledge.claims import types as t

DOC = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
PROJECT = "project-1"
WORLDBANK = "org-worldbank"
GIZ = "org-giz"


class _Index:
    def __init__(self, entities):
        self.entities = entities


def _context():
    return extract_cms.CmsClaimContext.from_index(_Index({
        PROJECT: {"entity_type": "PROJECT", "normalized_name": "a project",
                  "canonical_name": "A Project", "cms_uuid": DOC},
        WORLDBANK: {"entity_type": "ORGANIZATION", "normalized_name": "the world bank",
                    "canonical_name": "The World Bank"},
        GIZ: {"entity_type": "ORGANIZATION", "normalized_name": "giz",
              "canonical_name": "GIZ"},
        "person-alice": {"entity_type": "PERSON", "normalized_name": "alice smith",
                         "canonical_name": "Dr Alice Smith"},
    }))


def _claims(meta):
    return extract_cms.claims_from_meta(DOC, json.dumps(meta), context=_context())


def _of(claims, predicate):
    return [c for c in claims if c.predicate == predicate]


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #

def test_a_partner_becomes_a_partner_of_claim():
    claims = _of(_claims({"field_completed_partners": ["The World Bank"]}),
                 "PARTNER_OF")
    assert len(claims) == 1
    c = claims[0]
    assert c.subject_entity_id == PROJECT
    assert c.object_entity_id == WORLDBANK
    assert c.document_id == DOC
    assert c.evidence_kind == t.EVIDENCE_CMS_FIELD
    assert c.extraction_method == "cms_field"
    assert c.confidence == extract_cms.CMS_CONFIDENCE


def test_both_partner_fields_are_read():
    for field in ("field_completed_partners", "field_ongoing_partners"):
        claims = _of(_claims({field: ["GIZ"]}), "PARTNER_OF")
        assert len(claims) == 1, field
        assert claims[0].source_field == field


def test_the_direction_matches_the_declared_predicate():
    """PROJECT -> ORGANIZATION, as `PARTNER_OF` has always declared. The claim
    must type-check against the existing vocabulary rather than needing it
    widened."""
    p = vocab.get("PARTNER_OF")
    assert p.domain == ("PROJECT",) and p.range == ("ORGANIZATION",)
    assert vocab.accepts("PARTNER_OF", "PROJECT", "ORGANIZATION")


def test_several_partners_each_get_a_claim():
    claims = _of(_claims({"field_completed_partners": ["The World Bank", "GIZ"]}),
                 "PARTNER_OF")
    assert {c.object_entity_id for c in claims} == {WORLDBANK, GIZ}


def test_partners_inherit_the_projects_period():
    """Same treatment as a sponsor: the project's period scopes the
    relationship, under `subject_period` rather than `stated` — the partnership
    itself states no dates, so the basis records that the window was inherited
    and not asserted."""
    claims = _of(_claims({
        "field_completed_partners": ["GIZ"],
        "field_completed_start_date": "2020-01-01",
        "field_completed_end_date": "2022-12-31",
    }), "PARTNER_OF")
    assert claims[0].valid_from
    assert claims[0].temporal_basis == t.BASIS_SUBJECT_PERIOD
    # And identical to how the sponsor on the same project is scoped.
    sponsor = _of(_claims({
        "field_completed_sponsors": ["GIZ"],
        "field_completed_start_date": "2020-01-01",
        "field_completed_end_date": "2022-12-31",
    }), "FUNDED_BY")
    assert (sponsor[0].valid_from, sponsor[0].valid_until,
            sponsor[0].temporal_basis) == (
        claims[0].valid_from, claims[0].valid_until, claims[0].temporal_basis)


# --------------------------------------------------------------------------- #
# Safety
# --------------------------------------------------------------------------- #

def test_an_unknown_partner_is_skipped_not_created():
    assert _of(_claims({"field_completed_partners": ["Nobody Ltd"]}),
               "PARTNER_OF") == []


def test_an_unknown_partner_does_not_stop_the_known_ones():
    claims = _of(_claims({"field_completed_partners": ["Nobody Ltd", "GIZ"]}),
                 "PARTNER_OF")
    assert [c.object_entity_id for c in claims] == [GIZ]


def test_a_person_named_as_a_partner_is_not_recorded():
    """The rule resolves against ORGANIZATION only, so a stray person name in a
    partner field cannot become a partner."""
    assert _of(_claims({"field_completed_partners": ["Dr Alice Smith"]}),
               "PARTNER_OF") == []


def test_identical_input_produces_an_identical_claim_id():
    a = _of(_claims({"field_completed_partners": ["GIZ"]}), "PARTNER_OF")[0]
    b = _of(_claims({"field_completed_partners": ["GIZ"]}), "PARTNER_OF")[0]
    assert a.claim_id == b.claim_id


def test_a_partner_repeated_in_one_field_yields_one_claim():
    """Same subject, predicate, object and provenance, so the same claim_id —
    `dedupe` collapses it and the MERGE would too."""
    from app.knowledge.claims.validate import dedupe

    claims = _of(_claims({"field_completed_partners": ["GIZ", "GIZ"]}),
                 "PARTNER_OF")
    assert len({c.claim_id for c in claims}) == 1
    assert len(dedupe(claims)) == 1


def test_stakeholders_are_still_ignored():
    """Their values are audience categories, not organizations."""
    assert "field_completed_stakeholders" not in {
        f for f, _, _ in extract_cms._FIELD_RULES}
    assert "field_ongoing_stakeholders" not in {
        f for f, _, _ in extract_cms._FIELD_RULES}


# --------------------------------------------------------------------------- #
# The existing behaviour
# --------------------------------------------------------------------------- #

def test_sponsors_and_pi_still_produce_their_own_claims():
    claims = _claims({
        "field_completed_sponsors": ["The World Bank"],
        "field_completed_pi_name": ["Dr Alice Smith"],
        "field_completed_partners": ["GIZ"],
    })
    assert len(_of(claims, "FUNDED_BY")) == 1
    assert len(_of(claims, "LED_BY")) == 1
    assert len(_of(claims, "PARTNER_OF")) == 1


def test_a_sponsor_is_not_turned_into_a_partner():
    """Funding and partnership are separate facts in separate fields, and stay
    separate in the graph."""
    claims = _claims({"field_completed_sponsors": ["The World Bank"]})
    assert _of(claims, "PARTNER_OF") == []
    assert len(_of(claims, "FUNDED_BY")) == 1


def test_the_same_organization_can_be_both():
    """And when the CMS says an organization both funded and partnered, both
    edges exist — distinct predicates, distinct claim ids."""
    claims = _claims({
        "field_completed_sponsors": ["GIZ"],
        "field_completed_partners": ["GIZ"],
    })
    funded, partner = _of(claims, "FUNDED_BY"), _of(claims, "PARTNER_OF")
    assert len(funded) == 1 and len(partner) == 1
    assert funded[0].claim_id != partner[0].claim_id
