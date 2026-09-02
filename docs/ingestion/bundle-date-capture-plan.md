# Bundle-specific date capture — implementation plan

**Status.** Implemented. This document is the plan the implementation followed;
the resulting behaviour is documented in
[06 — The Canonical Document and Date Resolution](06-canonical-document-and-dates.md).

**Goal.** The date captured at ingestion must be the *effective business date for
each Drupal bundle*, resolved from a bundle → date-field mapping, rather than the
generic Drupal record date. Attached PDFs inherit their parent page's resolved
date. Every date must be explainable from stored evidence.

---

## 1. Current-state analysis

Measured on the live site (`https://teriin.org/jsonapi`, sampled 2026-09-02) and
read from the code, not assumed.

### How content is fetched

`app/ingestion/extractors/drupal_extractor.py` crawls JSON:API per bundle.
`_build_record` produces a `DrupalRecord(uuid, bundle, nid, title, url, body,
created, changed, metadata, files, refs)`.

- **Bundle identity** is the crawl parameter itself — `iter_bundle_records(bundle)`
  — so it is known before a record is parsed and is carried on `DrupalRecord.bundle`,
  `ChangeRecord.bundle` and the `documents.bundle` column.
- **`created`** comes from `_created_at`: `attributes.created` falling back to
  `revision_created` (block_content has no `created`). Never `changed`.
- **`metadata`** is `_partition_attributes` (scalar `field_*` attributes) plus
  `_resolve_relationships` (reference labels). Every mapped date field lands here
  as a scalar.

### How the date is currently resolved

Two independent paths.

**Website records** — `canonical._published_at_for` → `source_dates.resolve_published_at`.
The design is **field-keyed, not bundle-keyed**: `FIELD_KINDS` declares what each
field *means* globally, and only the four fields marked `publication`
(`field_news_date`, `field_pressrelease_date`, `field_report_date`,
`field_rpaper_year`) may set a date. Event and project-period fields are declared
and deliberately refused. A year-precision value is declined when `created`
already sits in that year.

**Attached PDFs** — `attachment.build_attachment_doc` → `date_resolution.resolve`.
The page date is `evidence.page.node_created` — **the raw creation stamp, never
the node's resolved date**. A verified publication statement quoted from the PDF's
own text may override it (`date_rules.decide` → `date_llm.interpret` → ten gates).

### Where the date is stored and who reads it

| Sink | Field |
| --- | --- |
| `CanonicalDocument` | `published_at`, `published_at_source`, `published_at_precision`, `document_published_at` |
| MySQL `documents` | same four columns (`published_at_source VARCHAR(16)`) |
| MySQL `documents_date_decision` | one row per document: action, rule, confidence, evidence, `current_published_at`, `candidate_source` |
| Qdrant chunk payload | `published_at`, `document_published_at`, `published_at_precision` (written **only** when `"year"`) — *not* `published_at_source` |

Downstream consumers of `published_at`: recency ranking and date filters
(`retrieval/search/temporal_gate.py`, `reranker.py`, `structured/filters.py`),
chronology in `pipeline/query_pipeline.py`, prompt rendering
(`generation/prompts.py`, `generation/date_claims.py`), the knowledge/claims
temporal layer, and reconciliation.

### PDF ↔ parent relationship

A PDF is its own `ChangeRecord` (`source_type="pdf_attachment"`,
`payload=(DrupalRecord, DrupalFile)`), its own `CanonicalDocument` and its own row.
It links back through `source_url` (the page), `linked_article_uuid`, and the
`documents_attachment` table. Multiple PDFs on one page are already separate
documents; `PageContext.pdf_count` records how many.

### Validated bundle → field facts

All 14 mapped bundles exist and every mapped field exists and is populated.

| Bundle | Field | Live shape | Fill (sampled) |
| --- | --- | --- | --- |
| article, page, feature_articles, policy_brief, videos, infographics, people | `created` | ISO 8601 `+00:00` | 100% |
| research_papers | `field_rpaper_year` | **int**, 2012–2019 | 399/400 |
| completed_projects | `field_completed_start_date` | ISO `+00:00` (IST midnight) | 400/400 |
| ongoing_projects | `field_ongoing_start_date` | ISO `+00:00` | 400/400 |
| news | `field_news_date` | ISO `+00:00` | 400/400 |
| events | `field_event_start_date` | ISO `+00:00` | 400/400 |
| press_release | `field_pressrelease_date` | ISO `+00:00` | 400/400 |
| report | `field_report_date` | ISO **`+05:30`** with real clock times | 6/8 |

No field is multi-valued, a date range, or a dict on this site.

### Discrepancies between the mapping and reality

| # | Finding | Recommendation (taken) |
| --- | --- | --- |
| D1 | `services` is crawled (`DEFAULT_BUNDLES`) but absent from the mapping. It has **no** date-like field. | Declare `services → created` explicitly so the table covers the whole crawl and "unmapped" stays a real alarm. |
| D2 | `block_content:basic` is crawled and is not a node bundle; it has no `created`. | Left unmapped → falls to the documented `created` default, which `_created_at` already resolves to `revision_created`. |
| D3 | **Semantic change.** `field_completed_start_date`, `field_ongoing_start_date` and `field_event_start_date` are today classified `period`/`event` and deliberately refused, on the reasoning that a project's start and a conference's date are not when the page was written. The mapping makes them the effective date. This moves ~5,500 documents. | Implement as specified — it is the stated business requirement — but state plainly that `published_at` now means **effective/business date**, not strictly "publication date", and keep the `Kind` classification for provenance. |
| D4 | `field_rpaper_year` is year-precision, and the current rule *declines* it when `created` already falls in that year (228 papers keep a real day). The new mapping is unconditional. | Apply unconditionally. Keep `precision="year"` so the 1-January value is read as a year marker, not a January publication. Cost: intra-year ordering is lost for those 228. |
| D5 | `field_report_date` is null on 2/8 live `report` nodes and carries `+05:30` offsets. | Documented fallback to `created`; `to_ist_date` already converts the offset correctly. |
| D6 | PDFs inherit `node.created`, never the node's *resolved* date — so a `research_papers` PDF is already dated differently from its own page. | Fixed: inherit the parent's resolved effective date. |
| D7 | The LLM `document_text` override can move a PDF off its parent's date, conflicting with "the parent page's resolved effective date is authoritative". | The bundle field wins: when the parent's date came from a bundle date field, the PDF keeps it and the LLM path is skipped entirely. Where the parent falls back to `created` — the weak case the override was built for — the override still applies. |

---

## 2. Proposed date-resolution architecture

One decision function, one configuration table, two entry points that both call it.

```
DrupalRecord(bundle, created, metadata)
        │
        ▼
bundle_dates.field_for(bundle)      ← the one mapping
        │
        ▼
bundle_dates.resolve(bundle, created, metadata)
        │  extract → normalise (IST) → plausibility → fallback ladder
        ▼
EffectiveDate(value, source, precision, bundle, field, raw_value, rule)
        │
        ├──► website document: published_at / _source / _precision
        │                      + documents_date_decision row
        │
        └──► PageContext.effective_date  ─►  every attached PDF
                                             (same value, same precision,
                                              source="parent_page")
```

The core logic is generic: bundle → field → extract → normalise → effective date.
Adding a bundle is one row in `BUNDLE_DATE_FIELDS` and no change to any algorithm.

## 3. Bundle → date-field mapping

`app/ingestion/bundle_dates.BUNDLE_DATE_FIELDS`, exactly the supplied mapping plus
D1's `services`.

## 4. Extraction and normalisation

Reuses `source_dates.to_ist_date` / `is_plausible` / `as_published_at` unchanged —
no new date format is introduced. Handles: bare four-digit year (int or str),
ISO date-times with any offset, `Z`, naive values (assumed UTC), lists (first
non-empty element), `None`/empty, unparseable, and out-of-range (1990 … next year).

## 5–6. PDF inheritance and multiple PDFs

The parent's `EffectiveDate` is resolved **once** per attachment build and carried
on `PageContext`. Every PDF on the page — one or many — takes that value, that
precision and `published_at_source="parent_page"`. File `created`, upload month,
DocInfo `CreationDate`/`ModDate`, filename years and ingestion time remain
*supporting signals only* and can never set a date.

## 7. Evidence / provenance

- `documents.published_at_source` — `created` | `cms_field` | `parent_page` | `document_text`.
- `documents.published_at_precision` — `year` | `day`.
- `documents_date_decision` — bundle, node uuid, page pdf count, the page's own
  date, the applied date, `candidate_source` = the field name, and a prose
  `evidence` sentence naming bundle, field, value, title and URL.
- Written for every document whose bundle maps to a real field, and for every PDF.

## 8. Missing / invalid dates

| Case | Behaviour | `source` | `rule` |
| --- | --- | --- | --- |
| Bundle maps to `created` | use `created` | `created` | `bundle_created` |
| Field present, valid | use it | `cms_field` | `bundle_date_field` |
| Field absent / empty / null | fall back to `created`, INFO log | `created` | `field_empty` |
| Field unparseable / implausible | fall back to `created`, WARNING log | `created` | `field_invalid` |
| Bundle not in the mapping | fall back to `created`, INFO log once | `created` | `bundle_unmapped` |
| No `created` either | `published_at = None`; existing `undated` flag fires | `created` | `no_date` |
| PDF with no parent page | cannot occur — an attachment record *is* `(node, file)` | — | — |

Falling back to `created` is justified: it is a real date the source states about
the record, it is exactly today's behaviour, and the alternative — no date — makes
a document invisible to every date filter rather than merely mis-ordered.

## 9. Data model / schema

No DDL change. `published_at_source` gains the value `parent_page` (11 chars,
fits `VARCHAR(16)`); `candidate_source` holds the field name (26 chars max, fits
`VARCHAR(32)`); `rule` values fit `VARCHAR(48)`.

## 10. Code changes

| File | Change |
| --- | --- |
| `app/ingestion/bundle_dates.py` | **New.** The mapping, `EffectiveDate`, `resolve`, `inherited`, `describe`. |
| `app/ingestion/source_dates.py` | Keeps the primitives and `FIELD_KINDS` (now provenance-only); `resolve_published_at` becomes a bundle-aware adapter delegating to `bundle_dates`. |
| `app/ingestion/canonical.py` | `_published_at_for(bundle, created, metadata)`; both Drupal builders pass the bundle. |
| `app/ingestion/date_evidence.py` | `PageContext` gains `node_published_at`, `date_field`, `date_field_value`, `date_source`, and `effective_date` / `date_from_bundle_field`. |
| `app/ingestion/date_rules.py` | Decisions anchor on `page.effective_date`; new first rule `parent_bundle_date_field` short-circuits to keep. |
| `app/ingestion/date_resolution.py` | `build_evidence` takes the parent `EffectiveDate`; `resolve` returns its precision and source. |
| `app/ingestion/extractors/attachment.py` | Resolve the parent's date once; PDFs get `parent_page` + the parent's precision. |
| `app/catalog/date_decisions.py` | `from_effective_date` replaces `from_source_record`; PDF rows carry the inheritance sentence. |
| `app/ingestion/pipeline.py` | Records the website decision from the `EffectiveDate`. |
| `app/ingestion/reconcile.py` | Bundle-aware `stated_date_not_applied`; new `unmapped_bundle_dates` check. |
| `scripts/backfill_bundle_dates.py` | **New.** Recompute pages from `bundle` + `raw_meta`, then push each page's date onto its attachments. Dry run by default. |
| `scripts/backfill_source_dates.py` | Superseded; refuses to run and points at the new script. |
| `scripts/backfill_date_provenance.py`, `scripts/scrape_site_dates.py` | Pass the record's bundle when asking the shared resolver. |
| `docs/ingestion/{01,06,10,11,12,README}.md` | Updated for the new flow, checks and runbooks. |

## 11. Testing strategy

| Module | Covers |
| --- | --- |
| `tests/ingestion/dates/test_bundle_dates.py` (new) | The mapping pinned one case per bundle against a second, hand-written copy of the supplied JSON; that it covers every crawled bundle and adds none the crawl does not fetch; resolution per bundle with the live field shapes; the whole fallback ladder (empty, absent, unparseable, implausible, far-future, multi-value, bare year, unmapped bundle, no bundle, no date at all); inheritance; the provenance prose; and that every emitted value fits the column that stores it. |
| `tests/ingestion/dates/test_pdf_date_inheritance.py` (new) | A page with 0, 1, 2, 3 and 12 PDFs; that each file stays its own document linked to the parent; precision inheritance; and one test per signal that must *not* set a date — upload stamp, URL month, filename year, PDF metadata (asserted never even read), the model (asserted never called). Plus the audit row's inheritance sentence, through the real builder. |
| `tests/scripts/test_backfill_bundle_dates.py` (new) | The pre-flight refusals, and attachment inheritance including a file shared by two pages, a file dated from its own text, and a precision-only change. |
| `test_canonical_published_at.py` (rewritten) | The builder applies the value, precision and provenance, carries the evidence for the audit row, keeps it out of the chunk payload, and disturbs nothing else on the document. |
| `test_source_date_decisions.py` (rewritten) | When a row is and is not written, which outcomes reach the review queue, and that `date_type` records what kind of date the field holds. |
| `test_date_resolution_pipeline.py` (extended) | That a PDF inherits its bundle's resolved date, and that a stated bundle date settles the case without reading the file or calling the model. |
| `tests/scripts/test_backfill_source_dates.py` (rewritten) | The retired script refuses, names its replacement, and retains no write path. |

`test_source_dates.py`, `test_reconcile_date_checks.py`, `test_date_resolution.py`
and `test_published_at_provenance.py` needed no changes — the concepts they pin
(field classification, plausibility, the LLM gates, precision provenance) are
unchanged.

## 12. Migration / backfill

Ingestion code alone does **not** fix historical rows. `published_at` lives in
three places; two need updating and one does not:

- `documents.published_at` — UPDATE.
- Qdrant chunk payloads — `set_payload` (no re-embed: the vector is built from
  `chunk_text`, which does not change).
- `documents_date_decision` — rewritten by the same run.

**No re-extraction, re-chunking or re-embedding**, and no `PIPELINE_VERSION` bump:
no payload *key* changes, only values of keys that already exist. Content hashes
are unaffected, so the next ordinary sweep will not re-index the corpus.

## 13. Risks

1. **~5,500 documents move** (D3). Ranking and date-filtered answers change for
   projects and events. This is the intended effect of the requirement.
2. **228 research papers lose intra-year ordering** (D4).
3. **Events move to the future.** `field_event_start_date` can post-date the
   crawl; `is_plausible` caps at next year, beyond which the record falls back to
   `created`.
4. **Fewer LLM date calls.** Attachments on mapped bundles short-circuit, which is
   cheaper but means previously-detected in-document publication statements no
   longer override — by design (D7).
5. **Backfill idempotence** is guaranteed by re-deriving from `raw_meta` rather
   than from the current `published_at`.
