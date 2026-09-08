# 16_pdf_ongoing_projects_12268b81-5e1a-4359-9d83-3b9d927c12ba

**pdf_attachment** · bundle `ongoing_projects` · outcome **indexed**

- document_id: `12268b81-5e1a-4359-9d83-3b9d927c12ba`
- title: Kapsarc TERI Discussion Paper
- source_key: https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discussion%20Paper.pdf
- parent page: `189ccbeb-0e47-4ade-b901-771f751e61cc` — KAPSARC–TERI Research Collaboration: The Role of Clean Energy Policies as Part of India's Transportation Sector Decarbonization (https://teriin.org/project/kapsarc-teri-research-collaboration-role-clean-energy-policies-part-indias-transportation)
- file: Kapsarc TERI Discussion Paper.pdf · origin `attachment` · description Kapsarc TERI Discussion Paper
- handled in 17.114s (build 8.156s, extract 7.563s, chunk 0.219s, embed+upsert 5.858s, knowledge 2.859s)

## Files in this folder

- `00_source/parent_record.json` — raw JSON:API resource of the parent page (plus included entities)
- `00_source/file_link.json` — the file reference as discovered on the page, and the download result
- `00_source/Kapsarc_TERI_Discussion_Paper.pdf` — the freshly downloaded PDF bytes
- `01_change_record.json` — the ChangeRecord as yielded by detect_drupal_changes, and the handler outcome
- `02_extraction.json` — ExtractionResult: every page's text, route (text/ocr/empty), tables, PDF metadata
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
- downloaded 3146297 bytes from `https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discussion%20Paper.pdf` (requested `https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discussion%20Paper.pdf`, https upgrade: False) · sha256 `b1ace39dc2bd312c9cf91fc4f3e4962f40e7762d9302ece973035e4a4129b474`
- change detection: status **new** · fingerprint `2026-09-08T03:38:59+00:00` · changed_mark 1788838739 · prior: False

### 2. Extraction
- 37 page(s) · routes {'text': 36, 'ocr': 1} · tables 18 · PDF metadata keys ['extraction_mode', 'page_signals', 'route']
- characters: 95123 · empty pages: 0

### 3. Canonical document
- sections 37 · body chars 95195 · content_hash `8a42b995941f597eca9d02fd113c3559d11d4d8e5e73e61fbcb32532596ee6e6` · doc_version 1
- authors [] · tags ['Clean Energy Technologies', 'Energy transitions', 'Road transport'] · categories ['Transport', 'True']
- entity_refs 8 · file_links []
- extra {'bundle': 'ongoing_projects'}

### 4. Dates
- effective_start_date **2024-11-01T00:00:00+00:00** (precision day, source parent_page) · effective_end_date None (precision None)
- parent page resolution: rule `bundle_date_field` source `cms_field` fields ['field_ongoing_start_date'] raw ['2024-11-01T04:30:00+00:00']
- file resolver: overridden=False · decision action `keep_page_date` rule `parent_bundle_date_field` · edition_label None · evidence used ['drupal']
- decision evidence: The parent ongoing_projects page states its date in field_ongoing_start_date ('2024-11-01T04:30:00+00:00'); an attached file carries its page's date.
- date_decision rows in MySQL: 1 — action `keep_page_date` rule `parent_bundle_date_field` candidate 2024-11-01 00:00:00

### 5. Chunks
- 16 parent(s), 66 child(ren) · child tokens min/avg/max 125/381/560 · section types ['None', 'references']

### 6. Qdrant
- collection `e2e_audit_documents` · points for this document: 82 · indexer reported 82
- delete_document calls: [{'document_id': '12268b81-5e1a-4359-9d83-3b9d927c12ba', 'keep_ids': 82}]

### 7. MySQL
- `e2e_audit_documents`: 1 row(s)
- `e2e_audit_documents_author`: 0 row(s)
- `e2e_audit_documents_tag`: 3 row(s)
- `e2e_audit_documents_theme`: 1 row(s)
- `e2e_audit_documents_retry`: 0 row(s)
- `e2e_audit_documents_dead_link`: 0 row(s)
- `e2e_audit_documents_date_decision`: 1 row(s)
- `e2e_audit_documents_entity_mention`: 52 row(s)
- `e2e_audit_documents_assertion`: 0 row(s)
- `e2e_audit_documents_assertion_rejection`: 0 row(s)
- `e2e_audit_documents_predicate_candidate`: 0 row(s)
- `e2e_audit_documents_knowledge_run`: 1 row(s)
- `e2e_audit_documents_attachment`: 0 row(s)
- `e2e_audit_documents_attachment (as file)`: 1 row(s)
- `e2e_audit_documents_entity_resolution_decision`: 52 row(s)
- `e2e_audit_documents_entity_extraction`: 66 row(s)
- `e2e_audit_documents_assertion_link`: 0 row(s)
- `e2e_audit_ingest_log`: 1 row(s)
- `e2e_audit_documents_entity (referenced)`: 2 row(s)

### 8. Knowledge stage
- status **ok** in 2.85s · knowledge_version `kv1:57e6b192246add32`
- counts {'chunks_seen': 66, 'chunks_cached': 0, 'mentions': 52, 'entities_auto': 17, 'entities_provisional': 0, 'entities_ambiguous': 0, 'entities_unresolved': 35, 'claims_built': 0, 'claims_staged': 0, 'claims_rejected': 0, 'claims_retracted': 0, 'pending_predicates': 0, 'conflicts_disputed': 0, 'conflicts_superseded': 0}
- projection {'status': 'skipped', 'version': None, 'edges': 0}
  - stage `prelude`: ran · counts {'entities': 2451, 'chunks': 66} · notes [] · errors []
  - stage `supersede`: skipped · counts {} · notes [] · errors []
  - stage `mentions`: ran · counts {'cached': 0, 'mentions': 52} · notes [] · errors []
  - stage `resolution`: ran · counts {'auto': 17, 'provisional': 0, 'ambiguous': 0, 'unresolved': 35, 'cache_recorded': 66} · notes [] · errors []
  - stage `claims`: ran · counts {'llm_calls': 7, 'llm': 0, 'unknown_predicates': 0, 'built': 0} · notes ['this document has no canonical PROJECT entity yet; seeding is a global pass (scripts.build_knowledge), and its claims will be staged once it runs'] · errors []
  - stage `validate`: ran · counts {} · notes [] · errors []
  - stage `persist`: ran · counts {'accepted': 0, 'pending_predicates': 0} · notes [] · errors []
  - stage `conflicts`: skipped · counts {} · notes [] · errors []
  - stage `project`: skipped · counts {} · notes [] · errors []

### 9. Neo4j
- Document node: None · chunk stubs: 0 · Claim nodes: 0 · current-state edges from this document's claims: 0

## Checks

**89 pass · 0 fail · 0 n/a · 5 info**

| status | category | check | detail | expected | actual |
| --- | --- | --- | --- | --- | --- |
| PASS | outcome | handler_outcome_is_indexed | Every fresh document is expected to end 'indexed'. | indexed | indexed |
| PASS | outcome | no_exception | - | - | - |
| PASS | source | pdf_downloaded_non_empty | - | >0 bytes | 3146297 |
| INFO | source | pdf_pages | 37 pages extracted, 37 with text | - | {'pages': 37, 'with_text': 37, 'routes': {'text': 36, 'ocr': 1}, 'tab… |
| PASS | canonical | sections_equal_non_empty_pages | from_pdf makes one section per page with text. | 37 | 37 |
| PASS | canonical | section_text_equals_page_text | Section text is the page text verbatim. | - | - |
| PASS | canonical | title_precedence_description_node_filename | title = file.description or node.title or filename | Kapsarc TERI Discussion Paper | Kapsarc TERI Discussion Paper |
| PASS | canonical | linked_article_uuid_is_parent_node | - | 189ccbeb-0e47-4ade-b901-771f751e61cc | 189ccbeb-0e47-4ade-b901-771f751e61cc |
| PASS | canonical | source_url_is_parent_page | - | https://teriin.org/project/kapsarc-teri-research-collaboration-role-c… | https://teriin.org/project/kapsarc-teri-research-collaboration-role-c… |
| PASS | canonical | file_url_is_fetched_url | - | https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discu… | https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discu… |
| PASS | canonical | bundle_inherited_from_parent | - | ongoing_projects | ongoing_projects |
| PASS | parent_child | facets_inherited_from_parent | categories/tags/authors equal the parent page's | {'categories': ['Transport', 'True'], 'tags': ['Clean Energy Technolo… | {'categories': ['Transport', 'True'], 'tags': ['Clean Energy Technolo… |
| PASS | parent_child | entity_refs_inherited_from_parent | - | - | - |
| PASS | parent_child | parent_lists_this_file | - | 12268b81-5e1a-4359-9d83-3b9d927c12ba | ['12268b81-5e1a-4359-9d83-3b9d927c12ba'] |
| PASS | canonical | content_hash_is_sha256_of_body_text | - | - | 8a42b995941f597eca9d02fd113c3559d11d4d8e5e73e61fbcb32532596ee6e6 |
| PASS | canonical | body_text_non_empty | - | >0 chars | 95195 |
| PASS | dates | effective_start_date_present | Undated documents are excluded from date filters (pipeline warns). | a date | 2024-11-01T00:00:00+00:00 |
| PASS | dates | resolver_ran | - | - | - |
| INFO | dates | pdf_date_path | inherited from parent page | - | {'parent_rule': 'bundle_date_field', 'parent_source': 'cms_field', 'd… |
| PASS | dates | pdf_start_date_equals_parent_resolved | - | 2024-11-01T00:00:00+00:00 | 2024-11-01T00:00:00+00:00 |
| PASS | dates | pdf_precision_equals_parent | - | day | day |
| PASS | dates | pdf_end_date_equals_parent | - | - | - |
| PASS | dates | date_source_is_parent_page | - | parent_page | parent_page |
| PASS | dates | parent_page_canonical_date_matches_parent_resolution | The page's own document and the value handed to its files agree. | 2024-11-01T00:00:00+00:00 | 2024-11-01T00:00:00+00:00 |
| PASS | dates | date_decision_row_presence | A row is written when the resolver produced a decision. | True | 1 |
| PASS | dates | date_decision_row_names_parent_node | - | 189ccbeb-0e47-4ade-b901-771f751e61cc | 189ccbeb-0e47-4ade-b901-771f751e61cc |
| PASS | dates | date_decision_current_date_is_parent_resolved | - | 2024-11-01T00:00:00+00:00 | 2024-11-01 00:00:00 |
| PASS | chunks | chunks_produced | - | >0 children | {'parents': 16, 'children': 66} |
| PASS | chunks | chunk_ids_unique | - | 82 | 82 |
| PASS | chunks | every_parent_reference_resolves | - | - | - |
| PASS | chunks | parents_have_at_least_two_children | A parent is emitted only when it groups more than one child. | ['030b2103-23f1-5437-9350-63e27b81f5fb', '0f79adcd-aba9-5e3e-9e4f-cda… | {'557ec8a9-9c70-5df1-969c-1d28346e2c3f': 2, '67280c5a-b03a-5f1f-9471-… |
| PASS | chunks | children_carry_document_id | - | - | - |
| PASS | chunks | children_carry_doc_version | - | 1 | [1] |
| PASS | chunks | children_within_token_limit | child_max_tokens=560 | 560 | {'max_child_tokens': 560, 'over': []} |
| PASS | chunks | parents_within_token_limit | parent_max_tokens=2600 | 2600 | {'max_parent_tokens': 1993, 'over': []} |
| PASS | chunks | content_hash_is_sha256_of_text | - | - | - |
| PASS | chunks | child_index_is_contiguous | - | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19… | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19… |
| PASS | chunks | children_carry_page_numbers | - | - | - |
| PASS | chunks | source_lines_covered_by_chunks | 100.000% of 1605 source lines appear verbatim in some chunk | >=98% | {'coverage': 1.0, 'missing_sample': []} |
| PASS | chunks | children_have_embed_text_with_breadcrumb | embed_text = 'title › heading' + text | - | - |
| PASS | qdrant | point_count_equals_chunks | - | {'chunks': 82, 'indexer_reported': 82} | 82 |
| PASS | qdrant | every_chunk_id_is_a_point | - | 82 | {'missing': [], 'extra': []} |
| PASS | qdrant | payload_equals_chunk_payload_plus_stamps | Stored payload == Chunk.to_payload() plus created_at/updated_at/embed_model. | - | - |
| PASS | qdrant | children_have_real_vectors | - | - | - |
| PASS | qdrant | parents_have_zero_vectors | - | - | - |
| PASS | qdrant | vector_dimension_matches_setting | - | 3072 | [3072] |
| PASS | qdrant | children_stamped_with_embed_model | - | - | ['text-embedding-3-large:3072'] |
| PASS | qdrant | points_carry_document_id | - | - | - |
| PASS | qdrant | points_carry_effective_start_date | - | 2024-11-01T00:00:00+00:00 | ['2024-11-01T00:00:00+00:00'] |
| PASS | qdrant | points_carry_year_precision_only_when_year | - | day | ['None'] |
| PASS | qdrant | points_are_current_and_versioned | - | 1 | ['1'] |
| PASS | qdrant | points_stamped_with_pipeline_version | - | c1.i1.p2.e1 | ['c1.i1.p2.e1'] |
| PASS | qdrant | swap_deleted_with_keep_ids | delete_document(id, keep_ids=<new chunk ids>) ran after the upsert. | 82 | [{'document_id': '12268b81-5e1a-4359-9d83-3b9d927c12ba', 'keep_ids': … |
| PASS | mysql | state_row_exists | - | - | - |
| PASS | mysql | row_source_type | - | pdf_attachment | pdf_attachment |
| PASS | mysql | row_source_key | - | https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discu… | https://teriin.org/sites/default/files/2026-09/Kapsarc%20TERI%20Discu… |
| PASS | mysql | row_fingerprint | - | 2026-09-08T03:38:59+00:00 | 2026-09-08T03:38:59+00:00 |
| PASS | mysql | row_content_hash | - | 8a42b995941f597eca9d02fd113c3559d11d4d8e5e73e61fbcb32532596ee6e6 | 8a42b995941f597eca9d02fd113c3559d11d4d8e5e73e61fbcb32532596ee6e6 |
| PASS | mysql | row_doc_version | - | 1 | 1 |
| PASS | mysql | row_pipeline_version | - | c1.i1.p2.e1 | c1.i1.p2.e1 |
| PASS | mysql | row_bundle | - | ongoing_projects | ongoing_projects |
| PASS | mysql | row_entity_type | - | - | - |
| PASS | mysql | row_changed_mark | - | 1788838739 | 1788838739 |
| PASS | mysql | row_title | - | Kapsarc TERI Discussion Paper | Kapsarc TERI Discussion Paper |
| PASS | mysql | row_url | - | https://teriin.org/project/kapsarc-teri-research-collaboration-role-c… | https://teriin.org/project/kapsarc-teri-research-collaboration-role-c… |
| PASS | mysql | row_effective_start_date | - | 2024-11-01T00:00:00+00:00 | 2024-11-01 00:00:00 |
| PASS | mysql | row_date_source | - | parent_page | parent_page |
| PASS | mysql | row_start_precision | - | day | day |
| PASS | mysql | row_effective_end_date | - | - | - |
| PASS | mysql | row_end_precision | - | - | - |
| PASS | mysql | row_indexed_at_set | - | not null | 2026-09-08 09:50:00 |
| PASS | mysql | row_raw_meta_equals_canonical | - | - | - |
| PASS | mysql | author_facet_rows | - | - | - |
| PASS | mysql | tag_facet_rows | - | ['Clean Energy Technologies', 'Energy transitions', 'Road transport'] | ['Clean Energy Technologies', 'Energy transitions', 'Road transport'] |
| PASS | mysql | theme_rows_match_classification | documents_theme = theme_taxonomy.classify(categories) | [('Transport', 'sub', 'Sustainable Habitat', 'main')] | [('Transport', 'sub', 'Sustainable Habitat', 'main')] |
| INFO | mysql | categories_dropped_by_theme_classifier | Categories with no theme row (grouping buckets or unknown names). | - | ['True'] |
| PASS | mysql | attachment_link_rows | - | - | - |
| PASS | mysql | ingest_log_indexed_row | - | 1 | ['indexed'] |
| PASS | mysql | ingest_log_chunk_count | - | 82 | 82 |
| PASS | mysql | ingest_log_hash_and_version | - | - | - |
| PASS | mysql | no_retry_marker | - | - | - |
| PASS | parent_child | linked_from_parent_in_attachment_table | - | 189ccbeb-0e47-4ade-b901-771f751e61cc | ['189ccbeb-0e47-4ade-b901-771f751e61cc'] |
| INFO | parent_child | parents_claiming_this_file | 1 page(s) link this file | - | ['189ccbeb-0e47-4ade-b901-771f751e61cc'] |
| INFO | knowledge | stage_report | status=ok {'chunks_seen': 66, 'chunks_cached': 0, 'mentions': 52, 'entities_auto': 17, 'e… | - | {'document_id': '12268b81-5e1a-4359-9d83-3b9d927c12ba', 'doc_version'… |
| PASS | knowledge | run_row_written | - | 1 | [(1, 'ok')] |
| PASS | knowledge | run_row_matches_report | - | {'status': 'ok', 'mentions': 52, 'claims_staged': 0} | {'status': 'ok', 'mentions': 52, 'claims_staged': 0} |
| PASS | knowledge | mention_rows_equal_report | - | 52 | 52 |
| PASS | knowledge | decision_rows_equal_report | - | 52 | 52 |
| PASS | knowledge | mentions_point_at_own_chunks | - | - | - |
| PASS | knowledge | staged_claim_rows_equal_report | - | 0 | 0 |
| PASS | knowledge | claims_cite_own_chunks_or_document | - | - | - |
| PASS | knowledge | rejection_rows_equal_report | - | 0 | 0 |
| PASS | knowledge | extraction_cache_recorded | One cache row per child chunk content hash. | 66 | 66 |
| PASS | graph | nothing_projected_when_skipped | projection skipped: no touched claims | - | {'claims_in_graph': 0} |

