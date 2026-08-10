# Date resolution — before / after

**v1**: upload timing (Drupal `file.created`, `/files/YYYY-MM/`) could override `published_at` on its own.  
**v2**: only a quoted, high-confidence publication statement in the document can override; upload timing routes a case for review.

| metric | v1 | v2 | change |
|---|---:|---:|---:|
| total PDFs analysed | 3733 | 3733 | +0 |
| keep page date | 3595 | 3697 | +102 |
| deterministic overrides | 130 | 0 | -130 |
| LLM overrides | 7 | 1 | -6 |
| review cases | 1 | 35 | +34 |
| PDFs downloaded + sent to LLM | 185 | 315 | +130 |
| **total proposed overrides** | **137** | **1** | **-136** |

- **false-positive candidates in v1**: 130 (every deterministic override was driven by upload timing alone, with the document unread)
- **false-positive candidates in v2**: 0 by construction — no rule can override without a quoted publication statement

## Decisions that changed: 154

| transition | count |
|---|---:|
| `propose_override -> keep_page_date` | 118 |
| `propose_override -> needs_manual_review` | 18 |
| `keep_page_date -> needs_manual_review` | 17 |
| `needs_manual_review -> keep_page_date` | 1 |

### Overrides withdrawn (136)

These had their `published_at` moved by v1 on upload timing alone. v2 keeps the page date.

| filename | PDFs on page | page date | v1 proposed | v1 rule | v2 action |
|---|---:|---|---|---|---|
| Best Practices on National Invento | 1 | 2018-12-18 | 2020-06-16 | `single_pdf_late_upload` | needs_manual_review |
| Ceramic_Report .pdf | 6 | 2018-02-05 | 2021-08-11 | `multi_pdf_upload_date` | keep_page_date |
| Glass_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | `multi_pdf_upload_date` | keep_page_date |
| Sugar_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | `multi_pdf_upload_date` | keep_page_date |
| Vegetable_Oil_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | `multi_pdf_upload_date` | keep_page_date |
| Copper_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | `multi_pdf_upload_date` | keep_page_date |
| Zinc_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | `multi_pdf_upload_date` | keep_page_date |
| 2017MC01-Air Quality Status of Mah | 1 | 2018-02-07 | 2020-02-04 | `single_pdf_late_upload` | keep_page_date |
| 2016MC04-Air Quality Status of Mah | 1 | 2018-02-07 | 2020-02-04 | `single_pdf_late_upload` | keep_page_date |
| 2017MC03 Water Quality Report.pdf | 1 | 2018-02-07 | 2020-02-04 | `single_pdf_late_upload` | keep_page_date |
| Vol II - Six micro-economic case s | 2 | 2018-04-30 | 2019-09-03 | `multi_pdf_upload_date` | keep_page_date |
| 2014BL18-es-women-empow.pdf | 2 | 2019-05-09 | 2020-11-09 | `multi_pdf_upload_date` | keep_page_date |
| Automobile_0.pdf | 8 | 2019-08-07 | 2024-05-17 | `multi_pdf_upload_date` | keep_page_date |
| Cement_0.pdf | 8 | 2019-08-07 | 2024-05-17 | `multi_pdf_upload_date` | keep_page_date |
| Container_0.pdf | 8 | 2019-08-07 | 2024-05-17 | `multi_pdf_upload_date` | keep_page_date |
| Fly Ash_0.pdf | 8 | 2019-08-07 | 2024-05-17 | `multi_pdf_upload_date` | keep_page_date |
| Parcel_0.pdf | 8 | 2019-08-07 | 2024-05-17 | `multi_pdf_upload_date` | keep_page_date |
| Steel_0.pdf | 8 | 2019-08-07 | 2024-05-17 | `multi_pdf_upload_date` | keep_page_date |
| SCAP_Booklet.pdf | 7 | 2020-02-11 | 2022-09-26 | `multi_pdf_upload_date` | keep_page_date |
| Cost-effectiveness-of -interventio | 7 | 2020-02-11 | 2021-12-09 | `multi_pdf_upload_date` | keep_page_date |
| Assessment_of_air_quality_during l | 7 | 2020-02-11 | 2021-02-02 | `multi_pdf_upload_date` | keep_page_date |
| Source_Apportionment_Study_of_ Amb | 7 | 2020-02-11 | 2021-09-03 | `multi_pdf_upload_date` | keep_page_date |
| Report_Component-I.pdf | 5 | 2020-03-12 | 2021-04-07 | `multi_pdf_upload_date` | keep_page_date |
| Report_Component-II.pdf | 5 | 2020-03-12 | 2021-04-07 | `multi_pdf_upload_date` | keep_page_date |
| MoRTH_Executive_Summary_0.pdf | 5 | 2020-03-12 | 2021-04-07 | `multi_pdf_upload_date` | keep_page_date |
| Water Efficient Measures for Resid | 13 | 2021-06-03 | 2022-03-22 | `multi_pdf_upload_date` | keep_page_date |
| Guidelines-for-Visual-Comfort.pdf | 13 | 2021-06-03 | 2021-11-25 | `multi_pdf_upload_date` | keep_page_date |
| Report-Visual-Survey.pdf | 13 | 2021-06-03 | 2021-11-25 | `multi_pdf_upload_date` | keep_page_date |
| Inside_Integrated-daylight-system. | 13 | 2021-06-03 | 2021-11-29 | `multi_pdf_upload_date` | keep_page_date |
| Thermal-Comfort-Prescription.pdf | 13 | 2021-06-03 | 2021-11-25 | `multi_pdf_upload_date` | keep_page_date |
| Circular-Economy-Plastics-India-Ro | 4 | 2021-07-26 | 2021-12-28 | `multi_pdf_upload_date` | needs_manual_review |
| White_paper_E-wasteEPR.pdf | 4 | 2022-03-15 | 2022-10-20 | `multi_pdf_upload_date` | needs_manual_review |
| Driving Equitable and Clean Mobili | 6 | 2026-02-17 | 2026-06-05 | `multi_pdf_upload_date` | keep_page_date |
| What does intercity electric mobil | 6 | 2026-02-17 | 2026-06-05 | `multi_pdf_upload_date` | keep_page_date |
| GSP-infographic.pdf | 2 | 2017-03-14 | 2018-10-11 | `multi_pdf_upload_date` | keep_page_date |
| cpcb-spatial-maping-forecasting.pd | 1 | 2017-11-05 | 2021-07-13 | `single_pdf_late_upload` | keep_page_date |
| existing-commercial-building-retro | 2 | 2017-12-27 | 2019-06-25 | `multi_pdf_upload_date` | keep_page_date |
| es-ludhiana.pdf | 1 | 2017-12-27 | 2021-07-14 | `single_pdf_late_upload` | keep_page_date |
| greening-solar-PV-value-chain.pdf | 6 | 2017-12-27 | 2018-10-31 | `multi_pdf_upload_date` | keep_page_date |
| towards-resource-efficient-ev-sect | 6 | 2017-12-27 | 2018-10-31 | `multi_pdf_upload_date` | keep_page_date |

_(96 more in the CSVs.)_

### Overrides retained in both versions: 1

