"""End-to-end Drupal extraction test over the live JSON:API corpus.

Runs the full extraction flow for every fetched Drupal node:

    iter_records(bundles)       ->  DrupalRecord            (live JSON:API crawl)
    chunk_drupal_record(record) ->  list[Chunk]             (canonical + chunking)
    -> id + vector + payload points                          (exactly what Qdrant gets)

and writes a categorised result folder per record, **entirely inside this
directory** (``app/local_tests/drupal_extraction_test/results/<bundle>/<slug>/``):

    00_summary.txt         headline stats + chunk breakdown
    00_summary.json        the same stats, machine-readable
    01_record.md           title + url + extracted body text
    02_chunks.md           canonical chunking output (parents + children)
    03_metadata.md         record metadata + canonical/chunk metadata
    03_metadata.json       the same metadata, machine-readable
    04_qdrant_points.json  the exact id+vector+payload points upserted to Qdrant
    04_qdrant_points.md    readable preview of those points (vectors truncated)
    full_text.md           the full record text (DrupalRecord.to_text())

A top-level ``results/_index.md`` + ``results/_index.json`` summarise the whole
run across all records and bundles.

Usage
-----
    # the default bundles (drupal_extractor.DEFAULT_BUNDLES)
    python -m app.local_tests.drupal_extraction_test.run

    # specific bundles
    python -m app.local_tests.drupal_extraction_test.run news events

    # cap records per bundle (live crawls can be large)
    python -m app.local_tests.drupal_extraction_test.run news --limit 5

    # include unpublished nodes; skip embedding (vectors left null)
    python -m app.local_tests.drupal_extraction_test.run news --include-unpublished --no-embed
"""

from __future__ import annotations

import json
import re
import sys
import time
import traceback
from pathlib import Path

# --- make the repo importable and keep Windows stdout from choking on text ---
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
    pass

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return slug or "record"


def _resolve_bundles(argv: list[str]) -> tuple[str, ...]:
    from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES

    return tuple(argv) if argv else DEFAULT_BUNDLES


def _record_slug(record) -> str:
    base = _slugify(record.title or record.uuid or "record")[:80]
    return f"{record.nid}_{base}" if record.nid is not None else base


def _preview(text: str, limit: int) -> str:
    snippet = (text or "").strip()
    if len(snippet) > limit:
        return snippet[:limit] + f"\n\n… [+{len(snippet) - limit} more chars]"
    return snippet


# --------------------------------------------------------------------------- #
# Per-record report writers — each writes one categorised file.
# --------------------------------------------------------------------------- #

def _write_summary(out_dir: Path, record, chunks, elapsed: float) -> dict:
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    child_tokens = [c.token_count for c in children]

    stats = {
        "bundle": record.bundle,
        "title": record.title,
        "url": record.url,
        "uuid": record.uuid,
        "nid": record.nid,
        "elapsed_seconds": round(elapsed, 2),
        "title_chars": len(record.title or ""),
        "body_chars": len(record.body or ""),
        "text_chars": len(record.to_text()),
        "chunks_total": len(chunks),
        "parent_chunks": len(parents),
        "child_chunks": len(children),
        "child_token_min": min(child_tokens) if child_tokens else 0,
        "child_token_max": max(child_tokens) if child_tokens else 0,
        "child_token_avg": sum(child_tokens) // len(child_tokens) if child_tokens else 0,
    }
    (out_dir / "00_summary.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        f"DRUPAL EXTRACTION SUMMARY — {record.bundle} · {record.title or record.uuid}",
        "=" * 78,
        f"  elapsed            : {stats['elapsed_seconds']}s",
        f"  bundle             : {stats['bundle']}",
        f"  url                : {stats['url'] or '—'}",
        f"  nid / uuid         : {stats['nid']} / {stats['uuid']}",
        "",
        f"  title chars        : {stats['title_chars']:,}",
        f"  body chars         : {stats['body_chars']:,}",
        f"  full text chars    : {stats['text_chars']:,}",
        "",
        f"  chunks (total)     : {stats['chunks_total']}",
        f"  parent chunks      : {stats['parent_chunks']}",
        f"  child chunks       : {stats['child_chunks']}",
        f"  child tokens       : min={stats['child_token_min']} "
        f"max={stats['child_token_max']} avg={stats['child_token_avg']}",
        "",
    ]
    (out_dir / "00_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    return stats


def _write_record(out_dir: Path, record) -> None:
    body = (record.body or "").strip()
    lines = [
        f"# Record — {record.title or record.uuid}",
        "",
        f"- bundle: `{record.bundle}`",
        f"- url: {record.url or '—'}",
        f"- nid / uuid: {record.nid} / {record.uuid}",
        f"- created: {record.created or '—'}",
        f"- changed: {record.changed or '—'}",
        "",
        "## Title",
        "",
        record.title or "_(no title)_",
        "",
        "## Body (extracted text)",
        "",
        body if body else "_(no body text)_",
        "",
    ]
    (out_dir / "01_record.md").write_text("\n".join(lines), encoding="utf-8")


def _write_chunks(out_dir: Path, record, chunks) -> None:
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    lines = [
        f"# Chunking (chunk_drupal_record) — {record.title or record.uuid}",
        "",
        f"- parents: **{len(parents)}**",
        f"- children: **{len(children)}**",
        "",
        "---",
        "",
        "## Parent chunks",
        "",
    ]
    if not parents:
        lines += ["_(no parent chunks — single-child sections stand alone)_", ""]
    for c in parents:
        lines.append(
            f"### Parent · section={c.section_heading!r} · type={c.section_type or '—'} "
            f"· {c.token_count} tok"
        )
        lines.append("")
        lines.append(_preview(c.text, 1200))
        lines.append("")
    lines += ["---", "", "## Child chunks", ""]
    for c in children:
        lines.append(
            f"### Child {c.chunk_index} · section={c.section_heading!r} "
            f"· type={c.section_type or '—'} · parent={c.parent_chunk_id} "
            f"· {c.token_count} tok"
        )
        lines.append("")
        lines.append(_preview(c.text, 800))
        lines.append("")
    (out_dir / "02_chunks.md").write_text("\n".join(lines), encoding="utf-8")


def _canonical_metadata(record) -> dict:
    """The CanonicalDocument fields ``from_drupal_record`` derives — i.e. exactly
    what feeds ``chunk_canonical`` and lands in chunk payloads. Best-effort."""
    from app.ingestion.canonical import from_drupal_record

    try:
        doc = from_drupal_record(record)
    except Exception as exc:  # pragma: no cover - defensive
        return {"_error": f"{type(exc).__name__}: {exc}"}
    return {
        "document_id": doc.document_id,
        "source_type": doc.source_type,
        "title": doc.title,
        "source_url": doc.source_url,
        "article_uuid": doc.article_uuid,
        "tags": doc.tags,
        "categories": doc.categories,
        "authors": doc.authors,
        "language": doc.language,
        "tenant_id": doc.tenant_id,
        "acl": doc.acl,
        "published_at": doc.published_at,
        "doc_version": doc.doc_version,
        "is_current": doc.is_current,
        "content_hash": doc.content_hash,
        "extra": doc.extra,
    }


def _write_metadata(out_dir: Path, record) -> dict:
    record_meta = record.to_metadata()
    canonical_meta = _canonical_metadata(record)
    payload = {
        "bundle": record.bundle,
        "record": record_meta,
        "canonical": canonical_meta,
    }
    (out_dir / "03_metadata.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    def _cell(v) -> str:
        if v is None or v == "" or v == [] or v == {}:
            return "—"
        return str(v).replace("|", r"\|").replace("\n", " ")

    lines = [
        f"# Metadata — {record.title or record.uuid}",
        "",
        "## Record metadata (Drupal JSON:API)",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key in sorted(record_meta):
        lines.append(f"| {key} | {_cell(record_meta[key])} |")
    lines.append("")

    lines += ["## Canonical metadata (chunking input)", ""]
    if canonical_meta.get("_error"):
        lines += [f"_Could not build canonical document: {canonical_meta['_error']}_", ""]
    else:
        lines += ["| field | value |", "| --- | --- |"]
        for key in (
            "document_id", "source_type", "title", "source_url", "article_uuid",
            "tags", "categories", "authors", "language", "tenant_id", "acl",
            "published_at", "doc_version", "is_current", "content_hash", "extra",
        ):
            lines.append(f"| {key} | {_cell(canonical_meta.get(key))} |")
        lines.append("")

    (out_dir / "03_metadata.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def _write_full_text(out_dir: Path, record) -> None:
    (out_dir / "full_text.md").write_text(
        f"# Full record text — {record.title or record.uuid}\n\n{record.to_text()}\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# Per-record driver
# --------------------------------------------------------------------------- #

def _process_one(record, *, embed: bool = True) -> dict:
    from app.ingestion.chunker import chunk_drupal_record

    out_dir = RESULTS / _slugify(record.bundle) / _record_slug(record)
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = out_dir.relative_to(RESULTS).as_posix()
    label = record.title or record.uuid or "(untitled)"

    print(f"\n• {record.bundle} · {label}")
    start = time.perf_counter()
    try:
        chunks = chunk_drupal_record(record)
    except Exception as exc:  # one bad record must not sink the whole run
        elapsed = time.perf_counter() - start
        (out_dir / "ERROR.txt").write_text(
            f"Chunking failed for {record.bundle} · {label}\n\n"
            f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}\n",
            encoding="utf-8",
        )
        print(f"  ✗ FAILED: {type(exc).__name__}: {exc}")
        return {
            "bundle": record.bundle, "title": record.title,
            "result_dir": rel, "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(elapsed, 2),
        }

    elapsed = time.perf_counter() - start
    stats = _write_summary(out_dir, record, chunks, elapsed)
    _write_record(out_dir, record)
    _write_chunks(out_dir, record, chunks)
    _write_metadata(out_dir, record)
    _write_full_text(out_dir, record)
    stats["result_dir"] = rel

    print(
        f"  ✓ {stats['text_chars']:,} chars, "
        f"{stats['child_chunks']} child chunks, "
        f"{stats['parent_chunks']} parents · {stats['elapsed_seconds']}s "
        f"-> {rel}"
    )
    return stats


def _write_index(all_stats: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "_index.json").write_text(
        json.dumps(all_stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ok = [s for s in all_stats if "error" not in s]
    failed = [s for s in all_stats if "error" in s]

    lines = [
        "# Drupal extraction test — run index",
        "",
        f"- records processed: **{len(all_stats)}** "
        f"({len(ok)} ok, {len(failed)} failed)",
        f"- total child chunks: **{sum(s.get('child_chunks', 0) for s in ok)}**",
        "",
        "| bundle | title | chunks | child | sec | result |",
        "| ------ | ----- | -----: | ----: | --: | ------ |",
    ]
    for s in all_stats:
        title = (s.get("title") or "—").replace("|", r"\|")
        rel = s.get("result_dir", "")
        if "error" in s:
            lines.append(
                f"| {s['bundle']} | {title} | — | — "
                f"| {s.get('elapsed_seconds', '?')} | ⚠ {s['error']} |"
            )
            continue
        lines.append(
            f"| {s['bundle']} | {title} | {s['chunks_total']} | {s['child_chunks']} "
            f"| {s['elapsed_seconds']} | [{rel}/](./{rel}/) |"
        )
    (RESULTS / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    embed = "--no-embed" not in argv
    published_only = "--include-unpublished" not in argv

    limit: int | None = None
    positional: list[str] = []
    i = 0
    flags = {"--no-embed", "--include-unpublished"}
    while i < len(argv):
        arg = argv[i]
        if arg == "--limit":
            i += 1
            limit = int(argv[i]) if i < len(argv) else None
        elif arg.startswith("--limit="):
            limit = int(arg.split("=", 1)[1])
        elif arg in flags:
            pass
        elif arg.startswith("--"):
            print(f"  ! ignoring unknown flag: {arg}")
        else:
            positional.append(arg)
        i += 1

    bundles = _resolve_bundles(positional)

    print(f"Running Drupal extraction flow over {len(bundles)} bundle(s)")
    print(f"  bundles  : {', '.join(bundles)}")
    print(f"  results  : {RESULTS}")
    print(f"  limit    : {limit if limit is not None else 'none (all records)'}")
    print(f"  published: {'published only' if published_only else 'incl. unpublished'}")
    print(f"  embed    : {'on' if embed else 'off (--no-embed)'}")

    from app.ingestion.extractors.drupal_extractor import iter_records

    run_start = time.perf_counter()
    all_stats: list[dict] = []
    for bundle in bundles:
        count = 0
        for record in iter_records((bundle,), published_only=published_only):
            if limit is not None and count >= limit:
                break
            all_stats.append(_process_one(record, embed=embed))
            count += 1
    _write_index(all_stats)

    if not all_stats:
        print("\nNo records fetched. Check the bundle name(s) and DRUPAL_JSONAPI_BASE.")
        return 1

    ok = sum(1 for s in all_stats if "error" not in s)
    print(
        f"\nDone in {time.perf_counter() - run_start:.1f}s — "
        f"{ok}/{len(all_stats)} ok. See {RESULTS / '_index.md'}"
    )
    return 0 if ok == len(all_stats) else 2


if __name__ == "__main__":
    raise SystemExit(main())
