"""Unit tests for the count / structured-query path.

Covers the deterministic pieces of "how many <bundle> / by <author> / on <date>":
bundle normalization, date-range derivation, the answer label, the semantic-path
datetime filter, and the value normalizers — plus the catalog wiring in
``_answer_count`` / ``answer_structured`` with ``count_documents`` and the LLM
parse stubbed. No MySQL, Qdrant, LLM, or network needed; the SQL counting itself
is exercised by ``app/local_tests/counting_test``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.ingestion import state
from app.retrieval import drupal_router as dr
from app.retrieval import query_processor as qp


# --------------------------------------------------------------------------- #
# Bundle normalization — "search it in event" must resolve to the real bundle.
# --------------------------------------------------------------------------- #

def test_normalize_bundle_known_and_variants():
    assert dr._normalize_bundle("event") == "events"          # plural fix
    assert dr._normalize_bundle(" Events ") == "events"       # case / whitespace
    assert dr._normalize_bundle("events") == "events"
    assert dr._normalize_bundle("press release") == "press_release"
    assert dr._normalize_bundle("press-release") == "press_release"
    assert dr._normalize_bundle("person") == "people"         # irregular synonym
    assert dr._normalize_bundle("papers") == "research_papers"  # plural synonym
    assert dr._normalize_bundle("news") == "news"


def test_normalize_bundle_unknown_stays_specific():
    # An unknown type must count as zero, not silently widen to "all bundles".
    assert dr._normalize_bundle("widgets") == "widgets"
    assert dr._normalize_bundle(None) is None
    assert dr._normalize_bundle("") is None


# --------------------------------------------------------------------------- #
# Date range + label.
# --------------------------------------------------------------------------- #

def test_date_range_year_only_spans_calendar_year():
    sq = dr.StructuredQuery(operation="count", year=2024)
    assert dr._date_range(sq) == (datetime(2024, 1, 1), datetime(2025, 1, 1))


def test_date_range_explicit_dates_override_year():
    sq = dr.StructuredQuery(
        operation="count", year=2024, date_from="2023-06-01", date_to="2023-07-01"
    )
    assert dr._date_range(sq) == (datetime(2023, 6, 1), datetime(2023, 7, 1))


def test_date_range_open_ended_and_empty():
    assert dr._date_range(dr.StructuredQuery(operation="count", date_from="2023-01-01")) == (
        datetime(2023, 1, 1),
        None,
    )
    assert dr._date_range(dr.StructuredQuery(operation="count")) == (None, None)


def test_period_label_matches_range():
    q = dr.StructuredQuery
    assert dr._period_label(q(operation="count", year=2024)) == " in 2024"
    assert (
        dr._period_label(q(operation="count", date_from="2024-03-15", date_to="2024-03-16"))
        == " between 2024-03-15 and 2024-03-16"
    )
    assert dr._period_label(q(operation="count", date_from="2023-01-01")) == " since 2023-01-01"
    assert dr._period_label(q(operation="count", date_to="2023-01-01")) == " before 2023-01-01"
    assert dr._period_label(q(operation="count")) == ""
    # a whole-year range (as the LLM tends to emit) collapses to "in YYYY"
    assert dr._period_label(q(operation="count", date_from="2024-01-01", date_to="2025-01-01")) == " in 2024"


def test_count_result_grammar_and_labels():
    ans = lambda n, scope: dr._count_result(n, scope, "")["answer"]
    assert ans(1, "events") == "There is 1 event matching your query."
    assert ans(3, "events") == "There are 3 events matching your query."
    assert ans(2, "news") == "There are 2 news items matching your query."
    assert ans(1, "items") == "There is 1 item matching your query."
    # unknown bundle -> humanized best-effort, still grammatical
    assert ans(1, "widgets") == "There is 1 widget matching your query."
    assert ans(2, "widget") == "There are 2 widgets matching your query."


# --------------------------------------------------------------------------- #
# Catalog wiring — stub count_documents, assert the filters we hand it.
# --------------------------------------------------------------------------- #

def test_answer_count_passes_catalog_filters(monkeypatch):
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 7)

    sq = dr.StructuredQuery(operation="count", bundle="events", author="Sharma", year=2024)
    out = dr._answer_count(sq)

    assert seen == {
        "source_type": "website",
        "bundle": "events",
        "entity_type": "node",  # facet terms/blocks never count as content
        "author": "Sharma",
        "published_from": datetime(2024, 1, 1),
        "published_to": datetime(2025, 1, 1),
    }
    assert out["answer"] == "There are 7 events in 2024 matching your query."
    assert out["intent"] == "structured"
    assert out["used_chunks"] == 0
    assert out["citations"] == []


def test_answer_count_specific_day(monkeypatch):
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 2)

    sq = dr.StructuredQuery(operation="count", date_from="2024-03-15", date_to="2024-03-16")
    out = dr._answer_count(sq)

    assert seen["published_from"] == datetime(2024, 3, 15)
    assert seen["published_to"] == datetime(2024, 3, 16)
    assert out["answer"] == "There are 2 items between 2024-03-15 and 2024-03-16 matching your query."


def test_answer_count_returns_none_on_db_error(monkeypatch):
    def boom(**kw):
        raise RuntimeError("db down")

    monkeypatch.setattr(state, "count_documents", boom)
    assert dr._answer_count(dr.StructuredQuery(operation="count", bundle="events")) is None


def test_answer_structured_normalizes_bundle_for_count(monkeypatch):
    monkeypatch.setattr(
        dr, "parse_structured", lambda q, h=None: dr.StructuredQuery(operation="count", bundle="event")
    )
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 3)

    out = dr.answer_structured("how many events?")

    assert seen["bundle"] == "events"  # normalized before the catalog query
    assert out["answer"] == "There are 3 events matching your query."


# --------------------------------------------------------------------------- #
# Semantic path — dates become a Qdrant DatetimeRange on published_at.
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


# --------------------------------------------------------------------------- #
# Unified analysis schema — structured slots default off; ProcessedQuery
# carries the full analysis for the structured route.
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
    analysis = qp.QueryAnalysis(
        search_query="how many events in 2024",
        intent="structured",
        operation="count",
        bundle="events",
    )

    class _FakeStructured:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            return analysis

    monkeypatch.setattr(qp, "get_structured_llm", lambda: _FakeStructured())
    pq = qp.process("how many events in 2024?")
    assert pq.analysis is analysis
    assert pq.intent == "structured"


def test_process_passthrough_has_no_analysis(monkeypatch):
    def boom():
        raise RuntimeError("llm down")

    monkeypatch.setattr(qp, "get_structured_llm", boom)
    pq = qp.process("hello")
    assert pq.analysis is None
    assert pq.intent == "qa"


# --------------------------------------------------------------------------- #
# Value normalizers.
# --------------------------------------------------------------------------- #

def test_parse_bound_normalizes_to_utc():
    assert qp._parse_bound("2024-03-15") == datetime(2024, 3, 15, tzinfo=timezone.utc)
    assert qp._parse_bound("2024-03-15T12:00:00+05:30") == datetime(
        2024, 3, 15, 6, 30, tzinfo=timezone.utc
    )
    assert qp._parse_bound("nonsense") is None
    assert qp._parse_bound(None) is None


def test_state_to_datetime_strips_tz_to_utc_naive():
    assert state._to_datetime("2024-03-15T00:00:00+00:00") == datetime(2024, 3, 15)
    assert state._to_datetime("2024-03-15T05:30:00+05:30") == datetime(2024, 3, 15)
    assert state._to_datetime(None) is None
    assert state._to_datetime("bad") is None


def test_state_like_wraps_and_escapes():
    assert state._like("Sharma") == "%Sharma%"
    assert state._like("a_b") == r"%a\_b%"
    assert state._like("50%") == r"%50\%%"
