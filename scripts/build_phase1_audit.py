"""Human-readable audit of every date change Phase 1 would make.

Produces four artefacts under ``reports/phase1``:

* ``date_overrides.csv``  — only PDFs whose date would actually change
* ``date_overrides.md``   — the same, written out for a person to approve
* ``date_reviews.csv``    — date evidence found but deliberately not applied
* ``edition_labels.csv``  — reporting periods extracted, which are not dates

Every candidate override is **re-verified live** against its PDF using the
production validators before it is allowed into the override list. A candidate
failing any check is moved to the review list, so the override file can be read
as "these and only these would change".

Reporting only. The catalog is opened with SELECT for page URLs; nothing is
written outside ``reports/phase1``. No ``published_at``, document row, Qdrant
point or fingerprint is touched, and Document Intelligence is unreachable —
this module does not import the extraction package.

    python -m scripts.build_phase1_audit
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys

import requests

from app.ingestion.date_evidence import edition_label as extract_edition
from app.ingestion.date_evidence import read_pdf_head
from app.ingestion.date_llm import (
    MIN_OVERRIDE_CONFIDENCE,
    DateInterpretation,
    date_is_in_text,
    statement_is_in_text,
)

logger = logging.getLogger(__name__)

IN_DIR = os.path.join("reports", "phase0")
OUT_DIR = os.path.join("reports", "phase1")
DECISIONS = os.path.join(IN_DIR, "prototype_decisions.csv")
B_CSV = os.path.join(IN_DIR, "phase0b_inbody.csv")
A_CSV = os.path.join(IN_DIR, "phase0a_attachments.csv")
METRICS = os.path.join(IN_DIR, "full_corpus_metrics.json")
SITE = "https://teriin.org"

OVERRIDE_COLUMNS = [
    "document_id", "pdf_filename", "page_url", "pdf_origin", "pdf_count_on_page",
    "current_published_at", "proposed_published_at", "date_type", "confidence",
    "publication_statement", "evidence_location", "date_grounded",
    "statement_grounded", "file_created", "pdf_creation_date", "filename",
    "anchor_text", "edition_label", "decision", "reason",
]
REVIEW_COLUMNS = [
    "document_id", "filename", "current_published_at", "candidate_date",
    "date_type", "confidence", "evidence", "reason_for_review",
]
EDITION_COLUMNS = [
    "document_id", "filename", "current_published_at", "edition_label",
    "evidence", "evidence_location",
]

_NON_PUB = re.compile(
    r"\b(updat|revis|amend|effective|w\.e\.f|notif|came into force|held|"
    r"scheduled|accessed|retrieved|annual report|reporting period)\b", re.I
)


def _d(value) -> str:
    return str(value)[:10] if value else ""


def load_side() -> dict[str, dict]:
    side: dict[str, dict] = {}
    for path in (A_CSV, B_CSV):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = row.get("document_id") or row.get("url") or ""
                if key:
                    side[key] = row
    return side


def load_catalog() -> dict[str, dict]:
    try:
        from app.catalog.db import state_table
        from app.core.clients import mysql_connection

        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT document_id, published_at, url FROM `{state_table()}` "
                "WHERE source_type = 'pdf_attachment'"
            )
            return {r["document_id"]: r for r in cur.fetchall()}
    except Exception:
        logger.warning("Catalog unreadable; page URLs will be blank.", exc_info=True)
        return {}


def verify(row: dict, session: requests.Session) -> tuple[bool, dict, str]:
    """Re-run every gate against the live PDF. Returns (passed, flags, reason)."""
    raw = json.loads(row["llm_raw"]) if row.get("llm_raw") else {}
    quote = (raw.get("publication_statement") or "").strip()
    proposed = _d(row.get("candidate_date"))
    url = row.get("url") or ""
    absolute = url if url.startswith("http") else SITE + url

    head, status = "", "ok"
    try:
        response = session.get(absolute, timeout=180)
        if response.status_code != 200:
            status = f"http_{response.status_code}"
        else:
            head, _title = read_pdf_head(response.content)
    except requests.RequestException as exc:
        status = type(exc).__name__

    verdict = None
    try:
        verdict = DateInterpretation(**{
            k: raw.get(k) for k in
            ("candidate_date", "date_type", "edition_label", "publication_statement",
             "confidence", "evidence", "recommended_action") if raw.get(k) is not None
        })
    except Exception:
        logger.warning("Could not rebuild verdict for %s", row.get("document_id"))

    checks = {
        "1_date_in_pdf": bool(head) and date_is_in_text(proposed, head),
        "2_statement_in_pdf": statement_is_in_text(quote, head),
        "3_statement_carries_date": bool(verdict) and verdict.statement_supports_date(),
        "4_publication_linkage": bool(verdict) and verdict.publication_linkage_ok(),
        "5_not_reconstructed": False,   # set below; needs check 2
        "6_precision_supported": bool(verdict) and verdict.statement_supports_the_day()
                                 and not verdict.statement_is_year_only(),
        "7_not_other_date_kind": (row.get("date_type") == "publication"
                                  and not _NON_PUB.search(quote)),
        "8_confidence": float(row.get("confidence") or 0) >= MIN_OVERRIDE_CONFIDENCE,
    }
    # 5. Reconstruction is the combination of "not in the document" with "looks
    # like the filename/anchor/URL". A statement that IS in the document cannot
    # have been reconstructed, whatever it resembles.
    checks["5_not_reconstructed"] = checks["2_statement_in_pdf"]

    failed = [name for name, ok in checks.items() if not ok]
    reason = "" if not failed else "failed " + ", ".join(failed)
    location = (
        "page 1-2 text (statement verbatim)" if checks["2_statement_in_pdf"]
        else ("page 1-2 text (date only)" if checks["1_date_in_pdf"]
              else (f"unverifiable ({status})" if status != "ok" else "not in text"))
    )
    flags = {
        "checks": checks, "location": location, "quote": quote,
        "head_chars": len(head), "fetch": status,
    }
    return (not failed), flags, reason


def why_publication(row: dict, quote: str) -> str:
    kind = {
        "publication": "the document states its own publication or issue date",
    }.get(row.get("date_type"), row.get("date_type") or "unknown")
    return (f"The document's own text carries the phrase \"{quote}\", which {kind}. "
            "The phrase was found verbatim in the PDF, so it was not inferred from "
            "the filename, the link text, the URL or file metadata.")


def why_replace(row: dict) -> str:
    count = row.get("page_pdf_count") or "1"
    return (
        f"The page this PDF hangs on holds {count} PDF(s), and its own creation date "
        f"({_d(row.get('current_published_at'))}) describes the page, not this "
        "document. Because the document states a publication date itself, that "
        "statement is better evidence than the page's date."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--decisions", default=DECISIONS)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(args.decisions, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    side = load_side()
    catalog = load_catalog()
    metrics = {}
    if os.path.exists(METRICS):
        with open(METRICS, encoding="utf-8") as fh:
            metrics = json.load(fh)

    candidates = [r for r in rows if r["action"] == "propose_override"]
    print(f"re-verifying {len(candidates)} candidate overrides against their PDFs\n")

    overrides: list[dict] = []
    demoted: list[dict] = []
    with requests.Session() as session:
        for row in candidates:
            passed, flags, reason = verify(row, session)
            extra = side.get(row["document_id"], {})
            cat = catalog.get(row["document_id"], {})
            current = _d(cat.get("published_at") or row.get("current_published_at"))
            proposed = _d(row.get("candidate_date"))
            common = {
                "document_id": row["document_id"],
                "pdf_filename": row.get("filename") or "",
                "page_url": cat.get("url") or "",
                "pdf_origin": row.get("origin") or "",
                "pdf_count_on_page": row.get("page_pdf_count") or "",
                "current_published_at": current,
                "proposed_published_at": proposed,
                "date_type": row.get("date_type") or "",
                "confidence": row.get("confidence") or "",
                "publication_statement": flags["quote"],
                "evidence_location": flags["location"],
                "date_grounded": str(flags["checks"]["1_date_in_pdf"]).lower(),
                "statement_grounded": str(flags["checks"]["2_statement_in_pdf"]).lower(),
                "file_created": _d(row.get("file_created")),
                "pdf_creation_date": _d(row.get("pdf_created")),
                "filename": row.get("filename") or "",
                "anchor_text": extra.get("anchor") or "",
                "edition_label": row.get("edition_label") or "",
                "_row": row,
            }
            if passed and current != proposed:
                overrides.append({**common, "decision": "override",
                                  "reason": why_publication(row, flags["quote"])})
                print(f"  KEEP AS OVERRIDE  {current} -> {proposed}  "
                      f"{(row.get('filename') or '')[:44]}")
            else:
                note = reason or "proposed date equals the current date"
                demoted.append({**common, "decision": "review", "reason": note})
                print(f"  DEMOTED TO REVIEW ({note[:44]})  "
                      f"{(row.get('filename') or '')[:40]}")

    # ------------------------------------------------------------- overrides --
    path = os.path.join(OUT_DIR, "date_overrides.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=OVERRIDE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(overrides)

    # --------------------------------------------------------------- reviews --
    reviews: list[dict] = []
    for row in rows:
        if row["action"] != "needs_manual_review":
            continue
        raw = json.loads(row["llm_raw"]) if row.get("llm_raw") else {}
        reviews.append({
            "document_id": row["document_id"],
            "filename": row.get("filename") or "",
            "current_published_at": _d(row.get("current_published_at")),
            "candidate_date": _d(raw.get("candidate_date")),
            "date_type": row.get("date_type") or "",
            "confidence": row.get("confidence") or "",
            "evidence": (raw.get("publication_statement") or raw.get("evidence")
                         or row.get("evidence") or "")[:400],
            "reason_for_review": row.get("rule") or "",
        })
    for item in demoted:
        raw = json.loads(item["_row"]["llm_raw"]) if item["_row"].get("llm_raw") else {}
        reviews.append({
            "document_id": item["document_id"],
            "filename": item["pdf_filename"],
            "current_published_at": item["current_published_at"],
            "candidate_date": item["proposed_published_at"],
            "date_type": item["date_type"],
            "confidence": item["confidence"],
            "evidence": item["publication_statement"][:400],
            "reason_for_review": "demoted during audit: " + item["reason"],
        })
    path = os.path.join(OUT_DIR, "date_reviews.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=REVIEW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(reviews)

    # -------------------------------------------------------------- editions --
    editions: list[dict] = []
    for row in rows:
        label = row.get("edition_label")
        if not label:
            continue
        extra = side.get(row["document_id"], {})
        anchor, filename = extra.get("anchor") or "", row.get("filename") or ""
        if extract_edition(anchor):
            source, evidence = "anchor/link text", anchor
        elif extract_edition(filename):
            source, evidence = "filename", filename
        else:
            source, evidence = "LLM reading of the document", (
                (json.loads(row["llm_raw"]).get("evidence") if row.get("llm_raw") else "") or "")
        editions.append({
            "document_id": row["document_id"],
            "filename": filename,
            "current_published_at": _d(row.get("current_published_at")),
            "edition_label": label,
            "evidence": evidence[:200],
            "evidence_location": source,
        })
    path = os.path.join(OUT_DIR, "edition_labels.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=EDITION_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(editions)

    # ------------------------------------------------------------- markdown ---
    L = ["# Proposed `published_at` changes — for manual approval\n"]
    L.append("Nothing here has been applied. This is the complete list of PDFs whose "
             "date would change if Phase 1 were enabled.\n")
    L.append("## Summary\n")
    L.append("| metric | value |")
    L.append("|---|---:|")
    L.append(f"| total PDFs analysed | {metrics.get('total PDFs', len(rows))} |")
    L.append(f"| **PDFs whose date would change** | **{len(overrides)}** |")
    L.append(f"| PDFs needing review | {len(reviews)} |")
    L.append(f"| edition labels extracted | {len(editions)} |")
    L.append(f"| PDFs sent to the LLM | {metrics.get('PDFs sent to LLM', '-')} |")
    L.append(f"| estimated cost | ${metrics.get('estimated cost USD', 0):.4f} |")
    L.append(f"| PDFs left untouched | "
             f"{metrics.get('total PDFs', len(rows)) - len(overrides)} |")
    L.append("\nEvery override below was re-verified against its live PDF during this "
             "report: the date and the quoted statement were both located in the "
             "document text. Candidates that failed any check were moved to "
             "`date_reviews.csv`.\n")

    L.append("\n## The changes\n")
    if not overrides:
        L.append("_None._")
    for i, o in enumerate(overrides, 1):
        L.append(f"\n### {i}. {o['pdf_filename']}\n")
        L.append(f"- **PDF:** `{o['pdf_filename']}`")
        L.append(f"- **Current date:** {o['current_published_at']}")
        L.append(f"- **Proposed date:** **{o['proposed_published_at']}**")
        L.append(f"- **Date type:** {o['date_type']}")
        L.append(f"- **Confidence:** {o['confidence']}")
        L.append(f"\n**Publication evidence:**\n\n> \"{o['publication_statement']}\"\n")
        L.append(f"**Evidence location:** {o['evidence_location']} "
                 f"(date grounded: {o['date_grounded']}, "
                 f"statement grounded: {o['statement_grounded']})\n")
        L.append(f"**Why the system believes this is a publication date:**  \n{o['reason']}\n")
        L.append(f"**Why the page date is being replaced:**  \n{why_replace(o['_row'])}\n")
        L.append(f"**Context:** page holds {o['pdf_count_on_page']} PDF(s) "
                 f"({o['pdf_origin']}); Drupal file date "
                 f"{o['file_created'] or '(none — in-body link)'}; "
                 f"PDF creation date {o['pdf_creation_date'] or '(unreadable)'}.")
        L.append(f"\n- page: {o['page_url'] or '-'}")
        L.append(f"- pdf: {o['_row'].get('url','')}")

    with open(os.path.join(OUT_DIR, "date_overrides.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"\noverrides: {len(overrides)}   reviews: {len(reviews)}   "
          f"edition labels: {len(editions)}")
    for name in ("date_overrides.csv", "date_overrides.md", "date_reviews.csv",
                 "edition_labels.csv"):
        print(f"wrote {os.path.join(OUT_DIR, name)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
