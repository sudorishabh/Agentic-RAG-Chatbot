"""Unit tests for the abstract backfill CLI.

Covers text reconstruction from indexed chunks, the per-document outcomes, the
dry-run spend guard, and the limit that is the whole point of running this by
hand. Catalog, Qdrant and model calls are stubbed; no network.
"""

from __future__ import annotations

from app.ingestion import enrich_backfill as bf


class _Point:
    def __init__(self, payload):
        self.payload = payload


class _FakeQdrant:
    """Pages through a fixed chunk list the way client.scroll does."""

    def __init__(self, chunks, page=256):
        self.chunks = chunks
        self.page = page
        self.calls = 0

    def scroll(self, *, offset=None, limit=None, **kw):
        self.calls += 1
        start = offset or 0
        end = start + (limit or self.page)
        window = [_Point(c) for c in self.chunks[start:end]]
        return window, (end if end < len(self.chunks) else None)


def _row(doc_id="d1", content_hash="h1", title="A Report", source_type="pdf"):
    return {
        "document_id": doc_id,
        "content_hash": content_hash,
        "title": title,
        "source_type": source_type,
    }


class _FakeCache:
    def __init__(self, rows):
        self.rows = rows
        self.puts: list[tuple[str, str]] = []
        self.failures: list[tuple[str, str]] = []

    def ensure_table(self):
        pass

    def pending(self, *, version, max_attempts, limit):
        return self.rows[:limit]

    def put(self, content_hash, *, version, abstract):
        self.puts.append((content_hash, abstract))

    def record_failure(self, content_hash, *, version, error):
        self.failures.append((content_hash, error))


def _patch(monkeypatch, rows, *, text="Body text.", generate=None):
    cache = _FakeCache(rows)
    monkeypatch.setattr(bf, "enrichment", cache)
    monkeypatch.setattr(bf, "abstract_version", lambda: "v1")
    monkeypatch.setattr(bf, "document_text", lambda doc_id: text)
    monkeypatch.setattr(
        bf, "generate_abstract", generate or (lambda doc: "An abstract.")
    )
    return cache


# --------------------------------------------------------------------------- #
# Text reconstruction.
# --------------------------------------------------------------------------- #

def test_document_text_orders_chunks_and_pages_through_scroll(monkeypatch):
    chunks = [{"chunk_text": f"part {i}", "chunk_index": i} for i in (2, 0, 3, 1)]
    fake = _FakeQdrant(chunks)
    monkeypatch.setattr(bf, "get_qdrant_client", lambda: fake)
    monkeypatch.setattr(bf, "_SCROLL_PAGE", 2)

    text = bf.document_text("d1")

    # Chunk order is restored across pages, and a long document is paged
    # through rather than silently truncated at one scroll.
    assert text == "part 0\n\npart 1\n\npart 2\n\npart 3"
    assert fake.calls == 2  # both pages read; the second reports exhaustion


def test_document_text_stops_at_the_chunk_cap(monkeypatch):
    """One pathological document must not pull an unbounded scroll into memory."""
    chunks = [{"chunk_text": "x", "chunk_index": i} for i in range(50)]
    monkeypatch.setattr(bf, "get_qdrant_client", lambda: _FakeQdrant(chunks))
    monkeypatch.setattr(bf, "_SCROLL_PAGE", 10)
    monkeypatch.setattr(bf, "_MAX_CHUNKS", 20)

    assert len(bf.document_text("d1").split("\n\n")) == 20


def test_document_text_is_empty_when_nothing_is_indexed(monkeypatch):
    monkeypatch.setattr(bf, "get_qdrant_client", lambda: _FakeQdrant([]))
    assert bf.document_text("d1") == ""


# --------------------------------------------------------------------------- #
# Outcomes.
# --------------------------------------------------------------------------- #

def test_a_pending_document_is_enriched_and_stored(monkeypatch):
    cache = _patch(monkeypatch, [_row()])

    tally = bf.backfill(limit=10)

    assert cache.puts == [("h1", "An abstract.")]
    assert tally["enriched"] == 1


def test_a_document_with_no_indexed_text_is_skipped(monkeypatch):
    cache = _patch(monkeypatch, [_row()], text="")

    tally = bf.backfill(limit=10)

    assert tally["no_text"] == 1
    assert cache.puts == []


def test_a_short_document_is_skipped_without_being_recorded_as_failed(monkeypatch):
    cache = _patch(monkeypatch, [_row()], generate=lambda doc: None)

    tally = bf.backfill(limit=10)

    assert tally["skipped"] == 1
    assert cache.puts == [] and cache.failures == []


def test_a_model_failure_is_recorded_and_the_run_continues(monkeypatch):
    calls: list[str] = []

    def flaky(doc):
        calls.append(doc.document_id)
        if doc.document_id == "d1":
            raise RuntimeError("rate limited")
        return "An abstract."

    cache = _patch(
        monkeypatch, [_row("d1", "h1"), _row("d2", "h2")], generate=flaky
    )

    tally = bf.backfill(limit=10)

    assert calls == ["d1", "d2"]  # one failure does not abort the pass
    assert tally["failed"] == 1 and tally["enriched"] == 1
    assert cache.failures == [("h1", "rate limited")]
    assert cache.puts == [("h2", "An abstract.")]


def test_the_reconstructed_document_carries_its_catalog_title(monkeypatch):
    seen: list[tuple[str, str]] = []
    _patch(
        monkeypatch, [_row(title="Rooftop Solar")],
        generate=lambda doc: seen.append((doc.title, doc.full_text())) or "A.",
    )

    bf.backfill(limit=10)

    assert seen == [("Rooftop Solar", "Body text.")]


# --------------------------------------------------------------------------- #
# Spend controls.
# --------------------------------------------------------------------------- #

def test_dry_run_reports_without_calling_the_model(monkeypatch):
    def never(doc):
        raise AssertionError("dry run must not call the model")

    cache = _patch(monkeypatch, [_row("d1", "h1"), _row("d2", "h2")], generate=never)

    tally = bf.backfill(limit=10, dry_run=True)

    assert tally["pending"] == 2
    assert tally["enriched"] == 0
    assert cache.puts == []


def test_the_limit_caps_the_work(monkeypatch):
    cache = _patch(monkeypatch, [_row(f"d{i}", f"h{i}") for i in range(10)])

    tally = bf.backfill(limit=3)

    assert tally["enriched"] == 3
    assert len(cache.puts) == 3
