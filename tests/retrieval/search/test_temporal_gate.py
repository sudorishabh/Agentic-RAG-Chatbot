"""Temporal scope detection and the "upcoming" retrieval gate.

Regression cover for the benchmark failure where "Are there any upcoming TERI
training programmes?" returned six *past* programmes (TERI-DST and TERI-ITEC
cycles from 2013-15): nothing distinguished "upcoming" from "ever", and nothing
consulted an event's own start date.
"""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.retrieval.search import temporal_gate as tg


def _block(document_id: str, n: int = 1, **payload):
    """A context block carrying only canonical payload fields.

    No Drupal field name appears here, and that is the point: the gate reads
    ``effective_start_date`` / ``effective_end_date`` and the precision markers
    out of the payload it already has, where it used to read
    ``field_event_start_date`` from ``documents.raw_meta`` over a MySQL round
    trip per query.
    """
    return SimpleNamespace(payload={"document_id": document_id, **payload}, n=n)


def _event(document_id: str, start: str, n: int = 1, **payload):
    return _block(document_id, n=n, bundle="events",
                  effective_start_date=f"{start}T00:00:00+00:00", **payload)


# --------------------------------------------------------------------------- #
# Mode detection
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "question, expected",
    [
        ("Are there any upcoming TERI training programmes?", tg.UPCOMING),
        ("What events are scheduled?", tg.UPCOMING),
        ("Any planned workshops?", tg.UPCOMING),
        ("What past training programmes did TERI run?", tg.PAST),
        ("What were TERI's previous centres?", tg.PAST),
        ("Can you provide a brief history of TERI?", tg.PAST),
        ("What are TERI's ongoing projects?", tg.CURRENT),
        ("What climate change projects are currently underway?", tg.CURRENT),
        ("What are the latest publications?", tg.CURRENT),
        ("Who led the project as of 2019?", tg.POINT_IN_TIME),
        ("What happened in 2019?", tg.POINT_IN_TIME),
        ("What did TERI publish between 2019 and 2021?", tg.DATE_RANGE),
        ("What has TERI done since 2015?", tg.DATE_RANGE),
        ("What is TERI's mission?", tg.NONE),
        ("", tg.NONE),
    ],
)
def test_modes_are_distinguished(question, expected):
    assert tg.detect_mode(question) == expected


def test_the_future_of_something_is_not_an_upcoming_query():
    """"the future of X" is a topic, not a temporal scope."""
    assert tg.detect_mode("What is the future of green hydrogen?") != tg.UPCOMING


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
def test_events_already_started_are_dropped():
    kept = tg.gate_upcoming(
        [_event("past", "2015-03-01", n=1), _event("future", "2026-09-18", n=2)],
        reference=date(2026, 8, 19),
    )
    assert [b.payload["document_id"] for b in kept] == ["future"]
    # Numbering is rebuilt so citations stay contiguous after a drop.
    assert [b.n for b in kept] == [1]


def test_only_scheduled_bundles_are_touched():
    """Every document has an `effective_start_date`, so the gate has to be
    scoped by what the date *means*. Without that it would drop most of the
    corpus for any future-tense question: a 2015 news item is not a stale event,
    it is a news item.

    The scope comes from `app.core.corpus.SCHEDULED_BUNDLES`, shared vocabulary
    both paths already agree on, not from a Drupal field name.
    """
    blocks = [
        _block("old-news", bundle="news",
               effective_start_date="2015-03-01T00:00:00+00:00"),
        _event("stale-event", "2015-03-01"),
        _block("old-project", bundle="completed_projects",
               effective_start_date="2010-01-01T00:00:00+00:00",
               effective_end_date="2012-01-01T00:00:00+00:00"),
    ]
    kept = tg.gate_upcoming(blocks, reference=date(2026, 8, 19))
    assert [b.payload["document_id"] for b in kept] == ["old-news", "old-project"]


def test_the_gate_never_empties_the_context():
    """Answering from stale events is bad; answering from nothing is worse.

    With every block stale the context is returned intact, so the generator can
    say that none are upcoming instead of refusing for lack of context.
    """
    blocks = [_event("a", "2014-01-01", n=1), _event("b", "2015-01-01", n=2)]
    kept = tg.gate_upcoming(blocks, reference=date(2026, 8, 19))
    assert len(kept) == 2


def test_an_event_starting_today_still_counts_as_upcoming():
    kept = tg.gate_upcoming([_event("x", "2026-08-19")], reference=date(2026, 8, 19))
    assert len(kept) == 1


def test_a_multi_day_event_survives_until_its_end_date():
    """A conference that began yesterday and runs to Friday is still upcoming in
    every sense the question means. The end date is what decides."""
    running = _event("running", "2026-08-18",
                     effective_end_date="2026-08-22T00:00:00+00:00")
    finished = _event("finished", "2026-08-10",
                      effective_end_date="2026-08-12T00:00:00+00:00")
    kept = tg.gate_upcoming([running, finished], reference=date(2026, 8, 19))
    assert [b.payload["document_id"] for b in kept] == ["running"]


def test_precision_is_respected_rather_than_read_as_a_day():
    """An event the source dated only to a month or a year is not past until
    that month or year is. Reading the stored 1st as the answer would call a
    September event stale on 2 September, which is the same invented day the
    answer layer refuses to render.
    """
    month = _event("month-event", "2026-09-01", start_precision="month")
    year = _event("year-event", "2026-01-01", start_precision="year")
    day = _event("day-event", "2026-09-01")

    # Mid-September: the month-precision event may still be ahead, the
    # day-precision one is not, the year runs to December.
    kept = tg.gate_upcoming([month, year, day], reference=date(2026, 9, 15))
    assert {b.payload["document_id"] for b in kept} == {"month-event", "year-event"}

    # October: the month is over, the year is not.
    kept = tg.gate_upcoming([month, year], reference=date(2026, 10, 1))
    assert [b.payload["document_id"] for b in kept] == ["year-event"]


def test_a_block_without_a_date_is_never_dropped():
    blocks = [_block("no-date", bundle="events"), _event("stale", "2015-01-01")]
    kept = tg.gate_upcoming(blocks, reference=date(2026, 8, 19))
    assert [b.payload["document_id"] for b in kept] == ["no-date"]


def test_an_unparseable_date_leaves_the_block_alone():
    """A malformed value is not evidence that an event has passed."""
    blocks = [_block("broken", bundle="events", effective_start_date="not a date"),
              _event("stale", "2015-01-01")]
    kept = tg.gate_upcoming(blocks, reference=date(2026, 8, 19))
    assert [b.payload["document_id"] for b in kept] == ["broken"]


def test_gate_is_a_no_op_without_a_scheduled_bundle():
    blocks = [_block("a", bundle="page"), _block("b", bundle="news")]
    assert tg.gate_upcoming(blocks, reference=date(2026, 8, 19)) == blocks


def test_the_gate_reads_no_drupal_field_name():
    """The regression this closes. `field_event_start_date` was the last source
    field name on the read path, and it reached MySQL for it."""
    import inspect

    # The module docstring explains the history, so it is excluded; what matters
    # is that no *code* names a source field or reaches for the metadata blob.
    code = inspect.getsource(tg).replace(tg.__doc__ or "", "")
    assert "field_event_start_date" not in code
    assert "raw_meta" not in code
    assert not hasattr(tg, "event_start_dates"), (
        "the MySQL lookup should be gone, not merely unused"
    )
    from app.catalog import state

    assert not hasattr(state, "event_start_dates"), (
        "and so should the catalog reader that existed only for it"
    )


def test_retriever_only_gates_upcoming_questions(monkeypatch):
    """The gate must not fire on a question that is not about the future."""
    from app.retrieval import retriever

    called = []
    monkeypatch.setattr(
        "app.retrieval.search.temporal_gate.gate_upcoming",
        lambda blocks, **kw: called.append(True) or list(blocks),
    )
    blocks = [_block("a")]
    assert retriever._gate_temporal("What is TERI's mission?", blocks) == blocks
    assert not called
    retriever._gate_temporal("Any upcoming training programmes?", blocks)
    assert called == [True]
