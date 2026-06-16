from __future__ import annotations

import json

from app.local_tests._util import SAMPLES, Reporter


def main() -> None:
    from app.ingestion.canonical import from_drupal_export

    rep = Reporter("CANONICAL NORMALIZATION TEST", "canonical_result.txt")
    items = json.loads((SAMPLES / "sample_article.json").read_text(encoding="utf-8"))
    rep.kv("source file", "samples/sample_article.json")
    rep.kv("records", len(items))
    rep.line()

    for i, item in enumerate(items):
        doc = from_drupal_export(item)
        rep.rule("-", f"[{i}] {doc.title}")
        rep.kv("document_id", doc.document_id)
        rep.kv("source_type", doc.source_type)
        rep.kv("source_url", doc.source_url)
        rep.kv("article_uuid", doc.article_uuid)
        rep.kv("authors", doc.authors)
        rep.kv("tags", doc.tags)
        rep.kv("categories", doc.categories)
        rep.kv("published_at", doc.published_at)
        rep.kv("language", doc.language)
        rep.kv("tenant_id", doc.tenant_id)
        rep.kv("acl", doc.acl)
        rep.kv("is_paginated", doc.is_paginated)
        rep.kv("sections", len(doc.sections))
        rep.kv("content_hash", doc.content_hash[:16] + "…")
        rep.kv("extra", doc.extra)
        rep.line()
        rep.line("body preview:")
        rep.preview(doc.full_text(), limit=400)
        rep.line()

    rep.write()


if __name__ == "__main__":
    main()
