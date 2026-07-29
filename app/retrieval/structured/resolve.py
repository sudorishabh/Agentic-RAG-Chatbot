"""Entity resolution: free-text query -> ranked canonical entity candidates.

Maps loose, synonym-heavy user phrasing ("rishab negi", "env theme") onto the
catalog's known authors, bundles, and themes. No new infrastructure — plain
normalization plus `difflib`, scored in Python over each type's small candidate
set (16 bundles, ~200 themes, low hundreds of authors), per the
no-new-dependency constraint in docs/database-retrieval-redesign.md §3, §4.

See docs/database-retrieval-redesign.md §4 for the design and the worked
examples the thresholds below were tuned against.
"""

from __future__ import annotations

import difflib
import re

ACCEPT = "accept"
AMBIGUOUS = "ambiguous"
MISS = "miss"

# A near-exact score always accepts regardless of the runner-up; a moderate
# score only accepts when it clearly dominates every alternative (no real
# competition) — otherwise it is ambiguous down to the floor, and a miss below
# it. Tuned against docs/database-retrieval-redesign.md §4's worked examples:
# "climate" -> Climate Change must accept (dominant, if not near-exact), while
# "rishab" -> Rishabh Negi / Rishab Nigam must not (a genuine tie).
_ACCEPT_SCORE = 0.90
_ACCEPT_FLOOR = 0.60
_ACCEPT_MARGIN = 0.30
_AMBIGUOUS_FLOOR = 0.60

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")

# Domain-generic descriptor words a user adds around the entity name itself
# ("env THEME", "policy BRIEF", "the THEME of waste") rather than being part of
# it — stripped from the query before scoring so they cannot dilute a match
# against the one word that actually names the entity. Never applied to the
# candidate side, and never strips a query down to nothing (see
# `_content_tokens`).
_FILLER_WORDS = frozenset(
    {"theme", "themes", "bundle", "bundles", "tag", "tags", "type", "category"}
)


def _normalize(value: str) -> str:
    """Casefold and collapse whitespace, treating punctuation as a word
    boundary rather than deleting it — "Rishabh-Negi" must tokenize the same
    as "Rishabh Negi", not merge into one word ("rishabhnegi") that no longer
    matches at all."""
    text = _PUNCT.sub(" ", value or "").casefold()
    return _WHITESPACE.sub(" ", text).strip()


def _content_tokens(tokens: list[str]) -> list[str]:
    """Query tokens with filler words removed, unless that would strip every
    token — an all-filler query still compares as typed rather than as empty."""
    kept = [t for t in tokens if t not in _FILLER_WORDS]
    return kept or tokens


def _token_set_ratio(a: str, b: str) -> float:
    """Word-order-insensitive similarity: sort each side's tokens before
    comparing, so "negi rishabh" and "Rishabh Negi" compare as equal."""
    ta = sorted(a.split())
    tb = sorted(b.split())
    return difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()


def _prefix_score(query_tokens: list[str], candidate_tokens: list[str]) -> float:
    """A single strong abbreviation/prefix match ("env" -> "Environment"),
    discounted by how much of the candidate that one token represents — an
    exact hit on the first word of a four-word candidate must not outscore an
    exact hit on a one-word candidate, or "environment" would tie "Environment"
    against "Environment and Public Health" instead of preferring the exact
    name. Only fires for a single-token query: with more than one token, a lone
    strong pair match says nothing about whether the OTHER tokens also
    correspond (two different people can share a first name) — see
    `_token_set_ratio` / the whole-string ratio in `score` for the multi-token
    case instead."""
    if len(query_tokens) != 1:
        return 0.0
    qt = query_tokens[0]
    if len(qt) < 3 or not candidate_tokens:
        return 0.0
    coverage = 1.0 / len(candidate_tokens)
    best = 0.0
    for ct in candidate_tokens:
        if qt == ct:
            best = max(best, 0.5 + 0.5 * coverage)
        elif ct.startswith(qt) or qt.startswith(ct):
            shorter, longer = sorted((len(qt), len(ct)))
            best = max(best, (0.5 + 0.5 * coverage) * (0.6 + 0.4 * (shorter / longer)))
    return best


def score(query: str, candidate: str) -> float:
    """Similarity in [0, 1] between a free-text query and one candidate name —
    the max of a whole-string ratio, a word-order-insensitive ratio, a
    single-token prefix/abbreviation match, and a length-aware substring boost.
    An empty query or candidate never matches (0.0), and a query that equals
    the candidate after normalization always scores 1.0."""
    q_raw, c = _normalize(query), _normalize(candidate)
    if not q_raw or not c:
        return 0.0
    q_tokens = _content_tokens(q_raw.split())
    q = " ".join(q_tokens)
    if q == c:
        return 1.0
    candidates = [
        difflib.SequenceMatcher(None, q, c).ratio(),
        _token_set_ratio(q, c),
        _prefix_score(q_tokens, c.split()),
    ]
    if q in c or c in q:
        shorter, longer = (q, c) if len(q) <= len(c) else (c, q)
        candidates.append(0.5 + 0.5 * (len(shorter) / len(longer)))
    return max(candidates)


def classify_band(top_score: float, runner_up_score: float = 0.0) -> str:
    """ACCEPT / AMBIGUOUS / MISS from the best score and the next-best score.

    ACCEPT is either a near-exact top score on its own, or a moderate score
    with a clear lead over the runner-up (no real competition) — a moderate
    score with an equally moderate second guess is ambiguous, not a guess to
    make silently. See docs/database-retrieval-redesign.md §4 for the worked
    examples these thresholds were tuned against."""
    dominant = top_score >= _ACCEPT_FLOOR and (top_score - runner_up_score) >= _ACCEPT_MARGIN
    if top_score >= _ACCEPT_SCORE or dominant:
        return ACCEPT
    if top_score >= _AMBIGUOUS_FLOOR:
        return AMBIGUOUS
    return MISS
