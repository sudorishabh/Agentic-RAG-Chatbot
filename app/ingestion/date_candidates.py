"""Candidate publication dates for an attached PDF — measured, never applied.

Phase 0 of the attachment-date work. Today every PDF inherits ``node.created``
(see :func:`app.ingestion.extractors.attachment.build_attachment_doc`), which is
right for the majority and wrong in two opposite directions. This module works
out what each available source *would* say and what a correction *would*
choose, so the blast radius can be measured against the real corpus before any
document's ``effective_start_date`` moves. Nothing here writes to a document.

What the corpus says (full JSON:API crawl, 8510 nodes / 2687 PDF attachments):

- 62.9% of attachments already have ``file.created`` on the same day as
  ``node.created`` — the current behaviour is correct and must not move.
- A content migration ran Dec 2017 - Feb 2018 with stragglers to May 2018:
  1406 files (52%) share just four timestamps, one of them
  (2017-12-19 06:59:00, 397 files) spanning 13.5 years of node dates. No file
  entity on the site predates 2017-12, while nodes go back to 2001, and file
  ids are perfectly ordered by ``created`` (0/2686 inversions) — the signature
  of a sequential batch insert. For these files ``file.created`` is the import
  timestamp, not an upload date.
- In that same window ``node.created`` is compromised too: it runs a median of
  1045 days *later* than the PDF's own authoring date, and is more than a year
  late for 66% of them (against 4% after the migration). Both Drupal dates are
  artifacts there, and only the PDF's own metadata is independent evidence.
- After the migration a >1y node/file gap is rare (5.4% vs 27.6%), so it is
  informative: it really does mean "this PDF was added to an older page".

Hence the two-sided correction modelled by :func:`resolve` — it moves a
document only on positive evidence and leaves the agreeing majority alone.
``Last-Modified`` is deliberately absent: a whole-filesystem copy on 2022-11-09
overwrote the mtime of every older file (85% of sampled attachments carry that
exact stamp, and none carries an earlier one), so it cannot date anything that
predates it.
"""
from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    "DateCandidates",
    "MIGRATION_CUTOFF",
    "parse_pdf_date",
    "read_pdf_docinfo",
    "resolve",
]

# Files created before this are migration imports, not uploads: monthly counts
# collapse from 929 (2017-12) and 497 (2018-01) to single digits from 2018-06,
# and the share sitting on a >1y-older node drops from 27.6% to 5.4% across it.
MIGRATION_CUTOFF = datetime(2018, 6, 1, tzinfo=timezone.utc)

# A correction has to clear a year to fire. Both error modes this addresses are
# multi-year (median 1045 days for the migration era); anything smaller is
# editorial noise -- a PDF attached a fortnight after its article -- where the
# node's date is as good an answer as any.
CORRECTION_THRESHOLD_DAYS = 365

# DocInfo dates outside this range are junk (the "D:00000000000000" default, a
# scanner with a dead clock, a machine set to 1970).
_MIN_YEAR = 1990

# PDF date strings are "D:YYYYMMDDHHmmSSOHH'mm'" with everything after the year
# optional in practice, so parse the leading run of digit pairs and stop.
_PDF_DATE_RE = re.compile(
    r"D:(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?"
)


def parse_pdf_date(value: str | None) -> str | None:
    """A PDF DocInfo date as an ISO-8601 UTC string, or None if unusable.

    Returns None rather than raising for every flavour of malformed value seen
    in the corpus, because a missing candidate is a fine outcome here — a
    document with no PDF date simply keeps whatever Drupal says.
    """
    if not value:
        return None
    match = _PDF_DATE_RE.match(str(value).strip())
    if match is None:
        return None
    year = int(match.group(1))
    if not (_MIN_YEAR <= year <= datetime.now(timezone.utc).year + 1):
        return None
    try:
        parsed = datetime(
            year,
            int(match.group(2) or 1),
            int(match.group(3) or 1),
            int(match.group(4) or 0),
            int(match.group(5) or 0),
            # Some producers emit 60 here; clamp rather than discard the date.
            min(int(match.group(6) or 0), 59),
            tzinfo=timezone.utc,
        )
    except ValueError:
        return None
    if parsed > datetime.now(timezone.utc):
        return None
    return parsed.isoformat()


def read_pdf_docinfo(content: bytes) -> tuple[str | None, str | None]:
    """``(creation_date, mod_date)`` from a PDF's DocInfo, as ISO strings.

    Opens the bytes a second time rather than threading metadata through
    :mod:`app.ingestion.extractors.pdf_extractor`: that module routes between
    local and Azure extraction, so there is no single place the DocInfo is read
    today, and shadow-mode measurement must not perturb that routing. Parsing
    the header is cheap next to extraction, and any failure costs a debug line
    and two Nones.
    """
    if not content:
        return None, None
    try:
        import fitz  # PyMuPDF

        with fitz.open(stream=content, filetype="pdf") as doc:
            meta = doc.metadata or {}
        return (
            parse_pdf_date(meta.get("creationDate")),
            parse_pdf_date(meta.get("modDate")),
        )
    except Exception:
        logger.debug("Could not read PDF DocInfo; no PDF date candidate.", exc_info=True)
        return None, None


@dataclass
class DateCandidates:
    """Every date source for one attachment, plus what a correction would pick.

    ``current`` is what the pipeline assigns today and what remains assigned:
    ``proposed`` is recorded for comparison only.
    """

    document_id: str
    origin: str
    node_created: str | None = None
    file_created: str | None = None
    pdf_created: str | None = None
    pdf_modified: str | None = None
    current: str | None = None
    proposed: str | None = None
    source: str = "node_created"
    rule: str = "default"
    delta_days: int | None = None
    url: str | None = None
    filename: str | None = None

    @property
    def would_move(self) -> bool:
        return bool(self.proposed) and self.proposed != self.current

    def as_dict(self) -> dict:
        return asdict(self)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def resolve(
    *,
    document_id: str,
    origin: str,
    node_created: str | None,
    file_created: str | None = None,
    pdf_created: str | None = None,
    pdf_modified: str | None = None,
    url: str | None = None,
    filename: str | None = None,
) -> DateCandidates:
    """Collect the candidates and model the two-sided correction.

    The default stays ``node.created``; a correction fires only when a second
    source disagrees by more than a year *and* is credible:

    1. **Migration era** — the PDF was authored more than a year before the
       date Drupal claims. Covers the ~57% of attachments whose Drupal dates
       are both import artifacts, where DocInfo is the only real evidence.
    2. **Late upload** — the file was uploaded, after the migration, more than
       a year after its node was created. This is the accretive-page case:
       a page from 2020 collecting a new PDF every year.

    Rule 1 is tried first because it is the larger and more wrong population,
    and because a file that is *both* post-migration-late and authored years
    earlier (a back-catalogue document posted today) is better described by
    when it was written than by when someone got round to uploading it.
    """
    node_dt = _parse(node_created)
    file_dt = _parse(file_created)
    pdf_dt = _parse(pdf_created)

    candidates = DateCandidates(
        document_id=document_id,
        origin=origin,
        node_created=node_created,
        file_created=file_created,
        pdf_created=pdf_created,
        pdf_modified=pdf_modified,
        current=node_created,
        proposed=node_created,
        url=url,
        filename=filename,
    )
    if node_dt is None:
        # Nothing to anchor a correction against; the PDF's own date is then
        # the only thing on offer, and better than nothing.
        if pdf_dt is not None:
            candidates.proposed = pdf_created
            candidates.source = "pdf_docinfo"
            candidates.rule = "no_node_date"
        return candidates

    if pdf_dt is not None and (node_dt - pdf_dt).days > CORRECTION_THRESHOLD_DAYS:
        candidates.proposed = pdf_created
        candidates.source = "pdf_docinfo"
        candidates.rule = "migration_era"
        candidates.delta_days = (pdf_dt - node_dt).days
        return candidates

    if (
        file_dt is not None
        and file_dt >= MIGRATION_CUTOFF
        and (file_dt - node_dt).days > CORRECTION_THRESHOLD_DAYS
    ):
        candidates.proposed = file_created
        candidates.source = "file_created"
        candidates.rule = "late_upload"
        candidates.delta_days = (file_dt - node_dt).days
        return candidates

    return candidates
