"""Shadow prototype of evidence-based PDF date resolution.

Runs the full decision tree over the corpus without changing anything:

    page PDF count -> single-PDF default | deterministic multi-PDF rules
                   -> ambiguous only: fetch DocInfo + head text (PyMuPDF)
                   -> still ambiguous: LLM interpretation
                   -> validated, recorded in `{state}_date_decision`

Cost control is structural, not advisory: PDFs are only downloaded for cases the
deterministic rules could not settle, and the LLM is only called for cases that
survive the download. ``--max-llm`` caps the call count for a run.

Read-only with respect to production: `documents`, Qdrant, fingerprints and
`published_at` are never written. Document Intelligence is unreachable — this
module does not import `app.ingestion.extractors.pdf_extractor`.

Usage::

    python -m scripts.shadow_date_prototype --dry-run          # routing only, no network
    python -m scripts.shadow_date_prototype --max-llm 60
    python -m scripts.shadow_date_prototype --nodes <uuid> --max-llm 20
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import requests

from app.ingestion.date_evidence import PageContext, PdfEvidence, read_pdf_head
from app.ingestion.date_llm import interpret, prompt_version
from app.ingestion.date_rules import DateDecision, decide

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
A_CSV = os.path.join(OUT_DIR, "phase0a_attachments.csv")
B_CSV = os.path.join(OUT_DIR, "phase0b_inbody.csv")
OUT_CSV = os.path.join(OUT_DIR, "prototype_decisions.csv")
OUT_MD = os.path.join(OUT_DIR, "prototype_report.md")

SITE = "https://teriin.org"
MAX_BYTES = 30 * 1024 * 1024

# Rough Azure GPT-4o-mini pricing, USD per 1M tokens, for an order-of-magnitude
# estimate only. Override with --price-in/--price-out.
PRICE_IN = 0.15
PRICE_OUT = 0.60


def _rows() -> list[dict]:
    out: list[dict] = []
    for path in (A_CSV, B_CSV):
        with open(path, encoding="utf-8") as fh:
            out += list(csv.DictReader(fh))
    return out


def build_pages(rows: list[dict]) -> dict[str, PageContext]:
    """One PageContext per node, counting PDFs across both origins."""
    per: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        per[row["node_uuid"]].append(row)
    pages: dict[str, PageContext] = {}
    for node_uuid, group in per.items():
        months = {r.get("url_path_month") for r in group if r.get("url_path_month")}
        first = group[0]
        pages[node_uuid] = PageContext(
            node_uuid=node_uuid,
            node_title=first.get("node_title") or "",
            node_created=first.get("node_created") or None,
            bundle=first.get("bundle"),
            pdf_count=len(group),
            distinct_upload_months=max(1, len(months)),
        )
    return pages


def to_evidence(row: dict, page: PageContext) -> PdfEvidence:
    return PdfEvidence(
        document_id=row.get("document_id") or row.get("url") or "",
        origin=row.get("origin") or "attachment",
        url=row.get("url"),
        filename=row.get("filename"),
        anchor=row.get("anchor") or None,
        current_published_at=row.get("current_published_at") or None,
        file_created=row.get("file_created") or None,
        fid=int(row["fid"]) if row.get("fid") else None,
        page=page,
    )


def enrich_from_pdf(session: requests.Session, evidence: PdfEvidence) -> str:
    """Fill DocInfo + head text for one PDF. PyMuPDF only; bytes discarded."""
    url = evidence.url or ""
    absolute = url if url.startswith("http") else SITE + url
    try:
        head = session.head(absolute, timeout=60, allow_redirects=True)
        if head.status_code >= 400:
            return f"http_{head.status_code}"
        if int(head.headers.get("Content-Length") or 0) > MAX_BYTES:
            return "too_large"
        response = session.get(absolute, timeout=180)
        if response.status_code >= 400:
            return f"http_{response.status_code}"
        content = response.content
    except requests.RequestException as exc:
        return type(exc).__name__

    from app.ingestion.date_candidates import read_pdf_docinfo

    created, modified = read_pdf_docinfo(content)
    text, title = read_pdf_head(content)
    evidence.pdf_created = created
    evidence.pdf_modified = modified
    evidence.pdf_title = title
    evidence.head_text = text
    del content
    return "ok"


def _est_tokens(evidence: PdfEvidence) -> int:
    """Crude prompt-size estimate: 4 chars per token."""
    from app.ingestion.date_llm import SYSTEM_PROMPT, build_user_message

    return (len(SYSTEM_PROMPT) + len(build_user_message(evidence))) // 4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-llm", type=int, default=60,
                        help="Cap on LLM calls this run (default: 60).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Route only: no downloads, no LLM, no DB writes.")
    parser.add_argument("--no-db", action="store_true", help="Skip shadow-table writes.")
    parser.add_argument("--nodes", help="Comma-separated node uuids to restrict to.")
    parser.add_argument("--limit", type=int, default=0, help="Cap PDFs examined.")
    parser.add_argument("--price-in", type=float, default=PRICE_IN)
    parser.add_argument("--price-out", type=float, default=PRICE_OUT)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    rows = _rows()
    pages = build_pages(rows)
    if args.nodes:
        wanted = {n.strip() for n in args.nodes.split(",")}
        rows = [r for r in rows if r["node_uuid"] in wanted]
    if args.limit:
        rows = rows[: args.limit]

    version = prompt_version()
    results: list[dict] = []
    llm_calls = 0
    tokens_in = 0
    fetches = Counter()

    session = requests.Session()
    for row in rows:
        page = pages[row["node_uuid"]]
        evidence = to_evidence(row, page)
        decision = decide(evidence)
        llm_raw = None

        fetch_status = ""
        _grounded = None
        if decision.action == "needs_llm" and not args.dry_run:
            status = enrich_from_pdf(session, evidence)
            fetch_status = status
            fetches[status] += 1
            # The download may itself settle the case (no readable evidence at
            # all), so re-run the deterministic tree before paying for a call.
            decision = decide(evidence)
            if decision.action == "needs_llm":
                if llm_calls >= args.max_llm:
                    decision = DateDecision(
                        document_id=evidence.document_id, action="needs_manual_review",
                        candidate_date=page.node_created, date_type="unknown",
                        edition_label=evidence.edition, source="node_created",
                        confidence=0.0, rule="llm_budget_exhausted",
                        evidence="LLM budget for this run was exhausted.",
                        used=["drupal", "pdf_meta"],
                    )
                else:
                    tokens_in += _est_tokens(evidence)
                    verdict = interpret(evidence)
                    llm_calls += 1
                    if verdict is None:
                        decision = DateDecision(
                            document_id=evidence.document_id, action="keep_page_date",
                            candidate_date=page.node_created, date_type="unknown",
                            edition_label=evidence.edition, source="node_created",
                            confidence=0.0, rule="llm_unavailable",
                            evidence="Interpretation call failed; page date kept.",
                            decided_by="llm", used=["drupal", "pdf_meta", "llm"],
                        )
                    else:
                        llm_raw = verdict.model_dump()
                        _grounded = verdict.evidence_grounded
                        action = verdict.safe_action()
                        # Only a quoted, high-confidence publication date moves
                        # anything; review and keep both retain the page date.
                        decision = DateDecision(
                            document_id=evidence.document_id,
                            action=("propose_override" if action == "override"
                                    else "needs_manual_review" if action == "review"
                                    else "keep_page_date"),
                            candidate_date=(verdict.candidate_date if action == "override"
                                            else page.node_created),
                            date_type=verdict.date_type,
                            edition_label=verdict.edition_label or evidence.edition,
                            source=("llm_publication" if action == "override"
                                    else "node_created"),
                            confidence=verdict.confidence,
                            evidence=verdict.evidence,
                            rule="llm_interpreted",
                            decided_by="llm",
                            supporting_evidence=(verdict.publication_statement or ""),
                            used=["drupal", "pdf_meta", "llm"],
                        )

        results.append({
            "document_id": evidence.document_id,
            "origin": evidence.origin,
            "bundle": page.bundle,
            "node_uuid": page.node_uuid,
            "node_title": page.node_title[:60],
            "page_pdf_count": page.pdf_count,
            "filename": evidence.filename,
            "current_published_at": evidence.current_published_at or page.node_created,
            "candidate_date": decision.candidate_date,
            "date_type": decision.date_type,
            "edition_label": decision.edition_label,
            "candidate_source": decision.source,
            "confidence": decision.confidence,
            "action": decision.action,
            "rule": decision.rule,
            "decided_by": decision.decided_by,
            "evidence": decision.evidence,
            "pdf_created": evidence.pdf_created,
            "file_created": evidence.file_created,
            # Recorded from the run so the override audit does not have to guess:
            # how much text the model could actually read, and whether the
            # proposed date was found in it.
            "pdf_text_chars": len(evidence.head_text),
            "publication_statement": (llm_raw or {}).get("publication_statement") or "",
            "evidence_grounded": ("" if llm_raw is None else str(_grounded).lower()),
            "fetch_status": fetch_status,
            "url": evidence.url,
            "llm_raw": json.dumps(llm_raw, ensure_ascii=False) if llm_raw else "",
        })

        if not args.dry_run and not args.no_db:
            try:
                from app.catalog import date_decisions

                date_decisions.ensure_table()
                date_decisions.record(date_decisions.from_decision(
                    decision, origin=evidence.origin, bundle=page.bundle,
                    node_uuid=page.node_uuid, page_pdf_count=page.pdf_count,
                    current_published_at=evidence.current_published_at or page.node_created,
                    url=evidence.url, filename=evidence.filename,
                    llm_raw=llm_raw, prompt_version=version,
                ))
            except Exception:
                logger.warning("Could not record decision for %s.",
                               evidence.document_id, exc_info=True)

    # ------------------------------------------------------------- output --
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    total = len(results)
    by_action = Counter(r["action"] for r in results)
    by_rule = Counter(r["rule"] for r in results)
    by_who = Counter(r["decided_by"] for r in results)
    by_type = Counter(r["date_type"] for r in results)
    moves = [r for r in results if r["action"] == "propose_override"]

    lines = ["# Shadow prototype — evidence-based PDF date resolution\n"]
    lines.append(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. "
                 f"{'DRY RUN (routing only). ' if args.dry_run else ''}"
                 "No production data modified; Document Intelligence not called.\n")
    lines.append(f"- PDFs examined: **{total}**")
    lines.append(f"- handled without the LLM: **{by_who['deterministic']}** "
                 f"({100*by_who['deterministic']/total:.1f}%)")
    lines.append(f"- required the LLM: **{by_who['llm']}** "
                 f"({100*by_who['llm']/total:.1f}%)")
    lines.append(f"- PDFs downloaded (DocInfo/head text only): **{sum(fetches.values())}**")
    lines.append(f"- LLM calls made: **{llm_calls}**")
    if llm_calls:
        out_tokens = llm_calls * 120
        cost = (tokens_in / 1e6) * args.price_in + (out_tokens / 1e6) * args.price_out
        lines.append(f"- estimated prompt tokens: ~{tokens_in:,}; "
                     f"estimated cost this run: **${cost:.4f}** "
                     f"(${args.price_in}/${args.price_out} per 1M in/out)")
        lines.append(f"- extrapolated to all {len(_rows())} corpus PDFs at this "
                     f"LLM rate: **${cost * len(_rows()) / max(total,1):.2f}**")

    for title, counter in (("Action", by_action), ("Decided by", by_who),
                           ("Date type", by_type), ("Rule", by_rule)):
        lines.append(f"\n### {title}\n")
        lines.append("| value | count |")
        lines.append("|---|---:|")
        for key, n in counter.most_common():
            lines.append(f"| `{key}` | {n} |")

    if fetches:
        lines.append("\n### Fetch status (ambiguous cases only)\n")
        lines.append("| status | count |")
        lines.append("|---|---:|")
        for key, n in fetches.most_common():
            lines.append(f"| `{key}` | {n} |")

    llm_rows = [r for r in results if r["decided_by"] == "llm"]
    if llm_rows:
        conf = Counter()
        for r in llm_rows:
            c = float(r["confidence"] or 0)
            conf["0.9-1.0" if c >= 0.9 else "0.8-0.9" if c >= 0.8 else
                 "0.6-0.8" if c >= 0.6 else "<0.6"] += 1
        lines.append("\n### LLM confidence distribution\n")
        lines.append("| band | count |")
        lines.append("|---|---:|")
        for band in ("0.9-1.0", "0.8-0.9", "0.6-0.8", "<0.6"):
            if conf[band]:
                lines.append(f"| {band} | {conf[band]} |")

    lines.append("\n### Proposed overrides\n")
    if moves:
        lines.append("| filename | page PDFs | current | proposed | type | source | conf | rule |")
        lines.append("|---|---:|---|---|---|---|---:|---|")
        for r in moves[:40]:
            lines.append(
                f"| {(r['filename'] or '')[:32]} | {r['page_pdf_count']} "
                f"| {str(r['current_published_at'])[:10]} | {str(r['candidate_date'])[:10]} "
                f"| {r['date_type']} | {r['candidate_source']} | {r['confidence']:.2f} "
                f"| {r['rule']} |")
    else:
        lines.append("_None._")

    review = [r for r in results if r["action"] == "needs_manual_review"]
    lines.append("\n### Flagged for manual review\n")
    if review:
        lines.append("| filename | page PDFs | rule | evidence |")
        lines.append("|---|---:|---|---|")
        for r in review[:25]:
            lines.append(f"| {(r['filename'] or '')[:30]} | {r['page_pdf_count']} "
                         f"| {r['rule']} | {(r['evidence'] or '')[:70]} |")
    else:
        lines.append("_None._")

    editions = [r for r in results if r["edition_label"]]
    lines.append(f"\n### Edition labels derived: {len(editions)}\n")
    if editions:
        lines.append("| filename | edition | date kept |")
        lines.append("|---|---|---|")
        for r in editions[:25]:
            lines.append(f"| {(r['filename'] or '')[:34]} | {r['edition_label']} "
                         f"| {str(r['candidate_date'])[:10]} |")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUT_MD}\nwrote {OUT_CSV}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
