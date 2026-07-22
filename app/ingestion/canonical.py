from __future__ import annotations
from typing import Any, Protocol
from app.core.models import CanonicalDocument, CanonicalSection, EntityRef, FileLink
from app.ingestion.textutil import slugify as _slugify

# Substring hints that route Drupal metadata fields into canonical facets.
# field_audit reports against these same rules — import from here, don't copy.
CATEGORY_HINTS: tuple[str, ...] = ("category", "theme", "area", "division")
TAG_HINTS: tuple[str, ...] = ("tag", "keyword")
AUTHOR_HINTS: tuple[str, ...] = ("author",)

# Taxonomy vocabularies whose terms are categories regardless of the name of
# the referencing field — vocabulary routing beats field-name guessing.
CATEGORY_VOCABULARIES: tuple[str, ...] = ("themes",)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = [str(v).strip() for v in value]
    else:
        items = [part.strip() for part in str(value).split(",")]
    return [item for item in items if item]


def _matching(meta: dict[str, Any], *substrings: str) -> list[tuple[str, Any]]:
    return [
        (key, value)
        for key, value in meta.items()
        if value not in (None, "", []) and any(s in key.lower() for s in substrings)
    ]


def _pick_list(meta: dict[str, Any], *substrings: str) -> list[str]:
    matches = _matching(meta, *substrings)
    for _, value in matches:
        if isinstance(value, (list, tuple)):
            return _as_list(value)
    return _as_list(matches[0][1]) if matches else []


def _union_list(meta: dict[str, Any], *substrings: str) -> list[str]:
    seen: dict[str, None] = {}
    for _, value in _matching(meta, *substrings):
        for item in _as_list(value):
            seen.setdefault(item, None)
    return list(seen)


class _PdfPage(Protocol):
    page_number: int
    text: str


class _PdfResult(Protocol):
    source: str
    pages: list[_PdfPage]


def from_pdf(
    result: _PdfResult,
    *,
    document_id: str | None = None,
    source_type: str = "pdf",
    **overrides: Any,
) -> CanonicalDocument:
    doc_id = document_id or _slugify(getattr(result, "source", "") or "")
    sections = [
        CanonicalSection(
            text=page.text,
            page_start=page.page_number,
            page_end=page.page_number,
            order=i,
        )
        for i, page in enumerate(result.pages)
        if getattr(page, "text", "")
    ]
    doc = CanonicalDocument(
        document_id=overrides.pop("document_id_override", doc_id),
        source_type=source_type,
        title=overrides.pop("title", getattr(result, "source", None)),
        sections=sections,
        pdf_id=overrides.pop("pdf_id", doc_id),
        pdf_path=overrides.pop("pdf_path", getattr(result, "source", None)),
        **overrides,
    )
    doc.ensure_content_hash()
    return doc


def drupal_facets(
    metadata: dict[str, Any], refs: list[EntityRef]
) -> dict[str, list[str]]:
    """Facet lists (categories/tags/authors) for a Drupal record. Shared by the
    node document and its attachment documents — an attached PDF inherits its
    node's facets so theme-scoped retrieval reaches the PDF content too."""
    categories = _union_list(metadata, *CATEGORY_HINTS)
    # Any reference into a category vocabulary is a category, whatever the
    # referencing field is called — catches fields the name hints miss.
    for ref in refs:
        if ref.vocabulary in CATEGORY_VOCABULARIES and ref.label:
            if ref.label not in categories:
                categories.append(ref.label)
    # A sub-theme's parent thematic area is itself a category, so the term is
    # retrievable under its parent (e.g. "Air" surfaces under "Environment").
    for parent in _as_list(metadata.get("parent")):
        if parent not in categories:
            categories.append(parent)
    return {
        "categories": categories,
        "tags": _union_list(metadata, *TAG_HINTS),
        "authors": _pick_list(metadata, *AUTHOR_HINTS),
    }


def _drupal_document(
    *,
    body: str,
    title: str | None,
    url: str | None,
    uuid: str | None,
    bundle: str | None,
    nid: int | None,
    created: str | None,
    changed: str | None,
    metadata: dict[str, Any],
    refs: list[EntityRef] | None = None,
    **overrides: Any,
) -> CanonicalDocument:
    refs = refs or []
    facets = drupal_facets(metadata, refs)

    doc = CanonicalDocument(
        document_id=uuid or _slugify(url or f"{bundle}/{title}"),
        source_type=overrides.pop("source_type", "website"),
        title=(title or "").strip() or None,
        sections=[CanonicalSection(text=body, order=0)] if body else [],
        source_url=url,
        article_uuid=uuid or None,
        tags=facets["tags"],
        categories=facets["categories"],
        authors=facets["authors"],
        published_at=created,
        extra={"bundle": bundle, "nid": nid, "changed": changed},
        entity_refs=refs,
        raw_meta=dict(metadata),
        **overrides,
    )
    doc.ensure_content_hash()
    return doc


def from_drupal_record(record: Any, **overrides: Any) -> CanonicalDocument:
    overrides.setdefault("file_url", getattr(record, "pdf_url", None))
    return _drupal_document(
        body=record.body,
        title=record.title,
        url=record.url,
        uuid=record.uuid or None,
        bundle=record.bundle,
        nid=record.nid,
        created=record.created,
        changed=record.changed,
        metadata=record.metadata or {},
        refs=list(getattr(record, "refs", None) or []),
        file_links=[
            FileLink(uuid=f.uuid, origin=f.origin, url=f.url, filename=f.filename)
            for f in getattr(record, "files", None) or []
            if f.uuid
        ],
        **overrides,
    )


def from_drupal_export(item: dict[str, Any], **overrides: Any) -> CanonicalDocument:
    meta = {k: v for k, v in item.items() if k != "text"}
    return _drupal_document(
        body=item.get("text", "") or "",
        title=meta.get("title"),
        url=meta.get("url"),
        uuid=meta.get("uuid") or None,
        bundle=meta.get("bundle"),
        nid=meta.get("nid"),
        created=meta.get("created"),
        changed=meta.get("changed"),
        metadata=meta,
        **overrides,
    )
