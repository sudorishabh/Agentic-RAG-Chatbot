# Date correction: what to run on your own machine

Pulling this branch gives you the **code**. It does not give you the corrected
**data** — that lives in whoever ran it. This is the four commands that apply it
to your own MySQL and Qdrant, and why each one exists.

Nothing here downloads a PDF or calls Azure Document Intelligence. The whole
sequence is minutes and costs nothing.

---

## Why any of this is needed

For a website document, `published_at` was always the CMS record's **creation
stamp** — when someone typed the record into Drupal. That is why 646 completed
projects, 369 events, 367 news items and 335 research papers each share one
timestamp *to the second*: they are import batches, not publications. 3,409
documents (28% of the corpus) sit inside the Dec 2017 – Jan 2018 migration
window across only 85 distinct timestamps.

Meanwhile Drupal states the real date in its own fields — `field_news_date`,
`field_pressrelease_date`, `field_rpaper_year`, `field_report_date` — and nothing
read them. **1,436 documents were wrong by 1 to 8 years**, concentrated at +3 to
+5. Press releases from 2012 reading as 2018. Research papers from 2016 reading
as 2020.

Verified against the rendered pages before anything was changed: 25 of 25 in one
sample, 8 of 8 on the riskiest single-day shifts, 7 of 7 on the year-only ones.
The corroboration is that the site itself displays exactly these values, and the
event dates in the titles line up — COP-21 → Nov 2015, Earth Day → April, 9th
GRIHA Summit → Dec 2017.

`published_at` is what every ranking, filter, ordering and recency path reads. So
this is not cosmetic: on an uncorrected corpus, "papers from 2016" misses them and
recency ranks them as years newer than they are.

---

## What the code gives you, and what it does not

| | Comes with the code? |
| --- | --- |
| The column definitions, the scripts, the tests, the audit tool | **yes** |
| The corrected dates | **no** |
| The provenance labels | **no** |
| The Qdrant precision markers | **no** |

Two things *do* happen on their own once you have the code:

* **The new columns appear by themselves.** `pipeline.py` calls
  `state.ensure_table()` at the start of every ingestion, so your first sweep adds
  them. Nothing to remember.
* **Any document a sweep re-ingests gets the right date**, with no script —
  `canonical._drupal_document` now consults the resolver.

That second one is not enough on its own, and it is worth understanding why. The
crawl window is `changed >= MAX(changed_mark)` per bundle, so a press release last
edited in 2012 sits outside every window forever, however many sweeps run. **The
backfills exist precisely to reach the documents the crawl will not.**

---

## Run these, in this order

### 1. Add the columns

```bash
python -c "from app.catalog import schema; schema.ensure_state_table()"
```

Two nullable columns — `published_at_source` and `published_at_precision` —
recording where each date came from and how precise it is. Idempotent, changes no
row, makes no network call. Skip it only if you are about to run an ingestion
anyway, which does the same thing first.

Until they exist, the backfills below refuse cleanly (the `UPDATE` raises before
any commit and before Qdrant is touched, so there is no partial state), and
`verify_corpus` reports the date checks as *skipped* rather than failed.

### 2. Take your own baseline

```bash
python -m scripts.audit_dates --json reports/dates/baseline.json
```

This is the "before" snapshot that step 5 diffs against, and it is what makes the
change reviewable rather than asserted.

**Do not copy someone else's snapshot.** `reports/dates/*.json` is gitignored for
exactly this reason: a baseline from a different corpus would report your normal
state as a regression.

### 3. Correct the dates

```bash
python -m scripts.backfill_source_dates                       # dry run
python -m scripts.backfill_source_dates --apply --expect <N>
```

The dry run writes nothing and prints the full diff: how many documents move, by
bundle and by source field, the shift distribution, **every document that moves
*later* listed individually** (those are the ones worth eyeballing), and the
largest corrections.

Read that before applying. Then pass `--expect <N>` with the number the dry run
showed.

> **The pre-flight will refuse if the count differs from `--expect`.** That is the
> check working, not a failure. Your number will not be 1,047 or 389 — it depends
> on when your corpus was ingested and what it holds. Re-read your own dry run and
> pass your own figure.

It also refuses if a value is not stored as UTC, if a year-precision value is not
1 January, or if a field that is not a publication date reached the move list.

What it does: `UPDATE documents`, `set_payload` on Qdrant, a decision row per
document, and **drops the semantic cache**. That last one matters — the cache's
partition key is `retrieval settings + top_k + answer_format + corpus revision`,
and the corpus revision is `MAX(indexed_at) + COUNT(*)`, neither of which a date
correction moves. Without the drop, a question asked in the previous 24 hours
replays its old answer with the old date, because the cache is consulted *before*
retrieval.

Afterwards it prints invariants that must be identical — the PDF date checksum
above all, since PDFs are out of scope and one moving would mean the scoping
failed.

### 4. Record where every date came from

```bash
python -m scripts.backfill_date_provenance          # dry run
python -m scripts.backfill_date_provenance --apply
```

Moves no dates — it asserts a checksum over `published_at` for all 12,003
documents and fails if even one changes. It only fills in the two provenance
columns:

* `created` — the record's own creation stamp (for an attachment, its parent
  page's)
* `cms_field` — the publisher states this date
* `document_text` — the PDF's own text stated it, quoted and verified

**Run it after step 3, not before.** It also relabels rows whose stored label
disagrees with what ingestion would now write — and if the dates have not been
corrected yet, that comparison is against the wrong values. Reversing the order
leaves the labels stale in a way that is easy to miss: it under-reports the
documents the publisher corroborates by about a third.

### 5. Check the result

```bash
python -m scripts.audit_dates --compare reports/dates/baseline.json
python -m scripts.verify_corpus
```

The comparison exits non-zero if a **defect** count rose, while letting
descriptive counts move freely — "3,409 documents are migration-dated" is expected
to fall, and that is not a regression.

Expect `source_field_disagrees_total` to drop by exactly the number of documents
you corrected, `documents_in_migration_window` and
`documents_on_a_crowded_timestamp` to fall, and `documents_with_own_timestamp` to
rise.

`verify_corpus` should report four date checks at zero:

```
OK   date_provenance_unrecorded    0
OK   stated_date_not_applied       0
OK   undeclared_source_date_field  0
OK   year_precision_not_january    0
```

`stated_date_not_applied` is the one to watch afterwards. It is non-zero if a
sweep did not apply the rule, or if something overwrote a corrected date —
specifically `app.ingestion.backfill`, which lifts `published_at` out of chunk
payloads and writes it back with a bare `SET`. That is the silent revert path that
wiped an earlier backfill, and this check is what makes it visible.

---

## Optional: check your corpus against the live site

```bash
python -m scripts.scrape_site_dates --fetch   # one JSON:API pass, no PDF bodies
python -m scripts.scrape_site_dates           # compare
```

Classifies every document as *agrees with what the site states*, *carries the
site's page/record stamp*, or *contradicts the site*. The third should be zero.

Useful as an independent second opinion, since it derives the expected date from
the live site rather than from your own `raw_meta`.

---

## What this does not fix

Worth knowing so the result is not oversold. After the full sequence, roughly
**23% of dates are verified** — someone stated them and we store that. The rest:

* **~9,200 carry a record or page stamp.** Nothing states a publication date for
  them. Many are fine (a news item written and posted the same day); ~2,400 are
  import-batch stamps and are wrong, with the right answer nowhere in the data.
* **1,400 PDFs share a page with other PDFs**, so they inherit the page's date.
  This is the annual reports: Drupal genuinely gives one date for all ten
  editions and has no per-PDF date field at all. Being faithful to that source is
  not the same as being right.
* **30 dates are provably wrong** — a document reporting on FY 2024-25 dated
  before 2024. Correct by the resolver's rules, which refuse to turn a reporting
  period into a publication date, and factually wrong. Fixing them needs a
  decision about using an edition as a lower bound.
* **896 PDFs share their page's title** — 43 documents all called "Brochures".
  The link text that would fix this exists on the live site and the code that
  reads it is fixed; the data is stale. Needs a re-sweep, which is the only
  remaining step that costs extraction money.

`documents.document_published_at` is deliberately left empty.

---

## Two things not to do

**Do not run a sweep before the backfill** on a corpus you care about measuring.
The sweep corrects the documents it touches and leaves the rest, which is not
corrupt and does converge — but it leaves you unable to tell what the backfill
changed.

**Do not run `python -m app.ingestion.backfill`** (the payload-lift tool) after
correcting dates unless you mean to. It reads `published_at` out of chunk payloads
and writes it back with a bare `SET`, and it clears the provenance columns when it
does. Harmless if both stores agree, a revert if they do not.
