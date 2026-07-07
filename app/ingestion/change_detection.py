from __future__ import annotations

import fnmatch
import hashlib
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Iterator

from app.config import get_settings
from app.ingestion import state
from app.ingestion.state import StateRecord

logger = logging.getLogger(__name__)


class ChangeStatus(str, Enum):
    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class ChangeRecord:

    status: ChangeStatus
    document_id: str
    source_type: str
    source_key: str
    fingerprint: str = ""
    bundle: str | None = None
    changed_mark: int | None = None
    prior: StateRecord | None = None
    payload: Any = None
    filename: str | None = None

    @property
    def is_actionable(self) -> bool:
        return self.status in (ChangeStatus.NEW, ChangeStatus.CHANGED, ChangeStatus.DELETED)


def content_changed(record: ChangeRecord, content_hash: str) -> bool:
    if record.prior is None:
        return True
    return record.prior.content_hash != content_hash


def next_version(record: ChangeRecord) -> int:
    return record.prior.doc_version + 1 if record.prior else 1


def _parse_roots(raw: str | None) -> list[Path]:
    if not raw:
        return []
    roots: list[Path] = []
    for part in raw.split(os.pathsep):
        part = part.strip()
        if not part:
            continue
        path = Path(part)
        if path.is_dir():
            roots.append(path)
        else:
            logger.warning("PDF source dir does not exist, skipping: %s", part)
    return roots


def _parse_globs(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [g.strip() for g in re.split(r"[,\n]", raw) if g.strip()]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return slug or "document"


def _document_id_for(rel_path: str) -> str:
    return _slugify(os.path.splitext(rel_path)[0])


def _is_ignored(rel_posix: str, ignore_globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_posix, pat) for pat in ignore_globs)


def _iter_pdfs(root: Path, ignore_globs: list[str]) -> Iterator[tuple[Path, str]]:
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        kept: list[str] = []
        for name in dirnames:
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            rel_posix = rel.replace(os.sep, "/")
            if _is_ignored(rel_posix, ignore_globs) or _is_ignored(f"{rel_posix}/", ignore_globs):
                logger.debug("Ignoring directory: %s", rel_posix)
            else:
                kept.append(name)
        dirnames[:] = kept

        for name in filenames:
            if not name.lower().endswith(".pdf"):
                continue
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            rel_posix = rel.replace(os.sep, "/")
            if _is_ignored(rel_posix, ignore_globs):
                continue
            yield Path(dirpath) / name, rel_posix


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_file_changes(
    roots: list[Path] | None = None,
    ignore_globs: list[str] | None = None,
) -> Iterator[ChangeRecord]:
    settings = get_settings()
    configured = settings.pdf_source_dirs or settings.pdf_source_path
    roots = roots if roots is not None else _parse_roots(configured)
    ignore_globs = (
        ignore_globs if ignore_globs is not None else _parse_globs(settings.pdf_ignore_globs)
    )
    if not roots:
        logger.warning("No PDF source dirs configured (pdf_source_dirs); nothing to scan.")
        return

    prior = state.load("pdf")
    seen: set[str] = set()

    for root in roots:
        for path, rel_posix in _iter_pdfs(root, ignore_globs):
            document_id = _document_id_for(rel_posix)
            if document_id in seen:
                logger.warning(
                    "Duplicate document id %r (%s) — keeping first, skipping this one.",
                    document_id, path,
                )
                continue
            seen.add(document_id)

            try:
                data = path.read_bytes()
            except OSError:
                logger.exception("Could not read PDF, skipping: %s", path)
                continue
            fingerprint = _sha256(data)
            prev = prior.get(document_id)

            if prev is None:
                status = ChangeStatus.NEW
            elif prev.fingerprint != fingerprint:
                status = ChangeStatus.CHANGED
            else:
                status = ChangeStatus.UNCHANGED

            yield ChangeRecord(
                status=status,
                document_id=document_id,
                source_type="pdf",
                source_key=str(path),
                fingerprint=fingerprint,
                prior=prev,
                payload=None if status is ChangeStatus.UNCHANGED else data,
                filename=path.name,
            )

    for document_id, record in prior.items():
        if document_id not in seen:
            yield ChangeRecord(
                status=ChangeStatus.DELETED,
                document_id=document_id,
                source_type="pdf",
                source_key=record.source_key,
                prior=record,
            )


def _to_unix(changed: str | None) -> int | None:
    if not changed:
        return None
    try:
        return int(datetime.fromisoformat(changed.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def detect_drupal_changes(
    bundles: Iterable[str] | None = None,
    *,
    published_only: bool = True,
    reconcile_deletes: bool = False,
) -> Iterator[ChangeRecord]:
    from app.ingestion.extractors.drupal_extractor import (
        DEFAULT_BLOCKS,
        DEFAULT_BUNDLES,
        DEFAULT_TAXONOMIES,
        _build_session,
        iter_bundle_records,
        iter_node_uuids,
    )

    settings = get_settings()
    # "website" is the canonical source_type for Drupal content; "article" rows
    # may remain from before the rename (until the migration script runs), so
    # load both to keep change detection incremental across the transition.
    prior_all = {**state.load("article"), **state.load("website")}
    prior_pdf_all = state.load("pdf_attachment")
    # Per-run dedup so an in-body PDF linked from several records ingests once.
    seen_pdf: set[str] = set()

    # A "source" is (entity_type, bundle, incremental). Node bundles support the
    # changed-since high-water mark; the small taxonomy/block sets are fetched in
    # full and change-detected purely on their fingerprint. An explicit
    # ``bundles`` argument is treated as node bundles (preserves --bundle).
    if bundles is not None:
        sources = [("node", b, True) for b in bundles]
    else:
        sources = (
            [("node", b, True) for b in DEFAULT_BUNDLES]
            + [("taxonomy_term", b, False) for b in DEFAULT_TAXONOMIES]
            + [("block_content", b, False) for b in DEFAULT_BLOCKS]
        )

    session = _build_session(settings.drupal_max_retries)
    try:
        for entity_type, bundle, incremental in sources:
            prior = {k: v for k, v in prior_all.items() if v.bundle == bundle}
            high = (
                max(
                    (v.changed_mark for v in prior.values() if v.changed_mark is not None),
                    default=None,
                )
                if incremental
                else None
            )
            # Live document UUIDs yielded this run. For full-fetch sources this is
            # the complete live set, used for delete reconciliation below.
            live_uuids: set[str] = set()

            try:
                for record in iter_bundle_records(
                    session,
                    bundle,
                    entity_type=entity_type,
                    published_only=published_only,
                    changed_since=high,
                ):
                    uuid = record.uuid
                    if not uuid:
                        continue

                    # Drop boilerplate custom blocks (Search box, footer strips)
                    # that carry neither substantial text nor a PDF to harvest.
                    if (
                        entity_type == "block_content"
                        and len(record.body.strip()) < settings.drupal_block_min_chars
                        and not record.files
                    ):
                        continue

                    live_uuids.add(uuid)
                    fingerprint = record.changed or ""
                    prev = prior.get(uuid)

                    if prev is None:
                        status = ChangeStatus.NEW
                    elif prev.fingerprint != fingerprint:
                        status = ChangeStatus.CHANGED
                    else:
                        status = ChangeStatus.UNCHANGED

                    yield ChangeRecord(
                        status=status,
                        document_id=uuid,
                        source_type="website",
                        source_key=record.source,
                        fingerprint=fingerprint,
                        bundle=bundle,
                        changed_mark=_to_unix(record.changed),
                        prior=prev,
                        payload=None if status is ChangeStatus.UNCHANGED else record,
                    )

                    # Each attached PDF becomes its own document. Real file--file
                    # attachments are fingerprinted on the node's changed mark
                    # (re-fetched when the node changes); in-body PDF links are
                    # fingerprinted on their URL so the same PDF, which may be
                    # linked from several nodes, ingests exactly once.
                    for file in record.files:
                        if not file.uuid or file.uuid in seen_pdf:
                            continue
                        seen_pdf.add(file.uuid)
                        a_fingerprint = (
                            f"inbody:{file.url}"
                            if file.origin == "inbody"
                            else fingerprint
                        )
                        a_prev = prior_pdf_all.get(file.uuid)
                        if a_prev is None:
                            a_status = ChangeStatus.NEW
                        elif a_prev.fingerprint != a_fingerprint:
                            a_status = ChangeStatus.CHANGED
                        else:
                            a_status = ChangeStatus.UNCHANGED
                        yield ChangeRecord(
                            status=a_status,
                            document_id=file.uuid,
                            source_type="pdf_attachment",
                            source_key=file.url,
                            fingerprint=a_fingerprint,
                            bundle=bundle,
                            changed_mark=_to_unix(record.changed),
                            prior=a_prev,
                            payload=None if a_status is ChangeStatus.UNCHANGED else (record, file),
                            filename=file.filename,
                        )
            except Exception:
                logger.exception(
                    "Drupal fetch failed for %s/%s; skipping bundle.", entity_type, bundle
                )
                continue

            # Delete reconciliation. Node bundles are crawled incrementally, so
            # the changed set doesn't reveal what is still live — enumerate their
            # UUIDs separately. Taxonomy/block sets are fetched in full every run,
            # so the documents we just yielded ARE the live set.
            if reconcile_deletes and prior:
                if incremental:
                    try:
                        live = set(
                            iter_node_uuids(
                                session, bundle,
                                entity_type=entity_type,
                                published_only=published_only,
                            )
                        )
                    except Exception:
                        logger.exception(
                            "Reconcile enumeration failed for %s/%s; skipping deletes.",
                            entity_type, bundle,
                        )
                        continue
                else:
                    live = live_uuids
                for uuid, record in prior.items():
                    if uuid not in live:
                        yield ChangeRecord(
                            status=ChangeStatus.DELETED,
                            document_id=uuid,
                            source_type="website",
                            source_key=record.source_key,
                            bundle=bundle,
                            prior=record,
                        )
    finally:
        session.close()
