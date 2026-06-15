"""Change detection — decide *what* to (re)ingest before paying to extract it.

Everything downstream of this module is expensive: PDF extraction runs Docling +
Azure OCR + vision captioning, and every source is embedded with Azure. So before
any of that, we classify each discovered document against the manifest
(:mod:`app.ingestion.state`) into one of:

* **NEW**       — not seen before → extract + index.
* **CHANGED**   — seen, but its cheap fingerprint moved → re-extract + re-index.
* **UNCHANGED** — fingerprint matches → skip entirely (no extraction).
* **DELETED**   — in the manifest but gone from the source → purge from Qdrant.

Two tiers of comparison keep us honest *and* cheap:

1. **Pre-extraction (this module).** A fingerprint that needs no extraction:
   PDFs use a raw-bytes SHA-256 (immune to OneDrive/copy mtime churn); Drupal
   nodes use their ``changed`` timestamp. This is where the savings come from.
2. **Post-extraction (the runner, via** :func:`content_changed` **).** Compare the
   canonical ``content_hash``. Equal → the bytes moved but the *content* didn't
   (re-saved file, metadata-only touch): refresh the fingerprint, skip re-embed.
   Different → bump ``doc_version`` and re-index.

This module only *discovers and classifies*; extraction, indexing, and Qdrant
deletes live in the ingest runner.
"""

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
    """The verdict for one document, plus what the runner needs to act on it.

    ``payload`` carries the already-loaded source for actionable records so the
    runner never re-reads it — PDF bytes for NEW/CHANGED files, a ``DrupalRecord``
    for NEW/CHANGED nodes. It is ``None`` for UNCHANGED/DELETED.
    """

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
        """NEW/CHANGED need (re)extraction; DELETED needs a purge; UNCHANGED is a no-op."""
        return self.status in (ChangeStatus.NEW, ChangeStatus.CHANGED, ChangeStatus.DELETED)


def content_changed(record: ChangeRecord, content_hash: str) -> bool:
    """Tier-2 check: did the *content* actually change vs. what we last indexed?

    Always ``True`` for a NEW document; otherwise compares the post-extraction
    canonical hash against the stored one.
    """
    if record.prior is None:
        return True
    return record.prior.content_hash != content_hash


def next_version(record: ChangeRecord) -> int:
    """Version to stamp on a (re)indexed document: 1 for new, prior + 1 for changed."""
    return record.prior.doc_version + 1 if record.prior else 1


# --------------------------------------------------------------------------- #
# Settings parsing
# --------------------------------------------------------------------------- #
def _parse_roots(raw: str | None) -> list[Path]:
    """Split the OS-path-separated ``pdf_source_dirs`` into existing directories."""
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
    """Split comma-/newline-separated ignore globs into a clean list."""
    if not raw:
        return []
    return [g.strip() for g in re.split(r"[,\n]", raw) if g.strip()]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return slug or "document"


def _document_id_for(rel_path: str) -> str:
    """Stable, tree-unique id for a PDF from its path relative to its root.

    Uses the full relative path (sans extension) so ``a/report.pdf`` and
    ``b/report.pdf`` don't collide — unlike a bare filename slug.
    """
    return _slugify(os.path.splitext(rel_path)[0])


def _is_ignored(rel_posix: str, ignore_globs: list[str]) -> bool:
    """True if the relative (``/``-separated) path matches any ignore glob.

    A pattern is matched both against the full path and against the bare path so
    ``archive/**`` skips a top-level ``archive`` tree and ``**/_drafts/**`` skips
    a ``_drafts`` folder at any depth.
    """
    return any(fnmatch.fnmatch(rel_posix, pat) for pat in ignore_globs)


# --------------------------------------------------------------------------- #
# PDF folder source
# --------------------------------------------------------------------------- #
def _iter_pdfs(root: Path, ignore_globs: list[str]) -> Iterator[tuple[Path, str]]:
    """Yield ``(absolute_path, relative_posix_path)`` for every non-ignored PDF
    under ``root``, descending into nested folders. Ignored *directories* are
    pruned so we never walk into them."""
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        # Prune ignored subdirectories in place so os.walk skips them entirely.
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
    """Walk the PDF source roots and classify every PDF against the manifest.

    Each file is read **once**: the bytes feed the SHA-256 fingerprint and, for
    NEW/CHANGED files, ride along on the :class:`ChangeRecord` as ``payload`` so
    the runner extracts without a second read. UNCHANGED files yield a verdict but
    no payload. After the walk, any manifest entry not seen on disk is emitted as
    DELETED.
    """
    settings = get_settings()
    roots = roots if roots is not None else _parse_roots(settings.pdf_source_dirs)
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


# --------------------------------------------------------------------------- #
# Drupal JSON:API source
# --------------------------------------------------------------------------- #
def _to_unix(changed: str | None) -> int | None:
    """Parse a Drupal ``changed`` timestamp (ISO 8601) into a unix int.

    Stored as ``changed_mark`` and used as the incremental high-water value the
    next crawl filters on. Returns ``None`` if the timestamp is missing/unparseable.
    """
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
    """Crawl the Drupal JSON:API incrementally and classify each node.

    Each bundle is fetched from its stored high-water ``changed`` mark onward
    (``filter[changed] > high_water``), so a normal run only pulls nodes modified
    since last time — everything returned is therefore NEW or CHANGED. The node's
    ``changed`` timestamp is both the fingerprint and the high-water value.

    Incremental crawls can't reveal deletions, so when ``reconcile_deletes`` is
    set the bundle's full set of live UUIDs is enumerated cheaply and any manifest
    entry no longer present (deleted or unpublished) is emitted as DELETED.
    """
    from app.ingestion.extractors.drupal_extractor import (
        DEFAULT_BUNDLES,
        _build_session,
        iter_bundle_records,
        iter_node_uuids,
    )

    settings = get_settings()
    bundles = tuple(bundles) if bundles is not None else DEFAULT_BUNDLES
    prior_all = state.load("article")

    session = _build_session(settings.drupal_max_retries)
    try:
        for bundle in bundles:
            prior = {k: v for k, v in prior_all.items() if v.bundle == bundle}
            high = max(
                (v.changed_mark for v in prior.values() if v.changed_mark is not None),
                default=None,
            )

            for record in iter_bundle_records(
                session, bundle, published_only=published_only, changed_since=high
            ):
                uuid = record.uuid
                if not uuid:
                    continue
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
                    source_type="article",
                    source_key=record.source,
                    fingerprint=fingerprint,
                    bundle=bundle,
                    changed_mark=_to_unix(record.changed),
                    prior=prev,
                    payload=None if status is ChangeStatus.UNCHANGED else record,
                )

            if reconcile_deletes and prior:
                try:
                    live = set(iter_node_uuids(session, bundle, published_only=published_only))
                except Exception:
                    logger.exception(
                        "Reconcile enumeration failed for node/%s; skipping deletes.", bundle
                    )
                    continue
                for uuid, record in prior.items():
                    if uuid not in live:
                        yield ChangeRecord(
                            status=ChangeStatus.DELETED,
                            document_id=uuid,
                            source_type="article",
                            source_key=record.source_key,
                            bundle=bundle,
                            prior=record,
                        )
    finally:
        session.close()
