"""Phase 0C: validate the date rules on a small, stratified PDF sample.

Downloads a *sample* of the candidates Phase 0A/0B identified and reads only the
PDF's DocInfo header with PyMuPDF, to check whether the proposed corrections
agree with what the document says about itself.

**Document Intelligence is never called.** This module does not import
``app.ingestion.extractors.pdf_extractor``; it uses
``app.ingestion.date_candidates.read_pdf_docinfo``, which opens the bytes with
PyMuPDF, reads the metadata dictionary and closes them. No text extraction, no
OCR, no Azure. Downloaded bytes are held in memory and discarded.

Read-only: the catalog, Qdrant, fingerprints and ``published_at`` are untouched.

Usage::

    python -m scripts.shadow_pdf_sample                 # default stratum sizes
    python -m scripts.shadow_pdf_sample --per-group 50
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone

import requests

from app.ingestion.date_candidates import read_pdf_docinfo, resolve

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
A_CSV = os.path.join(OUT_DIR, "phase0a_attachments.csv")
B_CSV = os.path.join(OUT_DIR, "phase0b_inbody.csv")
SAMPLE_CSV = os.path.join(OUT_DIR, "phase0c_sample.csv")
SAMPLE_MD = os.path.join(OUT_DIR, "phase0c_sample.md")

SITE = "https://teriin.org"
MAX_BYTES = 30 * 1024 * 1024
YEAR_RE = re.compile(r"(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)")

# Strata to validate, in the order they are reported.
GROUPS = (
    "migration_era_both_stamped",
    "migration_era_node_older",
    "potential_late_upload",
    "dates_agree",
    "file_older_than_node",
)


def _years(*texts: str | None) -> set[int]:
    found: set[int] = set()
    for text in texts:
        for match in YEAR_RE.findall(text or ""):
            found.add(int(match))
    return found


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def fetch(session: requests.Session, url: str) -> tuple[bytes | None, str]:
    """The PDF bytes, or (None, reason). Size-capped; nothing is written to disk."""
    if not url:
        return None, "no_url"
    absolute = url if url.startswith("http") else SITE + url
    try:
        head = session.head(absolute, timeout=60, allow_redirects=True)
        if head.status_code >= 400:
            return None, f"http_{head.status_code}"
        size = int(head.headers.get("Content-Length") or 0)
        if size > MAX_BYTES:
            return None, f"too_large_{size}"
        response = session.get(absolute, timeout=180)
        if response.status_code >= 400:
            return None, f"http_{response.status_code}"
        return response.content, "ok"
    except requests.RequestException as exc:
        return None, f"{type(exc).__name__}"


def judge(proposed: str | None, current: str | None, evidence_years: set[int]) -> str:
    """Does independent text evidence back the proposed date?

    The arbiter is a year written into the filename, anchor or node title. It is
    weak — plenty of those years are subject years, not publication years — so a
    document with none is reported as ``no_year_evidence`` rather than counted
    either way.
    """
    if not evidence_years:
        return "no_year_evidence"
    proposed_dt, current_dt = _dt(proposed), _dt(current)
    hit_proposed = proposed_dt is not None and proposed_dt.year in evidence_years
    hit_current = current_dt is not None and current_dt.year in evidence_years
    if hit_proposed and not hit_current:
        return "corroborated"
    if hit_current and not hit_proposed:
        return "contradicted"
    if hit_proposed and hit_current:
        return "both_match"
    return "neither_matches"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-group", type=int, default=40,
                        help="Sample size per attachment stratum (default: 40).")
    parser.add_argument("--inbody", type=int, default=40,
                        help="In-body PDFs to sample (default: 40).")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--groups", help="Comma-separated strata to sample "
                                         "(default: the five in GROUPS).")
    parser.add_argument("--out", default="", help="Suffix for the output files.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    random.seed(args.seed)

    with open(A_CSV, encoding="utf-8") as fh:
        attachments = list(csv.DictReader(fh))
    with open(B_CSV, encoding="utf-8") as fh:
        inbody = list(csv.DictReader(fh))

    groups = tuple(g.strip() for g in args.groups.split(",")) if args.groups else GROUPS
    suffix = args.out
    sample: list[dict] = []
    for group in groups:
        pool = [r for r in attachments if r["category"] == group]
        sample += random.sample(pool, min(args.per_group, len(pool)))

    # In-body: all annual reports (the known accretive page), plus a spread.
    if args.inbody:
        annual = [r for r in inbody
                  if "annual" in (r["filename"] + r["anchor"]).lower() or "TAR_" in r["filename"]]
        others = [r for r in inbody if r not in annual and r["category"] != "external_host"]
        inbody_sample = annual + random.sample(others, min(args.inbody, len(others)))
    else:
        inbody_sample = []

    print(f"Sampling {len(sample)} attachments + {len(inbody_sample)} in-body PDFs "
          f"(DocInfo only, no extraction).\n")

    rows: list[dict] = []
    with requests.Session() as session:
        for record in sample + inbody_sample:
            origin = record["origin"]
            content, status = fetch(session, record["url"])
            pdf_created = pdf_modified = None
            if content:
                pdf_created, pdf_modified = read_pdf_docinfo(content)
            del content  # bytes are not retained

            proposal = resolve(
                document_id=record.get("document_id") or "",
                origin=origin,
                node_created=record.get("node_created") or None,
                file_created=(record.get("file_created") or None),
                pdf_created=pdf_created,
                pdf_modified=pdf_modified,
                filename=record.get("filename"),
                url=record.get("url"),
            )
            evidence = _years(record.get("filename"), record.get("anchor"),
                              record.get("node_title"))
            verdict = judge(proposal.proposed, proposal.current, evidence)
            if status != "ok":
                outcome = "needs_manual_review"
            elif pdf_created is None and proposal.rule == "default":
                outcome = "insufficient_evidence"
            else:
                outcome = proposal.rule

            rows.append({
                "origin": origin,
                "category": record["category"],
                "bundle": record.get("bundle"),
                "filename": record.get("filename"),
                "node_title": (record.get("node_title") or "")[:60],
                "anchor": record.get("anchor", ""),
                "node_created": record.get("node_created"),
                "file_created": record.get("file_created", ""),
                "pdf_created": pdf_created or "",
                "current_published_at": record.get("current_published_at") or "",
                "proposed": proposal.proposed or "",
                "rule": proposal.rule,
                "source": proposal.source,
                "would_move": proposal.would_move,
                "fetch": status,
                "outcome": outcome,
                "trust": verdict,
                "url": record.get("url"),
            })
            print(f"  [{status:>12}] {record['category'][:26]:<27} "
                  f"node={str(record.get('node_created'))[:10]} "
                  f"pdf={str(pdf_created)[:10] or '--':<10} "
                  f"-> {proposal.rule:<16} {verdict:<16} "
                  f"{(record.get('filename') or '')[:34]}")

    with open(SAMPLE_CSV.replace(".csv", f"{suffix}.csv"), "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # --------------------------------------------------------------- report --
    lines = ["# Phase 0C — rule validation on a stratified PDF sample\n"]
    lines.append(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. "
                 f"{len(rows)} PDFs sampled; DocInfo read with PyMuPDF only. "
                 "Document Intelligence was not called. No production data was modified.\n")

    fetched = sum(1 for r in rows if r["fetch"] == "ok")
    lines.append(f"- downloaded successfully: **{fetched}/{len(rows)}**")
    lines.append(f"- DocInfo CreationDate present: "
                 f"**{sum(1 for r in rows if r['pdf_created'])}**")

    for title, key in (("Outcome", "outcome"), ("Trust verdict", "trust"),
                       ("Fetch status", "fetch")):
        lines.append(f"\n### {title}\n")
        lines.append("| value | count |")
        lines.append("|---|---:|")
        for value, n in Counter(r[key] for r in rows).most_common():
            lines.append(f"| `{value}` | {n} |")

    lines.append("\n### Trust verdict by stratum\n")
    lines.append("| stratum | n | corroborated | contradicted | both | neither | no year |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for group in tuple(groups) + ("managed_path_month", "unmanaged_no_file_entity"):
        sub = [r for r in rows if r["category"] == group]
        if not sub:
            continue
        c = Counter(r["trust"] for r in sub)
        lines.append(f"| {group} | {len(sub)} | {c['corroborated']} | {c['contradicted']} "
                     f"| {c['both_match']} | {c['neither_matches']} | {c['no_year_evidence']} |")

    lines.append("\n### Sample detail\n")
    lines.append("| filename | bundle | origin | node.created | file.created | pdf CreationDate "
                 "| current published_at | proposed | rule | trust |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {(r['filename'] or '')[:34]} | {r['bundle']} | {r['origin']} "
            f"| {str(r['node_created'])[:10]} | {str(r['file_created'])[:10]} "
            f"| {str(r['pdf_created'])[:10]} | {str(r['current_published_at'])[:10]} "
            f"| {str(r['proposed'])[:10]} | {r['rule']} | {r['trust']} |"
        )

    with open(SAMPLE_MD.replace(".md", f"{suffix}.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))
    print(f"\nwrote {SAMPLE_MD}\nwrote {SAMPLE_CSV}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
