"""Verify the graph against MySQL, and rebuild it when they disagree.

The projection is derived, so MySQL is always right and the graph is always the
thing that can be wrong. This diffs the two and reports; ``rebuild`` is the fix,
and it is always available because nothing in the graph is a system of record.

What is checked
---------------
* every claim-eligible entity is present, and no ineligible one is;
* every projectable claim is present;
* current-state edges exist only for claims that are still eligible for one —
  in particular **no disputed claim has a current edge**, which is the safety
  property the whole conflict layer exists to produce;
* every current-state edge carries a ``claim_id`` that resolves to a real claim.

The last two are the ones worth having: the first two would be caught by a
recount, but a disputed claim quietly keeping an edge would not.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VerificationReport:
    """Differences between MySQL and the graph."""

    expected: dict[str, int] = field(default_factory=dict)
    actual: dict[str, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "expected": dict(sorted(self.expected.items())),
            "actual": dict(sorted(self.actual.items())),
            "problems": list(self.problems),
        }


COUNT_ENTITIES = "MATCH (e:Entity) RETURN count(e) AS n"
COUNT_CLAIMS = "MATCH (c:Claim) RETURN count(c) AS n"
COUNT_ALIASES = "MATCH (a:Alias) RETURN count(a) AS n"
COUNT_CURRENT = "MATCH ()-[r {current: true}]->() RETURN count(r) AS n"

# A disputed or superseded claim must never back a current-state edge.
DISPUTED_WITH_EDGE = """
MATCH (c:Claim)
WHERE c.status <> 'active'
MATCH ()-[r {current: true, claim_id: c.claim_id}]->()
RETURN c.claim_id AS claim_id, c.status AS status LIMIT 25
"""

# Every current-state edge must trace back to a claim that exists.
ORPHAN_EDGES = """
MATCH ()-[r {current: true}]->()
WHERE NOT EXISTS { MATCH (c:Claim {claim_id: r.claim_id}) }
RETURN r.claim_id AS claim_id LIMIT 25
"""

# No provisional identity may exist in the graph at all.
INELIGIBLE_ENTITIES = """
MATCH (e:Entity)
WHERE e.claim_eligible <> true
RETURN e.entity_id AS entity_id, e.trust AS trust LIMIT 25
"""


def verify(*, session: Any = None, as_of: str | None = None) -> VerificationReport:
    """Diff MySQL against the graph. Never writes."""
    from app.catalog import assertions as store
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection
    from app.core.clients.graph import read_session
    from app.knowledge.graph.project import _current_state_rows, _load_entities

    report = VerificationReport()

    entities = _load_entities()
    eligible_ids = {e["entity_id"] for e in entities}
    claims = store.all_staged()
    projectable = [
        c
        for c in claims
        if c["subject_entity_id"] in eligible_ids
        and (not c["object_entity_id"] or c["object_entity_id"] in eligible_ids)
    ]
    current = _current_state_rows(projectable, as_of=as_of)

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS n FROM `{table}_entity_alias` a "
            f"JOIN `{table}_entity` e ON e.entity_id = a.entity_id "
            "WHERE e.status='active' AND e.claim_eligible=1"
        )
        alias_count = int(cur.fetchone()["n"])

    report.expected = {
        "Entity": len(entities),
        "Claim": len(projectable),
        "Alias": alias_count,
        "current_state_edges": len(current),
    }

    def _check(open_session: Any) -> None:
        report.actual = {
            "Entity": open_session.run(COUNT_ENTITIES).single()["n"],
            "Claim": open_session.run(COUNT_CLAIMS).single()["n"],
            "Alias": open_session.run(COUNT_ALIASES).single()["n"],
            "current_state_edges": open_session.run(COUNT_CURRENT).single()["n"],
        }
        for key, expected in report.expected.items():
            actual = report.actual.get(key, 0)
            if actual != expected:
                report.problems.append(
                    f"{key}: expected {expected}, graph has {actual}"
                )
        for row in open_session.run(DISPUTED_WITH_EDGE):
            report.problems.append(
                f"non-active claim {row['claim_id']} ({row['status']}) "
                "backs a current-state edge"
            )
        for row in open_session.run(ORPHAN_EDGES):
            report.problems.append(
                f"current-state edge cites missing claim {row['claim_id']}"
            )
        for row in open_session.run(INELIGIBLE_ENTITIES):
            report.problems.append(
                f"ineligible entity {row['entity_id']} ({row['trust']}) is in the graph"
            )

    if session is not None:
        _check(session)
    else:
        with read_session() as opened:
            _check(opened)
    return report


def rebuild(*, as_of: str | None = None) -> dict[str, Any]:
    """Drop the graph and project it again from MySQL.

    The always-available fix. Safe precisely because the graph is derived: a
    rebuild loses nothing, which is what made adopting a second database
    acceptable in the first place.
    """
    from app.core.clients.graph import write_session
    from app.knowledge.graph import writer
    from app.knowledge.graph.project import project
    from app.knowledge.graph.schema import ensure_graph_schema

    with write_session() as session:
        session.run(writer.DROP_ALL)
    ensure_graph_schema()
    report = project(as_of=as_of)
    logger.info("Rebuilt the graph: %s", report.as_dict())
    return report.as_dict()
