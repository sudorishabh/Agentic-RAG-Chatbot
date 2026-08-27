"""The read path: a question -> ordered context blocks.

Stages, in the order a query moves through them:

    understanding/  question -> QueryAnalysis (intents, filters, scope)
    search/         candidate fetch from Qdrant + reranking
    context/        admitted candidates -> numbered blocks + citations
    retriever.py    orchestrates the above; the package entry point

Two alternative answer routes sit beside that pipeline and are chosen by the
caller, not by it:

    structured/     questions the catalog can answer exactly (counts, lists)
    graph/          questions the knowledge graph can answer (verified relations)

Import direction is one-way: understanding -> search -> context, with retriever,
structured and graph above them. Nothing here imports app.pipeline or
app.generation.

Deliberately no imports in this file. The graph subpackage must not load when
production retrieval is imported, and `retriever.py` is the only module allowed
to name it at all — both properties are asserted in
tests/retrieval/graph/test_graph_retrieval.py, which searches for the dotted
path as text. That is why this docstring spells it out in prose.
"""
