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

`strategies.keyword_search` applies a `chunk_text` MatchText condition as an
**extra filter on the dense search**. So it is a dense pull restricted to chunks
containing the salient terms. There is no term-frequency scoring, no IDF, and no
lexical rank anywhere in the system. This matters for reading the tables below:
the `keyword` column is *dense ranking inside a lexical filter*, not a lexical
scorer.

**It had never worked.** The leg requires a `chunk_text` full-text index that did
not exist; `keyword_search` caught the resulting error and returned `[]`. With
`keyword_leg_enabled=True` it would have contributed nothing, silently. The
index now exists (`scripts.create_fulltext_index`, 148,214 points).

---

## 2. Method

- **38 queries**, 9 categories, authored against the live corpus — real titles,
  themes, authors, acronyms and years sampled from MySQL and Qdrant.
- **Pooled judging**, as in TREC: every configuration's top 10 merged per query,
  each pooled chunk graded 0/1/2 once. Pooling all legs is essential — judging
  only what dense returned would define the keyword leg's unique finds as
  irrelevant by construction.
- **Candidate retrieval only.** No reranking, no website preference, no context
  building.
- Metrics at k=10. Recall and MRR count grade 2 only; nDCG uses the full scale.

---

## 3. Run 1 — as the leg was originally written

```
config              R@10     MRR    nDCG      ms    p95ms
dense              0.779   0.660   0.751    50.7     49.6
keyword            0.491   0.406   0.470    17.8     39.0
dense+keyword      0.863   0.688   0.789    45.9     70.3
```

13 wins / 6 losses / 19 ties. The leg helped where dense was weakest (temporal
+0.147, identifier +0.085, entity_name +0.068) — but scored **0.077 on the
`exact_term` category**, the one thing it exists for.

### Why: the bottleneck was term selection, not retrieval

`extract_key_terms` matched only quoted phrases, Capitalised Bigrams, ALL-CAPS
acronyms and 4-digit years. It returned `None` — skipping the leg entirely — for
**40% of the query set**, including every lowercase exact phrase:

| query | result |
|---|---|
| "Life cycle analysis of transport modes" | no terms → leg skipped |
| "continuous ambient air quality monitoring station" | no terms → leg skipped |
| "PM2.5 annual average concentration" | `PM2.5` matched no pattern |

And a second defect: **`MatchText` over several words is an AND**. "Emission
Inventorisation for Faridabad Town" extracted four terms and returned **zero**
chunks, because no single chunk contained all four. One rare term killed the leg.

---

## 4. The fix

1. **Alphanumeric codes** (`PM2.5`, `CO2`) now match.
2. **Acronyms keep their qualifying number** — `SDG 7`, not `SDG`, which matches
   every goal.
3. **Lowercase content-word fallback**, reached *only* when no precise term was
   found, so ordinary vocabulary never dilutes a query that named something
   exactly.
4. **Terms are OR-ed**, one `MatchText` each, instead of AND-ed into one.
   Degrades toward the dense pull rather than collapsing to zero.
5. **Subsumed terms dropped** — keeping bare `GHG` beside `"GHG emissions"` would
   match every chunk mentioning GHG at all, making the quoted phrase useless.

Queries yielding no terms went from **15/38 to 0/38**.

---

## 5. Run 2 — after the fix

```
config              R@10     MRR    nDCG      ms    p95ms
dense              0.778   0.660   0.746    58.4     47.6
keyword            0.863   0.656   0.801    28.8     43.5     <-- best recall & nDCG
dense+keyword      0.852   0.682   0.786    59.8     80.3
```

16 wins / 5 losses / 17 ties for dense+keyword over dense.

### By category (nDCG@10)

| category | dense | keyword | dense+keyword |
|---|---|---|---|
| semantic | 0.949 | 0.949 | 0.949 |
| acronym | 0.787 | **0.896** | 0.851 |
| exact_term | 0.795 | **0.878** | 0.834 |
| temporal | 0.650 | 0.768 | **0.788** |
| identifier | 0.715 | 0.749 | **0.785** |
| entity_name | 0.694 | **0.753** | 0.736 |
| project | 0.690 | **0.733** | 0.691 |
| relational | 0.634 | **0.697** | 0.638 |
| mixed | 0.737 | 0.726 | 0.743 |

**`exact_term` went 0.077 → 0.878.** The mechanism was always fine; it was never
being invoked.

---

## 6. The finding

**A lexical filter with dense ranking beat both pure dense and the RRF fusion**,
while running roughly half the latency (28.8 ms vs 58.4 ms — the filter shrinks
the search space).

The fusion is now the *middle* option, not the best. Re-admitting the unfiltered
dense list dilutes a ranking the filter had already improved. Note also that
`keyword` never loses to `dense` on semantic queries (0.949 both): with the
content-word fallback the OR filter is permissive enough there to be nearly a
no-op, so the filter costs nothing where it cannot help.

**This is a draft-judgment result on 38 queries and should not be acted on as-is.**
The reading that survives scrutiny most easily is the narrower one: *the keyword
leg is now clearly worth enabling*. The stronger claim — that filtered-dense
should replace fusion — needs reviewed judgments and more queries.

---

## 7. Recommendation

1. **Enable `keyword_leg_enabled`** once judgments are reviewed. Net win either
   way you read the table, ~20 ms p95.
2. **Test a filter-only mode** as a third production configuration. It is the
   best config here on recall, nDCG *and* latency, which is not what the fusion
   design assumes.
3. **Still no case for BM25.** The gap Run 1 blamed on the mechanism closed with
   ~40 lines of term extraction. A real scorer would buy ranking quality *within*
   the matched set — worth revisiting only once judgments are reviewed and only
   if `project`/`relational` stay weak.
4. `relational` remains the weakest category (0.634–0.697) for every
   configuration, as expected. It is the graph layer's, and this is its baseline.

---

## 8. Reproducing

```bash
python -m scripts.create_fulltext_index      # once; the leg needs this index
python -m scripts.judge_retrieval --dry-run  # pool sizes, no spend
python -m scripts.judge_retrieval            # draft grades (costs LLM calls)
python -m scripts.eval_retrieval             # the tables above
python -m scripts.eval_retrieval --category exact_term --k 5
```

Reviewing a query's grades and setting its `reviewed: true` makes
`judge_retrieval` leave it alone on the next run, so the draft can be corrected
incrementally without losing work.

## 9. Files

| File | Role |
|---|---|
| `queries_v1.json` | 38 queries, 9 categories. Hand-editable. |
| `judgments_v1.draft.json` | Pooled grades, post-fix pools. **Draft.** |
| `judgments_v1.draft.pre-termfix.json` | Run 1 grades, kept for comparison. |
| `results_v1.draft.json` / `results_v2.draft.json` | Full per-query output. |
| `scripts/eval_retrieval.py` | Configurations, metrics, reporting. |
| `scripts/judge_retrieval.py` | Pooled LLM-assisted judging. |
| `tests/test_eval_retrieval_metrics.py` | Metric arithmetic. |
