"""Unit tests for the theme-scoped structured queries and distribution path.

Covers the theme vocabulary reader, the theme filter in the catalog SQL (exact
name or sub-theme parent), the distribution query shape, and the semantic-path
theme filter. All SQL runs against scripted fakes; no MySQL, no LLM.
"""

from __future__ import annotations

from app.catalog import queries as state
from app.retrieval import query_processor as qp


class _FakeCursor:
    def __init__(self, fetchall_results: list | None = None,
                 fetchone_results: list | None = None):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch(monkeypatch, module, cursor):
    monkeypatch.setattr(module, "mysql_connection", lambda: _FakeConn(cursor))


# --------------------------------------------------------------------------- #
# theme_vocabulary — what themes exist, from documents_theme.
# --------------------------------------------------------------------------- #

def _vocab_row(theme, group="main", theme_type="primary", parent=None, documents=1):
    return {"theme": theme, "theme_type": theme_type, "parent": parent,
            "theme_group": group, "documents": documents}


def test_theme_vocabulary_reads_the_facet_with_its_hierarchy(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[
        _vocab_row("Climate Change", documents=150),
        _vocab_row("Air", theme_type="sub", parent="Environment", documents=77),
    ]])
    _patch(monkeypatch, state, cursor)

    rows = state.theme_vocabulary()
    assert [r["theme"] for r in rows] == ["Climate Change", "Air"]
    assert rows[1]["parent"] == "Environment" and rows[1]["theme_group"] == "main"
    sql, params = cursor.calls[0]
    assert "_theme`" in sql and "GROUP BY theme, theme_type, parent, theme_group" in sql
    assert "theme NOT IN (%s, %s)" in sql  # boolean artefacts excluded in SQL
    assert params == ("False", "True")


def test_theme_vocabulary_collapses_conflicting_hierarchy_variants(monkeypatch):
    """data.json changing between ingests leaves stale rows, so one theme can
    carry two hierarchies. Callers must still see exactly one row per theme —
    the variant the most documents agree on."""
    cursor = _FakeCursor(fetchall_results=[[
        _vocab_row("Energy", theme_type="primary", documents=40),
        _vocab_row("Energy", theme_type="sub", parent="Stale", documents=2),
    ]])
    _patch(monkeypatch, state, cursor)

    rows = state.theme_vocabulary()
    assert len(rows) == 1
    assert rows[0]["theme_type"] == "primary" and rows[0]["documents"] == 40


def test_theme_vocabulary_clamps_the_theme_limit(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[
        [_vocab_row(f"T{i}") for i in range(10)],
    ])
    _patch(monkeypatch, state, cursor)
    assert len(state.theme_vocabulary(limit=3)) == 3


def test_distinct_themes_is_a_names_view_of_the_vocabulary(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[_vocab_row("Air"), _vocab_row("Water")]])
    _patch(monkeypatch, state, cursor)
    assert state.distinct_themes() == ["Air", "Water"]


# --------------------------------------------------------------------------- #
# Catalog SQL — theme/tag scoping and distribution.
# --------------------------------------------------------------------------- #

def test_count_by_theme_matches_name_or_sub_theme(monkeypatch):
    """Exact name OR parent: a substring match both missed the sub-themes and
    wrongly merged siblings ("Environment" sweeping in "Environment Education")."""
    cursor = _FakeCursor(fetchone_results=[{"n": 625}])
    _patch(monkeypatch, state, cursor)

    assert state.count_documents(source_type="website", theme="Environment") == 625
    sql, params = cursor.calls[0]
    assert "_theme` c" in sql
    assert "(c.theme = %s OR c.parent = %s)" in sql
    assert "LIKE" not in sql.split("WHERE")[1]  # no substring matching on the theme
    assert "COUNT(DISTINCT s.document_id)" in sql
    assert params == ("website", "Environment", "Environment")


def test_count_by_tag_uses_its_own_facet(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 12}])
    _patch(monkeypatch, state, cursor)

    assert state.count_documents(source_type="website", tag="Waste management") == 12
    sql, params = cursor.calls[0]
    assert "_tag` t" in sql and "t.tag = %s" in sql
    assert params == ("website", "Waste management")


def test_theme_and_tag_are_independent_joins(monkeypatch):
    """A document must satisfy both, so they cannot collapse into one condition."""
    cursor = _FakeCursor(fetchone_results=[{"n": 3}])
    _patch(monkeypatch, state, cursor)

    state.count_documents(source_type="website", theme="Energy", tag="solar")
    sql, params = cursor.calls[0]
    assert "_theme` c" in sql and "_tag` t" in sql
    assert sql.count("JOIN") == 2
    assert params == ("website", "Energy", "Energy", "solar")


def test_count_by_title_contains(monkeypatch):
    """count_documents must take the same title filter list_documents does, or a
    count and a listing of the same query disagree."""
    cursor = _FakeCursor(fetchone_results=[{"n": 4}])
    _patch(monkeypatch, state, cursor)

    assert state.count_documents(source_type="website", title_contains="Solar") == 4
    sql, params = cursor.calls[0]
    assert "s.title LIKE %s" in sql
    assert params == ("website", "%Solar%")


def test_count_scoped_to_entity_type(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 5}])
    _patch(monkeypatch, state, cursor)

    assert state.count_documents(source_type="website", entity_type="node") == 5
    sql, params = cursor.calls[0]
    assert "s.entity_type = %s" in sql
    assert params == ("website", "node")


def test_distribution_scoped_to_entity_type(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": "report", "n": 8}]])
    _patch(monkeypatch, state, cursor)

    assert state.distribution("bundle", entity_type="node") == [("report", 8)]
    sql, params = cursor.calls[0]
    assert "s.entity_type = %s" in sql and params == ("website", "node")


def test_distribution_by_theme_groups_on_the_facet(monkeypatch):
    cursor = _FakeCursor(
        fetchall_results=[[{"k": "Climate Change", "n": 12}, {"k": "Energy", "n": 5}]]
    )
    _patch(monkeypatch, state, cursor)

    rows = state.distribution("theme")
    assert rows == [("Climate Change", 12), ("Energy", 5)]
    sql, params = cursor.calls[0]
    assert "GROUP BY k ORDER BY n DESC" in sql
    assert "_theme` gt" in sql and "gt.theme AS k" in sql
    assert "COUNT(DISTINCT s.document_id)" in sql
    # Same artefact exclusion as theme_vocabulary, so a breakdown and a listing
    # never disagree about which themes exist.
    assert "gt.theme NOT IN (%s, %s)" in sql
    assert params == ("website", "False", "True")


def test_distribution_scoped_by_theme_and_author(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": "2024", "n": 4}]])
    _patch(monkeypatch, state, cursor)

    rows = state.distribution("year", theme="Energy", author="Sharma", limit=20)
    assert rows == [("2024", 4)]
    sql, params = cursor.calls[0]
    assert "_theme` c" in sql and "(c.theme = %s OR c.parent = %s)" in sql
    assert "_author` a" in sql and "a.author LIKE %s" in sql
    assert "COUNT(DISTINCT s.document_id)" in sql
    assert params == ("website", "%Sharma%", "Energy", "Energy")


def test_distribution_by_year_skips_undated(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": 2024, "n": 9}]])
    _patch(monkeypatch, state, cursor)

    assert state.distribution("year") == [("2024", 9)]
    sql, _ = cursor.calls[0]
    assert "YEAR(s.published_at)" in sql and "IS NOT NULL" in sql


def test_distribution_rejects_unknown_dimension():
    try:
        state.distribution("acl")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown dimension must raise")


# --------------------------------------------------------------------------- #
# Semantic path — theme filter over the vector search.
# --------------------------------------------------------------------------- #

def test_theme_condition_matches_payload_names():
    """The catalog is keyed by name, so the Qdrant filter is the name leg — there
    is no term table to translate a name into payload UUIDs."""
    condition = qp._theme_condition("climate change")
    legs = {c.key: c for c in condition.should}
    assert set(legs) == {"categories"}
    assert "Climate Change" in legs["categories"].match.any
    assert "climate change" in legs["categories"].match.any


def test_theme_condition_needs_no_database():
    """Purely a payload filter now, so it cannot fail on a MySQL outage."""
    condition = qp._theme_condition("Energy")
    assert [c.key for c in condition.should] == ["categories"]
