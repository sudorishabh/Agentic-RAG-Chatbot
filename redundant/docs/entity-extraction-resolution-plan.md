# Entity extraction and resolution: a knowledge layer over the corpus

Implementation plan for adding entity extraction and entity resolution to the
existing RAG system, so that mentions like "Dr. Raj Sharma" / "Raj Sharma" /
"R. Sharma" can be traced to one canonical entity with an auditable reason.

Complements [ingestion.md](ingestion.md) (the pipeline as it is),
[database-retrieval-redesign.md](database-retrieval-redesign.md) (query-time
name matching, which this reuses), and
[database-tool-registry.md](database-tool-registry.md) (the catalog tool
surface a later phase extends).

**Status: plan only.** No code, no migrations, no tables, no Qdrant changes.
Grounded in a read of `app/ingestion/`, `app/catalog/`, `app/retrieval/`,
`app/core/`, `app/pipeline/`, config and tests at commit `1eb1e4b`.

---

# A. Current Architecture Assessment

## A.1 What exists

**Ingestion (single entry path).** `app/ingestion/pipeline.py::_handle` is the
only per-document state machine:

```
ChangeRecord  ->  DELETED?    -> delete_document() + state.delete()
              ->  UNCHANGED?  -> (optional log) return
              ->  build_doc()                              [span ingest.extract]
              ->  content_hash = doc.ensure_content_hash()
              ->  _enrich(doc, content_hash)               <- LLM, cached by content_hash
              ->  content_changed()? no  -> _persist(indexed=False)
                                            refresh_document_title()   <- payload-only rewrite
              ->  content_changed()? yes -> version = next_version()
                                            chunk_canonical()          [span ingest.chunk]
                                            index_chunks()             [ingest.embed / ingest.upsert]
                                            delete_document(keep_ids=...) <- index-new-then-delete swap
                                            _persist(indexed=True)
              ->  _log(...)  -> ingest_log row
```

`_run` wraps this with a one-run-at-a-time `threading.Lock`, a `run_id`, a batch
budget (`ingest_max_docs_per_run`), an optional worker pool, and a `Counter`
tally. **Every external dependency fails open** (enrichment, date decisions,
dead-link markers, ingest_log) — a warning and continue, never a failed sweep.

**Change detection.** `ChangeStatus` NEW/CHANGED/UNCHANGED/DELETED. Node
fingerprint = Drupal `changed`; attachment fingerprint = its node's `changed`
(real attachments) or the in-body URL hash. `MAX(changed_mark)` per bundle is the
resume cursor, crawled oldest-first. `content_changed()` compares `content_hash`.

**`content_hash` is the key fact for incrementality.**
`CanonicalDocument.compute_content_hash()` is SHA-256 of **body text only** —
deliberately excluding title and metadata so it is reproducible from source bytes.
`documents_enrichment` is keyed by it (not by `document_id`, and with no FK) so
the cache survives a state-table reset and is shared by identical bodies.

**Chunking.** `chunk_canonical` -> parent/child chunks.
`chunk_id = uuid5(NS, "{document_id}|v{doc_version}|{suffix}")` —
**version-scoped**. Every `Chunk` already carries
`content_hash = sha256(chunk.text)`. Parents are stored as **zero vectors** and
never embedded; children carry `embed_text` (a `title > heading` breadcrumb +
text). Children overlap by `child_overlap_tokens`.

**MySQL catalog** (raw SQL, no ORM, idempotent DDL in one file
`app/catalog/schema.py`, table prefix from `ingest_state_table`, default
`documents`):

| Table | Key | Notes |
|---|---|---|
| `documents` | `document_id` PK VARCHAR(255) | source_type, bundle, entity_type, fingerprint, content_hash, doc_version, published_at, title, url, `raw_meta` JSON, indexed_at |
| `documents_author` | *(no PK)* | free-text author names, FK CASCADE |
| `documents_tag` | *(no PK)* | free-text tags, FK CASCADE |
| `documents_theme` | (document_id, theme) | theme_type/parent/theme_group hierarchy, FK CASCADE |
| `documents_attachment` | (file_uuid, document_id) | FK CASCADE |
| `documents_enrichment` | `content_hash` | **no FK by design**, version-invalidated, attempts counter |
| `documents_dead_link` | `document_id` | no FK; fingerprint-scoped expiry |
| `documents_date_candidate` / `_date_decision` | `document_id` | shadow/audit tables + review queue |
| `ingest_log` | `id` AUTO_INC | append-only event log |

**Qdrant.** One collection, dense cosine. Payload built by
`chunking/payload.py::build_payload`, which drops `None/""/[]` and ends with
`payload.update(m.extra)` — **anything parked in `CanonicalDocument.extra` leaks
into every chunk payload**. Payload indexes ensured at ingest (`published_at`,
`term_ids`, `theme_ids`) plus a script for the rest. Mandatory query filter:
`is_parent=False`, `is_current=True`, `tenant_id`, `acl` MatchAny,
`must_not section_type in (toc, references, glossary)`.
`refresh_document_title()` proves the pattern for **rewriting one payload field
over an existing document without re-embedding**.

**There is already an "entity" namespace, and it means something else.** This
matters more than anything else in the plan:

- `app/retrieval/structured/entities.py` — an "Entity" is a **Drupal content
  bundle** (`news`, `research_papers`, `people`, ...). Bundle registry, synonyms,
  display labels, ambiguous-word map.
- `app/retrieval/structured/resolve.py` — **query-time fuzzy name matching**
  against catalog facets (`author | bundle | theme`). Pure `difflib`:
  `_normalize`, `_token_set_ratio`, `_prefix_score`, `score()`, and
  `classify_band(top, runner_up)` returning `ACCEPT / AMBIGUOUS / MISS` with
  thresholds already tuned against worked examples (`_ACCEPT_SCORE=0.90`,
  `_ACCEPT_FLOOR=0.60`, `_ACCEPT_MARGIN=0.30`, `_AMBIGUOUS_FLOOR=0.60`).
  `EntityCandidate(id, canonical_name, type, score)`; `plausible()` picks
  clarification offers.
- `app/retrieval/structured/filters.py::resolve_filters` canonicalizes
  author/theme/tag on the way to SQL; `AmbiguousFilter` surfaces a clarification
  instead of guessing.
- `settings.entity_resolution_enabled` **already exists** (default `False`) and
  gates *fall-through behaviour* of that name matching.

**Consequence:** authors today are free text with no IDs
(`documents_author(document_id, author)`), which is exactly the gap this work
closes — but the new layer must not reuse the names `entities`,
`resolve_entity`, or the flag `entity_resolution_enabled`.

**The date-resolution subsystem is the template to copy.** `date_evidence.py`
(evidence model) -> `date_rules.py` (deterministic `decide()` returning
`keep_page_date | needs_llm`) -> `date_llm.py` (LLM interpreter with four hard
safety properties and `MIN_OVERRIDE_CONFIDENCE=0.9`) -> `date_resolution.py`
(canonical `resolve()`, fails **closed**) -> `catalog/date_decisions.py`
(decision + evidence table doubling as review queue) ->
`scripts/eval_date_resolution.py` (scored against a hand-labelled
`reports/phase0/date_evalset.json`, headline metric = **false overrides**) ->
shadow mode first, feature flag second. Entity resolution is the same problem
shape with "false merge" in place of "false override".

**Other reusable infrastructure.** LLM: `get_llm(temperature)` /
`get_structured_llm()` + `.with_structured_output(PydanticModel)`. Embeddings:
`get_embeddings()`, `embed_query()`. MySQL: `mysql_connection()` pool. Timing:
`span("name")` — names are the metric-stage contract, mapped to components in
`metrics._COMPONENTS`. Tests: plain pytest, `tests/test_*.py`, no conftest, heavy
`monkeypatch.setattr` on module-level functions. Backfill pattern:
`enrich_backfill.py` rebuilds document text from Qdrant child chunks so nothing
is re-downloaded.

**Dependency constraint.** `docs/database-retrieval-redesign.md §1` records it
explicitly: *"There is no fuzzy matching anywhere in the repo — no `difflib`, no
`rapidfuzz`, no `pg_trgm`."* The redesign deliberately chose stdlib `difflib`.
This plan honours that: **no new runtime dependency**.

## A.2 The corpus already contains authoritative entity records

This is the highest-leverage finding, and it changes the cost model completely.
`DEFAULT_BUNDLES` includes:

- **`people`** — a node per person, with a real Drupal **UUID**, `title` = name,
  body = bio, and a URL.
- **`completed_projects`, `ongoing_projects`** — a node per project, each with a
  UUID and title (the `resolve.py` comment records 918 completed projects).
- **`services`** — candidate PROGRAM records.
- `EntityRef(field_name, uuid, entity_type, label)` on every crawled document,
  carrying references into taxonomy vocabularies. `canonical.py` notes that
  non-theme vocabularies ("a division, a regional area") are deliberately *not*
  folded into themes and "still reach the catalog through entity refs and
  `raw_meta`" — i.e. **DEPARTMENT / LOCATION / ORGANIZATION vocabularies are
  already crawled and stored, just unused**.
- `documents.raw_meta` JSON — lossless source metadata on every row.
- `documents_author` — the distinct author list (low hundreds).

So canonical entities can be **seeded from CMS records with real UUIDs** rather
than invented from free text. Text extraction then only has to *link mentions to
existing entities*, which is a far safer and far cheaper problem than open-world
clustering.

## A.3 Where entity extraction/resolution fits

Extraction belongs **after chunking, before/alongside `index_chunks`**, inside
the `content_changed == True` branch only. Resolution belongs **after extraction,
in the same document transaction** for the deterministic tiers, and in a
**separate budgeted batch pass** for anything needing an LLM — because
per-document LLM calls inside a sweep are what the batch budget exists to
prevent.

---

# B. Proposed Architecture

## Before

```
Drupal crawl -> ChangeRecord -> build_doc -> content_hash -> enrich(abstract)
                                                 |
                              content changed? --+-> chunk_canonical -> embed -> Qdrant upsert
                                                                        \-> delete old points
                                                     -> MySQL: documents + author/tag/theme/attachment
```

## After

```
Drupal crawl -> ChangeRecord -> build_doc -> content_hash -> enrich(abstract)
                                                 |
                              content changed? --+-> chunk_canonical
                                                          |
                                    +---------------------+------------------+
                                    v                                        v
                          ENTITY EXTRACTION (children only)          embed -> Qdrant upsert
                          per-chunk, cached by chunk content_hash      \-> delete old points
                                    |
                                    v
                          MentionCandidate[]  (surface, type, offsets, confidence, method)
                                    |
                                    v
                          ENTITY RESOLUTION (staged, deterministic first)
                          T0 identifier -> T1 alias/dictionary -> T2 blocked fuzzy
                          -> T3 context scoring -> T4 LLM adjudication (deferred, batched)
                                    |
                                    v
                          MySQL: entity_mention (+ resolved_entity_id, confidence, band)
                                 entity_resolution_decision (evidence, rule, decided_by)
                                 entity_review           (AMBIGUOUS / REVIEW queue)
                                    |
                                    v (Phase 6, separate + reversible)
                          Qdrant set_payload(entity_ids=[...]) on that document's chunk points
```

Bootstrap, run once and then incrementally:

```
CMS records -> scripts/seed_entities_from_catalog.py
               people nodes        -> PERSON     (entity_id from node uuid)
               *_projects nodes    -> PROJECT
               services nodes      -> PROGRAM
               taxonomy refs       -> ORGANIZATION / DEPARTMENT / LOCATION
               documents_author    -> PERSON (name-only, lower trust)
                                   \-> entities + entity_alias + entity_identifier
```

New package `app/knowledge/` — deliberately neither `ingestion` nor `retrieval`,
because both consume it:

```
app/knowledge/
  __init__.py          canonical entry points: extract_mentions(), resolve_mentions()
  types.py             EntityType, MentionCandidate, ResolutionDecision, ResolutionBand
  normalize.py         name normalization, honorific/initial handling, acronym detection
  extract.py           mention extraction orchestration (gazetteer -> pattern -> LLM)
  gazetteer.py         in-process alias index, loaded from MySQL, versioned
  candidates.py        blocking / candidate generation
  scoring.py           feature vector -> score, band classification, structural gates
  adjudicate.py        LLM disambiguation (batched, gated, quote-required)
  resolve.py           the one canonical resolve() entry point; fails closed
  seed.py              CMS -> canonical entity bootstrap

app/catalog/
  entities.py          entities / entity_alias / entity_identifier / entity_attribute DAO
  mentions.py          entity_mention + entity_extraction cache DAO
  entity_decisions.py  entity_resolution_decision + entity_review + entity_merge_log DAO
  schema.py            + ensure_entity_tables()   (existing file, new function)
```

One small refactor is recommended: move the pure scoring primitives
(`_normalize`, `_token_set_ratio`, `_prefix_score`, `score`, `classify_band`) out
of `app/retrieval/structured/resolve.py` into `app/core/namematch.py`, and have
`resolve.py` re-export them. Behaviour-identical, existing tests keep passing,
and it removes an ingestion-imports-retrieval layering violation. ~40 lines
moved, no logic change.

---

# C. Data Model

Conventions followed: raw SQL in `app/catalog/schema.py`,
`CREATE TABLE IF NOT EXISTS` + `_ensure_column` guards, one `ensure_*` function,
table names templated off `state_table()`, `utf8mb4`, InnoDB.

## C.1 `{state}_entity` — canonical entities

```
entity_id       VARCHAR(64)   NOT NULL   -- 'person_00192', 'project_00121'
entity_type     ENUM('PERSON','ORGANIZATION','PROJECT','INSTITUTION',
                     'PROGRAM','DEPARTMENT','LOCATION') NOT NULL
canonical_name  VARCHAR(512)  NOT NULL
normalized_name VARCHAR(512)  NOT NULL   -- normalize.py output; blocking key source
source          VARCHAR(32)   NOT NULL   -- 'cms_node' | 'cms_taxonomy' | 'catalog_author' | 'text'
source_uuid     VARCHAR(255)  NULL       -- Drupal uuid when seeded from a CMS record
source_document_id VARCHAR(255) NULL     -- the people/project node this entity IS
trust           ENUM('authoritative','derived','provisional') NOT NULL DEFAULT 'provisional'
status          ENUM('active','merged','rejected') NOT NULL DEFAULT 'active'
merged_into     VARCHAR(64)   NULL       -- set when status='merged'; never deleted
mention_count   INT           NOT NULL DEFAULT 0   -- denormalized, refreshed by a pass
document_count  INT           NOT NULL DEFAULT 0
first_seen_at   DATETIME      NOT NULL
updated_at      DATETIME      NOT NULL
PRIMARY KEY (entity_id)
UNIQUE KEY uq_source_uuid (entity_type, source_uuid)     -- one entity per CMS record
KEY idx_type_norm (entity_type, normalized_name)          -- blocking lookups
KEY idx_status (status)
KEY idx_merged_into (merged_into)
KEY idx_trust (entity_type, trust)
```

`entity_id` is opaque, stable, and **never reused**.
`UNIQUE(entity_type, source_uuid)` is what makes the CMS seeder idempotent.
`merged_into` is a tombstone pointer, not a delete — a wrong merge is undone by
clearing it.

No FK to `documents` on `source_document_id`: a `people` node can be deleted from
the CMS while the person is still mentioned in a hundred PDFs. Same reasoning as
`documents_enrichment`.

## C.2 `{state}_entity_alias` — every surface form that may denote an entity

```
alias_id        BIGINT        NOT NULL AUTO_INCREMENT
entity_id       VARCHAR(64)   NOT NULL
alias           VARCHAR(512)  NOT NULL
normalized      VARCHAR(512)  NOT NULL
alias_type      ENUM('canonical','official_name','former_name','abbreviation',
                     'acronym','spelling_variant','initialism','transliteration',
                     'code','nickname','observed') NOT NULL
is_ambiguous    TINYINT(1)    NOT NULL DEFAULT 0  -- this surface maps to >1 entity
autolink        TINYINT(1)    NOT NULL DEFAULT 1  -- may this alias resolve on its own?
confidence      DECIMAL(4,3)  NOT NULL DEFAULT 1.000
source          VARCHAR(32)   NOT NULL  -- 'cms' | 'curated' | 'derived' | 'observed'
valid_from      DATE          NULL
valid_to        DATE          NULL      -- former names: "Tata Energy Research Institute"
created_at      DATETIME      NOT NULL
updated_at      DATETIME      NOT NULL
PRIMARY KEY (alias_id)
UNIQUE KEY uq_entity_alias (entity_id, normalized, alias_type)
KEY idx_normalized (normalized)         -- the gazetteer's primary lookup
KEY idx_norm_autolink (normalized, autolink)
CONSTRAINT fk_entity_alias FOREIGN KEY (entity_id)
  REFERENCES `{state}_entity` (entity_id) ON DELETE CASCADE
```

`autolink=0` is the mechanism that makes `"R. Sharma"` safe: an initialism shared
by several people is stored (so it is *recognized*) but cannot resolve on its own.

## C.3 `{state}_entity_identifier` — exact identifiers

```
entity_id       VARCHAR(64)   NOT NULL
scheme          VARCHAR(32)   NOT NULL  -- 'drupal_uuid'|'project_code'|'orcid'|'email'|'nid'
value           VARCHAR(255)  NOT NULL
confidence      DECIMAL(4,3)  NOT NULL DEFAULT 1.000
source          VARCHAR(32)   NOT NULL
created_at      DATETIME      NOT NULL
PRIMARY KEY (scheme, value)              -- an identifier denotes exactly one entity
KEY idx_entity (entity_id)
CONSTRAINT fk_entity_identifier FOREIGN KEY (entity_id)
  REFERENCES `{state}_entity` (entity_id) ON DELETE CASCADE
```

`PRIMARY KEY (scheme, value)` is the strongest correctness guarantee in the
schema: `P-1024` cannot silently belong to two projects. This is Tier 0 of
resolution and the only tier allowed to merge with no corroborating signal.

## C.4 `{state}_entity_mention` — one row per sighting, with full provenance

```
mention_id       BIGINT        NOT NULL AUTO_INCREMENT
document_id      VARCHAR(255)  NOT NULL
doc_version      INT           NOT NULL
chunk_id         VARCHAR(64)   NOT NULL   -- version-scoped uuid5
chunk_content_hash VARCHAR(64) NOT NULL   -- Chunk.content_hash -> extraction cache key
is_parent        TINYINT(1)    NOT NULL DEFAULT 0   -- always 0 today (children only)
page_number      INT           NULL
section_heading  VARCHAR(512)  NULL
surface_text     VARCHAR(512)  NOT NULL
normalized       VARCHAR(512)  NOT NULL
entity_type      ENUM(...)     NOT NULL   -- the extractor's type call
char_start       INT           NULL        -- offsets are CHUNK-relative
char_end         INT           NULL
context_before   VARCHAR(255)  NULL        -- the audit snippet
context_after    VARCHAR(255)  NULL
extraction_method VARCHAR(32)  NOT NULL   -- 'gazetteer'|'pattern'|'llm_ner'|'cms_field'
extraction_model  VARCHAR(64)  NULL
extractor_version VARCHAR(64)  NOT NULL
extraction_confidence DECIMAL(4,3) NOT NULL DEFAULT 0
resolved_entity_id VARCHAR(64) NULL        -- NULL = unresolved / ambiguous
resolution_band  ENUM('auto','review','new','ambiguous','unresolved')
                 NOT NULL DEFAULT 'unresolved'
resolution_confidence DECIMAL(4,3) NOT NULL DEFAULT 0
resolver_version VARCHAR(64)   NULL
resolved_at      DATETIME      NULL
created_at       DATETIME      NOT NULL
PRIMARY KEY (mention_id)
UNIQUE KEY uq_mention_span (chunk_id, char_start, char_end, normalized)
KEY idx_document (document_id, doc_version)
KEY idx_chunk (chunk_id)
KEY idx_entity (resolved_entity_id)
KEY idx_entity_doc (resolved_entity_id, document_id)   -- "docs mentioning X"
KEY idx_band (resolution_band)
KEY idx_unresolved (resolution_band, entity_type, normalized)
KEY idx_chunk_hash (chunk_content_hash)
CONSTRAINT fk_mention_document FOREIGN KEY (document_id)
  REFERENCES `{state}` (document_id) ON DELETE CASCADE
-- deliberately NO FK on resolved_entity_id: it must survive an entity merge
-- being reverted, and repointing is done by UPDATE, not by cascade.
```

**Why `chunk_id` is the right anchor.** Chunk ids are
`uuid5(doc|version|suffix)`, so they change only when `doc_version` bumps, which
happens only when `content_hash` changes. So *chunk_id changes <=> content
changed <=> mentions must be recomputed.* The key is self-invalidating; there is
no separate staleness question.

**Offsets are chunk-relative**, not document-relative. Document-relative offsets
would be unstable across extraction paths (paginated PDF sections vs. one-blob
website bodies) and unmappable back to a chunk. Chunk-relative offsets +
`chunk_id` give an exact, quotable span.

**Children only.** Parent text is the concatenation of its children, so
extracting from parents would double every mention at double cost. `is_parent`
exists so a later change (e.g. cross-sentence relations needing parent context)
doesn't need a migration.

**FK CASCADE to `documents` is correct and safe** — see §J.5 for why cascading
mentions does *not* delete canonical entities.

## C.5 `{state}_entity_extraction` — the cost cache

```
chunk_content_hash VARCHAR(64) NOT NULL
version            VARCHAR(64) NOT NULL   -- extractor_version fingerprint
mentions           JSON        NULL       -- MentionCandidate[] as extracted
mention_count      INT         NOT NULL DEFAULT 0
method             VARCHAR(32) NOT NULL
attempts           INT         NOT NULL DEFAULT 0
last_error         TEXT        NULL
updated_at         DATETIME    NOT NULL
PRIMARY KEY (chunk_content_hash)
KEY idx_version (version)
```

Modelled on `documents_enrichment`, for the same three reasons: it survives a
state-table reset; identical text anywhere in the corpus extracts once; an
always-failing chunk stops being retried. **No FK.** Version-invalidated, not
TTL'd — editing a prompt or swapping a model re-extracts transparently.

This is what makes re-ingestion cheap: a document whose paragraphs are stable but
whose chunk boundaries shifted still hits the cache for most of its text, even
though every `chunk_id` changed.

## C.6 `{state}_entity_resolution_decision` — the audit trail

```
decision_id     BIGINT        NOT NULL AUTO_INCREMENT
mention_id      BIGINT        NOT NULL
entity_id       VARCHAR(64)   NULL        -- what it resolved to (NULL = no merge)
action          VARCHAR(24)   NOT NULL    -- 'link'|'create'|'defer'|'reject'|'review'
band            VARCHAR(16)   NOT NULL
tier            VARCHAR(24)   NOT NULL    -- 'identifier'|'alias'|'fuzzy'|'context'|'llm'
rule            VARCHAR(64)   NOT NULL    -- named rule, e.g. 'unique_alias_autolink'
decided_by      ENUM('deterministic','llm','human') NOT NULL
score           DECIMAL(4,3)  NOT NULL DEFAULT 0
runner_up_id    VARCHAR(64)   NULL        -- the entity we did NOT pick
runner_up_score DECIMAL(4,3)  NULL        -- the margin, recomputable
features        JSON          NULL        -- the full feature vector
evidence        TEXT          NULL        -- one human sentence
llm_raw         JSON          NULL
prompt_version  VARCHAR(32)   NULL
resolver_version VARCHAR(64)  NOT NULL
superseded_by   BIGINT        NULL        -- corrections chain, never overwrite
created_at      DATETIME      NOT NULL
PRIMARY KEY (decision_id)
KEY idx_mention (mention_id)
KEY idx_entity (entity_id)
KEY idx_tier_action (tier, action)
KEY idx_decided_by (decided_by)
```

**Append-only** (like `ingest_log`, unlike `documents_date_decision` which
overwrites per document). A correction writes a new row and sets `superseded_by`
on the old one, so "why did the system decide this, and why did it change its
mind?" is answerable. `runner_up_id` + `runner_up_score` are stored, not just the
winner — the margin *is* the reason, and without it you cannot audit a near-tie.

## C.7 `{state}_entity_review` — the human queue

```
review_id     BIGINT       NOT NULL AUTO_INCREMENT
kind          VARCHAR(24)  NOT NULL  -- 'ambiguous_mention'|'candidate_merge'
                                      -- |'candidate_split'|'low_confidence_new'
entity_id     VARCHAR(64)  NULL
other_entity_id VARCHAR(64) NULL     -- the merge counterparty
mention_id    BIGINT       NULL
surface_text  VARCHAR(512) NULL
entity_type   VARCHAR(32)  NOT NULL
score         DECIMAL(4,3) NOT NULL DEFAULT 0
candidates    JSON         NULL      -- ranked options for a reviewer
evidence      TEXT         NULL
occurrences   INT          NOT NULL DEFAULT 1   -- how many mentions this covers
status        ENUM('open','resolved','dismissed') NOT NULL DEFAULT 'open'
resolution    VARCHAR(24)  NULL      -- 'merged'|'kept_separate'|'new_entity'|'dismissed'
resolved_by   VARCHAR(128) NULL
resolved_at   DATETIME     NULL
created_at    DATETIME     NOT NULL
updated_at    DATETIME     NOT NULL
PRIMARY KEY (review_id)
UNIQUE KEY uq_open_case (kind, entity_id, other_entity_id, surface_text)
KEY idx_status_score (status, score DESC)
KEY idx_kind (kind)
```

`UNIQUE(kind, entity_id, other_entity_id, surface_text)` + `occurrences`
collapses "the same ambiguity seen 400 times" into one reviewable case. Without
it the queue is unusable at corpus scale.

## C.8 `{state}_entity_merge_log` — reversible merges

```
merge_id      BIGINT       NOT NULL AUTO_INCREMENT
operation     ENUM('merge','unmerge','split','rename') NOT NULL
from_entity_id VARCHAR(64) NOT NULL
into_entity_id VARCHAR(64) NULL
mentions_moved INT         NOT NULL DEFAULT 0
mention_ids   JSON         NULL      -- exactly which mentions moved -> exact undo
aliases_moved JSON         NULL
reason        TEXT         NULL
performed_by  VARCHAR(128) NOT NULL  -- 'auto:<rule>' | a human identifier
reverted_by   BIGINT       NULL
created_at    DATETIME     NOT NULL
PRIMARY KEY (merge_id)
KEY idx_from (from_entity_id)
KEY idx_into (into_entity_id)
```

Recording `mention_ids` explicitly, not just a count, is what makes an unmerge
exact rather than a re-run of resolution.

## C.9 `{state}_entity_attribute` — temporal facts, and the claim bridge

```
attribute_id  BIGINT       NOT NULL AUTO_INCREMENT
entity_id     VARCHAR(64)  NOT NULL
attribute     VARCHAR(64)  NOT NULL  -- 'affiliation'|'role'|'location'|'department'
value_text    VARCHAR(512) NULL
value_entity_id VARCHAR(64) NULL     -- when the value is itself an entity
valid_from    DATE         NULL
valid_to      DATE         NULL      -- NULL = open interval / unknown
asserted_at   DATETIME     NOT NULL  -- when WE learned it
source_document_id VARCHAR(255) NULL
source_mention_id  BIGINT   NULL
confidence    DECIMAL(4,3) NOT NULL DEFAULT 0
status        ENUM('active','superseded','disputed','retracted')
              NOT NULL DEFAULT 'active'
created_at    DATETIME     NOT NULL
PRIMARY KEY (attribute_id)
KEY idx_entity_attr (entity_id, attribute, valid_from)
KEY idx_value_entity (value_entity_id)
KEY idx_status (status)
```

This is the table that answers "Raj Sharma at TERI, then at IIT Delhi"
**without versioning the entity** (§L below). It is also, deliberately, the shape
a `claim` table will take — see §M.

## C.10 What is reused unchanged

- `documents` / `documents_author` / `documents_theme` / `documents_tag` /
  `documents_attachment` — untouched. `documents_author` is *not* replaced;
  entities are layered beside it, and the free-text facet keeps working exactly
  as it does now.
- `ingest_log` — extraction/resolution counts ride in the existing per-run
  `Counter` tally, not in new log rows.
- `mysql_connection()`, `db.now()`, `db.state_table()`, `schema._ensure_column` —
  all reused.
- No new columns on `documents`. Nothing goes into `CanonicalDocument.extra` (it
  leaks to Qdrant).

## C.11 Relationships

```
documents 1-----n entity_mention n-----1 entity
                        |                  |1
                        |                  +--n entity_alias
                        |                  +--n entity_identifier
                        |                  \--n entity_attribute --> entity (value)
                        |
                        +--n entity_resolution_decision
                        \--0..1 entity_review

entity --merged_into--> entity          (self-referential tombstone)
entity_merge_log records every transition, with the mention ids
```

---

# D. Entity Extraction Pipeline

Runs only inside the `content_changed == True` branch, on **child chunks only**,
immediately after `chunk_canonical()`.

### Stage 0 — CMS-field mentions (free, no text reading)

Before touching any text, harvest the structured mentions the CMS already
asserts:

- `doc.authors` -> PERSON mentions, `extraction_method='cms_field'`,
  confidence 1.0
- `doc.entity_refs` where the target vocabulary is an
  organization/department/location vocabulary -> the corresponding type, with the
  ref's **UUID** in hand
- `documents_attachment` / node relationships -> INSTITUTION where applicable

These mentions are recorded with `chunk_id` of the document's first child (so
provenance stays uniform) and `char_start=NULL`. They cost nothing, carry a UUID,
and resolve at Tier 0. On this corpus they will account for a large share of
PERSON and ORGANIZATION links.

### Stage 1 — cache lookup

For each child chunk, look up `entity_extraction` by
`(chunk.content_hash, extractor_version)`. A hit yields the mention list with no
work. `extractor_version` is a fingerprint over: normalizer rules, gazetteer
version, pattern set, prompt text, model deployment name — computed exactly like
`enrich.abstract_version()`.

### Stage 2 — gazetteer pass (deterministic, no model)

Match the chunk text against the in-process alias index (`gazetteer.py`), built
from `entity_alias.normalized` and refreshed on a version bump. Implementation:
an Aho-Corasick-style longest-match scan over a normalized token stream, built
from a plain dict + trie in pure Python — no new dependency. Properties:

- Longest match wins ("The Energy and Resources Institute" beats "Energy").
- Word-boundary anchored on the normalized token stream, so "TERI" does not fire
  inside "TERITORY".
- Case-sensitivity is per-alias: acronyms (<=5 chars, all-caps in source) require
  a case-sensitive match; multi-word names do not. This is what stops "MAY" (a
  month) matching an acronym and "WHO" matching the pronoun.
- Emits `extraction_method='gazetteer'`, `extraction_confidence=0.95`, and
  **already carries the candidate `entity_id`** — a gazetteer hit is a resolution
  Tier 1 hit in the same step.

This is the workhorse. Because the gazetteer is seeded from CMS records, most
mentions of known people, projects, and organizations are found here at zero
model cost.

### Stage 3 — pattern pass (deterministic, no model)

Regex/heuristic extraction for the shapes a gazetteer cannot know:

- **Identifier codes** — `P-1024`, `TERI/2023/0451`, grant/award numbers.
  Configurable per-scheme patterns. These are the highest-value extractions
  because they resolve at Tier 0 with certainty.
- **Titled persons** — `(Dr|Prof|Mr|Ms|Mrs|Shri|Smt|Sh)\.?\s+<CapWords>{1,4}` ->
  PERSON. The honorific is a strong type signal and is stripped by
  `normalize.py`.
- **Organization suffixes** — trailing
  `Institute|University|Ministry|Department|Council|Foundation|Limited|Ltd|Pvt|Corporation|Board|Authority|Agency|Commission`
  -> ORGANIZATION / INSTITUTION / DEPARTMENT.
- **Project phrasings** — `Project <CapWords>` / `<CapWords> Project` /
  `the <CapWords> programme`.
- **Parenthetical acronym definitions** —
  `The Energy and Resources Institute (TERI)`. These are gold: they *define an
  alias in the text itself*, and they are the single best source of new
  abbreviation aliases. Emitted as a mention **plus** a proposed alias with
  `source='derived'`.

`extraction_confidence` 0.55-0.85 depending on pattern strength.

### Stage 4 — LLM NER (optional, budgeted, off by default)

Only for chunks that Stages 2-3 left **suspiciously empty**: a chunk whose text
carries capitalization/honorific density suggesting entities but which produced
none. Structured output via `.with_structured_output(MentionBatch)` where
`MentionBatch` is a pydantic model of `[{surface, type, quote}]`, with two hard
gates copied from `date_llm`:

1. **Every mention must quote the document.** The returned `surface` must appear
   verbatim in the chunk text (offsets recomputed by us, not trusted from the
   model). A mention that cannot be located is dropped. This is what stops a
   paraphrase becoming an entity.
2. **The model never assigns an `entity_id`.** It produces a surface form and a
   type; resolution is a separate stage it cannot reach.

Gated by `entity_llm_ner_enabled` (default `False`) and a per-run chunk budget.
Results are cached by chunk content hash, so the cost is paid once per distinct
text ever.

### Stage 5 — normalize, dedupe, persist

- `normalize.py`: casefold, collapse whitespace, punctuation->boundary (matching
  `resolve._normalize` exactly, so ingest-time and query-time normalization can
  never diverge), strip honorifics into a separate flag, expand/record initials,
  strip trailing org suffixes into a separate flag.
- Deduplicate within a chunk on `(char_start, char_end, normalized)`; the
  `UNIQUE KEY uq_mention_span` enforces it at the DB level too.
- **Do not** deduplicate across chunks: child overlap means the same sentence can
  appear in two chunks, and both are legitimate independent evidence. Counting
  queries use `COUNT(DISTINCT document_id)`, exactly as the existing facet tables
  do.
- Write `entity_extraction` cache row + `entity_mention` rows in one transaction
  with the document's other catalog writes.

### Failure contract

Extraction **fails open**: any exception logs a warning and the document indexes
with no mentions, matching `_enrich`. The document is fully searchable; only the
knowledge layer is thinner. `entity_extraction.attempts` counts failures so a
pathological chunk stops being retried.

---

# E. Entity Resolution Pipeline

## E.1 Candidate generation (blocking)

Never compare a mention against all entities. Blocking keys, unioned, per
mention:

| Key | Purpose | Index used |
|---|---|---|
| exact identifier `(scheme, value)` | Tier 0 | `entity_identifier` PK |
| exact `normalized` | the common case | `entity_alias.idx_normalized` |
| `(entity_type, normalized)` | type-scoped exact | `entity.idx_type_norm` |
| last-token key (PERSON) | `"r sharma"` and `"raj sharma"` share `sharma` | derived `normalized` prefix index |
| acronym key | `teri` <-> initials of `the energy and resources institute` | precomputed alias of type `acronym` |
| first-3-chars-of-each-token | catches spelling variants | derived, in-memory from gazetteer |

Type is a **hard block**: a PERSON mention is never compared to an ORGANIZATION
entity. This alone eliminates a large class of false merges (e.g. a person named
after an institution).

Candidate sets are expected to be small (single digits to low tens). Cap at 25 by
blocking-key strength; overflow means the name is generic, which is itself a
signal to defer.

## E.2 Scoring — features, not a single similarity number

The core requirement — *do not merge on name similarity alone* — is enforced
structurally, not by threshold tuning. Features per (mention, candidate):

**Name features** (reusing `app/core/namematch.py`, i.e. today's tuned `difflib`
scoring)

- `s_exact` — normalized strings equal
- `s_ratio` — whole-string `SequenceMatcher` ratio
- `s_token_set` — word-order-insensitive ratio
- `s_prefix` — single-token prefix/abbreviation score
- `initial_compatible` — `"r sharma"` vs `"raj sharma"`: initials consistent, no
  contradiction
- `name_specificity` — how discriminating the surface is (token count, corpus
  frequency of the surname/token). `"Sharma"` alone is low;
  `"Rajendra Kumar Sharma"` is high.

**Structural / corroborating features** (the ones that actually license a merge)

- `f_identifier` — an exact identifier matched
- `f_org` — mention's document/context organization matches an entity
  `affiliation` attribute
- `f_department`, `f_location` — same, for those attributes
- `f_cooccurrence` — mention's chunk/document co-mentions overlap the entity's
  known co-mentions (a person's collaborators are strong evidence)
- `f_document_shared` — the entity is already linked to this same document
- `f_temporal` — mention's document `published_at` falls inside the entity's
  attribute validity window, or at least does not contradict it
- `f_cms_link` — the document references the entity's source node via
  `entity_refs`
- `f_semantic` — cosine between the mention's chunk vector and the entity's
  profile vector; used only as a tie-breaker, never as a licence

**Negative features (vetoes)**

- `v_identifier_conflict` — mention carries identifier X, candidate holds
  identifier Y != X -> **hard reject**, whatever the name similarity
- `v_org_conflict` — mention's org contradicts every known affiliation *within
  the document's date window* -> strong penalty
- `v_type_conflict` — hard reject (already blocked)
- `v_temporal_impossible` — e.g. mention dated before the entity's `valid_from`
  on an exclusive attribute -> strong penalty

Score = a **transparent weighted sum** with the weights stored in config, not a
learned model. Explainability is a hard requirement here (§I), and an
interpretable linear score whose terms are all persisted in `decision.features`
is auditable in a way a black box is not. Weights are calibrated in Phase 0
against the gold set, not guessed.

## E.3 The tiers, in order — first decisive tier wins

**Tier 0 — identifier.** An exact `(scheme, value)` hit resolves at confidence
1.0, `rule='identifier_exact'`. This is the only tier that may merge with no
corroborating signal, because `entity_identifier` has a
`PRIMARY KEY (scheme, value)` — the uniqueness is a database invariant, not an
inference. A conflict is a hard reject and a `candidate_split` review row.

**Tier 1 — unique autolinkable alias.** `normalized` matches exactly one alias
with `autolink=1` and `is_ambiguous=0`, of the right type -> resolve at 0.97,
`rule='unique_alias_autolink'`. If it matches *several* entities -> straight to
AMBIGUOUS, no scoring, no guessing.

**Tier 2 — high name similarity + one corroborating signal.** `s_exact` or
`s_ratio >= 0.90`, **and** at least one of
`f_org / f_department / f_location / f_cooccurrence / f_document_shared /
f_cms_link` is true -> resolve, `rule='name_plus_context'`. Name similarity alone
at this tier is *not* sufficient; it falls to Tier 3.

**Tier 3 — scored dominance.** Full feature score, with the *margin* over the
runner-up as a first-class criterion (exactly the `_ACCEPT_MARGIN` logic already
in `resolve.classify_band`). Bands per §F. Low `name_specificity` caps the
achievable band: a bare surname can never reach AUTO.

**Tier 4 — LLM adjudication.** Only for mentions that land in the AMBIGUOUS band
**with 2-5 plausible candidates** and enough context to be decidable. See §F.

**Tier 5 — create or defer.**

- Confident new entity (specific multi-token name, clear type, no plausible
  candidate above the floor) -> create with `trust='provisional'`,
  `source='text'`, `rule='no_candidate_create'`.
- Otherwise -> leave `resolved_entity_id=NULL`, `band='unresolved'`. **An
  unresolved mention is a successful outcome**, fully recorded and re-resolvable
  later; it is not an error.

## E.4 How this design minimizes false merges

Seven independent mechanisms, in decreasing order of how much work they do:

1. **Seeded from CMS records with real UUIDs.** Most entities are not inferred at
   all — they are `people`/`projects`/`services` nodes and taxonomy terms with
   authoritative identity. The hardest part of entity resolution is mostly
   bypassed on this corpus.
2. **Type is a hard block.** No cross-type merge is even considered.
3. **Name similarity alone never merges** above Tier 1. A merge needs an
   identifier, a unique unambiguous alias, or a non-name corroborating signal.
4. **`autolink=0` on shared surfaces.** `"R. Sharma"`, `"Sharma"`, `"Phoenix"`
   (when shared) are recognized but structurally unable to resolve alone.
5. **Margin, not just score.** A 0.88 top score with a 0.86 runner-up is a tie,
   not a win — the existing tuned `_ACCEPT_MARGIN=0.30` logic.
6. **Vetoes override similarity.** An identifier conflict rejects a 1.00 name
   match.
7. **Merges are reversible and logged.** `merged_into` is a pointer,
   `entity_merge_log` records the exact `mention_ids`. A false merge is a
   recoverable incident, not corruption.

And one asymmetry baked in throughout: **the default action on doubt is "do not
merge."** Two duplicate entities cost recall and are trivially fixable by a later
merge. One false merge contaminates every downstream claim about both entities
and is expensive to unwind. Every threshold below is chosen on that asymmetry.

---

# F. LLM/Model Strategy — and the confidence model

## F.1 Confidence bands and thresholds

| Band | Condition | Action |
|---|---|---|
| **AUTO** | `score >= 0.90` **and** `margin >= 0.15` **and** >=1 corroborating feature **and** no veto | Link automatically |
| **REVIEW** | `0.75 <= score < 0.90`, `margin >= 0.15`, no veto | Link, `band='review'`, queue a `candidate_merge` review row. Reversible by design. |
| **AMBIGUOUS** | `score >= 0.60` **and** `margin < 0.15` (a genuine tie) | Do **not** link. Queue for LLM adjudication if eligible, else `ambiguous_mention` review. |
| **NEW** | best `score < 0.60`, name is specific, type is clear | Create a provisional entity |
| **UNRESOLVED** | anything else (generic name, veto fired, no context) | Leave NULL; re-resolvable later |

**Why these numbers, and not arbitrary ones.**

- **0.90 for AUTO** is the value `resolve._ACCEPT_SCORE` already uses for
  "near-exact, accept regardless of the runner-up", tuned in
  `docs/database-retrieval-redesign.md §4` against worked examples on *this
  corpus's* author and theme names. Reusing it means one calibrated notion of
  "near-exact" in the codebase rather than two. It is then made *stricter* than
  the query-time version by the additional margin and corroborating-feature
  requirements — correct, because a wrong query-time match shows the user the
  wrong list and they retype, while a wrong merge silently contaminates the
  store.
- **0.60 floor** is `resolve._AMBIGUOUS_FLOOR` / `_ACCEPT_FLOOR`, same
  provenance: below it, matches on this corpus are noise (the doc records
  unrelated names scoring ~0.38).
- **0.15 margin** is *half* the query-time `_ACCEPT_MARGIN=0.30`. Deliberate: at
  query time the margin is the only tie-break, so it must be wide; here the
  corroborating-feature gate carries much of that load, so demanding 0.30 on top
  would reject nearly every legitimate link. Half is the starting point and is
  **the single most important number to calibrate in Phase 0** against the gold
  set's same-name-different-person cases.
- **0.75 for REVIEW** exists because the alternative — a hard cliff at 0.90 —
  throws away every recoverable near-match. Linking at 0.75-0.90 *while flagging
  it* keeps recall and keeps the error visible and cheap to undo.
- **LLM override minimum 0.90**, mirroring `date_llm.MIN_OVERRIDE_CONFIDENCE=0.9`,
  which was itself *raised* from 0.85 after manual review for exactly this
  reason: a decision nothing else in the system would make must be near-certain.

All configurable:

```
entity_auto_min_score          = 0.90
entity_auto_min_margin         = 0.15
entity_review_min_score        = 0.75
entity_ambiguous_floor         = 0.60
entity_new_entity_min_score    = 0.60   # below this, consider creating
entity_llm_min_confidence      = 0.90
entity_mention_min_confidence  = 0.50   # extraction floor
```

## F.2 Where each technique is used, and why

| Technique | Used for | Never used for | Cost |
|---|---|---|---|
| **Deterministic rules / normalization** | honorific & initial handling, type inference from suffixes, identifier patterns, acronym definitions | scoring a genuine ambiguity | free |
| **Gazetteer (dictionary) exact match** | the bulk of mentions of known entities; Tier 1 resolution | discovering unknown entities | free, in-process |
| **Normalized / fuzzy match (`difflib`)** | candidate *generation* and one feature among many | licensing a merge on its own | free, ~us per pair on small blocks |
| **Metadata / structural signals** | the corroborating gate that licenses Tier 2 | — | one indexed SQL read per mention batch |
| **Embeddings** | tie-breaking within an already-narrow candidate set; entity profile similarity | primary matching signal; entity discovery | reuses chunk vectors already in Qdrant — **no new embeddings for Phase 1-5** |
| **LLM** | (a) NER only on chunks the deterministic passes left suspiciously empty; (b) adjudication of 2-5 way ties with real context | any mention a deterministic tier settled; bulk extraction; assigning `entity_id` | budgeted, cached, off by default |

## F.3 The LLM adjudication contract

Modelled directly on `date_llm.py`'s four safety properties:

1. **The model never links.** It returns a verdict; the resolver applies the
   gates and writes the decision.
2. **A verdict must quote the document.** The response must carry the verbatim
   evidence phrase supporting its choice, and that phrase must be present in the
   chunk text. Unquotable -> downgraded to `review`.
3. **Only `verdict='same'` at confidence >= 0.90 can link.** `different`,
   `unknown`, and lower confidence all mean "do not merge."
4. **It sees a bounded prompt** — the mention with +/-300 chars of context, the
   document's title/type/date/authors, and 2-5 candidate profiles (canonical
   name, type, top aliases, known affiliations with dates, 3 example
   co-mentions). Never a whole document, so per-call cost is bounded and
   predictable.

The model is also given an explicit fourth option — `"needs_more_context"` —
because forcing a binary choice on genuinely underdetermined input is how false
merges get manufactured.

## F.4 Expected cost distribution

Ordered by share of mentions, with the tier that settles them:

```
CMS-field mentions           -> Tier 0/1, zero model cost
Gazetteer hits               -> Tier 1, zero model cost
Pattern hits on known names  -> Tier 2, zero model cost
Pattern hits, new names      -> Tier 3/5, zero model cost
Genuine ties, 2-5 candidates -> Tier 4, ONE bounded LLM call, cached
```

The LLM budget is therefore proportional to *ambiguity*, not to corpus size —
which is the requirement. Concretely: a per-run cap
(`entity_llm_max_calls_per_run`) plus caching by
`(chunk_content_hash, extractor_version)` for NER and by
`(mention normalized, candidate id set, prompt_version)` for adjudication, so a
recurring ambiguity is paid for once, not once per sighting.

---

# G. Ingestion Integration

## G.1 Exact insertion points

**`app/ingestion/pipeline.py::_handle`** — one call, inside the content-changed
branch, between chunking and indexing:

```
version = cd.next_version(record)
doc.doc_version = version
with span("ingest.chunk"):
    new_chunks = chunk_canonical(doc)
+ with span("ingest.entities"):
+     knowledge = _extract_entities(doc, new_chunks)   # fails open, returns a tally
chunks = index_chunks(new_chunks)
delete_document(record.document_id, keep_ids=[...])
_persist(record, doc, content_hash, version, indexed=True)
+ _persist_entities(record, knowledge)                 # fails open
```

`_extract_entities` mirrors `_enrich` exactly: flag check, try/except -> warning
+ empty result, outcome string fed to the existing `note()` so `enrich_*`-style
counters appear in the run tally (`entity_mentions`, `entity_auto`,
`entity_review`, `entity_ambiguous`, `entity_new`, `entity_cache_hit`,
`entity_llm_calls`).

**`app/ingestion/pipeline.py::_run`** — add `entity_tables.ensure_table()` next
to the existing `enrichment.ensure_table()`, guarded by the same
try/except-and-log.

**`app/observability/metrics.py`** — add to `_COMPONENTS`:
`"ingest.entities": "other"`, `"ingest.entity_llm": "llm"`. Without this the new
span silently lands in "other" and the cost is invisible.

**Deliberately NOT touched:**

- `chunk_canonical` / `build_payload` / `DocumentMeta` / `Chunk` — no new fields
  in Phase 1-5. Payload changes are Phase 6 and go through `set_payload`, not
  through the chunker.
- `CanonicalDocument.extra` — never; it leaks into every chunk payload.
- `compute_content_hash` — never; changing it re-versions and re-embeds the
  entire corpus.
- `EntityRef` — kept as the CMS-reference model it is. The knowledge layer
  *reads* it.

## G.2 Lifecycle by change status

| Status | Mentions | Canonical entities |
|---|---|---|
| **NEW** | Extract + resolve | May create provisional entities |
| **CHANGED, content_hash same** (`unchanged_content`) | **Nothing.** No re-chunk, so chunk ids and mentions are still valid. Title-only edits are already handled by `refresh_document_title`. | Untouched |
| **CHANGED, content_hash differs** | Delete this document's mentions for the *old* `doc_version`, extract + resolve the new chunks. Per-chunk extraction cache means unchanged paragraphs cost nothing. | Never deleted. Counts refreshed. |
| **UNCHANGED** (fingerprint match) | Nothing — the crawl never even builds the document | Untouched |
| **DELETED** | Cascade-deleted with the `documents` row (FK) | **Never deleted.** See below. |
| **Restored** (same `document_id` returns) | Re-extracted as NEW; per-chunk cache makes this nearly free | Re-linked; `entity_id`s are unchanged, so all prior aliases and attributes still apply |

**Why deleting a document must not delete its entities.** An entity is a
real-world thing attested by many documents. `entity_mention` cascades (the
*evidence* is gone), but the entity row, its aliases, and its identifiers persist
with `mention_count`/`document_count` decremented. An entity that drops to zero
mentions becomes `orphaned` — reportable and prunable by a maintenance task,
exactly as `documents_enrichment` orphans are handled today, never cascaded. If
it were cascaded, deleting one news item could destroy the identity of a person
named in 300 PDFs, and re-ingesting that news item would mint a *new* `entity_id`
— every downstream claim silently repointed. This is the single most important
lifecycle rule in the design.

**Re-resolution without re-extraction.** Resolution quality improves as the
gazetteer grows, so `entity_mention` rows carry `resolver_version` separately
from `extractor_version`. A resolver upgrade re-resolves *stored* mentions with
zero extraction cost — a batch CLI over `resolver_version < current`, ordered by
band (unresolved and ambiguous first, since those are the ones a better resolver
actually helps). Already-AUTO mentions are re-resolved only under an explicit
`--all` flag, because silently repointing confident links is itself a risk.

## G.3 Backfill

`app/knowledge/backfill.py`, modelled line-for-line on `enrich_backfill.py`:

- Work list derived from what is *missing* (`documents` rows with
  `indexed_at IS NOT NULL` and no mentions at the current `extractor_version`) ->
  resumable by construction.
- Chunk text reconstructed **from Qdrant** (`enrich_backfill.document_text`
  pattern) — no PDF re-downloaded, no site re-crawled. Reads `chunk_text`,
  `chunk_id`, `content_hash`, `chunk_index`, `page_number`, `section_heading` per
  child point, which is everything a mention row needs.
- Ignores the feature flag and takes an explicit `--limit`, because it is the
  operation that can spend money, and it must be runnable *before* the flag is
  flipped.
- `--dry-run` reports the pending count and spends nothing.

---

# H. Retrieval Integration (design only — not implemented in this work)

## H.1 Target query-time flow

```
User query
   |
process()                        <- existing, unchanged
   |
QueryUnderstanding.scope          <- existing: author / theme / tags / dates
   |
[NEW] entity detection            gazetteer scan over the query text (in-process, ~us)
   |
[NEW] entity resolution           the SAME app/knowledge/resolve.py, one code path
   |                              -> EntityMatch[] with the same AUTO/AMBIGUOUS bands
   +- AMBIGUOUS -> clarification, reusing the existing AmbiguousFilter machinery
   |
entity_id[]
   |
[NEW] entity-scoped document set  MySQL: entity_mention -> DISTINCT document_id
   |                              (bounded by the existing _MAX_IDS = 150 cap)
   +- narrow set  -> scoped_retrieval.search_within_documents()   <- EXISTS TODAY
   \- wide set    -> Qdrant filter FieldCondition("entity_ids", MatchAny)  <- Phase 6
   |
rerank -> context_builder -> generation      <- existing, unchanged
```

Two things make this cheap to add: `scoped_retrieval.search_within_documents()`
already implements "catalog picks the ids, Qdrant ranks within them", and
`resolve_filters` already implements "canonicalize a name on the way to SQL,
surface ambiguity instead of guessing." Entity-aware retrieval is a new *source
of ids* for machinery that exists.

## H.2 What it fixes, per example query

**"What projects has Raj Sharma worked on?"** Today: `scope.author="Raj Sharma"`
-> `documents_author LIKE '%Raj Sharma%'`, which misses every document that
writes "Dr. R. Sharma" or names him in body text rather than an author field, and
cannot connect him to project documents where he isn't the author at all. With
entities: resolve to `person_00192`, take `entity_mention -> DISTINCT
document_id`, intersect with `bundle IN (completed_projects, ongoing_projects)` —
including documents where he is *mentioned* rather than credited.

**"Who currently leads Project Phoenix?"** Today: unanswerable — "leads" is a
relation and "currently" is temporal. With entities: `project_00121` scopes
retrieval to the right documents, and `published_at DESC` ordering makes
"currently" meaningful. Fully answered only with claims (§M), but entity scoping
is what makes the retrieved context correct rather than a keyword soup of every
document containing "Phoenix".

**"Which organizations are involved in Phoenix?"** Today: keyword search for
"Phoenix". With entities: documents mentioning `project_00121`, then the
ORGANIZATION mentions co-occurring in those documents — a
`GROUP BY resolved_entity_id` over `entity_mention`, ranked by co-occurrence
count. Answerable from MySQL alone, with citations.

**"Show research related to TERI's solar projects."** The alias problem in its
purest form: today "TERI" misses "The Energy and Resources Institute" and vice
versa. With `entity_alias`, all surface forms collapse to one `entity_id` before
any filter is built, then composed with the existing theme filter.

## H.3 Answer-quality effect

Entity ids also improve *ranking and framing*, not just recall: a chunk that
mentions the resolved entity is demonstrably on-topic, which is a cleaner boost
signal than the existing lexical proxies; and `citations` can name the entity a
passage is evidence *for*, which is what makes the eventual claim layer
explainable to a reader.

---

# I. Provenance and Explainability

The requirement — *"Why did the system decide that `R. Sharma` refers to
`person_00192`?"* — is answered by a single join, by construction:

```sql
SELECT m.surface_text, m.context_before, m.context_after,
       m.char_start, m.char_end, m.page_number, m.section_heading,
       m.extraction_method, m.extraction_model, m.extractor_version,
       m.extraction_confidence,
       d.tier, d.rule, d.decided_by, d.score,
       d.runner_up_id, d.runner_up_score, d.features, d.evidence,
       d.llm_raw, d.prompt_version, d.resolver_version,
       doc.title, doc.url, doc.source_type, doc.published_at, doc.doc_version
FROM   documents_entity_mention m
JOIN   documents_entity_resolution_decision d ON d.mention_id = m.mention_id
JOIN   documents doc ON doc.document_id = m.document_id
WHERE  m.resolved_entity_id = 'person_00192'
  AND  d.superseded_by IS NULL;
```

The full chain is intact at every hop:

```
surface_text + (char_start, char_end)   -> the exact span
  | chunk_id                            -> the exact Qdrant point (retrievable, quotable)
  | chunk_content_hash                  -> the extraction cache entry that produced it
  | document_id + doc_version           -> the document and the version it was read from
  | documents.source_key / url          -> the Drupal node or PDF URL
  | extraction_method + extractor_version -> which pass found it, under which rules
  | decision.tier + rule                -> which tier decided, by which named rule
  | decision.features                   -> every feature value that produced the score
  | decision.runner_up_id + score       -> what we did NOT pick, and by what margin
  | decision.evidence                   -> one human-readable sentence
  | decision.llm_raw + prompt_version   -> the model's verbatim verdict, if any
  \ decision.superseded_by              -> the correction chain
```

Three design choices make this hold up rather than merely look good:

**Named rules, not scores alone.** Every decision carries a `rule` string
(`identifier_exact`, `unique_alias_autolink`, `name_plus_context`,
`scored_dominant`, `llm_confirmed`, `no_candidate_create`, `ambiguous_tie`,
`veto_identifier_conflict`). Debugging then aggregates: "which rule produces our
false merges?" is a `GROUP BY rule` — the same question
`scripts/audit_overrides.py` answers for dates today.

**The runner-up is stored.** A score of 0.91 means nothing without knowing the
second-best was 0.42 (decisive) or 0.90 (a coin flip we should not have called).
Recording it is what makes margin thresholds auditable after the fact rather than
only tunable before.

**Decisions are append-only.** `superseded_by` chains corrections instead of
overwriting, so an incident review can reconstruct what the system believed at the
time it wrote a claim — which is exactly what the future claim/conflict layer will
need.

**Debugging surfaces** (all offline CLIs, none in the public API):

- `python -m app.knowledge.explain --mention <id>` / `--entity <id>` — prints the
  chain above as prose.
- `python -m app.knowledge.report --tier --rule --band` — distributions,
  mirroring `scripts/shadow_corpus_report.py`.
- `python -m app.knowledge.review --list --kind candidate_merge` — the queue,
  highest-occurrence first.

---

# J. Failure Handling

**J.1 No matching entity exists.** Specific name + clear type -> create
provisional (`trust='provisional'`, `source='text'`). Generic or low-specificity
-> leave `band='unresolved'`. Unresolved is a normal, recorded outcome; a later
gazetteer growth re-resolves it with no extraction cost. Not an error, never
logged as one.

**J.2 Multiple entities possible.** `band='ambiguous'`,
`resolved_entity_id=NULL`, one `entity_review` row with the ranked candidates in
`candidates` JSON (reusing `resolve.plausible()`'s "only offer genuinely close
options" rule — a blind top-3 implies a similarity that doesn't exist).
`UNIQUE(kind, entity_id, other_entity_id, surface_text)` + `occurrences`
collapses repeats. At query time an ambiguous entity produces a clarification via
the existing `AmbiguousFilter` path, never a silent guess.

**J.3 Conflicting names across sources.** Both become aliases of one entity;
`canonical_name` is chosen by a precedence rule (CMS `official_name` > most
frequent CMS form > longest attested form), with `alias_type` recording *what
kind* of variant each is (§K). Conflicting values of an *attribute* are not a
naming problem — they become two `entity_attribute` rows with different validity
windows (§L), which is the shape the conflict-resolution layer will consume.

**J.4 Entity renamed.** `canonical_name` updated; the old name is retained as
`alias_type='former_name'` with `valid_to` set. `entity_id` never changes, so no
mention, decision, or claim is repointed. Logged in `entity_merge_log` as
`operation='rename'`. Note the existing `refresh_document_title` precedent: a
display-name change must not trigger a re-embed, and here it doesn't touch Qdrant
at all.

**J.5 Entity deleted.** Two distinct cases, deliberately:

- *Source document deleted* -> mentions cascade (FK), the entity survives with
  decremented counts. May become `orphaned`; pruning is a maintenance task, never
  a cascade. (§G.2 explains why this is the most important rule here.)
- *Entity judged not to exist* (an extraction artefact) -> `status='rejected'`,
  never a row delete. Its mentions are set to `band='unresolved'` so a correct
  future resolution can claim them, and the surface is optionally recorded as a
  stop-form so it isn't re-created next run.

**J.6 Entity merged incorrectly.** `entity_merge_log` holds the exact
`mention_ids`. Unmerge: clear `merged_into`, set `status='active'`, repoint
exactly those mentions back, write an `operation='unmerge'` row with
`reverted_by`. Nothing is reconstructed by re-running resolution — the log is the
record. If Phase 6 payload writes happened, the affected documents' `entity_ids`
are rewritten by `set_payload` (no re-embed).

**J.7 A prior resolution decision needs correcting.**
`python -m app.knowledge.correct --mention <id> --entity <id> --reason "..."`
writes a **new** decision row with `decided_by='human'`, sets `superseded_by` on
the old one, and updates the mention. Human decisions are terminal: a later
automated pass must not overturn them, enforced by skipping mentions whose newest
live decision has `decided_by='human'`. Without that rule, every correction is
silently undone by the next backfill.

**J.8 Extraction or resolution fails outright.** Fails open, per the existing
convention: warning logged, document indexes and is fully searchable,
`entity_extraction.attempts` incremented so a hopeless chunk stops being retried.
A model outage must never change what the store believes — the same property
`date_resolution._interpret` enforces with its `llm_unavailable` branch.

---

# K. Duplicate and Alias Handling

## K.1 The TERI case

| Surface | `alias_type` | `autolink` | Why |
|---|---|---|---|
| The Energy and Resources Institute | `official_name` | 1 | Current legal name; highly specific |
| TERI | `acronym` | 1 | Attested initialism of the official name; case-sensitive match required |
| Tata Energy Research Institute | `former_name` | 1 | Renamed 2003; `valid_to='2003-12-31'` |
| T.E.R.I. | `initialism` | 1 | Punctuation variant — collapses under `normalize.py` |
| Energy and Resources Institute | `spelling_variant` | 1 | Article-dropped form |
| The Institute | `nickname` | **0** | Ubiquitous and context-dependent; recognized, never autolinked |

The mechanism: **all six point to one `entity_id`**; the distinctions live in
`alias_type`, `autolink`, and `valid_from/valid_to`. A former name still resolves
(documents from 2001 legitimately use it), but `f_temporal` scores a 2001
document using "Tata Energy Research Institute" higher than a 2024 one would —
which is how the temporal window earns its keep in scoring rather than merely
being recorded.

## K.2 The Phoenix case

| Surface | `alias_type` | `autolink` | Why |
|---|---|---|---|
| Project Phoenix | `canonical` | 1 | Canonical form |
| Phoenix Project | `spelling_variant` | 1 | Word-order variant — `_token_set_ratio` handles it natively |
| P-1024 | `code` | 1 | Also an `entity_identifier` row -> **Tier 0**, the strongest link available |
| Phoenix | `nickname` | **0 if shared** | Autolinks only while it is unique among PROJECT entities |

`autolink` on "Phoenix" is **data-driven, not hand-set**: a maintenance pass sets
`is_ambiguous=1, autolink=0` on any `normalized` value attested for more than one
active entity of the same type. So the moment a second Phoenix-anything appears
in the corpus, the bare form stops autolinking automatically and starts producing
`ambiguous` mentions — the system degrades to honest uncertainty rather than
continuing to merge on a name that is no longer discriminating. This is the
mechanism that keeps false-merge risk from growing with the corpus.

## K.3 Alias vs. genuinely different entity

The distinction is never made on string similarity:

| Case | Signal | Outcome |
|---|---|---|
| **Alias** | Same identifier, or same CMS UUID, or name variant + corroborating context | One entity, new alias row |
| **Abbreviation** | Parenthetical definition in text (`Full Name (ABBR)`), or initials-of-tokens match | One entity, `alias_type='acronym'` |
| **Spelling variation** | High `s_ratio` + corroborating context, no conflicting identifier | One entity, `alias_type='spelling_variant'` |
| **Alternate official name** | CMS record carries both, or a documented rename with dates | One entity, `official_name` / `former_name` + validity |
| **Genuinely different** | Identifier conflict (hard), or contradicting affiliation within the same window, or a tie with no corroboration | Two entities. `entity_alias` gets `is_ambiguous=1, autolink=0` on the shared surface. |

"Raj Sharma — TERI" vs. "Raj Sharma — IIT Delhi" is the last row: identical
names, `s_exact=1.0`, and **still two entities**, because `v_org_conflict` fires
and no corroborating feature survives it. A `candidate_merge` review row is
queued so a human can confirm they're distinct (or that one person moved — §L).
This is the case the whole design is built around, and the one the gold set must
cover most heavily.

---

# L. Entity Versioning and New Information

## L.1 Canonical entities do not need row versioning

Recommendation: **no SCD-2 on `entities`.** Reasons:

1. `entity_id` is immutable and is the only thing downstream data (mentions,
   decisions, future claims) references. Versioning the row would force every
   reference to carry a version, which is exactly the coupling that makes claim
   retraction hard later.
2. Everything genuinely mutable is *already* modelled as a child row with its own
   provenance and validity: names in `entity_alias` (with `valid_from/valid_to`),
   facts in `entity_attribute` (with validity, source, confidence, status),
   identity changes in `entity_merge_log`.
3. So the entity's history is fully reconstructible as of any date by querying
   those children — without the write amplification and join complexity of a
   versioned dimension.

`entities` therefore holds only the immutable identity plus a **current-best
display projection** (`canonical_name`, denormalized counts). That projection is
derivable and disposable; the authority is the children.

## L.2 The "TERI -> IIT Delhi" case, worked

Initial documents: `Raj Sharma` + `TERI`. Later documents: `Raj Sharma` +
`IIT Delhi`. The system must **not** assume the original is wrong. Three
readings, and the design distinguishes them by evidence, not by recency:

| Reading | Evidence | Action |
|---|---|---|
| **(a) One person who moved** | Corroborating signals bridge the two (shared co-mentions, shared identifier, shared project, continuous publication record) | One entity. Two `entity_attribute` rows: `affiliation='TERI' [valid_from ... valid_to=<first IIT doc date>]`, `affiliation='IIT Delhi' [valid_from=... valid_to=NULL]`. **Neither is deleted.** The earlier row is `status='superseded'`, not retracted — it was true then. |
| **(b) Two different people** | No corroboration; `v_org_conflict` fires; disjoint co-mention neighbourhoods | Two entities. Shared surface gets `is_ambiguous=1, autolink=0`. `candidate_merge` review row. |
| **(c) Cannot tell** | Insufficient context | **Default.** Do not merge, do not split an existing entity. `band='ambiguous'`, review row. |

**(c) is the default**, and that is the whole point: the asymmetry from §E.4
applied to temporal change. A new affiliation is never sufficient evidence *on
its own* to either merge two candidates or split one.

## L.3 Temporal semantics — three distinct times, kept apart

The date-resolution work already learned this lesson the hard way
(`date_llm`'s whole design is about not conflating date kinds), so the attribute
model separates:

- **`valid_from` / `valid_to`** — when the fact was true in the world.
- **`asserted_at`** — when *we* learned it (from `documents.published_at` of the
  source).
- **`created_at`** — when the row was written.

A document published in 2024 can assert a fact valid from 2019. Without all
three, "what did we believe in 2022?" and "what was true in 2022?" collapse into
one another — and that distinction is precisely what the future
conflict-resolution layer needs to arbitrate contradictory sources.

Open intervals (`valid_to=NULL`) mean "still true as far as we know", not "true
forever". A query for "who *currently* leads Project Phoenix" therefore ranks by
`asserted_at DESC` among open intervals, and can honestly say "as of the most
recent source, dated X" — which is a citable answer rather than an assertion.

---

# M. Relationship With Future Claim Extraction

Claim extraction is **not** implemented here. The design makes it a
straightforward addition rather than a redesign:

```
Entity   -> entities.entity_id                        (this work)
Claim    -> entity_claim(subject_entity_id, predicate,
                         object_entity_id | object_text)
Evidence -> claim_evidence(claim_id, mention_id, chunk_id,
                           document_id, quote)
Temporal -> claim.valid_from / valid_to / asserted_at
Conflict -> claim.status + claim_conflict(claim_a, claim_b, resolution)
```

`Raj Sharma -worked_on-> Phoenix Project` becomes:

```
entity_claim(subject_entity_id='person_00192',
             predicate='worked_on',
             object_entity_id='project_00121',
             valid_from=..., valid_to=..., asserted_at=...,
             confidence=..., status='active')
claim_evidence(claim_id=..., mention_id=<the R. Sharma mention>,
               chunk_id=..., quote='Dr. Raj Sharma joined the Phoenix project ...')
```

Four properties of *this* work are what make that easy:

1. **Stable `entity_id`s** are the subject/object endpoints. A claim never has to
   be repointed because a display name changed.
2. **`mention_id` is a citable, span-precise anchor.** Claim evidence is a
   foreign key to a real mention with `(chunk_id, char_start, char_end)` — so
   every claim quotes a specific span of a specific version of a specific
   document. This is the property that makes claim verification mechanical rather
   than manual.
3. **`entity_attribute` is already a claim in miniature** — subject, predicate,
   object, validity, source, confidence, status. `entity_claim` is that table
   generalized to entity-to-entity objects. Same shape, same conflict semantics,
   same audit discipline; a reviewer who understands one understands the other.
4. **Co-mention data is a free claim-candidate generator.** `entity_mention`
   grouped by `chunk_id` yields entity pairs that appear in the same passage —
   which is exactly the candidate set a relation extractor needs, already
   indexed, with no additional extraction pass.

One rule to carry forward: **claims must never be extracted for unresolved or
ambiguous mentions.** A claim about an unidentified entity is worse than no
claim, because it looks like knowledge. The `resolution_band` column is what
enforces that gate, and it exists from Phase 2.

---

# N. Evaluation Strategy

## N.1 Datasets

Following the date-resolution precedent (`reports/phase0/date_evalset.json` +
`scripts/eval_date_resolution.py`), under `reports/entities/`:

**`gold_mentions_v1.json`** — ~40 real chunks drawn from across the corpus
(website nodes, short PDFs, long reports, tables), every entity mention
hand-labelled with surface, type, and offsets. Sized to be *maintainable*: a gold
set nobody updates is worse than a small one that stays true. Must include
negatives — capitalized non-entities ("Annual Report", "Chapter 3", "Table 4"),
sentence-initial capitals, and all-caps headings.

**`gold_resolution_v1.json`** — ~120 (mention -> expected entity) pairs,
deliberately adversarial:

| Class | ~n | Purpose |
|---|---|---|
| Same entity, name variants (`Raj Sharma` / `Dr. Raj Sharma` / `R. Sharma` w/ context) | 25 | Recall |
| **Different entities, identical names** (TERI vs. IIT Delhi Raj Sharma) | **25** | **False merge — the headline** |
| Project aliases (`Phoenix` / `Project Phoenix` / `Phoenix Project` / `P-1024`) | 15 | Alias + identifier tiers |
| Organization aliases (TERI's six forms, incl. the former name) | 15 | Temporal aliases |
| Genuinely ambiguous (`R. Sharma`, no metadata) | 15 | Must be AMBIGUOUS, not resolved |
| Not-an-entity / negatives | 15 | Extraction precision |
| Temporal change (affiliation moves) | 10 | §L behaviour |

**`gold_pairs_v1.json`** — explicit (mention, mention) same/different labels,
which is what pairwise false-merge rate is computed over.

Building it: sample with `scripts/` tooling from the real corpus (the
`build_manual_review.py` / `shadow_pdf_sample.py` pattern already in the repo),
then hand-label. Not synthetic — synthetic names don't reproduce the failure
modes real Indian-English name variation and CMS tagging produce, which is the
same reason the date eval set was built from the actual corpus.

## N.2 Metrics

**Extraction**

- Precision, recall, F1 — at exact span, and at relaxed (overlapping-span) match,
  reported separately because tokenization disagreements are not the same failure
  as a hallucinated entity.
- Per-type precision/recall — an aggregate hides that LOCATION is unusable while
  PERSON is fine.
- Type-confusion matrix.

**Resolution**

- **False merge rate (headline).** Pairwise:
  `FP_pairs / (pairs the system merged)`. Two mentions of genuinely different
  entities assigned the same `entity_id`.
- **False split rate.** Two mentions of the same entity assigned different ids
  (or one left unresolved while the other resolved).
- Pairwise precision / recall / F1, plus **B-cubed** precision/recall (which,
  unlike pairwise, doesn't let one huge correct cluster mask errors in small ones
  — the exact failure mode of a name-frequency-skewed corpus like this one).
- Resolution accuracy on the gold pairs, by tier and by rule — so a regression is
  attributable.
- **Unresolved rate** and **ambiguous rate**. Both should be *non-zero*; a system
  that resolves everything is a system that is guessing. Targets are ranges, not
  minima.
- **Review-queue precision** — of the cases flagged REVIEW, what share a human
  actually changes. Too low and the queue is noise nobody reads.

**Cost and latency**

- LLM calls per 1,000 mentions; extraction-cache hit rate; mean/p95 added ms per
  document (span `ingest.entities`); resolution throughput (mentions/sec); tokens
  per adjudication.

## N.3 Acceptance gates

Published before implementation, so the numbers are targets rather than post-hoc
rationalizations. Calibrated on the Phase 0 baseline, but with these as the
intended bars:

| Metric | Gate |
|---|---|
| **False merge rate** | **< 1%** at AUTO. Any regression blocks a release, however good recall looks. |
| Extraction precision (PERSON, ORG) | >= 0.90 |
| Extraction recall (PERSON, ORG) | >= 0.75 (recall is recoverable; precision is not) |
| Resolution accuracy on gold | >= 0.90 at AUTO |
| Same-name-different-entity cases | **100% kept separate.** Zero tolerance — this is the failure the design exists to prevent. |
| Ambiguous cases correctly deferred | >= 0.90 |
| LLM calls per 1,000 mentions | < 50 |
| Added ingest latency per document | < 200 ms p95 without LLM NER |

`scripts/eval_entity_resolution.py`, mirroring `eval_date_resolution.py`: runs
the deterministic tiers on every case and the LLM only on cases the tiers defer —
the same routing production uses, so the score reflects the whole pipeline rather
than either half. Writes `reports/entities/eval_report.md`. `--no-llm` for a free
deterministic-only run in CI.

---

# O. Performance and Scalability

## O.1 Volume estimates

Grounded in what the code and docs record — ~16 bundles, 918 completed projects,
~1,545 pre-2018 attachments, low-hundreds of authors, ~200 themes, ~237 tags —
with a 10x growth allowance:

| Quantity | Today (est.) | At 10x |
|---|---|---|
| Documents (nodes + attachments) | ~10 K | ~100 K |
| Child chunks (~450 tok) | ~500 K | ~5 M |
| Mentions (~4 per child chunk) | ~2 M | ~20 M |
| Canonical entities | ~5 K | ~50 K |
| Aliases | ~15 K | ~150 K |
| Resolution decisions | ~2 M | ~20 M |

`entity_mention` at 20 M rows is a large but entirely ordinary InnoDB table given
the indexes in §C.4 — it is not a reason to reach for different infrastructure.

## O.2 Bottlenecks, in the order they will actually bite

1. **`entity_mention` write volume.** ~4 rows per chunk on a full backfill.
   Mitigation: `executemany` batched per document (the `_replace_facet` pattern),
   one transaction per document (never per mention), and a full backfill run
   under `--limit` off-peak like `enrich_backfill`. This is the #1 cost and it is
   a one-time backfill cost, not a steady-state one.
2. **Gazetteer memory and rebuild.** ~150 K aliases in a Python trie ~= 50-100 MB.
   Mitigation: build once per process behind `lru_cache` (the
   `_cached_author_names` pattern), keyed by gazetteer version; a
   `reload_gazetteer()` for tests and post-seed refresh. If it ever outgrows
   memory, shard by `entity_type` — each pass only needs the types it is scanning
   for.
3. **Candidate generation per mention.** Fatal if it hits MySQL per mention.
   Mitigation: blocking keys resolve **in-process** against the gazetteer, so the
   common path does zero SQL. Only Tier 3 context features need a DB read, and
   those are batched **per document** — one query fetching context for all of a
   document's mentions, not one per mention.
4. **LLM adjudication.** Bounded by construction: only ties reach it, results are
   cached by `(normalized, candidate id set, prompt_version)`, and
   `entity_llm_max_calls_per_run` caps a run. Cost scales with *ambiguity*, which
   is roughly constant per new entity, not with corpus size.
5. **Denormalized counters.** `mention_count`/`document_count` updated per
   mention would serialize every worker on a handful of hot entity rows — a real
   deadlock risk under `ingest_workers > 1`. Mitigation: **do not** maintain them
   transactionally. Refresh them in a periodic aggregate pass
   (`python -m app.knowledge.refresh_counts`), accepting staleness. They are a
   display convenience, never a correctness input.
6. **Concurrency.** `ingest_workers > 1` means several documents resolve at once
   and two may create the same entity. Mitigation:
   `UNIQUE(entity_type, source_uuid)` for seeded entities, and for text-created
   ones an `INSERT ... ON DUPLICATE KEY UPDATE` on a
   `UNIQUE(entity_type, normalized_name, trust='provisional')` guard so a race
   yields one row, not two. Keep `ingest_workers < mysql_pool_size`, as the
   existing config comment already warns.
7. **Re-resolution passes.** A resolver upgrade over 20 M mentions is a batch
   job, chunked by `mention_id` range with a resumable cursor, band-prioritized
   (unresolved/ambiguous first). Never inline in a sweep.

## O.3 Why this scales without an LLM per comparison

The cost of resolving one mention is: one in-process trie lookup + a handful of
Python string comparisons against a blocked candidate set of <25 + at most one
batched SQL read shared across the document. That is microseconds, and it is what
settles the overwhelming majority of mentions. The LLM is reached only by genuine
ties, which are cached and per-run capped. Corpus growth multiplies the cheap
path and leaves the expensive path roughly flat — because a bigger corpus mostly
means *more mentions of entities we already know*, which is precisely the case
the gazetteer handles for free.

## O.4 Caching layers

| Cache | Key | Invalidated by | Precedent |
|---|---|---|---|
| Chunk extraction | `(chunk_content_hash, extractor_version)` | version bump | `documents_enrichment` |
| Gazetteer | process-local, gazetteer version | `reload_gazetteer()` | `_cached_author_names` |
| Adjudication verdicts | `(normalized, candidate ids, prompt_version)` | prompt/model change | `documents_date_decision.llm_raw` |
| Entity profile vectors (Phase 6+) | `entity_id` + profile hash | profile change | — |

---

# P. MySQL vs Graph Database

**Recommendation: MySQL only. Do not introduce a graph database.** This confirms
the stated preference, and the reasoning is not merely deference:

**The query patterns are 1-2 hops.** Every query in §H is a bounded join:

- "documents mentioning X" — one indexed lookup on `idx_entity_doc`
- "organizations co-occurring with X" — self-join on `chunk_id`, `GROUP BY`
- "projects a person worked on" — mentions -> documents -> bundle filter
- "who leads X now" — claims by subject, ordered by `asserted_at`

None of these is a graph traversal. They are star-schema joins, and MySQL 8 with
the indexes in §C is the right tool. `docs/database-retrieval-redesign.md §2.1`
already establishes the catalog *is* a star schema.

**The existing operational surface is MySQL.** One connection pool, one DDL
discipline, one backup story, one set of idempotent `ensure_*` migrations, one
set of test conventions. A graph DB adds a second store to operate, back up, keep
consistent with MySQL, and reason about during a partial failure — for query
shapes that don't need it. That cost is real and immediate; the benefit is
hypothetical.

**Transactional integrity matters here.** Mentions and their decisions must be
written atomically with the document's catalog rows, and FK CASCADE is doing real
lifecycle work (§G.2). Splitting the knowledge layer into a second store means
either distributed transactions or an eventual-consistency window during which
provenance is broken — in a system whose headline requirement is auditability.

**Two-hop cost is manageable.** "Which organizations collaborate with
organizations that TERI collaborates with" is the first query where MySQL gets
awkward. Recursive CTEs (MySQL 8) handle 2-3 hops; if a genuine need for 4+ hops
appears, that is the signal to revisit, and it should be revisited with evidence.

**Reconsider when — and only when — one of these is true:** query patterns
genuinely need >=3 unbounded hops; relationship count exceeds ~50 M with
traversal-dominant reads; path queries ("how is A connected to B") become a
product requirement; or graph algorithms (community detection, centrality) become
part of retrieval.

**Migration path, kept clean deliberately:**

- `entity_claim` is stored as
  `(subject_entity_id, predicate, object_entity_id)` — **already a triple**.
  Exporting to Neo4j/Neptune is a `SELECT`, not a remodelling.
- Entity ids are opaque strings, portable as node ids with no rewriting.
- All graph-shaped reads go through one module (`app/catalog/entities.py` + a
  future `app/catalog/claims.py`), so a graph backend is swapped behind that
  interface — exactly how `app/retrieval/structured/tools.py` isolates the
  catalog today.
- No graph semantics leak into the schema (no adjacency lists, no path
  materialization) that would have to be undone.

---

# Q. Migration Strategy

Five properties keep the running RAG system untouched throughout:

1. **Additive schema only.** New tables, no columns on `documents`, no changes to
   any existing table. Idempotent `ensure_entity_tables()` in the existing
   `app/catalog/schema.py`, following the established
   `CREATE TABLE IF NOT EXISTS` + `_ensure_column` pattern. A deployment that
   never enables the feature never creates the tables.
2. **Off by default, one flag per capability.** `entity_extraction_enabled=False`,
   `entity_llm_ner_enabled=False`, `entity_llm_adjudication_enabled=False`,
   `entity_payload_enabled=False`, `entity_shadow_only=True`. Each launches OFF,
   matching the convention that `enrichment_enabled`, `multi_query_enabled`,
   `keyword_leg_enabled`, `corrective_loop_enabled`, and
   `database_multi_call_enabled` all follow — *"the first pass over an existing
   corpus costs real money, so it should be a deliberate act."*
3. **Shadow mode first.** Phases 2-4 write mentions and decisions and change
   **nothing** that retrieval reads — the exact discipline
   `documents_date_candidate` / `documents_date_decision` established. The
   knowledge layer is measured against the gold set on real corpus data before
   anything acts on it.
4. **Fails open everywhere.** Every entity call in the ingestion path is wrapped
   like `_enrich`: warning, continue, document still indexed and fully
   searchable. A broken knowledge layer degrades to today's behaviour.
5. **Qdrant untouched until Phase 6**, and then only via `set_payload` on
   existing points — **no re-embedding, no re-indexing, no collection change**.
   `refresh_document_title` is the precedent: rewrite one payload field over an
   existing document at negligible cost. Reversible by writing the field back
   empty.

**Rollback at each phase:** Phases 1-5 — set flags off; tables become inert
(optionally dropped). Phase 6 — flag off + one `set_payload` pass clearing
`entity_ids`; retrieval ignores the field regardless. Phase 7 — flag off; query
understanding reverts to today's facet path.

**The one refactor**, in Phase 1: extract the pure name-matching primitives from
`app/retrieval/structured/resolve.py` into `app/core/namematch.py` and
re-export. Behaviour-identical, ~40 lines moved, existing tests unchanged.
Justified by removing an ingestion->retrieval import and by guaranteeing
ingest-time and query-time normalization cannot diverge — a divergence that would
be a silent, corpus-wide recall bug.

---

# R. Phased Implementation Plan

## Phase 0 — Corpus survey and gold set (no code in the app)

- **Objective.** Measure what is actually there before designing against
  assumptions, and produce the labelled data every threshold in §F depends on.
- **Files.** `scripts/survey_entity_candidates.py` (new),
  `reports/entities/gold_mentions_v1.json`, `gold_resolution_v1.json`,
  `gold_pairs_v1.json`, `reports/entities/phase0_report.md`.
- **DB.** None. Read-only over `documents` / facets / `raw_meta`, and Qdrant
  chunk text.
- **Work.** Inventory `people` / `*_projects` / `services` nodes and their UUIDs;
  enumerate taxonomy vocabularies reachable via `entity_refs` and classify which
  map to ORGANIZATION / DEPARTMENT / LOCATION; measure name-collision statistics
  over `distinct_authors()` (shared surnames, initials-only forms,
  honorific-prefixed duplicates); sample chunks and hand-label the gold sets; run
  the §F feature weights over the gold pairs to **calibrate** thresholds —
  especially the 0.15 margin.
- **Dependencies.** None.
- **Tests.** None (script output is the deliverable).
- **Risks.** Labelling effort is underestimated. Mitigation: cap at the sizes in
  §N.1 and treat the gold set as living.
- **Acceptance.** `phase0_report.md` states entity counts by type, collision
  statistics, the calibrated thresholds with the evidence for each, and a
  go/no-go on the type list (§S Q1).

## Phase 1 — Schema + CMS seed (deterministic, offline)

- **Objective.** Canonical entities exist, seeded from authoritative CMS records.
  No text is read.
- **Files.** `app/catalog/schema.py` (+`ensure_entity_tables`),
  `app/catalog/entities.py` (new), `app/core/namematch.py` (new, extracted),
  `app/retrieval/structured/resolve.py` (re-export only),
  `app/knowledge/{__init__,types,normalize,seed}.py` (new),
  `scripts/seed_entities_from_catalog.py` (new).
- **DB.** `entity`, `entity_alias`, `entity_identifier`, `entity_attribute`.
- **Dependencies.** Phase 0 type decision.
- **Tests.** `test_entity_schema_migration.py` (idempotency, twice-run no-op —
  mirroring `test_catalog_schema_migration.py`); `test_entity_normalize.py`
  (honorifics, initials, acronyms, punctuation, unicode); `test_entity_seed.py`
  (idempotent re-seed, UUID uniqueness, alias derivation, `is_ambiguous`
  auto-flagging); `test_namematch.py` (asserts extraction preserved existing
  `resolve` behaviour exactly).
- **Risks.** The refactor breaks query-time resolution. Mitigation: pure move, no
  logic change, existing `test_entity_resolution_scoring.py` is the guard. Second
  risk: a taxonomy vocabulary is misclassified as ORGANIZATION. Mitigation:
  explicit allow-list in code, decided in Phase 0, never inferred from field
  names — the lesson `canonical.py` already records about theme hints.
- **Acceptance.** Seeder is idempotent; every seeded entity has >=1 alias and
  (for CMS-sourced ones) a `drupal_uuid` identifier; ambiguous surfaces are
  auto-flagged `autolink=0`; nothing in the ingestion or retrieval path is
  touched; existing test suite passes unchanged.

## Phase 2 — Mention extraction, shadow

- **Objective.** Mentions are extracted and stored with full provenance. Nothing
  is resolved.
- **Files.** `app/knowledge/{gazetteer,extract}.py`, `app/catalog/mentions.py`,
  `app/knowledge/backfill.py`, `scripts/eval_entity_extraction.py`.
- **DB.** `entity_mention`, `entity_extraction`.
- **Dependencies.** Phase 1.
- **Tests.** `test_entity_extraction.py` (gazetteer longest-match, word
  boundaries, acronym case sensitivity, pattern coverage, negatives, offset
  correctness against the source text, chunk-overlap duplicate behaviour, parent
  chunks skipped); `test_entity_extraction_cache.py` (hit/miss, version
  invalidation, attempts counter — mirroring `test_enrichment_cache.py`).
- **Risks.** Gazetteer false positives on short/common aliases. Mitigation:
  `autolink`, minimum alias length, case-sensitivity for acronyms, stop-form
  list; measured against gold before proceeding.
- **Acceptance.** Extraction precision >= 0.90 and recall >= 0.75 on PERSON/ORG
  against `gold_mentions_v1`; every mention's offsets reproduce its
  `surface_text` from the stored chunk text; backfill is resumable and
  `--dry-run` spends nothing.

## Phase 3 — Deterministic resolution (Tiers 0-3), shadow

- **Objective.** Mentions resolve by deterministic tiers with full decision
  provenance. Still nothing downstream reads it.
- **Files.** `app/knowledge/{candidates,scoring,resolve}.py`,
  `app/catalog/entity_decisions.py`, `scripts/eval_entity_resolution.py`.
- **DB.** `entity_resolution_decision`, `entity_review`, `entity_merge_log`.
- **Dependencies.** Phase 2.
- **Tests.** `test_entity_candidates.py` (blocking recall — the true match must
  be *in* the candidate set; type hard-block); `test_entity_scoring.py`
  (per-feature contribution, veto behaviour, band boundaries at exactly the
  configured thresholds); `test_entity_resolution_tiers.py` (**all §S/§K/§L
  cases**: same entity variants, same-name-different-org, project aliases incl.
  `P-1024`, ambiguous `R. Sharma`, identifier conflict rejects a perfect name
  match); `test_entity_decisions.py` (append-only, `superseded_by` chain,
  `runner_up` recorded).
- **Risks.** Threshold miscalibration. Mitigation: the eval gate below;
  thresholds are config, changeable without code.
- **Acceptance.** **False merge rate < 1%** and **100% of
  same-name-different-entity gold cases kept separate**; ambiguous cases deferred
  >= 0.90; zero LLM calls in this phase; `--no-llm` eval runs in CI.

## Phase 4 — LLM adjudication (Tier 4), gated

- **Objective.** Genuine ties get one bounded, quote-required model call.
- **Files.** `app/knowledge/adjudicate.py`, `app/knowledge/resolve.py` (Tier 4
  hook), config flags.
- **DB.** None (uses `decision.llm_raw` / `prompt_version`).
- **Dependencies.** Phase 3 + its acceptance gate met.
- **Tests.** `test_entity_adjudication.py` (unquotable verdict -> downgraded to
  review; `different`/`unknown`/`needs_more_context` never link; confidence <
  0.90 never links; model outage -> mention stays ambiguous, never links;
  `prompt_version` recorded; verdict cache hit avoids a second call).
- **Risks.** Cost blowout; the model becoming a merge oracle. Mitigation: per-run
  cap, verdict caching, and the four contract properties in §F.3 — the model
  cannot link, only confirm what already cleared the structural gates.
- **Acceptance.** LLM calls per 1,000 mentions < 50; adjudication improves
  ambiguous-case accuracy on gold **without any increase in false merge rate**
  (this is a hard AND — a recall win bought with merges is a regression).

## Phase 5 — Ingestion wiring (flag off) + backfill

- **Objective.** The sweep maintains the knowledge layer incrementally.
- **Files.** `app/ingestion/pipeline.py` (`_extract_entities` /
  `_persist_entities`, ~30 lines), `app/observability/metrics.py`
  (`_COMPONENTS`), `app/knowledge/backfill.py`,
  `app/knowledge/{explain,report,review,correct,refresh_counts}.py` CLIs.
- **DB.** None new.
- **Dependencies.** Phase 3 (Phase 4 optional).
- **Tests.** `test_entity_ingestion_lifecycle.py` — the lifecycle matrix from
  §G.2 as executable cases: NEW extracts; UNCHANGED does not;
  `unchanged_content` does not; content change replaces the old version's
  mentions; **DELETED cascades mentions and preserves the entity**; restore
  re-links to the *same* `entity_id`; extraction failure still indexes the
  document; flag off = byte-identical behaviour to today.
- **Risks.** Ingest latency regression; a concurrency-created duplicate entity.
  Mitigation: `ingest.entities` span measured against the < 200 ms p95 gate;
  unique-key guards from §O.2 item 6.
- **Acceptance.** With the flag off, the tally and timings are indistinguishable
  from today; with it on, added p95 < 200 ms per document; full corpus backfill
  completes under `--limit` batches; every §G.2 row has a passing test.

## Phase 6 — Qdrant payload `entity_ids`

- **Objective.** Entity filtering at the vector layer, for wide entity scopes.
- **Files.** `app/knowledge/payload_sync.py` (new),
  `app/core/clients/vector_store.py` (one
  `_ensure_keyword_index("entity_ids")`), `scripts/create_payload_indexes.py`
  (add the field).
- **DB.** None.
- **Dependencies.** Phase 5, plus a stable false-merge rate over a real sweep.
- **Tests.** `test_entity_payload_sync.py` (per-chunk `set_payload`, no
  re-embed, idempotent, reversible clear, merge repoints payloads, failure leaves
  search working).
- **Risks.** Payload drift between MySQL and Qdrant. Mitigation: MySQL is
  authoritative; the payload is a derived cache with a reconcile CLI. Any
  correctness-critical read goes to MySQL.
- **Acceptance.** Payload matches MySQL for a sampled document set; no
  re-embedding occurred (verify `updated_at` changed and vectors did not);
  clearing the field restores prior behaviour exactly.

## Phase 7 — Retrieval integration (separate design doc)

- **Objective.** Query-time entity detection and entity-scoped retrieval.
- **Files.** `app/retrieval/understanding/*`,
  `app/retrieval/scoped_retrieval.py`, `app/retrieval/structured/*`, new flag
  `entity_aware_retrieval_enabled`.
- **Dependencies.** Phase 6. **Out of scope for this plan** — it needs its own
  doc and its own retrieval eval, because it changes what users see.

## Phase 8 — Claim foundation (tables only)

- **Objective.** `entity_claim` / `claim_evidence` / `claim_conflict` exist and
  are populated by nothing yet, so the shape is settled before extraction is
  written. Separate plan.

---

# S. Open Questions / Decisions Needed

Only the ones that genuinely change the work:

**Q1. Which of the seven types do we actually start with?** PERSON,
ORGANIZATION, PROJECT are clearly supported by `people` / `*_projects` nodes and
author facets. INSTITUTION vs ORGANIZATION may be a distinction without a
difference on this corpus (is TERI an ORGANIZATION or an INSTITUTION? if the
answer is "either", the split creates ambiguity rather than removing it).
PROGRAM, DEPARTMENT, LOCATION depend on whether the taxonomy vocabularies Phase 0
finds are actually populated. **Recommendation:** ship PERSON, ORGANIZATION,
PROJECT in Phases 1-5; add the rest per type once Phase 0 shows a populated
source. Decide after Phase 0 — but the INSTITUTION-vs-ORGANIZATION call is needed
up front, since it affects the ENUM and the seeding rules.

**Q2. Can we treat the `people` bundle as authoritative for PERSON identity?** If
those nodes are complete and maintained, PERSON resolution becomes largely a
closed-world lookup and false-merge risk drops dramatically. If they cover only
senior staff (likely), body-text mentions of everyone else are open-world and the
provisional-entity path carries much more weight. This changes the expected LLM
budget materially. **Not determinable from the code** — it needs someone who knows
the CMS.

**Q3. Is there any project-code convention in the corpus?** The `P-1024` example
is illustrative. If real codes exist (in filenames, titles, or a `raw_meta`
field), Tier 0 becomes the dominant PROJECT tier and PROJECT resolution is
near-solved. If not, projects resolve on names alone and need the corroboration
gate much more. Phase 0 can partly answer this by pattern-mining titles and
`raw_meta`, but a known convention would be worth more than mining.

**Q4. Who reviews the queue, and at what volume?** The REVIEW band's value
depends entirely on someone reading it. If nobody will, the honest design
collapses REVIEW into AMBIGUOUS (do not link) — safer, lower recall, no queue. If
there is a reviewer, what weekly case volume is tolerable? That number sets the
REVIEW/AUTO boundary, not the other way round.

**Q5. Should provisional (text-created) entities be visible to retrieval?** An
entity attested only by body text with no CMS record is less trustworthy than a
seeded one. Options: (a) hide from retrieval until promoted by a human or by an
evidence threshold; (b) expose with the `trust` level surfaced.
**Recommendation: (a) for Phase 7** — a confident answer about a hallucinated
entity is worse than a missing one, and promotion is cheap.

**Q6. Is `people` node deletion a real scenario?** §G.2 asserts entities survive
document deletion. If CMS people records are routinely deleted and recreated
(rather than edited), the `UNIQUE(entity_type, source_uuid)` seeding key will
mint new entities for the same person each time. If that happens, seeding needs a
name-based reconciliation step on top of the UUID key.

---

# Recommended First Implementation Slice

**Phase 0 only: the corpus survey and the gold set.** Nothing in `app/`, no
tables, no migrations, no flags.

**Deliverables**

1. `scripts/survey_entity_candidates.py` — read-only over MySQL + Qdrant.
   Reports: `people` / `*_projects` / `services` node counts with UUIDs; every
   taxonomy vocabulary reachable via `entity_refs`, with fill rates, so we know
   which map to ORGANIZATION / DEPARTMENT / LOCATION; name-collision statistics
   over `distinct_authors()` (shared surnames, initials-only forms,
   honorific-prefixed duplicates); pattern-mining of titles/filenames/`raw_meta`
   for project-code conventions.
2. `reports/entities/gold_mentions_v1.json` — ~40 hand-labelled chunks sampled
   from the real corpus, including negatives.
3. `reports/entities/gold_resolution_v1.json` + `gold_pairs_v1.json` — ~120
   adversarial cases per §N.1, with the same-name-different-entity class the
   largest.
4. `reports/entities/phase0_report.md` — the numbers, the **calibrated**
   thresholds with the evidence for each (particularly the 0.15 margin), and a
   go/no-go on the type list.

**Why this is the right first slice**

- It is the only slice with **zero risk** to the running system — no code path, no
  schema, no flag.
- It answers Q1, and partly Q3, with data rather than assumption.
- It produces the artefact everything else is gated on: thresholds cannot be
  justified without labelled data from this corpus.
- It is exactly what was done for date resolution, and that worked:
  `reports/phase0/` measured the corpus first, and the resulting design ended up
  *narrower and safer* than the initial one (`date_rules.py`'s docstring records
  that a whole class of proposed overrides was removed after manual review). The
  same discipline is worth more here, where the failure mode is a false merge
  that contaminates every downstream claim.

**Immediately after (Slice 2), so the sequencing is clear:** Phase 1 —
`ensure_entity_tables()`, `app/core/namematch.py` extraction,
`app/knowledge/normalize.py`, and `scripts/seed_entities_from_catalog.py`. Still
offline, still nothing in the ingestion or retrieval path, but it produces a
real, queryable canonical entity catalog seeded from CMS records with
authoritative UUIDs — which is the foundation everything else in this plan stands
on.
