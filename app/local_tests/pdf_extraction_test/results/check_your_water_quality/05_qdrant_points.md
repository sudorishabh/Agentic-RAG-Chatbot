# Qdrant points — check-your-water-quality.pdf

- points (rows upserted): **1**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

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
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:54:37.906961+00:00",
  "updated_at": "2026-06-29T10:54:37.906961+00:00"
}
```
