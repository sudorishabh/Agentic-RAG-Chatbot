# TERI organisational chatbot - gold/reference set for the 121 evaluation questions (v2, independently judged and corrected) (v2, independently judged and corrected)

- **Question source**: `PROMPTS FOR TERI CHATBOT.docx` (121 questions, extracted verbatim)
- **Corpus snapshot**: 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17
- **Reference date for all current-state answers**: 2026-08-19
- **Stores consulted (read-only)**: MySQL `arc_db` (11,991 documents / 1,374 assertions / 2,451 entities), Qdrant `documents` (152,815 chunks, full-text index on `chunk_text`), Neo4j (1,071 Project + 524 Organization + 131 Person entities, 1,348 claims)
- **Not used as evidence**: chatbot output, LLM-generated abstracts in `documents_enrichment`, general world knowledge
- **Version**: v2. The 87 GOLD_VERIFIED entries were independently re-verified against the live stores; 23 were corrected. Baseline preserved as `organization_121_gold_v1_original.json`; per-entry audit trail in `organization_121_gold_corrections.md`; judgement in `organization_121_gold_judgement.md`.
- **Version**: v2. The 87 GOLD_VERIFIED entries were independently re-verified against the live stores; 23 were corrected. Baseline preserved as `organization_121_gold_v1_original.json`; per-entry audit trail in `organization_121_gold_corrections.md`; judgement in `organization_121_gold_judgement.md`.

## 1. Summary

| Metric | Value |
| --- | --- |
| Questions extracted | 121 |
| Exact duplicates | 0 |
| Near-duplicate pairs flagged | 7 |
| GOLD_VERIFIED | 87 |
| NEEDS_HUMAN_REVIEW | 33 |
| NO_SUPPORTED_ANSWER | 1 |

### Confidence (GOLD_VERIFIED only)

| Confidence | Count |
| --- | --- |
| HIGH | 12 |
| MEDIUM | 72 |
| LOW | 3 |

### Breakdown by question type

| Answer type | Total | GOLD_VERIFIED | NEEDS_HUMAN_REVIEW | NO_SUPPORTED_ANSWER |
| --- | --- | --- | --- | --- |
| narrative/summary | 48 | 44 | 4 | 0 |
| aggregation/list | 25 | 16 | 9 | 0 |
| factual | 14 | 11 | 3 | 0 |
| factual / procedural | 8 | 4 | 3 | 1 |
| person lookup | 5 | 1 | 4 | 0 |
| relationship / aggregation | 3 | 0 | 3 | 0 |
| aggregation/count | 2 | 2 | 0 | 0 |
| aggregation/list + time-range | 2 | 1 | 1 | 0 |
| factual / aggregation | 2 | 2 | 0 | 0 |
| factual / definitional | 2 | 1 | 1 | 0 |
| comparison | 1 | 0 | 1 | 0 |
| comparison / aggregation | 1 | 0 | 1 | 0 |
| current-state / count | 1 | 1 | 0 | 0 |
| factual + aggregation | 1 | 1 | 0 | 0 |
| factual + narrative | 1 | 1 | 0 | 0 |
| historical/narrative | 1 | 1 | 0 | 0 |
| location/city + aggregation | 1 | 0 | 1 | 0 |
| location/city + factual | 1 | 1 | 0 | 0 |
| person lookup / aggregation | 1 | 0 | 1 | 0 |
| person lookup / factual | 1 | 0 | 1 | 0 |

## 2. How to use this gold set

- `expected_facts` is the grading unit for narrative questions: score factual coverage and correctness against these statements, not string overlap with `gold_answer`.
- For aggregation/count questions the `mysql-derivation` entries in `source_ids` are the reproducible definition of the gold count; re-run them if the corpus is re-ingested.
- Every `document_ids` value is a live `documents.document_id`; every `claim_ids` value is a live `documents_assertion.claim_id`. Both were validated when this file was generated.
- `NEEDS_HUMAN_REVIEW` means *do not score this question automatically yet* - the `notes` field states exactly what a human has to decide.
- Current-state answers are snapshot-relative. Fix the reference date at 2026-08-19 when evaluating, or regenerate.

## 3. Corpus-level evidence gaps that shape this gold set

These are structural, not incidental, and explain most `NEEDS_HUMAN_REVIEW` labels.

1. **No staff or expert directory.** The only `people` nodes are 8 Governing Council profiles. Expertise, designations and current employment are recorded nowhere. Affects Q006, Q114-Q118, Q120 (and partially Q116).
2. **The knowledge graph covers completed projects only.** All 1,374 assertions and all 1,071 `PROJECT` entities derive from `completed_projects` CMS fields; `field_ongoing_sponsors` and `field_ongoing_pi_name` were never promoted to claims. Predicate coverage is FUNDED_BY 957, LED_BY 416, PARTNER_OF **1**. Affects Q025-Q039 and Q034 in particular.
3. **Claim validity effectively ends in 2021.** Only 5 of 1,374 assertions have `valid_until` in 2022 or later (max 2025-03-31), so no current-state relationship question can be answered from the graph.
4. **No SDG-to-project or SDG-to-publication mapping.** `documents_theme` has no SDG values; `documents_tag` has 23 `SDGs` + 17 `SDG` tags plus free-text compounds. Affects Q031, Q032.
5. **No geography model.** No store records project states, districts or cities; the only geography field, `field_ongoing_country_tmp`, is NULL on 486 of 594 ongoing projects. Affects Q033, Q037.
6. **No project-to-publication linkage.** Policy briefs and reports are independent CMS nodes with no back-reference to the producing project, and no such graph predicate exists. Affects Q038.
7. **TERI School of Advanced Studies is not in the corpus.** Zero ingested URLs on the `terisas.ac.in` domain; no programmes, admissions or curriculum. Affects Q103-Q106.
8. **No engagement/access processes for labs or collaboration.** The corpus states what services and laboratories exist but not how to engage them (no sample submission, price list, application form or proposal route). Affects Q039, Q094, Q116, Q120 and weakens Q082.
9. **No EIA service.** No service node, page or title covers environmental impact assessment. Affects Q087.
10. **Definitional questions are unsupported.** Full-text probes found no TERI definition of carbon markets/credits (Q054) and only a plastics-scoped, partly externally attributed definition of circular economy (Q072).
11. **`published_at` is partly an ingestion artefact.** Large clusters of legacy nodes carry 2017-12-28, 2018-01-09 and 2018-01-11 timestamps, so date-ordered answers are only trustworthy at the recent end of the range.
12. **Third-party news is mixed into the corpus.** 1,652 `news` nodes include coverage of ministers' and other organisations' statements. An answer that attributes those to TERI is wrong even though the text is in the corpus.

## 4. Suspicious or contradictory source data

| Where | Issue | Affects |
| --- | --- | --- |
| `/mission-and-goals` (d7744c0b) vs `/history` (6f3c7dea) | Pachauri's departure: "Executive Vice-Chairman until 2017" vs "demitted office as the executive vice chairman in March 2016" | Q002 |
| `/mission-and-goals` (d7744c0b) vs Ratings & Certification service (3e27858c) | GRIHA: TERI "developed and currently administers" vs "administered and promoted by GRIHA Council", "jointly developed by MNRE and TERI in 2007" | Q004, Q080 |
| Centres of Excellence hub (98ad60e0) vs standalone CoE pages | Hub lists 9 centres but the site also has pages for the DBT-TERI CoE in Advanced Biofuels (5b31ce53) and the CoE for Sustainable Habitats (7c8f0a6a) | Q004 |
| `/mission-and-goals` vs `/contact` | Regional-centre list: 7 cities vs 9 offices + TERI SAS; Goa office address is Alto-St. Cruz/Tiswadi, not Panaji town | Q005 |
| `documents_author` for 08b5053a | Author stored as the literal email `reetas@teri.res.in` | Q119 |
| `documents_author` generally | Un-normalised name-order duplicates (`Mandal Shovon`, `Agrawal Ruchi` alongside `Dr Ruchi Agrawal`); `TERI Web Desk` appears as an author 59 times | Q114-Q119 |
| `documents_tag` | Free-text compound tags stored as single values (e.g. `SDG 12;  Sustainable Consumption and Production;  SCP;  Sustainable Development  India`); no `ESG` tag at all | Q031, Q032, Q057, Q118 |
| Annual-report attachments | Every edition (2015-16 to 2024-25) hangs off one Drupal node, so all share the same title and `published_at`; the year is only in the filename | Q111 |
| `documents` titles | 8 `completed_projects` / `report` rows are titled just "Download" or "Publication"; several `report` nodes carry mojibake (`India\ufffds Pathway`) | general retrieval |
| `bundle='ongoing_projects'` | Start dates run 2017-2026 with no end-date field, so "ongoing" is a CMS classification, not verified activity | Q025-Q037 |

## 5. Duplicate and near-duplicate questions

No two questions are byte-identical or identical after normalisation, so there are **0 exact duplicates**. The table below lists pairs surfaced by automated token overlap (Jaccard over content words, threshold 0.5). Only some are true semantic duplicates - the rest are merely lexically similar and must be graded independently.

| Pair | Jaccard | Verdict | Questions |
| --- | --- | --- | --- |
| Q018 / Q057 | 0.57 | **semantic duplicate** - same evidence base, gold answers deliberately aligned | "What research is TERI conducting on climate finance?" <br> "What research is TERI doing on climate finance and ESG?" |
| Q017 / Q110 | 0.5 | lexical similarity only - distinct questions, grade separately | "What policy recommendations has TERI recently developed?" <br> "What policy briefs has TERI recently published?" |
| Q020 / Q048 | 0.5 | **semantic duplicate** - same evidence base, gold answers deliberately aligned | "What research is TERI undertaking on industrial decarbonization?" <br> "What is TERI's contribution to industrial decarbonization?" |
| Q025 / Q039 | 0.5 | lexical similarity only - distinct questions, grade separately | "What are TERI's ongoing projects?" <br> "How can organizations collaborate with TERI on ongoing projects?" |
| Q031 / Q032 | 0.5 | **semantic duplicate** - same evidence base, gold answers deliberately aligned | "Which TERI projects contribute to SDG 7 (Affordable and Clean Energy)?" <br> "Which TERI projects contribute to SDG 13 (Climate Action)?" |
| Q096 / Q097 | 0.5 | lexical similarity only - distinct questions, grade separately | "What training programmes and workshops does TERI offer?" <br> "Are there any upcoming TERI training programmes?" |
| Q097 / Q102 | 0.5 | lexical similarity only - distinct questions, grade separately | "Are there any upcoming TERI training programmes?" <br> "What international training programmes are conducted by TERI?" |

Additional semantically overlapping groups found by manual review (below the token threshold but sharing an evidence base, so their gold answers were deliberately kept consistent): Q041/Q045 (energy storage - Q041 battery-specific, Q045 broader), Q023/Q060/Q089 (policy tools / sustainability frameworks / assessment tools), Q058/Q077/Q088 (reducing footprint / industrial circular practices / achieving resource efficiency), Q062/Q063/Q064 (water conservation / water management solutions / wastewater reuse), Q090/Q092/Q093/Q095 (laboratory testing and analytical capabilities), Q015/Q065 (sustainable / climate-smart agriculture), Q103/Q105 (sustainability courses - both NEEDS_HUMAN_REVIEW for the same reason), Q114-Q118 (expert lookups - all NEEDS_HUMAN_REVIEW for the same structural reason).

## 6. Questions requiring human review

| ID | Question | Answer type | Why |
| --- | --- | --- | --- |
| Q006 | Who are TERI's leading experts and researchers? | person lookup / aggregation | NO STAFF/EXPERT DIRECTORY IN THE CORPUS. The only ingested `people` nodes are eight Governing Council profiles (Dr Vibha Dhawan, Mr M S Unnikrishnan, Mr Madhu S Nair, Mr Mahendra Singhi, Mr Nitin Desai, Mr R Mukundan, Mr Siddharth Sharma, Ms Vaishali Nigam Sinha) - governance, not 'experts and researchers'. Publication authorship (documents_author, 971 distinct names) and project PI names are derivable proxies but the corpus records no designations, expertise areas or current-employment status, so no closed or reliable answer set can be established. A human must decide whether the gold answer is (a) the Governing Council, (b) a derived author list, or (c) 'the corpus cannot answer this'. |
| Q008 | What national and international partnerships does TERI maintain? | relationship / aggregation | NO AUTHORITATIVE PARTNER LIST. The corpus has no partners/collaborators page. Funders are recorded per-project (field_ongoing_sponsors / field_completed_sponsors, the latter promoted to 957 FUNDED_BY claims over 498 distinct organisations), but funder is not the same relation as partner, and the graph holds exactly ONE PARTNER_OF assertion. Individual MoU press releases exist (USGBC, GIZ, NABARD, RBI, GCCA, Rajasthan Renewable Energy Corporation, Mahindra, CONCOR, Chambal Fertilisers, Hindustan Zinc, Ion Exchange, Methanol Institute, POSOCO, REMCL, SCGJ, Vedanta, VNV, Bisleri, FNI/INTASAVE-CARIBSAVE, British Council/HSBC, ICIMOD/NTNC, IGES, Emerson) but no closed set can be established and 'maintains' (present tense) cannot be verified for any of them. |
| Q013 | Can you summarize TERI's recent reports on climate change and energy policy? | narrative/summary | AMBIGUOUS SCOPE. 'Recent' is undefined and the question asks for a multi-report summary. The corpus holds 247 policy-brief nodes plus 624 research papers and 8 report nodes with no 'recent'/'flagship' marker, and no authoritative digest document. A defensible gold requires a human to fix the window (e.g. published_at >= 2025-08-19) and the report classes in scope. Candidate anchors listed in document_ids are the most recent climate/energy policy briefs. |
| Q017 | What policy recommendations has TERI recently developed? | aggregation/list | 'Recently' is undefined, and 'policy recommendations' has no structured marker: recommendations live inside policy briefs, discussion papers, press releases and project pages with no field distinguishing a recommendation from a finding. A closed answer set cannot be derived. Most recent policy briefs in the snapshot: Battery Assembly and Container Testing (2026-08-11), Solar Thermal Energy for Industrial Decarbonization (2026-08-05), Sustainable Land Futures for Utility-Scale RE (2026-07-31), Tenure Dynamics in Rajasthan Solar Land Procurement (2026-07-31), Fly Ash Utilization and Transportation (2026-07-21), Unlocking Solar at Scale / Agrivoltaics (2026-07-06), Towards Cleaner Freight in Delhi (2026-06-29), Circular Economy of End-of-Life Vehicles (2026-06-16). |
| Q022 | What are TERI's most impactful research contributions in the last five years? | comparison / aggregation | UNANSWERABLE AS ASKED. 'Most impactful' is a value judgement and the corpus contains no impact ranking, citation counts, outcome metrics or evaluation scores. A five-year window (2021-08-19..2026-08-19) is computable over published_at, but nothing in any store orders results by impact. The 'Creating Impacts, Transforming Lives' publication is TERI's own curated success-story set but is not scoped to the last five years. A human must define the impact criterion before this can be gold. |
| Q026 | Which renewable energy projects is TERI currently implementing? | aggregation/list | NO CLOSED SET DERIVABLE. There is no 'renewable energy' facet on projects: the nearest CMS themes are 'Electricity and Renewables' (5 ongoing nodes), 'Energy' (44) and 'Energy Access' (10), none of which means 'renewable energy project'. Keyword matching over titles is not authoritative and 'currently implementing' cannot be verified (no project end dates). A human must define the inclusion rule. |
| Q028 | What projects support sustainable agriculture and rural livelihoods? | aggregation/list | TWO-PART QUESTION, ONE FACET. 'Sustainable Agriculture' is a CMS theme (41 ongoing nodes) but 'rural livelihoods' is not a theme, tag facet or programme; livelihood projects sit under Social Transformation, Forest & Biodiversity and Environment and Public Health. The union is not derivable, so a human must fix the scope. |
| Q030 | What projects focus on sustainable urban development? | aggregation/list | AMBIGUOUS THEME MAPPING. 'Sustainable urban development' maps to no single CMS facet; it plausibly spans Sustainable Habitat (12 ongoing), Cities (7), Buildings (19) and Transport (20), plus urban air-quality and urban-waste projects filed under Air and Waste. Any single number would be an arbitrary choice. A human must fix the scope. |
| Q031 | Which TERI projects contribute to SDG 7 (Affordable and Clean Energy)? | aggregation/list | NO SDG-TO-PROJECT MAPPING EXISTS IN ANY STORE. documents_theme carries no SDG values; documents_tag has only 23 'SDGs' / 17 'SDG' tags plus a handful of free-text compounds, none of which map projects to SDG 7; Neo4j holds no SDG nodes. The SDG 7 page (0f23e106) is about the SDG 7 - sustainable agriculture policy interface, not a project list. Any list a chatbot returns would be an inference, not a corpus fact. |
| Q032 | Which TERI projects contribute to SDG 13 (Climate Action)? | aggregation/list | Same structural gap as Q031: no SDG-to-project mapping in MySQL, Neo4j or Qdrant payloads. The SDG 13 page (397b8e72) covers the SDG 13 - sustainable agriculture policy interface only. One research paper explicitly evaluates contributions to SDG 13 ('Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13') but that is a publication, not a project set. |
| Q033 | What are TERI's current international collaborative projects? | aggregation/list | GEOGRAPHY FIELD IS 82% EMPTY. field_ongoing_country_tmp is NULL on 486 of 594 ongoing projects, so no reliable international set can be derived; only three rows name a non-India country. Individually verifiable international projects exist (Climate Skills - Seeds for a Transition across India/Brazil/Mexico/Indonesia/Vietnam with British Council and HSBC; StoREin Indo-German energy storage with GIZ, BMUKN, MNRE, Fraunhofer IEE and IIT Bombay; Renewable Energy Transition in South Asia; rangeland degradation costing for the Kingdom of Saudi Arabia) but completeness cannot be established. |
| Q034 | Who are the partners associated with TERI's major projects? | relationship / aggregation | 'MAJOR' IS UNDEFINED AND THE PARTNER RELATION IS ESSENTIALLY ABSENT. The claim store has exactly one PARTNER_OF assertion; what it does hold is 957 FUNDED_BY (498 distinct funder organisations) and 416 LED_BY (137 distinct PIs) claims, all extracted from completed_projects CMS fields, with valid_until values that effectively stop in 2021 (only 5 claims end 2022 or later). Funder is not partner, ongoing-project sponsors were never promoted to claims, and no size or importance attribute exists to select 'major' projects. |
| Q036 | What are the expected outcomes and impacts of key TERI projects? | narrative/summary | 'KEY PROJECTS' IS UNDEFINED. Individual ongoing-project pages do state aims and expected activities verbatim (e.g. 'Accelerating Industrial Decarbonisation in India' lists three activities and a 2024 roadmap target; Climate Skills reports 500+ youth engaged and a 130-participant Phase II), but there is no importance ranking, no structured outcome/indicator field and no completion reporting, so neither the project selection nor the outcome set can be established. A human must nominate the projects in scope. |
| Q037 | Which states and regions are covered under TERI's current projects? | location/city + aggregation | NO STRUCTURED SUB-NATIONAL GEOGRAPHY ANYWHERE. Neither documents nor documents_tag nor documents_theme nor the Neo4j projection models locations; the Qdrant payload has no geography field. State names appear only inside free-text project titles and bodies (e.g. Karnataka, Uttarakhand, Andhra Pradesh, Maharashtra, Assam, Punjab, Haryana, Odisha, Manipur, Gujarat, Rajasthan, Telangana, Madhya Pradesh, West Bengal, Uttar Pradesh, Delhi, Goa, Bhutan), so a coverage answer would be an unverifiable text-mining result. Per the brief's Step 8 this is NOT marked unsupported merely because Neo4j cannot answer it - it is unsupported because no store records project geography at all. |
| Q038 | What policy briefs or reports have emerged from TERI projects? | relationship / aggregation | NO PROJECT-TO-PUBLICATION LINKAGE IN THE DATA MODEL. Policy briefs (247 nodes) and reports exist as independent CMS nodes with no field pointing back to the project that produced them, and the graph has no such predicate. A few project pages announce a report launch in their own title (e.g. 'Launch of report Practices and Solutions: Accelerating Indian Industry Decarbonisation'), but that is incidental, not a derivable mapping. |
| Q039 | How can organizations collaborate with TERI on ongoing projects? | factual / procedural | NO COLLABORATION/PARTNERSHIP PROCESS PAGE. The corpus has no 'work with us', 'collaborate' or 'call for proposals' page. Adjacent evidence: TERI Council for Business Sustainability membership with stated benefits and member services (b48f22b0, 4a4b782f), the Areas of Work page's 'consultancy & advisory' and 'strategy development for corporates' lines (8937e1db), and the general contact mailbox@teri.res.in (2a2e9a77). Whether that constitutes the gold answer to 'collaborate on ongoing projects' is a judgement call for a human; see Q121 which is answerable at organisation level. |
| Q047 | What research is TERI undertaking on carbon capture, utilization and storage? | narrative/summary | PRESENT-TENSE CLAIM NOT SUPPORTABLE. The question asks what TERI is UNDERTAKING on CCUS. The corpus contains: one COMPLETED project, 'Support for Research and Review of Preliminary Results for carbon capture and storage - Global CCS Institute' (published 2017); a 2026 opinion piece 'From budget provision to national capability: Why India's CCUS commitment matters'; a research paper on the role of woody biomass in carbon capture, circular bioeconomy and biomanufacturing (2023); and CCUS treated as one option inside the cement decarbonisation roadmap and net-zero event reports. There is NO ongoing CCUS project node and no CCUS programme, centre or service. A human must decide whether the commentary and cement-roadmap treatment constitute 'research TERI is undertaking'. |
| Q054 | What are carbon markets and carbon credits? | factual / definitional | DEFINITION NOT IN THE CORPUS. Targeted full-text probes for definitional phrasings ('carbon credit is a', 'carbon market is a', 'one carbon credit', 'carbon credits are') returned no definitional passage. What the corpus DOES support is TERI's carbon-market WORK: 'Achieving a Just Transition in India with an Effective Carbon Credit Trading Scheme'; voluntary carbon market projects with FPOs for agroforestry plantations in Saharanpur, Kanpur Forest Circle and Gorakhpur; a forestry carbon-credit roadmap for Uttarakhand under RECAP4NDC; and 60 'Carbon market'-tagged documents. Answering the definitional half would require general world knowledge, which this gold-set phase forbids. A human must decide whether a general definition is acceptable. |
| Q078 | How does TERI support sustainable materials management? | narrative/summary | TERM NOT USED BY TERI. 'Sustainable materials management' does not appear as a programme, service, theme or tag; the phrase is an external framing. Adjacent evidence exists but pulls in different directions: sustainable BUILDING materials R&D (Research & Innovation service; energy-efficient building materials directory; 'Sustainable Building Materials: Accelerating the journey towards low carbon development'), plastics material flow analysis, alternate packaging materials support, waste-derived nanomaterials, and resource-efficiency/material-productivity indicator work. Which of these the question means is a judgement call a human must make; scoring an answer against the wrong grouping would be unfair. |
| Q081 | What is the difference between LEED and GRIHA ratings? | comparison | NO COMPARISON EXISTS IN THE CORPUS. A full-text co-occurrence scroll for chunks containing both 'LEED' and 'GRIHA' returns only incidental joint mentions - lists of rating systems ('In India GRIHA, LEED, IGBC cater to...'), buildings holding both certifications (Indira Paryavaran Bhawan: LEED India Platinum + GRIHA 5-star), urban-service indicators counting GRIHA- and LEED-certified buildings separately, and TERI's own service note that its team facilitates LEED accreditation (LEED India NC, LEED India CS) while it 'assists and administers GRIHA, an indigenous green building rating system for buildings, developed at TERI'. Partial distinguishing facts ARE supported (GRIHA is India's indigenous/national system developed by TERI with MNRE in 2007 and administered by GRIHA Council; LEED is the U.S. Green Building Council's system, with India the third-largest LEED market outside the U.S.), but no criteria-level, scoring-level or scope-level comparison is documented. A human must decide whether the origin/ownership contrast is an acceptable gold answer. |
| Q087 | Does TERI provide support for environmental impact assessments? | factual | NO EIA SERVICE DOCUMENTED. Title search for 'environmental impact assessment' / 'environmental clearance' across website nodes returns nothing, and none of the 30 service nodes offers EIA. The nearest evidence is oblique: the Policy intervention and analysis service states 'the manual for environmental clearance of large construction for the Ministry of Environment and Forests, Government of India has also been developed at CRSBS'; the Environmental Design & Technical Advisory service assesses 'environmental and economic impacts' of design using simulation tools; and third-party EIA work appears inside project PDFs (e.g. an ARIAS Society/APART environmental-impact-assessment section) that is not TERI's own offering. Whether TERI 'provides support for environmental impact assessments' cannot be established from the corpus. |
| Q094 | How can organizations utilize TERI's laboratory facilities? | factual / procedural | NO ACCESS PROCESS DOCUMENTED. The corpus states WHAT the laboratories test (water, soil, sludge; air quality; materials/thermal properties) but nowhere states HOW an external organisation engages them: no sample-submission procedure, application form, laboratory contact person, price list, turnaround time or terms. By contrast the LIBRARY (KRC) does publish a membership route (membership open to researchers, NGO staff, government officials, corporate employees, students, teachers, consultants and policy-makers; forms at the library help desk or downloadable), which is an adjacent but different facility. A human must decide whether 'contact mailbox@teri.res.in' is an acceptable gold answer. |
| Q101 | Does TERI conduct training programmes for NGOs and civil society organizations? | factual | EVIDENCE TOO THIN. The corpus contains only: a 2018 civil-society workshop on 'Reforming Energy Subsidies' conducted with IISD; an article 'Evaluation and Rating of NGOs'; and the KRC library statement that membership is open to 'staff of non-governmental organizations' among others. TERI's Capacity Building service lists architects, engineers, urban planners and policy makers as its audiences - not NGOs or civil-society organisations. There is no NGO/civil-society training programme documented, so neither 'yes' nor 'no' can be gold. A human must decide. |
| Q103 | What sustainability courses are available through TERI? | aggregation/list | AMBIGUOUS AND NO CATALOGUE. 'Sustainability courses available through TERI' could mean (a) TERI's professional training and certificate programmes, or (b) degree programmes at TERI School of Advanced Studies - a separate deemed institution whose website (terisas.ac.in) is NOT in this corpus. Under reading (a) the corpus holds individual programme records but no current course catalogue and no availability status; under reading (b) the corpus holds no programme information at all. A human must fix the reading before this can be gold. |
| Q104 | Are there academic programmes offered by TERI School of Advanced Studies (TERI SAS)? | factual | TERI SAS CONTENT IS NOT IN THE CORPUS. The corpus confirms TERI School of Advanced Studies EXISTS as a distinct institution - it has an address (Plot No. 10, Institutional Area, Vasant Kunj, New Delhi - 110 070), a phone number, a registrar (registrar@terisas.ac.in, contact person Col. B Venkat (Retd.)), and a Vice-Chancellor post (Dr Vibha Dhawan led TERI SAS as Vice-Chancellor 2005-2007) - and it appears as an implementation partner in projects (Climate Skills) and collaborations (curriculum development on Green Buildings; a book launch with Emerson). The existence of a Vice-Chancellor and Registrar implies degree programmes, but NO programme, department, degree or curriculum listing is ingested, because terisas.ac.in is a separate domain outside this corpus. A human must decide whether the existence-level 'yes' is an acceptable gold answer. |
| Q105 | What courses are available in environmental studies, sustainability, and climate change? | aggregation/list | Same gap as Q103/Q104: no course catalogue for either TERI's professional programmes or TERI SAS degrees. The corpus can name individual past courses touching environmental studies, sustainability and climate change (TERI-ITEC Climate change and sustainability; e-Certificate Course on Mainstreaming Urban Climate Action; certificate course on solar energy systems; ESG certification with NDTV) but cannot establish what is currently available. |
| Q108 | What are TERI's most recent publications on renewable energy? | aggregation/list + time-range | 'MOST RECENT' IS COMPUTABLE BUT 'PUBLICATIONS ON RENEWABLE ENERGY' IS NOT A DERIVABLE SET. published_at ordering is reliable, but there is no renewable-energy publication facet: the nearest theme, 'Electricity and Renewables', holds 86 documents of mixed type, and many renewable-energy items in the corpus are third-party news, not TERI publications. Whether 'publications' means policy briefs only, or also research papers, reports and articles, changes the answer entirely. The document_ids list the strongest recent candidates for a human to confirm. |
| Q114 | Who are TERI experts working on climate change? | person lookup | NO EXPERT DIRECTORY. See Q006. What IS derivable is the authorship-by-theme intersection above - a defensible candidate pool but not an answer: the CMS records no designations, expertise statements or current-employment status, several listed names are former staff or advisors, and authorship of a climate-themed document does not establish that someone 'works on climate change' at TERI today. A human must decide whether the derived author list is acceptable gold. |
| Q115 | Which TERI experts specialize in renewable energy? | person lookup | Same structural gap as Q114. Additionally the theme 'Energy' is broader than renewable energy and the narrower 'Electricity and Renewables' theme carries only 86 documents, so even the candidate pool is a poor proxy for 'specialises in renewable energy'. |
| Q116 | Who can I contact regarding green hydrogen research? | person lookup / factual | NO TOPIC-LEVEL CONTACT ROUTING. The corpus has no researcher directory, no 'contact an expert' function and no per-topic contact. The Contact Us page gives only office-level contacts and the general mailbox@teri.res.in. Authorship of the green-hydrogen policy brief is recorded in documents_author but the corpus provides no email or role for those authors, so a chatbot cannot responsibly name an individual to contact. A human must decide whether 'write to mailbox@teri.res.in' is the gold answer. |
| Q117 | Which experts work on sustainable agriculture and food systems? | person lookup | Same structural gap as Q114/Q115. Note also that 'food systems' has no theme or tag facet, so the second half of the question is not derivable at all. Data-quality note: the author list mixes name orders ('Mandal Shovon', 'Agrawal Ruchi' alongside 'Dr Ruchi Agrawal'), indicating un-normalised duplicates in documents_author. |
| Q118 | Who are TERI's specialists in ESG and sustainable finance? | person lookup | WEAKEST OF THE EXPERT QUESTIONS. There is no ESG tag or theme at all, so not even a candidate pool is derivable by facet. Individual named evidence does exist: the TERI-NDTV ESG Certification Program page describes Mr R R Rashmi, a retired IAS officer, as an expert on climate change policies, strategies, actions and international negotiations; and 'Modeling for Climate Finance' identifies Manish Kumar Shrivastava as a senior fellow and associate director at TERI exploring interactions between energy, technology, finance and environmental policy. Two named individuals from programme copy are not a specialist roster. |
| Q120 | How can I collaborate with TERI researchers? | factual / procedural | NO RESEARCH-COLLABORATION ROUTE DOCUMENTED. Unlike Q121 (organisation-level partnering, which the CBS material does cover), there is no page describing how an individual researcher collaborates with TERI researchers - no visiting-fellow scheme, no joint-research call, no researcher directory to approach. The only related routes are the internship email (internship@teri.res.in) and the general mailbox@teri.res.in. A human must decide whether that is an acceptable gold answer. |

## 7. No supported answer

### Q106 - How can students enroll in TERI SAS programmes?

**Gold answer:** The corpus contains no information on enrolling in TERI School of Advanced Studies programmes.

**Established facts about the absence:**

- The corpus provides no admissions process, eligibility criteria, application route, deadlines, fees or programme list for TERI School of Advanced Studies.
- The only TERI SAS contact information in the corpus is the institutional address and the registrar's contact on TERI's Contact Us page (registrar@terisas.ac.in, tel (+91 11) 7180 0222, contact person Col. B Venkat (Retd.)).

**Evidence of absence:**

- `SELECT COUNT(*) FROM documents WHERE url LIKE '%terisas%' OR url LIKE '%teri-sas%' -> 0`
- `SELECT bundle,title FROM documents WHERE title LIKE '%School of Advanced Studies%' -> 2 rows, both the same news item about a book launch with Emerson`
- 2a2e9a77-da56-43a7-8138-3ebf16010d1b - Contact Us (https://teriin.org/contact)

**Notes:** Marked NO_SUPPORTED_ANSWER because the absence is establishable: TERI SAS runs on a separate domain (terisas.ac.in) with zero ingested URLs, and no admissions content exists anywhere in the 11,991 documents. The only defensible chatbot behaviour is to say it does not have TERI SAS admissions information and to point to the registrar contact. An answer that states specific programmes, eligibility or deadlines is a hallucination regardless of whether it happens to be true in the real world.

## 8. Gold entries

### Q001 - What is the primary mission and vision of TERI?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI is an independent, not-for-profit research organisation advancing innovative solutions in energy, environment, climate change and sustainable development. Its stated mission is to usher transitions to a cleaner and sustainable future through the conservation and efficient use of energy and other resources, and innovative ways of minimizing and reusing waste. The mission is pursued through twelve stated goals (clean-energy access, renewable-energy transition, energy efficiency, material efficiency, water conservation and watershed management, sustainable cities and green buildings, climate resilience, pollution abatement, ecosystem services, green mobility, sustainable food production, clean air) and six values (Collaboration, Integrity, Resilience, Nurture, Innovation, Inclusive).

**Expected facts**

- TERI is an independent, not-for-profit research organisation working on energy, environment, climate change and sustainable development.
- TERI's mission: to usher transitions to a cleaner and sustainable future through the conservation and efficient use of energy and other resources, and innovative ways of minimizing and reusing waste.
- TERI pursues the mission through an explicit list of goals covering clean-energy access, renewable energy, energy efficiency, material efficiency, water, sustainable cities and green buildings, climate resilience, pollution abatement, ecosystem services, green mobility, sustainable food production and clean air.
- TERI's stated values are Collaboration, Integrity, Resilience, Nurture, Innovation and Inclusive.

**Expected entities**: The Energy and Resources Institute (TERI)

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |

**Notes**: Mission is stated verbatim on the /mission-and-goals page. The corpus contains NO separately labelled 'vision' statement; the closest is the SDG page line 'to be a knowledge-based agent of change for realizing a shared vision of global sustainable development' (doc 5f273cf0). Answers that assert a distinct 'vision statement' beyond that should be treated as unsupported.

---

### Q002 - Can you provide a brief history of The Energy and Resources Institute (TERI)?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: historical/narrative
- **Temporal scope**: temporal_mode=historical; requested_period=1974-present; expected_validity_window=1974-01-01..open

**Gold answer**

> TERI was established in 1974 as the Tata Energy Research Institute. Shri JRD Tata was its first Chairman; Shri Darbari Seth, builder of Tata Chemicals, conceived the institute and funded its corpus from two companies he chaired, becoming Vice-Chairman of the TERI Governing Council in 1975 and remaining Chairman of the institute until his death (1920-1999). Dr R K Pachauri was TERI's first/founder-Director from 1981, leading it to 2015 and continuing as Executive Vice-Chairman; he was elected Chairman of the IPCC in April 2002 and received the 2007 Nobel Peace Prize on behalf of the IPCC. Shri Ratan Tata later joined the Governing Council. TERI is headquartered in New Delhi with regional centres across India and is today a 1,000+ person multidisciplinary institute.

**Expected facts**

- TERI was established in 1974.
- TERI's original name was the Tata Energy Research Institute.
- Shri JRD Tata was TERI's first Chairman.
- Shri Darbari Seth decided to establish TERI in 1974 and provided the funds for TERI's corpus from two companies he chaired; he became Vice-Chairman of the TERI Governing Council in 1975 and remained Chairman of the Institute until his last day (1920-1999).
- Dr R K Pachauri was TERI's first (founder) Director, assuming the role in 1981.
- Dr R K Pachauri was elected Chairman of the Intergovernmental Panel on Climate Change (IPCC) in April 2002 and received the Nobel Peace Prize on behalf of the IPCC for 2007, jointly with Al Gore.
- Shri Ratan Tata later joined the TERI Governing Council.
- TERI is headquartered in New Delhi.

**Expected entities**: Tata Energy Research Institute, Shri JRD Tata, Mr Darbari S Seth, Dr R K Pachauri, IPCC, Shri Ratan Tata, Tata Chemicals Limited

**Expected relationships**: Darbari Seth FOUNDED TERI (1974); JRD Tata WAS_FIRST_CHAIRMAN_OF TERI; R K Pachauri WAS_DIRECTOR_OF TERI (from 1981); R K Pachauri WAS_CHAIRMAN_OF IPCC (from 2002)

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `6f3c7dea-d0f9-4797-a7e3-5a00aef51d82` | website / page | Founders | https://teriin.org/history |
| `31b8d7da-7b7f-4f1a-9e6f-1271ccddfb28` | website / page | Mr. Darbari Seth: The Visionary Founder of TERI | https://teriin.org/darbari-seth-visionary-founder-teri |

**Notes**: CONTRADICTION IN CORPUS on the end of Pachauri's tenure: /mission-and-goals (d7744c0b) says he led TERI 'from 1981 to 2015 and later as Executive Vice-Chairman until 2017'; /history (6f3c7dea) says he 'demitted office as the executive vice chairman in March 2016'. Either is defensible; a grader must not penalise the other. Do not expect any statement about the circumstances of his departure - the corpus contains none.

---

### Q003 - What are TERI's core research areas and divisions?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's research is organised around seven thematic areas: Sustainable Agriculture; Climate Change; Energy; Environment; Sustainable Habitat; Health & Nutrition; and Resources and Sustainable Development. The same seven appear as the primary themes in the CMS taxonomy (with 'Environment and Public Health' as the taxonomy label for Health & Nutrition), each with sub-themes such as Water, Air, Waste, Land, Forest & Biodiversity, Microbes (under Environment); Energy Efficiency, Energy Access, Electricity and Renewables, Energy Assessment and Modelling (under Energy); and Transport, Buildings, Cities (under Sustainable Habitat). Delivery is organised into programmes/divisions, of which the CMS records nine on current projects: Natural Resources and Climate; Energy; Sustainable Habitat; Environmental & Industrial Biotechnology; Sustainable Agriculture; Communication Outreach & Advocacy Unit; Integrated Policy Analysis; Social Transformation; and Knowledge Management.

**Expected facts**

- TERI's thematic areas are Sustainable Agriculture, Climate Change, Energy, Environment, Sustainable Habitat, Health & Nutrition, and Resources and Sustainable Development.
- Sub-themes under Environment include Water, Air, Waste, Land, Forest & Biodiversity and Microbes.
- Sub-themes under Energy include Energy Efficiency, Energy Access, Electricity and Renewables, and Energy Assessment and Modelling.
- Sub-themes under Sustainable Habitat include Transport, Buildings and Cities.
- Programmes/divisions recorded against current projects include Natural Resources and Climate, Energy, Sustainable Habitat, Environmental & Industrial Biotechnology, Sustainable Agriculture, Communication Outreach & Advocacy Unit, Integrated Policy Analysis, Social Transformation and Knowledge Management.

**Expected entities**: Sustainable Agriculture, Climate Change, Energy, Environment, Sustainable Habitat, Health & Nutrition, Resources & Sustainable Development

**Reproducible derivations**

- `SELECT theme, theme_type, parent, COUNT(*) FROM documents_theme GROUP BY 1,2,3 -> 7 primary main themes (Environment 2215, Climate Change 1630, Energy 1439, Sustainable Agriculture 518, Sustainable Habitat 472, Resources & Sustainable Development 440, Environment and Public Health 195)`
- `SELECT JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_programme[0]')) FROM documents WHERE bundle='ongoing_projects' GROUP BY 1 -> 9 distinct non-null programmes`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |

**Notes**: 'Divisions' is the weaker half of the question: the CMS exposes field_ongoing_programme (9 values) and field_ongoing_division_area / field_division as free text (e.g. 'Renewable Energy Technology Applications', 'Growth, Diversification & Commercialization'), so no single authoritative division chart exists. The theme list is authoritative and corroborated by two independent stores.

---

### Q004 - What are TERI's flagship initiatives and centres of excellence?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's flagship outreach initiative is the World Sustainable Development Summit (WSDS), held annually since 2001. Other flagship initiatives named in the corpus include Act4Earth (launched at the 21st WSDS, comprising COP Compass and the SDG Charter), the Industry Charter for Near Zero Emission Ambition by 2050, Lighting a Billion Lives (LaBL), GRIHA (India's national green-building rating system developed by TERI with MNRE), and Mission LiFE youth programmes. The Centres of Excellence hub page lists nine: CONCOR-TERI CoE for Green and Sustainable Logistics; TERI-CoE for Coastal Studies and Resource Management (CoE-CSRM); NMCG-TERI CoE on Water Reuse (NTCoE); Centre of Excellence for Energy Transition (CoEET); Mahindra-TERI CoE; National CoE in Green Ports and Shipping; NCEARAN CoE (supported by DBT); TERI-CFCL CoE; and Tata Chemicals Ltd.-TERI CoE for Biochemicals.

**Expected facts**

- The World Sustainable Development Summit (WSDS) has been TERI's flagship event since 2001 and is held annually.
- The Centres of Excellence hub page lists nine centres: CONCOR-TERI CoE for Green and Sustainable Logistics, TERI-CoE for Coastal Studies and Resource Management (CoE-CSRM), NMCG-TERI CoE on Water Reuse (NTCoE), Centre of Excellence for Energy Transition (CoEET), Mahindra-TERI CoE, National CoE in Green Ports and Shipping, NCEARAN CoE (supported by DBT), TERI-CFCL CoE, and Tata Chemicals Ltd.-TERI CoE for Biochemicals.
- Act4Earth was launched at the valedictory session of the 21st WSDS and comprises COP Compass and the SDG Charter.
- The Industry Charter for Near Zero Emission Ambition by 2050 is a TERI business-facing initiative covering energy efficiency, renewable energy, circular economy, low-carbon supply chains, carbon sequestration, technology demonstration and the business-policy interface.
- GRIHA - Green Rating for Integrated Habitat Assessment - is India's national green-building rating system, developed by TERI (jointly with MNRE, 2007).

**Expected entities**: World Sustainable Development Summit (WSDS), Act4Earth, COP Compass, SDG Charter, Industry Charter for Near Zero Emission Ambition by 2050, GRIHA, Lighting a Billion Lives, CONCOR-TERI Centre of Excellence, CoE-CSRM, NMCG-TERI NTCoE, CoEET, Mahindra-TERI Centre of Excellence, National Centre of Excellence in Green Ports and Shipping, NCEARAN Centre of Excellence, TERI-CFCL Centre of Excellence, Tata Chemicals Ltd.-TERI Centre of Excellence for Biochemicals

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `98ad60e0-e960-4a46-b8c7-906ee0324d32` | website / page | Centres of Excellence | https://teriin.org/centre-of-excellence |
| `a7b2a24a-f80f-49ae-b5d1-97b0e522244a` | website / page | Outreach | https://teriin.org/outreach |
| `65cdeb2f-e4c0-4faa-ae6a-891223cac8d6` | website / page | ACT4EARTH | https://teriin.org/act4earth |
| `4bf09b06-a4dc-4daa-bb80-45fdbea9d4b9` | website / page | Industry Charter for Near Zero Emission Ambition by 2050 | https://teriin.org/industry-charter-near-zero-emission-ambitio-2050 |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `f029ec29-1dd2-4feb-bdc2-26bf95849774` | website / page | Centre of Excellence on Energy Transition (CoEET) | https://teriin.org/centre-of-excellence-for-energy-transition |
| `e697e316-850e-4ad0-b37e-f42bc83d60d0` | website / page | Mahindra-TERI Centre of Excellence | https://teriin.org/Mahindra-TERI-centre-of-excellence |
| `d1dda10c-8168-43c7-b364-fa3a6f4d661f` | website / page | TERI-CFCL Centre of Excellence (CoE) for Advanced and Sustainable Agriculture Solutions | https://teriin.org/TERI-CFCL-centre-of-excellence-CoE |
| `5b31ce53-5820-40a2-ba7c-be29e262f6c6` | website / page | DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities | https://teriin.org/dbt-teri-centre-excellence-advanced-biofuels-and-bio-commodities |

**Notes**: INCONSISTENT SOURCE DATA: the CoE hub page (98ad60e0) lists 9 centres, but the site also carries standalone pages for centres NOT on the hub - 'DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities' (5b31ce53) and 'Re-imagining India's building sector' = Centre of Excellence for Sustainable Habitats (7c8f0a6a). An answer naming 9 or 11 centres can both be justified; a grader should score on the 9 hub-page names and not penalise the extra two.

---

### Q005 - Where are TERI's offices located, and how can I contact them?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: location/city + factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI is headquartered at the Darbari Seth Block, Core 6C, India Habitat Centre, Lodhi Road, New Delhi 110 003, India (Tel +91 11 2468 2100 / 7110 2100, mailbox@teri.res.in). Its other locations listed on the Contact Us page are TERI Gram (Gwal Pahari, Gurugram, Haryana); the Centre for Himalayan Studies at Gauhati University Campus, Guwahati, Assam; TERI Southern Regional Centre, Bengaluru, Karnataka; TERI Institute of Energy Transition / Southern Regional Centre, Gachibowli, Hyderabad, Telangana; TERI Western Regional Centre, Navi Mumbai, Maharashtra; TERI Western Regional Centre, Goa (Alto-St. Cruz, Tiswadi); TERI Himalayan Centre, Mukteshwar, Nainital, Uttarakhand; TERI Japan (c/o IGES, Tokyo); and TERI School of Advanced Studies, Vasant Kunj, New Delhi.

**Expected facts**

- TERI's headquarters address is Darbari Seth Block, Core 6C, India Habitat Centre, Lodhi Road, New Delhi - 110 003, India.
- Headquarters telephone: (+91 11) 2468 2100, 7110 2100; general email: mailbox@teri.res.in.
- TERI Gram is at Gurugram-Faridabad Road, Gwal Pahari, Gurugram - 122 003, Haryana.
- The Centre for Himalayan Studies is on the Gauhati University Campus, Jalukbari, Guwahati - 781014, Assam.
- TERI Southern Regional Centre, Bengaluru is at 4th Main, 2nd Cross, Domlur II Stage, Bengaluru - 560 071, Karnataka.
- TERI Institute of Energy Transition / Southern Regional Centre, Hyderabad is at #37, near Wipro Circle, Gachibowli, Hyderabad - 500032, Telangana.
- TERI Western Regional Centre, Mumbai is at Office No. 318, Raheja Arcade, Sector-11, CBD-Belapur, Navi Mumbai - 400 614, Maharashtra.
- TERI Western Regional Centre, Goa is at 233/GH-2, Vasudha Colony, Alto-St. Cruz, Tiswadi, Goa - 403 202.
- TERI Himalayan Centre is at Latey Bunga, Mukteshwar, Nainital - 263 132, Uttarakhand.
- TERI Japan is hosted c/o the IGES Tokyo Sustainability Forum, Nishi-Shinbashi, Minato-ku, Tokyo, Japan.
- TERI School of Advanced Studies is at Plot No. 10, Institutional Area, Vasant Kunj, New Delhi - 110 070.

**Expected entities**: New Delhi, Gurugram, Guwahati, Bengaluru, Hyderabad, Navi Mumbai, Goa (Panaji), Nainital/Mukteshwar, Tokyo, India Habitat Centre

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |

**Notes**: Two authoritative pages give slightly different city lists. /mission-and-goals (d7744c0b) says 'regional centres in Gurugram, Bengaluru, Guwahati, Mumbai, Panaji, Nainital, and Hyderabad' (7 cities + New Delhi HQ). /contact (2a2e9a77) lists the same seven plus TERI Japan (Tokyo) and TERI School of Advanced Studies. Both are correct at different granularity; graders should accept either. Note the Goa entry's address is Alto-St. Cruz/Tiswadi, not Panaji town proper.

---

### Q006 - Who are TERI's leading experts and researchers?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: person lookup / aggregation
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT COUNT(*) FROM documents WHERE bundle='people' -> 8 (all Governing Council member profiles, url pattern teriin.org/governing-council/...)`
- `SELECT COUNT(DISTINCT author_norm) FROM documents_author -> 971 publication authors`
- `SELECT entity_type, source, COUNT(*) FROM documents_entity WHERE entity_type='PERSON' -> 674 provisional + 65 pi_attested from documents_author; 66+14 from field_completed_pi_name`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `ab2e2f0c-0eca-4681-8918-efb62f1adbe8` | website / people | Dr Vibha Dhawan | https://teriin.org/governing-council/dr-vibha-dhawan |

**Notes**: NO STAFF/EXPERT DIRECTORY IN THE CORPUS. The only ingested `people` nodes are eight Governing Council profiles (Dr Vibha Dhawan, Mr M S Unnikrishnan, Mr Madhu S Nair, Mr Mahendra Singhi, Mr Nitin Desai, Mr R Mukundan, Mr Siddharth Sharma, Ms Vaishali Nigam Sinha) - governance, not 'experts and researchers'. Publication authorship (documents_author, 971 distinct names) and project PI names are derivable proxies but the corpus records no designations, expertise areas or current-employment status, so no closed or reliable answer set can be established. A human must decide whether the gold answer is (a) the Governing Council, (b) a derived author list, or (c) 'the corpus cannot answer this'.

---

### Q007 - What are TERI's major achievements and contributions to sustainable development?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's flagship publication 'Creating Impacts, Transforming Lives' (TERI success story, 2024) names its landmark contributions: the Lighting a Billion Lives (LaBL) rural energy-access initiative; the Oilzapper microbial technology for oil-contaminated soil and sludge; TADOX advanced-oxidation wastewater treatment; TERI's contribution to framing India's National Action Plan on Climate Change; conceptualising the Clean Development Mechanism; and developing the GRIHA green-housing rating system. TERI is also credited with strengthening the voice of the Global South in climate negotiations, and Dr R K Pachauri received the 2007 Nobel Peace Prize on behalf of the IPCC he chaired. TERI's modelling work shaped the National Solar Mission and India's five-year plans, and its green-federalism work was used by the 13th Finance Commission to introduce sustainability criteria into centre-state fiscal transfers.

**Expected facts**

- Lighting a Billion Lives (LaBL) is one of TERI's landmark life-changing initiatives.
- TERI developed Oilzapper, a microbial technology that treats oil-contaminated soil and oily sludge; over 1.3 million tonnes of contaminated soil had been treated globally as of March 2025.
- TERI developed TADOX (TERI Advanced Oxidation Technology) for industrial and municipal wastewater treatment.
- TERI contributed to framing India's National Action Plan on Climate Change and to conceptualising the Clean Development Mechanism.
- TERI developed the GRIHA green-building rating system.
- Dr R K Pachauri, TERI's Director, chaired the IPCC and received the 2007 Nobel Peace Prize on the IPCC's behalf.
- TERI's energy modelling provided the basis for missions under the National Action Plan for Climate Change, especially the National Solar Mission, and fed India's five-year plans and the Planning Commission's Low Carbon Inclusive Growth study.
- TERI's work on green federalism was used by the 13th Finance Commission of India to introduce sustainability criteria into centre-to-state fiscal transfers.
- TERI's research contributed to the 2016 amendment of the Mines and Minerals (Development and Regulation) Act and to the creation of the Indian Resource Panel.

**Expected entities**: Lighting a Billion Lives, Oilzapper, TADOX, GRIHA, National Action Plan on Climate Change, Clean Development Mechanism, National Solar Mission, 13th Finance Commission, Indian Resource Panel

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `67523149-2bb5-4679-a353-e4e317852fb8` | website / page | Creating Impacts, Transforming Lives | https://teriin.org/creating-impacts-transforming-lives |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `6f3c7dea-d0f9-4797-a7e3-5a00aef51d82` | website / page | Founders | https://teriin.org/history |
| `79e5135e-aad0-476d-b53f-fabd7312a09e` | website / page | TERI’s Solutions for Sustainable Development | https://teriin.org/TERI_Solutions_for_Sustainable_Development |

**Notes**: Gold is coverage-style: the answer should name several of the listed contributions with correct attribution. There is no authoritative ranked 'top achievements' list, so completeness cannot be graded - only correctness of what is named.

---

### Q008 - What national and international partnerships does TERI maintain?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: relationship / aggregation
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_sponsors')) FROM documents WHERE bundle='ongoing_projects' GROUP BY 1 -> 377 non-null sponsor strings on 594 current projects; top: Department of Biotechnology (20), GIZ (14), Department of Science and Technology (10), Shakti Sustainable Energy Foundation (7), The World Bank (7)`
- `SELECT COUNT(*) FROM documents_assertion WHERE predicate='PARTNER_OF' -> 1`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `67523149-2bb5-4679-a353-e4e317852fb8` | website / page | Creating Impacts, Transforming Lives | https://teriin.org/creating-impacts-transforming-lives |
| `59aebc8a-58e2-450e-8bb2-1c5615b20e6e` | website / basic | TERI Council for Business Sustainability |  |
| `7da36f61-4f2e-4297-8ce4-125150ba5bf5` | website / page | TERI @ G20 | https://teriin.org/teri-at-g20 |

**Notes**: NO AUTHORITATIVE PARTNER LIST. The corpus has no partners/collaborators page. Funders are recorded per-project (field_ongoing_sponsors / field_completed_sponsors, the latter promoted to 957 FUNDED_BY claims over 498 distinct organisations), but funder is not the same relation as partner, and the graph holds exactly ONE PARTNER_OF assertion. Individual MoU press releases exist (USGBC, GIZ, NABARD, RBI, GCCA, Rajasthan Renewable Energy Corporation, Mahindra, CONCOR, Chambal Fertilisers, Hindustan Zinc, Ion Exchange, Methanol Institute, POSOCO, REMCL, SCGJ, Vedanta, VNV, Bisleri, FNI/INTASAVE-CARIBSAVE, British Council/HSBC, ICIMOD/NTNC, IGES, Emerson) but no closed set can be established and 'maintains' (present tense) cannot be verified for any of them.

---

### Q009 - Does TERI offer internships, fellowships, or career opportunities for students and researchers?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI accepts interns from universities, schools and colleges worldwide; applications (CV plus a letter stating start/end dates, reason for applying and the area of work sought) go to internship@teri.res.in. Assignments may be research-based - Renewable Energy, Sustainable Architecture and Urban Planning, Air Pollution, Waste Management, Water pollution, Biotechnology, Climate Change, Rural Livelihood, Energy Modelling, Environmental Education - or non-research (marketing, IT, Library, Outreach). Interns are attached to an ongoing project with a supervisor, submit a report at the end and receive a TERI certificate. TERI has also run fellowships, e.g. the Media Fellowship on Climate Change Reporting in the Himalayan Region, and describes its careers 'Areas of Work' as technology products, policy advisory and outreach, and technical services.

**Expected facts**

- TERI accepts interns from universities, schools and colleges all over the world.
- Internship applications (CV and application) are sent to internship@teri.res.in and must state the start and end dates, the reason for applying and the area of work sought.
- Internship research areas include Renewable Energy, Sustainable Architecture and Urban Planning, Air Pollution, Waste Management, Water pollution, Biotechnology, Climate Change, Rural Livelihood, Energy Modelling and Environmental Education.
- Non-research internships are available in marketing, IT, Library and Outreach.
- Interns are assigned work on an ongoing project, submit a report to their supervisor, and TERI awards a certificate at the end of the term.
- TERI has run the Media Fellowship on Climate Change Reporting in the Himalayan Region.

**Expected entities**: internship@teri.res.in, Media Fellowship on Climate Change Reporting in the Himalayan Region

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `48b331a3-2631-4f58-b5ba-e7673163c893` | website / page | Internship | https://teriin.org/careers/internship |
| `8937e1db-933e-45dc-80d3-80a0889f66cf` | website / page | Areas of Work | https://teriin.org/careers/areas-work |
| `add936be-a0ad-486d-a744-54424e41e0a5` | website / page | Media Fellowship on Climate Change Reporting in the Himalayan Region | https://teriin.org/media-fellowship-climate-change-reporting-himalayan-region |

**Notes**: Internships: HIGH confidence, fully documented. Fellowships: only one named example in the corpus. Career opportunities: the corpus has an 'Areas of Work' page but NO vacancies listing or recruitment process, so an answer must not claim to list current openings.

---

### Q010 - How can I stay updated on TERI's activities and announcements?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual
- **Temporal scope**: temporal_mode=current; requested_period=as of corpus snapshot 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> TERI publishes a monthly newsletter (archived at teriin.org/newsletters, hosted on newsletters.teriin.org, with issues through July 2026 in this snapshot), an Announcements page (teriin.org/announcements, carrying news items and tenders) with an Announcements Archive, thematic newsletters (TERI CBS Newsletters; Transport and Urban Governance; Sustainable Buildings), and a Documents/Brochures hub linking Annual Reports, Brochures and Newsletters. Its website also carries news, press releases, events and videos sections.

**Expected facts**

- TERI publishes a monthly newsletter, archived at teriin.org/newsletters (issues hosted on newsletters.teriin.org).
- TERI's Announcements page (teriin.org/announcements) carries current announcements and tenders, with an Announcements Archive for older items.
- TERI publishes thematic newsletters including TERI CBS Newsletters, the Transport and Urban Governance newsletter, and Newsletters and Resources - Sustainable Buildings.
- The Documents/Brochures hub (teriin.org/documents) links Annual Reports, Brochures, Newsletters and TERI's Solutions for Sustainable Development.

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `80d9bdc9-c159-493a-80e1-ca53cece85e3` | website / page | Newsletters | https://teriin.org/newsletters |
| `64b3242e-5578-4ff5-acd9-f9aaa1377ecf` | website / page | Announcements | https://teriin.org/announcements |
| `01937c6f-ea48-4c44-ba22-19fab25ba7bc` | website / page | Documents/Brochures | https://teriin.org/documents |
| `e1b33545-8a85-4250-8c5d-b49ef0b073b5` | website / page | Announcements Archive | https://teriin.org/announcements-archive |
| `158a8504-92da-41bb-863c-7cd7ecc00792` | website / page | CBS Newsletters | https://teriin.org/CBS-newsletters |
| `e5911c7d-d2b6-410a-8c6e-233b97c129a2` | website / page | Transport and Urban Governance (TUGD) | https://teriin.org/newsletter-transport-urban-governance |
| `874fc35b-a477-4090-aef2-c0ed050d5d79` | website / page | Newsletters and Resources - Sustainable Buildings | https://teriin.org/newsletter-resources-sustainable-buildings |

**Notes**: The corpus contains no evidence of an email-subscription form or social-media handles; an answer should not assert a newsletter sign-up mechanism.

---

### Q011 - What are TERI's latest research priorities?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=current; requested_period=2025-2030; expected_validity_window=2025-01-01..2030-12-31

**Gold answer**

> TERI's current research priorities are set out in the Strategic Document Vision: 2025-30. In the short term the focus is piloting innovative technologies, advancing regulatory frameworks, enhancing capacity building and fostering community-centric sustainable practices - supporting policy design, driving behaviour change, expanding stakeholder training and demonstrating on-ground models across clean energy, sustainable agriculture, water and waste management, climate resilience and social transformation. In the long term TERI aims to scale these through transformative research, large-scale deployment of clean technologies, integrated sustainability frameworks and stronger international partnerships, emphasising systemic decarbonization, circular-economy solutions, climate-smart infrastructure and a net-zero, resource-efficient, inclusive development trajectory by 2030.

**Expected facts**

- TERI's current research priorities are set out in the Strategic Document Vision: 2025-30 (teriin.org/files/Strategy_Plan_2025_30.pdf).
- Short-term strategic focus: piloting innovative technologies, advancing regulatory frameworks, enhancing capacity building, fostering community-centric sustainable practices.
- Sectors named for on-ground demonstration models: clean energy, sustainable agriculture, water and waste management, climate resilience, social transformation.
- Long-term focus: transformative research, large-scale clean-technology deployment, integrated sustainability frameworks, stronger international partnerships.
- Long-term emphases: systemic decarbonization, circular-economy solutions, mainstreaming climate-smart infrastructure, and a net-zero, resource-efficient and inclusive development trajectory by 2030.

**Expected entities**: Strategic Document Vision: 2025-30

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `08c11465-0bee-4bc2-be53-1eaa23938efe` | website / page | Strategic Document Vision: 2025–30 | https://teriin.org/Strategic-Document-Vision-2025–30 |
| `1f2d085c-58cc-4193-85b2-8b29f86ff86a` | website / page | Our Research Focus | https://teriin.org/Our-Research-Focus |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |

**Notes**: The Strategy 2025-30 landing page is authoritative and current; the linked PDF itself (Strategy_Plan_2025_30.pdf) is not separately ingested as a document row, so only the page-level summary is quotable.

---

### Q012 - What is TERI's contribution to India's Net-Zero 2070 goal?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=date range; requested_period=target year 2070; TERI outputs 2021-2026

**Gold answer**

> TERI's principal contributions to India's net-zero-by-2070 goal recorded in the corpus are: the discussion paper and conceptual framework 'India's Journey to Net Zero: A Conceptual Framework for Analysis' (May 2024); the 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070', launched with GCCA India in March 2025; the TERI-Shell report 'India: Transforming to a Net-Zero Emissions Energy System' with a call to action to 2030; 'Rising Ambition: Carving New Pathways - India's Energy Transition'; briefing to government on India's 2035 NDC (with the We Mean Business Coalition); and the Industry Charter for Near Zero Emission Ambition by 2050, through which TERI secures corporate commitments. TERI also states it has shaped India's NDC announcements with analytical inputs and evidence-based recommendations.

**Expected facts**

- TERI published the discussion paper 'India's Journey to Net Zero: A Conceptual Framework for Analysis' (20 May 2024) and announced it as a new conceptual framework charting India's path to net zero by 2070.
- TERI and GCCA India launched the 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070' in March 2025.
- The TERI-Shell report 'India: Transforming to a Net-Zero Emissions Energy System' sets out energy efficiency, electrification and decarbonized fuels as strategic pillars with a call to action to 2030.
- TERI convenes the Industry Charter for Near Zero Emission Ambition by 2050 to secure corporate commitments to near-zero-carbon operations.
- TERI, with the We Mean Business Coalition, prepared recommendations for India's 2035 NDC ('India's 2035 Climate Target: A Business Opportunity for Growth and Global Leadership').
- TERI states it played a pivotal role in shaping India's NDC announcements through analytical insights and evidence-based recommendations.

**Expected entities**: Net Zero 2070, GCCA India, Shell, We Mean Business Coalition, Industry Charter for Near Zero Emission Ambition by 2050

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `862bb586-1914-40ce-bc89-97f99869e872` | website / research_papers | Discussion paper on India’s Journey to Net Zero: A Conceptual Framework  for Analysis | https://teriin.org/research-paper/discussion-paper-indias-journey-net-zero-conceptual-framework-analysis |
| `85a11afd-6fdc-4689-b814-9f870d1340cc` | website / press_release | TERI charts India’s path to net zero by 2070 with new conceptual framework | https://teriin.org/press-release/teri-charts-indias-path-net-zero-2070-new-conceptual-framework |
| `2a310697-5393-4e1f-bd72-f22179e32011` | website / policy_brief | Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070 | https://teriin.org/policy-brief/decarbonization-roadmap-indian-cement-sector-net-zero-co2-2070 |
| `9d284876-e413-4015-b84b-0c8b3db8c866` | website / press_release | GCCA India and TERI Launch Decarbonisation Roadmap for the Indian Cement Industry: Net Zero CO2 by 2070 | https://teriin.org/press-release/gcca-india-and-teri-launch-decarbonisation-roadmap-indian-cement-industry-net-zero |
| `b9f4fdc0-155f-4c8f-9004-d46b582f2aad` | website / page | TERI'S CONTRIBUTIONS TO BUSINESS ACTION ON CLIMATE CHANGE | https://teriin.org/Shaping-India-CLimate-Policy-discourse |
| `4bf09b06-a4dc-4daa-bb80-45fdbea9d4b9` | website / page | Industry Charter for Near Zero Emission Ambition by 2050 | https://teriin.org/industry-charter-near-zero-emission-ambitio-2050 |
| `c555b305-da7c-4747-bc8e-9f302f130c1f` | website / press_release | ‘Rising Ambition’ Launched: TERI Unveils New Vision for India’s Energy Future | https://teriin.org/press-release/rising-ambition-launched-teri-unveils-new-vision-indias-energy-future |

**Notes**: 2070 is India's national target, not TERI's; the gold answer must attribute the target to India and the listed analytical products to TERI.

---

### Q013 - Can you summarize TERI's recent reports on climate change and energy policy?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT COUNT(*) FROM documents WHERE bundle='policy_brief' AND source_type='website' -> 247`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a310697-5393-4e1f-bd72-f22179e32011` | website / policy_brief | Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070 | https://teriin.org/policy-brief/decarbonization-roadmap-indian-cement-sector-net-zero-co2-2070 |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |
| `349ea25d-30d9-4315-94d9-dab2082d6592` | website / policy_brief | Modeling for Climate Finance | https://teriin.org/policy-brief/modeling-climate-finance |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `a1ca094a-591b-40d5-928f-fbe5c105c119` | website / policy_brief | Solar With Storage Is Cheaper Than New Thermal | https://teriin.org/policy-brief/solar-storage-cheaper-new-thermal |
| `862bb586-1914-40ce-bc89-97f99869e872` | website / research_papers | Discussion paper on India’s Journey to Net Zero: A Conceptual Framework  for Analysis | https://teriin.org/research-paper/discussion-paper-indias-journey-net-zero-conceptual-framework-analysis |

**Notes**: AMBIGUOUS SCOPE. 'Recent' is undefined and the question asks for a multi-report summary. The corpus holds 247 policy-brief nodes plus 624 research papers and 8 report nodes with no 'recent'/'flagship' marker, and no authoritative digest document. A defensible gold requires a human to fix the window (e.g. published_at >= 2025-08-19) and the report classes in scope. Candidate anchors listed in document_ids are the most recent climate/energy policy briefs.

---

### Q014 - How does TERI support evidence-based policymaking at the state and national levels?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports evidence-based policymaking through interdisciplinary modelling and analysis feeding national and sub-national decisions. Named national contributions: over four decades of energy modelling inputs, scenario-based modelling of emission intensities and non-fossil capacity shares; the missions under the National Action Plan for Climate Change - especially the National Solar Mission - delineated largely from TERI's modelling; inputs to India's five-year plans, the Integrated Energy Plan Report and the Planning Commission's Low Carbon Inclusive Growth study; work on green federalism used by the 13th Finance Commission to add sustainability criteria to centre-state fiscal transfers; inputs to India's Environment Policy 2006 and to India's negotiating positions at UNFCCC, CBD and WTO; contribution to the 2016 MMDR Act amendment; creation of the Indian Resource Panel; and end-of-life vehicle scrapping and metal recycling inputs to CPCB. Sub-nationally TERI has worked with states on biodiversity strategy and action plans, agriculture sustainability (Punjab, Haryana), resource-efficiency strategy (Goa), and runs Project Management Units - Sustainable Habitat cell in Vijayawada and ECBC cells in Odisha, Punjab and Haryana - to help state and local governments implement ECBC/ECSBC and climate-resilient policies.

**Expected facts**

- TERI's modelling has provided energy-policy inputs for over four decades, including scenario-based modelling of emission intensities and non-fossil generation capacity shares.
- The missions under the National Action Plan for Climate Change, especially the National Solar Mission, were delineated to a large extent from TERI's modelling and analytics.
- TERI provided inputs to India's five-year plans, was part of the Integrated Energy Plan Report, and did the modelling for the Planning Commission's Low Carbon Inclusive Growth study.
- TERI's work on green federalism was used by the 13th Finance Commission to introduce sustainability criteria in centre-to-state fiscal transfers.
- TERI contributed to India's Environment Policy 2006 and to India's negotiating positions at the UNFCCC, CBD and WTO.
- TERI's research was considered in the 2016 amendment of the Mines and Minerals (Development and Regulation) Act and led to the creation of the Indian Resource Panel with the Union environment ministry.
- TERI provided inputs for CPCB policies on end-of-life vehicle scrapping and metal recycling.
- TERI has worked with several states on biodiversity strategy and action plans and with Punjab and Haryana on agricultural sustainability.
- TERI runs Project Management Units for state governments: a Sustainable Habitat cell in Vijayawada and ECBC cells in Odisha, Punjab and Haryana.
- Goa became India's first state to have a resource-efficiency strategy, prepared with TERI.

**Expected entities**: National Action Plan for Climate Change, National Solar Mission, 13th Finance Commission, Indian Resource Panel, UNFCCC, CBD, WTO, CPCB, ECBC, Goa, Punjab, Haryana, Odisha, Vijayawada

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `07ea5072-b97a-450b-99dd-95e535ee6685` | website / services | Policy, Strategic Planning & Advocacy |  |
| `d9879bf4-a934-41b1-b580-00459fbadc6e` | website / services | Project Monitoring Unit |  |
| `70326006-9cc2-4e08-8f7b-55798dd65a51` | website / services | Policy intervention and analysis |  |
| `5041c386-21cc-426c-99ef-295ce726eeee` | website / services | Multidisciplinary research and policy advice |  |
| `058a0931-580e-481f-a02f-78641809321d` | website / press_release | Goa becomes India's first state to have resource efficiency strategy; measures suggested for tourism, construc | https://teriin.org/press-release/goa-becomes-indias-first-state-have-resource-efficiency-strategy-measures-suggested |

**Notes**: Strongly evidenced on the /policy page and service nodes. No dates are attached to most claims, so temporal precision cannot be graded.

---

### Q015 - What kind of research does TERI conduct on sustainable agriculture?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's sustainable-agriculture research develops plant- and microbe-derived products that cut chemical-fertiliser use while raising yields, and applies nano-biotechnology to nano-fertilisers, superfoods and algal bioenergy, demonstrating change by improving farming-community livelihoods. Concrete lines of work in the corpus: mycorrhiza biofertiliser (in-vitro mass-production technology, up to 1000 billion propagules/annum, commercialised with end-to-end handholding); micropropagation of cash crops and forest species (over 70 protocols); biogenic nano-fertilisers for climate-smart farming; cellulose-nanofibre nitrogen fertiliser; the TERI-CFCL Centre of Excellence for Advanced and Sustainable Agriculture Solutions (with Chambal Fertilisers and Chemicals Ltd); the SDG Blueprint for Sustainable Agriculture and its tool; policy work on organic agriculture, agricultural waste, planting-material standards and nano-product regulation; and the international AISAC conference on Agri-Inputs for Sustainable Agriculture and Climate.

**Expected facts**

- TERI's sustainable-agriculture work focuses on plant- and microbe-derived products that reduce chemical-fertiliser use while improving crop yields.
- TERI uses nano-biotechnology to develop nano-fertilisers, superfoods and algal-based bioenergy.
- TERI's In Vitro Mass Production Technology commercially produces high-quality mycorrhiza biofertiliser (up to 1000 billion propagules per annum), with end-to-end handholding to commercialisation.
- TERI's micropropagation centre supplies tissue-cultured plants to individuals and government bodies such as forest departments and has over 70 micropropagation protocols.
- TERI develops biogenic nano-fertilisers for climate-smart and sustainable farming.
- The TERI-CFCL Centre of Excellence for Advanced and Sustainable Agriculture Solutions was established with Chambal Fertilisers and Chemicals Limited.
- TERI produced the SDG Blueprint for Sustainable Agriculture and an SDG Blueprint Tool for Sustainable Agriculture.
- TERI's agriculture policy work covers climate impacts and resilience, natural-resource sustainability in farming, agricultural waste management, support for organic agriculture, standards for resilient planting material and regulation of nano-products in agriculture.

**Expected entities**: mycorrhiza biofertiliser, micropropagation, nano-fertilisers, TERI-CFCL Centre of Excellence, Chambal Fertilisers and Chemicals Limited, SDG Blueprint for Sustainable Agriculture, AISAC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `555ac39f-260f-41f4-a03d-e337e02fc844` | website / page | Micropropagation Technology Park | https://teriin.org/technology/micropropagation-technology-park |
| `b2827f5a-ae1c-47b5-895b-257c1336f017` | website / page | Innovations in Climate-Smart and Sustainable Farming through Nanotechnology | https://teriin.org/technologies/innovations-in-climate-smart-and-sustainable-farming-through-nanotechnology |
| `f387a567-cf91-4683-91ae-c431a037d49b` | website / services | Next generation technology to produce high-quality mycorrhiza |  |
| `d1dda10c-8168-43c7-b364-fa3a6f4d661f` | website / page | TERI-CFCL Centre of Excellence (CoE) for Advanced and Sustainable Agriculture Solutions | https://teriin.org/TERI-CFCL-centre-of-excellence-CoE |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `fc588c50-391a-400c-a6ad-74707615b2af` | website / policy_brief | SDG Blueprint for Sustainable Agriculture | https://teriin.org/policy-brief/sdg-blueprint-sustainable-agriculture |
| `2566f71f-afc8-4da2-8c40-253184d05591` | website / page | SDG Blueprint Tool for Sustainable Agriculture | https://teriin.org/SDG-Blueprint-tool-for-Sustainable-Agriculture |
| `b229225b-e2d0-4906-b923-bf31c7cc9006` | website / press_release | Chambal Fertilisers and Chemicals Limited and The Energy and Resources Institute partner to establish ‘Centre  | https://teriin.org/press-release/chambal-fertilisers-and-chemicals-limited-and-energy-and-resources-institute-partner |
| `270b7a01-39ba-497e-930f-911e390fc778` | website / ongoing_projects | TERI-CFCL Centre of Excellence (CoE) for Advanced and Sustainable Agriculture Solutions | https://teriin.org/project/teri-cfcl-centre-excellence-coe-advanced-and-sustainable-agriculture-solutions |
| `21102beb-b5ff-4d18-8ede-62354fb5bb2a` | website / ongoing_projects | TERI’s Mycorrhizal Platforms: Advancing Soil Health and Sustainable Agriculture | https://teriin.org/project/teris-mycorrhizal-platforms-advancing-soil-health-and-sustainable-agriculture |

---

### Q016 - Does TERI publish data or studies related to greenhouse gas (GHG) inventories?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual + aggregation
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI publishes emissions-inventory data and studies. Named outputs: the Catalogue of Indian Emission Inventory Reports, launched with EDF in January 2022 to aid policymakers and scientists; the India GHG Program, managed by WRI, TERI and CII, which TERI states covers about 10% of the country's industrial emissions; the article 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana, South Korea, Japan, and Chile'; and a large body of city/region emission-inventory and source-apportionment studies (Faridabad, Rishikesh, Kashipur, Kolkata-Howrah, Kanhia open-cast coal mine, Delhi-NCR). TERI's climate-change risk-assessment service explicitly includes GHG inventorization and mitigation analysis.

**Expected facts**

- TERI and EDF launched the Catalogue of Indian Emission Inventory Reports in January 2022.
- The India GHG Program, launched in July 2013, is facilitated by the World Resources Institute (WRI), TERI and the Confederation of Indian Industry (CII); as reported in December 2014 it tracked about 268 MT of carbon emissions - well over 10% of India's industrial emissions - across about 30 member companies.
- TERI's climate-change risk-assessment service includes GHG inventorization and mitigation analysis.
- TERI has conducted emission-inventory and source-apportionment studies for multiple Indian cities and regions, including Faridabad, Rishikesh, Kashipur, Kolkata and Howrah, and Delhi-NCR.
- TERI published 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana, South Korea, Japan, and Chile'.

**Expected entities**: Catalogue of Indian Emission Inventory Reports, India GHG Program, EDF, WRI, CII

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `b6d6a144-550e-4dec-9b56-a013d4c92356` | website / news | TERI Launches Catalogue of Indian Emission Inventory to Aid Policymakers and Scientists | https://teriin.org/news/teri-launches-catalogue-indian-emission-inventory-aid-policymakers-and-scientists |
| `ca0121eb-ad47-4f82-83c9-54470cf7e404` | website / news | TERI and EDF launch catalogue of Indian Emission Inventory reports | https://teriin.org/news/teri-and-edf-launch-catalogue-indian-emission-inventory-reports |
| `109b0e0e-6a76-400a-9a18-dc6c5d31b8fb` | website / events | Launch of Catalogue of Indian Emission Inventory Reports | https://teriin.org/event/launch-catalogue-indian-emission-inventory-reports |
| `fd6ef5a5-1591-489e-aa22-624107fe67f8` | pdf_attachment / press_release | India GHG Program: WRI, TERI and CII are managing 10% of the country’s industrial emissions | https://teriin.org/press-release/india-ghg-program-wri-teri-and-cii-are-managing-10-countrys-industrial-emissions |
| `93f819a5-01d8-472b-a547-b5ff8c4a4d72` | website / article | Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana, South Korea | https://teriin.org/casestudies/best-practices-national-ghg-inventory-management-system-case-studies-south-africa-ghana |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |
| `71154b8c-76b1-4777-82f6-76a67a94d850` | website / ongoing_projects | Emission inventories, Source apportionment studies and carrying capacity study for different cities in India | https://teriin.org/project/emission-inventories-source-apportionment-studies-and-carrying-capacity-study-different |
| `7e50bb16-8222-4a3a-801b-6662271c3ef0` | website / completed_projects | Emission Inventorisation for Faridabad Town | https://teriin.org/project/emission-inventorisation-faridabad-town |
| `d523671d-1b5f-4710-b117-7849dc545fc7` | website / ongoing_projects | Carrying out Source Apportionment and Emission Inventory study for Rishikesh City, Uttarakhand | https://teriin.org/project/carrying-out-source-apportionment-and-emission-inventory-study-rishikesh-city-uttarakhand |
| `7de92ace-6fdc-46e0-89f6-114ab0ae8dac` | website / ongoing_projects | Air Pollution Source Apportionment and Carrying Capacity of Kolkata and Howrah City | https://teriin.org/project/air-pollution-source-apportionment-and-carrying-capacity-kolkata-and-howrah-city |

**Notes**: Careful distinction the grader must enforce: most of TERI's inventory work in this corpus is AIR-POLLUTANT emission inventory / source apportionment, not GHG inventory. Only the India GHG Program, the GHG-inventory-management article and the risk-assessment service line are strictly GHG-inventory evidence. An answer that conflates the two should be marked partially correct. VINTAGE CAVEAT: the India GHG Program press release body is dated 1 December 2014 even though its documents.published_at is 2018-01-11 (a migration artefact), so the '10% / 268 MT / ~30 companies' figures are 2014 figures - a chatbot presenting them as current is overstating them.

---

### Q017 - What policy recommendations has TERI recently developed?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT document_id,title,published_at FROM documents WHERE bundle='policy_brief' AND source_type='website' ORDER BY published_at DESC -> 247 rows; 12 most recent listed in document_ids/notes`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |
| `7b4ca9d9-ae6c-4073-a586-fa74918a983b` | website / policy_brief | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward | https://teriin.org/policy-brief/battery-assembly-and-container-testing-safety-global-best-practices-and-way-forward |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `9032cec1-fc66-4da2-838e-0cdc4c831337` | website / policy_brief | Study on Circular Economy of End-of-Life Vehicles and Other Sectors | https://teriin.org/policy-brief/study-circular-economy-end-life-vehicles-and-other-sectors |
| `f0f9e576-bf3c-4a6c-93c2-6f8e88f0022b` | website / policy_brief | Policy Brief: Roadmap for Zero Emission Truck (ZET) Skilling in India | https://teriin.org/policy-brief/policy-brief-roadmap-zero-emission-truck-zet-skilling-india |
| `eeb196ea-84eb-416c-91af-cd05fae6fd9a` | website / policy_brief | Towards Cleaner Freight in Delhi | https://teriin.org/policy-brief/towards-cleaner-freight-delhi |
| `5a11ac34-44cc-4094-9868-ef9e159681fc` | website / policy_brief | Decarbonizing Transport: Supply-side Policies & Opportunities for Uttar Pradesh | https://teriin.org/policy-brief/decarbonizing-transport-supply-side-policies-opportunities-uttar-pradesh |
| `8a92ed23-54ed-466e-ae97-de06bb0d5293` | website / policy_brief | Tenure Dynamics in Land Procurement in Rajasthan’s Utility-Scale Solar Energy Transition | https://teriin.org/policy-brief/tenure-dynamics-land-procurement-rajasthans-utility-scale-solar-energy-transition |

**Notes**: 'Recently' is undefined, and 'policy recommendations' has no structured marker: recommendations live inside policy briefs, discussion papers, press releases and project pages with no field distinguishing a recommendation from a finding. A closed answer set cannot be derived. Most recent policy briefs in the snapshot: Battery Assembly and Container Testing (2026-08-11), Solar Thermal Energy for Industrial Decarbonization (2026-08-05), Sustainable Land Futures for Utility-Scale RE (2026-07-31), Tenure Dynamics in Rajasthan Solar Land Procurement (2026-07-31), Fly Ash Utilization and Transportation (2026-07-21), Unlocking Solar at Scale / Agrivoltaics (2026-07-06), Towards Cleaner Freight in Delhi (2026-06-29), Circular Economy of End-of-Life Vehicles (2026-06-16).

---

### Q018 - What research is TERI conducting on climate finance?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=current; requested_period=as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> TERI's climate-finance research in the current snapshot centres on: 'A Five Pillar Framework for Bankability: Recalibrating India's Commercial Finance for Climate Action' (May 2026), announced as a five-pillar framework to bridge India's climate-finance and bankability gap; the 'Modeling for Climate Finance' policy brief (May 2026) and TERI's climate-finance modelling contribution to the ICEF report in collaboration with Schmidt Sciences; work on blended finance for climate action; the 'Road to Baku: The New Collective Quantified Goal on Climate Finance' paper under COP29 Compass; and national dialogues on climate finance and risk preparedness with NBSC and NABARD (Jan 2026) and a TERI-RBI workshop on climate-induced physical and transition risks for the banking sector.

**Expected facts**

- TERI published 'A Five Pillar Framework for Bankability: Recalibrating India's Commercial Finance for Climate Action' and unveiled it as a five-pillar framework to bridge India's climate-finance and bankability gap (May 2026).
- TERI published the 'Modeling for Climate Finance' policy brief (May 2026) and contributed climate-finance modelling to the ICEF report in collaboration with Schmidt Sciences.
- TERI produced 'Road to Baku: The New Collective Quantified Goal on Climate Finance' under its COP29 Compass strand of Act4Earth.
- TERI, NBSC and NABARD led a national dialogue on climate finance and risk preparedness (January 2026).
- TERI held a workshop with the Reserve Bank of India on climate-induced physical and transition risks, and a workshop on capacity building for physical risks and low-carbon transition for the Indian banking sector.
- TERI has analysed blended-finance instruments for climate action and the risks they mitigate for private investors.

**Expected entities**: Five Pillar Framework for Bankability, ICEF, Schmidt Sciences, NABARD, NBSC, Reserve Bank of India, New Collective Quantified Goal, Act4Earth COP29 Compass

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |
| `895df16b-1b13-4ce6-ab3d-2ae0d09db4a8` | website / press_release | TERI Unveils Five-Pillar Framework to Bridge India’s Climate Finance and Bankability Gap | https://teriin.org/press-release/teri-unveils-five-pillar-framework-bridge-indias-climate-finance-and-bankability-gap |
| `349ea25d-30d9-4315-94d9-dab2082d6592` | website / policy_brief | Modeling for Climate Finance | https://teriin.org/policy-brief/modeling-climate-finance |
| `4930609a-7c2d-467d-99a8-2c7249487809` | website / press_release | TERI Highlights Climate Finance Modeling in ICEF Report, in Collaboration with Schmidt Sciences | https://teriin.org/press-release/teri-highlights-climate-finance-modeling-icef-report-collaboration-schmidt-sciences |
| `4242ea8f-f7ce-4318-873a-5a5625d906b2` | website / press_release | TERI, NBSC, and NABARD Lead National Dialogue on Climate Finance and Risk Preparedness | https://teriin.org/press-release/teri-nbsc-and-nabard-lead-national-dialogue-climate-finance-and-risk-preparedness |
| `b3a0b206-8545-4030-b5e8-14278f6946bd` | website / events | TERI-RBI Workshop on Climate Induced Physical and Transition Risks | https://teriin.org/event/teri-rbi-workshop-climate-induced-physical-and-transition-risks |
| `4830aaa0-58fa-4c6a-97f8-03e997723d80` | website / events | Workshop on Capacity Building on Physical Risks and Low-Carbon Transition for Indian Banking Sector | https://teriin.org/event/workshop-capacity-building-physical-risks-and-low-carbon-transition-indian-banking-sector |
| `65cdeb2f-e4c0-4faa-ae6a-891223cac8d6` | website / page | ACT4EARTH | https://teriin.org/act4earth |

**Notes**: Near-duplicate of Q057 (which adds ESG). Keep the gold answers consistent.

---

### Q019 - What are TERI's latest studies on air quality and pollution management?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=current; requested_period=as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> TERI's current air-quality work spans research, monitoring and management planning. Its Air Quality Research service provides end-to-end solutions through a NABL-accredited laboratory covering monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air quality management planning at urban, regional and national scales, plus policy and decision-support systems, environmental-compensation assessment, third-party audits, sustainable residue management, pilot demonstrations of emission-reduction technologies and capacity building. Current studies include Clean Air Zones pilots in Andhra Pradesh (Vijayawada and Visakhapatnam); development of an Integrated Air Quality Index (AQI) and Liveability Framework; emission-inventory, source-apportionment and atmospheric carrying-capacity studies for Indian cities; a State Air Quality Health Adaptation Plan for Maternal and Child Health (AQHAP, 2025); and a study on forest-fire management and air quality in the Himalaya/Bhutan with ICIMOD, NTNC and UK International Development. Its explainer page argues for evidence-based actions to achieve breathable air in Indian cities.

**Expected facts**

- TERI's Air Quality Research provides end-to-end air-quality and atmospheric-environment solutions through a NABL-accredited laboratory.
- Coverage includes monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air quality management planning at urban, regional and national scales.
- Additional services include policy and decision-support systems, environmental compensation assessment, third-party audits, sustainable residue management, pilot demonstrations of emission-reduction technologies, and capacity building for science-driven environmental governance.
- TERI is piloting Clean Air Zones in Andhra Pradesh, including Vijayawada and Visakhapatnam.
- TERI is developing an Integrated Air Quality Index (AQI) and Liveability Framework.
- TERI conducted a State Air Quality Health Adaptation Plan for Maternal and Child Health (AQHAP, 2025).
- TERI worked with ICIMOD, NTNC and UK International Development on forest-fire management and air-quality improvement in the Himalaya, including a stakeholder consultation on Bhutan.

**Expected entities**: Clean Air Zones, Integrated Air Quality Index and Liveability Framework, AQHAP, ICIMOD, NTNC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `34425ba3-e6e5-482b-8599-d10871edf964` | website / ongoing_projects | Improving Urban Air Quality through Clean Air Zones in Andhra Pradesh | https://teriin.org/project/improving-urban-air-quality-through-clean-air-zones-andhra-pradesh |
| `d6c23474-8f0a-4502-925d-33d07e1c74d5` | website / ongoing_projects | Improving Urban Air Quality by Facilitating Piloting of Clean Air Zones in Vijayawada & Visakhapatnam | https://teriin.org/project/improving-urban-air-quality-facilitating-piloting-clean-air-zones-vijayawada-visakhapatnam |
| `c402762d-53fc-4401-ace6-2bf25d5be8f3` | website / ongoing_projects | Development and Implementation of an Integrated Air Quality Index (AQI) and Liveability Framework for Krisala  | https://teriin.org/project/development-and-implementation-integrated-air-quality-index-aqi-and-liveability-framework |
| `c9234a8a-a45e-450f-accc-7bb1348c5dec` | website / completed_projects | Developing State Air Quality Health Adaptation Plan for Maternal and Child Health (AQHAP), 2025-2030 \| Maharas | https://teriin.org/project/developing-state-air-quality-health-adaptation-plan-maternal-and-child-health-aqhap-2025 |
| `7ac1eb9f-a72c-48d6-9e98-89ce8a6783e7` | website / completed_projects | Comprehensive Study on Solutions for Forest Fire Management and Air Quality Improvement in the HKH Region | https://teriin.org/project/comprehensive-study-solutions-forest-fire-management-and-air-quality-improvement-hkh-region |
| `f0f1c9fc-67cd-4372-8205-95d615cd148d` | website / page | Explainer: How evidence-based actions can help achieve breathable air in Indian cities | https://teriin.org/environment/air/explainer-how-evidence-based-actions-help-achieve-breathable-air-indian-cities |
| `2d89854d-19d9-4c61-83b2-5777dbc5cebc` | website / completed_projects | Air Pollution Emissions Inventory, Source Apportionment and Atmospheric Carrying Capacity Study of Kolkata in  | https://teriin.org/project/air-pollution-emissions-inventory-source-apportionment-and-atmospheric-carrying-capacity |
| `f52ed80f-79af-4497-bd79-ab3f5ad19565` | website / events | TERI - ICIMOD - NTNC - UK International Development Consultation Highlights Pathways for Forest Fire Managemen | https://teriin.org/event/teri-icimod-ntnc-uk-international-development-consultation-highlights-pathways-forest-fire |

---

### Q020 - What research is TERI undertaking on industrial decarbonization?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's industrial-decarbonisation research is anchored in the programme 'Accelerating Industrial Decarbonisation in India', whose stated aim is to build an evidence base and agree a roadmap for industrial decarbonisation in key sectors by 2024 - iron & steel, cement and related MSMEs - through policies, low-carbon technologies, finance and corporate commitment, with three main activities: developing targets and sectoral roadmaps, diffusion and demonstration of low-carbon technologies, and securing corporate commitment for near-zero-carbon operations. Related outputs: 'Industry decarbonisation pathways - iron & steel and cement value chains'; the report 'Practices and Solutions: Accelerating Indian Industry Decarbonisation'; the GCCA India-TERI Decarbonisation Roadmap for the Indian Cement Sector (Net-Zero CO2 by 2070); the policy brief 'Solar Thermal Energy for Industrial Decarbonization' (Aug 2026); work on electrifying Indian MSMEs; green market instruments for steel; low-carbon hydrogen's role; and the Industry Charter for Near Zero Emission Ambition by 2050.

**Expected facts**

- 'Accelerating Industrial Decarbonisation in India' aims to build an evidence base and agree a roadmap for industrial decarbonisation in key sectors by 2024.
- The sectors covered are iron & steel, cement and related micro, small and medium enterprises.
- The programme works through policies, low-carbon technologies, finance and corporate commitment.
- Its three main activities are developing targets and sectoral roadmaps, diffusion (scaling-up) and demonstration (pilots) of low-carbon technologies, and securing corporate commitment for near-zero-carbon operations.
- TERI runs a project on industry decarbonisation pathways for iron & steel value chains and cement/built environment value chains.
- TERI launched the report 'Practices and Solutions: Accelerating Indian Industry Decarbonisation'.
- TERI and GCCA India produced the Decarbonisation Roadmap for the Indian Cement Sector (Net-Zero CO2 by 2070).
- TERI published the policy brief 'Solar Thermal Energy for Industrial Decarbonization' (August 2026) and called for accelerated adoption of solar thermal technologies to decarbonise Indian industry.
- TERI convenes the Industry Charter for Near Zero Emission Ambition by 2050, whose focus areas include energy efficiency, renewable energy, circular economy, low-carbon solutions across the supply chain, carbon sequestration, technology demonstration and the business-policy interface.

**Expected entities**: Accelerating Industrial Decarbonisation in India, GCCA India, Industry Charter for Near Zero Emission Ambition by 2050

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c519f60b-7442-4f84-99fa-d732bd36201d` | website / ongoing_projects | Accelerating Industrial Decarbonisation in India | https://teriin.org/project/accelerating-industrial-decarbonisation-india |
| `ef74280d-97d2-4878-83af-11e72aeaecb2` | website / ongoing_projects | Industry decarbonisation pathways - Iron & steel value chains, Cement built environment & value chains, Corpor | https://teriin.org/project/industry-decarbonisation-pathways-iron-steel-value-chains-cement-built-environment-value |
| `3a873e17-e1be-4c6f-80e9-b5453f2ce1fe` | website / ongoing_projects | Launch of report 'Practices and Solutions: Accelerating Indian Industry Decarbonisation' | https://teriin.org/project/launch-report-practices-and-solutions-accelerating-indian-industry-decarbonisation |
| `2a310697-5393-4e1f-bd72-f22179e32011` | website / policy_brief | Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070 | https://teriin.org/policy-brief/decarbonization-roadmap-indian-cement-sector-net-zero-co2-2070 |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `a1156006-18d9-44ec-abe9-2384f493e99f` | website / press_release | TERI Calls for Accelerated Adoption of Solar Thermal Technologies to Decarbonize India’s Industrial Sector | https://teriin.org/press-release/teri-calls-accelerated-adoption-solar-thermal-technologies-decarbonize-indias |
| `4bf09b06-a4dc-4daa-bb80-45fdbea9d4b9` | website / page | Industry Charter for Near Zero Emission Ambition by 2050 | https://teriin.org/industry-charter-near-zero-emission-ambitio-2050 |
| `c4f6af5a-6169-414f-a13f-1a681ea0bee6` | website / events | Green Market Instruments for Industry Decarbonisation – Spotlight on Steel in Emerging Economies | https://teriin.org/event/green-market-instruments-industry-decarbonisation-spotlight-steel-emerging-economies |
| `0795e053-4ee5-4a87-8dcd-33e6ac01f292` | website / feature_articles | Why low-carbon hydrogen is an important piece in the industrial decarbonisation puzzle | https://teriin.org/opinion/why-low-carbon-hydrogen-important-piece-industrial-decarbonisation-puzzle |

**Notes**: Near-duplicate of Q048; keep gold answers consistent.

---

### Q021 - How does TERI contribute to national missions and international climate commitments?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI contributes to national missions and international climate commitments through modelling, negotiation support and convening. National: the missions under the National Action Plan for Climate Change - especially the National Solar Mission - were delineated to a large extent from TERI's modelling; TERI provided inputs to the National Mission on Sustainable Habitat, to India's Environment Policy 2006, to five-year plans and the Integrated Energy Plan Report; and it has briefed government on India's 2030 and 2035 NDCs. International: TERI provided inputs for India's negotiating positions at UNFCCC, CBD and WTO; it maintains dedicated engagement pages for COP26-COP30 and India's G20 Presidency; it hosted an official UNFCCC press conference at COP30; and it runs Act4Earth (COP Compass and SDG Charter) to feed multilateral processes.

**Expected facts**

- The missions under the National Action Plan for Climate Change, especially the National Solar Mission, were delineated to a large extent from TERI's modelling and analytics.
- TERI provided inputs to the National Mission on Sustainable Habitat under India's National Action Plan on Climate Change.
- TERI provided the inputs for India's negotiating positions at the UNFCCC, the Convention on Biological Diversity and the WTO.
- TERI engages at the UNFCCC COPs, with dedicated pages for COP26 through COP30, and hosted an official UNFCCC press conference at COP30 in November 2025.
- TERI engaged with India's G20 Presidency and commented on the G20 New Delhi Leaders' Declaration.
- TERI runs the Act4Earth initiative (COP Compass and SDG Charter) to promote inclusive and equitable transitions through multilateral mechanisms.
- TERI briefed government on India's 2035 NDC jointly with the We Mean Business Coalition.

**Expected entities**: National Action Plan for Climate Change, National Solar Mission, National Mission on Sustainable Habitat, UNFCCC, CBD, WTO, G20, COP30, Act4Earth

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `70326006-9cc2-4e08-8f7b-55798dd65a51` | website / services | Policy intervention and analysis |  |
| `7da36f61-4f2e-4297-8ce4-125150ba5bf5` | website / page | TERI @ G20 | https://teriin.org/teri-at-g20 |
| `65cdeb2f-e4c0-4faa-ae6a-891223cac8d6` | website / page | ACT4EARTH | https://teriin.org/act4earth |
| `b9f4fdc0-155f-4c8f-9004-d46b582f2aad` | website / page | TERI'S CONTRIBUTIONS TO BUSINESS ACTION ON CLIMATE CHANGE | https://teriin.org/Shaping-India-CLimate-Policy-discourse |
| `66869477-c0f7-42a7-a6e3-93574297ba27` | website / page | TERI @ COP28 | https://teriin.org/teri-at-cop28 |
| `c3211d7c-cac4-43fd-b0e7-66b8f8cb37b2` | website / page | TERI @ COP30 | https://teriin.org/teri-at-cop30 |
| `baedf008-217b-4716-8bdd-05c60886896f` | website / press_release | India Champions Industry-Led Climate Action at COP30: TERI Hosts High-Level UNFCCC Press Conference on Net-Zer | https://teriin.org/press-release/india-champions-industry-led-climate-action-cop30-teri-hosts-high-level-unfccc-press |

---

### Q022 - What are TERI's most impactful research contributions in the last five years?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: comparison / aggregation
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `67523149-2bb5-4679-a353-e4e317852fb8` | website / page | Creating Impacts, Transforming Lives | https://teriin.org/creating-impacts-transforming-lives |
| `08c11465-0bee-4bc2-be53-1eaa23938efe` | website / page | Strategic Document Vision: 2025–30 | https://teriin.org/Strategic-Document-Vision-2025–30 |

**Notes**: UNANSWERABLE AS ASKED. 'Most impactful' is a value judgement and the corpus contains no impact ranking, citation counts, outcome metrics or evaluation scores. A five-year window (2021-08-19..2026-08-19) is computable over published_at, but nothing in any store orders results by impact. The 'Creating Impacts, Transforming Lives' publication is TERI's own curated success-story set but is not scoped to the last five years. A human must define the impact criterion before this can be gold.

---

### Q023 - What evidence-based policy tools has TERI developed?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Evidence-based policy tools TERI has developed, as named in the corpus: the GRIHA rating system (with MNRE, 2007) and the GRIHA Infrastructure Rating for logistics parks and warehouses (2026); the Green Budgeting Toolkit 2.0 (Sept 2025); the SDG Blueprint Tool for Sustainable Agriculture; the Freight Greenhouse Gas Calculator; the Green Port Performance Index (GPPI); the Integrated Air Quality Index (AQI) and Liveability Framework; the Vulnerability Index Tool for health vulnerability assessment; the MTCoE Daylight Plugin Tool; GHG calculators covering Scope 1, 2 and 3 emissions; the Transport Demand Management toolkit; the Catalogue of Indian Emission Inventory Reports; and the UrjaSanchay energy-storage data dashboard.

**Expected facts**

- TERI developed the GRIHA green-building rating system jointly with the Ministry of New and Renewable Energy in 2007, and launched a GRIHA Infrastructure Rating for logistics parks and warehouses in 2026.
- TERI launched the Green Budgeting Toolkit 2.0 in September 2025 to align fiscal policy with climate goals.
- TERI developed the SDG Blueprint Tool for Sustainable Agriculture.
- TERI developed a Freight Greenhouse Gas Calculator.
- TERI developed the Green Port Performance Index (GPPI).
- TERI is developing an Integrated Air Quality Index (AQI) and Liveability Framework.
- TERI developed a Vulnerability Index Tool for health vulnerability assessment.
- TERI has developed GHG calculators covering Scope 1, 2 and 3 emissions.
- TERI launched the MTCoE Daylight Plugin Tool at WSDS 2024.
- TERI runs the UrjaSanchay platform with an interactive energy-storage data dashboard.

**Expected entities**: GRIHA, Green Budgeting Toolkit 2.0, SDG Blueprint Tool for Sustainable Agriculture, Freight Greenhouse Gas Calculator, Green Port Performance Index, Vulnerability Index Tool, Daylight Plugin Tool, UrjaSanchay

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `98800b2a-5011-43be-ad73-6039b898ca8e` | website / events | LAUNCH OF GRIHA INFRASTRUCTURE RATING FOR LOGISTICS PARKS AND WAREHOUSES | https://teriin.org/event/launch-griha-infrastructure-rating-logistics-parks-and-warehouses |
| `df038222-1e13-4bae-b7db-db6948f5aab7` | website / press_release | TERI Unveils Green Budgeting Toolkit 2.0 to Power Greener Public Finance and Drive the Green Economy | https://teriin.org/press-release/teri-unveils-green-budgeting-toolkit-20-power-greener-public-finance-and-drive-green |
| `a49604fc-e069-4d9f-b2c0-5413b9f8148c` | website / news | TERI launches green budgeting Toolkit 2.0 to align fiscal policy with climate goals | https://teriin.org/news/teri-launches-green-budgeting-toolkit-20-align-fiscal-policy-climate-goals |
| `2566f71f-afc8-4da2-8c40-253184d05591` | website / page | SDG Blueprint Tool for Sustainable Agriculture | https://teriin.org/SDG-Blueprint-tool-for-Sustainable-Agriculture |
| `0ab481b1-5840-49d7-a334-4083709d207a` | website / ongoing_projects | Freight Greenhouse Gas Calculator | https://teriin.org/project/freight-greenhouse-gas-calculator |
| `ea40133f-b34c-4ac7-b02b-0da92afb00ab` | website / policy_brief | Green Port Performance Index (GPPI) Measuring Progress, Powering Green Transformation | https://teriin.org/policy-brief/green-port-performance-index-gppi-measuring-progress-powering-green-transformation |
| `c402762d-53fc-4401-ace6-2bf25d5be8f3` | website / ongoing_projects | Development and Implementation of an Integrated Air Quality Index (AQI) and Liveability Framework for Krisala  | https://teriin.org/project/development-and-implementation-integrated-air-quality-index-aqi-and-liveability-framework |
| `da24182b-dd8a-4c14-af99-2edca57cde73` | website / article | Vulnerability Index Tool: Vulnerability assessment for health | https://teriin.org/article/vulnerability-index-tool-vulnerability-assessment-health |
| `6ca26c81-3a12-41ea-b138-4b19582c93b6` | website / article | WSDS2024: Launch of MTCoE’s Daylight Plugin Tool at the thematic session "Advancing Sustainable Building Pract | https://teriin.org/article/wsds2024-launch-mtcoes-daylight-plugin-tool-thematic-session-advancing-sustainable-building |
| `4eab067f-425a-4299-afee-f542e3a007f3` | website / services | Research, Innovation & Impact Assessment |  |
| `ec42a9ea-7d46-46b1-9263-a7a88aaea1c4` | website / ongoing_projects | UrjaSanchay: Energy Storage in India - Knowledge Systems | https://teriin.org/project/urjasanchay-energy-storage-india-knowledge-systems |

**Notes**: The list is assembled from many independent sources; no single authoritative tools catalogue exists, so completeness is not gradable. Score on correctness of the tools named.

---

### Q024 - How is TERI supporting the implementation of Sustainable Development Goals (SDGs)?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports SDG implementation through a TERI-wide SDG and Policy Coordination (SPC) initiative that facilitates integrated, multi-disciplinary research on resources, energy and environment-related SDGs and coordinates a continuing series of Think Pieces, Policy Briefs and Discussion Papers. It publishes SDG-interface material for each of the 17 goals, runs the SDG Charter strand of Act4Earth (identifying gaps and recommending measures to mainstream sustainable development in policy agendas), and produces work on SDG-climate synergies and multilateralism. TERI states its mission is to be a knowledge-based agent of change for a shared vision of global sustainable development, and that it brings its Millennium Development Goals experience to SDG implementation.

**Expected facts**

- A TERI-wide initiative on SDG and Policy Coordination (SPC) facilitates integrated and multi-disciplinary research on resources, energy and environment-related SDGs and policy across the institute.
- The SPC coordinates continuing publication of policy products including Think Pieces, Policy Briefs and Discussion Papers.
- TERI publishes SDG-interface pages for all 17 SDGs, including documents on the SDG 7 and SDG 13 interfaces with sustainable agriculture.
- The SDG Charter is one of the two components of TERI's Act4Earth initiative and focuses on identifying gaps and recommending measures to mainstream sustainable development within policy agendas.
- TERI produced policy briefs on synergies between climate action and the SDGs and their implications for multilateralism.
- TERI seeks to develop deeper understanding and expertise around SDGs, particularly those related to energy, environment and natural resources.

**Expected entities**: SDG and Policy Coordination (SPC), SDG Charter, Act4Earth

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `5f273cf0-9139-4990-ad3d-048ccd81d310` | website / page | Sustainable Development Goals | https://teriin.org/sustainable-development-goals |
| `65cdeb2f-e4c0-4faa-ae6a-891223cac8d6` | website / page | ACT4EARTH | https://teriin.org/act4earth |
| `0f23e106-b601-46f4-861d-15d991f97038` | website / page | SDG 7: AFFORDABLE AND CLEAN ENERGY | https://teriin.org/SDG-7-Affordable-and-Clean-Energy |
| `397b8e72-647d-414f-bb2b-2ac59c4cf96d` | website / page | SDG 13. CLIMATE ACTION | https://teriin.org/SDG-13-Climate-Action |
| `ad074197-e7d9-415e-b74d-01616c598ee2` | website / policy_brief | Synergies between Climate Action and SDGs: Implications for Multilateralism | https://teriin.org/policy-brief/synergies-between-climate-action-and-sdgs-implications-multilateralism |
| `fba0189e-1cdd-480a-af54-077173f45ff8` | website / press_release | Global experts convene at TERI's Act4Earth Dialogue to promote SDG-climate synergies ahead of HLPF 2024 | https://teriin.org/press-release/global-experts-convene-teris-act4earth-dialogue-promote-sdg-climate-synergies-ahead |

---

### Q025 - What are TERI's ongoing projects?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: aggregation/count
- **Temporal scope**: temporal_mode=current; requested_period=as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17; expected_validity_window=CMS 'ongoing' classification at snapshot time

**Gold answer**

> As of the corpus snapshot the CMS records 594 project nodes classified as ongoing (source_type='website', bundle='ongoing_projects'). Counting every theme value on each project, they are distributed across themes led by Environment (108), Energy (74), Climate Change (69), Sustainable Agriculture (48), Energy Efficiency (40), Air (37), Water (35), Waste (32), Forest & Biodiversity (30), Transport (28), Sustainable Habitat (26) and Buildings (21), with 98 carrying no theme at all; and across programmes led by Natural Resources and Climate (175), Energy (117) and Sustainable Habitat (45). A correct answer must be scoped and representative rather than exhaustive.

**Expected facts**

- The CMS records 594 ongoing project nodes as of the snapshot.
- Counting every value in the field_ongoing_theme array, the largest ongoing-project themes are Environment (108), Energy (74), Climate Change (69), Sustainable Agriculture (48), Energy Efficiency (40), Air (37), Water (35) and Waste (32). (Counting only the first array element - the original derivation - gives Environment 64, Climate Change 46, Energy 44, Sustainable Agriculture 41, which understates every theme and mis-orders Energy and Climate Change.)
- The largest ongoing-project programmes are Natural Resources and Climate (175), Energy (117) and Sustainable Habitat (45).
- 98 ongoing project nodes carry no theme value.

**Reproducible derivations**

- `SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='ongoing_projects' -> 594`
- `CORRECTED all-values derivation: SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='ongoing_projects' AND JSON_CONTAINS(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme'), '"<theme>"') -- run per theme; the superseded first-element form was JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme[0]'))`
- `SELECT JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_programme[0]')), COUNT(*) ... GROUP BY 1`

**Notes**: expected_count = 594. CAVEAT the grader must apply: 'ongoing' is the CMS bundle classification, not a verified activity status - field_ongoing_start_date values run from 2017 to 2026 and there is no end-date field, so some 'ongoing' nodes are almost certainly finished. The knowledge graph CANNOT answer this question: all 1,374 assertions and all 1,071 PROJECT entities derive from completed_projects only. JUDGEMENT CORRECTION: the original theme distribution used only the FIRST element of the field_ongoing_theme JSON array, but 135 of 594 ongoing projects carry two or more themes (100 have 2, 24 have 3, 5 have 4, 3 have 5, 1 has 7, 2 have 8, 1 has 19). Every per-theme figure was therefore understated and the Energy / Climate Change ordering was wrong. The total of 594 and the 98 untheme d nodes are unaffected and remain confirmed.

---

### Q026 - Which renewable energy projects is TERI currently implementing?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT COUNT(*) FROM documents WHERE bundle='ongoing_projects' AND JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme[0]'))='Electricity and Renewables' -> 5; theme 'Energy' -> 44; theme 'Energy Access' -> 10`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `017c11bf-7ad0-4a0a-99d8-3cc51051d7db` | website / ongoing_projects | Enhancing women’s empowerment as employees and entrepreneurs in decentralised renewable energy | https://teriin.org/project/enhancing-womens-empowerment-employees-and-entrepreneurs-decentralised-renewable-energy |
| `ec42a9ea-7d46-46b1-9263-a7a88aaea1c4` | website / ongoing_projects | UrjaSanchay: Energy Storage in India - Knowledge Systems | https://teriin.org/project/urjasanchay-energy-storage-india-knowledge-systems |
| `75857f7d-230b-4ec6-8dd7-9cc0b5448288` | website / ongoing_projects | Renewable Energy Transition in South Asia: Role of Regional Energy Trade | https://teriin.org/project/renewable-energy-transition-south-asia-role-regional-energy-trade |
| `2ab73442-453e-46b5-a893-0beeb57157c9` | website / press_release | Rajasthan Renewable Energy Corporation Limited and TERI Sign MoU to Advance Rajasthan’s Clean Energy Transitio | https://teriin.org/press-release/rajasthan-renewable-energy-corporation-limited-and-teri-sign-mou-advance-rajasthans |

**Notes**: NO CLOSED SET DERIVABLE. There is no 'renewable energy' facet on projects: the nearest CMS themes are 'Electricity and Renewables' (5 ongoing nodes), 'Energy' (44) and 'Energy Access' (10), none of which means 'renewable energy project'. Keyword matching over titles is not authoritative and 'currently implementing' cannot be verified (no project end dates). A human must define the inclusion rule.

---

### Q027 - What climate change projects are currently underway?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: aggregation/count
- **Temporal scope**: temporal_mode=current; requested_period=as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> The CMS classifies 69 ongoing project nodes under the theme 'Climate Change' (counting the theme anywhere in the field_ongoing_theme array; 46 carry it as the first element). Verified current examples include 'SHEETAL: Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All' and 'Preparedness towards implementing Enhanced Transparency Framework and tracking NDCs', both of which carry field_ongoing_theme ["Climate Change"].

**Expected facts**

- 69 ongoing project nodes carry the CMS theme 'Climate Change' anywhere in their field_ongoing_theme array as of the snapshot (46 carry it as the first array element).
- Ongoing climate-change projects include 'SHEETAL: Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All' (document 0095f7d8, field_ongoing_theme ["Climate Change"]).
- Ongoing climate-change work includes 'Preparedness towards implementing Enhanced Transparency Framework and tracking NDCs' (document 4043a8f6, field_ongoing_theme ["Climate Change"]).

**Reproducible derivations**

- `CORRECTED: SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='ongoing_projects' AND JSON_CONTAINS(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme'), '"Climate Change"') -> 69 (superseded first-element form -> 46)`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0095f7d8-821f-408d-84b9-f488b96a67f1` | website / ongoing_projects | SHEETAL: Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All | https://teriin.org/project/sheetal-alliance-sustainable-habitat-energy-efficiency-and-thermal-comfort-all-cooling |
| `4043a8f6-e116-4cd8-92ee-d6afe44f1e24` | website / ongoing_projects | Preparedness towards implementing Enhanced Transparency Framework and tracking NDCs under the Paris Agreement | https://teriin.org/project/preparedness-towards-implementing-enhanced-transparency-framework-and-tracking-ndcs-under |

**Notes**: expected_count = 46 (single-valued primary theme). If a grader counts projects whose theme array contains 'Climate Change' at any position the number may differ; the facet SQL above defines the gold count. Same 'ongoing != verified active' caveat as Q025. JUDGEMENT CORRECTIONS: (1) expected_count raised from 46 to 69 - the original used field_ongoing_theme[0] only, excluding projects where Climate Change is a secondary theme, which is the wrong reading of 'What climate change projects are underway?'. (2) BOTH originally cited example documents were wrong: 0d175a5b 'Just Transition' is themed ["Electricity and Renewables","Energy"] and 4b77a379 'Mapping Policies and Stakeholders on Climate Adaptation' is themed ["Resource Efficiency & Governance"] - neither is a Climate Change project in the CMS. They have been replaced with two verified Climate Change projects. (3) The second case also shows CMS theme assignment is noisy: a project titled 'Climate Adaptation' is not themed Climate Change, so theme-derived sets carry real classification risk.

---

### Q028 - What projects support sustainable agriculture and rural livelihoods?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `theme 'Sustainable Agriculture' ongoing -> 41; no CMS facet for 'rural livelihoods'`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `270b7a01-39ba-497e-930f-911e390fc778` | website / ongoing_projects | TERI-CFCL Centre of Excellence (CoE) for Advanced and Sustainable Agriculture Solutions | https://teriin.org/project/teri-cfcl-centre-excellence-coe-advanced-and-sustainable-agriculture-solutions |
| `21102beb-b5ff-4d18-8ede-62354fb5bb2a` | website / ongoing_projects | TERI’s Mycorrhizal Platforms: Advancing Soil Health and Sustainable Agriculture | https://teriin.org/project/teris-mycorrhizal-platforms-advancing-soil-health-and-sustainable-agriculture |
| `90e24426-1d56-4f13-afda-46bd0916799a` | website / ongoing_projects | Empowering Rural Livelihoods through Agroforestry in Aligarh | https://teriin.org/project/empowering-rural-livelihoods-through-agroforestry-aligarh |
| `4a66d21b-22bc-4e29-ac5b-5d0ae311437a` | website / ongoing_projects | Innovative interventions to address malnutrition and enhance the livelihood of ST communities | https://teriin.org/project/innovative-interventions-address-malnutrition-and-enhance-livelihood-st-communities |
| `5776adb9-6186-44d6-be43-8a9189767433` | website / page | Seeds of Hope | https://teriin.org/seeds-of-hope |

**Notes**: TWO-PART QUESTION, ONE FACET. 'Sustainable Agriculture' is a CMS theme (41 ongoing nodes) but 'rural livelihoods' is not a theme, tag facet or programme; livelihood projects sit under Social Transformation, Forest & Biodiversity and Environment and Public Health. The union is not derivable, so a human must fix the scope.

---

### Q029 - What initiatives is TERI running for clean energy access in rural areas?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=current; requested_period=as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> TERI's clean-energy-access work for rural areas is carried out under the CMS theme 'Energy Access' (18 ongoing project nodes at snapshot counting the theme at any array position; 10 as the first element) and the Lighting a Billion Lives (LaBL) initiative. Current and recent examples: enhancing women's empowerment as employees and entrepreneurs in decentralised renewable energy; Enhancing Energy Access through Women Entrepreneurs in Bihar - Clean Cookstove Programme; Sustainable energy in Micro-enterprises for Income and Livelihood Enhancement (SMILE); Supporting clean energy adoption in Rural India; PPP models for deploying DRE and energy-efficiency systems in MSME clusters; estimating carbon benefits from shifting rural households to improved cookstoves; and LaBL 2.0 as an accelerator for India's SDG 7 journey. TERI also offers a CSR service replacing kerosene lanterns with solar lighting devices.

**Expected facts**

- The CMS records 18 ongoing project nodes carrying the 'Energy Access' theme anywhere in their field_ongoing_theme array at snapshot (10 carry it as the first array element).
- Lighting a Billion Lives (LaBL) is TERI's rural energy-access initiative, now described in an LaBL 2.0 form linked to India's SDG 7 journey.
- TERI runs 'Enhancing Energy Access through Women Entrepreneurs in Bihar - Clean Cookstove Program'.
- TERI runs 'Sustainable energy in Micro-enterprises for Income and Livelihood Enhancement (SMILE)'.
- TERI supports PPP models for deployment of decentralised renewable energy and energy-efficiency systems in identified MSME clusters.
- TERI's CSR clean-energy service replaces kerosene/paraffin lanterns with solar lighting devices to give better illumination and a smoke-free indoor environment for women.

**Expected entities**: Lighting a Billion Lives, SMILE, Clean Cookstove Program Bihar, Energy Access

**Reproducible derivations**

- `CORRECTED: SELECT COUNT(*) FROM documents WHERE bundle='ongoing_projects' AND source_type='website' AND JSON_CONTAINS(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme'), '"Energy Access"') -> 18 (superseded first-element form -> 10)`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `dd64ff29-b63a-43fd-84aa-d6e11378b53a` | website / ongoing_projects | Enhancing Energy Access through Women Entrepreneurs in Bihar - Clean Cookstove Program | https://teriin.org/project/enhancing-energy-access-through-women-entrepreneurs-bihar-clean-cookstove-program |
| `96db4aa7-af23-4a1c-a4ba-6a81c6d965b8` | website / ongoing_projects | Sustainable energy in Micro-enterprises for Income and Livelihood Enhancement (SMILE) | https://teriin.org/project/sustainable-energy-micro-enterprises-income-and-livelihood-enhancement-smile |
| `64b2e8e7-bcda-46c2-be5f-18f13d69473f` | website / ongoing_projects | Supporting clean energy adoption in Rural India | https://teriin.org/project/supporting-clean-energy-adoption-rural-india |
| `f083534d-1c50-423a-8b26-d86c156a7a59` | website / ongoing_projects | Support PPP models for deployment of DRE and EE systems in identified MSME clusters in rural India | https://teriin.org/project/support-ppp-models-deployment-dre-and-ee-systems-identified-msme-clusters-rural-india |
| `a9b51697-df0e-4b86-9dbb-d73e8c122560` | website / ongoing_projects | Estimate the potential carbon benefit earn by shifting households to improved cookstoves | https://teriin.org/project/estimate-potential-carbon-benefit-earn-shifting-households-improved-cookstoves |
| `bfb8dbeb-afc2-4da7-8677-a9ddeffca937` | website / article | Lighting the Last Mile: How TERI’s LaBL 2.0 Can Accelerate India’s SDG 7 Journey | https://teriin.org/article/lighting-last-mile-how-teris-labl-20-can-accelerate-indias-sdg-7-journey |
| `769f4073-d894-496a-8386-322f8deadf91` | website / services | CSR engagements to provide clean energy solutions |  |
| `5ce4fb40-32f9-4dbe-a1bb-aeeb0b1f87c5` | website / completed_projects | Lighting a Billion Lives | https://teriin.org/project/lighting-billion-lives |

**Notes**: Note the theme facet mixes rural and non-rural work; five of the ten Energy Access nodes date from 2017 or 2021 so 'running' is uncertain for them. JUDGEMENT CORRECTION: count raised from 10 to 18 for the same first-element aggregation error described in Q025/Q027.

---

### Q030 - What projects focus on sustainable urban development?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `ongoing themes: Sustainable Habitat 12, Cities 7, Buildings 19, Transport 20 (no 'sustainable urban development' facet)`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `07ea5072-b97a-450b-99dd-95e535ee6685` | website / services | Policy, Strategic Planning & Advocacy |  |
| `e5911c7d-d2b6-410a-8c6e-233b97c129a2` | website / page | Transport and Urban Governance (TUGD) | https://teriin.org/newsletter-transport-urban-governance |
| `d6c23474-8f0a-4502-925d-33d07e1c74d5` | website / ongoing_projects | Improving Urban Air Quality by Facilitating Piloting of Clean Air Zones in Vijayawada & Visakhapatnam | https://teriin.org/project/improving-urban-air-quality-facilitating-piloting-clean-air-zones-vijayawada-visakhapatnam |

**Notes**: AMBIGUOUS THEME MAPPING. 'Sustainable urban development' maps to no single CMS facet; it plausibly spans Sustainable Habitat (12 ongoing), Cities (7), Buildings (19) and Transport (20), plus urban air-quality and urban-waste projects filed under Air and Waste. Any single number would be an arbitrary choice. A human must fix the scope.

---

### Q031 - Which TERI projects contribute to SDG 7 (Affordable and Clean Energy)?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT tag FROM documents_tag WHERE tag LIKE '%SDG%' -> 'SDGs'(23), 'SDG'(17), 'SDG 11'(1), 'SDG 4.7'(1) and free-text compounds; no per-goal facet`
- `documents_theme has no SDG themes`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0f23e106-b601-46f4-861d-15d991f97038` | website / page | SDG 7: AFFORDABLE AND CLEAN ENERGY | https://teriin.org/SDG-7-Affordable-and-Clean-Energy |
| `5f273cf0-9139-4990-ad3d-048ccd81d310` | website / page | Sustainable Development Goals | https://teriin.org/sustainable-development-goals |
| `bfb8dbeb-afc2-4da7-8677-a9ddeffca937` | website / article | Lighting the Last Mile: How TERI’s LaBL 2.0 Can Accelerate India’s SDG 7 Journey | https://teriin.org/article/lighting-last-mile-how-teris-labl-20-can-accelerate-indias-sdg-7-journey |

**Notes**: NO SDG-TO-PROJECT MAPPING EXISTS IN ANY STORE. documents_theme carries no SDG values; documents_tag has only 23 'SDGs' / 17 'SDG' tags plus a handful of free-text compounds, none of which map projects to SDG 7; Neo4j holds no SDG nodes. The SDG 7 page (0f23e106) is about the SDG 7 - sustainable agriculture policy interface, not a project list. Any list a chatbot returns would be an inference, not a corpus fact.

---

### Q032 - Which TERI projects contribute to SDG 13 (Climate Action)?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `397b8e72-647d-414f-bb2b-2ac59c4cf96d` | website / page | SDG 13. CLIMATE ACTION | https://teriin.org/SDG-13-Climate-Action |
| `5f273cf0-9139-4990-ad3d-048ccd81d310` | website / page | Sustainable Development Goals | https://teriin.org/sustainable-development-goals |
| `08b5053a-4d55-4128-a758-da9f5a13adc3` | website / research_papers | Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13 | https://teriin.org/research-paper/artificial-intelligence-climate-resilience-evaluating-contributions-sdg-13 |

**Notes**: Same structural gap as Q031: no SDG-to-project mapping in MySQL, Neo4j or Qdrant payloads. The SDG 13 page (397b8e72) covers the SDG 13 - sustainable agriculture policy interface only. One research paper explicitly evaluates contributions to SDG 13 ('Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13') but that is a publication, not a project set.

---

### Q033 - What are TERI's current international collaborative projects?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_country_tmp')), COUNT(*) FROM documents WHERE bundle='ongoing_projects' GROUP BY 1 -> NULL 486, 'India' 105, 'UAE' 1, 'India,Nepal' 1, 'Indonesia,Philippines,Thailand,Vietnam' 1`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `8b15b308-c364-46fb-ba6e-0f6535c1f6a1` | website / ongoing_projects | Climate Skills - Seeds for a Transition India | https://teriin.org/project/climate-skills-seeds-transition-india |
| `ec42a9ea-7d46-46b1-9263-a7a88aaea1c4` | website / ongoing_projects | UrjaSanchay: Energy Storage in India - Knowledge Systems | https://teriin.org/project/urjasanchay-energy-storage-india-knowledge-systems |
| `75857f7d-230b-4ec6-8dd7-9cc0b5448288` | website / ongoing_projects | Renewable Energy Transition in South Asia: Role of Regional Energy Trade | https://teriin.org/project/renewable-energy-transition-south-asia-role-regional-energy-trade |
| `caff274b-f7df-481a-b1fb-ca1c5d1ba579` | website / ongoing_projects | Assess the Cost of Rangeland Degradation, Deforestation, and Desertification in the Kingdom of Saudi Arabia | https://teriin.org/project/assess-cost-rangeland-degradation-deforestation-and-desertification-kingdom-saudi-arabia |
| `4b77a379-bff3-4335-a2b8-e6a98ee470ad` | website / ongoing_projects | Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South | https://teriin.org/project/mapping-policies-and-stakeholders-climate-adaptation-crop-based-systems-global-south |

**Notes**: GEOGRAPHY FIELD IS 82% EMPTY. field_ongoing_country_tmp is NULL on 486 of 594 ongoing projects, so no reliable international set can be derived; only three rows name a non-India country. Individually verifiable international projects exist (Climate Skills - Seeds for a Transition across India/Brazil/Mexico/Indonesia/Vietnam with British Council and HSBC; StoREin Indo-German energy storage with GIZ, BMUKN, MNRE, Fraunhofer IEE and IIT Bombay; Renewable Energy Transition in South Asia; rangeland degradation costing for the Kingdom of Saudi Arabia) but completeness cannot be established.

---

### Q034 - Who are the partners associated with TERI's major projects?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: relationship / aggregation
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT predicate, COUNT(*) FROM documents_assertion GROUP BY 1 -> FUNDED_BY 957, LED_BY 416, PARTNER_OF 1 (all from completed_projects CMS fields)`
- `field_ongoing_sponsors non-null on 377 of 594 ongoing projects`

**Claim IDs**: `claim_29a3cf59355d9eee2bf213c0`, `claim_340c4e769a28fad600ddd52b`, `claim_0badb921232295e7e39fd5e0`

**Notes**: 'MAJOR' IS UNDEFINED AND THE PARTNER RELATION IS ESSENTIALLY ABSENT. The claim store has exactly one PARTNER_OF assertion; what it does hold is 957 FUNDED_BY (498 distinct funder organisations) and 416 LED_BY (137 distinct PIs) claims, all extracted from completed_projects CMS fields, with valid_until values that effectively stop in 2021 (only 5 claims end 2022 or later). Funder is not partner, ongoing-project sponsors were never promoted to claims, and no size or importance attribute exists to select 'major' projects.

---

### Q035 - What innovations and technologies are being demonstrated under ongoing projects?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> The technologies TERI showcases as demonstrated and deployed are, per its Technologies page: mycorrhizae-based biofertilizers (In Vitro Mass Production Technology, marketed as tablets, granules and powder); high-quality planting material via micropropagation (70+ protocols); biogenic nanotechnology nano-fertilizers for climate-smart farming; TERI biomass gasifiers (throat-less patented downdraft design, multi-fuel, for heat and power in rural, commercial and industrial applications); smokeless clean-combustion cookstoves (2 kWth, 15-20% more effective than conventional stoves); Oilzapper (microbial cocktail; over 1.3 million tonnes of contaminated soil treated globally as of March 2025); TEAM (TERI's Enhanced Acidification and Methanation) for organic waste to biogas; fly-ash-based ceramic membrane filters in submerged membrane bioreactors for decentralised wastewater reuse; and TADOX, a patented advanced-oxidation wastewater treatment. Related service technologies include MEOR (microbial enhanced oil recovery) and PDB (paraffin-degrading bacteria), Xanthan gum production, and wasteland reclamation using mycorrhizal fungi.

**Expected facts**

- TERI's In Vitro Mass Production Technology produces mycorrhizae-based biofertilizers, available as tablets, granules and powder.
- TERI's micropropagation centre supplies tissue-cultured plants and has over 70 micropropagation protocols.
- TERI biomass gasifiers use a throat-less patented downdraft design with multi-fuel capability, customisable for heat and power in rural, commercial and industrial applications.
- TERI's smokeless clean-combustion cookstove has a thermal capacity of 2 kWth, is 15-20% more effective than conventional stoves and uses wood pieces and briquettes.
- Oilzapper is a microbial 'cocktail' developed by TERI that breaks hydrocarbons down into water and fatty acids; it had treated over 1.3 million tonnes of contaminated soil globally as of March 2025.
- TEAM (TERI's Enhanced Acidification and Methanation) converts organic waste into biogas with a shorter processing time than other biogas plants.
- TERI demonstrated fly-ash-based ceramic membrane filters in submerged membrane bioreactors for sewage treatment, cheaper than commercial membranes and suitable for decentralised on-site reuse.
- TADOX (TERI Advanced Oxidation Technology) is a patented end-to-end industrial and municipal wastewater treatment technology.
- TERI developed MEOR (microbial enhanced oil recovery) and PDB (paraffin-degrading bacteria) technologies for oil wells and pipelines.

**Expected entities**: Mycorrhizae biofertilizer, Micropropagation Technology Park, TERI biomass gasifier, clean combustion cookstove, Oilzapper, TEAM, ceramic membrane MBR, TADOX, MEOR, PDB

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `555ac39f-260f-41f4-a03d-e337e02fc844` | website / page | Micropropagation Technology Park | https://teriin.org/technology/micropropagation-technology-park |
| `f17bd41c-cbfb-4935-87fc-6d207cff88e8` | website / page | Biomass Gasifier for Thermal and Power applications | https://teriin.org/technology/biomass-gasifier-for-thermal-and-power-applications |
| `44d366d7-953c-41cc-aafa-3425fb604cc4` | website / page | Oilzapper and Oilivorous-S | https://teriin.org/technology/oilzapper-and-oilivorous-s |
| `d604f23f-cbaa-4c0f-9f6c-3c370f207e0c` | website / page | TERI's enhanced acidification and methanation technology | https://teriin.org/technology/teri-enhanced-acidification-and-methanation-technology |
| `687e4d39-90d3-4d85-8b6b-e9e3254aca6e` | website / page | Advanced wastewater treatment made affordable | https://teriin.org/technology/advanced-wastewater-treatment-made-affordable |
| `b2827f5a-ae1c-47b5-895b-257c1336f017` | website / page | Innovations in Climate-Smart and Sustainable Farming through Nanotechnology | https://teriin.org/technologies/innovations-in-climate-smart-and-sustainable-farming-through-nanotechnology |
| `f387a567-cf91-4683-91ae-c431a037d49b` | website / services | Next generation technology to produce high-quality mycorrhiza |  |
| `d073da23-c0f7-4bea-beaf-26766267de4e` | website / services | Enhanced oil recovery from mature oil reserves |  |
| `fc7e7a2e-8914-4ae8-b214-3246272f5333` | website / services | Technology for reclaming wastelands |  |
| `8971157f-46c4-48ff-8151-eb73ed47396d` | website / page | Production of Xanthan gum using novel Xanthomonas campestris | https://teriin.org/technology/xanthan-gum-xanthomonas-campestris-oil-well-drilling |
| `061056ba-c5c1-45f5-a450-4a1768087cfe` | website / page | Microbial Enhanced Oil Recovery (MEOR): Reviving Ageing Oil Wells Naturally | https://teriin.org/technologies/microbial-enhanced-oil-recovery-(MEOR)-reviving-ageing-oil-wells-naturally |
| `b0efce82-6055-406d-9274-8fb2befa0100` | website / page | A Microbial Revolution – Preventing Paraffin Deposition in Oil Wells | https://teriin.org/technologies/a-microbial-revolution-preventing-paraffin-deposition-in-oil-wells |
| `f2f185f9-d2ea-41ac-86dc-179f8c709ef7` | website / page | Coalbed Methane: Evolving Towards Biological Methanation for Sustainable Energy Production | https://teriin.org/technologies/coalbed-methane-evolving-towards-biological-methanation-for-sustainable-energy-production |

**Notes**: SCOPE MISMATCH the grader should note: the Technologies page is TERI's institutional technology portfolio, not a list scoped to ONGOING projects. The corpus provides no project-to-technology linkage, so an answer cannot be checked for 'under ongoing projects' specifically.

---

### Q036 - What are the expected outcomes and impacts of key TERI projects?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c519f60b-7442-4f84-99fa-d732bd36201d` | website / ongoing_projects | Accelerating Industrial Decarbonisation in India | https://teriin.org/project/accelerating-industrial-decarbonisation-india |
| `ec42a9ea-7d46-46b1-9263-a7a88aaea1c4` | website / ongoing_projects | UrjaSanchay: Energy Storage in India - Knowledge Systems | https://teriin.org/project/urjasanchay-energy-storage-india-knowledge-systems |
| `8b15b308-c364-46fb-ba6e-0f6535c1f6a1` | website / ongoing_projects | Climate Skills - Seeds for a Transition India | https://teriin.org/project/climate-skills-seeds-transition-india |

**Notes**: 'KEY PROJECTS' IS UNDEFINED. Individual ongoing-project pages do state aims and expected activities verbatim (e.g. 'Accelerating Industrial Decarbonisation in India' lists three activities and a 2024 roadmap target; Climate Skills reports 500+ youth engaged and a 130-participant Phase II), but there is no importance ranking, no structured outcome/indicator field and no completion reporting, so neither the project selection nor the outcome set can be established. A human must nominate the projects in scope.

---

### Q037 - Which states and regions are covered under TERI's current projects?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: location/city + aggregation
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `ongoing projects have NO state field; field_ongoing_country_tmp is NULL on 486/594 and country-level only`

**Notes**: NO STRUCTURED SUB-NATIONAL GEOGRAPHY ANYWHERE. Neither documents nor documents_tag nor documents_theme nor the Neo4j projection models locations; the Qdrant payload has no geography field. State names appear only inside free-text project titles and bodies (e.g. Karnataka, Uttarakhand, Andhra Pradesh, Maharashtra, Assam, Punjab, Haryana, Odisha, Manipur, Gujarat, Rajasthan, Telangana, Madhya Pradesh, West Bengal, Uttar Pradesh, Delhi, Goa, Bhutan), so a coverage answer would be an unverifiable text-mining result. Per the brief's Step 8 this is NOT marked unsupported merely because Neo4j cannot answer it - it is unsupported because no store records project geography at all.

---

### Q038 - What policy briefs or reports have emerged from TERI projects?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: relationship / aggregation
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `documents_assertion has no PRODUCED / CITES / DERIVED_FROM predicate; documents_attachment links files to their own node only`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `3a873e17-e1be-4c6f-80e9-b5453f2ce1fe` | website / ongoing_projects | Launch of report 'Practices and Solutions: Accelerating Indian Industry Decarbonisation' | https://teriin.org/project/launch-report-practices-and-solutions-accelerating-indian-industry-decarbonisation |
| `c837a254-0acb-4aa0-9acc-843d76fcf404` | website / policy_brief | Discussion Brief: Sustainable Land Futures for Utility Scale RE Expansion in States: Case Study of Rajasthan | https://teriin.org/policy-brief/discussion-brief-sustainable-land-futures-utility-scale-re-expansion-states-case-study |

**Notes**: NO PROJECT-TO-PUBLICATION LINKAGE IN THE DATA MODEL. Policy briefs (247 nodes) and reports exist as independent CMS nodes with no field pointing back to the project that produced them, and the graph has no such predicate. A few project pages announce a report launch in their own title (e.g. 'Launch of report Practices and Solutions: Accelerating Indian Industry Decarbonisation'), but that is incidental, not a derivable mapping.

---

### Q039 - How can organizations collaborate with TERI on ongoing projects?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |
| `4a4b782f-5110-4520-aec6-92209213a948` | website / page | Business & Sustainability | https://teriin.org/business-sustainability |
| `8937e1db-933e-45dc-80d3-80a0889f66cf` | website / page | Areas of Work | https://teriin.org/careers/areas-work |

**Notes**: NO COLLABORATION/PARTNERSHIP PROCESS PAGE. The corpus has no 'work with us', 'collaborate' or 'call for proposals' page. Adjacent evidence: TERI Council for Business Sustainability membership with stated benefits and member services (b48f22b0, 4a4b782f), the Areas of Work page's 'consultancy & advisory' and 'strategy development for corporates' lines (8937e1db), and the general contact mailbox@teri.res.in (2a2e9a77). Whether that constitutes the gold answer to 'collaborate on ongoing projects' is a judgement call for a human; see Q121 which is answerable at organisation level.

---

### Q040 - What is green hydrogen and how is TERI working in this field?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual + narrative
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Green hydrogen is hydrogen produced using renewable electricity; TERI positions it as a critical new-age technological solution for net-zero and energy security and treats it as one of its prime areas of work. TERI's documented work: the policy brief 'Green Hydrogen - Path to Decarbonization' (Nov 2024), which called for pilot-project subsidies and SPVs; 'Strategy for Downstream Use of Green Hydrogen' (Dec 2024, Energetica India); the primer 'A primer on green hydrogen'; the research paper 'Hydrogen Rotary Kilns for Ironmaking in India' (Nov 2025); the policy brief 'Harnessing the Potential of Bio-Resources to Produce Low Carbon Bio-Hydrogen'; commentary that green hydrogen is the missing link in India's net-zero transition and that $1/kg green hydrogen is achievable in India; and engagement with the National Green Hydrogen Mission.

**Expected facts**

- TERI names green hydrogen (with biofuels) as a critical new-age technological solution for India's net-zero goals and energy security, and one of its prime areas of work.
- TERI published the policy brief 'Green Hydrogen - Path to Decarbonization' in November 2024, calling for pilot-project subsidies and special purpose vehicles.
- TERI published 'Strategy for Downstream Use of Green Hydrogen' (Energetica India, Nov-Dec 2024).
- TERI published the research paper 'Hydrogen Rotary Kilns for Ironmaking in India' (November 2025).
- TERI published the policy brief 'Harnessing the Potential of Bio-Resources to Produce Low Carbon Bio-Hydrogen'.
- TERI's Director General Dr Vibha Dhawan has stated that a green hydrogen cost of $1 per kg is possible in India.
- TERI's site carries explainer content on green hydrogen, including 'A primer on green hydrogen' (document 42a753ed) and a video explainer on the National Green Hydrogen Mission; note the primer sits in the third-party-heavy `news` bundle, so its TERI authorship is not established by the corpus.

**Expected entities**: green hydrogen, National Green Hydrogen Mission, Green Hydrogen - Path to Decarbonization

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2f610ad2-6aca-4560-8c71-f42d42584435` | website / policy_brief | Green Hydrogen - Path to Decarbonization | https://teriin.org/policy-brief/green-hydrogen-path-decarbonization |
| `cba1731e-0f77-45c4-a624-2e300710368e` | website / news | India’s push for green hydrogen: TERI policy brief calls for pilot projects subsidies, and SPVs | https://teriin.org/news/indias-push-green-hydrogen-teri-policy-brief-calls-pilot-projects-subsidies-and-spvs |
| `84a07d3b-01a8-4668-b1af-0d4a87f9c082` | website / feature_articles | Strategy for Downstream Use of Green Hydrogen | https://teriin.org/opinion/strategy-downstream-use-green-hydrogen |
| `7eb6eaa8-31f3-4db6-98bb-e5a0fc12e972` | website / research_papers | Hydrogen Rotary Kilns for Ironmaking in India | https://teriin.org/research-paper/hydrogen-rotary-kilns-ironmaking-india |
| `b827a559-ba07-49a6-b97e-eff2455751f3` | website / feature_articles | Green hydrogen is the missing link in India’s net-zero transition | https://teriin.org/opinion/green-hydrogen-missing-link-indias-net-zero-transition |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |
| `4b069eb5-094e-4a3b-a7bc-d50f284c3c38` | website / policy_brief | Harnessing the Potential of Bio-Resources to Produce Low Carbon Bio-Hydrogen | https://teriin.org/policy-brief/harnessing-potential-bio-resources-produce-low-carbon-bio-hydrogen |
| `42a753ed-1b7f-46ad-bbb0-3363b572386a` | website / news | A primer on green hydrogen | https://teriin.org/news/primer-green-hydrogen |

**Notes**: The definitional half ('what is green hydrogen') is only weakly supported: the corpus has a primer page and many contextual mentions but no crisp TERI definition sentence. Do not treat a textbook definition as corpus-grounded. Several hydrogen items in the corpus are third-party news coverage of Union Minister Nitin Gadkari's statements, not TERI research - an answer must not attribute those to TERI. JUDGEMENT CORRECTIONS: two facts had no supporting citation - the bio-hydrogen policy brief (now cited as 4b069eb5-094e-4a3b-a7bc-d50f284c3c38) and 'A primer on green hydrogen' (now cited as 42a753ed-1b7f-46ad-bbb0-3363b572386a). The primer is filed in the `news` bundle, so the fact was reworded to stop asserting TERI authorship of it.

---

### Q041 - What research is TERI conducting on battery energy storage systems?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's battery-energy-storage research runs through the Indo-German technical cooperation project 'Energy Storage for Renewable Energy Integration in India' (StoREin), commissioned by Germany's BMUKN under the International Climate Initiative and jointly implemented by MNRE and GIZ, with Fraunhofer IEE, IIT Bombay and TERI as implementing partners. Its public output is UrjaSanchay (urjasanchay.in), a knowledge platform combining the Urja Sangraha interactive data dashboard with a dialogue platform and structured learning modules. Other documented work: the policy brief 'Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward' (Aug 2026); the GIZ-TERI-GUVNL collaboration to accelerate renewable-energy integration through energy storage (Aug 2025); a Capacity Building Program on BESS (2026); a rare BESS tender awarded to BHEL under a TERI consortium project (2020); and a national dialogue on strengthening India's renewable energy and storage ecosystem (Nov 2025).

**Expected facts**

- UrjaSanchay (urjasanchay.in) is TERI's energy-storage knowledge platform, integrating the Urja Sangraha interactive data dashboard and a dialogue platform, plus structured learning modules.
- UrjaSanchay was developed under the Indo-German technical cooperation project 'Energy Storage for Renewable Energy Integration in India' (StoREin).
- StoREin was commissioned by Germany's Federal Ministry for the Environment, Climate Action, Nature Conservation and Nuclear Safety (BMUKN) under the International Climate Initiative (IKI) and is jointly implemented by MNRE and GIZ; implementing partners include Fraunhofer IEE, IIT Bombay and TERI.
- TERI published the policy brief 'Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward' (August 2026).
- GIZ, TERI and GUVNL joined hands to accelerate renewable-energy integration through energy-storage solutions (August 2025).
- TERI ran a Capacity Building Program on Battery Energy Storage Systems (BESS).
- BHEL was awarded a battery-energy-storage-system tender under a TERI consortium project (2020).

**Expected entities**: UrjaSanchay, StoREin, GIZ, MNRE, BMUKN, Fraunhofer IEE, IIT Bombay, GUVNL, BHEL

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `ec42a9ea-7d46-46b1-9263-a7a88aaea1c4` | website / ongoing_projects | UrjaSanchay: Energy Storage in India - Knowledge Systems | https://teriin.org/project/urjasanchay-energy-storage-india-knowledge-systems |
| `7b4ca9d9-ae6c-4073-a586-fa74918a983b` | website / policy_brief | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward | https://teriin.org/policy-brief/battery-assembly-and-container-testing-safety-global-best-practices-and-way-forward |
| `94c10806-3c26-4050-bf7d-e18efa8e1406` | website / press_release | GIZ, TERI, and GUVNL Join Hands to Accelerate RE Integration through Energy Storage Solutions | https://teriin.org/press-release/giz-teri-and-guvnl-join-hands-accelerate-re-integration-through-energy-storage |
| `1cfce10c-1bfc-4b08-8ccf-ae8f7469b184` | website / news | GIZ, TERI, and GUVNL Join Hands to Accelerate Renewable Energy Integration Through Energy Storage Solutions | https://teriin.org/news/giz-teri-and-guvnl-join-hands-accelerate-renewable-energy-integration-through-energy-storage |
| `a31917b0-9e32-4485-869e-47f3b23b57a6` | website / events | Capacity Building Program on BESS | https://teriin.org/event/capacity-building-program-bess |
| `caa012a7-371b-4b4a-af34-1fa483b7baa3` | website / press_release | BHEL to be awarded rare tender for battery energy storage system under TERI consortium project | https://teriin.org/press-release/bhel-be-awarded-rare-tender-battery-energy-storage-system-under-teri-consortium |
| `c665fe38-2806-4a74-a0f1-2f5dd95c5f26` | website / press_release | TERI Leads National Dialogue on Strengthening India’s Renewable Energy and Storage Ecosystem | https://teriin.org/press-release/teri-leads-national-dialogue-strengthening-indias-renewable-energy-and-storage |
| `77c2cb37-2a69-4f48-87b1-d274f033dae8` | website / videos | Battery Energy Storage Systems: Enable Smooth Transition of India's Power Sector | https://teriin.org/video/battery-energy-storage-systems-enable-smooth-transition-indias-power-sector |

**Notes**: Many battery items in the corpus are third-party news about Indian government policy (PM Surya Ghar 2.0, localisation mandates, NITI Aayog) - not TERI research. Attribution must be checked.

---

### Q042 - How is TERI supporting India's energy transition?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports India's energy transition through dedicated institutions, analysis and convening: the TERI Institute of Energy Transition (Gachibowli, Hyderabad); the Centre of Excellence on Energy Transition (CoEET); the Energy Transition Hub for Eastern and North-Eastern States (ETHENS); the Electricity Transition and Industry Transition workstreams; a Just Transition programme; the 'Rising Ambition: Carving New Pathways - India's Energy Transition' report; MoUs with state utilities and agencies (Rajasthan Renewable Energy Corporation, BSES Rajdhani and BSES Yamuna, REMCL, POSOCO); and analysis such as 'Solar With Storage Is Cheaper Than New Thermal'. TERI states its energy work is founded on Industrial Energy Efficiency, Renewable Energy Technologies, Electricity and Fuels, and Energy Assessment & Modelling, with green hydrogen and biofuels as prime areas.

**Expected facts**

- TERI operates a TERI Institute of Energy Transition based at Gachibowli, Hyderabad.
- TERI hosts a Centre of Excellence on Energy Transition (CoEET).
- TERI is establishing an Energy Transition Hub for Eastern and North-Eastern States (ETHENS).
- TERI's energy work is founded on Industrial Energy Efficiency, Renewable Energy Technologies, Electricity and Fuels, and Energy Assessment & Modelling.
- TERI maintains Electricity Transition and Industry Transition workstreams and a Just Transition programme.
- TERI launched 'Rising Ambition: Carving New Pathways - India's Energy Transition'.
- TERI signed an MoU with Rajasthan Renewable Energy Corporation Limited to advance Rajasthan's clean-energy transition (May 2026) and MoUs with BSES Rajdhani and BSES Yamuna on renewable energy and smart distribution (March 2025).

**Expected entities**: TERI Institute of Energy Transition, CoEET, ETHENS, Just Transition, Rising Ambition, Rajasthan Renewable Energy Corporation Limited, BSES Rajdhani, BSES Yamuna

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `32f51389-6111-47cd-a984-a6822525c075` | website / page | TERI Institute of Energy Transition | https://teriin.org/TERI-institute-of-energy-transition |
| `f029ec29-1dd2-4feb-bdc2-26bf95849774` | website / page | Centre of Excellence on Energy Transition (CoEET) | https://teriin.org/centre-of-excellence-for-energy-transition |
| `1f4374aa-9dc1-4ae7-af8e-9b17be18f495` | website / page | Electricity Transition | https://teriin.org/energy-transitions/electricity-transition |
| `a11b7895-1369-4789-acbb-af9060fbfe39` | website / page | Industry Transition | https://teriin.org/energy-transitions/industry-transition |
| `720ee5ef-5080-4698-9a6c-d7b0738a36ce` | website / page | Just Transition | https://teriin.org/just-transition-page |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |
| `4efc51a5-a800-4b9e-a758-9eea8cea62ac` | website / events | Establishment of Energy Transition Hub for Eastern and North – Eastern States (ETHENS) | https://teriin.org/event/establishment-energy-transition-hub-eastern-and-north-eastern-states-ethens |
| `ccc8273a-aeb1-4e51-a0e3-3513d787e82b` | website / press_release | TERI Leads Push for Regional Energy Transition Hub in Eastern & North-East India | https://teriin.org/press-release/teri-leads-push-regional-energy-transition-hub-eastern-north-east-india |
| `c555b305-da7c-4747-bc8e-9f302f130c1f` | website / press_release | ‘Rising Ambition’ Launched: TERI Unveils New Vision for India’s Energy Future | https://teriin.org/press-release/rising-ambition-launched-teri-unveils-new-vision-indias-energy-future |
| `2ab73442-453e-46b5-a893-0beeb57157c9` | website / press_release | Rajasthan Renewable Energy Corporation Limited and TERI Sign MoU to Advance Rajasthan’s Clean Energy Transitio | https://teriin.org/press-release/rajasthan-renewable-energy-corporation-limited-and-teri-sign-mou-advance-rajasthans |
| `9d9d7376-09f0-4165-8ad0-1651588b0363` | website / press_release | TERI and BSES Rajdhani & BSES Yamuna Sign MoUs to Advance Renewable Energy and Smart Distribution Initiatives | https://teriin.org/press-release/teri-and-bses-rajdhani-bses-yamuna-sign-mous-advance-renewable-energy-and-smart |

---

### Q043 - What is TERI's work on solar energy technologies?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's solar work spans resource assessment, economics, manufacturing, land use and applications. Documented outputs: 'Reassessing India's Solar Potential', which pegged total estimated capacity at 10,830 GW (June 2025); 'Solar With Storage Is Cheaper Than New Thermal' (Oct 2025); the policy brief 'Solar Thermal Energy for Industrial Decarbonization' (Aug 2026) and a call to accelerate solar thermal adoption in industry; work on Concentrated Solar Power and Thermal Energy Storage; a report on India's PV manufacturing (Bharat Climate Forum 2026); agrivoltaics/AgriPV work including 'Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints', responsible AgriPV baseline assessments at the Renkube (Telangana) and Khare Energy (Madhya Pradesh) plants and an AgriPV DPR framework; land-tenure research on utility-scale solar in Rajasthan and 'Sustainable Land Futures for Utility-Scale RE Expansion'; a national stakeholder consultation on Building-Integrated Photovoltaics with the GRIHA Council; and solar applications projects (grid-tied solar PV for a water treatment plant, terracotta cluster solarisation in Gorakhpur, smart solar-powered irrigation in Karnataka).

**Expected facts**

- TERI's report 'Reassessing India's Solar Potential' pegged India's total estimated solar capacity at 10,830 GW (June 2025).
- TERI's analysis 'Solar With Storage Is Cheaper Than New Thermal' concluded solar with storage is cheaper than new thermal power for meeting demand (October 2025).
- TERI published 'Solar Thermal Energy for Industrial Decarbonization' and called for accelerated adoption of solar thermal technologies to decarbonise Indian industry (2026).
- TERI has examined pathways for scaling Concentrated Solar Power (CSP) and Thermal Energy Storage (TES).
- TERI released a report on India's PV manufacturing at the Bharat Climate Forum 2026.
- TERI works on agrivoltaics/AgriPV, including 'Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints in India's Energy Transition', responsible AgriPV baseline assessments at the Renkube plant (Telangana) and Khare Energy plant (Madhya Pradesh), and a framework for AgriPV DPR development.
- TERI researched tenure dynamics in land procurement for Rajasthan's utility-scale solar energy transition and released a report and discussion brief on Sustainable Land Futures for Utility-Scale RE expansion.
- TERI and the GRIHA Council convened a national stakeholder consultation to accelerate Building-Integrated Photovoltaics (BIPV) in India.

**Expected entities**: Reassessing India's Solar Potential, 10,830 GW, Concentrated Solar Power, AgriPV, BIPV, GRIHA Council

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c8c1a5df-d686-44cf-a350-6eeea55971db` | website / press_release | TERI Unveils a Report on Reassessing India’s Solar Potential: Total Estimated Capacity Pegged at 10,830 GW | https://teriin.org/press-release/teri-unveils-report-reassessing-indias-solar-potential-total-estimated-capacity |
| `a1ca094a-591b-40d5-928f-fbe5c105c119` | website / policy_brief | Solar With Storage Is Cheaper Than New Thermal | https://teriin.org/policy-brief/solar-storage-cheaper-new-thermal |
| `80afaa3e-da51-4304-b78d-da781fe936c0` | website / press_release | Solar With Storage Cheaper Than New Thermal Power: TERI’s Analysis for Meeting the Demand of a DISCOM | https://teriin.org/press-release/solar-storage-cheaper-new-thermal-power-teris-analysis-meeting-demand-discom |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `a1156006-18d9-44ec-abe9-2384f493e99f` | website / press_release | TERI Calls for Accelerated Adoption of Solar Thermal Technologies to Decarbonize India’s Industrial Sector | https://teriin.org/press-release/teri-calls-accelerated-adoption-solar-thermal-technologies-decarbonize-indias |
| `774c02a4-8342-4159-836d-a1c9fc7db3ba` | website / press_release | TERI Discusses Pathways for Scaling Concentrated Solar Power (CSP) and Thermal Energy Storage (TES) in India | https://teriin.org/press-release/teri-discusses-pathways-scaling-concentrated-solar-power-csp-and-thermal-energy |
| `9d69e02c-ce92-44af-85d2-3e04514a53e7` | website / press_release | TERI Report on India’s PV Manufacturing Released at Bharat Climate Forum 2026 | https://teriin.org/press-release/teri-report-indias-pv-manufacturing-released-bharat-climate-forum-2026 |
| `bf0abbc6-3a78-4005-8b5f-ae74a92ffb77` | website / policy_brief | Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints in India’s Energy Transition | https://teriin.org/policy-brief/unlocking-solar-scale-how-agrivoltaics-overcome-land-constraints-indias-energy |
| `97a6f920-779e-4f8b-86cd-ece45c7cac15` | website / policy_brief | RESPONSIBLE AGRI PV: BASELINE ASSESSMENT REPORT Renkube Plant, Telangana | https://teriin.org/policy-brief/responsible-agri-pv-baseline-assessment-report-renkube-plant-telangana |
| `eddaeeb7-1435-4b52-b346-d2b56c40e06d` | website / policy_brief | RESPONSIBLE AGRI PV BASELINE ASSESSMENT REPORT Khare Energy Plant, Madhya Pradesh | https://teriin.org/policy-brief/responsible-agri-pv-baseline-assessment-report-khare-energy-plant-madhya-pradesh |
| `39360ecc-576c-4b80-8e91-97dc7ac4dbaa` | website / policy_brief | FRAMEWORK FOR AGRIPV DPR DEVELOPMENT | https://teriin.org/policy-brief/framework-agripv-dpr-development |
| `8a92ed23-54ed-466e-ae97-de06bb0d5293` | website / policy_brief | Tenure Dynamics in Land Procurement in Rajasthan’s Utility-Scale Solar Energy Transition | https://teriin.org/policy-brief/tenure-dynamics-land-procurement-rajasthans-utility-scale-solar-energy-transition |
| `7458e3cc-a458-4385-95d0-63c60549f685` | website / press_release | TERI Releases Landmark Report and Discussion Brief on Sustainable Land Futures for Utility-Scale Solar Expansi | https://teriin.org/press-release/teri-releases-landmark-report-and-discussion-brief-sustainable-land-futures-utility |
| `5863058a-cfd4-4c1a-9a68-86a9e6f17606` | website / press_release | TERI–GRIHA Council Convene National Stakeholder Consultation to Accelerate Building-Integrated Solar in India | https://teriin.org/press-release/teri-griha-council-convene-national-stakeholder-consultation-accelerate-building |
| `10e1b10b-37f2-4dbd-83f6-8c50d6b0513d` | website / completed_projects | Solar PV Power system Grid -Tied for Water Treatment Plant at GWI | https://teriin.org/project/solar-pv-power-system-grid-tied-water-treatment-plant-gwi |
| `e22fe02b-8c8b-401e-9cf9-37ffffe7e425` | website / completed_projects | Empowering the Terracotta Clusters with Solar Power in Gorakhpur | https://teriin.org/project/empowering-terracotta-clusters-solar-power-gorakhpur |
| `b8fc9a99-908d-45cc-a3b3-4809e605b15f` | website / completed_projects | Smart Solar-Powered Irrigation and Pesticide Management for Sustainable Agriculture in Karnataka, India | https://teriin.org/project/smart-solar-powered-irrigation-and-pesticide-management-sustainable-agriculture-karnataka |

---

### Q044 - What is TERI's work on bioenergy and biofuels?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's bioenergy and biofuels work is anchored in the DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities and the Tata Chemicals Ltd.-TERI Centre of Excellence for Biochemicals, supported by biomass-gasifier technology for heat and power. Documented lines: biodiesel - 'Accelerating Biodiesel Blending in India' policy brief and 'Impact of Biodiesel Blending on Indian Oil Market by 2030'; ethanol/2G - process development of 2G ethanol under the Indo-UK Agri-Jet collaboration, algal bioethanol pathways under the Gujarat Biotech Mission, marine algal bioethanol, rice-straw second-generation biorefineries; oxyfuels - 'Enhancing India's Biofuels Program: Examining the Role of Oxyfuels'; aviation and maritime - the EU-India roadmap and workshop on sustainable biofuels for aviation and maritime transport and a comprehensive LCA of sugarcane-based SAF; algal biofuels - photobioreactor design and harvest technology, microalgal species work; and biomass potential assessment for biofuel plants in North-East India.

**Expected facts**

- TERI hosts the DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities.
- TERI hosts the Tata Chemicals Ltd.-TERI Centre of Excellence for Biochemicals.
- TERI biomass gasifiers (patented throat-less downdraft design, multi-fuel) are customisable for heat and power generation in rural, commercial and industrial applications.
- TERI published the policy brief 'Accelerating Biodiesel Blending in India' and research on the impact of biodiesel blending on the Indian oil market by 2030.
- TERI published 'Enhancing India's Biofuels Program: Examining the Role of Oxyfuels in India's Clean Fuel Transition'.
- TERI worked on an EU-India roadmap for cooperation on biofuels from biomass for aviation and maritime transport.
- TERI conducts a comprehensive Life Cycle Assessment of sugar-based Sustainable Aviation Fuel for India.
- TERI works on second-generation (2G) ethanol, including process development under the Indo-UK Agri-Jet collaboration, and on algal and marine-algal bioethanol pathways.
- TERI assessed biomass potential for biofuel plants in North-East India.

**Expected entities**: DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities, Tata Chemicals Ltd.-TERI Centre of Excellence for Biochemicals, TERI biomass gasifier, Sustainable Aviation Fuel, Indo-UK Agri-Jet

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `5b31ce53-5820-40a2-ba7c-be29e262f6c6` | website / page | DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities | https://teriin.org/dbt-teri-centre-excellence-advanced-biofuels-and-bio-commodities |
| `965602d0-7247-40dd-89d4-f9bef3d38d11` | website / ongoing_projects | DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities | https://teriin.org/project/dbt-teri-centre-excellence-advanced-biofuels-and-bio-commodities |
| `9bbe64eb-6157-4706-be29-1c5bd45eb40d` | website / page | Tata Chemicals Ltd.-TERI Centre of Excellence for Biochemicals | https://teriin.org/tata-chemicals-ltd-TERI-centre-of-excellence-for-biochemicals |
| `f17bd41c-cbfb-4935-87fc-6d207cff88e8` | website / page | Biomass Gasifier for Thermal and Power applications | https://teriin.org/technology/biomass-gasifier-for-thermal-and-power-applications |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `efdfdcef-734f-4cec-a60b-4346c4685fca` | website / policy_brief | Accelerating Biodiesel Blending in India | https://teriin.org/policy-brief/accelerating-biodiesel-blending-india-0 |
| `43f8d80f-f3d3-445c-a942-e1efbd79acbe` | website / research_papers | Impact of Biodiesel Blending on Indian Oil Market by 2030 | https://teriin.org/research-paper/impact-biodiesel-blending-indian-oil-market-2030 |
| `1f762670-2786-4bca-8ac3-51bd8e7b0b1f` | website / policy_brief | Enhancing India’s Biofuels Program: Examining the Role of Oxyfuels in India’s Clean Fuel Transition | https://teriin.org/policy-brief/enhancing-indias-biofuels-program-examining-role-oxyfuels-indias-clean-fuel-transition |
| `0cb25163-3e12-40c5-9c41-dcaf7a2ad1c7` | website / press_release | EU-India Biofuel Workshop on Sustainable Biofuels for Aviation and Maritime Transport | https://teriin.org/press-release/eu-india-biofuel-workshop-sustainable-biofuels-aviation-and-maritime-transport |
| `3395dd39-aa53-4704-a3fe-6fa9b4c571cb` | website / events | EU-India Roadmap for Cooperation On Biofuels from Biomass for Aviation and Maritime Transport | https://teriin.org/event/eu-india-roadmap-cooperation-biofuels-biomass-aviation-and-maritime-transport |
| `d626df61-45a0-4551-a47e-cc5f054615b9` | website / ongoing_projects | Comprehensive Life Cycle Assessment of Sugar-based Sustainable Aviation Fuel for India | https://teriin.org/project/comprehensive-life-cycle-assessment-sugar-based-sustainable-aviation-fuel-india |
| `2aba6136-73bd-4b3c-94df-3442d29acccd` | website / completed_projects | Process Development of 2G Ethanol under the Indo-UK Agri-Jet Collaboration | https://teriin.org/project/process-development-2g-ethanol-under-indo-uk-agri-jet-collaboration |
| `053e0c28-dcdf-4600-bf5b-8a34c9142383` | website / completed_projects | Exploring Algal-based bioethanol pathways under Gujarat Biotech Mission | https://teriin.org/project/exploring-algal-based-bioethanol-pathways-under-gujarat-biotech-mission |
| `f00b1bf8-8c22-4745-92a0-766ec524f0b3` | website / completed_projects | Marine Algal bioethanol research under DBT-RA individual fellowship | https://teriin.org/project/marine-algal-bioethanol-research-under-dbt-ra-individual-fellowship |
| `42df38d9-af30-405f-ad45-908635b0d12f` | website / completed_projects | Biomass Potential Assessment for Biofuel Plants in North-East India | https://teriin.org/project/biomass-potential-assessment-biofuel-plants-north-east-india |
| `c8d33109-f07d-4dc3-8378-67123877be75` | website / completed_projects | Photobioreactor Design and Harvest Technology for Algal Biofuels | https://teriin.org/project/photobioreactor-design-and-harvest-technology-algal-biofuels |

---

### Q045 - What research is being conducted on energy storage technologies?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's energy-storage research covers electrochemical and thermal storage. Battery/electrochemical: the StoREin Indo-German project and the UrjaSanchay knowledge platform and data dashboard; the policy brief 'Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward' (2026); the GIZ-TERI-GUVNL work on renewable-energy integration through storage; a Capacity Building Program on BESS. Thermal: pathways for Concentrated Solar Power with Thermal Energy Storage; a solar-biomass hybrid dryer with thermal energy storage. Systems/economics: 'Solar With Storage Is Cheaper Than New Thermal'; a joint Ember-TERI analysis of battery-storage cost trajectories and coal capacity (body text: 7% annual BESS cost decline, coal plateauing to 2032); and commentary on pumped-storage plants as a way ahead for India.

**Expected facts**

- TERI's energy-storage work includes the Indo-German StoREin project and the UrjaSanchay platform with an interactive storage data dashboard.
- TERI published 'Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward' (2026).
- GIZ, TERI and GUVNL work together on renewable-energy integration through energy-storage solutions.
- TERI researches thermal energy storage, including pathways for scaling Concentrated Solar Power with Thermal Energy Storage and a solar-biomass hybrid dryer with thermal energy storage.
- TERI's analysis concluded solar with storage is cheaper than new thermal power.
- A joint Ember-TERI report addressed battery-storage costs and coal capacity: the source text states that if BESS costs keep declining at the current rate of 7% annually, India's coal generation will plateau until 2032 while additional coal capacity may still be needed for non-solar hours. The '15%' figure appears only in a third-party news headline, not in the ingested body text, and the report is Ember-TERI, not TERI alone.

**Expected entities**: StoREin, UrjaSanchay, BESS, Concentrated Solar Power with Thermal Energy Storage

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `ec42a9ea-7d46-46b1-9263-a7a88aaea1c4` | website / ongoing_projects | UrjaSanchay: Energy Storage in India - Knowledge Systems | https://teriin.org/project/urjasanchay-energy-storage-india-knowledge-systems |
| `7b4ca9d9-ae6c-4073-a586-fa74918a983b` | website / policy_brief | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward | https://teriin.org/policy-brief/battery-assembly-and-container-testing-safety-global-best-practices-and-way-forward |
| `94c10806-3c26-4050-bf7d-e18efa8e1406` | website / press_release | GIZ, TERI, and GUVNL Join Hands to Accelerate RE Integration through Energy Storage Solutions | https://teriin.org/press-release/giz-teri-and-guvnl-join-hands-accelerate-re-integration-through-energy-storage |
| `774c02a4-8342-4159-836d-a1c9fc7db3ba` | website / press_release | TERI Discusses Pathways for Scaling Concentrated Solar Power (CSP) and Thermal Energy Storage (TES) in India | https://teriin.org/press-release/teri-discusses-pathways-scaling-concentrated-solar-power-csp-and-thermal-energy |
| `59fd6657-9e0f-4862-975a-5ce566ef787f` | website / ongoing_projects | Solar-biomass hybrid dryer with thermal energy storage | https://teriin.org/project/solar-biomass-hybrid-dryer-thermal-energy-storage |
| `a1ca094a-591b-40d5-928f-fbe5c105c119` | website / policy_brief | Solar With Storage Is Cheaper Than New Thermal | https://teriin.org/policy-brief/solar-storage-cheaper-new-thermal |
| `9858e812-9ecf-4358-a313-98e5bff9faf2` | website / news | Battery-storage costs must drop 15% to avoid new coal capacity: Report | https://teriin.org/news/battery-storage-costs-must-drop-15-avoid-new-coal-capacity-report |
| `8bc51d05-d34c-4436-869d-4e564f6456ba` | website / feature_articles | Pump Storage Plants: The way ahead for Energy Storage in India | https://teriin.org/opinion/pump-storage-plants-way-ahead-energy-storage-india |

**Notes**: Near-duplicate of Q041 (which is battery-specific). Q045 is broader; keep consistent. JUDGEMENT CORRECTION - ATTRIBUTION: the only source for the battery-cost fact is a third-party news node (9858e812) whose body attributes the report to 'global energy think tank Ember and the Delhi-based The Energy and Resources Institute (TERI)'. The original fact credited TERI alone and quoted a 15% figure that appears only in the news headline, not in the ingested text. Corrected to joint attribution and to the figures actually present in the source.

---

### Q046 - What innovations is TERI developing for energy access?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's energy-access innovations centre on the Lighting a Billion Lives (LaBL) initiative - solar lighting and charging-station models, now described as LaBL 2.0 accelerating India's SDG 7 journey - together with product and business-model innovation: the smokeless clean-combustion cookstove (2 kWth, 15-20% more effective than conventional stoves, distributed for community cooking under TERI's social-transformation programme); biomass gasifiers for rural heat and power; IDES technology deployed in flood-affected areas; a micro-energy-enterprise approach to energy access; the SMILE model for sustainable energy in micro-enterprises; women-entrepreneur delivery models in Bihar and Rajasthan; and the policy-level 'Feasibility Study of Energy Access for Enterprise Promotion' (2026). TERI's CSR service replaces kerosene lanterns with solar lighting devices.

**Expected facts**

- Lighting a Billion Lives (LaBL) is TERI's flagship energy-access initiative, including solar lantern charging stations; LaBL 2.0 is positioned as accelerating India's SDG 7 journey.
- TERI's clean combustion cookstove reduces emissions, is 15-20% more effective than conventional stoves, has 2 kWth thermal capacity, and has been distributed for community cooking in villages under TERI's social transformation programme.
- TERI promotes a micro-energy-enterprise approach for energy access.
- TERI's SMILE project promotes sustainable energy in micro-enterprises for income and livelihood enhancement.
- TERI has built women-entrepreneur delivery models for energy access, including the Bihar Clean Cookstove Program and women-led decentralised renewable energy enterprises in Rajasthan.
- TERI published a 'Feasibility Study of Energy Access for Enterprise Promotion' (2026).

**Expected entities**: Lighting a Billion Lives, LaBL 2.0, clean combustion cookstove, SMILE, micro-energy enterprise

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `5ce4fb40-32f9-4dbe-a1bb-aeeb0b1f87c5` | website / completed_projects | Lighting a Billion Lives | https://teriin.org/project/lighting-billion-lives |
| `bfb8dbeb-afc2-4da7-8677-a9ddeffca937` | website / article | Lighting the Last Mile: How TERI’s LaBL 2.0 Can Accelerate India’s SDG 7 Journey | https://teriin.org/article/lighting-last-mile-how-teris-labl-20-can-accelerate-indias-sdg-7-journey |
| `85458d64-9516-4c53-b5ca-7d8b64ddb828` | website / article | Hope amidst floods and challenges – A story on IDES technology "Lighting a Billion Lives Program" of TERI from | https://teriin.org/article/hope-amidst-floods-and-challenges-story-ides-technology-lighting-billion-lives-program-teri |
| `52ed23ab-a543-48ec-a211-c8e6c42fe89b` | website / infographics | Micro-Energy Enterprise Approach for Energy Access | https://teriin.org/infographics/micro-energy-enterprise-approach-energy-access |
| `96db4aa7-af23-4a1c-a4ba-6a81c6d965b8` | website / ongoing_projects | Sustainable energy in Micro-enterprises for Income and Livelihood Enhancement (SMILE) | https://teriin.org/project/sustainable-energy-micro-enterprises-income-and-livelihood-enhancement-smile |
| `dd64ff29-b63a-43fd-84aa-d6e11378b53a` | website / ongoing_projects | Enhancing Energy Access through Women Entrepreneurs in Bihar - Clean Cookstove Program | https://teriin.org/project/enhancing-energy-access-through-women-entrepreneurs-bihar-clean-cookstove-program |
| `f3e894b7-b3c2-41e5-b4be-f4df5ca05e5d` | website / completed_projects | Empowering Women-Led Enterprises in Rajasthan through Decentralized Renewable Energy | https://teriin.org/project/empowering-women-led-enterprises-rajasthan-through-decentralized-renewable-energy |
| `8d90ecfc-2213-4c62-929b-b0c45dfd7683` | website / policy_brief | Feasibility Study of Energy Access for Enterprise Promotion | https://teriin.org/policy-brief/feasibility-study-energy-access-enterprise-promotion |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `769f4073-d894-496a-8386-322f8deadf91` | website / services | CSR engagements to provide clean energy solutions |  |
| `2b154e6e-06d4-45a1-8355-d488a0b376a9` | website / infographics | Lighting a Billion Lives: Evolution | https://teriin.org/infographics/lighting-billion-lives-evolution |

---

### Q047 - What research is TERI undertaking on carbon capture, utilization and storage?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `e9d11daa-fdc6-45bd-925d-366084e1ff0a` | website / completed_projects | Support for Research and Review of Preliminary Results for carbon capture and storage - Global Components, Ind | https://teriin.org/project/support-research-and-review-preliminary-results-carbon-capture-and-storage-global |
| `5056e6bd-3994-44bc-855b-b281f0bea228` | website / feature_articles | From budget provision to national capability: Why India’s CCUS commitment matters | https://teriin.org/opinion/budget-provision-national-capability-why-indias-ccus-commitment-matters |
| `f4db8508-91de-4e4e-abc3-969e0b0f9fd0` | website / research_papers | Role of woody biomass in carbon capture, circular bioeconomy, and biomanufacturing | https://teriin.org/research-paper/role-woody-biomass-carbon-capture-circular-bioeconomy-and-biomanufacturing |
| `2a310697-5393-4e1f-bd72-f22179e32011` | website / policy_brief | Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070 | https://teriin.org/policy-brief/decarbonization-roadmap-indian-cement-sector-net-zero-co2-2070 |

**Notes**: PRESENT-TENSE CLAIM NOT SUPPORTABLE. The question asks what TERI is UNDERTAKING on CCUS. The corpus contains: one COMPLETED project, 'Support for Research and Review of Preliminary Results for carbon capture and storage - Global CCS Institute' (published 2017); a 2026 opinion piece 'From budget provision to national capability: Why India's CCUS commitment matters'; a research paper on the role of woody biomass in carbon capture, circular bioeconomy and biomanufacturing (2023); and CCUS treated as one option inside the cement decarbonisation roadmap and net-zero event reports. There is NO ongoing CCUS project node and no CCUS programme, centre or service. A human must decide whether the commentary and cement-roadmap treatment constitute 'research TERI is undertaking'.

---

### Q048 - What is TERI's contribution to industrial decarbonization?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's contribution to industrial decarbonization: it runs the 'Accelerating Industrial Decarbonisation in India' programme (evidence base and roadmap for iron & steel, cement and related MSMEs, through policy, low-carbon technologies, finance and corporate commitment); produced the GCCA India-TERI 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070'; published 'Practices and Solutions: Accelerating Indian Industry Decarbonisation' and the policy brief 'Solar Thermal Energy for Industrial Decarbonization'; analysed the potential for electrifying Indian MSMEs and green market instruments for steel; and convenes the Industry Charter for Near Zero Emission Ambition by 2050 plus a Chief Sustainability Officers' Forum, through which industry leaders commit to near-zero operations.

**Expected facts**

- TERI runs 'Accelerating Industrial Decarbonisation in India', covering iron & steel, cement and related MSMEs.
- TERI and GCCA India produced the 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070'.
- TERI published the report 'Practices and Solutions: Accelerating Indian Industry Decarbonisation'.
- TERI published the policy brief 'Solar Thermal Energy for Industrial Decarbonization' and called for accelerated solar-thermal adoption in Indian industry.
- TERI analysed the potential for electrifying Indian MSMEs, noting Indian industry consumes around 50% of total energy demand and about two-thirds of industrial energy consumption is for direct heat.
- TERI convenes the Industry Charter for Near Zero Emission Ambition by 2050 and a Chief Sustainability Officers' Forum for industry commitment.

**Expected entities**: Accelerating Industrial Decarbonisation in India, GCCA India, Industry Charter for Near Zero Emission Ambition by 2050, Chief Sustainability Officers' Forum

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c519f60b-7442-4f84-99fa-d732bd36201d` | website / ongoing_projects | Accelerating Industrial Decarbonisation in India | https://teriin.org/project/accelerating-industrial-decarbonisation-india |
| `2a310697-5393-4e1f-bd72-f22179e32011` | website / policy_brief | Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070 | https://teriin.org/policy-brief/decarbonization-roadmap-indian-cement-sector-net-zero-co2-2070 |
| `3a873e17-e1be-4c6f-80e9-b5453f2ce1fe` | website / ongoing_projects | Launch of report 'Practices and Solutions: Accelerating Indian Industry Decarbonisation' | https://teriin.org/project/launch-report-practices-and-solutions-accelerating-indian-industry-decarbonisation |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `4bf09b06-a4dc-4daa-bb80-45fdbea9d4b9` | website / page | Industry Charter for Near Zero Emission Ambition by 2050 | https://teriin.org/industry-charter-near-zero-emission-ambitio-2050 |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |
| `2835cda0-2514-4638-848d-b76b389f83b7` | website / events | Industry leaders echo how competitiveness is driving industrial decarbonization, clean tech and green finance | https://teriin.org/event/industry-leaders-echo-how-competitiveness-driving-industrial-decarbonization-clean-tech-and |

**Notes**: NEAR-DUPLICATE of Q020 ('What research is TERI undertaking on industrial decarbonization?'). Same evidence base; gold answers deliberately aligned. Flagged in the duplicates section.

---

### Q049 - What are TERI's initiatives in electric mobility and EV ecosystems?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's electric-mobility work combines skilling, policy and city-level implementation. Skilling: the 'Future-In-Charge' programme for India's EV charging workforce, expanded to Pune, Bengaluru and Kolkata (Dec 2025) with Phase 2 launched in Bengaluru (July 2026), and a policy-brief roadmap for Zero Emission Truck (ZET) skilling in India (Jan 2026). Policy and awareness: the policy brief 'Let’s Electrify- Accelerating Electric Vehicle Adoption and Awareness in India' (Sept 2025); a comparative LCA between ICE-vehicle and EV powertrain components; a Digital Knowledge Library on electric mobility and low-emission transport in India; and a readiness and capacity-needs assessment for EV adoption in Indian cities. Implementation: backing an EV deployment by the Naroda GIDC industries association (2026) and a multi-stakeholder roundtable on inclusive EV transition in Coimbatore (2026).

**Expected facts**

- TERI runs the 'Future-In-Charge' skilling programme for India's EV charging workforce, expanded to Pune, Bengaluru and Kolkata and with Phase 2 launched in Bengaluru in July 2026.
- TERI published a 'Policy Brief: Roadmap for Zero Emission Truck (ZET) Skilling in India' (January 2026).
- TERI published the policy brief 'Let’s Electrify- Accelerating Electric Vehicle Adoption and Awareness in India' (September 2025).
- TERI conducted a comparative Life Cycle Assessment between powertrain components of ICE vehicles and EVs.
- TERI maintains a Digital Knowledge Library on electric mobility and low-emission transport in India.
- TERI backed an electric-mobility deployment by the Naroda GIDC industries association and convened a multi-stakeholder roundtable on inclusive EV transition in Coimbatore (2026).

**Expected entities**: Future-In-Charge, Zero Emission Truck (ZET) skilling, Let's Electrify, Digital Knowledge Library on electric mobility, Naroda GIDC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `53af300b-96d8-4ac2-a056-aa49118f4937` | website / press_release | TERI Launches ‘Future-In-Charge’ Phase 2 in Bengaluru to Power India’s EV Charging Workforce | https://teriin.org/press-release/teri-launches-future-charge-phase-2-bengaluru-power-indias-ev-charging-workforce |
| `a8020a48-7603-44d0-80f5-61adba3eac1c` | website / news | TERI Launches 'Future-In-Charge' Phase 2 in Bengaluru to Power India's EV Charging Workforce | https://teriin.org/news/teri-launches-future-charge-phase-2-bengaluru-power-indias-ev-charging-workforce |
| `cb8af9b6-8295-4dc5-b447-dee5af37a686` | website / press_release | ‘Future-In-Charge’ Skilling Programme Expands Training to Pune, Bengaluru, and Kolkata | https://teriin.org/press-release/future-charge-skilling-programme-expands-training-pune-bengaluru-and-kolkata |
| `f0f9e576-bf3c-4a6c-93c2-6f8e88f0022b` | website / policy_brief | Policy Brief: Roadmap for Zero Emission Truck (ZET) Skilling in India | https://teriin.org/policy-brief/policy-brief-roadmap-zero-emission-truck-zet-skilling-india |
| `80bd4f12-3c7b-4aef-a1d0-49564f318a67` | website / policy_brief | Let’s Electrify- Accelerating Electric Vehicle Adoption and Awareness in India | https://teriin.org/policy-brief/lets-electrify-accelerating-electric-vehicle-adoption-and-awareness-india |
| `0c465c3c-c760-498a-898c-c157eb0ddb1c` | website / ongoing_projects | Comparative LCA Between Powertrain Components of ICE Vehicles Versus EVs | https://teriin.org/project/comparative-lca-between-powertrain-components-ice-vehicles-versus-evs |
| `1df53443-e533-47ff-9cc4-ef8075a3fbbf` | website / ongoing_projects | Digital Knowledge Library on electric mobility and low emission transport in India | https://teriin.org/project/digital-knowledge-library-electric-mobility-and-low-emission-transport-india |
| `a29d65a2-7410-48e1-9cba-0c6ce685dbfc` | website / article | Readiness and Capacity Needs Assessment for Electric Vehicle Adoption in Indian Cities | https://teriin.org/casestudies/readiness-and-capacity-needs-assessment-electric-vehicle-adoption-indian-cities |
| `1fd6da24-6dfb-43fa-9760-0bc30924327a` | website / press_release | TERI Backs Electric Mobility Push at Naroda GIDC as Industries Association Deploys EVs for Estate Services | https://teriin.org/press-release/teri-backs-electric-mobility-push-naroda-gidc-industries-association-deploys-evs |
| `ea375c7c-e3ba-40a0-bdef-052c78b4887c` | website / press_release | TERI Convenes Multi-Stakeholder Roundtable in Coimbatore on Inclusive EV Transition | https://teriin.org/press-release/teri-convenes-multi-stakeholder-roundtable-coimbatore-inclusive-ev-transition |
| `c33b983a-16fb-431d-91b2-925f00250e89` | website / events | WSDS 2026 Thematic Track: Partnerships for Accelerating EV Skilling Ecosystem in India | https://teriin.org/event/wsds-2026-thematic-track-partnerships-accelerating-ev-skilling-ecosystem-india |

**Notes**: Much of the EV content in the corpus is third-party news about Indian EV policy (Delhi EV policy, NITI Aayog targets, battery localisation). Only TERI-authored items above should be credited.

---

### Q050 - How does TERI support decentralized renewable energy systems?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports decentralised renewable energy (DRE) through technology, delivery models and policy. It states its work spans decentralized energy solutions for rural livelihoods. Current work: a TERI-MNRE partnership to scale decentralized energy with a shared vision for green growth (2026); projects enhancing women's empowerment as employees and entrepreneurs in DRE and empowering women-led DRE enterprises in Rajasthan; support for PPP models deploying DRE and energy-efficiency systems in MSME clusters; and the ceramic-membrane and gasifier technologies for decentralised service delivery. Its research base includes mini-grid studies (solar PV mini-grids vs large-scale embedded PV in Uttar Pradesh; a coevolutionary perspective on a solar mini-grid; mini-grid-based off-grid electrification to enhance access in developing countries; consumers' willingness to pay for solar-microgrid electricity attributes) and mini-grid workshops including Green Mini-grid Development in South Asia.

**Expected facts**

- TERI states its work includes decentralized energy solutions for rural livelihoods.
- TERI and MNRE partnered on a unified vision for green growth to scale decentralized energy (February 2026).
- TERI runs projects on enhancing women's empowerment as employees and entrepreneurs in decentralised renewable energy and on empowering women-led DRE enterprises in Rajasthan.
- TERI supports PPP models for deployment of DRE and energy-efficiency systems in identified MSME clusters.
- TERI's mini-grid research includes solar PV mini-grids versus large-scale embedded PV generation in Uttar Pradesh, mini-grid-based off-grid electrification for developing countries, and consumers' willingness to pay for solar-microgrid electricity attributes.

**Expected entities**: decentralised renewable energy, MNRE, mini-grid

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `05bcdbf7-bb9e-40fe-bee5-2cf473386328` | website / events | A Unified Vision for Green Growth: TERI and MNRE Partner to Scale Decentralized Energy with a strategic worksh | https://teriin.org/event/unified-vision-green-growth-teri-and-mnre-partner-scale-decentralized-energy-strategic |
| `017c11bf-7ad0-4a0a-99d8-3cc51051d7db` | website / ongoing_projects | Enhancing women’s empowerment as employees and entrepreneurs in decentralised renewable energy | https://teriin.org/project/enhancing-womens-empowerment-employees-and-entrepreneurs-decentralised-renewable-energy |
| `f3e894b7-b3c2-41e5-b4be-f4df5ca05e5d` | website / completed_projects | Empowering Women-Led Enterprises in Rajasthan through Decentralized Renewable Energy | https://teriin.org/project/empowering-women-led-enterprises-rajasthan-through-decentralized-renewable-energy |
| `f083534d-1c50-423a-8b26-d86c156a7a59` | website / ongoing_projects | Support PPP models for deployment of DRE and EE systems in identified MSME clusters in rural India | https://teriin.org/project/support-ppp-models-deployment-dre-and-ee-systems-identified-msme-clusters-rural-india |
| `f8e3c5c4-b7dc-4ee4-aaf4-efa3f63a019b` | website / research_papers | Solar PV mini-grids versus large-scale embedded PV generation: A case study of Uttar Pradesh (India) | https://teriin.org/research-paper/solar-pv-mini-grids-versus-large-scale-embedded-pv-generation-case-study-uttar |
| `f978ff13-7d69-467a-a9c1-dfd28f65bb6d` | website / research_papers | A coevolutionary perspective on decentralised electrification: a solar mini-grid project in India | https://teriin.org/research-paper/coevolutionary-perspective-decentralised-electrification-solar-mini-grid-project |
| `5ffb105d-a7b1-425a-b679-aa9252d5f0d6` | website / research_papers | Mini-grid based off-grid electrification to enhance electricity access in developing countries: What policies  | https://teriin.org/research-paper/mini-grid-based-grid-electrification-enhance-electricity-access-developing-countries |
| `8e406b56-d320-42af-af35-e1726bd12034` | website / research_papers | ​Solar microgrids in rural India: Consumers' willingness to pay for attributes of electricity​ | https://teriin.org/research-paper/solar-microgrids-rural-india-consumers-willingness-pay-attributes-electricity-0 |
| `db4b523c-e33c-452f-8c0c-aef478bddc3b` | website / events | Workshop on Green Mini-grid Development in South Asia | https://teriin.org/event/workshop-green-mini-grid-development-south-asia |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |

---

### Q051 - What developments is TERI pursuing in clean cooking energy?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's clean-cooking developments centre on its own smokeless clean-combustion cookstove (2 kWth, 15-20% more effective than conventional stoves, wood pieces and briquettes as fuel, customisable for rural needs, distributed for community cooking under TERI's social-transformation programme) and on a biomass gasifier demonstrated in April 2026 for clean, affordable community cooking. Delivery and policy work: the Bihar Clean Cookstove Programme building energy access through women entrepreneurs; TERI and GIZ enabling Assam communities to adopt clean cooking and save forests (2019); projects estimating the carbon benefit of shifting rural households to improved cookstoves; the policy brief 'Clean fuel for cooking: Solution to achieve better air quality'; and a body of research on induction stoves, methanol cookstoves, cookstove adoption barriers, gender and cooking-energy transitions, and cookstove performance testing (including a Wireless Cookstove Sensing System).

**Expected facts**

- TERI's clean combustion cookstove is smokeless, 15-20% more effective than conventional stoves, has 2 kWth thermal capacity, uses wood pieces and briquettes, and has been distributed for community cooking in villages.
- TERI demonstrated a biomass gasifier for clean, affordable community cooking in April 2026.
- TERI runs 'Enhancing Energy Access through Women Entrepreneurs in Bihar - Clean Cookstove Program'.
- TERI and GIZ worked to enable communities in Assam to adopt clean cooking and save forests (2019).
- TERI has projects estimating the carbon benefit of shifting rural households to improved cookstoves.
- TERI published the policy brief 'Clean fuel for cooking: Solution to achieve better air quality'.
- TERI research covers induction stoves for clean cooking in rural India, methanol cookstoves, barriers to cleaner cookstove adoption, and clean cooking's effect on women's social position.

**Expected entities**: clean combustion cookstove, biomass gasifier, Bihar Clean Cookstove Program, GIZ

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `e7992c51-eeaa-4a47-9b8d-5a218bb2dd7c` | website / press_release | TERI Demonstrates Biomass Gasifier for Clean, Affordable Community Cooking; Invites Media to Experience Techno | https://teriin.org/press-release/teri-demonstrates-biomass-gasifier-clean-affordable-community-cooking-invites-media |
| `dd64ff29-b63a-43fd-84aa-d6e11378b53a` | website / ongoing_projects | Enhancing Energy Access through Women Entrepreneurs in Bihar - Clean Cookstove Program | https://teriin.org/project/enhancing-energy-access-through-women-entrepreneurs-bihar-clean-cookstove-program |
| `1c08a710-54fe-46cb-9d54-49f72ef94125` | website / press_release | TERI and GIZ to enable communities in Assam adopt clean cooking, save forests | https://teriin.org/press-release/teri-and-giz-enable-communities-assam-adopt-clean-cooking-save-forests |
| `a9b51697-df0e-4b86-9dbb-d73e8c122560` | website / ongoing_projects | Estimate the potential carbon benefit earn by shifting households to improved cookstoves | https://teriin.org/project/estimate-potential-carbon-benefit-earn-shifting-households-improved-cookstoves |
| `e9ad0399-5671-46ea-af58-3c22c1577c40` | website / completed_projects | Assessment of Potential Carbon Benefits by Shifting to Improved Cookstove in Rural Households of West Bengal | https://teriin.org/project/assessment-potential-carbon-benefits-shifting-improved-cookstove-rural-households-west |
| `792d3916-b497-4697-90d1-724fc858c161` | website / policy_brief | Clean fuel for cooking: Solution to achieve better air quality | https://teriin.org/policy-brief/clean-fuel-cooking-solution-achieve-better-air-quality |
| `51ec43ee-3057-4e6e-9b33-b067bf45bffa` | website / research_papers | Induction stoves as an option for clean cooking in rural India | https://teriin.org/research-paper/induction-stoves-option-clean-cooking-rural-india |
| `bdc5ffe0-87ca-4c90-a0f5-daae6cd0c9e7` | website / research_papers | Energising change: Clean cooking and the changing social position of women | https://teriin.org/research-paper/energising-change-clean-cooking-and-changing-social-position-women |
| `38e05390-a193-4d6e-a719-c05c5c9b2a07` | website / research_papers | Adoption of cleaner cookstoves: Barriers and way forward | https://teriin.org/research-paper/adoption-cleaner-cookstoves-barriers-and-way-forward |

---

### Q052 - How does TERI approach climate adaptation and resilience?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's approach to climate adaptation and resilience: in India its climate work focuses on climate modelling to understand climate variability at regional scales and on studying the risks and vulnerabilities of key sectors - water, health, agriculture and industry - with the climate science inextricably linked to policy research and recommendations for the Indian government's domestic policies and its position in global negotiations, extended to other emerging economies. Operationally, its climate-change-risk-assessment service generates climate projections at global and regional scales and impacts, vulnerability and adaptation assessments in key sectors using established models and an in-house super-computing facility. Applied adaptation work includes health vulnerability assessments (Madhya Pradesh; a national assessment with a monitoring and evaluation framework), the State Air Quality Health Adaptation Plan for Maternal and Child Health, water security and climate adaptation in rural India, building climate resilience in smallholder fish farming, and the REWARD watershed programme. On the multilateral side TERI produced 'A Transformative Global Goal on Adaptation: Scope, Science and Policy' and 'Road to Dubai and the Global Goal on Adaptation', and contributed to the National Adaptation Plan stakeholder consultation.

**Expected facts**

- TERI's climate work in India focuses on climate modelling to better understand climate variability at regional scales.
- TERI studies the risks and vulnerabilities of key sectors including water, health, agriculture and industry.
- TERI's climate science is linked to policy research and recommendations for India's domestic policies and its position in global negotiations, and is being extended to other emerging economies.
- TERI's climate-change risk assessment generates climate projections at global and regional scales and impacts, vulnerability and adaptation assessments using established models and an in-house super-computing facility.
- TERI conducted health vulnerability assessments for Madhya Pradesh and a national-level health vulnerability assessment with a monitoring and evaluation framework.
- TERI produced 'A Transformative Global Goal on Adaptation: Scope, Science and Policy' and 'Road to Dubai and the Global Goal on Adaptation'.
- TERI participated in the stakeholder consultation on India's National Adaptation Plan (traditional knowledge and heritage).

**Expected entities**: Global Goal on Adaptation, National Adaptation Plan, REWARD, AQHAP

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |
| `7d39891b-4d13-4c13-8a82-18bae8d0215d` | website / ongoing_projects | Health vulnerability assessment for Madhya Pradesh: building health sector resilience for climate change | https://teriin.org/project/health-vulnerability-assessment-madhya-pradesh-building-health-sector-resilience-climate |
| `e1418a8e-cc09-4599-a7f2-6a82a92f37ff` | website / ongoing_projects | National Level Health Vulnerability Assessment and develop a Framework for Monitoring and Evaluation of the Na | https://teriin.org/project/national-level-health-vulnerability-assessment-and-develop-framework-monitoring-and |
| `c9234a8a-a45e-450f-accc-7bb1348c5dec` | website / completed_projects | Developing State Air Quality Health Adaptation Plan for Maternal and Child Health (AQHAP), 2025-2030 \| Maharas | https://teriin.org/project/developing-state-air-quality-health-adaptation-plan-maternal-and-child-health-aqhap-2025 |
| `69358ff1-4b2f-47a8-bdce-01d5ba6aa794` | website / ongoing_projects | Environment, Climate and Water Security: Water Security and Climate Adaptation in Rural India (WASCA) | https://teriin.org/project/environment-climate-and-water-security-water-security-and-climate-adaptation-rural-india |
| `09fc7987-d3a2-4eab-bb06-fd6054d0a34e` | website / ongoing_projects | Building Climate Resilience in Smallholder Fish Farming | https://teriin.org/project/building-climate-resilience-smallholder-fish-farming |
| `f5d7666d-64e9-4192-ad56-71b6ecd68edc` | website / policy_brief | A Transformative Global Goal on Adaptation: Scope, Science and Policy | https://teriin.org/policy-brief/transformative-global-goal-adaptation-scope-science-and-policy |
| `3d632bf3-735d-46a8-b40d-73b03750bc29` | website / policy_brief | Road to Dubai and the Global Goal on Adaptation | https://teriin.org/policy-brief/road-dubai-and-global-goal-adaptation |
| `04314f7e-b4b4-4334-a77e-2ac4d6635aae` | website / events | Stakeholder Consultation on the National Adaptation Plan (NAP): Traditional Knowledge and Heritage | https://teriin.org/event/stakeholder-consultation-national-adaptation-plan-nap-traditional-knowledge-and-heritage |

---

### Q053 - What climate risk assessment methodologies does TERI use?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> The methods TERI states it uses for climate risk assessment: generating climate projections at global and regional scales using established models plus an in-house super-computing facility; conducting impacts, vulnerability and adaptation assessments in key sectors; and GHG inventorization and mitigation analysis. Specific methodological instruments in the corpus: a Vulnerability Index Tool for health vulnerability assessment; statistical analysis of future short-duration rainfall using bias-corrected GCM ensembles; GIS and machine-learning approaches to assess forest and biodiversity vulnerability under climate stress (case study Assam); a vulnerability matrix concept for tracking agricultural productivity loss from slow-onset events; sectoral climate-risk screening (the ORCHID DFID-India Climate Risk Screening Process; climate risks to India's oil and gas sector); and physical versus transition risk framing developed with the Reserve Bank of India for the banking sector.

**Expected facts**

- TERI generates climate projections at global and regional scales using established models and an in-house super-computing facility.
- TERI conducts impacts, vulnerability and adaptation assessments in key sectors, plus GHG inventorization and mitigation analysis.
- TERI developed a Vulnerability Index Tool for health vulnerability assessment.
- TERI uses bias-corrected GCM ensembles in statistical analysis of future short-duration rainfall trends.
- TERI uses GIS and machine-learning approaches to assess forest and biodiversity vulnerability under climate stress, with a case study from Assam.
- TERI has applied climate-risk screening at sector level, including the ORCHID DFID-India Climate Risk Screening Process and an assessment of climate risks to India's oil and gas sector.
- TERI worked with the Reserve Bank of India on climate-induced physical and transition risks for the banking sector.

**Expected entities**: Vulnerability Index Tool, GCM ensembles, ORCHID, Reserve Bank of India

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |
| `da24182b-dd8a-4c14-af99-2edca57cde73` | website / article | Vulnerability Index Tool: Vulnerability assessment for health | https://teriin.org/article/vulnerability-index-tool-vulnerability-assessment-health |
| `0383d503-060b-46d4-a7f8-db1a9b56f507` | website / research_papers | Future trends in short-duration rainfall: A statistical analysis using bias-corrected GCM ensembles | https://teriin.org/research-paper/future-trends-short-duration-rainfall-statistical-analysis-using-bias-corrected-gcm |
| `28eeb229-b331-4889-ad05-368531ae6f82` | website / research_papers | GIS & Machine Learning Based Approaches to Assess Forest and Biodiversity Vulnerability Under Climate Stress:  | https://teriin.org/research-paper/gis-machine-learning-based-approaches-assess-forest-and-biodiversity-vulnerability |
| `130b7102-843a-46d5-a7a5-f3e2ceb4aaca` | website / completed_projects | ORCHID project: DFID-India Climate Risk Screening Process | https://teriin.org/project/orchid-project-dfid-india-climate-risk-screening-process |
| `d7d95190-3a5f-41f1-a7de-331823455bfd` | website / completed_projects | Assessing climate risks to India's oil and gas sector | https://teriin.org/project/assessing-climate-risks-indias-oil-and-gas-sector |
| `b3a0b206-8545-4030-b5e8-14278f6946bd` | website / events | TERI-RBI Workshop on Climate Induced Physical and Transition Risks | https://teriin.org/event/teri-rbi-workshop-climate-induced-physical-and-transition-risks |
| `397b8e72-647d-414f-bb2b-2ac59c4cf96d` | website / page | SDG 13. CLIMATE ACTION | https://teriin.org/SDG-13-Climate-Action |

**Notes**: The service page is the authoritative statement of method; the rest are instances. There is no single published TERI methodology document, so an answer naming a named proprietary framework should be treated as unsupported.

---

### Q054 - What are carbon markets and carbon credits?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual / definitional
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT tag, COUNT(*) FROM documents_tag WHERE tag LIKE '%carbon market%' -> 'Carbon market' 60, 'Carbon markets' 5; 'carbon credit' tags -> none`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `28ad24b0-265f-4e54-bdf6-20093a91c89d` | website / ongoing_projects | Achieving a Just Transition in India with an Effective Carbon Credit Trading Scheme | https://teriin.org/project/achieving-just-transition-india-effective-carbon-credit-trading-scheme |
| `824a4f1b-f3b8-43f3-842a-7126bd0105c3` | website / ongoing_projects | Developing a Voluntary Carbon Market Project with FPOs for Agroforestry Plantation in Saharanpur District, Utt | https://teriin.org/project/developing-voluntary-carbon-market-project-fpos-agroforestry-plantation-saharanpur-district |
| `64c01001-2296-4a33-a6d2-4e336c966407` | website / ongoing_projects | Developing Voluntary Carbon Market Projects for Agroforestry Plantations in Kanpur Forest Circle, Uttar Prades | https://teriin.org/project/developing-voluntary-carbon-market-projects-agroforestry-plantations-kanpur-forest-circle |
| `870aa800-c398-4678-8a4a-08c24edaa911` | website / ongoing_projects | Sustainable Livelihood through Carbon Finance and Agroforestry in Gorakhpur | https://teriin.org/project/sustainable-livelihood-through-carbon-finance-and-agroforestry-gorakhpur |
| `e4a68ac6-c2df-48b1-8af7-9b298444818b` | website / events | Building a Forestry Carbon Credit Roadmap for Uttarakhand under RECAP4NDC | https://teriin.org/event/building-forestry-carbon-credit-roadmap-uttarakhand-under-recap4ndc |

**Notes**: DEFINITION NOT IN THE CORPUS. Targeted full-text probes for definitional phrasings ('carbon credit is a', 'carbon market is a', 'one carbon credit', 'carbon credits are') returned no definitional passage. What the corpus DOES support is TERI's carbon-market WORK: 'Achieving a Just Transition in India with an Effective Carbon Credit Trading Scheme'; voluntary carbon market projects with FPOs for agroforestry plantations in Saharanpur, Kanpur Forest Circle and Gorakhpur; a forestry carbon-credit roadmap for Uttarakhand under RECAP4NDC; and 60 'Carbon market'-tagged documents. Answering the definitional half would require general world knowledge, which this gold-set phase forbids. A human must decide whether a general definition is acceptable.

---

### Q055 - How does TERI support organizations in achieving net-zero goals?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports organisations towards net zero mainly through the TERI Council for Business Sustainability (TERI CBS) and the Industry Charter for Near Zero Emission Ambition by 2050. TERI CBS is the interface between TERI's research and the corporate world; member services include sustainability strategy and roadmap development, performance benchmarking and improvement, participation in policy advocacy, and training and capacity building, with tailor-made advisory (strategy development, performance assessment and improvement, capacity building/MDPs) and complimentary consulting person-days plus discounted paid consulting for members; Gold members also get a complimentary sustainability-report assessment. The Industry Charter's focus areas are energy efficiency, renewable energy, circular economy, low-carbon solutions across the supply chain, carbon sequestration, technology demonstration and the business-policy interface. TERI also runs a Chief Sustainability Officers' Forum, published a Chief Sustainability Officers' Competency Framework, and launched a Corporate Sustainability Leadership Programme 2026 focused on ESG, AI and carbon.

**Expected facts**

- TERI Council for Business Sustainability (TERI CBS) is the interface for TERI's research to connect to the corporate world, governed by an Executive Committee of CEOs from member companies.
- TERI CBS member services include sustainability strategy and roadmap development, performance benchmarking and improvement, participation in policy advocacy, and training and capacity building.
- TERI CBS members receive complimentary consulting person-days annually and a discount on paid consulting services; Gold members additionally receive a complimentary assessment of their sustainability report.
- The Industry Charter for Near Zero Emission Ambition by 2050 covers energy efficiency, renewable energy, circular economy, low-carbon solutions across the supply chain, carbon sequestration, technology demonstration and the business-policy interface.
- TERI convenes a TERI CBS Chief Sustainability Officers' (CSO) Forum and a Director's Forum on Sustainability, and published a Chief Sustainability Officers' Competency Framework.
- TERI launched a Corporate Sustainability Leadership Programme 2026 focused on ESG, AI and carbon.

**Expected entities**: TERI Council for Business Sustainability, Industry Charter for Near Zero Emission Ambition by 2050, Chief Sustainability Officers' Forum, Corporate Sustainability Leadership Programme 2026

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `4a4b782f-5110-4520-aec6-92209213a948` | website / page | Business & Sustainability | https://teriin.org/business-sustainability |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |
| `59aebc8a-58e2-450e-8bb2-1c5615b20e6e` | website / basic | TERI Council for Business Sustainability |  |
| `4bf09b06-a4dc-4daa-bb80-45fdbea9d4b9` | website / page | Industry Charter for Near Zero Emission Ambition by 2050 | https://teriin.org/industry-charter-near-zero-emission-ambitio-2050 |
| `a5dc7df0-aa12-4a0d-8f33-32c8a7709012` | website / press_release | TERI Unveils Corporate Sustainability Leadership Programme 2026 Focused on ESG, AI, and Carbon Markets | https://teriin.org/press-release/teri-unveils-corporate-sustainability-leadership-programme-2026-focused-esg-ai-and |
| `9732ce4d-ce6a-433e-8637-a50fe8fb230d` | website / events | High Level Convening of Industry Charter for Near Zero Emissions by 2050 | https://teriin.org/event/high-level-convening-industry-charter-near-zero-emissions-2050 |

---

### Q056 - How does TERI address air pollution in Indian cities?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI addresses urban air pollution through evidence generation, city planning support and public advocacy. Its explainer 'How evidence-based actions can help achieve breathable air in Indian cities' sets out the argument; its Air Quality Research service delivers monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air-quality management planning at urban, regional and national scales through a NABL-accredited laboratory, plus third-party audits and pilot demonstrations of emission-reduction technologies. City-level instruments include Clean Air Zones pilots (Vijayawada, Visakhapatnam and other cities in Andhra Pradesh), emission-inventory/source-apportionment/atmospheric-carrying-capacity studies (Delhi-NCR, Kolkata and Howrah, Rishikesh, Kashipur, Faridabad), local air-quality management plans (e.g. Gorakhpur), an Integrated AQI and Liveability Framework, and capacity building for pollution control boards and urban officials. Public-facing outputs include TERI's 10-point action plan for cleaning India's air and infographics on Delhi-NCR air quality.

**Expected facts**

- TERI's Air Quality Research service covers monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air-quality management planning at urban, regional and national scales through a NABL-accredited laboratory.
- TERI is piloting Clean Air Zones in Andhra Pradesh cities including Vijayawada and Visakhapatnam.
- TERI conducts emission inventory, source apportionment and atmospheric carrying-capacity studies for Indian cities, including Delhi-NCR, Kolkata and Howrah, Rishikesh, Kashipur and Faridabad.
- TERI develops local air-quality management plans for city areas, for example Golghar and Shaheed Smarak in Gorakhpur.
- TERI is developing an Integrated Air Quality Index (AQI) and Liveability Framework.
- TERI runs capacity-building programmes on ambient air-quality management for state pollution control boards and city officials, including West Bengal and Kolkata.
- TERI published a 10-point action plan towards cleaning India's air.

**Expected entities**: Clean Air Zones, 10-point action plan, Integrated AQI and Liveability Framework

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `f0f1c9fc-67cd-4372-8205-95d615cd148d` | website / page | Explainer: How evidence-based actions can help achieve breathable air in Indian cities | https://teriin.org/environment/air/explainer-how-evidence-based-actions-help-achieve-breathable-air-indian-cities |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `34425ba3-e6e5-482b-8599-d10871edf964` | website / ongoing_projects | Improving Urban Air Quality through Clean Air Zones in Andhra Pradesh | https://teriin.org/project/improving-urban-air-quality-through-clean-air-zones-andhra-pradesh |
| `d6c23474-8f0a-4502-925d-33d07e1c74d5` | website / ongoing_projects | Improving Urban Air Quality by Facilitating Piloting of Clean Air Zones in Vijayawada & Visakhapatnam | https://teriin.org/project/improving-urban-air-quality-facilitating-piloting-clean-air-zones-vijayawada-visakhapatnam |
| `662bcd46-7785-41a5-b5ba-7573e97b7688` | website / events | Stakeholders Meeting on Local Air Quality Management Plan for Golghar and Shaheed Smarak areas in Patna | https://teriin.org/event/stakeholders-meeting-local-air-quality-management-plan-golghar-and-shaheed-smarak-areas-patna |
| `c402762d-53fc-4401-ace6-2bf25d5be8f3` | website / ongoing_projects | Development and Implementation of an Integrated Air Quality Index (AQI) and Liveability Framework for Krisala  | https://teriin.org/project/development-and-implementation-integrated-air-quality-index-aqi-and-liveability-framework |
| `741c7814-09ea-4292-8885-c0ff3cb5876b` | website / events | Capacity building training program for the officials of West Bengal Pollution Control Board on ‘emission inven | https://teriin.org/event/capacity-building-training-program-officials-west-bengal-pollution-control-board-emission |
| `6cda5963-88bd-4d3b-b75a-7ca878ff716e` | website / events | Capacity Building Program on Ambient Air Quality Management in Kolkata | https://teriin.org/event/capacity-building-program-ambient-air-quality-management-kolkata |
| `e8df5259-264d-4e77-91d3-533092346038` | website / infographics | TERI suggests a 10 point action plan towards cleaning India’s air | https://teriin.org/infographics/teri-suggests-10-point-action-plan-towards-cleaning-indias-air |
| `2823af8f-7454-44de-a4c2-13506c31d805` | website / infographics | State of air in Delhi NCR – pollution and solution | https://teriin.org/infographics/state-air-delhi-ncr-pollution-and-solution |
| `7e50bb16-8222-4a3a-801b-6662271c3ef0` | website / completed_projects | Emission Inventorisation for Faridabad Town | https://teriin.org/project/emission-inventorisation-faridabad-town |

---

### Q057 - What research is TERI doing on climate finance and ESG?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> On climate finance TERI's current work includes the Five Pillar Framework for Bankability, the 'Modeling for Climate Finance' policy brief and the ICEF climate-finance modelling contribution with Schmidt Sciences, blended-finance analysis, the 'Road to Baku' New Collective Quantified Goal paper, and national dialogues with NBSC/NABARD and the RBI. On ESG its work includes the ongoing project 'Green Port Index and ESG-based Reporting for Indian Major Ports' and the Green Port Performance Index; a three-month ESG certification programme run in partnership with NDTV; the Corporate Sustainability Leadership Programme 2026 focused on ESG, AI and carbon; a partnership with Vedanta to accelerate its ESG goals; TERI CBS events on strategic ESG for business sustainability; and legal analysis that competition laws must adapt to support the ESG mandate.

**Expected facts**

- TERI's climate-finance work includes the Five Pillar Framework for Bankability, the 'Modeling for Climate Finance' policy brief, and climate-finance modelling in the ICEF report with Schmidt Sciences.
- TERI produced 'Road to Baku: The New Collective Quantified Goal on Climate Finance' under COP29 Compass.
- TERI runs the ongoing project 'Green Port Index and ESG-based Reporting for Indian Major Port' and published the Green Port Performance Index (GPPI).
- TERI in partnership with NDTV launched a three-month ESG certification programme (August 2025).
- TERI unveiled a Corporate Sustainability Leadership Programme 2026 focused on ESG, AI and carbon.
- Vedanta partnered with TERI to accelerate its ESG goals (2022).
- TERI published analysis arguing competition laws must adapt to support the ESG mandate.

**Expected entities**: Five Pillar Framework for Bankability, Green Port Performance Index, NDTV ESG certification, Vedanta, ICEF, Schmidt Sciences

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |
| `349ea25d-30d9-4315-94d9-dab2082d6592` | website / policy_brief | Modeling for Climate Finance | https://teriin.org/policy-brief/modeling-climate-finance |
| `4930609a-7c2d-467d-99a8-2c7249487809` | website / press_release | TERI Highlights Climate Finance Modeling in ICEF Report, in Collaboration with Schmidt Sciences | https://teriin.org/press-release/teri-highlights-climate-finance-modeling-icef-report-collaboration-schmidt-sciences |
| `b518a527-ae0c-494b-b534-3cbd9a08a27e` | website / ongoing_projects | Green Port Index and ESG-based Reporting for Indian Major Port | https://teriin.org/project/green-port-index-and-esg-based-reporting-indian-major-port |
| `ea40133f-b34c-4ac7-b02b-0da92afb00ab` | website / policy_brief | Green Port Performance Index (GPPI) Measuring Progress, Powering Green Transformation | https://teriin.org/policy-brief/green-port-performance-index-gppi-measuring-progress-powering-green-transformation |
| `bd80d6c7-4c68-4fe9-9c8b-40d1ae6ca7d8` | website / events | TERI in partnership with NDTV launches the 3-month ESG certification programme | https://teriin.org/event/teri-partnership-ndtv-launches-3-month-esg-certification-programme |
| `a5dc7df0-aa12-4a0d-8f33-32c8a7709012` | website / press_release | TERI Unveils Corporate Sustainability Leadership Programme 2026 Focused on ESG, AI, and Carbon Markets | https://teriin.org/press-release/teri-unveils-corporate-sustainability-leadership-programme-2026-focused-esg-ai-and |
| `29e1d06a-0457-477e-a8b8-ee78a8aa2e77` | website / press_release | Vedanta partners with TERI to accelerate ESG Goals | https://teriin.org/press-release/vedanta-partners-teri-accelerate-esg-goals |
| `4b3ab550-159b-42a5-b0d0-25f53b6f0520` | website / article | Competition Laws must adapt to support the ESG mandate | https://teriin.org/blog/competition-laws-must-adapt-support-esg-mandate |
| `2aa29d06-bc09-45b6-8538-a307f1204c3c` | website / events | Strategic ESG for Business Sustainability & Growth | https://teriin.org/event/strategic-esg-business-sustainability-growth |
| `435e7517-f469-405d-9f26-a669d48a4101` | website / policy_brief | Road to Baku: The New Collective Quantified Goal on Climate Finance | https://teriin.org/policy-brief/road-baku-new-collective-quantified-goal-climate-finance |

**Notes**: NEAR-DUPLICATE of Q018 for the climate-finance half. Note documents_tag has NO 'ESG' tag, so ESG work is only discoverable via titles and body text.

---

### Q058 - How does TERI help organizations reduce their environmental footprint?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI helps organisations reduce their environmental footprint through its services catalogue: detailed energy, water and resource-efficiency audits with techno-economic recommendations backed by simulations and monitoring; plant-level energy audits and energy-performance benchmarking, and technology assessments for industrial sectors; resource-conservation studies for buildings and complexes (TERI reports energy audits of around 200 buildings across hotels, offices, hospitals, schools, universities, malls and theatres, using an instrument pool and offering techno-economic proposals); green design consultancy integrating energy efficiency, renewable energy and resource management, including emission inventories and life-cycle assessments; water audits and quality testing with rainwater-harvesting and reuse recommendations; carbon-sink and biodiversity assessment of company plantations; GHG calculators covering Scope 1, 2 and 3; and NABL-accredited water, soil and sludge testing. Corporate members can additionally access TERI CBS performance benchmarking and improvement services.

**Expected facts**

- TERI conducts detailed energy, water and resource-efficiency audits across sectors with techno-economic recommendations backed by simulations and monitoring.
- TERI has conducted energy audits of around 200 buildings across categories including hotels, commercial offices, hospitals, schools, universities, shopping malls and theatres.
- TERI assists industries in reducing energy consumption through plant-level audits and undertakes technology assessments of energy and environmental performance for industrial sectors.
- TERI's green design consultancy integrates energy efficiency, renewable energy and resource management, and covers emission inventories and life-cycle assessments.
- TERI conducts water audits and quality testing including building water-use estimation, water-saving fixture recommendations, landscape water demand, rainwater-harvesting potential and treated-wastewater reuse.
- TERI estimates carbon sink and biodiversity co-benefits from plantation activities in and around company premises.
- TERI has developed GHG calculators covering Scope 1, 2 and 3 emissions.

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `89f45551-aaac-4e1a-8a95-5b1b9a43668c` | website / services | Audits, Validation & PMU Support |  |
| `7358c7aa-b509-45f7-8d72-bc4a3417e172` | website / services | Energy performance benchmarking |  |
| `1535f84a-ac24-486d-ba8b-613113900325` | website / services | Resource conservation study/ energy audit/energy management programme |  |
| `259d7fb3-cd37-4616-82e5-35c609abc18f` | website / services | Environmental Design & Technical Advisory |  |
| `59eea124-2fa3-491c-8c3d-63f2c9530e18` | website / services | Environmental design consultancy and advisory services |  |
| `3625b53b-5299-43c4-9e55-06bbe3aab259` | website / services | Multidisciplinary research on natural resource conservation |  |
| `2ef2427a-1fdb-4398-9b73-2c4719ac38a4` | website / services | Carbon sequestration potential and biodiversity assessment |  |
| `4eab067f-425a-4299-afee-f542e3a007f3` | website / services | Research, Innovation & Impact Assessment |  |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |

---

### Q059 - What are TERI's latest climate resilience projects?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=current; requested_period=most recent as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> TERI's most recently published climate-resilience projects and initiatives in this snapshot: 'Building Climate Resilience in Smallholder Fish Farming' (ongoing, July 2026); process monitoring under REWARD - Rejuvenating Watersheds for Agricultural Resilience through Innovative Development (ongoing, May 2026); the Aravalli Green Wall Initiative, India's landscape ecological restoration programme for climate resilience (May 2026); a WSDS 2026 roundtable on unlocking climate-resilience finance; 'Water Resource Management through Spring and Catchment Rejuvenation in Uttarakhand'; 'Environment, Climate and Water Security: Water Security and Climate Adaptation in Rural India'; national and state health-vulnerability assessments building health-sector resilience; and the conceptual framework 'Climate Resilience in Water Resource Management in India'.

**Expected facts**

- 'Building Climate Resilience in Smallholder Fish Farming' is an ongoing TERI project (July 2026).
- TERI conducts process monitoring under REWARD (Rejuvenating Watersheds for Agricultural Resilience through Innovative Development).
- The Aravalli Green Wall Initiative is described as India's landscape ecological restoration programme for climate resilience.
- TERI runs 'Water Resource Management through Spring and Catchment Rejuvenation in Uttarakhand' and 'Environment, Climate and Water Security: Water Security and Climate Adaptation in Rural India'.
- TERI conducted health vulnerability assessments to build health-sector resilience to climate change, including for Madhya Pradesh and at national level.
- TERI published the policy brief 'Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action'.

**Expected entities**: REWARD, Aravalli Green Wall Initiative

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `09fc7987-d3a2-4eab-bb06-fd6054d0a34e` | website / ongoing_projects | Building Climate Resilience in Smallholder Fish Farming | https://teriin.org/project/building-climate-resilience-smallholder-fish-farming |
| `040491c8-07dc-44f3-a141-a67246c44d08` | website / ongoing_projects | Process Monitoring under Rejuvenating Watersheds for Agricultural Resilience through Innovative Development (R | https://teriin.org/project/process-monitoring-under-rejuvenating-watersheds-agricultural-resilience-through-0 |
| `82750a29-285c-48cc-95b1-5353661625ad` | website / ongoing_projects | Process Monitoring under Rejuvenating Watersheds for Agricultural Resilience through Innovative Development (R | https://teriin.org/project/process-monitoring-under-rejuvenating-watersheds-agricultural-resilience-through-innovative |
| `67362d57-2345-4d19-982a-9a398c413c97` | website / events | Aravalli Green Wall Initiative: India’s Landscape Ecological Restoration Programme for Climate Resilience and  | https://teriin.org/event/aravalli-green-wall-initiative-indias-landscape-ecological-restoration-programme-climate |
| `95a66610-5c67-4745-8c32-021eb4b81b9a` | website / events | WSDS 2026 Thematic Track: Roundtable Discussion on ‘Unlocking Climate Resilience Finance to Strengthen Climate | https://teriin.org/event/wsds-2026-thematic-track-roundtable-discussion-unlocking-climate-resilience-finance |
| `a264bf56-b146-483e-be4c-9262ac8b4001` | website / ongoing_projects | Water Resource Management through Spring and Catchment Rejuvenation in Uttarakhand for Improving Water Securit | https://teriin.org/project/water-resource-management-through-spring-and-catchment-rejuvenation-uttarakhand-improving |
| `69358ff1-4b2f-47a8-bdce-01d5ba6aa794` | website / ongoing_projects | Environment, Climate and Water Security: Water Security and Climate Adaptation in Rural India (WASCA) | https://teriin.org/project/environment-climate-and-water-security-water-security-and-climate-adaptation-rural-india |
| `7baccf12-187c-400e-b2fa-4fa9ea04e549` | website / policy_brief | Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action | https://teriin.org/policy-brief/climate-resilience-water-resource-management-india-conceptual-framework-action |
| `7d39891b-4d13-4c13-8a82-18bae8d0215d` | website / ongoing_projects | Health vulnerability assessment for Madhya Pradesh: building health sector resilience for climate change | https://teriin.org/project/health-vulnerability-assessment-madhya-pradesh-building-health-sector-resilience-climate |

**Notes**: 'Latest' is interpreted as 'most recently published in the snapshot'. There is no climate-resilience facet, so the set is title/body-derived and not closed; score on correctness of the named projects, not completeness.

---

### Q060 - What sustainability frameworks has TERI developed?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Sustainability frameworks TERI has developed, as named in the corpus: 'India's Journey to Net Zero: A Conceptual Framework for Analysis' (2024); 'A Five Pillar Framework for Bankability' for recalibrating India's commercial finance for climate action (2026); 'Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action' (2024); the Chief Sustainability Officers' Competency Framework (2025); the Green Port Performance Index (GPPI); an Integrated Air Quality Index (AQI) and Liveability Framework; a framework for AgriPV DPR development; the GRIHA rating system and GRIHA Infrastructure Rating; the SDG Blueprint for Sustainable Agriculture; the Green Budgeting Toolkit 2.0; and a compendium and enforcement framework for energy-efficiency regulations.

**Expected facts**

- TERI developed 'India's Journey to Net Zero: A Conceptual Framework for Analysis'.
- TERI developed 'A Five Pillar Framework for Bankability: Recalibrating India's Commercial Finance for Climate Action'.
- TERI developed 'Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action'.
- TERI published a Chief Sustainability Officers' Competency Framework.
- TERI developed the Green Port Performance Index (GPPI).
- TERI is developing an Integrated Air Quality Index (AQI) and Liveability Framework.
- TERI developed the GRIHA green-building rating system (with MNRE, 2007) and a GRIHA Infrastructure Rating for logistics parks and warehouses.
- TERI developed the SDG Blueprint for Sustainable Agriculture and the Green Budgeting Toolkit 2.0.

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `862bb586-1914-40ce-bc89-97f99869e872` | website / research_papers | Discussion paper on India’s Journey to Net Zero: A Conceptual Framework  for Analysis | https://teriin.org/research-paper/discussion-paper-indias-journey-net-zero-conceptual-framework-analysis |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |
| `7baccf12-187c-400e-b2fa-4fa9ea04e549` | website / policy_brief | Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action | https://teriin.org/policy-brief/climate-resilience-water-resource-management-india-conceptual-framework-action |
| `59aebc8a-58e2-450e-8bb2-1c5615b20e6e` | website / basic | TERI Council for Business Sustainability |  |
| `ea40133f-b34c-4ac7-b02b-0da92afb00ab` | website / policy_brief | Green Port Performance Index (GPPI) Measuring Progress, Powering Green Transformation | https://teriin.org/policy-brief/green-port-performance-index-gppi-measuring-progress-powering-green-transformation |
| `c402762d-53fc-4401-ace6-2bf25d5be8f3` | website / ongoing_projects | Development and Implementation of an Integrated Air Quality Index (AQI) and Liveability Framework for Krisala  | https://teriin.org/project/development-and-implementation-integrated-air-quality-index-aqi-and-liveability-framework |
| `39360ecc-576c-4b80-8e91-97dc7ac4dbaa` | website / policy_brief | FRAMEWORK FOR AGRIPV DPR DEVELOPMENT | https://teriin.org/policy-brief/framework-agripv-dpr-development |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `98800b2a-5011-43be-ad73-6039b898ca8e` | website / events | LAUNCH OF GRIHA INFRASTRUCTURE RATING FOR LOGISTICS PARKS AND WAREHOUSES | https://teriin.org/event/launch-griha-infrastructure-rating-logistics-parks-and-warehouses |
| `fc588c50-391a-400c-a6ad-74707615b2af` | website / policy_brief | SDG Blueprint for Sustainable Agriculture | https://teriin.org/policy-brief/sdg-blueprint-sustainable-agriculture |
| `df038222-1e13-4bae-b7db-db6948f5aab7` | website / press_release | TERI Unveils Green Budgeting Toolkit 2.0 to Power Greener Public Finance and Drive the Green Economy | https://teriin.org/press-release/teri-unveils-green-budgeting-toolkit-20-power-greener-public-finance-and-drive-green |
| `2af986df-47bc-4896-b5ac-1509d1c52a25` | website / ongoing_projects | Compendium and Enforcement Framework for Energy Efficiency Regulations | https://teriin.org/project/compendium-and-enforcement-framework-energy-efficiency-regulations |

**Notes**: Overlaps Q023 (policy tools). Gold answers are deliberately consistent; a framework named in one should not be penalised in the other.

---

### Q061 - How does TERI support sustainable consumption and lifestyles?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's work on sustainable consumption and lifestyles is largely built around India's Mission LiFE and the G20/multilateral agenda. Outputs: 'Internationalizing Lifestyles For Environment: Messages For G20' (2023); 'Internationalizing Lifestyles For Sustainable Development' (2023); 'Internationalizing Sustainable Lifestyles for Climate Justice' (2024); 'Promoting Sustainable Lifestyles: Metrics, Instruments, and Proposals for G20' (2023); 'From Linear to Circular: Pathways for Sustainable Lifestyles' (2023); 'Internationalising Lifestyle for the Environment' (2025); and the policy brief 'Green Public Procurement for Advancing Sustainable Development in India: Policy Nudges for Promoting Sustainable Consumption and Production' (2024). Programmes and convenings include the Mission LiFE Youth Ambassador Programme, 'Generation Green: Promoting Sustainable Lifestyles for Youth, by Youth', the COP29 Compass Dialogue on Sustainable Lifestyles, the Youth Climate Conclave, and the SDG Charter Dialogue on green budgeting and sustainable lifestyles.

**Expected facts**

- TERI published 'Internationalizing Lifestyles For Environment: Messages For G20' (2023).
- TERI published 'Promoting Sustainable Lifestyles: Metrics, Instruments, and Proposals for G20' (2023).
- TERI published 'Internationalizing Sustainable Lifestyles for Climate Justice' (2024).
- TERI published 'From Linear to Circular: Pathways for Sustainable Lifestyles' (2023).
- TERI published 'Green Public Procurement for Advancing Sustainable Development in India: Policy Nudges for Promoting Sustainable Consumption and Production' (2024).
- TERI runs a Mission LiFE Youth Ambassador Programme.
- TERI convened 'Generation Green: Promoting Sustainable Lifestyles for Youth, by Youth' and a COP29 Compass Dialogue on Sustainable Lifestyles.

**Expected entities**: Mission LiFE, G20, Green Public Procurement, Generation Green, COP29 Compass

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `cee29919-7405-43ce-bc22-cbe576317e0e` | website / policy_brief | Internationalizing Lifestyles For Environment: Messages For G20 | https://teriin.org/policy-brief/internationalizing-lifestyles-environment-messages-g20 |
| `96c74dfe-14ad-42b0-974b-989ce588225f` | website / policy_brief | Internationalizing Lifestyles For Sustainable Development | https://teriin.org/policy-brief/internationalizing-lifestyles-sustainable-development |
| `8a03ac91-d8de-4d66-8320-87a9a6762783` | website / policy_brief | Internationalizing Sustainable Lifestyles for Climate Justice | https://teriin.org/policy-brief/internationalizing-sustainable-lifestyles-climate-justice |
| `a0b98071-3247-48c0-99d7-a0b4989e440f` | website / research_papers | Promoting Sustainable Lifestyles: Metrics, Instruments, and Proposals for G20 | https://teriin.org/research-paper/promoting-sustainable-lifestyles-metrics-instruments-and-proposals-g20 |
| `72be821f-7a85-4ebc-ae98-32ed4cd79707` | website / research_papers | From Linear to Circular: Pathways for Sustainable Lifestyles | https://teriin.org/research-paper/linear-circular-pathways-sustainable-lifestyles |
| `066def98-2f5d-4d4f-985f-7a656dc720b5` | website / research_papers | Internationalising Lifestyle for the Environment | https://teriin.org/research-paper/internationalising-lifestyle-environment |
| `c8ccf5bd-e5ef-4eec-a902-59ef355feeea` | website / policy_brief | Green Public Procurement for Advancing Sustainable Development in India: Policy Nudges for Promoting Sustainab | https://teriin.org/policy-brief/green-public-procurement-advancing-sustainable-development-india-policy-nudges |
| `02670148-e914-4cc9-89ea-e2660a376b95` | website / ongoing_projects | Mission LiFE Youth Ambassador Programme | https://teriin.org/project/mission-life-youth-ambassador-programme |
| `70fddb28-3802-4dfa-b8b4-e1878417ea6f` | website / events | Generation Green: Promoting Sustainable Lifestyles for Youth, by Youth | https://teriin.org/event/generation-green-promoting-sustainable-lifestyles-youth-youth |
| `34aea232-7bb0-436e-bf1c-1c2a2ee39abf` | website / events | COP29 Compass Dialogue on Sustainable Lifestyles | https://teriin.org/event/cop29-compass-dialogue-sustainable-lifestyles |
| `b694994f-7b4c-4dd2-8402-7e263c68098e` | website / press_release | TERI’s SDG Charter Dialogue engages with experts on Green Budgeting and Sustainable Lifestyles | https://teriin.org/press-release/teris-sdg-charter-dialogue-engages-experts-green-budgeting-and-sustainable-lifestyles |

---

### Q062 - What water conservation initiatives is TERI undertaking?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's water-conservation work spans catchment rejuvenation, audits, certification and youth mobilisation. Current/recent: 'Water Resource Management through Spring and Catchment Rejuvenation in Uttarakhand'; 'Air to Water as solution for rural water security'; 'Environment, Climate and Water Security: Water Security and Climate Adaptation in Rural India'; and a State Specific Action Plan for the water sector for Manipur. Service lines: water audits and quality testing including estimation of building water use, water-saving fixtures, landscape water demand, rainwater-harvesting potential and treated-wastewater reuse; and GRIHA Water Positive Certification consulting, audit and certification. Earlier work includes pond rejuvenation with participatory community engagement, MY WATER (Mobilizing Youth for WATER conservation) Phases I and II, facility water audits for corporates such as Dabur India, and rainwater-harvesting design and feasibility studies. TERI has also publicly called for rainwater harvesting to be made mandatory across India and identified agriculture, forest and river conservation and domestic water-use efficiency as keys to India's water security. Mission and Goals lists enhancing conservation, utilisation of and access to water, including watershed management, as a core goal.

**Expected facts**

- Enhancing conservation, utilization of and access to water, including watershed management, is one of TERI's stated goals.
- TERI runs 'Water Resource Management through Spring and Catchment Rejuvenation in Uttarakhand'.
- TERI runs 'Air to Water as solution for rural water security'.
- TERI conducts water audits and quality testing covering building water use, water-saving fixtures, landscape water demand, rainwater-harvesting potential and reuse of treated wastewater and rainwater.
- TERI provides GRIHA Water Positive Certification consulting, audit and certification services, including water audits of existing buildings and complexes.
- TERI ran MY WATER (Mobilizing Youth for WATER conservation), including Phase II.
- TERI has publicly recommended making rainwater harvesting mandatory across India.
- TERI is preparing a State Specific Action Plan (SSAP) report for the water sector for Manipur.

**Expected entities**: MY WATER, GRIHA Water Positive Certification, Manipur SSAP

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `a264bf56-b146-483e-be4c-9262ac8b4001` | website / ongoing_projects | Water Resource Management through Spring and Catchment Rejuvenation in Uttarakhand for Improving Water Securit | https://teriin.org/project/water-resource-management-through-spring-and-catchment-rejuvenation-uttarakhand-improving |
| `0ade666b-2390-4bc7-bad1-c5668b819c9f` | website / ongoing_projects | Air to Water as solution for rural water security | https://teriin.org/project/air-water-solution-rural-water-security |
| `69358ff1-4b2f-47a8-bdce-01d5ba6aa794` | website / ongoing_projects | Environment, Climate and Water Security: Water Security and Climate Adaptation in Rural India (WASCA) | https://teriin.org/project/environment-climate-and-water-security-water-security-and-climate-adaptation-rural-india |
| `22973c65-87dc-4c5c-aa4a-c2a248efce69` | website / ongoing_projects | Preparation of State Specific Action Plan (SSAP) Report for Water Sector for the State of Manipur | https://teriin.org/project/preparation-state-specific-action-plan-ssap-report-water-sector-state-manipur |
| `3625b53b-5299-43c4-9e55-06bbe3aab259` | website / services | Multidisciplinary research on natural resource conservation |  |
| `512bf0b0-01b9-4d38-8547-d894ffef2f43` | website / services | Water Positive Certification - Consulting, Audit and Certification Services |  |
| `7b06dc9b-2597-4939-8e90-44cdb2cd1ebc` | website / page | Water Positive Certification - Consulting, Audit and Certification Services | https://teriin.org/services/habitat/water-positive-certification |
| `214fd71e-5aaf-4c6d-ba76-5a2dc19feb83` | website / completed_projects | Water Conservation through Rejuvenation of Pond with Participatory Community Engagement | https://teriin.org/project/water-conservation-through-rejuvenation-pond-participatory-community-engagement |
| `6c2f5794-d439-4949-b265-c3db444afd05` | website / completed_projects | MY WATER (Mobilizing Youth for WATER conservation) - Phase II | https://teriin.org/project/my-water-mobilizing-youth-water-conservation-phase-ii |
| `73b46dd3-e06c-487a-914e-2268e1d9b049` | website / completed_projects | Mobilizing youth for water conservation (MY WATER) | https://teriin.org/project/mobilizing-youth-water-conservation-my-water |
| `ec2deb3f-a6bd-4c0f-adea-10b81d42dc90` | website / completed_projects | Facility Water Audit of select unit of Dabur India Limited to identify water conservation measures | https://teriin.org/project/facility-water-audit-select-unit-dabur-india-limited-identify-water-conservation-measures |
| `a7a8e2b8-bcfc-4c06-88f4-78d7272a1e44` | website / press_release | Make rainwater harvesting mandatory across India | https://teriin.org/press-release/make-rainwater-harvesting-mandatory-across-india |
| `26de79ee-de9f-42f2-9e94-3bb00a784445` | website / press_release | Agriculture, forest and river conservation, domestic water use efficiency key to India's water security: Praka | https://teriin.org/press-release/agriculture-forest-and-river-conservation-domestic-water-use-efficiency-key-indias |

---

### Q063 - What innovative water management solutions is TERI researching?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's innovative water-management solutions: TADOX (TERI Advanced Oxidation Technology), a patented end-to-end treatment for industrial wastewater, mixed streams with untreated sewage and municipal wastewater with high colour and COD - commercialised through a licence agreement with Dew Projects and Chemicals (2023) and a partnership with Ion Exchange India (2024), with a policy brief on integrating TADOX to achieve net zero in textile wastewater treatment; fly-ash-based ceramic membrane filters in submerged membrane bioreactors, cheaper than commercial membranes and enabling decentralised on-site industrial-wastewater reuse; the NMCG-TERI Centre of Excellence on Water Reuse (NTCoE), the first of its kind, launched in December 2021; a hydropower forecasting system framework with a pilot; an Integrated River Pollution Management Framework for the Yamuna and Musi river basins; and 'Air to Water' for rural water security. TERI also runs the Water Sustainability Awards and a TERI-Bisleri collaboration on water credits and water stewardship.

**Expected facts**

- TADOX (TERI Advanced Oxidation Technology) is a patented comprehensive wastewater treatment technology offering end-to-end treatment of industrial wastewater, mixed streams with untreated sewage, and municipal wastewater with high colour and COD.
- TERI signed a licence agreement with Dew Projects and Chemicals Pvt Ltd for TADOX commercialisation (2023) and partnered with Ion Exchange India Ltd on TADOX (2024).
- TERI published a policy brief on integrating TADOX technology to achieve net zero in textile wastewater treatment.
- TERI demonstrated fly-ash-based ceramic membrane filters in submerged membrane bioreactors, cheaper than commercially available membranes and enabling decentralised on-site industrial wastewater reuse.
- NMCG and TERI launched the first-of-its-kind Centre of Excellence on Water Reuse (NTCoE) in December 2021.
- TERI is developing a hydropower forecasting system framework with a pilot project and an Integrated River Pollution Management Framework for the Yamuna and Musi river basins.
- TERI runs the Water Sustainability Awards (5th edition, 2026) and collaborates with Bisleri on water credits and sustainable water stewardship.

**Expected entities**: TADOX, ceramic membrane bioreactor, NMCG-TERI Centre of Excellence on Water Reuse (NTCoE), Dew Projects and Chemicals, Ion Exchange India, Bisleri

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d604f23f-cbaa-4c0f-9f6c-3c370f207e0c` | website / page | TERI's enhanced acidification and methanation technology | https://teriin.org/technology/teri-enhanced-acidification-and-methanation-technology |
| `687e4d39-90d3-4d85-8b6b-e9e3254aca6e` | website / page | Advanced wastewater treatment made affordable | https://teriin.org/technology/advanced-wastewater-treatment-made-affordable |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `68bfae3b-a24e-480c-a0a2-19ffc451ada8` | website / policy_brief | TERI Advanced Oxidation Technology (TADOX) to treat textile and dyeing wastewater, achieve zero liquid dischar | https://teriin.org/policy-brief/teri-advanced-oxidation-technology-tadox-treat-textile-and-dyeing-wastewater-achieve |
| `04fa5b91-c8d1-4226-8eb7-35a16bb6a9ac` | website / policy_brief | Integration of TADOX® technology to achieve net zero in textile wastewater treatment: Policy recommendations b | https://teriin.org/policy-brief/integration-tadoxr-technology-achieve-net-zero-textile-wastewater-treatment-policy |
| `106b039c-4b56-4854-89a1-b3ed372b53d7` | website / press_release | TERI and Dew Projects and Chemicals Pvt Ltd. sign a License Agreement for the commercialization of TERI’s pate | https://teriin.org/press-release/teri-and-dew-projects-and-chemicals-pvt-ltd-sign-license-agreement-commercialization |
| `be2a0c8f-23b1-4446-ad29-773e8034f103` | website / press_release | TERI and Ion Exchange India Ltd. come together to revolutionize Wastewater Treatment with TADOX® Technology | https://teriin.org/press-release/teri-and-ion-exchange-india-ltd-come-together-revolutionize-wastewater-treatment |
| `6b60fe32-9f02-456f-abf9-288ca7bd132c` | website / press_release | NMCG and TERI come together to launch the first of its kind Centre of Excellence on Water Reuse | https://teriin.org/press-release/nmcg-and-teri-come-together-launch-first-its-kind-centre-excellence-water-reuse |
| `643ed757-3db2-4983-b175-53b432ba5835` | website / ongoing_projects | Development of a Hydropower Forecasting System Framework and Implementation of a Pilot Project for Hydropower  | https://teriin.org/project/development-hydropower-forecasting-system-framework-and-implementation-pilot-project-0 |
| `e72da863-c6c8-40e7-9258-b76a3ec572ae` | website / ongoing_projects | Developing Integrated River Pollution Management Framework for Yamuna and Musi River Basin | https://teriin.org/project/developing-integrated-river-pollution-management-framework-yamuna-and-musi-river-basin |
| `0ade666b-2390-4bc7-bad1-c5668b819c9f` | website / ongoing_projects | Air to Water as solution for rural water security | https://teriin.org/project/air-water-solution-rural-water-security |
| `fe40b32c-a26d-45ee-b4c7-ce79f73a851b` | website / press_release | TERI Honours Excellence in Sustainable Water Management at the 5th Water Sustainability Awards 2026 | https://teriin.org/press-release/teri-honours-excellence-sustainable-water-management-5th-water-sustainability-awards |
| `a1ddc675-121e-4320-9acc-1a229d8d3a7e` | website / page | Outlook Business highlights TERI-Bisleri Collaboration on Water Credits and Sustainable Water Stewardship in J | https://teriin.org/outlook-business-highlights-teri-bisleri-collaboration-on-water-credits-and-sustainable-water-stewardship |

---

### Q064 - What services and research does TERI offer on wastewater treatment and reuse?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI offers both research and services on wastewater treatment and reuse. Technologies: TADOX (patented advanced oxidation, commercialised via Dew Projects and Chemicals and Ion Exchange India) and fly-ash ceramic membrane filters in submerged membrane bioreactors for decentralised reuse. Institutional platform: the NMCG-TERI Centre of Excellence on Water Reuse (NTCoE). Projects and research: 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and peri-urban areas in India'; acceptability of reclaimed municipal wastewater in cities (India's National Capital Region); microplastics in wastewater treatment plants; photocatalytic treatment of textile and dyeing wastewater at pilot scale; a Policy Brief on Net Zero in Textile Wastewater Treatment; and monitoring of community wastewater for early signalling of COVID-19 spread. Capacity building: an Online Training and Capacity Building (OTCB) Certificate Programme on developing treated wastewater reuse, plus events on wastewater treatment and reuse challenges and solutions in India and an annual international conference on advancing circular economy and water reuse. Service line: water audits and quality testing with recommendations on reuse and recycling of treated wastewater.

**Expected facts**

- TADOX is TERI's patented advanced-oxidation wastewater treatment technology, commercialised via Dew Projects and Chemicals and a partnership with Ion Exchange India.
- TERI demonstrated fly-ash ceramic membrane filters in submerged membrane bioreactors, enabling decentralised on-site treatment and reuse of industrial wastewater.
- The NMCG-TERI Centre of Excellence on Water Reuse (NTCoE) is TERI's institutional platform for water reuse.
- TERI runs 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and peri-urban areas in India'.
- TERI researched the acceptability of reclaimed municipal wastewater in cities using evidence from India's National Capital Region.
- TERI published a Policy Brief on Net Zero in Textile Wastewater Treatment and pilot-scale photocatalytic treatment research for textile and dyeing wastewater.
- TERI ran an Online Training and Capacity Building (OTCB) Certificate Programme on developing treated wastewater reuse.
- TERI monitored community wastewater for early signalling of COVID-19 spread.

**Expected entities**: TADOX, NTCoE, OTCB Certificate Programme, ceramic membrane bioreactor

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `687e4d39-90d3-4d85-8b6b-e9e3254aca6e` | website / page | Advanced wastewater treatment made affordable | https://teriin.org/technology/advanced-wastewater-treatment-made-affordable |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `6b60fe32-9f02-456f-abf9-288ca7bd132c` | website / press_release | NMCG and TERI come together to launch the first of its kind Centre of Excellence on Water Reuse | https://teriin.org/press-release/nmcg-and-teri-come-together-launch-first-its-kind-centre-excellence-water-reuse |
| `3029c6e2-8c33-403e-a41d-fb05e9f16e04` | website / ongoing_projects | Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and peri-urban area | https://teriin.org/project/unlocking-wastewater-treatment-water-re-use-and-resource-recovery-opportunities-urban-and-0 |
| `1e79db9f-6641-4a9c-b9bf-307998a58f5a` | website / research_papers | Acceptability of reclaimed municipal wastewater in cities: evidence from India’s National Capital Region | https://teriin.org/research-paper/acceptability-reclaimed-municipal-wastewater-cities-evidence-indias-national-capital |
| `96017abd-a4ef-4a00-a738-fa107f75f441` | website / research_papers | Study of occurrence, abundance, and characterization of microplastics in wastewater treatment plant in New Del | https://teriin.org/research-paper/study-occurrence-abundance-and-characterization-microplastics-wastewater-treatment |
| `884e7e4f-66d8-4402-acbc-2d6ef8cc502b` | website / research_papers | Novel pilot scale photocatalytic treatment of textile & dyeing industry wastewater to achieve process water qu | https://teriin.org/research-paper/novel-pilot-scale-photocatalytic-treatment-textile-dyeing-industry-wastewater-0 |
| `239202b4-5ae1-44de-a3ae-b266ddfc162a` | pdf_attachment / policy_brief | Policy Brief on Net Zero in Textile Wastewater Treatment | https://teriin.org/policy-brief/integration-tadoxr-technology-achieve-net-zero-textile-wastewater-treatment-policy |
| `91a23556-09b0-4f3b-9e99-bce615a25f21` | website / events | Online Training and Capacity Building (OTCB) Certificate Programme: Developing Treated Wastewater Reuse Facili | https://teriin.org/event/online-training-and-capacity-building-otcb-certificate-programme-developing-treated |
| `c302f95d-e408-4386-ab15-7fa25975fa3d` | website / events | Wastewater Treatment and Reuse: Challenges and Solutions in India | https://teriin.org/event/wastewater-treatment-and-reuse-challenges-and-solutions-india |
| `fee2380b-cde7-4ed3-b6f0-d200c8fa060f` | website / events | 1st Annual Meet & International Conference on Advancing Circular Economy and Water Reuse | https://teriin.org/event/1st-annual-meet-international-conference-advancing-circular-economy-and-water-reuse |
| `3625b53b-5299-43c4-9e55-06bbe3aab259` | website / services | Multidisciplinary research on natural resource conservation |  |
| `10572175-77da-46c2-ae44-18ac79cd0185` | pdf_attachment / policy_brief | Policy Bulletin - Monitoring of community wastewater for early signalling the spread of COVID-19 in Chennai Ci | https://teriin.org/policy-brief/monitoring-community-wastewater-early-signalling-spread-covid-19-chennai-city |

---

### Q065 - How does TERI support climate-smart agriculture?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports climate-smart agriculture by promoting climate-smart practices, applying biofertilizers and nano-fertilizers, enhancing soil and water productivity, and using biotechnological interventions to build resilient farming systems. Concrete work: nanofertilizers developed by TERI's Sustainable Agriculture Programme explicitly for climate-smart agriculture, and biogenic nanotechnology innovations in climate-smart and sustainable farming; the project 'Inclusion of Climate Smart Agriculture Approaches in existing Agricultural Practices and Capacity Building'; research on 'Financing Climate-Smart Agriculture for Sustainable Agri-Food Systems'; integrated climate-smart agricultural practices with the Government of Maharashtra; mycorrhizal biofertiliser platforms advancing soil health; the TERI-CFCL Centre of Excellence for Advanced and Sustainable Agriculture Solutions; smart solar-powered irrigation and pesticide management in Karnataka; and TRISHA/Seeds of Hope work in Supi (Uttarakhand) that shifted farmers to low-water herb and aromatic crops and revived millets and pulses (reported 38% increase in millet production and 45% in pulses from an 82-landrace live seed bank).

**Expected facts**

- TERI supports resilient farming systems by promoting climate-smart practices, applying biofertilizers and nano-fertilizers, enhancing soil and water productivity, and using biotechnological interventions.
- TERI's Sustainable Agriculture Programme developed nanofertilizers explicitly for achieving climate-smart agriculture.
- TERI runs the project 'Inclusion of Climate Smart Agriculture Approaches in existing Agricultural Practices and Capacity Building'.
- TERI published research on 'Financing Climate-Smart Agriculture for Sustainable Agri-Food Systems'.
- TERI implemented integrated climate-smart agricultural practices with the Government of Maharashtra.
- TERI's TRISHA initiative at Supi (Nainital, Uttarakhand, since 2003) shifted farmers to low-water herb and aromatic crops and created a live seed bank of about 82 Kumaon landraces, reporting a 38% increase in millet production and 45% in pulses.
- TERI runs smart solar-powered irrigation and pesticide management for sustainable agriculture in Karnataka.

**Expected entities**: nanofertilizers, TRISHA, Seeds of Hope, TERI-CFCL Centre of Excellence, Government of Maharashtra

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `736c7026-5244-4a56-b3ff-8577bf798944` | website / article | Nanofertilizers developed by TERI's Sustainable Agriculture Program for achieving climate-smart agriculture ar | https://teriin.org/article/nanofertilizers-developed-teris-sustainable-agriculture-program-achieving-climate-smart |
| `78d36f66-1da7-453b-8c35-a24859a5c1b3` | website / article | TERI team has developed nanofertilizers for climate smart agriculture | https://teriin.org/article/teri-team-has-developed-nanofertilizers-climate-smart-agriculture |
| `ca7ba199-710c-487e-a4ff-a69b9c0455f7` | website / article | Nano steps towards Climate Smart Agriculture | https://teriin.org/article/nano-steps-towards-climate-smart-agriculture |
| `b2827f5a-ae1c-47b5-895b-257c1336f017` | website / page | Innovations in Climate-Smart and Sustainable Farming through Nanotechnology | https://teriin.org/technologies/innovations-in-climate-smart-and-sustainable-farming-through-nanotechnology |
| `7593f713-7603-4986-be41-89d7f3512ba3` | website / ongoing_projects | Inclusion of Climate Smart Agriculture Approaches in existing Agricultural Practices and Capacity Building (MA | https://teriin.org/project/inclusion-climate-smart-agriculture-approaches-existing-agricultural-practices-and-capacity |
| `8daaf4a7-e449-493a-b2b2-82ba316a3e62` | website / research_papers | Financing Climate-Smart Agriculture for Sustainable Agri-Food Systems | https://teriin.org/research-paper/financing-climate-smart-agriculture-sustainable-agri-food-systems |
| `21102beb-b5ff-4d18-8ede-62354fb5bb2a` | website / ongoing_projects | TERI’s Mycorrhizal Platforms: Advancing Soil Health and Sustainable Agriculture | https://teriin.org/project/teris-mycorrhizal-platforms-advancing-soil-health-and-sustainable-agriculture |
| `d1dda10c-8168-43c7-b364-fa3a6f4d661f` | website / page | TERI-CFCL Centre of Excellence (CoE) for Advanced and Sustainable Agriculture Solutions | https://teriin.org/TERI-CFCL-centre-of-excellence-CoE |
| `b8fc9a99-908d-45cc-a3b3-4809e605b15f` | website / completed_projects | Smart Solar-Powered Irrigation and Pesticide Management for Sustainable Agriculture in Karnataka, India | https://teriin.org/project/smart-solar-powered-irrigation-and-pesticide-management-sustainable-agriculture-karnataka |
| `5776adb9-6186-44d6-be43-8a9189767433` | website / page | Seeds of Hope | https://teriin.org/seeds-of-hope |
| `inbody:0e41da3dbea8c5135d3a22191ed94b72670c9afc` | pdf_attachment / page | Annual Reports | https://teriin.org/annual-reports |

---

### Q066 - What research is TERI conducting on food systems sustainability?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's food-systems work links nutrition security, agri-food sustainability and bioresources. Documented lines: the FOLU (Food and Land Use Coalition) India engagement with farmers to improve nutrition; project SAHeLEE on growing resilience in India's food systems; the Global Center for Food Systems Innovation; research on 'Financing Climate-Smart Agriculture for Sustainable Agri-Food Systems'; malnutrition and alternate-livelihood interventions for Scheduled Tribe communities (including Mokhada and Palghar, Maharashtra) and Nutri-gardens with Kisan Seva Kendras; a digital library dedicated to nutrition security (2018); algae-based solutions for poultry, aquafeeds and cattle nutrition; and nanotechnology-for-sustainable-agriculture conferences (NANOFORAGRI). TERI's Western Regional Centre states a dedicated nutrition-security programme, including the 'Canteen for Teen' urban campaign and over a decade of work in Palghar district. TERI's stated goal set includes enabling sustainable food production and nutritional security through quality planting material, bio-based agricultural inputs and crop diversification.

**Expected facts**

- TERI's stated goals include enabling sustainable food production and nutritional security through quality planting material, bio-based agricultural inputs and crop diversification.
- TERI engages farmers to improve nutrition through FOLU India.
- TERI runs project SAHeLEE on growing resilience in India's food systems.
- TERI hosted a Global Center for Food Systems Innovation.
- TERI's Western Regional Centre (Mumbai) runs a nutrition-security programme, including the 'Canteen for Teen' initiative under an eco-city project and over a decade of nutrition interventions in Palghar district, rural Maharashtra.
- TERI runs interventions to address malnutrition and create alternate livelihoods for Scheduled Tribe communities, including in Mokhada, Maharashtra.
- TERI launched a first-of-its-kind digital library dedicated to nutrition security (2018).
- TERI advances algae-based solutions for poultry, aquafeeds and cattle nutrition.

**Expected entities**: FOLU India, SAHeLEE, Global Center for Food Systems Innovation, Canteen for Teen, Palghar, NANOFORAGRI

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `1f2d085c-58cc-4193-85b2-8b29f86ff86a` | website / page | Our Research Focus | https://teriin.org/Our-Research-Focus |
| `dfc646b9-636f-48bc-8537-23770997a0cc` | website / article | Connecting with the Community: How FOLU India engages farmers to improve nutrition | https://teriin.org/article/connecting-community-how-folu-india-engages-farmers-improve-nutrition |
| `ec9056b2-2cf1-4492-ad69-9f39d3aa69b9` | website / article | Growing resilience in India’s food systems: Introducing project SAHeLEE | https://teriin.org/article/growing-resilience-indias-food-systems-introducing-project-sahelee |
| `b03126e9-94d6-4547-a5ad-937016e6c378` | website / completed_projects | Global Center for Food Systems Innovation | https://teriin.org/project/global-center-food-systems-innovation |
| `8daaf4a7-e449-493a-b2b2-82ba316a3e62` | website / research_papers | Financing Climate-Smart Agriculture for Sustainable Agri-Food Systems | https://teriin.org/research-paper/financing-climate-smart-agriculture-sustainable-agri-food-systems |
| `4a66d21b-22bc-4e29-ac5b-5d0ae311437a` | website / ongoing_projects | Innovative interventions to address malnutrition and enhance the livelihood of ST communities | https://teriin.org/project/innovative-interventions-address-malnutrition-and-enhance-livelihood-st-communities |
| `0b74e6af-8745-4ee9-89ce-1af82f433208` | website / completed_projects | Implementation of field activities towards addressing malnutrition and creating alternate livelihood opportuni | https://teriin.org/project/implementation-field-activities-towards-addressing-malnutrition-and-creating-alternate |
| `6e5643a7-d1b0-4438-86ea-62796ab27191` | website / events | TERI Conducts Training Workshop to Empower ST Communities by Combating Malnutrition in Mokhada, Palghar | https://teriin.org/event/teri-conducts-training-workshop-empower-st-communities-combating-malnutrition-mokhada-palghar |
| `768889dc-5bce-493d-8144-2042b2536560` | website / press_release | TERI launches first-of-its-kind digital library dedicated to nutrition security | https://teriin.org/press-release/teri-launches-first-its-kind-digital-library-dedicated-nutrition-security |
| `ab1bbea2-f85d-45a6-9ae1-0655fbdeaad3` | website / ongoing_projects | TERI Advances Algae-Based Solutions for Poultry, Aquafeeds & Cattle Nutrition | https://teriin.org/project/teri-advances-algae-based-solutions-poultry-aquafeeds-cattle-nutrition |
| `739f7d96-0d59-4c68-8221-41d1941d9ad6` | website / events | 4th International Conference on NANOFORAGRI 2020 - Application of Nanotechnology for Sustainable, Productive a | https://teriin.org/event/4th-international-conference-nanoforagri-2020-application-nanotechnology-sustainable |
| `e4e6bccc-ea4d-45ee-82bd-391a57cabb7c` | website / completed_projects | Introducing the concept of Nutri-gardens to Address Rural Malnutrition by Involving Kisan Seva Kendras | https://teriin.org/project/introducing-concept-nutri-gardens-address-rural-malnutrition-involving-kisan-seva-kendras |

---

### Q067 - How does TERI work with local communities on forest conservation?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI works with local communities on forest conservation through participatory forest management, forest-based livelihoods and benefit-sharing at community level - the stated scope of its 'Capacity building for management of natural resources' service. Concrete work: the Assam Project on Forest and Biodiversity Conservation (APFBCS); a cluster of agroforestry-plus-carbon-finance projects that route benefits to farmers and Farmer Producer Organisations (Saharanpur voluntary carbon market project with FPOs, Kanpur Forest Circle, Gorakhpur, Aligarh, Gujarat/SHBVM); a GEF Small Grants Programme India OP7 publication on community-led action launched on Biological Diversity Day 2026; policy work on the Minimum Support Price for Minor Forest Produce and its sustainable harvesting, noting over 300 million people depend on forests for livelihoods and citing PESA 1996 and the Forest Rights Act 2006; a study on the implementation of compensatory afforestation in India; valuation of forest ecosystem services in Chhattisgarh; and forest-fire management and air quality work in the Himalaya with ICIMOD and NTNC. TERI states it strives for policy mainstreaming of community-led environmental management and conservation efforts.

**Expected facts**

- TERI works on institutional issues of participatory forest management and has major interests in forest-based livelihoods and benefit-sharing at the community level.
- TERI implemented the Assam Project on Forest and Biodiversity Conservation (APFBCS).
- TERI runs agroforestry and carbon-finance projects that channel benefits to farmers and Farmer Producer Organisations in Saharanpur, Kanpur Forest Circle, Gorakhpur, Aligarh and Gujarat.
- TERI launched a GEF Small Grants Programme India OP7 publication on community-led action on Biological Diversity Day 2026.
- TERI's policy work on Minimum Support Price of Minor Forest Produce states that more than 300 million people derive full or partial livelihood and sustenance from forests, that the MFP sector is India's largest unorganized sector, and that forest dwellers are legally empowered with ownership and governance of MFP through PESA, 1996 and the Forest Rights Act, 2006; TERI's study established an MSP methodology for 12 MFPs from 12,000 household surveys, 1,200 work studies and over 100 focus group discussions.
- TERI studied the implementation of compensatory afforestation in India and valued forest ecosystem services in Chhattisgarh.
- TERI states it strives towards policy mainstreaming of community-led environmental management and conservation efforts.

**Expected entities**: APFBCS, Farmer Producer Organisations, GEF Small Grants Programme India OP7, Minor Forest Produce MSP, Forest Rights Act 2006, ICIMOD, NTNC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c2d42e8b-4b6e-451c-9ddf-1d1f653b2b5f` | website / services | Capacity building for management of natural resources |  |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `0bf4c8b9-9c0a-412b-849b-f8b669507d21` | website / completed_projects | Assam Project on Forest and Biodiversity Conservation (APFBCS) | https://teriin.org/project/assam-project-forest-and-biodiversity-conservation-apfbcs |
| `824a4f1b-f3b8-43f3-842a-7126bd0105c3` | website / ongoing_projects | Developing a Voluntary Carbon Market Project with FPOs for Agroforestry Plantation in Saharanpur District, Utt | https://teriin.org/project/developing-voluntary-carbon-market-project-fpos-agroforestry-plantation-saharanpur-district |
| `64c01001-2296-4a33-a6d2-4e336c966407` | website / ongoing_projects | Developing Voluntary Carbon Market Projects for Agroforestry Plantations in Kanpur Forest Circle, Uttar Prades | https://teriin.org/project/developing-voluntary-carbon-market-projects-agroforestry-plantations-kanpur-forest-circle |
| `870aa800-c398-4678-8a4a-08c24edaa911` | website / ongoing_projects | Sustainable Livelihood through Carbon Finance and Agroforestry in Gorakhpur | https://teriin.org/project/sustainable-livelihood-through-carbon-finance-and-agroforestry-gorakhpur |
| `90e24426-1d56-4f13-afda-46bd0916799a` | website / ongoing_projects | Empowering Rural Livelihoods through Agroforestry in Aligarh | https://teriin.org/project/empowering-rural-livelihoods-through-agroforestry-aligarh |
| `2e6e10ea-8a82-4b7c-b143-900700301cac` | website / ongoing_projects | ENHANCING LIVELIHOODS OF FARMERS IN GUJARAT THROUGH AGROFORESTRY PLANTATIONS BY SHBVM | https://teriin.org/project/enhancing-livelihoods-farmers-gujarat-through-agroforestry-plantations-shbvm |
| `a07d981b-dc88-41a9-840d-8ce3961d7a1a` | website / press_release | Biological Diversity Day 2026: TERI Launches New GEF-SGP India OP7 Publication on Community-Led Coastal Biodiv | https://teriin.org/press-release/biological-diversity-day-2026-teri-launches-new-gef-sgp-india-op7-publication |
| `727e791c-f6a5-47be-aa90-ce7828ba49b5` | website / policy_brief | Study on Implementation of Compensatory Afforestation in India | https://teriin.org/policy-brief/study-implementation-compensatory-afforestation-india |
| `e2ccb4f7-b348-4dc1-993a-b8aa76d20b14` | website / completed_projects | Valuation of Ecosystem Services of Forest Ecosystem in Chhattisgarh and its potential contribution to State Gr | https://teriin.org/project/valuation-ecosystem-services-forest-ecosystem-chhattisgarh-and-its-potential-contribution |
| `7ac1eb9f-a72c-48d6-9e98-89ce8a6783e7` | website / completed_projects | Comprehensive Study on Solutions for Forest Fire Management and Air Quality Improvement in the HKH Region | https://teriin.org/project/comprehensive-study-solutions-forest-fire-management-and-air-quality-improvement-hkh-region |
| `00d5790d-09eb-40e8-ae8f-8fdad3c306f4` | website / policy_brief | Minimum Support Price of Minor Forest Produce (MFP) and Its Sustainable Harvest: A Social Safety Measure for M | https://teriin.org/policy-brief/minimum-support-price-minor-forest-produce-mfp-and-its-sustainable-harvest-social |
| `aaf55d78-b81b-408a-a287-337feb531c3f` | pdf_attachment / policy_brief | Policy brief - Minimum Support Price of Minor Forest Produce (MFP) and Its Sustainable Harvest | https://teriin.org/policy-brief/minimum-support-price-minor-forest-produce-mfp-and-its-sustainable-harvest-social |

**Notes**: JUDGEMENT CORRECTION: the MFP/MSP fact originally cited only the /policy page and the natural-resources capacity-building service node, neither of which contains it. An earlier concern that this fact came from an LLM-generated documents_enrichment abstract was CHECKED AND DISPROVED: the statements are present verbatim in real Qdrant chunk text of the MFP policy brief (website node 00d5790d-09eb-40e8-ae8f-8fdad3c306f4 and PDF aaf55d78-b81b-408a-a287-337feb531c3f). Wording tightened to the source's own phrasing.

---

### Q068 - What is TERI's role in watershed management projects?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's role in watershed management combines implementation support, monitoring/evaluation and capacity building. Its stated goal set includes enhancing conservation, utilisation of and access to water including watershed management. Current work: process monitoring under REWARD (Rejuvenating Watersheds for Agricultural Resilience through Innovative Development), including hosting the 3rd Annual REWARD Stakeholder Workshop in Karnataka on strengthening watershed governance; MEL&D (monitoring, evaluation, learning and documentation) services for the CEPMIZ Watershed Development Programme; and DRO/TSP support for implementation of a Watershed Development Project. Capacity building: training on Climate Resilient Integrated Watershed Management delivered with the State Level Nodal Agency (2025) and earlier workshops on the Integrated Watershed Management Programme. Analysis: the policy brief 'Food and Land Resources: Incorporating Watershed-Based Approaches for Better Sustainability' and reporting that Karnataka adopted a new approach to enhance the impact of its watershed programme.

**Expected facts**

- Enhancing conservation, utilization of and access to water, including watershed management, is one of TERI's stated goals.
- TERI conducts process monitoring under REWARD (Rejuvenating Watersheds for Agricultural Resilience through Innovative Development) and hosted the 3rd Annual REWARD Stakeholder Workshop in Karnataka on strengthening watershed governance.
- TERI provides MEL&D services for the CEPMIZ Watershed Development Programme.
- TERI provides DRO and TSP support for implementation of a Watershed Development Project.
- TERI and the State Level Nodal Agency (SLNA) hosted training on Climate Resilient Integrated Watershed Management (2025).
- TERI published the policy brief 'Food and Land Resources: Incorporating Watershed-Based Approaches for Better Sustainability'.

**Expected entities**: REWARD, CEPMIZ Watershed Development Programme, SLNA, Karnataka

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `040491c8-07dc-44f3-a141-a67246c44d08` | website / ongoing_projects | Process Monitoring under Rejuvenating Watersheds for Agricultural Resilience through Innovative Development (R | https://teriin.org/project/process-monitoring-under-rejuvenating-watersheds-agricultural-resilience-through-0 |
| `82750a29-285c-48cc-95b1-5353661625ad` | website / ongoing_projects | Process Monitoring under Rejuvenating Watersheds for Agricultural Resilience through Innovative Development (R | https://teriin.org/project/process-monitoring-under-rejuvenating-watersheds-agricultural-resilience-through-innovative |
| `cb3ab614-7ce3-4778-99e6-d59bde150f5d` | website / events | Strengthening Watershed Governance: TERI Hosts 3rd Annual REWARD Stakeholder Workshop in Karnataka | https://teriin.org/event/strengthening-watershed-governance-teri-hosts-3rd-annual-reward-stakeholder-workshop |
| `7018c2c9-79ff-4518-85cb-bdf87e9823e8` | website / ongoing_projects | MEL&D Services for CEPMIZ Watershed Development Programme | https://teriin.org/project/meld-services-cepmiz-watershed-development-programme |
| `ed1496ea-9359-433e-84c6-ce1ee4217ba3` | website / completed_projects | DRO and TSP for Implementation of Watershed Development Project | https://teriin.org/project/dro-and-tsp-implementation-watershed-development-project |
| `c2a3ebd9-86ff-4d7b-ba06-d7c0089fd97e` | website / press_release | TERI Hosts Training on Climate Resilient Integrated Watershed Management in Collaboration with SLNA, Governmen | https://teriin.org/press-release/teri-hosts-training-climate-resilient-integrated-watershed-management-collaboration |
| `b84aee6d-9de5-4ea8-9c89-c13caaeac5df` | website / press_release | Empowering Practitioners for Climate Resilience: TERI and SLNA Host Training on Integrated Watershed Managemen | https://teriin.org/press-release/empowering-practitioners-climate-resilience-teri-and-slna-host-training-integrated |
| `53f7bd72-fcb9-42e3-8336-1733575e2705` | website / events | Training on Climate Resilient Integrated Watershed Management | https://teriin.org/event/training-climate-resilient-integrated-watershed-management |
| `254fa43b-c3ae-4ef7-8c79-83e224ca09c0` | website / policy_brief | Food and Land Resources: Incorporating Watershed-Based Approaches for Better Sustainability-Productivity Balan | https://teriin.org/policy-brief/food-and-land-resources-incorporating-watershed-based-approaches-better-sustainability |
| `9437401d-fb78-4828-83d7-0ba95ee70483` | website / article | Karnataka adopts new approach to enhance impact of watershed programme | https://teriin.org/article/karnataka-adopts-new-approach-enhance-impact-watershed-programme |
| `5d8c7223-a9fe-419f-b45b-c80c17d1e3b1` | website / events | Workshop on 'Integrated Watershed Management Programme' | https://teriin.org/event/workshop-integrated-watershed-management-programme |

---

### Q069 - What biodiversity conservation programmes does TERI implement?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's biodiversity-conservation programmes: the Assam Project on Forest and Biodiversity Conservation (APFBCS); People's Biodiversity Register work, including a PBR and City Biodiversity Index for Panaji and PBR preparation for Zilla and Taluk Panchayats; strengthening the linkage of Biodiversity Management Committees with community-participation institutions; preparing state biodiversity strategy and action plans and work on access and benefit sharing in biodiversity (stated on the Policy page); a GEF Small Grants Programme India OP7 publication on community-led conservation (2026); carbon-stock and biodiversity assessment of corporate plantations (a service line, plus a Chemfab Alkalis case study); coastal and marine biodiversity work through the TERI-Centre of Excellence for Coastal Studies and Resource Management, the Coastal Ecology and Marine Resources Center and a G20 marine-biodiversity policy brief; and GIS/machine-learning assessment of forest and biodiversity vulnerability under climate stress. Enhancing ecosystem services, especially in forestry and biodiversity, is one of TERI's stated goals.

**Expected facts**

- Enhancing ecosystem services, especially in forestry and biodiversity, is one of TERI's stated goals.
- TERI implemented the Assam Project on Forest and Biodiversity Conservation (APFBCS).
- TERI prepared a People's Biodiversity Register (PBR) and City Biodiversity Index (CBI) for Panaji and PBRs for Zilla and Taluk Panchayats.
- TERI worked on linking Biodiversity Management Committees (BMCs) with institutions of community participation.
- TERI has worked with several states to prepare biodiversity strategy and action plans and has assisted on access and benefit sharing in biodiversity.
- TERI offers a service estimating carbon sink and biodiversity co-benefits of company plantations, and evaluated carbon stock and biodiversity dynamics in Chemfab Alkalis Limited's plantations.
- TERI works on marine and coastal biodiversity through the TERI-Centre of Excellence for Coastal Studies and Resource Management and the Coastal Ecology and Marine Resources Center (CEMRC), and published a policy brief on the G20's role in marine biodiversity.

**Expected entities**: APFBCS, People's Biodiversity Register, City Biodiversity Index, Biodiversity Management Committees, CoE-CSRM, CEMRC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `0bf4c8b9-9c0a-412b-849b-f8b669507d21` | website / completed_projects | Assam Project on Forest and Biodiversity Conservation (APFBCS) | https://teriin.org/project/assam-project-forest-and-biodiversity-conservation-apfbcs |
| `2ebbb7ba-3134-495d-bac4-80f9de7e0d0e` | website / ongoing_projects | People’s Biodiversity Register (PBR) and City Biodiversity Index (CBI) for the city of Panaji | https://teriin.org/project/peoples-biodiversity-register-pbr-and-city-biodiversity-index-cbi-city-panaji |
| `bdf6058e-43cf-4c71-9136-c6d33eb9f888` | website / ongoing_projects | Preparation of People Biodiversity Register for Zilla Panchayats and Taluk Panchayats levels | https://teriin.org/project/preparation-people-biodiversity-register-zilla-panchayats-and-taluk-panchayats-levels |
| `b262df5b-6148-4817-9f69-e2dd256191e4` | website / events | Linkages of Biodiversity Management Committees (BMCs) with institutions of community participation and Panchay | https://teriin.org/event/linkages-biodiversity-management-committees-bmcs-institutions-community-participation-and |
| `a07d981b-dc88-41a9-840d-8ce3961d7a1a` | website / press_release | Biological Diversity Day 2026: TERI Launches New GEF-SGP India OP7 Publication on Community-Led Coastal Biodiv | https://teriin.org/press-release/biological-diversity-day-2026-teri-launches-new-gef-sgp-india-op7-publication |
| `2ef2427a-1fdb-4398-9b73-2c4719ac38a4` | website / services | Carbon sequestration potential and biodiversity assessment |  |
| `928c4a33-addf-48b6-9490-8d73d8520865` | website / completed_projects | Evaluating Carbon Stock and Biodiversity Dynamics in Chemfab Alkalis Limited’s Plantations: A Comparative Stud | https://teriin.org/project/evaluating-carbon-stock-and-biodiversity-dynamics-chemfab-alkalis-limiteds-plantations |
| `abfa8cff-a8dc-41f3-8ad7-a5cd66bd3309` | website / policy_brief | G20's role in Marine Biodiversity | https://teriin.org/policy-brief/g20s-role-marine-biodiversity |
| `a5fcde1e-a569-4d4a-8570-4a95f00b1c94` | website / page | TERI-Centre of Excellence for Coastal Studies and Resource Management (CoE-CSRM) | https://teriin.org/TERI-centre-of-excellence-for-coastal-studies-and-resource-management |
| `fc72b1a0-5e63-49b0-8170-edc29381bcf9` | website / page | Coastal Ecology and Marine Resources Center (CEMRC) | https://teriin.org/coastal-ecology-and-marine-resources-center-cemrc |
| `28eeb229-b331-4889-ad05-368531ae6f82` | website / research_papers | GIS & Machine Learning Based Approaches to Assess Forest and Biodiversity Vulnerability Under Climate Stress:  | https://teriin.org/research-paper/gis-machine-learning-based-approaches-assess-forest-and-biodiversity-vulnerability |
| `0c58c947-b0e6-4e8a-85f4-62182966b5b5` | website / ongoing_projects | Sensitization Programs on Understanding Impact of Climate Change on Biodiversity and Ecosystem Services for Ec | https://teriin.org/project/sensitization-programs-understanding-impact-climate-change-biodiversity-and-ecosystem |

---

### Q070 - What nature-based solutions is TERI promoting?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `LOW` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI promotes nature-based solutions (NbS) chiefly for rural livelihoods, restoration and biological inputs. Evidence in the corpus: the article 'Nature-based solutions (NbS) for Rural Livelihoods'; the COP26 Charter of Actions virtual stakeholder roundtable on Nature-based Solutions; a press statement on the need to assess the potential of nature-based solutions and green technologies to facilitate green growth; 'Impact of Nature-based Innovative Biofertilizers on Agriculture'; and landscape restoration work presented as an NbS-type intervention (the Aravalli Green Wall Initiative, mangrove-ecosystem work in Goa, and the assessment of wetland restoration potential for climate-change mitigation). TERI's microbe-based technologies (mycorrhizal biofertilisers, Oilzapper, wasteland reclamation with mycorrhizal fungi) are its longest-running nature-based interventions.

**Expected facts**

- TERI published 'Nature-based solutions (NbS) for Rural Livelihoods'.
- TERI convened a COP26 Charter of Actions Virtual Stakeholder Roundtable on Nature-based Solutions.
- TERI stated the need to assess the potential of nature-based solutions and green technologies to facilitate green growth.
- TERI published 'Impact of Nature-based Innovative Biofertilizers on Agriculture'.
- TERI's nature-based interventions include mycorrhizal biofertilisers, Oilzapper microbial soil remediation and wasteland reclamation using mycorrhizal fungi.
- TERI works on landscape and ecosystem restoration including the Aravalli Green Wall Initiative, mangrove ecosystems in Goa, and assessing wetland restoration for climate-change mitigation.

**Expected entities**: nature-based solutions, Aravalli Green Wall Initiative, mangrove ecosystems in Goa

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `07e0123e-a093-4382-b40c-59e414ea7c75` | website / article | Nature-based solutions (NbS) for Rural Livelihoods | https://teriin.org/article/nature-based-solutions-nbs-rural-livelihoods |
| `1c501eec-f88c-45fe-b3f6-afbe577960a8` | website / events | COP26 Charter of Actions: Virtual Stakeholder Roundtable on Nature-based Solutions | https://teriin.org/event/cop26-charter-actions-virtual-stakeholder-roundtable-nature-based-solutions |
| `fe33deda-67ef-4f33-8878-d0e6122f6f01` | website / press_release | Need to assess the potential of nature-based solutions and green technologies to facilitate green recovery: Sh | https://teriin.org/press-release/need-assess-potential-nature-based-solutions-and-green-technologies-facilitate-green |
| `54eba398-a4b8-4a36-b0ad-55c380e4ce94` | website / article | Impact of Nature-based Innovative Biofertilizers on Agriculture | https://teriin.org/article/impact-nature-based-innovative-biofertilizers-agriculture |
| `67362d57-2345-4d19-982a-9a398c413c97` | website / events | Aravalli Green Wall Initiative: India’s Landscape Ecological Restoration Programme for Climate Resilience and  | https://teriin.org/event/aravalli-green-wall-initiative-indias-landscape-ecological-restoration-programme-climate |
| `ff509de9-87e5-4fe5-976b-4f23fd7e6d1f` | website / page | Mangrove ecosystems in Goa | https://teriin.org/mangrove-ecosystems-in-goa |
| `fe720546-2f55-4473-b5df-9bec6a0978ed` | website / events | Assessing the potential of wetland restoration for climate change mitigation | https://teriin.org/event/assessing-potential-wetland-restoration-climate-change-mitigation |
| `fc7e7a2e-8914-4ae8-b214-3246272f5333` | website / services | Technology for reclaming wastelands |  |
| `f387a567-cf91-4683-91ae-c431a037d49b` | website / services | Next generation technology to produce high-quality mycorrhiza |  |
| `44d366d7-953c-41cc-aafa-3425fb604cc4` | website / page | Oilzapper and Oilivorous-S | https://teriin.org/technology/oilzapper-and-oilivorous-s |

**Notes**: LOW confidence because TERI has no NbS programme page, centre or service line; the term appears in only ~5 TERI-authored items and the restoration/biofertiliser links are the gold-set author's grouping, not TERI's own framing. An answer that reports a formal 'NbS programme' should be marked unsupported.

---

### Q071 - What ecosystem restoration and land restoration initiatives are underway?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=current; requested_period=underway as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> Ecosystem- and land-restoration initiatives underway or recent: the Aravalli Green Wall Initiative, described as India's landscape ecological restoration programme for climate resilience (2026), with a WSDS 2026 track on Action for the Aravallis; an Ecological Restoration Project MoU signed with Hindustan Zinc Limited (June 2026); rejuvenation of HYPREP-remediated soil in Nkeleoken, Eleme LGA (Nigeria) using Oilzapper and Bio-NPK; RECAP4NDC work on financing Forest Landscape Restoration (including Gujarat and a forestry carbon-credit roadmap for Uttarakhand); the policy brief 'Biodiversity and Land Restoration in India'; a study on the implementation of compensatory afforestation in India; third-party evaluation of Haryana CAMPA works; and the wasteland-reclamation service using mycorrhizal fungi (successfully applied to fly-ash overburdens, alkali chlor-laden sites, distillery effluent discharge sites, phosphogypsum ponds, coal mines, red mud, saline and arid sites). TERI has also published recommendations to reverse land degradation in India and worked on the economics of desertification, land degradation and drought.

**Expected facts**

- The Aravalli Green Wall Initiative is described as India's landscape ecological restoration programme for climate resilience.
- TERI signed an MoU with Hindustan Zinc Limited for an Ecological Restoration Project (June 2026).
- TERI is rejuvenating HYPREP-remediated soil in Nkeleoken, Eleme LGA, using Oilzapper and Bio-NPK.
- TERI works on financing Forest Landscape Restoration under RECAP4NDC, including in Gujarat, and on a forestry carbon-credit roadmap for Uttarakhand.
- TERI published the policy brief 'Biodiversity and Land Restoration in India'.
- TERI's wasteland-reclamation technology using mycorrhizal fungi has been applied to fly-ash overburdens, alkali chlor-laden sites, distillery effluent discharge sites, phosphogypsum ponds, coal mines, red mud, and saline and arid sites.
- TERI recommended action points to reverse land degradation in India and studied the economics of desertification, land degradation and drought (DLDD).

**Expected entities**: Aravalli Green Wall Initiative, Hindustan Zinc Limited, RECAP4NDC, Oilzapper, CAMPA

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `67362d57-2345-4d19-982a-9a398c413c97` | website / events | Aravalli Green Wall Initiative: India’s Landscape Ecological Restoration Programme for Climate Resilience and  | https://teriin.org/event/aravalli-green-wall-initiative-indias-landscape-ecological-restoration-programme-climate |
| `89260965-2d11-4cbc-93f7-77abac14a033` | website / events | WSDS 2026 Thematic Track: Action for the Aravallis: Advancing Restoration, Resilience, and Inclusive Growth | https://teriin.org/event/wsds-2026-thematic-track-action-aravallis-advancing-restoration-resilience-and-inclusive |
| `502ae0eb-31a3-4bce-af9d-952f0e977e33` | website / events | Ecological Restoration Project: TERI signs MoU with Hindustan Zinc Limited | https://teriin.org/event/ecological-restoration-project-teri-signs-mou-hindustan-zinc-limited |
| `cae161ca-7cb6-47d8-831c-40b302f1f5c2` | website / completed_projects | Rejuvenation of HYPREP-Remediated Soil in Nkeleoken, Eleme LGA Through Oilzapper® and Bio-NPK-Based Soil Resto | https://teriin.org/project/rejuvenation-hyprep-remediated-soil-nkeleoken-eleme-lga-through-oilzapperr-and-bio-npk |
| `2242c11e-c3d2-4cc5-aa3a-76205619fa9e` | website / events | Financing Forest Landscape Restoration (FLR) under RECAP4NDC | https://teriin.org/event/financing-forest-landscape-restoration-flr-under-recap4ndc |
| `4878af34-7f92-4889-a26d-ba70308038cf` | website / events | Connecting Policy and Finance for Landscape Restoration in Gujarat under RECAP4NDC | https://teriin.org/event/connecting-policy-and-finance-landscape-restoration-gujarat-under-recap4ndc |
| `e4a68ac6-c2df-48b1-8af7-9b298444818b` | website / events | Building a Forestry Carbon Credit Roadmap for Uttarakhand under RECAP4NDC | https://teriin.org/event/building-forestry-carbon-credit-roadmap-uttarakhand-under-recap4ndc |
| `1a21d5f0-f0c9-4f34-8aa0-ed99343033c0` | website / policy_brief | Biodiversity and Land Restoration in India: A Narrative of India's Sustainability Efforts Vis-à-vis the World | https://teriin.org/policy-brief/biodiversity-and-land-restoration-india-narrative-indias-sustainability-efforts-vis |
| `727e791c-f6a5-47be-aa90-ce7828ba49b5` | website / policy_brief | Study on Implementation of Compensatory Afforestation in India | https://teriin.org/policy-brief/study-implementation-compensatory-afforestation-india |
| `3de36faa-f202-4c16-9c40-07c2a98e4942` | website / ongoing_projects | Third party evaluation of works undertaken during the period 2022-23 to 2023-24 under Haryana Compensatory Aff | https://teriin.org/project/third-party-evaluation-works-undertaken-during-period-2022-23-2023-24-under-haryana |
| `fc7e7a2e-8914-4ae8-b214-3246272f5333` | website / services | Technology for reclaming wastelands |  |
| `a30ce37b-9b6a-437a-8a07-45cdb61551bd` | website / press_release | TERI recommends action points to reverse land degradation in India | https://teriin.org/press-release/teri-recommends-action-points-reverse-land-degradation-india |
| `5443697b-cf75-4a90-a69f-1ab8ed67a3ad` | website / completed_projects | Study on Economics of Desertification, Land Degradation and Drought (DLDD) in India | https://teriin.org/project/study-economics-desertification-land-degradation-and-drought-dldd-india |

---

### Q072 - What is the circular economy and why is it important?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `LOW` &nbsp;|&nbsp; **Judgement**: `GOLD_AMBIGUOUS` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual / definitional
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> The corpus contains NO general definition of the circular economy. The only definitional passage is plastics-scoped, in TERI's article 'Towards a Circular Plastics Economy': circular economy 'involves every stage of a plastic product's lifetime from its production till it reaches the customer and ends up as plastic waste' and 'refers to a closed loop system in which the materials constantly flow without leaking into the environment, keeping the value of plastics in the economy'. The 'why it matters' half IS supported by TERI's own framing: unsustainable consumption of resources is at the heart of environmental degradation, so TERI works on understanding future resource demand and promoting pathways for resource efficiency, waste management and circular economy in order to decouple economic growth from environmental impacts; and it works towards solutions that reduce waste generation and promote reuse and recycling to build a circular economy. TERI's Critical Mineral Security work adds resource security as a driver.

**Expected facts**

- The corpus's only definitional passage is scoped to PLASTICS: 'Circular economy involves every stage of a plastic product's lifetime from its production till it reaches the customer and ends up as plastic waste. It refers to a closed loop system in which the materials constantly flow without leaking into the environment, keeping the value of plastics in the economy.' A general-purpose definition of the circular economy is NOT stated anywhere in the corpus.
- TERI's stated rationale: unsustainable consumption of resources is at the heart of environmental degradation, so promoting resource efficiency, waste management and circular economy is needed to decouple economic growth from environmental impacts.
- TERI works towards solutions that reduce waste generation and promote reuse and recycling to build a circular economy.

**Expected entities**: circular economy, 3Rs

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `280770ce-8e18-4ae7-b29e-78eb7111273d` | website / policy_brief | Critical Mineral Security: The Circular Pathway | https://teriin.org/policy-brief/critical-mineral-security-circular-pathway |
| `f5665b91-78a8-497a-b0ca-6044e0974d97` | website / ongoing_projects | Creating an integrated resource efficiency policy for India - with public input | https://teriin.org/project/heres-your-chance-influence-indias-resource-efficiency-policy |
| `be74de52-11c3-470c-94fa-bdbeaa962717` | website / article | Towards a Circular Plastics Economy: India’s Actions to #BeatPlasticPollution | https://teriin.org/article/towards-circular-plastics-economy-indias-actions-beatplasticpollution |

**Notes**: LOW confidence: the closest thing to a definition in the corpus is inside the article 'Towards a Circular Plastics Economy: India's Actions to #BeatPlasticPollution', where the closed-loop definition is stated for PLASTICS specifically and attributed in part to the Ellen MacArthur Foundation; the 3Rs framing appears in a description of CHINA's policy. TERI's own thematic and policy pages supply the importance half cleanly. A human should decide whether a general circular-economy definition may be credited. JUDGEMENT: RECLASSIFIED GOLD_AMBIGUOUS. Three problems were found. (1) None of the four originally cited documents contains a circular-economy definition at all (verified by full-text scan: 'closed loop' absent from all four; f5665b91 does not even contain the phrase 'circular economy'). (2) The definition the gold stated was generalised from a PLASTICS-scoped passage in be74de52-11c3-470c-94fa-bdbeaa962717 by silently deleting the word 'plastic'. (3) The '3Rs (reduce-reuse-recycle)' framing is not TERI's - in the corpus it appears as CHINA's definition of resource efficiency inside a TERI report (545965cc) and as JAPAN's Resource Circulation Strategy ('Concept of 3Rs + Renewable'); that fact has been REMOVED. The residual ambiguity a human must settle: whether a plastics-scoped definition may be credited as an answer to a general 'what is the circular economy' question. The importance half of the question remains properly supported by TERI's own thematic and policy pages.

---

### Q073 - What circular economy projects is TERI implementing?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's circular-economy projects and outputs include: 'Study on Circular Economy of End-of-Life Vehicles and Other Sectors' (2026); 'Critical Mineral Security: The Circular Pathway' (2026); 'Advancing Circular Economy of Waste Electronic and Electrical Equipment'; 'Maximising Resource Efficiency and Circularity in the Electrical and Electronic Equipment Value Chain'; the European Union Resource Efficiency Initiative Phase II; the 'Strategy for fostering Resource Efficiency and Circular Economy in Goa', which made Goa India's first state with a resource-efficiency strategy; the WCEF2026 accelerator session on Circular Public Procurement and Ecolabels; the 6th WasteTech Forum on electronic-waste recycling enabling India's circular economy; work on carton recycling; and circular-bioeconomy research (woody biomass in carbon capture and biomanufacturing; rare-earth recovery from coal and coal ash via urban mining). TERI is also involved in a Materials/product circularity indicator approach in packaging LCA work.

**Expected facts**

- TERI conducted a 'Study on Circular Economy of End-of-Life Vehicles and Other Sectors' (2026).
- TERI published 'Critical Mineral Security: The Circular Pathway' (2026).
- TERI published work on advancing the circular economy of waste electronic and electrical equipment and on maximising resource efficiency and circularity in the EEE value chain.
- TERI implemented the European Union Resource Efficiency Initiative Phase II.
- TERI prepared the 'Strategy for fostering Resource Efficiency and Circular Economy in Goa'; Goa became India's first state to have a resource-efficiency strategy.
- TERI convened a WCEF2026 accelerator session on Circular Public Procurement and Ecolabels and the 6th WasteTech Forum on electronic-waste recycling for India's circular economy.
- TERI researches the circular bioeconomy, including the role of woody biomass in carbon capture and biomanufacturing and recovery of rare-earth elements from coal and coal ash through urban mining.

**Expected entities**: End-of-Life Vehicles, Critical Mineral Security, EU Resource Efficiency Initiative, Goa resource-efficiency strategy, WCEF2026, WasteTech Forum

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `9032cec1-fc66-4da2-838e-0cdc4c831337` | website / policy_brief | Study on Circular Economy of End-of-Life Vehicles and Other Sectors | https://teriin.org/policy-brief/study-circular-economy-end-life-vehicles-and-other-sectors |
| `280770ce-8e18-4ae7-b29e-78eb7111273d` | website / policy_brief | Critical Mineral Security: The Circular Pathway | https://teriin.org/policy-brief/critical-mineral-security-circular-pathway |
| `ec9975f3-63c5-403e-8631-d7984db600e0` | pdf_attachment / policy_brief | Advancing Circular Economy of Waste Electronic and Electrical Equipment Ewaste and Lithium Ion Batteries in In | https://teriin.org/policy-brief/study-circular-economy-end-life-vehicles-and-other-sectors |
| `536b446c-10b9-4374-a52c-4c659c4e3488` | website / research_papers | Maximising Resource Efficiency and Circularity in the Electrical and Electronic Equipment Value Chain and the  | https://teriin.org/research-paper/maximising-resource-efficiency-and-circularity-electrical-and-electronic-equipment |
| `33bff102-3e12-4386-8de3-a75fcf780f72` | website / ongoing_projects | European Union Resource Efficiency Initiative Phase II | https://teriin.org/project/european-union-resource-efficiency-initiative-phase-ii |
| `705f02f3-d402-4196-80a7-8832ea255d2c` | website / policy_brief | Strategy for fostering Resource Efficiency and Circular Economy in Goa | https://teriin.org/policy-brief/strategy-fostering-resource-efficiency-and-circular-economy-goa |
| `058a0931-580e-481f-a02f-78641809321d` | website / press_release | Goa becomes India's first state to have resource efficiency strategy; measures suggested for tourism, construc | https://teriin.org/press-release/goa-becomes-indias-first-state-have-resource-efficiency-strategy-measures-suggested |
| `c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1` | website / events | WCEF2026 Accelerator Session: Circular Public Procurement and Ecolabels | https://teriin.org/event/wcef2026-accelerator-session-circular-public-procurement-and-ecolabels |
| `145b498c-c92d-476f-af75-176eff5797f0` | website / events | 6th Edition of WasteTech Forum on “Electronic Waste Recycling: Enabling India’s Circular Economy & Resource Se | https://teriin.org/event/6th-edition-wastetech-forum-electronic-waste-recycling-enabling-indias-circular-economy |
| `5e8c848e-b019-4d05-a1dc-174fd8d03ebc` | website / events | Closing the loop: Advancing Carton Recycling for a Circular Economy | https://teriin.org/event/closing-loop-advancing-carton-recycling-circular-economy |
| `f4db8508-91de-4e4e-abc3-969e0b0f9fd0` | website / research_papers | Role of woody biomass in carbon capture, circular bioeconomy, and biomanufacturing | https://teriin.org/research-paper/role-woody-biomass-carbon-capture-circular-bioeconomy-and-biomanufacturing |
| `537fca21-7961-4e77-8009-8863d1d72b40` | website / research_papers | Sustainable recovery of Rare Earth Elements (REEs) from coal and coal ash through urban mining: A Nature Based | https://teriin.org/research-paper/sustainable-recovery-rare-earth-elements-rees-coal-and-coal-ash-through-urban-mining |

**Notes**: documents_tag records only 43 'Circular economy' tags, so the set is title/body-derived and not closed; score correctness rather than completeness.

---

### Q074 - What research exists on waste-to-resource technologies?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's waste-to-resource research and technology: TEAM (TERI's Enhanced Acidification and Methanation), which converts organic waste to biogas with a shorter processing time than other biogas plants and is customisable for different climates, deployed for example as a 200 kg/day bio-methanation plant at NTPC-Farakka; pilot-scale process development for pyrolysis oil from multi-feedstock (biomass, tyre and other wastes); Refuse Derived Fuel from municipal solid waste and its co-processing; waste-derived nanomaterials (industrial wastes to nano-commodities; BIO2NANO bioresources to nanomaterials); silk-industry waste protein (sericin) hybrid nanoflowers for antibiotic remediation; rice-straw cellulose and cellulose-nanofibre coatings; recovery of rare-earth elements from coal and coal ash by urban mining; and anaerobic digestion work on minimising environmental burden. TERI's thematic framing is to reduce waste generation and promote reuse and recycling to build a circular economy; its stated goals include upscaling resource-efficient and waste-management solutions.

**Expected facts**

- TEAM (TERI's Enhanced Acidification and Methanation) converts organic waste into biogas with a shorter waste-processing time than other biogas plants and is customisable for different climatic conditions.
- TERI set up a bio-methanation plant using the TEAM process (200 kg/day) at NTPC-Farakka.
- TERI is running pilot-scale process development for generation of pyrolysis oil from multi-feedstock inputs including biomass and tyre waste.
- TERI has worked on Refuse Derived Fuel (RDF) prepared from municipal solid waste and its co-processing.
- TERI researches waste-derived nanomaterials, including industrial wastes to nano-commodities and bioresources to nanomaterials (BIO2NANO).
- TERI researched silk-industry waste protein-derived sericin hybrid nanoflowers for antibiotics remediation.
- TERI researched recovery of rare-earth elements from coal and coal ash through urban mining.

**Expected entities**: TEAM, NTPC-Farakka, Refuse Derived Fuel, BIO2NANO, sericin nanoflowers

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d604f23f-cbaa-4c0f-9f6c-3c370f207e0c` | website / page | TERI's enhanced acidification and methanation technology | https://teriin.org/technology/teri-enhanced-acidification-and-methanation-technology |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `0904c196-2f93-47ad-81ec-34b6f75c082a` | website / ongoing_projects | Setting up of a Bio Methanation plant (TEAM process) 200 kg/day at NTPC-Farakka for the production of biogas a | https://teriin.org/project/setting-bio-methanation-plant-team-process-200-kgday-ntpc-farakka-production-biogas-and |
| `6b129fcc-2ffc-48df-bb1a-e395dae7ad7d` | website / ongoing_projects | Pilot Scale Process Development for Generation of Pyrolysis Oil from Multifeed (Biomass, Tyre, Plastic) and it | https://teriin.org/project/pilot-scale-process-development-generation-pyrolysis-oil-multifeed-biomass-tyre-plastic-and |
| `a6f5e397-49e8-4e51-8a49-2702eed3ab9a` | website / events | Webinar on 'Preparation of Municipal Solid Waste based Refuse Derived Fuel (RDF) and its Co-processing in ceme | https://teriin.org/event/webinar-preparation-municipal-solid-waste-based-refuse-derived-fuel-rdf-and-its-co-processing |
| `675ad4a7-0f80-45b4-a244-317df68ae3b3` | website / events | Webinar Series on Waste-Derived Nanomaterials: Part-II - BIO2NANO: BioResources to Sustainable Nanoproducts- I | https://teriin.org/event/webinar-series-waste-derived-nanomaterials-part-ii-bio2nano-bioresources-sustainable |
| `eece31d5-8a8f-4f4e-bc7a-d86c25327ddb` | website / events | Webinar Series on Waste-Derived Nanomaterials: Part-I Industrial Wastes to Nano-commodities: Status, Impact an | https://teriin.org/event/webinar-waste-derived-nano-materials-status-impact-and-future-prospects |
| `8c943da5-f3aa-4171-aff3-c24fa995ebd3` | website / research_papers | Silk Industry Waste Protein-Derived Sericin Hybrid Nanoflowers for Antibiotics Remediation via Circular Econom | https://teriin.org/research-paper/silk-industry-waste-protein-derived-sericin-hybrid-nanoflowers-antibiotics |
| `7b3dbdd4-a62a-43b4-8e13-0baac2235085` | website / research_papers | Filling in the gaps in second‑generation biorefineries: evaluating rice straw and its bioethanol residue for t | https://teriin.org/research-paper/filling-gaps-second-generation-biorefineries-evaluating-rice-straw-and-its |
| `537fca21-7961-4e77-8009-8863d1d72b40` | website / research_papers | Sustainable recovery of Rare Earth Elements (REEs) from coal and coal ash through urban mining: A Nature Based | https://teriin.org/research-paper/sustainable-recovery-rare-earth-elements-rees-coal-and-coal-ash-through-urban-mining |
| `970dc27f-045f-4d11-b184-77823421944e` | website / research_papers | Emerging perspectives on environmental burden minimisation initiatives from anaerobic digestion technologies f | https://teriin.org/research-paper/emerging-perspectives-environmental-burden-minimisation-initiatives-anaerobic |
| `15b496a4-ab52-4cf3-9c15-bc46f4a94e01` | website / article | A green agenda: Converting waste to wealth | https://teriin.org/article/green-agenda-converting-waste-wealth |
| `0d106e9d-b19b-41ae-a45b-5b1a36ddd245` | website / page | Thematic Areas | https://teriin.org/thematic-areas |

---

### Q075 - How does TERI support plastic waste management?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI supports plastic-waste management chiefly through its Western Regional Centre in Mumbai, which states it has undertaken projects on managing plastic waste in the Mumbai Metropolitan Region through technology interventions, capacity building and awareness programmes, framed by the need to assess the types and quantities of plastic waste entering water bodies and the consumer behaviour behind it. Research and analysis: 'Plastics in the Indian economy: a comprehensive material flow analysis'; 'Towards a Circular Plastics Economy: India's Actions to #BeatPlasticPollution'; microplastics studies in wastewater treatment plants and in the Brahmani river-mangrove system, Bhitarkanika. Innovation support: 'Support to Start-ups and Innovators on Alternate Packaging Materials'. Outreach: the infographic 'Single-use plastic: Problems and alternatives'. TERI has also assessed beverage-packaging options through a comparative LCA and management of post-consumer Tetra Pak cartons.

**Expected facts**

- TERI Mumbai has undertaken projects on managing plastic waste in the Mumbai Metropolitan Region through technology interventions, capacity-building initiatives and awareness programmes.
- TERI frames plastic-waste work around assessing the types and quantities of plastic waste entering water bodies and the consumer behaviour behind plastic-waste management.
- TERI published 'Plastics in the Indian economy: a comprehensive material flow analysis'.
- TERI published 'Towards a Circular Plastics Economy: India's Actions to #BeatPlasticPollution'.
- TERI researches microplastics, including in wastewater treatment plants and in the Brahmani river-mangrove system in Bhitarkanika.
- TERI runs 'Support to Start-ups and Innovators on Alternate Packaging Materials'.
- TERI published the infographic 'Single-use plastic: Problems and alternatives' and studied management of post-consumer Tetra Pak cartons.

**Expected entities**: Mumbai Metropolitan Region, material flow analysis, microplastics, single-use plastic

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `1f2d085c-58cc-4193-85b2-8b29f86ff86a` | website / page | Our Research Focus | https://teriin.org/Our-Research-Focus |
| `1ee00350-33b2-4e9e-aa42-38c4bc3ab739` | website / research_papers | Plastics in the Indian economy: a comprehensive material flow analysis | https://teriin.org/research-paper/plastics-indian-economy-comprehensive-material-flow-analysis |
| `96017abd-a4ef-4a00-a738-fa107f75f441` | website / research_papers | Study of occurrence, abundance, and characterization of microplastics in wastewater treatment plant in New Del | https://teriin.org/research-paper/study-occurrence-abundance-and-characterization-microplastics-wastewater-treatment |
| `bfe0281d-3318-4847-b3c3-5b3393ed0eee` | website / research_papers | Microplastic Pollution in a Tropical River–Mangrove System of the Brahmani River in Bhitarkanika Wildlife Sanc | https://teriin.org/research-paper/microplastic-pollution-tropical-river-mangrove-system-brahmani-river-bhitarkanika |
| `f3ace558-5a39-4754-9950-a61a06655084` | website / ongoing_projects | Support to Start-ups and Innovators on Alternate Packaging Materials | https://teriin.org/project/support-start-ups-and-innovators-alternate-packaging-materials |
| `12775a79-b258-4d91-a44e-d908eb94ee71` | website / infographics | Single-use plastic: Problems and alternatives | https://teriin.org/infographics/single-use-plastic-problems-and-alternatives |
| `c07cba3f-09f2-47f8-80d1-2ece7f5060b3` | website / report | Sustainable Beverage Packaging Options in India - A Comparative Life Cycle Assessment Study | https://teriin.org/report/sustainable-beverage-packaging-options-india-comparative-life-cycle-assessment-study |
| `10815cde-ca73-4232-a9ae-fdc8120f5297` | website / completed_projects | Management of Post Consumer Tetra Pak Cartons (PCCs) | https://teriin.org/project/management-post-consumer-tetra-pak-cartons-pccs |
| `be74de52-11c3-470c-94fa-bdbeaa962717` | website / article | Towards a Circular Plastics Economy: India’s Actions to #BeatPlasticPollution | https://teriin.org/article/towards-circular-plastics-economy-indias-actions-beatplasticpollution |

---

### Q076 - What are TERI's solutions for urban waste management and sanitation?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's urban waste and sanitation solutions cover characterisation, planning, technology, audit and capacity building. Technology: TEAM bio-methanation for organic waste (deployed at NTPC-Farakka) and RDF preparation and co-processing from municipal solid waste. Characterisation and planning: sampling, characterisation and BMP assessment of municipal solid waste from Rajkot and Ahmedabad; GIZ-TERI support to Panjim to reduce GHG emissions through municipal waste management. Audit and assurance: third-party quality-assurance audit for the Solid Waste Management in Delhi project; municipal solid waste management audits in East Delhi and Varanasi wards, with published argument that independent audits can guide urban local bodies to reduce, reuse and recycle. Capacity building: Solid Waste Management exposure workshops for officials of Urban Local Bodies and elected representatives under the Swachh Bharat Mission (Urban), and a training programme for municipal staff for a cleaner and greener Lucknow. Sanitation and policy: the discussion paper 'Aligning India's Sanitation Policies with the SDGs', WASH school programmes with corporate partners, a Training of Trainers programme for the rural sanitation sector, and research on achieving SDGs in water and sanitation in India. TERI's stated goals include enabling the planning and governance of environmentally sustainable cities through management of solid waste, sewage and sanitation.

**Expected facts**

- TERI's stated goals include enabling planning and governance of environmentally sustainable cities through management of solid waste, sewage and sanitation.
- TERI's TEAM bio-methanation process converts organic waste to biogas and was deployed as a 200 kg/day plant at NTPC-Farakka.
- TERI conducts sampling, characterisation and BMP assessment of municipal solid waste, including for Rajkot and Ahmedabad.
- TERI acted as third-party quality-assurance audit agency for the 'Solid Waste Management in Delhi' project.
- TERI audited municipal solid waste management systems in East Delhi and in selected wards of Varanasi and argued independent audits can guide urban local bodies to reduce, reuse and recycle.
- TERI ran Solid Waste Management exposure workshops for officials of Urban Local Bodies and elected representatives under the Swachh Bharat Mission (Urban).
- TERI ran a training programme to strengthen municipal staff for a cleaner and greener Lucknow.
- TERI published the discussion paper 'Aligning India's Sanitation Policies with the SDGs'.

**Expected entities**: TEAM, Swachh Bharat Mission (Urban), Urban Local Bodies, Lucknow, Rajkot, Ahmedabad

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `d604f23f-cbaa-4c0f-9f6c-3c370f207e0c` | website / page | TERI's enhanced acidification and methanation technology | https://teriin.org/technology/teri-enhanced-acidification-and-methanation-technology |
| `0904c196-2f93-47ad-81ec-34b6f75c082a` | website / ongoing_projects | Setting up of a Bio Methanation plant (TEAM process) 200 kg/day at NTPC-Farakka for the production of biogas a | https://teriin.org/project/setting-bio-methanation-plant-team-process-200-kgday-ntpc-farakka-production-biogas-and |
| `a1b1a9a1-d99a-4cdf-a58d-7367ece50a2c` | website / ongoing_projects | Sampling, Characterization, and BMP Assessment of Municipal Solid Waste from Rajkot and Ahmedabad City Municip | https://teriin.org/project/sampling-characterization-and-bmp-assessment-municipal-solid-waste-rajkot-and-ahmedabad |
| `9793be85-925d-4860-a36c-c9ed58453a99` | website / article | GIZ-TERI to help Panjim reduce GHG emissions through municipal waste management | https://teriin.org/article/giz-teri-help-panjim-reduce-ghg-emissions-through-municipal-waste-management |
| `f736c31c-d05d-4d2c-ae28-f21cc71b99bf` | website / ongoing_projects | Third party quality assurance audit agency for the project "Solid Waste Management in Delhi" | https://teriin.org/project/third-party-quality-assurance-audit-agency-project-solid-waste-management-delhi |
| `eca98a32-eb0d-4978-9f2a-05b152c6d249` | website / research_papers | ​An Audit of Municipal Solid Waste Management in a Mega-City (East Delhi): Challenges and Opportunities. | https://teriin.org/research-paper/audit-municipal-solid-waste-management-mega-city-east-delhi-challenges-and |
| `0e1baa8c-d0c4-459f-b9f5-c9e8cd22243d` | website / research_papers | An Audit of Municipal Solid Waste Management System in Selected Wards of Varanasi - A Case Study | https://teriin.org/research-paper/audit-municipal-solid-waste-management-system-selected-wards-varanasi-case-study |
| `0368e432-7a0f-4e18-9cbc-4538fc2ef821` | website / article | Independent audits can guide urban local bodies to reduce, reuse and recycle municipal solid waste | https://teriin.org/interview/independent-audits-can-guide-urban-local-bodies-reduce-reuse-and-recycle-municipal-solid |
| `0060215e-5af6-418b-93dd-eaf883e82eae` | website / ongoing_projects | Solid waste management exposure workshops for the officials of  ULBs and elected representatives under Swachh  | https://teriin.org/project/solid-waste-management-exposure-workshops-officials-ulbs-and-elected-representatives-under |
| `c3a54973-e16e-46b8-b7b1-6b9180baa9ed` | website / ongoing_projects | Conducting Solid Waste Management Exposure Workshops for the officials of Urban Local Bodies and Elected Repre | https://teriin.org/project/conducting-solid-waste-management-exposure-workshops-officials-urban-local-bodies-and |
| `712ba1c8-5514-4f3f-a9d0-a071f6214c7a` | website / ongoing_projects | Strengthening Municipal Staff for Cleaner and Greener Lucknow: TERI's Innovative Training Program on Mechanica | https://teriin.org/project/strengthening-municipal-staff-cleaner-and-greener-lucknow-teris-innovative-training-program |
| `9ce46636-42c5-47b1-bb3e-d16609b85524` | website / policy_brief | Discussion Paper: Aligning India's Sanitation Policies with the SDGs | https://teriin.org/policy-brief/discussion-paper-aligning-indias-sanitation-policies-sdgs |
| `4d604a14-3ff9-4e5c-809a-15c1ab1f3d34` | website / events | Training of Trainers programme for the Rural Sanitation Sector | https://teriin.org/event/training-trainers-programme-rural-sanitation-sector |
| `cba07f58-533f-4a20-9bda-5a351aa6489a` | website / research_papers | Achieving SDGs in water and sanitation sectors in India | https://teriin.org/research-paper/achieving-sdgs-water-and-sanitation-sectors-india |

---

### Q077 - How can industries improve resource efficiency through circular practices?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's answer to how industries can improve resource efficiency through circular practices, as documented: sector roadmaps and studies (the Resource Efficiency Initiative detailed study of India's automobile sector; 'Maximising Resource Efficiency and Circularity in the Electrical and Electronic Equipment Value Chain'; the study on circular economy of end-of-life vehicles); policy instruments (an integrated resource-efficiency policy for India developed with public input, the roadmap TERI prepared to foster resource-efficiency policy, and inputs to end-of-life vehicle scrapping and metal-recycling policies for CPCB); state strategy (the Goa resource efficiency and circular-economy strategy, India's first); standards and business models (webinars on standards for fostering resource efficiency and circular economy in India and on business models for recycling and material-recovery infrastructure); and firm-level services (detailed energy, water and resource-efficiency audits with techno-economic recommendations, energy-performance benchmarking, technical consultancy for energy conservation and resource efficiency at plant level). TERI's research also led to the creation of the Indian Resource Panel.

**Expected facts**

- TERI conducted the Resource Efficiency Initiative detailed study of India's automobile sector.
- TERI published 'Maximising Resource Efficiency and Circularity in the Electrical and Electronic Equipment Value Chain'.
- TERI developed an integrated resource-efficiency policy for India with public input and prepared a roadmap to foster resource-efficiency policy for India.
- TERI prepared the resource-efficiency and circular-economy strategy for Goa, the first Indian state to have one.
- TERI's work led to the creation of the Indian Resource Panel working with the Union environment ministry, and provided inputs for CPCB policies on end-of-life vehicle scrapping and metal recycling.
- TERI conducts detailed energy, water and resource-efficiency audits with techno-economic recommendations backed by simulations and monitoring, and provides plant-level technical consultancy for energy conservation and resource efficiency.
- TERI convened webinars on standards for fostering resource efficiency and circular economy in India and on business models for recycling and material-recovery infrastructure.

**Expected entities**: Resource Efficiency Initiative, Indian Resource Panel, Goa, CPCB, end-of-life vehicles

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `00d028f5-f0b3-4da3-8fb2-e73b86da455a` | website / completed_projects | Resource Efficiency Initiative: A detailed study on India's Automobile Sector | https://teriin.org/project/resource-efficiency-initiative-detailed-study-indias-automobile-sector |
| `536b446c-10b9-4374-a52c-4c659c4e3488` | website / research_papers | Maximising Resource Efficiency and Circularity in the Electrical and Electronic Equipment Value Chain and the  | https://teriin.org/research-paper/maximising-resource-efficiency-and-circularity-electrical-and-electronic-equipment |
| `9032cec1-fc66-4da2-838e-0cdc4c831337` | website / policy_brief | Study on Circular Economy of End-of-Life Vehicles and Other Sectors | https://teriin.org/policy-brief/study-circular-economy-end-life-vehicles-and-other-sectors |
| `f5665b91-78a8-497a-b0ca-6044e0974d97` | website / ongoing_projects | Creating an integrated resource efficiency policy for India - with public input | https://teriin.org/project/heres-your-chance-influence-indias-resource-efficiency-policy |
| `d0641edb-aa10-44a9-8ade-cdf1a7056856` | website / press_release | TERI prepares roadmap to foster Resource Efficiency policy for India | https://teriin.org/press-release/teri-prepares-roadmap-foster-resource-efficiency-policy-india |
| `705f02f3-d402-4196-80a7-8832ea255d2c` | website / policy_brief | Strategy for fostering Resource Efficiency and Circular Economy in Goa | https://teriin.org/policy-brief/strategy-fostering-resource-efficiency-and-circular-economy-goa |
| `058a0931-580e-481f-a02f-78641809321d` | website / press_release | Goa becomes India's first state to have resource efficiency strategy; measures suggested for tourism, construc | https://teriin.org/press-release/goa-becomes-indias-first-state-have-resource-efficiency-strategy-measures-suggested |
| `b8b7e710-a6dd-4289-88cd-c372f5faa1a7` | website / page | Policy | https://teriin.org/policy |
| `89f45551-aaac-4e1a-8a95-5b1b9a43668c` | website / services | Audits, Validation & PMU Support |  |
| `7358c7aa-b509-45f7-8d72-bc4a3417e172` | website / services | Energy performance benchmarking |  |
| `1420d955-02b3-4d79-9053-16ab6607587c` | website / ongoing_projects | Technical consultancy for energy conservation and resource efficiency for MIL, Hapur plant, unit 1 & 2 combine | https://teriin.org/project/technical-consultancy-energy-conservation-and-resource-efficiency-mil-hapur-plant-unit-1-2 |
| `632a47df-9762-44f1-83ae-277d1da8c485` | website / events | Webinar on Standards for fostering Resource Efficiency and Circular Economy in India | https://teriin.org/event/webinar-standards-fostering-resource-efficiency-and-circular-economy-india |
| `8339b7cb-9160-4343-bd96-05f7b8b4b62b` | website / events | Webinar on Business models for fostering recycling and material recovery infrastructure | https://teriin.org/event/webinar-business-models-fostering-recycling-and-material-recovery-infrastructure |
| `33bff102-3e12-4386-8de3-a75fcf780f72` | website / ongoing_projects | European Union Resource Efficiency Initiative Phase II | https://teriin.org/project/european-union-resource-efficiency-initiative-phase-ii |

---

### Q078 - How does TERI support sustainable materials management?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `ce1386c7-867f-43e5-b97c-2207538a1135` | website / ongoing_projects | To develop energy efficient building materials directory for India | https://teriin.org/project/develop-energy-efficient-building-materials-directory-india |
| `1ee00350-33b2-4e9e-aa42-38c4bc3ab739` | website / research_papers | Plastics in the Indian economy: a comprehensive material flow analysis | https://teriin.org/research-paper/plastics-indian-economy-comprehensive-material-flow-analysis |
| `f3ace558-5a39-4754-9950-a61a06655084` | website / ongoing_projects | Support to Start-ups and Innovators on Alternate Packaging Materials | https://teriin.org/project/support-start-ups-and-innovators-alternate-packaging-materials |
| `4c0cebb1-9ee6-472b-8937-746e26882aa0` | website / article | Sustainable Building Materials: Accelerating the journey towards low carbon development | https://teriin.org/article/sustainable-building-materials-accelerating-journey-towards-low-carbon-development |
| `4eab067f-425a-4299-afee-f542e3a007f3` | website / services | Research, Innovation & Impact Assessment |  |

**Notes**: TERM NOT USED BY TERI. 'Sustainable materials management' does not appear as a programme, service, theme or tag; the phrase is an external framing. Adjacent evidence exists but pulls in different directions: sustainable BUILDING materials R&D (Research & Innovation service; energy-efficient building materials directory; 'Sustainable Building Materials: Accelerating the journey towards low carbon development'), plastics material flow analysis, alternate packaging materials support, waste-derived nanomaterials, and resource-efficiency/material-productivity indicator work. Which of these the question means is a judgement call a human must make; scoring an answer against the wrong grouping would be unfair.

---

### Q079 - What technologies are available for waste valorization?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Waste-valorisation technologies documented in the corpus: TEAM (TERI's Enhanced Acidification and Methanation) for organic waste to biogas; pilot-scale pyrolysis-oil generation from multi-feedstock (biomass, tyre and other waste), and an earlier pilot-scale pyrolysis test unit for liquid biofuels and value-added products; Refuse Derived Fuel from municipal solid waste with co-processing; Oilzapper and Oilivorous-S microbial formulations that convert oil-contaminated soil and oily sludge into harmless products; waste-derived nanomaterials (industrial wastes to nano-commodities; bioresources to nanomaterials); sericin hybrid nanoflowers from silk-industry waste protein; rice-straw-derived cellulose and cellulose-nanofibre coating materials; recovery of rare-earth elements from coal and coal ash via urban mining; algal and biomass conversion routes to bio-crude, bio-oil and carotenoids via hydrothermal liquefaction; and second-generation ethanol from rice straw.

**Expected facts**

- TEAM (TERI's Enhanced Acidification and Methanation) converts organic waste into biogas.
- TERI is developing pilot-scale processes for pyrolysis oil from multi-feedstock inputs including biomass and tyre waste, and earlier built a pilot-scale pyrolysis test unit for liquid biofuels and value-added products.
- TERI works on Refuse Derived Fuel from municipal solid waste and its co-processing.
- Oilzapper and Oilivorous-S are TERI microbial technologies that break down hydrocarbons in oil-contaminated soil and oily sludge into water and fatty acids.
- TERI researches waste-derived nanomaterials, including converting industrial wastes into nano-commodities.
- TERI produced sericin hybrid nanoflowers from silk-industry waste protein for antibiotic remediation.
- TERI researches rice-straw-derived cellulose and cellulose nanofibres for coating materials and second-generation ethanol.
- TERI researches recovery of rare-earth elements from coal and coal ash through urban mining, and hydrothermal liquefaction routes to bio-crude/bio-oil and carotenoids.

**Expected entities**: TEAM, pyrolysis oil, Refuse Derived Fuel, Oilzapper, Oilivorous-S, sericin nanoflowers, cellulose nanofibres, hydrothermal liquefaction

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `d604f23f-cbaa-4c0f-9f6c-3c370f207e0c` | website / page | TERI's enhanced acidification and methanation technology | https://teriin.org/technology/teri-enhanced-acidification-and-methanation-technology |
| `44d366d7-953c-41cc-aafa-3425fb604cc4` | website / page | Oilzapper and Oilivorous-S | https://teriin.org/technology/oilzapper-and-oilivorous-s |
| `4de04ffe-8ab9-4264-9f3e-c91cd45d7990` | website / page | Technologies | https://teriin.org/technologies |
| `6b129fcc-2ffc-48df-bb1a-e395dae7ad7d` | website / ongoing_projects | Pilot Scale Process Development for Generation of Pyrolysis Oil from Multifeed (Biomass, Tyre, Plastic) and it | https://teriin.org/project/pilot-scale-process-development-generation-pyrolysis-oil-multifeed-biomass-tyre-plastic-and |
| `df28b414-3340-438c-a9ce-b70f91f16fc8` | website / completed_projects | Development of Pilot Scale Pyrolysis Test Unit for Production of Liquid Bio-fuels and Value Added By-products  | https://teriin.org/project/development-pilot-scale-pyrolysis-test-unit-production-liquid-bio-fuels-and-value-added |
| `a6f5e397-49e8-4e51-8a49-2702eed3ab9a` | website / events | Webinar on 'Preparation of Municipal Solid Waste based Refuse Derived Fuel (RDF) and its Co-processing in ceme | https://teriin.org/event/webinar-preparation-municipal-solid-waste-based-refuse-derived-fuel-rdf-and-its-co-processing |
| `675ad4a7-0f80-45b4-a244-317df68ae3b3` | website / events | Webinar Series on Waste-Derived Nanomaterials: Part-II - BIO2NANO: BioResources to Sustainable Nanoproducts- I | https://teriin.org/event/webinar-series-waste-derived-nanomaterials-part-ii-bio2nano-bioresources-sustainable |
| `eece31d5-8a8f-4f4e-bc7a-d86c25327ddb` | website / events | Webinar Series on Waste-Derived Nanomaterials: Part-I Industrial Wastes to Nano-commodities: Status, Impact an | https://teriin.org/event/webinar-waste-derived-nano-materials-status-impact-and-future-prospects |
| `8c943da5-f3aa-4171-aff3-c24fa995ebd3` | website / research_papers | Silk Industry Waste Protein-Derived Sericin Hybrid Nanoflowers for Antibiotics Remediation via Circular Econom | https://teriin.org/research-paper/silk-industry-waste-protein-derived-sericin-hybrid-nanoflowers-antibiotics |
| `cfe9a705-f057-493c-96ce-0c38a5b70d75` | website / research_papers | Biodegradable Cellulose and Cellulose Nanofibres‑Based Coating Materials as a Postharvest Preservative for Hor | https://teriin.org/research-paper/biodegradable-cellulose-and-cellulose-nanofibres-based-coating-materials-postharvest |
| `7b3dbdd4-a62a-43b4-8e13-0baac2235085` | website / research_papers | Filling in the gaps in second‑generation biorefineries: evaluating rice straw and its bioethanol residue for t | https://teriin.org/research-paper/filling-gaps-second-generation-biorefineries-evaluating-rice-straw-and-its |
| `537fca21-7961-4e77-8009-8863d1d72b40` | website / research_papers | Sustainable recovery of Rare Earth Elements (REEs) from coal and coal ash through urban mining: A Nature Based | https://teriin.org/research-paper/sustainable-recovery-rare-earth-elements-rees-coal-and-coal-ash-through-urban-mining |
| `055ff8d5-62ee-4797-b09b-f91f54223309` | website / research_papers | Simultaneous production of bio-crude bio-oil via hydrothermal liquefaction and carotenoids via supercritical e | https://teriin.org/research-paper/simultaneous-production-bio-crude-bio-oil-hydrothermal-liquefaction-and-carotenoids |

**Notes**: 'Available' is ambiguous - the answer mixes commercialised technologies (TEAM, Oilzapper, Oilivorous-S) with laboratory/pilot research. A grader should accept either scoping but require the answer not to present research-stage routes as commercially available.

---

### Q080 - What green building rating services does TERI provide,

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's Ratings & Certification service assists projects in achieving national and international green-building certifications, including GRIHA, with performance assessments and documentation support across all project stages. GRIHA - Green Rating for Integrated Habitat Assessment - was jointly developed by the Ministry of New and Renewable Energy (MNRE), Government of India and TERI in 2007, is administered and promoted by the GRIHA Council, and holistically evaluates a building's environmental performance over its entire life cycle against qualitative and quantitative criteria. TERI also offers GRIHA Water Positive Certification (consulting, audit and certification, with water audits of existing buildings and complexes), and a GRIHA Infrastructure Rating for logistics parks and warehouses was launched in 2026. Historically TERI's environmental-design group has also provided LEED facilitation.

**Expected facts**

- TERI assists in achieving national and international green-building certifications, including GRIHA, with performance assessments and documentation support across all project stages.
- GRIHA stands for Green Rating for Integrated Habitat Assessment.
- GRIHA was jointly developed by the Ministry of New and Renewable Energy (MNRE), Government of India and TERI in 2007.
- GRIHA is administered and promoted by the GRIHA Council (www.grihaindia.org).
- GRIHA holistically evaluates the environmental performance of buildings over their entire life cycle based on qualitative and quantitative criteria.
- TERI offers GRIHA Water Positive Certification, including water audits of existing buildings and complexes and technical assistance to enhance water efficiency.
- A GRIHA Infrastructure Rating for logistics parks and warehouses was launched in 2026.

**Expected entities**: GRIHA, GRIHA Council, MNRE, GRIHA Water Positive Certification, GRIHA Infrastructure Rating

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `512bf0b0-01b9-4d38-8547-d894ffef2f43` | website / services | Water Positive Certification - Consulting, Audit and Certification Services |  |
| `7b06dc9b-2597-4939-8e90-44cdb2cd1ebc` | website / page | Water Positive Certification - Consulting, Audit and Certification Services | https://teriin.org/services/habitat/water-positive-certification |
| `98800b2a-5011-43be-ad73-6039b898ca8e` | website / events | LAUNCH OF GRIHA INFRASTRUCTURE RATING FOR LOGISTICS PARKS AND WAREHOUSES | https://teriin.org/event/launch-griha-infrastructure-rating-logistics-parks-and-warehouses |
| `d7744c0b-989e-48b1-bce1-f83be2e4b85c` | website / page | Mission and Goals | https://teriin.org/mission-and-goals |
| `4027e3b7-0b05-4cfc-8fda-c3c11ff58732` | pdf_attachment / completed_projects | Planning our cities better to make our houses cooler | https://teriin.org/project/planning-our-cities-better-make-our-houses-cooler |

**Notes**: CONTRADICTION IN CORPUS on who administers GRIHA: /mission-and-goals (d7744c0b) says TERI 'developed and currently administers' GRIHA; the Ratings & Certification service node (3e27858c) says GRIHA 'is administered and promoted by GRIHA Council' and was 'jointly developed by MNRE and TERI in 2007'. The service node is more specific and more recent (published 2025-09) and is treated as authoritative here. Note the question text in the source document ends with a comma, not a question mark - preserved verbatim.

---

### Q081 - What is the difference between LEED and GRIHA ratings?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: comparison
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `4027e3b7-0b05-4cfc-8fda-c3c11ff58732` | pdf_attachment / completed_projects | Planning our cities better to make our houses cooler | https://teriin.org/project/planning-our-cities-better-make-our-houses-cooler |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `2e51f75d-b92b-47e9-9f56-32b53fe55633` | pdf_attachment / press_release | TERI and USGBC join forces to promote  high performance buildings in India | https://teriin.org/press-release/teri-and-usgbc-join-forces-promote-high-performance-buildings-india |
| `cdd5bd10-6dd9-4efe-81c5-304b6e6c11e4` | website / article | Net-Zero Energy Buildings in India: A Step Towards Sustainable Urban Development | https://teriin.org/article/net-zero-energy-buildings-india-step-towards-sustainable-urban-development |
| `d3cf80ff-7fec-40d7-a39f-ff68fcb66f01` | pdf_attachment / completed_projects | Download | https://teriin.org/project/framework-basic-services-indian-cities |

**Notes**: NO COMPARISON EXISTS IN THE CORPUS. A full-text co-occurrence scroll for chunks containing both 'LEED' and 'GRIHA' returns only incidental joint mentions - lists of rating systems ('In India GRIHA, LEED, IGBC cater to...'), buildings holding both certifications (Indira Paryavaran Bhawan: LEED India Platinum + GRIHA 5-star), urban-service indicators counting GRIHA- and LEED-certified buildings separately, and TERI's own service note that its team facilitates LEED accreditation (LEED India NC, LEED India CS) while it 'assists and administers GRIHA, an indigenous green building rating system for buildings, developed at TERI'. Partial distinguishing facts ARE supported (GRIHA is India's indigenous/national system developed by TERI with MNRE in 2007 and administered by GRIHA Council; LEED is the U.S. Green Building Council's system, with India the third-largest LEED market outside the U.S.), but no criteria-level, scoring-level or scope-level comparison is documented. A human must decide whether the origin/ownership contrast is an acceptable gold answer.

---

### Q082 - How can my company consult with TERI for carbon footprinting and ESG reporting?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> For corporate engagement on carbon footprinting and ESG reporting, TERI's designated interface is the TERI Council for Business Sustainability (TERI CBS), which connects TERI's research to the corporate world; member services include sustainability strategy and roadmap development, performance benchmarking and improvement, and tailor-made advisory (strategy development, performance assessment and improvement, capacity building/MDPs), with complimentary consulting person-days and discounted paid consulting, and - for Gold members - a complimentary assessment of the sustainability report. On the technical side TERI has developed GHG calculators covering Scope 1, 2 and 3 emissions and conducts carbon-footprint assessments (e.g. of a dairy value chain, of Pune city, of urban public transport, of national highways) and ESG-based reporting work (Green Port Index and ESG-based Reporting for Indian Major Ports). It also runs capacity building on carbon footprint assessment and management and an ESG certification programme with NDTV. General contact is mailbox@teri.res.in (+91 11 2468 2100 / 7110 2100).

**Expected facts**

- TERI Council for Business Sustainability (TERI CBS) is the interface between TERI's research and the corporate world.
- TERI CBS member services include sustainability strategy and roadmap development, performance benchmarking and improvement, and tailor-made advisory covering strategy development, performance assessment and improvement, and capacity building.
- TERI CBS members receive complimentary consulting person-days and a discount on paid consulting; Gold members also receive a complimentary assessment of their sustainability report.
- TERI has developed GHG calculators and contributed to projects covering Scope 1, 2 and 3 emissions.
- TERI conducts carbon-footprint assessments, including of a dairy value chain, Pune city, urban public transport systems and national highways.
- TERI runs the ongoing project 'Green Port Index and ESG-based Reporting for Indian Major Port'.
- TERI has run a Capacity Building Program on 'Carbon Footprint Assessment and Management' and, with NDTV, a three-month ESG certification programme.
- TERI's general contact is mailbox@teri.res.in, tel (+91 11) 2468 2100 / 7110 2100.

**Expected entities**: TERI CBS, Scope 1, 2 and 3, Green Port Index and ESG-based Reporting, NDTV

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `4a4b782f-5110-4520-aec6-92209213a948` | website / page | Business & Sustainability | https://teriin.org/business-sustainability |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |
| `4eab067f-425a-4299-afee-f542e3a007f3` | website / services | Research, Innovation & Impact Assessment |  |
| `fa4e72f6-a1ed-400f-82d1-ff46d8fedc10` | website / ongoing_projects | Carbon Footprint Assessment of Dairy Value Chain | https://teriin.org/project/carbon-footprint-assessment-dairy-value-chain |
| `100b323a-797d-45c1-bba3-0ab719eb003a` | website / completed_projects | Environmental Status Report and estimation of Carbon footprint for Pune City | https://teriin.org/project/environmental-status-report-and-estimation-carbon-footprint-pune-city |
| `28574c99-dd5c-48cb-8549-4f50e56a58c6` | website / research_papers | Carbon footprint of urban public transport systems in Indian cities | https://teriin.org/research-paper/carbon-footprint-urban-public-transport-systems-indian-cities |
| `8da7c290-c1a9-433e-9b0b-0e434fc3b84a` | website / completed_projects | Reducing Carbon Footprint and Enhancing Climate Resilience of National Highways in India | https://teriin.org/project/reducing-carbon-footprint-and-enhancing-climate-resilience-national-highways-india |
| `b518a527-ae0c-494b-b534-3cbd9a08a27e` | website / ongoing_projects | Green Port Index and ESG-based Reporting for Indian Major Port | https://teriin.org/project/green-port-index-and-esg-based-reporting-indian-major-port |
| `8e8f9a3a-5672-47bd-a81c-9a1a317832e2` | website / events | Capacity Building Program on 'Carbon Footprint Assessment and Management' | https://teriin.org/event/capacity-building-program-carbon-footprint-assessment-and-management |
| `bd80d6c7-4c68-4fe9-9c8b-40d1ae6ca7d8` | website / events | TERI in partnership with NDTV launches the 3-month ESG certification programme | https://teriin.org/event/teri-partnership-ndtv-launches-3-month-esg-certification-programme |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |

**Notes**: The corpus documents the CBS route and TERI's technical capability, but NOT a named carbon-footprinting/ESG-reporting consulting product, fee structure or enquiry form. An answer must not invent an engagement process beyond CBS membership plus general contact.

---

### Q083 - Does TERI provide Life Cycle Assessment (LCA) services?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI's Environmental Design & Technical Advisory service explicitly lists life cycle assessments among its expertise (alongside emission inventories, logistics decarbonisation and sustainable mobility). Documented LCA work includes: the comparative LCA study 'Sustainable Beverage Packaging Options in India' (with a finding that aluminium beverage cans have superior environmental performance) under the project 'Rethinking Packaging: Aluminium as Sustainable Packaging Solutions in India'; a Comprehensive Life Cycle Assessment of Sugar-based Sustainable Aviation Fuel for India (2025-26, with a roundtable in July 2026); a comparative LCA between powertrain components of ICE vehicles and EVs; and an LCA of hot-mix and cold-mix technologies for road construction and maintenance. TERI has also applied LCA methodology to estimate the carbon footprint of India's national-highway network, and uses a material circularity indicator alongside LCA in packaging work.

**Expected facts**

- TERI's Environmental Design & Technical Advisory service lists life cycle assessments among its expertise.
- TERI produced 'Sustainable Beverage Packaging Options in India - A Comparative Life Cycle Assessment Study' and reported that aluminium beverage cans have superior environmental performance.
- TERI runs a Comprehensive Life Cycle Assessment of Sugar-based Sustainable Aviation Fuel for India.
- TERI conducted a Comparative LCA Between Powertrain Components of ICE Vehicles Versus EVs.
- TERI conducted a life cycle assessment of hot-mix and cold-mix technologies for construction and maintenance of roads.
- TERI applied LCA methodology to estimate the carbon footprint of India's national-highway network.

**Expected entities**: Life Cycle Assessment, Sustainable Beverage Packaging Options in India, Sustainable Aviation Fuel, material circularity indicator

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `259d7fb3-cd37-4616-82e5-35c609abc18f` | website / services | Environmental Design & Technical Advisory |  |
| `c07cba3f-09f2-47f8-80d1-2ece7f5060b3` | website / report | Sustainable Beverage Packaging Options in India - A Comparative Life Cycle Assessment Study | https://teriin.org/report/sustainable-beverage-packaging-options-india-comparative-life-cycle-assessment-study |
| `3b0d808c-d8a7-4374-ae9a-057d82671602` | pdf_attachment / report | Sustainable Beverage Packaging Final Report | https://teriin.org/report/sustainable-beverage-packaging-options-india-comparative-life-cycle-assessment-study |
| `6d823ab8-6d99-4536-ae2d-33df5fe09bd5` | website / press_release | Life Cycle Assessment (LCA) study in India reveals that aluminium beverage cans have superior environmental pe | https://teriin.org/press-release/life-cycle-assessment-lca-study-india-reveals-aluminium-beverage-cans-have-superior |
| `5b2bafac-2d0f-4b3f-9d59-ef828db1c62f` | website / ongoing_projects | Rethinking Packaging: Aluminium as Sustainable Packaging Solutionns in India - A Comparative Life Cycle Assess | https://teriin.org/project/sustainable-beverage-packaging-options-india-comparative-life-cycle-assessment-study |
| `d626df61-45a0-4551-a47e-cc5f054615b9` | website / ongoing_projects | Comprehensive Life Cycle Assessment of Sugar-based Sustainable Aviation Fuel for India | https://teriin.org/project/comprehensive-life-cycle-assessment-sugar-based-sustainable-aviation-fuel-india |
| `dbc4eeb8-3ed8-49ea-95b7-7b60f4ab5500` | website / events | Roundtable on Comprehensive Life Cycle Assessment of Sugarcane Based SAF in India | https://teriin.org/event/roundtable-comprehensive-life-cycle-assessment-sugarcane-based-saf-india |
| `0c465c3c-c760-498a-898c-c157eb0ddb1c` | website / ongoing_projects | Comparative LCA Between Powertrain Components of ICE Vehicles Versus EVs | https://teriin.org/project/comparative-lca-between-powertrain-components-ice-vehicles-versus-evs |
| `42e8c96f-519a-4b44-af74-3ac6be6432aa` | website / ongoing_projects | Life cycle assessment of Hot Mix and Cold Mix technologies for Construction and Maintenance of Rural Roads | https://teriin.org/project/life-cycle-assessment-hot-mix-and-cold-mix-technologies-construction-and-maintenance-rural |
| `8da7c290-c1a9-433e-9b0b-0e434fc3b84a` | website / completed_projects | Reducing Carbon Footprint and Enhancing Climate Resilience of National Highways in India | https://teriin.org/project/reducing-carbon-footprint-and-enhancing-climate-resilience-national-highways-india |

**Notes**: LCA is documented as a capability and as delivered project work; it is NOT listed as a standalone priced service line with a stated scope and standard (e.g. ISO 14040/44). An answer should say TERI does LCA work rather than claim a formal accredited LCA service.

---

### Q084 - Can TERI assist in conducting an energy audit for my industrial facility?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI conducts detailed energy, water and resource-efficiency audits across sectors, offering techno-economic recommendations backed by simulations and monitoring. For industry specifically it assists plants in reducing energy consumption through plant-level audits and undertakes technology assessments of energy and environmental performance for different industrial sectors. Its resource conservation / energy audit service reports audits of around 200 buildings across hotels, commercial offices, hospitals, schools, universities, shopping malls and theatres, with detailed analysis of lighting, HVAC, water heating, electrical steam boilers and steam distribution to find energy waste; validation of energy performance by computer simulation and modelling; water-demand estimation and conservation measures; energy-management programmes for service industries; an instrument pool (digital lux meters, temperature indicators, flue-gas analyzer, anemometer, ultrasonic flow meter, hygrometer, power analyzer); and techno-economic proposals for identified conservation measures from different vendors. TERI also runs MSME energy-efficiency capacity work with BEE.

**Expected facts**

- TERI conducts detailed energy, water and resource-efficiency audits across sectors, with techno-economic recommendations backed by simulations and monitoring.
- TERI assists industries in reducing energy consumption through audits at the plant level and undertakes technology assessments of energy and environmental performance for different industrial sectors.
- TERI has conducted energy audits of around 200 buildings across hotels, commercial offices, hospitals, schools, universities, shopping malls and theatres.
- TERI's audits analyse lighting, heating, ventilation, air conditioning, water heating, electrical steam boilers and steam distribution systems to identify energy waste.
- TERI validates energy performance using computer simulation and modelling and develops energy-management programmes for service industries such as hotels and the corporate sector.
- TERI maintains an instrument pool including digital lux meters, digital temperature indicators, flue-gas analyzer, anemometer, ultrasonic flow meter, hygrometer and power analyzer.
- TERI provides techno-economic proposals for identified energy-conservation measures from different vendors to facility managers.

**Expected entities**: energy audit, BEE, ECBC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `1535f84a-ac24-486d-ba8b-613113900325` | website / services | Resource conservation study/ energy audit/energy management programme |  |
| `7358c7aa-b509-45f7-8d72-bc4a3417e172` | website / services | Energy performance benchmarking |  |
| `89f45551-aaac-4e1a-8a95-5b1b9a43668c` | website / services | Audits, Validation & PMU Support |  |
| `5b2ca2ff-da97-4ecc-b439-59fa03ff25c9` | website / services | Energy efficient and environment-friendly solutions |  |
| `423a3cb3-b0dc-4672-84aa-8f2e22761df7` | website / completed_projects | Enhancing MSME Capacity for Energy Efficiency: TERI–BEE Collaborative Initiatives Under the ADEETIE Framework | https://teriin.org/project/enhancing-msme-capacity-energy-efficiency-teri-bee-collaborative-initiatives-under-adeetie |
| `1420d955-02b3-4d79-9053-16ab6607587c` | website / ongoing_projects | Technical consultancy for energy conservation and resource efficiency for MIL, Hapur plant, unit 1 & 2 combine | https://teriin.org/project/technical-consultancy-energy-conservation-and-resource-efficiency-mil-hapur-plant-unit-1-2 |

**Notes**: The audit-count evidence ('around 200 buildings') is building-sector; the industrial-plant claim comes from the energy-performance-benchmarking service node. Both are TERI's own service copy. No engagement process, price or turnaround time is documented.

---

### Q085 - What sustainability advisory services does TERI offer?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's website publishes 30 service nodes. They group into: policy and advisory (Policy, Strategic Planning & Advocacy; Policy intervention and analysis; Multidisciplinary research and policy advice; Policy research on the role of resources in national and global sustainable development); audits, validation and programme management (Audits, Validation & PMU Support; Project Monitoring Unit; Energy performance benchmarking; Resource conservation study / energy audit / energy management programme); climate and environment assessment (Climate change risk assessment; Air Quality Research; Carbon sequestration potential and biodiversity assessment; Impact evaluation of CSR initiatives); design and built environment (Environmental Design & Technical Advisory; Environmental design consultancy and advisory services; Research & development; Research, Innovation & Impact Assessment); ratings and certification (Ratings & Certification; Water Positive Certification); testing (Water, soil and sludge testing); water and natural resources (Multidisciplinary research on natural resource conservation; Multidisciplinary research on natural resource conservation; Capacity building for management of natural resources; Technology for reclaiming wastelands); technology and products (Enhanced oil recovery from mature oil reserves; Next generation technology to produce high-quality mycorrhiza; Energy efficient and environment-friendly solutions; CSR engagements to provide clean energy solutions); and capacity building and knowledge (Training & Capacity Building; Capacity Building & Knowledge Dissemination; Publication of academic and reference material; World Digital Library on Sustainable Development).

**Expected facts**

- TERI's website publishes 30 service nodes covering policy advisory, audits and PMU support, climate and environment assessment, environmental design consultancy, ratings and certification, laboratory testing, natural-resource and water services, technology and product services, and training/knowledge services.
- Named services include Policy, Strategic Planning & Advocacy; Audits, Validation & PMU Support; Project Monitoring Unit; Climate change risk assessment; Air Quality Research; Environmental Design & Technical Advisory; Ratings & Certification; Water Positive Certification; Water, soil and sludge testing; Training & Capacity Building; Capacity Building & Knowledge Dissemination; and the World Digital Library on Sustainable Development.
- TERI's Areas of Work page frames delivery as Technology Products, Policy Advisory and Outreach, and Technical Services (standard operating procedures, consultancy & advisory, strategy development for corporates, testing and certification, capacity building).

**Reproducible derivations**

- `SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='services' -> 30`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `89f45551-aaac-4e1a-8a95-5b1b9a43668c` | website / services | Audits, Validation & PMU Support |  |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |
| `c2d42e8b-4b6e-451c-9ddf-1d1f653b2b5f` | website / services | Capacity building for management of natural resources |  |
| `2ef2427a-1fdb-4398-9b73-2c4719ac38a4` | website / services | Carbon sequestration potential and biodiversity assessment |  |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |
| `769f4073-d894-496a-8386-322f8deadf91` | website / services | CSR engagements to provide clean energy solutions |  |
| `5b2ca2ff-da97-4ecc-b439-59fa03ff25c9` | website / services | Energy efficient and environment-friendly solutions |  |
| `7358c7aa-b509-45f7-8d72-bc4a3417e172` | website / services | Energy performance benchmarking |  |
| `d073da23-c0f7-4bea-beaf-26766267de4e` | website / services | Enhanced oil recovery from mature oil reserves |  |
| `259d7fb3-cd37-4616-82e5-35c609abc18f` | website / services | Environmental Design & Technical Advisory |  |
| `59eea124-2fa3-491c-8c3d-63f2c9530e18` | website / services | Environmental design consultancy and advisory services |  |
| `6757457e-cd88-4958-944c-2b3b4942e54c` | website / services | Impact evaluation of CSR intiatives |  |
| `5041c386-21cc-426c-99ef-295ce726eeee` | website / services | Multidisciplinary research and policy advice |  |
| `3625b53b-5299-43c4-9e55-06bbe3aab259` | website / services | Multidisciplinary research on natural resource conservation |  |
| `f387a567-cf91-4683-91ae-c431a037d49b` | website / services | Next generation technology to produce high-quality mycorrhiza |  |
| `70326006-9cc2-4e08-8f7b-55798dd65a51` | website / services | Policy intervention and analysis |  |
| `c6c0ebcf-2ac0-480a-965b-3a62e571e944` | website / services | Policy research on the role of resources in national and global sustainable development |  |
| `07ea5072-b97a-450b-99dd-95e535ee6685` | website / services | Policy, Strategic Planning & Advocacy |  |
| `d9879bf4-a934-41b1-b580-00459fbadc6e` | website / services | Project Monitoring Unit |  |
| `fa6999c0-c477-485d-8ce9-85409c1850d8` | website / services | Publication of academic and reference material |  |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `83010517-5e8d-43c8-8f79-64a30acf187f` | website / services | Research & development |  |
| `4eab067f-425a-4299-afee-f542e3a007f3` | website / services | Research, Innovation & Impact Assessment |  |
| `1535f84a-ac24-486d-ba8b-613113900325` | website / services | Resource conservation study/ energy audit/energy management programme |  |
| `fc7e7a2e-8914-4ae8-b214-3246272f5333` | website / services | Technology for reclaming wastelands |  |
| `c9fe4e63-cbf9-40c1-809f-bb6e1ba9b9f9` | website / services | Training & Capacity Building |  |
| `512bf0b0-01b9-4d38-8547-d894ffef2f43` | website / services | Water Positive Certification - Consulting, Audit and Certification Services |  |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `7f81af0f-d4fb-4ffd-9cd8-916e362ec0e3` | website / services | World Digital Library on Sustainable Development |  |
| `8937e1db-933e-45dc-80d3-80a0889f66cf` | website / page | Areas of Work | https://teriin.org/careers/areas-work |

**Notes**: expected_count = 30 service nodes. Note two service nodes carry near-identical titles about environmental design consultancy and two about natural-resource research, so a de-duplicated answer may legitimately name fewer distinct services.

---

### Q086 - What benefits can organizations gain from TERI's environmental design consultancy?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's environmental-design consultancy offers complete green design consultancy: site-planning inputs, full building performance analysis, evaluation of energy systems, renewable-energy integration, water and waste management strategies, and achieving indoor air-quality standards, with designs reviewed to incorporate energy efficiency into the building envelope and systems design. It uses a wide range of computation and simulation tools - DOE2, TRNSYS, ECOTECT, RADIANCE, FLOVENT, AGI32, LUMEN DESIGNER, BLAST, Phoenics, RETScreen - to assess the environmental and cost impact of design decisions. Its Environmental Design & Technical Advisory line adds emission inventories, life cycle assessments, logistics decarbonisation and sustainable mobility, and co-creates climate-responsive, inclusive and resilient infrastructure strategies with governments, public agencies and communities. So the benefits an organisation can expect are: quantified environmental AND cost impact of design choices, energy- and water-efficient buildings, renewable integration, indoor air-quality compliance, and support towards GRIHA/green certification.

**Expected facts**

- TERI provides complete green design consultancy including site-planning inputs, full building performance analysis, evaluation of energy systems, renewable-energy integration, water and waste management strategies, and achieving indoor air-quality standards.
- TERI reviews architects' designs to incorporate energy-efficiency measures in the building envelope and systems design.
- TERI uses DOE2, TRNSYS, ECOTECT, RADIANCE, FLOVENT, AGI32, LUMEN DESIGNER, BLAST, Phoenics and RETScreen to assess the environmental and cost impact of design decisions.
- TERI's Environmental Design & Technical Advisory expertise spans emission inventories, life cycle assessments, logistics decarbonisation and sustainable mobility.
- TERI co-creates climate-responsive, inclusive and resilient infrastructure strategies with governments, public agencies and communities.

**Expected entities**: DOE2, TRNSYS, ECOTECT, RADIANCE, FLOVENT, AGI32, LUMEN DESIGNER, BLAST, Phoenics, RETScreen

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `59eea124-2fa3-491c-8c3d-63f2c9530e18` | website / services | Environmental design consultancy and advisory services |  |
| `259d7fb3-cd37-4616-82e5-35c609abc18f` | website / services | Environmental Design & Technical Advisory |  |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `83010517-5e8d-43c8-8f79-64a30acf187f` | website / services | Research & development |  |

**Notes**: The 'benefits' framing is inferred from service-scope statements; TERI does not publish a benefits or ROI claim. An answer asserting quantified savings percentages would be unsupported.

---

### Q087 - Does TERI provide support for environmental impact assessments?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `70326006-9cc2-4e08-8f7b-55798dd65a51` | website / services | Policy intervention and analysis |  |
| `259d7fb3-cd37-4616-82e5-35c609abc18f` | website / services | Environmental Design & Technical Advisory |  |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |

**Notes**: NO EIA SERVICE DOCUMENTED. Title search for 'environmental impact assessment' / 'environmental clearance' across website nodes returns nothing, and none of the 30 service nodes offers EIA. The nearest evidence is oblique: the Policy intervention and analysis service states 'the manual for environmental clearance of large construction for the Ministry of Environment and Forests, Government of India has also been developed at CRSBS'; the Environmental Design & Technical Advisory service assesses 'environmental and economic impacts' of design using simulation tools; and third-party EIA work appears inside project PDFs (e.g. an ARIAS Society/APART environmental-impact-assessment section) that is not TERI's own offering. Whether TERI 'provides support for environmental impact assessments' cannot be established from the corpus.

---

### Q088 - How can TERI help organizations achieve resource efficiency?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI helps organisations achieve resource efficiency at three levels. Firm level: detailed energy, water and resource-efficiency audits with techno-economic recommendations backed by simulations and monitoring; plant-level energy audits and technology assessments; resource-conservation studies for buildings and complexes; water audits and quality testing with recommendations on water-saving fixtures, rainwater-harvesting potential and reuse of treated wastewater; and development and promotion of energy-efficient, environment-friendly technologies that let supply chains cut fuel use and improve environmental performance. Sector/value-chain level: resource-efficiency studies for the automobile sector and the electrical and electronic equipment value chain, and end-of-life-vehicle circularity work. System level: the integrated resource-efficiency policy roadmap for India, the Goa resource-efficiency and circular-economy strategy, the Indian Resource Panel, standards webinars, and business models for recycling and material-recovery infrastructure. Project Monitoring Units support state and local governments implementing ECBC/ECSBC.

**Expected facts**

- TERI conducts detailed energy, water and resource-efficiency audits across sectors with techno-economic recommendations backed by simulations and monitoring.
- TERI develops and promotes energy-efficient technologies and environment-friendly solutions so supply chains can reduce fuel consumption, use resources efficiently and improve environmental performance.
- TERI conducts water audits and quality testing including water-saving fixture recommendations, rainwater-harvesting potential and treated-wastewater reuse.
- TERI has done value-chain resource-efficiency studies for India's automobile sector and the electrical and electronic equipment value chain.
- TERI prepared an integrated resource-efficiency policy roadmap for India and the Goa resource-efficiency and circular-economy strategy.
- TERI manages Project Management Units supporting state and local governments implementing ECSBC/ECBC and climate-resilient policies.

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `89f45551-aaac-4e1a-8a95-5b1b9a43668c` | website / services | Audits, Validation & PMU Support |  |
| `1535f84a-ac24-486d-ba8b-613113900325` | website / services | Resource conservation study/ energy audit/energy management programme |  |
| `7358c7aa-b509-45f7-8d72-bc4a3417e172` | website / services | Energy performance benchmarking |  |
| `5b2ca2ff-da97-4ecc-b439-59fa03ff25c9` | website / services | Energy efficient and environment-friendly solutions |  |
| `3625b53b-5299-43c4-9e55-06bbe3aab259` | website / services | Multidisciplinary research on natural resource conservation |  |
| `d9879bf4-a934-41b1-b580-00459fbadc6e` | website / services | Project Monitoring Unit |  |
| `00d028f5-f0b3-4da3-8fb2-e73b86da455a` | website / completed_projects | Resource Efficiency Initiative: A detailed study on India's Automobile Sector | https://teriin.org/project/resource-efficiency-initiative-detailed-study-indias-automobile-sector |
| `536b446c-10b9-4374-a52c-4c659c4e3488` | website / research_papers | Maximising Resource Efficiency and Circularity in the Electrical and Electronic Equipment Value Chain and the  | https://teriin.org/research-paper/maximising-resource-efficiency-and-circularity-electrical-and-electronic-equipment |
| `f5665b91-78a8-497a-b0ca-6044e0974d97` | website / ongoing_projects | Creating an integrated resource efficiency policy for India - with public input | https://teriin.org/project/heres-your-chance-influence-indias-resource-efficiency-policy |
| `705f02f3-d402-4196-80a7-8832ea255d2c` | website / policy_brief | Strategy for fostering Resource Efficiency and Circular Economy in Goa | https://teriin.org/policy-brief/strategy-fostering-resource-efficiency-and-circular-economy-goa |

**Notes**: Overlaps Q058 and Q077; keep the three gold answers consistent.

---

### Q089 - What sustainability assessment tools are offered by TERI?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Sustainability assessment tools TERI offers or has developed: the GRIHA rating system (life-cycle environmental-performance evaluation of buildings, developed with MNRE in 2007) and the GRIHA Infrastructure Rating for logistics parks and warehouses; GRIHA Water Positive Certification with water audits; GHG calculators covering Scope 1, 2 and 3 emissions; the Freight Greenhouse Gas Calculator; the Green Port Performance Index (GPPI); the Green Budgeting Toolkit 2.0; the SDG Blueprint Tool for Sustainable Agriculture; the Vulnerability Index Tool for health vulnerability assessment; the Integrated Air Quality Index (AQI) and Liveability Framework; the MTCoE Daylight Plugin Tool; and a Transport Demand Management toolkit for city officials. TERI's climate-change risk assessment additionally provides climate projections, vulnerability and adaptation assessments and GHG inventorization using established models and an in-house super-computing facility.

**Expected facts**

- TERI developed the GRIHA rating system, which evaluates buildings' environmental performance over their entire life cycle, and a GRIHA Infrastructure Rating for logistics parks and warehouses.
- TERI offers GRIHA Water Positive Certification with water audits.
- TERI has developed GHG calculators covering Scope 1, 2 and 3 emissions, and a Freight Greenhouse Gas Calculator.
- TERI developed the Green Port Performance Index (GPPI).
- TERI developed the Green Budgeting Toolkit 2.0 and the SDG Blueprint Tool for Sustainable Agriculture.
- TERI developed a Vulnerability Index Tool for health vulnerability assessment.
- TERI launched the MTCoE Daylight Plugin Tool and produced a Transport Demand Management toolkit for city officials.

**Expected entities**: GRIHA, GRIHA Infrastructure Rating, GHG calculators, Freight Greenhouse Gas Calculator, Green Port Performance Index, Green Budgeting Toolkit 2.0, SDG Blueprint Tool for Sustainable Agriculture, Vulnerability Index Tool, Daylight Plugin Tool

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `3e27858c-18df-4866-b384-eda5efdd5154` | website / services | Ratings & Certification |  |
| `512bf0b0-01b9-4d38-8547-d894ffef2f43` | website / services | Water Positive Certification - Consulting, Audit and Certification Services |  |
| `4eab067f-425a-4299-afee-f542e3a007f3` | website / services | Research, Innovation & Impact Assessment |  |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |
| `98800b2a-5011-43be-ad73-6039b898ca8e` | website / events | LAUNCH OF GRIHA INFRASTRUCTURE RATING FOR LOGISTICS PARKS AND WAREHOUSES | https://teriin.org/event/launch-griha-infrastructure-rating-logistics-parks-and-warehouses |
| `0ab481b1-5840-49d7-a334-4083709d207a` | website / ongoing_projects | Freight Greenhouse Gas Calculator | https://teriin.org/project/freight-greenhouse-gas-calculator |
| `ea40133f-b34c-4ac7-b02b-0da92afb00ab` | website / policy_brief | Green Port Performance Index (GPPI) Measuring Progress, Powering Green Transformation | https://teriin.org/policy-brief/green-port-performance-index-gppi-measuring-progress-powering-green-transformation |
| `df038222-1e13-4bae-b7db-db6948f5aab7` | website / press_release | TERI Unveils Green Budgeting Toolkit 2.0 to Power Greener Public Finance and Drive the Green Economy | https://teriin.org/press-release/teri-unveils-green-budgeting-toolkit-20-power-greener-public-finance-and-drive-green |
| `2566f71f-afc8-4da2-8c40-253184d05591` | website / page | SDG Blueprint Tool for Sustainable Agriculture | https://teriin.org/SDG-Blueprint-tool-for-Sustainable-Agriculture |
| `da24182b-dd8a-4c14-af99-2edca57cde73` | website / article | Vulnerability Index Tool: Vulnerability assessment for health | https://teriin.org/article/vulnerability-index-tool-vulnerability-assessment-health |
| `6ca26c81-3a12-41ea-b138-4b19582c93b6` | website / article | WSDS2024: Launch of MTCoE’s Daylight Plugin Tool at the thematic session "Advancing Sustainable Building Pract | https://teriin.org/article/wsds2024-launch-mtcoes-daylight-plugin-tool-thematic-session-advancing-sustainable-building |
| `c402762d-53fc-4401-ace6-2bf25d5be8f3` | website / ongoing_projects | Development and Implementation of an Integrated Air Quality Index (AQI) and Liveability Framework for Krisala  | https://teriin.org/project/development-and-implementation-integrated-air-quality-index-aqi-and-liveability-framework |
| `e21323f5-0746-4575-b288-cea619f7c63b` | pdf_attachment / completed_projects | Download | https://teriin.org/project/preparation-toolkits-under-sustainable-urban-transport-project-ministry-urban-development |

**Notes**: Overlaps Q023 and Q060 by design; keep the three consistent. No consolidated tools catalogue exists, so completeness is not gradable.

---

### Q090 - What services does TERI's NABL-accredited laboratory provide?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI operates more than one NABL-accredited testing capability. Its 'Water, soil and sludge testing' service states: 'Accredited by the National Accreditation Board for Testing and Calibration Laboratories (NABL) we provide services to test water (ground, surface, and drinking water), soil, and sludge.' Its Air Quality Research service states it provides end-to-end air-quality and atmospheric-environment solutions through a NABL-accredited laboratory covering monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air-quality management planning. The Mahindra-TERI Centre of Excellence states its material-performance testing facility is NABL-accredited and uses ISO and ASTM standards to measure thermal properties (e.g. thermal conductivity per ISO 22007-2). TERI annual reports additionally record an EIB Laboratory NABL-accredited for water testing and hydrocarbon analysis, and a laboratory accredited as a NABL testing lab for packaged drinking water (per IS:14543) for some chemical parameters.

**Expected facts**

- TERI is accredited by the National Accreditation Board for Testing and Calibration Laboratories (NABL) and provides testing of water (ground, surface and drinking water), soil and sludge.
- TERI's Air Quality Research operates through a NABL-accredited laboratory covering monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air-quality management planning.
- The Mahindra-TERI Centre of Excellence's material-performance testing facility is NABL-accredited and uses ISO and ASTM standards to measure thermal properties, including thermal conductivity per ISO 22007-2.
- TERI's EIB Laboratory is NABL-accredited for water testing and hydrocarbon analysis.
- A TERI laboratory has been accredited as a NABL testing lab for testing of Packaged Drinking Water (per IS:14543) for some chemical parameters.

**Expected entities**: NABL, Water, soil and sludge testing, Air Quality Research laboratory, Mahindra-TERI Centre of Excellence, EIB Laboratory, IS:14543

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `e697e316-850e-4ad0-b37e-f42bc83d60d0` | website / page | Mahindra-TERI Centre of Excellence | https://teriin.org/Mahindra-TERI-centre-of-excellence |
| `db669bde-858c-478b-9751-fb148d2ecfb4` | website / page | Annual Reports | https://teriin.org/annual-reports |
| `e071ea2f-4ea8-4d9a-b101-42a037155282` | website / page | Brochures | https://teriin.org/brochures |
| `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2` | pdf_attachment / page | Annual Reports | https://teriin.org/annual-reports |

**Notes**: The question presumes ONE NABL-accredited laboratory. The corpus shows at least four distinct NABL-accredited TERI capabilities (water/soil/sludge, air quality, Mahindra-TERI materials/thermal, EIB water & hydrocarbon) plus a packaged-drinking-water scope, with no consolidated laboratory services catalogue and no accreditation certificate numbers or scope documents. A grader should accept an answer scoped to any one of these as correct-but-partial, and should not penalise an answer that says TERI has several accredited facilities.

---

### Q091 - Can TERI conduct air quality testing and monitoring?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI's Air Quality Research provides end-to-end air-quality and atmospheric-environment solutions through its NABL-accredited laboratory, covering monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air-quality management planning at urban, regional and national scales, plus policy and decision-support systems, environmental-compensation assessment, third-party audits, sustainable residue management, pilot demonstrations of emission-reduction technologies and capacity building. In project work TERI has carried 24-hourly PM2.5 and PM10 monitoring across summer and winter seasons using its NABL-accredited laboratory, and has run city-scale emission-inventory, source-apportionment and carrying-capacity studies and pollution-hotspot identification through dispersion modelling.

**Expected facts**

- TERI provides air-quality monitoring through a NABL-accredited laboratory.
- TERI's air-quality services cover monitoring, emissions assessment, source apportionment, forecasting, impact evaluation and air-quality management planning at urban, regional and national scales.
- TERI's air-quality services also include third-party audits, environmental-compensation assessment and pilot demonstrations of emission-reduction technologies.
- In project work TERI has undertaken 24-hourly PM2.5 and PM10 monitoring during summer and winter seasons, stating that TERI has a NABL-accredited laboratory for the purpose.
- TERI identifies pollution hotspot locations through dispersion modelling.

**Expected entities**: NABL, PM2.5, PM10, source apportionment, dispersion modelling

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `cc1a9a1f-d3d1-416a-8a17-20ba060bea9a` | website / completed_projects | Air Pollution Emission Inventory, Source Apportionment and Atmospheric Carrying Capacity Study of the Howrah C | https://teriin.org/project/air-pollution-emission-inventory-source-apportionment-and-atmospheric-carrying-capacity |
| `2d89854d-19d9-4c61-83b2-5777dbc5cebc` | website / completed_projects | Air Pollution Emissions Inventory, Source Apportionment and Atmospheric Carrying Capacity Study of Kolkata in  | https://teriin.org/project/air-pollution-emissions-inventory-source-apportionment-and-atmospheric-carrying-capacity |
| `71154b8c-76b1-4777-82f6-76a67a94d850` | website / ongoing_projects | Emission inventories, Source apportionment studies and carrying capacity study for different cities in India | https://teriin.org/project/emission-inventories-source-apportionment-studies-and-carrying-capacity-study-different |

---

### Q092 - What water quality testing services are available?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI's NABL-accredited testing service covers water - ground, surface and drinking water - alongside soil and sludge. Separately, TERI conducts water audits and quality testing that typically include estimation of building water use, recommendations on water-saving fixtures, estimation of landscape water demand (soft areas, plant-species and climatic factors), estimation of rainwater-harvesting potential, and recommendations on reuse and recycling of treated wastewater and rainwater plus appropriate wastewater-management schemes and systems. Water audits are also part of GRIHA Water Positive Certification. TERI annual reports additionally record NABL accreditation for packaged drinking water testing (per IS:14543) for some chemical parameters, testing of water, food and beverages for chemical, microbial and elemental parameters, and an EIB Laboratory accredited for water testing and hydrocarbon analysis.

**Expected facts**

- TERI, accredited by NABL, provides testing of water including ground water, surface water and drinking water.
- TERI conducts water audits and quality testing that include estimation of building water use, recommendations of water-saving fixtures, estimation of landscape water demand, estimation of rainwater-harvesting potential, and recommendations on reuse and recycling of treated wastewater and rainwater.
- Water audits are part of TERI's GRIHA Water Positive Certification service.
- A TERI laboratory holds NABL accreditation for testing of Packaged Drinking Water (per IS:14543) for some chemical parameters and tests water, food and beverages for chemical, microbial and elemental parameters.
- TERI's EIB Laboratory is NABL-accredited for water testing and hydrocarbon analysis.

**Expected entities**: NABL, IS:14543, GRIHA Water Positive Certification, EIB Laboratory

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `3625b53b-5299-43c4-9e55-06bbe3aab259` | website / services | Multidisciplinary research on natural resource conservation |  |
| `512bf0b0-01b9-4d38-8547-d894ffef2f43` | website / services | Water Positive Certification - Consulting, Audit and Certification Services |  |
| `7b06dc9b-2597-4939-8e90-44cdb2cd1ebc` | website / page | Water Positive Certification - Consulting, Audit and Certification Services | https://teriin.org/services/habitat/water-positive-certification |
| `db669bde-858c-478b-9751-fb148d2ecfb4` | website / page | Annual Reports | https://teriin.org/annual-reports |
| `e071ea2f-4ea8-4d9a-b101-42a037155282` | website / page | Brochures | https://teriin.org/brochures |
| `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2` | pdf_attachment / page | Annual Reports | https://teriin.org/annual-reports |

**Notes**: No published parameter list, price list or turnaround time; an answer must not invent one.

---

### Q093 - Does TERI offer soil testing and environmental analysis?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes for soil. TERI's NABL-accredited testing service provides testing of soil (alongside water and sludge). Related environmental-analysis capability documented elsewhere: air-quality monitoring and analysis through a NABL-accredited laboratory; thermal and material-performance testing at the Mahindra-TERI Centre of Excellence to ISO and ASTM standards; water, food and beverage testing for chemical, microbial and elemental parameters; hydrocarbon analysis at the EIB Laboratory; and soil-health work under TERI's mycorrhizal biofertiliser and wasteland-reclamation programmes.

**Expected facts**

- TERI, accredited by NABL, provides testing of soil, along with water and sludge.
- TERI's related environmental-analysis capability includes air-quality monitoring and analysis through a NABL-accredited laboratory.
- TERI tests water, food and beverages for chemical, microbial and elemental parameters and performs hydrocarbon analysis at its EIB Laboratory.
- The Mahindra-TERI Centre of Excellence performs material and thermal performance testing to ISO and ASTM standards under NABL accreditation.

**Expected entities**: NABL, soil testing, EIB Laboratory, Mahindra-TERI Centre of Excellence

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `e697e316-850e-4ad0-b37e-f42bc83d60d0` | website / page | Mahindra-TERI Centre of Excellence | https://teriin.org/Mahindra-TERI-centre-of-excellence |
| `db669bde-858c-478b-9751-fb148d2ecfb4` | website / page | Annual Reports | https://teriin.org/annual-reports |
| `f387a567-cf91-4683-91ae-c431a037d49b` | website / services | Next generation technology to produce high-quality mycorrhiza |  |
| `fc7e7a2e-8914-4ae8-b214-3246272f5333` | website / services | Technology for reclaming wastelands |  |
| `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2` | pdf_attachment / page | Annual Reports | https://teriin.org/annual-reports |

**Notes**: The soil half is HIGH-confidence and verbatim. 'Environmental analysis' is broader than anything the corpus scopes, so the second half of the gold answer is an assembly across sources; score the soil claim strictly and the rest leniently.

---

### Q094 - How can organizations utilize TERI's laboratory facilities?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `e697e316-850e-4ad0-b37e-f42bc83d60d0` | website / page | Mahindra-TERI Centre of Excellence | https://teriin.org/Mahindra-TERI-centre-of-excellence |
| `0031cf62-fcb1-46a6-b4df-cdefdfe62aa6` | website / page | KRC Services | https://teriin.org/krc-services |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |

**Notes**: NO ACCESS PROCESS DOCUMENTED. The corpus states WHAT the laboratories test (water, soil, sludge; air quality; materials/thermal properties) but nowhere states HOW an external organisation engages them: no sample-submission procedure, application form, laboratory contact person, price list, turnaround time or terms. By contrast the LIBRARY (KRC) does publish a membership route (membership open to researchers, NGO staff, government officials, corporate employees, students, teachers, consultants and policy-makers; forms at the library help desk or downloadable), which is an adjacent but different facility. A human must decide whether 'contact mailbox@teri.res.in' is an acceptable gold answer.

---

### Q095 - What analytical capabilities are available through TERI's testing laboratories?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Analytical capabilities documented across TERI's testing facilities: water testing (ground, surface and drinking water), soil testing and sludge testing under NABL accreditation; packaged drinking water testing per IS:14543 for some chemical parameters, and testing of water, food and beverages for chemical, microbial and elemental parameters; hydrocarbon analysis and water testing at the NABL-accredited EIB Laboratory; air-quality monitoring and analysis including 24-hourly PM2.5 and PM10 measurement, emissions assessment, source apportionment and dispersion modelling through a NABL-accredited laboratory; and material-performance testing at the Mahindra-TERI Centre of Excellence, NABL-accredited and using ISO and ASTM standards to measure thermal properties under controlled laboratory conditions (including thermal conductivity per ISO 22007-2).

**Expected facts**

- TERI's NABL-accredited testing covers water (ground, surface, drinking), soil and sludge.
- A TERI laboratory is NABL-accredited for packaged drinking water testing (IS:14543) for some chemical parameters and tests water, food and beverages for chemical, microbial and elemental parameters.
- TERI's EIB Laboratory is NABL-accredited for water testing and hydrocarbon analysis.
- TERI's air-quality analytical capability includes 24-hourly PM2.5 and PM10 monitoring, emissions assessment, source apportionment and dispersion modelling through a NABL-accredited laboratory.
- The Mahindra-TERI Centre of Excellence's NABL-accredited facility measures thermal properties using ISO and ASTM standards, including thermal conductivity per ISO 22007-2.

**Expected entities**: NABL, IS:14543, ISO 22007-2, ASTM, EIB Laboratory, PM2.5, PM10

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `8d783c0b-9097-4586-887f-f206c4775f87` | website / services | Water, soil and sludge testing |  |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `e697e316-850e-4ad0-b37e-f42bc83d60d0` | website / page | Mahindra-TERI Centre of Excellence | https://teriin.org/Mahindra-TERI-centre-of-excellence |
| `db669bde-858c-478b-9751-fb148d2ecfb4` | website / page | Annual Reports | https://teriin.org/annual-reports |
| `e071ea2f-4ea8-4d9a-b101-42a037155282` | website / page | Brochures | https://teriin.org/brochures |
| `cc1a9a1f-d3d1-416a-8a17-20ba060bea9a` | website / completed_projects | Air Pollution Emission Inventory, Source Apportionment and Atmospheric Carrying Capacity Study of the Howrah C | https://teriin.org/project/air-pollution-emission-inventory-source-apportionment-and-atmospheric-carrying-capacity |
| `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2` | pdf_attachment / page | Annual Reports | https://teriin.org/annual-reports |

**Notes**: Assembled across service nodes, a Centre-of-Excellence page, brochures and annual-report PDFs; there is no single laboratory-capability statement, so the parameter list is not exhaustive.

---

### Q096 - What training programmes and workshops does TERI offer?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: narrative/summary
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI runs training and capacity-building for professionals, officials and communities. Its Training & Capacity Building service targets architects, building developers and service engineers on topics including Green & Resource Efficient Developments, Construction Site Planning and Management - A GRIHA Approach, Resource Efficiency (Energy & water) in the Building Sector, Smart Cities/Urban Infrastructure, Green Construction, Disaster Management & Mitigation, Energy Conservation in Buildings, Construction & Demolition Waste Management, Zero Discharge Campus development, Solid Waste Management, Green Building Rating Systems in the Indian Context, Low Cooling Technologies, Net Zero Energy Buildings, ECBC compliance using whole-building performance method (eQUEST energy simulation), lighting and building automation with hands-on DIAlux training, HVAC and refrigeration, Green Cooling Technologies, O&M guidelines and Green Supply Chain; TERI states over 10,000 architects, developers and engineers have gone through these programmes, refresher courses, seminars and workshops. Its Capacity Building & Knowledge Dissemination service adds technical trainings, policy dialogues, e-courses, public engagements and academic partnerships. It also runs TERI-ITEC international courses, sectoral trainings (integrated watershed management, air-quality management for pollution control boards, biogas project risks, BESS, carbon-stock assessment, green shipping PtX), skilling programmes (Future-In-Charge for EV charging), and youth workshops (Innovate4Environment).

**Expected facts**

- TERI conducts capacity building for architects, building developers and service engineers across a long list of named green-building, energy-efficiency and waste topics.
- TERI states over 10,000 architects, developers and engineers have undergone its training programmes, refresher courses, seminars and workshops in green buildings, energy efficiency and sustainability of the built environment.
- TERI's training includes hands-on software training on energy simulation and DIAlux lighting design and ECBC compliance using the whole-building performance method.
- TERI's Capacity Building & Knowledge Dissemination service engages architects, engineers, urban planners and policy makers through capacity-building programmes, technical trainings, policy dialogues, e-courses, public engagements and academic partnerships.
- TERI runs TERI-ITEC international training courses.
- TERI runs sectoral trainings including Climate Resilient Integrated Watershed Management, ambient air-quality management for pollution control boards, biogas project risk, Battery Energy Storage Systems, carbon-stock assessment and green shipping PtX.
- TERI runs skilling programmes such as Future-In-Charge for EV charging and youth workshops under Innovate4Environment.

**Expected entities**: Training & Capacity Building, TERI-ITEC, Future-In-Charge, Innovate4Environment, GRIHA, ECBC, DIAlux

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c9fe4e63-cbf9-40c1-809f-bb6e1ba9b9f9` | website / services | Training & Capacity Building |  |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |
| `53f7bd72-fcb9-42e3-8336-1733575e2705` | website / events | Training on Climate Resilient Integrated Watershed Management | https://teriin.org/event/training-climate-resilient-integrated-watershed-management |
| `741c7814-09ea-4292-8885-c0ff3cb5876b` | website / events | Capacity building training program for the officials of West Bengal Pollution Control Board on ‘emission inven | https://teriin.org/event/capacity-building-training-program-officials-west-bengal-pollution-control-board-emission |
| `a31917b0-9e32-4485-869e-47f3b23b57a6` | website / events | Capacity Building Program on BESS | https://teriin.org/event/capacity-building-program-bess |
| `43fd3871-deac-4474-bea9-ee44903a988c` | website / events | Capacity Building for Carbon Stock Assessment and Monitoring | https://teriin.org/event/capacity-building-carbon-stock-assessment-and-monitoring |
| `70692bad-8f3a-4924-b860-72a159c25ad8` | website / events | Advancing Green Shipping: Highlights PtX Green Shipping Training Workshop | https://teriin.org/event/advancing-green-shipping-highlights-ptx-green-shipping-training-workshop |
| `53af300b-96d8-4ac2-a056-aa49118f4937` | website / press_release | TERI Launches ‘Future-In-Charge’ Phase 2 in Bengaluru to Power India’s EV Charging Workforce | https://teriin.org/press-release/teri-launches-future-charge-phase-2-bengaluru-power-indias-ev-charging-workforce |
| `1030c58b-7ed1-42ee-9e55-40dab2291408` | website / press_release | TERI Inaugurates Innovate4Environment Workshop in Bengaluru to Build Youth Capacity in Data Analytics for Sust | https://teriin.org/press-release/teri-inaugurates-innovate4environment-workshop-bengaluru-build-youth-capacity-data |
| `a7b108ed-43cb-4a75-8665-58ccd40154c1` | website / completed_projects | TERI-ITEC International Training Programme on Renewable Energy and Energy Efficiency (REEE) | https://teriin.org/project/teri-itec-international-training-programme-renewable-energy-and-energy-efficiency-reee |

---

### Q097 - Are there any upcoming TERI training programmes?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: current-state / count
- **Temporal scope**: temporal_mode=current / point-in-time; requested_period=after 2026-08-19; expected_validity_window=field_event_start_date >= 2026-08-19; expected_claims_during_period=3 events, 0 training programmes

**Gold answer**

> As of the corpus snapshot (events indexed to 2026-08-18, today 2026-08-19) only three events have a start date on or after 19 August 2026, and none of them is a training programme: the Darbari Seth Memorial Lecture 2026 (21 August 2026 IST, Stein Auditorium, India Habitat Centre, New Delhi); the UNCCD COP17 Green Zone Finance Day panel on 'Digital MRV & Carbon Finance' (24 August 2026); and the WCEF2026 Accelerator Session on Circular Public Procurement and Ecolabels (18 September 2026). The correct answer is therefore that the corpus lists no upcoming training programme, only these three upcoming events, and that a user should check TERI's Announcements and Events pages for new listings.

**Expected facts**

- Only three TERI events in the corpus have a start date on or after 19 August 2026.
- None of those three upcoming events is a training programme.
- Darbari Seth Memorial Lecture 2026 is scheduled for 21 August 2026 IST (field_event_start_date 2026-08-20T22:00Z, end 2026-08-21T17:00+05:30) at Stein Auditorium, India Habitat Centre, New Delhi.
- A UNCCD COP17 Green Zone Finance Day panel on 'Digital MRV & Carbon Finance' is scheduled for 24 August 2026.
- A WCEF2026 Accelerator Session on Circular Public Procurement and Ecolabels is scheduled for 18 September 2026.

**Expected entities**: Darbari Seth Memorial Lecture 2026, UNCCD COP17, WCEF2026

**Reproducible derivations**

- `SELECT document_id,title,field_event_start_date FROM documents WHERE bundle='events' AND source_type='website' AND JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_event_start_date')) >= '2026-08-19' -> 3 rows`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `3c24d94b-f8bb-4475-b147-56dd0c35318f` | website / events | Darbari Seth Memorial Lecture 2026 | https://teriin.org/event/darbari-seth-memorial-lecture-2026 |
| `31826b5d-c4be-4f1c-a291-c9d647ce8d3c` | website / events | UNCCD COP17 Green Zone Finance Day Panel on “Digital MRV & Carbon Finance” | https://teriin.org/event/unccd-cop17-green-zone-finance-day-panel-digital-mrv-carbon-finance |
| `c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1` | website / events | WCEF2026 Accelerator Session: Circular Public Procurement and Ecolabels | https://teriin.org/event/wcef2026-accelerator-session-circular-public-procurement-and-ecolabels |
| `64b3242e-5578-4ff5-acd9-f9aaa1377ecf` | website / page | Announcements | https://teriin.org/announcements |

**Notes**: expected_count = 0 upcoming training programmes (3 upcoming events). This is a snapshot-relative answer and will change with re-ingestion; the evaluation must fix the reference date. Note TERI training programmes are frequently advertised outside the events bundle (e.g. brochures, announcements), so 'zero' means 'none listed in the ingested events with a future start date', not 'TERI is running no training'.

---

### Q098 - Does TERI offer online learning and certification programmes?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual / aggregation
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. Documented online and certification programmes: the e-Certificate Course on Mainstreaming Urban Climate Action, launched in September 2021 as the first international e-certificate course of its kind; the Online Training and Capacity Building (OTCB) Certificate Programme on Developing Treated Wastewater Reuse (2021); a Certificate Course in 'Sustain and Enhance Technical Knowledge in Solar Energy Systems' at Guwahati; and a three-month ESG certification programme launched with NDTV in August 2025 (also described as an ESG Certification Program by TERI-NDTV). TERI's Capacity Building & Knowledge Dissemination service states it promotes its topics through e-courses, public engagements and academic partnerships. A Corporate Sustainability Leadership Programme 2026 focused on ESG, AI and carbon was also unveiled.

**Expected facts**

- TERI launched the e-Certificate Course on Mainstreaming Urban Climate Action in September 2021, described as the first international e-certificate course of its kind.
- TERI ran an Online Training and Capacity Building (OTCB) Certificate Programme on Developing Treated Wastewater Reuse.
- TERI ran a Certificate Course in 'Sustain and Enhance Technical Knowledge in Solar Energy Systems' at Guwahati.
- TERI, in partnership with NDTV, launched a three-month ESG certification programme in August 2025.
- TERI's Capacity Building & Knowledge Dissemination service delivers e-courses alongside public engagements and academic partnerships.
- TERI unveiled a Corporate Sustainability Leadership Programme 2026 focused on ESG, AI and carbon.

**Expected entities**: e-Certificate Course on Mainstreaming Urban Climate Action, OTCB Certificate Programme, ESG certification programme, NDTV, Corporate Sustainability Leadership Programme 2026

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `6960e619-2187-4622-9e1a-1543792246fb` | website / completed_projects | e-Certificate Course on Mainstreaming Urban Climate Action | https://teriin.org/project/e-certificate-course-mainstreaming-urban-climate-action |
| `04a01dce-1077-4c64-bf0b-7dbed4389716` | website / press_release | First International E-Certificate Course on Mainstreaming Urban Climate Action Launched by Key Institutions | https://teriin.org/press-release/first-international-e-certificate-course-mainstreaming-urban-climate-action-launched |
| `99a32adc-0862-4b63-bb64-f56cbce8dec3` | website / events | Launch of e-Certificate Course on Mainstreaming Urban Climate Action | https://teriin.org/event/launch-e-certificate-course-mainstreaming-urban-climate-action |
| `91a23556-09b0-4f3b-9e99-bce615a25f21` | website / events | Online Training and Capacity Building (OTCB) Certificate Programme: Developing Treated Wastewater Reuse Facili | https://teriin.org/event/online-training-and-capacity-building-otcb-certificate-programme-developing-treated |
| `78fcc956-e94c-4f8c-a9ec-13997907c4dd` | website / ongoing_projects | Certificate course in "Sustain and Enhance Technical Knowledge in Solar Energy Systems" at Guwahati, Assam und | https://teriin.org/project/certificate-course-sustain-and-enhance-technical-knowledge-solar-energy-systems-guwahati |
| `bd80d6c7-4c68-4fe9-9c8b-40d1ae6ca7d8` | website / events | TERI in partnership with NDTV launches the 3-month ESG certification programme | https://teriin.org/event/teri-partnership-ndtv-launches-3-month-esg-certification-programme |
| `780f0ff3-1147-477e-a7a5-bf2bea594df1` | pdf_attachment / events | ESG Certification Program by TERI NDTV | https://teriin.org/event/esg-works-turning-responsibility-results |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |
| `a5dc7df0-aa12-4a0d-8f33-32c8a7709012` | website / press_release | TERI Unveils Corporate Sustainability Leadership Programme 2026 Focused on ESG, AI, and Carbon Markets | https://teriin.org/press-release/teri-unveils-corporate-sustainability-leadership-programme-2026-focused-esg-ai-and |

**Notes**: These are individual programme records, not a current course catalogue; the corpus does not establish which are open for enrolment now. An answer must not present them as currently available.

---

### Q099 - Are certificates awarded upon successful completion of TERI programmes?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes, in the cases the corpus documents. For internships, TERI 'awards a certificate at the end of the term' and the supervisor completes an evaluation form provided by the intern's institution, with the intern expected to submit a report and, if possible, make a presentation. TERI also runs explicitly certificate-bearing programmes - the e-Certificate Course on Mainstreaming Urban Climate Action, the Online Training and Capacity Building (OTCB) Certificate Programme on treated wastewater reuse, a Certificate Course on solar energy systems at Guwahati, and a three-month ESG certification programme with NDTV - whose names indicate certification on completion.

**Expected facts**

- TERI awards a certificate at the end of an internship term, and the supervisor fills in an evaluation form provided by the intern's institution.
- Interns are expected to submit a report to their supervisor at the end of the internship and make a presentation if possible.
- TERI runs certificate-bearing programmes including the e-Certificate Course on Mainstreaming Urban Climate Action, the OTCB Certificate Programme on developing treated wastewater reuse, a certificate course on solar energy systems, and a three-month ESG certification programme with NDTV.

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `48b331a3-2631-4f58-b5ba-e7673163c893` | website / page | Internship | https://teriin.org/careers/internship |
| `6960e619-2187-4622-9e1a-1543792246fb` | website / completed_projects | e-Certificate Course on Mainstreaming Urban Climate Action | https://teriin.org/project/e-certificate-course-mainstreaming-urban-climate-action |
| `91a23556-09b0-4f3b-9e99-bce615a25f21` | website / events | Online Training and Capacity Building (OTCB) Certificate Programme: Developing Treated Wastewater Reuse Facili | https://teriin.org/event/online-training-and-capacity-building-otcb-certificate-programme-developing-treated |
| `78fcc956-e94c-4f8c-a9ec-13997907c4dd` | website / ongoing_projects | Certificate course in "Sustain and Enhance Technical Knowledge in Solar Energy Systems" at Guwahati, Assam und | https://teriin.org/project/certificate-course-sustain-and-enhance-technical-knowledge-solar-energy-systems-guwahati |
| `bd80d6c7-4c68-4fe9-9c8b-40d1ae6ca7d8` | website / events | TERI in partnership with NDTV launches the 3-month ESG certification programme | https://teriin.org/event/teri-partnership-ndtv-launches-3-month-esg-certification-programme |

**Notes**: The internship certificate statement is verbatim and unambiguous. For training programmes generally the corpus gives no blanket certification policy - only programme titles that include 'certificate' or 'certification'. An answer asserting that ALL TERI programmes award certificates would be unsupported.

---

### Q100 - Does TERI provide capacity-building programmes for government officials?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual / aggregation
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. Documented capacity building for government officials: a Training Programme for IAS officers on Regulation and reforms in Infrastructure sectors (2008); refresher courses for Indian Forest Service officers, including a 5-day refresher course on Environment Economics and Accounting, a one-week refresher course on Carbon-Based Forest Financing, and training on developing Project Design Documents for forestry Clean Development Mechanism projects; capacity-building training for officials of the West Bengal Pollution Control Board and a Capacity Building Program on Ambient Air Quality Management in Kolkata; Solid Waste Management exposure workshops for officials of Urban Local Bodies and elected representatives under the Swachh Bharat Mission (Urban); a training programme strengthening municipal staff for a cleaner and greener Lucknow; international training under a Capacity Building Program in the power sector for departmental officials; training on Climate Resilient Integrated Watershed Management with the State Level Nodal Agency; and a policy brief on 'Capacity Needs of Government Officials for Integration of Energy and Human Development'. TERI also manages Project Management Units embedded with state and local governments (Sustainable Habitat cell in Vijayawada; ECBC cells in Odisha, Punjab and Haryana).

**Expected facts**

- TERI ran a Training Programme for IAS officers on Regulation and reforms in Infrastructure sectors (2008).
- TERI runs refresher courses for Indian Forest Service (IFS) officers, including on Environment Economics and Accounting, Carbon-Based Forest Financing, and Project Design Documents for forestry CDM projects.
- TERI ran capacity-building training for officials of the West Bengal Pollution Control Board and a Capacity Building Program on Ambient Air Quality Management in Kolkata.
- TERI ran Solid Waste Management exposure workshops for officials of Urban Local Bodies and elected representatives under the Swachh Bharat Mission (Urban).
- TERI ran a training programme to strengthen municipal staff for a cleaner and greener Lucknow.
- TERI delivered international training under a 'Capacity Building Program' in the power sector for departmental officials.
- TERI and the State Level Nodal Agency hosted training on Climate Resilient Integrated Watershed Management.
- TERI manages Project Management Units with state and local governments, including a Sustainable Habitat cell in Vijayawada and ECBC cells in Odisha, Punjab and Haryana.

**Expected entities**: IAS officers, IFS officers, West Bengal Pollution Control Board, Urban Local Bodies, Swachh Bharat Mission (Urban), State Level Nodal Agency, ECBC cells

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `b2896232-c1bd-4a21-a5b0-697848e78561` | website / completed_projects | Training Programme for IAS officers on Regulation and reforms in Infrastructure sectors, 2008 | https://teriin.org/project/training-programme-ias-officers-regulation-and-reforms-infrastructure-sectors-2008 |
| `02050839-2ae3-4593-ae11-6f94014c1b83` | website / ongoing_projects | Organizing 5 day refresher course for IFS officers on the topic "Environment Economics and Accounting, Green G | https://teriin.org/project/organizing-5-day-refresher-course-ifs-officers-topic-environment-economics-and-accounting |
| `31844de8-4093-4f6c-9584-da37f9743450` | website / events | Carbon-Based Forest Financing - One Week Refresher Training Course for IFS Officers | https://teriin.org/event/carbon-based-forest-financing-one-week-refresher-training-course-ifs-officers |
| `194e7e28-138b-43a5-ad75-e89bf8bfac6b` | website / completed_projects | Training for IFS officers on Development of Project Design Document (PDD) for Forestry Clean Development Mecha | https://teriin.org/project/training-ifs-officers-development-project-design-document-pdd-forestry-clean-development |
| `741c7814-09ea-4292-8885-c0ff3cb5876b` | website / events | Capacity building training program for the officials of West Bengal Pollution Control Board on ‘emission inven | https://teriin.org/event/capacity-building-training-program-officials-west-bengal-pollution-control-board-emission |
| `6cda5963-88bd-4d3b-b75a-7ca878ff716e` | website / events | Capacity Building Program on Ambient Air Quality Management in Kolkata | https://teriin.org/event/capacity-building-program-ambient-air-quality-management-kolkata |
| `0060215e-5af6-418b-93dd-eaf883e82eae` | website / ongoing_projects | Solid waste management exposure workshops for the officials of  ULBs and elected representatives under Swachh  | https://teriin.org/project/solid-waste-management-exposure-workshops-officials-ulbs-and-elected-representatives-under |
| `712ba1c8-5514-4f3f-a9d0-a071f6214c7a` | website / ongoing_projects | Strengthening Municipal Staff for Cleaner and Greener Lucknow: TERI's Innovative Training Program on Mechanica | https://teriin.org/project/strengthening-municipal-staff-cleaner-and-greener-lucknow-teris-innovative-training-program |
| `77c52af9-e5e4-43f1-b1ae-3b97250d4658` | website / ongoing_projects | International Training under 'Capacity Building Program' in Power Sector for officials of Department of Power, | https://teriin.org/project/international-training-under-capacity-building-program-power-sector-officials-department |
| `c2a3ebd9-86ff-4d7b-ba06-d7c0089fd97e` | website / press_release | TERI Hosts Training on Climate Resilient Integrated Watershed Management in Collaboration with SLNA, Governmen | https://teriin.org/press-release/teri-hosts-training-climate-resilient-integrated-watershed-management-collaboration |
| `39221d9f-8c45-4da4-a8ae-be394a7356b7` | website / policy_brief | Capacity Needs of Government Officials for Integration of Energy and Human Development | https://teriin.org/policy-brief/capacity-needs-government-officials-integration-energy-and-human-development |
| `d9879bf4-a934-41b1-b580-00459fbadc6e` | website / services | Project Monitoring Unit |  |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |

**Notes**: Strong and varied evidence, but most named programmes are historical (2008-2025); the corpus does not establish a current standing offer for government officials.

---

### Q101 - Does TERI conduct training programmes for NGOs and civil society organizations?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c8b08727-3532-4cd7-9465-2bbabcba8e9e` | website / press_release | TERI in association with IISD conducts a Civil Society workshop on 'Reforming Energy Subsidies in India' | https://teriin.org/press-release/teri-association-iisd-conducts-civil-society-workshop-reforming-energy-subsidies |
| `821c8896-1c89-4118-b9f3-f0fc49bf19c6` | website / article | Evaluation and Rating of NGOs | https://teriin.org/article/evaluation-and-rating-ngos |
| `0031cf62-fcb1-46a6-b4df-cdefdfe62aa6` | website / page | KRC Services | https://teriin.org/krc-services |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |

**Notes**: EVIDENCE TOO THIN. The corpus contains only: a 2018 civil-society workshop on 'Reforming Energy Subsidies' conducted with IISD; an article 'Evaluation and Rating of NGOs'; and the KRC library statement that membership is open to 'staff of non-governmental organizations' among others. TERI's Capacity Building service lists architects, engineers, urban planners and policy makers as its audiences - not NGOs or civil-society organisations. There is no NGO/civil-society training programme documented, so neither 'yes' nor 'no' can be gold. A human must decide.

---

### Q102 - What international training programmes are conducted by TERI?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Yes. TERI's principal international training vehicle is the TERI-ITEC courses run under the Indian Technical and Economic Cooperation programme, spanning at least 2013-14 to 2017-18, with courses including Energy Access and Human Development; Decentralised energy solutions - planning and implementation; Climate change and sustainability; Trade and sustainable development - issues for developing countries; Resource security and governance issues; Renewable Energy and Energy Efficiency (also run as the TERI-ITEC International Training Programme on Renewable Energy and Energy Efficiency, REEE); Applications of Biotechnology and its Regulation; Mainstreaming Sustainable Development; and an Integrated approach towards sustainable development. Other international training: international training under a Capacity Building Program in the power sector for foreign departmental officials; short-term external training and experience-sharing study visits on biogas development for an Ethiopian delegation; the first international e-Certificate Course on Mainstreaming Urban Climate Action (2021); a TERI-DST training programme on Green Growth for Sustainable Development; and Innovate4Environment UK-India youth workshops with the British Council and the University of Warwick.

**Expected facts**

- TERI runs TERI-ITEC courses under the Indian Technical and Economic Cooperation programme, documented across 2013-14 to 2017-18 cycles.
- TERI-ITEC course topics include Energy Access and Human Development, Decentralised energy solutions, Climate change and sustainability, Trade and sustainable development, Resource security and governance, Renewable Energy and Energy Efficiency, Applications of Biotechnology and its Regulation, Mainstreaming Sustainable Development, and an Integrated approach towards sustainable development.
- TERI ran the TERI-ITEC International Training Programme on Renewable Energy and Energy Efficiency (REEE).
- TERI delivered international training under a Capacity Building Program in the power sector for departmental officials.
- TERI ran short-term external training and experience-sharing study visits on biogas development for an Ethiopian delegation.
- TERI launched the first international e-Certificate Course on Mainstreaming Urban Climate Action (2021).
- TERI runs Innovate4Environment UK-India youth workshops with the British Council and the University of Warwick.

**Expected entities**: TERI-ITEC, Indian Technical and Economic Cooperation, REEE, British Council, University of Warwick, Innovate4Environment

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `a7b108ed-43cb-4a75-8665-58ccd40154c1` | website / completed_projects | TERI-ITEC International Training Programme on Renewable Energy and Energy Efficiency (REEE) | https://teriin.org/project/teri-itec-international-training-programme-renewable-energy-and-energy-efficiency-reee |
| `019cfabf-7eec-4fe0-89d8-5a77f8dea786` | website / events | TERI-ITEC Courses 2013-14 Course II - Decentralised energy solutions - planning and implementation | https://teriin.org/event/teri-itec-courses-2013-14-course-ii-decentralised-energy-solutions-planning-and |
| `6dd63f36-decd-4e84-9e88-bec173f69cc2` | website / events | TERI-ITEC Courses 2014-15  Course I - Energy Access and Human Development | https://teriin.org/event/teri-itec-courses-2014-15-course-i-energy-access-and-human-development |
| `02a1f5a3-1663-4e28-8d65-3f06b42622ed` | website / events | TERI-ITEC Courses 2016-17: Course IV - Applications of Biotechnology and its Regulation | https://teriin.org/event/teri-itec-courses-2016-17-course-iv-applications-biotechnology-and-its-regulation |
| `12254c26-bb5d-49dd-817f-57152ad7d6b3` | website / events | TERI-ITEC Courses 2013-14 Course III - Climate change and sustainability | https://teriin.org/event/teri-itec-courses-2013-14-course-iii-climate-change-and-sustainability |
| `24a2f721-a456-424c-be18-fb7fc853756a` | website / events | TERI-ITEC Courses 2013-14 Course IV - Trade and sustainable development - issues for developing countries | https://teriin.org/event/teri-itec-courses-2013-14-course-iv-trade-and-sustainable-development-issues-developing |
| `2eadf8d8-84b7-4428-9ab7-951b25ff62be` | website / events | TERI-ITEC Courses 2013-14 Course VII - Resource security and governance issues: challenges and opportunities | https://teriin.org/event/teri-itec-courses-2013-14-course-vii-resource-security-and-governance-issues-challenges-and |
| `499bb245-0f10-4733-b855-6354fcdd472a` | website / events | TERI-ITEC Courses 2017-18: Course VIII - Integrated approach towards sustainable development | https://teriin.org/event/teri-itec-courses-2017-18-course-viii-integrated-approach-towards-sustainable-development |
| `55a7ce13-f53c-4871-9093-2e2cc76618d1` | website / events | TERI-ITEC Courses 2015-16 Course VI - Renewable Energy and Energy Efficiency | https://teriin.org/event/teri-itec-courses-2015-16-course-vi-renewable-energy-and-energy-efficiency |
| `77c52af9-e5e4-43f1-b1ae-3b97250d4658` | website / ongoing_projects | International Training under 'Capacity Building Program' in Power Sector for officials of Department of Power, | https://teriin.org/project/international-training-under-capacity-building-program-power-sector-officials-department |
| `04a01dce-1077-4c64-bf0b-7dbed4389716` | website / press_release | First International E-Certificate Course on Mainstreaming Urban Climate Action Launched by Key Institutions | https://teriin.org/press-release/first-international-e-certificate-course-mainstreaming-urban-climate-action-launched |
| `8b15b308-c364-46fb-ba6e-0f6535c1f6a1` | website / ongoing_projects | Climate Skills - Seeds for a Transition India | https://teriin.org/project/climate-skills-seeds-transition-india |

**Notes**: TEMPORAL CAVEAT: the ITEC course records in the corpus all carry a 2018-01-09 ingestion published_at and describe cycles up to 2017-18. The corpus does not establish that TERI-ITEC courses are still running, so an answer must use past or unspecified tense.

---

### Q103 - What sustainability courses are available through TERI?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c9fe4e63-cbf9-40c1-809f-bb6e1ba9b9f9` | website / services | Training & Capacity Building |  |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |
| `bd80d6c7-4c68-4fe9-9c8b-40d1ae6ca7d8` | website / events | TERI in partnership with NDTV launches the 3-month ESG certification programme | https://teriin.org/event/teri-partnership-ndtv-launches-3-month-esg-certification-programme |
| `6960e619-2187-4622-9e1a-1543792246fb` | website / completed_projects | e-Certificate Course on Mainstreaming Urban Climate Action | https://teriin.org/project/e-certificate-course-mainstreaming-urban-climate-action |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |

**Notes**: AMBIGUOUS AND NO CATALOGUE. 'Sustainability courses available through TERI' could mean (a) TERI's professional training and certificate programmes, or (b) degree programmes at TERI School of Advanced Studies - a separate deemed institution whose website (terisas.ac.in) is NOT in this corpus. Under reading (a) the corpus holds individual programme records but no current course catalogue and no availability status; under reading (b) the corpus holds no programme information at all. A human must fix the reading before this can be gold.

---

### Q104 - Are there academic programmes offered by TERI School of Advanced Studies (TERI SAS)?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `ab2e2f0c-0eca-4681-8918-efb62f1adbe8` | website / people | Dr Vibha Dhawan | https://teriin.org/governing-council/dr-vibha-dhawan |
| `8b15b308-c364-46fb-ba6e-0f6535c1f6a1` | website / ongoing_projects | Climate Skills - Seeds for a Transition India | https://teriin.org/project/climate-skills-seeds-transition-india |
| `874fc35b-a477-4090-aef2-c0ed050d5d79` | website / page | Newsletters and Resources - Sustainable Buildings | https://teriin.org/newsletter-resources-sustainable-buildings |
| `f3790995-bddc-424a-926f-599f3b8e5497` | website / news | TERI School of Advanced Studies and Emerson bring together leading universities to launch a book on Net Zero T | https://teriin.org/news/teri-school-advanced-studies-and-emerson-bring-together-leading-universities-launch-book-net-0 |

**Notes**: TERI SAS CONTENT IS NOT IN THE CORPUS. The corpus confirms TERI School of Advanced Studies EXISTS as a distinct institution - it has an address (Plot No. 10, Institutional Area, Vasant Kunj, New Delhi - 110 070), a phone number, a registrar (registrar@terisas.ac.in, contact person Col. B Venkat (Retd.)), and a Vice-Chancellor post (Dr Vibha Dhawan led TERI SAS as Vice-Chancellor 2005-2007) - and it appears as an implementation partner in projects (Climate Skills) and collaborations (curriculum development on Green Buildings; a book launch with Emerson). The existence of a Vice-Chancellor and Registrar implies degree programmes, but NO programme, department, degree or curriculum listing is ingested, because terisas.ac.in is a separate domain outside this corpus. A human must decide whether the existence-level 'yes' is an acceptable gold answer.

---

### Q105 - What courses are available in environmental studies, sustainability, and climate change?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `c9fe4e63-cbf9-40c1-809f-bb6e1ba9b9f9` | website / services | Training & Capacity Building |  |
| `6960e619-2187-4622-9e1a-1543792246fb` | website / completed_projects | e-Certificate Course on Mainstreaming Urban Climate Action | https://teriin.org/project/e-certificate-course-mainstreaming-urban-climate-action |
| `86810e54-afea-422a-bf76-ff1363f378d8` | website / page | KRC Resources | https://teriin.org/krc-resources |

**Notes**: Same gap as Q103/Q104: no course catalogue for either TERI's professional programmes or TERI SAS degrees. The corpus can name individual past courses touching environmental studies, sustainability and climate change (TERI-ITEC Climate change and sustainability; e-Certificate Course on Mainstreaming Urban Climate Action; certificate course on solar energy systems; ESG certification with NDTV) but cannot establish what is currently available.

---

### Q106 - How can students enroll in TERI SAS programmes?

- **Status**: `NO_SUPPORTED_ANSWER`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> The corpus contains no information on enrolling in TERI School of Advanced Studies programmes.

**Expected facts**

- The corpus provides no admissions process, eligibility criteria, application route, deadlines, fees or programme list for TERI School of Advanced Studies.
- The only TERI SAS contact information in the corpus is the institutional address and the registrar's contact on TERI's Contact Us page (registrar@terisas.ac.in, tel (+91 11) 7180 0222, contact person Col. B Venkat (Retd.)).

**Expected entities**: TERI School of Advanced Studies, registrar@terisas.ac.in

**Reproducible derivations**

- `SELECT COUNT(*) FROM documents WHERE url LIKE '%terisas%' OR url LIKE '%teri-sas%' -> 0`
- `SELECT bundle,title FROM documents WHERE title LIKE '%School of Advanced Studies%' -> 2 rows, both the same news item about a book launch with Emerson`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |

**Notes**: Marked NO_SUPPORTED_ANSWER because the absence is establishable: TERI SAS runs on a separate domain (terisas.ac.in) with zero ingested URLs, and no admissions content exists anywhere in the 11,991 documents. The only defensible chatbot behaviour is to say it does not have TERI SAS admissions information and to point to the registrar contact. An answer that states specific programmes, eligibility or deadlines is a hallucination regardless of whether it happens to be true in the real world.

---

### Q107 - How can I search TERI's research publications?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI's publications can be searched and browsed through several routes documented in the corpus: the Articles & Publications page (teriin.org/articles-publications), which lists TERI authors' articles, op-eds, policy briefs and book chapters with dates and the publication they appeared in; the Documents/Brochures hub (teriin.org/documents), linking Annual Reports, Brochures, Newsletters and TERI's Solutions for Sustainable Development; the TERI Library / Knowledge Resource Centre catalogue at library.teri.res.in, with abstracting services, literature search, reference and referral, document delivery, inter-library loan, a Digital Library, an Institutional Repository and online journals, books and databases; and the World Digital Library on Sustainable Development. The website also carries dedicated policy-brief, research-paper, report, article and infographic sections.

**Expected facts**

- TERI's Articles & Publications page (teriin.org/articles-publications) lists TERI authors' articles, op-eds and policy briefs with dates and the publication they appeared in.
- The Documents/Brochures hub (teriin.org/documents) links Annual Reports, Brochures, Newsletters and TERI's Solutions for Sustainable Development.
- The TERI Library catalogue is searchable at library.teri.res.in.
- TERI Library services include abstracting services, literature search, reference and referral services, document delivery, inter-library loan, a Digital Library, an Institutional Repository, and online journals, books and databases.
- TERI hosts a World Digital Library on Sustainable Development providing value-added information services to energy and environment professionals.

**Expected entities**: Articles & Publications, library.teri.res.in, TERI Library / KRC, World Digital Library on Sustainable Development

**Reproducible derivations**

- `SELECT bundle, COUNT(*) FROM documents WHERE source_type='website' GROUP BY 1 -> research_papers 624, policy_brief 247, article 459, infographics 45, report 8`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `498f897d-8577-4d47-b70f-3e9e7e91b909` | website / page | Articles & Publications | https://teriin.org/articles-publications |
| `01937c6f-ea48-4c44-ba22-19fab25ba7bc` | website / page | Documents/Brochures | https://teriin.org/documents |
| `0031cf62-fcb1-46a6-b4df-cdefdfe62aa6` | website / page | KRC Services | https://teriin.org/krc-services |
| `86810e54-afea-422a-bf76-ff1363f378d8` | website / page | KRC Resources | https://teriin.org/krc-resources |
| `7f81af0f-d4fb-4ffd-9cd8-916e362ec0e3` | website / services | World Digital Library on Sustainable Development |  |
| `fa6999c0-c477-485d-8ce9-85409c1850d8` | website / services | Publication of academic and reference material |  |

**Notes**: The corpus documents WHERE publications live but not a site-wide publication search UI with filters.

---

### Q108 - What are TERI's most recent publications on renewable energy?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: aggregation/list + time-range
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `theme 'Electricity and Renewables' -> 86 documents; no 'renewable energy' publication facet`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `c8c1a5df-d686-44cf-a350-6eeea55971db` | website / press_release | TERI Unveils a Report on Reassessing India’s Solar Potential: Total Estimated Capacity Pegged at 10,830 GW | https://teriin.org/press-release/teri-unveils-report-reassessing-indias-solar-potential-total-estimated-capacity |
| `a1ca094a-591b-40d5-928f-fbe5c105c119` | website / policy_brief | Solar With Storage Is Cheaper Than New Thermal | https://teriin.org/policy-brief/solar-storage-cheaper-new-thermal |
| `bf0abbc6-3a78-4005-8b5f-ae74a92ffb77` | website / policy_brief | Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints in India’s Energy Transition | https://teriin.org/policy-brief/unlocking-solar-scale-how-agrivoltaics-overcome-land-constraints-indias-energy |
| `8a92ed23-54ed-466e-ae97-de06bb0d5293` | website / policy_brief | Tenure Dynamics in Land Procurement in Rajasthan’s Utility-Scale Solar Energy Transition | https://teriin.org/policy-brief/tenure-dynamics-land-procurement-rajasthans-utility-scale-solar-energy-transition |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `7b4ca9d9-ae6c-4073-a586-fa74918a983b` | website / policy_brief | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward | https://teriin.org/policy-brief/battery-assembly-and-container-testing-safety-global-best-practices-and-way-forward |
| `d3cc1426-c67b-4e1c-89dc-d0a518be202c` | website / research_papers | Solar threads and social knots: Gender and energy transitions in the weaving community of Varanasi, India | https://teriin.org/research-paper/solar-threads-and-social-knots-gender-and-energy-transitions-weaving-community |

**Notes**: 'MOST RECENT' IS COMPUTABLE BUT 'PUBLICATIONS ON RENEWABLE ENERGY' IS NOT A DERIVABLE SET. published_at ordering is reliable, but there is no renewable-energy publication facet: the nearest theme, 'Electricity and Renewables', holds 86 documents of mixed type, and many renewable-energy items in the corpus are third-party news, not TERI publications. Whether 'publications' means policy briefs only, or also research papers, reports and articles, changes the answer entirely. The document_ids list the strongest recent candidates for a human to confirm.

---

### Q109 - Can you recommend reports on climate change adaptation?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI reports and papers on climate change adaptation that can be recommended from the corpus: 'A Transformative Global Goal on Adaptation: Scope, Science and Policy' (policy brief, Nov 2024); 'Road to Dubai and the Global Goal on Adaptation' (policy brief, Nov 2023, launched at a pre-COP28 dialogue); 'Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action' (policy brief, Sept 2024); 'Who is adapting and how? Identifying actors and roles in climate change adaptation' and 'A global assessment of actors and their roles in climate change adaptation' (research papers, Oct 2023); and 'Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South' (project). Related: TERI's knowledge documents on imperatives for the Global South on adaptation ahead of COP28, and its statement that India's LT-LEDS builds the case for adaptation and enhancing climate resilience.

**Expected facts**

- TERI published the policy brief 'A Transformative Global Goal on Adaptation: Scope, Science and Policy' (November 2024).
- TERI published the policy brief 'Road to Dubai and the Global Goal on Adaptation' (November 2023) and launched it at a pre-COP28 dialogue.
- TERI published 'Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action' (September 2024).
- TERI published the research papers 'Who is adapting and how? Identifying actors and roles in climate change adaptation' and 'A global assessment of actors and their roles in climate change adaptation' (October 2023).
- TERI runs 'Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South'.

**Expected entities**: Global Goal on Adaptation, Road to Dubai, LT-LEDS, COP28

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `f5d7666d-64e9-4192-ad56-71b6ecd68edc` | website / policy_brief | A Transformative Global Goal on Adaptation: Scope, Science and Policy | https://teriin.org/policy-brief/transformative-global-goal-adaptation-scope-science-and-policy |
| `3d632bf3-735d-46a8-b40d-73b03750bc29` | website / policy_brief | Road to Dubai and the Global Goal on Adaptation | https://teriin.org/policy-brief/road-dubai-and-global-goal-adaptation |
| `2fb38040-7b35-464c-ab37-2f19bf2f6f9a` | website / press_release | TERI Hosts Pre-COP28 Dialogue, Launches Road to Dubai and the Global Goal on Adaptation | https://teriin.org/press-release/teri-hosts-pre-cop28-dialogue-launches-road-dubai-and-global-goal-adaptation |
| `7baccf12-187c-400e-b2fa-4fa9ea04e549` | website / policy_brief | Climate Resilience in Water Resource Management in India: A Conceptual Framework for Action | https://teriin.org/policy-brief/climate-resilience-water-resource-management-india-conceptual-framework-action |
| `5243ca2f-bf7e-48b1-994a-8265073dba82` | website / research_papers | Who is adapting and how? Identifying actors and roles in climate change adaptation | https://teriin.org/research-paper/who-adapting-and-how-identifying-actors-and-roles-climate-change-adaptation |
| `65953ed4-e37b-45d4-a45d-9d57a375dbad` | website / research_papers | A global assessment of actors and their roles in climate change adaptation | https://teriin.org/research-paper/global-assessment-actors-and-their-roles-climate-change-adaptation |
| `4b77a379-bff3-4335-a2b8-e6a98ee470ad` | website / ongoing_projects | Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South | https://teriin.org/project/mapping-policies-and-stakeholders-climate-adaptation-crop-based-systems-global-south |
| `5419a5a2-e860-4799-bb93-9e09556454ed` | website / press_release | Road to Dubai: TERI knowledge documents highlight imperatives for the Global South on adaptation and energy tr | https://teriin.org/press-release/road-dubai-teri-knowledge-documents-highlight-imperatives-global-south-adaptation-and |
| `d7e7056f-0de7-44ca-a5f7-67a79f0b4c6b` | website / press_release | India's LT-LEDS builds the case for adaptation and enhancing climate resilience: TERI Experts | https://teriin.org/press-release/indias-lt-leds-builds-case-adaptation-and-enhancing-climate-resilience-teri-experts |

**Notes**: A recommendation question: the gold is the candidate pool, not a ranking. There is no 'recommended reading' list in the corpus, so any TERI adaptation publication cited correctly should score; citing non-TERI or non-adaptation items should not.

---

### Q110 - What policy briefs has TERI recently published?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_NEEDS_CORRECTION` (corrected - see `organization_121_gold_corrections.md`)
- **Answer type**: aggregation/list + time-range
- **Temporal scope**: temporal_mode=date range / publication date; requested_period=most recent; expected_validity_window=published_at DESC as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17

**Gold answer**

> The most recently published TERI policy briefs in the corpus snapshot, newest first: 'Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward' (11 Aug 2026); 'Solar Thermal Energy for Industrial Decarbonization' (5 Aug 2026); 'Discussion Brief: Sustainable Land Futures for Utility Scale RE Expansion in States' (31 Jul 2026); 'Tenure Dynamics in Land Procurement in Rajasthan's Utility-Scale Solar Energy Transition' (31 Jul 2026); 'Fly Ash Utilization and Transportation- Increasing Rail Share in Fly Ash Transportation' (21 Jul 2026); 'Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints in India's Energy Transition' (6 Jul 2026); 'Towards Cleaner Freight in Delhi' (29 Jun 2026); 'Study on Circular Economy of End-of-Life Vehicles and Other Sectors' (16 Jun 2026); 'Decarbonizing Transport: Supply-side Policies & Opportunities for Uttar Pradesh' (4 Jun 2026); 'A Five Pillar Framework for Bankability' (29 May 2026); 'Indian Armed Forces and Environmental Sustainability' (27 May 2026); and 'Feasibility Study of Energy Access for Enterprise Promotion' (21 May 2026). The corpus holds 247 policy-brief nodes in total.

**Expected facts**

- TERI's most recent policy brief in the snapshot is 'Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward' (11 August 2026).
- 'Solar Thermal Energy for Industrial Decarbonization' was published on 5 August 2026.
- 'Discussion Brief: Sustainable Land Futures for Utility Scale RE Expansion in States' and 'Tenure Dynamics in Land Procurement in Rajasthan's Utility-Scale Solar Energy Transition' were published on 31 July 2026.
- 'Fly Ash Utilization and Transportation- Increasing Rail Share in Fly Ash Transportation' was published on 21 July 2026.
- 'Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints in India's Energy Transition' was published on 6 July 2026.
- 'Towards Cleaner Freight in Delhi' was published on 29 June 2026 and 'Study on Circular Economy of End-of-Life Vehicles and Other Sectors' on 16 June 2026.
- The corpus holds 247 policy-brief nodes in total.

**Reproducible derivations**

- `SELECT document_id,title,published_at FROM documents WHERE bundle='policy_brief' AND source_type='website' ORDER BY published_at DESC LIMIT 12`
- `SELECT COUNT(*) FROM documents WHERE bundle='policy_brief' AND source_type='website' -> 247`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `7b4ca9d9-ae6c-4073-a586-fa74918a983b` | website / policy_brief | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward | https://teriin.org/policy-brief/battery-assembly-and-container-testing-safety-global-best-practices-and-way-forward |
| `b10ea3d2-1f77-4031-bd9c-14f247fc7721` | website / policy_brief | SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION | https://teriin.org/policy-brief/solar-thermal-energy-industrial-decarbonization |
| `c837a254-0acb-4aa0-9acc-843d76fcf404` | website / policy_brief | Discussion Brief: Sustainable Land Futures for Utility Scale RE Expansion in States: Case Study of Rajasthan | https://teriin.org/policy-brief/discussion-brief-sustainable-land-futures-utility-scale-re-expansion-states-case-study |
| `8a92ed23-54ed-466e-ae97-de06bb0d5293` | website / policy_brief | Tenure Dynamics in Land Procurement in Rajasthan’s Utility-Scale Solar Energy Transition | https://teriin.org/policy-brief/tenure-dynamics-land-procurement-rajasthans-utility-scale-solar-energy-transition |
| `485727f8-66d5-428d-be6e-858c1f7a6a39` | website / policy_brief | Fly Ash Utilization and Transportation- Increasing Rail Share in Fly Ash Transportation | https://teriin.org/policy-brief/discussion-paper-on-fly-ash-utilization-and-transportation-increasing-rail-share-fly-ash-transportation |
| `bf0abbc6-3a78-4005-8b5f-ae74a92ffb77` | website / policy_brief | Unlocking Solar at Scale: How Agrivoltaics Overcome Land Constraints in India’s Energy Transition | https://teriin.org/policy-brief/unlocking-solar-scale-how-agrivoltaics-overcome-land-constraints-indias-energy |
| `eeb196ea-84eb-416c-91af-cd05fae6fd9a` | website / policy_brief | Towards Cleaner Freight in Delhi | https://teriin.org/policy-brief/towards-cleaner-freight-delhi |
| `9032cec1-fc66-4da2-838e-0cdc4c831337` | website / policy_brief | Study on Circular Economy of End-of-Life Vehicles and Other Sectors | https://teriin.org/policy-brief/study-circular-economy-end-life-vehicles-and-other-sectors |
| `5a11ac34-44cc-4094-9868-ef9e159681fc` | website / policy_brief | Decarbonizing Transport: Supply-side Policies & Opportunities for Uttar Pradesh | https://teriin.org/policy-brief/decarbonizing-transport-supply-side-policies-opportunities-uttar-pradesh |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |
| `3c76bd30-d43c-4f37-b101-8ba5e8137362` | website / policy_brief | Indian Armed Forces and Environmental Sustainability: A Comprehensive Assessment of Simulators in ‘Green Train | https://teriin.org/policy-brief/indian-armed-forces-and-environmental-sustainability-comprehensive-assessment |
| `8d90ecfc-2213-4c62-929b-b0c45dfd7683` | website / policy_brief | Feasibility Study of Energy Access for Enterprise Promotion | https://teriin.org/policy-brief/feasibility-study-energy-access-enterprise-promotion |

**Notes**: Answerable because 'policy brief' IS a CMS bundle, making the set closed and orderable - unlike Q108. CAVEAT: published_at is the CMS node date, which for some legacy nodes is an ingestion artefact rather than a true publication date (many 2017-12-28 and 2018-01-09/11 timestamps in this corpus are migration artefacts); that does not affect the 2026 head of the list. The evaluation must fix the reference date.

---

### Q111 - Where can I download TERI's annual reports

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `HIGH` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual
- **Temporal scope**: temporal_mode=current; requested_period=as of 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17; expected_validity_window=most recent edition listed: 2024-25

**Gold answer**

> TERI's annual reports are on the Annual Reports page at teriin.org/annual-reports, which links direct PDF downloads for Annual Report 2024-25 (teriin.org/files/TERI-Annual-Report-2024-25.pdf), 2023-24, 2022-23, 2021-22, 2020-21, 2019-20, 2018-19, 2017-18, 2016-17 and 2015-16. The page is also reachable from the Documents/Brochures hub at teriin.org/documents.

**Expected facts**

- TERI's annual reports are available on the Annual Reports page at teriin.org/annual-reports.
- The page provides direct PDF download links for annual reports from 2015-2016 through 2024-2025.
- The most recent annual report linked is Annual Report 2024-25 at teriin.org/files/TERI-Annual-Report-2024-25.pdf.
- The Annual Reports page is also linked from the Documents/Brochures hub at teriin.org/documents.

**Expected entities**: Annual Reports page, teriin.org/annual-reports

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `db669bde-858c-478b-9751-fb148d2ecfb4` | website / page | Annual Reports | https://teriin.org/annual-reports |
| `01937c6f-ea48-4c44-ba22-19fab25ba7bc` | website / page | Documents/Brochures | https://teriin.org/documents |

**Notes**: Source-data quirk worth knowing for evaluation: all annual-report PDF attachments in this corpus hang off the single Annual Reports Drupal node, so every edition shares the same node title and published_at - the year is only distinguishable from the filename. The question as written in the source document has no question mark; preserved verbatim.

---

### Q112 - What publications are available on Sustainable Development Goals?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: aggregation/list
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> TERI publications on the SDGs documented in the corpus include: 'India and Sustainable Development Goals (SDGs)' (policy brief); the Special Commentary 'Sustainable Development Goals: An India Perspective'; 'Aligning India's Water Resource Policies with the SDGs' and the discussion paper 'Aligning India's Sanitation Policies with the SDGs'; 'Achieving SDGs in water and sanitation sectors in India'; 'Synergies between Climate Action and SDGs: Implications for Multilateralism' (Oct 2024); 'Re-anchoring CBDR-RC in Human Development and SDGs for Climate Justice' (Nov 2025); 'Reconciling Value Trade-Offs in Advancing Sustainable Development Goals: Risks and Opportunities' (Nov 2024); the 'SDG Blueprint for Sustainable Agriculture' (Mar 2024) and the accompanying tool; documents on the SDG 7 and SDG 13 interfaces with sustainable agriculture; 'Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13' (2025); 'Achieving SDG 14 in India: Assessing Progress Towards Sustainable Oceans'; and the Act4Earth SDG Charter paper series. TERI also coordinates continuing SDG policy products - Think Pieces, Policy Briefs and Discussion Papers - through its SDG and Policy Coordination initiative.

**Expected facts**

- TERI published the policy brief 'India and Sustainable Development Goals (SDGs)'.
- TERI published the Special Commentary 'Sustainable Development Goals: An India Perspective'.
- TERI published 'Aligning India's Water Resource Policies with the SDGs' and the discussion paper 'Aligning India's Sanitation Policies with the SDGs'.
- TERI published 'Synergies between Climate Action and SDGs: Implications for Multilateralism' (October 2024).
- TERI published 'Re-anchoring CBDR-RC in Human Development and SDGs for Climate Justice' (November 2025).
- TERI published the 'SDG Blueprint for Sustainable Agriculture' (March 2024) and an accompanying SDG Blueprint Tool.
- TERI publishes documents on the SDG 7 and SDG 13 interfaces with sustainable agriculture.
- TERI's SDG and Policy Coordination (SPC) initiative coordinates continuing publication of Think Pieces, Policy Briefs and Discussion Papers on SDGs.

**Expected entities**: SDG Blueprint for Sustainable Agriculture, SDG Charter, SDG and Policy Coordination, CBDR-RC

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `5f273cf0-9139-4990-ad3d-048ccd81d310` | website / page | Sustainable Development Goals | https://teriin.org/sustainable-development-goals |
| `65cdeb2f-e4c0-4faa-ae6a-891223cac8d6` | website / page | ACT4EARTH | https://teriin.org/act4earth |
| `0f23e106-b601-46f4-861d-15d991f97038` | website / page | SDG 7: AFFORDABLE AND CLEAN ENERGY | https://teriin.org/SDG-7-Affordable-and-Clean-Energy |
| `397b8e72-647d-414f-bb2b-2ac59c4cf96d` | website / page | SDG 13. CLIMATE ACTION | https://teriin.org/SDG-13-Climate-Action |
| `e4d62a8c-b446-483b-8048-2567162853b5` | website / policy_brief | India and Sustainable Development Goals (SDGs) | https://teriin.org/policy-brief/india-and-sustainable-development-goals-sdgs |
| `18f92aa1-9b46-4a0a-9267-027ede7906ba` | website / article | Special Commentary - Sustainable Development Goals: An India Perspective | https://teriin.org/article/special-commentary-sustainable-development-goals-india-perspective |
| `9ce46636-42c5-47b1-bb3e-d16609b85524` | website / policy_brief | Discussion Paper: Aligning India's Sanitation Policies with the SDGs | https://teriin.org/policy-brief/discussion-paper-aligning-indias-sanitation-policies-sdgs |
| `cba07f58-533f-4a20-9bda-5a351aa6489a` | website / research_papers | Achieving SDGs in water and sanitation sectors in India | https://teriin.org/research-paper/achieving-sdgs-water-and-sanitation-sectors-india |
| `ad074197-e7d9-415e-b74d-01616c598ee2` | website / policy_brief | Synergies between Climate Action and SDGs: Implications for Multilateralism | https://teriin.org/policy-brief/synergies-between-climate-action-and-sdgs-implications-multilateralism |
| `36961dd6-cf65-4dfa-aca6-cef71c843526` | website / policy_brief | Re-anchoring CBDR-RC in Human Development and SDGs for Climate Justice | https://teriin.org/policy-brief/re-anchoring-cbdr-rc-human-development-and-sdgs-climate-justice |
| `2c8b1bc0-bdda-4f1f-bfb9-7c34d181750a` | website / research_papers | Reconciling Value Trade-Offs in Advancing Sustainable Development Goals: Risks and Opportunities | https://teriin.org/research-paper/reconciling-value-trade-offs-advancing-sustainable-development-goals-risks-and |
| `fc588c50-391a-400c-a6ad-74707615b2af` | website / policy_brief | SDG Blueprint for Sustainable Agriculture | https://teriin.org/policy-brief/sdg-blueprint-sustainable-agriculture |
| `08b5053a-4d55-4128-a758-da9f5a13adc3` | website / research_papers | Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13 | https://teriin.org/research-paper/artificial-intelligence-climate-resilience-evaluating-contributions-sdg-13 |
| `d65fc049-793c-4078-8c00-4c5eab624aaf` | website / completed_projects | Achieving SDG 14 in India: Assessing Progress Towards Sustainable Oceans | https://teriin.org/project/achieving-sdg-14-india-assessing-progress-towards-sustainable-oceans |

**Notes**: Not a closed set: documents_tag holds only 264 'Sustainable Development Goals' tags and 23 'SDGs' tags, and SDG publications are spread across policy_brief, research_papers and article bundles. Score correctness of cited items, not completeness.

---

### Q113 - How can researchers obtain project reports and technical documents?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> Researchers can obtain TERI project reports and technical documents through the TERI Library / Knowledge Resource Centre. Membership is open to researchers, staff of non-governmental organizations, government officials, employees of corporate bodies, students, teachers, consultants and policy-makers in energy, environment and sustainable development; application forms are available at the library help desk or downloadable from the website, and proof of identity is required. Relevant services include document delivery, inter-library loan, reprography (photocopying at a nominal fee), literature search, reference and referral, a Digital Library, an Institutional Repository, a Project Based Information Service (PBIS) and projects/publication updates from other institutes; the catalogue is at library.teri.res.in. Library resources are available for reference and inter-library loans are allowed, but borrowing of resources is not. Many TERI reports, policy briefs and brochures are also downloadable directly from teriin.org (Annual Reports, Brochures, Documents and the Articles & Publications page).

**Expected facts**

- TERI Library membership is open to researchers, NGO staff, government officials, corporate employees, students, teachers, consultants and policy-makers in energy, environment and sustainable development.
- Library application forms are available at the library help desk or downloadable from the website, and proof of identity is required.
- TERI Library services include document delivery, inter-library loan, reprography, literature search, reference and referral services, a Digital Library, an Institutional Repository and a Project Based Information Service (PBIS).
- The TERI Library catalogue is at library.teri.res.in.
- Library resources are available for reference and inter-library loans are allowed, but borrowing of resources is not allowed; photocopying can be availed at a nominal fee.
- Many TERI reports, policy briefs and brochures are downloadable directly from teriin.org via the Annual Reports, Brochures, Documents and Articles & Publications pages.

**Expected entities**: TERI Library / Knowledge Resource Centre, library.teri.res.in, PBIS, Institutional Repository

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `0031cf62-fcb1-46a6-b4df-cdefdfe62aa6` | website / page | KRC Services | https://teriin.org/krc-services |
| `86810e54-afea-422a-bf76-ff1363f378d8` | website / page | KRC Resources | https://teriin.org/krc-resources |
| `01937c6f-ea48-4c44-ba22-19fab25ba7bc` | website / page | Documents/Brochures | https://teriin.org/documents |
| `498f897d-8577-4d47-b70f-3e9e7e91b909` | website / page | Articles & Publications | https://teriin.org/articles-publications |
| `db669bde-858c-478b-9751-fb148d2ecfb4` | website / page | Annual Reports | https://teriin.org/annual-reports |
| `e071ea2f-4ea8-4d9a-b101-42a037155282` | website / page | Brochures | https://teriin.org/brochures |
| `7f81af0f-d4fb-4ffd-9cd8-916e362ec0e3` | website / services | World Digital Library on Sustainable Development |  |

**Notes**: The library route is documented verbatim. The corpus does NOT document a request procedure for unpublished project reports or client deliverables, so an answer must not promise access to those.

---

### Q114 - Who are TERI experts working on climate change?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: person lookup
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT a.author, COUNT(*) FROM documents_author a JOIN documents_theme t ON t.document_id=a.document_id WHERE t.theme='Climate Change' GROUP BY 1 ORDER BY 2 DESC -> Mr R R Rashmi 42, Dr Shailly Kedia 38, Dr Manish Kumar Shrivastava 18, Ms Suruchi Bhadwal 17, Mr Manjeet Singh 16, Mr Ajay Shankar 14, Dr Vibha Dhawan 13, Mr Manjeev Singh Puri 13, Mr Karan Mangotra 12, Mr Shanmuganathan K 12, Mr Saurabh Bhardwaj 11, Ms N R Mekhala Sastry 9, Mr Abhishek Kaushik 9, Ms Neha Pahuja 9, Dr Ajay Mathur 8`

**Notes**: NO EXPERT DIRECTORY. See Q006. What IS derivable is the authorship-by-theme intersection above - a defensible candidate pool but not an answer: the CMS records no designations, expertise statements or current-employment status, several listed names are former staff or advisors, and authorship of a climate-themed document does not establish that someone 'works on climate change' at TERI today. A human must decide whether the derived author list is acceptable gold.

---

### Q115 - Which TERI experts specialize in renewable energy?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: person lookup
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `Same derivation with t.theme='Energy' -> Mr Ajay Shankar 60, Dr Debajit Palit 52, Dr Shailly Kedia 13, Mr R K Batra 12, Mr Amit Kumar 10, Dr Vibha Dhawan 7, Mr R R Rashmi 7, Ms Rashmi Murali 7, Dr Mini Govindan 7, Dr Sanjukta Subudhi 6, Mr S Arun 6, Dr Shashank Vyas 6, Mr Ajai Malhotra 6, Mr Saswata Chaudhury 6`

**Notes**: Same structural gap as Q114. Additionally the theme 'Energy' is broader than renewable energy and the narrower 'Electricity and Renewables' theme carries only 86 documents, so even the candidate pool is a poor proxy for 'specialises in renewable energy'.

---

### Q116 - Who can I contact regarding green hydrogen research?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: person lookup / factual
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `2f610ad2-6aca-4560-8c71-f42d42584435` | website / policy_brief | Green Hydrogen - Path to Decarbonization | https://teriin.org/policy-brief/green-hydrogen-path-decarbonization |

**Notes**: NO TOPIC-LEVEL CONTACT ROUTING. The corpus has no researcher directory, no 'contact an expert' function and no per-topic contact. The Contact Us page gives only office-level contacts and the general mailbox@teri.res.in. Authorship of the green-hydrogen policy brief is recorded in documents_author but the corpus provides no email or role for those authors, so a chatbot cannot responsibly name an individual to contact. A human must decide whether 'write to mailbox@teri.res.in' is the gold answer.

---

### Q117 - Which experts work on sustainable agriculture and food systems?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: person lookup
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `Same derivation with t.theme='Sustainable Agriculture' -> Dr Ruchi Agrawal 22, Dr Mayurika Goel 15, Dr Vibha Dhawan 14, Dr Pushplata Singh 10, Mandal Shovon 9, Dr Mandira Kochar 8, Dr Manish Anand 8, Dr Alok Adholeya 7, Dr Shilpanjali Deshpande Sarma 6, Ms Pratima Sinha 4`

**Notes**: Same structural gap as Q114/Q115. Note also that 'food systems' has no theme or tag facet, so the second half of the question is not derivable at all. Data-quality note: the author list mixes name orders ('Mandal Shovon', 'Agrawal Ruchi' alongside 'Dr Ruchi Agrawal'), indicating un-normalised duplicates in documents_author.

---

### Q118 - Who are TERI's specialists in ESG and sustainable finance?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: person lookup
- **Temporal scope**: temporal_mode=timeless

**Reproducible derivations**

- `SELECT tag FROM documents_tag WHERE tag LIKE '%ESG%' -> 0 rows (no ESG tag exists)`

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `780f0ff3-1147-477e-a7a5-bf2bea594df1` | pdf_attachment / events | ESG Certification Program by TERI NDTV | https://teriin.org/event/esg-works-turning-responsibility-results |
| `349ea25d-30d9-4315-94d9-dab2082d6592` | website / policy_brief | Modeling for Climate Finance | https://teriin.org/policy-brief/modeling-climate-finance |
| `e5b1f46e-0a1b-43a5-a300-02e9f3bfe286` | website / policy_brief | A Five Pillar Framework for Bankability: Recalibrating India’s Commercial Finance for Climate Action | https://teriin.org/policy-brief/five-pillar-framework-bankability-recalibrating-indias-commercial-finance-climate |

**Notes**: WEAKEST OF THE EXPERT QUESTIONS. There is no ESG tag or theme at all, so not even a candidate pool is derivable by facet. Individual named evidence does exist: the TERI-NDTV ESG Certification Program page describes Mr R R Rashmi, a retired IAS officer, as an expert on climate change policies, strategies, actions and international negotiations; and 'Modeling for Climate Finance' identifies Manish Kumar Shrivastava as a senior fellow and associate director at TERI exploring interactions between energy, technology, finance and environmental policy. Two named individuals from programme copy are not a specialist roster.

---

### Q119 - Which researchers work on AI and sustainability?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `LOW` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: person lookup
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> The TERI researchers the corpus associates with AI and sustainability are Dr Jitendra Vir Sharma and Mr Sayanta Ghosh, recorded as the authors of TERI's AI-for-land-restoration work - 'Artificial intelligence for restoring land: A review of land degradation mapping, climate change prediction and ecosystem service valuation' (2026) and 'AI for Restoring Degraded Lands: Mapping Degradation, Predicting Climate Risk and Valuing Ecosystem Services'. Mr Sayanta Ghosh is also the recorded author of 'GIS & Machine Learning Based Approaches to Assess Forest and Biodiversity Vulnerability Under Climate Stress: A Case Study from Assam, India' (2025). A further AI paper, 'Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13' (2025), has no usable author record. TERI has also run a Hybrid Seminar on Ethics in AI: Framework for Academic and Research Institutions in India and a Webinar on Leveraging AI Tools Across the Research Lifecycle, and its Corporate Sustainability Leadership Programme 2026 covers AI.

**Expected facts**

- Dr Jitendra Vir Sharma and Mr Sayanta Ghosh are the recorded authors of 'Artificial intelligence for restoring land: A review of land degradation mapping, climate change prediction and ecosystem service valuation'.
- Dr Jitendra Vir Sharma and Mr Sayanta Ghosh are the recorded authors of 'AI for Restoring Degraded Lands: Mapping Degradation, Predicting Climate Risk and Valuing Ecosystem Services'.
- Mr Sayanta Ghosh is the recorded author of 'GIS & Machine Learning Based Approaches to Assess Forest and Biodiversity Vulnerability Under Climate Stress: A Case Study from Assam, India'.
- TERI published 'Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13' (2025).
- TERI convened a Hybrid Seminar on Ethics in AI: Framework for Academic and Research Institutions in India and a Webinar on Leveraging AI Tools Across the Research Lifecycle.

**Expected entities**: Dr Jitendra Vir Sharma, Mr Sayanta Ghosh

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `5d123267-46f3-4f97-8969-74b30f47bccb` | website / research_papers | Artificial intelligence for restoring land: A review of land degradation mapping, climate change prediction an | https://teriin.org/research-paper/artificial-intelligence-restoring-land-review-land-degradation-mapping-climate |
| `5d20ecbc-586e-4e25-b7c7-6a2b1a10b911` | website / research_papers | AI for Restoring Degraded Lands: Mapping Degradation, Predicting Climate Risk and Valuing Ecosystem Services | https://teriin.org/research-paper/ai-restoring-degraded-lands-mapping-degradation-predicting-climate-risk-and-valuing |
| `28eeb229-b331-4889-ad05-368531ae6f82` | website / research_papers | GIS & Machine Learning Based Approaches to Assess Forest and Biodiversity Vulnerability Under Climate Stress:  | https://teriin.org/research-paper/gis-machine-learning-based-approaches-assess-forest-and-biodiversity-vulnerability |
| `08b5053a-4d55-4128-a758-da9f5a13adc3` | website / research_papers | Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13 | https://teriin.org/research-paper/artificial-intelligence-climate-resilience-evaluating-contributions-sdg-13 |
| `0663ef40-2d47-425f-9c34-3765f92b0b1c` | website / events | Hybrid Seminar on Ethics in AI: Framework for Academic and Research Institutions in India | https://teriin.org/event/hybrid-seminar-ethics-ai-frameworks-academic-and-research-institutions-india |
| `5bec92aa-c6fc-442b-ba81-32721267b6be` | website / events | Webinar on Leveraging AI Tools Across the Research Lifecycle | https://teriin.org/event/webinar-leveraging-ai-tools-across-research-lifecycle |
| `a5dc7df0-aa12-4a0d-8f33-32c8a7709012` | website / press_release | TERI Unveils Corporate Sustainability Leadership Programme 2026 Focused on ESG, AI, and Carbon Markets | https://teriin.org/press-release/teri-unveils-corporate-sustainability-leadership-programme-2026-focused-esg-ai-and |

**Notes**: LOW confidence, and the only one of the eight expert questions marked GOLD_VERIFIED - because the AI-and-sustainability output set is small enough (4 items) to enumerate, and CMS authorship for three of them is unambiguous. It is still NOT an expertise directory: no designations or roles are recorded and there may be TERI AI work outside these four items. SUSPICIOUS SOURCE DATA: documents_author for 'Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13' (08b5053a) stores the literal string 'reetas@teri.res.in' as the author name - an email address in a person field. A chatbot that surfaces that string as a researcher's name should be marked wrong.

---

### Q120 - How can I collaborate with TERI researchers?

- **Status**: `NEEDS_HUMAN_REVIEW`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `48b331a3-2631-4f58-b5ba-e7673163c893` | website / page | Internship | https://teriin.org/careers/internship |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |
| `8937e1db-933e-45dc-80d3-80a0889f66cf` | website / page | Areas of Work | https://teriin.org/careers/areas-work |

**Notes**: NO RESEARCH-COLLABORATION ROUTE DOCUMENTED. Unlike Q121 (organisation-level partnering, which the CBS material does cover), there is no page describing how an individual researcher collaborates with TERI researchers - no visiting-fellow scheme, no joint-research call, no researcher directory to approach. The only related routes are the internship email (internship@teri.res.in) and the general mailbox@teri.res.in. A human must decide whether that is an acceptable gold answer.

---

### Q121 - How can organizations partner with TERI for research, innovation, policy advisory, or implementation projects?

- **Status**: `GOLD_VERIFIED` &nbsp;|&nbsp; **Confidence**: `MEDIUM` &nbsp;|&nbsp; **Judgement**: `GOLD_CONFIRMED`
- **Answer type**: factual / procedural
- **Temporal scope**: temporal_mode=timeless

**Gold answer**

> For organisations, TERI's documented partnering routes are: (1) the TERI Council for Business Sustainability (TERI CBS), the interface connecting TERI's research to the corporate world, governed by an Executive Committee of member-company CEOs, with membership tiers (all members / Gold) and stated benefits and services - complimentary consulting person-days, discounted paid consulting, sustainability strategy and roadmap development, performance benchmarking and improvement, participation in policy advocacy, training and capacity building, tailor-made advisory, participation in pilots, working groups and policy dialogues, and forums for board members and Chief Sustainability Officers; (2) co-created Centres of Excellence with corporate and government partners (CONCOR, Mahindra, Tata Chemicals, Chambal Fertilisers/CFCL, NMCG, DBT); (3) consultancy and technical services described on the Areas of Work page (consultancy & advisory, strategy development for corporates, testing and certification, capacity building) and in the 30 service nodes; and (4) MoU-based bilateral partnerships (numerous examples with state utilities, ministries, industry associations and international agencies). The general enquiry route is mailbox@teri.res.in, (+91 11) 2468 2100 / 7110 2100, Darbari Seth Block, India Habitat Centre, Lodhi Road, New Delhi 110 003.

**Expected facts**

- TERI Council for Business Sustainability (TERI CBS) is the interface for TERI's research to connect to the corporate world, and is governed by an Executive Committee of CEOs from member companies.
- TERI CBS membership includes complimentary consulting person-days annually, a discount on paid consulting services, participation in pilots, working groups and policy dialogues, and Gold-member benefits such as a complimentary sustainability-report assessment.
- TERI CBS member services include sustainability strategy and roadmap development, performance benchmarking and improvement, participation in policy advocacy initiatives, and training and capacity building, plus tailor-made advisory services.
- Organisations also partner with TERI by co-creating Centres of Excellence, as with CONCOR, Mahindra, Tata Chemicals, Chambal Fertilisers (CFCL), NMCG and DBT.
- TERI's Areas of Work page lists consultancy & advisory, strategy development for corporates, testing and certification, and capacity building as its technical-services and policy-advisory offerings.
- TERI's general contact is mailbox@teri.res.in, tel (+91 11) 2468 2100 / 7110 2100, Darbari Seth Block, India Habitat Centre, Lodhi Road, New Delhi - 110 003.

**Expected entities**: TERI CBS, Centres of Excellence, CONCOR, Mahindra, Tata Chemicals, CFCL, NMCG, DBT, mailbox@teri.res.in

**Authoritative sources**

| document_id | source_type / bundle | title | url |
| --- | --- | --- | --- |
| `4a4b782f-5110-4520-aec6-92209213a948` | website / page | Business & Sustainability | https://teriin.org/business-sustainability |
| `b48f22b0-bc83-4340-b0c7-67a8a7051366` | website / page | More at TERI CBS | https://teriin.org/more-at-teri-cbs |
| `59aebc8a-58e2-450e-8bb2-1c5615b20e6e` | website / basic | TERI Council for Business Sustainability |  |
| `8937e1db-933e-45dc-80d3-80a0889f66cf` | website / page | Areas of Work | https://teriin.org/careers/areas-work |
| `98ad60e0-e960-4a46-b8c7-906ee0324d32` | website / page | Centres of Excellence | https://teriin.org/centre-of-excellence |
| `2a2e9a77-da56-43a7-8138-3ebf16010d1b` | website / page | Contact Us | https://teriin.org/contact |
| `37ff112e-f9d3-499c-bc56-ddb72fdba365` | website / services | Air Quality Research |  |
| `89f45551-aaac-4e1a-8a95-5b1b9a43668c` | website / services | Audits, Validation & PMU Support |  |
| `2945c8b9-1adb-4e43-8f07-dff9cca0c106` | website / services | Capacity Building & Knowledge Dissemination |  |
| `c2d42e8b-4b6e-451c-9ddf-1d1f653b2b5f` | website / services | Capacity building for management of natural resources |  |
| `2ef2427a-1fdb-4398-9b73-2c4719ac38a4` | website / services | Carbon sequestration potential and biodiversity assessment |  |
| `b6cfe3a0-929d-496f-86ef-a90c99efba76` | website / services | Climate change risk assessment |  |

**Notes**: Note the asymmetry with Q039 and Q120: organisation-level partnering IS documented (via CBS, CoEs and the services catalogue), whereas project-level collaboration (Q039) and individual researcher collaboration (Q120) are not. The corpus documents no formal partnership application process, membership fee or proposal route beyond CBS membership and general contact.

---

## 9. Second-pass consistency check (v2, post-judgement)

- exactly 121 questions extracted, IDs Q001-Q121 contiguous, no missing IDs
- exactly one gold entry per question, no duplicate entries
- 0 exact duplicate questions; near-duplicate pairs listed in section 5 with aligned gold answers
- all 485 referenced `document_id` values exist in MySQL `documents` (re-validated after correction)
- all referenced `claim_id` values exist in MySQL `documents_assertion`
- every GOLD_VERIFIED entry has a non-empty gold answer, at least one expected fact, at least one authoritative source or reproducible derivation, and a HIGH/MEDIUM/LOW confidence rating
- every NEEDS_HUMAN_REVIEW and NO_SUPPORTED_ANSWER entry states its reason
- all 87 GOLD_VERIFIED entries independently re-verified against live MySQL/Qdrant evidence; 64 GOLD_CONFIRMED, 22 GOLD_NEEDS_CORRECTION, 1 GOLD_AMBIGUOUS, 0 GOLD_NOT_SUPPORTED, 0 GOLD_CONTRADICTED
- all multi-valued CMS aggregations re-derived with `JSON_CONTAINS` over the whole array instead of `[0]` (Q025, Q027, Q029)
- no expected fact rests on a `documents_enrichment` LLM abstract (explicitly checked for Q067)
- known source contradictions preserved rather than reconciled (Q002, Q004, Q080) plus one newly recorded CMS classification conflict (Q027)
- no chatbot output was used at any point; the chatbot has not been run

**Gold set frozen and ready for chatbot evaluation.**

