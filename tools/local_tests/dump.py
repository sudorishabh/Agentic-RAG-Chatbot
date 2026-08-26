"""Render a complete per-document dict (from serialize.capture_to_dict) as a
readable text dump — nothing truncated. Every page, section, parent, child,
payload, and MySQL row is shown in full.
"""

from __future__ import annotations

import json
from typing import Any

from tools.local_tests import reporting as rep


def _json(value: Any, indent: int = 4) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    rep.block(text, indent=indent)


def _extraction(data: dict[str, Any] | None) -> None:
    if data is None:
        return
    rep.section("EXTRACTION (PDF)")
    rep.kv("source", data["source"])
    rep.kv("pages", data["page_count"])
    rep.kv("metadata", data["metadata"])
    for page in data["pages"]:
        rep.emit()
        rep.emit(
            f"  === page {page['page_number']} "
            f"(via {page['extracted_via']}, {page['char_count']} chars) ==="
        )
        rep.block(page["text"], indent=4)
        for i, table in enumerate(page["tables"]):
            rep.emit(
                f"    [table {i} on page {table['page_number']}: "
                f"{table['rows']}x{table['cols']}"
                + (f", caption={table['caption']!r}" if table["caption"] else "")
                + "]"
            )
            rep.block(table["markdown"], indent=6)


def _canonical(data: dict[str, Any] | None) -> None:
    if data is None:
        return
    rep.section("CANONICAL DOCUMENT")
    for key in (
        "document_id", "source_type", "title", "source_url", "file_url",
        "pdf_id", "pdf_path", "article_uuid", "linked_pdf_id",
        "linked_article_uuid", "language", "published_at",
        "doc_version", "is_current", "content_hash", "is_paginated",
        "authors", "tags", "categories", "extra",
    ):
        rep.kv(key, data[key])

    rep.emit()
    rep.emit(f"  entity_refs ({len(data['entity_refs'])}):")
    for ref in data["entity_refs"]:
        rep.emit(
            f"    - {ref['field_name']} | {ref['label']} | {ref['entity_type']}"
            f" | uuid={ref['uuid']} | vocabulary={ref['vocabulary']}"
        )

    rep.emit()
    rep.emit(f"  file_links ({len(data['file_links'])}):")
    for link in data["file_links"]:
        rep.emit(
            f"    - uuid={link['uuid']} | origin={link['origin']} |"
            f" filename={link['filename']} | url={link['url']}"
        )

    rep.emit()
    rep.emit("  raw_meta (full source metadata):")
    _json(data["raw_meta"], indent=4)

    rep.emit()
    rep.emit(f"  sections ({data['section_count']}):")
    for section in data["sections"]:
        rep.emit()
        rep.emit(
            f"    [section order={section['order']}]"
            f" heading={section['heading']!r}"
            f" pages={section['page_start']}-{section['page_end']}"
            f" chars={section['char_count']}"
        )
        rep.block(section["text"], indent=6)


def _chunk(chunk: dict[str, Any], label: str) -> None:
    rep.emit()
    rep.emit(f"  ===== {label}  (chunk_id={chunk['chunk_id']}) =====")
    for key in (
        "is_parent", "parent_chunk_id", "chunk_index", "section_heading",
        "section_type", "page_number", "page_range", "token_count",
        "content_hash", "has_table",
    ):
        rep.kv(key, chunk[key], indent=4)
    if chunk["table_markdown"]:
        rep.emit("    table_markdown:")
        rep.block(chunk["table_markdown"], indent=6)
    rep.emit("    text:")
    rep.block(chunk["text"], indent=6)
    rep.emit("    payload (as upserted to Qdrant):")
    _json(chunk["payload"], indent=6)


def _chunking(data: dict[str, Any]) -> None:
    rep.section("CHUNKING")
    rep.kv("parents", data["parent_count"])
    rep.kv("children", data["child_count"])
    for i, parent in enumerate(data["parents"]):
        _chunk(parent, f"PARENT {i}")
    for child in data["children"]:
        _chunk(child, f"CHILD index={child['chunk_index']}")


def _mysql(data: dict[str, Any]) -> None:
    rep.section("MYSQL CATALOG (read back)")
    rep.emit("  state row:")
    _json(data["state_row"], indent=4)
    rep.kv("author facet rows", data["author_rows"])
    rep.kv("theme facet rows", data["theme_rows"])
    rep.emit("  term_link rows:")
    _json(data["term_link_rows"], indent=4)
    rep.emit("  attachment rows:")
    _json(data["attachment_rows"], indent=4)
    rep.emit("  ingest_log rows:")
    _json(data["ingest_log_rows"], indent=4)


def render(data: dict[str, Any]) -> None:
    """Emit the full raw dump for one document to all active sinks."""
    rep.header(f"{data['document_id']}  ->  {data['outcome'].upper()}")
    rep.section("CHANGE DETECTION")
    for key, value in data["change_detection"].items():
        rep.kv(key, value)
    if data["error"]:
        rep.kv("error", data["error"])
    _extraction(data["extraction"])
    _canonical(data["canonical"])
    _chunking(data["chunking"])
    rep.section("INDEXING")
    rep.kv("qdrant points", data["indexing"]["qdrant_points"])
    _mysql(data["mysql"])
