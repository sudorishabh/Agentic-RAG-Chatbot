"""Filesystem PDF change detection: walk the configured source dirs, pre-filter
on size+mtime, and fingerprint on SHA-256 only when that pre-filter can't
rule out a change."""
from __future__ import annotations

import fnmatch
import hashlib
import logging
import os
from pathlib import Path
from typing import Iterator

from app.catalog import state
from app.config import get_settings
from app.ingestion.change_detection.base import ChangeRecord, ChangeStatus, compute_status
from app.ingestion.textutil import slugify

logger = logging.getLogger(__name__)


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
    import re

    return [g.strip() for g in re.split(r"[,\n]", raw) if g.strip()]


def _document_id_for(rel_path: str) -> str:
    return slugify(os.path.splitext(rel_path)[0])


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
                st = path.stat()
            except OSError:
                logger.exception("Could not stat PDF, skipping: %s", path)
                continue
            size, mtime_ns = st.st_size, st.st_mtime_ns
            prev = prior.get(document_id)

            # Cheap pre-filter: an unchanged size + mtime means the content is
            # unchanged, so skip the (expensive) full read + SHA-256 entirely.
            if prev is not None and prev.size == size and prev.mtime_ns == mtime_ns:
                yield ChangeRecord(
                    status=ChangeStatus.UNCHANGED,
                    document_id=document_id,
                    source_type="pdf",
                    source_key=str(path),
                    fingerprint=prev.fingerprint,
                    prior=prev,
                    payload=None,
                    filename=path.name,
                    size=size,
                    mtime_ns=mtime_ns,
                )
                continue

            try:
                data = path.read_bytes()
            except OSError:
                logger.exception("Could not read PDF, skipping: %s", path)
                continue
            fingerprint = _sha256(data)
            status = compute_status(prev, fingerprint)

            yield ChangeRecord(
                status=status,
                document_id=document_id,
                source_type="pdf",
                source_key=str(path),
                fingerprint=fingerprint,
                prior=prev,
                payload=None if status is ChangeStatus.UNCHANGED else data,
                filename=path.name,
                size=size,
                mtime_ns=mtime_ns,
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
