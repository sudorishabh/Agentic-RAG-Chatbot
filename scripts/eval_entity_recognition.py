"""Measure the whole naming path: can a question's words reach the right entity?

``scripts.eval_entity_resolution`` measures the resolver, and measures it well —
but it hands the resolver a ``Mention`` it constructs itself. That is the right
way to test resolution and it is blind to the step in front of it, which is
where the corpus was actually losing entities: the gazetteer matches *surfaces*,
every claim-eligible person is stored as "Dr X", questions say "X", so no
mention was produced and the resolver was never called. Perfect resolution
metrics, nothing resolved.

This benchmark starts one step earlier, from the string a user would type:

    surface -> extract_mentions -> candidates -> resolve -> decision

and reports each stage separately, because they fail for different reasons and
have different fixes.

Stages
------
``recognized``       the surface produced a mention of the expected type. A miss
                     here is a *gazetteer* problem; nothing downstream can
                     recover it.
``candidate_recall`` the expected entity appeared in the shortlist. A miss here
                     is a *candidate generation* problem (Phase 3): scoring
                     never saw the right answer, so no threshold change could
                     have helped.
``resolved``         a canonical link to the expected entity.

Safety
------
The negative set is the point of the exercise, not a footnote. Every case marked
``expect_canonical: false`` must fail to produce a canonical link, and any that
does is reported as a **false merge** or a **canonical leak** and fails the run.
Recall that costs either is not an improvement.

``--baseline`` rebuilds the gazetteer the way it was built before this work —
no honorific-stripped surfaces, no PI name fields, the ten-word cap applied to
project titles — so the before/after comparison is reproduced on demand rather
than remembered. It changes nothing on disk and nothing about the resolver.

    python -m scripts.eval_entity_recognition
    python -m scripts.eval_entity_recognition --baseline
    python -m scripts.eval_entity_recognition --json reports/knowledge/recognition.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

logger = logging.getLogger("eval_entity_recognition")

# Surfaces that must never yield a canonical identity, and why each is here.
# Every one is either a real string from this corpus or the exact shape the
# guards exist to refuse.
NEGATIVES: tuple[tuple[str, str, str], ...] = (
    # Generic project titles that really are in the CMS.
    ("Steel", "PROJECT", "a material, and a real one-word CMS title"),
    ("Summary", "PROJECT", "a heading, and a real one-word CMS title"),
    ("Download", "PROJECT", "a UI label that reached the title column"),
    ("Environment", "PROJECT", "a topic word"),
    ("Assessment of", "PROJECT", "a title fragment carrying no information"),
    # Surname-only and initials-only personal names.
    ("Sharma", "PERSON", "a surname shared by many people"),
    ("Kumar", "PERSON", "a surname shared by many people"),
    ("Singh", "PERSON", "a surname shared by many people"),
    ("A K", "PERSON", "initials name nobody in particular"),
    ("R K", "PERSON", "initials name nobody in particular"),
    ("S S", "PERSON", "initials name nobody in particular"),
    ("Neha", "PERSON", "a single given name"),
    # Names that are also ordinary words.
    ("Medium", "ORGANIZATION", "a real news source and an ordinary adjective"),
    ("Forbes", "ORGANIZATION", "real, but too short to link from prose"),
    # Nothing the corpus has ever seen.
    ("Wholly Unknown Person", "PERSON", "no such entity"),
    ("Utterly Fictional Holdings", "ORGANIZATION", "no such entity"),
    ("Nonexistent Flagship Programme", "PROJECT", "no such entity"),
)

# Surface transformations applied to each sampled canonical name. Each is a way
# a real question refers to an entity the CMS stored differently.
VARIANTS = (
    "canonical",        # exactly as stored
    "no_honorific",     # "Dr Banwari Lal" -> "Banwari Lal"
    "extra_honorific",  # "Banwari Lal" -> "Dr Banwari Lal"
    "dotted_honorific", # "Dr Banwari Lal" -> "Dr. Banwari Lal"
    "trailing_comma",   # punctuation a sentence would put after the name
    "collapsed_space",  # double spaces, as several CMS values really have
)


def _variant(name: str, kind: str, entity_type: str) -> str | None:
    from app.knowledge.normalize import is_honorific, strip_honorifics

    tokens = name.split()
    if kind == "canonical":
        return name
    if kind == "collapsed_space":
        return "  ".join(tokens)
    if kind == "trailing_comma":
        return f"{name},"
    if entity_type != "PERSON":
        return None
    has_title = bool(tokens) and is_honorific(tokens[0])
    if kind == "no_honorific":
        return strip_honorifics(name) if has_title else None
    if kind == "extra_honorific":
        return None if has_title else f"Dr {name}"
    if kind == "dotted_honorific":
        if not has_title:
            return None
        return f"{tokens[0].rstrip('.')}. {' '.join(tokens[1:])}"
    return None


def is_single_name(canonical_name: str, entity_type: str) -> bool:
    """Whether a stored canonical name is one name rather than a CMS blob.

    Some `field_completed_sponsors` values are a whole funder *list* pasted
    into one field — "DELL Foundation,Deutsche Gesellschaft ...,Ministry of
    New and Renewable Energy,..." — and the seeder made each such string an
    entity. Extraction then correctly matches the first real organization
    inside it and links to *that* entity, which this benchmark would score as a
    false merge. It is not one: the resolver is right and the stored name is a
    data-quality artifact that should never have been an entity.

    Excluded from the positive sample so the metric measures name recognition
    rather than seed-data hygiene. The count is reported, so the artifacts stay
    visible rather than being quietly dropped.

    PROJECT is exempt from the token bound: project titles are legitimately
    long (up to 32 tokens here), and no project title is a delimited list.
    """
    if canonical_name.count(",") >= 2:
        return False
    if entity_type != "PROJECT" and len(canonical_name.split()) > 12:
        return False
    return True


def _sample_entities(index: Any, per_type: int) -> tuple[list[dict[str, Any]], int]:
    """Claim-eligible entities from the live store, with malformed names dropped.

    Sampled from the store rather than hand-listed so the benchmark grows with
    the corpus and cannot drift away from what is actually in it. Ordered by
    entity_id for determinism.
    """
    out: list[dict[str, Any]] = []
    skipped = 0
    for entity_type in ("PERSON", "ORGANIZATION", "PROJECT"):
        rows = []
        for row in sorted(
            (
                row for row in index.entities.values()
                if row["entity_type"] == entity_type
                and row.get("claim_eligible")
            ),
            key=lambda r: r["entity_id"],
        ):
            if not is_single_name(row["canonical_name"], entity_type):
                skipped += 1
                continue
            rows.append(row)
        out.extend(rows[:per_type])
    return out, skipped


def _mention_for_surface(surface: str, entity_type: str, gazetteer: Any) -> Any:
    """The mention extraction would produce for this surface, if any.

    The surface is embedded in a sentence rather than passed bare: that is how
    it reaches the extractor in production, and it exercises the boundary
    anchoring and the case-sensitivity rule that a bare string would not.
    """
    from app.knowledge.extract import extract_mentions

    text = f"The record mentions {surface} in this context."
    mentions = extract_mentions(
        text, chunk_id="eval", document_id="eval", gazetteer=gazetteer
    )
    for mention in mentions:
        if mention.entity_type == entity_type:
            return mention
    return mentions[0] if mentions else None


def _evaluate(index: Any, gazetteer: Any, per_type: int) -> dict[str, Any]:
    from app.knowledge.candidates import ResolutionContext, generate
    from app.knowledge.normalize import normalize_for
    from app.knowledge.resolver import resolve_mention

    positives: list[dict[str, Any]] = []
    sampled, skipped = _sample_entities(index, per_type)
    for row in sampled:
        for kind in VARIANTS:
            surface = _variant(row["canonical_name"], kind, row["entity_type"])
            if not surface:
                continue
            positives.append(
                {
                    "surface": surface, "variant": kind,
                    "type": row["entity_type"],
                    "expected_entity_id": row["entity_id"],
                    "canonical_name": row["canonical_name"],
                }
            )

    results: list[dict[str, Any]] = []
    for case in positives:
        mention = _mention_for_surface(case["surface"], case["type"], gazetteer)
        record = {**case, "recognized": mention is not None}
        if mention is None:
            record.update(candidate_recall=False, decision="NOT_EXTRACTED",
                          linked_entity_id=None)
            results.append(record)
            continue
        candidates = generate(mention, index)
        record["candidate_recall"] = any(
            c.entity_id == case["expected_entity_id"] for c in candidates
        )
        # Corroboration as production would have it: the document's own CMS
        # metadata names this person. Supplied for PERSON only, because that is
        # the only type whose thresholds require it.
        context = ResolutionContext(document_id="eval")
        if case["type"] == "PERSON":
            context.cms_names["PERSON"].add(
                normalize_for("PERSON", case["canonical_name"])
            )
        decision = resolve_mention(mention, index, context)
        record["decision"] = decision.decision
        record["linked_entity_id"] = decision.entity_id if decision.canonical else None
        record["resolved"] = (
            decision.canonical and decision.entity_id == case["expected_entity_id"]
        )
        record["false_merge"] = (
            decision.canonical and decision.entity_id != case["expected_entity_id"]
        )
        results.append(record)

    negatives: list[dict[str, Any]] = []
    for surface, entity_type, why in NEGATIVES:
        mention = _mention_for_surface(surface, entity_type, gazetteer)
        record = {
            "surface": surface, "type": entity_type, "why": why,
            "recognized": mention is not None,
        }
        if mention is None:
            record.update(decision="NOT_EXTRACTED", canonical=False,
                          claim_eligible=False)
        else:
            decision = resolve_mention(mention, index, ResolutionContext())
            record["decision"] = decision.decision
            record["canonical"] = decision.canonical
            record["claim_eligible"] = decision.claim_eligible
            record["linked_entity_id"] = decision.entity_id if decision.canonical else None
        negatives.append(record)

    return {"positives": results, "negatives": negatives,
            "skipped_malformed_names": skipped}


def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
    positives, negatives = payload["positives"], payload["negatives"]

    def _rate(rows, key):
        return round(sum(1 for r in rows if r.get(key)) / len(rows), 3) if rows else 0.0

    by_type: dict[str, dict[str, Any]] = {}
    for row in positives:
        bucket = by_type.setdefault(
            row["type"], {"n": 0, "recognized": 0, "candidate": 0, "resolved": 0}
        )
        bucket["n"] += 1
        bucket["recognized"] += int(bool(row.get("recognized")))
        bucket["candidate"] += int(bool(row.get("candidate_recall")))
        bucket["resolved"] += int(bool(row.get("resolved")))

    by_variant: dict[str, dict[str, Any]] = {}
    for row in positives:
        bucket = by_variant.setdefault(
            row["variant"], {"n": 0, "recognized": 0, "resolved": 0}
        )
        bucket["n"] += 1
        bucket["recognized"] += int(bool(row.get("recognized")))
        bucket["resolved"] += int(bool(row.get("resolved")))

    # A negative that produced a canonical link is a false merge; one that
    # produced a canonical link to a provisional identity is also a leak.
    leaked = [r for r in negatives if r.get("canonical")]

    return {
        "positive_cases": len(positives),
        "recognized": _rate(positives, "recognized"),
        "candidate_recall": _rate(positives, "candidate_recall"),
        "resolved": _rate(positives, "resolved"),
        "false_merge": _rate(positives, "false_merge"),
        "negative_cases": len(negatives),
        "negative_false_merge": round(len(leaked) / len(negatives), 3) if negatives else 0.0,
        "negatives_linked": [r["surface"] for r in leaked],
        "by_type": by_type,
        "by_variant": by_variant,
    }


def _baseline_gazetteer() -> Any:
    """The gazetteer as it was built before the recognition fixes.

    Reproduces all three of them in reverse — the honorific-stripped surface
    variants, the PI name fields, and the project-title exemption from the
    prose length cap — against the same live catalog, so the two runs differ in
    nothing else. Restores every patched attribute before returning.
    """
    from app.knowledge import gazetteer as gz

    saved = (gz._META_SOURCES, gz._MAX_PROJECT_TITLE_TOKENS, gz.surface_variants)
    try:
        gz._META_SOURCES = tuple(
            pair for pair in gz._META_SOURCES if "pi_name" not in pair[0]
        )
        gz._MAX_PROJECT_TITLE_TOKENS = gz._MAX_SURFACE_TOKENS
        gz.surface_variants = lambda surface, entity_type: []
        return gz.build_gazetteer(gz.load_rows())
    finally:
        gz._META_SOURCES, gz._MAX_PROJECT_TITLE_TOKENS, gz.surface_variants = saved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-type", type=int, default=60,
                        help="claim-eligible entities sampled per entity type")
    parser.add_argument("--baseline", action="store_true",
                        help="measure the pre-change gazetteer instead")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.ERROR, format="%(message)s")

    from app.knowledge.candidates import EntityIndex
    from app.knowledge.gazetteer import get_gazetteer

    index = EntityIndex.load()
    gazetteer = _baseline_gazetteer() if args.baseline else get_gazetteer()
    if args.baseline:
        print("*** BASELINE gazetteer (pre-change recognition) ***")

    payload = _evaluate(index, gazetteer, args.per_type)
    summary = _summarize(payload)

    print(f"Positive cases: {summary['positive_cases']}   "
          f"negative cases: {summary['negative_cases']}   "
          f"(skipped {payload['skipped_malformed_names']} malformed CMS names)")
    print(f"\n  recognized       {summary['recognized']:.3f}   "
          "(surface produced a mention of the right type)")
    print(f"  candidate_recall {summary['candidate_recall']:.3f}   "
          "(the right entity reached the shortlist)")
    print(f"  resolved         {summary['resolved']:.3f}   "
          "(canonical link to the right entity)")
    print(f"  FALSE MERGE      {summary['false_merge']:.3f}   "
          "(linked to the WRONG entity)")
    print(f"  NEGATIVE LEAK    {summary['negative_false_merge']:.3f}   "
          "(a must-not-link surface linked anyway)")

    print(f"\n  {'type':14s} {'n':>4s} {'recog':>7s} {'cand':>7s} {'resolved':>9s}")
    for entity_type, bucket in sorted(summary["by_type"].items()):
        n = bucket["n"]
        print(f"  {entity_type:14s} {n:>4d} {bucket['recognized']/n:>7.3f} "
              f"{bucket['candidate']/n:>7.3f} {bucket['resolved']/n:>9.3f}")

    print(f"\n  {'variant':18s} {'n':>4s} {'recog':>7s} {'resolved':>9s}")
    for variant, bucket in sorted(summary["by_variant"].items()):
        n = bucket["n"]
        print(f"  {variant:18s} {n:>4d} {bucket['recognized']/n:>7.3f} "
              f"{bucket['resolved']/n:>9.3f}")

    if summary["negatives_linked"]:
        print("\n  NEGATIVES THAT LINKED:")
        for surface in summary["negatives_linked"]:
            print(f"    ! {surface!r}")

    if args.verbose:
        print("\n  Unrecognized positives:")
        for row in payload["positives"]:
            if not row.get("recognized"):
                print(f"    - [{row['variant']}] {row['surface'][:70]!r}")

    ok = summary["false_merge"] == 0.0 and summary["negative_false_merge"] == 0.0
    if args.baseline:
        # The baseline is a measurement, not a thing that has to pass.
        ok = True
    print(f"\nSAFETY GATE: false-merge {summary['false_merge']:.3f}, "
          f"negative-leak {summary['negative_false_merge']:.3f} -> "
          f"{'PASS' if ok else 'FAIL'}")

    if args.json_path:
        from pathlib import Path

        path = Path(args.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"summary": summary, **payload}, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"Wrote {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
