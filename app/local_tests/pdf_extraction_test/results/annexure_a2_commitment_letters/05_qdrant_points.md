# Qdrant points — Annexure_A2_Commitment-letters.pdf

- points (rows upserted): **10**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `413ecc28-1d12-5e05-b91d-66c4f487668e`

- vector: dim=3072 · [0.0054, 0.0008, -0.0161, -0.0059, -0.0013, -0.0096, 0.0011, 0.0333, …]

```json
{
  "chunk_id": "413ecc28-1d12-5e05-b91d-66c4f487668e",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "OCATION — ICLES' — MOTILALJHUNJHUNWALA COLLEGE — OF ARTS, SCIENCE & COMMERCE",
  "chunk_text": "Annexure- Commitment Letters for participation in the ‘Rethink Plastic’ campaign\\ \n1. Thane Belapur Industries Association (TBIA), Navi Mumbai\n\n2\\. ICLES Motilal Jhunjhunwala College, Navi Mumbai\n\nPlot No. 53, Sector - 9A, Amlendu Roye Marg, Vashi, Navi Mumbai - 400 703.\nTel. : 022 - 27663061 / 27800800 · Email : info@iclesmj.edu.in, Website : www.iclesmj.edu\nPermanently Affiliated to the University of Mumbai.\nListed u/s 2(f) & 12 (B) of UGC Act 1956",
  "content_hash": "dec0066bf3818295c890d1a0163bc1c5727c9cb08af5a184454b13f3ef1bc9c6",
  "token_count": 153,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    2
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Parent · `4c344519-4c50-50c9-bd53-a1ba60daebd6`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4c344519-4c50-50c9-bd53-a1ba60daebd6",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Accredited A Grade by NAAC",
  "chunk_text": "Accredited A Grade by NAAC\n\n(Established in 1978)\n\nRef. No .:\n/ICLES'MJ-(Sr./Jr.)/\n\nDate :\n\nDate: 27/2/2020\n\nIn line with our Institute's commitment towards Environment Conservation, we hereby\nagree to join hands with TERI-WRC and United Nations Environment Programme (UNEP)\nfor the 'Rethink Plastic' campaign under the project titled \"Promotion of countermeasures\nagainst marine plastic litter in Southeast Asia and India\".\n\nTowards this, our Institution commits to provide 100 number of native tree saplings\ncollected from roadsides and raised in waste plastic bottles. We shall also appeal to our\n\n\n… [+1512 more chars]",
  "content_hash": "9756fe9295b34c79a01ccf5dc0cff65125d682d827317c8c08a29f2c664b6713",
  "token_count": 593,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "page_range": [
    2,
    3
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `7fa681b4-1254-580c-933c-7ee308d466f8`

- vector: dim=3072 · [-0.0207, -0.0168, -0.0099, -0.0094, 0.0055, -0.0179, -0.0094, 0.0391, …]

```json
{
  "chunk_id": "7fa681b4-1254-580c-933c-7ee308d466f8",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Accredited A Grade by NAAC",
  "chunk_text": "(Established in 1978)\n\nRef. No .:\n/ICLES'MJ-(Sr./Jr.)/\n\nDate :\n\nDate: 27/2/2020\n\nIn line with our Institute's commitment towards Environment Conservation, we hereby\nagree to join hands with TERI-WRC and United Nations Environment Programme (UNEP)\nfor the 'Rethink Plastic' campaign under the project titled \"Promotion of countermeasures\nagainst marine plastic litter in Southeast Asia and India\".\n\nTowards this, our Institution commits to provide 100 number of native tree saplings\ncollected from roadsides and raised in waste plastic bottles. We shall also appeal to our\nstaff members and students t\n\n… [+875 more chars]",
  "content_hash": "0de2546d80ee80b332251ed96a5062e7bb9ed6384a1a75ae2979991b1dddecc5",
  "token_count": 407,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "4c344519-4c50-50c9-bd53-a1ba60daebd6",
  "chunk_index": 1,
  "page_number": 2,
  "page_range": [
    2,
    3
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `bd12525a-67a8-567f-b327-c413f54650c7`

- vector: dim=3072 · [-0.0176, 0.0196, -0.0092, -0.0119, -0.0001, -0.0049, 0.0031, 0.0441, …]

```json
{
  "chunk_id": "bd12525a-67a8-567f-b327-c413f54650c7",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Accredited A Grade by NAAC",
  "chunk_text": "V. S. Shivankar\n\nFOUNDER : Padmabhushan Dr. Karmaveer Bhaurao Patil, D. Litt. Ref. No .: 1202/2019-2020\n\nDate : 6/3/2020\n\nAUTONOMOUS — COLLEGE — NAAC GRADE 'A+'\n\nCOPA 3.53\n\nSub: Commitment Towards Environment Conservation\n\nDET-STAR COLLEGE — SCHEME — GOVERNMENT OF INDIA\n\n(SINCE 2054)\n\nDear Madam,\nthrough self-help\n\nIn line with our Institute's commitment towards Environment Conservation, we\nhereby agree to join hands with TERI-WRC and United Nations Environment\nProgramme (UNEP) for the 'Rethink Plastic' campaign under the project titled\n\"\"Promotion of countermeasures against marine plastic lit\n\n… [+85 more chars]",
  "content_hash": "7d047a1f01a5a12f0bf2d3ad9c8a58562114b00486a14656558956008fc3483a",
  "token_count": 210,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "4c344519-4c50-50c9-bd53-a1ba60daebd6",
  "chunk_index": 2,
  "page_number": 3,
  "page_range": [
    3,
    3
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `9703f35e-b5fa-5d5b-9cb1-31d85f1b023d`

- vector: dim=3072 · [-0.0195, 0.0042, -0.0132, -0.0187, -0.0023, 0.0002, 0.0028, 0.0528, …]

```json
{
  "chunk_id": "9703f35e-b5fa-5d5b-9cb1-31d85f1b023d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "BEST COLLEGE AWARD — UNIVERSITY OF MUMBAI",
  "chunk_text": "\\-\n\nTowards this, our Institution commits to provide -58 number of native tree\nsaplings collected from roadsides and raised in waste plastic bottles. We shall\nalso appeal to our staff members and students to take a pledge to avoid single use\nplastic and participate in perception survey on plastic usage and its management.\nMoreover, being part of a responsible Educational Institution, we would also like\nto participate in future events not only for this campaign but other activities\nrelated to environment conservation as well.\n\nISO 9001:2015\nINTERNATIONAL\nACCREDITATION FORUM\n(SINCE 2917)",
  "content_hash": "6bd779cdfe22b0297fca6219c1b5790855e8d6acccb02935af85118a18fcad99",
  "token_count": 124,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "chunk_index": 3,
  "page_number": 3,
  "page_range": [
    3,
    3
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Parent · `5b03a354-bf3c-5082-8117-af885548c032`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "5b03a354-bf3c-5082-8117-af885548c032",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College",
  "chunk_text": "COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College\n\nVashi, Navi Mumbai-400703.\n\n€\n\n4\\. Maharshi Dayanand College of Arts, Science and Commerce, Mumbai\n\nMaharshi Dayanand College of Arts, Science & Commerce\nNAAC - REACCREDITED - A GRADE\n\nॐ\n\nSHRI MANGALDAS VERMA CHOWK, 25, Dr. 5.5.RAO ROAD, PAREL, MUMBAJ - 400012.\nPHONE : 2410 4541 / 2410 0012 FAX : 2410 6960 Email : principal@/mdcollage.in\n\n। यहडिसनिम अल्पति ।।\n\n12016-20178\n\"Tebein\" She level freesmsés ferl\n\n\\# 2014-20151\nhvorbel \" Bnc C\n\n… [+1734 more chars]",
  "content_hash": "a66df58406fd7b86711b9a4c29b511496072c6b61c88aaff0c841ca324ef33b3",
  "token_count": 643,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "page_range": [
    3,
    5
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `8a35b735-fc05-5ca3-a86b-a5a9e9c0be9d`

- vector: dim=3072 · [-0.0254, 0.0294, -0.0099, 0.0298, 0.0075, 0.0110, -0.0247, 0.0309, …]

```json
{
  "chunk_id": "8a35b735-fc05-5ca3-a86b-a5a9e9c0be9d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College",
  "chunk_text": "Vashi, Navi Mumbai-400703.\n\n€\n\n4\\. Maharshi Dayanand College of Arts, Science and Commerce, Mumbai\n\nMaharshi Dayanand College of Arts, Science & Commerce\nNAAC - REACCREDITED - A GRADE\n\nॐ\n\nSHRI MANGALDAS VERMA CHOWK, 25, Dr. 5.5.RAO ROAD, PAREL, MUMBAJ - 400012.\nPHONE : 2410 4541 / 2410 0012 FAX : 2410 6960 Email : principal@/mdcollage.in\n\n। यहडिसनिम अल्पति ।।\n\n12016-20178\n\"Tebein\" She level freesmsés ferl\n\n\\# 2014-20151\nhvorbel \" Bnc College\" by thémeily of Mondul\n\n#2014-2015 8\n\"Rend Sehry Bwwonen' kvorbei by Best. od Hubusbtra\n\n12013-20141\n\"Touger bertrandd' Aworied ty Out of Moheranders\n\nRef\n\n… [+345 more chars]",
  "content_hash": "f74564b2483d104027e1e96ca85192afe31eb8482c4c59c58c3bebad933a4958",
  "token_count": 329,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "5b03a354-bf3c-5082-8117-af885548c032",
  "chunk_index": 4,
  "page_number": 3,
  "page_range": [
    3,
    4
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `7cc4b842-7e58-5f6c-83c9-fbba04c512e9`

- vector: dim=3072 · [-0.0194, -0.0014, -0.0118, -0.0239, -0.0047, -0.0142, 0.0077, 0.0432, …]

```json
{
  "chunk_id": "7cc4b842-7e58-5f6c-83c9-fbba04c512e9",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College",
  "chunk_text": "hereby\nagree to join hands with TERI-WRC and United Nations Environment Programme (UNEP) for the\n'Rethink Plastic' campaign under the project titled \"Promotion of countermeasures against\nmarine plastic litter in Southeast Asia and India\". Towards this, our Institutionhas provided218 number cf native tree saplings collected\nfrom roadsides and raised in waste plastic bottles. We shall also appeal to our staff members\nand students to take a pledge to avoid single use plastic and participate inperception survey on\nplastic usage and its management. Moreover, being part of a responsible Educational\n\n\n… [+865 more chars]",
  "content_hash": "9069c8384b7a21abed4e8e05ce9a006cb11fd998cdc680504806f824d99a35ec",
  "token_count": 315,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "5b03a354-bf3c-5082-8117-af885548c032",
  "chunk_index": 5,
  "page_number": 4,
  "page_range": [
    4,
    5
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `0001ebf6-4aec-5d42-a331-32bffe649c0d`

- vector: dim=3072 · [-0.0102, 0.0239, -0.0047, 0.0021, 0.0018, 0.0076, -0.0300, 0.0428, …]

```json
{
  "chunk_id": "0001ebf6-4aec-5d42-a331-32bffe649c0d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Head -Corporate Services — Indusind Bank Limited",
  "chunk_text": "Andheri East, Mumbai 400093\n\nPILA House Officer Indusind Bank Limited, Basement, Ist Floor, 3rd Floor & cth Floor,\nPNA House, Plet No 57, Street No. 17,MIDC, Andheri, Mumbai 400 093, India. Tel: (0022) 61069299\n\nRegistered Office: 2401 Gen. Thinmayya Road, Pine-411:001, Inda\nTel: (020) 2634 3201 Fax: (020) 2634 3241 Wist us at www.indunsind.com\nCN:L65191PN1994PLC076333\n\n6\\. Netel (India) Limited\n\nNETEL — Netel (India) Limited\n\n17.12.19",
  "content_hash": "42527cd5e44c8b6ef12157d112750b78d1359bc421a878ada37b310dbfc51cac",
  "token_count": 166,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "chunk_index": 6,
  "page_number": 5,
  "page_range": [
    5,
    6
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```

## Child · `e962f55b-36af-5c74-90b2-77fea0ee4cd3`

- vector: dim=3072 · [-0.0274, -0.0123, -0.0090, -0.0088, -0.0037, -0.0054, -0.0111, 0.0112, …]

```json
{
  "chunk_id": "e962f55b-36af-5c74-90b2-77fea0ee4cd3",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Pledge against Single Use Plastic",
  "chunk_text": "As a good citizen of my country and a responsible resident of the planet Earth, I\npledge to Refuse, Reduce, Recycle, Reuse, Repair, Re-gift, Recover and\n\"Rethink plastic\", to the best of my efforts by doing the following:\n\n. I shall say \"NO\" to single use plastic items (Straw, carry bags, cutlery etc.)\n\n· I shall always carry a cloth bag, reusable cutlery, straw and cup.\n\n· NOT purchase fruits and vegetables wrapped in plastic films\n\n· Sensitize peers, friends and family about minimizing single use plastic\n\n· Sort my waste for recycling and disposal\n\n. Ask restaurants NOT to send plastic cutle\n\n… [+596 more chars]",
  "content_hash": "468af87cdb36b1b8cd1b2e20eead03e772488bc84f7d7f241f59d9db1d81f369",
  "token_count": 326,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "chunk_index": 7,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-29T10:53:33.198073+00:00",
  "updated_at": "2026-06-29T10:53:33.198073+00:00"
}
```
