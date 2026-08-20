# Independent AI judgement of the 87 GOLD_VERIFIED gold entries

- **Baseline evaluated**: `organization_121_gold_v1_original.json` (unmodified audit copy)
- **Corrected output**: `organization_121_gold.json` (v2)
- **Corpus snapshot**: 2026-08-18 (max documents.indexed_at); corpus published_at max 2026-08-17
- **Reference date**: 2026-08-19
- **Evidence used**: MySQL CMS/catalog, MySQL claims/assertions, MySQL entity data, Qdrant source chunks, Neo4j projection counts
- **Evidence excluded**: chatbot output, `documents_enrichment` LLM abstracts, general world knowledge, web knowledge, model memory
- **Method**: every one of the 565 expected facts was reduced to distinctive probes (quoted titles, numbers, acronyms, proper-noun phrases) and tested against the *actual chunk text* of the documents the entry cites; every count/facet was re-derived independently in SQL; probe misses were then read manually. No entry was confirmed merely because its cited document exists.

## 1. Summary

| Metric | Value |
| --- | --- |
| Original GOLD_VERIFIED count | 87 |
| Evaluated | 87 |
| GOLD_CONFIRMED | 64 |
| GOLD_NEEDS_CORRECTION | 22 |
| GOLD_NOT_SUPPORTED | 0 |
| GOLD_CONTRADICTED | 0 |
| GOLD_AMBIGUOUS | 1 |
| Contradictions recorded | 5 |

### Fact-level results (565 facts)

| Status | Count |
| --- | --- |
| SUPPORTED | 554 |
| PARTIALLY_SUPPORTED | 9 |
| NOT_SUPPORTED | 2 |
| CONTRADICTED | 0 |

### Judgement confidence

| Confidence | Count |
| --- | --- |
| HIGH | 62 |
| MEDIUM | 24 |
| LOW | 1 |

### Source quality

| Quality | Count |
| --- | --- |
| HIGH | 31 |
| MEDIUM | 55 |
| LOW | 1 |

## 2. Major systematic issues found

**S1 - Aggregation used only the first element of a multi-valued CMS array (3 questions, material).** Every per-theme project count was derived from `field_ongoing_theme[0]`, but 135 of 594 ongoing projects carry two or more themes (100 have 2, 24 have 3, 5 have 4, 3 have 5, 1 has 7, 2 have 8, 1 has 19). Consequence: Climate Change 46 -> **69**, Energy Access 10 -> **18**, and the Q025 theme ranking flips (Energy 74 now ahead of Climate Change 69). Affects Q025, Q027, Q029; all three counts have been re-derived with `JSON_CONTAINS` over the whole array.

**S2 - Facts cited to a parent CMS node instead of the PDF chunk that holds the text (5 questions).** The laboratory facts (NABL packaged-drinking-water per IS:14543, the EIB Laboratory water/hydrocarbon accreditation) and the Government-of-Maharashtra climate-smart-agriculture fact were cited to the *website* Annual Reports node, which does not contain them; the text lives in `inbody:` PDF-attachment chunks. Affects Q090, Q092, Q093, Q095, Q065. This is exactly the kind of error that would make a retrieval evaluation unfair, because the gold pointed at a document the retriever could never use to support the answer.

**S3 - Facts with no supporting citation anywhere in the entry (7 questions).** ICIMOD/NTNC (Q019), the bio-hydrogen policy brief and green-hydrogen primer (Q040), Faridabad (Q056), 'Road to Baku' (Q057), the Minor Forest Produce policy brief (Q067), the #BeatPlasticPollution article (Q075). In every case the fact is TRUE and the correct document was located in the corpus; only the citation was missing.

**S4 - Titles paraphrased inside quotation marks (6 questions).** Q016 ('...South Africa, Ghana and other countries' for a title that enumerates South Korea, Japan and Chile) and Q064 ('for urban and industrial sectors' for 'for urban and peri-urban areas in India') are substantive; Q010, Q012/Q048, Q049 and Q110 are punctuation/preposition slips. All corrected to the exact CMS titles.

**S5 - One attribution error (1 question).** Q045 credited a battery-storage cost finding to 'TERI analysis'. The only source is a third-party news node whose body attributes the report to 'global energy think tank Ember and the Delhi-based The Energy and Resources Institute (TERI)', and the '15%' figure appears only in the news *headline* - the body says 7% annual decline and coal plateauing to 2032. Corrected to joint Ember-TERI attribution and to the figures actually in the source.

**S6 - One over-generalisation plus a foreign-policy definition attributed to TERI (1 question).** Q072's circular-economy definition was generalised from a plastics-scoped passage by deleting the word 'plastic', none of its four cited documents contained any definition, and the '3Rs' framing is in fact CHINA's definition of resource efficiency quoted inside a TERI report (plus JAPAN's Resource Circulation Strategy). The 3Rs fact was removed and the entry reclassified **GOLD_AMBIGUOUS**.

**S7 - CMS theme assignment is demonstrably noisy (data-quality risk, not a gold error per se).** Document 4b77a379, titled 'Mapping Policies and Stakeholders on Climate **Adaptation** for Crop-Based Systems in the Global South', carries `field_ongoing_theme = ["Resource Efficiency & Governance"]`. Any theme-derived project set therefore carries classification risk, and this is now recorded in the Q027 notes.

**Checked and DISPROVED:** an earlier concern that Q067's Minor-Forest-Produce facts originated in an LLM-generated `documents_enrichment` abstract. The statements are present verbatim in real Qdrant chunk text of the policy brief (website node `00d5790d` and PDF `aaf55d78`). **No fact in the 87 entries rests on an enrichment abstract.**

## 3. Temporal judgement

All 87 entries were checked for temporal interpretation. No historical fact was presented as current. Specific checks:

- **Q097 (current-state / count)** - the three upcoming events and the 'zero upcoming training programmes' finding were re-derived from `field_event_start_date >= 2026-08-19`; result identical. Snapshot-relative caveat correctly recorded.
- **Q016** - correctly flags that the India GHG Program '10% of industrial emissions / 268 MT / ~30 companies' figures are from a body dated 1 December 2014 sitting under a 2018 migration `published_at`. Verified in chunk text; the caveat is right.
- **Q102** - correctly uses past/unspecified tense for TERI-ITEC courses, whose records stop at the 2017-18 cycle. Verified.
- **Q110** - date-ordered list verified against `published_at DESC`; the legacy-timestamp caveat (2017-12-28 / 2018-01-09 / 2018-01-11 clusters) is accurate and does not affect the 2026 head of the list.
- **Q025/Q027/Q029/Q059/Q071** - 'ongoing'/'underway'/'latest' correctly presented as the CMS classification at snapshot rather than verified activity.
- **Q002** - the Pachauri 2016-vs-2017 conflict is preserved, not reconciled.

## 4. Aggregation / list judgement

| Question | Type | Original | Re-derived | Verdict |
| --- | --- | --- | --- | --- |
| Q025 | count + distribution | 594 total; themes Environment 64 / CC 46 / Energy 44 | 594 total **confirmed**; themes Environment 108 / Energy 74 / CC 69 | PARTIAL - total correct, distribution corrected |
| Q027 | count | 46 | **69** | PARTIAL - count corrected, 2 wrong example citations replaced |
| Q029 | count | 10 | **18** | PARTIAL - count corrected |
| Q085 | list | 30 service nodes | 30 | COMPLETE |
| Q097 | count | 3 upcoming events, 0 training | 3 / 0 | COMPLETE |
| Q107 | counts | research_papers 624, policy_brief 247, article 459, infographics 45, report 8 | identical | COMPLETE |
| Q110 | list + count | 12 most recent + 247 total | identical | COMPLETE |
| Q003 | list | 7 primary themes, 9 programmes | 7 / 9 | COMPLETE (illustrative row count for 'Environment' is 2216, the entry's facet note said 2215 - immaterial) |
| Q112 | list | SDG tag counts 264 / 23 / 17 | identical | COMPLETE (open set, as stated) |
| Q073 | list | 43 'Circular economy' tags | 43 | COMPLETE (open set, as stated) |

## 5. Contradictions

**Q002** - End of Dr R K Pachauri's tenure: 'Executive Vice-Chairman until 2017' vs 'demitted office as the executive vice chairman in March 2016'

- Source A: d7744c0b-989e-48b1-bce1-f83be2e4b85c (/mission-and-goals)
- Source B: 6f3c7dea-d0f9-4797-a7e3-5a00aef51d82 (/history)
- Both authoritative: True
- Handled correctly by the gold entry: **True**
- Both strings verified present in the respective documents. The gold entry records the conflict in notes and instructs graders to accept either. Correct handling; not silently reconciled.

**Q004** - Who administers GRIHA

- Source A: d7744c0b-989e-48b1-bce1-f83be2e4b85c (/mission-and-goals): TERI 'developed and currently administers' GRIHA
- Source B: 3e27858c-18df-4866-b384-eda5efdd5154 (Ratings & Certification service): GRIHA 'is administered and promoted by GRIHA Council', 'jointly developed by MNRE and TERI in 2007'
- Both authoritative: True
- Handled correctly by the gold entry: **True**
- Both strings verified present. Gold selects the more specific and more recent service node and records the conflict. Correct handling.

**Q004** - Number of TERI Centres of Excellence

- Source A: 98ad60e0-e960-4a46-b8c7-906ee0324d32 (Centres of Excellence hub): 9 centres
- Source B: 5b31ce53 (DBT-TERI CoE Advanced Biofuels) and 7c8f0a6a (CoE for Sustainable Habitats) exist as standalone pages but are absent from the hub
- Both authoritative: True
- Handled correctly by the gold entry: **True**
- Hub page independently verified to contain exactly 9 'Read More' centre links. Gold records the discrepancy and instructs graders to accept 9 or 11.

**Q027** - A project about climate adaptation is not themed Climate Change in the CMS

- Source A: field_ongoing_theme for 4b77a379 = ['Resource Efficiency & Governance']
- Source B: documents.title for 4b77a379 = 'Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South'
- Both authoritative: True
- Handled correctly by the gold entry: **False**
- The original gold treated this project as a Climate Change example on the basis of its title while its CMS theme says otherwise. Corrected: fact removed, citation replaced, and the classification risk recorded.

**Q080** - Who administers GRIHA

- Source A: d7744c0b-989e-48b1-bce1-f83be2e4b85c (/mission-and-goals): TERI 'developed and currently administers' GRIHA
- Source B: 3e27858c-18df-4866-b384-eda5efdd5154 (Ratings & Certification service): GRIHA 'is administered and promoted by GRIHA Council', 'jointly developed by MNRE and TERI in 2007'
- Both authoritative: True
- Handled correctly by the gold entry: **True**
- Both strings verified present. Gold selects the more specific and more recent service node and records the conflict. Correct handling.

## 6. Full judgement table

| ID | Question | Gold status | AI judgement | Conf. | Source quality | Facts S/P/U | Reason | Correction required |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q001 | What is the primary mission and vision of TERI? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 4/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q002 | Can you provide a brief history of The Energy and Resources Institute (TERI)? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q003 | What are TERI's core research areas and divisions? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q004 | What are TERI's flagship initiatives and centres of excellence? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q005 | Where are TERI's offices located, and how can I contact them? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 11/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q007 | What are TERI's major achievements and contributions to sustainable development? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 9/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q009 | Does TERI offer internships, fellowships, or career opportunities for students and researchers? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q010 | How can I stay updated on TERI's activities and announcements? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | HIGH | 4/0/0 | A publication title was quoted with the wrong preposition. The CMS title is 'Newsletters and Resources - Sustainable Buildings', not '... for Sustainable Buildings'. | YES |
| Q011 | What are TERI's latest research priorities? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q012 | What is TERI's contribution to India's Net-Zero 2070 goal? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 6/0/0 | A colon was inserted into a quoted report title that the source does not contain. | YES |
| Q014 | How does TERI support evidence-based policymaking at the state and national levels? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 10/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q015 | What kind of research does TERI conduct on sustainable agriculture? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q016 | Does TERI publish data or studies related to greenhouse gas (GHG) inventories? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 4/1/0 | A title was PARAPHRASED INSIDE QUOTATION MARKS ('...Ghana and other countries'). The actual title enumerates the countries. Paraphrasing inside a quotation is not permitted in a reference set. | YES |
| Q018 | What research is TERI conducting on climate finance? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q019 | What are TERI's latest studies on air quality and pollution management? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | The fact naming ICIMOD, NTNC and UK International Development had NO supporting citation: none of the eight cited documents contains those partner names. The consultation record that does name them was not cited. | YES |
| Q020 | What research is TERI undertaking on industrial decarbonization? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 9/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q021 | How does TERI contribute to national missions and international climate commitments? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q023 | What evidence-based policy tools has TERI developed? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 10/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q024 | How is TERI supporting the implementation of Sustainable Development Goals (SDGs)? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q025 | What are TERI's ongoing projects? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 3/1/0 | Aggregation methodology error: per-theme counts were derived from field_ongoing_theme[0] only, so multi-theme projects were counted under one theme instead of all applicable themes. | YES |
| Q027 | What climate change projects are currently underway? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 2/1/1 | Count derived from the first array element only, and both cited example projects were verified NOT to carry the Climate Change theme. | YES |
| Q029 | What initiatives is TERI running for clean energy access in rural areas? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 5/1/0 | Same first-element aggregation error as Q025/Q027. | YES |
| Q035 | What innovations and technologies are being demonstrated under ongoing projects? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 9/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q040 | What is green hydrogen and how is TERI working in this field? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 6/1/0 | Two facts cited no document containing them; one of those documents is a news-bundle node whose authorship cannot be established, so the claim was weakened accordingly. | YES |
| Q041 | What research is TERI conducting on battery energy storage systems? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q042 | How is TERI supporting India's energy transition? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q043 | What is TERI's work on solar energy technologies? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q044 | What is TERI's work on bioenergy and biofuels? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 9/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q045 | What research is being conducted on energy storage technologies? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 5/1/0 | Attribution error (joint Ember-TERI report credited to TERI alone) plus a figure taken from a news headline rather than source body text. | YES |
| Q046 | What innovations is TERI developing for energy access? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q048 | What is TERI's contribution to industrial decarbonization? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 6/0/0 | Same inserted colon in a quoted report title as Q012 (kept consistent between the near-duplicate pair). | YES |
| Q049 | What are TERI's initiatives in electric mobility and EV ecosystems? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 6/0/0 | Quoted policy-brief title did not match the source punctuation. | YES |
| Q050 | How does TERI support decentralized renewable energy systems? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q051 | What developments is TERI pursuing in clean cooking energy? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q052 | How does TERI approach climate adaptation and resilience? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q053 | What climate risk assessment methodologies does TERI use? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q055 | How does TERI support organizations in achieving net-zero goals? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q056 | How does TERI address air pollution in Indian cities? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | The city list in the emission-inventory fact named Faridabad, but no cited document covered it (the Faridabad study was cited only under Q016). | YES |
| Q057 | What research is TERI doing on climate finance and ESG? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | The 'Road to Baku' fact had no supporting citation among the ten cited documents. | YES |
| Q058 | How does TERI help organizations reduce their environmental footprint? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q059 | What are TERI's latest climate resilience projects? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q060 | What sustainability frameworks has TERI developed? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q061 | How does TERI support sustainable consumption and lifestyles? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q062 | What water conservation initiatives is TERI undertaking? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q063 | What innovative water management solutions is TERI researching? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q064 | What services and research does TERI offer on wastewater treatment and reuse? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/1/0 | A project title was paraphrased inside quotation marks: 'for urban and industrial sectors' instead of the actual 'for urban and peri-urban areas in India'. | YES |
| Q065 | How does TERI support climate-smart agriculture? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | The 'integrated climate-smart agricultural practices with the Government of Maharashtra' fact had no supporting citation; the evidence is in an annual-report PDF chunk. | YES |
| Q066 | What research is TERI conducting on food systems sustainability? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q067 | How does TERI work with local communities on forest conservation? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | Fact had no valid citation and was loosely paraphrased; correct authoritative source identified and wording aligned to it. | YES |
| Q068 | What is TERI's role in watershed management projects? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q069 | What biodiversity conservation programmes does TERI implement? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q070 | What nature-based solutions is TERI promoting? | GOLD_VERIFIED | **GOLD_CONFIRMED** | MEDIUM | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q071 | What ecosystem restoration and land restoration initiatives are underway? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q072 | What is the circular economy and why is it important? | GOLD_VERIFIED | **GOLD_AMBIGUOUS** | LOW | LOW | 2/2/1 | The definitional facts were unsupported by the cited documents, over-generalised from a plastics-scoped source, and one fact attributed another country's policy definition to TERI. | YES |
| Q073 | What circular economy projects is TERI implementing? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q074 | What research exists on waste-to-resource technologies? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q075 | How does TERI support plastic waste management? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | The fact asserting the article 'Towards a Circular Plastics Economy: India's Actions to #BeatPlasticPollution' had no supporting citation. | YES |
| Q076 | What are TERI's solutions for urban waste management and sanitation? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q077 | How can industries improve resource efficiency through circular practices? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q079 | What technologies are available for waste valorization? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q080 | What green building rating services does TERI provide, | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q082 | How can my company consult with TERI for carbon footprinting and ESG reporting? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q083 | Does TERI provide Life Cycle Assessment (LCA) services? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q084 | Can TERI assist in conducting an energy audit for my industrial facility? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q085 | What sustainability advisory services does TERI offer? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 3/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q086 | What benefits can organizations gain from TERI's environmental design consultancy? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q088 | How can TERI help organizations achieve resource efficiency? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q089 | What sustainability assessment tools are offered by TERI? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q090 | What services does TERI's NABL-accredited laboratory provide? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | HIGH | 5/0/0 | The IS:14543 packaged-drinking-water and EIB Laboratory facts were cited to the WEBSITE Annual Reports node, which does not contain them; the text is in an annual-report PDF attachment chunk. | YES |
| Q091 | Can TERI conduct air quality testing and monitoring? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q092 | What water quality testing services are available? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | HIGH | 5/0/0 | Same mis-citation as Q090: the IS:14543 / water-food-beverage / EIB Laboratory facts were attributed to the website Annual Reports node instead of the PDF chunk that holds them. | YES |
| Q093 | Does TERI offer soil testing and environmental analysis? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | HIGH | 4/0/0 | The EIB Laboratory / water-food-beverage testing fact had no cited document containing it. | YES |
| Q095 | What analytical capabilities are available through TERI's testing laboratories? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | HIGH | 5/0/0 | Same mis-citation as Q090/Q092 for the IS:14543 and EIB Laboratory analytical-capability facts. | YES |
| Q096 | What training programmes and workshops does TERI offer? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q097 | Are there any upcoming TERI training programmes? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q098 | Does TERI offer online learning and certification programmes? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q099 | Are certificates awarded upon successful completion of TERI programmes? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 3/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q100 | Does TERI provide capacity-building programmes for government officials? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q102 | What international training programmes are conducted by TERI? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 7/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q107 | How can I search TERI's research publications? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q109 | Can you recommend reports on climate change adaptation? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q110 | What policy briefs has TERI recently published? | GOLD_VERIFIED | **GOLD_NEEDS_CORRECTION** | MEDIUM | MEDIUM | 7/0/0 | Quoted policy-brief title did not match source punctuation. | YES |
| Q111 | Where can I download TERI's annual reports | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 4/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q112 | What publications are available on Sustainable Development Goals? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | MEDIUM | 8/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q113 | How can researchers obtain project reports and technical documents? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q119 | Which researchers work on AI and sustainability? | GOLD_VERIFIED | **GOLD_CONFIRMED** | MEDIUM | MEDIUM | 5/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |
| Q121 | How can organizations partner with TERI for research, innovation, policy advisory, or implementation projects? | GOLD_VERIFIED | **GOLD_CONFIRMED** | HIGH | HIGH | 6/0/0 | Independently verified: gold answer and all expected facts are supported by the cited authoritative sources; no contradictions or overstatements found. | no |

## 7. Non-SUPPORTED facts in detail

| ID | Fact (original) | Status | Note |
| --- | --- | --- | --- |
| Q016 | TERI published 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana and other countries'. | **PARTIALLY_SUPPORTED** | Title paraphrased inside quotation marks; the real title enumerates South Korea, Japan and Chile. |
| Q025 | The largest ongoing-project themes are Environment (64), Climate Change (46), Energy (44) and Sustainable Agriculture (41). | **PARTIALLY_SUPPORTED** | First-element derivation understates every theme and mis-orders Energy vs Climate Change. |
| Q027 | 46 ongoing project nodes carry the CMS theme 'Climate Change' as of the snapshot. | **PARTIALLY_SUPPORTED** | Count derived from field_ongoing_theme[0] only; the correct all-values derivation gives 69. |
| Q027 | Ongoing climate-change work includes 'Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South'. | **NOT_SUPPORTED** | This project is themed ['Resource Efficiency & Governance'], not Climate Change. Fact removed. |
| Q029 | The CMS records 10 ongoing project nodes under the 'Energy Access' theme at snapshot. | **PARTIALLY_SUPPORTED** | First-element derivation; all-values derivation gives 18. |
| Q040 | TERI has produced explainer content on the National Green Hydrogen Mission and 'A primer on green hydrogen'. | **PARTIALLY_SUPPORTED** | Document exists but sits in the news bundle; TERI authorship not established by the corpus. |
| Q045 | TERI analysis reported that battery-storage costs must drop about 15% to avoid new coal capacity. | **PARTIALLY_SUPPORTED** | Joint Ember-TERI report, not TERI alone; the 15% figure appears only in the third-party news headline, not in ingested body text. |
| Q064 | TERI runs 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and industrial sectors'. | **PARTIALLY_SUPPORTED** | Project title paraphrased inside quotation marks; actual title is '... for urban and peri-urban areas in India'. |
| Q072 | A circular economy is a closed-loop system in which materials constantly flow without leaking into the environment, keeping their value in the economy. | **PARTIALLY_SUPPORTED** | Source passage is scoped to plastics; generalisation is the gold author's, not the source's. |
| Q072 | The circular economy covers every stage of a product's lifetime, from production through to end-of-life. | **PARTIALLY_SUPPORTED** | Plastics-scoped in source; fact removed in the corrected set. |
| Q072 | The circular economy is framed around the 3Rs - reduce, reuse, recycle. | **NOT_SUPPORTED** | The 3Rs framing in the corpus is CHINA's definition of resource efficiency (545965cc) and JAPAN's Resource Circulation Strategy, not TERI's framing of the circular economy. Fact removed. |

## 8. Second-pass QC after corrections

- exactly 121 question IDs, Q001-Q121 contiguous, one record each, no duplicates
- exactly 87 GOLD_VERIFIED entries judged; no NEEDS_HUMAN_REVIEW or NO_SUPPORTED_ANSWER entry was included
- every judgement row cites at least one evidence source per fact
- every GOLD_VERIFIED entry still has a non-empty gold answer, at least one expected fact and at least one authoritative source or reproducible derivation after correction
- all 485 cited document_ids re-validated against MySQL `documents` after correction
- all cited claim_ids re-validated against MySQL `documents_assertion` (the 3 claim ids sit on Q034, which is NEEDS_HUMAN_REVIEW and out of scope)
- all aggregation derivations replaced with reproducible `JSON_CONTAINS` SQL where the first-element form was wrong
- no fact rests on a `documents_enrichment` LLM abstract (explicitly checked for Q067)
- known source contradictions preserved, not reconciled (Q002, Q004, Q080) and one newly found classification conflict recorded (Q027)
- no chatbot output was consulted; the chatbot was not run

**Result: 0 QC failures.**

