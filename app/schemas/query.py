"""Query API models.

The response carries the grounded ``answer`` (with inline ``[n]`` markers) plus
a structured ``citations`` list built in code from the retrieved-chunk payloads
(§8) — the LLM only emits the markers, never the citation metadata.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    """One prior turn of the conversation, used to resolve pronouns at rewrite."""

    role: str = Field(description='"user" or "assistant"')
    content: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    # Recent conversation, oldest first, for query rewriting (§6.1).
    history: list[ChatTurn] = Field(default_factory=list)
    # RBAC / multi-tenancy — enforced as Qdrant payload filters (§5.4, §10.7).
    tenant_id: str = "default"
    user_groups: list[str] = Field(default_factory=lambda: ["public"])
    # Override the reranked context size (N); None uses the configured default.
    top_k: int | None = None
    # Reserved for the streaming endpoint; the JSON endpoint ignores it.
    stream: bool = False


class CitationSource(BaseModel):
    """A secondary/alternate source for the same claim (§8.4 / §9.1)."""

    type: str
    title: str | None = None
    url: str | None = None
    page: int | None = None
    section: str | None = None


class Citation(BaseModel):
    """One numbered source, mapped from a retrieved chunk's payload (§8.3)."""

    n: int
    type: str  # "article" | "pdf" | ...
    title: str | None = None
    url: str | None = None
    page: int | None = None
    section: str | None = None
    document_id: str | None = None
    # Alternate sources covering the same material (dedup, §9.1).
    also_available: list[CitationSource] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    # "qa" (full RAG), "structured" (Drupal lookup/aggregate), or "chitchat".
    intent: str = "qa"
    used_chunks: int = 0
    # True when the pipeline surfaced a PDF/article disagreement (§9.3).
    conflict: bool = False
    # True when served from the response cache (§10.3).
    cached: bool = False


class FeedbackRequest(BaseModel):
    """Thumbs up/down + which citations were clicked — the §10.4 feedback loop."""

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
