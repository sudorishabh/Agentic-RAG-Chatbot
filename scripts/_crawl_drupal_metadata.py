"""Metadata-only crawl of the Drupal JSON:API, for the Phase 0 date analysis.

Fetches nodes with the same ``include=`` the ingestion extractor uses, and keeps
the date-bearing fields plus each attached ``file--file`` entity and each in-body
PDF link (with its anchor text). **No PDF body is ever downloaded** and no
extraction runs, so this cannot reach Document Intelligence.

Used by :mod:`scripts.shadow_corpus_report` under ``--refresh``.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

from app.config import get_settings
from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES, HEADERS

logger = logging.getLogger(__name__)

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}|$)")
HREF_PDF_RE = re.compile(
    r'<a[^>]+href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\'][^>]*>(.*?)</a>', re.I | re.S
)
BARE_PDF_RE = re.compile(r'(https?://[^\s"\'<>()]+\.pdf)', re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _get(session: requests.Session, url: str, params: dict | None, timeout: float, tries: int = 4):
    for attempt in range(tries):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            if response.status_code in (403, 404):
                return None
            logger.warning("HTTP %d on %s", response.status_code, url)
        except requests.RequestException:
            logger.warning("Request failed on %s", url, exc_info=True)
        time.sleep(2 * (attempt + 1))
    return None


def _date_like(attrs: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in attrs.items():
        candidate = None
        if isinstance(value, str):
            candidate = value
        elif isinstance(value, dict) and isinstance(value.get("value"), str):
            candidate = value["value"]
        elif isinstance(value, list) and value and isinstance(value[0], str):
            candidate = value[0]
        if candidate and ISO_RE.match(candidate):
            out[key] = candidate
    return out


def _inbody_pdfs(attrs: dict) -> list[dict[str, str]]:
    """Every PDF link in this node's rich text, with the best anchor text kept.

    The anchor is what a reader sees ("Annual Report 2021-2022") and is often
    the only place an edition is named; the ingestion extractor throws it away.

    One PDF is frequently linked more than once on a page — a thumbnail image
    wrapped in an `<a>` (empty text) beside a captioned text link. Keying by URL
    and keeping the *longest* non-empty anchor stops the image link from
    blanking the caption, which is what silently emptied every annual-report
    anchor in the first Phase 0B pass.
    """
    best: dict[str, str] = {}
    order: list[str] = []
    blobs: list[str] = []
    for value in attrs.values():
        if isinstance(value, str) and "<" in value:
            blobs.append(value)
        elif isinstance(value, dict):
            for key in ("value", "processed"):
                if isinstance(value.get(key), str):
                    blobs.append(value[key])

    def offer(url: str, anchor: str) -> None:
        if url not in best:
            best[url] = anchor
            order.append(url)
        elif len(anchor) > len(best[url]):
            best[url] = anchor

    for blob in blobs:
        for match in HREF_PDF_RE.finditer(blob):
            offer(match.group(1),
                  " ".join(TAG_RE.sub(" ", match.group(2)).split()))
        for match in BARE_PDF_RE.finditer(TAG_RE.sub(" ", blob)):
            offer(match.group(1), "")
    return [{"url": url, "anchor": best[url]} for url in order]


def crawl(bundles: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    timeout = settings.drupal_request_timeout
    records: list[dict[str, Any]] = []

    with requests.Session() as session:
        session.headers.update(HEADERS)
        for bundle in (bundles or DEFAULT_BUNDLES):
            probe = _get(session, f"{base}/node/{bundle}",
                         {"page[limit]": 1, "filter[status]": 1}, timeout)
            if not probe or not probe.get("data"):
                logger.info("node/%s unavailable; skipping.", bundle)
                continue
            fields = [n for n in probe["data"][0].get("relationships", {})
                      if n.startswith("field_")]
            params: dict[str, Any] = {
                "page[limit]": settings.drupal_page_size,
                "filter[status]": 1,
                "sort": "created",
            }
            if fields:
                params["include"] = ",".join(fields)
            url, first, count = f"{base}/node/{bundle}", True, 0
            while url:
                doc = _get(session, url, params if first else None, timeout)
                first = False
                if not doc:
                    break
                included = {(i.get("type"), i.get("id")): i for i in doc.get("included") or []}
                for node in doc.get("data") or []:
                    attrs = node.get("attributes", {})
                    files = []
                    for field_name, rel in (node.get("relationships") or {}).items():
                        if not field_name.startswith("field_"):
                            continue
                        data = rel.get("data")
                        if not data:
                            continue
                        for ref in (data if isinstance(data, list) else [data]):
                            if ref.get("type") != "file--file":
                                continue
                            entity = included.get(("file--file", ref.get("id")))
                            if not entity:
                                files.append({"field": field_name, "uuid": ref.get("id"),
                                              "unresolved": True})
                                continue
                            fa = entity.get("attributes", {})
                            files.append({
                                "field": field_name,
                                "uuid": entity.get("id"),
                                "fid": fa.get("drupal_internal__fid"),
                                "filename": fa.get("filename"),
                                "mime": fa.get("filemime"),
                                "size": fa.get("filesize"),
                                "created": fa.get("created"),
                                "changed": fa.get("changed"),
                                "uri": (fa.get("uri") or {}).get("value"),
                                "url": (fa.get("uri") or {}).get("url"),
                                "desc": (ref.get("meta") or {}).get("description"),
                            })
                    records.append({
                        "bundle": bundle,
                        "uuid": node.get("id"),
                        "nid": attrs.get("drupal_internal__nid"),
                        "title": attrs.get("title") or "",
                        "created": attrs.get("created"),
                        "changed": attrs.get("changed"),
                        "dates": _date_like(attrs),
                        "files": files,
                        "inbody": _inbody_pdfs(attrs),
                    })
                    count += 1
                nxt = (doc.get("links") or {}).get("next")
                url = nxt["href"] if nxt else None
            logger.info("node/%s: %d records", bundle, count)
    return records
