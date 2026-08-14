"""Measure mention extraction against a hand-labelled corpus sample.

Precision and recall are reported **per entity type**, never pooled. Pooling
would hide the finding this corpus makes unavoidable: ORGANIZATION and PROJECT
are well grounded in CMS metadata, PERSON is not (the `people` bundle holds 8
nodes against ~975 distinct author strings), so a pooled score would be carried
by the easy types and say nothing about the risky one.

The gold file is a JSON list of chunks, each with the mentions a human expects:

    [{"chunk_id": "...", "document_id": "...", "text": "...",
      "mentions": [{"surface": "ACC Limited", "type": "ORGANIZATION"}]}]

Sampling (`--sample`) writes a *draft* gold file by running the extractor over
real chunks and recording what it found. That is a labelling aid, not a gold
set: scoring against it would be circular, so it is written with
`"reviewed": false` and this script refuses to report until that is corrected.

    python -m scripts.eval_entity_extraction --sample 40   # draft to review
    python -m scripts.eval_entity_extraction               # score the gold set
    python -m scripts.eval_entity_extraction --force       # score a draft anyway
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("eval_entity_extraction")

_REPORT_DIR = Path("reports/knowledge")
# The reviewed set is authoritative; the draft is only a labelling aid that
# --sample writes. Scoring falls back to the draft only so the refusal message
# below can explain why the numbers would be meaningless.
_GOLD = _REPORT_DIR / "gold_mentions_v1.json"
_DRAFT = _REPORT_DIR / "gold_mentions_v1.draft.json"


def _sample_chunks(limit: int) -> list[dict[str, Any]]:
    """Real child chunks from Qdrant, biased toward text likely to carry names."""
    from app.config import get_settings
    from app.core.clients import get_qdrant_client
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_qdrant_client()
    settings = get_settings()
    points, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(
            must=[FieldCondition(key="is_parent", match=MatchValue(value=False))]
        ),
        limit=limit * 12,
        with_payload=["chunk_text", "document_id", "title"],
        with_vectors=False,
    )
    chunks = []
    for point in points:
        payload = point.payload or {}
        text = (payload.get("chunk_text") or "").strip()
        # Skip fragments and boilerplate: a 40-character chunk cannot be
        # meaningfully labelled for recall.
        if len(text) < 300:
            continue
        chunks.append(
            {
                "chunk_id": str(point.id),
                "document_id": payload.get("document_id") or "",
                "title": payload.get("title") or "",
                "text": text,
            }
        )
        if len(chunks) >= limit:
            break
    return chunks


def _write_draft(limit: int) -> int:
    from app.knowledge.extract import extract_mentions
    from app.knowledge.gazetteer import get_gazetteer

    chunks = _sample_chunks(limit)
    if not chunks:
        raise SystemExit("No chunks available to sample.")
    gazetteer = get_gazetteer()
    for chunk in chunks:
        found = extract_mentions(
            chunk["text"], chunk_id=chunk["chunk_id"],
            document_id=chunk["document_id"], gazetteer=gazetteer,
        )
        chunk["mentions"] = [
            {
                "surface": m.surface_text, "type": m.entity_type,
                "start": m.start_offset, "end": m.end_offset,
                "method": m.extraction_method,
            }
            for m in found
        ]
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    _GOLD.write_text(
        json.dumps(
            {
                "version": "v1-draft",
                "reviewed": False,
                "status": (
                    "DRAFT - NOT GOLD. These labels are the extractor's own output "
                    "over real chunks, recorded so a human has something to correct "
                    "rather than a blank file. Scoring against them is circular and "
                    "this script refuses to do it until 'reviewed' is true. Add the "
                    "mentions the extractor MISSED (that is what measures recall) "
                    "and delete the ones it should not have made."
                ),
                "chunks": chunks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    total = sum(len(c["mentions"]) for c in chunks)
    print(f"Wrote {_GOLD}: {len(chunks)} chunks, {total} draft mentions.")
    print("Review it — especially PERSON, where recall is the open question.")
    return 0


def _score(gold: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Per-type precision/recall, matched on (normalized surface, type).

    Matched on the normalized form rather than the exact span: a labeller who
    writes "ACC Limited" should not be counted wrong because the extractor's
    span began one character earlier.
    """
    from app.knowledge.extract import extract_mentions
    from app.knowledge.gazetteer import get_gazetteer
    from app.knowledge.normalize import normalize_for

    gazetteer = get_gazetteer()
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    # Kept alongside the counts because a count says a rule is wrong while an
    # example says *which* rule — and only the second is actionable.
    fp_examples: dict[str, list[str]] = defaultdict(list)
    fn_examples: dict[str, list[str]] = defaultdict(list)

    for chunk in gold["chunks"]:
        expected = {
            (normalize_for(m["type"], m["surface"]), m["type"])
            for m in chunk.get("mentions", [])
        }
        surfaces = {
            (normalize_for(m["type"], m["surface"]), m["type"]): m["surface"]
            for m in chunk.get("mentions", [])
        }
        found_mentions = extract_mentions(
            chunk["text"], chunk_id=chunk["chunk_id"],
            document_id=chunk.get("document_id", ""), gazetteer=gazetteer,
        )
        found_surfaces = {
            (m.normalized_text, m.entity_type): m.surface_text
            for m in found_mentions
        }
        found = set(found_surfaces)
        for key in found - expected:
            fp[key[1]] += 1
            fp_examples[key[1]].append(found_surfaces[key].replace("\n", " "))
        for key in expected - found:
            fn[key[1]] += 1
            fn_examples[key[1]].append(surfaces[key])
        for key in found & expected:
            tp[key[1]] += 1

    out: dict[str, dict[str, float]] = {}
    for entity_type in sorted({*tp, *fp, *fn}):
        t, f, n = tp[entity_type], fp[entity_type], fn[entity_type]
        precision = t / (t + f) if (t + f) else None
        recall = t / (t + n) if (t + n) else None
        out[entity_type] = {
            "tp": t, "fp": f, "fn": n,
            "false_positives": fp_examples[entity_type],
            "false_negatives": fn_examples[entity_type],
            "precision": precision, "recall": recall,
            "f1": (
                2 * precision * recall / (precision + recall)
                if precision and recall
                else None
            ),
        }
    return out


def _fmt(value: float | None) -> str:
    return f"{value:.3f}" if isinstance(value, float) else "    -"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", type=int, help="Write a draft gold file.")
    parser.add_argument(
        "--force", action="store_true",
        help="Score an unreviewed draft anyway. The result is circular.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    if args.sample:
        return _write_draft(args.sample)

    if not _GOLD.exists() and _DRAFT.exists():
        globals()["_GOLD"] = _DRAFT
    if not _GOLD.exists():
        raise SystemExit(
            f"{_GOLD} not found. Run with --sample N to write a draft to review."
        )
    gold = json.loads(_GOLD.read_text(encoding="utf-8"))
    if not gold.get("reviewed") and not args.force:
        raise SystemExit(
            f"{_GOLD} is still marked unreviewed. Its labels are the extractor's "
            "own output, so scoring against them measures nothing. Correct it and "
            "set \"reviewed\": true, or pass --force to see the circular numbers."
        )

    scores = _score(gold)
    chunks = len(gold["chunks"])
    print(f"Chunks: {chunks}   gold reviewed: {bool(gold.get('reviewed'))}")
    print(f"\n  {'type':14} {'P':>7} {'R':>7} {'F1':>7} {'TP':>5} {'FP':>5} {'FN':>5}")
    for entity_type, s in scores.items():
        print(
            f"  {entity_type:14} {_fmt(s['precision']):>7} {_fmt(s['recall']):>7} "
            f"{_fmt(s['f1']):>7} {s['tp']:>5} {s['fp']:>5} {s['fn']:>5}"
        )
    for entity_type, s in scores.items():
        if s["false_positives"]:
            print(f"\n  {entity_type} false positives ({s['fp']}):")
            for surface in sorted(set(s["false_positives"])):
                print(f"    - {surface[:70]}")
        if s["false_negatives"]:
            print(f"\n  {entity_type} false negatives ({s['fn']}):")
            for surface in sorted(set(s["false_negatives"])):
                print(f"    - {surface[:70]}")

    if not gold.get("reviewed"):
        print(
            "\nWARNING: scored against unreviewed labels. Precision is 1.000 by "
            "construction and recall is meaningless. Review the gold file."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
