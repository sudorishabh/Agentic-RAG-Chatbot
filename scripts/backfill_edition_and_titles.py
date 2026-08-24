"""Dry-run-first backfill of edition labels (B) and per-edition titles (C).

Both operate on already-ingested data. Nothing is re-extracted, re-chunked or
re-embedded: edition labels are rewritten in place on existing Qdrant points,
and titles come from the *page's* HTML (one JSON:API request), not from the PDFs.

  B. Normalise `edition_label` to YYYY-YY. The corpus currently holds
     "2024-25", "2020/21", "2019-2020" and "2017-2018" for the same kind of
     value, which makes the field unusable for filtering or sorting.

  C. Replace the inherited page title. All ten TERI annual reports are in-body
     attachments on one Drupal page, so every one is titled "Annual Reports".
     The page's link text names each edition; that text is also the only place
     one edition's label exists at all.

Default is a dry run that writes nothing. Pass --apply to commit, which touches
Qdrant payloads and `documents.title` for the affected documents only.

    python -m scripts.backfill_edition_and_titles            # show the diff
    python -m scripts.backfill_edition_and_titles --apply
"""
from __future__ import annotations

import argparse
import re
import sys

ANNUAL_REPORTS_NODE = "db669bde-858c-478b-9751-fb148d2ecfb4"
_SPAN = re.compile(r"(?<!\d)(20\d{2}|\d{2})\s*[-_/\u2013]\s*(\d{2,4})(?!\d)")


def normalise_edition(label: str | None) -> str | None:
    """Canonical YYYY-YY, or None when the value names no consecutive span."""
    if not label:
        return None
    for start, end in _SPAN.findall(str(label)):
        first = int(start) if len(start) == 4 else 2000 + int(start)
        second = int(end) % 100
        if 2000 <= first <= 2030 and (second - first % 100) % 100 == 1:
            return f"{first}-{second:02d}"
    return None


def anchor_titles() -> dict[str, str]:
    """{pdf url: link text} from the Annual Reports page. One request, no PDFs."""
    import requests

    from scripts._crawl_drupal_metadata import _inbody_pdfs

    response = requests.get(
        f"https://teriin.org/jsonapi/node/page/{ANNUAL_REPORTS_NODE}",
        headers={"Accept": "application/vnd.api+json"}, timeout=60,
    )
    response.raise_for_status()
    attrs = response.json()["data"]["attributes"]
    return {l["url"]: l["anchor"] for l in _inbody_pdfs(attrs) if l["anchor"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Commit the changes. Omit for a dry run.")
    parser.add_argument("--expect-titles", type=int, default=10,
                        help="Refuse to apply unless C targets exactly this many.")
    parser.add_argument("--expect-editions", type=int, default=5,
                        help="Refuse to apply unless B targets exactly this many.")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    from qdrant_client import models as qm

    from app.catalog.db import state_table
    from app.config import get_settings
    from app.core.clients import get_qdrant_client, mysql_connection

    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    table = state_table()

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, source_key, title FROM `{table}` "
            "WHERE source_type = 'pdf_attachment'"
        )
        catalog = {r["document_id"]: r for r in cur.fetchall()}
    by_url = {(r["source_key"] or ""): r for r in catalog.values()}

    points, _ = client.scroll(
        collection_name=collection,
        scroll_filter=qm.Filter(must=[qm.FieldCondition(
            key="source_type", match=qm.MatchValue(value="pdf_attachment"))]),
        limit=20000,
        with_payload=["document_id", "edition_label", "title", "file_url", "pdf_path"],
        with_vectors=False,
    )
    current: dict[str, dict] = {}
    chunk_counts: dict[str, int] = {}
    for point in points:
        payload = point.payload or {}
        doc_id = payload.get("document_id")
        if not doc_id:
            continue
        current.setdefault(doc_id, payload)
        chunk_counts[doc_id] = chunk_counts.get(doc_id, 0) + 1

    titles = anchor_titles()
    # Scope: only the PDFs the Annual Reports page links to. A generic
    # normalisation would also rewrite labels on unrelated documents (air
    # quality reports, TERI CBS material) that merely happen to be spelled
    # differently; those are deliberately left alone.
    in_scope_urls = set(titles)

    edition_changes: list[tuple[str, str, str, str, int]] = []
    title_changes: list[tuple[str, str, str, int]] = []
    for doc_id, payload in current.items():
        url = payload.get("file_url") or payload.get("pdf_path") or ""
        if url not in in_scope_urls:
            continue
        anchor = titles.get(url)
        # B — normalise, or derive from the link text when absent.
        have = payload.get("edition_label")
        want = normalise_edition(have) or normalise_edition(anchor)
        if want and want != have:
            edition_changes.append(
                (doc_id, payload.get("title") or "", str(have), want, chunk_counts[doc_id]))
        # C — the page's link text names this edition; the inherited title does not.
        if anchor and (payload.get("title") or "") != anchor:
            title_changes.append(
                (doc_id, payload.get("title") or "", anchor, chunk_counts[doc_id]))

    mode = "APPLY" if args.apply else "DRY RUN — nothing will be written"
    print(f"=== {mode} ===\n")
    print(f"B. edition_label normalisation, Annual Reports page only "
          f"— {len(edition_changes)} documents")
    print(f"{'current':<12}{'proposed':<12}{'chunks':>7}  title / document")
    for doc_id, title, have, want, n in sorted(edition_changes, key=lambda x: x[3]):
        print(f"{have:<12}{want:<12}{n:>7}  {title[:28]:<30}{doc_id}")

    print(f"\nC. title from the page's link text — {len(title_changes)} documents")
    print(f"{'current':<18}{'proposed':<26}{'chunks':>7}  document")
    for doc_id, have, want, n in sorted(title_changes, key=lambda x: x[2]):
        print(f"{have[:17]:<18}{want[:25]:<26}{n:>7}  {doc_id}")

    total_points = sum(n for *_, n in edition_changes) + sum(n for *_, n in title_changes)
    print(f"\nQdrant points whose payload would be rewritten: {total_points} "
          f"(set_payload only — no vectors touched, no re-embedding)")
    print(f"MySQL `{table}`.title rows updated: {len(title_changes)}")

    if not args.apply:
        print("\nNo changes written. Re-run with --apply to commit.")
        return 0

    # ---- pre-flight assertions ------------------------------------------
    # Fail before the first write, not after a partial one. These encode what
    # the reviewed dry run showed; a corpus that drifted since then stops the
    # run rather than silently rewriting something else.
    title_ids = {doc_id for doc_id, *_ in title_changes}
    edition_ids = {doc_id for doc_id, *_ in edition_changes}
    problems: list[str] = []
    if len(title_changes) != args.expect_titles:
        problems.append(
            f'C targets {len(title_changes)} documents, expected {args.expect_titles}')
    if len(edition_changes) != args.expect_editions:
        problems.append(
            f'B targets {len(edition_changes)} documents, expected {args.expect_editions}')
    stray = sorted(d for d in title_ids | edition_ids if not d.startswith('inbody:'))
    if stray:
        problems.append(f'not in-body documents: {stray}')
    outside = sorted(edition_ids - title_ids)
    if outside:
        problems.append(f'B targets documents off the Annual Reports page: {outside}')
    for _doc_id, _have, want, _n in title_changes:
        if not want.lower().startswith('annual report'):
            problems.append(f'unexpected proposed title: {want!r}')
    if problems:
        print(chr(10) + 'REFUSING TO APPLY:')
        for problem in problems:
            print(f'  - {problem}')
        return 1
    print(chr(10) + f'pre-flight OK: C={len(title_changes)} documents, '
          f'B={len(edition_changes)} documents, all in-body Annual Reports')

    def _invariants() -> dict:
        """published_at and the vector count, to prove neither moved."""
        import hashlib

        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f'SELECT document_id, published_at FROM `{table}` ORDER BY document_id')
            digest = hashlib.sha256()
            for row in cur.fetchall():
                digest.update((str(row['document_id']) + '|'
                               + str(row['published_at']) + chr(10)).encode())
        return {
            'published_at_checksum': digest.hexdigest()[:16],
            'qdrant_points': client.count(collection_name=collection, exact=True).count,
        }

    before_state = _invariants()

    for doc_id, _title, _have, want, _n in edition_changes:
        client.set_payload(
            collection_name=collection, payload={"edition_label": want},
            points=qm.Filter(must=[qm.FieldCondition(
                key="document_id", match=qm.MatchValue(value=doc_id))]),
        )
    from app.core.clients.vector_store import refresh_document_title

    with mysql_connection() as conn, conn.cursor() as cur:
        for doc_id, _have, want, _n in title_changes:
            refresh_document_title(doc_id, want)
            cur.execute(f"UPDATE `{table}` SET title = %s WHERE document_id = %s",
                        (want, doc_id))
        conn.commit()
    print(f"\napplied: {len(edition_changes)} edition labels, {len(title_changes)} titles")
    after_state = _invariants()
    print(chr(10) + 'invariants (must be identical):')
    for key in before_state:
        same = before_state[key] == after_state[key]
        print(f'  {key:<24}{before_state[key]!s:>20} -> {after_state[key]!s:<20}'
              + ('OK' if same else '*** CHANGED ***'))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
