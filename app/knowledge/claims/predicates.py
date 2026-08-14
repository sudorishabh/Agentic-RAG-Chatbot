"""The closed predicate vocabulary.

Closed on purpose. A model that can invent a relationship type can assert
anything, and no downstream validation could tell an invented predicate from a
real one. Everything here is grounded in something this corpus actually
carries — the CMS sponsor field, division membership, the role phrasing that
recurs in event agendas — rather than in what a knowledge graph might
conventionally have.

Each predicate declares the entity types it may join. Those domains and ranges
are the type system for claims: a claim whose subject or object sits outside
them is rejected before staging, which is what stops "TERI LED_BY Delhi" being
storable at all.

Direction is canonical and single. ``PROJECT --FUNDED_BY--> ORGANIZATION``
exists; the inverse does not, because two spellings of one fact would have to be
kept consistent forever.
"""
from __future__ import annotations

from dataclasses import dataclass

# Object kinds a predicate may take. A literal object is a value, not an
# identity, so it can never be an entity reference by accident.
OBJECT_ENTITY = "entity"
OBJECT_TEXT = "literal:text"


@dataclass(frozen=True)
class Predicate:
    """One relationship type, and the shape of claim it licenses."""

    name: str
    description: str
    # Entity types the subject may be. Empty is never valid.
    domain: tuple[str, ...]
    # Entity types the object may be, for entity-valued predicates.
    range: tuple[str, ...]
    object_kind: str = OBJECT_ENTITY
    # Functional: one subject may have at most one object valid at a time.
    # Conflict detection (a later phase) reads this; it is recorded now so the
    # vocabulary carries its own semantics rather than needing a second table.
    functional: bool = False

    @property
    def entity_valued(self) -> bool:
        return self.object_kind == OBJECT_ENTITY


PREDICATES: dict[str, Predicate] = {
    p.name: p
    for p in (
        Predicate(
            name="FUNDED_BY",
            description="The project was funded or sponsored by the organization.",
            domain=("PROJECT",), range=("ORGANIZATION",),
            # A project routinely has several funders.
            functional=False,
        ),
        Predicate(
            name="PARTNER_OF",
            description="The project was delivered in partnership with the organization.",
            domain=("PROJECT",), range=("ORGANIZATION",),
            functional=False,
        ),
        Predicate(
            name="LED_BY",
            description="The project is or was led by the person.",
            domain=("PROJECT",), range=("PERSON",),
            # One leader at a time; a change of leader is a temporal succession,
            # not two simultaneous truths.
            functional=True,
        ),
        Predicate(
            name="WORKS_AT",
            description="The person is or was employed by the organization.",
            domain=("PERSON",), range=("ORGANIZATION",),
            functional=True,
        ),
        Predicate(
            name="MEMBER_OF",
            description=(
                "The person belongs to the organization in a non-employment "
                "sense: a committee, a board, a division."
            ),
            domain=("PERSON",), range=("ORGANIZATION",),
            functional=False,
        ),
        Predicate(
            name="PARENT_OF",
            description="The organization contains the other as a unit or subsidiary.",
            domain=("ORGANIZATION",), range=("ORGANIZATION",),
            functional=False,
        ),
        Predicate(
            name="HAS_ROLE",
            description=(
                "The person holds the named role. The object is the role as "
                "written, not an entity: this corpus states roles constantly "
                '("Mr Sanjay Seth, Senior Director, TERI") and they denote no '
                "thing of their own."
            ),
            domain=("PERSON",), range=(),
            object_kind=OBJECT_TEXT,
            functional=True,
        ),
    )
}

PREDICATE_NAMES: tuple[str, ...] = tuple(sorted(PREDICATES))

# Bumped when the vocabulary changes in a way that would alter which claims are
# valid. Stored on every assertion, so claims made under an older vocabulary
# stay distinguishable rather than silently re-interpreted.
VOCABULARY_VERSION = "predicates-v1"


def get(name: str) -> Predicate | None:
    """The predicate, or None. Never raises: an unknown predicate is a
    validation outcome, not an exception."""
    return PREDICATES.get(name)


def is_known(name: str) -> bool:
    return name in PREDICATES


def accepts(name: str, subject_type: str, object_type: str | None) -> bool:
    """Whether this predicate may join these entity types.

    ``object_type`` is None for a literal-valued predicate. The two are checked
    together because a predicate's domain and range are one contract: LED_BY is
    not "any project" and "any person" independently, it is the pair.
    """
    predicate = PREDICATES.get(name)
    if predicate is None:
        return False
    if subject_type not in predicate.domain:
        return False
    if predicate.entity_valued:
        return object_type in predicate.range
    return object_type is None
