# Qdrant points — Annexure_A2_Commitment-letters.pdf

- points (rows upserted): **7**
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
  "chunk_text": "Annexure- Commitment Letters for participation in the ‘Rethink Plastic’ campaign\\ \n1. Thane Belapur Industries Association (TBIA), Navi Mumbai\n\n2. ICLES Motilal Jhunjhunwala College, Navi Mumbai\nAccredited A Grade by NAAC (Established in 1978)\nICLES' MOTILALJHUNJHUNWALA COLLEGE OF ARTS, SCIENCE & COMMERCE Plot No. 53, Sector - 9A, Amlendu Roye Marg, Vashi, Navi Mumbai - 400 703. Tel. : 022 - 27663061 / 27800800 · Email : info@iclesmj.edu.in, Website : www.iclesmj.edu Permanently Affiliated to the University of Mumbai. Listed u/s 2(f) & 12 (B) of UGC Act 1956\nRef. No .: /ICLES'MJ-(Sr./Jr.)/\nDat\n\n… [+3417 more chars]",
  "content_hash": "b418f6bc947942a345a2cbe8d73836f3c83907b8a4c6aae3813b1aff21e4cc31",
  "token_count": 1159,
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
    4
  ],
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```

## Child · `413ecc28-1d12-5e05-b91d-66c4f487668e`

- vector: dim=3072 · [-0.0024, 0.0023, -0.0157, -0.0108, -0.0039, -0.0160, -0.0022, 0.0267, …]

```json
{
  "chunk_id": "413ecc28-1d12-5e05-b91d-66c4f487668e",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "chunk_text": "Annexure- Commitment Letters for participation in the ‘Rethink Plastic’ campaign\\ \n1. Thane Belapur Industries Association (TBIA), Navi Mumbai\n\n2. ICLES Motilal Jhunjhunwala College, Navi Mumbai\nAccredited A Grade by NAAC (Established in 1978)\nICLES' MOTILALJHUNJHUNWALA COLLEGE OF ARTS, SCIENCE & COMMERCE Plot No. 53, Sector - 9A, Amlendu Roye Marg, Vashi, Navi Mumbai - 400 703. Tel. : 022 - 27663061 / 27800800 · Email : info@iclesmj.edu.in, Website : www.iclesmj.edu Permanently Affiliated to the University of Mumbai. Listed u/s 2(f) & 12 (B) of UGC Act 1956\nRef. No .: /ICLES'MJ-(Sr./Jr.)/\nDat\n\n… [+1027 more chars]",
  "content_hash": "2c123cf42bd6b373c4571cc42412ccdead2cd438e4ac7429847f132a4d931e1b",
  "token_count": 424,
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
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```

## Child · `7fa681b4-1254-580c-933c-7ee308d466f8`

- vector: dim=3072 · [-0.0086, -0.0072, -0.0123, -0.0093, 0.0228, -0.0111, -0.0299, 0.0277, …]

```json
{
  "chunk_id": "7fa681b4-1254-580c-933c-7ee308d466f8",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "chunk_text": "Moreover, being part of a responsible Educational Institution,we would also like to participate in future events not only for this campaign but other activitiesrelated to environment conservation as well.\nThanking You\nAladhar Varhi N.4 Mumeal 409703. COLU\nDr Anita S.Jadhav Associate Professor Head Department of Zoology\n\n3. Karmaveer Bhaurao Patil College, Navi Mumbai\nRayat Shikshan Sanstha's KARMAVEER BHAURAO PATIL COLLEGE, VASHI (AUTONOMOUS COLLEGE)\nSector 15-A, Vashi, Navi Mumbai - 400 703. (Maharashtra) (O): 022-2766 1210 (Fax) : 022-2789 1210 Email : principal@kbpcollegevashi.edu.in * Web \n\n… [+756 more chars]",
  "content_hash": "55884b05fabaa22db1ef4d5834b601d2d32b01f3170af0f60d928fa8b31f4fca",
  "token_count": 396,
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
  "chunk_index": 1,
  "page_number": 2,
  "page_range": [
    2,
    3
  ],
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```

## Child · `bd12525a-67a8-567f-b327-c413f54650c7`

- vector: dim=3072 · [-0.0148, 0.0418, -0.0099, 0.0276, -0.0037, -0.0161, -0.0530, 0.0175, …]

```json
{
  "chunk_id": "bd12525a-67a8-567f-b327-c413f54650c7",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "chunk_text": "E\nBEST COLLEGE AWARD UNIVERSITY OF MUMBAI Towards this, our Institution commits to provide -58 number of native tree saplings collected from roadsides and raised in waste plastic bottles. We shall also appeal to our staff members and students to take a pledge to avoid single use plastic and participate in perception survey on plastic usage and its management. Moreover, being part of a responsible Educational Institution, we would also like to participate in future events not only for this campaign but other activities related to environment conservation as well.\n150 9001-2015 INTERNATIONAL ACC\n\n… [+700 more chars]",
  "content_hash": "4c967b9fdec8174c31333c0d7f34dc6b691a007ffd897ba80e6f6c64e2fdd321",
  "token_count": 392,
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
  "chunk_index": 2,
  "page_number": 3,
  "page_range": [
    3,
    4
  ],
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```

## Child · `9703f35e-b5fa-5d5b-9cb1-31d85f1b023d`

- vector: dim=3072 · [-0.0183, 0.0059, -0.0089, -0.0269, -0.0110, -0.0057, 0.0058, 0.0520, …]

```json
{
  "chunk_id": "9703f35e-b5fa-5d5b-9cb1-31d85f1b023d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "2014-20151",
  "chunk_text": "#2014-2015 8\nX2055.20141\nRef. No\n5 ** February, 2020\nTa,\nDr. Anjali Parasnis Associate Director\nThe Energy and Resources Institute -Western Regional Centre (TERI-WRC) CBD-Belapur, Navi Mumbai, 400614\nIn line with our Institute's commitment towards Environment Conservation, we hereby agree to join hands with TERI-WRC and United Nations Environment Programme (UNEP) for the \"Rethink Plastic' campaign under the project titled \"Promotion of countermeasures against marine plastic litter in Southeast Asia and India\".\nTowards this, our Institutionhas provided218 number cf native tree saplings collecte\n\n… [+471 more chars]",
  "content_hash": "7ada7b40abffeed35419d6e71d5c8f74c9f8b45fdff7ab43b3052d3810d8e4d1",
  "token_count": 232,
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
  "page_number": 4,
  "page_range": [
    4,
    5
  ],
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```

## Child · `8a35b735-fc05-5ca3-a86b-a5a9e9c0be9d`

- vector: dim=3072 · [-0.0404, -0.0016, -0.0045, -0.0163, -0.0123, -0.0172, 0.0020, 0.0291, …]

```json
{
  "chunk_id": "8a35b735-fc05-5ca3-a86b-a5a9e9c0be9d",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "5. IndusInd Bank — IndusInd Bank",
  "chunk_text": "Date: January 13, 2020\nTo, Dr Anjali Parasnis Associate Director The Energy & Resources Institute CBD - Belapur, Navi Mumbai\nIn line with the Banks commitment towards Environment Conservation, we herewith join hands with TERI (The Energy & Resources Institute) and UNEP (United Nations Environment Programme) for the initiative \"Promotion of countermeasures against marine plastic litter in Southeast Asia and India\" and the campaign on \"ReThink Plastic'.\nWe shall appeal to our employees to take a pledge on the aforementioned cause.\nWe also permit usage of the Bank's logo as supporting associate i\n\n… [+493 more chars]",
  "content_hash": "f558e9b943cf0f44d66cdb60dafe590ca2631be6dae0e2ec0ae59381211218ac",
  "token_count": 289,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "chunk_index": 4,
  "page_number": 5,
  "page_range": [
    5,
    5
  ],
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```

## Child · `7cc4b842-7e58-5f6c-83c9-fbba04c512e9`

- vector: dim=3072 · [-0.0281, -0.0121, -0.0037, -0.0000, 0.0017, -0.0060, -0.0058, 0.0235, …]

```json
{
  "chunk_id": "7cc4b842-7e58-5f6c-83c9-fbba04c512e9",
  "document_id": "annexure_a2_commitment_letters_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_A2_Commitment-letters.pdf",
  "section_heading": "LNETEL — Netel (India) Limited",
  "chunk_text": "17.12.19\nPledge against Single Use Plastic\nAs a good citizen of my country and a responsible resident of the planet Earth, I pledge to Refuse, Reduce, Recycle, Reuse, Repair, Re-gift, Recover and \"Rethink plastic\", to the best of my efforts by doing the following:\n. I shall say \"NO\" to single use plastic items (Straw, carry bags, cutlery etc.)\n. I shall always carry a cloth bag, reusable cutlery, straw and cup.\nNOT purchase fruits and vegetables wrapped in plastic films\n· Sensitize peers, friends and family about minimizing single use plastic\n· Sort my waste for recycling and disposal\n. Ask re\n\n… [+699 more chars]",
  "content_hash": "63ba1c54df5b47cd2ed489da6eb2e5a5db1f8f4ed69fb74af577ab703e61a8b9",
  "token_count": 378,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_a2_commitment_letters_pdf",
  "pdf_path": "Annexure_A2_Commitment-letters.pdf",
  "chunk_index": 5,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-30T08:31:47.981366+00:00",
  "updated_at": "2026-06-30T08:31:47.981366+00:00"
}
```
