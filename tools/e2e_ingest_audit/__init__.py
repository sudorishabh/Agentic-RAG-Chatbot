"""End-to-end ingestion audit: 30 freshly fetched documents, every stage traced.

Runs the real write path (``app.ingestion.pipeline.ingest_drupal`` plus the
sweep tail) against isolated stores and writes one evidence folder per
document. Nothing under ``app/`` is modified; the pipeline is observed by
wrapping module attributes at run time.
"""
