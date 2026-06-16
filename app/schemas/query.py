from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):

    role: str = Field(description='"user" or "assistant"')
    content: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)
    tenant_id: str = "default"
    user_groups: list[str] = Field(default_factory=lambda: ["public"])
    top_k: int | None = None
    stream: bool = False


class CitationSource(BaseModel):

    type: str
    title: str | None = None
    url: str | None = None
    page: int | None = None
    section: str | None = None


class Citation(BaseModel):

    n: int
    type: str
    title: str | None = None
    url: str | None = None
    page: int | None = None
    section: str | None = None
    document_id: str | None = None
    also_available: list[CitationSource] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    intent: str = "qa"
    used_chunks: int = 0
    conflict: bool = False
    cached: bool = False


class FeedbackRequest(BaseModel):

    question: str
    rating: Literal["up", "down"]
    answer: str | None = None
    clicked_citations: list[int] = Field(default_factory=list)
    comment: str | None = None


class SearchRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)
    tenant_id: str = "default"
    user_groups: list[str] = Field(default_factory=lambda: ["public"])
    top_k: int | None = None


class SearchBlock(BaseModel):
    n: int
    score: float
    conflict: bool = False
    text: str
    document_id: str | None = None
    source_type: str | None = None
    title: str | None = None
    page_number: int | None = None
    section_heading: str | None = None


class SearchResponse(BaseModel):
    intent: str
    search_query: str
    blocks: list[SearchBlock] = Field(default_factory=list)
