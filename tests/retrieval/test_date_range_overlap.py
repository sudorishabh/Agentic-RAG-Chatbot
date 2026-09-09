"""Date-range retrieval semantics, over the canonical fields only.

The contract these defend, in one line: **a date query selects every document
whose period overlaps the requested range**, not every document whose start
falls inside it. A completed project running 2020-2024 is a document about 2022
and has to come back for 2022; the previous single-bound condition compared only
``effective_start_date`` and so treated every period as a point at its start,
missing a four-year project in three of its five years.

Two things are deliberately absent from every test here. No Drupal field name —
``field_event_start_date`` and its siblings are the *source* of a date and stop
existing at the ingest boundary; retrieval sees ``effective_start_date``,
``effective_end_date`` and the two precision markers. And no invented day: a
document stated as "2022" is stored as 2022-01-01 and must match a query about
June 2022, because we know the year and nothing says it is not June.

The overlap tests run against a real Qdrant, in a throwaway collection, because
the semantics are the engine's and a hand-rolled filter evaluator would only
prove that two of my own functions agree. They skip when Qdrant is unreachable.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest

from app.retrieval.understanding.filters import (
    _floor,
    date_conditions,
    date_scope_filter,
)

UTC = timezone.utc


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def _iso(text: str) -> str:
    return _at(text).isoformat()


# --------------------------------------------------------------------------- #
# Flooring: the range is compared at the document's own precision
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "precision, expected",
    [("day", "2022-06-15"), ("month", "2022-06-01"), ("year", "2022-01-01")],
)
def test_the_lower_bound_is_floored_to_the_documents_precision(precision, expected):
    assert _floor(_at("2022-06-15"), precision) == _at(expected)


def test_an_unknown_precision_is_treated_as_a_day():
    """The safe direction: an unrecognised marker must not widen the range."""
    assert _floor(_at("2022-06-15"), "fortnight") == _at("2022-06-15")


# --------------------------------------------------------------------------- #
# The scope object itself
# --------------------------------------------------------------------------- #

def test_no_bounds_means_no_scope():
    assert date_scope_filter(None, None) is None


def test_an_open_sided_query_carries_only_the_bound_it_has():
    upper = date_scope_filter(None, _at("2020-01-01"))
    lower = date_scope_filter(_at("2023-03-01"), None)
    assert len(upper.must) == 1 and len(lower.must) == 1


def test_the_date_scope_survives_the_filter_retry():
    """`retriever.retrieve` drops the LLM's guessed facets on a total miss but
    holds the period the user actually asked for. The scope is a nested filter
    now, and a nested filter has no `key` — so this is what stops the retry
    silently widening the query to every year."""
    scope = date_scope_filter(_at("2022-01-01"), _at("2023-01-01"))
    from qdrant_client.models import FieldCondition, MatchValue

    theme = FieldCondition(key="categories", match=MatchValue(value="Transport"))
    held = date_conditions([theme, scope])
    assert held == [scope]


# --------------------------------------------------------------------------- #
# Overlap, against a real Qdrant
# --------------------------------------------------------------------------- #

def _qdrant_or_skip():
    from qdrant_client import QdrantClient

    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    try:
        client = QdrantClient(url=url, timeout=10)
        client.get_collections()
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Qdrant is not reachable at {url}: {exc}")
    return client


#: One document per shape the date model can produce. ``id`` is the name the
#: assertions use; everything else is exactly what `build_payload` would write.
_DOCUMENTS = {
    # A single date known to the day.
    "day_point": {"effective_start_date": _iso("2022-03-15"), "bundle": "news"},
    # A date the source stated only as a year: stored as 1 January, marked.
    "year_point": {"effective_start_date": _iso("2022-01-01"),
                   "start_precision": "year", "bundle": "research_papers"},
    # A date stated as a month.
    "month_point": {"effective_start_date": _iso("2007-09-01"),
                    "start_precision": "month", "bundle": "report"},
    # The headline case: a closed period spanning several years.
    "closed_period": {"effective_start_date": _iso("2020-01-01"),
                      "effective_end_date": _iso("2024-06-30"),
                      "bundle": "completed_projects"},
    # A one-day event, where start and end are the same day.
    "one_day_event": {"effective_start_date": _iso("2026-08-21"),
                      "effective_end_date": _iso("2026-08-21"),
                      "bundle": "events"},
    # An open-ended period: a start, and no end field at all by declaration.
    "open_ended": {"effective_start_date": _iso("2005-04-01"),
                   "bundle": "ongoing_projects"},
    # No date at all. Must never satisfy a date scope.
    "undated": {"bundle": "page"},
}


@pytest.fixture(scope="module")
def collection():
    client = _qdrant_or_skip()
    from qdrant_client.models import Distance, PointStruct, VectorParams

    from app.core.clients.vector_store import PAYLOAD_INDEXES, _schema_for

    name = f"test_date_overlap_{uuid.uuid4().hex[:8]}"
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=2, distance=Distance.COSINE),
    )
    try:
        # The same indexes production declares, so the test exercises the
        # filter as it will actually be served.
        for field in ("effective_start_date", "effective_end_date",
                      "start_precision", "end_precision", "bundle"):
            client.create_payload_index(
                collection_name=name, field_name=field,
                field_schema=_schema_for(PAYLOAD_INDEXES[field]), wait=True,
            )
        client.upsert(collection_name=name, points=[
            PointStruct(id=index + 1, vector=[0.1, 0.2],
                        payload={"name": name_, **payload})
            for index, (name_, payload) in enumerate(_DOCUMENTS.items())
        ])
        yield client, name
    finally:
        client.delete_collection(name)


def _matches(collection, lo: str | None, hi: str | None) -> set[str]:
    client, name = collection
    scope = date_scope_filter(_at(lo) if lo else None, _at(hi) if hi else None)
    points, _ = client.scroll(collection_name=name, scroll_filter=scope,
                              limit=50, with_payload=True, with_vectors=False)
    return {p.payload["name"] for p in points}


def test_a_multi_year_project_matches_a_query_about_a_year_inside_it(collection):
    """The requirement, stated as the user did: 2020-2024 must match 2022."""
    assert "closed_period" in _matches(collection, "2022-01-01", "2023-01-01")


def test_a_whole_year_query(collection):
    got = _matches(collection, "2022-01-01", "2023-01-01")
    assert got == {"day_point", "year_point", "closed_period", "open_ended"}
    assert "undated" not in got


def test_a_single_month_query_keeps_a_year_precision_document(collection):
    """June 2022. `year_point` is stored as 2022-01-01 but all the source said
    was "2022", so excluding it would assert it is not from June — which nobody
    knows. `day_point` is 15 March and genuinely is not in June."""
    got = _matches(collection, "2022-06-01", "2022-07-01")
    assert "year_point" in got
    assert "day_point" not in got
    assert got == {"year_point", "closed_period", "open_ended"}


def test_a_month_precision_document_matches_its_own_month_and_year(collection):
    assert "month_point" in _matches(collection, "2007-09-01", "2007-10-01")
    assert "month_point" in _matches(collection, "2007-01-01", "2008-01-01")
    assert "month_point" not in _matches(collection, "2007-08-01", "2007-09-01")


def test_a_query_before_everything_matches_only_what_started_then(collection):
    got = _matches(collection, None, "2006-01-01")
    assert got == {"open_ended"}


def test_a_query_after_a_period_ends_excludes_it(collection):
    got = _matches(collection, "2025-01-01", "2026-01-01")
    assert "closed_period" not in got, "the project ended in June 2024"
    assert "open_ended" in got, "an ongoing project is still running"


def test_an_open_ended_period_matches_every_year_from_its_start(collection):
    for year in ("2005", "2015", "2026"):
        assert "open_ended" in _matches(collection, f"{year}-01-01", f"{int(year)+1}-01-01")
    assert "open_ended" not in _matches(collection, "2004-01-01", "2005-01-01"), (
        "not before it started"
    )


def test_the_boundaries_are_half_open(collection):
    """`lo` is included, `hi` excluded. A period ending exactly on `lo` overlaps
    by one day and matches; a document starting exactly on `hi` does not."""
    # closed_period ends 2024-06-30, so a range beginning that day still overlaps.
    assert "closed_period" in _matches(collection, "2024-06-30", "2024-07-31")
    assert "closed_period" not in _matches(collection, "2024-07-01", "2024-08-01")
    # one_day_event starts 2026-08-21: a range ending exactly there excludes it.
    assert "one_day_event" not in _matches(collection, "2026-08-01", "2026-08-21")
    assert "one_day_event" in _matches(collection, "2026-08-21", "2026-08-22")


def test_an_undated_document_never_satisfies_a_date_scope(collection):
    for lo, hi in (("2000-01-01", "2030-01-01"), (None, "2030-01-01"),
                   ("2000-01-01", None)):
        assert "undated" not in _matches(collection, lo, hi)


def test_a_one_day_event_matches_its_own_day_only(collection):
    assert "one_day_event" in _matches(collection, "2026-08-01", "2026-09-01")
    assert "one_day_event" not in _matches(collection, "2026-07-01", "2026-08-01")
