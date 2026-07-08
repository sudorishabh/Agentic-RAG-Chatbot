# Design: preferring website content in retrieval (dual-retrieval / "Lane S")

**Status:** **Implemented** behind `prefer_website_enabled` (default off), on branch
`feat/website-preference-retrieval`. Approach: **dual retrieval in the application
layer** with **segregated presentation** (website content and references first, PDFs
after). Testing guide: [website-preference-testing.md](website-preference-testing.md).
**Date:** 2026-07-07
**Related:** [retrieval.md](retrieval.md) (§6), [configuration.md](configuration.md),
[generation.md](generation.md), [ingestion.md](ingestion.md)

> **History.** Earlier drafts of this doc explored a boost/gate mechanism and a
> Qdrant-native scoring approach ("Lane 1 / W2"). Those are superseded. This
> revision is written fresh around the chosen approach and folds the useful
> findings from the prior code reviews inline as guardrails (§9).

---

## 1. Problem

Answers are dominated by PDF content. We have **~11k PDFs** versus a much smaller
volume of Drupal **website** content. Retrieval is almost entirely semantic
similarity over one mixed pool, so:

- The single candidate pull (`retrieval_candidate_k = 40`) is overwhelmingly PDF,
  and the final `retrieval_top_k = 6` blocks that reach the LLM are too. Website
  content often **never even enters the candidate set** — so it cannot be
  preferred, presented, or cited, no matter what we do downstream.
- Even when website content *is* retrieved, the reranker's authority map
  **penalizes** it (`website = 0.65` vs `pdf = 1.0`), and the generation system
  prompt explicitly tells the model *"an official PDF outranks an older web
  article."* Both fight the goal.

**Root cause is availability, not ranking.** A weight, a boost, or a prompt
tweak can only reorder what was fetched; none can retrieve a website chunk that
the single similarity pull left behind. The fix must therefore change *how
candidates are fetched*.

## 2. Goal & scope

- **Goal:** when the website has something relevant to say, the answer should
  **lead with website content and cite it first**, with PDFs providing supporting
  depth after. This is now an explicit **segregation** requirement, not merely a
  soft lean (see §6).
- **"Website content" = `source_type == "website"`** — Drupal nodes, taxonomy
  descriptions, and blocks. *(A fresh Qdrant rebuild + full re-ingest is planned,
  so only `{pdf, pdf_attachment, website}` will exist — the legacy `article` value
  and its migration are no longer relevant.)*
- **"PDF content" = `source_type in {pdf, pdf_attachment}`.** Website-linked PDFs
  we harvest (policy briefs, reports) are `pdf_attachment` and count as **PDF**
  here, by decision. Confirmed in ingestion: a Drupal node yields one `website`
  document whose body is *only* Drupal-rendered text; each attached/in-body PDF is
  a **separate** `pdf_attachment` document. **No PDF text is ever stored under
  `source_type = website`.** (The website body may contain the PDF's *link text*,
  never its extracted content.)
- **Preference is a lean, not exclusion:** PDFs remain available so facts/depth
  and correctness are preserved. A minimum PDF presence is always kept.
- Out of scope: the structured (`drupal_router`) path — it already returns Drupal
  data and bypasses this pipeline. Chitchat — no retrieval.

## 3. Locked decisions

| # | Decision |
|---|---|
| 1 | **Dual retrieval in the app layer (Lane S).** Two Qdrant queries — one filtered to website, one to PDF — merged and reranked in Python. This is the only mechanism that *guarantees the website's best chunk is fetched*; it also keeps the door open for the cross-encoder/LLM rerankers, which cannot run inside Qdrant. |
| 2 | **Segregated presentation.** In both the answer and the reference list, website content comes **first**, PDFs after (§6). |
| 3 | **Website is a concise lead; PDFs carry the depth.** Website content is capped at `website_max_slots = 2` (users' website needs are typically satisfied in ~2 sources); PDFs fill the remaining slots (the majority) so answers keep depth. Lean, not exclusive. |
| 4 | **Adaptive split, driven by a per-chunk relevance floor + the website cap.** Website takes `min(relevant website chunks clearing the floor, website_max_slots)`; PDFs take the rest. No hardcoded ratio, no boost math, no separate gate (§5). |
| 5 | **Quotas + ordering enforced *inside* the context builder**, not before it — because dedup and the token budget prune *after* selection (§5.1). |
| 6 | **Authority map:** stop penalizing website. Remove the source-type authority map (it is largely dead config and its only live effect is a constant anti-website tilt); keep the `source_authority` per-document override hook for future use. *(Decision B, resolved.)* |

## 4. Proposed architecture

```
query
 │  (query_processor already extracts explicit source_type + language + date filters)
 │
 ├─ if the user EXPLICITLY asked for pdf/website (pq.source_type set):
 │     single pull honoring that filter → rerank → build_context (NO segregation,
 │     the user chose the type) → present as today.   [skip everything below]
 │
 └─ otherwise (prefer_website_enabled):
      embed the query ONCE, then two Qdrant pulls sharing that vector —
        WEBSITE pull  filter = pq.filters + source_type == website            (website_candidate_k)
        PDF pull      filter = pq.filters + source_type != website (NOT-website) (retrieval_candidate_k)
        (pq.filters carries language + published_at date range — preserved in BOTH pulls)
        (PDF pull = "not website" so any stray/unknown source_type stays retrievable — §13 #2)
                    │
                    ▼
        rerank the UNION once   ← one pass so scores are comparable; keep the RAW
                                  semantic score alongside the blended one (§7)
                    │
                    ▼
        build_context — GROUP-AWARE & SEGREGATED (§5, §6):
          • split ranked union into website vs PDF candidates
          • website slots = website chunks (rank order) clearing website_chunk_floor,
            capped at website_max_slots (= 2)
          • ALL remaining slots (up to top_k, within token budget) filled by top PDFs
          • dedup + token budget applied during the walk; website walked first so it
            wins website/PDF near-dup ties → the PDF drops into also_available
          • FINAL ORDER: website blocks first (by score), then PDF blocks (by score)
                    │
                    ▼
        generate — system prompt says context is grouped website-first; lead with
                   website-grounded content, supplement with PDF detail (§6)
                    │
                    ▼
        cite — website citations first, then PDF; frontend groups by type (§6)
```

Two Qdrant queries instead of one. Latency impact is small for the default
reranker and dominated by LLM generation regardless (§9). The website pull hits a
small filtered subset and is cheap; the two pulls may be run **concurrently** to
hide even that (currently sequential — acceptable, see §9).

### 4.1 Implementation code map (as built)

| Concern | Where | What |
|---|---|---|
| Dual pull + routing | `rag.py::retrieve`, `rag.py::_dual_search` | `dual = prefer_website_enabled and not source_type and answer_format != "table"`; embeds once, runs website + "not website" pulls, merges; `source_type` now threaded in from all three callers |
| "not website" filter | `hybrid_search.py::build_filter`, `search` | new `extra_must_not` param feeds Qdrant `must_not`; website pull uses `extra_filter=[source_type==website]`, PDF pull uses `extra_must_not=[source_type==website]` |
| Raw relevance score | `hybrid_search.py::Candidate.semantic_score`, `reranker.py::rerank` | `rerank` populates `semantic_score` (raw, pre-blend) on each returned candidate |
| Authority map removal | `reranker.py::_authority_score` | source-type map deleted; neutral 0.5 unless `source_authority` override |
| Segregated selection + order | `context_builder.py::build_context`, `_admit` | `segregate`, `website_max_slots`, `website_chunk_floor` params; two-pass admission; website-first order replaces `_order_for_attention` when segregating |
| Conflict exclusion | `context_builder.py::_flag_conflicts`, `_same_source_two_formats` | website↔its-own-`pdf_attachment` pair not flagged |
| Prompt + labels | `generation/prompts.py` | rule 6 (lead website, then PDF); `format_context_blocks` emits group headers when website-led (`_is_website_led`) |
| Citations | `retrieval/citations.py` | unchanged — website-first falls out of block order; `type` drives the two UI sections |
| Cache invalidation | `cache/redis_cache.py::_pref_fingerprint` | preference-config hash mixed into `response_signature` + `_sem_key` |
| Config | `config.py` | `prefer_website_enabled`, `website_candidate_k`, `website_max_slots`, `website_chunk_floor`; `context_token_budget` 6000→9000 |

## 5. The adaptive split

The split is **emergent**, driven by one number — the per-chunk relevance floor —
plus one cap — `website_max_slots`. No boost, no gate, no PDF floor needed.

Mechanism: after the single rerank over the union, the context builder walks the
website candidates in rank order and admits each that clears `website_chunk_floor`,
**up to `website_max_slots` (= 2)**. Every remaining slot (up to `top_k`, within the
token budget) is filled with the top PDF candidates. So website is a concise lead,
PDFs are the majority/depth.

Effective total sources ≈ `min(top_k, token_budget ÷ ~1800/block)` — at
`top_k = 6`, `context_token_budget = 9000` that's **~5 sources**.

| Scenario | Website (lead) | PDF (depth) — at N≈5 |
|---|---|---|
| ≥ 2 relevant website chunks | 2 (capped) | 3 |
| exactly 1 relevant | 1 | 4 |
| none clear the floor | 0 | 5 (behaves as today) |

The floor prevents padding the answer with weak website text; the cap keeps website
brief; PDFs get everything else, preserving depth/correctness. That's the whole
policy. Website still **leads** (shown/cited first) whenever ≥ 1 website chunk
clears the floor.

> **Why no boost or gate anymore.** In earlier drafts a β-boost pushed website up
> the ranked list and a relative-gap gate decided *whether* to prefer website.
> Segregation makes both redundant: presentation is now deterministic
> (website-first by construction), so we don't need to inflate website scores to
> "win" slots, and the "should we prefer?" question collapses into "are there any
> website chunks above the floor?" — which the per-chunk floor already answers. An
> optional relative gate remains available as a conservatism knob (open decision).

### 5.1 Why quotas & ordering must live in the context builder

`build_context` walks the ranked list and prunes via parent-expand, **cosine
dedup (≥ 0.92)** and the **token budget** until `top_k` blocks remain
(`context_builder.py`). So the final blocks are "top *survivors*," not "top
`top_k` ranked." Any quota or ordering decided *before* this stage is cosmetic —
dedup or the budget can drop the very blocks you reserved. Therefore the website
cap and the website-first ordering are enforced **inside** the builder, on the
surviving blocks.

Two useful consequences of walking website candidates first:

- On a website/PDF near-duplicate pair (a policy-brief node body vs its own
  attached PDF), the website block is admitted first, so dedup keeps it and the
  PDF lands in its `also_available` — cited as a secondary "full document" under
  the website citation. Exactly the presentation we want, for free.
- `build_context` always admits the first block regardless of token budget, so
  when any website chunk clears the floor, the lead block is a website chunk.

> **No PDF-floor shortfall to worry about now.** Because website is *capped* (≤ 2)
> rather than PDFs being *floored*, PDFs simply take all remaining slots — there is
> no reservation that can fail. The only budget interaction is the effective source
> count (§5), which we sized with `context_token_budget = 9000`.

## 6. Segregation: response & references (the core new requirement)

Website content leads; PDFs follow. This is enforced at three points:

1. **Context ordering (in `build_context`).** Final blocks are ordered **website
   first (by score), then PDF (by score)**, and `[n]` numbers are assigned in that
   order. This **replaces `_order_for_attention`** — we deliberately trade its
   "best-at-front-and-back" attention layout for deterministic website-first
   grouping (accepted trade-off; see §10 fit check).

2. **Generation (`prompts.py`).** Two changes to `GROUNDED_SYSTEM_PROMPT`:
   - **Remove** the current rule that *"an official PDF outranks an older web
     article."*
   - **Add:** the numbered context is grouped — website sources first, then PDF
     sources — and the answer should **lead with website-grounded content and then
     supplement with PDF detail**, still citing `[n]` after every claim.
   - `format_context_blocks` prepends a light group label so the model sees the
     boundary, e.g. a `— TERI website —` / `— PDF documents —` marker before each
     group (the per-block `(source_type · title · …)` hint already exists).

3. **References — two labeled sections (LOCKED).** The reference panel renders
   **two headed sections: "TERI website" first, then "PDF documents".** Because
   block order is website-first, the citation list already arrives website-first,
   and the existing `Citation.type` field (`website`/`pdf`) is the group key — so
   the **backend needs no schema change**; it already supplies an ordered,
   type-tagged list. Rendering the two headers is a **frontend change** (coordinate
   with the UI owner). *Optional:* add an explicit `group` field to `Citation` only
   if the frontend prefers not to infer sections from `type` — not required.

**Edge — table queries:** tables live overwhelmingly in PDFs, so forcing
website-first can bury a requested table. Open decision (§ open decisions):
when `answer_format == "table"`, relax segregation (allow the table-bearing PDF to
lead) or keep website-first regardless.

## 7. Relevance signal & thresholds

- The per-chunk floor uses the **raw semantic relevance score** from the active
  reranker (dense cosine by default; cross-encoder/Cohere if enabled). **Not** the
  pool-normalized value — with two pools, per-pool normalization isn't comparable.
  `rerank()` currently returns only the blended score, so it must be extended to
  **carry the raw semantic score through `Candidate` into `build_context`**, where
  the floor is checked (exposing it from `rerank()` alone is insufficient — the
  floor is enforced in the builder). *(Locked; was hole B.)*
- **Threshold scales are provider-specific.** Dense cosine ≈ [0,1]; the
  cross-encoder (`bge-reranker-v2-m3`) emits logits on a different scale; LLM
  scores are 0–1 but uncalibrated across batches. `website_chunk_floor` is only
  meaningful **per reranker provider** and must be re-tuned if the provider
  changes (store it namespaced by provider name).
- **Content-type bias.** A short Drupal blurb and a long dense PDF chunk score in
  systematically different similarity ranges against the same query vector, so the
  floor is a per-group judgement of "is this website chunk relevant at all," not a
  cross-type comparison — which is exactly why segregation (not a cross-pool score
  gate) is the right tool. A cross-encoder reduces this bias and is the
  recommended fast-follow (decision D).
- **LLM-reranker cap:** `_MAX_LLM_CANDIDATES = 40`. The union
  (`retrieval_candidate_k + website_candidate_k`, ~60 by default) exceeds it, so
  with `reranker_provider = llm` the provider silently falls back to dense scores.
  If using `llm`, shrink the pulls (e.g. 25 + 15). Not an issue for the default
  `embedding` provider or the cross-encoder.

## 8. Config knobs (all tunable, feature-flagged)

| Setting | Purpose | Proposed default |
|---|---|---|
| `prefer_website_enabled` | Master on/off; off = today's single-pool behavior | `false` at launch → flip to `true` after eval tuning (§12) |
| `website_candidate_k` | Website-only candidates to pull | `20` |
| `website_max_slots` | Max website blocks (the concise lead); PDFs take the rest | `2` |
| `website_chunk_floor` | Per-chunk relevance floor for a website slot | *TBD — tune in §11* |
| `retrieval_top_k` (existing) | Total context blocks | `6` |
| `context_token_budget` (existing) | Token ceiling for context; sized so ~5 blocks fit | **raise `6000` → `9000`** |

`website_chunk_floor` is deliberately **TBD**: raw cosine values aren't intuitive,
so we set it empirically in the eval step (§11) rather than guess. The
`context_token_budget` bump (6000→9000) is what gives PDFs room for ~3 depth
sources alongside the 2-source website lead — see §5 and §13 #1.

## 9. Guardrails & edge cases (folded from prior code reviews)

- **Correctness first:** capping website at `website_max_slots = 2` (rather than
  flooring PDFs) means PDFs always take the majority of slots, so answers keep
  depth and don't degrade to thin website blurbs.
- **Fail open:** any error in the dual-pull / selection → fall back to today's
  single-pool ranking. Never worse than current.
- **Explicit user intent (required for correctness):** `pq.filters` is injected as
  a *mandatory* Qdrant condition. A PDF pull combined with an explicit
  `source_type = website` filter is contradictory and returns zero results (and
  vice versa). So when `pq.source_type` is set, **skip the dual-pull** and run a
  single pool honoring the user's filter. `retrieve()` must therefore receive
  `pq.source_type` (today it only gets the opaque `filters` list).
- **Preserve non-source filters in BOTH pulls:** `pq.filters` can carry a
  `language` match **and** a `published_at` date range (new in
  `query_processor.py`). Each pull = `pq.filters` **plus** its own source_type
  condition — *combine, never replace*, or language/date filtering silently breaks.
- **Fresh setup, no `article`:** a planned Qdrant rebuild + re-ingest yields only
  `{pdf, pdf_attachment, website}`. Website pull = `source_type == website`; PDF
  pull = `source_type != website`. No legacy `article` handling needed.
- **Embed once:** compute the query vector once and pass it to both pulls
  (`search()` accepts `query_vector`); `search_blocks` doesn't pre-embed today, so
  `retrieve()` must embed internally when no vector is supplied.
- **Empty website pool / nothing clears the floor** → 0 website slots → PDF-only,
  presented as today. No forced, irrelevant website lead.
- **Cache invalidation on config change:** both pre-retrieval caches — the exact
  response cache (`response_signature`) and the **semantic cache**
  (`semantic_cache.lookup`, Qdrant-backed) — key only on
  question/tenant/groups/top_k (+ corpus version
  / answer_format). Neither knows about preference settings, so flipping
  `prefer_website_enabled` or tuning the floor would keep serving old-mode answers
  until TTL and pollute before/after tuning comparisons. **Add a
  retrieval-config fingerprint** (hash of the preference settings) to both
  signatures so any config change self-invalidates.
- **Single integration point:** `answer_query`, `stream_answer`, and `/search`
  (`search_blocks`) all route through `rag.retrieve()` — the dual-pull + segregated
  build lands once, there, covering all three surfaces.
- **`_order_for_attention` replaced:** segregation orders website-first instead of
  the attention-optimized layout. Accepted trade-off (§10).
- **Conflict flagging excludes the website↔own-PDF pair:** `_flag_conflicts` must
  not flag a website node and its own attached PDF (`pdf_attachment` whose
  `linked_article_uuid` matches the node UUID) as a conflict — they are the same
  content in two formats. Only genuinely distinct linked documents flag. *(Decided;
  see §13 #3.)*

## 10. Fit check — features changed & architectural shift

**Files changed**

| File | Change | Risk |
|---|---|---|
| `rag.py::retrieve()` | Dual pull, embed-once, explicit-intent skip; accept `pq.source_type`. | Medium |
| `retrieval/context_builder.py` | Group-aware selection, per-chunk floor, `website_max_slots` cap, **website-first ordering replacing `_order_for_attention`**, thread raw score, exclude website↔own-PDF from conflict flagging. | High (core) |
| `generation/prompts.py` | Remove "PDF outranks web article"; add "lead with website, supplement with PDF"; group labels in `format_context_blocks`. | Low |
| `retrieval/citations.py` | Website citations first, then PDF (falls out of block order; `type` already supports grouping). | Low |
| `retrieval/reranker.py` | Expose raw semantic score; remove the source-type authority map, keep `source_authority` override (decision B). | Low |
| `cache/redis_cache.py` | Preference-config fingerprint in `response_signature` + semantic key. | Low |
| `config.py` | New settings (§8). | None |

**Stays intact (verified):** structured Drupal/counting path (bypasses
`retrieve()`); chitchat (no retrieval); faithfulness check, `also_available`,
conflict flagging (operate on final blocks); tenant/ACL/is_parent/is_current/
section filters (both pulls run through `search()`).

**Deliberate carry-over (regresses silently if missed):** language + `published_at`
filters preserved in both pulls; explicit-intent skip; LLM-reranker 40-cap.

**Accepted behavior shifts:** attention-optimized block order → website-first
order; `context_token_budget` 6000 → 9000 (small latency/cost bump on content-rich
queries; buys PDF depth); table-query edge case (open decision); β-boost and
relative gate dropped in favour of the simpler floor + `website_max_slots` cap.

## 11. Evaluation plan (before rollout)

Per [testing-strategy], validate on the real TERI query set + Qdrant, comparing
current vs proposed:

1. A query set that *should* be website-answerable (overview / "what does TERI do
   on X" / latest) and one that's clearly PDF-only (specific paper method/data).
2. Metrics: does the website-answerable set now lead with website content and cite
   it first, **without** the PDF-only set regressing? Spot-check answer quality,
   not just source order.
3. Tune `website_chunk_floor` and confirm `website_max_slots` / `context_token_budget`;
   lock defaults per reranker provider. Capture before/after latency (§13 #1).
4. Sign-off in plain language before enabling by default.

## 12. Rollout

1. Land behind `prefer_website_enabled` (default off), on its own branch.
2. Tune the floor on the eval set; then flip default on.
3. Add the two labeled reference sections ("TERI website" / "PDF documents") in the
   UI once context composition and citation ordering are verified (LOCKED choice;
   frontend task — backend already supplies an ordered, type-tagged citation list).
4. Fast-follow: enable the cross-encoder reranker for a sharper, less
   length-biased relevance signal (decision D).

---

## 13. Final loophole test (2026-07-07, pre-implementation)

Fresh adversarial pass over the actual code paths (`retrieve`, `build_filter`,
`rerank`, `build_context` / `_flag_conflicts`, cache, `query_processor`) against
the locked design. Two strong issues change defaults/filters and must be settled
**before branching**; one medium must be fixed **during** implementation.

| # | Severity | Loophole | Fix |
|---|---|---|---|
| 1 | 🔴 strong → **DECIDED** | **Token budget caps effective blocks at ~3, not 6.** `build_context` counts parent-expanded text (~1800 tok/block) against `context_token_budget = 6000` → only ~3 blocks fit, starving PDF depth (~1 PDF slot). | **Raise `context_token_budget` 6000 → 9000** (~5 blocks). With `website_max_slots = 2`, that yields a 2-source website lead + ~3 PDF depth sources. `top_k = 6` unchanged. Latency/cost impact small and only on content-rich queries (§9). |
| 2 | 🔴 strong → **DECIDED** | **Dual pull is source-specific → unknown `source_type` becomes unretrievable.** Today's single search has no source filter. Two allow-list pulls would silently drop any chunk with an unexpected/null `source_type`. | **Website pull = `source_type == website`; PDF pull = `source_type != website`** (not-website), so every chunk is reachable by exactly one pull. Requires `build_filter` to accept an `extra must_not` (today `extra` only feeds `must`). Fresh rebuild yields only `{pdf, pdf_attachment, website}`, so orphans shouldn't exist — the not-website rule is free insurance. |
| 3 | 🟠 medium | **False "conflict" flags spike.** `_flag_conflicts` marks any two `_linked` blocks as `conflict = True` (not actual disagreement). A website node + its own attached PDF are linked; post-change they co-occur often, and when similar-but-not-near-dup (cosine < 0.92, so not deduped) both survive and get falsely flagged as conflicting. | **DECIDED:** exclude the website↔its-own-attached-PDF relation from conflict flagging (a website node and the `pdf_attachment` whose `linked_article_uuid` matches its node UUID are the same content in two formats). Genuinely distinct linked documents still flag. |
| 4 | 🟡 low | `rerank_score_threshold` (default 0.0) applies one PDF-calibrated bar *before* segregation; if enabled it could over-drop website chunks (content-type bias). | Keep at 0 unless tuned per-group. |
| 5 | 🟡 low | Parallelizing the two pulls needs a thread pool (sync Qdrant client). | `qdrant-client` queries are thread-safe; sequential is also acceptable (§9). |

**Confirmed already handled:** embed-once; explicit-intent skip; language +
`published_at` filters preserved in both pulls; LLM 40-cap; cache fingerprint;
dedup vectors present; `also_available` linking (`article_uuid` ↔
`linked_article_uuid`) works; `_order_for_attention` replacement must renumber `n`
in website-first order.

**Gate to start coding:** #1 and #2 resolved (config/filters decided); #3 committed
for implementation. Design is locked — implementation may begin.

---

## Decisions log

**Locked**
- **Approach:** dual retrieval in the app layer (Lane S), segregated presentation.
- **Split:** `website_max_slots = 2` (concise website lead), PDFs fill the rest;
  `retrieval_top_k = 6`; `context_token_budget` 6000 → **9000** (~5 sources: 2
  website + ~3 PDF). Adaptive via `website_chunk_floor` (TBD, tuned in eval).
- **Filters:** fresh Qdrant → types `{pdf, pdf_attachment, website}`; website pull
  = `source_type == website`, PDF pull = `source_type != website`.
- **References:** two labeled sections ("TERI website" then "PDF documents");
  backend orders website-first + `type` tag, frontend renders the headers.
- **Authority map** removed (keep `source_authority` override).
- **Conflict flag:** exclude the website↔its-own-PDF pair.
- **No boost, no relative gate** (floor + cap only).
- **`prefer_website_enabled`** launches `false`, flipped `true` after eval tuning.
- **Reranker:** dense cosine for v1; cross-encoder (`BAAI/bge-reranker-v2-m3`) as a
  fast follow.

**Still open — one product decision**
- **Table queries** — when `answer_format == "table"` (tables live in PDFs),
  keep website-first or let the table-bearing PDF lead? *Recommended default:
  bypass website preference for `table` so the requested table isn't buried; will
  implement this unless you say otherwise.*

**Deferred to eval (not blocking)**
- `website_chunk_floor` value; final confirmation of `context_token_budget` /
  `website_max_slots`; before/after latency capture.
