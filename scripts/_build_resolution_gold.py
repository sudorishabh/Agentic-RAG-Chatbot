"""One-off builder for the reviewed resolution gold set.

Kept as a script so the case list is reviewable in version control rather than
buried in a shell heredoc. Re-run it to regenerate
``reports/knowledge/gold_resolution_v1.json`` after editing the cases below.

Expectations
    NAME:<canonical>  must link to that entity (AUTO when the entity is
                      canonical, PROVISIONAL when it is a provisional identity)
    NO_LINK           must not link at all
    NO_CANONICAL      may group provisionally, must NOT assert a canonical
                      identity -- the requirement that a provisional person
                      can never become a claim subject
    CODE              must resolve through the Tier-0 identifier path
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

P, O, J = "PERSON", "ORGANIZATION", "PROJECT"


def c(cid, t, surface, category, expected, note,
      authors=None, orgs=None, projects=None):
    return {
        "id": cid, "type": t, "surface": surface, "category": category,
        "expected": expected, "note": note,
        "doc_authors": authors or [], "doc_orgs": orgs or [],
        "co_projects": projects or [],
    }


CASES = [
    # --- AUTHORITATIVE people: the only PERSONs that may be canonical --------
    c("p-01", P, "Dr Vibha Dhawan", "authoritative+corroborated",
      "NAME:Dr Vibha Dhawan", "people-bundle node; the CMS asserts this identity",
      ["Dr Vibha Dhawan"]),
    c("p-02", P, "Mr Nitin Desai", "authoritative+corroborated",
      "NAME:Mr Nitin Desai", "people-bundle node", ["Mr Nitin Desai"]),
    c("p-03", P, "Ms Vaishali Nigam Sinha", "authoritative+honorific",
      "NAME:Ms Vaishali Nigam Sinha", "honorific folds before comparison",
      ["Ms Vaishali Nigam Sinha"]),
    c("p-04", P, "Vaishali Nigam Sinha", "authoritative+no_honorific",
      "NAME:Ms Vaishali Nigam Sinha", "same person written without the honorific",
      ["Ms Vaishali Nigam Sinha"]),
    c("p-05", P, "Mr M S Unnikrishnan", "authoritative+initials_in_name",
      "NAME:Mr M S Unnikrishnan",
      "initials inside an otherwise full name are part of it",
      ["Mr M S Unnikrishnan"]),
    c("p-06", P, "Dr Vibha Dhawan", "authoritative+no_context", "NO_CANONICAL",
      "even an authoritative name needs corroboration before it links"),
    c("p-07", P, "Dr Vibha Dhawan", "authoritative+contradicted", "NO_LINK",
      "the document is by someone else entirely", ["Mr Ajay Shankar"]),

    # --- PROVISIONAL people: may group, must never be canonical --------------
    c("p-08", P, "Dr Shailly Kedia", "provisional+corroborated", "NO_CANONICAL",
      "author-facet name; corroborated but still only a name",
      ["Dr Shailly Kedia"]),
    c("p-09", P, "Dr Debajit Palit", "provisional+corroborated", "NO_CANONICAL",
      "author-facet name", ["Dr Debajit Palit"]),
    c("p-10", P, "Dr Ritu Mathur", "provisional+corroborated", "NO_CANONICAL",
      "author-facet name", ["Dr Ritu Mathur"]),
    c("p-11", P, "Mr Ajay Shankar", "provisional+corroborated", "NO_CANONICAL",
      "the most prolific author in the facet", ["Mr Ajay Shankar"]),
    c("p-12", P, "Dr Prodipto Ghosh", "provisional+no_context", "NO_CANONICAL",
      "no corroboration, and provisional either way"),
    c("p-13", P, "Dr Anjali Parasnis", "provisional+no_context", "NO_CANONICAL",
      "no corroboration"),
    c("p-14", P, "Mr Sanjay Seth", "provisional+no_context", "NO_CANONICAL",
      "no corroboration"),
    c("p-15", P, "Dr Leena Srivastava", "provisional+no_context", "NO_CANONICAL",
      "no corroboration"),

    # --- same-name and shared-surname risk -----------------------------------
    c("p-16", P, "Sharma", "surname_only", "NO_LINK",
      "17 people in the facet share this surname"),
    c("p-17", P, "Kumar", "surname_only", "NO_LINK", "24 people share it"),
    c("p-18", P, "Singh", "surname_only", "NO_LINK", "28 people share it"),
    c("p-19", P, "Dr Narayan Singh", "shared_surname+full_name", "NO_CANONICAL",
      "the full name distinguishes among 28 Singhs, but stays provisional",
      ["Dr Narayan Singh"]),
    c("p-20", P, "Dr Prasoon Singh", "shared_surname+full_name", "NO_CANONICAL",
      "a different Singh; must not collapse into the previous one",
      ["Dr Prasoon Singh"]),
    c("p-21", P, "Mr Siddharth Sharma", "authoritative_vs_surname",
      "NAME:Mr Siddharth Sharma",
      "an authoritative Sharma; the other 17 must not interfere",
      ["Mr Siddharth Sharma"]),

    # --- initials -------------------------------------------------------------
    c("p-22", P, "A. K.", "initials_only", "NO_LINK", "names nobody in particular"),
    c("p-23", P, "R K", "initials_only", "NO_LINK", "initials are not an identity"),
    c("p-24", P, "M S", "initials_only", "NO_LINK",
      "shares initials with the authoritative M S Unnikrishnan and must not link"),
    c("p-25", P, "S S", "initials_only", "NO_LINK", "33 people share these initials"),

    # --- honorific variants ---------------------------------------------------
    c("p-26", P, "Prof Shailly Kedia", "honorific_variant", "NO_CANONICAL",
      "a different honorific on the same name must not change the outcome",
      ["Dr Shailly Kedia"]),
    c("p-27", P, "Shri Ajay Shankar", "honorific_variant", "NO_CANONICAL",
      "Indic honorifics fold too", ["Mr Ajay Shankar"]),

    # --- contradictory context -------------------------------------------------
    c("p-28", P, "Dr Shailly Kedia", "contradictory_context", "NO_LINK",
      "the document names a different author", ["Mr R R Rashmi"]),
    c("p-29", P, "Dr Debajit Palit", "contradictory_context", "NO_LINK",
      "document by someone else", ["Dr Leena Srivastava"]),

    # --- organization and project context --------------------------------------
    c("p-30", P, "Dr Shailly Kedia", "org_context_only", "NO_CANONICAL",
      "an organization in the chunk says nothing about which person this is",
      None, ["TERI"]),
    c("p-31", P, "Dr Ritu Mathur", "project_context_only", "NO_CANONICAL",
      "a project co-mention is not evidence of person identity",
      None, None, ["Water Sustainability Assessment of Chennai"]),

    # --- junk and unknown -------------------------------------------------------
    c("p-32", P, "& Sharma", "junk_surface", "NO_LINK",
      "a real facet fragment, not a person"),
    c("p-33", P, "Wholly Unknown Person", "no_candidate", "NO_LINK",
      "never asserted by the CMS"),
    c("p-34", P, "Neha", "single_token", "NO_LINK",
      "'Dr Neha' is a real facet value; one token cannot identify anyone"),

    # --- ORGANIZATION ------------------------------------------------------------
    c("o-01", O, "The Energy and Resources Institute", "acronym_gloss_expansion",
      "NAME:TERI", "the CMS seeds this as 'TERI'; the gloss supplies the full name"),
    c("o-02", O, "TERI", "acronym", "NAME:TERI", "the seeded canonical form"),
    c("o-03", O, "Ministry of External Affairs", "exact_name",
      "NAME:Ministry of External Affairs", "a real sponsor"),
    c("o-04", O, "MINISTRY OF EXTERNAL AFFAIRS", "case_variant",
      "NAME:Ministry of External Affairs", "casing folds"),
    c("o-05", O, "The Economic Times", "exact_name", "NAME:The Economic Times",
      "a real news source"),
    c("o-06", O, "Utterly Fictional Holdings", "no_candidate", "NO_LINK",
      "an organization the CMS never asserted"),
    c("o-07", O, "Environment & Waste Management", "ampersand",
      "NAME:Environment & Waste Management",
      "a real TERI division; the ampersand folds to 'and'"),

    # Reviewed debatables: real CMS values that are also ordinary words. They
    # are legitimately seeded, and what protects prose is extraction's
    # case-sensitivity for short surfaces -- not resolution refusing a
    # deliberate, correctly-cased mention.
    c("o-08", O, "Water Resources", "generic_but_real", "NAME:Water Resources",
      "a real division; extraction's case-sensitivity is the guard, not the resolver"),
    c("o-09", O, "Medium", "generic_but_real", "NAME:Medium",
      "a real publication in field_news_source, and also an ordinary noun"),
    c("o-10", O, "Forbes", "short_but_real", "NAME:Forbes", "a real publication"),

    # --- PROJECT -------------------------------------------------------------------
    c("j-01", J, "2004RP23", "project_code", "CODE", "tier 0 identifier"),
    c("j-02", J, "2099ZZ99", "unknown_code", "NO_LINK", "well-formed but unseeded"),
    c("j-03", J, "Steel", "descriptive_title", "NO_LINK",
      "a real title and an ordinary word"),
    c("j-04", J, "Summary", "descriptive_title", "NO_LINK",
      "a real title and a heading"),
    c("j-05", J, "Environmental status report for Navi Mumbai",
      "same_title_many_entities", "NO_LINK",
      "three CMS nodes share this title; there is no basis to choose"),
    c("j-06", J, "A national energy map for India - Technology vision up to 2030",
      "specific_title",
      "NAME:A national energy map for India - Technology vision up to 2030",
      "a genuinely seeded project node with a title unique across all entities"),
    c("j-07", J, "Water Sustainability Assessment of Chennai",
      "project_name_without_a_node", "NO_LINK",
      "a real project name the CMS holds only on a PDF attachment and a news "
      "item, never as a project node -- extraction finds the mention, and "
      "resolution correctly has nothing canonical to link it to"),
    c("j-08", J, "Water Sustainability Assessment of Gurugram",
      "attachment_title_not_a_node", "NO_LINK",
      "reads like a project but the row is a pdf_attachment inheriting its "
      "parent's bundle; only nodes become PROJECT entities"),
]

STATUS = (
    "Human-reviewed. Every case names a real seeded entity or a real corpus "
    "surface. Expectations: NAME:<canonical> must link to that entity; NO_LINK "
    "must not link at all; NO_CANONICAL may group provisionally but must not "
    "assert a canonical identity; CODE must use the Tier-0 path. NO_LINK and "
    "NO_CANONICAL together are the safety half of the set."
)


def main() -> int:
    out = Path("reports/knowledge/gold_resolution_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"version": "v2", "reviewed": True, "status": STATUS, "cases": CASES},
            indent=2,
        ),
        encoding="utf-8",
    )
    by_type = collections.Counter(case["type"] for case in CASES)
    by_expectation = collections.Counter(
        case["expected"] if case["expected"] in ("NO_LINK", "NO_CANONICAL", "CODE")
        else "NAME"
        for case in CASES
    )
    print(f"Wrote {out}: {len(CASES)} cases")
    print("  by type:", dict(by_type))
    print("  by expectation:", dict(by_expectation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
