# Drupal JSON:API Data Fetching

This folder fetches all TERI website content from `https://teriin.org/jsonapi`
in a clean, reusable way — each node comes back with its **related data already
resolved** (themes, tags, authors, regions, attached PDFs), so it's ready to
feed straight into the RAG ingestion pipeline.

```
drupal/
├── fetch.py     # fetch_nodes(content_type, status) — the one function you call
├── __init__.py
└── README.md    # this file
```

---

## Quick start

```python
from drupal.fetch import fetch_nodes

# Every published feature article, with themes/tags/authors resolved, fully paginated:
articles = fetch_nodes("feature_articles", status=1)

print(len(articles))
print(articles[0]["title"])
print(articles[0]["related"]["field_farticle_theme"])   # -> [{'name': 'Environment', ...}]
```

Or from the command line for a quick look:

```powershell
venv/Scripts/python.exe -m drupal.fetch report 1
```

---

## What each returned node looks like

`fetch_nodes` returns a **list of flat dicts**. Each node has its own fields at
the top level, plus a `related` dict holding the fully-resolved related entities:

```jsonc
{
  "id": "c64a037a-...",                 // JSON:API UUID
  "type": "node--report",
  "drupal_internal__nid": 8396,         // the numeric nid (matches the DB)
  "title": "Sustainability Super Trends 2018",
  "status": true,
  "created": "2018-12-10T09:45:01+00:00",
  "changed": "2018-12-19T08:22:03+00:00",
  "body": {
    "value": "<p>...raw HTML...</p>",
    "processed": "<p>...rendered HTML...</p>",   // use this, then strip tags
    "summary": ""
  },
  "field_report_date": "2018-03-06T...",
  "related": {
    "field_report_theme":   [ { "id": "...", "name": "Sustainable Development" } ],
    "field_report_tags":    [ { "id": "...", "name": "CSR" }, { "name": "..." } ],
    "field_report": [                                  // an attached PDF (file--file)
      { "filename": "sustainability-trends-2018-report.pdf",
        "filemime": "application/pdf",
        "uri": { "url": "/sites/default/files/2018-12/...report.pdf" } }
    ]
  }
}
```

> The `related` keys are whatever `field_*` relationships that content type has —
> they differ per type (`field_farticle_theme` for articles, `field_report_theme`
> for reports, etc.). `fetch.py` discovers them automatically, so you never have
> to hard-code field names.

---

## How it works (3 mechanics)

### 1. Related data (`include`)
Drupal returns a node's own fields directly, but relationships come back only as
`{type, id}` references. We add `?include=field_a,field_b,...` so the server
ships the full related records in a top-level `included` array. `fetch.py` then
stitches those back onto each node under `related`. The include list is built
automatically by sampling one node and taking all its `field_*` relationships.

### 2. Pagination
Drupal **hard-caps page size at 50** records. Asking for more is silently
ignored. The fetcher follows the `links.next` cursor in each response and keeps
requesting until there's no `next` link, accumulating every page. **This is the
#1 cause of "missing data" — never read just the first response.**

### 3. Status filter
`status=1` adds `filter[status][value]=1` (published), `status=0` filters to
unpublished, `status=None` removes the filter. (See the auth note below.)

---

## Attached files (PDFs / images) — the bridge to the PDF pipeline

Content types like `report`, `research_papers`, `policy_brief`, and
`press_release` attach PDFs. These resolve under `related` as `file--file`
entities. The file URL is **relative**, so prepend the host to download it:

```python
HOST = "https://teriin.org"
file_url = HOST + node["related"]["field_report"][0]["uri"]["url"]
# -> https://teriin.org/sites/default/files/2018-12/...report.pdf
```

This is how the "two data sources" (MySQL/Drupal text **and** PDFs) actually
converge: the PDFs are attached to Drupal nodes. Download these URLs and run
them through the existing PDF extractor in `app/services/extraction.py`, using
the node's title/theme/tags as metadata.

---

## ⚠️ Fetching unpublished content (`status: 0`)

Your type list includes many `status: 0` (unpublished) entries. **Anonymous
JSON:API requests only ever return published content** — an anonymous
`fetch_nodes(type, status=0)` returns an empty list. To read unpublished nodes
you must authenticate as a user with "view unpublished content" permission.
Once we have credentials, add one of these to `HEADERS`/the request in `fetch.py`:

- **Basic auth** (if the `basic_auth` module is on): `requests.get(url, auth=(user, pass))`
- **OAuth bearer** (if `simple_oauth` is on): `Authorization: Bearer <token>`
- **Session cookie** from a logged-in login request.

**Action needed:** confirm which auth method the site supports and provide a
service-account credential before we crawl the `status: 0` types.

---

## The plan: fetching ALL types with pagination

The full target set (from `data`), with the published counts we measured in the
DB for reference:

| Content type         | published | also need unpublished? |
|----------------------|----------:|:----------------------:|
| `news`               |     1,584 | yes |
| `feature_articles`   |     1,476 | yes |
| `completed_projects` |     1,157 | yes |
| `events`             |     1,072 | yes |
| `press_release`      |       702 | yes |
| `research_papers`    |       623 | yes |
| `ongoing_projects`   |       581 | yes |
| `article`            |       455 | yes |
| `policy_brief`       |       238 | yes |
| `videos`             |       215 | yes |
| `page`               |       128 | yes |
| `infographics`       |        45 | (published only) |
| `services`           |        29 | yes |
| `people`             |         8 | yes |
| `report`             |         8 | (published only) |
| `carousel`           |         2 | (published only) |
| `products`           |         0 | unpublished only |
| `recommendations`    |         0 | unpublished only |

Each `(type, status)` pair is fetched independently, each fully paginated. One
URL per content type returns that type's nodes **with all related data** — there
is no single URL across all types, because every bundle is its own endpoint with
its own field names.

```python
from drupal.fetch import fetch_nodes

data = [
    {"type": "news", "status": 1},
    {"type": "feature_articles", "status": 1},
    # ... the full list ...
    {"type": "recommendations", "status": 0},
]

all_content = {}
for entry in data:
    key = f"{entry['type']}__status{entry['status']}"
    nodes = fetch_nodes(entry["type"], status=entry["status"])   # paginated internally
    all_content[key] = nodes
    print(f"{key}: {len(nodes)} nodes")
```

> Published types work today. The `status: 0` rows return nodes only after the
> auth step above is in place.

---

## Future roadmap

1. **Auth for unpublished** — wire a service-account credential into `fetch.py`
   so `status=0` returns data (see warning above).
2. **Download + extract attached PDFs** — for each node with a `file--file`
   relationship, fetch the URL and run it through `app/services/extraction.py`.
3. **Map nodes → LangChain `Document`s** — body/full-text/summary as
   `page_content`; title, type, nid, themes, tags, region, date, source URL as
   `metadata`. Feed into the existing `ingest`/`vector_store` pipeline.
4. **Skip duplicates** — ingest from current data only; the `node_revision__*`
   and `old_*` tables/revisions are stale copies (we confirmed this when
   searching the DB).
5. **Incremental sync** — add `&sort=-changed` and stop once records are older
   than the last crawl, so re-runs only pull new/updated content.
6. **Cache raw JSON** — persist each fetch to disk so re-ingestion doesn't
   re-crawl the site.
