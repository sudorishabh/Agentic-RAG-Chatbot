# 02 — Sources and Data Acquisition

**Purpose.** Turn a live Drupal site into a stream of self-contained records the
rest of the pipeline can process one at a time.

**Inputs.** An HTTP endpoint (`drupal_jsonapi_base`, default
`https://teriin.org/jsonapi`), and the previous run's catalog state.

**Outputs.** A generator of `ChangeRecord` objects, each carrying a document id, a
status, a fingerprint and — for actionable records — the payload needed to build
a document without going back to the network.

**Components.** `app/ingestion/extractors/drupal_extractor.py` (the HTTP and
parsing layer), `app/ingestion/change_detection/drupal.py` (the crawl loop and
the change decision).

---

## The source system

TERI's website is a Drupal site exposing the JSON:API module at
`/jsonapi/{entity_type}/{bundle}`. The pipeline reads it **anonymously** — there
are no credentials in the ingestion configuration for the source, and that has a
consequence worth stating early: an anonymous client is served **only published
content**. `filter[status]=0` comes back empty, and an unfiltered walk returns
exactly the published set. So the pipeline cannot distinguish an unpublished
document from a deleted one, and treats them identically (see
[04, Delete reconciliation](04-change-detection-and-versioning.md#delete-reconciliation)).

### Which sources are crawled

Two lists, and they deliberately live in **different places**:

```python
# app/core/corpus.py  — shared vocabulary, read by both paths
DEFAULT_BUNDLES = ("article", "page", "research_papers", "completed_projects",
                   "feature_articles", "ongoing_projects", "news", "events",
                   "press_release", "policy_brief", "videos", "infographics",
                   "services", "report", "people")           # 15 node bundles

# app/ingestion/extractors/drupal_extractor.py — crawl-only settings
DEFAULT_BLOCKS  = ("basic",)                                  # block_content
SEARCHABLE_ENTITY_TYPES = frozenset({"node", "block_content"})
```

`DEFAULT_BUNDLES` sits in the neutral core layer because the **read** path needs
the identical list for three jobs — describing the corpus to the model
(`retrieval/understanding/catalog_prompt.py`), registering one queryable entity
per bundle (`retrieval/structured/entities.py`), and deciding whether a scope name
is a bundle (`pipeline/summarize.py`). Those three used to import it straight from
this extractor, which made retrieval depend on how the crawler happens to be
implemented. `drupal_extractor` re-exports it under the name the crawl has always
used, so ingestion code and tests read unchanged.

`DEFAULT_BLOCKS` and `SEARCHABLE_ENTITY_TYPES` stay here: no reader has any use
for them.

- `carousel` is deliberately excluded: those nodes are homepage promo slides with
  a title and no body, so they chunk to nothing, and the subjects they name are
  already covered by real news and event content.
- `block_content` is not a node bundle, but block bodies are prime corpus content
  the node crawl never reaches, so they are fetched as a separate source.

A source is a triple `(entity_type, bundle, incremental)`. Only node bundles are
incremental; the small block set is fetched in full every run and change-detected
purely on its fingerprint.

### The allowlist, and why taxonomy terms are refused

```python
SEARCHABLE_ENTITY_TYPES = frozenset({"node", "block_content"})
```

This is an **allowlist, not a list of exclusions**, so a new JSON:API entity type
cannot become a searchable document by default. It is enforced in
`_searchable_sources()`, on the single path that reaches chunking and Qdrant —
and applied to the *caller's* list as well as the default one, so
`--bundle taxonomy_term:themes` or a `POST /ingest/run` naming it gets the same
refusal with a logged reason.

Taxonomy terms are the case this exists for. A term is a *label a document
carries*, not a document: its name already travels in the payload of every
content chunk that references it (`categories` / `tags`), and that is what theme
and tag filtering match on. Crawling the term as well records the same fact a
second time as a near-empty document — most vocabularies carry no description at
all — and puts it in front of retrieval, where it can be returned *in place of*
the content it was only ever meant to label.

Metadata is untouched by this rule: it drops taxonomy **sources**, never the
taxonomy **references** on content records.

---

## Transport: the HTTP session

`_build_session(max_retries)` returns a `requests.Session` with:

- `Accept: application/vnd.api+json`
- A `urllib3` `Retry` mounted on both schemes: `total=drupal_max_retries`
  (default 3), `backoff_factor=1.0`, `status_forcelist=(429, 500, 502, 503, 504)`,
  `allowed_methods={"GET"}`, `respect_retry_after_header=True`.
- Per-request timeout `drupal_request_timeout` (default 60s), passed at call
  sites.

**One session per run.** `ingest_drupal` builds a session for attachment
downloads and closes it in a `finally`; the crawl builds its own and closes it in
a `finally`. Reusing one session means PDF downloads reuse its connection pool
rather than re-handshaking TLS per attachment — on a bundle with hundreds of PDFs
that is the difference between minutes and tens of minutes.

Retries here are **transport-level only**. A 4xx is not retried (it is not in the
force list), and a document-level failure is handled by the retry-marker
machinery described in [10](10-failures-retries-and-recovery.md), not by HTTP
retries.

---

## Walking a bundle

`iter_bundle_records(session, bundle, entity_type=..., published_only=...,
changed_since=..., ascending=...)` is a generator over one source.

### Step 1 — discover relationship fields

`_discover_relationship_fields` fetches **one** record (`page[limit]=1`) and
reads its `relationships` keys, keeping those that start with `field_`. Those
names are then passed as `include=` on every page request, so referenced entities
(taxonomy terms, people nodes, file entities) arrive embedded in the same
response instead of costing a request each.

If the sample fetch fails, it returns `[]` and the bundle is crawled without
`include` — degraded (labels will be missing) but not fatal.

### Step 2 — build the query

```
page[limit]      = drupal_page_size            (default 50)
sort             = _sort_key(entity_type, ascending)
include          = field_a,field_b,...          (when discovered)
filter[status]   = 1                            (when published_only)
filter[changed]  = >= changed_since             (when incremental)
```

### Step 3 — the sort key, and why it has a tiebreaker

```python
_SERIAL_ID_FIELD = {"node": "drupal_internal__nid",
                    "block_content": "drupal_internal__id",
                    "taxonomy_term": "drupal_internal__tid"}
```

Ascending, the sort is `changed,drupal_internal__nid`. Both halves matter.

**Oldest-first** is what makes `MAX(changed_mark)` usable as a resume cursor.
Newest-first would advance the mark past unprocessed older documents whenever a
run is capped or interrupted, stranding them behind the incremental filter
forever.

**The serial-id tiebreaker** makes the sort *total*. Thousands of records share a
single `changed` value from the site's 2017 content migration, and offset
pagination over a non-unique sort has no defined order among the ties — the order
the server happens to pick differs between page requests, so rows shift across
page boundaries. Measured on the live site, a plain `changed` sort never returned
**137 of 1,167** `completed_projects` while returning **126 others twice**,
silently, and the same records every run.

An entity type whose id field is not in `_SERIAL_ID_FIELD` keeps the plain
`changed` sort on purpose: a sort field the resource does not have answers HTTP
400 and loses the whole bundle, which is worse than the duplicate-and-skip it
would have fixed.

### Step 4 — page through

`_iter_pages` follows JSON:API's `links.next.href` until it is absent. Query
parameters are sent on the first request only; the `next` URL already carries
them. Each page yields `(data, included)` where `included` is keyed by
`(type, id)` for O(1) relationship resolution. `response.raise_for_status()` means
a non-2xx page raises — and the caller catches it per bundle.

---

## Building one record

`_build_record(node, included, bundle, site, entity_type=...)` produces a
`DrupalRecord`:

| Field | Source |
| --- | --- |
| `uuid` | `data.id` |
| `bundle` | the source's bundle |
| `nid` | `attributes.drupal_internal__nid` |
| `title` | `attributes.title` → `name` → `info`, stripped (terms use `name`, blocks use `info`) |
| `url` | `site + attributes.path.alias`, or `None` |
| `body` | every formatted-text field, flattened and joined |
| `created` | `attributes.created` → `attributes.revision_created` → `None` |
| `changed` | `attributes.changed` |
| `metadata` | short scalar `field_*` values plus resolved relationship labels |
| `files` | attached PDFs plus in-body PDF links |
| `refs` | `EntityRef` objects for every resolved relationship target |

### Attribute partitioning

`_partition_attributes` splits `attributes` into **body parts** and **metadata**:

- A dict with `processed` or `value` is a formatted-text field → flattened to text
  and treated as body.
- A `field_*` string longer than `LONG_TEXT_THRESHOLD` (255) → body.
- A `field_*` bool, number, short string, or homogeneous list of scalars →
  metadata.
- Anything else, and every non-`field_*` scalar, is Drupal plumbing and ignored.

Body parts are sorted so `body` leads, which keeps the main narrative first in
the concatenated text and therefore first in the chunk stream.

### `created`, and the block problem

`_created_at` reads `created`, then `revision_created`, then gives up.
`block_content` does not expose `created` at all, so before the fallback existed
every block — and every PDF hanging off one — was catalogued with **no date
whatsoever**: 109 documents invisible to every date filter and to recency
ranking, rather than merely ranked low.

`revision_created` is the timestamp of the revision being served. On a first
revision that *is* the creation date; on a later one it reads later than the
truth. It is used only where `created` is absent, and it is a real timestamp the
source states about this record — the alternative is not a better date, it is no
date. `changed` is deliberately **not** a third fallback: it moves on every edit,
so it would describe the document's last touch rather than its origin.

Nothing is synthesised. A record exposing neither field stays undated, is logged
as such by the pipeline, and is counted by the reconciliation report.

### Relationship resolution

`_resolve_relationships` walks `field_*` relationships plus `parent` (the taxonomy
tree link) and produces two things:

- `metadata[field] = [label, ...]` — the display names, which is what facet
  routing reads.
- `refs: list[EntityRef]` — `(field_name, uuid, entity_type, label)`, so catalog
  joins stay correct when a term is later renamed.

Three targets are skipped: `virtual` (the placeholder parent of root taxonomy
terms), `missing` (JSON:API's identifier for a relationship target that no longer
exists), and `file--file` (handled by `_resolve_files`). The first two are never
resolvable, so keeping them as refs would put an unresolvable id in the payload.

Refs are kept even when the entity is not embedded in `included` — the label
stays `None`, but the uuid is still recorded.

### HTML to text

`_html_to_text` runs a small `HTMLParser` subclass, `_TextExtractor`, which
preserves what a naive tag-strip loses:

| Markup | Becomes |
| --- | --- |
| `<a href="X">text</a>` | `text (X)` — in-page anchors (`#…`) and `javascript:` are dropped |
| `<img alt="A">` | `[image: A]` |
| `<iframe src="S">` | `[embedded: S]` |
| `<td>` / `<th>` | ` | ` separated cells |
| block elements | newlines |
| `<script>` / `<style>` | dropped entirely |

Output is whitespace-normalised per line, with runs of blank lines collapsed to
one. Keeping link destinations matters because a page whose body is a list of
links is otherwise reduced to link labels with no way to reach the target.

---

## PDF discovery

PDFs are found two ways, and both become `DrupalFile` records that the crawl
turns into `pdf_attachment` documents.

### Real file attachments — `_resolve_files`

Scans **every** `field_*` relationship for `file--file` targets, because the file
field name varies per bundle (`field_policybrieffile`, `field_report`,
`field_*_full_text`, …). For each:

- Keep it if `filemime == "application/pdf"` **or** the filename ends `.pdf`.
- If it is not a PDF but *is* a document type (`.doc .docx .xls .xlsx .ppt
  .pptx .csv`), log a warning and skip — so a genuinely missed source is visible
  rather than silent. Images and other media are excluded without noise.
- Resolve `attributes.uri.url` to an absolute URL through the same
  `_normalize_link` the in-body path uses (`from_html=False`, since there are no
  HTML entities in a JSON value and a filename that really contains `&amp;` must
  not be rewritten). Using `urljoin` rather than a prefix test means a
  scheme-relative or leading-slash-less `uri.url` cannot be concatenated into
  nonsense.
- Record `uuid` (the file entity's), `origin="attachment"`, `filename`,
  `description` (from the relationship `meta`), and the file entity's own
  `created`.

### In-body PDF links — `_extract_inbody_pdfs`

Scans **every** rich-text field, not just `body` — in-body PDF links were
confirmed in `body` and in several `field_*` text fields
(`field_completed_featured_text`, `field_ongoing_featured_text`, …). Three regexes
run over each field:

- `_HREF_PDF_RE` — `href="....pdf"` (optionally with a query string).
- `_BARE_PDF_RE` — a bare `https://….pdf` in prose.
- `_ANCHOR_PDF_RE` — the same link *with its anchor text kept*.

Anchor text is captured separately because **a PDF's link text is often the only
place its identity is written down**. Every TERI annual report is an in-body
attachment on one page, so all ten would inherit the page title "Annual Reports"
unless the anchor ("Annual Report 2024-2025") is kept. One PDF is often linked
twice on a page — a thumbnail image wrapped in an `<a>` with no text, beside a
captioned text link — so anchors are keyed by URL and the **longest** text wins,
which stops the image link blanking the caption. Anchor text is HTML-unescaped as
well as tag-stripped: it becomes the file's description, which
`build_attachment_doc` prefers over the node's title and which citations display,
and 20 of the 69 anchors on one page carry an entity.

Candidates are then normalised and filtered:

1. `_normalize_link` — HTML-unescape, strip surrounding whitespace, `urljoin`
   against the site base. Both halves cost real documents when missing:
   `Receipts_&amp;_Payments.pdf` stayed escaped and every download 404'd
   (15 links; the decoded URLs all answer 200), and `href=" https://…"` did not
   start with "http" once the space was counted, so an absolute URL was resolved
   as a relative one — producing an unresolvable
   `https://teriin.org/ https://www.ceew.in/….pdf` while the bare-URL regex
   matched the same link correctly, so the page emitted *two* documents, one that
   worked and one that never could.
2. The path (before `?`) must still end `.pdf`.
3. **Internal vs external.** Internal means no host, the configured site host, or
   a host containing `teriin.org` or `teri.res.in`. Internal PDFs are always
   harvested; external ones only when `drupal_ingest_external_pdfs` is on
   (default off — the corpus stays TERI-authored, and the external URL still
   survives in the body text via the link-preserving extractor).
   Host comparison uses `removeprefix("www.")`, **not** `lstrip("www.")`:
   `lstrip` strips the *character set* `{w, .}` and mangles `web.teriin.org` into
   `eb.teriin.org`.
4. De-duplicate against URLs already seen on this record.

Each surviving link gets a **URL-stable synthetic uuid**:

```python
uuid = f"inbody:{sha1(abs_url).hexdigest()}"
```

so the same PDF linked from several pages ingests exactly once, and so the
identity is reproducible without a file entity behind it. The filename is
percent-**decoded** here and only here — `abs_url` keeps its escapes because that
is what gets fetched, but the filename is metadata that gets displayed and read
for years and edition spans, and left encoded `Report%2024.pdf` offers the four
digits "2024" to the year detector via `%20` + `24`, a year nothing stated.

Candidates are iterated in **sorted** order rather than set order: two spellings
of one link normalise to the same URL and the same identity, but the order
documents are emitted in should not vary between runs over identical input.

---

## Records the crawl yields

Inside `detect_drupal_changes`, per source record:

1. **Boilerplate blocks are dropped first.** A `block_content` record whose
   stripped body is shorter than `drupal_block_min_chars` (default 200) *and*
   which carries no PDF is skipped — search boxes, "Follow us" strips, footer
   chrome.
2. **One `website` record**, fingerprinted on the node's `changed` string.
3. **Then one `pdf_attachment` record per PDF the node carries**, in order.

The ordering is load-bearing: an attachment record follows its node immediately,
and the batch budget refuses to stop between them (see
[03, The batch budget](03-triggers-and-control-plane.md#the-batch-budget)) — if a
run stopped after the node, the node's freshly written state row would make it
`UNCHANGED` next run and its attachments would never be reached.

### Attachment fingerprints

| Origin | Fingerprint | Why |
| --- | --- | --- |
| `attachment` | the node's `changed` | The file is part of the node's publication; re-fetch it when the node changes. |
| `inbody` | the in-body uuid itself | A percent-encoded PDF URL runs well past the catalog's `VARCHAR(128)` fingerprint column and the write failed with MySQL error 1406. The uuid *is* already a URL fingerprint, so reusing it is both short and correct. |

### Per-run de-duplication

`seen_pdf` is a run-scoped set of file uuids. An in-body PDF linked from several
nodes is yielded once, by the first node that references it — which is also the
node whose facets and entity refs it inherits.

### Dead-link suppression

Before yielding an attachment, the crawl consults the dead-link markers loaded
once at the start of the run. If a marker exists **and its fingerprint still
matches** the record's, the attachment is skipped and counted; at the end of the
run one line reports how many were suppressed. See
[10, Dead links](10-failures-retries-and-recovery.md#dead-attachment-links).

---

## Downloading an attachment

`extractors/attachment.build_attachment_doc(record, session)` is the document
builder for `pdf_attachment` records. `record.payload` is the
`(DrupalRecord, DrupalFile)` pair the crawl captured, so nothing is re-fetched
from JSON:API.

### `fetch_attachment` — the http→https upgrade

For a `http://` URL, the HTTPS variant is tried **first**. Old body HTML still
links plain-http PDFs, but teriin.org no longer answers on port 80 — the connect
attempt hangs until the timeout — while the same files are served fine over TLS.
The original URL remains the fallback so hosts that really are http-only keep
working. The function returns `(content, url_that_succeeded)`, and it is that URL
that lands in `file_url` on the document.

### Failure handling

```
RequestException
  ├─ dead_link_status(exc) is a 4xx  → warn once, write a dead-link marker,
  │                                    return None (document skipped)
  └─ anything else (timeout, DNS,
     5xx after retries)             → log with full traceback, return None
```

A 4xx means the server answered and the file is not there — old body HTML links
tender notices and RFQs that were taken down once they closed, and no amount of
retrying brings them back. Timeouts, DNS failures and 5xx can clear on their own,
so they keep the traceback that says which one it was and stay retryable with no
marker.

An empty response body is also a skip, with a warning.

Both skips return `None`, which `_handle` turns into the `skipped` outcome and a
retry marker whose reason says the document could not be built.

---

## Validation performed at this stage

| Check | On failure |
| --- | --- |
| `record.uuid` is present | record skipped silently (a record with no id cannot be catalogued) |
| Entity type is in `SEARCHABLE_ENTITY_TYPES` | source dropped, warning naming the entity types |
| Block body length vs `drupal_block_min_chars` | record skipped (unless it carries a PDF) |
| Attachment mime/extension is PDF | skipped; warned if it is a `.docx`-family document |
| `uri.url` present | file skipped |
| In-body URL path ends `.pdf` after normalisation | link ignored |
| In-body host is internal, or externals enabled | link ignored |
| HTTP status on any page fetch | bundle logged and skipped, run continues |
| HTTP status on an attachment | document skipped; 4xx additionally marked dead |

## Failure scenarios and their blast radius

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| Source host unreachable / TLS failure | `requests` raises inside `iter_bundle_records` | `logger.exception("Drupal fetch failed for %s/%s; skipping bundle")`, `continue` to the next source | Next sweep. The high-water mark did not move for that bundle, so nothing is lost. |
| One bundle 400s (bad sort field, renamed bundle) | Same path | Same — that bundle only | Fix the bundle name, or accept the plain-`changed` sort fallback |
| Relationship sample fetch fails | `RequestException` caught in `_discover_relationship_fields` | Warning, crawl continues with no `include` | Labels are missing this run; they return next run |
| Mid-pagination failure | Raise from `_iter_pages` | Bundle abandoned; records already yielded were already processed | Next sweep re-fetches from the same window |
| PDF host slow | Per-request timeout | Document skipped, retry marker written | Next sweep |
| PDF permanently removed | 4xx | Dead-link marker; suppressed until its fingerprint changes | Re-upload the file and save the node, or clear the marker |
| A page adds a `.docx` attachment | mime/extension check | Warning naming file and node | Add an extractor, or accept the gap knowingly |
| Malformed in-body URL | `_normalize_link` + `.pdf` check | Link ignored, or corrected and harvested | The corrected URL yields a *new* uuid, so the document arrives as `NEW` |

## Observability at this stage

- `Drupal ingestion started (bundles=…, reconcile=…)` — one line per run.
- `Extracted %d records from node/%s` — per bundle, in the standalone
  `iter_records` path.
- `Skipping non-PDF document attachment %r (mime=%s) on %s` — the visible gap.
- `Not crawling %s: … are metadata on content documents` — allowlist refusals.
- `Skipped %d attachment(s) the site last answered with a client error` — once
  per run, at the end.
- `HTTPS variant failed for %s; retrying original URL.` — the upgrade path.
- Span `ingest.extract` wraps the whole document build, tagged with
  `source_type`, and is aggregated as the `extraction` component in
  `GET /metrics/timings`.

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `drupal_jsonapi_base` | `https://teriin.org/jsonapi` | Source endpoint. The site base for URL resolution is derived by splitting on `/jsonapi`. |
| `drupal_request_timeout` | `60` | Per-request timeout, used for JSON:API and for PDF downloads. |
| `drupal_page_size` | `50` | `page[limit]`. Raising it reduces round trips and increases the cost of one failed page. |
| `drupal_max_retries` | `3` | Transport retries for 429/5xx with backoff. |
| `drupal_ingest_external_pdfs` | `false` | Whether non-TERI in-body PDFs are downloaded. |
| `drupal_block_min_chars` | `200` | Boilerplate-block threshold. |

## Hand-off to the next stage

The crawl hands `_handle` a `ChangeRecord` whose `payload` is either a
`DrupalRecord` (for `website`) or a `(DrupalRecord, DrupalFile)` pair (for
`pdf_attachment`) — or `None` when the status is `UNCHANGED`, because an unchanged
record is never built and carrying its payload would be wasted memory. The
decision about *which* of those statuses applies is [04](04-change-detection-and-versioning.md).

---

Previous: [01 — Overview](01-overview.md) · Next: [03 — Triggers, Transport and the Control Plane](03-triggers-and-control-plane.md)
