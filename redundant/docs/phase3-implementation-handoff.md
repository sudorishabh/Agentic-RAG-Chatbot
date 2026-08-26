# Phase 3 Implementation Handoff — Evaluation, Quality & Source Preference

Self-contained context for implementing Phase 3 of
`docs/retrieval-response-architecture-plan.md` (§6, §9, §12, §13.1, §13.2,
§13.4, §13.5, §13.8, §13.9, §13.10). Companion to
`docs/phase1-implementation-handoff.md` (system snapshot, schemas, code idiom,
test patterns) and `docs/phase2-implementation-handoff.md` — read both first;
nothing from them is repeated here.

Phase 3 also absorbs the plan's **Phase 1b** items (reranker switch, semantic
cache hardening, self-consistency voting, few-shot packs, buffered
faithfulness): they are eval-gated quality changes, and Phase 3 is where the
eval harness that gates them gets built. **Build the harness first, then flip
things** — that ordering is the point of this phase.

**Precondition:** Phases 1 and 2 are implemented and committed (both were
step-approved, so details may differ from their handoffs). **Verify §2 against
the actual code before writing anything.**

---

## 1. Hard constraints (unchanged)

1. **Ingestion frozen**: zero edits under `app/ingestion/` and to
   `app/deps.py`. Additive retrieval-side `app/config.py` settings allowed.
2. **Qdrant `documents` collection**: reads only. (The semantic cache lives in
   its own collection, `semantic_cache` — modifying *that* is allowed; it is
   retrieval-owned.) Eval runs are read-only against `documents`.
3. **GPT-4o-mini only** — including as the eval/faithfulness judge. Judging
   must be decomposed (claim-level binary verdicts, per-dimension rubrics),
   never one holistic score.
4. **Latency**: nothing on the request path may add an unbounded or ungated
   LLM call. Judging of production traffic is async, off the request path.
5. **Fail-open everywhere**; the user commits manually.

## 2. Assumed post-Phase-2 state (VERIFY FIRST)

Phase 1: unified `QueryAnalysis` (structured slots, `timeline` format,
`ProcessedQuery.analysis`); router consumes analysis (no second parse); count
fall-through guard; format renderers; author/tag QA filters; website-precedence
+ count-guard prompt rules; `scripts/create_payload_indexes.py`.

Phase 2: `app/retrieval/catalog.py` (id-set/attachment/author readers);
`app/retrieval/scoped_retrieval.py`; `scoped_summary` intent + summarizer;
lookup→content chaining; attachment supplementation on `detailed`;
`app/retrieval/fusion.py` (RRF) + multi-query behind `multi_query_enabled`
(default False); keyword leg + full-text index script.

Also verify which scripts the user has actually **run** against Qdrant
(payload indexes, full-text index) — several flips below depend on them.

Relevant existing plumbing for this phase:
- `app/generation/faithfulness.py`: `validate_markers`, `verify(answer,
  blocks) -> FaithfulnessReport` (single holistic LLM verdict — to be
  decomposed), `correction_note()`; wired in `rag._grounded_answer` behind
  `faithfulness_check` (default False) and in the buffered branch of
  `stream_answer`.
- `app/cache/semantic_cache.py`: Qdrant-backed, `lookup()` gated by
  `semantic_cache_threshold` (0.97) + `scope` partition
  (`redis_cache.semantic_partition(tenant, groups, top_k, answer_format)`);
  `store()` puts `{"result", "scope", "expires_at"}`.
- `app/observability/metrics.py`: `record_query_metrics(latency_ms, intent,
  used_chunks, has_citations, answered, conflict, cached, components, stages)`,
  `collect_into(stages)`; spans land per-stage timings.
- `app/retrieval/reranker.py`: providers embedding/llm/cross_encoder/cohere;
  `Candidate.semantic_score` carries the raw relevance score (the corrective
  loop's gate signal).
- Website preference: `prefer_website_enabled` (False), `_dual_search`,
  `build_context(segregate=)`, `website_max_slots`/`website_chunk_floor`,
  docs at `docs/website-preference-retrieval.md` and
  `docs/website-preference-testing.md` (read both before step 8).
- SSE stream contract (`rag.stream_answer` → `app/api/chat.py`): events
  `{"type": "token"|"sources"|"done"}` — step 7 adds `"correction"`.

## 3. What Phase 3 builds

```
scripts/eval/           golden.jsonl (labeled queries, 5 classes)
                        run_eval.py  (offline pipeline runs → report)
                        judges.py    (decomposed 4o-mini judging)
   │
   ▼  eval numbers gate every flip below
reranker provider + candidate_k ─┐
semantic-cache hardening         ├─ config/code flips, one at a time,
multi_query / keyword leg        │  before/after eval comparison
prefer_website_enabled           ┘
   +
self-consistency routing votes · few-shot packs · buffered faithfulness ON
streaming post-hoc verify + correction event + cache repair
numeric claim check · citation-coverage metric · async 100% judging
corrective retrieval loop (gated)
```

## 4. Working protocol (same as before)

One small step → run `python -m pytest tests/ -q` → one-line commit message
(no body, no attribution, no "Step N") → **wait for approval**. Eval runs that
need live services (Qdrant/MySQL/Azure) are executed only with the user's
go-ahead and never during an active ingestion run.

## 5. Steps (in order; one commit each)

### Step 1 — Golden dataset schema + seed set (`scripts/eval/golden.jsonl`)
One JSON object per line:
```json
{"id": "cnt-001", "class": "analytics", "question": "How many research papers were published in 2024?",
 "expect": {"intent": "structured", "operation": "count", "bundle": "research_papers",
            "sql_check": {"fn": "count_documents", "kwargs": {"bundle": "research_papers",
                          "published_from": "2024-01-01", "published_to": "2025-01-01"}}}}
{"id": "ret-001", "class": "retrieval", "question": "grassland carbon sequestration in India",
 "expect": {"relevant_document_ids": ["<uuid>", "..."]}}
{"id": "gen-001", "class": "generation", "question": "...",
 "expect": {"must_contain": ["..."], "must_not_contain": ["..."], "format": "table"}}
{"id": "ref-001", "class": "unanswerable", "question": "What is TERI's Bitcoin strategy?",
 "expect": {"refusal": true}}
{"id": "rte-001", "class": "routing", "question": "show a table of GHG emissions by sector from the Thoothukudi report",
 "expect": {"intent": "qa", "answer_format": "table"}}
```
Seed ~30–40 items across the 5 classes from the live corpus (query MySQL for
real bundles/themes/authors/titles to author realistic items — coordinate with
the user; they know the content). Include the §11.6 boundary pairs as routing
items. A `README.md` in `scripts/eval/` documents the schema and how to add
items. Target per plan: grow to 150–250 items over time.
Commit: `feat(eval): golden dataset schema and seed set`

### Step 2 — Eval runner (`scripts/eval/run_eval.py`)
Offline runner against live services (env-guarded; refuses to start if Qdrant/
MySQL unreachable). Per item, by class:
- **routing**: call `query_processor.process()` only; compare intent/
  operation/format/facets → accuracy per field.
- **analytics**: run the full `_prepare` path; independently execute
  `expect.sql_check` against MySQL; assert the answer contains that exact
  number → must be 100%.
- **retrieval**: call `rag.search_blocks()`; compute recall@k / MRR over
  `relevant_document_ids`; record website-lead rate.
- **generation**: run `answer_query()`; check must/must-not strings, format
  shape (table = has `|` header row; timeline = dated lines), citation
  presence.
- **unanswerable**: answer must equal `prompts.REFUSAL`.
Collect per-stage latencies via `metrics.collect_into`. Output: JSON results
file + markdown summary (per-class scores, p50/p95 per stage, failures listed
with ids). Flags: `--only class`, `--ids`, `--baseline <results.json>` (print
deltas vs a previous run). Caches must be **bypassed** for eval runs (fresh
answers): thread a `use_cache=False` through `_prepare` or monkeypatch-style
disable via settings in the runner process — pick the least invasive; do not
change production defaults.
Commit: `feat(eval): offline eval runner with per-class metrics and baseline diff`

### Step 3 — Decomposed judges (`scripts/eval/judges.py`) + citation coverage
- `extract_claims(answer) -> list[Claim]` — one structured 4o-mini call
  (few-shot: one worked example), claims carry their `[n]` citations.
- `claim_supported(claim, block_text) -> bool` — one binary structured call
  per claim, batched with a bounded ThreadPoolExecutor.
- `judge_faithfulness(answer, blocks) -> report` — composes the two;
  replaces the holistic `faithfulness.verify` **for eval use** (production
  wiring changes in step 7; do not modify `app/generation/faithfulness.py`
  yet).
- `judge_relevance(question, answer) -> 1..5` — rubric prompt, few-shot with
  two anchored examples (a 2 and a 5).
- `citation_coverage(answer) -> float` — deterministic: fraction of sentences
  (simple split) containing `[\d+]`. Lives here but is imported by step 9 for
  production metrics.
Wire all into `run_eval.py` for generation-class items.
Commit: `feat(eval): claim-level faithfulness and relevance judges`

### Step 4 — Baseline run + few-shot packs
1. Execute a full eval run with the user (services up, ingestion idle) —
   this is **the baseline**; commit the results file under
   `scripts/eval/results/` (small JSON, versioned on purpose).
2. Add the few-shot packs (§13.2.3) to `app/generation/prompts.py`:
   a compact worked example (tiny numbered context → ideally-cited answer)
   in `GROUNDED_SYSTEM_PROMPT`; conditional table/timeline exemplars appended
   with their directive only when that format is active. Keep the default-path
   prompt lean; measure prompt sizes in the commit description to the user.
3. Re-run eval; keep the packs only if generation-class scores improve or
   hold. Commit: `feat(generation): few-shot exemplars for grounded and formatted answers`

### Step 5 — Self-consistency routing votes (`query_processor.py`)
Behind `analysis_votes: int = 1` (config, additive): when >1, fire N analysis
calls concurrently (ThreadPoolExecutor; temperature ~0.7 via a per-call
override — `get_llm` is lru_cached per (temperature, streaming), so
`get_llm(temperature=0.7)` is fine), majority-vote per field (intent,
operation, answer_format, source_type; for free-text slots take the modal
value, ties → first non-null; intent tie → `"qa"`). Fail-open: any vote
erroring is dropped; all erroring → passthrough as today.
Eval-gate: routing-class accuracy with votes=3 vs baseline; recommend
flipping `analysis_votes=3` only if it wins.
Commit: `feat(query): self-consistency voting for query analysis`

### Step 6 — Semantic-cache hardening (`app/cache/semantic_cache.py`)
(Retrieval-owned collection — edits allowed.)
1. `store()` additionally persists the query's facet fingerprint (compact dict:
   source_type, theme term_uuids, date bounds, language, author) in the
   payload.
2. `lookup()` takes the same fingerprint and rejects hits whose stored
   fingerprint differs (post-filter on the returned point — one candidate,
   cheap).
3. Raise `semantic_cache_threshold` default 0.97 → 0.995.
Old entries without a fingerprint: treat as mismatch (they expire via TTL).
Tests: fingerprint match/mismatch paths with a fake client.
Commit: `fix(cache): semantic cache requires facet match and tighter threshold`

### Step 7 — Production faithfulness: buffered ON, streaming post-hoc
1. Port the decomposed claim-level verify into
   `app/generation/faithfulness.py` (keep `verify()` signature; internals
   become extract+check; holistic call removed). `rag._grounded_answer`
   keeps its verify→regenerate-once shape.
2. Streaming path (`rag.stream_answer`): after the token loop, when
   `faithfulness_check` is on — run verify post-hoc; if unfaithful, emit
   `{"type": "correction", "text": <corrected answer>, "reason": "faithfulness"}`
   **before** `sources`/`done`, and persist the corrected result to both
   caches (`_persist` already runs after assembly — ensure it stores the
   corrected version).
3. Numeric claim check (deterministic, always on, ~0 ms): extract numbers/
   years/percents from the answer (normalize thousands separators), verify
   each appears in at least one cited block's text; failures set a
   `numeric_mismatch` flag on the result and are logged to metrics (no
   auto-correction v1 — observe first).
4. Flip `faithfulness_check` default → True **only after** an eval run
   confirms the decomposed verifier's false-positive rate is acceptable
   (unfaithful-flag rate on golden generation items that judges clean).
Update `app/api/chat.py` / SSE docs for the new event type.
Tests: marker/regex logic, correction-event ordering with stubbed LLM.
Commit: `feat(generation): claim-level faithfulness with streaming correction events`

### Step 8 — Website preference: tune and enable (§6)
Read `docs/website-preference-retrieval.md` + `website-preference-testing.md`
first — the feature is fully built; this step is measurement.
1. Add a retrieval-class eval view: for mixed-coverage golden items, report
   website-lead rate, website block relevance (judge), and whether PDF depth
   still surfaces.
2. Sweep `website_chunk_floor` ∈ {0.25, 0.30, 0.35} and `website_max_slots`
   ∈ {1, 2, 3} offline via the runner (settings overridable per run).
3. Present results; on the user's pick, flip `prefer_website_enabled=True`.
Commit: `feat(retrieval): enable website-first retrieval with tuned thresholds`

### Step 9 — Async 100%-traffic judging + metrics
`app/observability/quality_monitor.py`: a bounded in-process queue + single
daemon worker thread. `rag._record` (or a hook beside it) enqueues
`(question, answer, block_texts, citations)` for non-cached, non-chitchat
results; the worker runs `citation_coverage` (always) and the claim-level
judge (sampling rate configurable, default 1.0 — cost is not a constraint),
then logs verdicts through `record_query_metrics`-style structured logs.
Queue full → drop silently (never block a request). Config (additive):
`quality_monitor_enabled: bool = False` (flip with user after smoke-testing),
`quality_judge_sample: float = 1.0`.
Tests: enqueue/drop behavior, worker happy path with stubbed judge.
Commit: `feat(observability): async answer quality monitor`

### Step 10 — Corrective retrieval loop (§13.5)
In `rag.retrieve` (or a wrapper in `_prepare`), behind
`corrective_loop_enabled: bool = False` + `corrective_min_score: float = 0.2`:
after rerank, if the top candidate's `semantic_score` < threshold — one
structured call: "the retrieved passages may not answer the question; suggest
one reformulated search query targeting the missing information" (few-shot:
one example) → embed → search → RRF-fuse with the original candidates →
rerank once more. Strictly one iteration; span-traced (`rag.corrective`);
fail-open. Eval-gate before flipping on: it must improve retrieval-class
recall on the golden set without pushing QA p95 past budget (§13.10: those
queries get < 5 s).
Commit: `feat(retrieval): one-shot corrective requery on low retrieval confidence`

## 6. Latency accounting

- Steps 1–4, 8: zero request-path impact (eval is offline; few-shot packs add
  only prompt prefill ≈ tens of ms).
- Step 5: votes run concurrently — TTFT impact ≈ the slowest of 3 mini calls
  (~0.5 s worst case vs 1 call; measure before flipping).
- Step 6: unchanged lookup cost; slightly lower hit rate by design.
- Step 7: streaming TTFT unchanged (verify is post-stream); buffered path
  +1–2 s when enabled; numeric check ~0 ms.
- Step 9: fully off the request path (queue put is O(1); drops when full).
- Step 10: +1.5–3 s but only for low-confidence queries; gated and flagged.

## 7. Out of scope for Phase 3

HyDE; feedback/satisfaction endpoint; streaming the scoped-summary reduce;
true sparse vectors; context-budget raise beyond eval-approved values;
anything editing `app/ingestion/` or `app/deps.py`. (Phase 4 per the plan.)

## 8. Open decisions to confirm with the user

1. **Reranker provider** (plan Phase 1b, §13.1 — gate with this harness):
   is an external Cohere API acceptable, or must it be the self-hosted
   cross-encoder (`sentence-transformers`, needs local weights/compute), or
   LLM-pointwise on 4o-mini? Then sweep `retrieval_candidate_k` 40 vs 100 in
   eval and flip config.
2. **Golden set authorship**: who supplies/validates ground-truth labels
   (especially `relevant_document_ids` and analytics expectations)? Assistant
   can draft from the live catalog; user must review before results are
   trusted.
3. **Committing eval results**: keep `scripts/eval/results/` in git
   (recommended, small JSON baselines) or gitignore it?
4. **`faithfulness_check` default flip** (step 7.4) and
   **`quality_monitor_enabled` flip** (step 9): explicit user sign-off after
   seeing eval/smoke numbers.
5. **Eval run windows**: full runs hit Azure OpenAI, MySQL and Qdrant
   (read-only) — confirm ingestion is idle and quota headroom exists before
   each run.
