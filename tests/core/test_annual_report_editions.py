"""Resolving "the latest annual report" to one edition, and nothing else.

The failure this prevents: every edition of the series is an attachment on one
Drupal page, so all of them share that page's date. Relevance cannot separate
ten near-identical documents and recency cannot break a ten-way tie, so
"latest annual report" returned whichever chunk scored a hair higher — observed
as page 148 of the 2020-21 edition.

The other half of these tests is the more important half: **every question that
does not name one edition must leave retrieval byte-identical.** A scope applied
too eagerly hides the answer whenever it lives in a different edition, which is
a worse failure than the one being fixed.
"""

from __future__ import annotations

import pytest

from app.core.editions import normalise_edition
from app.retrieval import annual_report_editions as editions

PAGE = "https://teriin.org/annual-reports"

# The real series, as the catalogue holds it: title is the page's link text.
_SERIES_ROWS = [
    {"document_id": f"inbody:{year}", "title": f"Annual Report {year}-{year + 1}",
     "url": PAGE}
    for year in range(2015, 2025)
]


@pytest.fixture(autouse=True)
def _isolated_series(monkeypatch):
    """Serve a known series and never touch MySQL."""
    editions.reset_cache()
    monkeypatch.setattr(editions, "_read_series_rows", lambda: list(_SERIES_ROWS))
    yield
    editions.reset_cache()


# --------------------------------------------------------------------------- #
# The label rule
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Annual Report 2024-2025", "2024-25"),
        ("Annual Report 2024-25", "2024-25"),
        ("2020/21", "2020-21"),
        ("2024_25", "2024-25"),
        ("FY 20-21", "2020-21"),
        ("TAR_2015-16.pdf", "2015-16"),
        ("ANNUAL REPORT 2017 / 18", "2017-18"),
    ],
)
def test_every_spelling_of_an_edition_normalises_to_one_form(raw, expected):
    assert normalise_edition(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "2019-2024",       # a range of years, not a reporting period
        "Report 2 - 3",
        "September 2022",  # a month, not a span
        "2024",            # a bare year
        "01.07.2016 to 30.09.2016",  # a date range
        None,
        "",
    ],
)
def test_a_value_that_names_no_consecutive_span_is_not_invented_into_one(raw):
    assert normalise_edition(raw) is None


def test_canonical_labels_order_as_strings():
    """Why no sort key exists: fixed width and zero padded, so max() is newest."""
    labels = ["2015-16", "2024-25", "2019-20", "2009-10"]
    assert max(labels) == "2024-25"
    assert min(labels) == "2009-10"


# --------------------------------------------------------------------------- #
# Questions that must NOT be scoped — retrieval stays exactly as it was
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "question",
    [
        # About the series as a whole: a count, a list, a trend, a comparison.
        "how many annual reports do you have",
        "list all annual reports",
        "give me every annual report",
        "how has TERI's revenue changed across annual reports",
        "revenue trend in the annual reports",
        "annual report history",
        "compare the annual reports",
        "annual report figures year on year",
        # Asks for older editions without saying which.
        "older annual reports",
        "previous annual reports",
        "show me past annual reports",
        "earlier annual reports",
        "the annual report archive",
        # Mentions a series-like thing, but not this one.
        "what is TERI's latest report",
        "give me the most recent publication",
        "latest news on air quality",
        # Nothing to do with it at all.
        "who is the director general",
        "",
    ],
)
def test_a_question_about_the_whole_series_leaves_retrieval_untouched(question):
    resolution = editions.resolve(question)
    assert resolution is None
    assert editions.conditions_for(resolution) == []


def test_an_edition_the_series_does_not_hold_is_not_silently_substituted():
    assert editions.resolve("annual report 2031-32") is None


def test_a_year_range_in_the_question_is_not_read_as_an_edition():
    """"2019-2024" is a range. It must not resolve, and must not fall through to
    the newest edition either — the question is plainly about several."""
    assert editions.resolve("annual reports from 2019-2024") is None


# --------------------------------------------------------------------------- #
# The default: an unqualified "annual report" means the newest one
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "question",
    [
        "give me the annual report",
        "what does the annual report say about solar",
        "annual report highlights",
        "show me the annual report",
        "what is in the annual report",
        "annual report",
        "summarise the annual report",
    ],
)
def test_an_unqualified_question_defaults_to_the_newest_edition(question):
    resolution = editions.resolve(question)
    assert resolution is not None
    assert resolution.edition == "2024-25"
    assert resolution.kind == "default_latest"
    assert resolution.document_ids == ("inbody:2024",)


@pytest.mark.parametrize(
    "question",
    [
        "give me the latest annual report",
        "the newest annual report",
        "most recent annual report please",
        "what is the current annual report",
        "LATEST ANNUAL REPORT",
        "show me teri's latest annual report",
    ],
)
def test_asking_for_the_latest_also_resolves_to_the_newest_edition(question):
    """Same answer as the default, but logged distinctly so a trace shows
    whether the user asked or we assumed."""
    resolution = editions.resolve(question)
    assert resolution is not None
    assert resolution.edition == "2024-25"
    assert resolution.document_ids == ("inbody:2024",)
    assert resolution.kind == "latest"


def test_earliest_resolves_to_the_oldest_edition():
    resolution = editions.resolve("the first annual report")
    assert resolution is not None
    assert resolution.edition == "2015-16"
    assert resolution.kind == "earliest"


@pytest.mark.parametrize(
    "question,expected",
    [
        ("annual report 2022-23", "2022-23"),
        ("annual report for 2019-20", "2019-20"),
        ("the 2016-2017 annual report", "2016-17"),
        ("annual report 2020/21", "2020-21"),
    ],
)
def test_a_named_edition_is_used_as_given(question, expected):
    resolution = editions.resolve(question)
    assert resolution is not None
    assert resolution.edition == expected
    assert resolution.kind == "named"


def test_a_named_edition_beats_a_superlative():
    """"latest" is a hint; a named edition is the user's actual constraint."""
    resolution = editions.resolve("the latest annual report 2018-19")
    assert resolution is not None
    assert resolution.edition == "2018-19"
    assert resolution.kind == "named"


def test_a_named_edition_beats_a_whole_series_cue():
    """"compare X with Y" names both, so it scopes to both rather than opening
    the whole series."""
    resolution = editions.resolve("compare the 2019-20 and 2024-25 annual reports")
    assert resolution is not None
    assert resolution.edition == "2019-20+2024-25"
    assert resolution.kind == "named"
    assert resolution.document_ids == ("inbody:2019", "inbody:2024")


def test_the_oldest_edition_is_still_reachable_by_name():
    resolution = editions.resolve("the oldest annual report")
    assert resolution is not None
    assert resolution.edition == "2015-16"
    assert resolution.kind == "earliest"


@pytest.mark.parametrize(
    "question,expected",
    [
        ("annual report 2018", "2018-19"),
        ("2018 annual report", "2018-19"),
        ("annual report for 2020", "2020-21"),
        ("annual report of 2016", "2016-17"),
    ],
)
def test_a_bare_year_against_the_series_name_selects_that_edition(question, expected):
    resolution = editions.resolve(question)
    assert resolution is not None
    assert resolution.edition == expected
    assert resolution.kind == "named"


@pytest.mark.parametrize(
    "question",
    [
        "what does the annual report say about the 2015 Paris Agreement",
        "annual report coverage of the 2016 monsoon",
        "does the annual report mention targets for 2030",
    ],
)
def test_a_year_elsewhere_in_the_sentence_is_not_read_as_an_edition(question):
    """The riskiest false positive: a year that is part of the subject. These
    fall through to the default rather than answering out of a 2015 edition."""
    resolution = editions.resolve(question)
    assert resolution is not None
    assert resolution.kind == "default_latest"
    assert resolution.edition == "2024-25"


# --------------------------------------------------------------------------- #
# The filter it produces
# --------------------------------------------------------------------------- #

def test_the_condition_scopes_by_document_id_not_by_label():
    """Label spellings differ between stores; ids do not."""
    resolution = editions.resolve("latest annual report")
    conditions = editions.conditions_for(resolution)
    assert len(conditions) == 1
    assert conditions[0].key == "document_id"
    assert conditions[0].match.any == ["inbody:2024"]


def test_the_condition_is_not_a_date_scope_so_a_miss_can_be_relaxed_away():
    """`retriever.retrieve` drops non-date filters and retries when a filter
    matches nothing. That is what stops this from ever starving retrieval."""
    from app.retrieval.understanding.filters import date_conditions

    conditions = editions.conditions_for(editions.resolve("latest annual report"))
    assert date_conditions(conditions) == []


def test_the_description_names_the_choice_and_the_series():
    resolution = editions.resolve("latest annual report")
    described = resolution.describe()
    assert "latest -> 2024-25" in described
    assert "2015-16" in described


# --------------------------------------------------------------------------- #
# Failure containment
# --------------------------------------------------------------------------- #

def test_an_unreadable_catalogue_resolves_nothing_rather_than_raising(monkeypatch):
    def _boom():
        raise RuntimeError("MySQL is down")

    monkeypatch.setattr(editions, "_read_series_rows", _boom)
    editions.reset_cache()
    assert editions.resolve("latest annual report") is None


def test_an_empty_catalogue_resolves_nothing(monkeypatch):
    monkeypatch.setattr(editions, "_read_series_rows", lambda: [])
    editions.reset_cache()
    assert editions.resolve("latest annual report") is None


def test_two_competing_series_resolve_nothing(monkeypatch):
    """A tie means no way to tell which series the question means."""
    other = [
        {"document_id": f"other:{y}", "title": f"Annual Report {y}-{y + 1}",
         "url": "https://teriin.org/some-project"}
        for y in range(2015, 2025)
    ]
    monkeypatch.setattr(
        editions, "_read_series_rows", lambda: list(_SERIES_ROWS) + other
    )
    editions.reset_cache()
    assert editions.resolve("latest annual report") is None


def test_a_smaller_lookalike_series_does_not_disturb_the_real_one(monkeypatch):
    """The corpus really does hold "Component 1 - Annual Report - ..." documents;
    a page with fewer editions must not win."""
    stray = [{
        "document_id": "stray:1",
        "title": "Annual Report 2011-2012",
        "url": "https://teriin.org/project/flow",
    }]
    monkeypatch.setattr(
        editions, "_read_series_rows", lambda: list(_SERIES_ROWS) + stray
    )
    editions.reset_cache()
    resolution = editions.resolve("latest annual report")
    assert resolution is not None
    assert resolution.edition == "2024-25"
    assert "2011-12" not in resolution.available


def test_a_title_naming_no_edition_is_ignored(monkeypatch):
    """The parent page is titled "Annual Reports" — plural, no span."""
    monkeypatch.setattr(
        editions, "_read_series_rows",
        lambda: list(_SERIES_ROWS) + [
            {"document_id": "page", "title": "Annual Reports", "url": PAGE}],
    )
    editions.reset_cache()
    resolution = editions.resolve("latest annual report")
    assert resolution is not None
    assert resolution.document_ids == ("inbody:2024",)


def test_the_series_is_read_once_and_cached(monkeypatch):
    calls = []

    def _counted():
        calls.append(1)
        return list(_SERIES_ROWS)

    monkeypatch.setattr(editions, "_read_series_rows", _counted)
    editions.reset_cache()
    editions.resolve("latest annual report")
    editions.resolve("newest annual report")
    editions.resolve("annual report 2019-20")
    assert len(calls) == 1
