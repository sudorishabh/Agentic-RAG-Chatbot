from __future__ import annotations

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    filename: str
    document_id: str
    chunks_ingested: int


class PdfIngestRunResponse(BaseModel):
    source: str
    tally: dict[str, int] = Field(default_factory=dict)


class ArticleIngestRequest(BaseModel):

    title: str | None = None
    body: str | None = None
    url: str | None = None
    uuid: str | None = None
    bundle: str = "article"
    bundles: list[str] | None = None


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
