"""Backfill ingest-time abstracts over the existing corpus.

The sweep only enriches a document when it re-crawls it, so documents that
never change would never get an abstract. This is the deliberate, budgeted pass
that fills them in.

Kept as its own CLI rather than folded into the sweep on purpose: it is the one
operation here that can spend a lot of money quickly, so it should be something
a human runs with a ``--limit`` and watches, not something a scheduled job
discovers at 2am. For the same reason it ignores ``enrichment_enabled`` — you
may well want to backfill *before* turning the sweep on.

Document text is reconstructed from the vector store rather than re-extracted
from source, following :mod:`app.ingestion.backfill`: no PDF is re-downloaded
and no site is re-crawled. The reconstruction concatenates a document's child
chunks in order, so it approximates ``CanonicalDocument.full_text()`` with some
overlap duplication — close enough for a summary, and it means an abstract
written here is interchangeable with one the sweep would have written for the
same content hash.

Run: python -m app.ingestion.enrich_backfill [--limit N] [--dry-run]
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from app.catalog import enrichment
from app.config import get_settings
from app.core.clients import get_qdrant_client
from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion.enrich import abstract_version, generate_abstract

logger = logging.getLogger(__name__)

# Chunks read per document when reconstructing its text. At ~450 tokens each
# this is far more than any abstract needs; the cap exists so one pathological
# document cannot pull an unbounded scroll into memory.
_MAX_CHUNKS = 2_000
_SCROLL_PAGE = 256


def document_text(document_id: str) -> str:
    """A document's text, rebuilt from its indexed child chunks in order."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    settings = get_settings()
    client = get_qdrant_client()
    scroll_filter = Filter(
        must=[
            FieldCondition(key="document_id", match=MatchValue(value=document_id)),
            FieldCondition(key="is_parent", match=MatchValue(value=False)),
        ]
    )
    payloads: list[dict[str, Any]] = []
    offset: Any = None
    while len(payloads) < _MAX_CHUNKS:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=scroll_filter,
            offset=offset,
            limit=_SCROLL_PAGE,
            with_payload=["chunk_text", "chunk_index"],
            with_vectors=False,
        )
        payloads.extend(p.payload or {} for p in points)
        if offset is None:
            break

    ordered = sorted(payloads, key=lambda p: p.get("chunk_index") or 0)
    return "\n\n".join(str(p.get("chunk_text") or "") for p in ordered).strip()


def _as_document(row: dict[str, Any], text: str) -> CanonicalDocument:
    return CanonicalDocument(
        document_id=row["document_id"],
        source_type=row.get("source_type") or "pdf",
        title=row.get("title"),
        sections=[CanonicalSection(text=text, order=0)],
    )


def backfill(*, limit: int, dry_run: bool = False) -> Counter:
    """Enrich up to ``limit`` documents that have no usable abstract.

    Resumable by construction: the work list is derived from what is missing, so
    an interrupted run simply finds less to do next time. Returns a tally of
    ``{enriched, skipped, failed, no_text, pending}``.
    """
    settings = get_settings()
    enrichment.ensure_table()
    version = abstract_version()
    rows = enrichment.pending(
        version=version, max_attempts=settings.enrichment_max_attempts, limit=limit
    )

    tally: Counter = Counter(pending=len(rows))
    if dry_run:
        return tally

    for row in rows:
        document_id = row["document_id"]
        content_hash = row["content_hash"]
        try:
            text = document_text(document_id)
        except Exception:
            logger.warning("Could not read text for %s; skipping.", document_id, exc_info=True)
            tally["no_text"] += 1
            continue
        if not text:
            logger.info("No indexed text for %s; skipping.", document_id)
            tally["no_text"] += 1
            continue

        try:
            abstract = generate_abstract(_as_document(row, text))
        except Exception as exc:
            logger.warning("Abstract generation failed for %s.", document_id, exc_info=True)
            enrichment.record_failure(content_hash, version=version, error=str(exc))
            tally["failed"] += 1
            continue

        if abstract is None:
            tally["skipped"] += 1
            continue
        enrichment.put(content_hash, version=version, abstract=abstract)
        tally["enriched"] += 1
        logger.info("Enriched %s.", document_id)

    return tally


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(
        description="Generate ingest-time abstracts for documents that lack one."
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="Max documents to enrich in this run (default: 100). This is the "
             "spend control — raise it deliberately.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report how many documents would be enriched, and spend nothing.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    tally = backfill(limit=args.limit, dry_run=args.dry_run)

    if args.dry_run:
        print(f"{tally['pending']} document(s) would be enriched (limit {args.limit}).")
    else:
        print(f"Backfill: {dict(tally)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
