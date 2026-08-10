# PDF date resolution — manual review pack

Generated 2026-08-10 11:21 UTC from the Phase 0 shadow results. **Nothing has been applied.** Every `proposed_published_at` below is a suggestion held in shadow storage; the live `published_at` is unchanged.

Companion CSV: `date_resolution_manual_review.csv` — the `human_*` columns are blank for you to fill in.

## Summary

| metric | value |
|---|---:|
| total PDFs in corpus analysis | 3779 |
| sampled for review | 58 |
| &nbsp;&nbsp;1_single_pdf | 10 |
| &nbsp;&nbsp;2_multi_pdf_over_time | 5 |
| &nbsp;&nbsp;2_multi_pdf_together | 5 |
| &nbsp;&nbsp;4_migration_era | 10 |
| &nbsp;&nbsp;5_annual_report | 10 |
| &nbsp;&nbsp;5_edition_style | 4 |
| &nbsp;&nbsp;6_llm_other | 8 |
| &nbsp;&nbsp;6_llm_override | 6 |
| single-PDF cases sampled | 20 |
| multi-PDF cases sampled | 38 |
| in-body cases sampled | 21 |
| LLM-assisted cases sampled | 30 |
| corpus: keep_page_date | 3745 |
| corpus: deterministic overrides | 0 |
| corpus: LLM overrides | 6 |
| corpus: review | 28 |
| corpus: LLM-assisted total | 315 |

### Sampled decisions by action

| action | count |
|---|---:|
| keep_page_date | 49 |
| override | 6 |
| review | 3 |

### Most common reasons for a proposed change (whole corpus)

| rule | overrides | what it means |
|---|---:|---|
| `llm_interpreted` | 6 | The document's own text states an explicit publication date, quoted verbatim by the model. This is now the only route to an override. |

## Annual reports — an edition, NOT a publication date

The system deliberately keeps the page date and records the reporting period separately. `2024-2025` is a **label**, not a date: none of these documents was published on 2024-01-01.

| filename | anchor text | edition_label | current published_at | proposed | PDF creation date | action |
|---|---|---|---|---|---|---|
| Annual-Report-19-20.pdf | Annual Report 2019-2020 | **2019-2020** | 2022-02-09 | 2022-02-09 | 2021-02-10 | keep_page_date |
| Annual-Report-20-21.pdf | Annual Report 2020-2021 | **2020-2021** | 2022-02-09 | 2022-02-09 | 2022-03-10 | keep_page_date |
| TAR_2015-16.pdf | Annual Report 2015-2016 | **2015-2016** | 2022-02-09 | 2022-02-09 | 2016-07-22 | keep_page_date |
| TAR_2016-17.pdf | Annual Report 2016-2017 | **2016-2017** | 2022-02-09 | 2022-02-09 | 2017-11-14 | keep_page_date |
| TAR_2017-18.pdf | Annual Report 2017-2018 | **2017-2018** | 2022-02-09 | 2022-02-09 | 2019-03-19 | keep_page_date |
| TAR_2018-19.pdf | Annual Report 2018-2019 | **2018-2019** | 2022-02-09 | 2022-02-09 | 2019-12-20 | keep_page_date |
| TERI-Annual-Report-2023-24.pdf | Annual Report 2023-2024 | **2023-2024** | 2022-02-09 | 2022-02-09 | 2024-12-23 | keep_page_date |
| TERI-Annual-Report-2024-25.pdf | Annual Report 2024-2025 | **2024-2025** | 2022-02-09 | 2022-02-09 | 2025-11-21 | keep_page_date |
| TERI_Annual_Report_2022_23.pdf | Annual Report 2022-2023 | **2022-2023** | 2022-02-09 | 2022-02-09 | 2024-03-15 | keep_page_date |
| TERI_Annual_Report_upload.pdf | Annual Report 2021-2022 | **2021-2022** | 2022-02-09 | 2022-02-09 | 2022-12-09 | keep_page_date |

## LLM-assisted decisions

30 sampled. `pdf_available_to_llm=false` means the model saw **metadata only** — the PDF could not be fetched, or had no readable internal metadata. Failed fetches are shown, not hidden.


### 20250331_pr_3851.pdf

- **action**: `override` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2025-05-30 · **proposed**: 2025-03-31
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: The Silent Disaster: Why India Must Build Stronger Heatwave  (6 PDFs, inbody)
- **evidence available**: node.created=2025-05-30, file.created=(none - in-body), pdf CreationDate=2025-03-31, anchor=April to June in 2025
- **LLM reasoning**: The first page text includes a date stating 'New Delhi, 31 March 2025', which indicates the publication date of the document.
- **decision**: proposes changing 2025-05-30 -> **2025-03-31**, on an explicit publication statement.
- pdf: https://internal.imd.gov.in/press_release/20250331_pr_3851.pdf

### Post_2015_bulletin%20and_TEDDY_launch.pdf

- **action**: `override` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2018-03-10 · **proposed**: 2014-07-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Sustainable Development Goals (12 PDFs, inbody)
- **evidence available**: node.created=2018-03-10, file.created=(none - in-body), pdf CreationDate=2014-07-09, anchor=Viewpoints on the Post-2015 Development 
- **LLM reasoning**: The first page text states that the bulletin was presented on July 9, 2014.
- **decision**: proposes changing 2018-03-10 -> **2014-07-09**, on an explicit publication statement.
- pdf: https://www.teriin.org/projects/teddy/pdf/Post_2015_bulletin%20and_TEDDY_launch.pdf

### Tender_No_22 _Project_TERI_2024_December_Tender_Renewables_V4.pdf

- **action**: `override` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2018-04-11 · **proposed**: 2024-12-11
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Announcements (70 PDFs, inbody)
- **evidence available**: node.created=2018-04-11, file.created=(none - in-body), pdf CreationDate=2024-12-11, anchor=Downloaded
- **LLM reasoning**: The first page text states 'ISSUE NO. 22 DATED 11-12-2024', indicating the publication date.
- **edition_label**: `2024-2025` (a reporting period, not a publication date)
- **decision**: proposes changing 2018-04-11 -> **2024-12-11**, on an explicit publication statement.
- pdf: https://teriin.org/sites/default/files/files/Tender_No_22 _Project_TERI_2024_December_Tender_Renewables_V4.pdf

### Tender_NAM_Project_TERI_2023_August_Tender_no_013_new.pdf

- **action**: `override` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2018-04-11 · **proposed**: 2023-08-10
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Announcements (70 PDFs, inbody)
- **evidence available**: node.created=2018-04-11, file.created=(none - in-body), pdf CreationDate=2023-08-23, anchor=Download
- **LLM reasoning**: The first page text states 'ISSUE NO. 01 DATED 10-08-2023', indicating the publication date of the tender.
- **decision**: proposes changing 2018-04-11 -> **2023-08-10**, on an explicit publication statement.
- pdf: https://teriin.org/sites/default/files/files/Tender_NAM_Project_TERI_2023_August_Tender_no_013_new.pdf

### 1.-MoR-circular-date-15.03.2022.pdf

- **action**: `override` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2022-10-18 · **proposed**: 2022-03-15
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Freight Greenhouse Gas Calculator (2 PDFs, inbody)
- **evidence available**: node.created=2022-10-18, file.created=(none - in-body), pdf CreationDate=2022-03-15, anchor=Rail Green Points
- **LLM reasoning**: The document contains a date stated as 'dt.15.03.2022' which indicates the publication date of the Rates Circular No. 6 of 2022.
- **decision**: proposes changing 2022-10-18 -> **2022-03-15**, on an explicit publication statement.
- pdf: https://www.ccai.co.in/wp-content/uploads/2022/05/1.-MoR-circular-date-15.03.2022.pdf

### India-News-Calling-Chandigarh-Monday-December-23-2013.pdf

- **action**: `override` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2018-01-09 · **proposed**: 2013-12-23
- **pdf_available_to_llm**: `false` · **url reachable now**: `http_200`
- **page**: Conference on 'Promoting Rooftop Solar Photovoltaic Systems  (11 PDFs, inbody)
- **evidence available**: node.created=2018-01-09, file.created=(none - in-body), pdf CreationDate=(unreadable), anchor=India News Calling, Chandigarh, Monday, 
- **LLM reasoning**: The text includes a date 'Chandigarh,23.12.13:' which indicates the publication date of the document.
- **decision**: proposes changing 2018-01-09 -> **2013-12-23**, on an explicit publication statement.
- pdf: https://www.teriin.org/eventdocs/files/India-News-Calling-Chandigarh-Monday-December-23-2013.pdf

### TAR_2016-17.pdf

- **action**: `keep_page_date` · **date_type**: `edition` · **confidence**: 0.9
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2017-11-14, anchor=Annual Report 2016-2017
- **LLM reasoning**: The filename 'TAR_2016-17.pdf' indicates that this document is an annual report for the period 2016-2017.
- **edition_label**: `2016-2017` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/TAR_2016-17.pdf

### TAR_2017-18.pdf

- **action**: `keep_page_date` · **date_type**: `edition` · **confidence**: 0.9
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2019-03-19, anchor=Annual Report 2017-2018
- **LLM reasoning**: The filename 'TAR_2017-18.pdf' and the first page text indicate that this is the Annual Report for the period 2017-2018.
- **edition_label**: `2017-2018` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/TAR_2017-18.pdf

### TAR_2018-19.pdf

- **action**: `keep_page_date` · **date_type**: `edition` · **confidence**: 0.9
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2019-12-20, anchor=Annual Report 2018-2019
- **LLM reasoning**: The filename 'TAR_2018-19.pdf' and the link text 'Annual Report 2018-2019' indicate the reporting period covered by the document.
- **edition_label**: `2018-2019` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/TAR_2018-19.pdf

### TERI-Annual-Report-2024-25.pdf

- **action**: `keep_page_date` · **date_type**: `edition` · **confidence**: 0.9
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2025-11-21, anchor=Annual Report 2024-2025
- **LLM reasoning**: The document is titled 'Annual Report 2024-2025', indicating it covers the reporting period of 2024-2025.
- **edition_label**: `2024-2025` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://teriin.org/files/TERI-Annual-Report-2024-25.pdf

### Satoyama_Book_Updated.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.9
- **current published_at**: 2022-01-25 · **proposed**: 2022-01-25
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Traditional agriculture for sustainable development: a Satoy (3 PDFs, attachment)
- **evidence available**: node.created=2022-01-25, file.created=2022-12-08, pdf CreationDate=2022-11-24, anchor=(none)
- **LLM reasoning**: The evidence provided consists of upload and authoring dates, but there is no explicit publication date mentioned in the text or metadata.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2022-12/Satoyama_Book_Updated.pdf

### Achieving Green Steel Roadmap to a Net Zero Steel Sector in India updated.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.9
- **current published_at**: 2020-01-30 · **proposed**: 2020-01-30
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Decarbonisation of iron and steel sectors (5 PDFs, attachment)
- **evidence available**: node.created=2020-01-30, file.created=2022-07-28, pdf CreationDate=2022-07-22, anchor=(none)
- **LLM reasoning**: The evidence provided includes upload and authoring dates, but there is no explicit publication date mentioned in the text.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2022-07/Achieving%20Green%20Steel%20Roadmap%20to%20a%20Net%20Zero%20Steel%20Sector%20in%20India%20updated.pdf

### Policy Brief Fuel  Efficiency Improvement Emission Standards.pdf

- **action**: `review` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2022-02-15 · **proposed**: 2022-02-15
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: National Transport Decarbonization Council (13 PDFs, attachment)
- **evidence available**: node.created=2022-02-15, file.created=2023-08-14, pdf CreationDate=2023-08-07, anchor=(none)
- **LLM reasoning**: The phrase 'PUBLISHED BY The Energy and Resources Institute (TERI)' indicates the document was published by TERI, suggesting a publication date in 2023.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2023-08/Policy%20Brief%20Fuel%20%20Efficiency%20Improvement%20Emission%20Standards.pdf

### existing-commercial-building-retrofit-guidelines.pdf.pdf

- **action**: `review` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2017-12-27 · **proposed**: 2017-12-27
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: United Technologies-TERI Center of Excellence for Energy Eff (2 PDFs, attachment)
- **evidence available**: node.created=2017-12-27, file.created=2019-06-25, pdf CreationDate=2019-02-08, anchor=(none)
- **LLM reasoning**: The first page text includes a citation format that references the year 2019 as the publication year for the guidelines.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2019-06/existing-commercial-building-retrofit-guidelines.pdf.pdf

### Minutes of meeting Efficiency.pdf

- **action**: `keep_page_date` · **date_type**: `event` · **confidence**: 0.9
- **current published_at**: 2022-02-15 · **proposed**: 2022-02-15
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: National Transport Decarbonization Council (13 PDFs, attachment)
- **evidence available**: node.created=2022-02-15, file.created=2022-12-23, pdf CreationDate=2022-09-09, anchor=(none)
- **LLM reasoning**: The first page text mentions a workshop held on September 01, 2022, which is the date of the event discussed in the document.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2022-12/Minutes%20of%20meeting%20Efficiency.pdf

### What does intercity electric mobility look like from a commuter's perspective new.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.9
- **current published_at**: 2026-02-17 · **proposed**: 2026-02-17
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Assessment of Community Benefits from E-Bus Operations (6 PDFs, attachment)
- **evidence available**: node.created=2026-02-17, file.created=2026-06-05, pdf CreationDate=2026-02-12, anchor=(none)
- **LLM reasoning**: The evidence provided consists of upload and authoring dates, but there is no explicit publication date mentioned in the text or metadata.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2026-06/What%20does%20intercity%20electric%20mobility%20look%20like%20from%20a%20commuter%27s%20perspective%20new.pdf

### 2017MC01-Air Quality Status of Maharashtra 2016-17.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.9
- **current published_at**: 2018-02-07 · **proposed**: 2018-02-07
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Air Quality Status Report of Maharashtra 2016-17 (1 PDFs, attachment)
- **evidence available**: node.created=2018-02-07, file.created=2020-02-04, pdf CreationDate=2019-08-29, anchor=(none)
- **LLM reasoning**: The document title indicates it is a report for the period 2016-2017, but there is no explicit publication date provided in the evidence.
- **edition_label**: `2016-2017` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2020-02/2017MC01-Air%20Quality%20Status%20of%20Maharashtra%202016-17.pdf

### Zinc_Report.pdf

- **action**: `review` · **date_type**: `publication` · **confidence**: 0.9
- **current published_at**: 2018-02-05 · **proposed**: 2018-02-05
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Widening the coverage of PAT scheme in subsequent phases by  (6 PDFs, attachment)
- **evidence available**: node.created=2018-02-05, file.created=2021-08-11, pdf CreationDate=2014-04-01, anchor=(none)
- **LLM reasoning**: The first page text includes the phrase 'Published by The Energy and Resources Institute', indicating the document's publication.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2021-08/Zinc_Report.pdf

### Annual-Report-20-21.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.8
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2022-03-10, anchor=Annual Report 2020-2021
- **LLM reasoning**: The document is titled 'Annual Report 2020-2021', indicating it covers the reporting period 2020-2021, but there is no explicit publication date provided in the evidence.
- **edition_label**: `2020-2021` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/Annual-Report-20-21.pdf

### TAR_2015-16.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.8
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2016-07-22, anchor=Annual Report 2015-2016
- **LLM reasoning**: The filename indicates the document is an Annual Report for the period 2015-2016, but there is no explicit publication date provided in the evidence.
- **edition_label**: `2015-2016` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/TAR_2015-16.pdf

### TERI-Annual-Report-2023-24.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.8
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2024-12-23, anchor=Annual Report 2023-2024
- **LLM reasoning**: The document is titled 'Annual Report 2023-2024', indicating it covers that reporting period, but there is no explicit publication date provided in the evidence.
- **edition_label**: `2023-2024` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://teriin.org/files/TERI-Annual-Report-2023-24.pdf

### TERI_Annual_Report_2022_23.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.8
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2024-03-15, anchor=Annual Report 2022-2023
- **LLM reasoning**: The document is titled 'Annual Report 2022-2023', indicating it covers the reporting period of 2022-2023, but there is no explicit publication date provided in the evidence.
- **edition_label**: `2022-2023` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/TERI_Annual_Report_2022_23.pdf

### Annual-Report-19-20.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.5
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2021-02-10, anchor=Annual Report 2019-2020
- **LLM reasoning**: The document is titled 'Annual Report 2019-2020', but there is no explicit publication date provided in the evidence.
- **edition_label**: `2019-2020` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/Annual-Report-19-20.pdf

### TERI_Annual_Report_upload.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.5
- **current published_at**: 2022-02-09 · **proposed**: 2022-02-09
- **pdf_available_to_llm**: `true` · **url reachable now**: `http_200`
- **page**: Annual Reports (10 PDFs, inbody)
- **evidence available**: node.created=2022-02-09, file.created=(none - in-body), pdf CreationDate=2022-12-09, anchor=Annual Report 2021-2022
- **LLM reasoning**: The document is titled 'Annual Report 2021-2022', but there is no explicit publication date provided in the evidence.
- **edition_label**: `2021-2022` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: https://www.teriin.org/sites/default/files/files/TERI_Annual_Report_upload.pdf

### Renewable-Power-Pathways-Report.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.0
- **current published_at**: 2018-01-01 · **proposed**: 2018-01-01
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Energy Transitions (6 PDFs, attachment)
- **evidence available**: node.created=2018-01-01, file.created=2020-07-21, pdf CreationDate=2020-07-21, anchor=(none)
- **LLM reasoning**: No publication date found in the provided evidence; all dates are related to upload or authoring.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2020-07/Renewable-Power-Pathways-Report.pdf

### Mapping-Impact-of-Coal-Mines-Case-of-Betul.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.0
- **current published_at**: 2018-01-01 · **proposed**: 2018-01-01
- **pdf_available_to_llm**: `true` · **url reachable now**: `not rechecked`
- **page**: Energy Transitions (6 PDFs, attachment)
- **evidence available**: node.created=2018-01-01, file.created=2021-03-12, pdf CreationDate=2021-02-09, anchor=(none)
- **LLM reasoning**: No publication date found in the provided evidence.
- **decision**: abstained — page date kept.
- pdf: /sites/default/files/2021-03/Mapping-Impact-of-Coal-Mines-Case-of-Betul.pdf

### Income-&amp;-Expenditure-2024-25.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.0
- **current published_at**: 2018-04-04 · **proposed**: 2018-04-04
- **pdf_available_to_llm**: `false` · **url reachable now**: `ConnectionError`
- **page**: FCRA Financials (69 PDFs, inbody)
- **evidence available**: node.created=2018-04-04, file.created=(none - in-body), pdf CreationDate=(unreadable), anchor=Income &amp; Expenditure
- **LLM reasoning**: No publication date evidence found in the provided information.
- **edition_label**: `2024-25` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: sites/default/files/files/fcra-receipts/Income-&amp;-Expenditure-2024-25.pdf

### Auditor_Report_2023_24.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.0
- **current published_at**: 2018-04-04 · **proposed**: 2018-04-04
- **pdf_available_to_llm**: `false` · **url reachable now**: `ConnectionError`
- **page**: FCRA Financials (69 PDFs, inbody)
- **evidence available**: node.created=2018-04-04, file.created=(none - in-body), pdf CreationDate=(unreadable), anchor=Auditor's Report
- **LLM reasoning**: No publication date evidence found in the provided information.
- **edition_label**: `2023-24` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: sites/default/files/files/fcra-receipts/Auditor_Report_2023_24.pdf

### Balance_Sheet_22_23.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.0
- **current published_at**: 2018-04-04 · **proposed**: 2018-04-04
- **pdf_available_to_llm**: `false` · **url reachable now**: `ConnectionError`
- **page**: FCRA Financials (69 PDFs, inbody)
- **evidence available**: node.created=2018-04-04, file.created=(none - in-body), pdf CreationDate=(unreadable), anchor=Auditor's Report
- **LLM reasoning**: No publication date or relevant evidence found in the provided information.
- **edition_label**: `2022-23` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: sites/default/files/files/fcra-receipts/Balance_Sheet_22_23.pdf

### Income_&amp;_Expenditure_2023_24.pdf

- **action**: `keep_page_date` · **date_type**: `unknown` · **confidence**: 0.0
- **current published_at**: 2018-04-04 · **proposed**: 2018-04-04
- **pdf_available_to_llm**: `false` · **url reachable now**: `ConnectionError`
- **page**: FCRA Financials (69 PDFs, inbody)
- **evidence available**: node.created=2018-04-04, file.created=(none - in-body), pdf CreationDate=(unreadable), anchor=Income &amp; Expenditure
- **LLM reasoning**: No publication date evidence found in the provided information.
- **edition_label**: `2023-24` (a reporting period, not a publication date)
- **decision**: abstained — page date kept.
- pdf: sites/default/files/files/fcra-receipts/Income_&amp;_Expenditure_2023_24.pdf

## Every proposed override in this sample (6)

Each block lays out the raw evidence so the decision can be checked without reading any code.


**20250331_pr_3851.pdf**  (6_llm_override)

```
Current:   2025-05-30
Proposed:  2025-03-31   [publication via llm_publication]
Evidence:
  node.created      = 2025-05-30
  file.created      = (no Drupal file record)
  PDF CreationDate  = 2025-03-31
  PDFs on this page = 6
  origin            = inbody
  anchor text       = April to June in 2025
  rule              = llm_interpreted
  LLM used          = yes (confidence 0.9)
```
page created 2025-05-30; no Drupal file record (in-body link); PDF internally created 2025-03-31; 6 PDF(s) on this page. Deterministic rules cannot propose a change, so the evidence was sent to the LLM to look for an explicit publication statement. LLM: The first page text includes a date stating 'New Delhi, 31 March 2025', which indicates the publication date of the document.

- page: -
- pdf: https://internal.imd.gov.in/press_release/20250331_pr_3851.pdf

**Post_2015_bulletin%20and_TEDDY_launch.pdf**  (6_llm_override)

```
Current:   2018-03-10
Proposed:  2014-07-09   [publication via llm_publication]
Evidence:
  node.created      = 2018-03-10
  file.created      = (no Drupal file record)
  PDF CreationDate  = 2014-07-09
  PDFs on this page = 12
  origin            = inbody
  anchor text       = Viewpoints on the Post-2015 Development Agenda
  rule              = llm_interpreted
  LLM used          = yes (confidence 0.9)
```
page created 2018-03-10; no Drupal file record (in-body link); PDF internally created 2014-07-09; 12 PDF(s) on this page. Deterministic rules cannot propose a change, so the evidence was sent to the LLM to look for an explicit publication statement. LLM: The first page text states that the bulletin was presented on July 9, 2014.

- page: https://teriin.org/sustainable-development-goals
- pdf: https://www.teriin.org/projects/teddy/pdf/Post_2015_bulletin%20and_TEDDY_launch.pdf

**Tender_No_22 _Project_TERI_2024_December_Tender_Renewables_V4.pdf**  (6_llm_override)

```
Current:   2018-04-11
Proposed:  2024-12-11   [publication via llm_publication]
Evidence:
  node.created      = 2018-04-11
  file.created      = (no Drupal file record)
  PDF CreationDate  = 2024-12-11
  PDFs on this page = 70
  origin            = inbody
  anchor text       = Downloaded
  rule              = llm_interpreted
  LLM used          = yes (confidence 0.9)
```
page created 2018-04-11; no Drupal file record (in-body link); PDF internally created 2024-12-11; 70 PDF(s) on this page. Deterministic rules cannot propose a change, so the evidence was sent to the LLM to look for an explicit publication statement. LLM: The first page text states 'ISSUE NO. 22 DATED 11-12-2024', indicating the publication date.

- page: https://teriin.org/announcements
- pdf: https://teriin.org/sites/default/files/files/Tender_No_22 _Project_TERI_2024_December_Tender_Renewables_V4.pdf

**Tender_NAM_Project_TERI_2023_August_Tender_no_013_new.pdf**  (6_llm_override)

```
Current:   2018-04-11
Proposed:  2023-08-10   [publication via llm_publication]
Evidence:
  node.created      = 2018-04-11
  file.created      = (no Drupal file record)
  PDF CreationDate  = 2023-08-23
  PDFs on this page = 70
  origin            = inbody
  anchor text       = Download
  rule              = llm_interpreted
  LLM used          = yes (confidence 0.9)
```
page created 2018-04-11; no Drupal file record (in-body link); PDF internally created 2023-08-23; 70 PDF(s) on this page. Deterministic rules cannot propose a change, so the evidence was sent to the LLM to look for an explicit publication statement. LLM: The first page text states 'ISSUE NO. 01 DATED 10-08-2023', indicating the publication date of the tender.

- page: https://teriin.org/announcements
- pdf: https://teriin.org/sites/default/files/files/Tender_NAM_Project_TERI_2023_August_Tender_no_013_new.pdf

**1.-MoR-circular-date-15.03.2022.pdf**  (6_llm_override)

```
Current:   2022-10-18
Proposed:  2022-03-15   [publication via llm_publication]
Evidence:
  node.created      = 2022-10-18
  file.created      = (no Drupal file record)
  PDF CreationDate  = 2022-03-15
  PDFs on this page = 2
  origin            = inbody
  anchor text       = Rail Green Points
  rule              = llm_interpreted
  LLM used          = yes (confidence 0.9)
```
page created 2022-10-18; no Drupal file record (in-body link); PDF internally created 2022-03-15; 2 PDF(s) on this page. Deterministic rules cannot propose a change, so the evidence was sent to the LLM to look for an explicit publication statement. LLM: The document contains a date stated as 'dt.15.03.2022' which indicates the publication date of the Rates Circular No. 6 of 2022.

- page: -
- pdf: https://www.ccai.co.in/wp-content/uploads/2022/05/1.-MoR-circular-date-15.03.2022.pdf

**India-News-Calling-Chandigarh-Monday-December-23-2013.pdf**  (6_llm_override)

```
Current:   2018-01-09
Proposed:  2013-12-23   [publication via llm_publication]
Evidence:
  node.created      = 2018-01-09
  file.created      = (no Drupal file record)
  PDF CreationDate  = (unreadable)
  PDFs on this page = 11
  origin            = inbody
  anchor text       = India News Calling, Chandigarh, Monday, December 23, 2013
  rule              = llm_interpreted
  LLM used          = yes (confidence 0.9)
```
page created 2018-01-09; no Drupal file record (in-body link); PDF creation date unreadable; 11 PDF(s) on this page. Deterministic rules cannot propose a change, so the evidence was sent to the LLM to look for an explicit publication statement. LLM: The text includes a date 'Chandigarh,23.12.13:' which indicates the publication date of the document.

- page: https://teriin.org/event/conference-promoting-rooftop-solar-photovoltaic-systems-india
- pdf: https://www.teriin.org/eventdocs/files/India-News-Calling-Chandigarh-Monday-December-23-2013.pdf

## Full sampled set

| # | group | filename | PDFs | origin | node.created | file.created | pdf date | current | proposed | action | rule | LLM |
|---:|---|---|---:|---|---|---|---|---|---|---|---|---|
| 1 | 1_single_pdf | not-so-rare-species-ircf.pdf | 1 | attachment | 2019-01-18 | 2019-01-18 | - | 2019-01-18 | 2019-01-18 | **keep_page_date** | single_pdf_page | no |
| 2 | 1_single_pdf | reversing-land-degradation-bg- | 1 | attachment | 2019-07-30 | 2019-07-31 | - | 2019-07-30 | 2019-07-30 | **keep_page_date** | single_pdf_page | no |
| 3 | 1_single_pdf | HAL-casestudy.pdf | 1 | attachment | 2018-02-02 | 2018-03-05 | - | 2018-02-02 | 2018-02-02 | **keep_page_date** | single_pdf_page | no |
| 4 | 1_single_pdf | case-study-panaji.pdf | 1 | attachment | 2018-03-03 | 2018-03-03 | - | 2018-03-03 | 2018-03-03 | **keep_page_date** | single_pdf_page | no |
| 5 | 1_single_pdf | EV RCNA Final Report.pdf | 1 | attachment | 2022-04-21 | 2022-04-21 | - | 2022-04-21 | 2022-04-21 | **keep_page_date** | single_pdf_page | no |
| 6 | 1_single_pdf | scp-framework-research-paper.p | 1 | attachment | 2018-01-20 | 2018-01-20 | - | 2018-01-20 | 2018-01-20 | **keep_page_date** | single_pdf_page | no |
| 7 | 1_single_pdf | 1694684809Lal 2022 - Science R | 1 | attachment | 2023-09-15 | 2023-09-15 | - | 2023-09-15 | 2023-09-15 | **keep_page_date** | single_pdf_page | no |
| 8 | 1_single_pdf | Dr Shiv Kumar Dube IJSRP Novem | 1 | attachment | 2018-12-18 | 2018-12-18 | - | 2018-12-18 | 2018-12-18 | **keep_page_date** | single_pdf_page | no |
| 9 | 1_single_pdf | The-Green-School-Project-Brief | 1 | attachment | 2018-07-04 | 2018-07-04 | - | 2018-07-04 | 2018-07-04 | **keep_page_date** | single_pdf_page | no |
| 10 | 1_single_pdf | Air_Quality_Report.pdf | 1 | attachment | 2019-06-07 | 2019-06-19 | - | 2019-06-07 | 2019-06-07 | **keep_page_date** | single_pdf_page | no |
| 11 | 2_multi_pdf_together | model-green-divison-ppt.pdf | 3 | attachment | 2019-07-02 | 2019-07-02 | - | 2019-07-02 | 2019-07-02 | **keep_page_date** | multi_pdf_uploaded_with_page | no |
| 12 | 2_multi_pdf_together | Green-Agenda-2019-Hindi-Versio | 2 | attachment | 2019-06-25 | 2019-06-25 | - | 2019-06-25 | 2019-06-25 | **keep_page_date** | multi_pdf_uploaded_with_page | no |
| 13 | 2_multi_pdf_together | maritime-strategy.pdf | 2 | attachment | 2019-08-05 | 2019-08-05 | - | 2019-08-05 | 2019-08-05 | **keep_page_date** | multi_pdf_uploaded_with_page | no |
| 14 | 2_multi_pdf_together | mining-recommendation-paper.pd | 2 | attachment | 2018-08-08 | 2018-08-08 | - | 2018-08-08 | 2018-08-08 | **keep_page_date** | multi_pdf_uploaded_with_page | no |
| 15 | 2_multi_pdf_together | e-bus-case-study-TERI-Kolkata. | 2 | attachment | 2020-06-16 | 2020-06-16 | - | 2020-06-16 | 2020-06-16 | **keep_page_date** | multi_pdf_uploaded_with_page | no |
| 16 | 2_multi_pdf_over_time | ES2007SF06.pdf | 2 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | migration_cohort_no_evidence | no |
| 17 | 2_multi_pdf_over_time | Renewable-Power-Pathways-Repor | 6 | attachment | 2018-01-01 | 2020-07-21 | 2020-07-21 | 2018-01-01 | 2018-01-01 | **keep_page_date** | llm_interpreted | yes |
| 18 | 2_multi_pdf_over_time | wsds-etc-es.pdf | 6 | inbody | 2018-01-01 | - | - | 2018-01-01 | 2018-01-01 | **keep_page_date** | multi_pdf_no_evidence | no |
| 19 | 2_multi_pdf_over_time | 2011RT05FR.pdf | 2 | attachment | 2017-12-28 | 2018-02-09 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | migration_cohort_no_evidence | no |
| 20 | 2_multi_pdf_over_time | Mapping-Impact-of-Coal-Mines-C | 6 | attachment | 2018-01-01 | 2021-03-12 | 2021-02-09 | 2018-01-01 | 2018-01-01 | **keep_page_date** | llm_interpreted | yes |
| 21 | 4_migration_era | case-study-RCC-check-dams-Assa | 1 | attachment | 2018-03-08 | 2018-03-08 | - | 2018-03-08 | 2018-03-08 | **keep_page_date** | single_pdf_page | no |
| 22 | 4_migration_era | ES2012EA14.pdf | 1 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | single_pdf_page | no |
| 23 | 4_migration_era | ES2012MS01.pdf | 1 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | single_pdf_page | no |
| 24 | 4_migration_era | Characteristics of the ozone p | 1 | attachment | 2018-01-11 | 2018-05-21 | - | 2018-01-11 | 2018-01-11 | **keep_page_date** | single_pdf_page | no |
| 25 | 4_migration_era | ES2012EA09.pdf | 1 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | single_pdf_page | no |
| 26 | 4_migration_era | ES2015EE04.pdf | 1 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | single_pdf_page | no |
| 27 | 4_migration_era | WASH_Indore.pdf | 2 | attachment | 2018-04-30 | 2018-04-30 | - | 2018-04-30 | 2018-04-30 | **keep_page_date** | migration_cohort_no_evidence | no |
| 28 | 4_migration_era | ES2011BL05.pdf | 1 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | single_pdf_page | no |
| 29 | 4_migration_era | mixed-cropping-case-study.pdf | 1 | attachment | 2018-02-26 | 2018-02-26 | - | 2018-02-26 | 2018-02-26 | **keep_page_date** | single_pdf_page | no |
| 30 | 4_migration_era | ES2010LC12.pdf | 1 | attachment | 2017-12-28 | 2017-12-28 | - | 2017-12-28 | 2017-12-28 | **keep_page_date** | single_pdf_page | no |
| 31 | 5_annual_report | Annual-Report-19-20.pdf | 10 | inbody | 2022-02-09 | - | 2021-02-10 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 32 | 5_annual_report | Annual-Report-20-21.pdf | 10 | inbody | 2022-02-09 | - | 2022-03-10 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 33 | 5_annual_report | TAR_2015-16.pdf | 10 | inbody | 2022-02-09 | - | 2016-07-22 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 34 | 5_annual_report | TAR_2016-17.pdf | 10 | inbody | 2022-02-09 | - | 2017-11-14 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 35 | 5_annual_report | TAR_2017-18.pdf | 10 | inbody | 2022-02-09 | - | 2019-03-19 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 36 | 5_annual_report | TAR_2018-19.pdf | 10 | inbody | 2022-02-09 | - | 2019-12-20 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 37 | 5_annual_report | TERI-Annual-Report-2023-24.pdf | 10 | inbody | 2022-02-09 | - | 2024-12-23 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 38 | 5_annual_report | TERI-Annual-Report-2024-25.pdf | 10 | inbody | 2022-02-09 | - | 2025-11-21 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 39 | 5_annual_report | TERI_Annual_Report_2022_23.pdf | 10 | inbody | 2022-02-09 | - | 2024-03-15 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 40 | 5_annual_report | TERI_Annual_Report_upload.pdf | 10 | inbody | 2022-02-09 | - | 2022-12-09 | 2022-02-09 | 2022-02-09 | **keep_page_date** | llm_interpreted | yes |
| 41 | 5_edition_style | Income-&amp;-Expenditure-2024- | 69 | inbody | 2018-04-04 | - | - | 2018-04-04 | 2018-04-04 | **keep_page_date** | llm_interpreted | yes |
| 42 | 5_edition_style | Auditor_Report_2023_24.pdf | 69 | inbody | 2018-04-04 | - | - | 2018-04-04 | 2018-04-04 | **keep_page_date** | llm_interpreted | yes |
| 43 | 5_edition_style | Balance_Sheet_22_23.pdf | 69 | inbody | 2018-04-04 | - | - | 2018-04-04 | 2018-04-04 | **keep_page_date** | llm_interpreted | yes |
| 44 | 5_edition_style | Income_&amp;_Expenditure_2023_ | 69 | inbody | 2018-04-04 | - | - | 2018-04-04 | 2018-04-04 | **keep_page_date** | llm_interpreted | yes |
| 45 | 6_llm_override | 20250331_pr_3851.pdf | 6 | inbody | 2025-05-30 | - | 2025-03-31 | 2025-05-30 | 2025-03-31 | **override** | llm_interpreted | yes |
| 46 | 6_llm_override | Post_2015_bulletin%20and_TEDDY | 12 | inbody | 2018-03-10 | - | 2014-07-09 | 2018-03-10 | 2014-07-09 | **override** | llm_interpreted | yes |
| 47 | 6_llm_override | Tender_No_22 _Project_TERI_202 | 70 | inbody | 2018-04-11 | - | 2024-12-11 | 2018-04-11 | 2024-12-11 | **override** | llm_interpreted | yes |
| 48 | 6_llm_override | Tender_NAM_Project_TERI_2023_A | 70 | inbody | 2018-04-11 | - | 2023-08-23 | 2018-04-11 | 2023-08-10 | **override** | llm_interpreted | yes |
| 49 | 6_llm_override | 1.-MoR-circular-date-15.03.202 | 2 | inbody | 2022-10-18 | - | 2022-03-15 | 2022-10-18 | 2022-03-15 | **override** | llm_interpreted | yes |
| 50 | 6_llm_override | India-News-Calling-Chandigarh- | 11 | inbody | 2018-01-09 | - | - | 2018-01-09 | 2013-12-23 | **override** | llm_interpreted | yes |
| 51 | 6_llm_other | Satoyama_Book_Updated.pdf | 3 | attachment | 2022-01-25 | 2022-12-08 | 2022-11-24 | 2022-01-25 | 2022-01-25 | **keep_page_date** | llm_interpreted | yes |
| 52 | 6_llm_other | Achieving Green Steel Roadmap  | 5 | attachment | 2020-01-30 | 2022-07-28 | 2022-07-22 | 2020-01-30 | 2020-01-30 | **keep_page_date** | llm_interpreted | yes |
| 53 | 6_llm_other | Policy Brief Fuel  Efficiency  | 13 | attachment | 2022-02-15 | 2023-08-14 | 2023-08-07 | 2022-02-15 | 2022-02-15 | **review** | llm_interpreted | yes |
| 54 | 6_llm_other | existing-commercial-building-r | 2 | attachment | 2017-12-27 | 2019-06-25 | 2019-02-08 | 2017-12-27 | 2017-12-27 | **review** | llm_interpreted | yes |
| 55 | 6_llm_other | Minutes of meeting Efficiency. | 13 | attachment | 2022-02-15 | 2022-12-23 | 2022-09-09 | 2022-02-15 | 2022-02-15 | **keep_page_date** | llm_interpreted | yes |
| 56 | 6_llm_other | What does intercity electric m | 6 | attachment | 2026-02-17 | 2026-06-05 | 2026-02-12 | 2026-02-17 | 2026-02-17 | **keep_page_date** | llm_interpreted | yes |
| 57 | 6_llm_other | 2017MC01-Air Quality Status of | 1 | attachment | 2018-02-07 | 2020-02-04 | 2019-08-29 | 2018-02-07 | 2018-02-07 | **keep_page_date** | llm_interpreted | yes |
| 58 | 6_llm_other | Zinc_Report.pdf | 6 | attachment | 2018-02-05 | 2021-08-11 | 2014-04-01 | 2018-02-05 | 2018-02-05 | **review** | llm_interpreted | yes |

## How to review

For each row in the CSV, fill in:

- `human_decision` — `keep_page_date`, `override` or `review`
- `human_correct` — `YES` if the system's action matches yours, else `NO`
- `human_published_at` — the date you believe is right (blank = keep current)
- `human_date_type` — publication / upload / authoring / edition / event
- `human_edition_label` — e.g. `2024-25`, where applicable
- `human_notes` — anything that explains a `NO`

The metric that matters is **false overrides**: rows where the system proposes a change and you judge the current date to be better. A stale date is recoverable; a confidently wrong one is not.
