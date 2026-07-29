"""Shared text for the three prompts that describe the document catalog's
database slots to an LLM: the intent classifier
(`app.retrieval.understanding.prompts`), the slot-extraction fallback
(`app.retrieval.structured.answerer`), and the v2 tool-calling planner
(`app.retrieval.structured.planner`). Kept in one place so the bundle list, the
vocabulary mapping, and the collective-word warning don't drift across three
independently-edited strings, each previously hand-duplicating its own version.

Each block is a self-contained sentence/paragraph meant to be appended as its
own line wherever it applies — not designed to be spliced mid-sentence. See
docs/database-retrieval-redesign.md §10.
"""

from __future__ import annotations

from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES

BUNDLE_LIST = ", ".join(DEFAULT_BUNDLES)

VOCABULARY = (
    "Vocabulary: \"articles\", \"items\", \"stories\", \"pieces\", and \"entries\" "
    "all mean a catalog record in general — none of them names a specific content "
    "type. A bundle's own name (e.g. \"events\", \"reports\", \"press releases\") "
    "does name one; users never say the word \"bundle\" itself."
)

COLLECTIVE_WORD_WARNING = (
    "A generic collective word (\"publications\", \"works\", \"output\", "
    "\"everything\") means every content type, not one — leave the content type "
    "null for these rather than collapsing onto a single bundle (do not map "
    "\"publications\" to research_papers)."
)

# resolve_entity is not advertised for tags — see
# docs/database-retrieval-redesign.md §3/§4.1: a dev-DB sample found ~237
# freeform tag terms over ~224 tagged documents, the shape of long-tail CMS
# tagging rather than a curated vocabulary fuzzy matching could usefully rank.
RESOLVE_FIRST = (
    "Names are resolved for you: pass an author or theme through exactly as the "
    "user wrote it (\"rishab negi\", \"climate\", \"env theme\") — the query layer "
    "matches it to the catalog's canonical name before filtering, and reports "
    "back which entity it used. Do NOT add a separate resolve_entity call just "
    "to look a name up first; its result cannot reach another call in the same "
    "plan. Call resolve_entity only when the user is explicitly asking which "
    "entities match a name (\"is there an author called Negi?\")."
)

OPERATIONS = (
    "count_records answers \"how many\" of one thing. aggregate_records answers "
    "\"how many per X\" or \"which X does Y appear in\" — always ONE call, never "
    "one call per value. list_records is for when the user wants to see rows or "
    "metadata, not just a number."
)

BEHAVIOR = (
    "Themes: a specific theme is a normal filter; \"how many themes are there?\" "
    "means list_themes, which lists Main themes first and Other themes in a "
    "separate section.\n"
    "Ambiguity: if resolve_entity returns more than one close match, ask the "
    "user to pick — never silently choose the top candidate.\n"
    "No fabrication: if a filter does not resolve to anything, say so explicitly "
    "(e.g. \"no author matching 'X' found\") rather than treating it as zero.\n"
    "Always name the resolved entities in the final answer, so the user can "
    "catch a wrong match."
)

FEW_SHOTS = (
    "Examples (the tool calls, not the answer). Names go in as written — the "
    "query layer canonicalizes them:\n"
    "1. \"How many posts are there from Rishabh Negi?\" -> "
    "count_records(filters={author=\"Rishabh Negi\"}).\n"
    "2. \"How many events are there?\" -> count_records(entity=\"events\").\n"
    "3. \"How many themes are there?\" -> list_themes().\n"
    "4. \"How many events are under Climate Change?\" -> "
    "count_records(entity=\"events\", filters={theme=\"Climate Change\"}).\n"
    "5. \"How many posts from rishab negi under env theme?\" -> "
    "count_records(filters={author=\"rishab negi\", theme=\"env theme\"}) — one "
    "call; the misspelling and the abbreviation are resolved for you.\n"
    "6. \"Which bundles does Rishabh Negi post in?\" -> "
    "aggregate_records(group_by=\"content_type\", filters={author=\"Rishabh Negi\"}).\n"
    "7. \"Latest 5 reports under Climate Change with their source links\" -> "
    "list_records(entity=\"report\", limit=5, filters={theme=\"Climate Change\"}).\n"
    "8. \"How many posts are tagged 'policy'?\" -> "
    "count_records(filters={tag=\"policy\"}) — tags are matched exactly.\n"
    "9. \"Is there an author called Negi?\" -> resolve_entity(\"Negi\", \"author\") "
    "— the question IS about which entities match, so resolving is the answer.\n"
    "The query layer handles the rest: a name matching several entities returns a "
    "clarification question instead of a count, and a name matching nothing "
    "returns \"no author matching 'X' found\" rather than a misleading zero. Plan "
    "the query you want; do not pre-resolve names yourself."
)
