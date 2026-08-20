# Grounded date resolution — final validation (2026-08-20)

## Scope note

This validation reads the **live** shadow decisions written by real ingestion runs between 2026-08-17 and 2026-08-20, rather than a re-run of the offline sweep. That is stronger evidence: the same code decided these in the production path.

**The targeted fix asked for is in place and enforced.** `statement_is_in_text` gates `safe_action()` in `app/ingestion/date_llm.py`, is set by `interpret()` alongside date grounding, and `app/ingestion/date_resolution.py` names it as a required gate.

## Corpus metrics (live)

| metric | value |
|---|---:|
| total PDFs with a decision | 3496 |
| keep_page_date | 3469 |
| review | 23 |
| **automatic overrides** | **4** |
| deterministic overrides | 0 |
| LLM overrides | 4 |
| PDFs read + sent to LLM | 234 |
| edition labels | 97 |

## Override audit — all overrides, none sampled

4 audited; **4 passed all eight checks**.

| filename | current | proposed | statement (verbatim in PDF) | checks |
|---|---|---|---|---|
| Chandigarh-Tribune-Chandigarh-Mond | 2018-01-09 | 2013-12-23 | `CHANDIGARHTRIBUNE CHANDIGARH | MONDAY | 23 DECEM` | 8/8 |
| Chandigarh-Tribune-Chandigarh-Tues | 2018-01-09 | 2013-12-24 | `CHANDIGARHTRIBUNE CHANDIGARH | TUESDAY | 24 | DE` | 8/8 |
| Tender_No_22 _Project_TERI_2024_De | 2018-04-11 | 2024-12-11 | `ISSUE NO. 22 DATED 11-12-2024` | 8/8 |
| Tender_NAM_Project_TERI_2023_Augus | 2018-04-11 | 2023-08-10 | `ISSUE NO. 01 DATED 10-08-2023` | 8/8 |

## Prior false positives, now rejected

| case | prior | now |
|---|---|---|
| The-Pioneer (print header laundered into a masthead) | override | **review** |
| Hindustan-Times (unreadable text layer) | override | **review** |
| Business-Standard (reformatted quote) | override | **review** |
| India-News-Calling | override | **keep** (classified `event`) |
| EI_Nashik (cover date) | override | **review** |
| Needs_Assessment (citation year) | override | **keep** (classified `edition`) |

## Production state

| invariant | value |
|---|---|
| documents_rows | 11995 |
| documents_max_updated_at | 2026-08-19 09:13:19 |
| documents_max_indexed_at | 2026-08-19 09:13:19 |
| pdf_attachment_rows | 3495 |
| checksum_fingerprint | 4ec63c7009da2abc |
| checksum_published_at | 441c8012af96af6f |
| checksum_content_hash | bbd8dc08e1039a68 |
| checksum_doc_version | c01afec2a2c7f9c8 |
| qdrant_collection | documents |
| qdrant_points | 152817 |
| captured_at | 2026-08-20T05:58:47.228343+00:00 |
