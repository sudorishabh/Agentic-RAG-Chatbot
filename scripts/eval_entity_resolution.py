"""Measure entity resolution against a reviewed case set, per entity type.

**False merge is the primary metric.** A false merge is a link to the wrong
entity, or any link at all on a case labelled ``NO_LINK``. It is reported first
and it is the only gate: a resolver that links more but merges falsely is worse
than one that links nothing, because a wrong identity silently corrupts every
claim later built on it.

Auto-resolution rate is reported but is explicitly *not* a target. Reading these
numbers, `unresolved` and `ambiguous` are healthy outcomes; they mean the
resolver declined rather than guessed.

    python -m scripts.eval_entity_resolution
    python -m scripts.eval_entity_resolution --type PERSON
    python -m scripts.eval_entity_resolution --json out.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("eval_entity_resolution")

_GOLD = Path("reports/knowledge/gold_resolution_v1.json")

# The safety gate. Phase 5 does not proceed to graph projection unless every
# type clears this, because a false merge is the one error the later phases
# cannot detect or undo.
MAX_FALSE_MERGE_RATE = 0.0


def _mention_for(case: dict[str, Any]) -> Any:
    from app.knowledge.normalize import normalize_for
    from app.knowledge.types import Mention

    surface = case["surface"]
    return Mention(
        chunk_id=f"eval-{case['id']}", document_id=f"doc-{case['id']}",
        start_offset=0, end_offset=max(1, len(surface)), surface_text=surface,
        normalized_text=normalize_for(case["type"], surface),
        entity_type=case["type"], extraction_method="gazetteer",
        extractor_version="eval", confidence=0.9,
    )


def _context_for(case: dict[str, Any]) -> Any:
    from app.knowledge.candidates import ResolutionContext
    from app.knowledge.normalize import normalize_for

    context = ResolutionContext(document_id=f"doc-{case['id']}")
    for name in case.get("doc_authors") or []:
        context.cms_names["PERSON"].add(normalize_for("PERSON", name))
    # Organization and project context, so the "context that is not about this
    # person" cases are genuinely exercised rather than merely asserted.
    for name in case.get("doc_orgs") or []:
        context.co_mentions["ORGANIZATION"].add(normalize_for("ORGANIZATION", name))
    for name in case.get("co_projects") or []:
        context.co_mentions["PROJECT"].add(normalize_for("PROJECT", name))
    return context


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    from app.knowledge.candidates import EntityIndex
    from app.knowledge.resolver import PROVISIONAL, resolve_mention

    index = EntityIndex.load()
    # Expectations are written as NAME:<canonical name>. Ids for CMS-backed
    # entities derive from record uuids, so a hard-coded id would not survive a
    # reseed on another machine; resolving the name here keeps the gold set
    # portable and keeps a wrong id from masquerading as a false merge.
    by_name = {
        row["canonical_name"]: entity_id for entity_id, row in index.entities.items()
    }

    def _expected_id(expected: str) -> str:
        if expected.startswith("NAME:"):
            return by_name.get(expected[5:], f"<unseeded:{expected[5:]}>")
        return expected
    per_type: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n": 0, "auto": 0, "provisional": 0, "ambiguous": 0,
            "unresolved": 0, "new": 0,
            "correct_link": 0, "false_merge": 0, "missed_link": 0,
            "canonical_leak": 0,
            "false_merges": [], "canonical_leaks": [], "declined": [],
        }
    )
    rows: list[dict[str, Any]] = []

    for case in cases:
        decision = resolve_mention(_mention_for(case), index, _context_for(case))
        stats = per_type[case["type"]]
        stats["n"] += 1
        stats[decision.decision.lower()] += 1

        expected = _expected_id(case["expected"])
        # `linked` covers a provisional link too: for a NO_LINK case, grouping a
        # surface under a name is still a claim the corpus does not support.
        linked = decision.linked
        canonical = decision.canonical

        if expected == "NO_CANONICAL":
            # The requirement that a provisional identity can never become a
            # claim subject. A provisional link is fine and expected; a
            # canonical one is the failure this expectation exists to catch.
            if canonical:
                stats["canonical_leak"] += 1
                stats["canonical_leaks"].append(
                    f"{case['id']} {case['surface']!r} -> {decision.entity_id} "
                    f"AUTO ({case['category']})"
                )
            else:
                stats["declined"].append(
                    f"{case['id']} {case['surface']!r} {decision.decision} "
                    f"({case['category']}: {decision.reason[:58]})"
                )
        elif expected == "NO_LINK":
            # Any link here is a false merge: the case says nothing should be
            # linked, so a link is an identity the corpus does not support.
            if linked:
                stats["false_merge"] += 1
                stats["false_merges"].append(
                    f"{case['id']} {case['surface']!r} -> {decision.entity_id} "
                    f"({case['category']})"
                )
            else:
                stats["declined"].append(
                    f"{case['id']} {case['surface']!r} {decision.decision} "
                    f"({case['category']}: {decision.reason[:60]})"
                )
        elif expected == "CODE":
            # Correct if it linked via the identifier tier at all; the specific
            # id depends on which CMS node holds the code.
            if linked and decision.tier == "tier0_identifier":
                stats["correct_link"] += 1
            else:
                stats["missed_link"] += 1
        elif linked and decision.entity_id == expected:
            stats["correct_link"] += 1
        elif linked:
            stats["false_merge"] += 1
            stats["false_merges"].append(
                f"{case['id']} {case['surface']!r} -> {decision.entity_id} "
                f"(expected {expected})"
            )
        else:
            stats["missed_link"] += 1
            stats["declined"].append(
                f"{case['id']} {case['surface']!r} {decision.decision} "
                f"({case['category']}: {decision.reason[:60]})"
            )

        rows.append({
            "id": case["id"], "type": case["type"], "surface": case["surface"],
            "category": case["category"], "expected": case["expected"],
            "expected_id": expected,
            "decision": decision.decision, "entity_id": decision.entity_id,
            "tier": decision.tier, "reason": decision.reason,
            "score": decision.score, "margin": decision.margin,
        })

    for stats in per_type.values():
        n = stats["n"] or 1
        links = stats["correct_link"] + stats["false_merge"]
        stats["precision"] = stats["correct_link"] / links if links else None
        stats["false_merge_rate"] = stats["false_merge"] / n
        stats["canonical_leak_rate"] = stats["canonical_leak"] / n
        stats["provisional_rate"] = stats["provisional"] / n
        stats["auto_rate"] = stats["auto"] / n
        stats["ambiguous_rate"] = stats["ambiguous"] / n
        stats["unresolved_rate"] = stats["unresolved"] / n
    return {"per_type": dict(per_type), "rows": rows}


def _fmt(value: Any) -> str:
    return f"{value:.3f}" if isinstance(value, float) else "    -"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--type", dest="entity_type", help="Restrict to one type.")
    parser.add_argument("--json", dest="json_out", help="Write full results here.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    if not _GOLD.exists():
        raise SystemExit(f"{_GOLD} not found.")
    gold = json.loads(_GOLD.read_text(encoding="utf-8"))
    cases = gold["cases"]
    if args.entity_type:
        cases = [c for c in cases if c["type"] == args.entity_type]

    result = evaluate(cases)
    per_type = result["per_type"]

    print(f"Cases: {len(cases)}   reviewed: {bool(gold.get('reviewed'))}")
    print(
        f"\n  {'type':14} {'n':>3} {'FALSE-MERGE':>12} {'LEAK':>6} {'prec':>7} "
        f"{'auto':>7} {'prov':>7} {'ambig':>7} {'unres':>7}"
    )
    for entity_type in sorted(per_type):
        s = per_type[entity_type]
        print(
            f"  {entity_type:14} {s['n']:>3} {_fmt(s['false_merge_rate']):>12} "
            f"{_fmt(s['canonical_leak_rate']):>6} {_fmt(s['precision']):>7} "
            f"{_fmt(s['auto_rate']):>7} {_fmt(s['provisional_rate']):>7} "
            f"{_fmt(s['ambiguous_rate']):>7} {_fmt(s['unresolved_rate']):>7}"
        )
    print(
        "\n  FALSE-MERGE = linked to the wrong entity, or linked at all where "
        "nothing should link."
        "\n  LEAK        = asserted a canonical identity for a provisional one "
        "(a claim subject that is only a name)."
    )

    for entity_type in sorted(per_type):
        s = per_type[entity_type]
        if s["canonical_leaks"]:
            print(f"\n  {entity_type} CANONICAL LEAKS ({s['canonical_leak']}):")
            for line in s["canonical_leaks"]:
                print(f"    ! {line}")
    for entity_type in sorted(per_type):
        s = per_type[entity_type]
        if s["false_merges"]:
            print(f"\n  {entity_type} FALSE MERGES ({s['false_merge']}):")
            for line in s["false_merges"]:
                print(f"    ! {line}")
    for entity_type in sorted(per_type):
        s = per_type[entity_type]
        if s["declined"]:
            print(f"\n  {entity_type} declined to link ({len(s['declined'])}):")
            for line in s["declined"]:
                print(f"    - {line}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nWrote {args.json_out}")

    worst = max((s["false_merge_rate"] for s in per_type.values()), default=0.0)
    leak = max((s["canonical_leak_rate"] for s in per_type.values()), default=0.0)
    passed = worst <= MAX_FALSE_MERGE_RATE and leak <= MAX_FALSE_MERGE_RATE
    print(
        f"\nSAFETY GATE: false-merge {worst:.3f}, canonical-leak {leak:.3f} "
        f"(both must be <= {MAX_FALSE_MERGE_RATE:.3f}) -> "
        f"{'PASS' if passed else 'FAIL'}"
    )
    if not passed:
        print("Graph projection must not proceed while this fails.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
