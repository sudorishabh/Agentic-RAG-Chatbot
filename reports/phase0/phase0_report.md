# Phase 0A/0B — cheap-metadata blast-radius report

Generated 2026-08-09 12:29 UTC. Read-only: no PDF was downloaded, no extraction ran, no production data was modified.

- Drupal records scanned: **8510**
- File-field PDF attachments: **2687**
- Distinct in-body PDF links: **1092**
- Catalog rows joined (`pdf_attachment`): **3174**

### Phase 0A — file-field attachments

| category | count | share |
|---|---:|---:|
| `migration_era_both_stamped` | 1119 | 41.6% |
| `dates_agree` | 633 | 23.6% |
| `minor_gap` | 439 | 16.3% |
| `migration_era_node_older` | 426 | 15.9% |
| `potential_late_upload` | 62 | 2.3% |
| `file_older_than_node` | 8 | 0.3% |
| **total** | **2687** | |

### Phase 0B — in-body PDFs

| category | count | share |
|---|---:|---:|
| `unmanaged_no_file_entity` | 529 | 48.4% |
| `external_host` | 317 | 29.0% |
| `managed_path_month` | 246 | 22.5% |
| **total** | **1092** | |

### What the rules would do on cheap metadata alone

- would move: **62** (2.3%)
- needs PDF metadata to decide: **1545**
- rule `default`: 2625
- rule `late_upload`: 62

### Gap distribution (file.created minus node.created, days)

| min | p25 | median | p75 | p90 | max |
|---:|---:|---:|---:|---:|---:|
| -760 | 0 | 0 | 28 | 3962 | 6561 |

### By bundle

| bundle | attachments | agree | late upload | migration-era | in-body |
|---|---:|---:|---:|---:|---:|
| events | 953 | 372 | 3 | 251 | 161 |
| completed_projects | 694 | 67 | 23 | 575 | 99 |
| feature_articles | 398 | 0 | 0 | 397 | 4 |
| press_release | 279 | 12 | 0 | 264 | 38 |
| policy_brief | 171 | 104 | 2 | 40 | 120 |
| ongoing_projects | 114 | 27 | 33 | 6 | 144 |
| article | 48 | 30 | 1 | 8 | 182 |
| research_papers | 22 | 16 | 0 | 4 | 8 |
| report | 8 | 5 | 0 | 0 | 2 |
| page | 0 | 0 | 0 | 0 | 319 |
| videos | 0 | 0 | 0 | 0 | 2 |
| infographics | 0 | 0 | 0 | 0 | 13 |

### Representative examples


**dates_agree**

| filename | bundle | node.created | file.created | gap | current published_at |
|---|---|---|---|---:|---|
| banni-grasslands.pdf | article | 2018-06-26 | 2018-06-26 | 0 | 2018-06-26 |
| The-Green-School-Project-Brief-Present | article | 2018-07-04 | 2018-07-04 | 0 | 2018-07-04 |
| case-study_Garhwal.pdf | article | 2018-07-12 | 2018-07-12 | 0 | 2018-07-12 |
| Post-Consumer Tetra Pak Cartons (PCCs) | article | 2018-07-24 | 2018-07-24 | 0 | 2018-07-24 |
| mining-recommendation-paper.pdf | article | 2018-08-08 | 2018-08-08 | 0 | 2018-08-08 |
| Briefing note on SB48-2 Bangkok.pdf | article | 2018-09-26 | 2018-09-26 | 0 | 2018-09-26 |

**file_older_than_node**

| filename | bundle | node.created | file.created | gap | current published_at |
|---|---|---|---|---:|---|
| Poster_Oceans Matters Phase II.pdf | ongoing_projects | 2025-12-01 | 2024-03-12 | -629 | 2025-12-01 |
| Background note_phase II Final.pdf | ongoing_projects | 2025-12-01 | 2023-11-03 | -760 | 2025-12-01 |
| Project FAQs Phase II.pdf | ongoing_projects | 2025-12-01 | 2024-10-25 | -403 | 2025-12-01 |
| Agenda.pdf | events | 2018-07-17 | 2018-07-12 | -5 | 2018-07-17 |
| NANOFORAGRI 2018.pdf | events | 2018-12-13 | 2018-12-11 | -2 | 2018-12-13 |
| Exploring Electricity Supply-Mix Scena | report | 2019-02-13 | 2019-02-08 | -5 | 2019-02-13 |

**migration_era_both_stamped**

| filename | bundle | node.created | file.created | gap | current published_at |
|---|---|---|---|---:|---|
| HAL-casestudy.pdf | article | 2018-02-02 | 2018-03-05 | 31 | 2018-02-02 |
| resource-efficiency-automobile-sector- | article | 2018-02-06 | 2018-03-05 | 27 | 2018-02-06 |
| mixed-cropping-case-study.pdf | article | 2018-02-26 | 2018-02-26 | 0 | 2018-02-26 |
| Forestry Sector in India is Net Source | article | 2018-03-03 | 2018-03-20 | 17 | 2018-03-03 |
| case-study-panaji.pdf | article | 2018-03-03 | 2018-03-03 | 0 | 2018-03-03 |
| case-study-RCC-check-dams-Assam.pdf | article | 2018-03-08 | 2018-03-08 | 0 | 2018-03-08 |

**migration_era_node_older**

| filename | bundle | node.created | file.created | gap | current published_at |
|---|---|---|---|---:|---|
| art241.pdf | feature_articles | 2000-01-01 | 2017-12-19 | 6561 | 2000-01-01 |
| art249.pdf | feature_articles | 2000-01-05 | 2017-12-19 | 6557 | None |
| art243.pdf | feature_articles | 2000-01-07 | 2017-12-19 | 6555 | None |
| art255.pdf | feature_articles | 2000-01-16 | 2017-12-19 | 6546 | None |
| art244.pdf | feature_articles | 2000-01-17 | 2017-12-19 | 6545 | None |
| art252.pdf | feature_articles | 2000-02-01 | 2017-12-19 | 6530 | 2000-02-01 |

**minor_gap**

| filename | bundle | node.created | file.created | gap | current published_at |
|---|---|---|---|---:|---|
| green-agenda.pdf | article | 2019-05-02 | 2019-05-21 | 19 | 2019-05-02 |
| Air_Quality_Report.pdf | article | 2019-06-07 | 2019-06-19 | 11 | 2019-06-07 |
| VMC-COVID_19-newsletter.pdf | article | 2020-03-26 | 2020-06-24 | 90 | 2020-03-26 |
| Nama-Newsletter-Special-Issue.pdf | article | 2020-03-26 | 2020-05-22 | 57 | 2020-03-26 |
| Nama-Newsletter.pdf | article | 2020-03-26 | 2020-05-22 | 57 | 2020-03-26 |
| e-newsletter-NAMA-project.pdf | article | 2020-03-26 | 2020-06-24 | 90 | 2020-03-26 |

**potential_late_upload**

| filename | bundle | node.created | file.created | gap | current published_at |
|---|---|---|---|---:|---|
| Best Practices on National Inventory.p | article | 2018-12-18 | 2020-06-16 | 545 | 2018-12-18 |
| Ceramic_Report .pdf | completed_projects | 2018-02-05 | 2021-08-11 | 1282 | 2018-02-05 |
| Glass_Report.pdf | completed_projects | 2018-02-05 | 2021-08-11 | 1282 | 2018-02-05 |
| Sugar_Report.pdf | completed_projects | 2018-02-05 | 2021-08-11 | 1282 | 2018-02-05 |
| Vegetable_Oil_Report.pdf | completed_projects | 2018-02-05 | 2021-08-11 | 1282 | 2018-02-05 |
| Copper_Report.pdf | completed_projects | 2018-02-05 | 2021-08-11 | 1282 | 2018-02-05 |

**in-body: external_host**

| filename | bundle | node.created | anchor | url month |
|---|---|---|---|---|
| 21majorminerals13032018.pdf | article | 2018-03-03 | The Ministry of Mines, March | - |
| Annexure213032018.pdf | article | 2018-03-03 | Mines | - |
| MMDR%20Act,%202015.pdf | article | 2018-03-03 | The Mines and Minerals (Deve | - |
| PMKKKY%20Guidelines.pdf | article | 2018-03-03 | Pradhan Mantri Khanij Kshetr | - |
| contribution%20to%20DMF%20Rules,.p | article | 2018-03-03 | Ministry of Mines notificati | - |
| Goa%20DMF%20Rules.pdf | article | 2018-03-03 | Goa | - |

**in-body: managed_path_month**

| filename | bundle | node.created | anchor | url month |
|---|---|---|---|---|
| life-on-land-exec-summary1.pdf | article | 2018-02-05 | Vol I: Macroeconomic assessm | 2018-03 |
| life-on-land-exec-summary2.pdf | article | 2018-02-05 | Vol II: Six micro-economic c | 2018-03 |
| Forestry%20Sector%20in%20India%20i | article | 2018-03-03 | Also Read: Forestry Sector i | 2018-03 |
| people-biodiversity-nagaland-repor | article | 2018-03-06 | View Report - A People's Bio | 2018-03 |
| Presentation_IGES_ISAP_2017.pdf | article | 2018-03-06 | View Presentation - The Sust | 2018-03 |
| improving-air-conditioners-in-indi | article | 2018-06-29 | here | 2018-04 |

**in-body: unmanaged_no_file_entity**

| filename | bundle | node.created | anchor | url month |
|---|---|---|---|---|
| TERI-emergency-plan-for-air-pollut | article | 2018-01-24 | 10-point Emergency Response  | - |
| waste-recycling-issues-and-opportu | article | 2018-02-23 | Presentation | - |
| waste-recycling-issues-and-opportu | article | 2018-06-15 | Here is a quick glimpse of t | - |
| energy-transitions-presentation.pd | article | 2018-08-28 | - | - |
| renewables2018_India.pdf | article | 2018-11-16 | Download presentation | - |
| Transitions-in-Indian-Electricity- | article | 2018-11-21 | TERI's estimates | - |
