# Qdrant points — ICDL_Poster_2019_Full.pdf

- points (rows upserted): **308**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `210cc344-ad0d-5494-877b-e40b83ee4c8a`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "210cc344-ad0d-5494-877b-e40b83ee4c8a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "THE ENERGY AND — RESOURCES INSTITUTE",
  "chunk_text": "THE ENERGY AND — RESOURCES INSTITUTE\n\nCreating Innovative Solutions for a Sustainable Future\nCONFERENCE PAPERS\nPoster Presentation\nOrganizer\nEditors\nDr P K Bhattacharya\nDr Shantanu Ganguly\nDr Projes Roy\nMs Jolly Koshy\nMs Pallavi Shukla\n\n|  | Editors |\n| --- | --- |\n|  | Dr P K Bhattacharya |\n| Organizer |  |\n|  | Dr Shantanu Ganguly |\n|  | Dr Projes Roy |\n| THE ENERGY AND |  |\n|  | Ms Jolly Koshy |\n| RESOURCES INSTITUTE |  |\n|  | Ms Pallavi Shukla |\n| Creating Innovative Solutions for a Sustainable Future |  |\n\nGoogle Play Store: https://play.google.com/store/apps/details?id=com.teri.icdl2019\n\n\n… [+1448 more chars]",
  "content_hash": "899cd43293ca67fdc67ff161ddf9e4d648737bcbcdd0a7888e82a1d605f72c7c",
  "token_count": 540,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    1,
    3
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `486a7c39-826e-58a1-a059-fdaa74dd5074`

- vector: dim=3072 · [-0.0022, 0.0417, -0.0175, -0.0044, -0.0032, 0.0028, 0.0186, 0.0340, …]

```json
{
  "chunk_id": "486a7c39-826e-58a1-a059-fdaa74dd5074",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "THE ENERGY AND — RESOURCES INSTITUTE",
  "chunk_text": "Creating Innovative Solutions for a Sustainable Future\nCONFERENCE PAPERS\nPoster Presentation\nOrganizer\nEditors\nDr P K Bhattacharya\nDr Shantanu Ganguly\nDr Projes Roy\nMs Jolly Koshy\nMs Pallavi Shukla\n\n|  | Editors |\n| --- | --- |\n|  | Dr P K Bhattacharya |\n| Organizer |  |\n|  | Dr Shantanu Ganguly |\n|  | Dr Projes Roy |\n| THE ENERGY AND |  |\n|  | Ms Jolly Koshy |\n| RESOURCES INSTITUTE |  |\n|  | Ms Pallavi Shukla |\n| Creating Innovative Solutions for a Sustainable Future |  |\n\nGoogle Play Store: https://play.google.com/store/apps/details?id=com.teri.icdl2019\nApple Store: https://apps.apple.com/us\n\n… [+505 more chars]",
  "content_hash": "217ae3c79845bf9b44bb8e7e52d2c6b245038356525622a9c98793f02c487923",
  "token_count": 294,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "210cc344-ad0d-5494-877b-e40b83ee4c8a",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    2
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `64ea2b28-7aba-5fae-b2dc-13643b9bdabc`

- vector: dim=3072 · [0.0072, 0.0606, -0.0131, -0.0107, 0.0216, 0.0232, 0.0097, 0.0443, …]

```json
{
  "chunk_id": "64ea2b28-7aba-5fae-b2dc-13643b9bdabc",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "THE ENERGY AND — RESOURCES INSTITUTE",
  "chunk_text": "session descriptions and locations\n• \nKnow about the speakers and schedule meetings with them\n• \nDevelop network with speakers and others delegates\nICDL 2019 MOBILE APP\nDOWNLOAD\nTweet using ICDL Hashtags\n#ICDL2019   \n#ActDigitally  \n#DigitalTransformation |  |  | ICDL 2019 MOBILE APP DOWNLOAD |  |  |\n| --- | --- | --- | --- | --- |\n|  |  | Google Play Store: https://play.google.com/store/apps/details?id=com.teri.icdl2019 Apple Store: https://apps.apple.com/us/app/icdl-2019/id1483451521 |  |  |\n|  |  | When you download the app, you will be able to: • View conference webcasting • Access the con\n\n… [+559 more chars]",
  "content_hash": "2ed9b3362bf5e3cd28e5b4f289d783b59e3a6167f1cfde13c3b22326942da1ac",
  "token_count": 296,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "210cc344-ad0d-5494-877b-e40b83ee4c8a",
  "chunk_index": 1,
  "page_number": 2,
  "page_range": [
    2,
    3
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1f9dbf03-2240-540a-86e2-2df462fcbf2c`

- vector: dim=3072 · [-0.0280, -0.0236, -0.0179, -0.0391, 0.0055, -0.0077, -0.0222, -0.0055, …]

```json
{
  "chunk_id": "1f9dbf03-2240-540a-86e2-2df462fcbf2c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Conference Proceedings",
  "chunk_text": "T P Sankar, TERI\nVijay Vikram S Parihar, TERI\nReeta Sharma, TERI\nR A Maningdoula Thangal, TERI\nSaloni Priya, TERI\nMs Mithu Dey, TERI\nJolly Koshy, TERI\nAnupama Jauhry, TERI\nEditorial Assistance\nPraveen Bakshi, TERI\nSwapan Kumar Das, TERI\nMuskaan Johri, TERI\nSudeep Pawar, TERI\nRajiv Sharma, TERI\nAman Sachdeva, TERI\nEDITORIAL BOARD",
  "content_hash": "18a2ab8b28f5cb3ad7cd911016146fe9d7409ed71d577e9f501536640ec06b5b",
  "token_count": 139,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 2,
  "page_number": 4,
  "page_range": [
    4,
    4
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `b26ec507-5707-5042-b9a7-e9236fa77766`

- vector: dim=3072 · [-0.0041, 0.0336, -0.0149, 0.0067, 0.0130, 0.0148, 0.0089, 0.0398, …]

```json
{
  "chunk_id": "b26ec507-5707-5042-b9a7-e9236fa77766",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "CONFERENCE PAPERS — International Conference on Digital Landscape",
  "chunk_text": "Digital Transformation for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019\nPOSTER PRESENTATION\nPartners\nKnowledge Partners\nGovernment of India\nMinistry of Science and Technology\nDepartment of Scientifi c and Industrial Research\nMinistry of Electronics and Information Technology\nGovernment of India\nMinistry of Culture\nGovernment of India\n\n© The Energy and Resources Institute, 2019\nNo part of this publication can be reproduced in any form or by any means without the prior permission of \nthe publisher.\nNote\nThe papers included in this publication have been directly reproduced, with m\n\n… [+583 more chars]",
  "content_hash": "79e7ec30d49870789b45d0a127da1d18132a1ebe1db9706c36b88e5a1f106686",
  "token_count": 321,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 3,
  "page_number": 5,
  "page_range": [
    5,
    6
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `25f958b8-b9b2-5d61-a2aa-aa0629870f10`

- vector: dim=3072 · [-0.0081, 0.0240, -0.0169, 0.0060, 0.0076, -0.0101, 0.0085, 0.0267, …]

```json
{
  "chunk_id": "25f958b8-b9b2-5d61-a2aa-aa0629870f10",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Pre-Conference Proceedings Sponsors — Government of India",
  "chunk_text": "Minsitry of Science and Technology\nDepartment of Scientifi c and Industrial Research\nDefence Scientifi c Information and Documentation Centre, Defence \nResearch & Development Organisation, Government of India\nMinistry of Culture\nGovernment of India\nIndian National Science Academy\nRaja Rammohun Roy Library Foundation\nCouncil of Scientifi c and Industrial Research\nGovernment of India\n\nICDL 2019 Organizer and Sponsors\nPartners\n••\nBio-Resources Development Centre\n••\nDefence Research & Development Organisation, Government of India\n••\nDepartment of Scientific and Industrial Research, Ministry of Sci\n\n… [+1064 more chars]",
  "content_hash": "ad0967213261eca3b8b69b32e141abeec73817109a525b7239d815d5af837d9f",
  "token_count": 395,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 4,
  "page_number": 7,
  "page_range": [
    7,
    8
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cb27fef4-f575-555c-b99c-5462b05f1d49`

- vector: dim=3072 · [-0.0168, -0.0093, -0.0114, -0.0069, 0.0020, 0.0051, -0.0238, 0.0469, …]

```json
{
  "chunk_id": "cb27fef4-f575-555c-b99c-5462b05f1d49",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "CONTENTS IN DETAIL — Foreword ...ix — Nitin Desai",
  "chunk_text": "Message from Director General ...xi \nAjay Mathur\nPreface ...xiii \nP K Bhattacharya and Shantanu Ganguly\nICDL 2019 Conference Committee ...xv\nKeynote Speech ...1\nNikhil Seth\nPosters\nDigital rights management and how it is solution to libraries ...11\nPriyanka Bose\nRole of librarian in promoting open access: Study of Indian librarians’ community ...18 \nVrushali Dandawate and M Dhanamajaya\nSecurity and Safety issues in Libraries with special reference to Disaster Management...28 \nJamal Anam and Ali Naushad P M\nIs science built on false claim: An analysis of citation dependency of scientific litera\n\n… [+1318 more chars]",
  "content_hash": "d83d8a419e57f8f14fe93902cc69b265239afbabe9aa475e7f43c1813d89c115",
  "token_count": 467,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 5,
  "page_number": 9,
  "page_range": [
    9,
    10
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0947ab55-c1a7-508b-80c6-ecfbef64f1ea`

- vector: dim=3072 · [-0.0060, 0.0488, -0.0101, -0.0075, 0.0247, 0.0195, -0.0048, 0.0440, …]

```json
{
  "chunk_id": "0947ab55-c1a7-508b-80c6-ecfbef64f1ea",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Foreword — W",
  "chunk_text": "ith the Digital Transformation (DT), the era of trotting from one \nplace to another for services, processes, business decisions, knowledge \naccess have become a story of the past. Virtual world has conquered \nthe world of knowledge and information so much so that by the click of a button \na gateway of wider avenues gets opened like a wonder world. DTl in all sectors \nacross the world has taken over the process of accumulation, transactions, decision \nmaking, marketing and dissemination of knowledge with ease and accuracy. \nToday, DT is no more a concept in incubating stage, but a reality with \n\n… [+1940 more chars]",
  "content_hash": "099dcc9e430a71e38a5a5b94197662dea6673a112ba8d78ce9f552fd713d71b1",
  "token_count": 481,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 6,
  "page_number": 11,
  "page_range": [
    11,
    11
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `a130554d-9f39-5536-b473-964502254e91`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "a130554d-9f39-5536-b473-964502254e91",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Message from Director General — I",
  "chunk_text": "Message from Director General — I\n\nCDL 2019 conference is being organized this year on the broader theme on Digital \nTransformation for an Agile Environment. It has envisaged holding discussions on cross-cutting \nareas in sustainability, access to information and digital transformation in various sectors. \n  In September 2015, the UN Sustainable Development Summit adopted the 2030 agenda which is \nthe key document guiding international eff orts for sustainable development until 2030 through 17 \ngoals in key areas such as poverty, water, energy, education, gender equality, economy, biodiversity\n\n… [+3611 more chars]",
  "content_hash": "6a50b0eef02748ea54dcf3e8640083a9f8af602c51b5ef94306ed6824f76cfc6",
  "token_count": 796,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `e9edbfcf-9571-5a2f-949c-5387e44693ae`

- vector: dim=3072 · [-0.0177, 0.0494, -0.0131, -0.0094, 0.0038, -0.0054, -0.0011, 0.0278, …]

```json
{
  "chunk_id": "e9edbfcf-9571-5a2f-949c-5387e44693ae",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Message from Director General — I",
  "chunk_text": "CDL 2019 conference is being organized this year on the broader theme on Digital \nTransformation for an Agile Environment. It has envisaged holding discussions on cross-cutting \nareas in sustainability, access to information and digital transformation in various sectors. \n  In September 2015, the UN Sustainable Development Summit adopted the 2030 agenda which is \nthe key document guiding international eff orts for sustainable development until 2030 through 17 \ngoals in key areas such as poverty, water, energy, education, gender equality, economy, biodiversity, \nclimate action, and many more. W\n\n… [+1691 more chars]",
  "content_hash": "4688a28fae7ea24bdf8fd06da954d527949f424e332c4e521dc17cf4d9508398",
  "token_count": 435,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "a130554d-9f39-5536-b473-964502254e91",
  "chunk_index": 7,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `22511e78-11f4-5081-a4ca-cdec9b6f3ef0`

- vector: dim=3072 · [0.0070, 0.0425, -0.0131, -0.0224, 0.0109, 0.0183, -0.0071, 0.0486, …]

```json
{
  "chunk_id": "22511e78-11f4-5081-a4ca-cdec9b6f3ef0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Message from Director General — I",
  "chunk_text": "Organizations are increasingly capitalizing enormous \nopportunities of digital transformation more than ever through increased use of digitization, knowledge management, data analytics \nand connected devices. In recent years, most important developments in modern information societies are data-driven research, use of social media for \ncollaborative research and learning and use of mobile technologies for knowledge access. Th e explosion of Social Media in the form \nof user-generated content on blogs, twitter, discussion forums, product reviews, and multimedia sharing sites presents many new \no\n\n… [+1492 more chars]",
  "content_hash": "7f3adf528fc250e05c11eadfd76624e74d8b890891d341bb0387db028d6e2d05",
  "token_count": 387,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "a130554d-9f39-5536-b473-964502254e91",
  "chunk_index": 8,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `370199a1-274e-5d74-955f-aec9e90047bf`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "370199a1-274e-5d74-955f-aec9e90047bf",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preface — D",
  "chunk_text": "Preface — D\n\nigital transformation is about revolutionising the way organisation and institutions are \ncontinuously changing internal operations and activities, addressing need of various \nstakeholders, and embracing new trends and technologies. Whereas an agile approach is \nto roll out new initiatives across the organisation, which will ensure all team members to quickly \nadapt and deliver key product and service innovations and survive in a rapidly developing digital \nworld. It has been estimated that by 2030, India will have 50% share of digital economy in GDP. \nSo there is a dire need to g\n\n… [+4822 more chars]",
  "content_hash": "a4624e30c5775884b8d8f044b4038f5d6d29e6e2b22928e0501aae9a6408a72f",
  "token_count": 1028,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    15,
    16
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `407bd36b-cd41-5e76-af5c-0a328be47380`

- vector: dim=3072 · [-0.0221, 0.0209, -0.0142, -0.0047, -0.0065, 0.0312, 0.0052, 0.0204, …]

```json
{
  "chunk_id": "407bd36b-cd41-5e76-af5c-0a328be47380",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preface — D",
  "chunk_text": "igital transformation is about revolutionising the way organisation and institutions are \ncontinuously changing internal operations and activities, addressing need of various \nstakeholders, and embracing new trends and technologies. Whereas an agile approach is \nto roll out new initiatives across the organisation, which will ensure all team members to quickly \nadapt and deliver key product and service innovations and survive in a rapidly developing digital \nworld. It has been estimated that by 2030, India will have 50% share of digital economy in GDP. \nSo there is a dire need to grow a digital\n\n… [+1771 more chars]",
  "content_hash": "58de49b7faa119eb12039eb4b7673477dc7cec27fed06814538cbfd77873530a",
  "token_count": 430,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "370199a1-274e-5d74-955f-aec9e90047bf",
  "chunk_index": 9,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7c6b3d97-5669-5b30-b7ff-fa7983161e34`

- vector: dim=3072 · [-0.0005, 0.0513, -0.0157, -0.0050, 0.0161, 0.0229, -0.0019, 0.0384, …]

```json
{
  "chunk_id": "7c6b3d97-5669-5b30-b7ff-fa7983161e34",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preface — D",
  "chunk_text": "It has become one of the premier international platforms to facilitate \nthe exchange of knowledge on all dimensions of digital libraries. The entire ICDL was started in 2004, but today in the sixth edition of this conference and research it has evinced a paradigm shift from Digital Libraries to Digital Landscape. This shift is due to \ncontinuous penetration and emergence of Digital Technologies to transform the 17 Sustainable Development Goals identified by \nUnited Nations.  The ICDL 2019 with the theme “Digital Transformation for an Agile Environment”, which will not only create \na roadmap to\n\n… [+819 more chars]",
  "content_hash": "6f3d005934ef3ab0a41eb371fd925a83597a5061c93ab35437ea785b9f7c729b",
  "token_count": 268,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "370199a1-274e-5d74-955f-aec9e90047bf",
  "chunk_index": 10,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `acf22d7c-3fc6-55fa-9147-0eab27e50089`

- vector: dim=3072 · [-0.0033, 0.0504, -0.0173, -0.0103, 0.0191, 0.0188, 0.0026, 0.0428, …]

```json
{
  "chunk_id": "acf22d7c-3fc6-55fa-9147-0eab27e50089",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preface — D",
  "chunk_text": "International Conference on Digital Landscape\nDigital Transformation\u0003 for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019 xiv\nThe event will bring together leaders spearheading digital disruptions in their organizations to offer insights, knowledge, and \ncase studies on contemporary issues and challenges of digital transformation. This conference will comprise an educative mix of \nevents like:\n••\nPlenary Sessions and Thematic Tracks highlighting recent digital library research across the globe by the luminaries\n••\nWorkshops addressing contemporary issues to a focused group of stak\n\n… [+1356 more chars]",
  "content_hash": "f7ceee34e1a3fe5976db8c1de6d4fe458dd4b542c830b3c2dc67a4697d395679",
  "token_count": 396,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "370199a1-274e-5d74-955f-aec9e90047bf",
  "chunk_index": 11,
  "page_number": 16,
  "page_range": [
    16,
    16
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `88cfcaf3-6c2b-537b-a4e5-abf2ecd331d7`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "88cfcaf3-6c2b-537b-a4e5-abf2ecd331d7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "ICDL 2019 Conference Committee — Conference Committee — Patron\n\n••\nNitin Desai, Chairman, Governing Council, The Energy and Resources Institute (TERI), India\nConference Chair\n••\nAjay Mathur, Director General, TERI, India\nConference Organizing Secretaries\n••\nP K Bhattacharya, Fellow and Associate Director, TERI, India\n••\nShantanu Ganguly, Fellow, TERI, India\nConference Convenor [SDG Sessions]\n••\nArupendra Nath Mullick, Fellow and Area Convenor, TERI, India\nAdvisory Committee\nCo-chairs\n••\nArun Goel1, Secretary, Ministry of Culture, Government of India, India\n••\nAmit Kumar, Senior Director, TERI,\n\n… [+3833 more chars]",
  "content_hash": "ff3348c275aca37682c8792c737a37bcd8fc44af90b4a968ed8a7b69d5e4bd68",
  "token_count": 1161,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    17,
    18
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `91eabd0a-5ecd-53c7-8217-4968a8766922`

- vector: dim=3072 · [0.0135, 0.0208, -0.0218, -0.0172, 0.0179, 0.0388, -0.0072, 0.0424, …]

```json
{
  "chunk_id": "91eabd0a-5ecd-53c7-8217-4968a8766922",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "••\nNitin Desai, Chairman, Governing Council, The Energy and Resources Institute (TERI), India\nConference Chair\n••\nAjay Mathur, Director General, TERI, India\nConference Organizing Secretaries\n••\nP K Bhattacharya, Fellow and Associate Director, TERI, India\n••\nShantanu Ganguly, Fellow, TERI, India\nConference Convenor [SDG Sessions]\n••\nArupendra Nath Mullick, Fellow and Area Convenor, TERI, India\nAdvisory Committee\nCo-chairs\n••\nArun Goel1, Secretary, Ministry of Culture, Government of India, India\n••\nAmit Kumar, Senior Director, TERI, India\n••\nRaimund Magis, Deputy High Commissioner, Delegation of\n\n… [+888 more chars]",
  "content_hash": "18e8cb9590f7314f4120495a4223ba91ccce9ace31b562695dc8b38f0a8f8093",
  "token_count": 398,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "88cfcaf3-6c2b-537b-a4e5-abf2ecd331d7",
  "chunk_index": 12,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `408f6954-8398-59a0-8acb-62b076d6a14c`

- vector: dim=3072 · [0.0090, 0.0191, -0.0189, 0.0072, 0.0338, 0.0278, -0.0173, 0.0323, …]

```json
{
  "chunk_id": "408f6954-8398-59a0-8acb-62b076d6a14c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": ", India\n••\nRanbir Singh, Vice Chancellor, National Law University, Delhi, India\n1\t  Note: Invited\nInternational Conference on Digital Landscape\nDigital Transformation\u0003 for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019 xvi\nSteering Committee\nCo-chairs\n••\nUpender Singh Rawat, Joint Secretary (Cyber Diplomacy), Ministry of External Affairs, Government of India,\nIndia\n••\nGopalakrishnan S, Joint Secretary, Ministry of Electronics and Information Technology (MeitY), Government\nof India, India\n••\nVishvas Vidu Sapkal, Join Secretary (BIMSTEC & SAARC), Ministry of External Affairs, Gover\n\n… [+1193 more chars]",
  "content_hash": "11a3a3af7b6baf977cd226d4ca46f0227fc87ca50bf449bc78ad227b3426d761",
  "token_count": 498,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "88cfcaf3-6c2b-537b-a4e5-abf2ecd331d7",
  "chunk_index": 13,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `48ae6f07-c96b-5d5f-9f04-093d7d7e4369`

- vector: dim=3072 · [0.0141, 0.0057, -0.0193, 0.0094, -0.0145, 0.0064, -0.0272, 0.0378, …]

```json
{
  "chunk_id": "48ae6f07-c96b-5d5f-9f04-093d7d7e4369",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "••\nArpan Kar, Associate Professor, Department of Management Studies, Indian Institute of Technology, India\n••\nDebal C Kar, University Librarian, Ambedkar University, India\n••\nH K Kaul Director, DELNET, India\n•• Payal Mago, Principal, Shaheed Rajguru College of Applied Sciences for Women, University of Delhi, India\n••\nThomas Meyer, Director Information and Library Services, South Asia, Goethe-Institut, India\n••\nSanjaya Mishra, Education Specialist (eLearning), Commonwealth of Learning, Canada\n••\nSuchita Ninawe, Department of Biotechnology, Ministry of Science and Technology, Government of India\n\n… [+929 more chars]",
  "content_hash": "d474716c879e7d1d6b6ee0b04b724e3083dba525d4fa8230b913dfbb995594c2",
  "token_count": 369,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "88cfcaf3-6c2b-537b-a4e5-abf2ecd331d7",
  "chunk_index": 14,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `298a2e1d-3503-50c3-adfb-6cc415d4a614`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "298a2e1d-3503-50c3-adfb-6cc415d4a614",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "ICDL 2019 Conference Committee — Conference Committee — Patron (cont.)\n\nxvii\n••\nAlejandro Bia, Miguel Hernández University, Spain\n••\nFrederic Blin, Preservation and Heritage Collections, Former Member of the Governing Board of the\nInternational Federation of Library Associations and Institutions, Bibliotheque nationale et universitaire de\nStrasbourg, France\n••\nJose Borbinha, Technical University of Lisbon, Portugal\n••\nLeslie Chan, Department of Social Sciences, University of Toronto at Scarborough, Canada\n••\nDaniel Castro, Vice President, Information Technology and Innovation Foundation, USA\n•\n\n… [+6050 more chars]",
  "content_hash": "116070422909a423607a2ac858fbd29d527982a3f02ec3313510942caf6afb2e",
  "token_count": 1799,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    19,
    20
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d7ff1f57-382f-5fe9-a254-6010df5b84ac`

- vector: dim=3072 · [0.0195, 0.0038, -0.0206, -0.0028, 0.0097, -0.0102, -0.0133, 0.0377, …]

```json
{
  "chunk_id": "d7ff1f57-382f-5fe9-a254-6010df5b84ac",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "xvii\n••\nAlejandro Bia, Miguel Hernández University, Spain\n••\nFrederic Blin, Preservation and Heritage Collections, Former Member of the Governing Board of the\nInternational Federation of Library Associations and Institutions, Bibliotheque nationale et universitaire de\nStrasbourg, France\n••\nJose Borbinha, Technical University of Lisbon, Portugal\n••\nLeslie Chan, Department of Social Sciences, University of Toronto at Scarborough, Canada\n••\nDaniel Castro, Vice President, Information Technology and Innovation Foundation, USA\n••\nKristy Crawford, Programme Director, Libraries Unlimited, British Coun\n\n… [+1080 more chars]",
  "content_hash": "95710d7d4d3c2c150182a390642ba2a3a74bf4b4c3109f7418c8b6e1cad46ebb",
  "token_count": 436,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "298a2e1d-3503-50c3-adfb-6cc415d4a614",
  "chunk_index": 15,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `74a0739b-7c32-5654-bb92-71e10e83c92f`

- vector: dim=3072 · [-0.0037, 0.0234, -0.0170, -0.0164, 0.0065, 0.0038, -0.0116, 0.0101, …]

```json
{
  "chunk_id": "74a0739b-7c32-5654-bb92-71e10e83c92f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "anus Wisnu Wijaya, Chairperson, Software Engineering Undergraduate Program, Universitas Prasetiya\nMulya, Indonesia\n••\nJohnny Yuen, Assistant Manager, Pao Yue-kong Library, The Hong Kong Polytechnic University, Hong Kong\nNational\n•• Ainul Abedin, Deputy Manager, Habitat Library and Resource Centre, India\n••\nAbdulla Al-Modabber, Assistant Librarian, Prof. G K Chadha Library, South Asian University, India\n••\nSanjay Kumar Bihani, Librarian, Ministry of External Affairs, Government of India, India\n••\nAnand Byrappa, Librarian, Indian Institute of Science, India\n••\nKalyan Kr Bhattacharjee, Deputy Reg\n\n… [+1161 more chars]",
  "content_hash": "027666b4579a8b775f7531e2d073582de519734cfcc4e287f078bd05daefa79f",
  "token_count": 497,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "298a2e1d-3503-50c3-adfb-6cc415d4a614",
  "chunk_index": 16,
  "page_number": 19,
  "page_range": [
    19,
    19
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `92c69a23-0ad9-5b76-8c59-d80567946d4d`

- vector: dim=3072 · [-0.0079, 0.0122, -0.0158, -0.0101, -0.0064, -0.0152, -0.0026, 0.0121, …]

```json
{
  "chunk_id": "92c69a23-0ad9-5b76-8c59-d80567946d4d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "ist ‘G’ and Head, KIRAN Project, DSIR, Government of India, India\n••\nAnand A Jha, Knowledge Manager, CMS India\n••\nH Anil Kumar, Librarian, Indian Institute of Management, Ahmedabad, India\n•• M Madhusudhan, Associate Professor, Department of Library and Information Science, University of Delhi,\nIndia\n••\nG Mahesh, Principal Scientist, Head, NSL, NSDL and NUCSSI, National Institute of Science Communication\nand Information Resources (CSIR-NISCAIR), India\n••\nKavi Mahesh, Director, KAnOE, Centre for Knowledge and Ontological Engineering, Prof., Department of\nComputer Science, Peoples Education Socie\n\n… [+1790 more chars]",
  "content_hash": "118694db0ddbe358d56025fa57bedd0c887c5b155deef9bb4903487eca689210",
  "token_count": 611,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "298a2e1d-3503-50c3-adfb-6cc415d4a614",
  "chunk_index": 17,
  "page_number": 19,
  "page_range": [
    19,
    20
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `97d06f31-3b5d-52ea-a22e-e86106127f4b`

- vector: dim=3072 · [0.0024, 0.0016, -0.0154, 0.0081, 0.0016, -0.0104, -0.0092, 0.0209, …]

```json
{
  "chunk_id": "97d06f31-3b5d-52ea-a22e-e86106127f4b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "ach, Senior Adviser, NASSCOM Foundation, India\n••\nJaideep Sharma, Professor, School of Social Sciences, Indira Gandhi National Open University, India\n••\nR K Sharma, Director (Library), United Nations Information Centre, India\n•• A M Siddiqui, Representative, New Energy and Industrial Technology, Development Organization (NEDO),\nIndia\n••\nM G Sreekumar, Indian Institute of Management Kozhikode, India\n••\nShalini R Urs, Executive Director, International School of Information Management, University of Mysore,\nIndia\n••\nRajeev Vij, Associate Director, Defence Scientific Information and Documentation \n\n… [+796 more chars]",
  "content_hash": "5c1aa5a5253b01c7f16435d7f3235515b5998798c8400ce154247b27ce28b5c7",
  "token_count": 416,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "298a2e1d-3503-50c3-adfb-6cc415d4a614",
  "chunk_index": 18,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `c6e1e964-f673-542d-83c7-4b73fc8d287e`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c6e1e964-f673-542d-83c7-4b73fc8d287e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "ICDL 2019 Conference Committee — Conference Committee — Patron (cont.)\n\nxix\n••\nMithu Dey, TERI, India\n••\nP K Jain, Librarian, Institute of Economic Growth, India\n••\nAnand A Jha, Deputy Manager, Center for Media Studies, India\n••\nI I Jose, TERI, India\n••\nSonali Mathur, TERI, India\n••\nVijay Vikram Singh Parihar, TERI, India\n••\nSaloni Priya, TERI, India\n••\nPraveen Sharma, TERI, India\n••\nJyoti Shukla, TERI, India\n••\nS Sreekala, TERI, India\n••\nN K Wadhwa, National Physical Laboratory, India\n••\nProgramme Cell, TERI, India\nReception Committee\n••\nProgramme Cell, TERI, India\n••\nSangeeta Badhwar, TERI, \n\n… [+2824 more chars]",
  "content_hash": "c5447a66ec8c5a2d61faa4ec828f5bb094c76a082b393c8f326801fc77e928ea",
  "token_count": 1245,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    21,
    25
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0b7e0f46-6e54-5126-98ad-0d234a45b95e`

- vector: dim=3072 · [-0.0023, 0.0008, -0.0097, -0.0117, -0.0039, 0.0154, -0.0206, 0.0323, …]

```json
{
  "chunk_id": "0b7e0f46-6e54-5126-98ad-0d234a45b95e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "xix\n••\nMithu Dey, TERI, India\n••\nP K Jain, Librarian, Institute of Economic Growth, India\n••\nAnand A Jha, Deputy Manager, Center for Media Studies, India\n••\nI I Jose, TERI, India\n••\nSonali Mathur, TERI, India\n••\nVijay Vikram Singh Parihar, TERI, India\n••\nSaloni Priya, TERI, India\n••\nPraveen Sharma, TERI, India\n••\nJyoti Shukla, TERI, India\n••\nS Sreekala, TERI, India\n••\nN K Wadhwa, National Physical Laboratory, India\n••\nProgramme Cell, TERI, India\nReception Committee\n••\nProgramme Cell, TERI, India\n••\nSangeeta Badhwar, TERI, India\n••\nP K Bhattacharya, TERI, India\n••\nN Deepa, TERI, India\n••\nShanta\n\n… [+585 more chars]",
  "content_hash": "08adfd69f0c7df2f71a21b4c0130a41aa6295b594ee85042c0df146ab109677d",
  "token_count": 450,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c6e1e964-f673-542d-83c7-4b73fc8d287e",
  "chunk_index": 19,
  "page_number": 21,
  "page_range": [
    21,
    21
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `091fd7b5-f46a-5575-b6a0-aca485a92912`

- vector: dim=3072 · [-0.0210, -0.0039, -0.0197, -0.0103, 0.0057, 0.0154, -0.0241, 0.0202, …]

```json
{
  "chunk_id": "091fd7b5-f46a-5575-b6a0-aca485a92912",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "••\nHarsh, TERI, India\n••\nAnand A Jha, Deputy Manager, Center for Media Studies, India\n••\nJolly Koshy, TERI, India\n••\nSweta Pandey, Librarian, LNMIIT, India ••\nProjes Roy, Librarian, SRCW, India\n••\nT P Sankar, TERI, India\n••\nNeha Sharma, TERI, India\n••\nReeta Sharma, TERI, India\n••\nAkash Singh, NLU, India\n••\nPallavi Shukla, TERI, India\n••\nR A Maningdoula Thangal, TERI, India\nCultural Committee\n••\nSufian Ahmed, Jamia Millia Islamia, India\n••\nPraveen Bakshi, TERI, India",
  "content_hash": "d37deb68241762126ad4f5c6cf31398bf1298494a7b48659875c21de29cebf84",
  "token_count": 193,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c6e1e964-f673-542d-83c7-4b73fc8d287e",
  "chunk_index": 20,
  "page_number": 21,
  "page_range": [
    21,
    21
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8da0e7ee-7174-5823-8900-1ece31811750`

- vector: dim=3072 · [0.0245, -0.0076, -0.0168, -0.0111, 0.0128, 0.0145, -0.0210, 0.0305, …]

```json
{
  "chunk_id": "8da0e7ee-7174-5823-8900-1ece31811750",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "la, TERI, India\n••\nR A Maningdoula Thangal, TERI, India\nCultural Committee\n••\nSufian Ahmed, Jamia Millia Islamia, India\n••\nPraveen Bakshi, TERI, India xx\n••\nLata Suresh, Indian Institute of Corporate Affairs, India\n••\nR A Maningdoula Thangal, TERI, India\nMedia/Public Relations/Publicity Committee\n••\nP K Bhattacharya, TERI, India\n••\nShantanu Ganguly, TERI, India\n••\nNikhil Kumar, TERI, India\n••\nNilofar, TERI, India\n••\nRishu Nigam, TERI, India\n••\nAkash Singh, Assistant Librarian, National Law University, New Delhi, India\n••\nDharamvir Singh, Former Librarian, Hindustan Times, India\n••\nCommunicatio\n\n… [+743 more chars]",
  "content_hash": "26cb55100295a2e93fa9c715b6828cde2b392b98a234add7221b7cea6b4d9b66",
  "token_count": 499,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c6e1e964-f673-542d-83c7-4b73fc8d287e",
  "chunk_index": 21,
  "page_number": 22,
  "page_range": [
    22,
    22
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `123f2314-7608-548d-af79-a6403b0dab6a`

- vector: dim=3072 · [0.0126, 0.0099, -0.0147, -0.0074, -0.0032, 0.0123, 0.0221, 0.0493, …]

```json
{
  "chunk_id": "123f2314-7608-548d-af79-a6403b0dab6a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "ICDL 2019 Conference Committee — Conference Committee — Patron",
  "chunk_text": "••\nProgramme Cell, TERI, India\nPrinting and Publications Committee\n••\nAnup Das, JNU, India\n••\nN Deepa, TERI, India\n••\nAnupama Jauhry, TERI, India\n•• R N Malviya, Library Consultant, New Delhi, India\n••\nProjes Roy, Librarian, SRCW, New Delhi, India\n••\nT P Sankar, TERI, India\n••\nPallavi Shukla, TERI, India\n••\nTERI Press, TERI, India\nSponsorship and Exhibition Committee\n••\nN Deepa, TERI, India\n••\nT P Sankar, TERI, India\n••\nProgramme Cell, TERI, India\n\nOrganizer — International Conference on Digital Landscape\n\nDigital Transformation\u0003 for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019\n\n… [+206 more chars]",
  "content_hash": "88eb48fb4942cf95c9681e75cd2959c3968ffc7b7c7c9107a6aa86e7b6b1c0d0",
  "token_count": 263,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c6e1e964-f673-542d-83c7-4b73fc8d287e",
  "chunk_index": 22,
  "page_number": 22,
  "page_range": [
    22,
    25
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2fd0607f-dd9e-5056-99f8-256ca9b2966b`

- vector: dim=3072 · [-0.0037, 0.0120, -0.0059, -0.0067, -0.0157, 0.0045, -0.0072, 0.0390, …]

```json
{
  "chunk_id": "2fd0607f-dd9e-5056-99f8-256ca9b2966b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "PART I",
  "chunk_text": "Agenda 2030 and its significance\n1. It is a special privilege for me to be in Delhi, invited by my “guru” Nitin Desai and TERI. Thank\nyou organizers for putting this together.\n2. 2030 Agenda and the SDG’s were adopted in September 2015 in the presence of over 169 Heads\nof    State and Government. The Climate Change agreement in Paris came soon thereafter.\nThe adoption came after two years of intense negotiations with the robust engagement of\ngovernments, business, academia, UN System and civil society.\nThe agenda was built on the ideas and approaches contained in the Millennium Summit, in th\n\n… [+1629 more chars]",
  "content_hash": "cd0f23645d5ac272fb0c1af20380462ebe99524fff1f8868e6e54cdf9d0c9d17",
  "token_count": 504,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 23,
  "page_number": 25,
  "page_range": [
    25,
    25
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `e9c9fac3-8155-5fe7-81e2-9cda74b7b94d`

- vector: dim=3072 · [-0.0250, 0.0313, -0.0075, -0.0233, -0.0094, -0.0224, 0.0138, 0.0290, …]

```json
{
  "chunk_id": "e9c9fac3-8155-5fe7-81e2-9cda74b7b94d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "PART II — Global Assessment",
  "chunk_text": "5. I have been at the SDGs Summit in New York this year. Overall, progress is being made with\nsome favorable trends:\nExtreme poverty and child mortality rates are falling\nProgress in some diseases such as hepatitis\nElectricity access is increasing\nUnemployment levels are back to pre-crisis levels\nUrban population living in slums falling\nMarine protected areas increasing\nGovernments integrating SDGs in national plans increasing\nNear universal response and country ownership\nLocal governments, business, civil society, academia, youth engaging UN system in deep\nreform.\n6. However, while t\n\n… [+1573 more chars]",
  "content_hash": "9a610a29caeed4f9442984b54fe14daecaf10b0cd7f816d8652e8714cc1080db",
  "token_count": 520,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 24,
  "page_number": 26,
  "page_range": [
    26,
    26
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2e94fbd1-3dbe-5086-b981-b5c19c0a6f27`

- vector: dim=3072 · [0.0009, 0.0396, -0.0208, -0.0193, 0.0185, 0.0032, 0.0336, 0.0243, …]

```json
{
  "chunk_id": "2e94fbd1-3dbe-5086-b981-b5c19c0a6f27",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "PART III",
  "chunk_text": "Digital Transformation leading to a low carbon footprint and \nachieving the SDGs \n10. In the past years, digital technologies have spread and began to transform virtually all sectors. The \neducational sector has benefitted largely. And while face-to-face learning will continue to play a \nrole, it is clear that online and blended learning offerings will continue to grow. The promises are \nimmense when we think of the fact that information is a public good, ie everyone can use it (non-\nexclusion) without reducing the benefit of others (non-rivalry). However, there are also challenges \nin develop\n\n… [+633 more chars]",
  "content_hash": "365c4e2c2c0b59aae245b9b17ffe3aac1e36677a6ab6c0bec21d8635f3d72123",
  "token_count": 253,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 25,
  "page_number": 27,
  "page_range": [
    27,
    27
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d144d958-b3a6-5f69-8c24-91176a5de55e`

- vector: dim=3072 · [-0.0288, 0.0380, -0.0180, -0.0099, 0.0069, 0.0057, 0.0096, 0.0267, …]

```json
{
  "chunk_id": "d144d958-b3a6-5f69-8c24-91176a5de55e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "12. Platform and partnership approach",
  "chunk_text": "The UNCC: Learn e-learning platform provides learners credible and free content as well as \ncertification that can help them to progress in their careers or become innovators/champions in \ntheir professional careers.  At this time most learners are public sector or university graduated, \nalthough increasingly teachers are signing up to our courses as a basis for becoming climate \nchange teachers within the general education system.\nThe main added value of UNCC:Learn is that the content is backed by the relevant expertise \nwithin the UN system. 38 UN entities have joined together. UNITAR does\n\n… [+1502 more chars]",
  "content_hash": "9cb180b939a89205c3a8e9413777ea630388b790b53b33ff806d4692cd99bb3e",
  "token_count": 435,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 26,
  "page_number": 27,
  "page_range": [
    27,
    27
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `edd1c991-837f-528b-9da2-cb1379d5eb7a`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "edd1c991-837f-528b-9da2-cb1379d5eb7a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "13. Reaching thousands of learners worldwide",
  "chunk_text": "13. Reaching thousands of learners worldwide\n\nUNCC: Learn is the single largest provider of online courses on climate change and green \neconomy globally, with a total of 250,000 registrants to date and currently issuing more than \n30,000 certificates of completion a year. There are about 25 different courses currently available\n5\n\nin multiple languages. We expect the content to continue to grow. The feedback is positive from \nlearners as evidences by the numbers that are not only starting the courses but completing them.  \nSDG: Learn was just recently launched and so only preliminary feedbac\n\n… [+2626 more chars]",
  "content_hash": "d719099b89de0f7202cc9f74b3b480902cb6d7d079e66ceddb487f8a11b5b285",
  "token_count": 676,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    27,
    28
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `f2acd136-c799-5eb4-97a4-614f95ce381f`

- vector: dim=3072 · [-0.0295, 0.0447, -0.0195, -0.0215, 0.0127, -0.0109, 0.0266, 0.0436, …]

```json
{
  "chunk_id": "f2acd136-c799-5eb4-97a4-614f95ce381f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "13. Reaching thousands of learners worldwide",
  "chunk_text": "UNCC: Learn is the single largest provider of online courses on climate change and green \neconomy globally, with a total of 250,000 registrants to date and currently issuing more than \n30,000 certificates of completion a year. There are about 25 different courses currently available\n5\n\nin multiple languages. We expect the content to continue to grow. The feedback is positive from \nlearners as evidences by the numbers that are not only starting the courses but completing them.  \nSDG: Learn was just recently launched and so only preliminary feedback has been gathered\nfrom members. It is too ea\n\n… [+1779 more chars]",
  "content_hash": "d82a3bc6696cf7f2fee9448844cf46af44f76e6c675857b72b7b4f4780db340a",
  "token_count": 507,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "edd1c991-837f-528b-9da2-cb1379d5eb7a",
  "chunk_index": 27,
  "page_number": 27,
  "page_range": [
    27,
    28
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `de84d325-fb09-5752-a0a3-0182607a6d5b`

- vector: dim=3072 · [-0.0077, 0.0337, -0.0262, -0.0092, 0.0088, 0.0150, 0.0048, 0.0323, …]

```json
{
  "chunk_id": "de84d325-fb09-5752-a0a3-0182607a6d5b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "13. Reaching thousands of learners worldwide",
  "chunk_text": "UNCC:Learn can issue a certificate of completion on the basics of climate change, for example, at less than USD 20.  By contrast, more advanced and\napplied content still requires a face to face approach, potential backed by on the job coaching.\nE-learning can significantly increase the cost effectiveness of this latter approach but blended\nlearning is the optimal approach in our estimate.\nSDG:Learn features search functions for blended learning that lists the available blended\nlearning courses within the users preferred interest areas. We foresee an increase in the blended\nlearning courses of\n\n… [+256 more chars]",
  "content_hash": "dcd005d88c3de27cbda586147b63a177e72fec83ebc8b1ac73a7eac5904c0a3c",
  "token_count": 170,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "edd1c991-837f-528b-9da2-cb1379d5eb7a",
  "chunk_index": 28,
  "page_number": 28,
  "page_range": [
    28,
    28
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `21c5a037-63e5-52a6-b9f6-19eadc513408`

- vector: dim=3072 · [-0.0126, 0.0222, -0.0250, -0.0004, 0.0202, 0.0118, -0.0192, 0.0332, …]

```json
{
  "chunk_id": "21c5a037-63e5-52a6-b9f6-19eadc513408",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "15. Innovation in design",
  "chunk_text": "Learning from social media: UNCC:Learn has active social media accounts but the impact in this\narea is relatively weak.  It is hard to measure the effectiveness of social media in advancing\nUNCC:Learn objectives and the programme is constantly re-evaluating its strategy. One lesson\nlearned appears to be that all visible global programmes need to have social media in order to have\ncredibility. But whether social media achieves something more tangible beyond this remains a key\nquestion.\nIncorporating best practice: SDG:Learn has made efforts to design the platform to be mindful of\npeople with \n\n… [+444 more chars]",
  "content_hash": "bece26678ad2bb4fe06c45628c6dc9869a83765697867f3d4c797bc6c645a83d",
  "token_count": 214,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 29,
  "page_number": 28,
  "page_range": [
    28,
    29
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2c470bae-9c4a-549e-9a68-4e1146598666`

- vector: dim=3072 · [-0.0566, 0.0360, -0.0201, -0.0100, -0.0100, -0.0077, -0.0186, 0.0517, …]

```json
{
  "chunk_id": "2c470bae-9c4a-549e-9a68-4e1146598666",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "16. Business models",
  "chunk_text": "Free vs. fee based approaches:  Both platforms are free to the learner but is relatively high cost to\nmaintain and to create content. We still depend on traditional donor contributions and UN co-\nfinancing.  Private sector funding has been obtained in developing specific courses that are of\ninterest to clients, but getting seed funding to support the overall efforts of the platform has been\nmore difficult.  We foresee that the traditional donors will continue to be needed for this with the\nargument being that we can leverage this funding significantly.  At this time we do not think that a\ndir\n\n… [+778 more chars]",
  "content_hash": "5d621957f6ab47dbd475471b08f4b6061de7fe1f8f48927df63e45956c8e2d9a",
  "token_count": 284,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 30,
  "page_number": 29,
  "page_range": [
    29,
    29
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `bade4e56-e957-5a79-ab08-f96911e2dad6`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "bade4e56-e957-5a79-ab08-f96911e2dad6",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "Organizer — International Conference on Digital Landscape\n\nDigital Transformation\u0003 for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019\nPOSTER PRESENTATION\nThe Energy and Resources Institute\n\nICDL 2019: Poster \nDigital Rights Management and how it is solution \nto libraries \nPriyanka Bose \nStudent, Master of Library and Information Science, Tata Institute of Social Sciences \nAbstract \nThis kind of Rights are thought to be very restrictive for libraries to flourish. We will search \nthrough this paper. That they are not in fact they are bridge between the intellectual output and \nthe \n\n… [+8987 more chars]",
  "content_hash": "961c780efd13a5862674711a8ba3ab51355070a3bd438a73a5d446eb6bb75fc0",
  "token_count": 1976,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    31,
    36
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1505847c-2b8e-5bf6-88e3-2d3a9346ff37`

- vector: dim=3072 · [-0.0182, 0.0071, -0.0138, 0.0034, 0.0035, 0.0079, -0.0220, 0.0264, …]

```json
{
  "chunk_id": "1505847c-2b8e-5bf6-88e3-2d3a9346ff37",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "Digital Transformation\u0003 for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019\nPOSTER PRESENTATION\nThe Energy and Resources Institute\n\nICDL 2019: Poster \nDigital Rights Management and how it is solution \nto libraries \nPriyanka Bose \nStudent, Master of Library and Information Science, Tata Institute of Social Sciences \nAbstract \nThis kind of Rights are thought to be very restrictive for libraries to flourish. We will search \nthrough this paper. That they are not in fact they are bridge between the intellectual output and \nthe users.  \nKeywords \nDRM, Right Holders, Copyright, IITD, Fai\n\n… [+1674 more chars]",
  "content_hash": "01277e066e7a567017394140c37ecb4d69bbe77b4dade0e33f239a92097e1c85",
  "token_count": 479,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "bade4e56-e957-5a79-ab08-f96911e2dad6",
  "chunk_index": 31,
  "page_number": 31,
  "page_range": [
    31,
    33
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1c2bdd1f-29cf-5042-8688-4b6dc0f9bfd8`

- vector: dim=3072 · [-0.0451, -0.0004, -0.0189, -0.0061, -0.0121, -0.0075, -0.0250, 0.0257, …]

```json
{
  "chunk_id": "1c2bdd1f-29cf-5042-8688-4b6dc0f9bfd8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "The concept of usage is connected to digital work.  \nDRM: The concept \nIt is by which that the control and management of the user right & business logic, integrating DRM technology with the components such as locker right, subscription management would be \n11\n\nICDL 2019: Poster \nacross the various devices. Those who have right in their hand can work out over who will use \ntheir work and how will they use the work. These kinds of the rights are attached to the particular \ndocument at the time of the distribution with the work author give up the rights of his work to the \npublisher. Those who ha\n\n… [+1680 more chars]",
  "content_hash": "abac3eda6f8dbc51cb85fdaf0f3a1c60ccf9adf9799b6ab114354613069cec90",
  "token_count": 490,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "bade4e56-e957-5a79-ab08-f96911e2dad6",
  "chunk_index": 32,
  "page_number": 33,
  "page_range": [
    33,
    34
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ed87aba3-0f0e-5156-ba0f-86e91826b81f`

- vector: dim=3072 · [-0.0276, -0.0072, -0.0157, 0.0156, 0.0023, 0.0228, -0.0074, 0.0060, …]

```json
{
  "chunk_id": "ed87aba3-0f0e-5156-ba0f-86e91826b81f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "Things like \nencryption is important as there is presence of workflow such as for those works which are yet to \nbe published. \nWhatever we are observing above is very important for the REL for the management of the data \nwhich is also automated. \n12 ICDL 2019: Poster \nInteroperability \nThere are large number of stakeholders who are working with these regulations, there is no \nalternate ways for cooperation, and all the standards have to be international in the global \ninternet. It is a precondition to see that if things are interoperable. Example can be taken of the \nthings such as in case of \n\n… [+1848 more chars]",
  "content_hash": "d6f3b670d6b13572860bc435c546d0c340a009ed0e9f723aa5d6a99e9f706cda",
  "token_count": 485,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "bade4e56-e957-5a79-ab08-f96911e2dad6",
  "chunk_index": 33,
  "page_number": 35,
  "page_range": [
    35,
    35
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `9ca4ffbd-315e-5d63-9dd1-bae166e65c54`

- vector: dim=3072 · [-0.0179, -0.0054, -0.0189, 0.0295, -0.0139, 0.0040, -0.0267, 0.0188, …]

```json
{
  "chunk_id": "9ca4ffbd-315e-5d63-9dd1-bae166e65c54",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "To produce this kind of files simple office tools are used such as Microsoft office, \nLibre office and various kind of office suites. In the era of only print libraries the libraries had minimal job when it comes to publishing. Only \npublication done was catalogue card and library manual. In the current era the libraries job has \nturned into what is known as a publisher. The creation of the content is done in the parent \norganization and by its students and faculty. The content can be very specific as the parent \ninstitution such as, if the institution is of engineering then the library will p\n\n… [+2470 more chars]",
  "content_hash": "5b1691cca5c3cbc26741b935b18251ba6bd25bda443f8ce669b3cab2611b1fe0",
  "token_count": 623,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "bade4e56-e957-5a79-ab08-f96911e2dad6",
  "chunk_index": 34,
  "page_number": 35,
  "page_range": [
    35,
    36
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `ca5cba69-1717-5c9a-b04c-5e3a1f29c81b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ca5cba69-1717-5c9a-b04c-5e3a1f29c81b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "Organizer — International Conference on Digital Landscape (cont.)\n\nICDL 2019: Poster \nCopyright Laws \nWorld Intellectual Property Organization \nThis is a kind of special organization of United Nations, created in 1967 so there is production of \nmore creative action to promote protection of intellectual right in the world. In this 192 members \nare present who administer 26 worldwide treaties, it’s headquarter in Geneva, Switzerland. \nDigital Millennium Copyright Acts (DMCA) \nThis law which was signed by U.S. President Clinton on October 28, 1998, as a response to \nWorld Intellectual Property Or\n\n… [+7505 more chars]",
  "content_hash": "9c201bc91457bb55f562639b721e74ef8c3754c08a6e1c848b2faa046ee1d2a7",
  "token_count": 1760,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    37,
    40
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `21b4c4ba-cd1d-5268-96ef-aece960eceeb`

- vector: dim=3072 · [-0.0261, -0.0023, -0.0161, 0.0070, 0.0037, -0.0031, -0.0218, 0.0235, …]

```json
{
  "chunk_id": "21b4c4ba-cd1d-5268-96ef-aece960eceeb",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "ICDL 2019: Poster \nCopyright Laws \nWorld Intellectual Property Organization \nThis is a kind of special organization of United Nations, created in 1967 so there is production of \nmore creative action to promote protection of intellectual right in the world. In this 192 members \nare present who administer 26 worldwide treaties, it’s headquarter in Geneva, Switzerland. \nDigital Millennium Copyright Acts (DMCA) \nThis law which was signed by U.S. President Clinton on October 28, 1998, as a response to \nWorld Intellectual Property Organization treaties, there is a provision where overcoming is \nimpo\n\n… [+1590 more chars]",
  "content_hash": "4f930183c9746354a62712554cb65d48ac7497a49c82530fb60deb6d76036560",
  "token_count": 445,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ca5cba69-1717-5c9a-b04c-5e3a1f29c81b",
  "chunk_index": 35,
  "page_number": 37,
  "page_range": [
    37,
    37
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7f7c9bb5-bde6-5499-8bea-563c852ed18b`

- vector: dim=3072 · [-0.0254, 0.0122, -0.0162, -0.0084, -0.0167, 0.0111, -0.0203, 0.0172, …]

```json
{
  "chunk_id": "7f7c9bb5-bde6-5499-8bea-563c852ed18b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "DRM sometimes turn out to be good for librarians such as, this make it possible to manage all \nthe rights which are associated with it. Machine readable information can enhance to develop \nnew offer. This becomes important for libraries if they don’t want to be get lost in the newly established intelligence world. They need to support rights which are transparent libraries need to \nhave new ways of showing rights to show things are transparent which supports DRM such as \n15\n\nICDL 2019: Poster \ndocuments & open access to have legal confidence. The users of the library will use their rights \nwel\n\n… [+2006 more chars]",
  "content_hash": "5e681ec2c14dec1dfd2848c767de20ad00130a88767113a2e9fe4f297010d2a8",
  "token_count": 540,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ca5cba69-1717-5c9a-b04c-5e3a1f29c81b",
  "chunk_index": 36,
  "page_number": 37,
  "page_range": [
    37,
    38
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4c13b2aa-be04-5e28-805c-21cb5616233e`

- vector: dim=3072 · [-0.0199, -0.0024, -0.0171, 0.0100, -0.0203, -0.0037, -0.0214, 0.0284, …]

```json
{
  "chunk_id": "4c13b2aa-be04-5e28-805c-21cb5616233e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "Not\nfollowing this could lead to penal action. If systematic download is done then the publisher will block entire community of users\nfrom accessing this resources.\nShould not be used for commercial gains. Distributing it to unauthorized user is not\nallowed. Uploading publisher’s version on the open access website is not acceptable.\nConclusion \nAs it can be seen that DRM is sometimes taken to be very restrictive on the libraries, at the same \ntime it is very useful, and make things manageable.  \n16\n\nICDL 2019: Poster \nReferences \n1.\nBöhner, D. (2008). Digital rights description as part of di\n\n… [+962 more chars]",
  "content_hash": "4e778cff2617fb37315204895b1ae64275ffc37a959fd60acf6eae7ef87da48d",
  "token_count": 407,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ca5cba69-1717-5c9a-b04c-5e3a1f29c81b",
  "chunk_index": 37,
  "page_number": 38,
  "page_range": [
    38,
    39
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ecb3d2df-7cbf-5143-b417-2281bcfa9cc8`

- vector: dim=3072 · [-0.0560, 0.0110, -0.0090, -0.0069, -0.0277, 0.0211, -0.0222, 0.0166, …]

```json
{
  "chunk_id": "ecb3d2df-7cbf-5143-b417-2281bcfa9cc8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Organizer — International Conference on Digital Landscape",
  "chunk_text": "Mahesh, G., & Mittal, R. (2009). Digital content creation and copyright issues. The Electronic Library,\n27(4), 676–683. https://doi.org/10.1108/02640470910979615\n17 ICDL 2019: Poster \nRole of Librarian in Promoting Open Access: \nStudy of Indian Librarians Community \nVrushali Dandawate   \nLibrarian, AISSMS College of Engineering College Pune; DOAJ Ambassador, India. \nM Dhanamajaya \nRegistrar, Reva University, Bangalore \nAbstract\nOpen Access put lot of impact on Library and information centres from last decade. Growth of \nOpen Access Journals and Scholarly communication is affecting Library serv\n\n… [+1571 more chars]",
  "content_hash": "898ed724e4ec8618fb979bf62970ecb3061fcd80a6a2c2b0ab74b790d5a1cd6f",
  "token_count": 476,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ca5cba69-1717-5c9a-b04c-5e3a1f29c81b",
  "chunk_index": 38,
  "page_number": 40,
  "page_range": [
    40,
    40
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `04a6260f-32dc-54e3-84e1-861db19ebd86`

- vector: dim=3072 · [-0.0446, 0.0310, -0.0031, -0.0155, -0.0034, 0.0073, -0.0053, 0.0254, …]

```json
{
  "chunk_id": "04a6260f-32dc-54e3-84e1-861db19ebd86",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "1 http://www.budapestopenaccessinitiative.org/ Accessed on 18/3/2018",
  "chunk_text": "18\n\nICDL 2019: Poster \ntechnical barriers other than those inseparable from gaining access to the internet itself. The only \nconstraint on reproduction and distribution, and the only role for copyright in this domain, should \nbe to give authors control over the integrity of their work and the right to be properly \nacknowledged and cited.\" \nPeter Suber 2007 mentioned2: \"Open-access (OA) literature is digital, online, free of charge, \nand free of most copyright and licensing restrictions. OA removes price barriers (subscriptions, \nlicensing fees, pay-per-view fees) and permission barriers (most \n\n… [+1682 more chars]",
  "content_hash": "a0c0f8622a7431d7a4eace7e36d0962285d1c8f174dea2241ae6a8ff02976378",
  "token_count": 464,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 39,
  "page_number": 40,
  "page_range": [
    40,
    41
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `06e8839b-48d5-56ee-bccc-9b56601898a1`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "06e8839b-48d5-56ee-bccc-9b56601898a1",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3 https://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018 — 4 http://wordpress.openoasis.org/promoting-open-access/ accessed on 24/5/2018",
  "chunk_text": "3 https://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018 — 4 http://wordpress.openoasis.org/promoting-open-access/ accessed on 24/5/2018\n\n19\n\n| ICDL 2019: Poster |  |  |\n| --- | --- | --- |\n| technical barriers other than those inseparable from gaining access to the internet itself. The only |  |  |\n| constraint on reproduction and distribution, and the only role for copyright in this domain, should |  |  |\n| be to give authors control over the integrity of their work and the right to be properly |  |  |\n| acknowledged and cited.\" |  |  |\n| Peter Suber 2007 me\n\n… [+2397 more chars]",
  "content_hash": "96ff56b7d8e85ddfdb056003780a57e48622ef9a66839810e2f3492086160421",
  "token_count": 757,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    41,
    42
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ab096762-694f-54b3-be46-d75421de8237`

- vector: dim=3072 · [-0.0449, 0.0187, -0.0062, -0.0306, -0.0113, -0.0011, 0.0111, 0.0259, …]

```json
{
  "chunk_id": "ab096762-694f-54b3-be46-d75421de8237",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3 https://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018 — 4 http://wordpress.openoasis.org/promoting-open-access/ accessed on 24/5/2018",
  "chunk_text": "19\n\n| ICDL 2019: Poster |  |  |\n| --- | --- | --- |\n| technical barriers other than those inseparable from gaining access to the internet itself. The only |  |  |\n| constraint on reproduction and distribution, and the only role for copyright in this domain, should |  |  |\n| be to give authors control over the integrity of their work and the right to be properly |  |  |\n| acknowledged and cited.\" |  |  |\n| Peter Suber 2007 mentioned2: \"Open-access (OA) literature is digital, online, free of charge, |  |  |\n| and free of most copyright and licensing restrictions. OA removes price barriers (subsc\n\n… [+1797 more chars]",
  "content_hash": "02523efdb81b28d03578f1fd66ab5623ae45bdacb257248f441b457230b1cce1",
  "token_count": 561,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "06e8839b-48d5-56ee-bccc-9b56601898a1",
  "chunk_index": 40,
  "page_number": 41,
  "page_range": [
    41,
    41
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0a5fa64c-4edd-5da6-a344-09c37927faf5`

- vector: dim=3072 · [-0.0298, 0.0227, -0.0067, -0.0573, 0.0100, 0.0066, 0.0033, 0.0395, …]

```json
{
  "chunk_id": "0a5fa64c-4edd-5da6-a344-09c37927faf5",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3 https://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018 — 4 http://wordpress.openoasis.org/promoting-open-access/ accessed on 24/5/2018",
  "chunk_text": "|\n| Open access helps to researcher by following ways |  |  |\n|  | 1. | To improve visibility and impact of their research |\n|  | 2. | Free access to required research material. |\n|  | 3. | Control of researcher publications usage policy | | 2 Suber, Peter. \"Open Access Overview\" Archived2007-05-19 at the Wayback Machine.. Earlham.edu. Retrieved on |  |  |\n| 17/3/2018. http://legacy.earlham.edu/~peters/fos/overview.htm |  |  |\n| 3 https://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018 |  |  |\n| 4 http://wordpress.openoasis.org/promoting-open-access/ accessed o\n\n… [+67 more chars]",
  "content_hash": "eb8aa3793dfb4678b02b85cd59f0b3018bf303740c47fff9f8661d129403b7f0",
  "token_count": 206,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "06e8839b-48d5-56ee-bccc-9b56601898a1",
  "chunk_index": 41,
  "page_number": 41,
  "page_range": [
    41,
    42
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7b9a1fe7-d956-5ac4-84e6-0bb1ac5c4073`

- vector: dim=3072 · [-0.0482, 0.0160, -0.0147, 0.0002, -0.0377, -0.0061, 0.0017, 0.0118, …]

```json
{
  "chunk_id": "7b9a1fe7-d956-5ac4-84e6-0bb1ac5c4073",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "1. Help to improve visibility and prestige of Institute",
  "chunk_text": "2. To enable research institutions to better account for their research output.\nPolicy makers and funding agencies \n1. All Government funded project are available for public access. Free peer reviewed\narticles can be refereed by all\n2. Open Access will increase the government's return on investment in research by enabling\nmore widespread dissemination and uptake of knowledge.\n3. Open Access will enable research funders who need to be able to access and keep track of\noutputs from their funding, and measure and assess how effectively their money has been\nspent.\nOpen Access Resources \nOpen Access\n\n… [+1350 more chars]",
  "content_hash": "49f9c0f403b8428fbf595af7fc9ae2796f0336d21e1ce046303fd9c081b7cfff",
  "token_count": 380,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 42,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `2102841c-6ca3-557c-a11c-a0312fc35009`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "2102841c-6ca3-557c-a11c-a0312fc35009",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "5 http://doabooks.org/",
  "chunk_text": "5 http://doabooks.org/\n\n20\n\n| ICDL 2019: Poster |  |\n| --- | --- |\n| Administrators |  |\n| 1. | Help to improve visibility and prestige of Institute |\n| 2. | To enable research institutions to better account for their research output. |\n| Policy makers and funding agencies |  |\n| 1. | All Government funded project are available for public access. Free peer reviewed |\n|  | articles can be refereed by all |\n| 2. | Open Access will increase the government's return on investment in research by enabling |\n|  | more widespread dissemination and uptake of knowledge. |\n| 3. | Open Access will enable r\n\n… [+4279 more chars]",
  "content_hash": "ba7225b965efa1b940893fb67e9bd19c159da99fb749e137f3fcfc79a5a7956b",
  "token_count": 1018,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    42,
    43
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a7b9bf87-a354-5d3a-af66-cc23c7a3dc32`

- vector: dim=3072 · [-0.0409, 0.0201, -0.0079, -0.0332, -0.0076, -0.0080, 0.0201, 0.0362, …]

```json
{
  "chunk_id": "a7b9bf87-a354-5d3a-af66-cc23c7a3dc32",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "5 http://doabooks.org/",
  "chunk_text": "20\n\n| ICDL 2019: Poster |  |\n| --- | --- |\n| Administrators |  |\n| 1. | Help to improve visibility and prestige of Institute |\n| 2. | To enable research institutions to better account for their research output. |\n| Policy makers and funding agencies |  |\n| 1. | All Government funded project are available for public access. Free peer reviewed |\n|  | articles can be refereed by all |\n| 2. | Open Access will increase the government's return on investment in research by enabling |\n|  | more widespread dissemination and uptake of knowledge. |\n| 3. | Open Access will enable research funders who need\n\n… [+1685 more chars]",
  "content_hash": "4e99b2f8bcbc77d476d438d741d8d620984ff1139793f0a21a29176a4942c932",
  "token_count": 520,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "2102841c-6ca3-557c-a11c-a0312fc35009",
  "chunk_index": 43,
  "page_number": 42,
  "page_range": [
    42,
    42
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7e3554eb-267e-5af8-a505-b136c970493e`

- vector: dim=3072 · [-0.0497, 0.0501, -0.0049, 0.0019, -0.0108, -0.0144, 0.0041, 0.0235, …]

```json
{
  "chunk_id": "7e3554eb-267e-5af8-a505-b136c970493e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "5 http://doabooks.org/",
  "chunk_text": "Some are subsidized, and some require payment on behalf of the |  |\n| author. |  |\n| 5 http://doabooks.org/ |  |\n|  | 20 | ICDL 2019: Poster \nDOAJ (https://doaj.org)6 is a centrally, publicly and internationally available community-curated\ndatabase containing information on high quality open access journal titles across all disciplines, \nmaintained by a team of professionals. It aims to become the default service for finding quality, \npeer-reviewed open access publications. Only trusted scholarly journal titles adhering to DOAJ \ncriteria are considered for inclusion. \nOpen Repositories \nVariou\n\n… [+2092 more chars]",
  "content_hash": "09f3cb1ef4c189e10726b8078bfbc431623908b747a87803698d9728bfcddf0e",
  "token_count": 531,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "2102841c-6ca3-557c-a11c-a0312fc35009",
  "chunk_index": 44,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `8a9ccb5e-0240-5022-ac5c-2db40945800c`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "8a9ccb5e-0240-5022-ac5c-2db40945800c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6 http://doaj.org — 7 http://opendoar.org/",
  "chunk_text": "6 http://doaj.org — 7 http://opendoar.org/\n\n8 Jain, Priti, \"Promoting Open Access to Research in Academic Libraries\" (2012). Library Philosophy and Practice (e-\njournal). 737. http://digitalcommons.unl.edu/libphilprac/737 \n9 Giarlo, M.J. (2005). The impact of open access on academic libraries. Available: \nhttp://lackoftalent.org/michael/papers/532.pdf \n10 Cryer, E., & Collins, M. (2011). Incorporating Open Access into Libraries. Serials , 37 (2), 103-107. Jain, P. (2012). \nPromoting Open Access to Research in Academic Libraries. \n21\n\nICDL 2019: Poster \nand becoming active OA journal publishers\n\n… [+5155 more chars]",
  "content_hash": "34aa9c810015b3412d233f6eeea247b5f1f0ba9ce4d85ed2e4fcb25ec8f38c88",
  "token_count": 1362,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    43,
    48
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8f9c13cb-4314-548d-9298-3bf93460ac8d`

- vector: dim=3072 · [-0.0480, 0.0320, -0.0160, 0.0328, -0.0310, -0.0014, -0.0149, 0.0193, …]

```json
{
  "chunk_id": "8f9c13cb-4314-548d-9298-3bf93460ac8d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6 http://doaj.org — 7 http://opendoar.org/",
  "section_type": "references",
  "chunk_text": "8 Jain, Priti, \"Promoting Open Access to Research in Academic Libraries\" (2012). Library Philosophy and Practice (e-\njournal). 737. http://digitalcommons.unl.edu/libphilprac/737 \n9 Giarlo, M.J. (2005). The impact of open access on academic libraries. Available: \nhttp://lackoftalent.org/michael/papers/532.pdf \n10 Cryer, E., & Collins, M. (2011). Incorporating Open Access into Libraries. Serials , 37 (2), 103-107. Jain, P. (2012). \nPromoting Open Access to Research in Academic Libraries. \n21",
  "content_hash": "2b56c5149586ce4ca7aef79553e4191e751060c1bfaa2792952baee27922a3d5",
  "token_count": 143,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "8a9ccb5e-0240-5022-ac5c-2db40945800c",
  "chunk_index": 45,
  "page_number": 43,
  "page_range": [
    43,
    43
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `9af24452-c3ce-5df7-90b4-e93621c16df7`

- vector: dim=3072 · [-0.0569, 0.0132, -0.0149, -0.0100, -0.0277, 0.0066, -0.0125, 0.0203, …]

```json
{
  "chunk_id": "9af24452-c3ce-5df7-90b4-e93621c16df7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6 http://doaj.org — 7 http://opendoar.org/",
  "chunk_text": "(2011). Incorporating Open Access into Libraries. Serials , 37 (2), 103-107. Jain, P. (2012). \nPromoting Open Access to Research in Academic Libraries. \n21 ICDL 2019: Poster \nand becoming active OA journal publishers. Ugwuanyi etl11 (2013) identified that the\nperceptions of librarians in colleges of education in south-east Nigeria towards Open Access to \nknowledge were positive. The researchers Ugwuanyi & Ugwaungy (2013) also discovered that \nmost of the librarians did not understand the concept of Open Access Kelem Kassahun12 and\nChatiwa Nsala (2015) studied the use of open access by private \n\n… [+1450 more chars]",
  "content_hash": "1e12a7c463a3d1e6b6010352b273fc6f15a8fee699805bd290eef496e7e4788b",
  "token_count": 486,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "8a9ccb5e-0240-5022-ac5c-2db40945800c",
  "chunk_index": 46,
  "page_number": 44,
  "page_range": [
    44,
    44
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `bfcdcdfa-0172-50ec-baa4-efb14ca60c40`

- vector: dim=3072 · [-0.0328, 0.0370, -0.0209, -0.0014, -0.0214, -0.0033, 0.0157, 0.0329, …]

```json
{
  "chunk_id": "bfcdcdfa-0172-50ec-baa4-efb14ca60c40",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6 http://doaj.org — 7 http://opendoar.org/",
  "chunk_text": "The awareness of academic librarians towards Open Access \nresources to support reference services: A case of private institutions of higher learning in Gaborone, Botswana \nConference paper IFLA Conference 2015 \n22 ICDL 2019: Poster \nChart 1: It shows the response rate to questionnaire from various respondent institute librarians \n79.4% was working as Academic Librarians while 3.2 % was corporate librarians 7.9 % was \nuniversity librarians and 9.5% was research librarians   \nChart 2: It shows 9.5% librarians was not aware about term Open Access where 90.5 % \nLibrarians was aware about Open Acce\n\n… [+933 more chars]",
  "content_hash": "8a64f0ea21e94f90abd5aab42b620f4fe9f35f7cffc8f682b8fcda884b526ee7",
  "token_count": 386,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "8a9ccb5e-0240-5022-ac5c-2db40945800c",
  "chunk_index": 47,
  "page_number": 45,
  "page_range": [
    45,
    46
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0d882efa-3289-5494-9696-ea01e9700909`

- vector: dim=3072 · [-0.0552, 0.0323, -0.0066, 0.0136, -0.0329, 0.0051, -0.0117, 0.0278, …]

```json
{
  "chunk_id": "0d882efa-3289-5494-9696-ea01e9700909",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6 http://doaj.org — 7 http://opendoar.org/",
  "chunk_text": "And 12.7% of librarians were involved in organizing workshop and \nconferences on Open Access for user community.    \n24 ICDL 2019: Poster \nChart 6: It shows 96.8% libraries in India are giving APC charges to the users to publish their \npaper in Open Access Journals while 3.2% libraries have budget for this was research Libraries.   \nChart 7: 93.7 % librarians said that Open Access is important for them while 6.3% librarians \nstill feel Open Access in not important    \nAnalysis of survey \nMany librarians mentioned Open Access is a good source, but most of the students and teachers \navoid librar\n\n… [+1518 more chars]",
  "content_hash": "30e851d984c96b5c7402ee6ba5c38d29df4525629b14318cbdf4278450b34e66",
  "token_count": 446,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "8a9ccb5e-0240-5022-ac5c-2db40945800c",
  "chunk_index": 48,
  "page_number": 47,
  "page_range": [
    47,
    48
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `e15ad54b-9c1b-51bc-af52-8eafaf883881`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e15ad54b-9c1b-51bc-af52-8eafaf883881",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "3. Library should start promoting Open Access Weeks\n\n(http://www.openaccessweek.org/page/about)\n4. Librarian should educate the users by proving links of various useful open access\nresources on the library website.  Librarian should assist in payment of author's fees to\npublish in open access journals.\nReferences \n1.\nhttp://www.budapestopenaccessinitiative.org/ Accessed on 18/3/2018\n2.\nSuber, Peter. \"Open Access Overview\" Archived2007-05-19 at the Wayback Machine.. Earlham.edu. \nRetrieved on 17/3/2018.  http://legacy.earlham.edu/~peters/fos/overview.htm \n3.\nhttps://www.opensocietyfoundations.o\n\n… [+6031 more chars]",
  "content_hash": "fcb59355a9bad9d899a972f805d3506fb6ecc0cfc74a66aad67ba538a03d2714",
  "token_count": 1492,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    48,
    51
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `e4c7ea4d-9405-5fe5-99d5-b22571a0030e`

- vector: dim=3072 · [-0.0423, 0.0206, -0.0213, -0.0024, -0.0287, -0.0008, 0.0110, 0.0330, …]

```json
{
  "chunk_id": "e4c7ea4d-9405-5fe5-99d5-b22571a0030e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "(http://www.openaccessweek.org/page/about)\n4. Librarian should educate the users by proving links of various useful open access\nresources on the library website.  Librarian should assist in payment of author's fees to\npublish in open access journals.\nReferences \n1.\nhttp://www.budapestopenaccessinitiative.org/ Accessed on 18/3/2018\n2.\nSuber, Peter. \"Open Access Overview\" Archived2007-05-19 at the Wayback Machine.. Earlham.edu. \nRetrieved on 17/3/2018.  http://legacy.earlham.edu/~peters/fos/overview.htm \n3.\nhttps://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018\n\n\n… [+78 more chars]",
  "content_hash": "a5bfac6f45dd9c01e4f084f9c99ab6e1de62e5167cc8a1ee6bd44df224c92107",
  "token_count": 187,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e15ad54b-9c1b-51bc-af52-8eafaf883881",
  "chunk_index": 49,
  "page_number": 48,
  "page_range": [
    48,
    48
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4ad6c7fd-9728-58ad-84ce-7fa4915bfe2f`

- vector: dim=3072 · [-0.0494, 0.0546, -0.0113, 0.0045, -0.0325, 0.0130, -0.0020, 0.0226, …]

```json
{
  "chunk_id": "4ad6c7fd-9728-58ad-84ce-7fa4915bfe2f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "section_type": "references",
  "chunk_text": ".edu/~peters/fos/overview.htm \n3.\nhttps://www.opensocietyfoundations.org/explainers/what-open-access Accessed on 18/3/2018\n4.\nhttp://wordpress.openoasis.org/promoting-open-access/ accessed on 24/5/2018 ICDL 2019: Poster \n8.\nJain, Priti, \"Promoting Open Access to Research in Academic Libraries\" (2012). Library Philosophy and\nPractice (e-journal). 737. http://digitalcommons.unl.edu/libphilprac/737\n9.\nGiarlo, M.J. (2005). The impact of open access on academic libraries. Available:\nhttp://lackoftalent.org/michael/papers/532.pdf\n10. Cryer, E., & Collins, M. (2011). Incorporating Open Access into Li\n\n… [+615 more chars]",
  "content_hash": "bf34aed522f9d55dcd39a6a9e946efa8361a439f8cf14ac630b242d6c3a6c67a",
  "token_count": 349,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e15ad54b-9c1b-51bc-af52-8eafaf883881",
  "chunk_index": 50,
  "page_number": 49,
  "page_range": [
    49,
    49
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7d2ff532-b4b1-58c0-8ec9-4020d9816735`

- vector: dim=3072 · [-0.0164, 0.0192, -0.0020, 0.0029, 0.0048, 0.0149, -0.0257, -0.0123, …]

```json
{
  "chunk_id": "7d2ff532-b4b1-58c0-8ec9-4020d9816735",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "Kelem Kassahun and Chatiwa Nsala (2015). The awareness of academic librarians towards Open Access\nresources to support reference services: A case of private institutions of higher learning in Gaborone,\nBotswana  Conference paper IFLA Conference 2015\n27 ICDL 2019: Poster \nSecurity and Safety issues in Libraries with \nspecial reference to Disaster Management \nAnam Jamal  \nJunior Research Fellow (JRF), Dept. of Library and Information Science, Aligarh Muslim \nUniversity, Aligarh, India \nP.M  Naushad Ali\nProfessor, Dept. of Library and Information Science, Aligarh Muslim University, Aligarh, India\n\n… [+1764 more chars]",
  "content_hash": "51eec83dab645811c4c8f820864ffe9bfd24b44c938df5b04cd016fffebe4389",
  "token_count": 490,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e15ad54b-9c1b-51bc-af52-8eafaf883881",
  "chunk_index": 51,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1ed0c484-8c76-54fb-afc2-5e69954a158d`

- vector: dim=3072 · [-0.0054, -0.0002, -0.0091, 0.0061, 0.0334, -0.0064, -0.0341, -0.0049, …]

```json
{
  "chunk_id": "1ed0c484-8c76-54fb-afc2-5e69954a158d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "It \nexplores the reasons and methods of theft, mutilation, and mutilation of library materials along \nwith the preparedness for natural disasters such as fire, flood, and earthquake. For this purpose, \nthe survey research method was employed, and two sets of questionnaires were constructed for the collection of data from the users and librarians of the above-said libraries. The paper also \nexplores the data security measures taken by both libraries. The result of the analysis revealed \nthat  akin to other libraries, these two libraries are also facing security issues such as the problem \nof th\n\n… [+339 more chars]",
  "content_hash": "19adbbf0ef657831cd60be0fce192f493ad430fe458a73d2e0fcec82121873ba",
  "token_count": 192,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e15ad54b-9c1b-51bc-af52-8eafaf883881",
  "chunk_index": 52,
  "page_number": 50,
  "page_range": [
    50,
    50
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `96e01d2c-99b3-58d5-bf3f-9e3d98b59620`

- vector: dim=3072 · [-0.0161, 0.0044, -0.0149, -0.0119, 0.0298, -0.0170, -0.0452, -0.0122, …]

```json
{
  "chunk_id": "96e01d2c-99b3-58d5-bf3f-9e3d98b59620",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "Some suggestions are also be proffered for the security of the collection  \nincluding E-resources and buildings of both libraries. \n28 ICDL 2019: Poster \nIs Science Built on False Claim: An Analysis of \nCitation Dependency of Scientific Literature on \nRetracted Article \nRosy Jan \nSr. Assistant Professor, Department of Library and Information Science, University of Kashmir, \nIndia.      \nSabha Ali \nFaculty, Department of Library and Information Science, University of Kashmir, India.   \nIrfan ul haq \nFaculty, Department of Library and Information Science, University of Kashmir, India. \nAbstract \n\n… [+1659 more chars]",
  "content_hash": "b4954739fc659cbc3e458f8549e67419335dc74fae66d2bf11ba663d34513427",
  "token_count": 467,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e15ad54b-9c1b-51bc-af52-8eafaf883881",
  "chunk_index": 53,
  "page_number": 51,
  "page_range": [
    51,
    51
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `08efc458-bcf0-5dba-bdc3-419033c91188`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "08efc458-bcf0-5dba-bdc3-419033c91188",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "3. Library should start promoting Open Access Weeks (cont.)\n\nICDL 2019: Poster \nethics, misbehavior or fraud in research and it has been revealed the main reason for such cause \nis the lack of dedication and honesty of researchers/scientists towards their research. Scientific \nfraud can take place with the emergence of various undesirable practices such as plagiarism, \nfalsification of results, data inconsistency, image duplication and compromised peer review etc. \nMoreover, the identification of research misconduct in a research article leads to its retraction \n(Greitemeyer, 2014). Retraction\n\n… [+6660 more chars]",
  "content_hash": "d85704bcd10a7575a97620119eaf35bf9e22702ecb95e3faac296e3fee806cdf",
  "token_count": 1668,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    52,
    54
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `107d1988-9fbd-549a-b6c7-524576b8f780`

- vector: dim=3072 · [-0.0199, -0.0008, -0.0170, -0.0342, 0.0473, -0.0072, -0.0450, -0.0012, …]

```json
{
  "chunk_id": "107d1988-9fbd-549a-b6c7-524576b8f780",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "ICDL 2019: Poster \nethics, misbehavior or fraud in research and it has been revealed the main reason for such cause \nis the lack of dedication and honesty of researchers/scientists towards their research. Scientific \nfraud can take place with the emergence of various undesirable practices such as plagiarism, \nfalsification of results, data inconsistency, image duplication and compromised peer review etc. \nMoreover, the identification of research misconduct in a research article leads to its retraction \n(Greitemeyer, 2014). Retraction of an article can take many years from the time of its \npubl\n\n… [+1403 more chars]",
  "content_hash": "7107402df286af883ff15569c8c6020af8af0995afb827b851cd333b23b56c41",
  "token_count": 449,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08efc458-bcf0-5dba-bdc3-419033c91188",
  "chunk_index": 54,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cd8ce2d9-3f09-5e69-b08a-6afdc52e8514`

- vector: dim=3072 · [-0.0226, 0.0237, -0.0168, -0.0105, 0.0659, -0.0206, -0.0152, -0.0065, …]

```json
{
  "chunk_id": "cd8ce2d9-3f09-5e69-b08a-6afdc52e8514",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "Number of problems arises when researchers favorably cite an \nerroneous article. Citations to erroneous paper make such papers credible. Finally, a researcher \nprompted by the invalid point may incorporate it in his writings and becomes a means for propagation of an error (Cor & Sood, 2017). Thus it is necessary to study and showcase the \nproblem in more explicit form. It is important to find out the extent to which retracted articles are \ninterwoven with the rest of the scientific literature. More importantly how such flawed literature \nis firmly entrenched in co-citation networks. The study \n\n… [+983 more chars]",
  "content_hash": "da322bb01de7b5137b536639dece5cec2c378f14288ba2b458bb720ff898d7b1",
  "token_count": 343,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08efc458-bcf0-5dba-bdc3-419033c91188",
  "chunk_index": 55,
  "page_number": 52,
  "page_range": [
    52,
    52
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7ff701b8-a443-57b6-ac61-ba64c756ca34`

- vector: dim=3072 · [-0.0027, 0.0348, -0.0197, -0.0112, 0.0536, -0.0228, 0.0050, -0.0073, …]

```json
{
  "chunk_id": "7ff701b8-a443-57b6-ac61-ba64c756ca34",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "Scope \nThe scope of study is confined to one of the retracted article “Visfatin: A protein secreted by \nvisceral fat that mimics the effects of insulin” \n30 ICDL 2019: Poster \nMethodology \nList of highly cited retracted articles were retrieved using “Retraction Watch”, devoted to the \nexamination of retracted articles as “a window into scientific process”. One the highly cited \nretracted article list on retraction watch was selected for analysis and examination in terms of \nnetworks visualization of citations using VOS viewer. The retracted article was searched in Web \nof Science (WoS) and a t\n\n… [+1373 more chars]",
  "content_hash": "ef5b580503ccfa9af71bb750e09b14fc3044d2f960a8ed7ad6d505a805b3335f",
  "token_count": 486,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08efc458-bcf0-5dba-bdc3-419033c91188",
  "chunk_index": 56,
  "page_number": 53,
  "page_range": [
    53,
    53
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2eb06059-643e-5f1c-bde4-418b5390425b`

- vector: dim=3072 · [-0.0150, 0.0334, -0.0130, -0.0041, 0.0410, -0.0161, 0.0054, -0.0010, …]

```json
{
  "chunk_id": "2eb06059-643e-5f1c-bde4-418b5390425b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "The graphical representation of large bibliometric maps can be much enhanced by means of zoom functionality, special labeling algorithms, and density metaphors. However, \nsuch kind of functionality is not integrated into the computer programs, frequently used by \nbibliometric researchers. The requirement was fulfilled by the software introduced by (Van & \nWaltman, 2009), the program is used for bibliometric mapping. This program pays special \nattention to the graphical representation of bibliometric maps. VOSviewer, where VOS stands \nfor visualization of similarities is a program developed for\n\n… [+723 more chars]",
  "content_hash": "a7363ca72cde1bbf93b3539579766ecca9440ece8ef1d256229d85b2efc481b6",
  "token_count": 291,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08efc458-bcf0-5dba-bdc3-419033c91188",
  "chunk_index": 57,
  "page_number": 53,
  "page_range": [
    53,
    53
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `b7099f77-88dc-57c5-b8bb-7cd32c61a245`

- vector: dim=3072 · [-0.0061, -0.0069, -0.0139, -0.0024, 0.0142, -0.0076, -0.0040, 0.0008, …]

```json
{
  "chunk_id": "b7099f77-88dc-57c5-b8bb-7cd32c61a245",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "3. Library should start promoting Open Access Weeks",
  "chunk_text": "The article was retracted since the authors have \nbeen unable to reproduce some of the reported spontaneous transformation events and suspect \nthe phenomenon is due to a cross-contamination artifact. However, the retracted article is cited \ncontinuously in the literature. \n31 ICDL 2019: Poster \nTable 1:  Citations Received by the article Before and After Retraction \n*Citations received by article as on July 2019\nTable 1 lists citation to retracted article. It was observed that out 1302 citations, 228 citations are \nreceived before the article is retracted and 1074 citations are received by the\n\n… [+469 more chars]",
  "content_hash": "17e15ae14af16fd7c28547ebe6e8774948e9128ceb9af57b572e5c70470b992f",
  "token_count": 236,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08efc458-bcf0-5dba-bdc3-419033c91188",
  "chunk_index": 58,
  "page_number": 54,
  "page_range": [
    54,
    54
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `ba5fb477-e62a-5766-85f0-d842b472d322`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ba5fb477-e62a-5766-85f0-d842b472d322",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles\n\nbefore \nretraction \nCiting \nArticles \nafter \nretraction \nTotal cites \nin Web of \nScience \n“Visfatin: \nA protein \nsecreted by \nvisceral fat \nthat \nmimics the \neffects of \ninsulin” \nFukuhara A, Matsuda M, \nNishizawa M, Segawa K, \nTanaka M, Kishimoto K, \nMatsuki Y, Murakami M, \nIchisaka T, Murakami H, \nWatanabe E, Takagi T, \nAkiyoshi M, Ohtsubo T, \nKihara S, Yamashita S, \nMakishima M, Funahashi \nT, Yamanaka S, \nHiramatsu R, Matsuzawa \nY, Shimomura I. \nJournal of Clinical Endocrinology & Metabolism \n20 \n3 \nMetabolism Clinical and Experimental \nHormone and Met\n\n… [+7183 more chars]",
  "content_hash": "42d8b762d4de815552a2a20eb994ef337b171593696f039d6846b112540b6166",
  "token_count": 1914,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    54,
    59
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `f5653f73-f858-5f9b-b367-01eeecfc02e2`

- vector: dim=3072 · [0.0201, 0.0157, -0.0118, -0.0124, 0.0526, -0.0135, -0.0032, 0.0032, …]

```json
{
  "chunk_id": "f5653f73-f858-5f9b-b367-01eeecfc02e2",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "before \nretraction \nCiting \nArticles \nafter \nretraction \nTotal cites \nin Web of \nScience \n“Visfatin: \nA protein \nsecreted by \nvisceral fat \nthat \nmimics the \neffects of \ninsulin” \nFukuhara A, Matsuda M, \nNishizawa M, Segawa K, \nTanaka M, Kishimoto K, \nMatsuki Y, Murakami M, \nIchisaka T, Murakami H, \nWatanabe E, Takagi T, \nAkiyoshi M, Ohtsubo T, \nKihara S, Yamashita S, \nMakishima M, Funahashi \nT, Yamanaka S, \nHiramatsu R, Matsuzawa \nY, Shimomura I. \nJournal of Clinical Endocrinology & Metabolism \n20 \n3 \nMetabolism Clinical and Experimental \nHormone and Metabolic Research \n13 \n7 \nJournal of Endo\n\n… [+604 more chars]",
  "content_hash": "3f05f9a8bfe266ad584249c8c099f7614464e2762258abc7fe19003dbc72b92d",
  "token_count": 348,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ba5fb477-e62a-5766-85f0-d842b472d322",
  "chunk_index": 59,
  "page_number": 54,
  "page_range": [
    54,
    55
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cbd07bb2-1522-52d2-adec-07b7ab914144`

- vector: dim=3072 · [0.0155, 0.0086, -0.0142, 0.0119, 0.0443, -0.0506, -0.0162, 0.0042, …]

```json
{
  "chunk_id": "cbd07bb2-1522-52d2-adec-07b7ab914144",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Construction & Visualization of Bibliometric Maps of data\n\nFig.1a: Bibliographic coupling of  Sources/Journals\n\nFig.1b:  Bibliographic coupling of  Sources  in  cluster View with left hand side and bottom  \npanel  providing details about clusters and link strength \n33 ICDL 2019: Poster \nThe above network visualization map shows bibliographic coupling patterns of the 100 citing \njournals of selected retracted article. Bibliographic coupling network includes the journals with \nthe largest number of bibliographic coupling links. The distance between two journals in the \nvisualization approximatel\n\n… [+1240 more chars]",
  "content_hash": "a0e86964bb8d56eff1ceb0117a0e987991bbd9a4b7f2b3318e6e5defa35c2d20",
  "token_count": 411,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ba5fb477-e62a-5766-85f0-d842b472d322",
  "chunk_index": 60,
  "page_number": 56,
  "page_range": [
    56,
    56
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `683ce385-8b66-5f46-9d02-7ab8384e07b4`

- vector: dim=3072 · [-0.0021, 0.0275, -0.0190, -0.0143, 0.0505, -0.0445, -0.0173, 0.0091, …]

```json
{
  "chunk_id": "683ce385-8b66-5f46-9d02-7ab8384e07b4",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "The data could be further \nverified and analyzed through the following screenshots captures in the VOSviewer. \n34 ICDL 2019: Poster \nFig.2a Cluster view of Citations and Total Link Strength of Cited References as Visualized \nthrough VOSviewer.\n The network visualization represented in fig. 2b represents the data set of cited references of the \nretracted article and chain of citation links of the cited references. It is divided into four clusters. \nCluster 1 represented in red is the biggest cluster with a total of 323 items linked followed by \ncluster 2 represented in green containing 136 item\n\n… [+1086 more chars]",
  "content_hash": "3e6a64a62ccee38849f3912cd4bdd7d26397c118986dc802de565b01c68ca899",
  "token_count": 376,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ba5fb477-e62a-5766-85f0-d842b472d322",
  "chunk_index": 61,
  "page_number": 57,
  "page_range": [
    57,
    58
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c7baa8d5-aa0d-55db-acb9-ec148c664192`

- vector: dim=3072 · [0.0072, -0.0098, -0.0193, -0.0092, 0.0471, -0.0231, -0.0259, -0.0065, …]

```json
{
  "chunk_id": "c7baa8d5-aa0d-55db-acb9-ec148c664192",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "9: Poster \nFig.2b Network visualization of Bibliographic coupling and co-citation of retracted article \nVisfatin: A protein secreted by visceral fat that mimics the effects of insulin”  published in  Science in 2005 \nby Fukuhara, A \n36 ICDL 2019: Poster \nDiscussion and Conclusion \nOur study aims to raise the awareness of the increasing prevalence of citations to retracted article \nby showcasing how retracted article is cited hundreds of times in the scientific literature. \nVisualizations of co-citation networks of the selected retracted article demonstrate that it is \ndeeply interwove with the\n\n… [+1699 more chars]",
  "content_hash": "6160a801ea65563b1d123d6404128797239d530909e3416edb05444c554156af",
  "token_count": 491,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ba5fb477-e62a-5766-85f0-d842b472d322",
  "chunk_index": 62,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `9218328b-33c5-5121-8b97-dd553df39ffa`

- vector: dim=3072 · [-0.0072, -0.0165, -0.0217, 0.0054, 0.0306, -0.0273, -0.0196, 0.0103, …]

```json
{
  "chunk_id": "9218328b-33c5-5121-8b97-dd553df39ffa",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Boyack, K.W., Klavans, R., & Börner, K. (2005). Mapping the backbone of science. Scientometrics, 64(3),\n351–374.\n3. Budd, J. M., Sievert, M., & Schultz, T. R. (1999). Phenomena of retraction: reasons for retraction and\ncitations to the publications. Jama, 280(3), 296-297.\n4.\nChen, C., Hu, Z., Milbank, J., & Schultz, T. (2013). A visual analytic study of retracted articles in scientific\nliterature. Journal of the American Society for Information Science and Technology, 64(2), 234-253.\n5.\nCor, K., & Sood, G. Propagation of Error: Approving Citations to Problematic Research.\n6.\nDa Silva, J. A. T.\n\n… [+843 more chars]",
  "content_hash": "ace3500cf834f2ea20fc96fa4c6c3f3198d5e21b6a86b9dc120d215901ac7221",
  "token_count": 462,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ba5fb477-e62a-5766-85f0-d842b472d322",
  "chunk_index": 63,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `159171ad-d48e-51dd-827b-2458382c8261`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "159171ad-d48e-51dd-827b-2458382c8261",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\n| References |  |\n| --- | --- |\n| 1. | Börner, K., Chen, C., & Boyack, K. W. (2003). Visualizing knowledge domains. Annual Review of |\n|  | Information Science and Technology, 37(1), 179–255. |\n| 2. | Boyack, K.W., Klavans, R., & Börner, K. (2005). Mapping the backbone of science. Scientometrics, 64(3), |\n|  | 351–374. |\n| 3. | Budd, J. M., Sievert, M., & Schultz, T. R. (1999). Phenomena of retraction: reasons for retraction and |\n|  | citations to the publications. Jama, 280(3), 296-297. |\n| 4. | Chen, C., Hu, Z., Milbank, J., & Schultz, T. (2013\n\n… [+4373 more chars]",
  "content_hash": "70c27d503b6eca7c1398d5ad3cafc13bf78e619949945e65b53f04afc5309aef",
  "token_count": 1604,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    59,
    60
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `89f2e87b-59ff-5663-aa54-04dfa9fc8ed0`

- vector: dim=3072 · [0.0142, -0.0022, -0.0208, 0.0118, 0.0390, -0.0342, -0.0010, 0.0057, …]

```json
{
  "chunk_id": "89f2e87b-59ff-5663-aa54-04dfa9fc8ed0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "| References |  |\n| --- | --- |\n| 1. | Börner, K., Chen, C., & Boyack, K. W. (2003). Visualizing knowledge domains. Annual Review of |\n|  | Information Science and Technology, 37(1), 179–255. |\n| 2. | Boyack, K.W., Klavans, R., & Börner, K. (2005). Mapping the backbone of science. Scientometrics, 64(3), |\n|  | 351–374. |\n| 3. | Budd, J. M., Sievert, M., & Schultz, T. R. (1999). Phenomena of retraction: reasons for retraction and |\n|  | citations to the publications. Jama, 280(3), 296-297. |\n| 4. | Chen, C., Hu, Z., Milbank, J., & Schultz, T. (2013). A visual analytic study of retracted article\n\n… [+1027 more chars]",
  "content_hash": "2c7fc61c18d9f0ceebfbe2a26e4f80878a9766bb24fa8247c6deb8a59d05d2f8",
  "token_count": 542,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "159171ad-d48e-51dd-827b-2458382c8261",
  "chunk_index": 64,
  "page_number": 59,
  "page_range": [
    59,
    59
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `524383ec-9662-56b8-845d-e97868f8a770`

- vector: dim=3072 · [-0.0227, 0.0118, -0.0203, 0.0017, 0.0131, -0.0209, -0.0230, 0.0261, …]

```json
{
  "chunk_id": "524383ec-9662-56b8-845d-e97868f8a770",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "(2014). Unwrapping “impact” for evaluation: A co-word analysis |\n|  | of the UK REF2014 policy documents using VOSviewer. In Proceedings of the science and technology |\n|  | indicators conference (pp. 145-154). | |  | 10. Fang, F. C., & Casadevall, A. (2011). Retracted science and the retraction index. Infection and immunity, |\n|  | IAI-05661. |\n\nICDL 2019: Poster \n11. Fang, F. C., Steen, R. G., & Casadevall, A. (2012). Misconduct accounts for the majority of retracted\nscientific publications. Proceedings of the National Academy of Sciences, 109(42), 17028-17033.\n12. Greitemeyer, T. (2014). Ar\n\n… [+1125 more chars]",
  "content_hash": "2d764e81d1b0f399cf470a9d57d9eb259fd972666408449ad60125c7d859fed8",
  "token_count": 542,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "159171ad-d48e-51dd-827b-2458382c8261",
  "chunk_index": 65,
  "page_number": 59,
  "page_range": [
    59,
    60
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d9c66573-6f9a-5c8b-86ba-d38d766545a3`

- vector: dim=3072 · [-0.0060, -0.0111, -0.0235, 0.0025, 0.0310, 0.0046, -0.0316, 0.0102, …]

```json
{
  "chunk_id": "d9c66573-6f9a-5c8b-86ba-d38d766545a3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "Moylan, E. C., & Kowalczuk, M. K. (2016). Why articles are retracted: A retrospective cross-sectional\nstudy of retraction notices at BioMed Central. British Medical Journal Open, 6(11), e012047. 20. Neale AV, Northrup J, Dailey R, Marks E, Abrams J. (2007).Correction and use of biomedical literature\naffected by scientific misconduct. Sci Eng Ethics. Mar; 13(1): p. 5-24\n21. Redman, B. K., Yarandi, H. N., & Merz, J. F. (2008). Empirical developments in retraction. Journal of\nMedical Ethics, 34(11), 807-809.\n22. Sangam, S. L., & Mogali, M. S. S.(2012). Mapping and Visualization Softwares tools: a\n\n… [+941 more chars]",
  "content_hash": "bf6be6b12a5263b3e9551b31bf5da95a865a01615decf0e4a22bc37d403f8eae",
  "token_count": 483,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "159171ad-d48e-51dd-827b-2458382c8261",
  "chunk_index": 66,
  "page_number": 60,
  "page_range": [
    60,
    60
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c0ff9b74-88f6-5277-a8c6-55bb92f76f7c`

- vector: dim=3072 · [-0.0051, -0.0048, -0.0302, -0.0006, -0.0009, 0.0018, 0.0155, 0.0282, …]

```json
{
  "chunk_id": "c0ff9b74-88f6-5277-a8c6-55bb92f76f7c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "Van Eck, N. J., Waltman, L., Van den Berg, J., & Kaymak, U. (2006). Visualizing the computational\nintelligence field. IEEE Computational Intelligence Magazine, 1(4), 6–10. 29. Van Noorden, R. (2011). The trouble with retractions. Nature, 478(7367), 26.\n30. Van Noorden, R. (2011). The trouble with retractions. Nature, 478(7367), 26.\n31. Waltman, L. (2017). Citation-based clustering of publications using CitNetExplorer and\nVOSviewer. Scientometrics, 111(2), 1053-1070.\n32. Waltman, L. (2017). Citation-based clustering of publications using CitNetExplorer and\nVOSviewer. Scientometrics, 111(2), 105\n\n… [+10 more chars]",
  "content_hash": "11f6d24fc63bfb14caeac924e350dfc963ad96ae33ddc12aa5e389237ac620a6",
  "token_count": 193,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "159171ad-d48e-51dd-827b-2458382c8261",
  "chunk_index": 67,
  "page_number": 60,
  "page_range": [
    60,
    60
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `4dcaf92c-02bf-50e9-a8ea-fd9df8c52fc2`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4dcaf92c-02bf-50e9-a8ea-fd9df8c52fc2",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\n| ICDL 2019: Poster |  |\n| --- | --- |\n|  | 11. Fang, F. C., Steen, R. G., & Casadevall, A. (2012). Misconduct accounts for the majority of retracted |\n|  | scientific publications. Proceedings of the National Academy of Sciences, 109(42), 17028-17033. |\n|  | 12. Greitemeyer, T. (2014). Article retracted, but the message lives on. Psychonomic bulletin & review, 21(2), |\n|  | 557-561. |\n|  | 13. Grieneisen, M. L., & Zhang, M. (2012). A comprehensive survey of retracted articles from the scholarly |\n|  | literature. PLoS ONE, 7, e44118. |\n| 14. | Io\n\n… [+6702 more chars]",
  "content_hash": "0b28362b36e1ae87eac63357beb36beef3399a8f9afb3b3bf2a3585c8171db4e",
  "token_count": 1956,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    60,
    62
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ce26214d-9deb-5838-aa1c-ba5881b884a2`

- vector: dim=3072 · [0.0005, -0.0130, -0.0104, -0.0086, 0.0222, -0.0374, -0.0212, 0.0217, …]

```json
{
  "chunk_id": "ce26214d-9deb-5838-aa1c-ba5881b884a2",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "| ICDL 2019: Poster |  |\n| --- | --- |\n|  | 11. Fang, F. C., Steen, R. G., & Casadevall, A. (2012). Misconduct accounts for the majority of retracted |\n|  | scientific publications. Proceedings of the National Academy of Sciences, 109(42), 17028-17033. |\n|  | 12. Greitemeyer, T. (2014). Article retracted, but the message lives on. Psychonomic bulletin & review, 21(2), |\n|  | 557-561. |\n|  | 13. Grieneisen, M. L., & Zhang, M. (2012). A comprehensive survey of retracted articles from the scholarly |\n|  | literature. PLoS ONE, 7, e44118. |\n| 14. | Ioannidis, J. P., Klavans, R., & Boyack, K. W. (2\n\n… [+1027 more chars]",
  "content_hash": "b58699849e38b26aa289440e7df8d39479ffa15104e58fdff872ca3e5e6ad985",
  "token_count": 547,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4dcaf92c-02bf-50e9-a8ea-fd9df8c52fc2",
  "chunk_index": 68,
  "page_number": 60,
  "page_range": [
    60,
    60
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `37f32570-77e4-5750-b7dd-31e756364b40`

- vector: dim=3072 · [0.0010, -0.0031, -0.0156, -0.0041, 0.0358, -0.0159, -0.0266, 0.0188, …]

```json
{
  "chunk_id": "37f32570-77e4-5750-b7dd-31e756364b40",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "British Medical Journal Open, 6(11), e012047. |\n|  | 20. Neale AV, Northrup J, Dailey R, Marks E, Abrams J. (2007).Correction and use of biomedical literature | |  | affected by scientific misconduct. Sci Eng Ethics. Mar; 13(1): p. 5-24 |\n|  | 21. Redman, B. K., Yarandi, H. N., & Merz, J. F. (2008). Empirical developments in retraction. Journal of |\n|  | Medical Ethics, 34(11), 807-809. |\n|  | 22. Sangam, S. L., & Mogali, M. S. S.(2012). Mapping and Visualization Softwares tools: a review. |\n|  | 23. Steen, R. G. (2011). Retractions in the scientific literature: is the incidence of research fr\n\n… [+1187 more chars]",
  "content_hash": "a95a7678ad0324e22cb6162bbadb25a71f7f3b4b51c584613f0c6e02c0072873",
  "token_count": 599,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4dcaf92c-02bf-50e9-a8ea-fd9df8c52fc2",
  "chunk_index": 69,
  "page_number": 60,
  "page_range": [
    60,
    60
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6044d05d-3243-5f4e-b32d-15e17c01c02f`

- vector: dim=3072 · [-0.0155, -0.0036, -0.0112, -0.0130, 0.0344, -0.0246, -0.0219, 0.0182, …]

```json
{
  "chunk_id": "6044d05d-3243-5f4e-b32d-15e17c01c02f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Van Noorden, R. (2011). The trouble with retractions. Nature, 478(7367), 26. |\n|  | 31. Waltman, L. (2017). Citation-based clustering of publications using CitNetExplorer and | |  | VOSviewer. Scientometrics, 111(2), 1053-1070. |\n|  | 32. Waltman, L. (2017). Citation-based clustering of publications using CitNetExplorer and |\n|  | VOSviewer. Scientometrics, 111(2), 1053-1070. |\n\nICDL 2019: Poster \nWas Beall’s List of predatory Journals worth \nDisappearing?  \nRosy Jan  \nSr. Assistant Professor, Deptt. of Library and Information Science, University of Kashmir, India \nSumeer Gul  \nSr. Assistant P\n\n… [+1125 more chars]",
  "content_hash": "ef5dacaf00b513c4aae3f70f7b295a8f6346aee78a3215ab61e33509676bce2e",
  "token_count": 405,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4dcaf92c-02bf-50e9-a8ea-fd9df8c52fc2",
  "chunk_index": 70,
  "page_number": 60,
  "page_range": [
    60,
    61
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `f3dcd3d3-e5e1-57ca-bcd2-fa1bdc0297a3`

- vector: dim=3072 · [-0.0337, -0.0127, -0.0126, -0.0351, 0.0247, -0.0245, -0.0215, -0.0061, …]

```json
{
  "chunk_id": "f3dcd3d3-e5e1-57ca-bcd2-fa1bdc0297a3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "The paper is a discourse on the 56 characteristics list by \nBeall as guidelines for Determining Predatory Open-Access Publishers and journals. \n39 ICDL 2019: Poster \nPredatory Publishing or Quality Research: Which \nis Bigger Challenge for India \nRosy Jan  \nSr. Assistant Professor, Deptt. of Library and Information Science, University of Kashmir,India \nSumeer Gul \nSr. Assistant Professor, Deptt. of Library and Information Science, University of Kashmir, India \nAbstract \nInternational Consortium of Investigative Journalists initiated an investigation on predatory \njournals and found India as one\n\n… [+1998 more chars]",
  "content_hash": "ce7bc942faf882e21b67f78f8ce919895c61548670dff43d190b2a02f197069d",
  "token_count": 529,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4dcaf92c-02bf-50e9-a8ea-fd9df8c52fc2",
  "chunk_index": 71,
  "page_number": 62,
  "page_range": [
    62,
    62
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `975f042b-78df-519c-8356-d51680a17812`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "975f042b-78df-519c-8356-d51680a17812",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \ndebate around such journals, and the term ‘predatory’ has become the standard way to describe \nthem. Indeed, the closure of his website has generated considerable consternation. In this \nframing, Beall is treated as the lone bulwark against the tide of predatory journals that would \notherwise overrun academics. Although the term, and its variants such as “predatory journals”, is \nwidely used, they have been criticized. One problem is that the term predator may cover a \nspectrum of organizations, business activities and publicati\n\n… [+6570 more chars]",
  "content_hash": "c8678dc15fad5c881eba112fb051ed60e59b4d16e1c0d61e026e45b0b7e5330a",
  "token_count": 1549,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    63,
    64
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `dd7632f7-4b67-5c76-8446-672331e35163`

- vector: dim=3072 · [-0.0144, 0.0133, -0.0259, -0.0425, 0.0355, 0.0017, -0.0109, -0.0050, …]

```json
{
  "chunk_id": "dd7632f7-4b67-5c76-8446-672331e35163",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ICDL 2019: Poster \ndebate around such journals, and the term ‘predatory’ has become the standard way to describe \nthem. Indeed, the closure of his website has generated considerable consternation. In this \nframing, Beall is treated as the lone bulwark against the tide of predatory journals that would \notherwise overrun academics. Although the term, and its variants such as “predatory journals”, is \nwidely used, they have been criticized. One problem is that the term predator may cover a \nspectrum of organizations, business activities and publications ranging from the amateurish but \ngenuine to\n\n… [+1609 more chars]",
  "content_hash": "f975af5b65e59f6c2c00ec2e8d86a1f4cfbcb2380785130e7af3598ab596bd2c",
  "token_count": 438,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "975f042b-78df-519c-8356-d51680a17812",
  "chunk_index": 72,
  "page_number": 63,
  "page_range": [
    63,
    63
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `bf053c24-39e1-538e-bc3c-a7b42508d63f`

- vector: dim=3072 · [-0.0556, -0.0142, -0.0133, -0.0517, 0.0233, 0.0167, 0.0035, -0.0275, …]

```json
{
  "chunk_id": "bf053c24-39e1-538e-bc3c-a7b42508d63f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Xia \net al (2015) noted that those who published in predatory journals were mainly “young and \ninexperienced researchers from developing countries. Others have noted that non-native English \nspeakers are more likely to be taken in by predatory websites. However, Indian is ranked as highest contributor in predatory journals. The problem is directly connected with the \ndissatisfactory Indian academic research system and unrealistic performance measures for \nselection, promotions, and other similar benefits which enhance the incentive to cheat. The \nproblem of publishing in such cheat outlets is \n\n… [+798 more chars]",
  "content_hash": "cf3d14780fb85ce13d6d4189d54a084bece3d4fe33e2220c02472ea32f83fca8",
  "token_count": 269,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "975f042b-78df-519c-8356-d51680a17812",
  "chunk_index": 73,
  "page_number": 63,
  "page_range": [
    63,
    63
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `46f644b6-4edf-515b-b355-ee2a301236a6`

- vector: dim=3072 · [-0.0353, -0.0129, -0.0116, -0.0468, 0.0261, 0.0172, -0.0108, 0.0071, …]

```json
{
  "chunk_id": "46f644b6-4edf-515b-b355-ee2a301236a6",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "into Indian Academia \nTaken advantage of the Internet technology, the open access movement, and the needs of young, \ninexperienced, or incompetent researchers for scholarly publications avaricious individuals and \npublishers created shoddy websites where authors might be enticed to publish because of lax \n41 ICDL 2019: Poster \nreview, if any, and promised fast printing. It has a negative impact on OA publishing in \nparticular and on scholarly communication in general. Predatory publishing are often \nunprofessional and lack quality control, it has many attributes that make it different from \npr\n\n… [+1486 more chars]",
  "content_hash": "e5b1b89f4b4c8cbc9a83a7cc6eef84e0f30380a80855efe5623546e5e23613ce",
  "token_count": 493,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "975f042b-78df-519c-8356-d51680a17812",
  "chunk_index": 74,
  "page_number": 64,
  "page_range": [
    64,
    64
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6d197e72-58da-5cba-8b62-63a474d6b84d`

- vector: dim=3072 · [-0.0196, -0.0049, -0.0160, -0.0408, 0.0217, -0.0149, -0.0025, -0.0125, …]

```json
{
  "chunk_id": "6d197e72-58da-5cba-8b62-63a474d6b84d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "These two lists were suddenly taken \ndown in January of 2017 for unknown reasons, which shocked the media and scholarly community (Chawla, 2017; Silver, 2017). However, the Internet archive site Web Archive has \npreserved the lists, including all of their update history since the first publication of both lists. \nBeall’s list include most of the predatory journals emerged from India. As indicated by many \nstudied most often Indian academicians and researchers submit in the predatory journals. The \nprosperity of such journal publishing in developing nations reflects an imbalanced supply-\ndemand\n\n… [+1538 more chars]",
  "content_hash": "1121919f83cad68d766b5992e1a76c0a8f7ed325105f01cb7bf640275eadef3b",
  "token_count": 478,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "975f042b-78df-519c-8356-d51680a17812",
  "chunk_index": 75,
  "page_number": 64,
  "page_range": [
    64,
    64
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `53a8c539-840a-5737-ad9b-51e0b45e4204`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "53a8c539-840a-5737-ad9b-51e0b45e4204",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \nReasons of low quality research and the consequent submission \nof manuscripts by Indian Acedemicians in Predatory journals \nLow Quality Academic Research in India \nThe establishment of the “Indian Association for the Cultivation of Science (IACS)” in Calcutta \nin 1876, whose founder Dr. Mahendra Lal Sircar envisioned an institution for “purescience \nlearning and science-teaching” with the hope of ultimate success in research. Elsewhere, \nbeginning in late nineteenth century, Sir Jagadis Chunder Bose and Sir Prafulla Chandra Ray \n\n… [+7157 more chars]",
  "content_hash": "c18ebf73de6a0ae8902bf7d5721f02f076287c4d5fef2b5490cf4d4530837fe7",
  "token_count": 1522,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    65,
    66
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `13614ced-2b40-51f2-9efd-696e13091f85`

- vector: dim=3072 · [-0.0224, 0.0030, -0.0178, -0.0338, 0.0056, 0.0006, 0.0101, -0.0090, …]

```json
{
  "chunk_id": "13614ced-2b40-51f2-9efd-696e13091f85",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ICDL 2019: Poster \nReasons of low quality research and the consequent submission \nof manuscripts by Indian Acedemicians in Predatory journals \nLow Quality Academic Research in India \nThe establishment of the “Indian Association for the Cultivation of Science (IACS)” in Calcutta \nin 1876, whose founder Dr. Mahendra Lal Sircar envisioned an institution for “purescience \nlearning and science-teaching” with the hope of ultimate success in research. Elsewhere, \nbeginning in late nineteenth century, Sir Jagadis Chunder Bose and Sir Prafulla Chandra Ray \nconducted internationally recognized research \n\n… [+1520 more chars]",
  "content_hash": "a4e7bd8b0247dce28610f85fb034312547c18f442c5e0d8e4b75603230f8c5fc",
  "token_count": 437,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a8c539-840a-5737-ad9b-51e0b45e4204",
  "chunk_index": 76,
  "page_number": 65,
  "page_range": [
    65,
    65
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `dcd4b4d2-dc08-5d29-9af7-fbd00333a2ae`

- vector: dim=3072 · [-0.0406, 0.0255, -0.0183, -0.0011, -0.0054, -0.0113, 0.0471, -0.0134, …]

```json
{
  "chunk_id": "dcd4b4d2-dc08-5d29-9af7-fbd00333a2ae",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "He argued that the research tradition and culture in developing countries seems to be the \nbyproduct of the global framework of international capitalist relations. Academic scholars in India seem to be under pressure to create “universal knowledge” in alignment with the developed \ncountries research paradigm (Khatri,et al., 2012). That seems to have led faculty to borrow \nknowledge from western world, rather than develop it indigenously. Academic scholars in India, \nas Prof. A. Ojha of IIM Bangalore has noted (Khatri et al., 2012), seem to have limited \nconfidence and rarely assert their stand\n\n… [+1198 more chars]",
  "content_hash": "9c380f52115b1dd7082b39b71d518d26e2f26915bf5933ae96e651edb1869eea",
  "token_count": 356,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a8c539-840a-5737-ad9b-51e0b45e4204",
  "chunk_index": 77,
  "page_number": 65,
  "page_range": [
    65,
    65
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `533829fc-056b-5463-8974-50ae892f09bc`

- vector: dim=3072 · [-0.0347, 0.0142, -0.0113, 0.0046, 0.0020, -0.0079, 0.0062, -0.0119, …]

```json
{
  "chunk_id": "533829fc-056b-5463-8974-50ae892f09bc",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Further, he pointed out that academic faculty are viewed as \ngeneralists; they are expected to be superior performers in all aspects of academics (teaching, \nresearch and administration), which is unrealistic as each requires a unique competence. The lack \n43 ICDL 2019: Poster \nof research in India universities could also be attributed to the “teaching” and “training” \nemphasis, which is in keeping with the mandate given by the Government of India to provide \nquality teaching and produce quality graduates. The recruitment of faculty is also based on their \nteaching skills. The institutional me\n\n… [+1982 more chars]",
  "content_hash": "050db31bb8d139579defba93e9c931dfa1b84ed7c4593ba8a770e5c68a1348f4",
  "token_count": 490,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a8c539-840a-5737-ad9b-51e0b45e4204",
  "chunk_index": 78,
  "page_number": 66,
  "page_range": [
    66,
    66
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `752ac71b-da11-5056-ac63-edd7f2bfacd7`

- vector: dim=3072 · [-0.0373, -0.0223, -0.0090, -0.0175, -0.0041, -0.0328, 0.0061, -0.0103, …]

```json
{
  "chunk_id": "752ac71b-da11-5056-ac63-edd7f2bfacd7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Most researchers are academically trained \nto develop or validate theories/ frameworks using scientifically rigorous data analysis tools rather \nthan conducting problem solving research through application of available knowledge (Kilmann et al., 1983) this is a requirement to publish in reputed peer review, and indexed journals. \nResearchers Aspirations toward academic promotion are directly connected with the presence of \ntheir papers in such journals. More importantly fear of job lose and “publish-or-perish” is \nanother major issue equally important to competition among colleagues; desire to\n\n… [+1287 more chars]",
  "content_hash": "357b04c3f6fe2edbc0a976c18910fdb2f49df2c7a0495690a72e621a6d5361cf",
  "token_count": 343,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a8c539-840a-5737-ad9b-51e0b45e4204",
  "chunk_index": 79,
  "page_number": 66,
  "page_range": [
    66,
    66
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `0d0f3610-f1ec-527b-a8ce-487707e1f300`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "0d0f3610-f1ec-527b-a8ce-487707e1f300",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \nConsequently, the academic leaders at Indian institutions are not really successful in raising \nmoney for research projects and other related aspects. Thus, to support and uphold academic \nresearch India needs considerable improvement in this regard. But education policymaking in \nindependent India is yet to demonstrate familiarity with the complex issues that underlie highest \nlevel academics and have failed to build great research universities and institutes. \nSuggestions to create an enabling ecosystem for research to end \nth\n\n… [+6084 more chars]",
  "content_hash": "d62382e9ff123ddd4b51945fdeda1e365e19bb054da78c156026a3f52e445095",
  "token_count": 1508,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    67,
    68
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `53d544fb-2115-5e23-b8f0-d02c0a28dd8a`

- vector: dim=3072 · [-0.0492, 0.0146, -0.0231, -0.0128, 0.0028, 0.0018, -0.0058, 0.0043, …]

```json
{
  "chunk_id": "53d544fb-2115-5e23-b8f0-d02c0a28dd8a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ICDL 2019: Poster \nConsequently, the academic leaders at Indian institutions are not really successful in raising \nmoney for research projects and other related aspects. Thus, to support and uphold academic \nresearch India needs considerable improvement in this regard. But education policymaking in \nindependent India is yet to demonstrate familiarity with the complex issues that underlie highest \nlevel academics and have failed to build great research universities and institutes. \nSuggestions to create an enabling ecosystem for research to end \nthe demand and dependence on predatory publishing\n\n… [+1877 more chars]",
  "content_hash": "06540b42093887c18779f788e5ac76614d7bf78a96a1feca2286101675f55c48",
  "token_count": 441,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0d0f3610-f1ec-527b-a8ce-487707e1f300",
  "chunk_index": 80,
  "page_number": 67,
  "page_range": [
    67,
    67
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `110e9342-082a-5cad-b87b-affab80f2d95`

- vector: dim=3072 · [-0.0243, -0.0096, -0.0159, -0.0109, -0.0024, 0.0016, -0.0039, -0.0038, …]

```json
{
  "chunk_id": "110e9342-082a-5cad-b87b-affab80f2d95",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "The relevance of academic \nresearch can be enhanced by doing research in relevant areas and working collaboratively with \norganizational members to understand research findings (Mohrman, Gibson, & Mohrman, \n2001). Academic institutions need to attract faculty with research skills and aptitude and who are adequately grounded in Indian ethos and also suitably exposed to other societies and cultures. In \nthe current system, as noted by Banerjee (2013), with the approach of evaluating faculty \nmembers on research and teaching, the quality of academic output would suffer as only a small \nnumber of \n\n… [+785 more chars]",
  "content_hash": "77136003502d62ad30e0efdd1157833b470b81e9f36d09f2dd6560509edd244a",
  "token_count": 265,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0d0f3610-f1ec-527b-a8ce-487707e1f300",
  "chunk_index": 81,
  "page_number": 67,
  "page_range": [
    67,
    67
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7cc567b6-0bdf-55c1-8647-d4d1359e4217`

- vector: dim=3072 · [-0.0203, -0.0201, -0.0186, -0.0131, 0.0061, -0.0032, -0.0225, -0.0025, …]

```json
{
  "chunk_id": "7cc567b6-0bdf-55c1-8647-d4d1359e4217",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Junior scholars should seek out \npartnership with senior scholars around the world to collaborate on and co-author research. This \nwould help them publish in quality journals that would bring an end to the demand and \ndependence on the market of predatory publishing. \n45 ICDL 2019: Poster \nConclusion \nA healthy eco-system that facilitates organizationally relevant research and transformation of the \nacademic research environment and reward system, raising standards and development of true \ncollegiality both within and between institutions will help to revamp the Indian academics and \nresearch \n\n… [+1377 more chars]",
  "content_hash": "93f7396d7545fba0b9ec65027892e43d5af8445c7a95c569f845cdfdee5cd00f",
  "token_count": 475,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0d0f3610-f1ec-527b-a8ce-487707e1f300",
  "chunk_index": 82,
  "page_number": 68,
  "page_range": [
    68,
    68
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `568a586f-71a5-54ab-8373-f0acc59e45db`

- vector: dim=3072 · [-0.0183, -0.0205, -0.0173, -0.0325, 0.0171, -0.0060, 0.0044, 0.0122, …]

```json
{
  "chunk_id": "568a586f-71a5-54ab-8373-f0acc59e45db",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "Bohannon, J. (2013). Who’s afraid of peer review? Science, 342(6154), pp. 60–65. DOI:\n10.1126/science.342.6154.60.\n7. Butler, D. (2013). The dark side of publishing. Nature, 495, pp. 433–435. Retrieved from:\nhttp://www.nature.com/news/investigatingjournals-the-dark-side-of-publishing-1.12666.\n8.\nChawla, D.S. (2017). Mystery as controversial list of predatory publishers disappears. Science News,\nJanuary 17. Retrieved from: http://www.sciencemag.org/news/2017/01/mystery-controversial-list-\npredatory-publishers-disappears.\n9.\nChossudovosky, M. (1977). Dependence and transfer of intellectual techn\n\n… [+889 more chars]",
  "content_hash": "833ceb0e81ef8433bd9c79e27f605fa579649c96b9082a83403b12375336a38c",
  "token_count": 472,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0d0f3610-f1ec-527b-a8ce-487707e1f300",
  "chunk_index": 83,
  "page_number": 68,
  "page_range": [
    68,
    68
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `1490974a-a7bd-5b97-baed-474f6dd001f7`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1490974a-a7bd-5b97-baed-474f6dd001f7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \n15. Khatri, N., Ojha, A. K., Budhwar, P., Srinivasan, V., & Varma, A. (2012). Management research in India:\ncurrent state and future directions. IIMB Management Review, 24, 104e115.\n16. Kilmann, R., Slevin, D., & Jerrell, L. S. (1983). The problem of producing useful knowledge. In R.\nKilmann, K. Thomas, D. Slevin, R. Nath, & S. Jerrell (Eds.), Producing useful knowledge for organizations\n(1e24). New York: Preager Publishers.\n17. Laakso, M. & Björk, B-C. (2012). Anatomy of open access publishing - A study of longitudinal\ndevelopm\n\n… [+5597 more chars]",
  "content_hash": "6c66d11390fc12ae67ed208c36023e548c1510408b09c4140a8c71323e57de50",
  "token_count": 1612,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    69,
    70
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0405e975-37a3-5bb3-af47-6b1cb78ae744`

- vector: dim=3072 · [-0.0057, 0.0150, -0.0146, -0.0044, 0.0085, 0.0024, -0.0020, 0.0135, …]

```json
{
  "chunk_id": "0405e975-37a3-5bb3-af47-6b1cb78ae744",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "ICDL 2019: Poster \n15. Khatri, N., Ojha, A. K., Budhwar, P., Srinivasan, V., & Varma, A. (2012). Management research in India:\ncurrent state and future directions. IIMB Management Review, 24, 104e115.\n16. Kilmann, R., Slevin, D., & Jerrell, L. S. (1983). The problem of producing useful knowledge. In R.\nKilmann, K. Thomas, D. Slevin, R. Nath, & S. Jerrell (Eds.), Producing useful knowledge for organizations\n(1e24). New York: Preager Publishers.\n17. Laakso, M. & Björk, B-C. (2012). Anatomy of open access publishing - A study of longitudinal\ndevelopment and internal structure. BMC Medicine, 10, p\n\n… [+820 more chars]",
  "content_hash": "99de991bf0788a912b99c9e2ed6632659591905f99c490215eeb15bc0c4a7bc3",
  "token_count": 450,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1490974a-a7bd-5b97-baed-474f6dd001f7",
  "chunk_index": 84,
  "page_number": 69,
  "page_range": [
    69,
    69
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `22ee3319-b83f-55c8-89b3-4401d4a6d735`

- vector: dim=3072 · [-0.0316, -0.0198, -0.0152, -0.0219, 0.0041, 0.0069, -0.0065, 0.0136, …]

```json
{
  "chunk_id": "22ee3319-b83f-55c8-89b3-4401d4a6d735",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "Learned Publishing, 28(2), pp. 114–122. DOI: 10.1087/20150205.\n22. Odiorne, G. S. (1966). The management theory jungle and the existential manager. Academy of Management Journal, 9,109e115.\n23. Omobowale, A.O., Akanle, A., Adeniran, A.I. & Olayinka, K (2014). Peripheral scholarship and the\ncontext of foreign paid publishing in Nigeria. Current Sociology, 62(5), pp. 666–684. DOI:\n10.1177/0011392113508127.\n24. Panda, A., & Gupta, Rajen K. (2007). Call for developing indigenous organization theories in India: setting\nagenda for future. International Journal of Indian Culture and Business Manageme\n\n… [+977 more chars]",
  "content_hash": "d174c10634a88447934c99ffe61eb26eca9cc8cc9b93dda171ac89ee7d30b9c9",
  "token_count": 476,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1490974a-a7bd-5b97-baed-474f6dd001f7",
  "chunk_index": 85,
  "page_number": 69,
  "page_range": [
    69,
    69
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `449285a8-10df-54db-ac00-db72930a8a8e`

- vector: dim=3072 · [-0.0223, -0.0174, -0.0190, -0.0059, 0.0183, -0.0143, -0.0156, 0.0456, …]

```json
{
  "chunk_id": "449285a8-10df-54db-ac00-db72930a8a8e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "section_type": "references",
  "chunk_text": "Current Science, 111(11),\npp. 1759–1764.\n29. Shen, C. & Björk, B-C. (2015). ‘Predatory’ open access: A longitudinal study of article volumes and market characteristics. BMC Medicine, 13, p. 230. DOI: 10.1186/s12916-015-0469-2.\n30. Silver, A. (2017). Controversial website that lists ‘predatory’ publishers shuts down. Nature News, January\n18. Retrieved from: http://www.nature.com/news/controversial-website-that-lists-predatory-publishers-\nshuts-down-1.21328.\n31. Xia, J. (2014a). An imbalanced journal publishing market. Learned Publishing, 27(3), pp. 236–238. DOI:\n10.1087/20140309.\n32. Xia, J. (2\n\n… [+126 more chars]",
  "content_hash": "4b9d52e90ab08b6c3e1925f1e9e4fc5c1830d1fe3b3c4f994c392ea5a4dc9f66",
  "token_count": 237,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1490974a-a7bd-5b97-baed-474f6dd001f7",
  "chunk_index": 86,
  "page_number": 69,
  "page_range": [
    69,
    69
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `f290a5ee-c983-586d-8184-a49f30146ba8`

- vector: dim=3072 · [-0.0260, 0.0240, -0.0142, -0.0168, 0.0316, -0.0167, -0.0150, 0.0079, …]

```json
{
  "chunk_id": "f290a5ee-c983-586d-8184-a49f30146ba8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "DOI:\n10.1087/20140309.\n32. Xia, J. (2015). Predatory journals and their article processing charges. Learned Publishing, 28(1), pp. 69–\n74. DOI:10.1087/20150111.\n47 ICDL 2019: Poster \nInformation Literacy Skills among Faculty \nmembers of Central Universities in India: A \nsurvey \nHaleema Khatoon \nAssistant Professor, Dept. of Library and Information Science, Bareilly College, Bareilly \nKhalid Nadeem Khan\nAssistant Librarian, Faculty of Dentistry, Jamia Millia Islamia, New Delhi, India.\nAbstract \nInformation literacy education is relevant to quality research, quality teaching and learning and \nqu\n\n… [+2292 more chars]",
  "content_hash": "5ca3b011dd83ad39fe1a8dd85dfe2193e7917cf934f1390396185f751eefeabb",
  "token_count": 596,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1490974a-a7bd-5b97-baed-474f6dd001f7",
  "chunk_index": 87,
  "page_number": 70,
  "page_range": [
    70,
    70
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `4b017013-59c1-56dc-91f7-22b68c87a52e`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4b017013-59c1-56dc-91f7-22b68c87a52e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \nSocial Science. Therefore, findings, conclusions and recommendations may be applicable and \nreasonable to be generalized on all the faculties of these universities as well as other central \nuniversities.  The study recommended a further research to examine more additional aspects of \ninformation literacy skills among faculty members of other disciplines. \nPractical implications: Findings and suggestions of this study will definitely help to develop \ninformation literacy skills among faculty members which will in turn improve the\n\n… [+7092 more chars]",
  "content_hash": "120bda3387e70f768126e70207ab1b6851b3da93fdfcc0d20aad675627ebfbf3",
  "token_count": 1500,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    71,
    73
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `de7b133d-9f72-57e8-9d71-a8620a6b7b89`

- vector: dim=3072 · [-0.0180, 0.0605, -0.0062, -0.0035, 0.0398, -0.0143, -0.0171, 0.0049, …]

```json
{
  "chunk_id": "de7b133d-9f72-57e8-9d71-a8620a6b7b89",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ICDL 2019: Poster \nSocial Science. Therefore, findings, conclusions and recommendations may be applicable and \nreasonable to be generalized on all the faculties of these universities as well as other central \nuniversities.  The study recommended a further research to examine more additional aspects of \ninformation literacy skills among faculty members of other disciplines. \nPractical implications: Findings and suggestions of this study will definitely help to develop \ninformation literacy skills among faculty members which will in turn improve the quality of \nteaching. It will definitely be go\n\n… [+1790 more chars]",
  "content_hash": "773cb2fb84335fdbcb9a2ca9e8a40bbdbd107621b4003767655e0fe79e9440b8",
  "token_count": 428,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4b017013-59c1-56dc-91f7-22b68c87a52e",
  "chunk_index": 88,
  "page_number": 71,
  "page_range": [
    71,
    71
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `b47dc524-8be1-5fbb-91ea-c620ce2ac744`

- vector: dim=3072 · [-0.0306, 0.0656, -0.0091, -0.0132, 0.0200, -0.0217, -0.0153, -0.0023, …]

```json
{
  "chunk_id": "b47dc524-8be1-5fbb-91ea-c620ce2ac744",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Keywords\nDigital Literacy,Information Literacy, Faculty members;Teaching and Learning \nIntroduction \nThe ability ofmost developing nations to achieve the earlier stated millennium goals(MDGs) \nwhich include eradication of poverty, universal primary education, gender equality and combating diseases of various kinds; among others, led to the adoption of 2030 agenda for the \nachievement of new sets of sustainable development goals by the united nations in \n2015.(Olufunke,2018). \nThe new formulated sustainable development goals include among others, ending poverty and \nhunger, fighting inequality,\n\n… [+2380 more chars]",
  "content_hash": "4fa9de5b0cbc2f2af0e3f44390cb423969adf3a507c8774a9bf63beb4829d4b1",
  "token_count": 607,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4b017013-59c1-56dc-91f7-22b68c87a52e",
  "chunk_index": 89,
  "page_number": 71,
  "page_range": [
    71,
    72
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c7da91e2-1fbd-552e-bbb4-bfe4432942fa`

- vector: dim=3072 · [-0.0330, 0.0557, -0.0114, -0.0192, 0.0220, -0.0034, -0.0299, 0.0131, …]

```json
{
  "chunk_id": "c7da91e2-1fbd-552e-bbb4-bfe4432942fa",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "(El Hassani and Nfissi, 2015). \nAccording to the UNESCO,the empowerment of people through media and Information \nLiteracy(MIL) is an important requirement for fostering equitable access to information and knowledge and “promoting free, independent and pluralistic media and information systems.” \nWith the rapid technological advances in society today and increased access to said technology \nby people around the world, becoming information Literate is of utmost importance It is very \ncomplicated to promote information Literacy in the digital age.Technological skills are the \ncommon prerequisite \n\n… [+2156 more chars]",
  "content_hash": "31fb3c563c019d66e0c0e5f74cdd4e9e86475adbe26af5dd1b3b9c8119962496",
  "token_count": 547,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4b017013-59c1-56dc-91f7-22b68c87a52e",
  "chunk_index": 90,
  "page_number": 72,
  "page_range": [
    72,
    73
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `e77934a1-bd02-519b-b672-c9caf3149277`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e77934a1-bd02-519b-b672-c9caf3149277",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \nover conventional documents.It has been found in the study that internet has become a vital \ninstrument for teaching , research and learning process of respondents. Mishra(2007) conducted \na questionnaire survey to study digital information literacy among faculty members at Sambalpur \nuniversity . It was found that faculty members need e-information in addition to traditional print \nsources and to some extent they are computer literate.The study by Elgorta ;Smith and \nToland(2008) gives an overview of students and lecturers  on \n\n… [+7219 more chars]",
  "content_hash": "b365993731a4172c96ec928ec321016d4122b9d587a02d2b4b193471c2f57b19",
  "token_count": 1844,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    74,
    78
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a2c2ef93-1025-5468-932e-5dd3daeaee77`

- vector: dim=3072 · [-0.0293, 0.0438, -0.0170, 0.0032, 0.0174, 0.0120, -0.0039, 0.0165, …]

```json
{
  "chunk_id": "a2c2ef93-1025-5468-932e-5dd3daeaee77",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ICDL 2019: Poster \nover conventional documents.It has been found in the study that internet has become a vital \ninstrument for teaching , research and learning process of respondents. Mishra(2007) conducted \na questionnaire survey to study digital information literacy among faculty members at Sambalpur \nuniversity . It was found that faculty members need e-information in addition to traditional print \nsources and to some extent they are computer literate.The study by Elgorta ;Smith and \nToland(2008) gives an overview of students and lecturers  on using wikis in the context of course \ngroup wor\n\n… [+1490 more chars]",
  "content_hash": "21d88105b907ab595c7c95d3caef16208ecaee1873bb74692febc1c92255fedd",
  "token_count": 426,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e77934a1-bd02-519b-b672-c9caf3149277",
  "chunk_index": 91,
  "page_number": 74,
  "page_range": [
    74,
    74
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `515dcd2d-1650-50de-a70b-1a47904f2654`

- vector: dim=3072 · [-0.0489, 0.0441, -0.0105, -0.0000, 0.0107, -0.0072, -0.0182, 0.0003, …]

```json
{
  "chunk_id": "515dcd2d-1650-50de-a70b-1a47904f2654",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ol(2012).Ganaie(2013) focuses on \nthe concept of information literacy and role of library professionals in supporting information \nliteracy.It has been found from the study that importance of information literacy has not been \nrealized fully by the department of library and information science in North India.Mehaboobullah and Humayun Kabir (2013) conducted a study among college librarians in \nKerala on their ICT literacy in the digital age. It has been found in the study that application of \nICT has become inevitable in an era of information explosion and wide spread use of digital \ninformatio\n\n… [+1633 more chars]",
  "content_hash": "ec93bd1b0b5b5170500a19082e0f01f72dd79afd2a2eaf79bec4e04c1c8170ed",
  "token_count": 471,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e77934a1-bd02-519b-b672-c9caf3149277",
  "chunk_index": 92,
  "page_number": 74,
  "page_range": [
    74,
    74
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5fcea6ab-d074-5d79-a738-92d644c53a98`

- vector: dim=3072 · [-0.0265, 0.0237, -0.0140, -0.0098, 0.0156, 0.0088, -0.0082, 0.0242, …]

```json
{
  "chunk_id": "5fcea6ab-d074-5d79-a738-92d644c53a98",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "aneefa K and Sarika C(2018) assessed the web competency of\nLibrary and information science students in universities of kerala.they revealed in the study that\nmost of the students are aware of web applications and are agree that web helps to enhance\nknowledge and skills of students.\n52 ICDL 2019: Poster \nMethodology \nA well-structured questionnaire was used for collecting data from faculty members of DU; JMI \nand BHU from various branches of science and social science. A total of 125, 125 and 196 \nquestionnaires were administered to the randomly selected faculty members of DU; JMI and \nBHU resp\n\n… [+1583 more chars]",
  "content_hash": "8f87ad4fc1e4fd9c7b690bfec3b47680b1e69cd059e299ce352c1d875efed314",
  "token_count": 509,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e77934a1-bd02-519b-b672-c9caf3149277",
  "chunk_index": 93,
  "page_number": 75,
  "page_range": [
    75,
    76
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c598165f-f886-5423-bf49-c1dfa5ac1103`

- vector: dim=3072 · [-0.0031, 0.0103, -0.0169, -0.0091, 0.0272, -0.0040, -0.0145, 0.0456, …]

```json
{
  "chunk_id": "c598165f-f886-5423-bf49-c1dfa5ac1103",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Electronic |  | 150 100 Responses 50 Responses Responses 0 1 2 3 4 5 6 Responses Responses Responses |  |\n| --- | --- | --- |\n\nICDL 2019: Poster\n\narticles are used by a significant number of respondents i.e. (82.43%) of BHU; (80.50%) of JMI \nfollowed by (83.5%) of DU. E-databases are however needed by 110 (74.32%) of BHU; \n(72.03%) of JMI and (71.1%) of DU.\n\nThe need of other sources of information such as E-books, Theses and dissertations and \nnewspaper articles are less popular among faculty members of all the respective universities.\n\nMost used search tool\n\nTable 3. Most used search tool\n\nF\n\n… [+306 more chars]",
  "content_hash": "495c1fbe59b9ae91bd4324b6ff0cee7e9ca81eea6ac4043e8141283760df1e48",
  "token_count": 267,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e77934a1-bd02-519b-b672-c9caf3149277",
  "chunk_index": 94,
  "page_number": 76,
  "page_range": [
    76,
    77
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d10c067d-be8a-50ef-bfdf-d75ccea35a4c`

- vector: dim=3072 · [-0.0096, 0.0082, -0.0221, -0.0076, 0.0119, 0.0261, -0.0062, 0.0239, …]

```json
{
  "chunk_id": "d10c067d-be8a-50ef-bfdf-d75ccea35a4c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "A significant \nnumber of respondents i.e.70 (72.1%) respondents of DU; 95(80.5%) of JMI and 117 (79.05%) ICDL 2019: Poster \nrespondents of BHU use web portals. Few of them prefer subject gateways i.e. 40.2% from DU; \n(74.57%) from JMI and (75%) from BHU.  Meta search engines and online bibliographic \ndatabases are least used search tool by the respondents of DU, JMI and BHU. \nPurpose of using E-resources \nTable 4.  Purpose of using E-resources \nS.No.\nFigure 4: Purpose of using E-resources \nTable 4 reveals that 69 respondents i.e.(71.13%) from DU; 88 respondents (74.5%) from JMI \nand 103 respon\n\n… [+458 more chars]",
  "content_hash": "f7adad07b11ed967c42b459af2134efcd5a108108249ca7a8fc75bcd15262b8f",
  "token_count": 317,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e77934a1-bd02-519b-b672-c9caf3149277",
  "chunk_index": 95,
  "page_number": 78,
  "page_range": [
    78,
    78
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `20ffec9b-2313-5f05-9560-b6eca580bbfb`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "20ffec9b-2313-5f05-9560-b6eca580bbfb",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Article — Authors — Citing — Articles (cont.)\n\nICDL 2019: Poster \nCriteria for evaluation of web resources \nTable 5. Criteria for evaluation of web resources \nS.No.\n      Figure 5: Criteria for evaluation of web resources \nIt is clear from table 5 that major criteria for evaluating web resources of information is the \nauthenticity of information i.e. (49.4%) from DU; (51.6%) from JMI and (48.6%) from BHU \nfollowed by Relevancy (39.17%); (38.13%) and (35.13%) from the respondents of DU:JMI and \nBHU respectively. Reliability is the minor criteria as (15.46%) respondents from DU; (12.16%) \nfrom J\n\n… [+4796 more chars]",
  "content_hash": "020f0971061f3aa5c251beca3dad154bb4b1f879d88197ad815cdeaf39c2f72b",
  "token_count": 1549,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    79,
    83
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `863a7d77-0a7a-5f1d-a801-356fa9e899f4`

- vector: dim=3072 · [0.0041, 0.0243, -0.0221, 0.0154, 0.0310, -0.0016, 0.0034, 0.0517, …]

```json
{
  "chunk_id": "863a7d77-0a7a-5f1d-a801-356fa9e899f4",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "ICDL 2019: Poster \nCriteria for evaluation of web resources \nTable 5. Criteria for evaluation of web resources \nS.No.\n      Figure 5: Criteria for evaluation of web resources \nIt is clear from table 5 that major criteria for evaluating web resources of information is the \nauthenticity of information i.e. (49.4%) from DU; (51.6%) from JMI and (48.6%) from BHU \nfollowed by Relevancy (39.17%); (38.13%) and (35.13%) from the respondents of DU:JMI and \nBHU respectively. Reliability is the minor criteria as (15.46%) respondents from DU; (12.16%) \nfrom JMI and (12.83%) from BHU evaluate web resources\n\n… [+1017 more chars]",
  "content_hash": "408748699b01a3fd2fb3a76f471dca0f80819fa4c49304fc3f95916bd5355cc9",
  "token_count": 438,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "20ffec9b-2313-5f05-9560-b6eca580bbfb",
  "chunk_index": 96,
  "page_number": 79,
  "page_range": [
    79,
    80
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7cd3b865-d408-51c7-87b0-80d74a5fce51`

- vector: dim=3072 · [0.0051, 0.0350, -0.0069, 0.0098, 0.0201, -0.0094, 0.0018, 0.0320, …]

```json
{
  "chunk_id": "7cd3b865-d408-51c7-87b0-80d74a5fce51",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Impact of digital sources on academic work performance \nTable 7. Impact of digital sources on academic work performance \nS.No.\nSimple search (use of keywords)\nPhrase search( use of quotations)\nComplex search\nAdvanced search\nResponses\nResponses\nResponses\n58 ICDL 2019: Poster \nFigure 7: Impact of digital sources on academic work performance \nTable 7 shows that 92 respondents i.e. (94.8%) from DU; 106 (89.8%) respondents from JMI and \n137(92.5%) from BHU access to current up-to-date information by using digital resources. 82 \n(84.5%) respondents from DU; 95 (80.5%) from JMI and 116 (78.3%) respon\n\n… [+378 more chars]",
  "content_hash": "3645e7d0ca576536224edb6cc1afb238f7d8c3886a4d14edf537f52bb83414ea",
  "token_count": 249,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "20ffec9b-2313-5f05-9560-b6eca580bbfb",
  "chunk_index": 97,
  "page_number": 81,
  "page_range": [
    81,
    81
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2cc30ed1-1afb-558a-859c-91adb38488c9`

- vector: dim=3072 · [0.0035, 0.0152, -0.0038, 0.0168, 0.0200, -0.0314, 0.0038, 0.0209, …]

```json
{
  "chunk_id": "2cc30ed1-1afb-558a-859c-91adb38488c9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "Constraints faced in searching the required information \nTable 8. Constraints faced in searching the required information \nS.No.\nAccess to wide range of |  | S.No. |  | Constraints |  | Responses (DU) | % | Responses (JMI) |  | % |  | Responses (BHU) | % |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | 1. |  | Non availability of required information |  | 38 | 39.17% | 53 |  | 44.9% | 78 |  |  | 52.7% |  |\n|  | 2. |  | Unskilled Library Staff |  | 24 | 24.7% | 34 |  | 28.8% | 42 |  |  | 28.37% |  |\n|  | 3. |  | Slow speed |  | 20 | 20.6% \n\n… [+220 more chars]",
  "content_hash": "31490f600ce1eee2237e8f79f231f7f711c60cc13c9e9da72b688948cb256d5e",
  "token_count": 356,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "20ffec9b-2313-5f05-9560-b6eca580bbfb",
  "chunk_index": 98,
  "page_number": 81,
  "page_range": [
    81,
    81
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ce9a0750-78bf-5a8f-a45a-c2cf2888fb8d`

- vector: dim=3072 · [-0.0083, 0.0160, -0.0012, 0.0078, 0.0088, -0.0158, 0.0133, 0.0193, …]

```json
{
  "chunk_id": "ce9a0750-78bf-5a8f-a45a-c2cf2888fb8d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "| 13.5% |  |\n|  | 5. |  | Language of search engine |  | 12 | 12.3% | 10 |  | 8.47% | 16 |  |  | 10.81% |  | ICDL 2019: Poster \nFigure 8: Constraints faced in searching the required information \nIt is clear from table 8 that major problem faced by the respondents while searching the \ninformation is non availability of required information according to their needs as per responses \nof 38 respondents i.e.(39.17%) from DU; 53 (44.9%) from JMI and 78(52.7%) from BHU. Other \nproblems involved are untrained library staff, slow speed Time consumption and discrete \nlanguage of search engine. \nFindings\n\n… [+1237 more chars]",
  "content_hash": "c46cfbfc571b9eff71b24e3ad88438be3fbc7a7059bd149a9fcd1a31aa5dc14f",
  "token_count": 511,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "20ffec9b-2313-5f05-9560-b6eca580bbfb",
  "chunk_index": 99,
  "page_number": 82,
  "page_range": [
    82,
    83
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6c4288ae-8ec1-5f89-bb32-340d2144fe58`

- vector: dim=3072 · [-0.0072, 0.0157, -0.0151, -0.0002, 0.0137, 0.0049, -0.0100, 0.0318, …]

```json
{
  "chunk_id": "6c4288ae-8ec1-5f89-bb32-340d2144fe58",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Article — Authors — Citing — Articles",
  "chunk_text": "R E QUIR ED \nINFOR M AT IO N \nUNSKILLED \nLIB R AR Y STAFF\n\nICDL 2019: Poster\n\n It is found from the study that major criteria for evaluating web resources is the authenticity \nof information followed by relevancy and reliability.  It is found from the study that more than 80% respondents from all respective universities \nuse simple search by using keywords. It is followed by phrase search by using quotation \nand least number of respondents use complex search (more than 30% respondents) and \nBoolean logic (by more than 20% respondents).\n\n It is found that major problem faced by the responden\n\n… [+239 more chars]",
  "content_hash": "4ad9e0852b16a1c66ff5252ae04939d308f12ae3695716fbd8c251387792bffd",
  "token_count": 184,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "20ffec9b-2313-5f05-9560-b6eca580bbfb",
  "chunk_index": 100,
  "page_number": 83,
  "page_range": [
    83,
    83
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `c7a6f079-a18d-5dc7-abb2-83e8b0e42c13`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "chunk_text": "Suggestions\n\n It is found from the study that most of the respondents depend on internet for searching \ntheir required information. It shows that dependency on internet has been increased. \nNowadays internet has become an important medium for communication. \nSo,by extended internet services in libraries, we can satisfy information requirements of \nscholars as well as of faculty members. On the other hand we can make users more \ncompetent about digital resources of information. \nSo, in this context university and college library authorities should provide various \nfacilities such as internet,W\n\n… [+10986 more chars]",
  "content_hash": "6d3688272bb2274d5b8489c250bd2863478d3d7de40e085d44018c3e42d78a98",
  "token_count": 2487,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    83,
    88
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1e454dfb-3274-5d85-b874-b894952c8330`

- vector: dim=3072 · [-0.0340, 0.0245, -0.0218, -0.0047, -0.0126, 0.0037, 0.0071, 0.0218, …]

```json
{
  "chunk_id": "1e454dfb-3274-5d85-b874-b894952c8330",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "chunk_text": " It is found from the study that most of the respondents depend on internet for searching \ntheir required information. It shows that dependency on internet has been increased. \nNowadays internet has become an important medium for communication. \nSo,by extended internet services in libraries, we can satisfy information requirements of \nscholars as well as of faculty members. On the other hand we can make users more \ncompetent about digital resources of information. \nSo, in this context university and college library authorities should provide various \nfacilities such as internet,Wi-Fi and LAN \n\n… [+1061 more chars]",
  "content_hash": "767e5bd3b6153431b188438359a145007a68d886b529edba95bfbca2b7e96091",
  "token_count": 309,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "chunk_index": 101,
  "page_number": 83,
  "page_range": [
    83,
    83
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `dc622bfb-10ca-5388-8ec1-572e2f99c862`

- vector: dim=3072 · [-0.0352, 0.0312, -0.0178, -0.0046, 0.0152, 0.0019, -0.0098, 0.0240, …]

```json
{
  "chunk_id": "dc622bfb-10ca-5388-8ec1-572e2f99c862",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "chunk_text": "authorities which will make users more vigilant about uses of digital \ntools of information.\n\n According to UNESCO(2008), IL empowers people in all works of life to seek, evaluate, \nuse and create information effectively to achieve their personal, social, occupational and \neducational goals.\n\n61 ICDL 2019: Poster \nIn view of the above assertion it can be recommended that: \no\nDigital information literacy should be incorporated in the university curriculum in such a\nway that every student of the college should undergo such a programme.\no\nStudent learning advisors and subject advisors should enc\n\n… [+1813 more chars]",
  "content_hash": "02680c96f9ae182249e0f99bd9660b01099cee980f787ba0b940f0bf7c0c0267",
  "token_count": 497,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "chunk_index": 102,
  "page_number": 84,
  "page_range": [
    84,
    84
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `92522b2a-cb4c-5eae-8a37-6653329893c7`

- vector: dim=3072 · [-0.0191, 0.0454, -0.0142, 0.0074, 0.0111, 0.0000, -0.0064, 0.0147, …]

```json
{
  "chunk_id": "92522b2a-cb4c-5eae-8a37-6653329893c7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "chunk_text": "Fariza and Yaacob(2009).Facilitating lifelong learning through development of information literacy skills:a\nstudy of integrated project work.European journal of social sciences.9(3).457-464.\n5. Ganaie, Shabir Ahmad(2013).Response of library and information science in India to information literacy:\nan analytical study. International research journal of library and information science. 2013.3(3).\n6.\nGlister, P. (1997). Digital Literacy. New York: willey. p.67.\n62\n\nICDL 2019: Poster \n7.\nHaneefa K and Sarika C(2018).Web competency of Library and information science students in\nuniversities in Kera\n\n… [+1648 more chars]",
  "content_hash": "c91630907781a95d45e6cabee07a0a3096cf26bd12616365d7ee3ba5642afef2",
  "token_count": 564,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "chunk_index": 103,
  "page_number": 84,
  "page_range": [
    84,
    85
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0a874879-fab0-5e13-beb5-975dc1af82fd`

- vector: dim=3072 · [-0.0373, 0.0188, -0.0137, 0.0120, 0.0122, 0.0023, -0.0151, 0.0100, …]

```json
{
  "chunk_id": "0a874879-fab0-5e13-beb5-975dc1af82fd",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "section_type": "references",
  "chunk_text": "Mishra, Champeswar (2007). A survey of digital information literacy of Faculty at Sambalpur university.\nLibrary philosophy and practice.2007.(9). 16. Murugesan,N.(2011).Application of ICT based resources and services in research and development\nlibraries in Tamilnadu: an analytical study.European journal of social science.23(1).157-164.\n17. Mutula,Stephen M.(2010).Challenges of information illiterate first year entrants for the university of\nBotswana. Information Development.26(1).79-86.\n18. Olatunji and Oluwadare(2011).Information and communication technology literacy among the staff of\nlibra\n\n… [+359 more chars]",
  "content_hash": "6459f84780f8a7d861818b4708c3fff021752bdb91040a86b4e5561a3e6119cf",
  "token_count": 242,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "chunk_index": 104,
  "page_number": 85,
  "page_range": [
    85,
    85
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `eab925c6-d9b4-5f26-bb11-0c0922a65937`

- vector: dim=3072 · [-0.0351, 0.0092, -0.0174, -0.0267, 0.0196, 0.0007, -0.0249, 0.0051, …]

```json
{
  "chunk_id": "eab925c6-d9b4-5f26-bb11-0c0922a65937",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "chunk_text": "Information Literacy skills among faculty members of engineering colleges in\nTirunelveli district, Tamil nadu: a study. International research journal of multidisciplinary science and\ntechnology. 1(6). p 42-50.\n63 ICDL 2019: Poster \nDigital Avatar: Is e-Publishing Future of \nPublishing \n“Yesterday’s backward nations were those which missed out on industrial revolution and \ntomorrow’s backward nations would those which would miss out on communication and \ninformation revolution: Bandyopadhyay” \nAnuradha Maurya \nProfessional Assistant, Teerthanker Mahaveer Medical College & Research Centre, Teer\n\n… [+1937 more chars]",
  "content_hash": "2abaea6937e2ffa08abc9a0293387b6ec4ba1c8edcb2fb8b7b4e1f19e7622bd3",
  "token_count": 499,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "chunk_index": 105,
  "page_number": 86,
  "page_range": [
    86,
    86
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c1bc2244-fe44-5724-89f3-06ceaafc7f36`

- vector: dim=3072 · [-0.0306, 0.0150, -0.0210, -0.0128, 0.0172, 0.0152, -0.0179, 0.0146, …]

```json
{
  "chunk_id": "c1bc2244-fe44-5724-89f3-06ceaafc7f36",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Suggestions",
  "chunk_text": "Electronic publishing (EP) is fast \ntransforming into a resource set of interactive publications endowed with rich multimedia that \ncan be packaged and disseminated in various forms across different networked environments.  \nElectronic publishing also called digital publishing, e-publishing, online publishing refers to the application of computing software by a publisher for content creation and the distribution of the \n64\n\nICDL 2019: Poster \nfinal product through electronic means. It includes the publication of journals, newspapers, \nbooks, magazines databases and other documents published el\n\n… [+2325 more chars]",
  "content_hash": "f5d42da70d3fed8f6c6528d87866c0b3a5ddca8f2153800603fd03f113621ef6",
  "token_count": 620,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c7a6f079-a18d-5dc7-abb2-83e8b0e42c13",
  "chunk_index": 106,
  "page_number": 86,
  "page_range": [
    86,
    88
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `87704fea-a03e-5fcb-ac36-8f2f13a400cf`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "87704fea-a03e-5fcb-ac36-8f2f13a400cf",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "1. PDF (Portable Document Format)",
  "chunk_text": "1. PDF (Portable Document Format)\n\n2. DOC/ DOCX: Microsoft Word .doc or .docx format.\n3. Mobipocket format: (.mobi) files are supported by various devices like Amazon Kindle,\nBlackBerry, Symbian OS (Nokia phones).\n4. DAISY: DAISY (Digital Accessible Information System) format is designed to listen e-\nbooks by using a DAISY digital book player that converts text to speech.\n5. EPUB: EPUB (Electronic PUBlication) Most pf the devices supports EPub such as\nBarnes & Noble Nook, Sony Reader, iPad, and Adobe Digital Edition.\n6. TXT file: is a very simple plain-text universal format.\n7. HTML: (Hypertex\n\n… [+3846 more chars]",
  "content_hash": "df820ada12262c3ee3a28afb34aab0c89647977d8f10641667eb8dcd6f6dc3bf",
  "token_count": 993,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    88,
    90
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `32005116-39ce-56e4-bcfe-0926c077a506`

- vector: dim=3072 · [-0.0056, -0.0160, -0.0133, -0.0203, 0.0085, -0.0073, -0.0192, 0.0002, …]

```json
{
  "chunk_id": "32005116-39ce-56e4-bcfe-0926c077a506",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "1. PDF (Portable Document Format)",
  "chunk_text": "2. DOC/ DOCX: Microsoft Word .doc or .docx format.\n3. Mobipocket format: (.mobi) files are supported by various devices like Amazon Kindle,\nBlackBerry, Symbian OS (Nokia phones).\n4. DAISY: DAISY (Digital Accessible Information System) format is designed to listen e-\nbooks by using a DAISY digital book player that converts text to speech.\n5. EPUB: EPUB (Electronic PUBlication) Most pf the devices supports EPub such as\nBarnes & Noble Nook, Sony Reader, iPad, and Adobe Digital Edition.\n6. TXT file: is a very simple plain-text universal format.\n7. HTML: (Hypertext Markup Language) (.htm or .html) \n\n… [+1282 more chars]",
  "content_hash": "1c114bd41e8025aef68ae59aa1dbc55d9e87cbe4ecd638e41e57e0449f72d7e8",
  "token_count": 434,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "87704fea-a03e-5fcb-ac36-8f2f13a400cf",
  "chunk_index": 107,
  "page_number": 88,
  "page_range": [
    88,
    88
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cf3e8638-ec03-595d-8d7f-a499e3d4a603`

- vector: dim=3072 · [-0.0023, -0.0115, -0.0158, -0.0143, 0.0146, -0.0050, -0.0136, 0.0108, …]

```json
{
  "chunk_id": "cf3e8638-ec03-595d-8d7f-a499e3d4a603",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "1. PDF (Portable Document Format)",
  "chunk_text": "In 2010, Nook was introduced by Barnes and Noble, which is the largest bookstore chain in US, \nanother US bookchain named Borders, presented an eReader called Kobo. Canada-based Wattpad readers spend over 2 billion minutes on the site every month. Sony captured the largest \nmarket shares in the eReader segment in Japan and pacific region. \neReaders are less convenient for special interest literature, newspapers, and magazines, Current \ne-Ink technology cannot jump instantly from one screen to another: In addition, photographs and\n66\n\nICDL 2019: Poster \nillustrations may not display well on an \n\n… [+2105 more chars]",
  "content_hash": "9a47484b6307df7026c453e3a0b75c18489c797a53bb1a05c20f59057794a7a6",
  "token_count": 591,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "87704fea-a03e-5fcb-ac36-8f2f13a400cf",
  "chunk_index": 108,
  "page_number": 88,
  "page_range": [
    88,
    90
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `23303ce6-581c-51a4-8f7d-127c9f77de66`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "23303ce6-581c-51a4-8f7d-127c9f77de66",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "6. Design Cover using image processing software\n\n7. ISBN (International Standard Book Number) : Acquire a ISBN if desired however for\nelectronic documents , ISBN is not necessary.\n8. If price is applied, it should be clearly mentioned along with payment Gateway options\nfor faster processing.\n9. Provide Comments and Feedbacks space to communicate, update or rectify errors from\nhis work.\nPrinted books can be converted into e-book by digitizing the contents using scanning or using \nspecialized software like Blurb, There are also services like Bound Book Scanning and Blue \nLeaf that have made the \n\n… [+8413 more chars]",
  "content_hash": "818a14696bce9decf3e211421c69c9f1a1d6c4b721f6c8d64045257c25073807",
  "token_count": 1876,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    90,
    93
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `97b91d91-fec6-56ff-87d4-1f89a56c0831`

- vector: dim=3072 · [-0.0154, -0.0382, -0.0092, -0.0023, 0.0027, -0.0274, 0.0056, 0.0137, …]

```json
{
  "chunk_id": "97b91d91-fec6-56ff-87d4-1f89a56c0831",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "7. ISBN (International Standard Book Number) : Acquire a ISBN if desired however for\nelectronic documents , ISBN is not necessary.\n8. If price is applied, it should be clearly mentioned along with payment Gateway options\nfor faster processing.\n9. Provide Comments and Feedbacks space to communicate, update or rectify errors from\nhis work.\nPrinted books can be converted into e-book by digitizing the contents using scanning or using \nspecialized software like Blurb, There are also services like Bound Book Scanning and Blue \nLeaf that have made the hardware investment and will digitize your book f\n\n… [+1512 more chars]",
  "content_hash": "0ac4a44c62e75436c581dda78a07039a18c24efc45b9bbf54b42405c5efda2c8",
  "token_count": 446,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "23303ce6-581c-51a4-8f7d-127c9f77de66",
  "chunk_index": 109,
  "page_number": 90,
  "page_range": [
    90,
    90
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2a19d48e-203f-539a-a664-2873fde376c0`

- vector: dim=3072 · [-0.0058, -0.0226, -0.0113, -0.0157, -0.0093, -0.0484, -0.0199, -0.0025, …]

```json
{
  "chunk_id": "2a19d48e-203f-539a-a664-2873fde376c0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Pollution is \nanother negative offshoot of the publishing industry. Large scale paper production releases COx, \nNOx, Sulphur etc in the air which promotes smog, acid rain and climate crisis, Carcinogenic chemicals like Sodium hydroxide, hydrogen peroxide are used in paper bleaching process. Paper \n68\n\nICDL 2019: Poster \nsourced for forests have issues like biodiversity loss, water level depletion, floods, displacement \nof distinct native habitats and human rights violations also. \nAmericans are the heaviest paper users in the world with per capita consumption 354kg or about \n7 trees. 40% of th\n\n… [+1538 more chars]",
  "content_hash": "eaba40aed4ce388cb3185af0ecfde50dae113ca71fa50164cf680f1bdf43f8ca",
  "token_count": 499,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "23303ce6-581c-51a4-8f7d-127c9f77de66",
  "chunk_index": 110,
  "page_number": 90,
  "page_range": [
    90,
    91
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2765f77a-fdfa-5c19-a76a-43b918115434`

- vector: dim=3072 · [-0.0142, -0.0287, -0.0101, -0.0368, 0.0073, -0.0327, 0.0111, 0.0280, …]

```json
{
  "chunk_id": "2765f77a-fdfa-5c19-a76a-43b918115434",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "According to the writersservice.com it takes about 3 to 6 \nmonths time to publish a book, Transportation, warehousing and others cost involved are paid by \nthe reader apart from it,  a printed book is taking book toll on environment. According to Global E-book Market 2015-2019 research report the Global E-book market is the \nfastest growing sub-market in the worldwide book publishing industry accounted for \napproximately 12.6% of the Global Book Publishing market is expected to increase to 27.8% by \n2019. \nThe publication of e-books is a natural consequence of the change of habits of billions \n\n… [+805 more chars]",
  "content_hash": "5c7dcad8ea718ea12a8bbb80da550712dc21ae106967f14e4519f7b9430dfd0b",
  "token_count": 294,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "23303ce6-581c-51a4-8f7d-127c9f77de66",
  "chunk_index": 111,
  "page_number": 91,
  "page_range": [
    91,
    91
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c03bab26-dbd1-553a-bb75-230db0f408c4`

- vector: dim=3072 · [-0.0110, -0.0199, -0.0185, -0.0224, 0.0171, 0.0015, -0.0008, 0.0089, …]

```json
{
  "chunk_id": "c03bab26-dbd1-553a-bb75-230db0f408c4",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Reasons of Growing E-Publication \nPublishers are open and responsive to e-Books because they \ngenerally offer lower costs and higher margins than print. \nAn e-Book publisher does not incur inventory return costs \nthat are typically associated with traditional print channels. \n69 ICDL 2019: Poster \nThe demands and requirements of the users can be promptly catered by the Electronic publishers \ndue to trimmed delivery process, also motivates larger range of titles availability, including \nbooks that customers would not find in standard book retailers, due to insufficient demand for a \ntraditional\n\n… [+1018 more chars]",
  "content_hash": "5d30eec8c371265c9e38eb8d28482a8956fb61b04f03d7c2d45ca61754b3f72c",
  "token_count": 313,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "23303ce6-581c-51a4-8f7d-127c9f77de66",
  "chunk_index": 112,
  "page_number": 92,
  "page_range": [
    92,
    92
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8d35c2b8-2c03-5297-af8d-f45963f240f9`

- vector: dim=3072 · [-0.0442, 0.0176, -0.0181, -0.0199, -0.0018, -0.0116, -0.0022, 0.0103, …]

```json
{
  "chunk_id": "8d35c2b8-2c03-5297-af8d-f45963f240f9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Accessibility: \nE-documents can be accessed by a number of users at a time without increasing the cost of\nacquisition; if the subscription is online a single user can also access e-documents on a multiple\n70 ICDL 2019: Poster \ndevice. Publishers and aggregators are providing access to online journals through assigning \npasswords to library patrons or IP addresses of universities and institutions. \nIndexing and Abstracting Services: \nIndexing plays a crucial role for gaining acceptance of journals. Indexing services face the \nproblems to cover electronic journals. Some journal publishers and au\n\n… [+2010 more chars]",
  "content_hash": "5a72c21eeeca6788fc4227c9b5014445373e8e95ad5bf33a0a4f95ae4bb3fc4b",
  "token_count": 511,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "23303ce6-581c-51a4-8f7d-127c9f77de66",
  "chunk_index": 113,
  "page_number": 93,
  "page_range": [
    93,
    93
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `26b8664d-9caa-5d4b-be0e-328c1ec31551`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "26b8664d-9caa-5d4b-be0e-328c1ec31551",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "6. Design Cover using image processing software (cont.)\n\nICDL 2019: Poster \nIntellectual property rights and copyright issues: \nVarious users are reluctant to pay for the digital editions as they think that internet is a place \nwhere everything is free. \nVarious Publishers and committee members consider electronic journals as of lower quality than \nprinted one in spite of the fact that e-journals also reviewed rigorously by editorial board. Even \nauthors prefer printed journals for submitting their manuscripts. It is interesting to know that \nresearchers prefer electronic journals as a reader \n\n… [+7552 more chars]",
  "content_hash": "7ce7e4f1ce29c1c45a93f8c2803fabee679c66433e434bac4c595a740da0b8dd",
  "token_count": 1653,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    94,
    97
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5426f8bb-8855-5aba-b19d-b2dc02e3298b`

- vector: dim=3072 · [-0.0328, 0.0140, -0.0271, -0.0128, 0.0128, -0.0190, -0.0035, 0.0220, …]

```json
{
  "chunk_id": "5426f8bb-8855-5aba-b19d-b2dc02e3298b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "ICDL 2019: Poster \nIntellectual property rights and copyright issues: \nVarious users are reluctant to pay for the digital editions as they think that internet is a place \nwhere everything is free. \nVarious Publishers and committee members consider electronic journals as of lower quality than \nprinted one in spite of the fact that e-journals also reviewed rigorously by editorial board. Even \nauthors prefer printed journals for submitting their manuscripts. It is interesting to know that \nresearchers prefer electronic journals as a reader but they choose printed versions while \nsubmitting the ar\n\n… [+1360 more chars]",
  "content_hash": "cccb10b8bc6f6b2e0e861c8652b6ca86e822dce3823becc248b78a6dde7be46b",
  "token_count": 360,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "26b8664d-9caa-5d4b-be0e-328c1ec31551",
  "chunk_index": 114,
  "page_number": 94,
  "page_range": [
    94,
    94
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `972bf240-a292-5f63-83cd-844c006bb5cf`

- vector: dim=3072 · [-0.0452, 0.0049, -0.0192, -0.0120, -0.0164, -0.0242, -0.0099, -0.0164, …]

```json
{
  "chunk_id": "972bf240-a292-5f63-83cd-844c006bb5cf",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Lack of e-Books in Regional Languages: \nMost of e-books are available only in English or international languages, these create problems \nfor regional or native language readers.  \n72 ICDL 2019: Poster \nImpact of E-Publishing \nBook publishing is the largest of the industries that produce media and entertainment content, \nbigger even than the much more glamorous film and entertainment businesses. The economics \nof print publishing is complex which involves allocation of funds for printing, warehousing, \ntransportation, salaries, delay times, estimating the demand and allocating new titles and \np\n\n… [+1739 more chars]",
  "content_hash": "ac549a37c86c2edb3993c8598e72617a26f7f58f68958ff1a325fa7712e1fb5b",
  "token_count": 478,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "26b8664d-9caa-5d4b-be0e-328c1ec31551",
  "chunk_index": 115,
  "page_number": 95,
  "page_range": [
    95,
    95
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `3339fdb8-9d2b-544c-8230-aada4a894ae7`

- vector: dim=3072 · [-0.0205, 0.0111, -0.0163, -0.0090, -0.0098, -0.0116, 0.0092, 0.0128, …]

```json
{
  "chunk_id": "3339fdb8-9d2b-544c-8230-aada4a894ae7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Across various subjects and languages, thousands of \nbooks has been converted in multiple formats and are available for the access for special \nstudents. Bengaluru based Samarthanam Trust for Disabled has 5,000 audio books and more are added by \nthe volunteers. \n73\n\nICDL 2019: Poster \nAudio Book Resources: \nAudible.com is the first and most successful source of commercial electronic books online. You \ncan listen to the books on your computer (streaming), iPhone, or transfer them to a portable MP3 \nplayer. Audible book readers like PlayAway Books are self contained listening device that are \nbe\n\n… [+1694 more chars]",
  "content_hash": "058e93c633f1cf409b1ebff32ab35482d4652f28c393e0150d1e1bd14b13e65e",
  "token_count": 487,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "26b8664d-9caa-5d4b-be0e-328c1ec31551",
  "chunk_index": 116,
  "page_number": 95,
  "page_range": [
    95,
    96
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0d67dd1f-71dd-52bd-b789-5d09b04c7dc1`

- vector: dim=3072 · [-0.0325, -0.0034, -0.0192, -0.0165, 0.0129, -0.0192, 0.0076, 0.0199, …]

```json
{
  "chunk_id": "0d67dd1f-71dd-52bd-b789-5d09b04c7dc1",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Listen Your Book: \nIf one is bored of reading with their eyes, they can read with their ears. There are many audio \nbooks existing which can be used by anyone. \nInternational Back Volumes: \n74 ICDL 2019: Poster \nA researcher can access those journals that have been subscribed in their Libraries, but they \nalways require more, with electronic publication researcher can use back volume journals of \nthose journals that has been published internationally and can continue their research works. \nLess Space: \nThe electronic publication helps the user to carry bulkier books, multiple documents in just\n\n… [+1425 more chars]",
  "content_hash": "3d8cf6a6a07a2b37bf40f91c3b5ab936ec4030b415eae332bb080ccd1ed781d4",
  "token_count": 422,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "26b8664d-9caa-5d4b-be0e-328c1ec31551",
  "chunk_index": 117,
  "page_number": 97,
  "page_range": [
    97,
    97
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `1604c935-e29f-53be-9264-55fff032647c`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1604c935-e29f-53be-9264-55fff032647c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "6. Design Cover using image processing software (cont.)\n\nICDL 2019: Poster \n7. Reference Verification: The authenticity can be checked with the source  if the content is\navailable online.\n8. Faster Publication: For paper documents, user need to wait till they are available in the\nmarket to their distributors, but with electronic publication, they just need to know about\nthe source that where they can find that particular document and rest is easy.\n9. Updates: These e published documents can be updated easily, errors can be removed\neasily with no time.\n10. Pay Less or Nothing: E-book prices are\n\n… [+6929 more chars]",
  "content_hash": "7580e3e30c397d649ef909872f45ff9ccb5fc9abe0e0b59f1866ca643aa41515",
  "token_count": 1755,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    98,
    100
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cca5f0f7-9721-5d1f-aed7-c4aef346e5e3`

- vector: dim=3072 · [-0.0320, 0.0124, -0.0155, -0.0131, 0.0038, 0.0062, -0.0021, 0.0156, …]

```json
{
  "chunk_id": "cca5f0f7-9721-5d1f-aed7-c4aef346e5e3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "ICDL 2019: Poster \n7. Reference Verification: The authenticity can be checked with the source  if the content is\navailable online.\n8. Faster Publication: For paper documents, user need to wait till they are available in the\nmarket to their distributors, but with electronic publication, they just need to know about\nthe source that where they can find that particular document and rest is easy.\n9. Updates: These e published documents can be updated easily, errors can be removed\neasily with no time.\n10. Pay Less or Nothing: E-book prices are mostly economical than physical document. Also,\nthere ar\n\n… [+1550 more chars]",
  "content_hash": "d2316dc70f3592e39d573fd70feb9bc9d6b9e160119ab77da148434fe69c3a19",
  "token_count": 445,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1604c935-e29f-53be-9264-55fff032647c",
  "chunk_index": 118,
  "page_number": 98,
  "page_range": [
    98,
    98
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `72e8ef49-1495-5a69-9544-4df7a5224816`

- vector: dim=3072 · [-0.0330, 0.0005, -0.0158, 0.0016, -0.0177, -0.0055, -0.0085, 0.0209, …]

```json
{
  "chunk_id": "72e8ef49-1495-5a69-9544-4df7a5224816",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Not all the e-documents are freely available, so to purchase them internet banking is\nessential for payment of the cost of the document.\n4. To access all the e documents, either paid or free, internet connection is required to\ndownload them or read online.\n76 ICDL 2019: Poster \n5. All e-book reading platforms are battery powered which required charging at regular\ninterval which can create a waiting period before reusing.\n6. The feel of traditional books is not available with digital book readers.\nConclusion: \nThe electronic era has posed some exciting challenges and opportunities to explore el\n\n… [+1882 more chars]",
  "content_hash": "42d898cd39f02fec4873ea26f5edc84696c1d7e7c495d6ba585a5818d7180ae8",
  "token_count": 497,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1604c935-e29f-53be-9264-55fff032647c",
  "chunk_index": 119,
  "page_number": 99,
  "page_range": [
    99,
    99
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4d8a6b2f-db34-58d0-8c70-27f1b2f45acb`

- vector: dim=3072 · [-0.0239, -0.0069, -0.0211, 0.0052, 0.0047, 0.0141, -0.0188, 0.0232, …]

```json
{
  "chunk_id": "4d8a6b2f-db34-58d0-8c70-27f1b2f45acb",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "As Budd and Harloe stated that more likely possibility for the first decades for the 21st century is\nthe continued evolution of a mixed system- part print, increasing electronic. \nTo encourage the use of e-documents and electronic publication, following actions can be taken: 1. Digital reading platforms should be provided to students at subsidized prices.\n2. Education department can create databases for school going students containing\nrecommended textbooks of each subject.\n3. Once atleast go through government electronic databases like ePG Pathshala, SWAYAM,\nNDL, etc before purchasing any sub\n\n… [+1571 more chars]",
  "content_hash": "7ccb162b127b3a8f01e0213c56282721e4fd09f2e141452f82bfa51aee43631c",
  "token_count": 551,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1604c935-e29f-53be-9264-55fff032647c",
  "chunk_index": 120,
  "page_number": 99,
  "page_range": [
    99,
    100
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4a301b86-4c63-588b-b5c5-9cfcc0ff5481`

- vector: dim=3072 · [-0.0233, -0.0203, -0.0091, -0.0007, 0.0092, -0.0266, 0.0147, 0.0158, …]

```json
{
  "chunk_id": "4a301b86-4c63-588b-b5c5-9cfcc0ff5481",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Publishing\nPerspectives. Retrieved form https://publishingperspectives.com/2017/05/global-ebook-report-2017-many-\nmarkets/\n6.\nAngier, Michael. (2017). Top Ten Reasons Why eBooks Are Better Than Printed Books Resource Center. Retried from http://successnet.org/cms/sales-and-marketing/top-ten-reasons-why-ebooks-are-better-than-\nprinted-books\n7.\nBlogger, Green. (2014). eBook- a Saviour for Trees !. Follow Green Living. Retrieved from\nhttps://followgreenliving.com/ebook-saviour-trees/\n8.\nBoyd, Kathleen. (2016). The power of Digital Publishing. Kite Communications. Retreived from\nhttp://webcache.go\n\n… [+825 more chars]",
  "content_hash": "c176e1bf157094214762ba9006bb82ec90d7b262aca8185ca725cb3b3994e83a",
  "token_count": 416,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1604c935-e29f-53be-9264-55fff032647c",
  "chunk_index": 121,
  "page_number": 100,
  "page_range": [
    100,
    100
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `712ed9cb-6e54-5a91-bd03-60dbd0103fed`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "712ed9cb-6e54-5a91-bd03-60dbd0103fed",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "6. Design Cover using image processing software (cont.)\n\nICDL 2019: Poster \n12. Emery, Christina, Mithu Lucraft, Agata Morka, and Ros Pyne. (2017). The OA Effect: How Does Open\nAccess Affect the Usage of Scholarly Books?, 1–34. Retrieved form\nhttps://doi.org/10.6084/m9.figshare.5559280.v1\n13. Eyeway. (2017). Not Just Seeing Is Believing, Accessible Audio Books & a Library for Visually Impaired\nAre Here. The Better India. Retrieved from https://www.thebetterindia.com/104715/accessible-audio-\nbooks/\n14. Flood, Alison. (2012). Enhanced ebooks are bad for children finds American study. The Guardia\n\n… [+3131 more chars]",
  "content_hash": "f061c887304cc789822ae05fe203ee32bab0906156d248313f7b7d1b656472f1",
  "token_count": 1108,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2297ff59-030d-52c8-b500-694f79480351`

- vector: dim=3072 · [-0.0155, 0.0228, -0.0130, -0.0177, -0.0002, 0.0012, -0.0064, 0.0244, …]

```json
{
  "chunk_id": "2297ff59-030d-52c8-b500-694f79480351",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "ICDL 2019: Poster \n12. Emery, Christina, Mithu Lucraft, Agata Morka, and Ros Pyne. (2017). The OA Effect: How Does Open\nAccess Affect the Usage of Scholarly Books?, 1–34. Retrieved form\nhttps://doi.org/10.6084/m9.figshare.5559280.v1\n13. Eyeway. (2017). Not Just Seeing Is Believing, Accessible Audio Books & a Library for Visually Impaired\nAre Here. The Better India. Retrieved from https://www.thebetterindia.com/104715/accessible-audio-\nbooks/\n14. Flood, Alison. (2012). Enhanced ebooks are bad for children finds American study. The Guardian.\nRetrieved from http://www.guardian.co.uk/books/2012/ju\n\n… [+829 more chars]",
  "content_hash": "c516b0889cb0f985f279076a07857d414b8a09c1a10e3a278c26e88f9669d1e5",
  "token_count": 422,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "712ed9cb-6e54-5a91-bd03-60dbd0103fed",
  "chunk_index": 122,
  "page_number": 101,
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `53598cd5-be16-5a55-8958-3162158d5638`

- vector: dim=3072 · [-0.0083, 0.0074, -0.0139, 0.0061, -0.0113, -0.0230, -0.0032, 0.0102, …]

```json
{
  "chunk_id": "53598cd5-be16-5a55-8958-3162158d5638",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Hoffelder, Nate (2015). New Survey Shows Surprisingly High Library eBook Usage. The Digital Reader.\nRetrieved from https://the-digital-reader.com/2015/12/01/new-survey-shows-surprisingly-high-library-\nebook-usage/ 19. Hutsko, Joe. (2009). Are eReaders Greener than Books? NY Times, 2–4. Retrieved from\nhttp://green.blogs.nytimes.com/2009/08/31/are-eReaders-greener-than-books/?_r=0\n20. Inouye, Alan S. (2016). What’s in Store for Ebooks?. American Libraries. Retrieved from\nhttps://americanlibrariesmagazine.org/2016/01/04/whats-store-ebooks/\n21. Junus, S.G. Ranti. (2012). E-Books and eReaders for U\n\n… [+1032 more chars]",
  "content_hash": "acf0f2c8babb008ccac9d20da25c9206554aeedc6e14c064047b221280c8fda4",
  "token_count": 477,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "712ed9cb-6e54-5a91-bd03-60dbd0103fed",
  "chunk_index": 123,
  "page_number": 101,
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `739205cc-e5e8-58ed-8619-87be9ea2ce18`

- vector: dim=3072 · [0.0005, 0.0089, -0.0115, -0.0050, -0.0087, -0.0107, 0.0070, 0.0163, …]

```json
{
  "chunk_id": "739205cc-e5e8-58ed-8619-87be9ea2ce18",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Kinsella, Bridget. (2004). Rueben's Reading Revolution.Epublishers Weekly. 20. Retrieved from\nhttps://www.publishersweekly.com/pw/print/20041129/24484-rueben-s-reading-revolution.html 26. Koganuramath, Dr. M M, Jange , Suresh and Angadi , Mallikarjun. (2014). Electronic publishing: an\nanalytical study., 1999 In: Vision of future library and information systems : Dr. S.S. Murthy festschrift.\nViva Books (New Delhi, India), pp. 45-53. Retrieved from http://eprints.rclis.org/4971/1/Electronic-\npublishing.PDF\n27. Kowalczyk, Piotr. (2016). 10 Sites Where You Can Read Books Online. Retrieved from\nhtt\n\n… [+409 more chars]",
  "content_hash": "616eb8a353df5c25f6558eb54bef6f450afd0e4f77a131e8a2794d813607135f",
  "token_count": 307,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "712ed9cb-6e54-5a91-bd03-60dbd0103fed",
  "chunk_index": 124,
  "page_number": 101,
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `f3a24c74-60ea-52df-be7c-8984a2c0ea3d`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f3a24c74-60ea-52df-be7c-8984a2c0ea3d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "6. Design Cover using image processing software (cont.)\n\n| ICDL 2019: Poster |  |\n| --- | --- |\n|  | 12. Emery, Christina, Mithu Lucraft, Agata Morka, and Ros Pyne. (2017). The OA Effect: How Does Open |\n|  | Access Affect the Usage of Scholarly Books?, 1–34. Retrieved form |\n|  | https://doi.org/10.6084/m9.figshare.5559280.v1 |\n|  | 13. Eyeway. (2017). Not Just Seeing Is Believing, Accessible Audio Books & a Library for Visually Impaired |\n|  | Are Here. The Better India. Retrieved from https://www.thebetterindia.com/104715/accessible-audio- |\n|  | books/ |\n|  | 14. Flood, Alison. (2012). Enh\n\n… [+3460 more chars]",
  "content_hash": "db4396b0e109185cf25d1cf62f7116b2e56716a47ef3887371ff4ec39dfa7d54",
  "token_count": 1277,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1f8d129f-fa9f-5177-adc4-af9b8ab8c73c`

- vector: dim=3072 · [-0.0043, 0.0125, -0.0087, -0.0134, -0.0129, -0.0254, 0.0086, 0.0226, …]

```json
{
  "chunk_id": "1f8d129f-fa9f-5177-adc4-af9b8ab8c73c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "| ICDL 2019: Poster |  |\n| --- | --- |\n|  | 12. Emery, Christina, Mithu Lucraft, Agata Morka, and Ros Pyne. (2017). The OA Effect: How Does Open |\n|  | Access Affect the Usage of Scholarly Books?, 1–34. Retrieved form |\n|  | https://doi.org/10.6084/m9.figshare.5559280.v1 |\n|  | 13. Eyeway. (2017). Not Just Seeing Is Believing, Accessible Audio Books & a Library for Visually Impaired |\n|  | Are Here. The Better India. Retrieved from https://www.thebetterindia.com/104715/accessible-audio- |\n|  | books/ |\n|  | 14. Flood, Alison. (2012). Enhanced ebooks are bad for children finds American study. T\n\n… [+1069 more chars]",
  "content_hash": "893e86a26835091af15a0b6cceff34c43c62f855e9ba242504bb1fc7bfffad4c",
  "token_count": 535,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f3a24c74-60ea-52df-be7c-8984a2c0ea3d",
  "chunk_index": 125,
  "page_number": 101,
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `12ac2662-f10d-53e1-9fbb-af6bcda9f411`

- vector: dim=3072 · [-0.0104, -0.0029, -0.0107, 0.0021, -0.0004, -0.0240, 0.0057, 0.0168, …]

```json
{
  "chunk_id": "12ac2662-f10d-53e1-9fbb-af6bcda9f411",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Hutsko, Joe. (2009). Are eReaders Greener than Books? NY Times, 2–4. Retrieved from | |  | http://green.blogs.nytimes.com/2009/08/31/are-eReaders-greener-than-books/?_r=0 |\n| 20. | Inouye, Alan S. (2016). What’s in Store for Ebooks?. American Libraries. Retrieved from |\n|  | https://americanlibrariesmagazine.org/2016/01/04/whats-store-ebooks/ |\n| 21. | Junus, S.G. Ranti. (2012). E-Books and eReaders for Users with Print Disabilities. Library Technology |\n|  | Reports. 22–28. Retrieved from journals.ala.org/ltr/article/download/4683/5566 |\n|  | 22. Kaushik, Sharat; Narayan, Shesh. (2016). Impac\n\n… [+1258 more chars]",
  "content_hash": "b03423fb8a5986c6284d500361a2db2c45cef962ba5407158a31a53c6d02cf6f",
  "token_count": 587,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f3a24c74-60ea-52df-be7c-8984a2c0ea3d",
  "chunk_index": 126,
  "page_number": 101,
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `598f69f4-3aab-5373-8fa3-cc7b03ea252e`

- vector: dim=3072 · [-0.0010, 0.0089, -0.0115, 0.0003, -0.0014, -0.0181, 0.0062, 0.0327, …]

```json
{
  "chunk_id": "598f69f4-3aab-5373-8fa3-cc7b03ea252e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "S.S. Murthy festschrift. |\n|  | Viva Books (New Delhi, India), pp. 45-53. Retrieved from http://eprints.rclis.org/4971/1/Electronic- | |  | publishing.PDF |\n|  | 27. Kowalczyk, Piotr. (2016). 10 Sites Where You Can Read Books Online. Retrieved from |\n|  | http://ebookfriendly.com/sites-where-you-can-read-books-online/ |\n|  | 28. Kumar, Deepak. (2019). eBooks vs Books (Pros & Cons): The Never Ending Debate. Devicebar. |\n|  | Retrieved form https://devicebar.com/ebooks-vs-books-pros-and-cons/2041/ |\n|  | 29. Lean, Geoffrey. (2010). How Many E-Books to Spare a Tree ?. Retrieved from |\n|  | https:\n\n… [+95 more chars]",
  "content_hash": "fc66bec5eacb667d18febd93ae6d15fbfd7697f3dfeb6564bd54acf4e19d11f6",
  "token_count": 224,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f3a24c74-60ea-52df-be7c-8984a2c0ea3d",
  "chunk_index": 127,
  "page_number": 101,
  "page_range": [
    101,
    101
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `e3a1019d-13b6-52f2-96c3-e02ad3d69dc8`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e3a1019d-13b6-52f2-96c3-e02ad3d69dc8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "6. Design Cover using image processing software (cont.)\n\nICDL 2019: Poster \n30. Mason, Caleb. (2016). Trashing Paper : Why We Should Consider Time Spent With Print. Book Business.\nRetrieved from https://www.bookbusinessmag.com/post/trashing-paper-consider-time-spent-print/\n31. McLachlin, Alana. (2015). “Traditional Publishing versus Self-Publishing.” Scribendi. 1–6. Retrieved from\nhttp://www.scribendi.com/advice/traditional_versus_self_publishing.en.html.\n32. Mims, Christopher. 2017. Are E-Books an Environmental Choice?. Green Living Show. Retrieved from\nwww.greenlivingonline.com/article/are-e\n\n… [+5162 more chars]",
  "content_hash": "510a2496b438fd7f896b7b02e28aeeefaae543763313ef9da6476daac24b7e19",
  "token_count": 1669,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    102,
    103
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `40e50f30-5d71-5c14-a772-c080e83132fa`

- vector: dim=3072 · [-0.0140, 0.0119, -0.0149, -0.0066, -0.0037, 0.0062, -0.0065, 0.0322, …]

```json
{
  "chunk_id": "40e50f30-5d71-5c14-a772-c080e83132fa",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "ICDL 2019: Poster \n30. Mason, Caleb. (2016). Trashing Paper : Why We Should Consider Time Spent With Print. Book Business.\nRetrieved from https://www.bookbusinessmag.com/post/trashing-paper-consider-time-spent-print/\n31. McLachlin, Alana. (2015). “Traditional Publishing versus Self-Publishing.” Scribendi. 1–6. Retrieved from\nhttp://www.scribendi.com/advice/traditional_versus_self_publishing.en.html.\n32. Mims, Christopher. 2017. Are E-Books an Environmental Choice?. Green Living Show. Retrieved from\nwww.greenlivingonline.com/article/are-e-books-environmental-choice\n33. NAB M. P. Shah All India \n\n… [+950 more chars]",
  "content_hash": "61ccff86eb6f2b52f2d72c342d673e32623bc1bc632385cfe96fccf9b75ff84d",
  "token_count": 433,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e3a1019d-13b6-52f2-96c3-e02ad3d69dc8",
  "chunk_index": 128,
  "page_number": 102,
  "page_range": [
    102,
    102
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `9be3da63-0138-5da1-b880-0811a9dc3289`

- vector: dim=3072 · [-0.0132, 0.0066, -0.0093, -0.0011, -0.0126, -0.0045, 0.0155, 0.0311, …]

```json
{
  "chunk_id": "9be3da63-0138-5da1-b880-0811a9dc3289",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Retrieved from http://www.vikalpsangam.org/article/a-digital-book-library-for-blind-students-is-\nhelping-them-visualise-a-bright-future/#.XSTZJz9KjIU 38. Palmer, Brian. (2010). Should You Ditch Your Books for an eReader ?. Slate. Retrieved from\nhttps://slate.com/technology/2010/08/are-ipads-and-kindles-better-for-the-environment-than-books.html\n39. Pappas, Christopher. (2014). Top 10 Reasons To Publish Online Your Learner's Work. Retrieved from\nhttps://elearningindustry.com/top-10-reasons-publish-online-learners-work\n40. Patrick, Allan. (2014). Ebooks or Paper Books :Your Best Arguments. Life \n\n… [+1059 more chars]",
  "content_hash": "2d9d8f3a7e315e9ac6560f8ff430669494f46720dd8a17787fb401d0eb4b35a3",
  "token_count": 478,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e3a1019d-13b6-52f2-96c3-e02ad3d69dc8",
  "chunk_index": 129,
  "page_number": 102,
  "page_range": [
    102,
    102
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a81cdd06-a98b-573b-bdc8-05e68a44b762`

- vector: dim=3072 · [-0.0170, 0.0036, -0.0107, 0.0181, -0.0108, -0.0037, 0.0055, 0.0242, …]

```json
{
  "chunk_id": "a81cdd06-a98b-573b-bdc8-05e68a44b762",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Reily, Markus. (2015). eBooks and The Environment: A Greener Reading Experience. Good EReader. 1–3. http://goodereader.com/blog/electronic-readers/ebooks-and-the-environment-a-greener-reading-experience\n46. Roth, Susanna, Zetterberg, Lars, AcWorth, William, Kangas, Hannah-Liisa, Neuhoff, Karsten, and Vera\nZipperer. (2016). The Pulp and Paper. 7–40. Retrieved from\nhttps://webcache.googleusercontent.com/search?q=cache:jrzwGOU69FkJ:https://www.diw.de/documents/d\nokumentenarchiv/17/diw_01.c.534645.de/cs-pulp-and-paper.pdf+&cd=1&hl=en&ct=clnk&gl=in\n47. S, Kamakshi. (2013). 10, 000 HP Pavilion G4 No\n\n… [+196 more chars]",
  "content_hash": "87d72ec92ba5c9d01243ac7ec6a9f5c136be63dfa1ccc29cebb8b4fadd283aa7",
  "token_count": 265,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e3a1019d-13b6-52f2-96c3-e02ad3d69dc8",
  "chunk_index": 130,
  "page_number": 102,
  "page_range": [
    102,
    102
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `785d57cc-d153-5cad-9852-4e20c7a5cc6e`

- vector: dim=3072 · [-0.0095, 0.0188, -0.0145, 0.0014, 0.0150, -0.0038, -0.0051, 0.0355, …]

```json
{
  "chunk_id": "785d57cc-d153-5cad-9852-4e20c7a5cc6e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "section_type": "references",
  "chunk_text": "Techtree.com. Retrieved form http://www.techtree.com/content/news/3245/10000-hp-pavilion-g4-\nnotebooks-distributed-akhilesh-yadav-govt.html\n80 ICDL 2019: Poster \n48. Shabbir, Imran, and Mirzaeian, Mojtaba. (2017). Carbon Emissions Reduction Potentials in Pulp and Paper\nMills by Applying Cogeneration Technologies. Energy Procedia 112 (October 2016). 142–49. Retrieved\nfrom https://doi.org/10.1016/j.egypro.2017.03.1075\n49. Singh, Kyli. (2018). 11 Places for Thrifty Bookworms to Download Free E-Books. Retrieved from\nhttps://mashable.com/article/free-ebooks/\n50. Springer. (2013). 10 Steps to Implem\n\n… [+1490 more chars]",
  "content_hash": "abe20d6f78c7b9310001f7caed36dad2b8534a94c5516dd7691fa91cb058c379",
  "token_count": 603,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "e3a1019d-13b6-52f2-96c3-e02ad3d69dc8",
  "chunk_index": 131,
  "page_number": 103,
  "page_range": [
    103,
    103
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `42871c3c-3434-5af0-a882-5ff4969ddbda`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "42871c3c-3434-5af0-a882-5ff4969ddbda",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "6. Design Cover using image processing software (cont.)\n\nICDL 2019: Poster \nInformation E-resources for Generation Alpha: \nMRIS library as an Information Resource Centre \nMonika Mukh \nLibrarian Manav Rachna International School Mohali. \nAbstract \nThere was a time when libraries were regarded as a store house and librarians were supposed to \nbe store keeper to keep the books inside lock and key as there were no use of books. But now \ndays that trend has totally been changed. 21st century libraries are regarded as Information \nservice centres, which are more approachable and easy to access. Diff\n\n… [+2490 more chars]",
  "content_hash": "0848762c8e3f68433b1cc97413cf85cbf7682cc33ed8c5e9f1578792f6886abe",
  "token_count": 619,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    104,
    105
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `56dbe273-6441-586f-9acf-1f7941341cee`

- vector: dim=3072 · [-0.0274, 0.0177, -0.0213, -0.0010, 0.0197, 0.0134, -0.0072, 0.0164, …]

```json
{
  "chunk_id": "56dbe273-6441-586f-9acf-1f7941341cee",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "ICDL 2019: Poster \nInformation E-resources for Generation Alpha: \nMRIS library as an Information Resource Centre \nMonika Mukh \nLibrarian Manav Rachna International School Mohali. \nAbstract \nThere was a time when libraries were regarded as a store house and librarians were supposed to \nbe store keeper to keep the books inside lock and key as there were no use of books. But now \ndays that trend has totally been changed. 21st century libraries are regarded as Information \nservice centres, which are more approachable and easy to access. Different libraries are working \non different perspectives wi\n\n… [+1514 more chars]",
  "content_hash": "02e322ffc46bfd3656893c105a728a39350ac6b4f15af1f81422c854bd796e65",
  "token_count": 436,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "42871c3c-3434-5af0-a882-5ff4969ddbda",
  "chunk_index": 132,
  "page_number": 104,
  "page_range": [
    104,
    104
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cc42e7fb-8f79-5ca9-b9b1-7094a5eb8660`

- vector: dim=3072 · [-0.0290, 0.0530, -0.0184, 0.0251, 0.0144, 0.0304, -0.0060, 0.0109, …]

```json
{
  "chunk_id": "cc42e7fb-8f79-5ca9-b9b1-7094a5eb8660",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Design Cover using image processing software",
  "chunk_text": "Pathshala: for students and teachers who can access e-books on \nmobile devices and desktops, mKavach (Mobile security solutions), DigiSevak: for citizen \nvolunteers, DigiLocker: for the safety of digital copies and eBasta app: for teachers and students is another very handy app, suggested by Indian Government in Education Domain for \nteachers and students which helps them access e-books and create study material. These E-\nresources are much helpful as they save the time of the users, are easy to access and more user \nfriendly.  \n82\n\nICDL 2019: Poster\n\nThe Government of India has initiated majo\n\n… [+561 more chars]",
  "content_hash": "2f5ff48d0da8f68bc012b67ac32e6324a08e4eb65c1dbebac386ce1fcd2a6562",
  "token_count": 231,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "42871c3c-3434-5af0-a882-5ff4969ddbda",
  "chunk_index": 133,
  "page_number": 104,
  "page_range": [
    104,
    105
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `09763510-b161-5962-904b-580b9369f12a`

- vector: dim=3072 · [-0.0526, 0.0365, -0.0148, 0.0239, 0.0166, 0.0362, -0.0032, 0.0251, …]

```json
{
  "chunk_id": "09763510-b161-5962-904b-580b9369f12a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "SWAYAM MOOCs Portal",
  "chunk_text": "Study Webs of Active learning for Young Aspiring Minds (SWAYAM) is an indigenous \nMassive Open Online Courses (MOOCs) portal that provides high quality education – anyone, \nanytime, anywhere at no cost- has been made operational. To make easy access of good quality \neducational content to even remotest part of the country, satellite communication has been used \nand 32 DTH channels have been made functional, under SWAYAM Prabha programme. So far, \nmore than 1,000 courses have been made available and more than 33 lakh users have registered \non this forum.\n\nNational Digital Library (NDL)\n\nThe ini\n\n… [+256 more chars]",
  "content_hash": "9a34989f42d78c50e369acf83c000e5698203c42e4c7a1703beb36ee430338a1",
  "token_count": 184,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 134,
  "page_number": 105,
  "page_range": [
    105,
    105
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `5e0e29fb-3ef4-546e-b8c9-7fc837226d22`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "5e0e29fb-3ef4-546e-b8c9-7fc837226d22",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Unnat Bharat Abhiyan (UBA)",
  "chunk_text": "Unnat Bharat Abhiyan (UBA)\n\nIt is a new initiative to make use of the knowledge base in the higher educational institutions for \nplugging technology gaps in the rural areas. It will help boosting the technology usage in rural \nIndia by customising the same as per local needs.\n\nPandit Madan Mohan Malaviya National Mission on Teachers and Teaching \n(PMMMNMTT)\n\nLaunched in December, 2014, The scheme is aimed to address the issues of supply of qualified \nteachers, attracting talent into teaching profession, raising the quality teaching in schools and \ncolleges.\n\nGlobal Initiative of Academic Netwo\n\n… [+2810 more chars]",
  "content_hash": "40c25f144da1dc25a6b0c6a64466068de8cdd2b0d9cb7a4e044649870d709f0f",
  "token_count": 755,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    105,
    107
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `152f051a-3713-51b5-befe-ddc77b9635be`

- vector: dim=3072 · [-0.0437, 0.0212, -0.0150, 0.0089, 0.0181, 0.0036, -0.0321, 0.0270, …]

```json
{
  "chunk_id": "152f051a-3713-51b5-befe-ddc77b9635be",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Unnat Bharat Abhiyan (UBA)",
  "chunk_text": "It is a new initiative to make use of the knowledge base in the higher educational institutions for \nplugging technology gaps in the rural areas. It will help boosting the technology usage in rural \nIndia by customising the same as per local needs.\n\nPandit Madan Mohan Malaviya National Mission on Teachers and Teaching \n(PMMMNMTT)\n\nLaunched in December, 2014, The scheme is aimed to address the issues of supply of qualified \nteachers, attracting talent into teaching profession, raising the quality teaching in schools and \ncolleges.\n\nGlobal Initiative of Academic Networks (GIAN)\n\nThe initiative l\n\n… [+380 more chars]",
  "content_hash": "b87ee2f1f67e0992e6a2b734925af448f6d2d573d1844b390b72944ca2f5637e",
  "token_count": 203,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5e0e29fb-3ef4-546e-b8c9-7fc837226d22",
  "chunk_index": 135,
  "page_number": 105,
  "page_range": [
    105,
    105
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `bf7cf7d7-f7de-5d57-b511-23b8e0c74379`

- vector: dim=3072 · [-0.0529, 0.0377, -0.0151, -0.0034, 0.0177, -0.0109, -0.0173, 0.0252, …]

```json
{
  "chunk_id": "bf7cf7d7-f7de-5d57-b511-23b8e0c74379",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Unnat Bharat Abhiyan (UBA)",
  "chunk_text": "GIAN is supposed to enable Indian students & \nfaculty to interact with best academic and industry experts from across the world. So far, 1,075 \ncourses have been conducted in which more than 40,000 students gained enriched academic \ninputs and knowledge.\n\n83 ICDL 2019: Poster \nIMPRINT India \nIt is an effort to direct research in the premier institutions into areas of social relevance. 10 such \ndomains have been identified which could substantially impact the living standards of the rural \nareas. More than 2,600 research proposals have been submitted by scientists in these areas. \nUchchtar Avis\n\n… [+2060 more chars]",
  "content_hash": "dc0c6d3a0ddd60b2cf7a6ed60c90e02d80e57545abaae193ec390b547dc9e4c4",
  "token_count": 595,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5e0e29fb-3ef4-546e-b8c9-7fc837226d22",
  "chunk_index": 136,
  "page_number": 106,
  "page_range": [
    106,
    107
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `f7ccfdb5-113c-5869-be2a-8ba37d8267e8`

- vector: dim=3072 · [-0.0276, 0.0596, -0.0097, -0.0014, -0.0079, -0.0187, 0.0176, 0.0283, …]

```json
{
  "chunk_id": "f7ccfdb5-113c-5869-be2a-8ba37d8267e8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Rashtriya Madhyamik Shiksha Abhiyan (RMSA)",
  "chunk_text": "It was launched by the Government of India in March, 2009 envisaging inter-alia provision of a \nsecondary school within a reasonable distance of any habitation and to improve quality of \neducation imparted at secondary level by making all secondary schools conform to prescribed \nnorms, removing gender, socio-economic and disability barriers etc. In 2013, secondary \neducation the schemes of ICT, vocational education, Girls Hostel and IEDSS were subsumed \nunder the umbrella of RMSA. Under the scheme, 12,682 new schools and 37,799 existing \nschools for strengthening have been sanctioned so far.",
  "content_hash": "5793ab6e09d6bb3179ac0d8ba5e15ca26f174b5aa77876ae2a7ecbe8313273d9",
  "token_count": 128,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 137,
  "page_number": 107,
  "page_range": [
    107,
    107
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `567e46bd-7fa8-53f2-9723-f2d71af5e1e6`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "567e46bd-7fa8-53f2-9723-f2d71af5e1e6",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "E-pathshala",
  "chunk_text": "E-pathshala\n\nIt has been developed by NCERT (National Council for Educational Research and Training) for \nshowcasing and disseminating all educational e-resources including textbooks, audio, video, \nperiodicals and a variety of other print and non-print materials. So far, 3,062 audios and videos, \n650 e-books (e-pubs) and 504 flip books have been made available on the portal and mobile app.\n\nLibrary at Manav Rachna International School as ‘Information \nResource Centre’\n\nAt MRIS Mohali, library is a place with open access system, which is more than an Information \nResource Centre wherein studen\n\n… [+4006 more chars]",
  "content_hash": "ab57c32d427b30d4e734ea791635c587d886f06ac61a7e06b4756de1f3078adf",
  "token_count": 968,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    107,
    111
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5b575b62-2e94-527c-8033-a431f4f4c92c`

- vector: dim=3072 · [-0.0161, 0.0325, -0.0230, 0.0227, -0.0089, -0.0016, 0.0202, 0.0135, …]

```json
{
  "chunk_id": "5b575b62-2e94-527c-8033-a431f4f4c92c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "E-pathshala",
  "chunk_text": "It has been developed by NCERT (National Council for Educational Research and Training) for \nshowcasing and disseminating all educational e-resources including textbooks, audio, video, \nperiodicals and a variety of other print and non-print materials. So far, 3,062 audios and videos, \n650 e-books (e-pubs) and 504 flip books have been made available on the portal and mobile app.\n\nLibrary at Manav Rachna International School as ‘Information \nResource Centre’\n\nAt MRIS Mohali, library is a place with open access system, which is more than an Information \nResource Centre wherein students come with \n\n… [+889 more chars]",
  "content_hash": "642d609eccddf0a456c902523f78b8e1ba73146c684a8d3a225051695bf60766",
  "token_count": 300,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "567e46bd-7fa8-53f2-9723-f2d71af5e1e6",
  "chunk_index": 138,
  "page_number": 107,
  "page_range": [
    107,
    107
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `f0fc66d1-f26c-5ee8-8634-c1196e806a6f`

- vector: dim=3072 · [0.0053, 0.0547, -0.0215, 0.0136, 0.0014, 0.0043, -0.0149, 0.0145, …]

```json
{
  "chunk_id": "f0fc66d1-f26c-5ee8-8634-c1196e806a6f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "E-pathshala",
  "chunk_text": "Class-Library connectivity is done during Academic Workshops wherein children visit the \nlibrary to complete their work and review the work done in the class. Children explore the \ndictionaries, encyclopaedias to retrieve the information related to their concerned learning areas \nor annual projects.\n\n85 ICDL 2019: Poster \nChart 1 : MRIS library as “Information Resource Centre” for seven learning areas \nChildren take up various activities in library like: vocabulary building by reading newspapers, \nweaving their our own story with new words, writing book reviews, solving word puzzles, cross \nwo\n\n… [+1700 more chars]",
  "content_hash": "d0da0549e106026de53142114167ec4d92c71f43c9f19769b7392c39bdb51411",
  "token_count": 470,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "567e46bd-7fa8-53f2-9723-f2d71af5e1e6",
  "chunk_index": 139,
  "page_number": 108,
  "page_range": [
    108,
    109
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `7f902d84-2ac2-5793-bd4c-15c8bd0ffe79`

- vector: dim=3072 · [-0.0176, 0.0069, -0.0112, -0.0044, 0.0118, -0.0038, -0.0049, 0.0104, …]

```json
{
  "chunk_id": "7f902d84-2ac2-5793-bd4c-15c8bd0ffe79",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "E-pathshala",
  "chunk_text": " Expose them to books from variety of genres through organizing ‘Books Tasting’ activity \nfrom time to time. \n Organize Edutrips to different libraries like State Library, District Library, Central State \nlibraries etc. to acquaint them with different sections of different libraries.\n\n87 ICDL 2019: Poster \nProvide the badges for ‘Star Readers’, ‘TRIVIA Stars’ and ‘Riddle Master’ \nConclusion \nThere are various ‘Electronic Information Resources’ available with in a click away. A librarian \nas total quality person who manages these information resources help the patrons through \ndisseminating r\n\n… [+796 more chars]",
  "content_hash": "1553e49a7dd5509e0753e227e81a366e377a59ad970fb1dc464b64ada2e43536",
  "token_count": 311,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "567e46bd-7fa8-53f2-9723-f2d71af5e1e6",
  "chunk_index": 140,
  "page_number": 110,
  "page_range": [
    110,
    111
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `053ed831-cde7-58e9-81bb-dfe36ba4e841`

- vector: dim=3072 · [0.0008, 0.0223, -0.0170, -0.0051, 0.0003, -0.0144, -0.0120, -0.0258, …]

```json
{
  "chunk_id": "053ed831-cde7-58e9-81bb-dfe36ba4e841",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Abstract",
  "chunk_text": "In an age when browsing the net, playing with funky handsets and passing non-stop SMSs seem \nto be the order of the day, reading a book in a peaceful corner of a library has become an archaic \nidea for most people. While technology is slowly taking a steady control over individual lives, \nthe reading habit is fast vanishing into thin air. Reading habits are calculated as how much a \nperson read, how often they read, when they read and what do they read. Reading can be \nsummarized as a habit that involves books, printed articles and electronic materials. It varies \ndifferently of how each mater\n\n… [+149 more chars]",
  "content_hash": "d9aca65e6559bbae706f03c7ce1468c6f78cb5fe7138ad022315731093ff0871",
  "token_count": 158,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 141,
  "page_number": 111,
  "page_range": [
    111,
    111
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `fa7647b9-53f9-5cb0-834c-0337ab01e17f`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "fa7647b9-53f9-5cb0-834c-0337ab01e17f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction\n\nToday, in the 21st century, where everything mobilised, we are experiencing a revolution of \ndigital technology. Like the printing press did, technological blessings like the internet, smart \nboards, tablets and e-readers are once more reshaping our reading and learning habits entirely. \nKnow a days, children are extremely fond of their gizmos like the tablets, smartphones, gaming \ngadgets and, of course, the television, which makes it difficult for parents to inculcate the habit \nof reading in young children. Fortunately enough, India can boast about some of the best \nchildren’s\n\n… [+8459 more chars]",
  "content_hash": "4dcfb6953ca4aac2c134fd93b852ff0036ec1eed28739c2e2d83d2b87d56dec5",
  "token_count": 1831,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    111,
    114
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4c014e4c-fda4-570f-a13d-b01271c60c7c`

- vector: dim=3072 · [-0.0241, 0.0110, -0.0150, 0.0199, -0.0257, -0.0298, -0.0031, 0.0025, …]

```json
{
  "chunk_id": "4c014e4c-fda4-570f-a13d-b01271c60c7c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Today, in the 21st century, where everything mobilised, we are experiencing a revolution of \ndigital technology. Like the printing press did, technological blessings like the internet, smart \nboards, tablets and e-readers are once more reshaping our reading and learning habits entirely. \nKnow a days, children are extremely fond of their gizmos like the tablets, smartphones, gaming \ngadgets and, of course, the television, which makes it difficult for parents to inculcate the habit \nof reading in young children. Fortunately enough, India can boast about some of the best \nchildren’s magazine subs\n\n… [+1654 more chars]",
  "content_hash": "0ccf942e40b073531693e9186570555b9cb5c7ba80be6ccc555660657b2282ab",
  "token_count": 442,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "fa7647b9-53f9-5cb0-834c-0337ab01e17f",
  "chunk_index": 142,
  "page_number": 111,
  "page_range": [
    111,
    111
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5fc46feb-672c-566d-b023-b1c3a1566fa1`

- vector: dim=3072 · [-0.0251, 0.0464, -0.0085, 0.0071, -0.0179, -0.0326, -0.0025, -0.0046, …]

```json
{
  "chunk_id": "5fc46feb-672c-566d-b023-b1c3a1566fa1",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "ILA asserts that every child deserves—frames reading as an issue of equity and social justice. \nThe campaign was focus on activating educators, policymakers and literacy partners to join ILA \nin their efforts to raise awareness of these Rights and see them realized for every child, \neverywhere.\n\n89 ICDL 2019: Poster \nThe 10 Fundamental Rights of Children’s Rights to Read are: \n1. Children have the basic human right to read.\n2. Children have the right to access texts in print and digital formats.\n3. Children have the right to choose what they read.\n4. Children have the right to read texts that \n\n… [+1848 more chars]",
  "content_hash": "dbac5b4bdb1e9696389abb7d442c3884c045275daf8ee867ac374413f3265b0a",
  "token_count": 492,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "fa7647b9-53f9-5cb0-834c-0337ab01e17f",
  "chunk_index": 143,
  "page_number": 112,
  "page_range": [
    112,
    112
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `df4f3fac-25ff-5eab-847d-99a09c437720`

- vector: dim=3072 · [-0.0106, 0.0492, -0.0083, 0.0021, -0.0071, -0.0219, -0.0051, -0.0144, …]

```json
{
  "chunk_id": "df4f3fac-25ff-5eab-847d-99a09c437720",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "While it’s not often recognized for its quality, education in the south \nAsian country has been on the rise, and now places in the top half of U.S. News & World \nReport’s rankings of 80 countries for best in education. With more than 700,000 schools in operation, India certainly has a big job on its hands. Despite \nthe recent improvements in Indian school systems, many parents choose to educate their children \nin private institutions. In fact, just 70% of school age children attend public schools. That being \nsaid, only about 50% of Indian children go to school at all: while registration is co\n\n… [+555 more chars]",
  "content_hash": "7ed110a3f2ef92354ae26ff48241724fd980277284642fe5b6a44783a8f22346",
  "token_count": 237,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "fa7647b9-53f9-5cb0-834c-0337ab01e17f",
  "chunk_index": 144,
  "page_number": 112,
  "page_range": [
    112,
    112
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4e7f9a64-6fb3-509c-ac42-aeea01114f31`

- vector: dim=3072 · [-0.0136, 0.0403, -0.0085, -0.0177, -0.0079, -0.0014, -0.0086, -0.0105, …]

```json
{
  "chunk_id": "4e7f9a64-6fb3-509c-ac42-aeea01114f31",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Reading is one of the powerful and everlasting influence \nin the promotion of one’s personal development in particular social progress in general. Regular \nand systematic reading sharpens the intellect, refines the emotions, elevates tastes and provides \n90 ICDL 2019: Poster \nperspective for one’s living and thereby prepares one for an effective participation in the social \nand political life. Reading gives a unifying and civilization force tending to unite social group \nthrough the dissemination of common experiences. \nIt helps in acquiring newer ideas, in providing the needed information, se\n\n… [+1844 more chars]",
  "content_hash": "acfe38b8f69159c5d293e79cfd51c005dfa33a0485302d91ce99071c7df01eb8",
  "token_count": 488,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "fa7647b9-53f9-5cb0-834c-0337ab01e17f",
  "chunk_index": 145,
  "page_number": 113,
  "page_range": [
    113,
    113
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `405b7adb-dfa6-5bb3-a2ad-01ca87411ae9`

- vector: dim=3072 · [-0.0145, 0.0302, -0.0119, -0.0124, -0.0027, -0.0182, -0.0147, -0.0184, …]

```json
{
  "chunk_id": "405b7adb-dfa6-5bb3-a2ad-01ca87411ae9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Broadly, reading habits cover broadly individual’s style of regularizing study behaviour and \nsensitization to curricular and extracurricular books, interest in newspapers, and magazines on \nthe one hand and such personal habits like reading aloud or silently in group or seclusion etc. Reading instructs, entertains and transports (stimulates) and further going to stay with us. \nReading scores over viewing because it is personal, intimate and certainly more stimulating. \nImportance of Reading for the Individual and for Society \nReading is an important process of acquiring information by receivi\n\n… [+1200 more chars]",
  "content_hash": "00635629fea9742a5a2c814522e2c1a082125524fdf02fc05aea73cc012344b8",
  "token_count": 381,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "fa7647b9-53f9-5cb0-834c-0337ab01e17f",
  "chunk_index": 146,
  "page_number": 113,
  "page_range": [
    113,
    114
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8bd007b1-2387-58e9-881a-1eddf1a4cf7b`

- vector: dim=3072 · [-0.0041, 0.0033, -0.0213, 0.0028, 0.0029, -0.0022, 0.0362, 0.0046, …]

```json
{
  "chunk_id": "8bd007b1-2387-58e9-881a-1eddf1a4cf7b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "5W1H Annotation",
  "chunk_text": "5W1H is the abbreviation summarising the following six questions: What? Who? Where? \nWhen? Why? How? These questions whose answers are considered basic in information \ngathering or problem solving. They are often mentioned in journalism (cf. news style), research \nand police investigations. They constitute a formula for getting the complete story on a subject. \nThis method consists of asking a systematic set of questions to collect all the data necessary to \ndraw up a report of the existing situation with the aim of identifying the true nature of the \nproblem and describing the context precise\n\n… [+673 more chars]",
  "content_hash": "f172b23b105f1127e1e8af51f82281d9d99da4f423911810e2895b92760b34c3",
  "token_count": 265,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 147,
  "page_number": 114,
  "page_range": [
    114,
    114
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `40ca67cf-c12d-5f5f-94b8-c04d1c81e9b8`

- vector: dim=3072 · [-0.0197, 0.0169, -0.0211, 0.0052, 0.0204, 0.0031, 0.0193, -0.0048, …]

```json
{
  "chunk_id": "40ca67cf-c12d-5f5f-94b8-c04d1c81e9b8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Research Questions",
  "chunk_text": "To achieve the research objectives some questions and their myths & predictions were \nformulated based on 5W1H analyses are tabulated below:\n\n92\n\nICDL 2019: Poster\n\n5W’s & 1H analyses sheet to describe the problem\n\n5W1H \nConsider these Questions \nMyths & Predictions \nWhy \nWhy children need to read? \n1. Is it really necessary for parents to take part \nin school reading activities? \n2. Difference could I make as a Parent? \n3. My child is too young to learn to read yet, but \nwhat can I do to set them off in the right \ndirection? \nWhat \nWhat should children read? \n4. Can children choose their own \n\n… [+216 more chars]",
  "content_hash": "5c95f0c9090ab0b715ccb0a16aebdc3458eb431a5666a7d8a160c8488274adc8",
  "token_count": 202,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 148,
  "page_number": 114,
  "page_range": [
    114,
    115
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `724a3db5-4fae-5f70-bdc7-dffd590b09a7`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "724a3db5-4fae-5f70-bdc7-dffd590b09a7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "7. I think my child’s problems are more serious",
  "chunk_text": "7. I think my child’s problems are more serious\n\n– what should I do? \n8. My son is switching off reading - what can I \ndo? \n9. What should I do if my child is not at the \nreading level they’re expected to be at? \nWhere \nWhere should Children read? \nWhere can I get help from? \nWho \nWhom should Children read? \n10. Tips can I use to help child learn to read? \nWho decides what? \nHow \nHow can we create a good reading \nenvironment? \nHow can we help children to nurture a reading \nhabit? \n11. Should parents arrange a large number of \nextra-curricular activities and tutorials for \nchildren after school\n\n… [+3607 more chars]",
  "content_hash": "e929831e1a47617e1dfd9ad46046b5b3986a1c03d555ecceebace9508256b38c",
  "token_count": 888,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    115,
    117
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6ff3b7d5-9393-53e3-8906-8ec3b9288610`

- vector: dim=3072 · [-0.0002, 0.0076, -0.0007, -0.0087, 0.0267, -0.0170, 0.0239, 0.0001, …]

```json
{
  "chunk_id": "6ff3b7d5-9393-53e3-8906-8ec3b9288610",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "7. I think my child’s problems are more serious",
  "chunk_text": "– what should I do? \n8. My son is switching off reading - what can I \ndo? \n9. What should I do if my child is not at the \nreading level they’re expected to be at? \nWhere \nWhere should Children read? \nWhere can I get help from? \nWho \nWhom should Children read? \n10. Tips can I use to help child learn to read? \nWho decides what? \nHow \nHow can we create a good reading \nenvironment? \nHow can we help children to nurture a reading \nhabit? \n11. Should parents arrange a large number of \nextra-curricular activities and tutorials for \nchildren after school? \n12. Is \nacademic \nperformance \nthe \nmost \nimpo\n\n… [+1286 more chars]",
  "content_hash": "d2a24cd22f35b7bfe4bf6c1156a575964fd92e218733d82171201acc1ef924f0",
  "token_count": 432,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "724a3db5-4fae-5f70-bdc7-dffd590b09a7",
  "chunk_index": 149,
  "page_number": 115,
  "page_range": [
    115,
    116
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6ddc8b48-22b8-5958-aa1d-93be08831fd5`

- vector: dim=3072 · [0.0098, 0.0228, -0.0118, -0.0172, 0.0095, -0.0156, 0.0065, -0.0133, …]

```json
{
  "chunk_id": "6ddc8b48-22b8-5958-aa1d-93be08831fd5",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "7. I think my child’s problems are more serious",
  "chunk_text": "Difference could I make as a Parent? 2. 3. My child is too young to learn to read yet, but what can I do to set them off in the right |\n\nICDL 2019: Poster\n\nA. \nDeveloping Cognitive Abilities: During the reading process, it is common to apply different skills such as understanding, \ninduction, analysis, deduction and imagination, which facilitate the development of children’s \ncognitive abilities. Thus children who read regularly have faster brain development and will be \nmore mature in their thinking.\n\nB. \nEnhancing Language Competence:\n\nReading can help children acquire more vocabulary, knowl\n\n… [+1862 more chars]",
  "content_hash": "a80053ae0151d2d5a9b7116dd1364afaa4af635a4c8666b03317010727cf0870",
  "token_count": 498,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "724a3db5-4fae-5f70-bdc7-dffd590b09a7",
  "chunk_index": 150,
  "page_number": 116,
  "page_range": [
    116,
    117
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `c3d7ae5f-02f1-53e2-bafb-20877b6ddb15`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "c3d7ae5f-02f1-53e2-bafb-20877b6ddb15",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Myths & Predictions",
  "chunk_text": "Myths & Predictions\n\nMyth-1. Is it really necessary for parents to take part in  school reading activities?\n\nAccording to the findings of PIRLS 2006, more frequent home-school co-operation led to better \nstudent’s reading performance. If parents can serve as ‘Story Pop’ or ‘Story Mom’ in schools \nregularly, they can help promote reading by creating a favourable atmosphere. In addition to \nnurturing children’s reading interest and habits, parents can convey the message that they have \nhigh regard for reading and great concern for children. As a result, parent-child relationship is \nenhanced.\n\nM\n\n… [+4497 more chars]",
  "content_hash": "a913a919c5ef2b45517b22f06a13d13794f30f1a948a77d5b38bdc72fcd2ff12",
  "token_count": 1048,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    117,
    119
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c14a0a5a-288b-587e-9f1a-e34c3588d593`

- vector: dim=3072 · [0.0284, -0.0062, -0.0174, 0.0110, -0.0080, -0.0057, 0.0051, -0.0190, …]

```json
{
  "chunk_id": "c14a0a5a-288b-587e-9f1a-e34c3588d593",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Myths & Predictions",
  "chunk_text": "Myth-1. Is it really necessary for parents to take part in  school reading activities?\n\nAccording to the findings of PIRLS 2006, more frequent home-school co-operation led to better \nstudent’s reading performance. If parents can serve as ‘Story Pop’ or ‘Story Mom’ in schools \nregularly, they can help promote reading by creating a favourable atmosphere. In addition to \nnurturing children’s reading interest and habits, parents can convey the message that they have \nhigh regard for reading and great concern for children. As a result, parent-child relationship is \nenhanced.\n\nMyth-2. Difference cou\n\n… [+1206 more chars]",
  "content_hash": "88d384d10d32a44650874bec51a4cb808233c6b607a553794705ff89854709cb",
  "token_count": 400,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c3d7ae5f-02f1-53e2-bafb-20877b6ddb15",
  "chunk_index": 151,
  "page_number": 117,
  "page_range": [
    117,
    117
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `bfd775e1-e378-54b1-89f9-f562ecb79e10`

- vector: dim=3072 · [0.0054, 0.0270, -0.0173, 0.0034, 0.0196, -0.0007, -0.0304, -0.0294, …]

```json
{
  "chunk_id": "bfd775e1-e378-54b1-89f9-f562ecb79e10",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Myths & Predictions",
  "chunk_text": "In this way, \nreading becomes a habit. Most importantly, talk to your child. Spend time with them, doing simple activities (cooking, \nmaking something, building a model). As you talk about what you’re doing, you are helping \nthem to learn new words. Later, when they see words written down, they have already heard \nthem and know what they mean.\n\n95\n\nICDL 2019: Poster\n\nWhat should Children Read?\n\nParents should let children choose their own books for leisure reading and expose them to \ndiversified reading experiences and text-types. Reading materials with healthy contents and \ncorrect language a\n\n… [+1709 more chars]",
  "content_hash": "ec46d12c139caf58e013ab494481f4d69eada6b30268e3bcf7e9f6207e174bbb",
  "token_count": 459,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c3d7ae5f-02f1-53e2-bafb-20877b6ddb15",
  "chunk_index": 152,
  "page_number": 117,
  "page_range": [
    117,
    119
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `89e26c9d-7079-5edf-a784-f22d1d91951b`

- vector: dim=3072 · [-0.0041, 0.0157, -0.0218, 0.0028, 0.0040, -0.0160, -0.0179, -0.0047, …]

```json
{
  "chunk_id": "89e26c9d-7079-5edf-a784-f22d1d91951b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Myths & Predictions",
  "chunk_text": "These books provide \nsimple and interesting experiments and challenging problems which stimulate children’s \ncuriosity as well as develop their interest and inquiry about science.\n\n96\n\nICDL 2019: Poster\n\nE. \nNewspapers & Magazines: Newspapers help to improve reading habits, knowledge, and awareness. They can be part of \ngood study habits for readers in any area of specialization.\n\nNewspapers are reading materials related to our daily lives. Newspapers of a high standard both \nin contents and language expose children to current affairs and\n\ninternational news as well as latest information of va\n\n… [+628 more chars]",
  "content_hash": "5a7d9d179cb12f9f5ac645ec4a7824ab3c35a81491a8217c5203c67e0542b936",
  "token_count": 241,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "c3d7ae5f-02f1-53e2-bafb-20877b6ddb15",
  "chunk_index": 153,
  "page_number": 119,
  "page_range": [
    119,
    119
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `0049965f-4b17-5879-8ad6-226ad078f80b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "0049965f-4b17-5879-8ad6-226ad078f80b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "MYTH\n\nMyth-4. Can children choose their own books?\n\nAllowing choices in favourite reading materials not only can help nurture children’s reading \ninterest, but also facilitate parents to have a better understanding of their children’s thoughts and \nlikes.\n\nIf children show preference only for a particular type of book, parents should guide them to read \na larger variety of reading materials to widen their horizons.\n\nMyth-5. Can children read comics and leisure magazines?\n\nComics and leisure magazines do, in general, stimulate children’s reading interest. They also \nprovide certain social exper\n\n… [+8857 more chars]",
  "content_hash": "261beb9b42baa1c3f60e3a3898bb1378cd8849dcbb3aa2fd21dcbafea4eb1a4f",
  "token_count": 2007,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    119,
    123
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5f89c634-dd14-5244-9e22-df7412c422e0`

- vector: dim=3072 · [0.0098, 0.0297, -0.0280, 0.0124, -0.0043, -0.0073, -0.0238, -0.0226, …]

```json
{
  "chunk_id": "5f89c634-dd14-5244-9e22-df7412c422e0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Myth-4. Can children choose their own books?\n\nAllowing choices in favourite reading materials not only can help nurture children’s reading \ninterest, but also facilitate parents to have a better understanding of their children’s thoughts and \nlikes.\n\nIf children show preference only for a particular type of book, parents should guide them to read \na larger variety of reading materials to widen their horizons.\n\nMyth-5. Can children read comics and leisure magazines?\n\nComics and leisure magazines do, in general, stimulate children’s reading interest. They also \nprovide certain social experiences\n\n… [+1559 more chars]",
  "content_hash": "51051e84fe795554ae99d322bcf5f3bb4caf1b2fd8f3507c6a7634f384951303",
  "token_count": 423,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0049965f-4b17-5879-8ad6-226ad078f80b",
  "chunk_index": 154,
  "page_number": 119,
  "page_range": [
    119,
    120
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `97f1172c-4d9e-506c-beca-ff47790dba9f`

- vector: dim=3072 · [0.0076, 0.0212, -0.0212, -0.0046, -0.0002, -0.0012, -0.0210, -0.0257, …]

```json
{
  "chunk_id": "97f1172c-4d9e-506c-beca-ff47790dba9f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "There are many good ways to tempt children to read:\n\n1. \nOrganising book fairs and exhibitions. 2. \nMeet the author: Invite authors to come and read out excerpts from their books. \nMaybe even autograph their books. This is a win-win for both parties.\n\n3. \nHave book review contests and give away the latest book as a prize.\n\n4. \nAllow students to borrow books during vacations and permit them to be renewed \nonline during vacations. (If the librarian and school authorities think that the borrower \nis responsible enough).\n\n5. \nHave book clubs: Let students meet say once a fortnight and discuss thei\n\n… [+1290 more chars]",
  "content_hash": "b38037d092c7aa1ff9d98c9be8de2dcc581b187a0094544c227f63d36a6549a9",
  "token_count": 416,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0049965f-4b17-5879-8ad6-226ad078f80b",
  "chunk_index": 155,
  "page_number": 120,
  "page_range": [
    120,
    121
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `02d97934-bd1c-5a4a-ae82-a67bc82d2a57`

- vector: dim=3072 · [0.0128, 0.0347, -0.0140, 0.0105, 0.0076, -0.0053, -0.0069, -0.0388, …]

```json
{
  "chunk_id": "02d97934-bd1c-5a4a-ae82-a67bc82d2a57",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Many children learn at different rates, and you shouldn’t \nget anxious. Remember that anxious children can’t learn, and that early enjoyment of books and \nstories lasts for life.\n\nMyth-6. My child doesn’t enjoy reading-this is not his cup of tea? o \nMake sure your child isn’t tired, hungry or desperate to watch their favourite TV \nprogramme when you read to them. Sit with them for a short time every day and \nread a book with them on a subject that interests them, whether that’s cars, animals \nor sports. Don’t expect them to read it for themselves. Just show them how \ninteresting it is to be ab\n\n… [+1561 more chars]",
  "content_hash": "53266a44a8ab68578e1b3bbf768691358ed394121bf66e2375b8c5501759d53e",
  "token_count": 482,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0049965f-4b17-5879-8ad6-226ad078f80b",
  "chunk_index": 156,
  "page_number": 121,
  "page_range": [
    121,
    122
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a3801848-9790-51d7-a20c-dd70a273bacb`

- vector: dim=3072 · [0.0397, 0.0527, -0.0142, 0.0448, 0.0019, -0.0166, 0.0017, -0.0310, …]

```json
{
  "chunk_id": "a3801848-9790-51d7-a20c-dd70a273bacb",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Many boys like non-fiction books, so try asking at your local library \nfor recommendations – it may be that he’ll enjoy reading Horrible Histories or the \nGuinness Book of Records more than fiction. o \nRole models are also important. Make sure boys see their dads, uncles or granddads \nreading, even if it’s a newspaper, so that it seems familiar and they can copy their \nreading behaviour. \no \nFinally, praise your son when something is read well. Equally, if he reads something \nincorrectly, don’t make him feel that this is bad - mistakes are just part of the \nlearning process.\n\nMyth-9. What shou\n\n… [+1611 more chars]",
  "content_hash": "a9c9130866406ca3a508be35781d4d7d9d08ea36b14c1c7ca0242e8b9ef1757f",
  "token_count": 487,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0049965f-4b17-5879-8ad6-226ad078f80b",
  "chunk_index": 157,
  "page_number": 122,
  "page_range": [
    122,
    122
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `de576dd0-be39-5afc-b517-e00511e222a2`

- vector: dim=3072 · [0.0143, 0.0436, -0.0149, 0.0140, -0.0016, -0.0064, 0.0008, -0.0154, …]

```json
{
  "chunk_id": "de576dd0-be39-5afc-b517-e00511e222a2",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Several schools have not just one library but \nmaybe even three — a reading room for pre-school, a primary school library and one for high \nschool. Even if it is restricted to just one, it is a repository of information. Books — both texts and reference — neatly catalogued and classified in well-designated areas \nmake the library more friendly and accessible. Books according to the choice of the reader and \nwithin the budget of the school are available in more than one copy. Fiction books are arranged \nclass-wise with a separate rack reserved for the staff. I have always loved libraries, and e\n\n… [+1185 more chars]",
  "content_hash": "846e48d6c43e37cc4483b65170f307644922cce8d26e8f9f28026e9c7a8edfb2",
  "token_count": 363,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "0049965f-4b17-5879-8ad6-226ad078f80b",
  "chunk_index": 158,
  "page_number": 122,
  "page_range": [
    122,
    123
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `09c88752-0366-5067-a526-10e8c0d88f33`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "09c88752-0366-5067-a526-10e8c0d88f33",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "MYTH (cont.)\n\nLibraries provide access to reading materials through the school library, students and youths can \ngain and improve their skills. Libraries help introduce the use of reading for information, \npleasure, passing examinations, and personal growth through lifelong learning. Libraries provide \nmaterials that offer more extensive and varied information than classroom study alone cannot \nprovide. Voluntary reading helps develop reading skills and mastery of language, extends \nstudents’ knowledge, and assists them in their academic work. Students and youths who read are \nlikely to have b\n\n… [+6460 more chars]",
  "content_hash": "99d72aeffa509d58ed7bc43afb1226e5b33c4c5de835bbb8df86a11434a50b82",
  "token_count": 1383,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    123,
    126
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `909b1a5d-d4a8-5d44-8a24-e29e866d21d8`

- vector: dim=3072 · [0.0037, 0.0560, -0.0143, 0.0146, -0.0114, -0.0048, 0.0128, -0.0157, …]

```json
{
  "chunk_id": "909b1a5d-d4a8-5d44-8a24-e29e866d21d8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Libraries provide access to reading materials through the school library, students and youths can \ngain and improve their skills. Libraries help introduce the use of reading for information, \npleasure, passing examinations, and personal growth through lifelong learning. Libraries provide \nmaterials that offer more extensive and varied information than classroom study alone cannot \nprovide. Voluntary reading helps develop reading skills and mastery of language, extends \nstudents’ knowledge, and assists them in their academic work. Students and youths who read are \nlikely to have background know\n\n… [+1850 more chars]",
  "content_hash": "616a76096dfc374cd2a8d09a73c163551b0db2414b800548385cb18f55f640ea",
  "token_count": 448,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "09c88752-0366-5067-a526-10e8c0d88f33",
  "chunk_index": 159,
  "page_number": 123,
  "page_range": [
    123,
    124
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `cccd0ce8-299a-57e5-bcf6-9d131e902e1a`

- vector: dim=3072 · [-0.0068, 0.0328, -0.0108, 0.0185, -0.0112, 0.0045, -0.0010, -0.0004, …]

```json
{
  "chunk_id": "cccd0ce8-299a-57e5-bcf6-9d131e902e1a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "School libraries are always rich in colourful story books \n101\n\nICDL 2019: Poster\n\nthat capture the attention and imaginations of students to develop lifelong learning \nabilities. Secondary school students can be taught about basic ICT appreciation to \nprepare them for future use. c) \nLibrary Orientation Programmes: Librarians engage in coaching fresh users on the \nuse of library materials. People using the library for the first time may not be \naccustomed with retrieving information from the library. It is the onus of the \nlibrarians to educate the fresh users on information retrieval process\n\n… [+1820 more chars]",
  "content_hash": "40dee1043dc31aa0d783eaaed420a89c4c6c7f31a81018c7485ecda57a0ae934",
  "token_count": 478,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "09c88752-0366-5067-a526-10e8c0d88f33",
  "chunk_index": 160,
  "page_number": 124,
  "page_range": [
    124,
    125
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d3397860-1587-5fdf-a6c8-12535d7dc095`

- vector: dim=3072 · [0.0034, 0.0064, -0.0053, -0.0118, 0.0003, -0.0241, -0.0033, -0.0241, …]

```json
{
  "chunk_id": "d3397860-1587-5fdf-a6c8-12535d7dc095",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Role of teachers: o Provide reading assignments \no twenty minute reading time; \no Teachers started the program in the first period and it was part of every school \nday; \no Students were free to choose which book to read; \no All students, teachers and staff were to do nothing but to read books which they \nlike; \no Class teachers acted as role models by participating in reading; \no Teachers allowed no interruption of students’ reading; and \no Teachers encourage students to write notes and reflections in their reading \njournals. \no The teacher should enjoy reading herself/himself so that s/he can\n\n… [+1872 more chars]",
  "content_hash": "fd3f04e4b8fa6ea65f157fe495c1e283635bbe375472c5d0d647aac9b7f187de",
  "token_count": 510,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "09c88752-0366-5067-a526-10e8c0d88f33",
  "chunk_index": 161,
  "page_number": 125,
  "page_range": [
    125,
    126
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ae2e4a3c-f5e8-5264-9465-ee36a2869993`

- vector: dim=3072 · [-0.0092, 0.0288, -0.0158, -0.0138, 0.0030, 0.0245, 0.0191, -0.0286, …]

```json
{
  "chunk_id": "ae2e4a3c-f5e8-5264-9465-ee36a2869993",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Your Child’s Teacher",
  "chunk_text": "When children see their parents and teachers working together, they feel more secure and \nconfident. Taking an interest in your child’s education will help your child do better in school. \nYour child’s teacher can provide advice about helping your child learn to read. Here are some \ntopics you could discuss with the teacher:\n\n• \nyour child’s reading strengths \n• \nthe reading goals for your child and how you can support your child in working towards \nthose goals, \n• \nbooks that your child could read easily and books that he or she would find more \ndifficult, \n• \nbooks and authors your child mig\n\n… [+901 more chars]",
  "content_hash": "a84ac07834e42478362408a3c77ae54292e80ed9fad90cb4d7ae68308c690f09",
  "token_count": 338,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 162,
  "page_number": 126,
  "page_range": [
    126,
    126
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `53a1e3d9-4d94-5f44-933a-900204b1e1e3`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "53a1e3d9-4d94-5f44-933a-900204b1e1e3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Others Who Can Help\n\nYou can enlist many other people besides your child’s teacher as partners in helping your child \nlearn to read. Here are some suggestions:\n\n• \nConsider involving relatives and friends in helping to motivate your child to learn to read. \nOlder siblings, grandparents, family friends, and your child’s caregivers can add their \nsupport and encouragement.\n\n• \nTake your child to your local library and look for books that will interest him or her. \nSome children find books with interactive features particularly motivating.\n\n104\n\nICDL 2019: Poster\n\nAsk the librarians for help. The\n\n… [+8072 more chars]",
  "content_hash": "84e227045bdda72704b5be2774db9596f5d7d48e3aa5ee8cabf052df3da54409",
  "token_count": 1967,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    126,
    130
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `64ccc07f-3305-588f-b9dc-0d0a46bfabe0`

- vector: dim=3072 · [0.0142, 0.0195, -0.0190, -0.0079, 0.0033, 0.0186, -0.0008, -0.0305, …]

```json
{
  "chunk_id": "64ccc07f-3305-588f-b9dc-0d0a46bfabe0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "You can enlist many other people besides your child’s teacher as partners in helping your child \nlearn to read. Here are some suggestions:\n\n• \nConsider involving relatives and friends in helping to motivate your child to learn to read. \nOlder siblings, grandparents, family friends, and your child’s caregivers can add their \nsupport and encouragement.\n\n• \nTake your child to your local library and look for books that will interest him or her. \nSome children find books with interactive features particularly motivating.\n\n104\n\nICDL 2019: Poster\n\nAsk the librarians for help. They will know which boo\n\n… [+1308 more chars]",
  "content_hash": "1771714102ea57f91e5544098cd79eec32f8f0bf0427b405f6105cf2015231c8",
  "token_count": 410,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a1e3d9-4d94-5f44-933a-900204b1e1e3",
  "chunk_index": 163,
  "page_number": 126,
  "page_range": [
    126,
    127
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `74dfcf5b-4a11-5d59-af24-ca4405a13eca`

- vector: dim=3072 · [0.0038, 0.0076, -0.0237, -0.0225, 0.0072, -0.0117, -0.0374, 0.0002, …]

```json
{
  "chunk_id": "74dfcf5b-4a11-5d59-af24-ca4405a13eca",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Over the next pages, you can pick up some tips on:\n\n• \nhow to read with your child \n• \nhelping children to enjoy reading \n• \nchoosing what to read \n• \nunderstanding phonics\n\na) \nHow to read with your child For most of us, reading aloud isn’t part of everyday life, so the thought of reading a story to your \nchild may be a bit daunting. But don’t let this put you off – your children will be enjoying \nthemselves too much to criticise your performance!\n\nb) \nWhen should I start reading with my child?\n\nIt’s great to read to your child from the earliest months. Cuddle close and sing nursery rhymes, \n\n\n… [+1565 more chars]",
  "content_hash": "520d98697e59f37bfdfa16572da084dcff707695cd68c6004a2cf8f88cc734a8",
  "token_count": 504,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a1e3d9-4d94-5f44-933a-900204b1e1e3",
  "chunk_index": 164,
  "page_number": 127,
  "page_range": [
    127,
    128
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `00bae8f3-cb63-5254-a830-962e801d479b`

- vector: dim=3072 · [0.0090, 0.0150, -0.0186, -0.0005, 0.0167, 0.0013, -0.0320, -0.0058, …]

```json
{
  "chunk_id": "00bae8f3-cb63-5254-a830-962e801d479b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "While you may not \nwin an Oscar, your child will enjoy your performance and appreciate the story even more.\n\n• \nRemember that your face says it all – so exaggerate your normal expression times three \nlike a children’s TV presenter: children will love it. • \nEmphasise repeated words and phrases (‘the big bad wolf ’; ‘… blew, and blew, and blew \nthe house down’). In this way, your child starts to learn the language used in books. \nEncourage your child to say the words with you.\n\n• \nTurn off the television and concentrate on enjoying the book.\n\n• \nTry audio books that children can listen to on th\n\n… [+1578 more chars]",
  "content_hash": "5ad5a2189a2e6e1d7d4732a01b8730f5824a532325485fca5eb0fe873ec58aa7",
  "token_count": 500,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a1e3d9-4d94-5f44-933a-900204b1e1e3",
  "chunk_index": 165,
  "page_number": 128,
  "page_range": [
    128,
    129
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `1f886215-e847-5aa4-94e4-53a989b33512`

- vector: dim=3072 · [0.0020, 0.0257, -0.0119, -0.0075, 0.0028, 0.0030, -0.0286, -0.0069, …]

```json
{
  "chunk_id": "1f886215-e847-5aa4-94e4-53a989b33512",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Reading is reading and it is all good. 5) \nGet comfortable! – Snuggle up somewhere warm and cosy with your child, either in \nbed, on a beanbag or on the sofa, or make sure they have somewhere comfy when \nreading alone.\n\n6) \nAsk questions – To keep them interested in the story, ask your child questions as you \nread such as, ‘What do you think will happen next?’ or ‘Where did we get to last \nnight? Can you remember what had happened already?’\n\n7) \nRead whenever you get the chance – Bring along a book or magazine for any time \nyour child has to wait, such as at a doctor’s surgery.\n\n8) \nRead again\n\n… [+963 more chars]",
  "content_hash": "960200befc4e73dad36c42a3db4a5626584b8702506851a0a7b7ea6b22811af8",
  "token_count": 367,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a1e3d9-4d94-5f44-933a-900204b1e1e3",
  "chunk_index": 166,
  "page_number": 129,
  "page_range": [
    129,
    130
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `e567153c-3026-547b-a09b-56944c0652b3`

- vector: dim=3072 · [-0.0059, 0.0310, -0.0118, 0.0031, -0.0002, -0.0073, -0.0035, -0.0241, …]

```json
{
  "chunk_id": "e567153c-3026-547b-a09b-56944c0652b3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Is it a book they have got from school to help \npractise reading and build fluency? Is it a book that they find easy to read that helps them build \nconfidence? Is it a book for you to read for pleasure to your child? f) \nWhat should I read to my child, what should they be reading, and when? With \nhundreds of books in your local library, school or bookshop, it can be hard to know \nwhere to start when choosing a book for your child. Remember that as adults we like \nto re-read favourite books, relax with a magazine or tackle something challenging. \nChildren are the same, so encourage choices – ma\n\n… [+946 more chars]",
  "content_hash": "4370896cabe0f918ca375fd23f5327a399c617903ff01c23c8faf31f20fbdae1",
  "token_count": 350,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "53a1e3d9-4d94-5f44-933a-900204b1e1e3",
  "chunk_index": 167,
  "page_number": 130,
  "page_range": [
    130,
    130
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `9609a225-9af5-5530-a97a-e3805ed9fc72`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "9609a225-9af5-5530-a97a-e3805ed9fc72",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Others Who Can Help (cont.)\n\nIntroduce the ‘Rule of five’ to older children. Encourage them to read the first page or two of a \nnew book. They must put up one finger for every word they cannot read. If they get to five \nfingers, then the book is too hard for them and they should choose another one. Don’t encourage \nthem just to guess at words they can’t read.\n\nWhen we asked authors what they liked to read to their children, a few old favourites cropped \nup:\n\n108\n\nICDL 2019: Poster\n\nh) \nMy child has just started school and is learning to read via phonics. What is \nphonics?\n\nWith phonics, childr\n\n… [+7687 more chars]",
  "content_hash": "a60d7503bab47b080ae69e0f9b4f372b5f9c4d19194e7c39444dc1c4f18d1caa",
  "token_count": 1977,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    130,
    134
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `57dd07e6-5646-5e7e-a67e-7b2cb9438f01`

- vector: dim=3072 · [-0.0173, 0.0092, -0.0161, 0.0033, -0.0151, -0.0002, -0.0023, -0.0022, …]

```json
{
  "chunk_id": "57dd07e6-5646-5e7e-a67e-7b2cb9438f01",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Introduce the ‘Rule of five’ to older children. Encourage them to read the first page or two of a \nnew book. They must put up one finger for every word they cannot read. If they get to five \nfingers, then the book is too hard for them and they should choose another one. Don’t encourage \nthem just to guess at words they can’t read.\n\nWhen we asked authors what they liked to read to their children, a few old favourites cropped \nup:\n\n108\n\nICDL 2019: Poster\n\nh) \nMy child has just started school and is learning to read via phonics. What is \nphonics?\n\nWith phonics, children are taught to read by lear\n\n… [+1211 more chars]",
  "content_hash": "0645973044ab8a1a744efe5aaa761246cb6c10d42a557ef7641e277ad54b2af5",
  "token_count": 451,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "9609a225-9af5-5530-a97a-e3805ed9fc72",
  "chunk_index": 168,
  "page_number": 130,
  "page_range": [
    130,
    131
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `11c76898-4aae-5035-bc4d-f1907f122b88`

- vector: dim=3072 · [0.0029, 0.0240, -0.0095, -0.0073, 0.0088, -0.0013, 0.0036, -0.0025, …]

```json
{
  "chunk_id": "11c76898-4aae-5035-bc4d-f1907f122b88",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Try not to add ‘uh’ to consonant sounds, such as /t/ and /p/, as this makes \nit trickier to blend the sounds together into words. Link sounds and letters to make words: Children are taught in school to quickly see a link \nbetween the phoneme (sounds) and a written representation of that sound (grapheme). At home, \nencourage your child to do the same when playing with fridge magnets in the kitchen, for \nexample, or ‘writing’ when you are writing.\n\nDon’t be scared – make it fun!: Phonics can seem daunting for parents who were probably \ntaught to read in a rather different way. However, simple ga\n\n… [+972 more chars]",
  "content_hash": "a6babdb29ed657e5b8cf15ba6d4bc9edceabfdcc502d50433658db71b8d12993",
  "token_count": 382,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "9609a225-9af5-5530-a97a-e3805ed9fc72",
  "chunk_index": 169,
  "page_number": 131,
  "page_range": [
    131,
    132
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `0ab6f89b-b379-5c90-8804-b6b96a342f21`

- vector: dim=3072 · [-0.0067, 0.0213, -0.0204, -0.0118, 0.0153, 0.0049, -0.0062, -0.0261, …]

```json
{
  "chunk_id": "0ab6f89b-b379-5c90-8804-b6b96a342f21",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Tips can I use to help Children learn to Read?\n\nA. \nTalk to your child:\n\nTalking and singing teach your child the sounds of language, making it easier for him or her to \nlearn how to read. • \nTell family stories about yourself, your child’s grandparents, and other relatives. \n• \nTalk to your child as much as possible about things you are doing and thinking. \n• \nAsk your child lots of questions. \n• \nEncourage your child to tell you what he or she thinks or feels. \n• \nAsk your child to tell you about his or her day – about activities and games played. \n• \nBe patient! Give your child time to find\n\n… [+1342 more chars]",
  "content_hash": "f6fb0bf15ab6414d5f5bfb91f55077a60b564df1cbba5b971805c80ee6bcc158",
  "token_count": 464,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "9609a225-9af5-5530-a97a-e3805ed9fc72",
  "chunk_index": 170,
  "page_number": 132,
  "page_range": [
    132,
    133
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4ad00f71-fc93-5925-9a8a-9291994e0f53`

- vector: dim=3072 · [-0.0045, 0.0140, -0.0107, 0.0147, 0.0205, 0.0038, -0.0096, -0.0038, …]

```json
{
  "chunk_id": "4ad00f71-fc93-5925-9a8a-9291994e0f53",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "He or she will love receiving mail!\n\n110\n\nICDL 2019: Poster\n\nC. \nRead every day: Children love routine, and reading is something that you and your child can look forward to \nevery day. By taking the time to read with your child, you show him or her that reading is \nimportant and fun to do.\n\nTry to read with your child as often as possible. It’s the best thing you can do to help him or her \nlearn at school! It also allows you to spend time together in an enjoyable way and to build a \nstrong and healthy relationship.\n\n• \nStart reading with your child when he or she is a baby. \n• \nSet aside a spe\n\n… [+1420 more chars]",
  "content_hash": "1ede417280bae321aa524a95f7729601b1d6c244b92270de6a4f214f3b9a3afd",
  "token_count": 465,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "9609a225-9af5-5530-a97a-e3805ed9fc72",
  "chunk_index": 171,
  "page_number": 133,
  "page_range": [
    133,
    133
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ebeca47f-db3a-540c-8bc2-9bf3fb094d02`

- vector: dim=3072 · [-0.0054, 0.0357, -0.0161, -0.0168, 0.0178, -0.0199, 0.0044, -0.0155, …]

```json
{
  "chunk_id": "ebeca47f-db3a-540c-8bc2-9bf3fb094d02",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "It also helps enrich your child’s vocabulary with new words and phrases. Here are some \nways to help your child acquire skills in comprehension, reasoning, and critical thinking: • \nAsk your child about the kinds of books he or she would like to read. \n• \nTalk to your child about your favourite books from childhood, and offer to read them. \n• \nEncourage your child to ask questions and to comment on the story and pictures in a book \n– before, during, and after reading it.  \n111\n\nICDL 2019: Poster\n\n• \nLook at the cover and the title of a book with your child, and ask your child what he or \nshe t\n\n… [+884 more chars]",
  "content_hash": "71a9f625aaf434932cd6b552e61ec9b65dff93d307a6e2259ea5151568fdfdd4",
  "token_count": 347,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "9609a225-9af5-5530-a97a-e3805ed9fc72",
  "chunk_index": 172,
  "page_number": 133,
  "page_range": [
    133,
    134
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `b67e1a70-58c5-53e7-abec-a634b41ecfff`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "b67e1a70-58c5-53e7-abec-a634b41ecfff",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Others Who Can Help (cont.)\n\n• \nShow your child that you are enjoying the book by indicating interest and by asking \nquestions. \n• \nGive your child time to figure out tricky words, and show your child how he or she can \nsolve problems. \n• \nTry to have your child read aloud to you at times when there will be no interruptions. \n• \nMake sure that your child selects books that are not too difficult. Don’t worry if the \nbooks your child chooses are a little easier than the ones he or she reads at school. \n• \nEncourage your child to “listen” to his or her own reading. Listening will help your child \n\n… [+8165 more chars]",
  "content_hash": "170b2b7cae7449d788d9833d30dcbf840a26558efbb47918b946316d8feecb17",
  "token_count": 1851,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    134,
    139
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `b4b4f070-31ba-517b-af2f-80f8a8901b24`

- vector: dim=3072 · [0.0199, 0.0338, -0.0098, -0.0060, 0.0108, -0.0005, 0.0073, 0.0058, …]

```json
{
  "chunk_id": "b4b4f070-31ba-517b-af2f-80f8a8901b24",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "• \nShow your child that you are enjoying the book by indicating interest and by asking \nquestions. \n• \nGive your child time to figure out tricky words, and show your child how he or she can \nsolve problems. \n• \nTry to have your child read aloud to you at times when there will be no interruptions. \n• \nMake sure that your child selects books that are not too difficult. Don’t worry if the \nbooks your child chooses are a little easier than the ones he or she reads at school. \n• \nEncourage your child to “listen” to his or her own reading. Listening will help your child \nhear what he or she can do, \n\n… [+1358 more chars]",
  "content_hash": "29abcea4fc3c012b121f36471936bbe2b9c8faec2e59b406e35c460c3b36a6a1",
  "token_count": 438,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "b67e1a70-58c5-53e7-abec-a634b41ecfff",
  "chunk_index": 173,
  "page_number": 134,
  "page_range": [
    134,
    135
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `e10349a8-58a7-53d0-9298-a7904af61875`

- vector: dim=3072 · [0.0194, 0.0211, -0.0186, 0.0009, 0.0042, 0.0292, -0.0005, -0.0004, …]

```json
{
  "chunk_id": "e10349a8-58a7-53d0-9298-a7904af61875",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "One person cannot change the learning culture of the school. For \nthis reason it is important for the school library development work to have a multi-professional \nteam that focuses on the task and represents the needs of the entire school.\n\n1. \nHeadmaster • \nDecides on the budget for the school library \n• \nSupports the development of the school library \n• \nCo-ordinates the further education of the staff \n• \nKeeps in touch with the board of the municipal educational administration \n• \nGuides the drawing up of the school curriculum\n\n2. \nSchool librarian, library-teacher\n\n• \nAcquires and removes\n\n… [+1497 more chars]",
  "content_hash": "fb88963515bec14f5448d8e1c49e5f0e529ce0015127ecd0477774444b797804",
  "token_count": 474,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "b67e1a70-58c5-53e7-abec-a634b41ecfff",
  "chunk_index": 174,
  "page_number": 135,
  "page_range": [
    135,
    136
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `682d83af-b02f-5eb4-97ab-1e891fc456d0`

- vector: dim=3072 · [0.0182, 0.0097, -0.0109, -0.0165, 0.0091, 0.0104, -0.0006, 0.0061, …]

```json
{
  "chunk_id": "682d83af-b02f-5eb4-97ab-1e891fc456d0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "Trusted pupils • \nAct as contact persons between the pupils and the teacher librarian \n• \nParticipate partly in the activities of the school library team \n• \nCarry out assistant duties in the school library \n• \nOrganise exhibitions of the pupils’ work in the school library\n\n7. \nThe board, the parents’ association and the school committee\n\n• \nSupport the development of the school library \n• \nCollect money for the school library \n• \nArrange for visiting authors etc. to support the library activities \n• \nParticipate in the planning of the school library activities \n114\n\nICDL 2019: Poster\n\n• \nDo v\n\n… [+1628 more chars]",
  "content_hash": "63cc42dfc6e68c216e3c31eef70b480278f4840b9fa62dd7bb3fed5dfb91fa23",
  "token_count": 445,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "b67e1a70-58c5-53e7-abec-a634b41ecfff",
  "chunk_index": 175,
  "page_number": 136,
  "page_range": [
    136,
    137
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `97f1144b-436c-50f1-b938-7494c5f900c8`

- vector: dim=3072 · [-0.0030, 0.0257, -0.0161, -0.0188, 0.0064, -0.0049, -0.0060, -0.0130, …]

```json
{
  "chunk_id": "97f1144b-436c-50f1-b938-7494c5f900c8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "The \nbest way to create a reading environment is to provide every child with a desk \nspecifically for reading and study. A simple desk will serve the purpose. b) \nA quiet environment: Provide a quiet reading environment for children. Turn off the \ntelevision or radio for just two hours each evening, or turn the volume down so that \nchildren can read and learn with better concentration.\n\n115\n\nICDL 2019: Poster\n\nc) \nComputers: Plenty of reading materials are available on the Internet. A home \ncomputer not only helps children learn the application, it also broadens their scope of \nreading and dev\n\n… [+1457 more chars]",
  "content_hash": "dd006899b621f7479db23cee66c48363bd0313c201ec1d43a081facdc2b2b5af",
  "token_count": 411,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "b67e1a70-58c5-53e7-abec-a634b41ecfff",
  "chunk_index": 176,
  "page_number": 137,
  "page_range": [
    137,
    138
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a23152dc-f903-5582-92a0-8d9a00024552`

- vector: dim=3072 · [-0.0098, 0.0207, -0.0193, -0.0097, 0.0090, -0.0217, -0.0158, -0.0047, …]

```json
{
  "chunk_id": "a23152dc-f903-5582-92a0-8d9a00024552",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Others Who Can Help",
  "chunk_text": "They \nshould read in their spare time, enjoy talking about books with others, and make reading part of \ntheir daily routines.\n\nB. Encouraging reading: Children of this age group are generally curious. Parents could first encourage them to \nread books they are particularly interested in and then go on to other reading materials. \nTo create more fun for reading, parents can engage children in different kinds of reading \nactivities. For instance, they can take turns to read aloud and then read aloud together, encourage \nchildren to share views on the characters in the story, the plot and the endi\n\n… [+370 more chars]",
  "content_hash": "7055f6dda1e4364d63d3dc4a4d0bc0b41e31e212f7a89bbdd6d2562e5c000ea7",
  "token_count": 194,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "b67e1a70-58c5-53e7-abec-a634b41ecfff",
  "chunk_index": 177,
  "page_number": 138,
  "page_range": [
    138,
    139
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `9c313855-4cbe-57c7-8499-e40dde05a71d`

- vector: dim=3072 · [-0.0089, 0.0147, -0.0168, -0.0097, 0.0262, 0.0060, -0.0168, 0.0190, …]

```json
{
  "chunk_id": "9c313855-4cbe-57c7-8499-e40dde05a71d",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "MYTH",
  "chunk_text": "Myth-11. \nShould parents arrange a large number of extra- curricular activities and \ntutorials for children after school?\n\nA suitable amount of extra-curricular activities can help children develop their multiple \nintelligences. However, it is counter-productive to impose too many on them as children may \nbecome resistant. The development of children’s reading competence will also be affected as \nthere is limited time for leisure reading.\n\nIf tutorial lessons are mere repetitions and drills of what was learned at school, they do no good \nto children’s learning. On the contrary, children’s lear\n\n… [+2026 more chars]",
  "content_hash": "f14250386ba8a80d83187431bd08b54b4854663f99ddf1468c1a50fa2341ac79",
  "token_count": 557,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 178,
  "page_number": 139,
  "page_range": [
    139,
    141
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4c5a58fe-ae03-5f07-bcd0-57ed89a9ad76`

- vector: dim=3072 · [-0.0193, 0.0191, -0.0285, -0.0269, 0.0044, -0.0004, 0.0015, -0.0010, …]

```json
{
  "chunk_id": "4c5a58fe-ae03-5f07-bcd0-57ed89a9ad76",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Abstract",
  "chunk_text": "E- Publishing or Electronic Publishing is a more recent way in which books, short stories, \ncollections and works of non-fiction can be distributed via the Internet and computers in general. \nThe term- electronic publishing is also known as e-publishing, digital publishing, desk top \npublishing, online publishing, web publishing for topical searches. This paper presents a very \nsimplified approach on e- publishing. This paper aims to explore the meaning, concepts, and \nexplanations on the contents of Electronic publishing and also describes the main categories, \nadvantages, limitations and pro\n\n… [+625 more chars]",
  "content_hash": "6e234e4d32509745e9ed44cd2e9e2d34df9759f28b480bc657175e8215151c26",
  "token_count": 228,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 179,
  "page_number": 141,
  "page_range": [
    141,
    141
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `5816f114-2fed-5a45-892b-8c1a17c0f0b9`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "5816f114-2fed-5a45-892b-8c1a17c0f0b9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction\n\nInformation Technology has brought about changes from traditional print to electronic format. \nElectronic publishing (EP), uses new technology to deliver books and other content to readers. \nSince the technology allows publishers to get information to the readers quickly and sufficiently, \nit is causing major changes to the publishing industry and stakeholders in the publishing sector. \nThe application of electronic technology to almost every aspect of human endeavors is on the \nincrease in the modern era of digital information revolution (Oladejo and Adelua, 2012).\n\nInformation \n\n… [+2568 more chars]",
  "content_hash": "f9949f3c816502a4b8742e43b82be2394d62c473d085e554017dc80561011b69",
  "token_count": 590,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    141,
    142
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `b020ccb5-16a0-5eaf-bf64-f2526e924a89`

- vector: dim=3072 · [-0.0283, 0.0285, -0.0231, -0.0077, 0.0134, 0.0009, -0.0153, 0.0039, …]

```json
{
  "chunk_id": "b020ccb5-16a0-5eaf-bf64-f2526e924a89",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Information Technology has brought about changes from traditional print to electronic format. \nElectronic publishing (EP), uses new technology to deliver books and other content to readers. \nSince the technology allows publishers to get information to the readers quickly and sufficiently, \nit is causing major changes to the publishing industry and stakeholders in the publishing sector. \nThe application of electronic technology to almost every aspect of human endeavors is on the \nincrease in the modern era of digital information revolution (Oladejo and Adelua, 2012).\n\nInformation is an intellec\n\n… [+1795 more chars]",
  "content_hash": "a7fbbb02ce9e8e0495104b8b613a3463f4dc815b7d9507f31820c29c11b31875",
  "token_count": 446,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5816f114-2fed-5a45-892b-8c1a17c0f0b9",
  "chunk_index": 180,
  "page_number": 141,
  "page_range": [
    141,
    142
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c4e63402-c596-5bbd-98e9-520c2926cddd`

- vector: dim=3072 · [-0.0161, 0.0194, -0.0376, -0.0021, 0.0200, -0.0043, -0.0320, -0.0166, …]

```json
{
  "chunk_id": "c4e63402-c596-5bbd-98e9-520c2926cddd",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "The media in an \nelectronic publishing can be text, numeric, graphic, still or motion pictures, video, sound or as in \nfrequently the case a combination of  any or all of these. E-publishing can be represented as - Electronic publishing = Electronic technology + computer technology + communication \ntechnology + publishing.\n\nElectronic publishing (e-publishing) deals with the collection, modification and distribution of \ninformation, art and software in any form, such as on physical media or via computer networks. \nE- publishing may be broadly divided into two categories: online and offline pub\n\n… [+372 more chars]",
  "content_hash": "d75166d9f6e828b5089fc1cfddcef8cb61bb447faa7c51ac9789732921b07452",
  "token_count": 192,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5816f114-2fed-5a45-892b-8c1a17c0f0b9",
  "chunk_index": 181,
  "page_number": 142,
  "page_range": [
    142,
    142
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `472473c7-3aa1-5239-888f-3ccb47859f7f`

- vector: dim=3072 · [-0.0255, 0.0273, -0.0194, -0.0350, 0.0012, -0.0004, -0.0058, 0.0215, …]

```json
{
  "chunk_id": "472473c7-3aa1-5239-888f-3ccb47859f7f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Definitions of Electronic Publishing",
  "chunk_text": "When the computer and electronic media are used for the publishing of any intellectual output, it \nis called electronic publishing. F.W. Lancaster (1995) defines Electronic Publishing as “a \npublication process where the manuscripts are submitted in electronic format, edited, printed, \nand even distributed to readers (users) in electronic form by employing computer and \ntelecommunication technology”.\n\nAccording to Encarta Online Dictionary it is the ‘publishing on computer network or disk: the \nproduction of documents in computer-readable form for distribution over a computer network or \nin ot\n\n… [+1652 more chars]",
  "content_hash": "5432169513ccf4af5657b785c4f79cd3e9bbfddc317401d5012135145584a82c",
  "token_count": 427,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 182,
  "page_number": 142,
  "page_range": [
    142,
    143
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `1dee6533-a05d-51cb-bf68-260821e4f735`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1dee6533-a05d-51cb-bf68-260821e4f735",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Methodology",
  "chunk_text": "Methodology\n\nThis is a desktop research and literatures were reviewed using core keywords for the literature \nsearch. To ensure that all concepts were included within publishing, the following general related \nterms, were used as core keywords for all literature searches publishing combined with any of \nthe following terms; digital, web, Internet and electronic. For example electronic publishing, web \npublishing, digital publishing etc. The literature searches were conducted using online databases \n(Library and Information Science Abstracts (LISA), Science direct, Ebscohost, Emerald, Google \ns\n\n… [+6203 more chars]",
  "content_hash": "a3a3ff150169e8eb188e1250aed5cac7f2b39a6a65b9c37ee3a949ea31274396",
  "token_count": 1412,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    143,
    145
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6f10acf5-f2ae-56c2-9a1b-9413d86f0759`

- vector: dim=3072 · [0.0048, 0.0539, -0.0241, -0.0149, 0.0064, 0.0071, 0.0129, 0.0253, …]

```json
{
  "chunk_id": "6f10acf5-f2ae-56c2-9a1b-9413d86f0759",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Methodology",
  "chunk_text": "This is a desktop research and literatures were reviewed using core keywords for the literature \nsearch. To ensure that all concepts were included within publishing, the following general related \nterms, were used as core keywords for all literature searches publishing combined with any of \nthe following terms; digital, web, Internet and electronic. For example electronic publishing, web \npublishing, digital publishing etc. The literature searches were conducted using online databases \n(Library and Information Science Abstracts (LISA), Science direct, Ebscohost, Emerald, Google \nscholar) avail\n\n… [+1151 more chars]",
  "content_hash": "fff79f2801196ac927b7e39d02fd7b1c9e2d73707d96f28e7b67e9622a0d469a",
  "token_count": 318,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1dee6533-a05d-51cb-bf68-260821e4f735",
  "chunk_index": 183,
  "page_number": 143,
  "page_range": [
    143,
    144
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5ea58b9c-e39f-54f9-88de-3f06750635f2`

- vector: dim=3072 · [-0.0014, 0.0126, -0.0261, -0.0280, -0.0116, 0.0145, 0.0081, 0.0223, …]

```json
{
  "chunk_id": "5ea58b9c-e39f-54f9-88de-3f06750635f2",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Methodology",
  "chunk_text": "latest research, or research that has not been \npublished\n\nGenesis, Development and Evolution of Electronic Publishing\n\nThe fusion of electronics, computer and communication technologies together for publishing can \nbe termed as electronic publishing to denote any information source published in electronic form. \n121\n\nICDL 2019: Poster ARPANET, the forerunner of the Internet were created more than forty years ago in 1969 by \nresearchers at the University of California Los Angeles, University of California Santa Barbara, \nStanford Research Institute and the University of Utah. Even in the early\n\n… [+1247 more chars]",
  "content_hash": "6b49ff0e10a046e9b0e8710ca5f3dae0c965afb762f17d9047b897cf002b5669",
  "token_count": 394,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1dee6533-a05d-51cb-bf68-260821e4f735",
  "chunk_index": 184,
  "page_number": 144,
  "page_range": [
    144,
    144
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `2264ec43-03d0-531c-b4d9-b1f3168a619b`

- vector: dim=3072 · [0.0076, 0.0238, -0.0247, -0.0225, -0.0245, 0.0038, -0.0063, 0.0160, …]

```json
{
  "chunk_id": "2264ec43-03d0-531c-b4d9-b1f3168a619b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Methodology",
  "chunk_text": "It was Michael Hart who envisioned the idea that computers could \nindefinitely reproduce anything that was entered and stored for future retrieval. Subsequently, there have been many offspring of his original idea leading to what was termed \nElectronic Texts. A Gutenberg Philosophy has evolved which strives toward “making \ninformation, books and other materials available to the general public in forms a vast majority of \nthe computer, programs and people can easily read, use, quote and search”. \n(http://promo.net/pg/history.html). The first e-book was published in 1985 in Germany and since \nth\n\n… [+1451 more chars]",
  "content_hash": "2bd3be5819179ea131ec3999db533126dd8d3f1870ff660673efdc04787d97d2",
  "token_count": 433,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1dee6533-a05d-51cb-bf68-260821e4f735",
  "chunk_index": 185,
  "page_number": 144,
  "page_range": [
    144,
    145
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c5382c67-08be-51aa-bc25-34705c146612`

- vector: dim=3072 · [-0.0091, 0.0239, -0.0371, -0.0114, 0.0040, 0.0110, -0.0097, 0.0233, …]

```json
{
  "chunk_id": "c5382c67-08be-51aa-bc25-34705c146612",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Methodology",
  "chunk_text": "The use of electronics to print on paper is not a \ncompletely pedestrian application since it allows new capabilities such as printing on \ndemand and even the production of customized publications tailored to individual needs.\n\n122\n\nICDL 2019: Poster  The distribution of text in electronic form, where the electronic version is the exact \nequivalent of a paper version and may have been used to generate the paper version. For \nsecondary publications (indexing and abstracting services), electronic distribution began \nearly in the 1960s. For primary journals, the development occurred somewhat lat\n\n… [+1272 more chars]",
  "content_hash": "16fe65903f78dec967223089e58a6c6683a28b00442a1dc496290e868ad43b23",
  "token_count": 396,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "1dee6533-a05d-51cb-bf68-260821e4f735",
  "chunk_index": 186,
  "page_number": 145,
  "page_range": [
    145,
    145
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `dc1a6010-02c0-56df-9552-a8ee31685aaf`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "dc1a6010-02c0-56df-9552-a8ee31685aaf",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Process of E-Publishing",
  "chunk_text": "Process of E-Publishing\n\nThe stages of electronic publishing are similar to the process of traditional print publishing in \nmany ways but there are some variations that consist of eight steps:\n\n Content creation: Content creation is the first step in electronic publishing. The creator \nmay be researchers, scholars or authors. The content of e-publication can be in various \nform and format – text, graphics, image, video, audio or combination of all these. \nHyperlink and hypermedia can be given to a file within or external.\n\n Manuscript Submission: digitally created manuscript will be submitte\n\n… [+3974 more chars]",
  "content_hash": "24ade79115dff51cb8697516731f1381e102205b86664b8a63ca183c2f06aa85",
  "token_count": 890,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    145,
    147
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `90ce71ff-29ad-58d0-8295-05e8fdc00a78`

- vector: dim=3072 · [-0.0199, -0.0027, -0.0266, -0.0237, 0.0087, -0.0016, 0.0120, 0.0232, …]

```json
{
  "chunk_id": "90ce71ff-29ad-58d0-8295-05e8fdc00a78",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Process of E-Publishing",
  "chunk_text": "The stages of electronic publishing are similar to the process of traditional print publishing in \nmany ways but there are some variations that consist of eight steps:\n\n Content creation: Content creation is the first step in electronic publishing. The creator \nmay be researchers, scholars or authors. The content of e-publication can be in various \nform and format – text, graphics, image, video, audio or combination of all these. \nHyperlink and hypermedia can be given to a file within or external.\n\n Manuscript Submission: digitally created manuscript will be submitted to the publisher \nvia e\n\n… [+1463 more chars]",
  "content_hash": "0855e13f568be4636a46fe24922ec8b08878331a93301c2602e202e14af6eeda",
  "token_count": 412,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "dc1a6010-02c0-56df-9552-a8ee31685aaf",
  "chunk_index": 187,
  "page_number": 145,
  "page_range": [
    145,
    146
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `261a037c-117c-52d0-b8b1-5f71753abbc8`

- vector: dim=3072 · [-0.0257, 0.0063, -0.0236, -0.0188, -0.0049, 0.0001, -0.0180, 0.0129, …]

```json
{
  "chunk_id": "261a037c-117c-52d0-b8b1-5f71753abbc8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Process of E-Publishing",
  "chunk_text": "The publisher takes care of content compatibility because the users may not \nuse the same device and software to read the content, for example the text should be \nreadable at desktop computer as well as Kindle e-book reader.  Production and distribution/ publishing: production is an important stage like in print \npublishing. E-publications are available both online and offline. In case of online the \ncontent will be uploaded in the respective web site on local network whichever is \nselected. For offline publication, digital storage media like CD-ROM or DVD are used. \nOnline publishing is easi\n\n… [+2109 more chars]",
  "content_hash": "7298135baed2b725b93f930e91f04694055f3772ad4a8ec361342b7d58bd5818",
  "token_count": 515,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "dc1a6010-02c0-56df-9552-a8ee31685aaf",
  "chunk_index": 188,
  "page_number": 146,
  "page_range": [
    146,
    147
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a665c2ae-5e3d-535d-8c67-b0cf2e1e80eb`

- vector: dim=3072 · [-0.0204, 0.0121, -0.0309, -0.0201, 0.0021, -0.0008, -0.0011, 0.0048, …]

```json
{
  "chunk_id": "a665c2ae-5e3d-535d-8c67-b0cf2e1e80eb",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Characteristics of Electronic Publishing",
  "chunk_text": "Wilson (1997) enlists the characteristics of electronic publishing as follows:\n\n Electronic publications can be produced and disseminated very rapidly - once a page of \ntext has been coded with HTML tags it can be published immediately.\n\n If correction is necessary, an electronic text can be updated or corrected with the same \nimmediacy, whereas a book must either go through a second edition, or, if the error is \ncaught in time, have an erratum slip inserted;\n\n Electronic publication can be made collaborative and interactive, involving either several \n\"authors\" or authors and readers;\n\n El\n\n… [+1788 more chars]",
  "content_hash": "0f79336cc80ab8edfefea2bef6edf451e568434871b0b470d6e8637b1f15880f",
  "token_count": 460,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 189,
  "page_number": 147,
  "page_range": [
    147,
    148
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `86dd5c56-646c-5ea9-9d14-63e5301eefd3`

- vector: dim=3072 · [-0.0097, 0.0056, -0.0253, -0.0324, 0.0054, 0.0076, -0.0183, 0.0046, …]

```json
{
  "chunk_id": "86dd5c56-646c-5ea9-9d14-63e5301eefd3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Electronic books",
  "chunk_text": "Borchers (1999) defines an eBook as a portable hardware and software system that can display \nlarge quantity of readable textual information to the user and let the user navigate through this \ninformation. An eBook is digital reading material that a user can view on a desktop or notebook \npersonal computer, or on a dedicated, portable device with a large storage capacity (1,500 to \n50,000 pages) and the ability to download new titles via a network connection required hard \nware. The reader hardware is expensive, e-titles cost about the same as their print counterparts, \nink and paper are still\n\n… [+746 more chars]",
  "content_hash": "2d989387caae3d5dab831effbc798db72064e63187aba355dae08ed405bb7bb7",
  "token_count": 284,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 190,
  "page_number": 148,
  "page_range": [
    148,
    148
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `131dbe30-6454-5398-9cd5-50fda82b70e3`

- vector: dim=3072 · [-0.0268, 0.0418, -0.0368, -0.0169, 0.0149, 0.0047, -0.0080, 0.0121, …]

```json
{
  "chunk_id": "131dbe30-6454-5398-9cd5-50fda82b70e3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Electronic periodicals",
  "chunk_text": "Electronic journal (or e-journal) is defined as any journal, magazine, e-zine, webzine, newsletter \nor type of electronic serial publication which is available over the Internet and can be accessed \nusing different technologies (Arora, 2001). Electronic Periodicals are accessible to all users \nregardless of geographic location. Anyone in the world with services and the proper computer \nsoftware and browser services can access online journals. This accessibility leads to a more \ndiverse audience throughout the world as well as a readership that may include not only \nacademics, but students and \n\n… [+50 more chars]",
  "content_hash": "88eb1b2fa6d8207aa7e4f27bcc969abe233ba91b51649f05b911b89899864078",
  "token_count": 142,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 191,
  "page_number": 148,
  "page_range": [
    148,
    149
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `489616a9-0b76-5a0d-93b1-ccd423940aa3`

- vector: dim=3072 · [-0.0166, 0.0127, -0.0275, -0.0008, 0.0206, -0.0159, -0.0062, -0.0034, …]

```json
{
  "chunk_id": "489616a9-0b76-5a0d-93b1-ccd423940aa3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Electronic databases",
  "chunk_text": "With the influx of computers and communication technologies, the strength of information \nsystem in the development of modern database has taken a new dimension. The stocks of the \nlibrary database consisting of books, periodicals, reports and theses can be converted to \nelectronic form that allows access for public use through digital networks. A variety of electronic \ndatabase publishers today account for publishing information both bibliographic and full text on \nCD-ROMs as well as making them available for On-line retrieval. The prominent On-line \npublishers include DIALOG, EBSCO host etc.\n\n… [+776 more chars]",
  "content_hash": "be211fed7966bf28e59ba9ae1e790d05a425a5340aea81143b0da85d07805068",
  "token_count": 279,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 192,
  "page_number": 149,
  "page_range": [
    149,
    149
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d75bba92-3b78-5961-97e9-448cada6f25e`

- vector: dim=3072 · [-0.0500, -0.0096, -0.0321, 0.0013, -0.0218, -0.0212, 0.0068, 0.0092, …]

```json
{
  "chunk_id": "d75bba92-3b78-5961-97e9-448cada6f25e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Print-on-Demand (POD)",
  "chunk_text": "Print-on-Demand is a new method for printing books (and other content) which allows books to \nbe printed one at a time, or on demand. It is a mix of electronic and print publishing .i.e. (print on \ndemand combines the Internet with more traditional publishing methods). The book is held by \nthe publisher in electronic form and is printed out in the hard copy form only on order. This \nmethod helps free publishers from the process of doing a traditional print run of several thousand \nbooks at a time. Print on demand thereby “eliminates the need for editions to be printed \nbeforehand, greatly redu\n\n… [+202 more chars]",
  "content_hash": "d08dda6f22f3da752777d11350a3f813dbee662732b874fffbe57c2a6198f479",
  "token_count": 172,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 193,
  "page_number": 149,
  "page_range": [
    149,
    149
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `dc1832f2-dd86-5d98-ad41-379e73cb9854`

- vector: dim=3072 · [-0.0153, 0.0224, -0.0268, -0.0169, 0.0033, 0.0114, 0.0163, -0.0006, …]

```json
{
  "chunk_id": "dc1832f2-dd86-5d98-ad41-379e73cb9854",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Digital content",
  "chunk_text": "Digital content generally refers to the electronic delivery of fiction that is shorter than book- \nlength, nonfiction, and other written works of shorter length. Publishers of digital content deliver \nshorter sized works to the consumer via download to handheld and other wireless devices. \nTechnology used for delivering digital content includes portable document file (PDF), hypertext \nmarkup language (XML), WAP (Wireless Application Protocol) and other technologies. The \nsecurity of the data being delivered is the major concern of publishers, who want to ensure they \ncan deliver digital conten\n\n… [+124 more chars]",
  "content_hash": "1c9fe63951d99e1022fed270109ef677e4951ffe53d2b0cfe12b6e1f17742f6b",
  "token_count": 145,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 194,
  "page_number": 149,
  "page_range": [
    149,
    150
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `b4c55b9f-5161-5baa-9b61-e4d17f053e13`

- vector: dim=3072 · [-0.0149, -0.0102, -0.0301, -0.0360, 0.0193, 0.0056, -0.0051, 0.0099, …]

```json
{
  "chunk_id": "b4c55b9f-5161-5baa-9b61-e4d17f053e13",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Electronic ink",
  "chunk_text": "Electronic Ink is a developing technology that has a huge impact on the media and publishing \nindustries. Electronic Ink could be used to create a newspaper or book that updates itself. It is a \nhigh-contrast reflective display ideal for e-book applications. In addition, this content could be \nprogrammed to change at any time. For example, you could have a billboard that rotates different \nadvertisements, or you could receive a coupon in the mail that is frequently updated with the \nlatest offer. For media companies, the possibilities are almost endless. Someday, electronic \nnewspaper will sim\n\n… [+675 more chars]",
  "content_hash": "049bf5c1f0d29ebc5aad1d5e5552a7ae4809fe5cf3a30d868cc7ed3c4d58a332",
  "token_count": 253,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 195,
  "page_number": 150,
  "page_range": [
    150,
    150
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `7c153c03-dc68-5d08-a5c2-e31a64094c7b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "7c153c03-dc68-5d08-a5c2-e31a64094c7b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Web publishing",
  "chunk_text": "Web publishing\n\nWeb publishing is not a novel practice any longer, but it continues to change and develop with \nthe introduction of new programming languages. Hypertext Markup Language (HTML) is still \nthe most widely used web programming language, but Extensible Markup Language (XML) is \nalso making headway. XML is valuable because it allows publishers to create content and data \nthat is portable to other devices. Nearly every company in the world has some types of website, \nand most media companies provide a large amount of web based content (Saxena, 2009).\n\nAdvantages of E-Publishing:\n\nFoll\n\n… [+4352 more chars]",
  "content_hash": "b0ac8bb828a443abfcb159e1337d88b4763ae6cfd20b82b4fbe4622e750090ca",
  "token_count": 972,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    150,
    152
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5921e81e-25b1-5e4d-971e-ffe88c9bf468`

- vector: dim=3072 · [-0.0358, 0.0341, -0.0248, -0.0082, 0.0139, 0.0106, 0.0142, 0.0019, …]

```json
{
  "chunk_id": "5921e81e-25b1-5e4d-971e-ffe88c9bf468",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Web publishing",
  "chunk_text": "Web publishing is not a novel practice any longer, but it continues to change and develop with \nthe introduction of new programming languages. Hypertext Markup Language (HTML) is still \nthe most widely used web programming language, but Extensible Markup Language (XML) is \nalso making headway. XML is valuable because it allows publishers to create content and data \nthat is portable to other devices. Nearly every company in the world has some types of website, \nand most media companies provide a large amount of web based content (Saxena, 2009).\n\nAdvantages of E-Publishing:\n\nFollowing are the ma\n\n… [+1409 more chars]",
  "content_hash": "3b62128efd1bdcd591e78663f8bab2b7b8fff412773ae8bdb352a53ccbaf506c",
  "token_count": 405,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7c153c03-dc68-5d08-a5c2-e31a64094c7b",
  "chunk_index": 196,
  "page_number": 150,
  "page_range": [
    150,
    151
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `94f56575-965d-56bd-8226-964406e2eb26`

- vector: dim=3072 · [-0.0299, 0.0233, -0.0199, -0.0155, -0.0114, 0.0029, 0.0131, -0.0013, …]

```json
{
  "chunk_id": "94f56575-965d-56bd-8226-964406e2eb26",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Web publishing",
  "chunk_text": "This leads to further reducing the gap between the author and the \nend-user.\n\n Distribution: The major advantages of e journals are their global distribution, their \nhyperlinks, and the ability to access from different sites and ability to search.  Retrieval: There are a good number of search engines available to access and retrieve the \nappropriate articles. Most of the publishers of E journals are providing keywords, author \nsearch, terms reducing the role of additional indexing and abstracting.\n\n Multiple Accesses: Most of the publishers of E journals are coming up with site license \npol\n\n… [+1494 more chars]",
  "content_hash": "724bd8f6ff3d8d556338adc3aef21fa913221e66b96311e953e9b03633c57a71",
  "token_count": 405,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7c153c03-dc68-5d08-a5c2-e31a64094c7b",
  "chunk_index": 197,
  "page_number": 151,
  "page_range": [
    151,
    152
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a4a8e10c-73c0-598a-9b19-e27479076cf1`

- vector: dim=3072 · [-0.0427, 0.0214, -0.0332, -0.0072, -0.0240, -0.0069, 0.0259, -0.0084, …]

```json
{
  "chunk_id": "a4a8e10c-73c0-598a-9b19-e27479076cf1",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Web publishing",
  "chunk_text": "Electronic Publishing and its Role in Libraries: Definition of a library is an institution that selects, acquire, organize, and provide access to \nrecord knowledge. This is obviously a very broad definition, but both the collecting ad \norganizing aspect of librarianship is threatened by electronic publishing. When it becomes \ncheaper to offer patrons access to material that is stored electronic ally than on paper, then \nelectronic access will rapidly become accepted, in spite of many limitations it has. One of the \nprimary characteristics of scholarly publishing is that he use of any particula\n\n… [+527 more chars]",
  "content_hash": "d9ee66d221ecf5e9e6a56d201745c00dfb5d05c5b1bd865d6a74f878c5b8c690",
  "token_count": 216,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7c153c03-dc68-5d08-a5c2-e31a64094c7b",
  "chunk_index": 198,
  "page_number": 152,
  "page_range": [
    152,
    152
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `9c182346-8859-541d-9d35-7e6f40429383`

- vector: dim=3072 · [-0.0234, 0.0103, -0.0253, -0.0321, -0.0008, -0.0047, -0.0104, 0.0166, …]

```json
{
  "chunk_id": "9c182346-8859-541d-9d35-7e6f40429383",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Conclusion",
  "chunk_text": "Electronic publishing has created a revolution in publishing industry. By now, they have \nreceived adequate acceptance among the users. During the past one decade, they have become \nquite popular, particularly for scientific and scholarly communication. Electronic publishing has \nled to a boom of online publishing by 'self author' and 'self-publisher' brought about Internet and \nWorld Wide Web. Drawbacks to this boom include the flexibility of copying, lack of style, \nuniformity and standardization etc. Emergence of self-publishing, combined with lack of \nconsistency and quality has led many t\n\n… [+814 more chars]",
  "content_hash": "5a7bd1c07c8e533d82ee400c9c03ce6409f34a9d78b758a631b5c87d7b27b6ed",
  "token_count": 257,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 199,
  "page_number": 152,
  "page_range": [
    152,
    152
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `5b7d4c4b-57fa-55fa-a4dc-41db47f9cd4e`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "5b7d4c4b-57fa-55fa-a4dc-41db47f9cd4e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Reference",
  "chunk_text": "Reference\n\n \nAnderson, K & Dresselhaus, A. (2011). Publishing 2.0: How the internet changes publications in society. \nThe Serials Librarian, 60, 23-36.\n\n \nBrownrigg, E. B., & Lynch, C. (1985). Electrons, Electronic Publishing, and Electronic \n130\n\nICDL 2019: Poster\n\n \nChandrakar, R. (2006). Electronic publishing model for Indian academic journals. Proceedings of \nInternational Conference on Digital Libraries, (pp. 412-421). New Delhi.\n\n \nDash, S, & Panda, KC (2006). E-Publishing: A Challenge for the contemporary.\n\n \nDisplay. Information Technology and Libraries, 4(3), 201-207.\n\n \nEducati\n\n… [+2794 more chars]",
  "content_hash": "0133e2af5e28c6887b1b7f0a9cf193ccdd9ab72c1a60f2ab69bb37d9682518d3",
  "token_count": 1015,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    152,
    155
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `847ecd54-a613-5457-b9b3-4ec8028d4027`

- vector: dim=3072 · [-0.0248, 0.0260, -0.0156, 0.0127, -0.0015, -0.0054, -0.0041, 0.0256, …]

```json
{
  "chunk_id": "847ecd54-a613-5457-b9b3-4ec8028d4027",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Reference",
  "chunk_text": " \nAnderson, K & Dresselhaus, A. (2011). Publishing 2.0: How the internet changes publications in society. \nThe Serials Librarian, 60, 23-36.\n\n \nBrownrigg, E. B., & Lynch, C. (1985). Electrons, Electronic Publishing, and Electronic \n130\n\nICDL 2019: Poster\n\n \nChandrakar, R. (2006). Electronic publishing model for Indian academic journals. Proceedings of \nInternational Conference on Digital Libraries, (pp. 412-421). New Delhi.\n\n \nDash, S, & Panda, KC (2006). E-Publishing: A Challenge for the contemporary.\n\n \nDisplay. Information Technology and Libraries, 4(3), 201-207.\n\n \nEducational Techno\n\n… [+751 more chars]",
  "content_hash": "a8bb350b0a8750267aed47befce02677eb2d4f7307f8cccd931878f0c0e1a5d0",
  "token_count": 443,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5b7d4c4b-57fa-55fa-a4dc-41db47f9cd4e",
  "chunk_index": 200,
  "page_number": 152,
  "page_range": [
    152,
    153
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `54e80340-6fc3-5d5f-a153-b305773e9b18`

- vector: dim=3072 · [-0.0162, 0.0202, -0.0107, 0.0029, 0.0031, 0.0178, 0.0024, 0.0268, …]

```json
{
  "chunk_id": "54e80340-6fc3-5d5f-a153-b305773e9b18",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Reference",
  "chunk_text": "20, \n2019)\n\n \nhttps://www.researchgate.net/publication/283433308_Electronic_Publishing_A_Powerful \n_Tool_for_Academic_Institutions_in_the_Electronic_Environment (Accessed on August 14, 2019)  \nHunter, K. (1994). Issues and Experiments in Electronic Publishing and Dissemination.Information \nTechnology and Libraries, 13(2), 127-132.\n\n \nLancaster, F. W. (1982). Libraries and Librarians in an Age of Electronics. Washington, D.C.: Information \nResources Press.\n\n \nLancaster, FW (1995). The evolution of electronic publishing. Library trend, 43 (4), 518-527.\n\n \nlibraries. In Anandan, C, Gangathar\n\n… [+1093 more chars]",
  "content_hash": "c387fbb9dc638ab8a8f40e7112040e7db3d8458ab4d40cc5ad24c270dcfe2926",
  "token_count": 490,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5b7d4c4b-57fa-55fa-a4dc-41db47f9cd4e",
  "chunk_index": 201,
  "page_number": 153,
  "page_range": [
    153,
    154
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d1b6b291-000f-50c6-b475-dc40e23bcc23`

- vector: dim=3072 · [0.0016, 0.0294, -0.0193, 0.0240, -0.0063, 0.0369, -0.0074, 0.0293, …]

```json
{
  "chunk_id": "d1b6b291-000f-50c6-b475-dc40e23bcc23",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Reference",
  "chunk_text": "Amherst Jct.\n\n131\n\nICDL 2019: Poster\n\n \nWills, M and Wills, G (1996). The Ins and Outs of electronic publishing. Internet Research: Electronic \nNetworking applications and Policy, 6 (1), 10-21  \nZhao, J L & Resh, V H (2001). Internet publishing and transformation of knowledge process.\n\n \nCommunications of the ACM, 44 (12), December.\n\n132\n\nICDL 2019: Poster\n\nCampus TV Through Digital Library: A Never-\nending Possibility for Knowledge Streaming\n\nShafiqunnabee Samadi\n\nProfessor, Dept. of Bangla & Former Administrator (Librarian-in-Charge), Rajshahi University \nCentral Library, Rajshahi, Bangla\n\n… [+121 more chars]",
  "content_hash": "7bea87d22e106bb90c6997486ae8045a07659615c7db268c94fd02a01c0ce45a",
  "token_count": 197,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "5b7d4c4b-57fa-55fa-a4dc-41db47f9cd4e",
  "chunk_index": 202,
  "page_number": 154,
  "page_range": [
    154,
    155
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `55a9648b-9f21-5d4a-957e-6da280fad190`

- vector: dim=3072 · [-0.0278, 0.0446, -0.0177, 0.0027, 0.0122, 0.0079, -0.0130, 0.0169, …]

```json
{
  "chunk_id": "55a9648b-9f21-5d4a-957e-6da280fad190",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Abstract",
  "chunk_text": "Knowledge streaming through digital process is very important now a days for a country like \nBangladesh. Rajshahi University Central Library has identified this mater five years back. Now \nRajshahi University Central Library has complete setup of digital operation and RFID system for \nthe security purpose and sharper usage of the library. We have to keep it in our mind that audio \nvisual knowledge streaming  is more effective than the older techniques.  In this connection we \ncan set up a Campus TV network. Rajshahi University already has a Fiber Optics Backbone \nLocal Area Network (LAN) all o\n\n… [+1306 more chars]",
  "content_hash": "b64c6fa0fb61e1caba1fda48d83591e49530abc21b2c6cd0578825ac44843806",
  "token_count": 372,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 203,
  "page_number": 155,
  "page_range": [
    155,
    156
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `34f88fcc-b867-57cb-b65a-b71759ca38b8`

- vector: dim=3072 · [-0.0270, 0.0573, -0.0134, -0.0220, 0.0148, -0.0057, -0.0091, 0.0101, …]

```json
{
  "chunk_id": "34f88fcc-b867-57cb-b65a-b71759ca38b8",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Libraries are synonymous with education and offer countless learning opportunities that can fuel \neconomic, social and cultural development. As an information centre library can provide \ndifferent types of learning resources to its users. There are  different types of users in a library \nbut some of them are not able to access resources of a library due to their different disabilities so, \nas an information centre the environment of a library should be a barrier free. The term ‘barrier-\nfree’ indicates an environment where all users irrespective of their physical disadvantages can \nenter, use \n\n… [+606 more chars]",
  "content_hash": "e4574f6e14f75111c50dad3d82d5144a1af8a578db95fce2a17e22ac1cde59c0",
  "token_count": 232,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 204,
  "page_number": 156,
  "page_range": [
    156,
    157
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `ea2f7490-1276-5027-b619-89ab980707ca`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ea2f7490-1276-5027-b619-89ab980707ca",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Indian Scenario",
  "chunk_text": "Indian Scenario\n\nAs per the Census 2011, in India out of the 121 Cr population, 2.68 Cr persons are ‘disabled’ \nwhich is 2.21% of the total population.\n\nPopulation ,India 2011 \nDisabled persons, India 2011 \nPersons \nMales \nFemales \nPersons \nMales \nFemales \n121.08 Cr \n62.32 Cr \n58.76 Cr \n2.68 Cr \n1.5 Cr \n1.18 Cr\n\nIndia is trying to empower its disabled citizens. All possible support is being provided to the \npersons with disabilities either by enacting a special Act, or by executing a ‘National Policy for \nPersons with Disabilities, 2006’, or by providing reservations in education, employment, \n\n… [+5597 more chars]",
  "content_hash": "4ef550afd11a1174be180953b2fe1eef5d16d09a4133cb19620ef36e1e3d4019",
  "token_count": 1310,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    157,
    159
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `dac57561-6ea0-53fe-9468-d96b7a49dbba`

- vector: dim=3072 · [-0.0520, 0.0192, 0.0050, 0.0024, 0.0338, 0.0057, -0.0150, 0.0061, …]

```json
{
  "chunk_id": "dac57561-6ea0-53fe-9468-d96b7a49dbba",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Indian Scenario",
  "chunk_text": "As per the Census 2011, in India out of the 121 Cr population, 2.68 Cr persons are ‘disabled’ \nwhich is 2.21% of the total population.\n\nPopulation ,India 2011 \nDisabled persons, India 2011 \nPersons \nMales \nFemales \nPersons \nMales \nFemales \n121.08 Cr \n62.32 Cr \n58.76 Cr \n2.68 Cr \n1.5 Cr \n1.18 Cr\n\nIndia is trying to empower its disabled citizens. All possible support is being provided to the \npersons with disabilities either by enacting a special Act, or by executing a ‘National Policy for \nPersons with Disabilities, 2006’, or by providing reservations in education, employment, \ngovernment schem\n\n… [+1437 more chars]",
  "content_hash": "939299be3202e73984db92a41f5d812fa7fbb27625348f91116b7e1989ba9e61",
  "token_count": 419,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ea2f7490-1276-5027-b619-89ab980707ca",
  "chunk_index": 205,
  "page_number": 157,
  "page_range": [
    157,
    157
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `3f66c196-7932-56b8-81a8-061760b0e0af`

- vector: dim=3072 · [-0.0324, 0.0276, 0.0047, 0.0029, 0.0231, -0.0079, -0.0047, 0.0189, …]

```json
{
  "chunk_id": "3f66c196-7932-56b8-81a8-061760b0e0af",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Indian Scenario",
  "chunk_text": "National Policy for Persons with Disabilities, 2006 The National Policy for Persons with Disabilities, 2006 recognizes persons with disabilities as \nvaluable human resource for the country and seeks to create an environment that provides those \nequal opportunities, protection of their rights and full participation in society. The policy focus \non the following aspects:\n\n1. Prevention of Disabilities: In Large number of cases disability is preventable; there is \nstrong emphasis on prevention of disabilities. Programme for prevention of diseases, \nwhich result in disability and the creation of a\n\n… [+937 more chars]",
  "content_hash": "f04b0b62bf4e9870192217a4c896345723c223eb23749ebc0a2e97701cc9fcd6",
  "token_count": 331,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ea2f7490-1276-5027-b619-89ab980707ca",
  "chunk_index": 206,
  "page_number": 157,
  "page_range": [
    157,
    158
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `414f70ca-b95a-56fe-8938-db5322a93b0a`

- vector: dim=3072 · [-0.0385, 0.0283, -0.0165, -0.0126, 0.0131, -0.0106, 0.0108, -0.0208, …]

```json
{
  "chunk_id": "414f70ca-b95a-56fe-8938-db5322a93b0a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Indian Scenario",
  "chunk_text": "It will also \ninclude development of rehabilitation professionals; Educational rehabilitation including \nvocational education; and economic rehabilitation for a dignified life in society.\n\nLibrary services for persons with disabilities All library collections and materials should properly be accessible for all persons with \ndisabilities, till today depend on two primary sources for information, i.e. Braille Books; and \nTalking book service. Libraries should acquire Assistive technology to facilitate information \nexchange, resource-sharing among different libraries for the purpose of serving pe\n\n… [+1447 more chars]",
  "content_hash": "ab276b532a7656468b42b104a5fd5926d0e70d57e6b6ea596d5068e1b8b64422",
  "token_count": 395,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ea2f7490-1276-5027-b619-89ab980707ca",
  "chunk_index": 207,
  "page_number": 158,
  "page_range": [
    158,
    158
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4182407c-66a9-5edf-b779-ba9a922e8257`

- vector: dim=3072 · [-0.0204, 0.0236, -0.0149, 0.0140, 0.0260, 0.0011, 0.0045, 0.0020, …]

```json
{
  "chunk_id": "4182407c-66a9-5edf-b779-ba9a922e8257",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Indian Scenario",
  "chunk_text": "� Telecommunication devices\nCognitive disabilities \n Books in enlarged print \n High interest, low-vocabulary materials and books. \n Spoken word collections \n Books on tape and text kits \n Audio and video tape in daisy format \n136 |  | Types of disabilities |  | Library services |  |\n| --- | --- | --- | --- | --- |\n|  | Print disabilities |  | Talking books   Audio magazines and newspaper Large print books  Computer files of text   Audio descriptive videos Braille and other tactile materials  |  |\n|  | Deaf or hearing impairment |  | Books and pamphlets on sign language, dictionarie\n\n… [+477 more chars]",
  "content_hash": "1940e5f8aee28e31fe3e7144bea02dadd5968c7e069b958d76662b6dc5b246b2",
  "token_count": 265,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "ea2f7490-1276-5027-b619-89ab980707ca",
  "chunk_index": 208,
  "page_number": 158,
  "page_range": [
    158,
    159
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `68e76712-b4a2-50d1-8dcc-acd974149294`

- vector: dim=3072 · [-0.0291, 0.0423, -0.0199, -0.0422, 0.0262, 0.0107, 0.0100, -0.0158, …]

```json
{
  "chunk_id": "68e76712-b4a2-50d1-8dcc-acd974149294",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Assistive or Adaptive Technology",
  "chunk_text": "Assistive technologies (ATs) that refers to assistive, adaptive rehabilitative devices, products, or \nequipment for helping people with disabilities. ATs assist individuals in communication, \neducation, work, and recreation and enhance quality of life. Assistive technologies offer \nindependence by enabling people with disabilities to perform tasks which they were formerly \nunable to accomplish.\n\nTypes of some Assistive technology\n\nText-to-speech software: Text-to-speech software enables computer to read aloud web pages, \ntext documents, emails and PDF documents in a natural sounding voice. Exa\n\n… [+1512 more chars]",
  "content_hash": "0aea3afde77689673fdcbf9c1482fda7bd7654735646c7f2a348fbf1f598596e",
  "token_count": 432,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 209,
  "page_number": 159,
  "page_range": [
    159,
    160
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `18ae9647-28df-5217-9265-c299d1fead10`

- vector: dim=3072 · [-0.0131, 0.0395, -0.0190, -0.0153, 0.0298, 0.0231, 0.0195, 0.0238, …]

```json
{
  "chunk_id": "18ae9647-28df-5217-9265-c299d1fead10",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Dolphin SuperNova",
  "chunk_text": "138\n\nICDL 2019: Poster\n\nNote-taking support: There is a wide range of note-taking support technology, the majority of \nwhich help to eliminate the difficulties that are associated with writing whilst listening. Some \ntechnology also helps individuals with organising and editing notes that have been made to help \nthem digest the information. Examples: Sonocent Audio Notetaker\n\nAudio Notetaker 4 from Sonocent\n\nMind mapping: Mind mapping is an established learning and organisational tool, allowing users \nto create maps and diagrams to represent their ideas.Example: Mindview, Inspiration.\n\nInspira\n\n… [+1436 more chars]",
  "content_hash": "f29866dae622c21d62186b3c4cf478ab6a8844b5af9d7073473c3ff78b2efcc3",
  "token_count": 427,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 210,
  "page_number": 160,
  "page_range": [
    160,
    163
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a2c8c32a-b06c-51db-b016-9019a344a880`

- vector: dim=3072 · [-0.0483, 0.0498, -0.0211, -0.0114, -0.0041, 0.0169, -0.0033, -0.0018, …]

```json
{
  "chunk_id": "a2c8c32a-b06c-51db-b016-9019a344a880",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Livescribe Smartpens",
  "chunk_text": "Digital recorder: Digital recorder is ideal for anyone with dyslexia and who needs support with \nnote-taking. \nDigital Voice Recorder\n\nHeadsets: Headsets are designed for a variety of uses for conference calls, telephone, podcasts, \nspeech recognition, music and much.\n\nICT for the differently abled persons\n\nSome of the most relevant and innovative applications of information and communication \ntechnology for development can be found in interventions developed for the differently abled. \nThe development of ICT presents new opportunities for these individuals to mainstream their \nactivities and \n\n… [+1253 more chars]",
  "content_hash": "cbcfec91366f3d7a989fa1440ca26ff9623f11a5d8c5fdbee9cd5ea3875d7cdf",
  "token_count": 355,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 211,
  "page_number": 163,
  "page_range": [
    163,
    164
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `f4bb0a69-fc5b-51f3-b0dd-00dbbff96c40`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f4bb0a69-fc5b-51f3-b0dd-00dbbff96c40",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "References",
  "section_type": "references",
  "chunk_text": "References\n\n1. Tripathi, M., & Shukla, A. (2014). Use of assistive technologies in academic libraries: A survey. Assistive \nTechnology, 26(2), 105–118. https://doi.org/10.1080/10400435.2013.853329\n\n2. Williamson, K., Schauder, D., Stockfield, L., Wright, S., & Bow, A. (2001). The role of the internet for \npeople with disabilities: Issues of access and equity for public libraries. Australian Library Journal, 50(2), \n157–174. https://doi.org/10.1080/00049670.2001.10755951\n\n3. Roy, P. C., & Bandyopadhyay, R. (2009). Designing barrier free services for visually challenged persons in \nthe academic \n\n… [+2079 more chars]",
  "content_hash": "8b353b27a7f3b4bce78c07e30816dc085a7dac395f98da3dcc48a62e4dde865f",
  "token_count": 819,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    164,
    166
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `aabe281e-5181-50c0-9ecd-331f591330a3`

- vector: dim=3072 · [-0.0328, 0.0367, -0.0095, 0.0109, -0.0018, 0.0012, -0.0056, 0.0147, …]

```json
{
  "chunk_id": "aabe281e-5181-50c0-9ecd-331f591330a3",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "References",
  "section_type": "references",
  "chunk_text": "1. Tripathi, M., & Shukla, A. (2014). Use of assistive technologies in academic libraries: A survey. Assistive \nTechnology, 26(2), 105–118. https://doi.org/10.1080/10400435.2013.853329\n\n2. Williamson, K., Schauder, D., Stockfield, L., Wright, S., & Bow, A. (2001). The role of the internet for \npeople with disabilities: Issues of access and equity for public libraries. Australian Library Journal, 50(2), \n157–174. https://doi.org/10.1080/00049670.2001.10755951\n\n3. Roy, P. C., & Bandyopadhyay, R. (2009). Designing barrier free services for visually challenged persons in \nthe academic libraries in\n\n… [+694 more chars]",
  "content_hash": "66da9d450d9f95578f1cc1909b174d7440b01c90601158eeb62299e1929ebf90",
  "token_count": 394,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f4bb0a69-fc5b-51f3-b0dd-00dbbff96c40",
  "chunk_index": 212,
  "page_number": 164,
  "page_range": [
    164,
    164
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `c92fa952-9002-5cf7-85f7-311f013a648c`

- vector: dim=3072 · [-0.0283, 0.0303, -0.0076, 0.0079, 0.0219, -0.0001, -0.0222, 0.0345, …]

```json
{
  "chunk_id": "c92fa952-9002-5cf7-85f7-311f013a648c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "References",
  "section_type": "references",
  "chunk_text": "International Journal of Information Sciences and Techniques, 6(1/2), 257–267. Retrieved \nfrom http://dspace-unipr.cineca.it/bitstream/1889/1147/1/Library Services for Blind and Visually Impaired \nPeople A Literature Review.pdf 6. Kaye, H. S., Yeager, P., & Reed, M. (2008). Disparities in Usage of Assistive Technology Among People \nWith Disabilities. Assistive Technology, 20(4), 194–203. https://doi.org/10.1080/10400435.2008.10131946\n\n7. National Sample Survey Office. (2016). Disabled persons in India: A statistical profile, 0–\n\n107. Retrieved from \nhttp://mospi.nic.in/sites/default/files/publ\n\n… [+999 more chars]",
  "content_hash": "a77a5e9f52061c8084c0d6d559129fd05b8236389de71e0ae621e0e8895ec2c1",
  "token_count": 482,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f4bb0a69-fc5b-51f3-b0dd-00dbbff96c40",
  "chunk_index": 213,
  "page_number": 164,
  "page_range": [
    164,
    166
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8805a3ea-8545-5b0c-a120-abaacf1a911f`

- vector: dim=3072 · [-0.0280, 0.0044, -0.0299, 0.0372, -0.0066, 0.0031, -0.0250, 0.0067, …]

```json
{
  "chunk_id": "8805a3ea-8545-5b0c-a120-abaacf1a911f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Archana Shukla — DLIS, IGNOU — Abstract",
  "chunk_text": "The present paper discusses digital prevention activities and processes. It also discusses why the \npreservation of digital assets in libraries is required. It has been observed that the preservation of \ntraditional material turns out to be more successful and systematic after libraries and archives \nintegrated preservation into the overall planning and resource allocation. The movement a \ndocument completes a process of digitization it becomes immortal and could be accessed easily \nas and when required. As the libraries are heading towards the possession to accession and \nmanaging the knowled\n\n… [+309 more chars]",
  "content_hash": "509dc03a6e0c4417bd3f13e7c72db90bf286dd6e7fa4ea32dee2a0dfabfa7dd5",
  "token_count": 160,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 214,
  "page_number": 166,
  "page_range": [
    166,
    166
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `37b04188-ad14-5b74-9488-e710c3ba51d9`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "37b04188-ad14-5b74-9488-e710c3ba51d9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Concept Building",
  "chunk_text": "Concept Building\n\nDigital Preservation is key not only for human history, education, culture, and economics but \nalso for our civilization. Earlier we used to preserve knowledge via wood, stone, bamboo, \nleather, ceramic, fiber, etc. but slowly and gradually the need and requirement of society for \ninformation changed and so the way of providing information also changed. Discovery of the \nprinting paper technology introduced writing on silk or printing on paper. Eventually, we were \nable to put photographic images, films, and music on records1. Today oceans of information are \navailable and pr\n\n… [+2289 more chars]",
  "content_hash": "2a2d6e73b7b1d29d3d7a09e1b6587aeacf1c477ce528707a9ac6e71019784044",
  "token_count": 551,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    166,
    167
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `6882bb91-1c29-5981-a000-7b3c6c5e816f`

- vector: dim=3072 · [-0.0282, 0.0300, -0.0338, 0.0098, 0.0312, 0.0371, -0.0064, 0.0135, …]

```json
{
  "chunk_id": "6882bb91-1c29-5981-a000-7b3c6c5e816f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Concept Building",
  "chunk_text": "Digital Preservation is key not only for human history, education, culture, and economics but \nalso for our civilization. Earlier we used to preserve knowledge via wood, stone, bamboo, \nleather, ceramic, fiber, etc. but slowly and gradually the need and requirement of society for \ninformation changed and so the way of providing information also changed. Discovery of the \nprinting paper technology introduced writing on silk or printing on paper. Eventually, we were \nable to put photographic images, films, and music on records1. Today oceans of information are \navailable and preserving them digi\n\n… [+1309 more chars]",
  "content_hash": "3941d21a9295c0dd166f502fdb35500c5c91dd8ebecab4f9c8dacbe61ec69426",
  "token_count": 376,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "37b04188-ad14-5b74-9488-e710c3ba51d9",
  "chunk_index": 215,
  "page_number": 166,
  "page_range": [
    166,
    167
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `395f031c-335e-50e2-983a-4153b46333f9`

- vector: dim=3072 · [-0.0264, 0.0380, -0.0276, -0.0048, 0.0185, 0.0254, -0.0010, 0.0272, …]

```json
{
  "chunk_id": "395f031c-335e-50e2-983a-4153b46333f9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Concept Building",
  "chunk_text": "Assess the current digital preservation landscape at each institution; (iii) Advocate for the value \n144\n\nICDL 2019: Poster\n\nof digital preservation activities; (iv) Implement shared digital preservation services; (v) Sustain \ngroup activities and establish structures for on-going support. Before we move further, we should understand digital material which refers to any material \nprocessed by a computer and born-digital. The digital preservation community is developing an \nawareness and understanding of the concept of disaster planning as part of a digital preservation \nprogram4, but a thoroug\n\n… [+651 more chars]",
  "content_hash": "24d45a0a811e8287658f9af8df86337d91348afa6790b8f0000ab659bc39c0cb",
  "token_count": 231,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "37b04188-ad14-5b74-9488-e710c3ba51d9",
  "chunk_index": 216,
  "page_number": 167,
  "page_range": [
    167,
    167
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `7fb82bdf-ffdd-5857-8d70-f19263902aaa`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "7fb82bdf-ffdd-5857-8d70-f19263902aaa",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Definition",
  "chunk_text": "Definition\n\nThere are many definitions available on digital preservation. It is a formal endeavor to ensure the \ndigital information of continuing value remains accessible and usable. Some of the definitions \nare:\n\nThe American Institute for Conservation of Historic and Artistic Work (AIC) defines as \n“Preservation is the protection of cultural property through activities that minimize chemical and \nphysical deterioration” and damage and that prevents loss of informational content.\n\nAccording to Russell (1998), Digital Preservation is a process by which digital data is perceived \nin digital fo\n\n… [+5850 more chars]",
  "content_hash": "7718b27c1219ff8fe36a6f600a3e4a3976f096c94435d6dc16eaa4d1c120aacc",
  "token_count": 1245,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    167,
    170
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a20e21a4-8c25-5574-913e-9807b65f9d26`

- vector: dim=3072 · [-0.0569, 0.0467, -0.0215, -0.0044, 0.0277, 0.0214, -0.0060, 0.0022, …]

```json
{
  "chunk_id": "a20e21a4-8c25-5574-913e-9807b65f9d26",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Definition",
  "chunk_text": "There are many definitions available on digital preservation. It is a formal endeavor to ensure the \ndigital information of continuing value remains accessible and usable. Some of the definitions \nare:\n\nThe American Institute for Conservation of Historic and Artistic Work (AIC) defines as \n“Preservation is the protection of cultural property through activities that minimize chemical and \nphysical deterioration” and damage and that prevents loss of informational content.\n\nAccording to Russell (1998), Digital Preservation is a process by which digital data is perceived \nin digital form in the of\n\n… [+874 more chars]",
  "content_hash": "aaac7506bdf0cb85cca9d7deb4fbf8326faac24779f4e75b743be8cad0ad6840",
  "token_count": 281,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7fb82bdf-ffdd-5857-8d70-f19263902aaa",
  "chunk_index": 217,
  "page_number": 167,
  "page_range": [
    167,
    168
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d1805454-4004-5bc2-a9b2-930817466993`

- vector: dim=3072 · [-0.0445, 0.0183, -0.0126, 0.0021, 0.0271, 0.0138, -0.0013, 0.0119, …]

```json
{
  "chunk_id": "d1805454-4004-5bc2-a9b2-930817466993",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Definition",
  "chunk_text": "The \ndangerous threat to digital continuity is “losing the access”.\n\n145\n\nICDL 2019: Poster\n\nNeed and Importance for Digital Preservation It becomes very easy, quick and ubiquitous access to information in the digital environment. \nSimultaneously it also has the risk of losing due to some unavoidable in short space of time and \npreserving information for meaningful reuse for posterity. Ensuring reliable access to digital \ncontent over time can be difficult due to hardware failure or changes in technology rendering \ndigital content obsolete (https://www.sheffield.ac.uk/library/digitalpreservati\n\n… [+1478 more chars]",
  "content_hash": "a0a3784d85c8877f6d2dea58c50c5d5a9f77e686b9f3560910d177b7965c8f63",
  "token_count": 395,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7fb82bdf-ffdd-5857-8d70-f19263902aaa",
  "chunk_index": 218,
  "page_number": 168,
  "page_range": [
    168,
    168
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `767cc2bd-2c63-54a1-9a23-45b0f6745879`

- vector: dim=3072 · [-0.0174, 0.0129, -0.0259, 0.0143, 0.0204, 0.0203, -0.0117, 0.0152, …]

```json
{
  "chunk_id": "767cc2bd-2c63-54a1-9a23-45b0f6745879",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Definition",
  "chunk_text": "Nowadays, libraries have started procuring/subscribing more collection in e-form as compare \nto print collection so the challenge for preserving them has also increased. We need a system in \nwhich long term preservation of digital content could be possible.\n\nStrategies for the preservation of Digital Materials There are various organizations and institutions have been constantly thinking about digital \npreservation strategies and some of the organizations have given their view also such as OCLC \nwho developed four-point strategies for long term preservation. Further, UNESCO has also given \ngui\n\n… [+1862 more chars]",
  "content_hash": "8288f53c431808835d0a79763fe504d2a415d5cc300d384ce90305148adeb715",
  "token_count": 476,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7fb82bdf-ffdd-5857-8d70-f19263902aaa",
  "chunk_index": 219,
  "page_number": 168,
  "page_range": [
    168,
    169
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8ca55197-d983-5259-a4b7-3c6c12de90d4`

- vector: dim=3072 · [-0.0269, 0.0030, -0.0298, 0.0093, 0.0212, 0.0242, -0.0171, -0.0020, …]

```json
{
  "chunk_id": "8ca55197-d983-5259-a4b7-3c6c12de90d4",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Definition",
  "chunk_text": "Despite all that copying, the digital content into another medium is the \nviolation of intellectual property rights. It strictly needs permission from copyright holders. \nFurther, it also includes data protection act or similar privacy legislation protection information \non individuals.\n\nDigital Preservation Strategies UNESCO has given strategies for the preservation of digital heritage during 2003 in four \ncategories. They are short term strategies; medium to long term, investment strategies and \nAlternative strategies.\n\nShort-term Strategies\n\nBit-stream Copying, Refreshing, Replication, Tech\n\n… [+589 more chars]",
  "content_hash": "748bb4e09eb439f63b91542d2dd18479b2d6082473a5194d51d597cf7524ebf8",
  "token_count": 225,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "7fb82bdf-ffdd-5857-8d70-f19263902aaa",
  "chunk_index": 220,
  "page_number": 169,
  "page_range": [
    169,
    170
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a9863276-20b0-5aa6-a039-056e5a20d3a1`

- vector: dim=3072 · [-0.0341, 0.0418, -0.0302, 0.0042, 0.0104, 0.0286, -0.0200, 0.0058, …]

```json
{
  "chunk_id": "a9863276-20b0-5aa6-a039-056e5a20d3a1",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Challenges to Digital Preservation",
  "chunk_text": "It is so easy creating content in digital media and keeping it up-to-date also but it has a lot of \neconomic and technical challenges in preservation. It is also could be challenging because of “its \ndynamic nature such as interactive web pages and virtual reality”. Digital Preservation is an area \ncharacterized by a “high level of uncertainty, in which experimentation and discovery are \nemployed in the search for preservation solutions”. Digital preservation presents a unique type of \nchallenges, arising from the basic nature of digital data. Digital preservation is very challenging \nfrom tec\n\n… [+1095 more chars]",
  "content_hash": "b053a7ce0f68b16101d51bbea8d6dffc4ef4045f570b31cc8663e6fa718549ec",
  "token_count": 329,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 221,
  "page_number": 170,
  "page_range": [
    170,
    171
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `49b04bc3-c5cb-5439-8d01-efffad6482ca`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "49b04bc3-c5cb-5439-8d01-efffad6482ca",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preservation Planning",
  "chunk_text": "Preservation Planning\n\nIn this process preservation activities are organized in a logical sequence. Preservation planning \nis a process that organizes preservation activities in a logical sequence. The “standards for \nplanning discuss the relationship among these activities while the remaining activity standards \nconsider how each activity should be carried out”. \n      The above-mentioned cycle shows the challenges being faced in Digital Preservation\n\nDigital preservation in India\n\nEach country of the world has been giving importance to a country's intellectual outputs for their \nposterity. “\n\n… [+3251 more chars]",
  "content_hash": "64174506e10351ea875aabd2dabefe9c3fc4fc8e209c1a9b4ddbeb172ec110a6",
  "token_count": 702,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    171,
    172
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `090fcf7d-9f5f-51c8-8764-4e63e19b77e7`

- vector: dim=3072 · [-0.0222, 0.0248, -0.0215, 0.0261, 0.0067, 0.0175, -0.0232, 0.0125, …]

```json
{
  "chunk_id": "090fcf7d-9f5f-51c8-8764-4e63e19b77e7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preservation Planning",
  "chunk_text": "In this process preservation activities are organized in a logical sequence. Preservation planning \nis a process that organizes preservation activities in a logical sequence. The “standards for \nplanning discuss the relationship among these activities while the remaining activity standards \nconsider how each activity should be carried out”. \n      The above-mentioned cycle shows the challenges being faced in Digital Preservation\n\nDigital preservation in India\n\nEach country of the world has been giving importance to a country's intellectual outputs for their \nposterity. “Preservation of digital\n\n… [+1860 more chars]",
  "content_hash": "03d44625c06c55bd1d59ba101bfb834393cd2c0833f492c11e37cae0602def4e",
  "token_count": 448,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "49b04bc3-c5cb-5439-8d01-efffad6482ca",
  "chunk_index": 222,
  "page_number": 171,
  "page_range": [
    171,
    172
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `360ccfb2-7875-553a-913f-1c678a967d5c`

- vector: dim=3072 · [-0.0143, 0.0168, -0.0235, 0.0388, 0.0030, -0.0001, -0.0243, -0.0049, …]

```json
{
  "chunk_id": "360ccfb2-7875-553a-913f-1c678a967d5c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Preservation Planning",
  "chunk_text": "No doubt that till now no such serious efforts have been undertaken by the Indian \ngovernment.\n\nSelection of Library Materials for Digital Preservation The primary work of the library is “selecting, collecting and preserving it for posterity”. This is \nalso a truth that we cannot preserve everything, and that nothing can be preserved forever. \nPreservation is the series of managed activities necessary to ensure continued access to digital \nmaterials for as long as necessary. The libraries select the material for acquisition intending to \npreserve it for a longer time but for most items in most\n\n… [+918 more chars]",
  "content_hash": "6303f48187bda1b1acf55e33a8fef35334b3a1ab24bc664c6b4653b992e6196f",
  "token_count": 274,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "49b04bc3-c5cb-5439-8d01-efffad6482ca",
  "chunk_index": 223,
  "page_number": 172,
  "page_range": [
    172,
    172
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `90429ce9-5663-5093-9ac9-759b89351136`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "90429ce9-5663-5093-9ac9-759b89351136",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Some Examples",
  "chunk_text": "Some Examples\n\nIt has been observed that the preservation of digital material has a lot of challenges from \nselecting tools for preservation to saving the digital content for a longer period. While doing this \nif we could not remain conscious or made some mistake the consequences could be much more \ndangerous. The below-mentioned examples show some of the incidents:\n\n1. Avant-Garde 3: AM Magazine used an outside service to manage their servers. One day, \nthey tried to access information saved on those servers and were denied access. They \nthought at first that there was a technology issue, but\n\n… [+4141 more chars]",
  "content_hash": "dd868332295cc7e4d340f71510b7b76fd2ea4358c7d3d2caf1a210262ca05352",
  "token_count": 1146,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    172,
    174
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `ecf3aacc-d480-5414-8399-24f1da818e38`

- vector: dim=3072 · [-0.0479, 0.0022, -0.0179, 0.0063, 0.0329, 0.0204, 0.0098, 0.0070, …]

```json
{
  "chunk_id": "ecf3aacc-d480-5414-8399-24f1da818e38",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Some Examples",
  "chunk_text": "It has been observed that the preservation of digital material has a lot of challenges from \nselecting tools for preservation to saving the digital content for a longer period. While doing this \nif we could not remain conscious or made some mistake the consequences could be much more \ndangerous. The below-mentioned examples show some of the incidents:\n\n1. Avant-Garde 3: AM Magazine used an outside service to manage their servers. One day, \nthey tried to access information saved on those servers and were denied access. They \nthought at first that there was a technology issue, but their servers \n\n… [+431 more chars]",
  "content_hash": "703bfc9ecbddd79558e0def6f1365ea95f5e4c2ccd2ca47a871256c6169f55b6",
  "token_count": 210,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "90429ce9-5663-5093-9ac9-759b89351136",
  "chunk_index": 224,
  "page_number": 172,
  "page_range": [
    172,
    172
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `73108dfd-9afe-56f7-9ab9-ab80153efa4f`

- vector: dim=3072 · [-0.0218, 0.0201, -0.0118, 0.0343, 0.0286, 0.0018, -0.0196, 0.0234, …]

```json
{
  "chunk_id": "73108dfd-9afe-56f7-9ab9-ab80153efa4f",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Some Examples",
  "chunk_text": "Data was contained in many different \nconnected files. Data in those files started disappearing. They retrieved back up files of \nthe data only to find out that data was corrupted. They had to pull up different versions \nand piece together enough good data to fix the problem6a\n\n150 ICDL 2019: Poster \nConclusion \nLong term preservation of library material in today’s time is a big challenge. It is also considered \nas fragile. Preservation is the “oldest and most fundamental function of libraries and archives”. \nEarlier documents were chained to preserve them. It is also being emphasized to prese\n\n… [+1675 more chars]",
  "content_hash": "82035dab722cad3603592a53fef4848416c6262647a8a1de36d5f9aaa891cc71",
  "token_count": 503,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "90429ce9-5663-5093-9ac9-759b89351136",
  "chunk_index": 225,
  "page_number": 173,
  "page_range": [
    173,
    173
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `fcbfe675-2068-5353-8807-4dbed0bbba27`

- vector: dim=3072 · [-0.0287, 0.0059, -0.0130, 0.0032, 0.0131, 0.0106, -0.0102, 0.0270, …]

```json
{
  "chunk_id": "fcbfe675-2068-5353-8807-4dbed0bbba27",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Some Examples",
  "chunk_text": "ISBN 978-0-7546-4038-7.\n4.\nGracy & Kahn, 2012 “Preservation in the Digital Age A Review of Preservation Literature”. LRTS,56.1.\n2009, 25-43.\n5. https://www.sheffield.ac.uk/library/digitalpreservation/need.\n6.\nLeFurgy, B. (2012, July 19). Digital Disaster Planning: Get the picture before losing the picture.Retrieved\nfrom https://blogs.loc.gov/digitalpreservation/2012/07/digital-disaster/planning-get-the-picture-before-\nlosing-the-picture/.\n151\n\n| Reference |  |\n| --- | --- |\n| 1. | Gandhi, et al. “Need of Digital Preservation Strategies, Issues and challenges for Future”. SRELS Journal |\n|  | o\n\n… [+1244 more chars]",
  "content_hash": "32cc3d7d44c9674fc1adf3c97c97e46f1845bc6fa175ce3750fabfbd4d470f6c",
  "token_count": 542,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "90429ce9-5663-5093-9ac9-759b89351136",
  "chunk_index": 226,
  "page_number": 173,
  "page_range": [
    173,
    174
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `3261aee4-806b-52ac-90f6-58009e4db4d9`

- vector: dim=3072 · [-0.0301, 0.0139, -0.0125, -0.0237, -0.0051, 0.0138, -0.0485, 0.0022, …]

```json
{
  "chunk_id": "3261aee4-806b-52ac-90f6-58009e4db4d9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Abstract",
  "chunk_text": "An attempt has been made to explain the concept of DRM (Digital Rights Management), which \nallows content providers to distribute, promote and market the digital contents in a secure way. \nThe main focus of this paper consists of 2012 Amendments of Indian Copyright Act, 1957 with \nregard to DRM.\n\nThis paper refers the management of Rights digitally systems within devices (Computer, Mobile \netc.). DRM begins with user authentication when accessing digital information system and \nPreventing copying in any form.  It is copyright protection by further locking safeguard. Yet, it is \nnot a full proo\n\n… [+1805 more chars]",
  "content_hash": "eca3126d7c6d0b81b2891497363dd26ca08b92ae07d3b4d17dbf7ff2b67dfdc4",
  "token_count": 478,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 227,
  "page_number": 174,
  "page_range": [
    174,
    175
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d6294008-5e90-50bd-8f5b-997d789a4749`

- vector: dim=3072 · [-0.0323, -0.0042, -0.0272, -0.0261, -0.0094, 0.0090, -0.0211, -0.0159, …]

```json
{
  "chunk_id": "d6294008-5e90-50bd-8f5b-997d789a4749",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Digital Rights Management (DRM)",
  "chunk_text": "Digital Rights Management (DRM) refers to technologies used by software and hardware \nmanufacturers, publishers, Content Owners, and Copyright holderslimitunauthorized use of \ndigital contents and devices. It also includes technologies that control the use, modification, and \ndistribution of works, as well as systems within devices(Computer, Mobile phone etc.). DRM \nallows content providers to distribute, promote and market the digital contents in a secure way. \nCopyright holders are allowed to use DRM to safeguard their work being duplicated or utilized \nby others. Therefore copyright laws ac\n\n… [+967 more chars]",
  "content_hash": "280ced90ca9c88303dbf948e1b04a8390c2cc988b5aea5c261fc9f3c6a4d17ad",
  "token_count": 286,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 228,
  "page_number": 175,
  "page_range": [
    175,
    175
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `f379521c-e7b3-5dab-a9cb-81e7098d9aa1`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f379521c-e7b3-5dab-a9cb-81e7098d9aa1",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Objectives",
  "chunk_text": "Objectives\n\nThe objectives of Digital Rights Management to provide needful services in digitization era in \nrespect of library professionals are:\n\n To protect intellectual property \n To restrict access to specific digital work, digital media or device without \nauthentication content creator \n To control free use of content, design and methodsthrough  rights protection \nmechanism  \n To prevent piracy of digital media property  \n To prevent loss of revenue, tax, employment \n To prevent unauthorized duplication artistic works  \n To prevent use of the content on false ownership \n To ensure\n\n… [+2301 more chars]",
  "content_hash": "d0a5d93030fe790ac0b6b819eae79e176e3b46de799ede7c95cc9b2eaf3010af",
  "token_count": 598,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    175,
    176
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `21061546-9086-5dce-94fa-55ea614135c7`

- vector: dim=3072 · [-0.0264, -0.0046, -0.0083, 0.0215, -0.0074, 0.0008, -0.0398, 0.0262, …]

```json
{
  "chunk_id": "21061546-9086-5dce-94fa-55ea614135c7",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Objectives",
  "chunk_text": "The objectives of Digital Rights Management to provide needful services in digitization era in \nrespect of library professionals are:\n\n To protect intellectual property \n To restrict access to specific digital work, digital media or device without \nauthentication content creator \n To control free use of content, design and methodsthrough  rights protection \nmechanism  \n To prevent piracy of digital media property  \n To prevent loss of revenue, tax, employment \n To prevent unauthorized duplication artistic works  \n To prevent use of the content on false ownership \n To ensure compliance \n\n… [+1441 more chars]",
  "content_hash": "b1a60fbe8c57d8dd2c9b62808bb13ab82061102035f78894e2cece07afbade2f",
  "token_count": 436,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f379521c-e7b3-5dab-a9cb-81e7098d9aa1",
  "chunk_index": 229,
  "page_number": 175,
  "page_range": [
    175,
    176
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `53e51bac-c853-55b1-ab23-5dd03cc8020a`

- vector: dim=3072 · [-0.0377, 0.0037, -0.0051, 0.0341, -0.0154, 0.0007, -0.0524, 0.0146, …]

```json
{
  "chunk_id": "53e51bac-c853-55b1-ab23-5dd03cc8020a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Objectives",
  "chunk_text": "In May 2012, both houses of the Indian Parliament unanimously placed their seal on \nthe Copyright Amendment Bill, 2012, bringing Indian copyright law into compliance with the \nWorld Intellectual Property Organization “Internet Treaties”. While introducing technological protection measures, the amended law ensures that fair use \nsurvives in the digital era by providing special fair use provisions. The amendments have made \nmany author-friendly amendments, special provisions for disabled, amendments facilitating \naccess to works and other amendments to streamline copyright administration.\n\nThis \n\n… [+484 more chars]",
  "content_hash": "6737448fbd6915fcb1c0849e0f6440bbd7227e9edeba5dcdfe301e0ba8d1205d",
  "token_count": 204,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "f379521c-e7b3-5dab-a9cb-81e7098d9aa1",
  "chunk_index": 230,
  "page_number": 176,
  "page_range": [
    176,
    176
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `80a6a588-e11a-5bad-84d0-5de25266e618`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "80a6a588-e11a-5bad-84d0-5de25266e618",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures",
  "chunk_text": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures\n\nThe new section 65A, introduced for protection of technological protection measures (TPM) \nused by a copyright owner to protect his rights on the work, makes circumvention of it a criminal \noffence punishable with imprisonment.\n\nAs a result, “any person who circumvents an effective technological measure applied for the \nprotection of any of the rights, with the intention of infringing such rights, shall be punishable \nwith imprisonment, which may extend to two years and shall also be liable to fine.\n\n… [+8223 more chars]",
  "content_hash": "afc61214f6ad18bf57086cb649cd592de59d39fd378260b8faee53fb75b0a246",
  "token_count": 1770,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    176,
    179
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5633960b-3dab-5113-ab03-88f2c8cfd285`

- vector: dim=3072 · [-0.0315, -0.0120, -0.0080, 0.0231, 0.0071, -0.0225, -0.0490, 0.0189, …]

```json
{
  "chunk_id": "5633960b-3dab-5113-ab03-88f2c8cfd285",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures",
  "chunk_text": "The new section 65A, introduced for protection of technological protection measures (TPM) \nused by a copyright owner to protect his rights on the work, makes circumvention of it a criminal \noffence punishable with imprisonment.\n\nAs a result, “any person who circumvents an effective technological measure applied for the \nprotection of any of the rights, with the intention of infringing such rights, shall be punishable \nwith imprisonment, which may extend to two years and shall also be liable to fine.” The rationale \nis to prevent the possibility of high rate infringement (digital piracy) in the\n\n… [+223 more chars]",
  "content_hash": "3e54eed67cad1c44e1a0b4e872d2a1743f85a3a925f9afc35f096d317a19c2d7",
  "token_count": 163,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "80a6a588-e11a-5bad-84d0-5de25266e618",
  "chunk_index": 231,
  "page_number": 176,
  "page_range": [
    176,
    176
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `8acccb2d-f609-5e8f-9767-e70f6796378e`

- vector: dim=3072 · [-0.0113, 0.0049, -0.0092, 0.0411, -0.0171, -0.0164, -0.0324, 0.0216, …]

```json
{
  "chunk_id": "8acccb2d-f609-5e8f-9767-e70f6796378e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures",
  "chunk_text": "This amendment also clarifies the problem of circumvention impacting the public interest on \naccess to work facilitated by the copyright laws. Sub-section (2) permits circumvention for \nspecified uses.\n\n154 ICDL 2019: Poster \nDigital Rights Management Information \nSection 65B has been introduced to provide protection of rights management information, which \nhas been defined under clause (xa) of section 2. \nThis amendment is intended to prevent the removal of the rights management information \nwithout authority and distributing any work, fixed performance or phonogram, after removal of \nrights \n\n… [+1909 more chars]",
  "content_hash": "f8d1b68b961bcdaedcd27c1cd4417f9e5497703c2538e3401cc328c3077e2559",
  "token_count": 482,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "80a6a588-e11a-5bad-84d0-5de25266e618",
  "chunk_index": 232,
  "page_number": 177,
  "page_range": [
    177,
    177
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `3372739d-b5de-5619-b4b1-41d336225cc0`

- vector: dim=3072 · [-0.0242, -0.0132, -0.0123, -0.0028, -0.0049, 0.0056, -0.0179, 0.0309, …]

```json
{
  "chunk_id": "3372739d-b5de-5619-b4b1-41d336225cc0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures",
  "chunk_text": "is available to specialized \nresearchers other than those affiliated with the institution) will not be liable for copyright \ninfringement based upon a library patron’s unsupervised use of reproducing equipment located \non its premises, provided that the copying equipment displays a notice that the making of a copy may be subject to the copyright law. The notice must appear in a specific form, as shown below. \nWhen patrons ask the library to copy text works, the warning notice must be printed within a box \nlocated prominently on the order form, either on the front side of the form or immediatel\n\n… [+2185 more chars]",
  "content_hash": "a7f1986ef48b2b0aff80989a050d936e1f4e6e62db500ed3716950b0adf0b69d",
  "token_count": 585,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "80a6a588-e11a-5bad-84d0-5de25266e618",
  "chunk_index": 233,
  "page_number": 177,
  "page_range": [
    177,
    178
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `46be20d1-4d58-592c-ab66-c0cfd470621c`

- vector: dim=3072 · [-0.0416, 0.0058, -0.0186, 0.0005, 0.0382, 0.0048, -0.0251, 0.0248, …]

```json
{
  "chunk_id": "46be20d1-4d58-592c-ab66-c0cfd470621c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures",
  "chunk_text": "running the applications through remote terminal sessions\n(protection from remote access).\n\nApplications can be protected automatically (no functions are selected).\n\nA custom user interface can be developed.\n\nDeciding on permission level – viewing, using, reproducing, printing, and trading: Security options to protect the files that you create. The security options may be\ncontrolled by two passwords: the Permission password and the Open password. The\nPermission password is the master password created by the owner of the file that lets you\ncontrol whether a file can be printed, edited, or co\n\n… [+1470 more chars]",
  "content_hash": "cc9dcb811409debcabc531cc7d7492ce67bfc88cfce07ae3a0eee0e2f13dc379",
  "token_count": 419,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "80a6a588-e11a-5bad-84d0-5de25266e618",
  "chunk_index": 234,
  "page_number": 178,
  "page_range": [
    178,
    179
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `4da8d7b4-608e-5d5d-b2e1-c9efd090d927`

- vector: dim=3072 · [-0.0270, -0.0290, -0.0170, -0.0077, -0.0164, 0.0009, -0.0108, 0.0017, …]

```json
{
  "chunk_id": "4da8d7b4-608e-5d5d-b2e1-c9efd090d927",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "6. Reform of Copyright Board and other minor amendments — Protection of Technological Measures",
  "chunk_text": "In such a network, each site makes local decisions about which other sites to \ncontact and offer trades as well as whether to accept trades offered by other sites. The \nresult is a global peer to peer archiving network, built up from a series of locally agreed \nupon binary trading links. • \nMechanism for tracking access through tamper detection tools, anti-screen capture, \nunique-identification, water marking:When the content owners create the digital content \nthat needs to be protected, they should specify a set of rights to the content and become \nthe content’s rights holder. When other user\n\n… [+1040 more chars]",
  "content_hash": "8286755d461d5aaa771482165c49fc21f1d1fc2fc63dbee96e5b958a2d9b4fbd",
  "token_count": 321,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "80a6a588-e11a-5bad-84d0-5de25266e618",
  "chunk_index": 235,
  "page_number": 179,
  "page_range": [
    179,
    179
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `97a3958e-4d41-59cf-b0e8-88b3a65797e0`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "97a3958e-4d41-59cf-b0e8-88b3a65797e0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "Copyright — Digital Rights Management\n\n• \nRight over expression of ideas, \ninvention (book narrating process of \nturning coal to diamond) \n• \nRight is automatic \n• \nLanguage is formal like mathematics or \nlike programming code; Language that \ncan be executed as an algorithm  \n• \nNot open to interpretation but precise \n157\n\n|  | C |  |  |\n| --- | --- | --- | --- |\n|  | opyright | Digital Rights Management |  |\n|  | Right over expression of ideas, • invention (book narrating process of turning coal to diamond) Right is automatic • | Language is formal like mathematics or • like programming code;\n\n… [+7941 more chars]",
  "content_hash": "e35c5da0cb82911567ed9e9043853cab12274138b29fe987ae9a4acf4a0367ec",
  "token_count": 1864,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    179,
    182
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `d1a2d943-eda9-5741-8b38-7dd4092c126b`

- vector: dim=3072 · [-0.0435, 0.0038, -0.0137, 0.0017, 0.0025, -0.0114, -0.0109, 0.0420, …]

```json
{
  "chunk_id": "d1a2d943-eda9-5741-8b38-7dd4092c126b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "• \nRight over expression of ideas, \ninvention (book narrating process of \nturning coal to diamond) \n• \nRight is automatic \n• \nLanguage is formal like mathematics or \nlike programming code; Language that \ncan be executed as an algorithm  \n• \nNot open to interpretation but precise \n157\n\n|  | C |  |  |\n| --- | --- | --- | --- |\n|  | opyright | Digital Rights Management |  |\n|  | Right over expression of ideas, • invention (book narrating process of turning coal to diamond) Right is automatic • | Language is formal like mathematics or • like programming code; Language that can be executed as an al\n\n… [+1233 more chars]",
  "content_hash": "9921d030165199e50e44d02e00c7aca8266e614391723f6cfef0f07ba8c65aba",
  "token_count": 408,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "97a3958e-4d41-59cf-b0e8-88b3a65797e0",
  "chunk_index": 236,
  "page_number": 179,
  "page_range": [
    179,
    180
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5e4c875e-4234-54f1-9e8c-ad02241251ed`

- vector: dim=3072 · [-0.0375, -0.0006, -0.0089, 0.0000, -0.0082, -0.0094, -0.0261, 0.0247, …]

```json
{
  "chunk_id": "5e4c875e-4234-54f1-9e8c-ad02241251ed",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "(Electronic Frontier \nFoundation has recorded fairly large \nnumber of such transgression cases)\n\nProblem arisen for Library and Academia  DRM will reduce open space \n In contrary coming days will discover more digital documents in a library \n Libraries may need to introduce undue restrictions and regulatory mechanism \n Interface between Library Management and Users will require to be redefined\n\nDRM provision is non-compliant with today’s India for the \nfollowing reasons\n\n• \nThe legislation has been brought about without making proper cost-benefit \nanalysis.\n\nComputer based application in I\n\n… [+1484 more chars]",
  "content_hash": "ec8ed364120f9d01674cfdbd4e6dab528314e380309e631bf3df8aa72535b776",
  "token_count": 413,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "97a3958e-4d41-59cf-b0e8-88b3a65797e0",
  "chunk_index": 237,
  "page_number": 180,
  "page_range": [
    180,
    180
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `5471f583-3465-5d37-b163-70a26ab748f9`

- vector: dim=3072 · [-0.0284, -0.0036, -0.0126, -0.0097, -0.0156, 0.0033, -0.0539, 0.0156, …]

```json
{
  "chunk_id": "5471f583-3465-5d37-b163-70a26ab748f9",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "(Electronic Frontier Foundation has recorded fairly large number of such transgression cases) |  |\n| --- | --- | --- | --- | ICDL 2019: Poster \n•\nNature of piracy is not that widespread (other than movies and songs) in\nIndia that DRM should be felt so pressing a need (internet mostly in\nworkplace/cybercafe)\n       A huge number of Indian people are yet to be computer friendly. Research and publication \nusing digital device at such a phenomenal scale is a recent development in India. Copyright \nviolation happened also inadvertently. And these violations often fall under the ambit of ‘Fair \nUse’\n\n… [+1350 more chars]",
  "content_hash": "33ec874e312ddd16321456d64fad46ec938bc7b0608936198dcb1c273b4c1c17",
  "token_count": 450,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "97a3958e-4d41-59cf-b0e8-88b3a65797e0",
  "chunk_index": 238,
  "page_number": 181,
  "page_range": [
    181,
    181
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `e754454e-441b-5a84-a0f1-20736bb2a56e`

- vector: dim=3072 · [-0.0118, 0.0040, -0.0077, 0.0224, 0.0064, -0.0207, -0.0334, 0.0253, …]

```json
{
  "chunk_id": "e754454e-441b-5a84-a0f1-20736bb2a56e",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "Kumar used \nDr.HarivanshRaiBachchan’s poem line, “Need kaNirmanPhirPhir”. Amitabh Bachchan alleged it \n159 ICDL 2019: Poster \nwas copyright infringement as this was used without obtaining prior permission.  Video was \ndeleted and Vishwas twitted to pay Rs. 32 earned  from it. \nSupreme Court Order on Privacy Right, 2017\nThe Govt. of India constituted a Committee of Experts in July 2017 under justice B N Srikrishna \nto identify the key issues relating to data protection in India and help govt. to draft a data \nprotection bill.  \nA White paper was published in last November as a first step to ini\n\n… [+1628 more chars]",
  "content_hash": "c9f791d83aaa16c23dac28351b0fe701ec02aebe9680a937c80b9366056da5ba",
  "token_count": 479,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "97a3958e-4d41-59cf-b0e8-88b3a65797e0",
  "chunk_index": 239,
  "page_number": 182,
  "page_range": [
    182,
    182
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `563f7f7a-1df7-59e1-a5db-47d45d9faf00`

- vector: dim=3072 · [-0.0454, -0.0134, -0.0168, 0.0681, -0.0521, -0.0007, -0.0294, 0.0079, …]

```json
{
  "chunk_id": "563f7f7a-1df7-59e1-a5db-47d45d9faf00",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "During that period different television broadcast companies in India telecast \nclippings taken from ESPN. ESPN filed suit against television companies for infringing their \ncopy right. The defendants argued that Australian Cricket Board was having copyright and ESPN obtained only the telecasting rights. And the clips used as a relevant news valued to cover cricket \nevent. The court upheld the defendant’s right. \nCipla v Roche, Del HC, 2012\nCipla, an Indian Pharma company made generic version of anti-cancer drug Erlotinib. Roche \nsued Cipla in 2008 claiming that Cipla’s generic product Erlocip \n\n… [+435 more chars]",
  "content_hash": "35b05b88267b6f28c76bf3e6d4fed40290624f2afec047f4b4c2e9b6ec5a3a3a",
  "token_count": 241,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "97a3958e-4d41-59cf-b0e8-88b3a65797e0",
  "chunk_index": 240,
  "page_number": 182,
  "page_range": [
    182,
    182
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `4148dc7b-2915-553e-af07-749244ef1f4b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4148dc7b-2915-553e-af07-749244ef1f4b",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "Copyright — Digital Rights Management (cont.)\n\nICDL 2019: Poster \nSome important Milestones in India under Intellectual Property \nRights \nIndian Patents Act, 1970 (Amended in 2005) \nThe Patents (Amendment) Act, 2005 is the third of three amendments to the Patents Act of 1970, \nto bring India’s patent regime into compliance with the WTO TRIPS Agreement. It extends the \nproduct patent protection to the areas of pharmaceuticals and agricultural chemicals. \nThis Act contains provisions relating to patent and traditional knowledge (see Art. 23(1)(k) & \nArt. 23(2)(k)), and genetic resources (see Art\n\n… [+5003 more chars]",
  "content_hash": "9149aac185145fafaef0bd437d32d52259ce8fb91a3151185e3b7cffa1c3eddb",
  "token_count": 1334,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    183,
    184
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `60df3947-7cce-5836-af01-f42ce3cb51f5`

- vector: dim=3072 · [-0.0238, 0.0237, -0.0062, 0.0182, -0.0019, 0.0011, -0.0276, 0.0044, …]

```json
{
  "chunk_id": "60df3947-7cce-5836-af01-f42ce3cb51f5",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "ICDL 2019: Poster \nSome important Milestones in India under Intellectual Property \nRights \nIndian Patents Act, 1970 (Amended in 2005) \nThe Patents (Amendment) Act, 2005 is the third of three amendments to the Patents Act of 1970, \nto bring India’s patent regime into compliance with the WTO TRIPS Agreement. It extends the \nproduct patent protection to the areas of pharmaceuticals and agricultural chemicals. \nThis Act contains provisions relating to patent and traditional knowledge (see Art. 23(1)(k) & \nArt. 23(2)(k)), and genetic resources (see Art. 10 & 25). \nMere invention of a scientific pri\n\n… [+1350 more chars]",
  "content_hash": "91503036f1e38aafc34e8fb3669afebf70c07ec5feee7933b45fc6cac85b2b77",
  "token_count": 434,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4148dc7b-2915-553e-af07-749244ef1f4b",
  "chunk_index": 241,
  "page_number": 183,
  "page_range": [
    183,
    183
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `68287cf8-0814-5076-9df3-2abcf4ea7254`

- vector: dim=3072 · [0.0146, 0.0162, -0.0045, 0.0200, -0.0006, 0.0135, -0.0223, -0.0198, …]

```json
{
  "chunk_id": "68287cf8-0814-5076-9df3-2abcf4ea7254",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "Quality, reputation or other \ncharacteristic of such goods is essentially attached to its geographical origin. When they are \nmanufactured goods, either production or processing or preparation of the goods concerned \ntakes place in such territory, region or locality. \nDesign Act, 2000 “Design” means only the features of shape, configuration, pattern, ornament or composition of \nlines or colours applied to any article whether in two dimensional or three dimensional or in both \nforms, by any industrial process or means, whether manual, mechanical or chemical, separate or \ncombined, which in the \n\n… [+355 more chars]",
  "content_hash": "d906d647f6e19d5e4d9bca53322d7eaa2e1f066999d2225368481d048d311762",
  "token_count": 198,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4148dc7b-2915-553e-af07-749244ef1f4b",
  "chunk_index": 242,
  "page_number": 183,
  "page_range": [
    183,
    183
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `84022c90-2e16-599c-a382-8db2374b00d0`

- vector: dim=3072 · [-0.0170, 0.0000, -0.0054, 0.0297, 0.0030, -0.0020, -0.0406, 0.0176, …]

```json
{
  "chunk_id": "84022c90-2e16-599c-a382-8db2374b00d0",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "construction or anything which is in substance a mere \nmechanical device, and does not include any trade mark as defined in clause (v) of sub-section \n(1) of section 2 of the Trade and Merchandise Marks Act, 1958 or property mark as defined in\n161 ICDL 2019: Poster \nsection 479 of the Indian Penal Code or any artistic work as defined in clause (c) of section 2 of \nthe Copyright Act, 1957 \nConclusion \nCopyright is a complex issue in the age of digital right management. Digital technologies would \ncontinue to evolve, and pose more challenges to the copyright regime in India. Through a \nplethora \n\n… [+1553 more chars]",
  "content_hash": "3d2a58941d2afc2fd2da3908e0884f8f9ad343a912d28dc7cebe1047539129b8",
  "token_count": 499,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4148dc7b-2915-553e-af07-749244ef1f4b",
  "chunk_index": 243,
  "page_number": 184,
  "page_range": [
    184,
    184
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `a79ed493-dc75-5005-80de-2227330faa4c`

- vector: dim=3072 · [-0.0461, -0.0151, -0.0029, 0.0089, -0.0106, -0.0077, -0.0067, 0.0290, …]

```json
{
  "chunk_id": "a79ed493-dc75-5005-80de-2227330faa4c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Copyright — Digital Rights Management",
  "chunk_text": "Hitsevich, Nataliya. Intellectual Property Rights infringement on the internet: an analysis of the private\ninternational law implications.\n7.\nWoznaik, Mike. Two ways to control subscription software licenses. See www.softwarekey.com\n8. Cooper, Brian and Gracia-Molina, Hector. Peer to Peer data trading to preserve information . Standford\nUniversity, Dept. of Computer Science, 2001.\n9.\nYu, Yang and Chiuch, Tzi-cker. Enterprise Digital Rights Management: Solution against information theft\nby insiders. Computer Science Department, Stony Book University.\n10. Seth, Karnika. Protecting Copyright in t\n\n… [+664 more chars]",
  "content_hash": "cf7a93eaca7a735c7c31fbc33631a11bb1f0bfdd4809e6014bdc703c79a536fa",
  "token_count": 360,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "4148dc7b-2915-553e-af07-749244ef1f4b",
  "chunk_index": 244,
  "page_number": 184,
  "page_range": [
    184,
    184
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `985ad744-0e46-587f-a28d-8107ac7912a2`

- vector: dim=3072 · [-0.0072, 0.0302, -0.0120, -0.0030, -0.0002, 0.0414, -0.0077, 0.0452, …]

```json
{
  "chunk_id": "985ad744-0e46-587f-a28d-8107ac7912a2",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Ali Sabha  29 — Bose Priyanka  11 — Chakraborty Somen  152 — Dandawate Vrushali   18 — Das Subarna Kumar  119 — Dhanamajaya M  18",
  "chunk_text": "Gul Sumeer   39, 40\nJamal Anam  28\nJan Rosy  29, 39, 40\nKhan Khalid Nadeem  48\nKhatoon Haleema  48\nMaurya Anuradha  64\nMukh Monika  82\nNaushad Ali P M  28\nPareek Sarwesh  89\nRahman M A M Mominur   133\nRoychowdhury Priyanka   119\nSamadi Shafi qunnabee   133\nShee Payel   134\nShukla Archana  144\nSingh Vikas  144\nUl haq Irfan  29\nVerma O P  152\nInternational Conference on Digital Landscape\nDigital Transformation for an Agile Environment\nNovember 6-8, 2019 | New Delhi\nICDL2019\nCONFERENCE POSTERS\nAUTHOR INDEX\n163\n\nICDL 2019 WEBCASTING\n\nSupported by\nIndira Gandhi National Open University (IGNOU)\n\nter\n\n… [+276 more chars]",
  "content_hash": "976ecadd3132f8521d2212a689d357aa1143efc6fa5b76f0d5c6de3973036a98",
  "token_count": 317,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "chunk_index": 245,
  "page_number": 185,
  "page_range": [
    185,
    187
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Parent · `08d44b51-faf3-556a-871b-1cd5c58e0036`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "08d44b51-faf3-556a-871b-1cd5c58e0036",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Agnou — R",
  "chunk_text": "Agnou — R\n\n00 30 30:30\n\n6\nE\n\nEditor-in-Chief   Prof. \nEditor   Dr Partha Kalyan Bhattacharya\nAssociate Editor   Dr Shantanu Ganguly\nMichael Seadle\nWorld Digital Libraries is an international peer-reviewed biannual journal. The journal seeks \nquality research papers that present original theoretical approaches. It also seeks \nexperimental case studies related to digital library developments, maintenance and \ndissemination of digital information focussing on research and integration of knowledge at \nthe interface of resources and development. The journal will, therefore, keep readers \nabreast wi\n\n… [+4392 more chars]",
  "content_hash": "7901acd50c75925237a8f7c4771cdfd0457d2cfebc293ef8ede2aeec7ab9a717",
  "token_count": 1186,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "page_range": [
    187,
    188
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `da315e32-c63b-5f1a-8b52-847a9ac0558a`

- vector: dim=3072 · [-0.0043, -0.0081, -0.0071, -0.0031, 0.0073, -0.0050, 0.0153, 0.0445, …]

```json
{
  "chunk_id": "da315e32-c63b-5f1a-8b52-847a9ac0558a",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Agnou — R",
  "chunk_text": "00 30 30:30\n\n6\nE\n\nEditor-in-Chief   Prof. \nEditor   Dr Partha Kalyan Bhattacharya\nAssociate Editor   Dr Shantanu Ganguly\nMichael Seadle\nWorld Digital Libraries is an international peer-reviewed biannual journal. The journal seeks \nquality research papers that present original theoretical approaches. It also seeks \nexperimental case studies related to digital library developments, maintenance and \ndissemination of digital information focussing on research and integration of knowledge at \nthe interface of resources and development. The journal will, therefore, keep readers \nabreast with the curr\n\n… [+1446 more chars]",
  "content_hash": "534aed59878cdeec70ab849a625f130a7bd54d00c007bbeec11e5804aaac1680",
  "token_count": 437,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08d44b51-faf3-556a-871b-1cd5c58e0036",
  "chunk_index": 246,
  "page_number": 187,
  "page_range": [
    187,
    188
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `09d34c5e-320f-5c27-97e6-62c70b8fad05`

- vector: dim=3072 · [-0.0165, 0.0002, -0.0195, -0.0056, 0.0214, 0.0008, -0.0098, 0.0376, …]

```json
{
  "chunk_id": "09d34c5e-320f-5c27-97e6-62c70b8fad05",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Agnou — R",
  "chunk_text": "Soft copy in English, in MS Word format \nshould be submitted to the editor: P K Bhattacharya at <pkbhatta@teri.res.in>. The length of the original article should not exceed a 8,000 words. The main text should be double-spaced, with headings and sub-headings clearly indicated and placed on the left-hand side of the text. \nAll tables, figures, and equations should be numbered with Arabic numerals and the measurements should be given in metric (SI) units.\nCall for papers\nDr Jagdish Arora,Director, INFLIBNET, \nProf. Gobinda Chowdhury, PhD,Professor, \nProf. Paul Nieuwenhuysen,Professor, Vrije \nDr M\n\n… [+1262 more chars]",
  "content_hash": "e62391dd4dd5bafd8931ce3b47654fe464087d1fff250ed0274d6dfe701d16a7",
  "token_count": 486,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08d44b51-faf3-556a-871b-1cd5c58e0036",
  "chunk_index": 247,
  "page_number": 188,
  "page_range": [
    188,
    188
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```

## Child · `75a534a6-92d0-5166-9fa0-fed2594c418c`

- vector: dim=3072 · [-0.0003, 0.0050, -0.0080, -0.0017, 0.0009, 0.0008, -0.0126, 0.0304, …]

```json
{
  "chunk_id": "75a534a6-92d0-5166-9fa0-fed2594c418c",
  "document_id": "icdl_poster_2019_full_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ICDL_Poster_2019_Full.pdf",
  "section_heading": "Agnou — R",
  "chunk_text": "Professor, \nBangalore, India\nTampere, Finland\nINESC-ID/IST, Information Systems \nDr Debal Chandra Kar,Librarian, \nGroup Lisbon Technical University, \nAmbedkar University, New Delhi, India\nDr Ratna Sanyal,Professor, Computer Prof. Shalini R Urs,Executive Director, \nPortugal\nScience Engineering, School of \nInternational School of Information \nProf. Gary Marchionini,Professor, School of \nEngineering and Technology, BML Munjal \nManagement, University of Mysore, \nProf. Daniel Chandran, PhD,Professor, \nInformation and Library Science University \nUniversity, India\nMysore, India\nFaculty of Information\n\n… [+874 more chars]",
  "content_hash": "1741d9c129243a383f2d79d9455019cc77635a1ec56dbe776422daa655209253",
  "token_count": 363,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "icdl_poster_2019_full_pdf",
  "pdf_path": "ICDL_Poster_2019_Full.pdf",
  "parent_chunk_id": "08d44b51-faf3-556a-871b-1cd5c58e0036",
  "chunk_index": 248,
  "page_number": 188,
  "page_range": [
    188,
    188
  ],
  "created_at": "2026-06-29T10:55:45.440768+00:00",
  "updated_at": "2026-06-29T10:55:45.440768+00:00"
}
```
