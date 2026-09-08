"""Query-time recognition of a project named by *part* of its title.

Why this exists
---------------
Gazetteer matching is exact: the whole stored title has to appear in the text.
That is right for prose, and it is why a project is recognised at all. It is
wrong for a question, because nobody types a 14-word CMS title. Measured
directly:

    "Who funds Films on Energy Efficiency for IREDA?"   -> matched
    "Who funds Films on Energy Efficiency?"             -> no mention at all
    "Who leads Heavy metal assessment of Yamuna River Water?"  -> matched
    "Who leads the Yamuna River Water project?"         -> no mention at all

The miss happens before resolution, so no veto, tier or trust rule is even
consulted — the question simply names nothing.

What makes it safe
------------------
The same thing that makes :mod:`app.retrieval.understanding.approved_aliases`
safe, and it is worth being explicit that this is a recognition change and not
an identity one:

* **Query-only.** Ingestion writes claims, so widening what *it* links changes
  what is asserted. Widening what a question may look up changes only what can
  be found. Nothing here is reachable from the ingest path.
* **It resolves nothing.** It turns a run of words into a
  :class:`~app.knowledge.types.Mention` carrying the project's *canonical name*,
  and the unchanged resolver then decides identity, trust and eligibility. Every
  veto still applies.
* **Uniqueness is the veto.** A run of words is only admitted when exactly one
  project title in the whole corpus contains it. A phrase shared by two projects
  identifies neither, and is dropped rather than guessed at — the same rule
  guard 3 of ``approved_aliases`` uses on the alias table.

Why a contiguous run, and why three tokens
------------------------------------------
Contiguous because it is the cheap, checkable version of "the user quoted part
of the title": word order is preserved and nothing is inferred. Three tokens and
twelve characters because those are already
``gazetteer._MIN_PROJECT_TOKENS`` / ``_MIN_PROJECT_CHARS`` — the corpus's own
answer to how much of a project title is enough to mean it, given titles like
"Steel" and "Summary" really exist.

Measured on the 1,071 claim-eligible projects: 99% have a 3-to-5 token run that
occurs in no other title, so the uniqueness guard rejects far less than it
sounds like it would.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Reused from `approved_aliases`, for the same reason: an index built per query
# would put a MySQL round trip on the read path, and the project set only
# changes when the knowledge layer re-seeds.
INDEX_TTL_SECONDS = 300.0

# The shingle width. Everything is indexed at this width and longer matches are
# grown from adjacent shingles, so the index stays one dict rather than one per
# possible length.
SHINGLE_TOKENS = 3

# Floors on what may be admitted as naming a project, in normalized form.
# Deliberately the same numbers as `gazetteer._MIN_PROJECT_TOKENS` and
# `_MIN_PROJECT_CHARS`.
MIN_MATCH_TOKENS = 3
MIN_MATCH_CHARS = 12

# A matched run must contain at least one token this rare across project
# titles, as a share of them.
#
# Uniqueness alone is not distinctiveness, and the gap is not theoretical: "the
# project on" and "project on solar" each occur in exactly one title, so the
# uniqueness guard admitted them and "Who leads the project on solar energy?" —
# a generic question naming no project — matched two. Measured document
# frequency over the 1,054 indexed titles separates the two cases cleanly:
# `on` 188, `the` 172, `project` 67, `solar` 38, against `yamuna` 4, `river` 6,
# `films` 2, `ireda` 1. At 1% of titles the floor sits between them.
#
# Relative rather than absolute so it keeps meaning if the corpus grows, with a
# small absolute minimum so a tiny corpus does not make every token "rare".
DISTINCTIVE_DF_SHARE = 0.01
DISTINCTIVE_DF_FLOOR = 2

# The provenance stamp. Distinct from `approved-alias-v1` on purpose: these
# mentions were matched by a *part* of a reviewed title, not by a whole reviewed
# alias, and anything downstream deciding what a query may do with them should
# be able to tell the two apart.
EXTRACTOR_VERSION = "partial-title-v1"

# Token spans in a question, so a mention's offsets index the original text.
# Same shape as `approved_aliases._TOKEN`.
_TOKEN = re.compile(r"[^\W_]+(?:[.'’&/-][^\W_]+)*", re.UNICODE)

_lock = threading.Lock()
_index: "PartialTitleIndex | None" = None
_loaded_at = 0.0


@dataclass(frozen=True)
class PartialTitleMatch:
    """One project named by part of its title."""

    entity_id: str
    canonical_name: str
    normalized_name: str
    start: int
    end: int


@dataclass
class PartialTitleIndex:
    """Contiguous title shingles -> the projects whose titles contain them."""

    #: shingle -> the entity ids whose normalized title contains it. A shingle
    #: owned by more than one project is kept, not dropped: the count is what
    #: the uniqueness guard reads.
    owners: dict[str, set[str]] = field(default_factory=dict)
    #: entity id -> (canonical_name, normalized_name)
    projects: dict[str, tuple[str, str]] = field(default_factory=dict)
    #: normalized token -> how many titles contain it, for the distinctiveness
    #: guard. See DISTINCTIVE_DF_SHARE.
    token_df: dict[str, int] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.projects)

    @property
    def _distinctive_max_df(self) -> int:
        return max(DISTINCTIVE_DF_FLOOR, int(len(self.projects) * DISTINCTIVE_DF_SHARE))

    def is_distinctive(self, token: str) -> bool:
        """Whether one token is rare enough across titles to carry a match."""
        return self.token_df.get(token, 0) <= self._distinctive_max_df

    @classmethod
    def load(cls) -> "PartialTitleIndex":
        """Build from the claim-eligible, active projects in the entity store.

        Eligibility is filtered here rather than after matching so an entity a
        question must not reach cannot even contribute a shingle.
        """
        from app.catalog.db import state_table
        from app.core.clients import mysql_connection
        from app.knowledge.normalize import normalize_project

        table = state_table()
        index = cls()
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT entity_id, canonical_name FROM `{table}_entity` "
                "WHERE entity_type = 'PROJECT' AND status = 'active' "
                "AND claim_eligible = 1"
            )
            rows = cur.fetchall()

        for row in rows:
            canonical = (row["canonical_name"] or "").strip()
            if not canonical:
                continue
            normalized = normalize_project(canonical)
            tokens = normalized.split()
            if len(tokens) < SHINGLE_TOKENS:
                # Too short to be found by a part of itself. The gazetteer's
                # exact pass still matches it whole.
                continue
            index.projects[row["entity_id"]] = (canonical, normalized)
            for token in set(tokens):
                index.token_df[token] = index.token_df.get(token, 0) + 1
            for i in range(len(tokens) - SHINGLE_TOKENS + 1):
                shingle = " ".join(tokens[i : i + SHINGLE_TOKENS])
                index.owners.setdefault(shingle, set()).add(row["entity_id"])
        return index

    def match(self, question: str) -> list[PartialTitleMatch]:
        """The projects this question names part of. At most one span each.

        Grows each match to the longest consecutive run of question tokens whose
        shingles all point at the same single project, so the span reported is
        the whole of what the user quoted rather than its first three words.
        """
        from app.knowledge.normalize import normalize

        spans = [(m.group(0), m.start(), m.end()) for m in _TOKEN.finditer(question)]
        normalized = [normalize(text) for text, _, _ in spans]
        # A token that folds away (punctuation-only) would silently shift every
        # shingle, so those positions are dropped from both lists together.
        kept = [i for i, tok in enumerate(normalized) if tok]
        if len(kept) < MIN_MATCH_TOKENS:
            return []

        best: dict[str, tuple[int, int, int]] = {}  # entity -> (tokens, start, end)
        run_owner: str | None = None
        run_start_k = 0
        for k in range(len(kept) - SHINGLE_TOKENS + 1):
            shingle = " ".join(normalized[kept[j]] for j in range(k, k + SHINGLE_TOKENS))
            holders = self.owners.get(shingle)
            # Uniqueness is the guard: a phrase two projects share names
            # neither of them.
            owner = next(iter(holders)) if holders and len(holders) == 1 else None
            if owner is not None and owner == run_owner:
                pass  # the run continues
            else:
                if run_owner is not None:
                    self._record(
                        best, run_owner, kept, run_start_k, k, spans, normalized
                    )
                run_owner, run_start_k = owner, k
        if run_owner is not None:
            self._record(
                best, run_owner, kept, run_start_k,
                len(kept) - SHINGLE_TOKENS + 1, spans, normalized,
            )

        out: list[PartialTitleMatch] = []
        for entity_id, (_, start, end) in best.items():
            canonical, normalized_name = self.projects[entity_id]
            out.append(
                PartialTitleMatch(
                    entity_id=entity_id, canonical_name=canonical,
                    normalized_name=normalized_name, start=start, end=end,
                )
            )
        return sorted(out, key=lambda m: m.start)

    def _record(
        self, best: dict[str, tuple[int, int, int]], entity_id: str,
        kept: list[int], from_k: int, to_k: int, spans: list[tuple[str, int, int]],
        normalized: list[str],
    ) -> None:
        """Keep the longest span found for one project, if it clears the floors."""
        first_token = kept[from_k]
        last_token = kept[to_k - 1 + SHINGLE_TOKENS - 1]
        token_count = (to_k - 1 - from_k) + SHINGLE_TOKENS
        if token_count < MIN_MATCH_TOKENS:
            return
        start, end = spans[first_token][1], spans[last_token][2]
        if end - start < MIN_MATCH_CHARS:
            return
        # Uniqueness got us here; distinctiveness decides whether the run says
        # anything. A span of nothing but corpus-wide filler ("the project on")
        # can be unique by accident and names no project.
        matched = [normalized[kept[j]] for j in range(from_k, to_k - 1 + SHINGLE_TOKENS)]
        if not any(self.is_distinctive(token) for token in matched):
            return
        current = best.get(entity_id)
        if current is None or token_count > current[0]:
            best[entity_id] = (token_count, start, end)


def lookup_mentions(
    question: str, *, chunk_id: str = "query", document_id: str = "query",
    index: "PartialTitleIndex | None" = None,
) -> list[Any]:
    """Mentions for the projects a question names part of. Never raises.

    Carries the project's canonical name as the surface, so the resolver's
    exact-name tier finds it by the name the store knows it by, while the span
    still points at what the user actually wrote — which is what keeps the
    router's entity masking honest.
    """
    from app.knowledge.types import Mention

    try:
        index = index if index is not None else get_index()
        matches = index.match(question)
    except Exception:  # pragma: no cover - recognition must never break a query
        logger.warning("Partial-title lookup failed.", exc_info=True)
        return []

    mentions: list[Any] = []
    for match in matches:
        try:
            mentions.append(
                Mention(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    start_offset=match.start,
                    end_offset=match.end,
                    surface_text=match.canonical_name,
                    normalized_text=match.normalized_name,
                    entity_type="PROJECT",
                    # Matched against the reviewed title set, not spotted in
                    # prose, which is what this method means elsewhere.
                    extraction_method="gazetteer",
                    extractor_version=EXTRACTOR_VERSION,
                    confidence=1.0,
                )
            )
        except Exception:
            logger.debug("Rejected a partial-title mention.", exc_info=True)
    return mentions


def get_index() -> PartialTitleIndex:
    """The process-wide index, rebuilt at most once per TTL."""
    global _index, _loaded_at
    with _lock:
        if _index is not None and time.monotonic() - _loaded_at < INDEX_TTL_SECONDS:
            return _index
    loaded = PartialTitleIndex.load()
    with _lock:
        _index = loaded
        _loaded_at = time.monotonic()
    logger.info(
        "Partial-title index: %d project(s), %d shingle(s).",
        len(loaded), len(loaded.owners),
    )
    return loaded


def reset_index_cache() -> None:
    """Force the next lookup to reload. For tests and after a re-seed."""
    global _index, _loaded_at
    with _lock:
        _index = None
        _loaded_at = 0.0
