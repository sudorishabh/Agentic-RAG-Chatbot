"""Offline eval runner over the golden dataset.

Feeds scripts/eval/golden.jsonl through the live pipeline (Azure OpenAI +
read-only Qdrant/MySQL) and scores each class: routing accuracy per field,
analytics numbers vs independent SQL (must be 100%), retrieval recall@k/MRR,
generation content/shape/citations, refusal correctness. Emits a JSON results
file plus a markdown summary with per-stage p50/p95 latencies.

Response and semantic caches are disabled in this process only — eval always
measures fresh answers; production defaults are untouched. Refuses to start
when MySQL or Qdrant is unreachable. Do not run during an active ingestion
run: reads are safe, but scores built on a shifting corpus are meaningless.

Usage:
  python -m scripts.eval.run_eval [--only CLASS] [--ids id1,id2]
                                  [--out results.json] [--baseline results.json]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("run_eval")

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN = EVAL_DIR / "golden.jsonl"
RESULTS_DIR = EVAL_DIR / "results"

_CLASSES = ("routing", "analytics", "retrieval", "generation", "unanswerable")


# --------------------------------------------------------------------------- #
# Environment guards.
# --------------------------------------------------------------------------- #

def _preflight() -> list[str]:
    problems: list[str] = []
    try:
        from app.deps import mysql_connection

        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as exc:
        problems.append(f"MySQL unreachable: {exc}")
    try:
        from app.config import get_settings
        from app.deps import get_qdrant_client

        if not get_qdrant_client().collection_exists(get_settings().qdrant_collection):
            problems.append("Qdrant reachable but the documents collection is missing")
    except Exception as exc:
        problems.append(f"Qdrant unreachable: {exc}")
    return problems


def _disable_caches() -> None:
    """Fresh answers only: no-op the response/semantic cache reads AND writes
    in this process (eval must not serve from or pollute production caches).
    The embedding cache stays on — embeddings are deterministic."""
    from app.cache import redis_cache, semantic_cache

    redis_cache.get_response = lambda signature: None          # type: ignore[assignment]
    redis_cache.set_response = lambda signature, result: None  # type: ignore[assignment]
    semantic_cache.lookup = lambda *a, **k: None               # type: ignore[assignment]
    semantic_cache.store = lambda *a, **k: None                # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Shared answer execution with stage timing.
# --------------------------------------------------------------------------- #

def _answer_with_stages(
    question: str,
) -> tuple[dict[str, Any], list[str], dict[str, float], float]:
    # Rebuilds the buffered answer flow from _prepare/_grounded_answer/_assemble:
    # a wrapper's own collect_into would shadow the runner's stage dict, and the
    # judges need the context block texts, which the assembled result doesn't
    # carry. Cache persistence is skipped (no-op'd here anyway).
    import app.rag as rag
    from app.observability.metrics import collect_into

    stages: dict[str, float] = {}
    block_texts: list[str] = []
    start = time.perf_counter()
    with collect_into(stages):
        result, gen = rag._prepare(
            question, history=None, tenant_id="default", user_groups=None, top_k=None
        )
        if result is None:
            answer = rag._grounded_answer(
                gen.pq.search_query, gen.blocks, answer_format=gen.pq.answer_format
            )
            result = rag._assemble(answer, gen)
            block_texts = [b.text for b in gen.blocks]
    return result, block_texts, stages, (time.perf_counter() - start) * 1000.0


def _value_in_answer(value: str, answer: str) -> bool:
    """Word-boundary match for pure numbers (so count 0 can't ride on '2020');
    case-insensitive substring otherwise."""
    if re.fullmatch(r"\d+", value):
        return re.search(rf"\b{re.escape(value)}\b", answer) is not None
    return value.lower() in answer.lower()


def _format_ok(fmt: str, answer: str) -> bool:
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    if fmt == "table":
        has_row = any(l.startswith("|") and l.endswith("|") for l in lines)
        has_separator = any(set(l) <= set("|-: ") and "-" in l for l in lines)
        return has_row and has_separator
    if fmt == "timeline":
        dated = [l for l in lines if re.search(r"\b(19|20)\d{2}\b", l)]
        return len(dated) >= 2
    if fmt == "summary":
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
        return len(sentences) <= 6
    return True


# --------------------------------------------------------------------------- #
# Per-class item runners. Each returns (checks, extras, latency_ms, stages).
# --------------------------------------------------------------------------- #

def _routing_actual(pq: Any, field: str) -> Any:
    if field == "intent":
        return pq.intent
    if field == "answer_format":
        return pq.answer_format
    if field == "source_type":
        return pq.source_type
    slot = {
        "theme_contains": "theme",
        "author_contains": "author",
        "title_contains_ci": "title_contains",
    }.get(field, field)
    return getattr(pq.analysis, slot, None) if pq.analysis is not None else None


def _run_routing(item: dict) -> tuple[dict[str, bool], dict, float, dict]:
    from app.retrieval.query_processor import process

    start = time.perf_counter()
    pq = process(item["question"])
    latency = (time.perf_counter() - start) * 1000.0

    checks: dict[str, bool] = {}
    got: dict[str, Any] = {}
    for field, expected in item["expect"].items():
        actual = _routing_actual(pq, field)
        got[field] = actual
        if field.endswith("_contains") or field.endswith("_ci"):
            checks[field] = str(expected).lower() in str(actual or "").lower()
        else:
            checks[field] = actual is not None and str(actual).lower() == str(expected).lower()
    return checks, {"got": got}, latency, {}


def _sql_expected(check: dict) -> tuple[list[str], str]:
    """Independently execute the item's SQL expectation; returns the strings
    the answer must contain plus a human-readable note."""
    from app.ingestion import state

    kwargs = dict(check["kwargs"])
    for key in ("published_from", "published_to"):
        if kwargs.get(key):
            kwargs[key] = datetime.fromisoformat(kwargs[key])
    fn = check["fn"]
    if fn == "count_documents":
        total = state.count_documents(source_type="website", entity_type="node", **kwargs)
        return [str(total)], f"count={total}"
    if fn == "distribution":
        group_by = kwargs.pop("group_by")
        rows = state.distribution(
            group_by, source_type="website", entity_type="node", **kwargs
        )[:3]
        values = [str(v) for v, _ in rows] + [str(n) for _, n in rows]
        return values, f"top3={rows}"
    records = state.list_documents(source_type="website", entity_type="node", **kwargs)
    if not records:
        return [], "sql returned no rows (corpus changed?)"
    title = records[0].title or records[0].document_id
    return [title], f"most_recent={title!r}"


def _run_analytics(item: dict) -> tuple[dict[str, bool], dict, float, dict]:
    result, _, stages, latency = _answer_with_stages(item["question"])
    answer = result.get("answer", "")
    expected_values, sql_note = _sql_expected(item["expect"]["sql_check"])
    checks = {
        "intent": result.get("intent") == item["expect"].get("intent", "structured"),
        "sql_values_in_answer": bool(expected_values)
        and all(_value_in_answer(v, answer) for v in expected_values),
    }
    return checks, {"sql": sql_note, "answer": answer[:400]}, latency, stages


def _run_retrieval(item: dict) -> tuple[dict[str, bool], dict, float, dict]:
    from app.observability.metrics import collect_into
    from app.rag import search_blocks

    stages: dict[str, float] = {}
    start = time.perf_counter()
    with collect_into(stages):
        res = search_blocks(item["question"])
    latency = (time.perf_counter() - start) * 1000.0

    got_ids = [b["document_id"] for b in res["blocks"]]
    relevant = set(item["expect"]["relevant_document_ids"])
    found = {d for d in got_ids if d in relevant}
    recall = len(found) / len(relevant)
    first_hit = next((i for i, d in enumerate(got_ids, 1) if d in relevant), None)
    extras = {
        "recall": round(recall, 3),
        "mrr": round(1.0 / first_hit, 3) if first_hit else 0.0,
        "website_lead": bool(res["blocks"])
        and res["blocks"][0]["source_type"] == "website",
        "k": len(got_ids),
    }
    return {"recall_full": recall == 1.0}, extras, latency, stages


def _run_generation(item: dict) -> tuple[dict[str, bool], dict, float, dict]:
    from app.generation.prompts import REFUSAL
    from scripts.eval.judges import citation_coverage, judge_faithfulness, judge_relevance

    result, block_texts, stages, latency = _answer_with_stages(item["question"])
    answer = result.get("answer", "")
    expect = item["expect"]
    checks: dict[str, bool] = {"answered": answer != REFUSAL}
    for s in expect.get("must_contain", []):
        checks[f"contains:{s}"] = s.lower() in answer.lower()
    for s in expect.get("must_not_contain", []):
        checks[f"not_contains:{s}"] = s.lower() not in answer.lower()
    if expect.get("format"):
        checks[f"format:{expect['format']}"] = _format_ok(expect["format"], answer)
    if expect.get("citations_required"):
        checks["citations"] = re.search(r"\[\d+\]", answer) is not None

    # Judged metrics are reported, not pass/fail gates — LLM judges are noisy;
    # deterministic assertions above decide pass/fail.
    extras: dict[str, Any] = {"answer": answer[:400]}
    if checks["answered"]:
        extras["citation_coverage"] = round(citation_coverage(answer), 3)
        report = judge_faithfulness(answer, block_texts)
        if report is not None:
            extras["faithful"] = report["faithful"]
            extras["claim_support_rate"] = report["rate"]
            extras["claims_checked"] = report["total"]
        relevance = judge_relevance(item["question"], answer)
        if relevance is not None:
            extras["relevance"] = relevance
    return checks, extras, latency, stages


def _run_unanswerable(item: dict) -> tuple[dict[str, bool], dict, float, dict]:
    from app.generation.prompts import REFUSAL

    result, _, stages, latency = _answer_with_stages(item["question"])
    answer = result.get("answer", "")
    return {"refusal": answer == REFUSAL}, {"answer": answer[:200]}, latency, stages


_RUNNERS = {
    "routing": _run_routing,
    "analytics": _run_analytics,
    "retrieval": _run_retrieval,
    "generation": _run_generation,
    "unanswerable": _run_unanswerable,
}


# --------------------------------------------------------------------------- #
# Aggregation and reporting.
# --------------------------------------------------------------------------- #

def _pctl(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))]


def _aggregate(items: list[dict]) -> dict[str, Any]:
    classes: dict[str, Any] = {}
    for cls in _CLASSES:
        rows = [i for i in items if i["class"] == cls]
        if not rows:
            continue
        entry: dict[str, Any] = {
            "total": len(rows),
            "passed": sum(1 for r in rows if r["passed"]),
        }
        entry["score"] = round(entry["passed"] / entry["total"], 3)
        if cls == "routing":
            fields: dict[str, list[bool]] = {}
            for r in rows:
                for field, ok in r["checks"].items():
                    fields.setdefault(field, []).append(ok)
            entry["field_accuracy"] = {
                f: round(sum(v) / len(v), 3) for f, v in sorted(fields.items())
            }
        if cls == "retrieval":
            entry["mean_recall"] = round(
                sum(r["extras"]["recall"] for r in rows) / len(rows), 3
            )
            entry["mean_mrr"] = round(
                sum(r["extras"]["mrr"] for r in rows) / len(rows), 3
            )
            entry["website_lead_rate"] = round(
                sum(1 for r in rows if r["extras"]["website_lead"]) / len(rows), 3
            )
        if cls == "generation":
            judged = [r for r in rows if "claim_support_rate" in r["extras"]]
            if judged:
                entry["faithful_rate"] = round(
                    sum(1 for r in judged if r["extras"]["faithful"]) / len(judged), 3
                )
                entry["mean_claim_support"] = round(
                    sum(r["extras"]["claim_support_rate"] for r in judged) / len(judged), 3
                )
            scored = [r["extras"]["relevance"] for r in rows if "relevance" in r["extras"]]
            if scored:
                entry["mean_relevance"] = round(sum(scored) / len(scored), 2)
            covered = [
                r["extras"]["citation_coverage"]
                for r in rows
                if "citation_coverage" in r["extras"]
            ]
            if covered:
                entry["mean_citation_coverage"] = round(sum(covered) / len(covered), 3)
        classes[cls] = entry
    return classes


def _aggregate_stages(items: list[dict]) -> dict[str, dict[str, float]]:
    samples: dict[str, list[float]] = {}
    for item in items:
        for stage, ms in (item.get("stages") or {}).items():
            samples.setdefault(stage, []).append(ms)
    return {
        stage: {
            "count": len(vals),
            "p50_ms": round(_pctl(vals, 0.50), 1),
            "p95_ms": round(_pctl(vals, 0.95), 1),
        }
        for stage, vals in sorted(samples.items())
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [f"# Eval run — {report['run_at']}", ""]
    lines += ["| class | passed | total | score |", "| --- | --- | --- | --- |"]
    for cls, e in report["classes"].items():
        lines.append(f"| {cls} | {e['passed']} | {e['total']} | {e['score']} |")
    retrieval = report["classes"].get("retrieval")
    if retrieval:
        lines += ["", f"Retrieval: recall={retrieval['mean_recall']} "
                      f"MRR={retrieval['mean_mrr']} "
                      f"website-lead={retrieval['website_lead_rate']}"]
    routing = report["classes"].get("routing")
    if routing:
        lines += ["", "Routing field accuracy: "
                  + ", ".join(f"{f}={a}" for f, a in routing["field_accuracy"].items())]
    generation = report["classes"].get("generation")
    if generation:
        judged_bits = [
            f"{k}={generation[k]}"
            for k in ("faithful_rate", "mean_claim_support", "mean_relevance",
                      "mean_citation_coverage")
            if k in generation
        ]
        if judged_bits:
            lines += ["", "Generation judges: " + ", ".join(judged_bits)]
    lines += ["", "## Stage latencies", "", "| stage | n | p50 ms | p95 ms |",
              "| --- | --- | --- | --- |"]
    for stage, s in report["stages"].items():
        lines.append(f"| {stage} | {s['count']} | {s['p50_ms']} | {s['p95_ms']} |")
    failures = [i for i in report["items"] if not i["passed"]]
    lines += ["", f"## Failures ({len(failures)})", ""]
    for f in failures:
        failed = [name for name, ok in f["checks"].items() if not ok] or ["error"]
        note = f.get("error") or ", ".join(failed)
        lines.append(f"- `{f['id']}` ({f['class']}): {note}")
    return "\n".join(lines) + "\n"


def _print_baseline_diff(report: dict[str, Any], baseline_path: Path) -> None:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    print(f"\n== Deltas vs {baseline_path.name} ==")
    for cls, e in report["classes"].items():
        old = baseline.get("classes", {}).get(cls)
        if old:
            print(f"  {cls}: score {old['score']} -> {e['score']} "
                  f"({e['score'] - old['score']:+.3f})")
    for stage, s in report["stages"].items():
        old = baseline.get("stages", {}).get(stage)
        if old:
            print(f"  {stage}: p95 {old['p95_ms']} -> {s['p95_ms']} ms")


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #

def _load_golden(only: str | None, ids: set[str] | None) -> list[dict]:
    items = [
        json.loads(line)
        for line in GOLDEN.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if only:
        items = [i for i in items if i["class"] == only]
    if ids:
        items = [i for i in items if i["id"] in ids]
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=_CLASSES, help="Run one class only.")
    parser.add_argument("--ids", help="Comma-separated item ids to run.")
    parser.add_argument("--out", help="Results JSON path (default: results/eval-<ts>.json).")
    parser.add_argument("--baseline", help="Previous results JSON to diff against.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    problems = _preflight()
    if problems:
        for p in problems:
            print(f"PREFLIGHT FAILED: {p}", file=sys.stderr)
        return 2
    _disable_caches()

    golden = _load_golden(args.only, set(args.ids.split(",")) if args.ids else None)
    if not golden:
        print("No golden items matched the filters.", file=sys.stderr)
        return 2

    results: list[dict] = []
    for item in golden:
        row: dict[str, Any] = {"id": item["id"], "class": item["class"]}
        try:
            checks, extras, latency, stages = _RUNNERS[item["class"]](item)
            row.update(
                checks=checks, extras=extras, latency_ms=round(latency, 1),
                stages={k: round(v, 1) for k, v in stages.items()},
                passed=all(checks.values()),
            )
        except Exception as exc:
            logger.warning("Item %s errored.", item["id"], exc_info=True)
            row.update(checks={}, extras={}, latency_ms=0.0, stages={},
                       passed=False, error=f"{type(exc).__name__}: {exc}")
        results.append(row)
        print(f"  {'PASS' if row['passed'] else 'FAIL'}  {item['id']} ({item['class']})")

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "golden": GOLDEN.name,
        "filters": {"only": args.only, "ids": args.ids},
        "classes": _aggregate(results),
        "stages": _aggregate_stages(results),
        "items": results,
    }

    out = Path(args.out) if args.out else RESULTS_DIR / (
        f"eval-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = _markdown(report)
    out.with_suffix(".md").write_text(summary, encoding="utf-8")
    print("\n" + summary)
    print(f"Results: {out}")

    if args.baseline:
        _print_baseline_diff(report, Path(args.baseline))
    return 0


if __name__ == "__main__":
    sys.exit(main())
