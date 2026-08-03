"""Which queries should let recency weigh more heavily.

Retrieval ranks relevance first and settles ties on recency (see
:mod:`app.retrieval.reranker`). How often that tie-break gets to fire is set by
the band tolerance — and how wide "similarly relevant" *should* be depends on the
topic. On a stable one, an older passage that answers better is simply the better
answer. On a volatile one — pricing, an API, a regulation, an announcement — an
older passage can be precisely and confidently wrong, so a wider band earns its
keep: the newer of two comparable passages leads more often, while a real
relevance gap still settles the ranking exactly as before.

Matched lexically against the *rewritten* query (pronouns already resolved by
query understanding), not asked of an LLM. This is a ranking nudge, not a routing
decision: a wrong call costs a marginally wider or narrower band, which does not
justify a model call's latency, cost and variance on every single search.

For the same reason the lexicon leans inclusive — over-matching widens a band a
little, and relevance still decides across bands, whereas a miss silently leaves
two editions of the same document ordered by a hair of cosine noise. On a policy-
or regulation-heavy corpus most queries will read as volatile; that is the
intended reading rather than a misfire, and `rerank_relevance_tolerance` is the
knob to reach for if the resulting bands are too wide.
"""

from __future__ import annotations

import re

# What the question is *about*, when the answer has a shelf life.
_VOLATILE_TOPICS: tuple[str, ...] = (
    # Software and product surfaces
    r"api(?:s)?", r"sdk(?:s)?", r"endpoint(?:s)?", r"changelog(?:s)?",
    r"release(?:s|d)?", r"version(?:s)?", r"deprecat\w+", r"migration(?:s)?",
    r"upgrade(?:s|d)?", r"roadmap(?:s)?", r"documentation", r"docs",
    # Money
    r"pric(?:e|es|ing)", r"cost(?:s)?", r"tariff(?:s)?", r"fee(?:s)?",
    r"subsid(?:y|ies)", r"budget(?:s)?",
    # Rules
    r"polic(?:y|ies)", r"regulation(?:s)?", r"regulatory", r"guideline(?:s)?",
    r"compliance", r"mandate(?:s|d)?", r"amendment(?:s)?", r"notification(?:s)?",
    r"standard(?:s)?", r"target(?:s)?", r"deadline(?:s)?", r"law(?:s)?",
    # Things that are news by definition
    r"announcement(?:s)?", r"announced", r"launch(?:es|ed)?",
    r"press release(?:s)?", r"update(?:s|d)?", r"statement(?:s)?",
)

# Cues that the user asked for the state of affairs *now*, whatever the topic.
_RECENCY_CUES: tuple[str, ...] = (
    r"latest", r"newest", r"most recent", r"recent(?:ly)?", r"current(?:ly)?",
    r"today", r"this year", r"right now", r"up[- ]to[- ]date", r"so far",
    r"as of",
)

_VOLATILE_RE = re.compile(
    r"\b(?:" + "|".join(_VOLATILE_TOPICS + _RECENCY_CUES) + r")\b", re.IGNORECASE
)


def is_volatile(query: str) -> bool:
    """True when `query` is about something that goes out of date, or asks for
    the current state of it."""
    return bool(query and _VOLATILE_RE.search(query))
