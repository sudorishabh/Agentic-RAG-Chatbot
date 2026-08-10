"""Shadow-mode store for attachment date candidates (Phase 0).

Holds what each date source *would* say for every PDF the sweep touches, beside
what the pipeline actually assigned. Nothing reads it back into ingestion or
retrieval — it exists to be queried (see ``scripts.report_date_candidates``)
so the blast radius of a date correction can be measured on the real corpus
before any ``published_at`` moves.

Separate table, no foreign key, one row per document, overwritten each sweep:
a snapshot to compare against, not an audit trail. Writes fail open at the call
site, like every other catalog write in the ingestion path — a measurement that
cannot be recorded must never cost a document its ingestion.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.core.clients import mysql_connection
from app.core.dates import parse_iso_date

if TYPE_CHECKING:
    from app.ingestion.date_candidates import DateCandidates

__all__ = ["ShadowRow", "ensure_table", "record", "load", "summary"]


@dataclass
class ShadowRow:
    """One document's date candidates, as stored."""

    document_id: str
    origin: str
    node_created: str | None = None
    file_created: str | None = None
    pdf_created: str | None = None
    pdf_modified: str | None = None
    current: str | None = None
    proposed: str | None = None
    source: str = "node_created"
    rule: str = "default"
    delta_days: int | None = None
    would_move: bool = False
    url: str | None = None
    filename: str | None = None


_ensured = False


def ensure_table() -> None:
    """Create the table if it is missing, at most once per process.

    Called per attachment, so the DDL round-trip is cached: a sweep touches
    thousands of PDFs and none of them needs to re-ask whether the table
    exists. Reset :data:`_ensured` if a test drops the table underneath.
    """
    global _ensured
    if _ensured:
        return
    schema.ensure_date_shadow_table()
    _ensured = True


def _dt(value: str | None) -> datetime | None:
    """ISO string -> naive UTC datetime, matching the DATETIME columns."""
    return parse_iso_date(value, field="date candidate")


def record(candidates: "DateCandidates") -> None:
    """Store one document's candidates, replacing any earlier reading.

    Re-running a sweep re-measures rather than accumulating: a second row for
    the same document would only ever describe the same file, and the queries
    this feeds all ask "how many documents would move", which duplicates break.
    """
    if not candidates.document_id:
        return
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{_table()}_date_candidate` "
            "(document_id, origin, node_created, file_created, pdf_created,"
            " pdf_modified, current_date_, proposed_date, source, rule,"
            " delta_days, would_move, url, filename, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  origin = VALUES(origin),"
            "  node_created = VALUES(node_created),"
            "  file_created = VALUES(file_created),"
            "  pdf_created = VALUES(pdf_created),"
            "  pdf_modified = VALUES(pdf_modified),"
            "  current_date_ = VALUES(current_date_),"
            "  proposed_date = VALUES(proposed_date),"
            "  source = VALUES(source),"
            "  rule = VALUES(rule),"
            "  delta_days = VALUES(delta_days),"
            "  would_move = VALUES(would_move),"
            "  url = VALUES(url),"
            "  filename = VALUES(filename),"
            "  updated_at = VALUES(updated_at)",
            (
                candidates.document_id,
                candidates.origin,
                _dt(candidates.node_created),
                _dt(candidates.file_created),
                _dt(candidates.pdf_created),
                _dt(candidates.pdf_modified),
                _dt(candidates.current),
                _dt(candidates.proposed),
                candidates.source,
                candidates.rule,
                candidates.delta_days,
                1 if candidates.would_move else 0,
                (candidates.url or None),
                (candidates.filename or None),
                _now(),
            ),
        )
        conn.commit()


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


def load() -> list[ShadowRow]:
    """Every recorded reading, for the report script."""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT * FROM `{_table()}_date_candidate`")
        return [
            ShadowRow(
                document_id=row["document_id"],
                origin=row.get("origin") or "",
                node_created=_iso(row.get("node_created")),
                file_created=_iso(row.get("file_created")),
                pdf_created=_iso(row.get("pdf_created")),
                pdf_modified=_iso(row.get("pdf_modified")),
                current=_iso(row.get("current_date_")),
                proposed=_iso(row.get("proposed_date")),
                source=row.get("source") or "",
                rule=row.get("rule") or "",
                delta_days=row.get("delta_days"),
                would_move=bool(row.get("would_move")),
                url=row.get("url"),
                filename=row.get("filename"),
            )
            for row in cur.fetchall()
        ]


def summary() -> dict[str, Any]:
    """Counts by rule and origin — the headline blast-radius numbers."""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT rule, origin, would_move, COUNT(*) AS n "
            f"FROM `{_table()}_date_candidate` GROUP BY rule, origin, would_move"
        )
        rows = cur.fetchall()
    total = sum(int(r["n"]) for r in rows)
    moved = sum(int(r["n"]) for r in rows if r["would_move"])
    by_rule: dict[str, int] = {}
    by_origin: dict[str, int] = {}
    for r in rows:
        by_rule[r["rule"]] = by_rule.get(r["rule"], 0) + int(r["n"])
        by_origin[r["origin"]] = by_origin.get(r["origin"], 0) + int(r["n"])
    return {
        "total": total,
        "would_move": moved,
        "by_rule": by_rule,
        "by_origin": by_origin,
    }
