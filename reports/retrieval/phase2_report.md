# Phase 2 — Retrieval baseline and lexical evaluation

**Status: results are DRAFT.** Relevance judgments were assigned by an LLM over
pooled results, not by a human who knows this corpus. The direction of the
findings is probably right; the exact numbers are not gold. Review
`judgments_v1.draft.json` before treating any of this as a decision.

Scope: dense-only vs dense + the **existing** MatchText keyword leg. True
BM25/sparse retrieval was deliberately not implemented — that decision is what
this evaluation is for.

---

## 1. What the "keyword leg" actually is

Not BM25, and not lexical *ranking* at all.

`strategies.keyword_search` builds a `FieldCondition(key="chunk_text",
match=MatchText(text=terms))` and passes it as an **extra filter to the dense
search**. So it is a dense pull restricted to chunks containing the salient
terms, RRF-fused with the unrestricted dense pull. There is no term-frequency
scoring, no IDF, and no lexical rank anywhere in the system.

Terms come from `extract_key_terms`, four regexes: quoted phrases, capitalised
bigrams, ALL-CAPS acronyms, four-digit years.

**It had never worked.** The leg requires a `chunk_text` full-text index that did
not exist; `keyword_search` caught the resulting error and returned `[]`. With
`keyword_leg_enabled=True` the leg would have contributed nothing, silently. The
index now exists (`scripts.create_fulltext_index`, 148,214 points, word
tokenizer, lowercase).

---

## 2. Method

- **38 queries** across 9 categories, authored against the live corpus — real
  titles, themes, authors, acronyms and years sampled from MySQL and Qdrant, not
  invented. `queries_v1.json`.
- **Pooled judging**, as in TREC: every configuration's top 10 merged per query,
  each pooled chunk graded once on 0/1/2. Pooling both legs is essential —
  judging only what dense returned would define the keyword leg's unique finds
  as irrelevant by construction.
- **Candidate retrieval only.** No reranking, no website preference, no context
  building, so a difference in the numbers is a difference in what was *fetched*.
- Metrics at k=10. Recall and MRR count grade 2 only; nDCG uses the full scale.

---

## 3. Results

```
config              R@10     MRR    nDCG      ms    p95ms
dense              0.779   0.660   0.751    50.7     49.6
keyword            0.491   0.406   0.470    17.8     39.0
dense+keyword      0.863   0.688   0.789    45.9     70.3
```

**Dense + keyword wins overall: +0.084 Recall@10, +0.038 nDCG, +0.028 MRR.**
Per-query: **13 wins, 6 losses, 19 ties.**

Latency: the mean is not meaningfully different (the fused config runs both legs
but dense pays a cold-start cost first in each loop); **p95 rises 49.6 → 70.3 ms**,
which is the honest cost. Still far inside any sane budget.

### By category (nDCG@10)

| category | dense | keyword | dense+keyword | verdict |
|---|---|---|---|---|
| semantic | 0.946 | 0.000 | 0.946 | leg never fires — no harm |
| exact_term | 0.929 | **0.077** | 0.929 | **leg fails at its own job** |
| temporal | 0.612 | 0.730 | **0.759** | biggest gain, +0.147 |
| identifier | 0.725 | 0.577 | **0.810** | +0.085 |
| entity_name | 0.630 | 0.524 | **0.698** | +0.068 |
| acronym | 0.784 | **0.894** | 0.847 | fusion *dilutes* a strong leg |
| mixed | 0.615 | 0.599 | 0.624 | +0.009 |
| relational | 0.620 | 0.475 | 0.625 | +0.005 — needs the graph |
| project | 0.840 | 0.363 | 0.811 | −0.029, slight harm |

---

## 4. The finding that matters

**The bottleneck is term extraction, not retrieval.** The leg helps exactly
where dense is weakest (temporal, identifier, entity names) and is *inert*
where it should help most.

`extract_key_terms` returns `None` — skipping the leg entirely — for:

| query | why |
|---|---|
| "Life cycle analysis of transport modes" | no capitals, no acronym, no year |
| "continuous ambient air quality monitoring station" | same |
| "PM2.5 annual average concentration" | `PM2.5` matches no pattern |

That is the whole `exact_term` category, which scored **0.077** for the keyword
leg. The mechanism is fine; it is never invoked on lowercase exact phrases.

A second, sharper limitation: **`MatchText` with several terms is AND
semantics.** "Emission Inventorisation for Faridabad Town" extracts four terms
and returns **zero** chunks, because no single chunk contains all four. One rare
term kills the entire leg.

Both are cheap to fix and neither requires BM25.

---

## 5. Recommendation

1. **Enable `keyword_leg_enabled`.** Net win on this benchmark, no category
   materially harmed, p95 cost ~20 ms. Confirm once judgments are reviewed.
2. **Fix `extract_key_terms` before considering BM25.** Lowercase noun phrases,
   alphanumerics like `PM2.5`, and OR-ing terms rather than AND-ing them are
   higher-leverage than a new retrieval mechanism, and far cheaper.
3. **Re-run this benchmark after that fix.** If the `exact_term` and `project`
   categories remain weak with terms extracted properly, *that* is the evidence
   for true BM25 — a real scorer would then be buying ranking quality the filter
   cannot express. On today's evidence BM25 is not yet justified.
4. `relational` (0.625) barely moves for either configuration, as expected. It
   is the graph layer's category; recorded here as its baseline.

---

## 6. Reproducing

```bash
python -m scripts.create_fulltext_index      # once; the leg needs this index
python -m scripts.judge_retrieval --dry-run  # pool sizes, no spend
python -m scripts.judge_retrieval            # draft grades (costs LLM calls)
python -m scripts.eval_retrieval             # the table above
python -m scripts.eval_retrieval --category acronym --k 5
```

Reviewing a query's grades and setting its `reviewed: true` makes
`judge_retrieval` leave it alone on the next run, so the draft can be corrected
incrementally without losing work.

## 7. Files

| File | Role |
|---|---|
| `queries_v1.json` | 38 queries, 9 categories. Hand-editable. |
| `judgments_v1.draft.json` | Pooled grades. **Draft.** |
| `results_v1.draft.json` | Full per-query output of the run above. |
| `scripts/eval_retrieval.py` | Configurations, metrics, reporting. |
| `scripts/judge_retrieval.py` | Pooled LLM-assisted judging. |
| `tests/test_eval_retrieval_metrics.py` | Metric arithmetic. |
