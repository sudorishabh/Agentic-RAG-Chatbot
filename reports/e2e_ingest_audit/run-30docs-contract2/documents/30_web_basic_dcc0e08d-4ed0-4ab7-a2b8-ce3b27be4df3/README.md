# 30_web_basic_dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3

**website** · bundle `basic` · outcome **indexed**

- document_id: `dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3`
- title: New in Marine and Coastal
- source_key: basic/dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3
- handled in 0.546s (build 0.0s, extract Nones, chunk 0.001s, embed+upsert 0.484s, knowledge 0.007s)

## Files in this folder

- `00_source/record.json` — raw JSON:API resource (with included entities) and the parsed DrupalRecord
- `01_change_record.json` — the ChangeRecord as yielded by detect_drupal_changes, and the handler outcome
- `02_extraction.json` — HTML→text per rich-text field, discovered PDF links, entity refs, scalar metadata
- `03_canonical.json` — CanonicalDocument (all fields, all sections)
- `03_canonical_text.txt` — full_text(): the exact string content_hash covers
- `04_dates.json` — EffectiveDate evidence (page) / ResolvedDate (file), raw CMS values, what was applied
- `05_chunks.json` — every Chunk: text, embed_text, ids, parent link, pages, tokens, the payload it was indexed with
- `05_chunks.md` — the parent/child tree in readable form
- `06_qdrant.json` — every point read back from Qdrant: payload + vector summary
- `07_mysql.json` — every row in every catalog/knowledge table that refers to this document
- `08_knowledge.json` — knowledge StageReport + the mention/decision/claim/rejection/candidate rows
- `09_neo4j.json` — Document stub, chunk stubs, Claim nodes and current-state edges in the graph
- `10_checks.json` — every cross-stage check with expected/actual
- `log.txt` — the pipeline's own log lines while this document was handled

## Stage trace

### 1. Source (fresh fetch)
- JSON:API `block_content/basic` uuid `dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3` · nid None · created 2026-08-31T08:25:46+00:00 · changed 2026-08-31T08:30:14+00:00
- change detection: status **new** · fingerprint `2026-08-31T08:30:14+00:00` · changed_mark 1788165014 · prior: False

### 2. Extraction
- HTML→text: body 471 chars from 1 rich-text field(s); 0 PDF link(s) discovered ([])

### 3. Canonical document
- sections 1 · body chars 471 · content_hash `99b483369ff60687dd530f30f79740ba4bd68a15bc7505e293753643b9d3a745` · doc_version 1
- authors [] · tags [] · categories []
- entity_refs 0 · file_links []
- extra {'bundle': 'basic', 'nid': None, 'changed': '2026-08-31T08:30:14+00:00'}

### 4. Dates
- effective_start_date **2026-08-31T08:25:46+00:00** (precision day, source created) · effective_end_date None (precision None)
- rule `bundle_unmapped` · source `created` · fields [] · raw values [] · role created_stamp · range_issue None
- date_decision rows in MySQL: 0

### 5. Chunks
- 0 parent(s), 1 child(ren) · child tokens min/avg/max 120/120/120 · section types ['None']

### 6. Qdrant
- collection `e2e_audit_documents` · points for this document: 1 · indexer reported 1
- delete_document calls: [{'document_id': 'dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3', 'keep_ids': 1}]

### 7. MySQL
- `e2e_audit_documents`: 1 row(s)
- `e2e_audit_documents_author`: 0 row(s)
- `e2e_audit_documents_tag`: 0 row(s)
- `e2e_audit_documents_theme`: 0 row(s)
- `e2e_audit_documents_retry`: 0 row(s)
- `e2e_audit_documents_dead_link`: 0 row(s)
- `e2e_audit_documents_date_decision`: 0 row(s)
- `e2e_audit_documents_entity_mention`: 0 row(s)
- `e2e_audit_documents_assertion`: 0 row(s)
- `e2e_audit_documents_assertion_rejection`: 0 row(s)
- `e2e_audit_documents_predicate_candidate`: 0 row(s)
- `e2e_audit_documents_knowledge_run`: 1 row(s)
- `e2e_audit_documents_attachment`: 0 row(s)
- `e2e_audit_documents_attachment (as file)`: 0 row(s)
- `e2e_audit_documents_entity_resolution_decision`: 0 row(s)
- `e2e_audit_documents_entity_extraction`: 1 row(s)
- `e2e_audit_documents_assertion_link`: 0 row(s)
- `e2e_audit_ingest_log`: 1 row(s)
- `e2e_audit_documents_entity (referenced)`: 0 row(s)

### 8. Knowledge stage
- status **ok** in 0.0s · knowledge_version `kv1:57e6b192246add32`
- counts {'chunks_seen': 1, 'chunks_cached': 0, 'mentions': 0, 'entities_auto': 0, 'entities_provisional': 0, 'entities_ambiguous': 0, 'entities_unresolved': 0, 'claims_built': 0, 'claims_staged': 0, 'claims_rejected': 0, 'claims_retracted': 0, 'pending_predicates': 0, 'conflicts_disputed': 0, 'conflicts_superseded': 0}
- projection {'status': 'skipped', 'version': None, 'edges': 0}
  - stage `prelude`: ran · counts {'entities': 2451, 'chunks': 1} · notes [] · errors []
  - stage `supersede`: skipped · counts {} · notes [] · errors []
  - stage `mentions`: ran · counts {'cached': 0, 'mentions': 0} · notes [] · errors []
  - stage `resolution`: ran · counts {'auto': 0, 'provisional': 0, 'ambiguous': 0, 'unresolved': 0, 'cache_recorded': 1} · notes [] · errors []
  - stage `claims`: ran · counts {'llm_calls': 0, 'llm_failures': 0, 'llm': 0, 'unknown_predicates': 0, 'built': 0} · notes [] · errors []
  - stage `validate`: ran · counts {} · notes [] · errors []
  - stage `persist`: ran · counts {'accepted': 0, 'pending_predicates': 0} · notes [] · errors []
  - stage `conflicts`: skipped · counts {} · notes [] · errors []
  - stage `project`: skipped · counts {} · notes [] · errors []

### 9. Neo4j
- Document node: None · chunk stubs: 0 · Claim nodes: 0 · current-state edges from this document's claims: 0

## Checks

**79 pass · 0 fail · 0 n/a · 2 info**

| status | category | check | detail | expected | actual |
| --- | --- | --- | --- | --- | --- |
| PASS | outcome | handler_outcome_is_indexed | Every fresh document is expected to end 'indexed'. | indexed | indexed |
| PASS | outcome | no_exception | - | - | - |
| PASS | canonical | title_equals_node_title | - | New in Marine and Coastal | New in Marine and Coastal |
| PASS | canonical | body_is_single_section | Website body becomes one section. | 471 | 471 |
| PASS | canonical | raw_meta_equals_record_metadata | - | - | - |
| PASS | canonical | article_uuid_is_node_uuid | - | dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3 | dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3 |
| PASS | canonical | file_links_equal_record_files | - | - | - |
| PASS | canonical | extra_carries_bundle_nid_changed | - | - | {'bundle': 'basic', 'nid': None, 'changed': '2026-08-31T08:30:14+00:0… |
| PASS | canonical | facets_match_drupal_facets_rule | - | {'categories': [], 'tags': [], 'authors': []} | {'categories': [], 'tags': [], 'authors': []} |
| PASS | canonical | content_hash_is_sha256_of_body_text | - | - | 99b483369ff60687dd530f30f79740ba4bd68a15bc7505e293753643b9d3a745 |
| PASS | canonical | body_text_non_empty | - | >0 chars | 471 |
| PASS | dates | effective_start_date_present | Undated documents are excluded from date filters (pipeline warns). | a date | 2026-08-31T08:25:46+00:00 |
| PASS | dates | effective_date_evidence_present | - | - | - |
| INFO | dates | website_date_rule | rule=bundle_unmapped source=created fields=[] | - | {'rule': 'bundle_unmapped', 'source': 'created', 'fields': [], 'raw_v… |
| PASS | dates | canonical_date_equals_evidence_value | - | 2026-08-31T08:25:46+00:00 | 2026-08-31T08:25:46+00:00 |
| PASS | dates | canonical_end_equals_evidence_end | - | - | - |
| PASS | dates | date_source_equals_evidence_source | - | created | created |
| PASS | dates | date_decision_row_presence | Written only when the bundle maps to a real CMS date field. | False | 0 |
| PASS | chunks | chunks_produced | - | >0 children | {'parents': 0, 'children': 1} |
| PASS | chunks | chunk_ids_unique | - | 1 | 1 |
| PASS | chunks | every_parent_reference_resolves | - | - | - |
| PASS | chunks | parents_have_at_least_two_children | A parent is emitted only when it groups more than one child. | - | - |
| PASS | chunks | children_carry_document_id | - | - | - |
| PASS | chunks | children_carry_doc_version | - | 1 | [1] |
| PASS | chunks | children_within_token_limit | child_max_tokens=512 | 512 | {'max_child_tokens': 120, 'over': []} |
| PASS | chunks | parents_within_token_limit | parent_max_tokens=2400 | 2400 | {'max_parent_tokens': 0, 'over': []} |
| PASS | chunks | content_hash_is_sha256_of_text | - | - | - |
| PASS | chunks | child_index_is_contiguous | - | [0] | [0] |
| PASS | chunks | source_lines_covered_by_chunks | 100.000% of 12 source lines appear verbatim in some chunk | >=98% | {'coverage': 1.0, 'missing_sample': []} |
| PASS | chunks | children_have_embed_text_with_breadcrumb | embed_text = 'title › heading' + text | - | - |
| PASS | qdrant | point_count_equals_chunks | - | {'chunks': 1, 'indexer_reported': 1} | 1 |
| PASS | qdrant | every_chunk_id_is_a_point | - | 1 | {'missing': [], 'extra': []} |
| PASS | qdrant | payload_equals_chunk_payload_plus_stamps | Stored payload == Chunk.to_payload() plus created_at/updated_at/embed_model. | - | - |
| PASS | qdrant | children_have_real_vectors | - | - | - |
| PASS | qdrant | parents_have_zero_vectors | - | - | - |
| PASS | qdrant | vector_dimension_matches_setting | - | 3072 | [3072] |
| PASS | qdrant | children_stamped_with_embed_model | - | - | ['text-embedding-3-large:3072'] |
| PASS | qdrant | points_carry_document_id | - | - | - |
| PASS | qdrant | points_carry_effective_start_date | - | 2026-08-31T08:25:46+00:00 | ['2026-08-31T08:25:46+00:00'] |
| PASS | qdrant | points_carry_year_precision_only_when_year | - | day | ['None'] |
| PASS | qdrant | points_are_current_and_versioned | - | 1 | ['1'] |
| PASS | qdrant | points_stamped_with_pipeline_version | - | c1.i1.p2.e1 | ['c1.i1.p2.e1'] |
| PASS | qdrant | swap_deleted_with_keep_ids | delete_document(id, keep_ids=<new chunk ids>) ran after the upsert. | 1 | [{'document_id': 'dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3', 'keep_ids': … |
| PASS | mysql | state_row_exists | - | - | - |
| PASS | mysql | row_source_type | - | website | website |
| PASS | mysql | row_source_key | - | basic/dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3 | basic/dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3 |
| PASS | mysql | row_fingerprint | - | 2026-08-31T08:30:14+00:00 | 2026-08-31T08:30:14+00:00 |
| PASS | mysql | row_content_hash | - | 99b483369ff60687dd530f30f79740ba4bd68a15bc7505e293753643b9d3a745 | 99b483369ff60687dd530f30f79740ba4bd68a15bc7505e293753643b9d3a745 |
| PASS | mysql | row_doc_version | - | 1 | 1 |
| PASS | mysql | row_pipeline_version | - | c1.i1.p2.e1 | c1.i1.p2.e1 |
| PASS | mysql | row_bundle | - | basic | basic |
| PASS | mysql | row_entity_type | - | block_content | block_content |
| PASS | mysql | row_changed_mark | - | 1788165014 | 1788165014 |
| PASS | mysql | row_title | - | New in Marine and Coastal | New in Marine and Coastal |
| PASS | mysql | row_url | - | - | - |
| PASS | mysql | row_effective_start_date | - | 2026-08-31T08:25:46+00:00 | 2026-08-31 08:25:46 |
| PASS | mysql | row_date_source | - | created | created |
| PASS | mysql | row_start_precision | - | day | day |
| PASS | mysql | row_effective_end_date | - | - | - |
| PASS | mysql | row_end_precision | - | - | - |
| PASS | mysql | row_indexed_at_set | - | not null | 2026-09-09 05:15:11 |
| PASS | mysql | row_raw_meta_equals_canonical | - | - | - |
| PASS | mysql | author_facet_rows | - | - | - |
| PASS | mysql | tag_facet_rows | - | - | - |
| PASS | mysql | theme_rows_match_classification | documents_theme = theme_taxonomy.classify(categories) | - | - |
| PASS | mysql | attachment_link_rows | - | - | - |
| PASS | mysql | ingest_log_indexed_row | - | 1 | ['indexed'] |
| PASS | mysql | ingest_log_chunk_count | - | 1 | 1 |
| PASS | mysql | ingest_log_hash_and_version | - | - | - |
| PASS | mysql | no_retry_marker | - | - | - |
| INFO | knowledge | stage_report | status=ok {'chunks_seen': 1, 'chunks_cached': 0, 'mentions': 0, 'entities_auto': 0, 'enti… | - | {'document_id': 'dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3', 'doc_version'… |
| PASS | knowledge | run_row_written | - | 1 | [(1, 'ok')] |
| PASS | knowledge | run_row_matches_report | - | {'status': 'ok', 'mentions': 0, 'claims_staged': 0} | {'status': 'ok', 'mentions': 0, 'claims_staged': 0} |
| PASS | knowledge | mention_rows_equal_report | - | 0 | 0 |
| PASS | knowledge | decision_rows_equal_report | - | 0 | 0 |
| PASS | knowledge | mentions_point_at_own_chunks | - | - | - |
| PASS | knowledge | staged_claim_rows_equal_report | - | 0 | 0 |
| PASS | knowledge | claims_cite_own_chunks_or_document | - | - | - |
| PASS | knowledge | rejection_rows_equal_report | - | 0 | 0 |
| PASS | knowledge | extraction_cache_recorded | One cache row per child chunk content hash. | 1 | 1 |
| PASS | graph | nothing_projected_when_skipped | projection skipped: no touched claims | - | {'claims_in_graph': 0} |

