# Date resolution — v2 vs v3

Baseline `prototype_decisions.v2.csv` against `prototype_decisions.csv`.

| metric | v2 | v3 | change |
|---|---:|---:|---:|
| total PDFs analysed | 3733 | 3733 | +0 |
| keep page date | 3697 | 3701 | +4 |
| deterministic overrides | 0 | 0 | +0 |
| LLM overrides | 1 | 19 | +18 |
| review cases | 35 | 13 | -22 |
| PDFs downloaded + sent to LLM | 315 | 315 | +0 |
| **total proposed overrides** | **1** | **19** | **+18** |

- **overrides made without reading the document** — v2: 0, v3: 0. Any non-zero value is the v1 false-positive class.

## Decisions that changed: 55

| transition | count |
|---|---:|
| `needs_manual_review -> keep_page_date` | 26 |
| `keep_page_date -> needs_manual_review` | 11 |
| `keep_page_date -> propose_override` | 11 |
| `needs_manual_review -> propose_override` | 7 |

### Overrides withdrawn (0)

Proposed by v2, no longer proposed by v3.

| filename | PDFs on page | page date | v2 proposed | v2 rule | v3 action |
|---|---:|---|---|---|---|

### Overrides added (18)

Recovered by v3.

| filename | page date | v3 proposed | evidence |
|---|---|---|---|
| Best Practices on National Inven | 2018-12-18 | 2018-09-01 | The first page text states 'SEPTEMBER 2018', indicating the publicatio |
| 2014BL18-es-women-empow.pdf | 2019-05-09 | 2019-01-07 | The first page text states '7 January 2019' as the publication date. |
| Report_Needs_Assessment_TERI_Upd | 2023-07-03 | 2023-01-01 | The first page text includes a suggested citation that states the docu |
| 2007.09-Marine-Litter-in-the-SAS | 2019-08-09 | 2007-09-01 | The first page text states 'Colombo, September 2007', indicating the p |
| COBENEFITS-Study-India-Health.pd | 2020-08-28 | 2019-10-01 | The first page text states 'October 2019 COBENEFITS STUDY', indicating |
| 20250331_pr_3851.pdf | 2025-05-30 | 2025-03-31 | The first page text includes a date stating 'New Delhi, 31 March 2025' |
| FS08_Informal-sector_updated-Nov | 2025-09-12 | 2023-11-11 | The first page text states that the factsheet was first published in S |
| Post_2015_bulletin%20and_TEDDY_l | 2018-03-10 | 2014-07-09 | The first page text states that the bulletin was presented on July 9,  |
| Tender_No_22 _Project_TERI_2024_ | 2018-04-11 | 2024-12-11 | The first page text states 'ISSUE NO. 22 DATED 11-12-2024', indicating |
| Tender_NAM_Project_TERI_2023_Aug | 2018-04-11 | 2023-08-10 | The first page text states 'ISSUE NO. 01 DATED 10-08-2023', indicating |
| 1.-MoR-circular-date-15.03.2022. | 2022-10-18 | 2022-03-15 | The document contains a date stated as 'dt.15.03.2022' which indicates |
| EI_Nashik_August2023.pdf | 2023-08-07 | 2023-01-01 | The first page text states 'January 2023 Final Report Emission Invento |
| Hindustan-Times-Chandigarh-Monda | 2018-01-09 | 2013-12-23 | The link text states 'Hindustan Times, Chandigarh, Monday, December 23 |
| Chandigarh-Tribune-Chandigarh-Mo | 2018-01-09 | 2013-12-23 | The text includes the phrase 'Chandigarh Tribune, Chandigarh, Monday,  |
| Chandigarh-Tribune-Chandigarh-Tu | 2018-01-09 | 2013-12-24 | The first page text includes the date 'TUESDAY | 24 | DECEMBER 2013',  |
| The-Pioneer-Chandigarh-Tuesday-D | 2018-01-09 | 2013-12-24 | The filename and link text both indicate a publication date of Decembe |
| India-News-Calling-Chandigarh-Mo | 2018-01-09 | 2013-12-23 | The filename and link text both indicate the document is related to 'I |
| Business-Standard-Chandigarh-Mon | 2018-01-09 | 2013-12-30 | The text includes the phrase 'Business Standard, Chandigarh, Monday, D |

### Overrides retained in both versions: 1

