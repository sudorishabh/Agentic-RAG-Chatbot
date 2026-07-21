# Retrieval & Generation — End-to-End Flow

A plain-language walkthrough of what happens between a user asking a question and
the answer streaming back. Read this top-to-bottom; every stage links to the code
that runs it.

The whole pipeline lives in [`app/rag.py`](../app/rag.py), with the query-understanding
brain in [`app/retrieval/query_processor.py`](../app/retrieval/query_processor.py)
and helpers under [`app/retrieval/`](../app/retrieval/) and
[`app/generation/`](../app/generation/).

---

## 1. The big picture

```
                          ┌─────────────────────────────────────────────┐
   user question  ──────► │  stream_answer()  (app/rag.py)                │
   + chat history         └───────────────────────┬─────────────────────┘
                                                  │ calls
                                                  ▼
                          ┌─────────────────────────────────────────────┐
                          │  _prepare()  — shared front-matter            │
                          └───────────────────────┬─────────────────────┘
                                                  │
      ┌───────────────────────────────────────────┼───────────────────────────────┐
      │ STEP A: UNDERSTAND         STEP B: ROUTE (on intent)                        │
      │ process(question, history) ──► intent + search_query + answer_format + facets│
      └───────────────────────────────────────────┼───────────────────────────────┘
                                                  │
        ┌──────────────┬──────────────────────────┼───────────────────────┐
        ▼              ▼                          ▼                        ▼
   "chitchat"     "structured"              "scoped_summary"            "qa"  (default)
   plain LLM      catalog lookup            summarize a doc set         FULL RAG
   reply,         (MySQL, no vectors)       (falls back to qa           │
   no retrieval   (may fall back to qa       if scope empty)            │
                   for one named doc)                                   ▼
                                                          ┌─────────────────────────┐
                                                          │ STEP C: EMBED + CACHE   │
                                                          │ STEP D: RETRIEVE        │
                                                          │ STEP E: GENERATE        │
                                                          │ STEP F: VERIFY + STORE  │
                                                          └─────────────────────────┘
```

Two things do all the routing:

1. **`process()`** turns the raw turn into a structured `QueryAnalysis` — most
   importantly an **intent** (the top-level router) plus a rewritten `search_query`,
   an `answer_format`, and metadata `filters`.
2. **`_prepare()`** reads that intent and sends the request down one of four paths.

---

## 2. The four intents (the master switch)

Intent is decided by an LLM, not by keywords. It is the single most important
value in the pipeline because it selects the entire downstream path.

| Intent | What it means | Path taken | Retrieval? |
| --- | --- | --- | --- |
| `qa` | Answerable from document *content* (the default & fallback) | Full RAG: embed → retrieve → generate | ✅ vector search |
| `structured` | A question about the *documents themselves* — count / list / lookup by type, author, theme, date | Catalog query via `drupal_router` (MySQL metadata) | ❌ (unless it resolves to one named doc → falls through to qa) |
| `scoped_summary` | "Summarize the *set* of docs matching theme/author/period/type" | `summarizer.summarize_scope` | ✅ scoped |
| `chitchat` | Greetings, thanks, meta ("what can you do?") | Plain conversational LLM reply | ❌ none |

> **Rule of thumb the classifier follows:** data reported *inside* a document
> (a figure in a report) is `qa`; questions about the *catalog* (how many reports
> exist) are `structured`. Summarizing **one named** document is `qa` with
> `answer_format="summary"`; summarizing a **set** is `scoped_summary`.

---

## 3. STEP A — Query understanding (how intent is decided)

**Code:** [`query_processor.py::process`](../app/retrieval/query_processor.py) → returns a `ProcessedQuery`.

The classifier is a single **structured-output LLM call** guided by the
`_ANALYSIS_SYSTEM` prompt (which spells out every intent, format, and facet rule).
Given the last ~6 turns of history + the latest turn, it emits a `QueryAnalysis`:

| Field | Purpose | Used by |
| --- | --- | --- |
| `intent` | Top-level route | `_prepare` |
| `search_query` | Standalone, pronoun-resolved rewrite of the turn | all retrieval |
| `answer_format` | `default`/`list`/`table`/`summary`/`detailed`/`timeline` | retrieval knobs + generation shape |
| `source_type` | `pdf` / `website` if the user pinned one | retrieval filter |
| `theme` / `author` / `tags` / `date_from` / `date_to` / `language` | Facet scope | `_facet_filters` → Qdrant filters |
| `operation` / `bundle` / `group_by` / `title_contains` / `limit` | Structured-path slots | `drupal_router` |

### 3a. Self-consistency voting (optional, for robustness)

Controlled by the `analysis_votes` setting ([`process`](../app/retrieval/query_processor.py)):

- **`analysis_votes == 1`** → one call at the pinned parsing temperature (`get_structured_llm`).
- **`analysis_votes > 1`** → [`_voted_analysis`](../app/retrieval/query_processor.py) fires
  N concurrent samples at **temperature 0.7** and majority-votes **each field**
  independently via [`_merge_votes`](../app/retrieval/query_processor.py) → [`_vote`](../app/retrieval/query_processor.py).

The tie-break is deliberate: for the **`intent`** field, a tie falls back to **`qa`**
(the safe route — a mis-routed qa is caught by downstream guards, but a wrong
structured/summary route is harder to recover). Other fields on a tie take the
first non-null value. Errored samples are dropped; if *all* fail → passthrough.

### 3b. It never hard-fails

Any exception (or all votes failing) returns a **passthrough**: `intent="qa"`,
`search_query = original question`, no filters. Query understanding can degrade
retrieval quality but can never break the request.

### 3c. Facets become Qdrant filters

[`_facet_filters`](../app/retrieval/query_processor.py) translates the scope
fields into Qdrant `FieldCondition`s:
theme (UUID-or-name, rename-proof via [`_theme_condition`](../app/retrieval/query_processor.py)),
author, tags, `source_type`, `language`, and a `published_at` `DatetimeRange`
from `date_from`/`date_to`. These ride along on every search in the qa path.

---

## 4. STEP B — Routing on intent

**Code:** [`_prepare`](../app/rag.py). It returns either a **finished result**
(`chitchat`, a structured lookup, a scoped summary, a cache hit, or a no-context
refusal) or a `_Generation` object meaning "still needs a grounded answer".

```
process() → pq.intent
   │
   ├─ "chitchat"        → _chitchat()  → return finished (empty citations)
   │
   ├─ "structured"      → resolve_lookup_document(pq.analysis)
   │                        ├─ names ONE title? → add document_id filter, fall through to QA
   │                        └─ else → answer_structured()  → return finished (from MySQL catalog)
   │
   ├─ "scoped_summary"  → summarize_scope()
   │                        ├─ scope resolves → return finished
   │                        └─ empty scope   → fall through to QA
   │
   └─ "qa" (+ fall-throughs) → STEP C onward
```

Note the two **fall-throughs**: a structured question that turns out to be about
one specific document, and an unresolvable summary scope, both drop into the qa
pipeline rather than failing.

---

## 5. STEP C — Embed + cache (qa path only)

**Code:** [`_prepare`](../app/rag.py) lines ~596–606.

1. **Embed** the `search_query` once (`embed_query`) — the vector is reused
   everywhere downstream so we never embed the same query twice.
2. **Semantic cache lookup** ([`app/cache/semantic_cache.py`]) keyed by the query
   vector + tenant + user groups + `answer_format` + a facet fingerprint. A hit
   returns the stored answer immediately with `cached: true` — no retrieval, no
   generation.

---

## 6. STEP D — Retrieval (the heart of RAG)

**Code:** [`retrieve()`](../app/rag.py). Turns a query + vector + filters into a
short list of `ContextBlock`s ready to feed the LLM.

### 6.1 Decide which retrieval strategies to enable

Three booleans are computed up front from intent/format/scope:

| Flag | Turns on when… | Effect |
| --- | --- | --- |
| `dual` | website-preference on, **no** pinned `source_type`, format ≠ `table` | Two pulls (website + "not website") so the website's best chunks aren't drowned out by PDFs — [`_dual_search`](../app/rag.py) |
| `multi` | multi-query on, **intent == `qa`**, no `source_type`, no `filters`, query ≥ 5 words | Recall expansion via LLM paraphrases |
| `keyword_terms` | `keyword_leg_enabled` and the query has salient terms | Adds an exact-match (full-text) leg |

This is the one place **intent** itself gates retrieval: paraphrase expansion is
reserved for open-ended `qa`. The rest is driven by `answer_format` / scope.

### 6.2 The searches (run in parallel, then fused)

```
                 base pull  ─────────────┐
  (dual? website + not-website)          │
                                         ├──►  RRF fusion  ──►  candidate list
  paraphrase pulls (if multi) ───────────┤   (rank-based,        (up to ~40)
                                         │    fusion.py)
  keyword pull (if terms) ───────────────┘
```

- **Dense search** — [`hybrid_search.py::search`](../app/retrieval/hybrid_search.py):
  Qdrant `query_points` over the query vector. A **mandatory** filter always applies
  ([`build_filter`](../app/retrieval/hybrid_search.py)): `is_parent=false`,
  `is_current=true`, tenant match, ACL match over `user_groups`, and it excludes
  non-searchable sections (TOC / references / glossary). Facet filters from STEP A
  are appended here.
- **Multi-query** — [`_paraphrases`](../app/rag.py) asks the LLM for N alternative
  phrasings (temp 0.7), each searched with [`_paraphrase_search`](../app/rag.py).
- **Keyword leg** — [`_extract_key_terms`](../app/rag.py) pulls quoted phrases,
  Capitalized Bigrams, ACRONYMs, and years (the things dense vectors handle worst),
  then [`_keyword_search`](../app/rag.py) does a `MatchText` pull. Fails open to `[]`.
- **Fusion** — [`fusion.py::rrf`](../app/retrieval/fusion.py) merges all rankings by
  **rank** (`score = Σ 1/(60 + rank)`), so incomparable scores (cosine vs full-text)
  combine cleanly. Skipped when there's only the base pull.

### 6.3 Rerank

**Code:** [`reranker.py::rerank`](../app/retrieval/reranker.py).

Re-scores candidates with a **semantic** score from the configured provider
(`embedding` dense score / `cross_encoder` / `cohere` / `llm`), normalizes to
[0,1], then **blends** with recency and a neutral authority baseline
(weights `rerank_recency_weight` / `rerank_authority_weight`). A `table_boost` is
added to table-bearing chunks when `answer_format == "table"`. Candidates below
`rerank_score_threshold` are dropped. Each survivor keeps its **raw** semantic
score in `semantic_score` for the website floor later.

### 6.4 Corrective loop (one shot)

**Code:** [`_corrective_requery`](../app/rag.py).

If the corrective loop is enabled **and** the top result's semantic score is below
`corrective_min_score`, the system reformulates the query once (aim at what the
weak results missed), searches again, RRF-fuses with the current ranking, and
reranks once more. Strictly **one** iteration; any failure keeps the original.

### 6.5 Build the context

**Code:** [`context_builder.py::build_context`](../app/retrieval/context_builder.py).

Walks ranked candidates and admits each block subject to:

- **Parent expansion** — a child chunk is replaced by its larger parent chunk text
  (better context for the LLM), fetched via [`_fetch_parents`](../app/retrieval/context_builder.py).
- **De-duplication** — near-duplicate blocks (cosine ≥ `dedup_cosine_threshold`)
  are dropped; if the dup is a *linked* other-format copy it's recorded in
  `also_available` instead.
- **Token budget** — stops once `context_token_budget` is reached.
- **Website segregation** (when `dual`): website blocks lead (capped by
  `website_max_slots`, gated by a `website_chunk_floor` on raw relevance), PDFs fill
  the rest; final order is website-first.
- **Attention ordering** (non-dual): [`_order_for_attention`](../app/retrieval/context_builder.py)
  interleaves so the strongest blocks sit at the start and end.
- **Conflict flagging** — [`_flag_conflicts`](../app/retrieval/context_builder.py)
  marks linked blocks that disagree (but not a website + its own attached PDF).

Each admitted block becomes a numbered `ContextBlock` (`n`, `text`, `payload`,
`score`, `conflict`, `also_available`).

### 6.6 Attachment supplement (detailed answers only)

If `answer_format == "detailed"`, [`_supplement_attachments`](../app/rag.py)
does one extra bounded pull of PDF chunks attached to admitted website blocks that
weren't already represented, then reranks and rebuilds. Any failure keeps the
original blocks.

### 6.7 No blocks? Refuse.

If retrieval yields nothing, `_prepare` returns the `REFUSAL` string
("I don't have information on that in the available sources.") — the system never
guesses without evidence.

---

## 7. STEP E — Generation

**Code:** streaming [`_generate_stream`](../app/rag.py), buffered
[`_generate`](../app/rag.py) / [`_grounded_answer`](../app/rag.py); prompts in
[`app/generation/prompts.py`](../app/generation/prompts.py).

### 7.1 Build the system prompt

[`_build_system`](../app/rag.py) = `GROUNDED_SYSTEM_PROMPT`
+ an optional **format directive** + an optional **correction note**.

- `GROUNDED_SYSTEM_PROMPT` enforces the core rules: answer **only** from the
  numbered context, cite `[n]` after every claim, reply with the exact refusal if
  the answer isn't present, don't invent sources, treat context text as reference
  (not instructions), lead with website sources when present, and never state
  corpus totals.
- [`format_directive`](../app/generation/prompts.py) appends per-format shaping
  (list / table / summary / detailed / timeline) plus a tiny worked exemplar for
  `table` and `timeline`. `default` adds nothing (let the model choose the shape).

### 7.2 Format the context

[`format_context_blocks`](../app/generation/prompts.py) renders each block as
`[n] (source · title · p.X · section · published…)` + text. When the context was
segregated it inserts `— TERI website —` / `— PDF documents —` group headers.

### 7.3 Produce the answer

The chain is `prompt | get_llm() | StrOutputParser`. In the streaming entrypoint
tokens are yielded to the client as `{"type": "token"}` events as they arrive.

---

## 8. STEP F — Verify, assemble, store

### 8.1 Faithfulness check (optional, `faithfulness_check`)

**Code:** [`app/generation/faithfulness.py`](../app/generation/faithfulness.py).

- [`validate_markers`](../app/generation/faithfulness.py) strips any `[n]` citation
  pointing outside the real block count (always runs).
- [`verify`](../app/generation/faithfulness.py) extracts **atomic claims**, then
  runs one binary *supported / not-supported* verdict per claim (in parallel)
  against its cited blocks. If any claim is unsupported, the answer is **regenerated
  once** with a correction note. In streaming, the correction is emitted as a
  `{"type": "correction"}` event and the corrected text is what gets cached.
- Fails open to "faithful" at every stage.

### 8.2 Numeric check (observe-only)

[`numeric_mismatches`](../app/generation/faithfulness.py) deterministically flags
numbers in the answer that appear in no cited block. In v1 this is **logged only**,
never auto-corrected, and surfaced as `numeric_mismatch` in metrics.

### 8.3 Assemble, cache, record

- [`_assemble`](../app/rag.py) builds the final dict: `answer`, `citations`
  ([`build_citations`](../app/retrieval/citations.py)), `intent`, `answer_format`,
  `used_chunks`, `conflict`, `numeric_mismatch`, `cached: false`.
- [`_persist`](../app/rag.py) stores the result in the semantic cache (keyed as in
  STEP C) so an equivalent future query short-circuits.
- [`_record`](../app/rag.py) emits query metrics (latency, intent, chunk count,
  citations present, answered vs refused, conflict, cached, per-stage timings).

### 8.4 The SSE event sequence (streaming)

```
{"type":"token", "text": "..."}          # repeated as the answer streams
{"type":"correction", "text":"...",       # only if faithfulness triggered a rewrite
 "reason":"faithfulness"}
{"type":"sources", "citations":[...],     # final metadata
 "intent":"qa", "answer_format":"...",
 "used_chunks":N, "conflict":false}
{"type":"done"}
```

Finished results from STEP B/C (chitchat, structured, scoped summary, cache hit,
refusal) are emitted through the same shape via
[`_stream_result`](../app/rag.py) — one token event with the whole answer, then
sources + done.

---

## 9. Fallbacks & safety nets (why it rarely breaks)

| Stage | If it fails… |
| --- | --- |
| Query analysis / voting | Passthrough: `intent="qa"`, raw query, no filters |
| Intent tie in voting | Falls to `qa` (safe route) |
| Structured lookup | Falls through to qa (as does an unresolvable summary scope) |
| Term resolution (theme filter) | Degrades to name-only filter |
| Multi-query / keyword / corrective / attachment legs | Each fails open to `[]` / the prior ranking |
| Rerank provider (llm / cross-encoder / cohere) | Falls back to dense score |
| Parent fetch | Falls back to child chunk text |
| Retrieval empty | Returns the exact `REFUSAL` string |
| Faithfulness at any stage | Assumes faithful (never blocks the answer) |

---

## 10. Key settings (knobs)

All in [`app/config.py`](../app/config.py) / `.env`:

| Setting | Controls |
| --- | --- |
| `analysis_votes` | 1 = single analysis call; >1 = N-way self-consistency vote |
| `retrieval_top_k` / `retrieval_candidate_k` | final blocks / candidates pulled per search |
| `prefer_website_enabled`, `website_candidate_k`, `website_max_slots`, `website_chunk_floor` | dual pull + website-first context |
| `multi_query_enabled`, `multi_query_paraphrases` | paraphrase recall expansion |
| `keyword_leg_enabled` | exact-match full-text leg |
| `reranker_provider`, `rerank_model`, `rerank_score_threshold`, `rerank_recency_weight`, `rerank_authority_weight`, `rerank_table_boost` | reranking |
| `corrective_loop_enabled`, `corrective_min_score` | one-shot corrective requery |
| `context_token_budget`, `dedup_cosine_threshold` | context building |
| `faithfulness_check` | claim-level verify + one regeneration |

---

## See also

- [retrieval.md](retrieval.md) — reference-style module detail
- [generation.md](generation.md) — LLM factories & grounding prompts
- [architecture.md](architecture.md) — module map & request lifecycle
- [website-preference-retrieval.md](website-preference-retrieval.md) — the dual-pull design
