"""Derive the relational-query benchmark from ground truth.

Run once to produce `reports/knowledge/graph_queries_v1.json`, which is then
reviewed and committed. Kept in the repository so the gold set is reproducible
and its derivation auditable, not because it is part of the pipeline.

Where the gold comes from
-------------------------
Every expected answer traces to a **human-authored Drupal field** —
`field_ongoing_sponsors`, `field_ongoing_pi_name` and their completed-project
counterparts — through MySQL and then the graph projection. Nothing here is
model output, and nothing is invented: a query is only included if the corpus
already answers it.

What is deliberately absent
---------------------------
**Superseded and disputed claims.** All 1,653 claims are `active`; the corpus
has produced no conflict yet. Fabricating one to fill a benchmark row would make
the numbers describe fiction, so those paths are covered by fixtures in
`tests/test_graph_retrieval.py` instead.

**Chunk-level evidence.** Every claim is CMS-derived and cites a document. The
chunk path is likewise tested, not benchmarked.

    python -m scripts._build_graph_benchmark
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUT = Path("reports/knowledge/graph_queries_v1.json")

# Seeds chosen for coverage, not for flattery: the organizations with the most
# current funding edges, the people leading the most projects, and — for the
# no-result class — entities that genuinely have no claim of the kind asked for.
ORGS = [
    ("org_fe5c9534f61e", "Department of Biotechnology"),
    ("org_88e3266d8acb", "Department of Science & Technology"),
    ("org_58d3cc33fc9e", "Shakti Sustainable Energy Foundation"),
    ("org_f49e864bd9f6", "The World Bank"),
]
MULTI_HOP_ORGS = [
    ("org_fe5c9534f61e", "Department of Biotechnology"),
    ("org_58d3cc33fc9e", "Shakti Sustainable Energy Foundation"),
    ("org_de67ac051b04", "European Commission"),
]
PEOPLE = [
    ("person_403e7b704e1c", "Mr R Suresh"),
    ("person_b2d6a06b8441", "Mr Prosanto Pal"),
    ("person_8b6a3969482f", "Mr Sharif Qamar"),
]
HISTORICAL_ORGS = [
    ("org_fe5c9534f61e", "Department of Biotechnology"),
    ("org_221431e32475", "Ministry of New and Renewable Energy"),
    ("org_1158b27b5209", "Ministry of Environment and Forests"),
]
# Real entities with no claim of the asked-for kind: only FUNDED_BY and LED_BY
# claims exist, so an employment question is a true empty result rather than a
# lookup failure.
NO_RESULT_PEOPLE = [
    ("person_403e7b704e1c", "Mr R Suresh"),
    ("person_b2d6a06b8441", "Mr Prosanto Pal"),
]

# Questions that name no resolvable entity, or name one but ask nothing
# relational. These measure false routing: the graph must decline all of them.
NON_RELATIONAL = [
    ("What are the environmental impacts of solar energy?", "no entity named"),
    ("How does India's energy policy address climate change?", "no entity named"),
    ("Tell me about the Department of Biotechnology", "entity, but topical"),
    ("What is the Department of Biotechnology's mission statement?",
     "entity, but not a relationship in the vocabulary"),
    ("Summarise TERI's work on air quality", "ambiguous entity, topical"),
]

# "TERI" is attested both as an organization (a sponsor) and as a person (an
# author string), so it does not autolink. A question naming only TERI must not
# route — the resolver's ambiguity is the whole point.
AMBIGUOUS = [("What projects are funded by TERI?", "TERI")]


def _rows(session, cypher: str, **params) -> list[dict[str, Any]]:
    return [dict(r) for r in session.run(cypher, **params)]


_CURRENT_FUNDING = """
MATCH (o:Organization {entity_id: $id})<-[f:FUNDED_BY {current: true}]-(p:Project)
OPTIONAL MATCH (c:Claim {claim_id: f.claim_id})-[:SUPPORTED_BY]->(d:Document)
RETURN p.entity_id AS entity_id, p.canonical_name AS name,
       f.claim_id AS claim_id, d.document_id AS document_id
ORDER BY p.canonical_name
"""

_MULTI_HOP = """
MATCH (o:Organization {entity_id: $id})<-[:FUNDED_BY {current: true}]-(p:Project)
MATCH (p)-[l:LED_BY {current: true}]->(x:Person)
OPTIONAL MATCH (c:Claim {claim_id: l.claim_id})-[:SUPPORTED_BY]->(d:Document)
RETURN x.entity_id AS entity_id, x.canonical_name AS name,
       l.claim_id AS claim_id, d.document_id AS document_id
ORDER BY x.canonical_name
"""

_LED_BY_PERSON = """
MATCH (x:Person {entity_id: $id})<-[l:LED_BY {current: true}]-(p:Project)
OPTIONAL MATCH (c:Claim {claim_id: l.claim_id})-[:SUPPORTED_BY]->(d:Document)
RETURN p.entity_id AS entity_id, p.canonical_name AS name,
       l.claim_id AS claim_id, d.document_id AS document_id
ORDER BY p.canonical_name
"""

_FUNDERS_OF_PROJECT = """
MATCH (p:Project {entity_id: $id})-[f:FUNDED_BY {current: true}]->(o:Organization)
OPTIONAL MATCH (c:Claim {claim_id: f.claim_id})-[:SUPPORTED_BY]->(d:Document)
RETURN o.entity_id AS entity_id, o.canonical_name AS name,
       f.claim_id AS claim_id, d.document_id AS document_id
ORDER BY o.canonical_name
"""

# History: funding claims whose validity has ended. These are the rows a
# current-state template deliberately cannot see.
_EXPIRED_FUNDING = """
MATCH (c:Claim {predicate: 'FUNDED_BY'})-[:OBJECT]->(o:Organization {entity_id: $id})
MATCH (c)-[:SUBJECT]->(p:Project)
WHERE c.valid_until IS NOT NULL AND c.valid_until < $today
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(d:Document)
RETURN p.entity_id AS entity_id, p.canonical_name AS name,
       c.claim_id AS claim_id, d.document_id AS document_id,
       c.valid_until AS valid_until
ORDER BY c.valid_until DESC
"""

_PROJECTS_WITH_FUNDER = """
MATCH (p:Project)-[f:FUNDED_BY {current: true}]->(:Organization)
RETURN p.entity_id AS entity_id, p.canonical_name AS name
ORDER BY p.canonical_name LIMIT 3
"""

TODAY = "2026-08-14"


def _gold(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold answer rows into the gold shape shared by every query."""
    entities, claims, documents = [], [], []
    for row in rows:
        if row.get("entity_id") and not any(
            e["entity_id"] == row["entity_id"] for e in entities
        ):
            entities.append({"entity_id": row["entity_id"], "name": row["name"]})
        for key, bucket in (("claim_id", claims), ("document_id", documents)):
            if row.get(key) and row[key] not in bucket:
                bucket.append(row[key])
    return {
        "expected_answer_entities": entities,
        "expected_claims": claims,
        "expected_evidence_documents": documents,
    }


def build() -> dict[str, Any]:
    from app.core.clients.graph import read_session

    queries: list[dict[str, Any]] = []

    def add(
        qid, cls, text, *, subject, template, mode, rows,
        characteristics, should_route=True,
    ):
        gold = _gold(rows)
        queries.append({
            "id": qid, "class": cls, "query": text,
            "should_route": should_route,
            "expected_template": template, "expected_mode": mode,
            "expected_subject": subject,
            **gold,
            "answer_characteristics": characteristics,
        })

    with read_session() as session:
        for i, (entity_id, name) in enumerate(ORGS, 1):
            rows = _rows(session, _CURRENT_FUNDING, id=entity_id)
            add(
                f"fund-{i:02d}", "current_funding",
                f"What projects are currently funded by {name}?",
                subject={"entity_id": entity_id, "name": name},
                template="projects_funded_by_org", mode="current", rows=rows,
                characteristics={
                    "must_name_at_least": 1,
                    "must_be_projects": True,
                    "must_not_present_ended_funding_as_current": True,
                    "must_cite_evidence": True,
                },
            )

        for i, (entity_id, name) in enumerate(MULTI_HOP_ORGS, 1):
            rows = _rows(session, _MULTI_HOP, id=entity_id)
            add(
                f"hop-{i:02d}", "multi_hop",
                f"Who leads projects funded by {name}?",
                subject={"entity_id": entity_id, "name": name},
                template="people_leading_projects_funded_by_org",
                mode="current", rows=rows,
                characteristics={
                    "must_name_at_least": 1,
                    "must_be_people": True,
                    "answer_requires_two_relationships": True,
                    "must_cite_evidence": True,
                },
            )

        for i, (entity_id, name) in enumerate(PEOPLE, 1):
            rows = _rows(session, _LED_BY_PERSON, id=entity_id)
            add(
                f"lead-{i:02d}", "leadership",
                f"What projects does {name} lead?",
                subject={"entity_id": entity_id, "name": name},
                template="projects_led_by_person", mode="current", rows=rows,
                characteristics={
                    "must_name_at_least": 1,
                    "must_be_projects": True,
                    "must_cite_evidence": True,
                },
            )

        for i, row in enumerate(_rows(session, _PROJECTS_WITH_FUNDER), 1):
            funders = _rows(session, _FUNDERS_OF_PROJECT, id=row["entity_id"])
            # Some CMS titles are themselves quoted; quoting again would put the
            # question's own punctuation inside the entity surface.
            title = row["name"].strip().strip('"').strip()
            add(
                f"funder-{i:02d}", "funders_of_project",
                f"Who funded the project \"{title}\"?",
                subject={"entity_id": row["entity_id"], "name": title},
                template="funders_of_project", mode="current", rows=funders,
                characteristics={
                    "must_name_at_least": 1,
                    "must_be_organizations": True,
                    "must_cite_evidence": True,
                },
            )

        for i, (entity_id, name) in enumerate(HISTORICAL_ORGS, 1):
            rows = _rows(session, _EXPIRED_FUNDING, id=entity_id, today=TODAY)
            add(
                f"hist-{i:02d}", "historical",
                f"What projects has {name} funded in the past?",
                subject={"entity_id": entity_id, "name": name},
                template="org_funding_history", mode="historical", rows=rows,
                characteristics={
                    "must_name_at_least": 1,
                    "must_include_ended_relationships": True,
                    "must_not_present_ended_funding_as_current": True,
                    "must_cite_evidence": True,
                },
            )

        for i, (entity_id, name) in enumerate(NO_RESULT_PEOPLE, 1):
            add(
                f"none-{i:02d}", "no_result",
                f"Which organisation does {name} work at?",
                subject={"entity_id": entity_id, "name": name},
                template="person_works_at", mode="current", rows=[],
                characteristics={
                    "must_name_at_least": 0,
                    "must_return_no_graph_rows": True,
                    "must_not_fabricate_an_employer": True,
                },
            )

    for i, (text, why) in enumerate(NON_RELATIONAL, 1):
        queries.append({
            "id": f"noroute-{i:02d}", "class": "non_relational", "query": text,
            "should_route": False, "why_not": why,
            "expected_template": None, "expected_mode": None,
            "expected_subject": None,
            "expected_answer_entities": [], "expected_claims": [],
            "expected_evidence_documents": [],
            "answer_characteristics": {
                "must_fall_back_to_existing_retrieval": True,
            },
        })

    for i, (text, surface) in enumerate(AMBIGUOUS, 1):
        queries.append({
            "id": f"ambig-{i:02d}", "class": "ambiguous", "query": text,
            "should_route": False,
            "why_not": f"{surface!r} resolves to more than one entity type",
            "expected_template": None, "expected_mode": None,
            "expected_subject": None,
            "expected_answer_entities": [], "expected_claims": [],
            "expected_evidence_documents": [],
            "answer_characteristics": {
                "must_not_guess_an_entity": True,
                "must_fall_back_to_existing_retrieval": True,
            },
        })

    return {
        "version": "graph_v1",
        "status": "reviewed",
        "built": TODAY,
        "purpose": (
            "Compare existing dense/lexical retrieval against graph retrieval on "
            "relational questions, and measure routing precision and recall."
        ),
        "gold_provenance": (
            "Expected answers derive from human-authored Drupal fields "
            "(field_ongoing_sponsors, field_ongoing_pi_name and their completed "
            "counterparts) via MySQL and the graph projection. No model output."
        ),
        "known_limits": [
            "Evidence-document recall is tautological for graph retrieval: the "
            "gold documents are the ones its claims cite. Only answer-entity "
            "coverage, routing and latency compare the two methods fairly.",
            "No superseded or disputed claims exist in the corpus (all 1,653 are "
            "active), so those paths are covered by fixtures, not benchmarked.",
            "No claim carries chunk-level evidence, so the chunk hydration path "
            "is tested rather than benchmarked.",
        ],
        "classes": [
            "current_funding", "multi_hop", "leadership", "funders_of_project",
            "historical", "no_result", "non_relational", "ambiguous",
        ],
        "queries": queries,
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    by_class: dict[str, int] = {}
    for query in payload["queries"]:
        by_class[query["class"]] = by_class.get(query["class"], 0) + 1
    print(f"Wrote {len(payload['queries'])} queries to {OUT}")
    for name, count in sorted(by_class.items()):
        print(f"  {name:22} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
