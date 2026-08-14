"""Compare existing retrieval against graph retrieval on relational questions.

Answers one question: **on which query classes does the graph beat the retrieval
we already have** — and by enough to justify routing to it.

Configurations
    existing    the production pull: `app.retrieval.hybrid_search.search`,
                optionally RRF-fused with the keyword leg. This is what a user
                gets today.
    graph       `app.retrieval.graph.pipeline.answer`: route, traverse, hydrate
                from Qdrant, then the *same* reranker and context builder.

Both end at context blocks, so the comparison is between two ways of filling a
prompt rather than between a database and a search engine.

Metrics
-------
`answer_coverage` is the headline, and the only one that compares the two
methods fairly.

    answer_coverage   fraction of gold answer entities (the PIs, the projects)
                      whose name appears in the retrieved context. This is what
                      "could a model answer from this?" reduces to, and neither
                      method is given an advantage in computing it.
    evidence_recall   fraction of gold evidence documents present in the result.
                      **Tautological for the graph** — the gold documents are
                      the ones its own claims cite — and reported only to show
                      what the existing pull does on the same question.
    evidence_precision
                      fraction of returned blocks that are gold evidence. Low is
                      not automatically bad: a document can be relevant without
                      being the field that recorded the fact.
    citation_validity fraction of cited chunk/document ids that Qdrant can still
                      resolve. Catches a graph citing text that no longer exists.
    route_precision   of the questions that routed, the fraction that should
                      have (1 - false routing).
    route_recall      of the questions that should route, the fraction that did
                      (1 - missed routing).
    latency           wall clock per query, per configuration.

    python -m scripts.eval_graph_retrieval
    python -m scripts.eval_graph_retrieval --class multi_hop
    python -m scripts.eval_graph_retrieval --k 10 --json out.json
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("eval_graph_retrieval")

_QUERIES = Path("reports/knowledge/graph_queries_v1.json")

# Blocks each configuration is allowed to put in front of the model. Both get
# the same budget, so a coverage difference is a difference in what was found.
DEFAULT_K = 8

# A gold name counts as covered if it appears in the context. Matching is on
# normalized text with honorifics dropped, because "Dr Alok Adholeya" in a field
# and "Alok Adholeya" in prose are the same person and pretending otherwise
# would flatter neither method honestly.
_HONORIFIC = re.compile(
    r"^(?:dr|mr|ms|mrs|prof|professor|shri|smt)\.?\s+", re.IGNORECASE
)
_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", (text or "").lower()).strip()


def _name_variants(name: str) -> list[str]:
    """The forms of a gold name that should count as a hit."""
    base = _normalize(name)
    variants = {base}
    stripped = _HONORIFIC.sub("", base).strip()
    if stripped:
        variants.add(stripped)
    return [v for v in variants if len(v) >= 6]


def _blocks_text(blocks: list[Any]) -> str:
    parts: list[str] = []
    for block in blocks:
        payload = getattr(block, "payload", None) or {}
        for key in ("title", "document_title", "chunk_text", "text", "content"):
            value = payload.get(key)
            if isinstance(value, str):
                parts.append(value)
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    return _normalize(" \n ".join(parts))


def _coverage(blocks: list[Any], gold_names: list[str]) -> float:
    if not gold_names:
        return 1.0
    haystack = _blocks_text(blocks)
    hits = sum(
        1 for name in gold_names
        if any(v in haystack for v in _name_variants(name))
    )
    return hits / len(gold_names)


def _documents_of(blocks: list[Any]) -> list[str]:
    out = []
    for block in blocks:
        payload = getattr(block, "payload", None) or {}
        document_id = payload.get("document_id")
        if document_id and document_id not in out:
            out.append(document_id)
    return out


def _citation_validity(answer: Any) -> float | None:
    """Fraction of the ids a graph answer cites that still resolve.

    A fact in a prompt is only checkable if its citation leads somewhere. This
    catches a graph asserting a claim against a document Qdrant no longer holds
    — the failure re-indexing produces, and the one a reader cannot detect.
    """
    result = getattr(answer, "result", None)
    if result is None or not result.rows:
        return None
    from app.retrieval.graph import hydrate as hydration

    cited = list(result.chunk_ids) + list(result.document_ids)
    if not cited:
        return None
    resolved = set()
    for candidate in hydration.hydrate_chunks(result.chunk_ids):
        resolved.add(candidate.id)
    for candidate in hydration.hydrate_documents(
        result.document_ids, per_document=1
    ):
        document_id = (candidate.payload or {}).get("document_id")
        if document_id:
            resolved.add(document_id)
    # Only the documents hydration was allowed to look at can be judged.
    judged = list(result.chunk_ids) + list(result.document_ids)[
        : hydration.MAX_DOCUMENTS
    ]
    if not judged:
        return None
    return sum(1 for c in judged if c in resolved) / len(judged)


def _prf(retrieved: list[str], gold: list[str]) -> tuple[float, float]:
    if not gold:
        return (1.0, 1.0 if not retrieved else 0.0)
    gold_set, retrieved_set = set(gold), set(retrieved)
    overlap = len(gold_set & retrieved_set)
    recall = overlap / len(gold_set)
    precision = overlap / len(retrieved_set) if retrieved_set else 0.0
    return recall, precision


# --------------------------------------------------------------------------- #
# Configurations
# --------------------------------------------------------------------------- #


def run_existing(query: str, *, k: int) -> dict[str, Any]:
    """The production pull, ending in the same context builder the graph uses."""
    from app.config import get_settings
    from app.retrieval.context_builder import build_context
    from app.retrieval.hybrid_search import search
    from app.retrieval.reranker import rerank

    settings = get_settings()
    started = time.perf_counter()
    candidates = search(query, limit=settings.retrieval_candidate_k)
    ranked = rerank(query, candidates) if candidates else []
    blocks = build_context(ranked, limit=k, segregate=False) if ranked else []
    return {
        "blocks": blocks,
        "elapsed_ms": (time.perf_counter() - started) * 1000,
        "routed": None,
    }


def run_graph(query: str, *, k: int, index: Any) -> dict[str, Any]:
    from app.retrieval.graph import pipeline

    started = time.perf_counter()
    answer = pipeline.answer(query, index=index, top_k=k)
    return {
        "blocks": answer.blocks,
        "elapsed_ms": (time.perf_counter() - started) * 1000,
        "routed": answer.route is not None,
        "answer": answer,
    }


def run_routed(query: str, *, k: int, allowed: tuple[str, ...]) -> dict[str, Any]:
    """Production as Phase 11 ships it: the graph for enabled classes, existing
    retrieval for everything else and for every graph outcome that is not a
    useful answer.

    This is the configuration a user would experience, so it is the one that
    should decide whether a class is worth enabling — a class the graph declines
    half the time still scores well here if the fallback covers it.
    """
    from app.retrieval.graph import policy

    started = time.perf_counter()
    attempt = policy.attempt(query, top_k=k, settings=_RoutingSettings(allowed))
    if attempt.used:
        return {
            "blocks": attempt.blocks,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "source": "graph", "outcome": attempt.outcome,
            "class": attempt.query_class,
        }
    existing = run_existing(query, k=k)
    return {
        "blocks": existing["blocks"],
        "elapsed_ms": (time.perf_counter() - started) * 1000,
        "source": "fallback", "outcome": attempt.outcome,
        "class": attempt.query_class,
    }


class _RoutingSettings:
    """A settings stand-in so one run can evaluate one class set."""

    def __init__(self, allowed: tuple[str, ...]):
        self.graph_routing_enabled = True
        self.graph_routing_classes = ",".join(allowed)
        self.graph_routing_budget_seconds = 15.0


# --------------------------------------------------------------------------- #


def evaluate(
    queries: list[dict[str, Any]], *, k: int,
    routed_classes: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    from app.knowledge.candidates import EntityIndex

    index = EntityIndex.load()
    results = []
    for spec in queries:
        gold_names = [e["name"] for e in spec["expected_answer_entities"]]
        gold_documents = spec["expected_evidence_documents"]

        row: dict[str, Any] = {
            "id": spec["id"], "class": spec["class"], "query": spec["query"],
            "should_route": spec["should_route"],
            "gold_answers": len(gold_names),
        }

        existing = run_existing(spec["query"], k=k)
        recall, precision = _prf(_documents_of(existing["blocks"]), gold_documents)
        row["existing"] = {
            "blocks": len(existing["blocks"]),
            "answer_coverage": _coverage(existing["blocks"], gold_names),
            "evidence_recall": recall, "evidence_precision": precision,
            "latency_ms": existing["elapsed_ms"],
        }

        graph = run_graph(spec["query"], k=k, index=index)
        answer = graph["answer"]
        recall, precision = _prf(_documents_of(graph["blocks"]), gold_documents)
        route = answer.route
        row["graph"] = {
            "blocks": len(graph["blocks"]),
            "answer_coverage": _coverage(graph["blocks"], gold_names),
            "evidence_recall": recall, "evidence_precision": precision,
            "latency_ms": graph["elapsed_ms"],
            "routed": graph["routed"],
            "template": route.template_id if route else None,
            "mode": route.mode if route else None,
            "rows": len(answer.result.rows) if answer.result else 0,
            "reason": answer.reason,
            "disputed": answer.disputed,
            "facts_block": answer.facts,
            "citation_validity": _citation_validity(answer),
        }
        if routed_classes is not None:
            routed = run_routed(spec["query"], k=k, allowed=routed_classes)
            row["routed_system"] = {
                "blocks": len(routed["blocks"]),
                "answer_coverage": _coverage(routed["blocks"], gold_names),
                "latency_ms": routed["elapsed_ms"],
                "source": routed["source"], "outcome": routed["outcome"],
                "class": routed["class"],
            }

        row["route_correct"] = graph["routed"] == spec["should_route"]
        row["template_correct"] = (
            route.template_id == spec["expected_template"] if route
            else spec["expected_template"] is None
        )
        results.append(row)
    return results


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, list[dict[str, Any]]] = {}
    for row in results:
        by_class.setdefault(row["class"], []).append(row)

    classes = {}
    for name, rows in sorted(by_class.items()):
        classes[name] = {
            "n": len(rows),
            "existing_coverage": _mean([r["existing"]["answer_coverage"] for r in rows]),
            "graph_coverage": _mean([r["graph"]["answer_coverage"] for r in rows]),
            "existing_evidence_recall": _mean(
                [r["existing"]["evidence_recall"] for r in rows]
            ),
            "graph_evidence_recall": _mean(
                [r["graph"]["evidence_recall"] for r in rows]
            ),
            "existing_latency_ms": _mean([r["existing"]["latency_ms"] for r in rows]),
            "graph_latency_ms": _mean([r["graph"]["latency_ms"] for r in rows]),
            "route_correct": sum(r["route_correct"] for r in rows),
            "routed_coverage": (
                _mean([r["routed_system"]["answer_coverage"] for r in rows])
                if "routed_system" in rows[0] else None
            ),
            "routed_latency_ms": (
                _mean([r["routed_system"]["latency_ms"] for r in rows])
                if "routed_system" in rows[0] else None
            ),
            "graph_used": sum(
                1 for r in rows
                if r.get("routed_system", {}).get("source") == "graph"
            ),
            # None, not 0.0, when nothing was cited: a class that correctly
            # declines to answer has no citations to be wrong about, and
            # scoring it zero would read as a failure.
            "citation_validity": (
                _mean(judged) if (judged := [
                    r["graph"]["citation_validity"] for r in rows
                    if r["graph"]["citation_validity"] is not None
                ]) else None
            ),
        }

    should = [r for r in results if r["should_route"]]
    should_not = [r for r in results if not r["should_route"]]
    routed = [r for r in results if r["graph"]["routed"]]
    false_routes = [r for r in should_not if r["graph"]["routed"]]
    missed_routes = [r for r in should if not r["graph"]["routed"]]

    outcomes: dict[str, int] = {}
    for row in results:
        outcome = row.get("routed_system", {}).get("outcome")
        if outcome:
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

    return {
        "classes": classes,
        "outcomes": outcomes,
        "routing": {
            "should_route": len(should),
            "should_not_route": len(should_not),
            "routed": len(routed),
            "false_routes": [r["id"] for r in false_routes],
            "missed_routes": [r["id"] for r in missed_routes],
            "precision": (len(routed) - len(false_routes)) / len(routed) if routed else 1.0,
            "recall": (len(should) - len(missed_routes)) / len(should) if should else 1.0,
            "template_correct": sum(r["template_correct"] for r in results),
            "total": len(results),
        },
    }


def _print(results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    print("\nPer query (answer coverage: fraction of gold answers named in context)\n")
    header = f"{'id':11} {'class':19} {'gold':>5} {'existing':>9} {'graph':>7}  route"
    print(header)
    print("-" * len(header))
    for row in results:
        mark = "ok " if row["route_correct"] else "BAD"
        routed = "routed" if row["graph"]["routed"] else "declined"
        print(
            f"{row['id']:11} {row['class']:19} {row['gold_answers']:5d} "
            f"{row['existing']['answer_coverage']:9.2f} "
            f"{row['graph']['answer_coverage']:7.2f}  {mark} {routed}"
        )

    print("\nBy class\n")
    header = (
        f"{'class':19} {'n':>3} {'exist cov':>10} {'graph cov':>10} "
        f"{'cite ok':>8} {'exist ms':>9} {'graph ms':>9}"
    )
    print(header)
    print("-" * len(header))
    for name, stats in summary["classes"].items():
        citation = stats["citation_validity"]
        citation_text = f"{citation:8.2f}" if citation is not None else f"{'-':>8}"
        print(
            f"{name:19} {stats['n']:3d} {stats['existing_coverage']:10.2f} "
            f"{stats['graph_coverage']:10.2f} {citation_text} "
            f"{stats['existing_latency_ms']:9.0f} {stats['graph_latency_ms']:9.0f}"
        )

    if summary.get("outcomes"):
        print(
            "\nRouted system "
            "(graph where enabled, existing retrieval otherwise)\n"
        )
        header = (
            f"{'class':19} {'n':>3} {'existing':>9} {'routed':>8} "
            f"{'graph used':>11} {'routed ms':>10}"
        )
        print(header)
        print("-" * len(header))
        for name, stats in summary["classes"].items():
            if stats.get("routed_coverage") is None:
                continue
            print(
                f"{name:19} {stats['n']:3d} {stats['existing_coverage']:9.2f} "
                f"{stats['routed_coverage']:8.2f} "
                f"{stats['graph_used']:>4}/{stats['n']:<6} "
                f"{stats['routed_latency_ms']:10.0f}"
            )
        print("\nOutcomes: " + ", ".join(
            f"{name}={count}" for name, count in
            sorted(summary["outcomes"].items(), key=lambda kv: -kv[1])
        ))

    routing = summary["routing"]
    print(
        f"\nRouting  precision={routing['precision']:.2f} "
        f"recall={routing['recall']:.2f}  "
        f"template correct {routing['template_correct']}/{routing['total']}"
    )
    if routing["false_routes"]:
        print(f"  false routes:  {routing['false_routes']}")
    if routing["missed_routes"]:
        print(f"  missed routes: {routing['missed_routes']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--class", dest="klass", help="evaluate one class only")
    parser.add_argument("--json", type=Path, help="write machine-readable results")
    parser.add_argument("--queries", type=Path, default=_QUERIES)
    parser.add_argument(
        "--routed", action="store_true",
        help="also evaluate the routed production system (graph + fallback)",
    )
    parser.add_argument(
        "--classes",
        help="comma-separated classes to enable for --routed (default: policy default)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING)
    payload = json.loads(args.queries.read_text(encoding="utf-8"))
    queries = payload["queries"]
    if args.klass:
        queries = [q for q in queries if q["class"] == args.klass]
    if not queries:
        print("No queries selected.", file=sys.stderr)
        return 2

    routed_classes = None
    if args.routed:
        from app.retrieval.graph import policy

        routed_classes = (
            tuple(c.strip() for c in args.classes.split(",") if c.strip())
            if args.classes else policy.DEFAULT_ENABLED_CLASSES
        )
        print(f"Routed configuration enables: {', '.join(routed_classes)}")
    results = evaluate(queries, k=args.k, routed_classes=routed_classes)
    summary = summarize(results)
    _print(results, summary)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {"k": args.k, "summary": summary, "results": results},
                indent=2, ensure_ascii=False, default=str,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
