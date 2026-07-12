from __future__ import annotations

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):

    role: str = Field(description='"user" or "assistant"')
    content: str


class QueryRequest(BaseModel):
    # tenant_id / user_groups are intentionally absent: the caller's tenant and
    # authorization groups come from the authenticated principal (see
    # app/api/auth.py), never from the request body.
    question: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)
    # Bounded: this is public input, and an absurd top_k inflates retrieval and
    # context-assembly work per request. None = server default.
    top_k: int | None = Field(default=None, ge=1, le=50)
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
    answer_format: str = "default"
    used_chunks: int = 0
    conflict: bool = False
    # A number in the answer was not found in any cited block (observe-only
    # deterministic check; see faithfulness.numeric_mismatches).
    numeric_mismatch: bool = False
    cached: bool = False


class SearchRequest(BaseModel):
    # Identity comes from the authenticated principal, not the body (see QueryRequest).
    question: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)
    top_k: int | None = Field(default=None, ge=1, le=50)


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
    answer_format: str = "default"
    search_query: str
    blocks: list[SearchBlock] = Field(default_factory=list)
