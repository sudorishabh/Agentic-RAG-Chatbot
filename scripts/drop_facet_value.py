"""Remove one stale value from a list facet on existing Qdrant payloads.

Payload-only, like ``scripts.backfill_edition_and_titles``: nothing is
re-extracted, re-chunked or re-embedded, and no vector is touched. ``set_payload``
rewrites the one list on the affected points; when the list would become empty
the key is deleted, because ``build_payload`` never writes an empty list.

Why it exists: ``field_show_on_theme_page`` (a boolean CMS switch on the project
bundles) matched the theme hint and its stringified value reached 5,598 points
as the category ``"True"``. Ingestion no longer produces it
(``canonical._matching`` refuses boolean values), but a point is only rewritten
when its document is rebuilt, and the corpus-wide rebuild those points are
already queued for (they sit on an older pipeline version) is a much larger
operation. This removes the value now and leaves everything else exactly as it
was; the eventual rebuild produces the same clean list.

Default is a dry run that writes nothing.

    python -m scripts.drop_facet_value                       # categories, "True"
    python -m scripts.drop_facet_value --field tags --value X --apply
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from typing import Any, Iterator

BATCH = 500


def without_value(values: list[Any] | None, value: str) -> list[Any]:
    """The list minus every occurrence of ``value``, order preserved."""
    return [v for v in (values or []) if v != value]


def affected_points(client: Any, collection: str, field: str, value: str) -> Iterator[Any]:
    """Every point whose ``field`` list contains ``value``, payload only."""
    from qdrant_client import models as qm

    flt = qm.Filter(must=[qm.FieldCondition(key=field, match=qm.MatchValue(value=value))])
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection, scroll_filter=flt, limit=BATCH,
            with_payload=[field, "document_id"], with_vectors=False, offset=offset,
        )
        yield from points
        if offset is None:
            break


def plan(client: Any, collection: str, field: str, value: str) -> dict[tuple, list]:
    """``{resulting list: [point ids]}`` — the writes grouped by their outcome."""
    groups: dict[tuple, list] = defaultdict(list)
    for point in affected_points(client, collection, field, value):
        remaining = without_value((point.payload or {}).get(field), value)
        groups[tuple(remaining)].append(point.id)
    return groups


def apply(client: Any, collection: str, field: str, groups: dict[tuple, list]) -> int:
    """Rewrite the facet on every planned point. Returns points written."""
    written = 0
    for remaining, ids in groups.items():
        for start in range(0, len(ids), BATCH):
            batch = ids[start:start + BATCH]
            if remaining:
                client.set_payload(collection_name=collection,
                                   payload={field: list(remaining)}, points=batch)
            else:
                client.delete_payload(collection_name=collection, keys=[field], points=batch)
            written += len(batch)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--field", default="categories", help="list facet on the payload")
    parser.add_argument("--value", default="True", help="the value to remove")
    parser.add_argument("--apply", action="store_true", help="write; default is a dry run")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from qdrant_client import models as qm

    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    flt = qm.Filter(must=[qm.FieldCondition(key=args.field, match=qm.MatchValue(value=args.value))])

    total_before = client.count(collection_name=collection, exact=True).count
    groups = plan(client, collection, args.field, args.value)
    points = sum(len(ids) for ids in groups.values())
    print(f"collection {collection!r}: {total_before} points; {points} carry "
          f"{args.field} = {args.value!r} in {len(groups)} distinct resulting list(s)")
    for remaining, ids in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f"  {len(ids):>6} points -> {list(remaining) or '(key removed)'}")
    if not args.apply:
        print("dry run: nothing written. Re-run with --apply.")
        return 0

    written = apply(client, collection, args.field, groups)
    total_after = client.count(collection_name=collection, exact=True).count
    left = client.count(collection_name=collection, count_filter=flt, exact=True).count
    print(f"applied: {written} points rewritten; points {total_before} -> {total_after} "
          f"(must be identical); points still carrying the value: {left}")
    return 0 if total_after == total_before and left == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
