# PDF Extraction

How the ingestion pipeline turns a PDF into clean, structured **Markdown** —
tables, figures and all — ready for [`chunker.py`](../app/ingestion/chunker.py).
The implementation lives in
[`app/ingestion/extractors/pdf_extractor.py`](../app/ingestion/extractors/pdf_extractor.py).

## Pipeline

```
extract_pdf(content: bytes, filename: str)
        │
        ▼
  classify each page (pypdfium2): has a real text layer?  ──► digital
                                  image-only / empty?      ──► scanned
        │
   ┌────┴───────────────────┐
   ▼                        ▼
 DOCLING                  AZURE DOCUMENT INTELLIGENCE
 (digital pages)          (scanned pages · prebuilt-layout)
 • layout + reading order • OCR text
 • TableFormer tables     • table structure
 • figure crops           • Markdown output
        │                        │
        └───────────┬────────────┘
                    ▼
   per-page Markdown ( ## headings · | tables | · figure placeholders )
   + extracted figure image files + AI vision captions
                    ▼
   ExtractionResult ──► chunk_pdf() ──► embed ──► Qdrant
```

The chunker is already **Markdown-aware** — it splits on `#` headings and keeps
`|`-delimited tables and code blocks atomic. Emitting Markdown is exactly what
lets tables and document structure survive into the chunks and citations.

## Why two engines

|                       | Digital PDF (born-digital)                                       | Scanned PDF (images)                                  |
| --------------------- | --------------------------------------------------------------- | ---------------------------------------------------- |
| Has a text layer      | yes                                                             | no                                                   |
| Best tool             | **Docling**                                                     | **Azure Document Intelligence**                      |
| Why                   | local, free, strong layout + TableFormer tables + figure crops  | cloud OCR that also recovers table structure (`prebuilt-layout`) |

A **mixed** PDF (mostly digital with a few scanned pages) uses Docling for the
digital pages and falls back to Azure OCR for the scanned ones, page by page.

---

## 1. Install

Docling pulls a large dependency tree (PyTorch, transformers, OpenCV, pandas …) —
expect **~2–3 GB** and a few minutes.

```powershell
# from the repo root, with the project venv active
pip install -r requirements.txt
```

The new lines in `requirements.txt`:

```
docling                        # digital-PDF structure: layout, tables, figures
azure-ai-documentintelligence  # OCR + layout for scanned PDFs
pypdfium2                      # per-page text probe + rasterisation
```

> **Python 3.14 note.** This repo runs on Python 3.14. Docling 2.102 and its
> heavy deps (torch 2.12, pandas 3, scipy, pillow 12, lxml 6 …) all ship native
> `cp314` wheels, so `pip install` needs no compiler. The same command also works
> on older Pythons if you ever switch.

### CPU vs GPU

Out of the box you get the **CPU** build of PyTorch, which is fine for
ingestion-scale PDF processing. For an NVIDIA GPU, install the matching CUDA build
of torch *before* installing the rest:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

Docling auto-detects and uses the GPU when torch sees one.

---

## 2. Docling models — the local setup

Docling runs two ML models **locally** at extraction time:

- a **layout** model — detects titles, paragraphs, tables, figures, reading order;
- **TableFormer** — recovers table row/column structure.

### First run (online) — zero config

The first time you convert a PDF, Docling downloads these models from Hugging
Face (the `ds4sd/*` repos) and caches them on disk. If the machine has internet,
it just works. The cache lives at:

```
%USERPROFILE%\.cache\huggingface\hub      (default)
%HF_HOME%\hub                             (if HF_HOME is set)
```

### Pre-fetch / offline (air-gapped) setup

To skip the first-run download — or to run with no internet — pre-download the
models once, then point the extractor at them.

**Option A — Docling CLI** (installed with the `docling` package):

```powershell
docling-tools models download
```

It prints the directory the models were written to. Put that in `.env`:

```
DOCLING_ARTIFACTS_PATH=C:\path\printed\by\the\command
```

**Option B — Python** (use if the CLI isn't on PATH):

```python
from docling.utils.model_downloader import download_models
print(download_models())     # downloads, then returns the artifacts directory
```

**For a fully offline host**, also stop Hugging Face from phoning home:

```powershell
$env:HF_HUB_OFFLINE = "1"     # models are already local; this just enforces it
```

When `DOCLING_ARTIFACTS_PATH` is set the extractor passes it straight into
Docling's pipeline options, so no network access is needed during extraction.

### Verify

```powershell
python -c "from docling.document_converter import DocumentConverter; print('docling OK')"
```

---

## 3. Azure Document Intelligence — the OCR path

For scanned PDFs you need an Azure **Document Intelligence** (formerly Form
Recognizer) resource.

1. In the Azure Portal, create a **Document Intelligence** resource.
2. Copy its **endpoint** and a **key** into `.env`:

```
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=<key>
AZURE_DOCUMENT_INTELLIGENCE_MODEL=prebuilt-layout
```

- **`prebuilt-layout`** (recommended) returns text **and** table structure and
  can emit Markdown directly — that's how scanned **tables** survive.
- `prebuilt-read` is cheaper but text-only (no tables).

If these are left blank, scanned pages are **skipped** (and logged) rather than
failing the whole document.

---

## 4. AI figure captions (optional, on by default)

With `PDF_DESCRIBE_IMAGES=true`, each extracted figure is sent to your Azure
OpenAI **vision** deployment (`AZURE_OPENAI_*`, which must be a multimodal model
such as `gpt-5-mini`). It returns a one-line description that is embedded in the
Markdown next to the figure, so a query like *"the bar chart of emissions by
sector"* can retrieve it. Turn it off to save cost/latency:

```
PDF_DESCRIBE_IMAGES=false
```

---

## 5. Configuration reference

| Env var                                | Default                 | Meaning                                            |
| -------------------------------------- | ----------------------- | -------------------------------------------------- |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | —                       | DI resource endpoint (scanned PDFs)                |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY`      | —                       | DI key                                             |
| `AZURE_DOCUMENT_INTELLIGENCE_MODEL`    | `prebuilt-layout`       | DI model id (`prebuilt-layout` / `prebuilt-read`)  |
| `PDF_SCANNED_CHAR_THRESHOLD`           | `100`                   | fewer chars than this on a page ⇒ treat as scanned |
| `PDF_OCR_RENDER_DPI`                   | `300`                   | DPI when rasterising a page for OCR                 |
| `DOCLING_TABLE_MODE`                   | `accurate`              | `accurate` (better) or `fast` table structure      |
| `DOCLING_ARTIFACTS_PATH`               | —                       | local Docling model dir (offline)                  |
| `PDF_EXTRACT_IMAGES`                   | `true`                  | extract figures to disk                            |
| `PDF_IMAGE_DIR`                        | `data/extracted_images` | figure output root                                 |
| `PDF_IMAGE_MIN_PIXELS`                 | `64`                    | ignore figures smaller than this (max side, px)    |
| `PDF_DESCRIBE_IMAGES`                  | `true`                  | AI-caption each figure                             |
| `PDF_IMAGE_CAPTION_MAX_TOKENS`         | `256`                   | caption length cap                                 |

---

## 6. Usage

```python
from app.ingestion.extractors.pdf_extractor import extract_pdf
from app.ingestion.chunker import chunk_pdf

result = extract_pdf(pdf_bytes, "annual-report-2024.pdf")
print(result.page_count, "pages")
chunks = chunk_pdf(result)        # parent + child chunks, tables/figures preserved
```

A `python -m app.ingestion.extractors.pdf_extractor <file.pdf>` inspection CLI is
added in the final step.

---

## 7. Troubleshooting

- **First conversion is slow / downloads a lot** — that's the one-time model
  download (§2). Pre-fetch to avoid it.
- **Windows: "cache-system uses symlinks" warning** — harmless (the HF cache
  just uses more disk). Silence it with `HF_HUB_DISABLE_SYMLINKS_WARNING=1`, or
  enable Windows Developer Mode for symlink support.
- **`OSError` / Hugging Face errors with no internet** — set
  `DOCLING_ARTIFACTS_PATH` and `HF_HUB_OFFLINE=1` (§2).
- **Scanned tables come out as plain text** — set
  `AZURE_DOCUMENT_INTELLIGENCE_MODEL=prebuilt-layout` (not `prebuilt-read`).
- **Out of memory on large PDFs** — use `DOCLING_TABLE_MODE=fast`, or run on a
  machine with more RAM / a GPU.
