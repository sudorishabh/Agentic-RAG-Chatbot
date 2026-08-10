"""LLM evidence interpreter for ambiguous PDF dates.

Called only for cases :mod:`app.ingestion.date_rules` deferred. Since that
module can no longer propose a change, **this is the only path in the system
that can produce a date override**, and it may do so on one basis: the document
itself states when it was published.

The model is not asked "when was this published?". It is asked what *kind* of
date the evidence supports, because the whole problem is that a corpus is full
of dates that look publishable and are not — reporting periods, event dates,
notification dates, effective dates, upload timestamps and PDF export dates.

Four safety properties:

1. **The model never sets a date.** It returns a proposal; the caller records it
   in shadow storage.
2. **An override must quote the document.** ``publication_statement`` has to
   carry the verbatim phrase that states publication; a verdict that cannot
   produce one is downgraded to ``review``. This is what stops a confident
   paraphrase from becoming a date.
3. **Only ``date_type="publication"`` can override**, at
   :data:`MIN_OVERRIDE_CONFIDENCE` or better. Everything else — including
   notification and effective dates, which read like publication dates and are
   not — keeps the page date or goes to review.
4. **It sees metadata and a short text head, never a whole PDF**, so cost per
   call is bounded and Document Intelligence is unreachable.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, PrivateAttr, field_validator

from app.ingestion.date_evidence import PdfEvidence

logger = logging.getLogger(__name__)

__all__ = [
    "DateInterpretation",
    "MIN_OVERRIDE_CONFIDENCE",
    "SYSTEM_PROMPT",
    "interpret",
    "prompt_version",
]

# Raised from 0.85 after manual review: an override now changes a date that
# nothing else in the system would have changed, so it must be near-certain.
MIN_OVERRIDE_CONFIDENCE = 0.9

# Shortest phrase accepted as a quotation of the document. Below this it is not
# a statement, it is a fragment.
MIN_STATEMENT_CHARS = 8

_MIN_YEAR = 1990

_MONTH_RE = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?"
    r"|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
    re.I,
)
_WEEKDAY_RE = re.compile(
    r"\b(mon|tues?|wed(?:nes)?|thur?s?|fri|sat(?:ur)?|sun)(?:day)?\b", re.I
)
# dd.mm.yyyy / dd-mm-yy / yyyy-mm-dd and friends.
_NUMERIC_DATE_RE = re.compile(r"\b(\d{1,4})[./-](\d{1,2})[./-](\d{2,4})\b")

# A dateline: a place, a comma, then a date carrying at least a day.
# "New Delhi, 31 March 2025" / "Chandigarh,23.12.13:" / "Colombo, July 9, 2014"
# This is how press releases and clippings state their issue date, with no
# publication verb anywhere. A bare year is deliberately NOT accepted here, so
# "TERI, 2023" is not mistaken for a dateline.
_MONTH_WORD = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?"
    r"|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_DATELINE_RE = re.compile(
    r"\b[A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){0,2}\s*,\s*"
    r"(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    rf"|\d{{1,2}}\s+{_MONTH_WORD}\s+\d{{4}}"
    rf"|{_MONTH_WORD}\s+\d{{1,2}},?\s+\d{{4}})",
    re.I,
)

# Language that ties a date to publication or issue.
_QUALIFIER_RE = re.compile(
    r"\b(publish(?:ed|ing)?|publication|issue(?:d)?|dated|dt\.?|released?|"
    r"printed|edition of|as on)\b",
    re.I,
)
# Language that ties a date to something that is NOT publication. Checked
# against the words immediately before the date, so the nearest cue wins.
_DISQUALIFIER_RE = re.compile(
    r"\b(updat(?:e|ed|ing)|revis(?:ed|ion)|amend(?:ed|ment)|effective|"
    r"w\.e\.f|with effect from|notif(?:ied|ication)|came into force|"
    r"comes into force|held|scheduled|valid|expir(?:es|y)|due|accessed|"
    r"retrieved|superseded|reprint(?:ed)?)\b",
    re.I,
)

SYSTEM_PROMPT = """\
You classify date evidence for a PDF published on a research institute's website.

You are NOT being asked "when was this published?". You are asked what kind of \
date, if any, the evidence supports. Getting the kind wrong is worse than \
returning nothing, because a wrong publication date is acted on silently.

ALWAYS report what you actually found. Set date_type and candidate_date to \
describe the best date in the evidence even when you recommend keeping the page \
date. "unknown" means you found no date at all — not "I found one but it does \
not qualify". The classification is used even when nothing is overridden.

Kinds you must keep apart:
- publication: when THIS document was released to readers.
- upload: when the file was put on the web server. NEVER a publication date on \
its own.
- authoring: when the PDF file was generated or exported. A PDF CreationDate is \
authoring evidence and is frequently a re-export years after publication.
- edition: a reporting period the document covers - "2024-2025" on an annual \
report, "Q3 2021", "FY 18-19". A LABEL, not a date. An annual report for \
2024-2025 was NOT published on 2024-01-01.
- event: the date of a conference, webinar or meeting. An agenda for a March \
event is not necessarily published in March.
- notification: a date something was notified, issued to parties, or came into \
force administratively. NOT a publication date.
- effective: a date a policy or rule takes effect. NOT a publication date.

WORKED EXAMPLES — publication (these SHOULD be recommended_action="override"):

1. Newspaper issue. A masthead naming a newspaper with its issue date IS that
   issue's publication date.
   text: "HINDUSTAN TIMES CHANDIGARH MONDAY, DECEMBER 23, 2013"
   -> date_type=publication, candidate_date=2013-12-23,
      publication_statement="HINDUSTAN TIMES CHANDIGARH MONDAY, DECEMBER 23, 2013"
   text: "The Hindu, December 23, 2013 - Business page"
   -> date_type=publication, candidate_date=2013-12-23,
      publication_statement="The Hindu, December 23, 2013"

2. Official issue / bulletin line. A numbered issue with a date is published on
   that date.
   text: "ISSUE NO. 22 DATED 11-12-2024"
   -> date_type=publication, candidate_date=2024-12-11,
      publication_statement="ISSUE NO. 22 DATED 11-12-2024"

3. Explicit publication labels, in any of these forms:
   "Published on 12 September 2024" / "Publication Date: March 2019" /
   "Date of Publication: 15.03.2019" / "First published 2015" /
   "Published by Authority ... 12 August 2021" (gazette publication line)
   -> date_type=publication, with the phrase copied verbatim.

WORKED EXAMPLES — NOT publication (these must NOT override):

   "Notified on 18.05.2023"          -> date_type=notification
   "Shall come into force with effect from 1 April 2024" -> date_type=effective
   "Workshop held on 5 March 2025"   -> date_type=event
   "Annual Report 2024-2025"         -> date_type=edition, edition_label="2024-2025"
   PDF CreationDate 2019-08-01, nothing in the text -> date_type=authoring
   Drupal file uploaded 2024-08-22, nothing in the text -> date_type=upload
   A year only in the filename ("2014BL18-report.pdf") -> not evidence at all

Only recommended_action="override" changes anything, and it requires ALL of:
  1. date_type = "publication";
  2. publication_statement = the VERBATIM phrase from the evidence. Copy it
     exactly; do not paraphrase. If you cannot quote it, you do not have it.
  3. the phrase genuinely refers to THIS document being published, as in the
     worked examples above;
  4. high confidence.

If the evidence is ambiguous or contradictory, or you are inferring rather than
reading a statement, answer recommended_action="review" — and still fill in the
date_type and candidate_date you found. If there is genuinely no date anywhere,
answer "keep_page_date" with date_type="unknown". Never guess a date to look
useful, and never promote an upload, authoring, edition, event, notification or
effective date to publication.
"""


class DateInterpretation(BaseModel):
    """Structured verdict from the model, validated before it is recorded."""

    candidate_date: str | None = Field(
        None, description="ISO date (YYYY-MM-DD) if a usable date is supported, else null."
    )
    date_type: Literal[
        "publication", "upload", "authoring", "edition", "event",
        "notification", "effective", "other", "unknown",
    ] = Field("unknown", description="What kind of date the evidence supports.")
    edition_label: str | None = Field(
        None, description="Reporting period such as '2024-2025', if named. Not a date."
    )
    publication_statement: str | None = Field(
        None,
        description=(
            "The VERBATIM phrase stating publication, copied from the evidence. "
            "Required for override; null if the document does not state one."
        ),
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence: str = Field("", description="One or two sentences citing what was relied on.")
    recommended_action: Literal["override", "keep_page_date", "review"] = "keep_page_date"

    # Whether the proposed date was found in the document text the model was
    # shown. A private attribute on purpose: it must not appear in the schema
    # the model answers, because a model cannot be trusted to certify its own
    # grounding. :func:`interpret` sets it; nothing else may.
    _grounded: bool = PrivateAttr(default=True)
    # Whether the quoted statement itself was found in the document text. Kept
    # separate from date grounding on purpose: a print header can carry the date
    # without carrying the statement, and that gap is what let a filename-built
    # masthead through.
    _statement_grounded: bool = PrivateAttr(default=True)

    @property
    def evidence_grounded(self) -> bool:
        return self._grounded

    @property
    def statement_grounded(self) -> bool:
        return self._statement_grounded

    def set_grounded(self, grounded: bool, statement_grounded: bool | None = None) -> None:
        self._grounded = bool(grounded)
        if statement_grounded is not None:
            self._statement_grounded = bool(statement_grounded)

    @field_validator("candidate_date")
    @classmethod
    def _sane_date(cls, value: str | None) -> str | None:
        """Drop a date in the wrong shape or the wrong era."""
        if not value:
            return None
        text = str(value).strip()[:10]
        try:
            parsed = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        except ValueError:
            logger.info("Discarding unparseable model date %r.", value)
            return None
        if not (_MIN_YEAR <= parsed.year <= datetime.now(timezone.utc).year + 1):
            logger.info("Discarding implausible model date %r.", value)
            return None
        return parsed.date().isoformat()

    def statement_supports_date(self) -> bool:
        """Does the quoted statement actually contain the date being proposed?

        A publisher imprint ("PUBLISHED BY The Energy and Resources Institute")
        satisfies "quotes something about publication" while saying nothing
        about *when*. Left unchecked the model pairs it with a date taken from
        elsewhere — usually the PDF CreationDate — which is the v1 failure mode
        wearing a quotation. The quote must carry the year it is being used to
        justify.
        """
        if not self.candidate_date:
            return False
        statement = self.publication_statement or ""
        if not any(ch.isdigit() for ch in statement):
            return False
        year = self.candidate_date[:4]
        if year in statement:
            return True
        # Numeric short-form dates keep a two-digit year: "23.12.13", "11-12-24".
        short = year[2:]
        return bool(re.search(rf"\d{{1,2}}[./-]\d{{1,2}}[./-]{short}\b", statement))

    def statement_is_year_only(self) -> bool:
        """Is the quote a bare year, with no month or day?

        "© TERI, 2023" supports the year and nothing finer, so turning it into
        2023-01-01 invents a January publication. Those go to review.

        Month names are matched on word boundaries. Substring matching looked
        fine and was not: "Decision Making" contains "dec", which made a
        citation year read as month precision and let
        ``Report_Needs_Assessment_TERI_Updated.pdf`` through as 2023-01-01.
        """
        statement = (self.publication_statement or "").lower()
        if _NUMERIC_DATE_RE.search(statement):
            return False
        if _MONTH_RE.search(statement):
            return False
        # Any non-year number (a day) also counts as finer than year precision.
        return all(len(n) == 4 for n in re.findall(r"\d+", statement))

    def statement_supports_the_day(self) -> bool:
        """Does the quote evidence the day-of-month being proposed?

        A quote that reaches only month precision ("Colombo, September 2007")
        cannot justify a specific day; mapping it to the 1st invents one. The
        day has to appear, either inside a numeric date or as its own number.
        """
        if not self.candidate_date:
            return False
        statement = self.publication_statement or ""
        day = int(self.candidate_date[8:10])
        for match in _NUMERIC_DATE_RE.finditer(statement):
            if day in (int(match.group(1)), int(match.group(2))):
                return True
        return any(int(n) == day for n in re.findall(r"\d{1,2}", statement))

    def publication_linkage_ok(self) -> bool:
        """Does the quote explicitly tie THIS date to publication or issue?

        Two failure modes this rejects, both seen in the corpus:

        - the date is governed by a different verb — "first been published in
          September 2020 and is being updated in 2023" proposing 2023, where the
          publication verb belongs to 2020 and 2023 is the update;
        - there is no publication language at all — "January 2023 Final Report"
          is a cover date, not a statement that the report was published then.

        A newspaper masthead is accepted without publication wording: naming a
        paper with a weekday and date *is* an issue line.
        """
        statement = self.publication_statement or ""
        if not statement:
            return False
        lowered = statement.lower()

        position = self._date_position(statement)

        # A weekday plus a date is a newspaper/bulletin issue line; a place plus
        # a date is a press dateline. Neither carries a publication verb, and
        # both state an issue date — unless an update/effective cue governs it.
        masthead = _WEEKDAY_RE.search(lowered) and (
            _MONTH_RE.search(lowered) or _NUMERIC_DATE_RE.search(lowered)
        )
        if masthead or _DATELINE_RE.search(statement):
            if position is None:
                return True
            window = lowered[max(0, position - 40):position]
            return _DISQUALIFIER_RE.search(window) is None

        if position is None:
            return False
        # The 60 characters before the date decide which verb governs it.
        window = lowered[max(0, position - 60):position]
        disqualifier = _DISQUALIFIER_RE.search(window)
        qualifier = _QUALIFIER_RE.search(window)
        if disqualifier is not None:
            # Whichever cue sits closest to the date wins.
            if qualifier is None or qualifier.start() < disqualifier.start():
                return False
        return qualifier is not None

    def _date_position(self, statement: str) -> int | None:
        """Index of the proposed date inside the quote, or None."""
        if not self.candidate_date:
            return None
        year = self.candidate_date[:4]
        index = statement.find(year)
        if index != -1:
            return index
        for match in _NUMERIC_DATE_RE.finditer(statement):
            if match.group(3).lstrip("0") in (year[2:].lstrip("0"), year):
                return match.start()
        return None

    def safe_action(self) -> str:
        """The action after safety downgrades — what the caller may record.

        Anything that is not a quoted, high-confidence publication date becomes
        ``review`` (when the model saw something) or ``keep_page_date`` (when it
        did not). Review is the honest landing place for near-misses: it puts
        the case in front of a person instead of silently changing a date or
        silently discarding real evidence.
        """
        if self.recommended_action == "keep_page_date":
            return "keep_page_date"
        if self.recommended_action == "review":
            return "review"

        # An override has to clear every gate.
        if self.date_type != "publication":
            # The model found a real date of some other kind. Keep the page date;
            # the kind and the date are still recorded for the reviewer.
            return "keep_page_date"
        if self.candidate_date is None:
            return "keep_page_date"
        if not self.evidence_grounded:
            logger.info(
                "Proposed date %s was not found in the document text the model was "
                "shown; downgrading to review.", self.candidate_date
            )
            return "review"
        if not self.statement_grounded:
            # A date can be present while the statement that supposedly
            # establishes it is not — the print-header case. Review, never keep:
            # a real date was identified and must stay visible to a reviewer.
            logger.info(
                "Supporting statement %r was not found in the document text; the "
                "date may have been reconstructed from the filename or anchor. "
                "Downgrading to review.", (self.publication_statement or "")[:60]
            )
            return "review"
        statement = (self.publication_statement or "").strip()
        if len(statement) < MIN_STATEMENT_CHARS:
            logger.info(
                "Override without a quotable publication statement; downgrading to "
                "review (date=%s, confidence=%.2f).", self.candidate_date, self.confidence
            )
            return "review"
        if not self.statement_supports_date():
            logger.info(
                "Quoted statement %r does not carry the proposed date %s; "
                "downgrading to review.", statement[:60], self.candidate_date
            )
            return "review"
        if self.statement_is_year_only():
            logger.info(
                "Quoted statement %r gives only a year; %s would invent a month "
                "and day. Downgrading to review.", statement[:60], self.candidate_date
            )
            return "review"
        if not self.statement_supports_the_day():
            logger.info(
                "Quoted statement %r does not give a day; %s would invent one. "
                "Downgrading to review.", statement[:60], self.candidate_date
            )
            return "review"
        if not self.publication_linkage_ok():
            logger.info(
                "Quoted statement %r does not tie %s to publication (no cue, or the "
                "date is governed by an update/effective/event). Downgrading to "
                "review.", statement[:60], self.candidate_date
            )
            return "review"
        if self.confidence < MIN_OVERRIDE_CONFIDENCE:
            return "review"
        return "override"


_MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)


def date_is_in_text(candidate_date: str | None, text: str) -> bool:
    """Does ``text`` actually contain the day, month and year of this date?

    The point is grounding, not formatting: a masthead may read
    ``CHANDIGARH | TUESDAY | 24 | DECEMBER 2013`` while the model quotes
    ``Chandigarh Tribune, Chandigarh, Tuesday, December 24, 2013``. Those are the
    same date and both should pass. What must NOT pass is a date the model
    assembled from the *filename* — the corpus has newspaper clippings whose
    page text is unreadable mojibake and whose "verbatim quote" was a tidied-up
    copy of ``Hindustan-Times-Chandigarh-Monday-December-23-2013.pdf``.

    So the day, the month and the year all have to appear close together
    somewhere in the text the model was shown.
    """
    if not candidate_date or not text:
        return False
    year = candidate_date[:4]
    month = int(candidate_date[5:7])
    day = int(candidate_date[8:10])
    lowered = " ".join(text.split()).lower()

    # A numeric date carrying the same three components, in either order.
    for match in _NUMERIC_DATE_RE.finditer(lowered):
        parts = {match.group(1), match.group(2), match.group(3)}
        if (str(day) in parts or f"{day:02d}" in parts) and \
           (str(month) in parts or f"{month:02d}" in parts) and \
           (year in parts or year[2:] in parts):
            return True

    # Otherwise the month name, the day and the year must sit in one window.
    name = _MONTH_NAMES[month - 1]
    day_pattern = re.compile(rf"(?<!\d){day}(?:st|nd|rd|th)?(?!\d)")
    for match in re.finditer(rf"{name[:3]}[a-z]*", lowered):
        window = lowered[max(0, match.start() - 60):match.end() + 60]
        if year in window and day_pattern.search(window):
            return True
    return False


def _squash(text: str) -> str:
    """Lowercase alphanumerics only — separators removed, nothing added.

    Absorbs exactly the differences PDF text extraction creates: case, runs of
    whitespace, line breaks, hyphenation across a break, and punctuation
    styling. It cannot introduce a word, reorder words, expand an abbreviation
    or supply a name, so a quote that only matches after "normalisation" of
    that kind will still fail.
    """
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def statement_is_in_text(statement: str | None, text: str) -> bool:
    """Is the model's supporting statement genuinely present in the document?

    Date grounding alone proved insufficient. ``The-Pioneer-...-December-24-2013.pdf``
    contains only a browser print header — ``12/24/13 The Pioneer`` — which
    satisfies "the date appears in the text", yet the model reported a full
    masthead (``The Pioneer, Tuesday, December 24, 2013``) assembled from the
    *filename*. The words "Tuesday" and "December" are nowhere in the document.

    So the quoted phrase itself has to appear. Comparison is on squashed
    alphanumerics, which forgives extraction artefacts and forgives nothing
    else: added words, reordered words and supplied names all fail.
    """
    statement = (statement or "").strip()
    if not statement or not text:
        return False
    squashed = _squash(statement)
    # Too short to be evidence of anything once separators are gone.
    if len(squashed) < MIN_STATEMENT_CHARS:
        return False
    return squashed in _squash(text)


def prompt_version() -> str:
    """Fingerprint of the prompt, schema and thresholds, for cache keys."""
    import hashlib

    payload = (
        SYSTEM_PROMPT
        + json.dumps(DateInterpretation.model_json_schema(), sort_keys=True)
        + f"|{MIN_OVERRIDE_CONFIDENCE}|{MIN_STATEMENT_CHARS}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_user_message(evidence: PdfEvidence) -> str:
    """The evidence bundle, labelled so each field's *kind* is unambiguous."""
    payload: dict[str, Any] = evidence.evidence_dict()
    return (
        "Evidence for one PDF. Fields may be null when unknown. The date fields "
        "below are upload/authoring evidence, not publication dates.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    )


def interpret(evidence: PdfEvidence) -> DateInterpretation | None:
    """Ask the model to classify this PDF's date evidence.

    Returns None when the call fails — the caller keeps the page date, so a
    model outage can never change a date.
    """
    from app.core.clients.llm import get_structured_llm

    try:
        model = get_structured_llm().with_structured_output(DateInterpretation)
        result = model.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(evidence)},
            ]
        )
    except Exception:
        logger.warning(
            "Date interpretation failed for %s; keeping the page date.",
            evidence.document_id, exc_info=True,
        )
        return None
    if not isinstance(result, DateInterpretation):
        logger.warning("Unexpected interpreter payload for %s.", evidence.document_id)
        return None
    # Ground the proposal in what the model was actually shown. Only the
    # document's own text counts: the filename and the anchor are part of the
    # prompt too, and a date lifted from either is exactly what the rules
    # forbid. No readable text means an override can never be grounded.
    if result.recommended_action == "override":
        result.set_grounded(
            date_is_in_text(result.candidate_date, evidence.head_text),
            statement_is_in_text(result.publication_statement, evidence.head_text),
        )
    return result
