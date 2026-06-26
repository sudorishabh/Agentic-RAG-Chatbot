# Qdrant points — make-solar-cooker.pdf

- points (rows upserted): **2**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `ec0f2cf4-3d0f-547d-8d08-e2c31682b2dc`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ec0f2cf4-3d0f-547d-8d08-e2c31682b2dc",
  "document_id": "make_solar_cooker_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "make-solar-cooker.pdf",
  "section_heading": "Let's Make a Solar Cooker! — YOU WILL NEED",
  "chunk_text": "Let's Make a Solar Cooker! — YOU WILL NEED\n\n. a large cardboard box . thermocol . aluminium foil . clear plastic wrap\n. a sheet of black paper . ruler . pair of scissors . glue . tape\n\n1\nStart by taking a cardboard box.\nLeaving an even margin of 2 cm on\neach side, draw a square on its lid.\n\n2\nMake a flap on the lid by cutting\nthree sides of the square. Fold this\nflap out so that it stands up when\nthe lid is closed.\n\n3\nTake five one-inch thick pieces\nof thermocol and stick them to\nthe base and walls of the box so\nthat they provide insulation.\n\n4\nGlue aluminium foil to all\nthe thermocol pieces. \n\n… [+605 more chars]",
  "content_hash": "360e92f186f032cf2847b3d214abf88356318133226537313c917104e21a9391",
  "token_count": 315,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "make_solar_cooker_pdf",
  "pdf_path": "make-solar-cooker.pdf",
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-25T12:31:42.288400+00:00",
  "updated_at": "2026-06-25T12:31:42.288400+00:00"
}
```

## Child · `fd87c043-52e1-5b27-be15-7896aa18ea12`

- vector: dim=3072 · [0.0147, -0.0144, 0.0045, 0.0082, 0.0164, -0.0342, 0.0096, 0.0107, …]

```json
{
  "chunk_id": "fd87c043-52e1-5b27-be15-7896aa18ea12",
  "document_id": "make_solar_cooker_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "make-solar-cooker.pdf",
  "section_heading": "Let's Make a Solar Cooker! — YOU WILL NEED",
  "chunk_text": ". a large cardboard box . thermocol . aluminium foil . clear plastic wrap\n. a sheet of black paper . ruler . pair of scissors . glue . tape\n\n1\nStart by taking a cardboard box.\nLeaving an even margin of 2 cm on\neach side, draw a square on its lid.\n\n2\nMake a flap on the lid by cutting\nthree sides of the square. Fold this\nflap out so that it stands up when\nthe lid is closed.\n\n3\nTake five one-inch thick pieces\nof thermocol and stick them to\nthe base and walls of the box so\nthat they provide insulation.\n\n4\nGlue aluminium foil to all\nthe thermocol pieces. The\nwalls and base of the box\nshould now hav\n\n… [+561 more chars]",
  "content_hash": "626c34980e10d04b79eb3df42df3d9a934807b2af160e9f03e352fb1f91ceaca",
  "token_count": 302,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "make_solar_cooker_pdf",
  "pdf_path": "make-solar-cooker.pdf",
  "parent_chunk_id": "ec0f2cf4-3d0f-547d-8d08-e2c31682b2dc",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-25T12:31:42.288400+00:00",
  "updated_at": "2026-06-25T12:31:42.288400+00:00"
}
```
