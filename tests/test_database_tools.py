"""Phase 2: the catalog tools. state.* and the name vocabularies are stubbed; no DB."""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.retrieval.structured import tools
from app.retrieval.structured.types import RecordFilters


def _rec(document_id="d1", title="A", url="http://a", published_at="2024-05-01T00:00:00",
         bundle="news"):
    return StateRecord(
        document_id=document_id, source_type="website", source_key="k",
        fingerprint="f", title=title, url=url, published_at=published_at, bundle=bundle,
    )


def _theme_vocab(*names, group="main"):
    """Vocabulary rows. Pass ("Name", "other") tuples to vary the group."""
    rows = []
    for entry in names:
        name, grp = entry if isinstance(entry, tuple) else (entry, group)
        rows.append({"theme": name, "theme_type": "primary", "parent": None,
                     "theme_group": grp, "documents": 3})
    return rows


@pytest.fixture(autouse=True)
def _offline_catalog(monkeypatch):
    """Themes/tags/authors come from the catalog by name; stub them empty so no
    test reaches MySQL, and let individual cases override."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: [])
    monkeypatch.setattr("app.catalog.queries.find_tag", lambda name: None)
    monkeypatch.setattr("app.catalog.queries.distinct_authors", lambda **kw: [])
    from app.retrieval.structured import resolve

    resolve.reload_authors()
    yield
    resolve.reload_authors()


@pytest.fixture
def resolve_theme_ok(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: _theme_vocab("Climate", "Climate Change", "Environment"),
    )


@pytest.fixture
def resolve_tag_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.find_tag",
                        lambda name: "policy" if name.lower() == "policy" else None)


# --------------------------------------------------------------------------- #
# _scope_phrase / _applied_filters — the shared "state the interpretation"
# helpers used by count_records / list_records / aggregate_records.
# --------------------------------------------------------------------------- #

def test_scope_phrase_empty_when_nothing_set():
    assert tools._scope_phrase(RecordFilters()) == ""


def test_scope_phrase_names_author_theme_tag_and_period_in_order():
    filters = RecordFilters(
        author="Rishabh Negi", theme="Climate Change", tag="policy",
        date_from="2024-01-01", date_to="2025-01-01",
    )
    assert tools._scope_phrase(filters) == (
        " by Rishabh Negi on 'Climate Change' tagged 'policy' in 2024"
    )


def test_scope_phrase_author_only():
    assert tools._scope_phrase(RecordFilters(author="Rishabh Negi")) == " by Rishabh Negi"


def test_scope_phrase_names_the_title_filter():
    assert tools._scope_phrase(RecordFilters(title_contains="Solar")) == (
        " with 'Solar' in the title"
    )


def test_scope_phrase_covers_every_filter_that_applied_filters_echoes():
    """The prose and the structured echo must name the same filter set — a
    filter stated in one but not the other is either an unexplained number or
    an unexplained key. Dates are compared as a period rather than verbatim:
    a whole calendar year deliberately reads "in 2024", not its raw bounds."""
    filters = RecordFilters(
        author="Rishabh Negi", theme="Climate Change", tag="policy",
        title_contains="Solar", date_from="2024-03-15", date_to="2024-06-01",
    )
    phrase = tools._scope_phrase(filters)
    applied = tools._applied_filters(None, filters)
    assert set(applied) == {
        "author", "theme", "tag", "title_contains", "date_from", "date_to",
    }
    for value in applied.values():
        assert value in phrase, f"{value!r} echoed in data but absent from the prose"


def test_scope_phrase_states_a_collapsed_calendar_year():
    filters = RecordFilters(date_from="2024-01-01", date_to="2025-01-01")
    assert tools._scope_phrase(filters) == " in 2024"
    assert set(tools._applied_filters(None, filters)) == {"date_from", "date_to"}


def test_applied_filters_omits_unset_values():
    assert tools._applied_filters("news", RecordFilters()) == {"entity": "news"}
    assert tools._applied_filters(None, RecordFilters()) == {}


def test_applied_filters_includes_every_set_value():
    filters = RecordFilters(
        author="Rishabh Negi", theme="Climate Change", tag="policy",
        date_from="2024-01-01", date_to="2025-01-01",
    )
    assert tools._applied_filters("events", filters) == {
        "entity": "events", "author": "Rishabh Negi", "theme": "Climate Change",
        "tag": "policy", "date_from": "2024-01-01", "date_to": "2025-01-01",
    }


# --------------------------------------------------------------------------- #
# count_records
# --------------------------------------------------------------------------- #

def test_count_records_renders_and_passes_scope(monkeypatch, resolve_theme_ok):
    seen = {}

    def fake_count(**kw):
        seen.update(kw)
        return 3

    monkeypatch.setattr("app.catalog.queries.count_documents", fake_count)
    r = tools.count_records(
        "news", RecordFilters(theme="Climate", date_from="2024-01-01", date_to="2025-01-01")
    )
    assert r.ok
    assert r.data == {
        "count": 3,
        "applied": {"entity": "news", "theme": "Climate",
                   "date_from": "2024-01-01", "date_to": "2025-01-01"},
    }
    assert r.rendered == "There are 3 news items on 'Climate' in 2024 matching your query."
    assert seen["bundle"] == "news"
    assert seen["source_type"] == "website" and seen["entity_type"] == "node"
    assert seen["theme"] == "Climate"


def test_count_records_unknown_entity_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 0)
    r = tools.count_records("tenders", RecordFilters())
    assert r.ok is False and "unknown entity" in (r.error or "")


def test_count_records_unresolved_theme_still_counts_via_name_fallback(monkeypatch):
    """A theme name the vocabulary could not place still filters — matching being
    unsure is not proof of absence, so the query runs and may well find rows."""
    seen = {}

    def fake_count(**kw):
        seen.update(kw)
        return 99

    monkeypatch.setattr("app.catalog.queries.count_documents", fake_count)
    r = tools.count_records("news", RecordFilters(theme="Environment"))
    assert r.ok is True
    assert seen["theme"] == "Environment"  # filtered by name
    assert r.data["count"] == 99


def test_count_records_unresolved_theme_with_no_rows_is_a_terminal_miss(monkeypatch):
    """Only when the fallback also finds nothing are "unknown theme" and
    "genuinely no documents" indistinguishable — then the miss is the honest
    answer, not a bare 0."""
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 0)
    r = tools.count_records("news", RecordFilters(theme="Quantum Beekeeping"))
    assert r.ok is False and r.error_kind == "unresolved"
    assert r.rendered == "No theme matching 'Quantum Beekeeping' found."


def test_count_records_resolved_theme_with_no_rows_is_an_honest_zero(monkeypatch):
    """A theme that DID resolve and matched nothing is a real zero — never
    relabelled as a miss."""
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: _theme_vocab("Climate Change"),
    )
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 0)
    r = tools.count_records("news", RecordFilters(theme="Climate Change"))
    assert r.ok is True and r.data["count"] == 0
    assert r.rendered == "There are 0 news items on 'Climate Change' matching your query."


def test_count_records_passes_tag_scope(monkeypatch, resolve_tag_ok):
    seen = {}

    def fake_count(**kw):
        seen.update(kw)
        return 4

    monkeypatch.setattr("app.catalog.queries.count_documents", fake_count)
    r = tools.count_records("news", RecordFilters(tag="policy"))
    assert r.ok
    assert r.data == {"count": 4, "applied": {"entity": "news", "tag": "policy"}}
    assert r.rendered == "There are 4 news items tagged 'policy' matching your query."
    assert seen["tag"] == "policy"


def test_count_records_unmatched_tag_with_no_rows_is_a_terminal_miss(monkeypatch):
    """Tags are matched exactly, so an unmatched name finds nothing — and an
    empty result on an unmatched name is the honest miss."""
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 0)
    r = tools.count_records("news", RecordFilters(tag="nonexistent"))
    assert r.ok is False and r.error_kind == "unresolved"
    assert r.rendered == "No tag matching 'nonexistent' found."


def test_count_records_singular_verb(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 1)
    r = tools.count_records("report", RecordFilters())
    assert r.rendered == "There is 1 report matching your query."


def test_count_records_bare_total(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 123)
    r = tools.count_records(None, RecordFilters())
    assert r.rendered == "There are 123 items matching your query."


def test_count_records_date_range_render(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 2)
    r = tools.count_records(
        None, RecordFilters(date_from="2024-03-15", date_to="2024-03-16")
    )
    assert r.rendered == (
        "There are 2 items between 2024-03-15 and 2024-03-16 matching your query."
    )


def test_count_records_applies_the_title_filter(monkeypatch):
    """count_documents did not accept title_contains at all, so a title-filtered
    count silently returned the whole corpus while list_records filtered
    correctly — the two disagreed on the same query."""
    seen = {}
    monkeypatch.setattr(
        "app.catalog.queries.count_documents", lambda **kw: seen.update(kw) or 3
    )
    r = tools.count_records("report", RecordFilters(title_contains="Solar"))
    assert seen["title_contains"] == "Solar"
    assert r.rendered == "There are 3 reports with 'Solar' in the title matching your query."


def test_count_and_list_pass_the_same_filter_set(monkeypatch):
    """Regression guard: whatever narrows a listing must narrow its count too."""
    counted, listed = {}, {}
    monkeypatch.setattr(
        "app.catalog.queries.count_documents", lambda **kw: counted.update(kw) or 1
    )
    monkeypatch.setattr(
        "app.catalog.queries.list_documents", lambda **kw: listed.update(kw) or [_rec()]
    )
    filters = RecordFilters(author="Sharma", title_contains="Solar",
                            date_from="2024-01-01", date_to="2025-01-01")
    tools.count_records("report", filters)
    tools.list_records("report", filters)
    # list_documents additionally takes paging keys; every filter must match.
    for key, value in counted.items():
        assert listed[key] == value, f"{key} differs between count and list"


def test_count_records_names_author_in_rendered_answer(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 21)
    r = tools.count_records(None, RecordFilters(author="Dr Suneel Pandey"))
    assert r.rendered == "There are 21 items by Dr Suneel Pandey matching your query."
    assert r.data["applied"] == {"author": "Dr Suneel Pandey"}


def test_count_records_combines_author_theme_tag_and_period(monkeypatch, resolve_theme_ok):
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary",
                        lambda name, vocabulary=None: [{"term_uuid": "u1", "name": name}])
    monkeypatch.setattr("app.catalog.queries.count_documents", lambda **k: 3)
    r = tools.count_records(
        "news",
        RecordFilters(author="Rishabh Negi", theme="Climate Change", tag="policy",
                     date_from="2024-01-01", date_to="2025-01-01"),
    )
    assert r.rendered == (
        "There are 3 news items by Rishabh Negi on 'Climate Change' tagged 'policy' "
        "in 2024 matching your query."
    )
    assert r.data["applied"] == {
        "entity": "news", "author": "Rishabh Negi", "theme": "Climate Change",
        "tag": "policy", "date_from": "2024-01-01", "date_to": "2025-01-01",
    }


def test_count_records_db_error_is_not_ok(monkeypatch):
    def boom(**k):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.catalog.queries.count_documents", boom)
    assert tools.count_records("news", RecordFilters()).ok is False


# --------------------------------------------------------------------------- #
# list_records
# --------------------------------------------------------------------------- #

def test_list_records_plain(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters())
    assert r.ok
    assert r.data["records"][0]["document_id"] == "d1"
    assert r.citations[0]["title"] == "A"
    assert r.rendered == "Here is what I found:\n- A (http://a)"
    assert r.data["applied"] == {"entity": "news"}


def test_list_records_applied_names_author(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters(author="Rishabh Negi"))
    assert r.data["applied"] == {"entity": "news", "author": "Rishabh Negi"}
    # the record list itself is the evidence; the prose stays unchanged
    assert r.rendered == "Here is what I found:\n- A (http://a)"


def test_list_records_table(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters(), output_format="table")
    assert "| Title | Published | Type |" in r.rendered


def test_list_records_empty_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [])
    r = tools.list_records("news", RecordFilters())
    assert r.ok is False


def test_list_records_passes_tag_scope(monkeypatch, resolve_tag_ok):
    seen = {}

    def fake_list(**kw):
        seen.update(kw)
        return [_rec()]

    monkeypatch.setattr("app.catalog.queries.list_documents", fake_list)
    r = tools.list_records("news", RecordFilters(tag="policy"))
    assert r.ok
    assert seen["tag"] == "policy"


def test_list_records_unmatched_tag_with_no_rows_is_a_terminal_miss(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [])
    r = tools.list_records("news", RecordFilters(tag="nonexistent"))
    assert r.ok is False and r.error_kind == "unresolved"


def test_list_records_passes_offset(monkeypatch):
    seen = {}

    def fake_list(**kw):
        seen.update(kw)
        return [_rec()]

    monkeypatch.setattr("app.catalog.queries.list_documents", fake_list)
    tools.list_records("news", RecordFilters(), limit=5, offset=15)
    assert seen["limit"] == 5 and seen["offset"] == 15


def test_list_records_projects_requested_fields(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters(), fields=["title", "url"])
    assert r.data["records"] == [{"title": "A", "url": "http://a"}]
    # rendered stays the normal human-readable answer, unaffected by fields
    assert r.rendered == "Here is what I found:\n- A (http://a)"


def test_list_records_unknown_fields_do_not_empty_the_records(monkeypatch):
    """An LLM-supplied field name that does not exist should cost the caller a
    few extra keys, not silently blank every record."""
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters(), fields=["nope", "alsonope"])
    assert r.data["records"][0]["title"] == "A"  # full record, not {}


def test_list_records_mixed_known_and_unknown_fields_keeps_the_known_ones(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters(), fields=["title", "nope"])
    assert r.data["records"] == [{"title": "A"}]


def test_list_records_without_fields_keeps_full_metadata(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.list_records("news", RecordFilters())
    assert set(r.data["records"][0]) == {
        "document_id", "title", "url", "published_at", "bundle",
    }


def test_list_records_timeline_groups_by_year(monkeypatch):
    recs = [
        _rec("d1", "Old", "http://old", "2023-11-02T00:00:00"),
        _rec("d2", "New", "http://new", "2024-05-20T00:00:00"),
        _rec("d3", "NoDate", None, None),
    ]
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: recs)
    r = tools.list_records("news", RecordFilters(), output_format="timeline")
    a = r.rendered
    assert a.index("2024:") < a.index("2023:") < a.index("Undated:")
    assert "- 2024-05: New (http://new)" in a
    assert "- n.d.: NoDate" in a
    # citations follow the rendered (newest-first) order
    assert [c["title"] for c in r.citations] == ["New", "Old", "NoDate"]


# --------------------------------------------------------------------------- #
# lookup_record
# --------------------------------------------------------------------------- #

def test_lookup_record_chains_on_content_question(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.lookup_record(
        "report", "Solar Report", RecordFilters(),
        question="what does the Solar Report say about capacity?",
    )
    assert r.data["chain_document_id"] == "d1"
    assert r.ok  # also renders the list
    # inherited from list_records's data via the {**result.data, ...} spread
    assert r.data["applied"] == {"entity": "report", "title_contains": "Solar Report"}


def test_lookup_record_no_chain_on_browse(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.list_documents", lambda **k: [_rec()])
    r = tools.lookup_record(
        "report", "Solar Report", RecordFilters(), question="show the Solar Report",
    )
    assert r.data["chain_document_id"] is None


def test_lookup_record_no_chain_when_multiple_match(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.list_documents",
        lambda **k: [_rec("d1"), _rec("d2")],
    )
    r = tools.lookup_record(
        "report", "Report", RecordFilters(), question="what does the report say?",
    )
    assert r.data["chain_document_id"] is None  # ambiguous -> no chain


# --------------------------------------------------------------------------- #
# aggregate_records
# --------------------------------------------------------------------------- #

def test_list_themes_renders_vocabulary(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: [
            {"theme": "Climate Change", "theme_type": "primary", "parent": None, "theme_group": "main", "documents": 3},
            {"theme": "Energy", "theme_type": "primary", "parent": None, "theme_group": "main", "documents": 3},
        ],
    )
    r = tools.list_themes()
    assert r.ok
    assert r.data["themes"] == ["Climate Change", "Energy"]
    assert "Climate Change" in r.rendered and "Energy" in r.rendered


def test_list_themes_reports_the_whole_vocabulary_not_a_page(monkeypatch):
    """The brief's "how many themes are there?" — the rendered total is a factual
    claim, so it must never be a truncated page of the vocabulary."""
    vocabulary = _theme_vocab(*[f"Theme {i}" for i in range(30)])
    seen = {}

    def fake_vocabulary(**kw):
        seen.update(kw)
        return vocabulary[: kw.get("limit", tools.THEME_VOCABULARY_LIMIT)]

    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", fake_vocabulary)
    r = tools.list_themes()
    assert seen["limit"] == tools.THEME_VOCABULARY_LIMIT
    assert len(r.data["themes"]) == 30
    assert r.rendered.startswith("The collection covers 30 themes:")



def test_list_themes_empty_falls_through(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: [])
    r = tools.list_themes()
    assert r.ok is False and r.tool == "list_themes"


def _mixed_vocab():
    """Two primary themes (one per group) plus sub-themes hanging off them."""
    return [
        {"theme": "Energy", "theme_type": "primary", "parent": None,
         "theme_group": "main", "documents": 227},
        {"theme": "Energy Access", "theme_type": "sub", "parent": "Energy",
         "theme_group": "main", "documents": 13},
        {"theme": "Energy Efficiency", "theme_type": "sub", "parent": "Energy",
         "theme_group": "main", "documents": 13},
        {"theme": "Green Shipping", "theme_type": "primary", "parent": None,
         "theme_group": "other", "documents": 2},
    ]


def test_list_themes_excludes_sub_themes_from_the_default_listing(monkeypatch):
    """"How many themes are there?" counts top-level themes. Including
    sub-themes both overstates the total and flattens the hierarchy."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes()
    assert r.data["themes"] == ["Energy", "Green Shipping"]
    assert r.data["main_themes"] == ["Energy"]
    assert r.data["other_themes"] == ["Green Shipping"]
    assert r.rendered.startswith("The collection covers 2 themes:")
    assert "Energy Access" not in r.rendered


def test_list_themes_children_renders_the_full_tree(monkeypatch):
    """"...with its children" wants the same themes, annotated — not a different,
    shorter set. Children nest under their parent; the Main/Other split stays."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes(children=True)
    assert r.ok
    assert r.data["themes"] == ["Energy", "Green Shipping"]
    assert r.data["by_parent"] == {"Energy": ["Energy Access", "Energy Efficiency"]}
    assert r.rendered == (
        "The collection covers 2 themes:\n\n"
        "Main themes:\n"
        "- Energy\n"
        "    - Energy Access\n"
        "    - Energy Efficiency\n\n"
        "Other themes:\n"
        "- Green Shipping"
    )


def test_list_themes_children_keeps_themes_that_have_none(monkeypatch):
    """The count must not shrink between "how many themes" and "with their
    children" — a childless theme still appears, just without a nested list."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    plain = tools.list_themes()
    tree = tools.list_themes(children=True)
    assert tree.data["themes"] == plain.data["themes"]
    assert tree.rendered.startswith("The collection covers 2 themes:")
    assert "- Green Shipping" in tree.rendered  # no children, still listed


def test_list_themes_children_as_a_table_groups_rows_under_one_theme(monkeypatch):
    """The theme is named on its first row only. Repeating it down the column
    reads as unrelated pairs instead of one theme owning several sub-themes."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes(children=True, output_format="table")
    assert r.rendered == (
        "The collection covers 2 themes:\n\n"
        "**Main themes**\n"
        "| theme | sub-theme |\n"
        "| --- | --- |\n"
        "| Energy | Energy Access |\n"
        "|  | Energy Efficiency |\n\n"     # same theme: cell left blank
        "**Other themes**\n"
        "| theme | sub-theme |\n"
        "| --- | --- |\n"
        "| Green Shipping | |"             # childless theme keeps its row
    )


def test_list_themes_children_of_one_parent(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes(children=True, parent="Energy")
    assert r.data["parent"] == "Energy"
    assert r.data["sub_themes"] == ["Energy Access", "Energy Efficiency"]
    assert r.rendered == (
        "Energy has 2 sub-themes:\n- Energy Access\n- Energy Efficiency"
    )


def test_list_themes_children_of_one_parent_is_case_insensitive(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes(children=True, parent="energy")
    assert r.ok and r.data["parent"] == "Energy"  # answers with the stored casing


def test_list_themes_real_theme_with_no_children_says_so(monkeypatch):
    """A true statement beats falling through to a vague semantic answer — the
    theme exists, it just has no children."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes(children=True, parent="Green Shipping")
    assert r.ok is True
    assert r.data["sub_themes"] == []
    assert r.rendered == "Green Shipping has no sub-themes."


def test_list_themes_children_of_an_unknown_theme_is_a_miss(monkeypatch):
    """Distinct from the case above: this name is not a theme at all."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: _mixed_vocab())
    r = tools.list_themes(children=True, parent="Quantum Beekeeping")
    assert r.ok is False and r.error_kind == "unresolved"
    assert r.rendered == "No theme matching 'Quantum Beekeeping' found."


def test_list_themes_no_primary_themes_falls_through(monkeypatch):
    """A vocabulary of only sub-themes cannot answer "what themes are there"."""
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: [{"theme": "Air", "theme_type": "sub", "parent": "Environment",
                       "theme_group": "main", "documents": 1}],
    )
    assert tools.list_themes().ok is False


def test_list_themes_splits_main_and_other(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: _theme_vocab("Energy", ("Green Shipping", "other")),
    )
    r = tools.list_themes()
    assert r.data["main_themes"] == ["Energy"]
    assert r.data["other_themes"] == ["Green Shipping"]
    assert r.rendered.index("Main themes:") < r.rendered.index("Other themes:")
    assert "- Energy" in r.rendered and "- Green Shipping" in r.rendered


def test_list_themes_ungrouped_theme_lists_under_other(monkeypatch):
    """theme_group is NULL for a theme ingestion never classified — it must list
    under Other rather than being dropped."""
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: _theme_vocab(("Quantum Beekeeping", None)),
    )
    r = tools.list_themes()
    assert r.data["main_themes"] == []
    assert r.data["other_themes"] == ["Quantum Beekeeping"]
    assert "Main themes" not in r.rendered
    assert "Other themes:\n- Quantum Beekeeping" in r.rendered



def test_list_themes_table_format_has_two_labelled_sections(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: _theme_vocab("Energy", ("Green Shipping", "other")),
    )
    r = tools.list_themes(output_format="table")
    assert "**Main themes**" in r.rendered and "**Other themes**" in r.rendered
    assert "| Energy |" in r.rendered and "| Green Shipping |" in r.rendered



def test_aggregate_records_table_and_dimension(monkeypatch):
    seen = {}

    def fake_dist(group_by, **kw):
        seen["dimension"] = group_by
        return [("Climate", 5), ("Energy", 3)]

    monkeypatch.setattr("app.catalog.queries.distribution", fake_dist)
    r = tools.aggregate_records(None, "theme", RecordFilters(), output_format="table")
    assert r.ok
    assert r.data["groups"] == [["Climate", 5], ["Energy", 3]]
    assert seen["dimension"] == "theme"  # theme -> theme facet
    assert "| theme | count |" in r.rendered


def test_aggregate_records_plain(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distribution", lambda group_by, **k: [("Climate", 5)]
    )
    r = tools.aggregate_records(None, "theme", RecordFilters())
    assert r.rendered == "Distribution of items by theme:\n- Climate: 5"


def test_aggregate_records_passes_tag_scope(monkeypatch, resolve_tag_ok):
    seen = {}

    def fake_dist(group_by, **kw):
        seen.update(kw)
        return [("Climate", 5)]

    monkeypatch.setattr("app.catalog.queries.distribution", fake_dist)
    r = tools.aggregate_records(None, "theme", RecordFilters(tag="policy"))
    assert r.ok
    assert seen["tag"] == "policy"


def test_aggregate_records_unmatched_tag_with_no_rows_is_a_terminal_miss(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.distribution", lambda group_by, **k: [])
    r = tools.aggregate_records(None, "theme", RecordFilters(tag="nonexistent"))
    assert r.ok is False and r.error_kind == "unresolved"


def test_aggregate_records_content_type_maps_to_bundle(monkeypatch):
    seen = {}

    def fake_dist(group_by, **kw):
        seen["dimension"] = group_by
        return [("news", 10)]

    monkeypatch.setattr("app.catalog.queries.distribution", fake_dist)
    tools.aggregate_records(None, "content_type", RecordFilters())
    assert seen["dimension"] == "bundle"


def test_aggregate_records_empty_is_not_ok(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.distribution", lambda group_by, **k: [])
    r = tools.aggregate_records("news", "year", RecordFilters())
    assert r.ok is False


# --------------------------------------------------------------------------- #
# resolve_entity — the tools.py wrapper around app.retrieval.structured.resolve.
# Candidate ranking/banding itself is covered by test_entity_resolution.py and
# test_entity_resolution_scoring.py; these tests cover the ToolResult shaping.
# --------------------------------------------------------------------------- #

def _cand(name, type_="author", score=1.0, id_=None):
    from app.retrieval.structured.resolve import EntityCandidate

    return EntityCandidate(id=id_ or name, canonical_name=name, type=type_, score=score)


def test_resolve_entity_accept_returns_resolved_candidate(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.resolve.resolve_entity",
        lambda query, type=None, **kw: [_cand("Rishabh Negi", score=0.957),
                                         _cand("Rishab Nigam", score=0.783)],
    )
    r = tools.resolve_entity("rishab negi", type="author")
    assert r.ok is True
    assert r.error_kind is None
    assert r.data["resolved"] == {
        "id": "Rishabh Negi", "canonical_name": "Rishabh Negi",
        "type": "author", "score": 0.957,
    }
    assert len(r.data["candidates"]) == 2
    assert r.rendered == "'rishab negi' resolves to Rishabh Negi (author)."


def test_resolve_entity_ambiguous_lists_candidates_and_asks(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.resolve.resolve_entity",
        lambda query, type=None, **kw: [_cand("Rishabh Negi", score=0.75),
                                         _cand("Rishab Nigam", score=0.75)],
    )
    r = tools.resolve_entity("rishab", type="author")
    assert r.ok is False
    assert r.error_kind == "ambiguous"
    assert "resolved" not in r.data
    assert r.rendered == (
        "'rishab' matches more than one author:\n"
        "1. Rishabh Negi\n"
        "2. Rishab Nigam\n"
        "Which did you mean?"
    )


def test_resolve_entity_ambiguous_caps_display_at_three(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.resolve.resolve_entity",
        lambda query, type=None, **kw: [
            _cand("A", score=0.75), _cand("B", score=0.74),
            _cand("C", score=0.73), _cand("D", score=0.72),
        ],
    )
    r = tools.resolve_entity("x", type="author")
    assert r.rendered.count("\n") == 4  # 3 numbered options + the closing question
    assert "D" not in r.rendered
    assert len(r.data["candidates"]) == 4  # the full ranking is still in data


def test_resolve_entity_no_candidates_is_terminal_miss(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.resolve.resolve_entity", lambda query, type=None, **kw: []
    )
    r = tools.resolve_entity("zzznonexistent", type="theme")
    assert r.ok is False
    assert r.error_kind == "unresolved"
    assert r.rendered == "No theme matching 'zzznonexistent' found."


def test_resolve_entity_low_score_is_terminal_miss(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.resolve.resolve_entity",
        lambda query, type=None, **kw: [_cand("Rishabh Negi", score=0.31)],
    )
    r = tools.resolve_entity("zzznonexistent", type="author")
    assert r.ok is False and r.error_kind == "unresolved"


def test_resolve_entity_unadvertised_type_is_reported_not_raised(monkeypatch):
    def boom(query, type=None, **kw):
        raise ValueError("bad type")

    monkeypatch.setattr("app.retrieval.structured.resolve.resolve_entity", boom)
    r = tools.resolve_entity("policy", type="tag")
    assert r.ok is False
    assert "bad type" in r.error


def test_resolve_entity_query_failure_is_not_ok(monkeypatch):
    def boom(query, type=None, **kw):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.retrieval.structured.resolve.resolve_entity", boom)
    r = tools.resolve_entity("rishabh", type="author")
    assert r.ok is False and r.error == "query failed"


def test_resolve_entity_no_type_labels_as_generic_entity(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.resolve.resolve_entity", lambda query, type=None, **kw: []
    )
    r = tools.resolve_entity("zzznonexistent")
    assert r.rendered == "No entity matching 'zzznonexistent' found."


@pytest.mark.parametrize("query", [None, "", "   "])
def test_resolve_entity_missing_query_falls_through_without_rendering_it(query):
    """`ToolCall.query` defaults to None, so a planned call that omits it lands
    here — it must not render the missing value into the answer ("No entity
    matching 'None' found."). A planner that forgot the query is a bug with
    nothing useful to tell the user, so this falls through rather than being
    terminal."""
    r = tools.resolve_entity(query, "author")
    assert r.ok is False
    assert r.rendered == ""
    assert r.error_kind is None  # fall through, not a terminal answer
    assert r.error == "no query to resolve"
