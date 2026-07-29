# teriin.org — Drupal JSON:API Coverage Analysis

**Date:** 2026-07-03
**Author:** generated from a live audit of `https://www.teriin.org`
**Scope:** Compare everything published on teriin.org against what our
ingestion pipeline fetches through the Drupal JSON:API
(`app/ingestion/extractors/drupal_extractor.py`), and identify content that is
missing or lost.

> **Status:** Analysis complete; **R1–R5 + R7 implemented and verified against
> live data** on branch `feat/drupal-coverage-inbody-pdfs`. This document is the
> living record — the [Change Log](#change-log) tracks what was done, and the
> [Implementation](#8-implementation) section (§8) summarises the code changes.

---

## 1. Executive summary

- At the **node** level our coverage is essentially complete. We fetch 15 of
  the 20 node bundles; of the 5 we skip, **4 are empty or demo junk** and only
  `carousel` (2 records) has real content.
- The real gaps are **outside node bundles**: several **taxonomy vocabularies**
  and **custom blocks** carry substantial, page-rendered prose that never enters
  the corpus — most importantly `taxonomy_term--themes` (TERI's thematic work
  descriptions), `taxonomy_term--extra_pages`, and
  `taxonomy_term--regional_centre`.
- A second class of loss is **transform loss**: we flatten body HTML to text,
  which drops hyperlink destinations, inline-image alt text, and embedded media
  (YouTube / maps / chart iframes); and we keep only PDF attachments, dropping
  any Office-document attachments.
- **PDFs linked inside rich-text fields** (not attached as `file--file`) are
  missed entirely — **~1,143 distinct PDF URLs across all of Drupal**: 1,096 in
  node text fields (528 nodes), 46 in custom blocks, 1 in a taxonomy term. These
  are core substantive documents (policy briefs, reports) and are fully
  fetchable. See §6.4. **This is the highest-impact content gap found.**
- Some website content is **not stored as a node at all** (homepage, section
  landing pages) — it is composed from Drupal Views + blocks, so it is only
  partially reachable via the API (via `block_content`).

---

## 2. Methodology

All figures below come from live calls to the production JSON:API on
2026-07-03:

- `GET /jsonapi` → full resource-type index (88 types).
- Per-bundle record counts by paging `GET /jsonapi/node/{bundle}?filter[status]=1`.
- Text sampling of `description` / `body` fields on taxonomy terms and blocks.
- The published **XML sitemap** (`/sitemap.xml`) as the site's own "what's
  public" list, reconciled URL-prefix by URL-prefix against bundles.

Notes / caveats:
- JSON:API does not return a total-count, so counts were obtained by paging;
  very large bundles are shown as `N+` where paging was capped.
- The sitemap page is capped at 500 URLs and is partially stale (see §6).
- Some pages (`/profile/*`, `/technology/*`) are WAF-protected (HTTP 403) to
  datacenter IPs; they were resolved via the JSON:API and a reader proxy.

---

## 3. JSON:API resource inventory

The site exposes **88 resource types**. They fall into:

- **20 `node--*` content types** (the article-like content) — see §4.
- **14 `taxonomy_term--*` vocabularies** — see §5.
- **`block_content--basic`** custom blocks — see §5.
- **`file--file`** (attachments) — handled, see §6.
- ~50 config/system resources (`block--block`, `menu--menu`, `view--view`,
  `user--user`, `search_api_*`, `image_style--*`, etc.) — not content.

---

## 4. Node bundle coverage

Our `DEFAULT_BUNDLES` (`drupal_extractor.py`) lists 15 bundles. Reconciliation
against the live site (published counts):

| Bundle | Fetched? | Published count | Notes |
|---|---|---|---|
| news | ✅ | ~1500+ | |
| feature_articles | ✅ | 1499 | |
| completed_projects | ✅ | 1162 | |
| events | ✅ | 1082 | |
| press_release | ✅ | 707 | |
| research_papers | ✅ | 624 | |
| ongoing_projects | ✅ | 585 | |
| article | ✅ | 456 | `/blog`, `/opinion`, `/interview` aliases resolve here |
| policy_brief | ✅ | 241 | |
| videos | ✅ | 217 | |
| page | ✅ | 131 | static pages (About, Mission, Founders, …) |
| infographics | ✅ | 45 | |
| services | ✅ | 30 | |
| people | ✅ | 8 | leadership/Governing Council only |
| report | ✅ | 8 | |
| **carousel** | ❌ | **2** | homepage banners (WSDS, Green Olympiad) — **should add** |
| products | ❌ | 0 | empty |
| recommendations | ❌ | 0 | empty |
| simplenews_issue | ❌ | 0 | empty (no newsletter nodes) |
| migrate_example_beer | ❌ | 0 | Drupal demo/migration junk — ignore |

**Conclusion:** the only non-empty content type we skip is `carousel`.

---

## 5. Gaps outside node bundles (reachable via JSON:API, not fetched)

The extractor only iterates `/jsonapi/node/{bundle}`. It never requests
taxonomy terms or blocks, several of which carry real prose.

### 5.1 HIGH value — rich descriptions, currently absent from the corpus

| Resource | Count | What it is |
|---|---|---|
| `taxonomy_term--themes` | 35 | Descriptions of TERI's thematic work areas (Air, Buildings, CSDR, …). Multi-paragraph. Renders as the thematic landing pages. |
| `taxonomy_term--extra_pages` | 9 | Landing pages: Corporate Social Responsibility, Energy Transitions (ETC India), HFCs, … each with several paragraphs. |
| `taxonomy_term--regional_centre` | 5 | Descriptions of regional centres (Nainital/TRISHA, Guwahati, Bengaluru, …). |

Sample (`themes` → *Air*): *"Long before air pollution became a national
concern, we built strong expertise in air quality research and management… We
actively support the implementation of the National Clean Air Programme
(NCAP)…"* — this "what TERI does" prose exists nowhere in the node corpus.

### 5.2 MEDIUM value

| Resource | Count | What it is |
|---|---|---|
| `block_content--basic` | 91 (≈38 substantial) | Custom blocks placed on pages: homepage highlight/announcement strips, About snippets. Mixed with boilerplate (Search box, "Follow us" footer). Needs a length/boilerplate filter. |
| `node--carousel` | 2 | Homepage banner items (see §4). |

### 5.3 LOW value — labels only, already captured indirectly

These vocabularies have **no descriptions** — they are just names, and we
already capture them as node metadata via the `field_*` relationship resolver
(`_resolve_relationships`). No standalone ingestion needed:

`division` (36), `division_areas` (62), `programs_units` (9), `partners` (748),
`region` (274), `stakeholders` (11), `podcast_category` (6), `tags` (1500+),
`language`, `related_terms`, `migrate_example_beer_styles`.

---

## 6. What is NOT reachable via JSON:API / lost in transform — exactly what a visitor sees that we miss

This section answers: *of the content a human sees on teriin.org, what will our
RAG never have?* Three distinct categories:

### 6.1 View/block-composed pages (not stored as a single node)

Some pages a visitor reads are **assembled by Drupal at render time** from
Views (query-driven lists) and placed blocks — there is no single node holding
their text:

- **The homepage** — hero carousel + curated highlight strips + "About us"
  snippet + latest-content lists. The prose parts live in `block_content`
  (§5.2) and `carousel` (§4); the *lists* are just links to nodes we already
  have.
- **Section/overview landing pages** (e.g. a theme overview, "Our People"
  listing, project listings) — the intro copy is a block or a
  `taxonomy_term` description (§5.1); the body is a View of nodes.
- **Search / facet / tag pages** — pure aggregations, no original content.

**What's missed:** the curated intro/announcement copy on these composed pages.
Reachable only through `block_content` + the taxonomy descriptions in §5 — which
today we don't fetch. The listing bodies themselves are not "lost" (they point
at nodes we already ingest).

### 6.2 In-body markup flattened to plain text (partial loss on content we DO fetch)

`_html_to_text` converts each body's HTML to plain text. That keeps paragraph
text but drops structure and embedded media. Measured over samples:

| Element | Seen in | What is lost |
|---|---|---|
| `<a href>` | events (~57 links / 15 recs), policy_brief, research_papers | The **link destination URL is dropped** — only the anchor text survives. So DOI/journal links, registration links, "read more" targets, and cross-references are not retrievable. A user asking "give me the link to X" can't be answered. |
| `<iframe src>` | events | **Embedded media fully dropped**: YouTube videos, Google Maps, Datawrapper/Flourish charts. Invisible to the RAG. |
| `<img alt>` | feature_articles, article (many) | Inline-image **alt text / captions are dropped** (alt is an attribute, not element text). `<figcaption>` text does survive. |
| `<table>` | events (agendas/schedules), articles | Table **content survives but structure is flattened** — `<td>`/`<th>` are not block-level in the parser, so cells concatenate. Row/column meaning is lost. |

### 6.3 Non-PDF file attachments

`_resolve_files` keeps only `application/pdf`. In the recent-file sample the
attachments were `image/jpeg` (45) and `application/pdf` (5) — images are
correctly excluded as non-text. **Risk:** any attached **DOCX/XLSX/PPTX**
document would be silently dropped. Low frequency today, but unbounded — no
alerting exists if such an attachment appears.

*(Multiple PDFs per node ARE handled — `change_detection.py` iterates
`record.files`, so this is not a gap.)*

### 6.4 PDFs linked inside body HTML — NOT `file--file` attachments (HIGHEST-IMPACT GAP)

Content editors frequently paste PDF links **into the body** (e.g.
`<a href="/sites/default/files/2019-04/RE-Reference-Report.pdf">…</a>`),
especially for large documents, rather than using the node's file-attachment
field. These fall through **both** of our capture mechanisms:

1. `_resolve_files` only scans `field_*` → `file--file` relationships, so these
   are invisible to it (they are not attachments).
2. `_html_to_text` **drops the `href`**, so we don't even retain the URL — only
   the anchor text survives.

**Measured — FULL uncapped sweep, every published node, every text field
(2026-07-03):**

- **8,428 nodes scanned; 528 nodes** contain at least one PDF link.
- **1,096 distinct PDF URLs** in nodes (**768 internal** + **328 external**).
- By bundle (nodes with ≥1 link): `policy_brief` **135**, `article` 97,
  `events` 82, `ongoing_projects` 51, `press_release` 50, `page` 44,
  `completed_projects` 42, `research_papers` 10, `infographics` 9,
  `feature_articles` 3, `videos` 3, `report` 2.
- **The links are NOT only in `body`.** Field breakdown of where PDF links were
  found: `body` (1,151), **`field_completed_featured_text` (43)**,
  **`field_ongoing_featured_text` (3)**, `field_rpaper_publisher` (2),
  `field_rpaper_published_in` (2). ⇒ R7 must scan **all** rich-text /
  long-string fields, not just `body`.

**Also outside nodes** (searched the whole Drupal, 2026-07-03):

- **`block_content--basic`: 46 PDF URLs** in `body` — the homepage/section
  highlight blocks ("New in Climate / Air / Transport / Cities …") link straight
  to policy-brief and report PDFs, including subdomains
  (`greenbudgeting.teriin.org`).
- **`taxonomy_term--extra_pages`: 1** ("Work with Us" → `strategy-plan.pdf`).
- All other taxonomies (themes, division, partners 750, region 274, tags 2000,
  related_terms 200, …), `simplenews_newsletter`, `comment`, `menu_link_content`
  — **clean, 0 PDF links.**

**⇒ ~1,143 distinct PDF URLs across all of Drupal.**

**Fetchable?** Yes. The URL is present in the rich-text HTML that JSON:API
already returns. Reachability spot-check of 6 internal URLs: **all HTTP 200,
`Content-Type: application/pdf`, valid `%PDF` header**, sizes **200 KB – 9.9 MB**
(the largest matches the "large PDFs in the body" the Drupal team flagged).
External URLs are absolute and also downloadable (ingesting third-party content
is a policy decision — see R7).

### 6.5 Intentionally-not-content (for completeness)

Menu/navigation, breadcrumbs, footer contact block, cookie/consent text,
facets, and `comment--node_comments` (commenting is effectively unused). No
action recommended.

---

## 7. Recommendations (detailed, prioritized)

### R1 — Add the three content-bearing taxonomies (HIGH, low effort) — ✅ IMPLEMENTED

Fetch `taxonomy_term/themes`, `taxonomy_term/extra_pages`,
`taxonomy_term/regional_centre` and ingest their `description` as body text.

- **Why it's cheap:** `_partition_attributes` already routes any attribute
  that is a dict with `processed`/`value` into the body path. A taxonomy term's
  `description` is exactly that shape, so **no text-parsing changes are needed** —
  only the iterator must be allowed to hit a non-`node` resource path.
- **Code change:** `iter_bundle_records` hardcodes `f"{base}/node/{bundle}"`
  and `_discover_relationship_fields` assumes `node`. Introduce a resource
  *type* (`node` | `taxonomy_term` | `block_content`) so a bundle can be fetched
  under the right path. Give taxonomy records a sensible `url`
  (`{site}/…` term alias) and `source`.
- **Metadata:** set `bundle` to e.g. `themes` and add a discriminator
  (`entity_type: taxonomy_term`) so retrieval/citation can label them.

### R2 — Add `node--carousel` (LOW effort) — ✅ IMPLEMENTED

One-line addition to `DEFAULT_BUNDLES`. 2 records; homepage banners.

### R3 — Ingest substantial custom blocks (MEDIUM) — ✅ IMPLEMENTED

Fetch `block_content/basic`, keep only blocks whose stripped body exceeds a
length threshold (≈200 chars drops the Search/Follow-us boilerplate; ≈38 of 91
qualify). Tag them `entity_type: block_content`. Give them a stable `source`
(block UUID) since blocks have no canonical URL.

### R4 — Preserve link destinations and embedded media in body text (MEDIUM) — ✅ IMPLEMENTED

Enhance `_TextExtractor`:
- For `<a href>`, append the URL, e.g. `anchor text (https://…)`, so external
  references and DOIs stay retrievable.
- For `<iframe src>` / `<img alt>`, emit a marker like
  `[video: https://youtu.be/…]` / the alt text, so embedded media is at least
  discoverable.
- Treat `<td>`/`<th>` as cell separators (tab/`|`) so tables keep row structure.

### R5 — Alert on dropped non-PDF document attachments (LOW) — ✅ IMPLEMENTED

In `_resolve_files`, log a warning when a `file--file` attachment is a
document MIME we skip (docx/xlsx/pptx). Decide per-need whether to extract them.

### R7 — Harvest in-body PDF links as attachment documents (HIGH — highest impact) — ✅ IMPLEMENTED

Extract `<a href="…pdf">` targets from each node's body HTML and treat them as
additional `DrupalFile`s so the existing attachment pipeline
(`_build_attachment_doc`) downloads + PDF-extracts them.

- **Where:** in `_resolve_files` (or a new sibling helper), scan **every
  rich-text / long-string attribute** (any dict with `processed`/`value`, plus
  long `field_*` strings) — confirmed the links live in `body` *and* in
  `field_completed_featured_text`, `field_ongoing_featured_text`,
  `field_rpaper_*`, so a `body`-only scan misses ~50 URLs. Match anchors
  (`href="…pdf"`) **and** bare `https://…pdf` URLs (case-insensitive, ignore
  query string). Resolve relative hrefs against the site base; dedupe against
  PDFs already found as `file--file` attachments and against duplicate URLs.
  Apply the **same scan to `block_content--basic` (46 URLs) and taxonomy
  descriptions (1)** once those resources are ingested (R3/R1).
- **Internal vs external:** internal (`teriin.org` / relative) — ingest.
  External (191 URLs, other domains) — gate behind a setting
  (`drupal_ingest_external_pdfs`, default off) since it pulls third-party
  content; when off, still capture the URL as metadata so it's retrievable.
- **Reuse:** these become `source_type="pdf_attachment"` records keyed by a
  stable id (hash of the URL, since there is no `file--file` uuid), fingerprinted
  on the node's `changed` mark — same delete-reconcile behaviour as R-none / the
  current attachment path. No new download/extract code needed.
- **Note:** R4 (keeping `<a href>` in body text) and R7 are complementary — R4
  keeps the link *mentioned* in the node's own text; R7 ingests the *content* of
  the linked PDF as its own document.

### R6 — Skip permanently (no action)

`products`, `recommendations`, `simplenews_issue`, `migrate_example_beer`
(empty/junk); the label-only taxonomies in §5.3; nav/footer/comments in §6.4.

**Suggested order:** R7 → R1 → R2 → R4 → R3 → R5.
(R7 first — highest content value; R4 pairs naturally with it.)

---

## 8. Implementation

Delivered on branch `feat/drupal-coverage-inbody-pdfs`. All changes verified
against the live JSON:API (no DB required for the extraction-layer checks).

**Files changed**

- `app/config.py` — new settings:
  - `drupal_ingest_external_pdfs: bool = False` (R7 external gate)
  - `drupal_block_min_chars: int = 200` (R3 boilerplate filter)
- `app/ingestion/extractors/drupal_extractor.py`
  - `DEFAULT_BUNDLES` += `carousel` (R2); new `DEFAULT_TAXONOMIES`
    (`themes`, `extra_pages`, `regional_centre`) and `DEFAULT_BLOCKS` (`basic`).
  - `iter_bundle_records` / `iter_node_uuids` / `_discover_relationship_fields`
    take an `entity_type` param → fetch `/{entity_type}/{bundle}` (R1/R3).
  - `_build_record` — title falls back to `name`/`info`; tags
    `entity_type` in metadata for non-node records; harvests in-body PDFs.
  - `_iter_rich_text` + `_extract_inbody_pdfs` (R7) — scan **all** rich-text /
    long-string fields for `<a href>` and bare `.pdf` URLs; internal → ingest,
    external → gated. Synthetic URL-stable uuid `inbody:<sha1>`.
  - `_resolve_files` — warns on skipped doc attachments (docx/xlsx/pptx…) (R5).
  - `DrupalFile.origin` field ("attachment" | "inbody").
  - `_TextExtractor` (R4) — keeps `<a href>` URLs, `[image: alt]`,
    `[embedded: src]`, and `|`-separated table cells.
- `app/ingestion/change_detection.py`
  - Source list = node bundles (incremental) + taxonomy + block sources
    (full-fetch). Per-run dedup of in-body PDFs; in-body PDFs fingerprinted on
    their URL (ingest-once), attachments on the node's changed mark. Boilerplate
    blocks below `drupal_block_min_chars` (with no PDF) are skipped. Delete
    reconciliation restricted to node bundles.

**Verification (live, 2026-07-03)**

- R4: unit-checked link/img/iframe/table handling.
- R7: policy_brief in-body PDFs harvested (e.g. `TOWARDS-CLEANER-FREIGHT…pdf`);
  external gated off; internal downloads confirmed `application/pdf`.
- R1/R2/R3: `themes` 35, `extra_pages` 9 (+1 PDF), `regional_centre` 5,
  `block_content/basic` 73 kept + 44 in-body PDFs (18 boilerplate dropped),
  `carousel` 2.
- Regression: real `file--file` attachments still resolve (report 8,
  policy_brief 5) alongside in-body PDFs.

**Known limitations / notes**

- R4's richer body text changes content, but article fingerprints are the Drupal
  `changed` timestamp, so existing docs only pick up the improvement on their
  next Drupal edit or a **full re-index** (fresh state). New/changed content
  gets it immediately.
- In-body PDFs are re-fetched only if their URL changes (URL-stable
  fingerprint), not if the target PDF's bytes change under the same URL.
- `carousel` items have no body → title-only docs (0 chunks); harmless.

**Operational follow-up (not code):** run a full re-index so the ~1,143 in-body
PDFs, taxonomy/block content, and R4 body improvements populate Qdrant. External
PDF ingestion stays off unless `drupal_ingest_external_pdfs=true`.

---

## 9. Thematic areas — coverage verification (2026-07-03)

Follow-up check: are TERI's thematic areas and their details fully captured by
the changes above? **Yes** — the term descriptions, the parent→child hierarchy,
and the theme↔content associations (including `news`) are all captured. Only
theme banner images and SEO metatags are intentionally skipped.

### Captured

- **All 35 theme terms** (`taxonomy_term/themes`, all published — none skipped),
  organised as 16 top-level areas with sub-themes:
  - **Energy** → Electricity & Renewables, Energy Access, Energy Assessment &
    Modelling, Energy Efficiency
  - **Environment** → Air, Forest & Biodiversity, Land, Microbes, Waste, Water
  - **Sustainable Habitat** → Buildings, Cities, Transport
  - **Resources & Sustainable Development** → Centre for Sustainable Development
    Research, Resource Efficiency & Governance
  - **Environment Education** → Education for Youth Empowerment, Strategic
    Communication for Sustainability
  - **TERI Knowledge Resource Centre** → Knowledge Products & Services, Knowledge
    Repositories & Information Centre, Skill Development & Awareness,
    Sustainability Driven Knowledge Projects
  - **Standalone:** Climate Change, Sustainable Agriculture, Corporate Social
    Responsibility, Environment & Public Health, Green Shipping, Himalayan Centre
    Nainital, TERI Council for Business Sustainability, World Sustainable
    Development Summit
- **Each theme's full `description` prose** (286–1027 chars each) — ingested as
  body text; it is the only content field on a theme term.
- **Theme → content associations.** Content nodes tag their theme(s) via
  `field_*_theme` relationships, which we resolve into `categories` metadata:
  `article`→`field_theme`, `research_papers`→`field_rpaper_themes`,
  `policy_brief`→`field_policybrief_theme`, `events`→`field_event_theme`,
  `feature_articles`→`field_farticle_theme`,
  `completed_projects`→`field_completed_theme`,
  `ongoing_projects`→`field_ongoing_theme`, `news`→`field_news_themes`. Verified
  end-to-end (e.g. a research paper resolves to `Forest & Biodiversity, Land,
  Environment`).
- **Theme hierarchy (parent → child).** The taxonomy `parent` relationship is
  captured (`include=parent`) and a sub-theme's parent area is indexed as a
  `category`, so e.g. "Air" is retrievable under "Environment". Top-level terms
  have no parent.
- **The content under each theme** — the articles/events/papers a theme page
  lists are the individual node documents we already ingest. Theme pages are
  Drupal Views (description + grouped lists), so nothing unique to the page is
  lost.

### Missing (ranked)

1. **Theme banner images** (`field_theme_image`) — not captured (intended;
   images are not text).
2. **Theme SEO `metatag`** — not captured; typically a shortened duplicate of the
   description, so no real content loss.

> **Corrected 2026-07-07** (via `app/local_tests/thematic_areas_test`): two items
> previously listed here are resolved. *Theme hierarchy* is now captured (see
> above). And `news` **is** themable — it carries `field_news_themes` and
> resolves into `categories` — correcting the earlier "news has no theme field"
> finding; the field exists on the live site.

---

## 10. Change Log

| Date | Change | Recs | Commit |
|---|---|---|---|
| 2026-07-03 | Initial analysis documented. No code changes yet. | — | — |
| 2026-07-03 | Added §6.4 + R7: in-body PDF links (698 URLs, ~10% of nodes) confirmed missed and fetchable. | R7 | — |
| 2026-07-03 | Full Drupal sweep: **1,096** PDF URLs in nodes (528 nodes) + 46 in blocks + 1 in taxonomy ≈ **1,143 total**. Links also in `field_*` text (not just `body`). R7 scope widened to all rich-text fields + blocks + taxonomy. | R7 | — |
| 2026-07-03 | Implemented R1–R5 + R7 on `feat/drupal-coverage-inbody-pdfs`; verified live. See §8. | R1–R5,R7 | `63b7f2e` |
| 2026-07-03 | Added §9: thematic-areas verification — all 35 themes + descriptions + associations captured; gaps = news has no theme field, theme parent/child tree & images not stored. | — | — |
| 2026-07-07 | Captured taxonomy `parent` → theme hierarchy preserved; sub-theme parent area indexed as a `category`. Corrected §9: `news` **is** themable (`field_news_themes`). Added `app/local_tests/thematic_areas_test`. | — | — |
| 2026-07-29 | Theme hierarchy moved onto the rows themselves: `documents_theme` gained `theme_type` (primary tag / sub-theme) + `parent`, classified from `app/data.json`. Supersedes the 2026-07-07 row's "parent area indexed as a `category`" — a parent is now a reference, not an extra theme. Themes narrowed to theme-vocabulary refs, so `field_*_division`/`_area` no longer land in `categories`. | — | — |
