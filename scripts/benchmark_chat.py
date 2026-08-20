"""Run the organizational gold benchmark against the live /chat endpoint, N times.

Why N times
-----------
The pipeline is not deterministic. The query-analysis call runs at the
deployment's default temperature (``llm_structured_temperature`` is unset), and
the answerer is a streaming chat completion, so the same question can be routed
to a different intent and can refuse on one call and answer on the next. A
single run therefore cannot tell a real change from a resample: measured on 15
questions, four changed outcome class across three repeats of identical code.

So the harness runs the whole benchmark ``--runs`` times and records every run
separately. Grading takes the majority verdict and reports the disagreement, and
a change is only credible when it moves the majority.

Read-only against every store: the retrieval server has no ingestion lifespan
and ``semantic_cache_enabled`` is false, so nothing is written back. ``/search``
is called alongside ``/chat`` purely for the per-block telemetry the SSE
contract does not expose.

Resumable: the output file is rewritten after every question, and an existing
file is reloaded so an interrupted run continues where it stopped.

    python scripts/benchmark_chat.py --runs 3 --out reports/benchmark/raw_3run.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

import requests

DEFAULT_GOLD = os.path.join("reports", "benchmark", "organization_121_gold.json")
DEFAULT_JUDGEMENT = os.path.join(
    "reports", "benchmark", "organization_121_gold_judgement.json")
ELIGIBLE_JUDGEMENTS = ("GOLD_CONFIRMED", "GOLD_NEEDS_CORRECTION")


def eligible_questions(gold_path: str, judgement_path: str) -> list[dict]:
    """The benchmark set: GOLD_VERIFIED questions the judgement pass confirmed.

    Same rule as the baseline and fix runs, so the three are comparable.
    """
    gold = json.load(io.open(gold_path, encoding="utf-8"))
    judged = json.load(io.open(judgement_path, encoding="utf-8"))
    verdicts = {x["question_id"]: x["judgement"] for x in judged["questions"]}
    return [
        q for q in gold["questions"]
        if q["status"] == "GOLD_VERIFIED"
        and verdicts.get(q["question_id"]) in ELIGIBLE_JUDGEMENTS
    ]


def run_chat(url: str, question: str, timeout: int) -> dict:
    """One /chat call, consuming the SSE stream the UI consumes."""
    tokens: list[str] = []
    sources: dict | None = None
    corrected: dict | None = None
    error: str | None = None
    ttft: float | None = None
    t0 = time.perf_counter()
    try:
        with requests.post(url, json={"question": question}, stream=True,
                           timeout=timeout) as response:
            response.raise_for_status()
            # The stream is `data: {json}` per line, with the event kind inside
            # the payload's `type` — there are no separate `event:` lines.
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                kind = event.get("type")
                if kind == "token":
                    if ttft is None and event.get("text"):
                        ttft = (time.perf_counter() - t0) * 1000
                    tokens.append(event.get("text", ""))
                elif kind == "correction":
                    corrected = {"text": event.get("text", ""),
                                 "reason": event.get("reason")}
                elif kind == "sources":
                    sources = event
                elif kind == "error":
                    error = "SSE error event (stream failed mid-response)"
    except Exception as exc:  # network, timeout, non-200
        error = f"{type(exc).__name__}: {exc}"
    total = (time.perf_counter() - t0) * 1000
    answer = corrected["text"] if corrected else "".join(tokens)
    return {
        "answer": answer,
        "sources": sources,
        "error": error,
        "latency_ms": round(total, 1),
        "ttft_ms": round(ttft, 1) if ttft else None,
        "generation_ms": round(total - ttft, 1) if ttft else None,
    }


def run_search(url: str, question: str, timeout: int) -> dict:
    """Retrieval telemetry for the same question: intent, blocks, per-block ids."""
    try:
        response = requests.post(url, json={"question": question}, timeout=timeout)
        response.raise_for_status()
        d = response.json()
        return {
            "intent": d.get("intent"),
            "answer_format": d.get("answer_format"),
            "search_query": d.get("search_query"),
            "intents": d.get("intents", []),
            "is_ambiguous": d.get("is_ambiguous"),
            "n_blocks": len(d.get("blocks", [])),
            "blocks": [
                {"n": b.get("n"), "score": b.get("score"),
                 "document_id": b.get("document_id"),
                 "source_type": b.get("source_type"), "title": b.get("title"),
                 "page_number": b.get("page_number"), "conflict": b.get("conflict"),
                 "text_head": (b.get("text") or "")[:300]}
                for b in d.get("blocks", [])
            ],
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--gold", default=DEFAULT_GOLD)
    ap.add_argument("--judgement", default=DEFAULT_JUDGEMENT)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--only", default="", help="comma-separated question ids")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    chat_url, search_url = f"{args.base_url}/chat", f"{args.base_url}/search"
    questions = eligible_questions(args.gold, args.judgement)
    if args.only:
        wanted = {q.strip() for q in args.only.split(",") if q.strip()}
        questions = [q for q in questions if q["question_id"] in wanted]

    done: dict[tuple[int, str], dict] = {}
    if os.path.exists(args.out):
        for record in json.load(io.open(args.out, encoding="utf-8")):
            # A response that errored is not evidence of anything; re-issue it.
            if not record["chat"]["error"] and not (record["search"] or {}).get("error"):
                done[(record["run"], record["question_id"])] = record
        print(f"resuming: {len(done)} clean responses already on disk", flush=True)

    total = args.runs * len(questions)
    results = list(done.values())
    for run in range(1, args.runs + 1):
        for i, question in enumerate(questions, 1):
            qid = question["question_id"]
            if (run, qid) in done:
                continue
            chat = run_chat(chat_url, question["question"], args.timeout)
            search = run_search(search_url, question["question"], args.timeout)
            results.append({
                "run": run,
                "question_id": qid,
                "question": question["question"],
                "answer_type": question["answer_type"],
                "chat": chat,
                "search": search,
            })
            results.sort(key=lambda r: (r["question_id"], r["run"]))
            json.dump(results, io.open(args.out, "w", encoding="utf-8"),
                      indent=1, ensure_ascii=False)
            print(f"[run {run}/{args.runs}] [{i}/{len(questions)}] {qid} "
                  f"{chat['latency_ms']:.0f}ms chars={len(chat['answer'])} "
                  f"intent={search.get('intent')} blocks={search.get('n_blocks')} "
                  f"err={chat['error']}", flush=True)

    errored = [r["question_id"] for r in results
               if r["chat"]["error"] or (r["search"] or {}).get("error")]
    print(f"DONE {len(results)}/{total} responses; errored: {sorted(set(errored)) or 'none'}")
    return 1 if len(results) < total else 0


if __name__ == "__main__":
    raise SystemExit(main())
