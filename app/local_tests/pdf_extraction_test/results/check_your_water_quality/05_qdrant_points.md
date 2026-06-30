# Qdrant points — check-your-water-quality.pdf

- points (rows upserted): **1**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `77306fc6-cc8b-56ac-b66a-6c471b31ef45`

- vector: dim=3072 · [-0.0318, 0.0087, 0.0113, 0.0403, -0.0061, -0.0194, -0.0279, 0.0023, …]

```json
{
  "chunk_id": "77306fc6-cc8b-56ac-b66a-6c471b31ef45",
  "document_id": "check_your_water_quality_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "check-your-water-quality.pdf",
  "section_heading": "HOW TO CHECK+ WATER QUALITY!",
  "chunk_text": "SI No.\nParameters\nMethod\nDesirable Limit\nUndesirable effect outisde the desirable limit\nPermissible limit in the absence of alternate source\nCause of these parameters in water\n1.\nColour (Hazen Units, max)\nBy Visual\n5\nAbove 5 consumer acceptance decreases.\n15\nDue to natural metallic, ions, humus, peat material, industrial waste.\n2.\nOdour\nBy smell\nAgreeable\nAgreeable\nOrganic & inorganic waste from municipal and industrial waste discharge, or due to natural sources.\n3.\nPH\nby pH paper strip\n6.5-8.5\nBeyond this range the water will affect the mucous membrane and/or water supply system.\nNo relaxatio\n\n… [+1160 more chars]",
  "content_hash": "691926101a070a63773680a01080bb57d62ef753dfc90d8826dddbbdb34fbc66",
  "token_count": 500,
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
  "created_at": "2026-06-30T08:32:52.646088+00:00",
  "updated_at": "2026-06-30T08:32:52.646088+00:00"
}
```
