"""Read/write path for canonical entities, aliases, identifiers and decisions.

Raw SQL, schema ensured once per process, batched writes — the conventions the
rest of ``app.catalog`` uses. Nothing here reaches Neo4j; projection is a later
phase and this layer is complete without it.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Sequence

from app.catalog import schema
from app.catalog.db import state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

_ensured = False


def _ensure() -> None:
    global _ensured
    if not _ensured:
        schema.ensure_resolution_tables()
        _ensured = True


def reset_ensure_cache() -> None:
    global _ensured
    _ensured = False


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #

def save_entities(entities: Sequence[Any]) -> dict[str, int]:
    """Persist seed entities with their aliases and identifiers.

    Upserts on the deterministic ``entity_id``, so re-seeding a clean corpus
    refreshes rather than duplicates. Identifiers use ``INSERT IGNORE``: the
    ``(scheme, value)`` primary key is the invariant that one identifier denotes
    one entity, and a collision means the *data* disagrees, which must not be
    silently overwritten.
    """
    _ensure()
    table = state_table()
    now = _now()
    counts = {"entities": 0, "aliases": 0, "identifiers": 0, "identifier_conflicts": 0}
    if not entities:
        return counts

    entity_rows = [
        (
            e.entity_id, e.entity_type, e.canonical_name[:512],
            e.normalized_name[:512], e.source, e.cms_uuid, e.trust, "active",
            1 if e.claim_eligible else 0, None, now, now,
        )
        for e in entities
    ]
    alias_rows = [
        (
            e.entity_id, _norm_for(e.entity_type, surface)[:512], surface[:512],
            alias_type, 1, 0, source,
        )
        for e in entities
        for surface, alias_type, source in e.aliases
        if surface.strip()
    ]
    identifier_rows = [
        (scheme, value, e.entity_id, e.source)
        for e in entities
        for scheme, value in e.identifiers
    ]

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO `{table}_entity` "
            "(entity_id, entity_type, canonical_name, normalized_name, source, "
            " cms_uuid, trust, status, claim_eligible, merged_into, created_at, "
            " updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE canonical_name=VALUES(canonical_name), "
            " normalized_name=VALUES(normalized_name), trust=VALUES(trust), "
            " claim_eligible=VALUES(claim_eligible), updated_at=VALUES(updated_at)",
            entity_rows,
        )
        counts["entities"] = len(entity_rows)
        if alias_rows:
            cur.executemany(
                f"INSERT IGNORE INTO `{table}_entity_alias` "
                "(entity_id, normalized, surface, alias_type, autolink, "
                " is_ambiguous, source) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                alias_rows,
            )
            counts["aliases"] = len(alias_rows)
        for scheme, value, entity_id, source in identifier_rows:
            cur.execute(
                f"SELECT entity_id FROM `{table}_entity_identifier` "
                "WHERE scheme=%s AND value=%s",
                (scheme, value),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    f"INSERT INTO `{table}_entity_identifier` "
                    "(scheme, value, entity_id, source) VALUES (%s,%s,%s,%s)",
                    (scheme, value, entity_id, source),
                )
                counts["identifiers"] += 1
            elif row["entity_id"] != entity_id:
                # Two entities claim one identifier. Recorded, never resolved
                # by guessing: Tier 0 must stay a lookup, so an ambiguous code
                # is better left denoting nobody than denoting the wrong one.
                counts["identifier_conflicts"] += 1
                logger.warning(
                    "Identifier %s=%s claimed by %s and %s; keeping the first.",
                    scheme, value, row["entity_id"], entity_id,
                )
        conn.commit()
    return counts


def _norm_for(entity_type: str, surface: str) -> str:
    from app.knowledge.normalize import normalize_for

    return normalize_for(entity_type, surface)


def mark_ambiguous_aliases() -> int:
    """Flag every alias whose normalized form denotes more than one entity.

    Data-driven rather than hand-listed, and the single most important
    false-merge guard: the moment a second "Sharma" or a second "Phoenix"
    appears, the shared surface stops autolinking for *everyone*, without anyone
    noticing it had become dangerous.
    """
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE `{table}_entity_alias` a "
            "JOIN ( "
            "  SELECT normalized FROM `{t}_entity_alias` "
            "  GROUP BY normalized HAVING COUNT(DISTINCT entity_id) > 1 "
            ") d ON d.normalized = a.normalized "
            "SET a.is_ambiguous = 1, a.autolink = 0".format(t=table)
        )
        changed = cur.rowcount
        conn.commit()
    logger.info("Marked %d alias rows ambiguous.", changed)
    return changed


def counts_by_type() -> dict[str, int]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_type, COUNT(*) AS n FROM `{table}_entity` "
            "WHERE status='active' GROUP BY entity_type"
        )
        return {r["entity_type"]: int(r["n"]) for r in cur.fetchall()}


def clear_all() -> None:
    """Drop every seeded row. The corpus is re-ingested clean, so rebuilding is
    the supported path and this is how a rebuild starts."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        for suffix in (
            "_entity_resolution_decision", "_entity_identifier",
            "_entity_alias", "_entity",
        ):
            cur.execute(f"DELETE FROM `{table}{suffix}`")
        conn.commit()


# --------------------------------------------------------------------------- #
# Lookups used by candidate generation
# --------------------------------------------------------------------------- #

def entity_by_identifier(scheme: str, value: str) -> dict[str, Any] | None:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT e.* FROM `{table}_entity_identifier` i "
            f"JOIN `{table}_entity` e ON e.entity_id = i.entity_id "
            "WHERE i.scheme=%s AND i.value=%s AND e.status='active'",
            (scheme, value),
        )
        return cur.fetchone()


def entities_by_normalized(entity_type: str, normalized: str) -> list[dict[str, Any]]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_entity` "
            "WHERE entity_type=%s AND normalized_name=%s AND status='active'",
            (entity_type, normalized),
        )
        return list(cur.fetchall())


def aliases_by_normalized(entity_type: str, normalized: str) -> list[dict[str, Any]]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT a.*, e.canonical_name, e.entity_type, e.trust "
            f"FROM `{table}_entity_alias` a "
            f"JOIN `{table}_entity` e ON e.entity_id = a.entity_id "
            "WHERE e.entity_type=%s AND a.normalized=%s AND e.status='active'",
            (entity_type, normalized),
        )
        return list(cur.fetchall())


def load_index() -> dict[str, Any]:
    """The whole entity index, for an in-process resolver.

    Resolution runs per mention over millions of mentions, so it cannot query
    per lookup. Loaded once and held, following the gazetteer's precedent.
    """
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_id, entity_type, canonical_name, normalized_name, "
            f"trust, source, claim_eligible FROM `{table}_entity` "
            "WHERE status='active'"
        )
        entities = {r["entity_id"]: r for r in cur.fetchall()}
        cur.execute(
            f"SELECT entity_id, normalized, surface, alias_type, autolink, "
            f"is_ambiguous FROM `{table}_entity_alias`"
        )
        aliases = list(cur.fetchall())
        cur.execute(f"SELECT scheme, value, entity_id FROM `{table}_entity_identifier`")
        identifiers = {(r["scheme"], r["value"]): r["entity_id"] for r in cur.fetchall()}
    return {"entities": entities, "aliases": aliases, "identifiers": identifiers}


# --------------------------------------------------------------------------- #
# Decisions
# --------------------------------------------------------------------------- #

def save_decisions(decisions: Sequence[Any]) -> int:
    """Append resolution decisions. Idempotent per mention span."""
    _ensure()
    if not decisions:
        return 0
    table = state_table()
    now = _now()
    rows = [
        (
            d.chunk_id, d.start_offset, d.end_offset, d.surface_text[:512],
            d.normalized_text[:512], d.entity_type, d.decision, d.entity_id,
            1 if d.claim_eligible else 0, d.tier, d.score, d.margin, d.reason[:255],
            json.dumps(d.candidate_audit), d.resolver_version, now,
        )
        for d in decisions
    ]
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO `{table}_entity_resolution_decision` "
            "(chunk_id, start_offset, end_offset, surface_text, normalized_text, "
            " entity_type, decision, entity_id, claim_eligible, tier, score, "
            " margin, reason, candidates, resolver_version, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE decision=VALUES(decision), "
            " entity_id=VALUES(entity_id), claim_eligible=VALUES(claim_eligible), "
            " tier=VALUES(tier), score=VALUES(score), "
            " margin=VALUES(margin), reason=VALUES(reason), "
            " candidates=VALUES(candidates), "
            " resolver_version=VALUES(resolver_version), created_at=VALUES(created_at)",
            rows,
        )
        conn.commit()
    return len(rows)


def decision_counts() -> dict[tuple[str, str], int]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_type, decision, COUNT(*) AS n "
            f"FROM `{table}_entity_resolution_decision` GROUP BY entity_type, decision"
        )
        return {(r["entity_type"], r["decision"]): int(r["n"]) for r in cur.fetchall()}
