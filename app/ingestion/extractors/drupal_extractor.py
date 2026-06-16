from __future__ import annotations
import logging
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Iterable, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import get_settings

logger = logging.getLogger(__name__)

HEADERS = {"Accept": "application/vnd.api+json"}

DEFAULT_BUNDLES: tuple[str, ...] = (
    "news",
    "feature_articles",
    "completed_projects",
    "events",
    "press_release",
    "research_papers",
    "ongoing_projects",
    "article",
    "policy_brief",
    "videos",
    "infographics",
    "services",
    "report",
    "people",
    "page",
)

LONG_TEXT_THRESHOLD = 255


@dataclass
class DrupalRecord:

    uuid: str
    bundle: str
    nid: int | None
    title: str
    url: str | None
    body: str
    created: str | None
    changed: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.url or f"{self.bundle}/{self.uuid}"

    def to_text(self) -> str:
        return "\n\n".join(part for part in (self.title, self.body) if part).strip()

    def to_metadata(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "source": self.source,
            "bundle": self.bundle,
            "title": self.title,
            "url": self.url,
            "nid": self.nid,
            "uuid": self.uuid,
            "created": self.created,
            "changed": self.changed,
        }
        base.update(self.metadata)
        return {k: v for k, v in base.items() if v not in (None, "", [])}

def iter_records(
    bundles: Iterable[str] | None = None,
    *,
    published_only: bool = True,
    changed_since: int | None = None,
    session: requests.Session | None = None,
) -> Iterator[DrupalRecord]:

    settings = get_settings()
    bundles = tuple(bundles) if bundles is not None else DEFAULT_BUNDLES

    owns_session = session is None
    session = session or _build_session(settings.drupal_max_retries)
    try:
        for bundle in bundles:
            count = 0
            try:
                for record in iter_bundle_records(
                    session,
                    bundle,
                    published_only=published_only,
                    changed_since=changed_since,
                ):
                    count += 1
                    yield record
            except requests.RequestException:
                logger.exception("Failed extracting node/%s; skipping bundle", bundle)
                continue
            logger.info("Extracted %d records from node/%s", count, bundle)
    finally:
        if owns_session:
            session.close()


def iter_bundle_records(
    session: requests.Session,
    bundle: str,
    *,
    published_only: bool = True,
    changed_since: int | None = None,
) -> Iterator[DrupalRecord]:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    site = _site_base(base)

    fields = _discover_relationship_fields(session, base, bundle, published_only)
    params: dict[str, Any] = {
        "page[limit]": settings.drupal_page_size,
        "sort": "-changed",
    }
    if fields:
        params["include"] = ",".join(fields)
    if published_only:
        params["filter[status]"] = 1
    if changed_since is not None:
        params["filter[changed][condition][path]"] = "changed"
        params["filter[changed][condition][operator]"] = ">"
        params["filter[changed][condition][value]"] = int(changed_since)

    url = f"{base}/node/{bundle}"
    for data, included in _iter_pages(session, url, params, settings.drupal_request_timeout):
        for node in data:
            yield _build_record(node, included, bundle, site)

def iter_node_uuids(
    session: requests.Session,
    bundle: str,
    *,
    published_only: bool = True,
) -> Iterator[str]:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    params: dict[str, Any] = {
        "page[limit]": settings.drupal_page_size,
        f"fields[node--{bundle}]": "drupal_internal__nid",
    }
    if published_only:
        params["filter[status]"] = 1

    url = f"{base}/node/{bundle}"
    for data, _included in _iter_pages(session, url, params, settings.drupal_request_timeout):
        for node in data:
            uuid = node.get("id")
            if uuid:
                yield uuid


def _build_session(max_retries: int) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session

def _iter_pages(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    timeout: int,
) -> Iterator[tuple[list[dict], dict[tuple[str, str], dict]]]:
    next_url: str | None = url
    next_params: dict[str, Any] | None = params
    while next_url:
        response = session.get(next_url, params=next_params, timeout=timeout)
        response.raise_for_status()
        doc = response.json()

        included = {
            (item["type"], item["id"]): item for item in doc.get("included", [])
        }
        data = doc.get("data") or []
        if isinstance(data, dict):
            data = [data]

        yield data, included
        next_url = doc.get("links", {}).get("next", {}).get("href")
        next_params = None


def _discover_relationship_fields(
    session: requests.Session,
    base: str,
    bundle: str,
    published_only: bool,
) -> list[str]:
    params: dict[str, Any] = {"page[limit]": 1}
    if published_only:
        params["filter[status]"] = 1
    try:
        response = session.get(
            f"{base}/node/{bundle}",
            params=params,
            timeout=get_settings().drupal_request_timeout,
        )
        response.raise_for_status()
        data = response.json().get("data") or []
    except requests.RequestException:
        logger.warning("Could not sample node/%s for include fields", bundle)
        return []

    if not data:
        return []
    relationships = data[0].get("relationships", {})
    return [name for name in relationships if name.startswith("field_")]

def _build_record(
    node: dict,
    included: dict[tuple[str, str], dict],
    bundle: str,
    site: str,
) -> DrupalRecord:
    attributes = node.get("attributes", {})
    body_parts, scalar_meta = _partition_attributes(attributes)

    metadata = _resolve_relationships(node, included)
    metadata.update(scalar_meta)

    return DrupalRecord(
        uuid=node.get("id", ""),
        bundle=bundle,
        nid=attributes.get("drupal_internal__nid"),
        title=(attributes.get("title") or "").strip(),
        url=_node_url(attributes, site),
        body="\n\n".join(body_parts),
        created=attributes.get("created"),
        changed=attributes.get("changed"),
        metadata=metadata,
    )


def _partition_attributes(attributes: dict) -> tuple[list[str], dict[str, Any]]:
    body: list[tuple[str, str]] = []
    meta: dict[str, Any] = {}

    for key, value in attributes.items():
        if isinstance(value, dict) and ("processed" in value or "value" in value):
            text = _html_to_text(value.get("processed") or value.get("value") or "")
            if text:
                body.append((key, text))
            continue

        if not key.startswith("field_"):
            continue

        if isinstance(value, bool):
            meta[key] = value
        elif isinstance(value, (int, float)):
            meta[key] = value
        elif isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            if len(stripped) > LONG_TEXT_THRESHOLD:
                body.append((key, _html_to_text(stripped)))
            else:
                meta[key] = stripped
        elif isinstance(value, list) and value and all(
            isinstance(item, (str, int, float, bool)) for item in value
        ):
            meta[key] = value

    body.sort(key=lambda item: 0 if item[0] == "body" else 1)
    return [text for _, text in body], meta


def _resolve_relationships(
    node: dict, included: dict[tuple[str, str], dict]
) -> dict[str, list[str]]:
    meta: dict[str, list[str]] = {}
    for field_name, relationship in node.get("relationships", {}).items():
        if not field_name.startswith("field_"):
            continue
        data = relationship.get("data")
        if not data:
            continue
        refs = data if isinstance(data, list) else [data]

        labels: list[str] = []
        for ref in refs:
            entity = included.get((ref.get("type"), ref.get("id")))
            if not entity:
                continue
            attrs = entity.get("attributes", {})
            label = attrs.get("name") or attrs.get("display_name") or attrs.get("title")
            if label:
                labels.append(label)
        if labels:
            meta[field_name] = labels
    return meta


def _node_url(attributes: dict, site: str) -> str | None:
    path = attributes.get("path")
    alias = path.get("alias") if isinstance(path, dict) else None
    return f"{site}{alias}" if alias else None


def _site_base(jsonapi_base: str) -> str:
    return jsonapi_base.split("/jsonapi")[0] or jsonapi_base

class _TextExtractor(HTMLParser):

    _BLOCK = {
        "p", "br", "div", "li", "ul", "ol", "tr", "table", "section", "article",
        "header", "footer", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6",
    }
    _SKIP = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._BLOCK:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self._BLOCK:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)

    def get_text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self._parts).split("\n")]
        out: list[str] = []
        for line in lines:
            if line:
                out.append(line)
            elif out and out[-1]:
                out.append("")
        return "\n".join(out).strip()


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return parser.get_text()


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "bundle",
        nargs="?",
        default="research_papers",
        help="Node bundle to fetch, e.g. news, events (default: feature_articles).",
    )
    parser.add_argument(
        "-n", "--limit", type=int, default=5,
        help="Max records to show; 0 for no limit (default: 5).",
    )
    parser.add_argument(
        "--count", action="store_true",
        help="Only count all records in the bundle (ignores --limit).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit full records as JSON (to_text + to_metadata) instead of a summary.",
    )
    parser.add_argument(
        "--include-unpublished", action="store_true",
        help="Include unpublished records (status=0) as well.",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List the default bundles and exit.",
    )
    args = parser.parse_args(argv)

    if args.list:
        print("\n".join(DEFAULT_BUNDLES))
        return 0

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    session = _build_session(get_settings().drupal_max_retries)
    published_only = not args.include_unpublished
    try:
        records = iter_bundle_records(session, args.bundle, published_only=published_only)

        if args.count:
            print(f"node/{args.bundle}: {sum(1 for _ in records)} records")
            return 0

        collected: list[dict] = []
        for i, record in enumerate(records):
            if args.limit and i >= args.limit:
                break
            if args.json:
                collected.append({"text": record.to_text(), **record.to_metadata()})
            else:
                print(f"[{i}] {record.title}")
                print(f"     url:      {record.url}")
                print(f"     body:     {record.body[:220]!r}")
                print(f"     metadata: {record.metadata}\n")

        if args.json:
            print(json.dumps(collected, indent=2, ensure_ascii=False))
        return 0
    except requests.RequestException as exc:
        print(f"Failed fetching node/{args.bundle}: {exc}", file=sys.stderr)
        print("Run with --list to see available bundles.", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(_main())
