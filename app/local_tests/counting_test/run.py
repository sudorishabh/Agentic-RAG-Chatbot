"""Catalog counting — MySQL integration harness.

Exercises the exact-number path (`state.count_documents` + the write / backfill /
delete-cascade plumbing) against a **real MySQL**, using a throwaway table
(`ingest_state_counttest`) that is created, seeded with known ground truth, and
dropped — the real `ingest_state` is never touched.

Unlike the sibling harnesses this one DOES need MySQL configured
(MYSQL_HOST/USER/PASSWORD/DATABASE); it needs neither Qdrant, Azure, nor network.

Run:  python -m app.local_tests.counting_test.run
"""

from __future__ import annotations

import sys
from datetime import datetime

from app.config import get_settings
from app.deps import mysql_connection
from app.ingestion import state
from app.ingestion.state import StateRecord

_TEST_TABLE = "ingest_state_counttest"

# Date bounds reused across checks (half-open [lo, hi)).
MAR15, MAR16 = datetime(2024, 3, 15), datetime(2024, 3, 16)
Y2024_LO, Y2024_HI = datetime(2024, 1, 1), datetime(2025, 1, 1)


def _rec(doc_id, bundle, authors, categories, published_at, source_type="website"):
    return StateRecord(
        document_id=doc_id,
        source_type=source_type,
        source_key=f"{bundle or source_type}/{doc_id}",
        fingerprint=doc_id,
        bundle=bundle,
        authors=authors,
        categories=categories,
        published_at=published_at,
    )


# Ground truth. "Sharma" (substring) hits e1, e2, n2, p1; e1 has two authors
# (dedup target); e3 sits exactly on the exclusive date bound; n2 has no date;
# pdf1 is a non-website doc that bundle/website counts must ignore.
_SEED = [
    _rec("e1", "events", ["Ravi Sharma", "A. Gupta"], ["Energy"], "2024-03-15T00:00:00+00:00"),
    _rec("e2", "events", ["Ravi Sharma"], ["Environment"], "2024-03-15T23:59:00+00:00"),
    _rec("e3", "events", [], [], "2024-03-16T00:00:00+00:00"),
    _rec("n1", "news", ["B. Rao"], [], "2023-11-01T00:00:00+00:00"),
    _rec("n2", "news", ["Ravi Sharma"], [], None),
    _rec("p1", "research_papers", ["Ravi Sharma", "C. Mehta"], [], "2024-07-01T00:00:00+00:00"),
    _rec("pdf1", None, [], [], None, source_type="pdf"),
]


def _drop_tables() -> None:
    table = state._table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS `{table}_author`")
        cur.execute(f"DROP TABLE IF EXISTS `{table}_category`")
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
        conn.commit()


def _child_rows(document_id: str, facet: str) -> int:
    table = state._table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS n FROM `{table}_{facet}` WHERE document_id = %s",
            (document_id,),
        )
        return int(cur.fetchone()["n"])


class _Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.total = 0

    def __call__(self, name: str, got, expected) -> None:
        self.total += 1
        ok = got == expected
        self.passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: got={got!r} expected={expected!r}")


def _run_checks(check: _Checks) -> None:
    cd = state.count_documents

    # --- Phase A: reads over the seeded ground truth -----------------------
    check("website total (pdf excluded)", cd(source_type="website"), 6)
    check("bundle=events", cd(source_type="website", bundle="events"), 3)
    check("bundle=news", cd(source_type="website", bundle="news"), 2)
    check("bundle=research_papers", cd(source_type="website", bundle="research_papers"), 1)
    check("unknown bundle -> 0 (not all)", cd(source_type="website", bundle="widgets"), 0)

    check("author 'Sharma' distinct docs", cd(source_type="website", author="Sharma"), 4)
    check("author 'Sharma' in events", cd(source_type="website", bundle="events", author="Sharma"), 2)
    check("author 'Gupta'", cd(source_type="website", author="Gupta"), 1)

    check(
        "date [Mar15,Mar16) excludes Mar16",
        cd(source_type="website", published_from=MAR15, published_to=MAR16),
        2,
    )
    check(
        "events on Mar15",
        cd(source_type="website", bundle="events", published_from=MAR15, published_to=MAR16),
        2,
    )
    check("year 2024", cd(source_type="website", published_from=Y2024_LO, published_to=Y2024_HI), 4)
    check(
        "events + Sharma + Mar15",
        cd(
            source_type="website", bundle="events", author="Sharma",
            published_from=MAR15, published_to=MAR16,
        ),
        2,
    )
    check(
        "null published_at excluded from year filter",
        cd(source_type="website", author="Sharma", published_from=Y2024_LO, published_to=Y2024_HI),
        3,
    )

    # --- Phase B: re-index replaces facet rows -----------------------------
    state.upsert(_rec("e1", "events", ["Solo Author"], ["Energy"], "2024-03-15T00:00:00+00:00"))
    check("author 'Sharma' after e1 re-index", cd(source_type="website", author="Sharma"), 3)
    check("author 'Solo'", cd(source_type="website", author="Solo"), 1)
    check("e1 author rows not duplicated", _child_rows("e1", "author"), 1)

    # --- Phase C: delete cascades to child rows ----------------------------
    state.delete(["e2"])
    check("bundle=events after delete e2", cd(source_type="website", bundle="events"), 2)
    check("author 'Sharma' after delete e2", cd(source_type="website", author="Sharma"), 2)
    check("e2 author rows cascade-deleted", _child_rows("e2", "author"), 0)

    # --- Phase D: backfill -------------------------------------------------
    check("backfill unknown id -> False", state.backfill_facets("nope", None, ["Ghost"], []), False)
    check("no orphan child for unknown id", cd(source_type="website", author="Ghost"), 0)
    check(
        "backfill existing id -> True",
        state.backfill_facets("e3", "2024-03-16T00:00:00+00:00", ["Backfilled"], ["Cat"]),
        True,
    )
    check("author 'Backfilled' after backfill", cd(source_type="website", author="Backfilled"), 1)
    state.backfill_facets("e3", "2024-03-16T00:00:00+00:00", ["Backfilled"], ["Cat"])
    check("backfill idempotent (no dup rows)", _child_rows("e3", "author"), 1)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    settings = get_settings()
    original = settings.ingest_state_table
    settings.ingest_state_table = _TEST_TABLE
    print(f"Catalog counting test — throwaway table: {_TEST_TABLE}\n")

    check = _Checks()
    try:
        _drop_tables()  # clean slate; also the MySQL connectivity probe
        state.ensure_table()
        for record in _SEED:
            state.upsert(record)
        _run_checks(check)
    except Exception as exc:  # noqa: BLE001 - report and exit, don't traceback-spam
        print(f"\nFAIL  Could not run (is MySQL configured?): {type(exc).__name__}: {exc}")
        return 2
    finally:
        try:
            _drop_tables()
        except Exception:
            pass
        settings.ingest_state_table = original

    print(f"\n{'=' * 60}\n{check.passed}/{check.total} checks passed")
    return 0 if check.passed == check.total else 2


if __name__ == "__main__":
    raise SystemExit(main())
