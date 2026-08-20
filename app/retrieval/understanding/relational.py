"""What relationship a question asks about: the closed predicate vocabulary.

Moved here from the graph package's ``intent`` module because it is *query
understanding*, not graph retrieval. Reading a predicate cue out of a question
needs no Neo4j, no template and no traversal — only the approved vocabulary — and
three layers now need it: the graph router (to plan a hop), the facet builder (to
tell a relationship's validity window from a document's publication date), and
intent classification (to know that a relational question is not small talk).

The dependency runs one way, and this file is why: understanding owns the cue
vocabulary and the graph package imports it. The reverse would have pulled graph
retrieval into the general retrieval path, which
``tests/test_graph_retrieval.py`` forbids for good reason — graph *retrieval*
must keep exactly one doorway, and it is the one in ``retriever.py``.

Cues live beside the vocabulary rather than in a route table, so an approved
predicate becomes askable by declaring how people say it, not by adding a branch
to a router.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Relational readings
# --------------------------------------------------------------------------- #

# How this corpus says each approved predicate. Keyed by predicate name, so a
# predicate added to the vocabulary becomes askable by adding its cues here —
# not by adding a route, a class or a template.
#
# Cues are matched as whole words against the question. Overlaps between
# predicates are expected and are resolved by entity type: "part of" reaches
# both MEMBER_OF (a person in an organization) and PARENT_OF (an organization in
# an organization), and the resolved entity's type decides which is meant.
PREDICATE_CUES: dict[str, tuple[str, ...]] = {
    "FUNDED_BY": (
        "fund", "funds", "funded", "funder", "funders", "funding", "finance",
        "finances", "financed", "financing", "sponsor", "sponsors", "sponsored",
        "sponsorship", "grant", "grants", "granted", "donor", "donors",
        "bankroll", "bankrolled", "underwrite", "underwritten", "money from",
        "paid for", "financial support",
    ),
    "LED_BY": (
        "lead", "leads", "leading", "led", "leader", "leaders", "leadership",
        "head", "heads", "headed", "heading", "run", "runs", "ran", "running",
        "principal investigator", "principal investigators", "pi", "pis",
        "in charge", "oversee", "oversees", "oversaw", "manage", "manages",
        "managed", "manager", "directed", "spearhead", "spearheaded",
    ),
    "PARTNER_OF": (
        "partner", "partners", "partnered", "partnering", "partnership",
        "partnerships", "collaborate", "collaborates", "collaborated",
        "collaborating", "collaboration", "collaborations", "collaborator",
        "collaborators", "in association with", "jointly", "joint",
        "consortium", "alliance", "allied", "teamed up", "works with",
        "worked with", "delivered with",
    ),
    "WORKS_AT": (
        "work", "works", "worked", "working", "employ", "employs", "employed",
        "employee", "employees", "employer", "employers", "employment",
        "job", "jobs", "based at", "affiliated", "affiliation", "affiliations",
        "staff", "on the payroll",
    ),
    "MEMBER_OF": (
        "member", "members", "membership", "memberships", "belong", "belongs",
        "belonged", "sits on", "sit on", "sat on", "serves on", "served on",
        "board", "boards", "committee", "committees", "council", "panel",
    ),
    # Deliberately narrow, and every cue is a *relational* phrase rather than an
    # organizational noun. "department", "centre", "unit" and "division" were
    # tried and removed: this corpus is full of organizations whose names
    # contain them, so they matched the question's own subject and turned every
    # question about the Department of Biotechnology into a question about its
    # internal structure. Entity spans are masked before matching (see
    # `router._mask_entities`), but a bare noun would still fire on the
    # surrounding prose, and "which department funded X" is not a PARENT_OF
    # question.
    "PARENT_OF": (
        "parent", "parent organisation", "parent organization", "subsidiary",
        "subsidiaries", "a unit of", "a division of", "a centre of",
        "a center of", "a department of", "a branch of", "owns", "owned by",
        "under the umbrella", "sub-unit", "sub-units",
    ),
    "HAS_ROLE": (
        "role", "roles", "title", "titles", "designation", "designations",
        "position", "positions", "post", "posts", "job title", "designated",
    ),
}

# Cues that say which way round a symmetric-domain question runs. PARENT_OF is
# the only predicate whose domain and range are the same type, so an anchor
# organization could be either end; these decide which.
_INVERSE_CUES = re.compile(
    r"\b(?:part of|belongs to|belong to|under|within|owned by|a unit of|"
    r"a division of|a centre of|a center of|sits under|parent of\s+which|"
    r"whose parent|which organi[sz]ation)\b",
    re.IGNORECASE,
)


def _cue_positions(question: str) -> dict[str, int]:
    """First character offset at which each predicate's cue appears.

    Offsets rather than a set, because a two-hop question is read in the order
    its relationships are named: "who leads projects funded by X" names LED_BY
    before FUNDED_BY, and the chain is built from the anchor outward.
    """
    text = (question or "").lower()
    found: dict[str, int] = {}
    for predicate, cues in PREDICATE_CUES.items():
        best: int | None = None
        for cue in cues:
            # Whole-word (or whole-phrase) match, so "run" does not fire on
            # "running costs" via a substring and "pi" does not fire on "pipe".
            match = re.search(rf"(?<!\w){re.escape(cue)}(?!\w)", text)
            if match and (best is None or match.start() < best):
                best = match.start()
        if best is not None:
            found[predicate] = best
    return found


@dataclass(frozen=True)
class RelationalIntent:
    """The approved predicates a question names, in the order it names them."""

    predicates: tuple[str, ...] = ()
    inverse_hint: bool = False
    # Where each predicate's cue was found, as a character offset into the
    # question. Kept because "in the order it names them" is not enough to build
    # a two-hop chain: the router has to know which relationship was named
    # *nearest the anchor entity*, and that is a distance, not a rank. See
    # `router._nearest_first`.
    offsets: dict[str, int] = field(default_factory=dict)

    @property
    def is_relational(self) -> bool:
        return bool(self.predicates)


def read_relational(question: str) -> RelationalIntent:
    """Which approved predicates a question is about, most-named first.

    Only predicates in the closed vocabulary can be returned: the cue table is
    keyed by predicate name and every key is checked against the vocabulary, so
    a cue left behind for a retired predicate cannot resurrect it.
    """
    from app.knowledge.claims import predicates as vocab

    positions = {
        name: offset
        for name, offset in _cue_positions(question).items()
        if vocab.is_known(name)
    }
    ordered = tuple(sorted(positions, key=lambda name: positions[name]))
    return RelationalIntent(
        predicates=ordered,
        inverse_hint=bool(_INVERSE_CUES.search(question or "")),
        offsets=positions,
    )

