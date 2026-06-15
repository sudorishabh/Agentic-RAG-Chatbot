# local_tests

Throwaway, run-by-hand harnesses for eyeballing what each ingestion stage
produces. Each runner reads a sample input, runs the real code, and writes a
human-readable `.txt` report into `outputs/`. None of them touch the network
except the PDF one (which calls the real extractor).

## Run

From the repo root:

```bash
python -m app.local_tests.test_canonical          # → outputs/canonical_result.txt
python -m app.local_tests.test_chunking           # → outputs/chunking_result.txt
python -m app.local_tests.test_pdf_extraction f.pdf   # → outputs/pdf_extraction_result.txt
```

`test_pdf_extraction` takes a PDF path; with no argument it uses the first
`*.pdf` in `./pdf_examples`. If a heavy/optional dependency or Azure config is
missing it records the error in the report instead of crashing.

## Layout

| Path                          | What it is                                              |
| ----------------------------- | ------------------------------------------------------- |
| `samples/sample_article.json` | Drupal `--json`-style dump (drives canonical + chunking)|
| `samples/sample_document.md`  | Structured multi-section doc (drives chunking)          |
| `test_canonical.py`           | source dict → `CanonicalDocument`                       |
| `test_chunking.py`            | `CanonicalDocument` → parent/child chunks + payloads    |
| `test_pdf_extraction.py`      | PDF → `ExtractionResult` → `chunk_pdf`                  |
| `outputs/`                    | generated `.txt` reports                                |
