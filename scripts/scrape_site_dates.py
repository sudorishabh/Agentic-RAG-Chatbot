"""Fetch every date the live site states, then compare it with what we store.

The question this answers is not "do our two stores agree" — ``audit_dates``
already covers that — but **is what we store what the site says**, document by
document, with nothing skipped.

Metadata only. It reads the JSON:API, which returns every node's fields in
pages of fifty, and never downloads a PDF body. So it cannot reach Document
Intelligence and cannot cost extraction money.

Three outcomes per document, and the third is the interesting one:

``agrees``
    We store what the site states, and the site states a real publication date.

``disagrees``
    We store something the site contradicts. Our bug.

``page_dated``
    We store what the site states, and the site's own value is a *page* or
    *import* stamp rather than the document's own date. All ten annual reports
    are here: Drupal genuinely says 2022-02-09 for every one of them, so we are
    faithful to a source that does not know. Being faithful is not being right,
    and this is the population where nothing in the data can help.

    python -m scripts.scrape_site_dates --fetch      # write the site snapshot
    python -m scripts.scrape_site_dates              # compare against it
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Iterator

SNAPSHOT = os.path.join("reports", "dates", "site_truth.json")

#: Node bundles plus the non-node resources the crawl also catalogues. Taken
#: from the live catalogue rather than hardcoded, so a bundle that exists locally
#: cannot be silently skipped.
_NON_NODE = {"basic": "block_content"}

#: Fields that state something about *this document's* date, and what kind. The
#: classification is `app.ingestion.source_dates.FIELD_KINDS`; repeated here only
#: as the set worth pulling out of the payload.
_KEEP_PREFIX = ("field_", )


def _bundles() -> list[tuple[str, str]]:
    """``(entity_type, bundle)`` for everything the catalogue actually holds."""
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT DISTINCT COALESCE(entity_type, 'node') et, bundle "
            f"FROM `{state_table()}` WHERE bundle IS NOT NULL ORDER BY bundle"
        )
        rows = cur.fetchall()
    out = []
    for row in rows:
        bundle = row["bundle"]
        entity = _NON_NODE.get(bundle, row["et"] or "node")
        if (entity, bundle) not in out:
            out.append((entity, bundle))
    return out


def _date_fields(attributes: dict[str, Any]) -> dict[str, Any]:
    """Every field-ish attribute whose value could be a date, kept verbatim."""
    out: dict[str, Any] = {}
    for key, value in attributes.items():
        if not key.startswith(_KEEP_PREFIX) or value in (None, "", [], {}):
            continue
        if not any(w in key.lower() for w in ("date", "year", "period", "time")):
            continue
        out[key] = value[0] if isinstance(value, list) and value else value
    return out


def _paged(session, url: str, params: dict, timeout: float,
           *, tries: int = 4) -> Iterator[tuple[list[dict], dict]]:
    """Walk a JSON:API collection by explicit offset, retrying each page.

    Offsets rather than ``links.next`` so a single page that fails can be
    retried in place instead of breaking the chain and truncating the bundle.
    Stops on the first short page, which is how a JSON:API collection ends.
    """
    limit = int(params.get("page[limit]") or 50)
    offset = 0
    while True:
        page = dict(params, **{"page[offset]": offset})
        for attempt in range(tries):
            try:
                response = session.get(url, params=page, timeout=timeout)
                response.raise_for_status()
                doc = response.json()
                break
            except Exception:
                if attempt == tries - 1:
                    raise
                time.sleep(1.5 * (attempt + 1))
        data = doc.get("data") or []
        if isinstance(data, dict):
            data = [data]
        included = {(i["type"], i["id"]): i for i in doc.get("included", [])}
        yield data, included
        if len(data) < limit:
            return
        offset += limit


def fetch() -> dict[str, Any]:
    """One pass over the JSON:API. Returns ``{uuid: what the site states}``."""
    import requests

    from app.config import get_settings
    from app.ingestion.extractors.drupal_extractor import (
        HEADERS,
        _normalize_link,
        _site_base,
        _sort_key,
    )
    from scripts._crawl_drupal_metadata import _inbody_pdfs

    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    site = _site_base(base)
    session = requests.Session()
    session.headers.update(HEADERS)

    nodes: dict[str, Any] = {}
    files: dict[str, Any] = {}
    failures: list[str] = []
    for entity, bundle in _bundles():
        url = f"{base}/{entity}/{bundle}"
        # `_sort_key`, not a plain "-changed". Thousands of records share one
        # `changed` value from the 2017 migration, and offset pagination over a
        # non-unique sort has no defined order among the ties: some records come
        # back on two pages and others on none. The ingestion crawler already
        # solved this by appending the entity's serial id, and writing a sort
        # param here by hand reintroduced it — 1,270 of 8,644 fetched records
        # were duplicates, so 1,264 documents looked absent from the site.
        params = {"page[limit]": settings.drupal_page_size,
                  "sort": _sort_key(entity, ascending=False),
                  "filter[status]": 1}
        # A set, so a duplicate can never look like progress again — the
        # previous counter incremented per record and reached 1,663 for news
        # while storing 1,490.
        fetched: set[str] = set()
        # Retried per page and never abandoned mid-bundle. The first version
        # wrapped the whole walk in one `except: continue`, so a single transient
        # error dropped every remaining page of that bundle — 1,264 nodes went
        # missing that way, and because the failure printed one line it was easy
        # to lose in the output.
        try:
            for data, included in _paged(
                session, url, params, settings.drupal_request_timeout
            ):
                for node in data:
                    uuid = node.get("id")
                    attrs = node.get("attributes", {}) or {}
                    if not uuid:
                        continue
                    nodes[uuid] = {
                        "bundle": bundle,
                        "entity": entity,
                        "title": attrs.get("title") or attrs.get("info"),
                        "created": attrs.get("created"),
                        "changed": attrs.get("changed"),
                        "date_fields": _date_fields(attrs),
                    }
                    fetched.add(uuid)
                    # In-body PDFs, so an attachment can be tied to the page
                    # whose date it inherits. Anchor text comes with them.
                    for link in _inbody_pdfs(attrs):
                        absolute = _normalize_link(link["url"], site)
                        files.setdefault(absolute, {
                            "page_uuid": uuid, "anchor": link.get("anchor"),
                            "origin": "inbody",
                        })
                    # Attached file entities, from the included documents.
                    for item in included.values():
                        if item.get("type") != "file--file":
                            continue
                        uri = (item.get("attributes", {}) or {}).get("uri") or {}
                        rel = uri.get("url") if isinstance(uri, dict) else None
                        if not rel:
                            continue
                        files.setdefault(_normalize_link(rel, site, from_html=False), {
                            "page_uuid": uuid,
                            "created": (item.get("attributes") or {}).get("created"),
                            "origin": "attachment",
                        })
                print(f"    {entity}/{bundle:22} {len(fetched):6}", end="\r")
        except Exception as exc:
            print(f"\n    {entity}/{bundle}: FAILED ({type(exc).__name__}: {exc})")
            failures.append(f"{entity}/{bundle}: {type(exc).__name__}: {exc}")
            continue
        print(f"    {entity}/{bundle:22} {len(fetched):6} distinct")
        time.sleep(0.2)
    return {"nodes": nodes, "files": files, "failures": failures}


def compare(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Classify every catalogued document against what the site states.

    The comparison runs the *pipeline's own rule* over the site's current data
    and checks the answer against what is stored. Two things this gets right
    that re-deriving by hand did not:

    * ``created`` is a real timestamp and is normalised to **naive UTC**, using
      the same ``state._to_datetime`` that produced the stored value. Converting
      it to IST — correct only for date-*only* CMS fields, which are stored as
      IST midnight — shifted every record created after 18:30 UTC by a day and
      produced hundreds of phantom disagreements.
    * The decision comes from ``resolve_published_at``, not from
      ``publication_date`` plus a hand-written rule. A second copy flagged all
      228 research papers whose stated *year* the stored date already falls in —
      cases the design deliberately leaves alone.
    """
    from app.catalog.db import state_table
    from app.catalog.state import _to_datetime
    from app.core.clients import mysql_connection
    from app.ingestion.source_dates import resolve_published_at

    def as_stored(value: Any):
        """A site value as the calendar date the catalogue would hold for it."""
        parsed = _to_datetime(str(value)) if value else None
        return parsed.date() if parsed else None

    nodes = snapshot["nodes"]
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, source_type, bundle, title, url, source_key, "
            f"published_at, published_at_source, published_at_precision "
            f"FROM `{table}`"
        )
        local = list(cur.fetchall())
        cur.execute(
            f"SELECT document_id, node_uuid FROM `{table}_date_decision`"
        )
        parent_of = {r["document_id"]: r["node_uuid"] for r in cur.fetchall()}

    verdicts: dict[str, list] = defaultdict(list)
    for row in local:
        stored = row["published_at"].date()
        doc_id = row["document_id"]

        if row["source_type"] == "website":
            site_node = nodes.get(doc_id)
            if site_node is None:
                verdicts["not_on_site"].append((doc_id, row, None, None))
                continue
            resolved, source, _p = resolve_published_at(
                site_node["created"], site_node["date_fields"])
            expected, kind = as_stored(resolved), source
        else:
            # An attachment has no date field of its own in Drupal, so the site's
            # answer for it is its page's stamp — which is exactly the annual
            # report situation. An override is the one case the site cannot
            # explain: it came from the PDF's own text.
            if row["published_at_source"] == "document_text":
                verdicts["dated_from_the_document_itself"].append(
                    (doc_id, row, stored, "document_text"))
                continue
            page_uuid = parent_of.get(doc_id)
            site_node = nodes.get(page_uuid) if page_uuid else None
            if site_node is None:
                verdicts["page_not_on_site"].append((doc_id, row, None, None))
                continue
            expected, kind = as_stored(site_node["created"]), "page_created"

        if expected is None:
            verdicts["site_states_nothing_usable"].append((doc_id, row, None, kind))
        elif expected != stored:
            verdicts["disagrees"].append((doc_id, row, expected, kind))
        elif kind == "cms_field":
            verdicts["agrees"].append((doc_id, row, expected, kind))
        else:
            verdicts["page_dated"].append((doc_id, row, expected, kind))
    return verdicts


def report(verdicts: dict[str, list], snapshot: dict[str, Any]) -> None:
    total = sum(len(v) for v in verdicts.values())
    print(f"\nsite snapshot : {len(snapshot['nodes'])} nodes, "
          f"{len(snapshot['files'])} files")
    print(f"local documents compared: {total}\n")
    labels = {
        "agrees": "we store the date the site STATES for the document",
        "dated_from_the_document_itself": "dated from a statement quoted in the PDF",
        "page_dated": "we store the site's PAGE/record stamp (faithful to a source "
                      "that does not know the document's own date)",
        "disagrees": "we store something the site CONTRADICTS  <-- our bug",
        "site_states_nothing_usable": "the site offers no usable date",
        "not_on_site": "catalogued but not returned by the site",
        "page_not_on_site": "attachment whose page was not returned",
    }
    for key in ("agrees", "dated_from_the_document_itself", "page_dated",
                "disagrees", "site_states_nothing_usable", "not_on_site",
                "page_not_on_site"):
        rows = verdicts.get(key, [])
        if not rows and key not in ("agrees", "page_dated", "disagrees"):
            continue
        print(f"  {len(rows):6}  {labels[key]}")

    if verdicts.get("disagrees"):
        print("\n  DISAGREEMENTS (first 20):")
        for doc_id, row, site_value, kind in verdicts["disagrees"][:20]:
            print(f"    stored {str(row['published_at'])[:10]}  site {site_value}  "
                  f"[{kind}] {str(row['title'])[:40]}")

    print("\n  page-dated, by bundle — where the site itself does not know:")
    by_bundle = Counter(row["bundle"] for _d, row, _s, _k in verdicts.get("page_dated", []))
    for bundle, n in by_bundle.most_common(12):
        print(f"    {str(bundle):26} {n:6}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fetch", action="store_true",
                        help="Re-fetch the site snapshot (one JSON:API pass).")
    parser.add_argument("--snapshot", default=SNAPSHOT)
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    if args.fetch or not os.path.exists(args.snapshot):
        print("fetching the site (metadata only, no PDF bodies):")
        snapshot = fetch()
        # A partial fetch must not replace a complete one. The first version
        # wrote whatever it had: a run where every bundle raised stored 691 of
        # 8,600 nodes and reported 7,825 documents as "not on the site", which
        # looks exactly like a corpus problem rather than a scrape problem.
        if snapshot["failures"]:
            print(f"\n{len(snapshot['failures'])} bundle(s) failed; the snapshot "
                  f"would be incomplete and is NOT being written:")
            for failure in snapshot["failures"]:
                print(f"  - {failure}")
            return 2
        os.makedirs(os.path.dirname(args.snapshot) or ".", exist_ok=True)
        with open(args.snapshot, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle)
        print(f"\nwrote {args.snapshot}")
    else:
        with open(args.snapshot, encoding="utf-8") as handle:
            snapshot = json.load(handle)
        print(f"using {args.snapshot} (pass --fetch to refresh)")

    report(compare(snapshot), snapshot)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
