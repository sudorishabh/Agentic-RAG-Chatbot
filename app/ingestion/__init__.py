"""The write path: the live site -> chunks in Qdrant + rows in MySQL.

End-to-end documentation lives in ``docs/ingestion/``. In short:

    change_detection/  what changed since last run (the crawl window)
    extractors/        Drupal JSON:API + PDF text/table extraction
    date_*.py          what date a document carries, and why
    canonical.py       one document shape everything converges on
    chunking/          parent/child windows, chunk identity, payload
    indexer.py         vector reuse, embedding, batched upsert
    pipeline.py        the run coordinator and the per-document handler

Operational tooling (reprocess, recovery, reconcile, backfill) sits beside them
as plain modules with CLIs.
"""
