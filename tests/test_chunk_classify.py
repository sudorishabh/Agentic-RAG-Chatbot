"""Tests for non-substantive section detection (TOC / references / glossary)."""

from __future__ import annotations

from app.ingestion.chunker import _classify_section


def test_toc_detected():
    text = "\n".join([
        "Introduction ............................................. 7",
        "1 Background ............................................. 9",
        "2 Macroeconomic impacts ................................. 28",
        "3 Competitiveness ....................................... 32",
        "Bibliography ............................................ 45",
    ])
    assert _classify_section(text) == "toc"


def test_references_detected():
    text = "\n".join([
        "ArcelorMittal. (2021). XCarb. Retrieved from https://corporate.arcelormittal.com/x",
        "Deloitte. (2021). Survey. Retrieved from https://www2.deloitte.com/global/x",
        "IEA. (2020). Iron and Steel Roadmap. Retrieved from https://iea.blob.core.windows.net/y",
        "MoS. (2021). Annual Report. Retrieved from https://steel.gov.in/z",
        "WSA. (2020). World Steel in Figures. Retrieved from https://www.worldsteel.org/a",
    ])
    assert _classify_section(text) == "references"


def test_glossary_detected():
    text = "\n".join([
        "BEE – Bureau of Energy Efficiency",
        "BF-BOF – Blast Furnace Basic Oxygen Furnace",
        "CAGR – Compounded Annual Growth Rate",
        "CCUS – Carbon Capture, Use and Storage",
        "EAF – Electric Arc Furnace",
        "GDP – Gross Domestic Product",
    ])
    assert _classify_section(text) == "glossary"


def test_url_sparse_bibliography_detected():
    # Tail of a bibliography: several entries have no URL, only "(YYYY)" citations.
    text = "\n".join([
        "World Bank. (2017). World Development Indicators.",
        "WSA. (2018). Steel Statistical Yearbook 2018.",
        "WSA. (2019). Towards a net-zero emissions steel industry.",
        "WSA. (2020a). World Steel in figures.",
        "WSA. (2020b). Steel Statistical Yearbook 2020 Concise Version.",
    ])
    assert _classify_section(text) == "references"


def test_inline_prose_citations_not_flagged():
    # Body prose with inline "(Author, YYYY)" citations must stay searchable.
    text = (
        "India is the second-largest producer of steel (WSA, 2020a).\n"
        "Crude production rose to 1869 Mt (Hall, Spencer & Kumar, 2020) by 2019.\n"
        "The sector is highly cyclical and capital-intensive in nature.\n"
        "Investment depends on public and private players (NSP, 2017)."
    )
    assert _classify_section(text) is None


def test_prose_not_flagged():
    text = (
        "The Indian steel sector is on the cusp of a significant transformation.\n"
        "Through scaling up renewable electricity and green hydrogen, the sector can "
        "shift away from imported fossil fuels.\n"
        "This report sets out that such a pathway is possible and desirable.\n"
        "Nonetheless there are significant risks of not rising to this challenge."
    )
    assert _classify_section(text) is None


def test_short_text_not_flagged():
    assert _classify_section("Bibliography ........ 45") is None  # < 4 lines
