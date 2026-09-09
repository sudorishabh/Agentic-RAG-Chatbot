# End-to-end ingestion audit — 30 freshly fetched documents

Run `20260909-050123` started 2026-09-09T05:01:23+00:00 finished 2026-09-09T05:08:17+00:00 · pipeline version `c1.i1.p2.e1` · results in `D:\OneDrive - The Energy and Resources Institute\Desktop\My_Files\Projects\Agentic-RAG-Chatbot\reports\e2e_ingest_audit\run-30docs-contract`

## How to read this

Part 1 is generated from the run: one row per document, then a per-document trace with links to the evidence folder (`documents/NN_.../`). Every folder holds the raw source, the extraction, the canonical document, the date evidence, every chunk, every Qdrant point, every MySQL row, the knowledge report and the Neo4j subgraph for that document, plus `10_checks.json`. Part 2 is the assessment written from that evidence.

## Isolation and assumptions

- MySQL tables: `e2e_audit_documents*` and `e2e_audit_ingest_log` (created fresh; 20 stale tables dropped first). Production `documents*` untouched.
- Qdrant collection: `e2e_audit_documents` (recreated). Production `documents` collection untouched.
- Neo4j: throwaway container `e2e-audit-neo4j` (neo4j:2026.07.1-community) at `bolt://localhost:7688`, empty at start.
- Entity store snapshot: production `documents_entity/_alias/_identifier` copied into the isolated prefix ({'e2e_audit_documents_entity': 2451, 'e2e_audit_documents_entity_alias': 3518, 'e2e_audit_documents_entity_identifier': 972}) so mention resolution runs against the index a deployment has. No check reads production data.
- Gazetteer, author facet and CMS-claim context are built from the isolated catalog, i.e. only from these 30 documents' metadata, so mention recognition is narrower than in production (see the assessment).
- Workers forced to 1 (production .env has INGEST_WORKERS=2); the per-document logic is identical, only concurrency differs.
- Feature flags as in .env: knowledge_enabled=True, knowledge_process_after_index=True, knowledge_extract_mentions=True, claim_extraction_enabled=True, knowledge_project_per_document=True, enrichment_enabled=False, date_resolution_enabled=True, extraction_mode=hybrid, verify_corpus_after_sweep=True.
- Selection: newest-first sample of every configured source; the real detect_drupal_changes ran with only its bundle enumeration substituted.

## Part 1 — Run summary

### Selection

- candidates sampled from the live JSON:API (newest first): 184 across 16 sources
- nodes chosen: 25 · attachments they carry: 5 · documents expected: 30
- documents actually yielded by change detection and handled: **30**
- bundles: ['article', 'page', 'completed_projects', 'feature_articles', 'ongoing_projects', 'news', 'events', 'press_release', 'block_content:basic']

### Outcomes

- pipeline tally: `{'indexed': 30}`
- wall clock for `ingest_drupal`: 261.6s
- stage timings (app.observability.metrics): see `timings.json`

### Post-sweep stages (the same order `workers.tasks.sweep` uses)

- knowledge catch-up: `{'examined': 0, 'ok': 0, 'failed': 0}`
- graph projection: version `graph-project-v1:20260909T050749:ed169a52` nodes `{'Alias': 2793, 'Entity': 1726, 'Organization': 524, 'Person': 131, 'Predicate': 7, 'Project': 1071}` relationships `{'HAS_ALIAS': 2793}` skipped `{}`
- reconciliation: ok=True documents=30 points=1053

| check | count | ok | skipped | samples | detail |
| --- | --- | --- | --- | --- | --- |
| indexed_without_points | 0 | True | False | - | Documents the catalog reports as indexed that have no points at all. Clear their content … |
| points_without_catalog_row | 0 | True | False | - | Documents with points but no catalog row. They are retrievable and uncatalogued; delete_d… |
| duplicate_live_versions | 0 | True | False | - | Documents whose points carry more than one doc_version — an interrupted swap. Re-index th… |
| version_mismatch | 0 | True | False | - | Documents whose points disagree with the catalog's doc_version. Re-index them; the catalo… |
| chunk_id_mismatch | 0 | True | False | - | Points whose payload chunk_id is not their own id. Citations resolve by payload, so these… |
| children_without_parent | 0 | True | False | - | Child points naming a parent that does not exist. Context expansion falls back to the chi… |
| catalog_pipeline_drift | 0 | True | False | - | Documents not built by pipeline c1.i1.p2.e1. Run scripts.reprocess_corpus to rebuild them. |
| point_pipeline_drift | 0 | True | False | - | Documents with points written by a pipeline other than c1.i1.p2.e1. Re-indexing replaces … |
| documents_without_date | 0 | True | False | - | Documents with no effective date. They are invisible to date filters and to recency ranki… |
| date_provenance_unrecorded | 0 | True | False | - | Documents whose effective_start_date has no recorded origin. Every write path sets it, so… |
| stated_date_not_applied | 0 | True | False | - | The bundle's configured date field states a date that effective_start_date does not match… |
| attachment_date_adrift | 0 | True | False | - | An attached file whose date or period differs from the page it hangs on. A file inherits … |
| inverted_date_range | 0 | True | False | - | A stored date range whose end falls before its start. `bundle_dates` drops an inverted en… |
| unmapped_bundle_dates | 0 | True | False | - | A catalogued node bundle with no entry in app.ingestion.bundle_dates.BUNDLE_DATE_FIELDS. … |
| undeclared_source_date_field | 0 | True | False | - | A source field that looks like a date and holds a parseable one, which nothing has classi… |
| year_precision_not_january | 0 | True | False | - | A year-precision date whose value is not 1 January. The day is a marker for the year, so … |
| month_precision_not_first_of_month | 0 | True | False | - | A month-precision date whose value is not the 1st. The day is a marker for the month, so … |
| graph_projection | 0 | True | False | - | projection matches MySQL and is current |


### Stores after the run

- Qdrant: `{'collection': 'e2e_audit_documents', 'exists': True, 'points_count': 1053, 'vector_size': 3072, 'distance': 'Cosine', 'payload_indexes': ['authors', 'bundle', 'categories', 'chunk_index', 'chunk_text', 'document_id', 'effective_end_date', 'effective_start_date', 'end_precision', 'is_current', 'is_parent', 'language', 'parent_chunk_id', 'section_type', 'source_type', 'start_precision', 'tags']}`
- Neo4j: `{'reachable': True, 'node_labels': {'Alias': 2793, 'Entity': 1726, 'Organization': 524, 'Person': 131, 'Predicate': 7, 'Project': 1071}, 'relationship_types': {'HAS_ALIAS': 2793}, 'current_state_edges': 0, 'projection_versions': {'graph-project-v1:20260909T050749:ed169a52': 4519}}`
- MySQL row counts:

| table | rows |
| --- | --- |
| e2e_audit_documents | 30 |
| e2e_audit_documents_assertion | 0 |
| e2e_audit_documents_assertion_link | 0 |
| e2e_audit_documents_assertion_rejection | 14 |
| e2e_audit_documents_attachment | 5 |
| e2e_audit_documents_author | 4 |
| e2e_audit_documents_date_decision | 20 |
| e2e_audit_documents_dead_link | 0 |
| e2e_audit_documents_entity | 2451 |
| e2e_audit_documents_entity_alias | 3518 |
| e2e_audit_documents_entity_extraction | 857 |
| e2e_audit_documents_entity_identifier | 972 |
| e2e_audit_documents_entity_mention | 2842 |
| e2e_audit_documents_entity_resolution_decision | 2842 |
| e2e_audit_documents_knowledge_run | 30 |
| e2e_audit_documents_predicate_candidate | 0 |
| e2e_audit_documents_retry | 0 |
| e2e_audit_documents_tag | 67 |
| e2e_audit_documents_theme | 23 |
| e2e_audit_ingest_log | 30 |


### Documents

| # | type | bundle | outcome | title | date | date_source | parents | children | points | claims | proj | fail | folder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | web | article | indexed | Carbon Sequestration by Seaweed is Not a Straightforward Pathway | 2026-08-25 | created | 1 | 5 | 6 | 0 | skipped | 0 | 01_web_article_491ae95c-a14d-4810-bb16-8df4ab16ad8e |
| 2 | web | article | indexed | When Risk Stops Looking Normal: Lessons from the Nepal Floods | 2026-08-31 | created | 0 | 4 | 4 | 0 | skipped | 0 | 02_web_article_0a5e1528-9f38-4f24-a0f4-3cf9a2930cb8 |
| 3 | web | article | indexed | Forest Pathshaala: Adivasi Children and the Ecologies of Knowledge | 2025-11-12 | created | 4 | 12 | 16 | 0 | skipped | 0 | 03_web_article_816867bf-eac7-4833-bfe1-7e202ff61c51 |
| 4 | web | page | indexed | TERI Alumni Association | 2025-09-30 | created | 6 | 23 | 29 | 0 | skipped | 0 | 04_web_page_04107bb4-fefe-4ffa-be5d-f88ac9310dd6 |
| 5 | pdf | page | indexed | TERI Alumni Association | 2025-09-30 | parent_page | 5 | 23 | 28 | 0 | skipped | 0 | 05_pdf_page_inbody_8a64f693f3de31c6620aa873d1d4c7425 |
| 6 | pdf | page | indexed | TERI Alumni Association | 2020-01-01 | document_copyright | 98 | 431 | 529 | 0 | skipped | 1 | 06_pdf_page_inbody_019c7e59163edfbb3535b05744ff6949b |
| 7 | pdf | page | indexed | TERI Alumni Association | 2022-01-01 | document_copyright | 69 | 294 | 363 | 0 | skipped | 1 | 07_pdf_page_inbody_0a7c343146247d17ae9ebdffa512fb4a3 |
| 8 | web | page | indexed | Newsletters | 2020-10-22 | created | 4 | 17 | 21 | 0 | skipped | 0 | 08_web_page_80d9bdc9-c159-493a-80e1-ca53cece85e3 |
| 9 | web | page | indexed | Contact Us | 2018-04-10 | created | 1 | 4 | 5 | 0 | skipped | 0 | 09_web_page_2a2e9a77-da56-43a7-8138-3ebf16010d1b |
| 10 | web | completed_projects | indexed | Science Technology and Innovation Hub in Gaondongrem, Goa | 2023-01-23 | cms_field | 0 | 3 | 3 | 0 | skipped | 0 | 10_web_completed_projects_36a999eb-b7c7-47fd-ac69-55f97841a9d3 |
| 11 | web | completed_projects | indexed | Delivering India’s NDC Targets: Role of Transport | 2024-09-01 | cms_field | 0 | 3 | 3 | 0 | skipped | 0 | 11_web_completed_projects_f4b58789-88af-4525-8c1e-93fe860663e1 |
| 12 | web | completed_projects | indexed | Establishing Resource and Knowledge Centre (RKC) for the Distribution Sector under the Al… | 2025-10-14 | cms_field | 0 | 1 | 1 | 0 | skipped | 0 | 12_web_completed_projects_74d106c0-968e-43dc-b873-83d2e7460af8 |
| 13 | web | feature_articles | indexed | Peace in Ukraine is nowhere in sight | 2026-09-01 | created | 0 | 1 | 1 | 0 | skipped | 0 | 13_web_feature_articles_6c62c011-9677-4f6a-9fb1-c01558c5f814 |
| 14 | web | feature_articles | indexed | Nuclear power expansion: India needs a clear financing strategy | 2026-09-06 | created | 0 | 1 | 1 | 0 | skipped | 0 | 14_web_feature_articles_d0bf1f2c-7e3e-4a65-b253-42cc49e8491f |
| 15 | web | feature_articles | indexed | Nepal: A wake-up call | 2026-09-07 | created | 0 | 1 | 1 | 0 | skipped | 0 | 15_web_feature_articles_2a1ca7a4-e2f8-4bb1-ad8c-b7a915986e69 |
| 16 | web | ongoing_projects | indexed | Adoption of green fuels in Indian Maritime sector. | 2026-01-14 | cms_field | 1 | 5 | 6 | 0 | skipped | 0 | 16_web_ongoing_projects_a240619a-8365-429e-adde-9bf707c46882 |
| 17 | web | ongoing_projects | indexed | National Roadmap: Solarisation of Closed & Reclaimed Coal Mines in India | 2026-04-10 | cms_field | 1 | 2 | 3 | 0 | skipped | 0 | 17_web_ongoing_projects_2f5ede1c-8091-4ec8-9dd8-866797f0af41 |
| 18 | web | ongoing_projects | indexed | Peer Review of Carbon Credit Methodology for Jute-Based Net CO2 Emission Reduction | 2026-05-22 | cms_field | 0 | 1 | 1 | 0 | skipped | 0 | 18_web_ongoing_projects_3807402a-fb95-4900-85ae-697403882e33 |
| 19 | web | news | indexed | TERI and ADB Convene Regional Knowledge-Sharing Session on Strengthening Transport-relate… | 2026-09-03 | cms_field | 0 | 1 | 1 | 0 | skipped | 0 | 19_web_news_b9d714ff-34cd-4d73-b67e-083c80936ebd |
| 20 | web | news | indexed | ISA SIDS and GRIHA Launch ISA-iSUN Design Challenge to Promote Solar and Climate-Resilien… | 2026-09-04 | cms_field | 0 | 1 | 1 | 0 | skipped | 0 | 20_web_news_74aba0c4-1457-4495-9263-a0b95aa97875 |
| 21 | web | news | indexed | Sarbananda Sonowal Charts Course for Zero-Emission Shipping Corridors, Pushes Ports to Fa… | 2026-09-03 | cms_field | 0 | 1 | 1 | 0 | skipped | 0 | 21_web_news_c00a39be-c021-4e95-9ce0-1c4a1912bc5e |
| 22 | web | events | indexed | Darbari Seth Memorial Lecture 2026 | 2026-08-21 | cms_field | 1 | 3 | 4 | 0 | skipped | 0 | 22_web_events_3c24d94b-f8bb-4475-b147-56dd0c35318f |
| 23 | pdf | events | indexed | Darbari Seth Memorial Lecture 2026 | 2026-08-21 | parent_page | 1 | 2 | 3 | 0 | skipped | 0 | 23_pdf_events_33c32e72-2a50-4547-86a1-269699dade92 |
| 24 | web | events | indexed | World Sustainable Development Summit 2027: Curtain Raiser | 2026-09-09 | cms_field | 1 | 2 | 3 | 0 | skipped | 0 | 24_web_events_ce219043-a7a7-41ed-9812-2ecfe3842fe1 |
| 25 | web | events | indexed | WCEF2026 Accelerator Session: Circular Public Procurement for Sustainable Consumption and… | 2026-09-18 | cms_field | 0 | 2 | 2 | 0 | skipped | 0 | 25_web_events_c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1 |
| 26 | pdf | events | indexed | Concept Note WCEF | 2026-09-18 | parent_page | 0 | 3 | 3 | 0 | skipped | 0 | 26_pdf_events_6658c489-9aad-483b-9004-27b62225425d |
| 27 | web | press_release | indexed | TERI and ADB Convene Regional Knowledge-Sharing Session on Strengthening Transport-relate… | 2026-09-02 | cms_field | 1 | 4 | 5 | 0 | skipped | 0 | 27_web_press_release_50892144-b9bd-4cc2-8661-4ae65b2921a3 |
| 28 | web | press_release | indexed | TERI and Indo-German StoREin Project Highlight Key Energy Storage Initiatives at POWERGEN… | 2026-09-03 | cms_field | 1 | 4 | 5 | 0 | skipped | 0 | 28_web_press_release_173d88db-c2f9-4e00-a094-8a2a1cce4601 |
| 29 | web | press_release | indexed | ISA SIDS Platform and GRIHA Council Partner on ISA-iSUN Design Challenge to Promote Solar… | 2026-09-02 | cms_field | 1 | 2 | 3 | 0 | skipped | 0 | 29_web_press_release_7126f143-21fe-4372-ac55-07a092503549 |
| 30 | web | basic | indexed | New in Marine and Coastal | 2026-08-31 | created | 0 | 1 | 1 | 0 | skipped | 0 | 30_web_basic_dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3 |


### Check results across all documents

| category | check | pass | fail | n/a | failing documents |
| --- | --- | --- | --- | --- | --- |
| canonical | article_uuid_is_node_uuid | 25 | 0 | 0 | - |
| canonical | body_is_single_section | 25 | 0 | 0 | - |
| canonical | body_text_non_empty | 30 | 0 | 0 | - |
| canonical | bundle_inherited_from_parent | 5 | 0 | 0 | - |
| canonical | content_hash_is_sha256_of_body_text | 30 | 0 | 0 | - |
| canonical | extra_carries_bundle_nid_changed | 25 | 0 | 0 | - |
| canonical | facets_match_drupal_facets_rule | 25 | 0 | 0 | - |
| canonical | file_links_equal_record_files | 25 | 0 | 0 | - |
| canonical | file_url_is_fetched_url | 5 | 0 | 0 | - |
| canonical | linked_article_uuid_is_parent_node | 5 | 0 | 0 | - |
| canonical | raw_meta_equals_record_metadata | 25 | 0 | 0 | - |
| canonical | section_text_equals_page_text | 5 | 0 | 0 | - |
| canonical | sections_equal_non_empty_pages | 5 | 0 | 0 | - |
| canonical | source_url_is_parent_page | 5 | 0 | 0 | - |
| canonical | title_equals_node_title | 25 | 0 | 0 | - |
| canonical | title_precedence_description_node_filename | 5 | 0 | 0 | - |
| chunks | child_index_is_contiguous | 30 | 0 | 0 | - |
| chunks | children_carry_doc_version | 30 | 0 | 0 | - |
| chunks | children_carry_document_id | 30 | 0 | 0 | - |
| chunks | children_carry_page_numbers | 5 | 0 | 0 | - |
| chunks | children_have_embed_text_with_breadcrumb | 30 | 0 | 0 | - |
| chunks | children_within_token_limit | 30 | 0 | 0 | - |
| chunks | chunk_ids_unique | 30 | 0 | 0 | - |
| chunks | chunks_produced | 30 | 0 | 0 | - |
| chunks | content_hash_is_sha256_of_text | 30 | 0 | 0 | - |
| chunks | every_parent_reference_resolves | 30 | 0 | 0 | - |
| chunks | parents_have_at_least_two_children | 30 | 0 | 0 | - |
| chunks | parents_within_token_limit | 30 | 0 | 0 | - |
| chunks | source_lines_covered_by_chunks | 30 | 0 | 0 | - |
| dates | canonical_date_equals_evidence_value | 25 | 0 | 0 | - |
| dates | canonical_end_equals_evidence_end | 25 | 0 | 0 | - |
| dates | date_decision_current_date_is_parent_resolved | 5 | 0 | 0 | - |
| dates | date_decision_row_names_parent_node | 5 | 0 | 0 | - |
| dates | date_decision_row_presence | 30 | 0 | 0 | - |
| dates | date_source_equals_evidence_source | 25 | 0 | 0 | - |
| dates | date_source_is_document_text | 0 | 2 | 0 | 6, 7 |
| dates | date_source_is_parent_page | 3 | 0 | 0 | - |
| dates | effective_date_evidence_present | 25 | 0 | 0 | - |
| dates | effective_start_date_present | 30 | 0 | 0 | - |
| dates | override_start_equals_resolver | 2 | 0 | 0 | - |
| dates | parent_page_canonical_date_matches_parent_resolution | 5 | 0 | 0 | - |
| dates | pdf_date_path | 0 | 0 | 0 | - |
| dates | pdf_end_date_equals_parent | 3 | 0 | 0 | - |
| dates | pdf_precision_equals_parent | 3 | 0 | 0 | - |
| dates | pdf_start_date_equals_parent_resolved | 3 | 0 | 0 | - |
| dates | resolver_ran | 5 | 0 | 0 | - |
| dates | website_date_rule | 0 | 0 | 0 | - |
| graph | nothing_projected_when_skipped | 30 | 0 | 0 | - |
| knowledge | claims_cite_own_chunks_or_document | 30 | 0 | 0 | - |
| knowledge | decision_rows_equal_report | 30 | 0 | 0 | - |
| knowledge | extraction_cache_recorded | 30 | 0 | 0 | - |
| knowledge | mention_rows_equal_report | 30 | 0 | 0 | - |
| knowledge | mentions_point_at_own_chunks | 30 | 0 | 0 | - |
| knowledge | rejection_rows_equal_report | 30 | 0 | 0 | - |
| knowledge | run_row_matches_report | 30 | 0 | 0 | - |
| knowledge | run_row_written | 30 | 0 | 0 | - |
| knowledge | stage_report | 0 | 0 | 0 | - |
| knowledge | staged_claim_rows_equal_report | 30 | 0 | 0 | - |
| mysql | attachment_link_rows | 30 | 0 | 0 | - |
| mysql | author_facet_rows | 30 | 0 | 0 | - |
| mysql | ingest_log_chunk_count | 30 | 0 | 0 | - |
| mysql | ingest_log_hash_and_version | 30 | 0 | 0 | - |
| mysql | ingest_log_indexed_row | 30 | 0 | 0 | - |
| mysql | no_retry_marker | 30 | 0 | 0 | - |
| mysql | row_bundle | 30 | 0 | 0 | - |
| mysql | row_changed_mark | 30 | 0 | 0 | - |
| mysql | row_content_hash | 30 | 0 | 0 | - |
| mysql | row_date_source | 30 | 0 | 0 | - |
| mysql | row_doc_version | 30 | 0 | 0 | - |
| mysql | row_effective_end_date | 30 | 0 | 0 | - |
| mysql | row_effective_start_date | 30 | 0 | 0 | - |
| mysql | row_end_precision | 30 | 0 | 0 | - |
| mysql | row_entity_type | 30 | 0 | 0 | - |
| mysql | row_fingerprint | 30 | 0 | 0 | - |
| mysql | row_indexed_at_set | 30 | 0 | 0 | - |
| mysql | row_pipeline_version | 30 | 0 | 0 | - |
| mysql | row_raw_meta_equals_canonical | 30 | 0 | 0 | - |
| mysql | row_source_key | 30 | 0 | 0 | - |
| mysql | row_source_type | 30 | 0 | 0 | - |
| mysql | row_start_precision | 30 | 0 | 0 | - |
| mysql | row_title | 30 | 0 | 0 | - |
| mysql | row_url | 30 | 0 | 0 | - |
| mysql | state_row_exists | 30 | 0 | 0 | - |
| mysql | tag_facet_rows | 30 | 0 | 0 | - |
| mysql | theme_rows_match_classification | 30 | 0 | 0 | - |
| outcome | handler_outcome_is_indexed | 30 | 0 | 0 | - |
| outcome | no_exception | 30 | 0 | 0 | - |
| parent_child | entity_refs_inherited_from_parent | 5 | 0 | 0 | - |
| parent_child | facets_inherited_from_parent | 5 | 0 | 0 | - |
| parent_child | linked_from_parent_in_attachment_table | 5 | 0 | 0 | - |
| parent_child | parent_lists_this_file | 5 | 0 | 0 | - |
| parent_child | parents_claiming_this_file | 0 | 0 | 0 | - |
| qdrant | children_have_real_vectors | 30 | 0 | 0 | - |
| qdrant | children_stamped_with_embed_model | 30 | 0 | 0 | - |
| qdrant | every_chunk_id_is_a_point | 30 | 0 | 0 | - |
| qdrant | parents_have_zero_vectors | 30 | 0 | 0 | - |
| qdrant | payload_equals_chunk_payload_plus_stamps | 30 | 0 | 0 | - |
| qdrant | point_count_equals_chunks | 30 | 0 | 0 | - |
| qdrant | points_are_current_and_versioned | 30 | 0 | 0 | - |
| qdrant | points_carry_document_id | 30 | 0 | 0 | - |
| qdrant | points_carry_effective_start_date | 30 | 0 | 0 | - |
| qdrant | points_carry_year_precision_only_when_year | 30 | 0 | 0 | - |
| qdrant | points_stamped_with_pipeline_version | 30 | 0 | 0 | - |
| qdrant | swap_deleted_with_keep_ids | 30 | 0 | 0 | - |
| qdrant | vector_dimension_matches_setting | 30 | 0 | 0 | - |
| source | pdf_downloaded_non_empty | 5 | 0 | 0 | - |
| source | pdf_pages | 0 | 0 | 0 | - |


## Part 1 — Per-document trace

### 1. 01_web_article_491ae95c-a14d-4810-bb16-8df4ab16ad8e

- source: node `491ae95c-a14d-4810-bb16-8df4ab16ad8e` (article) “Carbon Sequestration by Seaweed is Not a Straightforward Pathway” · body 6492 chars · 0 PDF link(s) · created 2026-08-25T08:22:39+00:00 · changed 2026-08-31T07:13:06+00:00
- outcome: **indexed** in 3.927s
- canonical: title “Carbon Sequestration by Seaweed is Not a Straightforward Pathway” · 1 section(s) · 6492 chars · hash `f4f2e9360617…` · authors ['Dr Raghab Ray'] · tags ['Carbon sequestration', 'Marine ecosystem', 'Marine Litter'] · categories ['Sustainable Agriculture']
- dates: start 2026-08-25T08:22:39+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 1 parents / 5 children · Qdrant points 6
- mysql: documents=1, ·author=1, ·tag=3, ·theme=1, ·entity_mention=1, ·knowledge_run=1, ·entity_resolution_decision=1, ·entity_extraction=5, e2e_audit_ingest_log=1
- knowledge: ok · mentions 1 · resolved auto/prov/amb/unres 0/0/0/1 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/01_web_article_491ae95c-a14d-4810-bb16-8df4ab16ad8e/`

### 2. 02_web_article_0a5e1528-9f38-4f24-a0f4-3cf9a2930cb8

- source: node `0a5e1528-9f38-4f24-a0f4-3cf9a2930cb8` (article) “When Risk Stops Looking Normal: Lessons from the Nepal Floods” · body 7019 chars · 0 PDF link(s) · created 2026-08-31T09:18:16+00:00 · changed 2026-08-31T09:19:47+00:00
- outcome: **indexed** in 0.621s
- canonical: title “When Risk Stops Looking Normal: Lessons from the Nepal Floods” · 1 section(s) · 7019 chars · hash `121d1735f6fb…` · authors ['Ms Shiren Pandita'] · tags [] · categories ['Sustainable Habitat']
- dates: start 2026-08-31T09:18:16+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 0 parents / 4 children · Qdrant points 4
- mysql: documents=1, ·author=1, ·theme=1, ·knowledge_run=1, ·entity_extraction=4, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/02_web_article_0a5e1528-9f38-4f24-a0f4-3cf9a2930cb8/`

### 3. 03_web_article_816867bf-eac7-4833-bfe1-7e202ff61c51

- source: node `816867bf-eac7-4833-bfe1-7e202ff61c51` (article) “Forest Pathshaala: Adivasi Children and the Ecologies of Knowledge” · body 18271 chars · 0 PDF link(s) · created 2025-11-12T08:16:05+00:00 · changed 2026-09-02T04:16:58+00:00
- outcome: **indexed** in 1.0s
- canonical: title “Forest Pathshaala: Adivasi Children and the Ecologies of Knowledge” · 1 section(s) · 18271 chars · hash `6256ef4f6506…` · authors ['Aryaman Tewari'] · tags ['Environment education', 'Rural India'] · categories ['Environment']
- dates: start 2025-11-12T08:16:05+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 4 parents / 12 children · Qdrant points 16
- mysql: documents=1, ·author=1, ·tag=2, ·theme=1, ·entity_mention=3, ·knowledge_run=1, ·entity_resolution_decision=3, ·entity_extraction=12, e2e_audit_ingest_log=1
- knowledge: ok · mentions 3 · resolved auto/prov/amb/unres 0/0/0/3 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/03_web_article_816867bf-eac7-4833-bfe1-7e202ff61c51/`

### 4. 04_web_page_04107bb4-fefe-4ffa-be5d-f88ac9310dd6

- source: node `04107bb4-fefe-4ffa-be5d-f88ac9310dd6` (page) “TERI Alumni Association” · body 24829 chars · 3 PDF link(s) · created 2025-09-30T04:28:20+00:00 · changed 2026-09-02T04:24:58+00:00
- outcome: **indexed** in 11.373s
- canonical: title “TERI Alumni Association” · 1 section(s) · 24829 chars · hash `2162448bb18f…` · authors [] · tags [] · categories []
- dates: start 2025-09-30T04:28:20+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 6 parents / 23 children · Qdrant points 29
- mysql: documents=1, ·entity_mention=104, ·assertion_rejection=1, ·knowledge_run=1, ·attachment=3, ·entity_resolution_decision=104, ·entity_extraction=23, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 104 · resolved auto/prov/amb/unres 2/0/20/82 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/04_web_page_04107bb4-fefe-4ffa-be5d-f88ac9310dd6/`

### 5. 05_pdf_page_inbody_8a64f693f3de31c6620aa873d1d4c7425

- source: PDF `TERI-Alumni-Quarterly-Inaugural-Issue.pdf` (inbody) on page `04107bb4-fefe-4ffa-be5d-f88ac9310dd6` “TERI Alumni Association” · 26806398 bytes
- extraction: 16 pages, routes {'text': 16}, 0 tables, 37233 chars
- outcome: **indexed** in 13.772s
- canonical: title “TERI Alumni Association” · 16 section(s) · 37263 chars · hash `91a5fb091b33…` · authors [] · tags [] · categories []
- dates: start 2025-09-30T04:28:20+00:00 (day, parent_page) · end None · page rule `bundle_created` · file resolver: inherit (multi_pdf_no_evidence)
- chunks: 5 parents / 23 children · Qdrant points 28
- mysql: documents=1, ·date_decision=1, ·entity_mention=56, ·knowledge_run=1, ·attachment (as file)=1, ·entity_resolution_decision=56, ·entity_extraction=23, e2e_audit_ingest_log=1
- knowledge: ok · mentions 56 · resolved auto/prov/amb/unres 0/0/9/47 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 89 pass / 0 fail · folder `documents/05_pdf_page_inbody_8a64f693f3de31c6620aa873d1d4c7425/`

### 6. 06_pdf_page_inbody_019c7e59163edfbb3535b05744ff6949b

- source: PDF `Book-on-Dr-RK-Pachauri.pdf` (inbody) on page `04107bb4-fefe-4ffa-be5d-f88ac9310dd6` “TERI Alumni Association” · 2825799 bytes
- extraction: 248 pages, routes {'ocr': 5, 'text': 240, 'empty': 3}, 0 tables, 617552 chars
- outcome: **indexed** in 126.012s
- canonical: title “TERI Alumni Association” · 245 section(s) · 618040 chars · hash `f71488117717…` · authors [] · tags [] · categories []
- dates: start 2020-01-01T00:00:00+00:00 (year, document_copyright) · end None · page rule `bundle_created` · file resolver: OVERRIDE (copyright_statement_corroborated)
- chunks: 98 parents / 431 children · Qdrant points 529
- mysql: documents=1, ·date_decision=1, ·entity_mention=1673, ·assertion_rejection=3, ·knowledge_run=1, ·attachment (as file)=1, ·entity_resolution_decision=1673, ·entity_extraction=431, e2e_audit_ingest_log=1, ·entity (referenced)=7
- knowledge: ok · mentions 1673 · resolved auto/prov/amb/unres 29/0/50/1594 · claims built/staged/rejected 3/0/3 · projection skipped (0 edges)
- knowledge notes: ["model calls stopped at 8; the document's remaining chunks were not examined"]
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 86 pass / 1 fail · folder `documents/06_pdf_page_inbody_019c7e59163edfbb3535b05744ff6949b/`
- **failed checks:**
  - `date_source_is_document_text` —  (expected document_text, actual document_copyright)

### 7. 07_pdf_page_inbody_0a7c343146247d17ae9ebdffa512fb4a3

- source: PDF `Book_on_Dr_RK_Pachauri_II.pdf` (inbody) on page `04107bb4-fefe-4ffa-be5d-f88ac9310dd6` “TERI Alumni Association” · 1509958 bytes
- extraction: 242 pages, routes {'ocr': 2, 'text': 239, 'empty': 1}, 0 tables, 521771 chars
- outcome: **indexed** in 57.715s
- canonical: title “TERI Alumni Association” · 241 section(s) · 522251 chars · hash `551db333c39e…` · authors [] · tags [] · categories []
- dates: start 2022-01-01T00:00:00+00:00 (year, document_copyright) · end None · page rule `bundle_created` · file resolver: OVERRIDE (copyright_statement_corroborated)
- chunks: 69 parents / 294 children · Qdrant points 363
- mysql: documents=1, ·date_decision=1, ·entity_mention=882, ·assertion_rejection=3, ·knowledge_run=1, ·attachment (as file)=1, ·entity_resolution_decision=882, ·entity_extraction=294, e2e_audit_ingest_log=1, ·entity (referenced)=6
- knowledge: ok · mentions 882 · resolved auto/prov/amb/unres 11/0/89/782 · claims built/staged/rejected 3/0/3 · projection skipped (0 edges)
- knowledge notes: ["model calls stopped at 8; the document's remaining chunks were not examined"]
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 86 pass / 1 fail · folder `documents/07_pdf_page_inbody_0a7c343146247d17ae9ebdffa512fb4a3/`
- **failed checks:**
  - `date_source_is_document_text` —  (expected document_text, actual document_copyright)

### 8. 08_web_page_80d9bdc9-c159-493a-80e1-ca53cece85e3

- source: node `80d9bdc9-c159-493a-80e1-ca53cece85e3` (page) “Newsletters” · body 17638 chars · 0 PDF link(s) · created 2020-10-22T09:00:43+00:00 · changed 2026-09-03T10:30:16+00:00
- outcome: **indexed** in 3.099s
- canonical: title “Newsletters” · 1 section(s) · 17638 chars · hash `780484baa217…` · authors [] · tags [] · categories []
- dates: start 2020-10-22T09:00:43+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 4 parents / 17 children · Qdrant points 21
- mysql: documents=1, ·knowledge_run=1, ·entity_extraction=17, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/08_web_page_80d9bdc9-c159-493a-80e1-ca53cece85e3/`

### 9. 09_web_page_2a2e9a77-da56-43a7-8138-3ebf16010d1b

- source: node `2a2e9a77-da56-43a7-8138-3ebf16010d1b` (page) “Contact Us” · body 2549 chars · 0 PDF link(s) · created 2018-04-10T09:14:26+00:00 · changed 2026-09-03T11:37:35+00:00
- outcome: **indexed** in 1.905s
- canonical: title “Contact Us” · 1 section(s) · 2549 chars · hash `8629b79099aa…` · authors [] · tags [] · categories []
- dates: start 2018-04-10T09:14:26+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 1 parents / 4 children · Qdrant points 5
- mysql: documents=1, ·entity_mention=19, ·knowledge_run=1, ·entity_resolution_decision=19, ·entity_extraction=4, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 19 · resolved auto/prov/amb/unres 2/0/5/12 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/09_web_page_2a2e9a77-da56-43a7-8138-3ebf16010d1b/`

### 10. 10_web_completed_projects_36a999eb-b7c7-47fd-ac69-55f97841a9d3

- source: node `36a999eb-b7c7-47fd-ac69-55f97841a9d3` (completed_projects) “Science Technology and Innovation Hub in Gaondongrem, Goa” · body 3589 chars · 0 PDF link(s) · created 2026-06-19T04:16:09+00:00 · changed 2026-08-31T08:30:58+00:00
- outcome: **indexed** in 0.604s
- canonical: title “Science Technology and Innovation Hub in Gaondongrem, Goa” · 1 section(s) · 3589 chars · hash `37fbdaa7b370…` · authors [] · tags ['Sustainable Livelihood'] · categories ['Marine and Coastal']
- dates: start 2023-01-23T00:00:00+00:00 (day, cms_field) · end 2026-01-22T00:00:00+00:00 · rule `bundle_date_field` fields ['field_completed_start_date', 'field_completed_end_date'] raw ['2023-01-23T04:30:00+00:00', '2026-01-22T11:30:00+00:00']
- chunks: 0 parents / 3 children · Qdrant points 3
- mysql: documents=1, ·tag=1, ·theme=1, ·date_decision=1, ·entity_mention=2, ·knowledge_run=1, ·entity_resolution_decision=2, ·entity_extraction=3, e2e_audit_ingest_log=1
- knowledge: ok · mentions 2 · resolved auto/prov/amb/unres 0/0/0/2 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/10_web_completed_projects_36a999eb-b7c7-47fd-ac69-55f97841a9d3/`

### 11. 11_web_completed_projects_f4b58789-88af-4525-8c1e-93fe860663e1

- source: node `f4b58789-88af-4525-8c1e-93fe860663e1` (completed_projects) “Delivering India’s NDC Targets: Role of Transport” · body 4446 chars · 0 PDF link(s) · created 2026-08-21T03:57:50+00:00 · changed 2026-09-02T04:07:55+00:00
- outcome: **indexed** in 0.533s
- canonical: title “Delivering India’s NDC Targets: Role of Transport” · 1 section(s) · 4446 chars · hash `e5bf760d8c0b…` · authors [] · tags ['Transport'] · categories ['Transport']
- dates: start 2024-09-01T00:00:00+00:00 (day, cms_field) · end 2026-09-02T00:00:00+00:00 · rule `bundle_date_field` fields ['field_completed_start_date', 'field_completed_end_date'] raw ['2024-09-01T04:30:00+00:00', '2026-09-02T11:30:00+00:00']
- chunks: 0 parents / 3 children · Qdrant points 3
- mysql: documents=1, ·tag=1, ·theme=1, ·date_decision=1, ·entity_mention=2, ·knowledge_run=1, ·entity_resolution_decision=2, ·entity_extraction=3, e2e_audit_ingest_log=1
- knowledge: ok · mentions 2 · resolved auto/prov/amb/unres 0/0/0/2 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- knowledge notes: ['this document has no canonical PROJECT entity yet; seeding is a global pass (scripts.build_knowledge), and its claims will be staged once it runs']
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/11_web_completed_projects_f4b58789-88af-4525-8c1e-93fe860663e1/`

### 12. 12_web_completed_projects_74d106c0-968e-43dc-b873-83d2e7460af8

- source: node `74d106c0-968e-43dc-b873-83d2e7460af8` (completed_projects) “Establishing Resource and Knowledge Centre (RKC) for the Distribution Sector under the All-India Discoms Association (AIDA)” · body 1073 chars · 0 PDF link(s) · created 2026-09-08T10:45:06+00:00 · changed 2026-09-08T10:48:10+00:00
- outcome: **indexed** in 0.433s
- canonical: title “Establishing Resource and Knowledge Centre (RKC) for the Distribution Sector under the All-India Discoms Association (AIDA)” · 1 section(s) · 1073 chars · hash `0bb4d0f259ee…` · authors [] · tags ['Energy services', 'Energy technology'] · categories ['Energy']
- dates: start 2025-10-14T00:00:00+00:00 (day, cms_field) · end 2026-03-31T00:00:00+00:00 · rule `bundle_date_field` fields ['field_completed_start_date', 'field_completed_end_date'] raw ['2025-10-14T04:30:29+00:00', '2026-03-31T11:30:00+00:00']
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=2, ·theme=1, ·date_decision=1, ·entity_mention=4, ·knowledge_run=1, ·entity_resolution_decision=4, ·entity_extraction=1, e2e_audit_ingest_log=1
- knowledge: ok · mentions 4 · resolved auto/prov/amb/unres 0/0/0/4 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- knowledge notes: ['this document has no canonical PROJECT entity yet; seeding is a global pass (scripts.build_knowledge), and its claims will be staged once it runs']
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/12_web_completed_projects_74d106c0-968e-43dc-b873-83d2e7460af8/`

### 13. 13_web_feature_articles_6c62c011-9677-4f6a-9fb1-c01558c5f814

- source: node `6c62c011-9677-4f6a-9fb1-c01558c5f814` (feature_articles) “Peace in Ukraine is nowhere in sight” · body 726 chars · 0 PDF link(s) · created 2026-09-01T10:55:25+00:00 · changed 2026-09-03T11:09:49+00:00
- outcome: **indexed** in 2.365s
- canonical: title “Peace in Ukraine is nowhere in sight” · 1 section(s) · 726 chars · hash `1dfb6bfa2a94…` · authors [] · tags ['Sustainable development'] · categories ['Resources & Sustainable Development']
- dates: start 2026-09-01T10:55:25+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=1, ·theme=1, ·entity_mention=6, ·assertion_rejection=1, ·knowledge_run=1, ·entity_resolution_decision=6, ·entity_extraction=1, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 6 · resolved auto/prov/amb/unres 4/0/0/2 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/13_web_feature_articles_6c62c011-9677-4f6a-9fb1-c01558c5f814/`

### 14. 14_web_feature_articles_d0bf1f2c-7e3e-4a65-b253-42cc49e8491f

- source: node `d0bf1f2c-7e3e-4a65-b253-42cc49e8491f` (feature_articles) “Nuclear power expansion: India needs a clear financing strategy” · body 1104 chars · 0 PDF link(s) · created 2026-09-06T09:18:39+00:00 · changed 2026-09-07T09:51:43+00:00
- outcome: **indexed** in 2.607s
- canonical: title “Nuclear power expansion: India needs a clear financing strategy” · 1 section(s) · 1104 chars · hash `c9c074e036e8…` · authors [] · tags ['Nuclear energy'] · categories ['Electricity and Renewables']
- dates: start 2026-09-06T09:18:39+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=1, ·theme=1, ·entity_mention=10, ·assertion_rejection=1, ·knowledge_run=1, ·entity_resolution_decision=10, ·entity_extraction=1, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 10 · resolved auto/prov/amb/unres 4/0/2/4 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/14_web_feature_articles_d0bf1f2c-7e3e-4a65-b253-42cc49e8491f/`

### 15. 15_web_feature_articles_2a1ca7a4-e2f8-4bb1-ad8c-b7a915986e69

- source: node `2a1ca7a4-e2f8-4bb1-ad8c-b7a915986e69` (feature_articles) “Nepal: A wake-up call” · body 618 chars · 0 PDF link(s) · created 2026-09-07T08:58:40+00:00 · changed 2026-09-08T09:04:12+00:00
- outcome: **indexed** in 2.252s
- canonical: title “Nepal: A wake-up call” · 1 section(s) · 618 chars · hash `6977bef29066…` · authors ['Mr Ajay Shankar'] · tags ['Climate change', 'Climate resilience', 'Global warming', 'Net zero emission'] · categories ['Electricity and Renewables', 'Climate Change']
- dates: start 2026-09-07T08:58:40+00:00 (day, created) · end None · rule `bundle_created` fields ['created'] raw []
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·author=1, ·tag=4, ·theme=2, ·entity_mention=6, ·assertion_rejection=1, ·knowledge_run=1, ·entity_resolution_decision=6, ·entity_extraction=1, e2e_audit_ingest_log=1, ·entity (referenced)=2
- knowledge: ok · mentions 6 · resolved auto/prov/amb/unres 4/2/0/0 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/15_web_feature_articles_2a1ca7a4-e2f8-4bb1-ad8c-b7a915986e69/`

### 16. 16_web_ongoing_projects_a240619a-8365-429e-adde-9bf707c46882

- source: node `a240619a-8365-429e-adde-9bf707c46882` (ongoing_projects) “Adoption of green fuels in Indian Maritime sector.” · body 6526 chars · 0 PDF link(s) · created 2026-09-08T10:21:39+00:00 · changed 2026-09-08T10:28:15+00:00
- outcome: **indexed** in 0.672s
- canonical: title “Adoption of green fuels in Indian Maritime sector.” · 1 section(s) · 6526 chars · hash `5ea5ef71872c…` · authors [] · tags ['Carbon intensity', 'E-Fuels', 'Fuel cell/hydrogen energy safety', 'GFI', 'Green Ammonia', 'Green Methanol', 'Green Shipping', 'Greenhouse gases', 'Hydrogen energy storage', 'Renewable energy', 'Renewable natural resources', 'Sustainable Development Goals', 'ZNZ Fuels'] · categories ['Pyrolytic Biofuels, Biochar & Green Chemicals']
- dates: start 2026-01-14T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_ongoing_start_date'] raw ['2026-01-14T04:30:00+00:00']
- chunks: 1 parents / 5 children · Qdrant points 6
- mysql: documents=1, ·tag=13, ·theme=1, ·date_decision=1, ·knowledge_run=1, ·entity_extraction=5, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- knowledge notes: ['this document has no canonical PROJECT entity yet; seeding is a global pass (scripts.build_knowledge), and its claims will be staged once it runs']
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/16_web_ongoing_projects_a240619a-8365-429e-adde-9bf707c46882/`

### 17. 17_web_ongoing_projects_2f5ede1c-8091-4ec8-9dd8-866797f0af41

- source: node `2f5ede1c-8091-4ec8-9dd8-866797f0af41` (ongoing_projects) “National Roadmap: Solarisation of Closed & Reclaimed Coal Mines in India” · body 2437 chars · 0 PDF link(s) · created 2026-09-08T10:31:02+00:00 · changed 2026-09-08T10:33:32+00:00
- outcome: **indexed** in 2.391s
- canonical: title “National Roadmap: Solarisation of Closed & Reclaimed Coal Mines in India” · 1 section(s) · 2437 chars · hash `dbcfee6fb4c3…` · authors [] · tags ['Renewable energy'] · categories ['Energy']
- dates: start 2026-04-10T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_ongoing_start_date'] raw ['2026-04-10T04:30:00+00:00']
- chunks: 1 parents / 2 children · Qdrant points 3
- mysql: documents=1, ·tag=1, ·theme=1, ·date_decision=1, ·entity_mention=8, ·assertion_rejection=1, ·knowledge_run=1, ·entity_resolution_decision=8, ·entity_extraction=2, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 8 · resolved auto/prov/amb/unres 2/0/0/6 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- knowledge notes: ['this document has no canonical PROJECT entity yet; seeding is a global pass (scripts.build_knowledge), and its claims will be staged once it runs']
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/17_web_ongoing_projects_2f5ede1c-8091-4ec8-9dd8-866797f0af41/`

### 18. 18_web_ongoing_projects_3807402a-fb95-4900-85ae-697403882e33

- source: node `3807402a-fb95-4900-85ae-697403882e33` (ongoing_projects) “Peer Review of Carbon Credit Methodology for Jute-Based Net CO2 Emission Reduction” · body 1325 chars · 0 PDF link(s) · created 2026-09-08T10:34:19+00:00 · changed 2026-09-08T10:35:59+00:00
- outcome: **indexed** in 0.465s
- canonical: title “Peer Review of Carbon Credit Methodology for Jute-Based Net CO2 Emission Reduction” · 1 section(s) · 1325 chars · hash `2238c571ae7d…` · authors [] · tags ['Carbon market', 'Carbon sequestration', 'Smart agriculture', 'Croplands'] · categories ['Land']
- dates: start 2026-05-22T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_ongoing_start_date'] raw ['2026-05-22T04:30:00+00:00']
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=4, ·theme=1, ·date_decision=1, ·knowledge_run=1, ·entity_extraction=1, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- knowledge notes: ['this document has no canonical PROJECT entity yet; seeding is a global pass (scripts.build_knowledge), and its claims will be staged once it runs']
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/18_web_ongoing_projects_3807402a-fb95-4900-85ae-697403882e33/`

### 19. 19_web_news_b9d714ff-34cd-4d73-b67e-083c80936ebd

- source: node `b9d714ff-34cd-4d73-b67e-083c80936ebd` (news) “TERI and ADB Convene Regional Knowledge-Sharing Session on Strengthening Transport-related Climate Targets in Asia and the Pacific” · body 188 chars · 0 PDF link(s) · created 2026-09-03T09:27:39+00:00 · changed 2026-09-08T09:30:49+00:00
- outcome: **indexed** in 0.618s
- canonical: title “TERI and ADB Convene Regional Knowledge-Sharing Session on Strengthening Transport-related Climate Targets in Asia and the Pacific” · 1 section(s) · 188 chars · hash `ef4a44b6e63c…` · authors [] · tags ['Climate action', 'Climate change'] · categories ['Transport']
- dates: start 2026-09-03T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_news_date'] raw ['2026-09-03T11:30:03+00:00']
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=2, ·theme=1, ·date_decision=1, ·knowledge_run=1, ·entity_extraction=1, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/19_web_news_b9d714ff-34cd-4d73-b67e-083c80936ebd/`

### 20. 20_web_news_74aba0c4-1457-4495-9263-a0b95aa97875

- source: node `74aba0c4-1457-4495-9263-a0b95aa97875` (news) “ISA SIDS and GRIHA Launch ISA-iSUN Design Challenge to Promote Solar and Climate-Resilient Tourism Infrastructure in Island Nations” · body 274 chars · 0 PDF link(s) · created 2026-09-04T09:31:12+00:00 · changed 2026-09-08T09:34:52+00:00
- outcome: **indexed** in 0.455s
- canonical: title “ISA SIDS and GRIHA Launch ISA-iSUN Design Challenge to Promote Solar and Climate-Resilient Tourism Infrastructure in Island Nations” · 1 section(s) · 274 chars · hash `d6d51130fa36…` · authors [] · tags ['GRIHA Council', 'Solar energy', 'Climate resilience'] · categories ['Sustainable Habitat']
- dates: start 2026-09-04T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_news_date'] raw ['2026-09-04T11:30:03+00:00']
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=3, ·theme=1, ·date_decision=1, ·entity_mention=2, ·knowledge_run=1, ·entity_resolution_decision=2, ·entity_extraction=1, e2e_audit_ingest_log=1
- knowledge: ok · mentions 2 · resolved auto/prov/amb/unres 0/0/0/2 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/20_web_news_74aba0c4-1457-4495-9263-a0b95aa97875/`

### 21. 21_web_news_c00a39be-c021-4e95-9ce0-1c4a1912bc5e

- source: node `c00a39be-c021-4e95-9ce0-1c4a1912bc5e` (news) “Sarbananda Sonowal Charts Course for Zero-Emission Shipping Corridors, Pushes Ports to Fast-Track Green Fuel Readiness” · body 289 chars · 0 PDF link(s) · created 2026-09-03T10:08:28+00:00 · changed 2026-09-08T10:12:22+00:00
- outcome: **indexed** in 0.505s
- canonical: title “Sarbananda Sonowal Charts Course for Zero-Emission Shipping Corridors, Pushes Ports to Fast-Track Green Fuel Readiness” · 1 section(s) · 289 chars · hash `c8301da5899f…` · authors [] · tags ['Green Shipping', 'Zero emission', 'Green Fuels'] · categories ['Resource Efficiency & Governance']
- dates: start 2026-09-03T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_news_date'] raw ['2026-09-03T11:30:03+00:00']
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·tag=3, ·theme=1, ·date_decision=1, ·entity_mention=1, ·knowledge_run=1, ·entity_resolution_decision=1, ·entity_extraction=1, e2e_audit_ingest_log=1
- knowledge: ok · mentions 1 · resolved auto/prov/amb/unres 0/0/1/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/21_web_news_c00a39be-c021-4e95-9ce0-1c4a1912bc5e/`

### 22. 22_web_events_3c24d94b-f8bb-4475-b147-56dd0c35318f

- source: node `3c24d94b-f8bb-4475-b147-56dd0c35318f` (events) “Darbari Seth Memorial Lecture 2026” · body 3625 chars · 1 PDF link(s) · created 2026-08-17T06:09:28+00:00 · changed 2026-08-31T09:52:29+00:00
- outcome: **indexed** in 2.417s
- canonical: title “Darbari Seth Memorial Lecture 2026” · 1 section(s) · 3625 chars · hash `b611c1133e0b…` · authors [] · tags ['Energy access', 'Green growth'] · categories []
- dates: start 2026-08-21T00:00:00+00:00 (day, cms_field) · end 2026-08-21T00:00:00+00:00 · rule `bundle_date_field` fields ['field_event_start_date', 'field_event_end_date'] raw ['2026-08-20T22:00:00+00:00', '2026-08-21T11:30:00+00:00']
- chunks: 1 parents / 3 children · Qdrant points 4
- mysql: documents=1, ·tag=2, ·date_decision=1, ·entity_mention=15, ·assertion_rejection=1, ·knowledge_run=1, ·attachment=1, ·entity_resolution_decision=15, ·entity_extraction=3, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 15 · resolved auto/prov/amb/unres 1/0/0/14 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/22_web_events_3c24d94b-f8bb-4475-b147-56dd0c35318f/`

### 23. 23_pdf_events_33c32e72-2a50-4547-86a1-269699dade92

- source: PDF `DSML2026_ AGENDA.pdf` (attachment) on page `3c24d94b-f8bb-4475-b147-56dd0c35318f` “Darbari Seth Memorial Lecture 2026” · 92856 bytes
- extraction: 1 pages, routes {'text': 1}, 1 tables, 2485 chars
- outcome: **indexed** in 3.327s
- canonical: title “Darbari Seth Memorial Lecture 2026” · 1 section(s) · 2485 chars · hash `c6366147e8e8…` · authors [] · tags ['Energy access', 'Green growth'] · categories []
- dates: start 2026-08-21T00:00:00+00:00 (day, parent_page) · end 2026-08-21T00:00:00+00:00 · page rule `bundle_date_field` · file resolver: inherit (parent_bundle_date_field)
- chunks: 1 parents / 2 children · Qdrant points 3
- mysql: documents=1, ·tag=2, ·date_decision=1, ·entity_mention=15, ·knowledge_run=1, ·attachment (as file)=1, ·entity_resolution_decision=15, ·entity_extraction=2, e2e_audit_ingest_log=1
- knowledge: ok · mentions 15 · resolved auto/prov/amb/unres 0/0/6/9 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 89 pass / 0 fail · folder `documents/23_pdf_events_33c32e72-2a50-4547-86a1-269699dade92/`

### 24. 24_web_events_ce219043-a7a7-41ed-9812-2ecfe3842fe1

- source: node `ce219043-a7a7-41ed-9812-2ecfe3842fe1` (events) “World Sustainable Development Summit 2027: Curtain Raiser” · body 3951 chars · 0 PDF link(s) · created 2026-09-07T05:27:15+00:00 · changed 2026-09-07T08:30:56+00:00
- outcome: **indexed** in 0.511s
- canonical: title “World Sustainable Development Summit 2027: Curtain Raiser” · 1 section(s) · 3951 chars · hash `dbd22d641e79…` · authors [] · tags ['Climate vulnerability'] · categories ['Resources & Sustainable Development']
- dates: start 2026-09-09T00:00:00+00:00 (day, cms_field) · end 2026-09-09T00:00:00+00:00 · rule `bundle_date_field` fields ['field_event_start_date', 'field_event_end_date'] raw ['2026-09-09T10:30:00+00:00', '2026-09-09T12:30:00+00:00']
- chunks: 1 parents / 2 children · Qdrant points 3
- mysql: documents=1, ·tag=1, ·theme=1, ·date_decision=1, ·knowledge_run=1, ·entity_extraction=2, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/24_web_events_ce219043-a7a7-41ed-9812-2ecfe3842fe1/`

### 25. 25_web_events_c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1

- source: node `c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1` (events) “WCEF2026 Accelerator Session: Circular Public Procurement for Sustainable Consumption and Production” · body 3330 chars · 1 PDF link(s) · created 2026-08-14T07:25:38+00:00 · changed 2026-09-08T06:49:49+00:00
- outcome: **indexed** in 0.484s
- canonical: title “WCEF2026 Accelerator Session: Circular Public Procurement for Sustainable Consumption and Production” · 1 section(s) · 3330 chars · hash `7e696dba9705…` · authors [] · tags ['Environmental governance', 'Government policy/regulations', 'Government schemes', 'Sustainable development', 'Sustainable Development Goals', 'Sustainable public procurement'] · categories ['Resources & Sustainable Development']
- dates: start 2026-09-18T00:00:00+00:00 (day, cms_field) · end 2026-09-18T00:00:00+00:00 · rule `bundle_date_field` fields ['field_event_start_date', 'field_event_end_date'] raw ['2026-09-18T08:30:00+00:00', '2026-09-18T10:00:00+00:00']
- chunks: 0 parents / 2 children · Qdrant points 2
- mysql: documents=1, ·tag=6, ·theme=1, ·date_decision=1, ·knowledge_run=1, ·attachment=1, ·entity_extraction=2, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/25_web_events_c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1/`

### 26. 26_pdf_events_6658c489-9aad-483b-9004-27b62225425d

- source: PDF `Concept Note_WCEF_CPP_Ecolabel_virtual.pdf` (attachment) on page `c78a7fde-a2f5-4b5c-9926-8f4f5ee240b1` “WCEF2026 Accelerator Session: Circular Public Procurement for Sustainable Consumption and Production” · 304839 bytes
- extraction: 2 pages, routes {'text': 2}, 1 tables, 3547 chars
- outcome: **indexed** in 1.969s
- canonical: title “Concept Note WCEF” · 2 section(s) · 3549 chars · hash `2906b1d7628d…` · authors [] · tags ['Environmental governance', 'Government policy/regulations', 'Government schemes', 'Sustainable development', 'Sustainable Development Goals', 'Sustainable public procurement'] · categories ['Resources & Sustainable Development']
- dates: start 2026-09-18T00:00:00+00:00 (day, parent_page) · end 2026-09-18T00:00:00+00:00 · page rule `bundle_date_field` · file resolver: inherit (parent_bundle_date_field)
- chunks: 0 parents / 3 children · Qdrant points 3
- mysql: documents=1, ·tag=6, ·theme=1, ·date_decision=1, ·knowledge_run=1, ·attachment (as file)=1, ·entity_extraction=3, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 89 pass / 0 fail · folder `documents/26_pdf_events_6658c489-9aad-483b-9004-27b62225425d/`

### 27. 27_web_press_release_50892144-b9bd-4cc2-8661-4ae65b2921a3

- source: node `50892144-b9bd-4cc2-8661-4ae65b2921a3` (press_release) “TERI and ADB Convene Regional Knowledge-Sharing Session on Strengthening Transport-related Climate Targets in Asia and the Pacific” · body 6924 chars · 0 PDF link(s) · created 2026-09-03T08:10:05+00:00 · changed 2026-09-03T08:37:07+00:00
- outcome: **indexed** in 5.247s
- canonical: title “TERI and ADB Convene Regional Knowledge-Sharing Session on Strengthening Transport-related Climate Targets in Asia and the Pacific” · 1 section(s) · 6924 chars · hash `c866dd57858b…` · authors [] · tags ['Electric vehicles', 'Transportation', 'Urban transport'] · categories ['Transport']
- dates: start 2026-09-02T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_pressrelease_date'] raw ['2026-09-02T13:30:25+00:00']
- chunks: 1 parents / 4 children · Qdrant points 5
- mysql: documents=1, ·tag=3, ·theme=1, ·date_decision=1, ·entity_mention=6, ·knowledge_run=1, ·entity_resolution_decision=6, ·entity_extraction=4, e2e_audit_ingest_log=1, ·entity (referenced)=2
- knowledge: ok · mentions 6 · resolved auto/prov/amb/unres 6/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/27_web_press_release_50892144-b9bd-4cc2-8661-4ae65b2921a3/`

### 28. 28_web_press_release_173d88db-c2f9-4e00-a094-8a2a1cce4601

- source: node `173d88db-c2f9-4e00-a094-8a2a1cce4601` (press_release) “TERI and Indo-German StoREin Project Highlight Key Energy Storage Initiatives at POWERGEN India 2026” · body 6837 chars · 0 PDF link(s) · created 2026-09-03T11:22:30+00:00 · changed 2026-09-03T11:29:08+00:00
- outcome: **indexed** in 9.777s
- canonical: title “TERI and Indo-German StoREin Project Highlight Key Energy Storage Initiatives at POWERGEN India 2026” · 1 section(s) · 6837 chars · hash `3c6a69384a4e…` · authors [] · tags ['Energy storage', 'Renewable energy', 'Energy transitions'] · categories ['Energy']
- dates: start 2026-09-03T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_pressrelease_date'] raw ['2026-09-03T04:30:00+00:00']
- chunks: 1 parents / 4 children · Qdrant points 5
- mysql: documents=1, ·tag=3, ·theme=1, ·date_decision=1, ·entity_mention=13, ·assertion_rejection=1, ·knowledge_run=1, ·entity_resolution_decision=13, ·entity_extraction=4, e2e_audit_ingest_log=1, ·entity (referenced)=2
- knowledge: ok · mentions 13 · resolved auto/prov/amb/unres 3/0/0/10 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/28_web_press_release_173d88db-c2f9-4e00-a094-8a2a1cce4601/`

### 29. 29_web_press_release_7126f143-21fe-4372-ac55-07a092503549

- source: node `7126f143-21fe-4372-ac55-07a092503549` (press_release) “ISA SIDS Platform and GRIHA Council Partner on ISA-iSUN Design Challenge to Promote Solar and Climate-Resilient Tourism Infrastructure in Island Nations” · body 4201 chars · 0 PDF link(s) · created 2026-09-07T08:33:00+00:00 · changed 2026-09-07T08:35:01+00:00
- outcome: **indexed** in 4.026s
- canonical: title “ISA SIDS Platform and GRIHA Council Partner on ISA-iSUN Design Challenge to Promote Solar and Climate-Resilient Tourism Infrastructure in Island Nations” · 1 section(s) · 4201 chars · hash `d609dc684bf0…` · authors [] · tags ['Habitat', 'Sustainable design', 'Buildings'] · categories ['Sustainable Habitat', 'Buildings']
- dates: start 2026-09-02T00:00:00+00:00 (day, cms_field) · end None · rule `bundle_date_field` fields ['field_pressrelease_date'] raw ['2026-09-02T04:30:25+00:00']
- chunks: 1 parents / 2 children · Qdrant points 3
- mysql: documents=1, ·tag=3, ·theme=2, ·date_decision=1, ·entity_mention=14, ·assertion_rejection=1, ·knowledge_run=1, ·entity_resolution_decision=14, ·entity_extraction=2, e2e_audit_ingest_log=1, ·entity (referenced)=1
- knowledge: ok · mentions 14 · resolved auto/prov/amb/unres 2/0/1/11 · claims built/staged/rejected 1/0/1 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/29_web_press_release_7126f143-21fe-4372-ac55-07a092503549/`

### 30. 30_web_basic_dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3

- source: node `dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3` (basic) “New in Marine and Coastal” · body 471 chars · 0 PDF link(s) · created 2026-08-31T08:25:46+00:00 · changed 2026-08-31T08:30:14+00:00
- outcome: **indexed** in 0.425s
- canonical: title “New in Marine and Coastal” · 1 section(s) · 471 chars · hash `99b483369ff6…` · authors [] · tags [] · categories []
- dates: start 2026-08-31T08:25:46+00:00 (day, created) · end None · rule `bundle_unmapped` fields [] raw []
- chunks: 0 parents / 1 children · Qdrant points 1
- mysql: documents=1, ·knowledge_run=1, ·entity_extraction=1, e2e_audit_ingest_log=1
- knowledge: ok · mentions 0 · resolved auto/prov/amb/unres 0/0/0/0 · claims built/staged/rejected 0/0/0 · projection skipped (0 edges)
- neo4j: document stub no · claim nodes 0 · current edges 0
- checks: 79 pass / 0 fail · folder `documents/30_web_basic_dcc0e08d-4ed0-4ab7-a2b8-ce3b27be4df3/`

