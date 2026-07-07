# Testing guide: website-content preference

How to validate the website-preference dual-retrieval feature before enabling it by
default. Design: [website-preference-retrieval.md](website-preference-retrieval.md).
Behavior reference: [retrieval.md](retrieval.md#6-website-content-preference-dual-retrieval).

The feature is behind `prefer_website_enabled` (**default off**), so nothing changes
in production until you flip it. This guide covers turning it on in a test
environment, what to verify, how to tune, and how to roll back.

---

## 1. Prerequisites

1. **Fresh Qdrant rebuild + full re-ingest** from current code. This guarantees the
   collection contains only `{pdf, pdf_attachment, website}` source types (no legacy
   `article`). The dual pull defines "PDF" as *not* `website`, so a clean type set
   avoids any ambiguity.
2. **Add a `source_type` payload index** in Qdrant for fast filtered pulls (the
   website pull filters `source_type == website`, the PDF pull filters `!= website`).
   Without it Qdrant still filters, just less optimally.
3. Working Azure OpenAI (chat + embeddings) and, ideally, Redis (to exercise the
   cache-invalidation path). Redis is optional — caches are inert when unset.

## 2. Enable / disable

Set in `.env` (env var = upper-cased field name):

```
PREFER_WEBSITE_ENABLED=true      # turn the feature on (default false)
WEBSITE_CANDIDATE_K=20           # website-only pull size
WEBSITE_MAX_SLOTS=2              # max website blocks (the concise lead)
WEBSITE_CHUNK_FLOOR=0.30         # relevance floor for a website slot (TUNE — see §6)
CONTEXT_TOKEN_BUDGET=9000        # raised from 6000 so ~5 blocks fit (2 web + ~3 pdf)
```

**Rollback** = `PREFER_WEBSITE_ENABLED=false` (instant; reverts to single-pull
behavior). No re-ingest needed to toggle.

> Toggling the flag or changing any of these knobs changes the cache fingerprint, so
> old-mode cached answers are automatically bypassed — before/after comparisons stay
> clean.

## 3. Fastest way to inspect behavior: `POST /search`

`/search` runs the full retrieval path (dual pull → rerank → segregated context)
**without** generation — so it's the cheapest, clearest way to see what's selected
and in what order. Each returned block includes `source_type`, `title`, `score`, and
`n` (the numbering). Verify segregation here first, then spot-check real answers via
`/chat`.

For each test query, check the returned `blocks[]`:
- website blocks come **first** (lowest `n`), then PDF blocks;
- at most `website_max_slots` (2) website blocks;
- total ≈ 5 blocks (budget-bound), majority PDF.

## 4. Test query sets

Build two labelled sets against the real corpus (per
[testing-strategy]):

**A. Website-answerable** — overview / "what does TERI do on X" / programme / latest:
- "What does TERI do on water conservation?"
- "Tell me about TERI's renewable energy programmes."
- "What are TERI's thematic focus areas?"

**B. PDF-only / deep** — specific paper method, data, or figure:
- "What method did the microalgae biofuel study use?"
- "What were the measured groundwater levels in the watershed assessment?"

**C. Control / edge** (see §5): explicit-intent, table, and off-topic-website queries.

## 5. What to verify

| # | Check | Expected |
|---|---|---|
| 1 | **Website leads** (set A) | Website block is `[1]`; website citations listed before PDF; answer opens with website-grounded overview |
| 2 | **Website capped** | ≤ 2 website blocks even when many website chunks are relevant |
| 3 | **PDF depth preserved** | Majority of blocks are PDF; set B answers are as detailed as before |
| 4 | **PDF-only set doesn't regress** (set B) | Same/again-correct answers; website not forced in when irrelevant |
| 5 | **Floor works** | A weak/off-topic website chunk does **not** take a slot (0 website blocks when nothing clears the floor → pure-PDF, as today) |
| 6 | **Explicit intent bypass** | "What does the *report* say about X" → single pull, no forced website lead; "on the *website*…" → website-only results |
| 7 | **Table bypass** | "Give me a table of …" → the table-bearing PDF is not buried under website content (segregation off for `table`) |
| 8 | **No false conflict** | A website page + its own attached PDF both present → response `conflict` is **false** |
| 9 | **Completeness** | No content silently missing vs the old single pull (the "not website" pull catches everything non-website) |
| 10 | **Cache invalidation** | Ask a question with the flag off, then on → the second call is **not** served the stale off-mode answer |
| 11 | **Filters preserved** | A query with a language or date restriction still applies it under the dual pull (both pulls carry `pq.filters`) |
| 12 | **Group labels** | In the context sent to the LLM (visible in traces/logs), website-led contexts show `— TERI website —` / `— PDF documents —` headers; single-pull contexts show none |

## 6. Tuning `website_chunk_floor`

The floor is the one value that needs empirical tuning; it's a **raw dense-cosine**
score, provider-specific.

- **Too low** → weak/tangential website chunks lead answers (padding). Symptom: set B
  (PDF-only) queries start showing an irrelevant website block at `[1]`.
- **Too high** → website rarely leads even when relevant. Symptom: set A queries stay
  PDF-first.
- **Method:** run set A + set B through `/search` at a few floor values (e.g. 0.20,
  0.30, 0.40), and pick the lowest value at which set A leads with website **without**
  set B gaining an irrelevant website lead. Lock it, then sign off in plain language.
- If you later switch `reranker_provider` (e.g. to the cross-encoder), the floor scale
  changes and must be **re-tuned**.

## 7. Latency & cost (budget 6000 → 9000)

Only content-rich queries send more tokens; sparse queries are unaffected.

- Capture `/chat` time-to-first-token with the flag off vs on for set A/B. Expect a
  small prefill increase (~0.1–0.5 s on a modern model), no change to generation.
- Confirm total response time is still dominated by generation, not retrieval.

## 8. Regression checks (must still pass)

- `python -m pytest tests/ -q` — the full unit suite (85 tests at time of writing).
- **Structured path** (counts/lists, e.g. "how many reports in 2024") — unchanged;
  bypasses `retrieve()` entirely.
- **Chitchat** ("hi", "what can you do") — no retrieval, unchanged.
- **Explicit `source_type`** and **language/date** filters — still honored.
- **Streaming `/chat`** vs non-streaming `answer_query()` — both produce the
  segregated, website-first result when the flag is on.

## 9. Known limitations / notes

- **LLM reranker cap:** with `reranker_provider = llm`, the merged union (~60) exceeds
  the 40-candidate cap and silently falls back to dense scores. Shrink the pulls
  (e.g. `WEBSITE_CANDIDATE_K=15`, `RETRIEVAL_CANDIDATE_K=25`) if using `llm`. Not an
  issue for the default `embedding` provider or the cross-encoder.
- **Two pulls run sequentially** today (one extra Qdrant round trip, tens of ms).
  Parallelizing is a possible follow-up; acceptable as-is.
- **Two labeled reference sections** in the UI ("TERI website" / "PDF documents") are
  a **frontend** task — the backend already emits an ordered, `type`-tagged citation
  list.

## 10. Sign-off checklist before flipping the default on

- [ ] Set A leads with website content and cites it first.
- [ ] Set B (PDF-only) shows no regression and no forced website lead.
- [ ] Explicit-intent and table queries behave per §5 (#6, #7).
- [ ] No false `conflict` flags on website+own-PDF pairs.
- [ ] `website_chunk_floor` tuned and locked.
- [ ] Latency delta measured and acceptable.
- [ ] Plain-language sign-off recorded.
