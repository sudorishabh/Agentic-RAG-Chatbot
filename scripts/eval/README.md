# Eval golden dataset

`golden.jsonl` holds labeled queries used by the offline eval runner
(`run_eval.py`) to gate quality changes: one JSON object per line, five item
classes. Current seed: ~37 items; target per the architecture plan: grow to
150–250 as the corpus and features settle.

## Item schema

Common fields:

| Field | Meaning |
| --- | --- |
| `id` | unique, `<prefix>-NNN` (`rte`/`ana`/`ret`/`gen`/`ref`) |
| `class` | `routing` \| `analytics` \| `retrieval` \| `generation` \| `unanswerable` |
| `question` | the user query, verbatim |
| `expect` | class-specific expectations (below) |
| `notes` | optional; provenance, review status, caveats |

### `routing` — query-understanding labels only (no retrieval/LLM answer)

`expect` compares against the unified `QueryAnalysis`. Exact-match fields
(case-insensitive): `intent`, `operation`, `bundle`, `group_by`,
`answer_format`, `source_type`, `date_from`, `date_to`. Substring fields:
`theme_contains`, `author_contains`, `title_contains_ci` (matched against the
extracted theme/author/title_contains). Omitted fields are not checked.

### `analytics` — numbers must match SQL exactly (target: 100%)

`expect.sql_check` names an `app.ingestion.state` reader (`count_documents`,
`distribution`, `list_documents`) plus `kwargs`. The runner executes it
independently (dates parsed to datetimes; `source_type="website"`,
`entity_type="node"` baked in, matching the structured route) and asserts the
pipeline's answer contains the same numbers/titles: the exact count for
`count_documents`, each of the top-3 `(value, count)` pairs for
`distribution`, the most recent title for `list_documents`.

### `retrieval` — ranking quality

`expect.relevant_document_ids`: the runner calls `search_blocks()` and
computes recall@k and MRR over the returned blocks' `document_id`s; also
records the website-lead rate for the source-preference eval.

### `generation` — answer content and shape

`must_contain` / `must_not_contain` (case-insensitive substrings),
`format` (`table` = markdown header row present; `timeline` = dated lines;
`summary` = length-bounded), `citations_required` (at least one `[n]`).

### `unanswerable` — refusal correctness

`expect.refusal: true` — the answer must equal `prompts.REFUSAL` exactly.

## Adding items

1. Pull real anchors from the catalog (read-only MySQL): bundles, categories,
   authors, titles + `document_id`s — invented content makes labels worthless.
2. Keep the §11.6 boundary pairs pattern: for every catalog-shaped phrasing
   add its content-shaped twin (and vice versa) so routing drift is caught.
3. `relevant_document_ids` and generation `must_contain` need a human who
   knows the content to validate — mark unreviewed items with `notes`.

## Seed-set caveats (2026-07-10)

- Authored while ingestion was mid-run: only `news`, `feature_articles`,
  `completed_projects` were ingested; `taxonomy_term` was still empty, so
  theme-scoped **analytics** items are deliberately absent (a theme count
  falls through to semantic search by design while terms don't resolve —
  add such items once the taxonomy mirror is populated).
- Analytics expectations recompute live, so corpus growth doesn't stale them;
  retrieval/generation items reference specific 2026 articles and should be
  re-checked if those documents are ever unpublished.
- All `generation` items and `retrieval` relevance labels are assistant-drafted
  from catalog titles and await user review (`notes` marks them).
