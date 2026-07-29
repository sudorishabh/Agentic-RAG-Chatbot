"""Unit tests for the structured (database-intent) answer path and its inputs.

Covers answer_structured's delegation to the Database Planner (analysis vs the
parse fallback, bundle normalization, format passthrough, fall-through), the
query_processor facet filters (semantic-path DatetimeRange / tags), the
generation format directives, and the ProcessedQuery contract. The catalog tools
themselves are covered by test_database_tools; the SQL by app/local_tests. No
MySQL, Qdrant, LLM, or network.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from app.catalog import queries as state
from app.retrieval.structured import answerer as dr
from app.retrieval.structured import planner
from app.retrieval.structured.types import ToolResult
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


def test_answer_structured_unresolved_theme_is_terminal_not_a_fallthrough(monkeypatch):
    """A theme that does not resolve to a known term is understood-but-unanswerable
    — the answer names it explicitly rather than silently falling through to a
    vague semantic-search guess (docs/database-retrieval-redesign.md §7)."""
    monkeypatch.setattr("app.catalog.terms.resolve_terms", lambda *a, **k: [])
    monkeypatch.setattr(state, "count_documents", _forbid_count)
    analysis = qp.QueryAnalysis(
        search_query="how many events under Mystery?",
        intent="structured", operation="count", bundle="events", theme="Mystery",
    )
    out = dr.answer_structured("how many events under Mystery?", analysis=analysis)
    assert out["answer"] == "No theme matching 'Mystery' found."


def test_answer_structured_unresolved_tag_is_terminal_not_a_fallthrough(monkeypatch):
    monkeypatch.setattr("app.catalog.terms.resolve_terms", lambda *a, **k: [])
    monkeypatch.setattr(state, "count_documents", _forbid_count)
    analysis = qp.QueryAnalysis(
        search_query="how many posts are tagged nonexistent?",
        intent="structured", operation="count", tags=["nonexistent"],
    )
    out = dr.answer_structured(
        "how many posts are tagged nonexistent?", analysis=analysis
    )
    assert out["answer"] == "No tag matching 'nonexistent' found."


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


def test_answer_structured_generic_publications_spans_all_types(monkeypatch):
    # "publications" is a collective word; the classifier may collapse it onto the
    # research_papers bundle, which would under-count a person's total output. The
    # bundle must be dropped so the count spans every content type.
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 21)
    analysis = qp.QueryAnalysis(
        search_query="how many publications from Dr Suneel Pandey",
        intent="structured", operation="count",
        bundle="research_papers", author="Dr Suneel Pandey",
    )
    out = dr.answer_structured(
        "tell me overall number of publications from Dr Suneel Pandey", analysis=analysis
    )
    assert seen["bundle"] is None  # spans all content types, not just papers
    assert out["answer"] == "There are 21 items matching your query."


def test_answer_structured_named_type_keeps_bundle(monkeypatch):
    # When the user actually names the type, the bundle is honored even though the
    # word "publications" is also present.
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 10)
    analysis = qp.QueryAnalysis(
        search_query="how many research paper publications from Dr Suneel Pandey",
        intent="structured", operation="count",
        bundle="research_papers", author="Dr Suneel Pandey",
    )
    dr.answer_structured(
        "how many research paper publications from Dr Suneel Pandey", analysis=analysis
    )
    assert seen["bundle"] == "research_papers"


def test_spans_all_content_helper():
    # Generic term, bundle words absent from the question -> span all types.
    assert dr._spans_all_content("how many publications from Dr X", "research_papers")
    # The named type appears -> keep the bundle.
    assert not dr._spans_all_content("how many research papers from Dr X", "research_papers")
    # No generic term -> keep the bundle.
    assert not dr._spans_all_content("how many articles from Dr X", "article")
    # No bundle to begin with -> nothing to clear.
    assert not dr._spans_all_content("how many publications from Dr X", None)


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


def test_answer_structured_prefers_multi_plan_when_enabled(monkeypatch):
    sentinel = object()
    seen: dict = {}

    def forbid_v1(*a, **k):
        raise AssertionError("v1 plan must not run when the multi-call plan succeeds")

    monkeypatch.setattr(
        dr, "get_settings", lambda: SimpleNamespace(database_multi_call_enabled=True)
    )
    monkeypatch.setattr(planner, "plan_multi", lambda q, *, output_format: sentinel)
    monkeypatch.setattr(planner, "plan", forbid_v1)
    monkeypatch.setattr(
        planner, "execute",
        lambda db_plan, *, question=None: seen.update(plan=db_plan)
        or [ToolResult(tool="count_records", ok=True, rendered="R")],
    )
    analysis = qp.QueryAnalysis(search_query="x", intent="structured", operation="count")
    out = dr.answer_structured("2023 vs 2024?", analysis=analysis)

    assert seen["plan"] is sentinel  # the v2 plan was executed
    assert out["answer"] == "R"


def test_answer_structured_partial_success_drops_terminal_failure(monkeypatch):
    """A terminal failure alongside a successful call in the same multi-call
    plan is dropped exactly like any other ok=False result — the terminal
    check only kicks in when EVERY call failed (see _terminal_result)."""
    sentinel = object()
    monkeypatch.setattr(
        dr, "get_settings", lambda: SimpleNamespace(database_multi_call_enabled=True)
    )
    monkeypatch.setattr(planner, "plan_multi", lambda q, *, output_format: sentinel)
    monkeypatch.setattr(
        planner, "execute",
        lambda db_plan, *, question=None: [
            ToolResult(tool="count_records", ok=True, rendered="3 items."),
            ToolResult(tool="count_records", ok=False, error_kind="unresolved",
                      rendered="No theme matching 'X' found."),
        ],
    )
    analysis = qp.QueryAnalysis(search_query="x", intent="structured", operation="count")
    out = dr.answer_structured("x", analysis=analysis)
    assert out["answer"] == "3 items."


def test_terminal_result_finds_first_terminal_failure():
    results = [
        ToolResult(tool="count_records", ok=False, error_kind=None),
        ToolResult(tool="count_records", ok=False, error_kind="unresolved",
                  rendered="No theme matching 'X' found."),
    ]
    terminal = dr._terminal_result(results)
    assert terminal is not None and terminal.rendered == "No theme matching 'X' found."


def test_terminal_result_none_when_no_failure_is_terminal():
    results = [ToolResult(tool="count_records", ok=False, error_kind="no_records")]
    assert dr._terminal_result(results) is None


def test_terminal_result_none_for_empty_results():
    assert dr._terminal_result([]) is None


def test_answer_structured_falls_back_to_v1_when_multi_none(monkeypatch):
    monkeypatch.setattr(
        dr, "get_settings", lambda: SimpleNamespace(database_multi_call_enabled=True)
    )
    monkeypatch.setattr(planner, "plan_multi", lambda q, *, output_format: None)
    monkeypatch.setattr(state, "count_documents", lambda **kw: 2)

    analysis = qp.QueryAnalysis(
        search_query="x", intent="structured", operation="count", bundle="events"
    )
    out = dr.answer_structured("how many events?", analysis=analysis)
    assert out["answer"] == "There are 2 events matching your query."


def test_compose_stacks_sections_and_renumbers_citations():
    r1 = ToolResult(
        tool="list_records", ok=True, data={"records": [{"title": "A"}]},
        citations=[{"n": 1, "title": "A"}], rendered="Section one",
    )
    r2 = ToolResult(
        tool="list_records", ok=True,
        data={"records": [{"title": "B"}, {"title": "C"}]},
        citations=[{"n": 1, "title": "B"}, {"n": 2, "title": "C"}],
        rendered="Section two",
    )
    out = dr._compose([r1, r2])
    assert out["answer"] == "Section one\n\nSection two"
    # Second section's citations shift up so numbering is unique across sections.
    assert [(c["n"], c["title"]) for c in out["citations"]] == [
        (1, "A"), (2, "B"), (3, "C"),
    ]
    assert out["used_chunks"] == 3  # 1 + 2 records
    assert out["intent"] == "structured" and out["conflict"] is False


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


def test_facet_filters_tags_exact_match_author_not_filtered():
    analysis = qp.QueryAnalysis(
        search_query="x", author="Dr R K Sharma", tags=["biofuels", "solar"]
    )
    conds = qp._facet_filters(analysis)
    by_key = {getattr(c, "key", None): c for c in conds}
    assert by_key["tags"].match.any == ["biofuels", "solar"]
    # author is intentionally NOT a hard filter: exact keyword match on sparse
    # display-name metadata excludes most of the corpus and rarely matches the
    # LLM's extracted form (see _facet_filters). Scoping stays on the catalog path.
    assert "authors" not in by_key


def test_facet_filters_absent_tags_add_nothing():
    conds = qp._facet_filters(qp.QueryAnalysis(search_query="x"))
    keys = {getattr(c, "key", None) for c in conds}
    assert "tags" not in keys


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
