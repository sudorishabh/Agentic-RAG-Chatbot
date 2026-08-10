# Shadow prototype — evidence-based PDF date resolution

Generated 2026-08-10 06:02 UTC. No production data modified; Document Intelligence not called.

- PDFs examined: **3779**
- handled without the LLM: **3464** (91.7%)
- required the LLM: **315** (8.3%)
- PDFs downloaded (DocInfo/head text only): **315**
- LLM calls made: **315**
- estimated prompt tokens: ~296,426; estimated cost this run: **$0.0671** ($0.15/$0.6 per 1M in/out)
- extrapolated to all 3779 corpus PDFs at this LLM rate: **$0.07**

### Action

| value | count |
|---|---:|
| `keep_page_date` | 3743 |
| `needs_manual_review` | 35 |
| `propose_override` | 1 |

### Decided by

| value | count |
|---|---:|
| `deterministic` | 3464 |
| `llm` | 315 |

### Date type

| value | count |
|---|---:|
| `publication` | 3483 |
| `unknown` | 259 |
| `edition` | 16 |
| `event` | 13 |
| `other` | 7 |
| `notification` | 1 |

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
| `ok` | 192 |
| `ConnectionError` | 66 |
| `http_404` | 17 |
| `ConnectTimeout` | 14 |
| `http_403` | 9 |
| `http_406` | 7 |
| `SSLError` | 5 |
| `http_400` | 2 |
| `http_500` | 1 |
| `too_large` | 1 |
| `ChunkedEncodingError` | 1 |

### LLM confidence distribution

| band | count |
|---|---:|
| 0.9-1.0 | 56 |
| <0.6 | 259 |

### Proposed overrides

| filename | page PDFs | current | proposed | type | source | conf | rule |
|---|---:|---|---|---|---|---:|---|
| doc202181311.pdf | 4 | 2021-11-10 | 2021-08-12 | publication | llm_publication | 0.90 | llm_interpreted |

### Flagged for manual review

| filename | page PDFs | rule | evidence |
|---|---:|---|---|
| Best Practices on National Inv | 1 | llm_interpreted | The first page text states 'SEPTEMBER 2018', but it does not clarify i |
| Circular-Economy-Plastics-Indi | 4 | llm_interpreted | The first page text indicates that this is a revised version of the pu |
| White_paper_E-wasteEPR.pdf | 4 | llm_interpreted | The evidence includes various dates related to the upload and authorin |
| FINAL REGISTRATION FORM 2022.p | 2 | llm_interpreted | The document contains information about registration deadlines and exa |
| Achieving Green Steel Roadmap  | 5 | llm_interpreted | The first page text includes a suggested citation with the year 2022,  |
| Policy Brief Biodiesel.pdf | 13 | llm_interpreted | The first page text states 'PUBLISHED BY The Energy and Resources Inst |
| NTDC Concept Note.pdf | 13 | llm_interpreted | The provided evidence includes upload and authoring dates, but no expl |
| Minutes of meeting Efficiency. | 13 | llm_interpreted | The document contains a meeting date of September 01, 2022, but does n |
| MoM Vehicle Scrappage Policy N | 13 | llm_interpreted | The first page text mentions a workshop held on August 24, 2022, but d |
| Summary Report - LAMP.pdf | 1 | llm_interpreted | The evidence includes various dates related to the upload and creation |
| Emission_Inventory_of_Pune.pdf | 21 | llm_interpreted | The first page text mentions 'September 2022' in the context of the re |
| Report_on_optimiztion_of_monit | 21 | llm_interpreted | The first page text mentions a preparation date of 'Sep, 2021' but doe |
| EI_Nashik_August2023.pdf | 21 | llm_interpreted | The first page text mentions 'January 2023 Final Report', but does not |
| Prioritisation of actions in P | 21 | llm_interpreted | The evidence provided includes upload and authoring dates, but no expl |
| Handbook of clean construction | 21 | llm_interpreted | The first page text includes a suggested citation format with the year |
| 21majorminerals13032018.pdf | 9 | llm_interpreted | The filename includes a date (13032018), but it does not provide a cle |
| urban_waste_water_re-use_polic | 8 | llm_interpreted | The filename includes a date (27.12.2017) but it is not clear if this  |
| 2007.09-Marine-Litter-in-the-S | 6 | llm_interpreted | The first page text mentions 'Colombo, September 2007', but it does no |
| RS-in-32-27-07-2023.pdf | 2 | llm_interpreted | The filename contains a date (27-07-2023), but it is not clear if this |
| StaticAttachment | 6 | llm_interpreted | The provided evidence includes upload and authoring dates, but no expl |
| TUGD-Brochure-2025.pdf | 43 | llm_interpreted | The filename suggests a focus on the year 2025, but there is no explic |
| Solar_Based_Electric_Mobility_ | 2 | llm_interpreted | The filename suggests a focus on 2024, but there is no explicit public |
| Jan-Feb-2024-India-Foundation- | 2 | llm_interpreted | The filename and first page text indicate the document is related to t |
| D3_Risk_perspectives_April_201 | 15 | llm_interpreted | The filename suggests a date (April 2010), but it does not provide a c |
| D8_MLG_framework_for NT_April  | 15 | llm_interpreted | The filename includes 'April 2010', but there is no clear publication  |

### Edition labels derived: 158

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
| SCAP_Booklet.pdf | September 2022 | 2020-02-11 |
| es-ludhiana.pdf | 2017-2020 | 2017-12-27 |
| Bending-the-Curve_Report.pdf | 2025 | 2018-01-01 |
| ITEC-Brochure-2016-17.pdf | 2016-17 | 2018-01-09 |
