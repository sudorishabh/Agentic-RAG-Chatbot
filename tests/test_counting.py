"""Unit tests for the structured (database-intent) answer path and its inputs.

Covers answer_structured's delegation to the Database Planner (analysis vs the
parse fallback, bundle normalization, format passthrough, fall-through), the
query_processor facet filters (semantic-path DatetimeRange / author / tags), the
generation format directives, and the ProcessedQuery contract. The catalog tools
themselves are covered by test_database_tools; the SQL by app/local_tests. No
MySQL, Qdrant, LLM, or network.
"""

from __future__ import annotations

from datetime import datetime

from app.ingestion import state
from app.retrieval import drupal_router as dr
from app.retrieval import query_processor as qp


# --------------------------------------------------------------------------- #
# answer_structured — delegation, normalization, fall-through, format.
# --------------------------------------------------------------------------- #

def _forbid_count(**kw):
    raise AssertionError("count_documents must not be called")


def test_answer_structured_unknown_bundle_falls_through(monkeypatch):
    monkeypatch.setattr(state, "count_documents", _forbid_count)
    analysis = qp.QueryAnalysis(
        search_query="table of emissions by sector",
        intent="structured",
        operation="count",
        bundle="emission",  # normalizes to no known bundle
    )
    assert dr.answer_structured("emissions by sector?", analysis=analysis) is None


def test_answer_structured_normalizes_bundle_for_count(monkeypatch):
    monkeypatch.setattr(
        dr, "parse_structured",
        lambda q, h=None: dr.StructuredQuery(operation="count", bundle="event"),
    )
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 3)

    out = dr.answer_structured("how many events?")

    assert seen["bundle"] == "events"  # normalized before the catalog query
    assert out["answer"] == "There are 3 events matching your query."


def test_answer_structured_skips_parse_when_analysis_provided(monkeypatch):
    def no_parse(q, h=None):
        raise AssertionError("parse_structured must not be called")

    monkeypatch.setattr(dr, "parse_structured", no_parse)
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 5)

    analysis = qp.QueryAnalysis(
        search_query="how many events in 2024",
        intent="structured",
        operation="count",
        bundle="event",
        date_from="2024-01-01",
        date_to="2025-01-01",
    )
    out = dr.answer_structured("how many events in 2024?", analysis=analysis)

    assert seen["bundle"] == "events"  # normalized before the catalog query
    assert seen["published_from"] == datetime(2024, 1, 1)
    assert seen["published_to"] == datetime(2025, 1, 1)
    assert out["answer"] == "There are 5 events in 2024 matching your query."


def test_answer_structured_falls_back_to_parse_without_operation(monkeypatch):
    monkeypatch.setattr(
        dr, "parse_structured",
        lambda q, h=None: dr.StructuredQuery(operation="count", bundle="events"),
    )
    monkeypatch.setattr(state, "count_documents", lambda **kw: 4)

    analysis = qp.QueryAnalysis(search_query="x", intent="structured")  # no operation
    out = dr.answer_structured("how many events?", analysis=analysis)
    assert out["answer"] == "There are 4 events matching your query."


def test_answer_structured_passes_format_from_analysis(monkeypatch):
    monkeypatch.setattr(state, "distribution", lambda *a, **k: [("Climate", 2)])
    analysis = qp.QueryAnalysis(
        search_query="articles per theme as a table",
        intent="structured", operation="distribution", answer_format="table",
    )
    out = dr.answer_structured("articles per theme as a table", analysis=analysis)
    assert "| theme | count |" in out["answer"]


# --------------------------------------------------------------------------- #
# Semantic path — dates / author / tags become query_processor facet filters.
# --------------------------------------------------------------------------- #

def test_facet_filters_builds_datetime_range():
    analysis = qp.QueryAnalysis(search_query="x", date_from="2024-03-01", date_to="2024-04-01")
    conds = qp._facet_filters(analysis)
    pub = [c for c in conds if getattr(c, "key", None) == "published_at"]
    assert len(pub) == 1
    assert pub[0].range.gte == qp._parse_bound("2024-03-01")
    assert pub[0].range.lt == qp._parse_bound("2024-04-01")


def test_facet_filters_no_dates_no_condition():
    conds = qp._facet_filters(qp.QueryAnalysis(search_query="x"))
    assert not any(getattr(c, "key", None) == "published_at" for c in conds)


def test_facet_filters_author_and_tags_exact_match():
    analysis = qp.QueryAnalysis(
        search_query="x", author="Dr R K Sharma", tags=["biofuels", "solar"]
    )
    conds = qp._facet_filters(analysis)
    by_key = {getattr(c, "key", None): c for c in conds}
    # Exact display-name / tag values — MatchAny has no substring matching.
    assert by_key["authors"].match.any == ["Dr R K Sharma"]
    assert by_key["tags"].match.any == ["biofuels", "solar"]


def test_facet_filters_absent_author_tags_add_nothing():
    conds = qp._facet_filters(qp.QueryAnalysis(search_query="x"))
    keys = {getattr(c, "key", None) for c in conds}
    assert "authors" not in keys and "tags" not in keys


# --------------------------------------------------------------------------- #
# Generation format directives.
# --------------------------------------------------------------------------- #

def test_timeline_format_directive_exists():
    from app.generation.prompts import format_directive

    directive = format_directive("timeline")
    assert "chronological" in directive and "citation" in directive


def test_format_exemplars_attach_only_with_their_directive():
    from app.generation.prompts import format_directive

    assert "Example shape:" in format_directive("table")
    assert "Example shape:" in format_directive("timeline")
    # The default path must stay lean: no directive, no exemplar.
    assert format_directive("default") == ""
    assert format_directive(None) == ""
    assert "Example shape:" not in format_directive("list")


def test_grounded_prompt_carries_worked_example():
    from app.generation.prompts import GROUNDED_SYSTEM_PROMPT

    assert "Example:" in GROUNDED_SYSTEM_PROMPT
    assert GROUNDED_SYSTEM_PROMPT.rstrip().endswith("Answer concisely and factually.")


# --------------------------------------------------------------------------- #
# ProcessedQuery / analysis schema.
# --------------------------------------------------------------------------- #

def test_query_analysis_structured_slot_defaults():
    a = qp.QueryAnalysis(search_query="x")
    assert a.operation is None
    assert a.bundle is None
    assert a.group_by is None
    assert a.title_contains is None
    assert a.author is None
    assert a.tags == []
    assert a.limit == 10


def test_answer_format_accepts_timeline():
    a = qp.QueryAnalysis(search_query="x", answer_format="timeline")
    assert a.answer_format == "timeline"


def test_process_carries_analysis(monkeypatch):
    understanding = qp.QueryUnderstanding(
        query_rewrite="how many events in 2024",
        intents=[qp.IntentPrediction(label="database", confidence=0.9, rationale="")],
        operation="count",
        bundle="events",
    )

    class _FakeStructured:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            return understanding

    monkeypatch.setattr(qp, "get_structured_llm", lambda: _FakeStructured())
    pq = qp.process("how many events in 2024?")
    # 'database' derives the legacy structured route; slots reach pq.analysis and
    # the full multi-label result is exposed on pq.understanding.
    assert pq.intent == "structured"
    assert pq.analysis.operation == "count"
    assert pq.analysis.bundle == "events"
    assert pq.understanding.intents[0].label == "database"


def test_process_passthrough_has_no_analysis(monkeypatch):
    def boom():
        raise RuntimeError("llm down")

    monkeypatch.setattr(qp, "get_structured_llm", boom)
    pq = qp.process("hello")
    assert pq.analysis is None
    assert pq.intent == "qa"
