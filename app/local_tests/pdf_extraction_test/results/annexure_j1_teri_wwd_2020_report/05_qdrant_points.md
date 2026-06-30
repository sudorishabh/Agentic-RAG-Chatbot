# Qdrant points — Annexure_J1_ TERI_WWD-2020_Report.pdf

- points (rows upserted): **44**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `7373d515-796a-507c-a29e-b88e125a414f`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "7373d515-796a-507c-a29e-b88e125a414f",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message — Shri Annasaheb Misal",
  "chunk_text": "Special Message — Shri Annasaheb Misal\n\nReport\n\non\nSave Wetlands from \nPlastic Litter\nA celebration of \nWorld Wetlands Day- February 2, 2020\nLocation : Veer Savarkar Udyan, Sagar Vihar; Vashi, \nNavi Mumbai\n\nCommissioner, Navi Mumbai Municipal Corporation \n(NMMC) \nNavi Mumbai Municipal Corporation (NMMC), one of the most progressive ULB’s in India has always focused on the\nenvironmental conservation and sustainable development of the city. The measures taken by NMMC have led to Navi Mumbai\nbeing ranked 7th in India under Swachha Bharat Abhiyan (SBA) in 2019. Additionally, Navi Mumbai has been b\n\n… [+2353 more chars]",
  "content_hash": "e0e8868853c5727a2a8c5ef99ca302e58835cf151dcc3cedab8bd7f1e8de7fc3",
  "token_count": 623,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    1,
    2
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `5eb2fc1f-dd6d-5e72-acce-3159065b25fd`

- vector: dim=3072 · [-0.0347, -0.0139, -0.0039, -0.0435, 0.0167, -0.0135, -0.0014, 0.0291, …]

```json
{
  "chunk_id": "5eb2fc1f-dd6d-5e72-acce-3159065b25fd",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message — Shri Annasaheb Misal",
  "chunk_text": "Report\n\non\nSave Wetlands from \nPlastic Litter\nA celebration of \nWorld Wetlands Day- February 2, 2020\nLocation : Veer Savarkar Udyan, Sagar Vihar; Vashi, \nNavi Mumbai\n\nCommissioner, Navi Mumbai Municipal Corporation \n(NMMC) \nNavi Mumbai Municipal Corporation (NMMC), one of the most progressive ULB’s in India has always focused on the\nenvironmental conservation and sustainable development of the city. The measures taken by NMMC have led to Navi Mumbai\nbeing ranked 7th in India under Swachha Bharat Abhiyan (SBA) in 2019. Additionally, Navi Mumbai has been bestowed with\nrich natural vegetation, ma\n\n… [+1637 more chars]",
  "content_hash": "693f114eab46dbd39b9c505ab530ed8d92cf80805936412c36a1e9e5e0d54b0a",
  "token_count": 479,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "7373d515-796a-507c-a29e-b88e125a414f",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    2
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `b18d4d7c-2053-5e8d-adf4-e1777a6d55bf`

- vector: dim=3072 · [-0.0401, -0.0031, -0.0122, -0.0202, 0.0128, -0.0171, -0.0050, 0.0252, …]

```json
{
  "chunk_id": "b18d4d7c-2053-5e8d-adf4-e1777a6d55bf",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message — Shri Annasaheb Misal",
  "chunk_text": "I feel motivated to see\nrepresentatives from Helen Keller Institute of Deaf and Deaf blind taking active part in the program. Furthermore, I truly\nappreciate the organizations and citizens who have raised the saplings in waste plastic bottles and those who have agreed to nurture it further for afforestation. As part of the Eco-city Project, a joint collaboration with TERI, NMMC would be pleased to\nwork towards the implementation of these initiatives on a larger scale with the objective of not only creating awareness but also\na bigger long term positive impact.\nI feel optimistic that with colla\n\n… [+347 more chars]",
  "content_hash": "82df4b53a6b0d4f8396c53df086919e6d710c73cb8d2f92dfec0dafb65d2d191",
  "token_count": 183,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "7373d515-796a-507c-a29e-b88e125a414f",
  "chunk_index": 1,
  "page_number": 2,
  "page_range": [
    2,
    2
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `77345c66-fa4d-5980-afe0-aa0bb8d94907`

- vector: dim=3072 · [-0.0057, 0.0081, -0.0089, -0.0269, 0.0213, -0.0110, -0.0117, 0.0192, …]

```json
{
  "chunk_id": "77345c66-fa4d-5980-afe0-aa0bb8d94907",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "Prof. Suhas Pednekar,\nVice Chancellor, University of Mumbai \nThe University of Mumbai, one of the oldest and largest Universities in India, has 720 kilometers of coastline under\nits jurisdiction. There are more than 800 colleges affiliated to the university with 176 environment initiatives being\nundertaken in the campuses with the combined participation of over 15,000 students. The University’s National\nService Scheme (NSS) unit has always been a front runner in participating in\nenvironment, social and community\nbased programs.\nWetlands are one of the most productive ecosystems, home to rich b\n\n… [+1678 more chars]",
  "content_hash": "f2b781012bc2866f20dc91f21c0a319a922655ae2545a75d3bac2e2789b4b8eb",
  "token_count": 460,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 2,
  "page_number": 3,
  "page_range": [
    3,
    3
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `0c839165-abf0-59da-8167-57c137bfee6c`

- vector: dim=3072 · [-0.0136, -0.0098, -0.0091, -0.0465, -0.0039, 0.0064, -0.0009, 0.0069, …]

```json
{
  "chunk_id": "0c839165-abf0-59da-8167-57c137bfee6c",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "Mr. Atul Bagai\nCountry Head- India Office, United Nations Environment Programme\n(UNEP)\nThe UNEP is the leading and authoritative global voice on environmental issues. It is the key driver of the environmental\ndimension of sustainable development, within the United Nations system. UNEP’s global campaigns ‘Beat Plastic Pollution’\nand ‘Clean Seas’ are increasingly gaining traction. The India office of UNEP started operations 3 years ago. It made its mark\nwhen it organised a highly successful World Environment Day in 2018 when the Prime Minister of India, committed to\nphasing out single-use plasti\n\n… [+1589 more chars]",
  "content_hash": "fc4312c7d323571de83db472091d8df82f5d3223544a09f43f9fb5528f32fe65",
  "token_count": 437,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 3,
  "page_number": 4,
  "page_range": [
    4,
    4
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Parent · `2fb5fd01-2431-5332-a1bf-c1c116d79e2a`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "2fb5fd01-2431-5332-a1bf-c1c116d79e2a",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "Special Message\n\nDr. Ajay Mathur\nDirector General, The Energy and Resources Institute\n(TERI)\nI am glad that TERI’s Western Regional Center (WRC) has been celebrating World Wetlands Day (WWD) in Mumbai for the\npast 12 years with diverse stakeholders and in collaboration with the Ramsar Convention. The reports of all these events are\navailable on the Ramsar website (https://www.ramsar.org/). The WWD-2020 celebration on the theme ’Save Wetlands from\nPlastic Litter’ by TERI was in collaboration with United Nations Environment Programme (UNEP), Navi Mumbai Municipal\nCorporation (NMMC), and National\n\n… [+6141 more chars]",
  "content_hash": "c9af3192b9fdd1b621bce1b910299f02c2fe79cc44da69a9c57d2c881bdaf923",
  "token_count": 1736,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    5,
    7
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `0ef1cb1e-b639-524f-b14c-b85dd3cc146c`

- vector: dim=3072 · [-0.0221, -0.0270, -0.0094, -0.0435, 0.0079, 0.0141, 0.0150, 0.0110, …]

```json
{
  "chunk_id": "0ef1cb1e-b639-524f-b14c-b85dd3cc146c",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "Dr. Ajay Mathur\nDirector General, The Energy and Resources Institute\n(TERI)\nI am glad that TERI’s Western Regional Center (WRC) has been celebrating World Wetlands Day (WWD) in Mumbai for the\npast 12 years with diverse stakeholders and in collaboration with the Ramsar Convention. The reports of all these events are\navailable on the Ramsar website (https://www.ramsar.org/). The WWD-2020 celebration on the theme ’Save Wetlands from\nPlastic Litter’ by TERI was in collaboration with United Nations Environment Programme (UNEP), Navi Mumbai Municipal\nCorporation (NMMC), and National Service Scheme (\n\n… [+1303 more chars]",
  "content_hash": "178e9b5c9c332c9b65932d4c5964533bd61d12c4e30e24dd4e52b81bda9c380e",
  "token_count": 436,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "2fb5fd01-2431-5332-a1bf-c1c116d79e2a",
  "chunk_index": 4,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `beea5fcc-b641-53d3-af02-a94c545e6748`

- vector: dim=3072 · [-0.0084, -0.0177, -0.0085, -0.0391, -0.0270, -0.0341, 0.0031, 0.0461, …]

```json
{
  "chunk_id": "beea5fcc-b641-53d3-af02-a94c545e6748",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "It was heartening to note that all participants have taken a pledge against single use plastics and many of them drafted\nroadmaps against plastic pollution. These suggestions will be collated and submitted to the Hon’ble Chief Minister of Maharashtra by TERI, UNEP and other project partners; requesting him to develop a roadmap against plastic pollution in the\nstate. The participation of representatives from Helen Keller Institute for Deaf and Deaf blind was a true value addition to the\nevent. I am happy that TERI handed over 100 saplings of native trees raised in waste plastic bottles to them \n\n… [+1153 more chars]",
  "content_hash": "4f8e7b58a873963d8ad3d126db0859af14e17f5da3b953234915e2d72f422686",
  "token_count": 381,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "2fb5fd01-2431-5332-a1bf-c1c116d79e2a",
  "chunk_index": 5,
  "page_number": 5,
  "page_range": [
    5,
    6
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `370a071e-4365-505a-a86e-abe2e9d7aece`

- vector: dim=3072 · [-0.0097, -0.0166, -0.0097, -0.0215, -0.0136, -0.0329, 0.0101, 0.0433, …]

```json
{
  "chunk_id": "370a071e-4365-505a-a86e-abe2e9d7aece",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "Wetland conservation message through art\nc\nPledge Against Single use plastic and Perception survey\nd\nPlant a Sapling in waste plastic bottle\ne\nDisplay of Cloth Bags - Aapli Pishvi\n4\nMedia Coverage\n5\nTake Home Message\nAcknowledgment\nIndex | Sr No. | Content |  |\n| --- | --- | --- |\n|  | Agenda |  |\n| 1 | Inaugural and Interactive Session |  |\n|  | a | Welcome and Event Introduction |\n|  | b | Key Address by the Chief Guest |\n|  | c | Address by the Dignitaries |\n|  | d | Pledge by participants against Single Use Plastic |\n|  | e | Felicitation: Exemplary Initiatives for Environmental Betterment\n\n… [+541 more chars]",
  "content_hash": "a4d8eb38936411c5a002142c9d8ab0a6da9bff3e773bd78fe696692d0bb777c8",
  "token_count": 317,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "2fb5fd01-2431-5332-a1bf-c1c116d79e2a",
  "chunk_index": 6,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `b95e05d8-0fd8-5ce0-bbee-2e56e0aa0bba`

- vector: dim=3072 · [-0.0248, -0.0195, 0.0020, -0.0286, -0.0165, -0.0329, 0.0094, 0.0439, …]

```json
{
  "chunk_id": "b95e05d8-0fd8-5ce0-bbee-2e56e0aa0bba",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "|\n|  | d | Plant a Sapling in waste plastic bottle |\n|  | e | Display of Cloth Bags - Aapli Pishvi |\n| 4 | Media Coverage |  |\n| 5 | Take Home Message |  |\n|  | Acknowledgment |  | 9.30 AM - 10.00 AM\nRegistration\n10.00 AM - 10.30 AM\nCleanup activity in mangroves\nInaugural and Interactive Session\n10.00 AM - 10.15 AM \nArrival of guests and chief guest; Exploring the live activities (Poster making, Mural \nmaking, Rangoli and more)\n10.15 AM - 10.30 AM\nWelcome and Introduction about project and the event- TERI and UNEP\n10.30 AM - 11.00 AM\nAddress by the Guest of Honor and dignitaries\n11.00 AM - 11.\n\n… [+750 more chars]",
  "content_hash": "807b8e8f68e164921dd27dff86cafa15a1e10394b34e63062fe56e5651c7facd",
  "token_count": 399,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "2fb5fd01-2431-5332-a1bf-c1c116d79e2a",
  "chunk_index": 7,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `2ec7bfb6-46a4-54df-b6e0-0cb6b97a43a9`

- vector: dim=3072 · [-0.0229, -0.0276, -0.0057, -0.0320, -0.0067, -0.0040, 0.0117, 0.0336, …]

```json
{
  "chunk_id": "2ec7bfb6-46a4-54df-b6e0-0cb6b97a43a9",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Special Message",
  "chunk_text": "single use plastic and Perception survey\nPlant a Sapling in waste plastic bottle\n12.30 PM - 1.00 PM\nRefreshments (Healthy Food- Millet Idli and Fruit Plate)\nAgenda: World Wetlands Day 2020 Event \nFebruary 2, 2020 | 9.30 AM - 10.00 AM | Registration |\n| --- | --- |\n| 10.00 AM - 10.30 AM | Cleanup activity in mangroves |\n| Inaugural and Interactive Session |  |\n| 10.00 AM - 10.15 AM | Arrival of guests and chief guest; Exploring the live activities (Poster making, Mural making, Rangoli and more) |\n| 10.15 AM - 10.30 AM | Welcome and Introduction about project and the event- TERI and UNEP |\n| 10.\n\n… [+841 more chars]",
  "content_hash": "97c014ab691f73a60547b0c62c98aaca38eaaf10e2186f4c71ee25ed63dc9575",
  "token_count": 421,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "2fb5fd01-2431-5332-a1bf-c1c116d79e2a",
  "chunk_index": 8,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `b385aa6a-ea2a-5bd6-b4d8-63ddabcf6f9c`

- vector: dim=3072 · [-0.0211, -0.0036, -0.0202, -0.0218, -0.0338, -0.0589, -0.0079, 0.0201, …]

```json
{
  "chunk_id": "b385aa6a-ea2a-5bd6-b4d8-63ddabcf6f9c",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "MUMBAI — 1. Inaugural and Interactive Session — Dignitaries on Dais",
  "chunk_text": "(From L to R): Smt. Shaila Sam, Media and Communication Specialist, UNEP; Shri. Lovish Ahuja, Vice\nPresident, Governmental Affairs – India, TOMRA; Smt. Saloni Goel, Consultant, Plastic Pollution Programme,\nUNEP; Shri. G.S. Gill (IAS), Distinguished Advisor, TERI-WRC; Shri. Annasaheb Misal, IAS, Commissioner,\nNMMC and Shri. J.S.Saharia, (IAS), Former Chief Secretary, Government of Maharashtra (GoM)\n\na) Welcome and Event Introduction\nDr. Anjali Parasnis \nWhile explaining the concept of ‘Rethink\nPlastic\nCampaign’, Dr. Anjali Parasnis,\nAssociate Director, TERI-WRC emphasized\non\nthe\ninnovative\nappr\n\n… [+358 more chars]",
  "content_hash": "08117104de3f4193de7d13bda0214bac2a21a3c3e61e7c68470df80ca1b167ea",
  "token_count": 260,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 9,
  "page_number": 9,
  "page_range": [
    9,
    10
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Parent · `9374ce48-16d2-5878-8d50-3fa4fc0ffd97`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "9374ce48-16d2-5878-8d50-3fa4fc0ffd97",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Program Inauguration — World Wetlands Day 2020",
  "chunk_text": "Program Inauguration — World Wetlands Day 2020\n\nHon’ble Chief Guest planting the Native Sapling (left) and unveiling the collage made \nfrom Plastic waste (right)\n\nWelcoming the Dignitaries with \nNative Tree Saplings\nMr. Lovish Ahuja, Vice President, Governmental \nAffairs, India, TOMRA\nMr. J.S. Saharia, Former Chief Secretary, \nGoM\n\nShri Annasaheb Misal, I.A.S., \nHon’ble Commissioner,\nNMMC\n•\nThe Commissioner, NMMC appreciated the TERI-\nUNEP initiative to counter marine plastic pollution.\n•\nHe highlighted the need of individual efforts by all\ncitizens to make the city free from plastic pollution\n\n… [+5116 more chars]",
  "content_hash": "cd9f651829b5d5ffe34f293dbfa1484de5cba6569ab6083d85f0923061ed5abc",
  "token_count": 1555,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    11,
    20
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `5f9e0514-0a40-5579-9f9e-f011d440ecb6`

- vector: dim=3072 · [-0.0173, -0.0104, -0.0091, -0.0399, -0.0147, -0.0401, -0.0070, 0.0153, …]

```json
{
  "chunk_id": "5f9e0514-0a40-5579-9f9e-f011d440ecb6",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Program Inauguration — World Wetlands Day 2020",
  "chunk_text": "Hon’ble Chief Guest planting the Native Sapling (left) and unveiling the collage made \nfrom Plastic waste (right)\n\nWelcoming the Dignitaries with \nNative Tree Saplings\nMr. Lovish Ahuja, Vice President, Governmental \nAffairs, India, TOMRA\nMr. J.S. Saharia, Former Chief Secretary, \nGoM\n\nShri Annasaheb Misal, I.A.S., \nHon’ble Commissioner,\nNMMC\n•\nThe Commissioner, NMMC appreciated the TERI-\nUNEP initiative to counter marine plastic pollution.\n•\nHe highlighted the need of individual efforts by all\ncitizens to make the city free from plastic pollution.\n•\nHe urged the youth to actively take action t\n\n… [+669 more chars]",
  "content_hash": "e83d26ff2a465443b2956d5a78e12256619012e8de3a61a5fd157d86d835192a",
  "token_count": 323,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "9374ce48-16d2-5878-8d50-3fa4fc0ffd97",
  "chunk_index": 10,
  "page_number": 11,
  "page_range": [
    11,
    13
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `2a9d24a0-6faf-5a80-b6b5-6136a3eef0bd`

- vector: dim=3072 · [-0.0212, 0.0034, -0.0158, -0.0289, -0.0013, -0.0380, -0.0013, 0.0198, …]

```json
{
  "chunk_id": "2a9d24a0-6faf-5a80-b6b5-6136a3eef0bd",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Program Inauguration — World Wetlands Day 2020",
  "chunk_text": "NMMC’s initiatives against single use\nplastic, he told that the NMMC head office is single\nuse plastic free; and the corporation shall continue\nto work towards managing plastic pollution in the\ncity through concrete policies and action against the\nsame.\nb) Key Address by the Chief Guest c) Address by the Dignitaries\nShri. J. S. Saharia (IAS),  \nFormer Chief Secretary, \nGoM\n•\nShri. J. S. Saharia (Guest of Honor) appreciated TERI and UNEP’s\nefforts\ntowards\ncreating\nawareness\nand\nsensitization\namong\nthe\ncitizens through action oriented programmes being conducted under\nthe ‘Rethink Plastic campaig\n\n… [+600 more chars]",
  "content_hash": "f090dc7e8ebe39731b3edbbb32b209ced03c937bd866ba5c4911d76e0708b0f7",
  "token_count": 318,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "9374ce48-16d2-5878-8d50-3fa4fc0ffd97",
  "chunk_index": 11,
  "page_number": 14,
  "page_range": [
    14,
    14
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `f11c581f-7935-51e6-99fd-de600cb5fc3e`

- vector: dim=3072 · [-0.0205, -0.0154, -0.0131, -0.0396, -0.0265, -0.0371, -0.0137, 0.0099, …]

```json
{
  "chunk_id": "f11c581f-7935-51e6-99fd-de600cb5fc3e",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Program Inauguration — World Wetlands Day 2020",
  "chunk_text": "Shri. G.S.Gill (IAS)\nDistinguished Advisor, \nTERI-WRC c) Address by the Dignitaries\nSmt. Saloni Goel\nConsultant, Plastic \nPollution, UNEP\n•\nSmt. Saloni Goel, gave insightful details about the UNEP project ‘Promotion of\ncountermeasures against marine plastic litter in Southeast Asia and India’ being\nimplemented in 4 Indian cities namely Agra, Prayagraj (Allahabad), Rishikesh and\nMumbai to tackle plastic pollution.\n•\nShe also highlighted that lack of knowledge and awareness about the intricacies\nof plastic like different types of plastic is a key concern in managing plastic\npollution.\nSmt.  Divy\n\n… [+795 more chars]",
  "content_hash": "f298d391e8c37171d5cf51a31e1a9d7c811ae18c4703942553d33ef3954218fb",
  "token_count": 337,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "9374ce48-16d2-5878-8d50-3fa4fc0ffd97",
  "chunk_index": 12,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `91d8fe80-205b-580b-8761-b25b3dfdba0b`

- vector: dim=3072 · [-0.0266, -0.0257, -0.0108, -0.0238, -0.0163, -0.0356, 0.0091, 0.0092, …]

```json
{
  "chunk_id": "91d8fe80-205b-580b-8761-b25b3dfdba0b",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Program Inauguration — World Wetlands Day 2020",
  "chunk_text": "is\nsegregation at source while technological and end of pipe solutions can mitigate\nonly ~30% of the waste problem.\n•\nHe also mentioned about the importance of life cycle analysis of each and every\nproduct we consume, specially with respect to the amount of waste generated by\nthose products. Pledge by the participants\nPledge by the Dignitaries\nd) More than 300 participants \ntook Pledge against Single Use \nPlastic\nAs a good citizen of my country and a responsible\nresident of the planet Earth, I pledge to Refuse,\nReduce, Recycle, Reuse, Repair, Re-gift, Recover\nand “Rethink plastic”, to the best\n\n… [+980 more chars]",
  "content_hash": "d141d32176486d01629e3e2fa02290b3cb71f8a8a2ac77dc81ec8aea3a8ae824",
  "token_count": 443,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "9374ce48-16d2-5878-8d50-3fa4fc0ffd97",
  "chunk_index": 13,
  "page_number": 16,
  "page_range": [
    16,
    17
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `601a4863-a004-5055-ba23-472d16d2ec4d`

- vector: dim=3072 · [-0.0195, -0.0004, -0.0048, -0.0200, -0.0225, -0.0251, 0.0078, -0.0008, …]

```json
{
  "chunk_id": "601a4863-a004-5055-ba23-472d16d2ec4d",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Program Inauguration — World Wetlands Day 2020",
  "chunk_text": "She\naims\nto\nmake\nat\nleast\none\nMunicipal Market in her locality,\nfree from plastic bags. 2. Shri. P. S Lokhande\nHe started PSL Waste Management LLP to\ncollect,\nsegregate\nand\neffectively\nmanage\nmunicipal waste.\n3. Smt. Jyoti Nadkarni\nShe\ncollectively\nworks\nwith\nhousing\nsocieties in Kharghar, Navi Mumbai to\nhelp collect and segregate household waste\nat source.\n\n4. Shri. Prakash Chandra Joshi\nIndividually\ncollected more than 1500\nwaste plastic bottles for the campaign\n5. Smt. Kalpana Chhatre\nA member of Mangrove Marshal Group,\nNavi Mumbai. The group organizes weekly\nmangrove cleanup activity at Sa\n\n… [+339 more chars]",
  "content_hash": "903b13f398fafc3d583d8eb660858baf8d92ca9b80d0c0c35fb5d189a96888c3",
  "token_count": 286,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "9374ce48-16d2-5878-8d50-3fa4fc0ffd97",
  "chunk_index": 14,
  "page_number": 18,
  "page_range": [
    18,
    20
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `8fc87a5b-d9de-57c6-8e1e-e3e900a703d4`

- vector: dim=3072 · [-0.0662, -0.0199, -0.0129, -0.0142, -0.0172, -0.0394, -0.0154, 0.0202, …]

```json
{
  "chunk_id": "8fc87a5b-d9de-57c6-8e1e-e3e900a703d4",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "part",
  "chunk_text": "of\nthe\nTERI-UNEP\n‘Rethink Plastic’ Campaign, at the hands of\nDr.\nAnita\nJadhav,\nAssociate\nProfessor,\nICLES\nMotilal\nJhunjhunwala\nCollege,\nVashi\n•\nTERI also committed to prepare a Braille\nbook and Touch and Feel kits for these\nspecial students to introduce them to\nPlastic and its impacts on health and\nenvironment.\n•\nA draft of the Braille book was handed\nover to representatives of Helen Keller\nInstitute of Deaf and Deaf blind by the\nHon’ble commissioner, NMMC.\n\ng) Panel discussion : Youth Vision on \nPlastic Pollution\nA 6 membered panel including 3 experts and 3 young volunteers led a very \nintera\n\n… [+920 more chars]",
  "content_hash": "bcfac5a6f86e98ac8b083890ec7af8cd8219e8404f92ed86b555eed5a0046a02",
  "token_count": 358,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 15,
  "page_number": 20,
  "page_range": [
    20,
    23
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `217ee824-f52c-55db-bdb1-657106ee2aa2`

- vector: dim=3072 · [-0.0039, 0.0064, 0.0045, -0.0283, 0.0142, -0.0388, -0.0069, 0.0111, …]

```json
{
  "chunk_id": "217ee824-f52c-55db-bdb1-657106ee2aa2",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "2. Mangrove Cleanup Activity- Sagar Vihar",
  "chunk_text": "•\nMangroves\nact\nas\nbuffer\nagainst\nextreme\nweather\nevents\nsuch\nas\nhurricanes, coastal floods.\n•\nThey\nstabilize\ncoastline\nand\nslows\ndown soil erosion rate\n•\nAct as source of livelihood for local\ncommunities – fishing, collection of\nhoney, tannins and wax\n•\nAct as a Carbon Sink\n•\nMangrove roots are a complex system\nthat\naccumulate\norganic\nand\ninorganic nutrients and thus, act as a\nbreeding\nground\nand\nnursery\nfor\nvarious\nmarine\norganisms.\nHowever, plastic litter in mangroves is\na cause of concern as it gets trapped\nin the mangroves.\n•\nThe cleanup activity was carried out\nin\norder\nto\ncollect\nplasti\n\n… [+693 more chars]",
  "content_hash": "0d0abcfcf33fc966b01f6c81c4cba1dd41e638b9356ea28c4760161600c4513a",
  "token_count": 372,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 16,
  "page_number": 25,
  "page_range": [
    25,
    29
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `d22f7d17-9059-5cb4-b6e3-e6aac8bfbbd0`

- vector: dim=3072 · [-0.0450, -0.0405, -0.0127, -0.0026, 0.0064, -0.0140, 0.0034, -0.0189, …]

```json
{
  "chunk_id": "d22f7d17-9059-5cb4-b6e3-e6aac8bfbbd0",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Volunteers",
  "chunk_text": "making\ncollage\nusing waste bottle caps\n• Waste plastic needs to be properly\nchannelized to prevent it from ending\nup\nin\nthe\nterrestrial\nand\nmarine\necosystems.\n• Caps\nof\nwaste\nplastic\nbottles\nwere\nused to convey an important message.\n• Plastic can be reused.\n• Single used caps to be recycled and\nchannelized\nfor\nresponsible\ndisposal.\n• SAVE OCEANS from single use\nplastic.\na) Collage from Waste Bottle Caps\nRationale\n\nVolunteers used bottle caps to create the display of the\nmessage ‘Save Oceans’. These caps were pasted on Duck\nshaped cardboard cut outs to depict the plight of aquatic\nanimals and b\n\n… [+226 more chars]",
  "content_hash": "fc954138e2d700932847aa4a0985a77b95d5c6fd6d7a5c69368e57bec23e2825",
  "token_count": 222,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 17,
  "page_number": 30,
  "page_range": [
    30,
    33
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Parent · `d3d3c510-dbdc-5237-bbc6-d56a08a941bf`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "d3d3c510-dbdc-5237-bbc6-d56a08a941bf",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "2. Awareness — through Posters",
  "chunk_text": "2. Awareness — through Posters\n\nA vibrant array of posters was\nmade by the volunteers. Each\nposter artistically conveyed the\nimportance\nof\nwetlands\nand\nthe need to save them from\nplastic pollution.\n\nc) Pledge and Perception survey\nPerception Survey- Rationale\n•\nPerception\nof\nindividuals\nis\nvery\nimportant\nto\nunderstand the behavior, practices and awareness of\nthe citizens as well as to carve out a way forward.\n•\nThe perception survey on ‘Plastic Use and Management’\nwas designed to assess the opinions of individuals\nregarding plastic use, management of plastic waste\nand\nawareness\nabout\nalternati\n\n… [+1766 more chars]",
  "content_hash": "a22ab4b4d5a993a4730705013278efbbfcd95c177d82c2dcdbed293f1086816b",
  "token_count": 556,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    34,
    37
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `2fbf871c-8295-560f-9595-92c5bf63aed2`

- vector: dim=3072 · [-0.0141, -0.0200, -0.0155, -0.0352, 0.0110, -0.0152, 0.0170, 0.0242, …]

```json
{
  "chunk_id": "2fbf871c-8295-560f-9595-92c5bf63aed2",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "2. Awareness — through Posters",
  "chunk_text": "A vibrant array of posters was\nmade by the volunteers. Each\nposter artistically conveyed the\nimportance\nof\nwetlands\nand\nthe need to save them from\nplastic pollution.\n\nc) Pledge and Perception survey\nPerception Survey- Rationale\n•\nPerception\nof\nindividuals\nis\nvery\nimportant\nto\nunderstand the behavior, practices and awareness of\nthe citizens as well as to carve out a way forward.\n•\nThe perception survey on ‘Plastic Use and Management’\nwas designed to assess the opinions of individuals\nregarding plastic use, management of plastic waste\nand\nawareness\nabout\nalternatives\nto\nplastic\nand\nimpacts\nof\npl\n\n… [+1108 more chars]",
  "content_hash": "4bde7da828ce388ec4d0a6cca1e97e380023ff40553c890be8512b1c20d557b9",
  "token_count": 398,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "d3d3c510-dbdc-5237-bbc6-d56a08a941bf",
  "chunk_index": 18,
  "page_number": 34,
  "page_range": [
    34,
    36
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `dd9c9412-355b-5490-9e68-3f1dfe848daf`

- vector: dim=3072 · [-0.0170, 0.0018, -0.0118, -0.0263, -0.0352, -0.0212, 0.0104, 0.0079, …]

```json
{
  "chunk_id": "dd9c9412-355b-5490-9e68-3f1dfe848daf",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "2. Awareness — through Posters",
  "chunk_text": "More than 300 \nindividuals took the \nPledge against \nSingle Use Plastics \nand filled in the \nPerception survey\nQR Code of the \n‘Rethink Plastic’ App \nto register \ncontribution of \nsaplings and waste \nplastic bottles d) Plant a Sapling in Waste Plastic \nBottle- Rationale\n• Native trees saplings raised in\nwaste\nplastic\nbottles\nwhen\nused for afforestation will help\noffset carbon footprint towards\nproduction of these bottles.\n• This would also demonstrate a\nresponsible reuse and disposal\nof waste plastic bottles.\nSapling of Indian Almond \nTree (Terminalia catappa)\nAround 630\nmature trees are \nrequ\n\n… [+240 more chars]",
  "content_hash": "1938b41fbb615ba2c55554de1385e52d5d1589731fb758c79b1176d1d47526f2",
  "token_count": 205,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "d3d3c510-dbdc-5237-bbc6-d56a08a941bf",
  "chunk_index": 19,
  "page_number": 37,
  "page_range": [
    37,
    37
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `bf276f72-1289-51f3-8c73-7af1e19be5bb`

- vector: dim=3072 · [-0.0032, 0.0320, -0.0085, 0.0053, -0.0441, 0.0087, -0.0304, -0.0386, …]

```json
{
  "chunk_id": "bf276f72-1289-51f3-8c73-7af1e19be5bb",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "Banyan (Ficus",
  "chunk_text": "benghalensis) (Vad, Bargad)\n• Medicinal\nproperties:\nleaf,\nbark,\nseeds\nand\nfig\ncure\ndisorders\nlike\ndiarrhea,\npolyuria,\ndental,\ndiabetes\nand urine disorders\n• Wood\n:\nmaking\ndoor\npanels, boxes\n• Bark : making paper and\nropes\n• Figs: edible\n• Habitat for numerous bird\nspecies\nSacred Fig (Ficus religiosa)\n(Peepal, Pimpal)\n• Host for Lac Insects\n• Fodder for goats and cattle\n• Figs: edible\n• Bark: extraction of reddish\ndye;\ncure\ninflammations\nand glandular swelling\n• Medicinal uses:\nbeneficial\nfor eczema, asthma, blood\npurification,\ndigestive\nailments\nNeem (Azadirachta indica)\n• Medicinal uses: effe\n\n… [+332 more chars]",
  "content_hash": "5afb3ae228e56cef9e310f8430461048beaaeace0847bc33c6fda04a46f9d01b",
  "token_count": 295,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 20,
  "page_number": 38,
  "page_range": [
    38,
    38
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `87136855-c6ee-59c6-9998-ca5c35c1a372`

- vector: dim=3072 · [-0.0354, -0.0019, -0.0095, -0.0135, -0.0254, -0.0238, 0.0148, 0.0051, …]

```json
{
  "chunk_id": "87136855-c6ee-59c6-9998-ca5c35c1a372",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "30 volunteers participated in this activity",
  "chunk_text": "Volunteers planting saplings of native tree species (collected \nfrom roadsides/ cracks of walls and buildings) in waste plastic \nbottles prepared as planters.\n\ne) Display of Cloth Bags - Aapli Pishvi\nA display of cloth carry bags made\nusing old clothes was set up by the\nrepresentatives\nof\nAapli\nPishvi\ninitiative\nThey gave away the cloth bags free of\ncost to the participants in order to\npromote the use of cloth carry bags\nand reducing plastic carry bags",
  "content_hash": "a19cd749f0c719a5d690cec05c6d8b8d7f8c1a0272999adc50912d74bcc9275b",
  "token_count": 113,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "chunk_index": 21,
  "page_number": 39,
  "page_range": [
    39,
    40
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Parent · `79ba3ccd-2304-53b3-b4cf-0640731bd262`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "79ba3ccd-2304-53b3-b4cf-0640731bd262",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "4. Media Coverage — Media Coverage\n\nClean-up drives carried out on World Wetland Day\nNavi Mumbai: The civic bo- dy, in association with The Energy and Resources Insti- tute (TERI) and United Na- tions Environment Program- me (UNEP), conducted a number of clean-up activiti- es along the vast wetland and mangrove fringe of Thane creek line in Sagar Vihar, Vashi. This was done on the ocassion of World Wetland Day, which was observed on Sunday. Hundreds of volun- teers joined hands to high- light the need and importan- ce of protecting wetlands and mangroves. TERI and UNEP have jointly begun a cam\n\n… [+1612 more chars]",
  "content_hash": "4ed04514b01182f6c6742f5a250d7dc863795fc71332acb6273409aab0618038",
  "token_count": 1719,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `de0355ef-6637-5f91-8f4c-279bce7bbd82`

- vector: dim=3072 · [-0.0475, -0.0350, -0.0052, -0.0031, 0.0141, 0.0005, -0.0259, 0.0078, …]

```json
{
  "chunk_id": "de0355ef-6637-5f91-8f4c-279bce7bbd82",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "Clean-up drives carried out on World Wetland Day\nNavi Mumbai: The civic bo- dy, in association with The Energy and Resources Insti- tute (TERI) and United Na- tions Environment Program- me (UNEP), conducted a number of clean-up activiti- es along the vast wetland and mangrove fringe of Thane creek line in Sagar Vihar, Vashi. This was done on the ocassion of World Wetland Day, which was observed on Sunday. Hundreds of volun- teers joined hands to high- light the need and importan- ce of protecting wetlands and mangroves. TERI and UNEP have jointly begun a campa- ign called 'Rethink Plastic' whi\n\n… [+126 more chars]",
  "content_hash": "dc3759c853b8b93823b6a6121531582fbba97036c3158cc6744ec83499364102",
  "token_count": 220,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "79ba3ccd-2304-53b3-b4cf-0640731bd262",
  "chunk_index": 22,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `19a7120f-b198-576a-94b6-d5481d9a01ef`

- vector: dim=3072 · [-0.0289, -0.0353, 0.0005, -0.0028, 0.0060, -0.0119, -0.0208, 0.0390, …]

```json
{
  "chunk_id": "19a7120f-b198-576a-94b6-d5481d9a01ef",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "9 and will go up to March 2020. - BB Nayak\nTimes of India_03.02.2020\nपाणथळ जागा वाचविण्यासाठी उपक्रम मुंबई : खारफुटी पूरनियंत्रणाचे काम करते. तसेच कार्बन कपात करत सागरी किनाऱ्याची धूप कमी करण्यातही खारफुटी महत्त्वाची भूमिका बजावते. पर्यावरण संतुलनासाठी महत्त्वाची असून यातून जैवविविधता आणि उपजीविका जपली जाते. खारफुटीच्या जंगलात अडकलेला प्लास्टिक कचरा स्वच्छ करणे महत्वाचे आहे. त्यामुळे ‘रिथिंक प्लास्टिक सारख्या उपक्रमावर भर देण्यात यावा, असे टेरीच्या सहसंचालिका डॉ. अंजली पारसनीस यांनी सांगितले",
  "content_hash": "1a8c6f1c33031defe82fddcd9fe4f2a7b520a59b8359dfc63af83951492a2ec8",
  "token_count": 463,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "79ba3ccd-2304-53b3-b4cf-0640731bd262",
  "chunk_index": 23,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `1213a5fd-e0cd-55f6-84d1-542c1144319d`

- vector: dim=3072 · [-0.0246, -0.0342, -0.0151, -0.0095, 0.0135, -0.0410, -0.0221, -0.0036, …]

```json
{
  "chunk_id": "1213a5fd-e0cd-55f6-84d1-542c1144319d",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": ", असे टेरीच्या सहसंचालिका डॉ. अंजली पारसनीस यांनी सांगितले सागरी कचऱ्यापासून पाणथळ जागांच्या बचावासाठी स्वच्छता मोहिमेचे आयोजन द एनर्जी अँड रिसोर्सेस इन्स्टिट्यूट (टेरी) आणि द युनायटेड नेशन्स एन्व्हायर्नमेंट प्रोग्रॅम (यूएनईपी) यांनी नवी मुंबई महानगरपालिका (एनएमएमसी), नॅशनल सर्व्हिस स्कीम (राष्ट्रीय सेवा योजना एनएसएस) आणि संघटनांच्या मदतीने या मोहिमेचे आयोजन केले होते. त्यावेळी पारसनीस बोलत होत्या",
  "content_hash": "96e62e979399ed4f0769aae1d5929d7a35d873c025beeaaba3b606eb86690300",
  "token_count": 420,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "79ba3ccd-2304-53b3-b4cf-0640731bd262",
  "chunk_index": 24,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `6e969308-7836-52a7-99e3-1f8a0b6075f8`

- vector: dim=3072 · [0.0018, -0.0494, -0.0147, -0.0024, 0.0060, 0.0004, -0.0408, -0.0008, …]

```json
{
  "chunk_id": "6e969308-7836-52a7-99e3-1f8a0b6075f8",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "�तीने या मोहिमेचे आयोजन केले होते. त्यावेळी पारसनीस बोलत होत्या या स्वच्छता मोहिमेचे उद्घाटन करताना नवी मुंबई पालिकेचे आयुक्त अण्णासाहेब मिसाळ म्हणाले, राज्यात नवी मुंबई पहिल्या क्रमांकाचे आणि देशातील सातव्या क्रमांकाचे स्वच्छ शहर ठरले होते. विविध उपाययोजनांमुळे आमचे एनएमएमसी मुख्यालय सिंगल यूज प्लास्टिक मुक्त इमारत असून प्लास्टिक प्रदूषणाचा यशस्वी मुकाबला करण्यासाठी वर्तणूक आणि विचारांमध्ये बदल करणे अत्यंत महत्वाचे आहे. टेरी आणि यूएनईपीने हाती घेतलेल्या या उपक्रमाचे कौतुक आयुक्तांनी केले",
  "content_hash": "f995d058ada6e10cc3639940bc26b2db0e7a57df09a3e2279fae6b45bebc7b0a",
  "token_count": 503,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "79ba3ccd-2304-53b3-b4cf-0640731bd262",
  "chunk_index": 25,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `70e585a1-3f97-5204-98fc-66debd85c795`

- vector: dim=3072 · [-0.0112, -0.0448, -0.0146, 0.0037, -0.0039, 0.0156, -0.0465, 0.0088, …]

```json
{
  "chunk_id": "70e585a1-3f97-5204-98fc-66debd85c795",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "�ूएनईपीने हाती घेतलेल्या या उपक्रमाचे कौतुक आयुक्तांनी केले त्याचप्रमाणे टेरीच्या चमूने प्लास्टिक कचऱ्यापासून बनवलेल्या कोलाजचे अनावरणही करण्यात आले.\n\nTarun Bharat_04.02.2020\nप्लास्टिक न वापरण्याची शपथ\nनवी मुंबई : 'प्लास्टिक़ वापरणार नाही, प्रदूषण होईल असे कृत्य करणार नाही' अशी शपथ रविवारी जागतिक पानथळ दिनाचे औचित्य साधून महाविद्यालयीन व",
  "content_hash": "dec856aa9cbbfdc7ff7c5c6d557091783faa25cb87d45199c3dd4e1f790a89c1",
  "token_count": 341,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "79ba3ccd-2304-53b3-b4cf-0640731bd262",
  "chunk_index": 26,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Parent · `5079c069-045b-5499-9807-346ca0d9cd64`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "5079c069-045b-5499-9807-346ca0d9cd64",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "4. Media Coverage — Media Coverage (cont.)\n\nद्यार्थ्यांना देण्यात आली.\nसांगरी कचऱ्यापासून पाणथळ जागांच्या बचावासाठी 'टेरी' आणि 'यूएनईपी' या संस्थेतर्फे जनजागृती कार्यक्रमाचे आयोजन करण्यात आले होते. या वेळी पालिका आयुक्त अण्णासाहेब मिसाळ प्रमुख पाहुणे म्हणून उपस्थित होते. 'प्लास्टिकबाबत पुनर्विचार करा' असे घोषवाक्य घेत रविवारी वाशी येथील सागर विहार येथे जनजागृती कार्यक्रमाचे आयोजन करण्यात आले होते. या वेळी मोठ्या संख्येने महाविद्यालयीन विद्यार्थी उपस्थित होते. पालिका आयुक्त अण्णासाहेब मिसाळ यांनी, प्रत्यकाने स्वतः प्लास्टिक वापर टाळणे आवश्यक असून वर्तणूक आणि विचारांमध्ये बदल अत्यंत महत्त्वाचे आ\n\n… [+1460 more chars]",
  "content_hash": "aab1cf9c7ad79fcfb0b83c1458e90bf9dff53c4983a6c013e872f717d605972b",
  "token_count": 1932,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `405e67b6-4f83-5f71-80bd-204a61c31afd`

- vector: dim=3072 · [-0.0181, -0.0266, -0.0089, 0.0002, 0.0094, -0.0067, -0.0254, 0.0094, …]

```json
{
  "chunk_id": "405e67b6-4f83-5f71-80bd-204a61c31afd",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "द्यार्थ्यांना देण्यात आली.\n\nसांगरी कचऱ्यापासून पाणथळ जागांच्या बचावासाठी 'टेरी' आणि 'यूएनईपी' या संस्थेतर्फे जनजागृती कार्यक्रमाचे आयोजन करण्यात आले होते. या वेळी पालिका आयुक्त अण्णासाहेब मिसाळ प्रमुख पाहुणे म्हणून उपस्थित होते. 'प्लास्टिकबाबत पुनर्विचार करा' असे घोषवाक्य घेत रविवारी वाशी येथील सागर विहार येथे जनजागृती कार्यक्रमाचे आयोजन करण्यात आले होते. या वेळी मोठ्या संख्येने महाविद्यालयीन विद्यार्थी उपस्थित होते",
  "content_hash": "417022e497eae1e9d1836200b79360bcf1e7013a25df2d7cf5241c353637956d",
  "token_count": 427,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "5079c069-045b-5499-9807-346ca0d9cd64",
  "chunk_index": 27,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `b5510915-191f-5be6-a596-12ebc33b8d6a`

- vector: dim=3072 · [0.0392, -0.0436, -0.0080, -0.0148, -0.0138, 0.0134, -0.0445, 0.0111, …]

```json
{
  "chunk_id": "b5510915-191f-5be6-a596-12ebc33b8d6a",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "�ा वेळी मोठ्या संख्येने महाविद्यालयीन विद्यार्थी उपस्थित होते पालिका आयुक्त अण्णासाहेब मिसाळ यांनी, प्रत्यकाने स्वतः प्लास्टिक वापर टाळणे आवश्यक असून वर्तणूक आणि विचारांमध्ये बदल अत्यंत महत्त्वाचे आहे असे सांगितले. या मोहिमेत सहभागी स्वयंसेवकांनी खारफुटीच्या जंगलात अडकलेला तब्बल १०० किलोग्रॅम प्लास्टिक कचरा गोळा केला.",
  "content_hash": "57d859a2e7bbe9ba6a4ef16572aa5c223d38a51701f0d39a2db5e84f29a31bbb",
  "token_count": 330,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "5079c069-045b-5499-9807-346ca0d9cd64",
  "chunk_index": 28,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `4788ec76-c770-5319-a354-ab1a58f3cb35`

- vector: dim=3072 · [-0.0150, -0.0441, -0.0087, -0.0042, -0.0055, -0.0109, -0.0403, 0.0238, …]

```json
{
  "chunk_id": "4788ec76-c770-5319-a354-ab1a58f3cb35",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "ात अडकलेला तब्बल १०० किलोग्रॅम प्लास्टिक कचरा गोळा केला. Loksatta_05.02.2020\nMedia Coverage\nMEN\nPromotion of Counter\npainst Marine Plastic\nLitter in Soc\nand India\nRETHI\nSTIC\n. 2020\nV\nटेरी, युनाइटेड नेशन्स एन्व्हायरमेन्ट आणि नवी मुंबई पालिकेच्या संयुक्त विद्यमाने वाशी येथे जागतिक पाणथळ दिवसाचे औचित्य साधून जनजागृती कार्यक्रम झाला. 'प्लास्टिकविषयी पुनर्विचार' संकल्पने- अंतर्गत प्लास्टिकपासून तयार केलेल्या कोलाज चित्राचे अनावरण आयुक्त अण्णासाहेब मिसाळ यांनी केले.\nMaharashtra Times_04.02.2020\nNavrashtra_05.02.2020\nजागतिक पाणथळ दिनानिमित्त विविध जनजागृतीपर उपक्रम संपन्न",
  "content_hash": "454b3703d78b5ba5f0eb52ab6590ad018042aa812809a5fa0135280c5a84510d",
  "token_count": 474,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "5079c069-045b-5499-9807-346ca0d9cd64",
  "chunk_index": 29,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `b8c6de0e-7d18-5a0b-b387-ef34b719b020`

- vector: dim=3072 · [0.0032, -0.0320, -0.0108, 0.0042, 0.0038, -0.0236, -0.0582, 0.0075, …]

```json
{
  "chunk_id": "b8c6de0e-7d18-5a0b-b387-ef34b719b020",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "2020\nजागतिक पाणथळ दिनानिमित्त विविध जनजागृतीपर उपक्रम संपन्न नवी मुंबई - नवी मुंबई हे राज्यातील पहिल्या मुख्यालय सिंगल यूज प्लास्टिक फ्री करण्यात आले क्रमांकाचे व देशातील सातव्या क्रमांकाचे स्वच्छ शहर आहे. प्लास्टिक प्रतिबंधाच्या दृष्टीने टेरी आणि यू. म्हणून मागील वर्षी नावाजले गेले असून, यावर्षी देशात एन.ई.पी. यांनी घेतलेला पुढाकार प्रशंसनीय असून, प्रथम क्रमांकाच्या मानांकनासाठी सज्ज आहे. स्वच्छ, शहरातील नागरिक व त्यातही विशेषत्वाने तरुणाईने सुंदर व प्लास्टिकमुक्त शहर निर्मितीकरिता नवी मुंबई",
  "content_hash": "c263eda5ba91811f5e3392904a32012f961357772cffda356c602b594c9e00a0",
  "token_count": 498,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "5079c069-045b-5499-9807-346ca0d9cd64",
  "chunk_index": 30,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `d1e8ab19-2ef6-56fd-916a-4a1c451a0802`

- vector: dim=3072 · [0.0097, -0.0561, -0.0044, -0.0220, -0.0076, -0.0312, -0.0562, 0.0237, …]

```json
{
  "chunk_id": "d1e8ab19-2ef6-56fd-916a-4a1c451a0802",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "रुणाईने सुंदर व प्लास्टिकमुक्त शहर निर्मितीकरिता नवी मुंबई यात सक्रिय सहभाग घेऊन प्लास्टिकमुक्त नवी मुंबई महानगरपालिका सातत्याने विविध उपक्रम राबवित करण्यासाठी पुढे आली आहे हे चित्र आश्वासन आहे. स्वच्छता ही नागरिकांची सवय होण्यासाठी असल्याचे मत महापालिका आयुक्त अण्णासाहेब स्वतःपासूनच सुरुवात करत प्रथमतः महानगरपालिकेचे मिसाळ यांनी व्यक्त केले.\nMumbai Chauffer_05.02.2020\nप्लास्टिक प्रदूषणाविरोधात भरीव कामाची गरज\nजे. एस. सहारिया यांचे प्रतिपादन",
  "content_hash": "1fbf300ad01a71fd5dbd128bb8e90f3e10af7007639e99f952921469c91b522d",
  "token_count": 431,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "5079c069-045b-5499-9807-346ca0d9cd64",
  "chunk_index": 31,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Parent · `74663cfa-7f55-5518-8050-a9289adb26b0`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "74663cfa-7f55-5518-8050-a9289adb26b0",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "4. Media Coverage — Media Coverage (cont.)\n\nनवी मुंबई : महाराष्ट्र शासनाचे माजी मुख्य सचिव जे.एस.सहारिया यांनी रिथीक प्लास्टिक या उपक्रमाचे कौतुक करून यामधील युवकांचा सहभाग लक्षणीय असल्याबद्दल समाधान व्यक्त केले. प्लास्टिक प्रदूषणाविरुद्ध वैयक्तिक आणि संस्थात्मक पातळीवर भरीव काम करण्याची गरज त्यांनी व्यक्त केली. टेरी संस्थेचे मुख्य सल्लागार निवृत्त सनदी अधिकारी जी. एस. गील यांनी नवी मुंबई शहर इको सिटी बनण्यासाठी महानगरपालिका प्रयत्नशील असून त्यादृष्टीने टेरी संस्था सहयोगाने काम करीत असल्याचे सांगितले, प्लास्टिक प्रतिबंधाबाबत एक अभिनव प्रकल्प राबविण्याबाबतही काम सुरु असल्याची माहिती त्यांनी दिल\n\n… [+1230 more chars]",
  "content_hash": "5736f1b124759d4a6a131338c7885d0364089205d0868166f7c583d900478708",
  "token_count": 1504,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "page_range": [
    43,
    47
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `76d3dc8c-ff35-5c47-a272-459ecbf8329d`

- vector: dim=3072 · [0.0101, -0.0267, -0.0092, -0.0295, -0.0120, 0.0193, -0.0302, 0.0096, …]

```json
{
  "chunk_id": "76d3dc8c-ff35-5c47-a272-459ecbf8329d",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "नवी मुंबई : महाराष्ट्र शासनाचे माजी मुख्य सचिव जे.एस.सहारिया यांनी रिथीक प्लास्टिक या उपक्रमाचे कौतुक करून यामधील युवकांचा सहभाग लक्षणीय असल्याबद्दल समाधान व्यक्त केले. प्लास्टिक प्रदूषणाविरुद्ध वैयक्तिक आणि संस्थात्मक पातळीवर भरीव काम करण्याची गरज त्यांनी व्यक्त केली. टेरी संस्थेचे मुख्य सल्लागार निवृत्त सनदी अधिकारी जी. एस",
  "content_hash": "f5bcac6fa7cc19fa133d782b50b3e9d0429372e1d32a1ea8f8825cd9691cb5d7",
  "token_count": 332,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "74663cfa-7f55-5518-8050-a9289adb26b0",
  "chunk_index": 32,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `c86f6d6c-f1ad-542e-b6aa-b7c1f16ec392`

- vector: dim=3072 · [0.0150, -0.0479, -0.0131, -0.0380, -0.0151, 0.0129, -0.0116, 0.0268, …]

```json
{
  "chunk_id": "c86f6d6c-f1ad-542e-b6aa-b7c1f16ec392",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "�ी. टेरी संस्थेचे मुख्य सल्लागार निवृत्त सनदी अधिकारी जी. एस गील यांनी नवी मुंबई शहर इको सिटी बनण्यासाठी महानगरपालिका प्रयत्नशील असून त्यादृष्टीने टेरी संस्था सहयोगाने काम करीत असल्याचे सांगितले, प्लास्टिक प्रतिबंधाबाबत एक अभिनव प्रकल्प राबविण्याबाबतही काम सुरु असल्याची माहिती त्यांनी दिली.",
  "content_hash": "c6c9e4f106be483f6b7201304a5cbb3b4f03cd7a1ee466f0cef14325b20ad23b",
  "token_count": 290,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "74663cfa-7f55-5518-8050-a9289adb26b0",
  "chunk_index": 33,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `89258cc6-139f-5d33-9bb5-e614ee76cdfd`

- vector: dim=3072 · [-0.0269, -0.0429, -0.0033, -0.0268, -0.0127, -0.0240, -0.0100, 0.0099, …]

```json
{
  "chunk_id": "89258cc6-139f-5d33-9bb5-e614ee76cdfd",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "� प्रकल्प राबविण्याबाबतही काम सुरु असल्याची माहिती त्यांनी दिली. · टेरी व युनाइटेड नेशन्स एन्व्हायरमेन्ट आणि नवी मुंबई महानगरपालिका यांच्या संयुक्त विद्यमाने सागर विहार से. ८, वाशी येथे जागतिक पाणथळ दिवसाचे औचित्य साधून आयोजित करण्यात आलेल्या विशेष कार्यक्रमाप्रसंगी से आपले मनोगत व्यक्त करीत होते.\n'समुद्री प्लास्टिकपासून पाणथळ जागांचा बचाव'",
  "content_hash": "12b3e721610cc7344106b6a5ce419073354bf634556bf8db2cc2c508ca58d27b",
  "token_count": 342,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "74663cfa-7f55-5518-8050-a9289adb26b0",
  "chunk_index": 34,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `8a2b4916-625e-5c44-adf9-4f93672a583c`

- vector: dim=3072 · [-0.0217, -0.0213, -0.0067, -0.0066, 0.0107, -0.0159, -0.0305, 0.0099, …]

```json
{
  "chunk_id": "8a2b4916-625e-5c44-adf9-4f93672a583c",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "्यक्त करीत होते.\n'समुद्री प्लास्टिकपासून पाणथळ जागांचा बचाव' · मनपा आयुक्त आवासाहेब मिसाळ टेरी संस्थेचे मुख्य सल्लागार माजी सनदी अधिकारी जी. एस. गिल, भारत सरकारचे उच्च अधिकारी लोविश अहूजा, नवी मुंबई महानगरपालिकेच्या पर्यावरण तदर्थ समिती सभापती दिव्या गायकवाड, उप आयुक्त दादासाहेब चाबुकस्वार, टेरी संस्थेच्या सह संचालक डॉ. अंजली पारसनीस, बूप्नईपोच्या प्लास्टिक प्रदूषण सल्लागार सलोनी गोयल व इतर मान्यवर उपस्थित\nहोते.\n\nावेळी वाशीतील कर्मवी\n\nभाऊराव पाटील महाविद्यालय व आयसीएल महाविद्यालय, नेरुळ्ढचे रामराव",
  "content_hash": "095b4beeecd6e774aa9ae8640caab83d9156bed09d0ad263462e5fd2c63d49eb",
  "token_count": 511,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "74663cfa-7f55-5518-8050-a9289adb26b0",
  "chunk_index": 35,
  "page_number": 43,
  "page_range": [
    43,
    45
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```

## Child · `e1c92df6-2320-54c2-9512-d10879f66b39`

- vector: dim=3072 · [-0.0233, 0.0151, -0.0102, -0.0049, -0.0020, -0.0026, -0.0257, 0.0410, …]

```json
{
  "chunk_id": "e1c92df6-2320-54c2-9512-d10879f66b39",
  "document_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "section_heading": "4. Media Coverage — Media Coverage",
  "chunk_text": "पाटील महाविद्यालय व आयसीएल महाविद्यालय, नेरुळ्ढचे रामराव दिक तंत्र महाविद्यालय व एसआईएस महाविद्यालय तसेच इंडियन इन्स्टिट्यूट ऑफ एनव्हारमेंट मॅनेजमेंट\n\nAcknowledgement\n\nWe would like to express our gratitude to :\n• Project\nPartners,\nSponsors,\nNSS\nvolunteers,\nCollege students for actively participating in all\nthe activities.\n• Local citizens and all participants for making this\nevent successful.\n• Media\npersonnel\nfor\ncovering\nthe\nevent\nand\nhelping us reach out to greater audience.\n• Each and Every one who has been associated with\nus in this endeavor\nTHANK YOU",
  "content_hash": "7f5e8f2c579abc0f0dfb089374cf27f9c8c2e44c8a0dd93cdc3a6fbdbb152546",
  "token_count": 257,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_j1_teri_wwd_2020_report_pdf",
  "pdf_path": "Annexure_J1_ TERI_WWD-2020_Report.pdf",
  "parent_chunk_id": "74663cfa-7f55-5518-8050-a9289adb26b0",
  "chunk_index": 36,
  "page_number": 46,
  "page_range": [
    46,
    47
  ],
  "created_at": "2026-06-30T08:31:58.394423+00:00",
  "updated_at": "2026-06-30T08:31:58.394423+00:00"
}
```
