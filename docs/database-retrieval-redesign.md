# Database retrieval redesign: natural-language queries over the catalog

Design doc for re-architecting how the assistant retrieves catalog data from
free-text questions. Complements [database-tool-registry.md](database-tool-registry.md)
(what the tools are) and [database-planner-architecture.md](database-planner-architecture.md)
(how calls are planned). Schema reference: [ingestion.md](ingestion.md).

---

## 1. Why

The structured (database-intent) path in `app/retrieval/structured/` already has a
five-tool surface and a shared filter object. Three gaps make loose,
synonym-heavy phrasing fail:

1. **No entity resolution.** There is no fuzzy matching anywhere in the repo — no
   `difflib`, no `rapidfuzz`, no `pg_trgm`. Author and theme matching is SQL
   `LIKE` substring plus case-insensitive exact match
   (`app/catalog/terms.py:107-121`). "rishab negi" or "env theme" resolve to
   nothing, and the pipeline then answers from vector search as though the
   question had been understood.
2. **Tags are unfilterable.** `RecordFilters` has no `tag` field, so "posts
   tagged policy" cannot be expressed — even though the link data is already in
   `documents_term` (role `field_tags`). The qa/vector path already applies
   `QueryAnalysis.tags` as a hard Qdrant filter (`understanding/filters.py:79-82`);
   only the structured/DB path drops the field, an asymmetry worth closing even
   though (§5) the tag vocabulary itself is too long-tailed to expose as a
   browsable dimension.
3. **Main vs Other themes are indistinguishable at query time.** `theme_group`
   now records the bucket on `documents_theme`, but `list_themes` reads the
   canonical `terms` table and renders one flat list.

Plus a maintenance problem: **three prompts** independently re-describe the same
DB slots (`app/retrieval/understanding/prompts.py:82-91`,
`app/retrieval/structured/answerer.py:36-60`,
`app/retrieval/structured/planner.py:119-137`), each carrying its own copy of the
"publications" collective-word warning. They drift.

**Goal.** The tools handle any `author × bundle × theme × tag × date`
combination, resolve fuzzy names to canonical entities with a confidence score,
surface ambiguity instead of guessing, and never report a `0` that actually means
"I didn't understand the filter".

---

## 2. The schema, as it actually is

Verified against `app/catalog/schema.py`. **MySQL 8 / InnoDB, raw SQL, no ORM.**
DDL is idempotent `CREATE TABLE IF NOT EXISTS` + `ALTER` guards in that one file.

| Question | Answer |
|---|---|
| Is theme on the post or the bundle? | **On the post.** Twice: `documents_theme` (free-text name + `theme_type` + `parent` + `theme_group`) and `documents_term` → `terms` (canonical UUID, `vocabulary='themes'`). The bundle carries **no** theme. |
| Can a post have many themes? Many bundles? | **Many themes, one bundle.** `documents_theme` is `PRIMARY KEY (document_id, theme)` — M:N. `documents.bundle` is a scalar `VARCHAR(128)`. |
| Is "Events" a reusable type or a per-theme row? | **Reusable type.** A hardcoded Drupal content-type string in `DEFAULT_BUNDLES` (`app/ingestion/extractors/drupal_extractor.py:44-61`). There is no bundle table and no `bundle_id`. |
| Are authors a table with IDs? | **No.** `documents_author(document_id, author)` — free text, no PK, no IDs. |
| What marks main vs other? | **`theme_group ENUM('main','other')`** on `documents_theme` (`schema.py:99`), derived from the `data.json` bucket by `theme_taxonomy._group_code`. |

### 2.1 It is a star schema, not a hierarchy

There is **no Theme→Bundle edge**. `bundle` and theme are independent facets
hanging off the document:

```
                    documents (the "post")
   bundle: VARCHAR ──┤ document_id ├── documents_theme   (M:N, + theme_group)
   published_at      │             ├── documents_author  (M:N, free text)
   title, url        │             └── documents_term ── terms (themes | tags | …)
```

Every target query still works — "events **under** Climate Change" is a facet
intersection (`bundle='events' AND theme='Climate Change'`), not a traversal.
Two consequences shape the tool surface:

- **`list_bundles(theme_id?)` is not a structural listing.** "Bundles under a
  theme" is derived — the distinct bundles among posts carrying that theme —
  which is exactly `aggregate_records(group_by="content_type", filters={theme})`.
  It folds in, keeping the count at five. `list_themes()` stays separate because
  the Main/Other rule (§6) is real behaviour, not a grouping.
- **`resolve_entity`'s `id` is polymorphic.** `term_uuid` for theme and tag; the
  canonical **name string** for author and bundle, because neither has an ID.

### 2.2 Column names

| Commonly assumed | Actual |
|---|---|
| `source_url` | **`url`** (`source_url` exists only on `ingest_log`) |
| `published_date` | **`published_at`** (DATETIME) |
| `author_name` on the post | **`documents_author`** child table |
| `tags[]` on the post | no column — `documents_term` → `terms` where `vocabulary='tags'` |
| `bundle_id` | **`bundle`** — the literal string |

---

## 3. Decisions

- **Keep the existing `*_records` tool names.** They are referenced by three
  prompts and ~10 test files that assert `rendered` output byte-exactly. The
  domain has no "posts" — these are website documents.
- **Ambiguity is a stateless clarify-in-answer.** The chat path is one-shot SSE
  with no ask-back turn; a near-tie returns candidates and the user re-asks.
- **An unresolvable filter is terminal; a resolved filter matching nothing
  reports an honest `0`.**
- **Scoring is stdlib `difflib` behind a SQL `LIKE` prefilter** — no new
  dependency, per the no-new-infrastructure constraint.
- **`lookup_record` stays** as a sixth tool. It is pre-existing, not new, and
  `app/pipeline/query_pipeline.py:126` depends on it for the lookup→content-QA
  chain. Removing it to reach "exactly five" would break that flow for no gain.
- **`year` stays** as an `aggregate_records` dimension. Already shipped and
  tested; answers "how many per year" with no extra surface.
- **Tag is a filter, not an advertised entity type.** A dev-DB sample (§4.1)
  shows 237 distinct tag terms over ~224 tagged documents — roughly 3 documents
  per tag, with near-duplicates like "Solid waste" / "Urban waste" / "Waste
  management" — the shape of freeform CMS tagging, not a curated vocabulary.
  Confidence-scored fuzzy resolution over that set would land in the ambiguous
  band constantly, and `group_by="tag"` would surface a noise-level long tail.
  `RecordFilters.tag` and the SQL join still get built (§5) so an exact tag name
  can be filtered on, but `resolve_entity`'s advertised types, the prompt's
  vocabulary map, and `group_by` options stay `author | bundle | theme` — the
  LLM is not taught to reach for tag matching given the long tail.

---

## 4. Resolution layer — `app/retrieval/structured/resolve.py` (new)

`resolve.py` scores names against three types — `author | bundle | theme` — per
the tag decision in §3. Candidate sources, cheapest first:

| type | source | notes |
|---|---|---|
| `bundle` | in-memory `DEFAULT_BUNDLES` + `_BUNDLE_SYNONYMS` + `_BUNDLE_LABELS` | no DB hit; reuse `entities.py` |
| `theme` | `terms` where `vocabulary='themes'`, else the `documents_theme` facet (§4.1) | `terms.list_themes()` is already vocabulary-parameterized |
| `author` | `SELECT DISTINCT author FROM documents_author` | new reader in `queries.py`; `lru_cache` the ranked result. Deliberately **not** `LIKE`-prefiltered: a misspelling ("rishab negi") is not a substring of the stored name, so a prefilter would exclude the very matches this exists to catch |

### 4.0 Where resolution is applied — the filter path, not a planner step

**Resolution runs inside `filters.resolve_filters()`, on the way to SQL.** An
earlier design had the planner emit `resolve_entity(...)` and then a filtered
call using the result; that cannot work, because a `DatabasePlan`'s calls
execute **in parallel** (`planner.execute` → `ThreadPoolExecutor.map`) with no
data flow between them. The two-call shape produced self-contradicting answers:

```
'rishab negi' resolves to Rishabh Negi (author).      <- resolve_entity's section
There are 0 items by rishab negi matching your query. <- the sibling call, unaffected
```

Canonicalizing in the filter path instead means every tool benefits regardless
of plan shape, with no ordering or substitution machinery. `ResolvedScope`
carries the outcome:

| field | meaning |
|---|---|
| `author` / `term_uuids` / `theme` | what reaches SQL — the **canonical** name after matching |
| `effective` | the same `RecordFilters` with canonical names substituted; tools render and echo `data["applied"]` from this, so an answer names the entity it really filtered on |
| `ambiguous` | a near-tie; tools return a clarification **before** querying |
| `author_missed` | fuzzy matching found nothing plausible; becomes a miss only if the query then returns empty (§7) |

`tools.resolve_entity` remains a tool for the one thing this path cannot do:
answering a question that *is* about which entities match a name ("is there an
author called Negi?"). The prompt tells the planner to pass names through as
written and **not** to pre-resolve them.

**Scoring.** Normalize (casefold, collapse whitespace, strip punctuation), then
take the max of: exact `1.0`; substring/prefix boost;
`difflib.SequenceMatcher.ratio()`; and a hand-rolled token-set ratio so word
order does not matter ("negi rishabh" → "Rishabh Negi").

```
score >= 0.90 and clear of runner-up by >= 0.10  -> ACCEPT
score >= 0.60                                    -> AMBIGUOUS (surface candidates)
otherwise                                        -> MISS (terminal, explicit)
```

Returns `list[EntityCandidate]` — `@dataclass(frozen=True)` with
`id, canonical_name, type, score`, following the house dataclass/pydantic split
(dataclass for internal contracts, pydantic only for LLM-filled schemas).

Wrap the existing `filters.resolve_theme` / `terms.resolve_terms` rather than
duplicating them: exact match must stay the fast path, and alias resolution and
`descendant_uuids` subtree expansion already work.

`type` omitted → try every type and return the merged ranked list, which makes
"how many climate?" answerable without the caller knowing the entity kind.

### 4.1 Operational dependency: `resolve_entity(type="theme")` needs `terms` populated

`resolve_entity` for `theme` reads the canonical `terms` table
(`vocabulary='themes'`), not the free-text `documents_theme` facet. `terms` is
only populated by `_sync_term` (`app/ingestion/pipeline.py:93-98`), which fires
for `entity_type == "taxonomy_term"` records. Per
`app/ingestion/change_detection/drupal.py:60-67`, taxonomy-term sources are only
added on a **full, unfiltered** crawl (`bundles is None`); an explicit `--bundle`
crawl (typical for a targeted/incremental run) builds node sources only and
never touches `terms`.

Verified against the local dev DB: `terms` has **0 rows across every
vocabulary**, while `documents_theme` (258 rows, `theme_group` populated) and
`documents_term` (2,192 rows, including 668 `field_tags` links across 237
distinct term UUIDs) are both populated. `ingest_log` confirms why — every row
is `bundle='article'`, i.e. this DB has only ever run a node-bundle-scoped
crawl. A term/tag-scoped or full crawl
(`--bundle taxonomy_term:themes --bundle taxonomy_term:tags`) has never run
here, so those 237 tag-term UUIDs and every theme UUID are currently
unresolvable to a name.

**This is a real operational gap the resolver must degrade through, not paper
over:**

- **`theme` has a fallback, and every tool must actually reach it.**
  `resolve_theme` falls back to the `documents_theme.theme` display-name facet
  when `terms` yields no rows for a name, and `ResolvedScope.as_kwargs` carries
  that name through as a `theme` kwarg. **A tool must therefore not refuse an
  unresolved theme up front** — doing so returns before `as_kwargs` is ever
  consulted, making the fallback dead code and denying a theme that plainly
  exists (measured: with `terms` empty, `documents_theme` still held 27 distinct
  themes over 2,016 documents, so an up-front refusal answered "no theme
  matching 'Environment' found" against 461 real matches). The correct order is:
  query with the fallback, then treat an *empty result* on an unresolved theme as
  the miss — at that point "unknown theme" and "genuinely no documents" are
  indistinguishable, so the miss is the honest answer. A theme that *did* resolve
  and matched nothing stays an honest `0`. `resolve_entity(type="theme")` uses
  the same fallback for its candidate list.
- **`tag` has no fallback, so it is guarded up front.** There is no free-text tag
  facet table analogous to `documents_theme`. If `terms` has no rows for
  `vocabulary='tags'`, a tag filter has no column to match on at all — so unlike
  theme, an unresolved tag *is* a terminal miss before querying, since querying
  would silently drop the filter and count everything. This is a second,
  independent reason (beyond the long-tail argument in §3) not to advertise
  confident tag resolution.

Check `SELECT COUNT(*) FROM terms WHERE vocabulary = 'themes'` before enabling
`entity_resolution_enabled`: non-zero means themes resolve canonically
(rename-proof, subtree-expanding); zero means every theme query runs on the
display-name fallback above — correct, but fuzzier (substring `LIKE`, no
sub-theme expansion). Tag filtering does not work at all until a
taxonomy-scoped crawl populates `vocabulary='tags'`.

---

## 5. Tag filtering — filter only, no confidence-scored resolution

Add `tag: str | None` to `RecordFilters` (`types.py:24`) and `tag_uuids` to
`ResolvedScope`. Resolve it with a small `resolve_tag(tag: str | None)` helper in
`filters.py`, mirroring `resolve_theme` exactly (exact/alias match against
`terms` where `vocabulary='tags'`, degrading to `{"tag": tag}` on no match) —
**not** the confidence-scored `resolve_entity` flow. A tag name goes straight
into an exact/alias lookup; there is no ambiguous-candidate step and no
free-text fallback table for the display-name case (§4.1), so an unresolved tag
is always a hard miss, never a guess.

In `_catalog_filters` (`app/catalog/queries.py:38-96`), add a **second,
separately-aliased** `documents_term` join:

```
theme -> JOIN documents_term dt   (alias dt exists today)
tag   -> JOIN documents_term tt   (new alias)
```

They must be separate joins ANDed together, **not** one merged `IN` list — a post
filtered by theme *and* tag has to satisfy both, and merging the UUID lists turns
that into an OR. Set `distinct = True` as the existing facet joins do.

`"tag"` is **not** added to `_GROUP_DIMENSIONS` (no `aggregate_records(group_by=
"tag")` — see §3) but the join above is exercised directly whenever
`RecordFilters.tag` is set on `count_records` / `list_records`.

---

## 6. `list_themes` — Main/Other sections

`theme_group` lives on `documents_theme`, which only has rows for themes some
document actually carries. `list_themes` reads `terms`, which includes themes with
zero documents. Do **not** switch it to the facet table — that loses
zero-document themes and reintroduces display-name drift.

Instead keep `terms` as the canonical set and label each name from
`theme_taxonomy` in-process, since `data.json` is the authority `theme_group` is
itself derived from. `_load()` is private and `primary_tags()` discards the group,
so add public accessors beside it:

```python
def group_of(name: str) -> str | None:      # "main" | "other" | None
def themes_by_group() -> dict[str, list[str]]
```

Render two labelled sections, main first, with per-theme counts from the existing
term-join path. A theme the map does not know (added in the CMS since) groups as
`None` — list it under "Other themes", never drop it.

Asking about **one specific theme** does not touch this path — that is a normal
filtered query, with no main/other distinction.

---

## 7. Miss semantics — `ok=False` is currently overloaded

Today `ok=False` means "fall through to vector search" for *every* failure
(`answerer.py:179-182` returns `None` when no result is ok). The split needs two
channels. Add one defaulted field to `ToolResult` (`types.py:68`) — additive, so
no existing construction site changes:

```python
error_kind: str | None = None
# "unresolved" | "ambiguous"                      -> terminal, render the message
# "no_records" | "unknown_entity" | "query_failed" -> fall through (today's behaviour)
```

In `answerer.py`, before returning `None`, check for a terminal result and return
its `rendered` instead. Existing `"no matching records"` and `"query failed"`
paths keep falling through, so golden queries and the byte-exact `rendered`
assertions stay green.

**One real behaviour change.** `count_records`'s existing `"theme did not resolve
to a known term"` guard (`tools.py:126-127`) becomes terminal rather than falling
through. `test_count_records_unresolved_theme_is_not_ok` asserts only
`ok is False`, so it still passes — but the user-visible answer changes from a
vague semantic answer to "no theme matching 'X' found". That is the intent, noted
here so it is not a surprise.

---

## 8. Echo the applied filters

Every tool sets `data["applied"]` — the resolved filters with their canonical
names and scores, not the user's raw strings. This is what lets an answer read
"3 posts by **Rishabh Negi** in **Events** under **Climate Change**", and lets the
user catch a wrong match. Extend the `rendered` phrase-builder (`_period_label`
and the theme phrase in `count_records`) to name author, bundle, and tag too.

Exact-input renders are unchanged; only fuzzy-matched inputs render the canonical
name in place of what was typed.

---

## 9. `list_records` — `offset` and `fields[]`

Add `offset: int = 0` to `list_documents` (`queries.py:130`) → `LIMIT n OFFSET m`,
clamped as `limit` already is.

Keep `fields[]` **out of SQL** — apply it when projecting `StateRecord` into
`data["records"]` and the rendered lines. Pushing a caller-supplied field list
into `SELECT` would add an injection surface and break `_row_to_record`, for no
benefit at these row counts.

---

## 10. One prompt, three consumers

New `app/retrieval/structured/prompt.py` exports composable blocks — vocabulary
map, entity types, resolve-first rules, behavioural rules, few-shots — imported by
all three existing prompts, so the slot documentation and the collective-word
warning exist once. Keep interpolating `", ".join(DEFAULT_BUNDLES)` from its
single source.

**Contents.**

- **Vocabulary map** — articles / items / stories / pieces / entries → post; a
  bundle's own name → `bundle` (users never say "bundle").
- **Pass names through; do not pre-resolve** — author and theme names go into
  `filters` exactly as the user wrote them and are canonicalized in the filter
  path (§4.0). A separate `resolve_entity` call cannot help: its result cannot
  reach a sibling call. `resolve_entity` is for questions that *are* about
  matching a name ("is there an author called Negi?"). Tags are matched exactly
  (§3, §4.1).
- **Counting vs. aggregating vs. listing** — `count_records` for "how many" of one
  thing; `aggregate_records` for "how many per X" / "which X does Y appear in"
  (one call, never N, `group_by` one of `theme | content_type | author | year`);
  `list_records` when the user wants rows or metadata.
- **Behavioural rules** — theme Main/Other; ask on ambiguity, never silently pick
  the top hit; no fabrication; always state the interpretation.

### 10.1 Few-shot examples

Each shows the **tool call**, not the answer. Names go in as written; the filter
path canonicalizes them (§4.0), so every filtered query is a single call.

| # | Query | Call |
|---|---|---|
| 1 | How many posts are there from Rishabh Negi? | `count_records(filters={author="Rishabh Negi"})` |
| 2 | How many events are there? | `count_records(entity="events")` |
| 3 | How many themes are there? | `list_themes()` — Main/Other sections |
| 4 | How many events are under Climate Change? | `count_records(entity="events", filters={theme="Climate Change"})` |
| 5 | How many posts from **rishab negi** under **env theme**? | one `count_records` — the misspelling and abbreviation resolve inside the filter path |
| 6 | Which bundles does Rishabh Negi post in? | `aggregate_records(group_by="content_type", filters={author=…})` |
| 7 | Latest 5 reports under Climate Change with source links | `list_records(entity="report", limit=5, filters={theme=…})` |
| 8 | How many posts are tagged "policy"? | `count_records(filters={tag="policy"})` — tags matched exactly |
| 9 | Is there an author called Negi? | `resolve_entity("Negi","author")` — the question *is* about matching a name |

The two edge cases are handled by the filter path, not by the planner:
**ambiguity** ("rishab" → clarification question instead of a count) and **miss**
("posts by Zzz" → "no author matching 'Zzz' found" instead of a misleading zero).

---

## 11. Rollout

Gate the resolver and the terminal miss semantics behind
`entity_resolution_enabled: bool = False` in `app/config.py`, following the house
pattern (`database_multi_call_enabled` at `:139`) with the
`# Launches OFF; flip after eval.` comment. This is the one change that alters
existing pipeline fall-through, so it needs a rollback switch.

The tag filter, `offset` / `fields[]`, and the Main/Other listing are pure
additions — no flag.

**Operational prerequisite (§4.1).** `resolve_entity(type="theme")` and the tag
filter both depend on `terms` being populated for the relevant vocabulary. Before
flipping `entity_resolution_enabled` on in any environment, run:

```sql
SELECT COUNT(*) FROM terms WHERE vocabulary = 'themes';
SELECT COUNT(*) FROM terms WHERE vocabulary = 'tags';
```

If either is `0`, the environment has only run node-bundle-scoped crawls; run a
taxonomy-scoped or full crawl first (`--bundle taxonomy_term:themes --bundle
taxonomy_term:tags`, or drop the `--bundle` filter for a full crawl) — this
calls the live Drupal JSON:API and writes the resulting rows, so treat it as a
deliberate action against an external system, not a routine local step.

---

## 12. Files

**New** — `app/retrieval/structured/resolve.py`, `app/retrieval/structured/prompt.py`

| File | Change |
|---|---|
| `app/retrieval/structured/types.py` | `RecordFilters.tag`; `ToolResult.error_kind` |
| `app/retrieval/structured/filters.py` | `resolve_tag` (mirrors `resolve_theme`); `tag_uuids` on `ResolvedScope` |
| `app/retrieval/structured/tools.py` | `resolve_entity`; `data["applied"]`; `error_kind`; `offset`/`fields`; `list_themes` sections |
| `app/retrieval/structured/planner.py` | `resolve_entity` in the `Literal`; reuse `ToolName`; import the shared prompt |
| `app/retrieval/structured/answerer.py` | terminal-vs-fall-through branch; import the shared prompt |
| `app/catalog/queries.py` | tag join in `_catalog_filters`; `offset`; `distinct_authors` |
| `app/catalog/theme_taxonomy.py` | public `group_of` / `themes_by_group` |
| `app/retrieval/understanding/prompts.py` | import the shared slot block |
| `app/config.py` | `entity_resolution_enabled` |
| `docs/database-tool-registry.md`, `docs/database-planner-architecture.md` | document the sixth tool, tag filter, Main/Other, resolution bands |

**Reuse, do not reimplement:** `terms.resolve_terms` (alias-aware exact match),
`terms.descendant_uuids` (subtree expansion), `terms.list_themes` (already
vocabulary-parameterized), `entities.normalize_entity` / `entity_label`,
`filters.resolve_theme` (the pattern `resolve_tag` mirrors), `queries._like`,
`queries._catalog_filters`.

---

## 13. Tests

pytest, flat `tests/`, no conftest. Match the two existing DB patterns: stub the
reader for tool tests; the `_FakeCursor` / `_FakeConn` pair for SQL-string
assertions. No real DB.

**New**

- `tests/test_entity_resolution.py` — per-type candidate sourcing for
  `author | bundle | theme` only (`tag` is not a `resolve_entity` type — §3);
  exact beats fuzzy; misspelling ("rishab negi"), casing ("climate"), partial
  ("env theme"); word-order via token-set; band boundaries; near-tie →
  ambiguous; below floor → miss; `type=None` merged ranking excludes tag;
  `lru_cache` means one DB hit per term; `resolve_entity(type="theme")` falls
  back to `documents_theme` when `terms` has no rows for the name (§4.1).
- `tests/test_theme_groups.py` — main-first sections; zero-document theme still
  listed; unknown theme groups under Other, never dropped; `group_of` for a
  sub-theme inherits its primary tag's bucket.
- `tests/test_tag_filter_sql.py` — `resolve_tag` exact/alias match against
  `vocabulary='tags'`, degrading to a literal `{"tag": ...}` scope (never an
  ambiguous-candidate list) when unmatched; tag join alias and param order;
  **tag AND theme produce two separate joins**, not a merged `IN` list (the
  regression that matters); no `group_by="tag"` dimension exists.

**Extended**

- `tests/test_database_tools.py` — all 8 queries from §10.1 over stubbed readers;
  `data["applied"]` echoes canonical names; terminal vs fall-through for each
  `error_kind`; zero-result with resolved filters renders an honest `0`;
  multi-filter `author × bundle × theme × tag × date`.
- `tests/test_database_planner.py` — planner emits `resolve_entity` before a
  filtered call for a fuzzy name, and skips it for an exact bundle name.
- `tests/test_counting.py` — the unresolved-theme case is now terminal.

---

## 14. Verification

```bash
python -m pytest -q                              # full offline suite
python -m pytest -q tests/test_entity_resolution.py tests/test_theme_groups.py \
                    tests/test_tag_filter_sql.py tests/test_database_tools.py
```

Then against real MySQL, outside pytest:

```bash
python -m app.local_tests.run_ingestion_test     # isolated local_test_* tables
python scripts/reclassify_theme_rows.py          # backfill theme_group on existing rows
```

The backfill matters: `theme_group` is `NULL` on every row written before
`f1ff99b`, so confirm it is populated before trusting any main/other split against
production data.

Finally, walk all 8 queries plus the two edge cases through `POST /chat`, checking
that each answer names the resolved entities. Run the `code-review-graph`
`detect_changes` and `get_impact_radius` tools against `_catalog_filters` before
merging — it backs every catalog read, including the id-scope path used by scoped
summarization.
