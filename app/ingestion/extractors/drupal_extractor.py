from __future__ import annotations
import hashlib
import logging
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Iterable, Iterator
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import get_settings
from app.core.models import EntityRef

logger = logging.getLogger(__name__)

HEADERS = {"Accept": "application/vnd.api+json"}

# Content-bearing resources that are NOT node bundles. Their descriptive text
# (taxonomy term descriptions, custom-block bodies) is prime corpus content that
# the node crawl never reaches. Fetched under /jsonapi/{entity_type}/{bundle}.

DEFAULT_TAXONOMIES: tuple[str, ...] = (
    # "themes",
    # "extra_pages",
    # "regional_centre",

    # Facet vocabularies referenced by node bundles (field_audit, 2026-07).
    # Crawling them keeps the term catalog able to resolve every
    # document_term link to a name; most terms carry no body text, so they
    # land in the catalog without producing vector points.
    
    # "tags",
    # "partners",
    # "programs_units",
    # "related_terms",
    # "stakeholders",
    # "division",
    # "division_areas",
    # "region",
    # "language",
)

DEFAULT_BUNDLES: tuple[str, ...] = (
    "article",
    "page",
    "research_papers",
    "completed_projects",
    "feature_articles",
    "ongoing_projects",
    "news",
    "events",
    "press_release",
    "policy_brief",
    "videos",
    "infographics",
    "services",
    "report",
    "people",
    "carousel",
    )


DEFAULT_BLOCKS: tuple[str, ...] = ("basic",)


LONG_TEXT_THRESHOLD = 255

# MIME types / extensions of document attachments we do not extract today but
# want visibility into (R5). Images/media are intentionally excluded elsewhere.
_DOC_EXTS = (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv")

# In-body links (href="…pdf") and bare https://…pdf URLs embedded in rich text.
_HREF_PDF_RE = re.compile(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', re.I)
_BARE_PDF_RE = re.compile(r'(https?://[^\s"\'<>()]+\.pdf)', re.I)

@dataclass
class DrupalFile:
    """A file attached to a node — typically the source PDF behind an article."""

    url: str
    filename: str
    description: str | None = None
    uuid: str = ""
    # "attachment" = referenced file--file entity; "inbody" = harvested from a
    # rich-text field (see R7 in docs/drupal-coverage-analysis.md).
    origin: str = "attachment"


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
    files: list[DrupalFile] = field(default_factory=list)
    refs: list[EntityRef] = field(default_factory=list)

    @property
    def source(self) -> str:
        return self.url or f"{self.bundle}/{self.uuid}"

    @property
    def pdf_url(self) -> str | None:
        """The primary attached PDF's absolute URL, if any."""
        return self.files[0].url if self.files else None

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
    entity_type: str = "node",
    published_only: bool = True,
    changed_since: int | None = None,
    ascending: bool = False,
) -> Iterator[DrupalRecord]:
    """Yield records for one resource bundle. ``entity_type`` is the JSON:API
    entity ("node", "taxonomy_term", "block_content"); the resource is fetched
    from /jsonapi/{entity_type}/{bundle}. ``ascending`` crawls oldest-first —
    used by capped batch runs so the changed high-water mark advances only
    past documents that were actually processed (a resume cursor)."""
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    site = _site_base(base)

    fields = _discover_relationship_fields(
        session, base, bundle, published_only, entity_type=entity_type
    )
    # Taxonomy terms carry their tree via the `parent` relationship (not a
    # field_*), so it is excluded above. Include it explicitly so the parent
    # term is embedded and its name is resolvable — this is what preserves the
    # thematic-area hierarchy (e.g. "Air" under "Environment").
    if entity_type == "taxonomy_term" and "parent" not in fields:
        fields.append("parent")
    params: dict[str, Any] = {
        "page[limit]": settings.drupal_page_size,
        "sort": "changed" if ascending else "-changed",
    }
    if fields:
        params["include"] = ",".join(fields)
    if published_only:
        params["filter[status]"] = 1
    if changed_since is not None:
        # ">=" (not ">") so a record edited in the same second as the stored
        # high-water mark is not skipped. The boundary-second records re-fetched
        # each run are cheap and resolve to UNCHANGED via their fingerprint.
        params["filter[changed][condition][path]"] = "changed"
        params["filter[changed][condition][operator]"] = ">="
        params["filter[changed][condition][value]"] = int(changed_since)

    url = f"{base}/{entity_type}/{bundle}"
    for data, included in _iter_pages(session, url, params, settings.drupal_request_timeout):
        for node in data:
            yield _build_record(node, included, bundle, site, entity_type=entity_type)

def iter_node_uuids(
    session: requests.Session,
    bundle: str,
    *,
    entity_type: str = "node",
    published_only: bool = True,
) -> Iterator[str]:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    params: dict[str, Any] = {
        "page[limit]": settings.drupal_page_size,
        f"fields[{entity_type}--{bundle}]": "drupal_internal__nid",
    }
    
    if published_only:
        params["filter[status]"] = 1

    url = f"{base}/{entity_type}/{bundle}"
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
    *,
    entity_type: str = "node",
) -> list[str]:
    params: dict[str, Any] = {"page[limit]": 1}
    if published_only:
        params["filter[status]"] = 1
    try:
        response = session.get(
            f"{base}/{entity_type}/{bundle}",
            params=params,
            timeout=get_settings().drupal_request_timeout,
        )
        response.raise_for_status()
        data = response.json().get("data") or []
    except requests.RequestException:
        logger.warning("Could not sample %s/%s for include fields", entity_type, bundle)
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
    *,
    entity_type: str = "node",
) -> DrupalRecord:
    attributes = node.get("attributes", {})
    body_parts, scalar_meta = _partition_attributes(attributes)

    metadata, refs = _resolve_relationships(node, included)
    metadata.update(scalar_meta)
    if entity_type != "node":
        metadata.setdefault("entity_type", entity_type)

    files = _resolve_files(node, included, site)
    files.extend(_extract_inbody_pdfs(attributes, site, {f.url for f in files}))

    # Taxonomy terms label their title "name"; custom blocks use "info".
    title = (
        attributes.get("title")
        or attributes.get("name")
        or attributes.get("info")
        or ""
    ).strip()

    return DrupalRecord(
        uuid=node.get("id", ""),
        bundle=bundle,
        nid=attributes.get("drupal_internal__nid"),
        title=title,
        url=_node_url(attributes, site),
        body="\n\n".join(body_parts),
        created=attributes.get("created"),
        changed=attributes.get("changed"),
        metadata=metadata,
        files=files,
        refs=refs,
    )


_PDF_MIME = "application/pdf"


def _resolve_files(
    node: dict, included: dict[tuple[str, str], dict], site: str
) -> list[DrupalFile]:
    """Collect this node's attached PDF files. Scans every field_* relationship
    for referenced file--file entities (the file field name varies per bundle:
    field_policybrieffile, field_report, field_*_full_text, ...) and keeps the
    PDFs, resolving their relative uri.url to an absolute URL."""
    out: list[DrupalFile] = []
    seen: set[str] = set()
    for field_name, relationship in node.get("relationships", {}).items():
        if not field_name.startswith("field_"):
            continue
        data = relationship.get("data")
        if not data:
            continue
        refs = data if isinstance(data, list) else [data]
        for ref in refs:
            if ref.get("type") != "file--file":
                continue
            entity = included.get((ref.get("type"), ref.get("id")))
            if not entity:
                continue
            attrs = entity.get("attributes", {})
            filename = (attrs.get("filename") or "").strip()
            mime = (attrs.get("filemime") or "").lower()
            if mime != _PDF_MIME and not filename.lower().endswith(".pdf"):
                # R5: surface document attachments we skip (docx/xlsx/pptx/…) so
                # a genuinely missed source is visible rather than silent.
                if filename.lower().endswith(_DOC_EXTS):
                    logger.warning(
                        "Skipping non-PDF document attachment %r (mime=%s) on %s",
                        filename, mime, node.get("id"),
                    )
                continue
            uri = attrs.get("uri")
            rel_url = uri.get("url") if isinstance(uri, dict) else None
            if not rel_url:
                continue
            abs_url = rel_url if rel_url.startswith("http") else f"{site}{rel_url}"
            if abs_url in seen:
                continue
            seen.add(abs_url)
            meta = ref.get("meta") if isinstance(ref.get("meta"), dict) else {}
            out.append(
                DrupalFile(
                    url=abs_url,
                    filename=filename,
                    description=(meta.get("description") or None),
                    uuid=ref.get("id") or "",
                )
            )
    return out


def _iter_rich_text(attributes: dict) -> Iterator[str]:
    """Yield every HTML/long-text value on a record: formatted-text fields
    (dicts with processed/value) plus long plain strings. This is where in-body
    PDF links live — confirmed in ``body`` and in several ``field_*`` text
    fields (field_completed_featured_text, field_ongoing_featured_text, …)."""
    for value in attributes.values():
        if isinstance(value, dict) and ("processed" in value or "value" in value):
            html = value.get("processed") or value.get("value") or ""
            if html:
                yield html
        elif isinstance(value, str) and len(value) > LONG_TEXT_THRESHOLD:
            yield value


def _extract_inbody_pdfs(
    attributes: dict, site: str, seen_urls: set[str]
) -> list[DrupalFile]:
    """Harvest PDF links embedded in rich-text fields (R7). Internal
    (teriin.org / relative) PDFs are always returned so the attachment pipeline
    ingests them; external PDFs are only returned when
    ``drupal_ingest_external_pdfs`` is set (their URL otherwise survives in the
    body text via the link-preserving text extractor). Returns DrupalFiles with
    a URL-stable synthetic uuid so the same PDF ingests once."""
    ingest_external = get_settings().drupal_ingest_external_pdfs
    # removeprefix, NOT lstrip: lstrip("www.") strips *characters* {w, .} from
    # the left, mangling hosts like "web.teriin.org" -> "eb.teriin.org".
    site_host = urlparse(site).netloc.lower().removeprefix("www.")

    out: list[DrupalFile] = []
    local_seen = set(seen_urls)
    for html in _iter_rich_text(attributes):
        candidates = set(_HREF_PDF_RE.findall(html)) | set(_BARE_PDF_RE.findall(html))
        for raw in candidates:
            if not raw.split("?")[0].lower().endswith(".pdf"):
                continue
            abs_url = raw if raw.lower().startswith("http") else f"{site}{raw if raw.startswith('/') else '/' + raw}"
            host = urlparse(abs_url).netloc.lower().removeprefix("www.")
            is_internal = (not host) or host == site_host or "teriin.org" in host or "teri.res.in" in host
            if not is_internal and not ingest_external:
                continue
            if abs_url in local_seen:
                continue
            local_seen.add(abs_url)
            filename = abs_url.split("?")[0].rsplit("/", 1)[-1] or "document.pdf"
            out.append(
                DrupalFile(
                    url=abs_url,
                    filename=filename,
                    uuid=f"inbody:{hashlib.sha1(abs_url.encode('utf-8')).hexdigest()}",
                    origin="inbody",
                )
            )
    return out


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
) -> tuple[dict[str, list[str]], list[EntityRef]]:
    """Resolve entity relationships to label metadata plus full entity refs.

    The labels keep the existing metadata shape (field -> resolved names); the
    refs additionally carry each entity's UUID and JSON:API type, so catalog
    joins stay correct when a term is later renamed. Refs are kept even when
    the entity is not embedded in ``included`` (label stays None)."""
    meta: dict[str, list[str]] = {}
    refs: list[EntityRef] = []
    for field_name, relationship in node.get("relationships", {}).items():
        # field_* are content relationships; `parent` is the taxonomy tree link.
        if not (field_name.startswith("field_") or field_name == "parent"):
            continue
        data = relationship.get("data")
        if not data:
            continue
        items = data if isinstance(data, list) else [data]

        labels: list[str] = []
        for item in items:
            uuid, ref_type = item.get("id"), item.get("type")
            # "virtual" is the placeholder parent of root taxonomy terms; "missing"
            # is JSON:API's resource identifier for a relationship target that no
            # longer exists (deleted/unpublished) -- never resolvable, so keeping
            # it as a ref would put an unresolvable id in the Qdrant payload.
            # file--file attachments are handled by _resolve_files.
            if (
                not uuid
                or not ref_type
                or uuid in ("virtual", "missing")
                or ref_type == "file--file"
            ):
                continue
            entity = included.get((ref_type, uuid))
            attrs = entity.get("attributes", {}) if entity else {}
            label = attrs.get("name") or attrs.get("display_name") or attrs.get("title")
            refs.append(
                EntityRef(
                    field_name=field_name, uuid=uuid, entity_type=ref_type, label=label
                )
            )
            if label:
                labels.append(label)
        if labels:
            meta[field_name] = labels
    return meta, refs


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
    _CELL = {"td", "th"}
    _SKIP = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0
        self._pending_href: str | None = None

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        adict = {k: v for k, v in attrs}
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._CELL:
            # Keep table structure legible: separate cells rather than merging.
            self._parts.append(" | ")
        elif tag in self._BLOCK:
            self._parts.append("\n")

        # R4: preserve information that would otherwise be dropped on flatten.
        if self._skip_depth:
            return
        if tag == "a":
            href = (adict.get("href") or "").strip()
            # Skip in-page anchors / javascript; keep real destinations.
            self._pending_href = href if href and not href.startswith(("#", "javascript:")) else None
        elif tag == "img":
            alt = (adict.get("alt") or "").strip()
            if alt:
                self._parts.append(f" [image: {alt}] ")
        elif tag == "iframe":
            src = (adict.get("src") or "").strip()
            if src:
                self._parts.append(f" [embedded: {src}] ")

    def handle_startendtag(self, tag: str, attrs: Any) -> None:
        # Void elements like <img .../> arrive here, not via handle_starttag.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self._BLOCK:
            self._parts.append("\n")
        if tag == "a" and self._pending_href and not self._skip_depth:
            self._parts.append(f" ({self._pending_href})")
            self._pending_href = None

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

    parser = argparse.ArgumentParser(
        description=(__doc__ or "Inspect Drupal JSON:API node records.").splitlines()[0]
    )
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
