"""The corpus-wide name index, built from authoritative CMS metadata.

Every name here came from a structured CMS field, not from prose. That is what
makes a gazetteer hit worth more than a pattern hit: the CMS asserted the name
exists, so matching it in text is recognition rather than guessing.

Sources, and how well grounded each type actually is
----------------------------------------------------
ORGANIZATION  ``field_completed_sponsors`` (~481 distinct funders/partners),
              ``field_news_source`` (~396 publications), ``field_division``
              (~28 TERI divisions). All plain text in ``raw_meta`` — **not**
              taxonomy references, so they survived taxonomy removal intact.
PROJECT       titles of ``ongoing_projects`` / ``completed_projects`` nodes,
              plus ``field_completed_project_code`` (~932 distinct codes, e.g.
              ``2004BS22``) which the identifier pass matches exactly.
PERSON        ``field_authors`` (~226 distinct) and the ``documents_author``
              facet (~975 distinct). The ``people`` bundle holds **8** nodes.

So PERSON is the open-world case: it has the least authoritative grounding and
the noisiest surfaces ("A.", "A. K.", "& Sharma", "Asha Ram Sihag2"). The
guards below — minimum token counts, no initials-only autolinking, ambiguity
marking — exist almost entirely for it.

Loaded once per process behind an ``lru_cache``, following
``app.retrieval.structured.resolve._cached_author_names``: the extraction hot
path must do zero network I/O per chunk.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable

from app.knowledge.normalize import (
    is_initials_only,
    normalize_org,
    normalize_person,
    normalize_project,
    strip_honorifics,
)

logger = logging.getLogger(__name__)

# Names shorter than this never autolink from prose. A two-character surface
# matches far too much ordinary text to be evidence of anything.
_MIN_SURFACE_CHARS = 4

# A single-token personal name ("Neha", which really appears in field_authors)
# is not enough to recognise someone in prose. Kept in the index for resolution
# to use as a candidate, but not eligible to produce a mention on its own.
_MIN_PERSON_TOKENS = 2

# Project *titles* in this CMS are frequently descriptive rather than naming:
# "Steel", "Summary", "Study of Studies" and "Download" are all real titles.
# Matching those in prose produced almost nothing but false positives — "steel"
# as a material, "EXECUTIVE SUMMARY" as a heading — so a title has to look like
# a name before it may autolink. The project *code* pattern is unaffected and
# remains the reliable PROJECT signal.
_MIN_PROJECT_TOKENS = 3
_MIN_PROJECT_CHARS = 12

# Beyond this many words a CMS field value is a description, not a name.
#
# Applies to values pulled out of free-text CMS *fields* — `field_news_source`
# really does contain whole sentences — where length is good evidence that the
# value is prose.
_MAX_SURFACE_TOKENS = 10

# Project titles are exempt from that cap, and get their own much looser one.
#
# A project title is not a field value that might be prose; it is the `title`
# column of a project-bundle node, which is a title by construction. Applying
# the ten-word rule to it was a category error with a large measured cost: 395
# of 847 distinct project titles were rejected for length alone, so nearly half
# the projects in the corpus could not be recognised by their own full name.
#
# Length is also the *opposite* of a risk here. A false positive needs a run of
# consecutive tokens to match verbatim, and the longer the title the less
# plausible that is; "Ecological footprint: establishing a tool to measure and
# manage urban energy use in India and China" cannot be matched by accident.
# The bound is kept only so a pathological value cannot become a surface at all
# (the longest real title is 32 tokens).
#
# The grammatical checks in `_looks_like_prose` still apply to titles: a title
# containing a finite verb is descriptive, and 8 of them are, so those stay out.
_MAX_PROJECT_TITLE_TOKENS = 40

# At or below this many words, a gazetteer surface is matched case-sensitively.
# See `surface_pattern` for why: short names collide with ordinary nouns, and
# capitalisation is the only thing in the text that tells them apart.
_CASE_SENSITIVE_MAX_TOKENS = 3

# Words that only appear in sentences. Their presence means the field holds
# prose — these fields are free text and some values really are whole
# sentences.
_PROSE_MARKERS = frozenset(
    """
    is are was were has have had will would should could can may might
    while when where which that this these those than because although
    however therefore thus said says according
    """.split()
)

# Surfaces that are real names but also ordinary words, so matching them in
# prose says nothing. Data-driven marking (a normalized form attested for more
# than one entity type) covers the rest; this handles the single-source cases.
_STOP_SURFACES = frozenset(
    """
    the a an and or of for in on at to by with from india energy water air waste
    environment climate change transport research report study news update
    project projects programme program division office limited institute
    """.split()
)


@dataclass(frozen=True)
class GazetteerEntry:
    """One known name, and what is known about it."""

    normalized: str
    surface: str
    entity_type: str
    source: str
    # False when the surface is too short, too generic, or attested for more
    # than one type — such a name may still be a resolution *candidate*, but it
    # must not silently become a mention.
    autolink: bool = True
    is_ambiguous: bool = False


@dataclass
class Gazetteer:
    """Normalized name -> the entries sharing it."""

    entries: dict[str, list[GazetteerEntry]] = field(default_factory=dict)
    # Surfaces eligible for text matching, longest first so that scanning
    # prefers "Ministry of External Affairs" over "Ministry".
    _ordered: list[GazetteerEntry] = field(default_factory=list)

    def add(self, entry: GazetteerEntry) -> None:
        bucket = self.entries.setdefault(entry.normalized, [])
        if any(e.surface == entry.surface and e.entity_type == entry.entity_type
               for e in bucket):
            return
        bucket.append(entry)

    def finalize(self) -> "Gazetteer":
        """Mark ambiguity, then order for longest-match-first scanning.

        Ambiguity is decided from the data rather than a hand-written list: the
        moment one normalized form is attested for two entity types, every entry
        under it stops autolinking. A corpus that grows a second "Phoenix" thus
        disarms the bare form automatically, which is the property that keeps
        false merges rare later.
        """
        rebuilt: dict[str, list[GazetteerEntry]] = {}
        for normalized, bucket in self.entries.items():
            ambiguous = len({e.entity_type for e in bucket}) > 1
            rebuilt[normalized] = [
                GazetteerEntry(
                    normalized=e.normalized, surface=e.surface,
                    entity_type=e.entity_type, source=e.source,
                    autolink=e.autolink and not ambiguous,
                    is_ambiguous=ambiguous,
                )
                for e in bucket
            ]
        self.entries = rebuilt
        self._ordered = sorted(
            (e for bucket in rebuilt.values() for e in bucket if e.autolink),
            key=lambda e: (-len(e.surface), e.surface),
        )
        return self

    @property
    def linkable(self) -> list[GazetteerEntry]:
        return self._ordered

    def candidates(self, text: str) -> list[GazetteerEntry]:
        """The linkable entries that *could* match this text, longest first.

        Running every surface's regex over every chunk is what the naive
        implementation does, and at ~3.6k surfaces it costs ~109 ms per chunk —
        4.5 hours over this corpus, before any LLM stage. This prefilter is the
        difference between that and minutes.

        Exact, not approximate: a surface can only match if its first token
        appears literally in the text (the regex escapes that token and only
        the *separators* between tokens are flexible), so anything filtered out
        here could not have matched. Case-folded on both sides because the
        matcher is case-insensitive.
        """
        if not text:
            return []
        lowered = text.lower()
        return [e for e in self._ordered if _first_token(e.surface) in lowered]

    def lookup(self, normalized: str) -> list[GazetteerEntry]:
        return self.entries.get(normalized, [])

    def __len__(self) -> int:
        return sum(len(b) for b in self.entries.values())


def _looks_like_prose(surface: str, entity_type: str = "") -> bool:
    """Whether a CMS field value is a sentence rather than a name.

    These fields are free text and really do contain prose — one
    ``field_news_source`` value is "India has the third largest emissions while
    the European Union...". Matching that as an organization name is worse than
    useless, and no length rule alone catches it, so the test is grammatical:
    a name does not contain a finite verb or run past a full stop.

    ``entity_type`` selects the length bound only. See
    ``_MAX_PROJECT_TITLE_TOKENS`` for why a project title gets a different one;
    every other test below applies to every type unchanged.
    """
    tokens = surface.split()
    limit = (
        _MAX_PROJECT_TITLE_TOKENS if entity_type == "PROJECT"
        else _MAX_SURFACE_TOKENS
    )
    if len(tokens) > limit:
        return True
    if any(t in _PROSE_MARKERS for t in (w.lower().strip(".,") for w in tokens)):
        return True
    # A capital-less surface is a common noun, not a name ("water resources").
    return not any(t[:1].isupper() for t in tokens)


def _eligible(surface: str, normalized: str, entity_type: str) -> bool:
    """Whether a name may be matched in prose at all."""
    if len(surface.strip()) < _MIN_SURFACE_CHARS or not normalized:
        return False
    if normalized in _STOP_SURFACES:
        return False
    if _looks_like_prose(surface, entity_type):
        return False
    if entity_type == "PERSON":
        if is_initials_only(normalized):
            return False
        if len(normalized.split()) < _MIN_PERSON_TOKENS:
            return False
    if entity_type == "PROJECT":
        if len(normalized.split()) < _MIN_PROJECT_TOKENS:
            return False
        if len(normalized) < _MIN_PROJECT_CHARS:
            return False
    return True


def surface_variants(surface: str, entity_type: str) -> list[str]:
    """Further *spellings of the same name* that should also be recognised.

    Strictly a recognition aid. Every variant folds to the **same normalized
    key** as the surface it came from, so it produces the same candidates, the
    same scores, the same vetoes and the same decision — it only widens the set
    of strings in prose that can become a mention in the first place. Nothing
    here can create an identity, and nothing here weakens a guard: each variant
    is put through ``_eligible`` on its own, so a variant that is too short, too
    generic or initials-only is dropped exactly as a primary surface would be.

    PERSON, honorific-stripped
        The whole of the measured recognition gap. All 102 claim-eligible people
        are stored as "Dr X" / "Mr X" / "Ms X", and questions say "X".

    Deliberately *not* generated: initials expansions, surname-only forms,
    reversed word order, acronyms. Each of those changes which person a string
    could denote, which is a resolution question and not this function's to
    answer.
    """
    if entity_type != "PERSON":
        return []
    bare = strip_honorifics(surface)
    return [bare] if bare and bare != surface else []


def build_gazetteer(rows: Iterable[tuple[str, str, str]]) -> Gazetteer:
    """Build from ``(surface, entity_type, source)`` triples.

    Takes an iterable rather than reading the database itself, so tests build
    one from literals and the loader below is the only thing that needs MySQL.
    """
    normalizers = {
        "PERSON": normalize_person,
        "ORGANIZATION": normalize_org,
        "PROJECT": normalize_project,
    }
    gazetteer = Gazetteer()
    for surface, entity_type, source in rows:
        surface = (surface or "").strip()
        normalizer = normalizers.get(entity_type)
        if not surface or normalizer is None:
            continue
        normalized = normalizer(surface)
        if not normalized:
            continue
        gazetteer.add(
            GazetteerEntry(
                normalized=normalized, surface=surface, entity_type=entity_type,
                source=source, autolink=_eligible(surface, normalized, entity_type),
            )
        )
        for variant in surface_variants(surface, entity_type):
            # Same normalized key by construction, so `finalize` marks it
            # ambiguous with its parent and it can never link where the parent
            # would not.
            gazetteer.add(
                GazetteerEntry(
                    normalized=normalized, surface=variant,
                    entity_type=entity_type, source=source,
                    autolink=_eligible(variant, normalized, entity_type),
                )
            )
    return gazetteer.finalize()


# --------------------------------------------------------------------------- #
# Loading from the catalog
# --------------------------------------------------------------------------- #

# raw_meta field -> entity type. Only fields whose values are plain names; a
# field holding dates, codes or free prose is not a name source.
_META_SOURCES: tuple[tuple[str, str], ...] = (
    ("field_completed_sponsors", "ORGANIZATION"),
    ("field_news_source", "ORGANIZATION"),
    ("field_division", "ORGANIZATION"),
    ("field_authors", "PERSON"),
    # The principal-investigator fields. Added because leaving them out was the
    # larger half of the person-recognition gap: 50 of the 102 claim-eligible
    # people had no gazetteer surface *at all*, with or without their title,
    # and every one of them is `pi_attested` — an identity minted from these
    # very fields by `app.knowledge.pi_promotion`.
    #
    # So the corpus was in the position of trusting `field_completed_pi_name`
    # enough to create a canonical, claim-eligible person from it, while not
    # trusting it enough to recognise that person's name in text. Adding it
    # here introduces no new trust; it removes an inconsistency.
    ("field_completed_pi_name", "PERSON"),
    ("field_ongoing_pi_name", "PERSON"),
)

_PROJECT_BUNDLES = ("ongoing_projects", "completed_projects")


def _json_values(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()] if str(value).strip() else []


def load_rows() -> list[tuple[str, str, str]]:
    """Every candidate name in the catalog, as (surface, type, source)."""
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    rows: list[tuple[str, str, str]] = []
    with mysql_connection() as conn, conn.cursor() as cur:
        for field_name, entity_type in _META_SOURCES:
            cur.execute(
                f"SELECT JSON_EXTRACT(raw_meta, %s) AS v FROM `{table}` "
                "WHERE JSON_EXTRACT(raw_meta, %s) IS NOT NULL",
                (f"$.{field_name}", f"$.{field_name}"),
            )
            for row in cur.fetchall():
                rows.extend(
                    (value, entity_type, field_name)
                    for value in _json_values(row["v"])
                )
        # Deliberately NOT restricted to `entity_type='node'`, unlike the seeder
        # (app.knowledge.seed._seed_projects), which creates a PROJECT entity
        # only for a node. A PDF attachment inherits its parent's bundle, so
        # this picks up ~159 further titles that have no canonical entity —
        # "Water Sustainability Assessment of Chennai" among them, which is a
        # real project name the CMS happens to hold only as an event and a news
        # item.
        #
        # Those mentions are extracted and then resolve to UNRESOLVED, and that
        # is the intended division of labour: extraction reports sightings,
        # resolution decides identity. Filtering them here would trade a real
        # mention for nothing, since junk titles like "Download" are already
        # excluded by the minimum-token rule in `_eligible`.
        placeholders = ", ".join(["%s"] * len(_PROJECT_BUNDLES))
        cur.execute(
            f"SELECT title FROM `{table}` WHERE bundle IN ({placeholders}) "
            "AND title IS NOT NULL AND title <> ''",
            _PROJECT_BUNDLES,
        )
        rows.extend((r["title"], "PROJECT", "project_title") for r in cur.fetchall())
        # The author facet: broader and noisier than field_authors, which is why
        # it is loaded last and the eligibility guards above matter.
        #
        # A single-token value is filtered here rather than left to _eligible,
        # because an ineligible entry still counts toward finalize()'s
        # cross-type ambiguity check -- and app.knowledge.seed already treats a
        # single-token author facet value as not a name at all (`if
        # len(normalized.split()) < 2: continue`), so the real entity table
        # never has one. Without this, an institutional byline sharing its
        # exact name with a real organization ("TERI" as an "author", not a
        # person) silently disarms the organization's own, otherwise-eligible
        # entry: the moment "teri" is attested for PERSON at all, finalize()
        # marks the whole bare form ambiguous and the corpus's own flagship
        # organization can no longer be recognised in a plain question about
        # it. Matching seed.py's rule here is applying the same fact this
        # facet already established, not inventing a new exception to
        # ambiguity in general -- a real two-type collision (e.g. a project
        # and an organization both genuinely named "Phoenix") still counts.
        cur.execute(f"SELECT DISTINCT author FROM `{table}_author`")
        rows.extend(
            (r["author"], "PERSON", "documents_author")
            for r in cur.fetchall()
            if len((r["author"] or "").strip().split()) >= 2
        )
    return rows


@lru_cache(maxsize=1)
def get_gazetteer() -> Gazetteer:
    """The process-wide gazetteer. Empty (not fatal) if the catalog is
    unreachable — extraction degrades to its pattern passes rather than failing
    a sweep, matching the fail-open convention everywhere else in ingestion."""
    try:
        gazetteer = build_gazetteer(load_rows())
    except Exception:
        logger.warning("Could not load the gazetteer; patterns only.", exc_info=True)
        return Gazetteer().finalize()
    logger.info(
        "Gazetteer: %d names, %d linkable.", len(gazetteer), len(gazetteer.linkable)
    )
    return gazetteer


def reload_gazetteer() -> None:
    """Drop the cached gazetteer. For tests, and after seeding new names."""
    get_gazetteer.cache_clear()


def gazetteer_version(gazetteer: Gazetteer) -> str:
    """A short fingerprint of the linkable name set.

    Part of the extraction cache key: adding a name changes what extraction
    would find, so cached mentions computed without it must not be reused.
    """
    import hashlib

    joined = "\x1f".join(
        f"{e.entity_type}:{e.normalized}" for e in gazetteer.linkable
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


_WORD_BOUNDARY_CACHE: dict[str, re.Pattern[str]] = {}
_FIRST_TOKEN_CACHE: dict[str, str] = {}


def _first_token(surface: str) -> str:
    """The lower-cased first whitespace-delimited token of a surface.

    Used as the containment prefilter key in `Gazetteer.candidates`, and cached
    because it is asked for once per surface per chunk.
    """
    cached = _FIRST_TOKEN_CACHE.get(surface)
    if cached is None:
        parts = surface.split()
        cached = parts[0].lower() if parts else surface.lower()
        _FIRST_TOKEN_CACHE[surface] = cached
    return cached


def surface_pattern(surface: str) -> re.Pattern[str]:
    """A boundary-anchored, whitespace-tolerant matcher for one surface.

    Whitespace in the stored name is matched as "any run of whitespace" so a
    line-wrapped "Ministry of\\nExternal Affairs" is still found, and the
    boundaries stop "Air" matching inside "Airport".

    Anchored with ``(?<!\\w)`` / ``(?!\\w)`` rather than ``\\b``. A CMS name is
    untrusted text and may begin or end with punctuation — "Kris Heavy
    Engineering (Sdn.Bhd)" is a real sponsor — and ``\\b`` after ")" asserts a
    boundary between two non-word characters, which never holds, so the name
    could never be matched at all. The lookarounds mean the same thing for a
    name ending in a letter and still work for one ending in a bracket.
    """
    cached = _WORD_BOUNDARY_CACHE.get(surface)
    if cached is None:
        parts = [re.escape(p) for p in surface.split()]
        # Short names are matched case-sensitively, long ones are not.
        #
        # Several real CMS values are also ordinary noun phrases — the news
        # source "Medium", the division "Water Resources" — and matching those
        # case-insensitively turned every "medium" and "water resources" in
        # prose into an organization. Capitalisation is the only signal in the
        # text that distinguishes the name from the noun. Longer names are
        # distinctive enough that the risk inverts, and there case-insensitivity
        # buys back headings and all-caps runs.
        flags = 0 if len(parts) <= _CASE_SENSITIVE_MAX_TOKENS else re.IGNORECASE
        cached = re.compile(
            r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)", flags
        )
        _WORD_BOUNDARY_CACHE[surface] = cached
    return cached
