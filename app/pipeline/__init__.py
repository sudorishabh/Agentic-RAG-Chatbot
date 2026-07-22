"""Application orchestration layer.

Combines the retrieval and generation packages into the end-to-end query
pipeline (query understanding → cache → retrieve → generate → assemble → persist
→ record). This is the only layer that depends on both retrieval and generation;
neither depends on the other.
"""
from app.pipeline.query_pipeline import search_blocks, stream_answer

__all__ = ["stream_answer", "search_blocks"]
