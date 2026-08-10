# Full-corpus shadow validation — statement-grounded (v4)

Run 2026-08-10 over the complete corpus. One targeted change from v3-final: an automatic override now also requires the **supporting statement itself** to be present in the PDF text, not merely the date. Shadow mode throughout.

## The fix

`date_is_in_text()` proved insufficient. `The-Pioneer-...-December-24-2013.pdf` contains only a browser print header (`12/24/13 The Pioneer`), which satisfies "the date appears in the document" — yet the model reported a full masthead assembled from the *filename*. `statement_is_in_text()` now requires the quoted phrase to appear in the document. Comparison is on squashed alphanumerics, which absorbs case, whitespace, line breaks, hyphenation and punctuation styling, and absorbs nothing else: an added word, a reordered phrase or a supplied name all fail. Both gates must pass; failure yields `review`, never `keep_page_date`.

## Corpus metrics

| metric | value |
|---|---:|
| total PDFs | 3779 |
| keep_page_date | 3745 |
| review | 28 |
| automatic overrides | 6 |
| deterministic overrides | 0 |
| LLM overrides | 6 |
| PDFs sent to LLM | 315 |
| LLM calls | 315 |
| LLM fetch failures | 122 |
| estimated cost USD | 0.0858 |
| edition labels | 144 |
| unreadable/unavailable PDFs | 128 |
| no-date cases | 240 |

## v3-final -> v4

| metric | v3-final | v4 |
|---|---:|---:|
| keep_page_date | 3747 | 3745 |
| review | 22 | 28 |
| **automatic overrides** | **10** | **6** |
| deterministic overrides | 0 | 0 |
| overrides passing all 8 audit checks | 7/10 | **6/6** |

Four overrides removed, all newspaper clippings whose quoted masthead was reconstructed from the filename. In every case the date was genuinely in the document but the statement was not:

| filename | was proposing | date grounded | statement grounded | now |
|---|---|---|---|---|
| The-Pioneer-...-December-24-2013 | 2013-12-24 | yes | **no** | review |
| Chandigarh-Tribune (Mon 23 Dec) | 2013-12-23 | yes | **no** | review |
| Chandigarh-Tribune (Tue 24 Dec) | 2013-12-24 | yes | **no** | review |
| Business-Standard (Mon 30 Dec) | 2013-12-30 | yes | **no** | review |

(Hindustan-Times was already review in v3-final: its text layer is unreadable mojibake, so neither gate could pass.)

## The 6 surviving overrides — all audited, none sampled

| filename | current | proposed | statement | checks |
|---|---|---|---|---|
| 20250331_pr_3851.pdf | 2025-05-30 | 2025-03-31 | `New Delhi, 31 March 2025` | 8/8 |
| Post_2015_bulletin%20and_TEDDY_launch. | 2018-03-10 | 2014-07-09 | `New Delhi, July 9, 2014: The bulletin on the` | 8/8 |
| Tender_No_22 _Project_TERI_2024_Decemb | 2018-04-11 | 2024-12-11 | `ISSUE NO. 22 DATED 11-12-2024` | 8/8 |
| Tender_NAM_Project_TERI_2023_August_Te | 2018-04-11 | 2023-08-10 | `ISSUE NO. 01 DATED 10-08-2023` | 8/8 |
| 1.-MoR-circular-date-15.03.2022.pdf | 2022-10-18 | 2022-03-15 | `dt.15.03.2022` | 8/8 |
| India-News-Calling-Chandigarh-Monday-D | 2018-01-09 | 2013-12-23 | `Chandigarh,23.12.13:` | 8/8 |

## Production safety

| invariant | before | after | unchanged |
|---|---|---|---|
| documents_rows | 15434 | 15434 | YES |
| documents_max_updated_at | 2026-08-09 11:44:34 | 2026-08-09 11:44:34 | YES |
| documents_max_indexed_at | 2026-08-09 11:44:34 | 2026-08-09 11:44:34 | YES |
| pdf_attachment_rows | 3174 | 3174 | YES |
| checksum_fingerprint | aa1bfe817d8c0152 | aa1bfe817d8c0152 | YES |
| checksum_published_at | e8d10b89e050851a | e8d10b89e050851a | YES |
| checksum_content_hash | 03307c3371313fdc | 03307c3371313fdc | YES |
| checksum_doc_version | 98ec5871dd805b2c | 98ec5871dd805b2c | YES |
| qdrant_collection | documents | documents | YES |
| qdrant_points | 149457 | 149457 | YES |

No document row, `published_at`, fingerprint, `content_hash`, `doc_version` or Qdrant point changed. No re-index, no backfill, no ingestion change. Document Intelligence was never called.

