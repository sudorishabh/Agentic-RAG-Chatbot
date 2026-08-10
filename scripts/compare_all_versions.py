"""Full-corpus comparison across every shadow version: v1 -> v2 -> v3 -> v3-final.

Each version is a stored decisions CSV. This reports the category totals side by
side and explains, per transition, which class of decision moved and why.

Read-only; reads CSVs and writes one markdown file.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter

OUT_DIR = os.path.join("reports", "phase0")
OUT_MD = os.path.join(OUT_DIR, "version_comparison_all.md")

VERSIONS = [
    ("v1", "prototype_decisions.v1.csv",
     "Upload timing could override on its own (file.created, /files/YYYY-MM/)."),
    ("v2", "prototype_decisions.v2.csv",
     "Deterministic overrides removed; only a quoted publication statement can "
     "override, confidence >= 0.9."),
    ("v3", "prototype_decisions.v3a.csv",
     "Few-shot prompt added for newspaper/issue/publication forms to recover recall."),
    ("v3-final", "prototype_decisions.csv",
     "Quote must carry the date; year-only and month-only cannot invent a day; "
     "publication linkage required; date must be grounded in the document text."),
]


def load(name: str) -> dict[str, dict]:
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return {r["document_id"]: r for r in csv.DictReader(fh)}


def counts(rows: dict[str, dict]) -> dict[str, int]:
    action = Counter(r["action"] for r in rows.values())
    return {
        "total": len(rows),
        "keep": action["keep_page_date"],
        "review": action["needs_manual_review"],
        "det_over": sum(1 for r in rows.values() if r["action"] == "propose_override"
                        and r["decided_by"] == "deterministic"),
        "llm_over": sum(1 for r in rows.values() if r["action"] == "propose_override"
                        and r["decided_by"] == "llm"),
        "llm_used": sum(1 for r in rows.values() if r["decided_by"] == "llm"),
        "editions": sum(1 for r in rows.values() if r.get("edition_label")),
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    data = [(label, load(fname), note) for label, fname, note in VERSIONS]
    data = [(label, rows, note) for label, rows, note in data if rows]

    L = ["# Full-corpus comparison: v1 -> v2 -> v3 -> v3-final\n"]
    for label, _rows, note in data:
        L.append(f"- **{label}** — {note}")
    L.append("")

    rows_by_label = {label: rows for label, rows, _ in data}
    stats = {label: counts(rows) for label, rows, _ in data}

    L.append("\n## Category totals\n")
    header = "| metric | " + " | ".join(label for label, _, _ in data) + " |"
    L.append(header)
    L.append("|---|" + "---:|" * len(data))
    labels = {
        "total": "PDFs analysed",
        "keep": "keep_page_date",
        "review": "review",
        "det_over": "deterministic overrides",
        "llm_over": "LLM overrides",
        "llm_used": "PDFs sent to the LLM",
        "editions": "edition labels",
    }
    for key, name in labels.items():
        L.append(f"| {name} | " + " | ".join(str(stats[label][key])
                                             for label, _, _ in data) + " |")
    L.append("| **total overrides** | " + " | ".join(
        f"**{stats[label]['det_over'] + stats[label]['llm_over']}**"
        for label, _, _ in data) + " |")

    L.append("\n## What changed at each step, and why\n")
    for (label_a, rows_a, _), (label_b, rows_b, note_b) in zip(data, data[1:]):
        shared = set(rows_a) & set(rows_b)
        moved = [(rows_a[d], rows_b[d]) for d in shared
                 if rows_a[d]["action"] != rows_b[d]["action"]]
        L.append(f"\n### {label_a} -> {label_b}\n")
        L.append(f"_{note_b}_\n")
        L.append(f"- decisions changed: **{len(moved)}**")
        pairs = Counter(f"{a['action']} -> {b['action']}" for a, b in moved)
        L.append("\n| transition | count | class of decision |")
        L.append("|---|---:|---|")
        why = {
            "propose_override -> keep_page_date":
                "upload-driven override withdrawn (upload timing is now supporting "
                "evidence only)",
            "propose_override -> needs_manual_review":
                "override withdrawn but the divergence is still worth a human look",
            "keep_page_date -> propose_override":
                "publication evidence recovered from the document text",
            "keep_page_date -> needs_manual_review":
                "routed for review after upload divergence was detected",
            "needs_manual_review -> keep_page_date":
                "the model found no date at all, so the page date stands",
            "needs_manual_review -> propose_override":
                "quoted publication statement accepted",
        }
        for key, n in pairs.most_common():
            L.append(f"| `{key}` | {n} | {why.get(key, '')} |")

        withdrawn = [(a, b) for a, b in moved
                     if a["action"] == "propose_override" and b["action"] != "propose_override"]
        upload_driven = [(a, b) for a, b in withdrawn
                         if a["decided_by"] == "deterministic"]
        llm_withdrawn = [(a, b) for a, b in withdrawn if a["decided_by"] == "llm"]
        added = [(a, b) for a, b in moved
                 if b["action"] == "propose_override" and a["action"] != "propose_override"]
        L.append(f"\n- upload-driven overrides removed: **{len(upload_driven)}**")
        L.append(f"- LLM overrides withdrawn: **{len(llm_withdrawn)}**")
        L.append(f"- overrides added: **{len(added)}**")
        if llm_withdrawn:
            L.append("\n  withdrawn LLM overrides:\n")
            L.append("  | filename | was proposed | reason class |")
            L.append("  |---|---|---|")
            for a, b in llm_withdrawn[:15]:
                L.append(f"  | {(a['filename'] or '')[:34]} "
                         f"| {str(a['candidate_date'])[:10]} | {b['action']} |")

    # Overrides surviving into the final version, traced back.
    final_label = data[-1][0]
    final = rows_by_label[final_label]
    survivors = [d for d, r in final.items() if r["action"] == "propose_override"]
    L.append(f"\n## The {len(survivors)} overrides in {final_label}, traced through every version\n")
    L.append("| filename | " + " | ".join(label for label, _, _ in data) + " |")
    L.append("|---|" + "---|" * len(data))
    for doc in survivors:
        cells = []
        for label, rows, _ in data:
            row = rows.get(doc)
            cells.append("—" if row is None else
                         {"propose_override": "override",
                          "keep_page_date": "keep",
                          "needs_manual_review": "review"}.get(row["action"], row["action"]))
        L.append(f"| {(final[doc]['filename'] or '')[:38]} | " + " | ".join(cells) + " |")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
