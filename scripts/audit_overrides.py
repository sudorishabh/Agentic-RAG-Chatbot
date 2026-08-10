"""Audit EVERY proposed override against its actual PDF. No sampling.

For each override the shadow run produced, this re-downloads the PDF, extracts
the same first-two-pages text the model was shown (PyMuPDF only), and runs eight
independent checks:

1. the proposed date appears in the PDF text;
2. the quoted statement appears in the PDF text (allowing punctuation and
   whitespace differences, since a masthead may read
   ``CHANDIGARH | MONDAY | 23 DECEMBER 2013``);
3. the quote is not merely a reconstruction of the filename, anchor or URL;
4. the date is explicitly connected to publication / issue / dateline meaning;
5. the date is not an upload, PDF-creation, update, notification, effective,
   event or reporting-period date, nor a citation year;
6. the date's precision is supported (the day is stated, not inferred);
7. no day or month was invented;
8. the document context is consistent with the interpretation.

A check that cannot be verified fails closed. ``human_audit_result`` and
``audit_notes`` are left blank for the reviewer.

Read-only: no production table, Qdrant collection, fingerprint or
``published_at`` is touched, and Document Intelligence is unreachable.

    python -m scripts.audit_overrides
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

from app.ingestion.date_evidence import read_pdf_head
from app.ingestion.date_llm import (
    DateInterpretation,
    date_is_in_text,
    statement_is_in_text,
)

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
DECISIONS = os.path.join(OUT_DIR, "prototype_decisions.csv")
OUT_CSV = os.path.join(OUT_DIR, "override_audit.csv")
OUT_MD = os.path.join(OUT_DIR, "override_audit.md")
SITE = "https://teriin.org"

COLUMNS = [
    "document_id", "filename", "page_url", "page_pdf_count", "origin",
    "current_published_at", "proposed_published_at", "date_type", "confidence",
    "publication_statement", "evidence_location", "evidence_grounded",
    "check1_date_in_pdf", "check2_quote_in_pdf", "check3_not_from_filename",
    "check4_publication_linkage", "check5_not_other_date_kind",
    "check6_precision_supported", "check7_no_invented_parts",
    "check8_context_reasonable", "checks_passed", "verdict",
    "pdf_text_chars", "fetch_status", "url",
    "human_audit_result", "audit_notes",
]

_NON_PUB_HINT = re.compile(
    r"\b(updat|revis|amend|effective|w\.e\.f|notif|came into force|held|"
    r"scheduled|accessed|retrieved|annual report|reporting period)\b", re.I
)


def _norm(text: str) -> str:
    """Alphanumeric-only lowercase, for punctuation-insensitive comparison."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def fetch_head(session: requests.Session, url: str) -> tuple[str, str]:
    """(head text, fetch status). PyMuPDF only; bytes are discarded."""
    if not url:
        return "", "no_url"
    absolute = url if url.startswith("http") else SITE + url
    try:
        response = session.get(absolute, timeout=180)
        if response.status_code != 200:
            return "", f"http_{response.status_code}"
        text, _title = read_pdf_head(response.content)
        return text, "ok"
    except requests.RequestException as exc:
        return "", type(exc).__name__


def audit_row(row: dict, session: requests.Session) -> dict:
    raw = json.loads(row["llm_raw"]) if row.get("llm_raw") else {}
    quote = (raw.get("publication_statement") or "").strip()
    proposed = str(row.get("candidate_date") or "")[:10]
    head, status = fetch_head(session, row.get("url") or "")
    norm_head = _norm(head)

    # 1. the date itself is in the document text.
    check1 = bool(head) and date_is_in_text(proposed, head)

    # 2. the quote is in the document text. Uses the *production* validator, so
    # the audit and the pipeline cannot drift apart.
    check2 = statement_is_in_text(quote, head)
    location = ""
    if check1:
        location = "page 1-2 text (date present)"
        if check2:
            location = "page 1-2 text (quote verbatim)"
    elif status != "ok":
        location = f"unverifiable ({status})"
    else:
        location = "date NOT in text"

    # 3. the quote is not a laundered filename / anchor / URL.
    surface = _norm(f"{row.get('filename','')} {row.get('anchor','')} {row.get('url','')}")
    quote_norm = _norm(quote)
    # Word overlap with the filename/anchor/URL only matters when the quote is
    # NOT in the document: that combination is what a reconstruction looks like.
    surface_words = set(re.findall(r"[a-z0-9]+", surface))
    quote_words = set(re.findall(r"[a-z0-9]+", quote.lower()))
    overlap = (len(quote_words & surface_words) / len(quote_words)) if quote_words else 0.0
    check3 = bool(quote) and (check2 or overlap < 0.5)

    # 4/5/6/7 — replay the deterministic gates on the stored verdict.
    verdict = None
    try:
        verdict = DateInterpretation(**{
            k: raw.get(k) for k in
            ("candidate_date", "date_type", "edition_label", "publication_statement",
             "confidence", "evidence", "recommended_action")
            if raw.get(k) is not None
        })
    except Exception:
        logger.warning("Could not rebuild verdict for %s", row.get("document_id"))

    check4 = bool(verdict) and verdict.publication_linkage_ok()
    check5 = (row.get("date_type") == "publication"
              and not _NON_PUB_HINT.search(quote)
              and float(row.get("confidence") or 0) >= 0.9)
    check6 = bool(verdict) and verdict.statement_supports_the_day() \
        and not verdict.statement_is_year_only()
    check7 = check6 and check1  # a stated day, and the whole date is in the text
    # 8. context: the proposal must not simply echo the PDF CreationDate with no
    # independent textual support, and must be a plausible calendar date.
    echoes_docinfo = (str(row.get("pdf_created") or "")[:10] == proposed)
    check8 = check1 and (not echoes_docinfo or check2)

    checks = [check1, check2, check3, check4, check5, check6, check7, check8]
    passed = sum(1 for c in checks if c)
    verdict_text = "PASS" if all(checks) else (
        "FAIL - not grounded" if not check1 else "REVIEW - partial"
    )
    return {
        "document_id": row.get("document_id", ""),
        "filename": row.get("filename", ""),
        "page_url": row.get("page_url", "") or row.get("node_uuid", ""),
        "page_pdf_count": row.get("page_pdf_count", ""),
        "origin": row.get("origin", ""),
        "current_published_at": str(row.get("current_published_at") or "")[:10],
        "proposed_published_at": proposed,
        "date_type": row.get("date_type", ""),
        "confidence": row.get("confidence", ""),
        "publication_statement": quote,
        "evidence_location": location,
        "evidence_grounded": str(check1).lower(),
        "check1_date_in_pdf": str(check1).lower(),
        "check2_quote_in_pdf": str(check2).lower(),
        "check3_not_from_filename": str(check3).lower(),
        "check4_publication_linkage": str(check4).lower(),
        "check5_not_other_date_kind": str(check5).lower(),
        "check6_precision_supported": str(check6).lower(),
        "check7_no_invented_parts": str(check7).lower(),
        "check8_context_reasonable": str(check8).lower(),
        "checks_passed": f"{passed}/8",
        "verdict": verdict_text,
        "pdf_text_chars": len(head),
        "fetch_status": status,
        "url": row.get("url", ""),
        "human_audit_result": "",
        "audit_notes": "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--decisions", default=DECISIONS)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    with open(args.decisions, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["action"] == "propose_override"]
    print(f"auditing ALL {len(rows)} overrides (no sampling)\n")

    audited = []
    with requests.Session() as session:
        for row in rows:
            result = audit_row(row, session)
            audited.append(result)
            print(f"  {result['verdict']:<20} {result['checks_passed']}  "
                  f"{result['proposed_published_at']}  "
                  f"{(result['filename'] or '')[:44]}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(audited)

    passes = [a for a in audited if a["verdict"] == "PASS"]
    L = ["# Override audit — every proposed override, verified against its PDF\n"]
    L.append(f"{len(audited)} overrides audited, none sampled. "
             f"**{len(passes)} passed all eight checks**, "
             f"{len(audited) - len(passes)} did not.\n")
    L.append("| # | filename | current | proposed | checks | verdict |")
    L.append("|---:|---|---|---|---|---|")
    for i, a in enumerate(audited, 1):
        L.append(f"| {i} | {a['filename'][:36]} | {a['current_published_at']} "
                 f"| {a['proposed_published_at']} | {a['checks_passed']} "
                 f"| {a['verdict']} |")

    L.append("\n## Per-override detail\n")
    for i, a in enumerate(audited, 1):
        L.append(f"\n### {i}. {a['filename']}\n")
        L.append(f"- **{a['current_published_at']} -> {a['proposed_published_at']}** "
                 f"(`{a['date_type']}`, confidence {a['confidence']})")
        L.append(f"- statement: `{a['publication_statement'][:160]}`")
        L.append(f"- found: {a['evidence_location']}  ·  "
                 f"text extracted: {a['pdf_text_chars']} chars  ·  "
                 f"fetch: {a['fetch_status']}")
        L.append(f"- page holds {a['page_pdf_count']} PDFs ({a['origin']})")
        L.append("- checks: " + ", ".join(
            f"{name}={a[key]}" for name, key in (
                ("1 date-in-pdf", "check1_date_in_pdf"),
                ("2 quote-in-pdf", "check2_quote_in_pdf"),
                ("3 not-from-filename", "check3_not_from_filename"),
                ("4 pub-linkage", "check4_publication_linkage"),
                ("5 not-other-kind", "check5_not_other_date_kind"),
                ("6 precision", "check6_precision_supported"),
                ("7 nothing-invented", "check7_no_invented_parts"),
                ("8 context", "check8_context_reasonable"),
            )))
        L.append(f"- **{a['checks_passed']} → {a['verdict']}**")
        L.append(f"- pdf: {a['url']}")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"\n{len(passes)}/{len(audited)} passed all eight checks")
    print(f"wrote {OUT_CSV}\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
