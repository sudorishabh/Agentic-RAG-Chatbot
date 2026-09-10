"""Apply the Neo4j constraints and indexes, reconciling any that have drifted.

`ensure_graph_schema()` is idempotent and runs on the paths that need it, so a
healthy deployment needs nothing from this script. It exists for the case that
`CREATE ... IF NOT EXISTS` cannot fix on its own: an index whose *definition*
changed while its *name* did not.

That is not hypothetical. `document_published` was declared on `published_at`;
the date model replaced that property with `effective_start_date` and the DDL was
updated, but `IF NOT EXISTS` matches on the name, so the server kept the old
index and reported success. Measured on the deployed graph before this ran:
1,044 Document nodes, all 1,044 carrying `effective_start_date` and none
carrying `published_at` — an index over nothing, and every date-filtered
Document query a full label scan.

Indexes are derived structures: dropping and rebuilding one costs time, never
data. Nothing here reads, writes or deletes a node. Index builds run
server-side over existing nodes, so run it while no projection is in progress.

Usage:  python -m scripts.ensure_graph_indexes [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("ensure_graph_indexes")


def _show(session) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Every index the server holds that owns a label and properties.

    Token-lookup indexes own neither and are skipped: they are Neo4j's own, not
    this module's, and reading them as drift would drop them on every start.
    """
    out: dict[str, tuple[str, tuple[str, ...]]] = {}
    for record in session.run(
        "SHOW INDEXES YIELD name, labelsOrTypes, properties, type "
        "RETURN name, labelsOrTypes, properties, type"
    ):
        row = dict(record)
        labels, props = row.get("labelsOrTypes"), row.get("properties")
        if labels and props:
            out[row["name"]] = (labels[0], tuple(props))
    return out


def _elsewhere() -> set[str]:
    """Index names this module owns but does not declare in ``INDEXES``.

    A uniqueness constraint creates its own backing index and a fulltext index
    has its own DDL, so both appear in ``SHOW INDEXES`` without appearing in
    ``INDEXES``. Neither is drift and the migration never drops them — naming
    them keeps the report from calling them obsolete and alarming whoever reads
    it.
    """
    from app.knowledge.graph.schema import CONSTRAINTS, FULLTEXT_INDEXES

    names = {statement.split()[2] for statement in CONSTRAINTS}
    names |= {statement.split()[3] for statement in FULLTEXT_INDEXES}
    return names


def _classify(name, want, have, elsewhere, obsolete) -> str:
    if have is None:
        return "MISSING - will be created"
    if name in obsolete:
        return "OBSOLETE - will be dropped"
    if name in elsewhere:
        return "ok (constraint or fulltext)"
    if want is None:
        return "unknown to this module - left alone"
    if have == want:
        return "ok"
    return f"DRIFTED - declared on {list(want[1])}"


def _report(session, declared, heading: str) -> None:
    from app.knowledge.graph.schema import OBSOLETE_INDEXES

    stored = _show(session)
    elsewhere = _elsewhere()
    print()
    print(heading)
    print(f"  {'index':32} {'label':11} {'properties':34} state")
    for name in sorted(set(declared) | set(stored)):
        want, have = declared.get(name), stored.get(name)
        shown = have or want
        state = _classify(name, want, have, elsewhere, OBSOLETE_INDEXES)
        print(f"  {name:32} {shown[0]:11} {str(list(shown[1])):34} {state}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report the declared/stored comparison and change nothing.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from app.core.clients.graph import read_session, write_session
    from app.knowledge.graph.schema import (
        OBSOLETE_INDEXES, declared_indexes, ensure_graph_schema,
        migrate_index_drift, statements,
    )

    declared = declared_indexes()

    if args.dry_run:
        with read_session() as session:
            _report(session, declared, "Before (dry run - nothing changed):")
            stored = _show(session)
        drift = [n for n, have in stored.items()
                 if n in declared and have != declared[n]]
        obsolete = [n for n in OBSOLETE_INDEXES if n in stored]
        missing = [n for n in declared if n not in stored]
        untouched = sorted(set(stored) - set(declared) - _elsewhere()
                           - set(OBSOLETE_INDEXES))
        print()
        print(f"would drop {len(obsolete)} obsolete : {obsolete or '-'}")
        print(f"would drop {len(drift)} drifted  : {drift or '-'}")
        print(f"would create {len(missing)} missing : {missing or '-'}")
        print(f"would leave {len(untouched)} unknown  : {untouched or '-'}")
        return 0

    with write_session() as session:
        _report(session, declared, "Before:")
        dropped = migrate_index_drift(session)
        print()
        print(f"dropped {len(dropped)}: {dropped or '-'}")
        ensure_graph_schema(session=session)
        print(f"applied {len(statements())} schema statements")

    # A fresh session, so the report reflects committed server state rather
    # than anything cached on the writing one.
    with read_session() as session:
        _report(session, declared, "After:")
        stored = _show(session)

    bad = {n: have for n, have in stored.items()
           if n in declared and have != declared[n]}
    left = [n for n in OBSOLETE_INDEXES if n in stored]
    if bad or left:
        print()
        print(f"FAILED: still drifted {bad}, still present {left}")
        return 1
    print()
    print("Every declared index matches its declaration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
