"""Before/after comparison of two shadow date-resolution runs.

Compares ``prototype_decisions.v1.csv`` (upload timing could override) against
the current ``prototype_decisions.csv`` (only a quoted publication statement
can override), and lists the documents whose decision changed.

Read-only; reads two CSVs and writes one markdown file.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter

OUT_DIR = os.path.join("reports", "phase0")
V1 = os.path.join(OUT_DIR, "prototype_decisions.v1.csv")
V2 = os.path.join(OUT_DIR, "prototype_decisions.csv")
OUT_MD = os.path.join(OUT_DIR, "before_after_comparison.md")


def load(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as fh:
        return {r["document_id"]: r for r in csv.DictReader(fh)}


def counts(rows: dict[str, dict]) -> dict[str, int]:
    action = Counter(r["action"] for r in rows.values())
    who = Counter(r["decided_by"] for r in rows.values())
    return {
        "total": len(rows),
        "keep_page_date": action["keep_page_date"],
        "deterministic_overrides": sum(
            1 for r in rows.values()
            if r["action"] == "propose_override" and r["decided_by"] == "deterministic"),
        "llm_overrides": sum(
            1 for r in rows.values()
            if r["action"] == "propose_override" and r["decided_by"] == "llm"),
        "review": action["needs_manual_review"],
        "llm_processed": who["llm"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", default=V1, help="Earlier run's CSV.")
    parser.add_argument("--current", default=V2, help="Later run's CSV.")
    parser.add_argument("--labels", default="v1,v2", help="Names for the two runs.")
    parser.add_argument("--out", default=OUT_MD)
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    name_a, name_b = (x.strip() for x in args.labels.split(","))
    v1, v2 = load(args.baseline), load(args.current)
    c1, c2 = counts(v1), counts(v2)

    L = [f"# Date resolution — {name_a} vs {name_b}\n"]
    L.append(f"Baseline `{os.path.basename(args.baseline)}` against "
             f"`{os.path.basename(args.current)}`.\n")

    L.append(f"| metric | {name_a} | {name_b} | change |")
    L.append("|---|---:|---:|---:|")
    labels = {
        "total": "total PDFs analysed",
        "keep_page_date": "keep page date",
        "deterministic_overrides": "deterministic overrides",
        "llm_overrides": "LLM overrides",
        "review": "review cases",
        "llm_processed": "PDFs downloaded + sent to LLM",
    }
    for key, label in labels.items():
        delta = c2[key] - c1[key]
        L.append(f"| {label} | {c1[key]} | {c2[key]} | {delta:+d} |")

    total_over_1 = c1["deterministic_overrides"] + c1["llm_overrides"]
    total_over_2 = c2["deterministic_overrides"] + c2["llm_overrides"]
    L.append(f"| **total proposed overrides** | **{total_over_1}** | "
             f"**{total_over_2}** | **{total_over_2 - total_over_1:+d}** |")

    # False-positive candidates: an override made without reading the document.
    # A deterministic override is one by construction — those rules never open
    # the PDF, so their only support is upload timing.
    L.append(f"\n- **overrides made without reading the document** — {name_a}: "
             f"{c1['deterministic_overrides']}, {name_b}: "
             f"{c2['deterministic_overrides']}. Any non-zero value is the v1 "
             "false-positive class.\n")

    changed = []
    for doc_id, row2 in v2.items():
        row1 = v1.get(doc_id)
        if not row1:
            continue
        if (row1["action"], row1["candidate_start_date"][:10] if row1["candidate_start_date"] else "") != \
           (row2["action"], row2["candidate_start_date"][:10] if row2["candidate_start_date"] else ""):
            changed.append((row1, row2))

    L.append(f"## Decisions that changed: {len(changed)}\n")
    pairs = Counter(f"{a['action']} -> {b['action']}" for a, b in changed)
    L.append("| transition | count |")
    L.append("|---|---:|")
    for key, n in pairs.most_common():
        L.append(f"| `{key}` | {n} |")

    reverted = [(a, b) for a, b in changed
                if a["action"] == "propose_override" and b["action"] != "propose_override"]
    L.append(f"\n### Overrides withdrawn ({len(reverted)})\n")
    L.append(f"Proposed by {name_a}, no longer proposed by {name_b}.\n")
    L.append(f"| filename | PDFs on page | page date | {name_a} proposed "
             f"| {name_a} rule | {name_b} action |")
    L.append("|---|---:|---|---|---|---|")
    for a, b in reverted[:40]:
        L.append(f"| {(a['filename'] or '')[:34]} | {a['page_pdf_count']} "
                 f"| {str(b['current_start_date'])[:10]} | {str(a['candidate_start_date'])[:10]} "
                 f"| `{a['rule']}` | {b['action']} |")
    if len(reverted) > 40:
        L.append(f"\n_({len(reverted) - 40} more in the CSVs.)_")

    new_over = [(a, b) for a, b in changed
                if b["action"] == "propose_override" and a["action"] != "propose_override"]
    if new_over:
        L.append(f"\n### Overrides added ({len(new_over)})\n")
        L.append(f"Recovered by {name_b}.\n")
        L.append(f"| filename | page date | {name_b} proposed | evidence |")
        L.append("|---|---|---|---|")
        for a, b in new_over:
            L.append(f"| {(b['filename'] or '')[:32]} | {str(b['current_start_date'])[:10]} "
                     f"| {str(b['candidate_start_date'])[:10]} | {(b['evidence'] or '')[:70]} |")

    still = [doc for doc, r in v2.items()
             if r["action"] == "propose_override"
             and v1.get(doc, {}).get("action") == "propose_override"]
    L.append(f"\n### Overrides retained in both versions: {len(still)}\n")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
