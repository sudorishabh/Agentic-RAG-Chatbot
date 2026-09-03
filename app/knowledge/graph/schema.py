"""Neo4j constraints and indexes for the entity/claim model.

Mirrors ``app.catalog.schema``: every statement is idempotent (``IF NOT
EXISTS``), the whole set is applied by one ``ensure_*`` function, and it is safe
to call once per process. Unlike the MySQL schema this creates no storage — only
constraints and indexes — so applying it to an empty graph is the intended
order (adding a uniqueness constraint to a populated graph fails on existing
duplicates).

Edition
-------
Measured against the deployed server (Neo4j 2026.07.1, **Community**):

===================  ==========  ====================================
DDL                  Community   Consequence here
===================  ==========  ====================================
uniqueness           yes         the identity backbone below
range index          yes         used
composite index      yes         used
relationship index   yes         deferred to the projection phase
fulltext index       yes         used for operator entity lookup
NODE KEY             **no**      Alias identity uses a derived single
                                 property, ``alias_key``, instead
existence (NOT NULL) **no**      required properties are enforced in
                                 code at write time
===================  ==========  ====================================

The two rejections are Enterprise-only features, so they are designed around
rather than assumed. Both design-arounds are recorded where they bite:
``ALIAS_KEY_TEMPLATE`` and ``REQUIRED_PROPERTIES``.

No property here carries tenant, ACL or taxonomy data: the corpus is public and
read whole by every caller, and taxonomy is not part of this model.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Vocabulary. Code-owned allow-lists: Cypher cannot parameterize a label or a
# relationship type, so every one used anywhere must originate here rather than
# from a request, a document, or a model. This is the primary injection control
# for the graph, and it is why these are constants and not configuration.
# --------------------------------------------------------------------------- #

# Entity subtype labels. Every canonical entity also carries the shared
# :Entity label, so provenance queries can match generically while typed
# traversal stays index-backed.
#
# Deliberately the smallest set the corpus actually evidences. Phase 0 discovery
# decides whether LOCATION / SERVICE / PROGRAM / DEPARTMENT earn a label; adding
# one later is a constant and an index, not a migration.
ENTITY_LABELS: tuple[str, ...] = ("Person", "Organization", "Project")

# Structural / provenance relationships. These are mechanical: they say where a
# claim came from, not what it asserts.
PROVENANCE_RELATIONSHIPS: tuple[str, ...] = (
    "HAS_ALIAS",
    "SUBJECT",
    "OBJECT",
    "USES_PREDICATE",
    "SUPPORTED_BY",
    "PART_OF",
    "CONTRADICTS",
    "SUPERSEDES",
    "MERGED_INTO",
)

# Properties this model requires but Community cannot enforce, since existence
# constraints are Enterprise-only. Writers check these; the list exists so the
# check has one definition and the tests can assert against it.
REQUIRED_PROPERTIES: dict[str, tuple[str, ...]] = {
    "Entity": ("entity_id", "entity_type", "canonical_name", "normalized_name"),
    "Alias": ("alias_key", "entity_id", "normalized"),
    "Claim": ("claim_id", "predicate", "subject_id", "status"),
    "Chunk": ("chunk_id", "document_id"),
    "Document": ("document_id",),
    "Predicate": ("name",),
}

# An alias is identified by (entity_id, normalized, alias_type). NODE KEY would
# express that directly and is Enterprise-only, so the triple is folded into one
# property a uniqueness constraint can cover. Writers must derive the key with
# `alias_key` and never assign it by hand.
#
# Hashed over a unit-separator join rather than formatted into a readable
# string, following app.cache.cache_keys._sha. A printable delimiter is not
# safe here: with "|", ("a", "b|c", "d") and ("a|b", "c", "d") produce the same
# key, and since this key *is* the uniqueness constraint that would silently
# merge two different aliases onto one node. The readable parts are stored as
# their own properties, so nothing is lost for debugging.
_ALIAS_KEY_SEP = "\x1f"


def alias_key(entity_id: str, normalized: str, alias_type: str) -> str:
    """The single-property stand-in for the unavailable NODE KEY constraint."""
    import hashlib

    joined = _ALIAS_KEY_SEP.join((entity_id, normalized, alias_type))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# DDL
# --------------------------------------------------------------------------- #

# Identity. These are what make projection idempotent: every writer MERGEs on
# one of these keys, so re-running a projection updates rather than duplicates.
CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
    "FOR (n:Entity) REQUIRE n.entity_id IS UNIQUE",
    "CREATE CONSTRAINT claim_id_unique IF NOT EXISTS "
    "FOR (n:Claim) REQUIRE n.claim_id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS "
    "FOR (n:Chunk) REQUIRE n.chunk_id IS UNIQUE",
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS "
    "FOR (n:Document) REQUIRE n.document_id IS UNIQUE",
    "CREATE CONSTRAINT predicate_name_unique IF NOT EXISTS "
    "FOR (n:Predicate) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT alias_key_unique IF NOT EXISTS "
    "FOR (n:Alias) REQUIRE n.alias_key IS UNIQUE",
    # One entity per authoritative CMS record. Nulls are exempt from uniqueness
    # in Neo4j, so entities with no CMS record are unaffected.
    "CREATE CONSTRAINT entity_cms_uuid_unique IF NOT EXISTS "
    "FOR (n:Entity) REQUIRE n.cms_uuid IS UNIQUE",
)

INDEXES: tuple[str, ...] = (
    # Resolution / gazetteer lookups: the hot path when mentions are matched.
    "CREATE INDEX alias_normalized IF NOT EXISTS FOR (n:Alias) ON (n.normalized)",
    "CREATE INDEX entity_normalized IF NOT EXISTS "
    "FOR (n:Entity) ON (n.entity_type, n.normalized_name)",
    "CREATE INDEX entity_status IF NOT EXISTS FOR (n:Entity) ON (n.status)",
    # Claim filtering: nearly every traversal filters on status and predicate,
    # and temporal questions filter on the validity window.
    "CREATE INDEX claim_status IF NOT EXISTS FOR (n:Claim) ON (n.status)",
    "CREATE INDEX claim_predicate IF NOT EXISTS FOR (n:Claim) ON (n.predicate)",
    "CREATE INDEX claim_subject IF NOT EXISTS FOR (n:Claim) ON (n.subject_id)",
    "CREATE INDEX claim_object IF NOT EXISTS FOR (n:Claim) ON (n.object_id)",
    # Composite, so an "as of date D" filter is not a scan of the predicate's
    # claims. This is what makes temporal queries affordable.
    "CREATE INDEX claim_validity IF NOT EXISTS "
    "FOR (n:Claim) ON (n.valid_from, n.valid_until)",
    # Lifecycle: drop one document version's graph footprint in a single pass.
    "CREATE INDEX chunk_document IF NOT EXISTS "
    "FOR (n:Chunk) ON (n.document_id, n.doc_version)",
    "CREATE INDEX document_published IF NOT EXISTS "
    "FOR (n:Document) ON (n.effective_start_date)",
)

# Operator-facing entity lookup (review CLIs, "which entity did you mean").
# Separate from INDEXES because fulltext DDL has its own syntax and its own
# failure mode, not because it is optional.
FULLTEXT_INDEXES: tuple[str, ...] = (
    "CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS "
    "FOR (n:Entity) ON EACH [n.canonical_name]",
    "CREATE FULLTEXT INDEX alias_surface_fulltext IF NOT EXISTS "
    "FOR (n:Alias) ON EACH [n.surface]",
)


def statements() -> tuple[str, ...]:
    """Every DDL statement, in application order.

    Constraints first: a uniqueness constraint creates its own backing index, so
    creating an equivalent index beforehand would leave a redundant one behind.
    """
    return CONSTRAINTS + INDEXES + FULLTEXT_INDEXES


def ensure_graph_schema(*, session: Any | None = None) -> int:
    """Apply the schema. Returns the number of statements executed.

    Idempotent through ``IF NOT EXISTS``, so a second call is a no-op and this
    can run on every process start, like ``catalog.schema.ensure_*``.

    Fails loudly rather than open: this is a deliberate operator action (or a
    guarded startup step), and a half-built schema is worth knowing about
    immediately — unlike the runtime paths, where an unreachable graph must
    degrade quietly.
    """
    from app.core.clients.graph import write_session

    if session is not None:
        for statement in statements():
            session.run(statement)
        return len(statements())

    with write_session() as opened:
        for statement in statements():
            opened.run(statement)
    logger.info("Applied %d Neo4j schema statements.", len(statements()))
    return len(statements())


def drop_graph_schema(*, session: Any | None = None) -> None:
    """Drop every constraint and index this module creates.

    The graph is a rebuildable projection, so tearing the schema down is a
    supported operation rather than an emergency: it is how a model change is
    applied. Data is not touched here.
    """
    from app.core.clients.graph import write_session

    names = [
        statement.split()[2]
        for statement in statements()
        if statement.startswith("CREATE CONSTRAINT")
    ]
    index_names = [
        statement.split()[2] if statement.startswith("CREATE INDEX")
        else statement.split()[3]
        for statement in statements()
        if not statement.startswith("CREATE CONSTRAINT")
    ]

    def _run(target: Any) -> None:
        for name in names:
            target.run(f"DROP CONSTRAINT {name} IF EXISTS")
        for name in index_names:
            target.run(f"DROP INDEX {name} IF EXISTS")

    if session is not None:
        _run(session)
        return
    with write_session() as opened:
        _run(opened)
