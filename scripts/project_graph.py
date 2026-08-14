"""Project the knowledge layer from MySQL into Neo4j.

Neo4j is a rebuildable projection: MySQL is authoritative, so this is always
safe to re-run and ``--rebuild`` is always available as the fix.

    python -m scripts.project_graph                # project / refresh
    python -m scripts.project_graph --rebuild      # drop and rebuild
    python -m scripts.project_graph --verify       # diff only, no writes
    python -m scripts.project_graph --as-of 2020-01-01
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

logger = logging.getLogger("project_graph")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Drop every node and project again from MySQL.",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Diff MySQL against the graph and report. Writes nothing.",
    )
    parser.add_argument(
        "--as-of", dest="as_of",
        help="Date the current-state projection is computed for (YYYY-MM-DD).",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from app.core.clients.graph import graph_available
    from app.knowledge.graph.schema import ensure_graph_schema
    from app.knowledge.graph.verify import rebuild, verify

    if not graph_available():
        # Fail-open is for the runtime paths; this is a deliberate operator
        # action, so an unreachable graph is worth stopping for.
        print("Neo4j is not reachable. Check NEO4J_* settings.")
        return 1

    if args.verify:
        report = verify(as_of=args.as_of)
        print(json.dumps(report.as_dict(), indent=2))
        print("\nVERIFY:", "OK" if report.ok else "MISMATCH")
        return 0 if report.ok else 1

    if args.rebuild:
        print(json.dumps(rebuild(as_of=args.as_of), indent=2))
    else:
        from app.knowledge.graph.project import project

        ensure_graph_schema()
        print(json.dumps(project(as_of=args.as_of).as_dict(), indent=2))

    report = verify(as_of=args.as_of)
    print("\nVERIFY:", "OK" if report.ok else "MISMATCH")
    for problem in report.problems:
        print("  !", problem)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
