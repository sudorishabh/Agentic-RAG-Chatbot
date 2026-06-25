# Qdrant points — check-your-water-quality.pdf

- points (rows upserted): **3**
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
  "chunk_text": "HOW TO CHECK WATER QUALITYA\n\n| SI. No. | Parameters | Method | Desirable Limit | Undesirable effect outisde the desirable limit | Permissible limit in the absence of alternate source | Cause of these parameters in water |\n| --- | --- | --- | --- | --- | --- | --- |\n| 1. | Colour (Hazen Units, max) | By Visual | 5 | Above 5 consumer acceptance decreases. | 15 | Due to natural metallic, ions, humus, peat material, industrial waste. |\n| 2. | Odour | By smell | Agreeable |  | Agreeable | Organic & inorganic waste from municipal and industrial waste discharge, or due to natural sources. |\n| 3. | pH\n\n… [+1713 more chars]",
  "content_hash": "6d08338c6796a84b1b6eca525fff15f2e0e09be257f22a045cc323107b0aaad7",
  "token_count": 738,
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
  "created_at": "2026-06-25T11:23:15.947981+00:00",
  "updated_at": "2026-06-25T11:23:15.947981+00:00"
}
```

## Child · `77306fc6-cc8b-56ac-b66a-6c471b31ef45`

- vector: dim=3072 · [-0.0159, -0.0098, 0.0100, 0.0250, -0.0098, -0.0174, -0.0244, -0.0102, …]

```json
{
  "chunk_id": "77306fc6-cc8b-56ac-b66a-6c471b31ef45",
  "document_id": "check_your_water_quality_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "check-your-water-quality.pdf",
  "section_heading": "HOW TO CHECK WATER QUALITYA",
  "chunk_text": "| SI. No. | Parameters | Method | Desirable Limit | Undesirable effect outisde the desirable limit | Permissible limit in the absence of alternate source | Cause of these parameters in water |\n| --- | --- | --- | --- | --- | --- | --- |\n| 1. | Colour (Hazen Units, max) | By Visual | 5 | Above 5 consumer acceptance decreases. | 15 | Due to natural metallic, ions, humus, peat material, industrial waste. |\n| 2. | Odour | By smell | Agreeable |  | Agreeable | Organic & inorganic waste from municipal and industrial waste discharge, or due to natural sources. |\n| 3. | pH | by pH paper strip | 6.5-8.\n\n… [+1088 more chars]",
  "content_hash": "e919f723693c2eb782506a120dae04093f5d3594849aef2cc391856d80af291a",
  "token_count": 462,
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
  "created_at": "2026-06-25T11:23:15.947981+00:00",
  "updated_at": "2026-06-25T11:23:15.947981+00:00"
}
```

## Child · `7bdd4fe5-b74f-585a-90eb-1de38e9bd9ae`

- vector: dim=3072 · [-0.0359, -0.0020, 0.0032, 0.0264, -0.0164, -0.0339, -0.0185, 0.0164, …]

```json
{
  "chunk_id": "7bdd4fe5-b74f-585a-90eb-1de38e9bd9ae",
  "document_id": "check_your_water_quality_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "check-your-water-quality.pdf",
  "section_heading": "HOW TO CHECK WATER QUALITYA",
  "chunk_text": "decomposition of organic residue |\n| 8. | Residual, free Chlorine mg/l min | Colorimetric (ortho toluidine) | 0.2 | - | 1 | Chlorinated industrial effluent, sewage waste. | \\* Drinking water quality standard as per IS-10500, 2012.\n\n| PERIOD | I | II | II | III | IV | エ | V | VI | VII | VIII |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| TIME |  |  |  |  |  |  |  |  |  |  |\n| MONDAY |  |  |  |  |  | LUNC |  |  |  |  |\n| TUESDAY |  |  |  |  |  |  |  |  |  |  |\n| WEDNESDAY |  |  |  |  |  |  |  |  |  |  |\n| THURSDAY |  |  |  |  |  |  |  |  |  |  |\n| FRIDAY |  |  |  |  |  |\n\n… [+167 more chars]",
  "content_hash": "6ab194a375a5d710ba682cc703b568aa0bf895bc34415444c5f39c579fc43a06",
  "token_count": 319,
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
  "chunk_index": 1,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-25T11:23:15.947981+00:00",
  "updated_at": "2026-06-25T11:23:15.947981+00:00"
}
```
