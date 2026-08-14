"""Audit the conflation risk inside the promoted PI identities.

Phase 7.1 promoted 192 PI names to ``pi_attested``, and the false-merge rate
reported there measured the *resolver* against reviewed cases — not the
*promotion rule* against reality. This estimates the second.

The question is narrow: **for how many promoted names could the row actually be
more than one real person?** The corpus cannot answer that directly, so this
computes the observable signals that would betray it and ranks the sample by
them, biasing selection toward the risky end rather than sampling uniformly.

Risk signals, and what each would mean
--------------------------------------
``surname_shared``    other people in the corpus with the same surname. The
                      "Amit Kumar" shape. Two-token names built on a crowded
                      surname are the primary conflation risk.
``initials_shared``   other people with the same initials — a weaker signal, but
                      it is how "R K Pachauri" and "Rajendra Kumar Pachauri"
                      would fail to be distinguished.
``prefix_shared``     other people whose name starts with the same given name and
                      shares the surname, e.g. "Anil Kumar" vs "Anil K Kumar".
                      Near-duplicates that may or may not be one person.
``pi_projects``       blast radius: how many LED_BY claims hang off this identity
                      if it is wrong.
``divisions``         the coherence signal. Exactly 1 is required to promote, so
                      a name at 1 with many projects is coherent; the interest is
                      in names that only *just* stayed at 1.
``career_years``      a long span with a crowded name is the compound risk.

Selection is deliberately biased. A uniform sample would be dominated by
one-project three-token names that carry almost no risk and would flatter the
result.

    python -m scripts.audit_pi_promotions              # 40-row sample
    python -m scripts.audit_pi_promotions --size 50
    python -m scripts.audit_pi_promotions --json out.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("audit_pi_promotions")

_OUT = Path("reports/knowledge/pi_promotion_audit.json")

# Risk bands. Deliberately coarse: the inputs are heuristics, and a finer scale
# would imply a precision the evidence does not support.
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"


@dataclass
class AuditRow:
    """One promoted identity, with everything needed to judge it by hand."""

    canonical_name: str
    normalized_name: str
    entity_id: str
    trust: str
    pi_projects: int
    pi_occurrences: int
    project_codes: list[str]
    divisions: list[str]
    career_years: int
    name_tokens: int
    surname_shared: int
    initials_shared: int
    prefix_shared: int
    same_name_candidates: list[str]
    authoritative_match: bool
    risk: str = RISK_LOW
    risk_reasons: list[str] = field(default_factory=list)


def _risk(row: AuditRow) -> tuple[str, list[str]]:
    """Assess one row. Compound signals matter more than any single one.

    A three-token name with a crowded surname is far safer than a two-token one,
    because the middle token is itself discriminating — which is why the
    promotion rule only applies the surname test to two-token names, and why the
    same asymmetry appears here.
    """
    reasons: list[str] = []
    score = 0

    if row.name_tokens == 2:
        score += 1
        reasons.append("two-token name")
    if row.surname_shared >= 3:
        score += 1
        reasons.append(f"surname shared with {row.surname_shared}")
    if row.same_name_candidates:
        # Another *person entity* whose name is a near-duplicate. The strongest
        # available signal that the row may not denote one person.
        score += 2
        reasons.append(
            f"{len(row.same_name_candidates)} near-duplicate person name(s)"
        )
    if row.prefix_shared:
        score += 1
        reasons.append(f"{row.prefix_shared} sharing given name and surname")
    if row.pi_projects >= 8:
        # Not a conflation signal on its own — it is a blast-radius signal.
        score += 1
        reasons.append(f"{row.pi_projects} projects depend on this identity")
    if row.career_years >= 15 and row.surname_shared >= 3:
        score += 1
        reasons.append(f"{row.career_years}-year span on a crowded surname")
    if row.authoritative_match:
        # A CMS person record with the same name is corroboration, not risk.
        score -= 2
        reasons.append("matches an authoritative CMS person record")

    if score >= 3:
        return RISK_HIGH, reasons
    if score >= 1:
        return RISK_MEDIUM, reasons
    return RISK_LOW, reasons or ["no risk signal"]


def build_rows() -> list[AuditRow]:
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection
    from app.knowledge.normalize import initials_of
    from app.knowledge.pi_promotion import collect_pi_evidence

    table = state_table()
    evidence = collect_pi_evidence()

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_id, canonical_name, normalized_name, trust "
            f"FROM `{table}_entity` WHERE entity_type='PERSON'"
        )
        people = list(cur.fetchall())

    by_surname: dict[str, list[str]] = defaultdict(list)
    by_initials: dict[str, list[str]] = defaultdict(list)
    authoritative = {
        r["normalized_name"] for r in people if r["trust"] == "authoritative"
    }
    for person in people:
        tokens = person["normalized_name"].split()
        if len(tokens) >= 2:
            by_surname[tokens[-1]].append(person["normalized_name"])
        by_initials[initials_of(person["normalized_name"])].append(
            person["normalized_name"]
        )

    rows: list[AuditRow] = []
    for person in people:
        if person["trust"] != "pi_attested":
            continue
        normalized = person["normalized_name"]
        entry = evidence.get(normalized)
        if entry is None:
            continue
        tokens = normalized.split()
        surname = tokens[-1]

        # Near-duplicates: another person sharing the surname *and* the first
        # given name, differing only in a middle token or an initial.
        prefix_shared = [
            other
            for other in by_surname.get(surname, [])
            if other != normalized and other.split()[0] == tokens[0]
        ]
        # A stricter notion of "same name": identical once middle initials are
        # dropped.
        def _bare(name: str) -> str:
            parts = name.split()
            return " ".join([parts[0], parts[-1]]) if len(parts) >= 2 else name

        same_name = [
            other
            for other in by_surname.get(surname, [])
            if other != normalized and _bare(other) == _bare(normalized)
        ]

        row = AuditRow(
            canonical_name=person["canonical_name"],
            normalized_name=normalized,
            entity_id=person["entity_id"],
            trust=person["trust"],
            pi_projects=len(entry.project_ids),
            pi_occurrences=len(entry.start_dates) or len(entry.project_ids),
            project_codes=sorted(entry.project_codes)[:6],
            divisions=sorted(entry.divisions),
            career_years=entry.career_years,
            name_tokens=len(tokens),
            surname_shared=max(0, len(by_surname.get(surname, [])) - 1),
            initials_shared=max(
                0, len(by_initials.get(initials_of(normalized), [])) - 1
            ),
            prefix_shared=len(prefix_shared),
            same_name_candidates=sorted(same_name)[:5],
            authoritative_match=normalized in authoritative,
        )
        row.risk, row.risk_reasons = _risk(row)
        rows.append(row)
    return rows


def select(rows: list[AuditRow], size: int) -> list[AuditRow]:
    """Bias the sample toward the risky end.

    Ranked by the signals that would betray conflation, then the top ``size``
    taken. A uniform sample would be dominated by one-project three-token names
    that carry almost no risk and would flatter the result.
    """
    risk_order = {RISK_HIGH: 0, RISK_MEDIUM: 1, RISK_LOW: 2}
    ranked = sorted(
        rows,
        key=lambda r: (
            risk_order[r.risk],
            -len(r.same_name_candidates),
            -r.prefix_shared,
            -r.surname_shared,
            -r.pi_projects,
            r.name_tokens,
            r.normalized_name,
        ),
    )
    return ranked[:size]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--size", type=int, default=40, help="Sample size.")
    parser.add_argument("--json", dest="json_out", default=str(_OUT))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    rows = build_rows()
    if not rows:
        raise SystemExit("No pi_attested identities found. Run scripts.seed_entities.")
    sample = select(rows, args.size)

    population = {band: sum(1 for r in rows if r.risk == band)
                  for band in (RISK_HIGH, RISK_MEDIUM, RISK_LOW)}
    print(f"Promoted identities: {len(rows)}")
    print(f"  population risk: {population}")
    print(f"  sample: {len(sample)} (biased toward the risky end)\n")

    header = (
        f"  {'name':30} {'tok':>3} {'proj':>4} {'surn':>4} {'pref':>4} "
        f"{'dup':>3} {'yrs':>3}  {'risk':6} reasons"
    )
    print(header)
    for row in sample:
        print(
            f"  {row.canonical_name[:29]:30} {row.name_tokens:>3} "
            f"{row.pi_projects:>4} {row.surname_shared:>4} {row.prefix_shared:>4} "
            f"{len(row.same_name_candidates):>3} {row.career_years:>3}  "
            f"{row.risk:6} {'; '.join(row.risk_reasons)[:58]}"
        )

    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(
        json.dumps(
            {
                "promoted_total": len(rows),
                "population_risk": population,
                "sample_size": len(sample),
                "note": (
                    "Risk bands are heuristic. They rank observable signals that "
                    "would betray a name covering more than one person; they are "
                    "not evidence that it does."
                ),
                "sample": [asdict(r) for r in sample],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
