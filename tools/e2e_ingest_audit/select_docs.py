"""Choose 30 freshly published/changed source documents from the live site.

The real crawl walks each bundle oldest-first from its high-water mark. Against
empty state tables that would start in 2017, so selection is done here: the
newest records of every configured source are fetched with the real extractor
(``iter_bundle_records``, newest-first), the raw JSON:API resource behind each
record is kept as source evidence, and a greedy fill picks records until the
document count — one per node plus one per distinct attached PDF, exactly as
change detection will yield them — reaches the target.

The selected records are then fed to the real ``detect_drupal_changes`` by
substituting only the bundle enumeration, so every downstream decision
(status, fingerprint, attachment fan-out, in-body de-duplication, block
filtering) is the pipeline's own.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterator
from unittest import mock

logger = logging.getLogger(__name__)


@dataclass
class Selection:
    records: list[Any] = field(default_factory=list)
    raw_by_uuid: dict[str, dict[str, Any]] = field(default_factory=dict)
    candidates_seen: int = 0
    per_source_fetched: dict[str, int] = field(default_factory=dict)
    expected_documents: int = 0
    expected_attachments: int = 0

    def bundle_specs(self) -> list[str]:
        """The ``--bundle`` specs that reach exactly the selected sources."""
        from app.ingestion.extractors.drupal_extractor import DEFAULT_BLOCKS, DEFAULT_BUNDLES

        wanted = {(r.metadata.get("entity_type", "node"), r.bundle) for r in self.records}
        specs: list[str] = []
        for bundle in DEFAULT_BUNDLES:
            if ("node", bundle) in wanted:
                specs.append(bundle)
        for bundle in DEFAULT_BLOCKS:
            if ("block_content", bundle) in wanted:
                specs.append(f"block_content:{bundle}")
        return specs

    def by_source(self) -> dict[tuple[str, str], list[Any]]:
        out: dict[tuple[str, str], list[Any]] = {}
        for record in self.records:
            key = (record.metadata.get("entity_type", "node"), record.bundle)
            out.setdefault(key, []).append(record)
        for records in out.values():
            records.sort(key=lambda r: (_to_unix(r.changed) or 0, r.nid or 0))
        return out


def _to_unix(changed: str | None) -> int | None:
    if not changed:
        return None
    try:
        return int(datetime.fromisoformat(changed.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def _included_for(node: dict, included: dict[tuple[str, str], dict]) -> list[dict]:
    """The included resources this node references, in relationship order."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for relationship in (node.get("relationships") or {}).values():
        data = relationship.get("data")
        if not data:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            key = (item.get("type"), item.get("id"))
            entity = included.get(key)
            if entity is not None and key not in seen:
                seen.add(key)
                out.append(entity)
    return out


def _block_is_dropped(record: Any, settings: Any) -> bool:
    """The same boilerplate filter change detection applies to custom blocks."""
    return (
        record.metadata.get("entity_type") == "block_content"
        and len(record.body.strip()) < settings.drupal_block_min_chars
        and not record.files
    )


def fetch_candidates(session: Any, per_source: int) -> Selection:
    from app.config import get_settings
    from app.ingestion.extractors import drupal_extractor as dx

    settings = get_settings()
    selection = Selection()
    real_build_record = dx._build_record

    def build_record(node: dict, included: dict, bundle: str, site: str, **kw: Any) -> Any:
        record = real_build_record(node, included, bundle, site, **kw)
        if record.uuid:
            selection.raw_by_uuid[record.uuid] = {
                "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "jsonapi_resource": node,
                "included": _included_for(node, included),
            }
        return record

    sources = [("node", b) for b in dx.DEFAULT_BUNDLES] + [
        ("block_content", b) for b in dx.DEFAULT_BLOCKS
    ]
    candidates: list[Any] = []
    with mock.patch.object(dx, "_build_record", build_record):
        for entity_type, bundle in sources:
            taken = 0
            try:
                stream: Iterator[Any] = dx.iter_bundle_records(
                    session, bundle, entity_type=entity_type,
                    published_only=True, ascending=False,
                )
                for record in stream:
                    if not record.uuid:
                        continue
                    if entity_type != "node":
                        record.metadata.setdefault("entity_type", entity_type)
                    if _block_is_dropped(record, settings):
                        continue
                    candidates.append(record)
                    taken += 1
                    if taken >= per_source:
                        break
                stream.close()
            except Exception:
                logger.exception("Could not sample %s/%s; skipping it.", entity_type, bundle)
            selection.per_source_fetched[f"{entity_type}/{bundle}"] = taken
    selection.candidates_seen = len(candidates)
    selection.records = candidates
    return selection


def choose(selection: Selection, *, target: int, per_bundle_cap: int) -> Selection:
    """Greedy newest-first fill to exactly ``target`` documents.

    A record contributes one document for itself plus one per attached PDF not
    already claimed by an earlier pick (in-body PDFs are de-duplicated per run
    on their URL-derived uuid, exactly as change detection does). Bundle
    diversity comes from a soft per-bundle cap that is relaxed only if the
    target cannot otherwise be met.
    """
    ordered = sorted(
        selection.records,
        key=lambda r: (_to_unix(r.changed) or 0, r.nid or 0),
        reverse=True,
    )
    chosen: list[Any] = []
    claimed_files: set[str] = set()
    total = 0

    def contribution(record: Any) -> tuple[int, set[str]]:
        new_files = {f.uuid for f in record.files if f.uuid and f.uuid not in claimed_files}
        return 1 + len(new_files), new_files

    for cap in (per_bundle_cap, None):
        per_bundle: dict[str, int] = {}
        for record in chosen:
            per_bundle[record.bundle] = per_bundle.get(record.bundle, 0) + 1
        for record in ordered:
            if total >= target:
                break
            if record in chosen:
                continue
            if cap is not None and per_bundle.get(record.bundle, 0) >= cap:
                continue
            count, new_files = contribution(record)
            if total + count > target:
                continue
            chosen.append(record)
            claimed_files |= new_files
            total += count
            per_bundle[record.bundle] = per_bundle.get(record.bundle, 0) + 1
        if total >= target:
            break

    picked = Selection(
        records=chosen,
        raw_by_uuid={r.uuid: selection.raw_by_uuid[r.uuid] for r in chosen if r.uuid in selection.raw_by_uuid},
        candidates_seen=selection.candidates_seen,
        per_source_fetched=selection.per_source_fetched,
        expected_documents=total,
        expected_attachments=len(claimed_files),
    )
    return picked


def substitute_crawl(selection: Selection):
    """A patch that makes the real crawl enumerate only the selected records."""
    from app.ingestion.extractors import drupal_extractor as dx

    by_source = selection.by_source()

    def iter_bundle_records(session: Any, bundle: str, *, entity_type: str = "node", **kw: Any):
        yield from by_source.get((entity_type, bundle), [])

    return mock.patch.object(dx, "iter_bundle_records", iter_bundle_records)
