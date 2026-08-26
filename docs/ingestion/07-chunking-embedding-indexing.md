# 07 — Chunking, Embedding and Indexing

**Purpose.** Turn one document's text into retrievable, embedded, filterable
points in Qdrant — and replace the previous version without the document ever
disappearing from search.

**Inputs.** A `CanonicalDocument` with a `doc_version` assigned.

**Outputs.** Points in the Qdrant collection, and a count of points written.

**Components.** `app/ingestion/chunking/` (segmenter, packer, classifier, payload,
config), `app/ingestion/indexer.py`, `app/core/clients/vector_store.py`,
`app/core/clients/embeddings.py`, `app/ingestion/version.py`.

---

## Parent/child chunking, and why

A **child** is the retrieval unit: a few hundred tokens, embedded, returned by
search. A **parent** is the wider window the child sits in: stored with a
**zero vector** so it is never itself a search hit, and fetched afterwards to give
the answer layer surrounding context.

The two are stored as points in the same collection, told apart by the
`is_parent` payload flag — which every search filters on, and which is one of the
indexed payload fields.

---

## Sizing

`ChunkingConfig` is a frozen dataclass; `config_for(key)` picks a preset by
`source_type` or by bundle, falling back to the base config.

```python
child_target_tokens = 400   child_max_tokens = 512   child_min_tokens = 120
child_overlap_tokens = 60
parent_target_tokens = 1800 parent_max_tokens = 2400
encoding_name = "cl100k_base"
breadcrumb_max_tokens = 32
```

| Preset | Child target / max | Overlap | Parent target / max |
| --- | --- | --- | --- |
| `pdf`, `pdf_attachment`, `manual` | 450 / 560 | 60 | 2000 / 2600 |
| `research_paper(s)` | 480 / 560 | 48 | 2000 / 2600 |
| `report` | 420 / 540 | 60 | 1900 / 2500 |
| `policy`, `policy_brief` | 400 / 512 | 60 | 1800 / 2400 |
| `article`, `website`, and every other news-like bundle | 380 / 480 | 40 | 1600 / 2200 |
| `small_pdf` | 400 / 512 | 50 | **100 000 / 100 000** |

Two notes:

- `website` and `pdf_attachment` are aliased explicitly. `website` is the canonical
  `source_type` for Drupal content (renamed from `article`) and **must** resolve to
  the article preset, not the base config.
- `small_pdf` is selected by `chunk_canonical` when a paginated document has
  `<= small_doc_pages` (10) pages. Its effectively unlimited parent size means a
  short PDF becomes **one parent** holding the whole document, which is exactly the
  context a reader of a 4-page brief wants.

`breadcrumb_max_tokens` is bounded so a runaway title or a garbled OCR heading
cannot dominate the embedding of a short chunk.

---

## Stage 1 — segmentation

`blocks_from_text(text, page)` parses one page into typed `Block`s:
`text`, `code`, `table`, `heading`.

- **Fenced code** (` ``` ` or `~~~`) is captured verbatim to the closing fence.
- **Tables** are runs of consecutive lines with ≥2 pipes.
- **Headings** are decided by `line_heading_level`.
- Everything else buffers into a `text` block, flushed on a blank line or a
  structural boundary.

### Heading detection

`line_heading_level(line, at_block_start, next_line)` returns a level or `None`.
In order:

1. **ATX** (`## Heading`) → the number of hashes. Checked first, so an authored
   `## See http://host for detail` still stands.
2. **Negative signals that outrank everything below**: `_is_junk_heading`
   (≥4-dot ToC leaders, a `|`, `<!--`/`-->` fragments, or fewer than 55% letters
   among non-space characters — OCR symbol soup), a URL, or a list marker
   (`i)`, `(2)`, `a)`).
3. More than 12 words → not a heading.
4. **Numbered** (`4.1 Transition Pathway`): the number must be a plausible section
   number (≤3 dots, no leading zero, first component < 100 — so `0.35` and `250`
   are excluded), the line must not end in terminal punctuation, and the title must
   start uppercase, be ≤8 words and not read as prose. A bare number opening a
   sentence ("4 way segregation centres") is rejected.
5. **Labelled** (`Section`, `Chapter`, `Article`, `Clause`, `Appendix`, `Annex`,
   `Part`) → level 2.
6. The remaining two rules require `at_block_start` **and** a corroborating
   `next_line`, because they rest on capitalisation alone, which a flattened table
   cell ("Water Supply") shares with a real heading:
   - **ALL-CAPS**, ≤8 words, >85% of letters uppercase → level 2.
   - **Title Case**, ≤8 words, every *content* word capitalised → level 3. Minor
     words (`a`, `the`, `of`, `to`, …) are skipped rather than counted against the
     line, so "Scope of the Study" qualifies while ordinary prose — which
     capitalises only its first word — does not.

`_is_body_line(next_line)` is the corroboration: a real heading introduces body
content (≥4 words, or ending in sentence punctuation), whereas a flattened table
cell is followed by the next cell. Passing `next_line=None` means "no context
available", which is deliberately **not** evidence against a heading.

### Sections

`assemble_sections(blocks)` groups blocks under the heading that owns them. One
subtlety: heading detection is a heuristic, so a run of short lines — an extracted
table column, a bare list — can arrive as consecutive heading blocks. **Only the
first titles the section; the rest are demoted to body text.** Folding them into
the heading string instead kept them out of every chunk's `text` and left a section
with no body at all, which packs to zero chunks and drops the text entirely.

`merge_small_sections(sections, min_tokens, enc)` folds any section under
`child_min_tokens` into its predecessor (its heading becoming a text block), and
handles the leading section specially by prepending it to the second.

### Page boundaries

`chunk_pages` blockifies **one page at a time**, so a paragraph broken by a page
break becomes two blocks and reads as a paragraph break. Stitching those back
together is deliberately **not** attempted: the only available signal — the
previous page not ending in punctuation — is dominated by page furniture and figure
captions, which sit exactly at that boundary.

---

## Stage 2 — packing

`packer.pack(blocks, target, max_tokens, min_fill, enc)`:

1. `_expand_atoms` splits any block bigger than its cap into pieces. Text blocks
   use the `target` as a soft cap; `code` and `table` blocks get the `max_tokens`
   hard cap, so a table is kept whole for as long as possible.
   `_split_text_recursive` splits on `\n\n`, then `\n`, then `. `, then ` `, then
   falls back to a hard token split.
2. Greedy accumulation: start a new window when adding the next atom would exceed
   `target` **and** the current window has reached `min_fill`, or when it would
   exceed `max_tokens` outright.

`coalesce_windows` then merges any window under `min_tokens` into the smaller
neighbour that still fits under `max_tokens`. `min_tokens` is a *target* but
`max_tokens` is a *hard limit*, so an undersized window is acceptable where an
oversized one is not — if no merge fits, the window stays short. The scan resumes at
the merged window rather than restarting, because every window before it is already
large enough and rescanning from the start can never find a new merge.

### The tokenizer

`Encoder` wraps `tiktoken` (`cl100k_base`), cached by `get_encoder(name)`
(`lru_cache(maxsize=4)`). If `tiktoken` is unavailable it logs a warning once and
falls back to a **~4 characters per token heuristic**. That fallback keeps ingestion
working offline, but chunk sizes will differ from a run with the real encoder — so
do not mix the two across a corpus.

### Overlap

Each child (except the first in a section) is prefixed with a **carry**: the tail of
the previous child, advanced to the next sentence boundary so both the carried
context and the child start on a whole sentence.

```python
def _with_carry(prev, text, overlap, max_tokens, enc):
    budget = min(overlap, max_tokens - enc.count(text) - 1)   # -1 for the space
    while budget > 0:
        carry = overlap_carry(prev, budget, enc)
        merged = f"{carry} {text}".strip()
        excess = enc.count(merged) - max_tokens
        if excess <= 0: return merged, carry
        budget -= excess
    return text, ""
```

**The carry is what gives way, never the chunk.** The budget shrinks until the
result fits, and a trimmed carry still starts on a sentence boundary. The fit is
*measured* rather than predicted, because `enc.tail` is not an exact round trip and
the sentence advance moves the boundary.

The sentence-boundary regex is whitespace after `.!?` followed by an opening capital
or `(`. A lower-case follow ("et. al,") is intentionally not a boundary.

### Honest page attribution for the carry

The carry comes from a different place in the document, possibly a different page.
So `ChildText` records both halves:

```python
@dataclass(frozen=True)
class ChildText:
    blocks: list[Block]                  # the blocks this child's OWN text came from
    text: str                            # carry + own content
    overlap_pages: tuple[int, int] | None  # where the carry came from
    window_index: int                    # which packed window produced it
```

`_tail_pages(blocks, chars)` attributes the carry by walking the previous child's
blocks **backwards**, consuming each block's text plus the join separator until the
carry is accounted for — using only the last block's page would misreport a carry
that reaches back across a page boundary.

`_fit_groups` is the other half of honest attribution. `pack` sizes a window by
summing its atoms' token counts, while the emitted text is the *joined* string, and
re-tokenising that join does not always agree with the sum. So `window_texts`
re-groups the blocks — rather than cutting the joined string — until each group's
text fits `max_tokens`. Each group's text is exactly the join of the blocks recorded
beside it, so a group that lands wholly on page 7 is not labelled with the whole
window's span. A lone block larger than the cap is split on the same boundaries
`_expand_atoms` uses, and the pieces keep that one block, so their attribution is
still exact.

`window_texts` is **the single point at which `child_max_tokens` becomes a hard
limit rather than a target**, and it breaks oversized windows up — never truncates
them.

---

## Stage 3 — building chunks

`_build_chunks(sections, meta, config, enc)`, per section:

1. Compute the **breadcrumb**: `"title › heading"`, capped at
   `breadcrumb_max_tokens`. Headings are lifted out of the block stream into
   `Section.heading` and only ever rejoined onto *parent* text — and parents are
   stored as zero vectors, so **without the breadcrumb a heading reaches no vector
   at all** and contributes nothing to retrieval.
2. If the section fits `parent_max_tokens`, it is one parent window; otherwise
   `pack` + `coalesce_windows` at parent sizing.
3. For each parent window, `pack` + `coalesce_windows` at child sizing, recording
   which parent each child window belongs to.
4. **The overlap chain runs across the whole section, not per parent.** A parent
   boundary *inside* a section exists only because the section outgrew
   `parent_max_tokens` — those splits land mid-sentence — so restarting the chain
   there would drop context across an arbitrary cut. A **section** boundary is
   semantic and does start a fresh chain, so no heading's text bleeds into the next.
5. Emit.

### When a parent is emitted

```python
emit_parent = len(children) > 1
```

A window with exactly one child gets **no parent record**: the child already carries
that window's whole body, so the parent would differ only by the heading — which
reaches the reader anyway through `section_heading`. The context builder falls back
to child text when `parent_chunk_id` is absent, so such a child is not degraded, and
skipping the record avoids a near-duplicate point per single-child section.

A section with a heading and no body emits the heading itself as a single child.
This is the last point at which extracted text can silently vanish.

### Chunk identity

```python
chunk_id = uuid5(_NAMESPACE, f"{document_id}|{kind}|{sha256(owned)}|{ordinal}")
```

Deliberately independent of everything transient, so an unchanged chunk keeps its id
and its stored vector can be reused:

| Excluded | Why |
| --- | --- |
| `doc_version` | A version bump alone must not churn every id. |
| Positional index | Inserting or deleting text elsewhere must not shift the ids of chunks that did not change. |
| Page number | Repagination (a cover page added) is not a content edit. |
| The overlap carry | The carry belongs to the previous chunk, and overlap settings are configuration, not content. Identity uses **owned** text only. |

`ordinal` is a per-document occurrence counter over `(kind, owned)`, so genuinely
repeated text ("Not applicable." twice in one document) cannot collapse two distinct
chunks onto one id.

**Identity is not the re-embed test.** `content_hash` on the chunk still covers the
exact stored `text`, carry included, so a chunk whose carry changed keeps its id but
is correctly re-embedded rather than reusing a stale vector.

### `text` vs `embed_text`

```python
@property
def embed_input(self):  return self.embed_text or self.text
@property
def embed_hash(self):   return sha256(self.embed_input).hexdigest()
```

`embed_text` is `"{breadcrumb}\n\n{text}"` on children, empty on parents. Kept apart
from `text` because `text` is what citations quote and what the chunk's
`content_hash` covers, and neither may drift. `embed_input` is the single definition
of the string the embedder is handed, so the vector, its fingerprint and the payload
can never disagree about what was embedded.

`embed_hash` is distinct from `content_hash` **on purpose**: the embedder sees the
breadcrumb too, so retitling a document — or correcting one heading — changes what
would be embedded while leaving `content_hash` byte-identical. Reuse has to key on
what was embedded.

### Section classification

`classify_section(text)` flags non-substantive sections: `toc`, `references`,
`glossary`, or `None`. Content, not the heading, decides — a chunk filed under a
"References" heading can still be ordinary prose that bled in past a missed heading,
and flagging on the heading alone would hide real content from every search.

| Type | Rule |
| --- | --- |
| `toc` | ≥3 lines with a ≥4-dot leader, and ≥30% of lines |
| `references` | ≥4 citation-ish lines **and** ≥1.5 citations per 100 words |
| `glossary` | ≥5 lines matching `ABBREV – definition`, and ≥40% of lines |

The reference rule uses **density**, not a per-line ratio, because PDF text is
hard-wrapped: one entry spans two or three lines whose continuations carry no
citation marker, which drags any per-line ratio below a usable threshold. Measured
over the sample corpus, body chunks peak at 0.94 citations per 100 words and real
bibliographies start at 2.45, so the gate sits at 1.5, in that gap.

The patterns are careful about false positives: `_CITE_YEAR` matches a standalone
`(2020)` but not an inline `(Hall, Spencer & Kumar, 2020)` — the paren opens on a
name, not a digit — and `_ENTRY_YEAR` requires a full stop or comma on **both**
sides of the year, which prose carrying a year ("rose in 2015, then fell") never
satisfies.

**Nothing is dropped.** A flagged chunk is still stored and still embedded; only
`hybrid_search.build_filter` excludes it from normal retrieval. The knowledge layer
deliberately does *not* filter these out — a bibliography is exactly where author
names live.

Requires ≥4 lines, so short chunks are never classified.

---

## Stage 4 — the payload

`build_payload(chunk)` (`chunking/payload.py`) produces the point payload. Fields
with a value of `None`, `""` or `[]` are stripped, so absence is meaningful.

| Field | Notes |
| --- | --- |
| `chunk_id` | Also the point id. Reconciliation checks they agree — citations resolve by payload. |
| `document_id`, `doc_version`, `is_current` | |
| `pipeline_version` | On the payload *as well as* the catalog row. |
| `is_parent` | Every search filters on it. |
| `source_type`, `language` | |
| `title`, `section_heading`, `section_type` | |
| `chunk_text` | The chunk's `text` — what citations quote and what the keyword leg's `MatchText` searches. |
| `content_hash`, `token_count` | |
| `has_table` | `True` or absent. Read by the prompt builder and the rerank table boost. |
| `tags`, `categories`, `authors` | The document's facets. |
| `source_url`, `file_url` | |
| `published_at` | |
| `document_published_at` | |
| `published_at_precision` | Written **only** when it is `"year"`. A full date needs no marker, so absent means "a full date" — true of every point already in the collection, which is why this needed no `PAYLOAD` bump. |
| `pdf_id`, `pdf_path`, `article_uuid`, `linked_pdf_id`, `linked_article_uuid` | |
| `page_range`, `overlap_page_range` | Lists, when known. |
| children only: `embed_hash`, `parent_chunk_id`, `chunk_index`, `page_number` | Only children carry a real vector, so only they carry the fingerprint of the text it was built from. |
| plus `meta.extra` | `bundle`, `nid`, `changed`, `edition_label`. |

**The table markdown is deliberately not stored.** `join_blocks` already put every
table row into `chunk_text`, so persisting it again duplicated ~10% of the payload
for no reader. It stays on the `Chunk` object for tooling and to derive `has_table`.

`created_at` / `updated_at` are added by the indexer, not here.

---

## Stage 5 — indexing

```python
index_chunks(chunks, batch_size=128, stamp=True) -> int   # points written
```

1. **`ensure_collection()`** — see below.
2. **`_reusable_vectors(children)`** — the vector-reuse pass.
3. **Embed only the pending children**, in batches of `batch_size`, inside span
   `ingest.embed` (tagged with `chunks` and `reused` counts).
4. **`_build_points`** — payload, vector, stamps.
5. **Upsert in batches** inside span `ingest.upsert`.

### Vector reuse

```python
records = client.retrieve(collection, ids=[chunk ids],
                          with_payload=["embed_hash", "embed_model"],
                          with_vectors=True)
reusable = {id: vector for record in records
            if vector is a non-empty list
            and payload["embed_model"] == embedding_version()
            and payload["embed_hash"] == this chunk's embed_hash}
```

Three deliberate choices:

| Choice | Why |
| --- | --- |
| `embed_hash`, not `content_hash` | `content_hash` covers `text` alone; the embedder also sees the breadcrumb, so keying on it reused a vector built from the *old title* whenever a document was renamed. |
| `embed_model` must match | The same input embedded by a different model is a different vector. Without this check, repointing the deployment leaves the collection a silent mix of two models' vectors that **no re-index repairs** — because re-indexing is exactly what reuses them. |
| Best-effort | Any failure reading the store returns `{}` and everything is embedded, which is the behaviour that predates the feature. A point stored before either key existed has nothing to match and is re-embedded — the safe direction. |

Anything that moves the embedded string re-embeds: an edit to the chunk, to its
carry, to the document title, or to the heading above it.

### `embedding_version()`

```python
f"{azure_openai_embedding_model}:{azure_openai_embedding_dimensions or 'native'}"
```

Deliberately readable rather than a digest, so the index says which model produced
each point. Deliberately **excludes** the endpoint, api-version and key: moving
region, bumping the wire protocol or rotating a secret must not re-embed the corpus.

The one thing it cannot see is **a deployment repointed in place to a different
model** — the name and dimension are unchanged, so that still requires clearing the
collection.

### Points

```python
zero = [0.0] * dim
payload = chunk.to_payload()
if stamp:
    payload.setdefault("created_at", now)   # only if absent
    payload["updated_at"] = now
if not chunk.is_parent:
    payload["embed_model"] = model          # written even when stamping is off
vector = zero if chunk.is_parent else vec_by_id[chunk.chunk_id]
PointStruct(id=chunk.chunk_id, vector=vector, payload=payload)
```

`embed_model` is written **even when `stamp=False`**, because it is *identity*
rather than a timestamp and reuse compares it.

`dim` comes from the first available vector, or from `_probe_dim()` (one
`embed_query("dimension probe")` call) when every child was reused and there is
nothing to measure.

### Log line

> Indexed 47 points (39 children: 12 embedded, 27 reused; 8 parents) into 'documents'

The `embedded` vs `reused` split is the number to watch after a version bump or a
title change.

---

## The collection

`ensure_collection()` makes the collection **usable**: it exists, it is the right
shape, and it is indexed. Memoised per process in `_ensured_collections`, recorded
**only after** the collection is confirmed or created, so a transient failure
retries on the next call rather than being cached as done.

### Creation

Vector size is `azure_openai_embedding_dimensions` when set (default **3072**),
falling back to a probe. Distance is **cosine**. Using the configured size means
creation follows configuration rather than whatever the model answered first.

### Dimension validation

`_validate_dimension` raises `VectorDimensionMismatch` when an existing collection's
vector size disagrees with `azure_openai_embedding_dimensions`:

> Collection 'documents' stores 1536-dimensional vectors but this deployment embeds
> to 3072 (azure_openai_embedding_dimensions). Point
> AZURE_OPENAI_EMBEDDING_DIMENSIONS at 1536, or use a different collection —
> writing into this one would mix two vector spaces.

Qdrant rejects the writes anyway, but only per request and with a message about
vector sizes rather than about configuration — and the reads it does not reject
return nothing useful. One clear failure at the boundary beats a deployment that
half-works. When no dimension is pinned (ada-002 accepts no `dimensions`
parameter) there is nothing to validate and the check is skipped.

### Payload indexes

`PAYLOAD_INDEXES` in `vector_store.py` is **the single list**. A fresh deployment
gets all of it from `ensure_collection`, and both index scripts apply exactly this
rather than keeping their own copies — which is how nine of these came to exist only
on machines where someone remembered to run a script.

| Field | Kind | Read by |
| --- | --- | --- |
| `is_parent` | bool | every search excludes parent points |
| `is_current` | bool | every search |
| `source_type` | keyword | website / PDF splits, website preference |
| `language` | keyword | language filter |
| `section_type` | keyword | section-type filters |
| `categories` | keyword | theme filtering |
| `tags` | keyword | tag filtering |
| `authors` | keyword | author-scoped retrieval |
| `document_id` | keyword | `delete_document`, title refresh, scoped retrieval |
| `parent_chunk_id` | keyword | child → parent resolution |
| `chunk_index` | integer | neighbour expansion |
| `published_at` | datetime | date-range filters and recency |
| `chunk_text` | **text** (word tokenizer, lowercased) | the keyword leg's `MatchText` |

`chunk_text` is the heaviest index and the one the lexical path cannot work
without: `keyword_leg_enabled` degrades to dense-only while it is missing,
**silently**.

`ensure_payload_indexes` is best-effort **per field** — one index that cannot be
built must not stop the others, because each one it does build is one filter that
works. And a failure is *confirmed by reading the schema back* rather than believed
from the exception: building a text index over a large collection routinely
outlives the client's request timeout while Qdrant carries on server-side.

Deliberately absent: `term_ids` / `theme_ids` (taxonomy, retired) and `tenant_id` /
`acl` (there is no document-level access control — the corpus is public). Their
payload fields are gone; indexing them would be reviving a removed model.

Standalone application, for a collection that predates a new index:

```bash
python -m scripts.create_payload_indexes [--dry-run]
python -m scripts.create_fulltext_index  [--dry-run]
```

Index creation runs server-side over existing points — nothing is re-ingested or
re-embedded — but it does alter the collection, so **run it while no ingestion is in
progress**. Idempotent.

---

## The safe swap

This is the most important sequence in the pipeline.

```python
new_chunks = chunk_canonical(doc)                      # span ingest.chunk
if _extraction_is_empty(new_chunks):  -> error, keep the previous version
chunks = index_chunks(new_chunks)                      # spans ingest.embed, ingest.upsert
delete_document(document_id, keep_ids=[c.chunk_id for c in new_chunks])
_persist(record, doc, content_hash, version, indexed=True, run_id=run_id)
```

**New points are upserted first, then everything else for that `document_id` is
deleted with the new ids excluded.** Consequences:

- The document never disappears from search mid-update.
- A mid-index failure leaves the previous version fully intact.
- Chunk ids are content-derived and version-independent, so an unchanged chunk is
  simply overwritten in place with a refreshed payload; only chunks that genuinely
  changed or disappeared are affected.

### `delete_document`'s refusal

```python
if keep_ids is not None and not keep_ids:
    raise ValueError("delete_document(keep_ids=[]) would delete every point for ...")
```

`keep_ids=None` means "delete the document outright" — the delete path and the
orphan collector. An **empty list is refused**, because it can only ever arrive from
a swap that indexed nothing, and "replace this document with nothing" is never what
a swap means. It read as "spare no point" and wiped the document while the caller
believed it had just re-indexed it.

The refusal and the `is not None` test in the filter are deliberately redundant: one
makes the mistake loud at the boundary, the other keeps the filter correct even if
some future caller is allowed to pass an empty list.

The empty-extraction guard is the *first* line of defence for the same failure; this
is the second.

### Title refresh without re-embedding

On the `unchanged_content` path, `refresh_document_title(document_id, title)` issues
one `set_payload` filtered on `document_id`. The content hash covers body text only,
so a title-only edit resolves to `unchanged_content` and never re-indexes — which
would leave the payload title (what citations display) stale against the catalog.
Rewriting the one field costs one call and no embedding. Best-effort: a failure
leaves a stale display title, which the document's next real re-index heals anyway.

### Diagram to include: the swap

Two timelines. **Top — the safe order (current):** upsert v2 points → collection
briefly holds v1 ∪ v2 → scoped delete removes v1 → collection holds v2. Mark a
"crash here" arrow at every step and label what a reader sees: v1, then v1+v2
(harmless, both current, reconciliation would flag it as `duplicate_live_versions`),
then v2. **Bottom — the naive order:** delete v1 → **collection holds nothing** →
upsert v2. Mark the same crash arrow in the gap and label it "document invisible
until the next sweep". This is the clearest way to show why the ordering is not
arbitrary.

---

## Validation at this stage

| Check | Where | On failure |
| --- | --- | --- |
| Chunks are non-empty | `pipeline._extraction_is_empty` | `error`, previous version kept |
| No child exceeds `child_max_tokens` | `_build_chunks` tripwire | WARNING; content is kept either way. `window_texts` caps every text it returns, so this branch is a regression tripwire, not a reachable path |
| Collection exists and is the right dimension | `ensure_collection` | `VectorDimensionMismatch` raised — the run fails loudly |
| Payload index exists | `ensure_payload_indexes` | Per-field warning; that filter is unindexed (slower, and `MatchText` will not work at all) |
| `keep_ids` is not an empty list | `delete_document` | `ValueError` |
| Stored vector's model and hash match | `_reusable_vectors` | Re-embedded |
| `document_id` present | `delete_document` | `ValueError` |

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| Qdrant unreachable | `ensure_collection` / `upsert` raises | Document raises → `error` outcome, retry marker, run continues | Next sweep |
| Qdrant unreachable mid-upsert | Partial batches written | Points exist for a version the catalog does not claim; the delete never ran, so the previous version survives too | Next sweep re-indexes; reconciliation reports `duplicate_live_versions` |
| Collection dimension changed | `_validate_dimension` | `VectorDimensionMismatch` | Repoint the setting, or use a new collection |
| Deployment repointed in place | **Not detectable** | Silent mix of two vector spaces | Clear the collection and re-ingest |
| Embedding throttled | 429 hook | Deployment-wide pause; SDK retries (8) | Automatic; exhausted retries → `error` + retry marker |
| Embedding call fails outright | Raised from `_embed_children` | `error` outcome, previous version intact (the upsert never ran) | Next sweep |
| `tiktoken` unavailable | Warning at encoder construction | 4-chars/token heuristic; chunk sizes differ | Restore network/cache before ingesting a corpus |
| `chunk_text` index missing | Nothing at ingest time | The keyword retrieval leg silently does nothing | `scripts.create_fulltext_index` |
| Text index build times out | Exception from `create_payload_index` | Schema is read back; if the server built it anyway, INFO "did not return in time" and it counts as created | — |
| Interrupted swap | Points for two versions | Both are `is_current`, so search may return either | Reconciliation's `duplicate_live_versions`; re-index to collapse |
| Chunk id / payload `chunk_id` disagree | `chunk_id_mismatch` check | Citations resolve to the wrong chunk | Re-index |
| Child names a missing parent | `children_without_parent` check | Context expansion falls back to the child alone | Re-index |

## Observability

- Spans: `ingest.chunk`, `ingest.embed` (with `chunks` and `reused`),
  `ingest.upsert` (with `points`). Aggregated as the `embedding` and `qdrant`
  components in `GET /metrics/timings`.
- `Indexed %d points (%d children: %d embedded, %d reused; %d parents) into %r`.
- `Created collection %r with %d-dimensional vectors.`
- `Created %d payload index(es) on %r: %s`
- `embedding_http` event counters: `ok` / `throttled` / `error`.
- Reconciliation: `indexed_without_points`, `points_without_catalog_row`,
  `duplicate_live_versions`, `version_mismatch`, `chunk_id_mismatch`,
  `children_without_parent`, `point_pipeline_drift`.

### Inspecting chunking by hand

```bash
python -m app.ingestion.chunking path/to/file.pdf -n 5 --full
```

Prints parent and child counts, child token min/max/avg, and the first N children
with their section heading and parent id.

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `qdrant_url`, `qdrant_api_key` | `http://localhost:6333`, none | Store location. |
| `qdrant_collection` | `documents` | Collection name. |
| `azure_openai_embedding_model` | `""` | Deployment name. Part of `embedding_version()`. |
| `azure_openai_embedding_dimensions` | `3072` | Vector size, validated against the collection. Matryoshka truncation to 1536 halves storage and search cost with negligible retrieval loss on `text-embedding-3-*`. Leave blank for ada-002. |
| `azure_openai_embedding_max_retries` | `8` | SDK retries per embedding call. |
| `azure_openai_embedding_max_throttle_seconds` | `60.0` | Ceiling on one throttle pause. |

## Hand-off

The points are written and the previous version is gone. `_persist` now writes the
catalog — [08](08-persistence-and-catalog.md) — and, once that has landed and been
logged, the optional knowledge stage runs — [09](09-knowledge-layer-and-graph.md).

---

Previous: [06 — The Canonical Document and Date Resolution](06-canonical-document-and-dates.md) · Next: [08 — Persistence and the Catalog](08-persistence-and-catalog.md)
