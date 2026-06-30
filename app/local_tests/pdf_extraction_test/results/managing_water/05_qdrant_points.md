# Qdrant points — managing-water.pdf

- points (rows upserted): **4**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `4f263bfa-e4c6-5431-8a85-f6db47c4ee91`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "4f263bfa-e4c6-5431-8a85-f6db47c4ee91",
  "document_id": "managing_water_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "IN PERSPECTIVE",
  "chunk_text": "IN PERSPECTIVE\n\nIntegrated means of managing water\nNeed to promote development of water, land, other resources in a sustainable manner\nSK Sarkar\nfor many years, policymak- Fers have adopted a top- down approach in water management. But this tradition- al approach is not enough now, given the complexity of rapidly ageing water infrastructure, population growth, rapid eco- nomic growth, climate change, and increasing urbanisation. Thus, an alternative approach is called for.\nIn the 19th century, the top- down approach was successful as the available water resources were adequate to meetthe needs\n\n… [+4912 more chars]",
  "content_hash": "7d88a241b48e7039ad8f95e760483030407cc0137cd411a49b4c15077f68115a",
  "token_count": 1122,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "managing_water_pdf",
  "pdf_path": "managing-water.pdf",
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:50.250425+00:00",
  "updated_at": "2026-06-30T08:33:50.250425+00:00"
}
```

## Child · `8063e1f4-c648-565a-b73f-e87fc5ca76a5`

- vector: dim=3072 · [-0.0459, -0.0013, -0.0124, -0.0240, -0.0090, -0.0087, -0.0010, 0.0047, …]

```json
{
  "chunk_id": "8063e1f4-c648-565a-b73f-e87fc5ca76a5",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "IN PERSPECTIVE",
  "chunk_text": "Integrated means of managing water\nNeed to promote development of water, land, other resources in a sustainable manner\nSK Sarkar\nfor many years, policymak- Fers have adopted a top- down approach in water management. But this tradition- al approach is not enough now, given the complexity of rapidly ageing water infrastructure, population growth, rapid eco- nomic growth, climate change, and increasing urbanisation. Thus, an alternative approach is called for.\nIn the 19th century, the top- down approach was successful as the available water resources were adequate to meetthe needs of the populati\n\n… [+1193 more chars]",
  "content_hash": "a20351d9f75d679aa75e4b7a26553b177223af6299d71dac2982f5e019895108",
  "token_count": 375,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "managing_water_pdf",
  "pdf_path": "managing-water.pdf",
  "parent_chunk_id": "4f263bfa-e4c6-5431-8a85-f6db47c4ee91",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:50.250425+00:00",
  "updated_at": "2026-06-30T08:33:50.250425+00:00"
}
```

## Child · `2d3d3b45-8c59-57a5-8582-1b3e67c1ceac`

- vector: dim=3072 · [-0.0320, 0.0084, -0.0101, -0.0108, 0.0011, 0.0104, 0.0217, -0.0025, …]

```json
{
  "chunk_id": "2d3d3b45-8c59-57a5-8582-1b3e67c1ceac",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "IN PERSPECTIVE",
  "chunk_text": "These goals also stipulate the implementation of integrated waterresource man- agement at all levels by 2030. A holistic approach is called for. Integrated water resource management at all levels is an appropriate framework. It pro- motes the coordinated develop- ment and management of wa- ter, landandrelatedresourcesto maximise economic and social welfare equitably and sustain- ably. It is thus a cross-sectoral policy approach to replace the traditional and fragmented ap- proach to water management.\nPolicymakers should invoke the Dublin Principles (1992) of the United Nations on water and env\n\n… [+1488 more chars]",
  "content_hash": "e29d74b058f2bd05c5adfa9e2c194ca9f8964e42f535511585e2334699615da8",
  "token_count": 423,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "managing_water_pdf",
  "pdf_path": "managing-water.pdf",
  "parent_chunk_id": "4f263bfa-e4c6-5431-8a85-f6db47c4ee91",
  "chunk_index": 1,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:50.250425+00:00",
  "updated_at": "2026-06-30T08:33:50.250425+00:00"
}
```

## Child · `d346549e-8ec5-5a7f-a35e-eea0620498d9`

- vector: dim=3072 · [-0.0501, -0.0048, -0.0158, -0.0123, -0.0237, -0.0039, 0.0266, -0.0016, …]

```json
{
  "chunk_id": "d346549e-8ec5-5a7f-a35e-eea0620498d9",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "IN PERSPECTIVE",
  "chunk_text": "For example, the 'nexus approach' can provide an excellent mech- anism for facilitating dialogue between relevant sectors (for example, food, water, and ener- gy) in a given context. Similarly, the 'ecosystem' based approach prioritises ecosystem functioning and its related goods and services. In the context of water resources, ecosystem approach regulates water quality and quantity, habitat resources and offers na- ture-based solutions.\nCritics, however, point out that there are some pitfalls in the integrated water resources management approach: col- laboration is time-consuming and resource\n\n… [+1306 more chars]",
  "content_hash": "66665d43d1af1d931d943094346d58cd53e9417170d791f28870f210aeafd3a3",
  "token_count": 382,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "managing_water_pdf",
  "pdf_path": "managing-water.pdf",
  "parent_chunk_id": "4f263bfa-e4c6-5431-8a85-f6db47c4ee91",
  "chunk_index": 2,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:50.250425+00:00",
  "updated_at": "2026-06-30T08:33:50.250425+00:00"
}
```
