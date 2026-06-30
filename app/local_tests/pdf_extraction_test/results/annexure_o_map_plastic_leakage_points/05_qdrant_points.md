# Qdrant points — Annexure_O_Map-Plastic-Leakage-Points.pdf

- points (rows upserted): **1**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `021607f7-4afe-58a0-81db-13cb022b38e3`

- vector: dim=3072 · [-0.0179, 0.0213, -0.0123, -0.0222, -0.0127, -0.0066, -0.0016, 0.0415, …]

```json
{
  "chunk_id": "021607f7-4afe-58a0-81db-13cb022b38e3",
  "document_id": "annexure_o_map_plastic_leakage_points_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Annexure_O_Map-Plastic-Leakage-Points.pdf",
  "chunk_text": "UNO environment programme\nCounter MEASURE FOR PLASTIC FREE RIVERS\n00\ntevi\nRETHINK PLASTIC\nMicro Plastic Leakage Points\nLegend\nO Leakage points\n+ + Railroads\nDrains and Rivers MMR Boundary\nBuilt Up\nWater Bodies\nSlums\n0 3.5 7\n14 21 28\nKilometers",
  "content_hash": "b6fed97e4d8baf24f877fabff78730da07ba19c7805a0eb5122bbd42c0c35079",
  "token_count": 78,
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
  "created_at": "2026-06-30T08:32:01.282501+00:00",
  "updated_at": "2026-06-30T08:32:01.282501+00:00"
}
```
