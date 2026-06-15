### Recommended metadata schema (canonical)

Every chunk — PDF or article — carries this payload. Fields that don’t apply to a source type are simply `null`.

| Field                                 | Type               | Applies to | Purpose                                    |
| ------------------------------------- | ------------------ | ---------- | ------------------------------------------ | --------------------------------- |
| `chunk_id`                            | string (UUID)      | all        | Qdrant point ID                            |
| `document_id`                         | string             | all        | Stable parent doc id (PDF file or article) |
| `parent_chunk_id`                     | string             | all        | Link child → parent chunk (parent-child)   |
| `article_id`                          | int / null         | article    | FK to MySQL `articles`                     |
| `pdf_id`                              | string / null      | pdf        | FK to MySQL `pdf_documents`                |
| `linked_pdf_id` / `linked_article_id` | string/int / null  | cross-ref  | The 70–80% overlap link                    |
| `source_type`                         | enum: `pdf`        | `article`  | all                                        | Primary filter + citation routing |
| `title`                               | string             | all        | Document/article title                     |
| `section_heading`                     | string / null      | all        | Nearest heading (citation + context)       |
| `page_number`                         | int / null         | pdf        | Citation page                              |
| `page_range`                          | [int,int] / null   | pdf        | For chunks spanning pages                  |
| `source_url`                          | string / null      | article    | Citation link                              |
| `pdf_path`                            | string / null      | pdf        | Object-storage key for the binary          |
| `chunk_text`                          | string             | all        | The retrievable text                       |
| `chunk_index`                         | int                | all        | Order within document                      |
| `tags`                                | string[]           | all        | Filtering                                  |
| `categories`                          | string[]           | all        | Filtering                                  |
| `authors`                             | string[]           | all        | Filtering / display                        |
| `language`                            | string (ISO 639-1) | all        | Multilingual filtering                     |
| `tenant_id`                           | string             | all        | Multi-tenant isolation                     |
| `acl`                                 | string[]           | all        | Access-control groups (RBAC)               |
| `content_hash`                        | string             | all        | Change detection                           |
| `doc_version`                         | int                | all        | Versioning                                 |
| `published_at`                        | datetime / null    | all        | Recency ranking / filter                   |
| `created_at` / `updated_at`           | datetime           | all        | Audit + freshness                          |

### 2.1 The canonical Document model

Normalize everything into this before chunking:

```python
@dataclass
class CanonicalSection:
    heading: str | None
    text: str
    page_start: int | None   # PDFs only
    page_end: int | None
    order: int

@dataclass
class CanonicalDocument:
    document_id: str
    source_type: str          # "pdf" | "article"
    title: str
    sections: list[CanonicalSection]
    # citation + filter metadata
    article_id: int | None = None
    pdf_id: str | None = None
    source_url: str | None = None
    pdf_path: str | None = None
    linked_pdf_id: str | None = None
    linked_article_id: int | None = None
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    language: str = "en"
    tenant_id: str = "default"
    acl: list[str] = field(default_factory=lambda: ["public"])
    published_at: datetime | None = None
    content_hash: str = ""
    doc_version: int = 1
```

### Ingesting large PDFs (100+ pages)

These are your hardest input — technical manuals, policy bundles, research compilations.

1. **Parse with a layout-aware parser.** Use **Docling** or **Unstructured** to recover reading order, headings, tables, and lists, and to keep **page numbers** on every element. PyMuPDF alone gives you text but loses structure and table fidelity. For 100+ page docs, structure is what makes good chunks possible.
2. **Tables:** extract them as Markdown or HTML and keep them as _atomic_ chunks (never split a table mid-row). Prepend the table’s caption/section heading to the chunk so it’s retrievable by topic.
3. **Build the section tree** (H1 > H2 > H3). This drives both chunking and the `section_heading` citation field.
4. **Stream, don’t load it all in RAM.** Process page-by-page / section-by-section so a 500-page PDF doesn’t blow memory. Embed in batches.
5. **OCR fallback:** if a page has no extractable text (scanned), route it through OCR (Tesseract, or a vision model for tricky layouts) before chunking. Flag `needs_ocr` so you can audit quality.

### Ingesting small PDFs (1–10 pages)

Simpler: a single parse pass, often a single parent with a handful of child chunks. Still preserve page numbers and headings. If a small PDF is essentially one continuous text, fall back to semantic/recursive chunking rather than forcing a heading tree that isn’t there.

### drupal data

1. Pull `articles` rows (id, title, body, url, author, dates, category/tag joins).
2. The article body becomes `sections`. If your CMS already stores HTML, strip to clean text but **keep heading tags** to reconstruct the section tree.
3. `source_url` = the canonical article URL (this _is_ the citation).
4. Capture category/tag relations from the join tables into `categories` / `tags`.

### Paragraph-level content from Puddle

If Puddle stores content at paragraph granularity (common in CMS schemas), you have two options:

- **Recommended:** treat each paragraph as the _atomic_ unit but **group consecutive paragraphs under the same heading into child chunks** of your target size. Pure per-paragraph chunks are usually too small (poor embeddings, fragmented context).
- Keep the `paragraph_id`(s) that compose each chunk in the payload so you can map a citation back to exact CMS paragraphs and even deep-link to them.
