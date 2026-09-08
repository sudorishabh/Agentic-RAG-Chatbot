"""Read back what every store holds for one document, after the run.

MySQL: every catalog and knowledge table, filtered to the document (or to its
chunk ids / content hashes / claim ids where the table has no document column).
Qdrant: every point whose payload names the document, with payload and a
vector summary. Neo4j: the document stub, its chunks, its claims and the
current-state edges those claims produced.
"""
from __future__ import annotations

from typing import Any, Iterable

from tools.e2e_ingest_audit.serialize import vector_summary


def _rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def existing_tables(prefix: str) -> list[str]:
    rows = _rows(
        "SELECT table_name AS t FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name LIKE %s ORDER BY table_name",
        (prefix + "%",),
    )
    return [r["t"] for r in rows]


def table_counts(tables: Iterable[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in tables:
        out[name] = int(_rows(f"SELECT COUNT(*) AS n FROM `{name}`")[0]["n"])
    return out


def _in(values: list[str]) -> str:
    return ", ".join(["%s"] * len(values))


def mysql_document(
    document_id: str,
    *,
    chunk_ids: list[str],
    content_hashes: list[str],
) -> dict[str, Any]:
    from app.catalog.db import log_table, state_table

    table = state_table()
    tables = set(existing_tables(table))
    out: dict[str, Any] = {}

    def maybe(name: str, sql: str, params: tuple) -> None:
        if name in tables:
            out[name] = _rows(sql, params)
        else:
            out[name] = None

    maybe(table, f"SELECT * FROM `{table}` WHERE document_id = %s", (document_id,))
    for suffix in ("author", "tag", "theme", "retry", "dead_link", "date_decision",
                   "entity_mention", "assertion", "assertion_rejection",
                   "predicate_candidate", "knowledge_run"):
        name = f"{table}_{suffix}"
        maybe(name, f"SELECT * FROM `{name}` WHERE document_id = %s ORDER BY 1", (document_id,))
    maybe(f"{table}_attachment",
          f"SELECT * FROM `{table}_attachment` WHERE document_id = %s ORDER BY file_uuid",
          (document_id,))
    if f"{table}_attachment" in tables:
        out[f"{table}_attachment (as file)"] = _rows(
            f"SELECT * FROM `{table}_attachment` WHERE file_uuid = %s ORDER BY document_id",
            (document_id,),
        )
    if chunk_ids and f"{table}_entity_resolution_decision" in tables:
        out[f"{table}_entity_resolution_decision"] = _rows(
            f"SELECT * FROM `{table}_entity_resolution_decision` "
            f"WHERE chunk_id IN ({_in(chunk_ids)}) ORDER BY chunk_id, start_offset",
            tuple(chunk_ids),
        )
    else:
        out[f"{table}_entity_resolution_decision"] = [] if chunk_ids else None
    if content_hashes and f"{table}_entity_extraction" in tables:
        out[f"{table}_entity_extraction"] = _rows(
            f"SELECT * FROM `{table}_entity_extraction` "
            f"WHERE content_hash IN ({_in(content_hashes)})",
            tuple(content_hashes),
        )
    else:
        out[f"{table}_entity_extraction"] = []
    claim_ids = [r["claim_id"] for r in (out.get(f"{table}_assertion") or [])]
    if claim_ids and f"{table}_assertion_link" in tables:
        out[f"{table}_assertion_link"] = _rows(
            f"SELECT * FROM `{table}_assertion_link` "
            f"WHERE from_claim_id IN ({_in(claim_ids)}) OR to_claim_id IN ({_in(claim_ids)})",
            tuple(claim_ids + claim_ids),
        )
    else:
        out[f"{table}_assertion_link"] = []
    log = log_table()
    if log in set(existing_tables(log)):
        out[log] = _rows(f"SELECT * FROM `{log}` WHERE document_id = %s ORDER BY id", (document_id,))
    else:
        out[log] = None
    # Entities referenced by this document's claims and decisions, so a reader
    # can see what an entity id denotes without a second lookup.
    entity_ids: set[str] = set()
    for row in out.get(f"{table}_assertion") or []:
        entity_ids.add(row.get("subject_entity_id"))
        entity_ids.add(row.get("object_entity_id"))
    for row in out.get(f"{table}_entity_resolution_decision") or []:
        entity_ids.add(row.get("entity_id"))
    entity_ids.discard(None)
    if entity_ids and f"{table}_entity" in tables:
        ids = sorted(entity_ids)
        out[f"{table}_entity (referenced)"] = _rows(
            f"SELECT * FROM `{table}_entity` WHERE entity_id IN ({_in(ids)})", tuple(ids)
        )
    else:
        out[f"{table}_entity (referenced)"] = []
    return out


def qdrant_document(document_id: str) -> dict[str, Any]:
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    if not client.collection_exists(collection):
        return {"collection": collection, "exists": False, "points": []}
    points: list[dict[str, Any]] = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
            limit=500, with_payload=True, with_vectors=True, offset=offset,
        )
        for point in batch:
            points.append({
                "id": str(point.id),
                "payload": dict(point.payload or {}),
                "vector": vector_summary(point.vector),
            })
        if offset is None:
            break
    points.sort(key=lambda p: (p["payload"].get("is_parent", False),
                               p["payload"].get("chunk_index", -1), p["id"]))
    return {"collection": collection, "exists": True, "count": len(points), "points": points}


def qdrant_collection_info() -> dict[str, Any]:
    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    if not client.collection_exists(collection):
        return {"collection": collection, "exists": False}
    info = client.get_collection(collection)
    return {
        "collection": collection,
        "exists": True,
        "points_count": info.points_count,
        "vector_size": getattr(info.config.params.vectors, "size", None),
        "distance": str(getattr(info.config.params.vectors, "distance", None)),
        "payload_indexes": sorted((info.payload_schema or {}).keys()),
    }


def _node(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"labels": sorted(value.labels), **dict(value)}


def _rel(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"type": value.type, **dict(value)}


def neo4j_document(document_id: str, claim_ids: list[str]) -> dict[str, Any]:
    from app.core.clients import graph_available, read_session

    if not graph_available():
        return {"reachable": False}
    out: dict[str, Any] = {"reachable": True}
    with read_session() as session:
        rows = session.run(
            "MATCH (d:Document {document_id: $id}) "
            "OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(d) "
            "RETURN d, collect(c) AS chunks", id=document_id,
        ).data()
        out["document_node"] = _node_from_data(rows[0]["d"]) if rows else None
        out["chunk_nodes"] = [c for c in (rows[0]["chunks"] if rows else []) if c]
        out["claims"] = session.run(
            "MATCH (cl:Claim {document_id: $id}) "
            "OPTIONAL MATCH (cl)-[:SUBJECT]->(s:Entity) "
            "OPTIONAL MATCH (cl)-[:OBJECT]->(o:Entity) "
            "OPTIONAL MATCH (cl)-[:USES_PREDICATE]->(p:Predicate) "
            "OPTIONAL MATCH (cl)-[:SUPPORTED_BY]->(ev) "
            "RETURN cl, s, o, p.name AS predicate, labels(ev) AS evidence_labels, "
            "ev.chunk_id AS evidence_chunk, ev.document_id AS evidence_document "
            "ORDER BY cl.claim_id", id=document_id,
        ).data()
        ids = sorted({c for c in claim_ids if c})
        out["current_state_edges"] = session.run(
            "MATCH (s:Entity)-[r]->(o:Entity) WHERE r.claim_id IN $ids "
            "RETURN type(r) AS type, properties(r) AS properties, "
            "s.entity_id AS subject_id, s.canonical_name AS subject, "
            "o.entity_id AS object_id, o.canonical_name AS object ORDER BY r.claim_id",
            ids=ids,
        ).data() if ids else []
        out["claim_nodes_for_staged_ids"] = session.run(
            "MATCH (cl:Claim) WHERE cl.claim_id IN $ids RETURN cl.claim_id AS claim_id",
            ids=ids,
        ).value() if ids else []
    return out


def _node_from_data(value: Any) -> Any:
    return value


def neo4j_stats() -> dict[str, Any]:
    from app.core.clients import graph_available, read_session

    if not graph_available():
        return {"reachable": False}
    with read_session() as session:
        labels = session.run(
            "MATCH (n) UNWIND labels(n) AS l RETURN l AS label, count(*) AS n ORDER BY l"
        ).data()
        rels = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n ORDER BY type"
        ).data()
        current = session.run(
            "MATCH ()-[r {current: true}]->() RETURN count(r) AS n"
        ).single()["n"]
        versions = session.run(
            "MATCH (n) WHERE n.projection_version IS NOT NULL "
            "RETURN n.projection_version AS v, count(*) AS n ORDER BY v"
        ).data()
    return {
        "reachable": True,
        "node_labels": {r["label"]: r["n"] for r in labels},
        "relationship_types": {r["type"]: r["n"] for r in rels},
        "current_state_edges": current,
        "projection_versions": {r["v"]: r["n"] for r in versions},
    }
