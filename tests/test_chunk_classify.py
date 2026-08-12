"""Tests for non-substantive section detection (TOC / references / glossary)."""

from __future__ import annotations

from app.ingestion.chunking.classifier import classify_section


def test_toc_detected():
    text = "\n".join([
        "Introduction ............................................. 7",
        "1 Background ............................................. 9",
        "2 Macroeconomic impacts ................................. 28",
        "3 Competitiveness ....................................... 32",
        "Bibliography ............................................ 45",
    ])
    assert classify_section(text) == "toc"


def test_references_detected():
    text = "\n".join([
        "ArcelorMittal. (2021). XCarb. Retrieved from https://corporate.arcelormittal.com/x",
        "Deloitte. (2021). Survey. Retrieved from https://www2.deloitte.com/global/x",
        "IEA. (2020). Iron and Steel Roadmap. Retrieved from https://iea.blob.core.windows.net/y",
        "MoS. (2021). Annual Report. Retrieved from https://steel.gov.in/z",
        "WSA. (2020). World Steel in Figures. Retrieved from https://www.worldsteel.org/a",
    ])
    assert classify_section(text) == "references"


def test_glossary_detected():
    text = "\n".join([
        "BEE – Bureau of Energy Efficiency",
        "BF-BOF – Blast Furnace Basic Oxygen Furnace",
        "CAGR – Compounded Annual Growth Rate",
        "CCUS – Carbon Capture, Use and Storage",
        "EAF – Electric Arc Furnace",
        "GDP – Gross Domestic Product",
    ])
    assert classify_section(text) == "glossary"


def test_url_sparse_bibliography_detected():
    # Tail of a bibliography: several entries have no URL, only "(YYYY)" citations.
    text = "\n".join([
        "World Bank. (2017). World Development Indicators.",
        "WSA. (2018). Steel Statistical Yearbook 2018.",
        "WSA. (2019). Towards a net-zero emissions steel industry.",
        "WSA. (2020a). World Steel in figures.",
        "WSA. (2020b). Steel Statistical Yearbook 2020 Concise Version.",
    ])
    assert classify_section(text) == "references"


def test_inline_prose_citations_not_flagged():
    # Body prose with inline "(Author, YYYY)" citations must stay searchable.
    text = (
        "India is the second-largest producer of steel (WSA, 2020a).\n"
        "Crude production rose to 1869 Mt (Hall, Spencer & Kumar, 2020) by 2019.\n"
        "The sector is highly cyclical and capital-intensive in nature.\n"
        "Investment depends on public and private players (NSP, 2017)."
    )
    assert classify_section(text) is None


def test_prose_not_flagged():
    text = (
        "The Indian steel sector is on the cusp of a significant transformation.\n"
        "Through scaling up renewable electricity and green hydrogen, the sector can "
        "shift away from imported fossil fuels.\n"
        "This report sets out that such a pathway is possible and desirable.\n"
        "Nonetheless there are significant risks of not rising to this challenge."
    )
    assert classify_section(text) is None


def test_short_text_not_flagged():
    assert classify_section("Bibliography ........ 45") is None  # < 4 lines


# --- bare-year bibliographies (the house style in this corpus) -------------- #
#
# Entries here read "Author A. 2005. Title." rather than "Author, A. (2005)".
# Only the parenthesised form was recognised, so real bibliographies scored zero
# citations and stayed searchable.

def test_bare_year_bibliography_detected():
    text = "\n".join([
        "Claude A (ed). 2002. Fish Curry and Rice: A Sourcebook on Goa. The Goa Foundation.",
        "Brenkert AL and Malone EL. 2005. Modelling Vulnerability and Resilience.",
        "Byravan Sujatha et al. 2010. Impact on Major Infrastructure and Ecosystems.",
        "Ministry of Environment and Forests. 2010. Climate Change and India.",
    ])
    assert classify_section(text) == "references"


def test_comma_delimited_year_bibliography_detected():
    text = "\n".join([
        "Millennium Development Goals India Report, 2015, Ministry of Statistics.",
        "The Millennium Development Goals Report, 2015, UNDP, India.",
        "National Voluntary Reviews at the High-level Political Forum, 2017.",
        "Transforming our World: The 2030 Agenda, 2015, United Nations.",
    ])
    assert classify_section(text) == "references"


def test_hard_wrapped_bibliography_still_detected():
    """PDF text wraps each entry over two or three lines whose continuations
    carry no citation marker; a per-line ratio sank below any usable gate."""
    text = "\n".join([
        "Claude A (ed). 2002. Fish Curry and Rice: A Sourcebook on Goa, Its Ecology",
        "and Other India Bookstore",
        "Brenkert AL and Malone EL. 2005. Modelling Vulnerability and Resilience to",
        "Climatic Change 72: 57-102, Doi: 10.1007/S10584-005-5930-3",
        "Byravan Sujatha et al. 2010. Impact on Major Infrastructure, Ecosystems,",
        "and Land Along the Tamil Nadu Coast.",
        "Ministry of Environment and Forests. 2010. Climate Change and India: A 4x4",
        "Assessment for 2030s.",
    ])
    assert classify_section(text) == "references"


# --- prose must stay searchable -------------------------------------------- #

def test_prose_mentioning_references_is_not_a_bibliography():
    text = (
        "The following references are discussed in the methodology section.\n"
        "References to previous studies are summarised before the analysis.\n"
        "Each reference was checked against the original source document.\n"
        "The bibliography appears at the end of this report."
    )
    assert classify_section(text) is None


def test_inline_bracket_citations_not_flagged():
    text = (
        "According to Smith et al. [12], water demand increased by 30 percent.\n"
        "Later work [13] confirmed the trend across three coastal districts.\n"
        "The methodology follows the approach described in [14] and [15].\n"
        "These findings informed the vulnerability assessment presented here."
    )
    assert classify_section(text) is None


def test_prose_carrying_years_not_flagged():
    """A year in running text is not a citation: 'in 2015, demand rose'."""
    text = (
        "Demand grew steadily in 2015, then fell sharply the following year.\n"
        "By 2019, the sector had recovered most of the lost capacity.\n"
        "Between 2010 and 2020, investment tripled across the region.\n"
        "The 2030 targets remain achievable under the current pathway."
    )
    assert classify_section(text) is None


def test_explanatory_footnotes_are_not_a_bibliography():
    """Footnotes are not a category here: they carry real content and must stay
    searchable. The classifier has no separate 'footnotes' class by design."""
    text = "\n".join([
        "1. 'Vikram' is the local name for a three-wheeled auto rickshaw in Alwar.",
        "2. 'Samman aur Seva', meaning Respect and Service, is the motto of the service.",
        "3. The fare is collected per passenger rather than per trip.",
        "4. Operators are organised into a registered cooperative society.",
    ])
    assert classify_section(text) is None


def test_content_decides_not_the_heading():
    """A chunk filed under a References heading whose body is real prose (a
    section whose own heading was missed) must stay searchable."""
    text = (
        "About TERI\n"
        "A dynamic and flexible organization with a global vision and a local focus.\n"
        "TERI was established in 1974, with an initial focus on documentation.\n"
        "Research activities were rooted in a conviction about efficient energy use.\n"
        "All activities move from local strategies to shaping global solutions."
    )
    assert classify_section(text) is None
