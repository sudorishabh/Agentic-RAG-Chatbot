# Qdrant points — Annexure_A2_Commitment-letters.pdf

- points (rows upserted): **16**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `50f2c586-9666-5112-b982-1a256719daa8`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "50f2c586-9666-5112-b982-1a256719daa8",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "OCATION — ICLES' — MOTILALJHUNJHUNWALA COLLEGE — OF ARTS, SCIENCE & COMMERCE",
  "chunk_text": "OCATION — ICLES' — MOTILALJHUNJHUNWALA COLLEGE — OF ARTS, SCIENCE & COMMERCE\n\nAnnexure- Commitment Letters for participation in the ‘Rethink Plastic’ campaign\\ \n1. Thane Belapur Industries Association (TBIA), Navi Mumbai\n\n2\\. ICLES Motilal Jhunjhunwala College, Navi Mumbai\n\nPlot No. 53, Sector - 9A, Amlendu Roye Marg, Vashi, Navi Mumbai - 400 703.\nTel. : 022 - 27663061 / 27800800 · Email : info@iclesmj.edu.in, Website : www.iclesmj.edu\nPermanently Affiliated to the University of Mumbai.\nListed u/s 2(f) & 12 (B) of UGC Act 1956",
  "content_hash": "1480cbe3f74f05b78a09b48f4dc8fa9c44ff7ef4fc7439ab0aa0012a7d445719",
  "token_count": 186,
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
    1,
    2
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

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
  "parent_chunk_id": "50f2c586-9666-5112-b982-1a256719daa8",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    2
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
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
  "chunk_text": "Accredited A Grade by NAAC\n\n(Established in 1978)\n\nRef. No .:\n/ICLES'MJ-(Sr./Jr.)/\n\nDate :\n\nDate: 27/2/2020\n\nTo.\n\nIn line with our Institute's commitment towards Environment Conservation, we hereby\nagree to join hands with TERI-WRC and United Nations Environment Programme (UNEP)\nfor the 'Rethink Plastic' campaign under the project titled \"Promotion of countermeasures\nagainst marine plastic litter in Southeast Asia and India\".\n\nTowards this, our Institution commits to provide 100 number of native tree saplings\ncollected from roadsides and raised in waste plastic bottles. We shall also appeal to\n\n… [+1471 more chars]",
  "content_hash": "5cfe3353b67a5ab960ff2d510fc90576920b22f1dfed2b5196fbe7f5c6b5df2a",
  "token_count": 577,
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
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `7fa681b4-1254-580c-933c-7ee308d466f8`

- vector: dim=3072 · [-0.0202, -0.0180, -0.0098, -0.0105, 0.0062, -0.0153, -0.0108, 0.0406, …]

```json
{
  "chunk_id": "7fa681b4-1254-580c-933c-7ee308d466f8",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Accredited A Grade by NAAC",
  "chunk_text": "(Established in 1978)\n\nRef. No .:\n/ICLES'MJ-(Sr./Jr.)/\n\nDate :\n\nDate: 27/2/2020\n\nTo.\n\nIn line with our Institute's commitment towards Environment Conservation, we hereby\nagree to join hands with TERI-WRC and United Nations Environment Programme (UNEP)\nfor the 'Rethink Plastic' campaign under the project titled \"Promotion of countermeasures\nagainst marine plastic litter in Southeast Asia and India\".\n\nTowards this, our Institution commits to provide 100 number of native tree saplings\ncollected from roadsides and raised in waste plastic bottles. We shall also appeal to our\nstaff members and stude\n\n… [+880 more chars]",
  "content_hash": "e894dcd9609c90f901aed9263d6e9dc535738f8d8a37d7910bcdeb49363c57b1",
  "token_count": 409,
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
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `bd12525a-67a8-567f-b327-c413f54650c7`

- vector: dim=3072 · [-0.0195, 0.0113, -0.0120, -0.0158, 0.0057, -0.0052, -0.0032, 0.0470, …]

```json
{
  "chunk_id": "bd12525a-67a8-567f-b327-c413f54650c7",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Accredited A Grade by NAAC",
  "chunk_text": "V. S. Shivankar\n\nFOUNDER : Padmabhushan Dr. Karmaveer Bhaurao Patil, D. Litt. Ref. No .: 1202/2019-2020\n\nDate : 6/3/2020\n\nAUTONOMOUS — COLLEGE\n\nTo,\n\nNAAC GRADE 'A+' — COPA 3.53\n\nSub: Commitment Towards Environment Conservation\n\nDET-STAR COLLEGE — SCHEME — GOVERNMENT OF INDIA — (SINCE 2054)\n\nDear Madam,\nthrough self-help\n\nIn line with our Institute's commitment towards Environment Conservation, we\nhereby agree to join hands with TERI-WRC and United Nations Environment\nProgramme (UNEP) for the 'Rethink Plastic' campaign under the project titled\n\"\"Promotion of countermeasures against marine plast\n\n… [+39 more chars]",
  "content_hash": "f973d35f23d4d1b4fd2bad401a23f03735984d5e11937557dc9db735b8e828dc",
  "token_count": 192,
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
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Parent · `7174166f-660a-5058-b9e4-d63ab6497bf7`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "7174166f-660a-5058-b9e4-d63ab6497bf7",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "DST-FIST SCHEME — GOVERNMENT OF INDIA — (SINCE 2013 — BEST COLLEGE AWARD — UNIVERSITY OF MUMBAI",
  "chunk_text": "DST-FIST SCHEME — GOVERNMENT OF INDIA — (SINCE 2013 — BEST COLLEGE AWARD — UNIVERSITY OF MUMBAI\n\n\\-\n\nTowards this, our Institution commits to provide -58 number of native tree\nsaplings collected from roadsides and raised in waste plastic bottles. We shall\nalso appeal to our staff members and students to take a pledge to avoid single use\nplastic and participate in perception survey on plastic usage and its management.\nMoreover, being part of a responsible Educational Institution, we would also like\nto participate in future events not only for this campaign but other activities\nrelated to enviro\n\n… [+27 more chars]",
  "content_hash": "79d2a5f4c0356fa17c624095a319f0c1f5786d3764d9b9600c44e446f2f5d472",
  "token_count": 136,
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
    3
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `9703f35e-b5fa-5d5b-9cb1-31d85f1b023d`

- vector: dim=3072 · [-0.0213, -0.0017, -0.0166, -0.0220, -0.0078, 0.0020, 0.0043, 0.0488, …]

```json
{
  "chunk_id": "9703f35e-b5fa-5d5b-9cb1-31d85f1b023d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "DST-FIST SCHEME — GOVERNMENT OF INDIA — (SINCE 2013 — BEST COLLEGE AWARD — UNIVERSITY OF MUMBAI",
  "chunk_text": "\\-\n\nTowards this, our Institution commits to provide -58 number of native tree\nsaplings collected from roadsides and raised in waste plastic bottles. We shall\nalso appeal to our staff members and students to take a pledge to avoid single use\nplastic and participate in perception survey on plastic usage and its management.\nMoreover, being part of a responsible Educational Institution, we would also like\nto participate in future events not only for this campaign but other activities\nrelated to environment conservation as well.",
  "content_hash": "c5d491637a5f38b96586601a6fcb9f5ce78bc4f6844f7b7bc6a1a525cddd8db3",
  "token_count": 100,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "7174166f-660a-5058-b9e4-d63ab6497bf7",
  "chunk_index": 3,
  "page_number": 3,
  "page_range": [
    3,
    3
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
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
  "section_heading": "ISO 9001:2015 — INTERNATIONAL — ACCREDITATION FORUM — (SINCE 2917) — COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College",
  "chunk_text": "ISO 9001:2015 — INTERNATIONAL — ACCREDITATION FORUM — (SINCE 2917) — COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College\n\nVashi, Navi Mumbai-400703.\n\n€\n\n4\\. Maharshi Dayanand College of Arts, Science and Commerce, Mumbai\n\nMaharshi Dayanand College of Arts, Science & Commerce\nNAAC - REACCREDITED - A GRADE\n\nॐ\n\nSHRI MANGALDAS VERMA CHOWK, 25, Dr. 5.5.RAO ROAD, PAREL, MUMBAJ - 400012.\nPHONE : 2410 4541 / 2410 0012 FAX : 2410 6960 Email : principal@/mdcollage.in\n\n। यहडिसनिम अल्पति ।।\n\n12016-2\n\n… [+1184 more chars]",
  "content_hash": "5a5979488736e85eb6cfc26da7d9c14181f3653c105f85c4b5825fc964633455",
  "token_count": 532,
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
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `8a35b735-fc05-5ca3-a86b-a5a9e9c0be9d`

- vector: dim=3072 · [-0.0250, 0.0293, -0.0101, 0.0305, 0.0071, 0.0113, -0.0244, 0.0310, …]

```json
{
  "chunk_id": "8a35b735-fc05-5ca3-a86b-a5a9e9c0be9d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "ISO 9001:2015 — INTERNATIONAL — ACCREDITATION FORUM — (SINCE 2917) — COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College",
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
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `7cc4b842-7e58-5f6c-83c9-fbba04c512e9`

- vector: dim=3072 · [-0.0181, -0.0018, -0.0094, -0.0301, -0.0040, -0.0088, 0.0050, 0.0544, …]

```json
{
  "chunk_id": "7cc4b842-7e58-5f6c-83c9-fbba04c512e9",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "ISO 9001:2015 — INTERNATIONAL — ACCREDITATION FORUM — (SINCE 2917) — COMMUNITY — COLLEGE — UNIVERSITY OF MUMILAL — Thanking You — MERIT IN — INNOVATION AWARD — HIGHER EDUCATION FORUM — Principal — Marmaveer Bhaurao Patil College",
  "chunk_text": "hereby\nagree to join hands with TERI-WRC and United Nations Environment Programme (UNEP) for the\n'Rethink Plastic' campaign under the project titled \"Promotion of countermeasures against\nmarine plastic litter in Southeast Asia and India\". Towards this, our Institutionhas provided218 number cf native tree saplings collected\nfrom roadsides and raised in waste plastic bottles. We shall also appeal to our staff members\nand students to take a pledge to avoid single use plastic and participate inperception survey on\nplastic usage and its management. Moreover, being part of a responsible Educational\n\n\n… [+246 more chars]",
  "content_hash": "89f1b39e8ba7600427ea366bd27652508ba950576c47c8bf06ae75ef3dc935b7",
  "token_count": 179,
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
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Parent · `8026bbc6-663b-5280-bc2c-34f3c8d73cd0`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "8026bbc6-663b-5280-bc2c-34f3c8d73cd0",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "IndusInd Bank",
  "chunk_text": "IndusInd Bank\n\nDate: January 13, 2020\n\nTo,\nDr Anjali Parasnis\nThe Energy & Resources Institute\nCBD - Belapur, Navi Mumbai\n\nIn line with the Banks commitment towards Environment Conservation, we herewith join hands with\nTERI (The Energy & Resources Institute) and UNEP (United Nations Environment Programme) for the\ninitiative \"Promotion of countermeasures against marine plastic litter in Southeast Asia and India\" and\nthe campaign on \"ReThink Plastic'.\n\nWe shall appeal to our employees to take a pledge on the aforementioned cause.\n\nWe also permit usage of the Bank's logo as supporting associate i\n\n… [+89 more chars]",
  "content_hash": "6e59cb232ef4b809f8bd79fc58aa9601d87eb90f5df16f124947ef3ce48bec2a",
  "token_count": 159,
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
    5,
    5
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `0001ebf6-4aec-5d42-a331-32bffe649c0d`

- vector: dim=3072 · [-0.0309, -0.0135, -0.0047, -0.0049, -0.0155, -0.0115, 0.0088, 0.0471, …]

```json
{
  "chunk_id": "0001ebf6-4aec-5d42-a331-32bffe649c0d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "IndusInd Bank",
  "chunk_text": "Date: January 13, 2020\n\nTo,\nDr Anjali Parasnis\nThe Energy & Resources Institute\nCBD - Belapur, Navi Mumbai\n\nIn line with the Banks commitment towards Environment Conservation, we herewith join hands with\nTERI (The Energy & Resources Institute) and UNEP (United Nations Environment Programme) for the\ninitiative \"Promotion of countermeasures against marine plastic litter in Southeast Asia and India\" and\nthe campaign on \"ReThink Plastic'.\n\nWe shall appeal to our employees to take a pledge on the aforementioned cause.\n\nWe also permit usage of the Bank's logo as supporting associate in the campaign \n\n… [+74 more chars]",
  "content_hash": "17d8fc2c32fc862ab3dd32658cba6027933986950db299618b458cd2c775c551",
  "token_count": 154,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "8026bbc6-663b-5280-bc2c-34f3c8d73cd0",
  "chunk_index": 6,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Parent · `ec8f80ba-12c7-520b-9ee5-36cf6029e7cc`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ec8f80ba-12c7-520b-9ee5-36cf6029e7cc",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Head -Corporate Services — Indusind Bank Limited",
  "chunk_text": "Head -Corporate Services — Indusind Bank Limited\n\nAndheri East, Mumbai 400093\n\nPILA House Officer Indusind Bank Limited, Basement, Ist Floor, 3rd Floor & cth Floor,\nPNA House, Plet No 57, Street No. 17,MIDC, Andheri, Mumbai 400 093, India. Tel: (0022) 61069299\n\nRegistered Office: 2401 Gen. Thinmayya Road, Pine-411:001, Inda\nTel: (020) 2634 3201 Fax: (020) 2634 3241 Wist us at www.indunsind.com\nCN:L65191PN1994PLC076333\n\n<!-- PageBreak -\n\n->\n\n6\\. Netel (India) Limited\n\nNETEL — Netel (India) Limited\n\n17.12.19",
  "content_hash": "e14b8ca42a1afcdab7f8df40473d6f9fecb89691a49fc3370aae362a1dfd6d7e",
  "token_count": 183,
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
    5,
    6
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `e962f55b-36af-5c74-90b2-77fea0ee4cd3`

- vector: dim=3072 · [-0.0082, 0.0133, -0.0025, 0.0064, 0.0019, 0.0039, -0.0321, 0.0438, …]

```json
{
  "chunk_id": "e962f55b-36af-5c74-90b2-77fea0ee4cd3",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Head -Corporate Services — Indusind Bank Limited",
  "chunk_text": "Andheri East, Mumbai 400093\n\nPILA House Officer Indusind Bank Limited, Basement, Ist Floor, 3rd Floor & cth Floor,\nPNA House, Plet No 57, Street No. 17,MIDC, Andheri, Mumbai 400 093, India. Tel: (0022) 61069299\n\nRegistered Office: 2401 Gen. Thinmayya Road, Pine-411:001, Inda\nTel: (020) 2634 3201 Fax: (020) 2634 3241 Wist us at www.indunsind.com\nCN:L65191PN1994PLC076333\n\n<!-- PageBreak -\n\n->\n\n6\\. Netel (India) Limited\n\nNETEL — Netel (India) Limited\n\n17.12.19",
  "content_hash": "725e8e212b6e2dc3b34e3fcde6cf30a7093211d0a768585266f36c2167bb5e4d",
  "token_count": 172,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "parent_chunk_id": "ec8f80ba-12c7-520b-9ee5-36cf6029e7cc",
  "chunk_index": 7,
  "page_number": 5,
  "page_range": [
    5,
    6
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Parent · `e3555a0f-a883-5816-9ca0-0e5a5c4c71d2`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e3555a0f-a883-5816-9ca0-0e5a5c4c71d2",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "Pledge against Single Use Plastic",
  "chunk_text": "Pledge against Single Use Plastic\n\nAs a good citizen of my country and a responsible resident of the planet Earth, I\npledge to Refuse, Reduce, Recycle, Reuse, Repair, Re-gift, Recover and\n\"Rethink plastic\", to the best of my efforts by doing the following:\n\n. I shall say \"NO\" to single use plastic items (Straw, carry bags, cutlery etc.)\n\n· I shall always carry a cloth bag, reusable cutlery, straw and cup.\n\n· NOT purchase fruits and vegetables wrapped in plastic films\n\n· Sensitize peers, friends and family about minimizing single use plastic\n\n· Sort my waste for recycling and disposal\n\n. Ask re\n\n… [+631 more chars]",
  "content_hash": "2e4284559b20b8ee196784a38875a0b872facd287946f8830d6900132af801d6",
  "token_count": 333,
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
    6,
    6
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```

## Child · `8fb9f143-c296-57f5-a878-084fe5596da8`

- vector: dim=3072 · [-0.0273, -0.0122, -0.0090, -0.0088, -0.0038, -0.0053, -0.0110, 0.0112, …]

```json
{
  "chunk_id": "8fb9f143-c296-57f5-a878-084fe5596da8",
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
  "parent_chunk_id": "e3555a0f-a883-5816-9ca0-0e5a5c4c71d2",
  "chunk_index": 8,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-25T12:29:44.297551+00:00",
  "updated_at": "2026-06-25T12:29:44.297551+00:00"
}
```
