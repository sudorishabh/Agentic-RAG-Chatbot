"""Formatting normalization for author names — and nothing more.

Drupal stores authors as free text, so the same person is written several ways.
This module collapses the differences that are provably **formatting**, and
refuses to go further.

What it does
------------
Unicode form, whitespace, case, punctuation, and a leading courtesy title. Each
of those changes how a name is *written* without changing *which name is
written*, so collapsing them asserts nothing about people.

What it deliberately does not do
--------------------------------
It does not reorder tokens. ``"Datta Debajit"`` and ``"Debajit Datta"`` are left
as two names, because deciding they are one person is an inference about naming
convention, not a fact about formatting — and the investigation behind this
module found no evidence in the corpus that could settle it: Drupal exposes no
author id, no email and no reference, and the graph's person entities for
authors are all `provisional`. There is also no safe general rule; token
permutation would merge any two people whose names are anagrams.

Measured on the live catalog: 975 raw strings -> 955 normalized, 20 groups. The
55 order-variant groups are left separate, which under-reports rather than
inventing a merge. That is the correct direction of error here.

The raw value is never destroyed — `documents_author.author` keeps exactly what
Drupal sent, and this result is stored beside it (see
`app.catalog.state._replace_authors`), the same way `documents_theme` keeps the
theme name beside its derived group.
"""
from __future__ import annotations

import re
import unicodedata

# Courtesy titles that may precede a name. Order matters only for readability;
# the matcher is anchored and applied repeatedly.
TITLES: tuple[str, ...] = (
    "dr", "mr", "mrs", "ms", "miss", "prof", "professor",
    "shri", "smt", "sh", "er", "late",
)

_TITLE = re.compile(
    r"^(?:" + "|".join(TITLES) + r")\.?\s+", re.IGNORECASE
)
_PUNCT = re.compile(r"[.,;]")
_WS = re.compile(r"\s+")

# A title is only stripped while at least this many tokens survive it. Without
# the guard, "Shri Prakash" — a real person, 24 documents — normalizes to
# "prakash", because "Shri" is both a courtesy title and a common given name.
# The guard costs nothing (the same 955 identities either way) and keeps the
# name intact.
MIN_TOKENS_AFTER_TITLE = 2


def normalize(raw: str | None) -> str:
    """The formatting-normalized form of an author name.

    Deterministic, and idempotent: ``normalize(normalize(x)) == normalize(x)``.
    Returns "" for an empty or whitespace-only value, which the write path
    treats as "no derived form" rather than storing a blank identity.
    """
    if not raw:
        return ""
    # NFKC folds compatibility forms (non-breaking spaces, full-width letters)
    # onto their ordinary equivalents; without it two visually identical names
    # stay distinct.
    text = unicodedata.normalize("NFKC", str(raw))
    text = _WS.sub(" ", _PUNCT.sub(" ", text)).strip().casefold()
    if not text:
        return ""
    while True:
        match = _TITLE.match(text)
        if match is None:
            break
        remainder = text[match.end():].strip()
        if len(remainder.split()) < MIN_TOKENS_AFTER_TITLE:
            break
        text = remainder
    return text
