## 3. Chunking Strategy

Chunking is the single highest-leverage decision in a RAG system. Get it wrong and no reranker or LLM will save you.

### 3.1 Fixed-size vs semantic vs structure-aware

- **Fixed-size (token/char window + overlap):** simple, predictable, fast. Weakness: blindly cuts mid-sentence, mid-table, mid-idea. Fine as a _fallback_ for unstructured small docs.
- **Semantic chunking (split where embedding similarity drops):** keeps coherent ideas together. Weakness: slower (needs embeddings during ingest), variable sizes, can still ignore document structure.
- **Structure-aware chunking (split on the document’s own headings/sections, then size-bound within):** **the recommended default here.** Your PDFs and CMS articles _have_ structure (headings, sections, paragraphs) — use it. You get chunks that align with how a human would cite the document.

**The practical recipe used throughout this design:** structure-aware splitting on headings → if a section exceeds the target size, sub-split with a recursive/semantic splitter → enforce min/max bounds so you never emit a 30-token or 3000-token chunk.

### 3.2 Parent-child chunking (strongly recommended)

The core trick that gives you _both_ precise retrieval and rich context:

- **Child chunks (small, ~300–500 tokens):** what you embed and search over. Small = sharp semantic match, precise citations.
- **Parent chunks (large, the full section or ~1500–2000 tokens):** what you actually feed the LLM. Big = enough surrounding context to answer well.

Flow: search hits a child chunk → you look up its `parent_chunk_id` → you send the _parent_ to the LLM (deduplicated if multiple children share a parent). You search small and read big. This single technique typically gives the biggest quality jump over naive chunking.

Store parents either (a) as separate Qdrant points with `is_parent=true` (not embedded, retrieved by ID), or (b) in the app DB keyed by `parent_chunk_id`. Option (b) keeps the vector collection lean; option (a) keeps everything in one store. For this scale, **(a)** is simplest — one system to operate.

### 3.3 Hierarchical chunking

A generalization of parent-child for very large, deeply-nested docs (your 100+ page manuals): keep a 3-level tree — **document summary → section chunk → paragraph chunk** — and store the level in the payload. Retrieval can match at the paragraph level but escalate to the section or even a generated section-summary when a query is broad (“summarize chapter 4”). Add this only after the basic parent-child is working; it’s an optimization, not a starting point.

### 3.4 Per-document-type recommendations

| Doc type                           | Strategy                                           | Child size  | Overlap | Notes                                                                                                                  |
| ---------------------------------- | -------------------------------------------------- | ----------- | ------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Large technical PDFs / manuals** | Structure-aware + parent-child + hierarchical      | 350–500 tok | 10–15%  | Keep code blocks, command examples, and tables atomic. Parent = full section.                                          |
| **Policy documents**               | Structure-aware on clause/section numbers          | 300–450 tok | 15%     | Preserve clause numbering in `section_heading`; people cite “Section 4.2”. Don’t merge clauses.                        |
| **Research papers**                | Structure-aware on paper sections                  | 400–512 tok | 10%     | Treat Abstract / Methods / Results / References as boundaries. Tables & figure captions atomic. Keep citations intact. |
| **Small PDFs (1–10 pg)**           | Recursive/semantic; parent = whole doc             | 300–500 tok | 10–15%  | Often 1 parent, few children. Don’t over-engineer.                                                                     |
| **Website articles (Drupal)**      | Structure-aware on HTML headings; group paragraphs | 300–450 tok | 10%     | `source_url` is the citation. Strip boilerplate (nav/footer) before chunking.                                          |

**General defaults if unsure:** child ≈ 400 tokens, overlap ≈ 15% (~60 tokens), parent = section or ~1800 tokens. Measure tokens with the _embedding model’s_ tokenizer, not characters.

### 3.5 Overlap — why and how much

Overlap exists so an idea split across a chunk boundary still appears whole in at least one chunk. **10–15%** is the sweet spot. Too little → boundary ideas get orphaned; too much → near-duplicate chunks inflate your index, waste embedding cost, and pollute retrieval with redundant hits. For structure-aware chunks that already break on natural boundaries, lean toward the lower end (10%).

### 3.6 Metadata attached to each chunk

Every child chunk gets the full canonical payload from §1.5. The fields that matter _most_ for chunk quality and citation: `document_id`, `parent_chunk_id`, `source_type`, `section_heading`, `page_number`/`source_url`, `title`, `tags`, `categories`, `tenant_id`, `acl`, `content_hash`, `doc_version`.

### 3.7 Exactly how chunks look in Qdrant

A **child** chunk (PDF source):

```json
{
  "id": "a7f3c9e2-1b4d-4f8a-9c2e-3d5b6a7c8e90",
  "vector": {
    "dense": [0.0123, -0.0456, 0.0789, "... 1024 dims (BGE-M3) ..."],
    "sparse": {
      "indices": [1023, 5051, 88123, 120934],
      "values": [0.71, 0.55, 0.49, 0.33]
    }
  },
  "payload": {
    "chunk_id": "a7f3c9e2-1b4d-4f8a-9c2e-3d5b6a7c8e90",
    "document_id": "pdf_policy_guide_2024",
    "parent_chunk_id": "parent_pdf_policy_guide_2024_s12",
    "pdf_id": "pdf_policy_guide_2024",
    "linked_article_uuid": "6e9d2a3f-7c41-4b8e-9f0a-1d2c3b4a5e6f",
    "source_type": "pdf",
    "title": "Corporate Policy Guide 2024",
    "section_heading": "4.2 Data Retention Requirements",
    "page_number": 42,
    "page_range": [42, 42],
    "pdf_path": "s3://rag-pdfs/policy/policy_guide_2024.pdf",
    "source_url": null,
    "chunk_text": "All customer records must be retained for a minimum of seven years from the date of last activity. Records pertaining to active disputes...",
    "chunk_index": 87,
    "tags": ["data-retention", "compliance", "gdpr"],
    "categories": ["policy", "legal"],
    "authors": ["Legal Department"],
    "language": "en",
    "tenant_id": "acme-corp",
    "acl": ["employees", "legal-team"],
    "content_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "doc_version": 3,
    "is_current": true,
    "is_parent": false,
    "published_at": "2024-01-15T00:00:00Z",
    "created_at": "2024-02-01T10:30:00Z",
    "updated_at": "2024-06-20T14:12:00Z"
  }
}
```

The matching **parent** chunk (not embedded — note dummy/zero or omitted vector, `is_parent=true`, full section text):

```json
{
  "id": "parent_pdf_policy_guide_2024_s12",
  "vector": { "dense": [0.0, "... (zeros; never searched) ..."] },
  "payload": {
    "chunk_id": "parent_pdf_policy_guide_2024_s12",
    "document_id": "pdf_policy_guide_2024",
    "is_parent": true,
    "source_type": "pdf",
    "title": "Corporate Policy Guide 2024",
    "section_heading": "4.2 Data Retention Requirements",
    "page_range": [42, 44],
    "chunk_text": "4.2 Data Retention Requirements\n\nAll customer records must be retained ... (the full ~1800-token section) ...",
    "tenant_id": "acme-corp",
    "acl": ["employees", "legal-team"],
    "doc_version": 3,
    "is_current": true
  }
}
```

A child chunk from a **CMS article** differs only in source fields (`source_type: "article"`, `article_uuid`, `source_url` set, `page_number: null`, `pdf_path: null`).
