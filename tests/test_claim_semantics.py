"""Unit tests for temporal normalization, conflict detection and supersession.

No database and no model. The Bob/Alice succession is the case the whole design
turns on: two leaders of one project at different times are *history*, not a
contradiction, and getting that wrong either loses the past or fabricates a
dispute.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.knowledge.claims import conflicts as cf
from app.knowledge.claims import temporal as tm
from app.knowledge.claims import types as t

PROJECT = "project_0000000000a1"
BOB = "person_0000000000b1"
ALICE = "person_0000000000b2"
ORG_A = "org_0000000000c1"
ORG_B = "org_0000000000c2"


def _claim(predicate="LED_BY", obj=BOB, *, valid_from=None, valid_until=None,
           basis=t.BASIS_STATED, status=t.STATUS_ACTIVE, chunk="chunk-1",
           subject=PROJECT, literal=None):
    return t.build(
        subject_entity_id=subject, predicate=predicate,
        object_entity_id=obj, object_literal=literal,
        document_id="doc-1", chunk_id=chunk, evidence_kind=t.EVIDENCE_CHUNK,
        quote="a quote long enough to count", valid_from=valid_from,
        valid_until=valid_until, temporal_basis=basis, status=status,
        confidence=0.9, extraction_method="llm", extractor_version="test",
    )


# --------------------------------------------------------------------------- #
# A — temporal normalization
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "phrase,expected_from,expected_until",
    [
        ("led the project since 2019", "2019-01-01", None),
        ("funded from March 2019", "2019-03-01", None),
        ("ran until 2021", None, "2021-01-01"),
        ("active 2019-2021", "2019-01-01", "2021-01-01"),
        ("ran from 2019 to present", "2019-01-01", None),
        ("between 2015 and 2018", "2015-01-01", "2018-01-01"),
        ("w.e.f. 2020-04-01", "2020-04-01", None),
    ],
)
def test_explicit_source_language_is_parsed(phrase, expected_from, expected_until):
    window = tm.parse_temporal_phrase(phrase)
    assert (window.valid_from, window.valid_until) == (expected_from, expected_until)
    assert window.basis == t.BASIS_STATED


@pytest.mark.parametrize(
    "phrase",
    ["published in 2024", "the 2019 report", "reached 2030 targets",
     "no dates at all", ""],
)
def test_a_bare_year_is_not_a_validity_claim(phrase):
    """This corpus is full of years that are citations, measurements and
    targets. Reading one as a validity window would date almost every claim
    wrongly."""
    assert tm.parse_temporal_phrase(phrase).is_unknown


def test_present_means_open_ended_not_forever():
    window = tm.parse_temporal_phrase("from 2019 to present")
    assert window.is_open_ended
    assert not window.is_unknown
    assert window.valid_until is None


def test_open_ended_and_unknown_are_distinguishable():
    """The distinction conflict detection depends on: an open-ended window
    overlaps everything after its start, an unknown one overlaps nothing."""
    open_ended = tm.Window("2019-01-01", None, t.BASIS_STATED)
    unknown = tm.Window(None, None, t.BASIS_UNKNOWN)
    assert open_ended.is_open_ended and not open_ended.is_unknown
    assert unknown.is_unknown and not unknown.is_open_ended


def test_inverted_phrase_is_refused_not_reordered():
    """Reordering would invent a reading the source did not have."""
    assert tm.parse_temporal_phrase("from 2021 until 2019").is_unknown


def test_document_date_is_never_used_as_validity():
    """The inference nobody approved: a 2024 article about a 2019 partnership
    does not make the partnership start in 2024."""
    assert t.BASIS_DOCUMENT not in t.CURRENT_STATE_BASES
    claim = _claim(valid_from="2024-01-01", basis=t.BASIS_DOCUMENT)
    assert not cf.is_current_state_eligible(claim, as_of="2024-06-01")


# --- the approved rule: the subject's own CMS period ------------------------ #

def test_completed_project_period_is_a_closed_interval():
    window = tm.subject_period({
        "field_completed_start_date": "2004-06-28T18:30:00+00:00",
        "field_completed_end_date": "2005-06-30T18:30:00+00:00",
    })
    assert (window.valid_from, window.valid_until) == ("2004-06-28", "2005-06-30")
    assert window.basis == t.BASIS_SUBJECT_PERIOD
    assert window.is_closed


def test_ongoing_project_period_is_open_ended():
    """593 ongoing projects carry a start and no end. That is the corpus's own
    way of saying "current"."""
    window = tm.subject_period(
        {"field_ongoing_start_date": "2019-10-24T10:35:27+00:00"}
    )
    assert window.valid_from == "2019-10-24" and window.valid_until is None
    assert window.is_open_ended


def test_subject_period_is_its_own_basis():
    """Never `stated`: the CMS dated the project, not the relationship."""
    window = tm.subject_period({"field_ongoing_start_date": "2019-01-01T00:00:00Z"})
    assert window.basis == t.BASIS_SUBJECT_PERIOD
    assert window.basis != t.BASIS_STATED


def test_inverted_cms_period_is_ignored():
    window = tm.subject_period({
        "field_completed_start_date": "2010-01-01T00:00:00Z",
        "field_completed_end_date": "2005-01-01T00:00:00Z",
    })
    assert window.is_unknown


def test_dates_coerce_whatever_shape_they_arrive_in():
    """MySQL returns date objects; extraction produces strings. Every
    comparison here is lexical, so they have to meet in one place."""
    assert tm.as_iso(dt.date(2019, 5, 6)) == "2019-05-06"
    assert tm.as_iso(dt.datetime(2019, 5, 6, 12, 0)) == "2019-05-06"
    assert tm.as_iso("2019-05-06") == "2019-05-06"
    assert tm.as_iso(None) is None


# --------------------------------------------------------------------------- #
# Interval arithmetic
# --------------------------------------------------------------------------- #

def test_adjacent_intervals_do_not_overlap():
    """The boundary belongs to the later claim, which is what makes a handover
    a succession rather than a one-day contradiction."""
    bob = tm.Window("2024-01-01", "2026-03-01", t.BASIS_STATED)
    alice = tm.Window("2026-03-01", None, t.BASIS_STATED)
    assert not tm.overlaps(bob, alice)
    assert tm.precedes(bob, alice)


def test_open_ended_overlaps_everything_after_its_start():
    a = tm.Window("2019-01-01", None, t.BASIS_STATED)
    b = tm.Window("2020-01-01", "2021-01-01", t.BASIS_STATED)
    assert tm.overlaps(a, b)


def test_unknown_windows_overlap_nothing():
    """Treating "undated" as "always" would make every undated claim conflict
    with every other one."""
    unknown = tm.Window(None, None, t.BASIS_UNKNOWN)
    dated = tm.Window("2019-01-01", "2021-01-01", t.BASIS_STATED)
    assert not tm.overlaps(unknown, dated)
    assert not tm.overlaps(unknown, unknown)


# --------------------------------------------------------------------------- #
# B — conflict detection
# --------------------------------------------------------------------------- #

def test_non_overlapping_succession_is_not_a_conflict():
    """The Bob/Alice case. Both claims survive, neither is disputed, and the
    history stays queryable."""
    bob = _claim(obj=BOB, valid_from="2024-01-01", valid_until="2026-03-01",
                 chunk="chunk-1")
    alice = _claim(obj=ALICE, valid_from="2026-03-01", chunk="chunk-2")
    report = cf.detect([bob, alice])
    assert report.links == []
    assert report.status_changes == {}
    assert report.disputed == []


def test_overlapping_functional_claims_conflict():
    bob = _claim(obj=BOB, valid_from="2026-01-01", chunk="chunk-1")
    alice = _claim(obj=ALICE, valid_from="2026-01-01", chunk="chunk-2")
    report = cf.detect([bob, alice])
    assert set(report.disputed) == {bob.claim_id, alice.claim_id}
    assert all(l.kind == cf.LINK_CONTRADICTS for l in report.links)


def test_non_functional_predicate_allows_many_objects():
    """A project has many funders. Treating that as a contradiction is a bug."""
    a = _claim(predicate="FUNDED_BY", obj=ORG_A, valid_from="2019-01-01",
               chunk="chunk-1")
    b = _claim(predicate="FUNDED_BY", obj=ORG_B, valid_from="2019-01-01",
               chunk="chunk-2")
    report = cf.detect([a, b])
    assert report.examined == 0        # not even considered
    assert report.status_changes == {}


def test_same_object_from_two_chunks_is_corroboration_not_conflict():
    a = _claim(obj=BOB, valid_from="2019-01-01", chunk="chunk-1")
    b = _claim(obj=BOB, valid_from="2019-01-01", chunk="chunk-2")
    assert a.claim_id != b.claim_id     # independent evidence
    assert cf.detect([a, b]).status_changes == {}


def test_conflicting_evidence_is_preserved_not_discarded():
    bob = _claim(obj=BOB, valid_from="2026-01-01", chunk="chunk-1")
    alice = _claim(obj=ALICE, valid_from="2026-01-01", chunk="chunk-2")
    report = cf.detect([bob, alice])
    # Status changed; nothing about the claims themselves did.
    assert bob.quote and alice.quote
    assert bob.valid_from == "2026-01-01" and alice.valid_from == "2026-01-01"
    assert len(report.status_changes) == 2


def test_already_disputed_claims_are_not_re_examined():
    disputed = _claim(obj=BOB, valid_from="2026-01-01", status=t.STATUS_DISPUTED)
    active = _claim(obj=ALICE, valid_from="2026-01-01", chunk="chunk-2")
    report = cf.detect([disputed, active])
    assert report.examined == 1


# --------------------------------------------------------------------------- #
# C — supersession
# --------------------------------------------------------------------------- #

def test_a_stated_window_supersedes_one_derived_from_the_subject_period():
    derived = _claim(obj=BOB, valid_from="2019-01-01",
                     basis=t.BASIS_SUBJECT_PERIOD, chunk="chunk-1")
    stated = _claim(obj=ALICE, valid_from="2019-01-01",
                    basis=t.BASIS_STATED, chunk="chunk-2")
    report = cf.detect([derived, stated])
    assert report.superseded == [derived.claim_id]
    assert stated.claim_id not in report.status_changes
    link = next(l for l in report.links if l.kind == cf.LINK_SUPERSEDES)
    assert link.from_claim_id == stated.claim_id
    assert link.to_claim_id == derived.claim_id


def test_a_later_start_supersedes_an_earlier_overlapping_claim():
    early = _claim(obj=BOB, valid_from="2019-01-01", chunk="chunk-1")
    late = _claim(obj=ALICE, valid_from="2022-01-01", chunk="chunk-2")
    report = cf.detect([early, late])
    assert report.superseded == [early.claim_id]


def test_superseded_claims_remain_queryable_history():
    """Supersession is a status change, never a deletion: "who led this in
    2019" must stay answerable after a successor arrives."""
    early = _claim(obj=BOB, valid_from="2019-01-01", chunk="chunk-1")
    late = _claim(obj=ALICE, valid_from="2022-01-01", chunk="chunk-2")
    report = cf.detect([early, late])
    early.status = report.status_changes[early.claim_id]
    assert early.status == t.STATUS_SUPERSEDED
    assert early.valid_from == "2019-01-01"
    assert early.object_entity_id == BOB
    assert early.quote


def test_a_disputed_claim_is_not_downgraded_to_superseded():
    """An unresolved contradiction is not cured by a third claim outranking one
    side of it."""
    a = _claim(obj=BOB, valid_from="2026-01-01", chunk="chunk-1")
    b = _claim(obj=ALICE, valid_from="2026-01-01", chunk="chunk-2")
    c = _claim(obj=ORG_A, valid_from="2026-01-01", basis=t.BASIS_STATED,
               chunk="chunk-3")
    report = cf.detect([a, b, c])
    assert report.status_changes[a.claim_id] == t.STATUS_DISPUTED
    assert report.status_changes[b.claim_id] == t.STATUS_DISPUTED


# --------------------------------------------------------------------------- #
# D — current-state eligibility
# --------------------------------------------------------------------------- #

def test_disputed_claims_never_become_current_state():
    """The safety property: traversal under-reports rather than mis-reports."""
    claim = _claim(obj=BOB, valid_from="2019-01-01", status=t.STATUS_DISPUTED)
    assert not cf.is_current_state_eligible(claim, as_of="2020-01-01")


@pytest.mark.parametrize(
    "status", [t.STATUS_SUPERSEDED, t.STATUS_RETRACTED, t.STATUS_DISPUTED]
)
def test_only_active_claims_are_current_state_eligible(status):
    claim = _claim(obj=BOB, valid_from="2019-01-01", status=status)
    assert not cf.is_current_state_eligible(claim, as_of="2020-01-01")


def test_open_ended_claim_is_current():
    claim = _claim(obj=BOB, valid_from="2019-01-01")
    assert cf.is_current_state_eligible(claim, as_of="2026-01-01")


def test_a_closed_interval_that_ended_is_history_not_current():
    claim = _claim(obj=BOB, valid_from="2019-01-01", valid_until="2021-01-01")
    assert cf.is_current_state_eligible(claim, as_of="2020-01-01")
    assert not cf.is_current_state_eligible(claim, as_of="2026-01-01")


def test_a_claim_that_has_not_started_is_not_current():
    claim = _claim(obj=BOB, valid_from="2030-01-01")
    assert not cf.is_current_state_eligible(claim, as_of="2026-01-01")


def test_an_undated_claim_is_not_current_state():
    """A relationship with no validity is not evidence about now."""
    claim = _claim(obj=BOB, basis=t.BASIS_UNKNOWN)
    assert not cf.is_current_state_eligible(claim, as_of="2026-01-01")


def test_current_state_claims_filters_a_batch():
    current = _claim(obj=BOB, valid_from="2019-01-01", chunk="chunk-1")
    past = _claim(obj=ALICE, valid_from="2010-01-01", valid_until="2012-01-01",
                  chunk="chunk-2")
    kept = cf.current_state_claims([current, past], as_of="2026-01-01")
    assert [c.claim_id for c in kept] == [current.claim_id]


# --------------------------------------------------------------------------- #
# E — CMS-field provenance
# --------------------------------------------------------------------------- #

def test_editing_a_cms_field_value_yields_a_different_claim():
    """The answer to "can an edit silently change a claim's meaning?" — no,
    because the value reaches the id through the object."""
    before = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_A,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", source_value="Org A",
        confidence=1.0, extraction_method="cms_field", extractor_version="test",
    )
    after = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_B,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", source_value="Org B",
        confidence=1.0, extraction_method="cms_field", extractor_version="test",
    )
    assert before.claim_id != after.claim_id


def test_source_value_is_recorded_but_not_part_of_identity():
    """Recorded for explainability; excluded from the id so re-reading the same
    value under a different spelling does not fork the claim."""
    a = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_A,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", source_value="Org A",
        confidence=1.0, extraction_method="cms_field", extractor_version="test",
    )
    b = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_A,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", source_value="Org A Ltd.",
        confidence=1.0, extraction_method="cms_field", extractor_version="test",
    )
    assert a.claim_id == b.claim_id
    assert a.source_value != b.source_value


def test_a_removed_field_value_leaves_a_stale_claim_to_retract():
    """An edit cannot change a claim's meaning, but it can leave the old claim
    behind. Retraction, not content hashing, is the correct treatment."""
    from app.knowledge.claims.extract_cms import stale_claim_ids

    old = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_A,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", confidence=1.0,
        extraction_method="cms_field", extractor_version="test",
    )
    fresh = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_B,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", confidence=1.0,
        extraction_method="cms_field", extractor_version="test",
    )
    staged = [{
        "claim_id": old.claim_id, "evidence_kind": t.EVIDENCE_CMS_FIELD,
        "document_id": "doc-1", "source_field": "field_completed_sponsors",
        "status": t.STATUS_ACTIVE,
    }]
    assert stale_claim_ids([fresh], staged) == [old.claim_id]


def test_a_field_outside_this_run_is_not_judged_stale():
    """A field the pass never looked at says nothing about its claims."""
    from app.knowledge.claims.extract_cms import stale_claim_ids

    fresh = t.build(
        subject_entity_id=PROJECT, predicate="FUNDED_BY", object_entity_id=ORG_B,
        document_id="doc-1", evidence_kind=t.EVIDENCE_CMS_FIELD,
        source_field="field_completed_sponsors", confidence=1.0,
        extraction_method="cms_field", extractor_version="test",
    )
    staged = [{
        "claim_id": "claim_other", "evidence_kind": t.EVIDENCE_CMS_FIELD,
        "document_id": "doc-1", "source_field": "field_completed_pi_name",
        "status": t.STATUS_ACTIVE,
    }]
    assert stale_claim_ids([fresh], staged) == []


# --------------------------------------------------------------------------- #
# Invariants carried forward from Phase 6
# --------------------------------------------------------------------------- #

def test_claim_id_is_unchanged_by_temporal_reinterpretation():
    """The Phase 6 invariant, re-asserted now that temporal fields are actually
    populated: reading a date must update a claim, never fork it."""
    base = _claim(obj=BOB)
    for changed in (
        _claim(obj=BOB, valid_from="2019-01-01"),
        _claim(obj=BOB, valid_until="2021-01-01"),
        _claim(obj=BOB, basis=t.BASIS_SUBJECT_PERIOD),
        _claim(obj=BOB, status=t.STATUS_DISPUTED),
    ):
        assert changed.claim_id == base.claim_id


def test_changed_evidence_produces_a_distinct_claim():
    assert _claim(obj=BOB, chunk="chunk-1").claim_id != _claim(
        obj=BOB, chunk="chunk-2"
    ).claim_id


def test_conflict_detection_is_idempotent():
    """Running the pass twice must reach the same verdict, whatever order the
    rows arrive in."""
    claims = [
        _claim(obj=BOB, valid_from="2026-01-01", chunk="chunk-1"),
        _claim(obj=ALICE, valid_from="2026-01-01", chunk="chunk-2"),
    ]
    first = cf.detect(claims)
    second = cf.detect(list(reversed(claims)))
    assert first.status_changes == second.status_changes
    assert {(l.from_claim_id, l.to_claim_id, l.kind) for l in first.links} == {
        (l.from_claim_id, l.to_claim_id, l.kind) for l in second.links
    }


def test_a_retired_predicate_cannot_be_current_state():
    claim = _claim(predicate="NO_LONGER_A_PREDICATE", obj=BOB,
                   valid_from="2019-01-01")
    assert not cf.is_current_state_eligible(claim, as_of="2020-01-01")


def test_literal_predicate_is_not_required_to_have_an_entity_object():
    claim = _claim(predicate="HAS_ROLE", obj=None, literal="Senior Director",
                   subject=BOB, valid_from="2019-01-01")
    assert cf.is_current_state_eligible(claim, as_of="2020-01-01")
