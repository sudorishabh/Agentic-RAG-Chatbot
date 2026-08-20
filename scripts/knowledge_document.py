"""Build the knowledge layer for one already-ingested document.

The manual counterpart of the ingest hook. Three uses, and the third is the one
that matters most in practice:

    python -m scripts.knowledge_document <document_id>
    python -m scripts.knowledge_document <document_id> --dry-run
    python -m scripts.knowledge_document --pending 20

* a document whose stage failed, once its cause is fixed;
* a document being examined during a review, with ``--dry-run`` so every gate
  runs and nothing is written;
* the retry queue, drained by hand rather than waiting for a sweep.

It runs the *same* :func:`app.knowledge.document_pipeline.process_document` the
ingest hook runs, so what it reports is what ingestion would have done. What it
does **not** do is any of the global work: seeding, acronym mining, ambiguity
marking and PI promotion are corpus-wide passes and belong to
``scripts.build_knowledge``. A document whose entity has never been seeded will
report ``unknown_subject`` here too, and the fix is to run that.

Unlike the hook, this is not gated on ``knowledge_process_after_index``: an
operator invoking it by name has already decided. It still respects
``knowledge_enabled``, because a deployment without a knowledge layer has no
stores for this to write to.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

logger = logging.getLogger("knowledge_document")

EXIT_OK = 0
EXIT_ERRORS = 1      # ran, but a document ended partial or failed
EXIT_FATAL = 2       # could not run at all


def _run_one(document_id: str, options: Any) -> dict[str, Any] | None:
    from app.knowledge.document_loader import load_document
    from app.knowledge.document_pipeline import process_document

    doc = load_document(document_id)
    if doc is None:
        print(f"  {document_id}: not catalogued, or has no current chunks")
        return None
    return process_document(doc, options).as_dict()


def _print(report: dict[str, Any]) -> None:
    from app.knowledge.reporting import print_stages

    counts = "  ".join(f"{k}={v}" for k, v in report["counts"].items() if v)
    print(
        f"{report['document_id']} v{report['doc_version']} "
        f"[{report['status']}] {report['seconds']}s  {report['knowledge_version']}"
    )
    print(f"  {counts or 'nothing produced'}")
    projection = report["projection"]
    print(
        f"  projection: {projection['status']}"
        + (f" {projection['version']} edges={projection['edges']}"
           if projection["version"] else "")
    )
    print_stages(report["stages"], indent="    ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "document_id", nargs="*",
        help="Document id(s) to process. Omit with --pending.",
    )
    parser.add_argument(
        "--pending", type=int, metavar="N", default=None,
        help="Instead of named documents, process up to N from the retry queue "
             "(failed, partial, or never run).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run every stage, including the gates that reject claims, and "
             "write nothing.",
    )
    parser.add_argument(
        "--with-mentions", action="store_true",
        help="Also extract and resolve mentions. Off by default: nothing reads "
             "those tables at query time, and it is the most expensive stage.",
    )
    parser.add_argument(
        "--no-projection", action="store_true",
        help="Stage to MySQL only. The graph catches up at the next "
             "project_after_sweep or scripts.project_graph.",
    )
    parser.add_argument(
        "--budget", type=float, default=None, metavar="SECONDS",
        help="Override the per-document wall-clock budget.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    from app.config import get_settings
    from app.knowledge.document_pipeline import StageOptions

    if not get_settings().knowledge_enabled:
        logger.error(
            "knowledge_enabled is off; this deployment has no knowledge layer "
            "to build. Set KNOWLEDGE_ENABLED=true to use it."
        )
        return EXIT_FATAL

    options = StageOptions.from_settings(
        dry_run=args.dry_run or None,
        with_mentions=args.with_mentions or None,
        with_projection=False if args.no_projection else None,
        budget_seconds=args.budget,
    )

    document_ids = list(args.document_id)
    if args.pending is not None:
        try:
            from app.catalog import knowledge_runs

            document_ids += [
                row["document_id"]
                for row in knowledge_runs.pending(
                    max_attempts=get_settings().knowledge_stage_max_attempts,
                    limit=args.pending,
                )
            ]
        except Exception:
            logger.exception("Could not read the knowledge retry queue.")
            return EXIT_FATAL
    if not document_ids:
        parser.error("give at least one document id, or use --pending N")

    reports: list[dict[str, Any]] = []
    try:
        for document_id in document_ids:
            report = _run_one(document_id, options)
            if report is not None:
                reports.append(report)
    except KeyboardInterrupt:
        logger.warning("Interrupted; everything already written stays valid.")
    except Exception:
        logger.exception("The knowledge build could not run.")
        return EXIT_FATAL

    if args.json:
        print(json.dumps(reports, indent=2, default=str))
    else:
        mode = "DRY RUN — nothing written" if args.dry_run else "writing"
        print(f"knowledge_document ({mode}, {len(reports)} document(s))")
        for report in reports:
            _print(report)

    return EXIT_ERRORS if any(r["status"] != "ok" for r in reports) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
