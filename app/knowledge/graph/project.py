"""Project MySQL entities and staged claims into Neo4j.

Neo4j is a **rebuildable projection**, never a system of record. Everything here
is derived from MySQL, so a corrupt graph is fixed by rebuilding rather than by
forensics, and an unreachable graph costs a retry rather than data.

What is projected, and what is refused
--------------------------------------
* **Entities**: only ``claim_eligible`` ones. The 803 provisional people do not
  reach the graph at all, so a traversal cannot arrive at a name-level identity
  and mistake it for a person. Trust is carried onto the node, so
  ``pi_attested`` stays distinguishable from ``authoritative``.
* **Claims**: every staged claim, whatever its status, because history is the
  point — a superseded claim is still the answer to "who led this in 2019".
* **Current-state edges**: only from claims that are ``active``, non-disputed,
  currently valid and eligible on both ends. This is the one place where the
  graph asserts "this is true now", and it is the narrowest thing here.

Every projected current-state edge carries ``claim_id`` back to the claim that
produced it, so the chain

    edge -> claim_id -> claim -> chunk_id/document_id -> Qdrant -> source text

is walkable for anything the graph asserts.

Idempotency and rebuild
-----------------------
Every write is ``MERGE`` on a deterministic key, so re-projecting is an update.
``projection_version`` stamps each generation; current-state edges from an older
generation are deleted after a run, which is how a claim that stopped being
current loses its edge without anything having to remember it existed.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.knowledge.claims import conflicts as cf
from app.knowledge.claims import predicates as vocab
from app.knowledge.claims import types as claim_types
from app.knowledge.graph import schema, writer

logger = logging.getLogger(__name__)

PROJECTOR_VERSION = "graph-project-v1"

# Entity type -> the typed label it also carries alongside :Entity.
_TYPE_LABELS = {
    "PERSON": "Person",
    "ORGANIZATION": "Organization",
    "PROJECT": "Project",
}


def make_projection_version(*, at: datetime | None = None) -> str:
    """A stamp identifying one generation of projected current-state edges."""
    moment = (at or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%S")
    digest = hashlib.sha256(
        f"{PROJECTOR_VERSION}\x1f{moment}".encode("utf-8")
    ).hexdigest()[:8]
    return f"{PROJECTOR_VERSION}:{moment}:{digest}"


@dataclass
class ProjectionReport:
    """What one projection pass wrote."""

    projection_version: str
    nodes: dict[str, int] = field(default_factory=dict)
    relationships: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)

    def note(self, bucket: dict[str, int], key: str, count: int) -> None:
        if count:
            bucket[key] = bucket.get(key, 0) + count

    def as_dict(self) -> dict[str, Any]:
        return {
            "projection_version": self.projection_version,
            "nodes": dict(sorted(self.nodes.items())),
            "relationships": dict(sorted(self.relationships.items())),
            "skipped": dict(sorted(self.skipped.items())),
        }


# --------------------------------------------------------------------------- #
# Reading MySQL
# --------------------------------------------------------------------------- #

def _load_entities() -> list[dict[str, Any]]:
    """Claim-eligible, active entities only.

    The filter is the point: a provisional identity must not exist in the graph
    at all, so no traversal can reach one.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_id, entity_type, canonical_name, normalized_name, "
            f"trust, cms_uuid, source, status FROM `{table}_entity` "
            "WHERE status = 'active' AND claim_eligible = 1"
        )
        return list(cur.fetchall())


def _load_aliases(entity_ids: set[str]) -> list[dict[str, Any]]:
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_id, normalized, surface, alias_type, autolink, "
            f"is_ambiguous FROM `{table}_entity_alias`"
        )
        return [r for r in cur.fetchall() if r["entity_id"] in entity_ids]


def _load_claims() -> list[dict[str, Any]]:
    from app.catalog import assertions as store

    return store.all_staged()


def _load_links() -> list[dict[str, Any]]:
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT from_claim_id, to_claim_id, kind, reason "
            f"FROM `{table}_assertion_link`"
        )
        return list(cur.fetchall())


def _load_documents(document_ids: set[str]) -> list[dict[str, Any]]:
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    if not document_ids:
        return []
    table = state_table()
    ids = sorted(document_ids)
    out: list[dict[str, Any]] = []
    with mysql_connection() as conn, conn.cursor() as cur:
        for start in range(0, len(ids), 500):
            batch = ids[start : start + 500]
            placeholders = ", ".join(["%s"] * len(batch))
            cur.execute(
                f"SELECT document_id, title, source_type, bundle, published_at, url "
                f"FROM `{table}` WHERE document_id IN ({placeholders})",
                batch,
            )
            out.extend(cur.fetchall())
    return out


def _iso(value: Any) -> str | None:
    from app.knowledge.claims.temporal import as_iso

    return as_iso(value)


# --------------------------------------------------------------------------- #
# Projection
# --------------------------------------------------------------------------- #

def project(
    *, session: Any = None, projection_version: str | None = None,
    as_of: str | None = None,
) -> ProjectionReport:
    """Project entities, claims, evidence and current state. Idempotent."""
    from app.core.clients.graph import write_session

    version = projection_version or make_projection_version()
    report = ProjectionReport(projection_version=version)

    entities = _load_entities()
    eligible_ids = {e["entity_id"] for e in entities}
    aliases = _load_aliases(eligible_ids)
    claims = _load_claims()
    links = _load_links()

    # A claim may only be projected when *both* ends are still eligible. The
    # entity store is authoritative here, not the claim row: a demotion since
    # staging must take effect without rewriting claims.
    projectable, refused = [], 0
    for claim in claims:
        if claim["subject_entity_id"] not in eligible_ids:
            refused += 1
            continue
        if claim["object_entity_id"] and claim["object_entity_id"] not in eligible_ids:
            refused += 1
            continue
        projectable.append(claim)
    report.note(report.skipped, "claim_entity_not_eligible", refused)

    document_ids = {c["document_id"] for c in projectable if c["document_id"]}
    chunk_ids = {c["chunk_id"] for c in projectable if c["chunk_id"]}
    documents = _load_documents(document_ids)

    def _run(open_session: Any) -> None:
        # --- entities ---------------------------------------------------- #
        rows = [
            {
                "entity_id": e["entity_id"],
                "canonical_name": e["canonical_name"],
                "normalized_name": e["normalized_name"],
                "entity_type": e["entity_type"],
                "trust": e["trust"],
                "claim_eligible": True,
                "cms_uuid": e["cms_uuid"],
                "source": e["source"],
                "status": e["status"],
            }
            for e in entities
        ]
        writer.run_batches(
            open_session, writer.MERGE_ENTITY, rows, projection_version=version
        )
        report.note(report.nodes, "Entity", len(rows))
        for entity_type, label in _TYPE_LABELS.items():
            typed = [r for r in rows if r["entity_type"] == entity_type]
            if not typed:
                continue
            statement = writer.ADD_TYPE_LABEL % writer.safe_label(label)
            writer.run_batches(open_session, statement, typed)
            report.note(report.nodes, label, len(typed))

        # --- aliases ------------------------------------------------------ #
        alias_rows = [
            {
                "entity_id": a["entity_id"],
                "alias_key": schema.alias_key(
                    a["entity_id"], a["normalized"], a["alias_type"]
                ),
                "normalized": a["normalized"],
                "surface": a["surface"],
                "alias_type": a["alias_type"],
                "autolink": bool(a["autolink"]),
                "is_ambiguous": bool(a["is_ambiguous"]),
            }
            for a in aliases
        ]
        writer.run_batches(open_session, writer.MERGE_ALIAS, alias_rows)
        report.note(report.nodes, "Alias", len(alias_rows))
        report.note(report.relationships, "HAS_ALIAS", len(alias_rows))

        # --- predicate vocabulary ----------------------------------------- #
        predicate_rows = [
            {
                "name": p.name, "description": p.description,
                "domain": list(p.domain), "range": list(p.range),
                "functional": p.functional, "object_kind": p.object_kind,
                "vocabulary_version": vocab.VOCABULARY_VERSION,
            }
            for p in vocab.PREDICATES.values()
        ]
        writer.run_batches(open_session, writer.MERGE_PREDICATE, predicate_rows)
        report.note(report.nodes, "Predicate", len(predicate_rows))

        # --- provenance stubs --------------------------------------------- #
        document_rows = [
            {
                "document_id": d["document_id"], "title": d["title"],
                "source_type": d["source_type"], "bundle": d["bundle"],
                "published_at": _iso(d["published_at"]), "url": d["url"],
            }
            for d in documents
        ]
        writer.run_batches(open_session, writer.MERGE_DOCUMENT, document_rows)
        report.note(report.nodes, "Document", len(document_rows))

        chunk_rows = [
            {"chunk_id": c["chunk_id"], "document_id": c["document_id"]}
            for c in projectable
            if c["chunk_id"]
        ]
        # Only chunks that actually carry a claim get a stub. A stub per corpus
        # chunk would put ~149k nodes in the graph for no traversal benefit.
        writer.run_batches(open_session, writer.MERGE_CHUNK, chunk_rows)
        report.note(report.nodes, "Chunk", len(chunk_ids))
        report.note(report.relationships, "PART_OF", len(chunk_rows))

        # --- claims -------------------------------------------------------- #
        claim_rows = [
            {
                "claim_id": c["claim_id"], "predicate": c["predicate"],
                "subject_id": c["subject_entity_id"],
                "object_id": c["object_entity_id"],
                "object_literal": c["object_literal"],
                "valid_from": _iso(c["valid_from"]),
                "valid_until": _iso(c["valid_until"]),
                "temporal_basis": c["temporal_basis"],
                "confidence": float(c["confidence"] or 0.0),
                "status": c["status"], "evidence_kind": c["evidence_kind"],
                "source_field": c["source_field"], "quote": c["quote"],
                "quote_start": c["quote_start"], "quote_end": c["quote_end"],
                "document_id": c["document_id"], "chunk_id": c["chunk_id"],
                "extraction_method": c["extraction_method"],
                "extractor_version": c["extractor_version"],
            }
            for c in projectable
        ]
        writer.run_batches(
            open_session, writer.MERGE_CLAIM, claim_rows,
            projection_version=version,
        )
        report.note(report.nodes, "Claim", len(claim_rows))

        writer.run_batches(open_session, writer.LINK_CLAIM_SUBJECT, claim_rows)
        report.note(report.relationships, "SUBJECT", len(claim_rows))
        with_object = [r for r in claim_rows if r["object_id"]]
        writer.run_batches(open_session, writer.LINK_CLAIM_OBJECT, with_object)
        report.note(report.relationships, "OBJECT", len(with_object))
        writer.run_batches(open_session, writer.LINK_CLAIM_PREDICATE, claim_rows)
        report.note(report.relationships, "USES_PREDICATE", len(claim_rows))

        with_chunk = [r for r in claim_rows if r["chunk_id"]]
        writer.run_batches(open_session, writer.LINK_CLAIM_CHUNK, with_chunk)
        without_chunk = [
            r for r in claim_rows if not r["chunk_id"] and r["document_id"]
        ]
        writer.run_batches(open_session, writer.LINK_CLAIM_DOCUMENT, without_chunk)
        report.note(
            report.relationships, "SUPPORTED_BY", len(with_chunk) + len(without_chunk)
        )

        # --- contradiction and supersession -------------------------------- #
        projected_ids = {r["claim_id"] for r in claim_rows}
        for kind, rel in (
            (cf.LINK_CONTRADICTS, "CONTRADICTS"),
            (cf.LINK_SUPERSEDES, "SUPERSEDES"),
        ):
            rows_for_kind = [
                {
                    "from_claim_id": l["from_claim_id"],
                    "to_claim_id": l["to_claim_id"],
                    "reason": l["reason"],
                }
                for l in links
                if l["kind"] == kind
                and l["from_claim_id"] in projected_ids
                and l["to_claim_id"] in projected_ids
            ]
            if not rows_for_kind:
                continue
            statement = writer.LINK_CLAIM_CLAIM % writer.safe_relationship(rel)
            writer.run_batches(open_session, statement, rows_for_kind)
            report.note(report.relationships, rel, len(rows_for_kind))

        # --- derived current state ----------------------------------------- #
        current = _current_state_rows(projectable, as_of=as_of)
        by_predicate: dict[str, list[dict]] = {}
        for row in current:
            by_predicate.setdefault(row["predicate"], []).append(row)
        for predicate_name, rows_for_predicate in sorted(by_predicate.items()):
            statement = (
                writer.PROJECT_CURRENT_STATE
                % writer.safe_relationship(predicate_name)
            )
            writer.run_batches(
                open_session, statement, rows_for_predicate,
                projection_version=version,
            )
            report.note(
                report.relationships, f"{predicate_name} (current)",
                len(rows_for_predicate),
            )
        # Anything from an older generation is no longer current.
        open_session.run(
            writer.DELETE_STALE_CURRENT_STATE, projection_version=version
        )

    if session is not None:
        _run(session)
    else:
        with write_session() as opened:
            _run(opened)

    logger.info("Projection %s complete: %s", version, report.as_dict())
    return report


def _current_state_rows(
    claims: list[dict[str, Any]], *, as_of: str | None
) -> list[dict[str, Any]]:
    """Claims that may become a current-state edge.

    Entity-valued only: a literal is a property, not a relationship, so
    ``HAS_ROLE`` never becomes an edge between two nodes.
    """

    class _Row:
        def __init__(self, data: dict[str, Any]) -> None:
            self.__dict__.update(data)
            self.valid_from = _iso(data.get("valid_from"))
            self.valid_until = _iso(data.get("valid_until"))

    rows: list[dict[str, Any]] = []
    for claim in claims:
        if not claim["object_entity_id"]:
            continue
        if not cf.is_current_state_eligible(_Row(claim), as_of=as_of):
            continue
        rows.append({
            "claim_id": claim["claim_id"],
            "predicate": claim["predicate"],
            "subject_id": claim["subject_entity_id"],
            "object_id": claim["object_entity_id"],
            "confidence": float(claim["confidence"] or 0.0),
            "valid_from": _iso(claim["valid_from"]),
            "valid_until": _iso(claim["valid_until"]),
            "temporal_basis": claim["temporal_basis"],
        })
    return rows
