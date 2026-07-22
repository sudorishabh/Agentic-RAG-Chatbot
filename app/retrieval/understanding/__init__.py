"""Query understanding.

The classification pipeline (LLM call, voting/merge, legacy derivation) and its
data contracts live in :mod:`app.retrieval.query_processor`; the large prompt
text and the Qdrant facet-filter builder are split out here to keep that module
focused on control flow.
"""
