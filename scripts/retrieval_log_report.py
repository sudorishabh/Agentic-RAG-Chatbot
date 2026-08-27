"""Read the retrieval traces back: latency, recall and failures per retriever.

The traces (`is_retrieval_log=true`, see docs/retrieval-logging.md) are one JSON
file per query, which is the right shape for reading one query and the wrong
shape for reading a thousand. This folds a day — or a range of days — into the
three read-outs the files are collected for:

1. **Per retriever and stage**: calls, p50/p95 latency, results returned, and
   how often a pull came back empty. This is where "Qdrant vs graph vs MySQL"
   is actually answered.
2. **Per query**: the slowest queries, so a tail can be opened by request id.
3. **Failures**: every event that errored, with the message.

Stdlib only, and read-only. For anything beyond these three, the digest is
already a dataframe:

    pd.read_json("logs/summary/2026-08-26.jsonl", lines=True)

Usage:
    python -m scripts.retrieval_log_report                    # today
    python -m scripts.retrieval_log_report --day 2026-08-26
    python -m scripts.retrieval_log_report --all --slowest 20
    python -m scripts.retrieval_log_report --errors-only
    python -m scripts.retrieval_log_report --request-id 5f3c1e9a  # read out one query
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
from datetime import datetime, timezone
from typing import Any, Iterator


def _printable_console() -> None:
    """Let the corpus's own characters through on a Windows console.

    The passages hold CO₂, en dashes and curly quotes, and the default cp1252
    console raises ``UnicodeEncodeError`` on the first one — which would turn a
    read-only report into a crash. UTF-8 where the terminal supports it, a
    replacement character where it does not.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # pragma: no cover - not a real terminal
            pass


def _root(override: str | None) -> pathlib.Path:
    if override:
        return pathlib.Path(override).expanduser()
    from app.observability.retrieval_log import log_root

    return log_root()


def _day_dirs(root: pathlib.Path, day: str | None, every: bool) -> list[pathlib.Path]:
    if every:
        return sorted(
            p for p in root.iterdir()
            if p.is_dir() and p.name not in {"errors", "summary"}
        )
    target = day or datetime.now(timezone.utc).date().isoformat()
    return [root / target]


def trace_files(directory: pathlib.Path) -> list[pathlib.Path]:
    """Every trace in one day's directory.

    One query is a directory holding ``trace.json`` and ``report.md``. The flat
    ``query_<id>.json`` form is still read, so logs written before the layout
    changed remain readable.
    """
    return sorted(
        list(directory.glob("query_*/trace.json"))
        + list(directory.glob("query_*.json"))
    )


def traces(paths: list[pathlib.Path]) -> Iterator[dict[str, Any]]:
    for directory in paths:
        if not directory.is_dir():
            continue
        for path in trace_files(directory):
            try:
                yield json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # a half-written or hand-edited file
                print(f"  ! could not read {path}: {exc}")


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))]


def _stage_table(loaded: list[dict[str, Any]]) -> None:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for trace in loaded:
        for event in trace.get("events", []):
            key = (event.get("retriever", "?"), event.get("stage") or "-")
            bucket = buckets.setdefault(
                key, {"latency": [], "results": 0, "empty": 0, "errors": 0}
            )
            bucket["latency"].append(float(event.get("latency_ms") or 0.0))
            count = int(event.get("result_count") or 0)
            bucket["results"] += count
            bucket["empty"] += 1 if count == 0 else 0
            bucket["errors"] += 1 if event.get("error") else 0

    print(f"\n{'retriever':<10} {'stage':<26} {'calls':>6} {'p50':>8} {'p95':>8} "
          f"{'total s':>8} {'results':>8} {'empty':>6} {'errors':>6}")
    print("-" * 92)
    for (retriever, stage), bucket in sorted(
        buckets.items(), key=lambda kv: -sum(kv[1]["latency"])
    ):
        latency = bucket["latency"]
        print(
            f"{retriever:<10} {stage:<26} {len(latency):>6} "
            f"{_percentile(latency, 0.5):>8.1f} {_percentile(latency, 0.95):>8.1f} "
            f"{sum(latency) / 1000:>8.1f} {bucket['results']:>8} "
            f"{bucket['empty']:>6} {bucket['errors']:>6}"
        )


def _query_table(loaded: list[dict[str, Any]], slowest: int) -> None:
    rows = sorted(
        loaded, key=lambda t: -(t.get("timings", {}).get("total_latency_ms") or 0)
    )[:slowest]
    print(f"\nslowest {len(rows)} quer{'y' if len(rows) == 1 else 'ies'}")
    print(f"{'total ms':>9} {'retrieval':>10} {'blocks':>7} {'id':<12} question")
    print("-" * 92)
    for trace in rows:
        timings = trace.get("timings", {})
        print(
            f"{timings.get('total_latency_ms', 0):>9.0f} "
            f"{timings.get('retrieval_latency_ms', 0):>10.0f} "
            f"{trace.get('context', {}).get('block_count', 0):>7} "
            f"{trace.get('request_id', '')[:10]:<12} "
            f"{(trace.get('question') or '')[:48]}"
        )


def _failures(loaded: list[dict[str, Any]]) -> None:
    printed = 0
    for trace in loaded:
        problems = [
            (e.get("retriever"), e.get("stage"), e["error"])
            for e in trace.get("events", [])
            if e.get("error")
        ]
        for entry in trace.get("errors", []):
            problems.append(("pipeline", entry.get("where"), entry))
        if not problems:
            continue
        if printed == 0:
            print("\nfailures")
            print("-" * 92)
        printed += 1
        print(f"  {trace.get('request_id', '')[:10]}  {(trace.get('question') or '')[:56]}")
        for retriever, stage, error in problems:
            print(f"      {retriever}/{stage}: {error.get('type')}: "
                  f"{(error.get('message') or '')[:90]}")
    if printed == 0:
        print("\nfailures: none")


def _one_trace(root: pathlib.Path, request_id: str, *, raw: bool) -> int:
    """One query, read out as an outline. ``--raw`` prints the JSON instead."""
    matches = [
        p for p in list(root.rglob(f"query_{request_id}*/trace.json"))
        + list(root.rglob(f"query_{request_id}*.json"))
        if "errors" not in p.parts
    ]
    if not matches:
        print(f"No trace found for request id starting {request_id!r} under {root}")
        return 1
    trace = json.loads(matches[0].read_text(encoding="utf-8"))
    if raw:
        print(json.dumps(trace, indent=2))
        return 0
    report = matches[0].with_name("report.md")
    if report.is_file():
        print(f"\n(the same query written out in full: {report})")

    query = trace.get("query", {})
    timings = trace.get("timings", {})
    print(f"\n{trace.get('question')}")
    print(f"  {trace.get('timestamp')}  ·  {trace.get('entrypoint')}  ·  "
          f"{trace.get('request_id', '')[:10]}  ·  {matches[0]}")
    print(f"  understood as: intent={query.get('intent')} "
          f"format={query.get('answer_format')} "
          f"search_query={query.get('search_query')!r}")
    if query.get("filters"):
        print(f"  filters: {json.dumps(query['filters'])[:160]}")
    print(f"  {timings.get('total_latency_ms', 0):.0f} ms total, "
          f"{timings.get('retrieval_latency_ms', 0):.0f} ms in retrievers")

    print("\n  retrieval")
    for event in trace.get("events", []):
        count = event.get("result_count", 0)
        print(f"    {event.get('retriever'):<7} {event.get('stage'):<26} "
              f"{event.get('latency_ms', 0):>7.1f} ms  {count:>6} result(s)"
              + ("  [ERROR]" if event.get("error") else ""))
        if event.get("error"):
            print(f"        {event['error'].get('type')}: "
                  f"{(event['error'].get('message') or '')[:100]}")
        shown = (event.get("results") or [])[:5]
        for line in shown:
            text = line if isinstance(line, str) else json.dumps(line, default=str)
            print(f"        {text[:150]}")
        if not shown and count:
            # A bulk vocabulary load: counted on purpose, not lost.
            print("        (bulk load — rows not sampled)")
        elif count > len(shown):
            print(f"        … {count - len(shown)} more")

    context = trace.get("context", {})
    print(f"\n  context handed to the LLM: {context.get('block_count', 0)} block(s), "
          f"{context.get('total_chars', 0)} chars")
    for block in context.get("blocks", []):
        where = block.get("source") or json.dumps(block.get("metadata", {}))[:80]
        print(f"    [{block.get('n')}] {where}")
        snippet = " ".join((block.get("text") or "").split())
        if snippet:
            print(f"        {snippet[:220]}")

    outcome = trace.get("outcome", {})
    if outcome:
        print("\n  outcome: " + ", ".join(f"{k}={v}" for k, v in outcome.items()))
    for entry in trace.get("errors", []):
        print(f"  ! {entry.get('where')}: {entry.get('type')}: {entry.get('message')}")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", help="log directory (default: the configured one)")
    parser.add_argument("--day", help="YYYY-MM-DD (default: today, UTC)")
    parser.add_argument("--all", action="store_true", help="every day present")
    parser.add_argument("--slowest", type=int, default=10)
    parser.add_argument("--errors-only", action="store_true")
    parser.add_argument("--request-id", help="read out one query (prefix of its id)")
    parser.add_argument("--raw", action="store_true",
                        help="with --request-id: print the JSON instead of the outline")
    args = parser.parse_args()

    _printable_console()
    root = _root(args.dir)
    if not root.is_dir():
        print(f"No retrieval logs at {root}. Set is_retrieval_log=true and ask a question.")
        return 1
    if args.request_id:
        return _one_trace(root, args.request_id, raw=args.raw)

    days = _day_dirs(root, args.day, args.all)
    loaded = list(traces(days))
    if not loaded:
        print(f"No traces in {', '.join(d.name for d in days)} (under {root}).")
        return 1

    print(f"{len(loaded)} quer{'y' if len(loaded) == 1 else 'ies'} from "
          f"{', '.join(d.name for d in days)}  [{root}]")
    totals = [t.get("timings", {}).get("total_latency_ms") or 0.0 for t in loaded]
    cached = sum(1 for t in loaded if t.get("outcome", {}).get("cached"))
    answered = sum(1 for t in loaded if t.get("outcome", {}).get("answered"))
    print(f"  latency: mean {statistics.fmean(totals):.0f} ms, "
          f"p95 {_percentile(totals, 0.95):.0f} ms, max {max(totals):.0f} ms")
    print(f"  answered {answered}/{len(loaded)}, cached {cached}")

    if not args.errors_only:
        _stage_table(loaded)
        _query_table(loaded, args.slowest)
    _failures(loaded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
