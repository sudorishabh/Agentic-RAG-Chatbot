"""Why did a query answer from an old document instead of the newest one?

Reranking can only reorder what search returned, so "it gave me the 3-year-old
report" has three quite different causes and they need different fixes:

1. **Catalog gap** — the newest edition was never indexed, or carries no
   ``published_at``. Nothing in the query path can fix that.
2. **Recall gap** — its chunks exist but never entered the candidate set, so the
   reranker never saw them. Tuning ranking does nothing; the candidate pull or
   the query text is the problem.
3. **Ranking gap** — its chunks were candidates and lost. Then the band tolerance
   is the dial, and this prints the bands so you can see by how much.

This walks all three in order and names the one that applies. Read-only: it runs
the same query understanding, search and rerank the live path does, and writes
nothing.

Usage:
    python -m scripts.diagnose_recency "what does the annual report say about X"
    python -m scripts.diagnose_recency "..." --title "annual report" --top 20
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

logger = logging.getLogger("diagnose_recency")

_RULE = "─" * 78


def _date(payload: dict[str, Any]) -> str:
    return str(payload.get("published_at") or "—")[:10]


def _title(payload: dict[str, Any]) -> str:
    return str(payload.get("title") or payload.get("document_id") or "?")[:52]


def _catalog_stage(title_contains: str, top: int) -> list[Any]:
    """Stage 1 — what the catalog holds under this title, newest first."""
    from app.catalog.queries import list_documents, published_range

    print(f"\n{_RULE}\n1. CATALOG — documents whose title contains {title_contains!r}\n{_RULE}")
    oldest, newest = published_range()
    print(f"Catalog covers: {oldest or '?'} .. {newest or '?'}"
          + ("   (unknown — the coverage directive stays silent)" if not newest else ""))

    records = list_documents(title_contains=title_contains, limit=top)
    if not records:
        print(f"\n  NOTHING MATCHES {title_contains!r}.")
        print("  Either the title differs from what you searched for, or the")
        print("  document was never ingested. Ranking cannot reach it either way.")
        return []
    print(f"\n  {'published':<12} {'source':<16} title")
    for r in records:
        print(f"  {str(r.published_at or '—')[:10]:<12} {(r.source_type or '?'):<16} "
              f"{(r.title or r.document_id)[:52]}")
    undated = [r for r in records if not r.published_at]
    if undated:
        print(f"\n  {len(undated)} of {len(records)} carry NO published_at — recency")
        print("  cannot rank those at all. For Drupal attachments this comes from the")
        print("  node's `created` date (app/ingestion/extractors/attachment.py).")
    return records


def _chunk_stage(document_id: str) -> None:
    """Stage 2 — do that document's chunks carry the date in their payload?"""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    print(f"\n{_RULE}\n2. CHUNKS — payload of the newest matching document\n{_RULE}")
    settings = get_settings()
    client = get_qdrant_client()
    points, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(must=[
            FieldCondition(key="document_id", match=MatchValue(value=document_id)),
            FieldCondition(key="is_current", match=MatchValue(value=True)),
        ]),
        limit=200,
        with_payload=True,
        with_vectors=False,
    )
    if not points:
        print(f"  NO CHUNKS INDEXED for document_id={document_id!r}.")
        print("  It is in the catalog but not in the vector store — search can never")
        print("  return it. Re-ingest that document.")
        return
    dated = [p for p in points if (p.payload or {}).get("published_at")]
    print(f"  {len(points)} chunks indexed, {len(dated)} carry published_at.")
    if not dated:
        print("\n  The catalog has a date but the CHUNK PAYLOADS DO NOT. The reranker")
        print("  reads payload['published_at'], so recency is inert for this document.")
        print("  Chunks written before the field existed need re-ingesting.")
    else:
        print(f"  Sample: published_at={_date(dated[0].payload)!r}")


def _retrieval_stage(question: str, needle: str, top: int) -> None:
    """Stage 3 — what search returned, and what ranking did with it."""
    from app.config import get_settings
    from app.retrieval import hybrid_search
    from app.retrieval.query_processor import process
    from app.retrieval.reranker import (
        _bands,
        _relevance_tolerance,
        _substance_tolerance,
        rerank,
    )
    from app.retrieval.volatility import is_volatile

    print(f"\n{_RULE}\n3. RETRIEVAL — candidates before and after ranking\n{_RULE}")
    settings = get_settings()
    pq = process(question)
    print(f"  intent={pq.intent}  search_query={pq.search_query!r}")
    dates = [c for c in pq.filters if getattr(c, "key", None) == "published_at"]
    print(f"  date filter: {dates[0].range if dates else 'none (correct for a bare "latest")'}")
    print(f"  volatile topic: {is_volatile(pq.search_query)}  "
          f"relevance band = {_relevance_tolerance(pq.search_query, settings):.3f}  "
          f"substance band = {_substance_tolerance(settings):.3f}")

    candidates = hybrid_search.search(
        pq.search_query, limit=settings.retrieval_candidate_k, extra_filter=pq.filters,
    )
    if not candidates:
        print("\n  SEARCH RETURNED NOTHING. Check the filters above before ranking.")
        return

    hits = [c for c in candidates if needle.lower() in _title(c.payload).lower()]
    print(f"\n  {len(candidates)} candidates pulled; {len(hits)} match {needle!r} by title.")
    if not hits:
        print("\n  RECALL GAP: the document never entered the candidate set, so no")
        print("  ranking change can surface it. Raise retrieval_candidate_k, or check")
        print("  that the query wording matches the document's language.")
        return

    bands = _bands([c.score for c in candidates],
                   tolerance=_relevance_tolerance(pq.search_query, settings))
    by_id = {c.id: b for c, b in zip(candidates, bands)}

    print(f"\n  RAW (by semantic score)   {'band':<5} {'score':<8} {'published':<12} title")
    for c in sorted(candidates, key=lambda c: c.score, reverse=True)[:top]:
        mark = ">>" if needle.lower() in _title(c.payload).lower() else "  "
        print(f"  {mark} {by_id[c.id]:<5} {c.score:<8.4f} {_date(c.payload):<12} {_title(c.payload)}")

    print(f"\n  RANKED (final order)      {'band':<5} {'score':<8} {'published':<12} title")
    for c in rerank(pq.search_query, candidates, top_n=top):
        mark = ">>" if needle.lower() in _title(c.payload).lower() else "  "
        print(f"  {mark} {by_id.get(c.id, '?'):<5} {c.score:<8.4f} {_date(c.payload):<12} {_title(c.payload)}")

    best = min(by_id[c.id] for c in hits)
    top_band = min(bands)
    print()
    if best == top_band:
        print("  Its chunks are in the TOP RELEVANCE BAND, so recency and completeness")
        print("  decide between them. If an older document still leads, compare their")
        print("  published dates and passage lengths in the table above.")
    else:
        gap = max(c.score for c in candidates) - max(c.score for c in hits)
        print(f"  RANKING GAP: its best chunk sits in band {best}, {gap:.4f} below the")
        print(f"  leader, against a band width of "
              f"{_relevance_tolerance(pq.search_query, settings):.3f}. Relevance is")
        print("  ranked above recency by design, so it stays below. Widen")
        print(f"  rerank_relevance_tolerance past {gap:.3f} to let the date decide here.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question", help="The question to trace, as the user would ask it.")
    parser.add_argument(
        "--title", default=None,
        help="Title substring identifying the document series (default: the question).",
    )
    parser.add_argument("--top", type=int, default=15, help="Rows to print per table.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    needle = args.title or args.question

    records = _catalog_stage(needle, args.top)
    if records:
        newest = max(records, key=lambda r: r.published_at or "")
        print(f"\n  Newest under this title: {(newest.title or newest.document_id)[:60]!r} "
              f"({str(newest.published_at or '—')[:10]})")
        _chunk_stage(newest.document_id)
    _retrieval_stage(args.question, needle, args.top)
    print(f"\n{_RULE}\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
