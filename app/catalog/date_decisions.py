"""Shadow storage for evidence-based PDF date decisions.

One row per PDF, holding what the resolver *would* propose and why: the
candidate, what kind of date it is, which rule or model produced it, the
confidence and the evidence sentence. Deliberately its own table, and
deliberately not ``CanonicalDocument.extra`` — ``build_payload`` does
``payload.update(m.extra)``, so anything parked there would flow straight into
Qdrant chunk payloads. Nothing reads this back into ingestion or retrieval.

Writes fail open at the call site, matching the rest of the ingestion path.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.core.clients import mysql_connection
from app.core.dates import parse_iso_date

if TYPE_CHECKING:
    from app.ingestion.date_rules import DateDecision

__all__ = ["DecisionRow", "ensure_table", "record", "load", "reset_cache"]

_ensured = False


def ensure_table() -> None:
    """Create the table if missing, at most once per process."""
    global _ensured
    if _ensured:
        return
    schema.ensure_date_decision_table()
    _ensured = True


def reset_cache() -> None:
    """Forget that the table was ensured (for tests that drop it)."""
    global _ensured
    _ensured = False


@dataclass
class DecisionRow:
    document_id: str
    origin: str
    bundle: str | None = None
    node_uuid: str | None = None
    page_pdf_count: int = 1
    current_published_at: str | None = None
    candidate_date: str | None = None
    date_type: str = "unknown"
    edition_label: str | None = None
    candidate_source: str = "node_created"
    confidence: float = 0.0
    action: str = "keep_page_date"
    rule: str = ""
    decided_by: str = "deterministic"
    evidence: str | None = None
    llm_raw: dict[str, Any] | None = None
    prompt_version: str | None = None
    url: str | None = None
    filename: str | None = None


def from_decision(
    decision: "DateDecision",
    *,
    origin: str,
    bundle: str | None,
    node_uuid: str | None,
    page_pdf_count: int,
    current_published_at: str | None,
    url: str | None,
    filename: str | None,
    llm_raw: dict[str, Any] | None = None,
    prompt_version: str | None = None,
) -> DecisionRow:
    return DecisionRow(
        document_id=decision.document_id,
        origin=origin,
        bundle=bundle,
        node_uuid=node_uuid,
        page_pdf_count=page_pdf_count,
        current_published_at=current_published_at,
        candidate_date=decision.candidate_date,
        date_type=decision.date_type,
        edition_label=decision.edition_label,
        candidate_source=decision.source,
        confidence=decision.confidence,
        action=decision.action,
        rule=decision.rule,
        decided_by=decision.decided_by,
        evidence=decision.evidence,
        llm_raw=llm_raw,
        prompt_version=prompt_version,
        url=url,
        filename=filename,
    )


def record(row: DecisionRow) -> None:
    """Store one decision, replacing any earlier reading for the document."""
    if not row.document_id:
        return
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{_table()}_date_decision` "
            "(document_id, origin, bundle, node_uuid, page_pdf_count,"
            " current_published_at, candidate_date, date_type, edition_label,"
            " candidate_source, confidence, action, rule, decided_by, evidence,"
            " llm_raw, prompt_version, url, filename, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
            " %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  origin = VALUES(origin), bundle = VALUES(bundle),"
            "  node_uuid = VALUES(node_uuid),"
            "  page_pdf_count = VALUES(page_pdf_count),"
            "  current_published_at = VALUES(current_published_at),"
            "  candidate_date = VALUES(candidate_date),"
            "  date_type = VALUES(date_type),"
            "  edition_label = VALUES(edition_label),"
            "  candidate_source = VALUES(candidate_source),"
            "  confidence = VALUES(confidence), action = VALUES(action),"
            "  rule = VALUES(rule), decided_by = VALUES(decided_by),"
            "  evidence = VALUES(evidence), llm_raw = VALUES(llm_raw),"
            "  prompt_version = VALUES(prompt_version), url = VALUES(url),"
            "  filename = VALUES(filename), updated_at = VALUES(updated_at)",
            (
                row.document_id, row.origin, row.bundle, row.node_uuid,
                int(row.page_pdf_count),
                parse_iso_date(row.current_published_at, field="current published_at"),
                parse_iso_date(row.candidate_date, field="candidate date"),
                row.date_type, row.edition_label, row.candidate_source,
                round(float(row.confidence), 3), row.action, row.rule, row.decided_by,
                row.evidence,
                json.dumps(row.llm_raw, ensure_ascii=False) if row.llm_raw else None,
                row.prompt_version, row.url, row.filename, _now(),
            ),
        )
        conn.commit()


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


def load() -> list[DecisionRow]:
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT * FROM `{_table()}_date_decision`")
        return [
            DecisionRow(
                document_id=row["document_id"],
                origin=row.get("origin") or "",
                bundle=row.get("bundle"),
                node_uuid=row.get("node_uuid"),
                page_pdf_count=int(row.get("page_pdf_count") or 1),
                current_published_at=_iso(row.get("current_published_at")),
                candidate_date=_iso(row.get("candidate_date")),
                date_type=row.get("date_type") or "unknown",
                edition_label=row.get("edition_label"),
                candidate_source=row.get("candidate_source") or "",
                confidence=float(row.get("confidence") or 0),
                action=row.get("action") or "",
                rule=row.get("rule") or "",
                decided_by=row.get("decided_by") or "",
                evidence=row.get("evidence"),
                prompt_version=row.get("prompt_version"),
                url=row.get("url"),
                filename=row.get("filename"),
            )
            for row in cur.fetchall()
        ]
