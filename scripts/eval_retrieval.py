"""Compare retrieval configurations on a judged query set.

Answers one question: does the existing keyword leg earn its place next to dense
retrieval, and on which kinds of query? It deliberately measures *candidate
retrieval*, not answers — no reranking, no website preference, no context
building — so a difference in the numbers is a difference in what was fetched
rather than in how it was later reordered.

Configurations
    dense           app.retrieval.search.hybrid_search.search, the pull retrieval
                    has always done.
    dense+keyword   the same pull, RRF-fused with the MatchText leg
                    (app.retrieval.search.strategies.keyword_search). This is
                    what `keyword_leg_enabled` turns on in production. The leg
                    needs the chunk_text index — run
                    `python -m scripts.create_fulltext_index` first, or it
                    silently contributes nothing.
    keyword         the MatchText leg alone, reported for diagnosis. It is not
                    a candidate configuration: it returns nothing for a query
                    with no salient terms.

Metrics are computed against `reports/retrieval/judgments_v1.draft.json`, whose
grades are LLM-assisted drafts. **Treat every number here as provisional until
those judgments are reviewed** — see the file's own status field.

Reading the output
    This evaluator has twice produced a confident, plausible, wrong number
    rather than an error, so it now guards both cases loudly. Judge a result by
    asking what it *would* read if the thing it measures had not run at all —
    not whether the figure looks reasonable.

    - Every metric 0.000 across every configuration means the judged chunk ids
      are not in the collection, not that retrieval failed. Chunk ids are
      content-derived, so any re-chunking invalidates the gold set; re-run
      `scripts.judge_retrieval`.
    - A single configuration scoring badly may be a Qdrant timeout, not a
      ranking. Retrieval errors are recorded per call, excluded from the means
      as None rather than averaged in as zeros, and reported in a block headed
      "retrieval calls FAILED". If that block appears, the run is incomplete.
    - Two configurations returning *identical* per-category scores means they
      are the same configuration. Settings not named in a config's overrides are
      pinned by `_RERANK_DEFAULTS`, never inherited from `.env` — an earlier
      pass had the nominally-512 sequence length silently running at the 256 in
      the developer's environment.

    python -m scripts.eval_retrieval                    # all queries
    python -m scripts.eval_retrieval --k 5              # cut at rank 5
    python -m scripts.eval_retrieval --category acronym # one category
    python -m scripts.eval_retrieval --json out.json    # machine-readable
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import statistics
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Sequence

logger = logging.getLogger("eval_retrieval")

_REPORT_DIR = Path("reports/retrieval")
_QUERIES = _REPORT_DIR / "queries_v1.json"
_JUDGMENTS = _REPORT_DIR / "judgments_v1.draft.json"

# Depth every configuration is asked for and, unless --k says otherwise, the
# rank cut metrics are computed at. Kept well below retrieval_candidate_k so the
# comparison is about ordering quality rather than how deep each leg can dig.
DEFAULT_K = 10

# A pooled judgment at or above this grade counts as relevant for the binary
# metrics (Recall@K, MRR). Grade 1 ("related but does not answer") is kept out
# so recall is not inflated by near-misses.
RELEVANT_AT = 2


# --------------------------------------------------------------------------- #
# Configurations under test
# --------------------------------------------------------------------------- #

def _dense(query: str, query_vector: list[float], limit: int) -> list[Any]:
    from app.retrieval.search.hybrid_search import search

    return search(query, limit=limit, query_vector=query_vector)


def _keyword(query: str, query_vector: list[float], limit: int) -> list[Any]:
    from app.retrieval.search.strategies import extract_key_terms, keyword_search

    terms = extract_key_terms(query)
    if not terms:
        return []
    return keyword_search(
        query, terms, filters=None, query_vector=query_vector, limit=limit
    )


def _dense_keyword(query: str, query_vector: list[float], limit: int) -> list[Any]:
    from app.retrieval.search.fusion import rrf

    dense = _dense(query, query_vector, limit)
    keyword = _keyword(query, query_vector, limit)
    if not keyword:
        # No salient terms, or the leg found nothing: RRF over one ranking is
        # the identity, but skip it so the result is literally the dense list.
        return dense
    return rrf([dense, keyword])[:limit]


# --------------------------------------------------------------------------- #
# Reranking configurations
#
# These reorder the `dense+keyword` pool rather than retrieving their own, which
# is deliberate. The judgments are pooled from the retrieval legs at depth
# POOL_DEPTH, so any chunk a deeper pull would surface is ungraded and scores 0
# by construction — exactly the bias `scripts.judge_retrieval` documents for the
# keyword leg. Reranking inside the judged set removes it: the set is identical
# across these configs and only the *order* differs, so Recall@K is fixed by
# construction and every move in nDCG/MRR is ordering quality, which is the only
# thing a reranker claims to improve.
# --------------------------------------------------------------------------- #

# The retrieval pool, memoised per (query, limit) so every rerank config scores
# the identical candidate set and the timing delta is the reranker's own cost
# rather than another Qdrant round trip.
_POOL_CACHE: dict[tuple[str, int], list[Any]] = {}


def _pool(query: str, query_vector: list[float], limit: int) -> list[Any]:
    key = (query, limit)
    if key not in _POOL_CACHE:
        _POOL_CACHE[key] = _dense_keyword(query, query_vector, limit)
    # Copied because `rerank` writes `score` on the candidates it is given.
    return list(_POOL_CACHE[key])


@contextmanager
def _settings(**overrides: str):
    """Run with these Settings fields overridden.

    `get_settings` is lru_cached, so the environment alone is not enough — the
    cache has to be dropped on the way in and again on the way out, or the
    override leaks into whatever runs next.
    """
    from app.config import get_settings

    previous = {k: os.environ.get(k) for k in overrides}
    os.environ.update(overrides)
    get_settings.cache_clear()
    try:
        yield
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        get_settings.cache_clear()


#: Every rerank setting, pinned to its shipped default. `_reranked` applies this
#: whole set and then the config's overrides on top, so a configuration means the
#: same thing on any machine.
#:
#: Not optional. `Settings` reads `.env`, so a config that overrode only the
#: provider inherited every other value from whatever the developer had
#: configured — measured once, when `.env` carried RERANK_MAX_SEQ_LENGTH=256 and
#: the nominally-512 configuration silently ran at 256, returning per-category
#: scores identical to the explicit 256 config. A benchmark whose configurations
#: are defined partly by ambient state is not a benchmark.
_RERANK_DEFAULTS = {
    "RERANKER_PROVIDER": "embedding",
    "RERANK_MODEL": "",
    "RERANK_MAX_SEQ_LENGTH": "0",
    "RERANK_MAX_CANDIDATES": "40",
    "RERANK_RELEVANCE_TOLERANCE": "0.03",
    "RERANK_SCORE_THRESHOLD": "0.0",
}


def _reranked(**overrides: str) -> Callable[[str, list[float], int], list[Any]]:
    """A config that reranks the shared pool under `overrides`.

    Settings not named in `overrides` are pinned to `_RERANK_DEFAULTS`, not
    inherited from the environment.
    """
    pinned = {**_RERANK_DEFAULTS, **overrides}

    def run(query: str, query_vector: list[float], limit: int) -> list[Any]:
        from app.retrieval.search.reranker import rerank

        candidates = _pool(query, query_vector, limit)
        with _settings(**pinned):
            return rerank(query, candidates, top_n=limit)

    return run


# Cross-encoders under test. MiniLM is the small English-only baseline (~90MB);
# bge-reranker-v2-m3 is the multilingual XLM-R-large model `reranker.py` defaults
# to (~2.3GB).
#
# No tolerance override: `reranker._cross_encoder_semantic` squashes the logit
# through a sigmoid, so the score is back on the 0..1 footing that
# `rerank_relevance_tolerance` (0.03) and the context builder's floors are
# calibrated for. The `_t20` variants widen the band instead, which is the one
# knob that trades relevance against the recency/authority keys underneath it.
_CE_MODELS = {
    "minilm": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "bge": "BAAI/bge-reranker-v2-m3",
}

CONFIGS: dict[str, Callable[[str, list[float], int], list[Any]]] = {
    "dense": _dense,
    "keyword": _keyword,
    "dense+keyword": _dense_keyword,
    # Production today: `reranker_provider` defaults to "embedding", which
    # `reranker._semantic_scores` resolves to the dense score retrieval already
    # returned. So this measures the banding alone, on an unchanged relevance
    # signal — the honest baseline for what adding a real reranker buys.
    "rr_embedding": _reranked(RERANKER_PROVIDER="embedding"),
}

for _key, _model in _CE_MODELS.items():
    CONFIGS[f"rr_{_key}"] = _reranked(
        RERANKER_PROVIDER="cross_encoder", RERANK_MODEL=_model,
    )
    CONFIGS[f"rr_{_key}_t20"] = _reranked(
        RERANKER_PROVIDER="cross_encoder", RERANK_MODEL=_model,
        RERANK_RELEVANCE_TOLERANCE="0.20",
    )
    # Sequence-length variants. Latency is close to linear in this, so the
    # question is what judging a passage on its opening costs in ranking quality.
    for _seq in ("256", "128", "64"):
        CONFIGS[f"rr_{_key}_s{_seq}"] = _reranked(
            RERANKER_PROVIDER="cross_encoder", RERANK_MODEL=_model,
            RERANK_MAX_SEQ_LENGTH=_seq,
        )

POOL_CONFIGS = ("dense", "keyword", "dense+keyword")

# The pair the phase is actually deciding between; `keyword` alone is diagnostic.
# Overridable with --compare, since the file now carries two decisions: whether
# the keyword leg earns its place, and whether a real reranker does.
COMPARED = ("dense", "dense+keyword")


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #

def recall_at_k(ranked_ids: Sequence[str], relevant: set[str], k: int) -> float | None:
    """Share of known relevant chunks appearing in the top k.

    None when nothing relevant is known for the query — reported as "no
    judgments" rather than folded in as a zero, which would silently punish a
    configuration for a gap in the gold set.
    """
    if not relevant:
        return None
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked_ids: Sequence[str], relevant: set[str]) -> float | None:
    if not relevant:
        return None
    for rank, chunk_id in enumerate(ranked_ids, start=1):
        if chunk_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: Sequence[str], grades: dict[str, int], k: int) -> float | None:
    """Graded nDCG. Uses the full 0/1/2 scale, so it is the only metric here
    that distinguishes "answers the question" from "related"."""
    if not any(grades.values()):
        return None
    gains = [grades.get(cid, 0) for cid in ranked_ids[:k]]
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(gains))
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else None


def _mean(values: Sequence[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.fmean(present) if present else None


def _fmt(value: float | None, width: int = 6) -> str:
    return f"{value:.3f}".rjust(width) if value is not None else "    - "


# --------------------------------------------------------------------------- #
# Running
# --------------------------------------------------------------------------- #

def _load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"{path} not found. Build the query set first, then run "
            "`python -m scripts.judge_retrieval` to draft judgments."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def run_query(
    query: str, *, limit: int, configs: Sequence[str]
) -> dict[str, dict[str, Any]]:
    """Every configuration's ranking for one query, with its wall time.

    The query is embedded once and shared, so the timings compare retrieval
    rather than repeated embedding calls — which is also how production works.
    """
    from app.core.clients.embeddings import embed_query

    query_vector = embed_query(query)
    out: dict[str, dict[str, Any]] = {}
    for name in configs:
        started = time.perf_counter()
        error = None
        try:
            hits = CONFIGS[name](query, query_vector, limit)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Config %r failed on %r.", name, query, exc_info=True)
            hits = []
            # Recorded rather than swallowed. An empty result from a Qdrant
            # timeout is not the same measurement as a configuration that
            # genuinely retrieved nothing, and scoring it as 0.0 silently
            # depresses whichever configurations happened to run while the
            # server was busy — measured once, when a post-migration optimiser
            # pass timed out the first query for six of seven configurations and
            # left the seventh looking better than it was.
            error = f"{type(exc).__name__}: {exc}"
        elapsed_ms = (time.perf_counter() - started) * 1000
        out[name] = {"ids": [h.id for h in hits], "ms": elapsed_ms, "error": error}
    return out


def evaluate(
    queries: list[dict], judgments: dict[str, dict[str, int]], *, k: int,
    configs: Sequence[str],
) -> list[dict]:
    rows: list[dict] = []
    for case in queries:
        grades = {cid: int(g) for cid, g in judgments.get(case["id"], {}).items()}
        relevant = {cid for cid, g in grades.items() if g >= RELEVANT_AT}
        results = run_query(case["query"], limit=k, configs=configs)
        row: dict[str, Any] = {
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "judged": len(grades),
            "relevant": len(relevant),
            "configs": {},
        }
        for name, res in results.items():
            ids = res["ids"]
            failed = res.get("error") is not None
            row["configs"][name] = {
                # None, not 0.0, when the retrieval itself errored: `_mean` skips
                # None, so a failed call is excluded from the aggregate instead
                # of being averaged in as a total miss.
                "recall": None if failed else recall_at_k(ids, relevant, k),
                "mrr": None if failed else reciprocal_rank(ids, relevant),
                "ndcg": None if failed else ndcg_at_k(ids, grades, k),
                "ms": res["ms"],
                "returned": len(ids),
                "error": res.get("error"),
                "ids": ids,
            }
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def _aggregate(rows: list[dict], configs: Sequence[str]) -> dict[str, dict]:
    return {
        name: {
            "recall": _mean([r["configs"][name]["recall"] for r in rows]),
            "mrr": _mean([r["configs"][name]["mrr"] for r in rows]),
            "ndcg": _mean([r["configs"][name]["ndcg"] for r in rows]),
            "ms_mean": _mean([r["configs"][name]["ms"] for r in rows]),
            "ms_p95": (
                sorted(r["configs"][name]["ms"] for r in rows)[
                    max(0, int(len(rows) * 0.95) - 1)
                ]
                if rows
                else None
            ),
        }
        for name in configs
    }


def _print_table(title: str, rows: list[dict], configs: Sequence[str], k: int) -> None:
    print(f"\n{title}")
    print(f"  {'config':16} {'R@%d' % k:>7} {'MRR':>7} {'nDCG':>7} {'ms':>8} {'p95ms':>8}")
    agg = _aggregate(rows, configs)
    for name in configs:
        a = agg[name]
        print(
            f"  {name:16} {_fmt(a['recall'], 7)} {_fmt(a['mrr'], 7)} "
            f"{_fmt(a['ndcg'], 7)} {_fmt(a['ms_mean'], 8)} {_fmt(a['ms_p95'], 8)}"
        )


def _print_wins(rows: list[dict], k: int, compared: tuple[str, str] = COMPARED) -> None:
    """Per-query wins and losses between the two compared configurations.

    Reported per query rather than only in aggregate because a mean can hide the
    shape that matters here: a leg that transforms three acronym queries and
    slightly hurts twenty semantic ones is a different decision from one that
    helps everything a little.
    """
    a, b = compared
    print(f"\nPer-query change ({b} vs {a}), by nDCG@{k}:")
    wins = losses = ties = 0
    for row in rows:
        ca, cb = row["configs"].get(a), row["configs"].get(b)
        if not ca or not cb or ca["ndcg"] is None or cb["ndcg"] is None:
            continue
        delta = cb["ndcg"] - ca["ndcg"]
        unique = len(set(cb["ids"]) - set(ca["ids"]))
        if abs(delta) < 1e-9:
            ties += 1
            continue
        wins += delta > 0
        losses += delta < 0
        mark = "+" if delta > 0 else "-"
        print(
            f"  {mark} {row['id']:10} {row['category']:12} "
            f"dNDCG={delta:+.3f}  new-chunks={unique:2}  {row['query'][:52]}"
        )
    print(f"\n  wins={wins}  losses={losses}  ties={ties}")


def _print_by_category(rows: list[dict], configs: Sequence[str], k: int) -> None:
    print(f"\nBy category (nDCG@{k}):")
    header = "  " + f"{'category':14}" + "".join(f"{c:>16}" for c in configs)
    print(header)
    categories = sorted({r["category"] for r in rows})
    for category in categories:
        subset = [r for r in rows if r["category"] == category]
        cells = ""
        for name in configs:
            cells += _fmt(_mean([r["configs"][name]["ndcg"] for r in subset]), 16)
        print(f"  {category:14}{cells}   (n={len(subset)})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Rank cut.")
    parser.add_argument("--category", help="Restrict to one category.")
    parser.add_argument(
        "--configs", default=",".join(CONFIGS),
        help=f"Comma-separated subset of: {', '.join(CONFIGS)}",
    )
    parser.add_argument(
        "--compare", default=",".join(COMPARED),
        help="Config pair for the per-query wins table, as 'baseline,candidate'.",
    )
    parser.add_argument("--json", dest="json_out", help="Write full results here.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    queries = _load(_QUERIES)["queries"]
    if args.category:
        queries = [q for q in queries if q["category"] == args.category]
        if not queries:
            raise SystemExit(f"No queries in category {args.category!r}.")

    judged = _load(_JUDGMENTS)
    judgments = {qid: v["grades"] for qid, v in judged["queries"].items()}
    configs = [c.strip() for c in args.configs.split(",") if c.strip() in CONFIGS]

    print(f"Queries: {len(queries)}   k={args.k}   configs={', '.join(configs)}")
    print(f"Judgments: {_JUDGMENTS}  ({judged.get('status', 'unknown status')})")

    rows = evaluate(queries, judgments, k=args.k, configs=configs)

    _print_table("Overall", rows, configs, args.k)
    _print_by_category(rows, configs, args.k)
    compared = tuple(c.strip() for c in args.compare.split(","))
    if len(compared) == 2 and all(c in configs for c in compared):
        _print_wins(rows, args.k, compared)

    errors = [
        (r["id"], name, cfg["error"])
        for r in rows for name, cfg in r["configs"].items() if cfg.get("error")
    ]
    if errors:
        print()
        print(f"*** {len(errors)} retrieval calls FAILED and are excluded "
              f"from the means. These numbers are incomplete: ***")
        for qid, name, err in errors[:12]:
            print(f"  ! {qid:10} {name:22} {err}")
        if len(errors) > 12:
            print(f"  ... and {len(errors) - 12} more")
        print("  Re-run before comparing configurations — a config that ran while "
              "the server was busy is not comparable to one that did not.")

    unjudged = [r["id"] for r in rows if not r["relevant"]]
    if unjudged:
        print(
            f"\n{len(unjudged)} queries have no relevant chunk judged and are "
            f"excluded from the means: {', '.join(unjudged[:8])}"
            + (" ..." if len(unjudged) > 8 else "")
        )

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {"k": args.k, "aggregate": _aggregate(rows, configs), "rows": rows},
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nWrote {args.json_out}")

    print(
        "\nNOTE: judgments are LLM-assisted drafts and are not authoritative. "
        "Review them before treating any of this as a decision."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
