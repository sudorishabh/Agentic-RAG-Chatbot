"""The publication-date model is gone, and stays gone.

The system used to represent a document's date as a *publication* date. It no
longer does: a document has an **effective date** — the business/content date its
Drupal bundle's configured field states — and, where the bundle declares one, an
end to the period that date opens. For `news` or `report` the two happen to
coincide; for `events` and the project bundles the field is a start date, and
calling it a publication date was simply wrong.

Two concepts with one meaning is the failure this guards against. A rename that
leaves the old names reachable invites new code to reach for them, and six months
later the codebase has both. So the old vocabulary is asserted **absent** from
application code, not merely unused.

The migration helpers are the one deliberate exception: they name the legacy
columns because their whole job is carrying data out of them and then dropping
them. They are listed explicitly below rather than pattern-matched, so adding a
new exception is a visible decision.
"""

from __future__ import annotations

import pathlib

import pytest

#: The names the system must no longer use for its own concepts.
RETIRED = (
    "FIELD_KINDS",
    "published_at",
    "published_until",
    "published_at_source",
    "published_at_precision",
    "published_until_precision",
    "document_published_at",
    "current_published_at",
    "resolve_published_at",
    "_published_at_for",
)

#: Files allowed to name them, and why. Each one exists to *remove* the old
#: model; none of them reads a legacy column as a source of truth.
ALLOWED = {
    # The copy/verify/drop migration. It cannot drop a column without naming it.
    "app/catalog/schema.py":
        "LEGACY_DATE_COLUMNS / DROPPED_DATE_COLUMNS drive the column migration",
    # The payload-key migration, for the same reason.
    "scripts/backfill_bundle_dates.py":
        "LEGACY_PAYLOAD_KEYS drives the Qdrant key migration",
    # The bump changelog. Naming what a version changed *from* is the whole
    # value of it: "which points predate the rename" is unanswerable otherwise.
    "app/ingestion/version.py":
        "the PAYLOAD=2 note records which keys were renamed",
    # This file.
    "tests/ingestion/dates/test_no_publication_date_vocabulary.py":
        "asserts the absence",
}

ROOTS = ("app", "scripts")


def _sources() -> list[pathlib.Path]:
    found: list[pathlib.Path] = []
    for root in ROOTS:
        for path in pathlib.Path(root).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            found.append(path)
    assert found, "no sources found; the test is looking in the wrong place"
    return found


def _relative(path: pathlib.Path) -> str:
    return path.as_posix()


@pytest.mark.parametrize("name", RETIRED)
def test_no_application_code_uses_the_retired_name(name):
    offenders = []
    for path in _sources():
        if _relative(path) in ALLOWED:
            continue
        if name in path.read_text(encoding="utf-8"):
            offenders.append(_relative(path))
    assert offenders == [], (
        f"{name!r} is retired. The system has one date model: "
        f"effective_start_date / effective_end_date (+ start_precision, "
        f"end_precision, date_source). Found in: {offenders}"
    )


def test_the_allowlist_is_not_stale():
    """An exception that no longer needs to exist is an exception that will be
    copied. Every allowed file must still actually name a retired term."""
    for name in ALLOWED:
        path = pathlib.Path(name)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert any(term in text for term in RETIRED), (
            f"{name} no longer names any retired term; drop it from ALLOWED."
        )


def test_no_module_is_named_after_the_old_model():
    for root in ROOTS:
        for path in pathlib.Path(root).rglob("*.py"):
            assert "published" not in path.stem, path


# --------------------------------------------------------------------------- #
# The replacement is present and consistent
# --------------------------------------------------------------------------- #

def test_the_canonical_document_carries_exactly_the_new_fields():
    from app.core.models import CanonicalDocument

    doc = CanonicalDocument(document_id="d", source_type="website")
    for field in ("effective_start_date", "effective_end_date",
                  "start_precision", "end_precision", "date_source"):
        assert hasattr(doc, field), field
    for field in RETIRED:
        assert not hasattr(doc, field), field


def test_the_catalog_row_carries_exactly_the_new_fields():
    from app.catalog.models import StateRecord

    row = StateRecord(document_id="d", source_type="website", source_key="k",
                      fingerprint="f")
    for field in ("effective_start_date", "effective_end_date",
                  "start_precision", "end_precision", "date_source"):
        assert hasattr(row, field), field
    for field in RETIRED:
        assert not hasattr(row, field), field


def test_the_chunk_payload_carries_exactly_the_new_keys():
    from app.ingestion.chunking.models import Chunk, DocumentMeta
    from app.ingestion.chunking.payload import build_payload

    meta = DocumentMeta(
        document_id="d", source_type="website", title="t",
        effective_start_date="2020-01-02T00:00:00+00:00",
        start_precision="year",
        effective_end_date="2022-12-31T00:00:00+00:00",
        end_precision="year",
    )
    payload = build_payload(Chunk(chunk_id="c", text="x", is_parent=False,
                                  meta=meta))
    assert payload["effective_start_date"] == "2020-01-02T00:00:00+00:00"
    assert payload["effective_end_date"] == "2022-12-31T00:00:00+00:00"
    assert payload["start_precision"] == "year"
    assert payload["end_precision"] == "year"
    for key in RETIRED:
        assert key not in payload, key


def test_the_two_date_objects_agree_on_their_field_names():
    """`EffectiveDate` and `ResolvedDate` describe the same four things. Naming
    them differently is how a caller ends up reading the wrong one."""
    from dataclasses import fields

    from app.ingestion.bundle_dates import EffectiveDate
    from app.ingestion.date_resolution import ResolvedDate

    shared = {"start_value", "start_precision", "end_value", "end_precision"}
    assert shared <= {f.name for f in fields(EffectiveDate)}
    assert shared <= {f.name for f in fields(ResolvedDate)}


def test_the_payload_migration_map_matches_the_column_migration_map():
    """One rename, described in two places because two stores need it. They must
    not disagree about what a key becomes."""
    from app.catalog.schema import LEGACY_DATE_COLUMNS
    from scripts.backfill_bundle_dates import LEGACY_PAYLOAD_KEYS

    columns = LEGACY_DATE_COLUMNS[""]
    for old, new in LEGACY_PAYLOAD_KEYS.items():
        if not new:
            continue  # dropped, not renamed
        assert columns.get(old) == new, (old, new, columns.get(old))


def test_the_dropped_column_is_one_nothing_ever_wrote():
    """`document_published_at` is dropped rather than carried across. It was
    modelled as "the date the document states about itself" and no ingestion
    path, script or backfill ever assigned it — so there is no data to lose."""
    from app.catalog.schema import DROPPED_DATE_COLUMNS, LEGACY_DATE_COLUMNS

    assert "document_published_at" in DROPPED_DATE_COLUMNS[""]
    assert "document_published_at" not in LEGACY_DATE_COLUMNS[""]


def test_dropping_is_gated_on_the_copy_having_finished():
    """A drop is the one irreversible step, so it must refuse rather than
    truncate a half-migrated database."""
    import inspect

    from app.catalog import schema

    source = inspect.getsource(schema.drop_legacy_date_columns)
    assert "unmigrated_legacy_rows()" in source
    assert "raise RuntimeError" in source


# --------------------------------------------------------------------------- #
# The source-field taxonomy describes the field, not a publication
# --------------------------------------------------------------------------- #

def test_the_field_taxonomy_has_no_publication_role():
    """`FIELD_ROLES` says what a *Drupal field* is. It used to say `publication`
    / `event` / `period`, which read as a claim about the resulting date — and
    the system stores no publication dates. The roles now describe the field."""
    from app.ingestion.source_dates import FIELD_ROLES

    roles = {role for role, _ in FIELD_ROLES.values()}
    assert roles == {"date", "range_start", "range_end", "sort_key", "not_a_date"}


def test_every_role_the_resolver_can_emit_is_declared():
    """`created_stamp` is emitted but not in the table, because `created` is not
    a CMS field. It still has to be a declared member of the vocabulary."""
    import typing

    from app.ingestion.source_dates import FIELD_ROLES, FieldRole

    declared = set(typing.get_args(FieldRole))
    assert {role for role, _ in FIELD_ROLES.values()} <= declared
    assert "created_stamp" in declared


def test_the_effective_date_carries_a_field_role_not_a_kind():
    from dataclasses import fields

    from app.ingestion.bundle_dates import EffectiveDate

    names = {f.name for f in fields(EffectiveDate)}
    assert "field_role" in names
    assert "kind" not in names


def test_the_llm_date_type_keeps_its_publication_vocabulary():
    """The one place "publication" still earns its keep, and it is a different
    question about a different thing: what kind of date the model found *inside
    a PDF's text*. The prompt literally asks whether a quoted statement is a
    publication, a notification or an effective date, so the verdict has to be
    able to say so."""
    import typing

    from app.ingestion.date_rules import DateType

    values = set(typing.get_args(DateType))
    assert "publication" in values
    assert "notification" in values


def test_the_two_taxonomies_do_not_overlap():
    """They share one `date_type` column, told apart by `origin`. Overlapping
    values would make a row ambiguous about which question it answers."""
    import typing

    from app.ingestion.date_rules import DateType
    from app.ingestion.source_dates import FIELD_ROLES

    roles = {role for role, _ in FIELD_ROLES.values()}
    shared = roles & set(typing.get_args(DateType))
    assert shared == set(), shared


def test_the_payload_version_was_bumped_for_the_key_rename():
    """Payload keys changed, which is precisely what PAYLOAD tracks. Without the
    bump a deployment that skipped the migration would serve points whose date
    keys no reader consults, with nothing to signal it."""
    from app.ingestion.version import PAYLOAD, PIPELINE_VERSION

    assert PAYLOAD >= 2
    assert f"p{PAYLOAD}" in PIPELINE_VERSION
