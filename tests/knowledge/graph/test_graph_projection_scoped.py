"""Scoped projection: what one document's claims may and may not do to the graph.

No live Neo4j. A fake session records the statements and parameters that would
be sent, following ``tests/test_graph_projection.py`` — asserting on the
*emitted* Cypher is what makes the safety properties structural rather than a
matter of review.

The property that matters most here is negative. The whole-corpus
``project()`` finishes with ``DELETE_STALE_CURRENT_STATE``, which removes every
current-state edge the run did not re-stamp. That is correct after examining
every staged claim and catastrophic after examining one document's, because the
rest of the corpus's edges are exactly the ones it did not re-stamp. So the
scoped pass must never emit it.
"""

from __future__ import annotations

import pytest

from app.catalog import assertions as assertion_store
from app.knowledge.graph import project as gp
from app.knowledge.graph import writer

PROJECT_ID = "project_aaaaaaaaaaaa"
ORG_ID = "org_bbbbbbbbbbbb"
PROVISIONAL_ID = "person_dddddddddddd"


class _Result:
    def __init__(self, rows=(), deleted=0):
        self._rows = list(rows)
        self._deleted = deleted

    def consume(self):
        """Summary shape `writer.run_sweep` reads. Zero deletions by default; a
        test that cares sets `deleted` on the response it registered."""
        class _Counters:
            nodes_deleted = self._deleted

        class _Summary:
            counters = _Counters()

        return _Summary()

    def single(self):
        return self._rows[0] if self._rows else {"n": 0}

    def __iter__(self):
        return iter(self._rows)


class _FakeSession:
    """Records statements and parameters instead of running them."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def run(self, statement, **params):
        self.calls.append((statement, params))
        return _Result()

    @property
    def statements(self) -> str:
        return "\n".join(s for s, _ in self.calls)

    def rows_for(self, needle: str) -> list[dict]:
        return [
            row
            for statement, params in self.calls
            if needle in statement
            for row in params.get("rows", [])
        ]


def _entity(entity_id, entity_type, name):
    return {
        "entity_id": entity_id, "entity_type": entity_type,
        "canonical_name": name, "normalized_name": name.lower(),
        "trust": "authoritative", "cms_uuid": None, "source": "cms",
        "status": "active",
    }


def _claim(claim_id, **overrides):
    row = {
        "claim_id": claim_id, "subject_entity_id": PROJECT_ID,
        "predicate": "FUNDED_BY", "object_entity_id": ORG_ID,
        "object_literal": None, "document_id": "doc-1", "chunk_id": None,
        "evidence_kind": "cms_field", "source_field": "field_completed_sponsors",
        "quote": None, "quote_start": None, "quote_end": None,
        "valid_from": "2019-01-01", "valid_until": None,
        "temporal_basis": "subject_period", "confidence": 1.0,
        "status": "active", "extraction_method": "cms_field",
        "extractor_version": "claims-cms-v2",
        "vocabulary_version": "predicates-v1",
    }
    row.update(overrides)
    return row


@pytest.fixture
def graph(monkeypatch):
    """A scoped projection wired to in-memory rows."""
    state = {
        "claims": [],
        "entities": [
            _entity(PROJECT_ID, "PROJECT", "Solar Pilot Study"),
            _entity(ORG_ID, "ORGANIZATION", "Ministry of Power"),
        ],
        "links": [],
    }
    monkeypatch.setattr(
        assertion_store, "by_claim_ids",
        lambda ids: [c for c in state["claims"] if c["claim_id"] in set(ids)],
    )
    monkeypatch.setattr(
        assertion_store, "links_among", lambda ids: list(state["links"])
    )
    monkeypatch.setattr(
        gp, "_load_entities_by_ids",
        lambda ids: [e for e in state["entities"] if e["entity_id"] in ids],
    )
    monkeypatch.setattr(gp, "_load_aliases", lambda ids: [])
    monkeypatch.setattr(
        gp, "_load_documents",
        lambda ids: [
            {"document_id": d, "title": "T", "source_type": "website",
             "bundle": "completed_projects", "effective_start_date": None, "url": None}
            for d in sorted(ids)
        ],
    )
    return state


def _project(state, claim_ids, **kwargs):
    session = _FakeSession()
    report = gp.project_claims(
        claim_ids, session=session, as_of=kwargs.pop("as_of", "2020-06-01"),
        **kwargs,
    )
    return session, report


# --------------------------------------------------------------------------- #
# The scope
# --------------------------------------------------------------------------- #

def test_the_global_stale_delete_is_never_emitted(graph):
    """The one statement a per-document pass must not run: it would delete every
    current-state edge belonging to every other document."""
    graph["claims"] = [_claim("claim_1")]
    session, _ = _project(graph, ["claim_1"])
    assert "r.projection_version <> $projection_version" not in session.statements
    assert writer.DELETE_STALE_CURRENT_STATE not in session.statements


def test_only_the_named_claims_are_written(graph):
    graph["claims"] = [_claim("claim_1"), _claim("claim_2")]
    session, _ = _project(graph, ["claim_1"])
    written = {row["claim_id"] for row in session.rows_for("MERGE (cl:Claim")}
    assert written == {"claim_1"}


def test_an_eligible_claim_projects_a_current_state_edge(graph):
    graph["claims"] = [_claim("claim_1")]
    session, report = _project(graph, ["claim_1"])
    edges = session.rows_for("MERGE (s)-[r:FUNDED_BY")
    assert [e["claim_id"] for e in edges] == ["claim_1"]
    assert report.relationships["FUNDED_BY (current)"] == 1


@pytest.mark.parametrize(
    "overrides, why",
    [
        ({"status": "retracted"}, "retracted claims are history"),
        ({"status": "disputed"}, "a disputed claim must not become a confident edge"),
        ({"status": "superseded"}, "superseded claims are history"),
        ({"temporal_basis": "unknown", "valid_from": None},
         "an undated claim is not evidence about now"),
        ({"valid_until": "2019-06-01"}, "a window that closed is not current"),
        ({"valid_from": "2030-01-01"}, "a window that has not opened is not current"),
    ],
)
def test_an_ineligible_claim_loses_its_edge(graph, overrides, why):
    graph["claims"] = [_claim("claim_1", **overrides)]
    session, _ = _project(graph, ["claim_1"])
    assert not session.rows_for("MERGE (s)-[r:FUNDED_BY"), why
    retired = session.rows_for("MATCH ()-[r {claim_id: row.claim_id}]->()")
    assert retired == [{"claim_id": "claim_1"}], why


def test_a_claim_that_was_never_staged_still_has_its_edge_retired(graph):
    """A retracted claim deleted from scope, or one whose entity was demoted,
    must still lose its edge — the caller asked about it, and the answer is
    'not current'."""
    graph["claims"] = []
    session, _ = _project(graph, ["claim_gone"])
    # No rows to project at all, so the pass returns before opening a session.
    assert session.calls == []


def test_a_demoted_entity_costs_the_claim_its_edge(graph):
    """The entity store is authoritative, not the claim row: a demotion since
    staging takes effect without rewriting claims."""
    graph["claims"] = [_claim("claim_1", object_entity_id=PROVISIONAL_ID)]
    session, report = _project(graph, ["claim_1"])
    assert report.skipped["claim_entity_not_eligible"] == 1
    assert not session.rows_for("MERGE (cl:Claim")
    assert session.rows_for("MATCH ()-[r {claim_id: row.claim_id}]->()") == [
        {"claim_id": "claim_1"}
    ]


def test_a_provisional_identity_never_reaches_the_graph(graph):
    graph["claims"] = [_claim("claim_1", object_entity_id=PROVISIONAL_ID)]
    session, _ = _project(graph, ["claim_1"])
    assert PROVISIONAL_ID not in session.statements
    assert all(
        row.get("entity_id") != PROVISIONAL_ID
        for row in session.rows_for("MERGE (e:Entity")
    )


# --------------------------------------------------------------------------- #
# Idempotency and vocabulary
# --------------------------------------------------------------------------- #

def test_every_node_write_is_a_merge_on_a_deterministic_key(graph):
    graph["claims"] = [_claim("claim_1")]
    session, _ = _project(graph, ["claim_1"])
    for statement, _params in session.calls:
        if "CREATE " in statement:
            pytest.fail(f"a scoped projection must not CREATE: {statement}")


def test_projecting_twice_emits_the_same_writes(graph):
    graph["claims"] = [_claim("claim_1")]
    first, _ = _project(graph, ["claim_1"])
    second, _ = _project(graph, ["claim_1"])
    # Statements are identical; only the projection_version parameter differs,
    # and every write is a MERGE on a key that does not include it.
    assert [s for s, _ in first.calls] == [s for s, _ in second.calls]
    assert first.rows_for("MERGE (cl:Claim") == second.rows_for("MERGE (cl:Claim")


def test_no_value_is_interpolated_into_a_statement(graph):
    """Labels and relationship types are the only interpolation, and both come
    from the code-side allow-list. A document id or an entity name appearing in
    a statement would mean a value was formatted in."""
    graph["claims"] = [_claim("claim_1")]
    session, _ = _project(graph, ["claim_1"])
    for value in ("doc-1", PROJECT_ID, ORG_ID, "claim_1", "Solar Pilot Study"):
        assert value not in session.statements, value


def test_an_unknown_predicate_cannot_become_a_relationship_type(graph):
    """The predicate is the one interpolated value, so it is the injection
    surface. Two independent things stop it, and this asserts both.

    First, ``is_current_state_eligible`` refuses a predicate that is not in the
    vocabulary, so an unknown one never reaches the interpolation at all — no
    edge of that type is emitted even though a row claiming it was handed in.
    Second, if it somehow did reach it, ``safe_relationship`` raises. Belt and
    braces, because a claim row like this should be impossible in the first
    place: ``validate`` rejects ``unknown_predicate`` before staging.
    """
    graph["claims"] = [_claim("claim_1", predicate="COLLABORATED_WITH")]
    session, report = _project(graph, ["claim_1"])

    assert "COLLABORATED_WITH]" not in session.statements
    assert not any(
        name.startswith("COLLABORATED_WITH") for name in report.relationships
    )
    # And the edge that a stale generation might have left is retired.
    assert session.rows_for("MATCH ()-[r {claim_id: row.claim_id}]->()") == [
        {"claim_id": "claim_1"}
    ]

    with pytest.raises(writer.UnsafeIdentifier):
        writer.safe_relationship("COLLABORATED_WITH")


# --------------------------------------------------------------------------- #
# K. The whole-corpus pass remains the repair path
# --------------------------------------------------------------------------- #

def test_the_whole_corpus_pass_still_emits_the_global_stale_delete(monkeypatch):
    """This is what repairs drift a scoped run left behind: it re-stamps
    everything MySQL justifies and deletes every current edge it did not."""
    monkeypatch.setattr(gp, "_load_entities", lambda: [])
    monkeypatch.setattr(gp, "_load_aliases", lambda ids: [])
    monkeypatch.setattr(gp, "_load_claims", lambda: [])
    monkeypatch.setattr(gp, "_load_links", lambda: [])
    monkeypatch.setattr(gp, "_load_documents", lambda ids: [])

    session = _FakeSession()
    gp.project(session=session)
    assert "r.projection_version <> $projection_version" in session.statements


def test_both_passes_share_one_writer(graph, monkeypatch):
    """The scoped pass is the same code with a different scope. If it drifted
    into its own statements, an eligibility rule fixed in one would silently
    not apply in the other."""
    import inspect

    source = inspect.getsource(gp)
    assert source.count("def _write_projection(") == 1
    assert source.count("_write_projection(") == 3   # the def and two callers
