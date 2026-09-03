"""Batched, parameterized writes into Neo4j.

Every write in the knowledge layer goes through here, and the module exists to
make three properties structural rather than a matter of care:

**Parameterized, always.** No value is ever formatted into a Cypher string.
Statements are module-level constants and data arrives via ``$rows``.

**Labels and relationship types come from a code-side allow-list.** Cypher
cannot parameterize either, so they are the one thing that must be interpolated
— and they are interpolated only from
:mod:`app.knowledge.graph.schema`'s constants, never from a row, a request or a
model. :func:`safe_label` and :func:`safe_relationship` are the choke points.

**Idempotent by ``MERGE`` on a deterministic key.** Every node is merged on the
id its source computed (``entity_id``, ``claim_id``, ``chunk_id``,
``document_id``), so re-running a projection updates rather than duplicates.
That is what makes a rebuild safe and a partial failure resumable.

Batches are ``UNWIND $rows AS row MERGE ...`` — one round trip per few thousand
rows rather than one per row, and a failed batch retries safely because every
statement in it is a MERGE on a stable key.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Sequence

from app.knowledge.graph import schema

logger = logging.getLogger(__name__)

# Rows per transaction. Large enough that the round trip is amortised, small
# enough that a failure retries cheaply and a transaction stays modest.
BATCH_SIZE = 1000


class UnsafeIdentifier(ValueError):
    """A label or relationship type that did not come from the allow-list."""


def safe_label(label: str) -> str:
    """A node label, or raise. The only way a label reaches Cypher."""
    allowed = {"Entity", "Alias", "Claim", "Chunk", "Document", "Predicate"}
    allowed.update(schema.ENTITY_LABELS)
    if label not in allowed:
        raise UnsafeIdentifier(f"label not in the allow-list: {label!r}")
    return label


def safe_relationship(name: str) -> str:
    """A relationship type, or raise.

    Covers the structural relationships and the projected current-state ones,
    the latter being exactly the closed predicate vocabulary — so a predicate
    that is not in that vocabulary cannot become an edge type.
    """
    from app.knowledge.claims import predicates as vocab

    allowed = set(schema.PROVENANCE_RELATIONSHIPS) | set(vocab.PREDICATE_NAMES)
    if name not in allowed:
        raise UnsafeIdentifier(f"relationship not in the allow-list: {name!r}")
    return name


def batched(rows: Sequence[Any], size: int = BATCH_SIZE) -> Iterable[Sequence[Any]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def run_batches(
    session: Any, statement: str, rows: Sequence[dict], **params: Any
) -> int:
    """Execute one statement over rows in batches. Returns rows written.

    Extra keyword arguments become Cypher parameters alongside ``$rows`` — which
    is how ``$projection_version`` reaches the statements that stamp a
    generation. They are parameters, never interpolation.
    """
    written = 0
    for batch in batched(rows):
        session.run(statement, rows=list(batch), **params)
        written += len(batch)
    return written


# --------------------------------------------------------------------------- #
# Statements. Module-level constants: nothing here is built at call time, so a
# reviewer can read every statement the application can execute.
# --------------------------------------------------------------------------- #

MERGE_ENTITY = """
UNWIND $rows AS row
MERGE (e:Entity {entity_id: row.entity_id})
SET e.canonical_name  = row.canonical_name,
    e.normalized_name = row.normalized_name,
    e.entity_type     = row.entity_type,
    e.trust           = row.trust,
    e.claim_eligible  = row.claim_eligible,
    e.cms_uuid        = row.cms_uuid,
    e.source          = row.source,
    e.status          = row.status,
    e.projection_version = $projection_version
"""

# Typed label applied in a second pass, one statement per label, because the
# label cannot be parameterized and must therefore be interpolated from the
# allow-list rather than from the row.
ADD_TYPE_LABEL = """
UNWIND $rows AS row
MATCH (e:Entity {entity_id: row.entity_id})
SET e:%s
"""

MERGE_ALIAS = """
UNWIND $rows AS row
MATCH (e:Entity {entity_id: row.entity_id})
MERGE (a:Alias {alias_key: row.alias_key})
SET a.normalized   = row.normalized,
    a.surface      = row.surface,
    a.alias_type   = row.alias_type,
    a.autolink     = row.autolink,
    a.is_ambiguous = row.is_ambiguous,
    a.entity_id    = row.entity_id,
    a.projection_version = $projection_version
MERGE (e)-[:HAS_ALIAS]->(a)
"""

MERGE_PREDICATE = """
UNWIND $rows AS row
MERGE (p:Predicate {name: row.name})
SET p.description = row.description,
    p.domain      = row.domain,
    p.range       = row.range,
    p.functional  = row.functional,
    p.object_kind = row.object_kind,
    p.vocabulary_version = row.vocabulary_version
"""

MERGE_DOCUMENT = """
UNWIND $rows AS row
MERGE (d:Document {document_id: row.document_id})
SET d.title        = row.title,
    d.source_type  = row.source_type,
    d.bundle       = row.bundle,
    d.effective_start_date = row.effective_start_date,
    d.url          = row.url
"""

# Chunk stubs carry join keys and nothing else. No text, no vectors: Qdrant owns
# those, and duplicating them here would make the graph a second text store.
MERGE_CHUNK = """
UNWIND $rows AS row
MERGE (c:Chunk {chunk_id: row.chunk_id})
SET c.document_id = row.document_id
WITH c, row
MATCH (d:Document {document_id: row.document_id})
MERGE (c)-[:PART_OF]->(d)
"""

MERGE_CLAIM = """
UNWIND $rows AS row
MERGE (cl:Claim {claim_id: row.claim_id})
SET cl.predicate         = row.predicate,
    cl.subject_id        = row.subject_id,
    cl.object_id         = row.object_id,
    cl.object_literal    = row.object_literal,
    cl.valid_from        = row.valid_from,
    cl.valid_until       = row.valid_until,
    cl.temporal_basis    = row.temporal_basis,
    cl.confidence        = row.confidence,
    cl.status            = row.status,
    cl.evidence_kind     = row.evidence_kind,
    cl.source_field      = row.source_field,
    cl.quote             = row.quote,
    cl.quote_start       = row.quote_start,
    cl.quote_end         = row.quote_end,
    cl.document_id       = row.document_id,
    cl.chunk_id          = row.chunk_id,
    cl.extraction_method = row.extraction_method,
    cl.extractor_version = row.extractor_version,
    cl.projection_version = $projection_version
"""

LINK_CLAIM_SUBJECT = """
UNWIND $rows AS row
MATCH (cl:Claim {claim_id: row.claim_id})
MATCH (s:Entity {entity_id: row.subject_id})
MERGE (cl)-[:SUBJECT]->(s)
"""

LINK_CLAIM_OBJECT = """
UNWIND $rows AS row
MATCH (cl:Claim {claim_id: row.claim_id})
MATCH (o:Entity {entity_id: row.object_id})
MERGE (cl)-[:OBJECT]->(o)
"""

LINK_CLAIM_PREDICATE = """
UNWIND $rows AS row
MATCH (cl:Claim {claim_id: row.claim_id})
MATCH (p:Predicate {name: row.predicate})
MERGE (cl)-[:USES_PREDICATE]->(p)
"""

LINK_CLAIM_CHUNK = """
UNWIND $rows AS row
MATCH (cl:Claim {claim_id: row.claim_id})
MATCH (c:Chunk {chunk_id: row.chunk_id})
MERGE (cl)-[:SUPPORTED_BY]->(c)
"""

# A CMS-derived claim has no chunk, so its evidence points at the document.
LINK_CLAIM_DOCUMENT = """
UNWIND $rows AS row
MATCH (cl:Claim {claim_id: row.claim_id})
MATCH (d:Document {document_id: row.document_id})
MERGE (cl)-[:SUPPORTED_BY]->(d)
"""

LINK_CLAIM_CLAIM = """
UNWIND $rows AS row
MATCH (a:Claim {claim_id: row.from_claim_id})
MATCH (b:Claim {claim_id: row.to_claim_id})
MERGE (a)-[r:%s]->(b)
SET r.reason = row.reason
"""

# The derived current-state edge. Carries `claim_id` back to its authoritative
# claim, so every projected relationship can be traced to the evidence that
# produced it — and `projection_version`, so a stale generation is removable.
PROJECT_CURRENT_STATE = """
UNWIND $rows AS row
MATCH (s:Entity {entity_id: row.subject_id})
MATCH (o:Entity {entity_id: row.object_id})
MERGE (s)-[r:%s {claim_id: row.claim_id}]->(o)
SET r.confidence         = row.confidence,
    r.valid_from         = row.valid_from,
    r.valid_until        = row.valid_until,
    r.temporal_basis     = row.temporal_basis,
    r.current            = true,
    r.projection_version = $projection_version
"""

DELETE_STALE_CURRENT_STATE = """
MATCH ()-[r]->()
WHERE r.current = true AND r.projection_version <> $projection_version
DELETE r
"""

# The scoped counterpart, for a projection that only looked at some claims.
#
# DELETE_STALE_CURRENT_STATE above is correct only for a pass that examined the
# WHOLE staged set: it deletes every current edge this generation did not
# re-stamp, so a per-document run would wipe the rest of the corpus's current
# state. This one names the claims instead. A claim that stopped being
# current-state eligible — retracted, disputed, superseded, out of window —
# loses its edge, and nothing else is touched.
#
# Matched on `claim_id` rather than on endpoints because that property is what
# ties an edge to the claim that justifies it, and it is set by
# PROJECT_CURRENT_STATE on every edge this system creates.
DELETE_CURRENT_STATE_FOR_CLAIMS = """
UNWIND $rows AS row
MATCH ()-[r {claim_id: row.claim_id}]->()
WHERE r.current = true
DELETE r
"""

# --------------------------------------------------------------------------- #
# Retiring nodes an older generation left behind
#
# `DELETE_STALE_CURRENT_STATE` above retires *relationships*, and for a long time
# that was the only retirement the projector did. It was not enough. Every write
# above is a MERGE over the rows MySQL currently says are projectable, so a row
# that *stops* being projectable is never visited again: nothing updates it and
# nothing removes it. An entity demoted from `pi_attested` to `provisional` kept
# a graph node still claiming `pi_attested, claim_eligible: true`, and the claims
# naming it kept their nodes too — measured on the live graph as 2 entities, 17
# claims and 2 aliases stranded on a projection generation four hours older than
# the rest of the graph.
#
# The rule is the one the current-state edges already use: a whole-corpus pass
# re-stamps `projection_version` on everything that should exist (the SET clauses
# above are unconditional, so a MATCH is re-stamped exactly like a CREATE), so
# after it runs, anything still carrying an older stamp is by construction
# something MySQL no longer projects.
#
# Only a whole-corpus pass may use these. A scoped pass re-stamps one document's
# rows, so "everything else" is the rest of the corpus — see the note on
# `DELETE_CURRENT_STATE_FOR_CLAIMS` for the same distinction, and
# `project.project_claims`, which deliberately does not call these.
#
# Claims go first, then entities: deleting a claim detaches its SUBJECT/OBJECT
# before the entity sweep runs, so neither sweep depends on the other's leftovers.

DELETE_STALE_CLAIMS = """
MATCH (c:Claim)
WHERE c.projection_version <> $projection_version
DETACH DELETE c
"""

# DETACH also removes HAS_ALIAS, and any current-state edge the entity still had.
DELETE_STALE_ENTITIES = """
MATCH (e:Entity)
WHERE e.projection_version <> $projection_version
DETACH DELETE e
"""

# Stamped like entities and claims, so an alias *removed from MySQL* is retired
# on the same rule as one whose entity was demoted. Without the stamp only the
# second case was reachable, because the first leaves the alias attached to an
# entity that is still perfectly valid.
DELETE_STALE_ALIASES = """
MATCH (a:Alias)
WHERE a.projection_version IS NULL
   OR a.projection_version <> $projection_version
DETACH DELETE a
"""

# Evidence stubs are not stamped, because they are shared: one document backs
# many claims, and a scoped pass legitimately re-merges a document whose other
# claims it never looked at. They are retired by reachability instead — a stub
# exists only to be evidence, so one that no longer backs anything is spent.
DELETE_ORPHAN_CHUNKS = """
MATCH (c:Chunk)
WHERE NOT EXISTS { MATCH (:Claim)-[:SUPPORTED_BY]->(c) }
DETACH DELETE c
"""

# Checked after the chunks, and against both routes to a document: a claim may
# cite it directly, or cite a chunk that is PART_OF it.
DELETE_ORPHAN_DOCUMENTS = """
MATCH (d:Document)
WHERE NOT EXISTS { MATCH (:Claim)-[:SUPPORTED_BY]->(d) }
  AND NOT EXISTS { MATCH (:Chunk)-[:PART_OF]->(d) }
DETACH DELETE d
"""


def run_sweep(session: Any, statement: str, **params: Any) -> int:
    """Run a retirement statement and report how many nodes it removed.

    Separate from :func:`run_batches` because a sweep takes no ``$rows``: it is
    defined by what is *absent* from this generation, which is the whole reason
    it can retire something no batch will ever mention.
    """
    summary = session.run(statement, **params).consume()
    return summary.counters.nodes_deleted


COUNT_NODES = "MATCH (n) RETURN labels(n) AS labels, count(*) AS n"
COUNT_RELATIONSHIPS = "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n"

DROP_ALL = "MATCH (n) DETACH DELETE n"
