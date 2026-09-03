"""Build a manual-review pack from the Phase 0 shadow results.

Reads what has already been computed — ``prototype_decisions.csv`` (the
resolver's proposal for every PDF), the Phase 0A/0B metadata, the catalog's
current ``effective_start_date``, and the LLM reachability recheck — and produces a
stratified, reproducible sample for a human to check.

Read-only. Nothing here writes to `documents`, Qdrant, fingerprints or any
ingestion path; the catalog is opened with SELECT only. No PDF is downloaded,
no LLM is called, and Document Intelligence is unreachable (this module does
not import the extraction package).

Usage::

    python -m scripts.build_manual_review
    python -m scripts.build_manual_review --per-group 10 --seed 20260809
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
DECISIONS = os.path.join(OUT_DIR, "prototype_decisions.csv")
A_CSV = os.path.join(OUT_DIR, "phase0a_attachments.csv")
B_CSV = os.path.join(OUT_DIR, "phase0b_inbody.csv")
RECHECK = os.path.join(OUT_DIR, "llm_fetch_recheck.json")
LOCATIONS = os.path.join(OUT_DIR, "override_evidence_locations.json")
GROUNDING = os.path.join(OUT_DIR, "override_grounding_audit.json")
OUT_CSV = os.path.join(OUT_DIR, "date_resolution_manual_review.csv")
OUT_MD = os.path.join(OUT_DIR, "date_resolution_manual_review.md")

MIGRATION_END = datetime(2018, 6, 1, tzinfo=timezone.utc)

# Left blank on purpose — these are the reviewer's to fill in.
HUMAN_COLUMNS = [
    "human_decision", "human_correct", "human_effective_start_date",
    "human_date_type", "human_edition_label", "human_notes",
]

CSV_COLUMNS = [
    "review_group", "document_id", "page_url", "page_title", "page_pdf_count",
    "origin", "bundle", "filename", "anchor_text",
    "node_created", "file_created", "pdf_creation_date", "current_start_date",
    "proposed_effective_start_date", "action", "date_type", "date_source",
    "deterministic_rule", "llm_used", "llm_confidence", "llm_evidence",
    "edition_label", "publication_statement", "evidence_location",
    "evidence_grounded", "pdf_available_to_llm", "pdf_url_reachable_now",
    "why", "url",
] + HUMAN_COLUMNS


def _dt(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _d(value) -> str:
    return str(value)[:10] if value else ""


def load_side_metadata() -> dict[str, dict]:
    """Anchor text and node/file dates keyed by document_id, from Phase 0A/0B."""
    side: dict[str, dict] = {}
    for path in (A_CSV, B_CSV):
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = row.get("document_id") or row.get("url") or ""
                if key:
                    side[key] = row
    return side


def load_catalog() -> dict[str, dict]:
    """Current effective_start_date and page URL per document. SELECT only."""
    try:
        from app.catalog.db import state_table
        from app.core.clients import mysql_connection

        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT document_id, effective_start_date, url, title FROM `{state_table()}` "
                "WHERE source_type = 'pdf_attachment'"
            )
            return {r["document_id"]: r for r in cur.fetchall()}
    except Exception:
        logger.warning("Catalog unreadable; page URLs will be blank.", exc_info=True)
        return {}


def why_sentence(row: dict) -> str:
    """A plain-language justification a reviewer can check without the code."""
    node, file_c = row["node_created"], row["file_created"]
    pdf_c = row["pdf_creation_date"]
    bits = [f"page created {node or 'unknown'}"]
    bits.append(f"file uploaded to Drupal {file_c}" if file_c
                else "no Drupal file record (in-body link)")
    bits.append(f"PDF internally created {pdf_c}" if pdf_c
                else "PDF creation date unreadable")
    bits.append(f"{row['page_pdf_count']} PDF(s) on this page")

    explain = {
        "single_pdf_page":
            "Only one PDF on the page, so it is treated as part of the page's own "
            "publication. A different PDF creation date does NOT override this.",
        "single_pdf_late_upload_review":
            "Only one PDF, but Drupal logged the upload more than a year after the "
            "page. Upload timing alone cannot set a date, so the document was "
            "checked for an explicit publication statement.",
        "multi_pdf_late_upload_review":
            "Several PDFs on the page and this one was uploaded well after it. "
            "That is a reason to LOOK for a publication date, not a date itself.",
        "multi_pdf_uploaded_with_page":
            "Several PDFs, but this one was uploaded alongside the page.",
        "multi_pdf_url_month_review":
            "In-body PDF whose managed URL path shows it stored well after the "
            "page; checked for an explicit publication statement.",
        "multi_pdf_url_month_matches":
            "In-body PDF whose URL path month is close to the page date.",
        "migration_cohort_no_evidence":
            "File date falls in the 2017-2018 migration import, so it records the "
            "import rather than an upload; nothing better is available.",
        "migration_cohort_review":
            "File date is a migration import, so only the document's own content "
            "could date it.",
        "multi_pdf_no_evidence":
            "Several PDFs but no per-document evidence of any kind.",
        "llm_interpreted":
            "Deterministic rules cannot propose a change, so the evidence was sent "
            "to the LLM to look for an explicit publication statement.",
    }.get(row["deterministic_rule"], "")
    text = "; ".join(bits) + ". " + explain
    if row["llm_used"] == "yes" and row["llm_evidence"]:
        text += f" LLM: {row['llm_evidence']}"
    return text.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-group", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260809,
                        help="Fixed so the sample is reproducible.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    random.seed(args.seed)

    with open(DECISIONS, encoding="utf-8") as fh:
        decisions = list(csv.DictReader(fh))
    side = load_side_metadata()
    catalog = load_catalog()
    recheck: dict[str, str] = {}
    if os.path.exists(RECHECK):
        with open(RECHECK, encoding="utf-8") as fh:
            recheck = json.load(fh)
    # Where each surviving override's quote sits in its PDF, and whether the
    # proposed date was actually found in the document text.
    locations: dict[str, str] = {}
    if os.path.exists(LOCATIONS):
        with open(LOCATIONS, encoding="utf-8") as fh:
            locations = json.load(fh)
    grounding: dict[str, dict] = {}
    if os.path.exists(GROUNDING):
        with open(GROUNDING, encoding="utf-8") as fh:
            grounding = json.load(fh)

    # Per-page fact used for stratification: does this page's set of PDFs span
    # more than one upload year? That is the accretive signature.
    per_node: dict[str, list[dict]] = defaultdict(list)
    for row in decisions:
        per_node[row["node_uuid"]].append(row)
    node_span_years = {
        node: len({_dt(r["file_created"]).year for r in group if _dt(r["file_created"])})
        for node, group in per_node.items()
    }

    def enrich(row: dict, group_name: str) -> dict:
        extra = side.get(row["document_id"], {})
        cat = catalog.get(row["document_id"], {})
        llm_raw = {}
        if row.get("llm_raw"):
            try:
                llm_raw = json.loads(row["llm_raw"])
            except (ValueError, TypeError):
                llm_raw = {}
        used_llm = row["decided_by"] == "llm"
        # The PDF was demonstrably in front of the model only if its DocInfo was
        # parsed during the run. A fetch that succeeded but yielded no DocInfo is
        # counted conservatively as unavailable.
        available = "true" if row.get("pdf_created") else "false"
        out = {
            "review_group": group_name,
            "document_id": row["document_id"],
            "page_url": cat.get("url") or "",
            "page_title": row.get("node_title") or "",
            "page_pdf_count": row.get("page_pdf_count") or "",
            "origin": row.get("origin") or "",
            "bundle": row.get("bundle") or "",
            "filename": row.get("filename") or "",
            "anchor_text": extra.get("anchor") or "",
            "node_created": _d(extra.get("node_created")),
            "file_created": _d(row.get("file_created")),
            "pdf_creation_date": _d(row.get("pdf_created")),
            "current_start_date": _d(cat.get("effective_start_date")
                                       or row.get("current_start_date")),
            "proposed_effective_start_date": _d(row.get("candidate_start_date")),
            "action": {"keep_page_date": "keep_page_date",
                       "propose_override": "override",
                       "needs_manual_review": "review"}.get(row["action"], row["action"]),
            "date_type": row.get("date_type") or "",
            "date_source": row.get("date_source") or "",
            "deterministic_rule": row.get("rule") or "",
            "llm_used": "yes" if used_llm else "no",
            "llm_confidence": row.get("confidence") if used_llm else "",
            "llm_evidence": (llm_raw.get("evidence") or row.get("evidence") or "")
                            if used_llm else "",
            "edition_label": row.get("edition_label") or "",
            "publication_statement": (llm_raw.get("publication_statement") or ""),
            "evidence_location": locations.get(row["document_id"], ""),
            "evidence_grounded": (
                str(grounding[row["document_id"]]["grounded"]).lower()
                if row["document_id"] in grounding else ""),
            "pdf_available_to_llm": available if used_llm else "",
            "pdf_url_reachable_now": recheck.get(row["document_id"], "") if used_llm else "",
            "url": row.get("url") or "",
        }
        out["why"] = why_sentence(out)
        for column in HUMAN_COLUMNS:
            out[column] = ""
        return out

    # --------------------------------------------------------------- strata --
    def pick(pool: list[dict], n: int, key=None) -> list[dict]:
        """Deterministic choice: rank by interest, then sample within the top."""
        if not pool or n <= 0:
            return []
        if key:
            pool = sorted(pool, key=key)
        head = pool[: max(n * 3, n)]
        return random.sample(head, min(n, len(head)))

    def node_created_of(row: dict) -> str | None:
        """The page's date. It lives in the Phase 0A/0B metadata, not in the
        decisions CSV, which only records the resolver's output."""
        return (side.get(row["document_id"], {}) or {}).get("node_created")

    def gap(row: dict) -> int:
        node, file_c = _dt(node_created_of(row)), _dt(row["file_created"])
        return abs((file_c - node).days) if (node and file_c) else 0

    def pdf_conflict(row: dict) -> int:
        node, pdf_c = _dt(node_created_of(row)), _dt(row["pdf_created"])
        return abs((node - pdf_c).days) if (node and pdf_c) else 0

    single = [r for r in decisions if r["rule"] == "single_pdf_page"]
    multi_together = [r for r in decisions if r["rule"] == "multi_pdf_uploaded_with_page"]
    multi_overtime = [r for r in decisions
                      if int(r["page_pdf_count"] or 1) > 1
                      and node_span_years.get(r["node_uuid"], 0) > 1]
    late = [r for r in decisions if r["rule"] in
            ("multi_pdf_late_upload_review", "single_pdf_late_upload_review",
             "multi_pdf_url_month_review", "multi_pdf_upload_date",
             "single_pdf_late_upload", "multi_pdf_url_month")]
    migration = [r for r in decisions
                 if _dt(r["file_created"]) and _dt(r["file_created"]) < MIGRATION_END]
    inbody = [r for r in decisions if r["origin"] == "inbody"]
    annual = [r for r in decisions
              if "annual" in (r["filename"] or "").lower()
              or (r["filename"] or "").startswith("TAR_")]
    editions = [r for r in decisions if r["edition_label"]]
    llm_rows = [r for r in decisions if r["decided_by"] == "llm"]
    llm_overrides = [r for r in llm_rows if r["action"] == "propose_override"]

    selected: list[dict] = []
    seen: set[str] = set()

    def add(rows: list[dict], group: str) -> None:
        for row in rows:
            if row["document_id"] in seen:
                continue
            seen.add(row["document_id"])
            selected.append(enrich(row, group))

    n = args.per_group
    # 1. Single-PDF pages: prefer ones where the PDF's own date disagrees, since
    #    that is where the default rule is doing the most work.
    add(pick(single, n, key=lambda r: -pdf_conflict(r)), "1_single_pdf")
    # 2. Multi-PDF: half published together, half accreted across years.
    add(pick(multi_together, n // 2), "2_multi_pdf_together")
    add(pick(multi_overtime, n - n // 2,
             key=lambda r: -node_span_years.get(r["node_uuid"], 0)), "2_multi_pdf_over_time")
    # 3. Late uploads, biggest gaps first.
    add(pick(late, n, key=lambda r: -gap(r)), "3_late_upload")
    # 4. Migration era, prioritising DocInfo conflicts.
    add(pick(migration, n, key=lambda r: -pdf_conflict(r)), "4_migration_era")
    # 5. In-body / annual / edition.
    # The annual-report series is the motivating example, so take the whole run
    # of editions rather than whatever sorts first: rank by having a recovered
    # edition label, then by how crowded the page is (the accretive shelf).
    add(sorted(annual, key=lambda r: (not r["edition_label"],
                                      -int(r["page_pdf_count"] or 1),
                                      r["filename"] or ""))[:10], "5_annual_report")
    add(pick(editions, 4, key=lambda r: -int(r["page_pdf_count"] or 1)), "5_edition_style")
    add(pick(inbody, max(0, n - 10)), "5_inbody_other")
    # Always: every LLM override, then a spread of other LLM cases.
    add(llm_overrides, "6_llm_override")
    add([r for r in decisions if r["action"] == "propose_override"], "6_override_other")
    add(pick([r for r in llm_rows if r["action"] != "propose_override"], 8,
             key=lambda r: -float(r["confidence"] or 0)), "6_llm_other")

    # ------------------------------------------------------------------ CSV --
    os.makedirs(OUT_DIR, exist_ok=True)
    # utf-8-sig so Excel opens the non-ASCII filenames correctly.
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected)

    # ------------------------------------------------------------------- MD --
    total = len(decisions)
    by_group = Counter(r["review_group"] for r in selected)
    by_action = Counter(r["action"] for r in selected)
    all_actions = Counter(r["action"] for r in decisions)
    L: list[str] = []
    L.append("# PDF date resolution — manual review pack\n")
    L.append(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} from the Phase 0 "
             "shadow results. **Nothing has been applied.** Every "
             "`proposed_effective_start_date` below is a suggestion held in shadow storage; "
             "the live `effective_start_date` is unchanged.\n")
    L.append(f"Companion CSV: `{os.path.basename(OUT_CSV)}` — the `human_*` columns "
             "are blank for you to fill in.\n")

    L.append("## Summary\n")
    L.append("| metric | value |")
    L.append("|---|---:|")
    L.append(f"| total PDFs in corpus analysis | {total} |")
    L.append(f"| sampled for review | {len(selected)} |")
    for group in sorted(by_group):
        L.append(f"| &nbsp;&nbsp;{group} | {by_group[group]} |")
    L.append(f"| single-PDF cases sampled | "
             f"{sum(1 for r in selected if str(r['page_pdf_count']) == '1')} |")
    L.append(f"| multi-PDF cases sampled | "
             f"{sum(1 for r in selected if str(r['page_pdf_count']) not in ('1', ''))} |")
    L.append(f"| in-body cases sampled | "
             f"{sum(1 for r in selected if r['origin'] == 'inbody')} |")
    L.append(f"| LLM-assisted cases sampled | "
             f"{sum(1 for r in selected if r['llm_used'] == 'yes')} |")
    L.append(f"| corpus: keep_page_date | {all_actions['keep_page_date']} |")
    L.append(f"| corpus: deterministic overrides | "
             f"{sum(1 for r in decisions if r['action'] == 'propose_override' and r['decided_by'] == 'deterministic')} |")
    L.append(f"| corpus: LLM overrides | {len(llm_overrides)} |")
    L.append(f"| corpus: review | {all_actions['needs_manual_review']} |")
    L.append(f"| corpus: LLM-assisted total | {len(llm_rows)} |")

    L.append("\n### Sampled decisions by action\n")
    L.append("| action | count |")
    L.append("|---|---:|")
    for key, count in by_action.most_common():
        L.append(f"| {key} | {count} |")

    L.append("\n### Most common reasons for a proposed change (whole corpus)\n")
    reasons = Counter(r["rule"] for r in decisions if r["action"] == "propose_override")
    meaning = {
        "llm_interpreted": "The document's own text states an explicit publication "
                           "date, quoted verbatim by the model. This is now the only "
                           "route to an override.",
    }
    L.append("| rule | overrides | what it means |")
    L.append("|---|---:|---|")
    for rule, count in reasons.most_common():
        L.append(f"| `{rule}` | {count} | {meaning.get(rule, '')} |")

    annual_rows = [r for r in selected if r["review_group"] == "5_annual_report"]
    if annual_rows:
        L.append("\n## Annual reports — an edition, NOT a publication date\n")
        L.append("The system deliberately keeps the page date and records the reporting "
                 "period separately. `2024-2025` is a **label**, not a date: none of "
                 "these documents was published on 2024-01-01.\n")
        L.append("| filename | anchor text | edition_label | current effective_start_date "
                 "| proposed | PDF creation date | action |")
        L.append("|---|---|---|---|---|---|---|")
        for r in annual_rows:
            L.append(f"| {r['filename'][:34]} | {r['anchor_text'][:26] or '-'} "
                     f"| **{r['edition_label'] or '-'}** | {r['current_start_date'] or '-'} "
                     f"| {r['proposed_effective_start_date'] or '-'} "
                     f"| {r['pdf_creation_date'] or '-'} | {r['action']} |")

    llm_selected = [r for r in selected if r["llm_used"] == "yes"]
    if llm_selected:
        L.append("\n## LLM-assisted decisions\n")
        L.append(f"{len(llm_selected)} sampled. `pdf_available_to_llm=false` means the "
                 "model saw **metadata only** — the PDF could not be fetched, or had no "
                 "readable internal metadata. Failed fetches are shown, not hidden.\n")
        for r in sorted(llm_selected, key=lambda x: (x["action"] != "override",
                                                     -float(x["llm_confidence"] or 0))):
            L.append(f"\n### {r['filename'] or r['document_id']}\n")
            L.append(f"- **action**: `{r['action']}` · **date_type**: `{r['date_type']}` "
                     f"· **confidence**: {r['llm_confidence']}")
            L.append(f"- **current effective_start_date**: {r['current_start_date'] or '-'} · "
                     f"**proposed**: {r['proposed_effective_start_date'] or '(unchanged)'}")
            L.append(f"- **pdf_available_to_llm**: `{r['pdf_available_to_llm']}` · "
                     f"**url reachable now**: `{r['pdf_url_reachable_now'] or 'not rechecked'}`")
            L.append(f"- **page**: {(r['page_title'] or '-')[:60]} "
                     f"({r['page_pdf_count']} PDFs, {r['origin']})")
            L.append("- **evidence available**: "
                     f"node.created={r['node_created'] or '-'}, "
                     f"file.created={r['file_created'] or '(none - in-body)'}, "
                     f"pdf CreationDate={r['pdf_creation_date'] or '(unreadable)'}, "
                     f"anchor={r['anchor_text'][:40] or '(none)'}")
            L.append(f"- **LLM reasoning**: {r['llm_evidence'] or '-'}")
            if r["edition_label"]:
                L.append(f"- **edition_label**: `{r['edition_label']}` "
                         "(a reporting period, not a publication date)")
            L.append("- **decision**: " + (
                f"proposes changing {r['current_start_date'] or '?'} -> "
                f"**{r['proposed_effective_start_date']}**, on an explicit publication statement."
                if r["action"] == "override" else "abstained — page date kept."))
            L.append(f"- pdf: {r['url']}")

    overrides = [r for r in selected if r["action"] == "override"]
    L.append(f"\n## Every proposed override in this sample ({len(overrides)})\n")
    L.append("Each block lays out the raw evidence so the decision can be checked "
             "without reading any code.\n")
    for r in overrides:
        L.append(f"\n**{r['filename'] or r['document_id']}**  ({r['review_group']})\n")
        L.append("```")
        L.append(f"Current:   {r['current_start_date'] or '(none)'}")
        L.append(f"Proposed:  {r['proposed_effective_start_date']}   "
                 f"[{r['date_type']} via {r['date_source']}]")
        L.append("Evidence:")
        L.append(f"  node.created      = {r['node_created'] or '-'}")
        L.append(f"  file.created      = {r['file_created'] or '(no Drupal file record)'}")
        L.append(f"  PDF CreationDate  = {r['pdf_creation_date'] or '(unreadable)'}")
        L.append(f"  PDFs on this page = {r['page_pdf_count']}")
        L.append(f"  origin            = {r['origin']}")
        L.append(f"  anchor text       = {r['anchor_text'] or '-'}")
        L.append(f"  rule              = {r['deterministic_rule']}")
        L.append(f"  LLM used          = {r['llm_used']}"
                 + (f" (confidence {r['llm_confidence']})" if r["llm_used"] == "yes" else ""))
        L.append("```")
        L.append(r["why"])
        L.append(f"\n- page: {r['page_url'] or '-'}\n- pdf: {r['url']}")

    L.append("\n## Full sampled set\n")
    L.append("| # | group | filename | PDFs | origin | node.created | file.created "
             "| pdf date | current | proposed | action | rule | LLM |")
    L.append("|---:|---|---|---:|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(selected, 1):
        L.append(
            f"| {i} | {r['review_group']} | {(r['filename'] or '')[:30]} "
            f"| {r['page_pdf_count']} | {r['origin']} | {r['node_created'] or '-'} "
            f"| {r['file_created'] or '-'} | {r['pdf_creation_date'] or '-'} "
            f"| {r['current_start_date'] or '-'} | {r['proposed_effective_start_date'] or '-'} "
            f"| **{r['action']}** | {r['deterministic_rule']} | {r['llm_used']} |")

    L.append("\n## How to review\n")
    L.append("For each row in the CSV, fill in:\n")
    L.append("- `human_decision` — `keep_page_date`, `override` or `review`")
    L.append("- `human_correct` — `YES` if the system's action matches yours, else `NO`")
    L.append("- `human_effective_start_date` — the date you believe is right (blank = keep current)")
    L.append("- `human_date_type` — publication / upload / authoring / edition / event")
    L.append("- `human_edition_label` — e.g. `2024-25`, where applicable")
    L.append("- `human_notes` — anything that explains a `NO`\n")
    L.append("The metric that matters is **false overrides**: rows where the system "
             "proposes a change and you judge the current date to be better. A stale "
             "date is recoverable; a confidently wrong one is not.")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"selected {len(selected)} cases across {len(by_group)} groups")
    print(f"  LLM-assisted: {sum(1 for r in selected if r['llm_used'] == 'yes')}")
    print(f"  proposed overrides: {len(overrides)}")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
