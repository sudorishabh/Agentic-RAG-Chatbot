"""Do the stores agree? The check nothing in the codebase did.

85 documents were catalogued as indexed with no retrievable content, and every
signal a human could look at said the system was healthy: green suite, green
/ready, green /metrics. What found them was one scroll of the collection and
three SQL queries — so that is what runs after every sweep now.

Two properties are as important as the checks themselves: this only ever reads,
and an unreachable *optional* store is skipped rather than counted as drift. A
graph outage must not make a healthy corpus look broken.

The stores are fakes; no MySQL, no Qdrant, no Neo4j.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion import reconcile as rc
from app.ingestion.version import PIPELINE_VERSION

OTHER_VERSION = "c0.i0.p0.e0"


def _row(version=1, indexed=True, published_at="2026-01-01", pipeline=PIPELINE_VERSION):
    return rc._Catalogued(
        doc_version=version, indexed=indexed,
        published_at=published_at, pipeline_version=pipeline,
    )


def _point(document_id, *, point_id="p1", version=1, parent=False,
           parent_id=None, published_at="2026-01-01", pipeline=PIPELINE_VERSION,
           chunk_id=None):
    payload = {
        "document_id": document_id, "doc_version": version, "is_parent": parent,
        "published_at": published_at, "pipeline_version": pipeline,
        "chunk_id": chunk_id if chunk_id is not None else point_id,
    }
    if parent_id:
        payload["parent_chunk_id"] = parent_id
    return SimpleNamespace(id=point_id, payload=payload)


@pytest.fixture
def stores(monkeypatch):
    """Install a scripted catalog and collection. Returns the setter."""

    def _scroll(points):
        """The aggregation `_read_collection` performs, over given points."""
        by_document: dict[str, rc._Indexed] = {}
        parent_ids: set[str] = set()
        child_parents: dict[str, str] = {}
        for point in points:
            payload = point.payload
            state = by_document.setdefault(payload["document_id"], rc._Indexed())
            state.points += 1
            if payload.get("doc_version") is not None:
                state.versions.add(int(payload["doc_version"]))
            if not payload.get("published_at"):
                state.undated += 1
            if payload.get("pipeline_version") != PIPELINE_VERSION:
                state.stale_version += 1
            if str(payload.get("chunk_id")) != str(point.id):
                state.id_mismatch += 1
            if payload.get("is_parent"):
                parent_ids.add(str(point.id))
            elif payload.get("parent_chunk_id"):
                child_parents[str(point.id)] = str(payload["parent_chunk_id"])
        return by_document, parent_ids, child_parents

    def setter(catalog: dict, points: list):
        monkeypatch.setattr(rc, "_read_catalog", lambda: catalog)
        monkeypatch.setattr(rc, "_read_collection", lambda batch=1024: _scroll(points))
        # The graph is its own test below.
        monkeypatch.setattr(
            rc, "_graph_check",
            lambda: rc.Check("graph_projection", 0, "not under test", skipped=True),
        )

    return setter


def _named(report, name):
    return next(c for c in report.checks if c.name == name)


# --------------------------------------------------------------------------- #
# A balanced corpus.
# --------------------------------------------------------------------------- #

def test_a_healthy_corpus_reports_no_drift(stores):
    stores(
        {"doc-1": _row()},
        [_point("doc-1", point_id="p1"), _point("doc-1", point_id="p2", parent=True)],
    )

    report = rc.reconcile()

    assert report.ok
    assert report.documents == 1 and report.points == 2
    assert report.drift == []


# --------------------------------------------------------------------------- #
# The defect that started all of this.
# --------------------------------------------------------------------------- #

def test_a_document_indexed_with_no_points_is_drift(stores):
    """The F1 signature: indexed_at stamped, every point deleted."""
    stores({"doc-1": _row(indexed=True)}, [])

    check = _named(rc.reconcile(), "indexed_without_points")

    assert check.count == 1 and check.samples == ["doc-1"]
    assert "clear their content hash" in check.detail.lower()


def test_a_document_that_was_never_indexed_is_not_drift(stores):
    """No indexed_at, no claim to have content. Absence is correct here."""
    stores({"doc-1": _row(indexed=False)}, [])

    assert _named(rc.reconcile(), "indexed_without_points").count == 0


# --------------------------------------------------------------------------- #
# The rest of the invariants.
# --------------------------------------------------------------------------- #

def test_points_with_no_catalog_row_are_drift(stores):
    stores({}, [_point("ghost")])

    check = _named(rc.reconcile(), "points_without_catalog_row")

    assert check.count == 1 and check.samples == ["ghost"]


def test_two_live_versions_for_one_document_are_drift(stores):
    """An interrupted swap: the new version indexed, the old never removed."""
    stores(
        {"doc-1": _row(version=2)},
        [_point("doc-1", point_id="p1", version=1), _point("doc-1", point_id="p2", version=2)],
    )

    assert _named(rc.reconcile(), "duplicate_live_versions").count == 1


def test_points_disagreeing_with_the_catalog_version_are_drift(stores):
    stores({"doc-1": _row(version=5)}, [_point("doc-1", version=4)])

    assert _named(rc.reconcile(), "version_mismatch").count == 1


def test_a_payload_chunk_id_that_is_not_its_point_id_is_drift(stores):
    """Citations resolve by payload, so this cites the wrong chunk."""
    stores({"doc-1": _row()}, [_point("doc-1", point_id="p1", chunk_id="somewhere-else")])

    assert _named(rc.reconcile(), "chunk_id_mismatch").count == 1


def test_a_child_naming_a_missing_parent_is_drift(stores):
    stores({"doc-1": _row()}, [_point("doc-1", point_id="c1", parent_id="gone")])

    assert _named(rc.reconcile(), "children_without_parent").count == 1


def test_a_child_whose_parent_exists_is_fine(stores):
    stores(
        {"doc-1": _row()},
        [
            _point("doc-1", point_id="par", parent=True),
            _point("doc-1", point_id="c1", parent_id="par"),
        ],
    )

    assert _named(rc.reconcile(), "children_without_parent").count == 0


def test_pipeline_drift_is_reported_from_both_sides(stores):
    """The catalog says what a document was built by; the points say what they
    were written by, and a document can be stamped current while old points
    survive beside the new ones."""
    stores(
        {"doc-1": _row(pipeline=OTHER_VERSION), "doc-2": _row()},
        [_point("doc-2", pipeline=OTHER_VERSION)],
    )

    report = rc.reconcile()

    assert _named(report, "catalog_pipeline_drift").count == 1
    assert _named(report, "point_pipeline_drift").count == 1
    assert "reprocess_corpus" in _named(report, "catalog_pipeline_drift").detail


def test_documents_without_a_date_are_reported(stores):
    stores({"doc-1": _row(published_at=None)}, [_point("doc-1")])

    check = _named(rc.reconcile(), "documents_without_date")

    assert check.count == 1
    assert "date filters" in check.detail


def test_every_check_says_what_to_do_about_it(stores):
    """A number with no next step is how drift gets watched rather than fixed."""
    stores({"doc-1": _row()}, [_point("doc-1")])

    for check in rc.reconcile().checks:
        assert check.detail, check.name


# --------------------------------------------------------------------------- #
# Failure semantics.
# --------------------------------------------------------------------------- #

def test_an_unreadable_store_fails_the_report_rather_than_reporting_clean(monkeypatch):
    def boom():
        raise RuntimeError("qdrant is down")

    monkeypatch.setattr(rc, "_read_catalog", dict)
    monkeypatch.setattr(rc, "_read_collection", lambda batch=1024: boom())

    report = rc.reconcile()

    assert report.ok is False
    assert "qdrant is down" in report.error


def test_a_disabled_knowledge_layer_is_skipped_not_failed(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "knowledge_enabled", False)

    check = rc._graph_check()

    assert check.skipped is True and check.ok is True


def test_an_unreachable_graph_is_skipped_not_failed(monkeypatch):
    """Neo4j is a projection that rebuilds from MySQL. Its absence is a degraded
    knowledge layer, never evidence that the corpus is wrong — and must never
    make anything destructive happen."""
    import app.core.clients as clients
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "knowledge_enabled", True)
    monkeypatch.setattr(clients, "graph_available", lambda: False)

    check = rc._graph_check()

    assert check.skipped is True and check.ok is True
    assert "rebuild" in check.detail.lower() or "rebuilds" in check.detail.lower()


def test_a_skipped_check_is_not_counted_as_passing(stores):
    """`ok` is true for a skipped check so a graph outage cannot fail the run,
    but the report says plainly that it did not run."""
    check = rc.Check("graph_projection", 0, "unreachable", skipped=True)

    assert check.ok and check.skipped
    assert check.as_dict()["skipped"] is True


def test_reconciliation_never_writes(stores, monkeypatch):
    """The one behaviour that would turn a wrong reading into data loss."""
    import app.core.clients as clients

    monkeypatch.setattr(
        clients, "delete_document",
        lambda *a, **k: pytest.fail("reconciliation must not delete"),
    )
    stores({"doc-1": _row(indexed=True)}, [])  # maximal drift

    report = rc.reconcile()

    assert not report.ok, "it reports the drift..."
    # ...and the delete stub above proves it did not act on it.


# --------------------------------------------------------------------------- #
# After the sweep.
# --------------------------------------------------------------------------- #

def test_the_sweep_hook_logs_drift_without_failing(stores, monkeypatch, caplog):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "verify_corpus_after_sweep", True)
    stores({"doc-1": _row(indexed=True)}, [])

    with caplog.at_level("WARNING"):
        report = rc.reconcile_after_sweep()

    assert report is not None and not report.ok
    assert "corpus_reconcile ok=false" in caplog.text
    assert "indexed_without_points=1" in caplog.text


def test_the_hook_can_be_turned_off(stores, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "verify_corpus_after_sweep", False)
    stores({"doc-1": _row()}, [])

    assert rc.reconcile_after_sweep() is None


def test_a_failing_reconciliation_does_not_break_the_sweep(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "verify_corpus_after_sweep", True)
    monkeypatch.setattr(rc, "reconcile", lambda: (_ for _ in ()).throw(RuntimeError("x")))

    assert rc.reconcile_after_sweep() is None, "swallowed; the ingest still happened"


def test_the_last_report_is_kept_for_metrics(stores, monkeypatch):
    """A full scroll is far too expensive for a probe, so /metrics reports what
    the last sweep found rather than measuring on demand."""
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "verify_corpus_after_sweep", True)
    stores({"doc-1": _row()}, [_point("doc-1")])

    rc.reconcile_after_sweep()

    assert rc.last_report() is not None and rc.last_report().ok
