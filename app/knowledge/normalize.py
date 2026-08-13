"""Name normalization for the knowledge layer.

Normalization exists to make two spellings of the same name compare equal
*without* making two different names compare equal. Every rule here is
type-aware for that reason: stripping "Dr" is right for a person and wrong for
an organization ("Dr Reddy's Laboratories"), and folding "&" to "and" is right
for an organization and meaningless for a person.

The normalized form is a **blocking and comparison key only**. It is never
displayed, never stored as the canonical name, and never used as an identity by
itself — resolution (a later phase) decides identity, and this only decides what
is worth comparing. That distinction is what keeps aggressive folding safe here.
"""
from __future__ import annotations

import re
import unicodedata

# Titles that precede a personal name in this corpus. Stripped for PERSON only.
# "Er" (Engineer) and the Indic honorifics appear in TERI author fields.
_HONORIFICS = frozenset(
    """
    dr dr. mr mr. mrs mrs. ms ms. miss prof prof. professor shri smt sri sh
    er er. adv adv. hon hon. late rev rev.
    """.split()
)

# Post-nominals carry no identity: two "Sharma"s are not distinguished by one
# holding a PhD.
_SUFFIXES = frozenset("phd ph.d md m.d jr sr ii iii iv esq".split())

# Legal / structural forms an organization's name may or may not be written
# with. Folded to a single spelling rather than dropped, because "X Limited" and
# "X Ltd" are the same organization while "X" alone may not be.
_ORG_FORMS = {
    "ltd": "limited",
    "pvt": "private",
    "pvt.": "private",
    "co": "company",
    "corp": "corporation",
    "inc": "incorporated",
    "intl": "international",
    "univ": "university",
    "dept": "department",
    "govt": "government",
    "org": "organisation",
    "organization": "organisation",
}

_WHITESPACE = re.compile(r"\s+")
# Keep intra-word punctuation out of the key, but do not let removal join two
# words: "Asia-Pacific" and "Asia Pacific" must land on the same key.
_PUNCT_TO_SPACE = re.compile(r"[-–—/\\_,;:()\[\]{}\"“”'’`]+")
_PUNCT_DROP = re.compile(r"[.!?*]+")
# A period *between two letters* separates them — "R.K." is two initials, and
# dropping the period outright yields "rk", which no longer matches "R K".
# Restricted to letters on both sides so a decimal ("PM2.5") is left alone.
_DOT_BETWEEN_LETTERS = re.compile(r"(?<=[a-z])\.(?=[a-z])")
# A digit glued to the end of a name is a data artifact in this corpus
# ("Asha Ram Sihag2" appears in field_authors), not part of anyone's name.
_TRAILING_DIGITS = re.compile(r"(?<=[a-z])\d+$")


def _fold(text: str) -> str:
    """Case, accent and whitespace folding shared by every entity type."""
    if not text:
        return ""
    # NFKD splits an accented character into base + combining mark, so dropping
    # the marks leaves ASCII: "Zusammenarbeit für" -> "zusammenarbeit fur".
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = stripped.casefold()
    separated = _DOT_BETWEEN_LETTERS.sub(" ", lowered)
    spaced = _PUNCT_TO_SPACE.sub(" ", separated)
    dropped = _PUNCT_DROP.sub("", spaced)
    return _WHITESPACE.sub(" ", dropped).strip()


def normalize(text: str) -> str:
    """Type-agnostic fold. Use when the entity type is unknown."""
    return _fold(text)


def normalize_person(text: str) -> str:
    """Fold a personal name: honorifics, post-nominals and OCR digit artifacts
    removed, initials reduced to bare letters.

    Initials are the corpus's hardest case — "R K Pachauri", "R.K. Pachauri" and
    "Dr R K Pachauri" must agree — so punctuation is dropped *before* tokens are
    inspected and single letters are kept as tokens rather than discarded. They
    are weak evidence, but discarding them would make "R K Pachauri" and
    "S K Pachauri" identical, which is a false merge waiting to happen.
    """
    tokens = _fold(text).split()
    while tokens and tokens[0] in _HONORIFICS:
        tokens.pop(0)
    while tokens and tokens[-1] in _SUFFIXES:
        tokens.pop()
    if tokens:
        tokens[-1] = _TRAILING_DIGITS.sub("", tokens[-1])
    return " ".join(t for t in tokens if t)


def normalize_org(text: str) -> str:
    """Fold an organization name: ampersands spelled out, legal forms
    regularised. Honorifics are *not* stripped — "Dr Reddy's Laboratories" is an
    organization whose name begins with one."""
    folded = _fold(text.replace("&", " and "))
    return " ".join(_ORG_FORMS.get(t, t) for t in folded.split() if t)


def normalize_project(text: str) -> str:
    """Fold a project name. Projects are titled like sentences here, so only the
    generic fold applies; leading articles are dropped because "The Solar
    Mission" and "Solar Mission" are one project."""
    tokens = _fold(text).split()
    if tokens and tokens[0] in ("the", "a", "an"):
        tokens.pop(0)
    return " ".join(tokens)


# Entity type -> normalizer. The single place the mapping lives, so extraction,
# the gazetteer and any later resolver cannot disagree about what a key means.
NORMALIZERS = {
    "PERSON": normalize_person,
    "ORGANIZATION": normalize_org,
    "PROJECT": normalize_project,
}


def normalize_for(entity_type: str, text: str) -> str:
    """Normalize by entity type, falling back to the generic fold."""
    return NORMALIZERS.get(entity_type, normalize)(text)


def initials_of(normalized_person: str) -> str:
    """First letters of a normalized personal name — the blocking key that lets
    "r k pachauri" and "rajendra kumar pachauri" be *considered* as candidates.
    Deliberately not an identity test: it is a wide net, not a match."""
    return "".join(token[0] for token in normalized_person.split() if token)


def is_initials_only(normalized_person: str) -> bool:
    """Whether a name is nothing but initials ("a k", "r"). Such a mention can
    never safely stand alone: it names nobody in particular, and this corpus's
    author facet is full of them."""
    tokens = normalized_person.split()
    return bool(tokens) and all(len(t) == 1 for t in tokens)
