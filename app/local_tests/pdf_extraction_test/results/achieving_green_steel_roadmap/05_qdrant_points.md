# Qdrant points — Achieving_Green_Steel_Roadmap.pdf

- points (rows upserted): **100**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `40949763-d9a2-5766-bff5-8e78dca2c44f`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "40949763-d9a2-5766-bff5-8e78dca2c44f",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
  "chunk_text": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY\n\nACHIEVING GREEN STEEL — Roadmap To A Net Zero — Steel Sector In India\n\nteri\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\n\n©2022 The Energy and Resources Institute\nAuthors\nWill Hall, Visiting Fellow, TERI (till June 2022)\nSachin Kumar, Senior Fellow, TERI (till Dec 2021)\nSneha Kashyap, Research Associate, TERI (till Mar 2022)\nShruti Dayal, Research Associate, TERI\nReviewer\nMr Girish Sethi, Senior Director, TERI\nDisclaimer\nThis report is an output of a research exercise undertaken by TERI supported by CIFF.\n\n… [+2878 more chars]",
  "content_hash": "4897d8a83ab2420f4a90a43213a9b5995e5cd23cc77dd257b1e175600f70a833",
  "token_count": 835,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    1,
    5
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `7588344d-0b1b-5f91-a8ba-5adc03800e51`

- vector: dim=3072 · [0.0270, -0.0184, -0.0139, -0.0162, -0.0279, 0.0010, -0.0017, 0.0189, …]

```json
{
  "chunk_id": "7588344d-0b1b-5f91-a8ba-5adc03800e51",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
  "chunk_text": "ACHIEVING GREEN STEEL — Roadmap To A Net Zero — Steel Sector In India\n\nteri\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\n\n©2022 The Energy and Resources Institute\nAuthors\nWill Hall, Visiting Fellow, TERI (till June 2022)\nSachin Kumar, Senior Fellow, TERI (till Dec 2021)\nSneha Kashyap, Research Associate, TERI (till Mar 2022)\nShruti Dayal, Research Associate, TERI\nReviewer\nMr Girish Sethi, Senior Director, TERI\nDisclaimer\nThis report is an output of a research exercise undertaken by TERI supported by CIFF. It does not represent \nthe views of the supp\n\n… [+448 more chars]",
  "content_hash": "c96445527f0afafd4f555c80e27be195f494011a0edca11835fcc18808f007df",
  "token_count": 265,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "40949763-d9a2-5766-bff5-8e78dca2c44f",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    2
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `358a363e-e752-5149-a03a-98a2055c2ade`

- vector: dim=3072 · [0.0156, -0.0079, -0.0134, -0.0237, -0.0186, -0.0097, -0.0187, 0.0171, …]

```json
{
  "chunk_id": "358a363e-e752-5149-a03a-98a2055c2ade",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
  "chunk_text": "omission in the publication.\nSuggested Citation\nWill Hall, Sachin Kumar, Sneha Kashyap, Shruti Dayal. 2022. Achieving Green Steel: Roadmap to a net zero \nsteel sector in India. New Delhi: The Energy and Resources Institute (TERI) Energy Transitions Commission (ETC) India is a research platform based in The Energy and \nResources Institute (TERI) in Delhi. ETC India is the Indian chapter of the global Energy \nTransitions Commission, which is chaired by Lord Adair Turner.\nIn 2018, ETC launched its ‘Mission Possible’ report, which detailed decarbonization \npathways for the ‘hard-to-abate’ sectors.\n\n… [+518 more chars]",
  "content_hash": "6e9bebcb0f020e2727b655517d6c409535032d2d9ecb5a060fcf1bcc01a06a80",
  "token_count": 272,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "40949763-d9a2-5766-bff5-8e78dca2c44f",
  "chunk_index": 1,
  "page_number": 3,
  "page_range": [
    3,
    3
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `5f049072-f979-58e9-a2ab-b832a7900270`

- vector: dim=3072 · [0.0210, 0.0133, -0.0152, -0.0387, -0.0205, -0.0151, -0.0154, 0.0146, …]

```json
{
  "chunk_id": "5f049072-f979-58e9-a2ab-b832a7900270",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
  "chunk_text": "work on industry \ntransformation, particularly in the ‘harder-to-abate’ sectors including iron & steel, cement, \nand other industry sub-sectors. \nLearn more at: https://www.teriin.org/energy-transitions\nENERGY TRANSITIONS \nCOMMISSION INDIA We would like to extend our sincere thanks to the Children’s Investment Fund Foundation. \nThis work would not have been possible without their financial support. Their contribution \nwas vital in continuing the conversation on a low carbon transition for the Indian iron and \nsteel sector.  \nWe would also like to acknowledge the support of ETC, which has alrea\n\n… [+1133 more chars]",
  "content_hash": "0702f3c84a01304c6b0b1a063a2125596b8729dd98ba57d279a27ece69c76069",
  "token_count": 405,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "40949763-d9a2-5766-bff5-8e78dca2c44f",
  "chunk_index": 2,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `a873ae25-59c5-5b0a-87bd-bd0d69c7716b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "a873ae25-59c5-5b0a-87bd-bd0d69c7716b",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": "FOREWORD\n\nThe Indian steel sector has been, and will remain an important pillar of India's economic growth and\ndevelopment. Steel demand is estimated to increase more than by twofold 2030-31, spurred by increased\nspending on infrastructure, automobiles and affordable housing. This increase in demand will provide\nboth challenges and opportunities, including the impact of the sector on the environment. There is a need\nto ensure that future pathways for growing steel demand are green with minimal environmental impacts.\n\nThe Energy and Resources Institute (TERI), as part of the Energy Transitions \n\n… [+6803 more chars]",
  "content_hash": "3df7ed739a1540fd0500f81c2325b1a7adabaeab6052bf845f7dfa1d73338dff",
  "token_count": 996,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    7,
    9
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `58684db4-2513-5f62-85ad-68415c46e32d`

- vector: dim=3072 · [0.0115, -0.0378, -0.0107, -0.0081, -0.0257, -0.0244, 0.0054, -0.0071, …]

```json
{
  "chunk_id": "58684db4-2513-5f62-85ad-68415c46e32d",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": "The Indian steel sector has been, and will remain an important pillar of India's economic growth and\ndevelopment. Steel demand is estimated to increase more than by twofold 2030-31, spurred by increased\nspending on infrastructure, automobiles and affordable housing. This increase in demand will provide\nboth challenges and opportunities, including the impact of the sector on the environment. There is a need\nto ensure that future pathways for growing steel demand are green with minimal environmental impacts.\n\nThe Energy and Resources Institute (TERI), as part of the Energy Transitions Commission\n\n… [+1300 more chars]",
  "content_hash": "84c722d06fe127052256df3c551d8aa10b57be1861c3f8c4eb86929e159c54e7",
  "token_count": 352,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a873ae25-59c5-5b0a-87bd-bd0d69c7716b",
  "chunk_index": 3,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `59f1eb07-3835-5a15-8ec9-0ebe172400e9`

- vector: dim=3072 · [0.0333, -0.0237, -0.0102, -0.0065, -0.0294, -0.0282, 0.0030, 0.0323, …]

```json
{
  "chunk_id": "59f1eb07-3835-5a15-8ec9-0ebe172400e9",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": ": Roadmap to a Net Zero\nSteel Sector in India builds on this work. In the formulation of this Roadmap, TERI has carried out extensive\nconsultations with various stakeholders in the steel sector - producers, buyers, technology providers,\nfinanciers, government bodies and the research community. This comprehensive Roadmap provides an overview of the current state of the steel sector and details a\nrange of possible emissions mitigation strategies. In the near term, implementation of strategies such\nas maximizing energy efficiency, increasing utilization of scrap, introducing green product standar\n\n… [+3628 more chars]",
  "content_hash": "6383fa467e993bf1fe04c14c703ebdc7d1e96f2e861f7892d36351200964757f",
  "token_count": 521,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a873ae25-59c5-5b0a-87bd-bd0d69c7716b",
  "chunk_index": 4,
  "page_number": 7,
  "page_range": [
    7,
    9
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `b17edf1f-3af1-5e56-811f-b2fdd1142fdf`

- vector: dim=3072 · [0.0370, -0.0249, -0.0053, 0.0016, -0.0449, -0.0033, -0.0083, 0.0471, …]

```json
{
  "chunk_id": "b17edf1f-3af1-5e56-811f-b2fdd1142fdf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": "itiveness................................................................................................................. 20\n\n3.2\t Rapid growth required in the near term.................................................................................21\n\n3.3\t Technology availability ....................................................................................................... 22\n\n3.4\t Capital requirements.......................................................................................................... 24\n4. Transition pathway....................................................\n\n… [+1627 more chars]",
  "content_hash": "edfba759dcad4c435be85f25993038e27304c399f4217a3dad31f18b68d07efd",
  "token_count": 240,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a873ae25-59c5-5b0a-87bd-bd0d69c7716b",
  "chunk_index": 5,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `71ad9fc6-9201-5cd2-a276-b4c2effc7645`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "71ad9fc6-9201-5cd2-a276-b4c2effc7645",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff..........................................................................................41",
  "chunk_text": "5.9\t Implement a carbon border tariff..........................................................................................41\n\n5.10 \tRetire older, polluting facilities............................................................................................ 42\nConclusions\t\n............................................................................................................................... 44\nBibliography\t\n................................................................................................................................45\nTABLE OF CONTENTS\n\nFigure 1: Route-wise crud\n\n… [+3493 more chars]",
  "content_hash": "fa40ac4d9b34a665a13e76099f9a51ea79a03fd43dfb9eab7a8cc6b52f8ae47a",
  "token_count": 558,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    9,
    11
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `3da91747-884e-5226-ab20-712e4ebd5abf`

- vector: dim=3072 · [0.0280, -0.0316, -0.0111, 0.0260, -0.0154, -0.0233, -0.0202, 0.0369, …]

```json
{
  "chunk_id": "3da91747-884e-5226-ab20-712e4ebd5abf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff..........................................................................................41",
  "chunk_text": "5.10 \tRetire older, polluting facilities............................................................................................ 42\nConclusions\t\n............................................................................................................................... 44\nBibliography\t\n................................................................................................................................45\nTABLE OF CONTENTS\n\nFigure 1: Route-wise crude steel production share, 2020-21...............................................................7\nFigure 2: Historical steel produc\n\n… [+3363 more chars]",
  "content_hash": "7e850dc7e4ff15b15c1893310d754979ae6584d65c492808ec64a2d989678c35",
  "token_count": 544,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "71ad9fc6-9201-5cd2-a276-b4c2effc7645",
  "chunk_index": 6,
  "page_number": 9,
  "page_range": [
    9,
    11
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `f5ae8d44-fa13-5c1c-ab65-b72167d58baf`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f5ae8d44-fa13-5c1c-ab65-b72167d58baf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "AI – Artificial Intelligence",
  "chunk_text": "AI – Artificial Intelligence\n\nBEE – Bureau of Energy Efficiency \nBF-BOF – Blast Furnace – Basic Oxygen Furnace \nBIS –Bureau of Indian Standards \nCAGR – Compounded Annual Growth Rate \nCBAM – Carbon Border Adjustment Mechanism \nCCUS – Carbon Capture, Use and Storage \nCO2 – Carbon Dioxide DR – Direct Reduction \nEAF – Electric Arc Furnace \nEBITDA – Earnings before Interest, Taxes, Depreciation, and Amortization \nEIF – Electric Induction Furnace \nETS – Emissions Trading Scheme \nFDI – Foreign Direct Investment \nFTA – Free Trade Agreements \nGDP – Gross Domestic Product \nGHG – Greenhouse Gases \nGoI – \n\n… [+1209 more chars]",
  "content_hash": "0d230411fe57745a5f9e603ed9d5013f8cf4050b29a1a3aded89f3cba82bf946",
  "token_count": 449,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    12,
    13
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `ebce17fd-eca3-5605-ad95-53a0e5364d46`

- vector: dim=3072 · [0.0179, 0.0009, -0.0051, -0.0076, -0.0234, -0.0081, -0.0043, 0.0228, …]

```json
{
  "chunk_id": "ebce17fd-eca3-5605-ad95-53a0e5364d46",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "AI – Artificial Intelligence",
  "chunk_text": "BEE – Bureau of Energy Efficiency \nBF-BOF – Blast Furnace – Basic Oxygen Furnace \nBIS –Bureau of Indian Standards \nCAGR – Compounded Annual Growth Rate \nCBAM – Carbon Border Adjustment Mechanism \nCCUS – Carbon Capture, Use and Storage \nCO2 – Carbon Dioxide DR – Direct Reduction \nEAF – Electric Arc Furnace \nEBITDA – Earnings before Interest, Taxes, Depreciation, and Amortization \nEIF – Electric Induction Furnace \nETS – Emissions Trading Scheme \nFDI – Foreign Direct Investment \nFTA – Free Trade Agreements \nGDP – Gross Domestic Product \nGHG – Greenhouse Gases \nGoI – Government of India \nIEA – Int\n\n… [+1179 more chars]",
  "content_hash": "816fec241fccd3fc6d6f3c32278a2a9cdca093498a85c5d7219c1f0c40af4643",
  "token_count": 444,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "f5ae8d44-fa13-5c1c-ab65-b72167d58baf",
  "chunk_index": 7,
  "page_number": 12,
  "page_range": [
    12,
    13
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `d40369bc-8956-54b7-b13c-1a1295d7dea3`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "d40369bc-8956-54b7-b13c-1a1295d7dea3",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": "ENERGY TRANSITIONS — COMMISSION TARDE\n\n•\t\nThe global steel sector is shifting rapidly. More than 30% of steel companies (by \nproduction) have net zero targets - up from zero less than 3 years ago - and more \nthan 90% of countries (by GDP) have national level net zero targets. \n•\t\nGovernments are moving fast to create ‘level playing fields’ to protect domestic \nsteel sectors during transition, including carbon border adjustment proposals, \ncommitments to joint standardization and climate clubs. \n•\t\nThe financial sector is shifting funds away from fossil investments, with a \nsignificant addition\n\n… [+4477 more chars]",
  "content_hash": "9b9d347c644a830f1e9eb2d918d9008178c26d25df0e7bd35f09cad72b00427b",
  "token_count": 1029,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    15,
    17
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `e7655ac3-96f6-53f5-88d4-b0c0e5bb12f8`

- vector: dim=3072 · [0.0253, -0.0162, -0.0100, -0.0053, -0.0168, -0.0325, 0.0055, 0.0120, …]

```json
{
  "chunk_id": "e7655ac3-96f6-53f5-88d4-b0c0e5bb12f8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": "•\t\nThe global steel sector is shifting rapidly. More than 30% of steel companies (by \nproduction) have net zero targets - up from zero less than 3 years ago - and more \nthan 90% of countries (by GDP) have national level net zero targets. \n•\t\nGovernments are moving fast to create ‘level playing fields’ to protect domestic \nsteel sectors during transition, including carbon border adjustment proposals, \ncommitments to joint standardization and climate clubs. \n•\t\nThe financial sector is shifting funds away from fossil investments, with a \nsignificant additional push from COP26 under the Glasgow Fi\n\n… [+1508 more chars]",
  "content_hash": "a1347bc564d9959cb603ad37e83a1957f0a12cd05b6df8620118188830d3e689",
  "token_count": 433,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "d40369bc-8956-54b7-b13c-1a1295d7dea3",
  "chunk_index": 8,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `46964e2c-480b-5118-beb9-4475834cdecb`

- vector: dim=3072 · [0.0237, -0.0320, -0.0015, -0.0123, -0.0340, -0.0195, 0.0017, 0.0161, …]

```json
{
  "chunk_id": "46964e2c-480b-5118-beb9-4475834cdecb",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": "the sector will need to make bold decisions on new \ntechnologies, rapidly build out enabling infrastructure, supported by domestic \npolicy and international finance. The result will be a globally competitive steel \nsector, supporting India’s ambitions of a self-reliant, net zero major economy.\nEXECUTIVE SUMMARY The steel sector plays an important role in the Indian economy and has been a core pillar of India’s industrial \ndevelopment. As a critical input for various sectors, steel will play a major role in helping India support the \ninfrastructure that facilitates growth, the housing that driv\n\n… [+1939 more chars]",
  "content_hash": "ec3dc77cd912aec15ab9c104f48a8fe8425838848822d3b7e3f8d982c45c020a",
  "token_count": 491,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "d40369bc-8956-54b7-b13c-1a1295d7dea3",
  "chunk_index": 9,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `d9574072-ac9e-531a-968e-901f37082db4`

- vector: dim=3072 · [0.0139, -0.0391, -0.0144, -0.0014, -0.0329, -0.0162, 0.0096, 0.0143, …]

```json
{
  "chunk_id": "d9574072-ac9e-531a-968e-901f37082db4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": ", such \nas green product standards and procurement targets, can help ensure that the Indian steel industry is \nprepared to compete in the global steel market as it transitions to low emission production.\nThis roadmap is a follow-up to the consultation document published by TERI in 2020, “Towards a Low Carbon Steel Sector: An overview of the changing market, technology and policy context for Indian steel”. \nThe updated consultation document is available at our website as Tech Annex . The roadmap builds on this \npreceding work, along with other TERI and ETC publications on steel and hydrogen1, i\n\n… [+403 more chars]",
  "content_hash": "87d8eeb000ac0fdcf1958ddd6d9924f00f46da72df15cbbf96cde85941f70a1b",
  "token_count": 213,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "d40369bc-8956-54b7-b13c-1a1295d7dea3",
  "chunk_index": 10,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `62f3149e-c5f3-5e77-9075-d170848bcb51`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "62f3149e-c5f3-5e77-9075-d170848bcb51",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
  "chunk_text": "1 BACKGROUND — 1.1\t Indian steel industry\n\nIndia is currently the world’s second-largest steel producer, and second-largest steel consumer (WSA, \n2020a). The steel industry in India is relatively heterogeneous compared to other countries, with a wide \nrange of different sized facilities in the primary and secondary steelmaking sectors. There are also several \ndifferent technologies currently being used, including the Blast Furnace – Basic Oxygen Furnace (BF-BOF), \ncoal-based Direct Reduction (DR), gas-based DR, Electric Induction Furnace (EIF) and Electric Arc Furnace \n(EAF). BOF technology do\n\n… [+4059 more chars]",
  "content_hash": "73f65b20780464ee2b7af4474139c94606c7c9d6d9ac7f55bb24cf3029c683ac",
  "token_count": 1067,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    19,
    21
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `2684799c-bdc3-56e1-b5e0-ee100d5297fc`

- vector: dim=3072 · [0.0296, 0.0127, -0.0107, -0.0065, -0.0082, -0.0145, 0.0012, -0.0171, …]

```json
{
  "chunk_id": "2684799c-bdc3-56e1-b5e0-ee100d5297fc",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
  "chunk_text": "India is currently the world’s second-largest steel producer, and second-largest steel consumer (WSA, \n2020a). The steel industry in India is relatively heterogeneous compared to other countries, with a wide \nrange of different sized facilities in the primary and secondary steelmaking sectors. There are also several \ndifferent technologies currently being used, including the Blast Furnace – Basic Oxygen Furnace (BF-BOF), \ncoal-based Direct Reduction (DR), gas-based DR, Electric Induction Furnace (EIF) and Electric Arc Furnace \n(EAF). BOF technology dominates a growing share of steel production\n\n… [+1170 more chars]",
  "content_hash": "06edba93bd3aefb37b858565f383d737c102986c10b98f3ff611e7dacdab34c5",
  "token_count": 382,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "62f3149e-c5f3-5e77-9075-d170848bcb51",
  "chunk_index": 11,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `65fef68a-bd8c-5a56-99ea-ebce6c7b6e68`

- vector: dim=3072 · [0.0063, 0.0040, 0.0019, -0.0036, -0.0199, -0.0081, -0.0232, 0.0122, …]

```json
{
  "chunk_id": "65fef68a-bd8c-5a56-99ea-ebce6c7b6e68",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
  "chunk_text": "new steel capacity focused on \nthe BF-BOF and EAF technologies.\nFigure 1: Route-wise crude steel production share, 2020-21\nSource: (MoS, 2021a) \nBackground\n45%\n28%\n27%\nBOF\nEAF\nEIF Figure 2: Historical steel production and use\nSource: (MoS, 2021a; 2021b) \nAs with any industrializing economy, the steel sector is of vital importance to India, contributing around \n2% to the country’s GDP and employing around 2.5 million people in the steel and related sectors (MoS, \n2020a). Crude steel production in India grew from 89 Mt in 2014-15 to 111 Mt in 2019-20. It fell to just \nbelow 100 Mt in 2020-212 fo\n\n… [+1406 more chars]",
  "content_hash": "adc4e8e81b6c91610d219b1af0575688569a232988454c360f4a776be1e86def",
  "token_count": 507,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "62f3149e-c5f3-5e77-9075-d170848bcb51",
  "chunk_index": 12,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `69b7c667-73cc-519e-9c11-0c69e6548f97`

- vector: dim=3072 · [0.0036, -0.0049, 0.0007, 0.0214, -0.0254, -0.0010, -0.0144, 0.0112, …]

```json
{
  "chunk_id": "69b7c667-73cc-519e-9c11-0c69e6548f97",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
  "chunk_text": "attention, including re-considering in commissioning dates of plants \nin the current pipeline, so as not to exacerbate domestic and international overcapacity issues. \nIn 2017, the Ministry of Steel (MoS) launched the National Steel Policy (NSP), which included an aim to increase India’s steelmaking capacity to 300 Mt by 2030. This policy also encompasses targets to reduce \nenergy consumption per tonne of steel, through adopting the latest energy efficiency measures. To support \nthe adoption of energy efficiency measures across a number of sectors, the GoI has developed the Perform, \nAchieve a\n\n… [+688 more chars]",
  "content_hash": "fc3f2d3950310c26a0953708320855d8d0ce73436b632c21be8dc1169afaa237",
  "token_count": 284,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "62f3149e-c5f3-5e77-9075-d170848bcb51",
  "chunk_index": 13,
  "page_number": 20,
  "page_range": [
    20,
    21
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `6735efd5-1ad3-5cb6-9ec6-f2a61992b883`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "6735efd5-1ad3-5cb6-9ec6-f2a61992b883",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.2 Global steel industry",
  "chunk_text": "1.2 Global steel industry\n\nThe global steel industry has continued to grow rapidly over the past few decades, with a significant \nportion of that growth coming from China, which still produces over half of the world’s steel (WSA, 2020a). \nGlobally, crude production of steel increased from 734 Mt in 1991-92 to 1869 Mt in 2018-19. BF-BOF and \nEAF are the dominant routes, currently holding a greater than 99% share for global crude steel production \n(see Figure 3). In 2018, India overtook Japan as the second largest producer of steel, symptomatic of a \nbroader shift in steel production and demand \n\n… [+1361 more chars]",
  "content_hash": "ebdee80d9a350917374a819f1f194674461e6ac7d152675e4ea88d98e7bc1520",
  "token_count": 455,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    21,
    22
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `aea94858-15b5-5a41-9fd2-098f1d473790`

- vector: dim=3072 · [0.0208, 0.0051, -0.0136, 0.0086, -0.0149, -0.0209, 0.0012, -0.0145, …]

```json
{
  "chunk_id": "aea94858-15b5-5a41-9fd2-098f1d473790",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.2 Global steel industry",
  "chunk_text": "The global steel industry has continued to grow rapidly over the past few decades, with a significant \nportion of that growth coming from China, which still produces over half of the world’s steel (WSA, 2020a). \nGlobally, crude production of steel increased from 734 Mt in 1991-92 to 1869 Mt in 2018-19. BF-BOF and \nEAF are the dominant routes, currently holding a greater than 99% share for global crude steel production \n(see Figure 3). In 2018, India overtook Japan as the second largest producer of steel, symptomatic of a \nbroader shift in steel production and demand to developing countries.\nCh\n\n… [+1334 more chars]",
  "content_hash": "3a9e9d9fb00902c82f1c7e67659d3f1be878d5d7ec32c299274138c52bd045d9",
  "token_count": 448,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "6735efd5-1ad3-5cb6-9ec6-f2a61992b883",
  "chunk_index": 14,
  "page_number": 21,
  "page_range": [
    21,
    22
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `bbdf441a-3093-55b6-872d-7c7d563cb744`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "bbdf441a-3093-55b6-872d-7c7d563cb744",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3\t Macro-trends",
  "chunk_text": "1.3\t Macro-trends\n\nIn the coming decades, the iron and steel sector in India will be affected by a number of ‘macro-trends’, \nwhich have the potential to radically change the way steel is produced and consumed. Primarily, these \nare development, digitalisation, and decarbonisation. Development will drive the growth in demand for \nsteel across a number of key sectors, digitalisation will deliver step-changes in productivity, operational \nefficiency and labour intensity of production, and decarbonisation will require new approaches to material \nefficiency and circularity and the adoption of deep\n\n… [+38 more chars]",
  "content_hash": "38eb4beff89e8ec52c8502e40975e5c4c69897de42b8b2a2f696b96d8bf6f1be",
  "token_count": 128,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `687441d7-1545-5fd7-909d-c355cda58034`

- vector: dim=3072 · [-0.0011, -0.0105, -0.0124, -0.0016, 0.0073, -0.0021, -0.0050, -0.0182, …]

```json
{
  "chunk_id": "687441d7-1545-5fd7-909d-c355cda58034",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3\t Macro-trends",
  "chunk_text": "In the coming decades, the iron and steel sector in India will be affected by a number of ‘macro-trends’, \nwhich have the potential to radically change the way steel is produced and consumed. Primarily, these \nare development, digitalisation, and decarbonisation. Development will drive the growth in demand for \nsteel across a number of key sectors, digitalisation will deliver step-changes in productivity, operational \nefficiency and labour intensity of production, and decarbonisation will require new approaches to material \nefficiency and circularity and the adoption of deep decarbonisation pr\n\n… [+19 more chars]",
  "content_hash": "3ab51a02f3c163543143251e73eef94e8b27480e626f8d528a5a00234757e03e",
  "token_count": 120,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "bbdf441a-3093-55b6-872d-7c7d563cb744",
  "chunk_index": 15,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `b38a1ea2-96fb-533d-a05f-1d70d95b52a0`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "b38a1ea2-96fb-533d-a05f-1d70d95b52a0",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.1\t Development",
  "chunk_text": "1.3.1\t Development\n\nSteel is a material of vital importance to countries as they develop, a key input across construction, \ninfrastructure, and manufacturing sectors. As countries reach a certain level of economic development, \nsteel demand starts to saturate, as most major infrastructure is built and future steel demand can largely \nbe satisfied by recycling, or is replaced with alternative materials. As such, we are likely to see emerging \neconomies like India become the major centres of steel demand growth in the coming decades, as demand \nin other major economies, such as China, stabilises\n\n… [+2346 more chars]",
  "content_hash": "b0f3d4cda5cc634c7934c03994efaaae0bf0d504cfe6c7705d5b00db69d24f44",
  "token_count": 704,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    22,
    24
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `03ce0500-0a6b-5cc2-8fca-cd515588433e`

- vector: dim=3072 · [0.0036, 0.0019, -0.0137, 0.0021, -0.0060, -0.0283, 0.0014, -0.0118, …]

```json
{
  "chunk_id": "03ce0500-0a6b-5cc2-8fca-cd515588433e",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.1\t Development",
  "chunk_text": "Steel is a material of vital importance to countries as they develop, a key input across construction, \ninfrastructure, and manufacturing sectors. As countries reach a certain level of economic development, \nsteel demand starts to saturate, as most major infrastructure is built and future steel demand can largely \nbe satisfied by recycling, or is replaced with alternative materials. As such, we are likely to see emerging \neconomies like India become the major centres of steel demand growth in the coming decades, as demand \nin other major economies, such as China, stabilises.\n200\n100\nJapan, Sou\n\n… [+261 more chars]",
  "content_hash": "fffdd4345e5fe347e51ca0bd597cc817b240080d35d0390879ffaf65d89eb323",
  "token_count": 216,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "b38a1ea2-96fb-533d-a05f-1d70d95b52a0",
  "chunk_index": 16,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `241d7bd7-74c0-5722-a48b-1669da1e1bb0`

- vector: dim=3072 · [0.0091, -0.0090, -0.0084, -0.0040, 0.0082, -0.0253, 0.0158, 0.0156, …]

```json
{
  "chunk_id": "241d7bd7-74c0-5722-a48b-1669da1e1bb0",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.1\t Development",
  "chunk_text": "200\n100\nMiddle East\n100\n50\nCIS\n400\n200\nSoutheast Asia\n300\n200\n100\nNAFTA\n200\n100\nAfrica\n100\n50\nSouth and Central America\nCrude steel demand\nScrap availability\nin million metric tonnes Forecasting demand growth out to 2050, and beyond, clearly carries a lot of uncertainty. Both the rate of \neconomic growth, as well as its key drivers, are uncertain. Will India follow a more service-based economy? \nOr will its rate of infrastructure investment and industrialization pick up, following a path more similar to \nthat charted by China and other East Asian industrial powerhouses like South Korea? \nIn ou\n\n… [+1646 more chars]",
  "content_hash": "94aeb6b97b8d2e39a7221f46dd654d73e3af7eb010d1e274b0233874b32d40dd",
  "token_count": 538,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "b38a1ea2-96fb-533d-a05f-1d70d95b52a0",
  "chunk_index": 17,
  "page_number": 23,
  "page_range": [
    23,
    24
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `d10078fe-9d37-5cbb-9239-014bd8adfed9`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "d10078fe-9d37-5cbb-9239-014bd8adfed9",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.2\t Digitalisation",
  "chunk_text": "1.3.2\t Digitalisation\n\nAs with other sectors in the economy, the iron and steel sector is set to realise significant benefits from \nthe digitalisation of production processes and supply chains. This is likely to have a step-change impact in \noperational efficiencies. It will be important to consider digitalisation alongside other major trends, such \nas decarbonisation, to better understand the net impact of such major technological shifts.\nDigitalisation of industry is a wide-ranging area, often covered under topics such as Industry 4.0 (or 4th \nIndustrial Revolution), Internet of Things (IoT)\n\n… [+2684 more chars]",
  "content_hash": "d607e435c7b14785c83c310bcd286121aefc3aab2dd1367a628b34468aa3ceac",
  "token_count": 641,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    24,
    25
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `151361de-b436-59d5-87d1-ececede0c345`

- vector: dim=3072 · [0.0249, 0.0316, -0.0173, 0.0093, 0.0060, 0.0102, 0.0089, -0.0004, …]

```json
{
  "chunk_id": "151361de-b436-59d5-87d1-ececede0c345",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.2\t Digitalisation",
  "chunk_text": "As with other sectors in the economy, the iron and steel sector is set to realise significant benefits from \nthe digitalisation of production processes and supply chains. This is likely to have a step-change impact in \noperational efficiencies. It will be important to consider digitalisation alongside other major trends, such \nas decarbonisation, to better understand the net impact of such major technological shifts.\nDigitalisation of industry is a wide-ranging area, often covered under topics such as Industry 4.0 (or 4th \nIndustrial Revolution), Internet of Things (IoT), cloud computing, Arti\n\n… [+1356 more chars]",
  "content_hash": "972573f203705075e4d8bf6a9f3ca0c017be8895111bac80c77e7c4fa98fc971",
  "token_count": 394,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "d10078fe-9d37-5cbb-9239-014bd8adfed9",
  "chunk_index": 18,
  "page_number": 24,
  "page_range": [
    24,
    24
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `106c1561-5c4a-5559-a953-315cedd22e4b`

- vector: dim=3072 · [0.0193, 0.0098, -0.0099, -0.0006, -0.0018, 0.0066, 0.0058, -0.0003, …]

```json
{
  "chunk_id": "106c1561-5c4a-5559-a953-315cedd22e4b",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.2\t Digitalisation",
  "chunk_text": "multi-year \ndigital-enabled business transformation journey intending to be the leader in digital steel making by 2025 \nthrough the adoption of digital technologies (The Economic Times, 2021). Their Kalinganagar plant has \ndeveloped an expert team of analytics specialists, including data scientists and translators. The net impact of digitalisation on the Indian iron and steel sector is uncertain. It represents a significant\nopportunity for Indian steelmakers as build new capacity in the coming decades, able to take advantage of\nthe latest technologies, unavailable to other countries when they \n\n… [+1020 more chars]",
  "content_hash": "5276fc4e022900eb4074c555eaee4ee36f0ae02f8467f65c248453ac15203bb1",
  "token_count": 298,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "d10078fe-9d37-5cbb-9239-014bd8adfed9",
  "chunk_index": 19,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `bf332323-2dfc-59a2-822e-7ba007c960f4`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "1.3.3 Decarbonisation\n\nThe third macro-trend, and arguably\nthe trend driving the most significant\ndisruption in the iron and steel\nsector, is the growing imperative for\ndecarbonisation. The iron and steel\nsector is currently both highly energy\nand emissions-intensive, accounting\nfor 8% of global final energy use and\n7% of global direct energy-related\nCO2 emissions (including industrial\nprocess emissions) (IEA, 2020). As\nprogress to decarbonize the power\nand transport sectors accelerates,\nwe are starting to see greater focus\non the heavy industry sectors,\nsuch as iron & steel, cement and\nchemic\n\n… [+2225 more chars]",
  "content_hash": "4853f11a8e528fe980045fdfe6b2d4d4069843962efb54bf3b882448afb34c3f",
  "token_count": 1002,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `b8a4fdc1-b3ea-596f-981f-5a4cab66dfce`

- vector: dim=3072 · [0.0185, -0.0229, -0.0181, -0.0074, -0.0297, -0.0470, 0.0145, -0.0104, …]

```json
{
  "chunk_id": "b8a4fdc1-b3ea-596f-981f-5a4cab66dfce",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "The third macro-trend, and arguably\nthe trend driving the most significant\ndisruption in the iron and steel\nsector, is the growing imperative for\ndecarbonisation. The iron and steel\nsector is currently both highly energy\nand emissions-intensive, accounting\nfor 8% of global final energy use and\n7% of global direct energy-related\nCO2 emissions (including industrial\nprocess emissions) (IEA, 2020). As\nprogress to decarbonize the power\nand transport sectors accelerates,\nwe are starting to see greater focus\non the heavy industry sectors,\nsuch as iron & steel, cement and\nchemicals.",
  "content_hash": "9cdc4a5c1930e3f19edb59214a3466f76d5c404a9beda651f3b191c254410060",
  "token_count": 133,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "chunk_index": 20,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `2016fa91-aa35-5177-a341-2634b8dfbac8`

- vector: dim=3072 · [0.0194, 0.0083, -0.0105, 0.0104, -0.0143, -0.0132, 0.0059, 0.0170, …]

```json
{
  "chunk_id": "2016fa91-aa35-5177-a341-2634b8dfbac8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "CO2 emissions (including industrial\nprocess emissions) (IEA, 2020). As\nprogress to decarbonize the power\nand transport sectors accelerates,\nwe are starting to see greater focus\non the heavy industry sectors,\nsuch as iron & steel, cement and\nchemicals. |  | TOTAL STEEL PRODUCED (MN TONNES P.A.)* COMPANY | TOTAL STEEL PRODUCED (MN TONNES P.A.)* COMPANY | TOTAL STEEL PRODUCED (MN TONNES P.A.)* COMPANY | TOTAL STEEL PRODUCED (MN TONNES P.A.)* COMPANY | PROJECTS (WITH LAUNCH YEAR) | PROJECTS (WITH LAUNCH YEAR) | PROJECTS (WITH LAUNCH YEAR) | PROJECTS (WITH LAUNCH YEAR) | PROJECTS (WITH LAUNCH YEAR)\n\n… [+913 more chars]",
  "content_hash": "6aa41ff01a026c5e5489c83b7dc52e340ae4aef0d13245a705d644e60948acb5",
  "token_count": 592,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "chunk_index": 21,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `e69fa337-3862-5a53-a466-66d5f6b75657`

- vector: dim=3072 · [0.0221, -0.0022, -0.0069, 0.0008, -0.0190, -0.0090, 0.0129, 0.0314, …]

```json
{
  "chunk_id": "e69fa337-3862-5a53-a466-66d5f6b75657",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "2030 |  | 2017 |  |  |  |  |  |  |\n|  |  |  | JFE | JFE | TBC | TBC |  |  |  |  |  |  |  |  |  |  | |  |  |  | US Steel | US Steel | TBC | TBC |  |  |  |  |  |  |  |  |  |  |\n|  |  |  | Thyssen Krupp | Thyssen Krupp | 2025 | 2025 | 2025 | 2025 |  | 2027 |  |  |  |  |  |  |\n|  |  |  | Tenaris | Tenaris | TBC | TBC |  |  |  |  |  |  |  |  |  |  |\n|  | 115 57 0 | 115 57 0 |  | Project scale |  |  |  |  |  |  |  |  |  |  |  |  |\n|  | * Source: World Steel in Figures 2020 | * Source: World Steel in Figures 2020 | Full scale Pilots Demonstration Plant | Full scale Pilots Demonstration Plant | Full s\n\n… [+457 more chars]",
  "content_hash": "e1de92854c0bc75cf0017d78f46d3fb2000db6f40c25ed3fd0afd0c65dd0c8ea",
  "token_count": 388,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "chunk_index": 22,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `ab1cfcab-0ef4-5597-9d0b-9e4ab19d7d17`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ab1cfcab-0ef4-5597-9d0b-9e4ab19d7d17",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "250 MtCO2 (about 10% of total",
  "chunk_text": "250 MtCO2 (about 10% of total\n\nemissions) and will increase more than threefold to approximately 800 MtCO, by 2050, if no concerted\naction to decarbonize is taken (Hall, Spencer & Kumar, 2020). Even with ambitious energy and material\nefficiency measures to reduce energy consumption and mitigate demand growth, the level of emissions\nin the Indian iron & steel sector will be incompatible with the ambition of limiting global warming to well\nbelow 2ºC.\n\nFor further emissions reduction, the introduction of new, low carbon technologies will be required, such \nas the use of low carbon hydrogen or car\n\n… [+858 more chars]",
  "content_hash": "e2bc636403ce4ea9579b17aa6665e533cf3886513a271c9c829cfca75f134bdf",
  "token_count": 303,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    25,
    26
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `4731a355-4f0a-5cae-93eb-9d68ce161448`

- vector: dim=3072 · [0.0229, -0.0087, -0.0103, 0.0079, -0.0157, -0.0239, -0.0259, -0.0164, …]

```json
{
  "chunk_id": "4731a355-4f0a-5cae-93eb-9d68ce161448",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "250 MtCO2 (about 10% of total",
  "chunk_text": "emissions) and will increase more than threefold to approximately 800 MtCO, by 2050, if no concerted\naction to decarbonize is taken (Hall, Spencer & Kumar, 2020). Even with ambitious energy and material\nefficiency measures to reduce energy consumption and mitigate demand growth, the level of emissions\nin the Indian iron & steel sector will be incompatible with the ambition of limiting global warming to well\nbelow 2ºC.\n\nFor further emissions reduction, the introduction of new, low carbon technologies will be required, such \nas the use of low carbon hydrogen or carbon, capture, utilisation and s\n\n… [+827 more chars]",
  "content_hash": "d4b644b3a314b357686bae1fa183f651e636ad6b6f16292860690f2272354c06",
  "token_count": 291,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "ab1cfcab-0ef4-5597-9d0b-9e4ab19d7d17",
  "chunk_index": 23,
  "page_number": 25,
  "page_range": [
    25,
    26
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `c349d62f-46eb-54a8-8c30-d32d4fcb9cbd`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c349d62f-46eb-54a8-8c30-d32d4fcb9cbd",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2 MACROECONOMIC IMPACTS — ZA — 2.1\t Overview",
  "chunk_text": "2 MACROECONOMIC IMPACTS — ZA — 2.1\t Overview\n\nThe steel sector contributes around 2% of India’s GDP (MoS, 2020a) and is valued at well over $100bn (Niti \nAayog, 2016). The indirect contribution of the sector is significantly higher, given its enabling role in several \nend-use sectors including construction, infrastructure, industrial machinery and consumer products. For \nthis reason, it is estimated that the investment in the Indian steel sector has an output multiplier effect of \nnearly 4 times on GDP and employment multiplier factor of 6.8 times (NSP, 2017), signalling its importance \nfor In\n\n… [+26 more chars]",
  "content_hash": "657775bd494e548421f0cf18b9d6abf6341a181a84182daddeb6f806a48b2422",
  "token_count": 152,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `004f77c3-23e1-5d46-b4c5-5a53460f780f`

- vector: dim=3072 · [0.0148, 0.0130, -0.0050, -0.0187, 0.0256, -0.0244, 0.0101, 0.0068, …]

```json
{
  "chunk_id": "004f77c3-23e1-5d46-b4c5-5a53460f780f",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2 MACROECONOMIC IMPACTS — ZA — 2.1\t Overview",
  "chunk_text": "The steel sector contributes around 2% of India’s GDP (MoS, 2020a) and is valued at well over $100bn (Niti \nAayog, 2016). The indirect contribution of the sector is significantly higher, given its enabling role in several \nend-use sectors including construction, infrastructure, industrial machinery and consumer products. For \nthis reason, it is estimated that the investment in the Indian steel sector has an output multiplier effect of \nnearly 4 times on GDP and employment multiplier factor of 6.8 times (NSP, 2017), signalling its importance \nfor India’s future growth story.",
  "content_hash": "04904373789c90c1de890d76290f231bd34091544cbcf79f9fcbf15b8ce1af2f",
  "token_count": 132,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "c349d62f-46eb-54a8-8c30-d32d4fcb9cbd",
  "chunk_index": 24,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `de5e6033-8c61-5985-af33-b5fbeb17e795`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "de5e6033-8c61-5985-af33-b5fbeb17e795",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.2\t Investment and profitability",
  "chunk_text": "2.2\t Investment and profitability\n\nThe Indian iron and steel sector is currently relatively financially fragile. Even with a recent upswing with \nnarrow profit margins, low investment intensities, and an increasing interest burden (Hall, Spencer & \nKumar, 2020). The iron and steel sector is highly cyclical, and upswings and downswings are a normal \nfeature of this industry. However, as the impacts of the Covid-19 pandemic have lessened, the global and \nIndian steel sector has seen an improvement in its condition. This being said, it is clear that large and \nrisky investments will not be possib\n\n… [+85 more chars]",
  "content_hash": "f1814ff76f2710a7b3dcd06326cb3df4d279ad62c692e1d19c1d00f2f2003361",
  "token_count": 145,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `0c7a15af-0cc7-5d8f-a638-fcf3fbf3e115`

- vector: dim=3072 · [0.0163, 0.0185, -0.0120, 0.0039, 0.0220, -0.0272, -0.0228, -0.0200, …]

```json
{
  "chunk_id": "0c7a15af-0cc7-5d8f-a638-fcf3fbf3e115",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.2\t Investment and profitability",
  "chunk_text": "The Indian iron and steel sector is currently relatively financially fragile. Even with a recent upswing with \nnarrow profit margins, low investment intensities, and an increasing interest burden (Hall, Spencer & \nKumar, 2020). The iron and steel sector is highly cyclical, and upswings and downswings are a normal \nfeature of this industry. However, as the impacts of the Covid-19 pandemic have lessened, the global and \nIndian steel sector has seen an improvement in its condition. This being said, it is clear that large and \nrisky investments will not be possible without support from public and \n\n… [+50 more chars]",
  "content_hash": "9a31b4c95f1e0809878ea95c3299ed54a53bf7d95f03762002f6e701e958d7e5",
  "token_count": 137,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "de5e6033-8c61-5985-af33-b5fbeb17e795",
  "chunk_index": 25,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `f8a0bb9a-083b-5b88-9b9b-c18323066fd1`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f8a0bb9a-083b-5b88-9b9b-c18323066fd1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.3\t Rapid growth",
  "chunk_text": "2.3\t Rapid growth\n\nOver 80% of India’s iron reserves are in India’s eastern states (Odisha, Jharkhand, West Bengal, \nChhattisgarh and North Andhra Pradesh) (see Figure 8). These states also have access to logistics \ninfrastructure including ports, inland waterways and slurry pipelines (MoS, 2019b). The top states \nin terms of steel production include Odisha (25 Mt), Jharkhand (20 Mt), Chhattisgarh (19 Mt), \nKarnataka (15 Mt), Gujarat (13 Mt) and Maharashtra (12 Mt) (JPC, 2020).\nThe Ministry of Steel, under Mission Purvodaya, aims to support the development of an integrated steel hub \nin easter\n\n… [+1209 more chars]",
  "content_hash": "0fefe1151f662671a20d8d42d2376d98091d7b11627cacec254690f7727e0f8a",
  "token_count": 421,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    28,
    30
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `9820d55d-49ab-5d0c-89a5-b39eaa5dfa03`

- vector: dim=3072 · [0.0153, 0.0179, -0.0009, 0.0047, -0.0328, -0.0216, 0.0030, -0.0185, …]

```json
{
  "chunk_id": "9820d55d-49ab-5d0c-89a5-b39eaa5dfa03",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.3\t Rapid growth",
  "chunk_text": "Over 80% of India’s iron reserves are in India’s eastern states (Odisha, Jharkhand, West Bengal, \nChhattisgarh and North Andhra Pradesh) (see Figure 8). These states also have access to logistics \ninfrastructure including ports, inland waterways and slurry pipelines (MoS, 2019b). The top states \nin terms of steel production include Odisha (25 Mt), Jharkhand (20 Mt), Chhattisgarh (19 Mt), \nKarnataka (15 Mt), Gujarat (13 Mt) and Maharashtra (12 Mt) (JPC, 2020).\nThe Ministry of Steel, under Mission Purvodaya, aims to support the development of an integrated steel hub \nin eastern India to improve \n\n… [+1190 more chars]",
  "content_hash": "ae00d5b06f44f09a670285755091c31ead2a09faff9214712ba528f5e5e08bab",
  "token_count": 414,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "f8a0bb9a-083b-5b88-9b9b-c18323066fd1",
  "chunk_index": 26,
  "page_number": 28,
  "page_range": [
    28,
    30
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `c54323cf-18db-565e-9709-e795520a466a`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c54323cf-18db-565e-9709-e795520a466a",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.4 Employment",
  "chunk_text": "2.4 Employment\n\nThe Indian steel sector currently employs approximately 2.5 million people throughout the supply chain \n(MoS, 2020a). This is estimated to increase to around 3.5 million by 2030, depending on the degree of \nautomation (NSP, 2017). The highest-skilled jobs include engineers and metallurgists, which are vital for \nthe efficient operation of the plants and timely adoption of new technologies. \nHowever, the sector is currently facing a significant skills shortage, which is being exacerbated by skilled \ngraduates moving away from the manufacturing sectors to the service sectors. Thi\n\n… [+1434 more chars]",
  "content_hash": "a1a1ce16efa96f0ec08da164640ebf916632cd0d06892aca920aef09fa927d4d",
  "token_count": 421,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    30,
    32
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `9f95be06-4b5e-5bd4-90c0-e7e0a15f8708`

- vector: dim=3072 · [0.0110, -0.0034, -0.0036, 0.0047, -0.0221, -0.0276, -0.0196, -0.0116, …]

```json
{
  "chunk_id": "9f95be06-4b5e-5bd4-90c0-e7e0a15f8708",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.4 Employment",
  "chunk_text": "The Indian steel sector currently employs approximately 2.5 million people throughout the supply chain \n(MoS, 2020a). This is estimated to increase to around 3.5 million by 2030, depending on the degree of \nautomation (NSP, 2017). The highest-skilled jobs include engineers and metallurgists, which are vital for \nthe efficient operation of the plants and timely adoption of new technologies. \nHowever, the sector is currently facing a significant skills shortage, which is being exacerbated by skilled \ngraduates moving away from the manufacturing sectors to the service sectors. This is being drive\n\n… [+1418 more chars]",
  "content_hash": "18d01cf52894196e4344355a7efa1fc5e3d4f44878fb42e90e7d7bbccd2fb433",
  "token_count": 416,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "c54323cf-18db-565e-9709-e795520a466a",
  "chunk_index": 27,
  "page_number": 30,
  "page_range": [
    30,
    32
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `a9ef31a8-c2b3-5729-8961-e3ed32bb0616`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "a9ef31a8-c2b3-5729-8961-e3ed32bb0616",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.1 Competitiveness",
  "chunk_text": "3.1 Competitiveness\n\nWhilst there have been significant improvements in the operational efficiencies of steel production in\nIndia in recent years, on average, Indian steel producers are still facing costs around 5-10% higher as\ncompared to the global average. In the context of a global glut in steel supply, this places Indian steel\nproducers in a difficult position, reducing profits for reinvestment and limiting export markets. The cost\npremium is driven by a number of factors (see Table 1), with the main contributors being costs of finance\n(approximately 12% versus 3-5% across the European Un\n\n… [+1461 more chars]",
  "content_hash": "537bffd1a6d7f17030c134156e53b525d8a3e20e101c8bc33f80e1f7361354ae",
  "token_count": 494,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    32,
    32
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `acdddbc7-8827-59f4-84c0-a5f16c70a126`

- vector: dim=3072 · [0.0090, -0.0069, -0.0038, 0.0095, -0.0238, -0.0270, -0.0071, -0.0001, …]

```json
{
  "chunk_id": "acdddbc7-8827-59f4-84c0-a5f16c70a126",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.1 Competitiveness",
  "chunk_text": "Whilst there have been significant improvements in the operational efficiencies of steel production in\nIndia in recent years, on average, Indian steel producers are still facing costs around 5-10% higher as\ncompared to the global average. In the context of a global glut in steel supply, this places Indian steel\nproducers in a difficult position, reducing profits for reinvestment and limiting export markets. The cost\npremium is driven by a number of factors (see Table 1), with the main contributors being costs of finance\n(approximately 12% versus 3-5% across the European Union) and the costs of\n\n… [+1440 more chars]",
  "content_hash": "6312fd6b652d89efce801d2469c173927513ae053dae8327238cb5c4324eb498",
  "token_count": 487,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a9ef31a8-c2b3-5729-8961-e3ed32bb0616",
  "chunk_index": 28,
  "page_number": 32,
  "page_range": [
    32,
    32
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `c4b987d2-cc35-50cb-95f4-5bc0a88e505e`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c4b987d2-cc35-50cb-95f4-5bc0a88e505e",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "EBITDA/Net Sales (%) — JSW",
  "chunk_text": "EBITDA/Net Sales (%) — JSW\n\nTata Steel Ltd.\nSteel Authority of India Ltd.\nJindal Steel & Power Ltd.\nJindal Stainless Ltd.\nAverage\nFigure 9: EBITDA for the top five iron and steel producers\nSource: TERI analysis based on annual reports of iron and steel producers (JSW, Tata Steel, SAIL, Jindal Steel & Power Ltd., and \nJindal Stainless Steel Ltd.) \n3\t Earnings before interest, taxes, depreciation, and amortization.\n4\t The Resource Efficiency scenario includes more optimistic assumptions around the lifetime of steel products, the recycling rate, replacement of steel \nwith alternative materials an\n\n… [+574 more chars]",
  "content_hash": "6aafe07f5e385883ef122a8358565240cbdc734f5434eef4e1c170e84c058f31",
  "token_count": 271,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    33,
    33
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `53440e1e-175f-5063-a8af-71aae63bac96`

- vector: dim=3072 · [-0.0091, 0.0220, -0.0130, 0.0111, 0.0219, -0.0132, -0.0445, 0.0049, …]

```json
{
  "chunk_id": "53440e1e-175f-5063-a8af-71aae63bac96",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "EBITDA/Net Sales (%) — JSW",
  "chunk_text": "Tata Steel Ltd.\nSteel Authority of India Ltd.\nJindal Steel & Power Ltd.\nJindal Stainless Ltd.\nAverage\nFigure 9: EBITDA for the top five iron and steel producers\nSource: TERI analysis based on annual reports of iron and steel producers (JSW, Tata Steel, SAIL, Jindal Steel & Power Ltd., and \nJindal Stainless Steel Ltd.) \n3\t Earnings before interest, taxes, depreciation, and amortization.\n4\t The Resource Efficiency scenario includes more optimistic assumptions around the lifetime of steel products, the recycling rate, replacement of steel \nwith alternative materials and light weighting through in\n\n… [+546 more chars]",
  "content_hash": "788d3ed5b1be813a19937a316fa6cfa0ed82c979e44254aa8d9871aaffa33df7",
  "token_count": 260,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "c4b987d2-cc35-50cb-95f4-5bc0a88e505e",
  "chunk_index": 29,
  "page_number": 33,
  "page_range": [
    33,
    33
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `ad57f944-65bb-5fbc-a070-823c4da8b6eb`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ad57f944-65bb-5fbc-a070-823c4da8b6eb",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.2\t Rapid growth required in the near term",
  "chunk_text": "3.2\t Rapid growth required in the near term\n\nAs India’s economy grows, its steel demand will grow substantially. India currently has the world’s second \nlargest population and is expected to be the largest by 2023 (OECD, 2018). By 2030, in our Baseline \nscenario (see Figure 10), we expect steel demand to more than double versus today, increasing the steel \nuse per capita to 150 kg. Under the Resource efficiency4 scenario, steel use per capita is similar over this \ntime frame, given the time taken for resource efficiency measures to have a substantial impact.\nBy 2050, in the Baseline scenario, \n\n… [+1177 more chars]",
  "content_hash": "4ce3fae6d0856b69874fa6dabd9546457ac466c384c4986ecdacd3a71c480678",
  "token_count": 410,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    33,
    34
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `580b0363-c934-5ea2-876f-b7615995eaae`

- vector: dim=3072 · [-0.0111, -0.0007, -0.0032, -0.0006, -0.0144, -0.0281, -0.0072, -0.0028, …]

```json
{
  "chunk_id": "580b0363-c934-5ea2-876f-b7615995eaae",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.2\t Rapid growth required in the near term",
  "chunk_text": "As India’s economy grows, its steel demand will grow substantially. India currently has the world’s second \nlargest population and is expected to be the largest by 2023 (OECD, 2018). By 2030, in our Baseline \nscenario (see Figure 10), we expect steel demand to more than double versus today, increasing the steel \nuse per capita to 150 kg. Under the Resource efficiency4 scenario, steel use per capita is similar over this \ntime frame, given the time taken for resource efficiency measures to have a substantial impact.\nBy 2050, in the Baseline scenario, we expect steel demand per capita to nearly q\n\n… [+1132 more chars]",
  "content_hash": "350f39b2f68af38d1548352036b622fab77590ea1e10b3959c0ea88f9dc02c27",
  "token_count": 398,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "ad57f944-65bb-5fbc-a070-823c4da8b6eb",
  "chunk_index": 30,
  "page_number": 33,
  "page_range": [
    33,
    34
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `192c6065-5cf1-5ec9-8d3c-5ec092881b0c`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "192c6065-5cf1-5ec9-8d3c-5ec092881b0c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3 Technology availability",
  "chunk_text": "3.3 Technology availability\n\nTo achieve deep decarbonisation of the iron and steel sector, new technologies will be required -\nin particular for the replacement of conventional primary production processes with low emissions\nalternatives. There are several emerging low emissions technologies to produce steel from iron ore. They\nbroadly fall into three categories:\n\n· Carbon capture, utilisation, and storage (CCUS)\n\n· The use of low carbon hydrogen to replace fossil fuels\n\n· Direct electrification through electrolysis of iron ore\n\nEach of these technologies differ in their suitability to the Ind\n\n… [+3883 more chars]",
  "content_hash": "386a0618d6123d0c60689a5603ef00c7026a76ad1106ee432a8aa4d377a621e6",
  "token_count": 1005,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    34,
    36
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `452f5453-f766-5889-8b03-ea64ba4fadae`

- vector: dim=3072 · [0.0259, -0.0081, -0.0175, 0.0119, -0.0330, -0.0012, -0.0116, -0.0156, …]

```json
{
  "chunk_id": "452f5453-f766-5889-8b03-ea64ba4fadae",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3 Technology availability",
  "chunk_text": "To achieve deep decarbonisation of the iron and steel sector, new technologies will be required -\nin particular for the replacement of conventional primary production processes with low emissions\nalternatives. There are several emerging low emissions technologies to produce steel from iron ore. They\nbroadly fall into three categories:\n\n· Carbon capture, utilisation, and storage (CCUS)\n\n· The use of low carbon hydrogen to replace fossil fuels\n\n· Direct electrification through electrolysis of iron ore\n\nEach of these technologies differ in their suitability to the Indian context, based on their c\n\n… [+161 more chars]",
  "content_hash": "48f3e411a5bd0a31867a0036d349ada7a1fd30702625aaacf6c7004281f24ae6",
  "token_count": 142,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "192c6065-5cf1-5ec9-8d3c-5ec092881b0c",
  "chunk_index": 31,
  "page_number": 34,
  "page_range": [
    34,
    34
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `345c8e44-03e4-5c99-972b-fe3fde487ad1`

- vector: dim=3072 · [0.0137, -0.0112, -0.0127, 0.0015, -0.0385, -0.0137, -0.0045, 0.0015, …]

```json
{
  "chunk_id": "345c8e44-03e4-5c99-972b-fe3fde487ad1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3 Technology availability",
  "chunk_text": "fossil fuels\n\n· Direct electrification through electrolysis of iron ore\n\nEach of these technologies differ in their suitability to the Indian context, based on their commercial\navailability, ability to reduce emissions, and interface with India's existing infrastructure and resource\nprofile. An overview is provided in Table 2. | Technology | TRL | Emissions reduction potential | Suitability for deep decarbonisation in India |\n| --- | --- | --- | --- |\n| Carbon Capture, Utilisation, and Storage | Carbon Capture, Utilisation, and Storage | Carbon Capture, Utilisation, and Storage |  |\n| BF-BOF w\n\n… [+1928 more chars]",
  "content_hash": "e3338c1efa57aaa45460eb06a00d2ee37cad1d83bcdbda0b9bf36e5fe9536a31",
  "token_count": 539,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "192c6065-5cf1-5ec9-8d3c-5ec092881b0c",
  "chunk_index": 32,
  "page_number": 35,
  "page_range": [
    35,
    35
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `4572236d-ca35-52ee-9063-3648b85c059c`

- vector: dim=3072 · [0.0222, 0.0067, -0.0195, 0.0021, -0.0233, -0.0071, 0.0194, 0.0142, …]

```json
{
  "chunk_id": "4572236d-ca35-52ee-9063-3648b85c059c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3 Technology availability",
  "chunk_text": "2 blending | 7 | It is expected that H, would only be able to replace part of the injected coal, resulting in maximum 20% emissions reduction. | The limited emissions reduction means that H2 injection into BFs can only ever be a transition technology to deeper decarbonisation. | | H, DRI | 7 | Emissions reduction potential depends on the share of H2 and whether the H, is from low carbon sources. Assuming 100% green H2, emissions reduction can be >90%, with residual emissions from carbon sources for steelmaking, graphite electrodes and limestone. | Low cost renewable electricity provides a cost\n\n… [+1171 more chars]",
  "content_hash": "b1117da31ac3e20899c8e3f6236b3ffe6e6e8050ea802c4caa457d22c52e3e95",
  "token_count": 439,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "192c6065-5cf1-5ec9-8d3c-5ec092881b0c",
  "chunk_index": 33,
  "page_number": 35,
  "page_range": [
    35,
    36
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `e6cd6a41-86ff-5f98-a83a-6d4c139a91f4`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e6cd6a41-86ff-5f98-a83a-6d4c139a91f4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.4 Capital requirements",
  "chunk_text": "3.4 Capital requirements\n\nThe transition towards a net-zero steel sector will be highly capital-intensive, as new steel facilities will \nneed to be built, alongside supporting infrastructure (such as electricity, hydrogen and CCUS networks). \nThe Indian steel sector relies heavily on FDI, which was estimated to be over $14 billion between April \n2000 and June 2020 (IBEF, 2021), representing 2.01% of total FDI (DIPP, 2020). This funding is increasingly \nlooking to align itself with a net zero target, meaning only near zero emission steelmaking technologies \nwill attract finance in future (see G\n\n… [+587 more chars]",
  "content_hash": "4bec80ab5977f91ac627099b93ba6473d60c5a98500782d50e11290d610f2576",
  "token_count": 242,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    36,
    36
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `0ec0cc77-7e2b-5815-b705-fd2551d61ef1`

- vector: dim=3072 · [0.0092, 0.0157, -0.0082, -0.0038, -0.0130, -0.0287, 0.0212, 0.0052, …]

```json
{
  "chunk_id": "0ec0cc77-7e2b-5815-b705-fd2551d61ef1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.4 Capital requirements",
  "chunk_text": "The transition towards a net-zero steel sector will be highly capital-intensive, as new steel facilities will \nneed to be built, alongside supporting infrastructure (such as electricity, hydrogen and CCUS networks). \nThe Indian steel sector relies heavily on FDI, which was estimated to be over $14 billion between April \n2000 and June 2020 (IBEF, 2021), representing 2.01% of total FDI (DIPP, 2020). This funding is increasingly \nlooking to align itself with a net zero target, meaning only near zero emission steelmaking technologies \nwill attract finance in future (see Glasgow Financial Alliance \n\n… [+561 more chars]",
  "content_hash": "08dfd93ed5c6f9ef3f28fe329f32c3b78dd44204cf46bf09285d6a6703f7142b",
  "token_count": 236,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "e6cd6a41-86ff-5f98-a83a-6d4c139a91f4",
  "chunk_index": 34,
  "page_number": 36,
  "page_range": [
    36,
    36
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `626d82a2-6ec1-5dad-b507-03e96e3b6925`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "626d82a2-6ec1-5dad-b507-03e96e3b6925",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets\n\nBefore exploring future pathways for the Indian steel sector, it is worth outlining the structure of existing \nassets. Principally, we are concerned with (a) the technological make-up and (b) lifetime of the existing \nassets, as these two factors will be most influential in setting the future direction of the Indian steel sector.\nThe current make-up of India’s iron and steelmaking facilities shows an accelerating trend towards larger, \nintegrated steel plants using blast furnace, basic oxygen furnace and electric\n\n… [+2961 more chars]",
  "content_hash": "504ce46db56bd695545b000b5eb665f88f3c863e688cdb339d697a88278e2bd5",
  "token_count": 789,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    38,
    40
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `5a971ca9-e29a-5685-a930-76fc9e31b300`

- vector: dim=3072 · [0.0143, 0.0073, -0.0143, 0.0020, -0.0228, -0.0138, -0.0195, 0.0043, …]

```json
{
  "chunk_id": "5a971ca9-e29a-5685-a930-76fc9e31b300",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "Before exploring future pathways for the Indian steel sector, it is worth outlining the structure of existing \nassets. Principally, we are concerned with (a) the technological make-up and (b) lifetime of the existing \nassets, as these two factors will be most influential in setting the future direction of the Indian steel sector.\nThe current make-up of India’s iron and steelmaking facilities shows an accelerating trend towards larger, \nintegrated steel plants using blast furnace, basic oxygen furnace and electric arc furnace technologies, as \nper global trends. There is still a relatively sign\n\n… [+1115 more chars]",
  "content_hash": "c3e6114b919ecbb42b41f2a557613a08ce40144c3779e506c00661f4e74787c6",
  "token_count": 363,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "626d82a2-6ec1-5dad-b507-03e96e3b6925",
  "chunk_index": 35,
  "page_number": 38,
  "page_range": [
    38,
    38
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `c578deaa-fdae-5ac6-8324-76e9f58c87a4`

- vector: dim=3072 · [-0.0178, -0.0038, -0.0138, -0.0015, -0.0434, -0.0188, -0.0327, 0.0281, …]

```json
{
  "chunk_id": "c578deaa-fdae-5ac6-8324-76e9f58c87a4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "added. \nFigure 12: Ironmaking and steelmaking production routes, Mt\nSource: (JPC, 2021) \n80\n1.65\n49\nBlast furnace\nCOREX\nSponge iron\n57\n49\n42\nBOF\nEAF\nEIF Based on the largest assessment of blast furnace capacity done to date (Vogl, Olsson & Nykvist, 2021), we \ncan understand in more detail about the lifetime of this technology and timescales for reinvestment. The \naverage blast furnace can last around 45 to 50 years, with between 2 and 3 relining campaigns occurring \nover that timeframe. The length of time between campaigns tends to decrease the more that take place \n(see Figure 14).  \nFigure 1\n\n… [+1315 more chars]",
  "content_hash": "689fc7cb8a2411f7e0f3f2e3e1cdbbe5454b7e4a52e803481a0dc07a6d5104d2",
  "token_count": 465,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "626d82a2-6ec1-5dad-b507-03e96e3b6925",
  "chunk_index": 36,
  "page_number": 39,
  "page_range": [
    39,
    40
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `430cc7b2-b681-5a11-9092-4ed40aff55e2`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "430cc7b2-b681-5a11-9092-4ed40aff55e2",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "4.2 Technology option assessment\n\nAfter understanding the existing technology make-up of the Indian steel sector, it is necessary to \nunderstand how future lower emission technologies could compete, in terms of both costs, as well as \nbroader suitability (resource availability, import / export impacts). TERI and ETC have undertaken detailed \ntechnology assessments for the Indian and global steel sector,5 which will inform the conclusions in this \nsection. \nBased on this assessment, we observe that the costs of steel production from the main conventional \nroutes in India range from around $300/\n\n… [+4941 more chars]",
  "content_hash": "3574d676ab92f76ab28422adefbf673ff71912084feecbed4ad78af494012372",
  "token_count": 1297,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    40,
    42
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `922301fa-18fd-585c-97f4-5dbf7f040360`

- vector: dim=3072 · [0.0011, -0.0226, -0.0220, -0.0032, -0.0266, -0.0294, -0.0066, 0.0141, …]

```json
{
  "chunk_id": "922301fa-18fd-585c-97f4-5dbf7f040360",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "After understanding the existing technology make-up of the Indian steel sector, it is necessary to \nunderstand how future lower emission technologies could compete, in terms of both costs, as well as \nbroader suitability (resource availability, import / export impacts). TERI and ETC have undertaken detailed \ntechnology assessments for the Indian and global steel sector,5 which will inform the conclusions in this \nsection. \nBased on this assessment, we observe that the costs of steel production from the main conventional \nroutes in India range from around $300/t of crude steel, to just below $5\n\n… [+275 more chars]",
  "content_hash": "0aaec12d10e550565d67406a6e89498ef302e08664bb5dc8f4c454d2866bc297",
  "token_count": 195,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "430cc7b2-b681-5a11-9092-4ed40aff55e2",
  "chunk_index": 37,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `cb53d3e7-4a87-5102-aab3-7b787a9cd004`

- vector: dim=3072 · [0.0153, -0.0260, -0.0155, 0.0237, -0.0328, -0.0344, -0.0053, 0.0001, …]

```json
{
  "chunk_id": "cb53d3e7-4a87-5102-aab3-7b787a9cd004",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "et. al, 2020); The Potential Role of Hydrogen in India (Hall et. al, 2020); Green steel through hydrogen direct \nreduction (Hall et. al, 2021); Net-Zero Steel: Sector Transition Strategy (MPP, 2021) analysis is the coal-based direct reduction using a rotary kiln. Lower capital and operational costs, as well \nas having access to cheaper, domestically available fuel mean that this route is one of the cheaper ways \nto produce steel in India today. However, many of these plants are highly polluting and the quality of steel \nproduced is not always sufficient for certain specialist applications. \nNe\n\n… [+1591 more chars]",
  "content_hash": "bdf56084f2d0c21949f413e5f0b109ff67b5fb5b76664668f50271ded80c61e3",
  "token_count": 506,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "430cc7b2-b681-5a11-9092-4ed40aff55e2",
  "chunk_index": 38,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `fbba2519-b45b-50c7-8297-7a057fbf1cfe`

- vector: dim=3072 · [0.0130, -0.0132, -0.0105, 0.0242, -0.0394, -0.0560, -0.0071, 0.0128, …]

```json
{
  "chunk_id": "fbba2519-b45b-50c7-8297-7a057fbf1cfe",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "infrastructure in India, which are reflected in the larger \ncost range for the SR-BOF CCUS route. \nFigure 16: Costs of steel production by route6 \n Source: TERI analysis based on (IEA, 2019) and (MPP, 2021) 6\t BF-BOF = Blast Furnace – Basic Oxygen Furnace, Coal DR-EAF = Coal-based Direct Reduction – Electric Arc Furnace, NG DR-EAF = Natural gas-based \nDirect Reduction – Electric Arc Furnace, SR-BOF CCUS = Smelting Reduction – Basic Oxygen Furnace with Carbon Capture, Usage and or Storage, H2 \nDR-EAF = Hydrogen-based Direct Reduction – Electric Arc Furnace, MOE-EAF = Molten Oxide Electrolysis –\n\n… [+1255 more chars]",
  "content_hash": "db25fc38cbd59199c3cc2a29883f478f800bc81959e3ede1f46dc21f619136df",
  "token_count": 453,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "430cc7b2-b681-5a11-9092-4ed40aff55e2",
  "chunk_index": 39,
  "page_number": 41,
  "page_range": [
    41,
    42
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `3eddf45e-793a-59d4-a15d-3baedfe3dcc8`

- vector: dim=3072 · [0.0255, -0.0084, -0.0105, 0.0109, -0.0259, -0.0565, 0.0027, 0.0216, …]

```json
{
  "chunk_id": "3eddf45e-793a-59d4-a15d-3baedfe3dcc8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "would be cheaper than\nthe hydrogen direct reduction route (provided there are suitable sites closer to the steel plant locations).\nOne key sensitivity to explore in a little more detail is how the cost of hydrogen would impact their relative\ncompetitiveness and how falling costs of green hydrogen could change this over time. In Figure 17, we present the range of costs for a smelting reduction plant with CCUS, as well as declining\ncosts of steel produced via the hydrogen direct reduction route, based on declining costs of hydrogen. With\ncosts in excess of $4/kg today, we can see that hydrogen d\n\n… [+714 more chars]",
  "content_hash": "628ebaeeaddf71e9d129403a923b12af4e39db28fd7e2179325b3aaaece536e0",
  "token_count": 318,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "430cc7b2-b681-5a11-9092-4ed40aff55e2",
  "chunk_index": 40,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `1b320875-fced-5616-8213-97b18e420c63`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1b320875-fced-5616-8213-97b18e420c63",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Hydrogen Cost ($/kg) — SR-BOF CCUS — H, DR-EAF",
  "chunk_text": "Hydrogen Cost ($/kg) — SR-BOF CCUS — H, DR-EAF\n\nSource: TERI analysis based on (IEA, 2019; Hall, Spencer, & Kumar, 2020; BNEF, 2020)\nNote: tCO2 refers to the cost of carbon capture and storage, not to carbon price.\n\npilot facility, being taken forward by Tata Steel Europe in the Netherlands has now switched to developing \na hydrogen direct reduction facility, signalling the industry’s relative support for these technologies. \nConversely, there are over 30 (and growing) hydrogen direct reduction projects. \nSecondly, our estimates for the costs of producing hydrogen in India, whilst among the mo\n\n… [+513 more chars]",
  "content_hash": "12f21fb14cb351feaacc8334b4cc41a06a201dabf50e8b010a8c5b52fb42f344",
  "token_count": 263,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    42,
    43
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `f59ea535-f03f-55f6-b659-02ef03481ecf`

- vector: dim=3072 · [0.0012, -0.0144, -0.0137, 0.0013, -0.0512, -0.0406, 0.0036, 0.0167, …]

```json
{
  "chunk_id": "f59ea535-f03f-55f6-b659-02ef03481ecf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Hydrogen Cost ($/kg) — SR-BOF CCUS — H, DR-EAF",
  "chunk_text": "Source: TERI analysis based on (IEA, 2019; Hall, Spencer, & Kumar, 2020; BNEF, 2020)\nNote: tCO2 refers to the cost of carbon capture and storage, not to carbon price.\n\npilot facility, being taken forward by Tata Steel Europe in the Netherlands has now switched to developing \na hydrogen direct reduction facility, signalling the industry’s relative support for these technologies. \nConversely, there are over 30 (and growing) hydrogen direct reduction projects. \nSecondly, our estimates for the costs of producing hydrogen in India, whilst among the most ambitious \nwhen published, have been supersed\n\n… [+465 more chars]",
  "content_hash": "3fd94e7fdb650e38e9cadc5280c15eb10311a9ed4a15426af7c3f2be6d404503",
  "token_count": 241,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "1b320875-fced-5616-8213-97b18e420c63",
  "chunk_index": 41,
  "page_number": 42,
  "page_range": [
    42,
    43
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `3fc555c6-1d05-5eb0-80c5-a9fb1eda665d`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "3fc555c6-1d05-5eb0-80c5-a9fb1eda665d",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "4.3 Pathways to net zero\n\nOff the back of this understanding the existing assets and future technological trends, we can construct \nfuture pathways to help us better understand the challenges and opportunities of achieving a net zero \nsteel sector. The main scenario illustrated here represents a pathway to net zero by 2070 (NZ2070), in \nline with the Government’s economy-wide net zero target, announced in 2021. We also explore a more \nambitious scenario, which sees the steel sector reach another key government target – ‘Atmanirbhar \nBharat’ (or self-reliance) by 2047 – which also puts it on tr\n\n… [+6025 more chars]",
  "content_hash": "42214833a128f9fd4a31c0aab33bd491b4f517ab9aced138638fb9c84376c9f9",
  "token_count": 1574,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    43,
    48
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `7639440e-35ef-5f4e-80e9-7b798dc70567`

- vector: dim=3072 · [0.0200, -0.0147, -0.0177, -0.0031, -0.0381, -0.0168, 0.0008, 0.0229, …]

```json
{
  "chunk_id": "7639440e-35ef-5f4e-80e9-7b798dc70567",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "Off the back of this understanding the existing assets and future technological trends, we can construct \nfuture pathways to help us better understand the challenges and opportunities of achieving a net zero \nsteel sector. The main scenario illustrated here represents a pathway to net zero by 2070 (NZ2070), in \nline with the Government’s economy-wide net zero target, announced in 2021. We also explore a more \nambitious scenario, which sees the steel sector reach another key government target – ‘Atmanirbhar \nBharat’ (or self-reliance) by 2047 – which also puts it on track for net zero by 2050 (\n\n… [+586 more chars]",
  "content_hash": "c03e39cd153e6c08348ca0121730546304cb7c49bc413c0b5c56bee3d71387da",
  "token_count": 289,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "3fc555c6-1d05-5eb0-80c5-a9fb1eda665d",
  "chunk_index": 42,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `478beb0a-08a6-5fbf-8374-5fa74ac5679a`

- vector: dim=3072 · [0.0047, -0.0145, -0.0126, 0.0070, -0.0279, -0.0114, -0.0012, 0.0202, …]

```json
{
  "chunk_id": "478beb0a-08a6-5fbf-8374-5fa74ac5679a",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": ". \nFigure 18: Net Zero by 2070 scenario\n Source: TERI analysis\nSteel production (Mt)\nBF-BOF\nCoal DR-EAF\nNG DR-EAF\nScrap EAF\nBF-BOF CCUS\nMOE\nH2 DR-EAF From 2040 onwards, we also see some early MOE plants being deployed. They are at an earlier stage of \ndevelopment versus the hydrogen route but could prove competitive in certain areas without access to \nhydrogen, as they use a similar amount of electricity. Scrap-based EAFs will see an ever-increasing role, \nalthough will be limited by the domestic availability of scrap. No import of scrap is assumed. \nIn terms of phasing out existing, high emis\n\n… [+1542 more chars]",
  "content_hash": "5a700939ef680bd3dd3f9dfa6412a1f8b85287624b89e8176c7fa966ab0d6fa5",
  "token_count": 507,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "3fc555c6-1d05-5eb0-80c5-a9fb1eda665d",
  "chunk_index": 43,
  "page_number": 44,
  "page_range": [
    44,
    44
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `d131021e-32cc-54a3-a56e-0023754ea85d`

- vector: dim=3072 · [0.0166, -0.0126, -0.0100, 0.0014, -0.0340, -0.0100, 0.0019, 0.0154, …]

```json
{
  "chunk_id": "d131021e-32cc-54a3-a56e-0023754ea85d",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "achieves Net Zero by 2050, supported by domestic energy resources alone. This highlights the important \njoining together of the Net Zero vision, along with a vision of self-reliance, which can both support one \nanother. \nFigure 19: Net Zero by 2050 scenario Source: TERI analysis\nSteel production (Mt)\nBF-BOF\nCoal DR-EAF\nNG DR-EAF\nScrap EAF\nBF-BOF CCUS\nMOE\nH2 DR-EAF\n\nIn the NZ2050 scenario, low emission technologies are introduced at an even faster rate, with the most \nsignificant additions being made up by hydrogen direct reduction, followed by MOE. The greater challenge \nhere is phasing out bl\n\n… [+1764 more chars]",
  "content_hash": "3abcb7e7c6e495a8c3feb1d46ec4a25b632a3615707b788c10bb863a5597cc99",
  "token_count": 556,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "3fc555c6-1d05-5eb0-80c5-a9fb1eda665d",
  "chunk_index": 44,
  "page_number": 44,
  "page_range": [
    44,
    45
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `0c93286e-0250-566d-8c19-ab29b02e332c`

- vector: dim=3072 · [0.0154, -0.0098, -0.0074, 0.0169, -0.0405, -0.0018, -0.0057, 0.0408, …]

```json
{
  "chunk_id": "0c93286e-0250-566d-8c19-ab29b02e332c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "again by 2070 to 900 \nTWh. This represents 65% of India’s electricity production today, for just a single sector. \nFigure 20: Coking coal demand in Net Zero scenarios\n Source: TERI analysis\nCoking coal demand (Mt)\nNZ2070 NZ2050\n6\t Electricity consumption assumptions = 650 kWh for EAF, 3.4 MWh for MOE and 2.9 MWh for H2DR\n\nIn the NZ2050 scenario, the challenge is even more extreme with demand increasing by 100-fold between \nnow and 2050, before reaching just over 1,000 TWh in 2070. This faster ramp-up is required in order to \nmeet the dual targets of net zero and self-reliance. To put this in t\n\n… [+931 more chars]",
  "content_hash": "aab94ec33ca3eb6344636d4fd6826d8a5897448cd8a7a77efdf7a52371184f55",
  "token_count": 389,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "3fc555c6-1d05-5eb0-80c5-a9fb1eda665d",
  "chunk_index": 45,
  "page_number": 45,
  "page_range": [
    45,
    48
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `6a29ca38-5007-5b71-935e-353c0b562e06`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "6a29ca38-5007-5b71-935e-353c0b562e06",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.1\t Maximize energy efficiency",
  "chunk_text": "5.1\t Maximize energy efficiency\n\nThe application of best available energy efficient technologies (where cost-effective) should be encouraged, \nparticularly in recently built capacity with long lifetimes. Our analysis shows that the application of best \navailable technologies have the potential to reduce energy and emissions by around 15% across the two \nprimary steelmaking routes (see Technical Annex). There are a number of older plants in dire need of \nmodernization and by applying even the already widely adopted efficiency technologies, these plants can \nsubstantially improve their energy ef\n\n… [+963 more chars]",
  "content_hash": "6bfca81c2da0e440645a3cc7210724f96104d5d30af8f731a9f4b8f2baa26e9c",
  "token_count": 362,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    48,
    49
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `051bfdc0-b1b0-542d-8801-25380dd83cd1`

- vector: dim=3072 · [0.0254, 0.0086, -0.0136, -0.0041, -0.0310, 0.0121, -0.0198, 0.0108, …]

```json
{
  "chunk_id": "051bfdc0-b1b0-542d-8801-25380dd83cd1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.1\t Maximize energy efficiency",
  "chunk_text": "The application of best available energy efficient technologies (where cost-effective) should be encouraged, \nparticularly in recently built capacity with long lifetimes. Our analysis shows that the application of best \navailable technologies have the potential to reduce energy and emissions by around 15% across the two \nprimary steelmaking routes (see Technical Annex). There are a number of older plants in dire need of \nmodernization and by applying even the already widely adopted efficiency technologies, these plants can \nsubstantially improve their energy efficiency (see Figure 23).\nIne\u001f ci\n\n… [+930 more chars]",
  "content_hash": "9204db32abfef040b51b77e7dd3c7e7007eb8fa3c809be02c214a50f82abec2d",
  "token_count": 353,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "6a29ca38-5007-5b71-935e-353c0b562e06",
  "chunk_index": 46,
  "page_number": 48,
  "page_range": [
    48,
    49
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `f47ea2af-639d-513c-876d-817d5601aeee`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f47ea2af-639d-513c-876d-817d5601aeee",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.2\t Increase scrap utilisation",
  "chunk_text": "5.2\t Increase scrap utilisation\n\nImproving resource efficiency and encouraging greater levels of material circularity is vital for mitigating \nnegative environmental impacts as India continues to grow. This includes encouraging greater use of scrap, \nwhich reduces the amount of raw material required for primary steel production, resulting in positive knock-\non effects for energy and emissions. \nThe main scrap-based production route is the electric arc furnace (EAF). If we compare the raw materials, \nenergy and emissions from the scrap-based route with a primary steelmaking process, such as a b\n\n… [+1261 more chars]",
  "content_hash": "a62c5622e73edbb31fe4becb718002718222d64f5c43f1365662d322161e95bb",
  "token_count": 445,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    49,
    49
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `8537da82-5b00-52e1-a060-fabb8d14a1b1`

- vector: dim=3072 · [0.0072, -0.0126, -0.0092, 0.0024, -0.0272, -0.0057, 0.0042, -0.0166, …]

```json
{
  "chunk_id": "8537da82-5b00-52e1-a060-fabb8d14a1b1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.2\t Increase scrap utilisation",
  "chunk_text": "Improving resource efficiency and encouraging greater levels of material circularity is vital for mitigating \nnegative environmental impacts as India continues to grow. This includes encouraging greater use of scrap, \nwhich reduces the amount of raw material required for primary steel production, resulting in positive knock-\non effects for energy and emissions. \nThe main scrap-based production route is the electric arc furnace (EAF). If we compare the raw materials, \nenergy and emissions from the scrap-based route with a primary steelmaking process, such as a blast \nfurnace with a basic oxygen\n\n… [+1228 more chars]",
  "content_hash": "b168c63d0981dc23b26612dff24ad419bcad456ea824de139e73bbd734204bab",
  "token_count": 436,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "f47ea2af-639d-513c-876d-817d5601aeee",
  "chunk_index": 47,
  "page_number": 49,
  "page_range": [
    49,
    49
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `53808833-b96a-5bee-b7e4-044d05ad7b66`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "53808833-b96a-5bee-b7e4-044d05ad7b66",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.3\t Create procurement alliances",
  "chunk_text": "5.3\t Create procurement alliances\n\nTo send clear demand signals to steel producers to start producing green steel, groups of corporates who \nuse steel can band together to create clubs which achieve a critical mass of demand. Over time, such clubs \ncould provide guaranteed markets for green steel, helping to de-risk investments for producers. SteelZero \nis an example of such an initiative in the private sector. Discussions are at an early stage in India.\nAlongside private sector activity, to help drive initial large-scale demand for green products, governments \nand public bodies should also co\n\n… [+771 more chars]",
  "content_hash": "5a1628e7b6ebe831bfd60f16571ea7ce19424e4ca431d85c134542ca8cfb269b",
  "token_count": 264,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `edc78c62-5e99-5e47-a15e-f63ecdb06e56`

- vector: dim=3072 · [0.0081, -0.0085, -0.0168, 0.0049, -0.0388, -0.0140, 0.0180, 0.0077, …]

```json
{
  "chunk_id": "edc78c62-5e99-5e47-a15e-f63ecdb06e56",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.3\t Create procurement alliances",
  "chunk_text": "To send clear demand signals to steel producers to start producing green steel, groups of corporates who \nuse steel can band together to create clubs which achieve a critical mass of demand. Over time, such clubs \ncould provide guaranteed markets for green steel, helping to de-risk investments for producers. SteelZero \nis an example of such an initiative in the private sector. Discussions are at an early stage in India.\nAlongside private sector activity, to help drive initial large-scale demand for green products, governments \nand public bodies should also commit to procuring environmentally s\n\n… [+736 more chars]",
  "content_hash": "ef834866cecead42852ef1782fab0cf5b9e6357c73f03a3dd758906d13c8c1cb",
  "token_count": 256,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "53808833-b96a-5bee-b7e4-044d05ad7b66",
  "chunk_index": 48,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `c278deda-b6ba-5aed-b7e6-65bd9f4c6841`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c278deda-b6ba-5aed-b7e6-65bd9f4c6841",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.4\t Introduce green product standards",
  "chunk_text": "5.4\t Introduce green product standards\n\nTo help grow the market for green steel as a premium product, public and private sector players will need to \ndevelop and implement green product standards and related product labelling. This will help consumers \ndecide between more or less sustainable products, as they seek to decarbonize their supply chains.\nThe Confederation of Indian Industry (CII) is working in partnership with producers such as Tata Steel \nto apply its GreenPro framework to products such as steel rebar. At the global level, an alliance of steel \nproducers and users are developing ‘\n\n… [+1010 more chars]",
  "content_hash": "465f3a9f23c096fed69959e865c58998cf137f4e991d9ece3b455373db93bf2a",
  "token_count": 326,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `67611954-cfe9-55ba-8bca-76490fd82e86`

- vector: dim=3072 · [0.0265, 0.0028, -0.0215, 0.0183, -0.0010, -0.0021, 0.0086, -0.0031, …]

```json
{
  "chunk_id": "67611954-cfe9-55ba-8bca-76490fd82e86",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.4\t Introduce green product standards",
  "chunk_text": "To help grow the market for green steel as a premium product, public and private sector players will need to \ndevelop and implement green product standards and related product labelling. This will help consumers \ndecide between more or less sustainable products, as they seek to decarbonize their supply chains.\nThe Confederation of Indian Industry (CII) is working in partnership with producers such as Tata Steel \nto apply its GreenPro framework to products such as steel rebar. At the global level, an alliance of steel \nproducers and users are developing ‘ResponsibleSteel’ standards, where a red\n\n… [+970 more chars]",
  "content_hash": "16307f30bb0cd91795b11ffe9ce6663af85649fc172aaaf74b8619efbcd4779b",
  "token_count": 316,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "c278deda-b6ba-5aed-b7e6-65bd9f4c6841",
  "chunk_index": 49,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `1d83eae1-267c-5595-8aea-42ce86d4c809`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1d83eae1-267c-5595-8aea-42ce86d4c809",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.5\t Promote technical research & development and set-",
  "chunk_text": "5.5\t Promote technical research & development and set-\n\nup demonstration plants\nTechnological research and development (R&D) plays a crucial role in determining a steel producer’s \nsustained success in global markets. Whilst the Indian steel sector has invested some resources into R&D \nfor cleaner production, this is often limited to early-stage laboratory and pilot scale efforts. To do this at \nthe pace and scale required will require joint efforts from the government and industry. The Government of \nIndia, through the “Promotion of R&D in Iron & Steel Sector” scheme has been providing financ\n\n… [+819 more chars]",
  "content_hash": "f0bc8cc48c8da2777077e53eef39c03dfe11e38c014c8af1709a668a6e966c0c",
  "token_count": 272,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    51,
    51
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `13e50e3e-0967-5c17-b2b7-513e14e65f6c`

- vector: dim=3072 · [0.0118, 0.0273, -0.0180, -0.0079, -0.0132, -0.0229, 0.0032, 0.0075, …]

```json
{
  "chunk_id": "13e50e3e-0967-5c17-b2b7-513e14e65f6c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.5\t Promote technical research & development and set-",
  "chunk_text": "up demonstration plants\nTechnological research and development (R&D) plays a crucial role in determining a steel producer’s \nsustained success in global markets. Whilst the Indian steel sector has invested some resources into R&D \nfor cleaner production, this is often limited to early-stage laboratory and pilot scale efforts. To do this at \nthe pace and scale required will require joint efforts from the government and industry. The Government of \nIndia, through the “Promotion of R&D in Iron & Steel Sector” scheme has been providing financial support \nto R&D projects identified for funding by t\n\n… [+763 more chars]",
  "content_hash": "9fd36318838f2c49c83138f5fc671908ab5d0e1aeb5e5902befaa769062ee128",
  "token_count": 259,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "1d83eae1-267c-5595-8aea-42ce86d4c809",
  "chunk_index": 50,
  "page_number": 51,
  "page_range": [
    51,
    51
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `3fbc07fb-d50c-5cb3-96cd-c3135e2d088c`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "3fbc07fb-d50c-5cb3-96cd-c3135e2d088c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.6\t Future-proof new capacity",
  "chunk_text": "5.6\t Future-proof new capacity\n\nAn important consideration for low carbon steelmaking routes in India is the lifetime of the plants and \nthe possibility of retrofit in the coming decades. Steel plants have long lifetimes (30 years plus), resulting \nin significant potential for emissions lock-in for plants being built in the coming years, when low carbon \noptions might not be commercially available.\nFigure 25 illustrates two potential transition pathways for the leading technologies discussed earlier. \nFor the hydrogen route, gas-based capacity could be built in the 2020s, using natural gas or \n\n… [+1059 more chars]",
  "content_hash": "a3cc50faec67a3e533f102fa799c57c987a8f170f074b59d19cd88fb53dd3f37",
  "token_count": 373,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    51,
    52
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `4c913f94-b6f1-5aab-864c-78be629b895c`

- vector: dim=3072 · [0.0049, -0.0008, -0.0102, 0.0162, -0.0404, -0.0189, -0.0096, 0.0064, …]

```json
{
  "chunk_id": "4c913f94-b6f1-5aab-864c-78be629b895c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.6\t Future-proof new capacity",
  "chunk_text": "An important consideration for low carbon steelmaking routes in India is the lifetime of the plants and \nthe possibility of retrofit in the coming decades. Steel plants have long lifetimes (30 years plus), resulting \nin significant potential for emissions lock-in for plants being built in the coming years, when low carbon \noptions might not be commercially available.\nFigure 25 illustrates two potential transition pathways for the leading technologies discussed earlier. \nFor the hydrogen route, gas-based capacity could be built in the 2020s, using natural gas or coal-based \nsyngas, which is mor\n\n… [+1027 more chars]",
  "content_hash": "d48cc6bdc7173eaf478ef8f334a11ab37986f91ede17e1c00e788217b89f279c",
  "token_count": 364,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "3fbc07fb-d50c-5cb3-96cd-c3135e2d088c",
  "chunk_index": 51,
  "page_number": 51,
  "page_range": [
    51,
    52
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `e2055103-754c-5c92-8520-ec53409c8a06`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e2055103-754c-5c92-8520-ec53409c8a06",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.7 Lay the groundwork for a domestic carbon trading market",
  "chunk_text": "5.7 Lay the groundwork for a domestic carbon trading market\n\nAn important tool to help accelerate the switch to low carbon technologies is development of domestic\ncarbon trading market. India has already achieved much success with the implementation of the Perform,\nAchieve and Trade (PAT) scheme, which trades energy efficiency certificates between Designated\nConsumers (DCS), including the iron and steel sector. As the need for emission reduction grows, one\npossibility would be to amend this existing policy to measure and control carbon emissions, as opposed\nto energy consumption. This would op\n\n… [+410 more chars]",
  "content_hash": "08724bb594e6a7ad00b50cfbae8ac050412f1c6adb2954dd3e27039fdb3f17d9",
  "token_count": 200,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `95e1bd9a-5eaf-5d4e-afbb-a99e7dfa3b35`

- vector: dim=3072 · [0.0155, -0.0142, -0.0117, 0.0041, -0.0472, 0.0026, -0.0477, 0.0074, …]

```json
{
  "chunk_id": "95e1bd9a-5eaf-5d4e-afbb-a99e7dfa3b35",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.7 Lay the groundwork for a domestic carbon trading market",
  "chunk_text": "An important tool to help accelerate the switch to low carbon technologies is development of domestic\ncarbon trading market. India has already achieved much success with the implementation of the Perform,\nAchieve and Trade (PAT) scheme, which trades energy efficiency certificates between Designated\nConsumers (DCS), including the iron and steel sector. As the need for emission reduction grows, one\npossibility would be to amend this existing policy to measure and control carbon emissions, as opposed\nto energy consumption. This would operate similar to the EU Emissions Trading Scheme (ETS).\n\nTaki\n\n… [+349 more chars]",
  "content_hash": "655113382d490384bd6911e0b2b0a6cbc04c52f72b8c45ac7fe8472021170d3b",
  "token_count": 187,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "e2055103-754c-5c92-8520-ec53409c8a06",
  "chunk_index": 52,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `c00ab0bb-37c1-5d96-8ae9-01ec00cf349b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c00ab0bb-37c1-5d96-8ae9-01ec00cf349b",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.8 Support for commercial-scale plants",
  "chunk_text": "5.8 Support for commercial-scale plants\n\nAs a series of demonstration projects in the 2020s help clarify the preferred technology options for low\nemission steel production in India, by the 20305, public and private sector should have proven joint\nfinancing models to facilitate the construction of commercial-scale green steel plants. This will require\nconsiderable support, assuming some cost difference between green steel and 'dirty' steel persists. Whilst\nthe difference in production costs will be mitigated somewhat if green product standards, procurement\ninitiatives, and an emissions penalty \n\n… [+1249 more chars]",
  "content_hash": "b4e2a1c7d10b6f62d6850636bfbe3d5ba0db7904efeef899ce7aae21dd73efaf",
  "token_count": 348,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    52,
    53
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `89834947-b0e6-55bc-88a2-f320c4d86224`

- vector: dim=3072 · [0.0125, -0.0004, -0.0190, 0.0055, -0.0265, -0.0073, 0.0125, 0.0140, …]

```json
{
  "chunk_id": "89834947-b0e6-55bc-88a2-f320c4d86224",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.8 Support for commercial-scale plants",
  "chunk_text": "As a series of demonstration projects in the 2020s help clarify the preferred technology options for low\nemission steel production in India, by the 20305, public and private sector should have proven joint\nfinancing models to facilitate the construction of commercial-scale green steel plants. This will require\nconsiderable support, assuming some cost difference between green steel and 'dirty' steel persists. Whilst\nthe difference in production costs will be mitigated somewhat if green product standards, procurement\ninitiatives, and an emissions penalty are introduced, it may still be necessary\n\n… [+1208 more chars]",
  "content_hash": "5bd30d3933f35678fddaa2b405059effc37c2e48ba35268e64cba5c745251813",
  "token_count": 339,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "c00ab0bb-37c1-5d96-8ae9-01ec00cf349b",
  "chunk_index": 53,
  "page_number": 52,
  "page_range": [
    52,
    53
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `90684a8c-367e-5fee-bd72-5849a8384350`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "90684a8c-367e-5fee-bd72-5849a8384350",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff",
  "chunk_text": "5.9\t Implement a carbon border tariff\n\nSteel, a carbon intensive product which is also heavily traded globally, has found a lot of attention in \nrecent years in the trade environment policy discourses. For example, the EU green deal mentions \nimposition of Carbon Border Adjustment Mechanism (CBAM), to prevent carbon leakage while creating \nlevel playing field in the EU where steel is one of the few sectors that will come under this measure. It may \nbe worth exploring similar import restrictions on steel imports to India originating from countries having \nFigure 26: Carbon border adjustment\nSou\n\n… [+2297 more chars]",
  "content_hash": "fbeeb637f45fd5378d816404d010611ed330a68d65c3024e55f89bea2c881e06",
  "token_count": 608,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    53,
    55
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `4af5dae5-3e9a-5f3e-a997-d7bd7fcce5af`

- vector: dim=3072 · [-0.0060, -0.0121, -0.0097, -0.0016, -0.0039, -0.0191, -0.0469, 0.0068, …]

```json
{
  "chunk_id": "4af5dae5-3e9a-5f3e-a997-d7bd7fcce5af",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff",
  "chunk_text": "Steel, a carbon intensive product which is also heavily traded globally, has found a lot of attention in \nrecent years in the trade environment policy discourses. For example, the EU green deal mentions \nimposition of Carbon Border Adjustment Mechanism (CBAM), to prevent carbon leakage while creating \nlevel playing field in the EU where steel is one of the few sectors that will come under this measure. It may \nbe worth exploring similar import restrictions on steel imports to India originating from countries having \nFigure 26: Carbon border adjustment\nSource: TERI\n+ carbon tax\nat the border\nCh\n\n… [+101 more chars]",
  "content_hash": "4fff29ad813d62b1b4638799ec3d48cccbb9879e906436224f36cb6807c17333",
  "token_count": 142,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "90684a8c-367e-5fee-bd72-5849a8384350",
  "chunk_index": 54,
  "page_number": 53,
  "page_range": [
    53,
    53
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `794200f4-54f2-5b05-a50b-185635f3f244`

- vector: dim=3072 · [-0.0088, -0.0133, -0.0030, -0.0024, -0.0164, -0.0099, -0.0474, 0.0279, …]

```json
{
  "chunk_id": "794200f4-54f2-5b05-a50b-185635f3f244",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff",
  "chunk_text": "be worth exploring similar import restrictions on steel imports to India originating from countries having \nFigure 26: Carbon border adjustment\nSource: TERI\n+ carbon tax\nat the border\nCheaper imports\nwithout carbon tax\nCarbon border tax protects\ndomestic industry during transition\n250\n0 higher steel carbon intensity. This may dissuade Indian steel importers from importing and will help in \nswitching to domestic. Additional revenue, that may be collected as import duty, based on carbon content \nof imported steel, can be considered for supporting India’s greening of steel. This may enhance expor\n\n… [+1843 more chars]",
  "content_hash": "14ca1a97199d0304fe78ee85997a99d268b4970174b23518a02c4c723e9c1c23",
  "token_count": 514,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "90684a8c-367e-5fee-bd72-5849a8384350",
  "chunk_index": 55,
  "page_number": 54,
  "page_range": [
    54,
    55
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `a99f1710-0aca-504c-ae7e-4a8d016f3ee3`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "a99f1710-0aca-504c-ae7e-4a8d016f3ee3",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "Conclusions\n\nThe Indian steel sector is on the cusp of a significant transformation. As explored in this report, India is \nwell positioned to reap many of the benefits associated with a competitive, digital, and decarbonised \nsector, making use of domestic resources and skills. \nNonetheless, there are significant risks of not rising to this challenge. The global steel sector is shifting \nrapidly, with governments, the finance sector, and steel buyers all moving fast to clean up their act. India \ncurrently operates one of the highest polluting steel sectors and so has further to go than many ot\n\n… [+6295 more chars]",
  "content_hash": "2a4e1dd11d898d71c6b83da46ce1af0f2fa3996a876a4124829117d8ade1cc56",
  "token_count": 1938,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    56,
    58
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `435e0044-b723-5726-b8ac-c3f3bb3f2a92`

- vector: dim=3072 · [0.0262, -0.0235, -0.0160, 0.0046, -0.0191, -0.0154, -0.0024, 0.0006, …]

```json
{
  "chunk_id": "435e0044-b723-5726-b8ac-c3f3bb3f2a92",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "The Indian steel sector is on the cusp of a significant transformation. As explored in this report, India is \nwell positioned to reap many of the benefits associated with a competitive, digital, and decarbonised \nsector, making use of domestic resources and skills. \nNonetheless, there are significant risks of not rising to this challenge. The global steel sector is shifting \nrapidly, with governments, the finance sector, and steel buyers all moving fast to clean up their act. India \ncurrently operates one of the highest polluting steel sectors and so has further to go than many others, \nwhilst\n\n… [+348 more chars]",
  "content_hash": "31cd9d5c0010afc0f58229711817b0232cb1798de60ac14208ea96eb8564299e",
  "token_count": 190,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a99f1710-0aca-504c-ae7e-4a8d016f3ee3",
  "chunk_index": 56,
  "page_number": 56,
  "page_range": [
    56,
    56
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `25f58c8d-2e8a-5d5a-bdcf-e6a65547d180`

- vector: dim=3072 · [0.0167, 0.0090, -0.0124, 0.0139, -0.0132, -0.0039, 0.0100, 0.0059, …]

```json
{
  "chunk_id": "25f58c8d-2e8a-5d5a-bdcf-e6a65547d180",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "Whilst challenging, this report sets out that such a pathway is possible and desirable. Through rapidly \nscaling-up renewable electricity and green hydrogen production, in particular, the steel sector can shift \naway from imported fossil fuels, putting the sector on a path to a net zero, self-reliant future. ArcelorMittal. (2021). ArcelorMittal launches XCarb™, signalling its commitment to producing carbon neutral \nsteel. \nRetrieved \nfrom \nhttps://corporate.arcelormittal.com/media/press-releases/arcelormittal-launches-\nxcarb-signalling-its-commitment-to-producing-carbon-neutral-steel#:~:text=A\n\n… [+1233 more chars]",
  "content_hash": "a3a58413f06c31438226bea1c7285d69f40b96212fe25510dee3a7761f8f6715",
  "token_count": 494,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a99f1710-0aca-504c-ae7e-4a8d016f3ee3",
  "chunk_index": 57,
  "page_number": 57,
  "page_range": [
    57,
    57
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `aec6a648-0987-5e58-828a-b8d5fe9c0a40`

- vector: dim=3072 · [0.0213, 0.0080, -0.0146, 0.0136, -0.0174, -0.0089, 0.0048, -0.0036, …]

```json
{
  "chunk_id": "aec6a648-0987-5e58-828a-b8d5fe9c0a40",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "al-steel-and-power-using-iot-future-proof-its-business\nDeloitte. (2021). The Deloitte Global Millennial Survey 2020. Retrieved from https://www2.deloitte.com/global/en/\npages/about-deloitte/articles/millennialsurvey.html DIPP. (2020). Fact sheet on foreign direct investment (FDI). Retrieved from https://dipp.gov.in/sites/default/files/\nFDI_Factsheet_June20_23Sept2020.pdf\nDIW Berlin, TERI. (2020). Transitioning India’s steel and cement industries to low carbon pathways. Retrieved from \nhttps://www.diw.de/documents/dokumentenarchiv/17/diw_01.c.794597.de/cs-ndc_tracking_india_jul_2020.pdf\nEuropea\n\n… [+1224 more chars]",
  "content_hash": "821794098beae4390253bc8c3be48d4c7182fdc5b4b5a01abdfcdd8a7f1a0622",
  "token_count": 502,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a99f1710-0aca-504c-ae7e-4a8d016f3ee3",
  "chunk_index": 58,
  "page_number": 57,
  "page_range": [
    57,
    57
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `faa68e5f-7f42-53ed-9dff-415735df20c3`

- vector: dim=3072 · [0.0093, 0.0095, -0.0083, 0.0169, 0.0018, -0.0152, -0.0156, 0.0151, …]

```json
{
  "chunk_id": "faa68e5f-7f42-53ed-9dff-415735df20c3",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "-toward-\nfossil-free-steel\nIBEF. (2018). Retrieved from https://www.ibef.org/states/odisha-presentation\nIBEF. (2020). Retrieved from https://www.ibef.org/download/Chhattisgarh-June-2020.pdf IBEF. (2021). Retrieved from https://www.ibef.org/states/steel-presentation\nBibliography\n\nIEA. (2017). Renewable Energy for Industry. Retrieved from https://iea.blob.core.windows.net/assets/48356f8e-77a7-\n49b8-87de-87326a862a9a/Insights_series_2017_Renewable_Energy_for_Industry.pdf\nIEA. (2020). Iron and Steel Technology Roadmap: Towards more sustainable steelmaking. Retrieved October 2020, \nfrom \nhttps://ie\n\n… [+1112 more chars]",
  "content_hash": "4a345ca05ee15a598dc073d1c76d147f28a8461cd5e29a3dd626f174edafb779",
  "token_count": 521,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a99f1710-0aca-504c-ae7e-4a8d016f3ee3",
  "chunk_index": 59,
  "page_number": 57,
  "page_range": [
    57,
    58
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `e28042e8-3ff5-59c9-8320-9d55a96eca56`

- vector: dim=3072 · [0.0273, 0.0083, -0.0126, 0.0057, 0.0113, -0.0017, -0.0088, 0.0213, …]

```json
{
  "chunk_id": "e28042e8-3ff5-59c9-8320-9d55a96eca56",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "20Term%20Perspectives.pdf\nMoS. (2019). Draft Framework Policy - Development of Steel Clusters in India. Retrieved from Ministry of Steel: https://\nsteel.gov.in/sites/default/files/Draft%20Policy%20for%20Steel%20Cluster_vf15.pdf MoS. (2020a). Annual Report 2019-20. Retrieved from https://steel.gov.in/sites/default/files/Annual%20Report-\nMinistry%20of%20Steel%202019-20.pdf\nMoS. (2020b). Retrieved from https://www.pib.gov.in/PressReleasePage.aspx?PRID=1673977\nMoS. (2021a). Annual Report 2020-21. Retrieved from https://steel.gov.in/sites/default/files/Annual%20Report-\nMinistry%20of%20Steel%202020-\n\n… [+909 more chars]",
  "content_hash": "03514123c6ca3b6367b531e2eb5b3acb4b44f597b268410f5b38f20e0b1494de",
  "token_count": 466,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "a99f1710-0aca-504c-ae7e-4a8d016f3ee3",
  "chunk_index": 60,
  "page_number": 58,
  "page_range": [
    58,
    58
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Parent · `27bd41ee-f5ca-5f8b-94e0-a00ec8314546`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "27bd41ee-f5ca-5f8b-94e0-a00ec8314546",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "Conclusions (cont.)\n\nOECD. (2018). Economic Outlook No 103 - July 2018 - Long-term baseline projections. (Organisation for Economic Co-\noperation and Development) Retrieved from Stat: https://stats.oecd.org/Index.aspx?DataSetCode=EO103_LTB\nPHDCCI. (2019). Retrieved from https://www.phdcci.in/wp-content/uploads/2019/01/Rising-Jharkhand-Economic-\nProfile-_final-for-Print-Low-size-updated.pdf\nPIB. (2021). Production Linked Incentive (PLI) Scheme for Specialty Steel Approved by Union Cabinet. Retrieved from \nhttps://pib.gov.in/PressReleasePage.aspx?PRID=1738126\nPrimetals Technologies. (2019). Prim\n\n… [+3171 more chars]",
  "content_hash": "8a0075d788a654f44b2b9c051557bd591797b0d2cf8dc692e24f21cd3b26dd45",
  "token_count": 1072,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "page_range": [
    59,
    60
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `244dc7b2-e82f-5831-ae7c-779dda4e4ed8`

- vector: dim=3072 · [0.0284, 0.0238, -0.0107, 0.0295, 0.0069, -0.0076, 0.0079, 0.0116, …]

```json
{
  "chunk_id": "244dc7b2-e82f-5831-ae7c-779dda4e4ed8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "OECD. (2018). Economic Outlook No 103 - July 2018 - Long-term baseline projections. (Organisation for Economic Co-\noperation and Development) Retrieved from Stat: https://stats.oecd.org/Index.aspx?DataSetCode=EO103_LTB\nPHDCCI. (2019). Retrieved from https://www.phdcci.in/wp-content/uploads/2019/01/Rising-Jharkhand-Economic-\nProfile-_final-for-Print-Low-size-updated.pdf\nPIB. (2021). Production Linked Incentive (PLI) Scheme for Specialty Steel Approved by Union Cabinet. Retrieved from \nhttps://pib.gov.in/PressReleasePage.aspx?PRID=1738126\nPrimetals Technologies. (2019). Primetals Technologies de\n\n… [+1014 more chars]",
  "content_hash": "f4f1bc544b6adcc6ee15e22a75be9773f15ea75292015b573edd1fa09967249e",
  "token_count": 437,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "27bd41ee-f5ca-5f8b-94e0-a00ec8314546",
  "chunk_index": 61,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `e4a4aef9-fedf-5cad-b653-d1b19b8186f9`

- vector: dim=3072 · [0.0411, 0.0220, -0.0039, 0.0091, -0.0078, 0.0036, 0.0071, 0.0056, …]

```json
{
  "chunk_id": "e4a4aef9-fedf-5cad-b653-d1b19b8186f9",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "Tata Steel. (2021). Tata Steel commissions India’s first plant for CO2 capture from Blast Furnace gas at Jamshedpur. \nRetrieved from https://www.tatasteel.com/media/newsroom/press-releases/india/2021/tata-steel-commissions- india-s-first-plant-for-co2-capture-from-blast-furnace-gas-at-jamshedpur/\nTERI. (2020). Transitioning India’s steel and cement industries to low carbon pathways. Retrieved from https://www.\ndiw.de/documents/dokumentenarchiv/17/diw_01.c.794597.de/cs-ndc_tracking_india_jul_2020.pdf\nThe Economic Times. (2021). Tata Steel’s Jamshedpur plant recognised as advanced 4th industrial\n\n… [+1170 more chars]",
  "content_hash": "02ba10a948bbe2746c5ca3af6b6bdeaac26da704e59a30d6d5376291ad8709ad",
  "token_count": 497,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "27bd41ee-f5ca-5f8b-94e0-a00ec8314546",
  "chunk_index": 62,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```

## Child · `ba33c38a-29e3-5ce2-acb1-90549857e10f`

- vector: dim=3072 · [0.0231, 0.0261, -0.0090, -0.0095, -0.0052, -0.0279, 0.0157, 0.0127, …]

```json
{
  "chunk_id": "ba33c38a-29e3-5ce2-acb1-90549857e10f",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "chunk_text": "/export\nWorld Bank. (2017). World Development Indicators. \nWSA. (2018). Steel Statistical Yearbook 2018. \nWSA. (2019). Towards a net-zero emissions steel industry. Retrieved from https://iea-industry.org/app/uploads/5- Ekdahl-Towrds-a-net-zero-emissions-steel-industry.pdf\nWSA. (2020a). World Steel in figures. Retrieved 2020, from World Steel Association: https://www.worldsteel.org/en/\ndam/jcr:f7982217-cfde-4fdc-8ba0-795ed807f513/World%2520Steel%2520in%2520Figures%25202020i.pdf\nWSA. (2020b). Steel Statistical Yearbook 2020 Concise Version. Retrieved from https://www.worldsteel.org/en/dam/\njcr:5\n\n… [+207 more chars]",
  "content_hash": "bfc6cd06915aab52ee1351e535aafdbd13457e47685a0a30e8efc9165a1cbb39",
  "token_count": 252,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "27bd41ee-f5ca-5f8b-94e0-a00ec8314546",
  "chunk_index": 63,
  "page_number": 59,
  "page_range": [
    59,
    60
  ],
  "created_at": "2026-06-25T11:17:23.139953+00:00",
  "updated_at": "2026-06-25T11:17:23.139953+00:00"
}
```
