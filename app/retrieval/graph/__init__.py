"""Graph retrieval: the read side of the knowledge layer.

Isolated by construction. Nothing in the default retrieval path imports this
package, and ``graph_retrieval_enabled`` is off — so with the flag down the
existing dense/lexical pipeline behaves exactly as it did before the graph
existed.

The flow, and where each store's responsibility begins:

    question -> router -> template registry -> Neo4j
                                                 |
                          entity ids, claim ids, chunk/document ids
                                                 |
                                        batched Qdrant lookup
                                                 |
                                       existing reranker/context
                                                 |
                                                LLM

Neo4j returns *identifiers and structure*, never source text. Qdrant remains the
only place chunk text lives, and the hop between them is `chunk_id`, which has
been the cross-store key since long before the graph.
"""
