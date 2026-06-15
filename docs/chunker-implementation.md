# Chunker Implementation

This document explains [`app/ingestion/chunker.py`](../app/ingestion/chunker.py) —
the concrete implementation of the chunking strategy described in
[`chunking.md`](./chunking.md). Where `chunking.md` says _what_ and _why_, this
document says _how_: every data structure, every function, the algorithm at each
stage, the design decisions, and how to extend it.

Section references like **(§3.2)** point back to `chunking.md`.

---

## 1. What this module is (and isn't)

The chunker turns **already-extracted text** into a list of `Chunk` objects ready
to embed and upsert into Qdrant. It is the middle stage of the ingestion pipeline:

```
extract  ─►  CHUNK (this module)  ─►  embed  ─►  index/upsert
(PDF text,     parent + child           (Azure        (Qdrant
 Drupal HTML)  chunks + payloads)        OpenAI)       points)
```

It deliberately does **not**:

- read PDFs or call the network (extraction lives in
  [`app/services/extraction.py`](../app/services/extraction.py) and
  [`app/ingestion/extractors/`](../app/ingestion/extractors/));
- compute embeddings (that's [`app/ingestion/embedder.py`](../app/ingestion/embedder.py));
- write to Qdrant (that's the indexer);
- stamp `created_at` / `updated_at` timestamps (the indexer does, at write time).

Keeping the core free of `fitz`/`requests` means importing the chunker is cheap and
the logic is unit-testable with plain strings. The PDF/Drupal adapters
(§10) use **lazy imports** so the heavy dependencies are only pulled in when you
actually call them.

---

## 2. The pipeline at a glance

A document flows through six stages. The public entry points are `chunk_pages()`
and `chunk_document()`; everything else is internal.

```
              ┌─────────────────────────────────────────────────────────┐
              │ chunk_pages(pages, meta, config)                         │
              └─────────────────────────────────────────────────────────┘
                                    │
  (1) _blocks_from_text   per page: text ─► [_Block, _Block, …]
        • detect headings / fenced code / tables / paragraphs
        • each block tagged with its page number
                                    │
  (2) _assemble_sections  [_Block…] ─► [_Section, _Section, …]
        • a heading opens a new section; content before the first
          heading is an untitled intro section
        • consecutive headings with no body in between are merged
                                    │
  (3) _merge_small_sections  fold sub-threshold sections into a neighbour
        • avoids tiny parents / a stray heading becoming its own section
                                    │
  (4) _build_chunks  per section ─► 1+ parent chunks, each with N child chunks
        • _pack       greedily group atoms into token-bounded windows
        • _coalesce_windows  merge away any too-small window
        • _apply_overlap     prepend the previous window's tail (children only)
                                    │
  (5) Chunk objects   (parents: is_parent=True; children: parent_chunk_id set)
                                    │
  (6) .to_payload()   ─►  the Qdrant payload dict (§3.7)
```

Token lengths are measured everywhere with the **embedding model's tokenizer**
(tiktoken `cl100k_base`, what `text-embedding-3-large` uses), never character
counts (§3.4).

---

## 3. Data model

### 3.1 `ChunkingConfig` (public, frozen)

The token budgets for one document type. It's a frozen dataclass so a preset can
be shared safely and never mutated.

| Field | Default | Meaning |
| --- | --- | --- |
| `child_target_tokens` | 400 | The size we aim each child at. |
| `child_max_tokens` | 512 | Soft ceiling for a child window. |
| `child_min_tokens` | 120 | Below this a window is "too small" and gets merged. |
| `child_overlap_tokens` | 60 | Tokens of the previous child prepended to the next (~15%, §3.5). |
| `parent_target_tokens` | 1800 | Size we aim each parent at when a section must be split. |
| `parent_max_tokens` | 2400 | A section larger than this is split into multiple parents. |
| `encoding_name` | `"cl100k_base"` | tiktoken encoding used for all token counts. |

> **"max" is a soft ceiling, not a hard cap.** A window may exceed the target by
> at most one atom plus the overlap carry. The point of `*_max_tokens` is to
> prevent the pathological "3000-token chunk" the design doc warns about — not to
> stay under the embedding model's input limit (8191 tokens for
> text-embedding-3-large, far above anything we emit).

### 3.2 `DocumentMeta` (public)

Document-level fields that propagate onto **every** chunk's payload (§3.6). One
instance per document. Source-specific fields are simply left `None` for the type
that doesn't use them and dropped from the payload later.

- **Identity:** `document_id`, `source_type` (`"pdf"` / `"article"` / …),
  `doc_version`, `is_current`.
- **Citation:** `title`, `source_url` (web), `pdf_path` / `pdf_id` /
  `page_number` (PDF), `article_uuid`, `linked_article_uuid`.
- **Classification:** `tags`, `categories`, `authors`, `language`.
- **Access control / multi-tenancy:** `tenant_id`, `acl`.
- **Timeline:** `published_at`.
- **`extra`:** a free-form dict merged into the payload verbatim — used by the
  Drupal adapter to carry `bundle`, `nid`, `changed`.

### 3.3 `Chunk` (public)

One emitted chunk. The same class represents both children and parents; the
`is_parent` flag and which fields are populated distinguish them.

| Field | Child | Parent |
| --- | --- | --- |
| `chunk_id` | deterministic UUID | deterministic UUID |
| `text` | body only (no heading) | heading + body |
| `is_parent` | `False` | `True` |
| `section_heading` | set | set |
| `parent_chunk_id` | the parent's id | `None` |
| `chunk_index` | global ordinal `0..N` | `None` |
| `page_number` | first page of the window | `None` |
| `page_range` | `(min, max)` pages | `(min, max)` pages |
| `token_count` | tiktoken count of `text` | tiktoken count of `text` |
| `content_hash` | sha256 of `text` | sha256 of `text` |
| `meta` | the shared `DocumentMeta` | the shared `DocumentMeta` |

`Chunk.to_payload()` flattens `meta` + the per-chunk fields into the §3.7 payload
(see §9).

### 3.4 `_Block` and `_Section` (internal)

- **`_Block`** — the smallest unit of parsed text. `kind` is one of `"heading"`,
  `"text"`, `"code"`, `"table"`; `level` is the heading depth (0 for non-headings);
  `page` is the page it came from (or `None` for unpaginated input).
- **`_Section`** — a `heading` (or `None` for the intro) plus the ordered list of
  `_Block`s underneath it. This is the unit that becomes a parent.

---

## 4. Token measurement — `_Encoder`

A thin wrapper over a tiktoken encoding with a **graceful fallback**. tiktoken's
`cl100k_base` BPE table is fetched from the network the first time and then cached
on disk; if that fetch fails (offline, locked-down host) the encoder logs a warning
and falls back to a `len(text) / 4` heuristic so ingestion still runs — just with
less precise sizing.

Methods:

- `count(text)` → number of tokens. The single source of truth for "how big is
  this?" used throughout packing.
- `split_to_token_limit(text, max_tokens)` → hard-cuts text into ≤ `max_tokens`
  pieces by slicing the **token id list** and decoding. The last resort when no
  natural separator survives (e.g. one enormous unbroken run).
- `tail(text, n)` → the last `n` tokens of `text`, decoded back to a string. This
  is how child overlap is produced (§8.3).

`_get_encoder(name)` is `@lru_cache`-d, so the (relatively expensive) encoding load
happens once per process per encoding name.

---

## 5. Stage 1 — block parsing (`_blocks_from_text`)

Turns one page's raw text into a list of `_Block`s. This is the **structure-aware**
part (§3.1): we read the document's own markup instead of blindly slicing.

The function is a single-pass line state machine. For each line, in priority order:

1. **Fenced code block** (` ``` ` or `~~~`): consume every line up to and including
   the matching closing fence into one `kind="code"` block. **Kept atomic** — never
   split mid-block (§3.4).
2. **Blank line:** flush the current paragraph buffer as a `kind="text"` block.
3. **Table region:** a run of ≥2 consecutive lines that each contain ≥2 `|`
   characters becomes one `kind="table"` block. **Kept atomic.**
4. **Heading:** a line that `_line_heading_level` classifies as a heading flushes
   the paragraph buffer, then emits a `kind="heading"` block.
5. **Otherwise:** append the line to the paragraph buffer.

Each block records the `page` it was parsed from, which is how page numbers
eventually reach the chunk payload.

### 5.1 Heading detection (`_line_heading_level`)

Returns a heading depth (1–6) or `None`. The rules, in order, are tuned to catch
real headings in PDFs and stripped HTML without turning prose into headings:

| Signal | Example | Depth | Accepted… |
| --- | --- | --- | --- |
| Markdown ATX | `## 4.2 Retention` | count of `#` | anywhere |
| Numbered | `4.2 Data Retention Requirements` | dot-depth + 1 | anywhere¹ |
| Labelled | `Section 4.2`, `Appendix B` | 2 | anywhere¹ |
| ALL CAPS, short | `DATA RETENTION` | 2 | only at block start² |
| Title Case, short | `Data Retention` | 3 | only at block start² |

¹ Rejected if the line ends in terminal punctuation (`. ! ? , ; :`) — that signals
prose, e.g. "1. We will discuss the following." is not a heading.
² "Block start" means the paragraph buffer is empty (the line is standalone). Soft
signals are only trusted there so we don't carve a heading out of the middle of a
sentence. Lines longer than `_MAX_HEADING_WORDS` (12) are never headings.

`_clean_heading` then strips the `#` markers from ATX headings but **keeps the
numbering** ("4.2 …") intact, because people cite "Section 4.2".

> **Heuristic by nature.** A missed heading just yields a larger section (which
> still gets sub-split correctly). A false-positive heading yields a small section
> (which the small-section merge in §6 absorbs). Both failure modes are cheap.

---

## 6. Stage 2 & 3 — sections (`_assemble_sections`, `_merge_small_sections`)

**Assembly** walks the flat block list and groups it into `_Section`s:

- A `heading` block **opens a new section** — unless the current section has no
  body yet, in which case the headings are **merged** (`"Title — Subtitle"`). This
  handles multi-line titles and a title immediately followed by a subheading.
- Non-heading blocks accumulate into the current section.
- Content before the very first heading becomes an **untitled intro section**
  (`heading=None`).

**Small-section merge** then folds any section whose total text is below
`child_min_tokens` into a neighbour, so we never build a 30-token parent out of a
stray heading:

- A small section merges **backward** into the previous one (its heading is
  demoted to a text block so the words aren't lost).
- A special case handles a small **leading** section by folding it **forward** into
  the next section instead (there's no previous one to merge into).

---

## 7. Stage 4 — building parents and children (`_build_chunks`)

For each section, in document order:

### 7.1 Parents (§3.2)

- If the section (heading + body) fits within `parent_max_tokens` → **one parent**,
  the whole section. This is the common case and the design's ideal: "parent = full
  section".
- If the section is larger → split into **multiple same-section parents** via
  `_pack` (no overlap — parents are read whole and de-duplicated by id, so they
  don't need it), then `_coalesce_windows` to avoid a tiny trailing parent.

Parent text is built by `_parent_text`: the heading is prepended to the body (and
`" (cont.)"` is appended to the heading on the 2nd+ part of a split section). This
matches the design doc, where a parent's `chunk_text` begins with its heading.

### 7.2 Children (§3.2)

For **each parent**, its blocks are turned into children:

1. `_pack` groups the parent's atoms into ~`child_target_tokens` windows.
2. `_coalesce_windows` merges away any window below `child_min_tokens`.
3. `_apply_overlap` prepends each window's predecessor tail (the overlap, §3.5).

Children are built **per parent**, so a child's atoms always come from exactly one
parent. That's what makes "search the child → look up `parent_chunk_id` → read the
parent" exact — a child never straddles two parents.

`chunk_index` is a **global** counter across the whole document (so child 87 is the
88th child overall, matching the design doc's example), while parent ids are keyed
per `section.part`.

---

## 8. The sizing algorithms

These three functions are where the earlier naive approach had bugs; the current
design is deliberate. All operate on `_Block` "atoms" and use the `_Encoder` for
sizing.

### 8.1 `_expand_atoms` — make atoms small enough to pack

Before packing, any block that's too big to fit a window is split via
`_split_text_recursive`. The cap depends on the block kind:

- **Plain text** is split down to the **soft cap** (the window _target_). This gives
  packing fine-grained, well-sized units and leaves room for overlap.
- **Code and tables** are only split if they exceed the **hard cap** (the window
  _max_), preserving atomicity (§3.4) up to the largest size we'll tolerate.

`_split_text_recursive` tries separators from coarse to fine —
`"\n\n"` → `"\n"` → `". "` → `" "` — regrouping pieces greedily so each stays within
budget, and only falls back to a hard token cut (`split_to_token_limit`) if even
single "words" are too long.

### 8.2 `_pack` — greedy windowing with a min-fill rule

The core packer. It accumulates atoms into the current window and decides when to
flush:

```
flush the current window before adding the next atom when EITHER:
  • adding it would exceed `target` AND the window already has ≥ `min_fill` tokens
  • adding it would exceed `max_tokens`   (hard-ish stop)
```

The **min-fill rule** (`min_fill = child_min_tokens`) is the important subtlety: it
prevents a small leading atom — say a heading plus a one-line intro — from being
flushed on its own as a tiny chunk. Such atoms stay attached to the body that
follows. (An earlier version without this rule emitted 6-token "orphan head"
chunks.) The early-flush-on-max branch stops a near-max atomic block (a big table)
from blowing the window wide open.

### 8.3 `_coalesce_windows` — kill the tiny ones

After packing, any window still below `min_tokens` is merged into a neighbour:

- Candidate neighbours (left and right) are ranked: **prefer a merge that stays
  ≤ `max_tokens`**, then prefer the **smaller** resulting window.
- If a too-small window has _no_ neighbour it can merge into without exceeding max,
  it's merged anyway — "a slightly-over-target chunk beats a tiny one" (§3.1's "never
  emit a 30-token chunk" wins over the soft max).
- The scan restarts after each merge because indices shift. `n` per parent is small,
  so the O(n²) is irrelevant.

### 8.4 `_apply_overlap` — text-level overlap (children only)

Rather than carry _atoms_ between windows (which fails when a window is a single
large atom), overlap is applied at the **text** level: each child gets the last
`child_overlap_tokens` tokens of the previous child prepended (via `_Encoder.tail`).
This is reliable regardless of how the window was packed, and is computed _after_
coalescing so sizes are final. Overlap is **not** applied to parents.

---

## 9. IDs, hashing, determinism, and the payload

### 9.1 Deterministic UUIDs (`_uuid`)

Chunk ids are `uuid5(_NAMESPACE, "{document_id}|v{doc_version}|{suffix}")` where
suffix is `parent|{section}.{part}` or `child|{index}`.

- **Why UUIDs, not the doc's readable strings?** Qdrant point ids must be unsigned
  ints or UUIDs. The design doc's `parent_pdf_..._s12` is illustrative; in practice
  a string id is rejected, so we hash that readable key into a `uuid5`.
- **Why deterministic?** Re-ingesting identical content produces identical ids, so
  the upsert is **idempotent** — no duplicate points. The `_NAMESPACE` constant must
  never change, or every previously ingested chunk would be re-keyed.
- A child's `parent_chunk_id` is its parent's UUID — the exact "search small, read
  big" link (§3.2).

### 9.2 `content_hash`

`sha256` of the chunk text. Used downstream for change detection / dedup.

### 9.3 `to_payload()` — the Qdrant payload (§3.7)

Builds the payload dict from `meta` + per-chunk fields. Notes:

- **Children** additionally carry `parent_chunk_id`, `chunk_index`, `page_number`.
- `page_range` is emitted as a list when present.
- `meta.extra` is merged in verbatim.
- Empty values are dropped, but the test is `v not in (None, "", [])` — so `False`
  and `0` are **kept** (e.g. `is_parent: false`, `is_current: true`).
- `created_at` / `updated_at` are intentionally **absent** — the indexer stamps
  those at write time. `published_at` comes from the source and is passed through.

---

## 10. Configuration & presets

`config_for(key)` maps a `source_type` _or_ a Drupal bundle name (case-insensitive)
to a preset, falling back to the general defaults (`_BASE`). The presets implement
the §3.4 per-document-type table:

| Preset key(s) | child target / max / overlap | parent target / max | Rationale |
| --- | --- | --- | --- |
| `pdf`, `manual` | 450 / 560 / 60 | 2000 / 2600 | Large technical PDFs; parent = full section. |
| `research_paper(s)` | 480 / 560 / 48 | 2000 / 2600 | Section-bounded; 10% overlap. |
| `policy`, `policy_brief` | 400 / 512 / 60 | 1800 / 2400 | Clause-bounded; 15% overlap; don't merge clauses. |
| `report` | 420 / 540 / 60 | 1900 / 2500 | In between. |
| `article` + Drupal bundles | 380 / 480 / 40 | 1600 / 2200 | Short web pages; 10% overlap. |
| `small_pdf` | 400 / 512 / 50 | 100000 / 100000 | 1–10 pg; the huge parent budget forces **parent = whole doc**. |

Drupal bundle names (`news`, `events`, `feature_articles`, …) are registered as
aliases of `article` so the adapter can look up by bundle directly.

---

## 11. Public API & source adapters

### 11.1 Generic core

```python
chunk_pages(pages, meta, *, config=None) -> list[Chunk]
chunk_document(text, meta, *, config=None) -> list[Chunk]
```

- `chunk_pages` takes `[(page_number, text), …]` in reading order; page numbers flow
  onto each chunk. This is the entry point for paginated sources (PDFs).
- `chunk_document` is the unpaginated convenience wrapper — it just calls
  `chunk_pages([(None, text)], …)`.
- If `config` is omitted, it's resolved from `meta.source_type` via `config_for`.

### 11.2 `chunk_pdf(result, …)`

Adapter for `app.services.extraction.ExtractionResult`. It duck-types the result
(reads `.source`, `.pages[].page_number`, `.pages[].text`, `.page_count`) and imports
nothing from the extraction module at call time, so it works even where `fitz`
isn't installed. Documents of `small_doc_pages` (default 10) pages or fewer get the
`small_pdf` preset (parent = whole doc, §3.4). Extra `DocumentMeta` fields can be
passed as keyword args.

### 11.3 `chunk_drupal_record(record, …)`

Adapter for `app.ingestion.extractors.drupal_extractor.DrupalRecord`. It sets
`source_type="article"` (the citation type per §3.7) while sizing with the
record's **bundle** preset (so a `research_papers` node is sized like a paper but
cited as an article). `source_url` is the citation; `tags` / `categories` /
`authors` are lifted from the record metadata; `bundle` / `nid` / `changed` ride
along in `extra`.

### 11.4 CLI

```bash
python -m app.ingestion.chunker path/to/file.md        # or .txt, or .pdf
python -m app.ingestion.chunker file.pdf -n 5 --full   # show 5 children, full text
```

Prints parent/child counts, child token min/max/avg, and a preview of the first
few children. The `.pdf` path imports `extract_pdf` lazily (and therefore needs
PyMuPDF installed). Handy for eyeballing how a real document chunks.

---

## 12. A worked example

Input (a small structured doc):

```
# Corporate Policy Guide 2024

## 4.1 Scope
This policy applies to all employees… (≈400 tokens)

## 4.2 Data Retention Requirements
All customer records must be retained… (≈600 tokens)

| Field | Retention |
| ----- | --------- |
| email | 7 years   |
```

What happens:

1. **Blocks:** headings `# Corporate…`, `## 4.1 Scope`, `## 4.2 …`; text paragraphs;
   one atomic `table` block.
2. **Sections:** `# Corporate…` has no body before `## 4.1`, so they merge into a
   section headed **"Corporate Policy Guide 2024 — 4.1 Scope"**. `## 4.2 …` opens a
   second section (its body + the table).
3. **Small-section merge:** both sections are above `child_min_tokens`; nothing
   merges.
4. **Parents:** each section is under `parent_max_tokens` → **2 parents**.
5. **Children:** section 4.1 → 1 child (~400 tok); section 4.2 (~650 tok with the
   table) → 2 children, with the table kept whole in one of them. Overlap tokens are
   prepended to the 2nd child.
6. **Result:** 2 parents + 3 children. Every child's `parent_chunk_id` points at its
   section's parent; `section_heading` is set; ids are stable across re-runs.

---

## 13. Design decisions & deviations from `chunking.md`

- **UUID ids instead of readable strings** — Qdrant requirement; see §9.1.
- **Soft, not hard, max sizes** — see the callout in §3.1. We favour keeping a table
  or a clean idea whole over hitting an exact token count.
- **Overlap is text-level, not atom-level** — more robust; see §8.4.
- **Timestamps deferred to the indexer** — keeps the chunker free of wall-clock
  state and keeps ids/hashes deterministic.
- **`source_type` vs sizing preset are decoupled** — a Drupal research paper is
  _cited_ as an `article` but _sized_ with the research-paper budgets.
- **Hierarchical chunking (§3.3) is not implemented** — the design doc explicitly
  calls it an optimisation to add after parent-child works. The section model is a
  natural place to grow into it later (a document-summary level above sections).

---

## 14. Invariants & guarantees

Verified behaviour the rest of the pipeline can rely on:

- Every child's `parent_chunk_id` references a parent emitted in the same run.
- A child never spans two parents.
- `chunk_index` on children is contiguous `0..N-1` in document order.
- No empty chunks are emitted.
- No child is below `child_min_tokens` **except** an unavoidable final remainder
  in a single-fragment document.
- No child wildly exceeds max — bounded by roughly `max + min + overlap`, never the
  3000-token failure case.
- Identical input + identical `DocumentMeta` ⇒ identical ids, text, hashes, and
  token counts (fully deterministic).
- Empty / whitespace-only input ⇒ `[]` (no crash).

---

## 15. Extending the chunker

- **New document type / tuning:** add an entry to `_PRESETS` keyed by source type
  (and any bundle aliases), or pass a `ChunkingConfig` explicitly to a `chunk_*`
  call.
- **New source:** write a thin adapter (like `chunk_pdf` / `chunk_drupal_record`)
  that builds a `DocumentMeta` and calls `chunk_pages` / `chunk_document`. Keep any
  heavy imports lazy.
- **Better heading detection:** extend `_line_heading_level` — it's the single
  choke point for "what counts as a heading", and everything downstream adapts.
- **A different tokenizer:** set `ChunkingConfig.encoding_name`; `_Encoder` /
  `_get_encoder` handle the rest.
