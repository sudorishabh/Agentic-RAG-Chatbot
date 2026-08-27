"""Link text and filenames harvested from a page body, decoded.

Both feed things that are read, not just stored. The anchor becomes the file's
description, which ``build_attachment_doc`` prefers over the node's title and
which citations display. The filename is scanned for years and edition spans by
``app.core.editions`` and ``app.ingestion.date_evidence``.

Left raw, each produces a specific wrong output seen on the live site:

* ``Receipts &amp; Payments`` as a document title — 20 of the 69 anchors on the
  FCRA Financials page carry an entity;
* ``Draft%20Agenda%20COP%2027.pdf`` offering the year 2027 to the year detector,
  because ``%20`` followed by ``27`` is four consecutive digits.

Neither had bitten yet: the sweep that produced the current corpus predates the
fix that made anchor capture work at all, so these values are not in the
catalogue. They would have arrived with the next re-crawl, which is why this
lands before any title re-sweep rather than after it.
"""

from __future__ import annotations

import pytest

from app.core.editions import normalise_edition
from app.ingestion.extractors.drupal_extractor import _extract_inbody_pdfs

SITE = "https://teriin.org"


def _harvest(html: str):
    """The in-body PDFs a body field yields, keyed by filename."""
    files = _extract_inbody_pdfs({"body": {"value": html}}, SITE, set())
    return {f.filename: f for f in files}


# --------------------------------------------------------------------------- #
# Anchor text
# --------------------------------------------------------------------------- #

def test_an_html_entity_in_link_text_is_decoded():
    files = _harvest(
        '<a href="/files/rp.pdf">Receipts &amp; Payments</a>')
    assert files["rp.pdf"].description == "Receipts & Payments"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Receipts &amp; Payments", "Receipts & Payments"),
        ("Officers&#8217; Framework", "Officers’ Framework"),
        ("Income &amp; Expenditure", "Income & Expenditure"),
        # `&nbsp;` decodes to  , which the whitespace collapse then turns
        # into an ordinary space. That is the wanted outcome: a
        # non-breaking space inside a title is invisible trouble for
        # matching and for display.
        ("A&nbsp;Report", "A Report"),
        ("Baseline&nbsp;Study&nbsp;2024", "Baseline Study 2024"),
        ("&quot;Quoted&quot; Title", '"Quoted" Title'),
    ],
)
def test_the_entity_forms_the_site_actually_uses(raw, expected):
    files = _harvest(f'<a href="/files/x.pdf">{raw}</a>')
    assert files["x.pdf"].description == expected


def test_plain_link_text_is_unchanged():
    files = _harvest('<a href="/files/y.pdf">Annual Report 2024-2025</a>')
    assert files["y.pdf"].description == "Annual Report 2024-2025"


def test_tags_inside_the_link_are_still_stripped():
    files = _harvest('<a href="/files/z.pdf"><strong>Balance</strong> &amp; Sheet</a>')
    assert files["z.pdf"].description == "Balance & Sheet"


def test_an_empty_anchor_still_yields_no_description():
    files = _harvest('<a href="/files/w.pdf"><img src="t.png"></a>')
    assert files["w.pdf"].description is None


# --------------------------------------------------------------------------- #
# Filenames
# --------------------------------------------------------------------------- #

def test_a_percent_encoded_filename_is_decoded():
    files = _harvest('<a href="/files/Policy%20Brief%20Biodiesel.pdf">Brief</a>')
    assert "Policy Brief Biodiesel.pdf" in files


def test_the_url_keeps_its_escapes_because_that_is_what_is_fetched():
    """Decoding the URL would break the download for any path that needs the
    escape. Only the metadata copy is decoded."""
    files = _harvest('<a href="/files/Policy%20Brief.pdf">Brief</a>')
    file = files["Policy Brief.pdf"]
    assert "%20" in file.url
    assert file.url.endswith("Policy%20Brief.pdf")


def test_decoding_removes_the_phantom_year():
    """``%20`` + ``27`` reads as 2027 to any four-digit year pattern. This is the
    real case: a COP-27 agenda that looked like a 2027 document."""
    encoded = "Draft%20Agenda%20COP%2027.pdf"
    assert "2027" in encoded
    files = _harvest(f'<a href="/files/{encoded}">Agenda</a>')
    name = next(iter(files))
    assert name == "Draft Agenda COP 27.pdf"
    assert "2027" not in name


def test_decoding_does_not_invent_an_edition():
    """``Net%20Zero%20Report%20_24-5-2024.pdf`` must not start reading as a
    fiscal span once the escapes are gone."""
    files = _harvest('<a href="/files/Net%20Zero%20_24-5-2024.pdf">x</a>')
    assert normalise_edition(next(iter(files))) is None


def test_a_real_edition_in_a_filename_still_reads():
    files = _harvest('<a href="/files/TERI-Annual-Report-2024-25.pdf">x</a>')
    assert normalise_edition(next(iter(files))) == "2024-25"


def test_an_unencoded_filename_is_unchanged():
    files = _harvest('<a href="/files/Auditor-Report-2024-25.pdf">x</a>')
    assert "Auditor-Report-2024-25.pdf" in files


def test_the_synthetic_id_still_derives_from_the_url_not_the_filename():
    """Identity has to follow the URL, or decoding would re-ingest every
    percent-encoded PDF as a new document."""
    import hashlib

    files = _harvest('<a href="/files/Policy%20Brief.pdf">Brief</a>')
    file = files["Policy Brief.pdf"]
    expected = hashlib.sha1(file.url.encode("utf-8")).hexdigest()
    assert file.uuid == f"inbody:{expected}"
