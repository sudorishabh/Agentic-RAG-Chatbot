# 05 — Extraction and Normalisation

**Purpose.** Turn source bytes — HTML fields, or a PDF file — into clean,
page-attributed plain text that a chunker can segment and an embedder can read.

**Inputs.** A `DrupalRecord` (for `website`), or PDF bytes plus a filename (for
`pdf_attachment`).

**Outputs.** For a website record, a flattened body string. For a PDF, an
`ExtractionResult`: one `PageContent` per page, each with text, an
`ExtractedVia` marker and any tables, plus routing metadata.

**Components.** `drupal_extractor._TextExtractor` (HTML),
`extractors/pdf_extractor.py` (the router and Azure DI),
`extractors/pymupdf_local.py` (classification and local text),
`extractors/camelot_tables.py` (tables), `extractors/text_normalize.py`
(cleanup).

---

## Website content

Covered in [02](02-sources-and-acquisition.md#html-to-text). In short: every
formatted-text field and every long `field_*` string is flattened by
`_TextExtractor`, which preserves link destinations as `text (url)`, image `alt`
as `[image: alt]`, iframe `src` as `[embedded: src]`, and table cells as
`|`-separated text. Body parts are joined with blank lines, `body` first.

There is no page structure, so the resulting `CanonicalDocument` has exactly one
section and `is_paginated` is false.

The rest of this document is about PDFs.

---

## The PDF extraction contract

```python
extract_pdf(content: bytes, filename: str) -> ExtractionResult
```

```python
@dataclass
class ExtractionResult:
    source: str
    pages: list[PageContent]      # 1-based page_number, in order, no gaps
    metadata: dict                # extraction_mode, route, page_signals

@dataclass
class PageContent:
    page_number: int
    text: str
    extracted_via: ExtractedVia   # OCR | TEXT | EMPTY
    tables: list[TableData]
```

Two guarantees the rest of the pipeline relies on:

- **Every page is present**, in order, even if empty. `_hybrid_extract` fills gaps
  with `PageContent(text="", extracted_via=EMPTY)` for `range(1, total + 1)`, so
  page numbers in citations are the real page numbers.
- **Tables reach the chunker through page text.** The chunker reads
  `page.text` and never the separate `tables` list, so a table page's text is
  `prose + "\n\n" + each table's markdown`. The `tables` list stays on the result
  for tooling and to derive the `has_table` payload flag.

---

## Mode selection

`extraction_mode` (default `hybrid`); an unrecognised value logs a warning and
falls back to `hybrid`.

| Mode | Behaviour |
| --- | --- |
| `local_only` | PyMuPDF text for every page. No OCR, no tables. Cheapest and fully offline. |
| `azure_only` | The whole document to Azure Document Intelligence; falls back to local text if Azure is unavailable. |
| `hybrid` | Classify every page once, then route **per page**. The default. |

### Hybrid routing

`classify_document(content)` opens every page once with PyMuPDF and produces a
`PageSignal` carrying `char_count`, `scanned`, `has_table` and — importantly —
**the extracted text itself**, so local and table pages never re-open the PDF just
to re-extract it.

```python
@property
def route(self):
    if self.scanned:  return "azure"    # Camelot cannot read an image
    if self.has_table: return "camelot"
    return "local"
```

| Condition | Route | Rationale |
| --- | --- | --- |
| `len(text) < pdf_scanned_char_threshold` (default 100) | `azure` | There is no text layer to read; only OCR can help. Scanned wins over table. |
| A table was detected | `camelot` | Table structure from the vector layer, merged with the page's prose. |
| otherwise | `local` | PyMuPDF text. |

If classification itself raises, the whole document is biased to Azure
(`_azure_with_fallback`), on the grounds that a PDF PyMuPDF cannot even open is
more likely to be an image than a text document.

### Table detection, three tiers

`_page_has_table(page, settings)`:

1. **PyMuPDF `find_tables()`** — the primary, reliable signal, handling both ruled
   and borderless tables. Always on. Exceptions are debug-logged and ignored.
2. **Ruled-grid heuristic** (`pdf_detect_ruled_grid`, **off**). Counts distinct
   horizontal and vertical ruling positions from `page.get_drawings()`, quantised
   to a 2pt grid, and requires `pdf_table_min_grid_lines` (3) on **both** axes.
   Requiring both is what keeps a header underline or a logo box from qualifying.
3. **Borderless heuristic** (`pdf_detect_borderless_tables`, **off**). Quantises
   word-start x-positions to a 5pt grid and requires at least
   `pdf_borderless_min_columns` (3) column positions each shared by at least
   `pdf_borderless_min_aligned_rows` (4) lines. Requiring multiple *internal*
   columns — not just a shared left margin — is what keeps ordinary prose out.

Both optional tiers default **off** because on heavily designed PDFs (banners, side
panels, page borders, multi-column text) they fire on nearly every page and
over-route everything to Azure. Enable them only for simpler corpora where biasing
harder toward Azure is worth the false positives.

### Diagram to include: per-page routing

A decision tree from "page" → `scanned?` → `has_table?` → three leaves (Azure OCR,
Camelot + PyMuPDF prose, PyMuPDF text), with a dashed fallback edge from each
non-local leaf back to "PyMuPDF text" labelled with what is lost (tables degrade to
plain text; scanned pages produce nothing). Alongside it, a small strip of pages
1..N coloured by route, showing that one document mixes all three.

---

## Azure Document Intelligence

`_ocr_pdf(content, page_numbers)`:

- Returns `{}` immediately if endpoint/key are unset, with a warning naming how
  many pages were skipped. That is the "Azure not configured" path, and it is not
  an error.
- Sends bytes via `AnalyzeDocumentRequest(bytes_source=content)`. `page_numbers`
  becomes a compact range string (`_page_range_str` collapses runs into
  `1-3,7`), so only the pages that need OCR are billed.
- Requests `output_content_format=MARKDOWN` **only for layout-style models** —
  `prebuilt-read` rejects the parameter and the whole call would fail. The check is
  `"layout" in model.lower()`.
- Any exception → `logger.exception` and `{}`. The caller degrades those pages to
  local text.

`azure_document_intelligence_model` defaults to `prebuilt-read`: OCR only, text
only, no table structure, cheap. `prebuilt-layout` costs roughly 6× more but also
reconstructs tables and document structure and supports Markdown output.

### Slicing DI output back into pages

`_pages_from_di(result, requested_pages)`:

- DI returns one combined `content` string plus per-page `spans`.
  `_slice_page_text` concatenates `content[offset : offset+length]` for each span.
- Special case: a single-page result with no usable spans falls back to the whole
  `content`.
- `<table>` HTML in the text is converted to pipe tables (`_html_tables_to_pipe` →
  `_HTMLTableParser` → `_rows_to_markdown`, honouring `colspan`).
- Tables are bucketed by the page number of their first bounding region. **Tables
  with no bounding region are kept on the first emitted page** rather than lost:
  bucketing them under page 0 silently dropped them, because pages are 1-based and
  nothing ever read that key. Placement is genuinely unknowable, so keeping the
  content on page 1 is the least-wrong option.
- A page with neither text nor tables is `EMPTY`; otherwise `OCR`.

---

## Camelot (born-digital tables)

`camelot_tables.extract_tables(content, page_numbers)` returns
`{page_number: [TableData, ...]}`, or `{}` if Camelot is not installed (with a
warning) or finds nothing.

Four non-obvious things happen here.

**1. A temp file, re-saved without encryption.** Camelot needs a path, so the
bytes are written to `tempfile.mkstemp(suffix=".pdf")` — and re-saved through
PyMuPDF with `encryption=fitz.PDF_ENCRYPT_NONE`. Plenty of PDFs ship with an owner
password that clears the "extract content" permission bit. PyMuPDF ignores that
flag — which is why classification still yields text — but Camelot's backend
enforces it and refuses the whole document. Dropping the encryption dictionary
keeps the tables reachable. If the re-save fails, the raw bytes are written
instead.

**2. Degenerate matches are dropped.** `_table_to_data` refuses anything with
fewer than 2 rows or fewer than 2 columns: the borderless `stream` flavor produces
those from ordinary prose.

**3. A second pass.** With the default `camelot_flavor="lattice"` (ruled tables,
needs Ghostscript), pages that produced nothing get a second pass with `stream`
for borderless tables.

**4. Windows temp-file cleanup.** `_remove_temp_pdf` tries `os.remove`, and on
`OSError` runs `gc.collect()` and retries. On Windows the first remove loses to
WinError 32 — Camelot's PDF backend leaves a document object holding an open
handle, released only on finalization — and without forcing the finalizers every
extracted page leaks a PDF into the temp dir. POSIX unlinks an open file happily,
so the retry never runs there.

A `PDFTextExtractionNotAllowed` is recognised specifically and logged as a warning
("the PDF forbids text extraction, so these pages fall back to local text");
anything else gets a full `logger.exception`. Either way the return is `{}` and the
page keeps just its PyMuPDF prose.

**Camelot is serialised** across the whole extraction by `_camelot_lock`, held for
the temp file's entire life rather than just `read_pdf` — the backend's objects
outlive the call and are torn down by the finalizers `_remove_temp_pdf` forces, so
the cleanup races too. See
[03, Sequential vs parallel](03-triggers-and-control-plane.md#sequential-vs-parallel)
for the crash this prevents.

---

## Stitching the result

```python
if azure_pages:  di = _ocr_pdf(content, azure_pages)
                 if di: pages_map.update(di); routes.append("azure")
                 else:  local_pages += azure_pages          # degrade
                        routes.append("azure_unavailable_local_fallback")

if table_pages:  tables_map = _camelot_tables(content, table_pages)
                 for n in table_pages:
                     merged = _merge_table_text(text_by_page[n], tables_map.get(n, []))
                 routes.append("camelot" if any tables else "camelot_empty_local_fallback")

if local_pages:  pages_map[n] = PageContent(text=text_by_page[n], ...)   # from classification
```

`result.metadata["route"]` is the `+`-joined list of routes actually taken, and
`result.metadata["page_signals"]` records which page numbers went where. Those two
fields are the audit trail for "why does this document read badly?" and are worth
checking first when a PDF's content looks wrong.

Note the degradation is always **downward and lossy but never fatal**: Azure
unavailable → those pages get PyMuPDF text (and any tables on them are lost);
Camelot finds nothing → the page keeps its prose.

---

## Page-text normalisation

`_normalize_result` runs two passes over the finished result, in place.

### Pass 1 — per page: `normalize_page_text`

In order:

| Step | What it does |
| --- | --- |
| `_repair_ligatures` | Literal ligature glyphs (`ﬁ`→`fi`, `ﬀ`→`ff`, …) plus ~40 hand-listed dropped-ligature words (`e cient`→`efficient`, `signi cant`→`significant`). Every listed broken form is non-lexical, so the replacement can never hit real text. Case of the first letter is preserved. |
| `_repair_subscripts` | Formula subscripts extraction mangled to commas: `MtCO,`→`MtCO2`, and `CO,`/`H,` **only** in front of a right-context only a formula carries (`CO, emissions`, `H, DRI`). A bare `CO,` is legitimate — carbon monoxide in a list — so each rule is anchored. |
| `_HTML_COMMENT` | Drops `<!-- PageBreak -->`, `<!-- PageNumber="22" -->`-style layout comments DI's Markdown leaves behind. |
| `_strip_figures` | Unwraps `<figure>…</figure>` to its inner content; empty ones disappear. |
| `_drop_garbage_tables` | Drops contiguous markdown-table blocks that are ≥6 columns wide and either ≥50% empty cells or ≥40% one repeated phrase — infographics and timeline graphics DI rendered as tables. Narrow tables are never garbage. |
| Dangling comment halves | A line containing `<!--` or `-->` after the comment regex ran is a comment split across a page break; dropped. |
| `_PAGE_NUMBER_BAR` | Drops single-cell rows holding only a page number, roman or arabic (`\| ii \|`). Real multi-cell rows are left alone. |
| `_is_number_soup` | Drops a line of ≥4 tokens that is ≥70% number tokens — chart axis labels. |
| `_drop_number_runs` | Drops contiguous *blocks* of bare-number lines, optionally interleaved with short category labels, when the block holds ≥4 bare numbers and is ≥40% numeric. This is the vertical bar/line chart case: an axis and its data with no prose. |
| Blank-run collapse | `\n{3,}` → `\n\n`. |

The last two are gated by `pdf_drop_number_soup` (default on).

`_is_chart_label` is what makes the block heuristic safe: a "label" is ≤28
characters, ≤4 words, does not start with `|`, and does not end in sentence
punctuation. So a real short list — which carries few or no bare numbers — is kept
while number-dominated chart soup goes.

### Pass 2 — document-wide: `strip_running_lines`

Removes running headers and footers: short lines repeated across most pages.

- No-op for documents under `min_pages` (4) or when
  `pdf_running_header_min_fraction` is `<= 0`.
- Candidate lines are non-blank, do not start with `|`, and are ≤12 words.
- Detection joins up to **3 consecutive** candidate lines into a **letters-only
  key** (`re.sub(r"[^a-z]", "", line.lower())`), keeping keys between 12 and 90
  characters. The joining and the letters-only key together absorb the fact that a
  footer fragments differently per page: `"…for Ma" + "ritime Application-"` on one
  page and `"…for M" + "aritime Application-"` on another produce the same key.
- A key appearing on `max(min_count=3, ceil(min_fraction * n))` pages is dropped
  from **every** page.
- **Plus a parity rule.** Print layouts routinely put a running head on one side
  only, so a recto-only footer cannot reach half of *all* pages — a 28-page booklet
  has 14 recto pages against a threshold of 14. So a key is also measured against
  its own recto/verso side, and qualifies at `side_fraction` (0.7) of that side —
  **but only when it is absent from the other side entirely**. Real page furniture
  alternates strictly; repeated body text lands on both sides.

### What normalisation deliberately does not fix

Font-specific Private-Use-Area glyphs and `(cid:N)` markers are **not recoverable
from the text layer** — the mapping lives in the embedded font — and are left
as-is. A PDF whose text layer is entirely PUA glyphs will produce mojibake, be
detected as non-empty, and index as garbage. That is a known gap; the detector for
it is a human reading the extracted text, or the date-resolution grounding checks
refusing to trust it (see [06](06-canonical-document-and-dates.md)).

---

## Validation performed at this stage

| Check | Where | On failure |
| --- | --- | --- |
| PDF opens | `_open` / `classify_document` | Whole document biased to Azure |
| Text layer has ≥ `pdf_scanned_char_threshold` chars | `classify_document` | Page routed to OCR |
| Azure is configured | `_di_client` | `{}` returned; pages degrade to local text with a warning |
| Model supports Markdown output | `_ocr_pdf` | Parameter omitted |
| Camelot importable | `extract_tables` | `{}` with a warning |
| Table has ≥2 rows and ≥2 cols | `_table_to_data` | Table dropped |
| PDF permits extraction | `_write_pdf` / `_run_flavor` | Encryption stripped; if still refused, a warning and local text |
| Extraction produced *something* | `pipeline._extraction_is_empty` | **`error` outcome — the previous version is kept.** See below. |

### The empty-extraction guard

This one lives in `pipeline.py`, not the extractor, and it is the most important
validation in the pipeline:

```python
def _extraction_is_empty(chunks):
    return not any(chunk.text.strip() for chunk in chunks)
```

Deliberately not merely `not chunks`: a chunk carrying only whitespace is the same
outcome reached by a different route — a body of non-breaking spaces, a PDF whose
text layer yields blank lines — and indexing it would replace real content with an
empty point just as surely.

When it fires, **nothing below it runs**. No embedding, no upsert, no delete, no
catalog write. The previous version keeps its vectors, its catalog row and its
`indexed_at`, and the retry marker written from the `error` outcome brings the
document back next run. The log line is explicit:

> %s (%s) extracted to nothing; keeping the previous version rather than replacing
> it with an empty one.

The reason recorded on the retry row is
`extraction produced no indexable content (N chunks); keeping version V`.

This is the "swap precondition": there must be something to swap *in*. An empty
extraction is a failure of *this run*, not a statement that the document is now
empty.

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| PDF is corrupt / not a PDF | PyMuPDF raises in `classify_document` | Whole document to Azure; if Azure also fails, local fallback returns nothing → empty-extraction error | Retry marker; fix or remove the source file |
| PDF is a pure scan, Azure unconfigured | `_di_client()` is `None` | Warning, pages degrade to local text, which is empty → empty-extraction error | Configure Azure DI, or accept the gap |
| Azure DI call fails or times out | `except` in `_ocr_pdf` | `logger.exception`, `{}`; those pages get local text | Next sweep retries the whole document |
| Azure DI returns tables with no region | `td.page_number is None` | Kept on page 1 | — |
| Ghostscript missing (lattice) | Camelot raises | `logger.exception`, `{}` for those pages; prose survives | Install Ghostscript, or set `camelot_flavor="stream"` |
| PDF forbids extraction | `PDFTextExtractionNotAllowed` | Warning; tables degrade to plain text | — |
| Camelot leaks temp files | Temp dir growth | `gc.collect()` + retry | Watch the temp dir on Windows |
| Camelot races under workers | Process crash (`0xC0000374`) | Prevented by `_camelot_lock` | `ingest_workers=1` if it recurs |
| Running-header stripper eats real content | A short repeated *body* line on most pages | The parity rule requires absence on the other side; the key length window (12–90) excludes very short lines | Lower `pdf_running_header_min_fraction`, or set it to 0 to disable |
| Number-soup stripper eats a real table | Table lines start with `|` and are excluded from `_is_chart_label`; `_is_number_soup` needs ≥70% numeric | — | Set `pdf_drop_number_soup=false` |
| PUA / `(cid:N)` text layer | Not detected | Indexed as garbage | Re-source the PDF; or route it to OCR by lowering nothing — this needs a manual `azure_only` run |

## Observability

- `Extracted %s: %d page(s), %d table(s); OCR on page(s) [...]` — one line per PDF.
- `result.metadata`: `extraction_mode`, `route`, `page_signals`
  (`{"pages": n, "azure": [...], "camelot": [...], "local": [...]}`).
- `%s routed to Azure but Azure is unavailable; falling back to local PyMuPDF text
  (tables on this document will degrade to plain text).`
- `Azure Document Intelligence is not configured; %s scanned page(s) skipped.`
- Span `ingest.extract` — the whole document build, aggregated as the
  `extraction` component in `/metrics/timings`.
- Reconciliation's `indexed_without_points` check catches documents that were
  stamped indexed while having nothing retrievable — the signature of the defect
  the empty-extraction guard now prevents.

### Inspecting one PDF by hand

```bash
python -m app.ingestion.extractors.pdf_extractor path/to/file.pdf -n 3 --full --chunk
```

Prints page count, table count, pages by extraction source, the OCR page list, the
first N pages' text, and — with `--chunk` — the parent/child counts the chunker
would produce. This is the first thing to run when a PDF's answers look wrong.

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `extraction_mode` | `hybrid` | `hybrid` / `azure_only` / `local_only`. |
| `pdf_scanned_char_threshold` | `100` | Below this many characters a page is "scanned". |
| `azure_document_intelligence_endpoint` / `_key` | `""` | Unset disables OCR entirely. |
| `azure_document_intelligence_model` | `prebuilt-read` | `prebuilt-layout` adds table structure and Markdown at ~6× the cost. |
| `camelot_flavor` | `lattice` | Primary flavor; `stream` is the automatic second pass. |
| `pdf_detect_ruled_grid` | `false` | Extra table tier. |
| `pdf_table_min_grid_lines` | `3` | Distinct ruling positions needed on both axes. |
| `pdf_detect_borderless_tables` | `false` | Extra table tier. |
| `pdf_borderless_min_aligned_rows` | `4` | Lines that must share columns. |
| `pdf_borderless_min_columns` | `3` | Internal columns needed. |
| `pdf_running_header_min_fraction` | `0.5` | Page share that makes a repeated line furniture. `0` disables. |
| `pdf_drop_number_soup` | `true` | Chart axis/data-region stripping. |

## Hand-off

The `ExtractionResult` goes to `canonical.from_pdf`, which becomes one
`CanonicalSection` per non-empty page with `page_start == page_end == page_number`
— and that page attribution is what makes citations resolvable. See
[06](06-canonical-document-and-dates.md).

---

Previous: [04 — Change Detection and Versioning](04-change-detection-and-versioning.md) · Next: [06 — The Canonical Document and Date Resolution](06-canonical-document-and-dates.md)
