"""Score the date resolver against the hand-labelled evaluation set.

The headline metric is **false overrides**: proposing a date change where the
expected outcome was to keep the page date. A stale date is consistent with its
page and merely unhelpful; a confidently wrong date is a silent corruption that
retrieval and recency ranking will act on. Recall of correct overrides is the
secondary metric.

Runs the deterministic tree on every case, and the LLM on whichever cases the
tree defers — the same routing production would use, so the score reflects the
whole pipeline rather than either half.

    python -m scripts.eval_date_resolution            # deterministic + LLM
    python -m scripts.eval_date_resolution --no-llm   # deterministic only
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections import Counter

from app.ingestion.date_evidence import PageContext, PdfEvidence
from app.ingestion.date_llm import interpret
from app.ingestion.date_rules import decide

EVALSET = os.path.join("reports", "phase0", "date_evalset.json")
OUT_MD = os.path.join("reports", "phase0", "eval_report.md")

logger = logging.getLogger(__name__)


def _norm_edition(label: str | None) -> str | None:
    """Canonicalise 2024-2025 / 2024-25 to 2024-25 for comparison.

    The model spells the span out in full; the deterministic extractor emits the
    short form. Both name the same period, so scoring must not treat the
    difference as a miss.
    """
    if not label:
        return None
    match = re.match(r"(20\d{2})\s*[-_/]\s*(\d{2,4})", str(label).strip())
    if not match:
        return str(label).strip()
    return f"{match.group(1)}-{int(match.group(2)) % 100:02d}"


def build(case: dict) -> PdfEvidence:
    return PdfEvidence(
        document_id=case["id"],
        origin=case.get("origin", "attachment"),
        url=case.get("url"),
        filename=case.get("filename"),
        anchor=case.get("anchor"),
        current_start_date=case.get("node_created"),
        file_created=case.get("file_created"),
        pdf_created=case.get("pdf_created"),
        head_text=case.get("head_text", ""),
        page=PageContext(
            node_uuid=f"node-{case['id']}",
            node_title=case.get("node_title", ""),
            node_created=case.get("node_created"),
            bundle=case.get("bundle"),
            pdf_count=int(case.get("page_pdf_count", 1)),
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-llm", action="store_true",
                        help="Score the deterministic tree alone.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    with open(EVALSET, encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]

    rows = []
    llm_calls = 0
    for case in cases:
        evidence = build(case)
        decision = decide(evidence)
        raw = None
        if decision.action == "needs_llm":
            if args.no_llm:
                decision.action = "needs_manual_review"
                decision.rule = "llm_skipped"
            else:
                verdict = interpret(evidence)
                llm_calls += 1
                if verdict is None:
                    decision.action = "keep_page_date"
                    decision.rule = "llm_unavailable"
                else:
                    raw = verdict.model_dump()
                    safe = verdict.safe_action()
                    decision.action = ("propose_override" if safe == "override"
                                       else "needs_manual_review" if safe == "review"
                                       else "keep_page_date")
                    decision.date_type = verdict.date_type
                    decision.edition_label = verdict.edition_label or evidence.edition
                    decision.confidence = verdict.confidence
                    decision.evidence = verdict.evidence
                    decision.decided_by = "llm"
                    if safe == "override":
                        decision.candidate_start_date = verdict.candidate_start_date
                        decision.source = "llm_publication"

        expected = case["expected_action"]
        got = decision.action
        # A deferral that ends as review is an acceptable outcome wherever the
        # label says review; overrides and keeps must match exactly.
        correct = got == expected
        false_override = expected != "propose_override" and got == "propose_override"
        missed_override = expected == "propose_override" and got != "propose_override"
        rows.append({
            "id": case["id"], "expected": expected, "got": got, "correct": correct,
            "false_override": false_override, "missed_override": missed_override,
            "expected_type": case.get("expected_type"), "got_type": decision.date_type,
            "expected_edition": case.get("expected_edition"),
            "got_edition": decision.edition_label,
            "rule": decision.rule, "by": decision.decided_by,
            "conf": decision.confidence, "note": case.get("note", ""),
            "evidence": decision.evidence, "raw": raw,
        })

    total = len(rows)
    correct = sum(1 for r in rows if r["correct"])
    fo = [r for r in rows if r["false_override"]]
    mo = [r for r in rows if r["missed_override"]]
    ed_ok = sum(1 for r in rows if r["expected_edition"]
                and _norm_edition(r["got_edition"]) == _norm_edition(r["expected_edition"]))
    ed_total = sum(1 for r in rows if r["expected_edition"])

    lines = ["# Date-resolution evaluation\n"]
    lines.append(f"{total} hand-labelled cases from the real corpus. "
                 f"{'Deterministic only.' if args.no_llm else f'{llm_calls} LLM calls.'}\n")
    lines.append(f"- action correct: **{correct}/{total}** ({100*correct/total:.0f}%)")
    lines.append(f"- **false overrides: {len(fo)}** (primary metric — lower is better)")
    lines.append(f"- missed overrides: {len(mo)}")
    lines.append(f"- edition labels correct: **{ed_ok}/{ed_total}**")

    lines.append("\n### Per-case\n")
    lines.append("| id | expected | got | type | edition | by | rule | ok |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        mark = "ok" if r["correct"] else ("**FALSE OVERRIDE**" if r["false_override"]
                                          else "miss")
        lines.append(f"| {r['id']} | {r['expected']} | {r['got']} | {r['got_type']} "
                     f"| {r['got_edition'] or '-'} | {r['by']} | {r['rule']} | {mark} |")

    if fo:
        lines.append("\n### False overrides\n")
        for r in fo:
            lines.append(f"- **{r['id']}** — {r['note']}\n  - rule `{r['rule']}` "
                         f"({r['by']}), evidence: {r['evidence']}")
    if mo:
        lines.append("\n### Missed overrides\n")
        for r in mo:
            lines.append(f"- **{r['id']}** — {r['note']}\n  - got `{r['got']}` via "
                         f"`{r['rule']}` ({r['by']})")

    mism = [r for r in rows if not r["correct"] and not r["false_override"]
            and not r["missed_override"]]
    if mism:
        lines.append("\n### Other mismatches (keep vs review)\n")
        for r in mism:
            lines.append(f"- **{r['id']}**: expected `{r['expected']}`, got `{r['got']}` "
                         f"via `{r['rule']}`")

    lines.append("\n### Date-type distribution\n")
    lines.append("| type | count |")
    lines.append("|---|---:|")
    for key, n in Counter(r["got_type"] for r in rows).most_common():
        lines.append(f"| {key} | {n} |")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
