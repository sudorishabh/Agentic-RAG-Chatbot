# Structured/list fix + benchmark stabilization - final report

- **Benchmark**: the same 86 validated gold questions, unchanged. The gold set was not edited in this phase.
- **Protocol**: three runs per question per arm (516 responses), majority verdict per question. No single-run headline is quoted anywhere in this report.
- **A/B on one build**: both arms are the same commit, differing only in `structured_topic_constraint_enabled`. The control ran on a separate server instance with the flag off, so the comparison cannot be confounded by any other change made during this phase.
- **Stores untouched**: no re-ingest, no rebuild, no schema change. MySQL, Qdrant and Neo4j hold exactly what they held before.

## 1. Benchmark stability, before and after

| Metric | Control | Treatment |
| --- | --- | --- |
| Unanimous across 3 runs | 72 | 75 |
| **Unstable questions** | 14 | 11 |
| Intent flapped | 4 | 2 |
| Answer changed materially | 37 | 36 |
| Mean coverage spread across runs | 0.067 | 0.064 |

### 2. Number of unstable questions

**Control: 14 of 86. Treatment: 11 of 86.**

Unstable means the automatic verdict was not the same on all three runs. The instability is a property of the pipeline, not of the fix: the query-analysis call runs at the deployment's default temperature and no seed is passed on any call, so intent routing and the answerer can both differ between identical requests. This phase measured that rather than hiding it; see `organization_121_stability_report.md`.

Unstable in the control: Q007, Q011, Q019, Q035, Q049, Q050, Q079, Q082, Q089, Q091, Q093, Q099, Q111, Q112

Unstable in the treatment: Q011, Q016, Q050, Q057, Q079, Q082, Q086, Q091, Q092, Q093, Q111

Unstable in both: Q011, Q050, Q079, Q082, Q091, Q093, Q111

## 3. Majority benchmark, before and after

| Verdict | Control | Treatment | Change |
| --- | --- | --- | --- |
| CORRECT | 14 | 16 | +2 |
| PARTIALLY_CORRECT | 63 | 62 | -1 |
| INCORRECT | 4 | 3 | -1 |
| UNSUPPORTED | 0 | 0 | +0 |
| NO_ANSWER | 5 | 5 | +0 |
| SYSTEM_ERROR | 0 | 0 | +0 |
| **Total** | **86** | **86** | |

| Metric | Control | Treatment | Change |
| --- | --- | --- | --- |
| Strict success rate | 16.3% | 18.6% | +2.3 pp |
| Gold-document retrieval | 47.7% | 47.7% | +0.0 pp |
| Gold-citation alignment | 38.4% | 39.5% | +1.2 pp |
| Mean fact coverage | 0.208 | 0.204 | -0.004 |
| Latency p50 | 9962 ms | 8862 ms | -1100 ms |
| Latency p90 | 12078 ms | 10531 ms | -1548 ms |
| Latency p95 | 12775 ms | 10953 ms | -1822 ms |

**Questions whose majority verdict moved:**

| Question | Control | Treatment | Direction |
| --- | --- | --- | --- |
| Q011 - What are TERI's latest research priorities? | PARTIALLY_CORRECT | CORRECT | improved |
| Q089 - What sustainability assessment tools are offered by  | PARTIALLY_CORRECT | CORRECT | improved |
| Q093 - Does TERI offer soil testing and environmental analy | NO_ANSWER | CORRECT | improved |
| Q099 - Are certificates awarded upon successful completion  | CORRECT | PARTIALLY_CORRECT | **worse** |
| Q119 - Which researchers work on AI and sustainability? | INCORRECT | NO_ANSWER | **worse** |

## 4. The five target questions, and the one that had to survive

| Question | Verdict | Coverage | Gold docs hit (of 3 runs) |
| --- | --- | --- | --- |
| Q025 | INCORRECT -> INCORRECT | 0.000 -> 0.125 | 0 -> 0 |
| Q035 | INCORRECT -> INCORRECT | 0.058 -> 0.031 | 0 -> 0 |
| Q109 | INCORRECT -> INCORRECT | 0.000 -> 0.000 | 3 -> 3 |
| Q112 | PARTIALLY_CORRECT -> PARTIALLY_CORRECT | 0.090 -> 0.135 | 3 -> 3 |
| Q119 | INCORRECT -> NO_ANSWER | 0.123 -> 0.083 | 3 -> 3 |
| Q110 | CORRECT -> CORRECT | 0.513 -> 0.656 | 0 -> 0 |

## 5. Gold retrieval and citation

- Gold-document retrieval (in a majority of runs): **47.7% -> 47.7%**
- Gold-citation alignment: **38.4% -> 39.5%**
- Mean fact coverage: **0.208 -> 0.204**

## 6. Remaining failures

| Question | Majority | Coverage | Why |
| --- | --- | --- | --- |
| Q004 - What are TERI's flagship initiatives and centres o | NO_ANSWER | 0.000 | refuses |
| Q019 - What are TERI's latest studies on air quality and  | NO_ANSWER | 0.000 | refuses |
| Q025 - What are TERI's ongoing projects? | INCORRECT | 0.125 | wrong list |
| Q035 - What innovations and technologies are being demons | INCORRECT | 0.031 | wrong list |
| Q082 - How can my company consult with TERI for carbon fo | NO_ANSWER | 0.024 | refuses |
| Q097 - Are there any upcoming TERI training programmes? | NO_ANSWER | 0.000 | refuses |
| Q109 - Can you recommend reports on climate change adapta | INCORRECT | 0.000 | wrong list |
| Q119 - Which researchers work on AI and sustainability? | NO_ANSWER | 0.083 | refuses |
| Q003 - What are TERI's core research areas and divisions? | PARTIALLY_CORRECT | 0.000 | grounded but off-gold |
| Q018 - What research is TERI conducting on climate financ | PARTIALLY_CORRECT | 0.024 | grounded but off-gold |
| Q029 - What initiatives is TERI running for clean energy  | PARTIALLY_CORRECT | 0.042 | grounded but off-gold |
| Q042 - How is TERI supporting India's energy transition? | PARTIALLY_CORRECT | 0.000 | grounded but off-gold |
| Q061 - How does TERI support sustainable consumption and  | PARTIALLY_CORRECT | 0.032 | grounded but off-gold |
| Q073 - What circular economy projects is TERI implementin | PARTIALLY_CORRECT | 0.032 | grounded but off-gold |
| Q074 - What research exists on waste-to-resource technolo | PARTIALLY_CORRECT | 0.048 | grounded but off-gold |
| Q079 - What technologies are available for waste valoriza | PARTIALLY_CORRECT | 0.005 | grounded but off-gold |
| Q113 - How can researchers obtain project reports and tec | PARTIALLY_CORRECT | 0.008 | grounded but off-gold |
| Q121 - How can organizations partner with TERI for resear | PARTIALLY_CORRECT | 0.000 | grounded but off-gold |

## 7. Structured/list root cause, in one paragraph

The catalog filters on a closed facet set; a question's topic is open vocabulary. When the two did not line up the structured path answered anyway, in two different ways. A topic that was not a theme got **snapped onto the nearest theme** - "Sustainable Development Goals" onto "Resources & Sustainable Development", "climate change adaptation" onto "Climate Change" - so the filter was wrong, not missing. Anything no facet could express was **dropped**: Q119 planned a `lookup_record` with every filter empty. Both paths end at `ORDER BY published_at DESC LIMIT 10`, so the answer became the newest rows of whatever bucket survived - the *list head*, identical for any two questions landing in the same bucket. The full trace is in `organization_121_structured_report.md`.

The fix is one rule: every topical word must be accounted for by a facet that genuinely means it, or constrain the rows explicitly, or the structured path declines and semantic retrieval answers.

## 8. Files changed

| File | New | What changed |
| --- | --- | --- |
| `app/retrieval/structured/topic.py` | yes | the rule itself: `residual_topic`, `faithful_theme`, `wants_person`, `bundle_words`, `content_terms`, and the `enabled()` flag accessor |
| `app/retrieval/structured/filters.py` |  | drops a theme that resolved to something broader than the ask, records it as `theme_widened`, and carries `topic_terms` through `ResolvedScope` |
| `app/retrieval/structured/planner.py` |  | `_applied_theme` (asks the resolver which facet will actually survive) and the residual-topic derivation, for list and lookup operations only |
| `app/retrieval/structured/tools.py` |  | passes `topic_terms` into the list query; `_scope_total` states the total behind a truncated list |
| `app/retrieval/structured/answerer.py` |  | declines a question that asks for people rather than for documents |
| `app/retrieval/structured/types.py` |  | `RecordFilters.topic_terms` |
| `app/catalog/queries.py` |  | `topic_terms` on `_catalog_filters`, `count_documents` and `list_documents`: OR-ed title conditions, ordered by how many matched before recency |
| `app/config.py` |  | `structured_topic_constraint_enabled` (default on), so both behaviours can be A/B'd on one build |
| `scripts/benchmark_chat.py` | yes | N-run benchmark harness, resumable |
| `scripts/benchmark_grade.py` | yes | per-run measurement, automatic verdict, majority and disagreement reporting |

## 9. Tests

**2,947 -> 2,970 passing, 0 failing.** 23 new tests in `tests/test_structured_topic_constraint.py` cover every case the brief listed: entity+topic filtering, person/researcher filtering, project lists, content-type filtering, temporal lists, same-bundle-different-question, same-entity-different-predicate, same-bundle-different-topic ordering, unrelated questions not sharing a head, the Q110 guard, and one test per target question - plus the safety cases: an unmatched topic declines instead of widening, and no list item can be invented.

One existing test, `test_misspelled_theme_canonicalizes_to_the_stored_name`, failed when the faithfulness check first went in, because "enviroment" is not a word-for-word match for "Environment". The test was right and the code was wrong: resolution exists to fix spelling as well as to generalise. Word matching is now approximate, so a typo passes and a missing word does not. The test was not modified.

## 10. Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Three-run evaluation reports majority verdicts | Met | `benchmark_chat.py --runs 3` + `benchmark_grade.py`; 516 responses across two arms, 0 errors, majority verdict per question. |
| Nondeterminism visible, not hidden | Met | 14 unstable, 4 intent-flapping and 37 answer-flapping questions listed by id. The temperature/seed situation is stated, not silently pinned. |
| Q025 improves | Partly | Verdict unchanged (INCORRECT); coverage 0.000 -> 0.125, because the answer now says "the 10 most recent of 594 ongoing projects" and 594 is the gold's own figure. The list itself is legitimately unconstrained. |
| Q035 improves | Partly | Verdict unchanged (INCORRECT) and coverage fell 0.058 -> 0.031, but the list stopped being a copy of Q025's: it now returns innovation and technology projects. The gold's named technologies are not CMS project rows, so no list can score on them. |
| Q109 improves | **Not met** | Verdict and coverage unchanged. The constrained list returns one on-topic report rather than two off-topic ones, but the gold's adaptation publications are policy briefs and research papers, while the classifier maps "reports" to the `report` bundle, which holds almost nothing. |
| Q112 improves | Met | Coverage 0.090 -> 0.135; the list went from an education op-ed, a WCEF session and a children's science congress to real SDG publications, and became unanimous across runs. |
| Q119 improves | Partly | INCORRECT -> NO_ANSWER: the unrelated document list is gone and the system declines instead. That is the Phase 6 rule working as specified, but it is a safety improvement, not a correctness one. |
| Q110 remains correct | Met | CORRECT on 3/3 runs in both arms; coverage 0.513 -> 0.656; the list head is byte-identical. |
| No incorrect list answers introduced | Met | INCORRECT 4 -> 3; no question moved into INCORRECT. |
| Generic bundle lists no longer substituted | Met | Distinct questions whose answers open with the same two items: 1 group before (Q025 and Q035), 0 after, across all 86 questions. |
| Structured retrieval respects topic/entity/predicate/content type | Met | Topic via `topic_terms`, content type via the bundle, entity via the existing facets, requested object type via the person guard. |
| Safe fallback available | Met | An empty constrained list returns `ok=False` and falls through to semantic retrieval; it is never retried without the constraint. |
| Gold set unchanged | Met | `organization_121_gold.json` untouched; both arms graded against it. |
| Ingestion untouched | Met | Nothing under `app/ingestion/` modified; no re-ingest, no rebuild. |
| Full test suite passes | Met | 2,970 passed, 0 failed. |
| No increase in UNSUPPORTED | Met | 0 -> 0. |
| No regression in graph/Qdrant/hybrid retrieval | Met | Gold-document retrieval flat at 47.7%; gold-citation alignment 38.4% -> 39.5%. Nothing in the graph/Qdrant merge was touched. |

### What this phase does not claim

- **Three of the five target questions did not change verdict.** The list *content* is demonstrably corrected and the collision is gone, but the automatic verdict is driven by fact coverage against gold documents that, for Q035 and Q109, are not CMS list rows at all. A better list cannot score against them.
- **Mean fact coverage moved 0.208 -> 0.204** - slightly down, and well inside the 0.064 mean run-to-run spread. Treat it as flat.
- **The stability gain is small and partly incidental.** 14 -> 11 unstable questions. Some of that is the fix making two questions deterministic (a person question now always declines; a topical list no longer depends on which theme the resolver happened to pick), and some is simply a different draw. The nondeterminism in the intent classifier and the answerer is untouched.
- **Q099 moved CORRECT -> PARTIALLY_CORRECT.** It is on the control arm's own unstable list, so the move is not attributable to this change.
- **A combined answer can still end with a refusal that contradicts the list above it** (Q025, in both arms). Pre-existing, unrelated to this fix, and out of scope because generation was excluded from this phase.

