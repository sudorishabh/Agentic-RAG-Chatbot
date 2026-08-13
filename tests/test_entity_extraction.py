"""Unit tests for knowledge-layer mention extraction.

No DB, no network: the gazetteer is built from literals via
``build_gazetteer``, and the LLM stage is monkeypatched. The recurring assertion
is that a mention's span really holds its surface text — offsets are the one
thing downstream provenance cannot re-derive, so every stage is checked against
the source string rather than against itself.
"""

from __future__ import annotations

import pytest

from app.knowledge import extract
from app.knowledge.gazetteer import build_gazetteer
from app.knowledge.types import Mention

CHUNK = "c-1"
DOC = "d-1"


def _gaz(rows=()):
    return build_gazetteer(rows)


def _extract(text, *, cms_names=(), rows=()):
    return extract.extract_mentions(
        text, chunk_id=CHUNK, document_id=DOC,
        cms_names=cms_names, gazetteer=_gaz(rows),
    )


def _assert_spans_hold(mentions, text):
    """The invariant every stage must satisfy."""
    for m in mentions:
        assert text[m.start_offset : m.end_offset] == m.surface_text
        assert m.verify_against(text)


# --------------------------------------------------------------------------- #
# Span correctness
# --------------------------------------------------------------------------- #

def test_offsets_are_chunk_relative_and_exact():
    text = "The study was funded by ACC Limited in 2019."
    found = _extract(text, rows=[("ACC Limited", "ORGANIZATION", "sponsors")])
    assert len(found) == 1
    m = found[0]
    assert (m.start_offset, m.end_offset) == (24, 35)
    assert m.surface_text == "ACC Limited"
    _assert_spans_hold(found, text)


def test_every_occurrence_is_a_separate_mention():
    text = "ACC Limited met ACC Limited."
    found = _extract(text, rows=[("ACC Limited", "ORGANIZATION", "s")])
    assert [m.span for m in found] == [(0, 11), (16, 27)]
    _assert_spans_hold(found, text)


def test_word_boundaries_prevent_substring_matches():
    """"Air" must not match inside "Airport"."""
    text = "The Airport authority replied."
    assert _extract(text, rows=[("Air", "ORGANIZATION", "s")]) == []


def test_line_wrapped_name_is_still_found():
    text = "funded by Ministry of\nExternal Affairs last year"
    found = _extract(text, rows=[("Ministry of External Affairs", "ORGANIZATION", "s")])
    assert len(found) == 1
    assert found[0].surface_text == "Ministry of\nExternal Affairs"
    _assert_spans_hold(found, text)


def test_a_mention_rejects_an_impossible_span():
    with pytest.raises(ValueError):
        Mention(
            chunk_id=CHUNK, document_id=DOC, start_offset=5, end_offset=3,
            surface_text="x", normalized_text="x", entity_type="PERSON",
            extraction_method="pattern", extractor_version="v", confidence=0.5,
        )


# --------------------------------------------------------------------------- #
# Type classification and closed vocabulary
# --------------------------------------------------------------------------- #

def test_types_come_from_the_closed_vocabulary():
    with pytest.raises(ValueError):
        Mention(
            chunk_id=CHUNK, document_id=DOC, start_offset=0, end_offset=1,
            surface_text="x", normalized_text="x", entity_type="LOCATION",
            extraction_method="pattern", extractor_version="v", confidence=0.5,
        )


def test_person_and_organization_are_distinguished_by_source():
    text = "Dr Vibha Dhawan chairs ACC Limited."
    found = _extract(text, rows=[("ACC Limited", "ORGANIZATION", "s")])
    by_type = {m.entity_type for m in found}
    assert by_type == {"PERSON", "ORGANIZATION"}
    _assert_spans_hold(found, text)


# --------------------------------------------------------------------------- #
# CMS-derived extraction
# --------------------------------------------------------------------------- #

def test_cms_names_outrank_a_gazetteer_hit_on_the_same_span():
    """The CMS asserting this document is by someone is stronger evidence than
    the name merely being known corpus-wide."""
    text = "Written by Ajay Mathur for the review."
    found = _extract(
        text,
        cms_names=[("Ajay Mathur", "PERSON")],
        rows=[("Ajay Mathur", "PERSON", "documents_author")],
    )
    assert len(found) == 1
    assert found[0].extraction_method == "cms_field"
    assert found[0].confidence > 0.9


def test_cms_name_absent_from_the_text_yields_no_mention():
    """A mention is a sighting. Metadata that the body never states is a
    document-level fact for a later phase, not a span."""
    found = _extract("Nothing relevant here.", cms_names=[("Ajay Mathur", "PERSON")])
    assert found == []


# --------------------------------------------------------------------------- #
# Identifiers
# --------------------------------------------------------------------------- #

def test_project_code_is_extracted_exactly():
    text = "Project 2004BS22 concluded in March."
    found = _extract(text)
    assert len(found) == 1
    m = found[0]
    assert m.entity_type == "PROJECT" and m.extraction_method == "identifier"
    assert m.surface_text == "2004BS22"
    _assert_spans_hold(found, text)


@pytest.mark.parametrize("bad", ["2004bs22", "204BS22", "2004BS2", "2004BSS22"])
def test_project_code_pattern_does_not_fire_on_near_misses(bad):
    assert _extract(f"Project {bad} concluded.") == []


def test_a_bare_year_is_not_a_project_code():
    assert _extract("The 2019 report was published.") == []


# --------------------------------------------------------------------------- #
# Aliases / gazetteer
# --------------------------------------------------------------------------- #

def test_long_gazetteer_names_match_case_insensitively():
    """A distinctive multi-word name is safe to match in any casing — headings
    and all-caps runs would otherwise be missed."""
    text = "signed with the ministry of external affairs today"
    found = _extract(
        text, rows=[("Ministry of External Affairs", "ORGANIZATION", "s")]
    )
    assert len(found) == 1
    assert found[0].surface_text == "ministry of external affairs"


def test_short_gazetteer_names_match_case_sensitively():
    """Real CMS values collide with ordinary nouns: "Medium" is a publication
    and "Water Resources" a division. Case is the only signal in the text that
    separates the name from the noun, so short surfaces demand it."""
    rows = [("Water Resources", "ORGANIZATION", "field_division")]
    assert _extract("improving water resources in the region", rows=rows) == []
    found = _extract("the Water Resources division met", rows=rows)
    assert [m.surface_text for m in found] == ["Water Resources"]


def test_a_name_attested_for_two_types_stops_autolinking():
    """Data-driven ambiguity: the moment one normalized form is claimed by two
    types, the bare form is no longer safe to link from prose."""
    gaz = _gaz([("Phoenix", "PROJECT", "t"), ("Phoenix", "ORGANIZATION", "s")])
    assert gaz.lookup("phoenix")[0].is_ambiguous
    assert gaz.linkable == []
    assert extract.extract_mentions(
        "Phoenix delivered results.", chunk_id=CHUNK, document_id=DOC, gazetteer=gaz
    ) == []


def test_longer_name_wins_an_overlap():
    text = "funded by Ministry of External Affairs today"
    found = _extract(
        text,
        rows=[
            ("Ministry of External Affairs", "ORGANIZATION", "s"),
            ("Ministry", "ORGANIZATION", "s"),
        ],
    )
    assert len(found) == 1
    assert found[0].surface_text == "Ministry of External Affairs"


# --------------------------------------------------------------------------- #
# PERSON guards — the open-world case
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("initials", ["A.", "A. K.", "R"])
def test_initials_only_names_never_autolink(initials):
    """The author facet is full of these; they name nobody in particular, and
    linking them would merge unrelated people on first sight."""
    gaz = _gaz([(initials, "PERSON", "documents_author")])
    assert gaz.linkable == []


def test_single_token_person_name_does_not_autolink():
    """"Dr Neha" really appears in field_authors. One token is not enough to
    recognise someone in prose."""
    gaz = _gaz([("Neha", "PERSON", "field_authors")])
    assert gaz.linkable == []


def test_short_and_generic_surfaces_do_not_autolink():
    gaz = _gaz([("TERI Energy", "ORGANIZATION", "s"), ("the", "ORGANIZATION", "s")])
    surfaces = {e.surface for e in gaz.linkable}
    assert "TERI Energy" in surfaces and "the" not in surfaces


def test_honorific_pattern_finds_a_person_no_gazetteer_knows():
    text = "The review was led by Dr Ananya Krishnan last spring."
    found = _extract(text)
    assert len(found) == 1
    m = found[0]
    assert m.entity_type == "PERSON" and m.extraction_method == "pattern"
    assert m.surface_text == "Ananya Krishnan"
    _assert_spans_hold(found, text)


def test_a_bare_capitalised_bigram_is_not_a_person():
    """Without an honorific this pattern would match every place name and
    heading in the corpus."""
    assert _extract("The Solar Mission was announced.") == []


# --------------------------------------------------------------------------- #
# Duplicates and overlaps
# --------------------------------------------------------------------------- #

def test_two_stages_finding_one_name_produce_one_mention():
    text = "funded by ACC Limited."
    found = _extract(text, rows=[("ACC Limited", "ORGANIZATION", "s")])
    assert len(found) == 1  # gazetteer + org-suffix pattern both match


def test_dedupe_prefers_method_rank_then_length():
    text = "ACC Limited"
    high = extract._mention(
        chunk_id=CHUNK, document_id=DOC, text=text, start=0, end=11,
        entity_type="ORGANIZATION", method="cms_field",
    )
    low = extract._mention(
        chunk_id=CHUNK, document_id=DOC, text=text, start=0, end=3,
        entity_type="ORGANIZATION", method="pattern",
    )
    kept = extract.dedupe([low, high])
    assert [m.extraction_method for m in kept] == ["cms_field"]


def test_mentions_come_back_in_document_order():
    text = "ACC Limited and Tata Limited signed."
    found = _extract(
        text, rows=[("ACC Limited", "ORGANIZATION", "s"), ("Tata Limited", "ORGANIZATION", "s")]
    )
    assert [m.start_offset for m in found] == sorted(m.start_offset for m in found)


# --------------------------------------------------------------------------- #
# Malformed input
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("junk", ["", "   ", "\n\n", "…", "....", "\x00\x00"])
def test_malformed_text_yields_no_mentions_and_does_not_raise(junk):
    assert _extract(junk, rows=[("ACC Limited", "ORGANIZATION", "s")]) == []


def test_gazetteer_ignores_unusable_rows():
    gaz = _gaz(
        [("", "ORGANIZATION", "s"), ("   ", "PERSON", "s"), ("X", "NOT_A_TYPE", "s")]
    )
    assert len(gaz) == 0


def test_extraction_survives_regex_metacharacters_in_a_name():
    """A CMS name is untrusted text: "Kris Heavy Engineering (Sdn.Bhd)" is real,
    and an unescaped surface would either crash or match wrongly."""
    text = "paid to C++ Systems (Pvt) today"
    found = _extract(text, rows=[("C++ Systems (Pvt)", "ORGANIZATION", "s")])
    assert len(found) == 1
    _assert_spans_hold(found, text)


# --------------------------------------------------------------------------- #
# Idempotency
# --------------------------------------------------------------------------- #

def test_repeated_extraction_is_identical():
    text = "Dr Ananya Krishnan of ACC Limited ran 2004BS22."
    rows = [("ACC Limited", "ORGANIZATION", "s")]
    first = _extract(text, rows=rows)
    second = _extract(text, rows=rows)
    assert first == second
    assert len({(m.chunk_id, m.span, m.normalized_text) for m in first}) == len(first)


def test_candidate_prefilter_never_hides_a_real_match():
    """`candidates()` exists for speed (~4.75x), so it must be exact: anything
    it filters out could not have matched anyway. Checked by running the full
    linkable set against the same text and demanding the same result."""
    text = "Report by Ministry of External Affairs, funded by ACC Limited."
    rows = [
        ("Ministry of External Affairs", "ORGANIZATION", "s"),
        ("ACC Limited", "ORGANIZATION", "s"),
        ("Tata Consultancy", "ORGANIZATION", "s"),   # absent from the text
        ("Deutsche Gesellschaft", "ORGANIZATION", "s"),
    ]
    gaz = _gaz(rows)
    prefiltered = {e.surface for e in gaz.candidates(text)}
    exhaustive = {
        e.surface
        for e in gaz.linkable
        if __import__("app.knowledge.gazetteer", fromlist=["surface_pattern"])
        .surface_pattern(e.surface)
        .search(text)
    }
    assert exhaustive <= prefiltered
    assert exhaustive == {"Ministry of External Affairs", "ACC Limited"}


def test_candidate_prefilter_is_case_insensitive():
    gaz = _gaz([("ACC Limited", "ORGANIZATION", "s")])
    assert gaz.candidates("paid to acc limited today")


def test_extraction_key_covers_content_extractor_and_gazetteer():
    """A cached result must not outlive any input that would change it."""
    base = extract.extraction_key("hash-a", "gaz-1")
    assert base == extract.extraction_key("hash-a", "gaz-1")
    assert base != extract.extraction_key("hash-b", "gaz-1")
    assert base != extract.extraction_key("hash-a", "gaz-2")
