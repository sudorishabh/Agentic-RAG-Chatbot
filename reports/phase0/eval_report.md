# Date-resolution evaluation

30 hand-labelled cases from the real corpus. 17 LLM calls.

- action correct: **29/30** (97%)
- **false overrides: 0** (primary metric — lower is better)
- missed overrides: 1
- edition labels correct: **4/4**

### Per-case

| id | expected | got | type | edition | by | rule | ok |
|---|---|---|---|---|---|---|---|
| single-01 | keep_page_date | keep_page_date | publication | - | deterministic | single_pdf_page | ok |
| single-02 | keep_page_date | keep_page_date | publication | - | deterministic | single_pdf_page | ok |
| single-03 | keep_page_date | keep_page_date | publication | - | deterministic | single_pdf_page | ok |
| single-04 | keep_page_date | keep_page_date | publication | - | deterministic | single_pdf_page | ok |
| single-05 | keep_page_date | keep_page_date | unknown | - | llm | single_pdf_late_upload_review | ok |
| migration-01 | keep_page_date | keep_page_date | publication | - | deterministic | single_pdf_page | ok |
| migration-02 | keep_page_date | keep_page_date | publication | - | deterministic | single_pdf_page | ok |
| migration-03 | keep_page_date | keep_page_date | unknown | - | llm | migration_cohort_review | ok |
| multi-01 | keep_page_date | keep_page_date | unknown | - | llm | multi_pdf_late_upload_review | ok |
| multi-02 | keep_page_date | keep_page_date | publication | - | deterministic | multi_pdf_uploaded_with_page | ok |
| annual-01 | keep_page_date | keep_page_date | unknown | 2024-2025 | llm | multi_pdf_textual_only | ok |
| annual-02 | keep_page_date | keep_page_date | unknown | 2021-2022 | llm | multi_pdf_textual_only | ok |
| annual-03 | keep_page_date | keep_page_date | edition | 2015-2016 | llm | multi_pdf_textual_only | ok |
| annual-04 | keep_page_date | keep_page_date | edition | 2017-2018 | llm | multi_pdf_textual_only | ok |
| inbody-01 | keep_page_date | keep_page_date | publication | - | deterministic | multi_pdf_url_month_matches | ok |
| inbody-02 | keep_page_date | keep_page_date | unknown | 2025 | llm | multi_pdf_url_month_review | ok |
| event-01 | keep_page_date | keep_page_date | publication | - | deterministic | multi_pdf_uploaded_with_page | ok |
| subject-year-01 | keep_page_date | keep_page_date | publication | - | deterministic | multi_pdf_uploaded_with_page | ok |
| subject-year-02 | keep_page_date | keep_page_date | unknown | - | llm | multi_pdf_late_upload_review | ok |
| file-older-01 | keep_page_date | keep_page_date | publication | - | deterministic | multi_pdf_uploaded_with_page | ok |
| no-evidence-01 | keep_page_date | keep_page_date | publication | - | deterministic | multi_pdf_no_evidence | ok |
| pubstatement-01 | propose_override | propose_override | publication | - | llm | multi_pdf_textual_only | ok |
| newspaper-01 | propose_override | propose_override | publication | - | llm | multi_pdf_textual_only | ok |
| notification-01 | keep_page_date | keep_page_date | notification | - | llm | multi_pdf_textual_only | ok |
| tender-01 | propose_override | propose_override | publication | - | llm | multi_pdf_textual_only | ok |
| pubdate-label-01 | propose_override | keep_page_date | publication | - | deterministic | multi_pdf_uploaded_with_page | miss |
| effective-01 | keep_page_date | keep_page_date | effective | - | llm | multi_pdf_textual_only | ok |
| update-year-01 | keep_page_date | keep_page_date | authoring | - | llm | multi_pdf_textual_only | ok |
| cover-date-01 | keep_page_date | keep_page_date | edition | January 2023 | llm | multi_pdf_late_upload_review | ok |
| citation-year-01 | keep_page_date | keep_page_date | edition | January - April 2023 | llm | multi_pdf_late_upload_review | ok |

### Missed overrides

- **pubdate-label-01** — Explicit 'Date of Publication' label.
  - got `keep_page_date` via `multi_pdf_uploaded_with_page` (deterministic)

### Date-type distribution

| type | count |
|---|---:|
| publication | 16 |
| unknown | 7 |
| edition | 4 |
| notification | 1 |
| effective | 1 |
| authoring | 1 |
