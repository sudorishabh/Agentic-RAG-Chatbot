"""Unit tests for the eval runner's scoring logic.

Covers the deterministic pieces: value-in-answer matching (word-boundary for
numbers), answer-shape checks, routing field comparison, SQL expectation
execution, recall/MRR extras, percentile and aggregation math, and golden-file
filtering. Pipeline and MySQL are stubbed; no services, no LLM.
"""

from __future__ import annotations

from app.ingestion import state
from app.retrieval import query_processor as qp
from scripts.eval import run_eval as ev


# --------------------------------------------------------------------------- #
# Value matching and format shapes.
# --------------------------------------------------------------------------- #

def test_value_in_answer_numbers_need_word_boundaries():
    assert ev._value_in_answer("936", "There are 936 completed projects.")
    assert not ev._value_in_answer("93", "There are 936 completed projects.")
    assert not ev._value_in_answer("0", "Published in 2020.")
    assert ev._value_in_answer("0", "There are 0 items matching your query.")


def test_value_in_answer_text_is_ci_substring():
    assert ev._value_in_answer("Ken-Betwa", "the ken-betwa project flood")
    assert not ev._value_in_answer("Ganga", "the ken-betwa project flood")


def test_format_ok_table_needs_rows_and_separator():
    table = "Intro:\n| Title | Count |\n| --- | --- |\n| A | 3 |"
    assert ev._format_ok("table", table)
    assert not ev._format_ok("table", "| header only |")
    assert not ev._format_ok("table", "just prose")


def test_format_ok_timeline_needs_two_dated_lines():
    good = "2024:\n- 2024-05: A\n2023:\n- 2023-01: B"
    assert ev._format_ok("timeline", good)
    assert not ev._format_ok("timeline", "- 2024-05: only one dated line")


def test_format_ok_summary_bounds_sentences():
    assert ev._format_ok("summary", "One. Two. Three.")
    assert not ev._format_ok("summary", "S. " * 10)
    assert ev._format_ok("default", "anything")


# --------------------------------------------------------------------------- #
# Routing comparison.
# --------------------------------------------------------------------------- #

def _pq(**kw):
    analysis = qp.QueryAnalysis(
        search_query="x", intent=kw.get("intent", "structured"),
        operation=kw.get("operation"), bundle=kw.get("bundle"),
        theme=kw.get("theme"), answer_format=kw.get("answer_format", "default"),
        date_from=kw.get("date_from"),
    )
    return qp.ProcessedQuery(
        original="q", search_query="x", intent=analysis.intent,
        answer_format=analysis.answer_format, analysis=analysis,
    )


def test_run_routing_checks_exact_and_contains(monkeypatch):
    monkeypatch.setattr(
        qp, "process",
        lambda q, h=None: _pq(intent="structured", operation="count",
                              bundle="news", theme="Climate Change",
                              date_from="2024-01-01"),
    )
    item = {
        "id": "r1", "class": "routing", "question": "q",
        "expect": {"intent": "structured", "operation": "count", "bundle": "news",
                   "theme_contains": "climate", "date_from": "2024-01-01"},
    }
    checks, extras, latency, stages = ev._run_routing(item)
    assert all(checks.values()), checks
    assert extras["got"]["bundle"] == "news"


def test_run_routing_flags_mismatches_and_passthrough(monkeypatch):
    monkeypatch.setattr(qp, "process", lambda q, h=None: _pq(intent="qa"))
    item = {
        "id": "r2", "class": "routing", "question": "q",
        "expect": {"intent": "structured", "operation": "count"},
    }
    checks, *_ = ev._run_routing(item)
    assert checks == {"intent": False, "operation": False}

    # Passthrough (no analysis): slot fields compare as None -> fail, not crash.
    passthrough = qp.ProcessedQuery(original="q", search_query="q")
    monkeypatch.setattr(qp, "process", lambda q, h=None: passthrough)
    checks, *_ = ev._run_routing(item)
    assert checks["intent"] is False and checks["operation"] is False


# --------------------------------------------------------------------------- #
# SQL expectations.
# --------------------------------------------------------------------------- #

def test_sql_expected_count(monkeypatch):
    seen = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 42)
    values, note = ev._sql_expected(
        {"fn": "count_documents",
         "kwargs": {"bundle": "news", "published_from": "2025-01-01"}}
    )
    assert values == ["42"] and "42" in note
    assert seen["source_type"] == "website" and seen["entity_type"] == "node"
    assert seen["published_from"].year == 2025


def test_sql_expected_distribution_top3(monkeypatch):
    monkeypatch.setattr(
        state, "distribution",
        lambda g, **kw: [("news", 10), ("events", 5), ("videos", 2), ("x", 1)],
    )
    values, _ = ev._sql_expected({"fn": "distribution", "kwargs": {"group_by": "bundle"}})
    assert values == ["news", "events", "videos", "10", "5", "2"]


def test_sql_expected_list_most_recent(monkeypatch):
    rec = state.StateRecord(
        document_id="d1", source_type="website", source_key="k",
        fingerprint="f", title="Newest",
    )
    monkeypatch.setattr(state, "list_documents", lambda **kw: [rec])
    values, _ = ev._sql_expected({"fn": "list_documents", "kwargs": {}})
    assert values == ["Newest"]

    monkeypatch.setattr(state, "list_documents", lambda **kw: [])
    values, note = ev._sql_expected({"fn": "list_documents", "kwargs": {}})
    assert values == [] and "no rows" in note


# --------------------------------------------------------------------------- #
# Aggregation math.
# --------------------------------------------------------------------------- #

def test_pctl_nearest_rank():
    assert ev._pctl([10.0], 0.95) == 10.0
    # index = round(q * (n-1)): p50 of 4 values rounds up to the 3rd
    assert ev._pctl([1.0, 2.0, 3.0, 4.0], 0.5) == 3.0
    assert ev._pctl([1.0, 2.0, 3.0, 4.0], 0.95) == 4.0
    assert ev._pctl([1.0, 2.0, 3.0, 4.0, 5.0], 0.5) == 3.0


def test_aggregate_classes_and_stages():
    items = [
        {"id": "a", "class": "routing", "passed": True,
         "checks": {"intent": True}, "extras": {}, "stages": {"rag.search": 100.0}},
        {"id": "b", "class": "routing", "passed": False,
         "checks": {"intent": False}, "extras": {}, "stages": {"rag.search": 300.0}},
        {"id": "c", "class": "retrieval", "passed": True, "checks": {"recall_full": True},
         "extras": {"recall": 1.0, "mrr": 1.0, "website_lead": True},
         "stages": {}},
    ]
    classes = ev._aggregate(items)
    assert classes["routing"] == {
        "total": 2, "passed": 1, "score": 0.5, "field_accuracy": {"intent": 0.5},
    }
    assert classes["retrieval"]["mean_recall"] == 1.0
    assert classes["retrieval"]["website_lead_rate"] == 1.0

    stages = ev._aggregate_stages(items)
    assert stages["rag.search"]["count"] == 2
    assert stages["rag.search"]["p95_ms"] == 300.0


# --------------------------------------------------------------------------- #
# Golden loading filters.
# --------------------------------------------------------------------------- #

def test_load_golden_filters():
    all_items = ev._load_golden(None, None)
    assert len(all_items) >= 30
    routing = ev._load_golden("routing", None)
    assert routing and all(i["class"] == "routing" for i in routing)
    one = ev._load_golden(None, {"ana-001"})
    assert [i["id"] for i in one] == ["ana-001"]
