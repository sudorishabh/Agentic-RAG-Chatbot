"""Search strategies.

The dense/keyword search primitive lives in :mod:`app.retrieval.hybrid_search`;
this package layers the recall-expansion strategies on top of it (website-biased
dual pull, keyword full-text leg, multi-query paraphrasing, one-shot corrective
requery). They were previously private helpers in the monolithic ``app.rag``.
"""
