# Shadow prototype — evidence-based PDF date resolution

Generated 2026-08-10 11:10 UTC. No production data modified; Document Intelligence not called.

- PDFs examined: **3779**
- handled without the LLM: **3464** (91.7%)
- required the LLM: **315** (8.3%)
- PDFs downloaded (DocInfo/head text only): **315**
- LLM calls made: **315**
- estimated prompt tokens: ~420,835; estimated cost this run: **$0.0858** ($0.15/$0.6 per 1M in/out)
- extrapolated to all 3779 corpus PDFs at this LLM rate: **$0.09**

### Action

| value | count |
|---|---:|
| `keep_page_date` | 3745 |
| `needs_manual_review` | 28 |
| `propose_override` | 6 |

### Decided by

| value | count |
|---|---:|
| `deterministic` | 3464 |
| `llm` | 315 |

### Date type

| value | count |
|---|---:|
| `publication` | 3497 |
| `unknown` | 240 |
| `event` | 22 |
| `edition` | 10 |
| `authoring` | 5 |
| `notification` | 4 |
| `upload` | 1 |

### Rule

| value | count |
|---|---:|
| `single_pdf_page` | 2016 |
| `multi_pdf_uploaded_with_page` | 644 |
| `multi_pdf_no_evidence` | 485 |
| `llm_interpreted` | 315 |
| `multi_pdf_url_month_matches` | 212 |
| `migration_cohort_no_evidence` | 107 |

### Fetch status (ambiguous cases only)

| status | count |
|---|---:|
| `ok` | 193 |
| `ConnectionError` | 65 |
| `http_404` | 17 |
| `ConnectTimeout` | 15 |
| `http_403` | 9 |
| `http_406` | 7 |
| `SSLError` | 4 |
| `http_400` | 2 |
| `ReadTimeout` | 1 |
| `http_500` | 1 |
| `too_large` | 1 |

### LLM confidence distribution

| band | count |
|---|---:|
| 0.9-1.0 | 96 |
| 0.8-0.9 | 14 |
| <0.6 | 205 |

### Proposed overrides

| filename | page PDFs | current | proposed | type | source | conf | rule |
|---|---:|---|---|---|---|---:|---|
| 20250331_pr_3851.pdf | 6 | 2025-05-30 | 2025-03-31 | publication | llm_publication | 0.90 | llm_interpreted |
| Post_2015_bulletin%20and_TEDDY_l | 12 | 2018-03-10 | 2014-07-09 | publication | llm_publication | 0.90 | llm_interpreted |
| Tender_No_22 _Project_TERI_2024_ | 70 | 2018-04-11 | 2024-12-11 | publication | llm_publication | 0.90 | llm_interpreted |
| Tender_NAM_Project_TERI_2023_Aug | 70 | 2018-04-11 | 2023-08-10 | publication | llm_publication | 0.90 | llm_interpreted |
| 1.-MoR-circular-date-15.03.2022. | 2 | 2022-10-18 | 2022-03-15 | publication | llm_publication | 0.90 | llm_interpreted |
| India-News-Calling-Chandigarh-Mo | 11 | 2018-01-09 | 2013-12-23 | publication | llm_publication | 0.90 | llm_interpreted |

### Flagged for manual review

| filename | page PDFs | rule | evidence |
|---|---:|---|---|
| Best Practices on National Inv | 1 | llm_interpreted | The first page text states 'SEPTEMBER 2018', indicating the publicatio |
| Zinc_Report.pdf | 6 | llm_interpreted | The first page text includes the phrase 'Published by The Energy and R |
| 2014BL18-es-women-empow.pdf | 2 | llm_interpreted | The first page text states '7 January 2019' as the publication date. |
| existing-commercial-building-r | 2 | llm_interpreted | The first page text includes a citation format that references the yea |
| Bending-the-Curve_Report.pdf | 6 | llm_interpreted | The phrase 'PUBLISHED BY The Energy and Resources Institute (TERI)' in |
| Direct Reduction of Iron Proce | 5 | llm_interpreted | The document includes a statement indicating it was published by The E |
| NTDC Discussion Paper on Vehic | 13 | llm_interpreted | The text states 'PUBLISHED BY The Energy and Resources Institute (TERI |
| NTDC Discussion Paper on_Emiss | 13 | llm_interpreted | The text states 'PUBLISHED BY The Energy and Resources Institute (TERI |
| NTDC Discussion Paper on_Biodi | 13 | llm_interpreted | The text states 'PUBLISHED BY The Energy and Resources Institute (TERI |
| Policy Brief Biodiesel.pdf | 13 | llm_interpreted | The first page text states the publication year as 2023. |
| Policy Brief Vehicle Scrappage | 13 | llm_interpreted | The text states 'PUBLISHED BY The Energy and Resources Institute (TERI |
| Policy Brief Fuel  Efficiency  | 13 | llm_interpreted | The phrase 'PUBLISHED BY The Energy and Resources Institute (TERI)' in |
| Handbook of clean construction | 21 | llm_interpreted | The first page text includes a citation format stating 'T E R I. 2023  |
| Report_Needs_Assessment_TERI_U | 6 | llm_interpreted | The first page text includes a suggested citation stating the document |
| 2007.09-Marine-Litter-in-the-S | 6 | llm_interpreted | The first page text states 'Colombo, September 2007', indicating the p |
| COBENEFITS-Study-India-Health. | 2 | llm_interpreted | The first page text states 'October 2019 COBENEFITS STUDY', indicating |
| doc202181311.pdf | 4 | llm_interpreted | The text states 'PUBLISHED BY AUTHORITY पयाावरण, वन और िलवायु पररवतान  |
| FS08_Informal-sector_updated-N | 2 | llm_interpreted | The first page text states that the factsheet has first been published |
| April-June2020_SB_NL.pdf | 3 | llm_interpreted | The first page text states 'April 2020 Issue 1', indicating the public |
| existing-commercial-building-r | 2 | llm_interpreted | The first page text includes a citation format that references the yea |
| Direct Reduction of Iron Proce | 5 | llm_interpreted | The document includes a statement indicating it was published by The E |
| EI_Nashik_August2023.pdf | 21 | llm_interpreted | The first page text states 'January 2023 Final Report Emission Invento |
| Hindustan-Times-Chandigarh-Mon | 11 | llm_interpreted | The link text states 'Hindustan Times, Chandigarh, Monday, December 23 |
| Chandigarh-Tribune-Chandigarh- | 11 | llm_interpreted | The text includes the phrase 'Chandigarh Tribune, Chandigarh, Monday,  |
| Chandigarh-Tribune-Chandigarh- | 11 | llm_interpreted | The first page text includes the date 'TUESDAY | 24 | DECEMBER 2013',  |

### Edition labels derived: 144

| filename | edition | date kept |
|---|---|---|
| 2017MC01-Air Quality Status of Mah | 2016-2017 | 2018-02-07 |
| 2013MC02 Air Quality Report_MPCB_2 | 2011-12 | 2018-02-07 |
| 2013MC02 Air Quality Report_MPCB_2 | 2011-12 | 2018-02-07 |
| 2013MC08 Air Quality Report_MPCB_2 | 2012-13 | 2018-02-07 |
| 2014MC02 Air Quality Report_MPCB_2 | 2013-14 | 2018-02-07 |
| 2015MC02 Air Quality Report_MPCB_2 | 2014-15 | 2018-02-07 |
| 2010WR02 Pune_ESR_2009-2010_Englis | 2009-10 | 2018-02-07 |
| 2013MC10 Nanded_ESR_2014-15.pdf | 2014-15 | 2018-02-07 |
| 2014MC06    NMMC_ESR Final Report_ | 2013-14 | 2018-02-07 |
| 2015MC04  NMMC_ESR Final Report_20 | 2014-15 | 2018-02-07 |
| 2016MC02   Kolahpur ESR 2015-16 (E | 2015-16 | 2018-02-07 |
| 2016MC05  NMMC_ESR Final Report_20 | 2015-16 | 2018-02-07 |
| 2014MC06    NMMC_ESR Final Report_ | 2013-14 | 2018-02-07 |
| 2014MC06    NMMC_ESR Final Report_ | 2013-14 | 2018-02-07 |
| 2017MC06  NMMC_ESR Final Report_20 | 2016-17 | 2018-02-07 |
| 2015MC02 Air Quality Report_MPCB_2 | 2014-15 | 2018-02-07 |
| 2016MC04-Air Quality Status of Mah | 2015-16 | 2018-02-07 |
| 2013MC06 Water Quality Report_MPCB | 2011-12 | 2018-02-07 |
| 2017MC03 Water Quality Report.pdf | 2016-17 | 2018-02-07 |
| 2012MC10 Introducing the concept o | 2013-14 | 2018-02-09 |
| 2015MC06 PROTEIN-Promotion of Nutr | 2015-16 | 2018-02-27 |
| Technical Annex of Green Steel Roa | 2022 | 2020-01-30 |
| EI_Nashik_August2023.pdf | 2023 | 2023-08-07 |
| ITEC-Brochure-2016-17.pdf | 2016-17 | 2018-01-09 |
| ITEC-Brochure-2016-17.pdf | 2016-17 | 2018-01-09 |
