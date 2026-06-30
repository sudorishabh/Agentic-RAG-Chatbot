# Qdrant points — Achieving_Green_Steel_Roadmap.pdf

- points (rows upserted): **82**
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
  "chunk_text": "teri THE ENERGY AND RESOURCES INSTITUTE Creating Innovative Solutions for a Sustainable Future\nENERGY TRANSITIONS COMMISSION INDIA\n\n©2022 The Energy and Resources Institute\nAuthors\nWill Hall, Visiting Fellow, TERI (till June 2022)\nSachin Kumar, Senior Fellow, TERI (till Dec 2021)\nSneha Kashyap, Research Associate, TERI (till Mar 2022)\nShruti Dayal, Research Associate, TERI\nReviewer\nMr Girish Sethi, Senior Director, TERI\nDisclaimer\nThis report is an output of a research exercise undertaken by TERI supported by CIFF. It does not represent \nthe views of the supporting organisations or the acknowl\n\n… [+2798 more chars]",
  "content_hash": "7881eca04c3185b68d2bd8cbe983d321d32c7826d01317de66cd16f7f12e46e3",
  "token_count": 808,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `7588344d-0b1b-5f91-a8ba-5adc03800e51`

- vector: dim=3072 · [0.0166, -0.0061, -0.0171, -0.0291, -0.0298, 0.0098, 0.0063, 0.0121, …]

```json
{
  "chunk_id": "7588344d-0b1b-5f91-a8ba-5adc03800e51",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_text": "teri THE ENERGY AND RESOURCES INSTITUTE Creating Innovative Solutions for a Sustainable Future\nENERGY TRANSITIONS COMMISSION INDIA\n\n©2022 The Energy and Resources Institute\nAuthors\nWill Hall, Visiting Fellow, TERI (till June 2022)\nSachin Kumar, Senior Fellow, TERI (till Dec 2021)\nSneha Kashyap, Research Associate, TERI (till Mar 2022)\nShruti Dayal, Research Associate, TERI\nReviewer\nMr Girish Sethi, Senior Director, TERI\nDisclaimer\nThis report is an output of a research exercise undertaken by TERI supported by CIFF. It does not represent \nthe views of the supporting organisations or the acknowl\n\n… [+413 more chars]",
  "content_hash": "bec55602ca0cb4be6fba4c32d04ea99cbe7dd667c3f21665534cb2d638431183",
  "token_count": 251,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `358a363e-e752-5149-a03a-98a2055c2ade`

- vector: dim=3072 · [0.0117, -0.0062, -0.0163, -0.0219, -0.0312, 0.0037, -0.0280, 0.0126, …]

```json
{
  "chunk_id": "358a363e-e752-5149-a03a-98a2055c2ade",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_text": "Suggested Citation\nWill Hall, Sachin Kumar, Sneha Kashyap, Shruti Dayal. 2022. Achieving Green Steel: Roadmap to a net zero \nsteel sector in India. New Delhi: The Energy and Resources Institute (TERI) Energy Transitions Commission (ETC) India is a research platform based in The Energy and \nResources Institute (TERI) in Delhi. ETC India is the Indian chapter of the global Energy \nTransitions Commission, which is chaired by Lord Adair Turner.\nIn 2018, ETC launched its ‘Mission Possible’ report, which detailed decarbonization \npathways for the ‘hard-to-abate’ sectors. This included a sectoral foc\n\n… [+489 more chars]",
  "content_hash": "6a9d37da6255af1ab0ffcffb0e80c2b6c9940faec597f2a8bf5ab7be4a7b79eb",
  "token_count": 266,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `5f049072-f979-58e9-a2ab-b832a7900270`

- vector: dim=3072 · [0.0092, 0.0110, -0.0202, -0.0364, -0.0312, -0.0154, 0.0024, 0.0207, …]

```json
{
  "chunk_id": "5f049072-f979-58e9-a2ab-b832a7900270",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_text": "Learn more at: https://www.teriin.org/energy-transitions\nENERGY TRANSITIONS \nCOMMISSION INDIA We would like to extend our sincere thanks to the Children’s Investment Fund Foundation. \nThis work would not have been possible without their financial support. Their contribution \nwas vital in continuing the conversation on a low carbon transition for the Indian iron and \nsteel sector.  \nWe would also like to acknowledge the support of ETC, which has already done so much to \nadvance the conversation around decarbonising the heavy industry sectors. The comments \nand advice from Lord Adair Turner and \n\n… [+987 more chars]",
  "content_hash": "223c4e0700a8af346c08335a385dfaf4fcff6b081149cc80076e01b0d371e907",
  "token_count": 371,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "chunk_text": "FOREWORD\n\nThe Indian steel sector has been, and will remain an important pillar of India's economic growth and development. Steel demand is estimated to increase more than by twofold 2030-31, spurred by increased spending on infrastructure, automobiles and affordable housing. This increase in demand will provide both challenges and opportunities, including the impact of the sector on the environment. There is a need to ensure that future pathways for growing steel demand are green with minimal environmental impacts.\nThe Energy and Resources Institute (TERI), as part of the Energy Transitions C\n\n… [+2755 more chars]",
  "content_hash": "8af608cd5d3322328d79f5bfc28dfd57462fe2255de444a7809437ec37992cd9",
  "token_count": 561,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `58684db4-2513-5f62-85ad-68415c46e32d`

- vector: dim=3072 · [0.0068, -0.0331, -0.0112, -0.0077, -0.0255, -0.0240, 0.0098, -0.0107, …]

```json
{
  "chunk_id": "58684db4-2513-5f62-85ad-68415c46e32d",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": "The Indian steel sector has been, and will remain an important pillar of India's economic growth and development. Steel demand is estimated to increase more than by twofold 2030-31, spurred by increased spending on infrastructure, automobiles and affordable housing. This increase in demand will provide both challenges and opportunities, including the impact of the sector on the environment. There is a need to ensure that future pathways for growing steel demand are green with minimal environmental impacts.\nThe Energy and Resources Institute (TERI), as part of the Energy Transitions Commission \n\n… [+1298 more chars]",
  "content_hash": "b77a8375acd81c6804b10b01e9ee362e46b75626d8a2f1df289937b09c03f1c4",
  "token_count": 332,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `59f1eb07-3835-5a15-8ec9-0ebe172400e9`

- vector: dim=3072 · [0.0312, -0.0284, -0.0035, -0.0096, -0.0217, -0.0254, 0.0111, 0.0154, …]

```json
{
  "chunk_id": "59f1eb07-3835-5a15-8ec9-0ebe172400e9",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": "In the formulation of this Roadmap, TERI has carried out extensive consultations with various stakeholders in the steel sector - producers, buyers, technology providers, financiers, government bodies and the research community. This comprehensive Roadmap provides an overview of the current state of the steel sector and details a range of possible emissions mitigation strategies. In the near term, implementation of strategies such as maximizing energy efficiency, increasing utilization of scrap, introducing green product standards, creating demand for green steel, setting up pilot demonstration\n\n… [+1074 more chars]",
  "content_hash": "074633530b9e5722721f0783e65ba2fbdacb57b3ad28bb6aecad3a19266b1fca",
  "token_count": 266,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `b17edf1f-3af1-5e56-811f-b2fdd1142fdf`

- vector: dim=3072 · [0.0303, -0.0069, -0.0159, -0.0047, 0.0161, -0.0311, 0.0110, 0.0417, …]

```json
{
  "chunk_id": "b17edf1f-3af1-5e56-811f-b2fdd1142fdf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1. Background",
  "section_type": "toc",
  "chunk_text": "................................................................................................................................ 6\n\n1.1\t\nIndian steel industry..............................................................................................................7\n\n1.2\t Global steel industry............................................................................................................. 9\n\n1.3\t Macro-trends.......................................................................................................................10\n\n1.3.1\t\nDevelopment................................\n\n… [+1033 more chars]",
  "content_hash": "4b8e2487f61432469625ea215819b0e767ea9bb34f6c7bc836c367b4f214cc25",
  "token_count": 141,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 5,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "3. Challenges",
  "section_type": "toc",
  "chunk_text": "3. Challenges\n\n...............................................................................................................................19\n\n3.1\t Competitiveness................................................................................................................. 20\n\n3.2\t Rapid growth required in the near term.................................................................................21\n\n3.3\t Technology availability ....................................................................................................... 22\n\n3.4\t Capital requirements..........................\n\n… [+5879 more chars]",
  "content_hash": "28f7d96175a9ed68f6e214f46458ff33c3891bff09a5981f62c6122e71c9e80f",
  "token_count": 814,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `3da91747-884e-5226-ab20-712e4ebd5abf`

- vector: dim=3072 · [0.0419, -0.0267, -0.0019, -0.0011, -0.0345, -0.0077, -0.0080, 0.0325, …]

```json
{
  "chunk_id": "3da91747-884e-5226-ab20-712e4ebd5abf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3. Challenges",
  "section_type": "toc",
  "chunk_text": "...............................................................................................................................19\n\n3.1\t Competitiveness................................................................................................................. 20\n\n3.2\t Rapid growth required in the near term.................................................................................21\n\n3.3\t Technology availability ....................................................................................................... 22\n\n3.4\t Capital requirements.........................................\n\n… [+2344 more chars]",
  "content_hash": "fdee8829e3ec2c052de2d358654f7633a15f074184c8e5edc393ff12475fd666",
  "token_count": 306,
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
  "chunk_index": 6,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `ebce17fd-eca3-5605-ad95-53a0e5364d46`

- vector: dim=3072 · [0.0325, -0.0260, -0.0097, 0.0218, -0.0154, -0.0200, -0.0180, 0.0374, …]

```json
{
  "chunk_id": "ebce17fd-eca3-5605-ad95-53a0e5364d46",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3. Challenges",
  "section_type": "toc",
  "chunk_text": "................................................................................... 40\n\n5.9\t Implement a carbon border tariff..........................................................................................41\n\n5.10 \tRetire older, polluting facilities............................................................................................ 42\nConclusions\t\n............................................................................................................................... 44\nBibliography\t\n.......................................................................................\n\n… [+3581 more chars]",
  "content_hash": "8f101c2b9bc28fbcaae50abb8e703fbcefce0bce1eb02f85b4a3ab89c53b5464",
  "token_count": 563,
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
  "page_number": 10,
  "page_range": [
    10,
    11
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `e7655ac3-96f6-53f5-88d4-b0c0e5bb12f8`

- vector: dim=3072 · [0.0131, 0.0401, -0.0097, -0.0029, 0.0239, -0.0118, -0.0184, 0.0265, …]

```json
{
  "chunk_id": "e7655ac3-96f6-53f5-88d4-b0c0e5bb12f8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "AI – Artificial Intelligence",
  "section_type": "glossary",
  "chunk_text": "BEE – Bureau of Energy Efficiency \nBF-BOF – Blast Furnace – Basic Oxygen Furnace \nBIS –Bureau of Indian Standards \nCAGR – Compounded Annual Growth Rate \nCBAM – Carbon Border Adjustment Mechanism \nCCUS – Carbon Capture, Use and Storage \nCO2 – Carbon Dioxide DR – Direct Reduction \nEAF – Electric Arc Furnace \nEBITDA – Earnings before Interest, Taxes, Depreciation, and Amortization \nEIF – Electric Induction Furnace \nETS – Emissions Trading Scheme \nFDI – Foreign Direct Investment \nFTA – Free Trade Agreements \nGDP – Gross Domestic Product \nGHG – Greenhouse Gases \nGoI – Government of India \nIEA – Int\n\n… [+426 more chars]",
  "content_hash": "0a9f9000a4dbe37306f66aa3f6a3a8657e8f9e50c813e4a427de0e5732534503",
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
  "chunk_index": 8,
  "page_number": 12,
  "page_range": [
    12,
    12
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "Steel Scrap Recycling",
  "chunk_text": "Steel Scrap Recycling\n\nPolicy, 2019\nTowards a Low Carbon\nSteel Sector (TERI Consultation\nDocument), 2020\nR&D and\nDemonstration plants\nPublic procurement\ntargets\nGreen product\nstandards\nIncrease scrap\nutilisation\nMaximise energy\nefficiency\nNet zero iron and\nsteel sector\nNational Steel\nPolicy, 2017\nGreen steel vision \nCommercial-scale\nfacilities\nRapid scale-up of\nnew low-carbon\ntechnologies\nRetirement of high\nemission capacity\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\nComprehensive\npolicy framework\n\nThe global steel sector is shifting rapidly. More\n\n… [+5002 more chars]",
  "content_hash": "b6c50872d0e0fd40911d3c30146dd42887d612a299697456461f5123325d268e",
  "token_count": 1157,
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
    13,
    18
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `46964e2c-480b-5118-beb9-4475834cdecb`

- vector: dim=3072 · [0.0231, -0.0133, -0.0048, 0.0046, -0.0320, 0.0029, 0.0005, 0.0155, …]

```json
{
  "chunk_id": "46964e2c-480b-5118-beb9-4475834cdecb",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Steel Scrap Recycling",
  "chunk_text": "Policy, 2019\nTowards a Low Carbon\nSteel Sector (TERI Consultation\nDocument), 2020\nR&D and\nDemonstration plants\nPublic procurement\ntargets\nGreen product\nstandards\nIncrease scrap\nutilisation\nMaximise energy\nefficiency\nNet zero iron and\nsteel sector\nNational Steel\nPolicy, 2017\nGreen steel vision \nCommercial-scale\nfacilities\nRapid scale-up of\nnew low-carbon\ntechnologies\nRetirement of high\nemission capacity\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\nComprehensive\npolicy framework",
  "content_hash": "136408137407441f3af7df0d4fdca73e0c7e2190500c063d0b88824b89361d0e",
  "token_count": 130,
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
  "chunk_index": 9,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `d9574072-ac9e-531a-968e-901f37082db4`

- vector: dim=3072 · [0.0204, -0.0125, -0.0063, 0.0017, -0.0156, -0.0169, 0.0154, 0.0255, …]

```json
{
  "chunk_id": "d9574072-ac9e-531a-968e-901f37082db4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Steel Scrap Recycling",
  "chunk_text": ", 2017\nGreen steel vision \nCommercial-scale\nfacilities\nRapid scale-up of\nnew low-carbon\ntechnologies\nRetirement of high\nemission capacity\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\nComprehensive\npolicy framework The global steel sector is shifting rapidly. More than 30% of steel companies (by \nproduction) have net zero targets - up from zero less than 3 years ago - and more \nthan 90% of countries (by GDP) have national level net zero targets. \n•\t\nGovernments are moving fast to create ‘level playing fields’ to protect domestic \nsteel sectors during\n\n… [+1764 more chars]",
  "content_hash": "70e74fe6f8855d947561df2da8b7e02ea26f85da7398da12281571537efb2aaa",
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
  "parent_chunk_id": "62f3149e-c5f3-5e77-9075-d170848bcb51",
  "chunk_index": 10,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `2684799c-bdc3-56e1-b5e0-ee100d5297fc`

- vector: dim=3072 · [0.0298, -0.0377, -0.0006, -0.0075, -0.0323, -0.0177, 0.0012, 0.0174, …]

```json
{
  "chunk_id": "2684799c-bdc3-56e1-b5e0-ee100d5297fc",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Steel Scrap Recycling",
  "chunk_text": "The result will be a globally competitive steel \nsector, supporting India’s ambitions of a self-reliant, net zero major economy.\nEXECUTIVE SUMMARY The steel sector plays an important role in the Indian economy and has been a core pillar of India’s industrial \ndevelopment. As a critical input for various sectors, steel will play a major role in helping India support the \ninfrastructure that facilitates growth, the housing that drives urbanisation, and the machinery and tools \nthat power industrialisation. The sector is expected to experience significant growth in the coming decades \nto satisfy \n\n… [+1773 more chars]",
  "content_hash": "c2c5a56b1b3f7c27edba7331771ddc820c7ad1d8d574f4ccb1f28aa26b84bde4",
  "token_count": 462,
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
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `65fef68a-bd8c-5a56-99ea-ebce6c7b6e68`

- vector: dim=3072 · [0.0169, -0.0418, -0.0156, -0.0107, -0.0352, -0.0243, 0.0130, 0.0334, …]

```json
{
  "chunk_id": "65fef68a-bd8c-5a56-99ea-ebce6c7b6e68",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Steel Scrap Recycling",
  "chunk_text": "This roadmap is a follow-up to the consultation document published by TERI in 2020, “Towards a Low Carbon Steel Sector: An overview of the changing market, technology and policy context for Indian steel”. \nThe updated consultation document is available at our website as Tech Annex . The roadmap builds on this \npreceding work, along with other TERI and ETC publications on steel and hydrogen1, incorporating in the \ndetailed comments and feedback from discussions with international experts, steel sector representatives, \nand government officials.\nINTRODUCTION\n1\t The Potential Role of Hydrogen in \n\n… [+215 more chars]",
  "content_hash": "d575daab9a11a491a970cd2866e83745c58b1b5bd9f8a16b30da3b219dcda98c",
  "token_count": 181,
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
  "page_number": 17,
  "page_range": [
    17,
    18
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "1.1\t Indian steel industry",
  "chunk_text": "1.1\t Indian steel industry\n\nIndia is currently the world’s second-largest steel producer, and second-largest steel consumer (WSA, \n2020a). The steel industry in India is relatively heterogeneous compared to other countries, with a wide \nrange of different sized facilities in the primary and secondary steelmaking sectors. There are also several \ndifferent technologies currently being used, including the Blast Furnace – Basic Oxygen Furnace (BF-BOF), \ncoal-based Direct Reduction (DR), gas-based DR, Electric Induction Furnace (EIF) and Electric Arc Furnace \n(EAF). BOF technology dominates a growi\n\n… [+4002 more chars]",
  "content_hash": "1a4fd49e82f20e466e03c1f38a3308f96971fcf8ea3b764493d7bc801a9019ee",
  "token_count": 1053,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `69b7c667-73cc-519e-9c11-0c69e6548f97`

- vector: dim=3072 · [0.0296, 0.0127, -0.0107, -0.0065, -0.0082, -0.0145, 0.0012, -0.0171, …]

```json
{
  "chunk_id": "69b7c667-73cc-519e-9c11-0c69e6548f97",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.1\t Indian steel industry",
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
  "parent_chunk_id": "6735efd5-1ad3-5cb6-9ec6-f2a61992b883",
  "chunk_index": 13,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `aea94858-15b5-5a41-9fd2-098f1d473790`

- vector: dim=3072 · [0.0071, -0.0032, 0.0020, -0.0023, -0.0253, -0.0143, -0.0167, 0.0154, …]

```json
{
  "chunk_id": "aea94858-15b5-5a41-9fd2-098f1d473790",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.1\t Indian steel industry",
  "chunk_text": "Figure 1: Route-wise crude steel production share, 2020-21\nSource: (MoS, 2021a) \nBackground\n45%\n28%\n27%\nBOF\nEAF\nEIF Figure 2: Historical steel production and use\nSource: (MoS, 2021a; 2021b) \nAs with any industrializing economy, the steel sector is of vital importance to India, contributing around \n2% to the country’s GDP and employing around 2.5 million people in the steel and related sectors (MoS, \n2020a). Crude steel production in India grew from 89 Mt in 2014-15 to 111 Mt in 2019-20. It fell to just \nbelow 100 Mt in 2020-212 following the Covid-19 pandemic. However, the cumulative productio\n\n… [+1342 more chars]",
  "content_hash": "2483d90373a7c23773859596463fe1eb3f8df268feb242938f34364b6e90d592",
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
  "parent_chunk_id": "6735efd5-1ad3-5cb6-9ec6-f2a61992b883",
  "chunk_index": 14,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `687441d7-1545-5fd7-909d-c355cda58034`

- vector: dim=3072 · [0.0069, -0.0110, -0.0015, 0.0188, -0.0210, 0.0053, -0.0172, 0.0093, …]

```json
{
  "chunk_id": "687441d7-1545-5fd7-909d-c355cda58034",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.1\t Indian steel industry",
  "chunk_text": "In 2017, the Ministry of Steel (MoS) launched the National Steel Policy (NSP), which included an aim to increase India’s steelmaking capacity to 300 Mt by 2030. This policy also encompasses targets to reduce \nenergy consumption per tonne of steel, through adopting the latest energy efficiency measures. To support \nthe adoption of energy efficiency measures across a number of sectors, the GoI has developed the Perform, \nAchieve and Trade (PAT) scheme, delivered through the Bureau of Energy Efficiency (BEE). The steel sector \nhas been covered under the PAT scheme since its inception in 2012. Unt\n\n… [+478 more chars]",
  "content_hash": "4e16fcd926d5bec7d8a315d9491ce520f40154bffb7efacdec0433f0303f70ee",
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
  "parent_chunk_id": "6735efd5-1ad3-5cb6-9ec6-f2a61992b883",
  "chunk_index": 15,
  "page_number": 20,
  "page_range": [
    20,
    21
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `03ce0500-0a6b-5cc2-8fca-cd515588433e`

- vector: dim=3072 · [0.0206, 0.0050, -0.0136, 0.0088, -0.0145, -0.0207, 0.0012, -0.0142, …]

```json
{
  "chunk_id": "03ce0500-0a6b-5cc2-8fca-cd515588433e",
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
  "chunk_index": 16,
  "page_number": 21,
  "page_range": [
    21,
    22
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `241d7bd7-74c0-5722-a48b-1669da1e1bb0`

- vector: dim=3072 · [-0.0012, -0.0105, -0.0125, -0.0015, 0.0073, -0.0022, -0.0049, -0.0181, …]

```json
{
  "chunk_id": "241d7bd7-74c0-5722-a48b-1669da1e1bb0",
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
  "chunk_index": 17,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `151361de-b436-59d5-87d1-ececede0c345`

- vector: dim=3072 · [0.0079, -0.0025, -0.0090, -0.0030, 0.0165, -0.0154, 0.0064, -0.0002, …]

```json
{
  "chunk_id": "151361de-b436-59d5-87d1-ececede0c345",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.1\t Development",
  "chunk_text": "Steel is a material of vital importance to countries as they develop, a key input across construction, \ninfrastructure, and manufacturing sectors. As countries reach a certain level of economic development, \nsteel demand starts to saturate, as most major infrastructure is built and future steel demand can largely \nbe satisfied by recycling, or is replaced with alternative materials. As such, we are likely to see emerging \neconomies like India become the major centres of steel demand growth in the coming decades, as demand \nin other major economies, such as China, stabilises.\n\nForecasting deman\n\n… [+2048 more chars]",
  "content_hash": "9a0e3d9b3a59b7a79595e9cf9547b495e6eba7b7b5a5cc7ccff6219ad36b7f0b",
  "token_count": 586,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 18,
  "page_number": 22,
  "page_range": [
    22,
    24
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "1.3.2\t Digitalisation",
  "chunk_text": "1.3.2\t Digitalisation\n\nAs with other sectors in the economy, the iron and steel sector is set to realise significant benefits from \nthe digitalisation of production processes and supply chains. This is likely to have a step-change impact in \noperational efficiencies. It will be important to consider digitalisation alongside other major trends, such \nas decarbonisation, to better understand the net impact of such major technological shifts.\nDigitalisation of industry is a wide-ranging area, often covered under topics such as Industry 4.0 (or 4th \nIndustrial Revolution), Internet of Things (IoT)\n\n… [+2695 more chars]",
  "content_hash": "e1edea3eca067c8a6674323d025df52fb0ca4b3f887c97746bed91c7e304da98",
  "token_count": 644,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `106c1561-5c4a-5559-a953-315cedd22e4b`

- vector: dim=3072 · [0.0250, 0.0318, -0.0173, 0.0093, 0.0063, 0.0102, 0.0086, -0.0002, …]

```json
{
  "chunk_id": "106c1561-5c4a-5559-a953-315cedd22e4b",
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
  "parent_chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "chunk_index": 19,
  "page_number": 24,
  "page_range": [
    24,
    24
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `b8a4fdc1-b3ea-596f-981f-5a4cab66dfce`

- vector: dim=3072 · [0.0171, 0.0062, -0.0114, 0.0059, -0.0085, 0.0040, 0.0055, -0.0122, …]

```json
{
  "chunk_id": "b8a4fdc1-b3ea-596f-981f-5a4cab66dfce",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.2\t Digitalisation",
  "chunk_text": "Their Kalinganagar plant has \ndeveloped an expert team of analytics specialists, including data scientists and translators. The net impact of digitalisation on the Indian iron and steel sector is uncertain. It represents a significant \nopportunity for Indian steelmakers as build new capacity in the coming decades, able to take advantage of \nthe latest technologies, unavailable to other countries when they were expanding their steel production. \nIndia has shown a proficiency for rapid adoption of new technologies in other sectors, with a relatively \nyoung and technically literate workforce bett\n\n… [+838 more chars]",
  "content_hash": "b277f656d9184414c693d95cc7fc5a2ed303ec9bdca930366fa87ed31bf54230",
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
  "parent_chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "chunk_index": 20,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "1.3.3\t Decarbonisation",
  "chunk_text": "1.3.3\t Decarbonisation\n\nThe third macro-trend, and arguably \nthe trend driving the most significant \ndisruption in the iron and steel \nsector, is the growing imperative for \ndecarbonisation. The iron and steel \nsector is currently both highly energy \nand emissions-intensive, accounting \nfor 8% of global final energy use and \n7% of global direct energy-related \nCO2 emissions (including industrial \nprocess emissions) (IEA, 2020). As \nprogress to decarbonize the power \nand transport sectors accelerates, \nwe are starting to see greater focus \non the heavy industry sectors, \nsuch as iron & steel, c\n\n… [+2658 more chars]",
  "content_hash": "5f428cbf5919475e1783b9389bc71b17d826e20f3aadb866aa4f4265d2a73474",
  "token_count": 948,
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
    27
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `2016fa91-aa35-5177-a341-2634b8dfbac8`

- vector: dim=3072 · [0.0135, -0.0125, -0.0182, 0.0040, -0.0275, -0.0259, 0.0060, 0.0039, …]

```json
{
  "chunk_id": "2016fa91-aa35-5177-a341-2634b8dfbac8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3\t Decarbonisation",
  "chunk_text": "The third macro-trend, and arguably \nthe trend driving the most significant \ndisruption in the iron and steel \nsector, is the growing imperative for \ndecarbonisation. The iron and steel \nsector is currently both highly energy \nand emissions-intensive, accounting \nfor 8% of global final energy use and \n7% of global direct energy-related \nCO2 emissions (including industrial \nprocess emissions) (IEA, 2020). As \nprogress to decarbonize the power \nand transport sectors accelerates, \nwe are starting to see greater focus \non the heavy industry sectors, \nsuch as iron & steel, cement and \nchemicals.\nIn\n\n… [+971 more chars]",
  "content_hash": "9fea8b4612a1b5745205b1b15998ebf47a0a797704ea4e427d5eebc96063f9f8",
  "token_count": 450,
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
  "chunk_index": 21,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `e69fa337-3862-5a53-a466-66d5f6b75657`

- vector: dim=3072 · [0.0322, 0.0225, -0.0212, -0.0018, -0.0135, -0.0173, 0.0140, 0.0392, …]

```json
{
  "chunk_id": "e69fa337-3862-5a53-a466-66d5f6b75657",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3\t Decarbonisation",
  "chunk_text": "TBC\n‘25\n‘25\n‘26\n‘28\n‘30\n‘30\n‘21\n‘22\n‘26\n‘24\nTBC\n‘21\nTBC\n2021\nTBC\nTBC\nTBC\nTBC\nTBC 2030\n2017\n2024\n2025\n2027\n2025\nTBC\nTBC\nTBC\nTBC\nTBC\n\n| TOTAL STEEL PROJECTS PRODUCED (MN COMPANY (WITH LAUNCH YEAR) TONNES P.A.)* 115 57 0 Project scale * Source: World Steel in Full scale Pilots Demonstration Plant R&D partnership Figures 2020 |  |  |  |\n| --- | --- | --- | --- |\n|  |  |  | Baowu TBC TBC |\n|  |  |  | Arcelor Mittal ‘25 ‘25 ‘26 ‘28 ‘30 ‘30 TBC ‘21 ‘22 ‘26 ‘24 ‘21 |\n|  |  |  | HBIS 2021 TBC |\n|  |  |  | Nippon Steel TBC |\n|  |  |  | POSCO TBC TBC TBC TBC TBC |\n|  |  |  | Tata Steel 2024 2030 2017 |\n|\n\n… [+112 more chars]",
  "content_hash": "9a0c9242998c2232d5e7918a54980e23bde91a671f5d1640bffea1cf4a2e8ab5",
  "token_count": 340,
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
  "chunk_index": 22,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `4731a355-4f0a-5cae-93eb-9d68ce161448`

- vector: dim=3072 · [0.0252, -0.0049, -0.0062, 0.0182, 0.0083, -0.0303, 0.0097, 0.0107, …]

```json
{
  "chunk_id": "4731a355-4f0a-5cae-93eb-9d68ce161448",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3\t Decarbonisation",
  "chunk_text": "7 |\n|  |  |  | JFE TBC |\n|  |  |  | US Steel TBC |\n|  |  |  | Thyssen Krupp 2025 2025 2027 |\n|  |  |  | Tenaris TBC | For further emissions reduction, the introduction of new, low carbon technologies will be required, such \nas the use of low carbon hydrogen or carbon, capture, utilisation and storage (CCUS). Initially, these \nnew processes will increase the costs of steel production, and will require the introduction of supportive \npolicies by the government to help the industry through the transition, as we have seen in other sectors, \nsuch as power and transport.\nWhilst it is true that some \n\n… [+547 more chars]",
  "content_hash": "1f7322e06bb633fb264ca120828945e30ca1df1d9893b25f9a07ac94cfcc2a3e",
  "token_count": 267,
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
  "page_number": 26,
  "page_range": [
    26,
    27
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `004f77c3-23e1-5d46-b4c5-5a53460f780f`

- vector: dim=3072 · [0.0148, 0.0129, -0.0050, -0.0187, 0.0257, -0.0245, 0.0102, 0.0068, …]

```json
{
  "chunk_id": "004f77c3-23e1-5d46-b4c5-5a53460f780f",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.1\t Overview",
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
  "chunk_index": 24,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `0c7a15af-0cc7-5d8f-a638-fcf3fbf3e115`

- vector: dim=3072 · [0.0162, 0.0185, -0.0120, 0.0040, 0.0219, -0.0270, -0.0229, -0.0199, …]

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
  "chunk_index": 25,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `9820d55d-49ab-5d0c-89a5-b39eaa5dfa03`

- vector: dim=3072 · [0.0153, 0.0209, 0.0007, 0.0031, -0.0348, -0.0215, 0.0020, -0.0202, …]

```json
{
  "chunk_id": "9820d55d-49ab-5d0c-89a5-b39eaa5dfa03",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.3\t Rapid growth",
  "chunk_text": "Over 80% of India’s iron reserves are in India’s eastern states (Odisha, Jharkhand, West Bengal, \nChhattisgarh and North Andhra Pradesh) (see Figure 8). These states also have access to logistics \ninfrastructure including ports, inland waterways and slurry pipelines (MoS, 2019b). The top states \nin terms of steel production include Odisha (25 Mt), Jharkhand (20 Mt), Chhattisgarh (19 Mt), \nKarnataka (15 Mt), Gujarat (13 Mt) and Maharashtra (12 Mt) (JPC, 2020).\nThe Ministry of Steel, under Mission Purvodaya, aims to support the development of an integrated steel hub \nin eastern India to improve \n\n… [+1118 more chars]",
  "content_hash": "943efae3f72c7b71e2462e2825b79275144c0757970c9f775c200e532378a748",
  "token_count": 396,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 26,
  "page_number": 28,
  "page_range": [
    28,
    29
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `9f95be06-4b5e-5bd4-90c0-e7e0a15f8708`

- vector: dim=3072 · [0.0129, -0.0074, -0.0022, 0.0025, -0.0204, -0.0254, -0.0184, -0.0110, …]

```json
{
  "chunk_id": "9f95be06-4b5e-5bd4-90c0-e7e0a15f8708",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "2.4 Employment",
  "chunk_text": "The Indian steel sector currently employs approximately 2.5 million people throughout the supply chain \n(MoS, 2020a). This is estimated to increase to around 3.5 million by 2030, depending on the degree of \nautomation (NSP, 2017). The highest-skilled jobs include engineers and metallurgists, which are vital for \nthe efficient operation of the plants and timely adoption of new technologies. \nHowever, the sector is currently facing a significant skills shortage, which is being exacerbated by skilled \ngraduates moving away from the manufacturing sectors to the service sectors. This is being drive\n\n… [+1407 more chars]",
  "content_hash": "4654d2a0885fa31f2613b2cb4df6b9c92e640612eee03c55d70ba63f5340b225",
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
  "chunk_index": 27,
  "page_number": 30,
  "page_range": [
    30,
    32
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "3.1\t Competitiveness",
  "chunk_text": "3.1\t Competitiveness\n\nWhilst there have been significant improvements in the operational efficiencies of steel production in \nIndia in recent years, on average, Indian steel producers are still facing costs around 5-10% higher as \ncompared to the global average. In the context of a global glut in steel supply, this places Indian steel \nproducers in a difficult position, reducing profits for reinvestment and limiting export markets. The cost \npremium is driven by a number of factors (see Table 1), with the main contributors being costs of finance \n(approximately 12% versus 3-5% across the Europ\n\n… [+2889 more chars]",
  "content_hash": "5a7fcd506773ea443981fd29edde7dc7310e553ca979c95441fe88d20d0bf55f",
  "token_count": 828,
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
    33
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `acdddbc7-8827-59f4-84c0-a5f16c70a126`

- vector: dim=3072 · [0.0052, 0.0135, -0.0020, 0.0159, -0.0183, -0.0261, -0.0160, -0.0023, …]

```json
{
  "chunk_id": "acdddbc7-8827-59f4-84c0-a5f16c70a126",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.1\t Competitiveness",
  "chunk_text": "Whilst there have been significant improvements in the operational efficiencies of steel production in \nIndia in recent years, on average, Indian steel producers are still facing costs around 5-10% higher as \ncompared to the global average. In the context of a global glut in steel supply, this places Indian steel \nproducers in a difficult position, reducing profits for reinvestment and limiting export markets. The cost \npremium is driven by a number of factors (see Table 1), with the main contributors being costs of finance \n(approximately 12% versus 3-5% across the European Union) and the cos\n\n… [+1340 more chars]",
  "content_hash": "947a3068f61bccd6f3e50376a4485264bf785989383d34b8109f2e7cc84927ff",
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
  "parent_chunk_id": "a9ef31a8-c2b3-5729-8961-e3ed32bb0616",
  "chunk_index": 28,
  "page_number": 32,
  "page_range": [
    32,
    32
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `53440e1e-175f-5063-a8af-71aae63bac96`

- vector: dim=3072 · [-0.0100, 0.0241, -0.0054, 0.0035, -0.0120, -0.0336, -0.0162, 0.0129, …]

```json
{
  "chunk_id": "53440e1e-175f-5063-a8af-71aae63bac96",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.1\t Competitiveness",
  "chunk_text": "Table 1: Cost premium for steel production in India\nTaxes and duties on iron ore\n8-12\nFinance\n30-35\nTotal cost disadvantage\n80-100\nSource: (Niti Aayog, 2016)\nChallenges | too early to assess the effectiveness of this programme. |  |\n| --- | --- |\n| Table 1: Cost premium for steel production in india |  |\n| Item | Cost ($/ton) |\n| Logistics and infrastructure | 25-30 |\n| Power | 8-12 |\n| import duty on coal | 5-7 |\n| GST Compensation Cess | 2-4 |\n| Taxes and duties on iron ore | 8-12 |\n| Finance | 30-35 |\n| Total cost disadvantage | 80-100 |\n\nTata Steel Ltd.\nSteel Authority of India Ltd.\nJindal\n\n… [+1094 more chars]",
  "content_hash": "72a503eaaabb328a99b8e569cb97f50a2fa0303d9e909d27122cf03abd3d8a96",
  "token_count": 427,
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
  "chunk_index": 29,
  "page_number": 32,
  "page_range": [
    32,
    33
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `580b0363-c934-5ea2-876f-b7615995eaae`

- vector: dim=3072 · [-0.0134, 0.0015, -0.0046, -0.0026, -0.0147, -0.0255, 0.0000, -0.0103, …]

```json
{
  "chunk_id": "580b0363-c934-5ea2-876f-b7615995eaae",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.2\t Rapid growth required in the near term",
  "chunk_text": "As India’s economy grows, its steel demand will grow substantially. India currently has the world’s second \nlargest population and is expected to be the largest by 2023 (OECD, 2018). By 2030, in our Baseline \nscenario (see Figure 10), we expect steel demand to more than double versus today, increasing the steel \nuse per capita to 150 kg. Under the Resource efficiency4 scenario, steel use per capita is similar over this \ntime frame, given the time taken for resource efficiency measures to have a substantial impact.\nBy 2050, in the Baseline scenario, we expect steel demand per capita to nearly q\n\n… [+988 more chars]",
  "content_hash": "c0b39a2c29995ba128d00f17b5b0036207baa632e5953789db90944755b978fe",
  "token_count": 350,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 30,
  "page_number": 33,
  "page_range": [
    33,
    34
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `452f5453-f766-5889-8b03-ea64ba4fadae`

- vector: dim=3072 · [0.0238, -0.0098, -0.0105, 0.0102, -0.0317, -0.0240, -0.0087, 0.0038, …]

```json
{
  "chunk_id": "452f5453-f766-5889-8b03-ea64ba4fadae",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3\t Technology availability",
  "chunk_text": "To achieve deep decarbonisation of the iron and steel sector, new technologies will be required – \nin particular for the replacement of conventional primary production processes with low emissions \nalternatives. There are several emerging low emissions technologies to produce steel from iron ore. They \nbroadly fall into three categories:\n•\t\nCarbon capture, utilisation, and storage (CCUS)\n•\t\nThe use of low carbon hydrogen to replace fossil fuels\n•\t\nDirect electrification through electrolysis of iron ore\nEach of these technologies differ in their suitability to the Indian context, based on their\n\n… [+288 more chars]",
  "content_hash": "cdaf2910a4daed9b4fd32985b48c78147022ab79377d168924ad630fbf14e60c",
  "token_count": 206,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 31,
  "page_number": 34,
  "page_range": [
    34,
    34
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "Technology TRL",
  "chunk_text": "Technology TRL\n\nEmissions reduction potential\nSuitability for deep decarbonisation in \nIndia\nCarbon Capture, Utilisation, and Storage \nBF-BOF \nwith CCUS\n5\nPossibility \nto \nreduce \nCO2 \nby \napproximately 60%. Although higher \ncapture rates are possible, costs \nincrease substantially due to multiple \nCO2 sources (IEA, 2017).\nLimited cost-effective CO2 capture will \nrestrict the use of this technology for deep \ndecarbonisation, although could play an \nimportant role in retrofitting existing plants.\nCoal based \nDRI with \nCCUS\n4\nThere have been no comprehensive \nstudies on applying CCUS technology \n\n… [+6274 more chars]",
  "content_hash": "5577bd98150294625bf3b54f9e5bfb9b9f980a405aee280b21aa27c60c4c9d91",
  "token_count": 1791,
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
    35,
    36
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `345c8e44-03e4-5c99-972b-fe3fde487ad1`

- vector: dim=3072 · [0.0099, 0.0224, -0.0139, 0.0133, -0.0148, -0.0145, -0.0109, 0.0057, …]

```json
{
  "chunk_id": "345c8e44-03e4-5c99-972b-fe3fde487ad1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Technology TRL",
  "chunk_text": "Emissions reduction potential\nSuitability for deep decarbonisation in \nIndia\nCarbon Capture, Utilisation, and Storage \nBF-BOF \nwith CCUS\n5\nPossibility \nto \nreduce \nCO2 \nby \napproximately 60%. Although higher \ncapture rates are possible, costs \nincrease substantially due to multiple \nCO2 sources (IEA, 2017).\nLimited cost-effective CO2 capture will \nrestrict the use of this technology for deep \ndecarbonisation, although could play an \nimportant role in retrofitting existing plants.\nCoal based \nDRI with \nCCUS\n4\nThere have been no comprehensive \nstudies on applying CCUS technology \nto coal-based r\n\n… [+1198 more chars]",
  "content_hash": "0645536f7a69a43fe2c2bb8dd7484f3a8f11a5266b6f454a4888804ee206d5b6",
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
  "parent_chunk_id": "192c6065-5cf1-5ec9-8d3c-5ec092881b0c",
  "chunk_index": 32,
  "page_number": 35,
  "page_range": [
    35,
    35
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `4572236d-ca35-52ee-9063-3648b85c059c`

- vector: dim=3072 · [0.0087, 0.0132, -0.0157, 0.0142, -0.0257, -0.0062, 0.0044, -0.0006, …]

```json
{
  "chunk_id": "4572236d-ca35-52ee-9063-3648b85c059c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Technology TRL",
  "chunk_text": "The CAPEX \nand OPEX savings make such a technology \nattractive, although the potential of CCUS is \nuncertain.\nHydrogen \nBF with H2 \nblending\n7 It is expected that H2 would only be \nable to replace part of the injected \ncoal, resulting in maximum 20% \nemissions reduction. \nThe limited emissions reduction means \nthat H2 injection into BFs can only ever \nbe a transition technology to deeper \ndecarbonisation. \nH2 DRI \n7\nEmissions \nreduction \npotential \ndepends on the share of H2 and \nwhether the H2 is from low carbon \nsources. Assuming 100% green H2, \nemissions reduction can be >90%, \nwith residua\n\n… [+911 more chars]",
  "content_hash": "7729445d918dc5e0043e2ffcd6acb3e5d33d483c87c2f77f6005b2a84b8b91cc",
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
  "parent_chunk_id": "192c6065-5cf1-5ec9-8d3c-5ec092881b0c",
  "chunk_index": 33,
  "page_number": 35,
  "page_range": [
    35,
    35
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `0ec0cc77-7e2b-5815-b705-fd2551d61ef1`

- vector: dim=3072 · [0.0215, 0.0090, -0.0172, 0.0078, -0.0363, -0.0177, 0.0070, 0.0012, …]

```json
{
  "chunk_id": "0ec0cc77-7e2b-5815-b705-fd2551d61ef1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Technology TRL",
  "chunk_text": "Current research projects are still at \nearly stages with uncertain timeline for \ncommercial scale. (Siderwin and Boston \nMetal)\nTable 2: Low emissions steelmaking technologies | Table 2: Low emissions steelmaking technologies |  |  |  |\n| --- | --- | --- | --- |\n| Technology | TRL | Emissions reduction potential | Suitability for deep decarbonisation in |\n|  |  |  | India |\n|  | Carbon Capture, Utilisation, and Storage |  |  |\n| BF-BOF | 5 | by Possibility to reduce CO2 | Limited cost-effective capture will CO2 |\n| with CCUS |  | approximately 60%. Although higher | restrict the use of this t\n\n… [+1704 more chars]",
  "content_hash": "b5a065a77ccaf66fc070dbd4a1856925f9ece5200e99ba14d9989307c62981c3",
  "token_count": 587,
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
  "chunk_index": 34,
  "page_number": 35,
  "page_range": [
    35,
    35
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `5a971ca9-e29a-5685-a930-76fc9e31b300`

- vector: dim=3072 · [0.0300, 0.0053, -0.0191, 0.0006, -0.0179, -0.0055, 0.0093, 0.0031, …]

```json
{
  "chunk_id": "5a971ca9-e29a-5685-a930-76fc9e31b300",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Technology TRL",
  "chunk_text": "| and OPEx savings make such a technology |\n|  |  | emissions by 80% (Tata Steel, 2020). | attractive, although the potential of CCUS is |\n|  |  |  | uncertain. |\n| Hydrogen |  |  |  | | BF with H2 | 7 | it is expected that H2 would only be | The limited emissions reduction means |\n| blending |  | able to replace part of the injected | injection into BFs can only ever that H2 |\n|  |  | coal, resulting in maximum 20% | be a transition technology to deeper |\n|  |  | emissions reduction. | decarbonisation. |\n| H2 DRi | 7 | Emissions reduction potential | Low cost renewable electricity provides a \n\n… [+1146 more chars]",
  "content_hash": "039baf843fdaeb6e51ed2b1ca7026867f9c0007f22b52cdece087b742aa6b76e",
  "token_count": 527,
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
  "chunk_index": 35,
  "page_number": 35,
  "page_range": [
    35,
    36
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `c578deaa-fdae-5ac6-8324-76e9f58c87a4`

- vector: dim=3072 · [0.0133, 0.0166, -0.0059, -0.0002, -0.0178, -0.0287, 0.0190, 0.0128, …]

```json
{
  "chunk_id": "c578deaa-fdae-5ac6-8324-76e9f58c87a4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.4 Capital requirements",
  "chunk_text": "The transition towards a net-zero steel sector will be highly capital-intensive, as new steel facilities will \nneed to be built, alongside supporting infrastructure (such as electricity, hydrogen and CCUS networks). \nThe Indian steel sector relies heavily on FDI, which was estimated to be over $14 billion between April \n2000 and June 2020 (IBEF, 2021), representing 2.01% of total FDI (DIPP, 2020). This funding is increasingly \nlooking to align itself with a net zero target, meaning only near zero emission steelmaking technologies \nwill attract finance in future (see Glasgow Financial Alliance \n\n… [+583 more chars]",
  "content_hash": "1dcb02da3ac81aba939b57c19a35c268c9e69ab3e85223b4fa2f0304a9118604",
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
  "chunk_index": 36,
  "page_number": 36,
  "page_range": [
    36,
    37
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "Transition Pathway — 4.1 Structure of Indian steel assets\n\nBefore exploring future pathways for the Indian steel sector, it is worth outlining the structure of existing \nassets. Principally, we are concerned with (a) the technological make-up and (b) lifetime of the existing \nassets, as these two factors will be most influential in setting the future direction of the Indian steel sector.\nThe current make-up of India’s iron and steelmaking facilities shows an accelerating trend towards larger, \nintegrated steel plants using blast furnace, basic oxygen furnace and electric arc furnace technologi\n\n… [+2758 more chars]",
  "content_hash": "5281be7e262b14ab5e01700ee68bfca971fab63f6050a7dc6c0bca103bdf9499",
  "token_count": 711,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `922301fa-18fd-585c-97f4-5dbf7f040360`

- vector: dim=3072 · [0.0185, 0.0004, -0.0118, 0.0028, -0.0200, -0.0180, -0.0225, 0.0060, …]

```json
{
  "chunk_id": "922301fa-18fd-585c-97f4-5dbf7f040360",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "Before exploring future pathways for the Indian steel sector, it is worth outlining the structure of existing \nassets. Principally, we are concerned with (a) the technological make-up and (b) lifetime of the existing \nassets, as these two factors will be most influential in setting the future direction of the Indian steel sector.\nThe current make-up of India’s iron and steelmaking facilities shows an accelerating trend towards larger, \nintegrated steel plants using blast furnace, basic oxygen furnace and electric arc furnace technologies, as \nper global trends. There is still a relatively sign\n\n… [+1030 more chars]",
  "content_hash": "8705bca16e4382c9e03193b80793008678ec985e9e248dae6d9128426b543e26",
  "token_count": 319,
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
  "chunk_index": 37,
  "page_number": 38,
  "page_range": [
    38,
    38
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `cb53d3e7-4a87-5102-aab3-7b787a9cd004`

- vector: dim=3072 · [-0.0128, 0.0097, -0.0129, -0.0164, -0.0383, -0.0154, -0.0338, 0.0190, …]

```json
{
  "chunk_id": "cb53d3e7-4a87-5102-aab3-7b787a9cd004",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "India has seen a relatively steady growth in blast \nfurnace technology since the 1960s, with a marked acceleration in deployment since 2000 from which \npoint two-thirds of blast furnace capacity was added. \nFigure 12: Ironmaking and steelmaking production routes, Mt Based on the largest assessment of blast furnace capacity done to date (Vogl, Olsson & Nykvist, 2021), we \ncan understand in more detail about the lifetime of this technology and timescales for reinvestment. The \naverage blast furnace can last around 45 to 50 years, with between 2 and 3 relining campaigns occurring \nover that timef\n\n… [+1334 more chars]",
  "content_hash": "7c3157136d4257c050f37bfbdf74edfeb4093b62cc3099dfd890fc2d88a93e91",
  "token_count": 435,
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
  "chunk_index": 38,
  "page_number": 39,
  "page_range": [
    39,
    40
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "chunk_text": "4.2 Technology option assessment\n\nAfter understanding the existing technology make-up of the Indian steel sector, it is necessary to \nunderstand how future lower emission technologies could compete, in terms of both costs, as well as \nbroader suitability (resource availability, import / export impacts). TERI and ETC have undertaken detailed \ntechnology assessments for the Indian and global steel sector,5 which will inform the conclusions in this \nsection. \nBased on this assessment, we observe that the costs of steel production from the main conventional \nroutes in India range from around $300/\n\n… [+6128 more chars]",
  "content_hash": "cad97d2c9e40005745414a12bd35ef64a5bbb36efac9d9b1950674d35650a916",
  "token_count": 1618,
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
    43
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `fbba2519-b45b-50c7-8297-7a057fbf1cfe`

- vector: dim=3072 · [0.0010, -0.0225, -0.0220, -0.0033, -0.0267, -0.0293, -0.0067, 0.0142, …]

```json
{
  "chunk_id": "fbba2519-b45b-50c7-8297-7a057fbf1cfe",
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
  "chunk_index": 39,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `3eddf45e-793a-59d4-a15d-3baedfe3dcc8`

- vector: dim=3072 · [0.0152, -0.0260, -0.0154, 0.0238, -0.0329, -0.0343, -0.0056, 0.0000, …]

```json
{
  "chunk_id": "3eddf45e-793a-59d4-a15d-3baedfe3dcc8",
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
  "chunk_index": 40,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `f59ea535-f03f-55f6-b659-02ef03481ecf`

- vector: dim=3072 · [0.0069, -0.0162, -0.0117, 0.0214, -0.0285, -0.0308, -0.0219, 0.0273, …]

```json
{
  "chunk_id": "f59ea535-f03f-55f6-b659-02ef03481ecf",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "Figure 16: Costs of steel production by route6 \n Source: TERI analysis based on (IEA, 2019) and (MPP, 2021) 6\t BF-BOF = Blast Furnace – Basic Oxygen Furnace, Coal DR-EAF = Coal-based Direct Reduction – Electric Arc Furnace, NG DR-EAF = Natural gas-based \nDirect Reduction – Electric Arc Furnace, SR-BOF CCUS = Smelting Reduction – Basic Oxygen Furnace with Carbon Capture, Usage and or Storage, H2 \nDR-EAF = Hydrogen-based Direct Reduction – Electric Arc Furnace, MOE-EAF = Molten Oxide Electrolysis – Electric Arc Furnace. \n0\n100\n200\n300\n400\n500\n600\nBF-BOF\nCoal DR-EAF\nNG DR-EAF\nSR-BOF\nCCUS\nH2 DR-EA\n\n… [+81 more chars]",
  "content_hash": "1e3e5a4da71a3d513d54799bf7a50274780993ea95116afa55d47e38a089933d",
  "token_count": 219,
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
  "chunk_index": 41,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `7639440e-35ef-5f4e-80e9-7b798dc70567`

- vector: dim=3072 · [0.0299, -0.0159, -0.0114, 0.0258, -0.0378, -0.0473, 0.0068, 0.0165, …]

```json
{
  "chunk_id": "7639440e-35ef-5f4e-80e9-7b798dc70567",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "600\nBF-BOF\nCoal DR-EAF\nNG DR-EAF\nSR-BOF\nCCUS\nH2 DR-EAF\nMOE-EAF\nCost of production ($/t)\nCAPEX\nFixed OPEX\nFuel\nRaw materials\nCCUS\nRange Costs of production from the hydrogen direct reduction route are largely similar to those in the natural \ngas direct reduction route, with the main difference being the cost of hydrogen as a fuel versus natural \ngas. In our cost analysis, we assume that hydrogen is purchased from a separate producer by the steel \nplant, as opposed to having the capital costs of the electrolysers included in the capital costs of the steel \nplant. Today, costs of electrolytic hyd\n\n… [+1558 more chars]",
  "content_hash": "ca8f39201e8d9cf289472a9f8954a260d8afdc880de4b6c386cacdaa2fbf54cd",
  "token_count": 508,
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
  "chunk_index": 42,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `478beb0a-08a6-5fbf-8374-5fa74ac5679a`

- vector: dim=3072 · [0.0167, -0.0116, -0.0128, 0.0189, -0.0392, -0.0563, 0.0051, 0.0249, …]

```json
{
  "chunk_id": "478beb0a-08a6-5fbf-8374-5fa74ac5679a",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "reduction with CCUS \nFigure 17: Costs of production - H2-DR vs SR-BOF with CCUS\n Source: TERI analysis based on (IEA, 2019; Hall, Spencer, & Kumar, 2020; BNEF, 2020) Note: tCO2 refers to the cost of carbon capture and storage, not to carbon price.\n\n|  | TERI | TERI |  |\n| --- | --- | --- | --- |\n|  | 2050 | 2030 |  |\n| 700 |  |  |  |\n| 600 |  |  |  |\n| 500 |  |  | $80/tCO2 |\n|  |  |  | Cost of CCS |\n| 400 |  |  |  |\n|  |  |  | $20/tCO2 |\n| 300 |  |  |  |\n| 200 |  |  |  |\n| 100 |  |  |  |\n\npilot facility, being taken forward by Tata Steel Europe in the Netherlands has now switched to developing\n\n… [+791 more chars]",
  "content_hash": "ae1229ce611ed50bdc44862d1ba48bd197532ebbb1fad97bf3916b367326993d",
  "token_count": 399,
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
  "chunk_index": 43,
  "page_number": 42,
  "page_range": [
    42,
    43
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "4.3 Pathways to net zero\n\nOff the back of this understanding the existing assets and future technological trends, we can construct \nfuture pathways to help us better understand the challenges and opportunities of achieving a net zero \nsteel sector. The main scenario illustrated here represents a pathway to net zero by 2070 (NZ2070), in \nline with the Government’s economy-wide net zero target, announced in 2021. We also explore a more \nambitious scenario, which sees the steel sector reach another key government target – ‘Atmanirbhar \nBharat’ (or self-reliance) by 2047 – which also puts it on tr\n\n… [+5644 more chars]",
  "content_hash": "b0af6bb3898dea1aaae23d37201726103cdab8d483af40dc6945a8b3102fc432",
  "token_count": 1423,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `d131021e-32cc-54a3-a56e-0023754ea85d`

- vector: dim=3072 · [0.0173, -0.0073, -0.0155, -0.0025, -0.0480, -0.0124, 0.0030, 0.0253, …]

```json
{
  "chunk_id": "d131021e-32cc-54a3-a56e-0023754ea85d",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "Off the back of this understanding the existing assets and future technological trends, we can construct \nfuture pathways to help us better understand the challenges and opportunities of achieving a net zero \nsteel sector. The main scenario illustrated here represents a pathway to net zero by 2070 (NZ2070), in \nline with the Government’s economy-wide net zero target, announced in 2021. We also explore a more \nambitious scenario, which sees the steel sector reach another key government target – ‘Atmanirbhar \nBharat’ (or self-reliance) by 2047 – which also puts it on track for net zero by 2050 (\n\n… [+476 more chars]",
  "content_hash": "dd3adcf1de2132fced4ebeda1c1c0af5778929c21f8cd52d8536d3cdeca26a62",
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
  "parent_chunk_id": "1b320875-fced-5616-8213-97b18e420c63",
  "chunk_index": 44,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `0c93286e-0250-566d-8c19-ab29b02e332c`

- vector: dim=3072 · [-0.0002, -0.0037, -0.0151, 0.0020, -0.0363, -0.0073, 0.0021, 0.0274, …]

```json
{
  "chunk_id": "0c93286e-0250-566d-8c19-ab29b02e332c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "This can be scaled rapidly \nfrom the 2030s, at which point it will start to compete directly with the less efficient conventional plants. \nFigure 18: Net Zero by 2070 scenario From 2040 onwards, we also see some early MOE plants being deployed. They are at an earlier stage of \ndevelopment versus the hydrogen route but could prove competitive in certain areas without access to \nhydrogen, as they use a similar amount of electricity. Scrap-based EAFs will see an ever-increasing role, \nalthough will be limited by the domestic availability of scrap. No import of scrap is assumed. \nIn terms of phasi\n\n… [+1568 more chars]",
  "content_hash": "74d28c3cebf882ca9405cd667c4ac410201a7c2745f80f30b0b795aff73b2034",
  "token_count": 488,
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
  "chunk_index": 45,
  "page_number": 44,
  "page_range": [
    44,
    44
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `051bfdc0-b1b0-542d-8801-25380dd83cd1`

- vector: dim=3072 · [0.0105, -0.0090, -0.0134, 0.0045, -0.0415, -0.0177, 0.0025, 0.0104, …]

```json
{
  "chunk_id": "051bfdc0-b1b0-542d-8801-25380dd83cd1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "This highlights the important \njoining together of the Net Zero vision, along with a vision of self-reliance, which can both support one \nanother. \nFigure 19: Net Zero by 2050 scenario In the NZ2050 scenario, low emission technologies are introduced at an even faster rate, with the most \nsignificant additions being made up by hydrogen direct reduction, followed by MOE. The greater challenge \nhere is phasing out blast furnaces faster, potentially before the end of their useful lifetime. This is largely \ndue to the limits on domestic coking coal of an adequate quality. Today, India imports over \n\n… [+1527 more chars]",
  "content_hash": "1265f3efcd5b714d7b89abaaf9fc95ef30b4cc2c9d146e2b04ea35d51366171a",
  "token_count": 476,
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
  "chunk_index": 46,
  "page_number": 45,
  "page_range": [
    45,
    45
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `8537da82-5b00-52e1-a060-fabb8d14a1b1`

- vector: dim=3072 · [0.0195, -0.0074, -0.0066, 0.0253, -0.0449, -0.0043, -0.0016, 0.0411, …]

```json
{
  "chunk_id": "8537da82-5b00-52e1-a060-fabb8d14a1b1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.3 Pathways to net zero",
  "chunk_text": "This represents 65% of India’s electricity production today, for just a single sector. \nFigure 20: Coking coal demand in Net Zero scenarios 6\t Electricity consumption assumptions = 650 kWh for EAF, 3.4 MWh for MOE and 2.9 MWh for H2DR\n\nIn the NZ2050 scenario, the challenge is even more extreme with demand increasing by 100-fold between \nnow and 2050, before reaching just over 1,000 TWh in 2070. This faster ramp-up is required in order to \nmeet the dual targets of net zero and self-reliance. To put this in the context of India’s current installations, \noverall renewable deployment hit 100 GW in\n\n… [+743 more chars]",
  "content_hash": "ce0a366b95ae77a62d46525264e543c6c5e9c365ea2f61f47f083470632dfbf1",
  "token_count": 321,
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
  "chunk_index": 47,
  "page_number": 45,
  "page_range": [
    45,
    48
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `edc78c62-5e99-5e47-a15e-f63ecdb06e56`

- vector: dim=3072 · [0.0264, 0.0072, -0.0160, -0.0033, -0.0355, 0.0058, -0.0050, 0.0089, …]

```json
{
  "chunk_id": "edc78c62-5e99-5e47-a15e-f63ecdb06e56",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.1\t Maximize energy efficiency",
  "chunk_text": "The application of best available energy efficient technologies (where cost-effective) should be encouraged, \nparticularly in recently built capacity with long lifetimes. Our analysis shows that the application of best \navailable technologies have the potential to reduce energy and emissions by around 15% across the two \nprimary steelmaking routes (see Technical Annex). There are a number of older plants in dire need of \nmodernization and by applying even the already widely adopted efficiency technologies, these plants can \nsubstantially improve their energy efficiency (see Figure 23).\nFigure \n\n… [+719 more chars]",
  "content_hash": "bc051c317809b60644f2c1e36e359e201c46baffa1b7f74d982ea0a20b2731e2",
  "token_count": 285,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 48,
  "page_number": 48,
  "page_range": [
    48,
    49
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `67611954-cfe9-55ba-8bca-76490fd82e86`

- vector: dim=3072 · [-0.0026, -0.0051, -0.0085, 0.0027, -0.0243, -0.0126, 0.0103, -0.0123, …]

```json
{
  "chunk_id": "67611954-cfe9-55ba-8bca-76490fd82e86",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.2\t Increase scrap utilisation",
  "chunk_text": "Improving resource efficiency and encouraging greater levels of material circularity is vital for mitigating \nnegative environmental impacts as India continues to grow. This includes encouraging greater use of scrap, \nwhich reduces the amount of raw material required for primary steel production, resulting in positive knock-\non effects for energy and emissions. \nThe main scrap-based production route is the electric arc furnace (EAF). If we compare the raw materials, \nenergy and emissions from the scrap-based route with a primary steelmaking process, such as a blast \nfurnace with a basic oxygen\n\n… [+1065 more chars]",
  "content_hash": "a03a7151a476ba29bef77bb55b25130937ebb816f40c0d798f4dc00ea88c81fc",
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
  "chunk_index": 49,
  "page_number": 49,
  "page_range": [
    49,
    49
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `13e50e3e-0967-5c17-b2b7-513e14e65f6c`

- vector: dim=3072 · [0.0081, -0.0085, -0.0168, 0.0049, -0.0388, -0.0140, 0.0180, 0.0077, …]

```json
{
  "chunk_id": "13e50e3e-0967-5c17-b2b7-513e14e65f6c",
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
  "chunk_index": 50,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `4c913f94-b6f1-5aab-864c-78be629b895c`

- vector: dim=3072 · [0.0271, 0.0028, -0.0214, 0.0197, -0.0014, -0.0016, 0.0086, -0.0036, …]

```json
{
  "chunk_id": "4c913f94-b6f1-5aab-864c-78be629b895c",
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
  "chunk_index": 51,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `95e1bd9a-5eaf-5d4e-afbb-a99e7dfa3b35`

- vector: dim=3072 · [0.0118, 0.0279, -0.0180, -0.0079, -0.0129, -0.0230, 0.0033, 0.0076, …]

```json
{
  "chunk_id": "95e1bd9a-5eaf-5d4e-afbb-a99e7dfa3b35",
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
  "chunk_index": 52,
  "page_number": 51,
  "page_range": [
    51,
    51
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `89834947-b0e6-55bc-88a2-f320c4d86224`

- vector: dim=3072 · [0.0159, 0.0110, -0.0153, 0.0204, -0.0373, -0.0117, -0.0140, 0.0020, …]

```json
{
  "chunk_id": "89834947-b0e6-55bc-88a2-f320c4d86224",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.6\t Future-proof new capacity",
  "chunk_text": "An important consideration for low carbon steelmaking routes in India is the lifetime of the plants and \nthe possibility of retrofit in the coming decades. Steel plants have long lifetimes (30 years plus), resulting \nin significant potential for emissions lock-in for plants being built in the coming years, when low carbon \noptions might not be commercially available.\nFigure 25 illustrates two potential transition pathways for the leading technologies discussed earlier. \nFor the hydrogen route, gas-based capacity could be built in the 2020s, using natural gas or coal-based \nsyngas, which is mor\n\n… [+503 more chars]",
  "content_hash": "60e016e6389ed795c54be87f599d4aec82798dc75577210ad341f17d8c9f1bb5",
  "token_count": 215,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 53,
  "page_number": 51,
  "page_range": [
    51,
    51
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `4af5dae5-3e9a-5f3e-a997-d7bd7fcce5af`

- vector: dim=3072 · [0.0042, -0.0106, -0.0092, 0.0058, -0.0414, -0.0029, -0.0394, 0.0130, …]

```json
{
  "chunk_id": "4af5dae5-3e9a-5f3e-a997-d7bd7fcce5af",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.7 Lay the groundwork for a domestic carbon trading",
  "chunk_text": "market\nAn important tool to help accelerate the switch to low carbon technologies is development of domestic \ncarbon trading market. India has already achieved much success with the implementation of the Perform, \nAchieve and Trade (PAT) scheme, which trades energy efficiency certificates between Designated \nConsumers (DCs), including the iron and steel sector. As the need for emission reduction grows, one \npossibility would be to amend this existing policy to measure and control carbon emissions, as opposed \nto energy consumption. This would operate similar to the EU Emissions Trading Scheme \n\n… [+363 more chars]",
  "content_hash": "e5e89a2c295d2d16b850bfb8799df04c91fe3bdaf4a426627f3da03213d28588",
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
  "chunk_index": 54,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "5.8 Support for commercial-scale plants",
  "chunk_text": "5.8 Support for commercial-scale plants\n\nAs a series of demonstration projects in the 2020s help clarify the preferred technology options for low \nemission steel production in India, by the 2030s, public and private sector should have proven joint \nfinancing models to facilitate the construction of commercial-scale green steel plants. This will require \nconsiderable support, assuming some cost difference between green steel and ‘dirty’ steel persists. Whilst \nthe difference in production costs will be mitigated somewhat if green product standards, procurement \ninitiatives, and an emissions pen\n\n… [+3732 more chars]",
  "content_hash": "137b09b256d31a522eff14f8f19f7c2066752bac420aee6b922be06275fe3926",
  "token_count": 954,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `794200f4-54f2-5b05-a50b-185635f3f244`

- vector: dim=3072 · [0.0233, -0.0030, -0.0137, -0.0018, -0.0490, -0.0192, 0.0114, 0.0201, …]

```json
{
  "chunk_id": "794200f4-54f2-5b05-a50b-185635f3f244",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.8 Support for commercial-scale plants",
  "chunk_text": "As a series of demonstration projects in the 2020s help clarify the preferred technology options for low \nemission steel production in India, by the 2030s, public and private sector should have proven joint \nfinancing models to facilitate the construction of commercial-scale green steel plants. This will require \nconsiderable support, assuming some cost difference between green steel and ‘dirty’ steel persists. Whilst \nthe difference in production costs will be mitigated somewhat if green product standards, procurement \ninitiatives, and an emissions penalty are introduced, it may still be nece\n\n… [+517 more chars]",
  "content_hash": "d8090f1c311923050034b9e822901b4cd3c43772a68cf1dcf31151d27ad26e36",
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
  "parent_chunk_id": "e2055103-754c-5c92-8520-ec53409c8a06",
  "chunk_index": 55,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `435e0044-b723-5726-b8ac-c3f3bb3f2a92`

- vector: dim=3072 · [0.0185, -0.0285, -0.0072, 0.0001, -0.0577, -0.0216, -0.0090, 0.0309, …]

```json
{
  "chunk_id": "435e0044-b723-5726-b8ac-c3f3bb3f2a92",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.8 Support for commercial-scale plants",
  "chunk_text": ">90%, making\nuse of excess carbon where possible\nShift to >90% hydrogen use, produced\nentirely from low carbon sources\nBegin blending of low\ncarbon hydrogen\nCH4\nH2\nH2\nCO2\nCO2\nCarbon capture, use/\nstorage technology |  | Figure 25: Pathways for low carbon primary steelmaking |  |\n| --- | --- | --- |\n|  |  | Source: TERI Analysis |\n| 5.7 Lay the groundwork for a domestic carbon trading |  |  |\n| market |  |  |\n| An important tool to help accelerate the switch to low carbon technologies is development of domestic |  |  |\n| carbon trading market. india has already achieved much success with the im\n\n… [+1629 more chars]",
  "content_hash": "219b41d77db6070c022ef418d126611d102990e92040dfca1b75710139c44f00",
  "token_count": 526,
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
  "chunk_index": 56,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `25f58c8d-2e8a-5d5a-bdcf-e6a65547d180`

- vector: dim=3072 · [0.0078, 0.0077, -0.0158, 0.0147, -0.0302, -0.0186, 0.0034, 0.0132, …]

```json
{
  "chunk_id": "25f58c8d-2e8a-5d5a-bdcf-e6a65547d180",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.8 Support for commercial-scale plants",
  "chunk_text": "|  |\n| the difference in production costs will be mitigated somewhat if green product standards, procurement |  |  |\n| initiatives, and an emissions penalty are introduced, it may still be necessary to support the first few |  |  |\n| commercial-scale plants. |  |  | This could include direct financial support from the GoI, via existing bodies such as the Ministry of Steel \n(for example through Carbon Contracts for Difference, which are being explored in Germany), although this \nis likely to be insufficient given limited domestic resources. As renewable electricity projects become ‘self-\nfinanc\n\n… [+823 more chars]",
  "content_hash": "f4714babaa645e6bc2f1d1bfcdb16c18f9ff702e8cd9ccf5db3173b32abf17db",
  "token_count": 275,
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
  "chunk_index": 57,
  "page_number": 53,
  "page_range": [
    53,
    53
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `aec6a648-0987-5e58-828a-b8d5fe9c0a40`

- vector: dim=3072 · [0.0014, -0.0242, -0.0032, 0.0026, -0.0121, -0.0177, -0.0433, 0.0076, …]

```json
{
  "chunk_id": "aec6a648-0987-5e58-828a-b8d5fe9c0a40",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff",
  "chunk_text": "Steel, a carbon intensive product which is also heavily traded globally, has found a lot of attention in \nrecent years in the trade environment policy discourses. For example, the EU green deal mentions \nimposition of Carbon Border Adjustment Mechanism (CBAM), to prevent carbon leakage while creating \nlevel playing field in the EU where steel is one of the few sectors that will come under this measure. It may \nbe worth exploring similar import restrictions on steel imports to India originating from countries having \nFigure 26: Carbon border adjustment\ndomestic industry during transition\n250\n0\n\n\n… [+2157 more chars]",
  "content_hash": "5ea15cd073e1d7aca7009230595e6e12f6d0b634b8f661078272516855245184",
  "token_count": 576,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "chunk_index": 58,
  "page_number": 53,
  "page_range": [
    53,
    55
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
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
  "section_heading": "Conclusions",
  "section_type": "references",
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `faa68e5f-7f42-53ed-9dff-415735df20c3`

- vector: dim=3072 · [0.0262, -0.0235, -0.0160, 0.0046, -0.0191, -0.0154, -0.0024, 0.0006, …]

```json
{
  "chunk_id": "faa68e5f-7f42-53ed-9dff-415735df20c3",
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
  "parent_chunk_id": "90684a8c-367e-5fee-bd72-5849a8384350",
  "chunk_index": 59,
  "page_number": 56,
  "page_range": [
    56,
    56
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `e28042e8-3ff5-59c9-8320-9d55a96eca56`

- vector: dim=3072 · [0.0132, 0.0067, -0.0107, 0.0139, -0.0058, -0.0048, 0.0092, -0.0008, …]

```json
{
  "chunk_id": "e28042e8-3ff5-59c9-8320-9d55a96eca56",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "Through rapidly \nscaling-up renewable electricity and green hydrogen production, in particular, the steel sector can shift \naway from imported fossil fuels, putting the sector on a path to a net zero, self-reliant future. ArcelorMittal. (2021). ArcelorMittal launches XCarb™, signalling its commitment to producing carbon neutral \nsteel. \nRetrieved \nfrom \nhttps://corporate.arcelormittal.com/media/press-releases/arcelormittal-launches-\nxcarb-signalling-its-commitment-to-producing-carbon-neutral-steel#:~:text=ArcelorMittal%20launches%20\nXCarb%E2%84%A2%2C%20signalling%20its%20commitment%20to%20prod\n\n… [+1145 more chars]",
  "content_hash": "bacc8cba5675aecf571e6535c8d30874300ed1a5791d365baa66c6b969fa8891",
  "token_count": 478,
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
  "chunk_index": 60,
  "page_number": 57,
  "page_range": [
    57,
    57
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `244dc7b2-e82f-5831-ae7c-779dda4e4ed8`

- vector: dim=3072 · [0.0209, 0.0065, -0.0145, 0.0133, -0.0195, -0.0060, 0.0036, 0.0011, …]

```json
{
  "chunk_id": "244dc7b2-e82f-5831-ae7c-779dda4e4ed8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "(2021). The Deloitte Global Millennial Survey 2020. Retrieved from https://www2.deloitte.com/global/en/\npages/about-deloitte/articles/millennialsurvey.html DIPP. (2020). Fact sheet on foreign direct investment (FDI). Retrieved from https://dipp.gov.in/sites/default/files/\nFDI_Factsheet_June20_23Sept2020.pdf\nDIW Berlin, TERI. (2020). Transitioning India’s steel and cement industries to low carbon pathways. Retrieved from \nhttps://www.diw.de/documents/dokumentenarchiv/17/diw_01.c.794597.de/cs-ndc_tracking_india_jul_2020.pdf\nEuropean Union. (2005). EU Emissions Trading System (EU ETS). Retrieved \n\n… [+1159 more chars]",
  "content_hash": "7505f2d34ad70becaae91553572d78f331fde590f9aa50ba928ac00f95594d73",
  "token_count": 483,
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
  "chunk_index": 61,
  "page_number": 57,
  "page_range": [
    57,
    57
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `e4a4aef9-fedf-5cad-b653-d1b19b8186f9`

- vector: dim=3072 · [0.0144, 0.0179, -0.0085, 0.0159, 0.0055, -0.0155, -0.0067, 0.0086, …]

```json
{
  "chunk_id": "e4a4aef9-fedf-5cad-b653-d1b19b8186f9",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "(2018). Retrieved from https://www.ibef.org/states/odisha-presentation\nIBEF. (2020). Retrieved from https://www.ibef.org/download/Chhattisgarh-June-2020.pdf IBEF. (2021). Retrieved from https://www.ibef.org/states/steel-presentation\nBibliography\n\nIEA. (2017). Renewable Energy for Industry. Retrieved from https://iea.blob.core.windows.net/assets/48356f8e-77a7-\n49b8-87de-87326a862a9a/Insights_series_2017_Renewable_Energy_for_Industry.pdf\nIEA. (2020). Iron and Steel Technology Roadmap: Towards more sustainable steelmaking. Retrieved October 2020, \nfrom \nhttps://iea.blob.core.windows.net/assets/eb\n\n… [+1079 more chars]",
  "content_hash": "c2f2a216cba16619c6c758c4b5a675f18a25d8ae74cc438091079dd4651bb123",
  "token_count": 509,
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
  "chunk_index": 62,
  "page_number": 57,
  "page_range": [
    57,
    58
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `ba33c38a-29e3-5ce2-acb1-90549857e10f`

- vector: dim=3072 · [0.0288, 0.0097, -0.0104, -0.0004, 0.0095, -0.0029, -0.0071, 0.0168, …]

```json
{
  "chunk_id": "ba33c38a-29e3-5ce2-acb1-90549857e10f",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "(2019). Draft Framework Policy - Development of Steel Clusters in India. Retrieved from Ministry of Steel: https://\nsteel.gov.in/sites/default/files/Draft%20Policy%20for%20Steel%20Cluster_vf15.pdf MoS. (2020a). Annual Report 2019-20. Retrieved from https://steel.gov.in/sites/default/files/Annual%20Report-\nMinistry%20of%20Steel%202019-20.pdf\nMoS. (2020b). Retrieved from https://www.pib.gov.in/PressReleasePage.aspx?PRID=1673977\nMoS. (2021a). Annual Report 2020-21. Retrieved from https://steel.gov.in/sites/default/files/Annual%20Report-\nMinistry%20of%20Steel%202020-21.pdf\nMoS. (2021b). An Overvie\n\n… [+878 more chars]",
  "content_hash": "6f979bb8863caa2a1003881b7269cedaac3d8ffa07f05a1ea30a08d7d36205c0",
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
  "parent_chunk_id": "90684a8c-367e-5fee-bd72-5849a8384350",
  "chunk_index": 63,
  "page_number": 58,
  "page_range": [
    58,
    58
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Parent · `e8824cc1-0a94-58f5-b881-c57a582b033a`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e8824cc1-0a94-58f5-b881-c57a582b033a",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "Conclusions (cont.)\n\nOECD. (2018). Economic Outlook No 103 - July 2018 - Long-term baseline projections. (Organisation for Economic Co-\noperation and Development) Retrieved from Stat: https://stats.oecd.org/Index.aspx?DataSetCode=EO103_LTB\nPHDCCI. (2019). Retrieved from https://www.phdcci.in/wp-content/uploads/2019/01/Rising-Jharkhand-Economic-\nProfile-_final-for-Print-Low-size-updated.pdf\nPIB. (2021). Production Linked Incentive (PLI) Scheme for Specialty Steel Approved by Union Cabinet. Retrieved from \nhttps://pib.gov.in/PressReleasePage.aspx?PRID=1738126\nPrimetals Technologies. (2019). Prim\n\n… [+3168 more chars]",
  "content_hash": "1ac27d190be99480001d35d68e05fcfc72eb8b5536b36de00824da07701bd2e4",
  "token_count": 1069,
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
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `dfc71df6-7e4d-5875-b1cf-7fcbcfa55f59`

- vector: dim=3072 · [0.0284, 0.0238, -0.0107, 0.0295, 0.0068, -0.0076, 0.0079, 0.0115, …]

```json
{
  "chunk_id": "dfc71df6-7e4d-5875-b1cf-7fcbcfa55f59",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
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
  "parent_chunk_id": "e8824cc1-0a94-58f5-b881-c57a582b033a",
  "chunk_index": 64,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `8380484e-96e8-512a-bf1a-db990c643dd2`

- vector: dim=3072 · [0.0424, 0.0220, -0.0051, 0.0089, -0.0080, 0.0028, 0.0076, 0.0053, …]

```json
{
  "chunk_id": "8380484e-96e8-512a-bf1a-db990c643dd2",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "(2021). Tata Steel commissions India’s first plant for CO2 capture from Blast Furnace gas at Jamshedpur. \nRetrieved from https://www.tatasteel.com/media/newsroom/press-releases/india/2021/tata-steel-commissions- india-s-first-plant-for-co2-capture-from-blast-furnace-gas-at-jamshedpur/\nTERI. (2020). Transitioning India’s steel and cement industries to low carbon pathways. Retrieved from https://www.\ndiw.de/documents/dokumentenarchiv/17/diw_01.c.794597.de/cs-ndc_tracking_india_jul_2020.pdf\nThe Economic Times. (2021). Tata Steel’s Jamshedpur plant recognised as advanced 4th industrial revolution \n\n… [+1158 more chars]",
  "content_hash": "5b7c4d90d357e078e4f168ca518ed2027d3d25db7e76ebc38bf8fb7a2fb76512",
  "token_count": 493,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "e8824cc1-0a94-58f5-b881-c57a582b033a",
  "chunk_index": 65,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```

## Child · `9fca97af-dd37-5ee3-ad6e-93942d1c80c2`

- vector: dim=3072 · [0.0287, 0.0234, -0.0102, -0.0137, 0.0046, -0.0092, 0.0110, 0.0057, …]

```json
{
  "chunk_id": "9fca97af-dd37-5ee3-ad6e-93942d1c80c2",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "(2017). World Development Indicators. \nWSA. (2018). Steel Statistical Yearbook 2018. \nWSA. (2019). Towards a net-zero emissions steel industry. Retrieved from https://iea-industry.org/app/uploads/5- Ekdahl-Towrds-a-net-zero-emissions-steel-industry.pdf\nWSA. (2020a). World Steel in figures. Retrieved 2020, from World Steel Association: https://www.worldsteel.org/en/\ndam/jcr:f7982217-cfde-4fdc-8ba0-795ed807f513/World%2520Steel%2520in%2520Figures%25202020i.pdf\nWSA. (2020b). Steel Statistical Yearbook 2020 Concise Version. Retrieved from https://www.worldsteel.org/en/dam/\njcr:5001dac8-0083-46f3-aa\n\n… [+184 more chars]",
  "content_hash": "71c0ab3eda70ed446ed204c467fc85ea53bffd9eab89942346706026ec73eef0",
  "token_count": 244,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "achieving_green_steel_roadmap_pdf",
  "pdf_path": "Achieving_Green_Steel_Roadmap.pdf",
  "parent_chunk_id": "e8824cc1-0a94-58f5-b881-c57a582b033a",
  "chunk_index": 66,
  "page_number": 59,
  "page_range": [
    59,
    60
  ],
  "created_at": "2026-06-30T08:25:25.928884+00:00",
  "updated_at": "2026-06-30T08:25:25.928884+00:00"
}
```
