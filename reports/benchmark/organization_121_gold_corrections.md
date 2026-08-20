# Gold-set corrections applied after the independent judgement pass

- **Baseline (unchanged audit copy)**: `organization_121_gold_v1_original.json`
- **Corrected set**: `organization_121_gold.json` (v2)
- **Questions corrected**: 23 of 87 GOLD_VERIFIED (22 GOLD_NEEDS_CORRECTION + 1 GOLD_AMBIGUOUS)
- **Questions unchanged**: 64 GOLD_CONFIRMED, plus all 33 NEEDS_HUMAN_REVIEW and Q106 NO_SUPPORTED_ANSWER, which were out of scope for this pass

Correction-type legend: **facts** = a claim's content changed or was removed; **citations** = document ids added/removed; **counts** = an expected count changed; **methodology** = the derivation itself was wrong; **wording** = quotation/title accuracy; **attribution** = who made the claim; **scope** = the claim's scope was narrowed.

| ID | Types | Reason |
| --- | --- | --- |
| Q010 | wording | A publication title was quoted with the wrong preposition. The CMS title is 'Newsletters and Resources - Sustainable Buildings', not '... for Sustainable Buildings'. |
| Q012 | wording | A colon was inserted into a quoted report title that the source does not contain. |
| Q016 | wording, facts | A title was PARAPHRASED INSIDE QUOTATION MARKS ('...Ghana and other countries'). The actual title enumerates the countries. Paraphrasing inside a quotation is not permitted in a reference set. |
| Q019 | citations | The fact naming ICIMOD, NTNC and UK International Development had NO supporting citation: none of the eight cited documents contains those partner names. The consultation record that does name them was not cited. |
| Q025 | counts, methodology | Aggregation methodology error: per-theme counts were derived from field_ongoing_theme[0] only, so multi-theme projects were counted under one theme instead of all applicable themes. |
| Q027 | counts, methodology, citations | Count derived from the first array element only, and both cited example projects were verified NOT to carry the Climate Change theme. |
| Q029 | counts, methodology | Same first-element aggregation error as Q025/Q027. |
| Q040 | citations | Two facts cited no document containing them; one of those documents is a news-bundle node whose authorship cannot be established, so the claim was weakened accordingly. |
| Q045 | facts, attribution | Attribution error (joint Ember-TERI report credited to TERI alone) plus a figure taken from a news headline rather than source body text. |
| Q048 | wording | Same inserted colon in a quoted report title as Q012 (kept consistent between the near-duplicate pair). |
| Q049 | wording | Quoted policy-brief title did not match the source punctuation. |
| Q056 | citations | The city list in the emission-inventory fact named Faridabad, but no cited document covered it (the Faridabad study was cited only under Q016). |
| Q057 | citations | The 'Road to Baku' fact had no supporting citation among the ten cited documents. |
| Q064 | wording, citations | A project title was paraphrased inside quotation marks: 'for urban and industrial sectors' instead of the actual 'for urban and peri-urban areas in India'. |
| Q065 | citations | The 'integrated climate-smart agricultural practices with the Government of Maharashtra' fact had no supporting citation; the evidence is in an annual-report PDF chunk. |
| Q067 | citations, wording | Fact had no valid citation and was loosely paraphrased; correct authoritative source identified and wording aligned to it. |
| Q072 | facts, citations, scope | The definitional facts were unsupported by the cited documents, over-generalised from a plastics-scoped source, and one fact attributed another country's policy definition to TERI. |
| Q075 | citations | The fact asserting the article 'Towards a Circular Plastics Economy: India's Actions to #BeatPlasticPollution' had no supporting citation. |
| Q090 | citations | The IS:14543 packaged-drinking-water and EIB Laboratory facts were cited to the WEBSITE Annual Reports node, which does not contain them; the text is in an annual-report PDF attachment chunk. |
| Q092 | citations | Same mis-citation as Q090: the IS:14543 / water-food-beverage / EIB Laboratory facts were attributed to the website Annual Reports node instead of the PDF chunk that holds them. |
| Q093 | citations | The EIB Laboratory / water-food-beverage testing fact had no cited document containing it. |
| Q095 | citations | Same mis-citation as Q090/Q092 for the IS:14543 and EIB Laboratory analytical-capability facts. |
| Q110 | wording | Quoted policy-brief title did not match source punctuation. |

## Q010 - How can I stay updated on TERI's activities and announcements?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording
- **Reason**: A publication title was quoted with the wrong preposition. The CMS title is 'Newsletters and Resources - Sustainable Buildings', not '... for Sustainable Buildings'.
- **Authoritative evidence**: documents.title for 874fc35b-a477-4090-aef2-c0ed050d5d79 = 'Newsletters and Resources - Sustainable Buildings'
- **Source/document IDs**: `874fc35b-a477-4090-aef2-c0ed050d5d79`
- **Confidence after correction**: HIGH

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI publishes thematic newsletters including TERI CBS Newsletters, the Transport and Urban Governance newsletter, and Newsletters and Resources for Sustainable Buildings. | TERI publishes thematic newsletters including TERI CBS Newsletters, the Transport and Urban Governance newsletter, and Newsletters and Resources - Sustainable Buildings. |

---

## Q012 - What is TERI's contribution to India's Net-Zero 2070 goal?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording
- **Reason**: A colon was inserted into a quoted report title that the source does not contain.
- **Authoritative evidence**: documents.title for 2a310697-5393-4e1f-bd72-f22179e32011 = 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070' (no colon)
- **Source/document IDs**: `2a310697-5393-4e1f-bd72-f22179e32011`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI and GCCA India launched the 'Decarbonization Roadmap for the Indian Cement Sector: Net-Zero CO2 by 2070' in March 2025. | TERI and GCCA India launched the 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070' in March 2025. |
| gold_answer | rewritten | 'Decarbonization Roadmap for the Indian Cement Sector: Net-Zero CO2 by 2070' | 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070' |

---

## Q016 - Does TERI publish data or studies related to greenhouse gas (GHG) inventories?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording, facts
- **Reason**: A title was PARAPHRASED INSIDE QUOTATION MARKS ('...Ghana and other countries'). The actual title enumerates the countries. Paraphrasing inside a quotation is not permitted in a reference set.
- **Authoritative evidence**: documents.title for 93f819a5-01d8-472b-a547-b5ff8c4a4d72 = 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana, South Korea, Japan, and Chile'
- **Source/document IDs**: `93f819a5-01d8-472b-a547-b5ff8c4a4d72`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI published 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana and other countries'. | TERI published 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana, South Korea, Japan, and Chile'. |
| gold_answer | rewritten | 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana...' | 'Best Practices on National GHG Inventory Management System: Case studies from South Africa, Ghana, South Korea, Japan, and Chile' |

---

## Q019 - What are TERI's latest studies on air quality and pollution management?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The fact naming ICIMOD, NTNC and UK International Development had NO supporting citation: none of the eight cited documents contains those partner names. The consultation record that does name them was not cited.
- **Authoritative evidence**: Full-text scan of all cited documents for Q019: 'icimod'/'ntnc'/'bhutan' absent from 7ac1eb9f-a72c-48d6-9e98-89ce8a6783e7 (the cited forest-fire study). Present in f52ed80f-79af-4497-bd79-ab3f5ad19565
- **Source/document IDs**: `f52ed80f-79af-4497-bd79-ab3f5ad19565`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | f52ed80f-79af-4497-bd79-ab3f5ad19565 |

---

## Q025 - What are TERI's ongoing projects?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: counts, methodology
- **Reason**: Aggregation methodology error: per-theme counts were derived from field_ongoing_theme[0] only, so multi-theme projects were counted under one theme instead of all applicable themes.
- **Authoritative evidence**: SELECT JSON_LENGTH(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme')) n, COUNT(*) FROM documents WHERE bundle='ongoing_projects' AND source_type='website' GROUP BY 1 -> NULL:98, 1:360, 2:100, 3:24, 4:5, 5:3, 7:1, 8:2, 19:1. Re-derived with JSON_CONTAINS: Environment 108, Energy 74, Climate Change 69, Sustainable Agriculture 48, Energy Efficiency 40, Air 37, Water 35, Waste 32, Forest & Biodiversity 30, Transport 28, Sustainable Habitat 26, Buildings 21, Energy Access 18, Cities 17.
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | The largest ongoing-project themes are Environment (64), Climate Change (46), Energy (44) and Sustainable Agriculture (41). | Counting every value in the field_ongoing_theme array, the largest ongoing-project themes are Environment (108), Energy (74), Climate Change (69), Sustainable Agriculture (48), Energy Efficiency (40), Air (37), Water (35) and Waste (32). (Counting only the first array element - the original derivation - gives Environment 64, Climate Change 46, Energy 44, Sustainable Agriculture 41, which understates every theme and m |
| gold_answer | rewritten | They are distributed across themes led by Environment (64), Climate Change (46), Energy (44), Sustainable Agriculture (41), Air (31), Energy Efficiency (30), Water (27), Waste (25), Forest & Biodiversity (23), Transport (20), Microbes (19) and Buildings (19), with 98 carrying no theme; | Counting every theme value on each project, they are distributed across themes led by Environment (108), Energy (74), Climate Change (69), Sustainable Agriculture (48), Energy Efficiency (40), Air (37), Water (35), Waste (32), Forest & Biodiversity (30), Transport (28), Sustainable Habitat (26) and Buildings (21), with 98 carrying no theme at all; |
| source_ids(derivation) | rewritten | SELECT JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme[0]')), COUNT(*) ... GROUP BY 1 | CORRECTED all-values derivation: SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='ongoing_projects' AND JSON_CONTAINS(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme'), '"<theme>"') -- run per theme; the superseded first-element form was JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme[0]')) |
| notes | appended | - | JUDGEMENT CORRECTION: the original theme distribution used only the FIRST element of the field_ongoing_theme JSON array, but 135 of 594 ongoing projects carry two or more themes (100 have 2, 24 have 3, 5 have 4, 3 have 5, 1 has 7, 2 have 8, 1 has 19). Every per-theme figure was therefore understated and the Energy / Climate Change ordering was wrong. The total of 594 and the 98 untheme d nodes are |

---

## Q027 - What climate change projects are currently underway?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: counts, methodology, citations
- **Reason**: Count derived from the first array element only, and both cited example projects were verified NOT to carry the Climate Change theme.
- **Authoritative evidence**: JSON_CONTAINS re-derivation -> 69. field_ongoing_theme for 0d175a5b = ["Electricity and Renewables","Energy"]; for 4b77a379 = ["Resource Efficiency & Governance"]; for 0095f7d8 and 4043a8f6 = ["Climate Change"].
- **Source/document IDs**: `0095f7d8-821f-408d-84b9-f488b96a67f1`, `4043a8f6-e116-4cd8-92ee-d6afe44f1e24`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | 46 ongoing project nodes carry the CMS theme 'Climate Change' as of the snapshot. | 69 ongoing project nodes carry the CMS theme 'Climate Change' anywhere in their field_ongoing_theme array as of the snapshot (46 carry it as the first array element). |
| expected_facts | rewritten | Ongoing climate-change projects include SHEETAL: Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All. | Ongoing climate-change projects include 'SHEETAL: Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All' (document 0095f7d8, field_ongoing_theme ["Climate Change"]). |
| expected_facts | rewritten | Ongoing climate-change work includes 'Preparedness towards implementing the Enhanced Transparency Framework and tracking NDCs'. | Ongoing climate-change work includes 'Preparedness towards implementing Enhanced Transparency Framework and tracking NDCs' (document 4043a8f6, field_ongoing_theme ["Climate Change"]). |
| expected_facts | removed | Ongoing climate-change work includes 'Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South'. | - |
| gold_answer | rewritten | The CMS classifies 46 ongoing project nodes under the theme 'Climate Change' as of the snapshot. Representative current examples include SHEETAL (Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All), Just Transition, Mapping Policies and Stakeholders on Climate Adaptation for Crop-Based Systems in the Global South, Preparedness towards implementing the Enhanced Transparency Framework and t | The CMS classifies 69 ongoing project nodes under the theme 'Climate Change' (counting the theme anywhere in the field_ongoing_theme array; 46 carry it as the first element). Verified current examples include 'SHEETAL: Alliance for Sustainable Habitat, Energy Efficiency and Thermal Comfort for All' and 'Preparedness towards implementing Enhanced Transparency Framework and tracking NDCs', both of which carry field_ong |
| source_ids(derivation) | rewritten | SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='ongoing_projects' AND JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme[0]'))='Climate Change' -> 46 | CORRECTED: SELECT COUNT(*) FROM documents WHERE source_type='website' AND bundle='ongoing_projects' AND JSON_CONTAINS(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme'), '"Climate Change"') -> 69 (superseded first-element form -> 46) |
| document_ids | removed | 0d175a5b-bf3b-4dab-9d36-a80382dad47f | - |
| document_ids | removed | 4b77a379-bff3-4335-a2b8-e6a98ee470ad | - |
| document_ids | added | - | 0095f7d8-821f-408d-84b9-f488b96a67f1, 4043a8f6-e116-4cd8-92ee-d6afe44f1e24 |
| notes | appended | - | JUDGEMENT CORRECTIONS: (1) expected_count raised from 46 to 69 - the original used field_ongoing_theme[0] only, excluding projects where Climate Change is a secondary theme, which is the wrong reading of 'What climate change projects are underway?'. (2) BOTH originally cited example documents were wrong: 0d175a5b 'Just Transition' is themed ["Electricity and Renewables","Energy"] and 4b77a379 'Map |

---

## Q029 - What initiatives is TERI running for clean energy access in rural areas?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: counts, methodology
- **Reason**: Same first-element aggregation error as Q025/Q027.
- **Authoritative evidence**: JSON_CONTAINS re-derivation for 'Energy Access' -> 18; first-element form -> 10.
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | The CMS records 10 ongoing project nodes under the 'Energy Access' theme at snapshot. | The CMS records 18 ongoing project nodes carrying the 'Energy Access' theme anywhere in their field_ongoing_theme array at snapshot (10 carry it as the first array element). |
| gold_answer | rewritten | under the CMS theme 'Energy Access' (10 ongoing project nodes at snapshot) | under the CMS theme 'Energy Access' (18 ongoing project nodes at snapshot counting the theme at any array position; 10 as the first element) |
| source_ids(derivation) | rewritten | SELECT COUNT(*) FROM documents WHERE bundle='ongoing_projects' AND JSON_UNQUOTE(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme[0]'))='Energy Access' -> 10 | CORRECTED: SELECT COUNT(*) FROM documents WHERE bundle='ongoing_projects' AND source_type='website' AND JSON_CONTAINS(JSON_EXTRACT(raw_meta,'$.field_ongoing_theme'), '"Energy Access"') -> 18 (superseded first-element form -> 10) |
| notes | appended | - | JUDGEMENT CORRECTION: count raised from 10 to 18 for the same first-element aggregation error described in Q025/Q027. |

---

## Q040 - What is green hydrogen and how is TERI working in this field?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: Two facts cited no document containing them; one of those documents is a news-bundle node whose authorship cannot be established, so the claim was weakened accordingly.
- **Authoritative evidence**: documents.title 'Harnessing the Potential of Bio-Resources to Produce Low Carbon Bio-Hydrogen' = 4b069eb5-094e-4a3b-a7bc-d50f284c3c38 (policy_brief, website); 'A primer on green hydrogen' = 42a753ed-1b7f-46ad-bbb0-3363b572386a (news, website). Neither was in the original citation list.
- **Source/document IDs**: `4b069eb5-094e-4a3b-a7bc-d50f284c3c38`, `42a753ed-1b7f-46ad-bbb0-3363b572386a`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI has produced explainer content on the National Green Hydrogen Mission and 'A primer on green hydrogen'. | TERI's site carries explainer content on green hydrogen, including 'A primer on green hydrogen' (document 42a753ed) and a video explainer on the National Green Hydrogen Mission; note the primer sits in the third-party-heavy `news` bundle, so its TERI authorship is not established by the corpus. |
| document_ids | added | - | 4b069eb5-094e-4a3b-a7bc-d50f284c3c38, 42a753ed-1b7f-46ad-bbb0-3363b572386a |
| notes | appended | - | JUDGEMENT CORRECTIONS: two facts had no supporting citation - the bio-hydrogen policy brief (now cited as 4b069eb5-094e-4a3b-a7bc-d50f284c3c38) and 'A primer on green hydrogen' (now cited as 42a753ed-1b7f-46ad-bbb0-3363b572386a). The primer is filed in the `news` bundle, so the fact was reworded to stop asserting TERI authorship of it. |

---

## Q045 - What research is being conducted on energy storage technologies?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: facts, attribution
- **Reason**: Attribution error (joint Ember-TERI report credited to TERI alone) plus a figure taken from a news headline rather than source body text.
- **Authoritative evidence**: Chunk text of 9858e812-9ecf-4358-a313-98e5bff9faf2: 'The report compiled by global energy think tank Ember and the Delhi-based The Energy and Resources Institute (TERI) says if the BESS costs continue to decline at the current rate of 7 per cent annually, India's power sector will see coal generation plateauing until 2032...'
- **Source/document IDs**: `9858e812-9ecf-4358-a313-98e5bff9faf2`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI analysis reported that battery-storage costs must drop about 15% to avoid new coal capacity. | A joint Ember-TERI report addressed battery-storage costs and coal capacity: the source text states that if BESS costs keep declining at the current rate of 7% annually, India's coal generation will plateau until 2032 while additional coal capacity may still be needed for non-solar hours. The '15%' figure appears only in a third-party news headline, not in the ingested body text, and the report is Ember-TERI, not TER |
| gold_answer | rewritten | analysis that battery-storage costs must fall 15% to avoid new coal capacity; | a joint Ember-TERI analysis of battery-storage cost trajectories and coal capacity (body text: 7% annual BESS cost decline, coal plateauing to 2032); |
| notes | appended | - | JUDGEMENT CORRECTION - ATTRIBUTION: the only source for the battery-cost fact is a third-party news node (9858e812) whose body attributes the report to 'global energy think tank Ember and the Delhi-based The Energy and Resources Institute (TERI)'. The original fact credited TERI alone and quoted a 15% figure that appears only in the news headline, not in the ingested text. Corrected to joint attri |

---

## Q048 - What is TERI's contribution to industrial decarbonization?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording
- **Reason**: Same inserted colon in a quoted report title as Q012 (kept consistent between the near-duplicate pair).
- **Authoritative evidence**: documents.title for 2a310697-5393-4e1f-bd72-f22179e32011 has no colon.
- **Source/document IDs**: `2a310697-5393-4e1f-bd72-f22179e32011`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI and GCCA India produced the 'Decarbonization Roadmap for the Indian Cement Sector: Net-Zero CO2 by 2070'. | TERI and GCCA India produced the 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070'. |
| gold_answer | rewritten | 'Decarbonization Roadmap for the Indian Cement Sector: Net-Zero CO2 by 2070' | 'Decarbonization Roadmap for the Indian Cement Sector Net-Zero CO2 by 2070' |

---

## Q049 - What are TERI's initiatives in electric mobility and EV ecosystems?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording
- **Reason**: Quoted policy-brief title did not match the source punctuation.
- **Authoritative evidence**: documents.title for 80bd4f12-3c7b-4aef-a1d0-49564f318a67 = 'Let’s Electrify- Accelerating Electric Vehicle Adoption and Awareness in India'
- **Source/document IDs**: `80bd4f12-3c7b-4aef-a1d0-49564f318a67`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI published the policy brief 'Let's Electrify - Accelerating Electric Vehicle Adoption and Awareness in India' (September 2025). | TERI published the policy brief 'Let’s Electrify- Accelerating Electric Vehicle Adoption and Awareness in India' (September 2025). |
| gold_answer | rewritten | 'Let's Electrify - Accelerating Electric Vehicle Adoption and Awareness in India' | 'Let’s Electrify- Accelerating Electric Vehicle Adoption and Awareness in India' |

---

## Q056 - How does TERI address air pollution in Indian cities?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The city list in the emission-inventory fact named Faridabad, but no cited document covered it (the Faridabad study was cited only under Q016).
- **Authoritative evidence**: 'faridabad' absent from all Q056 cited documents; present as documents.title 'Emission Inventorisation for Faridabad Town' = 7e50bb16-8222-4a3a-801b-6662271c3ef0
- **Source/document IDs**: `7e50bb16-8222-4a3a-801b-6662271c3ef0`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | 7e50bb16-8222-4a3a-801b-6662271c3ef0 |

---

## Q057 - What research is TERI doing on climate finance and ESG?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The 'Road to Baku' fact had no supporting citation among the ten cited documents.
- **Authoritative evidence**: 'road to baku' absent from all Q057 cited documents; present as documents.title 'Road to Baku: The New Collective Quantified Goal on Climate Finance' = 435e7517-f469-405d-9f26-a669d48a4101 (policy_brief, website)
- **Source/document IDs**: `435e7517-f469-405d-9f26-a669d48a4101`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | 435e7517-f469-405d-9f26-a669d48a4101 |

---

## Q064 - What services and research does TERI offer on wastewater treatment and reuse?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording, citations
- **Reason**: A project title was paraphrased inside quotation marks: 'for urban and industrial sectors' instead of the actual 'for urban and peri-urban areas in India'.
- **Authoritative evidence**: documents.title for 3029c6e2-8c33-403e-a41d-fb05e9f16e04 = 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and peri-urban areas in India'
- **Source/document IDs**: `3029c6e2-8c33-403e-a41d-fb05e9f16e04`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI runs 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and industrial sectors'. | TERI runs 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and peri-urban areas in India'. |
| gold_answer | rewritten | 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and industrial sectors' | 'Unlocking wastewater treatment, water re-use and resource recovery opportunities for urban and peri-urban areas in India' |

---

## Q065 - How does TERI support climate-smart agriculture?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The 'integrated climate-smart agricultural practices with the Government of Maharashtra' fact had no supporting citation; the evidence is in an annual-report PDF chunk.
- **Authoritative evidence**: 'Integrated Climate Smart Agricultural practices', Government of Maharashtra (GoM) appears in inbody:0e41da3dbea8c5135d3a22191ed94b72670c9afc (page / pdf_attachment, Annual Reports); absent from all originally cited Q065 documents.
- **Source/document IDs**: `inbody:0e41da3dbea8c5135d3a22191ed94b72670c9afc`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | inbody:0e41da3dbea8c5135d3a22191ed94b72670c9afc |

---

## Q067 - How does TERI work with local communities on forest conservation?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations, wording
- **Reason**: Fact had no valid citation and was loosely paraphrased; correct authoritative source identified and wording aligned to it.
- **Authoritative evidence**: Chunk text of 00d5790d-09eb-40e8-ae8f-8fdad3c306f4: 'More than 300 million people derive full or partial livelihood and sustenance need from forests... the minor forest produce (MFP) sector is India's largest unorganized sector... legally empowered with ownership and governance of minor forest produce (MFP) through two important legislations of Government of India, namely PESA, 1996 and Forest Rights Act, 2006... TERI has conducted research study for establishing methodology for determining minimum support price for 12 MFPS and on the basis of 12000 household surveys, 1200 work studies and more than 100 Focus Group Discussions.'
- **Source/document IDs**: `00d5790d-09eb-40e8-ae8f-8fdad3c306f4`, `aaf55d78-b81b-408a-a287-337feb531c3f`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | TERI's policy work on Minimum Support Price for Minor Forest Produce notes that over 300 million people rely on forests for their livelihoods and references the PESA Act 1996 and the Forest Rights Act 2006. | TERI's policy work on Minimum Support Price of Minor Forest Produce states that more than 300 million people derive full or partial livelihood and sustenance from forests, that the MFP sector is India's largest unorganized sector, and that forest dwellers are legally empowered with ownership and governance of MFP through PESA, 1996 and the Forest Rights Act, 2006; TERI's study established an MSP methodology for 12 MF |
| document_ids | added | - | 00d5790d-09eb-40e8-ae8f-8fdad3c306f4, aaf55d78-b81b-408a-a287-337feb531c3f |
| notes | appended | - | JUDGEMENT CORRECTION: the MFP/MSP fact originally cited only the /policy page and the natural-resources capacity-building service node, neither of which contains it. An earlier concern that this fact came from an LLM-generated documents_enrichment abstract was CHECKED AND DISPROVED: the statements are present verbatim in real Qdrant chunk text of the MFP policy brief (website node 00d5790d-09eb-40 |

---

## Q072 - What is the circular economy and why is it important?

- **AI judgement**: `GOLD_AMBIGUOUS`
- **Correction types**: facts, citations, scope
- **Reason**: The definitional facts were unsupported by the cited documents, over-generalised from a plastics-scoped source, and one fact attributed another country's policy definition to TERI.
- **Authoritative evidence**: 'closed loop' present only in be74de52-11c3-470c-94fa-bdbeaa962717 (article, website), plastics-scoped. '3Rs (reduce-reuse-recycle)' present in 545965cc-9439-40e9-92a5-37daf0f49cbe describing China's Circular Economy Promotion Law, and in the Japan Industry Federation section of the plastics article. Absent from 0d106e9d, b8b7e710, 280770ce, f5665b91.
- **Source/document IDs**: `be74de52-11c3-470c-94fa-bdbeaa962717`
- **Confidence after correction**: LOW

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | A circular economy is a closed-loop system in which materials constantly flow without leaking into the environment, keeping their value in the economy. | The corpus's only definitional passage is scoped to PLASTICS: 'Circular economy involves every stage of a plastic product's lifetime from its production till it reaches the customer and ends up as plastic waste. It refers to a closed loop system in which the materials constantly flow without leaking into the environment, keeping the value of plastics in the economy.' A general-purpose definition of the circular econo |
| expected_facts | removed | The circular economy covers every stage of a product's lifetime, from production through to end-of-life. | - |
| expected_facts | removed | The circular economy is framed around the 3Rs - reduce, reuse, recycle. | - |
| gold_answer | rewritten | As described in TERI's material, a circular economy is a closed-loop system in which materials constantly flow without leaking into the environment, keeping their value in the economy - covering every stage of a product's lifetime from production through use to end-of-life - and is framed around the 3Rs (reduce, reuse, recycle). TERI's own framing of why it matters: | The corpus contains NO general definition of the circular economy. The only definitional passage is plastics-scoped, in TERI's article 'Towards a Circular Plastics Economy': circular economy 'involves every stage of a plastic product's lifetime from its production till it reaches the customer and ends up as plastic waste' and 'refers to a closed loop system in which the materials constantly flow without leaking into  |
| document_ids | added | - | be74de52-11c3-470c-94fa-bdbeaa962717 |
| notes | appended | - | JUDGEMENT: RECLASSIFIED GOLD_AMBIGUOUS. Three problems were found. (1) None of the four originally cited documents contains a circular-economy definition at all (verified by full-text scan: 'closed loop' absent from all four; f5665b91 does not even contain the phrase 'circular economy'). (2) The definition the gold stated was generalised from a PLASTICS-scoped passage in be74de52-11c3-470c-94fa-bd |

---

## Q075 - How does TERI support plastic waste management?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The fact asserting the article 'Towards a Circular Plastics Economy: India's Actions to #BeatPlasticPollution' had no supporting citation.
- **Authoritative evidence**: documents.title 'Towards a Circular Plastics Economy: India’s Actions to #BeatPlasticPollution' = be74de52-11c3-470c-94fa-bdbeaa962717 (article, website); absent from the original Q075 citation list.
- **Source/document IDs**: `be74de52-11c3-470c-94fa-bdbeaa962717`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | be74de52-11c3-470c-94fa-bdbeaa962717 |

---

## Q090 - What services does TERI's NABL-accredited laboratory provide?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The IS:14543 packaged-drinking-water and EIB Laboratory facts were cited to the WEBSITE Annual Reports node, which does not contain them; the text is in an annual-report PDF attachment chunk.
- **Authoritative evidence**: '14543', 'EIB Laboratory', 'packaged drinking water' and 'hydrocarbon' all present in inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2 (page / pdf_attachment, Annual Reports); absent from db669bde (page / website) and e071ea2f (Brochures).
- **Source/document IDs**: `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2 |

---

## Q092 - What water quality testing services are available?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: Same mis-citation as Q090: the IS:14543 / water-food-beverage / EIB Laboratory facts were attributed to the website Annual Reports node instead of the PDF chunk that holds them.
- **Authoritative evidence**: Same as Q090 - evidence text located in inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2
- **Source/document IDs**: `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2 |
| confidence | changed | HIGH | MEDIUM |

---

## Q093 - Does TERI offer soil testing and environmental analysis?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: The EIB Laboratory / water-food-beverage testing fact had no cited document containing it.
- **Authoritative evidence**: 'EIB' absent from all originally cited Q093 documents; present in inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2
- **Source/document IDs**: `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2 |

---

## Q095 - What analytical capabilities are available through TERI's testing laboratories?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: citations
- **Reason**: Same mis-citation as Q090/Q092 for the IS:14543 and EIB Laboratory analytical-capability facts.
- **Authoritative evidence**: Same as Q090 - evidence text located in inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2
- **Source/document IDs**: `inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| document_ids | added | - | inbody:0e0407abe9359f9f2848c2d0999c513ec6df37b2 |

---

## Q110 - What policy briefs has TERI recently published?

- **AI judgement**: `GOLD_NEEDS_CORRECTION`
- **Correction types**: wording
- **Reason**: Quoted policy-brief title did not match source punctuation.
- **Authoritative evidence**: documents.title for 485727f8-66d5-428d-be6e-858c1f7a6a39 = 'Fly Ash Utilization and Transportation- Increasing Rail Share in Fly Ash Transportation'
- **Source/document IDs**: `485727f8-66d5-428d-be6e-858c1f7a6a39`
- **Confidence after correction**: MEDIUM

| Field | Action | Original | Corrected |
| --- | --- | --- | --- |
| expected_facts | rewritten | 'Fly Ash Utilization and Transportation - Increasing Rail Share in Fly Ash Transportation' was published on 21 July 2026. | 'Fly Ash Utilization and Transportation- Increasing Rail Share in Fly Ash Transportation' was published on 21 July 2026. |
| gold_answer | rewritten | 'Fly Ash Utilization and Transportation - Increasing Rail Share in Fly Ash Transportation' | 'Fly Ash Utilization and Transportation- Increasing Rail Share in Fly Ash Transportation' |

---

