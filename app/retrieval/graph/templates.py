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

One template per predicate, or one per shape
--------------------------------------------
This registry began with one template per *question*, which meant a predicate
was queryable only if someone had written Cypher for it — and three of the seven
approved predicates had none. The second family below fixes that by
parameterizing the predicate: ``c.predicate = $predicate`` is a bound **value**,
so one reviewed query serves every approved predicate, present and future.

That is safe precisely because a predicate never becomes an *identifier*. A
relationship type would have to be interpolated into the query text; a property
value is bound like any other parameter, and ``validate_parameters`` checks it
against the closed vocabulary first, so an unapproved predicate cannot even be
probed for.

Current versus historical
-------------------------
The distinction is not cosmetic; it decides which part of the graph is read.

``current``     the present state. Traverses the **derived current-state edges**
                (``{current: true}``) where a template for that predicate and
                direction exists — cheap, and the graph's own statement of what
                is true now. Where none exists, the claim-based template applies
                the identical rule (see ``_current_clause``): active status, an
                approved validity basis, and a window open at the moment asked
                about. Either way a claim that has ended cannot come back.
``historical``  traverses **Claim nodes** and their validity windows. Superseded
                claims are included — they are the answer to "who led this in
                2019" — and each row carries ``status`` so a caller can present a
                disputed claim as disputed rather than as fact.

No lower bound on age
---------------------
Nothing here compares a claim against the present. There is no ``date()`` or
``datetime()`` in any template, no minimum year, and no test of a document's
age: a relationship that ran 1996-1999 is retrieved on exactly the same terms as
one that started last year. Temporal validity decides whether something is
*current*, never whether it can be *found*.

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
    # Parameters the caller *may* supply and which may be ``None``. Used only
    # for the temporal bounds of the predicate-parameterized templates, where
    # "no bound on this side" is a meaningful value rather than a missing one:
    # `NULL` is bound and the Cypher tests for it. They are still validated —
    # a non-null value must still be a well-formed ISO date — so "optional"
    # means "may be absent", never "unchecked".
    optional_parameters: tuple[str, ...] = ()

    @property
    def is_current(self) -> bool:
        return self.mode == MODE_CURRENT

    @property
    def all_parameters(self) -> tuple[str, ...]:
        return self.parameters + self.optional_parameters


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
       properties(c).object_literal AS object_literal,
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


# --------------------------------------------------------------------------- #
# Predicate-parameterized templates — one query per *shape*, not per predicate
#
# The registry above has one template per question, which is why six approved
# predicates had four routes between them and three (PARTNER_OF, PARENT_OF,
# HAS_ROLE) had none at all. These templates close that gap without opening the
# one the registry exists to keep shut.
#
# The move that makes it safe: a predicate travels as a **property value**, not
# as a relationship type. `c.predicate = $predicate` is a bound parameter, so
# one reviewed query serves every approved predicate and no new Cypher is
# written when the vocabulary grows. `validate_parameters` still checks the
# value against the closed vocabulary before it is bound, so an unapproved
# predicate cannot even be probed for. There is still no path by which a label
# or a relationship type is built from input — the only identifiers in this
# Cypher are `Claim`, `Entity`, `Document`, `Chunk`, `SUBJECT`, `OBJECT` and
# `SUPPORTED_BY`, all literal in reviewed text.
#
# Composition, not duplication
# ----------------------------
# The temporal and current-state clauses are identical across the shapes, so
# they are assembled from module-level fragments rather than copied. The
# fragments are called only with the literal variable names below, at import
# time; nothing runtime-supplied reaches them, and the resulting Cypher is fixed
# for the life of the process. Tests assert the assembled text, so what is
# reviewed is what runs.
# --------------------------------------------------------------------------- #


def _overlap(var: str) -> str:
    """The interval-overlap clause for a claim bound to ``var``.

    Half-open on both sides, matching ``app.knowledge.claims.temporal.overlaps``
    exactly, so "valid during" means the same thing at query time as it does in
    conflict detection.

    Two properties are worth stating because both were requirements:

    * **No minimum date.** An absent ``window_start`` and ``window_end`` impose
      no filter, and no bound anywhere below compares a claim's dates against
      "now", a document's age, or any floor. A relationship that ran 1996-1999
      is as retrievable as one that started last year.
    * **An unknown window matches nothing.** A claim with neither a start nor an
      end is not evidence about any particular time, so it is excluded whenever
      a window is asked for — rather than being treated as spanning all of it.
      With no window asked for it is returned like anything else.
    """
    return f"""
  AND (
        ($window_start IS NULL AND $window_end IS NULL)
        OR (
             ({var}.valid_from IS NOT NULL OR {var}.valid_until IS NOT NULL)
             AND ($window_end   IS NULL OR {var}.valid_from  IS NULL
                  OR {var}.valid_from  <  $window_end)
             AND ($window_start IS NULL OR {var}.valid_until IS NULL
                  OR {var}.valid_until >  $window_start)
           )
      )"""


def _current_clause(var: str) -> str:
    """The extra conditions a claim must meet to be asserted as *present* fact.

    Mirrors ``app.knowledge.claims.conflicts.is_current_state_eligible`` term
    for term — active status, an approved validity basis, a window open at the
    moment asked about — which is the same rule the projector applies when it
    derives a current-state edge. Stating it here rather than only traversing
    the derived edges means a current-state question is answered from the claims
    themselves, so it cannot silently return nothing merely because a projection
    has not been re-run. The *semantics* of "current" are unchanged; only where
    they are evaluated is.

    The window test lives in ``_overlap``: a current query passes
    ``[today, tomorrow)`` as its window, so "open now" and "overlaps today" are
    one condition rather than two that could drift apart.

    ``$current_bases`` is filled by ``validate_parameters`` from
    ``claim_types.CURRENT_STATE_BASES``; a caller cannot widen it.
    """
    return f"""
  AND (NOT $current_only
       OR ({var}.status = 'active' AND {var}.temporal_basis IN $current_bases))"""


_EVIDENCE = """
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(ch:Chunk)"""

_CLAIM_COLUMNS = """
       c.claim_id       AS claim_id,
       c.predicate      AS predicate,
       c.status         AS status,
       c.valid_from     AS valid_from,
       c.valid_until    AS valid_until,
       c.temporal_basis AS temporal_basis,
       c.confidence     AS confidence,
       properties(c).object_literal AS object_literal,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c.document_id) AS document_id"""

# Why `properties(c).object_literal` and not `c.object_literal`
# -----------------------------------------------------------
# Both return null when the property is absent, but the direct form makes Neo4j
# emit `UnknownPropertyKeyWarning` on every routed query in this corpus. The key
# genuinely does not exist in the database: every one of the 1,374 projected
# claims has an *entity* object and none has a literal one, and Cypher's
# `SET cl.object_literal = null` removes the property rather than storing a null.
#
# The projection is correct and the claim model is unchanged — a literal-valued
# predicate approved into the vocabulary later will populate it and this keeps
# reading it. Only the access form changed, so the read layer stops warning about
# a property the current data legitimately lacks.

# Most recent first. A question with no stated period wants the freshest thing
# known before the oldest, and a history question wants the sequence to read
# backwards from now — the same order serves both.
_RECENCY_ORDER = """
ORDER BY coalesce(c.valid_until, '9999-12-31') DESC,
         coalesce(c.valid_from,  '0000-01-01') DESC,
         c.claim_id
LIMIT $limit"""

# The question named the subject; the answer is the objects.
_RELATIONSHIP_BY_SUBJECT = f"""
MATCH (c:Claim)-[:SUBJECT]->(anchor:Entity {{entity_id: $entity_id}})
WHERE c.predicate = $predicate{_overlap("c")}{_current_clause("c")}
OPTIONAL MATCH (c)-[:OBJECT]->(other:Entity){_EVIDENCE}
RETURN{_CLAIM_COLUMNS},
       anchor.entity_id     AS subject_id,
       anchor.canonical_name AS subject_name,
       other.entity_id      AS object_id,
       other.canonical_name AS object_name{_RECENCY_ORDER}
"""

# The question named the object; the answer is the subjects. This is the
# inverse direction the vocabulary deliberately does not store a second time —
# "which projects did this organization fund" is `FUNDED_BY` read backwards, not
# a `FUNDS` predicate.
_RELATIONSHIP_BY_OBJECT = f"""
MATCH (c:Claim)-[:OBJECT]->(anchor:Entity {{entity_id: $entity_id}})
WHERE c.predicate = $predicate{_overlap("c")}{_current_clause("c")}
OPTIONAL MATCH (c)-[:SUBJECT]->(other:Entity){_EVIDENCE}
RETURN{_CLAIM_COLUMNS},
       other.entity_id      AS subject_id,
       other.canonical_name AS subject_name,
       anchor.entity_id     AS object_id,
       anchor.canonical_name AS object_name{_RECENCY_ORDER}
"""

# Everything the graph records about one entity, whichever end it sits at and
# whatever the predicate. `$predicates` is bound by `validate_parameters` to the
# whole approved vocabulary, so even this cannot surface a claim made under a
# predicate that has since been retired.
_ENTITY_TIMELINE = f"""
MATCH (c:Claim)-[:SUBJECT|OBJECT]->(anchor:Entity {{entity_id: $entity_id}})
WHERE c.predicate IN $predicates{_overlap("c")}{_current_clause("c")}
OPTIONAL MATCH (c)-[:SUBJECT]->(subject:Entity)
OPTIONAL MATCH (c)-[:OBJECT]->(object:Entity){_EVIDENCE}
RETURN{_CLAIM_COLUMNS},
       subject.entity_id     AS subject_id,
       subject.canonical_name AS subject_name,
       object.entity_id      AS object_id,
       object.canonical_name AS object_name,
       anchor.entity_id      AS anchor_id,
       anchor.canonical_name AS anchor_name{_RECENCY_ORDER}
"""

# Two relationships chained through a shared entity: "who leads the projects
# this organization funded", "which projects do this person's colleagues run".
# Both legs are bound predicate values and both are temporally filtered, so a
# chain cannot join a 2005 funding to a 2019 leadership and present it as one
# fact. Direction is left open on each leg (`SUBJECT|OBJECT`) because the useful
# chains run both ways through the middle entity; the hop count is still fixed
# at two by the text of the query, with no variable-length path anywhere.
_RELATIONSHIP_TWO_HOP = f"""
MATCH (c1:Claim)-[:SUBJECT|OBJECT]->(anchor:Entity {{entity_id: $entity_id}})
WHERE c1.predicate = $predicate{_overlap("c1")}{_current_clause("c1")}
MATCH (c1)-[:SUBJECT|OBJECT]->(mid:Entity)
WHERE mid.entity_id <> anchor.entity_id
MATCH (c2:Claim)-[:SUBJECT|OBJECT]->(mid)
WHERE c2.predicate = $predicate2
  AND c2.claim_id <> c1.claim_id{_overlap("c2")}{_current_clause("c2")}
MATCH (c2)-[:SUBJECT|OBJECT]->(far:Entity)
WHERE far.entity_id <> mid.entity_id AND far.entity_id <> anchor.entity_id
OPTIONAL MATCH (c2)-[:SUPPORTED_BY]->(doc:Document)
OPTIONAL MATCH (c2)-[:SUPPORTED_BY]->(ch:Chunk)
RETURN c2.claim_id       AS claim_id,
       c1.claim_id       AS via_claim_id,
       c2.predicate      AS predicate,
       c1.predicate      AS via_predicate,
       c2.status         AS status,
       c2.valid_from     AS valid_from,
       c2.valid_until    AS valid_until,
       c2.temporal_basis AS temporal_basis,
       c2.confidence     AS confidence,
       anchor.entity_id      AS anchor_id,
       anchor.canonical_name AS anchor_name,
       mid.entity_id         AS mid_id,
       mid.canonical_name    AS mid_name,
       far.entity_id         AS far_id,
       far.canonical_name    AS far_name,
       // Which way round each leg runs. The match leaves direction open, so
       // without these a renderer would have to guess, and guessing turns
       // "Alok works at TERI" into "TERI works at Alok".
       c1.subject_id = anchor.entity_id AS anchor_is_subject,
       c2.subject_id = mid.entity_id    AS mid_is_subject,
       ch.chunk_id      AS chunk_id,
       coalesce(doc.document_id, c2.document_id) AS document_id
ORDER BY coalesce(c2.valid_until, '9999-12-31') DESC,
         far.canonical_name, c2.claim_id
LIMIT $limit
"""

# Parameters shared by every predicate-parameterized template.
_WINDOW_PARAMS = ("window_start", "window_end")


TEMPLATES: dict[str, QueryTemplate] = {
    t.template_id: t
    for t in (
        QueryTemplate(
            "relationship_by_subject",
            "Claims about a named subject under one approved predicate, "
            "optionally restricted to a validity window.",
            MODE_HISTORICAL, ("entity_id", "predicate", "current_only"),
            _RELATIONSHIP_BY_SUBJECT, max_hops=1,
            optional_parameters=_WINDOW_PARAMS,
        ),
        QueryTemplate(
            "relationship_by_object",
            "Claims naming an entity as the object of one approved predicate — "
            "the inverse direction — optionally restricted to a window.",
            MODE_HISTORICAL, ("entity_id", "predicate", "current_only"),
            _RELATIONSHIP_BY_OBJECT, max_hops=1,
            optional_parameters=_WINDOW_PARAMS,
        ),
        QueryTemplate(
            "entity_timeline",
            "Every approved claim naming an entity at either end, optionally "
            "restricted to a validity window.",
            MODE_HISTORICAL, ("entity_id", "current_only"),
            _ENTITY_TIMELINE, max_hops=1,
            optional_parameters=_WINDOW_PARAMS,
        ),
        QueryTemplate(
            "relationship_two_hop",
            "Two approved relationships chained through a shared entity, each "
            "leg restricted to the same validity window.",
            MODE_HISTORICAL,
            ("entity_id", "predicate", "predicate2", "current_only"),
            _RELATIONSHIP_TWO_HOP, max_hops=2,
            optional_parameters=_WINDOW_PARAMS,
        ),
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
    from app.knowledge.claims import types as claim_types

    checked: dict[str, Any] = {}
    for name in template.parameters:
        if name not in params or params[name] is None:
            raise InvalidParameter(f"{template.template_id}: missing {name!r}")
        checked[name] = _check(name, params[name], vocab)

    # Optional parameters bind as NULL when absent. The Cypher tests for NULL
    # explicitly, so "no bound on this side" is expressed rather than implied;
    # a value that *is* supplied is checked exactly as a required one.
    for name in template.optional_parameters:
        value = params.get(name)
        checked[name] = None if value is None else _check(name, value, vocab)

    start, end = checked.get("window_start"), checked.get("window_end")
    if start and end and start >= end:
        # Half-open, so an empty or inverted window can only be a planner bug.
        # It would return nothing either way; failing says which.
        raise InvalidParameter(f"empty validity window: [{start}..{end})")

    # Derived parameters: filled here, never accepted from a caller. These are
    # the two places where the closed vocabulary has to reach the query, and
    # routing them through the validator is what stops a caller widening either.
    if "$current_bases" in template.cypher:
        checked["current_bases"] = list(claim_types.CURRENT_STATE_BASES)
    if "$predicates" in template.cypher:
        checked["predicates"] = list(vocab.PREDICATE_NAMES)

    requested = DEFAULT_LIMIT if limit is None else int(limit)
    checked["limit"] = max(1, min(requested, MAX_LIMIT))
    return checked


def _check(name: str, value: Any, vocab: Any) -> Any:
    """Type- and shape-check one parameter value, or raise."""
    if name == "entity_id":
        if not isinstance(value, str) or not ENTITY_ID_RE.match(value):
            raise InvalidParameter(f"malformed entity_id: {value!r}")
    elif name == "claim_id":
        if not isinstance(value, str) or not value.startswith("claim_"):
            raise InvalidParameter(f"malformed claim_id: {value!r}")
    elif name in ("predicate", "predicate2"):
        # A predicate reaches Cypher as a *value*, never as a relationship
        # type, but it is still checked against the closed vocabulary so a
        # caller cannot probe for arbitrary strings.
        if not vocab.is_known(str(value)):
            raise InvalidParameter(f"unknown predicate: {value!r}")
    elif name in ("as_of", "window_start", "window_end"):
        if not isinstance(value, str) or not DATE_RE.match(value):
            raise InvalidParameter(f"malformed {name} date: {value!r}")
    elif name == "current_only":
        # A bool, and strictly so: a truthy string would silently turn a
        # historical query into a current-state one, or the reverse.
        if not isinstance(value, bool):
            raise InvalidParameter(f"{name} must be a bool, got {value!r}")
    return value
