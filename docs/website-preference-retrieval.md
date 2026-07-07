# Design: preferring website content in retrieval

**Status:** Design / discussion. No code yet. A few [open decisions](#open-decisions)
remain before implementation.
**Date:** 2026-07-03
**Related:** [retrieval.md](retrieval.md), [ingestion.md](ingestion.md)

---

## 1. Problem

Answers are dominated by PDF content. We have **~11k PDFs** (a large document
corpus) versus a much smaller volume of Drupal **website** content. Retrieval is
almost entirely semantic similarity, so:

- The candidate pool (`retrieval_candidate_k = 40`) is overwhelmingly PDF, and the
  final `retrieval_top_k = 6` blocks that reach the LLM are too. Website content
  often **never even enters the candidate set**.
- The reranker's ranking is `blended = 0.90·semantic + 0.05·recency + 0.05·authority`.
  Authority is keyed by source type — and it currently **penalizes** website:
  `_AUTHORITY = {pdf: 1.0, pdf_attachment: 1.0, article: 0.65, …}`. So Drupal
  content is treated as *lower* authority, and even that only moves 5% of the score.

Net effect: the website loses on both volume and weighting, so answers rarely lean
on it.

## 2. Goal & scope

- **Goal:** the *answer itself* should lean on website content when the website has
  something relevant to say — not merely reorder the sources list.
- **"Website content" = `source_type == "website"` only** — Drupal nodes, taxonomy
  descriptions, and blocks. *(Terminology: this source_type was historically named
  `article` — one value for every Drupal bundle, confusingly colliding with the
  Drupal bundle also named `article`. It has been renamed to `website` throughout
  the code; `scripts/migrate_source_type_website.py` converges stored data, and
  read paths tolerate the legacy value until then.)*
- **"PDF content" = `source_type in {pdf, pdf_attachment}`.** Note: website-linked
  PDFs we harvest (policy briefs, reports) are `pdf_attachment` and count as **PDF**
  here, by decision — only Drupal-rendered content is "website."
- **Preference is a lean, not exclusion** (decision 1a): the answer leads with and
  emphasizes website content, but PDFs remain available so facts/depth and answer
  correctness are preserved.
- Out of scope: the structured (`drupal_router`) path — it already returns Drupal
  data. Chitchat — no retrieval.

## 3. Locked decisions

| # | Decision |
|---|---|
| 1 | **Lean, not exclusive.** Keep a minimum PDF presence even when website is preferred. |
| 2 | **Relative-gap gate + small absolute floor**, not a single fixed absolute similarity cutoff (raw cosine isn't calibrated across queries). |
| 3 | **Adaptive split** — the number of website vs PDF blocks is decided by the data (how many website chunks are genuinely relevant), not a hardcoded ratio. |

## 4. Proposed architecture

```
query  (skip dual-pull entirely if the user explicitly asked for pdf/article — §8)
 ├─ retrieve WEBSITE candidates   filter source_type = website            (website_candidate_k)
 └─ retrieve PDF candidates       filter source_type in {pdf,pdf_attach}  (retrieval_candidate_k)
                │
                ▼
   rerank the UNION once  ← one rerank pass so scores are comparable (§6);
                            keep the RAW semantic score alongside the blended one
                │
                ├─ w* = top raw semantic score among website candidates
                ├─ p* = top raw semantic score among PDF candidates
                ▼
GATE (is the website worth preferring for THIS query?)
   website_preferred = (w* ≥ p* − margin) AND (w* ≥ floor)
   (empty website pool ⇒ gate fails ⇒ PDF-first)

BOOST (not a separate selection step)
   if website_preferred:
       add +β to the blended score of website candidates that clear the
       per-chunk floor; re-sort the union

build_context — QUOTA-AWARE (see §5.1): parent-expand, dedup, token budget as
   today, but the pdf_min reservation is enforced HERE, on the surviving blocks
present: group + label "TERI website" vs "PDF documents"; website section first when preferred
```

Two Qdrant queries instead of one (negligible latency) — this is the load-bearing
change: it **guarantees the website's best chunk is measurable**, which pure
re-weighting can never do.

> **Why one rerank over the union (not per-pool):** the reranker min-max
> normalizes semantic scores *within the pool it is given*
> (`reranker.py::_normalize`) and returns only the blended score. Reranking the
> two pools separately would map each pool's best chunk to 1.0 regardless of its
> absolute quality — merging those lists is meaningless. One pass over the union
> normalizes across both pools, so boosted merging is valid. The **gate** uses
> raw (pre-normalization) semantic scores, which are comparable across pools
> because both pulls use the same query vector / scoring model; `rerank()` must
> be extended to expose the raw score (today it discards it).

## 5. The adaptive split (answering "can AI decide based on results?")

Yes — the split is **emergent**, not fixed. The only fixed numbers are guardrails.

Mechanism: when the gate says website is preferred, every website chunk that clears
a **per-chunk relevance floor** gets a preference boost `β` added to its selection
score. We then fill the `top_k` slots greedily by boosted score, while **reserving
`pdf_min` slots for PDFs**. So:

| Scenario | What happens | Example split (top_k=6, pdf_min=2) |
|---|---|---|
| Website has lots of strongly-relevant chunks | Website fills everything except the reserved PDF slots | 4 website / 2 PDF |
| Website has a couple of relevant chunks | Those get in; PDFs fill the rest | 2 website / 4 PDF |
| Website relevant but shallow (1 good chunk) | 1 website leads; PDFs support | 1 website / 5 PDF |
| Website not relevant (gate fails) | PDF-first as today; 1 website slot only if decent | 0–1 website / 5–6 PDF |

The "AI deciding" is the relevance distribution deciding: website earns slots only
to the extent it has chunks that are actually relevant. `β` controls *how strongly*
we lean (a knob), but it never overrides the per-chunk floor or the PDF reservation.

> Why a boost rather than a hard "website-first block": a boost degrades gracefully.
> A marginally-relevant website chunk won't leapfrog a clearly-superior PDF unless β
> is set high; a strongly-relevant one will. It's one tunable dial for "how much lean."

### 5.1 Quotas must be enforced in the context builder, not before it

A pre-selection step ("pick 4 website + 2 PDF, hand them over") **does not
survive the existing pipeline**: `build_context` walks the full ranked list and
prunes via parent-expand, **cosine dedup (≥ 0.92)** and the **token budget**
until `top_k` blocks remain (`context_builder.py`). Dedup is especially relevant
here — a policy-brief node's body text and its own attached PDF's text are
near-duplicates, so one of the two is always dropped. Any quota enforced before
this stage is cosmetic.

Therefore the reservation lives **inside the context builder**: it walks the
boosted union as today, but tracks per-group counts and stops admitting website
blocks once taking another would make the `pdf_min_slots` reservation
unsatisfiable from the remaining candidates (and vice versa for the website's
lead slot when the gate passed). Two useful side effects of boosting *before*
context building:

- On a website/PDF near-duplicate pair, the **website block now sorts first**, so
  dedup keeps it and the PDF lands in its `also_available` — i.e. cited as a
  secondary source under the website citation. That is exactly the presentation
  we want, and it happens for free.
- `build_context` always admits the first block regardless of token budget, so in
  website-preferred mode the lead block is guaranteed to be a website chunk.

## 6. Relevance signal & thresholds

- The gate and per-chunk floor use the **raw semantic relevance score** from the
  active reranker (dense cosine by default; the cross-encoder/Cohere score if
  enabled — a better signal, see decision D). **Not** the pool-normalized value —
  with two pools, per-pool normalization isn't comparable. `rerank()` currently
  returns only the blended score, so it must be extended to carry the raw
  semantic score through.
- **Gate:** `website_preferred = (w* ≥ p* − margin) AND (w* ≥ floor)`.
  - `margin` — how far behind the best PDF the best website chunk may be and still
    win. Larger margin = more website preference.
  - `floor` — a low absolute bar so a genuinely off-topic website chunk never
    triggers preference.
- **Per-chunk floor** — a website chunk must clear this to receive the boost / take a
  preferred slot (prevents padding the answer with weak website text).
- **Threshold scales are provider-specific.** Dense cosine lives in ≈[0,1];
  the cross-encoder (`bge-reranker-v2-m3`) outputs logits on a different scale;
  LLM scores are 0–1 but not calibrated across batches. `margin` / `floor` /
  `chunk_floor` values are therefore only meaningful **per reranker provider** —
  they are tuned for the active provider and must be re-tuned if the provider
  changes (store them with the provider name, or namespace the settings).
- **LLM-reranker cap:** `_MAX_LLM_CANDIDATES = 40`. The union
  (`retrieval_candidate_k + website_candidate_k` = 60 by default) exceeds it, and
  the LLM provider then silently falls back to dense scores. If
  `reranker_provider=llm`, either shrink the pulls (e.g. 25 + 15) or accept the
  dense fallback. Not an issue for the default `embedding` provider or the
  cross-encoder.

## 7. Config knobs (all tunable, feature-flagged)

| Setting | Purpose | Proposed default |
|---|---|---|
| `prefer_website_enabled` | Master on/off; off = today's behavior | `true` |
| `website_gate_margin` | Relative gap `w* ≥ p* − margin` | *TBD — tune* |
| `website_gate_floor` | Absolute floor for the gate | *TBD — tune* |
| `website_chunk_floor` | Per-chunk relevance floor for boost/slot | *TBD — tune* |
| `website_boost` (`β`) | Lean strength when preferred | *TBD — tune* |
| `pdf_min_slots` | PDF slots always reserved (correctness) | `2` (of `top_k=6`) |
| `website_candidate_k` | Website-only candidates to pull | `20` |

The threshold defaults are deliberately left **TBD**: raw cosine values aren't
intuitive, so we'll set them empirically in the eval step (§9) rather than guess.

## 8. Guardrails & edge cases

- **Correctness first:** `pdf_min_slots` guarantees PDFs stay in context so answers
  don't degrade to thin website blurbs.
- **Fail open:** any error in the gate/selection → fall back to today's single-pool
  ranking. Never worse than current.
- **Explicit user intent:** if the query processor set `source_type` (user asked
  "in the paper… / on the website…"), **skip the dual-pull entirely** and run a
  single pool honoring the user's filter. This is not just decision C — it is
  required for correctness: `pq.filters` is injected as a *mandatory* Qdrant
  condition into every query, so a PDF pull (`source_type ∈ {pdf,pdf_attachment}`)
  combined with an explicit `source_type=website` filter is contradictory and
  returns zero results (and vice versa).
- **No website content at all** for a query (empty website pool) → `w*` is
  undefined → gate fails → PDF-first. No forced, irrelevant website lead.
- **Cache invalidation on config change:** both pre-retrieval caches — the exact
  response cache (`response_signature`) and the **semantic cache**
  (`semantic_lookup`, which fires on *similar* queries) — currently key only on
  question/tenant/groups/top_k. Neither knows about preference settings, so
  flipping `prefer_website_enabled` (or tuning β / margins) would keep serving
  old-mode cached answers until TTL, and would pollute before/after comparisons
  during tuning. **Include a retrieval-config fingerprint** (hash of the
  preference settings) in both signatures so any config change self-invalidates.
- **`table_boost` interplay:** table-formatted queries add +0.15 to chunks with
  tables (`rerank_table_boost`), which are overwhelmingly PDFs. β and
  `table_boost` act on the same blended score, so for table queries PDFs may
  out-rank boosted website chunks. This is *acceptable* (tables live in PDFs) but
  β must be chosen with this scale in mind.
- **Single integration point:** `answer_query`, `stream_answer`, and the
  `/search` endpoint (`search_blocks`) all route retrieval through
  `rag.retrieve()` — the dual-pull + gate + boost lands once, there, and covers
  all three surfaces.
- **Authority map cleanup:** at minimum, stop `website` being *penalized* (0.65 <
  pdf 1.0). Either neutralize the map or let the new boost supersede it. *(Decision B.)*

## 9. Evaluation plan (before rollout)

Per [testing-strategy], validate on the real TERI query set + Qdrant, comparing
current vs proposed:

1. A query set that *should* be website-answerable (overview / "what does TERI do on
   X" / latest) and one that's clearly PDF-only (specific paper method/data).
2. Metrics: does the website-answerable set now lead with website content **without**
   the PDF-only set regressing? Spot-check answer quality (not just source order).
3. Tune `margin` / `floor` / `chunk_floor` / `β` on this set; lock defaults.
4. Sign-off in plain language before enabling by default.

## 10. Rollout

1. Land behind `prefer_website_enabled` (default off), on its own branch.
2. Tune thresholds on the eval set; then flip default on.
3. Add source-section labels in the UI once context composition is verified.

---

## 11. Code-level review (2026-07-03)

The design was re-checked against the actual pipeline code (`rag.py`,
`hybrid_search.py`, `reranker.py`, `context_builder.py`, `query_processor.py`,
cache flow). Holes found and how the design above was amended:

| # | Hole | Severity | Resolution (now in design) |
|---|---|---|---|
| 1 | Slot quotas enforced before `build_context` are cosmetic — dedup (≥0.92) and token budget prune *after* selection, and website/PDF near-dups (node body vs its own attached PDF) are common | **breaks design** | Quotas enforced *inside* the context builder (§5.1); boost applied before it so website wins near-dup ties and the PDF becomes a secondary citation |
| 2 | Per-pool `rerank()` scores are incomparable — min-max normalization is pool-relative and the raw semantic score is discarded | **breaks design** | One rerank over the union (§4); extend `rerank()` to expose raw semantic scores; gate uses raw scores |
| 3 | Response + semantic caches don't key on preference config → stale-mode answers after flipping the flag; polluted tuning comparisons | **breaks rollout** | Retrieval-config fingerprint added to both cache signatures (§8) |
| 4 | Explicit user `source_type` filter is injected as a mandatory Qdrant condition → dual-pull produces contradictory filters (zero results) | **breaks queries** | Explicit `source_type` ⇒ skip dual-pull, single pool (§8) |
| 5 | `_MAX_LLM_CANDIDATES=40` < union size 60 ⇒ silent dense fallback with `reranker_provider=llm` | provider-dependent | Documented in §6; shrink pulls or accept fallback |
| 6 | Threshold scales differ per reranker provider (cosine vs cross-encoder logits vs LLM 0–1) | provider-dependent | Thresholds tuned & stored per provider (§6) |
| 7 | `table_boost` (+0.15, PDF-heavy) competes with β on the same scale | minor | Documented (§8); acceptable, β chosen accordingly |
| 8 | Empty website pool leaves `w*` undefined | minor | Gate defaults to PDF-first (§4, §8) |

Confirmed sound: `retrieve()` is the single integration point for
`answer_query` / `stream_answer` / `search_blocks`; parent expansion preserves
`source_type` (parents belong to the same document); the structured Drupal path
bypasses this design entirely (already website data); `build_context` always
admits the first block, guaranteeing the website lead when the gate passes.

---

## Open decisions

Please confirm so we can lock the design and start:

- **A. Adaptive split guardrails** — OK with `top_k = 6`, `pdf_min_slots = 2`
  (so website can take up to 4)? Or a different `top_k` / reserve?
- **B. Authority map** — when we add the boost, should we also **fix the existing
  authority table** (article currently 0.65 vs pdf 1.0) so it stops fighting us —
  neutralize it, or leave it and rely purely on the new boost?
- **C. Honor explicit intent** — if the user clearly asks about "the paper/report,"
  should we suppress website preference for that query? (Recommended: yes.)
- **D. Reranker provider** — the gate is only as good as the relevance signal.
  Default is dense-cosine (`embedding`). Enable `cross_encoder`
  (`BAAI/bge-reranker-v2-m3`) for a sharper signal, or keep dense for now and revisit?
- **E. Threshold defaults** — agree to set `margin` / `floor` / `chunk_floor` / `β`
  empirically in the eval step rather than pick numbers now?
