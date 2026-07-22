"""Small text helpers shared across ingestion (previously duplicated per-module)."""
from __future__ import annotations

import re


def slugify(value: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return slug or "document"
