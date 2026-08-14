# Phase 11 — controlled graph routing

Graph routing is **on**, for four measured query classes and nothing else. The
existing retrieval system is unchanged and remains the fallback for every other
question and for every graph outcome that is not a useful answer.

```
graph_routing_enabled   = true      <- the kill switch
graph_routing_classes   = current_funding, leadership, multi_hop, funders_of_project
graph_routing_budget    = 3.0s
graph_shadow_enabled    = false     (preserved, unchanged)
```

---

## 1. Before / after

24-query benchmark, `k=8`. "routed" is the shipped system: graph for enabled
classes, existing retrieval for everything else and for every fallback.

| class | n | existing | **routed** | graph used | routed ms |
|---|---:|---:|---:|---:|---:|
| current_funding | 4 | 0.00 | **1.00** | 4/4 | 62 |
| leadership | 3 | 0.06 | **1.00** | 3/3 | 39 |
| multi_hop | 3 | 0.03 | **1.00** | 3/3 | 36 |
| funders_of_project | 3 | 0.67 | **1.00** | 2/3 | 222 |
| historical | 3 | 0.00 | 0.00 | 0/3 | 667 |
| no_result | 2 | 1.00 | 1.00 | 0/2 | 626 |
| non_relational | 5 | 1.00 | 1.00 | 0/5 | 592 |
| ambiguous | 1 | 1.00 | 1.00 | 0/1 | 599 |

```
enabled classes (n=13)   coverage 0.174 -> 1.000     latency 813ms -> 88ms
other classes   (n=11)   coverage 0.727 -> 0.727     (untouched)
all queries     (n=24)   coverage 0.428 -> 0.875
regressions                                          none
```

**No query got worse.** The classes that are not routed are byte-identical to
before, because nothing in their path changed.

### Routing precision and recall

```
precision 1.00      no false routes: every non-relational and ambiguous
                    question was declined
recall    0.94      one miss, funder-02
template  23/24 correct
```

`funder-02` is *"A stakeholder forum for key actors in the electricity
distribution sector (Phase-2)"*, which Phase 4's `v_project_name_not_specific`
veto rejects as a descriptive phrase rather than a name. It falls back, existing
retrieval answers it at 1.00, and the class still scores 1.00 overall — which is
the fallback doing exactly its job. Extraction v1.1 is unchanged.

### Graph / fallback rates

```
answered        12 / 24    the graph answered
not_routed       7 / 24    not a graph-shaped question
class_disabled   5 / 24    3 historical + 2 employment, both deliberately off
zero_result      0 / 24    (exercised separately; see §4)
failed           0 / 24
```

---

## 2. `funders_of_project` — the class Phase 10 left open

Phase 10 measured it as a tie (0.67 both ways) and recommended against it. That
judged **graph alone**; production has a fallback. Measured both ways:

| enabled classes | routed coverage | routed latency |
|---|---:|---:|
| current_funding, leadership, multi_hop | 0.67 | 761 ms |
| …+ funders_of_project | **1.00** | **368 ms** |

The graph answers 2 of 3; the third declines and existing retrieval covers it.
The combination is strictly better than either alone, on both quality and
latency. **Enabled.**

This is the general lesson: a class is worth routing when *graph-or-fallback*
beats existing retrieval, not when the graph alone does.

---

## 3. Production behaviour

```
query
  ↓ pinned scope (filters / source_type)? ──yes──> existing retrieval
  ↓ no
deterministic router
  ├── not graph-shaped ──────────────────────────> existing retrieval
  ├── class not enabled ─────────────────────────> existing retrieval
  └── enabled class
        ↓
      traverse + hydrate
        ├── useful result ───────────> graph context
        ├── zero results ────────────> existing retrieval
        ├── error ───────────────────> existing retrieval
        └── over budget ─────────────> existing retrieval
```

A **pinned scope skips the graph entirely**: the graph applies neither `filters`
nor `source_type`, so answering from it would quietly discard a restriction the
caller asked for.

`_try_graph` returns `[]` for every outcome that is not a useful answer, and
`retrieve` carries on. One test parametrizes all seven non-answer outcomes and
asserts the fallback for each.

---

## 4. Zero result is not failure

Both fall back, so a user cannot tell them apart — but an operator must. A
`ZERO_RESULT` is the graph correctly reporting the corpus knows of no such
relationship; a `FAILED` is the graph being unable to say. Counting them together
would let Neo4j degrade silently behind a fallback that keeps working.

Verified live, with `employment` temporarily enabled so the zero-result path is
reachable:

```
zero_result   used=False rows=0   Which organisation does Mr R Suresh work at?
answered      used=True  rows=20  What projects are funded by DBT?
not_routed    used=False rows=0   What are the environmental impacts of solar energy?
not_routed    used=False rows=0   What projects are funded by TERI?
```

Eight distinct outcomes are counted: `answered`, `zero_result`, `no_evidence`,
`failed`, `timed_out`, `not_routed`, `class_disabled`, `circuit_open`. Metrics
land in the existing registry (`app.observability.metrics`) and appear under
`events` in `GET /metrics/timings`, per family and per class.

Only `failed` and `timed_out` count as the graph being broken — a zero result is
the graph working.

---

## 5. Neo4j failure cannot take `/chat` down — or make it slow

Verified against an unreachable Neo4j (`bolt://127.0.0.1:9`):

```
query0: blocks=5   6711ms    failed
query1: blocks=5   2888ms    failed
query2: blocks=5   2741ms    failed
query3: blocks=5    569ms    circuit_open
query4: blocks=5    660ms    circuit_open
query5: blocks=5    666ms    circuit_open
```

Every query answered. Falling back keeps `/chat` **available**, but the first
three still paid ~2.3–2.7 s for a doomed attempt, so availability alone was not
enough. A **circuit breaker** opens after 3 consecutive failures and skips the
graph for 60 s; latency returns to baseline (569 ms vs 666 ms normal). Any
success closes it. A zero result never trips it.

The 3 s budget is enforced independently, on a worker thread — measured firing at
exactly 3013 ms when the driver hung rather than refused.

---

## 6. A performance defect found while measuring

Enabling routing initially cost **+82 ms on every non-routing query**. The cause
was not routing, which takes 0.4 ms: `EntityIndex.load()` rebuilds from MySQL on
every call, and the routing path called it **twice per query** — once to decide,
once to answer.

That is correct for ingestion, which must see entities seeded moments earlier,
and ruinous for retrieval. The index is now cached at the retrieval boundary with
a 300 s TTL and shared between the routing probe and the answer, leaving
ingestion's fresh read untouched. Phases 9 and 10 never saw this because the eval
harness always passed an index explicitly; production does not.

```
declined attempt   0.43 ms
non-routing query  routing off 585ms  |  routing on 579ms   (interleaved, n=18)
```

No measurable overhead on queries that do not route. Routed-class latency fell
from 813 ms to 88 ms — a ~9× improvement, most of it this fix.

---

## 7. Graph answers still carry their provenance

Unchanged from Phase 10 and re-asserted by tests: verified structured rows, the
`claim_id` on each, the validity window, current-vs-historical mode, a
`[DISPUTED]` marker where applicable, document references, and Qdrant evidence
where it exists.

For CMS-field claims **no text quote is fabricated**. The structured fact is
stated as what it is — a recorded relationship with a validity window and a
claim id — and the document is cited beside it. When hydration returns nothing,
the facts block still stands alone rather than inventing a passage to sit under.

---

## 8. Tests

```
pytest tests/test_graph_routing.py -q   ->   42 passed
pytest -q                               -> 1864 passed, 0 failed
```

`tests/test_graph_routing.py` is new. It covers the kill switch, class
enable/disable, unknown class names failing closed, every outcome falling back,
zero-result versus failure, the budget, the circuit breaker opening/closing/not
tripping on zero results, per-class metrics, a metrics backend failure not
breaking routing, pinned scopes skipping the graph, and the index cache being
loaded once and shared.

Shadow instrumentation is preserved and still tested
(`tests/test_graph_shadow.py`, 24 tests).

---

## 9. The kill switch

```bash
GRAPH_ROUTING_ENABLED=false      # complete rollback, no restart logic needed
```

With it false no query is answered from the graph, whatever the class list says,
and the graph package is not imported on the request path. Nothing else has to
be undone, because existing retrieval was never replaced — only bypassed for
four classes with evidence.

Narrower options, without a full rollback:

```bash
GRAPH_ROUTING_CLASSES=current_funding,multi_hop   # drop a class
GRAPH_ROUTING_BUDGET_SECONDS=1.0                  # tighten the budget
```

---

## 10. Open questions

**1. Historical stays in probation.** 0.83 coverage on three queries is a signal,
not a mandate. Those questions currently get existing retrieval's 0.00 — the
honest cost of waiting for a larger reviewed historical benchmark, and the
clearest remaining win.

**2. 24 queries is a small benchmark**, seeded from the best-populated entities.
Shadow mode remains available for live traffic, and `novel_documents` is still
the number to watch.

**3. Answer coverage is a proxy.** It measures what reached the prompt, not what
the model does with it. No answer-level judging has been done.

**4. Under-merging still under-reports.** The Phase 7.2 audit found 60 name-order
variant groups, so one person can be several `:Person` nodes.

**5. `zero_result` is untested on live traffic** because both classes that
produce it are disabled. It is exercised by tests and by the manual check in §4.
