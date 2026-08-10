"""Re-apply the current validation gate to already-stored LLM verdicts.

The gate is deterministic post-processing, so re-scoring the *same* model
outputs isolates a validator change from the model's run-to-run variance —
which re-running the sweep would not. No LLM call is made and no PDF is
downloaded unless ``--locate`` is passed (which fetches only the surviving
overrides, to record where in the document the evidence sits).

Read-only with respect to production: `documents`, Qdrant, fingerprints and
`published_at` are untouched. Rewrites the shadow decisions CSV and, unless
``--no-db`` is given, the shadow decision table.

    python -m scripts.rescore_date_decisions --locate
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from collections import Counter

from app.ingestion.date_llm import DateInterpretation

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
DECISIONS = os.path.join(OUT_DIR, "prototype_decisions.csv")
LOCATIONS = os.path.join(OUT_DIR, "override_evidence_locations.json")
SITE = "https://teriin.org"
_VERDICT_FIELDS = (
    "candidate_date", "date_type", "edition_label", "publication_statement",
    "confidence", "evidence", "recommended_action",
)


def rebuild(raw: dict) -> DateInterpretation | None:
    try:
        return DateInterpretation(**{k: raw.get(k) for k in _VERDICT_FIELDS
                                     if raw.get(k) is not None})
    except Exception:
        logger.warning("Could not rebuild a stored verdict.", exc_info=True)
        return None


def locate_quote(url: str, quote: str) -> str:
    """Which page of the PDF the quoted statement sits on. PyMuPDF only."""
    if not quote or not url:
        return "no quote"
    absolute = url if url.startswith("http") else SITE + url
    try:
        import fitz
        import requests

        response = requests.get(absolute, timeout=180)
        if response.status_code != 200:
            return f"unverified (HTTP {response.status_code})"
        needle = " ".join(quote.split())[:60].lower()
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            for index in range(min(3, doc.page_count)):
                page_text = " ".join((doc[index].get_text("text") or "").split())
                if needle and needle in page_text.lower():
                    return f"page {index + 1} text"
        return "not found in first 3 pages"
    except Exception as exc:
        return f"unverified ({type(exc).__name__})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--locate", action="store_true",
                        help="Fetch surviving overrides to record where the quote sits.")
    parser.add_argument("--no-db", action="store_true", help="Skip shadow-table writes.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    with open(DECISIONS, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())

    before = Counter(r["action"] for r in rows)
    changed: list[tuple[dict, str]] = []

    for row in rows:
        if row["decided_by"] != "llm" or not row.get("llm_raw"):
            continue
        raw = json.loads(row["llm_raw"])
        verdict = rebuild(raw)
        if verdict is None:
            continue
        safe = verdict.safe_action()
        action = ("propose_override" if safe == "override"
                  else "needs_manual_review" if safe == "review" else "keep_page_date")
        if action == row["action"]:
            continue
        was = row["action"]
        row["action"] = action
        if action == "propose_override":
            row["candidate_date"] = verdict.candidate_date
            row["candidate_source"] = "llm_publication"
        else:
            # Anything that is not an override keeps the page's own date.
            row["candidate_date"] = row.get("node_created") or row["current_published_at"]
            row["candidate_source"] = "node_created"
        changed.append((row, was))

    after = Counter(r["action"] for r in rows)
    print(f"re-scored {len(rows)} decisions; {len(changed)} changed\n")
    print(f"{'action':<24}{'before':>8}{'after':>8}")
    for key in sorted(set(before) | set(after)):
        print(f"{key:<24}{before[key]:>8}{after[key]:>8}")

    overrides = [r for r in rows if r["action"] == "propose_override"]
    print(f"\nsurviving overrides: {len(overrides)}")

    locations: dict[str, str] = {}
    if args.locate:
        if os.path.exists(LOCATIONS):
            with open(LOCATIONS, encoding="utf-8") as fh:
                locations = json.load(fh)
        print("\nlocating evidence in each surviving override:")
        for row in overrides:
            key = row["document_id"]
            if key in locations:
                continue
            raw = json.loads(row["llm_raw"]) if row.get("llm_raw") else {}
            locations[key] = locate_quote(row["url"],
                                          raw.get("publication_statement") or "")
            print(f"  {locations[key]:<28} {(row['filename'] or '')[:46]}")
        with open(LOCATIONS, "w", encoding="utf-8") as fh:
            json.dump(locations, fh, ensure_ascii=False, indent=1)
        print(f"\nwrote {LOCATIONS}")

    with open(DECISIONS, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {DECISIONS}")

    if not args.no_db:
        try:
            from app.catalog import date_decisions

            date_decisions.ensure_table()
            for row, _ in changed:
                raw = json.loads(row["llm_raw"]) if row.get("llm_raw") else None
                date_decisions.record(date_decisions.DecisionRow(
                    document_id=row["document_id"], origin=row["origin"],
                    bundle=row["bundle"], node_uuid=row["node_uuid"],
                    page_pdf_count=int(row["page_pdf_count"] or 1),
                    current_published_at=row["current_published_at"],
                    candidate_date=row["candidate_date"], date_type=row["date_type"],
                    edition_label=row["edition_label"] or None,
                    candidate_source=row["candidate_source"],
                    confidence=float(row["confidence"] or 0), action=row["action"],
                    rule=row["rule"], decided_by=row["decided_by"],
                    evidence=row["evidence"], llm_raw=raw,
                    url=row["url"], filename=row["filename"],
                ))
            print(f"updated {len(changed)} shadow rows")
        except Exception:
            logger.warning("Could not update the shadow table.", exc_info=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
