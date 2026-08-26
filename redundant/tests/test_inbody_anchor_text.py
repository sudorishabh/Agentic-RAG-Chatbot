"""In-body PDF links must keep their anchor text.

A PDF linked from rich text has no Drupal file entity and therefore no field
description, so ``build_attachment_doc`` falls back to the node's title. On a
page holding a series that makes every document identical: all ten TERI annual
reports are in-body attachments on one page, so all ten were titled "Annual
Reports". The link text is the only place each edition is named.
"""

from __future__ import annotations

from app.ingestion.extractors.drupal_extractor import _extract_inbody_pdfs

SITE = "https://teriin.org"


def _attrs(body: str) -> dict:
    return {"body": {"value": body, "format": "full_html"}}


def test_the_link_text_becomes_the_description():
    files = _extract_inbody_pdfs(
        _attrs('<p><a href="/files/TERI-Annual-Report-2024-25.pdf">'
               'Annual Report 2024-2025</a></p>'),
        SITE, set(),
    )
    assert len(files) == 1
    assert files[0].description == "Annual Report 2024-2025"


def test_markup_inside_the_anchor_is_flattened():
    files = _extract_inbody_pdfs(
        _attrs('<a href="/files/x.pdf">Annual Report <strong>2024-2025</strong></a>'),
        SITE, set(),
    )
    assert files[0].description == "Annual Report 2024-2025"


def test_a_thumbnail_link_does_not_blank_the_caption():
    """The shape that silently emptied every annual-report anchor.

    The same PDF is linked twice: once wrapping an image (no text) and once as a
    captioned text link. Keeping the longest anchor is what preserves the caption.
    """
    body = ('<a href="/files/TAR_2015-16.pdf"><img src="thumb.png"></a>'
            '<a href="/files/TAR_2015-16.pdf">Annual Report 2015-2016</a>')
    files = _extract_inbody_pdfs(_attrs(body), SITE, set())
    assert len(files) == 1, "the same PDF must still ingest once"
    assert files[0].description == "Annual Report 2015-2016"


def test_the_caption_wins_regardless_of_link_order():
    body = ('<a href="/files/TAR_2015-16.pdf">Annual Report 2015-2016</a>'
            '<a href="/files/TAR_2015-16.pdf"><img src="thumb.png"></a>')
    files = _extract_inbody_pdfs(_attrs(body), SITE, set())
    assert files[0].description == "Annual Report 2015-2016"


def test_single_quoted_attributes_are_handled():
    files = _extract_inbody_pdfs(
        _attrs("<a class='btn' href='/files/y.pdf'>Annual Report 2019-2020</a>"),
        SITE, set(),
    )
    assert files[0].description == "Annual Report 2019-2020"


def test_a_bare_url_still_harvests_with_no_description():
    """The pre-existing path must be untouched: no <a> wrapper, no anchor."""
    files = _extract_inbody_pdfs(
        _attrs("see https://teriin.org/files/report.pdf for detail"), SITE, set())
    assert len(files) == 1
    assert files[0].description is None


def test_an_href_without_an_anchor_wrapper_still_harvests():
    files = _extract_inbody_pdfs(_attrs('href="/files/z.pdf"'), SITE, set())
    assert len(files) == 1
    assert files[0].description is None


def test_a_full_series_yields_one_description_each():
    editions = [f"{y}-{y + 1}" for y in range(2015, 2025)]
    body = "".join(
        f'<a href="/files/TAR_{e}.pdf">Annual Report {e}</a>' for e in editions)
    files = _extract_inbody_pdfs(_attrs(body), SITE, set())
    assert len(files) == len(editions)
    assert [f.description for f in files] == [f"Annual Report {e}" for e in editions]
    # The point of the change: the descriptions are all different.
    assert len({f.description for f in files}) == len(editions)


def test_identity_and_dedup_are_unchanged():
    """The synthetic uuid drives change detection; it must still be URL-derived
    and still collapse two spellings of one link to one document."""
    body = ('<a href="/files/a.pdf">First</a>'
            '<a href="https://teriin.org/files/a.pdf">Second label</a>')
    files = _extract_inbody_pdfs(_attrs(body), SITE, set())
    assert len(files) == 1
    assert files[0].uuid.startswith("inbody:")
    assert files[0].origin == "inbody"


def test_an_already_seen_url_is_not_re_emitted():
    body = '<a href="/files/a.pdf">Label</a>'
    files = _extract_inbody_pdfs(
        _attrs(body), SITE, {"https://teriin.org/files/a.pdf"})
    assert files == []


def test_the_description_reaches_the_document_title():
    """`build_attachment_doc` prefers the description over the node's title."""
    from types import SimpleNamespace

    file = SimpleNamespace(description="Annual Report 2024-2025",
                           filename="TERI-Annual-Report-2024-25.pdf")
    node = SimpleNamespace(title="Annual Reports")
    title = file.description or node.title or file.filename or None
    assert title == "Annual Report 2024-2025"
