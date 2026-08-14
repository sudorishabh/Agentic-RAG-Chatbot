"""Unit tests for Neo4j projection.

No live Neo4j: a fake session records the statements and parameters that would
be sent. That is deliberate rather than a limitation — asserting on the
*emitted* Cypher is what makes the safety properties structural. A statement
that interpolated a value, or a projection that leaked a provisional identity,
fails here rather than in review.
"""

from __future__ import annotations

import pytest

from app.knowledge.graph import project as gp
from app.knowledge.graph import writer


class _Result:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def single(self):
        return self._rows[0] if self._rows else {"n": 0}

    def __iter__(self):
        return iter(self._rows)


class _FakeSession:
    """Records statements and parameters instead of running them."""

    def __init__(self, responses=None):
        self.calls: list[tuple[str, dict]] = []
        self._responses = responses or {}

    def run(self, statement, **params):
        self.calls.append((statement, params))
        for needle, rows in self._responses.items():
            if needle in statement:
                return _Result(rows)
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


# --------------------------------------------------------------------------- #
# Safety: labels and relationship types come from a code-side allow-list
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "label", ["Entity", "Person", "Organization", "Project", "Claim", "Alias"]
)
def test_allowed_labels_pass(label):
    assert writer.safe_label(label) == label


@pytest.mark.parametrize(
    "label",
    ["Person) DETACH DELETE (n", "Secret", "", "Entity;DROP", "person"],
)
def test_unknown_labels_are_refused(label):
    """Cypher cannot parameterize a label, so this is the injection surface.
    Anything not in the allow-list must raise rather than reach the driver."""
    with pytest.raises(writer.UnsafeIdentifier):
        writer.safe_label(label)


@pytest.mark.parametrize("name", ["LED_BY", "FUNDED_BY", "SUBJECT", "SUPERSEDES"])
def test_allowed_relationships_pass(name):
    assert writer.safe_relationship(name) == name


@pytest.mark.parametrize(
    "name", ["SECRETLY_CONTROLS", "LED_BY]->() DELETE r //", "", "led_by"]
)
def test_unknown_relationships_are_refused(name):
    with pytest.raises(writer.UnsafeIdentifier):
        writer.safe_relationship(name)


def test_relationship_allow_list_is_exactly_the_closed_vocabulary():
    """A predicate that is not in the vocabulary cannot become an edge type."""
    from app.knowledge.claims import predicates as vocab
    from app.knowledge.graph import schema

    for name in vocab.PREDICATE_NAMES:
        assert writer.safe_relationship(name) == name
    for name in schema.PROVENANCE_RELATIONSHIPS:
        assert writer.safe_relationship(name) == name


def test_every_statement_is_parameterized():
    """No value is ever formatted into Cypher. The only `%s` in these constants
    are the label/relationship slots, which the allow-list fills."""
    import re

    for name in dir(writer):
        if not name.isupper():
            continue
        statement = getattr(writer, name)
        if not isinstance(statement, str) or "MATCH" not in statement.upper():
            continue
        # Anything that looks like an interpolated value rather than a
        # parameter would show up as a quoted literal next to a property.
        assert not re.search(r"=\s*'", statement), name
        assert not re.search(r'=\s*"', statement), name


# --------------------------------------------------------------------------- #
# What may and may not be projected
# --------------------------------------------------------------------------- #

def _entity(entity_id, entity_type, trust="derived", eligible=1):
    return {
        "entity_id": entity_id, "entity_type": entity_type,
        "canonical_name": entity_id, "normalized_name": entity_id,
        "trust": trust, "cms_uuid": None, "source": "test", "status": "active",
        "claim_eligible": eligible,
    }


def _claim(claim_id, subject, obj=None, *, status="active", predicate="FUNDED_BY",
           valid_from="2019-01-01", valid_until=None, basis="subject_period",
           chunk=None, document="doc-1"):
    return {
        "claim_id": claim_id, "predicate": predicate,
        "subject_entity_id": subject, "object_entity_id": obj,
        "object_literal": None, "valid_from": valid_from,
        "valid_until": valid_until, "temporal_basis": basis, "confidence": 1.0,
        "status": status, "evidence_kind": "cms_field" if not chunk else "chunk",
        "source_field": "field_completed_sponsors" if not chunk else None,
        "quote": None, "quote_start": None, "quote_end": None,
        "document_id": document, "chunk_id": chunk,
        "extraction_method": "cms_field", "extractor_version": "test",
    }


def _project(monkeypatch, entities, claims, links=(), documents=(), aliases=(),
             as_of="2026-01-01"):
    monkeypatch.setattr(gp, "_load_entities", lambda: list(entities))
    monkeypatch.setattr(gp, "_load_claims", lambda: list(claims))
    monkeypatch.setattr(gp, "_load_links", lambda: list(links))
    monkeypatch.setattr(gp, "_load_aliases", lambda ids: list(aliases))
    monkeypatch.setattr(gp, "_load_documents", lambda ids: list(documents))
    session = _FakeSession()
    report = gp.project(session=session, projection_version="v-test", as_of=as_of)
    return session, report


def test_only_claim_eligible_entities_are_projected(monkeypatch):
    """`_load_entities` filters at the source, so a provisional identity never
    reaches the graph at all and no traversal can arrive at one."""
    import inspect

    source = inspect.getsource(gp._load_entities)
    assert "claim_eligible = 1" in source
    assert "status = 'active'" in source


def test_a_claim_naming_an_ineligible_entity_is_refused(monkeypatch):
    """The second gate: even a staged claim is refused if its entity is no
    longer eligible, because the entity store is authoritative at project time."""
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [
        _claim("claim_ok", "project_1", "org_1"),
        _claim("claim_bad", "project_1", "org_missing"),
        _claim("claim_bad2", "person_provisional", "org_1"),
    ]
    session, report = _project(monkeypatch, entities, claims)
    projected = {r["claim_id"] for r in session.rows_for("MERGE (cl:Claim")}
    assert projected == {"claim_ok"}
    assert report.skipped["claim_entity_not_eligible"] == 2


def test_trust_is_carried_onto_the_node(monkeypatch):
    """`pi_attested` must stay distinguishable from `authoritative` in the
    graph, or the distinction Phase 5.1 built is lost at projection."""
    entities = [
        _entity("person_1", "PERSON", trust="pi_attested"),
        _entity("person_2", "PERSON", trust="authoritative"),
    ]
    session, _ = _project(monkeypatch, entities, [])
    trust = {r["entity_id"]: r["trust"] for r in session.rows_for("MERGE (e:Entity")}
    assert trust == {"person_1": "pi_attested", "person_2": "authoritative"}


def test_typed_labels_are_applied_per_entity_type(monkeypatch):
    entities = [
        _entity("person_1", "PERSON"),
        _entity("org_1", "ORGANIZATION"),
        _entity("project_1", "PROJECT"),
    ]
    session, _ = _project(monkeypatch, entities, [])
    assert "SET e:Person" in session.statements
    assert "SET e:Organization" in session.statements
    assert "SET e:Project" in session.statements


# --------------------------------------------------------------------------- #
# Claims, evidence, and history
# --------------------------------------------------------------------------- #

def test_claims_of_every_status_are_projected(monkeypatch):
    """History is the point: a superseded claim is still the answer to "who led
    this in 2019"."""
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [
        _claim("claim_a", "project_1", "org_1", status="active"),
        _claim("claim_b", "project_1", "org_1", status="superseded"),
        _claim("claim_c", "project_1", "org_1", status="disputed"),
    ]
    session, _ = _project(monkeypatch, entities, claims)
    projected = {r["claim_id"] for r in session.rows_for("MERGE (cl:Claim")}
    assert projected == {"claim_a", "claim_b", "claim_c"}


def test_a_chunk_claim_is_supported_by_its_chunk(monkeypatch):
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1", chunk="chunk-1")]
    session, _ = _project(monkeypatch, entities, claims)
    assert session.rows_for("MERGE (c:Chunk")
    assert "MERGE (cl)-[:SUPPORTED_BY]->(c)" in session.statements


def test_a_cms_claim_is_supported_by_its_document(monkeypatch):
    """No chunk exists for a metadata fact, so evidence points at the document
    rather than inventing a span."""
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1", chunk=None)]
    session, _ = _project(monkeypatch, entities, claims)
    assert not session.rows_for("MERGE (c:Chunk")
    assert "MERGE (cl)-[:SUPPORTED_BY]->(d)" in session.statements


def test_only_chunks_carrying_a_claim_get_a_stub(monkeypatch):
    """A stub per corpus chunk would put ~149k nodes in the graph for no
    traversal benefit."""
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1", chunk="chunk-1")]
    session, _ = _project(monkeypatch, entities, claims)
    assert {r["chunk_id"] for r in session.rows_for("MERGE (c:Chunk")} == {"chunk-1"}


def test_contradiction_and_supersession_links_are_projected(monkeypatch):
    entities = [_entity("project_1", "PROJECT"), _entity("person_1", "PERSON")]
    claims = [
        _claim("claim_a", "project_1", "person_1", predicate="LED_BY"),
        _claim("claim_b", "project_1", "person_1", predicate="LED_BY"),
    ]
    links = [
        {"from_claim_id": "claim_a", "to_claim_id": "claim_b",
         "kind": "supersedes", "reason": "later start"},
        {"from_claim_id": "claim_b", "to_claim_id": "claim_a",
         "kind": "contradicts", "reason": "overlap"},
    ]
    session, report = _project(monkeypatch, entities, claims, links=links)
    assert "SUPERSEDES" in report.relationships
    assert "CONTRADICTS" in report.relationships


def test_a_link_to_an_unprojected_claim_is_dropped(monkeypatch):
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1")]
    links = [{"from_claim_id": "claim_a", "to_claim_id": "claim_missing",
              "kind": "supersedes", "reason": "x"}]
    _, report = _project(monkeypatch, entities, claims, links=links)
    assert "SUPERSEDES" not in report.relationships


# --------------------------------------------------------------------------- #
# Derived current state — the narrowest thing the graph asserts
# --------------------------------------------------------------------------- #

def test_disputed_claims_produce_no_current_state_edge(monkeypatch):
    """The safety property the whole conflict layer exists to produce."""
    entities = [_entity("project_1", "PROJECT"), _entity("person_1", "PERSON")]
    claims = [_claim("claim_a", "project_1", "person_1", predicate="LED_BY",
                     status="disputed")]
    _, report = _project(monkeypatch, entities, claims)
    assert not any("current" in key for key in report.relationships)


@pytest.mark.parametrize("status", ["superseded", "retracted", "disputed"])
def test_only_active_claims_become_current_state(monkeypatch, status):
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1", status=status)]
    _, report = _project(monkeypatch, entities, claims)
    assert not any("current" in key for key in report.relationships)


def test_an_expired_claim_is_history_not_current(monkeypatch):
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1",
                     valid_from="2010-01-01", valid_until="2012-01-01")]
    _, report = _project(monkeypatch, entities, claims, as_of="2026-01-01")
    assert not any("current" in key for key in report.relationships)
    # ...but the claim itself is still projected.
    assert report.nodes["Claim"] == 1


def test_an_open_ended_claim_is_current(monkeypatch):
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1", valid_from="2019-01-01")]
    session, report = _project(monkeypatch, entities, claims, as_of="2026-01-01")
    assert report.relationships["FUNDED_BY (current)"] == 1
    row = session.rows_for("MERGE (s)-[r:FUNDED_BY")[0]
    assert row["claim_id"] == "claim_a"


def test_every_current_edge_carries_its_claim_id(monkeypatch):
    """The provenance contract: edge -> claim_id -> claim -> chunk/document."""
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1")]
    session, _ = _project(monkeypatch, entities, claims)
    assert "MERGE (s)-[r:FUNDED_BY {claim_id: row.claim_id}]->(o)" in session.statements


def test_a_literal_claim_never_becomes_an_edge(monkeypatch):
    """A role is a property, not a relationship between two nodes."""
    entities = [_entity("person_1", "PERSON")]
    claims = [_claim("claim_a", "person_1", None, predicate="HAS_ROLE")]
    claims[0]["object_literal"] = "Senior Director"
    _, report = _project(monkeypatch, entities, claims)
    assert not any("current" in key for key in report.relationships)


def test_stale_generations_are_removed(monkeypatch):
    """A claim that stopped being current loses its edge without anything having
    to remember the edge existed."""
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    session, _ = _project(monkeypatch, entities, [])
    assert "r.projection_version <> $projection_version" in session.statements


def test_projection_version_is_a_parameter_not_interpolated(monkeypatch):
    entities = [_entity("project_1", "PROJECT")]
    session, _ = _project(monkeypatch, entities, [])
    versioned = [
        params for statement, params in session.calls
        if "$projection_version" in statement
    ]
    assert versioned
    assert all(p.get("projection_version") == "v-test" for p in versioned)


def test_projection_versions_are_distinct_per_run():
    from datetime import datetime, timezone

    a = gp.make_projection_version(at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    b = gp.make_projection_version(at=datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert a != b and a.startswith(gp.PROJECTOR_VERSION)


# --------------------------------------------------------------------------- #
# Idempotency
# --------------------------------------------------------------------------- #

def test_every_write_is_a_merge_on_a_deterministic_key():
    """What makes re-projection an update rather than a duplication."""
    for name in (
        "MERGE_ENTITY", "MERGE_ALIAS", "MERGE_CLAIM", "MERGE_CHUNK",
        "MERGE_DOCUMENT", "MERGE_PREDICATE",
    ):
        statement = getattr(writer, name)
        assert "MERGE" in statement
        assert "CREATE " not in statement


def test_repeated_projection_emits_identical_rows(monkeypatch):
    entities = [_entity("project_1", "PROJECT"), _entity("org_1", "ORGANIZATION")]
    claims = [_claim("claim_a", "project_1", "org_1")]
    first, _ = _project(monkeypatch, entities, claims)
    second, _ = _project(monkeypatch, entities, claims)
    assert first.rows_for("MERGE (cl:Claim") == second.rows_for("MERGE (cl:Claim")
    assert first.statements == second.statements


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #

def test_verification_flags_a_disputed_claim_with_an_edge(monkeypatch):
    """The check worth having: a recount would not catch this."""
    from app.knowledge.graph import verify as gv

    monkeypatch.setattr(gv, "__name__", gv.__name__)
    session = _FakeSession(responses={
        "c.status <> 'active'": [{"claim_id": "claim_x", "status": "disputed"}],
    })
    monkeypatch.setattr(
        "app.knowledge.graph.project._load_entities", lambda: []
    )
    monkeypatch.setattr("app.catalog.assertions.all_staged", lambda: [])
    monkeypatch.setattr(
        "app.catalog.assertions._ensure", lambda: None
    )

    class _Cur:
        def execute(self, *a, **kw):
            pass

        def fetchone(self):
            return {"n": 0}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _Conn:
        def cursor(self):
            return _Cur()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr("app.core.clients.mysql_connection", lambda: _Conn())
    report = gv.verify(session=session)
    assert not report.ok
    assert any("disputed" in problem for problem in report.problems)
