"""In-body PDF links must resolve to the URL a browser would fetch.

The regexes lift an href verbatim out of rich text, and two verbatim details
cost real documents:

* an HTML entity survived — ``Receipts_&amp;_Payments.pdf`` was fetched with the
  ``&amp;`` intact and 404'd every time. Fifteen attachment links carried one;
  every decoded URL answers 200;
* leading whitespace made ``href=" https://…"`` fail the ``startswith("http")``
  test, so an absolute URL was resolved as a relative one and concatenated onto
  the site base. The bare-URL regex matched the same link correctly, so the page
  emitted two documents with different synthetic uuids — one that worked and one
  that never could. Fifty-seven attachment links contain a space.

Both are identity bugs as much as fetch bugs: the uuid is a hash of the URL, so
a malformed URL is a *different document* that can never heal.

No network: `_extract_inbody_pdfs` is pure over its inputs.
"""

from __future__ import annotations

import hashlib

import pytest

from app.ingestion.extractors import drupal_extractor as de

SITE = "https://teriin.org"
FCRA = "https://teriin.org/sites/default/files/files/Receipts_&_Payments_22_23.pdf"
EXTERNAL = "https://www.ceew.in/sites/default/files/future.pdf"


def _extract(html: str, *, seen: set[str] | None = None) -> list:
    """Run the harvester over one rich-text field."""
    return de._extract_inbody_pdfs({"body": {"processed": html}}, SITE, seen or set())


def _urls(html: str, **kw) -> list[str]:
    return [f.url for f in _extract(html, **kw)]


def _uuid_for(url: str) -> str:
    return f"inbody:{hashlib.sha1(url.encode('utf-8')).hexdigest()}"


# --------------------------------------------------------------------------- #
# F4 — HTML entities.
# --------------------------------------------------------------------------- #

def test_an_ampersand_entity_is_decoded():
    """The live case: this URL 404s as extracted and answers 200 decoded."""
    html = (
        '<a href="https://teriin.org/sites/default/files/files/'
        'Receipts_&amp;_Payments_22_23.pdf">FCRA receipts</a>'
    )

    assert _urls(html) == [FCRA]


@pytest.mark.parametrize("entity", ["&amp;", "&#38;", "&#x26;"])
def test_every_spelling_of_an_ampersand_decodes(entity):
    html = f'<a href="{SITE}/files/a{entity}b.pdf">x</a>'

    assert _urls(html) == [f"{SITE}/files/a&b.pdf"]


def test_the_identity_is_derived_from_the_decoded_url():
    """The uuid is a hash of the URL, so an undecoded one is a different
    document — and one that can never be fetched."""
    html = f'<a href="{SITE}/files/a&amp;b.pdf">x</a>'

    (file,) = _extract(html)
    assert file.uuid == _uuid_for(f"{SITE}/files/a&b.pdf")
    assert "&amp;" not in file.uuid + file.url + file.filename


def test_the_filename_is_taken_from_the_decoded_url():
    html = f'<a href="{SITE}/files/Receipts_&amp;_Payments.pdf">x</a>'

    assert _extract(html)[0].filename == "Receipts_&_Payments.pdf"


# --------------------------------------------------------------------------- #
# F5 — whitespace, and the duplicate document it produced.
# --------------------------------------------------------------------------- #

def test_a_whitespace_padded_absolute_url_is_not_treated_as_relative(monkeypatch):
    monkeypatch.setattr(
        de, "get_settings", lambda: _settings(ingest_external=True)
    )
    html = f'<a href=" {EXTERNAL} ">Future of X</a>'

    assert _urls(html) == [EXTERNAL]


def test_the_padded_href_and_the_bare_url_collapse_to_one_document(monkeypatch):
    """Both regexes match this markup: the href with its space, and the bare URL
    without. Before normalisation that was two DrupalFiles with two uuids —
    ``https://teriin.org/ https://www.ceew.in/…`` alongside the real one."""
    monkeypatch.setattr(de, "get_settings", lambda: _settings(ingest_external=True))
    html = f'<a href=" {EXTERNAL} ">{EXTERNAL}</a>'

    files = _extract(html)

    assert [f.url for f in files] == [EXTERNAL]
    assert len({f.uuid for f in files}) == 1
    assert not any(" " in f.url for f in files)


def test_no_url_is_ever_emitted_with_the_site_base_glued_on(monkeypatch):
    monkeypatch.setattr(de, "get_settings", lambda: _settings(ingest_external=True))
    html = f'<a href="\n  {EXTERNAL}">x</a>'

    assert all(not u.startswith(f"{SITE}/https") for u in _urls(html))


# --------------------------------------------------------------------------- #
# Resolution of the other link shapes, which the string test got wrong.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "href,expected",
    [
        ("/sites/files/a.pdf", f"{SITE}/sites/files/a.pdf"),   # root-relative
        ("sites/files/a.pdf", f"{SITE}/sites/files/a.pdf"),    # relative
        ("//teriin.org/files/a.pdf", "https://teriin.org/files/a.pdf"),  # scheme-relative
        (f"{SITE}/files/a.pdf", f"{SITE}/files/a.pdf"),        # already absolute
    ],
)
def test_each_link_shape_resolves_the_way_a_browser_resolves_it(href, expected):
    assert _urls(f'<a href="{href}">x</a>') == [expected]


# --------------------------------------------------------------------------- #
# De-duplication happens on the normalised URL.
# --------------------------------------------------------------------------- #

def test_two_spellings_of_one_link_produce_one_document():
    html = (
        f'<a href="{SITE}/files/a&amp;b.pdf">escaped</a>'
        f'<a href=" {SITE}/files/a&b.pdf ">padded</a>'
    )

    assert _urls(html) == [f"{SITE}/files/a&b.pdf"]


def test_a_link_already_attached_as_a_file_is_not_harvested_again():
    """`seen_urls` carries the node's real file--file attachments, resolved the
    same way, so one PDF reached both ways is one document."""
    html = f'<a href="{SITE}/files/a&amp;b.pdf">x</a>'

    assert _urls(html, seen={f"{SITE}/files/a&b.pdf"}) == []


def test_the_emitted_order_does_not_vary_between_runs():
    html = "".join(f'<a href="{SITE}/files/{name}.pdf">x</a>' for name in "dcba")

    assert _urls(html) == sorted(_urls(html))


# --------------------------------------------------------------------------- #
# Behaviour that must not change.
# --------------------------------------------------------------------------- #

def _settings(*, ingest_external: bool):
    from types import SimpleNamespace

    return SimpleNamespace(drupal_ingest_external_pdfs=ingest_external)


def test_external_pdfs_are_still_excluded_by_default(monkeypatch):
    monkeypatch.setattr(de, "get_settings", lambda: _settings(ingest_external=False))

    assert _urls(f'<a href=" {EXTERNAL} ">x</a>') == []


def test_internal_pdfs_are_still_always_harvested(monkeypatch):
    monkeypatch.setattr(de, "get_settings", lambda: _settings(ingest_external=False))

    assert _urls(f'<a href="{SITE}/files/a.pdf">x</a>') == [f"{SITE}/files/a.pdf"]


def test_a_query_string_still_counts_as_a_pdf():
    html = f'<a href="{SITE}/files/a.pdf?download=1">x</a>'

    (file,) = [f for f in _extract(html) if f.url.endswith("?download=1")]
    assert file.filename == "a.pdf", "the query is not part of the filename"


def test_a_query_string_href_is_known_to_yield_both_forms():
    """Documented, not fixed. The two regexes disagree about where the URL ends
    — the href pattern keeps ``?download=1``, the bare-URL pattern stops at
    ``.pdf`` — so one link becomes two documents of the same file.

    Collapsing them would mean choosing a winner, and the wrong choice loses the
    file outright if only one form is served. Two documents of one PDF costs
    storage; zero documents costs an answer. Left as-is deliberately, and
    unchanged by the normalisation above: both forms were emitted before it too.
    """
    urls = _urls(f'<a href="{SITE}/files/a.pdf?download=1">x</a>')

    assert urls == [f"{SITE}/files/a.pdf", f"{SITE}/files/a.pdf?download=1"]


def test_non_pdf_links_are_still_ignored():
    assert _urls(f'<a href="{SITE}/files/a.docx">x</a>') == []


def test_the_same_url_always_gets_the_same_identity():
    first = _extract(f'<a href="{SITE}/files/a&amp;b.pdf">x</a>')[0]
    second = _extract(f'<a href="{SITE}/files/a&b.pdf">x</a>')[0]

    assert first.uuid == second.uuid == _uuid_for(f"{SITE}/files/a&b.pdf")


# --------------------------------------------------------------------------- #
# The JSON:API side resolves identically — minus entity decoding, which would
# rewrite a filename that genuinely contains those characters.
# --------------------------------------------------------------------------- #

def test_an_attachment_uri_resolves_the_same_way():
    assert de._normalize_link("/sites/files/a.pdf", SITE, from_html=False) == (
        f"{SITE}/sites/files/a.pdf"
    )


def test_a_json_value_is_not_entity_decoded():
    assert de._normalize_link("/files/a&amp;b.pdf", SITE, from_html=False) == (
        f"{SITE}/files/a&amp;b.pdf"
    )
