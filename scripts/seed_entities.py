"""Build the canonical entity store from CMS records.

Four steps, in order, because each depends on the last:

1. **seed** canonical entities, aliases and identifiers from CMS metadata;
2. **mine** acronym aliases from glosses the corpus actually writes
   ("The Energy and Resources Institute (TERI)"), pairing them to entities
   already seeded — which is why it cannot run first;
3. **mark ambiguity**, flagging every alias whose normalized form denotes more
   than one entity, which must run *after* the acronyms are in;
4. report what was built.

Idempotent: ``entity_id`` is derived from the seed source, so re-running
refreshes rather than duplicates. ``--rebuild`` clears first, which is the
supported path after a clean re-ingestion.

    python -m scripts.seed_entities              # seed / refresh
    python -m scripts.seed_entities --rebuild    # wipe and rebuild
    python -m scripts.seed_entities --skip-acronyms   # no corpus scan
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("seed_entities")


def _write_acronyms(found: list[tuple[str, str, int]]) -> int:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Delete every entity, alias, identifier and decision first.",
    )
    parser.add_argument(
        "--skip-acronyms", action="store_true",
        help="Skip the corpus scan for acronym glosses (needs Qdrant).",
    )
    parser.add_argument(
        "--skip-promotion", action="store_true",
        help="Leave every PI name provisional.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from app.catalog import entities as store
    from app.knowledge.seed import build_seed_entities, mine_acronym_aliases

    if args.rebuild:
        store.clear_all()
        print("  cleared existing entities, aliases, identifiers and decisions")

    counts = store.save_entities(build_seed_entities())
    print(
        f"  seeded {counts['entities']} entities, {counts['aliases']} aliases, "
        f"{counts['identifiers']} identifiers"
    )
    if counts["identifier_conflicts"]:
        # Two CMS records claiming one project code. Reported rather than
        # resolved: Tier 0 must stay a lookup, so an ambiguous code is better
        # left denoting nobody than denoting the wrong project.
        print(
            f"  {counts['identifier_conflicts']} identifier conflicts "
            "(two records claiming one code; first kept, see the log)"
        )

    if not args.skip_acronyms:
        written = _write_acronyms(mine_acronym_aliases())
        print(f"  mined {written} acronym aliases from observed glosses")

    print(f"  marked {store.mark_ambiguous_aliases()} alias rows ambiguous")

    # Promotion runs last: it needs the alias ambiguity marks above, and the
    # full person population to judge how crowded a surname is.
    if not args.skip_promotion:
        from app.knowledge.pi_promotion import apply_promotions, evaluate_promotions

        decisions = evaluate_promotions()
        promoted = apply_promotions(decisions)
        considered = len(decisions)
        print(
            f"  PI promotion: {considered} names considered, "
            f"{sum(1 for d in decisions if d.promote)} passed, {promoted} raised"
        )
    for entity_type, count in sorted(store.counts_by_type().items()):
        print(f"    {entity_type:14} {count}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
