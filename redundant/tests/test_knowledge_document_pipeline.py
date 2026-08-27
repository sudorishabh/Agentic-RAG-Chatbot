"""The per-document knowledge stage: ordering, gates, idempotency, retry.

No MySQL, no Qdrant, no Neo4j and no model. Every store is replaced with an
in-memory double that records what was written, and the *real*
``app.knowledge`` stages run against it — so what these tests exercise is the
orchestration and the gates, which is exactly what was untested before this
module existed. The stage implementations themselves are covered by the
entity-resolution, claim-extraction and projection suites.

The entity index is a real :class:`app.knowledge.candidates.EntityIndex` built
from a payload rather than a stub, because eligibility, CMS object lookup and
resolution all read it differently and a stub that satisfied one would quietly
mislead the others.
"""

from __future__ import annotations

import pytest

from app.catalog import assertions as assertion_store
from app.catalog import entities as entity_store
from app.catalog import knowledge_runs as run_store
from app.catalog import mentions as mention_store
from app.catalog import predicate_candidates as candidate_store
from app.knowledge import candidates as candidates_mod
from app.knowledge import document_pipeline as dp
from app.knowledge.candidates import EntityIndex
from app.knowledge.claims import types as claim_types

PROJECT_DOC = "doc-project-1"
PROJECT_ID = "project_aaaaaaaaaaaa"
ORG_ID = "org_bbbbbbbbbbbb"
PERSON_ID = "person_cccccccccccc"
PROVISIONAL_PERSON_ID = "person_dddddddddddd"


# --------------------------------------------------------------------------- #
# Doubles
# --------------------------------------------------------------------------- #

def _entity_index() -> EntityIndex:
    """Three claim-eligible identities and one provisional person.

    The provisional person is the population this corpus is mostly made of, and
    the reason the eligibility gate exists: it is a *name*, not a person.
    """
    entities = {
        PROJECT_ID: {
            "entity_id": PROJECT_ID, "entity_type": "PROJECT",
            "canonical_name": "Solar Pilot Study",
            "normalized_name": "solar pilot study", "trust": "authoritative",
            "source": "cms", "claim_eligible": 1, "cms_uuid": PROJECT_DOC,
        },
        ORG_ID: {
            "entity_id": ORG_ID, "entity_type": "ORGANIZATION",
            "canonical_name": "Ministry of Power",
            "normalized_name": "ministry of power", "trust": "derived",
            "source": "cms", "claim_eligible": 1, "cms_uuid": None,
        },
        PERSON_ID: {
            "entity_id": PERSON_ID, "entity_type": "PERSON",
            "canonical_name": "Asha Rao", "normalized_name": "asha rao",
            "trust": "authoritative", "source": "cms", "claim_eligible": 1,
            "cms_uuid": "person-uuid-1",
        },
        PROVISIONAL_PERSON_ID: {
            "entity_id": PROVISIONAL_PERSON_ID, "entity_type": "PERSON",
            "canonical_name": "Arun Kumar", "normalized_name": "arun kumar",
            "trust": "provisional", "source": "author_facet",
            "claim_eligible": 0, "cms_uuid": None,
        },
    }
    aliases = [
        {"entity_id": ORG_ID, "normalized": "ministry of power",
         "surface": "Ministry of Power", "alias_type": "name",
         "autolink": 1, "is_ambiguous": 0},
    ]
    return EntityIndex(
        {"entities": entities, "aliases": aliases, "identifiers": {}}
    )


class Stores:
    """Every write the stage can make, held in memory."""

    def __init__(self) -> None:
        self.staged: dict[str, object] = {}
        self.rejections: list[object] = []
        self.retracted: list[str] = []
        self.status_changes: dict[str, str] = {}
        self.links: list[object] = []
        self.mentions: list[object] = []
        self.decisions: list[object] = []
        self.extractions: dict[str, int] = {}
        self.cache: dict[str, int] = {}
        self.candidates: list[object] = []
        self.runs: list[object] = []
        self.projected: list[list[str]] = []
        self.existing: list[dict] = []          # rows already in the store
        self.deleted_mentions: list[tuple] = []
        self.deleted_decisions: list[tuple] = []
        self.calls: list[str] = []              # ordering witness
        self.fail: set[str] = set()             # names that should raise

    # -- assertions ------------------------------------------------------- #
    def stage(self, assertions):
        self._maybe_fail("stage")
        self.calls.append("stage")
        for a in assertions:
            self.staged[a.claim_id] = a
        return len(assertions)

    def record_rejections(self, rejections):
        self.calls.append("record_rejections")
        self.rejections.extend(rejections)
        return len(rejections)

    def for_document(self, document_id):
        return [r for r in self.existing if r["document_id"] == document_id]

    def retract(self, claim_ids):
        self.calls.append("retract")
        self.retracted.extend(claim_ids)
        for row in self.existing:
            if row["claim_id"] in claim_ids:
                row["status"] = "retracted"
        return len(claim_ids)

    def for_subject_predicates(self, pairs):
        wanted = set(pairs)
        return [
            r for r in self.existing
            if (r["subject_entity_id"], r["predicate"]) in wanted
        ]

    def apply_status(self, changes):
        self.calls.append("apply_status")
        self.status_changes.update(changes)
        return len(changes)

    def save_links(self, links, *, detector):
        self.calls.append("save_links")
        self.links.extend(links)
        return len(links)

    # -- mentions / decisions --------------------------------------------- #
    def cached_extraction(self, content_hash, key):
        return self.cache.get(content_hash)

    def save_mentions(self, mentions, *, doc_version=None):
        self._maybe_fail("save_mentions")
        self.calls.append("save_mentions")
        self.mentions.extend(mentions)
        return len(mentions)

    def record_extraction(self, content_hash, key, version, count, error=None):
        self.calls.append("record_extraction")
        self.extractions[content_hash] = count
        self.cache[content_hash] = count

    def delete_document_mentions(self, document_id, *, doc_version=None,
                                 before_version=None):
        self.calls.append("delete_document_mentions")
        self.deleted_mentions.append((document_id, doc_version, before_version))
        return 0

    def save_decisions(self, decisions):
        self.calls.append("save_decisions")
        self.decisions.extend(decisions)
        return len(decisions)

    def delete_decisions_before_version(self, document_id, doc_version):
        self.calls.append("delete_decisions_before_version")
        self.deleted_decisions.append((document_id, doc_version))
        return 0

    # -- candidates / runs ------------------------------------------------- #
    def record_candidates(self, candidates):
        self.calls.append("record_candidates")
        self.candidates.extend(candidates)
        return len(candidates)

    def record_run(self, report):
        self.calls.append("record_run")
        self.runs.append(report)
        return True

    def _maybe_fail(self, name):
        if name in self.fail:
            raise RuntimeError(f"{name} is unavailable")


@pytest.fixture
def stores(monkeypatch):
    s = Stores()
    index = _entity_index()

    monkeypatch.setattr(candidates_mod, "get_entity_index", lambda: index)
    for name in ("stage", "record_rejections", "for_document", "retract",
                 "for_subject_predicates", "apply_status", "save_links"):
        monkeypatch.setattr(assertion_store, name, getattr(s, name))
    for name in ("cached_extraction", "save_mentions", "record_extraction",
                 "delete_document_mentions"):
        monkeypatch.setattr(mention_store, name, getattr(s, name))
    monkeypatch.setattr(entity_store, "save_decisions", s.save_decisions)
    monkeypatch.setattr(entity_store, "delete_decisions_before_version",
                        s.delete_decisions_before_version)
    monkeypatch.setattr(candidate_store, "record", s.record_candidates)
    monkeypatch.setattr(run_store, "record", s.record_run)

    # Projection is exercised on its own below; here it only has to be visible.
    def _project_claims(claim_ids, **kwargs):
        s.calls.append("project_claims")
        s.projected.append(sorted(claim_ids))
        from app.knowledge.graph.project import ProjectionReport

        return ProjectionReport(projection_version="test-projection")

    monkeypatch.setattr("app.knowledge.graph.project.project_claims", _project_claims)
    monkeypatch.setattr("app.knowledge.graph.schema.ensure_graph_schema", lambda: 0)
    monkeypatch.setattr("app.core.clients.graph_available", lambda: True)
    s.index = index
    return s


def _project_meta(**overrides):
    meta = {
        "field_completed_sponsors": ["Ministry of Power"],
        "field_completed_pi_name": ["Asha Rao"],
        "field_completed_start_date": "2019-01-01",
        # Inside app.knowledge.claims.types.MAX_YEAR (today + 5) and still open
        # at the fixed `as_of` below, so these claims are current-state
        # eligible. A date beyond MAX_YEAR is extraction noise and validation
        # rejects it, which is correct and is not what these tests are about.
        "field_completed_end_date": "2030-01-01",
    }
    meta.update(overrides)
    return meta


def _document(**overrides):
    fields = {
        "document_id": PROJECT_DOC,
        "doc_version": 1,
        "chunks": (dp.ChunkText("chunk-1", "Ministry of Power funded it.", "h1"),),
        "source_type": "website",
        "bundle": "completed_projects",
        "raw_meta": _project_meta(),
    }
    fields.update(overrides)
    return dp.DocumentInput(**fields)


def _options(**overrides):
    fields = {
        "with_llm_claims": False, "with_projection": True,
        "budget_seconds": 30.0, "llm_max_calls": 8, "min_confidence": 0.6,
        "as_of": "2020-06-01",
    }
    fields.update(overrides)
    return dp.StageOptions(**fields)


def _staged_row(claim_id, **overrides):
    row = {
        "claim_id": claim_id, "subject_entity_id": PROJECT_ID,
        "predicate": "LED_BY", "object_entity_id": PERSON_ID,
        "object_literal": None, "document_id": "other-doc", "chunk_id": None,
        "evidence_kind": "cms_field", "source_field": "field_completed_pi_name",
        "quote": None, "quote_start": None, "quote_end": None,
        "valid_from": "2019-01-01", "valid_until": None,
        "temporal_basis": "subject_period", "confidence": 1.0,
        "status": "active", "extraction_method": "cms_field",
        "extractor_version": "claims-cms-v2",
        "vocabulary_version": "predicates-v1", "model": None,
        "prompt_version": None,
    }
    row.update(overrides)
    return row


# --------------------------------------------------------------------------- #
# B. Stage ordering, and what is deliberately absent
# --------------------------------------------------------------------------- #

def test_the_stages_run_in_dependency_order(stores):
    report = dp.process_document(_document(), _options())
    names = [s.name for s in report.stages]
    assert names == [
        "prelude", "supersede", "mentions", "resolution", "claims",
        "validate", "persist", "conflicts", "project",
    ]


def test_global_entity_work_is_never_done_per_document(stores, monkeypatch):
    """Seeding, acronym mining, ambiguity marking and PI promotion are
    corpus-wide passes. Running any of them here would take a global decision on
    one document's evidence, which is how false merges get committed."""
    from app.knowledge import pi_promotion, seed

    def forbidden(name):
        def _call(*a, **kw):
            raise AssertionError(f"{name} must not run per document")
        return _call

    monkeypatch.setattr(seed, "build_seed_entities", forbidden("build_seed_entities"))
    monkeypatch.setattr(seed, "mine_acronym_aliases", forbidden("mine_acronym_aliases"))
    monkeypatch.setattr(entity_store, "mark_ambiguous_aliases",
                        forbidden("mark_ambiguous_aliases"))
    monkeypatch.setattr(pi_promotion, "evaluate_promotions",
                        forbidden("evaluate_promotions"))
    monkeypatch.setattr(pi_promotion, "apply_promotions", forbidden("apply_promotions"))

    report = dp.process_document(_document(), _options())
    assert report.status == "ok"


def test_a_dry_run_reaches_every_gate_and_writes_nothing(stores):
    report = dp.process_document(_document(), _options(dry_run=True))
    assert report.claims_built == 2      # the sponsor and the PI
    assert stores.staged == {}
    assert stores.calls == []
    assert report.projection_status == "skipped"


# --------------------------------------------------------------------------- #
# C. Mentions: optional, cached, isolated
# --------------------------------------------------------------------------- #

def test_mentions_are_off_by_default(stores):
    report = dp.process_document(_document(), _options())
    assert [s for s in report.stages if s.name == "mentions"][0].skipped
    assert stores.mentions == []


def test_mentions_run_when_asked(stores):
    report = dp.process_document(_document(), _options(with_mentions=True))
    assert report.mentions >= 1
    assert stores.mentions
    assert "save_mentions" in stores.calls


def test_a_cached_chunk_is_not_re_extracted(stores):
    stores.cache["h1"] = 3
    report = dp.process_document(_document(), _options(with_mentions=True))
    assert report.chunks_cached == 1
    assert stores.mentions == []


def test_the_extraction_cache_is_recorded_only_after_resolution(stores):
    """A crash between extracting and resolving must re-run the chunk, not mark
    it done. So the cache write follows resolution, never precedes it."""
    dp.process_document(_document(), _options(with_mentions=True))
    assert stores.calls.index("save_decisions") < stores.calls.index("record_extraction")


def test_one_chunk_failing_costs_only_that_chunk(stores):
    doc = _document(chunks=(
        dp.ChunkText("chunk-1", "Ministry of Power funded it.", "h1"),
        dp.ChunkText("chunk-2", "Ministry of Power funded it too.", "h2"),
    ))
    calls = {"n": 0}

    from app.knowledge import extract as extract_mod

    original = extract_mod.extract_mentions

    def flaky(text, **kwargs):
        calls["n"] += 1
        if kwargs.get("chunk_id") == "chunk-1":
            raise RuntimeError("unreadable")
        return original(text, **kwargs)

    extract_mod.extract_mentions = flaky
    try:
        report = dp.process_document(_document(chunks=doc.chunks),
                                     _options(with_mentions=True))
    finally:
        extract_mod.extract_mentions = original

    assert calls["n"] == 2                       # the second chunk still ran
    assert report.status == "partial"
    assert any(e["id"] == "chunk-1" for e in report.errors)
    assert report.mentions >= 1                  # chunk-2's mentions survived


# --------------------------------------------------------------------------- #
# D. Claims
# --------------------------------------------------------------------------- #

def test_cms_claims_are_extracted_for_one_document(stores):
    report = dp.process_document(_document(), _options())
    assert report.claims_built == 2
    predicates = sorted(a.predicate for a in stores.staged.values())
    assert predicates == ["FUNDED_BY", "LED_BY"]
    funded = next(a for a in stores.staged.values() if a.predicate == "FUNDED_BY")
    assert funded.subject_entity_id == PROJECT_ID
    assert funded.object_entity_id == ORG_ID
    assert funded.temporal_basis == "subject_period"
    assert funded.evidence_kind == "cms_field"


def test_a_non_project_document_produces_no_cms_claims(stores):
    report = dp.process_document(
        _document(document_id="doc-news-1", bundle="news", raw_meta={}), _options()
    )
    assert report.claims_built == 0
    assert stores.staged == {}


def test_a_provisional_person_may_not_carry_a_claim(stores):
    """The eligibility gate, reached from the ingest path exactly as it is from
    the corpus builder. 'Arun Kumar' is a name the corpus attests, not a person
    it has distinguished, so a claim about him asserts something unestablished."""
    report = dp.process_document(
        _document(raw_meta=_project_meta(field_completed_pi_name=["Arun Kumar"])),
        _options(),
    )
    assert report.rejection_counts == {"object_not_claim_eligible": 1}
    assert [a.predicate for a in stores.staged.values()] == ["FUNDED_BY"]
    assert len(stores.rejections) == 1


def test_a_project_with_no_seeded_entity_stages_nothing_and_says_so(stores):
    report = dp.process_document(_document(document_id="doc-unseeded"), _options())
    assert report.claims_built == 0
    claims_stage = [s for s in report.stages if s.name == "claims"][0]
    assert any("no canonical PROJECT entity yet" in n for n in claims_stage.notes)
    assert stores.staged == {}


# --------------------------------------------------------------------------- #
# E. Unknown entities and unknown predicates
# --------------------------------------------------------------------------- #

def test_an_unresolved_name_creates_no_entity_and_no_claim(stores):
    """A name nothing in the store matches leaves a sighting and a verdict, and
    nothing else. No id is minted, so nothing downstream can reference it."""
    doc = _document(chunks=(
        dp.ChunkText("chunk-1", "Dr Nobody Whatsoever chaired the panel.", "h9"),
    ))
    report = dp.process_document(doc, _options(with_mentions=True))
    assert report.entities_unresolved >= 1
    assert report.entities_auto == 0
    linked = [d for d in stores.decisions if d.entity_id]
    assert linked == []
    # Nothing about the unresolved name reached the claim layer.
    assert all(
        a.subject_entity_id in {PROJECT_ID, ORG_ID, PERSON_ID}
        for a in stores.staged.values()
    )


def test_an_unknown_predicate_is_captured_but_never_staged(stores, monkeypatch):
    """The whole point of the pending table: the claim is still refused, but the
    evidence that would have justified a vocabulary entry survives."""
    from app.knowledge.claims import pending

    text = "Ministry of Power collaborated closely with the study team."
    candidate = pending.build(
        predicate_surface="collaborated with", subject_entity_id=PROJECT_ID,
        object_entity_id=ORG_ID, document_id=PROJECT_DOC, chunk_id="chunk-1",
        chunk_text=text, quote="collaborated closely with the study team",
        confidence=0.8, extractor_version="claims-llm-v1",
    )
    assert candidate is not None

    monkeypatch.setattr(
        "app.knowledge.claims.extract_llm.extract_claims_for_chunk",
        lambda *a, **kw: ([], [candidate]),
    )
    doc = _document(chunks=(dp.ChunkText("chunk-1", text, "h1"),))
    report = dp.process_document(
        doc, _options(with_mentions=True, with_llm_claims=True)
    )

    assert report.pending_predicates == 1
    assert stores.candidates[0].predicate_normalized == "COLLABORATED_WITH"
    assert stores.candidates[0].quote == "collaborated closely with the study team"
    assert stores.candidates[0].status == "pending"
    # Never a claim, and never a graph relationship type.
    assert all(a.predicate != "COLLABORATED_WITH" for a in stores.staged.values())


def test_a_pending_predicate_can_never_become_a_relationship_type():
    from app.knowledge.graph import writer

    with pytest.raises(writer.UnsafeIdentifier):
        writer.safe_relationship("COLLABORATED_WITH")


# --------------------------------------------------------------------------- #
# F. Conflicts, across documents
# --------------------------------------------------------------------------- #

def test_conflict_detection_sees_claims_from_other_documents(stores):
    """LED_BY is functional, and a contradiction about one project is inherently
    cross-document. A batch holding only this document's claims would miss it."""
    stores.existing.append(_staged_row(
        "claim_other", object_entity_id=PROVISIONAL_PERSON_ID,
        document_id="other-doc", valid_from="2019-01-01",
    ))
    report = dp.process_document(_document(), _options())
    conflicts = [s for s in report.stages if s.name == "conflicts"][0]
    assert conflicts.counts["siblings"] == 1
    assert report.conflicts_disputed == 2
    assert stores.status_changes["claim_other"] == "disputed"


def test_a_succession_is_not_a_conflict(stores):
    """Non-overlapping windows are a change of leader, not a contradiction, and
    both claims stay active."""
    stores.existing.append(_staged_row(
        "claim_earlier", object_entity_id=PROVISIONAL_PERSON_ID,
        valid_from="2000-01-01", valid_until="2018-01-01",
    ))
    report = dp.process_document(_document(), _options())
    assert report.conflicts_disputed == 0
    assert report.conflicts_superseded == 0
    assert stores.status_changes == {}


def test_status_is_applied_before_links_are_saved(stores):
    """The interruption-safe order. Statuses first means a crash between the two
    leaves a suppressed claim missing its audit link, rather than an
    unsuppressed claim projecting an edge it should not."""
    stores.existing.append(_staged_row(
        "claim_other", object_entity_id=PROVISIONAL_PERSON_ID,
    ))
    dp.process_document(_document(), _options())
    assert stores.calls.index("apply_status") < stores.calls.index("save_links")


# --------------------------------------------------------------------------- #
# G. Projection scope
# --------------------------------------------------------------------------- #

def test_projection_is_scoped_to_the_claims_this_run_touched(stores):
    stores.existing.append(_staged_row("claim_other",
                                       object_entity_id=PROVISIONAL_PERSON_ID))
    dp.process_document(_document(), _options())
    projected = stores.projected[0]
    # This document's two claims, plus the sibling whose status just changed.
    assert "claim_other" in projected
    assert len(projected) == 3


def test_projection_is_skipped_when_neo4j_is_unreachable(stores, monkeypatch):
    monkeypatch.setattr("app.core.clients.graph_available", lambda: False)
    report = dp.process_document(_document(), _options())
    assert report.projection_status == "unreachable"
    assert report.status == "partial"
    # MySQL still has the claims: a graph outage is a lag, never a loss.
    assert len(stores.staged) == 2


def test_a_projection_failure_does_not_lose_the_claims(stores, monkeypatch):
    def boom(claim_ids, **kwargs):
        raise RuntimeError("neo4j exploded mid-write")

    monkeypatch.setattr("app.knowledge.graph.project.project_claims", boom)
    report = dp.process_document(_document(), _options())
    assert report.projection_status == "failed"
    assert len(stores.staged) == 2
    assert report.status == "partial"


def test_projection_can_be_turned_off_without_affecting_staging(stores):
    report = dp.process_document(_document(), _options(with_projection=False))
    assert report.projection_status == "skipped"
    assert stores.projected == []
    assert len(stores.staged) == 2


# --------------------------------------------------------------------------- #
# H. Version changes
# --------------------------------------------------------------------------- #

def test_a_new_version_retracts_claims_whose_evidence_is_gone(stores):
    """Chunk ids are version-scoped, so re-indexing strands every claim that
    cited one. Retracted rather than deleted: the claim was true of the source
    as it stood."""
    stores.existing.append(_staged_row(
        "claim_v1", document_id=PROJECT_DOC, chunk_id="old-chunk",
        evidence_kind="chunk", predicate="FUNDED_BY", object_entity_id=ORG_ID,
    ))
    report = dp.process_document(_document(doc_version=2), _options())
    assert report.claims_retracted == 1
    assert stores.retracted == ["claim_v1"]
    # And the retracted claim is projected, which is how its edge is removed.
    assert "claim_v1" in stores.projected[0]


def test_a_claim_whose_chunk_survives_is_not_retracted(stores):
    stores.existing.append(_staged_row(
        "claim_kept", document_id=PROJECT_DOC, chunk_id="chunk-1",
        evidence_kind="chunk", predicate="FUNDED_BY", object_entity_id=ORG_ID,
    ))
    report = dp.process_document(_document(doc_version=2), _options())
    assert report.claims_retracted == 0
    assert stores.retracted == []


def test_only_superseded_versions_lose_their_mentions(stores):
    """Deleting the current version's mentions would be unrecoverable: the
    extraction cache is keyed on content_hash, so they would read as already
    extracted and never come back."""
    dp.process_document(_document(doc_version=3), _options(with_mentions=True))
    assert stores.deleted_mentions == [(PROJECT_DOC, None, 3)]
    assert stores.deleted_decisions == [(PROJECT_DOC, 3)]


def test_decisions_are_dropped_before_the_mentions_they_join_against(stores):
    dp.process_document(_document(doc_version=2), _options())
    assert (
        stores.calls.index("delete_decisions_before_version")
        < stores.calls.index("delete_document_mentions")
    )


def test_a_first_version_supersedes_nothing(stores):
    report = dp.process_document(_document(doc_version=1), _options())
    assert [s for s in report.stages if s.name == "supersede"][0].skipped
    assert stores.deleted_mentions == []


# --------------------------------------------------------------------------- #
# I. Idempotency and retry
# --------------------------------------------------------------------------- #

def test_running_twice_produces_the_same_claims_and_no_duplicates(stores):
    first = dp.process_document(_document(), _options())
    ids_first = set(stores.staged)
    second = dp.process_document(_document(), _options())
    assert set(stores.staged) == ids_first
    assert len(stores.staged) == 2
    assert first.claims_built == second.claims_built
    assert first.knowledge_version == second.knowledge_version


def test_claim_ids_are_stable_across_runs(stores):
    dp.process_document(_document(), _options())
    before = sorted(stores.staged)
    stores.staged.clear()
    dp.process_document(_document(), _options())
    assert sorted(stores.staged) == before


def test_a_staging_failure_stands_the_later_stages_down(stores):
    """Conflict verdicts and graph edges about claims that are not in the store
    would be assertions about nothing."""
    stores.fail.add("stage")
    report = dp.process_document(_document(), _options())
    assert report.status == "partial"
    assert stores.projected == []
    assert stores.status_changes == {}
    assert any(e["id"] == "stage" for e in report.errors)


def test_a_staging_failure_still_retires_edges_that_were_retracted(stores):
    """The retraction committed on its own connection and is still true, so its
    edge must still go even though the new claims never landed."""
    stores.existing.append(_staged_row(
        "claim_v1", document_id=PROJECT_DOC, chunk_id="old-chunk",
        evidence_kind="chunk",
    ))
    stores.fail.add("stage")
    dp.process_document(_document(doc_version=2), _options())
    assert stores.projected == [["claim_v1"]]


def test_the_run_row_is_written_last(stores):
    dp.process_document(_document(), _options())
    assert stores.calls[-1] == "record_run"


def test_a_run_is_recorded_even_when_the_entity_index_is_unavailable(
    stores, monkeypatch
):
    monkeypatch.setattr(
        candidates_mod, "get_entity_index",
        lambda: (_ for _ in ()).throw(RuntimeError("mysql is down")),
    )
    report = dp.process_document(_document(), _options())
    assert report.status == "failed"
    assert stores.runs and stores.runs[0].status == "failed"
    assert stores.staged == {}


# --------------------------------------------------------------------------- #
# J. Budget
# --------------------------------------------------------------------------- #

def test_an_exhausted_budget_makes_the_run_partial_and_retryable(stores):
    report = dp.process_document(_document(), _options(budget_seconds=-1.0))
    assert report.status == "partial"
    assert all(
        s.skipped for s in report.stages if s.name != "prelude"
    )
    assert stores.staged == {}
    # Still recorded, so the catch-up sweep can find it.
    assert stores.runs and stores.runs[0].status == "partial"


def test_the_llm_call_budget_is_per_document(stores, monkeypatch):
    calls = {"n": 0}

    def counted(*a, **kw):
        calls["n"] += 1
        return ([], [])

    monkeypatch.setattr(
        "app.knowledge.claims.extract_llm.extract_claims_for_chunk", counted
    )
    chunks = tuple(
        dp.ChunkText(f"chunk-{i}", "Ministry of Power funded it.", f"h{i}")
        for i in range(5)
    )
    dp.process_document(
        _document(chunks=chunks),
        _options(with_mentions=True, with_llm_claims=True, llm_max_calls=2),
    )
    assert calls["n"] == 2


# --------------------------------------------------------------------------- #
# Versioning
# --------------------------------------------------------------------------- #

def test_the_knowledge_version_covers_every_rule_that_changes_output():
    from app.knowledge.version import components, knowledge_version

    parts = components()
    assert set(parts) == {
        "entity_extract", "resolver", "claims_cms", "claims_llm",
        "vocabulary", "conflicts", "projector", "gazetteer",
    }
    assert knowledge_version() == knowledge_version()
    assert knowledge_version(gazetteer_fingerprint="a") != knowledge_version(
        gazetteer_fingerprint="b"
    )


def test_the_knowledge_version_is_not_part_of_claim_identity(stores):
    """Folding a rules fingerprint into claim_id would fork every claim on every
    rule change — the exact failure the identity design exists to prevent."""
    dp.process_document(_document(), _options())
    for claim_id, assertion in stores.staged.items():
        assert claim_id == assertion.recompute_id()


def test_from_row_round_trips_a_staged_claim():
    row = _staged_row("claim_x")
    assertion = claim_types.from_row(row)
    assert assertion.claim_id == "claim_x"
    assert assertion.valid_from == "2019-01-01"
    assert assertion.status == "active"
    assert assertion.temporal_basis == "subject_period"


# --------------------------------------------------------------------------- #
# The loader: reading a document back for a retry or a CLI run
# --------------------------------------------------------------------------- #

def test_the_loader_reads_raw_meta_from_its_own_reader(monkeypatch):
    """Regression. ``StateRecord`` has a ``raw_meta`` field but
    ``state._row_to_record`` never fills it — the blob is too large to carry on
    every record ``state.load`` builds — so taking it from the record silently
    yields None and every CMS claim on this path vanishes with no error to
    explain it. The loader must ask for it directly.
    """
    from types import SimpleNamespace

    from app.catalog import state
    from app.knowledge import document_loader

    record = SimpleNamespace(
        source_type="website", bundle="completed_projects", content_hash="h",
        doc_version=1, raw_meta=None,      # exactly what state.get returns
    )
    monkeypatch.setattr(state, "get", lambda document_id: record)
    monkeypatch.setattr(state, "raw_meta_for", lambda document_id: {"field_x": 1})
    monkeypatch.setattr(
        document_loader, "load_chunks",
        lambda document_id, **kw: [dp.ChunkText("c1", "text", "h1")],
    )

    doc = document_loader.load_document(PROJECT_DOC)
    assert doc.raw_meta == {"field_x": 1}


def test_the_loader_returns_none_for_a_document_with_no_current_chunks(monkeypatch):
    from types import SimpleNamespace

    from app.catalog import state
    from app.knowledge import document_loader

    monkeypatch.setattr(
        state, "get",
        lambda document_id: SimpleNamespace(
            source_type="website", bundle=None, content_hash="", doc_version=1
        ),
    )
    monkeypatch.setattr(state, "raw_meta_for", lambda document_id: None)
    monkeypatch.setattr(document_loader, "load_chunks", lambda document_id, **kw: [])
    assert document_loader.load_document("gone") is None


def test_the_loader_returns_none_for_an_uncatalogued_document(monkeypatch):
    from app.catalog import state
    from app.knowledge import document_loader

    monkeypatch.setattr(state, "get", lambda document_id: None)
    assert document_loader.load_document("never-seen") is None


def test_the_ingest_path_corroborates_from_the_documents_own_authors(stores):
    """Ingestion has the author names in memory on the canonical document, so
    the stage takes them from there rather than paying for a facet query."""
    doc = _document(
        authors=("Dr Preeti Jain Das",),
        chunks=(dp.ChunkText("chunk-1", "Ministry of Power funded it.", "h1"),),
    )
    report = dp.process_document(doc, _options(with_mentions=True))
    assert report.status == "ok"
    # The context the resolution stage actually used.
    from app.knowledge.candidates import context_for_document

    context = context_for_document(doc.document_id, doc.raw_meta, authors=doc.authors)
    assert context.asserts("PERSON", "preeti jain das")


def test_the_loader_reads_authors_from_the_facet(monkeypatch):
    """The retry and CLI paths have no canonical document, so they read the
    facet — not `raw_meta.field_authors`, which is empty corpus-wide."""
    from types import SimpleNamespace

    from app.catalog import state
    from app.knowledge import document_loader

    monkeypatch.setattr(
        state, "get",
        lambda document_id: SimpleNamespace(
            source_type="website", bundle=None, content_hash="h", doc_version=1
        ),
    )
    monkeypatch.setattr(state, "raw_meta_for", lambda document_id: {})
    monkeypatch.setattr(state, "authors_for", lambda document_id: ["Meena Sehgal"])
    monkeypatch.setattr(
        document_loader, "load_chunks",
        lambda document_id, **kw: [dp.ChunkText("c1", "text", "h1")],
    )

    doc = document_loader.load_document(PROJECT_DOC)
    assert doc.authors == ("Meena Sehgal",)
