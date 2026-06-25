# Qdrant points — managing-water.pdf

- points (rows upserted): **5**
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
  "section_heading": "SK Sarkar — F",
  "chunk_text": "SK Sarkar — F\n\nIntegrated means of managing water\n\nNeed to promote\ndevelopment of\nwater, land, other\nresources in a\nsustainable manner\n\nfor many years, policymak-\ners have adopted a top-\ndown approach in water\nmanagement. But this tradition-\nal approach is not enough now,\ngiven the complexity of rapidly\nageing water infrastructure,\npopulation growth, rapid eco-\nnomic growth, climate change,\nand increasing urbanisation.\nThus, an alternative approach\nis called for.\n\nIn the 19th century, the top-\ndown approach was successful\nas the available water resources\nwere adequateto meetthe needs\nof the po\n\n… [+4914 more chars]",
  "content_hash": "0f36e865a6465d5a19edc6329c2dfef94a0d4177f0c03be34331e3fc28bdc580",
  "token_count": 1242,
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
  "created_at": "2026-06-25T11:24:11.969859+00:00",
  "updated_at": "2026-06-25T11:24:11.969859+00:00"
}
```

## Child · `8063e1f4-c648-565a-b73f-e87fc5ca76a5`

- vector: dim=3072 · [-0.0450, 0.0079, -0.0089, -0.0210, -0.0078, -0.0159, -0.0012, 0.0050, …]

```json
{
  "chunk_id": "8063e1f4-c648-565a-b73f-e87fc5ca76a5",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "SK Sarkar — F",
  "chunk_text": "Integrated means of managing water\n\nNeed to promote\ndevelopment of\nwater, land, other\nresources in a\nsustainable manner\n\nfor many years, policymak-\ners have adopted a top-\ndown approach in water\nmanagement. But this tradition-\nal approach is not enough now,\ngiven the complexity of rapidly\nageing water infrastructure,\npopulation growth, rapid eco-\nnomic growth, climate change,\nand increasing urbanisation.\nThus, an alternative approach\nis called for.\n\nIn the 19th century, the top-\ndown approach was successful\nas the available water resources\nwere adequateto meetthe needs\nof the population. The c\n\n… [+774 more chars]",
  "content_hash": "5c9edd091a6be24d24a552a49ab185b00098a68f2aa596ba9f38090f39045826",
  "token_count": 312,
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
  "created_at": "2026-06-25T11:24:11.969859+00:00",
  "updated_at": "2026-06-25T11:24:11.969859+00:00"
}
```

## Child · `2d3d3b45-8c59-57a5-8582-1b3e67c1ceac`

- vector: dim=3072 · [-0.0364, -0.0062, -0.0027, -0.0090, 0.0010, -0.0068, 0.0035, -0.0151, …]

```json
{
  "chunk_id": "2d3d3b45-8c59-57a5-8582-1b3e67c1ceac",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "SK Sarkar — F",
  "chunk_text": "carce country, and its per\ncapita annual water availability\nwill be far less than the availa-\nble benchmark of scarce water\nsupply. There is also an ongoing\ndeterioration of the quality of\navailable water supply. To fulfill promises of the Sus-\ntainable Development Goals\n(SDG) in water and sanitation\nby 2030, the need of the hour is\nachieving universal and equita-\nble access to safe and affordable\ndrinking water for all, and also\nfor achieving access to adequate\nand equitable sanitation and hy-\ngiene for all. These goals also\nstipulate the implementation of\nintegrated water resource man-\nageme\n\n… [+1165 more chars]",
  "content_hash": "3ad20054c1235368f25557a96256d8caa1377b3293928082e22333a339f79ffd",
  "token_count": 397,
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
  "created_at": "2026-06-25T11:24:11.969859+00:00",
  "updated_at": "2026-06-25T11:24:11.969859+00:00"
}
```

## Child · `d346549e-8ec5-5a7f-a35e-eea0620498d9`

- vector: dim=3072 · [-0.0355, 0.0015, -0.0178, -0.0108, -0.0044, 0.0076, 0.0147, -0.0101, …]

```json
{
  "chunk_id": "d346549e-8ec5-5a7f-a35e-eea0620498d9",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "SK Sarkar — F",
  "chunk_text": "is holistic in\nnature as it recognises various\ndimensions of water, for exam-\nple, water economics, water\nquality and environment. This\nis also multidisciplinary involv-\ning fields such as engineering,\neconomic and social sciences. In effect, the Dublin princi-\nples emphasise the need for\nactions at grassroots level for\npolicy effectiveness, which\nresults in the participatory ap-\nproach to water management\nwidely known as the bottom-up\napproach. Under this, thelocals\nthemselves areconsidered as ex-\nperts of their environment and\ntheir knowledge should be in-\ncorporated in decision-making.\nIt p\n\n… [+1061 more chars]",
  "content_hash": "2140a9c80535ec1fbe9174e1ac37eb2f44c74c7d333fdf89849026cd57872ab9",
  "token_count": 367,
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
  "created_at": "2026-06-25T11:24:11.969859+00:00",
  "updated_at": "2026-06-25T11:24:11.969859+00:00"
}
```

## Child · `3cde37a3-a037-57fd-9ddd-71d2741fc84c`

- vector: dim=3072 · [-0.0470, -0.0104, -0.0145, -0.0052, -0.0090, 0.0073, 0.0123, 0.0095, …]

```json
{
  "chunk_id": "3cde37a3-a037-57fd-9ddd-71d2741fc84c",
  "document_id": "managing_water_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "managing-water.pdf",
  "section_heading": "SK Sarkar — F",
  "chunk_text": "management approach: col-\nlaboration is time-consuming\nandresourcesintensive, and the\nlevel of coordination required\nfor large projects may make\nthis framework too complex to\nundertake when there is lack of\ninstitutional capacities. In India, water schemes are\ngenerally supply-driven, not de-\nmand-driven. In this case, the\nmoneydevolves from the Centre\nto states and subsequently from\nstates to local bodies based on\ncertain criteria. For example,\n'Namame Gange' programme\nallocates money for undertak-\ning various activities, interalia,\nto states/local bodies based on\nsome criteria. It is a highl\n\n… [+771 more chars]",
  "content_hash": "1daeb9abf276d8558af407a4520a008fd44fe69ef76e893a7d60c36dfbb23e22",
  "token_count": 310,
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
  "chunk_index": 3,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-25T11:24:11.969859+00:00",
  "updated_at": "2026-06-25T11:24:11.969859+00:00"
}
```
