"""The graph should follow the corpus — and must never be able to hold it back.

Nothing in ingestion wrote Neo4j: projection existed only as a script someone
ran by hand, so the graph drifted from the moment they stopped. It is now
refreshed at the end of each sweep and its age is reported, but every part of
that is subordinate to one rule: Neo4j is a derived store, and an outage there
costs a log line, never a document.

The projection is deliberately *not* wired into the per-document path — it is a
whole-graph pass over claims, not documents, and a synchronous step inside
`_handle` could not fail without failing the document.

Neo4j is never contacted here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.config import get_settings
from app.ingestion import graph_sync


@pytest.fixture
def knowledge(monkeypatch):
    """Turn the knowledge layer on; return a handle to what the graph answers."""
    import app.core.clients as clients

    settings = get_settings()
    monkeypatch.setattr(settings, "knowledge_enabled", True)
    monkeypatch.setattr(settings, "graph_project_after_sweep", True)
    state = {"reachable": True}
    monkeypatch.setattr(clients, "graph_available", lambda: state["reachable"])
    return state


# --------------------------------------------------------------------------- #
# It cannot break ingestion.
# --------------------------------------------------------------------------- #

def test_a_disabled_knowledge_layer_does_nothing_at_all(monkeypatch):
    """`knowledge_enabled` off means nothing opens a Neo4j connection."""
    import app.core.clients as clients

    monkeypatch.setattr(get_settings(), "knowledge_enabled", False)
    monkeypatch.setattr(
        clients, "graph_available", lambda: pytest.fail("must not touch the graph")
    )

    assert graph_sync.project_after_sweep() is None
    assert graph_sync.freshness() == {"enabled": False}


def test_an_unreachable_graph_is_skipped_not_raised(knowledge, caplog):
    knowledge["reachable"] = False

    with caplog.at_level("WARNING"):
        assert graph_sync.project_after_sweep() is None

    assert "Ingestion is unaffected" in caplog.text


def test_a_projection_that_explodes_does_not_escape(knowledge, monkeypatch, caplog):
    """The sweep's documents are already written and its result already decided
    by the time this runs."""
    import app.knowledge.graph.schema as graph_schema

    monkeypatch.setattr(
        graph_schema, "ensure_graph_schema",
        lambda: (_ for _ in ()).throw(RuntimeError("neo4j fell over")),
    )

    with caplog.at_level("ERROR"):
        assert graph_sync.project_after_sweep() is None

    assert "unaffected" in caplog.text


def test_the_sweep_still_reports_its_ingestion_when_the_graph_is_down(
    knowledge, monkeypatch
):
    """The whole point, at the level that matters: a sweep with a dead graph
    still returns what it ingested.

    `project_after_sweep` reports failure by returning None — the graph really
    is unreachable here — and the sweep's result carries the ingestion and no
    graph section at all.
    """
    from app.workers import tasks

    knowledge["reachable"] = False
    monkeypatch.setattr(tasks, "ingest_drupal", lambda reconcile=False: {"indexed": 3})
    monkeypatch.setattr("app.ingestion.reconcile.reconcile_after_sweep", lambda: None)

    assert tasks.sweep() == {"drupal": {"indexed": 3}}


def test_the_switch_can_be_turned_off(knowledge, monkeypatch):
    monkeypatch.setattr(get_settings(), "graph_project_after_sweep", False)

    assert graph_sync.project_after_sweep() is None


# --------------------------------------------------------------------------- #
# Freshness.
# --------------------------------------------------------------------------- #

def _stamp(age: timedelta) -> str:
    moment = (datetime.now(timezone.utc) - age).strftime("%Y%m%dT%H%M%S")
    return f"graph-project-v1:{moment}:9f2c1a08"


def _freshness_from(version: str | None):
    from app.knowledge.graph.verify import projection_freshness

    class _Session:
        def run(self, statement, **params):
            class _Result:
                def single(self_inner):
                    return {"version": version}

            return _Result()

    return projection_freshness(session=_Session())


def test_the_age_comes_from_the_stamp_the_projection_already_writes():
    """No bookkeeping node: every projected node carries its generation, and the
    timestamp component sorts lexically, so the newest stamp is the maximum."""
    state = _freshness_from(_stamp(timedelta(hours=2)))

    assert state.known
    assert 7100 < state.age_seconds < 7300


def test_a_never_projected_graph_has_an_unknown_age_not_a_zero_one():
    """"Never projected" and "just projected" must not look the same."""
    state = _freshness_from(None)

    assert not state.known and state.age_seconds is None


def test_an_unparseable_stamp_is_reported_without_an_age():
    state = _freshness_from("something-else-entirely")

    assert state.version == "something-else-entirely" and not state.known


def test_staleness_is_measured_against_the_configured_tolerance(knowledge, monkeypatch):
    monkeypatch.setattr(get_settings(), "graph_projection_max_age_seconds", 3600)

    assert graph_sync.is_stale({"age_seconds": 7200}) is True
    assert graph_sync.is_stale({"age_seconds": 600}) is False


@pytest.mark.parametrize(
    "state",
    [{"enabled": False}, {"enabled": True, "reachable": False}, {"enabled": True}],
)
def test_absent_is_not_stale(state):
    """Disabled, unreachable and never-projected are their own conditions,
    reported separately. Staleness means "it ran, and that was too long ago" —
    the one that says the scheduled refresh has stopped."""
    assert graph_sync.is_stale(state) is False


# --------------------------------------------------------------------------- #
# What reconciliation makes of it.
# --------------------------------------------------------------------------- #

def test_a_stale_projection_is_reported_as_drift(knowledge, monkeypatch):
    """Content agreeing is not the same as the projection still running: a graph
    that stopped months ago agrees about everything it was told."""
    from app.ingestion import reconcile as rc
    from app.knowledge.graph.verify import VerificationReport

    monkeypatch.setattr("app.knowledge.graph.verify.verify", lambda: VerificationReport())
    monkeypatch.setattr(
        graph_sync, "freshness",
        lambda: {"enabled": True, "reachable": True, "projected_at": "2026-01-01",
                 "age_seconds": 90 * 86400},
    )
    monkeypatch.setattr(rc, "SAMPLE_LIMIT", 5)

    check = rc._graph_check()

    assert check.count == 1 and not check.ok
    assert "may have stopped" in check.detail


def test_a_current_matching_projection_passes(knowledge, monkeypatch):
    from app.ingestion import reconcile as rc
    from app.knowledge.graph.verify import VerificationReport

    monkeypatch.setattr("app.knowledge.graph.verify.verify", lambda: VerificationReport())
    monkeypatch.setattr(
        graph_sync, "freshness",
        lambda: {"enabled": True, "reachable": True,
                 "projected_at": "2026-08-16", "age_seconds": 600},
    )

    check = rc._graph_check()

    assert check.ok and "current" in check.detail
