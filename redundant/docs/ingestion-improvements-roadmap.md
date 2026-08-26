# Ingestion pipeline — improvement roadmap

> **Note (2026-08-09):** the `POST /ingest/pdf` upload route was removed when
> Drupal became the only ingestion source. Items below that weigh added latency
> against that endpoint's contract no longer apply — the sweep is the only path.

An analysis of proposed changes to the ingestion pipeline
([app/ingestion/](../app/ingestion/)), including where an LLM would add real
value and where it would not. Each item states what changes, why, how hard it
is, what can go wrong, and what it depends on.

Nothing here has been implemented. This document exists to make the
impact / effort / risk trade-off explicit **before** any code changes.

> **Cost figures** assume a `gpt-4o-mini`-class deployment (the model
> [summarize.py](../app/pipeline/summarize.py) already targets) at roughly
> $0.15 / 1M input and $0.60 / 1M output tokens, and Azure Document
> Intelligence at roughly $1.50 / 1k pages (`prebuilt-read`) and $10 / 1k pages
> (`prebuilt-layout`). Verify against your actual Azure pricing tier before
> budgeting.

---

## Summary

| # | Change | Complexity | Risk | Cost / 1k docs |
| --- | --- | --- | --- | --- |
| 1 | Embed the section breadcrumb into child chunk text | Easy | Low | $0 |
| 2 | Retire the dead `chunk_size` / `chunk_overlap` settings | Easy | Low | $0 |
| 3 | Make enrichment safe: content-hash stability | Medium | Low | $0 |
| 4 | Enrichment cache + backfill path | Medium | Low | $0 |
| 5 | Recover structure on scanned documents | Medium | Low | ~$8.50 extra OCR |
| 6 | LLM front-matter extraction for local PDFs | Medium | Medium | ~$0.50–1.00 |
| 7 | Per-document abstract generated at ingest | Medium | Low | ~$2.50 |
| 8 | LLM theme classification with provenance | Medium | Medium | ~$0.20 |
| 9 | Semantic near-duplicate detection + LLM adjudication | Hard | Medium | ~$1 |
| 10 | LLM contextual chunk headers | Medium | Medium | ~$60–120 |
| 11 | LLM OCR repair pass | Medium | **High** | ~$15 |
| 12 | Keep the heading heuristics as they are | — | — | — |
| 13 | Keep Drupal facet routing deterministic (one-time offline mapping) | Medium | Low | ~$0 |
| 14 | Do **not** adopt LLM semantic chunk boundaries | — | — | — |

---

## 1. Embed the section breadcrumb into child chunk text

**Complexity: Easy · Risk: Low · Cost: $0**

### What changes

In [`chunking/__init__.py`](../app/ingestion/chunking/__init__.py), the text
sent to the embedder for each child chunk becomes
`{title} › {section_heading}\n\n{chunk_text}` instead of bare `chunk_text`.
The **stored** `chunk_text` payload field stays exactly as it is, so citations,
`content_hash`, and the generator's context blocks are unaffected.

### Rationale

Section headings currently contribute **nothing** to retrieval:

- `assemble_sections` (`segmenter.py:190`) lifts headings out of the block
  stream into `Section.heading`, so they leave the block list.
- `_parent_text` (`chunking/__init__.py:62`) prefixes the heading back onto
  *parent* text — but parents are stored as **zero vectors**
  (`indexer.py:46`) and are never embedded.
- Child text comes from `join_blocks(window)` (`chunking/__init__.py:108`),
  which contains no heading.

So the entire heading-detection apparatus in `segmenter.py` only ever reaches
the payload as a display field. A child from page 30 of a report is embedded
with no indication of which report or which section it belongs to.

This is the cheapest available approximation of "contextual retrieval"
(item 10), and it should be measured before paying an LLM for the same effect.

### Failure modes

- Breadcrumb tokens consume part of the child's token budget. With
  `child_max_tokens` at 512–560 the overhead is ~10–20 tokens; measurable but
  small. Count the prefix against the budget rather than letting chunks
  silently exceed it.
- A long or garbled OCR heading could dominate a short chunk's embedding.
  Truncate the breadcrumb to a fixed token cap.
- Requires a **full re-embed** of the corpus to take effect. Existing points
  keep their old vectors until re-ingested.

### Dependencies

None. Ships independently.

---

## 2. Retire the dead `chunk_size` / `chunk_overlap` settings

**Complexity: Easy · Risk: Low · Cost: $0**

### What changes

Remove `chunk_size: int = 1000` and `chunk_overlap: int = 200` from
[`config.py:77-78`](../app/config.py). Nothing in the codebase reads them —
real sizing lives in
[`chunking/config.py`](../app/ingestion/chunking/config.py).

### Rationale

Two plausible-looking knobs that do nothing are an active trap: someone will
eventually tune them and conclude the chunker is broken when nothing changes.

### Failure modes

An operator's `.env` may already set them. `Settings` is configured with
`extra="ignore"`, so stale entries are harmless — but note the removal in the
changelog so nobody assumes a behaviour change.

### Dependencies

None.

---

## 3. Make enrichment safe: content-hash stability

**Complexity: Medium · Risk: Low · Cost: $0**

> **This is a hard prerequisite for items 6, 7, and 8. Doing them without it
> will cause a corpus-wide re-index loop.**

### What changes

`ensure_content_hash()` ([`document.py:95`](../app/core/models/document.py))
hashes `title + full_text`, and `from_pdf` calls it at
[`canonical.py:93`](../app/ingestion/canonical.py). Either:

- **(a)** compute the hash over extracted body text only, excluding any
  LLM-derived field; or
- **(b)** keep the hash over source-derived values, and apply enrichment
  strictly *after* `ensure_content_hash()` has run.

Option (a) is cleaner. Option (b) is a smaller diff but leaves a live footgun
for whoever next touches ordering in `from_pdf`.

### Rationale

If an LLM sets the title, the content hash becomes non-deterministic across
runs. `content_changed()` (`change_detection/base.py:53`) then returns true on
every sweep, so every document bumps `doc_version`, re-chunks, re-embeds, and
re-upserts — permanently, at full embedding cost, on every scheduled run.

This is the single easiest way to turn a $1/1k-docs feature into an unbounded
recurring bill, and it fails silently: the pipeline keeps working, it just
never converges.

### Failure modes

- Changing what feeds the hash invalidates every stored `content_hash`. This is
  **not** a corpus-wide re-version, though: `compute_status` decides
  NEW/CHANGED/UNCHANGED on the *fingerprint* alone, and `_handle` returns early
  on UNCHANGED, so an unchanged document never recomputes its content hash. The
  real cost is bounded and self-healing — a document whose fingerprint moves but
  whose body is identical re-indexes **once** instead of taking the
  `unchanged_content` fast path, and is correct from then on.
- Excluding the title from the hash means a title-only correction no longer
  triggers a re-index, which would leave the *payload* title (what citations
  display) stale against the catalog. Handled by refreshing that one field with
  a Qdrant `set_payload` on the `unchanged_content` path — no re-embed.

### Dependencies

None, but must land before 6 / 7 / 8.

---

## 4. Enrichment cache + backfill path

**Complexity: Medium · Risk: Low · Cost: $0**

> **Prerequisite for items 6, 7, 8, and 10.**

### What changes

Persist LLM-derived fields (title, authors, date, abstract, inferred themes)
in the catalog keyed by the document's `content_hash` or `fingerprint`, and
read from that cache before calling the model. Add a one-shot backfill entry
point in the shape of [`backfill.py`](../app/ingestion/backfill.py).

### Rationale

Without this, any re-ingest re-pays for enrichment. That includes routine
operational events that have nothing to do with document content: a chunking
preset change, an embedding-model swap, a Qdrant rebuild, the one-time
re-version from item 3. A corpus-wide re-chunk should cost embedding tokens
only, never LLM enrichment tokens.

It also makes enrichment **restartable**: a sweep interrupted halfway resumes
without redoing completed work, which matters because enrichment is the
slowest step in the per-document path.

### Failure modes

- Cache invalidation: if the enrichment *prompt* changes, cached values are
  stale but still valid-looking. Store a prompt/schema version alongside the
  cached value and treat a version mismatch as a miss.
- Storage growth: abstracts are ~1–2 KB per document. Negligible against the
  vector store, but it is a new column on the `documents` table with the usual
  idempotent-migration requirement (see
  [`catalog/schema.py`](../app/catalog/schema.py)).

### Dependencies

Item 3 (a stable hash is what makes the cache key meaningful).

---

## 5. Recover structure on scanned documents

**Complexity: Medium · Risk: Low · Cost: ~$8.50 / 1k pages routed to layout**

### What changes

`azure_document_intelligence_model` defaults to `prebuilt-read`
([`config.py:30`](../app/config.py)), which is OCR-only and returns **no
layout**. Options, in preference order:

1. Route scanned pages of *structurally important* documents (reports, policy
   briefs) to `prebuilt-layout`, keeping `prebuilt-read` for the rest. The
   per-page router in `_hybrid_extract` (`pdf_extractor.py:346`) already has
   the shape for this — it needs a per-document policy input, not new
   plumbing.
2. For born-digital pages, derive headings from PyMuPDF font-size clustering
   in [`pymupdf_local.py`](../app/ingestion/extractors/pymupdf_local.py).
   Free, and `classify_document` already opens every page.

### Rationale

With no layout markup, `assemble_sections` collapses a scanned document into a
**single heading-less section**. Parent/child chunking then degrades to
fixed-size sliding windows — for exactly the documents (scanned reports) that
most need structure. Item 1's breadcrumb also has nothing to prepend for these
documents, so the two changes compound.

Note the code already handles layout Markdown when it is requested
(`pdf_extractor.py:262` gates `output_content_format` on the model name), so
the extraction side is mostly ready.

### Failure modes

- `prebuilt-layout` is roughly 6× the cost of `prebuilt-read`. Routing policy
  must be conservative or OCR spend jumps.
- Layout Markdown carries more boilerplate (`<figure>`, HTML comments, page
  bars) — which is exactly what
  [`text_normalize.py`](../app/ingestion/extractors/text_normalize.py) was
  written for, so this is covered, but the normalizer's behaviour on a much
  larger share of the corpus should be re-checked against
  `test_text_normalize.py`.
- Font-size clustering is unreliable on heavily designed PDFs — the same
  reason `pdf_detect_ruled_grid` and `pdf_detect_borderless_tables` default to
  off. Ship it behind a setting with the same default-off posture.

### Dependencies

Pairs naturally with item 1 (breadcrumbs need headings to exist).

---

## 6. LLM front-matter extraction for local PDFs

**Complexity: Medium · Risk: Medium · Cost: ~$0.50–1.00 / 1k PDFs**

### What changes

One structured-output call over the first 1–2 extracted pages returning
`{title, authors[], published_at, doc_type, publisher}`, applied in
`from_pdf` ([`canonical.py:66`](../app/ingestion/canonical.py)). `doc_type` is
constrained to the existing `DEFAULT_BUNDLES` vocabulary. Values already
supplied by the source are never overwritten — Drupal attachments inherit node
facets at `attachment.py:79` and must keep them.

### Rationale

Today `from_pdf` sets `title` to the filename and nothing else. No authors, no
`published_at`, no themes, no document type. Every consumer of document-level
metadata is degraded as a result:

- `_recency_scores` ([`reranker.py:28`](../app/retrieval/reranker.py)) returns
  a flat `_UNKNOWN` (0.5) for every PDF, so the recency tie-break inside a
  relevance band cannot separate them — it is inert across most
  of the corpus.
- `documents_theme` gets no rows, so PDFs are invisible to theme-scoped
  retrieval and to per-theme counts.
- `_scope_filters` ([`summarize.py:101`](../app/pipeline/summarize.py)) cannot
  select them.
- The structured `count` / `list` path answers questions about a corpus that
  silently excludes loose PDFs — a correctness problem, not just a recall one.

Cost is negligible next to OCR, which the same documents already incur.

### Failure modes

- **Fabricated metadata.** The main risk. Mitigate by requiring each extracted
  scalar to appear verbatim (or near-verbatim) in the supplied page text, and
  dropping it otherwise. A missing author is much cheaper than a wrong one,
  because these values feed the *catalog*, which users read as fact.
- **Date ambiguity.** "March 2024" on a cover page may be the publication
  date, the data vintage, or the event covered. Prefer `None` over a guess;
  consider capturing a confidence and only writing high-confidence dates.
- **Hash instability** — see item 3. Blocking.
- **Latency on the upload route.** `ingest_upload`
  ([`upload.py`](../app/ingestion/upload.py)) indexes inline for
  `POST /ingest/pdf`. Adding 1–2s changes that endpoint's latency contract.
  Either defer enrichment on that path or accept it explicitly.
- **Throughput.** `ingest_workers` defaults to `1` (`config.py:265`).
  Enrichment makes ingestion TPM-bound on the Azure deployment; raise workers
  and confirm `ingest_batch_pause_seconds` interacts sanely with rate limits.
- Must fail open, matching every other external dependency in this pipeline
  (`_ocr_pdf` warns and skips, `classify_document` biases to Azure). An LLM
  timeout leaves fields `None` and the document still indexes.

### Dependencies

Items 3 and 4, both blocking.

---

## 7. Per-document abstract generated at ingest

**Complexity: Medium · Risk: Low · Cost: ~$2.50 / 1k docs**

### What changes

Generate a ~200-word abstract per document at ingest (hierarchically over the
parent chunks, so the whole document is seen), store it on the catalog row,
and have `summarize_scope` read it instead of running its map stage.

### Rationale

This is the clearest case of moving work from the query hot path to ingest.

`summarize_scope` ([`summarize.py:225`](../app/pipeline/summarize.py))
currently uses each document's **lead parent chunk** as a stand-in for the
whole document (`summarize.py:241`), then runs map-reduce over up to
`_SCOPE_DOC_CAP = 30` documents with `_MAP_WORKERS = 4` — 4–8 LLM calls on a
live request.

With stored abstracts the map stage disappears entirely: the reduce reads 30
abstracts (~7k tokens) in a single call.

- **Latency:** scoped-summary responses drop from roughly 8–15s to 2–3s.
- **Quality:** the abstract is built from the whole document, not just its
  first ~1800 tokens. A lead parent chunk on a report is frequently a cover
  page or table of contents.
- **Cost:** paid once per `doc_version` instead of on every query that touches
  the document. For any document summarized more than once, this is net
  cheaper.

It also unlocks item 8 cheaply, since the abstract is the natural classifier
input.

### Failure modes

- **Staleness** is bounded by `doc_version`, which is already the pipeline's
  contract. Low concern.
- Abstract quality on non-prose documents (datasets, image-heavy
  infographics, `people` bundle records) will be poor. Gate generation on a
  minimum extracted-text length and skip rather than emit filler.
- `summarize_scope` must keep working for documents with no abstract yet —
  keep the existing lead-parent path as the fallback until backfill completes.
- The reduce prompt is currently written against per-document *bullets*
  (`_REDUCE_SYSTEM`, `summarize.py:64`). Feeding it abstracts instead needs a
  prompt revision, covered by `test_scoped_summary.py`.

### Dependencies

Items 3 and 4. Should ship together with item 6 (same call site, same cache).

---

## 8. LLM theme classification with provenance

**Complexity: Medium · Risk: Medium · Cost: ~$0.20 / 1k docs**

### What changes

Where `theme_taxonomy.classify`
([`theme_taxonomy.py:165`](../app/catalog/theme_taxonomy.py)) finds no themes,
classify the document's abstract against the closed label set from
[`app/data.json`](../app/data.json). Add a `theme_source ENUM('curated',
'inferred')` column to `documents_theme` and let the structured path choose
which to count.

### Rationale

Theme assignment today is pure name-matching against Drupal tags. Local PDFs
get no themes at all, so they are absent from theme-scoped retrieval and from
every per-theme count. A fixed, curated label set is close to the ideal setup
for zero-shot classification — the model picks from a list rather than
inventing labels, which makes output verifiable.

### Failure modes

- **This is the item with the real design risk.** `documents_theme` currently
  holds *asserted* facts (a curator tagged this) and feeds the structured
  count path. Mixing inferred labels in means "how many documents are under
  Energy?" silently starts returning a model's guesses alongside curated
  truth. The provenance column is not optional — without it, a visible gap
  becomes an invisible inaccuracy, which is strictly worse.
- Decide and document the default: I would count `curated` only unless the
  user asks for inferred coverage, since the catalog's value is that it is
  factual.
- Multi-label over-assignment: models tend to tag generously. Cap the number
  of inferred themes per document and require a confidence floor.
- `data.json` evolving means inferred rows drift out of date. The existing
  `scripts/reclassify_theme_rows` pattern covers curated rows; inferred rows
  need the same treatment or an explicit re-run.

### Dependencies

Item 7 (the abstract is the classifier input), plus a schema migration
following the idempotent pattern in `catalog/schema.py`.

---

## 9. Semantic near-duplicate detection + LLM adjudication

**Complexity: Hard · Risk: Medium · Cost: ~$1 / 1k docs**

### What changes

Detect near-duplicates using the **embeddings already computed** — cluster
abstract vectors, or check each new document against existing ones. Use the
LLM only to adjudicate the small set of borderline pairs: *same document /
superseding version / genuinely distinct?* Feed the outcome into `is_current`
and `linked_pdf_id`, which exist today but carry no supersession semantics.

### Rationale

Dedup is currently exact-only: `content_hash`
([`document.py:95`](../app/core/models/document.py)) plus URL dedup for
in-body PDFs (`change_detection/drupal.py:135`). Query-time cosine dedup
exists (`context_builder.py:183`, threshold `0.92`) but only within a single
result set.

The corpus structurally manufactures near-duplicates:

- a Drupal node body paraphrasing its own attached PDF;
- the same report published under both the `report` and `policy_brief`
  bundles;
- annual reports repeating 80% of the previous year;
- the same PDF reachable at two different URLs (URL dedup misses this).

The retrieval consequence is that the generator receives three paraphrases of
one fact and treats the repetition as corroboration.

Note the LLM is deliberately **not** the detector here — embeddings are
cheaper, already computed, and better at similarity. The LLM handles only the
judgement call, which is dozens of invocations per corpus, not one per
document.

### Failure modes

- **Wrongly merging distinct documents** is the serious one: a 2023 and 2024
  edition of the same annual report are ~90% similar and must stay separate.
  Bias hard toward "distinct" and never delete — mark supersession and let
  retrieval de-prioritize.
- Cross-document work does not fit the current per-document architecture.
  `_handle` (`pipeline.py:136`) processes one document in isolation, and
  parallel mode (`pipeline.py:270`) has no shared state. This most likely
  belongs as a **post-sweep pass**, not inside the per-document path — which
  is most of why this is Hard.
- Threshold tuning is corpus-specific and needs a labelled sample to
  calibrate. Budget for evaluation effort, not just implementation.

### Dependencies

Item 7 (abstract embeddings are the practical comparison unit). Best treated
as a separate pass after the enrichment items are stable.

---

## 10. LLM contextual chunk headers

**Complexity: Medium · Risk: Medium · Cost: ~$60–120 / 1k reports**

### What changes

For each child chunk, one LLM call over `(parent_text, child_text)` producing
a 1–2 sentence prefix situating the chunk in its document. Prepend to the
embedded text only.

### Rationale

The published "contextual retrieval" technique reports substantial reductions
in retrieval failure, and it composes with the existing parent/child design
rather than replacing it.

**However:** item 1 delivers a deterministic approximation of the same idea
for free. This item should only be evaluated *after* item 1 has been measured,
against the marginal gain over the breadcrumb baseline — not against today's
no-context baseline. That comparison is the whole decision.

### Failure modes

- **By far the most expensive item on this list** — one call per child chunk,
  ~60 children for a 40-page report. Prompt caching over the parent block
  helps materially but does not change the order of magnitude.
- Adds tens of seconds per large document. Fine for a nightly sweep, painful
  for the synchronous `/ingest/pdf` route.
- Generated context is model output stored in the embedding input. It cannot
  corrupt a citation (stored `chunk_text` is untouched) but it can skew
  retrieval toward the model's framing of a document.
- Amplifies every throughput concern in item 6 by roughly the chunk count.

### Dependencies

Items 3, 4, and — critically — measured results from item 1.

---

## 11. LLM OCR repair pass

**Complexity: Medium · Risk: High · Cost: ~$15 / 1k documents**

### What changes

On pages where `extracted_via is ExtractedVia.OCR`, an LLM pass repairing
extraction damage, replacing the hand-maintained
`_DROPPED_LIGATURE` dictionary
([`text_normalize.py:40`](../app/ingestion/extractors/text_normalize.py)) and
`_SUBSCRIPT_FIXES` regexes (`text_normalize.py:79`).

### Rationale

The current approach is a treadmill: ~40 hard-coded broken words and three
regexes, each added after someone noticed a specific failure. It will never be
complete, and every new corpus adds entries.

### Failure modes — read before considering this

This is **the only proposed change where a generative model rewrites source
text that will later be quoted as a citation** and checked by
[`faithfulness.py`](../app/generation/faithfulness.py). A silently altered
digit in an emissions table is unrecoverable corruption: it passes every
downstream check, because every downstream check trusts the extracted text.

If pursued, all of the following are required, not optional:

- restrict strictly to OCR-sourced pages;
- prompt for character-level repair only, with explicit "never change digits,
  never add or remove words" instruction;
- **gate on a diff** — reject the rewrite if edit distance exceeds a few
  percent, or if any numeric token changed;
- retain the raw text in the payload for audit.

**Recommendation:** treat item 5 (`prebuilt-layout` on the pages that matter)
as the preferred alternative. It buys more accuracy per rupee with zero
hallucination risk. Revisit this item only if a measured OCR-quality problem
survives item 5.

### Dependencies

Item 5 should be evaluated first, and may remove the need for this entirely.

---

## 12. Keep the heading heuristics as they are

**No change recommended.**

`line_heading_level` ([`segmenter.py:86`](../app/ingestion/chunking/segmenter.py))
is heuristic — word counts, capitalization ratios, numbering plausibility —
but it is well-tuned, covered by `test_chunk_heading.py`, and its failure mode
is bounded (a missed heading merges two sections; it does not corrupt text).

The real segmentation problem is upstream and is addressed by item 5: with
`prebuilt-read` there are no headings *to detect* on scanned pages. Replacing
a working deterministic parser with an LLM would add cost and
non-determinism without touching the actual cause.

---

## 13. Keep Drupal facet routing deterministic

**Complexity: Medium · Risk: Low · Cost: ~$0 (one-time)**

### What changes

Replace the substring-hint heuristics (`THEME_HINTS` / `TAG_HINTS` /
`AUTHOR_HINTS`, [`canonical.py:13`](../app/ingestion/canonical.py)) with an
**explicit per-bundle field mapping table**, committed to the repo.

Use an LLM **once, offline** to draft that mapping from the existing
[`field_audit.py`](../app/ingestion/field_audit.py) report — which already
identifies precisely which populated fields are dropped — then have a human
review and commit it.

### Rationale

Field-to-facet routing is stable per bundle. Paying a model per document for a
decision that changes only when the CMS schema changes is the wrong cost
shape. `field_audit.py`'s docstring already states the intent: *"The JSON
report is the ground truth for designing explicit per-bundle field mappings."*
This item is finishing that plan, with an LLM used as drafting assistance
rather than as a runtime dependency.

### Failure modes

- New bundles or renamed fields fall through a static map. Keep the substring
  hints as a logged fallback rather than deleting them, and keep the audit in
  a scheduled run so drift is visible.
- A hand-written mapping is only as good as its review. Budget the review time
  honestly; an unreviewed generated mapping is worse than the heuristics.

### Dependencies

None. Independent of every LLM item, and can proceed in parallel.

---

## 14. Do not adopt LLM semantic chunk boundaries

**No change recommended.**

Per-document LLM-chosen chunk boundaries ("semantic chunking") is a popular
proposal with weak evidence relative to its cost, and here it carries a
specific architectural conflict.

Chunk ids are `uuid5(document_id | version | suffix)`
(`chunking/__init__.py:54`). The safe swap in `_handle`
(`pipeline.py:176-183`) — index the new version first, then delete everything
else for the document — depends on those ids being **deterministic** for a
given document version. Non-deterministic boundaries mean every re-ingest
rewrites every point, and a mid-index failure no longer leaves the prior
version intact.

The current sizing presets ([`chunking/config.py`](../app/ingestion/chunking/config.py))
are already per-bundle and structure-aware. Tune those if chunk sizing proves
to be a problem.

---

## Recommended implementation order

Ordered by impact per unit of risk and effort. Each phase is independently
shippable; do not start a phase before its prerequisites are stable.

### Phase 1 — free, deterministic, no LLM (days)

1. **Item 1** — embed the section breadcrumb. Highest value-to-cost ratio on
   this list, and it establishes the retrieval baseline that item 10 must
   later beat.
2. **Item 2** — remove the dead settings.
3. **Item 13** — start the field-mapping work; it is independent and can run in
   parallel with everything below.

**Gate:** measure retrieval quality before and after item 1. That number is
the reference point for every later decision.

### Phase 2 — infrastructure for safe enrichment (1–2 weeks)

4. **Item 3** — content-hash stability. Blocking; plan the one-time
   re-version window.
5. **Item 4** — enrichment cache and backfill path.

Neither delivers user-visible value on its own. Both prevent expensive,
hard-to-diagnose failures later. Skipping this phase is the most likely way
for this roadmap to go wrong.

### Phase 3 — high-value enrichment (2–3 weeks)

6. **Item 6** — PDF front-matter extraction. Fixes a correctness gap in the
   structured catalog path, not just a quality one.
7. **Item 7** — document abstracts. Immediately recovers scoped-summary
   latency; ship alongside item 6 (same call site, same cache).
8. **Item 5** — scanned-document structure recovery. Slot here or earlier;
   independent of the LLM items but compounds with item 1.

### Phase 4 — evaluate, then decide (ongoing)

9. **Item 8** — theme classification, only with the provenance column.
10. **Item 9** — near-duplicate detection, as a post-sweep pass.
11. **Item 10** — contextual chunk headers, **only** if measured to beat the
    item 1 baseline by enough to justify ~$60–120 / 1k reports.
12. **Item 11** — OCR repair, **only** if a measured quality problem survives
    item 5.

### Cross-cutting requirements for every LLM item

- **Fail open.** An LLM timeout leaves fields `None` and the document still
  indexes. Every existing external dependency in this pipeline already behaves
  this way; enrichment must not be the exception that stalls a sweep.
- **Handle the synchronous upload path.** `ingest_upload`
  ([`upload.py`](../app/ingestion/upload.py)) indexes inline for
  `POST /ingest/pdf`. Either defer enrichment there or accept the added
  latency deliberately.
- **Raise `ingest_workers`.** It defaults to `1` (`config.py:265`).
  Enrichment makes ingestion TPM-bound; keep workers below `mysql_pool_size`
  and verify `ingest_batch_pause_seconds` behaves sanely against Azure rate
  limits.
- **Version every prompt.** Store the prompt/schema version with each cached
  value so a prompt change invalidates the cache instead of leaving stale
  output that looks current.
