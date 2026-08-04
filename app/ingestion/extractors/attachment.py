"""Attached-PDF download + extraction for Drupal nodes.

Network I/O for a node's attached PDF: download (with an http->https upgrade
for hosts that dropped plain-http), extract, and build the canonical PDF
document linked back to its node. Pulled out of the ingestion run coordinator
so that module stays pure orchestration.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.models import CanonicalDocument

if TYPE_CHECKING:
    import requests

    from app.ingestion.change_detection import ChangeRecord

logger = logging.getLogger(__name__)


def fetch_attachment(
    session: "requests.Session", url: str, timeout: float
) -> tuple[bytes, str]:
    """GET an attachment, trying the https:// variant first for http:// URLs.
    Old body HTML still links plain-http PDFs, but teriin.org no longer answers
    on port 80 (the connect attempt hangs until timeout), while the same files
    are served fine over TLS. Falls back to the original URL so hosts that are
    still http-only keep working. Returns (content, url that succeeded)."""
    import requests

    if url.lower().startswith("http://"):
        upgraded = "https://" + url[len("http://"):]
        try:
            response = session.get(upgraded, timeout=timeout)
            response.raise_for_status()
            return response.content, upgraded
        except requests.RequestException:
            logger.info("HTTPS variant failed for %s; retrying original URL.", url)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content, url


def dead_link_status(exc: "requests.RequestException") -> int | None:
    """The HTTP status if this failure was a client error, else None.

    A 4xx means the server answered and the file is not there: old body HTML
    links tender notices and RFQs that were taken down once they closed, and no
    amount of retrying brings them back. Those are worth one quiet line.
    Timeouts, DNS failures and 5xx can clear on their own, so they keep the
    full traceback that tells you which one it was.
    """
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int) and 400 <= status < 500:
        return status
    return None


def _mark_dead(record: "ChangeRecord", url: str, status: int) -> None:
    """Remember a client error so the crawl stops re-fetching this attachment.

    Fails open, like the rest of the pipeline's catalog writes: an unreachable
    database costs one warning and a download retried next sweep, which is what
    happened before the markers existed — never a failed sweep.
    """
    from app.catalog import dead_links

    try:
        dead_links.record(
            record.document_id,
            fingerprint=record.fingerprint,
            url=url,
            status=status,
        )
    except Exception:
        logger.warning(
            "Could not record %s as a dead link; it will be retried.",
            url, exc_info=True,
        )


def build_attachment_doc(
    record: "ChangeRecord", session: "requests.Session"
) -> CanonicalDocument | None:
    """Download a node's attached PDF, extract it, and build a canonical PDF
    document linked back to the node. ``record.payload`` is a (DrupalRecord,
    DrupalFile) pair; ``source_type`` is 'pdf_attachment' so the local on-disk
    PDF pipeline's delete-reconcile never touches these web-sourced docs. The
    ``session`` is shared across the run so downloads reuse the connection pool
    instead of re-handshaking per attachment."""
    import requests

    from app.config import get_settings
    from app.ingestion.canonical import drupal_facets, from_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    node, file = record.payload
    settings = get_settings()
    try:
        content, fetched_url = fetch_attachment(
            session, file.url, settings.drupal_request_timeout
        )
    except requests.RequestException as exc:
        status = dead_link_status(exc)
        if status is not None:
            logger.warning(
                "Attachment %s is unavailable (HTTP %d); skipping.", file.url, status
            )
            _mark_dead(record, file.url, status)
        else:
            logger.exception("Could not download attachment %s; skipping.", file.url)
        return None
    if not content:
        logger.warning("Empty attachment body for %s; skipping.", file.url)
        return None

    result = extract_pdf(content, file.filename or record.document_id)
    # The PDF inherits its node's entity refs and facets so theme-scoped
    # retrieval and per-theme counts reach the attached content too. In-body
    # PDFs linked from several nodes inherit from the first-seen node.
    refs = list(getattr(node, "refs", None) or [])
    return from_pdf(
        result,
        document_id=record.document_id,
        source_type="pdf_attachment",
        title=(file.description or node.title or file.filename or None),
        source_url=node.url,
        file_url=fetched_url,
        linked_article_uuid=(node.uuid or None),
        published_at=node.created,
        extra={"bundle": node.bundle},
        entity_refs=refs,
        **drupal_facets(node.metadata or {}, refs),
    )
