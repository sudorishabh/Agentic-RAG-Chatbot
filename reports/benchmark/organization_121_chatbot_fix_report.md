# Retrieval and generation fix pass - 86-question gold benchmark

- **Endpoint**: `POST http://localhost:8000/chat` - the real production SSE pipeline (`app.main`), same as the baseline run. No stub.
- **Retrieval telemetry**: `POST http://localhost:8000/search`, same pipeline, called separately because the /chat SSE contract does not expose per-block detail.
- **Date**: 2026-08-19 | **Gold set**: `organization_121_gold.json` (v2, corrected) - **unchanged in this phase**; the file was last written when the judgement pass froze it, before the baseline run. No gold answer, expected fact or evidence definition was edited, added or removed.
- **Benchmark**: the same 86 questions, in the same order, graded by the same script (`grade_after.py` is `grade.py` with the input file swapped). No grading rule was changed.
- **Configuration unchanged**: `graph_routing_enabled=True`, `graph_retrieval_enabled=False`, `semantic_cache_enabled=False`, `retrieval_top_k=6`, `website_max_slots=2`, `pdf_max_slots=2`, `graph_routing_budget_seconds=3.0` (**not raised**), model `gpt-4o-mini`.
- **Stores untouched**: no re-ingest, no corpus clearing, no knowledge-base rebuild, no graph reprojection. MySQL, Qdrant and Neo4j hold exactly what they held at baseline.
- **Run integrity**: the retrieval server failed mid-run at Q064 and returned HTTP 500 for the remainder. Those 41 questions were discarded and re-issued against a recovered server; the graded set contains 86 clean responses and zero errored ones. The failure was transient and environmental - the same questions succeed on retry with unchanged code - and it is recorded here rather than quietly re-run.

## 0. Summary

Nine files changed across retrieval, generation, graph routing and query understanding, fixing five diagnosed defects and one regression this pass caused. The measurable result:

- **Retrieval improved, and that gain is solid.** The authoritative source the gold names now reaches 49% of questions, up from 41.9%, and gold citation alignment moved 32.6% -> 38%. Retrieval is also the layer that repeats deterministically, so these numbers mean what they say.
- **Verdicts barely moved**: CORRECT 9 -> 11, NO_ANSWER 8 -> 7, with seven questions changing class in both directions. Four of those seven are questions the variance probe shows are unstable run to run, so the verdict table overstates what changed.
- **The graph deadlock is genuinely fixed** - breaker CLOSED, no timeouts from the index load - but the graph still contributes to one question in this set, and that one is marginal against its 3 s budget on a cold process.
- **Two of the four targeted refusals are properly fixed** (Q083, Q099). Q091 is intermittent, Q093 is untouched, and two new refusals appeared (Q019, Q111).
- **The stale-present-tense and structured-list problems are not solved.** A prompt rule did not stop the model repeating a dated sentence, and the list-collision work was deliberately deferred.

The most consequential finding of this pass is not any of the fixes: it is that **the benchmark cannot currently resolve small changes**, because four of fifteen re-tested questions change outcome across repeats of identical code. Section 1b sets that out, and it should be fixed before the next pass, or the next pass will not be measurable either.

## 1. Baseline metrics (what this pass started from)

| Metric | Baseline |
| --- | --- |
| CORRECT / PARTIALLY_CORRECT / INCORRECT / NO_ANSWER | 9 / 65 / 4 / 8 |
| Strict success rate | 10.5% |
| Gold document retrieval rate | 41.9% |
| Gold citation alignment rate | 32.6% |
| Mean per-question fact coverage | 0.185 |
| Facts substantially covered | 97 of 559 |
| Graph route outcomes | {'timed_out': 3, 'circuit_open': 83} |
| Latency mean / p50 / p90 / p95 | 9113 / 9272 / 10749 / 11306 ms |

The baseline report's headline finding was that the authoritative source the gold names reached retrieval for only 42% of questions. Everything below is aimed at that, at the four refusals that sat on top of usable evidence, and at the graph layer being inert.

## 1b. How much of any measured change is real

This has to come before the results table, because it bounds how the table can be read.

Two runs of the *same build* disagreed on several questions, so 15 verdict-critical questions were re-issued three times each against unchanged code. **Four of the fifteen changed outcome class or routed intent across the three repeats:**

| Question | Repeat 1 | Repeat 2 | Repeat 3 |
| --- | --- | --- | --- |
| Q019 | refuses | answers (1522 chars) | refuses |
| Q079 | qa, 227 chars | chitchat, 301 chars | chitchat, 1890 chars |
| Q091 | deflects (155 chars) | answers (1062 chars) | deflects (224 chars) |
| Q111 | answers | refuses | answers |

Q002's stale anniversary sentence appears in one of three. Q093 refuses in three of three. Q083, Q018, Q063, Q096, Q110, Q099, Q004, Q082 and Q097 were stable.

Two independent sources of nondeterminism are visible: the **intent classifier**, which is LLM-backed and put Q079 in two different buckets and Q091 in two different buckets, and the **answerer**, which refused and answered the same context on different calls. The retrieval layer is comparatively stable - block counts were identical across repeats for 14 of the 15.

What follows from that:

- A single-run verdict flip on a refusal-adjacent question is **weak evidence**. Where the probe covers a question, its note in the results JSON records the measured rate rather than the single sample.
- Aggregate retrieval measures - gold document retrieval, gold citation alignment, which documents reach context - are the trustworthy numbers here, because retrieval is the stable layer.
- Per-question fact-coverage deltas below roughly 0.05 should be read as noise.
- The benchmark as it stands **cannot resolve a change worth less than about one verdict in twenty**. Running each question three times and grading the majority would fix that, and is the most valuable single improvement available to this harness.

## 2. Before vs after

| Verdict | Before | After | Change |
| --- | --- | --- | --- |
| CORRECT | 9 | 11 | +2 |
| PARTIALLY_CORRECT | 65 | 64 | -1 |
| INCORRECT | 4 | 4 | +0 |
| UNSUPPORTED | 0 | 0 | +0 |
| NO_ANSWER | 8 | 7 | -1 |
| SYSTEM_ERROR | 0 | 0 | +0 |
| **Total** | **86** | **86** | |

| Metric | Before | After | Change |
| --- | --- | --- | --- |
| Strict success rate (CORRECT only) | 10.5% | 12.8% | +2.3 pp |
| Gold document retrieval rate | 41.9% | 48.8% | +7.0 pp |
| Gold citation alignment rate | 32.6% | 38.4% | +5.8 pp |
| Mean gold documents retrieved per question | 0.48 | 0.53 | |
| Mean per-question fact coverage | 0.185 | 0.205 | +0.020 |
| Facts substantially covered (of 559) | 97 | 104 | +7 |
| Answers with zero citations | 3 | 1 | |
| Answers using zero retrieved chunks | 3 | 1 | |
| System errors | 0 | 0 | |

**Verdict changes, question by question:**

| Question | Before | After |
| --- | --- | --- |
| Q019 - What are TERI's latest studies on air quality and pollution ma | PARTIALLY_CORRECT | NO_ANSWER |
| Q035 - What innovations and technologies are being demonstrated under | INCORRECT | PARTIALLY_CORRECT |
| Q083 - Does TERI provide Life Cycle Assessment (LCA) services? | NO_ANSWER | CORRECT |
| Q091 - Can TERI conduct air quality testing and monitoring? | NO_ANSWER | CORRECT |
| Q096 - What training programmes and workshops does TERI offer? | PARTIALLY_CORRECT | INCORRECT |
| Q099 - Are certificates awarded upon successful completion of TERI pr | NO_ANSWER | PARTIALLY_CORRECT |
| Q111 - Where can I download TERI's annual reports | PARTIALLY_CORRECT | NO_ANSWER |

Four of these seven - Q019, Q091, Q096 and Q111 - are questions the variance probe found unstable across repeats of identical code. Q019 refuses on two runs in three, Q091 answers on one in three, Q111 refuses on one in three, and Q096 returned correct prose on all three repeats despite the graded run producing an off-topic event list. Only Q083, Q099 and Q035 changed for reasons the evidence ties to the code.

## 3. What was changed, and why

Nine source files. Every change is in retrieval, generation, graph retrieval or query understanding - the layers this brief permits. No ingestion, entity-extraction, entity-resolution, claim-extraction or schema code was touched.

### 3.1 The graph was inert on all 86 questions - cold-start deadlock

**Files**: `app/retrieval/graph/policy.py`

**Root cause.** Not a slow query. `entity_index()` costs **7.2 s on a cold cache** against a **3.0 s** routing budget, and the load happened *inside* the budget. Every attempt therefore timed out during the load, three timeouts opened the circuit breaker, the breaker's 60 s cooldown outlived nothing because each probe re-entered the same load - so the index could never finish warming and the graph could never answer. The baseline's `3 timed_out + 83 circuit_open` is that deadlock, not 86 slow queries.

**Change.** Added a third outcome, `INDEX_WARMING`, and `entity_index_or_warm()`. On a cold cache it submits a **one-shot background load** on the existing graph executor and returns `None` immediately; `_attempt` then returns `INDEX_WARMING`. That outcome is in `FALLBACK_OUTCOMES` and deliberately **not** in `BREAKING_OUTCOMES`, so declining to route does not count against the breaker. `prewarm_entity_index()` lets a caller warm it up front. The 3.0 s budget is unchanged.

**Evidence it worked.** A cold call now **declines in ~250 ms** instead of burning the budget, and the breaker stays **CLOSED** across a full 86-question replay, so the baseline's `3 timed_out + 83 circuit_open` cannot recur. It did not make the graph fast: measured five times in a row in one process, the one routable query took 3036 ms (timed out), 1980 ms, 95 ms, 62 ms, 74 ms - a second cold cost, in the driver or the Cypher plan cache, that this change does not address. See section 8.

### 3.2 `Claim.object_literal` mismatch

**Files**: `app/retrieval/graph/templates.py`

**Root cause.** All 1,374 claims in the graph carry an entity object and none a literal. The projection writes `SET cl.object_literal = null`, and Cypher **removes** a property set to null rather than storing it - so the key does not exist on any node and `c.object_literal AS object_literal` emits `UnknownPropertyKeyWarning` on every template execution.

**Change.** Two occurrences changed to `properties(c).object_literal AS object_literal`, which reads the key if it is ever written and yields null silently when it is not. Literal support is preserved for future data; the schema was not touched and no reprojection was needed.

**Evidence it worked.** Verified warning-free against the live graph, with the literal path still returning the value when a claim has one.

### 3.3 Canonical pages were unreachable - three stacked defects

**Files**: `app/retrieval/reranker.py`, `app/retrieval/search/strategies.py`, `app/retrieval/title_leg.py` (new), `app/catalog/state.py`, `app/retrieval/retriever.py`

**Root cause.** The baseline's headline failure had three independent causes, and fixing any one alone changes nothing. (a) `_authority_scores` read a payload key **nothing in this corpus writes**, so authority was a constant and the first tie-break inside a relevance band was *completeness* - a length proxy. A 60-word service node that answers the question loses every length contest to a 400-word annual-report chunk that merely mentions the subject. (b) `extract_key_terms` skips its content-word pass whenever any precise pattern matched, and the organisation's acronym matches nearly every question here, so the lexical leg pulled on `['TERI']` alone. (c) Neither of those can retrieve a page whose body text is a list of link labels - the Centres of Excellence hub page reads as 'CONCOR-TERI Centre ... Read More' nine times over, so its embedding sits far from the question while a press release *about* one centre reads like prose and wins. Only its **title** identifies it.

**Change.** (a) `_derived_authority()` derives authority from `source_type` and CMS `bundle` when the payload does not carry it (canonical page/services/basic 0.90, primary publications 0.75, projects 0.60, news and events 0.45, attachments 0.35, graph facts 1.0), and authority is now banded **above** completeness in `_sort_key`. An explicitly stamped `source_authority` still wins, so a corpus that sets it keeps control. (b) `extract_content_terms()` returns the query's plain content words unconditionally, as a **separate** lexical pull, so it cannot dilute a query that already named something precisely. (c) A new title leg resolves documents by word-level title overlap against `documents.title` in MySQL, then pulls their chunks from Qdrant by id and hands them to RRF as one more ranking. It adds a ranking and never replaces one, so a coincidental title match loses to the dense pull as usual.

**Evidence it worked.** The title leg now ranks 'Annual Reports', 'Mission and Goals', 'Contact Us' and 'Environmental design consultancy and advisory services' first for their questions. Gold document retrieval across the benchmark moved 41.9% -> 48.8%.

### 3.4 Refusal while the evidence was in context

**Files**: `app/generation/prompts.py`

**Root cause.** Four questions (Q083, Q091, Q093, Q099) refused or deflected while the exact gold document sat in the context. Q091's block 1 *was* the Air Quality Research service node, which states that TERI provides monitoring through a NABL-accredited laboratory. The cause was prompt rule 8: written to stop the model inventing counts and enumerating a catalogue from a handful of chunks, it was broad enough that the model treated any enumerable question as unanswerable and refused rather than answering the part it could.

**Change.** Rule 8 keeps the count prohibition but now permits enumeration from blocks the context marks as an `official page`; `_source_hint` stamps that marker using the same derived-authority function the reranker uses, so the prompt and the ranker agree on what canonical means. Rule 3 gained two sub-bullets: a grounded partial answer is worth more than a refusal, and a yes/no question whose answer is evidenced is answered yes or no. **The prompt does not tell the model to answer every question** - the refusal path and the `REFUSAL` constant are unchanged, and the rule still requires the evidence to be present.

**Evidence it worked.** Mixed, and the variance probe is what separates the parts. **Q083 is fixed and stable** - a documented yes on all three repeats at consistent length (796 / 821 / 820 characters), coverage 0.112 -> 0.412. **Q099 is fixed** - coverage 0.0 -> 0.333, answered on all three. **Q091 is not settled**: it answers correctly in the graded run (coverage 0.016 -> 0.506) but deflects on two of three repeats. **Q093 is not fixed at all** - it refuses on all three repeats. So of four refusals this change targeted, two are fixed, one is intermittent and one is untouched. Zero-citation answers fell 3 -> 1.

### 3.5 Temporal: 'upcoming' answered with past events, and stale present tense

**Files**: `app/retrieval/temporal_gate.py` (new), `app/catalog/state.py`, `app/generation/prompts.py`

**Root cause.** Q097 ('any upcoming TERI training programmes?') retrieved six **past** programmes (TERI-ITEC 2013-14, 2015-16) with no date filtering at all, so the system had no way to tell upcoming from historic. Separately, Q002 reported 'As of 2023, TERI is celebrating its 50th anniversary' in the present tense - a dated press-release sentence presented as current at the 2026 reference date.

**Change.** `temporal_gate.py` classifies a question as PAST / UPCOMING / CURRENT / POINT_IN_TIME / DATE_RANGE / NONE and, for UPCOMING only, removes context blocks whose `field_event_start_date` is in the past, renumbering the survivors. It is **removal-only and fail-safe**: if gating would empty the context it returns the list unchanged, so it can never turn an answerable question into a refusal. Dates come from a new read-only batched accessor, `state.event_start_dates()`. On the generation side, rule 9 gained a sub-bullet: time-bound wording in a source is reported as of that source's date, never as of now.

**Evidence it worked.** The gate works; the prompt guard does not, reliably. Q097 no longer presents 2013-15 courses as upcoming - its context fell from 6 blocks to 3 - but it still refuses instead of stating the documented negative, so only its false positive is fixed. Q002's coverage rose 0.484 -> 0.659 and it now names the founder and the Pachauri tenure, but the stale 'As of 2023 ... celebrating its 50th anniversary' sentence **appears in one of three repeats** and is present in the graded run. A prompt line is advisory; suppressing dated wording reliably needs enforcement in the pipeline, which this pass did not build.

### 3.6 A regression this pass caused, found and fixed before shipping

**Files**: `app/retrieval/title_leg.py`

**Root cause.** The first post-fix run regressed Q018 ('What research is TERI conducting on climate finance?') from a grounded answer to one about a **spring census in Manipur**, with context cut from 5 blocks to 2. Isolated by re-running the pipeline's own `retrieve()` call with each new leg disabled in turn: with the title leg off the question returns 5 blocks led by 'Climate Finance Study for ...'; with it on, 2. The cause was the title leg's single-distinctive-word rule. 'research' is 6 letters and so counted as distinctive, and it matched the grab-bag page 'Our Research Focus', whose chunks then displaced the real evidence through RRF.

**Change.** A one-word match must now clear a much tighter document-frequency bar than a two-word match: the term must appear in at most 1% of catalogue titles. Measured on the live catalogue (8,500 website titles) that drops 'research' (1.48%), 'training' (1.69%), 'quality' (1.62%) and 'finance' (1.34%) from carrying a match alone, while keeping every canonical page this leg exists for: 'contact' 0.02%, 'reports' 0.12%, 'mission' 0.58%, 'excellence' 0.74%, 'centres' 0.08%. Two-word matches are unaffected, because agreement between two terms is evidence a single common word cannot supply.

**Evidence it worked.** Q018 recovers 5 blocks led by 'Climate Finance Study for ...' and 'Investment and Financial flows'. The **entire 86-question benchmark was re-run after this change**, and the numbers in this report are from that run, not from the run that exposed the bug.

### What was deliberately not changed

- **The structured/list collision (Q025, Q035, Q109, Q112, Q119).** Diagnosed: `list_records` lists by CMS *bundle* with no topical constraint, so two different questions that resolve to the same bundle produce a byte-identical list head, and a person-lookup question returns publications. Not changed, because the same mechanism produces Q110 - the run's one complete structured success, with all ten citations resolving to gold documents - and destabilising it immediately before the regression run would have cost more than it bought. This is the single largest piece of known, diagnosed work left.
- **The graph fallback contract.** `if graph_blocks: return graph_blocks` was **not** reintroduced. Graph rows still merge with the semantic pull under `SEMANTIC_MIN_SLOTS = 2`.
- **The routing budget.** Still 3.0 s. The deadlock was fixed by moving the index load out of the budget, not by widening it.
- **Tests.** No test was weakened or deleted to make a change pass. Two were repointed at a renamed seam with their assertions intact (see section 5).

## 4. Files changed

| File | New/modified | What changed |
| --- | --- | --- |
| `app/retrieval/graph/policy.py` | modified | `INDEX_WARMING` outcome, `_fresh_index()`, `entity_index_or_warm()`, `prewarm_entity_index()`; `_attempt` declines instead of timing out on a cold index |
| `app/retrieval/graph/templates.py` | modified | `c.object_literal` -> `properties(c).object_literal` in two templates |
| `app/retrieval/reranker.py` | modified | `_derived_authority()`, `is_graph_facts_payload()`, `_nested_bands()`, `_authority_bands()`, bundle authority constants; `_Ranked.authority_band` and a re-ordered `_sort_key` |
| `app/retrieval/search/strategies.py` | modified | `extract_content_terms()` - the unconditional content-word companion to `extract_key_terms` |
| `app/retrieval/title_leg.py` | **new** | title-anchored retrieval leg: `_terms()`, `_title_words()`, `_score()`, `_title_frequencies()`, `_selective_terms()`, `_rare_terms()`, `title_candidates()`, `title_search()` |
| `app/retrieval/temporal_gate.py` | **new** | `detect_mode()`, `event_start_dates()`, `gate_upcoming()` - removal-only date gating for 'upcoming' questions |
| `app/catalog/state.py` | modified | two read-only accessors: `website_titles()` and `event_start_dates(document_ids)` |
| `app/retrieval/retriever.py` | modified | wires the content-term and title legs into the existing thread pool as two more RRF rankings (`rag.content_term_leg`, `rag.title_leg`) and calls `_gate_temporal()` last |
| `app/generation/prompts.py` | modified | `CANONICAL_MARKER`, `_is_canonical()`; `_source_hint` marks canonical blocks; rule 3 sub-bullets on partial answers and yes/no questions; rule 8 permits enumeration from official pages; rule 9 sub-bullet on reporting time-bound wording as of the source's date |

## 5. Tests

**Suite: 2,901 passed at baseline -> 2,947 passed now, 0 failed.** All 46 new tests are regression cover for the defects above.

| Test file | New/modified | Tests | Covers |
| --- | --- | --- | --- |
| `tests/test_graph_index_warmup.py` | **new** | 5 | the cold-start deadlock: that a cold index declines rather than blocking, that the decline does not open the breaker, that the background load runs once and not per-query, and that a warm index answers |
| `tests/test_temporal_gate.py` | **new** | 23 | mode detection across the six modes, that gating is removal-only, that it fails safe rather than emptying the context, and that block numbering stays contiguous |
| `tests/test_canonical_retrieval.py` | **new** | 18 | derived authority ordering and the explicit-authority override; that authority beats the length proxy inside a relevance band; that `extract_key_terms` collapses to the org acronym and `extract_content_terms` recovers the topical words; title-leg word boundaries, the ubiquitous-term cut, the small-catalogue floor, and the one-word rarity rule that fixes Q018 |
| `tests/test_graph_routing.py` | modified | - | one monkeypatch repointed from `entity_index` to `entity_index_or_warm`, the seam `_attempt` now calls. Assertions unchanged |
| `tests/test_keyword_leg.py` | modified | - | `pulls == [['COP','2024']]` became `['COP','2024'] in pulls` plus `len(pulls) == 2`, because the content leg makes a second, separate lexical pull by design. The precise-term assertion is intact |

Three of the new title-leg tests failed on first run and were **right to fail**: with only 8 fixture titles the 10% document-frequency ceiling rounds to 0, so every term looked ubiquitous and the query emptied itself. That is a real defect on any small catalogue, and the fix is in the code (`_MIN_DF_CEILING = 25`), not in the test.

## 6. Retrieval

| Metric | Before | After |
| --- | --- | --- |
| Questions where any gold document was retrieved | 36 (41.9%) | 42 (48.8%) |
| Mean gold documents retrieved per question | 0.48 | 0.53 |
| Answers that used none of the retrieved chunks | 3 | 1 |

The gain is real but modest, and it is worth being precise about why. The three retrieval defects were genuine and are fixed, but retrieval feeds a **five-block context budget** (2 website + 2 PDF + 1 conditional). Surfacing the right page into the candidate pool does not guarantee a slot, and Q004 is the clean demonstration: the Centres of Excellence hub page is now in the pool and still does not reach context.

## 7. Generation

- Refusals and one-line deflections: **7 -> 6**.
- Answers emitting no citation at all: **3 -> 1**.
- Facts substantially covered: **97 -> 104** of 559.

Generation remains the largest single failure layer (45 of 86), and that is the honest reading: the model is given the authoritative page and still writes a summary that omits most of what the page says. Q053 is the cleanest example - the service node moved into block 1 after this pass and fact coverage did not move at all, because the answer still prefers the narrative material.

## 8. Graph retrieval

| Metric | Before | After |
| --- | --- | --- |
| Route outcomes (independent replay) | {'timed_out': 3, 'circuit_open': 83} | {'not_routed': 85, 'timed_out': 1} |
| Circuit breaker after replay | OPEN | CLOSED |
| Questions where the graph contributed | 0 | 0 |

**The deadlock is fixed. The graph still contributes to one question, and even that one is marginal.** This report will not blur those three facts together.

Fixed: the entity index warms on a background thread, a cold attempt *declines* in ~250 ms instead of burning the budget, declining does not count against the breaker, and the breaker stayed **CLOSED** across every replay. The baseline's `3 timed_out + 83 circuit_open` cannot recur.

Not fixed, and newly measured: **85 of the 86 questions are `not_routed`** - no template matches them, because this benchmark asks for narrative summaries of unstructured page text, which is not what a claim graph is for. That is a property of the question mix, not a defect. But the one routable question (Q002, `entity_timeline`, 11 rows) sits right on the budget. Executed five times in a row in one process it took **3036 ms (timed out), 1980 ms, 95 ms, 62 ms, 74 ms** - so there is a second cold cost beyond the entity index, in the driver or the Cypher plan cache, and a cold process loses its first routed query while a long-running server does not. The replay recorded in the results JSON is a cold process and records that timeout. The obvious next step is to have `prewarm_entity_index()` also execute one cheap warm-up query; that was not done in this pass.

Graph routing precision on the single positive is 1/1; recall is not estimable from one instance.

## 9. Temporal correctness

- Q002: coverage rose 0.484 -> 0.659 and the founder and the Pachauri tenure are now named, but the stale present-tense '**As of 2023 ... celebrating its 50th anniversary**' claim is still there in the graded run, and in one of three repeats. **The prompt-side temporal guard did not work.**
- Q097: past training programmes are no longer admitted as answers to an 'upcoming' question (context 6 blocks -> 3). The question still fails, for a different reason - the model refuses rather than stating the documented negative.
- Q110: unchanged behaviour, improved result - the ten most recent policy briefs in correct reverse-chronological order, coverage 0.514 -> 0.799.
- The gate is removal-only and fails safe, so it cannot manufacture a refusal.

## 10. Citations

| Metric | Before | After |
| --- | --- | --- |
| Answers with at least one gold-cited document | 28 | 33 |
| Gold citation alignment rate | 32.6% | 38.4% |
| Answers with no citation | 3 | 1 |
| Fabricated citations | 0 | 0 |

Every emitted citation still resolves to a real corpus document, and no fabricated citation was found in either run.

One new observation, worth recording because it is cheap to fix and embarrassing in production: **Q111 emits five citations attached to the sentence 'I don't have information on that in the available sources'** - and three of the five are the Annual Reports document, which is exactly what the question asked for. A refusal that ships sources contradicts itself in front of the user, and the sources it ships here show the refusal was wrong. Suppressing citations on the refusal path, or better, treating a refusal that has cited sources as a bug the pipeline can detect, is a small change this pass did not make.

## 11. Latency

| Percentile | Before | After | Change |
| --- | --- | --- | --- |
| mean | 9113 ms | 10029 ms | +916 ms |
| p50 | 9272 ms | 9869 ms | +597 ms |
| p90 | 10749 ms | 13044 ms | +2295 ms |
| p95 | 11306 ms | 14289 ms | +2984 ms |
| max | 14802 ms | 21215 ms | +6413 ms |

| Component | Before | After |
| --- | --- | --- |
| Mean time to first token | 6842 ms | 7521 ms |
| Mean generation time | 2270 ms | 2508 ms |

Two extra retrieval legs run **inside the existing thread pool**, so they cost the slower of the two rather than their sum, and the title leg caches the title table for 300 s. No timeout or budget was raised.

**This comparison is confounded and should not be quoted as a regression.** 41 of the 86 responses in the after run were collected immediately after the retrieval server recovered from a mid-run failure, on a machine that was also warming a 14 s entity-index load; the baseline run had a quiet machine throughout. The tail moved more than the median, which is the signature of load rather than of added work per request. An isolated measurement of the two new legs, rather than an end-to-end comparison across two differently-loaded runs, is what would settle the real cost - and this pass did not make one.

## 12. Question-level movement

Using an absolute change of 0.03 in per-question mean fact coverage: **23 improved, 15 regressed**, the rest flat.

**Improved** (coverage before -> after):

- Q002 0.484 -> 0.659 - Can you provide a brief history of The Energy and Resources Institute 
- Q007 0.289 -> 0.363 - What are TERI's major achievements and contributions to sustainable de
- Q011 0.248 -> 0.498 - What are TERI's latest research priorities?
- Q012 0.430 -> 0.463 - What is TERI's contribution to India's Net-Zero 2070 goal?
- Q040 0.071 -> 0.137 - What is green hydrogen and how is TERI working in this field?
- Q044 0.030 -> 0.094 - What is TERI's work on bioenergy and biofuels?
- Q049 0.228 -> 0.285 - What are TERI's initiatives in electric mobility and EV ecosystems?
- Q053 0.131 -> 0.179 - What climate risk assessment methodologies does TERI use?
- Q057 0.047 -> 0.464 - What research is TERI doing on climate finance and ESG?
- Q059 0.167 -> 0.263 - What are TERI's latest climate resilience projects?
- Q067 0.109 -> 0.139 - How does TERI work with local communities on forest conservation?
- Q068 0.067 -> 0.100 - What is TERI's role in watershed management projects?
- Q075 0.114 -> 0.166 - How does TERI support plastic waste management?
- Q080 0.771 -> 0.843 - What green building rating services does TERI provide,
- Q083 0.112 -> 0.412 - Does TERI provide Life Cycle Assessment (LCA) services?
- Q084 0.270 -> 0.309 - Can TERI assist in conducting an energy audit for my industrial facili
- Q085 0.000 -> 0.167 - What sustainability advisory services does TERI offer?
- Q086 0.378 -> 0.410 - What benefits can organizations gain from TERI's environmental design 
- Q091 0.016 -> 0.506 - Can TERI conduct air quality testing and monitoring?
- Q099 0.000 -> 0.333 - Are certificates awarded upon successful completion of TERI programmes
- Q102 0.227 -> 0.261 - What international training programmes are conducted by TERI?
- Q110 0.514 -> 0.799 - What policy briefs has TERI recently published?
- Q112 0.000 -> 0.041 - What publications are available on Sustainable Development Goals?

**Regressed:**

- Q001 0.465 -> 0.435 - What is the primary mission and vision of TERI?
- Q009 0.300 -> 0.245 - Does TERI offer internships, fellowships, or career opportunities for 
- Q010 0.150 -> 0.050 - How can I stay updated on TERI's activities and announcements?
- Q019 0.241 -> 0.000 - What are TERI's latest studies on air quality and pollution management
- Q021 0.143 -> 0.071 - How does TERI contribute to national missions and international climat
- Q023 0.217 -> 0.117 - What evidence-based policy tools has TERI developed?
- Q024 0.555 -> 0.472 - How is TERI supporting the implementation of Sustainable Development G
- Q035 0.079 -> 0.013 - What innovations and technologies are being demonstrated under ongoing
- Q046 0.222 -> 0.147 - What innovations is TERI developing for energy access?
- Q056 0.286 -> 0.190 - How does TERI address air pollution in Indian cities?
- Q069 0.283 -> 0.234 - What biodiversity conservation programmes does TERI implement?
- Q074 0.171 -> 0.071 - What research exists on waste-to-resource technologies?
- Q095 0.614 -> 0.574 - What analytical capabilities are available through TERI's testing labo
- Q096 0.159 -> 0.087 - What training programmes and workshops does TERI offer?
- Q111 0.385 -> 0.083 - Where can I download TERI's annual reports

Read this table against section 1b. Per-question movements below about 0.05 are inside the measured run-to-run noise of the pipeline, and the query-understanding step can produce a different facet filter - and therefore a different candidate pool - for the same question on two calls. What is trustworthy here is the direction of the aggregate and the retrieval-side measures, not any individual row.

## 13. Remaining failures, classified

| Class | Count | Meaning |
| --- | --- | --- |
| G | 44 | generation failure - the evidence was in context and the answer did not use it |
| R | 21 | retrieval failure - the authoritative evidence never reached context |
| Q+R | 3 | routing and retrieval - the wrong answer mechanism was applied |
| R+G | 2 | both - evidence partly reached context and was partly misused |
| G+C | 2 | generation, bounded by what the gold can be scored against |
| Q+G | 2 | routing and generation |
| Q | 1 | query understanding/routing |

| Layer | Before | After |
| --- | --- | --- |
| CITATION | 1 | 0 |
| CONTEXT_BUILDING | 2 | 3 |
| GENERATION | 39 | 45 |
| GRAPH_DATA | 1 | 1 |
| QDRANT_RETRIEVAL | 26 | 19 |
| QUERY_UNDERSTANDING | 1 | 1 |
| RANKING | 3 | 3 |
| SCOPE_HANDLING | 2 | 2 |
| TEMPORAL_INTERPRETATION | 2 | 1 |

| Severity | Before | After |
| --- | --- | --- |
| CRITICAL | 4 | 3 |
| HIGH | 9 | 8 |
| MEDIUM | 45 | 44 |
| LOW | 19 | 20 |

The one clear structural shift is `QDRANT_RETRIEVAL` 26 -> 19, matching the measured gain in gold document retrieval: seven questions no longer fail primarily because the evidence could not be found. `GENERATION` rose 39 -> 45 by exactly that mechanism - when retrieval stops being the first thing that fails, the next thing that fails becomes the answer. That is progress in diagnosis, not in outcome, and it is where the next pass should aim.

`TEMPORAL_INTERPRETATION` fell 2 -> 1 (Q097's false positive is gone; Q002's stale wording is not). `QUERY_UNDERSTANDING` is unchanged at 1 - Q079 is still misrouted to chitchat. `CONTEXT_BUILDING` rose 2 -> 3.

## 14. The ten worst remaining failures

### 1. Q079 - What technologies are available for waste valorization?

- **Verdict**: NO_ANSWER (baseline: NO_ANSWER) | **layer**: QUERY_UNDERSTANDING | **severity**: CRITICAL | **class**: query understanding/routing
- **Fact coverage**: 0.000 -> 0.000 | **gold docs retrieved**: 1 -> 1 | **admitted blocks**: 5 -> 5 | **chunks the answer used**: 0 -> 0
- NOT fixed. On the previous run this was classified qa and retrieved five blocks; on this run it is misrouted to chitchat again and deflects with zero context blocks and zero citations, exactly as at baseline - even though retrieval had surfaced the TERI enhanced acidification and methanation page, a gold document. Measured over three repeats the classifier said chitchat twice and qa once and answer length ranged from 227 to 1890 characters. The intent classifier is nondeterministic on this question and nothing in this pass addressed it.

### 2. Q004 - What are TERI's flagship initiatives and centres of excellence?

- **Verdict**: NO_ANSWER (baseline: NO_ANSWER) | **layer**: CONTEXT_BUILDING | **severity**: HIGH | **class**: retrieval failure
- **Fact coverage**: 0.000 -> 0.000 | **gold docs retrieved**: 0 -> 0 | **admitted blocks**: 5 -> 5 | **chunks the answer used**: 5 -> 5
- UNFIXED, and the largest single remaining defect. The title leg now resolves the Centres of Excellence hub page - which lists all nine centres - into the candidate pool, but RRF across four rankings plus the two-slot website cap in context admission keeps it out of the five admitted blocks. Those five are all individual centres (Mahindra-TERI, DBT, UTC, Mahindra Lifespaces) and the model refuses rather than answering partially from them. Left deliberately rather than tuned around one question.

### 3. Q019 - What are TERI's latest studies on air quality and pollution management?

- **Verdict**: NO_ANSWER (baseline: PARTIALLY_CORRECT) | **layer**: GENERATION | **severity**: HIGH | **class**: generation failure
- **Fact coverage**: 0.241 -> 0.000 | **gold docs retrieved**: 1 -> 1 | **admitted blocks**: 5 -> 5 | **chunks the answer used**: 5 -> 2
- REGRESSION. The baseline produced a grounded partial answer naming Delhi-NCR, Ludhiana and Patna (coverage 0.241); this run refuses. The cause moved: five blocks are retrieved including a gold document (the Explainer page, twice), and the model declines anyway. At baseline this was a retrieval shortfall; now the evidence is present and unused, which makes it the same class of failure as Q079 and Q111. Measured over three repeats it refuses twice and answers once, so the graded refusal is the majority behaviour rather than an unlucky sample.

### 4. Q082 - How can my company consult with TERI for carbon footprinting and ESG reporting?

- **Verdict**: NO_ANSWER (baseline: NO_ANSWER) | **layer**: QDRANT_RETRIEVAL | **severity**: HIGH | **class**: retrieval failure
- **Fact coverage**: 0.000 -> 0.000 | **gold docs retrieved**: 0 -> 0 | **admitted blocks**: 5 -> 5 | **chunks the answer used**: 5 -> 5
- UNFIXED. Five blocks are retrieved and all are TERI CBS-adjacent - the businesses portal, the CBS Knowledge Library and Archives, a best-practices item - but none of the eleven gold documents (the TERI CBS page, its member services, the GHG calculator service, the contact route) reaches context, and the model refuses. A commercial-enquiry question is exactly what a public-facing chatbot must answer.

### 5. Q093 - Does TERI offer soil testing and environmental analysis?

- **Verdict**: NO_ANSWER (baseline: NO_ANSWER) | **layer**: GENERATION | **severity**: HIGH | **class**: generation failure
- **Fact coverage**: 0.000 -> 0.000 | **gold docs retrieved**: 1 -> 1 | **admitted blocks**: 5 -> 5 | **chunks the answer used**: 5 -> 5
- NOT fixed. On the previous run of the same build this answered with coverage 0.562; on this run it refuses outright, with five blocks retrieved including the Air Quality Research service node. The corpus states plainly that TERI is NABL-accredited for testing water, soil and sludge. Measured over three repeats it refused all three times, so the earlier answered run was the outlier and this question is genuinely unfixed - the prompt change did not reach it.

### 6. Q111 - Where can I download TERI's annual reports

- **Verdict**: NO_ANSWER (baseline: PARTIALLY_CORRECT) | **layer**: GENERATION | **severity**: HIGH | **class**: generation failure
- **Fact coverage**: 0.385 -> 0.083 | **gold docs retrieved**: 0 -> 0 | **admitted blocks**: 5 -> 5 | **chunks the answer used**: 5 -> 5
- REGRESSION, and the worst one. The baseline answered - imprecisely, citing the CBS Knowledge Library rather than teriin.org/annual-reports - and this run refuses outright, although three of the five retrieved blocks are the Annual Reports document itself. Coverage 0.385 -> 0.083. A question with the answer sitting in the majority of its own context should never refuse. Measured over three repeats it answers twice and refuses once, so the graded refusal is the minority behaviour - this question is unstable rather than uniformly broken.

### 7. Q097 - Are there any upcoming TERI training programmes?

- **Verdict**: NO_ANSWER (baseline: NO_ANSWER) | **layer**: GENERATION | **severity**: MEDIUM | **class**: generation failure
- **Fact coverage**: 0.000 -> 0.000 | **gold docs retrieved**: 0 -> 0 | **admitted blocks**: 6 -> 6 | **chunks the answer used**: 6 -> 3
- The temporal gate worked and the failure moved. The baseline admitted six PAST training programmes (TERI-DST, TERI-ITEC 2013-15) as though they answered 'upcoming'; the gate removed half of them and three blocks remain. The model still refuses instead of stating the documented negative - no upcoming training programme is listed, and the only three future-dated events are the Darbari Seth Memorial Lecture, a UNCCD COP17 panel and a WCEF2026 session. Suppressing a false positive is not the same as answering a negative with evidence.

### 8. Q112 - What publications are available on Sustainable Development Goals?

- **Verdict**: INCORRECT (baseline: INCORRECT) | **layer**: RANKING | **severity**: CRITICAL | **class**: routing and retrieval
- **Fact coverage**: 0.000 -> 0.041 | **gold docs retrieved**: 1 -> 2 | **admitted blocks**: 5 -> 2 | **chunks the answer used**: 10 -> 10
- UNFIXED, deliberately deferred. Gold documents retrieved rose 1 -> 2 and the retrieval blocks are the correct Sustainable Development Goals page and 'India and Sustainable Development Goals', but the structured list still emits ten items with no SDG-publication relationship - an opinion piece on education, a children's science congress, a UNCCD panel.

### 9. Q119 - Which researchers work on AI and sustainability?

- **Verdict**: INCORRECT (baseline: INCORRECT) | **layer**: RANKING | **severity**: CRITICAL | **class**: routing and retrieval
- **Fact coverage**: 0.124 -> 0.124 | **gold docs retrieved**: 2 -> 2 | **admitted blocks**: 4 -> 4 | **chunks the answer used**: 10 -> 10
- UNFIXED, deliberately deferred. The retrieval blocks are now precisely the right ones - 'Artificial Intelligence in Climate...' and 'AI for Restoring Degraded Lands' - whose recorded authors, Dr Jitendra Vir Sharma and Mr Sayanta Ghosh, are the answer. The structured list path still names no person and returns the same unrelated items as Q112.

### 10. Q109 - Can you recommend reports on climate change adaptation?

- **Verdict**: INCORRECT (baseline: INCORRECT) | **layer**: RANKING | **severity**: HIGH | **class**: routing and retrieval
- **Fact coverage**: 0.000 -> 0.000 | **gold docs retrieved**: 0 -> 1 | **admitted blocks**: 5 -> 2 | **chunks the answer used**: 2 -> 2
- UNFIXED, deliberately deferred. A gold document is now retrieved ('Who is adapting and how?'), but the structured list path still lists by CMS bundle with no topical constraint and returns two off-topic reports. Correcting the list mechanism was held back because the same path produces Q110, the run's one complete structured success.

## 15. Against the acceptance criteria - including what was not met

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Canonical pages are retrievable | Partly met | Three real defects fixed and gold document retrieval moved 41.9% -> 48.8%. Q004 still fails: the hub page reaches the candidate pool and not the context. |
| 2 | No refusal when the evidence is in context | Partly met | Q083 (stable across three repeats) and Q099 stopped refusing. Q091 answers in the graded run but deflects on two of three repeats; Q093 refuses on all three. Seven questions still refuse or deflect in the graded run - Q004, Q019, Q079, Q082, Q093, Q097, Q111 - and Q019, Q079 and Q111 do so with the evidence in context, which is the worst kind. |
| 3 | Graph timeouts and the circuit breaker | Partly met | The deadlock is gone: a cold index declines in ~250 ms, declining does not count against the breaker, and the breaker stayed CLOSED. 85 of 86 are not_routed by question class. But the one routable question still exceeds the 3.0 s budget on the *first* execution in a cold process (3036 ms, then 1980 / 95 / 62 / 74 ms), so a second cold cost remains unaddressed. The budget was not raised. |
| 4 | `Claim.object_literal` mismatch | Met | `properties(c).object_literal` in both templates; verified warning-free with literal support preserved. |
| 5 | Temporal 'upcoming' | Partly met | Past events no longer answer an upcoming question (Q097 context 6 -> 3), but Q097 still refuses instead of stating the documented negative. |
| 6 | Stale present tense | **Not met** | Rule 9 now requires time-bound wording to be reported as of the source's date, and Q002 improved on other axes (0.484 -> 0.659, founder named). But the 'As of 2023 ... celebrating its 50th anniversary' sentence is present in the graded run and in one of three repeats. A prompt line did not solve this. |
| 7 | Structured/list collisions | **Not met - deliberately deferred** | Q025, Q035, Q109, Q112 and Q119 are unchanged. The mechanism is diagnosed (`list_records` lists by bundle with no topical constraint) and was not changed because the same path produces Q110, the run's one complete structured success. |
| 8 | Generation quality | Partly met | Facts substantially covered 97 -> 104; generation is still the largest failure layer at 45 of 86. |
| 9 | Graph + Qdrant hybrid preserved | Met | `if graph_blocks: return graph_blocks` was not reintroduced; `SEMANTIC_MIN_SLOTS = 2` is unchanged and graph rows merge with the semantic pull. |
| 10 | No hardcoding of the 86 questions | Met | No question text, id or expected answer appears in any source file. Every threshold is computed from the corpus (document frequency over titles) or is a bundle-level constant. |
| 11 | No timeout inflated to hide the problem | Met | The routing budget is still 3.0 s; the index load moved out of it. |
| 12 | No prompt that forces an answer | Met | The refusal path and the `REFUSAL` constant are unchanged. Rule 3 says a grounded partial answer beats a refusal; it does not say answer regardless of evidence. Seven questions still decline in the graded run - if the prompt were forcing answers there would be none - and the residual complaint about four of them is that they decline when they should not. |
| 13 | No test weakened to pass | Met | 2,901 -> 2,947 passing, 0 failing. Two tests were repointed at a renamed seam with assertions intact; three of my own new tests exposed a real code defect and the code was fixed, not the test. |
| 14 | The gold set was not changed | Met | `organization_121_gold.json` was last written at 17:10 on the run date, when the judgement pass froze v2 - before the baseline benchmark at 18:04 and before any code in this pass. No answer, expected fact or evidence definition was touched. |

### What this pass does not claim

- Not that the refusal rate fell: refusals and deflections went 7 -> 6, which is barely a move. Three refusals were recovered (Q083 stably, Q099 stably, Q091 intermittently) and two new ones appeared (Q019, Q111).
- Not that retrieval recall improved in the abstract: the number that matters is whether the *authoritative* source reached the answer, and it does so for 49% of questions, not for most.
- Not that more graph queries succeeded: one question is routed, and the reason the other 85 are not is the question mix.
- Not that answers got longer or better organised. Q096's graded answer is a clean, correctly formatted list of seven real TERI events with working URLs - and it is wrong, because the question asked about training programmes. Presentation improved nothing there.
- **11 of 86 answers are fully correct.** The system's dominant behaviour is still a fluent, grounded, partial answer built on secondary sources.

## Appendix - full results table

`Blocks` is admitted context / chunks the answer actually used.

| ID | Verdict (before -> after) | Layer | Sev | Facts | Gold docs | Cites (gold) | Blocks | Coverage before -> after | ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q001 | PARTIALLY_CORRECT | GENERATION | LOW | 2/4 | 1/1 | 4 (1) | 5/5 | 0.465 -> 0.435 | 15362 |
| Q002 | PARTIALLY_CORRECT | TEMPORAL_INTERPRETATION | MEDIUM | 6/8 | 1/3 | 2 (1) | 6/6 | 0.484 -> 0.659 | 10421 |
| Q003 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/5 | 1/2 | 4 (1) | 5/5 | 0.000 -> 0.000 | 11083 |
| Q004 | NO_ANSWER | CONTEXT_BUILDING | HIGH | 0/5 | 0/9 | 5 (0) | 5/5 | 0.000 -> 0.000 | 7792 |
| Q005 | PARTIALLY_CORRECT | CONTEXT_BUILDING | MEDIUM | 9/11 | 1/2 | 4 (1) | 5/5 | 0.788 -> 0.788 | 14581 |
| Q007 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 4/9 | 1/5 | 4 (1) | 5/5 | 0.289 -> 0.363 | 12019 |
| Q009 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 2/6 | 1/3 | 2 (1) | 5/5 | 0.300 -> 0.245 | 11453 |
| Q010 | PARTIALLY_CORRECT | CONTEXT_BUILDING | MEDIUM | 0/4 | 1/7 | 3 (0) | 5/5 | 0.150 -> 0.050 | 8381 |
| Q011 | PARTIALLY_CORRECT | GENERATION | LOW | 2/5 | 0/3 | 2 (0) | 5/5 | 0.248 -> 0.498 | 8856 |
| Q012 | PARTIALLY_CORRECT | GENERATION | LOW | 2/6 | 1/7 | 4 (1) | 5/5 | 0.430 -> 0.463 | 9709 |
| Q014 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/10 | 1/6 | 3 (1) | 5/5 | 0.075 -> 0.082 | 10143 |
| Q015 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | HIGH | 0/8 | 0/12 | 5 (0) | 5/5 | 0.086 -> 0.094 | 9747 |
| Q016 | CORRECT | - | - | 3/5 | 2/10 | 3 (2) | 5/5 | 0.420 -> 0.420 | 8400 |
| Q018 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/6 | 0/8 | 3 (0) | 5/5 | 0.048 -> 0.023 | 9648 |
| Q019 | **PARTIALLY_CORRECT -> NO_ANSWER** | GENERATION | HIGH | 0/7 | 1/9 | 2 (0) | 5/2 | 0.241 -> 0.000 | 7178 |
| Q020 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/9 | 1/9 | 3 (1) | 5/5 | 0.200 -> 0.184 | 10548 |
| Q021 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/7 | 1/8 | 3 (1) | 5/5 | 0.143 -> 0.071 | 10168 |
| Q023 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 2/10 | 0/12 | 2 (0) | 5/5 | 0.217 -> 0.117 | 10758 |
| Q024 | CORRECT | - | - | 3/6 | 1/6 | 4 (1) | 5/5 | 0.555 -> 0.472 | 9482 |
| Q025 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/4 | 0/0 | 10 (0) | 5/10 | 0.000 -> 0.000 | 4217 |
| Q027 | PARTIALLY_CORRECT | GRAPH_DATA | MEDIUM | 1/3 | 0/2 | 4 (0) | 5/5 | 0.307 -> 0.307 | 8841 |
| Q029 | PARTIALLY_CORRECT | GENERATION | LOW | 0/6 | 1/8 | 3 (1) | 5/5 | 0.042 -> 0.042 | 10620 |
| Q035 | **INCORRECT -> PARTIALLY_CORRECT** | QDRANT_RETRIEVAL | MEDIUM | 0/9 | 0/14 | 4 (0) | 4/4 | 0.079 -> 0.013 | 9071 |
| Q040 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/7 | 1/8 | 4 (1) | 5/5 | 0.071 -> 0.137 | 10113 |
| Q041 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 1/7 | 1/8 | 4 (1) | 5/5 | 0.071 -> 0.071 | 9532 |
| Q042 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/7 | 0/11 | 3 (0) | 5/5 | 0.000 -> 0.000 | 9944 |
| Q043 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 3/8 | 0/17 | 3 (0) | 5/5 | 0.188 -> 0.188 | 9431 |
| Q044 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/9 | 0/16 | 5 (0) | 5/5 | 0.030 -> 0.094 | 10420 |
| Q045 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/6 | 0/8 | 3 (0) | 5/5 | 0.098 -> 0.123 | 11850 |
| Q046 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/6 | 0/11 | 3 (0) | 5/5 | 0.222 -> 0.147 | 9136 |
| Q048 | PARTIALLY_CORRECT | GENERATION | LOW | 0/6 | 0/7 | 4 (0) | 5/5 | 0.055 -> 0.055 | 11197 |
| Q049 | PARTIALLY_CORRECT | GENERATION | LOW | 1/6 | 0/11 | 4 (0) | 5/5 | 0.228 -> 0.285 | 11495 |
| Q050 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 2/5 | 0/10 | 4 (0) | 5/5 | 0.400 -> 0.400 | 8528 |
| Q051 | PARTIALLY_CORRECT | GENERATION | LOW | 1/7 | 2/10 | 5 (2) | 5/5 | 0.137 -> 0.157 | 14461 |
| Q052 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/7 | 0/10 | 4 (0) | 5/5 | 0.187 -> 0.200 | 9869 |
| Q053 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/7 | 1/8 | 4 (0) | 5/5 | 0.131 -> 0.179 | 10654 |
| Q055 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/6 | 0/6 | 3 (0) | 5/5 | 0.222 -> 0.222 | 11259 |
| Q056 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/7 | 1/11 | 3 (1) | 5/5 | 0.286 -> 0.190 | 10410 |
| Q057 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 3/7 | 1/11 | 3 (1) | 5/5 | 0.047 -> 0.464 | 9609 |
| Q058 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/7 | 0/10 | 4 (0) | 5/5 | 0.104 -> 0.116 | 9135 |
| Q059 | PARTIALLY_CORRECT | GENERATION | LOW | 1/6 | 1/9 | 2 (1) | 2/2 | 0.167 -> 0.263 | 8802 |
| Q060 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/8 | 0/12 | 4 (0) | 5/5 | 0.050 -> 0.050 | 9766 |
| Q061 | PARTIALLY_CORRECT | GENERATION | LOW | 0/7 | 1/11 | 5 (1) | 5/5 | 0.000 -> 0.000 | 14289 |
| Q062 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/8 | 0/14 | 2 (0) | 5/5 | 0.133 -> 0.138 | 13957 |
| Q063 | PARTIALLY_CORRECT | GENERATION | LOW | 2/7 | 0/13 | 5 (0) | 5/5 | 0.267 -> 0.277 | 11208 |
| Q064 | PARTIALLY_CORRECT | GENERATION | LOW | 1/8 | 0/13 | 5 (0) | 5/5 | 0.139 -> 0.122 | 14264 |
| Q065 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 2/7 | 0/12 | 4 (0) | 5/5 | 0.251 -> 0.251 | 11853 |
| Q066 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/8 | 1/13 | 3 (0) | 5/5 | 0.108 -> 0.094 | 9790 |
| Q067 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 1/7 | 0/14 | 2 (0) | 5/5 | 0.109 -> 0.139 | 13044 |
| Q068 | PARTIALLY_CORRECT | GENERATION | LOW | 1/6 | 1/12 | 3 (1) | 5/5 | 0.067 -> 0.100 | 11780 |
| Q069 | PARTIALLY_CORRECT | GENERATION | LOW | 1/7 | 0/14 | 5 (0) | 5/5 | 0.283 -> 0.234 | 12663 |
| Q070 | PARTIALLY_CORRECT | GENERATION | LOW | 0/6 | 1/10 | 3 (0) | 5/5 | 0.100 -> 0.100 | 10600 |
| Q071 | PARTIALLY_CORRECT | SCOPE_HANDLING | MEDIUM | 0/7 | 0/13 | 2 (0) | 5/5 | 0.080 -> 0.080 | 13802 |
| Q073 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/7 | 0/12 | 2 (0) | 5/5 | 0.031 -> 0.031 | 21215 |
| Q074 | PARTIALLY_CORRECT | GENERATION | LOW | 0/7 | 1/13 | 5 (1) | 5/5 | 0.171 -> 0.071 | 10569 |
| Q075 | PARTIALLY_CORRECT | GENERATION | LOW | 1/7 | 1/9 | 3 (1) | 5/5 | 0.114 -> 0.166 | 10162 |
| Q076 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/8 | 0/15 | 3 (0) | 5/5 | 0.181 -> 0.198 | 12266 |
| Q077 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/7 | 0/14 | 5 (0) | 5/5 | 0.167 -> 0.167 | 11312 |
| Q079 | NO_ANSWER | QUERY_UNDERSTANDING | CRITICAL | 0/8 | 1/13 | 0 (0) | 5/0 | 0.000 -> 0.000 | 8347 |
| Q080 | CORRECT | - | - | 6/7 | 1/6 | 4 (1) | 5/5 | 0.771 -> 0.843 | 10101 |
| Q082 | NO_ANSWER | QDRANT_RETRIEVAL | HIGH | 0/8 | 0/11 | 5 (0) | 5/5 | 0.000 -> 0.000 | 8837 |
| Q083 | **NO_ANSWER -> CORRECT** | - | - | 2/6 | 0/10 | 2 (0) | 5/5 | 0.112 -> 0.412 | 9019 |
| Q084 | CORRECT | - | - | 1/7 | 1/6 | 4 (1) | 5/5 | 0.270 -> 0.309 | 9057 |
| Q085 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 1/3 | 0/31 | 2 (0) | 5/5 | 0.000 -> 0.167 | 9908 |
| Q086 | CORRECT | - | - | 1/5 | 1/4 | 3 (1) | 5/5 | 0.378 -> 0.410 | 11265 |
| Q088 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/6 | 0/10 | 3 (0) | 5/5 | 0.080 -> 0.075 | 10530 |
| Q089 | PARTIALLY_CORRECT | GENERATION | LOW | 2/7 | 0/13 | 2 (0) | 5/5 | 0.423 -> 0.394 | 9680 |
| Q090 | CORRECT | - | - | 4/5 | 0/6 | 3 (0) | 5/5 | 0.574 -> 0.574 | 8886 |
| Q091 | **NO_ANSWER -> CORRECT** | - | - | 3/5 | 1/4 | 5 (1) | 5/5 | 0.016 -> 0.506 | 9423 |
| Q092 | CORRECT | - | - | 3/5 | 1/7 | 3 (1) | 5/5 | 0.474 -> 0.460 | 8729 |
| Q093 | NO_ANSWER | GENERATION | HIGH | 0/4 | 1/7 | 5 (1) | 5/5 | 0.000 -> 0.000 | 8363 |
| Q095 | CORRECT | - | - | 4/5 | 1/7 | 3 (0) | 5/5 | 0.614 -> 0.574 | 8907 |
| Q096 | **PARTIALLY_CORRECT -> INCORRECT** | SCOPE_HANDLING | HIGH | 1/7 | 0/10 | 10 (1) | 5/10 | 0.159 -> 0.087 | 4216 |
| Q097 | NO_ANSWER | GENERATION | MEDIUM | 0/5 | 0/4 | 3 (0) | 6/3 | 0.000 -> 0.000 | 9003 |
| Q098 | PARTIALLY_CORRECT | GENERATION | MEDIUM | 0/6 | 1/9 | 2 (0) | 5/5 | 0.070 -> 0.070 | 8616 |
| Q099 | **NO_ANSWER -> PARTIALLY_CORRECT** | GENERATION | LOW | 2/3 | 1/5 | 1 (1) | 5/5 | 0.000 -> 0.333 | 7815 |
| Q100 | PARTIALLY_CORRECT | GENERATION | LOW | 0/8 | 0/13 | 3 (0) | 5/5 | 0.095 -> 0.095 | 9306 |
| Q102 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 2/7 | 0/12 | 3 (0) | 5/5 | 0.227 -> 0.261 | 10750 |
| Q107 | PARTIALLY_CORRECT | GENERATION | LOW | 1/5 | 1/6 | 2 (1) | 5/5 | 0.206 -> 0.206 | 8794 |
| Q109 | INCORRECT | RANKING | HIGH | 0/5 | 1/9 | 2 (0) | 2/2 | 0.000 -> 0.000 | 4514 |
| Q110 | CORRECT | - | - | 6/7 | 0/12 | 10 (10) | 6/10 | 0.514 -> 0.799 | 4969 |
| Q111 | **PARTIALLY_CORRECT -> NO_ANSWER** | GENERATION | HIGH | 0/4 | 0/2 | 5 (0) | 5/5 | 0.385 -> 0.083 | 6809 |
| Q112 | INCORRECT | RANKING | CRITICAL | 0/8 | 2/14 | 10 (0) | 2/10 | 0.000 -> 0.041 | 4747 |
| Q113 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/6 | 0/7 | 2 (0) | 4/4 | 0.000 -> 0.000 | 11055 |
| Q119 | INCORRECT | RANKING | CRITICAL | 0/5 | 2/7 | 10 (0) | 4/10 | 0.124 -> 0.124 | 4466 |
| Q121 | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | 0/6 | 0/12 | 2 (0) | 5/5 | 0.000 -> 0.000 | 9528 |

## Quality check

- QC problems: none
- 86 questions, each evaluated once: True
- Answers read in full before verdicting: 43; verdicts inherited from the baseline: 43. a baseline verdict was kept only where fact coverage moved by less than 0.06 against both the baseline and the intermediate run, chunks used moved by fewer than 2, and the gold-document count was unchanged; every question outside that envelope was re-read in full.
- Zero system errors, zero timeouts, zero malformed SSE responses across 86 requests.
- Raw transcripts, per-question measurements and the graph replay are in `organization_121_chatbot_fix_results.json`.

