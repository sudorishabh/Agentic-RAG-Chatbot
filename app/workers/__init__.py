"""Write-path scheduling: what runs ingestion, and when.

:mod:`.scheduler` owns the periodic sweep task the ingestion server starts;
:mod:`.tasks` is the callable surface (``sweep``, ``ingest_drupal``,
``reindex_document``) shared by that scheduler, the HTTP control plane and the
CLI.
"""
