"""A document that fails must stay reachable by the next run.

The incremental cursor is ``MAX(changed_mark)`` over catalog rows, and a row is
written only on success. A document that errors or is skipped therefore leaves
nothing behind, while every document processed after it raises the mark above
it — so the next run's ``changed >= mark`` filter never returns it again.
Crawling oldest-first does not help: the hole is behind the mark either way.

These tests drive a whole cycle — crawl, process, persist — over a fake Drupal
bundle, then run it again and assert on the ``changed_since`` the second crawl
actually asks for. The catalog, the retry markers, the extractor and the network
are all in memory; no MySQL, no Qdrant, no HTTP.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.catalog.models import StateRecord
from app.ingestion import pipeline
from app.ingestion.change_detection import drupal
from app.ingestion.extractors import drupal_extractor

BUNDLE = "news"
OTHER_BUNDLE = "events"


# --------------------------------------------------------------------------- #
# In-memory stand-ins for the two catalogs a run reads and writes.
# --------------------------------------------------------------------------- #

class _Retries:
    """The retry-marker table, with the one query the crawl makes of it."""

    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def ensure_table(self) -> None:
        pass

    def load(self) -> dict[str, dict]:
        return dict(self.items)

    def floors(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.items.values():
            bundle, mark = item["bundle"], item["changed_mark"]
            if bundle is None or mark is None:
                continue
            out[bundle] = min(out.get(bundle, mark), mark)
        return out

    def record(self, document_id, *, source_type, bundle, changed_mark, outcome, error=None):
        existing = self.items.get(document_id)
        self.items[document_id] = {
            "source_type": source_type,
            "bundle": bundle,
            "changed_mark": changed_mark,
            "outcome": outcome,
            "attempts": (existing["attempts"] + 1) if existing else 1,
        }

    def clear(self, document_ids) -> int:
        return sum(bool(self.items.pop(d, None)) for d in document_ids)


class _Corpus:
    """A Drupal bundle plus the catalog rows runs over it leave behind."""

    def __init__(self) -> None:
        self.nodes: list[SimpleNamespace] = []
        self.rows: dict[str, StateRecord] = {}
        self.retries = _Retries()
        # (bundle, changed_since) per crawl, in order. A run crawls every
        # bundle, so the cursor has to be read per bundle, not per run.
        self.asked_for: list[tuple[str, int | None]] = []

    def add(self, doc_id: str, mark: int, *, bundle: str = BUNDLE, files=()) -> None:
        """``mark`` is the crawl position — seconds since the epoch, which is
        what the cursor compares. Drupal states it as an ISO timestamp, and the
        crawl converts back, so the fixture states it both ways."""
        self.nodes.append(
            SimpleNamespace(
                uuid=doc_id,
                bundle=bundle,
                mark=mark,
                changed=datetime.fromtimestamp(mark, tz=timezone.utc).isoformat(),
                source=f"https://example.org/{doc_id}",
                body="A node with enough body text to survive the block filter.",
                files=list(files),
            )
        )

    def cursor_for(self, bundle: str = BUNDLE) -> int | None:
        """The changed_since the most recent crawl of this bundle asked for."""
        asked = [since for b, since in self.asked_for if b == bundle]
        return asked[-1] if asked else None


def _attachment(uuid: str) -> SimpleNamespace:
    return SimpleNamespace(
        uuid=uuid,
        url=f"https://example.org/{uuid}.pdf",
        filename=f"{uuid}.pdf",
        origin="attachment",
    )


# --------------------------------------------------------------------------- #
# One crawl+process cycle, wired the way ingest_drupal wires it.
# --------------------------------------------------------------------------- #

@pytest.fixture
def corpus(monkeypatch):
    site = _Corpus()

    monkeypatch.setattr(
        drupal, "get_settings",
        lambda: SimpleNamespace(drupal_max_retries=1, drupal_block_min_chars=200),
    )
    monkeypatch.setattr(
        drupal.state, "load",
        lambda source_type: dict(site.rows) if source_type == "website" else {},
    )
    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", dict)
    monkeypatch.setattr(drupal, "retries", site.retries)
    monkeypatch.setattr(pipeline, "retries", site.retries)
    monkeypatch.setattr(drupal_extractor, "_build_session", lambda retries: _Session())

    def iter_bundle_records(session, bundle, *, changed_since=None, **kw):
        """The JSON:API walk, reduced to the filter under test."""
        site.asked_for.append((bundle, changed_since))
        return iter([
            n for n in site.nodes
            if n.bundle == bundle and (changed_since is None or n.mark >= changed_since)
        ])

    monkeypatch.setattr(drupal_extractor, "iter_bundle_records", iter_bundle_records)

    monkeypatch.setattr(pipeline.state, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline.ingest_log, "ensure_table", lambda: None)
    # The audit log is a separate table with its own tests; the raised-error
    # path writes to it, and this module reaches no database.
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    return site


class _Session:
    def close(self) -> None:
        pass


def _settings(workers: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        ingest_max_docs_per_run=0,
        ingest_batch_size=0,
        ingest_batch_pause_seconds=0.0,
        ingest_workers=workers,
        enrichment_enabled=False,
    )


def _run(corpus, monkeypatch, outcomes: dict[str, str], *, workers: int = 1,
         before_outcome=None) -> list[str]:
    """Crawl the bundle and process what comes back; returns the ids reached.

    ``outcomes`` maps a document id to what processing it produces; anything
    unlisted is indexed. A successful outcome writes the catalog row that moves
    the high-water mark, which is what makes the cursor observable next run.
    """
    monkeypatch.setattr(pipeline, "get_settings", lambda: _settings(workers))
    reached: list[str] = []
    lock = threading.Lock()

    # `**_` absorbs `_run`'s optional reporting callbacks (note, fail, flag):
    # this module is about the crawl cursor, not about what a run reports.
    def handle(record, build_doc, run_id, **_):
        with lock:
            reached.append(record.document_id)
        outcome = outcomes.get(record.document_id, "indexed")
        if before_outcome is not None:
            before_outcome(record.document_id)
        if outcome == "raise":
            raise RuntimeError("boom")
        if outcome in ("indexed", "unchanged_content"):
            corpus.rows[record.document_id] = StateRecord(
                document_id=record.document_id,
                source_type=record.source_type,
                source_key=record.source_key,
                fingerprint=record.fingerprint,
                content_hash="hash",
                doc_version=1,
                bundle=record.bundle,
                changed_mark=record.changed_mark,
            )
        return outcome

    monkeypatch.setattr(pipeline, "_handle", handle)
    records = drupal.detect_drupal_changes(bundles=[BUNDLE, OTHER_BUNDLE])
    pipeline._run(records, build_doc=lambda r: None)
    return reached


# --------------------------------------------------------------------------- #
# A clean run: the cursor advances the way it always did.
# --------------------------------------------------------------------------- #

def test_a_clean_run_advances_the_cursor_normally(corpus, monkeypatch):
    corpus.add("n-100", 100)
    corpus.add("n-200", 200)
    corpus.add("n-300", 300)

    _run(corpus, monkeypatch, {})
    assert corpus.retries.load() == {}

    _run(corpus, monkeypatch, {})
    assert corpus.cursor_for() == 300, "a clean run leaves the mark at the newest document"


# --------------------------------------------------------------------------- #
# A failure in the middle holds the cursor at that document.
# --------------------------------------------------------------------------- #

def test_a_middle_failure_keeps_the_cursor_at_that_document(corpus, monkeypatch):
    corpus.add("n-100", 100)
    corpus.add("n-200", 200)
    corpus.add("n-300", 300)

    _run(corpus, monkeypatch, {"n-200": "error"})

    assert corpus.retries.load()["n-200"]["changed_mark"] == 200
    assert "n-200" not in corpus.rows, "a failed document must not be catalogued"

    _run(corpus, monkeypatch, {"n-200": "error"})
    assert corpus.cursor_for() == 200, (
        "the mark reached 300 on the successes, but must be pulled back to the hole"
    )


def test_a_later_success_does_not_lift_the_cursor_over_an_earlier_failure(corpus, monkeypatch):
    corpus.add("n-100", 100)
    corpus.add("n-200", 200)
    corpus.add("n-300", 300)
    _run(corpus, monkeypatch, {"n-200": "error"})

    # A brand new document, newer than everything, indexes cleanly.
    corpus.add("n-400", 400)
    _run(corpus, monkeypatch, {"n-200": "error"})

    assert corpus.rows["n-400"].changed_mark == 400
    _run(corpus, monkeypatch, {"n-200": "error"})
    assert corpus.cursor_for() == 200, "newer successes must not raise the floor"


def test_the_next_run_fetches_the_failed_document_again(corpus, monkeypatch):
    corpus.add("n-100", 100)
    corpus.add("n-200", 200)
    corpus.add("n-300", 300)
    _run(corpus, monkeypatch, {"n-200": "error"})

    reached = _run(corpus, monkeypatch, {"n-200": "error"})

    assert "n-200" in reached, "the failed document must come back without a Drupal edit"
    assert corpus.retries.load()["n-200"]["attempts"] == 2


# --------------------------------------------------------------------------- #
# The floor lifts as soon as the document succeeds.
# --------------------------------------------------------------------------- #

def test_a_successful_retry_lifts_the_floor(corpus, monkeypatch):
    corpus.add("n-100", 100)
    corpus.add("n-200", 200)
    corpus.add("n-300", 300)
    _run(corpus, monkeypatch, {"n-200": "error"})

    _run(corpus, monkeypatch, {})  # this time it works

    assert corpus.retries.load() == {}, "a resolved document keeps no marker"
    _run(corpus, monkeypatch, {})
    assert corpus.cursor_for() == 300, "with the hole filled the cursor advances again"


def test_unchanged_content_also_resolves_a_marker(corpus, monkeypatch):
    """The fingerprint moved but the body did not — the document is settled and
    its catalog row is written, so it is no longer a hole."""
    corpus.add("n-100", 100)
    corpus.add("n-200", 200)
    _run(corpus, monkeypatch, {"n-200": "error"})

    _run(corpus, monkeypatch, {"n-200": "unchanged_content"})

    assert corpus.retries.load() == {}


# --------------------------------------------------------------------------- #
# Several failures, and several bundles.
# --------------------------------------------------------------------------- #

def test_the_floor_is_the_earliest_of_several_failures(corpus, monkeypatch):
    for mark in (100, 200, 300, 400):
        corpus.add(f"n-{mark}", mark)

    _run(corpus, monkeypatch, {"n-200": "error", "n-400": "error"})
    _run(corpus, monkeypatch, {"n-200": "error", "n-400": "error"})

    assert corpus.cursor_for() == 200, "the window must reach the oldest failure"

    # Fix only the oldest. n-400 is still failing, so it still has no catalog
    # row and the high-water mark stays at n-300 — below its floor. The clamp
    # only ever lowers the bound, never raises it to meet a later failure.
    _run(corpus, monkeypatch, {"n-400": "error"})
    reached = _run(corpus, monkeypatch, {"n-400": "error"})

    assert corpus.cursor_for() == 300
    assert "n-400" in reached, "the remaining failure is still inside the window"
    assert set(corpus.retries.load()) == {"n-400"}


def test_a_floor_in_one_bundle_leaves_another_bundle_alone(corpus, monkeypatch):
    corpus.add("n-100", 100)
    corpus.add("n-300", 300)
    corpus.add("e-500", 500, bundle=OTHER_BUNDLE)
    corpus.add("e-700", 700, bundle=OTHER_BUNDLE)

    _run(corpus, monkeypatch, {"n-100": "error"})
    _run(corpus, monkeypatch, {"n-100": "error"})

    assert corpus.cursor_for(BUNDLE) == 100, "the failing bundle is pulled back"
    assert corpus.cursor_for(OTHER_BUNDLE) == 700, "the healthy bundle is untouched"


# --------------------------------------------------------------------------- #
# Skips, which are how an attachment download failure surfaces.
# --------------------------------------------------------------------------- #

def test_a_skipped_attachment_leaves_a_retry_item(corpus, monkeypatch):
    """An attachment carries its parent node's mark, so flooring on it pulls the
    window back to the node — the only thing that can yield the attachment."""
    corpus.add("n-200", 200, files=[_attachment("file-a")])
    corpus.add("n-300", 300)

    _run(corpus, monkeypatch, {"file-a": "skipped"})

    marker = corpus.retries.load()["file-a"]
    assert marker["outcome"] == "skipped"
    assert marker["changed_mark"] == 200, "the parent node's position, not the file's"
    assert marker["bundle"] == BUNDLE

    _run(corpus, monkeypatch, {"file-a": "skipped"})
    assert corpus.cursor_for() == 200

    reached = _run(corpus, monkeypatch, {})
    assert "file-a" in reached and corpus.retries.load() == {}


def test_a_skip_cannot_silently_become_a_permanent_hole(corpus, monkeypatch):
    """Without a marker the node succeeds, the mark advances past it, and the
    attachment is unreachable — its only route back is a re-crawl of the node."""
    corpus.add("n-200", 200, files=[_attachment("file-a")])
    corpus.add("n-900", 900)

    _run(corpus, monkeypatch, {"file-a": "skipped"})
    reached = _run(corpus, monkeypatch, {"file-a": "skipped"})

    assert "n-200" in reached, "the parent must be re-crawled for the skip to be retried"
    assert "file-a" in reached


# --------------------------------------------------------------------------- #
# Workers finishing out of order.
# --------------------------------------------------------------------------- #

def test_out_of_order_worker_completion_still_floors_at_the_failure(corpus, monkeypatch):
    """The floor is a value, not a position, so it does not care which worker
    finished when. Here the earliest document finishes last and by raising."""
    corpus.add("n-200", 200)
    corpus.add("n-400", 400)
    corpus.add("n-600", 600)

    newest_done = threading.Event()
    order: list[str] = []

    def gate(document_id: str) -> None:
        if document_id == "n-200":
            # Hold the oldest until a newer one has already been persisted.
            assert newest_done.wait(timeout=5), "the newer document never finished"
        order.append(document_id)
        if document_id == "n-600":
            newest_done.set()

    _run(corpus, monkeypatch, {"n-200": "raise"}, workers=3, before_outcome=gate)

    assert order.index("n-600") < order.index("n-200"), "completion order was not inverted"
    assert corpus.rows["n-600"].changed_mark == 600
    assert "n-200" not in corpus.rows

    _run(corpus, monkeypatch, {"n-200": "raise"}, workers=3, before_outcome=gate)
    assert corpus.cursor_for() == 200
