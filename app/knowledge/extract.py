"""Mention extraction: find names in chunk text, with verified spans.

Staged cheapest-and-surest first, so the expensive stage sees only what the
cheap ones could not settle:

===  ==================  =========================================  ======
 #   method              source                                     cost
===  ==================  =========================================  ======
 0   ``cms_field``       names this document's own CMS asserts      free
 1   ``identifier``      exact coded patterns (project codes)       free
 2   ``gazetteer``       names known corpus-wide from CMS fields    free
 3   ``pattern``         honorific+name, org suffixes               free
 4   ``llm``             model proposal, span-verified              paid
===  ==================  =========================================  ======

Two invariants hold across every stage:

* **Every mention's span is verified against the chunk text before it is
  returned.** ``surface_text`` must equal ``chunk_text[start:end]``. For stages
  0-3 that is an assertion; for stage 4 it is the whole defence, because model
  output is untrusted input.
* **No stage assigns an ``entity_id``.** Extraction reports sightings; deciding
  which canonical entity a sighting denotes belongs to resolution, and keeping
  that out of here is what stops extraction inventing identity.

Overlapping spans are resolved by length first, then method: a longer name is
more specific, so "Ministry of External Affairs" beats "Ministry" and
"Hindustan Copper Ltd" beats the publication "Hindustan". Among spans of equal
length the cheaper, surer method wins.
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Iterable, Sequence

from app.knowledge.gazetteer import Gazetteer, get_gazetteer, surface_pattern
from app.knowledge.normalize import normalize_for
from app.knowledge.types import EXTRACTION_METHODS, Mention

logger = logging.getLogger(__name__)

# Bumped whenever a change here would make extraction produce different output
# for the same text. Stored beside every cached result and every mention row, so
# stale output reads as a miss instead of being served by newer code. Mirrors
# app.ingestion.enrich.abstract_version.
EXTRACTOR_VERSION = "entity-extract-v1"

# Confidence by method. Not probabilities — a deliberate ordering that later
# stages (resolution, review) can threshold on. A CMS-asserted name found in the
# document it belongs to is as sure as this layer gets; a bare textual pattern
# is a guess worth checking.
_CONFIDENCE = {
    "cms_field": 0.98,
    "identifier": 0.97,
    "gazetteer": 0.85,
    "pattern": 0.60,
    "llm": 0.50,
}

_METHOD_RANK = {method: i for i, method in enumerate(EXTRACTION_METHODS)}

# --------------------------------------------------------------------------- #
# Deterministic patterns
# --------------------------------------------------------------------------- #

# TERI project codes: four-digit year, two letters, two digits (2004BS22).
# Anchored on word boundaries and case-sensitive, so it cannot fire on prose.
_PROJECT_CODE = re.compile(r"\b((?:19|20)\d{2}[A-Z]{2}\d{2})\b")

# An honorific followed by a name. The honorific is what makes this safe: bare
# capitalised bigrams match every place name and section heading in the corpus.
_PERSON_TITLED = re.compile(
    r"\b(?:Dr|Mr|Mrs|Ms|Prof|Professor|Shri|Smt|Sh|Er)\.?\s+"
    r"((?:[A-Z]\.?\s+){0,3}[A-Z][a-z]+(?:\s+(?:[A-Z]\.?\s+)*[A-Z][a-z]+){0,3})"
)

# Words that mark a name as naming an *organization* rather than a concept,
# split by how much work the word does on its own.
#
# STRONG words name a body by themselves: "Indian Institute", "Tata Limited".
# WEAK words are ordinary nouns that only name an organization once enough
# proper noun precedes them — "Steering Committee", "High School" and "Village
# Council" are generic bodies, while "Govt. First Grade College" is a school.
# One preceding capitalised word is enough for a strong indicator; a weak one
# needs at least two, which is what separates those two lists.
_ORG_STRONG = (
    "Limited|Ltd|Institute|University|Ministry|Foundation|Agency|Corporation|"
    "Commission|Laboratories|Association|Federation|Convention|Consultancy|"
    "Consultants|Organisation|Organization"
)
_ORG_WEAK = (
    "Council|Authority|Department|Society|Bank|Board|Centre|Center|Alliance|"
    "Partnership|College|School|Company|Trust|Union|Committee"
)
_ORG_INDICATORS = _ORG_STRONG + "|" + _ORG_WEAK

# Indicator words that must never *begin* a name. "Corporation Limited" and
# "Services Limited" are the tails of names whose head the pattern could not
# see, usually because a lowercase word ("and", "of") broke the capitalised run.
_ORG_HEAD_BANNED = frozenset(
    w.lower() for w in _ORG_INDICATORS.split("|")
) | {"other", "holding", "medium", "high", "the"}

# An organization named by its structural suffix. `[^\S\n]` (whitespace that is
# not a newline) separates the words, so a match cannot run across a line break
# — without it the pattern swept up the prose that followed, storing "Tata
# Chemicals\nsuccessfully commissioned a" as an organization name.
_ORG_GLOSS_CONNECTORS = "of|and|for|the|in|on|de|van|von|del"
# Connectors are admitted between the capitalised words, but the name must
# still *start* with one: "The Energy and Resources Institute" was otherwise cut
# to "Resources Institute", because the lowercase "and" ended the run. They are
# a closed list of short function words, so a verb like "has" still stops the
# match and prose cannot be swallowed.
_ORG_SUFFIX = re.compile(
    r"\b([A-Z][\w&.'-]*"
    r"(?:[^\S\n]+(?:[A-Z][\w&.'-]*|(?:" + _ORG_GLOSS_CONNECTORS + r"))){0,6}"
    r"[^\S\n]+(?:" + _ORG_INDICATORS + r"))\b"
)


def _org_suffix_is_credible(surface: str) -> bool:
    """Whether an org-suffix match names a body rather than describing one."""
    tokens = surface.split()
    if len(tokens) < 2:
        return False
    if tokens[0].strip(".").lower() in _ORG_HEAD_BANNED:
        return False
    indicator = tokens[-1].strip(".").lower()
    weak = {w.lower() for w in _ORG_WEAK.split("|")}
    # A weak indicator needs at least two words of proper noun ahead of it.
    return len(tokens) >= 3 if indicator in weak else True

# An organization written as "Full Name (ACRONYM)". The expansion must itself
# end in an organization indicator, because this pattern otherwise fires on
# every glossed concept in the corpus — "carbon capture and utilisation plant
# (CCU)" is a technology, not a body.
#
# The words between the head and the indicator must themselves be capitalised,
# apart from the short connectors a name may legitimately contain ("of", "and",
# "for"). Allowing any word there let the pattern swallow whole sentences:
# "India has the third largest emissions while the European Union (EU)" was
# being captured as one organization name.
_ORG_ACRONYM_GLOSS = re.compile(
    r"\b([A-Z][\w&.'-]*"
    r"(?:[^\S\n]+(?:[A-Z][\w&.'-]*|(?:" + _ORG_GLOSS_CONNECTORS + r"))){1,8}"
    r"[^\S\n]+(?:" + _ORG_INDICATORS + r"))[^\S\n]*\(([A-Z]{2,8})\)"
)


def _span_ok(text: str, start: int, end: int) -> bool:
    return 0 <= start < end <= len(text)


def _mention(
    *, chunk_id: str, document_id: str, text: str, start: int, end: int,
    entity_type: str, method: str, confidence: float | None = None,
) -> Mention | None:
    """Build a mention, or None when the span does not hold what it claims.

    The single construction point for every stage, so span verification cannot
    be skipped by adding a new one.
    """
    if not _span_ok(text, start, end):
        return None
    surface = text[start:end]
    if not surface.strip():
        return None
    # Trim whitespace the pattern may have swept in, keeping offsets honest.
    lead = len(surface) - len(surface.lstrip())
    trail = len(surface) - len(surface.rstrip())
    start, end = start + lead, end - trail
    if start >= end:
        return None
    surface = text[start:end]
    normalized = normalize_for(entity_type, surface)
    if not normalized:
        return None
    mention = Mention(
        chunk_id=chunk_id, document_id=document_id,
        start_offset=start, end_offset=end, surface_text=surface,
        normalized_text=normalized, entity_type=entity_type,
        extraction_method=method, extractor_version=EXTRACTOR_VERSION,
        confidence=_CONFIDENCE[method] if confidence is None else confidence,
    )
    return mention if mention.verify_against(text) else None


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #

def _from_names(
    text: str, names: Iterable[tuple[str, str]], *, chunk_id: str,
    document_id: str, method: str,
) -> list[Mention]:
    """Locate each ``(surface, entity_type)`` in the text, every occurrence."""
    found: list[Mention] = []
    for surface, entity_type in names:
        for match in surface_pattern(surface).finditer(text):
            mention = _mention(
                chunk_id=chunk_id, document_id=document_id, text=text,
                start=match.start(), end=match.end(),
                entity_type=entity_type, method=method,
            )
            if mention is not None:
                found.append(mention)
    return found


def extract_cms_field(
    text: str, *, chunk_id: str, document_id: str,
    cms_names: Sequence[tuple[str, str]],
) -> list[Mention]:
    """Stage 0 — names this document's own CMS metadata asserts.

    Worth more than a corpus-wide gazetteer hit: the CMS says this document is
    by, or about, this name, so finding it in the body is confirmation rather
    than recognition.
    """
    return _from_names(
        text, cms_names, chunk_id=chunk_id, document_id=document_id,
        method="cms_field",
    )


def extract_identifiers(text: str, *, chunk_id: str, document_id: str) -> list[Mention]:
    """Stage 1 — coded identifiers. Exact by construction, so no ambiguity."""
    return [
        m
        for match in _PROJECT_CODE.finditer(text)
        if (m := _mention(
            chunk_id=chunk_id, document_id=document_id, text=text,
            start=match.start(1), end=match.end(1),
            entity_type="PROJECT", method="identifier",
        )) is not None
    ]


def extract_gazetteer(
    text: str, *, chunk_id: str, document_id: str, gazetteer: Gazetteer,
) -> list[Mention]:
    """Stage 2 — corpus-wide known names, longest surface first."""
    return _from_names(
        text,
        [(e.surface, e.entity_type) for e in gazetteer.candidates(text)],
        chunk_id=chunk_id, document_id=document_id, method="gazetteer",
    )


def extract_patterns(text: str, *, chunk_id: str, document_id: str) -> list[Mention]:
    """Stage 3 — deterministic textual patterns, for names no CMS field knows."""
    found: list[Mention] = []
    for match in _PERSON_TITLED.finditer(text):
        mention = _mention(
            chunk_id=chunk_id, document_id=document_id, text=text,
            start=match.start(1), end=match.end(1),
            entity_type="PERSON", method="pattern",
        )
        if mention is not None:
            found.append(mention)
    for match in _ORG_SUFFIX.finditer(text):
        if not _org_suffix_is_credible(match.group(1)):
            continue
        mention = _mention(
            chunk_id=chunk_id, document_id=document_id, text=text,
            start=match.start(1), end=match.end(1),
            entity_type="ORGANIZATION", method="pattern",
        )
        if mention is not None:
            found.append(mention)
    for match in _ORG_ACRONYM_GLOSS.finditer(text):
        for group in (1, 2):
            mention = _mention(
                chunk_id=chunk_id, document_id=document_id, text=text,
                start=match.start(group), end=match.end(group),
                entity_type="ORGANIZATION", method="pattern",
            )
            if mention is not None:
                found.append(mention)
    return found


# --------------------------------------------------------------------------- #
# Overlap resolution
# --------------------------------------------------------------------------- #

def dedupe(mentions: Sequence[Mention]) -> list[Mention]:
    """One mention per span, and no span inside another.

    Precedence is **length first**, then method rank, then confidence. Two
    stages finding the same name is the normal case — the gazetteer and the
    org-suffix pattern both match "Ministry of External Affairs" — and keeping
    both would double every count downstream.

    Length outranks method because ranking by method first truncates names: the
    gazetteer knows the publication "Hindustan" and beats the pattern's longer,
    correct "Hindustan Copper Ltd" purely for being a cheaper stage. Among spans
    of equal length the method still decides, which is what keeps a CMS-asserted
    name ahead of the same span found by a bare pattern.
    """
    ordered = sorted(
        mentions,
        key=lambda m: (
            -(m.end_offset - m.start_offset),
            _METHOD_RANK.get(m.extraction_method, len(EXTRACTION_METHODS)),
            -m.confidence,
            m.start_offset,
        ),
    )
    kept: list[Mention] = []
    for mention in ordered:
        if any(
            mention.start_offset < k.end_offset and k.start_offset < mention.end_offset
            for k in kept
        ):
            continue
        kept.append(mention)
    return sorted(kept, key=lambda m: (m.start_offset, m.end_offset))


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def extract_mentions(
    text: str,
    *,
    chunk_id: str,
    document_id: str,
    cms_names: Sequence[tuple[str, str]] = (),
    gazetteer: Gazetteer | None = None,
) -> list[Mention]:
    """Every mention in one chunk, deduplicated and span-verified.

    Deterministic: the same text, gazetteer and CMS names always yield the same
    list, which is what makes repeated extraction idempotent without a
    bookkeeping table.
    """
    if not text or not text.strip():
        return []
    gazetteer = get_gazetteer() if gazetteer is None else gazetteer
    found: list[Mention] = []
    found += extract_cms_field(
        text, chunk_id=chunk_id, document_id=document_id, cms_names=cms_names
    )
    found += extract_identifiers(text, chunk_id=chunk_id, document_id=document_id)
    found += extract_gazetteer(
        text, chunk_id=chunk_id, document_id=document_id, gazetteer=gazetteer
    )
    found += extract_patterns(text, chunk_id=chunk_id, document_id=document_id)
    return dedupe(found)


def extraction_key(content_hash: str, gazetteer_fingerprint: str) -> str:
    """Cache key for one chunk's extraction.

    Covers the chunk's content, the extractor and the name index, because all
    three change what extraction would find. Keyed on ``content_hash`` rather
    than ``chunk_id`` deliberately: chunk ids are version-scoped, so re-indexing
    a document changes every id while most paragraphs are untouched — hashing
    the text keeps those cache hits.
    """
    joined = "\x1f".join((content_hash, EXTRACTOR_VERSION, gazetteer_fingerprint))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
