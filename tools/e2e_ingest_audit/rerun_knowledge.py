"""Re-run the per-document knowledge stage on documents from an audit run.

Uses the audit run's isolated stores (``e2e_audit_*`` MySQL tables and the
``e2e_audit_documents`` Qdrant collection, which the audit leaves in place) and
a throwaway Neo4j container, exactly as ``run_audit`` does. The stage is driven
through the same code the ingest hook and the catch-up sweep use
(``document_loader.load_document`` + ``document_pipeline.process_document``).

Because the mention-extraction cache would otherwise short-circuit the stage,
the cache rows for the chosen documents' chunks are cleared first — in the
isolated table only — so the run is a genuine re-extraction ending in real
model calls.

    python -m tools.e2e_ingest_audit.rerun_knowledge --run reports/e2e_ingest_audit/run-30docs --doc 12 --doc 13
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

from tools.e2e_ingest_audit.run_audit import PREFIX, _apply_env, _start_neo4j, _stop_neo4j
from tools.e2e_ingest_audit.serialize import dump_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, help="audit run directory")
    parser.add_argument("--doc", action="append", default=[], help="document folder number(s), e.g. 12")
    parser.add_argument("--keep-neo4j", action="store_true")
    args = parser.parse_args(argv)

    _apply_env(use_container=True)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from app.catalog.db import state_table
    from app.config import get_settings
    from app.core.clients import mysql_connection

    get_settings.cache_clear()
    settings = get_settings()
    table = state_table()
    assert table.startswith(PREFIX), table
    run_dir = Path(args.run)
    out_dir = run_dir / "knowledge_rerun"
    out_dir.mkdir(exist_ok=True)

    folders = []
    for number in args.doc:
        matches = glob.glob(str(run_dir / "documents" / f"{int(number):02d}_*"))
        if not matches:
            raise SystemExit(f"no document folder {number}")
        folders.append(Path(matches[0]))

    print(f"stores: MySQL {table!r}, Qdrant {settings.qdrant_collection!r}, Neo4j {settings.neo4j_uri}")
    print(f"LLM endpoint: {settings.azure_openai_endpoint} deployment {settings.azure_openai_model}")
    _start_neo4j(settings.neo4j_password)
    started = True
    try:
        from app.knowledge.document_loader import load_document
        from app.knowledge.document_pipeline import StageOptions, process_document
        from app.knowledge.candidates import reload_entity_index

        reload_entity_index()
        results = []
        for folder in folders:
            before = json.load(open(folder / "08_knowledge.json", encoding="utf-8"))
            document_id = before["knowledge_run_rows"][0]["document_id"]
            before_report = before["stage_report"]
            claims_stage = next(s for s in before_report["stages"] if s.get("stage") == "claims")
            failures_before = sum(
                1 for line in (folder / "log.txt").read_text(encoding="utf-8").splitlines()
                if "Claim extraction failed" in line
            )

            doc = load_document(document_id)
            if doc is None:
                print(f"!! {folder.name}: not loadable from the isolated stores")
                continue
            hashes = sorted({c.content_hash for c in doc.chunks if c.content_hash})
            with mysql_connection() as conn, conn.cursor() as cur:
                if hashes:
                    cur.execute(
                        f"DELETE FROM `{table}_entity_extraction` WHERE content_hash IN "
                        f"({', '.join(['%s'] * len(hashes))})", tuple(hashes),
                    )
                conn.commit()

            report = process_document(doc, StageOptions.from_settings())
            after = report.as_dict()
            after_claims = next(s for s in after["stages"] if s.get("stage") == "claims")

            with mysql_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    f"SELECT claim_id, subject_entity_id, predicate, object_entity_id, object_literal, "
                    f"confidence, status, quote, extraction_method FROM `{table}_assertion` "
                    f"WHERE document_id = %s ORDER BY claim_id", (document_id,),
                )
                staged = [dict(r) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT code, COUNT(*) n FROM `{table}_assertion_rejection` "
                    f"WHERE document_id = %s GROUP BY code", (document_id,),
                )
                rejections = {r["code"]: r["n"] for r in cur.fetchall()}
                cur.execute(
                    f"SELECT status, claims_built, claims_staged, claims_rejected, projection_status, errors "
                    f"FROM `{table}_knowledge_run` WHERE document_id = %s", (document_id,),
                )
                run_row = dict(cur.fetchone() or {})
                ids = sorted({e for c in staged for e in (c["subject_entity_id"], c["object_entity_id"]) if e})
                names = {}
                if ids:
                    cur.execute(
                        f"SELECT entity_id, canonical_name, entity_type FROM `{table}_entity` "
                        f"WHERE entity_id IN ({', '.join(['%s'] * len(ids))})", tuple(ids),
                    )
                    names = {r["entity_id"]: f"{r['canonical_name']} ({r['entity_type']})" for r in cur.fetchall()}

            result = {
                "folder": folder.name,
                "document_id": document_id,
                "before": {
                    "status": before_report["status"],
                    "llm_calls": claims_stage["counts"].get("llm_calls"),
                    "http_400_failures_in_log": failures_before,
                    "claims_built": before_report["counts"]["claims_built"],
                    "claims_staged": before_report["counts"]["claims_staged"],
                    "errors": before_report["errors"],
                },
                "after": {
                    "status": after["status"],
                    "llm_calls": after_claims["counts"].get("llm_calls"),
                    "llm_failures": after_claims["counts"].get("llm_failures"),
                    "claims_built": after["counts"]["claims_built"],
                    "claims_staged": after["counts"]["claims_staged"],
                    "claims_rejected": after["counts"]["claims_rejected"],
                    "rejection_counts": after["rejection_counts"],
                    "pending_predicates": after["counts"]["pending_predicates"],
                    "projection": after["projection"],
                    "errors": after["errors"],
                    "seconds": after["seconds"],
                },
                "run_row": run_row,
                "staged_claims": [
                    {**c, "subject": names.get(c["subject_entity_id"]),
                     "object": names.get(c["object_entity_id"])} for c in staged
                ],
                "rejections_in_table": rejections,
                "full_report": after,
            }
            results.append(result)
            print(f"[{folder.name[:38]}] before: status={result['before']['status']} calls={result['before']['llm_calls']} "
                  f"400s={failures_before} claims=0 | after: status={after['status']} calls={result['after']['llm_calls']} "
                  f"failures={result['after']['llm_failures']} built={after['counts']['claims_built']} "
                  f"staged={after['counts']['claims_staged']} rejected={after['counts']['claims_rejected']} "
                  f"{after['rejection_counts']} proj={after['projection']['status']} edges={after['projection']['edges']}")
            for c in staged:
                print(f"      {c['subject']} --{c['predicate']}--> {c['object'] or c['object_literal']!r} "
                      f"conf={float(c['confidence']):.2f} status={c['status']} quote={str(c['quote'])[:90]!r}")
        dump_json(out_dir / "results.json", results)
        print(f"written {out_dir / 'results.json'}")
        return 0
    finally:
        if started and not args.keep_neo4j:
            _stop_neo4j()


if __name__ == "__main__":
    raise SystemExit(main())
