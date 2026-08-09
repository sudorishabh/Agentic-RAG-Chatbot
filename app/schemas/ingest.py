from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_bundles(value: list[str] | None) -> list[str] | None:
    """Drop blank entries; treat an empty/blank list as 'use default bundles'."""
    if not value:
        return None
    cleaned = [b.strip() for b in value if b and b.strip()]
    return cleaned or None


class DirectIngestRequest(BaseModel):
    bundles: list[str] | None = Field(default=None, examples=[["news"]])
    reconcile: bool = False

    _normalize_bundles = field_validator("bundles")(_clean_bundles)


class DirectIngestResponse(BaseModel):
    drupal: dict[str, int] = Field(default_factory=dict)


class ArticleIngestRequest(BaseModel):

    title: str | None = None
    body: str | None = None
    url: str | None = None
    uuid: str | None = None
    bundle: str = "article"
    bundles: list[str] | None = Field(default=None, examples=[["news"]])

    _normalize_bundles = field_validator("bundles")(_clean_bundles)


class ArticleIngestResponse(BaseModel):
    document_id: str | None = None
    chunks_ingested: int | None = None
    crawled: dict[str, int] | None = None


class ReindexRequest(BaseModel):

    document_id: str | None = None
    source_type: str = "website"
    sweep: bool = False


class ReindexResponse(BaseModel):
    status: str
    detail: dict = Field(default_factory=dict)


class IngestLogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    run_id: str | None = None
    document_id: str
    source_type: str
    source_path: str | None = None
    source_url: str | None = None
    bundle: str | None = None
    tags: str | None = None
    title: str | None = None
    status: str
    doc_version: int | None = None
    chunks_indexed: int | None = None
    fingerprint: str | None = None
    content_hash: str | None = None
    error_message: str | None = None
    event_time: str | None = None


class IngestLogResponse(BaseModel):
    count: int
    entries: list[IngestLogEntry] = Field(default_factory=list)
