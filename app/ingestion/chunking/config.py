"""Chunk sizing configuration: per-bundle presets for parent/child token targets."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:

    child_target_tokens: int = 400
    child_max_tokens: int = 512
    child_min_tokens: int = 120
    child_overlap_tokens: int = 60
    parent_target_tokens: int = 1800
    parent_max_tokens: int = 2400
    encoding_name: str = "cl100k_base"


_BASE = ChunkingConfig()

_PRESETS: dict[str, ChunkingConfig] = {
    "pdf": ChunkingConfig(
        child_target_tokens=450, child_max_tokens=560, child_overlap_tokens=60,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "manual": ChunkingConfig(
        child_target_tokens=450, child_max_tokens=560, child_overlap_tokens=60,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "research_paper": ChunkingConfig(
        child_target_tokens=480, child_max_tokens=560, child_overlap_tokens=48,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "research_papers": ChunkingConfig(
        child_target_tokens=480, child_max_tokens=560, child_overlap_tokens=48,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "policy": ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_overlap_tokens=60,
        parent_target_tokens=1800, parent_max_tokens=2400,
    ),
    "policy_brief": ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_overlap_tokens=60,
        parent_target_tokens=1800, parent_max_tokens=2400,
    ),
    "report": ChunkingConfig(
        child_target_tokens=420, child_max_tokens=540, child_overlap_tokens=60,
        parent_target_tokens=1900, parent_max_tokens=2500,
    ),
    "article": ChunkingConfig(
        child_target_tokens=380, child_max_tokens=480, child_overlap_tokens=40,
        parent_target_tokens=1600, parent_max_tokens=2200,
    ),
    "small_pdf": ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_overlap_tokens=50,
        parent_target_tokens=100_000, parent_max_tokens=100_000,
    ),
}

for _bundle in (
    "news", "feature_articles", "events", "press_release", "videos",
    "infographics", "services", "people", "page", "completed_projects",
    "ongoing_projects",
):
    _PRESETS.setdefault(_bundle, _PRESETS["article"])

# PDFs attached to Drupal nodes chunk like any other PDF.
_PRESETS.setdefault("pdf_attachment", _PRESETS["pdf"])

# "website" is the canonical source_type for Drupal content (renamed from
# "article"); it must resolve to the article preset, not _BASE.
_PRESETS.setdefault("website", _PRESETS["article"])


def config_for(key: str | None) -> ChunkingConfig:
    if not key:
        return _BASE
    return _PRESETS.get(key.strip().lower(), _BASE)
