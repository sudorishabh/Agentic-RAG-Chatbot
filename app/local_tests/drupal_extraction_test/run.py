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

import re
import sys
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
