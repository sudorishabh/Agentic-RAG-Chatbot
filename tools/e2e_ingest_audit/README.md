# End-to-end ingestion audit (30 freshly fetched documents)

Runs the **real** write path — `app.ingestion.pipeline.ingest_drupal` followed by
the sweep tail (`knowledge_sync.catch_up`, `graph_sync.project_after_sweep`,
`reconcile.reconcile_after_sweep`) — on a fresh sample of live Drupal content,
and writes one evidence folder per document covering every stage from the raw
JSON:API resource / PDF bytes to the rows in MySQL, the points in Qdrant and the
nodes in Neo4j.

No application code is changed. The pipeline is observed by wrapping module
attributes it resolves at call time (`tools/e2e_ingest_audit/capture.py`); the
wrappers call the real implementation and record inputs and outputs.

```bash
python -m tools.e2e_ingest_audit.run_audit --target 30
python -m tools.e2e_ingest_audit.run_audit --target 30 --out reports/e2e_ingest_audit/run-30docs
```

## Isolation

| Store | Where the run writes | Production left untouched |
| --- | --- | --- |
| MySQL | `e2e_audit_documents*`, `e2e_audit_ingest_log` (all names derive from `INGEST_STATE_TABLE` / `INGEST_LOG_TABLE`) | `documents*`, `ingest_log` |
| Qdrant | collection `e2e_audit_documents`, recreated per run | collection `documents` |
| Neo4j | a throwaway `neo4j:2026.07.1-community` container on bolt 7688 / http 7475, removed at the end (`--keep-neo4j` keeps it) | the compose instance on 7687 |

The only production data read is a **snapshot of the canonical entity store**
(`documents_entity`, `_entity_alias`, `_entity_identifier`), copied into the
isolated prefix so the per-document knowledge stage resolves mentions against
the index a deployment has. Disable with `--no-entity-snapshot`. No check
asserts against production data.

## Selection

The real crawl walks each bundle oldest-first from its high-water mark, which on
empty state tables would start in 2017. So `select_docs.py` samples the newest
records of every configured source with the real extractor (newest-first),
keeps the raw JSON:API resource of each, and greedily fills to exactly `--target`
documents counting one document per node plus one per distinct attached PDF —
the same fan-out change detection performs. The real `detect_drupal_changes`
then runs with only its bundle enumeration substituted, so status, fingerprint,
attachment fan-out, in-body de-duplication and block filtering are the
pipeline's own.

## Output

```
<run dir>/
  REPORT.md            Part 1 generated (summary, per-document trace, check matrix); Part 2 assessment
  summary.json         everything in REPORT.md as data, plus effective settings (secrets stripped)
  selection.json       the nodes chosen, with their files
  post_sweep.json      catch-up, projection and reconciliation results
  timings.json         app.observability.metrics snapshot (ingest.extract/chunk/embed/upsert spans)
  run.log              every log line the pipeline emitted
  documents/NN_<web|pdf>_<bundle>_<id>/
    README.md                 stage trace + check table for this document
    00_source/                raw JSON:API resource (+ included) / parent record, file link, downloaded PDF
    01_change_record.json     ChangeRecord as yielded, outcome, per-stage seconds
    02_extraction.json        PDF: pages, routes, tables, metadata · web: HTML->text per field, PDF links found
    03_canonical.json/.txt    CanonicalDocument and the exact text content_hash covers
    04_dates.json             EffectiveDate evidence / ResolvedDate, raw CMS values, parent page date
    05_chunks.json/.md        every parent and child chunk, embed_text, payload; readable tree
    06_qdrant.json            every point read back (payload + vector summary)
    07_mysql.json             every row in every catalog/knowledge table that refers to the document
    08_knowledge.json         StageReport + mention/decision/claim/rejection/candidate rows
    09_neo4j.json             Document stub, chunk stubs, Claim nodes, current-state edges
    10_checks.json            every cross-stage check with expected/actual
    log.txt                   the pipeline's log lines while this document was handled
```

Exit code 0 when every check passed, 1 otherwise.

## Cleanup

The isolated MySQL tables and Qdrant collection are left in place for
inspection. To remove them:

```sql
-- MySQL (all names start with e2e_audit_)
SET FOREIGN_KEY_CHECKS=0; DROP TABLE IF EXISTS e2e_audit_documents, e2e_audit_documents_author, ...; SET FOREIGN_KEY_CHECKS=1;
```

```bash
curl -X DELETE http://localhost:6333/collections/e2e_audit_documents
```
