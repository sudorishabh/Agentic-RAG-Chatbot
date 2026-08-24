"""Deterministic guard against dating a document by the page that carries it.

Every edition of the TERI annual report is an in-body attachment on one Drupal
page, so all ten share ``published_at = 2022-02-09``. That date belongs to the
page; it is not the publication date of any edition. A model shown it beside a
report title reports it as the report's own date, and measurement said
instruction alone does not stop that: with the prompt rule and the header caveat
both in place, four of six sampled answers to "When was the 2024-25 annual
report published?" still said "published on 9 February 2022".

So this is checked, not requested. The check runs after generation, where
:mod:`app.generation.faithfulness` runs, and reuses the same one-retry
correction path. Two distinct failures are caught:

**Conflation** — a sentence asserting that a report was published on a date that
is a page date. The subject matters: "the page carrying it was published on
2022-02-09" is the wording we want and must not be flagged, while "the report
was published on 2022-02-09" is the false claim.

**Mis-attribution** — the sentence cites ``[n]`` but block *n* does not carry the
date being claimed. Every observed failure did this: the answer cited the FCRA
Financials block, dated 2018-04-04, while quoting 2022-02-09 from another block.
A citation-blind check would have passed it.

If one regeneration still trips the check, :func:`safe_rewrite` replaces the
offending sentences rather than returning them. The job of this guard is that
the claim cannot reach a reader, not that it is usually absent.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from app.core.models.context import ContextBlock

logger = logging.getLogger(__name__)

__all__ = [
    "DateClaimReport",
    "Offender",
    "safe_rewrite",
    "verify_date_claims",
]

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))

# 2022-02-09
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# 9 February 2022 / 9th Feb 2022
_DMY = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + _MONTH_ALT + r")\.?,?\s+(\d{4})\b", re.I)
# February 9, 2022 / Feb 9 2022
_MDY = re.compile(
    r"\b(" + _MONTH_ALT + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I)
# 09/02/2022, 9-2-2022, 2022/02/09
_NUM = re.compile(r"\b(\d{1,4})[/.-](\d{1,2})[/.-](\d{2,4})\b")

# A claim that something was published, in the wordings models actually use.
_PUBLISHED = re.compile(
    r"\b(?:was|were|is|are|been)?\s*"
    r"(?:published|publication\s+date|date\s+of\s+publication|released|issued)\b",
    re.I,
)
# The kind of subject that must never own a page date.
_DOCUMENT_SUBJECT = re.compile(
    r"\b(?:report|edition|document|publication|brochure|factsheet|paper|brief)\b"
    r"|\b20\d{2}\s*[-/]\s*\d{2}\b",
    re.I,
)
# Wording that correctly attributes the date to the page instead.
_PAGE_SUBJECT = re.compile(r"\b(?:web\s*page|page|site|website|listing)\b", re.I)

_CITATION = re.compile(r"\[(\d+)\]")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

SAFE_TEMPLATE = (
    "report edition: {edition}\n"
    "page publication date: {page_date}\n"
    "report publication date: not stated in the available sources"
)


@dataclass
class Offender:
    """One sentence that must not reach a reader, and the reason why."""

    sentence: str
    claimed_date: date
    citations: tuple[int, ...] = ()
    reason: str = "conflation"

    def describe(self) -> str:
        cited = ", ".join(f"[{n}]" for n in self.citations) or "no citation"
        return (
            f"{self.reason}: {self.sentence.strip()[:160]!r} dates a document to "
            f"{self.claimed_date.isoformat()}, which is a page date "
            f"(cited {cited})"
        )


@dataclass
class DateClaimReport:
    offenders: list[Offender] = field(default_factory=list)
    #: Page dates seen on edition-bearing blocks, used by the safe rewrite.
    page_dates: list[date] = field(default_factory=list)
    editions: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.offenders

    def correction_note(self) -> str:
        """The rewrite instruction, naming the offending claim explicitly."""
        joined = "; ".join(o.describe() for o in self.offenders)
        return (
            f"A prior draft dated a document by the web page that carries it "
            f"({joined}). That page date belongs to the page, not to any "
            "document listed on it, and a citation that does not itself carry "
            "the date cannot support the claim. Rewrite without ever stating "
            "that a report, edition or document was published on a page date. "
            "Where the question asks when such a document was published, answer "
            "in these labelled parts instead: report edition; page publication "
            "date; report publication date: not stated in the available "
            "sources. Keep [n] citations, and keep the answer structure "
            "required above."
        )


def _parse_dates(text: str) -> set[date]:
    """Every date the text states, in any of the wordings models use."""
    found: set[date] = set()

    def add(year: int, month: int, day: int) -> None:
        try:
            found.add(date(year, month, day))
        except ValueError:
            pass

    for match in _ISO.finditer(text):
        add(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    for match in _DMY.finditer(text):
        add(int(match.group(3)), _MONTHS[match.group(2).lower().rstrip(".")],
            int(match.group(1)))
    for match in _MDY.finditer(text):
        add(int(match.group(3)), _MONTHS[match.group(1).lower().rstrip(".")],
            int(match.group(2)))
    for match in _NUM.finditer(text):
        a, b, c = (int(match.group(i)) for i in (1, 2, 3))
        if a > 31:                      # yyyy/mm/dd
            add(a, b, c)
        else:                           # dd/mm/yyyy, plus the mm/dd/yyyy reading
            year = c if c > 99 else 2000 + c
            add(year, b, a)
            add(year, a, b)
    return found


def _block_date(payload: dict) -> date | None:
    raw = str(payload.get("published_at") or "")[:10]
    match = _ISO.match(raw)
    if match is None:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def verify_date_claims(
    answer: str, blocks: "Iterable[ContextBlock]"
) -> DateClaimReport:
    """Find sentences that date a document by a page date.

    Citation-aware by design. A sentence is also flagged when the block it cites
    does not carry the date it claims, because that is how the observed failures
    looked: the date came from one block and the citation pointed at another.
    """
    blocks = list(blocks)
    by_n: dict[int, dict] = {}
    page_dates: dict[date, str] = {}
    for block in blocks:
        payload = getattr(block, "payload", {}) or {}
        by_n[getattr(block, "n", 0)] = payload
        block_date = _block_date(payload)
        if block_date is not None and payload.get("edition_label"):
            # Only the date of an edition-bearing block is a page date in the
            # sense that matters: that page holds a series, so its date is the
            # date of no single document on it.
            #
            # Anchored to `published_at` on purpose, and it must stay that way.
            # `document_published_at` is the date the document states about
            # itself — the legitimate answer to "when was this published?" — so
            # treating it as forbidden would invert this guard, rewriting correct
            # answers and admitting the wrong ones. `_block_date` reads only
            # `published_at`; do not "modernise" it to the newer field.
            page_dates.setdefault(block_date, str(payload.get("edition_label")))

    report = DateClaimReport(
        page_dates=sorted(page_dates),
        editions=[page_dates[d] for d in sorted(page_dates)],
    )
    if not page_dates:
        return report

    for sentence in _SENTENCE_SPLIT.split(answer):
        if not sentence.strip() or not _PUBLISHED.search(sentence):
            continue
        claimed = _parse_dates(sentence) & set(page_dates)
        if not claimed:
            continue
        verb = _PUBLISHED.search(sentence)
        subject = sentence[: verb.start()] if verb else sentence
        if _PAGE_SUBJECT.search(subject):
            # "the page carrying it was published on ..." is the wording we want.
            continue
        if not _DOCUMENT_SUBJECT.search(subject):
            continue
        cited = tuple(sorted({int(m.group(1)) for m in _CITATION.finditer(sentence)}))
        # Mis-attribution is named separately: the citation given does not itself
        # carry the date, so it cannot support the claim.
        supported = any(_block_date(by_n.get(n, {})) in claimed for n in cited)
        for claimed_date in sorted(claimed):
            report.offenders.append(Offender(
                sentence=sentence,
                claimed_date=claimed_date,
                citations=cited,
                reason="conflation" if supported else "mis-attributed citation",
            ))
    return report


def safe_rewrite(answer: str, report: DateClaimReport) -> str:
    """Replace each offending sentence with the labelled, safe formulation.

    The last line of defence, reached only when a regeneration has already
    failed the same check. The choice at that point is between a wrong date and
    a mechanically correct answer, and this takes the latter.
    """
    if report.clean:
        return answer
    edition = report.editions[0] if report.editions else "not stated"
    page_date = report.page_dates[0].isoformat() if report.page_dates else "not stated"
    replacement = SAFE_TEMPLATE.format(edition=edition, page_date=page_date)
    rewritten = answer
    for offender in report.offenders:
        if offender.sentence in rewritten:
            rewritten = rewritten.replace(offender.sentence, replacement, 1)
    logger.info(
        "Replaced %d unsafe publication-date sentence(s) after a failed "
        "regeneration.", len(report.offenders),
    )
    return rewritten
