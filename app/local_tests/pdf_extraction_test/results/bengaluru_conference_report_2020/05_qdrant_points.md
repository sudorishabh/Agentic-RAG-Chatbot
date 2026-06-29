# Qdrant points — Bengaluru-Conference-Report_2020.pdf

- points (rows upserted): **67**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `8e9fddea-d91f-5130-9e4d-6b5d90aac302`

- vector: dim=3072 · [0.0007, -0.0232, -0.0152, -0.0312, 0.0023, 0.0018, 0.0122, 0.0100, …]

```json
{
  "chunk_id": "8e9fddea-d91f-5130-9e4d-6b5d90aac302",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "ASSOCHAM — Celebrating 100 Years",
  "chunk_text": "teri\nTHE ENERGY AND RESOURCES INSTITUTE\nCreating Innovative Solutions for a Sustainable Future\n\nREPORT OF THE CONFERENCE ON APPROACHES TO SHAPING CLIMATE RESILIENT AGRICULTURE\n\n28th February 2020, Bengaluru, India\n\nOrganized by\nThe Energy and Resources Institute (TERI)\n&\nThe Associated Chambers of Commerce of India (ASSOCHAM)\n\nREPORT OF THE CONFERENCE ON APPROACHES TO SHAPING CLIMATE RESILIENT AGRICULTURE — Authors\n\nRhea Puri . Suruchi Bhadwal\n\nReviewed by\nD N Narasimha Raju",
  "content_hash": "ceaa11f3e29fa6fb4115ac990bc8c48551f95255daf95a461f1615a2684801d3",
  "token_count": 130,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    3
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `c93c864f-a9c5-5ae3-a7c8-9bed9f22c890`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c93c864f-a9c5-5ae3-a7c8-9bed9f22c890",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Table of Contents",
  "chunk_text": "Table of Contents\n\n| INTRODUCTION | 6 |\n| --- | --- |\n| WELCOME ADDRESS BY MR S. SAMPATHRAMAN, ASSOCHAM KARNATAKA CHAPTER | 7 |\n| CONTEXT SETTING BY MR D N NARASIMHA RAJU, DIRECTOR, SOUTHERN REGIONAL CENTRE, TERI | 8 |\n| INAUGURAL ADDRESS BY SHRI B S YEDIYURUPPA, HONOURABLE CHIEF MINISTER OF KARNATAKA | 9 |\n| VOTE OF THANKS BY MR R.R RASHMI, DISTINGUISHED FELLOW & PROGRAMME DIRECTOR, TERI | 10 |\n| SESSION 1: EXPOSURE TO CLIMATIC RISKS: DEVELOPING AN UNDERSTANDING OF THE RISKS AT |  |\n| THE SUB-NATIONAL SCALE | 11 |\n| 1.1 Introduction - Dr K J Ramesh | 11 |\n| 1.2 Impact of climate change on agr\n\n… [+2376 more chars]",
  "content_hash": "a1c1f4c448de27b2e9e025babc945824fef3b88525d2b34eaaa8f2530d109f1a",
  "token_count": 998,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `6e5b246d-e3ae-55dc-8deb-064a6cf66064`

- vector: dim=3072 · [0.0291, -0.0372, 0.0025, -0.0280, -0.0162, -0.0515, 0.0208, 0.0517, …]

```json
{
  "chunk_id": "6e5b246d-e3ae-55dc-8deb-064a6cf66064",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Table of Contents",
  "chunk_text": "| INTRODUCTION | 6 |\n| --- | --- |\n| WELCOME ADDRESS BY MR S. SAMPATHRAMAN, ASSOCHAM KARNATAKA CHAPTER | 7 |\n| CONTEXT SETTING BY MR D N NARASIMHA RAJU, DIRECTOR, SOUTHERN REGIONAL CENTRE, TERI | 8 |\n| INAUGURAL ADDRESS BY SHRI B S YEDIYURUPPA, HONOURABLE CHIEF MINISTER OF KARNATAKA | 9 |\n| VOTE OF THANKS BY MR R.R RASHMI, DISTINGUISHED FELLOW & PROGRAMME DIRECTOR, TERI | 10 |\n| SESSION 1: EXPOSURE TO CLIMATIC RISKS: DEVELOPING AN UNDERSTANDING OF THE RISKS AT |  |\n| THE SUB-NATIONAL SCALE | 11 |\n| 1.1 Introduction - Dr K J Ramesh | 11 |\n| 1.2 Impact of climate change on agriculture - Mr T K A\n\n… [+1007 more chars]",
  "content_hash": "1b7a173bd3879230275f9e8615668571c6a215d1b8e5e357e7013183503aed6d",
  "token_count": 550,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "c93c864f-a9c5-5ae3-a7c8-9bed9f22c890",
  "chunk_index": 1,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `0763bf19-b308-57d3-a801-ff1968840fd9`

- vector: dim=3072 · [0.0159, -0.0226, -0.0006, -0.0157, -0.0266, -0.0660, 0.0126, 0.0359, …]

```json
{
  "chunk_id": "0763bf19-b308-57d3-a801-ff1968840fd9",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Table of Contents",
  "chunk_text": "|\n| 3.1 Introduction - Mr R R Rashmi. | 20 |\n| 3.2 Schemes for Resilient Agriculture - Dr Sandeep Dave | 21 |\n| 3.3 State driven initiatives - Dr K H Vinaykumar | 21 | | 3.4 Need for policies | 22 |\n| 3.5 Conclusion | 23 |\n| SESSION 4: CASE STUDIES SHOWCASING SUSTAINABLE AGRICULTURE PRACTICES (INCLUDING INTEGRATED FARMING SYSTEMS MODELS) IN EMERGING CLIMATE CHANGE SCENARIOS | 24 |\n| 4.1 Introduction - Dr Ashok Dalwai | 25 |\n| 4.2 Case study on Climate Resilient Agriculture Household, Telangana - Dr B Siva Prasad | 25 |\n| 4.3 Promoting the use of agro-meteorological information - Dr P Vijaya Ku\n\n… [+917 more chars]",
  "content_hash": "99186a7916714fa1e32561cf9f27cd4fa8b11c6333c4fbe90f2d526a8c6f6234",
  "token_count": 504,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "c93c864f-a9c5-5ae3-a7c8-9bed9f22c890",
  "chunk_index": 2,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `34a19142-7d4b-577b-90cd-15f5d566cbc5`

- vector: dim=3072 · [-0.0137, -0.0181, 0.0045, -0.0055, 0.0104, -0.0276, 0.0187, 0.0219, …]

```json
{
  "chunk_id": "34a19142-7d4b-577b-90cd-15f5d566cbc5",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "With a focus on the Paris Agreement on climate change, the Sendai framework on\ndisaster risk reduction and the sustainable development goals, the conference will\naddress the issues that fall within the ambit of these international discourses that\nhave implications at the national and subnational scales.\n\nThe following listed targets under Goal 13 of \"Climate Action\" under Sustainable\nDevelopment Goals are planned to be addressed:\n\n· Strengthen resilience and adaptive capacity to climate-related hazards and\nnatural disasters in all countries.\n\n· Integrate climate change measures into national p\n\n… [+1057 more chars]",
  "content_hash": "06d55d65f623fb3aa3fab95bddad0120d8a74841aaf3a4a8a0e07c9aaf97ee4c",
  "token_count": 311,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 3,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `22ab97bd-3ecc-5686-a920-a9727cc410ec`

- vector: dim=3072 · [0.0187, -0.0173, -0.0077, -0.0363, 0.0043, -0.0206, 0.0129, 0.0155, …]

```json
{
  "chunk_id": "22ab97bd-3ecc-5686-a920-a9727cc410ec",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Welcome Address by Mr S. Sampathraman, ASSOCHAM Karnataka Chapter",
  "chunk_text": "Mr S Sampathraman welcomed the participants and thanked the Honourable\nChief Minister for sparing his valuable time to come to the Conference. In his\naddress, he made the following observations:\n\nWe human beings are now returning to the preservation of nature. We are\nworshippers of nature for tens of thousands of years. Controlling the damage is\nabsolutely important so that the nature does not punish us more. The essence\nof the conference sessions highlights upon taking measures and steps towards\ncontrolling the damage caused to our nature. Karnataka is a pioneer in digital\ntechnology and has \n\n… [+532 more chars]",
  "content_hash": "73b45121c1465962549018b0c76a0a38530be572578c8a1d5b7da74c1b65f292",
  "token_count": 235,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 4,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `f6a3e2fe-e821-5ecb-b16a-d3fda63976e2`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f6a3e2fe-e821-5ecb-b16a-d3fda63976e2",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Context setting by Mr D N Narasimha Raju, Director, Southern Regional Centre, TERI",
  "chunk_text": "Context setting by Mr D N Narasimha Raju, Director, Southern Regional Centre, TERI\n\nAt the outset, he expressed gratitude to the Hon'ble Chief Minister for his presence and to inaugurate\nthe Conference.\n\nThe subject of Climate change encompasses many disciplines of science. It is not limited to\nenvironment sector but covers aspects of equity, economy and technology.\n\nChange is the law of nature and therefore, climate change is a natural phenomenon. However,\nresearch has shown that human actions have contributed in great measure toclimate change. There\nis recorded evidence that India's climate \n\n… [+2949 more chars]",
  "content_hash": "1e966974645fc8c2e123e365f091e23f2808e43f7e9ede3d89b8f68618808f44",
  "token_count": 724,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `7865368f-3458-5457-81ca-195ecb2ba78d`

- vector: dim=3072 · [0.0243, -0.0141, -0.0063, -0.0347, -0.0069, -0.0326, -0.0119, 0.0200, …]

```json
{
  "chunk_id": "7865368f-3458-5457-81ca-195ecb2ba78d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Context setting by Mr D N Narasimha Raju, Director, Southern Regional Centre, TERI",
  "chunk_text": "At the outset, he expressed gratitude to the Hon'ble Chief Minister for his presence and to inaugurate\nthe Conference.\n\nThe subject of Climate change encompasses many disciplines of science. It is not limited to\nenvironment sector but covers aspects of equity, economy and technology.\n\nChange is the law of nature and therefore, climate change is a natural phenomenon. However,\nresearch has shown that human actions have contributed in great measure toclimate change. There\nis recorded evidence that India's climate is changing and this change is likely to accelerate. This is\nwitnessed in events suc\n\n… [+1294 more chars]",
  "content_hash": "bb391f51df52e6b9f6f8dd50ac4fb7a68579a1068a79643dc73207abf5119a7d",
  "token_count": 398,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "f6a3e2fe-e821-5ecb-b16a-d3fda63976e2",
  "chunk_index": 5,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `bc277d51-d174-52d9-9ac1-dfc2c5aeaa9f`

- vector: dim=3072 · [0.0148, -0.0266, 0.0009, -0.0133, -0.0044, -0.0272, 0.0024, -0.0107, …]

```json
{
  "chunk_id": "bc277d51-d174-52d9-9ac1-dfc2c5aeaa9f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Context setting by Mr D N Narasimha Raju, Director, Southern Regional Centre, TERI",
  "chunk_text": "Promoting forestry and Agro-forestry on a massive\nscale will create the carbon sink and bring down the CO2 levels. In recent years, Karnataka has been\nable to increase forest cover and has taken a major initiative to promote Agro-forestry in farmer's\nfields. In Karnataka, over the years, the contribution of agriculture to GSDP has come down to 7.73per\ncent (2018-19). A large population is dependent on agriculture for employment and income. The\nState's vulnerability is high. It has faced more droughts in the past. The State Natural Disaster\nMonitoring Centre has developed a Composite Index for \n\n… [+1228 more chars]",
  "content_hash": "d92b3d4e05478b31be32ce2d19ec7f380477a015dde89db3c28f9f1bc8934cc1",
  "token_count": 363,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "f6a3e2fe-e821-5ecb-b16a-d3fda63976e2",
  "chunk_index": 6,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `425d8427-4cd8-501a-af40-9670e1f3c4a5`

- vector: dim=3072 · [0.0263, -0.0250, 0.0001, -0.0460, 0.0117, -0.0439, 0.0282, 0.0306, …]

```json
{
  "chunk_id": "425d8427-4cd8-501a-af40-9670e1f3c4a5",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Inaugural Address by Shri B S Yediyuruppa, Honourable Chief Minister of Karnataka",
  "chunk_text": "In his address, Shri B S Yediyurappa, Honourable Chief Minister, Government of Karnataka, noted\nthe presence of participants and speakers and spoke about the state having faced major flood and\ndrought issues in the past decade. He stated that during 2019, as many as 103 talukas of 22 districts\nwere flood affected and 49 talukas of 18 districts had faced drought. The State has witnessed\nunforeseen crop loss due to the drought and landslides in 2018-19. This is alarming and a high time\nto think of long term solutions locally & globally. According to him, it is extremely imperative to\nhave a scie\n\n… [+998 more chars]",
  "content_hash": "c27d0b953b6bced2c6bdbb6ba5f24409fc91bbe2f1d3a061536b0970684d24c2",
  "token_count": 342,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 7,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `af8e94c8-426a-5adb-bc7e-3df31b41034f`

- vector: dim=3072 · [0.0099, -0.0308, -0.0021, -0.0349, 0.0101, -0.0387, 0.0249, 0.0218, …]

```json
{
  "chunk_id": "af8e94c8-426a-5adb-bc7e-3df31b41034f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Vote of Thanks by Mr R.R Rashmi, Distinguished Fellow & Programme Director, TERI",
  "chunk_text": "Mr R R Rashmi expressed gratitude to the Honourable Chief Minister for having\ntaken time off to come & bless the Conference by inaugurating it. He noted\nthat Chief Minister has taken deep interest in the subject with the interest of the\nState in mind. The topic is indeed a burning issue of our times, as mentioned by\nthe Chief Minister. It affects a large number of agriculturists. With inspiration &\nvision of Chief Minister, the Conference will deliberate and contribute in a small\nmeasure to achieve goals set for the state.\n\nHe acknowledged the presence of Central Government departments, other \n\n… [+1193 more chars]",
  "content_hash": "988c1fb55150e8b843596d46eb5583163c8ade9f1fe3047b2e5f1b698ddf26e3",
  "token_count": 388,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 8,
  "page_number": 10,
  "page_range": [
    10,
    11
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `fc991ff1-bc7c-5041-9450-25a3d04260e8`

- vector: dim=3072 · [-0.0228, -0.0003, 0.0012, 0.0168, 0.0036, -0.0351, -0.0030, -0.0108, …]

```json
{
  "chunk_id": "fc991ff1-bc7c-5041-9450-25a3d04260e8",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "₹ TCI — Orllis Mails Partners — Jagran — EN16 February 2000% — SEHAM — M — SSI — M — ASSO — DE.i & Ranein — .1 Introduction - Dr K J Ramesh",
  "chunk_text": "The impact of climate change has been noticed in agriculture, water resources, public health\nsectors and in extreme events. India is good in predicting occurrence of extreme events. To have a\nclimate ready future towards any development plan or any ground action, it is imperative to have\na scientifically robust, and sector specific risk profiling of the hazards set up both at baseline and\nfuture. The existing knowledge, success stories from different states in mainstreaming climate\n\ninformation in planning is necessary and there is a need for providing high resolution climate\ninformation for l\n\n… [+631 more chars]",
  "content_hash": "381d373c8f0778baffbc5de3a6c432af4bc319fdd6f1ad4b574495098f46ce2f",
  "token_count": 227,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 9,
  "page_number": 11,
  "page_range": [
    11,
    12
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `abe70d61-a166-54ce-aa86-842201ce03ab`

- vector: dim=3072 · [0.0055, -0.0103, -0.0069, -0.0200, 0.0021, -0.0042, -0.0069, -0.0096, …]

```json
{
  "chunk_id": "abe70d61-a166-54ce-aa86-842201ce03ab",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.2 Impact of climate change on agriculture - Mr T K Anil Kumar:",
  "chunk_text": "Climate change is real. Karnataka is facing the adverse impacts of climate change and during\nthe last 15-20 years there have been many droughts in different parts of the state. While from a\nclimate disaster perspective, many steps have been taken, there are many gaps. The 15th Finance\nCommission considered very broad parameters at State level in making their recommendations\non mitigation and disaster relief fund. There are wide variations at State level. We need to take into\naccount the granularity of the climate impacts, at the village and gram panchayat level, to make\nrelevant solutions. Mai\n\n… [+448 more chars]",
  "content_hash": "11c22aa79fb26fd5ff01c23b5da05b1ce4218cf880d3c7807c0a4e7e28230b3d",
  "token_count": 204,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 10,
  "page_number": 12,
  "page_range": [
    12,
    12
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `e1c79bb2-bba7-5d63-b414-b5a6ff65bf67`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e1c79bb2-bba7-5d63-b414-b5a6ff65bf67",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.3 Forecasting the weather conditions and provision of updated data - Dr G S Srinivasa Reddy:",
  "chunk_text": "1.3 Forecasting the weather conditions and provision of updated data - Dr G S Srinivasa Reddy:\n\nThe Agriculture and allied activities in India, which provide livelihood to majority of its population,\nis heavily dependent on climatic conditions. The multiple risks associated with Agriculture, weather\ndeviations stand out distinctly. Any deviation from normal condition adversely affects these activities\nand in turn, the socio-economic condition of the population and also the State / National economy.\nIf accurate weather forecasts are given to the farmers in real time, it will help them to take t\n\n… [+2511 more chars]",
  "content_hash": "e246bcac3a46545c26cfde90b9e339f0ef0a586d118abe3d52399ae80f7f9618",
  "token_count": 615,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    12,
    13
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `b9e082c0-02c0-5026-9051-38612b40f056`

- vector: dim=3072 · [-0.0036, -0.0219, 0.0120, -0.0284, -0.0201, -0.0318, 0.0104, 0.0039, …]

```json
{
  "chunk_id": "b9e082c0-02c0-5026-9051-38612b40f056",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.3 Forecasting the weather conditions and provision of updated data - Dr G S Srinivasa Reddy:",
  "chunk_text": "The Agriculture and allied activities in India, which provide livelihood to majority of its population,\nis heavily dependent on climatic conditions. The multiple risks associated with Agriculture, weather\ndeviations stand out distinctly. Any deviation from normal condition adversely affects these activities\nand in turn, the socio-economic condition of the population and also the State / National economy.\nIf accurate weather forecasts are given to the farmers in real time, it will help them to take timely\nand appropriate decision relating to their production plan. India has been undertaking mon\n\n… [+1120 more chars]",
  "content_hash": "022b578013308a6905193561e21db0d7483c90f94fc1f5a4fcb8ec421a75f261",
  "token_count": 323,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "e1c79bb2-bba7-5d63-b414-b5a6ff65bf67",
  "chunk_index": 11,
  "page_number": 12,
  "page_range": [
    12,
    12
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `2ceeeabb-a71d-53ab-bde5-c70c8ef57360`

- vector: dim=3072 · [0.0091, 0.0115, -0.0013, -0.0105, -0.0065, -0.0002, 0.0178, 0.0126, …]

```json
{
  "chunk_id": "2ceeeabb-a71d-53ab-bde5-c70c8ef57360",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.3 Forecasting the weather conditions and provision of updated data - Dr G S Srinivasa Reddy:",
  "chunk_text": "The Karnataka State Natural Disaster Management Centre has set up a dense network of telemetry\nrain gauges up to Gram Panchayat level in 6500 stations which are solar powered and GPS enabled. The process of data collection and dissemination to all the key stakeholders is on real time basis\nand automated which is first in the country. Forecasts are being shared at the gram panchayat level.\nRadars are being procured which will help in the Centre to upgrade to \"now cast\" system, so that\nthe farmers get real-time updates. This system is already being used for disseminating information\non markets, \n\n… [+885 more chars]",
  "content_hash": "3273438159556faaa084c704ce6a3ae122d5fff55f83b786d2489444af58dff6",
  "token_count": 308,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "e1c79bb2-bba7-5d63-b414-b5a6ff65bf67",
  "chunk_index": 12,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `251efb54-1375-589e-b2b5-9173d12f8118`

- vector: dim=3072 · [-0.0133, -0.0086, 0.0069, -0.0066, -0.0115, -0.0204, 0.0177, -0.0326, …]

```json
{
  "chunk_id": "251efb54-1375-589e-b2b5-9173d12f8118",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.4 Impact of Climate Change on Agriculture in Kerala - Mr Harikumar B:",
  "chunk_text": "In Kerala, Agriculture, livestock and fisheries contribute 11% to state gross domestic product (GDP).\nAround 17.15% of the population depends on this sector and 52% of Kerala is under crop cultivation.\nThe state supports diverse ecological conditions and variety of crops- the lowlands have over 600\nvarieties of paddy and highlands have different species and plantation crops.\n\nThe pattern of both monsoons has changed. Rainfall pattern has become unpredictable. During the\n2018 floods, around 11% of area under cultivation was affected and 1/6th of the state's population\nsuffered. Around 58,000 he\n\n… [+1639 more chars]",
  "content_hash": "8222897c54babc9ad93fc57af4b1142ca430f9b1b3caeec3ba17ae7a065ab31d",
  "token_count": 476,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 13,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `0ca4a23b-16fb-556a-850b-6650acbd9263`

- vector: dim=3072 · [-0.0073, -0.0023, -0.0015, 0.0005, 0.0058, -0.0314, -0.0023, -0.0205, …]

```json
{
  "chunk_id": "0ca4a23b-16fb-556a-850b-6650acbd9263",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.5 Measures taken for Climate Change in Tamil Nadu - Mr T Karthikeyan:",
  "chunk_text": "Agriculture is highly integrated into the challenge of climate change. Climate smart agriculture is\nneeded as it is dependent on weather. Failure of rains and occurrence of natural disasters such\nas floods and droughts could lead to crop failures, food insecurity, famine, loss of property and\nlife, mass migration and negative national economic growth. Certain planned adaptive measures\nlike development of genetically adaptive varieties, hybrid seed programme, crop diversification\nprogramme etc. can help in improving the agricultural sector.\n\nTo adapt to climate change, the State of Tamil Nadu i\n\n… [+1254 more chars]",
  "content_hash": "8ba9c5bc2a9e59acb4c41af65dcb865cb9b8b7af93577edf104e66f90d032a52",
  "token_count": 395,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 14,
  "page_number": 14,
  "page_range": [
    14,
    14
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `4c0b959f-6253-5b91-8c82-f8ed7ee4db30`

- vector: dim=3072 · [-0.0192, -0.0095, -0.0049, 0.0120, 0.0001, -0.0134, 0.0002, -0.0167, …]

```json
{
  "chunk_id": "4c0b959f-6253-5b91-8c82-f8ed7ee4db30",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.6 .. 6 Future Projections - Mr Saurabh Bhardwaj:",
  "chunk_text": "The global climate change and variability is manifesting itself in terms of changing regional climate\nvariability and extremes. The extremes are changing, the variability-the hot days and high rainfall\ndays are increasing and simultaneously the dry days are increasing. So at one scale, flooding events\nin some parts are increasing, similarly in some parts, droughts are predominant. This has been an\nindication of global climate change in the variability of climate which is also observed at the regional\nlevel.\n\nAccording to the IPCC Assessment Report 5, if mitigation measures are being taken, the\n\n… [+1607 more chars]",
  "content_hash": "b34f28284d358b02e6b46dc1c8b955818be2e0c7e506a2240e23b312b4b4b383",
  "token_count": 442,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 15,
  "page_number": 14,
  "page_range": [
    14,
    15
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `6ebb334a-5394-5e33-8cbd-e20059d5f7f7`

- vector: dim=3072 · [0.0003, -0.0393, -0.0018, -0.0198, 0.0123, -0.0501, -0.0001, 0.0165, …]

```json
{
  "chunk_id": "6ebb334a-5394-5e33-8cbd-e20059d5f7f7",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.7 Conclusion:",
  "chunk_text": "The Chair noted that the three States have taken many initiatives for Climate Resilient Agriculture.\nRainfall variability, temperature changes and local anomalies have to be addressed. Rainfall in\ncoastal areas and high hills has decreased marginally and in interior areas, increased. While climate\nchange is global in nature, actions have to be local. Making available accurate weather information\nto farmers in advance is the key. Providing data driven information at local level by downscaling\ninformation from global level through Agro-met advisories is needed. This is possible as granularity\nal\n\n… [+1098 more chars]",
  "content_hash": "52803938f58721cea3ebfcd82e539914768408c364400e2fd351b797aa39bf82",
  "token_count": 403,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 16,
  "page_number": 15,
  "page_range": [
    15,
    16
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `ab4b032a-5b0d-5f6f-8936-37394ea71e26`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ab4b032a-5b0d-5f6f-8936-37394ea71e26",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Es — 2.1 L Introduction - Dr S Bhaskar:",
  "chunk_text": "Es — 2.1 L Introduction - Dr S Bhaskar:\n\nClimate change is a reality. The frequency of extreme events is increasing enormously over the\npast two decades. The status of arid and non-arid zones may change. Under the National Action\nplan on Climate Change Agriculture Mission, the focus is on four to five major components aiming\non sustainable development goals. . There is a need to formulate the risk assessment map at the\nnational level, state level and district level.\n\nStudies show that 85% of water is going for irrigation, and in the view of water vulnerability, this\nneeds to be minimized. With\n\n… [+1768 more chars]",
  "content_hash": "7cb142a817d4ef5bcbb1c8bdfa38f0899da636b1da2ca68b0f6a53b21f115873",
  "token_count": 487,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    16,
    17
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `d2b6ecef-0b9f-561e-b49a-1e392bc23b3d`

- vector: dim=3072 · [-0.0174, -0.0088, -0.0023, 0.0315, 0.0213, -0.0181, 0.0123, -0.0057, …]

```json
{
  "chunk_id": "d2b6ecef-0b9f-561e-b49a-1e392bc23b3d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Es — 2.1 L Introduction - Dr S Bhaskar:",
  "chunk_text": "Climate change is a reality. The frequency of extreme events is increasing enormously over the\npast two decades. The status of arid and non-arid zones may change. Under the National Action\nplan on Climate Change Agriculture Mission, the focus is on four to five major components aiming\non sustainable development goals. . There is a need to formulate the risk assessment map at the\nnational level, state level and district level.\n\nStudies show that 85% of water is going for irrigation, and in the view of water vulnerability, this\nneeds to be minimized. With Central Institute for Dry land Agricultu\n\n… [+976 more chars]",
  "content_hash": "5e419d96e619ec938270147233f37d321a92dbbc10a971c9c6f72452b6abaa2e",
  "token_count": 324,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "ab4b032a-5b0d-5f6f-8936-37394ea71e26",
  "chunk_index": 17,
  "page_number": 16,
  "page_range": [
    16,
    17
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `3549ab78-4dd3-5d89-bac1-09e4f360a5db`

- vector: dim=3072 · [-0.0232, -0.0059, -0.0158, 0.0322, 0.0206, -0.0159, -0.0091, -0.0050, …]

```json
{
  "chunk_id": "3549ab78-4dd3-5d89-bac1-09e4f360a5db",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Es — 2.1 L Introduction - Dr S Bhaskar:",
  "chunk_text": "NICRA has also changed definition of vulnerability to a broader concept of risk\nassessment (R.A.) and bringing out reports which help in planning for adaptation. Currently, 250\ndistricts have been identified under high and very high risk category. The climate models need to be developed for India and ICAR is working on Integrated modeling\napproach. A drought and flood resistant variety of rice has been developed. Demonstration of\nClimate Resilient technologies has been taken up in 151 villages in vulnerable districts. Under\ninnovations in Climate Resilient village models, 446 villages have bee\n\n… [+397 more chars]",
  "content_hash": "fce22f01f347ba6f395acf8050956eb408007302408c7189db5fcf424e51c5cf",
  "token_count": 197,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "ab4b032a-5b0d-5f6f-8936-37394ea71e26",
  "chunk_index": 18,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `46be6486-ef05-5235-9e30-e1ac85758ee8`

- vector: dim=3072 · [-0.0063, 0.0188, -0.0135, -0.0176, -0.0011, -0.0213, 0.0233, 0.0015, …]

```json
{
  "chunk_id": "46be6486-ef05-5235-9e30-e1ac85758ee8",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.2 Adoption of Technological Changes- Mr Rajender Kumar Kataria:",
  "chunk_text": "The point of focus should be on how to get the required technologies and deploy them. This can\neither be done through using demonstration projects or collaborating with universities to roll-out\ntheir research to real action on ground.\n\nPresently, a major portion of department's budget goes towards input subsidies; focus should also\nbe on extension to spread use of better technologies, cropping systems, efficient irrigation methods\netc. so that livelihood and income support is better for the farmers.\n\nTechnology demonstration to farmers should be one of the measures to secure a balance between\n\n\n… [+291 more chars]",
  "content_hash": "174ac411e998ce3000ef4076da187c732fa6ef641d3bd28de215f405c53bf5e5",
  "token_count": 169,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 19,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `aca1f6a5-b4d1-5678-9ea2-b527478ffeac`

- vector: dim=3072 · [-0.0143, -0.0138, -0.0108, 0.0015, -0.0092, -0.0265, 0.0152, -0.0178, …]

```json
{
  "chunk_id": "aca1f6a5-b4d1-5678-9ea2-b527478ffeac",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.3 Horticulture - Dr R H Laxman",
  "chunk_text": "Under the National Innovations in Climate Resilient Agriculture (NICRA) Project, seven core\ninstitutions have been identified to carry out the research work and development of adaptation\nstrategies. Similarly, IIHR is one of the core institutions for initiating research work. Agriculture and\nhorticulture will be impacted more by climate variability than the climate change. When crops are\ngrown in various seasons, the critical stages of growing and being subject to abiotic stress becomes\nimportant. In Karnataka, drought like situation was created in July 2019, and in August month,\nnorthern Karn\n\n… [+1777 more chars]",
  "content_hash": "ad30b5576c61be2ac3157e79f76d5befc847186ab2b907e02e1c91ad2351db26",
  "token_count": 470,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 20,
  "page_number": 17,
  "page_range": [
    17,
    18
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `aae1614d-c84f-537e-a219-5de3200e0e2f`

- vector: dim=3072 · [-0.0195, -0.0224, 0.0016, 0.0193, -0.0045, -0.0452, 0.0007, -0.0225, …]

```json
{
  "chunk_id": "aae1614d-c84f-537e-a219-5de3200e0e2f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.4 Impact of Climate Change on Agriculture - Dr. M.B Rajegowda:",
  "chunk_text": "According to the IPCC 20th century report findings, an increase in the global mean temperature is\nobserved by over 0.7%. A decrease in 10% snow since late 1960's and 10-15% reduction in spring/\nsummer ice extent since 1950s has been observed. Similarly, based on the IPCC 21st century\nprojections, global mean temperatures and sea level is projected to rise under all the scenarios.\n\nWorldwide, the precipitation over land has increased by ~1%, but in India monsoon rainfall has\ndecreased by 5-8% and temperature increased by 20% in all summer monsoon rainfall.Climate\nchange is leading to a wide ran\n\n… [+795 more chars]",
  "content_hash": "fc0af01e4763a9c41a405f4ebde2b73662c057448ac192b62e6ee7ad0ed3063f",
  "token_count": 290,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 21,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `771061e9-a997-5328-af87-9bbefe063f4b`

- vector: dim=3072 · [-0.0073, 0.0047, -0.0057, 0.0384, 0.0079, -0.0271, -0.0055, -0.0436, …]

```json
{
  "chunk_id": "771061e9-a997-5328-af87-9bbefe063f4b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "The impacts on agriculture can be direct (change in temperature, fertilization, etc.) and indirect\n(water scarcity, extremes, pests, etc.), will significantly impact agriculture productivity. This is inter-\nconnected with the non-production aspects, which need to be looked at to assess the vulnerability\nof the sector and build resilience - such as transport, storage, processing and retailing.\n\nTogether, these factors impact India's food security. Climate change will have a mix of largely\nnegative, but also some positive impacts for agriculture productivity, by region. According to\nthe studies,\n\n… [+574 more chars]",
  "content_hash": "b47fa301eaedac413e567caae1df38bb35aaf151f6882076883d900bb49ea76c",
  "token_count": 228,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 22,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `8c3f3b89-9e32-50af-a1e4-5f65fc580390`

- vector: dim=3072 · [0.0123, -0.0288, -0.0106, 0.0045, -0.0079, -0.0313, -0.0100, 0.0307, …]

```json
{
  "chunk_id": "8c3f3b89-9e32-50af-a1e4-5f65fc580390",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Adaptation strategies:",
  "chunk_text": "· Replacing the vulnerable crops with potential crops in a phased manner\n\n· Shifting in sowing windows/growing periods\n\n· Change in cropping systems\n\n· Growing only millets in drought prone regions\n\n· Growing long rice in water logging area\n\n· Farm level adaptations- change in timings, inputs crop grown etc\n\n· Increasing the adaptive capacity of farmers\n\n· Early warning/ forecasting systems\n\n· Community watershed management\n\nAlso, while framing the adaptation strategies we should also take into account its co-benefits and\nthe need for it to be communicated to all stakeholders.\n\n2.6 Conclusion \n\n… [+1397 more chars]",
  "content_hash": "dd8694717094da6cc0a0c8362580618e851ee998d8789464dfb771c779c3aeb4",
  "token_count": 464,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 23,
  "page_number": 19,
  "page_range": [
    19,
    20
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `e74efe2a-eafa-57dd-a67b-7c90cc4a62ee`

- vector: dim=3072 · [-0.0298, 0.0151, -0.0056, 0.0094, 0.0043, -0.0278, 0.0023, 0.0015, …]

```json
{
  "chunk_id": "e74efe2a-eafa-57dd-a67b-7c90cc4a62ee",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Ch — ASSOCHAM — ASS — 3.1 Introduction - Mr R R Rashmi:",
  "chunk_text": "Given the challenges, there needs to be a focus on the policy environment, gaps if any and need\nfor further integration. It also seeks to look at the developments in polices at the international level\nincluding the Paris agreement, the Sendai Framework and the SDGs. Implications at the country\nlevel and subnational scales were discussed in the form of India's National Missions on Climate\n\nChange, its Nationally Determined Contributions (NDCs) and the State Action Plans on Climate\nChange (SAPCCs). There is a need for enhanced financial resources, additional scientific knowledge\nand capacity bui\n\n… [+71 more chars]",
  "content_hash": "111eb58e93e47792395c276d514c73583fed77e08a310a6f2f97e7a9dfead0f9",
  "token_count": 136,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 24,
  "page_number": 20,
  "page_range": [
    20,
    21
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `2acafe61-0e12-5a5c-af75-75c1f592c947`

- vector: dim=3072 · [0.0009, 0.0012, -0.0118, -0.0011, 0.0079, 0.0031, 0.0018, -0.0149, …]

```json
{
  "chunk_id": "2acafe61-0e12-5a5c-af75-75c1f592c947",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "3.2 Schemes for Resilient Agriculture - Dr Sandeep Dave:",
  "chunk_text": "Climate Change is one particular phenomenon that unless we take indicative measures we won't\nbe having a sustainable future. Agriculture itself produces nearly 30% of GHGs and is a contributor\nto emissions. Promotion of agriculture can increase emissions. However, Agro-forestry is a way\nof mitigating it as it can act as a dual medicine- on one hand it helps in building the carbon stock\nthrough carbon sink and on the other hand through various species, livelihood of the farmers can\nalso grow. Through the Krishi Aranya Prothsahan Yojana (state driven scheme) Rs. 125 is given per\nsaplings planted\n\n… [+805 more chars]",
  "content_hash": "7d0094140e2d2febfb88d9e5842c8e93a6e2e4bde50782a319a9a304c9aa706d",
  "token_count": 304,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 25,
  "page_number": 21,
  "page_range": [
    21,
    21
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `12cda1d6-2128-56b3-941c-5f713312b00c`

- vector: dim=3072 · [-0.0189, -0.0015, 0.0006, 0.0167, -0.0032, -0.0330, -0.0113, -0.0160, …]

```json
{
  "chunk_id": "12cda1d6-2128-56b3-941c-5f713312b00c",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "3.3 State driven initiatives - Dr K H Vinaykumar:",
  "chunk_text": "Climate Change is predicted to impact India's natural resource base, including water resources,\nforestry and agriculture, through changes in precipitation, temperatures, monsoon timings, and\nextreme events. Among all sectors, agriculture sector is likely to be impacted the most. Agriculture is\nhighly vulnerable to climate change because of its wide exposure through changes in temperature,\nprecipitation, pest attack and diseases.\n\nThe National network project on Climate Change initiated by ICAR has projected a net decline of\n2.5% in agricultural production over the next two to five decades. The\n\n… [+1497 more chars]",
  "content_hash": "04d04ea947306a8bc24065c417f314fce73a977ffadffca72f8fe95708e3b84e",
  "token_count": 398,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 26,
  "page_number": 21,
  "page_range": [
    21,
    22
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `72f0c4ea-a56d-510d-a0c6-b261c3790645`

- vector: dim=3072 · [0.0180, -0.0224, -0.0085, 0.0039, -0.0141, -0.0404, 0.0029, -0.0084, …]

```json
{
  "chunk_id": "72f0c4ea-a56d-510d-a0c6-b261c3790645",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Dr. S. Rajendra Prasad:",
  "chunk_text": "The State has faced many adverse weather conditions in the last few years, however, productivity of\ncrops has not been impacted much. Four areas identified for mitigation are:\n\n· Reducing natural resources run-off;\n\n· Precision crop rating;\n\n· Evaluation of endophytes- use of beneficial microbes for addressing biotic and abiotic stress; and,\n\n· Prediction of pests and diseases.\n\nThe need for policy support in linking up interventions such as subsidy to adoption of prescribed\nmitigation measure by farmers was also highlighted. The revision of criteria for drought declaration\nis framed by the un\n\n… [+257 more chars]",
  "content_hash": "6156c9a80a2f97c3e244b0497eb516a9d39a11e7cbf3992c91107aef41da4269",
  "token_count": 173,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 27,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `b4fbeffb-5caf-5001-b072-fa337f4bfd3f`

- vector: dim=3072 · [-0.0042, 0.0047, -0.0132, -0.0092, -0.0211, 0.0028, 0.0093, -0.0061, …]

```json
{
  "chunk_id": "b4fbeffb-5caf-5001-b072-fa337f4bfd3f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Dr. Amir Bashir Bazaz :",
  "chunk_text": "The land ecosystem transition was identified as a critical component to achieve 1.5 scenarios. It has\nbeen found from a survey of 300 farmers in northern Karnataka that there is need to re-imagine\nextension services. Efficient irrigation, conservation agriculture, improving climate services are\nimportant vehicles that can potentially be used for system change. There is a lot of potential for\nknowledge networks to contribute to adaptation on the ground especially for small and marginal\nfarmers. As knowledge is complex, there is a need to unpack and demystify the knowledge that\nbenefits the peop\n\n… [+603 more chars]",
  "content_hash": "b1e0099d7e24f2b1b9f7424ae179e5cb1b6bb8cb72f8fc7785e4d3ea15dfda96",
  "token_count": 230,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 28,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `f70a1189-90c3-58f7-a11e-147ee8eec248`

- vector: dim=3072 · [0.0104, -0.0105, -0.0035, 0.0056, -0.0273, -0.0436, -0.0062, -0.0422, …]

```json
{
  "chunk_id": "f70a1189-90c3-58f7-a11e-147ee8eec248",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Dr. Raghu Ramulu, Coffee Board :",
  "chunk_text": "In the plantation sector, coffee, tea, rubber and spices cover 3 million hectare and immensely\nintegrate with forest ecosystem in carbon sequestration and biodiversity conservation. India is the\n7th largest producer and 6th largest exporter of coffee. Karnataka Kerala and Tamil Nadu have been\ncultivating coffee over last two centuries with Karnataka producing about 70%. In recent years,\ncoffee is being grown in North East, Andhra Pradesh and Odisha.\n\nIn a multi-country study of Coffee Agro-forestry, India stood top on most parameters. In Coorg\n\narea, coffee grown with multi-species is on a par\n\n… [+765 more chars]",
  "content_hash": "0c0a9688b906658034f2db94794391d2a9bf2756fb125fd4e5e130cfed938856",
  "token_count": 274,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 29,
  "page_number": 22,
  "page_range": [
    22,
    23
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `22c24e49-af81-5071-b931-b9c6caf8f39d`

- vector: dim=3072 · [-0.0185, -0.0162, -0.0071, 0.0182, -0.0225, -0.0453, 0.0021, -0.0024, …]

```json
{
  "chunk_id": "22c24e49-af81-5071-b931-b9c6caf8f39d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Situation across the coffee growing countries:",
  "chunk_text": "· Brazil- New coffee areas shifted to Northeast, but Frosts are becoming rare.\n\n· Central America- Leaf rust flare up during 2012-13, resulting in about 30% crop loss\n\n· Mexico- Berry borer incidence seen even at higher elevations\n\n· Guatemala and Honduras: Rise in temperature. in the last 2-3 decades and decline in rainfall by\nupto 15%\n\n· India - severe flare up of white stem borer twice during the last one decade; shift in South-West\nmonsoon pattern; rise in minimum temperature.\n\nThe shaded coffee plants with native trees are strong carbon sinks. Coffee production is\ncontributing significant\n\n… [+1551 more chars]",
  "content_hash": "e5c48b5eb960e6548f527d1a2859e58041ba1a8399e107767aa04b643c6000e7",
  "token_count": 462,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 30,
  "page_number": 23,
  "page_range": [
    23,
    24
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `4b585fae-807c-585b-b86c-c5002833edbe`

- vector: dim=3072 · [0.0102, -0.0216, -0.0055, -0.0291, 0.0033, -0.0215, 0.0002, 0.0231, …]

```json
{
  "chunk_id": "4b585fae-807c-585b-b86c-c5002833edbe",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Speakers:",
  "chunk_text": "1\\) Dr. B. Siva Prasad, Head- Biotech lab, Environment Protection Training and Research Institute (EPTRI),\nTelangana\n\n2\\) Dr. P. Vijaya Kumar, Project Coordinator, All India Coordinated Research Project on Agro-meteorology\n(AICRPAM), ICAR-Central Research Institute for Dryland Agriculture (CRIDA), Hyderabad\n\n3\\) Mr. Cariappa M.R, Vice-Chairman and MD, Puthari Farmer Producer Company Ltd\n\n4\\) Dr. Debabrata Ray, Scientist, Regional Research Station, Rubber Research Institute of India, Rubber\nBoard\n\nking Partners — Gold Partners — ASSOCHAM — Celebrating 100 Years\n\nteri\nTHE ENERGY AND\nRESOURCES IN\n\n… [+273 more chars]",
  "content_hash": "0a59f492f710c4f536f41b2bcb621571b0ed2a1d90f7c7039e78a3dd868e3436",
  "token_count": 235,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 31,
  "page_number": 24,
  "page_range": [
    24,
    24
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `fe7aa908-dae7-55e6-8020-b9852fc1501d`

- vector: dim=3072 · [-0.0103, 0.0161, -0.0029, 0.0138, 0.0019, -0.0442, -0.0050, -0.0003, …]

```json
{
  "chunk_id": "fe7aa908-dae7-55e6-8020-b9852fc1501d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "ASSOCHAM — M — ASSENTI — CHAM — ASSOCHAM — ALL — ASSOCHA — 4.1 Introduction - Dr Ashok Dalwai:",
  "chunk_text": "Climate Change that was doubted few years back has now been accepted across the globe.\nThe linear trend in rise of temperature is 0.64 in 1905 till 1995 and has increased to 0.74 from\n1995-2004. The hottest 12 years were recorded in recent times during the period 1996 to 2006.\nHuman intervention has accelerated the pace of GHGs addition in atmosphere and is challenging\nmankind to develop adaptation measures. Within agriculture, CO2, Methane and Nitrous oxide are\ncontributors to GHGs and their contribution is 28%. CO2 has the most adverse impact. GHGs in\nIndia will have an increasing trend simi\n\n… [+1035 more chars]",
  "content_hash": "c89c78ac34115d04a4672e03110048d25780e8d87a808b76e4c2d8e1df1a49ca",
  "token_count": 337,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 32,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `feefe60f-2e11-5031-a932-bacf8bdd7a7b`

- vector: dim=3072 · [-0.0358, 0.0022, -0.0069, 0.0233, 0.0097, 0.0001, 0.0118, 0.0104, …]

```json
{
  "chunk_id": "feefe60f-2e11-5031-a932-bacf8bdd7a7b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Major components under the project:",
  "chunk_text": "· Designing household level adaptation interventions based on vulnerability assessment\n\n· Developing information system\n\n· Capacity building for implementing climate smart strategies\n\nNABARD is the implementing agency, EPTRI is the executing agency, DOA, PJTSAU, and ICRISAT\nare technical partners of the project. The project cost is Rs. 24 crore covering 3438 farmers of the\nMahbubnagar district in 3 mandals and 15 villages. A baseline survey of 8400 farmers was done\nand their vulnerability to climate was classified under four categories. Sensitizing farmers about the\nidea of climate change is a\n\n… [+525 more chars]",
  "content_hash": "d9bbf1bbedf7e14677626f3778ae39b135ef856c647fab386d3232916e21891e",
  "token_count": 228,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 33,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `13354a34-caf1-51a3-b8fd-ea86bd670187`

- vector: dim=3072 · [-0.0380, 0.0001, -0.0042, -0.0172, -0.0119, -0.0234, 0.0193, -0.0030, …]

```json
{
  "chunk_id": "13354a34-caf1-51a3-b8fd-ea86bd670187",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "4.3 Promoting the use of agro-meteorological information - Dr P Vijaya Kumar:",
  "chunk_text": "Under the All India Coordinated Project on Agro-meteorology, 25 centres have been set up which\nare working on 5 themes. Weather and climate information in Agriculture can help in procurement\nof inputs for timely sowing, to plan cropping systems, selection of crop / variety, timely sowing\n/ transplanting, irrigation scheduling, fertilizers application, timing of plant protection & reduce\nindiscriminate pesticide usage, harvesting etc.\n\nThe project on the use of agro-meteorological information aims at better planning for climate\nchange. Agriculture is the most sensitive enterprise as compared to\n\n… [+1232 more chars]",
  "content_hash": "94dbadf3a29694cee43f80f9ba412c92245f9a63af853967bb372f0862595089",
  "token_count": 356,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 34,
  "page_number": 26,
  "page_range": [
    26,
    26
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `800ab434-4436-5e72-b59e-148cc827350b`

- vector: dim=3072 · [0.0102, -0.0241, -0.0036, 0.0006, -0.0471, -0.0521, 0.0190, -0.0299, …]

```json
{
  "chunk_id": "800ab434-4436-5e72-b59e-148cc827350b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "4.4 Impact of Climate Change on Coffee - Mr Cariappa M R:",
  "chunk_text": "India grows about 3% of the world coffee and, therefore has no say in the prices of coffee. Kodagu\ndistrict has faced huge challenges in terms of climate change hampering the quality and production\nof coffee. There is a need to focus on Capacity Building. In relation to this every month, two training\nprograms across multiple topics are held. 30% of farmers attended the training. Farmers require\nhand holding support during the 3 to 5 year period when they implement new measures and face\nloss in income. With the onset of heavy rain, top soils are being washed away and this is being\nmitigated by \n\n… [+324 more chars]",
  "content_hash": "969af0e20d77ea382b2a56f78ab8816ec3fb255d410b56efa395159037f0a3b1",
  "token_count": 195,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 35,
  "page_number": 26,
  "page_range": [
    26,
    26
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `7edd0030-f19d-5d4a-9fbb-79521bfae44a`

- vector: dim=3072 · [0.0070, -0.0228, -0.0069, -0.0064, -0.0169, -0.0132, -0.0026, -0.0334, …]

```json
{
  "chunk_id": "7edd0030-f19d-5d4a-9fbb-79521bfae44a",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "4.5 Case study on Climate Smart Rubber Cultivation- An Option for Changing Climate Situations - Dr Debabrata Ray:",
  "chunk_text": "Rubber was introduced from Brazil. 65% of rubber grown is used by automobile industry. The\nproject on climate smart rubber cultivation which is an option for changing climate situations was\nhighlighted. Rubber can grow in temperature that can go less than 10 degree Celsius in North East\n\nIndia and more than 40 degrees in Maharashtra. One ton of rubber produced removes more than 10\ntons of carbon from atmosphere. Thus, 2.1% of the current rate of CO2 increase in the atmosphere\nhas been reversed by the world's natural rubber plantation. Barren land can be converted to a forest\nby growing rubber \n\n… [+698 more chars]",
  "content_hash": "f38408518713c9f9ec1f22b1fa80aa735335085cdb8eb6770087a4369edc1ff1",
  "token_count": 256,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 36,
  "page_number": 26,
  "page_range": [
    26,
    27
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `ea6fd048-cbdd-51f6-94de-f4fd4064b9ea`

- vector: dim=3072 · [-0.0091, -0.0107, -0.0019, -0.0184, -0.0040, -0.0367, -0.0004, 0.0211, …]

```json
{
  "chunk_id": "ea6fd048-cbdd-51f6-94de-f4fd4064b9ea",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "4.6 NICRA - Dr. M Prabhakar",
  "chunk_text": "When NICRA was started in 2011, there was no indigenously developed data available and IPCC\nCoefficients were used. With the involvement of 40 ICAR institutes, 121 KVKs, 30 Universities, a lot\nhas been achieved. Creation of infrastructure to conduct advanced research with an investment of\nRs. 200 crore has resulted in generation of data leading us to show that our emissions are not that\nhigh. Also, carbon sequestration potential in the country has been under estimated. Agro-forestry\nhas been left out in estimation. The huge areas of mango cultivated has also not been factored in.\n\nIn 151 villa\n\n… [+1567 more chars]",
  "content_hash": "53323a95886a6b4a651c6418b10a05c665df87bd4f8f09f61db6d66fa7817a8b",
  "token_count": 490,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 37,
  "page_number": 27,
  "page_range": [
    27,
    28
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `c31d659a-4038-5d97-899f-3dfd3101d947`

- vector: dim=3072 · [-0.0261, -0.0047, -0.0137, -0.0051, -0.0062, -0.0155, 0.0111, -0.0188, …]

```json
{
  "chunk_id": "c31d659a-4038-5d97-899f-3dfd3101d947",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Ber — O — ASSOCH — O — ASSOCI — AS — ASSOC — AS — 5.1 Introduction - Ms Ulka Kelkar:",
  "chunk_text": "Mobilizing Investments and Climate Finance is an important component under the broader theme.\nAdaptation investments, specifically in agriculture, offer an opportunity to leverage both climate\nand sustainable development benefits. However, the benefits of adaptation are difficult to quantify\n\nin monetary terms and take time for impacts to show up, and this acts as a barrier to raising current\nadaptation investments and mobilizing them in future.\n\nFinance is the key and necessary to all approaches that are taken in meeting the climate change\ngoals in agriculture. It has 3 features viz.,\n\n1\\. Cr\n\n… [+580 more chars]",
  "content_hash": "10e085cf8ae0e0d9f0febc9f4477858c1f7aeecc8b4371b0f44157b741c59104",
  "token_count": 240,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 38,
  "page_number": 28,
  "page_range": [
    28,
    29
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `bd6defc8-2de1-51aa-a6e6-081daa774a97`

- vector: dim=3072 · [-0.0559, 0.0136, -0.0149, -0.0095, 0.0207, -0.0227, 0.0184, 0.0201, …]

```json
{
  "chunk_id": "bd6defc8-2de1-51aa-a6e6-081daa774a97",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "NABARD is a National Implementing Entity (NIE) and Direct Access Entity for accessing funds from -\n\n(a) Green Climatic Fund(GCF); and, (b) Adaptation Fund under UNFCC.\n\nGCF is based on voluntary contributions and hence limited in its fund size. About 134 million US\nDollars has been provided for two projects. Under Adaptation fund, 10 million US Dollars was\navailable which has been fully utilized.\n\nNABARD is also the NIE for National Adaptation fund for Climate Change and has funded 30\nprojects. It does the work of appraisal monitoring of utilization of funds and physical progress.\nIn addition,\n\n… [+683 more chars]",
  "content_hash": "414bc2810f0a02cc78d9f967b87f6de3fb35e73740d73cf9cb6bc08d5f30bbd4",
  "token_count": 278,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 39,
  "page_number": 29,
  "page_range": [
    29,
    29
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `936eef86-f3fb-5845-9240-c72b0bdcbded`

- vector: dim=3072 · [-0.0145, 0.0091, -0.0042, -0.0025, -0.0209, -0.0218, 0.0313, 0.0089, …]

```json
{
  "chunk_id": "936eef86-f3fb-5845-9240-c72b0bdcbded",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.3 3 Projects undertaken by Watershed Development Department, Karnataka - Mr Prabhash Chandra Ray:",
  "chunk_text": "Soil and water conservation activities have been taken up in the last three decades. Karnataka\nhas been a pioneer in applying technology in watershed sector. About 14 lakh hectare has been\ncovered in developing the Land Resource Information (LRI), wherein mapping of several important\nparameters pertaining to land use has been done. Policy guidelines on the use of inputs based on\nsoil health card and LRI data are being developed.\n\nDigital library is established and Decision Support System has gone live and is in the public domain.\nInformation on each parcel of land has been given in 12 district\n\n… [+1728 more chars]",
  "content_hash": "99f53bb720f76431bc6f3210edbd0502567a3adffb5d8cfa88cb8c232eea29df",
  "token_count": 503,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 40,
  "page_number": 29,
  "page_range": [
    29,
    30
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `26fd6082-6b37-54b1-94f4-a24d623b7986`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "26fd6082-6b37-54b1-94f4-a24d623b7986",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.4 Projects undertaken by KfW - Ms Sangeeta Agarwal:",
  "chunk_text": "5.4 Projects undertaken by KfW - Ms Sangeeta Agarwal:\n\nKfW, being a German Development Bank, provides international financing and development\nfinancing is an important component. In the last 60 years, 9 billion Euros worth of projects have\nbeen financed in India.\n\nClimate change adaptation is one of the core components in the financing of projects. One of the\nmain programs- The Umbrella Programme in Natural Resource Management is in partnership with\nNABARD. This was the first project in India that brought a paradigm shift from grant based projects\nto loan based projects.\n\nThe annual commitment\n\n… [+2372 more chars]",
  "content_hash": "96f01b07a82388f84cc9983a57b362e0d4b31826d8bd43634eddb335d80f2a46",
  "token_count": 624,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    30,
    31
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `530dc5a6-d7c4-50bd-9933-a0b858c4fa1f`

- vector: dim=3072 · [-0.0302, 0.0171, -0.0151, 0.0387, -0.0206, -0.0351, 0.0212, -0.0019, …]

```json
{
  "chunk_id": "530dc5a6-d7c4-50bd-9933-a0b858c4fa1f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.4 Projects undertaken by KfW - Ms Sangeeta Agarwal:",
  "chunk_text": "KfW, being a German Development Bank, provides international financing and development\nfinancing is an important component. In the last 60 years, 9 billion Euros worth of projects have\nbeen financed in India.\n\nClimate change adaptation is one of the core components in the financing of projects. One of the\nmain programs- The Umbrella Programme in Natural Resource Management is in partnership with\nNABARD. This was the first project in India that brought a paradigm shift from grant based projects\nto loan based projects.\n\nThe annual commitment to projects is one billion Euros. In India, energy, su\n\n… [+1440 more chars]",
  "content_hash": "bb59cd008912b8632c847421e824ea72e5b5bcaacbafecafaff138aa5bf35911",
  "token_count": 425,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "26fd6082-6b37-54b1-94f4-a24d623b7986",
  "chunk_index": 41,
  "page_number": 30,
  "page_range": [
    30,
    31
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `0b6292fa-533d-5fc7-b3e0-077f3c4cb69b`

- vector: dim=3072 · [-0.0359, 0.0169, -0.0081, 0.0271, -0.0355, -0.0321, 0.0134, 0.0095, …]

```json
{
  "chunk_id": "0b6292fa-533d-5fc7-b3e0-077f3c4cb69b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.4 Projects undertaken by KfW - Ms Sangeeta Agarwal:",
  "chunk_text": "The challenges and requirements in financing adaptation projects are:\n\n1\\. Identifying bankable projects in agriculture, where market distortions in the form of high level\nsubsidies make it difficult to identify bankable projects. 2\\. The preponderances of small and marginal farmers make it necessary to aggregate the farmers in\nthe form of FPCs to channelize finance.\n\n3\\. Planning natural resource management with linkages to livelihood requirement and providing\nintensive hand-holding support to farmers.\n\n4\\. For better risk management, provisioning for credit guarantee is necessary.\n\n5\\. Even \n\n… [+506 more chars]",
  "content_hash": "8120e639b43b62f148c79a7e4a3cd6ed08c92c6dad50008b6ccd3606b4dbf4ee",
  "token_count": 225,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "26fd6082-6b37-54b1-94f4-a24d623b7986",
  "chunk_index": 42,
  "page_number": 31,
  "page_range": [
    31,
    31
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `57ed357e-b63a-58cb-a9e2-c5841c7f15ed`

- vector: dim=3072 · [-0.0146, 0.0063, -0.0161, -0.0135, -0.0160, -0.0104, 0.0310, -0.0207, …]

```json
{
  "chunk_id": "57ed357e-b63a-58cb-a9e2-c5841c7f15ed",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.5 Projects funded by State Bank of India (SBI)-Mr Sridhar P:",
  "chunk_text": "There are only 4-5 bio-tech institutions in Karnataka, which SBI has funded. The bank has also\nfinanced solar pump set, cold storage buildings, tissue culture, dry land cultivation. Digital banking\nis promoted through the Yono Krishi App, which helps in providing quick weather updates, getting\ninputs through online orders, and advisories from several agricultural experts.\n\nThere has been adaption of solar ATMs across India. All offices, have completely eradicated the use\nof plastics.\n\nSBI has also financed land reclamation programme for reclaiming saline soils to an extent of 5000\nacres in Bag\n\n… [+499 more chars]",
  "content_hash": "de90d1391ce9b7716177acfa21cc91b27200dd15e93f13bddd7f03c313d530d0",
  "token_count": 221,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 43,
  "page_number": 31,
  "page_range": [
    31,
    31
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `bffb78a2-4588-58a7-8a00-c1b473772e65`

- vector: dim=3072 · [-0.0328, -0.0024, -0.0109, 0.0131, -0.0286, -0.0169, 0.0301, 0.0088, …]

```json
{
  "chunk_id": "bffb78a2-4588-58a7-8a00-c1b473772e65",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.6 Climate Finance for Agriculture- Ms Tamiksha Singh:",
  "chunk_text": "Traditional agriculture has many barriers such as lack of collaterals and the associated high risks. Last\nmile delivery to small farmers is another main issue. International Climate Funds are very limited in\nthis area and thus, need to bring in private financing.\n\nThere is a requirement for enhancing the capacity of the farmers who need to understand the risks\nand possible benefits. 22 case studies have revealed that the following 3 aspects are important.\n\nCapacity building is required for (i) farmers to understand risks and mitigating it, (ii) Bank officers\nand Government officers to know abo\n\n… [+1206 more chars]",
  "content_hash": "86cb2281967d02e5ce693cf3edc642e47673414cf6a52d0055d53000353bfc40",
  "token_count": 343,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 44,
  "page_number": 31,
  "page_range": [
    31,
    32
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `0010f922-e7c6-56ed-89c3-a9c43652ba94`

- vector: dim=3072 · [-0.0238, 0.0008, 0.0007, -0.0195, -0.0186, -0.0320, 0.0253, 0.0311, …]

```json
{
  "chunk_id": "0010f922-e7c6-56ed-89c3-a9c43652ba94",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.7 Conclusion :",
  "chunk_text": "The Chair noted that the session has identified several sources of funding and also recognised the\nneed for building up the capacities and wondered if any policy changes are required in Government\nof Karnataka to which NABARD responded that if credit can go to the cluster based project, it\nwill enhance financing to the sector. KfW suggested that for fixing the interest rate, the entire\ninvestment grant from production to marketing needs to be taken into account.\n\nSBI mentioned that while Mudra loans are designed for SME sector, they have developed a special\nproduct under MUDRA for the agricult\n\n… [+696 more chars]",
  "content_hash": "fbdcc99e4cd95e86ed18e791eeb2d0d2dfce194744470eaf7e0c45e7a91d63ea",
  "token_count": 269,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 45,
  "page_number": 32,
  "page_range": [
    32,
    33
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `4dc9ae73-2d43-5bee-8dc9-609c80979ab3`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "Agri Partner — ASSCX\n\nThe Valedictory session started with Dr. Annapurna Vancheswaran Senior Director, TERI putting the session\nin context by acknowledging Honourable Chief Minister of Karnataka, Shri. B.S. Yediyurappa for giving\nus his valuable time to flag off this conference on 'Approaches to Shaping Climate Resilient Agriculture'.\nKarnataka, having the second largest area under rainfed agriculture, has higher vulnerability and in this\nregard, it is important to analyze the trends and identify measures required to build up the resilience of\nrainfed agriculture, which will lead to developmen\n\n… [+10148 more chars]",
  "content_hash": "e0b78101183e4e5e1da5d01783e34b461b3898ce72c3f6e2753fc2b479eea6f9",
  "token_count": 2157,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    33,
    37
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `9aa4b332-417f-50a3-9047-f37b9f358645`

- vector: dim=3072 · [0.0035, -0.0191, -0.0120, -0.0289, -0.0071, -0.0828, 0.0150, 0.0229, …]

```json
{
  "chunk_id": "9aa4b332-417f-50a3-9047-f37b9f358645",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "The Valedictory session started with Dr. Annapurna Vancheswaran Senior Director, TERI putting the session\nin context by acknowledging Honourable Chief Minister of Karnataka, Shri. B.S. Yediyurappa for giving\nus his valuable time to flag off this conference on 'Approaches to Shaping Climate Resilient Agriculture'.\nKarnataka, having the second largest area under rainfed agriculture, has higher vulnerability and in this\nregard, it is important to analyze the trends and identify measures required to build up the resilience of\nrainfed agriculture, which will lead to development of an implementation\n\n… [+1134 more chars]",
  "content_hash": "61e3d29fd993d513dc46edf3ccd6bbd99f2334eb29f953ca2d1d7aee94acaaa0",
  "token_count": 350,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "chunk_index": 46,
  "page_number": 33,
  "page_range": [
    33,
    33
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `5a691cb6-c36d-53d9-8a4e-e9fc4b091ea5`

- vector: dim=3072 · [-0.0036, -0.0147, -0.0067, -0.0235, -0.0156, -0.0364, 0.0263, 0.0172, …]

```json
{
  "chunk_id": "5a691cb6-c36d-53d9-8a4e-e9fc4b091ea5",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "ended the deliberations that were carried out in the\nconglomeration of speakers with various backgrounds like policy makers, practitioners from government,\nscientists, academicians, sector experts, leaders from industry and trade, farmer producing organizations,\nsenior officers of major banks and financial organizations, etc. Mr T.M Vijay Bhaskar, Chief Secretary, Government of Karnataka In his Valedictory Address, highlighted\nthat agriculture and farmers welfare is the top priority of the Government, which has also been mentioned\nby the Honourable Chief Minister. Indian agriculture is a const\n\n… [+1486 more chars]",
  "content_hash": "cda5e75d70f7aac093b4518f7d048fd46d3f5e8d793c770f3a46ad8732e6aeb7",
  "token_count": 402,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "chunk_index": 47,
  "page_number": 34,
  "page_range": [
    34,
    34
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `c266884e-c7c9-537e-ac49-466808ec97df`

- vector: dim=3072 · [-0.0111, 0.0048, -0.0071, -0.0045, -0.0217, -0.0021, 0.0288, -0.0033, …]

```json
{
  "chunk_id": "c266884e-c7c9-537e-ac49-466808ec97df",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "He mentioned about micro irrigation projects, which are bringing\nin water use efficiency in the irrigation sector and referred to the investment made in Ramthal project. He\nsuggested that TERI can undertake evaluation of this project for its success and indicate the lessons learnt\nin its implementation. Karnataka is a major producer of millets which are climate resilient in nature. He recalled that the State\nhad organized an international conference on millets and many major initiations have been taken to\npromote cultivation of millets and also expansion of market for millets. The State has al\n\n… [+1776 more chars]",
  "content_hash": "c283515fec134017b66eb0aaca6d1622abb9342d9a2823a93fb6d200fb047bc3",
  "token_count": 483,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "chunk_index": 48,
  "page_number": 34,
  "page_range": [
    34,
    34
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `fd96db20-5340-5ca1-be90-6f447ce61eec`

- vector: dim=3072 · [-0.0013, -0.0088, -0.0102, -0.0049, 0.0069, -0.0309, 0.0001, 0.0072, …]

```json
{
  "chunk_id": "fd96db20-5340-5ca1-be90-6f447ce61eec",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "While concluding, he observed that most of the actions taken by the State Government are in the direction\nof climate resilient farming and in that effort, the suggestions made in this conference will be considered\nin making the Governmental programmes more effective. Ms. Uma S Nair Regional Director, ASSOCHAM proposed vote of thanks. She expressed gratitude to\nHonourable Chief Minister and the Chief Secretary for their participation and their wishes.\n\nShe thanked the Distinguished Speakers for taking out time and contributing to the sessions, the media\nand participants.\n\nShe also thanked ICAR-\n\n… [+1756 more chars]",
  "content_hash": "b2298a9d6916d370dae0a27576aeddb798c039977299febaef3211f8b1b9b4e4",
  "token_count": 471,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "chunk_index": 49,
  "page_number": 35,
  "page_range": [
    35,
    36
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `bb3eab12-386d-5b0c-9b0d-2d8ae4f8cafc`

- vector: dim=3072 · [-0.0191, -0.0077, -0.0019, 0.0054, -0.0057, -0.0253, 0.0068, 0.0059, …]

```json
{
  "chunk_id": "bb3eab12-386d-5b0c-9b0d-2d8ae4f8cafc",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "This can be done by collaborating with\nscientists and researchers to develop robust approaches for downscaling climate models, and\nwork with different government departments, the private sector, civil society, and the farmers for\neffective last mile delivery of information, to form locally relevant and feasible solutions. 4\\. Research Institutes and Commodity boards have shown success in recommended adaptation\npractices. ICAR is working on integrated modeling approach and has prepared contingency\nplans for districts for adoption by States. NICRA has reported 21% reduction in GHG emissions\nfrom\n\n… [+1977 more chars]",
  "content_hash": "1371e5434432c74d97ac8dbf538613699eb106741c33449891eab434465a5e77",
  "token_count": 501,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "chunk_index": 50,
  "page_number": 36,
  "page_range": [
    36,
    37
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `b2e5bbe4-bbfc-5ed8-8828-973bb4cc6583`

- vector: dim=3072 · [-0.0290, 0.0089, -0.0034, -0.0023, -0.0031, -0.0001, 0.0418, 0.0306, …]

```json
{
  "chunk_id": "b2e5bbe4-bbfc-5ed8-8828-973bb4cc6583",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agri Partner — ASSCX",
  "chunk_text": "Banks have taken certain steps in filling this gap. NABRD has started allocating a portion of its\nlending to this area. SBI through its digital banking App provides services and provides small\nloans without collateral. KfW through its channel partners is implementing many projects. 11\\. From a financing perspective, measures suggested include:\n\n· Capacity building for all stakeholders.\n\n· Successful pilot programmes required in up-scaling new methodologies.\n\n· Demand aggregation platform to attract large scale funding.\n\n· Government to create a fund for guaranteeing use of proven technologies.\n\n… [+495 more chars]",
  "content_hash": "653ffcb7cf54129c6df7d29ccb057511845e68a5a097c54fd3dee18021ae6f1e",
  "token_count": 222,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4dc9ae73-2d43-5bee-8dc9-609c80979ab3",
  "chunk_index": 51,
  "page_number": 37,
  "page_range": [
    37,
    37
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `1c64671b-929f-57ad-ac28-a5de2599c02b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1c64671b-929f-57ad-ac28-a5de2599c02b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India",
  "chunk_text": "Agenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India\n\n| 8:00-9:00 | Registration |\n| --- | --- |\n| 9:00-10:30 | Session 1: Exposure to climatic risks: Developing an understanding of the risks at the sub-national scales |\n| Chair: Dr K.J Ramesh, Former Director General, India Meteorological Department |  |\n| Co-Chair: Mr T.K Anil Kumar, IAS, Principal Secretary, Revenue Department, Government of Karnataka |  |\n| Speakers: |  |\n| · Dr. G.S Srinivasa Reddy, Director, Karnataka State Natural Disaster Monitoring Centre |  |\n| · Mr Harikumar B,\n\n… [+4362 more chars]",
  "content_hash": "862b3de3e49a0ed5b6ba35ea015d82db71a0916f159a8f129852d8a922634aa0",
  "token_count": 1319,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    38,
    39
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `04120c09-951d-514d-950a-a6adfe12c4e3`

- vector: dim=3072 · [0.0052, -0.0263, -0.0019, -0.0332, -0.0023, -0.0684, 0.0266, 0.0552, …]

```json
{
  "chunk_id": "04120c09-951d-514d-950a-a6adfe12c4e3",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India",
  "chunk_text": "| 8:00-9:00 | Registration |\n| --- | --- |\n| 9:00-10:30 | Session 1: Exposure to climatic risks: Developing an understanding of the risks at the sub-national scales |\n| Chair: Dr K.J Ramesh, Former Director General, India Meteorological Department |  |\n| Co-Chair: Mr T.K Anil Kumar, IAS, Principal Secretary, Revenue Department, Government of Karnataka |  |\n| Speakers: |  |\n| · Dr. G.S Srinivasa Reddy, Director, Karnataka State Natural Disaster Monitoring Centre |  |\n| · Mr Harikumar B, Assistant Director (Agriculture), Project Preparation and Monitoring Cell, Government Secretariat, Thiruvanan\n\n… [+1422 more chars]",
  "content_hash": "e327d1845a026b88521945abfd1f8649328de86c3053d34a0bff6e176a032c12",
  "token_count": 560,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "1c64671b-929f-57ad-ac28-a5de2599c02b",
  "chunk_index": 52,
  "page_number": 38,
  "page_range": [
    38,
    38
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `b2b4cb13-5c5d-558c-a8d4-e308776ce4cf`

- vector: dim=3072 · [0.0066, -0.0213, -0.0094, -0.0216, -0.0156, -0.0681, 0.0192, 0.0336, …]

```json
{
  "chunk_id": "b2b4cb13-5c5d-558c-a8d4-e308776ce4cf",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India",
  "chunk_text": "R.H Laxman, Principal Scientist, Division of Plant Physiology and Biochemistry, ICAR- Indian Institute of Horticultural Research (IIHR) |  |\n| · Ms Suruchi Bhadwal, Senior Fellow, Earth Science and Climate Change, TERI |  | | 12:45-14:00 | Session 3: The policy landscape; international to national and sub-national linkages |\n| --- | --- |\n| Chair: Mr R.R Rashmi, Distinguished Fellow & Programme Director, Earth Science and Climate Change ,TERI |  |\n| Co-chair: Dr. Sandeep Dave, IAS, Additional Chief Secretary, Department of Forest, Ecology & Environment, Government of Karnataka |  |\n| Speakers:\n\n… [+1741 more chars]",
  "content_hash": "d7027c2bd78a26f412640f5135566876285ec5e54a27ba9cc5809321d34bd559",
  "token_count": 598,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "1c64671b-929f-57ad-ac28-a5de2599c02b",
  "chunk_index": 53,
  "page_number": 39,
  "page_range": [
    39,
    39
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `e5332e58-0f8d-5738-b30f-0e7a48823c1b`

- vector: dim=3072 · [-0.0033, 0.0068, -0.0131, -0.0375, -0.0097, -0.0616, 0.0116, 0.0360, …]

```json
{
  "chunk_id": "e5332e58-0f8d-5738-b30f-0e7a48823c1b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Agenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India",
  "chunk_text": "ing Support for Actions |\n| Chair: Ms Ulka Kelkar, Director - Climate Program, World Resources Institute |  |\n| (WRI), India Co-chair: Mr C.V Reddy, Deputy General Manager, Karnataka Regional Office, NABARD |  |\n| Speakers: |  | | · Mr Prabhash Chandra Ray, IFS, Additional Principal Chief Conservator of Forests & Commissioner Watershed Development Department & Ex-officio Secretary to Government, Agriculture & Horticulture Department, Government of Karnataka · Ms Sangeeta Agarwal, Senior Project Manager, KfW · Ms Tamiksha Singh, Associate Fellow, Earth Science and Climate Change, TERI · Mr Srid\n\n… [+339 more chars]",
  "content_hash": "9fda64ea4ba12f1df530e4e5d8121041ccec0df0be56214c43101cc8277e9853",
  "token_count": 248,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "1c64671b-929f-57ad-ac28-a5de2599c02b",
  "chunk_index": 54,
  "page_number": 39,
  "page_range": [
    39,
    39
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Parent · `046b2cef-6f14-5bac-b2d2-257f8f04aad8`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "046b2cef-6f14-5bac-b2d2-257f8f04aad8",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "List of Participants\n\n| SL. No. | Name | Designation | Organization |\n| --- | --- | --- | --- |\n| 1 | Dr. B.L. Manjunath | Principal Scientist | ICAR - IIHR |\n| 2 | Dr Suneel Kunamaneni | Senior Lecturer in Innovation Management | Leeds Beckett University |\n| 3 | Mr Anoop H V | Manager Exports | Indira Food Pvt.Ltd |\n| 4 | Mr Imtimongla Jamir | Executive - Social Media | AVIANWE |\n| 5 | Mr S S M Gavaskar | Scientist | Karnataka State Natural Disaster Monitoring Centre |\n| 6 | Mr Shankara Hebbar | Principal Scientist | ICAR - IIHR |\n| 7 | Ms Anitha Reddy | Director | Sahaja Samrudha Organic Pro\n\n… [+4235 more chars]",
  "content_hash": "9106c8068fefb79226645f77ea9dbddaeb04bab881e300f4b5530b4c5210f4a3",
  "token_count": 1327,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "page_range": [
    40,
    41
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `4a242553-63a2-547d-8b8b-8552fa881a2b`

- vector: dim=3072 · [0.0042, -0.0135, -0.0094, -0.0411, -0.0039, -0.0355, 0.0181, 0.0212, …]

```json
{
  "chunk_id": "4a242553-63a2-547d-8b8b-8552fa881a2b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "| SL. No. | Name | Designation | Organization |\n| --- | --- | --- | --- |\n| 1 | Dr. B.L. Manjunath | Principal Scientist | ICAR - IIHR |\n| 2 | Dr Suneel Kunamaneni | Senior Lecturer in Innovation Management | Leeds Beckett University |\n| 3 | Mr Anoop H V | Manager Exports | Indira Food Pvt.Ltd |\n| 4 | Mr Imtimongla Jamir | Executive - Social Media | AVIANWE |\n| 5 | Mr S S M Gavaskar | Scientist | Karnataka State Natural Disaster Monitoring Centre |\n| 6 | Mr Shankara Hebbar | Principal Scientist | ICAR - IIHR |\n| 7 | Ms Anitha Reddy | Director | Sahaja Samrudha Organic Producer Company Ltd |\n| \n\n… [+1713 more chars]",
  "content_hash": "ad2ab7c0f54db536a038ad980d0f7a8ee5d9558b23946cdcdda8135bc9e02143",
  "token_count": 626,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "046b2cef-6f14-5bac-b2d2-257f8f04aad8",
  "chunk_index": 55,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `ddf2d0a5-ef4d-5e7d-a99c-0cfec120e2fa`

- vector: dim=3072 · [0.0077, -0.0175, -0.0090, -0.0404, -0.0088, -0.0169, 0.0175, 0.0129, …]

```json
{
  "chunk_id": "ddf2d0a5-ef4d-5e7d-a99c-0cfec120e2fa",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "Sridhar | Principal Scientist | ICAR - IIHR |\n| 27 | Ms Arathi | Business Developer | Universal Enterprises |\n| 28 | Mr B Mahesh | Managing Director | Karnataka Council for Technological Upgradation |\n| 29 | Mr Amit B | Manager | Universal Corporation | | Sl. No. | Name | Designation | Organization |\n| --- | --- | --- | --- |\n| 30 | Ms Devika. S | Accountant | Universal Enterprises |\n| 31 | Prof. Shakunthala Sri- dhara | Member, Board of Manage- ment - GKVK | University of Agricultural Sciences |\n| 32 | Dr Sanjay M T | Agronomist & Head | University of Agricultural Sciences |\n| 33 | Dr Meenaks\n\n… [+1713 more chars]",
  "content_hash": "a0bcf1218c128b3acd62ad2e5ceadbe2605aa95aa4b1836f1a1470ec6d06cdd6",
  "token_count": 620,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "046b2cef-6f14-5bac-b2d2-257f8f04aad8",
  "chunk_index": 56,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `2a656cec-6482-532c-be8f-bcbc57cc212b`

- vector: dim=3072 · [0.0249, -0.0147, -0.0119, -0.0262, 0.0006, -0.0060, 0.0102, 0.0290, …]

```json
{
  "chunk_id": "2a656cec-6482-532c-be8f-bcbc57cc212b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "Professor | University of Horticultural Sciences- Bagalkot |\n| 53 | Mr Jayakumar H | Director | Tanindo Seed Pvt.Ltd | | 54 | Mr M Shekar | Chief Executive Officer | Tanindo Seed Pvt.Ltd |\n| 55 | Dr Archana Thulaseed- haran | Asst. Professor | Indian Council of Plantation |\n| 56 | Mr R Mohan Kumar | Director | Vokkal Seeds Pvt.Ltd |\n| 57 | Mr Jayaprakash | Reporter | Udayavani |\n| 58 | Ms Poornima N | Managing Partner | Universal Enterprises |\n| 59 | Mr Sebastian | Partner | HDFC |\n| 60 | Mr Ravi | Consultant | UC |\n| 61 | Mr Ramesh | Partner | Rujul |",
  "content_hash": "4531c7327a195cc74dc34adfd5aedf94728a85cbf03c69854a779ece24fc747d",
  "token_count": 168,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "046b2cef-6f14-5bac-b2d2-257f8f04aad8",
  "chunk_index": 57,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```

## Child · `3ccc1382-1020-5881-b960-1135c31ab752`

- vector: dim=3072 · [-0.0197, 0.0159, -0.0169, -0.0291, 0.0028, -0.0137, 0.0250, -0.0095, …]

```json
{
  "chunk_id": "3ccc1382-1020-5881-b960-1135c31ab752",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Notes — Notes — About TERI",
  "chunk_text": "The Energy and Resources Institute (TERI) is an independent, non-profit organization, with\ncapabilities in research, policy, consultancy and implementation. TERI has multi-disciplinary\nexpertise in the areas of energy, environment, climate change, resources, and sustainability.\nWith the vision of creating innovative solutions for a sustainable future, TERI's mission is to usher\nin transitions to a cleaner and more sustainable future through the conservation and efficient use\nof the Earth's resources and develop innovative ways of minimizing waste and reusing resources.\n\nTERI's work across sect\n\n… [+1006 more chars]",
  "content_hash": "2ce4ef3619e8228f601a31358041d23bbba93ad8863ac9b900c8e54f70a0972c",
  "token_count": 346,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 58,
  "page_number": 44,
  "page_range": [
    44,
    44
  ],
  "created_at": "2026-06-29T10:54:32.915089+00:00",
  "updated_at": "2026-06-29T10:54:32.915089+00:00"
}
```
