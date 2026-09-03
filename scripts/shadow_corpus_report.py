"""Phase 0A/0B: read-only blast-radius analysis of the PDF date corrections.

Classifies every PDF in the corpus from metadata that is already on hand — the
node's date, the file entity's date, the URL, the filename, the anchor text —
and reports what the proposed corrections would do. Nothing is downloaded and
nothing is written outside ``reports/phase0``.

Read-only by construction:

- the catalog is opened with SELECT only, so no document row, fingerprint or
  ``effective_start_date`` can move;
- Qdrant is never opened;
- the extraction pipeline is never called, so Document Intelligence cannot run;
- no PDF bytes are fetched (that is Phase 0C, ``scripts.shadow_pdf_sample``).

Usage::

    python -m scripts.shadow_corpus_report
    python -m scripts.shadow_corpus_report --refresh      # re-crawl JSON:API metadata

``--refresh`` re-reads the Drupal JSON:API (metadata only, no file bodies) into
``reports/phase0/drupal_metadata.json``; without it the cached crawl is reused.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from app.ingestion.date_candidates import MIGRATION_CUTOFF, resolve

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
METADATA = os.path.join(OUT_DIR, "drupal_metadata.json")

YEAR_RE = re.compile(r"(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)")
MANAGED_RE = re.compile(r"/sites/default/files/(\d{4})-(\d{2})/")
AGREE_DAYS = 1
LATE_DAYS = 365


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #

def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_catalog() -> dict[str, dict]:
    """Indexed pdf_attachment rows, by document_id. SELECT only."""
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, source_key, bundle, effective_start_date, title, url "
            f"FROM `{state_table()}` WHERE source_type = 'pdf_attachment'"
        )
        return {row["document_id"]: row for row in cur.fetchall()}


def load_metadata(refresh: bool) -> list[dict]:
    if refresh or not os.path.exists(METADATA):
        from scripts._crawl_drupal_metadata import crawl

        records = crawl()
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(METADATA, "w", encoding="utf-8") as fh:
            json.dump(records, fh)
        return records
    with open(METADATA, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# classification
# --------------------------------------------------------------------------- #

def classify_attachment(node_dt, file_dt) -> str:
    """The Phase 0A bucket for one file-field attachment.

    Ordered so the *reason a date is untrustworthy* wins over the size of the
    gap: a pre-cutoff file date is an import stamp whatever it looks like, and
    calling it a late upload would propose exactly the wrong correction.
    """
    if node_dt is None or file_dt is None:
        return "insufficient_metadata"
    gap = (file_dt - node_dt).days
    if file_dt < MIGRATION_CUTOFF:
        # Both Drupal dates are suspect here. Split by whether the node still
        # carries its own, older date (then the node is the better source) or
        # was stamped alongside the file (then only the PDF itself can say).
        return "migration_era_node_older" if gap > LATE_DAYS else "migration_era_both_stamped"
    if gap < -AGREE_DAYS:
        return "file_older_than_node"
    if gap > LATE_DAYS:
        return "potential_late_upload"
    if abs(gap) <= AGREE_DAYS:
        return "dates_agree"
    return "minor_gap"


def classify_inbody(url: str, node_dt) -> str:
    host = re.sub(r"^https?://", "", url or "").split("/")[0].lower()
    internal = (not host) or "teriin.org" in host
    if not internal:
        return "external_host"
    if MANAGED_RE.search(url or ""):
        return "managed_path_month"
    if node_dt is None:
        return "insufficient_metadata"
    return "unmanaged_no_file_entity"


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #

def _pct(n: int, total: int) -> str:
    return f"{100 * n / total:.1f}%" if total else "-"


def _table(lines: list[str], title: str, counts: Counter, total: int) -> None:
    lines.append(f"\n### {title}\n")
    lines.append("| category | count | share |")
    lines.append("|---|---:|---:|")
    for key, n in counts.most_common():
        lines.append(f"| `{key}` | {n} | {_pct(n, total)} |")
    lines.append(f"| **total** | **{total}** | |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true",
                        help="Re-crawl Drupal JSON:API metadata (no PDF bodies).")
    parser.add_argument("--examples", type=int, default=6)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # The report carries filenames straight from the corpus, which are not all
    # cp1252-encodable; the file is written UTF-8 either way, this is for stdout.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    os.makedirs(OUT_DIR, exist_ok=True)

    records = load_metadata(args.refresh)
    try:
        catalog = load_catalog()
    except Exception:
        logger.warning("Catalog unreadable; continuing without effective_start_date.", exc_info=True)
        catalog = {}

    # ---------------------------------------------------------- Phase 0A ----
    attachments: list[dict] = []
    for rec in records:
        node_dt = _parse(rec.get("created"))
        for f in rec.get("files") or []:
            if f.get("unresolved"):
                continue
            name = (f.get("filename") or "")
            if f.get("mime") != "application/pdf" and not name.lower().endswith(".pdf"):
                continue
            file_dt = _parse(f.get("created"))
            bucket = classify_attachment(node_dt, file_dt)
            cat = catalog.get(f.get("uuid") or "")
            proposal = resolve(
                document_id=f.get("uuid") or "",
                origin="attachment",
                node_created=rec.get("created"),
                file_created=f.get("created"),
                filename=name,
                url=f.get("url"),
            )
            attachments.append({
                "document_id": f.get("uuid") or "",
                "fid": f.get("fid"),
                "origin": "attachment",
                "bundle": rec.get("bundle"),
                "node_uuid": rec.get("uuid"),
                "node_title": rec.get("title") or "",
                "filename": name,
                "url": f.get("url"),
                "node_created": rec.get("created"),
                "file_created": f.get("created"),
                "gap_days": (file_dt - node_dt).days if (node_dt and file_dt) else None,
                "category": bucket,
                "indexed": bool(cat),
                "current_start_date": (str(cat["effective_start_date"]) if cat and cat.get("effective_start_date") else None),
                "cheap_proposed": proposal.proposed,
                "cheap_rule": proposal.rule,
                "cheap_source": proposal.source,
                "cheap_would_move": proposal.would_move,
                # Only the PDF's own metadata can separate a genuinely old
                # document from one the migration stamped.
                "needs_pdf_metadata": bucket in ("migration_era_both_stamped",
                                                 "migration_era_node_older"),
                "year_in_filename": bool(YEAR_RE.search(name)),
            })

    # ---------------------------------------------------------- Phase 0B ----
    inbody: list[dict] = []
    seen_urls: dict[str, int] = {}
    for rec in records:
        node_dt = _parse(rec.get("created"))
        for link in rec.get("inbody") or []:
            url = link.get("url") or ""
            if url in seen_urls:
                # The same PDF can be linked from several nodes. Keep the first
                # sighting (that is the node ingestion attributes it to) but let
                # a later, richer anchor win — an edition named on one page must
                # not be lost because another page linked the file bare.
                prior = inbody[seen_urls[url]]
                if len((link.get("anchor") or "").strip()) > len(prior["anchor"]):
                    prior["anchor"] = (link.get("anchor") or "").strip()
                    prior["year_in_anchor"] = bool(YEAR_RE.search(prior["anchor"]))
                continue
            seen_urls[url] = len(inbody)
            name = url.split("?")[0].rsplit("/", 1)[-1]
            anchor = (link.get("anchor") or "").strip()
            bucket = classify_inbody(url, node_dt)
            managed = MANAGED_RE.search(url)
            doc_id = None
            for key, row in catalog.items():
                if key.startswith("inbody:") and row.get("source_key") == url:
                    doc_id = key
                    break
            cat = catalog.get(doc_id or "")
            inbody.append({
                "document_id": doc_id or "",
                "origin": "inbody",
                "bundle": rec.get("bundle"),
                "node_uuid": rec.get("uuid"),
                "node_title": rec.get("title") or "",
                "filename": name,
                "url": url,
                "anchor": anchor,
                "node_created": rec.get("created"),
                "url_path_month": f"{managed.group(1)}-{managed.group(2)}" if managed else None,
                "category": bucket,
                "indexed": bool(cat),
                "current_start_date": (str(cat["effective_start_date"]) if cat and cat.get("effective_start_date") else None),
                "year_in_filename": bool(YEAR_RE.search(name)),
                "year_in_anchor": bool(YEAR_RE.search(anchor)),
                "needs_pdf_metadata": bucket in ("unmanaged_no_file_entity", "managed_path_month"),
            })

    # ------------------------------------------------------------- CSVs -----
    a_csv = os.path.join(OUT_DIR, "phase0a_attachments.csv")
    b_csv = os.path.join(OUT_DIR, "phase0b_inbody.csv")
    for path, rows in ((a_csv, attachments), (b_csv, inbody)):
        if not rows:
            continue
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # ----------------------------------------------------------- report -----
    a_counts = Counter(r["category"] for r in attachments)
    b_counts = Counter(r["category"] for r in inbody)
    lines: list[str] = []
    lines.append("# Phase 0A/0B — cheap-metadata blast-radius report\n")
    lines.append(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. "
                 "Read-only: no PDF was downloaded, no extraction ran, "
                 "no production data was modified.\n")
    lines.append(f"- Drupal records scanned: **{len(records)}**")
    lines.append(f"- File-field PDF attachments: **{len(attachments)}**")
    lines.append(f"- Distinct in-body PDF links: **{len(inbody)}**")
    lines.append(f"- Catalog rows joined (`pdf_attachment`): **{len(catalog)}**")

    _table(lines, "Phase 0A — file-field attachments", a_counts, len(attachments))
    _table(lines, "Phase 0B — in-body PDFs", b_counts, len(inbody))

    moves = [r for r in attachments if r["cheap_would_move"]]
    lines.append("\n### What the rules would do on cheap metadata alone\n")
    lines.append(f"- would move: **{len(moves)}** ({_pct(len(moves), len(attachments))})")
    lines.append(f"- needs PDF metadata to decide: "
                 f"**{sum(1 for r in attachments if r['needs_pdf_metadata'])}**")
    for rule, n in Counter(r["cheap_rule"] for r in attachments).most_common():
        lines.append(f"- rule `{rule}`: {n}")

    gaps = sorted(r["gap_days"] for r in attachments if r["gap_days"] is not None)
    if gaps:
        lines.append("\n### Gap distribution (file.created minus node.created, days)\n")
        lines.append("| min | p25 | median | p75 | p90 | max |")
        lines.append("|---:|---:|---:|---:|---:|---:|")
        n = len(gaps)
        lines.append(f"| {gaps[0]} | {gaps[n//4]} | {gaps[n//2]} | {gaps[3*n//4]} "
                     f"| {gaps[9*n//10]} | {gaps[-1]} |")

    lines.append("\n### By bundle\n")
    lines.append("| bundle | attachments | agree | late upload | migration-era | in-body |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    per: dict[str, Counter] = defaultdict(Counter)
    for r in attachments:
        per[r["bundle"]][r["category"]] += 1
        per[r["bundle"]]["_n"] += 1
    for r in inbody:
        per[r["bundle"]]["_inbody"] += 1
    for bundle, c in sorted(per.items(), key=lambda kv: -kv[1]["_n"]):
        lines.append(
            f"| {bundle} | {c['_n']} | {c['dates_agree']} | {c['potential_late_upload']} "
            f"| {c['migration_era_node_older'] + c['migration_era_both_stamped']} "
            f"| {c['_inbody']} |"
        )

    lines.append("\n### Representative examples\n")
    for bucket in sorted(a_counts):
        sample = [r for r in attachments if r["category"] == bucket][: args.examples]
        lines.append(f"\n**{bucket}**\n")
        lines.append("| filename | bundle | node.created | file.created | gap | current effective_start_date |")
        lines.append("|---|---|---|---|---:|---|")
        for r in sample:
            lines.append(
                f"| {r['filename'][:38]} | {r['bundle']} | {str(r['node_created'])[:10]} "
                f"| {str(r['file_created'])[:10]} | {r['gap_days']} "
                f"| {str(r['current_start_date'])[:10]} |"
            )
    for bucket in sorted(b_counts):
        sample = [r for r in inbody if r["category"] == bucket][: args.examples]
        lines.append(f"\n**in-body: {bucket}**\n")
        lines.append("| filename | bundle | node.created | anchor | url month |")
        lines.append("|---|---|---|---|---|")
        for r in sample:
            lines.append(
                f"| {r['filename'][:34]} | {r['bundle']} | {str(r['node_created'])[:10]} "
                f"| {(r['anchor'] or '-')[:28]} | {r['url_path_month'] or '-'} |"
            )

    report = os.path.join(OUT_DIR, "phase0_report.md")
    with open(report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nwrote {report}\nwrote {a_csv}\nwrote {b_csv}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
