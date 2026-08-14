"""Render verified graph rows as a citable context block.

Why this exists
---------------
The Phase 10 benchmark found graph retrieval scoring **zero** answer coverage on
multi-hop questions it had answered perfectly. The traversal returned twelve
principal investigators; the context contained none of their names.

The reason is that hydration returns *evidence*, and for a CMS-derived claim the
evidence is a project page whose body never states the fact — the PI lives in
`field_ongoing_pi_name`, a structured field that was never prose. So the graph
knew the answer, cited the right document, and handed on a passage that did not
contain it.

For a relational question the **rows are the answer** and the chunks are the
citation. This module renders the rows so both reach the model, each labelled
for what it is.

What it will not do
-------------------
It states only what the graph asserts, and annotates every row with its validity
and status. An ended relationship reads "until 2021-03-31" and a contradicted
one is marked disputed, so a superseded or disputed fact cannot be read as a
current one. Every line carries its `claim_id`, so a claim is traceable from the
prompt back through the graph to the document that recorded it.
"""
from __future__ import annotations

from typing import Any

# Rows rendered into one block. The block competes with evidence passages for a
# token budget, and a hundred lines of triples would crowd out the source text
# that makes them checkable.
#
# A historical question gets more room because its answer *is* the list: asking
# what an organization has funded over time and receiving the most recent
# quarter of it is a wrong answer, not a short one.
MAX_LINES = 25
MAX_LINES_HISTORICAL = 50

# A hard character ceiling regardless of mode, so one pathological row set
# cannot crowd the evidence out of the prompt.
MAX_CHARS = 8000


def _validity(row: dict[str, Any]) -> str:
    """A human phrase for the validity window, or '' when unbounded."""
    start, end = row.get("valid_from"), row.get("valid_until")
    start = str(start)[:10] if start else None
    end = str(end)[:10] if end else None
    if start and end:
        return f" ({start} until {end})"
    if end:
        return f" (until {end})"
    if start:
        return f" (since {start})"
    return ""


def _status(row: dict[str, Any]) -> str:
    """A marker for anything that must not be read as a settled current fact."""
    status = row.get("status")
    if status == "disputed":
        return " [DISPUTED - the sources contradict each other]"
    if status == "superseded":
        return " [SUPERSEDED by a later record]"
    if status in (None, "active"):
        return ""
    return f" [{status}]"


def _predicate_phrase(predicate: str | None) -> str:
    return {
        "FUNDED_BY": "is funded by",
        "LED_BY": "is led by",
        "WORKS_AT": "works at",
        "MEMBER_OF": "is a member of",
        "PARTNER_OF": "is a partner of",
        "PARENT_OF": "is the parent of",
        "HAS_ROLE": "has the role",
    }.get(predicate or "", "is related to")


def _line(row: dict[str, Any]) -> str | None:
    """One row as a sentence, chosen by which names the row actually carries.

    Driven by the row's shape rather than by a per-template formatter, so a
    template added to the registry renders without another branch here.
    """
    person = row.get("person_name")
    project = row.get("project_name")
    funder = row.get("funder_name")
    organization = row.get("organization_name")

    if project and person and funder:
        text = f"{funder} funds \"{project}\", which is led by {person}"
    elif project and person:
        text = f"\"{project}\" is led by {person}"
    elif project and funder:
        text = f"\"{project}\" is funded by {funder}"
    elif person and organization:
        text = f"{person} — {organization}"
    elif row.get("subject_name"):
        phrase = _predicate_phrase(row.get("predicate"))
        obj = row.get("object_name") or row.get("object_literal") or "(unknown)"
        text = f"{row['subject_name']} {phrase} {obj}"
    elif project:
        text = f"\"{project}\""
    elif organization or funder:
        text = str(organization or funder)
    else:
        return None

    claim_id = row.get("claim_id")
    citation = f" [{claim_id}]" if claim_id else ""
    return f"- {text}{_validity(row)}{_status(row)}{citation}"


def render(result: Any, route: Any = None) -> str | None:
    """The facts block, or None when there is nothing to state."""
    if result is None or not result.rows:
        return None

    historical = result.mode == "historical"
    max_lines = MAX_LINES_HISTORICAL if historical else MAX_LINES

    lines: list[str] = []
    spent = 0
    for row in result.rows:
        rendered = _line(row)
        if not rendered or rendered in lines:
            continue
        if len(lines) >= max_lines or spent + len(rendered) > MAX_CHARS:
            break
        lines.append(rendered)
        spent += len(rendered)
    if not lines:
        return None

    subject = getattr(route, "entity_name", None)
    heading = "Verified relationships recorded in the knowledge graph"
    if subject:
        heading += f" for {subject}"
    if result.mode == "historical":
        heading += " (including past relationships)"

    remaining = len(result.rows) - len(lines)
    footer = ""
    if remaining > 0:
        footer = f"\n(+{remaining} further records not shown)"
    elif result.truncated:
        footer = "\n(more records exist than were retrieved)"

    return f"{heading}:\n" + "\n".join(lines) + footer


def as_block(result: Any, route: Any = None) -> Any:
    """The facts rendered as a `ContextBlock`, or None.

    Numbered 1 by convention; the caller renumbers the evidence blocks that
    follow so the citations a model emits stay consistent.
    """
    from app.core.models.context import ContextBlock

    text = render(result, route)
    if text is None:
        return None
    return ContextBlock(
        n=1,
        text=text,
        payload={
            "source": "knowledge_graph",
            "kind": "graph_facts",
            "template_id": result.template_id,
            "mode": result.mode,
            "claim_ids": list(result.claim_ids),
            "entity_ids": list(result.entity_ids),
            "document_ids": list(result.document_ids),
            "disputed": result.has_disputed,
        },
        score=1.0,
    )
