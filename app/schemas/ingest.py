from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _clean_bundles(value: list[str] | None) -> list[str] | None:
    """Drop blank entries; treat an empty/blank list as 'use default bundles'."""
    if not value:
        return None
    cleaned = [b.strip() for b in value if b and b.strip()]
    return cleaned or None


class IngestResponse(BaseModel):
    filename: str
    document_id: str
    chunks_ingested: int


class PdfIngestRunResponse(BaseModel):
    source: str
    tally: dict[str, int] = Field(default_factory=dict)


class DirectIngestRequest(BaseModel):
    bundles: list[str] | None = Field(default=None, examples=[["news"]])
    reconcile: bool = False

    _normalize_bundles = field_validator("bundles")(_clean_bundles)


class DirectIngestResponse(BaseModel):
    pdf_source: str | None = None
    pdfs: dict[str, int] = Field(default_factory=dict)
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
    source_type: str = "article"
    sweep: bool = False


class ReindexResponse(BaseModel):
    status: str
    detail: dict = Field(default_factory=dict)
