"""Neo4j projection of the knowledge layer.

Neo4j is a *rebuildable projection* of MySQL and Qdrant, never a system of
record. Nothing here may be the only copy of anything: a corrupt graph is fixed
by rebuilding it, and an unreachable graph degrades the knowledge layer without
touching ingestion or existing retrieval.
"""
