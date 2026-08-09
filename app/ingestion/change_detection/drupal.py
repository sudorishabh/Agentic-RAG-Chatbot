"""Drupal change detection: incremental node crawl (changed-since high-water
mark), full-fetch block sources, attached-PDF fan-out, and optional delete
reconciliation."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, Iterator

from app.catalog import dead_links, state
from app.config import get_settings
from app.ingestion.change_detection.base import (
    ChangeRecord,
    ChangeStatus,
    _parse_bundle_spec,
    compute_status,
)

logger = logging.getLogger(__name__)


def _to_unix(changed: str | None) -> int | None:
    if not changed:
        return None
    try:
        return int(datetime.fromisoformat(changed.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def _load_dead_links() -> dict[str, dead_links.DeadLink]:
    """Attachments already known to answer with a client error.

    Falls open to an empty skip list: without it the crawl re-downloads a
    handful of dead URLs — exactly what it did before the markers existed, and
    no reason to abandon a sweep over.
    """
    try:
        dead_links.ensure_table()
        return dead_links.load()
    except Exception:
        logger.warning(
            "Could not load dead attachment links; retrying them all.", exc_info=True
        )
        return {}


def detect_drupal_changes(
    bundles: Iterable[str] | None = None,
    *,
    published_only: bool = True,
    reconcile_deletes: bool = False,
) -> Iterator[ChangeRecord]:
    from app.ingestion.extractors.drupal_extractor import (
        DEFAULT_BLOCKS,
        DEFAULT_BUNDLES,
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
    dead_pdf = _load_dead_links()
    # Per-run dedup so an in-body PDF linked from several records ingests once.
    seen_pdf: set[str] = set()
    suppressed = 0

    # A "source" is (entity_type, bundle, incremental). Node bundles support the
    # changed-since high-water mark; the small block set is fetched in full and
    # change-detected purely on its fingerprint. An explicit ``bundles`` argument
    # is treated as node bundles (preserves --bundle); an "entity_type:bundle"
    # spec (e.g. block_content:basic) scopes others.
    if bundles is not None:
        sources = [_parse_bundle_spec(spec) for spec in bundles]
    else:
        sources = [("node", b, True) for b in DEFAULT_BUNDLES] + [
            ("block_content", b, False) for b in DEFAULT_BLOCKS
        ]

    # Always crawl oldest-first: the MAX(changed_mark) high-water then only
    # ever covers documents that were actually processed, so it acts as a
    # resume cursor. Newest-first would advance the mark past unprocessed
    # older documents whenever a run is capped or interrupted, stranding them
    # behind the incremental filter forever.
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
                    ascending=True,
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
                    status = compute_status(prev, fingerprint)

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
                        entity_type=entity_type,
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
                        # An in-body uuid already *is* that URL fingerprint
                        # (`inbody:<sha1 of the absolute URL>`, see
                        # drupal_extractor._extract_inbody_pdfs), so reuse it
                        # instead of the raw URL: percent-encoded PDF paths run
                        # well past the catalog's VARCHAR(128) fingerprint
                        # column, and the write failed with MySQL 1406.
                        a_fingerprint = (
                            file.uuid if file.origin == "inbody" else fingerprint
                        )
                        # A URL the site answered 4xx for stays out of the run
                        # entirely while the fingerprint that failed is still
                        # current: yielding it would only buy the same 404 and
                        # the same skip, once an hour, forever.
                        marker = dead_pdf.get(file.uuid)
                        if marker is not None and marker.fingerprint == a_fingerprint:
                            suppressed += 1
                            continue
                        a_prev = prior_pdf_all.get(file.uuid)
                        a_status = compute_status(a_prev, a_fingerprint)
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
                            entity_type=entity_type,
                        )
    finally:
        session.close()
        if suppressed:
            logger.info(
                "Skipped %d attachment(s) the site last answered with a client "
                "error; clear their dead-link markers to retry.", suppressed
            )
