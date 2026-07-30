"""Unit tests for the ingestion pipeline's enrichment step.

Covers the cache hit/miss/skip/failure outcomes, the attempt budget that stops a
hopeless document costing money on every sweep, the fail-open behaviour that
keeps a sweep running when the model or the catalog is unavailable, and the
counters that make the cache's hit rate visible. Catalog and model calls are
stubbed; no MySQL, Qdrant, or network.
"""

from __future__ import annotations

import pytest

from app.catalog.enrichment import Enrichment
from app.config import get_settings
from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion import pipeline

HASH = "c" * 64
VERSION = "test-version"


def _doc() -> CanonicalDocument:
    return CanonicalDocument(
        document_id="doc-1",
        source_type="pdf",
        title="A Report",
        sections=[CanonicalSection(text="Body text of the report.", order=0)],
    )


class _FakeCache:
    """Stands in for app.catalog.enrichment."""

    def __init__(self, row: Enrichment | None = None, get_raises: bool = False):
        self.row = row
        self.get_raises = get_raises
        self.puts: list[tuple[str, str]] = []
        self.failures: list[str] = []

    def get(self, content_hash, *, version):
        if self.get_raises:
            raise RuntimeError("catalog unreachable")
        return self.row

    def put(self, content_hash, *, version, abstract):
        self.puts.append((content_hash, abstract))

    def record_failure(self, content_hash, *, version, error):
        self.failures.append(error)


def _patch(monkeypatch, *, cache=None, generate=None, enabled=True, max_attempts=3):
    base = get_settings()
    monkeypatch.setattr(
        pipeline, "get_settings",
        lambda: base.model_copy(
            update={"enrichment_enabled": enabled, "enrichment_max_attempts": max_attempts}
        ),
    )
    monkeypatch.setattr(pipeline, "abstract_version", lambda: VERSION)
    cache = cache if cache is not None else _FakeCache()
    monkeypatch.setattr(pipeline, "enrichment", cache)
    if generate is not None:
        monkeypatch.setattr(pipeline, "generate_abstract", generate)
    return cache


def _never(doc):
    raise AssertionError("the model must not be called")


# --------------------------------------------------------------------------- #
# The flag.
# --------------------------------------------------------------------------- #

def test_disabled_does_nothing_at_all(monkeypatch):
    cache = _patch(monkeypatch, generate=_never, enabled=False)
    # Not even a cache read: the flag is checked before anything is imported.
    monkeypatch.setattr(
        pipeline, "abstract_version", lambda: pytest.fail("version must not be computed")
    )

    assert pipeline._enrich(_doc(), HASH) == "off"
    assert cache.puts == []


# --------------------------------------------------------------------------- #
# Cache outcomes.
# --------------------------------------------------------------------------- #

def test_a_cached_abstract_is_reused_without_calling_the_model(monkeypatch):
    cache = _patch(
        monkeypatch,
        cache=_FakeCache(Enrichment(HASH, VERSION, abstract="Cached abstract.")),
        generate=_never,
    )

    assert pipeline._enrich(_doc(), HASH) == "hit"
    assert cache.puts == []


def test_a_miss_generates_and_stores(monkeypatch):
    cache = _patch(monkeypatch, generate=lambda doc: "A fresh abstract.")

    assert pipeline._enrich(_doc(), HASH) == "stored"
    assert cache.puts == [(HASH, "A fresh abstract.")]


def test_a_skipped_document_stores_nothing(monkeypatch):
    """Too short to summarize is not a failure — it must not consume the
    attempt budget, and it must not be cached as an empty abstract."""
    cache = _patch(monkeypatch, generate=lambda doc: None)

    assert pipeline._enrich(_doc(), HASH) == "skipped"
    assert cache.puts == []
    assert cache.failures == []


# --------------------------------------------------------------------------- #
# Failure handling and the attempt budget.
# --------------------------------------------------------------------------- #

def test_a_model_failure_is_recorded_not_raised(monkeypatch):
    def boom(doc):
        raise RuntimeError("deployment rate limited")

    cache = _patch(monkeypatch, generate=boom)

    assert pipeline._enrich(_doc(), HASH) == "failed"
    assert cache.failures == ["deployment rate limited"]


def test_the_attempt_budget_stops_a_hopeless_document(monkeypatch):
    cache = _patch(
        monkeypatch,
        cache=_FakeCache(Enrichment(HASH, VERSION, abstract=None, attempts=3)),
        generate=_never,
        max_attempts=3,
    )

    assert pipeline._enrich(_doc(), HASH) == "exhausted"


def test_a_document_under_the_budget_is_retried(monkeypatch):
    cache = _patch(
        monkeypatch,
        cache=_FakeCache(Enrichment(HASH, VERSION, abstract=None, attempts=1)),
        generate=lambda doc: "Second time lucky.",
        max_attempts=3,
    )

    assert pipeline._enrich(_doc(), HASH) == "stored"


def test_an_unreachable_catalog_does_not_stop_the_sweep(monkeypatch):
    _patch(monkeypatch, cache=_FakeCache(get_raises=True), generate=_never)

    assert pipeline._enrich(_doc(), HASH) == "error"


# --------------------------------------------------------------------------- #
# Counters — the hit rate has to be observable.
# --------------------------------------------------------------------------- #

def test_handle_reports_the_enrichment_outcome(monkeypatch):
    monkeypatch.setattr(pipeline, "_save_state", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "chunk_canonical", lambda doc: [])
    monkeypatch.setattr(pipeline, "index_chunks", lambda chunks: 0)
    monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: None)
    monkeypatch.setattr(pipeline, "_enrich", lambda doc, content_hash: "stored")

    from app.ingestion.change_detection import ChangeRecord, ChangeStatus

    record = ChangeRecord(
        status=ChangeStatus.NEW,
        document_id="doc-1",
        source_type="pdf",
        source_key="/tmp/a.pdf",
        fingerprint="f1",
    )
    seen: list[str] = []

    assert pipeline._handle(record, lambda r: _doc(), None, note=seen.append) == "indexed"
    assert seen == ["stored"]


def test_handle_works_without_a_note_callback(monkeypatch):
    """The CLI and tests call _handle directly; counting is opt-in."""
    monkeypatch.setattr(pipeline, "_save_state", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "chunk_canonical", lambda doc: [])
    monkeypatch.setattr(pipeline, "index_chunks", lambda chunks: 0)
    monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: None)
    monkeypatch.setattr(pipeline, "_enrich", lambda doc, content_hash: "stored")

    from app.ingestion.change_detection import ChangeRecord, ChangeStatus

    record = ChangeRecord(
        status=ChangeStatus.NEW,
        document_id="doc-1",
        source_type="pdf",
        source_key="/tmp/a.pdf",
        fingerprint="f1",
    )
    assert pipeline._handle(record, lambda r: _doc()) == "indexed"
