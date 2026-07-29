"""Unit tests for batched ingestion runs.

Covers the run budget (worked outcomes only, clean stop at a document
boundary so attachments stay with their node), the batch pause, and the
oldest-first crawl flag that makes the high-water mark a resume cursor.
Collaborators are stubbed; no MySQL, Qdrant, or network.
"""

from __future__ import annotations

from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeRecord, ChangeStatus


def _record(doc_id: str, source_type: str = "website") -> ChangeRecord:
    return ChangeRecord(
        status=ChangeStatus.NEW,
        document_id=doc_id,
        source_type=source_type,
        source_key=doc_id,
    )


def _patch_run(monkeypatch, outcomes: dict[str, str], settings) -> list[str]:
    """Stub _run's collaborators; returns the processed-document log."""
    processed: list[str] = []

    def fake_handle(record, build_doc, run_id):
        processed.append(record.document_id)
        return outcomes.get(record.document_id, "indexed")

    monkeypatch.setattr(pipeline.state, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline.ingest_log, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline, "_handle", fake_handle)
    monkeypatch.setattr(pipeline, "get_settings", lambda: settings)
    return processed


class _Settings:
    ingest_max_docs_per_run = 0
    ingest_batch_size = 0
    ingest_batch_pause_seconds = 0.0
    ingest_workers = 1


def test_budget_stops_at_document_boundary(monkeypatch):
    settings = _Settings()
    settings.ingest_max_docs_per_run = 1
    processed = _patch_run(monkeypatch, {}, settings)

    records = [
        _record("node-a"),
        _record("att-a1", source_type="pdf_attachment"),  # belongs to node-a
        _record("att-a2", source_type="pdf_attachment"),
        _record("node-b"),
        _record("node-c"),
    ]
    tally = pipeline._run(iter(records), build_doc=lambda r: None)

    # node-a fills the budget, but its attachments still land in this run;
    # the stop happens at the next document boundary (node-b).
    assert processed == ["node-a", "att-a1", "att-a2"]
    assert tally["budget_stop"] == 1
    assert tally["indexed"] == 3


def test_unchanged_scans_do_not_consume_budget(monkeypatch):
    settings = _Settings()
    settings.ingest_max_docs_per_run = 1
    outcomes = {"old-1": "unchanged", "old-2": "unchanged", "old-3": "unchanged_content"}
    processed = _patch_run(monkeypatch, outcomes, settings)

    records = [_record("old-1"), _record("old-2"), _record("old-3"), _record("new-1")]
    tally = pipeline._run(iter(records), build_doc=lambda r: None)

    # A caught-up capped run must still reach the document that changed.
    assert processed == ["old-1", "old-2", "old-3", "new-1"]
    assert tally["indexed"] == 1 and "budget_stop" not in tally


def test_errors_consume_budget(monkeypatch):
    settings = _Settings()
    settings.ingest_max_docs_per_run = 2
    processed = _patch_run(monkeypatch, {"bad-1": "error", "bad-2": "error"}, settings)

    records = [_record("bad-1"), _record("bad-2"), _record("node-c")]
    tally = pipeline._run(iter(records), build_doc=lambda r: None)

    # Failed documents consumed real work (downloads/extraction attempts);
    # they must not let a crashing corpus loop past the cap.
    assert processed == ["bad-1", "bad-2"]
    assert tally["budget_stop"] == 1


def test_pause_fires_every_batch(monkeypatch):
    settings = _Settings()
    settings.ingest_batch_size = 2
    settings.ingest_batch_pause_seconds = 0.5
    _patch_run(monkeypatch, {}, settings)
    sleeps: list[float] = []
    monkeypatch.setattr(pipeline.time, "sleep", lambda s: sleeps.append(s))

    records = [_record(f"n{i}") for i in range(5)]
    pipeline._run(iter(records), build_doc=lambda r: None)

    assert sleeps == [0.5, 0.5]  # after docs 2 and 4


# --------------------------------------------------------------------------- #
# Parallel mode — one crawler, a pool of document workers.
# --------------------------------------------------------------------------- #

def _patch_parallel(monkeypatch, outcomes, settings):
    processed = _patch_run(monkeypatch, outcomes, settings)
    # The parallel branch pre-creates the collection; not under test here.
    import app.core.clients as deps

    monkeypatch.setattr(deps, "ensure_collection", lambda: None)
    return processed


def test_parallel_run_processes_everything(monkeypatch):
    settings = _Settings()
    settings.ingest_workers = 3
    outcomes = {"old-1": "unchanged", "bad-1": "error"}
    processed = _patch_parallel(monkeypatch, outcomes, settings)

    records = [_record(f"n{i}") for i in range(8)]
    records += [_record("old-1"), _record("bad-1")]
    tally = pipeline._run(iter(records), build_doc=lambda r: None)

    assert sorted(processed) == sorted(r.document_id for r in records)
    assert tally["indexed"] == 8
    assert tally["unchanged"] == 1 and tally["error"] == 1


def test_parallel_worker_exception_becomes_error(monkeypatch):
    settings = _Settings()
    settings.ingest_workers = 2

    def exploding_handle(record, build_doc, run_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(pipeline.state, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline.ingest_log, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline, "_handle", exploding_handle)
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "get_settings", lambda: settings)
    import app.core.clients as deps

    monkeypatch.setattr(deps, "ensure_collection", lambda: None)

    tally = pipeline._run(iter([_record("a"), _record("b")]), build_doc=lambda r: None)
    assert tally["error"] == 2  # exceptions surface as tallied errors, run survives


def test_parallel_budget_never_overshoots(monkeypatch):
    settings = _Settings()
    settings.ingest_workers = 2
    settings.ingest_max_docs_per_run = 1
    processed = _patch_parallel(monkeypatch, {}, settings)

    records = [
        _record("node-a"),
        _record("att-a1", source_type="pdf_attachment"),
        _record("node-b"),
        _record("node-c"),
    ]
    tally = pipeline._run(iter(records), build_doc=lambda r: None)

    # node-a (worked or in flight) fills the budget pessimistically; its
    # attachment still lands in the run, node-b/c never start.
    assert sorted(processed) == ["att-a1", "node-a"]
    assert tally["budget_stop"] == 1


def test_capped_runs_crawl_oldest_first(monkeypatch):
    from app.ingestion.extractors import drupal_extractor as de

    captured: dict = {}

    def fake_iter_pages(session, url, params, timeout):
        captured["sort"] = params.get("sort")
        return iter(())

    monkeypatch.setattr(de, "_iter_pages", fake_iter_pages)
    monkeypatch.setattr(de, "_discover_relationship_fields", lambda *a, **k: [])

    list(de.iter_bundle_records(None, "report", ascending=True))
    assert captured["sort"] == "changed"
    list(de.iter_bundle_records(None, "report"))
    assert captured["sort"] == "-changed"
