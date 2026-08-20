"""Measure schema-aware graph routing against the fixed-route configuration.

Answers the question the change has to justify: *how much of the graph could be
asked for before, and how much can be asked for now* — measured on the same
questions, against the same data, through the same pipeline.

Two configurations, run back to back:

``fixed``   what the repository shipped. The router's pattern table only (the
            schema-aware planner is switched off), gated by the four classes
            ``policy.DEFAULT_ENABLED_CLASSES`` used to contain.
``schema``  the planner, gated by the shipped defaults.

Both run the real router, the real registry, the real Neo4j session, the real
Qdrant hydration and the real context builder. Nothing is mocked, so a
difference in the numbers is a difference in what a user would get.

Metrics
-------
``routed``          the question selected a template at all. A question that
                    does not route never reaches the graph, whatever the graph
                    knows — this is the number the routing limitation showed up
                    in.
``answered``        the traversal returned rows *and* they became context
                    blocks. This is the number the temporal limitation showed up
                    in: the fixed configuration routes several questions and
                    then returns nothing, because every template it can reach
                    reads current-state edges and this corpus has none.
``rows``            graph rows per answered question.
``hydrated``        evidence chunks Qdrant resolved for those rows. A gap
                    between rows and hydration is the graph citing text that no
                    longer exists.
``predicates``      distinct approved predicates any question reached.
``latency``         wall clock per question, and per stage.

    python -m scripts.bench_graph_routing
    python -m scripts.bench_graph_routing --section temporal
    python -m scripts.bench_graph_routing --json reports/knowledge/graph_routing_bench.json
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from typing import Any

logger = logging.getLogger("bench_graph_routing")

# Blocks each configuration may put in front of the model. Equal for both.
DEFAULT_K = 8

# The classes the repository shipped before this change. Used to reproduce the
# old gate exactly rather than approximating it.
FIXED_CLASSES = (
    "current_funding", "leadership", "multi_hop", "funders_of_project",
)


def _anchors(index: Any) -> dict[str, dict[str, Any]]:
    """Real entities from the live graph, so the benchmark is not fixture-bound.

    Picks, per type, the entity with the most claims **whose name the resolver
    can actually resolve from a question**. Both halves matter. Claim count is
    what makes the row counts meaningful; resolvability is what keeps the
    benchmark measuring routing rather than entity resolution.

    The first version skipped the second check and picked a project whose
    canonical name is a 90-character CMS title. It resolved from nothing, so
    eight temporal questions in a row reported "not routed" — a true statement
    about that name and a completely misleading one about the router.
    """
    from app.core.clients.graph import read_session
    from app.retrieval.graph import router

    picks: dict[str, dict[str, Any]] = {}
    label_for = {
        "ORGANIZATION": "Organization", "PROJECT": "Project", "PERSON": "Person",
    }
    with read_session() as session:
        for entity_type, label in label_for.items():
            candidates = session.run(
                f"MATCH (c:Claim)-[:SUBJECT|OBJECT]->(e:{label}) "
                "RETURN e.canonical_name AS name, count(*) AS n "
                "ORDER BY n DESC LIMIT 40"
            )
            for record in candidates:
                # Names in this corpus can carry trailing CMS markup.
                name = (
                    str(record["name"]).replace("\r", " ").replace("<br>", " ").strip()
                )
                if not name:
                    continue
                resolved, _, _ = router._resolve_entities(name, index)
                if any(d.entity_type == entity_type for d in resolved):
                    picks[entity_type] = {"name": name, "claims": record["n"]}
                    break
            else:
                logger.warning("No resolvable %s anchor found.", entity_type)
    return picks


def _questions(anchors: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """The benchmark set, grouped by what each group is evidence for."""
    org = anchors.get("ORGANIZATION", {}).get("name", "")
    person = anchors.get("PERSON", {}).get("name", "")
    project = anchors.get("PROJECT", {}).get("name", "")

    rows: list[dict[str, Any]] = []

    def add(section: str, question: str, expect_predicate: str | None = None):
        if not question:
            return
        rows.append(
            {"section": section, "question": question,
             "expect_predicate": expect_predicate}
        )

    # A. relational — one group per approved predicate, both directions
    add("relational", f"Which projects has {org} funded?", "FUNDED_BY")
    add("relational", f"Who funded {project}?", "FUNDED_BY")
    add("relational", f"Who led {project}?", "LED_BY")
    add("relational", f"What projects did {person} lead?", "LED_BY")
    add("relational", f"Who has {org} partnered with?", "PARTNER_OF")
    add("relational", f"Which organisations collaborated on {project}?", "PARTNER_OF")
    add("relational", f"Where does {person} work?", "WORKS_AT")
    add("relational", f"Who is employed by {org}?", "WORKS_AT")
    add("relational", f"Which committees is {person} a member of?", "MEMBER_OF")
    add("relational", f"What are the subsidiaries of {org}?", "PARENT_OF")
    add("relational", f"What is the designation of {person}?", "HAS_ROLE")

    # B. temporal — the same relationship asked for over different periods
    add("temporal", f"Who currently leads {project}?", "LED_BY")
    add("temporal", f"Who led {project} in 2010?", "LED_BY")
    add("temporal", f"Who led {project} between 2007 and 2012?", "LED_BY")
    add("temporal", f"Who led {project} after 2015?", "LED_BY")
    add("temporal", f"Who led {project} before 2010?", "LED_BY")
    add("temporal", f"Which projects has {org} funded since 2010?", "FUNDED_BY")
    add("temporal", f"What is the leadership history of {project}?", "LED_BY")
    add("temporal", f"Who led {project}?", "LED_BY")

    # C. old evidence — nothing may be unreachable for being old
    add("old", f"Which projects did {org} fund in 1999?", "FUNDED_BY")
    add("old", f"Which projects did {org} fund before 2005?", "FUNDED_BY")

    # D. multi-hop
    add("multi_hop", f"Who led the projects funded by {org}?", "FUNDED_BY")
    add("multi_hop", f"Who led the projects funded by {org} in 2010?", "FUNDED_BY")
    add("multi_hop", f"Who currently leads the projects funded by {org}?", "FUNDED_BY")

    # E. timeline
    add("timeline", f"What is the history of {org}?")
    add("timeline", f"What happened with {project} in 2010?")

    # F. must not route — the graph is not a topic index, and an unnamed
    #    subject is not an entity.
    add("declines", f"Tell me about {org}")
    add("declines", "Who funds climate research?")
    add("declines", "What is renewable energy?")

    return rows


def _run_one(question: str, *, index: Any, k: int) -> dict[str, Any]:
    from app.retrieval.graph import pipeline

    started = time.perf_counter()
    try:
        answer = pipeline.answer(question, index=index, top_k=k)
    except Exception as exc:  # pragma: no cover - a benchmark must not stop
        return {"error": f"{type(exc).__name__}: {exc}", "elapsed_ms":
                (time.perf_counter() - started) * 1000}
    elapsed = (time.perf_counter() - started) * 1000
    route = answer.route
    result = answer.result
    return {
        "routed": route is not None,
        "template_id": getattr(route, "template_id", None),
        "mode": getattr(route, "mode", None),
        "query_class": getattr(route, "query_class", "") or None,
        "predicates": list(getattr(route, "predicates", ()) or ()),
        "rows": len(result.rows) if result else 0,
        "hydrated": answer.hydrated,
        "blocks": len(answer.blocks),
        "answered": bool(answer.blocks),
        "error": result.error if result else None,
        "elapsed_ms": elapsed,
        "stage_ms": dict(answer.stage_ms),
        "reason": answer.reason,
    }


def _run_config(
    questions: list[dict[str, Any]], *, config: str, index: Any, k: int
) -> list[dict[str, Any]]:
    """One configuration over the whole question set.

    ``fixed`` is reproduced by disabling the schema-aware planner and gating on
    the four classes that used to ship, which is exactly what the old code did:
    the pattern table chose a template and the class list decided whether it was
    allowed. Nothing else is changed, so the comparison isolates routing.
    """
    from app.retrieval.graph import policy, router

    original_plan = router._plan_route
    try:
        if config == "fixed":
            router._plan_route = lambda *a, **kw: None
        out = []
        for row in questions:
            measured = _run_one(row["question"], index=index, k=k)
            if config == "fixed" and measured.get("routed"):
                # The old gate, applied after routing exactly as it was.
                template_class = policy.class_of(measured["template_id"])
                if template_class not in FIXED_CLASSES:
                    measured = {
                        **measured, "routed": True, "answered": False,
                        "rows": 0, "hydrated": 0, "blocks": 0,
                        "gated_out": True,
                        "reason": f"class {template_class!r} not enabled",
                    }
            out.append({**row, **measured, "config": config})
        return out
    finally:
        router._plan_route = original_plan


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graded = [r for r in rows if r["section"] != "declines"]
    declines = [r for r in rows if r["section"] == "declines"]
    latencies = [r["elapsed_ms"] for r in rows if "elapsed_ms" in r]
    predicates: set[str] = set()
    for row in graded:
        predicates.update(row.get("predicates") or [])

    def _frac(subset, key):
        return round(sum(1 for r in subset if r.get(key)) / len(subset), 3) if subset else 0.0

    # A question that routed and came back empty is the graph correctly saying
    # "the corpus records no such relationship". Counting it alongside the
    # questions that could not be asked at all would hide exactly the
    # distinction this change is about, so it gets its own number.
    #
    # Computed before the per-section tally below, which reads it.
    for row in graded:
        row["zero_result"] = bool(
            row.get("routed") and not row.get("answered")
            and not row.get("gated_out") and not row.get("error")
        )

    by_section: dict[str, dict[str, Any]] = {}
    for row in graded:
        bucket = by_section.setdefault(
            row["section"],
            {"n": 0, "routed": 0, "answered": 0, "zero": 0, "rows": 0},
        )
        bucket["n"] += 1
        bucket["routed"] += int(bool(row.get("routed")))
        bucket["answered"] += int(bool(row.get("answered")))
        bucket["zero"] += int(bool(row.get("zero_result")))
        bucket["rows"] += row.get("rows", 0)

    return {
        "questions": len(graded),
        "routed": _frac(graded, "routed"),
        "answered": _frac(graded, "answered"),
        "zero_result": _frac(graded, "zero_result"),
        "total_rows": sum(r.get("rows", 0) for r in graded),
        "total_hydrated": sum(r.get("hydrated", 0) for r in graded),
        "predicates_reached": sorted(predicates),
        "correctly_declined": _frac(
            [{"ok": not r.get("routed")} for r in declines], "ok"
        ),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 1) if latencies else 0.0,
            "median": round(statistics.median(latencies), 1) if latencies else 0.0,
            "max": round(max(latencies), 1) if latencies else 0.0,
        },
        "by_section": by_section,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--section", help="run only one section")
    parser.add_argument("--json", dest="json_path", help="write the full report")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.ERROR,
        format="%(message)s",
    )
    logging.getLogger("neo4j").setLevel(logging.ERROR)

    from app.retrieval.graph import plans, policy

    index = policy.entity_index()
    anchors = _anchors(index)
    if not anchors:
        print("No entities in the graph; nothing to benchmark.", file=sys.stderr)
        return 1

    questions = _questions(anchors)
    if args.section:
        questions = [q for q in questions if q["section"] == args.section]
    if not questions:
        print(f"No questions in section {args.section!r}.", file=sys.stderr)
        return 1

    print("Anchors")
    for entity_type, info in sorted(anchors.items()):
        print(f"  {entity_type:13s} {info['name'][:58]:60s} {info['claims']:4d} claims")

    coverage = plans.coverage()
    unaskable = [
        name for name, info in coverage["predicates"].items() if not info["askable"]
    ]
    print(f"\nApproved predicates : {len(coverage['predicates'])}")
    print(f"Queryable           : {len(coverage['queryable'])}")
    if unaskable:
        print(f"  NOT ASKABLE       : {', '.join(unaskable)}")

    results: dict[str, Any] = {}
    for config in ("fixed", "schema"):
        rows = _run_config(questions, config=config, index=index, k=args.k)
        results[config] = {"summary": _summarize(rows), "rows": rows}

    print(f"\n{'':22s} {'fixed':>12s} {'schema':>12s}")
    print("-" * 48)
    fixed, schema = results["fixed"]["summary"], results["schema"]["summary"]
    for label, key in (
        ("routed", "routed"), ("answered", "answered"),
        ("routed, 0 rows", "zero_result"),
        ("correctly declined", "correctly_declined"),
    ):
        print(f"{label:22s} {fixed[key]:>12.3f} {schema[key]:>12.3f}")
    for label, key in (("graph rows", "total_rows"),
                       ("evidence chunks", "total_hydrated")):
        print(f"{label:22s} {fixed[key]:>12d} {schema[key]:>12d}")
    print(f"{'predicates reached':22s} {len(fixed['predicates_reached']):>12d} "
          f"{len(schema['predicates_reached']):>12d}")
    for stat in ("mean", "median", "max"):
        print(f"{'latency ' + stat + ' (ms)':22s} "
              f"{fixed['latency_ms'][stat]:>12.1f} {schema['latency_ms'][stat]:>12.1f}")

    print(f"\n{'section':12s} {'n':>3s} {'fixed r/a':>12s} {'schema r/a':>12s} {'0 rows':>7s}")
    print("-" * 52)
    for section in sorted(schema["by_section"]):
        f = fixed["by_section"].get(
            section, {"routed": 0, "answered": 0, "n": 0, "zero": 0}
        )
        s = schema["by_section"][section]
        print(f"{section:12s} {s['n']:>3d} "
              f"{str(f['routed']) + '/' + str(f['answered']):>12s} "
              f"{str(s['routed']) + '/' + str(s['answered']):>12s}"
              f" {s.get('zero', 0):>7d}")

    print(f"\nPredicates reached (schema): "
          f"{', '.join(schema['predicates_reached']) or 'none'}")
    print(f"Predicates reached (fixed) : "
          f"{', '.join(fixed['predicates_reached']) or 'none'}")

    if args.verbose:
        print("\nPer question (schema):")
        for row in results["schema"]["rows"]:
            mark = "ok " if row.get("answered") else ("rt " if row.get("routed") else "-- ")
            print(f"  {mark}{row['question'][:66]:68s} "
                  f"{str(row.get('template_id')):24s} rows={row.get('rows', 0):3d} "
                  f"{row.get('elapsed_ms', 0):6.0f}ms")

    if args.json_path:
        from pathlib import Path

        payload = {
            "anchors": anchors, "coverage": coverage,
            "k": args.k, "results": results,
        }
        path = Path(args.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"\nWrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
