# Phase 4 Implementation Handoff — Feedback Loop & Optional Enhancements

Self-contained context for implementing Phase 4 of
`docs/retrieval-response-architecture-plan.md`. Companion to the Phase 1–3
handoffs (`docs/phase{1,2,3}-implementation-handoff.md`) — read them for the
system snapshot, code idiom, and test patterns; nothing is repeated here.

Phase 4 is the **optional / evidence-driven** phase: everything here is either
a product feature (user feedback), a deferred refinement from earlier phases,
or an enhancement that only ships if Phase 3 eval numbers say it's needed.
Nothing in this phase is a precondition for production operation.

**Precondition:** Phases 1–3 implemented and committed (all step-approved —
details may differ from their handoffs). **Verify §2 against the actual code
before writing anything.** The Phase 3 eval harness is the gatekeeper for most
steps here; do not implement an eval-gated step before looking at the relevant
eval numbers with the user.

---

## 1. Hard constraints (unchanged)

1. **Ingestion frozen**: zero edits under `app/ingestion/` and to
   `app/deps.py`. Retrieval-side additive `app/config.py` settings allowed.
   Creating a **new retrieval-owned MySQL table** (step 1) is allowed — the
   freeze protects ingestion code and its tables, not the database.
2. **Qdrant `documents` collection**: reads only, always.
3. **GPT-4o-mini only**; decomposed micro-tasks, few-shot, structured outputs.
4. **Latency**: gated/parallel additions only; §13.10 budgets still bind.
5. **Fail-open**; user commits manually; one-line commit messages, no
   attribution, approval gate between steps.

## 2. Assumed post-Phase-3 state (VERIFY FIRST)

- Eval harness at `scripts/eval/` (golden.jsonl, run_eval.py, judges.py,
  results/ with a baseline) — **ask the user for the latest results file**;
  steps 5–8 read their go/no-go from it.
- Decomposed claim-level faithfulness in production (`faithfulness_check`
  state — confirm whether the default flip happened); streaming `correction`
  SSE event; numeric claim check logging `numeric_mismatch`.
- `analysis_votes` config (self-consistency); semantic cache facet-fingerprint
  matching at threshold 0.995.
- Website preference: confirm whether `prefer_website_enabled` was flipped and
  with which `website_max_slots` / `website_chunk_floor`.
- Reranker provider decision (embedding vs cohere vs cross_encoder vs llm) and
  `retrieval_candidate_k` value actually deployed.
- `quality_monitor_enabled` state; multi_query / keyword-leg flag states;
  which Qdrant index scripts have been run.
- Phase 2 scoped-summary doc cap actually chosen (30 vs 150) — step 7 depends
  on it.

## 3. What Phase 4 builds

```
(1) POST /feedback ── response_id on every answer ──► `answer_feedback` table
(2) feedback report script ──► weekly regression review + golden-set candidates
(3) author-scoped QA via catalog id-set (LIKE matching, replaces exact MatchAny)
(4) "did you mean" author disambiguation (deterministic)
(5) HyDE leg                      ── only if eval shows residual recall gaps
(6) streaming scoped-summary reduce ── perceived-latency refinement
(7) scoped-summary two-level reduce to ~150 docs ── if capped at 30 in Phase 2
(8) final tuning sweeps (candidate_k, context budget, thresholds) ── eval-driven
```

## 4. Steps (in order; one commit each; approval gates)

### Step 1 — Feedback endpoint + response identity
1. **Response identity**: add `response_id: str` (uuid4 hex) to every result
   dict assembled in `rag._assemble` / `_empty` / structured & scoped-summary
   results, and include it in the SSE `sources` event and `QueryResponse`
   schema. Cached hits keep their original `response_id` (it identifies the
   *answer content*, which is what feedback is about).
2. **Storage**: new retrieval-owned table (created lazily by the API side,
   idempotent `CREATE TABLE IF NOT EXISTS`, mirroring the state.py DDL style —
   but in a NEW module, e.g. `app/retrieval/feedback_store.py`):
```sql
CREATE TABLE IF NOT EXISTS `answer_feedback` (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    response_id  VARCHAR(64)  NOT NULL,
    verdict      TINYINT      NOT NULL,          -- 1 = up, -1 = down
    comment      VARCHAR(2000) NULL,
    question     VARCHAR(2000) NULL,             -- denormalized for review
    intent       VARCHAR(32)  NULL,
    answer_format VARCHAR(16) NULL,
    tenant_id    VARCHAR(128) NOT NULL DEFAULT 'default',
    created_at   DATETIME     NOT NULL,
    KEY idx_response (response_id),
    KEY idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```
3. **API**: `POST /feedback` in a new `app/api/feedback.py`
   (`FeedbackRequest: response_id, verdict ∈ {"up","down"}, comment?,
   question?, intent?, answer_format?`) — tenant from the authenticated
   principal like /chat (see `app/api/auth.py` pattern), never from the body.
   Rate-limit-friendly: clamp comment length, one insert, fail-open 202 even
   if MySQL write fails (log it). Register the router in `app_factory.py`.
4. Metrics: count feedback events via the existing metrics log.
Tests: store SQL shape via `_FakeCursor`; endpoint validation via FastAPI
TestClient with auth disabled.
Commit: `feat(api): answer feedback endpoint with response identity`

### Step 2 — Feedback regression report (`scripts/eval/feedback_report.py`)
Reads `answer_feedback` for a date window (`--days 7`): down-vote rate by
intent/format, the down-voted questions with comments, and — where the
question is present — a ready-to-review JSONL block of **golden-set candidate
items** (class guessed from intent, expectations left blank for the user to
fill). Markdown output to stdout/file. No LLM required; optionally
`--suggest-class` uses one mini call per item to draft the golden `class`.
Commit: `feat(eval): weekly feedback regression report`

### Step 3 — Author-scoped QA via catalog id-set
Phase 1 shipped author QA filtering as exact `MatchAny` on the `authors`
payload (display-name exact match — brittle for "Dr." prefixes / partial
names). Upgrade: in `rag.retrieve` (or query_processor), when
`analysis.author` is set and intent is `qa`/`scoped_summary`, resolve the
scope via `catalog.document_ids_in_scope(author=<fragment>, ...)` (SQL `LIKE`)
and filter retrieval by `document_id` MatchAny instead of the `authors`
payload condition. Fall back to the payload condition when the catalog
returns nothing (or errors). Requires the `document_id` payload index
(confirm the Phase 1 script ran).
Tests: scope-resolution branch, fallback branch.
Commit: `feat(retrieval): author filters resolve through catalog id scope`

### Step 4 — Author "did you mean" disambiguation (deterministic)
In the structured route: when `analysis.author` is set and
`catalog.authors_matching(fragment)` returns 2–5 distinct names **and** the
requested operation would return zero rows with the raw fragment, answer with
a deterministic clarification ("I found several matching authors: …") listing
the names — no LLM. One name → proceed with it. >5 or 0 names → existing
behavior. Applies to count/list only; never blocks the QA path.
Tests: each branch with stubbed catalog.
Commit: `feat(retrieval): author disambiguation for structured queries`

### Step 5 — HyDE leg (EVAL-GATED — check first)
Go/no-go: Phase 3 retrieval-class results. Only if recall@k gaps persist on
items multi-query didn't close (look for failures where golden relevant docs
use vocabulary far from the question's).
Implementation (behind `hyde_enabled: bool = False`): one mini call →
hypothetical 3–5 sentence answer (few-shot: one example; explicitly "write a
plausible passage, factuality not required — it is only used for search");
embed it (`embed_query_cached`); one extra dense pull with that vector;
RRF-fuse via `fusion.rrf` alongside base (and multi-query) pulls. Runs
concurrently with the base search like the paraphrase call. Skip when intent
!= qa or when explicit facet filters are set (HyDE text can't respect them
reliably — the *filters* still apply to its pull, so it stays safe, but the
signal degrades; measure).
Commit: `feat(retrieval): optional hyde retrieval leg`

### Step 6 — Streaming the scoped-summary reduce step
Deferred from Phase 2 (buffered v1). Rework: `summarize_scope` splits into
`prepare_scope(...) -> _ScopeGeneration | result-dict | None` (id selection,
lead parents, map stage — unchanged, still buffered/parallel) and a
`stream_reduce(gen) -> Iterator[str]` that streams the final reduce call
(`get_llm(streaming=True)`).
Wiring in `rag.stream_answer`: `scoped_summary` intent gets its own branch —
stream reduce tokens as `token` events, then the document-level citations as
`sources`, then `done`; persist the assembled result to caches afterward
(mirror the existing generation branch). Buffered `answer_query` keeps using
the joined text. TTFT for large scopes drops from "whole map+reduce" to
"map + first reduce token".
Tests: event ordering with stubbed LLM/stream.
Commit: `feat(retrieval): stream scoped summary reduce step`

### Step 7 — Scoped-summary breadth: two-level reduce (~150 docs)
Only if Phase 2 shipped the 30-doc cap (verify). Raise
`scoped_summary_max_docs` (config) toward 150: map batches → **group
summaries** (one intermediate structured call per ~8–10 doc summaries,
grouped by year or sub-theme from catalog metadata) → final reduce over group
summaries. Keep the ≤5-doc single-call and ≤30-doc single-reduce paths
untouched; the two-level path activates only above the single-reduce cap.
Honest truncation stays: beyond the cap, state the distribution + top-N.
Commit: `feat(retrieval): two-level reduce for large summary scopes`

### Step 8 — Final tuning sweeps (config-only, eval-driven)
With all features in place, run eval sweeps and settle final values with the
user: `retrieval_candidate_k` (40/70/100), `context_token_budget`
(9000/12000), `rerank_score_threshold`, `corrective_min_score`,
`multi_query_paraphrases` (2/3), semantic-cache threshold sanity check, and
the multi-query / keyword-leg / HyDE / corrective-loop flag states. Deliver a
summary table (option → per-class eval deltas → latency deltas) and apply the
chosen values to `.env` guidance / config defaults as the user prefers.
Commit: `chore(retrieval): tuned retrieval and generation defaults`

## 5. Latency accounting

- Step 1–2: off the answer path entirely (one INSERT on user action).
- Step 3: replaces a payload filter with one ms-scale SQL query before search
  — net ≈ 0; catalog errors fall back without delay.
- Step 4: SQL-only, structured route.
- Step 5: HyDE call runs concurrently with base search → +~300–600 ms when
  enabled, same envelope as multi-query.
- Step 6: **improves** perceived latency (streamed reduce).
- Step 7: large scopes only; parallel maps keep wall-clock in the §13.10
  scoped-summary budget; two-level adds one sequential LLM round for >30-doc
  scopes — acceptable there.
- Step 8: config-only.

## 6. Blocked by the ingestion freeze — do NOT implement

Listed so a future session doesn't reinvent them while the freeze holds:
- **True sparse vectors** (BM25/SPLADE) — requires sparse vectors written at
  ingest time and a collection schema change.
- **Payload enrichment** (e.g. per-document `source_authority`, summary-at-
  ingest fields) — requires chunker/indexer changes and re-indexing.
- **Embedding model/dimension changes** — requires full re-embed.
If the freeze is ever lifted, revisit plan §13.6 (sparse) first.

## 7. Open decisions to confirm with the user

1. **Feedback auth**: is `/feedback` open to anonymous callers when
   `auth_enabled=False` (matches /chat today), and should verdicts be
   deduplicated per response_id per caller?
2. **HyDE go/no-go**: review the Phase 3 retrieval eval failures together
   before building step 5 at all.
3. **Step 7 go/no-go**: is >30-doc summarization actually requested by users?
   (Feedback/report data from steps 1–2 can answer this — consider running
   those first for a few weeks, which is why they are steps 1–2.)
4. **Final defaults** (step 8): each flip is a joint decision on the eval
   summary table; nothing is changed silently.
5. **Frontend**: who wires the `response_id` + feedback UI into the chat
   client? (Backend contract is delivered by step 1; the UI is outside this
   repo's retrieval layer — `ui-render` community exists in the codebase, ask
   the user whether to wire it there too.)
