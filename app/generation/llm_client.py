"""Backwards-compatible facade.

The chat/structured LLM gateway now lives in :mod:`app.core.clients.llm` (it is a
shared concern used by retrieval and generation alike). This module re-exports it
so existing ``app.generation.llm_client`` imports keep working; prefer importing
from ``app.core.clients`` in new code.
"""
from app.core.clients.llm import _build_llm, get_llm, get_structured_llm

__all__ = ["get_llm", "get_structured_llm"]
