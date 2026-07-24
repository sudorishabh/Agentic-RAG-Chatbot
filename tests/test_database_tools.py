"""Phase 2: the four catalog tools. state.* and terms.* are stubbed; no DB."""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.retrieval.structured import tools
from app.retrieval.structured.types import RecordFilters


def _rec(document_id="d1", title="A", url="http://a", published_at="2024-05-01T00:00:00",
         bundle="news"):
    return StateRecord(
        document_id=document_id, source_type="website", source_key="k",
        fingerprint="f", title=title, url=url, published_at=published_at, bundle=bundle,
    )


@pytest.fixture
def resolve_theme_ok(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.terms.resolve_terms",
        lambda name, vocabulary=None: [{"term_uuid": "u1", "name": name}],
    )


# --------------------------------------------------------------------------- #
# count_records
# --------------------------------------------------------------------------- #

def test_count_records_renders_and_passes_scope(monkeypatch, resolve_theme_ok):
    seen = {}

    def fake_count(**kw):
        seen.update(kw)
        return 3

    monkeypatch.setattr("app.catalog.queries.count_documents", fake_count)
    r = tools.count_records(
        "news", RecordFilters(theme="Climate", date_from="2024-01-01", date_to="2025-01-01")
    )
    assert r.ok and r.data == {"count": 3}
    assert r.rendered == "There are 3 news items on 'Climate' in 2024 matching your query."
    assert seen["bundle"] == "news"
    assert seen["source_type"] == "website" and seen["entity_type"] == "node"
    assert seen["term_uuids"] == ["u1"]


def test_count_records_unknown_entity_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 0)
    r = tools.count_records("tenders", RecordFilters())
    assert r.ok is False and "unknown entity" in (r.error or "")


def test_count_records_unresolved_theme_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.terms.resolve_terms", lambda *a, **k: [])
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 99)
    r = tools.count_records("news", RecordFilters(theme="Mystery"))
    assert r.ok is False  # must not answer a misleading zero/count


def test_count_records_singular_verb(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 1)
    r = tools.count_records("report", RecordFilters())
    assert r.rendered == "There is 1 report matching your query."


def test_count_records_bare_total(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 123)
    r = tools.count_records(None, RecordFilters())
    assert r.rendered == "There are 123 items matching your query."


def test_count_records_date_range_render(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 2)
    r = tools.count_records(
        None, RecordFilters(date_from="2024-03-15", date_to="2024-03-16")
    )
    assert r.rendered == (
        "There are 2 items between 2024-03-15 and 2024-03-16 matching your query."
    )


def test_count_records_db_error_is_not_ok(monkeypatch):
    def boom(**k):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.catalog.queries.count_documents", boom)
    assert tools.count_records("news", RecordFilters()).ok is False


# --------------------------------------------------------------------------- #
# list_records
# --------------------------------------------------------------------------- #

def test_list_records_plain(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters())
    assert r.ok
    assert r.data["records"][0]["document_id"] == "d1"
    assert r.citations[0]["title"] == "A"
    assert r.rendered == "Here is what I found:\n- A (http://a)"


def test_list_records_table(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters(), output_format="table")
    assert "| Title | Published | Type |" in r.rendered


def test_list_records_empty_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [])
    r = tools.list_records("news", RecordFilters())
    assert r.ok is False


def test_list_records_timeline_groups_by_year(monkeypatch):
    recs = [
        _rec("d1", "Old", "http://old", "2023-11-02T00:00:00"),
        _rec("d2", "New", "http://new", "2024-05-20T00:00:00"),
        _rec("d3", "NoDate", None, None),
    ]
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: recs)
    r = tools.list_records("news", RecordFilters(), output_format="timeline")
    a = r.rendered
    assert a.index("2024:") < a.index("2023:") < a.index("Undated:")
    assert "- 2024-05: New (http://new)" in a
    assert "- n.d.: NoDate" in a
    # citations follow the rendered (newest-first) order
    assert [c["title"] for c in r.citations] == ["New", "Old", "NoDate"]


# --------------------------------------------------------------------------- #
# lookup_record
# --------------------------------------------------------------------------- #

def test_lookup_record_chains_on_content_question(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.lookup_record(
        "report", "Solar Report", RecordFilters(),
        question="what does the Solar Report say about capacity?",
    )
    assert r.data["chain_document_id"] == "d1"
    assert r.ok  # also renders the list


def test_lookup_record_no_chain_on_browse(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.lookup_record(
        "report", "Solar Report", RecordFilters(), question="show the Solar Report",
    )
    assert r.data["chain_document_id"] is None


def test_lookup_record_no_chain_when_multiple_match(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.list_documents",
        lambda **k: [_rec("d1"), _rec("d2")],
    )
    r = tools.lookup_record(
        "report", "Report", RecordFilters(), question="what does the report say?",
    )
    assert r.data["chain_document_id"] is None  # ambiguous -> no chain


# --------------------------------------------------------------------------- #
# aggregate_records
# --------------------------------------------------------------------------- #

def test_aggregate_records_table_and_dimension(monkeypatch):
    seen = {}

    def fake_dist(group_by, **kw):
        seen["dimension"] = group_by
        return [("Climate", 5), ("Energy", 3)]

    monkeypatch.setattr("app.catalog.queries.distribution", fake_dist)
    r = tools.aggregate_records(None, "theme", RecordFilters(), output_format="table")
    assert r.ok
    assert r.data["groups"] == [["Climate", 5], ["Energy", 3]]
    assert seen["dimension"] == "theme"  # theme -> theme facet
    assert "| theme | count |" in r.rendered


def test_aggregate_records_plain(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distribution", lambda group_by, **k: [("Climate", 5)]
    )
    r = tools.aggregate_records(None, "theme", RecordFilters())
    assert r.rendered == "Distribution of items by theme:\n- Climate: 5"


def test_aggregate_records_content_type_maps_to_bundle(monkeypatch):
    seen = {}

    def fake_dist(group_by, **kw):
        seen["dimension"] = group_by
        return [("news", 10)]

    monkeypatch.setattr("app.catalog.queries.distribution", fake_dist)
    tools.aggregate_records(None, "content_type", RecordFilters())
    assert seen["dimension"] == "bundle"


def test_aggregate_records_empty_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.distribution", lambda group_by, **k: [])
    r = tools.aggregate_records("news", "year", RecordFilters())
    assert r.ok is False
