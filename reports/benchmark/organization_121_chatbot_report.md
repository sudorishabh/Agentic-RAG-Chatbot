# Baseline chatbot evaluation - 86 validated gold questions

- **Endpoint**: `POST http://localhost:8000/chat (real production SSE pipeline, app.main)` - the real production SSE pipeline, no stub
- **Retrieval telemetry**: `POST http://localhost:8000/search (same pipeline, read-only)` (same pipeline, called separately because the /chat SSE contract does not expose per-block detail)
- **Date**: 2026-08-19 | **Gold set**: `organization_121_gold.json` (v2, corrected)
- **Eligibility**: gold status GOLD_VERIFIED and judgement in {GOLD_CONFIRMED, GOLD_NEEDS_CORRECTION}
- **Scope**: 86 questions, not 87: Q072 was reclassified GOLD_AMBIGUOUS by the judgement pass and is excluded by the stated rule (64 CONFIRMED + 22 NEEDS_CORRECTION = 86)
- **Configuration was not touched.** `graph_routing_enabled=True`, `graph_retrieval_enabled=False`, `semantic_cache_enabled=False`, `retrieval_top_k=6`, `website_max_slots=2`, `pdf_max_slots=2`, `faithfulness_check=False`, model `gpt-4o-mini`.

## A. Executive summary

| Verdict | Count | Share |
| --- | --- | --- |
| CORRECT | 9 | 10% |
| PARTIALLY_CORRECT | 65 | 76% |
| INCORRECT | 4 | 5% |
| UNSUPPORTED | 0 | 0% |
| NO_ANSWER | 8 | 9% |
| SYSTEM_ERROR | 0 | 0% |
| **Total** | **86** | 100% |

- **Strict success rate (CORRECT only): 10.5%**
- **Usable-answer rate (CORRECT or PARTIALLY_CORRECT): 86.1%**
- Zero system errors, zero timeouts, zero malformed responses across 86 requests.
- **No hallucinations detected.** Every emitted citation resolved to a real corpus document, and a sample of claims the gold did not contain (Food Testing Laboratory, 'over 2000 industrial energy audits', River Bank Filtration, Joint Forest Management Committees, ResBuild India, UI-ASSIST, TERI Climate Tool Suite) was checked against chunk text and found genuine. The system's problem is not invention - it is *which* evidence it finds.
- Latency: mean 9113 ms, p50 9272 ms, p90 10749 ms, p95 11306 ms, max 14802 ms.

### The headline finding

**The authoritative source the gold identifies was retrieved for only 42% of questions, and only 33% of answers cite even one gold document.** On average 0.48 gold documents reach retrieval per question. Answers are fluent, on-topic and genuinely grounded - but grounded in press releases, annual-report PDFs and brochures rather than the canonical service nodes, thematic pages and hub pages that authoritatively answer organisational questions. That single pattern explains most of the 65 PARTIALLY_CORRECT verdicts.

## B. Failure breakdown by layer

| Layer | Count | Reading |
| --- | --- | --- |
| GENERATION | 39 | correct evidence reached context; the model omitted or under-used it |
| QDRANT_RETRIEVAL | 26 | the authoritative document was never retrieved |
| RANKING | 3 | structured/list mechanism returned off-topic items while correct blocks were retrieved |
| TEMPORAL_INTERPRETATION | 2 | stale content presented as current, or no date filtering on 'upcoming' |
| CONTEXT_BUILDING | 2 | right document retrieved, wrong chunk admitted to context |
| SCOPE_HANDLING | 2 | answered about India or generic practice instead of TERI |
| GRAPH_DATA | 1 | CMS/graph facet needed for the answer is not on the answer path |
| QUERY_UNDERSTANDING | 1 | intent misclassification discarded usable evidence |
| CITATION | 1 | cited document does not support the specific claim |

## C. Failure breakdown by severity

| Severity | Count |
| --- | --- |
| CRITICAL | 4 |
| HIGH | 9 |
| MEDIUM | 45 |
| LOW | 19 |

**CRITICAL (4):** Q079 (QUERY_UNDERSTANDING), Q091 (GENERATION), Q112 (RANKING), Q119 (RANKING). These are cases where the required evidence was demonstrably in hand and the system still produced nothing usable or produced an unrelated list.

## D. Graph vs Qdrant vs hybrid

- `graph_routing_enabled` = **True**, `graph_retrieval_enabled` = **False**, budget = **3.0s**.
- **Questions where the graph contributed facts to an answer: 0 of 86.**
- Independent replay of the production router (`policy.attempt`, the same function the retrieval path calls) gave these outcomes: `{'timed_out': 3, 'circuit_open': 83}`. The first three attempts exceeded the 3-second budget and the circuit breaker then short-circuited the remaining 83 without trying.
- Consequently the advertised architecture - *graph + Qdrant -> combined context* - did not run. Every answer in this baseline is Qdrant-dense-only. The graph could not suppress prose evidence for narrative questions because it never returned any.
- Two data-layer defects were observed while reading the graph, and are recorded rather than fixed: (1) the claim template selects `c.object_literal`, but `Claim` nodes in Neo4j carry no such property (Neo4j emits a `property key does not exist` warning on every routed query); (2) the projected claim set still ends effectively in 2021, so no current-state relationship question is graph-answerable even when the route succeeds.

### Qdrant behaviour

- Context blocks admitted: `{'5': 75, '6': 2, '4': 2, '0': 3, '2': 1, '10': 3}` - the overwhelming mode is 5, consistent with `website_max_slots=2` + `pdf_max_slots=2` + one conditional slot.
- Answers with zero context blocks: **3** (Q079, Q083, Q091) - all three are refusals/deflections.
- **Structural note that bears on fairness:** several gold entries legitimately span 10-31 authoritative documents (Q085 lists 31 service nodes; Q043 seventeen solar sources). A 5-block context cannot carry them, so full fact coverage was unattainable for those questions regardless of retrieval quality. Those cases are marked `failure_class` C or `G+C` and should not be read as pure system defects.
- No evidence was found in this run that the known tokenisation classes (24x7/24/7 variants, acronyms, lowercase names, punctuation) affected any result; none of the 86 questions exercises them directly. Short project names and title-based lookups DID fail, but via the structured/list mechanism (Q112, Q119) rather than tokenisation.

## E. Citation correctness

| Metric | Value |
| --- | --- |
| Answers with at least one citation | 83 / 86 |
| Answers with no citation at all | 3 (Q079, Q083, Q091) |
| Answers citing at least one gold document | 28 (33%) |
| Questions where any gold document was retrieved | 36 (42%) |
| Fabricated / non-resolving citations | 0 |
| Citations that do not support the claim made | 1 (Q111) |

Citation *mechanics* are sound - numbered markers map to real documents with real URLs, and nothing was invented. Citation *alignment* with the authoritative sources is weak, which is a restatement of the retrieval finding rather than a separate defect. Q110 is the one question where all ten citations resolve to gold documents.

## F. Temporal correctness

- **Q002 - stale presented as current (HIGH).** "As of 2023, TERI is celebrating its 50th anniversary" is written in the present tense at a 2026 reference date, taken from a dated press release. This is exactly the failure mode the gold set was built to catch.
- **Q097 - no date filtering on 'upcoming' (MEDIUM).** Asked for upcoming training programmes, retrieval returned six *past* programmes (TERI-DST, TERI-ITEC 2013-15) and the system then refused. The documented answer is a negative with evidence: no upcoming training programme is listed, and the only three future-dated events are a memorial lecture, a UNCCD COP17 panel and a WCEF session. Nothing in the answer path filters `field_event_start_date`.
- **Q059 / Q025 / Q027 / Q071 - unevidenced recency.** Words like "latest", "currently" and "underway" are reproduced in the answers without any date ordering or currency check behind them.
- No case was found of a *historical* fact being asserted with a wrong date. The temporal problem in this baseline is recency handling, not date accuracy.

## G. Retrieval vs generation

| Class | Count | Meaning |
| --- | --- | --- |
| G | 38 | generation failure - correct evidence reached context and was under-used |
| R | 27 | retrieval failure - the authoritative document never reached context |
| R+G | 4 | both retrieval and generation contributed |
| Q+R | 3 | routing plus retrieval |
| G+C | 2 | generation plus a gold/benchmark breadth limitation |
| Q+G | 2 | routing plus generation |
| Q | 1 | query understanding / intent routing |

Read carefully, this is close to an even split, and that is the most actionable result in the report: **38 generation-side and 27 retrieval-side failures.** In the 38 generation cases the authoritative document was retrieved and often cited, and the model still omitted most of what it contained - Q001 (goals and values on the page it cited), Q014 (the /policy page's specifics), Q007, Q055 (TERI CBS on a retrieved page), Q091 and Q093 (refusals with the correct service node in context). Fixing retrieval alone would therefore not fix the majority of these questions.

## H. Twenty worst responses

### 1. Q079 - What technologies are available for waste valorization?

- **Verdict**: `NO_ANSWER` | **Layer**: `QUERY_UNDERSTANDING` | **Severity**: `CRITICAL` | **Class**: query understanding/routing
- **Gold expected** (8 facts, 13 authoritative documents): TEAM (TERI's Enhanced Acidification and Methanation) converts organic waste into biogas. ...
- **Chatbot returned**: I primarily assist with questions grounded in your organization's documents. If you have specific inquiries about waste valorization or related topics, feel free to ask!
- **Evidence retrieved**: Market development for clean energy sector: focus on (MSW) municipal solid waste based energy projects, TERI's enhanced acidification and methanation technology, Download, TERI Highlights Workforce Imperatives for India's Clean Energy Ambitions at ICC Global Business Summit 2025 | context blocks: 0 | gold docs retrieved: 1/13
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 13 verified sources
- **Root cause**: Misrouted to the chitchat intent and deflected with 'I primarily assist with questions grounded in your organization's documents', returning zero context blocks and zero citations. This is a plain factual question about waste-valorization technologies, and retrieval had already surfaced the TERI enhanced acidification and methanation page - a gold document. An intent-classification error silently discarded usable evidence.

### 2. Q091 - Can TERI conduct air quality testing and monitoring?

- **Verdict**: `NO_ANSWER` | **Layer**: `GENERATION` | **Severity**: `CRITICAL` | **Class**: generation failure
- **Gold expected** (5 facts, 4 authoritative documents): TERI provides air-quality monitoring through a NABL-accredited laboratory. ...
- **Chatbot returned**: I can help you find information on that. You might want to check the relevant documents or articles in the knowledge base for details on TERI's capabilities regarding air quality testing and monitoring. If you have specific questions or need assistance, let me know!
- **Evidence retrieved**: Air Quality Research, Explainer: How evidence-based actions can help achieve breathable air in Indian cities, TERI’s Solutions for Sustainable Development, Brochures | context blocks: 0 | gold docs retrieved: 1/4
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 4 verified sources
- **Root cause**: Deflects with a meta-response and zero used chunks while block 1 retrieved is the Air Quality Research service node - the exact gold source, which states TERI provides monitoring through a NABL-accredited laboratory. The required evidence reached retrieval and the model declined to use it. The clearest generation-side failure in the run.

### 3. Q112 - What publications are available on Sustainable Development Goals?

- **Verdict**: `INCORRECT` | **Layer**: `RANKING` | **Severity**: `CRITICAL` | **Class**: routing and retrieval
- **Gold expected** (8 facts, 14 authoritative documents): TERI published the policy brief 'India and Sustainable Development Goals (SDGs)'. ...
- **Chatbot returned**: Here is what I found: - Decentralise education, create jobs (https://teriin.org/opinion/decentralise-education-create-jobs) - WCEF2026 Accelerator Session: Circular Public Procurement and Ecolabels (https://teriin.org/event/wcef2026-accelerator-session-circular-public-procurement-and-ecolabels) - Ch ...
- **Evidence retrieved**: Sustainable Development Goals, Understanding sustainable development, Sustainable Development Goals, Sustainable Development Goals | context blocks: 10 | gold docs retrieved: 1/14
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 14 verified sources
- **Root cause**: Structured path returned a list dominated by items with no SDG-publication relationship at all - 'Decentralise education, create jobs', a Chandigarh University children's science congress workshop, a WCEF accelerator session, a BioE3 video - while the retrieval blocks were four copies of the correct Sustainable Development Goals page. Ten citations were emitted, none matching a gold document. The list mechanism and the retrieved evidence disagree completely.

### 4. Q119 - Which researchers work on AI and sustainability?

- **Verdict**: `INCORRECT` | **Layer**: `RANKING` | **Severity**: `CRITICAL` | **Class**: routing and retrieval
- **Gold expected** (5 facts, 7 authoritative documents): Dr Jitendra Vir Sharma and Mr Sayanta Ghosh are the recorded authors of 'Artificial intelligence for restoring land: A review of land degradation mapping, climate change prediction and ecosystem service valuation'. ...
- **Chatbot returned**: Here is what I found: - Decentralise education, create jobs (https://teriin.org/opinion/decentralise-education-create-jobs) - Mobius Foundation's ICSE 2026 to Bring Global Sustainability Leaders Together to Advance Education for Transformative Action (https://teriin.org/news/mobius-foundations-icse- ...
- **Evidence retrieved**: Artificial Intelligence in Climate Resilience: Evaluating Contributions to SDG 13, AI for Restoring Degraded Lands: Mapping Degradation, Predicting Climate Risk and Valuing Ecosystem Services, TERI Highlights Workforce Imperatives for India's Clean Energy Ambitions at ICC Global Business Summit 2025, TERI Highlights Workforce Imperatives for India's Clean Energy Ambitions at ICC Global Business Summit 2025 | context blocks: 10 | gold docs retrieved: 2/7
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 7 verified sources
- **Root cause**: The most serious failure in the run. A person-lookup question returned a list of entirely unrelated items (an opinion piece on education, a Mobius Foundation conference, a UNCCD panel, the Darbari Seth Memorial Lecture, a PM Surya Ghar news item) and named NO researcher - even though blocks 1 and 2 were precisely the two AI papers whose recorded authors, Dr Jitendra Vir Sharma and Mr Sayanta Ghosh, are the answer. Correct evidence retrieved, wrong mechanism applied, no person named.

### 5. Q004 - What are TERI's flagship initiatives and centres of excellence?

- **Verdict**: `NO_ANSWER` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `HIGH` | **Class**: retrieval failure
- **Gold expected** (5 facts, 9 authoritative documents): The World Sustainable Development Summit (WSDS) has been TERI's flagship event since 2001 and is held annually. ...
- **Chatbot returned**: I don't have information on that in the available sources.
- **Evidence retrieved**: Mahindra-TERI Centre of Excellence launches Chennai Water Sustainability Assessment Report, Sustainable development and the role of TERI, Executive Summary, TERI and UTC set up Center of Excellence to Focus on Energy Efficient Buildings in India | context blocks: 5 | gold docs retrieved: 0/9
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 9 verified sources
- **Root cause**: Refuses with 'I don't have information on that in the available sources' while five retrieved blocks are all about TERI Centres of Excellence (Mahindra-TERI, DBT, UTC, Mahindra Lifespaces). The authoritative Centres of Excellence hub page (98ad60e0, which lists nine centres) and the WSDS/Act4Earth/Industry Charter pages were not retrieved. A refusal is the worst possible outcome here because partially useful evidence was in context.

### 6. Q082 - How can my company consult with TERI for carbon footprinting and ESG reporting?

- **Verdict**: `NO_ANSWER` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `HIGH` | **Class**: retrieval failure
- **Gold expected** (8 facts, 11 authoritative documents): TERI Council for Business Sustainability (TERI CBS) is the interface between TERI's research and the corporate world. ...
- **Chatbot returned**: I don't have information on that in the available sources.
- **Evidence retrieved**: Indian business leaders affirm proactive action for zero carbon emissions, TERI launches portal for businesses to self-assess and improve renewable energy consumption, Annual Reports, Experts share best practices and solutions to increase our Green Building Footprint | context blocks: 5 | gold docs retrieved: 0/11
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 11 verified sources
- **Root cause**: Refuses outright on a straightforward commercial-enquiry question. Five blocks were retrieved, including a businesses portal and a GHG standards item, but none of the eleven gold documents - TERI CBS, its member services, the GHG calculator service or the contact details - reached context. For a public-facing chatbot, failing to route a 'how do I engage you commercially' question is a high-impact miss.

### 7. Q093 - Does TERI offer soil testing and environmental analysis?

- **Verdict**: `NO_ANSWER` | **Layer**: `GENERATION` | **Severity**: `HIGH` | **Class**: generation failure
- **Gold expected** (4 facts, 7 authoritative documents): TERI, accredited by NABL, provides testing of soil, along with water and sludge. ...
- **Chatbot returned**: I don't have information on that in the available sources.
- **Evidence retrieved**: TERI develops innovative technology for end-to-end treatment of wastewater, Air Quality Research, TERI’s Solutions for Sustainable Development, TERI’s Solutions for Sustainable Development | context blocks: 5 | gold docs retrieved: 1/7
- **Existed in corpus?** yes - the gold entry is `GOLD_NEEDS_CORRECTION` with 7 verified sources
- **Root cause**: Refuses although five blocks were retrieved including the Air Quality Research service node (a gold document), and the corpus states plainly that TERI is NABL-accredited for testing water, soil and sludge. A documented yes/no question answered as unknown.

### 8. Q099 - Are certificates awarded upon successful completion of TERI programmes?

- **Verdict**: `NO_ANSWER` | **Layer**: `GENERATION` | **Severity**: `HIGH` | **Class**: generation failure
- **Gold expected** (3 facts, 5 authoritative documents): TERI awards a certificate at the end of an internship term, and the supervisor fills in an evaluation form provided by the intern's institution. ...
- **Chatbot returned**: I don't have information on that in the available sources.
- **Evidence retrieved**: First International E-Certificate Course on Mainstreaming Urban Climate Action Launched by Key Institutions, TERI in partnership with NDTV launches the 3-month ESG certification programme, TERI University and Coca-Cola Join Hands to set up Department of Regional Water Studies, TERI University confers Honorary Degrees on Eminent Luminaries | context blocks: 5 | gold docs retrieved: 1/5
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 5 verified sources
- **Root cause**: Refuses although the Internship page (a gold document) was retrieved and cited and states explicitly that TERI awards a certificate at the end of the term, and although block 1 is the first international e-Certificate Course. Straightforwardly answerable and answered as unknown.

### 9. Q083 - Does TERI provide Life Cycle Assessment (LCA) services?

- **Verdict**: `NO_ANSWER` | **Layer**: `GENERATION` | **Severity**: `HIGH` | **Class**: generation failure
- **Gold expected** (6 facts, 10 authoritative documents): TERI's Environmental Design & Technical Advisory service lists life cycle assessments among its expertise. ...
- **Chatbot returned**: I can help with questions grounded in specific documents or articles from the knowledge base. If you have any further inquiries or need information about TERI's services, feel free to ask!
- **Evidence retrieved**: Life cycle analysis of transport modes, TERI launches portal for businesses to self-assess and improve renewable energy consumption, TERI’s Solutions for Sustainable Development, Harnessing the Potential of Bio-Resources to Produce Low Carbon Bio-Hydrogen | context blocks: 0 | gold docs retrieved: 0/10
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 10 verified sources
- **Root cause**: Deflects with a meta-response about the knowledge base and emits zero citations and zero used chunks, even though block 1 retrieved was 'Life cycle analysis of transport modes' and the corpus contains an explicit LCA service line plus at least four TERI LCA studies. The answer to 'Does TERI provide LCA services?' is a documented yes.

### 10. Q109 - Can you recommend reports on climate change adaptation?

- **Verdict**: `INCORRECT` | **Layer**: `RANKING` | **Severity**: `HIGH` | **Class**: routing and retrieval
- **Gold expected** (5 facts, 9 authoritative documents): TERI published the policy brief 'A Transformative Global Goal on Adaptation: Scope, Science and Policy' (November 2024). ...
- **Chatbot returned**: Here is what I found: - Navigating Discussions on Decarbonisation and Business Actions at COP28 (https://teriin.org/report/navigating-discussions-decarbonisation-and-business-actions-cop28) - White paper on National Action Plan on Climate Change (NAPCC) (https://teriin.org/report/white-paper-nationa ...
- **Evidence retrieved**: Everything you wanted to know about climate change, Solutions to tackle climate change, Study of Studies 2022-Final Report, Study of Studies 2022-Final Report | context blocks: 2 | gold docs retrieved: 0/9
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 9 verified sources
- **Root cause**: Structured path returned only two reports, neither about adaptation: 'Navigating Discussions on Decarbonisation and Business Actions at COP28' and a white paper on the NAPCC. None of the five gold adaptation publications appears, and only two context blocks were used. A recommendation request answered with an off-topic two-item list.

### 11. Q035 - What innovations and technologies are being demonstrated under ongoing projects?

- **Verdict**: `INCORRECT` | **Layer**: `SCOPE_HANDLING` | **Severity**: `HIGH` | **Class**: routing and generation
- **Gold expected** (9 facts, 14 authoritative documents): TERI's In Vitro Mass Production Technology produces mycorrhizae-based biofertilizers, available as tablets, granules and powder. ...
- **Chatbot returned**: Here is what I found: - Compendium and Enforcement Framework for Energy Efficiency Regulations (https://teriin.org/project/compendium-and-enforcement-framework-energy-efficiency-regulations) - Agroecological Region (AER) Based Variations in Soil Carbon Sequestration Potential (C-SPOT) vis-à-vis carb ...
- **Evidence retrieved**: Zero-emission Truck and Bus Showcase, Demonstration of new agro-technologies at farmer's field, Strengthen National Climate Policy Implementation: Comparative Empirical Learning & Creating Linkage to Climate Finance (SNAPFI), Report | context blocks: 4 | gold docs retrieved: 0/14
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 14 verified sources
- **Root cause**: Returned the SAME generic ongoing-project list as Q025, opening with the identical four items, instead of answering what innovations and technologies are demonstrated. None of TERI's named technologies (mycorrhiza, biomass gasifier, cookstove, Oilzapper, TEAM, ceramic membranes, TADOX, MEOR/PDB) is mentioned, and the Technologies page was not retrieved. Two different questions producing a byte-identical list head is a template/routing defect.

### 12. Q015 - What kind of research does TERI conduct on sustainable agriculture?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `HIGH` | **Class**: retrieval failure
- **Gold expected** (8 facts, 12 authoritative documents): TERI's sustainable-agriculture work focuses on plant- and microbe-derived products that reduce chemical-fertiliser use while improving crop yields. ...
- **Chatbot returned**: TERI conducts research on the **impact of climate change and sustainability on the agriculture sector in India**, aiming to develop probable solutions to address these challenges [1]. Additionally, it highlights the effects of urbanization and industrialization on agriculture, such as the loss of fe ...
- **Evidence retrieved**: TERI to study impact of climate change on farm sector, Transforming Indian agriculture: Sustainable solutions for a greener future, Conference on Approaches to Shaping Climate Resilient Agriculture, Discussion Paper - Women in agriculture: Enhancing their role and promoting sustainability and livelihood support | context blocks: 5 | gold docs retrieved: 0/12
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 12 verified sources
- **Root cause**: None of the twelve gold documents was retrieved. The answer is generic ('TERI studies climate impacts on agriculture') and misses TERI's entire distinctive portfolio - mycorrhiza biofertiliser, micropropagation, nano-fertilisers, the TERI-CFCL Centre of Excellence and the SDG Blueprint - because the Technologies page, service nodes and CoE pages were never retrieved. Retrieval returned press releases / annual reports / brochures instead of the canonical page or service node the gold cites; the answer is grounded but not in the authoritative source.

### 13. Q002 - Can you provide a brief history of The Energy and Resources Institute (TERI)?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `TEMPORAL_INTERPRETATION` | **Severity**: `HIGH` | **Class**: retrieval and generation
- **Gold expected** (8 facts, 3 authoritative documents): TERI was established in 1974. ...
- **Chatbot returned**: The Energy and Resources Institute (TERI) was established in **1974** as the Tata Energy Research Institute, with **Shri JRD Tata** serving as its first Chairman [5]. Initially focused on energy research, TERI expanded its scope over the years to address broader issues related to **climate change**  ...
- **Evidence retrieved**: , Framework for mainstreaming eco-housing in Pune, Development of biodegradable soy flour composites for short-term applications, Wastewater treatment in membrane bioreactor using low-cost membranes | context blocks: 6 | gold docs retrieved: 1/3
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 3 verified sources
- **Root cause**: Correct on 1974, Tata Energy Research Institute, JRD Tata as first Chairman, Pachauri from 1981, and GRIHA. Two problems: (1) founder Darbari Seth, the IPCC chairmanship and the 2007 Nobel Peace Prize are all absent because the /history and Darbari Seth pages were never retrieved (only Mission and Goals plus one press release); (2) it states 'As of 2023, TERI is celebrating its 50th anniversary' in the present tense, which is stale at the 2026 reference date and is a dated press-release statement presented as current.

### 14. Q097 - Are there any upcoming TERI training programmes?

- **Verdict**: `NO_ANSWER` | **Layer**: `TEMPORAL_INTERPRETATION` | **Severity**: `MEDIUM` | **Class**: retrieval and generation
- **Gold expected** (5 facts, 4 authoritative documents): Only three TERI events in the corpus have a start date on or after 19 August 2026. ...
- **Chatbot returned**: I don't have information on that in the available sources.
- **Evidence retrieved**: TERI-DST training programme on 'Development & Research for Sustainable Urbanization & Habitat', Three-Days Training Programme on "Grid-connected Rooftop Solar PV Systems" for Channel Partners, New Entrepreneurs, Project Developers & Manufacturers, TERI-DST training programme on 'Promoting Sustainability Through Science', Training Program on Energy, Environment and Sustainable Development | context blocks: 6 | gold docs retrieved: 0/4
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 4 verified sources
- **Root cause**: Refuses, when the documented answer is a negative with evidence: no upcoming training programme is listed, and the only three future-dated events are a memorial lecture, a UNCCD COP17 panel and a WCEF session. Retrieval returned six PAST training programmes (TERI-DST, TERI-ITEC 2013-15) with no date filtering, so the system has no way to distinguish upcoming from historic.

### 15. Q003 - What are TERI's core research areas and divisions?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `GENERATION` | **Severity**: `MEDIUM` | **Class**: generation failure
- **Gold expected** (5 facts, 2 authoritative documents): TERI's thematic areas are Sustainable Agriculture, Climate Change, Energy, Environment, Sustainable Habitat, Health & Nutrition, and Resources and Sustainable Development. ...
- **Chatbot returned**: TERI's core research areas encompass **energy, environment, climate change, and sustainable development**. The organization focuses on various fields including clean energy, sustainable agriculture, water security, land resource management, air pollution, and low-emission transport systems [1]. Addi ...
- **Evidence retrieved**: Mission and Goals, Sustainable development and the role of TERI, Brochures, Annual Reports | context blocks: 5 | gold docs retrieved: 1/2
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 2 verified sources
- **Root cause**: Names divisions that do exist in the corpus (Sustainable Agriculture, Sustainable Habitat, Land Resources, TERI-Deakin Nano Biotechnology Centre) but does not give the seven thematic areas even though the Thematic Areas content was retrieved; substitutes the four-word institutional description ('energy, environment, climate change, sustainable development') for the seven research areas the question asks for.

### 16. Q025 - What are TERI's ongoing projects?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `GENERATION` | **Severity**: `MEDIUM` | **Class**: generation + gold limit
- **Gold expected** (4 facts, 0 authoritative documents): The CMS records 594 ongoing project nodes as of the snapshot. ...
- **Chatbot returned**: Here is what I found: - Compendium and Enforcement Framework for Energy Efficiency Regulations (https://teriin.org/project/compendium-and-enforcement-framework-energy-efficiency-regulations) - Agroecological Region (AER) Based Variations in Soil Carbon Sequestration Potential (C-SPOT) vis-à-vis carb ...
- **Evidence retrieved**: Sustainable development and the role of TERI, Eco design sustainable buildings for a new India, Executive Summary, Project Report | context blocks: 5 | gold docs retrieved: 0/0
- **Existed in corpus?** yes - the gold entry is `GOLD_NEEDS_CORRECTION` with 0 verified sources
- **Root cause**: Routed to the structured path and returned a real list of current ongoing projects with working URLs, which is a reasonable shape for the question. It gives no count and no scope statement, whereas the gold's graded content is the 594 total and the theme/programme distribution. A user cannot tell from the answer whether ten or six hundred projects exist.

### 17. Q042 - How is TERI supporting India's energy transition?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `MEDIUM` | **Class**: retrieval failure
- **Gold expected** (7 facts, 11 authoritative documents): TERI operates a TERI Institute of Energy Transition based at Gachibowli, Hyderabad. ...
- **Chatbot returned**: TERI supports India's energy transition through its **Energy Programme**, which focuses on ensuring adequate, reliable, affordable, and sustainable supplies of clean and renewable energy. This includes developing and promoting energy-efficient technological solutions for end-users and forming partne ...
- **Evidence retrieved**: Energy Programme, India's remarkable journey towards energy transition, TERI Highlights Workforce Imperatives for India's Clean Energy Ambitions at ICC Global Business Summit 2025, Strategic Document Vision: 2025–30 | context blocks: 5 | gold docs retrieved: 0/11
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 11 verified sources
- **Root cause**: Zero gold documents retrieved and zero gold facts covered, yet the answer is grounded and substantive (Energy Programme, 'India's Electricity Transition: Pathways to 2050', USD 1.2-1.6 trillion investment need). It misses every institutional anchor the gold names - the TERI Institute of Energy Transition, CoEET, ETHENS and the state utility MoUs. Retrieval returned press releases / annual reports / brochures instead of the canonical page or service node the gold cites; the answer is grounded but not in the authoritative source.

### 18. Q085 - What sustainability advisory services does TERI offer?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `MEDIUM` | **Class**: retrieval failure
- **Gold expected** (3 facts, 31 authoritative documents): TERI's website publishes 30 service nodes covering policy advisory, audits and PMU support, climate and environment assessment, environmental design consultancy, ratings and certification, laboratory testing, natural-resource and  ...
- **Chatbot returned**: TERI offers a range of **sustainability advisory services** aimed at various stakeholders. These include **strategy development and implementation** for corporates, **policy advisory**, and **capacity building** initiatives. The organization provides platforms for engagement with policymakers, acade ...
- **Evidence retrieved**: Sustainable development and the role of TERI, Eco design sustainable buildings for a new India, TERI’s Solutions for Sustainable Development, Harnessing the Potential of Bio-Resources to Produce Low Carbon Bio-Hydrogen | context blocks: 5 | gold docs retrieved: 0/31
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 31 verified sources
- **Root cause**: None of the thirty-one service nodes was retrieved. The answer describes advisory services at the right level of generality and is grounded, but it cannot enumerate the actual catalogue, so a user learns that TERI advises without learning what it offers. The clearest instance of the run's dominant pattern: canonical service nodes are invisible to retrieval.

### 19. Q113 - How can researchers obtain project reports and technical documents?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `MEDIUM` | **Class**: retrieval failure
- **Gold expected** (6 facts, 7 authoritative documents): TERI Library membership is open to researchers, NGO staff, government officials, corporate employees, students, teachers, consultants and policy-makers in energy, environment and sustainable development. ...
- **Chatbot returned**: Researchers can obtain project reports and technical documents through the **NSTMIS-sponsored Digital Repository** developed by TERI. This web-based platform stores and provides access to NSTMIS publications, reports, and datasets, featuring advanced search and retrieval capabilities. Users can sear ...
- **Evidence retrieved**: Study of Studies, NSTMIS-DST DIGITAL REPOSITORY, Study of Studies 2022-Final Report, Annual Reports | context blocks: 4 | gold docs retrieved: 0/7
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 7 verified sources
- **Root cause**: Answers with a real but narrow artefact - the NSTMIS-DST digital repository - and then drifts into an irrelevant COVID-19 anecdote from a 'Study of Studies' project. The documented route (TERI Library membership, document delivery, inter-library loan, library.teri.res.in) is absent because no gold document was retrieved.

### 20. Q121 - How can organizations partner with TERI for research, innovation, policy advisory, or implementation projects?

- **Verdict**: `PARTIALLY_CORRECT` | **Layer**: `QDRANT_RETRIEVAL` | **Severity**: `MEDIUM` | **Class**: retrieval failure
- **Gold expected** (6 facts, 12 authoritative documents): TERI Council for Business Sustainability (TERI CBS) is the interface for TERI's research to connect to the corporate world, and is governed by an Executive Committee of CEOs from member companies. ...
- **Chatbot returned**: Organizations can partner with TERI through various collaborative efforts aimed at enhancing technological capabilities, sharing knowledge, and fostering innovation. TERI actively seeks partnerships with local, international, and bilateral institutions to promote sustainable interventions. These par ...
- **Evidence retrieved**: TERI experts recommend provisions for Green Fund, and river policies at State and Central levels in Union Budget 2023-24, Need to assess the potential of nature-based solutions and green technologies to facilitate green recovery: Shri Bhupender Yadav, Union Minister for Environment, Forest and Climate Change, Annual Reports, Experts share best practices and solutions to increase our Green Building Footprint | context blocks: 5 | gold docs retrieved: 0/12
- **Existed in corpus?** yes - the gold entry is `GOLD_CONFIRMED` with 12 verified sources
- **Root cause**: Generic partnership language - funding support, project agreements, collaborative research - that is grounded but tells an organisation nothing actionable. None of the twelve gold documents was retrieved, so TERI CBS and its membership model, the co-created Centres of Excellence, the Areas of Work framing and the contact details are all missing.

## I. Systemic patterns

1. **Canonical pages are effectively invisible to retrieval.** The 30 `services` nodes, the thematic/hub pages and the Contact/Internship/Annual-Reports pages are short, authoritative and exactly what these questions need - yet Q085 (31 gold service nodes) retrieved none, and Q015, Q023, Q042, Q058, Q062, Q067, Q085, Q096, Q121 all retrieved zero gold documents. Long PDF attachments and press releases dominate instead. This is the single highest-leverage finding.
2. **Refusal with evidence in hand (8 questions).** Q004, Q079, Q082, Q083, Q091, Q093, Q097, Q099 all say some variant of "I don't have information on that" while relevant - sometimes exactly correct - blocks sit in context. Q091 is the starkest: the Air Quality Research service node, which states the NABL-accredited monitoring capability, was retrieved as block 1 and the answer still declined. Q093 and Q099 are documented yes/no questions answered as unknown.
3. **The structured/list path is unreliable outside dates.** It is excellent for a date-ordered query (Q110: ten most recent policy briefs, all ten citations gold-aligned) and produces off-topic lists everywhere else - Q112 returned a children's science-congress workshop for "publications on SDGs"; Q119 returned a memorial lecture and a solar news item for "which researchers work on AI" while the two correct AI papers sat in blocks 1-2; Q109 returned two non-adaptation reports. Q025 and Q035 returned a byte-identical list head for two different questions.
4. **Person lookups do not resolve to people.** Q119 named no researcher at all despite both source papers being retrieved and their authors being recorded in `documents_author`. The entity layer that would answer this exists in MySQL and is not on the answer path.
5. **The graph is inert (0/86).** Three timeouts against a 3-second budget opened the circuit breaker; combined with a template that selects a `Claim.object_literal` property that does not exist in the projection, the knowledge layer contributed nothing to any answer.
6. **Answers omit content from documents they themselves cite.** Q001 cites the Mission and Goals page and skips its twelve goals and six values; Q014 cites /policy and skips most of its named contributions; Q055 has the business-climate page as block 1 and never mentions TERI CBS. This is a context-utilisation and prompt-shape problem, not a retrieval one.
7. **Scope drift to national policy.** Q071 answered with India's National Afforestation Programme, Green India Mission and CAMPA instead of TERI's own restoration work; Q088 answered at national-policy level instead of describing TERI's services to an organisation.
8. **A structural marker leaks into the answer text.** Answers begin with a literal `<website_answer>` tag and contain a `**From our documents**` divider. Harmless if the UI strips it, but it is present in the API payload.
9. **Benchmark-side factor, stated for fairness.** Several gold entries span far more sources (10-31) than a 5-block context can carry, so 100% fact coverage was unattainable for them. These are marked `C` / `G+C`. The gold set is not wrong - it was built to describe what the corpus authoritatively supports - but per-question fact-coverage percentages should not be read as a pure system score.

## J. Questions answered correctly

| ID | Question | Why it worked |
| --- | --- | --- |
| Q016 | Does TERI publish data or studies related to greenhouse gas (GHG) inventories? | Correctly answers yes and identifies the Catalogue of Indian Emission Inventory Reports with EDF, with both gold press releases retrieved and cited. Adds grounded detail on state and city GHG inventory work. Does not mention the India GHG Program, but the question is answerable as asked and nothing  |
| Q024 | How is TERI supporting the implementation of Sustainable Development Goals (SDGs)? | Identifies the SDG and Policy Coordination (SPC) initiative correctly from the authoritative SDG page, which was retrieved and cited, and adds the grounded SDSN South Asia regional-hub role. Four of six gold facts covered with no material error. |
| Q080 | What green building rating services does TERI provide, | The Ratings & Certification service node was retrieved and cited, and six of seven gold facts are covered: GRIHA assistance, life-cycle environmental evaluation, qualitative and quantitative criteria, and LEED/GRIHA facilitation plus energy audits and capacity building. It says TERI administers GRIH |
| Q084 | Can TERI assist in conducting an energy audit for my industrial facility? | Answers yes and supports it with the Industrial Energy Efficiency Division, plant-level audits, sector coverage and the grounded figure of over 2000 industrial energy audits (verified in the corpus). Uses a different but real evidence base from the gold's ~200-building service copy; nothing stated i |
| Q086 | What benefits can organizations gain from TERI's environmental design consultancy? | The environmental-design service node was retrieved and cited, and the answer correctly lists the benefits the gold identifies: energy efficiency, full building performance analysis, renewable integration, water and waste strategies and indoor air quality. Does not name the simulation-tool list, whi |
| Q090 | What services does TERI's NABL-accredited laboratory provide? | Describes a genuinely NABL-accredited TERI laboratory - the Food Testing Laboratory, verified in the corpus - with over 70 parameters and its accredited and non-accredited scopes. It is a different accredited facility from the ones the gold enumerates, which the gold itself warns about ('at least fo |
| Q092 | What water quality testing services are available? | Correct and useful: the potable-water testing kit with eleven named parameters and the NABL-accredited packaged-drinking-water and mineral-water testing, plus chemical, microbiological and trace-element analysis. Grounded throughout; covers the substance of the gold's water-testing facts through a d |
| Q095 | What analytical capabilities are available through TERI's testing laboratories? | The best of the laboratory answers: Food Testing Laboratory scope with over 70 parameters under ISO/IEC 17025:2017, plus the Environmental and Industrial Biotechnology laboratory NABL-accredited for 32 water-quality and petroleum-hydrocarbon parameters - which is the gold's EIB Laboratory fact, inde |
| Q110 | What policy briefs has TERI recently published? | The standout success. The structured path returned the ten most recent policy briefs in correct reverse-chronological order with working URLs, and all ten citations resolve to gold documents - the only question in the run with complete citation-to-gold alignment. Five of seven gold facts covered; on |

The common thread: every one of these either (a) hit a single short authoritative node that retrieval happened to surface (Q080, Q086, Q016, Q024), (b) asked a yes/no question answerable from any competent source (Q084, Q090, Q092, Q095), or (c) used the date-ordered structured path (Q110). None required synthesising across many documents.

## K. Questions needing follow-up (highest value first)

These are recorded for the next phase. **No fix was applied in this run.**

| Priority | Question(s) | What to investigate |
| --- | --- | --- |
| 1 | Q085, Q015, Q023, Q042, Q058, Q062, Q067, Q096, Q121 | Why short canonical `services` / hub pages lose to long PDF attachments in ranking. 9 questions retrieved zero gold documents. |
| 2 | Q091, Q093, Q099, Q083, Q004, Q082 | Refusal behaviour when relevant blocks are present. Q091 and Q093 had the exact gold service node in context. |
| 3 | Q112, Q119, Q109, Q035, Q025 | The structured/list path: off-topic lists, an identical list head for two different questions, and no person resolution. |
| 4 | Q001, Q014, Q055, Q007 | Context utilisation: content omitted from documents the answer itself cites. |
| 5 | Q002, Q097, Q059 | Recency and currency: stale statements in present tense, and no `field_event_start_date` filtering for 'upcoming'. |
| 6 | all | Graph route: 3s budget timeouts, circuit-breaker behaviour, and the missing `Claim.object_literal` property in the Neo4j projection. |
| 7 | Q071, Q088 | Scope anchoring to TERI rather than to India or generic practice. |

## Appendix - full results table

| ID | Type | Verdict | Layer | Sev | Class | Facts | Gold docs retr. | Cites (gold) | Blocks | Intent | ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q001 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 2/4 | 1/1 | 4 (1) | 5 | qa | 10413 |
| Q002 | historical/narrative | PARTIALLY_CORRECT | TEMPORAL_INTERPRETATION | HIGH | R+G | 4/8 | 1/3 | 2 (1) | 6 | qa | 10490 |
| Q003 | aggregation/list | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/5 | 1/2 | 5 (1) | 5 | qa | 9209 |
| Q004 | aggregation/list | NO_ANSWER | QDRANT_RETRIEVAL | HIGH | R | 0/5 | 0/9 | 5 (0) | 5 | qa | 6645 |
| Q005 | location/city + fact | PARTIALLY_CORRECT | CONTEXT_BUILDING | MEDIUM | R | 9/11 | 1/2 | 5 (1) | 5 | qa | 14802 |
| Q007 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 3/9 | 1/5 | 5 (1) | 5 | qa | 10340 |
| Q009 | factual | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 3/6 | 1/3 | 2 (1) | 5 | qa | 8630 |
| Q010 | factual | PARTIALLY_CORRECT | CONTEXT_BUILDING | MEDIUM | R+G | 0/4 | 1/7 | 2 (0) | 5 | qa | 8763 |
| Q011 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/5 | 0/3 | 2 (0) | 5 | qa | 8793 |
| Q012 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 3/6 | 2/7 | 5 (2) | 5 | qa | 9979 |
| Q014 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 1/10 | 1/6 | 4 (1) | 5 | qa | 8358 |
| Q015 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | HIGH | R | 0/8 | 0/12 | 3 (0) | 5 | qa | 9489 |
| Q016 | factual + aggregatio | CORRECT | - | - | - | 3/5 | 2/10 | 4 (2) | 5 | qa | 9497 |
| Q018 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/6 | 1/8 | 2 (1) | 5 | qa | 9410 |
| Q019 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 2/7 | 1/9 | 4 (1) | 5 | qa | 9637 |
| Q020 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 1/9 | 1/9 | 4 (1) | 5 | qa | 10286 |
| Q021 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 1/7 | 1/8 | 3 (1) | 5 | qa | 9021 |
| Q023 | aggregation/list | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 3/10 | 0/12 | 2 (0) | 5 | qa | 8783 |
| Q024 | narrative/summary | CORRECT | - | - | - | 4/6 | 1/6 | 4 (1) | 5 | qa | 8591 |
| Q025 | aggregation/count | PARTIALLY_CORRECT | GENERATION | MEDIUM | G+C | 0/4 | 0/0 | 5 (0) | 5 | structured | 6797 |
| Q027 | aggregation/count | PARTIALLY_CORRECT | GRAPH_DATA | MEDIUM | G+C | 1/3 | 0/2 | 3 (0) | 5 | structured | 10675 |
| Q029 | aggregation/list | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/6 | 1/8 | 3 (1) | 5 | qa | 9843 |
| Q035 | aggregation/list | INCORRECT | SCOPE_HANDLING | HIGH | Q+G | 1/9 | 0/14 | 3 (0) | 4 | qa | 9097 |
| Q040 | factual + narrative | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/7 | 0/8 | 4 (0) | 5 | qa | 9418 |
| Q041 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 1/7 | 1/8 | 4 (0) | 5 | qa | 9272 |
| Q042 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/7 | 0/11 | 4 (0) | 5 | qa | 9164 |
| Q043 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 3/8 | 0/17 | 3 (0) | 5 | qa | 10764 |
| Q044 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/9 | 0/16 | 4 (0) | 5 | qa | 10088 |
| Q045 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/6 | 0/8 | 3 (0) | 5 | qa | 10269 |
| Q046 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 1/6 | 0/11 | 3 (0) | 5 | qa | 14371 |
| Q048 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/6 | 0/7 | 4 (0) | 5 | qa | 9969 |
| Q049 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/6 | 0/11 | 3 (0) | 5 | qa | 10911 |
| Q050 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 2/5 | 0/10 | 4 (0) | 5 | qa | 9041 |
| Q051 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 1/7 | 2/10 | 5 (2) | 5 | qa | 9406 |
| Q052 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/7 | 0/10 | 5 (0) | 5 | qa | 8460 |
| Q053 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 1/7 | 0/8 | 4 (0) | 5 | qa | 8917 |
| Q055 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 1/6 | 0/6 | 4 (0) | 5 | qa | 9976 |
| Q056 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 2/7 | 1/11 | 4 (1) | 5 | qa | 10056 |
| Q057 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/7 | 1/11 | 4 (1) | 5 | qa | 8609 |
| Q058 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/7 | 0/10 | 4 (0) | 5 | qa | 10218 |
| Q059 | aggregation/list | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/6 | 0/9 | 4 (0) | 5 | structured | 11306 |
| Q060 | aggregation/list | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/8 | 0/12 | 2 (0) | 5 | qa | 8308 |
| Q061 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/7 | 1/11 | 4 (1) | 5 | qa | 10097 |
| Q062 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/8 | 0/14 | 2 (0) | 5 | qa | 10583 |
| Q063 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 2/7 | 0/13 | 5 (0) | 5 | qa | 13180 |
| Q064 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 1/8 | 0/13 | 4 (0) | 5 | qa | 10349 |
| Q065 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 2/7 | 0/12 | 4 (0) | 5 | qa | 9390 |
| Q066 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/8 | 1/13 | 3 (0) | 5 | qa | 9044 |
| Q067 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/7 | 0/14 | 2 (0) | 5 | qa | 9550 |
| Q068 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/6 | 1/12 | 2 (1) | 5 | qa | 9341 |
| Q069 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 2/7 | 0/14 | 3 (0) | 5 | qa | 9061 |
| Q070 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/6 | 1/10 | 3 (0) | 5 | qa | 8427 |
| Q071 | aggregation/list | PARTIALLY_CORRECT | SCOPE_HANDLING | MEDIUM | Q+G | 0/7 | 0/13 | 2 (0) | 5 | qa | 11505 |
| Q073 | aggregation/list | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/7 | 0/12 | 1 (0) | 5 | qa | 10846 |
| Q074 | narrative/summary | PARTIALLY_CORRECT | GENERATION | LOW | G | 1/7 | 2/13 | 4 (2) | 5 | qa | 9979 |
| Q075 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 1/7 | 0/9 | 3 (0) | 5 | qa | 10601 |
| Q076 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/8 | 0/15 | 3 (0) | 5 | qa | 10382 |
| Q077 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 1/7 | 0/14 | 2 (0) | 5 | qa | 10167 |
| Q079 | aggregation/list | NO_ANSWER | QUERY_UNDERSTANDING | CRITICAL | Q | 0/8 | 1/13 | 0 (0) | 0 | chitchat | 6812 |
| Q080 | factual | CORRECT | - | - | - | 6/7 | 1/6 | 3 (1) | 5 | qa | 8913 |
| Q082 | factual / procedural | NO_ANSWER | QDRANT_RETRIEVAL | HIGH | R | 0/8 | 0/11 | 5 (0) | 5 | qa | 6906 |
| Q083 | factual | NO_ANSWER | GENERATION | HIGH | G | 1/6 | 0/10 | 0 (0) | 0 | qa | 7185 |
| Q084 | factual | CORRECT | - | - | - | 1/7 | 1/6 | 4 (1) | 5 | qa | 9490 |
| Q085 | aggregation/list | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/3 | 0/31 | 3 (0) | 5 | qa | 7987 |
| Q086 | narrative/summary | CORRECT | - | - | - | 2/5 | 1/4 | 2 (1) | 5 | qa | 9766 |
| Q088 | narrative/summary | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/6 | 0/10 | 3 (0) | 5 | qa | 9864 |
| Q089 | aggregation/list | PARTIALLY_CORRECT | GENERATION | LOW | G | 3/7 | 0/13 | 2 (0) | 5 | qa | 8201 |
| Q090 | factual | CORRECT | - | - | - | 4/5 | 0/6 | 3 (0) | 5 | qa | 8410 |
| Q091 | factual | NO_ANSWER | GENERATION | CRITICAL | G | 0/5 | 1/4 | 0 (0) | 0 | qa | 6683 |
| Q092 | factual | CORRECT | - | - | - | 3/5 | 0/7 | 4 (0) | 5 | qa | 8699 |
| Q093 | factual | NO_ANSWER | GENERATION | HIGH | G | 0/4 | 1/7 | 5 (1) | 5 | qa | 6723 |
| Q095 | aggregation/list | CORRECT | - | - | - | 4/5 | 0/7 | 3 (0) | 5 | qa | 10749 |
| Q096 | narrative/summary | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 1/7 | 0/10 | 5 (0) | 5 | qa | 9449 |
| Q097 | current-state / coun | NO_ANSWER | TEMPORAL_INTERPRETATION | MEDIUM | R+G | 0/5 | 0/4 | 6 (0) | 6 | qa | 6703 |
| Q098 | factual / aggregatio | PARTIALLY_CORRECT | GENERATION | MEDIUM | G | 0/6 | 1/9 | 2 (0) | 5 | qa | 8511 |
| Q099 | factual | NO_ANSWER | GENERATION | HIGH | G | 0/3 | 1/5 | 5 (1) | 5 | qa | 6546 |
| Q100 | factual / aggregatio | PARTIALLY_CORRECT | GENERATION | LOW | G | 0/8 | 0/13 | 4 (0) | 5 | qa | 8238 |
| Q102 | aggregation/list | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 1/7 | 0/12 | 3 (0) | 5 | qa | 8597 |
| Q107 | factual / procedural | PARTIALLY_CORRECT | GENERATION | LOW | G | 1/5 | 1/6 | 2 (1) | 5 | qa | 8336 |
| Q109 | aggregation/list | INCORRECT | RANKING | HIGH | Q+R | 0/5 | 0/9 | 2 (0) | 2 | structured | 4035 |
| Q110 | aggregation/list + t | CORRECT | - | - | - | 5/7 | 0/12 | 10 (10) | 10 | structured | 3998 |
| Q111 | factual | PARTIALLY_CORRECT | CITATION | MEDIUM | R+G | 2/4 | 0/2 | 3 (0) | 5 | qa | 7978 |
| Q112 | aggregation/list | INCORRECT | RANKING | CRITICAL | Q+R | 0/8 | 1/14 | 10 (0) | 10 | structured | 4358 |
| Q113 | factual / procedural | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/6 | 0/7 | 2 (0) | 4 | qa | 8167 |
| Q119 | person lookup | INCORRECT | RANKING | CRITICAL | Q+R | 0/5 | 2/7 | 10 (0) | 10 | structured | 5256 |
| Q121 | factual / procedural | PARTIALLY_CORRECT | QDRANT_RETRIEVAL | MEDIUM | R | 0/6 | 0/12 | 3 (0) | 5 | qa | 8562 |

## Final quality check

- all 86 eligible questions evaluated exactly once; no duplicates
- no excluded question was run: Q072 (GOLD_AMBIGUOUS), the 33 NEEDS_HUMAN_REVIEW entries and Q106 (NO_SUPPORTED_ANSWER) were all held out
- the real production /chat endpoint was used for every answer; no stub, no direct function calls for grading
- no chatbot output was used to alter the gold set - the gold files are byte-identical to the pre-run state
- no application file, prompt, or configuration value was modified
- no database state modified: MySQL documents/assertions/entities, Neo4j nodes/relationships and the Qdrant `documents` collection were counted before and after and are unchanged; `semantic_cache_enabled=False` meant the run wrote no cache points either
- no re-ingestion, no knowledge-graph rebuild, no data clearing
- no bug was fixed during the benchmark; all defects are recorded only

**Result: 0 QC problems.**

