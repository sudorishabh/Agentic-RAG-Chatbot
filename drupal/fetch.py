"""Fetch Drupal content (with all related data) from teriin.org via JSON:API.

Single entry point: ``fetch_nodes(content_type, status=1)``.

Give it a content type and it returns a list of every node of that type, where
each node already carries its related data resolved inline — themes, tags,
authors, regions, stakeholders, attached files, etc. Pagination is handled
internally, so you always get the full set, not just the first 50.

Why related data needs resolving:
    Drupal's JSON:API returns a node's own fields (title, body, dates) directly,
    but relationships (themes/tags/author/files) come back only as
    ``{type, id}`` references. We pass ``include=...`` so the server ships the
    full related records in a top-level ``included`` array, then we stitch them
    back onto each node here. See README.md for the full picture.

Quick run:
    venv/Scripts/python.exe -m drupal.fetch feature_articles
"""

from __future__ import annotations

from typing import Any

import requests

BASE_URL = "https://teriin.org/jsonapi"
HEADERS = {"Accept": "application/vnd.api+json"}
# Drupal JSON:API hard-caps page size at 50 regardless of what you ask for.
PAGE_LIMIT = 50
REQUEST_TIMEOUT = 60

# Relationship keys that are framework plumbing, not content metadata.
_SKIP_RELATIONSHIPS = {"node_type", "revision_uid"}


def _discover_include_fields(content_type: str) -> list[str]:
    """Sample one node of this type to learn which ``field_*`` relationships
    it has, so we know exactly what to ``include``.

    Doing this per type means we never hard-code field names (which differ
    between content types, e.g. ``field_farticle_theme`` vs
    ``field_rpaper_themes``) and never miss a metadata field.
    """
    url = f"{BASE_URL}/node/{content_type}?page[limit]=1"
    doc = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT).json()
    data = doc.get("data") or []
    if not data:
        return []
    relationships = data[0].get("relationships", {})
    return [
        key
        for key in relationships
        if key.startswith("field_") and key not in _SKIP_RELATIONSHIPS
    ]


def _build_first_url(content_type: str, status: int | None) -> str:
    """Build the first page URL with includes, status filter and page size."""
    params = [f"page[limit]={PAGE_LIMIT}"]
    include_fields = _discover_include_fields(content_type)
    if include_fields:
        params.append("include=" + ",".join(include_fields))
    if status is not None:
        params.append(f"filter[status][value]={status}")
    return f"{BASE_URL}/node/{content_type}?" + "&".join(params)


def _index_included(included: list[dict], store: dict[tuple[str, str], dict]) -> None:
    """Add this page's ``included`` entities to a (type, id) -> entity lookup."""
    for item in included:
        store[(item["type"], item["id"])] = item


def _resolve_node(node: dict, included: dict[tuple[str, str], dict]) -> dict[str, Any]:
    """Flatten one node into ``{id, type, ...attributes, related: {...}}`` with
    every relationship reference replaced by the full related entity."""
    related: dict[str, list[dict]] = {}
    for field, relationship in node.get("relationships", {}).items():
        if field in _SKIP_RELATIONSHIPS:
            continue
        data = relationship.get("data")
        if not data:
            continue
        references = data if isinstance(data, list) else [data]
        entities = []
        for ref in references:
            entity = included.get((ref["type"], ref["id"]))
            if entity is not None:
                entities.append(
                    {
                        "id": entity["id"],
                        "type": entity["type"],
                        **entity.get("attributes", {}),
                    }
                )
        if entities:
            related[field] = entities

    return {
        "id": node["id"],
        "type": node["type"],
        **node.get("attributes", {}),
        "related": related,
    }


def fetch_nodes(content_type: str, status: int | None = 1) -> list[dict[str, Any]]:
    """Fetch every node of ``content_type`` with related data resolved inline.

    Args:
        content_type: Machine name, e.g. ``"feature_articles"`` or ``"news"``.
        status: ``1`` = published (default), ``0`` = unpublished, ``None`` = no
            filter. NOTE: unpublished content requires an authenticated request;
            an anonymous call returns an empty list for ``status=0``. See
            README.md ("Fetching unpublished content").

    Returns:
        A list of nodes. Each node is a flat dict of its own attributes plus a
        ``"related"`` dict mapping each field to its resolved related entities.

    Pagination is handled internally by following ``links.next`` until exhausted.
    """
    url = _build_first_url(content_type, status)

    raw_nodes: list[dict] = []
    included_index: dict[tuple[str, str], dict] = {}
    while url:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        doc = response.json()
        raw_nodes.extend(doc.get("data", []))
        _index_included(doc.get("included", []), included_index)
        # links.next carries all our query params forward; absent => last page.
        url = (doc.get("links", {}).get("next") or {}).get("href")

    return [_resolve_node(node, included_index) for node in raw_nodes]


if __name__ == "__main__":
    import json
    import sys

    content_type = sys.argv[1] if len(sys.argv) > 1 else "feature_articles"
    status = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    nodes = fetch_nodes(content_type, status=status)
    print(f"Fetched {len(nodes)} '{content_type}' node(s) (status={status})")
    if nodes:
        print("\nFirst node (truncated):")
        preview = json.dumps(nodes[0], indent=2, ensure_ascii=False)
        print(preview[:3000] + ("\n... (truncated)" if len(preview) > 3000 else ""))
