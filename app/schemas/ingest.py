"""Ingest API models."""

from __future__ import annotations

from pydantic import BaseModel


class IngestResponse(BaseModel):
    filename: str
    document_id: str
    chunks_ingested: int
