"""Graph retrieval: routing, templates, traversal and hydration.

No live Neo4j and no live Qdrant. A fake session returns rows and records the
statement it was given, so the tests assert on the **Cypher that would be sent**
rather than on what a server happened to return. That is what makes the safety
properties structural: a template that interpolated a value, or a caller that
found a way to pass a query instead of a template id, fails here.

The registry is enumerated rather than sampled — a template added later is
covered by the bounded-traversal and parameterization tests the moment it exists.

`test_live_graph_smoke` at the end is the one exception: it talks to a real
Neo4j and skips when there isn't one.
"""
from __future__ import annotations

import re

import pytest

from app.retrieval.graph import hydrate as hydration
from app.retrieval.graph import pipeline, router, traverse
from app.retrieval.graph import templates as reg


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


class _FakeSession:
    """Records what was run; returns canned rows."""

    def __init__(self, rows=None, *, raises: Exception | None = None):
        self._rows = rows if rows is not None else []
        self._raises = raises
        self.statements: list[str] = []
        self.parameters: list[dict] = []

    def run(self, statement, **params):
        self.statements.append(statement)
        self.parameters.append(params)
        if self._raises is not None:
            raise self._raises
        return [dict(r) for r in self._rows]


class _Record:
    """A Qdrant point."""

    def __init__(self, point_id, payload=None):
        self.id = point_id
        self.payload = payload or {"document_id": f"doc-of-{point_id}"}


class _FakeQdrant:
    def __init__(self, known=None, *, scroll_points=None, raises=False):
        self.known = set(known or [])
        self.scroll_points = scroll_points or []
        self.raises = raises
        self.retrieve_calls: list[list[str]] = []
        self.scroll_calls: list = []

    def retrieve(self, *, collection_name, ids, **kwargs):
        self.retrieve_calls.append(list(ids))
        if self.raises:
            raise RuntimeError("qdrant down")
        return [_Record(i) for i in ids if i in self.known]

    def scroll(self, *, collection_name, scroll_filter, limit, **kwargs):
        self.scroll_calls.append((scroll_filter, limit))
        if self.raises:
            raise RuntimeError("qdrant down")
        # Honour the document_id condition, and otherwise return points in
        # insertion order — which is what makes a long document able to starve
        # the rest of a batch, exactly as a real scroll would.
        wanted = _documents_in(scroll_filter)
        matched = [
            p for p in self.scroll_points
            if wanted is None or p.payload.get("document_id") in wanted
        ]
        return matched[:limit], None


def _documents_in(scroll_filter):
    """The document ids a scroll filter selects, or None if it selects none."""
    for condition in scroll_filter.must:
        if condition.key != "document_id":
            continue
        match = condition.match
        if hasattr(match, "any"):
            return set(match.any)
        return {match.value}
    return None


def _use_qdrant(monkeypatch, client):
    monkeypatch.setattr("app.core.clients.get_qdrant_client", lambda: client)


ORG = "org_aeeeb2a91bdd"
PERSON = "person_1234567890ab"
PROJECT = "project_abcdef012345"


# --------------------------------------------------------------------------- #
# The registry is closed, bounded and parameterized — enumerated, not sampled
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("template_id", reg.TEMPLATE_IDS)
def test_every_template_is_bounded(template_id):
    """Bounded traversal: a row cap, and no variable-length path."""
    template = reg.TEMPLATES[template_id]
    assert "LIMIT $limit" in template.cypher
    # `[*]`, `[*1..5]`, `[:LED_BY*]` — any of these would make depth a function
    # of the data rather than of the reviewed query text.
    assert not re.search(r"\[[^\]]*\*", template.cypher), "variable-length path"
    assert template.max_hops <= 3


@pytest.mark.parametrize("template_id", reg.TEMPLATE_IDS)
def test_every_template_is_fully_parameterized(template_id):
    """No value is formatted into a query; every one arrives as $param."""
    cypher = reg.TEMPLATES[template_id].cypher
    assert "%s" not in cypher and "{}" not in cypher
    # A `{` in a template is a map literal (`{current: true}`, `{entity_id: $x}`)
    # and every value in one must be a parameter, a boolean, or a reference to a
    # property already bound in the query — never a string built from input.
    for body in re.findall(r"\{([^}]*)\}", cypher):
        for pair in body.split(","):
            _, _, value = pair.partition(":")
            value = value.strip()
            assert (
                value.startswith("$")
                or value in ("true", "false")
                or re.fullmatch(r"\w+\.\w+", value)
            ), f"non-parameter map value in {template_id}: {pair!r}"


@pytest.mark.parametrize("template_id", reg.TEMPLATE_IDS)
def test_every_template_returns_identifiers_not_text(template_id):
    """Neo4j is not a text store: no template returns chunk or document body."""
    cypher = reg.TEMPLATES[template_id].cypher
    for forbidden in (".text", ".content", ".body", ".chunk_text"):
        assert forbidden not in cypher


@pytest.mark.parametrize("template_id", reg.TEMPLATE_IDS)
def test_every_template_can_cite_its_evidence(template_id):
    """An answer nobody can trace is worse than no answer.

    Every template returns `document_id` and `chunk_id`, so a row can always be
    hydrated back to source text — including the current-state templates, which
    reach it through the claim behind the edge.
    """
    cypher = reg.TEMPLATES[template_id].cypher
    assert "AS document_id" in cypher
    assert "AS chunk_id" in cypher


def test_current_templates_read_only_current_edges():
    """A current-state answer comes from `{current: true}` edges — which the
    projection withholds from disputed and expired claims."""
    for template in reg.TEMPLATES.values():
        if template.is_current:
            assert "{current: true}" in template.cypher


def test_historical_templates_expose_status():
    """Superseded and disputed claims stay reachable, and stay labelled: a
    historical row carries `status` so a caller can say "this is disputed"."""
    for template in reg.TEMPLATES.values():
        if not template.is_current:
            assert "AS status" in template.cypher or "claim_id" in template.cypher
    # The templates that answer "what was true" must never filter status out.
    for template_id in ("project_history", "person_history", "org_funding_history"):
        cypher = reg.TEMPLATES[template_id].cypher
        assert "AS status" in cypher
        assert "status = 'active'" not in cypher
        assert "status <> " not in cypher


# --------------------------------------------------------------------------- #
# Arbitrary Cypher, and injection-shaped input
# --------------------------------------------------------------------------- #


def test_raw_cypher_as_a_template_id_is_rejected():
    """The registry is the only way in. A query passed where a template id
    belongs is an unknown id, not a query."""
    session = _FakeSession([{"n": 1}])
    result = traverse.run_template(
        "MATCH (n) DETACH DELETE n", {"entity_id": ORG}, session=session
    )
    assert result.error and "no such query template" in result.error
    assert session.statements == [], "nothing reached the session"


@pytest.mark.parametrize(
    "template_id",
    ["", "unknown", "MATCH (n) RETURN n", "projects_funded_by_org; DROP", None, 42],
)
def test_unknown_template_ids_are_refused(template_id):
    session = _FakeSession([{"n": 1}])
    result = traverse.run_template(template_id, {"entity_id": ORG}, session=session)
    assert result.error is not None
    assert session.statements == []


@pytest.mark.parametrize(
    "entity_id",
    [
        "org_1') DETACH DELETE (n",
        "org_aeeeb2a91bdd' OR '1'='1",
        "Person) DETACH DELETE (n",
        "org_AEEEB2A91BDD",          # wrong case: ids are lowercase hex
        "org_aeeeb2a91bd",           # one digit short
        "taxonomy_aeeeb2a91bdd",     # not an allowed entity kind
        "",
        None,
        123,
        {"$ne": None},
    ],
)
def test_injection_shaped_entity_ids_never_reach_the_driver(entity_id):
    session = _FakeSession([{"project_id": PROJECT}])
    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": entity_id}, session=session
    )
    assert result.error is not None
    assert result.rows == []
    assert session.statements == [], "a malformed id must fail before the driver"


@pytest.mark.parametrize(
    "predicate", ["FUNDED_BY'] AS x MATCH (n) DETACH DELETE n //", "OWNS", "", "*"]
)
def test_predicates_outside_the_closed_vocabulary_are_refused(predicate):
    """A predicate travels as a value, never as a relationship type — and is
    still checked against the vocabulary so it cannot be used to probe."""
    session = _FakeSession([])
    result = traverse.run_template(
        "claims_as_of",
        {"entity_id": PROJECT, "predicate": predicate, "as_of": "2020-01-01"},
        session=session,
    )
    assert result.error is not None
    assert session.statements == []


@pytest.mark.parametrize(
    "as_of", ["2020-13-01' RETURN 1 //", "yesterday", "2020/01/01", "", "20200101"]
)
def test_malformed_as_of_dates_are_refused(as_of):
    session = _FakeSession([])
    result = traverse.run_template(
        "claims_as_of",
        {"entity_id": PROJECT, "predicate": "LED_BY", "as_of": as_of},
        session=session,
    )
    assert result.error is not None
    assert session.statements == []


def test_labels_and_relationship_types_are_literals_in_the_template_text():
    """Cypher cannot parameterize a label or a relationship type, so the only
    safe place for one is reviewed template text. No template builds either."""
    from app.knowledge.graph import schema

    from app.knowledge.claims import predicates as vocab

    labels = set(schema.ENTITY_LABELS) | {
        "Entity", "Claim", "Chunk", "Document", "Alias", "Predicate",
    }
    relationships = (
        set(schema.PROVENANCE_RELATIONSHIPS)
        | set(vocab.PREDICATES)
        | {"CONTRADICTS", "SUPERSEDES"}
    )
    allowed = labels | relationships
    for template in reg.TEMPLATES.values():
        # `:Name` is a label or a relationship type — the only two things Cypher
        # cannot parameterize, so every one must already be on an allow-list.
        # `:X|Y` is an alternation of relationship types.
        for token in re.findall(r":([A-Za-z][A-Za-z_|]*)", template.cypher):
            for part in token.split("|"):
                assert part in allowed, (
                    f"{template.template_id}: unexpected label/type {part!r}"
                )


# --------------------------------------------------------------------------- #
# Limits
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "requested,expected",
    [(None, reg.DEFAULT_LIMIT), (10, 10), (0, 1), (-5, 1),
     (10_000, reg.MAX_LIMIT), (reg.MAX_LIMIT + 1, reg.MAX_LIMIT)],
)
def test_the_row_limit_is_clamped(requested, expected):
    session = _FakeSession([])
    traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG},
        limit=requested, session=session,
    )
    assert session.parameters[0]["limit"] == expected


def test_hitting_the_limit_is_reported_as_truncated():
    rows = [{"project_id": f"project_{i:012x}"} for i in range(5)]
    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG}, limit=5,
        session=_FakeSession(rows),
    )
    assert result.truncated is True

    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG}, limit=50,
        session=_FakeSession(rows),
    )
    assert result.truncated is False


# --------------------------------------------------------------------------- #
# Traversal results
# --------------------------------------------------------------------------- #


def test_a_current_state_query_collects_ids_from_its_rows():
    rows = [
        {"project_id": PROJECT, "funder_id": ORG, "claim_id": "claim_a",
         "chunk_id": "chunk-1", "document_id": "doc-1"},
    ]
    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG}, session=_FakeSession(rows)
    )
    assert result.error is None
    assert result.mode == reg.MODE_CURRENT
    assert result.claim_ids == ["claim_a"]
    assert result.chunk_ids == ["chunk-1"]
    assert result.document_ids == ["doc-1"]
    assert set(result.entity_ids) == {PROJECT, ORG}


def test_a_multi_hop_query_returns_both_ends_and_both_claims():
    """The four-hop question — org funds project, project led by person — comes
    back with the entities at both ends and the claim behind each edge."""
    rows = [
        {"person_id": PERSON, "person_name": "Dr A", "project_id": PROJECT,
         "project_name": "P", "funder_name": "DBT", "claim_id": "claim_led",
         "funding_claim_id": "claim_funded", "chunk_id": None,
         "document_id": "doc-1"},
    ]
    result = traverse.run_template(
        "people_leading_projects_funded_by_org", {"entity_id": ORG},
        session=_FakeSession(rows),
    )
    assert set(result.entity_ids) == {PERSON, PROJECT}
    # Both hops are cited, not just the last one.
    assert result.claim_ids == ["claim_led", "claim_funded"]
    assert reg.TEMPLATES["people_leading_projects_funded_by_org"].max_hops == 2


def test_multiple_rows_deduplicate_ids_but_keep_order():
    rows = [
        {"project_id": "project_00000000000a", "claim_id": "claim_1",
         "document_id": "doc-1"},
        {"project_id": "project_00000000000b", "claim_id": "claim_2",
         "document_id": "doc-1"},
        {"project_id": "project_00000000000a", "claim_id": "claim_3",
         "document_id": "doc-2"},
    ]
    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG}, session=_FakeSession(rows)
    )
    assert len(result.rows) == 3
    assert result.entity_ids == ["project_00000000000a", "project_00000000000b"]
    assert result.document_ids == ["doc-1", "doc-2"]
    assert result.claim_ids == ["claim_1", "claim_2", "claim_3"]


def test_a_query_with_no_matches_is_empty_and_not_an_error():
    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG}, session=_FakeSession([])
    )
    assert result.empty is True
    assert result.error is None
    assert result.rows == []


def test_a_disputed_historical_row_is_flagged():
    rows = [
        {"claim_id": "claim_1", "status": "active", "document_id": "doc-1"},
        {"claim_id": "claim_2", "status": "disputed", "document_id": "doc-2"},
    ]
    result = traverse.run_template(
        "project_history", {"entity_id": PROJECT}, session=_FakeSession(rows)
    )
    assert result.has_disputed is True, "a contradicted claim must be visible"


def test_a_superseded_claim_is_returned_by_a_historical_query():
    """Supersession is history, not deletion — "who led this in 2019" needs it."""
    rows = [
        {"claim_id": "claim_old", "status": "superseded",
         "valid_from": "2018-01-01", "valid_until": "2020-01-01",
         "object_name": "Dr A", "document_id": "doc-1"},
        {"claim_id": "claim_new", "status": "active",
         "valid_from": "2020-01-01", "valid_until": None,
         "object_name": "Dr B", "document_id": "doc-2"},
    ]
    result = traverse.run_template(
        "project_history", {"entity_id": PROJECT}, session=_FakeSession(rows)
    )
    assert {r["status"] for r in result.rows} == {"superseded", "active"}
    assert result.has_disputed is False


def test_a_current_state_row_carries_the_claim_that_backs_it():
    """Current-edge provenance: every current template returns `claim_id`, so a
    present-tense assertion can be traced to the claim that produced it."""
    for template in reg.TEMPLATES.values():
        if template.is_current:
            assert "AS claim_id" in template.cypher


def test_explain_claim_reaches_evidence_and_contradictions():
    rows = [{
        "claim_id": "claim_a", "predicate": "LED_BY", "status": "active",
        "quote": None, "evidence_kind": "cms_field",
        "source_field": "field_ongoing_pi_name", "subject_id": PROJECT,
        "object_id": PERSON, "chunk_id": None, "document_id": "doc-1",
        "contradicted_by": [],
    }]
    result = traverse.run_template(
        "explain_claim", {"claim_id": "claim_a"}, session=_FakeSession(rows)
    )
    assert result.error is None
    assert result.rows[0]["evidence_kind"] == "cms_field"
    assert result.document_ids == ["doc-1"]


# --------------------------------------------------------------------------- #
# Temporal boundaries
# --------------------------------------------------------------------------- #


def test_the_as_of_window_is_half_open():
    """`[valid_from, valid_until)`. A claim that ends on the queried date is
    already over — the alternative double-counts the handover day."""
    cypher = reg.TEMPLATES["claims_as_of"].cypher
    assert "c.valid_from  <= $as_of" in cypher
    assert "c.valid_until >  $as_of" in cypher
    # An open-ended claim is still current, so NULL must not exclude a row.
    assert "c.valid_from  IS NULL" in cypher
    assert "c.valid_until IS NULL" in cypher


@pytest.mark.parametrize("as_of", ["2019-01-01", "2020-12-31", "1999-06-15"])
def test_valid_as_of_dates_pass_validation(as_of):
    checked = reg.validate_parameters(
        reg.TEMPLATES["claims_as_of"],
        {"entity_id": PROJECT, "predicate": "LED_BY", "as_of": as_of},
    )
    assert checked["as_of"] == as_of


def test_a_missing_required_parameter_is_refused():
    session = _FakeSession([])
    result = traverse.run_template(
        "claims_as_of", {"entity_id": PROJECT}, session=session
    )
    assert result.error and "missing" in result.error
    assert session.statements == []


# --------------------------------------------------------------------------- #
# Failure is a value
# --------------------------------------------------------------------------- #


def test_a_neo4j_failure_degrades_instead_of_raising():
    """The graph is an enrichment. An outage costs the graph leg, not the turn."""
    result = traverse.run_template(
        "projects_funded_by_org", {"entity_id": ORG},
        session=_FakeSession(raises=RuntimeError("ServiceUnavailable")),
    )
    assert result.error is not None
    assert result.rows == []
    assert result.empty is True


def test_the_pipeline_returns_no_blocks_when_the_graph_is_down(monkeypatch):
    monkeypatch.setattr(
        router, "route",
        lambda q, **kw: router.RoutingOutcome(
            route=router.Route(
                template_id="projects_funded_by_org",
                parameters={"entity_id": ORG}, entity_id=ORG,
                entity_type="ORGANIZATION", entity_name="DBT",
                mode=reg.MODE_CURRENT, reason="test",
            ),
            reason="test",
        ),
    )
    monkeypatch.setattr(
        traverse, "run_template",
        lambda *a, **kw: traverse.GraphResult(
            "projects_funded_by_org", reg.MODE_CURRENT,
            error="ServiceUnavailable",
        ),
    )
    answer = pipeline.answer("What projects are funded by DBT?")
    assert answer.answered is False
    assert answer.blocks == []
    assert "graph query failed" in answer.reason


# --------------------------------------------------------------------------- #
# Hydration: identifiers -> source text, from Qdrant
# --------------------------------------------------------------------------- #


def test_chunks_are_fetched_by_exact_id_in_batches(monkeypatch):
    ids = [f"chunk-{i}" for i in range(hydration.BATCH_SIZE * 2 + 7)]
    client = _FakeQdrant(known=ids)
    _use_qdrant(monkeypatch, client)

    out = hydration.hydrate_chunks(ids)
    assert len(out) == len(ids)
    assert len(client.retrieve_calls) == 3, "batched, not one call per chunk"
    assert all(len(c) <= hydration.BATCH_SIZE for c in client.retrieve_calls)
    # Batches partition the input: nothing fetched twice, nothing dropped.
    assert [i for call in client.retrieve_calls for i in call] == ids


def test_duplicate_chunk_ids_are_fetched_and_returned_once(monkeypatch):
    client = _FakeQdrant(known={"chunk-a", "chunk-b"})
    _use_qdrant(monkeypatch, client)

    out = hydration.hydrate_chunks(
        ["chunk-a", "chunk-b", "chunk-a", "chunk-a", "chunk-b"]
    )
    assert [c.id for c in out] == ["chunk-a", "chunk-b"]
    assert client.retrieve_calls == [["chunk-a", "chunk-b"]]


def test_a_chunk_the_graph_cites_but_qdrant_lacks_is_dropped(monkeypatch):
    """A stale citation is dropped, never invented. Re-indexing changes chunk
    ids, so the graph outliving a chunk is expected rather than exceptional."""
    client = _FakeQdrant(known={"chunk-a", "chunk-c"})
    _use_qdrant(monkeypatch, client)

    out = hydration.hydrate_chunks(["chunk-a", "chunk-missing", "chunk-c"])
    assert [c.id for c in out] == ["chunk-a", "chunk-c"]


def test_hydration_survives_a_qdrant_failure(monkeypatch):
    _use_qdrant(monkeypatch, _FakeQdrant(known={"chunk-a"}, raises=True))
    assert hydration.hydrate_chunks(["chunk-a"]) == []


def test_no_ids_means_no_qdrant_call(monkeypatch):
    client = _FakeQdrant()
    _use_qdrant(monkeypatch, client)
    assert hydration.hydrate_chunks([]) == []
    assert hydration.hydrate_chunks([None, ""]) == []
    assert hydration.hydrate_documents([]) == []
    assert client.retrieve_calls == [] and client.scroll_calls == []


def _by_document(candidates):
    counts: dict[str, int] = {}
    for candidate in candidates:
        doc = candidate.payload["document_id"]
        counts[doc] = counts.get(doc, 0) + 1
    return counts


def test_document_evidence_is_capped_per_document(monkeypatch):
    """Document-level evidence is a few chunks, not a whole document: every
    claim today is a CMS field, and a metadata fact has no span to point at."""
    points = [_Record(f"c{i}", {"document_id": "doc-1"}) for i in range(10)]
    points += [_Record(f"d{i}", {"document_id": "doc-2"}) for i in range(10)]
    _use_qdrant(monkeypatch, _FakeQdrant(scroll_points=points))

    out = hydration.hydrate_documents(["doc-1", "doc-2"], per_document=2)
    assert _by_document(out) == {"doc-1": 2, "doc-2": 2}


def test_a_long_document_cannot_starve_the_others(monkeypatch):
    """`scroll` has no fairness: it returns what it reaches first. Without the
    per-document top-up, one chunk-heavy document spends the whole budget and
    the remaining cited documents contribute no evidence at all."""
    points = [_Record(f"big{i}", {"document_id": "doc-big"}) for i in range(50)]
    points += [_Record("s1", {"document_id": "doc-small"})]
    points += [_Record("s2", {"document_id": "doc-other"})]
    client = _FakeQdrant(scroll_points=points)
    _use_qdrant(monkeypatch, client)

    out = hydration.hydrate_documents(
        ["doc-big", "doc-small", "doc-other"], per_document=2
    )
    counts = _by_document(out)
    assert counts["doc-big"] == 2, "the long document is still capped"
    assert counts.get("doc-small") == 1, "a starved document is fetched directly"
    assert counts.get("doc-other") == 1


def test_documents_already_covered_are_not_fetched_again(monkeypatch):
    """The fairness pass is a repair, not a second hydration: when the broad
    scroll covers everything it costs exactly one round trip."""
    points = [_Record(f"c{i}", {"document_id": f"doc-{i}"}) for i in range(3)]
    client = _FakeQdrant(scroll_points=points)
    _use_qdrant(monkeypatch, client)

    hydration.hydrate_documents(["doc-0", "doc-1", "doc-2"], per_document=2)
    assert len(client.scroll_calls) == 1


def test_the_number_of_hydrated_documents_is_bounded(monkeypatch):
    """A graph result may cite up to MAX_LIMIT documents; hydrating each one
    would be a round trip spent on candidates the context builder discards."""
    ids = [f"doc-{i}" for i in range(reg.MAX_LIMIT)]
    points = [_Record(f"c{i}", {"document_id": d}) for i, d in enumerate(ids)]
    client = _FakeQdrant(scroll_points=points)
    _use_qdrant(monkeypatch, client)

    out = hydration.hydrate_documents(ids, per_document=1)
    assert len(_by_document(out)) == hydration.MAX_DOCUMENTS


def test_document_hydration_keeps_the_mandatory_shape_filter(monkeypatch):
    """It reuses `build_filter`, so a graph answer cannot surface a parent chunk
    or a superseded version that ordinary retrieval would exclude."""
    client = _FakeQdrant(scroll_points=[])
    _use_qdrant(monkeypatch, client)
    hydration.hydrate_documents(["doc-1"])

    scroll_filter, _ = client.scroll_calls[0]
    keys = {c.key for c in scroll_filter.must}
    assert {"is_parent", "is_current", "document_id"} <= keys


def test_hydrate_prefers_chunks_and_falls_back_to_documents(monkeypatch):
    """Chunk evidence is exact; document evidence is the fallback for claims
    that have no span. A document already covered by a chunk is not re-fetched."""
    client = _FakeQdrant(
        known={"chunk-a"},
        scroll_points=[_Record("c9", {"document_id": "doc-2"})],
    )
    _use_qdrant(monkeypatch, client)

    result = traverse.GraphResult("project_history", reg.MODE_HISTORICAL)
    result.chunk_ids = ["chunk-a"]
    result.document_ids = ["doc-of-chunk-a", "doc-2"]

    out = hydration.hydrate(result)
    assert [c.id for c in out] == ["chunk-a", "c9"]
    # doc-of-chunk-a was already covered by the chunk fetch.
    scroll_filter, _ = client.scroll_calls[0]
    document_condition = next(
        c for c in scroll_filter.must if c.key == "document_id"
    )
    assert document_condition.match.any == ["doc-2"]


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #


class _Decision:
    def __init__(self, entity_id, entity_type, surface_text, score=0.9):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.surface_text = surface_text
        self.score = score
        self.canonical = True
        self.decision = "AUTO"


def _routes_as(monkeypatch, resolved, ambiguous=(), spans=(), resolved_spans=None):
    """Stub resolution. `spans` is every mention (what masking blanks);
    `resolved_spans` is index-aligned with `resolved` and says where each anchor
    sits, which is what the two-hop chain is ordered by.

    Defaulting each anchor to offset 0 makes `_nearest_first` order the
    predicates by cue offset ascending — the question's own word order, which is
    what these tests asserted before the anchor position was available."""
    anchored = (
        list(resolved_spans) if resolved_spans is not None
        else [(0, 0)] * len(resolved)
    )
    monkeypatch.setattr(
        router, "_resolve_entities",
        lambda q, index: (resolved, list(ambiguous), list(spans), anchored),
    )


@pytest.mark.parametrize(
    "question,predicate,template_id",
    [
        # Two relationships named, so the chain between them is the question.
        ("Who leads projects funded by the Department of Biotechnology?",
         "FUNDED_BY", "relationship_two_hop"),
        ("What projects are funded by DBT?",
         "FUNDED_BY", "relationship_by_object"),
        ("Which programmes has DBT sponsored?",
         "FUNDED_BY", "relationship_by_object"),
        # A predicate that had no route at all before: no template named it, so
        # the claims the graph held for it were unreachable from any question.
        ("Who has DBT partnered with?", "PARTNER_OF", "relationship_by_object"),
    ],
)
def test_relational_questions_route_to_a_template(
    monkeypatch, question, predicate, template_id
):
    """Routing is by predicate now, not by memorised question shape.

    The template ids changed with the architecture: a question that names no
    period is answered from Claim nodes rather than from current-state edges,
    because the edges deliberately hold only what is true *now* and the question
    did not ask about now. What the caller gets is unchanged in kind — the same
    rows, the same claim ids, the same evidence — and each row now carries the
    validity window that says which it is.
    """
    _routes_as(monkeypatch, [_Decision(ORG, "ORGANIZATION", "DBT")])
    outcome = router.route(question)
    assert outcome.routed
    assert outcome.route.template_id == template_id
    assert outcome.route.parameters["entity_id"] == ORG
    assert outcome.route.parameters["predicate"] == predicate


def test_a_historical_question_routes_to_a_historical_template(monkeypatch):
    _routes_as(monkeypatch, [_Decision(ORG, "ORGANIZATION", "DBT")])
    outcome = router.route("What projects did DBT fund previously?")
    assert outcome.routed
    assert outcome.route.mode == reg.MODE_HISTORICAL
    assert outcome.route.is_historical


def test_an_explicitly_current_question_routes_to_a_current_template(monkeypatch):
    """Only an explicit statement of currency asks for current state.

    This test used to accept the present tense — "what projects *are* funded by
    DBT" — as meaning "now", and route to a current-state template. That reading
    is what made the graph useless on this corpus: every claim in it has an end
    date in the past, so the most natural phrasing of a funding question was
    answered "nothing is known" by a graph that holds 839 funding relationships.

    The present tense is now read as unspecified (see the test below). A
    question that actually says "currently" still gets current state, and still
    gets it from the cheap derived edges.
    """
    _routes_as(monkeypatch, [_Decision(ORG, "ORGANIZATION", "DBT")])
    outcome = router.route("What projects are currently funded by DBT?")
    assert outcome.route.mode == reg.MODE_CURRENT
    assert outcome.route.template_id == "projects_funded_by_org"


def test_an_unspecified_question_filters_by_no_window_at_all(monkeypatch):
    """The safest reading of a question that states no period.

    Neither "now" (which would hide every ended relationship, i.e. all of them)
    nor "the past" (which would hide an ongoing one). No temporal filter is
    applied, results come back newest-first, and every row carries its own
    validity window so the answer can say which relationships have ended.
    """
    _routes_as(monkeypatch, [_Decision(ORG, "ORGANIZATION", "DBT")])
    outcome = router.route("Which projects has DBT funded?")
    assert outcome.route.parameters["window_start"] is None
    assert outcome.route.parameters["window_end"] is None
    assert outcome.route.parameters["current_only"] is False


def test_a_question_naming_nobody_does_not_route(monkeypatch):
    _routes_as(monkeypatch, [])
    outcome = router.route("Who funds climate research?")
    assert not outcome.routed
    assert "no entity" in outcome.reason


def test_an_ambiguous_entity_does_not_route(monkeypatch):
    """The resolver is the same one ingestion uses, so a surface too ambiguous
    to link there is equally unusable here — and a guess is worse than a miss."""
    _routes_as(monkeypatch, [], ambiguous=["TERI"])
    outcome = router.route("What projects are funded by TERI?")
    assert not outcome.routed
    assert outcome.ambiguous == ["TERI"]
    assert "ambiguous" in outcome.reason


def test_a_topical_question_about_a_known_entity_does_not_route(monkeypatch):
    """Naming an entity is not enough. "Tell me about X" is a retrieval
    question, and answering it from the graph would lose the corpus."""
    _routes_as(monkeypatch, [_Decision(ORG, "ORGANIZATION", "DBT")])
    outcome = router.route("Tell me about the Department of Biotechnology")
    assert not outcome.routed
    assert "not relational" in outcome.reason


@pytest.mark.parametrize("question", ["", "   ", "\n"])
def test_an_empty_question_does_not_route(question):
    assert not router.route(question).routed


def test_the_entity_type_selects_the_direction(monkeypatch):
    """The same question shape means different things for a project and an org.

    It always did; what has changed is that the direction is now *derived* from
    the predicate's declared domain and range rather than looked up in a table
    of question shapes. `FUNDED_BY` runs PROJECT -> ORGANIZATION, so a project
    anchors the subject end and an organization the object end, and one pair of
    templates serves both readings.
    """
    _routes_as(monkeypatch, [_Decision(PROJECT, "PROJECT", "Some Project")])
    outcome = router.route("Who funded Some Project?")
    assert outcome.route.template_id == "relationship_by_subject"
    assert outcome.route.parameters["predicate"] == "FUNDED_BY"

    _routes_as(monkeypatch, [_Decision(ORG, "ORGANIZATION", "DBT")])
    outcome = router.route("What has DBT funded?")
    assert outcome.route.template_id == "relationship_by_object"
    assert outcome.route.parameters["predicate"] == "FUNDED_BY"


def test_an_entity_type_the_predicate_forbids_does_not_route(monkeypatch):
    """The claim type system governs questions as well as assertions.

    `FUNDED_BY` joins PROJECT to ORGANIZATION and nothing else, so there is no
    direction in which a person could anchor it. Declining is right: such a
    query could only ever return nothing, and existing retrieval may well find
    the answer in prose.
    """
    _routes_as(monkeypatch, [_Decision(PERSON, "PERSON", "A Person")])
    outcome = router.route("Who funded A Person?")
    assert not outcome.routed


def test_every_routable_template_id_exists_in_the_registry():
    """Routing cannot name a template the registry does not have."""
    for _, by_type, _ in router._PATTERNS:
        for template_id in by_type.values():
            assert template_id in reg.TEMPLATES
    for source, target in router._HISTORICAL_EQUIVALENT.items():
        assert source in reg.TEMPLATES and target in reg.TEMPLATES
        assert reg.TEMPLATES[target].mode == reg.MODE_HISTORICAL


# --------------------------------------------------------------------------- #
# Isolation from the default retrieval path
# --------------------------------------------------------------------------- #


def test_graph_retrieval_is_disabled_by_default():
    """Both flags ship off.

    Read from the field defaults rather than a loaded ``Settings()``: the
    latter reflects the local ``.env``, which is gitignored and therefore never
    the thing being guarded. See the same argument in
    tests/test_graph_schema.py::test_knowledge_flags_default_off.
    """
    from app.config import Settings

    assert Settings.model_fields["graph_retrieval_enabled"].default is False
    assert Settings.model_fields["knowledge_enabled"].default is False


def _repo_root():
    """The repository root, found by walking up to the directory holding ``app``.

    Deliberately not a hard-coded ``parents[n]``: this file has already moved
    once (into ``tests/retrieval/graph/``), and the depth-counting version kept
    resolving to ``tests/retrieval``. One of the two tests below then failed for
    a reason unrelated to what it asserts, and the other passed *vacuously* by
    globbing a directory that did not exist. Searching for the marker cannot
    break that way.
    """
    import pathlib

    here = pathlib.Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "app").is_dir() and (candidate / "tests").is_dir():
            return candidate
    raise AssertionError(f"could not locate the repository root from {here}")


def test_importing_production_retrieval_does_not_load_the_graph_package():
    """The flag is a policy; this is the structural guarantee behind it.

    Shadow mode gives `retriever.py` one reference to the graph, so "no module
    mentions it" is no longer the property to check. The property that matters
    is stronger and tested directly: importing production retrieval must not
    *load* the graph package. Every reference to it is inside a function, behind
    a flag that is off, so with shadow disabled the code is never reached.

    A subprocess, so the result cannot depend on what the rest of the suite has
    already imported. Three things are pinned explicitly, because this test
    failed once in a full run and never in isolation and none of them should be
    inherited from whatever ran before it:

    * ``cwd`` - the repo root, so ``app`` is importable regardless of the
      ambient directory;
    * the graph flags - forced off in the child environment, so a stray export
      or a local ``.env`` cannot flip the behaviour being asserted;
    * both streams are reported on failure, so a recurrence is diagnosable
      rather than another unreproducible line in a log.
    """
    import os
    import pathlib
    import subprocess
    import sys

    program = (
        "import sys;"
        "import app.retrieval.retriever, app.retrieval.search.hybrid_search,"
        " app.retrieval.context.builder;"
        "leaked=[m for m in sys.modules if m.startswith('app.retrieval.graph')];"
        "print(','.join(leaked))"
    )
    repo_root = _repo_root()
    env = {
        **os.environ,
        "GRAPH_RETRIEVAL_ENABLED": "false",
        "GRAPH_ROUTING_ENABLED": "false",
        "KNOWLEDGE_ENABLED": "false",
        # Keeps the child from re-resolving imports through a stale cache.
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    try:
        completed = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True, text=True, timeout=300,
            cwd=str(repo_root), env=env,
        )
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - load-dependent
        raise AssertionError(
            "importing production retrieval did not finish within 300s; the "
            f"import itself normally takes ~11s. stdout={exc.stdout!r}"
        ) from exc
    assert completed.returncode == 0, (
        f"child exited {completed.returncode}\n"
        f"stdout: {completed.stdout[-1000:]}\nstderr: {completed.stderr[-2000:]}"
    )
    leaked = completed.stdout.strip()
    assert leaked == "", (
        f"graph package loaded by production retrieval: {leaked}\n"
        f"stderr: {completed.stderr[-1000:]}"
    )


def test_only_the_shadow_hook_references_the_graph_from_production_retrieval():
    """One doorway, and it is the observing one."""
    root = _repo_root()
    # The glob below silently passes if `root` is wrong — an empty iteration
    # yields no offenders. This test spent a while doing exactly that after the
    # test tree grew a `graph/` level and the hard-coded depth stopped matching.
    assert (root / "app" / "retrieval").is_dir(), f"bad repo root: {root}"
    offenders = []
    for path in list((root / "app" / "retrieval").rglob("*.py")) + list(
        (root / "app" / "pipeline").rglob("*.py")
    ):
        if "graph" in path.parts:
            continue
        if "app.retrieval.graph" not in path.read_text(encoding="utf-8"):
            continue
        if path.name != "retriever.py":
            offenders.append(str(path.relative_to(root)))
    assert offenders == [], f"graph retrieval leaked into: {offenders}"


# --------------------------------------------------------------------------- #
# Live smoke test — skipped without a running Neo4j
# --------------------------------------------------------------------------- #


def _graph_reachable() -> bool:
    try:
        from app.core.clients.graph import graph_available

        return graph_available()
    except Exception:
        return False


@pytest.mark.skipif(not _graph_reachable(), reason="no Neo4j reachable")
def test_live_graph_smoke():
    """Against a real graph: every template runs, stays bounded, and returns
    only identifiers. Catches Cypher that is valid text but invalid to the
    server — a syntax error, a renamed property — which fakes cannot."""
    from app.core.clients.graph import read_session

    with read_session() as session:
        for template_id in reg.TEMPLATE_IDS:
            template = reg.TEMPLATES[template_id]
            params = {"entity_id": ORG, "claim_id": "claim_none",
                      "predicate": "LED_BY", "predicate2": "FUNDED_BY",
                      "as_of": "2020-01-01", "current_only": False,
                      "window_start": None, "window_end": None}
            result = traverse.run_template(
                template_id,
                {k: params[k] for k in template.all_parameters},
                limit=5, session=session,
            )
            assert result.error is None, f"{template_id}: {result.error}"
            assert len(result.rows) <= 5
            for row in result.rows:
                for key, value in row.items():
                    if isinstance(value, str) and key.endswith("_name"):
                        continue
                    if isinstance(value, str) and len(value) > 500:
                        pytest.fail(f"{template_id}.{key} looks like source text")
