"""Thematic-areas / non-node extraction test — the "is-this-actually-captured?"
probe for TERI's *Thematic Areas* mega-menu and the rest of the content that is
**not** a Drupal node.

Motivation
----------
Node content (`iter_records` over `DEFAULT_BUNDLES`) is already exercised by the
sibling ``drupal_extraction_test``. This test targets *only* the content that
lives outside node bundles and is therefore easy to miss:

    taxonomy_term/themes          <- the "Thematic Areas" menu (Energy, Environment, …)
    taxonomy_term/extra_pages     <- CSR, Energy Transitions, HFCs, … landing pages
    taxonomy_term/regional_centre <- regional centre descriptions
    block_content/basic           <- homepage / section highlight blocks

It walks the exact extraction path the pipeline uses
(``iter_bundle_records(entity_type=…)`` → ``from_drupal_record`` →
``chunk_drupal_record``) and, crucially, **calls out every point that is in
doubt** — the things my code-review flagged as "may or may not actually work":

    CHECK 1  Schema / silent-skip probe   does sort=-changed & filter[status]=1
                                          400 for taxonomy_term / block_content?
                                          (a 400 → the whole bundle is swallowed
                                          by change_detection's broad except and
                                          silently yields ZERO documents.)
    CHECK 2  Thematic-areas extraction    does taxonomy_term/themes return terms
                                          with real descriptions (body text)?
    CHECK 3  Menu ↔ taxonomy coverage     is every "Thematic Areas" menu label
                                          backed by a fetched term? (what you asked)
    CHECK 4  Hierarchy gap                the menu is a tree (Energy › …). Do we
                                          keep the parent→child link, or flatten it?
    CHECK 5  Downstream ingestability     do these records survive canonical +
                                          chunking, i.e. produce retrievable chunks?
    CHECK 6  Block boilerplate filter     block_content/basic: how many survive the
                                          drupal_block_min_chars filter vs dropped?
    CHECK 7  Theme→content association    do content nodes carry their theme(s) in
                                          `categories`? (and confirm `news` doesn't)
    CHECK 8  Change-detection wiring       end-to-end (DB-free): does
                                          detect_drupal_changes actually EMIT these
                                          as source_type="website" documents?

Everything hits the **live** JSON:API (``DRUPAL_JSONAPI_BASE``, default
teriin.org). No MySQL / Qdrant / Azure needed — CHECK 8 stubs the state store so
it runs DB-free. Results (git-ignored) are written under ``results/``:

    results/report.md     human-readable verdict report + DOUBTS summary
    results/report.json   the same, machine-readable
    results/themes.json    every fetched theme term (name, body chars, url, parent)
    results/blocks.json    every fetched block (kept/dropped + why)

Usage
-----
    python -m app.local_tests.thematic_areas_test.run
    python -m app.local_tests.thematic_areas_test.run --limit 3   # smaller assoc. sample
"""

from __future__ import annotations

import json
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- make the repo importable and keep Windows stdout from choking on text ---
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
    pass

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

# The "Thematic Areas" menu as a visitor sees it (screenshot + doc §9). Sub-items
# are the › fly-outs. We check every one of these is backed by a fetched term.
MENU_TOP: tuple[str, ...] = (
    "Sustainable Agriculture",
    "Climate Change",
    "Energy",
    "Environment",
    "Sustainable Habitat",
    "Environment and Public Health",
    "Resources and Sustainable Development",
    # below-the-fold / other top-level areas (doc §9)
    "Environment Education",
    "TERI Knowledge Resource Centre",
    "Green Shipping",
    "Corporate Social Responsibility",
    "World Sustainable Development Summit",
)
MENU_CHILDREN: dict[str, tuple[str, ...]] = {
    "Energy": (
        "Electricity & Renewables", "Energy Access",
        "Energy Assessment & Modelling", "Energy Efficiency",
    ),
    "Environment": ("Air", "Forest & Biodiversity", "Land", "Microbes", "Waste", "Water"),
    "Sustainable Habitat": ("Buildings", "Cities", "Transport"),
    "Resources and Sustainable Development": (
        "Centre for Sustainable Development Research",
        "Resource Efficiency & Governance",
    ),
}

# Content bundles whose theme relationship should surface in `categories`.
# `news` is included precisely to demonstrate it has NO theme field (doc §9).
ASSOC_BUNDLES: tuple[str, ...] = (
    "research_papers", "policy_brief", "events", "article",
    "feature_articles", "news",
)

PASS, WARN, DOUBT, FAIL = "PASS", "WARN", "DOUBT", "FAIL"


@dataclass
class Check:
    id: str
    title: str
    verdict: str = PASS
    summary: str = ""
    detail: list[str] = field(default_factory=list)
    doubts: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "verdict": self.verdict,
            "summary": self.summary, "detail": self.detail,
            "doubts": self.doubts, "data": self.data,
        }


def _norm(value: str) -> str:
    """Normalise a label for matching: lowercase, & → and, drop punctuation."""
    v = (value or "").lower().replace("&", " and ")
    v = re.sub(r"[^a-z0-9]+", " ", v)
    return re.sub(r"\s+", " ", v).strip()


def _label_matches(label: str, candidates: dict[str, str]) -> str | None:
    """Return the vocab a normalised label is found in, else None. `candidates`
    maps normalised term name -> vocab bundle."""
    n = _norm(label)
    if n in candidates:
        return candidates[n]
    # substring both ways ("environment public health" ⊂ term / vice-versa)
    for term_n, vocab in candidates.items():
        if n and (n in term_n or term_n in n):
            return vocab
    return None


# --------------------------------------------------------------------------- #
# Low-level JSON:API helpers (raw, so we can probe params the extractor sends)
# --------------------------------------------------------------------------- #

def _raw_get(session, url: str, params: dict, timeout: int) -> tuple[int | None, dict | None, str | None]:
    try:
        resp = session.get(url, params=params, timeout=timeout)
        status = resp.status_code
        try:
            body = resp.json()
        except ValueError:
            body = None
        return status, body, None
    except Exception as exc:  # network / TLS / timeout
        return None, None, f"{type(exc).__name__}: {exc}"


# --------------------------------------------------------------------------- #
# CHECK 1 — schema / silent-skip probe
# --------------------------------------------------------------------------- #

def check_schema(session, base: str, timeout: int) -> Check:
    """The extractor always sends sort=-changed & filter[status]=1. If a resource
    lacks either field JSON:API returns 400 and change_detection's broad `except`
    swallows the whole bundle → 0 documents, no error surfaced. Prove it works."""
    c = Check("1", "Schema / silent-skip probe (sort=-changed, filter[status]=1)")
    resources = [
        ("taxonomy_term", "themes"),
        ("taxonomy_term", "extra_pages"),
        ("taxonomy_term", "regional_centre"),
        ("block_content", "basic"),
    ]
    for entity_type, bundle in resources:
        url = f"{base}/{entity_type}/{bundle}"
        exact = {"page[limit]": 1, "filter[status]": 1, "sort": "-changed"}
        status, body, err = _raw_get(session, url, exact, timeout)
        if err:
            c.detail.append(f"  {entity_type}/{bundle}: network error — {err}")
            c.verdict = FAIL
            c.doubts.append(f"{entity_type}/{bundle}: could not reach JSON:API ({err}).")
            continue
        if status == 200:
            n = len((body or {}).get("data") or [])
            c.detail.append(
                f"  {entity_type}/{bundle}: 200 with exact extractor params "
                f"(sample returned {n} record) — OK, no silent-skip."
            )
            continue
        # 400/406 — localise which parameter is unsupported
        c.verdict = FAIL if status in (400, 404) else max_verdict(c.verdict, WARN)
        breakdown = []
        for name, p in (
            ("sort=-changed", {"page[limit]": 1, "sort": "-changed"}),
            ("filter[status]=1", {"page[limit]": 1, "filter[status]": 1}),
            ("plain", {"page[limit]": 1}),
        ):
            s, _b, _e = _raw_get(session, url, p, timeout)
            breakdown.append(f"{name}→{s}")
        c.detail.append(
            f"  {entity_type}/{bundle}: exact params returned HTTP {status}! "
            f"param isolation: {', '.join(breakdown)}"
        )
        c.doubts.append(
            f"{entity_type}/{bundle} returns HTTP {status} for the exact params "
            f"the extractor sends — change_detection would silently skip it "
            f"(0 documents). See change_detection.py:319 broad except."
        )
    if c.verdict == PASS:
        c.summary = "All 4 non-node resources answer the extractor's exact params with 200."
    else:
        c.summary = "At least one non-node resource rejects the extractor's params — silent-skip risk is LIVE."
    return c


def max_verdict(a: str, b: str) -> str:
    order = {PASS: 0, WARN: 1, DOUBT: 2, FAIL: 3}
    return a if order[a] >= order[b] else b


# --------------------------------------------------------------------------- #
# CHECK 2 — thematic-areas extraction (the core)
# --------------------------------------------------------------------------- #

def check_themes_extraction(session) -> tuple[Check, list]:
    from app.ingestion.extractors.drupal_extractor import iter_bundle_records

    c = Check("2", "Thematic-areas extraction (taxonomy_term/themes)")
    records = []
    try:
        for rec in iter_bundle_records(session, "themes", entity_type="taxonomy_term"):
            records.append(rec)
    except Exception as exc:
        c.verdict = FAIL
        c.summary = f"iter_bundle_records(themes) raised: {type(exc).__name__}: {exc}"
        c.doubts.append("themes fetch raised — thematic areas would NOT be extracted at all.")
        c.detail.append(traceback.format_exc())
        return c, records

    empty_body = [r for r in records if not (r.body or "").strip()]
    no_url = [r for r in records if not r.url]
    bodies = [len((r.body or "").strip()) for r in records]
    c.data = {
        "term_count": len(records),
        "with_description": len(records) - len(empty_body),
        "empty_description": len(empty_body),
        "no_url": len(no_url),
        "body_chars_min": min(bodies) if bodies else 0,
        "body_chars_max": max(bodies) if bodies else 0,
    }
    c.detail.append(f"  fetched {len(records)} theme terms")
    c.detail.append(
        f"  descriptions: {c.data['with_description']} non-empty, "
        f"{len(empty_body)} empty · body chars {c.data['body_chars_min']}–{c.data['body_chars_max']}"
    )
    if records:
        c.detail.append("  sample:")
        for r in sorted(records, key=lambda x: -len(x.body or ""))[:3]:
            c.detail.append(f"    · {r.title!r} — {len((r.body or '').strip())} body chars — url={r.url or '—'}")

    if not records:
        c.verdict = FAIL
        c.summary = "themes returned 0 terms — thematic areas are NOT being extracted."
        c.doubts.append("taxonomy_term/themes returned 0 records.")
    else:
        c.summary = f"{len(records)} theme terms extracted; {c.data['with_description']} carry description prose."
        if empty_body:
            c.verdict = WARN
            c.doubts.append(
                f"{len(empty_body)} theme term(s) have an EMPTY description → they "
                f"ingest as title-only docs (0 retrievable body): "
                f"{', '.join(r.title for r in empty_body[:8])}"
            )
        if no_url:
            c.verdict = max_verdict(c.verdict, WARN)
            c.doubts.append(f"{len(no_url)} theme term(s) have no path alias (url=None) — citations fall back to bundle/uuid.")
    return c, records


# --------------------------------------------------------------------------- #
# CHECK 3 — menu ↔ taxonomy coverage (what you asked for)
# --------------------------------------------------------------------------- #

def check_menu_coverage(session, theme_records: list) -> Check:
    from app.ingestion.extractors.drupal_extractor import iter_bundle_records

    c = Check("3", "Menu ↔ taxonomy coverage (every 'Thematic Areas' label backed by a term?)")

    # Build normalised name -> vocab map from themes (+ extra_pages, which holds
    # some menu landing pages like CSR).
    candidates: dict[str, str] = {}
    for r in theme_records:
        if r.title:
            candidates.setdefault(_norm(r.title), "themes")
    extra_titles: list[str] = []
    try:
        for rec in iter_bundle_records(session, "extra_pages", entity_type="taxonomy_term"):
            if rec.title:
                candidates.setdefault(_norm(rec.title), "extra_pages")
                extra_titles.append(rec.title)
    except Exception as exc:
        c.detail.append(f"  (extra_pages fetch failed: {type(exc).__name__}: {exc})")

    matched, missing = [], []
    for label in MENU_TOP:
        vocab = _label_matches(label, candidates)
        if vocab:
            matched.append((label, vocab))
        else:
            missing.append(label)
    c.detail.append(f"  top-level menu labels checked: {len(MENU_TOP)}")
    for label, vocab in matched:
        c.detail.append(f"    ✓ {label}  → {vocab}")
    for label in missing:
        c.detail.append(f"    ✗ {label}  → NOT found in themes/extra_pages")

    # sub-items (fly-outs)
    child_missing = []
    for parent, kids in MENU_CHILDREN.items():
        for kid in kids:
            if not _label_matches(kid, candidates):
                child_missing.append(f"{parent} › {kid}")
    if child_missing:
        c.detail.append(f"  sub-items not matched to a term: {len(child_missing)}")
        for cm in child_missing:
            c.detail.append(f"    ✗ {cm}")

    c.data = {
        "top_matched": len(matched), "top_total": len(MENU_TOP),
        "top_missing": missing, "child_missing": child_missing,
    }
    if missing or child_missing:
        c.verdict = DOUBT
        c.summary = (
            f"{len(matched)}/{len(MENU_TOP)} top-level labels backed by a term; "
            f"{len(missing)} top + {len(child_missing)} sub unmatched."
        )
        if missing:
            c.doubts.append(
                "These menu labels are NOT matched to any themes/extra_pages term, "
                "so this extraction path does not capture their landing content: "
                + ", ".join(missing)
            )
        if child_missing:
            c.doubts.append(
                "Menu sub-items not matched to a term (naming drift or different "
                "vocab): " + ", ".join(child_missing)
            )
    else:
        c.summary = f"All {len(MENU_TOP)} top-level + sub menu labels map to a fetched term."
    return c


# --------------------------------------------------------------------------- #
# CHECK 4 — hierarchy gap (parent → child)
# --------------------------------------------------------------------------- #

def check_hierarchy(session, base: str, timeout: int, theme_records: list) -> Check:
    c = Check("4", "Theme hierarchy (parent → child tree) capture")
    url = f"{base}/taxonomy_term/themes"
    params = {"page[limit]": 50, "filter[status]": 1, "include": "parent"}
    status, body, err = _raw_get(session, url, params, timeout)
    if err or status != 200 or not body:
        c.verdict = WARN
        c.summary = f"Could not fetch themes with include=parent (status={status}, err={err})."
        return c

    included = {(i["type"], i["id"]): i for i in body.get("included", [])}
    data = body.get("data") or []
    top, children = 0, 0
    child_examples = []
    for term in data:
        name = (term.get("attributes", {}) or {}).get("name")
        pdata = ((term.get("relationships", {}) or {}).get("parent", {}) or {}).get("data")
        refs = pdata if isinstance(pdata, list) else ([pdata] if pdata else [])
        parent_names = []
        for ref in refs:
            ent = included.get((ref.get("type"), ref.get("id")))
            pname = (ent or {}).get("attributes", {}).get("name") if ent else None
            if pname:  # a real parent term (not the virtual root)
                parent_names.append(pname)
        if parent_names:
            children += 1
            if len(child_examples) < 8:
                child_examples.append(f"{parent_names[0]} › {name}")
        else:
            top += 1

    # Does OUR extraction keep the parent link? _resolve_relationships only keeps
    # field_* relationships, and taxonomy's parent is named 'parent' → dropped.
    meta_has_parent = any(
        any("parent" in k.lower() for k in (r.metadata or {})) for r in theme_records
    )
    c.data = {
        "top_level_terms": top, "child_terms": children,
        "extraction_keeps_parent": meta_has_parent,
        "child_examples": child_examples,
    }
    c.detail.append(f"  Drupal exposes a tree: {top} top-level, {children} child terms.")
    c.detail += [f"    · {ex}" for ex in child_examples]
    c.detail.append(
        f"  extraction metadata contains a parent key? {meta_has_parent} "
        f"(_resolve_relationships keeps only field_* rels; 'parent' is dropped)"
    )
    if children and not meta_has_parent:
        c.verdict = DOUBT
        c.summary = (
            f"Drupal has a {children}-child tree, but extraction flattens it — "
            f"the parent→child link is NOT stored."
        )
        c.doubts.append(
            f"Theme hierarchy is lost: {children} sub-themes (e.g. "
            f"{child_examples[0] if child_examples else 'Air › …'}) are kept as flat "
            f"records with no parent. 'What falls under Environment?' is not "
            f"structurally answerable. Fix: capture the `parent` relationship."
        )
    else:
        c.summary = f"{top} top-level / {children} child terms; parent link captured={meta_has_parent}."
    return c


# --------------------------------------------------------------------------- #
# CHECK 5 — downstream ingestability (canonical + chunking)
# --------------------------------------------------------------------------- #

def check_ingestability(session, theme_records: list) -> Check:
    from app.ingestion.canonical import from_drupal_record
    from app.ingestion.chunker import chunk_drupal_record
    from app.ingestion.extractors.drupal_extractor import iter_bundle_records

    c = Check("5", "Downstream ingestability (canonical → chunking → retrievable chunks)")

    def _run_over(label: str, recs: list) -> dict:
        zero_chunk, total_child, bad_type, no_entity = [], 0, [], []
        for r in recs:
            try:
                doc = from_drupal_record(r)
                chunks = chunk_drupal_record(r)
            except Exception as exc:
                c.doubts.append(f"{label}: {r.title!r} failed canonical/chunk — {type(exc).__name__}: {exc}")
                c.verdict = FAIL
                continue
            children = [ch for ch in chunks if not ch.is_parent]
            total_child += len(children)
            if not children:
                zero_chunk.append(r.title or r.uuid)
            if doc.source_type != "website":
                bad_type.append((r.title, doc.source_type))
            if (r.metadata or {}).get("entity_type") is None:
                no_entity.append(r.title)
        return {
            "records": len(recs), "child_chunks": total_child,
            "zero_chunk": zero_chunk, "bad_source_type": bad_type,
            "missing_entity_type": no_entity,
        }

    themes_res = _run_over("themes", theme_records)
    c.data["themes"] = themes_res
    c.detail.append(
        f"  themes: {themes_res['records']} recs → {themes_res['child_chunks']} child chunks; "
        f"{len(themes_res['zero_chunk'])} produced 0 chunks."
    )

    # also blocks + regional_centre + extra_pages (small)
    for bundle, etype in (("regional_centre", "taxonomy_term"), ("extra_pages", "taxonomy_term")):
        try:
            recs = list(iter_bundle_records(session, bundle, entity_type=etype))
        except Exception as exc:
            c.detail.append(f"  {bundle}: fetch failed — {type(exc).__name__}: {exc}")
            continue
        res = _run_over(bundle, recs)
        c.data[bundle] = res
        c.detail.append(
            f"  {bundle}: {res['records']} recs → {res['child_chunks']} child chunks; "
            f"{len(res['zero_chunk'])} produced 0 chunks."
        )

    all_zero = sum(len(v.get("zero_chunk", [])) for v in c.data.values())
    all_bad = sum(len(v.get("bad_source_type", [])) for v in c.data.values())
    all_missing = sum(len(v.get("missing_entity_type", [])) for v in c.data.values())
    if all_bad:
        c.verdict = max_verdict(c.verdict, WARN)
        c.doubts.append(f"{all_bad} record(s) got a source_type other than 'website'.")
    if all_missing:
        c.verdict = max_verdict(c.verdict, WARN)
        c.doubts.append(
            f"{all_missing} non-node record(s) lack an 'entity_type' metadata tag — "
            f"retrieval/citation can't distinguish them from nodes."
        )
    if all_zero and c.verdict == PASS:
        c.verdict = WARN
        c.doubts.append(f"{all_zero} non-node record(s) produced 0 chunks (title-only) → no retrievable body.")
    c.summary = c.summary or (
        f"Non-node records chunk into retrievable content "
        f"(themes → {themes_res['child_chunks']} child chunks)."
    )
    return c


# --------------------------------------------------------------------------- #
# CHECK 6 — block boilerplate filter
# --------------------------------------------------------------------------- #

def check_blocks(session) -> tuple[Check, list]:
    from app.config import get_settings
    from app.ingestion.extractors.drupal_extractor import iter_bundle_records

    c = Check("6", "Custom blocks (block_content/basic) — boilerplate filter")
    min_chars = get_settings().drupal_block_min_chars
    records = []
    try:
        records = list(iter_bundle_records(session, "basic", entity_type="block_content"))
    except Exception as exc:
        c.verdict = FAIL
        c.summary = f"block_content/basic fetch raised: {type(exc).__name__}: {exc}"
        c.doubts.append("Custom blocks would NOT be extracted (fetch raised).")
        return c, records

    kept, dropped = [], []
    for r in records:
        # mirror change_detection.py: drop short blocks that carry no PDF
        if len((r.body or "").strip()) < min_chars and not r.files:
            dropped.append(r)
        else:
            kept.append(r)
    with_pdf = [r for r in kept if r.files]
    c.data = {
        "total": len(records), "kept": len(kept), "dropped": len(dropped),
        "min_chars": min_chars, "kept_with_pdf": len(with_pdf),
    }
    c.detail.append(
        f"  {len(records)} blocks fetched · kept {len(kept)} / dropped {len(dropped)} "
        f"(threshold={min_chars} chars) · {len(with_pdf)} kept blocks carry a PDF link"
    )
    c.summary = f"{len(kept)}/{len(records)} blocks pass the {min_chars}-char boilerplate filter."
    if not records:
        c.verdict = WARN
        c.doubts.append("block_content/basic returned 0 blocks — homepage/section highlight prose not captured.")
    return c, records


# --------------------------------------------------------------------------- #
# CHECK 7 — theme → content association
# --------------------------------------------------------------------------- #

def check_association(session, limit: int) -> Check:
    from app.ingestion.canonical import from_drupal_record
    from app.ingestion.extractors.drupal_extractor import iter_bundle_records

    c = Check("7", "Theme → content association (categories on content nodes)")
    for bundle in ASSOC_BUNDLES:
        sampled, with_cat, theme_fields = 0, 0, set()
        try:
            for rec in iter_bundle_records(session, bundle, entity_type="node"):
                sampled += 1
                doc = from_drupal_record(rec)
                if doc.categories:
                    with_cat += 1
                theme_fields |= {k for k in (rec.metadata or {}) if "theme" in k.lower()}
                if sampled >= limit:
                    break
        except Exception as exc:
            c.detail.append(f"  {bundle}: fetch failed — {type(exc).__name__}: {exc}")
            continue
        c.data[bundle] = {
            "sampled": sampled, "with_categories": with_cat,
            "theme_fields": sorted(theme_fields),
        }
        note = f"theme field(s): {', '.join(sorted(theme_fields)) or 'NONE'}"
        c.detail.append(f"  {bundle}: {with_cat}/{sampled} records have categories · {note}")
        if bundle == "news" and not theme_fields:
            # Regression guard: docs §9 (corrected 2026-07-07) records that news
            # carries field_news_themes and resolves into categories. If it ever
            # stops, surface it rather than passing silently.
            c.verdict = max_verdict(c.verdict, WARN)
            c.doubts.append(
                "`news` has NO theme field in this sample — docs §9 expects "
                "`field_news_themes`. Either a regression or a sampling miss."
            )
        elif sampled and not with_cat and theme_fields:
            c.verdict = max_verdict(c.verdict, WARN)
            c.doubts.append(
                f"{bundle}: has theme field(s) {sorted(theme_fields)} but 0 sampled "
                f"records resolved into `categories` — check field_*→categories mapping."
            )
    if c.verdict == PASS:
        c.summary = "All sampled content bundles (incl. `news`) resolve their theme(s) into `categories`."
    else:
        c.summary = "Theme→content association works for most bundles; see doubts."
    return c


# --------------------------------------------------------------------------- #
# CHECK 8 — change-detection wiring (end-to-end, DB-free)
# --------------------------------------------------------------------------- #

def check_wiring() -> Check:
    """Run the REAL detect_drupal_changes over ONLY the non-node sources, DB-free
    (stub state.load), and confirm both halves of the pipeline contract:
      (a) it EMITS source_type='website' documents for themes / extra_pages /
          regional_centre / basic, and
      (b) delete-reconciliation now PURGES a stale non-node document (a theme that
          no longer exists live) when reconcile_deletes=True."""
    c = Check("8", "Change-detection wiring + delete reconciliation (DB-free)")

    import app.ingestion.change_detection as cd
    import app.ingestion.state as state_mod
    import app.ingestion.extractors.drupal_extractor as dx
    from app.ingestion.state import StateRecord

    orig_load = state_mod.load
    orig_bundles = dx.DEFAULT_BUNDLES

    def _run(prior_by_type: dict, reconcile: bool) -> list:
        # state.load(source_type) → seeded prior for that type ({} = nothing yet)
        state_mod.load = lambda st, *_a, **_k: dict(prior_by_type.get(st, {}))
        dx.DEFAULT_BUNDLES = ()  # skip the ~8k node crawl; only non-node sources
        out = []
        for i, rec in enumerate(cd.detect_drupal_changes(reconcile_deletes=reconcile)):
            out.append(rec)
            if i > 5000:  # safety cap
                break
        return out

    try:
        # (a) emission — no prior, so every live record reads as NEW
        emitted = _run({}, False)
        by_bundle: dict[str, int] = {}
        by_source_type: dict[str, int] = {}
        for rec in emitted:
            by_bundle[rec.bundle or "?"] = by_bundle.get(rec.bundle or "?", 0) + 1
            by_source_type[rec.source_type] = by_source_type.get(rec.source_type, 0) + 1

        # (b) reconciliation — seed a stale 'themes' doc that no longer exists live
        ghost = "ghost-theme-0000-0000-0000-000000000000"
        stale = StateRecord(
            document_id=ghost, source_type="website",
            source_key="themes/ghost", fingerprint="x", bundle="themes",
        )
        reconciled = _run({"website": {ghost: stale}}, True)
        ghost_deleted = any(
            r.status.value == "deleted" and r.document_id == ghost for r in reconciled
        )
    except Exception as exc:
        c.verdict = FAIL
        c.summary = f"detect_drupal_changes raised: {type(exc).__name__}: {exc}"
        c.detail.append(traceback.format_exc())
        return c
    finally:
        state_mod.load = orig_load
        dx.DEFAULT_BUNDLES = orig_bundles

    c.data = {
        "by_bundle": by_bundle, "by_source_type": by_source_type,
        "emitted": len(emitted), "ghost_deleted": ghost_deleted,
    }
    c.detail.append(f"  emitted {len(emitted)} ChangeRecords from non-node sources")
    c.detail.append(f"  by source_type: {by_source_type}")
    c.detail.append(f"  by bundle: {by_bundle}")
    c.detail.append(
        f"  reconcile: stale 'themes' ghost doc "
        f"{'PURGED (DELETED emitted)' if ghost_deleted else 'NOT purged'}"
    )

    missing = {"themes", "extra_pages", "regional_centre", "basic"} - set(by_bundle)
    if missing:
        c.verdict = FAIL
        c.summary = f"detect_drupal_changes did NOT emit: {', '.join(sorted(missing))}."
        c.doubts.append(
            f"These non-node sources produced 0 ChangeRecords: {', '.join(sorted(missing))} "
            f"— they are declared but not reaching the pipeline."
        )
    elif not ghost_deleted:
        c.verdict = FAIL
        c.summary = "Non-node sources emit, but a stale theme was NOT purged on reconcile."
        c.doubts.append(
            "reconcile_deletes=True did not emit a DELETED record for a stale "
            "taxonomy document — non-node deletes are not reconciled."
        )
    else:
        c.summary = (
            f"All non-node sources flow through as documents "
            f"({by_source_type.get('website', 0)} website + "
            f"{by_source_type.get('pdf_attachment', 0)} in-body PDF); stale non-node "
            f"docs are purged when reconcile_deletes=True."
        )
    return c


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

_BADGE = {PASS: "✅ PASS", WARN: "🟡 WARN", DOUBT: "🟠 DOUBT", FAIL: "🔴 FAIL"}


def _write_report(checks: list[Check], elapsed: float, base: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "report.json").write_text(
        json.dumps(
            {
                "jsonapi_base": base,
                "elapsed_seconds": round(elapsed, 1),
                "checks": [c.as_dict() for c in checks],
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Thematic-areas / non-node extraction test — report",
        "",
        f"- JSON:API base: `{base}`",
        f"- run time: {elapsed:.1f}s",
        f"- checks: {len(checks)}",
        "",
        "## Verdict summary",
        "",
        "| # | Check | Verdict | Summary |",
        "| - | ----- | ------- | ------- |",
    ]
    for c in checks:
        summ = (c.summary or "").replace("|", r"\|")
        lines.append(f"| {c.id} | {c.title} | {_BADGE[c.verdict]} | {summ} |")

    # DOUBTS section — the direct answer to "which things are in doubt"
    lines += ["", "## 🟠 What is in doubt / needs attention", ""]
    any_doubt = False
    for c in checks:
        if not c.doubts:
            continue
        any_doubt = True
        lines.append(f"**Check {c.id} — {c.title}** ({_BADGE[c.verdict]})")
        for d in c.doubts:
            lines.append(f"- {d}")
        lines.append("")
    if not any_doubt:
        lines.append("_No doubts surfaced — everything the menu shows is captured and wired._")

    lines += ["", "## Detail", ""]
    for c in checks:
        lines.append(f"### Check {c.id} — {c.title}  {_BADGE[c.verdict]}")
        lines.append("")
        lines.append(c.summary or "")
        lines.append("")
        lines += [f"    {d}" for d in c.detail]
        lines.append("")
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _dump(name: str, obj: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    limit = 5
    for i, a in enumerate(argv):
        if a == "--limit" and i + 1 < len(argv):
            limit = int(argv[i + 1])
        elif a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])

    from app.config import get_settings
    from app.ingestion.extractors.drupal_extractor import _build_session

    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    timeout = settings.drupal_request_timeout
    session = _build_session(settings.drupal_max_retries)

    print(f"Thematic-areas / non-node extraction test")
    print(f"  JSON:API : {base}")
    print(f"  results  : {RESULTS}")
    print(f"  assoc.limit: {limit} records/bundle\n")

    checks: list[Check] = []
    start = time.perf_counter()
    try:
        c1 = check_schema(session, base, timeout); _p(c1); checks.append(c1)
        c2, themes = check_themes_extraction(session); _p(c2); checks.append(c2)
        _dump("themes.json", [
            {"title": r.title, "url": r.url, "uuid": r.uuid,
             "body_chars": len((r.body or "").strip()),
             "metadata_keys": sorted((r.metadata or {}).keys())}
            for r in themes
        ])
        c3 = check_menu_coverage(session, themes); _p(c3); checks.append(c3)
        c4 = check_hierarchy(session, base, timeout, themes); _p(c4); checks.append(c4)
        c5 = check_ingestability(session, themes); _p(c5); checks.append(c5)
        c6, blocks = check_blocks(session); _p(c6); checks.append(c6)
        _dump("blocks.json", [
            {"title": r.title, "body_chars": len((r.body or "").strip()),
             "files": [f.url for f in r.files]}
            for r in blocks
        ])
        c7 = check_association(session, limit); _p(c7); checks.append(c7)
        c8 = check_wiring(); _p(c8); checks.append(c8)
    finally:
        session.close()

    elapsed = time.perf_counter() - start
    _write_report(checks, elapsed, base)

    worst = PASS
    for c in checks:
        worst = max_verdict(worst, c.verdict)
    doubts = sum(len(c.doubts) for c in checks)
    print(f"\n{'='*70}")
    print(f"Overall: {_BADGE[worst]} · {doubts} doubt(s) flagged · {elapsed:.1f}s")
    print(f"Report : {RESULTS / 'report.md'}")
    return 0 if worst in (PASS, WARN) else 2


def _p(c: Check) -> None:
    print(f"{_BADGE[c.verdict]}  Check {c.id} — {c.title}")
    print(f"        {c.summary}")
    for d in c.doubts:
        print(f"        ⚠ {d}")


if __name__ == "__main__":
    raise SystemExit(main())
