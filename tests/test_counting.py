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


# --------------------------------------------------------------------------- #
# Count fall-through guard — unresolvable scopes are usually misrouted content
# questions; they must reach semantic search, not answer "0 items".
# --------------------------------------------------------------------------- #

def _forbid_count(**kw):
    raise AssertionError("count_documents must not be called")


def test_answer_count_unknown_bundle_falls_through(monkeypatch):
    monkeypatch.setattr(state, "count_documents", _forbid_count)
    sq = dr.StructuredQuery(operation="count", bundle="widgets", year=2024)
    assert dr._answer_count(sq) is None


def test_answer_count_unresolved_theme_falls_through(monkeypatch):
    monkeypatch.setattr(dr.terms, "resolve_terms", lambda name: [])
    monkeypatch.setattr(state, "count_documents", _forbid_count)
    sq = dr.StructuredQuery(operation="count", theme="emissions by sector")
    assert dr._answer_count(sq) is None


def test_answer_count_bare_total_still_answers(monkeypatch):
    # No dimensions at all = a genuine corpus-size question.
    monkeypatch.setattr(state, "count_documents", lambda **kw: 123)
    out = dr._answer_count(dr.StructuredQuery(operation="count"))
    assert out["answer"] == "There are 123 items matching your query."


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
        dr, "parse_structured", lambda q, h=None: dr.StructuredQuery(operation="count", bundle="event")
    )
    seen: dict = {}
    monkeypatch.setattr(state, "count_documents", lambda **kw: seen.update(kw) or 3)

    out = dr.answer_structured("how many events?")

    assert seen["bundle"] == "events"  # normalized before the catalog query
    assert out["answer"] == "There are 3 events matching your query."


# --------------------------------------------------------------------------- #
# Unified-analysis routing — a provided analysis replaces the second LLM parse;
# the parse remains the fallback when no usable analysis came.
# --------------------------------------------------------------------------- #

def test_query_from_analysis_maps_fields():
    analysis = qp.QueryAnalysis(
        search_query="x",
        intent="structured",
        operation="distribution",
        bundle="news",
        theme="Climate",
        group_by="year",
        title_contains="solar",
        author="Sharma",
        date_from="2023-01-01",
        date_to="2024-01-01",
        limit=5,
    )
    sq = dr._query_from_analysis(analysis)
    assert sq.operation == "distribution"
    assert sq.bundle == "news"
    assert sq.theme == "Climate"
    assert sq.group_by == "year"
    assert sq.title_contains == "solar"
    assert sq.author == "Sharma"
    assert sq.year is None  # the unified prompt emits explicit dates instead
    assert (sq.date_from, sq.date_to) == ("2023-01-01", "2024-01-01")
    assert sq.limit == 5


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
# Format-aware renderers — deterministic table / timeline shapes from SQL rows.
# --------------------------------------------------------------------------- #

def _rec(document_id="d1", title="T", url="https://t/x", published_at=None, bundle="news"):
    return state.StateRecord(
        document_id=document_id, source_type="website", source_key="k",
        fingerprint="f", title=title, url=url, published_at=published_at,
        bundle=bundle,
    )


def test_answer_list_table_format(monkeypatch):
    recs = [
        _rec(title="Solar push", url="https://t/solar",
             published_at="2024-03-15T00:00:00", bundle="news"),
        _rec(document_id="d2", title="Wind | Energy", url=None,
             published_at=None, bundle="events"),
    ]
    monkeypatch.setattr(state, "list_documents", lambda **kw: recs)
    out = dr._answer_list(dr.StructuredQuery(operation="list"), "table")

    a = out["answer"]
    assert "| Title | Published | Type |" in a and "| --- | --- | --- |" in a
    assert "| [Solar push](https://t/solar) | 2024-03-15 | news |" in a
    assert "| Wind \\| Energy |  | events |" in a  # escaped pipe; no URL -> plain text
    assert len(out["citations"]) == 2


def test_answer_list_timeline_groups_by_year_desc(monkeypatch):
    recs = [
        _rec(document_id="d1", title="Old", url="https://t/old",
             published_at="2023-11-02T00:00:00"),
        _rec(document_id="d2", title="New", url="https://t/new",
             published_at="2024-05-20T00:00:00"),
        _rec(document_id="d3", title="NoDate", url=None, published_at=None),
    ]
    monkeypatch.setattr(state, "list_documents", lambda **kw: recs)
    out = dr._answer_list(dr.StructuredQuery(operation="list"), "timeline")

    a = out["answer"]
    assert a.index("2024:") < a.index("2023:") < a.index("Undated:")
    assert "- 2024-05: New (https://t/new)" in a
    assert "- 2023-11: Old (https://t/old)" in a
    assert "- n.d.: NoDate" in a
    # Citations follow the rendered (newest-first) order.
    assert [c["title"] for c in out["citations"]] == ["New", "Old", "NoDate"]


def test_answer_list_default_stays_bullets(monkeypatch):
    monkeypatch.setattr(
        state, "list_documents", lambda **kw: [_rec(title="Solar push", url="https://t/solar")]
    )
    out = dr._answer_list(dr.StructuredQuery(operation="list"))
    assert out["answer"] == "Here is what I found:\n- Solar push (https://t/solar)"


def test_answer_distribution_table_format(monkeypatch):
    monkeypatch.setattr(
        state, "distribution", lambda *a, **k: [("Climate", 12), ("Energy", 5)]
    )
    out = dr._answer_distribution(dr.StructuredQuery(operation="distribution"), "table")

    a = out["answer"]
    assert "| theme | count |" in a and "| --- | --- |" in a
    assert "| Climate | 12 |" in a and "| Energy | 5 |" in a


def test_answer_structured_passes_format_from_analysis(monkeypatch):
    monkeypatch.setattr(state, "distribution", lambda *a, **k: [("Climate", 2)])
    analysis = qp.QueryAnalysis(
        search_query="articles per theme as a table",
        intent="structured", operation="distribution", answer_format="table",
    )
    out = dr.answer_structured("articles per theme as a table", analysis=analysis)
    assert "| theme | count |" in out["answer"]


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
