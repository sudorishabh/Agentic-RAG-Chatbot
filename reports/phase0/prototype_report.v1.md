# Shadow prototype — evidence-based PDF date resolution

Generated 2026-08-09 13:50 UTC. No production data modified; Document Intelligence not called.

- PDFs examined: **3779**
- handled without the LLM: **3594** (95.1%)
- required the LLM: **185** (4.9%)
- PDFs downloaded (DocInfo/head text only): **185**
- LLM calls made: **185**
- estimated prompt tokens: ~137,747; estimated cost this run: **$0.0340** ($0.15/$0.6 per 1M in/out)
- extrapolated to all 3779 corpus PDFs at this LLM rate: **$0.03**

### Action

| value | count |
|---|---:|
| `keep_page_date` | 3641 |
| `propose_override` | 137 |
| `needs_manual_review` | 1 |

### Decided by

| value | count |
|---|---:|
| `deterministic` | 3594 |
| `llm` | 185 |

### Date type

| value | count |
|---|---:|
| `publication` | 3472 |
| `upload` | 130 |
| `edition` | 100 |
| `unknown` | 58 |
| `event` | 11 |
| `authoring` | 8 |

### Rule

| value | count |
|---|---:|
| `single_pdf_page` | 2016 |
| `multi_pdf_uploaded_with_page` | 644 |
| `multi_pdf_no_evidence` | 485 |
| `multi_pdf_url_month_matches` | 212 |
| `llm_interpreted` | 185 |
| `migration_cohort_no_evidence` | 107 |
| `multi_pdf_upload_date` | 103 |
| `multi_pdf_url_month` | 18 |
| `single_pdf_late_upload` | 9 |

### Fetch status (ambiguous cases only)

| status | count |
|---|---:|
| `ConnectionError` | 65 |
| `ok` | 65 |
| `http_404` | 16 |
| `ConnectTimeout` | 13 |
| `http_403` | 10 |
| `http_406` | 7 |
| `SSLError` | 5 |
| `http_400` | 2 |
| `http_500` | 1 |
| `too_large` | 1 |

### LLM confidence distribution

| band | count |
|---|---:|
| 0.9-1.0 | 65 |
| 0.8-0.9 | 83 |
| 0.6-0.8 | 4 |
| <0.6 | 33 |

### Proposed overrides

| filename | page PDFs | current | proposed | type | source | conf | rule |
|---|---:|---|---|---|---|---:|---|
| Best Practices on National Inven | 1 | 2018-12-18 | 2020-06-16 | upload | file_created | 0.75 | single_pdf_late_upload |
| Ceramic_Report .pdf | 6 | 2018-02-05 | 2021-08-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Glass_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Sugar_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Vegetable_Oil_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Copper_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Zinc_Report.pdf | 6 | 2018-02-05 | 2021-08-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| 2017MC01-Air Quality Status of M | 1 | 2018-02-07 | 2020-02-04 | upload | file_created | 0.75 | single_pdf_late_upload |
| 2016MC04-Air Quality Status of M | 1 | 2018-02-07 | 2020-02-04 | upload | file_created | 0.75 | single_pdf_late_upload |
| 2017MC03 Water Quality Report.pd | 1 | 2018-02-07 | 2020-02-04 | upload | file_created | 0.75 | single_pdf_late_upload |
| Vol II - Six micro-economic case | 2 | 2018-04-30 | 2019-09-03 | upload | file_created | 0.85 | multi_pdf_upload_date |
| 2014BL18-es-women-empow.pdf | 2 | 2019-05-09 | 2020-11-09 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Automobile_0.pdf | 8 | 2019-08-07 | 2024-05-17 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Cement_0.pdf | 8 | 2019-08-07 | 2024-05-17 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Container_0.pdf | 8 | 2019-08-07 | 2024-05-17 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Fly Ash_0.pdf | 8 | 2019-08-07 | 2024-05-17 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Parcel_0.pdf | 8 | 2019-08-07 | 2024-05-17 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Steel_0.pdf | 8 | 2019-08-07 | 2024-05-17 | upload | file_created | 0.85 | multi_pdf_upload_date |
| SCAP_Booklet.pdf | 7 | 2020-02-11 | 2022-09-26 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Cost-effectiveness-of -intervent | 7 | 2020-02-11 | 2021-12-09 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Assessment_of_air_quality_during | 7 | 2020-02-11 | 2021-02-02 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Source_Apportionment_Study_of_ A | 7 | 2020-02-11 | 2021-09-03 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Report_Component-I.pdf | 5 | 2020-03-12 | 2021-04-07 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Report_Component-II.pdf | 5 | 2020-03-12 | 2021-04-07 | upload | file_created | 0.85 | multi_pdf_upload_date |
| MoRTH_Executive_Summary_0.pdf | 5 | 2020-03-12 | 2021-04-07 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Water Efficient Measures for Res | 13 | 2021-06-03 | 2022-03-22 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Guidelines-for-Visual-Comfort.pd | 13 | 2021-06-03 | 2021-11-25 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Report-Visual-Survey.pdf | 13 | 2021-06-03 | 2021-11-25 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Inside_Integrated-daylight-syste | 13 | 2021-06-03 | 2021-11-29 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Thermal-Comfort-Prescription.pdf | 13 | 2021-06-03 | 2021-11-25 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Circular-Economy-Plastics-India- | 4 | 2021-07-26 | 2021-12-28 | upload | file_created | 0.85 | multi_pdf_upload_date |
| White_paper_E-wasteEPR.pdf | 4 | 2022-03-15 | 2022-10-20 | upload | file_created | 0.85 | multi_pdf_upload_date |
| Driving Equitable and Clean Mobi | 6 | 2026-02-17 | 2026-06-05 | upload | file_created | 0.85 | multi_pdf_upload_date |
| What does intercity electric mob | 6 | 2026-02-17 | 2026-06-05 | upload | file_created | 0.85 | multi_pdf_upload_date |
| GSP-infographic.pdf | 2 | 2017-03-14 | 2018-10-11 | upload | file_created | 0.85 | multi_pdf_upload_date |
| cpcb-spatial-maping-forecasting. | 1 | 2017-11-05 | 2021-07-13 | upload | file_created | 0.75 | single_pdf_late_upload |
| existing-commercial-building-ret | 2 | 2017-12-27 | 2019-06-25 | upload | file_created | 0.85 | multi_pdf_upload_date |
| es-ludhiana.pdf | 1 | 2017-12-27 | 2021-07-14 | upload | file_created | 0.75 | single_pdf_late_upload |
| greening-solar-PV-value-chain.pd | 6 | 2017-12-27 | 2018-10-31 | upload | file_created | 0.85 | multi_pdf_upload_date |
| towards-resource-efficient-ev-se | 6 | 2017-12-27 | 2018-10-31 | upload | file_created | 0.85 | multi_pdf_upload_date |

### Flagged for manual review

| filename | page PDFs | rule | evidence |
|---|---:|---|---|
| D5_NT_Development_in_India_Apr | 15 | llm_interpreted | The filename includes 'Apri_2010', suggesting a publication date in Ap |

### Edition labels derived: 199

| filename | edition | date kept |
|---|---|---|
| 2017MC01-Air Quality Status of Mah | 2016-17 | 2020-02-04 |
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
| 2016MC04-Air Quality Status of Mah | 2015-16 | 2020-02-04 |
| 2013MC06 Water Quality Report_MPCB | 2011-12 | 2018-02-07 |
| 2012MC10 Introducing the concept o | 2013-14 | 2018-02-09 |
| 2015MC06 PROTEIN-Promotion of Nutr | 2015-16 | 2018-02-27 |
| ITEC-Brochure-2016-17.pdf | 2016-17 | 2018-01-09 |
| ITEC-Brochure-2016-17.pdf | 2016-17 | 2018-01-09 |
| TERI-ITEC_2017-18.pdf | 2017-18 | 2018-01-09 |
| TERI-ITEC_2017-18.pdf | 2017-18 | 2018-01-09 |
| TERI-ITEC_2017-18.pdf | 2017-18 | 2018-01-09 |
