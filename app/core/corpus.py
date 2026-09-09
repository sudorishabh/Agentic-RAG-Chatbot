"""What the corpus is made of: the content types both paths have to agree about.

This exists for the same reason :mod:`app.core.editions` does. The bundle list is
*ingestion's* configuration — it decides what to crawl — but the read path needs
the identical list for three different jobs:

* :mod:`app.retrieval.understanding.catalog_prompt` describes the corpus to the
  model, and a bundle missing from that description is a bundle the model will
  not ask for;
* :mod:`app.retrieval.structured.entities` registers one queryable entity per
  bundle, so the structured planner can count and list them;
* :mod:`app.pipeline.summarize` decides whether a scope name is a bundle.

Those three used to import ``DEFAULT_BUNDLES`` from
``app.ingestion.extractors.drupal_extractor`` — the read path reaching into a
write-path *extractor* for a list of names. That is backwards, and it is the kind
of import that quietly makes retrieval depend on how the crawler happens to be
implemented.

So the vocabulary lives in the neutral core layer and both paths read it from
here. Ingestion still owns the *decision* of what to crawl: it re-exports this
list under its own name and adds the crawl-only settings (block types, the
searchable-entity allowlist) that no reader has any use for.
"""
from __future__ import annotations

__all__ = ["DEFAULT_BUNDLES", "OPEN_ENDED_BUNDLES", "SCHEDULED_BUNDLES"]

#: The Drupal node bundles that make up the corpus.
#:
#: ``carousel`` is deliberately absent: those nodes are homepage promo slides
#: carrying a title and no body, so they chunk to nothing, and both of the live
#: ones name subjects already covered by real news and event content.
#:
#: This is the list ingestion *attempts*. A bundle that exists here but has no
#: rows in a given deployment is a bundle that was configured and never
#: populated, which is why the read path checks it against the catalog rather
#: than trusting it (see ``catalog_prompt.describe_corpus``).
DEFAULT_BUNDLES: tuple[str, ...] = (
    "article",
    "page",
    "research_papers",
    "completed_projects",
    "feature_articles",
    "ongoing_projects",
    "news",
    "events",
    "press_release",
    "policy_brief",
    "videos",
    "infographics",
    "services",
    "report",
    "people",
)


#: Bundles whose date is a *scheduled occurrence* rather than a publication.
#:
#: This is what makes "upcoming" a meaningful question. An event has a date it
#: will happen on; a news item has a date it was published on, and asking
#: whether it is upcoming is a category error. The read path needs the
#: distinction for the temporal gate and must not get it by reading a Drupal
#: field name out of the metadata blob — the canonical
#: ``effective_start_date`` already *is* the event's start date, because the
#: bundle names the field it is dated by.
SCHEDULED_BUNDLES: frozenset[str] = frozenset({"events"})

#: Bundles whose period is open at the far end: a start, and no end until
#: someone says otherwise.
#:
#: ``ongoing_projects`` declares only a start field, deliberately — an *ongoing*
#: project has no end date. Stored, that is indistinguishable from a single-date
#: document, so a range query would treat a project running since 2005 as a
#: point in 2005 and miss it for 2022. Declared here, the read path can read it
#: as "from its start until now", which is what the bundle means.
OPEN_ENDED_BUNDLES: frozenset[str] = frozenset({"ongoing_projects"})
