"""Does the corpus balance? MySQL against Qdrant, and the graph beside them.

Nothing compared the stores. The test suite was green, `/ready` was green,
`/metrics` was green, and the catalog said every document was indexed while 85
of them had no retrievable content at all. The defect that produced them was
found by one full scroll and three SQL queries — which is exactly what this
does, on every sweep, loudly.

Shape of it
-----------
One scroll of the collection builds a per-document picture (points, versions,
parents, payload stamps), one query builds the catalog's, and each invariant is
a :class:`Check` over the pair. A check reports a count, up to a handful of
example ids, and what to *do* about it — a number with no next step is how drift
gets watched rather than fixed.

Failure semantics
-----------------
This reads. It never deletes, re-indexes or repairs anything: a reconciliation
that acts on what it finds would be a second, unsupervised ingestion path, and
the failure mode of a wrong reading would be data loss rather than a wrong
number.

The optional stores are treated as optional. Neo4j is a derived projection, so
an unreachable graph is *skipped*, never a violation — a graph outage must not
make a healthy corpus look broken, and must certainly not make anything
destructive happen. Qdrant and MySQL are the system of record and its index; if
either cannot be read the report says so and fails, because at that point
nothing can be verified.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.ingestion.version import PIPELINE_VERSION

logger = logging.getLogger(__name__)

#: How many offending ids a check keeps. Enough to start an investigation,
#: few enough that a report of a broken corpus is still readable.
SAMPLE_LIMIT = 5

#: Payload fields the scroll needs. Everything else is left on the server —
#: chunk_text alone would be a hundred times the bytes.
_SCROLL_FIELDS = [
    "document_id", "doc_version", "is_parent", "chunk_id",
    "parent_chunk_id", "published_at", "pipeline_version",
]

__all__ = ["Check", "ReconciliationReport", "reconcile", "last_report"]


@dataclass(frozen=True)
class Check:
    """One invariant, and what violating it means."""

    name: str
    count: int
    detail: str
    samples: list[str] = field(default_factory=list)
    #: True when the check could not run (an optional store was unavailable).
    #: A skipped check is not a passing check and is never reported as one.
    skipped: bool = False

    @property
    def ok(self) -> bool:
        return self.skipped or self.count == 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "check": self.name,
            "count": self.count,
            "ok": self.ok,
            "skipped": self.skipped,
            "detail": self.detail,
            "samples": self.samples,
        }


@dataclass
class ReconciliationReport:
    documents: int = 0
    points: int = 0
    checks: list[Check] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and all(c.ok for c in self.checks)

    @property
    def drift(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "documents": self.documents,
            "points": self.points,
            "error": self.error,
            "checks": [c.as_dict() for c in self.checks],
        }

    def summary(self) -> str:
        """One line, in the shape the ingest run line already uses."""
        if self.error:
            return f"corpus_reconcile ok=false error={self.error!r}"
        parts = " ".join(f"{c.name}={c.count}" for c in self.checks)
        return (
            f"corpus_reconcile ok={str(self.ok).lower()} documents={self.documents} "
            f"points={self.points} {parts}"
        )


@dataclass
class _Catalogued:
    doc_version: int
    indexed: bool
    published_at: Any
    pipeline_version: str | None


@dataclass
class _Indexed:
    """What the collection holds for one document."""

    points: int = 0
    versions: set[int] = field(default_factory=set)
    undated: int = 0
    stale_version: int = 0
    id_mismatch: int = 0


def _read_catalog() -> dict[str, _Catalogued]:
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, doc_version, indexed_at, published_at, "
            f"pipeline_version FROM `{state_table()}`"
        )
        return {
            row["document_id"]: _Catalogued(
                doc_version=int(row["doc_version"] or 1),
                indexed=row["indexed_at"] is not None,
                published_at=row["published_at"],
                pipeline_version=row["pipeline_version"],
            )
            for row in cur.fetchall()
        }


def _read_collection(batch: int = 1024) -> tuple[dict[str, _Indexed], set[str], dict[str, str]]:
    """Scroll every point once. Returns (per document, parent ids, child->parent)."""
    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    settings = get_settings()
    client = get_qdrant_client()
    by_document: dict[str, _Indexed] = {}
    parent_ids: set[str] = set()
    child_parents: dict[str, str] = {}

    if not client.collection_exists(settings.qdrant_collection):
        return by_document, parent_ids, child_parents

    offset: Any = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=batch,
            offset=offset,
            with_payload=_SCROLL_FIELDS,
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            document_id = payload.get("document_id")
            if not document_id:
                continue
            state = by_document.setdefault(document_id, _Indexed())
            state.points += 1
            version = payload.get("doc_version")
            if version is not None:
                state.versions.add(int(version))
            if not payload.get("published_at"):
                state.undated += 1
            if payload.get("pipeline_version") != PIPELINE_VERSION:
                state.stale_version += 1
            if payload.get("chunk_id") and str(payload["chunk_id"]) != str(point.id):
                state.id_mismatch += 1
            if payload.get("is_parent"):
                parent_ids.add(str(point.id))
            elif payload.get("parent_chunk_id"):
                child_parents[str(point.id)] = str(payload["parent_chunk_id"])
        if offset is None:
            break
    return by_document, parent_ids, child_parents


def _check(name: str, offenders: list[str], detail: str) -> Check:
    return Check(
        name=name,
        count=len(offenders),
        detail=detail,
        samples=sorted(offenders)[:SAMPLE_LIMIT],
    )


def _graph_check() -> Check:
    """Neo4j against MySQL, when the deployment has a graph at all.

    Skipped — not failed — when the knowledge layer is off or the graph is
    unreachable. The graph is a projection that can be rebuilt from MySQL at any
    time, so its absence is a degraded knowledge layer and never evidence that
    the corpus is wrong.
    """
    from app.config import get_settings

    if not get_settings().knowledge_enabled:
        return Check("graph_projection", 0, "knowledge layer disabled", skipped=True)
    try:
        from app.core.clients import graph_available

        if not graph_available():
            return Check(
                "graph_projection", 0,
                "Neo4j unreachable; the projection was not checked. It rebuilds "
                "from MySQL with scripts.project_graph.",
                skipped=True,
            )
        # The graph's own MySQL-vs-graph diff, rather than a second opinion
        # written here.
        from app.ingestion.graph_sync import freshness, is_stale
        from app.knowledge.graph.verify import verify

        report = verify()
        problems = list(report.problems)

        # Content agreeing is not the same as the projection still running. A
        # graph that stopped being projected months ago agrees with MySQL about
        # everything it was told, and is wrong about everything since.
        state = freshness()
        if is_stale(state):
            hours = (state.get("age_seconds") or 0) / 3600
            problems.append(
                f"projection last ran {hours:.0f}h ago "
                f"({state.get('projected_at')}); the scheduled refresh may have "
                f"stopped"
            )
        elif not state.get("projected_at"):
            problems.append("the graph carries no projection stamp; it may never have been projected")

        return Check(
            "graph_projection",
            len(problems),
            "; ".join(problems[:3]) or "projection matches MySQL and is current",
            samples=problems[:SAMPLE_LIMIT],
        )
    except Exception as exc:
        return Check(
            "graph_projection", 0, f"projection check failed: {exc}", skipped=True
        )


#: Name patterns that make a source field *look* like it carries a date. Used
#: only to ask "has anyone classified this?", never to read a value — the
#: classification lives in ``app.ingestion.source_dates.FIELD_KINDS``.
_DATE_LIKE_FIELD = re.compile(r"date|year|publish|issued|period", re.I)


def date_checks() -> list[Check]:
    """Invariants over ``published_at`` and where it came from.

    Every one of these was zero when it was written, and each has a specific
    cause when it stops being zero. That is the bar for living here rather than
    in ``scripts.audit_dates``: a check that is non-zero in a healthy corpus
    would make every sweep warn, and a warning that is always on is not a
    warning. The audit script keeps the deeper measurements that are legitimately
    non-zero — 30 documents dated before the period their own name states, 2,796
    dated by an import batch with nothing better available.

    Read-only, and each check independently fail-soft: an unreadable catalogue
    reports a skipped check rather than failing a sweep that otherwise worked.
    """
    import json

    from app.catalog.db import state_table
    from app.core.clients import mysql_connection
    from app.ingestion.source_dates import (
        FIELD_KINDS,
        is_plausible,
        resolve_published_at,
        to_ist_date,
    )

    table = state_table()
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT document_id FROM `{table}` "
                f"WHERE published_at_source IS NULL LIMIT 200"
            )
            unrecorded = [r["document_id"] for r in cur.fetchall()]
            cur.execute(
                f"SELECT document_id FROM `{table}` "
                f"WHERE published_at_precision = 'year' "
                f"AND (MONTH(published_at) <> 1 OR DAY(published_at) <> 1) LIMIT 200"
            )
            mismatched_precision = [r["document_id"] for r in cur.fetchall()]
            cur.execute(
                f"SELECT document_id, raw_meta, published_at FROM `{table}` "
                f"WHERE raw_meta IS NOT NULL"
            )
            rows = list(cur.fetchall())
    except Exception as exc:
        logger.warning("Date checks could not read the catalogue.", exc_info=True)
        return [Check("date_invariants", 0,
                      f"not checked ({type(exc).__name__})", skipped=True)]

    not_applied: list[str] = []
    undeclared: list[str] = []
    for row in rows:
        try:
            meta = (json.loads(row["raw_meta"]) if isinstance(row["raw_meta"], str)
                    else row["raw_meta"])
        except (TypeError, ValueError):
            continue
        if not isinstance(meta, dict):
            continue
        # The same single decision ingestion and the backfill make. Asking
        # `publication_date` directly would be a third copy of the rule, and it
        # would miscount the 228 documents whose stated *year* the stored date
        # already falls in — cases the design deliberately leaves alone.
        stored = row["published_at"].isoformat()
        resolved, source, _precision = resolve_published_at(stored, meta)
        if source == "cms_field" and resolved and resolved[:10] != stored[:10]:
            not_applied.append(row["document_id"])
        for key, value in meta.items():
            if key in FIELD_KINDS or not _DATE_LIKE_FIELD.search(key):
                continue
            if value in (None, "", [], {}):
                continue
            candidate = value[0] if isinstance(value, list) and value else value
            if is_plausible(to_ist_date(candidate)):
                undeclared.append(row["document_id"])
                break

    return [
        _check("date_provenance_unrecorded", unrecorded,
               "Documents whose published_at has no recorded origin. Every write "
               "path sets it, so these came from one that does not — or predate "
               "scripts.backfill_date_provenance."),
        _check("stated_date_not_applied", not_applied,
               "The source states a publication date that published_at does not "
               "match. Either a sweep did not apply it, or something overwrote "
               "the value afterwards (app.ingestion.backfill lifts dates out of "
               "chunk payloads). Re-run scripts.backfill_source_dates."),
        _check("undeclared_source_date_field", undeclared,
               "A source field that looks like a date and holds a parseable one, "
               "which nothing has classified. It is being ignored — the safe "
               "direction — but if it is a publication date those documents are "
               "mis-dated. Classify it in app.ingestion.source_dates.FIELD_KINDS."),
        _check("year_precision_not_january", mismatched_precision,
               "A year-precision date whose value is not 1 January. The day is a "
               "marker for the year, so anything else means the value and its "
               "precision disagree about what is known."),
    ]


def reconcile() -> ReconciliationReport:
    """Compare the stores and report every way they disagree. Changes nothing."""
    report = ReconciliationReport()
    try:
        catalog = _read_catalog()
        indexed, parent_ids, child_parents = _read_collection()
    except Exception as exc:
        logger.exception("Reconciliation could not read the stores.")
        report.error = f"{type(exc).__name__}: {exc}"
        return report

    report.documents = len(catalog)
    report.points = sum(state.points for state in indexed.values())

    # A. Catalogued and indexed, but nothing in the collection. The F1 signature:
    # an empty extraction deleted the points and stamped indexed_at anyway.
    missing = [
        document_id for document_id, row in catalog.items()
        if row.indexed and document_id not in indexed
    ]
    report.checks.append(_check(
        "indexed_without_points", missing,
        "Documents the catalog reports as indexed that have no points at all. "
        "Clear their content hash (app.catalog.state.clear_change_markers) and "
        "let the next sweep rebuild them.",
    ))

    # B. Points for documents the catalog has never heard of: the delete path
    # leaving vectors behind, or an ingest that wrote points and lost its row.
    orphans = [document_id for document_id in indexed if document_id not in catalog]
    report.checks.append(_check(
        "points_without_catalog_row", orphans,
        "Documents with points but no catalog row. They are retrievable and "
        "uncatalogued; delete_document(id) removes them.",
    ))

    # C/D. Version agreement. A document serving two versions at once means a
    # swap did not complete; disagreeing with the catalog means it completed and
    # the row did not follow.
    mismatched, duplicated = [], []
    for document_id, state in indexed.items():
        if len(state.versions) > 1:
            duplicated.append(document_id)
        row = catalog.get(document_id)
        if row and state.versions and state.versions != {row.doc_version}:
            mismatched.append(document_id)
    report.checks.append(_check(
        "duplicate_live_versions", duplicated,
        "Documents whose points carry more than one doc_version — an "
        "interrupted swap. Re-index them to collapse it.",
    ))
    report.checks.append(_check(
        "version_mismatch", mismatched,
        "Documents whose points disagree with the catalog's doc_version. "
        "Re-index them; the catalog is authoritative.",
    ))

    # Chunk identity and parent integrity, free during the same scroll.
    report.checks.append(_check(
        "chunk_id_mismatch",
        [d for d, s in indexed.items() if s.id_mismatch],
        "Points whose payload chunk_id is not their own id. Citations resolve "
        "by payload, so these cite the wrong chunk.",
    ))
    dangling = [child for child, parent in child_parents.items() if parent not in parent_ids]
    report.checks.append(_check(
        "children_without_parent", dangling,
        "Child points naming a parent that does not exist. Context expansion "
        "falls back to the child alone for these.",
    ))

    # Pipeline drift, from both sides. The catalog says what a document was
    # built by; the points say what they were written by, and a document can be
    # stamped current while old points survive beside the new ones.
    report.checks.append(_check(
        "catalog_pipeline_drift",
        [d for d, row in catalog.items() if row.pipeline_version != PIPELINE_VERSION],
        f"Documents not built by pipeline {PIPELINE_VERSION}. Run "
        f"scripts.reprocess_corpus to rebuild them.",
    ))
    report.checks.append(_check(
        "point_pipeline_drift",
        [d for d, s in indexed.items() if s.stale_version],
        f"Documents with points written by a pipeline other than "
        f"{PIPELINE_VERSION}. Re-indexing replaces them.",
    ))

    # Dates. Not an error — some sources state none — but a document without one
    # is excluded from every date-filtered query rather than merely ranked low.
    report.checks.append(_check(
        "documents_without_date",
        [d for d, row in catalog.items() if row.published_at is None],
        "Documents with no publication date. They are invisible to date filters "
        "and to recency ranking; check the source exposes a date field.",
    ))

    report.checks += date_checks()
    report.checks.append(_graph_check())
    return report


_last: ReconciliationReport | None = None


def last_report() -> ReconciliationReport | None:
    """The most recent reconciliation this process ran, for /metrics to show.

    A full scroll is far too expensive to run from a probe, so the endpoint
    reports what the last sweep found rather than measuring on demand.
    """
    return _last


def reconcile_after_sweep() -> ReconciliationReport | None:
    """Reconcile at the end of a sweep, log the result, and never raise.

    Drift is logged at WARNING with the offending counts — the whole point is
    that it stops being silent — but it does not fail the sweep: the documents
    that ingested successfully did so, and refusing to admit that would help
    nobody. Nothing here repairs anything.
    """
    global _last
    from app.config import get_settings

    if not get_settings().verify_corpus_after_sweep:
        return None
    try:
        report = reconcile()
    except Exception:
        logger.exception("Reconciliation failed; the sweep itself is unaffected.")
        return None

    _last = report
    if report.ok:
        logger.info(report.summary())
    else:
        logger.warning(report.summary())
        for check in report.drift:
            logger.warning(
                "corpus_drift %s=%d samples=%s — %s",
                check.name, check.count, ", ".join(check.samples) or "-", check.detail,
            )
    return report
