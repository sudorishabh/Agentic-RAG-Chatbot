# Thematic-areas / non-node extraction test

Focused probe for the content that is **not** a Drupal node — above all the
**Thematic Areas** mega-menu (`taxonomy_term/themes`) — and a blunt answer to
*"is this actually captured, and what's still in doubt?"*

The sibling `drupal_extraction_test` covers node bundles. This one covers only:

```
taxonomy_term/themes          the "Thematic Areas" menu (Energy, Environment, …)
taxonomy_term/extra_pages     CSR, Energy Transitions, HFCs, … landing pages
taxonomy_term/regional_centre regional-centre descriptions
block_content/basic           homepage / section highlight blocks
```

## What it checks

| # | Check | Answers |
|---|-------|---------|
| 1 | Schema / silent-skip probe | Do `sort=-changed` & `filter[status]=1` 400 for these resources? (a 400 → `change_detection`'s broad `except` silently skips the whole bundle) |
| 2 | Thematic-areas extraction | Does `taxonomy_term/themes` return terms with real description prose? |
| 3 | Menu ↔ taxonomy coverage | Is every "Thematic Areas" menu label backed by a fetched term? |
| 4 | Hierarchy gap | The menu is a tree (Energy › …). Do we keep the parent→child link or flatten it? |
| 5 | Downstream ingestability | Do these records survive canonical + chunking into retrievable chunks? |
| 6 | Block boilerplate filter | `block_content/basic`: how many survive `drupal_block_min_chars`? |
| 7 | Theme→content association | Do content nodes carry their theme(s) in `categories`? (and confirm `news` doesn't) |
| 8 | Change-detection wiring + delete reconciliation | End-to-end (DB-free): does `detect_drupal_changes` **emit** these as `website` docs, and **purge** a stale theme when `reconcile_deletes=True`? |

Each check returns `✅ PASS` / `🟡 WARN` / `🟠 DOUBT` / `🔴 FAIL`.

## Run

```bash
python -m app.local_tests.thematic_areas_test.run

# smaller association sample (records per content bundle; default 5)
python -m app.local_tests.thematic_areas_test.run --limit 3
```

Hits the **live** JSON:API (`DRUPAL_JSONAPI_BASE`, default teriin.org).
**No MySQL / Qdrant / Azure needed** — check 8 stubs the state store and empties
the node bundles so it runs DB-free over only the non-node sources.

## Output (git-ignored, under `results/`)

```
results/
  report.md      verdict summary + a "What is in doubt" section + full detail
  report.json    the same, machine-readable
  themes.json    every fetched theme term (name, url, body chars, metadata keys)
  blocks.json    every fetched block (body chars + PDF links)
```

Start with `report.md` → the **"What is in doubt / needs attention"** section is
the direct answer to "which things are uncertain."
