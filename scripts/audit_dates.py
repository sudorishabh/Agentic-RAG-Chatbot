"""Read-only audit of every date the corpus stores, and a baseline to diff against.

Every issue this reports existed for months without anything noticing, which is
the actual problem: `published_at` is the field all ranking, filtering, ordering
and recency reads, and nothing ever checked whether it was right.

Two jobs:

**Measure.** One pass over MySQL and one scroll of Qdrant, grouped into the
questions worth asking separately — is the value present and plausible, do the
stores agree, does it match the decision it was based on, does the document's
own name contradict it, does the source metadata contradict it, and is it
precise enough to mean anything.

**Compare.** ``--json`` writes a snapshot; ``--compare`` re-runs and diffs
against one, exiting non-zero if a count moved in the wrong direction. That is
what makes a date change reviewable: run it before, apply, run it after, and the
difference is the change's actual blast radius rather than a claim about it.

Deliberately read-only. It issues SELECTs and one Qdrant scroll and writes
nothing but its own report — a checker that repaired what it found would be a
second, unsupervised write path, and the cost of a wrong reading would be data
loss instead of a wrong number.

    python -m scripts.audit_dates
    python -m scripts.audit_dates --json reports/dates/baseline.json
    python -m scripts.audit_dates --compare reports/dates/baseline.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.core.editions import normalise_edition
from app.ingestion.source_dates import IST, is_plausible, to_ist_date  # noqa: F401

#: How many offending ids a check keeps. Enough to start an investigation, few
#: enough that a report of a broken corpus is still readable.
SAMPLE_LIMIT = 5

#: A document sharing its exact timestamp with at least this many others was
#: dated by a batch import, not by publication. One second cannot be the
#: publication instant of a hundred separate documents.
CROWD_THRESHOLD = 100

_PERCENT = re.compile(r"%[0-9A-Fa-f]{2}")
_YEAR = re.compile(r"(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)")
_DATEISH_KEY = re.compile(r"date|year|publish|issued|created|changed|period", re.I)

# Language that makes a later year in a name legitimate rather than a
# contradiction: a document about a 2030 target is not published in 2030.
#
# ``post-20xx`` and ``award`` were added after the source-date backfill flagged
# three documents whose corrections were then confirmed against the rendered
# pages — "Sustainability 4.0 Awards 2017" announced 8 November 2016, and two
# "Post-2015 Development Agenda" bulletins from 9 July 2014. Both are ordinary
# forward references: an award named for a year is announced before it, and
# "post-2015" names the period after 2015 rather than a publication date. The
# dates were verified first; the filter was widened second.
_FORWARD_LOOKING = re.compile(
    r"\b(vision|target|roadmap|outlook|projection|scenario|strateg|pathway|"
    r"net[-\s]?zero|forecast|goal|awards?|by\s+20\d{2}|to\s+20\d{2}|"
    r"post[-\s]?20\d{2}|2030|2040|2047|2050|2070)\b",
    re.I,
)


# --------------------------------------------------------------------------- #
# Pure helpers. No I/O, so the judgements below are unit-testable without a
# database — which is the same split `date_rules.decide` uses.
# --------------------------------------------------------------------------- #

def strip_percent_encoding(name: str | None) -> str:
    """``name`` with percent-escapes blanked out.

    Not decoded — blanked. ``Report%2024.pdf`` is "Report 24", and the escape
    ``%20`` followed by ``24`` reads as the four digits ``2024`` to any year
    pattern. Removing the escapes removes a class of phantom years without
    guessing what the original character was.
    """
    return _PERCENT.sub(" ", name or "")


def fiscal_year_conflict(name: str | None, published_year: int) -> int | None:
    """Years by which ``published_year`` precedes the period the name reports on.

    A document titled for FY 2024-25 cannot have been published in 2018. This is
    the strongest signal available without reading the document, because it needs
    no external source — the date and the name contradict each other.
    """
    edition = normalise_edition(strip_percent_encoding(name))
    if edition is None:
        return None
    gap = int(edition[:4]) - published_year
    return gap if gap > 0 else None


def plain_year_conflict(name: str | None, published_year: int) -> int | None:
    """Years by which ``published_year`` precedes a plain year in the name.

    Weaker than :func:`fiscal_year_conflict`: a name may reference a future year
    legitimately, so forward-looking language disqualifies the reading.
    """
    cleaned = strip_percent_encoding(name)
    if _FORWARD_LOOKING.search(cleaned):
        return None
    years = [int(y) for y in _YEAR.findall(cleaned)]
    if not years:
        return None
    gap = max(years) - published_year
    return gap if gap > 0 else None


def date_ish_keys(meta: dict[str, Any]) -> dict[str, Any]:
    """Source-metadata entries whose *name* suggests a date, with usable values.

    Name-based on purpose. This audit deliberately does not decide which of
    these is a publication date — several are event and project-period dates
    that would be actively wrong to use, and that classification belongs to
    ``app.ingestion.source_dates`` rather than to a measurement script. What is
    reported here is the raw disagreement per field, so the classification can
    be argued from data.
    """
    out: dict[str, Any] = {}
    for key, value in (meta or {}).items():
        if not _DATEISH_KEY.search(key) or value in (None, "", [], {}):
            continue
        out[key] = value[0] if isinstance(value, list) and value else value
    return out


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

@dataclass
class Check:
    """One question, its answer, and what a non-zero answer means."""

    name: str
    count: int
    detail: str
    samples: list[str] = field(default_factory=list)
    #: False for counts that are descriptive rather than defects, so a
    #: comparison run does not treat "3409 documents are migration-dated" as a
    #: regression when it has not moved.
    is_defect: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {"count": self.count, "detail": self.detail,
                "samples": self.samples, "is_defect": self.is_defect}


def _check(name: str, offenders: Iterable[str], detail: str,
           *, is_defect: bool = True) -> Check:
    items = list(offenders)
    return Check(name=name, count=len(items), detail=detail,
                 samples=sorted(items)[:SAMPLE_LIMIT], is_defect=is_defect)


def _rows(cur, sql: str, params: tuple = ()) -> list[dict]:
    cur.execute(sql, params)
    return list(cur.fetchall())


def _sql_check(cur, name: str, source: str, clause: str, detail: str,
               *, id_column: str = "document_id", is_defect: bool = True) -> Check:
    """A check counted by the database, with a handful of ids for a sample.

    The count comes from ``COUNT(*)`` and the samples from a separate ``LIMIT``.
    Doing both with one limited query — which this did — caps every count at the
    limit, so a check with a thousand offenders reports the limit and the number
    is quietly wrong. In a tool whose whole job is measurement that is the worst
    possible defect, and it hid the true size of a check the first time one
    exceeded it.

    ``source`` is a full FROM expression, so a check over a join reads the same
    way as one over a single table and there is no quoting to get wrong.
    """
    count = int(_rows(cur, f"SELECT COUNT(*) n FROM {source} WHERE {clause}")[0]["n"])
    samples = [str(r["id"]) for r in _rows(
        cur, f"SELECT {id_column} AS id FROM {source} WHERE {clause} "
             f"ORDER BY {id_column} LIMIT {SAMPLE_LIMIT}")]
    return Check(name=name, count=count, detail=detail, samples=samples,
                 is_defect=is_defect)


def catalogue_checks(cur, table: str) -> list[Check]:
    """Is the value present, plausible, and precise enough to mean anything?"""
    checks: list[Check] = []
    for name, clause, detail in (
        ("no_published_at", "published_at IS NULL",
         "Documents with no date. Invisible to every date filter and to recency."),
        ("date_in_future", "published_at > NOW()",
         "Dated after now. Ranks above everything real."),
        ("date_before_1990", "published_at < '1990-01-01'",
         "Implausibly old; almost always a placeholder or a parse failure."),
        ("date_is_epoch", "YEAR(published_at) = 1970",
         "The unix epoch, i.e. a zero timestamp read as a date."),
        # 1 January *is* the correct marker for a year-precision value — the
        # column must hold some day and that is the one chosen. What would be
        # wrong is any other day, because then the value and its precision
        # disagree about what is known. This check was written before year
        # precision was applied and had the condition the other way round, which
        # made 389 correctly-stored dates read as a defect.
        ("year_precision_not_january",
         "published_at_precision = 'year' "
         "AND (MONTH(published_at) <> 1 OR DAY(published_at) <> 1)",
         "A year-precision date whose value is not 1 January, so the value and "
         "its recorded precision disagree about what is known."),
        ("date_provenance_unrecorded", "published_at_source IS NULL",
         "Documents whose published_at has no recorded origin."),
    ):
        try:
            checks.append(_sql_check(cur, name, f"`{table}`", clause, detail))
        except Exception as exc:
            # A column may not exist yet on an older schema; a check that cannot
            # run is reported as such rather than as passing.
            checks.append(Check(name, 0, f"not applicable ({type(exc).__name__})",
                                is_defect=False))
    return checks


def store_agreement_checks(cur, table: str) -> list[Check]:
    """Do MySQL and Qdrant carry the same date for the same document?"""
    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    catalogue = {r["document_id"]: str(r["published_at"])[:10]
                 for r in _rows(cur, f"SELECT document_id, published_at FROM `{table}`")}
    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        return [Check("qdrant_unreachable", 0, "collection missing; not compared",
                      is_defect=False)]

    indexed: dict[str, str] = {}
    undated: list[str] = []
    offset: Any = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection, limit=2048, offset=offset,
            with_payload=["document_id", "published_at"], with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            document_id = payload.get("document_id")
            if not document_id or document_id in indexed:
                continue
            stamp = str(payload.get("published_at") or "")[:10]
            if not stamp:
                undated.append(document_id)
                continue
            indexed[document_id] = stamp
        if offset is None:
            break

    mismatched = [d for d, stamp in indexed.items()
                  if d in catalogue and stamp != catalogue[d]]
    return [
        _check("point_without_date", undated,
               "Indexed chunks carrying no published_at; excluded from date filters."),
        _check("mysql_qdrant_date_mismatch", mismatched,
               "The catalogue and the index disagree about a date. The catalogue "
               "is authoritative; re-index or set_payload to converge."),
        _check("indexed_not_catalogued", [d for d in indexed if d not in catalogue],
               "Points for documents the catalogue has never heard of."),
        _check("catalogued_not_indexed", [d for d in catalogue if d not in indexed],
               "Catalogued documents with no indexed chunk.", is_defect=False),
    ]


def resolver_checks(cur, table: str) -> list[Check]:
    """Does the stored date match the decision it was supposedly based on?"""
    decision = f"`{table}_date_decision`"
    return [
        _sql_check(
            cur, "date_contradicts_its_decision",
            f"{decision} dd JOIN `{table}` d USING (document_id)",
            "(dd.action = 'propose_override' AND d.published_at <> dd.candidate_date) "
            "OR (dd.action <> 'propose_override' "
            "    AND d.published_at <> dd.current_published_at)",
            "published_at is not what the recorded decision says it should be. "
            "Either the decision or the write path is wrong.",
            id_column="dd.document_id"),
        _sql_check(
            cur, "decision_without_document",
            f"{decision} dd LEFT JOIN `{table}` d ON d.document_id = dd.document_id",
            "d.document_id IS NULL",
            "A decision row whose document is not catalogued.",
            id_column="dd.document_id", is_defect=False),
        _sql_check(
            cur, "decision_without_page",
            f"{decision} dd LEFT JOIN `{table}` p ON p.document_id = dd.node_uuid",
            "p.document_id IS NULL",
            "A decision row whose parent page is not catalogued.",
            id_column="dd.document_id", is_defect=False),
    ]


def contradiction_checks(cur, table: str) -> list[Check]:
    """Does the document's own name contradict its date?"""
    rows = _rows(cur, f"""
        SELECT document_id, title, source_key, YEAR(published_at) py FROM `{table}`""")
    fiscal, plain = [], []
    for row in rows:
        filename = (row["source_key"] or "").rsplit("/", 1)[-1]
        year = int(row["py"])
        if fiscal_year_conflict(filename, year):
            fiscal.append(row["document_id"])
        elif plain_year_conflict(f"{row['title'] or ''} {filename}", year):
            plain.append(row["document_id"])
    return [
        _check("dated_before_its_reporting_period", fiscal,
               "The name states a fiscal year starting after the stored date. A "
               "report on FY X cannot have been published before X."),
        _check("name_year_after_date", plain,
               "A plain year in the name is later than the stored date. Weaker "
               "than the above: check for forward-looking titles."),
    ]


def source_metadata_checks(cur, table: str) -> tuple[list[Check], dict[str, dict]]:
    """Per source-metadata field: how often does it disagree with the date?

    Reported per field, unclassified. Which of these fields *is* a publication
    date is decided elsewhere; this only establishes the size of each candidate.
    """
    rows = _rows(cur, f"""
        SELECT document_id, bundle, raw_meta, published_at FROM `{table}`
        WHERE raw_meta IS NOT NULL""")
    per_field: dict[str, dict] = {}
    for row in rows:
        try:
            meta = json.loads(row["raw_meta"]) if isinstance(row["raw_meta"], str) \
                else row["raw_meta"]
        except (TypeError, ValueError):
            continue
        if not isinstance(meta, dict):
            continue
        stored = row["published_at"].date()
        for key, value in date_ish_keys(meta).items():
            entry = per_field.setdefault(
                key, {"present": 0, "parses": 0, "differs": 0, "bundles": {}})
            entry["present"] += 1
            parsed = to_ist_date(value)
            if not is_plausible(parsed):
                continue
            entry["parses"] += 1
            if parsed != stored:
                entry["differs"] += 1
                entry["bundles"][row["bundle"]] = entry["bundles"].get(row["bundle"], 0) + 1
    total = sum(e["differs"] for e in per_field.values())
    return [Check("source_field_disagrees_total", total,
                  "Source-metadata date fields that disagree with published_at, "
                  "summed over all fields. NOT all of these are publication "
                  "dates — see the per-field breakdown.", is_defect=False)], per_field


def precision_checks(cur, table: str) -> list[Check]:
    """Is the date precise enough to be about one document?"""
    crowded = _rows(cur, f"""
        SELECT published_at, COUNT(*) n FROM `{table}`
        GROUP BY published_at HAVING n >= %s ORDER BY n DESC""", (CROWD_THRESHOLD,))
    crowd_total = sum(int(r["n"]) for r in crowded)
    migration = _rows(cur, f"""
        SELECT COUNT(*) n, COUNT(DISTINCT published_at) d FROM `{table}`
        WHERE published_at >= '2017-12-01' AND published_at < '2018-02-01'""")[0]
    own = _rows(cur, f"""
        SELECT COUNT(*) n FROM (SELECT published_at FROM `{table}`
        GROUP BY published_at HAVING COUNT(*) = 1) t""")[0]
    return [
        Check("documents_on_a_crowded_timestamp", crowd_total,
              f"Documents sharing an exact timestamp with >= {CROWD_THRESHOLD} "
              f"others, across {len(crowded)} timestamps. A batch import, not a "
              f"publication instant.", is_defect=False),
        Check("documents_in_migration_window", int(migration["n"]),
              f"Dated Dec 2017 - Jan 2018, across only {migration['d']} distinct "
              f"timestamps.", is_defect=False),
        Check("documents_with_own_timestamp", int(own["n"]),
              "Documents whose timestamp is theirs alone.", is_defect=False),
    ]


def adjacent_checks(cur, table: str) -> list[Check]:
    """Dates stored elsewhere that describe a document or a claim about one."""
    checks: list[Check] = []
    stated = _rows(cur, f"SELECT COUNT(*) n FROM `{table}` "
                        "WHERE document_published_at IS NOT NULL")[0]
    checks.append(Check("document_published_at_populated", int(stated["n"]),
                        "Documents carrying a date the document itself states. "
                        "Two readers consume this field; nothing writes it.",
                        is_defect=False))
    checks.append(_sql_check(
        cur, "changed_before_published", f"`{table}`",
        "changed_mark IS NOT NULL AND changed_mark < UNIX_TIMESTAMP(published_at)",
        "The crawl stamp predates the publication date. Investigated: on 22 of "
        "these the CMS itself has created > changed, and one is a journal paper "
        "carrying a 2019 issue year on a record made in Dec 2018 — both source "
        "properties, not ingestion errors. The cursor reads `changed` and the "
        "date reads `created`, so nothing downstream is wrong. Worth watching "
        "for a *rise*, which would suggest a crawl-window fault."))
    try:
        checks.append(_sql_check(
            cur, "claim_validity_epoch", f"`{table}_assertion`",
            "YEAR(valid_from) = 1970",
            "Claim validity starting at the unix epoch. Investigated: the one "
            "instance reflects the CMS, whose field_completed_start_date for "
            "that project is literally 1970-01-01 — the claim is faithful to a "
            "zero date in the source. Fixing it means the claims layer treating "
            "1970 as unknown when it reads a project period, which is a "
            "different subsystem from published_at.", id_column="claim_id"))
    except Exception as exc:
        checks.append(Check("claim_validity_epoch", 0,
                            f"not checked ({type(exc).__name__})", is_defect=False))
    return checks


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #

def run() -> tuple[list[Check], dict[str, dict]]:
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        checks = catalogue_checks(cur, table)
        checks += resolver_checks(cur, table)
        checks += contradiction_checks(cur, table)
        meta_checks, per_field = source_metadata_checks(cur, table)
        checks += meta_checks
        checks += precision_checks(cur, table)
        checks += adjacent_checks(cur, table)
        checks += store_agreement_checks(cur, table)
    return checks, per_field


def snapshot(checks: list[Check], per_field: dict[str, dict]) -> dict[str, Any]:
    return {
        "checks": {c.name: c.as_dict() for c in checks},
        "source_fields": per_field,
    }


def print_report(checks: list[Check], per_field: dict[str, dict]) -> None:
    defects = [c for c in checks if c.is_defect and c.count]
    print("=" * 78)
    print("DATE AUDIT")
    print("=" * 78)
    for heading, names in (
        ("value present and plausible",
         ("no_published_at", "date_in_future", "date_before_1990", "date_is_epoch",
          "year_precision_not_january", "date_provenance_unrecorded")),
        ("stores agree",
         ("point_without_date", "mysql_qdrant_date_mismatch", "indexed_not_catalogued",
          "catalogued_not_indexed", "qdrant_unreachable")),
        ("matches the decision it was based on",
         ("date_contradicts_its_decision", "decision_without_document",
          "decision_without_page")),
        ("the document's own name contradicts it",
         ("dated_before_its_reporting_period", "name_year_after_date")),
        ("source metadata contradicts it",
         ("source_field_disagrees_total",)),
        ("precise enough to be about one document",
         ("documents_on_a_crowded_timestamp", "documents_in_migration_window",
          "documents_with_own_timestamp")),
        ("dates stored elsewhere",
         ("document_published_at_populated", "changed_before_published",
          "claim_validity_epoch")),
    ):
        print(f"\n{heading}")
        for check in checks:
            if check.name not in names:
                continue
            flag = "" if not check.is_defect else ("  <-- defect" if check.count else "")
            print(f"  {check.name:36} {check.count:6}{flag}")

    print("\nsource-metadata date fields, per field (unclassified)")
    print(f"  {'field':32} {'present':>8} {'parses':>7} {'differs':>8}  top bundles")
    for key, entry in sorted(per_field.items(), key=lambda kv: -kv[1]["differs"]):
        if not entry["present"]:
            continue
        bundles = ", ".join(f"{b}:{n}" for b, n in
                            sorted(entry["bundles"].items(), key=lambda kv: -kv[1])[:3])
        print(f"  {key:32} {entry['present']:8} {entry['parses']:7} "
              f"{entry['differs']:8}  {bundles}")

    print("\n" + "-" * 78)
    if defects:
        print(f"{len(defects)} check(s) reporting a defect:")
        for check in defects:
            print(f"  {check.name} = {check.count}")
            print(f"      {check.detail}")
            if check.samples:
                print(f"      e.g. {', '.join(check.samples[:3])}")
    else:
        print("no defects reported")


def compare(current: dict[str, Any], baseline: dict[str, Any]) -> int:
    """Diff two snapshots. Non-zero exit when a defect count rose."""
    print("=" * 78)
    print("COMPARISON AGAINST BASELINE")
    print("=" * 78)
    print(f"  {'check':36} {'baseline':>9} {'now':>8} {'delta':>7}")
    regressed = 0
    names = sorted(set(current["checks"]) | set(baseline["checks"]))
    for name in names:
        was = baseline["checks"].get(name, {}).get("count")
        now = current["checks"].get(name, {}).get("count")
        if was is None or now is None:
            print(f"  {name:36} {'-' if was is None else was:>9} "
                  f"{'-' if now is None else now:>8} {'NEW/GONE':>7}")
            continue
        if was == now:
            continue
        is_defect = current["checks"].get(name, {}).get("is_defect", True)
        delta = now - was
        mark = ""
        if is_defect and delta > 0:
            regressed += 1
            mark = "  <-- REGRESSION"
        print(f"  {name:36} {was:9} {now:8} {delta:+7}{mark}")
    if regressed:
        print(f"\n{regressed} defect count(s) rose. Treat as a regression.")
    else:
        print("\nno defect count rose.")
    return 1 if regressed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", metavar="PATH", help="Write a snapshot here.")
    parser.add_argument("--compare", metavar="PATH",
                        help="Diff against a snapshot; non-zero exit on regression.")
    parser.add_argument("--quiet", action="store_true", help="Only print the summary.")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    checks, per_field = run()
    current = snapshot(checks, per_field)
    if not args.quiet:
        print_report(checks, per_field)

    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(current, handle, indent=1, sort_keys=True)
        print(f"\nwrote {args.json}")

    if args.compare:
        with open(args.compare, encoding="utf-8") as handle:
            baseline = json.load(handle)
        print()
        return compare(current, baseline)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
