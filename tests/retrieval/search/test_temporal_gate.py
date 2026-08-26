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


def _block(document_id: str, n: int = 1):
    return SimpleNamespace(payload={"document_id": document_id}, n=n)


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
def test_events_already_started_are_dropped(monkeypatch):
    monkeypatch.setattr(
        tg, "event_start_dates",
        lambda ids: {"past": date(2015, 3, 1), "future": date(2026, 9, 18)},
    )
    kept = tg.gate_upcoming(
        [_block("past", 1), _block("future", 2)], reference=date(2026, 8, 19)
    )
    assert [b.payload["document_id"] for b in kept] == ["future"]
    # Numbering is rebuilt so citations stay contiguous after a drop.
    assert [b.n for b in kept] == [1]


def test_documents_without_an_event_date_are_never_touched(monkeypatch):
    """A page, a policy brief or a project has no event date and must survive."""
    monkeypatch.setattr(
        tg, "event_start_dates", lambda ids: {"past-event": date(2015, 3, 1)}
    )
    kept = tg.gate_upcoming(
        [_block("service-page"), _block("past-event"), _block("policy-brief")],
        reference=date(2026, 8, 19),
    )
    assert [b.payload["document_id"] for b in kept] == ["service-page", "policy-brief"]


def test_the_gate_never_empties_the_context(monkeypatch):
    """Answering from stale events is bad; answering from nothing is worse.

    With every block stale the context is returned intact, so the generator can
    say that none are upcoming instead of refusing for lack of context.
    """
    monkeypatch.setattr(
        tg, "event_start_dates",
        lambda ids: {"a": date(2014, 1, 1), "b": date(2015, 1, 1)},
    )
    blocks = [_block("a", 1), _block("b", 2)]
    kept = tg.gate_upcoming(blocks, reference=date(2026, 8, 19))
    assert len(kept) == 2


def test_an_event_starting_today_still_counts_as_upcoming(monkeypatch):
    monkeypatch.setattr(tg, "event_start_dates", lambda ids: {"x": date(2026, 8, 19)})
    kept = tg.gate_upcoming([_block("x")], reference=date(2026, 8, 19))
    assert len(kept) == 1


def test_a_lookup_failure_leaves_the_context_alone(monkeypatch):
    def _boom(ids):
        raise RuntimeError("mysql down")

    monkeypatch.setattr(tg, "event_start_dates", _boom)
    blocks = [_block("a"), _block("b")]
    with pytest.raises(RuntimeError):
        tg.gate_upcoming(blocks, reference=date(2026, 8, 19))


def test_gate_is_a_no_op_without_event_dates(monkeypatch):
    monkeypatch.setattr(tg, "event_start_dates", lambda ids: {})
    blocks = [_block("a"), _block("b")]
    assert tg.gate_upcoming(blocks, reference=date(2026, 8, 19)) == blocks


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
