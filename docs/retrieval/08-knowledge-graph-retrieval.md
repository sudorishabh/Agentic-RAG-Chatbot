# 08 — Knowledge Graph Retrieval

**Purpose.** Answer relational questions ("who leads projects funded by X",
"who has DBT partnered with", "the history of Project Y") from verified
Neo4j claims instead of vector search, with every row traceable back to the
document that supported it.

**Inputs.** A question, and (from query understanding / the pipeline's scope)
the filters and source-type pin a query already carries.

**Outputs.** A `ContextBlock` list — a "facts block" naming the verified rows,
followed by the source passages that back them — merged into the same context
ordinary retrieval builds, or `[]` when the graph has nothing useful to add.

**Components.** `app/retrieval/graph/{router,templates,plans,policy,pipeline,
traverse,hydrate,facts,scope,shadow,intent}.py`, consumed from
`app/retrieval/retriever.py` (`graph_blocks_for`, `_merge_graph_and_retrieval`,
`_observe_in_shadow`). Reads `app/knowledge/graph/` (the write-path projection,
[docs/ingestion/09](../ingestion/09-knowledge-layer-and-graph.md)) and
`app/knowledge/claims/predicates.py` (the closed predicate vocabulary).

---

## Read this section first: what "isolated" actually means today

Every docstring in this package — `app/retrieval/graph/__init__.py`,
`pipeline.py`, and `app/retrieval/README.md` — describes the graph as
"isolated by construction" and says the isolation holds because
`graph_retrieval_enabled` is off. That flag *is* off by default
(`Settings.graph_retrieval_enabled = False`), and a test
(`test_graph_retrieval_is_disabled_by_default`) asserts it. But **no code path
reads `graph_retrieval_enabled` at all** — grep the app and the only hits are
the flag's own declaration and these docstrings. It is vestigial.

The flag that actually gates whether a production question reaches the graph
is `graph_routing_enabled`, checked in `app/retrieval/retriever.py:graph_blocks_for`.
Its default is **`True`**, as of Phase 11 (per the comment beside it in
`app/config.py`):

```python
graph_routing_enabled: bool = True
```

So on an unconfigured deployment, `retrieve()` calls into
`app/retrieval/graph/policy.attempt` on **every** query, and a routed,
answerable question **is** merged into the context the LLM sees. What stays
correctly true from the docstrings:

- the graph package is still loaded via a local `import` inside
  `graph_blocks_for`, never at module top level, so a deployment that flips
  `graph_routing_enabled` back to `false` truly pays nothing;
- the two structural tests still hold — importing production retrieval with
  `GRAPH_ROUTING_ENABLED=false` in the environment does not load the package,
  and no file outside `graph/` (except `retriever.py`) mentions it — but that
  is a statement about the flag being off, and the flag's *default* is on;
- `knowledge_enabled` (whether the write path builds any graph at all) is
  correctly off by default, so on a deployment that has never turned on the
  knowledge layer, `graph_routing_enabled=True` routes plenty of questions but
  every attempt ends in `NOT_ROUTED`, `ZERO_RESULT` or a Neo4j-unreachable
  `FAILED` — never a wrong answer, just wasted routing work.

Treat this as the standing fact to check before trusting any other document,
comment, or mental model that says "the graph only runs when explicitly
enabled." On this codebase, as it stands, it does not.

---

## Why a question can safely reach Neo4j at all

Two independent guarantees do the work; neither depends on the flag above.

**No query reaches Neo4j except a reviewed template.** `templates.py` is a
closed, module-level registry. A caller supplies a `template_id` and typed
parameters — never Cypher. Every template is parameterized (`$param`
everywhere; a label or relationship type is a **literal in reviewed text**,
never built from input), has a fixed hop count (no `[*]` variable-length
path), and ends in `LIMIT $limit`. `templates.validate_parameters` checks
every parameter's shape (`entity_id` against `^(?:person|org|project)_[0-9a-f]{12}$`,
dates against `^\d{4}-\d{2}-\d{2}$`, a predicate against the closed vocabulary)
before anything reaches the driver — `traverse.run_template("MATCH (n) DETACH
DELETE n", ...)` is rejected as an unknown template id, and a malformed
`entity_id` never gets as far as opening a session. Tests enumerate the whole
registry (`test_every_template_is_bounded`,
`test_every_template_is_fully_parameterized`,
`test_labels_and_relationship_types_are_literals_in_the_template_text`) rather
than sampling it, so a template added later is covered the moment it exists.

**Neo4j returns identifiers and structure, never text.** `traverse.GraphResult`
holds `rows`, `entity_ids`, `claim_ids`, `chunk_ids`, `document_ids` — no
template's `RETURN` clause contains `.text`, `.content`, `.body` or
`.chunk_text` (asserted by
`test_every_template_returns_identifiers_not_text`). Source text still comes
from Qdrant, exactly as it does for every other retrieval leg, via
`hydrate.py`. This is what keeps Neo4j from becoming a second text store and
what makes a stale graph citation harmless: a chunk the graph names but Qdrant
no longer holds (because a re-index changed chunk ids) is silently dropped,
never invented.

Sessions are opened read-only (`app.core.clients.graph.read_session`), which
matters specifically because **Neo4j Community has no role-based access
control** — the read/write boundary is enforced in this codebase's own code,
not by a restricted database user (see also
[docs/ingestion/09, Security notes](../ingestion/09-knowledge-layer-and-graph.md#security-notes-for-this-layer)).

---

## Routing: which questions are graph-shaped

`router.route(question)` needs two things to agree, and either alone is not
enough:

1. **A resolved entity** — the question names something the knowledge layer
   has a canonical, claim-eligible identity for.
2. **A relational shape** — the question asks about a *relationship*, not a
   topic. "Tell me about TERI" resolves an entity and asks nothing relational;
   it does not route, and existing retrieval answers it.

### Entity resolution is reused, with one narrow exception

Routing resolves entities with the **same** resolver ingestion uses
(`app.knowledge.candidates`, `app.knowledge.resolver`), so a name too
ambiguous to link during ingestion is equally unusable here — there is no
separate, looser query-time matcher to drift from the write path's identity
rules.

The one deliberate departure: `_accept_unique_match`. PERSON resolution
normally requires co-occurring corroboration (an employer, a project) before
linking a name, because one seeded "Ritu Sharma" does not make every
"Ritu Sharma" that person — essential during ingestion, where a wrong link is
written permanently. A question is a one-line document with no co-mentions by
construction, so that rule as written rejects *every* person question. The
query-side carve-out accepts a resolver decision only when **exactly one**
candidate survived scoring, it is claim-eligible, carries no veto, and sits at
`authoritative`, `pi_attested` or `derived` trust — uniqueness in the entity
store substitutes for the missing corroboration. A companion carve-out,
`_accept_approved_project`, does the same for short, exact project-title
matches from the reviewed alias table that a specificity veto
(`v_project_name_not_specific`) would otherwise block outright (titles under
three tokens or twelve characters, like "Green Jobs" or "WEO 2007") — again
only when it is the *only* veto and everything else about the match is clean.
Neither carve-out changes what ingestion writes; both only change what a
*query* may accept from the resolver's own audit trail.

### Masking: a cue inside a name is part of the name

Before relational cues are matched, every resolved entity's span in the
question is blanked to spaces (`_mask_entities`) — offsets are preserved, only
the characters are replaced, so downstream distance calculations still index
into the original text. This corpus is full of organizations named
"Department of Biotechnology" and "National Centre for ..."; without masking,
"department" and "centre" read as cues for a `PARENT_OF` (organizational
structure) question on every mention of such a name, and years embedded in a
name ("Highlights 2008-11") read as validity windows.

### The schema-derived path, tried first

`_plan_route` reads a predicate out of the closed vocabulary
(`app.retrieval.graph.intent`), a direction out of that predicate's declared
domain and range, and a validity window out of the question's own words, then
asks `plans.py` for a template to bind them to. This is what makes a predicate
queryable by declaring it and its phrasing — no template, route, or class has
to be hand-written for it (see "Why this used to be a smaller graph" below).

**Two hops before one.** A question naming two relationships
("who leads work granted by the Ministry of Environment and Forests") is
asking about the chain between them, and the schema alone under-determines
which relationship is the first hop: iterating cues in the order they were
declared previously matched `(WORKS_AT, LED_BY)` for that question — legal
under the schema, and wrong, because the corpus holds zero `WORKS_AT` claims
naming that ministry and the correct chain (`FUNDED_BY` then `LED_BY`) held
ten. `_nearest_first` orders candidate first hops by distance from the cue to
the anchor entity's span, so the hop adjacent to the named entity in the
question text is tried first.

### The pattern-table fallback

A second, older table (`_PATTERNS` in `router.py`) maps a handful of
memorised question shapes onto specific template ids by regex. It is tried
only when the schema-derived path finds nothing, and it survives for two
reasons: it covers the pre-existing hand-written current-state templates
directly, and it catches phrasing the cue vocabulary in `intent.py` has not
yet learned. Historical questions matched here are redirected through
`_HISTORICAL_EQUIVALENT` to the claim-based template, so a "history of X"
question routed through the old table still reads Claim nodes rather than
current-state edges.

---

## Current versus historical: the distinction that decides which half of the graph is read

- **`current`** reads **derived current-state edges** (`{current: true}`
  relationships) where a hand-written template exists for the predicate and
  direction — cheap, and the graph's own statement of what is true *now*.
  Disputed and superseded claims never get a current edge, so a current
  template structurally cannot surface one
  (`test_current_templates_read_only_current_edges`).
- **`historical`** reads **Claim nodes** and their validity windows directly,
  including superseded ones — because "who led this in 2019" needs exactly
  the claim a current-state edge withholds. Every historical row carries
  `status`, so a disputed claim is presented as disputed rather than as fact
  (`test_historical_templates_expose_status`); the query never filters
  `status` to hide one.

**No template anywhere compares a claim's dates against "now."** A
relationship that ran 1996–1999 is retrieved on identical terms to one that
started last year — temporal validity decides whether something is
*current*, never whether it can be *found*. This matters concretely on this
corpus: every one of its 1,143 projected claims has an end date in the past
(comment in `policy.py`), so a current-only reading of an unstated question
would answer "nothing is known" to questions the graph can answer completely.

### The unstated case: neither "now" nor "the past"

"Who led Project X?" states no period. `intent.read_temporal` returns
`TEMPORAL_UNSPECIFIED` for it — deliberately its own reading, not folded into
either `current` or `history`, because either guess is wrong in a different
direction on this corpus (current: near-total silence; historical-only:
suppresses an ongoing relationship where one genuinely exists). `plans.py`
answers it as **latest**: no temporal filter at all, rows ordered
newest-first, and — the part that makes this safe — every row carries its own
validity window into the rendered output (`facts._validity`), so an ended
relationship reads `(until 2021-03-31)` and cannot be mistaken for a present
one. The distinction is preserved in the answer, not guessed at in the query.

### Capability classes, and why the previous default answered nothing

A schema-derived plan carries one of four capability classes describing the
*shape* of the retrieval, not the subject matter: `relational_current`,
`relational_history`, `relational_multi_hop`, `entity_timeline`. This is what
lets a newly approved predicate land in a class that already exists and is
already enabled — nothing has to be added to `GRAPH_ROUTING_CLASSES` for its
claims to become reachable.

The gate used to default to four legacy classes (`current_funding`,
`multi_hop`, `leadership`, `employment` — all current-state), chosen because
Phase 10 had benchmarked exactly those four. Given the corpus fact above (every
claim ended before 2020), that default could only ever return zero rows: the
one class that reads Claim nodes (`historical`) was switched off. The **current
default is every known class** (`policy.DEFAULT_ENABLED_CLASSES`), because
safety here was never the class gate's job — it comes from the closed
vocabulary, the reviewed templates, parameter validation and the scope check
(below), all of which apply whatever class a route lands in.
`graph_routing_classes` remains useful as a staged-rollout allow-list or for
isolating one class while debugging, but it no longer defines what the graph
*can* answer.

---

## Query scope: fail closed on constraints the graph cannot honour

`scope.py` reduces a query's Qdrant filters and `source_type` pin to a set of
payload keys. `SUPPORTED_SCOPE_KEYS` is **empty by design** — every key is
therefore unsupported today, and a scoped question (by theme, tag, PDF vs.
website, date range beyond a template's own window parameter) declines the
graph outright rather than answering it while silently discarding the
constraint. An unparseable filter condition counts as an unsupported scope
too (`UNKNOWN_KEY`), so a new filter type added elsewhere cannot quietly
disable this check by going unrecognised.

The module explains why filtering the *evidence* instead is not a fix:
hydration fetches supporting text for facts the traversal already selected,
so filtering it would still assert a relationship read from an out-of-scope
document — merely without showing the passage. Scope has to constrain which
**facts** are eligible, and no template does that yet.

---

## The policy layer: budget, breaker, and the index that must not block a request

`policy.attempt(question, ...)` is the single entry point `retriever.py`
calls, and it owns everything that keeps the graph from being able to hurt a
request:

- **Kill switch first.** `graph_routing_enabled` is checked before anything
  else is imported.
- **Wall-clock budget** (`graph_routing_budget_seconds`, default 3.0s) around
  the whole attempt — route, traverse, hydrate, context — run on a worker
  thread via `ThreadPoolExecutor`. A timeout cancels the future (the work is
  abandoned, not awaited) and returns `TIMED_OUT`, costing one worker thread,
  never the request.
- **A circuit breaker.** After `BREAKER_THRESHOLD` (3) consecutive `FAILED`
  or `TIMED_OUT` outcomes, the graph is skipped outright for
  `BREAKER_COOLDOWN_SECONDS` (60s) — measured at ~2.3s per attempt against an
  unreachable server and a full 3s budget when the driver hangs, so
  availability alone ("fall back") is not enough if every question still pays
  a multi-second tax during an outage. `ZERO_RESULT` never trips the breaker;
  only `FAILED`/`TIMED_OUT` do, because a zero result is the graph working
  correctly.
- **A cached, non-blocking entity index.** `EntityIndex.load()` takes ~7s
  cold, ~0ms warm, against a 3s routing budget — so a cold cache load would
  always time out *inside itself*, and because `TIMED_OUT` trips the breaker,
  three of them would shut routing off before the cache ever populated
  (measured: 0 of 86 benchmark questions used the graph under the old
  blocking design). `entity_index_or_warm()` fixes this structurally: the
  first caller starts the load on a background executor and gets `None`
  immediately (`INDEX_WARMING` — a decline, not a failure, and explicitly
  excluded from the breaker), every caller during the build also gets `None`,
  and once the load lands every later query routes at the warm cost (~0.3s to
  route). The index is reused for `INDEX_TTL_SECONDS` (300s) rather than
  reloaded every query — right for ingestion, which must see entities seeded
  moments earlier, wrong for retrieval, which was paying 60–100ms per query to
  rebuild an index that only changes when the graph is reprojected.

### Outcomes are one of eleven distinct values, and they matter individually

`DISABLED`, `NOT_ROUTED`, `CLASS_DISABLED`, `ANSWERED`, `ZERO_RESULT`,
`NO_EVIDENCE`, `FAILED`, `TIMED_OUT`, `CIRCUIT_OPEN`, `SCOPE_UNSUPPORTED`,
`INDEX_WARMING`. The module is explicit that zero-result and failure are
different things an operator must be able to tell apart even though a user
cannot: `ZERO_RESULT` is the graph correctly reporting the corpus knows of no
such relationship; `FAILED` is the graph being unable to say. Every one of
these is its own counter (`FALLBACK_OUTCOMES` covers all of them except
`ANSWERED`, so a caller checking `attempt.used` cannot accidentally answer
from anything else).

---

## Executing a template: `traverse.run_template`

The only module that talks to Neo4j on the read path. It accepts a
`template_id` and parameters, resolves the id against the registry (an
unknown id — including literal Cypher passed where an id belongs — errors
before a session is even opened), validates every parameter, and runs the
template's fixed Cypher text with the checked parameters bound.

`mode` is an explicit override the caller supplies rather than the template's
own declared mode, because the predicate-parameterized templates
(`relationship_by_subject`, `relationship_by_object`, `entity_timeline`,
`relationship_two_hop`) read Claim nodes whichever period is asked about — the
*same* template answers "who leads this now" and "who led it in 2015",
differing only in the window bound into it. Declaring the storage mode
(`historical`, since it hits Claim nodes) would be true but useless to a
renderer that needs to know which question was actually asked. The route
carries that, and `run_template`'s `mode` parameter is how it reaches the
result — still checked against the closed `MODES` set.

Every call is wrapped in `retrieval_log.graph_call`, which records the
template id, mode, validated parameters, the registry's fixed Cypher text, and
the resulting rows — the whole graph side of a query, safe to log verbatim
because the Cypher is a reviewed constant and the parameters have already
passed validation.

`_collect` gathers `entity_ids`, `claim_ids`, `chunk_ids`, `document_ids` out
of whichever columns a row happens to carry (the predicate-parameterized
templates name their ends `anchor_id`/`mid_id`/`far_id` rather than by type,
since one query now serves every predicate) — deduplicated and order-stable,
so hydration is deterministic across repeats of the same query.

---

## Hydration: `chunk_id` is the bridge the whole design rests on

Neo4j knows *that* something is true and *where* it was read; Qdrant holds the
text. The hop between them is `chunk_id`, which has been the Qdrant point ID
since long before the graph existed — no new key, no duplicated text store to
keep in sync.

Two distinct lookups:

- **`hydrate_chunks`** — an exact fetch by point id (`client.retrieve`), not a
  search: no embedding, no scoring, no filter, because the graph already
  decided which chunks are relevant. Deduplicated first (a result routinely
  names the same chunk twice, from two claims on one document) and batched at
  150 ids per call (`hydration.BATCH_SIZE`, matching the existing id-scoped
  retrieval's cap). A chunk the graph cites but Qdrant no longer holds — the
  expected outcome after a re-index changes chunk ids — is dropped, never
  invented.
- **`hydrate_documents`** — used only when a claim's evidence is a *document*
  rather than a chunk, which today is **every** claim: all of them are
  CMS-field claims, and a metadata fact (a project's `field_ongoing_pi_name`)
  has no prose span to point at. Fetches a few chunks per document
  (`CHUNKS_PER_DOCUMENT`, 3) via the existing `build_filter`, so the mandatory
  shape filter (current, non-parent chunks) applies exactly as everywhere
  else. Two passes, because Qdrant's `scroll` has no fairness: one long
  document can consume a whole batched scroll and starve every other cited
  document of any evidence at all, so a second, per-document pass tops up
  anything the broad scroll missed entirely. Capped at `MAX_DOCUMENTS` (20):
  the context builder keeps a handful of blocks regardless, so hydrating a
  hundred documents would spend round trips on candidates that are discarded
  anyway.

`hydrate(result)` prefers chunk evidence and falls back to document evidence
only for documents no chunk already covered.

---

## Rendering: rows are the answer, passages are the citation

`facts.py` exists because of a measured failure: the Phase 10 benchmark found
graph retrieval scoring **zero** answer coverage on multi-hop questions it had
answered *perfectly* — the traversal returned twelve principal investigators,
and the context handed to the model contained none of their names, because
the evidence passage (a project page's body) never states a fact that lives
in a structured CMS field.

So for a relational question, `facts.render(result, route)` turns the
verified rows themselves into a citable `ContextBlock`, and the evidence
passages become supporting citation rather than the sole vehicle for the
answer:

- Every line states the relationship, its validity window (`_validity` —
  never silently empty; an undated claim renders `(no recorded dates)` rather
  than an unqualified present-tense sentence, which previously produced "the
  Framework **is a partner of** TERI" from a claim carrying no dates at all),
  and its status (`_status` — `[DISPUTED — the sources contradict each
  other]`, `[SUPERSEDED by a later record]`, or nothing for active).
- A two-hop row renders **both** legs, in the direction the traversal
  actually recorded (`anchor_is_subject`/`mid_is_subject`, since the Cypher
  matches direction-agnostically) — without this, "Alok Adholeya works at
  TERI" renders backwards on half the rows.
- `_temporal_heading` states, once, how the whole block's period should be
  read — "(as currently recorded)", a named window, or "(including past
  relationships — read each validity window)" for an unspecified historical
  pull — so nothing is left for the model to infer from the rows alone.
- The block always states the **total** row count, even when only some rows
  are shown, because a model asked to count a truncated list gets it wrong:
  a 40-row block once produced "a total of 56 projects" when asked to sum
  itself. The traversal already knows the number.

Line and character caps (`MAX_LINES`/`MAX_LINES_HISTORICAL` = 25/50,
`MAX_CHARS` = 8000) keep one large result from crowding the evidence passages
out of the token budget entirely — a historical question gets more room
because for it the list *is* the answer, not a shortened version of one.

---

## Merging with ordinary retrieval — the graph no longer replaces anything

`retriever.retrieve()` calls `graph_blocks_for` unconditionally (subject to
the flag discussed above) and, when it returns blocks, merges them with the
semantic pull via `_merge_graph_and_retrieval` rather than returning the graph
answer alone. This is itself a correction of a measured failure: the graph
used to short-circuit retrieval (`if graph_blocks: return`), which is right
only when the rows are the *whole* answer. "A brief history of TERI" routes to
`entity_timeline` and answers with eleven funding/partnership rows whose
evidence is a handful of project pages — none of which say when TERI was
founded. The Annual Report chunk that opens "TERI was established in 1974"
sits at 0.77 similarity and was never fetched, because the semantic leg never
ran at all.

The merge keeps the facts block first (it is what the graph verified), then
graph evidence, then reserves `SEMANTIC_MIN_SLOTS` (2) slots for ordinary
retrieval's prose before letting any leftover graph evidence back in, and
de-duplicates both legs against each other by parent-chunk identity
(`_block_key` prefers `parent_chunk_id` — the graph can hydrate one child of a
parent while the semantic pull admits a sibling child, which would otherwise
print the same passage twice). The token budget is shared rather than spent
twice, closing an earlier gap where the facts block was appended *after*
`build_context` had already spent its whole allowance.

---

## Shadow mode: observing without ever answering

`shadow.observe(question, production_blocks)` exists to gather evidence on
live traffic **before** anything is routed to the graph in production —
useful independently of whether `graph_routing_enabled` is on, e.g. to
compare a candidate class or template change against production first.

The non-influence is structural, not a matter of discipline:

- `observe` **returns `None`**, so there is no value for any caller to use.
- It runs on a background thread (`MAX_WORKERS=2`); a slow or hanging graph
  adds zero latency to the request.
- Every exception is caught and logged; an unreachable Neo4j cannot fail a
  request that had already succeeded without it.
- Work already in flight caps at `MAX_IN_FLIGHT` (8) and is **dropped**, never
  queued, past that — a traffic spike costs a missing sample, never a growing
  backlog.

Each observation records whether the question routed, the template, rows,
errors, and — the actual point of running it — `document_overlap` and
`novel_documents` between the graph's cited documents and what production
retrieval found on its own: agreement is reassuring, and a novel document is
the signal worth investigating.

---

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| `graph_routing_enabled` off | checked first in `policy.attempt` | Package not imported; `[]` returned | Enable the flag |
| Question names no resolvable entity | `router._resolve_entities` | `NOT_ROUTED` | — (retrieval answers instead) |
| Named entity is ambiguous | resolver `AMBIGUOUS`/`PROVISIONAL`, no carve-out applies | `NOT_ROUTED`, `outcome.ambiguous` lists the surface | — |
| Entity resolved, question not relational | no predicate cues matched | `NOT_ROUTED`, reason "not relational" | — |
| Routed class not enabled | `class_of_route` not in `enabled_classes()` | `CLASS_DISABLED` | Add the class to `graph_routing_classes`, or leave the default (every class) |
| Query scope no template can honour | `scope.describe(...).is_supported` is false | `SCOPE_UNSUPPORTED`, unsupported keys named | — (retrieval honours the scope) |
| Entity index cold | `entity_index_or_warm()` returns `None` | `INDEX_WARMING`; does **not** trip the breaker | Automatic once the background warm-up lands |
| Neo4j unreachable or errors | exception in `traverse.run_template` / session open | `FAILED`, `result.error` set | Breaker opens after 3 consecutive; closes on any success |
| Query exceeds its budget | `future.result(timeout=budget)` raises | `TIMED_OUT`, future cancelled | Same breaker as above |
| Breaker open | `circuit_is_open()` | `CIRCUIT_OPEN`, skipped without waiting | Closes automatically after `BREAKER_COOLDOWN_SECONDS`, or `reset_circuit()` |
| Graph runs, no rows | `result.empty` | `ZERO_RESULT` — never trips the breaker | — (retrieval may still find prose evidence) |
| Rows returned but unrenderable/unhydratable | `facts_block is None and not evidence` | `NO_EVIDENCE` | — |
| Cited chunk missing from Qdrant | `hydrate_chunks` | Dropped silently, never invented | Expected after a re-index; nothing to recover |
| Long document starves a scroll batch | fairness pass in `hydrate_documents` | Second, per-document fetch tops it up | — |
| Malformed template parameter (any shape) | `templates.validate_parameters` / `_check` | Rejected before the driver is touched | Fix the caller; this should never fire from routed traffic |

## Observability

- Per attempt: `retrieval_log.record(retrieval_log.GRAPH, "route", ...)` — the
  full routing decision, with `outcome`, `used`, `query_class`, `template_id`,
  `mode`, `entity`, block count, and `reason`.
- Per traversal: `retrieval_log.graph_call("cypher_template", ...)` — the
  template id, mode, validated parameters, the fixed Cypher text, and the
  rows returned.
- Per hydration call: `retrieval_log.qdrant_call("retrieve" | "scroll", ...)`.
- Metrics: `record_event("graph_routing", outcome)` and
  `record_event("graph_routing.class", f"{class}:{outcome}")` — see
  [11](11-observability-and-logging.md) for how these surface on
  `GET /metrics`.
- Shadow mode: one `graph shadow: {...}` log line per observation, and
  optionally one JSONL row per observation at `graph_shadow_log_path`.
- `policy.py` logs the outcome summary at INFO on every attempt
  (`logger.info("graph routing: %s", result.summary())`).

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `graph_routing_enabled` | **`true`** | The actual kill switch for graph-backed retrieval. See the section above — this is not the flag most of this package's own comments describe. |
| `graph_retrieval_enabled` | `false` | Declared, tested, and read by nothing. Vestigial. |
| `knowledge_enabled` | `false` | Master switch for the write-side knowledge layer; with this off the graph is structurally empty regardless of routing. See [docs/ingestion/09](../ingestion/09-knowledge-layer-and-graph.md). |
| `graph_routing_classes` | `""` (→ every class) | Comma-separated allow-list; unknown names are dropped with a warning. |
| `graph_routing_budget_seconds` | `3.0` | Wall-clock budget for one whole attempt. |
| `graph_shadow_enabled` | `false` | Run the graph beside production and only log the comparison. |
| `graph_shadow_log_path` | *(unset → log only)* | Optional JSONL destination for shadow observations. |
| `neo4j_uri` / `_user` / `_password` / `_database` | `bolt://localhost:7687`, `neo4j`, —, `neo4j` | Connection, shared with the write path. |
| `neo4j_connection_timeout` | `10.0` | Handshake timeout. |

## Cross-references

- [docs/ingestion/09 — The Knowledge Layer and Graph](../ingestion/09-knowledge-layer-and-graph.md)
  for how the graph is built and projected on the write path.
- `app/retrieval/README.md` for the package-level import rules this module
  respects (they hold structurally; only the flag's default has drifted from
  what the prose says).
- `tests/retrieval/graph/test_graph_retrieval.py` for the executable version
  of every safety claim in this document — including the flag-forcing
  subprocess test that only proves isolation when `GRAPH_ROUTING_ENABLED` is
  explicitly set to `false`.

---

Previous: [07 — Structured Answers](07-structured-answers.md) · Next: [09 — Generation and Synthesis](09-generation-and-synthesis.md)
