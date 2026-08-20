"""Query-time recognition from the **approved alias model**.

Why this exists
---------------
Recognition on both the ingest and query paths runs through
``app.knowledge.gazetteer``, which is built from raw CMS metadata: every project
title of every bundle, every ``field_news_source`` value, every author facet
row. That breadth is why it needs conservative heuristics — a minimum token
count, a minimum length, case-sensitive matching for short surfaces — because
its inputs really do include "Steel", "Summary", "Download" and "Medium" as
titles, and matching those in prose produced almost nothing but false positives.

Those heuristics are right for prose. They are too blunt for a *question*, and
the benchmark measured the cost: five classes of perfectly ordinary phrasing
never produced a mention at all, so entity resolution was never even reached.

    "What did ADB fund?"                     acronym, 3 chars
    "Which projects did dr alok adholeya lead?"   lower case
    "Who led WEO 2007?"                      2 tokens, 8 chars
    "Who worked on HI-AWARE?"                1 token
    "Who led the Eco-city Project - Phase I?"  en dash, not the stored hyphen

This module reads a different, much cleaner source: ``documents_entity_alias``,
the reviewed alias table of *seeded entities*. Every row there belongs to an
entity the knowledge layer created deliberately, and each carries the two flags
review produced — ``autolink`` and ``is_ambiguous``. Measured on the live
catalog: ``steel``, ``summary``, ``download``, ``medium`` and ``environment``
are not in it at all.

What it does not do
-------------------
It does not resolve anything. It turns a string in a question into a
:class:`~app.knowledge.types.Mention`, and the **unchanged** resolver then
decides identity, trust and eligibility exactly as it does for a gazetteer
mention. So a provisional person still declines, an ambiguous surface still
declines, and every veto still applies. The only thing widened is which strings
get to *ask* the resolver.

It is also query-only, and deliberately so: ingestion writes claims, and
widening what ingestion links would change what is asserted. Widening what a
question may look up changes only what can be found.

The four guards
---------------
Admission to the index (all must hold):

1. ``autolink = 1`` and ``is_ambiguous = 0`` — review said this surface may link;
2. the entity is ``active`` and ``claim_eligible``;
3. the normalized form maps to exactly **one** entity across the *whole* alias
   table, non-autolink rows included — a recorded ambiguity anywhere is a veto,
   which is what keeps ``MPCB`` (Haryana State and Maharashtra Pollution Control
   Boards) unresolved;
4. an ``acronym`` row must be acronym-*shaped* and its letters must be
   derivable from the initials of the name it claims to abbreviate.

Guard 4 earns its place on this corpus. The glossary extractor produced
``MOEFCC -> Central Pollution Control Board`` — wrong, and flagged
``is_ambiguous = 0``, so the review flags alone would have admitted it. The
initials test rejects it because CPCB is not MOEFCC. It costs three legitimate
syllabic acronyms (TRIFED, HAREDA, POSOCO), which stay unresolved rather than
risk a wrong identity.

Accepting a match in the text is separately guarded; see :func:`_admissible`.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# How long a loaded index is reused. Mirrors `policy.INDEX_TTL_SECONDS`: the
# alias table changes only when the knowledge layer re-seeds, and rebuilding it
# per query would cost a MySQL round trip on the read path.
INDEX_TTL_SECONDS = 300.0

# Longest alias, in tokens, that we will try to match. A cap on the n-gram sweep
# rather than on the data: an alias longer than this simply is not looked for,
# and the gazetteer pass already handles long names well.
MAX_ALIAS_TOKENS = 12

# Below this many tokens an ORGANIZATION or PROJECT surface is treated as
# possibly-a-common-noun and needs a capital in the question to be admitted.
# Deliberately the same number as `gazetteer._CASE_SENSITIVE_MAX_TOKENS`, and for
# the same reason: "Water Resources" is a real TERI division *and* an ordinary
# noun phrase, and only the writer's capitalisation distinguishes them.
CASE_SENSITIVE_MAX_TOKENS = 3

# Words skipped when deriving initials, so "Ministry of New and Renewable
# Energy" yields MNRE rather than MONARE.
_INITIAL_SKIP = frozenset(
    {"and", "of", "the", "for", "on", "in", "a", "an", "to", "at", "de", "&"}
)

# What may be read as an acronym *in a question*: a short, upper-case run. The
# case requirement is the guard, not decoration — `oil` is an approved acronym
# alias of "Oil India Limited", and a question about oil is not a question about
# that company. `OIL` is.
_ACRONYM_SHAPE = re.compile(r"^[A-Z][A-Z0-9&.\-]{1,7}$")

# Token spans in a question, so a mention's offsets index the original text.
_TOKEN = re.compile(r"[^\W_]+(?:[.'’&/-][^\W_]+)*", re.UNICODE)

_lock = threading.Lock()
_index: "ApprovedAliasIndex | None" = None
_loaded_at = 0.0


def initials_of(name: str) -> str:
    """The acronym a name would produce, skipping joining words."""
    tokens = [
        t for t in re.split(r"[^A-Za-z0-9]+", name or "")
        if t and t.lower() not in _INITIAL_SKIP
    ]
    if len(tokens) < 2:
        return ""
    return "".join(t[0].upper() for t in tokens)


def acronym_matches_name(acronym: str, name: str) -> bool:
    """Whether ``acronym`` is derivable from ``name``'s initials.

    Accepts a prefix in either direction and a subsequence, so ``ONGC`` matches
    "Oil and Natural Gas Corporation **Limited**" (ONGCL) and ``CPCB`` matches
    "Central Pollution Control Board" exactly. Rejects ``MOEFCC`` against
    "Central Pollution Control Board", which is the mapping this exists for.
    """
    letters = re.sub(r"[^A-Za-z0-9]", "", acronym or "").upper()
    derived = initials_of(name)
    if not letters or not derived:
        return False
    if derived.startswith(letters) or letters.startswith(derived):
        return True
    seen = 0
    for char in derived:
        if seen < len(letters) and char == letters[seen]:
            seen += 1
    return seen == len(letters)


@dataclass(frozen=True)
class ApprovedAlias:
    """One reviewed alias a question may be matched against."""

    entity_id: str
    entity_type: str
    canonical_name: str
    alias_type: str
    surface: str
    normalized: str
    # The *entity's* normalized name, which is not the alias's own normalized
    # form: an acronym row is stored under "mnre" while the entity it names is
    # stored under "ministry of new and renewable energy". A mention claiming to
    # be that entity has to carry the entity's key, or the resolver's exact-name
    # tier looks up "mnre", finds nothing, and the acronym silently fails to
    # resolve even though recognition worked.
    entity_normalized: str = ""

    @property
    def tokens(self) -> int:
        return len(self.normalized.split())

    @property
    def is_code(self) -> bool:
        return self.alias_type == "code"

    @property
    def is_acronym(self) -> bool:
        return self.alias_type == "acronym"


def _normalized_forms(text: str) -> set[str]:
    """Every normalized key ``text`` could be stored under.

    The alias table's ``normalized`` column was written by these same functions
    during seeding, so asking all three and taking any hit is exact matching
    against the store rather than a similarity guess. It is also what makes this
    module case- and punctuation-insensitive for free: `normalize_project`
    already folds "Eco-city Project - Phase I", "Eco-city Project- Phase I" and
    "Eco-city Project (Phase I)" onto one key.
    """
    from app.knowledge.normalize import (
        normalize_org,
        normalize_person,
        normalize_project,
    )

    forms = set()
    for normalizer in (normalize_person, normalize_org, normalize_project):
        try:
            value = normalizer(text)
        except Exception:  # pragma: no cover - a normalizer must not break a query
            continue
        if value:
            forms.add(value)
    return forms


class ApprovedAliasIndex:
    """Reviewed aliases, keyed by normalized form. Built once, read many."""

    def __init__(self, aliases: dict[str, ApprovedAlias], derived: dict[str, ApprovedAlias]):
        self._by_normalized = aliases
        self._derived_acronyms = derived
        self._max_tokens = min(
            MAX_ALIAS_TOKENS,
            max((a.tokens for a in aliases.values()), default=1),
        )

    def __len__(self) -> int:
        return len(self._by_normalized)

    @property
    def derived_acronyms(self) -> dict[str, ApprovedAlias]:
        return self._derived_acronyms

    def get(self, normalized: str) -> ApprovedAlias | None:
        return self._by_normalized.get(normalized)

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #

    @classmethod
    def load(cls) -> "ApprovedAliasIndex":
        from app.catalog.db import state_table
        from app.core.clients import mysql_connection

        table = state_table()
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT a.entity_id, a.normalized, a.surface, a.alias_type, "
                f"       a.autolink, a.is_ambiguous, e.entity_type, "
                f"       e.canonical_name, e.normalized_name "
                f"FROM `{table}_entity_alias` a "
                f"JOIN `{table}_entity` e ON e.entity_id = a.entity_id "
                f"WHERE e.status = 'active' AND e.claim_eligible = 1"
            )
            rows = list(cur.fetchall())
            cur.execute(
                f"SELECT entity_id, canonical_name, normalized_name "
                f"FROM `{table}_entity` "
                "WHERE entity_type = 'ORGANIZATION' AND status = 'active' "
                "  AND claim_eligible = 1"
            )
            organizations = list(cur.fetchall())
        return cls.build(rows, organizations)

    @classmethod
    def build(
        cls, rows: Iterable[dict[str, Any]], organizations: Iterable[dict[str, Any]] = ()
    ) -> "ApprovedAliasIndex":
        """Build from alias rows and organization rows. Pure, so tests use literals."""
        rows = list(rows)
        # Guard 3 is computed over *every* row for the normalized form, including
        # ones the flags would exclude: a surface recorded as ambiguous anywhere
        # must not become unambiguous because one of its rows happens to pass.
        owners: dict[str, set[str]] = {}
        vetoed: set[str] = set()
        for row in rows:
            normalized = (row.get("normalized") or "").strip()
            if not normalized:
                continue
            owners.setdefault(normalized, set()).add(row["entity_id"])
            if row.get("is_ambiguous"):
                vetoed.add(normalized)

        aliases: dict[str, ApprovedAlias] = {}
        for row in rows:
            normalized = (row.get("normalized") or "").strip()
            if not normalized or normalized in vetoed:
                continue
            if not row.get("autolink") or row.get("is_ambiguous"):
                continue
            if len(owners.get(normalized, ())) != 1:
                continue
            alias = ApprovedAlias(
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                canonical_name=row["canonical_name"],
                alias_type=row["alias_type"],
                surface=row["surface"],
                normalized=normalized,
                entity_normalized=row.get("normalized_name") or normalized,
            )
            if alias.is_acronym and not (
                _ACRONYM_SHAPE.match(alias.surface or "")
                and acronym_matches_name(alias.surface, alias.canonical_name)
            ):
                continue
            aliases[normalized] = alias

        # Acronyms derived from an organization's own authoritative name. Not new
        # data: a deterministic function of `canonical_name`, and the inverse of
        # guard 4. Accepted only when exactly one organization yields the form,
        # and never when the alias table already records that form as ambiguous.
        derived_owners: dict[str, list[dict[str, Any]]] = {}
        for org in organizations:
            acronym = initials_of(org.get("canonical_name") or "")
            if 2 <= len(acronym) <= 8:
                derived_owners.setdefault(acronym, []).append(org)
        derived: dict[str, ApprovedAlias] = {}
        for acronym, owning in derived_owners.items():
            if len(owning) != 1:
                continue
            org = owning[0]
            normalized = acronym.lower()
            if normalized in vetoed or len(owners.get(normalized, ())) > 1:
                continue
            derived[acronym] = ApprovedAlias(
                entity_id=org["entity_id"],
                entity_type="ORGANIZATION",
                canonical_name=org["canonical_name"],
                alias_type="acronym",
                surface=acronym,
                normalized=normalized,
                entity_normalized=org.get("normalized_name") or normalized,
            )
        return cls(aliases, derived)

    # ------------------------------------------------------------------ #
    # Matching
    # ------------------------------------------------------------------ #

    def match(self, question: str) -> list[tuple[int, int, ApprovedAlias]]:
        """Longest-first, non-overlapping alias matches in ``question``."""
        spans = [(m.start(), m.end()) for m in _TOKEN.finditer(question or "")]
        if not spans:
            return []
        found: list[tuple[int, int, ApprovedAlias]] = []
        used: list[tuple[int, int]] = []

        def overlaps(start: int, end: int) -> bool:
            return any(start < u_end and u_start < end for u_start, u_end in used)

        for width in range(min(self._max_tokens, len(spans)), 0, -1):
            for i in range(len(spans) - width + 1):
                start, end = spans[i][0], spans[i + width - 1][1]
                if overlaps(start, end):
                    continue
                text = question[start:end]
                alias = self._lookup(text, width)
                if alias is None:
                    continue
                found.append((start, end, alias))
                used.append((start, end))
        found.sort(key=lambda item: item[0])
        return found

    def _lookup(self, text: str, width: int) -> ApprovedAlias | None:
        # A single upper-case token may be a derived organization acronym even
        # when the alias table has no row for it.
        if width == 1 and _ACRONYM_SHAPE.match(text):
            derived = self._derived_acronyms.get(text.upper())
            if derived is not None and _admissible(derived, text):
                return derived
        for form in _normalized_forms(text):
            alias = self._by_normalized.get(form)
            if alias is not None and _admissible(alias, text):
                return alias
        return None


def _admissible(alias: ApprovedAlias, text: str) -> bool:
    """Whether this alias may be matched by *this* occurrence in a question.

    Admission to the index says the alias is safe to link; this says the string
    in front of us is really being used as that name. The distinction is the
    whole of the common-noun defence, and it is where case is allowed to matter
    again after normalization has ignored it.
    """
    if alias.is_acronym:
        # Case is the signal. `oil` is not "Oil India Limited"; `OIL` is.
        return bool(_ACRONYM_SHAPE.match(text))
    if alias.is_code:
        # A project code is distinctive by construction ("2012MC03"); no casing
        # or length rule adds anything.
        return True
    if alias.entity_type == "PERSON":
        # A person's name is not a common noun, so lower case is not evidence of
        # anything and "dr alok adholeya" is admitted. A single token still is
        # not a person: "Neha" really appears in field_authors.
        return alias.tokens >= 2
    # ORGANIZATION / PROJECT titles and full names.
    if alias.tokens > CASE_SENSITIVE_MAX_TOKENS:
        # Long enough to be distinctive on its own; this is the same threshold
        # `gazetteer.surface_pattern` uses to drop to case-insensitive matching.
        return True
    if alias.tokens == 1:
        # One short word. Admitted only when its *shape* is distinctive rather
        # than its capitalisation: a digit or an internal capital means
        # "Water4Crops" and "HI-AWARE", not "environment".
        return bool(re.search(r"\d", text) or re.search(r"[a-z][A-Z]", text))
    # Two or three tokens: require a capital, which is what separates the
    # division "Water Resources" from the phrase "water resources".
    return any(ch.isupper() for ch in text)


# --------------------------------------------------------------------------- #
# Mentions
# --------------------------------------------------------------------------- #

def lookup_mentions(
    question: str, *, chunk_id: str = "query", document_id: str = "query",
    index: "ApprovedAliasIndex | None" = None,
) -> list[Any]:
    """Mentions for the approved aliases a question names. Never raises.

    The mention carries the alias's **canonical name** as its surface, not the
    string the user typed, so the resolver's exact-name tier finds the entity by
    the name the store knows it by. The span still points at what the user
    actually wrote, which is what keeps entity masking in the router honest.
    """
    from app.knowledge.types import Mention

    try:
        index = index if index is not None else get_index()
        matches = index.match(question)
    except Exception:  # pragma: no cover - recognition must never break a query
        logger.warning("Approved-alias lookup failed.", exc_info=True)
        return []

    mentions: list[Any] = []
    for start, end, alias in matches:
        try:
            mentions.append(
                Mention(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    start_offset=start,
                    end_offset=end,
                    surface_text=alias.canonical_name,
                    normalized_text=alias.entity_normalized or alias.normalized,
                    entity_type=alias.entity_type,
                    # The row really was matched by an exact identifier or an
                    # exact reviewed alias, which is what these two methods mean.
                    extraction_method="identifier" if alias.is_code else "gazetteer",
                    extractor_version="approved-alias-v1",
                    confidence=1.0,
                )
            )
        except Exception:
            logger.debug("Rejected an approved-alias mention.", exc_info=True)
    return mentions


def get_index() -> ApprovedAliasIndex:
    """The process-wide index, rebuilt at most once per TTL."""
    global _index, _loaded_at
    with _lock:
        if _index is not None and time.monotonic() - _loaded_at < INDEX_TTL_SECONDS:
            return _index
    loaded = ApprovedAliasIndex.load()
    with _lock:
        _index = loaded
        _loaded_at = time.monotonic()
    logger.info("Approved-alias index: %d alias(es), %d derived acronym(s).",
                len(loaded), len(loaded.derived_acronyms))
    return loaded


def reset_index_cache() -> None:
    """Force the next lookup to reload. For tests and after a re-seed."""
    global _index, _loaded_at
    with _lock:
        _index = None
        _loaded_at = 0.0
