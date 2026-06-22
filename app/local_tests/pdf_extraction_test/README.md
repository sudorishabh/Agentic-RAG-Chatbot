# PDF extraction test

Runs the full PDF extraction flow over the sample corpus in `../../../pdf_examples`
and writes a categorised result folder per PDF — all output stays inside this
directory under `results/`.

Flow exercised:

```
extract_pdf(bytes, name)  ->  ExtractionResult   (pypdfium2 classify -> text / Azure DI OCR)
chunk_pdf(result)         ->  list[Chunk]         (canonical doc -> hierarchical chunks)
```

## Run

```bash
# every PDF in ./pdf_examples
python -m app.local_tests.pdf_extraction_test.run

# only specific files (bare names resolve inside pdf_examples, or pass full paths)
python -m app.local_tests.pdf_extraction_test.run managing-water.pdf ES2012RS02.pdf
```

## Output layout

```
results/
  _index.md            run overview table across all PDFs
  _index.json          same, machine-readable
  <pdf-slug>/
    00_summary.txt     headline stats + digital/OCR route breakdown
    00_summary.json
    01_pages.md        page-by-page extracted text
    02_tables.md       every table (markdown) with page + caption
    03_chunks.md       chunking output (parents + children)
    full_text.md       full concatenated extracted text
    ERROR.txt          present only if that PDF failed (with traceback)
```

`results/` contents are git-ignored. A failure on one PDF is recorded in its
own `ERROR.txt` and does not stop the rest of the run. Scanned-page OCR needs
Azure Document Intelligence configured; without it those pages are reported as
empty (the run still completes).
