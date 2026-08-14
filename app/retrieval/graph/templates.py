"""The closed registry of graph query templates.

**No query reaches Neo4j except one of these.** There is no code path that
accepts Cypher from a user, a model, or a request — the registry is a
module-level constant, and a caller selects a ``template_id`` and supplies typed
parameters. That is the whole of the Cypher-injection defence, and it is
structural rather than a matter of care.

Every template obeys the same rules, which the tests enforce by enumerating the
registry rather than by inspection:

* **parameterized** — every value arrives as ``$param``; nothing is formatted in;
* **fixed hops** — no variable-length path (``[*]``) is expressible, so traversal
  depth is bounded by the text of the query itself;
* **``LIMIT $limit``** — every template caps its rows;
* **labels and relationship types are literals in reviewed text**, never built
  from input.

Current versus historical
-------------------------
The distinction is not cosmetic; it decides which part of the graph is read.

``current``     traverses the **derived current-state edges** (``{current: true}``).
                Those exist only for claims that are active, non-disputed and
                valid now, so a disputed claim cannot appear as a present fact.
                Cheap: the four-hop question is four hops.
``historical``  traverses **Claim nodes** and their validity windows. Superseded
                claims are included — they are the answer to "who led this in
                2019" — and each row carries ``status`` so a caller can present a
                disputed claim as disputed rather than as fact.

Results carry identifiers, never text: ``claim_id``, ``chunk_id``,
``document_id``, ``entity_id``. Source text is hydrated from Qdrant afterwards,
which is what keeps Neo4j from becoming a second text store.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MODE_CURRENT = "current"
MODE_HISTORICAL = "historical"
MODES = (MODE_CURRENT, MODE_HISTORICAL)

# Hard ceiling on rows, whatever a caller asks for. A graph answer feeds a
# reranker and then a prompt; a thousand rows helps nobody and costs a lot.
MAX_LIMIT = 100
DEFAULT_LIMIT = 25

# `entity_id` shape, validated before it is ever sent as a parameter. A
# malformed id fails here rather than reaching the driver.
ENTITY_ID_RE = re.compile(r"^(?:person|org|project)_[0-9a-f]{12}$")

# ISO date, for the `as_of` parameter of a historical query.
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class QueryTemplate:
    """One reviewed, parameterized query."""

    template_id: str
    description: str
    mode: str
    # Parameter names the caller must supply, besides `limit`.
    parameters: tuple[str, ...]
    cypher: str
    # Documented for review and asserted by tests; the bound is in the Cypher.
    max_hops: int

    @property
    def is_current(self) -> bool:
        return self.mode == MODE_CURRENT


# --------------------------------------------------------------------------- #
# Current-state templates — derived edges, so disputed claims cannot appear
# --------------------------------------------------------------------------- #

_PROJECTS_FUNDED_BY_ORG = """
MATCH (o:Organization {entity_id: $entity_id})<-[f:FUNDED_BY {current: true}]-(p:Project)
OPTIONAL MATCH (c:Claim {claim_id: f.claim_id})
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN p.entity_id      AS project_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       p.canonical_name AS project_name,
       o.entity_id      AS funder_id,
       o.canonical_name AS funder_name,
       f.claim_id       AS claim_id,
       f.valid_from     AS valid_from,
       f.valid_until    AS valid_until,
       f.confidence     AS confidence
ORDER BY p.canonical_name
LIMIT $limit
"""

_PEOPLE_LEADING_PROJECTS_FUNDED_BY_ORG = """
MATCH (o:Organization {entity_id: $entity_id})<-[f:FUNDED_BY {current: true}]-(p:Project)
MATCH (p)-[l:LED_BY {current: true}]->(person:Person)
OPTIONAL MATCH (c:Claim {claim_id: l.claim_id})
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN person.entity_id      AS person_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       person.canonical_name AS person_name,
       person.trust          AS person_trust,
       p.entity_id           AS project_id,
       p.canonical_name      AS project_name,
       o.canonical_name      AS funder_name,
       l.claim_id            AS claim_id,
       f.claim_id            AS funding_claim_id,
       l.valid_from          AS valid_from,
       l.valid_until         AS valid_until
ORDER BY person.canonical_name, p.canonical_name
LIMIT $limit
"""

_PROJECTS_LED_BY_PERSON = """
MATCH (person:Person {entity_id: $entity_id})<-[l:LED_BY {current: true}]-(p:Project)
OPTIONAL MATCH (c:Claim {claim_id: l.claim_id})
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN p.entity_id           AS project_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       p.canonical_name      AS project_name,
       person.entity_id      AS person_id,
       person.canonical_name AS person_name,
       person.trust          AS person_trust,
       l.claim_id            AS claim_id,
       l.valid_from          AS valid_from,
       l.valid_until         AS valid_until
ORDER BY p.canonical_name
LIMIT $limit
"""

_PERSON_WORKS_AT = """
MATCH (person:Person {entity_id: $entity_id})-[w:WORKS_AT {current: true}]->(o:Organization)
OPTIONAL MATCH (c:Claim {claim_id: w.claim_id})
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN o.entity_id           AS organization_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       o.canonical_name      AS organization_name,
       person.entity_id      AS person_id,
       person.canonical_name AS person_name,
       w.claim_id            AS claim_id,
       w.valid_from          AS valid_from,
       w.valid_until         AS valid_until
ORDER BY o.canonical_name
LIMIT $limit
"""

_PERSON_MEMBER_OF = """
MATCH (person:Person {entity_id: $entity_id})-[m:MEMBER_OF {current: true}]->(o:Organization)
OPTIONAL MATCH (c:Claim {claim_id: m.claim_id})
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN o.entity_id           AS organization_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       o.canonical_name      AS organization_name,
       person.entity_id      AS person_id,
       person.canonical_name AS person_name,
       m.claim_id            AS claim_id,
       m.valid_from          AS valid_from,
       m.valid_until         AS valid_until
ORDER BY o.canonical_name
LIMIT $limit
"""

_FUNDERS_OF_PROJECT = """
MATCH (p:Project {entity_id: $entity_id})-[f:FUNDED_BY {current: true}]->(o:Organization)
OPTIONAL MATCH (c:Claim {claim_id: f.claim_id})
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN o.entity_id      AS funder_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       o.canonical_name AS funder_name,
       p.entity_id      AS project_id,
       p.canonical_name AS project_name,
       f.claim_id       AS claim_id,
       f.valid_from     AS valid_from,
       f.valid_until    AS valid_until
ORDER BY o.canonical_name
LIMIT $limit
"""

# --------------------------------------------------------------------------- #
# Historical templates — Claim nodes, so superseded history stays reachable
#
# `status` is returned on every row so a caller can present a disputed claim as
# disputed. These templates deliberately do NOT filter it out: hiding a
# contradiction is worse than showing it, as long as it is labelled.
# --------------------------------------------------------------------------- #

_PROJECT_HISTORY = """
MATCH (c:Claim)-[:SUBJECT]->(p:Project {entity_id: $entity_id})
OPTIONAL MATCH (c)-[:OBJECT]->(other:Entity)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN c.claim_id       AS claim_id,
       c.predicate      AS predicate,
       c.status         AS status,
       c.valid_from     AS valid_from,
       c.valid_until    AS valid_until,
       c.temporal_basis AS temporal_basis,
       c.confidence     AS confidence,
       c.object_literal AS object_literal,
       p.entity_id      AS subject_id,
       p.canonical_name AS subject_name,
       other.entity_id      AS object_id,
       other.canonical_name AS object_name,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id
ORDER BY c.valid_from DESC, c.claim_id
LIMIT $limit
"""

_PERSON_HISTORY = """
MATCH (c:Claim)-[:SUBJECT|OBJECT]->(person:Person {entity_id: $entity_id})
OPTIONAL MATCH (c)-[:SUBJECT]->(subject:Entity)
OPTIONAL MATCH (c)-[:OBJECT]->(object:Entity)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN c.claim_id       AS claim_id,
       c.predicate      AS predicate,
       c.status         AS status,
       c.valid_from     AS valid_from,
       c.valid_until    AS valid_until,
       c.temporal_basis AS temporal_basis,
       c.confidence     AS confidence,
       subject.entity_id      AS subject_id,
       subject.canonical_name AS subject_name,
       object.entity_id       AS object_id,
       object.canonical_name  AS object_name,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id
ORDER BY c.valid_from DESC, c.claim_id
LIMIT $limit
"""

# "Who led this on date X" — the question the current-state graph cannot answer.
_CLAIMS_AS_OF = """
MATCH (c:Claim)-[:SUBJECT]->(s:Entity {entity_id: $entity_id})
WHERE c.predicate = $predicate
  AND (c.valid_from  IS NULL OR c.valid_from  <= $as_of)
  AND (c.valid_until IS NULL OR c.valid_until >  $as_of)
OPTIONAL MATCH (c)-[:OBJECT]->(other:Entity)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN c.claim_id       AS claim_id,
       c.predicate      AS predicate,
       c.status         AS status,
       c.valid_from     AS valid_from,
       c.valid_until    AS valid_until,
       s.entity_id      AS subject_id,
       s.canonical_name AS subject_name,
       other.entity_id      AS object_id,
       other.canonical_name AS object_name,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id
ORDER BY c.claim_id
LIMIT $limit
"""

_ORG_FUNDING_HISTORY = """
MATCH (c:Claim)-[:OBJECT]->(o:Organization {entity_id: $entity_id})
WHERE c.predicate = 'FUNDED_BY'
OPTIONAL MATCH (c)-[:SUBJECT]->(p:Project)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN c.claim_id       AS claim_id,
       c.status         AS status,
       c.valid_from     AS valid_from,
       c.valid_until    AS valid_until,
       p.entity_id      AS project_id,
       p.canonical_name AS project_name,
       o.entity_id      AS funder_id,
       o.canonical_name AS funder_name,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id
ORDER BY c.valid_from DESC, c.claim_id
LIMIT $limit
"""

# Explaining one relationship: the "why does the system believe this?" path.
_EXPLAIN_CLAIM = """
MATCH (c:Claim {claim_id: $claim_id})
OPTIONAL MATCH (c)-[:SUBJECT]->(s:Entity)
OPTIONAL MATCH (c)-[:OBJECT]->(o:Entity)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)
OPTIONAL MATCH (c)-[:CONTRADICTS]->(other:Claim)
RETURN c.claim_id       AS claim_id,
       c.predicate      AS predicate,
       c.status         AS status,
       c.valid_from     AS valid_from,
       c.valid_until    AS valid_until,
       c.temporal_basis AS temporal_basis,
       c.confidence     AS confidence,
       c.quote          AS quote,
       c.evidence_kind  AS evidence_kind,
       c.source_field   AS source_field,
       s.canonical_name AS subject_name,
       s.entity_id      AS subject_id,
       o.canonical_name AS object_name,
       o.entity_id      AS object_id,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id,
       collect(other.claim_id) AS contradicted_by
LIMIT $limit
"""


TEMPLATES: dict[str, QueryTemplate] = {
    t.template_id: t
    for t in (
        QueryTemplate(
            "projects_funded_by_org",
            "Projects an organization currently funds.",
            MODE_CURRENT, ("entity_id",), _PROJECTS_FUNDED_BY_ORG, max_hops=1,
        ),
        QueryTemplate(
            "people_leading_projects_funded_by_org",
            "People currently leading projects an organization currently funds.",
            MODE_CURRENT, ("entity_id",),
            _PEOPLE_LEADING_PROJECTS_FUNDED_BY_ORG, max_hops=2,
        ),
        QueryTemplate(
            "projects_led_by_person",
            "Projects a person currently leads.",
            MODE_CURRENT, ("entity_id",), _PROJECTS_LED_BY_PERSON, max_hops=1,
        ),
        QueryTemplate(
            "funders_of_project",
            "Organizations currently funding a project.",
            MODE_CURRENT, ("entity_id",), _FUNDERS_OF_PROJECT, max_hops=1,
        ),
        QueryTemplate(
            "person_works_at",
            "Organizations a person currently works at.",
            MODE_CURRENT, ("entity_id",), _PERSON_WORKS_AT, max_hops=1,
        ),
        QueryTemplate(
            "person_member_of",
            "Organizations a person is currently a member of.",
            MODE_CURRENT, ("entity_id",), _PERSON_MEMBER_OF, max_hops=1,
        ),
        QueryTemplate(
            "project_history",
            "Every claim about a project, including superseded ones.",
            MODE_HISTORICAL, ("entity_id",), _PROJECT_HISTORY, max_hops=1,
        ),
        QueryTemplate(
            "person_history",
            "Every claim naming a person, including superseded ones.",
            MODE_HISTORICAL, ("entity_id",), _PERSON_HISTORY, max_hops=1,
        ),
        QueryTemplate(
            "claims_as_of",
            "Claims about a subject valid on a given date.",
            MODE_HISTORICAL, ("entity_id", "predicate", "as_of"),
            _CLAIMS_AS_OF, max_hops=1,
        ),
        QueryTemplate(
            "org_funding_history",
            "Every funding claim naming an organization, including superseded.",
            MODE_HISTORICAL, ("entity_id",), _ORG_FUNDING_HISTORY, max_hops=1,
        ),
        QueryTemplate(
            "explain_claim",
            "One claim with its evidence and any contradiction.",
            MODE_HISTORICAL, ("claim_id",), _EXPLAIN_CLAIM, max_hops=1,
        ),
    )
}

TEMPLATE_IDS: tuple[str, ...] = tuple(sorted(TEMPLATES))


class UnknownTemplate(KeyError):
    """A template id that is not in the registry."""


class InvalidParameter(ValueError):
    """A parameter that failed validation before reaching the driver."""


def get(template_id: str) -> QueryTemplate:
    """The template, or raise. There is no path that builds one at runtime."""
    template = TEMPLATES.get(template_id)
    if template is None:
        raise UnknownTemplate(f"no such query template: {template_id!r}")
    return template


def validate_parameters(
    template: QueryTemplate, params: dict[str, Any], *, limit: int | None = None
) -> dict[str, Any]:
    """Type- and shape-check every parameter, and clamp the limit.

    Validation is here rather than at the call site so it cannot be skipped by a
    new caller, and so a malformed ``entity_id`` fails fast instead of becoming
    a slow full-scan against an indexed property.
    """
    from app.knowledge.claims import predicates as vocab

    checked: dict[str, Any] = {}
    for name in template.parameters:
        if name not in params or params[name] is None:
            raise InvalidParameter(f"{template.template_id}: missing {name!r}")
        value = params[name]
        if name == "entity_id":
            if not isinstance(value, str) or not ENTITY_ID_RE.match(value):
                raise InvalidParameter(f"malformed entity_id: {value!r}")
        elif name == "claim_id":
            if not isinstance(value, str) or not value.startswith("claim_"):
                raise InvalidParameter(f"malformed claim_id: {value!r}")
        elif name == "predicate":
            # A predicate reaches Cypher as a *value*, never as a relationship
            # type, but it is still checked against the closed vocabulary so a
            # caller cannot probe for arbitrary strings.
            if not vocab.is_known(str(value)):
                raise InvalidParameter(f"unknown predicate: {value!r}")
        elif name == "as_of":
            if not isinstance(value, str) or not DATE_RE.match(value):
                raise InvalidParameter(f"malformed as_of date: {value!r}")
        checked[name] = value

    requested = DEFAULT_LIMIT if limit is None else int(limit)
    checked["limit"] = max(1, min(requested, MAX_LIMIT))
    return checked
