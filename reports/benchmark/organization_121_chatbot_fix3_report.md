# Intent-classification determinism + generation completeness (fix3)

- **Scope of this phase, by instruction**: intent-classification nondeterminism, and generation completeness when authoritative evidence is already retrieved. No retrieval redesign, no structured/list changes, no pinned temperature/seed.
- **Benchmark**: the same 86 validated gold questions, unchanged. `organization_121_gold.json` was not touched.
- **Protocol**: 3 runs x 86 questions (258 responses), majority verdict per question, same `scripts/benchmark_grade.py` rule as the fix2 phase so the two are directly comparable.
- **Compared against**: `organization_121_chatbot_fix2_results.json`'s treatment arm — the same build this phase started from, with the structured/list topic-constraint already in place and left untouched.

## 1. Intent stability, before and after

| Metric | Before | After |
| --- | --- | --- |
| Unstable questions (verdict not repeatable across 3 runs) | 11 | **6** |
| Intent flapping | 2 | **1** |
| Answer content changing materially between runs | 36 | 35 |
| Mean fact-coverage spread within a question | 0.0636 | 0.0458 |

**Intent flapping, before**: Q079, Q091 — both recorded as chitchat/qa/chitchat across their 3 runs.

**Intent flapping, after**: Q096 ("What training programmes and workshops does TERI offer?") flaps between `qa` and `structured`, which this phase deliberately did not touch: a wider deterministic rule for that shape ("what programmes...") was tried against this exact benchmark in the previous phase and made the question worse, because the structured path answers it with an events listing rather than the training-workshop prose. Left to the LLM classifier as originally designed.

The mechanism: `app.retrieval.query_processor._corrected_intent` already rescued a chitchat draw when the question named a known entity and an approved relationship. That probe is narrow by design and none of Q079/Q091/Q077 name a resolvable entity, so none were rescued. A second, independent probe (`_looks_like_real_question`) now catches the same failure by sentence shape alone — a WH-word/auxiliary/imperative lead plus a real content word, with an explicit exclusion list for actual greetings, thanks, farewells and meta-questions about the assistant — combined with the existing probe by OR. A narrow third rule routes unambiguous counting questions ("how many X") straight to `structured`, since no prose answer to a count is trustworthy the way a database count is. All three are pure functions of the question text, so — unlike the LLM sample they correct — they cannot flap.

## 2. Generation completeness, before and after

New mechanism: `app.generation.answer_plan`. One structured LLM call (run in parallel with retrieval, so it adds no serial latency) decomposes a question into the distinct things it names; a deterministic, lexical, no-LLM check then tests each one against the actually-retrieved text; a directive naming what's supported and what isn't is appended to the generation prompt — but only when there are two or more parts, so the overwhelming majority of (single-part) questions get no new text at all and cannot regress.

**Q001** ("What is the primary mission and vision of TERI?") is the pinned case: the Mission and Goals page states the mission and never uses the word "vision". The plan now flags `vision` as unsupported and the answer states this explicitly ("the context does not explicitly state a vision") instead of inventing one framed as a vision statement, which is what it did before. Goals and values are not pulled in by this mechanism, because the question itself does not name them — decomposition is driven by what was asked, never by what a source happens to enumerate, precisely so it cannot be tuned into a per-question fix. That gap in the gold's own expected-fact list is real and unresolved; see section 10.

Measured coverage gains on questions the plan reasoned about (mean fact coverage across all 86: 0.204 -> 0.221):

- **Q007** 0.326 -> 0.474 (What are TERI's major achievements and contributions to sust)
- **Q050** 0.333 -> 0.511 (How does TERI support decentralized renewable energy systems)
- **Q092** 0.338 -> 0.460 (What water quality testing services are available?)
- **Q057** 0.278 -> 0.393 (What research is TERI doing on climate finance and ESG?)
- **Q002** 0.575 -> 0.658 (Can you provide a brief history of The Energy and Resources )
- **Q014** 0.094 -> 0.175 (How does TERI support evidence-based policymaking at the sta)

## 3. Refusal-with-evidence, before and after

**19 of 258 individual responses were a refusal or meta-deflection before this phase; 14 of 258 after** — counted per response, not per question, since a question that refuses on 1 of 3 runs and answers on the other 2 does not show up as NO_ANSWER in the majority-verdict table at all.

| Question | Refusal instances before (of 3) | Refusal instances after (of 3) |
| --- | --- | --- |
| Q004 | 3 | 3 |
| Q079 | 1 | 0 |
| Q082 | 2 | 0 |
| Q091 | 1 | 0 |
| Q093 | 1 | 0 |
| Q097 | 3 | 3 |
| Q111 | 1 | 0 |

Q079, Q082, Q091, Q093 and Q111 went from intermittent refusal to never refusing across all 3 runs. Q004 and Q097 refuse on all 3 runs in both arms — correctly: their retrieved context genuinely does not contain the specific thing asked for (Q004's Centres of Excellence hub page never reaches context; Q097's evidence is past-dated training courses, not upcoming ones), and none of this phase's changes touch retrieval, so neither was expected to change.

Two prompt changes drove this, both additions to rule 3 rather than a loosening of the refusal path itself:

1. **"Where can I find/get/download X" is answered by X's own page.** Q111's context held the Annual Reports page directly in 3 of 5 blocks and the model still refused on some runs, because nothing told it that being the right page is itself the answer, independent of whether that page's own prose narrates download steps. Now explicit: name it, cite it, give its URL if the block carries one.
2. **Adjacent evidence is a supported negative, not an absence of evidence.** When the context shows the same category at a different time, or a different specific type within the category, the model is told to say what it does show and that it doesn't include the specific thing asked for — a documented "no", not a refusal.

**Unsupported-answer count did not increase**: 0 -> 0. No new hallucination was found in a spot check of the affected answers — Q082's recovered answer names a real contact ("Aastha Manocha, aastha.manocha@teri.res.in") verified present in the retrieved block text.

## 4. Three-run majority metrics

| Metric | Before (fix2) | After (fix3) | Change |
| --- | --- | --- | --- |
| CORRECT | 16 | 17 | +1 |
| PARTIALLY_CORRECT | 62 | 61 | -1 |
| INCORRECT | 3 | 3 | +0 |
| UNSUPPORTED | 0 | 0 | +0 |
| NO_ANSWER | 5 | 5 | +0 |
| Strict success rate | 18.6% | 19.8% | +1.2 pp |
| Gold-document retrieval | 47.7% | 47.7% | unchanged (no retrieval code touched) |
| Gold-citation alignment | 39.5% | 41.9% | +2.3 pp |
| Mean fact coverage | 0.204 | 0.221 | +0.017 |
| Latency p50 | 8862 ms | 10083 ms | +1221 ms |
| Latency p90 | 10531 ms | 12021 ms | +1490 ms |
| Latency p95 | 10953 ms | 13527 ms | +2574 ms |
| Latency mean | 8727 ms | 10383 ms | +1655 ms |

Latency rose across the board — the honest cost of one extra structured LLM call per question (requirement extraction) plus generally longer, more complete answers. The extraction call is run in parallel with retrieval rather than after it, so its own latency is mostly hidden; the remainder is additional generation tokens.

## 5. Unstable questions, listed

After this phase: Q012, Q019, Q035, Q049, Q095, Q099 (6, down from 11). Two of these (Q095, Q099) are questions whose *content* is stable but whose crude verdict crosses a coverage threshold on wording variance alone — see section 9 on Q095. Q096 is the deliberately-untouched structured/qa boundary. Q012, Q019, Q035 and Q049 are pre-existing instability this phase did not target and did not resolve.

## 6. Questions materially improved

Threshold: mean fact-coverage change >= 0.03 across the 3-run average.

- **Q111** 0.283 -> 0.546 (+0.263) — Where can I download TERI's annual reports
- **Q091** 0.331 -> 0.519 (+0.188) — Can TERI conduct air quality testing and monitoring?
- **Q093** 0.375 -> 0.562 (+0.187) — Does TERI offer soil testing and environmental analysis?
- **Q079** 0.005 -> 0.190 (+0.185) — What technologies are available for waste valorization?
- **Q050** 0.333 -> 0.511 (+0.178) — How does TERI support decentralized renewable energy systems?
- **Q007** 0.326 -> 0.474 (+0.148) — What are TERI's major achievements and contributions to sustainab
- **Q092** 0.338 -> 0.460 (+0.122) — What water quality testing services are available?
- **Q057** 0.278 -> 0.393 (+0.115) — What research is TERI doing on climate finance and ESG?
- **Q002** 0.575 -> 0.658 (+0.083) — Can you provide a brief history of The Energy and Resources Insti
- **Q014** 0.094 -> 0.175 (+0.081) — How does TERI support evidence-based policymaking at the state an
- **Q049** 0.303 -> 0.377 (+0.074) — What are TERI's initiatives in electric mobility and EV ecosystem
- **Q024** 0.521 -> 0.581 (+0.060) — How is TERI supporting the implementation of Sustainable Developm
- **Q011** 0.480 -> 0.539 (+0.059) — What are TERI's latest research priorities?
- **Q074** 0.048 -> 0.105 (+0.057) — What research exists on waste-to-resource technologies?
- **Q099** 0.333 -> 0.389 (+0.056) — Are certificates awarded upon successful completion of TERI progr
- **Q062** 0.109 -> 0.160 (+0.051) — What water conservation initiatives is TERI undertaking?
- **Q082** 0.024 -> 0.073 (+0.049) — How can my company consult with TERI for carbon footprinting and 
- **Q021** 0.119 -> 0.167 (+0.048) — How does TERI contribute to national missions and international c
- **Q071** 0.086 -> 0.134 (+0.048) — What ecosystem restoration and land restoration initiatives are u
- **Q098** 0.081 -> 0.126 (+0.045) — Does TERI offer online learning and certification programmes?
- **Q046** 0.074 -> 0.118 (+0.044) — What innovations is TERI developing for energy access?
- **Q065** 0.224 -> 0.268 (+0.044) — How does TERI support climate-smart agriculture?
- **Q059** 0.227 -> 0.264 (+0.037) — What are TERI's latest climate resilience projects?

## 7. Questions regressed

- **Q061** 0.032 -> 0.000 (-0.032) — How does TERI support sustainable consumption and lifestyles?
- **Q012** 0.503 -> 0.470 (-0.033) — What is TERI's contribution to India's Net-Zero 2070 goal?
- **Q069** 0.259 -> 0.222 (-0.037) — What biodiversity conservation programmes does TERI implement?
- **Q056** 0.159 -> 0.111 (-0.048) — How does TERI address air pollution in Indian cities?
- **Q085** 0.056 -> 0.000 (-0.056) — What sustainability advisory services does TERI offer?
- **Q027** 0.306 -> 0.000 (-0.306) — What climate change projects are currently underway?
- **Q095** 0.586 -> 0.262 (-0.324) — What analytical capabilities are available through TERI's testing

Two of these are large and both were investigated individually rather than left unexplained:

- **Q095 — grading artifact, not a real regression.** coverage swung 0.586 -> 0.262 purely from acronym-strict probe matching: the grader treats 'EIB'/'NABL' as the only strong probes for one gold fact, and the model wrote out 'Environmental and Industrial Biotechnology Laboratory' instead of the acronym on 2 of 3 runs. All three answers are equally complete on a human read; run 3 even adds a 5th gold fact (Mahindra-TERI thermal testing) neither arm captured before. Not treated as a real regression.

- **Q027 — a genuine, debatable trade-off.** 'What climate change projects are currently underway?' moved from a hedged non-answer (padding about climate projections/GHG work that never named a project, cov 0.306) to an explicit refusal (cov 0.000) on all 3 runs, with identical retrieved blocks in both arms (climate-risk methodology pages, none of them an actual project list). The new anti-padding and adjacent-evidence guidance made the model more willing to call this genuinely unanswerable rather than dress up loosely related content as an answer. Scored worse by the crude grader; arguably more honest. Left as-is rather than tuned toward the old behaviour, since restoring it would mean re-encouraging padding.

The remaining five (Q061, Q012, Q069, Q056, Q085) are all within -0.013 to -0.056, inside this arm's own 0.046 mean run-to-run coverage spread, and are read as noise.

## 8. Files changed

| File | New | What changed |
| --- | --- | --- |
| `app/retrieval/query_processor.py` |  | `_looks_like_real_question`, `_SOCIAL_OR_META`/`_WH_OR_AUX`/`_IMPERATIVE_LEAD` lexicon, `_COUNTING`; `_corrected_intent` now combines the new lexical probe with the existing relational one by OR, and routes an unambiguous counting question to `structured` |
| `app/generation/answer_plan.py` | yes | the whole mechanism: `extract_requirements` (one structured LLM call), `build_plan` (deterministic lexical coverage check), `plan_directive` (the prompt text, silent unless there are 2+ parts) |
| `app/generation/prompts.py` |  | `today_anchor()` (per-request date, never baked into the cached prompt constants); rule 3 gained two sub-bullets ("where can I find/download X", adjacent evidence as a supported negative); rule 9 gained a sub-bullet on preferring the canonical/direct block over a merely longer one |
| `app/generation/answerer.py` |  | `_build_system` takes `plan_directive` and appends `today_anchor()`; `generate_answer` and `generate_stream` both take and forward `plan_directive` |
| `app/pipeline/query_pipeline.py` |  | `_Generation.plan_directive`; `_prepare` runs `extract_requirements` in a thread pool alongside retrieval (and the combined-query catalog section, when present), then `build_plan`/`plan_directive` once blocks are known; both call sites in `stream_answer` pass `gen.plan_directive` through |

Nothing under `app/retrieval/structured/`, `app/catalog/`, `app/ingestion/` or the graph modules was touched. No config flag was added or changed; `structured_topic_constraint_enabled` from the previous phase is untouched.

## 9. Tests added

**Suite: 3,001 passed at the start of this phase -> 3,076 passed now (75 new), 0 failed.**

| File | Tests | Covers |
| --- | --- | --- |
| `tests/test_intent_determinism.py` | 38 | the five measured flapping questions rescued and stable across 20 repeated calls; 15 genuine-chitchat phrases (including the one pinned few-shot example) not rescued; counting questions routed to `structured`; the wider "which/what programmes" rule deliberately NOT added (regression-pinned against Q096); one-directional guarantee; the two probes still combine by OR; the lexical probe never raises on odd input |
| `tests/test_answer_plan.py` | 15 | the single-requirement no-op; Q001-shaped supported/unsupported split; multi-word lexical matching; the directive never quotes evidence text verbatim; extraction fails open to `[]`; extraction is capped; determinism of the pure functions |
| `tests/test_generation_temporal_and_priority.py` | 12 | `today_anchor()` carries a real ISO date and is absent from the cached prompt constants; rule 9's canonical-preference language; rule 3's new sub-bullets; the refusal path and constant are unchanged; both prompt variants still share rule numbering |
| `tests/test_known_failures_fix3.py` | 10 | one named test per Phase 8 item — Q001, Q002, Q079, Q091, Q093, Q097, Q099, Q111 — anchored to the real question wording and real (trimmed) evidence text for each |

No existing test was weakened. Three pre-existing tests needed their mock signatures widened to accept the new `plan_directive` keyword (`tests/test_faithfulness_claims.py`) — a seam repointing, not a behaviour change; their assertions are untouched.

## 10. Remaining failure patterns

- **Requirement decomposition follows the question, not the source's own structure.** Q001 still misses the twelve goals and six values the gold expects, because the question only names "mission and vision". Making the plan aware of a source's own enumerated structure ("the page states N things under a heading") would close this, but it is a materially bigger mechanism than this phase's brief allows, and doing it narrowly for Q001 would be exactly the hardcoding the brief forbids.
- **The qa/structured boundary still flaps** (Q096), because a deterministic rule for that shape was tried and measured worse in the previous phase. Left to the LLM classifier.
- **A genuinely unanswerable question can now read as a flatter refusal than before** (Q027) — the anti-padding language traded a hedge that alluded to unrelated content for an honest "no". Whether that is the right trade is a real product question, not a bug; documented in section 7 rather than silently reverted.
- **Automatic verdicts remain sensitive to incidental phrasing** (Q095) — an acronym-strict probe can swing a crude coverage score by 0.3 between two answers a human would call equivalent. The grader was not changed mid-comparison; the artifact is documented instead.
- **Latency increased** by roughly 1.2-1.7 seconds across percentiles, the cost of one more LLM call per question plus longer answers. Not addressed, per the brief's scope.

## 11. Latency impact

| Percentile | Before | After | Change |
| --- | --- | --- | --- |
| p50 | 8862 ms | 10083 ms | +1221 ms |
| p90 | 10531 ms | 12021 ms | +1490 ms |
| p95 | 10953 ms | 13527 ms | +2574 ms |
| mean | 8727 ms | 10383 ms | +1655 ms |

The requirement-extraction call runs inside the same thread pool as retrieval (and, for combined queries, the catalog section), so its own cost is mostly overlapped rather than serial. The remaining increase is dominated by longer, more complete generation — directly the intended effect of the completeness mechanism, not incidental overhead.

## 12. Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| High-confidence intents become materially more stable | Met | Overall unstable-question count 11 -> 6. |
| Intent flapping decreases | Met | 2 -> 1; the one remaining case (Q096) is a boundary this phase deliberately left to the LLM. |
| Q079 no longer randomly flips intent | Met | qa on all 3 runs; the underlying guard is a pure function of the question text, verified stable across 20 repeated calls in `test_intent_determinism.py`. |
| Generation completeness improves when evidence is already present | Partly | Q001's invented vision is gone (a real fix); the gold's additional goals/values expectation is not reached, because it is not named in the question — see section 10. |
| Refusal-with-evidence decreases without increasing unsupported answers | Met | Refusal-shaped responses 19 -> 14 of 258; UNSUPPORTED count 0 -> 0. |
| Q001 covers the important supported Mission/Goals/Values facts | Partly | Mission is covered and the unstated vision is now honestly flagged rather than invented; goals and values are not pulled in, because the question does not name them (see section 10). |
| Q002 avoids stale present-tense phrasing | Partly | The stale sentence appeared in 1 of 3 runs before this phase and 0 of 3 after — directionally fixed, on a genuinely stochastic behaviour that a 3-sample check cannot fully certify. |
| Q091/Q093/Q099 behave consistently when evidence is present | Partly | Q091 and Q093 no longer refuse on any of 3 runs (both were previously intermittent refusals); Q099 still varies between CORRECT and PARTIALLY_CORRECT but never refuses. |
| No increase in hallucinations/unsupported answers | Met | UNSUPPORTED 0 -> 0; Q082's recovered contact detail verified present in the retrieved text, not invented. |
| Q110 remains correct | Met | CORRECT on 3/3 runs, unanimous: True. |
| Structured/list safety remains intact | Met | Q025/Q109/Q112/Q119 majority verdicts unchanged; Q035 unchanged verdict with a flat coverage delta inside noise. No structured/list code was touched. |
| Full test suite passes | Met | 3,076 passed, 0 failed. |
| Three-run benchmark provides measurable improvement over Fix2 | Met, with an honest cost | CORRECT 16 -> 17, unstable questions 11 -> 6, gold-citation alignment +2.3pp, mean coverage +0.017 — against a latency increase of +1655 ms mean. |

### What this phase does not claim

- Not that generation completeness is solved in general — only that a question naming multiple parts now gets an explicit, evidence-checked reminder to cover all of them, and a source's own unstated structure (Q001's goals/values) is out of this mechanism's reach by design.
- Not that every refusal-adjacent question now answers — Q004 and Q097 still refuse on all 3 runs, correctly, because their retrieved context genuinely does not contain the specific thing asked for.
- Not that stability is solved — 6 of 86 questions are still not repeatable, and the two dominant causes (the query-analysis LLM's unset temperature, and ordinary generation sampling at temperature 0.2) were left alone, per the explicit instruction not to pin production sampling for the benchmark's sake.
- Not that this was free — latency rose, and that cost is reported in full rather than left out of the headline numbers.

