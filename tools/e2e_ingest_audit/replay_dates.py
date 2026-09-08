"""Replay the date resolver over catalogued attachments and diff the outcome.

Read-only. For each sampled attachment it rebuilds the evidence exactly as
ingestion does — the live JSON:API node (so anchor text, ``created`` and the
bundle's configured field are real), the live PDF bytes, ``build_evidence``,
``date_resolution.resolve`` — and compares the result with the date the catalog
currently holds. Nothing is written to any store.

The sample is stratified by how each link *routes*, taken from the baseline
written by the pre-change survey, so the effect of a routing change can be read
per population rather than as one average. Single-PDF links are included as a
control: they must not move.

    python -m tools.e2e_ingest_audit.replay_dates --baseline reports/date_model/baseline_attachment_routing.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SITE = "https://teriin.org"
JSONAPI = "https://teriin.org/jsonapi"

#: How many links to replay per routing case. Case 0 multi is the population the
#: multi-PDF change frees, so it gets the largest share.
DEFAULT_QUOTAS = {
    "Case 0 parent_bundle_date_field": 20,          # split single/multi below
    "Case 2 multi_pdf_no_evidence": 8,
    "Case 2 multi_pdf_url_month_matches": 8,
    "Case 2 multi_pdf_uploaded_with_page": 8,
    "Case 2 migration_cohort_no_evidence": 5,
    "Case 2 llm_interpreted": 6,
    "Case 1 single_pdf_page": 10,
}


def live_record(session: Any, entity_type: str, bundle: str, uuid: str) -> Any:
    """One live record, with its relationships resolved, as the crawl builds it."""
    from app.ingestion.extractors import drupal_extractor as dx

    url = f"{JSONAPI}/{entity_type}/{bundle}/{uuid}"
    probe = session.get(url, timeout=60)
    probe.raise_for_status()
    data = probe.json().get("data")
    if not data:
        return None
    fields = [n for n in (data.get("relationships") or {}) if n.startswith("field_")]
    full = session.get(url, params={"include": ",".join(fields)} if fields else None,
                       timeout=60)
    full.raise_for_status()
    doc = full.json()
    included = {(i["type"], i["id"]): i for i in doc.get("included", [])}
    return dx._build_record(doc["data"], included, bundle, SITE, entity_type=entity_type)


def parent_entity_types() -> dict[str, tuple[str, str]]:
    """``{parent document_id: (entity_type, bundle)}`` from the catalog."""
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT document_id, entity_type, bundle FROM documents "
                    "WHERE source_type = 'website'")
        return {r["document_id"]: (r["entity_type"] or "node", r["bundle"])
                for r in cur.fetchall()}


def replay_one(session: Any, link: dict[str, Any], parents: dict[str, tuple[str, str]]) -> dict[str, Any]:
    from app.ingestion.date_resolution import build_evidence, resolve
    from app.ingestion.extractors.attachment import fetch_attachment, resolve_parent_date

    out: dict[str, Any] = {**link}
    parent = parents.get(link["parent_id"])
    if parent is None:
        return {**out, "status": "skipped", "reason": "parent not catalogued"}
    entity_type, bundle = parent
    try:
        node = live_record(session, entity_type, bundle, link["parent_id"])
        if node is None:
            return {**out, "status": "skipped", "reason": "node gone from the site"}
        file = next((f for f in node.files if f.uuid == link["file_uuid"]), None)
        if file is None:
            return {**out, "status": "skipped", "reason": "file no longer linked"}
        content, _ = fetch_attachment(session, file.url, 60)
        parent_date = resolve_parent_date(node)
        got = resolve(build_evidence(document_id=link["file_uuid"], node=node,
                                     file=file, parent_date=parent_date), content)
    except Exception as exc:
        return {**out, "status": "error", "reason": f"{type(exc).__name__}: {exc}"[:160]}

    new_date = str(got.start_value)[:10] if got.start_value else None
    changed = new_date != link["date"]
    return {
        **out, "status": "replayed", "changed": changed,
        "new_date": new_date, "new_precision": got.start_precision,
        "new_rule": got.decision.rule if got.decision else None,
        "new_decided_by": got.decision.decided_by if got.decision else None,
        "new_source": "document_text" if got.overridden else "parent_page",
        "overridden": got.overridden,
        "pdfs_on_page": node and len([f for f in node.files if f.uuid]),
        "used": list(got.used),
        "read_the_file": "pdf_text" in got.used,
        "evidence": (got.decision.evidence if got.decision else "")[:400],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--out", default="reports/date_model/replay_multi_pdf.json")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--scale", type=float, default=1.0,
                        help="multiply every per-case quota")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from app.ingestion.extractors.drupal_extractor import _build_session

    links = json.load(open(args.baseline, encoding="utf-8"))["links"]
    by_case: dict[tuple, list] = defaultdict(list)
    for link in links:
        by_case[(link["forward_case"], link["shape"])].append(link)

    random.seed(args.seed)
    sample: list[dict] = []
    for (case, shape), group in sorted(by_case.items()):
        quota = int(DEFAULT_QUOTAS.get(case, 0) * args.scale)
        if case == "Case 0 parent_bundle_date_field":
            quota = int((14 if shape == "multi" else 6) * args.scale)
        if quota:
            sample.extend(random.sample(group, min(quota, len(group))))
    print(f"replaying {len(sample)} of {len(links)} attachment links "
          f"across {len(by_case)} routing cases\n")

    parents = parent_entity_types()
    session = _build_session(3)
    results: list[dict] = []
    try:
        for i, link in enumerate(sample, 1):
            r = replay_one(session, link, parents)
            results.append(r)
            mark = ("MOVED" if r.get("changed") else "same ") if r["status"] == "replayed" else r["status"]
            print(f"  [{i:>3}/{len(sample)}] {mark} {link['shape']:6} "
                  f"{(link['forward_case'] or '')[:34]:36} {link['date']} -> "
                  f"{r.get('new_date') or '-'} ({r.get('new_precision') or '-'}) "
                  f"{(r.get('new_rule') or r.get('reason') or '')[:40]}")
    finally:
        session.close()

    replayed = [r for r in results if r["status"] == "replayed"]
    moved = [r for r in replayed if r["changed"]]
    tally = Counter((r["shape"], r["forward_case"], "MOVED" if r["changed"] else "same")
                    for r in replayed)
    read = Counter((r["shape"], r["read_the_file"]) for r in replayed)

    print(f"\n{'shape':7}{'routing case':38}{'same':>6}{'moved':>7}")
    seen = set()
    for (shape, case, _), _n in tally.items():
        if (shape, case) in seen:
            continue
        seen.add((shape, case))
        print(f"{shape:7}{case[:36]:38}{tally[(shape, case, 'same')]:>6}"
              f"{tally[(shape, case, 'MOVED')]:>7}")
    print(f"\nreplayed {len(replayed)}, moved {len(moved)}, "
          f"skipped/errored {len(results) - len(replayed)}")
    print("file was read:", dict(read))
    if moved:
        print("\nmoves by rule:")
        for rule, n in Counter(r["new_rule"] for r in moved).most_common():
            print(f"  {rule:36} {n:>4}")
        for r in moved[:8]:
            print(f"\n  {r['file_uuid'][:44]}  {r['date']} -> {r['new_date']} "
                  f"({r['new_precision']}) via {r['new_rule']}")
            print(f"    {r['evidence'][:220]}")
    single_moved = [r for r in moved if r["shape"] == "single"]
    print(f"\nCONTROL — single-PDF links that moved: {len(single_moved)} "
          f"{'(expected 0)' if not single_moved else '*** REGRESSION ***'}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(args.out, "w", encoding="utf-8"), indent=2, default=str)
    print(f"\nwritten {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
