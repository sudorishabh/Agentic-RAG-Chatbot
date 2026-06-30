# Qdrant points — Bengaluru-Conference-Report_2020.pdf

- points (rows upserted): **69**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `cabc15d5-0b27-51be-9233-a199a22dcd45`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "cabc15d5-0b27-51be-9233-a199a22dcd45",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Table of Contents — INTRODUCTION 6",
  "chunk_text": "Table of Contents — INTRODUCTION 6\n\nASSOCHAM Celebrating 100 Years\n\nteri\nTHE ENERGY AND RESOURCES INSTITUTE Creating Innovative Solutions for a Sustainable Future\n28th February 2020, Bengaluru, India\nOrganized by The Energy and Resources Institute (TERI)\nThe Associated Chambers of Commerce of India (ASSOCHAM)\n\nAuthors Rhea Puri . Suruchi Bhadwal\nReviewed by D N Narasimha Raju\n\n٠٫١٠٠\n\nWELCOME ADDRESS BY MR S. SAMPATHRAMAN, ASSOCHAM KARNATAKA CHAPTER 7\nCONTEXT SETTING BY MR D N NARASIMHA RAJU, DIRECTOR, SOUTHERN REGIONAL CENTRE, TERI 8\nINAUGURAL ADDRESS BY SHRI B S YEDIYURUPPA, HONOURABLE CHIEF \n\n… [+1429 more chars]",
  "content_hash": "0c758d33bd398238d55d99d1d63c8d13319aba3f68438d409c3db0f8fdbe3b28",
  "token_count": 649,
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
    1,
    5
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `8e9fddea-d91f-5130-9e4d-6b5d90aac302`

- vector: dim=3072 · [0.0089, -0.0278, -0.0070, -0.0177, 0.0104, -0.0357, 0.0048, 0.0351, …]

```json
{
  "chunk_id": "8e9fddea-d91f-5130-9e4d-6b5d90aac302",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Table of Contents — INTRODUCTION 6",
  "chunk_text": "ASSOCHAM Celebrating 100 Years\n\nteri\nTHE ENERGY AND RESOURCES INSTITUTE Creating Innovative Solutions for a Sustainable Future\n28th February 2020, Bengaluru, India\nOrganized by The Energy and Resources Institute (TERI)\nThe Associated Chambers of Commerce of India (ASSOCHAM)\n\nAuthors Rhea Puri . Suruchi Bhadwal\nReviewed by D N Narasimha Raju\n\n٠٫١٠٠\n\nWELCOME ADDRESS BY MR S. SAMPATHRAMAN, ASSOCHAM KARNATAKA CHAPTER 7\nCONTEXT SETTING BY MR D N NARASIMHA RAJU, DIRECTOR, SOUTHERN REGIONAL CENTRE, TERI 8\nINAUGURAL ADDRESS BY SHRI B S YEDIYURUPPA, HONOURABLE CHIEF MINISTER OF KARNATAKA 9 VOTE OF THAN\n\n… [+711 more chars]",
  "content_hash": "f77103850fefc6e506968e9daeafeabfcaab83e44975a15cdc389d6df6328670",
  "token_count": 419,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "cabc15d5-0b27-51be-9233-a199a22dcd45",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    5
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `6e5b246d-e3ae-55dc-8deb-064a6cf66064`

- vector: dim=3072 · [0.0064, -0.0146, -0.0087, 0.0029, -0.0067, -0.0624, -0.0047, 0.0496, …]

```json
{
  "chunk_id": "6e5b246d-e3ae-55dc-8deb-064a6cf66064",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Table of Contents — INTRODUCTION 6",
  "chunk_text": "Projections - Mr Saurabh Bhardwaj 14 — 1.7 Conclusion 15\n\nSESSION 2: IMPACTS ON AGRICULTURE, MITIGATION AND ADAPTATION STRATEGIES 16\n\n2.1 Introduction - Dr S Bhaskar 16 2.2 Adoption of Technological Changes- Mr Rajender Kumar Kataria 17\n2.3 Horticulture - Dr R H Laxman. 17\n2.4 Impact of Climate Change on Agriculture - Dr. M.B Rajegowda 18\n\n2.5 Impacts & Strategies - Ms Suruchi Bhadwal 19 — 2.6 Conclusion 19\n\nSESSION 3: THE POLICY LANDSCAPE; INTERNATIONAL TO NATIONAL AND SUB-NATIONAL LINKAGES 20\n3.1 Introduction - Mr R R Rashmi. 20\n3.2 Schemes for Resilient Agriculture - Dr Sandeep Dave 21\n3.3 \n\n… [+249 more chars]",
  "content_hash": "f57e09e71046c4e27bfc9df97e7ac0b683431354fa6415c73854d876ad975385",
  "token_count": 281,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "cabc15d5-0b27-51be-9233-a199a22dcd45",
  "chunk_index": 1,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `0763bf19-b308-57d3-a801-ff1968840fd9`

- vector: dim=3072 · [0.0109, -0.0138, -0.0025, -0.0139, -0.0269, -0.0483, 0.0057, 0.0498, …]

```json
{
  "chunk_id": "0763bf19-b308-57d3-a801-ff1968840fd9",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "4.1 Introduction - Dr Ashok Dalwai 25",
  "chunk_text": "4.2 Case study on Climate Resilient Agriculture Household, Telangana - Dr B Siva Prasad. 25\n4.3 Promoting the use of agro-meteorological information - Dr P Vijaya Kumar. 26\n4.4 Impact of Climate Change on Coffee - Mr Cariappa M R 26\n4.5 Case study on Climate Smart Rubber Cultivation- An Option for Changing Climate Situations\n- Dr Debabrata Ray 26\n4.6 NICRA - Dr. M Prabhakar\n27\n\n4.7 Conclusion 27\n\nSESSION 5: CLIMATE FINANCE: GARNERING SUPPORT FOR ACTIONS 28\n\n5.1 Introduction - Ms Ulka Kelkar 28 — 5.2 NABARD - Mr C V Reddy 29\n\n5.3 Projects undertaken by Watershed Development Department, Karnatak\n\n… [+394 more chars]",
  "content_hash": "5dbf6b40053c22be5d9f20d04adb9d1e0171d6d9870e43b5efd5e0283fb1a3a2",
  "token_count": 309,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 2,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `0e9d3473-822a-595a-ab91-c4436abd2be7`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction\n\nWith a focus on the Paris Agreement on climate change, the Sendai framework on disaster risk reduction and the sustainable development goals, the conference will address the issues that fall within the ambit of these international discourses that have implications at the national and subnational scales.\nThe following listed targets under Goal 13 of \"Climate Action\" under Sustainable Development Goals are planned to be addressed:\n· Strengthen resilience and adaptive capacity to climate-related hazards and natural disasters in all countries.\n· Integrate climate change measures into\n\n… [+9397 more chars]",
  "content_hash": "9732087ab0e2c5e8ecfbcb4b47b8b7d47c907044c63242681fe362718df43443",
  "token_count": 1999,
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
    6,
    11
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `34a19142-7d4b-577b-90cd-15f5d566cbc5`

- vector: dim=3072 · [-0.0173, -0.0165, 0.0068, -0.0021, 0.0114, -0.0226, 0.0165, 0.0150, …]

```json
{
  "chunk_id": "34a19142-7d4b-577b-90cd-15f5d566cbc5",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "With a focus on the Paris Agreement on climate change, the Sendai framework on disaster risk reduction and the sustainable development goals, the conference will address the issues that fall within the ambit of these international discourses that have implications at the national and subnational scales.\nThe following listed targets under Goal 13 of \"Climate Action\" under Sustainable Development Goals are planned to be addressed:\n· Strengthen resilience and adaptive capacity to climate-related hazards and natural disasters in all countries.\n· Integrate climate change measures into national poli\n\n… [+1052 more chars]",
  "content_hash": "8df3bc52e217313b01ced0868e085378d913c8d18be92654578b8a32caca88a5",
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
  "parent_chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "chunk_index": 3,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `22ab97bd-3ecc-5686-a920-a9727cc410ec`

- vector: dim=3072 · [0.0100, -0.0227, -0.0087, -0.0328, 0.0213, -0.0388, 0.0255, 0.0195, …]

```json
{
  "chunk_id": "22ab97bd-3ecc-5686-a920-a9727cc410ec",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "The vulnerability of agriculture in states like Karnataka is much more and in this context, it is important to analyze the trends and identify measures required to build in resilience in rain-fed agriculture leading to development of an implementation plan.\n6 Welcome Address by Mr S. Sampathraman, ASSOCHAM Karnataka Chapter\nMr S Sampathraman welcomed the participants and thanked the Honourable Chief Minister for sparing his valuable time to come to the Conference. In his address, he made the following observations:\nWe human beings are now returning to the preservation of nature. We are worship\n\n… [+858 more chars]",
  "content_hash": "dc4b306b2fbbee2d7d524237e116edaeedec84abef35ed8c02619e09bdebaf61",
  "token_count": 282,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "chunk_index": 4,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `7865368f-3458-5457-81ca-195ecb2ba78d`

- vector: dim=3072 · [0.0127, -0.0138, -0.0099, -0.0475, -0.0059, -0.0425, 0.0188, 0.0217, …]

```json
{
  "chunk_id": "7865368f-3458-5457-81ca-195ecb2ba78d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "A big thanks to the sponsors, department of agriculture and horticulture, Government of Karnataka, NABARD, State Bank of India, ICAR, IIHR, office bearers of ASSOCHAM in together bringing out the conference on approaches to shaping climate resilient agriculture.\n7 Context setting by Mr D N Narasimha Raju, Director, Southern Regional Centre, TERI\nAt the outset, he expressed gratitude to the Hon'ble Chief Minister for his presence and to inaugurate the Conference.\nThe subject of Climate change encompasses many disciplines of science. It is not limited to environment sector but covers aspects of \n\n… [+1637 more chars]",
  "content_hash": "eba4c28797fc27c999877c6f1c5663cd7599c16c602ef0f5a181d370ea62d21f",
  "token_count": 457,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "chunk_index": 5,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `bc277d51-d174-52d9-9ac1-dfc2c5aeaa9f`

- vector: dim=3072 · [0.0166, -0.0260, 0.0018, -0.0114, -0.0072, -0.0262, 0.0055, -0.0161, …]

```json
{
  "chunk_id": "bc277d51-d174-52d9-9ac1-dfc2c5aeaa9f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Promoting forestry and Agro-forestry on a massive scale will create the carbon sink and bring down the CO2 levels. In recent years, Karnataka has been able to increase forest cover and has taken a major initiative to promote Agro-forestry in farmer's fields. In Karnataka, over the years, the contribution of agriculture to GSDP has come down to 7.73per cent (2018-19). A large population is dependent on agriculture for employment and income. The State's vulnerability is high. It has faced more droughts in the past. The State Natural Disaster Monitoring Centre has developed a Composite Index for \n\n… [+1228 more chars]",
  "content_hash": "237f62d7adbe568223e2b3912d9596d2b6c1ef6de1dce172206478eca5a777a8",
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
  "parent_chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "chunk_index": 6,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `425d8427-4cd8-501a-af40-9670e1f3c4a5`

- vector: dim=3072 · [0.0227, -0.0170, 0.0010, -0.0350, 0.0077, -0.0410, 0.0157, 0.0289, …]

```json
{
  "chunk_id": "425d8427-4cd8-501a-af40-9670e1f3c4a5",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "views amongst the Policy makers and Practitioners from Government of India and from Southern States, scientists and experts from national institutes & agricultural Universities, leaders from Industry and Trade, Farmer Producer Organizations and Senior Officers from Banks will lead to preparation of a report on suggestions to meet the emerging climate change challenges.\n8 Inaugural Address by Shri B S Yediyuruppa,\nHonourable Chief Minister of Karnataka\nIn his address, Shri B S Yediyurappa, Honourable Chief Minister, Government of Karnataka, noted the presence of participants and speakers and sp\n\n… [+1435 more chars]",
  "content_hash": "70310bbc527a8027defa2074e9f9ec54955c1aa2c9643a6389dc7f263fcc7fbf",
  "token_count": 401,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "chunk_index": 7,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `af8e94c8-426a-5adb-bc7e-3df31b41034f`

- vector: dim=3072 · [0.0046, -0.0261, -0.0042, -0.0312, -0.0025, -0.0417, 0.0164, 0.0273, …]

```json
{
  "chunk_id": "af8e94c8-426a-5adb-bc7e-3df31b41034f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Introduction",
  "chunk_text": "He wished the Conference all success.\nMERGY AND\nBars\nRESOURCES INSTITUTE Creating Innovative Solutions for a Suntainable Future\nonfereng ping Cli\nResi\nculture\n- vediwerappa\n9 Vote of Thanks by Mr R.R Rashmi, Distinguished Fellow & Programme Director, TERI\nMr R R Rashmi expressed gratitude to the Honourable Chief Minister for having taken time off to come & bless the Conference by inaugurating it. He noted that Chief Minister has taken deep interest in the subject with the interest of the State in mind. The topic is indeed a burning issue of our times, as mentioned by the Chief Minister. It aff\n\n… [+1497 more chars]",
  "content_hash": "1b00b02337817434655bdb066e6341810e93866750378a02017e6ecbace0c0e0",
  "token_count": 480,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "0e9d3473-822a-595a-ab91-c4436abd2be7",
  "chunk_index": 8,
  "page_number": 10,
  "page_range": [
    10,
    11
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `46d18f54-fe50-577a-8550-4864ce550175`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "46d18f54-fe50-577a-8550-4864ce550175",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "1.1 Introduction - Dr K J Ramesh\n\nThe impact of climate change has been noticed in agriculture, water resources, public health sectors and in extreme events. India is good in predicting occurrence of extreme events. To have a climate ready future towards any development plan or any ground action, it is imperative to have a scientifically robust, and sector specific risk profiling of the hazards set up both at baseline and future. The existing knowledge, success stories from different states in mainstreaming climate\n11\n\ninformation in planning is necessary and there is a need for providing high\n\n… [+7201 more chars]",
  "content_hash": "5a043dca8bbcb0e898ef85b240f06a5dd8b71a1370ea16df7bb2c331cca5b75f",
  "token_count": 1499,
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
    11,
    13
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `fc991ff1-bc7c-5041-9450-25a3d04260e8`

- vector: dim=3072 · [-0.0091, -0.0134, 0.0062, -0.0057, 0.0014, -0.0373, 0.0025, 0.0055, …]

```json
{
  "chunk_id": "fc991ff1-bc7c-5041-9450-25a3d04260e8",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "The impact of climate change has been noticed in agriculture, water resources, public health sectors and in extreme events. India is good in predicting occurrence of extreme events. To have a climate ready future towards any development plan or any ground action, it is imperative to have a scientifically robust, and sector specific risk profiling of the hazards set up both at baseline and future. The existing knowledge, success stories from different states in mainstreaming climate\n11\n\ninformation in planning is necessary and there is a need for providing high resolution climate information fo\n\n… [+1842 more chars]",
  "content_hash": "b6c6c4fc2bc372a86cbda07773871d5e38e9aab073e0e73774f5589895624b15",
  "token_count": 452,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "46d18f54-fe50-577a-8550-4864ce550175",
  "chunk_index": 9,
  "page_number": 11,
  "page_range": [
    11,
    12
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `abe70d61-a166-54ce-aa86-842201ce03ab`

- vector: dim=3072 · [-0.0112, -0.0052, 0.0021, -0.0312, -0.0044, -0.0367, 0.0127, 0.0174, …]

```json
{
  "chunk_id": "abe70d61-a166-54ce-aa86-842201ce03ab",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "Strengthening of existing institutions, creating new institutions, data analytics and use of Al are important.\n1.3 Forecasting the weather conditions and provision of updated data - Dr G S Srinivasa Reddy: The Agriculture and allied activities in India, which provide livelihood to majority of its population, is heavily dependent on climatic conditions. The multiple risks associated with Agriculture, weather deviations stand out distinctly. Any deviation from normal condition adversely affects these activities and in turn, the socio-economic condition of the population and also the State / Nati\n\n… [+1327 more chars]",
  "content_hash": "b700cd2f2b18aa55b17ede3bcfca29541b675a6e1bf2efcb9868e49dae635194",
  "token_count": 355,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "46d18f54-fe50-577a-8550-4864ce550175",
  "chunk_index": 10,
  "page_number": 12,
  "page_range": [
    12,
    12
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `b9e082c0-02c0-5026-9051-38612b40f056`

- vector: dim=3072 · [-0.0092, -0.0093, 0.0018, -0.0176, -0.0053, -0.0043, 0.0278, -0.0019, …]

```json
{
  "chunk_id": "b9e082c0-02c0-5026-9051-38612b40f056",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "The Karnataka State Natural Disaster Management Centre has set up a dense network of telemetry rain gauges up to Gram Panchayat level in 6500 stations which are solar powered and GPS enabled.\n12 The process of data collection and dissemination to all the key stakeholders is on real time basis and automated which is first in the country. Forecasts are being shared at the gram panchayat level. Radars are being procured which will help in the Centre to upgrade to \"now cast\" system, so that the farmers get real-time updates. This system is already being used for disseminating information on market\n\n… [+1337 more chars]",
  "content_hash": "8631105e4b0f68916406d89d2a2f601654522caa174de7e9ff67239adcfdc788",
  "token_count": 391,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "46d18f54-fe50-577a-8550-4864ce550175",
  "chunk_index": 11,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `2ceeeabb-a71d-53ab-bde5-c70c8ef57360`

- vector: dim=3072 · [-0.0140, -0.0121, 0.0085, -0.0059, -0.0305, -0.0134, 0.0192, -0.0346, …]

```json
{
  "chunk_id": "2ceeeabb-a71d-53ab-bde5-c70c8ef57360",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "Around 17.15% of the population depends on this sector and 52% of Kerala is under crop cultivation. The state supports diverse ecological conditions and variety of crops- the lowlands have over 600 varieties of paddy and highlands have different species and plantation crops. The pattern of both monsoons has changed. Rainfall pattern has become unpredictable. During the 2018 floods, around 11% of area under cultivation was affected and 1/6th of the state's population suffered. Around 58,000 hectare of agriculture land was damaged due to silt deposition and top soil erosion. Crop losses were est\n\n… [+1534 more chars]",
  "content_hash": "9ad1d752b39149286e19ca394a5961955382396b1b87dd436e791d94adccd5d6",
  "token_count": 429,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "46d18f54-fe50-577a-8550-4864ce550175",
  "chunk_index": 12,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `546b52de-ec9d-59de-bd1a-ed8f0f0b51ed`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "1.1 Introduction - Dr K J Ramesh (cont.)\n\n1.5 Measures taken for Climate Change in Tamil Nadu - Mr T Karthikeyan:\nAgriculture is highly integrated into the challenge of climate change. Climate smart agriculture is needed as it is dependent on weather. Failure of rains and occurrence of natural disasters such as floods and droughts could lead to crop failures, food insecurity, famine, loss of property and life, mass migration and negative national economic growth. Certain planned adaptive measures like development of genetically adaptive varieties, hybrid seed programme, crop diversification pr\n\n… [+8570 more chars]",
  "content_hash": "91f228356de34328dd6b3e5d815412f5207e055f56346b8cfd67a5092cf61e7b",
  "token_count": 1842,
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
    14,
    17
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `251efb54-1375-589e-b2b5-9173d12f8118`

- vector: dim=3072 · [-0.0141, -0.0139, -0.0002, -0.0041, 0.0157, -0.0487, -0.0032, 0.0082, …]

```json
{
  "chunk_id": "251efb54-1375-589e-b2b5-9173d12f8118",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "1.5 Measures taken for Climate Change in Tamil Nadu - Mr T Karthikeyan:\nAgriculture is highly integrated into the challenge of climate change. Climate smart agriculture is needed as it is dependent on weather. Failure of rains and occurrence of natural disasters such as floods and droughts could lead to crop failures, food insecurity, famine, loss of property and life, mass migration and negative national economic growth. Certain planned adaptive measures like development of genetically adaptive varieties, hybrid seed programme, crop diversification programme etc. can help in improving the agr\n\n… [+1363 more chars]",
  "content_hash": "4c38db639162693f39e30b54e01afcdc3f00e2121f0b1fc42a1704c2a8522748",
  "token_count": 413,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "chunk_index": 13,
  "page_number": 14,
  "page_range": [
    14,
    14
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `0ca4a23b-16fb-556a-850b-6650acbd9263`

- vector: dim=3072 · [-0.0509, -0.0154, -0.0018, 0.0096, 0.0056, -0.0514, 0.0046, 0.0064, …]

```json
{
  "chunk_id": "0ca4a23b-16fb-556a-850b-6650acbd9263",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "There is a need for capacity building for the farmers to understand the usage of various chemicals in agriculture.\n1.6 Future Projections - Mr Saurabh Bhardwaj: The global climate change and variability is manifesting itself in terms of changing regional climate variability and extremes. The extremes are changing, the variability-the hot days and high rainfall days are increasing and simultaneously the dry days are increasing. So at one scale, flooding events in some parts are increasing, similarly in some parts, droughts are predominant. This has been an indication of global climate change in\n\n… [+1133 more chars]",
  "content_hash": "9d2eca99d376b51af0b9c730fe4599b3a46ac61110433b253e9ce5110e497cdb",
  "token_count": 329,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "chunk_index": 14,
  "page_number": 14,
  "page_range": [
    14,
    14
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `4c0b959f-6253-5b91-8c82-f8ed7ee4db30`

- vector: dim=3072 · [-0.0183, -0.0149, -0.0042, -0.0110, -0.0192, -0.0484, 0.0059, 0.0138, …]

```json
{
  "chunk_id": "4c0b959f-6253-5b91-8c82-f8ed7ee4db30",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "It has also brought out State specific and District specific models in regional and sectoral modeling in Maharashtra and West Bengal. It enhances the ability to deal with risks by stakeholders who are aware of the climate impacts. But, they need a policy backed\n14 direction and framework to start developing and implementing required measures. At the smaller scale, the municipalities are getting sensitive to the issues. Around 71 local bodies of Telangana were mandated to create a climate change action plan. TERI, has developed tools which are data-driven and user-centric, to help understand th\n\n… [+1025 more chars]",
  "content_hash": "4681a2d35e634f34afcf4e789e16950719fb9b96deea735d1dc171332ebdce4e",
  "token_count": 301,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "chunk_index": 15,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `6ebb334a-5394-5e33-8cbd-e20059d5f7f7`

- vector: dim=3072 · [-0.0002, -0.0299, -0.0089, -0.0111, 0.0142, -0.0523, -0.0034, 0.0089, …]

```json
{
  "chunk_id": "6ebb334a-5394-5e33-8cbd-e20059d5f7f7",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "Providing data driven information at local level by downscaling information from global level through Agro-met advisories is needed. This is possible as granularity allows it and application of data analytics enables faster processing for providing inputs in policy making.\n15 Session 2: Impacts on Agriculture, Mitigation and Adaptation Strategies\nChair: Dr S. Bhaskar, Assistant Director General, Natural Resources Management (NRM) Division, ICAR Co-chair: Mr Rajender Kumar Kataria, IAS, Principal Secretary, Agriculture Department, Government of Karnataka\nSpeakers:\n1. Dr R.H Laxman, Principal Sc\n\n… [+1052 more chars]",
  "content_hash": "268b8228b9db26b25008865d1ca8f8dc3fb26e6cf2b9dad50fe8d06afae0241b",
  "token_count": 379,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "chunk_index": 16,
  "page_number": 16,
  "page_range": [
    16,
    16
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `d2b6ecef-0b9f-561e-b49a-1e392bc23b3d`

- vector: dim=3072 · [-0.0191, 0.0029, -0.0060, 0.0129, 0.0102, -0.0241, -0.0035, -0.0002, …]

```json
{
  "chunk_id": "d2b6ecef-0b9f-561e-b49a-1e392bc23b3d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "Under the National Action plan on Climate Change Agriculture Mission, the focus is on four to five major components aiming on sustainable development goals. . There is a need to formulate the risk assessment map at the national level, state level and district level.\n16 Studies show that 85% of water is going for irrigation, and in the view of water vulnerability, this needs to be minimized. With Central Institute for Dry land Agriculture (CRIDA), activities such as identification and developing technologies, technology demonstration as well as simultaneously building the capacity of farmers ha\n\n… [+1866 more chars]",
  "content_hash": "a2b055d17fcd32a6574469ec813f5d264abf2d8502a9157f0e0657ad3cb432d6",
  "token_count": 466,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "chunk_index": 17,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `3549ab78-4dd3-5d89-bac1-09e4f360a5db`

- vector: dim=3072 · [-0.0065, 0.0192, -0.0146, 0.0036, 0.0091, -0.0075, 0.0192, 0.0078, …]

```json
{
  "chunk_id": "3549ab78-4dd3-5d89-bac1-09e4f360a5db",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "1.1 Introduction - Dr K J Ramesh",
  "chunk_text": "This can either be done through using demonstration projects or collaborating with universities to roll-out their research to real action on ground. Presently, a major portion of department's budget goes towards input subsidies; focus should also be on extension to spread use of better technologies, cropping systems, efficient irrigation methods etc. so that livelihood and income support is better for the farmers.\nTechnology demonstration to farmers should be one of the measures to secure a balance between the available technology and its uses. Also, there is a need to get farmers interested i\n\n… [+203 more chars]",
  "content_hash": "1c196eafe312b7f2c10e86993251831881d05466bb7a05835a2224b2ff9f6da7",
  "token_count": 144,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "546b52de-ec9d-59de-bd1a-ed8f0f0b51ed",
  "chunk_index": 18,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
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
  "section_heading": "2.3 Horticulture - Dr R H Laxman",
  "chunk_text": "2.3 Horticulture - Dr R H Laxman\n\nUnder the National Innovations in Climate Resilient Agriculture (NICRA) Project, seven core institutions have been identified to carry out the research work and development of adaptation strategies. Similarly, IIHR is one of the core institutions for initiating research work. Agriculture and horticulture will be impacted more by climate variability than the climate change. When crops are grown in various seasons, the critical stages of growing and being subject to abiotic stress becomes important. In Karnataka, drought like situation was created in July 2019, \n\n… [+3264 more chars]",
  "content_hash": "6af35f67b93f4b97ae8530ecdefe922a9e414955969561baf367e7132cd26f6e",
  "token_count": 757,
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
    17,
    18
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `46be6486-ef05-5235-9e30-e1ac85758ee8`

- vector: dim=3072 · [-0.0151, -0.0124, -0.0085, -0.0060, -0.0025, -0.0263, 0.0181, -0.0174, …]

```json
{
  "chunk_id": "46be6486-ef05-5235-9e30-e1ac85758ee8",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.3 Horticulture - Dr R H Laxman",
  "chunk_text": "Under the National Innovations in Climate Resilient Agriculture (NICRA) Project, seven core institutions have been identified to carry out the research work and development of adaptation strategies. Similarly, IIHR is one of the core institutions for initiating research work. Agriculture and horticulture will be impacted more by climate variability than the climate change. When crops are grown in various seasons, the critical stages of growing and being subject to abiotic stress becomes important. In Karnataka, drought like situation was created in July 2019, and in August month, northern Karn\n\n… [+160 more chars]",
  "content_hash": "f3b6e39331615b9b457127a8d5531cb912fcdb3a46dfddfe6f7fe734e0642fe1",
  "token_count": 142,
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
  "chunk_index": 19,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `aca1f6a5-b4d1-5678-9ea2-b527478ffeac`

- vector: dim=3072 · [-0.0232, -0.0367, -0.0021, 0.0057, -0.0093, -0.0458, 0.0104, 0.0008, …]

```json
{
  "chunk_id": "aca1f6a5-b4d1-5678-9ea2-b527478ffeac",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.3 Horticulture - Dr R H Laxman",
  "chunk_text": "In Karnataka, drought like situation was created in July 2019, and in August month, northern Karnataka had heavy rainfall. Onion crop could not be harvested and it rotted in fields. In monitoring such situations, weather forecasting plays a crucial role.\n17 Horticulture crops are crucial in mitigating risks of climate change. Apart from diversifying crop production, they provide employment, income and nutritional security. Under NICRA, State-of-the- Art facilities like Free Air Temperature Enhancement, Phenomics for identifying phenotypes, CO2 and Temperature gradient chambers and rain out she\n\n… [+1716 more chars]",
  "content_hash": "fcd41f52459df43fedc37064a5448c4f76de9150d1b47f41659fcdc6b5e11918",
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
  "parent_chunk_id": "f6a3e2fe-e821-5ecb-b16a-d3fda63976e2",
  "chunk_index": 20,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `aae1614d-c84f-537e-a219-5de3200e0e2f`

- vector: dim=3072 · [-0.0285, -0.0173, 0.0002, 0.0290, -0.0060, -0.0431, 0.0034, -0.0343, …]

```json
{
  "chunk_id": "aae1614d-c84f-537e-a219-5de3200e0e2f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.3 Horticulture - Dr R H Laxman",
  "chunk_text": "Similarly, based on the IPCC 21st century projections, global mean temperatures and sea level is projected to rise under all the scenarios. Worldwide, the precipitation over land has increased by ~1%, but in India monsoon rainfall has decreased by 5-8% and temperature increased by 20% in all summer monsoon rainfall.Climate change is leading to a wide range of issues for agriculture and the environment. For instance, climate warming enhances the survival of pests and thus, will lead to higher use of pesticides, etc. All this further damages the environment.\nEffects of higher temperature:\n· In m\n\n… [+549 more chars]",
  "content_hash": "ad04e739d3e45e28883d2e8fcc85c1fba6bb0ffcfe8b1745d97554e82f35e2fb",
  "token_count": 216,
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
  "chunk_index": 21,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `4c08fc0b-565e-52a8-ae3a-d7738bc49f31`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4c08fc0b-565e-52a8-ae3a-d7738bc49f31",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal\n\nThe impacts on agriculture can be direct (change in temperature, fertilization, etc.) and indirect (water scarcity, extremes, pests, etc.), will significantly impact agriculture productivity. This is inter- connected with the non-production aspects, which need to be looked at to assess the vulnerability of the sector and build resilience - such as transport, storage, processing and retailing.\nTogether, these factors impact India's food security. Climate change will have a mix of largely negative, but also some positive impacts for agriculture prod\n\n… [+6545 more chars]",
  "content_hash": "5a679d25c973487e00e5bd9527a87557565bca3edece9bee311e821fe5c9e215",
  "token_count": 1473,
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
    19,
    21
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `771061e9-a997-5328-af87-9bbefe063f4b`

- vector: dim=3072 · [0.0018, -0.0244, -0.0011, 0.0182, -0.0025, -0.0461, -0.0112, -0.0194, …]

```json
{
  "chunk_id": "771061e9-a997-5328-af87-9bbefe063f4b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "The impacts on agriculture can be direct (change in temperature, fertilization, etc.) and indirect (water scarcity, extremes, pests, etc.), will significantly impact agriculture productivity. This is inter- connected with the non-production aspects, which need to be looked at to assess the vulnerability of the sector and build resilience - such as transport, storage, processing and retailing.\nTogether, these factors impact India's food security. Climate change will have a mix of largely negative, but also some positive impacts for agriculture productivity, by region. According to the studies, \n\n… [+1655 more chars]",
  "content_hash": "8bee57bc2fd35e918afc310845afa7021ae992e3578d8a7c55cac9b3b7bc066b",
  "token_count": 437,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4c08fc0b-565e-52a8-ae3a-d7738bc49f31",
  "chunk_index": 22,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `8c3f3b89-9e32-50af-a1e4-5f65fc580390`

- vector: dim=3072 · [-0.0000, -0.0116, -0.0123, -0.0093, -0.0168, -0.0452, 0.0084, 0.0244, …]

```json
{
  "chunk_id": "8c3f3b89-9e32-50af-a1e4-5f65fc580390",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "They noted crop zone shifting may have to be done and ZBNF needs to be tested a little more before wider adoption.\n19 Session 3: The Policy Landscape; International to National and Sub-National Linkages\nChair: Mr. R.R Rashmi, Distinguished Fellow and Programme Director, Earth Science and Climate Change, TERI\nCo-chair: Dr. Sandeep Dave, IAS, Additional Chief Secretary, Department of Forest, Ecology and Environment, Government of Karnataka\nSpeakers:\n1) Dr. K.H Vinaykumar, IFS, Director, EMPRI\n2) Dr. S. Rajendra Prasad, Vice Chancellor, University of Agricultural Science, GKVK\n3) Dr. Amir Bashir \n\n… [+805 more chars]",
  "content_hash": "2f0d1cc2c44021da52f18ac4f751eab9c8359ef31a4392288e57073ae31ac40b",
  "token_count": 354,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4c08fc0b-565e-52a8-ae3a-d7738bc49f31",
  "chunk_index": 23,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `e74efe2a-eafa-57dd-a67b-7c90cc4a62ee`

- vector: dim=3072 · [-0.0160, 0.0059, -0.0050, 0.0046, 0.0047, -0.0170, 0.0196, -0.0025, …]

```json
{
  "chunk_id": "e74efe2a-eafa-57dd-a67b-7c90cc4a62ee",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "It also seeks to look at the developments in polices at the international level including the Paris agreement, the Sendai Framework and the SDGs. Implications at the country level and subnational scales were discussed in the form of India's National Missions on Climate\n20 Change, its Nationally Determined Contributions (NDCs) and the State Action Plans on Climate Change (SAPCCs). There is a need for enhanced financial resources, additional scientific knowledge and capacity building for farmers to address and prepare for these unanticipated risks.\n3.2 Schemes for Resilient Agriculture - Dr Sand\n\n… [+1898 more chars]",
  "content_hash": "d2efd4952ca78feaa0f780e5734195be398b105ca62f01cd5ec6d5bb2f89b639",
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
  "parent_chunk_id": "4c08fc0b-565e-52a8-ae3a-d7738bc49f31",
  "chunk_index": 24,
  "page_number": 21,
  "page_range": [
    21,
    21
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `2acafe61-0e12-5a5c-af75-75c1f592c947`

- vector: dim=3072 · [-0.0109, 0.0034, 0.0017, 0.0109, -0.0037, -0.0387, -0.0054, -0.0297, …]

```json
{
  "chunk_id": "2acafe61-0e12-5a5c-af75-75c1f592c947",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "Among all sectors, agriculture sector is likely to be impacted the most. Agriculture is highly vulnerable to climate change because of its wide exposure through changes in temperature, precipitation, pest attack and diseases. The National network project on Climate Change initiated by ICAR has projected a net decline of 2.5% in agricultural production over the next two to five decades. The Karnataka SAPCC, provided first comprehensive assessment of sectors that could be affected by climate change. It examined climate trends, projected vulnerabilities and adaptation and mitigation priorities. I\n\n… [+952 more chars]",
  "content_hash": "53bf6716578f3442a0da129ea08f9ec8bf5e55adcdfb3c39c0ed362b84249107",
  "token_count": 279,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "4c08fc0b-565e-52a8-ae3a-d7738bc49f31",
  "chunk_index": 25,
  "page_number": 21,
  "page_range": [
    21,
    21
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `302ba3cb-e8a1-55e5-81f6-51970642af8e`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal (cont.)\n\n3.4 Need for policies:\nIndia level information is limited and many successful initiatives go unreported. There is a need for better dissemination of knowledge and information sharing across states and regions. In a country like India, we need to make sure that adaptive measures are more critical as compared to the mitigation measures.\nDr. S. Rajendra Prasad:\nThe State has faced many adverse weather conditions in the last few years, however, productivity of crops has not been impacted much. Four areas identified for mitigation are:\n· Reduci\n\n… [+9145 more chars]",
  "content_hash": "a249615ec9aff432864a25fbe76ee6b9ac4f41805341faf028aa6e9d1eab8a93",
  "token_count": 2008,
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
    22,
    25
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `12cda1d6-2128-56b3-941c-5f713312b00c`

- vector: dim=3072 · [-0.0105, -0.0065, -0.0089, -0.0083, -0.0148, -0.0276, -0.0020, 0.0050, …]

```json
{
  "chunk_id": "12cda1d6-2128-56b3-941c-5f713312b00c",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "3.4 Need for policies:\nIndia level information is limited and many successful initiatives go unreported. There is a need for better dissemination of knowledge and information sharing across states and regions. In a country like India, we need to make sure that adaptive measures are more critical as compared to the mitigation measures.\nDr. S. Rajendra Prasad:\nThe State has faced many adverse weather conditions in the last few years, however, productivity of crops has not been impacted much. Four areas identified for mitigation are:\n· Reducing natural resources run-off;\n· Precision crop rating;\n\n\n… [+1278 more chars]",
  "content_hash": "60125d853f17a62847dc9ee81b11e0e90efae3d7f7a281b7452dd1321d2fae58",
  "token_count": 360,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "chunk_index": 26,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `72f0c4ea-a56d-510d-a0c6-b261c3790645`

- vector: dim=3072 · [0.0093, -0.0094, -0.0119, -0.0198, -0.0356, -0.0231, 0.0000, -0.0139, …]

```json
{
  "chunk_id": "72f0c4ea-a56d-510d-a0c6-b261c3790645",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "There is a lot of potential for knowledge networks to contribute to adaptation on the ground especially for small and marginal farmers. As knowledge is complex, there is a need to unpack and demystify the knowledge that benefits the people who are at the edge or at the margin. While climatic factors affect production, non-climatic factors influence experience of impact. Typically, small and marginal farmers have no asset base, lack access to knowledge and struggle for market linkage. In such a scenario, risk management intervention needs to be made in the social context. Localizing interventio\n\n… [+824 more chars]",
  "content_hash": "1237c1c63de74520f1d4d9da495ab7c6abc14826b2c2a017db6b21d38d1b78fd",
  "token_count": 276,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "chunk_index": 27,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `b4fbeffb-5caf-5001-b072-fa337f4bfd3f`

- vector: dim=3072 · [0.0011, -0.0184, 0.0005, 0.0088, -0.0334, -0.0453, 0.0022, -0.0486, …]

```json
{
  "chunk_id": "b4fbeffb-5caf-5001-b072-fa337f4bfd3f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "In recent years, coffee is being grown in North East, Andhra Pradesh and Odisha.\nIn a multi-country study of Coffee Agro-forestry, India stood top on most parameters. In Coorg\n22 area, coffee grown with multi-species is on a par with adjoining natural forest in terms of carbon sequestration and biodiversity conservation.\nIndia is the only country where 100% of coffee is grown under shade canopy and combined with mixed crops like spices, fruits etc.\nImpacts of climate change on coffee:\n· Rising temperatures may render certain producing areas less suitable or even completely unsuitable for coffe\n\n… [+1759 more chars]",
  "content_hash": "0276d0c8194eb1557764c6dc894f689586d11cdab26c5e8c91aee44f1bd97a28",
  "token_count": 479,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "chunk_index": 28,
  "page_number": 23,
  "page_range": [
    23,
    23
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `f70a1189-90c3-58f7-a11e-147ee8eec248`

- vector: dim=3072 · [-0.0209, -0.0020, -0.0117, -0.0059, -0.0126, -0.0497, -0.0063, 0.0148, …]

```json
{
  "chunk_id": "f70a1189-90c3-58f7-a11e-147ee8eec248",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "To reduce organic pollution in coffee processing, there is need to provide/promote zero discharge Pulpus machines which are expensive.\n3.5 Conclusion. The Chair summed up the key points made by Panellists at the end of each presentation and observed that a number of important suggestions have been made which are useful inputs in policy making. Further, in preparation of SAPCC, some suggestions could be incorporated for implementation.\n23\n\nSession 4: Case studies showcasing Sustainable Agriculture practices (including Integrated Farming Systems models) in emerging Climate Change Scenarios\nChair\n\n… [+1205 more chars]",
  "content_hash": "5b2f4f092f30cd6713177dd642b3aa41ccee410adf61a89b855326774879db32",
  "token_count": 438,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "chunk_index": 29,
  "page_number": 23,
  "page_range": [
    23,
    24
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `22c24e49-af81-5071-b931-b9c6caf8f39d`

- vector: dim=3072 · [-0.0172, 0.0045, -0.0049, 0.0027, 0.0100, -0.0327, 0.0157, 0.0184, …]

```json
{
  "chunk_id": "22c24e49-af81-5071-b931-b9c6caf8f39d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "aches to Shaping Climate Resilient Agriculture\nApri Partner\nKAOH\nBengaluru\n28th February 2020\n@\nASSOCHAM\n15\nBM\nASSERTIES\nCHAM Aos\nASSOCHAM\n1\nASSOCHA\n24 4.1 Introduction - Dr Ashok Dalwai:\nClimate Change that was doubted few years back has now been accepted across the globe. The linear trend in rise of temperature is 0.64 in 1905 till 1995 and has increased to 0.74 from 1995-2004. The hottest 12 years were recorded in recent times during the period 1996 to 2006. Human intervention has accelerated the pace of GHGs addition in atmosphere and is challenging mankind to develop adaptation measures. \n\n… [+1435 more chars]",
  "content_hash": "fdde19fe2d00b63d8fbf48b6adbbf67c6aea05592530344004fbcee85f7a75d0",
  "token_count": 428,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "chunk_index": 30,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `4b585fae-807c-585b-b86c-c5002833edbe`

- vector: dim=3072 · [-0.0340, 0.0049, -0.0071, 0.0224, 0.0122, -0.0021, 0.0102, 0.0125, …]

```json
{
  "chunk_id": "4b585fae-807c-585b-b86c-c5002833edbe",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "Major components under the project:\n· Designing household level adaptation interventions based on vulnerability assessment\n· Developing information system\n· Capacity building for implementing climate smart strategies NABARD is the implementing agency, EPTRI is the executing agency, DOA, PJTSAU, and ICRISAT are technical partners of the project. The project cost is Rs. 24 crore covering 3438 farmers of the Mahbubnagar district in 3 mandals and 15 villages. A baseline survey of 8400 farmers was done and their vulnerability to climate was classified under four categories. Sensitizing farmers abou\n\n… [+559 more chars]",
  "content_hash": "decc67b218ea730c58606845af7aade765b5ee245b9dc34c5b826c00bcf19166",
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
  "parent_chunk_id": "302ba3cb-e8a1-55e5-81f6-51970642af8e",
  "chunk_index": 31,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `b0dea1fa-b1bc-547b-a7c2-579828526055`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "b0dea1fa-b1bc-547b-a7c2-579828526055",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal (cont.)\n\n4.3 Promoting the use of agro-meteorological information - Dr P Vijaya Kumar:\nUnder the All India Coordinated Project on Agro-meteorology, 25 centres have been set up which are working on 5 themes. Weather and climate information in Agriculture can help in procurement of inputs for timely sowing, to plan cropping systems, selection of crop / variety, timely sowing / transplanting, irrigation scheduling, fertilizers application, timing of plant protection & reduce indiscriminate pesticide usage, harvesting etc.\nThe project on the use of agr\n\n… [+7190 more chars]",
  "content_hash": "e2d3adae39034bc5741b120678d34d4dbaa38227726f52e4d655a3e8c66cc84e",
  "token_count": 1627,
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
    26,
    29
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `fe7aa908-dae7-55e6-8020-b9852fc1501d`

- vector: dim=3072 · [-0.0138, -0.0316, -0.0021, -0.0142, -0.0250, -0.0315, 0.0192, 0.0023, …]

```json
{
  "chunk_id": "fe7aa908-dae7-55e6-8020-b9852fc1501d",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "4.3 Promoting the use of agro-meteorological information - Dr P Vijaya Kumar:\nUnder the All India Coordinated Project on Agro-meteorology, 25 centres have been set up which are working on 5 themes. Weather and climate information in Agriculture can help in procurement of inputs for timely sowing, to plan cropping systems, selection of crop / variety, timely sowing / transplanting, irrigation scheduling, fertilizers application, timing of plant protection & reduce indiscriminate pesticide usage, harvesting etc.\nThe project on the use of agro-meteorological information aims at better planning fo\n\n… [+1366 more chars]",
  "content_hash": "b628d74bb24f0158fba0309ed2ef6ef240499f79e200ee5933c81e9067e326da",
  "token_count": 379,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "b0dea1fa-b1bc-547b-a7c2-579828526055",
  "chunk_index": 32,
  "page_number": 26,
  "page_range": [
    26,
    26
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `feefe60f-2e11-5031-a932-bacf8bdd7a7b`

- vector: dim=3072 · [-0.0136, -0.0197, -0.0053, 0.0003, -0.0165, -0.0475, 0.0071, -0.0048, …]

```json
{
  "chunk_id": "feefe60f-2e11-5031-a932-bacf8bdd7a7b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "Similar systems/products required to be set up for horticulture and poultry. To conclude he stated that characterization of climate and climate analogues is the need of the hour.\n4.4 Impact of Climate Change on Coffee - Mr Cariappa M R: India grows about 3% of the world coffee and, therefore has no say in the prices of coffee. Kodagu district has faced huge challenges in terms of climate change hampering the quality and production of coffee. There is a need to focus on Capacity Building. In relation to this every month, two training programs across multiple topics are held. 30% of farmers atte\n\n… [+960 more chars]",
  "content_hash": "9062811064750fad56f06f21c8aa70c2eec3c55f295c803d0180b3b99b7b5d54",
  "token_count": 320,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "b0dea1fa-b1bc-547b-a7c2-579828526055",
  "chunk_index": 33,
  "page_number": 26,
  "page_range": [
    26,
    26
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `13354a34-caf1-51a3-b8fd-ea86bd670187`

- vector: dim=3072 · [-0.0008, -0.0088, -0.0050, -0.0004, -0.0022, -0.0444, -0.0210, 0.0205, …]

```json
{
  "chunk_id": "13354a34-caf1-51a3-b8fd-ea86bd670187",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "The project on climate smart rubber cultivation which is an option for changing climate situations was highlighted. Rubber can grow in temperature that can go less than 10 degree Celsius in North East\n26 India and more than 40 degrees in Maharashtra. One ton of rubber produced removes more than 10 tons of carbon from atmosphere. Thus, 2.1% of the current rate of CO2 increase in the atmosphere has been reversed by the world's natural rubber plantation. Barren land can be converted to a forest by growing rubber plantation. Rubber is commercially and ecologically significant.\nIntroduction of suit\n\n… [+1832 more chars]",
  "content_hash": "5b2741fa4865480b29e88f0566c4fa4dc19ed0f9113f37d848dd17986275ee27",
  "token_count": 482,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "b0dea1fa-b1bc-547b-a7c2-579828526055",
  "chunk_index": 34,
  "page_number": 27,
  "page_range": [
    27,
    27
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `800ab434-4436-5e72-b59e-148cc827350b`

- vector: dim=3072 · [-0.0082, 0.0028, -0.0047, -0.0280, -0.0136, -0.0427, 0.0003, 0.0301, …]

```json
{
  "chunk_id": "800ab434-4436-5e72-b59e-148cc827350b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "Panellists with the observations that:\n· Weather advisories are helpful to negotiate climate risks and Karnataka is a pioneer in setting up such facility to provide advance information;\n· Standardised data formats need to be evolved for better data management, remote sensing information to be matched with actual ground situation; and, . Where rational use of inputs results in loss of income in the short term, compensation needs to be provided.\n27\n\nSession 5: Climate Finance: Garnering Support for Actions\nChair: Ms Ulka Kelkar, Director - Climate Program, World Resources Institute (WRI), India \n\n… [+1070 more chars]",
  "content_hash": "0f9f4912988b96d0cfedfea22649eb697e915609e79a63089cec6f96dbb68aae",
  "token_count": 393,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "b0dea1fa-b1bc-547b-a7c2-579828526055",
  "chunk_index": 35,
  "page_number": 27,
  "page_range": [
    27,
    28
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `7edd0030-f19d-5d4a-9fbb-79521bfae44a`

- vector: dim=3072 · [-0.0341, 0.0050, -0.0096, -0.0087, -0.0169, -0.0200, 0.0150, -0.0164, …]

```json
{
  "chunk_id": "7edd0030-f19d-5d4a-9fbb-79521bfae44a",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "2.5 Impacts & Strategies - Ms Suruchi Bhadwal",
  "chunk_text": "Adaptation investments, specifically in agriculture, offer an opportunity to leverage both climate and sustainable development benefits. However, the benefits of adaptation are difficult to quantify\n28\nY\nCeletrường 102 Years in monetary terms and take time for impacts to show up, and this acts as a barrier to raising current adaptation investments and mobilizing them in future.\nFinance is the key and necessary to all approaches that are taken in meeting the climate change goals in agriculture. It has 3 features viz.,\n1. Cross-cutting in nature - it is the only thing that can cut across departm\n\n… [+504 more chars]",
  "content_hash": "05952e76e2e40068dfdc80d97ff74fa1b9cf8937ab008a0b14b673096d1a60f1",
  "token_count": 224,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "b0dea1fa-b1bc-547b-a7c2-579828526055",
  "chunk_index": 36,
  "page_number": 29,
  "page_range": [
    29,
    29
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "5.2 NABARD - Mr C V Reddy\n\nNABARD is a National Implementing Entity (NIE) and Direct Access Entity for accessing funds from -\n(a) Green Climatic Fund(GCF); and, (b) Adaptation Fund under UNFCC.\nGCF is based on voluntary contributions and hence limited in its fund size. About 134 million US Dollars has been provided for two projects. Under Adaptation fund, 10 million US Dollars was available which has been fully utilized.\nNABARD is also the NIE for National Adaptation fund for Climate Change and has funded 30 projects. It does the work of appraisal monitoring of utilization of funds and physica\n\n… [+10183 more chars]",
  "content_hash": "dbbe2c843ef535b879a505ff7b2a6d53c6c372356bc49439bd313feb166a2810",
  "token_count": 2156,
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
    29,
    32
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `ea6fd048-cbdd-51f6-94de-f4fd4064b9ea`

- vector: dim=3072 · [-0.0475, 0.0257, -0.0101, -0.0129, -0.0042, -0.0199, 0.0329, 0.0263, …]

```json
{
  "chunk_id": "ea6fd048-cbdd-51f6-94de-f4fd4064b9ea",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "NABARD is a National Implementing Entity (NIE) and Direct Access Entity for accessing funds from -\n(a) Green Climatic Fund(GCF); and, (b) Adaptation Fund under UNFCC.\nGCF is based on voluntary contributions and hence limited in its fund size. About 134 million US Dollars has been provided for two projects. Under Adaptation fund, 10 million US Dollars was available which has been fully utilized.\nNABARD is also the NIE for National Adaptation fund for Climate Change and has funded 30 projects. It does the work of appraisal monitoring of utilization of funds and physical progress.\nIn addition, to\n\n… [+1553 more chars]",
  "content_hash": "fbc88aad1509126e50909a1e369bf1912abb81177119aa08e1c66c71aedd2970",
  "token_count": 443,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "chunk_index": 37,
  "page_number": 29,
  "page_range": [
    29,
    29
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `c31d659a-4038-5d97-899f-3dfd3101d947`

- vector: dim=3072 · [-0.0329, 0.0287, -0.0095, 0.0143, -0.0257, -0.0331, 0.0311, 0.0218, …]

```json
{
  "chunk_id": "c31d659a-4038-5d97-899f-3dfd3101d947",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "Information on each parcel of land has been given in 12 districts covering 44 taluks. The Decision Support System will also be linked to Agro-met in the new watershed project termed as REVIVE, under which 10 lakh hectare will be covered.\n29 Finance is an issue but there are opportunities. Following are the projects that are being undertaken by the department:\n· Sujala I- World bank funded\n· Sujala II- NABARD funded\n· Sujala III- World bank funded, 14 consortium partners (the project was completed in December 2019)\nGovernment of India funded Integrated Watershed project will be coming to an end\n\n… [+1761 more chars]",
  "content_hash": "903c943bdc0b1d84f43d6f0b3bb8e658cbc50563c1cc0c723db5a9c2c34ce5ee",
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
  "parent_chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "chunk_index": 38,
  "page_number": 30,
  "page_range": [
    30,
    30
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `bd6defc8-2de1-51aa-a6e6-081daa774a97`

- vector: dim=3072 · [-0.0460, 0.0193, -0.0158, 0.0341, -0.0420, -0.0147, -0.0055, 0.0088, …]

```json
{
  "chunk_id": "bd6defc8-2de1-51aa-a6e6-081daa774a97",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "Climate change adaptation is one of the core components in the financing of projects. One of the main programs- The Umbrella Programme in Natural Resource Management is in partnership with NABARD. This was the first project in India that brought a paradigm shift from grant based projects to loan based projects. The annual commitment to projects is one billion Euros. In India, energy, sustainable urban development and annual resource management are the key sectors. Financing is done through the channel partners viz., Corporates, NGOs, FPOs, FPCs, Banks and State governments. For example, Omnivo\n\n… [+429 more chars]",
  "content_hash": "01bf849d8688272dc7eb82ab4edcee7d4cb0b5551de3e2c4d786f409cfca5307",
  "token_count": 203,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "chunk_index": 39,
  "page_number": 30,
  "page_range": [
    30,
    30
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `936eef86-f3fb-5845-9240-c72b0bdcbded`

- vector: dim=3072 · [-0.0358, 0.0207, -0.0116, 0.0095, -0.0181, -0.0303, 0.0470, 0.0046, …]

```json
{
  "chunk_id": "936eef86-f3fb-5845-9240-c72b0bdcbded",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "Mainstreaming was possible where the bank was tied up with a NGO. The creation of credit guarantee fund was necessary in this project.\nThe Andhra Pradesh Zero Budget Natural Farming-loan based agricultural project is being\n30 implemented. With the goal of reaching out to all farmers, sound institutional structure is made available. This was a major consideration for providing loan financing by KfW. The major challenges faced are : (a) Agricultural Financing is still a niche market, (b) High level subsidies creating market distortions, and (c) Preponderance of small and marginal farmers.\nPresen\n\n… [+1835 more chars]",
  "content_hash": "2afcee1d393878aceec578d8437236de18c2bb90e341dfb3e3beb00d80fa3d4a",
  "token_count": 493,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "chunk_index": 40,
  "page_number": 31,
  "page_range": [
    31,
    31
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `530dc5a6-d7c4-50bd-9933-a0b858c4fa1f`

- vector: dim=3072 · [-0.0242, -0.0031, -0.0121, -0.0186, -0.0148, -0.0346, 0.0284, 0.0020, …]

```json
{
  "chunk_id": "530dc5a6-d7c4-50bd-9933-a0b858c4fa1f",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "Digital banking is promoted through the Yono Krishi App, which helps in providing quick weather updates, getting inputs through online orders, and advisories from several agricultural experts.\nThere has been adaption of solar ATMs across India. All offices, have completely eradicated the use of plastics. SBI has also financed land reclamation programme for reclaiming saline soils to an extent of 5000 acres in Bagalkot district. SBI has financed more than 2000 irrigation projects in north Karnataka and sub-surface drip irrigation projects for sugar cane in Belgaum district.\nOne suggestion made \n\n… [+637 more chars]",
  "content_hash": "a6ceb5364c1478d066731adb1319d7c53d62ca1592d129b4bf52b30dd40f8892",
  "token_count": 233,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "chunk_index": 41,
  "page_number": 31,
  "page_range": [
    31,
    31
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `0b6292fa-533d-5fc7-b3e0-077f3c4cb69b`

- vector: dim=3072 · [-0.0226, 0.0059, -0.0017, -0.0020, -0.0199, -0.0299, 0.0301, 0.0240, …]

```json
{
  "chunk_id": "0b6292fa-533d-5fc7-b3e0-077f3c4cb69b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "5.2 NABARD - Mr C V Reddy",
  "chunk_text": "Last mile delivery to small farmers is another main issue. International Climate Funds are very limited in this area and thus, need to bring in private financing.\n31 There is a requirement for enhancing the capacity of the farmers who need to understand the risks and possible benefits. 22 case studies have revealed that the following 3 aspects are important.\nCapacity building is required for (i) farmers to understand risks and mitigating it, (ii) Bank officers and Government officers to know about available technology/methodology in risk mitigation, and (iii) private sector to know opportuniti\n\n… [+2186 more chars]",
  "content_hash": "148341e60922e07d72780a824beba0235ea8610c4ac978ecf7f3b3bd5019072a",
  "token_count": 511,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "d08b1279-a3b4-5bc4-ba3a-fe8ec2cae0c4",
  "chunk_index": 42,
  "page_number": 32,
  "page_range": [
    32,
    32
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `e08add95-dc53-5ca0-892d-d4b545ad4017`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e08add95-dc53-5ca0-892d-d4b545ad4017",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Valedictory Session — Banking Partners — Gold Partners — Supporting Partner Y — ASSOCHAM",
  "chunk_text": "Valedictory Session — Banking Partners — Gold Partners — Supporting Partner Y — ASSOCHAM\n\nteri\nTHE ENERGY AND RESOURCES INSTITUTE\nDning Media Partners\nConference on\nTCI\nJagran\nA\npaches Ce\nAgri Partner\naping as ate Resili Agricultu\nO\nASSOC\nThe Valedictory session started with Dr. Annapurna Vancheswaran Senior Director, TERI putting the session in context by acknowledging Honourable Chief Minister of Karnataka, Shri. B.S. Yediyurappa for giving us his valuable time to flag off this conference on 'Approaches to Shaping Climate Resilient Agriculture'. Karnataka, having the second largest area unde\n\n… [+5770 more chars]",
  "content_hash": "93ac09aa9c496e26406c6e090da6f712a8aa6d4f866a6d8d52932f83d0057b11",
  "token_count": 1244,
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
    35
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `57ed357e-b63a-58cb-a9e2-c5841c7f15ed`

- vector: dim=3072 · [-0.0046, -0.0190, -0.0117, -0.0297, -0.0184, -0.0423, 0.0052, 0.0200, …]

```json
{
  "chunk_id": "57ed357e-b63a-58cb-a9e2-c5841c7f15ed",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Valedictory Session — Banking Partners — Gold Partners — Supporting Partner Y — ASSOCHAM",
  "chunk_text": "teri\nTHE ENERGY AND RESOURCES INSTITUTE\nDning Media Partners\nConference on\nTCI\nJagran\nA\npaches Ce\nAgri Partner\naping as ate Resili Agricultu\nO\nASSOC\nThe Valedictory session started with Dr. Annapurna Vancheswaran Senior Director, TERI putting the session in context by acknowledging Honourable Chief Minister of Karnataka, Shri. B.S. Yediyurappa for giving us his valuable time to flag off this conference on 'Approaches to Shaping Climate Resilient Agriculture'. Karnataka, having the second largest area under rainfed agriculture, has higher vulnerability and in this regard, it is important to ana\n\n… [+1286 more chars]",
  "content_hash": "88366684e9e0cd2f9027da54038f246377e96bec687874605d69b31b527b3d47",
  "token_count": 378,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "e08add95-dc53-5ca0-892d-d4b545ad4017",
  "chunk_index": 43,
  "page_number": 33,
  "page_range": [
    33,
    33
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `bffb78a2-4588-58a7-8a00-c1b473772e65`

- vector: dim=3072 · [-0.0051, -0.0186, -0.0085, -0.0231, -0.0036, -0.0371, 0.0276, 0.0085, …]

```json
{
  "chunk_id": "bffb78a2-4588-58a7-8a00-c1b473772e65",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Valedictory Session — Banking Partners — Gold Partners — Supporting Partner Y — ASSOCHAM",
  "chunk_text": "She commended the deliberations that were carried out in the conglomeration of speakers with various backgrounds like policy makers, practitioners from government, scientists, academicians, sector experts, leaders from industry and trade, farmer producing organizations, senior officers of major banks and financial organizations, etc.\n33 Mr T.M Vijay Bhaskar, Chief Secretary, Government of Karnataka In his Valedictory Address, highlighted that agriculture and farmers welfare is the top priority of the Government, which has also been mentioned by the Honourable Chief Minister. Indian agriculture\n\n… [+1495 more chars]",
  "content_hash": "4ebc6846f3fe74fc127f550a9e44be4b77f573660a870eb8480559c58f257280",
  "token_count": 384,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "e08add95-dc53-5ca0-892d-d4b545ad4017",
  "chunk_index": 44,
  "page_number": 34,
  "page_range": [
    34,
    34
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `0010f922-e7c6-56ed-89c3-a9c43652ba94`

- vector: dim=3072 · [-0.0057, 0.0080, -0.0097, -0.0137, -0.0078, -0.0449, 0.0092, 0.0080, …]

```json
{
  "chunk_id": "0010f922-e7c6-56ed-89c3-a9c43652ba94",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Valedictory Session — Banking Partners — Gold Partners — Supporting Partner Y — ASSOCHAM",
  "chunk_text": "He mentioned about micro irrigation projects, which are bringing in water use efficiency in the irrigation sector and referred to the investment made in Ramthal project. He suggested that TERI can undertake evaluation of this project for its success and indicate the lessons learnt in its implementation. Karnataka is a major producer of millets which are climate resilient in nature. He recalled that the State had organized an international conference on millets and many major initiations have been taken to promote cultivation of millets and also expansion of market for millets. The State has al\n\n… [+2340 more chars]",
  "content_hash": "fa1c9b3e468d2d3dab3ae9c753e7b08dc5486f0cfdd911aabc533fa9739858e5",
  "token_count": 571,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "e08add95-dc53-5ca0-892d-d4b545ad4017",
  "chunk_index": 45,
  "page_number": 34,
  "page_range": [
    34,
    35
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `84e6b3e3-f14d-5eba-9f0e-a458e1c24773`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "84e6b3e3-f14d-5eba-9f0e-a458e1c24773",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Key Takeaways and Suggestions",
  "chunk_text": "Key Takeaways and Suggestions\n\n1. Climate Change has huge impacts on multiple sectors. Its impacts in agriculture can be a result of changes in average temperatures, rainfall and climate extremes (flood, droughts). It will have a mix of largely negative, but also some positive impacts for agriculture productivity, by region. Agriculture and allied sectors continue to play a significant role in terms of employment, income and national food security. The contribution of agriculture to Gross Value Added (GVA) was 16.5% in 2019-20. About 50% of population is dependent on agriculture.\n2. While clim\n\n… [+3959 more chars]",
  "content_hash": "14d4351825bd57d70043fec2d5d859868c7e0099fb377a0a9123e8bcdcc39a89",
  "token_count": 869,
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
    36,
    37
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `9aa4b332-417f-50a3-9047-f37b9f358645`

- vector: dim=3072 · [-0.0041, -0.0036, -0.0044, 0.0097, -0.0021, -0.0367, 0.0032, -0.0199, …]

```json
{
  "chunk_id": "9aa4b332-417f-50a3-9047-f37b9f358645",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Key Takeaways and Suggestions",
  "chunk_text": "1. Climate Change has huge impacts on multiple sectors. Its impacts in agriculture can be a result of changes in average temperatures, rainfall and climate extremes (flood, droughts). It will have a mix of largely negative, but also some positive impacts for agriculture productivity, by region. Agriculture and allied sectors continue to play a significant role in terms of employment, income and national food security. The contribution of agriculture to Gross Value Added (GVA) was 16.5% in 2019-20. About 50% of population is dependent on agriculture.\n2. While climate change is global in nature,\n\n… [+1616 more chars]",
  "content_hash": "71ea5e2e1095f80650deaa98260391575089fb0ca49edadd107d03bf207ce8b3",
  "token_count": 418,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "84e6b3e3-f14d-5eba-9f0e-a458e1c24773",
  "chunk_index": 46,
  "page_number": 36,
  "page_range": [
    36,
    36
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `5a691cb6-c36d-53d9-8a4e-e9fc4b091ea5`

- vector: dim=3072 · [-0.0104, -0.0060, 0.0034, -0.0019, -0.0010, -0.0197, 0.0179, 0.0280, …]

```json
{
  "chunk_id": "5a691cb6-c36d-53d9-8a4e-e9fc4b091ea5",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Key Takeaways and Suggestions",
  "chunk_text": "Certain policy measures like PMKSY scheme benefits to be extended to coffee cultivation, Pulpus machines for coffee processing, promoting cultivation of native species of shade trees, and in Rubber, funding support from Ministries of Agriculture and Environment has been suggested. 5. The farming community in India is faced with low income & poverty. There is a need to focus on farm income approach. Agro-met advisory services and weather based insurance products are helpful. Also, characterization of climate and climate analogues is the need of the hour.\n6. It was widely accepted and suggested \n\n… [+1993 more chars]",
  "content_hash": "f3d952a043f2ce7eda11195afb4bf44309b2c1f9c51f4a9156fb9e71be6664d4",
  "token_count": 496,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "84e6b3e3-f14d-5eba-9f0e-a458e1c24773",
  "chunk_index": 47,
  "page_number": 36,
  "page_range": [
    36,
    37
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
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
  "section_heading": "Annexure",
  "chunk_text": "Annexure\n\nAgenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India\n8:00-9:00\nRegistration\n9:00-10:30\nSession 1: Exposure to climatic risks: Developing an understanding of the risks at the sub-national scales\nChair: Dr K.J Ramesh, Former Director General, India Meteorological Department\nCo-Chair: Mr T.K Anil Kumar, IAS, Principal Secretary, Revenue Department, Government of Karnataka\nSpeakers:\n. Dr. G.S Srinivasa Reddy, Director, Karnataka State Natural Disaster Monitoring Centre\n· Mr Harikumar B, Assistant Director (Agriculture), Project Prep\n\n… [+4005 more chars]",
  "content_hash": "5be29b0411cdbd4cd0ee2cfcf8678af2229b577f88c365f438b1fb29536d195d",
  "token_count": 1165,
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
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `c266884e-c7c9-537e-ac49-466808ec97df`

- vector: dim=3072 · [-0.0084, -0.0311, -0.0086, -0.0284, 0.0035, -0.0527, 0.0138, 0.0297, …]

```json
{
  "chunk_id": "c266884e-c7c9-537e-ac49-466808ec97df",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Annexure",
  "chunk_text": "Agenda: Approaches to Shaping Climate Resilient Agriculture 28th February, The Lalit Ashok, Bengaluru, India\n8:00-9:00\nRegistration\n9:00-10:30\nSession 1: Exposure to climatic risks: Developing an understanding of the risks at the sub-national scales\nChair: Dr K.J Ramesh, Former Director General, India Meteorological Department\nCo-Chair: Mr T.K Anil Kumar, IAS, Principal Secretary, Revenue Department, Government of Karnataka\nSpeakers:\n. Dr. G.S Srinivasa Reddy, Director, Karnataka State Natural Disaster Monitoring Centre\n· Mr Harikumar B, Assistant Director (Agriculture), Project Preparation an\n\n… [+1122 more chars]",
  "content_hash": "ffe3b956bf6e9943aaefcedf11832c0bd34d07166a9fee3be4e266b5303199cf",
  "token_count": 450,
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
  "chunk_index": 48,
  "page_number": 38,
  "page_range": [
    38,
    38
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `fd96db20-5340-5ca1-be90-6f447ce61eec`

- vector: dim=3072 · [0.0044, -0.0234, -0.0083, -0.0097, -0.0202, -0.0513, -0.0082, 0.0325, …]

```json
{
  "chunk_id": "fd96db20-5340-5ca1-be90-6f447ce61eec",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Annexure",
  "chunk_text": "M.B Rajegowda, Former Professor and Head All India Coordinated Research Project on Agro- meteorology, University of Agricultural Sciences, GKVK . Dr. R.H Laxman, Principal Scientist, Division of Plant Physiology and Biochemistry, ICAR- Indian Institute of Horticultural Research (IIHR)\n. Ms Suruchi Bhadwal, Senior Fellow, Earth Science and Climate Change, TERI\n38\n\nSession 3: The policy landscape; international to national and sub-national linkages\nChair: Mr R.R Rashmi, Distinguished Fellow & Programme Director, Earth Science and Climate Change ,TERI\nCo-chair: Dr. Sandeep Dave, IAS, Additional C\n\n… [+1561 more chars]",
  "content_hash": "fcf85b3d708f9d244da3c0ccd4ab211f4204e00093cd3b68629b83736e1bf6d8",
  "token_count": 524,
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
  "chunk_index": 49,
  "page_number": 38,
  "page_range": [
    38,
    39
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `bb3eab12-386d-5b0c-9b0d-2d8ae4f8cafc`

- vector: dim=3072 · [-0.0102, -0.0033, -0.0071, -0.0349, -0.0117, -0.0568, 0.0106, 0.0367, …]

```json
{
  "chunk_id": "bb3eab12-386d-5b0c-9b0d-2d8ae4f8cafc",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "Annexure",
  "chunk_text": "Debabrata Ray, Scientist, Regional Research Station, Rubber Research Institute of India, Rubber Board\n16:15-17:30\nSession 5: Climate Finance: Garnering Support for Actions Chair: Ms Ulka Kelkar, Director - Climate Program, World Resources Institute\n(WRI), India Co-chair: Mr C.V Reddy, Deputy General Manager, Karnataka Regional Office, NABARD Speakers:\n. Mr Prabhash Chandra Ray, IFS, Additional Principal Chief Conservator of Forests & Commissioner Watershed Development Department & Ex-officio Secretary to Government, Agriculture & Horticulture Department, Government of Karnataka\n· Ms Sangeeta A\n\n… [+426 more chars]",
  "content_hash": "5d8079b43047cf64dac09e01859eb329f9dd93c5596e140b16095245a3ee7a51",
  "token_count": 257,
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
  "chunk_index": 50,
  "page_number": 39,
  "page_range": [
    39,
    39
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Parent · `aaedcadf-dc4e-5b10-b87a-8ca9d6950e51`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "aaedcadf-dc4e-5b10-b87a-8ca9d6950e51",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "List of Participants\n\nSl. No.\nName\nDesignation\nOrganization\n1\nDr. B.L. Manjunath\nPrincipal Scientist\nICAR - IIHR\n2\nDr Suneel Kunamaneni\nSenior Lecturer in Innovation Management\nLeeds Beckett University\n3\nMr Anoop H V\nManager Exports\nIndira Food Pvt.Ltd\n4\nMr Imtimongla Jamir\nExecutive - Social Media\nAVIANWE\n5\nMr S S M Gavaskar\nScientist\nKarnataka State Natural Disaster Monitoring Centre\n6\nMr Shankara Hebbar\nPrincipal Scientist\nICAR - IIHR\n7\nMs Anitha Reddy\nDirector\nSahaja Samrudha Organic Producer Company Ltd\n8\nMr Chacochan Muller\nHead - Sales\nBarrix Agro\n9\nDr. S. Kannan\nHead - R&D\nBarrix Agro\n\n\n… [+3579 more chars]",
  "content_hash": "7db6cdd1b2a5ab8d4d3d03c2b95166f806998704da99066aa41e99fb7a0136cf",
  "token_count": 1219,
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
    43
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `b2e5bbe4-bbfc-5ed8-8828-973bb4cc6583`

- vector: dim=3072 · [0.0087, -0.0156, -0.0104, -0.0446, -0.0088, -0.0345, 0.0157, 0.0227, …]

```json
{
  "chunk_id": "b2e5bbe4-bbfc-5ed8-8828-973bb4cc6583",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "Sl. No.\nName\nDesignation\nOrganization\n1\nDr. B.L. Manjunath\nPrincipal Scientist\nICAR - IIHR\n2\nDr Suneel Kunamaneni\nSenior Lecturer in Innovation Management\nLeeds Beckett University\n3\nMr Anoop H V\nManager Exports\nIndira Food Pvt.Ltd\n4\nMr Imtimongla Jamir\nExecutive - Social Media\nAVIANWE\n5\nMr S S M Gavaskar\nScientist\nKarnataka State Natural Disaster Monitoring Centre\n6\nMr Shankara Hebbar\nPrincipal Scientist\nICAR - IIHR\n7\nMs Anitha Reddy\nDirector\nSahaja Samrudha Organic Producer Company Ltd\n8\nMr Chacochan Muller\nHead - Sales\nBarrix Agro\n9\nDr. S. Kannan\nHead - R&D\nBarrix Agro\n10\nMs Sapna Harihar\nAg\n\n… [+895 more chars]",
  "content_hash": "8b08390f0eb0ea85f484d86029c1b0cce54873b751f22c088992f871de472947",
  "token_count": 447,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "aaedcadf-dc4e-5b10-b87a-8ca9d6950e51",
  "chunk_index": 51,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `04120c09-951d-514d-950a-a6adfe12c4e3`

- vector: dim=3072 · [0.0245, -0.0259, -0.0060, -0.0104, -0.0111, -0.0216, -0.0061, 0.0282, …]

```json
{
  "chunk_id": "04120c09-951d-514d-950a-a6adfe12c4e3",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "arnataka Agribusiness Development Corporation\n20\nMr C R Janardhana\nPresident\nFederation of Karnataka Chambers of Commerce and Industry\n21\nMr M Sugnama Murthy\nSecretary\nFederation of Karnataka Chambers of Commerce and Industry\n22\nMr M Lokaraj\nSecretary General Federation of Karnataka Chambers of Commerce and Industry\n23\nMr N Jhansi Rani\nStudent (PhD Bachelor)\nUniversity of Horticultural Science - Bangalore\n24\nDr M A Shankar\nProfessor\nUniversity of Agricultural Sciences\n25\nMr H C Prasanna\nPrincipal Scientist\nICAR - IIHR\n26\nDr V Sridhar\nPrincipal Scientist\nICAR - IIHR\n27\nMs Arathi\nBusiness Develo\n\n… [+152 more chars]",
  "content_hash": "9b8e422b448d3eccaa30d53dcf8ea45c0fa4df929355e96b8986de75184371d8",
  "token_count": 187,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "aaedcadf-dc4e-5b10-b87a-8ca9d6950e51",
  "chunk_index": 52,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `b2b4cb13-5c5d-558c-a8d4-e308776ce4cf`

- vector: dim=3072 · [0.0108, -0.0143, -0.0094, -0.0377, -0.0209, -0.0169, 0.0070, 0.0137, …]

```json
{
  "chunk_id": "b2b4cb13-5c5d-558c-a8d4-e308776ce4cf",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "Dr V Sridhar\nPrincipal Scientist\nICAR - IIHR\n27\nMs Arathi\nBusiness Developer\nUniversal Enterprises\n28\nMr B Mahesh\nManaging Director\nKarnataka Council for Technological Upgradation\n29\nMr Amit B\nManager\nUniversal Corporation\n40 Sl. No.\nName\nDesignation\nOrganization\n30\nMs Devika. S\nAccountant\nUniversal Enterprises\n31\nProf. Shakunthala Sri- dhara\nMember, Board of Manage- ment - GKVK\nUniversity of Agricultural Sciences\n32\nDr Sanjay M T\nAgronomist & Head\nUniversity of Agricultural Sciences\n33\nDr Meenakshi Sood\nAsst. Professor\nUniversity of Horticultural Sciences- Bagalkot\n34\nDr A G Sreenivas\nProfess\n\n… [+1210 more chars]",
  "content_hash": "e634c0c82d5e1a95c31c2c93bcaadf6f1fe14f3948fd394dd24dc4ddf927c7ba",
  "token_count": 508,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "parent_chunk_id": "aaedcadf-dc4e-5b10-b87a-8ca9d6950e51",
  "chunk_index": 53,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `e5332e58-0f8d-5738-b30f-0e7a48823c1b`

- vector: dim=3072 · [0.0195, -0.0190, -0.0066, -0.0218, -0.0115, -0.0071, 0.0100, 0.0303, …]

```json
{
  "chunk_id": "e5332e58-0f8d-5738-b30f-0e7a48823c1b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "List of Participants",
  "chunk_text": "University of Horticultural Sciences- Bagalkot\n49\nDr Manjunath G\nScientist\nUniversity of Horticultural Sciences- Bagalkot\n50\nMr D G Revappa\nSupervisor\nBruhat Bengaluru Mahanagara Palike(BBMP)\n51\nDr Shivanna Professor & Head\nUniversity of Horticultural Sciences- Bagalkot\n52\nDr Raghunatha Reddy\nAsst. Professor\nUniversity of Horticultural Sciences- Bagalkot\n53\nMr Jayakumar H\nDirector\nTanindo Seed Pvt.Ltd\n54\nMr M Shekar\nChief Executive Officer\nTanindo Seed Pvt.Ltd\n55\nDr Archana Thulaseed- haran\nAsst. Professor\nIndian Council of Plantation\n56\nMr R Mohan Kumar\nDirector\nVokkal Seeds Pvt.Ltd\n57\nMr Jay\n\n… [+189 more chars]",
  "content_hash": "03b59c64c62f030542271b767eb7294f0b507009faeb3f50f1cb516428301f65",
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
  "parent_chunk_id": "aaedcadf-dc4e-5b10-b87a-8ca9d6950e51",
  "chunk_index": 54,
  "page_number": 41,
  "page_range": [
    41,
    43
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```

## Child · `4a242553-63a2-547d-8b8b-8552fa881a2b`

- vector: dim=3072 · [-0.0195, 0.0161, -0.0179, -0.0280, -0.0009, -0.0145, 0.0306, -0.0118, …]

```json
{
  "chunk_id": "4a242553-63a2-547d-8b8b-8552fa881a2b",
  "document_id": "bengaluru_conference_report_2020_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Bengaluru-Conference-Report_2020.pdf",
  "section_heading": "About TERI",
  "chunk_text": "The Energy and Resources Institute (TERI) is an independent, non-profit organization, with capabilities in research, policy, consultancy and implementation. TERI has multi-disciplinary expertise in the areas of energy, environment, climate change, resources, and sustainability. With the vision of creating innovative solutions for a sustainable future, TERI's mission is to usher in transitions to a cleaner and more sustainable future through the conservation and efficient use of the Earth's resources and develop innovative ways of minimizing waste and reusing resources. TERI's work across secto\n\n… [+984 more chars]",
  "content_hash": "8180528f377bdd9ff4ff4886a1c744229d97f9d7c8ee4585c002ccbe36def13e",
  "token_count": 330,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "bengaluru_conference_report_2020_pdf",
  "pdf_path": "Bengaluru-Conference-Report_2020.pdf",
  "chunk_index": 55,
  "page_number": 44,
  "page_range": [
    44,
    44
  ],
  "created_at": "2026-06-30T08:32:48.347957+00:00",
  "updated_at": "2026-06-30T08:32:48.347957+00:00"
}
```
