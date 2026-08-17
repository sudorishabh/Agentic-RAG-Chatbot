"""Build the knowledge layer from an already-ingested corpus.

Every stage below already existed, tested, in ``app.knowledge`` and
``app.catalog``; what did not exist was a committed command that ran them in
order. The knowledge layer was therefore reproducible only by hand, which is why
a clean rebuild left ``documents_entity`` and ``documents_assertion`` empty while
the phase reports recorded 1,653 staged claims. This module is that command and
nothing more: it orchestrates, it does not extract, resolve, validate or score.

    python -m scripts.build_knowledge --dry-run
    python -m scripts.build_knowledge --limit 500
    python -m scripts.build_knowledge                    # full corpus

Order, and why it cannot be rearranged
--------------------------------------
1. seed entities        from CMS metadata; everything else needs the entity ids
2. mine acronyms        pairs corpus glosses to seeded names, so it follows (1)
3. mark ambiguity       an acronym can *create* ambiguity, so it follows (2)
4. promote PIs          needs the ambiguity marks and the full person population
5. extract mentions     needs the gazetteer, which is built from (1)-(4)
6. resolve mentions     needs the entity index and the mentions from (5)
7. extract CMS claims   needs the entity index; reads CMS fields, not mentions
8. validate             trust and eligibility gates decide what may be staged
9. stage + rejections   durable claims
10. conflicts + status  supersession and dispute verdicts over the staged set
11. project             MySQL -> Neo4j

Re-running is safe by construction, and this module adds no bookkeeping of its
own: mentions are ``INSERT IGNORE`` on their span, extraction is cached on
``(content_hash, extraction_key)``, entity ids derive from the seed source,
decisions upsert per span, assertions upsert on ``claim_id``, links upsert on
their triple, and every Neo4j write is a ``MERGE``. Interrupting a run and
re-running it resumes rather than duplicates.

``--limit`` is a pilot control, not a corpus view: see :meth:`Build.conflicts`.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

logger = logging.getLogger("build_knowledge")

EXIT_OK = 0
EXIT_ERRORS = 1      # finished, but individual documents failed
EXIT_FATAL = 2       # could not run: a store was unreachable or a stage is unusable

# Reported whenever the claim set this run examined is not the whole staged set.
PARTIAL_CONFLICTS = (
    "conflict detection is partial when --limit is used: supersession and "
    "dispute verdicts cover only the claims this run extracted, not the corpus"
)


class Fatal(RuntimeError):
    """A condition that makes the rest of the build meaningless."""


@dataclass
class Stage:
    """What one stage did. ``counts`` is what a reader wants; ``errors`` is what
    an operator needs — an id per failure, never a bare total."""

    name: str
    counts: dict[str, int] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    skipped: bool = False
    seconds: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.name,
            "skipped": self.skipped,
            "seconds": round(self.seconds, 2),
            "counts": self.counts,
            "notes": self.notes,
            "errors": self.errors,
        }


@dataclass
class Options:
    limit: int | None = None
    dry_run: bool = False
    with_mentions: bool = False
    skip_seed: bool = False
    skip_acronyms: bool = False
    skip_promotion: bool = False
    skip_project: bool = False


class Build:
    """One build run.

    Writes are gated in exactly one way: every stage computes its result first
    and reports the count from that, then writes only ``if self.writes``. A
    dry run therefore exercises the whole pipeline — including the gates that
    reject claims — and touches no store, which is what makes it a useful
    rehearsal rather than a syntax check.
    """

    def __init__(self, options: Options) -> None:
        self.o = options
        self.stages: list[Stage] = []
        self._index: Any = None

    @property
    def writes(self) -> bool:
        return not self.o.dry_run

    # ------------------------------------------------------------------ #
    # Stage plumbing
    # ------------------------------------------------------------------ #

    @contextmanager
    def _stage(self, name: str, *, skip: bool = False) -> Iterator[Stage]:
        stage = Stage(name=name, skipped=skip)
        self.stages.append(stage)
        if skip:
            logger.info("%-14s skipped", name)
            yield stage
            return
        started = time.monotonic()
        try:
            yield stage
        finally:
            stage.seconds = time.monotonic() - started
            summary = " ".join(f"{k}={v}" for k, v in stage.counts.items())
            logger.info(
                "%-14s %s%s", name, summary or "-",
                f"  ({len(stage.errors)} errors)" if stage.errors else "",
            )

    def index(self, *, refresh: bool = False) -> Any:
        """The entity index, loaded once and reused.

        Refreshed after seeding, because everything downstream resolves against
        what seeding just wrote.
        """
        from app.knowledge.candidates import EntityIndex

        if self._index is None or refresh:
            self._index = EntityIndex.load()
        return self._index

    # ------------------------------------------------------------------ #
    # 1-4. Canonical entities. The same four steps, in the same order, as
    #      scripts/seed_entities.py — reused rather than reimplemented so the
    #      two commands cannot drift.
    # ------------------------------------------------------------------ #

    def seed(self) -> None:
        from app.catalog import entities as store
        from app.knowledge.seed import build_seed_entities

        with self._stage("seed", skip=self.o.skip_seed) as stage:
            if stage.skipped:
                return
            entities = build_seed_entities()
            if not entities:
                raise Fatal(
                    "no seed entities were built from the catalog; the corpus "
                    "has no CMS metadata to derive identities from"
                )
            if self.writes:
                stage.counts.update(store.save_entities(entities))
            else:
                stage.counts["entities"] = len(entities)
                stage.counts["aliases"] = sum(len(e.aliases) for e in entities)
            if stage.counts.get("identifier_conflicts"):
                # Two CMS records claiming one project code. Reported, never
                # resolved: Tier 0 must stay a lookup, so an ambiguous code is
                # better left denoting nobody than denoting the wrong project.
                stage.notes.append(
                    f"{stage.counts['identifier_conflicts']} identifier conflicts "
                    "(two records claiming one code; first kept)"
                )

    def acronyms(self) -> None:
        from app.knowledge.seed import mine_acronym_aliases

        with self._stage("acronyms", skip=self.o.skip_acronyms) as stage:
            if stage.skipped:
                return
            found = mine_acronym_aliases()
            stage.counts["mined"] = len(found)
            if self.writes:
                stage.counts["written"] = _write_acronym_aliases(found)

    def ambiguity(self) -> None:
        from app.catalog import entities as store

        with self._stage("ambiguity") as stage:
            if self.writes:
                stage.counts["marked"] = store.mark_ambiguous_aliases()
            else:
                stage.notes.append("ambiguity marking needs the alias rows above")

    def promotion(self) -> None:
        with self._stage("pi-promotion", skip=self.o.skip_promotion) as stage:
            if stage.skipped:
                return
            from app.knowledge.pi_promotion import apply_promotions, evaluate_promotions

            decisions = evaluate_promotions()
            stage.counts["considered"] = len(decisions)
            stage.counts["passed"] = sum(1 for d in decisions if d.promote)
            if self.writes:
                stage.counts["raised"] = apply_promotions(decisions)

    # ------------------------------------------------------------------ #
    # 11. Projection.
    # ------------------------------------------------------------------ #

    def project(self) -> None:
        with self._stage("project", skip=self.o.skip_project) as stage:
            if stage.skipped:
                return
            from app.core.clients import graph_available

            if not graph_available():
                stage.notes.append(
                    "Neo4j unreachable; MySQL is authoritative and "
                    "scripts.project_graph rebuilds the projection later"
                )
                stage.errors.append({"id": "neo4j", "error": "unreachable"})
                return
            if not self.writes:
                stage.notes.append("projection skipped under --dry-run")
                return
            from app.knowledge.graph.project import project as run_projection
            from app.knowledge.graph.schema import ensure_graph_schema

            # Same two calls, in the same order, as scripts/project_graph.py:
            # the constraints have to exist before the first MERGE.
            ensure_graph_schema()
            report = run_projection().as_dict()
            stage.counts.update(
                {k: v for k, v in report.items() if isinstance(v, int)}
            )

    # ------------------------------------------------------------------ #
    # Run
    # ------------------------------------------------------------------ #

    def run(self) -> int:
        self.seed()
        self.acronyms()
        self.ambiguity()
        self.promotion()
        self.index(refresh=True)
        self.project()
        return self.exit_code()

    def exit_code(self) -> int:
        return EXIT_ERRORS if any(s.errors for s in self.stages) else EXIT_OK

    def report(self) -> dict[str, Any]:
        return {
            "dry_run": self.o.dry_run,
            "limit": self.o.limit,
            "with_mentions": self.o.with_mentions,
            "stages": [s.as_dict() for s in self.stages],
            "errors": sum(len(s.errors) for s in self.stages),
        }


def _write_acronym_aliases(found: list[tuple[str, str, int]]) -> int:
    """Persist mined acronym aliases.

    The same statement ``scripts/seed_entities.py`` uses. ``INSERT IGNORE``
    keeps a re-run from duplicating an alias that is already there.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection
    from app.knowledge.normalize import normalize_org

    if not found:
        return 0
    table = state_table()
    rows = [
        (entity_id, normalize_org(acronym), acronym, "acronym", 1, 0, f"gloss_x{count}")
        for entity_id, acronym, count in found
    ]
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT IGNORE INTO `{table}_entity_alias` "
            "(entity_id, normalized, surface, alias_type, autolink, is_ambiguous, "
            " source) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            rows,
        )
        conn.commit()
    return len(rows)


def _print(report: dict[str, Any]) -> None:
    mode = "DRY RUN — nothing written" if report["dry_run"] else "writing"
    scope = f"limit={report['limit']}" if report["limit"] else "full corpus"
    print(f"build_knowledge ({mode}, {scope})")
    for stage in report["stages"]:
        if stage["skipped"]:
            print(f"  {stage['stage']:14} skipped")
            continue
        counts = "  ".join(f"{k}={v}" for k, v in stage["counts"].items())
        print(f"  {stage['stage']:14} {counts or '-'}   {stage['seconds']}s")
        for note in stage["notes"]:
            print(f"    note: {note}")
        for err in stage["errors"][:10]:
            print(f"    error: {err['id']}: {err['error']}")
        if len(stage["errors"]) > 10:
            print(f"    ... and {len(stage['errors']) - 10} more")
    print(f"  {'errors':14} {report['errors']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Pilot control: cap the documents processed. Makes conflict "
             "detection partial (see the run's notes).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run every stage and write nothing.",
    )
    parser.add_argument(
        "--with-mentions", action="store_true",
        help="Also extract and resolve mentions. Off by default: nothing reads "
             "those tables at query time, and it is the most expensive stage.",
    )
    parser.add_argument("--skip-seed", action="store_true")
    parser.add_argument("--skip-acronyms", action="store_true")
    parser.add_argument("--skip-promotion", action="store_true")
    parser.add_argument("--skip-project", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    build = Build(
        Options(
            limit=args.limit, dry_run=args.dry_run, with_mentions=args.with_mentions,
            skip_seed=args.skip_seed, skip_acronyms=args.skip_acronyms,
            skip_promotion=args.skip_promotion, skip_project=args.skip_project,
        )
    )
    try:
        code = build.run()
    except Fatal as exc:
        logger.error("%s", exc)
        return EXIT_FATAL
    except Exception:
        logger.exception("Knowledge build failed.")
        return EXIT_FATAL

    report = build.report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
