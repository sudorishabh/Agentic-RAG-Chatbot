# Phase 3 — Does a real reranker earn its place?

**Status: results are DRAFT.** Relevance judgments were assigned by an LLM over
pooled results, not by a human who knows this corpus. The direction of the
findings is probably right; the exact numbers are not gold. Review
`judgments_v1.draft.json` before treating any of this as a decision. 38 queries
is a small set — read "+28% MRR" as a strong directional signal, not an effect
size.

**The numbers below are the post-migration re-measurement.** An earlier pass was
taken while `effective_start_date` was populated on 0 of 152,833 points, so the
recency tier returned a constant and did nothing. The date backfill has since
completed and been verified point-by-point against MySQL (152,833 exact matches,
0 mismatches, 0 orphans), and every figure here was re-measured with all four
ranking tiers live. §8 records what changed and why the first pass was held.

Scope: the `cross_encoder` reranker provider against the `embedding` default
that production has always run. Phase 2 measured *what gets fetched*; this
measures *how it is ordered*.

---

## 1. The stage was not doing the reranking

`reranker_provider` defaults to `"embedding"`, and `_semantic_scores` resolves
that to `_dense_scores`, which returns `semantic_score or score` — the cosine
Qdrant already produced. So the second-stage scorer was the first stage's own
output.

The banding around it (relevance → authority → completeness → recency) was real
work, but it re-*orders* on metadata rather than re-*judging* relevance. Three
cross-encoder providers were wired and dormant: `sentence-transformers` was
commented out in `requirements.txt`, and the setting pointed elsewhere.

---

## 2. The benchmark had to be rebuilt first

`reports/` did not exist in the working tree. `queries_v1.json` and
`judgments_v1.draft.json` were recovered from `f6cc0bd`, and **0 of 20 sampled
judged chunk ids still existed in Qdrant**: the corpus was re-ingested after the
judgments were drafted, and chunk ids are content-derived, so all 488 changed.
The first evaluation run returned 0.000 on every metric for every configuration.

`scripts.judge_retrieval` was re-run against the live corpus — 504 pooled
chunks, 172 graded relevant, 1 query with nothing relevant. The stale file is
kept at `judgments_v1.stale-aug2026.json`.

**Lesson for the next phase:** the gold set is pinned to chunk ids and so is
invalidated by any re-chunking. Judgments should be re-drafted whenever the
corpus is rebuilt, and the eval should fail loudly on a total id miss rather
than reporting a confident 0.000.

---

## 3. Method

- The rerank configurations **reorder the `dense+keyword` pool** rather than
  pulling their own candidates. Judgments are pooled at depth 10, so a deeper
  pull would surface ungraded chunks that score 0 by construction — the same
  bias `judge_retrieval` documents for the keyword leg. Reranking in-pool means
  the candidate set is identical across configurations and only the *order*
  differs, so Recall@10 is fixed by construction and every move in nDCG/MRR is
  ordering quality.
- The pool is memoised per query, so all rerank configurations score an
  identical set and the timing delta is the reranker's own cost.
- `POOL_CONFIGS` restricts judging to the retrieval legs: a rerank config
  contributes no chunk they did not already surface.
- Metrics at k=10. Recall and MRR count grade 2 only; nDCG uses the full scale.

---

## 4. A scale defect had to be fixed before the provider was usable

A cross-encoder emits an unbounded logit, not a cosine. Measured on this
corpus: **+4.17** for a passage that answers the query, **-11.17** for one that
does not.

`rerank` writes the provider score to `semantic_score`, which four consumers
read expecting 0..1:

| Consumer | Threshold | What a raw logit does |
| --- | --- | --- |
| `rerank_relevance_tolerance` | 0.03 | Below the gap between any two logits — every candidate takes its own band, so the recency/authority/completeness keys become unreachable and the banding silently stops existing |
| `context.builder` `website_chunk_floor` | 0.30 | A moderately relevant passage at -2 falls under a floor meant to reject the weakly related |
| `context.builder` `pdf_high_confidence_floor` | 0.5 | Same |
| `retriever` `corrective_min_score` | 0.2 | A negative top score pins the corrective loop permanently open |

This is the defect `fusion.rrf` documents for its own scale, in the other
direction. `_cross_encoder_semantic` now squashes through a sigmoid — the
model's own calibration, since these are trained with BCE on that logit, and
the normalisation BAAI publish for bge-reranker. Every threshold keeps meaning
what it says and none needed retuning. Pinned by
`tests/retrieval/search/test_fusion_score_integrity.py`.

Observed on one query, top-10 pool: cosine spanned **0.522–0.608** (0.086
wide), the normalised cross-encoder **0.254–0.994** (0.74 wide). The dense score
barely separates candidates it has already agreed are plausible, which is the
mechanism behind the numbers below.

---

## 5. Results — 38 queries, k=10, `cross-encoder/ms-marco-MiniLM-L-6-v2`

All four ranking tiers live. Every rerank setting is pinned per configuration
rather than inherited from `.env` — see `_RERANK_DEFAULTS`.

| config | R@10 | MRR | nDCG | ms | p95ms | wins/losses/ties |
| --- | --- | --- | --- | --- | --- | --- |
| `dense` | 0.765 | 0.663 | 0.728 | 347 | 459 | — |
| `dense+keyword` | 0.845 | 0.678 | 0.763 | 308 | 448 | 21/16/1 |
| `rr_embedding` (production) | 0.845 | 0.669 | 0.761 | 317 | 452 | baseline |
| `rr_minilm` (512 tokens) | 0.845 | 0.805 | 0.822 | 1370 | 1361 | 27/10/1 |
| `rr_minilm_s256` | 0.845 | 0.817 | 0.822 | 574 | 716 | 29/8/1 |
| **`rr_minilm_s128`** | 0.845 | **0.855** | **0.825** | **323** | 434 | 28/9/1 |
| `rr_minilm_s64` | 0.845 | 0.863 | 0.828 | 181 | 233 | 27/10/1 |
| `rr_minilm_t20` (band 0.20) | 0.845 | 0.785 | 0.807 | 1584 | 2737 | 22/11/5 |

Against `rr_embedding` at 128 tokens: **MRR +0.186, nDCG +0.064, 28 wins / 9
losses / 1 tie.** Read that margin as the top of a range, not a point estimate —
the least-confounded configuration gives +0.136, for the reason set out below.
Recall is identical by construction: in-pool reranking reorders, it cannot add.

**`rr_embedding` is still slightly worse than not reranking at all** — MRR 0.669
vs 0.678, nDCG 0.761 vs 0.763, and `dense+keyword` beats it head-to-head 21-16.
Banding on top of an unchanged relevance signal costs a little ranking quality.
The recency tier coming alive helped it (0.650 -> 0.669 MRR, 0.757 -> 0.761
nDCG, exactly the direction predicted in §8) but did not close the gap. The
stage is not idle; it is marginally negative.

### By category (nDCG@10)

| category | `rr_embedding` | `rr_minilm_s128` | Δ |
| --- | --- | --- | --- |
| relational | 0.644 | **0.849** | +0.205 |
| acronym | 0.823 | **0.921** | +0.098 |
| entity_name | 0.734 | **0.810** | +0.076 |
| temporal | 0.639 | **0.701** | +0.062 |
| project | 0.701 | 0.749 | +0.048 |
| mixed | 0.738 | 0.787 | +0.049 |
| identifier | 0.829 | 0.842 | +0.013 |
| exact_term | 0.818 | 0.832 | +0.014 |
| semantic | 0.880 | 0.896 | +0.016 |

At 128 tokens every category improves, including `semantic` and `identifier`,
which both lost slightly in the pre-migration pass. `relational` remains the
largest single gain in every configuration measured.

The gain is concentrated exactly where a bi-encoder is weak. Pure semantic
questions — what embeddings are already good at — are a wash or slightly worse.
The transformed queries are relationship-shaped: "Who leads TERI's energy
programme" (+0.428 at 512), "Which organizations fund TERI's water projects"
(+0.508). Those need word-level interaction between query and passage, which is
the one thing a bi-encoder cannot do.

### What is actually established

| claim | status |
| --- | --- |
| The cross-encoder beats the embedding reranker | **robust**, but the margin is a range: +0.136 MRR at its least-confounded configuration, +0.194 at its most |
| Truncating to 64-128 tokens costs 4.6-7.6x less than 512 with no measurable quality loss | **robust** |
| Any one sequence length *ranks* better than another | **not measurable on this benchmark** (see below) |

---

### Sequence length: a cost result, and a measurement artifact

Measured in one pass on a quiet box with the migration closed, so all four
points are comparable. Every baseline reproduced its previous value exactly
(`dense` 0.663/0.728, `dense+keyword` 0.678/0.763, `rr_embedding` 0.669/0.761),
which is the evidence that these figures are stable and that only the latencies
moved with box conditions.

| max_seq_length | ~chars seen | MRR | nDCG | ms | wins/losses/ties |
| --- | --- | --- | --- | --- | --- |
| 512 (model default) | ~2048 | 0.805 | 0.822 | 1370 | 27/10/1 |
| 256 | ~1024 | 0.817 | 0.822 | 574 | **29/8/1** |
| 128 | ~512 | 0.855 | 0.825 | 323 | 28/9/1 |
| 64 | ~256 | **0.863** | **0.828** | **181** | 27/10/1 |

MRR rises at every step and the curve does not turn. **That is the outcome most
likely to mislead, and it should not be read as confirmation of anything.** Two
observations kill the quality interpretation:

**1. The win counts are flat.** 27, 29, 28, 27 across an 8x range of sequence
length. If shorter sequences ranked genuinely better, more queries would
improve. They do not — the aggregate MRR rise comes from a few queries moving a
long way, which is exactly what MRR is most sensitive to and least robust
about. nDCG moves 0.822 -> 0.828 across the whole range, 0.003 per step, inside
the noise of 38 queries.

**2. The gold set was built with a 700-character window.**
`scripts.judge_retrieval` sends `text[:SNIPPET]` with `SNIPPET = 700`
(line 83). The population that matters is not the corpus but the graded set, and
that is small enough to measure exhaustively rather than sample — a census of
all 491 distinct chunks in `judgments_v1.draft.json`:

| | median | mean | p25 | p75 | longer than 700 |
| --- | --- | --- | --- | --- | --- |
| gold set (n=491, census) | **1637** | 1581 | 1118 | 2088 | **88.8%** |
| corpus (n=125,206, full scroll) | 1426 | — | — | — | 82.0% |

**The grader saw 42.8% of a median graded chunk, and 88.8% of graded chunks were
longer than its window.** Nine in ten relevance labels in this gold set were
assigned without reading the whole passage.

Being a census, that needs no sampling assumption — which matters, because the
earlier evidence for it did. A 1587-char median measured from 360 *retrieved*
chunks across three queries looked significant against a bootstrap
(p = 0.002 for a median that high by chance) but those 360 draws were ~120 per
query and so heavily correlated by topic and document; effective n was nearer
three than 360, and the p-value was worthless. The census replaces the inference
with a count. The superseded 1587 is recorded here deliberately: it is what a
retrieval-biased sample gives, and someone recomputing it that way should find
out why it disagrees rather than trusting it.

The effect is not about relevance. Gold-set length is flat across grades —
median 1608 for grade 2, 1648 for grade 1, 1655 for grade 0 — so it is retrieval
that surfaces longer chunks, not the grader that favours them. Which means the
confound applies uniformly to the judged pool rather than to one end of it.

That makes sequence length partly a measure of *agreement with the judge's field
of view* rather than of ranking quality:

- at 64-128 tokens the reranker reads ~256-512 chars, well inside what the
  grader saw
- at 512 tokens it reads ~2048 chars, including ~1300 characters the grader
  never read and could not have graded

A reranker that reads text the grader never saw earns no credit for it, and is
penalised if that text moves its score. The win-count peak at 256 (~1024 chars,
bracketing the 700-char window) is consistent with the same effect.

**So this benchmark cannot separate ranking quality across sequence lengths.**
The confound is structural, not statistical — a larger query set would not fix
it. Fixing it means re-judging on full chunk text, which changes every grade in
the gold set.

### The same confound reaches the cross-encoder comparison

`_semantic_scores` routes the `embedding` provider to `_dense_scores`, which
returns the vector-search cosine — computed from an embedding built over the
**whole** chunk (nothing in the embed path truncates). So `rr_embedding` is
scored on 100% of every chunk, while the cross-encoder at 128 tokens reads ~512
chars, comfortably inside the 700 the grader saw. Same artifact, same direction,
now applied to the headline comparison: some of the cross-encoder's margin is
field-of-view agreement rather than reranking quality.

The curve bounds it. If the confound were driving the result, the advantage
should shrink as the cross-encoder's window grows past 700 chars. It does — and
it does not vanish:

| cross-encoder window | MRR | vs `rr_embedding` | vs `dense+keyword` |
| --- | --- | --- | --- |
| 64 tokens (~256 chars, deepest inside the grader's window) | 0.863 | +0.194 | +0.185 |
| 512 tokens (~2048 chars, ~1350 beyond it) | 0.805 | **+0.136** | **+0.127** |

At 512 the cross-encoder is maximally *disadvantaged* — judged partly on ~1350
characters the grader never read, earning nothing for them — and still beats
both baselines decisively. **+0.136 is the confound-resistant floor.** The
spread between the two rows, roughly 0.06 MRR, is about the size of the
artifact, which is more useful to have written down than either endpoint alone.

So the honest headline is not a single number: the cross-encoder is worth
**+0.136 MRR at the least-confounded configuration, rising to +0.194 as its
window narrows toward the grader's.**

What survives cleanly is the cost result, independent of the confound and large:
**64 tokens is 7.6x cheaper than 512 (181ms vs 1370ms) with no measurable
quality loss.** Choose sequence length on latency and on how much of a chunk you
want the model to actually judge — not on the MRR column above.

### Widening the band costs

`rerank_relevance_tolerance` at 0.20 costs 0.070 MRR and 0.015 nDCG against the
0.03 default, and drops from 28 wins to 22. Widening the band lets recency,
authority and completeness decide more often, and with a real relevance signal
underneath that is a bad trade — the reranker's ordering is more informative than
the metadata tie-breaks it would be overridden by. The cost is larger now than
the 0.038 measured while recency was inert, which is consistent: a wider band is
exactly what lets the newly-live recency tier fire. After the sigmoid fix the
0.03 default needs no per-provider adjustment.

---

## 6. Latency is the real constraint

`retriever` reranks the **whole** fused candidate set, and with three legs at
`retrieval_candidate_k` (40) that is routinely 100+ candidates. Cost is linear —
one model pass each — where every other provider is flat. Measured on CPU:

| candidates | 512 tok | 256 tok | 128 tok |
| --- | --- | --- | --- |
| 10 | 622ms | 346ms | 184ms |
| 40 | 2097ms | 1308ms | 661ms |
| 120 | 6623ms | 3822ms | 2004ms |

Uncapped production would have paid **6.6s per query**. `rerank_max_candidates`
(40) now bounds it, mirroring `_MAX_LLM_CANDIDATES` for the `llm` provider —
except that provider declines entirely past its limit, which here would mean
never reranking at all. Candidates past the cap keep their fused order behind
every scored one and are deliberately **not** ranked against them: their score
is still a cosine while the head's is a normalised cross-encoder relevance. With
`retrieval_top_k` at 6, a candidate the first stage ranked below 40th has never
reached an answer.

At the cap, expect **~1.3s** (256 tokens) or **~0.66s** (128) added to a query.

---

## 7. `BAAI/bge-reranker-v2-m3` could not be measured here

The `reranker.py` default is XLM-R-large, ~2.3GB resident. On this host it
failed to load with `OSError 1455` (paging file too small), twice. The fallback
worked exactly as designed — `_cross_encoder_semantic` returned `None`, the
provider fell back to dense, and `rr_bge` came out **byte-identical to
`rr_embedding`** (0.650 / 0.757, 38 ties).

That is worth flagging as an operational trap: **the symptom of a reranker too
large for its host is silently unchanged ranking**, not an error. One WARNING is
logged and the request succeeds. Anyone enabling `cross_encoder` should confirm
from the retrieval log that scores actually moved.

Separately, `hf_xet` (HuggingFace's Rust download backend) crashed on this host
with allocation failures at 2.8MB and 67MB while ~2GB was free; Python could
allocate 3.2GB in the same environment. `HF_HUB_DISABLE_XET=1` is required here
to download any model.

---

## 8. The first pass was held because the recency tier was dead

Checking whether the in-flight `published_at` -> `effective_start_date` rename
affected the first measurement turned up a code/data split:

```
effective_start_date   populated       0/152833
published_at           populated  152833/152833
```

The payload *index* on `effective_start_date` existed, and `app/` had no
remaining payload read of `published_at` — the code side of the rename was
complete, the data side had not run. So `_recency_scores` read a key no point
carried, `known` came back empty, and it returned `[_UNKNOWN] * len(candidates)`.
Recency, tier 4 of the ranking priority, was doing nothing: no error, no log
line.

Worse, mid-migration it was actively *biased* rather than merely inert.
`_UNKNOWN = 0.5` parks an undated candidate mid-set while dated ones scale
across [0,1], so at 44.6% populated an undated chunk outranked every dated chunk
scaling below 0.5. And the populated fraction was not a random sample — it was
precisely the ~5,150 documents whose dates were being corrected. Position within
a relevance band was briefly a function of how far the write had progressed.
Nothing was changed to accommodate that: `_UNKNOWN = 0.5` is the right answer
for a genuinely undated document, which the corpus still contains, and the state
resolved when the run completed.

**What the tier being live actually changed**, first pass -> re-measurement:

| config | MRR before | MRR after | nDCG before | nDCG after |
| --- | --- | --- | --- | --- |
| `dense+keyword` | 0.678 | 0.678 | 0.763 | 0.763 |
| `rr_embedding` | 0.650 | 0.669 | 0.757 | 0.761 |
| `rr_minilm_s128` | 0.828 | 0.855 | 0.824 | 0.825 |

`dense+keyword` is unmoved, as it must be — it does no banding. `rr_embedding`
improved, which was the prediction: it had been ordering on two of three
tie-break tiers. It did not improve enough to overtake doing nothing at all.

The gold set survived the backfill untouched: `--apply` selects points by
`document_id` and only calls `set_payload`/`delete_payload`, no point id is
created or changed, and `version.py` bumps `PAYLOAD` while leaving `CHUNKING`
and `CHUNK_IDENTITY` alone. No re-judging was needed.

### Three defects found while establishing that, none of them here

All three belonged to other sessions' work and were reported, not fixed, in this
tree.

1. `page_moves()` read the new columns before `copy_legacy_date_columns()` ran,
   so every page was silently skipped. The dry-run count went from 2,296 to
   5,154 documents once fixed.
2. **`migrate_payload_keys()` reverted what `apply()` wrote.** `apply()` sets the
   corrected `effective_start_date` but never deletes `published_at` — its
   `stale` list only ever holds *new* keys whose value is None.
   `migrate_payload_keys()` then scrolled with `with_payload=legacy`, could not
   see the new value, found the legacy key still present, and `set_payload`'d the
   legacy value over the correction. MySQL and Neo4j would both have looked
   correct while Qdrant silently reverted on ~5,150 documents.
   `invariants()` cannot catch it — it compares document counts, a content-hash
   checksum and a Qdrant point *count*, no payload values — and
   `migrate_payload_keys()` runs after the after-snapshot and after the
   `if not ok` gate. Fixed by making the key migration read both names and never
   overwrite a new key that already holds a value.
3. Two tests in `test_fusion_score_integrity.py` asserted a *scale* while
   reading ambient config, so enabling `RERANKER_PROVIDER=cross_encoder` in
   `.env` made them run a real model and compare 0.72 against sigmoid(-11.1).
   Pre-existing and not caused by the sigmoid change — which made an existing
   setting reachable rather than introducing the coupling. Both now pin the
   provider.

---

## 9. Recommendation

```
RERANKER_PROVIDER=cross_encoder
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANK_MAX_SEQ_LENGTH=128
# rerank_max_candidates stays at its 40 default
```

**128, on cost, and deliberately not 64.** At a 10-candidate pool: 512 costs
1370ms, 256 costs 574ms, 128 costs 323ms, 64 costs 181ms. Ranking quality is
indistinguishable across all four on this benchmark, so cost is the only
measured basis for the choice — the rising MRR column must carry no weight,
because §5 shows it is confounded with the gold set's 700-character judging
window rather than reflecting relevance.

128 rather than 64 because once the benchmark is silent the choice has to rest
on something else, and 64 tokens is ~256 characters: about a sixth of the graded
set's 1637-char median, and an eighth of a p75 chunk. A model judging a passage on its first sixth is doing topic
matching, and this corpus contains chunks whose relevance genuinely turns on
their later half — the benchmark cannot see that because its grader could not
either. 128 keeps roughly a third of a chunk in view at a quarter of 512's cost,
which is the conservative point on a curve whose quality axis is not
trustworthy. Take 64 if latency is the binding constraint; the measured evidence
does not distinguish them.

~90MB, English-only, which matches this corpus. At the 40-candidate cap expect
roughly 0.7s added per query, extrapolating from the scaling table in §6.

`reranker_provider` is left at `embedding` in `app/config.py`; the switch is a
separate, reviewed change.

Remaining, in order of value:

1. **Review a sample of `judgments_v1.draft.json` by hand.** Every number here
   rests on LLM-drafted grades. This is the single largest source of doubt.
2. **Re-judge on full chunk text: set `SNIPPET = 4000`.** `judge_retrieval`
   grades on `text[:700]` while **88.8% of the chunks it graded are longer than
   that**; the grader saw 42.8% of a median graded chunk and 42.6% of the gold
   set's total text. That favours any scorer whose window sits inside the
   grader's, and it confounds the sequence-length sweep *and* the
   cross-encoder-vs-embedding comparison, so a re-judging run must re-measure
   both. It is the only way to turn the +0.136-to-+0.194 range into a single
   trustworthy number.

   Costed exactly over the 491 graded passages, so it is not mistaken for a
   large job:

   | `SNIPPET` | gold-set text seen | extra input vs 700 |
   | --- | --- | --- |
   | 700 (current) | 42.6% | — |
   | 2088 (gold-set p75) | 95.8% | +103k tokens |
   | **4000** | **100.0%** | **+111k tokens** |

   Full coverage costs only ~8k tokens more than p75, so there is no reason to
   stop short of it. The entire untruncated gold set is 776k chars / ~194k
   tokens across 491 passages — one judging run, one constant changed, and a
   benchmark that can speak to sequence length instead of one that cannot.
3. **Re-measure `bge-reranker-v2-m3` on a host with the headroom** (§7). The
   ceiling reported here is the small model's, not the reranker idea's.
4. Re-check these figures after the legacy `published_at` payload keys are
   dropped. Nothing reads them, so this should not move, which is worth
   confirming rather than assuming.
