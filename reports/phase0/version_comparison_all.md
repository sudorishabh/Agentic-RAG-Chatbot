# Full-corpus comparison: v1 -> v2 -> v3 -> v3-final

- **v1** — Upload timing could override on its own (file.created, /files/YYYY-MM/).
- **v2** — Deterministic overrides removed; only a quoted publication statement can override, confidence >= 0.9.
- **v3** — Few-shot prompt added for newspaper/issue/publication forms to recover recall.
- **v3-final** — Quote must carry the date; year-only and month-only cannot invent a day; publication linkage required; date must be grounded in the document text.


## Category totals

| metric | v1 | v2 | v3 | v3-final |
|---|---:|---:|---:|---:|
| PDFs analysed | 3733 | 3733 | 3733 | 3733 |
| keep_page_date | 3595 | 3697 | 3700 | 3701 |
| review | 1 | 35 | 0 | 22 |
| deterministic overrides | 130 | 0 | 0 | 0 |
| LLM overrides | 7 | 1 | 33 | 10 |
| PDFs sent to the LLM | 185 | 315 | 315 | 315 |
| edition labels | 164 | 123 | 108 | 107 |
| **total overrides** | **137** | **1** | **33** | **10** |

## What changed at each step, and why


### v1 -> v2

_Deterministic overrides removed; only a quoted publication statement can override, confidence >= 0.9._

- decisions changed: **154**

| transition | count | class of decision |
|---|---:|---|
| `propose_override -> keep_page_date` | 118 | upload-driven override withdrawn (upload timing is now supporting evidence only) |
| `propose_override -> needs_manual_review` | 18 | override withdrawn but the divergence is still worth a human look |
| `keep_page_date -> needs_manual_review` | 17 | routed for review after upload divergence was detected |
| `needs_manual_review -> keep_page_date` | 1 | the model found no date at all, so the page date stands |

- upload-driven overrides removed: **130**
- LLM overrides withdrawn: **6**
- overrides added: **0**

  withdrawn LLM overrides:

  | filename | was proposed | reason class |
  |---|---|---|
  | Tracking_climate_finance-Primer-Se | 2019-09-12 | needs_manual_review |
  | Tender_No_22 _Project_TERI_2024_De | 2024-12-11 | keep_page_date |
  | NEP_2022_32_FINAL_GAZETTE_English. | 2023-05-18 | keep_page_date |
  | Business-Standard-Chandigarh-Monda | 2013-12-30 | needs_manual_review |
  | Clarification.pdf | 2019-10-03 | keep_page_date |
  | Hindustan-Times-Chandigarh-Monday- | 2013-12-23 | keep_page_date |

### v2 -> v3

_Few-shot prompt added for newspaper/issue/publication forms to recover recall._

- decisions changed: **58**

| transition | count | class of decision |
|---|---:|---|
| `needs_manual_review -> keep_page_date` | 26 | the model found no date at all, so the page date stands |
| `keep_page_date -> propose_override` | 23 | publication evidence recovered from the document text |
| `needs_manual_review -> propose_override` | 9 | quoted publication statement accepted |

- upload-driven overrides removed: **0**
- LLM overrides withdrawn: **0**
- overrides added: **32**

### v3 -> v3-final

_Quote must carry the date; year-only and month-only cannot invent a day; publication linkage required; date must be grounded in the document text._

- decisions changed: **23**

| transition | count | class of decision |
|---|---:|---|
| `propose_override -> needs_manual_review` | 22 | override withdrawn but the divergence is still worth a human look |
| `propose_override -> keep_page_date` | 1 | upload-driven override withdrawn (upload timing is now supporting evidence only) |

- upload-driven overrides removed: **0**
- LLM overrides withdrawn: **23**
- overrides added: **0**

  withdrawn LLM overrides:

  | filename | was proposed | reason class |
  |---|---|---|
  | Policy Brief Fuel  Efficiency Impr | 2023-01-01 | needs_manual_review |
  | EI_Nashik_August2023.pdf | 2023-01-01 | needs_manual_review |
  | Handbook of clean construction.pdf | 2023-01-01 | needs_manual_review |
  | 2007.09-Marine-Litter-in-the-SAS-R | 2007-09-01 | needs_manual_review |
  | NTDC Discussion Paper on Vehicle S | 2022-12-24 | needs_manual_review |
  | Policy Brief Biodiesel.pdf | 2023-01-01 | needs_manual_review |
  | existing-commercial-building-retro | 2019-01-01 | needs_manual_review |
  | Policy Brief Vehicle Scrappage in  | 2023-01-01 | needs_manual_review |
  | Direct Reduction of Iron Process.p | 2021-01-01 | needs_manual_review |
  | NTDC Discussion Paper on_Emission  | 2022-12-24 | needs_manual_review |
  | Bending-the-Curve_Report.pdf | 2020-01-01 | needs_manual_review |
  | Best Practices on National Invento | 2018-09-01 | needs_manual_review |
  | April-June2020_SB_NL.pdf | 2020-04-01 | keep_page_date |
  | NTDC Discussion Paper on_Biodiesel | 2022-12-24 | needs_manual_review |
  | existing-commercial-building-retro | 2019-01-01 | needs_manual_review |

## The 10 overrides in v3-final, traced through every version

| filename | v1 | v2 | v3 | v3-final |
|---|---|---|---|---|
| 20250331_pr_3851.pdf | keep | keep | override | override |
| Post_2015_bulletin%20and_TEDDY_launch. | keep | keep | override | override |
| Tender_No_22 _Project_TERI_2024_Decemb | override | keep | override | override |
| Tender_NAM_Project_TERI_2023_August_Te | keep | keep | override | override |
| 1.-MoR-circular-date-15.03.2022.pdf | keep | keep | override | override |
| Chandigarh-Tribune-Chandigarh-Monday-D | keep | review | override | override |
| Chandigarh-Tribune-Chandigarh-Tuesday- | keep | review | override | override |
| The-Pioneer-Chandigarh-Tuesday-Decembe | keep | review | override | override |
| India-News-Calling-Chandigarh-Monday-D | keep | keep | override | override |
| Business-Standard-Chandigarh-Monday-De | override | review | override | override |
