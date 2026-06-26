# Qdrant points — check-your-water-quality.pdf

- points (rows upserted): **2**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `e4c27ba6-2f19-5b37-af6b-63f6f36c9a69`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "e4c27ba6-2f19-5b37-af6b-63f6f36c9a69",
  "document_id": "check_your_water_quality_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "check-your-water-quality.pdf",
  "section_heading": "HOW TO CHECK WATER QUALITYA",
  "chunk_text": "HOW TO CHECK WATER QUALITYA\n\n| SI. No. | Parameters | Method | Desirable Limit | Undesirable effect outisde the desirable limit | Permissible limit in the absence of alternate source | Cause of these parameters in water |\n| --- | --- | --- | --- | --- | --- | --- |\n| 1. | Colour (Hazen Units, max) | By Visual | 5 | Above 5 consumer acceptance decreases. | 15 | Due to natural metallic, ions, humus, peat material, industrial waste. |\n| 2. | Odour | By smell | Agreeable |  | Agreeable | Organic & inorganic waste from municipal and industrial waste discharge, or due to natural sources. |\n| 3. | pH\n\n… [+1285 more chars]",
  "content_hash": "8c9db7701ba5724aad1d2cfc40dd135f4edd76796968e02485e10d36af2a53e0",
  "token_count": 515,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "check_your_water_quality_pdf",
  "pdf_path": "check-your-water-quality.pdf",
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-25T12:30:53.645456+00:00",
  "updated_at": "2026-06-25T12:30:53.645456+00:00"
}
```

## Child · `77306fc6-cc8b-56ac-b66a-6c471b31ef45`

- vector: dim=3072 · [-0.0321, 0.0013, 0.0108, 0.0360, -0.0120, -0.0213, -0.0210, -0.0123, …]

```json
{
  "chunk_id": "77306fc6-cc8b-56ac-b66a-6c471b31ef45",
  "document_id": "check_your_water_quality_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "check-your-water-quality.pdf",
  "section_heading": "HOW TO CHECK WATER QUALITYA",
  "chunk_text": "| SI. No. | Parameters | Method | Desirable Limit | Undesirable effect outisde the desirable limit | Permissible limit in the absence of alternate source | Cause of these parameters in water |\n| --- | --- | --- | --- | --- | --- | --- |\n| 1. | Colour (Hazen Units, max) | By Visual | 5 | Above 5 consumer acceptance decreases. | 15 | Due to natural metallic, ions, humus, peat material, industrial waste. |\n| 2. | Odour | By smell | Agreeable |  | Agreeable | Organic & inorganic waste from municipal and industrial waste discharge, or due to natural sources. |\n| 3. | pH | by pH paper strip | 6.5-8.\n\n… [+1256 more chars]",
  "content_hash": "95f67664d9030508aa1e8cb33e9d93877a34b66e302190bf1b20b4fa3ca913ed",
  "token_count": 507,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "check_your_water_quality_pdf",
  "pdf_path": "check-your-water-quality.pdf",
  "parent_chunk_id": "e4c27ba6-2f19-5b37-af6b-63f6f36c9a69",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-25T12:30:53.645456+00:00",
  "updated_at": "2026-06-25T12:30:53.645456+00:00"
}
```
