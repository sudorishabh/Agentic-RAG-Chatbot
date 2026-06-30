# Qdrant points — make-solar-cooker.pdf

- points (rows upserted): **1**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `fd87c043-52e1-5b27-be15-7896aa18ea12`

- vector: dim=3072 · [0.0149, -0.0283, -0.0014, 0.0156, 0.0103, -0.0240, 0.0007, -0.0039, …]

```json
{
  "chunk_id": "fd87c043-52e1-5b27-be15-7896aa18ea12",
  "document_id": "make_solar_cooker_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "make-solar-cooker.pdf",
  "chunk_text": "Let's Make a Solar Cooker!\nYOU WILL NEED\n. a large cardboard box . thermocol . aluminium foil . clear plastic wrap . a sheet of black paper . ruler . pair of scissors . glue . tape\n1 Start by taking a cardboard box. Leaving an even margin of 2 cm on each side, draw a square on its lid.\n2 Make a flap on the lid by cutting three sides of the square. Fold this flap out so that it stands up when the lid is closed.\n3 Take five one-inch thick pieces of thermocol and stick them to the base and walls of the box so that they provide insulation.\n4 Glue aluminium foil to all the thermocol pieces. The wal\n\n… [+594 more chars]",
  "content_hash": "51add8452b26f0f7d02d4598d907990ee9ab9e3af871de0a4c773164fc40e999",
  "token_count": 277,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "make_solar_cooker_pdf",
  "pdf_path": "make-solar-cooker.pdf",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:47.084948+00:00",
  "updated_at": "2026-06-30T08:33:47.084948+00:00"
}
```
