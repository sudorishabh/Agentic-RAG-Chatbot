# Qdrant points — Achieving_Green_Steel_Roadmap.pdf

- points (rows upserted): **75**
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
  "chunk_text": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY\n\nteri\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\n\n©2022 The Energy and Resources Institute\nAuthors\nWill Hall, Visiting Fellow, TERI (till June 2022)\nSachin Kumar, Senior Fellow, TERI (till Dec 2021)\nSneha Kashyap, Research Associate, TERI (till Mar 2022)\nShruti Dayal, Research Associate, TERI\nReviewer\nMr Girish Sethi, Senior Director, TERI\nDisclaimer\nThis report is an output of a research exercise undertaken by TERI supported by CIFF. It does not represent \nthe views of the supporting organisations or th\n\n… [+2807 more chars]",
  "content_hash": "6ea4d4fa479846a4bdba3c19b84a1e25e1422014be84d78d8c3819315f8179e2",
  "token_count": 815,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `7588344d-0b1b-5f91-a8ba-5adc03800e51`

- vector: dim=3072 · [0.0115, -0.0065, -0.0166, -0.0221, -0.0247, 0.0100, 0.0030, 0.0089, …]

```json
{
  "chunk_id": "7588344d-0b1b-5f91-a8ba-5adc03800e51",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
  "chunk_text": "teri\nTHE ENERGY AND\nRESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\n\n©2022 The Energy and Resources Institute\nAuthors\nWill Hall, Visiting Fellow, TERI (till June 2022)\nSachin Kumar, Senior Fellow, TERI (till Dec 2021)\nSneha Kashyap, Research Associate, TERI (till Mar 2022)\nShruti Dayal, Research Associate, TERI\nReviewer\nMr Girish Sethi, Senior Director, TERI\nDisclaimer\nThis report is an output of a research exercise undertaken by TERI supported by CIFF. It does not represent \nthe views of the supporting organisations or the acknowledged individuals. While every effor\n\n… [+377 more chars]",
  "content_hash": "d0972cd858f3102fd9c42cfdd10d60b31eca5d7bf8f0df0ce53eb6bd56212f04",
  "token_count": 245,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `358a363e-e752-5149-a03a-98a2055c2ade`

- vector: dim=3072 · [0.0116, -0.0060, -0.0162, -0.0220, -0.0313, 0.0034, -0.0283, 0.0126, …]

```json
{
  "chunk_id": "358a363e-e752-5149-a03a-98a2055c2ade",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `5f049072-f979-58e9-a2ab-b832a7900270`

- vector: dim=3072 · [0.0095, 0.0106, -0.0201, -0.0361, -0.0310, -0.0154, 0.0020, 0.0210, …]

```json
{
  "chunk_id": "5f049072-f979-58e9-a2ab-b832a7900270",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION INDIA — CHY",
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "chunk_text": "FOREWORD\n\nThe Indian steel sector has been, and will remain an important pillar of India's economic growth and\ndevelopment. Steel demand is estimated to increase more than by twofold 2030-31, spurred by increased\nspending on infrastructure, automobiles and affordable housing. This increase in demand will provide\nboth challenges and opportunities, including the impact of the sector on the environment. There is a need\nto ensure that future pathways for growing steel demand are green with minimal environmental impacts.\n\nThe Energy and Resources Institute (TERI), as part of the Energy Transitions \n\n… [+2760 more chars]",
  "content_hash": "0c808e9e357a180c02cac5747c389e6b560e7826f3e764ff63bfef7eff3ab52e",
  "token_count": 589,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `58684db4-2513-5f62-85ad-68415c46e32d`

- vector: dim=3072 · [0.0116, -0.0381, -0.0107, -0.0081, -0.0258, -0.0241, 0.0058, -0.0069, …]

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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `59f1eb07-3835-5a15-8ec9-0ebe172400e9`

- vector: dim=3072 · [0.0297, -0.0302, -0.0079, -0.0107, -0.0208, -0.0234, 0.0069, 0.0163, …]

```json
{
  "chunk_id": "59f1eb07-3835-5a15-8ec9-0ebe172400e9",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "FOREWORD",
  "chunk_text": "In the formulation of this Roadmap, TERI has carried out extensive\nconsultations with various stakeholders in the steel sector - producers, buyers, technology providers,\nfinanciers, government bodies and the research community. This comprehensive Roadmap provides an overview of the current state of the steel sector and details a\nrange of possible emissions mitigation strategies. In the near term, implementation of strategies such\nas maximizing energy efficiency, increasing utilization of scrap, introducing green product standards,\ncreating demand for green steel, setting up pilot demonstration\n\n… [+1076 more chars]",
  "content_hash": "a2e45312a1e34154056be43ee88cb05bf4e8a9dd0131369f85228096ddc212c6",
  "token_count": 277,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `b17edf1f-3af1-5e56-811f-b2fdd1142fdf`

- vector: dim=3072 · [0.0304, -0.0069, -0.0159, -0.0047, 0.0160, -0.0311, 0.0109, 0.0417, …]

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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `3da91747-884e-5226-ab20-712e4ebd5abf`

- vector: dim=3072 · [0.0420, -0.0267, -0.0019, -0.0012, -0.0346, -0.0076, -0.0078, 0.0326, …]

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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `ebce17fd-eca3-5605-ad95-53a0e5364d46`

- vector: dim=3072 · [0.0325, -0.0260, -0.0097, 0.0216, -0.0155, -0.0198, -0.0179, 0.0376, …]

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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `e7655ac3-96f6-53f5-88d4-b0c0e5bb12f8`

- vector: dim=3072 · [0.0160, 0.0021, -0.0050, -0.0042, -0.0225, -0.0069, -0.0009, 0.0206, …]

```json
{
  "chunk_id": "e7655ac3-96f6-53f5-88d4-b0c0e5bb12f8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "AI – Artificial Intelligence",
  "section_type": "glossary",
  "chunk_text": "BEE – Bureau of Energy Efficiency \nBF-BOF – Blast Furnace – Basic Oxygen Furnace \nBIS –Bureau of Indian Standards \nCAGR – Compounded Annual Growth Rate \nCBAM – Carbon Border Adjustment Mechanism \nCCUS – Carbon Capture, Use and Storage \nCO2 – Carbon Dioxide DR – Direct Reduction \nEAF – Electric Arc Furnace \nEBITDA – Earnings before Interest, Taxes, Depreciation, and Amortization \nEIF – Electric Induction Furnace \nETS – Emissions Trading Scheme \nFDI – Foreign Direct Investment \nFTA – Free Trade Agreements \nGDP – Gross Domestic Product \nGHG – Greenhouse Gases \nGoI – Government of India \nIEA – Int\n\n… [+1111 more chars]",
  "content_hash": "c756aa7060f98d1933b06232bd8f4723564d951cc6e4f6acd895f058d54426ca",
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
  "chunk_index": 8,
  "page_number": 12,
  "page_range": [
    12,
    13
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": "ENERGY TRANSITIONS — COMMISSION TARDE\n\nThe global steel sector is shifting rapidly. More than 30% of steel companies (by \nproduction) have net zero targets - up from zero less than 3 years ago - and more \nthan 90% of countries (by GDP) have national level net zero targets. \n•\t\nGovernments are moving fast to create ‘level playing fields’ to protect domestic \nsteel sectors during transition, including carbon border adjustment proposals, \ncommitments to joint standardization and climate clubs. \n•\t\nThe financial sector is shifting funds away from fossil investments, with a \nsignificant additional \n\n… [+4474 more chars]",
  "content_hash": "2fa8d0478fef6ab785c488af3289a267cbf4f938de07e0ec043b6de7a538639c",
  "token_count": 1027,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `46964e2c-480b-5118-beb9-4475834cdecb`

- vector: dim=3072 · [0.0258, -0.0194, -0.0094, -0.0035, -0.0134, -0.0333, 0.0043, 0.0104, …]

```json
{
  "chunk_id": "46964e2c-480b-5118-beb9-4475834cdecb",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": "The global steel sector is shifting rapidly. More than 30% of steel companies (by \nproduction) have net zero targets - up from zero less than 3 years ago - and more \nthan 90% of countries (by GDP) have national level net zero targets. \n•\t\nGovernments are moving fast to create ‘level playing fields’ to protect domestic \nsteel sectors during transition, including carbon border adjustment proposals, \ncommitments to joint standardization and climate clubs. \n•\t\nThe financial sector is shifting funds away from fossil investments, with a \nsignificant additional push from COP26 under the Glasgow Finan\n\n… [+1505 more chars]",
  "content_hash": "08ebb390cafb744502a6a52304532d5f4d9fb95ea0c97176166b220aa7f723bf",
  "token_count": 431,
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
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `d9574072-ac9e-531a-968e-901f37082db4`

- vector: dim=3072 · [0.0300, -0.0377, -0.0005, -0.0072, -0.0323, -0.0177, 0.0016, 0.0171, …]

```json
{
  "chunk_id": "d9574072-ac9e-531a-968e-901f37082db4",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
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
  "chunk_index": 10,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `2684799c-bdc3-56e1-b5e0-ee100d5297fc`

- vector: dim=3072 · [0.0153, -0.0381, -0.0159, -0.0097, -0.0398, -0.0220, 0.0130, 0.0317, …]

```json
{
  "chunk_id": "2684799c-bdc3-56e1-b5e0-ee100d5297fc",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "ENERGY TRANSITIONS — COMMISSION TARDE",
  "chunk_text": "This roadmap is a follow-up to the consultation document published by TERI in 2020, “Towards a Low Carbon Steel Sector: An overview of the changing market, technology and policy context for Indian steel”. \nThe updated consultation document is available at our website as Tech Annex . The roadmap builds on this \npreceding work, along with other TERI and ETC publications on steel and hydrogen1, incorporating in the \ndetailed comments and feedback from discussions with international experts, steel sector representatives, \nand government officials.\nINTRODUCTION\n1\t The Potential Role of Hydrogen in \n\n… [+199 more chars]",
  "content_hash": "630c8ecb0f829e0312aa3f2b1c52a9e9f7c0bb4735a34a25042bd69780fb555f",
  "token_count": 176,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
  "chunk_text": "1 BACKGROUND — 1.1\t Indian steel industry\n\nIndia is currently the world’s second-largest steel producer, and second-largest steel consumer (WSA, \n2020a). The steel industry in India is relatively heterogeneous compared to other countries, with a wide \nrange of different sized facilities in the primary and secondary steelmaking sectors. There are also several \ndifferent technologies currently being used, including the Blast Furnace – Basic Oxygen Furnace (BF-BOF), \ncoal-based Direct Reduction (DR), gas-based DR, Electric Induction Furnace (EIF) and Electric Arc Furnace \n(EAF). BOF technology do\n\n… [+4017 more chars]",
  "content_hash": "ac74ac99febc2220e3fc121b41f6b92b68843a6a8cb3a8c74a59696bf253f3b7",
  "token_count": 1057,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `65fef68a-bd8c-5a56-99ea-ebce6c7b6e68`

- vector: dim=3072 · [0.0297, 0.0127, -0.0107, -0.0065, -0.0082, -0.0145, 0.0011, -0.0172, …]

```json
{
  "chunk_id": "65fef68a-bd8c-5a56-99ea-ebce6c7b6e68",
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
  "parent_chunk_id": "6735efd5-1ad3-5cb6-9ec6-f2a61992b883",
  "chunk_index": 12,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `69b7c667-73cc-519e-9c11-0c69e6548f97`

- vector: dim=3072 · [0.0072, -0.0032, 0.0020, -0.0023, -0.0252, -0.0145, -0.0168, 0.0154, …]

```json
{
  "chunk_id": "69b7c667-73cc-519e-9c11-0c69e6548f97",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
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
  "chunk_index": 13,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `aea94858-15b5-5a41-9fd2-098f1d473790`

- vector: dim=3072 · [0.0069, -0.0110, -0.0015, 0.0188, -0.0209, 0.0053, -0.0172, 0.0093, …]

```json
{
  "chunk_id": "aea94858-15b5-5a41-9fd2-098f1d473790",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1 BACKGROUND — 1.1\t Indian steel industry",
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
  "chunk_index": 14,
  "page_number": 20,
  "page_range": [
    20,
    21
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `687441d7-1545-5fd7-909d-c355cda58034`

- vector: dim=3072 · [0.0209, 0.0050, -0.0136, 0.0087, -0.0147, -0.0209, 0.0012, -0.0146, …]

```json
{
  "chunk_id": "687441d7-1545-5fd7-909d-c355cda58034",
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
  "chunk_index": 15,
  "page_number": 21,
  "page_range": [
    21,
    22
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `03ce0500-0a6b-5cc2-8fca-cd515588433e`

- vector: dim=3072 · [-0.0004, -0.0122, -0.0119, -0.0030, 0.0084, 0.0011, -0.0066, -0.0172, …]

```json
{
  "chunk_id": "03ce0500-0a6b-5cc2-8fca-cd515588433e",
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
  "chunk_index": 16,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `241d7bd7-74c0-5722-a48b-1669da1e1bb0`

- vector: dim=3072 · [0.0079, -0.0025, -0.0090, -0.0030, 0.0165, -0.0154, 0.0064, -0.0002, …]

```json
{
  "chunk_id": "241d7bd7-74c0-5722-a48b-1669da1e1bb0",
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
  "chunk_index": 17,
  "page_number": 22,
  "page_range": [
    22,
    24
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "parent_chunk_id": "bf332323-2dfc-59a2-822e-7ba007c960f4",
  "chunk_index": 18,
  "page_number": 24,
  "page_range": [
    24,
    24
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `106c1561-5c4a-5559-a953-315cedd22e4b`

- vector: dim=3072 · [0.0186, 0.0062, -0.0113, 0.0087, -0.0093, 0.0035, 0.0042, -0.0171, …]

```json
{
  "chunk_id": "106c1561-5c4a-5559-a953-315cedd22e4b",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.2\t Digitalisation",
  "chunk_text": "Their Kalinganagar plant has \ndeveloped an expert team of analytics specialists, including data scientists and translators. The net impact of digitalisation on the Indian iron and steel sector is uncertain. It represents a significant\nopportunity for Indian steelmakers as build new capacity in the coming decades, able to take advantage of\nthe latest technologies, unavailable to other countries when they were expanding their steel production.\nIndia has shown a proficiency for rapid adoption of new technologies in other sectors, with a relatively\nyoung and technically literate workforce better s\n\n… [+827 more chars]",
  "content_hash": "e6979d96606fab03b1c6861160872252d09b812784a5267f195602b2a6f8f002",
  "token_count": 261,
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
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "1.3.3 Decarbonisation\n\nThe third macro-trend, and arguably\nthe trend driving the most significant\ndisruption in the iron and steel\nsector, is the growing imperative for\ndecarbonisation. The iron and steel\nsector is currently both highly energy\nand emissions-intensive, accounting\nfor 8% of global final energy use and\n7% of global direct energy-related\nCO2 emissions (including industrial\nprocess emissions) (IEA, 2020). As\nprogress to decarbonize the power\nand transport sectors accelerates,\nwe are starting to see greater focus\non the heavy industry sectors,\nsuch as iron & steel, cement and\nchemic\n\n… [+1617 more chars]",
  "content_hash": "d767703453183205301257b33e1b9bfa48cc1828f57f794c2b8f70453c40b41c",
  "token_count": 489,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `b8a4fdc1-b3ea-596f-981f-5a4cab66dfce`

- vector: dim=3072 · [0.0028, -0.0238, -0.0166, 0.0038, -0.0356, -0.0320, 0.0066, -0.0041, …]

```json
{
  "chunk_id": "b8a4fdc1-b3ea-596f-981f-5a4cab66dfce",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "The third macro-trend, and arguably\nthe trend driving the most significant\ndisruption in the iron and steel\nsector, is the growing imperative for\ndecarbonisation. The iron and steel\nsector is currently both highly energy\nand emissions-intensive, accounting\nfor 8% of global final energy use and\n7% of global direct energy-related\nCO2 emissions (including industrial\nprocess emissions) (IEA, 2020). As\nprogress to decarbonize the power\nand transport sectors accelerates,\nwe are starting to see greater focus\non the heavy industry sectors,\nsuch as iron & steel, cement and\nchemicals.\n\nFigure 7: Green s\n\n… [+588 more chars]",
  "content_hash": "d8aad38f9a01ce83e2d88cc455329cb91e019f4519a5ff2223696190e9714a40",
  "token_count": 283,
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
  "chunk_index": 20,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `2016fa91-aa35-5177-a341-2634b8dfbac8`

- vector: dim=3072 · [0.0236, -0.0077, -0.0131, 0.0106, -0.0206, -0.0282, -0.0216, -0.0230, …]

```json
{
  "chunk_id": "2016fa91-aa35-5177-a341-2634b8dfbac8",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "1.3.3 Decarbonisation",
  "chunk_text": "Even with ambitious energy and material\nefficiency measures to reduce energy consumption and mitigate demand growth, the level of emissions\nin the Indian iron & steel sector will be incompatible with the ambition of limiting global warming to well\nbelow 2ºC. For further emissions reduction, the introduction of new, low carbon technologies will be required, such \nas the use of low carbon hydrogen or carbon, capture, utilisation and storage (CCUS). Initially, these \nnew processes will increase the costs of steel production, and will require the introduction of supportive \npolicies by the governm\n\n… [+663 more chars]",
  "content_hash": "ce237b68f91829962a067feb457df746c97c58b54334eced7c666c08769f1801",
  "token_count": 247,
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
  "page_number": 26,
  "page_range": [
    26,
    26
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `e69fa337-3862-5a53-a466-66d5f6b75657`

- vector: dim=3072 · [0.0148, 0.0131, -0.0050, -0.0188, 0.0257, -0.0243, 0.0101, 0.0067, …]

```json
{
  "chunk_id": "e69fa337-3862-5a53-a466-66d5f6b75657",
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
  "chunk_index": 22,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `4731a355-4f0a-5cae-93eb-9d68ce161448`

- vector: dim=3072 · [0.0163, 0.0185, -0.0120, 0.0039, 0.0220, -0.0272, -0.0228, -0.0200, …]

```json
{
  "chunk_id": "4731a355-4f0a-5cae-93eb-9d68ce161448",
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
  "chunk_index": 23,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `004f77c3-23e1-5d46-b4c5-5a53460f780f`

- vector: dim=3072 · [0.0150, 0.0210, 0.0009, 0.0030, -0.0343, -0.0211, 0.0021, -0.0202, …]

```json
{
  "chunk_id": "004f77c3-23e1-5d46-b4c5-5a53460f780f",
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
  "chunk_index": 24,
  "page_number": 28,
  "page_range": [
    28,
    29
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `0c7a15af-0cc7-5d8f-a638-fcf3fbf3e115`

- vector: dim=3072 · [0.0110, -0.0034, -0.0036, 0.0047, -0.0221, -0.0276, -0.0196, -0.0116, …]

```json
{
  "chunk_id": "0c7a15af-0cc7-5d8f-a638-fcf3fbf3e115",
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
  "chunk_index": 25,
  "page_number": 30,
  "page_range": [
    30,
    32
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "chunk_text": "3.1 Competitiveness\n\nWhilst there have been significant improvements in the operational efficiencies of steel production in\nIndia in recent years, on average, Indian steel producers are still facing costs around 5-10% higher as\ncompared to the global average. In the context of a global glut in steel supply, this places Indian steel\nproducers in a difficult position, reducing profits for reinvestment and limiting export markets. The cost\npremium is driven by a number of factors (see Table 1), with the main contributors being costs of finance\n(approximately 12% versus 3-5% across the European Un\n\n… [+2609 more chars]",
  "content_hash": "7d34cdf9cdcf0936b9f3484a7710173bc4eaf8affea532380abfb7bf28241535",
  "token_count": 754,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `9820d55d-49ab-5d0c-89a5-b39eaa5dfa03`

- vector: dim=3072 · [0.0089, 0.0126, -0.0057, 0.0163, -0.0139, -0.0230, -0.0092, -0.0018, …]

```json
{
  "chunk_id": "9820d55d-49ab-5d0c-89a5-b39eaa5dfa03",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.1 Competitiveness",
  "chunk_text": "Whilst there have been significant improvements in the operational efficiencies of steel production in\nIndia in recent years, on average, Indian steel producers are still facing costs around 5-10% higher as\ncompared to the global average. In the context of a global glut in steel supply, this places Indian steel\nproducers in a difficult position, reducing profits for reinvestment and limiting export markets. The cost\npremium is driven by a number of factors (see Table 1), with the main contributors being costs of finance\n(approximately 12% versus 3-5% across the European Union) and the costs of\n\n… [+1156 more chars]",
  "content_hash": "2244951d814a5194631f63b265cf00bd36b48bac34e6e45a926582f90b131b07",
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
  "parent_chunk_id": "a9ef31a8-c2b3-5729-8961-e3ed32bb0616",
  "chunk_index": 26,
  "page_number": 32,
  "page_range": [
    32,
    32
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `9f95be06-4b5e-5bd4-90c0-e7e0a15f8708`

- vector: dim=3072 · [0.0082, 0.0172, -0.0055, 0.0120, -0.0009, -0.0207, -0.0038, 0.0165, …]

```json
{
  "chunk_id": "9f95be06-4b5e-5bd4-90c0-e7e0a15f8708",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.1 Competitiveness",
  "chunk_text": "To help improve the relative competitiveness of domestic producers, the Government has\nrecently approved the Production Linked Incentive Scheme for 'Speciality Steel' (PIB, 2021), although it is\ntoo early to assess the effectiveness of this programme. | Item | Cost ($/ton) |\n| --- | --- |\n| Logistics and Infrastructure | 25-30 |\n| Power | 8-12 |\n| Import duty on coal | 5-7 |\n| GST Compensation Cess | 2-4 |\n| Taxes and duties on iron ore | 8-12 |\n| Finance | 30-35 |\n| Total cost disadvantage | 80-100 |\n\nSource: (Niti Aayog, 2016)\n\nTata Steel Ltd.\nSteel Authority of India Ltd.\nJindal Steel & Pow\n\n… [+1082 more chars]",
  "content_hash": "529a243ebce71fdc134efec50a194845f048b2c60bc0c5dfc7e99dc438832f54",
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
  "parent_chunk_id": "a9ef31a8-c2b3-5729-8961-e3ed32bb0616",
  "chunk_index": 27,
  "page_number": 32,
  "page_range": [
    32,
    33
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `acdddbc7-8827-59f4-84c0-a5f16c70a126`

- vector: dim=3072 · [-0.0111, -0.0007, -0.0032, -0.0006, -0.0144, -0.0281, -0.0072, -0.0028, …]

```json
{
  "chunk_id": "acdddbc7-8827-59f4-84c0-a5f16c70a126",
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
  "chunk_index": 28,
  "page_number": 33,
  "page_range": [
    33,
    34
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "section_heading": "3.3 Technology availability",
  "chunk_text": "3.3 Technology availability\n\nTo achieve deep decarbonisation of the iron and steel sector, new technologies will be required -\nin particular for the replacement of conventional primary production processes with low emissions\nalternatives. There are several emerging low emissions technologies to produce steel from iron ore. They\nbroadly fall into three categories:\n\n· Carbon capture, utilisation, and storage (CCUS)\n\n· The use of low carbon hydrogen to replace fossil fuels\n\n· Direct electrification through electrolysis of iron ore\n\nEach of these technologies differ in their suitability to the Ind\n\n… [+3877 more chars]",
  "content_hash": "8051587bb14fd4e606e34096ae3bc30a4e8ce7140a989837c84b237eecd5f765",
  "token_count": 1006,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `53440e1e-175f-5063-a8af-71aae63bac96`

- vector: dim=3072 · [0.0258, -0.0081, -0.0175, 0.0118, -0.0331, -0.0012, -0.0115, -0.0156, …]

```json
{
  "chunk_id": "53440e1e-175f-5063-a8af-71aae63bac96",
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
  "parent_chunk_id": "ad57f944-65bb-5fbc-a070-823c4da8b6eb",
  "chunk_index": 29,
  "page_number": 34,
  "page_range": [
    34,
    34
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `580b0363-c934-5ea2-876f-b7615995eaae`

- vector: dim=3072 · [0.0111, 0.0002, -0.0175, -0.0024, -0.0226, -0.0219, 0.0024, -0.0032, …]

```json
{
  "chunk_id": "580b0363-c934-5ea2-876f-b7615995eaae",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3 Technology availability",
  "chunk_text": "An overview is provided in Table 2. | Technology | TRL | Emissions reduction potential | Suitability for deep decarbonisation in India |\n| --- | --- | --- | --- |\n| Carbon Capture, Utilisation, and Storage | Carbon Capture, Utilisation, and Storage | Carbon Capture, Utilisation, and Storage |  |\n| BF-BOF with CCUS | 5 | Possibility to reduce CO2 by approximately 60%. Although higher capture rates are possible, costs increase substantially due to multiple CO, sources (IEA, 2017). | Limited cost-effective CO2 capture will restrict the use of this technology for deep decarbonisation, although cou\n\n… [+1635 more chars]",
  "content_hash": "0634bd2d12d5b7b0fb6169d81198bc611663a43bee18a56ce69780a481f5e907",
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
  "parent_chunk_id": "ad57f944-65bb-5fbc-a070-823c4da8b6eb",
  "chunk_index": 30,
  "page_number": 35,
  "page_range": [
    35,
    35
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `452f5453-f766-5889-8b03-ea64ba4fadae`

- vector: dim=3072 · [0.0209, 0.0058, -0.0196, 0.0013, -0.0217, -0.0048, 0.0175, 0.0127, …]

```json
{
  "chunk_id": "452f5453-f766-5889-8b03-ea64ba4fadae",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "3.3 Technology availability",
  "chunk_text": "2 blending | 7 | It is expected that H, would only be able to replace part of the injected coal, resulting in maximum 20% emissions reduction. | The limited emissions reduction means that H2 injection into BFs can only ever be a transition technology to deeper decarbonisation. | | H, DRI | 7 | Emissions reduction potential depends on the share of H2 and whether the H, is from low carbon sources. Assuming 100% green H2, emissions reduction can be >90%, with residual emissions from carbon sources for steelmaking, graphite electrodes and limestone. | Low cost renewable electricity provides a cost\n\n… [+1165 more chars]",
  "content_hash": "cecdfa8a1a988efc81b6b26170035cbaaca8ab11742e222797e6b67650b4f3b1",
  "token_count": 440,
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
  "chunk_index": 31,
  "page_number": 35,
  "page_range": [
    35,
    36
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `345c8e44-03e4-5c99-972b-fe3fde487ad1`

- vector: dim=3072 · [0.0092, 0.0157, -0.0081, -0.0041, -0.0126, -0.0289, 0.0210, 0.0048, …]

```json
{
  "chunk_id": "345c8e44-03e4-5c99-972b-fe3fde487ad1",
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
  "chunk_index": 32,
  "page_number": 36,
  "page_range": [
    36,
    36
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "section_heading": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets",
  "chunk_text": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets\n\nBefore exploring future pathways for the Indian steel sector, it is worth outlining the structure of existing \nassets. Principally, we are concerned with (a) the technological make-up and (b) lifetime of the existing \nassets, as these two factors will be most influential in setting the future direction of the Indian steel sector.\nThe current make-up of India’s iron and steelmaking facilities shows an accelerating trend towards larger, \nintegrated steel plants using blast furnace, basic oxygen furnace and electric\n\n… [+2781 more chars]",
  "content_hash": "652c1255877c80ec432f920a3465b19621ab67b21ca5730ecadadf5f0303e501",
  "token_count": 717,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `4572236d-ca35-52ee-9063-3648b85c059c`

- vector: dim=3072 · [0.0185, 0.0005, -0.0118, 0.0029, -0.0200, -0.0180, -0.0224, 0.0061, …]

```json
{
  "chunk_id": "4572236d-ca35-52ee-9063-3648b85c059c",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets",
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
  "parent_chunk_id": "e6cd6a41-86ff-5f98-a83a-6d4c139a91f4",
  "chunk_index": 33,
  "page_number": 38,
  "page_range": [
    38,
    38
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `0ec0cc77-7e2b-5815-b705-fd2551d61ef1`

- vector: dim=3072 · [-0.0129, 0.0097, -0.0129, -0.0166, -0.0382, -0.0153, -0.0339, 0.0190, …]

```json
{
  "chunk_id": "0ec0cc77-7e2b-5815-b705-fd2551d61ef1",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4 TRANSITION PATHWAY — Transition Pathway — 4.1 Structure of Indian steel assets",
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
  "parent_chunk_id": "e6cd6a41-86ff-5f98-a83a-6d4c139a91f4",
  "chunk_index": 34,
  "page_number": 39,
  "page_range": [
    39,
    40
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "4.2 Technology option assessment\n\nAfter understanding the existing technology make-up of the Indian steel sector, it is necessary to \nunderstand how future lower emission technologies could compete, in terms of both costs, as well as \nbroader suitability (resource availability, import / export impacts). TERI and ETC have undertaken detailed \ntechnology assessments for the Indian and global steel sector,5 which will inform the conclusions in this \nsection. \nBased on this assessment, we observe that the costs of steel production from the main conventional \nroutes in India range from around $300/\n\n… [+4967 more chars]",
  "content_hash": "204aa73529bcfdb74fdff2debd60fb3deed9f285cf20f3fff4f6c657f7550030",
  "token_count": 1311,
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `5a971ca9-e29a-5685-a930-76fc9e31b300`

- vector: dim=3072 · [0.0010, -0.0225, -0.0220, -0.0033, -0.0267, -0.0293, -0.0067, 0.0142, …]

```json
{
  "chunk_id": "5a971ca9-e29a-5685-a930-76fc9e31b300",
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
  "parent_chunk_id": "626d82a2-6ec1-5dad-b507-03e96e3b6925",
  "chunk_index": 35,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `c578deaa-fdae-5ac6-8324-76e9f58c87a4`

- vector: dim=3072 · [0.0152, -0.0259, -0.0155, 0.0236, -0.0325, -0.0342, -0.0053, 0.0001, …]

```json
{
  "chunk_id": "c578deaa-fdae-5ac6-8324-76e9f58c87a4",
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
  "parent_chunk_id": "626d82a2-6ec1-5dad-b507-03e96e3b6925",
  "chunk_index": 36,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `922301fa-18fd-585c-97f4-5dbf7f040360`

- vector: dim=3072 · [0.0133, -0.0213, -0.0098, 0.0329, -0.0355, -0.0397, 0.0086, 0.0150, …]

```json
{
  "chunk_id": "922301fa-18fd-585c-97f4-5dbf7f040360",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "Figure 16: Costs of steel production by route6 \n Source: TERI analysis based on (IEA, 2019) and (MPP, 2021) 6\t BF-BOF = Blast Furnace – Basic Oxygen Furnace, Coal DR-EAF = Coal-based Direct Reduction – Electric Arc Furnace, NG DR-EAF = Natural gas-based \nDirect Reduction – Electric Arc Furnace, SR-BOF CCUS = Smelting Reduction – Basic Oxygen Furnace with Carbon Capture, Usage and or Storage, H2 \nDR-EAF = Hydrogen-based Direct Reduction – Electric Arc Furnace, MOE-EAF = Molten Oxide Electrolysis – Electric Arc Furnace. \n0\n100\n200\n300\n400\n500\n600\nBF-BOF\nCoal DR-EAF\nNG DR-EAF\nSR-BOF\nCCUS\nH2 DR-EA\n\n… [+1182 more chars]",
  "content_hash": "ddc5ff3986bd920e5874891e5fa06d073f7728d7d2e63bd50bbd581926cdbc89",
  "token_count": 442,
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
  "page_number": 41,
  "page_range": [
    41,
    42
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `cb53d3e7-4a87-5102-aab3-7b787a9cd004`

- vector: dim=3072 · [0.0258, -0.0112, -0.0138, 0.0049, -0.0298, -0.0586, 0.0065, 0.0217, …]

```json
{
  "chunk_id": "cb53d3e7-4a87-5102-aab3-7b787a9cd004",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "4.2 Technology option assessment",
  "chunk_text": "One key sensitivity to explore in a little more detail is how the cost of hydrogen would impact their relative\ncompetitiveness and how falling costs of green hydrogen could change this over time. In Figure 17, we present the range of costs for a smelting reduction plant with CCUS, as well as declining\ncosts of steel produced via the hydrogen direct reduction route, based on declining costs of hydrogen. With\ncosts in excess of $4/kg today, we can see that hydrogen direct reduction is consistently more expensive\nthan the smelting reduction route. However, as costs of green hydrogen start to fall\n\n… [+583 more chars]",
  "content_hash": "7e6bd12d95c5af98b4610a3b7c8076fbaaf7063f90b54230a207d69c29f4440f",
  "token_count": 295,
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
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `fbba2519-b45b-50c7-8297-7a057fbf1cfe`

- vector: dim=3072 · [0.0012, -0.0144, -0.0137, 0.0013, -0.0512, -0.0406, 0.0036, 0.0167, …]

```json
{
  "chunk_id": "fbba2519-b45b-50c7-8297-7a057fbf1cfe",
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
  "chunk_index": 39,
  "page_number": 42,
  "page_range": [
    42,
    43
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `3eddf45e-793a-59d4-a15d-3baedfe3dcc8`

- vector: dim=3072 · [0.0173, -0.0073, -0.0155, -0.0025, -0.0481, -0.0124, 0.0030, 0.0254, …]

```json
{
  "chunk_id": "3eddf45e-793a-59d4-a15d-3baedfe3dcc8",
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
  "chunk_index": 40,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `f59ea535-f03f-55f6-b659-02ef03481ecf`

- vector: dim=3072 · [-0.0001, -0.0038, -0.0152, 0.0021, -0.0363, -0.0073, 0.0021, 0.0273, …]

```json
{
  "chunk_id": "f59ea535-f03f-55f6-b659-02ef03481ecf",
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
  "chunk_index": 41,
  "page_number": 44,
  "page_range": [
    44,
    44
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `7639440e-35ef-5f4e-80e9-7b798dc70567`

- vector: dim=3072 · [0.0105, -0.0090, -0.0134, 0.0045, -0.0415, -0.0177, 0.0025, 0.0105, …]

```json
{
  "chunk_id": "7639440e-35ef-5f4e-80e9-7b798dc70567",
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
  "chunk_index": 42,
  "page_number": 45,
  "page_range": [
    45,
    45
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `478beb0a-08a6-5fbf-8374-5fa74ac5679a`

- vector: dim=3072 · [0.0195, -0.0073, -0.0066, 0.0253, -0.0448, -0.0043, -0.0017, 0.0411, …]

```json
{
  "chunk_id": "478beb0a-08a6-5fbf-8374-5fa74ac5679a",
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
  "chunk_index": 43,
  "page_number": 45,
  "page_range": [
    45,
    48
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `d131021e-32cc-54a3-a56e-0023754ea85d`

- vector: dim=3072 · [0.0264, 0.0074, -0.0160, -0.0032, -0.0356, 0.0056, -0.0050, 0.0088, …]

```json
{
  "chunk_id": "d131021e-32cc-54a3-a56e-0023754ea85d",
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
  "chunk_index": 44,
  "page_number": 48,
  "page_range": [
    48,
    49
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `0c93286e-0250-566d-8c19-ab29b02e332c`

- vector: dim=3072 · [-0.0025, -0.0049, -0.0085, 0.0027, -0.0244, -0.0123, 0.0104, -0.0124, …]

```json
{
  "chunk_id": "0c93286e-0250-566d-8c19-ab29b02e332c",
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
  "chunk_index": 45,
  "page_number": 49,
  "page_range": [
    49,
    49
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `051bfdc0-b1b0-542d-8801-25380dd83cd1`

- vector: dim=3072 · [0.0081, -0.0085, -0.0167, 0.0049, -0.0389, -0.0140, 0.0182, 0.0077, …]

```json
{
  "chunk_id": "051bfdc0-b1b0-542d-8801-25380dd83cd1",
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
  "chunk_index": 46,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `8537da82-5b00-52e1-a060-fabb8d14a1b1`

- vector: dim=3072 · [0.0265, 0.0028, -0.0215, 0.0183, -0.0010, -0.0021, 0.0086, -0.0031, …]

```json
{
  "chunk_id": "8537da82-5b00-52e1-a060-fabb8d14a1b1",
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
  "chunk_index": 47,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `edc78c62-5e99-5e47-a15e-f63ecdb06e56`

- vector: dim=3072 · [0.0118, 0.0279, -0.0180, -0.0079, -0.0129, -0.0230, 0.0033, 0.0076, …]

```json
{
  "chunk_id": "edc78c62-5e99-5e47-a15e-f63ecdb06e56",
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
  "chunk_index": 48,
  "page_number": 51,
  "page_range": [
    51,
    51
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `67611954-cfe9-55ba-8bca-76490fd82e86`

- vector: dim=3072 · [0.0041, -0.0012, -0.0094, 0.0157, -0.0397, -0.0196, -0.0085, 0.0056, …]

```json
{
  "chunk_id": "67611954-cfe9-55ba-8bca-76490fd82e86",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.6\t Future-proof new capacity",
  "chunk_text": "An important consideration for low carbon steelmaking routes in India is the lifetime of the plants and \nthe possibility of retrofit in the coming decades. Steel plants have long lifetimes (30 years plus), resulting \nin significant potential for emissions lock-in for plants being built in the coming years, when low carbon \noptions might not be commercially available.\nFigure 25 illustrates two potential transition pathways for the leading technologies discussed earlier. \nFor the hydrogen route, gas-based capacity could be built in the 2020s, using natural gas or coal-based \nsyngas, which is mor\n\n… [+1025 more chars]",
  "content_hash": "7bacc137504b8daffcf830a7667fb7086a950a2b083850bc3739bcb67b4e5754",
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
  "chunk_index": 49,
  "page_number": 51,
  "page_range": [
    51,
    52
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `13e50e3e-0967-5c17-b2b7-513e14e65f6c`

- vector: dim=3072 · [0.0155, -0.0142, -0.0117, 0.0041, -0.0472, 0.0026, -0.0477, 0.0074, …]

```json
{
  "chunk_id": "13e50e3e-0967-5c17-b2b7-513e14e65f6c",
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
  "chunk_index": 50,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `4c913f94-b6f1-5aab-864c-78be629b895c`

- vector: dim=3072 · [0.0124, -0.0002, -0.0190, 0.0055, -0.0265, -0.0074, 0.0125, 0.0141, …]

```json
{
  "chunk_id": "4c913f94-b6f1-5aab-864c-78be629b895c",
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
  "chunk_index": 51,
  "page_number": 52,
  "page_range": [
    52,
    53
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `95e1bd9a-5eaf-5d4e-afbb-a99e7dfa3b35`

- vector: dim=3072 · [-0.0027, -0.0211, -0.0004, -0.0006, -0.0084, -0.0137, -0.0473, 0.0143, …]

```json
{
  "chunk_id": "95e1bd9a-5eaf-5d4e-afbb-a99e7dfa3b35",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "5.9\t Implement a carbon border tariff",
  "chunk_text": "Steel, a carbon intensive product which is also heavily traded globally, has found a lot of attention in \nrecent years in the trade environment policy discourses. For example, the EU green deal mentions \nimposition of Carbon Border Adjustment Mechanism (CBAM), to prevent carbon leakage while creating \nlevel playing field in the EU where steel is one of the few sectors that will come under this measure. It may \nbe worth exploring similar import restrictions on steel imports to India originating from countries having \nFigure 26: Carbon border adjustment\ndomestic industry during transition\n250\n0\n\n\n… [+2155 more chars]",
  "content_hash": "5625e2874e1140fdcb0998651492a927172f82dc8f95872541afece224474971",
  "token_count": 572,
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
  "page_number": 53,
  "page_range": [
    53,
    55
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `89834947-b0e6-55bc-88a2-f320c4d86224`

- vector: dim=3072 · [0.0262, -0.0235, -0.0160, 0.0046, -0.0191, -0.0154, -0.0024, 0.0006, …]

```json
{
  "chunk_id": "89834947-b0e6-55bc-88a2-f320c4d86224",
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
  "chunk_index": 53,
  "page_number": 56,
  "page_range": [
    56,
    56
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `4af5dae5-3e9a-5f3e-a997-d7bd7fcce5af`

- vector: dim=3072 · [0.0132, 0.0065, -0.0106, 0.0142, -0.0057, -0.0047, 0.0089, -0.0008, …]

```json
{
  "chunk_id": "4af5dae5-3e9a-5f3e-a997-d7bd7fcce5af",
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
  "chunk_index": 54,
  "page_number": 57,
  "page_range": [
    57,
    57
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `794200f4-54f2-5b05-a50b-185635f3f244`

- vector: dim=3072 · [0.0209, 0.0065, -0.0145, 0.0133, -0.0195, -0.0060, 0.0036, 0.0011, …]

```json
{
  "chunk_id": "794200f4-54f2-5b05-a50b-185635f3f244",
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
  "chunk_index": 55,
  "page_number": 57,
  "page_range": [
    57,
    57
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `435e0044-b723-5726-b8ac-c3f3bb3f2a92`

- vector: dim=3072 · [0.0144, 0.0179, -0.0085, 0.0159, 0.0055, -0.0155, -0.0067, 0.0086, …]

```json
{
  "chunk_id": "435e0044-b723-5726-b8ac-c3f3bb3f2a92",
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
  "chunk_index": 56,
  "page_number": 57,
  "page_range": [
    57,
    58
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `25f58c8d-2e8a-5d5a-bdcf-e6a65547d180`

- vector: dim=3072 · [0.0288, 0.0096, -0.0103, -0.0004, 0.0094, -0.0032, -0.0073, 0.0168, …]

```json
{
  "chunk_id": "25f58c8d-2e8a-5d5a-bdcf-e6a65547d180",
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
  "chunk_index": 57,
  "page_number": 58,
  "page_range": [
    58,
    58
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
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
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `aec6a648-0987-5e58-828a-b8d5fe9c0a40`

- vector: dim=3072 · [0.0284, 0.0237, -0.0107, 0.0295, 0.0069, -0.0076, 0.0080, 0.0116, …]

```json
{
  "chunk_id": "aec6a648-0987-5e58-828a-b8d5fe9c0a40",
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
  "chunk_index": 58,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `faa68e5f-7f42-53ed-9dff-415735df20c3`

- vector: dim=3072 · [0.0424, 0.0219, -0.0050, 0.0089, -0.0079, 0.0029, 0.0077, 0.0053, …]

```json
{
  "chunk_id": "faa68e5f-7f42-53ed-9dff-415735df20c3",
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
  "chunk_index": 59,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```

## Child · `e28042e8-3ff5-59c9-8320-9d55a96eca56`

- vector: dim=3072 · [0.0291, 0.0225, -0.0110, -0.0124, 0.0037, -0.0147, 0.0107, 0.0045, …]

```json
{
  "chunk_id": "e28042e8-3ff5-59c9-8320-9d55a96eca56",
  "document_id": "achieving_green_steel_roadmap_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Achieving_Green_Steel_Roadmap.pdf",
  "section_heading": "Conclusions",
  "section_type": "references",
  "chunk_text": "(2017). World Development Indicators. \nWSA. (2018). Steel Statistical Yearbook 2018. \nWSA. (2019). Towards a net-zero emissions steel industry. Retrieved from https://iea-industry.org/app/uploads/5- Ekdahl-Towrds-a-net-zero-emissions-steel-industry.pdf\nWSA. (2020a). World Steel in figures. Retrieved 2020, from World Steel Association: https://www.worldsteel.org/en/\ndam/jcr:f7982217-cfde-4fdc-8ba0-795ed807f513/World%2520Steel%2520in%2520Figures%25202020i.pdf\nWSA. (2020b). Steel Statistical Yearbook 2020 Concise Version. Retrieved from https://www.worldsteel.org/en/dam/\njcr:5001dac8-0083-46f3-aa\n\n… [+187 more chars]",
  "content_hash": "5effa822ee4ac0c35e4344d989baad603f562b0cee80b166be327eeea0bb169c",
  "token_count": 247,
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
  "chunk_index": 60,
  "page_number": 59,
  "page_range": [
    59,
    60
  ],
  "created_at": "2026-06-26T05:47:11.935944+00:00",
  "updated_at": "2026-06-26T05:47:11.935944+00:00"
}
```
