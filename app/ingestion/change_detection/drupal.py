"""Drupal change detection: incremental node crawl (changed-since high-water
mark), full-fetch block sources, attached-PDF fan-out, and optional delete
reconciliation."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, Iterator, Mapping

from app.catalog import dead_links, retries, state
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


def _load_retry_floors() -> dict[str, int]:
    """The earliest unresolved failure per bundle, as a crawl position.

    Falls open to no floors: without them the crawl behaves exactly as it did
    before they existed — which strands failures, but is no reason to abandon a
    sweep over an unreachable table.
    """
    try:
        retries.ensure_table()
        return retries.floors()
    except Exception:
        logger.warning(
            "Could not load retry floors; failed documents may stay out of "
            "this run's window.", exc_info=True
        )
        return {}


def _deletions_are_plausible(
    entity_type: str, bundle: str, *, catalogued: int, live: int, missing: int
) -> bool:
    """Whether this bundle's live enumeration can be trusted enough to delete by.

    Reconciliation infers deletion from absence, so an enumeration that merely
    came back short is indistinguishable from a bundle that was really emptied.
    What follows is not reversible: the points, the catalog row and every facet
    row hanging off it go, with no tombstone to restore from. A fetch that
    *fails* already skips the bundle; this is for the responses that arrive
    successfully and incomplete — a renamed bundle, a filter that stopped
    matching, a cache serving an empty page, a walk that lost one page of fifty.

    Two rules, both per bundle so one bad source cannot stop the others:

    * a live set that is empty while the catalog is not is never believed —
      whatever emptied a whole bundle at once, it is worth a human look;
    * otherwise the missing share may not reach
      ``ingest_reconcile_max_missing_ratio``, with an absolute allowance of
      ``ingest_reconcile_min_deletions`` so a small bundle can still lose a
      document or two. That allowance sits far below one page of results, so it
      cannot mask the truncation it is guarding against.
    """
    settings = get_settings()
    ratio = missing / catalogued if catalogued else 0.0

    if catalogued and not live:
        reason = "the live enumeration returned nothing at all"
    elif missing >= catalogued * settings.ingest_reconcile_max_missing_ratio and (
        missing > settings.ingest_reconcile_min_deletions
    ):
        reason = (
            f"{ratio:.1%} of the bundle is missing, at or above the "
            f"{settings.ingest_reconcile_max_missing_ratio:.1%} limit"
        )
    else:
        return True

    logger.warning(
        "Refusing to reconcile deletes for %s/%s: %s. Catalogued %d, live %d, "
        "missing %d. No documents were deleted; the rest of the run is "
        "unaffected. Re-check the source, then raise "
        "ingest_reconcile_max_missing_ratio if the drop is real.",
        entity_type, bundle, reason, catalogued, live, missing,
    )
    return False


def _safe_to_delete(uuid: str, bundle: str) -> bool:
    """Whether this candidate is really gone, or just filed somewhere else now.

    The prior snapshot is read once at the start of a run, so it keeps filing a
    document under the bundle it has since left. If the new bundle was crawled
    earlier in this same run the document has already been re-indexed under it,
    and deleting on the strength of the stale snapshot takes a live, freshly
    indexed document straight back out — invisible until the next sweep repairs
    it. One catalog read per candidate settles it.

    A missing row means there is nothing left to protect and the delete goes
    ahead as before. Anything else leaves the document alone, a read that fails
    included: not deleting costs one more sweep, deleting wrongly costs a
    document out of the index until then.

    Only ever removes candidates from a batch the completeness guard has already
    approved, so it cannot loosen that check.
    """
    try:
        current = state.get(uuid)
    except Exception:
        logger.warning(
            "Could not confirm the current bundle of %s; leaving it in place "
            "rather than deleting on a stale read.", uuid, exc_info=True,
        )
        return False

    if current is None:
        return True
    if current.bundle != bundle:
        logger.info(
            "Not deleting %s: it is catalogued under %r now, not %r, so it moved "
            "bundles rather than disappearing.", uuid, current.bundle, bundle,
        )
        return False
    return True


def _searchable_sources(
    sources: list[tuple[str, str, bool]]
) -> list[tuple[str, str, bool]]:
    """Drop every source the searchable crawl must not turn into a document.

    Taxonomy terms are what this exists for. A term is a label a document
    carries, not a document: its name already travels in the payload of every
    content chunk that references it (``categories`` / ``tags``), and that is
    what theme and tag filtering match on. Crawling the term as well records the
    same fact a second time as a near-empty document — most vocabularies carry no
    description at all — and puts it in front of retrieval, where it can be
    returned in place of the content it was only ever meant to label.

    Enforced here, on the single path that reaches chunking and Qdrant, rather
    than by leaving them out of the default list: ``--bundle`` and the ingest API
    both take an arbitrary "entity_type:bundle" spec, so a default list is a
    convention while this is the rule. Metadata is untouched — this drops
    taxonomy *sources*, never the taxonomy references on content records.
    """
    from app.ingestion.extractors.drupal_extractor import SEARCHABLE_ENTITY_TYPES

    kept, dropped = [], []
    for source in sources:
        (kept if source[0] in SEARCHABLE_ENTITY_TYPES else dropped).append(source)
    if dropped:
        logger.warning(
            "Not crawling %s: %s are metadata on content documents, never "
            "searchable documents of their own. Their uuids still reach "
            "retrieval through the payloads of the content that references them.",
            ", ".join(f"{entity}/{bundle}" for entity, bundle, _ in dropped),
            ", ".join(sorted({entity for entity, _, _ in dropped})),
        )
    return kept


def detect_drupal_changes(
    bundles: Iterable[str] | None = None,
    *,
    published_only: bool = True,
    reconcile_deletes: bool = False,
    extra_floors: Mapping[str, int] | None = None,
) -> Iterator[ChangeRecord]:
    """Yield NEW/CHANGED/UNCHANGED/DELETED records for the configured sources.

    ``extra_floors`` widens the incremental window for named bundles, exactly as
    an unresolved retry marker does — the lowest floor wins. It is how a
    catalog-driven pass (:mod:`app.ingestion.reprocess`) reaches documents the
    changed-since cursor has long since passed, without writing a marker row per
    document or bypassing the ordinary crawl.
    """
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
    retry_floor = _load_retry_floors()
    for bundle, mark in (extra_floors or {}).items():
        held = retry_floor.get(bundle)
        retry_floor[bundle] = mark if held is None else min(held, mark)
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
    # Applied to the caller's list as well as the default one: a spec arriving
    # from --bundle or POST /ingest/run gets the same answer as the default.
    sources = _searchable_sources(sources)

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
            # The high-water mark is a maximum over documents that *succeeded*,
            # which only resumes correctly if every document below it succeeded
            # too. One error or skip in the middle breaks that, and oldest-first
            # ordering does not help: the documents after it still raise the
            # mark above the hole. Pull the window back to the earliest
            # unresolved failure so it stays inside it. Only ever lowers the
            # bound, so the crawl can return more than before but never less.
            floor = retry_floor.get(bundle)
            if high is not None and floor is not None:
                high = min(high, floor)
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
            # UUIDs separately. Block sets are fetched in full every run, so the
            # documents we just yielded ARE the live set.
            #
            # "Live" means *published*, and unpublishing is deliberately handled
            # the same way as deletion. It is not a choice the code could make
            # differently: the site's JSON:API serves an anonymous client nothing
            # but published content — `filter[status]=0` comes back empty and an
            # unfiltered walk returns exactly the published set — so an
            # unpublished document is simply absent, indistinguishable from one
            # that was removed outright.
            #
            # The index is meant to hold what the site currently publishes, so
            # absent means gone from search. Nothing here records the document as
            # permanently deleted: the catalog row goes and its retry marker is
            # cleared, so if it is published again it comes back through the
            # ordinary crawl as NEW. Republishing saves the node, which moves
            # `changed` to now — above any bundle's high-water mark — so the very
            # next run picks it up.
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

                missing = {u: r for u, r in prior.items() if u not in live}
                # Checked before anything is yielded, so a bundle whose live set
                # looks incomplete loses nothing at all — not even the deletions
                # that would have been correct.
                if missing and not _deletions_are_plausible(
                    entity_type, bundle,
                    catalogued=len(prior), live=len(live), missing=len(missing),
                ):
                    continue
                for uuid, record in missing.items():
                    # Confirmed one at a time, against the catalog as it stands
                    # now rather than as it stood when the run began.
                    if not _safe_to_delete(uuid, bundle):
                        continue
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
