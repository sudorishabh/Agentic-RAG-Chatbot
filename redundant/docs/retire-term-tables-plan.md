# Retiring the term tables: MySQL as the single source of truth

Plan for removing `terms`, `term_aliases` and `documents_term` from MySQL, making
`documents_theme` / `documents_tag` the authority for theme and tag data keyed by
**name**, and leaving taxonomy UUIDs to the Qdrant payload only.

Supersedes the `terms`-based parts of
[database-retrieval-redesign.md](database-retrieval-redesign.md) §4.1, §5, §6.

---

## 1. Why

The catalog currently stores taxonomy links twice, indirectly:

- **`documents_term`** — 15,443 rows of `(document_id, term_uuid, role)` across
  **24 distinct roles** (themes, tags, stakeholders, divisions, regions, areas,
  partners, programmes, languages, audiences).
- **`terms`** — the dictionary mapping `term_uuid` → name. **0 rows.**

So every one of those 15,443 links points at an identifier nothing can resolve.
The design's four intended benefits — rename survival, parent→child expansion,
one table for every vocabulary, and themes that exist before any document uses
them — all require a `taxonomy_term` crawl that has never run in this
environment. None of them are delivered today.

Meanwhile the same information is already stored **as readable names**, twice:

- `documents_theme(theme, theme_type, parent, theme_group)` — 2,493 rows,
  26 real themes, hierarchy and Main/Other already materialized.
- `documents.raw_meta` — the full per-field payload as names, e.g.
  `field_tags: ["Solid waste", "Urban waste", …]`, `field_theme: ["Waste"]`,
  `field_division: […]`, `field_article_stakeholder: […]`.

The indirection is not merely unused — it is actively harmful. `list_themes`
reads `terms`, finds it empty, returns `ok=False`, and "how many themes are
there?" falls through to vector search, which then refuses because
`GROUNDED_SYSTEM_PROMPT` rule 8 forbids stating totals. Three layers away from
the actual cause.

**Decision:** delete the UUID indirection. Names become identity. This removes a
second copy of data, not the data.

### 1.1 What is genuinely given up

1. **Rename self-healing.** Renaming a Drupal taxonomy term does not bump the
   referencing nodes' `changed` marks, so incremental ingestion will not notice;
   `documents_theme` keeps the old name until those documents are re-ingested.
   Measured against the real 26-theme pool, this degrades well — see §6.
2. **Zero-document themes disappear from listings.** `app/data.json` names 36
   themes; only 26 appear on documents. "How many themes are there?" will answer
   26. That is the direct consequence of "the actual data comes from MySQL".

No silent wrong answers arise from either. That property is load-bearing and is
what §6 verifies.

---

## 2. Target shape

| concern | today | after |
|---|---|---|
| theme identity | `term_uuid` via `documents_term` → `terms` | `documents_theme.theme` (name) |
| theme hierarchy | `terms.parent_uuid`, walked transitively | `documents_theme.parent` (one level — see §3.3) |
| Main / Other | `app/data.json` read at query time | `documents_theme.theme_group` |
| theme matching | substring `LIKE` fallback | exact name **or** `parent` (§3.3) |
| tag storage | `documents_term` where role=`field_tags` | **new** `documents_tag` facet |
| taxonomy UUIDs | MySQL + Qdrant payload | **Qdrant payload only** |
| `app/data.json` | classifier *and* query-time source | ingest-time reference only |

`app/data.json` keeps exactly one job: at ingest, `theme_taxonomy.classify()`
turns raw theme names into `(theme_type, parent, theme_group)` rows. Those
columns are the materialized result; queries read the columns, never the file.

---

## 3. Phase 1 — stop reading (tables still exist and are still written)

Reversible throughout. Nothing is dropped.

### 3.1 Theme vocabulary reader — `app/catalog/queries.py`

```python
def theme_vocabulary(*, limit: int = 500) -> list[dict[str, Any]]
```

`SELECT DISTINCT theme, theme_type, parent, theme_group FROM documents_theme`,
ordered by name, excluding junk values (§5.1). Replaces `terms.list_themes()`.

### 3.2 `list_themes` reads MySQL — `app/retrieval/structured/tools.py`

Group on `theme_group` (`NULL` → Other) instead of calling
`theme_taxonomy.group_of()`. **This is the fix for the reported bug**: real
themes instead of `ok=False`.

`theme_taxonomy.group_of` / `themes_by_group` remain — they are still the ingest
classifier — but `tools.py` stops importing them.

**Since revised — top-level themes only.** `list_themes` has two shapes:

| call | answers | result here |
|---|---|---|
| `list_themes()` | "what themes are there?" — `theme_type='primary'` only, Main then Other | **10** (7 main + 3 other) |
| `list_themes(children=True)` | "what are the sub-themes?" — grouped by parent | **16** across 5 parents |
| `list_themes(children=True, parent="Energy")` | one theme's children | 4 |

Sub-themes are excluded from the default listing because including them both
overstates the count (26 vs 10) and flattens the hierarchy the taxonomy exists
to express — "Air" and "Waste" are not peers of "Climate Change".

Two distinctions the children path keeps separate: a **real theme with no
children** answers plainly (`"Climate Change has no sub-themes."`, `ok=True`)
rather than falling through, because that is a true and useful statement; a
**name that is not a theme at all** is an `unresolved` miss.

Routing: the classifier gains a `theme_children` boolean
(`QueryAnalysis`/`QueryUnderstanding`/`StructuredQuery` + both prompts). The v1
planner also treats a *named theme* in a `list_themes` request as implying its
children — "what's under Environment?" has no other sensible reading — so that
phrasing works even when the classifier leaves the flag unset.

### 3.3 Theme filtering by name, with parent expansion

Replace the `term_uuids` join and the `theme LIKE` fallback in
`_catalog_filters`, `distribution("theme")` and `document_ids_in_scope` with a
single `documents_theme` join matching:

```sql
JOIN documents_theme c ON c.document_id = s.document_id
WHERE c.theme = %s OR c.parent = %s      -- exact name, or a sub-theme of it
```

**This is strictly more correct than today's substring match**, which is wrong in
both directions. Measured for `theme="Environment"`:

| | documents | behaviour |
|---|---|---|
| current `LIKE '%Environment%'` | 472 | **misses** all 6 sub-themes (Air, Water, Land, Waste, Microbes, Forest & Biodiversity); **wrongly merges** two separate top-level themes — *Environment and Public Health* (62 docs, main) and *Environment Education* (3 docs, **other**) |
| proposed exact-or-parent | **625** | includes the sub-themes, excludes the unrelated siblings |

Exact matching is only safe *because* fuzzy resolution now canonicalizes the name
before it reaches SQL (see redesign doc §4.0) — the substring match was
compensating for user spelling, which is no longer its job.

One level of `parent` is sufficient, not a compromise: `theme_taxonomy` flattens
deeper nesting so `parent` always names the **primary tag**, meaning
`parent = 'Environment'` already covers that tag's whole subtree. This replaces
`terms.descendant_uuids`.

### 3.4 Theme candidates — `app/retrieval/structured/resolve.py`

`_theme_candidates` drops its `terms`-then-facet two-step and reads
`theme_vocabulary()` directly. The §4.1 "operational dependency on a crawl"
caveat is deleted from the redesign doc — that failure mode ceases to exist.

### 3.5 `documents_tag` facet — the one genuinely new table

`documents_term` is currently the **only** MySQL tag storage, so it cannot be
removed without replacing it. The existing machinery makes this ~5 lines:

- `STATE_FACETS: tuple[str, ...] = ("author", "tag")` — `_STATE_CHILD_DDL`,
  `_replace_facet` and the `ON DELETE CASCADE` are already generic
- `StateRecord.tags: list[str]`, written via
  `_replace_facet(cur, table, "tag", record.document_id, record.tags)`
- `canonical.drupal_facets()` already extracts `tags` — wire it into the record
- `_catalog_filters` tag join moves from `documents_term` to `documents_tag`
- `filters.resolve_tag` matches the name directly

This deletes an awkwardness introduced in earlier work: tag no longer needs
special-casing as "the filter with no fallback", so `_scope_guard` /
`_empty_result_miss` become uniform across author, theme and tag.

Backfill for existing documents comes from `raw_meta` (§5.2) — no re-crawl.

### 3.6 Vector path — `app/retrieval/understanding/filters.py`

`_theme_condition` drops the `resolve_terms` / `descendant_uuids` lookup and
filters on the `categories` (name) leg. This is a **deletion**: the name leg
already exists and the docstring already documents it as the degradation path.
Qdrant payloads keep `theme_ids` / `term_ids` / `categories` unchanged — written
at ingest from `entity_refs`, with no MySQL involvement. That is the "terms for
vector store only" end state.

`app/pipeline/summarize.py` scoped-theme retrieval follows §3.3.

---

## 4. Phase 2 — stop writing (tables inert)

**Verify real queries before this point.** After Phase 2 the tables still exist
but hold only stale data; after Phase 3 they are gone.

Delete:

| target | notes |
|---|---|
| `app/catalog/terms.py` | whole module |
| `_sync_term` in `app/ingestion/pipeline.py` | plus the `taxonomy_term` delete branch |
| `TermLink` (`catalog/models.py`), `StateRecord.term_links`, its writes in `state.py` | |
| `state.documents_for_term` | |
| `app/catalog/payload_refresh.py` rename machinery | keyed on term UUIDs; §6 replaces it |
| `terms` / `term_aliases` / `documents_term` DDL in `schema.py` | plus `TERM_TABLE`, `ALIAS_TABLE`, `THEME_VOCABULARY`, `TAG_VOCABULARY` |
| term-table exports in `app/catalog/__init__.py` | |
| term snapshots in `app/local_tests/db_checks.py`, `run_ingestion_test.py` | |

`scripts/rename_catalog_tables.py` and `scripts/reclassify_theme_rows.py` stay —
the first is a historical migration, the second still backfills `theme_group`.

Note: dropping `payload_refresh` means a rename no longer rewrites Qdrant payload
display names. §6's script covers MySQL; payload names go stale until reindex.
Acceptable because the vector path matches on `categories` with an OR of name
variants, so a stale payload name still matches the old name.

---

## 5. Data cleanup (alongside Phase 1)

### 5.1 The `'False'` theme — an ingestion bug

`documents_theme` holds **404 rows** whose theme is the literal string `'False'`
— a boolean leaking into the theme facet. It is the *entire*
`theme_group IS NULL` population, and would surface as a theme the moment
`list_themes` reads MySQL.

- Guard in `theme_taxonomy.classify()` / `canonical.drupal_facets()`: reject
  non-string and boolean-literal theme values.
- One-off cleanup: `DELETE FROM documents_theme WHERE theme IN ('False','True')`.
- `theme_vocabulary()` filters defensively regardless.

### 5.2 Tag backfill from `raw_meta`

`scripts/backfill_tag_facet.py` — read `raw_meta` per document, extract the
tag-named fields via the existing `canonical.TAG_HINTS`, write `documents_tag`.
No network, no re-crawl; the names are already stored.

---

## 6. Renames — what replaces UUID identity

Verified against the real 26-theme pool with the shipped fuzzy resolver:

| rename | resolves to | outcome |
|---|---|---|
| Climate Change → "Climate Action" | Climate Change (0.71) | **ambiguous** → clarification, correct theme first |
| Sustainable Habitat → "Sustainable Cities" | Sustainable Habitat (0.76) | ambiguous → clarification |
| Environment and Public Health → "Environmental Health" | correct (0.82) | ambiguous → clarification |
| Waste → "Waste Management" | Waste (0.66) | ambiguous → clarification |
| Transport → "Green Mobility" (no shared word) | — (0.48) | **explicit miss**: "No theme matching 'Green Mobility' found." |

**No case produces a silently wrong count.** A partial rename costs one
confirmation turn; a total rewrite is an honest miss.

Repair is a single statement, because names are the identity:

```sql
UPDATE documents_theme SET theme = 'new name' WHERE theme = 'old name';
```

`scripts/rename_theme.py <old> <new>` wraps it (building on the existing
per-document `state.rename_theme_facet`). Its docstring must state the **two-step
procedure**: run the script, *then* update `app/data.json`, or newly ingested
documents get the new name with no `theme_group` and land under "Other".

A `theme_aliases` table was considered and **rejected**: it guards a failure mode
that already degrades safely, and reintroduces the taxonomy side-table this plan
exists to remove.

---

## 7. Phase 3 — drop the tables (you run this)

`scripts/drop_term_tables.py`, deliberately not wired into `ensure_tables()`:

```sql
DROP TABLE IF EXISTS documents_term;   -- 15,443 rows
DROP TABLE IF EXISTS terms;            -- 0 rows
DROP TABLE IF EXISTS term_aliases;
```

Irreversible without a full re-ingest, so it stays a deliberate manual step
taken after Phase 1–2 are verified in place.

---

## 8. Step sequence

| # | Step | Phase | Status |
|---|---|---|---|
| 1 | `theme_vocabulary()` reader + artefact filter | 1 | done |
| 2 | `list_themes` reads `theme_group` — **fixes the reported bug** | 1 | done |
| 3 | Theme filtering: exact name or `parent`, across all three query builders | 1 | done |
| 4 | `_theme_candidates` reads `theme_vocabulary()` | 1 | done |
| 5 | `documents_tag` facet: DDL, write path, filter join, `find_tag` | 1 | done |
| 6 | Tag backfill from `raw_meta` (`scripts/backfill_tag_facet.py`) | 1 | done, **applied** |
| 7 | `_theme_condition` name-only; `summarize` scoped theme | 1 | done |
| 8 | Boolean-artefact ingestion guard + cleanup | 1 | done, **applied** |
| 9 | Delete `terms.py`, `_sync_term`, `TermLink`, `documents_for_term`, `payload_refresh` | 2 | done |
| 10 | Remove term DDL + constants from `schema.py`; update `__init__` | 2 | done |
| 11 | `scripts/rename_theme.py` | 2 | done |
| 12 | `scripts/drop_term_tables.py` | 3 | **yours to run** |

### 8.1 Two corrections found while building

- **`find_tag` replaced a vocabulary scan.** The first cut matched tags by loading
  `distinct_tags()` and comparing in Python, with a 2000-row cap. This corpus has
  **2,364 distinct tags**, so every tag sorting after ~"T" was silently judged a
  miss. Since tags are matched *exactly*, the fix is a targeted indexed lookup
  (`queries.find_tag`) with no vocabulary load and no cap to get wrong.
- **The feature flag gates reporting, not matching.** `_resolve_name` runs
  unconditionally: theme and tag filters match names exactly in SQL, so
  canonicalizing is now part of how filtering *works*. `entity_resolution_enabled`
  decides only whether an imperfect match becomes a clarification / terminal
  message or quietly falls through — which is what keeps flag-off behaviour
  identical to before (an unrecognized filter falls through rather than answering
  a bare `0`).

### 8.2 Data-quality notes for you

- The backfill wrote **4,425 tag links (2,364 distinct)** and removed the **404**
  boolean-artefact theme rows.
- Some tags look like un-split delimited blobs, e.g.
  `"3D printing; Additive manufacturing; Biomass; Cellulose; …"` as a single tag,
  and one begins `";s Rice straw biomass"`. That is upstream field data, not a
  bug in this change — but splitting on `;` at ingest would materially improve tag
  quality if you want it.

---

## 9. Test impact

Substantial — the term tables are woven through the suite. Expect to rewrite:

| file | change |
|---|---|
| `tests/test_term_catalog.py` | **delete** (tests `terms.py`) |
| `tests/test_theme_queries.py` | drop `resolve_terms` / `descendant_uuids` / term-join tests; add exact-or-parent SQL assertions |
| `tests/test_database_registry.py` | `resolve_theme` / `resolve_tag` now name-based |
| `tests/test_database_tools.py` | `resolve_theme_ok` / `resolve_tag_ok` fixtures; `list_themes` reads `theme_group` |
| `tests/test_filter_resolution.py` | `_theme_candidates` mocks move to `theme_vocabulary` |
| `tests/test_entity_resolution.py` | same |
| `tests/test_catalog_readers.py` | term-join assertions → theme-join |
| `tests/test_catalog_schema_migration.py` | term DDL assertions removed; `documents_tag` added |
| `tests/test_counting.py` | `resolve_terms` mocks removed |
| `tests/test_theme_rows.py` | mostly unaffected (already `documents_theme`) |

New: `documents_tag` facet write/filter tests, `theme_vocabulary` tests,
exact-or-parent expansion tests, `'False'` rejection tests.

---

## 10. Verification

```bash
python -m pytest -q                      # full offline suite
```

Against the live DB, before and after each phase:

```sql
-- must return 26 (22 main + 4 other), not 0
SELECT theme_group, COUNT(DISTINCT theme) FROM documents_theme
 WHERE theme NOT IN ('False','True') GROUP BY theme_group;

-- must return 625, not 472
SELECT COUNT(DISTINCT d.document_id) FROM documents d
  JOIN documents_theme t ON t.document_id = d.document_id
 WHERE d.source_type='website' AND d.entity_type='node'
   AND (t.theme='Environment' OR t.parent='Environment');

-- must be non-zero after the backfill
SELECT COUNT(*) FROM documents_tag;
```

Then through `POST /chat`, with `entity_resolution_enabled=true`:

- "how many themes are there" → 22 main + 4 other, sectioned (**the reported bug**)
- "how many posts under Environment" → 625, sub-themes included
- "how many posts under Environment Education" → 3, *not* merged into Environment
- "how many posts tagged waste management" → answered from `documents_tag`
- "how many posts by <misspelled real author>" → canonical name, correct count
- "how many posts under Green Mobility" → explicit miss, no fabricated zero
