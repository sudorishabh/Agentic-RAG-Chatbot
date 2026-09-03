# Bundle-specific date capture — implementation plan

**Status.** Implemented. This document is the plan the implementation followed;
the resulting behaviour is documented in
[06 — The Canonical Document and Date Resolution](06-canonical-document-and-dates.md).

**Goal.** The date captured at ingestion must be the *effective business date for
each Drupal bundle*, resolved from a bundle → date-field mapping, rather than the
generic Drupal record date. Attached PDFs inherit their parent page's resolved
date. Every date must be explainable from stored evidence.

**Revision 2 — date ranges.** A bundle maps to an *ordered list* of date
fields, not one field: `[start]` or `[start, end]`.

**Revision 3 — the publication-date model is removed.** `published_*` became
`effective_start_date` / `effective_end_date`, and the source-field taxonomy
stopped describing dates as publications.

Each revision supersedes the sections above it wherever the two differ, and the
closing section records what running the migration actually cost.

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

**Website records** — `canonical._effective_dates_for` → `source_dates.resolve_effective_dates`.
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
| `CanonicalDocument` | `effective_start_date`, `date_source`, `start_precision` (all named `published_*` at the time; see Revision 3) |
| MySQL `documents` | same four columns (`date_source VARCHAR(16)`) |
| MySQL `documents_date_decision` | one row per document: action, rule, confidence, evidence, `current_start_date`, `date_source` |
| Qdrant chunk payload | `effective_start_date`, `start_precision` (written **only** when `"year"`) — *not* `date_source` |

Downstream consumers of `effective_start_date`: recency ranking and date filters
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
| D3 | **Semantic change.** `field_completed_start_date`, `field_ongoing_start_date` and `field_event_start_date` are today classified `period`/`event` and deliberately refused, on the reasoning that a project's start and a conference's date are not when the page was written. The mapping makes them the effective date. This moves ~5,500 documents. | Implement as specified — it is the stated business requirement — but state plainly that `effective_start_date` now means **effective/business date**, not strictly "publication date", and keep the `Kind` classification for provenance. |
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
        ├──► website document: effective_start_date / _source / _precision
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

Reuses `source_dates.to_ist_date` / `is_plausible` / `as_stored_date` unchanged —
no new date format is introduced. Handles: bare four-digit year (int or str),
ISO date-times with any offset, `Z`, naive values (assumed UTC), lists (first
non-empty element), `None`/empty, unparseable, and out-of-range (1990 … next year).

## 5–6. PDF inheritance and multiple PDFs

The parent's `EffectiveDate` is resolved **once** per attachment build and carried
on `PageContext`. Every PDF on the page — one or many — takes that value, that
precision and `date_source="parent_page"`. File `created`, upload month,
DocInfo `CreationDate`/`ModDate`, filename years and ingestion time remain
*supporting signals only* and can never set a date.

## 7. Evidence / provenance

- `documents.date_source` — `created` | `cms_field` | `parent_page` | `document_text`.
- `documents.start_precision` — `year` | `day`.
- `documents_date_decision` — bundle, node uuid, page pdf count, the page's own
  date, the applied date, `date_source` = the field name, and a prose
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
| No `created` either | `effective_start_date = None`; existing `undated` flag fires | `created` | `no_date` |
| PDF with no parent page | cannot occur — an attachment record *is* `(node, file)` | — | — |

Falling back to `created` is justified: it is a real date the source states about
the record, it is exactly today's behaviour, and the alternative — no date — makes
a document invisible to every date filter rather than merely mis-ordered.

## 9. Data model / schema

No DDL change. `date_source` gains the value `parent_page` (11 chars,
fits `VARCHAR(16)`); `date_source` holds the field name (26 chars max, fits
`VARCHAR(32)`); `rule` values fit `VARCHAR(48)`.

## 10. Code changes

| File | Change |
| --- | --- |
| `app/ingestion/bundle_dates.py` | **New.** The mapping, `EffectiveDate`, `resolve`, `inherited`, `describe`. |
| `app/ingestion/source_dates.py` | Keeps the primitives and `FIELD_KINDS` (now provenance-only); `resolve_effective_dates` becomes a bundle-aware adapter delegating to `bundle_dates`. |
| `app/ingestion/canonical.py` | `_effective_dates_for(bundle, created, metadata)`; both Drupal builders pass the bundle. |
| `app/ingestion/date_evidence.py` | `PageContext` gains `node_start_date`, `date_field`, `date_field_value`, `date_source`, and `effective_date` / `date_from_bundle_field`. |
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
| `test_canonical_effective_start_date.py` (rewritten) | The builder applies the value, precision and provenance, carries the evidence for the audit row, keeps it out of the chunk payload, and disturbs nothing else on the document. |
| `test_source_date_decisions.py` (rewritten) | When a row is and is not written, which outcomes reach the review queue, and that `date_type` records what kind of date the field holds. |
| `test_date_resolution_pipeline.py` (extended) | That a PDF inherits its bundle's resolved date, and that a stated bundle date settles the case without reading the file or calling the model. |
| `tests/scripts/test_backfill_source_dates.py` (rewritten) | The retired script refuses, names its replacement, and retains no write path. |

`test_source_dates.py`, `test_reconcile_date_checks.py`, `test_date_resolution.py`
and `test_effective_start_date_provenance.py` needed no changes — the concepts they pin
(field classification, plausibility, the LLM gates, precision provenance) are
unchanged.

## 12. Migration / backfill

Ingestion code alone does **not** fix historical rows. `effective_start_date` lives in
three places; two need updating and one does not:

- `documents.effective_start_date` — UPDATE.
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
   than from the current `effective_start_date`.

---

# Revision 2 — bundle → *one or more* date fields

**Goal.** A bundle may carry a single date or a start/end pair. The abstraction
becomes `bundle → ordered list of date fields`, where the first is the
effective/start date and the second, if configured, is the end. A single-date
bundle is not a special case of a range bundle, nor the reverse: both are the
same shape with a different number of fields.

## 1. Existing single-date assumptions

The Revision 1 model is single-valued throughout:

| Where | Assumption |
| --- | --- |
| `BUNDLE_DATE_FIELDS` | `dict[str, BundleDateField]` — exactly one field per bundle, carrying its precision |
| `EffectiveDate` | `value`, `precision`, `field`, `raw_value` — one of each |
| `PageContext` | `node_start_date`, `node_start_precision`, `date_field`, `date_field_value` |
| `ResolvedDate` | `effective_start_date`, `precision` |
| `CanonicalDocument` / `StateRecord` / `DocumentMeta` | `effective_start_date`, `start_precision` |
| MySQL `documents` | `effective_start_date`, `start_precision` |
| `documents_date_decision` | `candidate_start_date` |
| Qdrant payload | `effective_start_date`, `start_precision` |
| `backfill_bundle_dates` | one value per document |

Nothing anywhere can express "and it ran until".

## 2. Validated field shapes — full published corpus, sampled 2026-09-02

Measured through the project's own `to_ist_date` / `is_plausible` rather than by
string comparison, because that distinction turns out to matter.

**`completed_projects` — 1,168 published records**

| Outcome | Count |
| --- | --- |
| Ordered range (start < end) | 1,148 |
| Same day (start == end) | 11 |
| **Inverted (start > end)** | **2** |
| End field holds an unusable value (all three are `1970-01-01`, the zero timestamp) | 3 |
| Start present, end absent | 3 |
| **End present, start unusable** | **4** |

Span: median 436 days, max 10,956 (about 30 years).

**`events` — 1,094 published records**

| Outcome | Count |
| --- | --- |
| Ordered range | 308 |
| **Same day (start == end)** | **784** |
| **Inverted** | **2** |

Both fields are single-valued strings, `+00:00`, IST-midnight encoded, present on
100% of records, and never a dict or a list.

Two findings shape the design:

1. **Compare normalised calendar dates, not raw values.** By raw string, 13
   events and 5 completed projects look inverted. After `to_ist_date` only **2 and
   2** are, because the rest differ solely in the time component and land on the
   same Indian calendar day, and because `is_plausible` removes the three
   `1970-01-01` ends first.
2. **`start == end` is the normal case for an event** — 784 of 1,094, a one-day
   event — so it is valid, not a defect.

### Discrepancy

| # | Finding | Resolution |
| --- | --- | --- |
| D8 | **`field_ongoing_end_date` does not exist.** Drupal answers a filter on it with "The field `field_ongoing_end_date` ... does not exist", and the attribute is absent from all 595 published `ongoing_projects` records. | Confirmed with the requester as a mistake in the supplied mapping. `ongoing_projects` stays **single-field**. That is also the semantically right answer: an *ongoing* project has no end date. |

## 3. The range-aware data model

Precision stops being declared per bundle and is derived **per field** from
`source_dates.FIELD_KINDS`, which already declares `(kind, precision)` for every
one of these fields. One fact, one place.

```python
BUNDLE_DATE_FIELDS: dict[str, tuple[str, ...]] = {
    "article":            ("created",),
    ...
    "research_papers":    ("field_rpaper_year",),
    "completed_projects": ("field_completed_start_date", "field_completed_end_date"),
    "ongoing_projects":   ("field_ongoing_start_date",),
    "events":             ("field_event_start_date", "field_event_end_date"),
}
```

`EffectiveDate` gains a symmetric end, and "one or more fields" is represented
literally rather than as two named slots:

```python
@dataclass(frozen=True)
class EffectiveDate:
    value: str | None                 # the effective/start date
    precision: Precision
    source: Source
    rule: str
    end_value: str | None = None      # never manufactured
    end_precision: Precision | None = None
    bundle: str | None = None
    fields: tuple[str, ...] = ()      # ordered, exactly as configured
    raw_values: tuple[Any, ...] = ()  # parallel to `fields`
    kind: str = "unknown"
    range_issue: str | None = None
```

`value` and `precision` keep their names: they *are* the effective date, they map
to `effective_start_date` / `start_precision`, and renaming them would churn every
consumer to say the same thing. `start_field`, `end_field`, `start_raw`,
`end_raw`, `has_range` and `end_missing` are properties over `fields` and
`raw_values`, so a bundle that grows a third field needs no new attributes.

## 4. Resolution and validation

Every configured field runs through the **same** per-field resolution — extract,
`to_ist_date`, `is_plausible`, bare-year precision downgrade. The endpoints are
then compared as normalised calendar dates:

| Case | Behaviour | `range_issue` |
| --- | --- | --- |
| No end field configured | `end_value = None` | `None` |
| `start <= end` (including `start == end`) | both kept | `None` |
| **`start > end`** | end **dropped**, start kept, raw values preserved, review row | `inverted` |
| End field empty | `end_value = None`, start kept — a valid partial range | `None` (`end_missing` is true) |
| End field holds a non-date | end dropped, raw preserved, review row | `end_invalid` |
| **End present, start unusable or empty** | start falls back to `created`, **the end is preserved**, review row | `end_without_start` |
| Both absent | the Revision 1 `field_empty` ladder, unchanged | `None` |

Values are never swapped and an end date is never manufactured.
`end_without_start` deliberately does **not** re-run the inversion check against
the fallback `created` stamp: a creation stamp is not a range endpoint, so
comparing one to the other would assert a relationship the source never made.

## 5. Storage

| Store | New |
| --- | --- |
| `CanonicalDocument`, `StateRecord`, `DocumentMeta` | `effective_end_date`, `end_precision` |
| MySQL `documents` | `effective_end_date DATETIME NULL`, `end_precision VARCHAR(8) NULL`, both through the idempotent `_ensure_column` |
| MySQL `documents_date_decision` | `candidate_end_date DATETIME NULL`, `range_issue VARCHAR(24) NULL` — plus `_ensure_column` calls, which this table did not previously have at all |
| Qdrant payload | `effective_end_date`; `end_precision` only when `"year"`, mirroring the existing rule for the start |

`effective_end_date` reads naturally against `effective_start_date` and reuses the existing
naming convention rather than introducing a second vocabulary.

**No `PIPELINE_VERSION` bump.** The test in `app/ingestion/version.py` is "would a
reader expect a field that old points lack?" — nothing reads `effective_end_date`
yet (§6), so no reader breaks, and the backfill writes it onto existing points. A
bump would force a full corpus reprocess to add a key the migration already
writes.

## 6. Downstream consumers — classified, and deliberately unchanged

Every use of `effective_start_date` was reviewed.

**Need only the effective/start date; unchanged:**

| Consumer | Why |
| --- | --- |
| `retrieval/search/reranker.py` recency | Recency is about one point in time |
| `retrieval/structured/tools.py` — list, group-by-year, "latest" | Chronological ordering is by the effective date |
| `retrieval/search/temporal_gate.py` | Already routes relationship-time questions *away* from `effective_start_date` to claim intervals |
| `generation/prompts.py`, `generation/date_claims.py` | Render the document's date; the guard anchors on `effective_start_date` deliberately |
| `knowledge/graph/{writer,project}.py` | Projects the document date onto the graph node |
| `pipeline/summarize.py`, `retrieval/context/builder.py` | Display and dedup |

**Could use the range, and are left alone in this revision:**

| Consumer | Note |
| --- | --- |
| `retrieval/understanding/filters.py` `_DATE_FIELD` | Every date scope is one `DatetimeRange` over `effective_start_date`. Making a scope match on interval *overlap* changes what a query returns — a retrieval-behaviour decision, not a data-model one |
| `retrieval/structured/filters.py` | The same, over MySQL |

This is the backward-compatibility requirement: the end date is **captured,
stored, propagated and explainable**, and no ranking or filtering behaviour
changes here. Switching retrieval to interval overlap is a separate, measurable
change.

## 7. Files changed

`app/ingestion/bundle_dates.py`, `canonical.py`, `date_evidence.py`,
`date_resolution.py`, `date_rules.py`, `extractors/attachment.py`, `pipeline.py`,
`reconcile.py`, `chunking/{models,payload,__init__}.py`;
`app/core/models/document.py`; `app/catalog/{models,state,schema,date_decisions}.py`;
`scripts/backfill_bundle_dates.py`; the docs; the tests.

## 8. Risks

1. **The end date is inert.** Nothing filters on it yet, so "which projects were
   active in 2015" still gets start-date behaviour. Deliberate (§6); the data is
   now there to change it.
2. **About 2,250 documents gain an end date** (completed projects and events),
   and their attachments inherit it. No start date moves because of this revision.
3. **11 documents reach the review queue** — 2 + 2 inverted, 3 unusable ends,
   4 end-without-start. All are real CMS defects, all visible in
   `documents_date_decision` rather than silently corrected.
4. A deployment that never ran the Revision 1 migration needs both, in order.

---

# Revision 3 — the publication-date model is removed

**Goal.** Stop representing a document's date as a *publication* date. The system
resolves an effective/business date from the bundle's configured field; for
`events` and the project bundles that field is a start date, and calling the
result a publication date was simply wrong.

## What the names became

| Was | Is |
| --- | --- |
| `published_at` | `effective_start_date` |
| `published_until` | `effective_end_date` |
| `published_at_precision` | `start_precision` |
| `published_until_precision` | `end_precision` |
| `published_at_source` | `date_source` |
| `current_published_at` | `current_start_date` |
| `candidate_date` / `candidate_source` | `candidate_start_date` / `date_source` |
| `resolve_published_at` | deleted — a compatibility adapter |
| `document_published_at` | **deleted** |

`EffectiveDate` and `ResolvedDate` now share four field names — `start_value`,
`start_precision`, `end_value`, `end_precision` — so a caller holding either
reads the same way and neither endpoint is the implicit one.

**`document_published_at` was deleted rather than renamed.** It was modelled as
"the date the document states about itself" and **no path ever assigned it**: not
ingestion, not a script, not a backfill. Every row was NULL, and the prompt line
that rendered it always said "not stated". There was no data to carry across.

## The source-field taxonomy

`FIELD_KINDS` became `FIELD_ROLES`, and its vocabulary changed from claims about
the resulting date to descriptions of the Drupal field:

| Was | Is | Why |
| --- | --- | --- |
| `publication` | `date` | The misleading one. The field states the content's date; whether that is a "publication" is not something this system asserts. |
| `event`, `period` | `range_start`, `range_end` | The event/period split controlled nothing — the bundle already says which. The **start/end** split is load-bearing: `BUNDLE_DATE_FIELDS` is ordered `(start, end)`, and this is the only independent check that a pair is not reversed. |
| `event` (on `field_enddate_forlatestfirst`) | `sort_key` | It was mis-classified. It orders a listing and describes nothing, and a test now asserts no bundle maps to it. |
| `unknown` | `not_a_date` | `unknown` implied "unclassified"; these three *are* classified, as non-dates. |
| — | `created_stamp` | A bug the live check caught: `classify("created")` returned `not_a_date`, putting "that field is not a date field" into the audit row of every `article` and `page`. |

`upload`, `authoring`, `edition`, `notification` and `effective` were dropped —
no CMS field used them. They still exist in
`app.ingestion.date_rules.DateType`, which classifies a date the model found
**inside a PDF's text**: a different question about a different thing, and the
one place the word "publication" still earns its keep. The two share the
`documents_date_decision.date_type` column, told apart by `origin`, and a test
asserts the value sets are disjoint.

## `PIPELINE_VERSION`

`PAYLOAD` 1 → 2. Payload *keys* changed, which is exactly what that component
tracks; without the bump a deployment that skipped the migration would serve
points whose date keys no reader consults, with nothing to signal it. The bump is
cheap: `_reusable_vectors` keys on chunk id + `embed_hash` + `embed_model`, none
of which this touches, so a re-indexed document reuses its stored vector and
nothing is re-embedded.

## The guard

`tests/ingestion/dates/test_no_publication_date_vocabulary.py` asserts the
retired names are **absent** from `app/` and `scripts/`, with an explicit
allowlist of three files that name them because their job is to remove them
(`schema.py`, `backfill_bundle_dates.py`, `version.py`). A rename that leaves the
old names reachable invites new code to reach for them.

---

# Running it — what the migration actually cost

Kept because it is the part that cannot be reconstructed from the diff, and
because every failure below was found by *running* the thing, not by testing it.

## The shape of the problem

The date lives in three stores — MySQL, Qdrant payloads, Neo4j Document nodes —
and the migration is only correct if its steps run in one order. Nothing enforced
that, and it produced four defects:

1. **A silent no-op projection.** `ensure_state_table()` is additive: it creates
   the new columns *empty*. Running the graph projection then read NULL for every
   row, and because Cypher *removes* a property set to NULL, it reported success
   while writing no dates at all — leaving stale `published_at` properties from an
   older run.
2. **A dry run that measured nothing.** `page_moves()` read the new columns to
   recover each page's creation stamp, but the copy that fills them ran *after*
   the move set was computed. On a half-migrated database every page was silently
   skipped: the run reported 2,296 moves, all attachments, 0 of 8,507 pages.
   Fixed by reading through `COALESCE(new, legacy)` so the same query is correct
   before the copy, after it, and after the drop.
3. **A pre-flight refusal that was right.** 31 moves carried no timezone (a
   creation stamp read back from a MySQL `DATETIME` is naive) and 2 would have
   stored a range running backwards (`end_without_start`, where the fallback start
   is a 2017 import stamp and the real end is 1999). The resolver's comment and
   the pre-flight contradicted each other; the pre-flight was right.
4. **A payload clobber that would have been invisible.** `apply()` wrote the
   corrected date under the new key but left the legacy key on the point, and
   `migrate_payload_keys()` then read the legacy name and wrote it back over the
   correction. MySQL and Neo4j would both have looked right while Qdrant silently
   reverted on ~5,150 documents. Fixed by making the key migration
   order-independent: it reads both names and never overwrites a new key that
   already holds a value.

## The recovery path

`apply()` writes MySQL in one `executemany` and Qdrant in a loop afterwards, so a
crash between them leaves MySQL complete and Qdrant partial — and the move set,
computed by diffing against the stored MySQL value, is then empty. A retry writes
nothing and strands everything.

So `--repair-qdrant` is driven by the **catalogue**, not by a move set: MySQL is
the authority, every point is reconciled to its row, and the run is idempotent and
resumable. It never promotes a legacy value, because for an uncorrected document
`published_at` holds the *old* date.

Its write path deliberately **does not scroll**. Reading the collection is what
failed twice (a client-side zstd allocation error against a container using a
tenth of its memory), and the catalogue already holds the answer. The legacy keys
are dropped in one collection-wide call, **last**, and only on a run that reached
the end — dropping them first would open a window in which a point carried neither
the old key nor the new one.

## Three interruptions, three causes

| # | Cause | Response |
| --- | --- | --- |
| 1–2 | client-side zstd allocation error decompressing scroll responses | removed the scroll from the write path |
| 3 | the whole compose stack was stopped and started underneath the run — both containers started 2 ms apart, `RestartCount 0`, `ExitCode 0` | retry backoff extended to 112 s so a restart is sat out; resume hint printed on failure |

Progress was monotonic and durable throughout — 1,171 → 10,508 → 60,382 points —
because every write is idempotent. That is the property that made three
interruptions survivable rather than compounding.

## What to do differently

- **Make a migration idempotent and resumable before running it**, not after.
  Every fix above is a variation on that one property.
- **Never let a monitoring query compete with the run.** A full-collection scroll
  or a filtered `exact=True` count is the same class of work as the migration
  itself; two sessions checking progress timed out the very run they were
  watching. Sample a few hundred points instead.
- **A read that is correct in only one migration state is a bug.** `COALESCE`
  over the legacy column costs nothing and removes a whole class of ordering
  defect.
- **Freeze and checksum the artifact** when more than one person is verifying it.
  A reproduced number is worth nothing if the file moved underneath it.
- **Distrust a confident number more than an error.** Every defect that got past
  review on this change produced a plausible result rather than an exception, and
  in most cases the answer was already written down somewhere in this repository.
  Four instances in one day, across two unrelated workstreams:

  | What was reported | What was true |
  | --- | --- |
  | dry run: "2,296 documents would change" | 0 of 8,507 pages were even examined |
  | graph projection: "VERIFY: OK" | every node had had its date property removed |
  | eval: a configuration scoring 0.000 | the retrieval call had timed out |
  | eval: 512-token and 256-token runs scoring identically | the 512 run was inheriting 256 from `.env` |

  Three of those four had a precedent in the codebase that would have prevented
  them — `ensure_payload_indexes` documents a mutation outliving the client
  timeout and says to confirm by reading back; `build_payload` documents writing
  a precision marker only when it is meaningful. The knowledge was present and
  simply not reached for.

  It is worth being precise about that, because the tempting generalisation —
  "this repository's knowledge is prose that nothing enforces" — is false, and
  was checked. `test_no_minimum_relationship_date_exists_in_the_retrieval_path`
  iterates *every* template asserting no `date()` or `datetime()` reaches the
  Cypher, and its own docstring explains why: "asserted structurally, because the
  failure mode is a constant nobody notices". `test_fusion_score_integrity.py`
  does the same for the reranker's score scale, and `test_architecture.py` for
  the layering rules. The knowledge existed in two forms, prose and tests, and
  the failures above came from consulting neither. That is a search problem on
  the reader's part, not a structural gap in the repository — a less flattering
  diagnosis and a more accurate one. When a number looks right, the useful question is not
  "is it plausible?" but "what would this read if the thing it measures had not
  run at all?" — because that is the value all four of these returned.
