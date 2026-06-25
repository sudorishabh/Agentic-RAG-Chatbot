"""Tests for the retrieval query filter."""

from __future__ import annotations

from app.retrieval.hybrid_search import _NON_SEARCHABLE_SECTIONS, build_filter


def test_filter_excludes_non_searchable_sections():
    f = build_filter()
    cond = next(c for c in (f.must_not or []) if c.key == "section_type")
    assert set(cond.match.any) == set(_NON_SEARCHABLE_SECTIONS)


def test_filter_keeps_core_must_conditions():
    f = build_filter(tenant_id="default", user_groups=["public"])
    keys = {c.key for c in f.must}
    assert {"is_parent", "is_current", "tenant_id", "acl"} <= keys
