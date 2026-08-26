# MySQL schema

Every table, what it stores, why it exists, and its columns.

**Source of truth:** [app/catalog/schema.py](../app/catalog/schema.py) — all DDL and
migrations. Nothing else in the codebase creates or alters a table.
**Row counts** below are from the handover dataset (`arc_db`), for orientation.

---

## Conventions

**Table names are derived, not fixed.** The prefix comes from the
`ingest_state_table` setting (default `documents`) and the log table from
`ingest_log_table` (default `ingest_log`). Both pass through
`db.safe_table()` — a name that isn't alphanumeric-plus-underscore falls back to
the default, so a bad setting can't become a SQL-injection vector in the
f-string DDL.

**All DDL is idempotent.** Each group has an `ensure_*()` function using
`CREATE TABLE IF NOT EXISTS` plus `_ensure_column()` for columns added after a
table shipped. Any ingestion run applies them; running twice is a no-op.

**Two deliberate design rules govern foreign keys:**

| Rule | Tables | Reason |
| --- | --- | --- |
| **Cascade** from `documents` | the 4 facet children | a document's facets are meaningless without it, and a reindex rewrites them wholesale |
| **No FK at all** | everything else | must survive a catalogue reset; must not lose rows when content returns under a different id; and a failed document must never appear as a catalogued one in an analytical read |

That second rule is why the retry, dead-link, enrichment and knowledge tables
are standalone. A placeholder row in `documents` would be counted as a real
document by every count, list and distribution query.

**Engine/charset:** `InnoDB`, `utf8mb4` throughout.

---

## Table index

| Group | Tables | Rows (handover) |
| --- | --- | --- |
| [Core catalogue](#1-core-catalogue) | `documents` + 4 facet children | 12,003 + 42,210 |
| [Ingestion control](#2-ingestion-control) | `_retry`, `_dead_link`, `ingest_log` | 25,734 |
| [Caches](#3-caches) | `_enrichment`, `_entity_extraction` | 8,868 |
| [Date resolution](#4-date-resolution) | `_date_decision` | 4,933 |
| [Knowledge — identity](#5-knowledge--identity) | `_entity`, `_entity_alias`, `_entity_identifier`, `_entity_mention`, `_entity_resolution_decision` | 6,953 |
| [Knowledge — claims](#6-knowledge--claims) | `_assertion`, `_assertion_rejection`, `_assertion_link`, `_predicate_candidate` | 1,950 |
| [Knowledge — runs](#7-knowledge--runs) | `_knowledge_run` | 11,238 |

---

## 1. Core catalogue

### `documents` — 12,003 rows

**Stores** one row per ingested document: a website page, a custom block, or a
PDF attachment. This is the system of record for what the corpus contains.

**Why it exists** — three jobs at once, which is unusual but deliberate:

1. **The crawl cursor.** `MAX(changed_mark)` per bundle is the incremental
   window's lower bound, so this table is what makes a sweep resumable.
2. **Change detection.** `fingerprint` decides whether to re-extract;
   `content_hash` decides whether to re-embed; `pipeline_version` decides
   whether to rebuild after a code change.
3. **The relational answer path.** Counting and listing questions are answered
   here rather than from passages, so a count is a fact rather than something a
   model inferred from prose.

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | node uuid, file uuid, or `inbody:<sha1-of-url>` |
| `source_type` | varchar(32) | `website` \| `pdf_attachment` |
| `source_key` | varchar(1024) | page URL or file URL |
| `bundle` | varchar(128) | content type; an attachment inherits its parent's |
| `entity_type` | varchar(32) | `node` \| `block_content`; NULL for attachments. Content counts filter on it so blocks don't count as documents |
| `fingerprint` | varchar(128) | the source's `changed` stamp — gates re-extraction |
| `content_hash` | varchar(64) | SHA-256 of **body text only** — gates re-embedding |
| `doc_version` | int | incremented on every real content change |
| `pipeline_version` | varchar(32) | which code built this. Differs → rebuild even if content is identical |
| `changed_mark` | bigint | unix `changed` — the cursor input |
| `published_at` | datetime | the best known **publication** date. Everything ranks, filters and orders on this |
| `published_at_source` | varchar(16) | where that value came from: `created` \| `cms_field` \| `document_text` |
| `published_at_precision` | varchar(8) | how precise it is: `year` \| `month` \| `day` |
| `document_published_at` | datetime | the date the **document itself states**. NULL unless it says so — never inferred. Nothing reads it yet, and nothing writes it |
| `title`, `url` | varchar(1024) | so list/lookup needs no live fetch |
| `raw_meta` | json | lossless source metadata; the only home for fields with no column |
| `indexed_at` | datetime | NULL until a real index happens |
| `updated_at` | datetime | |
| `size`, `mtime_ns` | bigint | **vestigial** — from the removed local-PDF pipeline |

Indexes: `idx_source_type`, `idx_bundle (source_type, bundle)`, `idx_pipeline_version`.

> **The dates are the subtlest thing in this schema.** All ten TERI annual
> reports are attachments on one page, so all ten share
> `published_at = 2022-02-09`. That is the page's date and the publication date
> of no edition. A full scrape of the live JSON:API confirmed the site itself has
> no per-PDF date field, so being faithful to Drupal here is not the same as
> being right. `document_published_at` exists to hold the real answer where a
> document states one; an audit found none of the ten do, so all ten are NULL.
>
> **`published_at_source` is what makes a bare value readable.** Until it existed,
> an import timestamp shared by 646 completed projects and a date the publisher
> stated looked identical. The current split over 12,003 documents:
>
> | | | |
> | --- | ---: | --- |
> | `cms_field` | 2,770 | the source states this date — **verified** |
> | `document_text` | 4 | quoted from the PDF's own text and checked against it |
> | `created` | 9,229 | a record or page stamp; ~2,400 of them import batches |
>
> It uses `VALUES()` in the upsert rather than `COALESCE()`, unlike
> `document_published_at` below: both columns describe `published_at`, which is
> overwritten outright, and a provenance that outlived the value it described
> would read as evidence for a date it was never about. For the same reason
> `state.backfill_facets` **clears** them — it lifts `published_at` out of a chunk
> payload, which carries the value and not its origin.
>
> **`published_at_precision = 'year'` means the day is a marker, not a claim.**
> 389 research papers state only a year (`field_rpaper_year`), and the column must
> hold some day, so it holds 1 January. This is the only column that says so, and
> it is carried to the chunk payload for exactly one reason: the answer layer is
> the only place that can stop the marker being read as a day. A reader that
> ignores it reports an invented January publication. Absent means a full date,
> which is true of every other document — which is why adding it needed no
> `PAYLOAD` version bump.

### The four facet children

All four `CASCADE` on delete from `documents`, and all four are **replaced
wholesale** on every ingest — so a reindex heals drift and a document that loses
its last theme is cleaned up.

**Why separate tables rather than columns:** each is multi-valued, and one row
per `(document, value)` is what lets `COUNT(DISTINCT document_id)` count
documents correctly regardless of how many values each has.

#### `documents_author` — 4,683 rows

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | → `documents` |
| `author` | varchar(255) **PK** | as the CMS supplies it |
| `author_norm` | varchar(255) | normalised form; counting distinct people uses this, because the raw values spell one person several ways |

#### `documents_tag` — 22,778 rows

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | → `documents` |
| `tag` | varchar(255) **PK** | freeform, long-tail. Matched **exactly**, never fuzzily — thousands of near-duplicates would make similarity ranking flag an ambiguity on almost every query |

#### `documents_theme` — 11,120 rows

The one facet with hierarchy, classified at ingest against
[app/theme_structure.json](../app/theme_structure.json).

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | → `documents` |
| `theme` | varchar(255) **PK** | display name as stored |
| `theme_type` | enum(`primary`,`sub`) | position within its bucket |
| `parent` | varchar(255) | the primary tag a sub-theme hangs off; NULL for a primary tag |
| `theme_group` | enum(`main`,`other`) | which top-level bucket it traces back to. Tracked separately because two primary tags can share `(primary, NULL)` while coming from different buckets |

> Only themes the document **actually carries** get a row. A sub-theme's parent
> is recorded as a reference, never materialised as an extra row — so a document
> tagged only "Energy Access" is never credited with "Energy". Theme filters
> match `theme = X OR parent = X` in SQL, which is how scoping to a primary tag
> picks up its children.

#### `documents_attachment` — 3,629 rows

| Column | Type | Notes |
| --- | --- | --- |
| `file_uuid` | varchar(255) **PK** | the attachment's own document id |
| `document_id` | varchar(255) **PK** | the page claiming it → `documents` |
| `origin` | varchar(16) | `attachment` (CMS file field) \| `inbody` (harvested from rich text) |
| `url`, `filename` | | first link wins per file — an explicit attachment ref outranks a later in-body sighting |

> **The composite key is the whole point.** One PDF is reachable from several
> pages, so deleting a page must only end *that page's* claim. An attachment is
> deleted when it has no rows left here — which is the only mechanism in the
> system that ever deletes one.

---

## 2. Ingestion control

### `documents_retry` — 183 rows

**Stores** documents a run reached but did not index.

**Why it exists** — the crawl cursor is `MAX(changed_mark)` over rows that
*exist*, and a row is written only on success. So an errored document left no
trace while every document processed *after* it did, pushing the next run's
window past the hole. Editing the source in the CMS was the only way back. A row
here floors the cursor at the earliest unresolved failure per bundle; success
deletes the row and the floor lifts itself.

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | |
| `source_type`, `bundle` | | `bundle` is what the floor is computed per |
| `changed_mark` | bigint | mirrors the column it's compared against. NULL can't position a cursor |
| `outcome` | varchar(16) | `error` \| `skipped` \| `reindex` (an operator request, kept distinct so the queue can be triaged) |
| `attempts` | int | counts every run that tried |
| `error` | text | |
| `first_seen`, `updated_at` | datetime | `first_seen` survives retries, so how long something has been failing stays readable |

Index: `idx_retry_floor (bundle, changed_mark)` — the floor is one grouped read.

> **No attempt cap, deliberately.** A permanently failing document holds its
> bundle's floor down forever. The cost is a larger scan per run, not lost work —
> the trade for "a temporary failure stays visible without anyone editing the
> source".

### `documents_dead_link` — 61 rows

**Stores** attachment URLs the site answers a 4xx for.

**Why it exists** — old page HTML links tender notices and RFQs that were taken
down once they closed. The link stays in the text forever, so every sweep
harvested it, downloaded it, and got the same 404 — work that can never succeed,
and which produced no document row and therefore no fingerprint to compare
against next time.

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | the attachment's file uuid |
| `fingerprint` | varchar(128) | **the expiry mechanism** — see below |
| `url` | varchar(1024) | |
| `status` | smallint | the 4xx code. Only client errors are recorded; timeouts and 5xx stay retryable because they clear on their own |
| `attempts` | int | resets when the fingerprint changes |
| `first_seen`, `updated_at` | datetime | |

> **Qualified by fingerprint, not permanent.** The marker suppresses a download
> only while the fingerprint still matches the one that failed — so the retry
> comes back exactly when something could have changed. Re-upload the file and
> save the node, and its real attachments revive; edit the body link and the
> in-body PDF's URL-derived id changes into a row that was never marked dead.

### `ingest_log` — 25,490 rows

**Stores** one row per document per run: what happened and why.

**Why it exists** — `documents` is overwritten in place, so it can only say what
is true *now*. This is the append-only history: which run touched what, what
status it reached, how many chunks it produced, and the error if it failed.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | bigint **PK** | auto-increment; `ORDER BY id DESC` is "most recent" |
| `run_id` | varchar(64) | hex uuid per sweep — groups every row from one run |
| `document_id`, `source_type` | | |
| `source_path`, `source_url`, `bundle`, `tags`, `title` | | denormalised for readability without joins |
| `status` | varchar(32) | `indexed` \| `unchanged` \| `unchanged_content` \| `deleted` \| `skipped` \| `error` |
| `doc_version`, `chunks_indexed` | int | |
| `fingerprint`, `content_hash` | | what the decision was made on |
| `error_message` | text | |
| `event_time` | datetime | pruned after `ingest_log_retention_days` (default 90) |

Indexes: `idx_document`, `idx_source_type`, `idx_event_time`, `idx_run`.

> `ingest_log_unchanged` defaults **off**. On an incremental sweep almost every
> document is unchanged, so logging each one is one INSERT+commit per document
> and the main driver of this table's growth. The run tally already reports the
> count.

---

## 3. Caches

Both are keyed by **content hash rather than document id**, and both are
deliberately FK-free, for the same three reasons: they must survive a catalogue
reset (the usual way to force a reindex, and exactly when re-paying hurts most);
documents with identical bodies share one row and pay once; and content that
returns under a different id must not have lost its row to a cascade.

The trade is that orphaned rows are pruned rather than cascaded — a maintenance
task, not a correctness one.

### `documents_enrichment` — 8,867 rows

**Stores** the LLM-generated per-document abstract.

**Why it exists** — the abstract replaces a query-time stand-in (a document's
lead chunk, which for a long report is its cover page). Generating it at ingest
sees the whole document and is paid once per content hash instead of on every
query that touches it.

| Column | Type | Notes |
| --- | --- | --- |
| `content_hash` | varchar(64) **PK** | |
| `version` | varchar(64) | fingerprint of the prompts + sizing + model. A mismatch reads as a **miss**, so editing a prompt re-enriches automatically instead of serving stale output |
| `abstract` | text | NULL when generation failed or was skipped |
| `attempts` | int | without this, a document that always fails is retried at full cost every sweep forever |
| `last_error` | text | |
| `updated_at` | datetime | |

### `documents_entity_extraction` — 1 row

**Stores** which chunks have already had entity extraction run.

**Why it exists** — mention extraction is the most expensive deterministic stage
in the knowledge layer. Keyed by the chunk's content hash, not its id, so a
reindex whose paragraphs are unchanged still hits.

| Column | Type | Notes |
| --- | --- | --- |
| `content_hash` | varchar(64) **PK** | |
| `extraction_key` | varchar(64) | covers extractor version **and** the gazetteer, so newer code never serves output it wouldn't produce |
| `extractor_version` | varchar(64) | |
| `mention_count` | int | |
| `attempts`, `last_error`, `updated_at` | | |

---

## 4. Date resolution

### `documents_date_decision` — 4,933 rows

**Stores** how each document's publication date was decided, and the evidence.

**Why it exists** — two jobs. It's the **audit trail** ("why does this document
carry this date?") and the **review queue** (a case the resolver couldn't settle
safely lands here rather than moving a date). Kept out of `documents` because
`extra` fields there flow into the Qdrant chunk payloads, and confidence scores
and model verdicts must not reach retrieval.

**Both source types, but not every document.** It began as PDF-only; website
documents now land here too, so one table and one queue answer the question for
the whole corpus. A row is written only when the source *offered* a publication
date, because a row for the ~5,500 that state nothing would cost an INSERT and a
commit each to record what `documents.published_at_source` already says.

Website rows are also **not yet complete**: the 1,436 present are the ones the
backfill corrected, since it writes a row only for a document whose date it moves.
The further ~1,562 whose source already agreed — `cms_field_matches_created` and
`year_already_correct` — get theirs the next time each is ingested, taking the
website total to roughly 3,000. The audit trail is therefore behind the provenance
column, which covers all 12,003 today.

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | |
| `origin` | varchar(16) | `attachment` \| `inbody` \| `website` |
| `bundle`, `node_uuid` | | the page it hangs off; for a website record, itself, so the join every report makes resolves rather than dangling |
| `page_pdf_count` | int | one PDF vs a shelf — the single most informative signal |
| `current_published_at` | datetime | the page's own date, so a row reads "would have been X, assigned Y" |
| `candidate_date` | datetime | what was proposed |
| `date_type` | varchar(16) | `publication` \| `upload` \| `authoring` \| `edition` \| `event` \| `notification` \| `effective` \| `unknown`. **Only `publication` may override** |
| `edition_label` | varchar(64) | e.g. `2024-25` — a label, never a date |
| `candidate_source` | varchar(32) | `node_created` \| `llm_publication` \| a source field name such as `field_news_date` \| … |
| `confidence` | decimal(4,3) | `1.000` for a CMS field — a transcription of what the source states, not an inference from evidence |
| `action` | varchar(24) | `keep_page_date` \| `needs_manual_review` \| `propose_override` |
| `rule` | varchar(48) | which rule fired. Website rows use `cms_publication_field`, `cms_field_matches_created`, `year_already_correct` |
| `decided_by` | varchar(16) | `deterministic` \| `llm` |
| `evidence` | text | the human-readable justification |
| `llm_raw` | json | the model's full verdict |
| `prompt_version` | varchar(32) | so a rerun under new rules is distinguishable |
| `url`, `filename`, `updated_at` | | |

Indexes: `idx_action`, `idx_decided_by`, `idx_rule` — `WHERE action='needs_manual_review'` is the review queue.

> **Not in the handover:** `documents_date_candidate`, the Phase-0 shadow
> measurement table. It records what every date source *would* say; it's
> regenerable and read only by report scripts, so its absence is expected.

---

## 5. Knowledge — identity

Turns names in text into canonical entities. **Nothing here cascades from
`documents`**: deleting one news item must not destroy the identity of a person
named in three hundred PDFs. Orphans are reportable and prunable, never cascaded.

### `documents_entity` — 2,451 rows


**Stores** the canonical things mentions may resolve *to*.

| Column | Type | Notes |
| --- | --- | --- |
| `entity_id` | varchar(64) **PK** | opaque, derived deterministically from the seed source — re-seeding a clean corpus reproduces the same ids |
| `entity_type` | varchar(32) | `PERSON` \| `ORGANIZATION` \| `PROJECT` (closed set) |
| `canonical_name` | varchar(512) | display form |
| `normalized_name` | varchar(512) | match form |
| `source` | varchar(64) | which seed pass created it |
| `cms_uuid` | varchar(255) **UNIQUE** | one entity per authoritative CMS record. NULLs are exempt from uniqueness |
| `trust` | varchar(16) | `authoritative` \| `pi_attested` \| `derived` |
| `status` | varchar(16) | `active` \| demoted |
| `claim_eligible` | tinyint(1) | **0 = provisional identity** — see below |
| `merged_into` | varchar(64) | set when this entity was merged away |
| `created_at`, `updated_at` | | |

> **`claim_eligible = 0` is the most important column in the knowledge layer.**
> It marks a *provisional* identity: a name the corpus attests but has not shown
> to denote exactly one real-world thing. The author facet is full of these —
> two different people called "Arun Kumar" are one row — so linking a mention to
> such a row groups sightings by name and asserts nothing about identity. A
> provisional entity may not carry claims and cannot be a graph-retrieval target.

### `documents_entity_alias` — 3,518 rows

**Stores** every surface form that may denote an entity.

| Column | Type | Notes |
| --- | --- | --- |
| `entity_id` | varchar(64) **PK** | |
| `normalized` | varchar(512) **PK** | |
| `alias_type` | varchar(32) **PK** | e.g. name, acronym, title |
| `surface` | varchar(512) | as written |
| `autolink` | tinyint(1) | 0 = a resolution *candidate* but never an automatic match |
| `is_ambiguous` | tinyint(1) | set globally when a surface is attested for more than one entity |
| `source` | varchar(64) | |

> `autolink` and `is_ambiguous` carry the eligibility rule: a surface too short,
> too generic, or attested for more than one entity can be considered but never
> auto-matched. `is_ambiguous` is set by a **global** pass — the moment a second
> "Sharma" exists the shared surface must stop autolinking *for everyone*, which
> is why it can't be decided per document.

### `documents_entity_identifier` — 972 rows

**Stores** exact identifiers — project codes and the like.

| Column | Type | Notes |
| --- | --- | --- |
| `scheme` | varchar(32) **PK** | the identifier namespace |
| `value` | varchar(255) **PK** | |
| `entity_id` | varchar(64) | |
| `source` | varchar(64) | |

> `PRIMARY KEY (scheme, value)` states *"this identifier denotes exactly one
> entity"* as a **database invariant**. That's the strongest correctness
> guarantee in the entity layer, and it's what makes identifier resolution
> (Tier 0) a lookup rather than an inference.

### `documents_entity_mention` — 6 rows

**Stores** one row per sighting of a name in a chunk. The largest table the
knowledge layer adds when fully populated.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | bigint **PK** | |
| `chunk_id` | varchar(64) | |
| `document_id`, `doc_version` | | a reindex replaces a document's whole mention set by this pair |
| `start_offset`, `end_offset` | int | **chunk-relative** |
| `surface_text` | varchar(512) | must equal `chunk_text[start:end]` |
| `normalized_text` | varchar(512) | |
| `entity_type` | varchar(32) | |
| `extraction_method` | varchar(32) | `cms_field` \| `identifier` \| `gazetteer` \| `pattern` \| `llm` — cheapest and surest first |
| `extractor_version` | varchar(64) | |
| `confidence` | float | |
| `created_at` | datetime | |

Key: `UNIQUE (chunk_id, start_offset, end_offset, normalized_text)`.

> Two things this table deliberately does **not** have. **No `entity_id`** — a
> mention is a *sighting*, and resolution owns identity; keeping it out is what
> stops extraction from quietly inventing it. And the unique span key is what
> makes repeated extraction **idempotent**, so retries and re-sweeps cannot
> duplicate knowledge.
>
> Offsets are chunk-relative because there is no single text a document-level
> offset could index into — a website body is one blob while a PDF is paginated
> sections. Chunk-relative offsets are also *verifiable*, which is the check
> that keeps a model from inventing a span.

### `documents_entity_resolution_decision` — 6 rows

**Stores** one row per resolution attempt: what was decided and everything
needed to explain why.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | bigint **PK** | |
| `chunk_id`, `start_offset`, `end_offset` | | identifies the span |
| `surface_text`, `normalized_text`, `entity_type` | | |
| `decision` | varchar(16) | `AUTO` \| `PROVISIONAL` \| `AMBIGUOUS` \| `UNRESOLVED` |
| `entity_id` | varchar(64) | NULL unless linked |
| `claim_eligible` | tinyint(1) | denormalised from the entity, so a consumer never joins back — and the log stays readable after a later promotion changes the entity |
| `tier` | varchar(24) | which of the five tiers decided |
| `score`, `margin` | float | |
| `reason` | varchar(255) | human-readable |
| `candidates` | json | the scored shortlist, so a decision can be re-read without re-running the resolver |
| `resolver_version` | varchar(64) | a rerun under new rules is distinguishable from the old verdict |
| `created_at` | datetime | |

Key: `UNIQUE (chunk_id, start_offset, end_offset, normalized_text)`.

---

## 6. Knowledge — claims

**Claims live here first and only here.** Projection to Neo4j is a separate,
retryable pass — so a graph outage costs a retry rather than a re-extraction,
and no transaction ever spans two databases.

### `documents_assertion` — 1,374 rows

**Stores** staged claims: subject–predicate–object with verified evidence.

| Column | Type | Notes |
| --- | --- | --- |
| `claim_id` | varchar(64) **PK** | hash of **evidence + subject + predicate + object** — see below |
| `subject_entity_id` | varchar(64) | |
| `predicate` | varchar(64) | one of 7 closed predicates |
| `object_entity_id` | varchar(64) | for entity-valued predicates |
| `object_literal` | varchar(255) | for literal-valued predicates (e.g. a role) |
| `document_id`, `chunk_id` | | provenance |
| `evidence_kind` | varchar(16) | `cms_field` \| `chunk` |
| `source_field` | varchar(64) | which CMS field, for a CMS claim |
| `source_value`, `source_value_hash` | | the literal CMS value. **Not** part of identity — recorded for explainability, and so a re-extraction can tell an *edited* value from a *removed* one |
| `quote`, `quote_start`, `quote_end` | | the verbatim sentence and its offsets |
| `valid_from`, `valid_until` | date | when the claim was true |
| `temporal_basis` | varchar(16) | how validity was derived. Only `stated` / `subject_period` earn a current-state edge |
| `confidence` | float | |
| `status` | varchar(16) | `active` \| `disputed` \| `superseded` \| `retracted` |
| `extraction_method`, `extractor_version`, `vocabulary_version` | | |
| `model`, `prompt_version` | | for model-extracted claims |
| `asserted_at`, `created_at`, `updated_at` | | |

Indexes: `idx_subject (subject_entity_id, predicate)`, `idx_object`,
`idx_document`, `idx_chunk`, `idx_status`, `idx_predicate`.

> **Claim identity is what the source states, and nothing about how it was
> read.** Validity, confidence, status, the quote and the extracting model are
> all *state on* the claim, never part of it. So re-extracting the same chunk
> with a better prompt **updates** the row rather than forking it — which is the
> property that makes retries safe.
>
> Two claims from two chunks asserting the same fact stay separate on purpose:
> they're independent evidence, and merging them would lose a corroboration.
>
> Claims are **retracted, never deleted** — the claim was true of the source as
> it stood, and that history is worth keeping.

### `documents_assertion_rejection` — 576 rows

**Stores** why a proposed claim was refused.

**Why it exists** — *"the model produced fewer claims today"* is only
diagnosable if the refusals were recorded. And a rejected claim must never sit in
the same table as an accepted one.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | bigint **PK** | |
| `code` | varchar(48) | the reason, e.g. `unknown_subject`, `object_not_claim_eligible` |
| `detail` | varchar(255) | |
| `subject_entity_id`, `predicate`, `document_id`, `chunk_id` | | as far as they were known |
| `extraction_method` | varchar(32) | |
| `created_at` | datetime | |

### `documents_assertion_link` — 0 rows

**Stores** directed links between claims: one supersedes another, or two
contradict.

**Why a table rather than columns** — a claim may contradict several others, and
a contradiction is a fact worth inspecting on its own rather than something
implied by two status flags.

| Column | Type | Notes |
| --- | --- | --- |
| `from_claim_id` | varchar(64) **PK** | |
| `to_claim_id` | varchar(64) **PK** | |
| `kind` | varchar(16) **PK** | `contradicts` \| `supersedes` |
| `reason` | varchar(255) | |
| `detector` | varchar(64) | detector version |
| `created_at` | datetime | |

### `documents_predicate_candidate` — 0 rows

**Stores** relationships an extractor proposed that the closed vocabulary does
not contain — e.g. `COLLABORATED_WITH`.

**Why it exists** — the evidence used to be thrown away twice: the extractor
dropped the proposal and validation rejected it with a code and no quote. So the
one question the vocabulary needs answered — *"what relationship does this corpus
keep asserting that we cannot express?"* — had no data behind it.

| Column | Type | Notes |
| --- | --- | --- |
| `candidate_id` | varchar(64) **PK** | same hash construction as `claim_id`, so a retry upserts |
| `predicate_surface` | varchar(128) | as proposed |
| `predicate_normalized` | varchar(128) | |
| `subject_entity_id`, `object_entity_id`, `object_literal` | | |
| `document_id`, `chunk_id`, `evidence_kind` | | |
| `quote`, `quote_start`, `quote_end` | | the same verified quote a claim would carry, so a reviewer can read the sentence that proposed it |
| `confidence` | float | |
| `extraction_method`, `extractor_version`, `vocabulary_version` | | |
| `model`, `prompt_version` | | |
| `status` | varchar(16) | `pending` \| reviewed |
| `observations` | int | how many times the corpus proposed it — the number that decides whether it's worth adding |
| `first_seen_at`, `last_seen_at` | datetime | |

> **A candidate is evidence, never a claim and never an edge.** It cannot become
> real without a source-code change to the predicate vocabulary and a version
> bump. Nothing at runtime can widen the graph vocabulary.

---

## 7. Knowledge — runs

### `documents_knowledge_run` — 11,238 rows

**Stores** one row per `(document_id, doc_version)`: what the knowledge stage did.

**Why it exists** — three questions nothing else could answer: which documents
have been processed at their current version, which failed and why, and what the
stage actually produced. The row is written **last**, so its *absence* means
"did not finish" — which is exactly what the catch-up sweep looks for.

| Column | Type | Notes |
| --- | --- | --- |
| `document_id` | varchar(255) **PK** | |
| `doc_version` | int **PK** | |
| `run_id` | varchar(64) | |
| `status` | varchar(16) | `ok` \| `partial` \| `failed` |
| `attempts`, `seconds` | | |
| `chunks_seen`, `chunks_cached` | int | cache hit rate — this cache's failure mode is silently re-paying |
| `mentions` | int | |
| `entities_auto`, `entities_provisional`, `entities_ambiguous`, `entities_unresolved` | int | the resolution breakdown |
| `claims_built`, `claims_staged`, `claims_rejected`, `claims_retracted` | int | |
| `pending_predicates` | int | |
| `conflicts_disputed`, `conflicts_superseded` | int | |
| `projection_status` | varchar(16) | `ok` \| `skipped` \| `unreachable` \| `failed` |
| `projection_version`, `projection_edges` | | |
| `rejection_counts` | json | per-code breakdown |
| `errors` | json | per-stage errors |
| `last_error` | text | |
| `knowledge_version` | varchar(128) | fingerprint of extractor + gazetteer + rules |
| `created_at`, `updated_at` | datetime | |

> **Upserted, not append-only.** History of *versions* is what matters; history
> of *retries* is `attempts` plus `last_error` — the shape the enrichment and
> dead-link tables already use. An append-only log would grow one row per sweep
> per document and answer no question the counters don't.

---

## Retired tables

If you see these in an older dump, they're gone:

| Table | Replaced by |
| --- | --- |
| `terms`, `term_aliases`, `documents_term` | themes/tags keyed by **name** in `documents_theme` / `documents_tag`; taxonomy UUIDs live only in Qdrant payloads |
| `documents_category` | renamed to `documents_theme`, with the value column renamed too — handled by `migrate_renamed_facets` |

---

## Operational notes

**Creating the schema** — any ingestion run does it. Or explicitly:

```python
from app.catalog import schema
schema.ensure_state_table()            # documents + 4 facet children
schema.ensure_log_table()              # ingest_log
schema.ensure_enrichment_table()
schema.ensure_dead_link_table()
schema.ensure_retry_table()
schema.ensure_date_decision_table()
schema.ensure_entity_tables()          # mentions + extraction cache
schema.ensure_resolution_tables()      # entities, aliases, identifiers, decisions
schema.ensure_assertion_tables()       # claims, rejections, links
schema.ensure_predicate_candidate_table()
schema.ensure_knowledge_run_table()
```

**Verifying it** — read-only scripts:

```bash
python -m scripts.verify_corpus           # MySQL vs Qdrant vs Neo4j, plus 4 date invariants
python -m scripts.verify_catalog_counts   # every reader vs independent SQL
python -m scripts.audit_dates             # every date the corpus stores
python -m scripts.scrape_site_dates       # every date the live site states, compared
```

`verify_catalog_counts` matters more than it sounds: the catalogue readers compose
joins to support arbitrary filter combinations, which makes a fan-out bug easy to
miss — a document with two authors and three themes joins to six rows, and a
`COUNT(*)` where `COUNT(DISTINCT …)` was meant reports six documents.

The date checks inside `verify_corpus` run on **every sweep**
(`reconcile_after_sweep`), not only on demand, and all four are zero in a healthy
corpus — that is the bar for living there rather than in `audit_dates`. A sweep
that always warns is a sweep nobody reads, so findings that are legitimately
non-zero (30 documents dated before the period their own name states, ~2,400
dated by an import batch) stay in the audit script.

`stated_date_not_applied` is the one to watch: it is non-zero if a sweep did not
apply the source's stated date, or if something overwrote a corrected one —
specifically `app.ingestion.backfill`, which lifts `published_at` out of chunk
payloads and writes it back with a bare `SET`. That is the silent revert path an
earlier backfill was lost to.

**Correcting dates** — see [date-correction-runbook.md](date-correction-runbook.md).
The two backfills are dry-run-first and neither re-extracts, re-chunks or
re-embeds anything: a date is metadata, so the correction is an `UPDATE` plus a
`set_payload`, and no `PIPELINE_VERSION` bump is involved.
