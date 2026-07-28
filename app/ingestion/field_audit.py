"""Audit which Drupal JSON:API fields the ingestion pipeline keeps or drops.

Samples raw records from every configured source (node bundles, taxonomy
vocabularies, custom blocks) and reports per field: how the extractor
partitions it (body / metadata / core / ignored), which canonical facet the
current substring heuristics route it to (categories / tags / authors — or
nothing, i.e. dropped), the observed fill rate, and relationship target types.
The JSON report is the ground truth for designing explicit per-bundle field
mappings.

Run: python -m app.ingestion.field_audit [--sample N] [--bundle B ...] [--out PATH]
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

import requests

from app.config import get_settings
from app.ingestion.canonical import (
    AUTHOR_HINTS,
    CATEGORY_VOCABULARIES,
    TAG_HINTS,
    THEME_HINTS,
)
from app.ingestion.extractors.drupal_extractor import (
    DEFAULT_BLOCKS,
    DEFAULT_BUNDLES,
    DEFAULT_TAXONOMIES,
    _build_session,
    _iter_pages,
    _partition_attributes,
)

logger = logging.getLogger(__name__)

# Attributes _build_record consumes directly (title/name/info, dates, path,
# internal ids) or that drive filtering (status). Any other non-field_ scalar
# attribute is Drupal plumbing the pipeline ignores by design.
_CONSUMED_ATTRIBUTES = frozenset(
    {
        "title", "name", "info", "created", "changed", "path", "status",
        "drupal_internal__nid", "drupal_internal__tid", "drupal_internal__id",
    }
)

_FACET_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("categories", THEME_HINTS),
    ("tags", TAG_HINTS),
    ("authors", AUTHOR_HINTS),
)


@dataclass
class _FieldStats:
    kind: str  # "attribute" | "relationship"
    seen: int = 0
    partition: str | None = None
    value_types: set[str] = field(default_factory=set)
    targets: set[str] = field(default_factory=set)
    example: str | None = None


def _destinations(field_name: str, targets: set[str] | None = None) -> list[str]:
    """Facets the canonical heuristics would route this field to.

    ``targets`` are a relationship's JSON:API target types. drupal_facets routes
    a reference into a theme vocabulary to categories whatever the field is
    called — including a taxonomy term's ``parent`` — so the audit has to consult
    the target vocabulary, not just the field name."""
    key = field_name.lower()
    dests = [facet for facet, hints in _FACET_HINTS if any(h in key for h in hints)]
    if "categories" not in dests and any(
        target.startswith("taxonomy_term--")
        and target.partition("--")[2] in CATEGORY_VOCABULARIES
        for target in targets or ()
    ):
        dests.append("categories")
    return dests


def _classify_attribute(key: str, value: Any) -> str:
    """Mirror the extractor's body/metadata split for a single attribute."""
    body, meta = _partition_attributes({key: value})
    if meta:
        return "metadata"
    if body:
        return "body"
    return "core" if key in _CONSUMED_ATTRIBUTES else "ignored"


def _example(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("processed") or value.get("value") or value
    return str(value)[:120]


def _observe(node: dict, stats: dict[str, _FieldStats]) -> None:
    for key, value in node.get("attributes", {}).items():
        st = stats.setdefault(key, _FieldStats(kind="attribute"))
        if value in (None, "", [], {}):
            continue
        st.seen += 1
        st.value_types.add(type(value).__name__)
        if st.partition is None:
            st.partition = _classify_attribute(key, value)
        if st.example is None:
            st.example = _example(value)

    for name, rel in node.get("relationships", {}).items():
        # field_* are content relationships; `parent` is the taxonomy tree
        # link; `uid` is the node owner — a possible authorship signal the
        # pipeline currently ignores.
        if not (name.startswith("field_") or name in ("parent", "uid")):
            continue
        data = rel.get("data")
        refs = data if isinstance(data, list) else [data] if data else []
        # Root taxonomy terms carry a placeholder parent ref with id "virtual".
        refs = [r for r in refs if r and r.get("id") != "virtual"]
        st = stats.setdefault(name, _FieldStats(kind="relationship"))
        if refs:
            st.seen += 1
            st.targets.update(r.get("type", "?") for r in refs)


def _field_row(name: str, st: _FieldStats, records: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "field": name,
        "kind": st.kind,
        "fill_rate": round(st.seen / records, 2) if records else 0.0,
    }
    if st.kind == "attribute":
        row["partition"] = st.partition or "empty"
        row["value_types"] = sorted(st.value_types)
        if st.example is not None:
            row["example"] = st.example
    else:
        row["targets"] = sorted(st.targets)

    # "canonical" is where the current heuristics send the field; an empty
    # list means a populated field that never reaches the catalog or payload.
    if st.kind == "relationship":
        if st.targets and st.targets <= {"file--file"}:
            row["canonical"] = ["attachments"]
        else:
            row["canonical"] = _destinations(name, st.targets)
    elif st.partition == "metadata":
        row["canonical"] = _destinations(name)
    return row


def _sample_records(
    session: requests.Session, entity_type: str, bundle: str, sample: int
) -> Iterator[dict]:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    params: dict[str, Any] = {
        "page[limit]": min(sample, settings.drupal_page_size),
        "sort": "-changed",
        "filter[status]": 1,
    }
    url = f"{base}/{entity_type}/{bundle}"
    yielded = 0
    for data, _included in _iter_pages(
        session, url, params, settings.drupal_request_timeout
    ):
        for node in data:
            yield node
            yielded += 1
            if yielded >= sample:
                return


def _audit_source(
    session: requests.Session, entity_type: str, bundle: str, sample: int
) -> dict[str, Any]:
    stats: dict[str, _FieldStats] = {}
    records = 0
    for node in _sample_records(session, entity_type, bundle, sample):
        records += 1
        _observe(node, stats)
    logger.info(
        "Audited %s/%s: %d records, %d fields", entity_type, bundle, records, len(stats)
    )
    return {
        "entity_type": entity_type,
        "bundle": bundle,
        "records_sampled": records,
        "fields": [_field_row(name, st, records) for name, st in sorted(stats.items())],
    }


def build_report(sample: int, bundles: list[str] | None = None) -> dict[str, Any]:
    if bundles:
        sources = [("node", b) for b in bundles]
    else:
        sources = (
            [("node", b) for b in DEFAULT_BUNDLES]
            + [("taxonomy_term", t) for t in DEFAULT_TAXONOMIES]
            + [("block_content", b) for b in DEFAULT_BLOCKS]
        )

    session = _build_session(get_settings().drupal_max_retries)
    audited: list[dict[str, Any]] = []
    try:
        for entity_type, bundle in sources:
            try:
                audited.append(_audit_source(session, entity_type, bundle, sample))
            except requests.RequestException:
                logger.exception("Audit failed for %s/%s; skipping.", entity_type, bundle)
    finally:
        session.close()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sample_per_source": sample,
        "sources": audited,
    }


def _dropped(source: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        f
        for f in source["fields"]
        if "canonical" in f and not f["canonical"] and f["fill_rate"] > 0
    ]


def _print_summary(report: dict[str, Any]) -> None:
    print(
        f"\nAudited {len(report['sources'])} sources "
        f"(up to {report['sample_per_source']} records each)."
    )
    for source in report["sources"]:
        label = f"{source['entity_type']}/{source['bundle']}"
        lost = _dropped(source)
        if not lost:
            print(f"  {label}: no populated metadata fields dropped")
            continue
        names = ", ".join(f"{f['field']} ({f['fill_rate']:.0%})" for f in lost)
        print(f"  {label}: DROPS {names}")


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Audit which Drupal fields the ingestion pipeline keeps or drops."
    )
    parser.add_argument(
        "--sample", type=int, default=50, help="records sampled per source (default: 50)"
    )
    parser.add_argument(
        "--bundle", action="append", help="audit only this node bundle (repeatable)"
    )
    parser.add_argument(
        "--out",
        default="field_audit_report.json",
        help="JSON report path (default: field_audit_report.json)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    report = build_report(args.sample, args.bundle)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    _print_summary(report)
    print(f"\nFull report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
