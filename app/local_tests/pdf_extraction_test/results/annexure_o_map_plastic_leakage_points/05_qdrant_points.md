# Qdrant points — Annexure_O_Map-Plastic-Leakage-Points.pdf

- points (rows upserted): **1**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `021607f7-4afe-58a0-81db-13cb022b38e3`

- vector: dim=3072 · [-0.0178, 0.0040, -0.0044, -0.0206, -0.0176, -0.0222, -0.0092, 0.0458, …]

```json
{
  "chunk_id": "021607f7-4afe-58a0-81db-13cb022b38e3",
  "document_id": "annexure_o_map_plastic_leakage_points_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_O_Map-Plastic-Leakage-Points.pdf",
  "section_heading": "UN@",
  "chunk_text": "environment\nprogramme\n\nCounter — MEASURE — FOR PLASTIC FREE RIVERS\n\nteri\nRETHINK PLASTIC\n\nMicro Plastic Leakage Points — Legend — O Leakage points — Railroads — Drains and Rivers — MMR Boundary — Built Up — Water Bodies — Slums\n\n0 3.5 7\n\n14\n\n21\n\n28\n\nKilometers",
  "content_hash": "cf14c5df641a0ea0fca72793a6027196beb91f2b71b723c9bc1812e6fafdf0ce",
  "token_count": 77,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "annexure_o_map_plastic_leakage_points_pdf",
  "pdf_path": "Annexure_O_Map-Plastic-Leakage-Points.pdf",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:53:49.641499+00:00",
  "updated_at": "2026-06-29T10:53:49.641499+00:00"
}
```
