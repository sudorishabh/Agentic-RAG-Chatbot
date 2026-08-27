"""Shadow mode, the facts block, and the failure modes Phase 10 asked about.

The claim shadow mode makes is absolute — *the user's answer is what it would
have been with this module absent* — so most of these tests try to break that
claim rather than confirm it: a graph that raises, a graph that hangs, a graph
that returns nothing, a Qdrant that is down mid-hydration.

Disputed and superseded claims are exercised with fixtures. The corpus has
produced no conflict yet (all 1,653 claims are active), and inventing one to
make a benchmark row would make the numbers describe fiction — but the code that
handles them still has to be right before one appears.
"""
from __future__ import annotations

import json
import time

import pytest

from app.retrieval.graph import facts, pipeline, shadow, traverse
from app.retrieval.graph import templates as reg


ORG = "org_aeeeb2a91bdd"
PERSON = "person_1234567890ab"
PROJECT = "project_abcdef012345"


class _FakeSession:
    def __init__(self, rows=None, *, raises=None):
        self._rows = rows or []
        self._raises = raises

    def run(self, statement, **params):
        if self._raises is not None:
            raise self._raises
        return [dict(r) for r in self._rows]


def _result(template_id, mode, rows, *, truncated=False):
    out = traverse.GraphResult(template_id, mode, rows=list(rows))
    out.truncated = truncated
    traverse._collect(out)
    return out


class _Block:
    def __init__(self, document_id):
        self.payload = {"document_id": document_id}
        self.n = 1
        self.text = "text"


@pytest.fixture(autouse=True)
def _clean_shadow():
    shadow.reset()
    yield
    shadow.reset()


def _enable_shadow(monkeypatch, tmp_path=None, enabled=True):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "graph_shadow_enabled", enabled, raising=False)
    path = str(tmp_path / "shadow.jsonl") if tmp_path else None
    monkeypatch.setattr(settings, "graph_shadow_log_path", path, raising=False)
    return path


def _drain(timeout=10.0):
    """Wait for in-flight observations, since they run on a background thread."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if shadow.stats()["in_flight"] == 0:
            return True
        time.sleep(0.01)
    return False


# --------------------------------------------------------------------------- #
# Shadow mode cannot touch the answer
# --------------------------------------------------------------------------- #


def test_observe_returns_none_even_when_the_graph_answers(monkeypatch, tmp_path):
    """There is no value for a caller to misuse."""
    _enable_shadow(monkeypatch, tmp_path)
    monkeypatch.setattr(
        pipeline, "answer",
        lambda q, **kw: pipeline.GraphAnswer(blocks=[_Block("doc-1")], reason="ok"),
    )
    assert shadow.observe("who leads what?", [_Block("doc-2")]) is None
    assert _drain()


def test_observe_is_a_no_op_when_the_flag_is_off(monkeypatch):
    _enable_shadow(monkeypatch, enabled=False)
    called = []
    monkeypatch.setattr(
        pipeline, "answer", lambda q, **kw: called.append(q) or pipeline.GraphAnswer()
    )
    assert shadow.observe("anything", []) is None
    assert called == [], "the graph must not run with shadow disabled"


def test_a_raising_graph_never_propagates(monkeypatch, tmp_path):
    """An outage costs an observation, never a request that already succeeded."""
    _enable_shadow(monkeypatch, tmp_path)

    def _boom(question, **kwargs):
        raise RuntimeError("ServiceUnavailable")

    monkeypatch.setattr(pipeline, "answer", _boom)
    assert shadow.observe("who funds what?", [_Block("doc-1")]) is None
    assert _drain()
    assert shadow.stats()["in_flight"] == 0


def test_a_slow_graph_does_not_delay_the_caller(monkeypatch, tmp_path):
    """The observation is submitted, not awaited."""
    _enable_shadow(monkeypatch, tmp_path)
    monkeypatch.setattr(
        pipeline, "answer",
        lambda q, **kw: (time.sleep(1.5), pipeline.GraphAnswer())[1],
    )
    started = time.perf_counter()
    shadow.observe("slow question", [])
    elapsed = (time.perf_counter() - started) * 1000
    assert elapsed < 250, f"observe blocked for {elapsed:.0f}ms"


def test_observations_are_dropped_rather_than_queued_when_saturated(monkeypatch):
    """Saturation costs samples, not the process."""
    _enable_shadow(monkeypatch)
    release = __import__("threading").Event()
    monkeypatch.setattr(
        pipeline, "answer",
        lambda q, **kw: (release.wait(5), pipeline.GraphAnswer())[1],
    )
    try:
        for _ in range(shadow.MAX_IN_FLIGHT + 6):
            shadow.observe("q", [])
        assert shadow.stats()["in_flight"] <= shadow.MAX_IN_FLIGHT
        assert shadow.stats()["dropped"] >= 1
    finally:
        release.set()
        _drain()


def test_the_shadow_record_compares_both_retrievals(monkeypatch, tmp_path):
    """The point of a shadow: what did the graph find that production did not?"""
    path = _enable_shadow(monkeypatch, tmp_path)
    result = _result(
        "projects_funded_by_org", reg.MODE_CURRENT,
        [{"project_id": PROJECT, "claim_id": "claim_a", "document_id": "doc-1"},
         {"project_id": PROJECT, "claim_id": "claim_b", "document_id": "doc-新"}],
    )
    answer = pipeline.GraphAnswer(
        blocks=[_Block("doc-1")], result=result, hydrated=2, facts=True,
        reason="projects funded by an organization",
    )
    monkeypatch.setattr(pipeline, "answer", lambda q, **kw: answer)

    shadow.observe("What projects are funded by DBT?", [_Block("doc-1"),
                                                        _Block("doc-2")])
    assert _drain()

    record = json.loads(open(path, encoding="utf-8").read().strip())
    assert record["graph_documents"] == 2
    assert record["production_documents"] == 2
    assert record["document_overlap"] == 1
    assert record["novel_documents"] == 1
    assert record["facts_block"] is True


def test_the_production_hook_is_inert_with_the_flag_off(monkeypatch):
    """The hook production retrieval calls on every query."""
    from app.retrieval import retriever

    _enable_shadow(monkeypatch, enabled=False)
    called = []
    monkeypatch.setattr(shadow, "observe", lambda *a, **kw: called.append(a))
    retriever._observe_in_shadow("a question", [])
    assert called == []


def test_the_production_hook_swallows_a_failing_shadow(monkeypatch):
    from app.retrieval import retriever

    _enable_shadow(monkeypatch)

    def _boom(*args, **kwargs):
        raise RuntimeError("shadow exploded")

    monkeypatch.setattr(shadow, "observe", _boom)
    # Must not raise: production retrieval has already produced its blocks.
    assert retriever._observe_in_shadow("a question", []) is None


# --------------------------------------------------------------------------- #
# The facts block
# --------------------------------------------------------------------------- #


def test_facts_state_the_relationship_and_cite_the_claim():
    """The rows are the answer; hydrated passages are only the citation."""
    result = _result(
        "people_leading_projects_funded_by_org", reg.MODE_CURRENT,
        [{"person_name": "Dr A", "project_name": "P1", "funder_name": "DBT",
          "claim_id": "claim_a", "valid_from": "2019-03-11",
          "document_id": "doc-1"}],
    )
    text = facts.render(result)
    assert "Dr A" in text and "P1" in text and "DBT" in text
    assert "claim_a" in text, "a fact in the prompt must be traceable"
    assert "since 2019-03-11" in text


def test_a_disputed_fact_is_labelled_not_hidden():
    result = _result(
        "project_history", reg.MODE_HISTORICAL,
        [{"subject_name": "P1", "object_name": "Dr A", "predicate": "LED_BY",
          "status": "disputed", "claim_id": "claim_a", "document_id": "doc-1"}],
    )
    text = facts.render(result)
    assert "DISPUTED" in text
    assert "contradict" in text.lower()


def test_a_superseded_fact_is_labelled():
    result = _result(
        "project_history", reg.MODE_HISTORICAL,
        [{"subject_name": "P1", "object_name": "Dr A", "predicate": "LED_BY",
          "status": "superseded", "valid_from": "2018-01-01",
          "valid_until": "2020-01-01", "claim_id": "claim_old",
          "document_id": "doc-1"}],
    )
    text = facts.render(result)
    assert "SUPERSEDED" in text
    assert "2018-01-01 until 2020-01-01" in text


def test_an_ended_relationship_is_not_rendered_as_present_tense():
    result = _result(
        "org_funding_history", reg.MODE_HISTORICAL,
        [{"project_name": "P1", "funder_name": "DBT", "status": "active",
          "valid_from": "2015-01-01", "valid_until": "2018-06-30",
          "claim_id": "claim_a", "document_id": "doc-1"}],
    )
    text = facts.render(result)
    assert "2015-01-01 until 2018-06-30" in text


def test_the_facts_block_is_bounded():
    rows = [
        {"project_name": f"Project {i}", "funder_name": "DBT",
         "claim_id": f"claim_{i}", "document_id": f"doc-{i}"}
        for i in range(500)
    ]
    result = _result("projects_funded_by_org", reg.MODE_CURRENT, rows)
    text = facts.render(result)
    assert len(text) <= facts.MAX_CHARS + 500
    assert text.count("\n- ") <= facts.MAX_LINES
    assert "further records not shown" in text


def test_a_historical_block_may_be_longer_than_a_current_one():
    """A timeline truncated to a quarter of itself is a wrong answer."""
    rows = [
        {"project_name": f"Project {i}", "funder_name": "DBT",
         "claim_id": f"claim_{i}", "document_id": f"doc-{i}"}
        for i in range(facts.MAX_LINES_HISTORICAL)
    ]
    current = facts.render(_result("projects_funded_by_org", reg.MODE_CURRENT, rows))
    historical = facts.render(
        _result("org_funding_history", reg.MODE_HISTORICAL, rows)
    )
    assert historical.count("\n- ") > current.count("\n- ")


def test_no_rows_render_to_no_block():
    assert facts.render(_result("projects_funded_by_org", reg.MODE_CURRENT, [])) is None
    assert facts.as_block(None) is None


def test_the_facts_block_carries_its_provenance():
    result = _result(
        "projects_funded_by_org", reg.MODE_CURRENT,
        [{"project_name": "P1", "funder_name": "DBT", "claim_id": "claim_a",
          "project_id": PROJECT, "document_id": "doc-1"}],
    )
    block = facts.as_block(result)
    assert block.payload["kind"] == "graph_facts"
    assert block.payload["claim_ids"] == ["claim_a"]
    assert block.payload["document_ids"] == ["doc-1"]
    assert block.payload["template_id"] == "projects_funded_by_org"


# --------------------------------------------------------------------------- #
# Failure modes the pipeline must survive
# --------------------------------------------------------------------------- #


def _route_to(monkeypatch, template_id="projects_funded_by_org",
              mode=reg.MODE_CURRENT):
    from app.retrieval.graph import router as routing

    monkeypatch.setattr(
        routing, "route",
        lambda q, **kw: routing.RoutingOutcome(
            route=routing.Route(
                template_id=template_id, parameters={"entity_id": ORG},
                entity_id=ORG, entity_type="ORGANIZATION", entity_name="DBT",
                mode=mode, reason="test",
            ),
            reason="test",
        ),
    )


def test_neo4j_unavailable_yields_no_answer_and_no_exception(monkeypatch):
    _route_to(monkeypatch)
    monkeypatch.setattr(
        traverse, "run_template",
        lambda *a, **kw: traverse.GraphResult(
            "projects_funded_by_org", reg.MODE_CURRENT, error="ServiceUnavailable"
        ),
    )
    answer = pipeline.answer("What projects are funded by DBT?")
    assert answer.answered is False and answer.blocks == []
    assert "graph query failed" in answer.reason


def test_qdrant_unavailable_during_hydration_still_yields_the_facts(monkeypatch):
    """Hydration is the citation, not the answer. Losing Qdrant costs the
    supporting passages; the verified rows are still worth stating."""
    _route_to(monkeypatch)
    result = _result(
        "projects_funded_by_org", reg.MODE_CURRENT,
        [{"project_name": "P1", "funder_name": "DBT", "claim_id": "claim_a",
          "document_id": "doc-1"}],
    )
    monkeypatch.setattr(traverse, "run_template", lambda *a, **kw: result)

    from app.retrieval.graph import hydrate as hydration

    monkeypatch.setattr(hydration, "hydrate", lambda *a, **kw: [])
    answer = pipeline.answer("What projects are funded by DBT?")
    assert answer.answered is True
    assert answer.hydrated == 0
    assert answer.facts is True
    assert "P1" in answer.blocks[0].text


def test_a_graph_result_with_no_renderable_rows_and_no_evidence_declines(monkeypatch):
    _route_to(monkeypatch)
    result = _result(
        "projects_funded_by_org", reg.MODE_CURRENT, [{"unrelated": "value"}]
    )
    monkeypatch.setattr(traverse, "run_template", lambda *a, **kw: result)
    from app.retrieval.graph import hydrate as hydration

    monkeypatch.setattr(hydration, "hydrate", lambda *a, **kw: [])
    answer = pipeline.answer("What projects are funded by DBT?")
    assert answer.answered is False
    assert "could not be rendered" in answer.reason


def test_no_graph_result_declines(monkeypatch):
    _route_to(monkeypatch)
    monkeypatch.setattr(
        traverse, "run_template",
        lambda *a, **kw: _result("projects_funded_by_org", reg.MODE_CURRENT, []),
    )
    answer = pipeline.answer("What projects are funded by DBT?")
    assert answer.answered is False
    assert answer.reason == "graph query returned no rows"


def test_a_historical_question_gets_the_larger_row_budget(monkeypatch):
    """Measured: at the current-state default an organization with many records
    returns its recent rows and almost none of its ended ones."""
    _route_to(monkeypatch, "org_funding_history", reg.MODE_HISTORICAL)
    seen = {}

    def _capture(template_id, params, *, limit=None, **kwargs):
        seen["limit"] = limit
        return _result(template_id, reg.MODE_HISTORICAL, [])

    monkeypatch.setattr(traverse, "run_template", _capture)
    pipeline.answer("What has DBT funded in the past?")
    assert seen["limit"] == pipeline.HISTORICAL_LIMIT


def test_an_explicit_limit_is_not_overridden_for_history(monkeypatch):
    _route_to(monkeypatch, "org_funding_history", reg.MODE_HISTORICAL)
    seen = {}

    def _capture(template_id, params, *, limit=None, **kwargs):
        seen["limit"] = limit
        return _result(template_id, reg.MODE_HISTORICAL, [])

    monkeypatch.setattr(traverse, "run_template", _capture)
    pipeline.answer("What has DBT funded in the past?", limit=5)
    assert seen["limit"] == 5


# --------------------------------------------------------------------------- #
# Chunk evidence — tested, because the corpus cannot exercise it yet
# --------------------------------------------------------------------------- #


class _Record:
    def __init__(self, point_id, payload=None):
        self.id = point_id
        self.payload = payload or {"document_id": f"doc-of-{point_id}"}


def test_chunk_evidence_is_preferred_over_document_evidence(monkeypatch):
    """Every claim today is CMS-derived and cites a document. When text-derived
    claims arrive they will cite a chunk, and that span is the better evidence —
    so the chunk path is exercised here rather than waiting for the corpus."""
    from app.retrieval.graph import hydrate as hydration

    retrieved, scrolled = [], []

    class _Client:
        def retrieve(self, *, collection_name, ids, **kwargs):
            retrieved.extend(ids)
            return [_Record(i, {"document_id": "doc-1", "chunk_text": "span"})
                    for i in ids]

        def scroll(self, *, collection_name, scroll_filter, limit, **kwargs):
            scrolled.append(limit)
            return [], None

    monkeypatch.setattr("app.core.clients.get_qdrant_client", lambda: _Client())

    result = _result(
        "project_history", reg.MODE_HISTORICAL,
        [{"claim_id": "claim_a", "chunk_id": "chunk-1", "document_id": "doc-1",
          "subject_name": "P1", "object_name": "Dr A", "predicate": "LED_BY"}],
    )
    out = hydration.hydrate(result)
    assert retrieved == ["chunk-1"], "the cited span is fetched exactly"
    assert scrolled == [], "no document fallback when a chunk covers the claim"
    assert [c.id for c in out] == ["chunk-1"]


def test_a_claim_citing_both_a_chunk_and_a_document_uses_the_chunk(monkeypatch):
    from app.retrieval.graph import hydrate as hydration

    class _Client:
        def retrieve(self, *, collection_name, ids, **kwargs):
            return [_Record(i, {"document_id": "doc-1"}) for i in ids]

        def scroll(self, *, collection_name, scroll_filter, limit, **kwargs):
            raise AssertionError("document fallback must not run")

    monkeypatch.setattr("app.core.clients.get_qdrant_client", lambda: _Client())
    result = _result(
        "project_history", reg.MODE_HISTORICAL,
        [{"claim_id": "claim_a", "chunk_id": "chunk-1", "document_id": "doc-1"}],
    )
    assert [c.id for c in hydration.hydrate(result)] == ["chunk-1"]
