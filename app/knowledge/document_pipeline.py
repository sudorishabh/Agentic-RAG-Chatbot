"""The knowledge layer for one document.

``scripts.build_knowledge`` runs the same stages over the whole corpus. This
runs them over a single document that ingestion has just indexed, so a new
document contributes knowledge without waiting for the next corpus pass. The
two share every stage implementation — nothing is extracted, resolved,
validated or projected here — and they share the reporting model, so a stage
cannot mean one thing in one orchestrator and something else in the other.

What is deliberately NOT here
-----------------------------
Four stages the corpus builder runs are absent, and their absence is the design
rather than an omission:

``seed``          reads the whole catalog to mint canonical entities.
``acronyms``      pairs corpus-wide glosses against seeded names.
``ambiguity``     a single global ``UPDATE``; its correctness depends on seeing
                  every alias at once. The moment a second "Sharma" exists the
                  shared surface must stop autolinking *for everyone*, and a
                  per-document pass cannot know that.
``pi-promotion``  weighs a name against the whole PI population.

Running any of them per document would either repeat global work once per
document or, worse, take a global decision on partial evidence — which is how
false merges get committed. So a newly ingested project may have **no canonical
PROJECT entity yet**, and its CMS claims are refused as ``unknown_subject``
until the next ``scripts.build_knowledge``. That refusal is recorded rather than
silent, and it is the correct answer: the alternative is inventing an identity.

Fail-open, and where that is enforced
-------------------------------------
This module does not know about ingestion and never touches Qdrant. It raises
only on a programming error; a store or model failure is recorded on the report
and the run continues where it safely can. The guarantee that a knowledge
failure cannot fail an *ingestion* is enforced one layer up, in
:mod:`app.ingestion.knowledge_sync`, which is the only thing ingestion calls.

Idempotency
-----------
Every write is idempotent on a deterministic key — ``INSERT IGNORE`` on a
mention span, upsert on a decision span, upsert on ``claim_id``, ``MERGE`` on a
graph key — so a retry re-derives rather than duplicates. The stage adds no
bookkeeping of its own beyond the run row, which is written last precisely so
its absence marks a run that never finished.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Sequence

from app.knowledge.reporting import (
    STATUS_OK,
    Stage,
    collect_errors,
    stage_timer,
    status_for,
)

logger = logging.getLogger(__name__)

# Reported when the wall-clock budget ended a run early.
BUDGET_EXCEEDED = (
    "the stage budget was exhausted; remaining stages were skipped and the run "
    "is retryable — everything already written is valid"
)

# Reported when a project document has no canonical entity yet.
NOT_SEEDED = (
    "this document has no canonical PROJECT entity yet; seeding is a global "
    "pass (scripts.build_knowledge), and its claims will be staged once it runs"
)


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ChunkText:
    """One chunk's text, as the knowledge layer needs it.

    Deliberately not ``app.ingestion.chunking.Chunk``: this module must be
    callable from a CLI that reads chunks back out of Qdrant, from tests that
    have neither, and from ingestion that has the real thing. Three shapes, one
    contract.
    """

    chunk_id: str
    text: str
    content_hash: str = ""


@dataclass(frozen=True)
class DocumentInput:
    """A successfully indexed document, as handed to the knowledge stage."""

    document_id: str
    doc_version: int
    chunks: tuple[ChunkText, ...] = ()
    source_type: str = ""
    bundle: str | None = None
    content_hash: str = ""
    raw_meta: dict[str, Any] | None = None
    # Author names, for PERSON corroboration during resolution. Carried on the
    # input rather than looked up, because ingestion already has them on the
    # canonical document and they no longer live in `raw_meta` — the facet
    # `documents_author` holds them now, and reading only the metadata left
    # PERSON resolution permanently uncorroborated.
    authors: tuple[str, ...] = ()
    run_id: str | None = None

    @classmethod
    def from_chunks(
        cls, *, document_id: str, doc_version: int, chunks: Sequence[Any],
        source_type: str = "", bundle: str | None = None,
        content_hash: str = "", raw_meta: dict[str, Any] | None = None,
        authors: Sequence[str] = (), run_id: str | None = None,
    ) -> "DocumentInput":
        """Build from ingestion's chunk objects.

        Parents are dropped: a parent chunk is an assembly of its children's
        text, so extracting from both would double every mention and stage the
        same claim from two spans. This is the same ``is_parent = False`` filter
        ``scripts.build_knowledge`` applies when it scrolls Qdrant.
        """
        texts = tuple(
            ChunkText(
                chunk_id=str(getattr(chunk, "chunk_id", "")),
                text=getattr(chunk, "text", "") or "",
                content_hash=getattr(chunk, "content_hash", "") or "",
            )
            for chunk in chunks
            if not getattr(chunk, "is_parent", False)
            and getattr(chunk, "chunk_id", None)
        )
        return cls(
            document_id=document_id, doc_version=int(doc_version), chunks=texts,
            source_type=source_type, bundle=bundle, content_hash=content_hash,
            raw_meta=raw_meta, authors=tuple(authors or ()), run_id=run_id,
        )

    @property
    def chunk_ids(self) -> set[str]:
        return {c.chunk_id for c in self.chunks}

    @property
    def chunk_texts(self) -> dict[str, str]:
        return {c.chunk_id: c.text for c in self.chunks}


@dataclass(frozen=True)
class StageOptions:
    """What this run is allowed to do. Immutable, so a stage cannot retune it."""

    dry_run: bool = False
    # Mentions and resolution are audit and evaluation material: nothing reads
    # those tables at query time, and CMS claim extraction does not depend on
    # them. Off by default for the same reason `--with-mentions` is off in the
    # corpus builder — it is by far the most expensive deterministic stage.
    with_mentions: bool = False
    with_llm_claims: bool | None = None
    with_projection: bool | None = None
    budget_seconds: float | None = None
    llm_max_calls: int | None = None
    min_confidence: float | None = None
    # Fixed "now" for current-state eligibility. Exists so a test can assert on
    # a window without depending on the date it runs.
    as_of: str | None = None

    @classmethod
    def from_settings(cls, **overrides: Any) -> "StageOptions":
        """Defaults from configuration, with explicit overrides on top."""
        from app.config import get_settings

        settings = get_settings()
        base = {
            "with_llm_claims": bool(settings.claim_extraction_enabled),
            "with_projection": bool(settings.knowledge_project_per_document),
            "budget_seconds": float(settings.knowledge_stage_budget_seconds),
            "llm_max_calls": int(settings.knowledge_llm_max_calls_per_document),
            "min_confidence": float(settings.claim_min_confidence),
        }
        base.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**base)


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

@dataclass
class StageReport:
    """What one document's knowledge run did.

    Field names match ``app.catalog.knowledge_runs.COUNTER_COLUMNS`` so the
    store reads them directly; a counter added here reaches the table by adding
    the column, not by teaching a mapper about it.
    """

    document_id: str
    doc_version: int
    run_id: str | None = None
    status: str = STATUS_OK
    seconds: float = 0.0
    knowledge_version: str = ""

    chunks_seen: int = 0
    chunks_cached: int = 0
    mentions: int = 0
    entities_auto: int = 0
    entities_provisional: int = 0
    entities_ambiguous: int = 0
    entities_unresolved: int = 0
    claims_built: int = 0
    claims_staged: int = 0
    claims_rejected: int = 0
    claims_retracted: int = 0
    pending_predicates: int = 0
    conflicts_disputed: int = 0
    conflicts_superseded: int = 0

    projection_status: str = "skipped"
    projection_version: str | None = None
    projection_edges: int = 0

    rejection_counts: dict[str, int] = field(default_factory=dict)
    stages: list[Stage] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "doc_version": self.doc_version,
            "run_id": self.run_id,
            "status": self.status,
            "seconds": round(self.seconds, 2),
            "knowledge_version": self.knowledge_version,
            "counts": {
                "chunks_seen": self.chunks_seen,
                "chunks_cached": self.chunks_cached,
                "mentions": self.mentions,
                "entities_auto": self.entities_auto,
                "entities_provisional": self.entities_provisional,
                "entities_ambiguous": self.entities_ambiguous,
                "entities_unresolved": self.entities_unresolved,
                "claims_built": self.claims_built,
                "claims_staged": self.claims_staged,
                "claims_rejected": self.claims_rejected,
                "claims_retracted": self.claims_retracted,
                "pending_predicates": self.pending_predicates,
                "conflicts_disputed": self.conflicts_disputed,
                "conflicts_superseded": self.conflicts_superseded,
            },
            "rejection_counts": dict(sorted(self.rejection_counts.items())),
            "projection": {
                "status": self.projection_status,
                "version": self.projection_version,
                "edges": self.projection_edges,
            },
            "stages": [s.as_dict() for s in self.stages],
            "errors": self.errors,
        }


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #

class _Run:
    """One document's pass. Holds the state the stages hand each other."""

    def __init__(self, doc: DocumentInput, options: StageOptions) -> None:
        self.doc = doc
        self.o = options
        self.started = time.monotonic()
        self.stages: list[Stage] = []
        self.report = StageReport(
            document_id=doc.document_id, doc_version=doc.doc_version,
            run_id=doc.run_id, stages=self.stages,
        )
        self.index: Any = None
        self.context: Any = None
        self.gazetteer: Any = None
        self.gazetteer_fingerprint: str | None = None
        self.mentions_by_chunk: dict[str, list[Any]] = {}
        self.decisions_by_chunk: dict[str, list[Any]] = {}
        self.claims_built: list[Any] = []
        self.pending_candidates: list[Any] = []
        self.accepted: list[Any] = []
        self.rejected: list[Any] = []
        # Claims this run retracted. Tracked apart from `touched_claims`
        # because a later staging failure invalidates that set but not these:
        # the retraction already committed, and its edge must still go.
        self.retracted_claims: set[str] = set()
        # Every claim this run may have changed the current-state eligibility
        # of. Retractions and conflict verdicts both belong here, because a
        # claim that lost its edge is as much this run's business as one that
        # gained one.
        self.touched_claims: set[str] = set()

    @property
    def writes(self) -> bool:
        return not self.o.dry_run

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def over_budget(self) -> bool:
        budget = self.o.budget_seconds
        return bool(budget) and self.elapsed >= budget

    def stage(self, name: str, *, skip: bool = False) -> Any:
        return stage_timer(self.stages, name, skip=skip, log=logger)


def process_document(
    doc: DocumentInput, options: StageOptions | None = None
) -> StageReport:
    """Run the knowledge layer for one indexed document. Idempotent."""
    run = _Run(doc, options or StageOptions.from_settings())
    fatal = False
    try:
        _prelude(run)
    except Exception as exc:
        # Nothing has been written and nothing downstream is meaningful without
        # the entity index, so this is the one failure that ends the run rather
        # than one stage of it.
        logger.warning(
            "Knowledge stage could not start for %s: %s", doc.document_id, exc,
            exc_info=True,
        )
        fatal = True
    else:
        for step in (
            _supersede, _mentions, _resolution, _claims, _validate,
            _persist, _conflicts, _project,
        ):
            name = step.__name__.strip("_")
            if run.over_budget():
                with run.stage(name, skip=True) as stage:
                    stage.notes.append(BUDGET_EXCEEDED)
                    stage.fail("budget", BUDGET_EXCEEDED)
                continue
            before = len(run.stages)
            try:
                step(run)
            except Exception as exc:  # pragma: no cover - defence in depth
                # A stage that raises past its own handling costs itself and
                # nothing else: every stage before it has already committed, on
                # its own connection, and the run continues to the next.
                logger.warning(
                    "Knowledge stage %s failed for %s: %s",
                    name, doc.document_id, exc, exc_info=True,
                )
                # Blame the stage the step actually opened. A step that raised
                # before opening one gets a stage of its own rather than an
                # error attributed to whatever ran last.
                if len(run.stages) > before:
                    run.stages[-1].fail(name, exc)
                else:
                    failed = Stage(name=name)
                    failed.fail(name, exc)
                    run.stages.append(failed)

    report = run.report
    report.seconds = run.elapsed
    report.errors = collect_errors(run.stages)
    report.status = status_for(run.stages, fatal=fatal)
    if fatal:
        report.errors = report.errors or [
            {"stage": "prelude", "id": "entity_index", "error": "unavailable"}
        ]
    _record(run)
    logger.info(
        "knowledge_document id=%s v=%s status=%s claims=%s pending=%s proj=%s %.2fs",
        report.document_id, report.doc_version, report.status,
        report.claims_staged, report.pending_predicates,
        report.projection_status, report.seconds,
    )
    return report


# --------------------------------------------------------------------------- #
# 0. Prelude
# --------------------------------------------------------------------------- #

def _prelude(run: _Run) -> None:
    """Load what every later stage resolves against. Writes nothing."""
    from app.knowledge.candidates import context_for_document, get_entity_index
    from app.knowledge.version import knowledge_version

    with run.stage("prelude") as stage:
        run.index = get_entity_index()
        run.context = context_for_document(
            run.doc.document_id, run.doc.raw_meta, authors=run.doc.authors
        )
        if run.o.with_mentions:
            from app.knowledge.gazetteer import gazetteer_version, get_gazetteer

            run.gazetteer = get_gazetteer()
            run.gazetteer_fingerprint = gazetteer_version(run.gazetteer)
        run.report.knowledge_version = knowledge_version(
            gazetteer_fingerprint=run.gazetteer_fingerprint
        )
        run.report.chunks_seen = len(run.doc.chunks)
        stage.counts["entities"] = len(run.index.entities)
        stage.counts["chunks"] = len(run.doc.chunks)


# --------------------------------------------------------------------------- #
# 1. Supersede the previous version
# --------------------------------------------------------------------------- #

def _supersede(run: _Run) -> None:
    """Retire what the previous version of this document left behind.

    Chunk ids are version-scoped (``uuid5(doc|version|suffix)``), so re-indexing
    a document strands everything keyed by them: mentions whose spans point at
    text that no longer exists, decisions about those spans, and — because
    ``claim_id`` embeds the chunk — claims citing evidence nobody can fetch.

    Claims are **retracted, never deleted**: the claim was true of the source as
    it stood, and that history is worth keeping. This is the same treatment
    ``extract_cms.stale_claim_ids`` gives a CMS field that was edited away.
    """
    from app.catalog import assertions as assertion_store
    from app.knowledge.claims import types as t

    first_version = run.doc.doc_version <= 1
    with run.stage("supersede", skip=first_version) as stage:
        if stage.skipped:
            return

        current = run.doc.chunk_ids
        stale = [
            row["claim_id"]
            for row in assertion_store.for_document(run.doc.document_id)
            if row.get("evidence_kind") == t.EVIDENCE_CHUNK
            and row.get("chunk_id") not in current
            and row.get("status") != t.STATUS_RETRACTED
        ]
        stage.counts["stale_claims"] = len(stale)
        run.report.claims_retracted = len(stale)
        # Retracted claims still need projecting: that is how their
        # current-state edge is removed.
        run.retracted_claims.update(stale)
        run.touched_claims.update(stale)

        if not run.writes:
            return
        if stale:
            stage.counts["retracted"] = assertion_store.retract(stale)
        from app.catalog import entities as entity_store
        from app.catalog import mentions as mention_store

        try:
            # Decisions first. The decision log has no document_id — a decision
            # is about a span — so the document's own mention rows are what
            # identify its chunks, and deleting those first would leave nothing
            # to join against.
            stage.counts["decisions_dropped"] = (
                entity_store.delete_decisions_before_version(
                    run.doc.document_id, run.doc.doc_version
                )
            )
            stage.counts["mentions_dropped"] = mention_store.delete_document_mentions(
                run.doc.document_id, before_version=run.doc.doc_version
            )
        except Exception as exc:
            stage.fail("supersede_mentions", exc)


# --------------------------------------------------------------------------- #
# 2. Mentions
# --------------------------------------------------------------------------- #

def _mentions(run: _Run) -> None:
    """Extract mentions per chunk, skipping what the cache already covers."""
    from app.catalog import mentions as mention_store
    from app.knowledge.extract import extract_mentions, extraction_key

    with run.stage("mentions", skip=not run.o.with_mentions) as stage:
        if stage.skipped:
            return
        cached = 0
        found_total = 0
        for chunk in run.doc.chunks:
            if run.over_budget():
                stage.notes.append(BUDGET_EXCEEDED)
                break
            key = (
                extraction_key(chunk.content_hash, run.gazetteer_fingerprint or "")
                if chunk.content_hash else None
            )
            try:
                if key and mention_store.cached_extraction(
                    chunk.content_hash, key
                ) is not None:
                    cached += 1
                    continue
                found = extract_mentions(
                    chunk.text, chunk_id=chunk.chunk_id,
                    document_id=run.doc.document_id, gazetteer=run.gazetteer,
                )
                run.mentions_by_chunk[chunk.chunk_id] = found
                found_total += len(found)
                if run.writes and found:
                    mention_store.save_mentions(
                        found, doc_version=run.doc.doc_version
                    )
            except Exception as exc:
                # One chunk's failure is that chunk's failure. The chunks
                # already written stay written — every writer here commits per
                # call — and the id is reported so the run can be repeated.
                logger.warning(
                    "Mention extraction failed for chunk %s: %s",
                    chunk.chunk_id, exc, exc_info=True,
                )
                stage.fail(chunk.chunk_id, exc)
        stage.counts["cached"] = cached
        stage.counts["mentions"] = found_total
        run.report.chunks_cached = cached
        run.report.mentions = found_total


# --------------------------------------------------------------------------- #
# 3. Resolution
# --------------------------------------------------------------------------- #

def _resolution(run: _Run) -> None:
    """Decide which canonical entity each mention denotes.

    Per chunk, because ``resolve_mentions`` shares co-occurrence context between
    a chunk's mentions. Nothing here mints an entity: an unresolved name leaves
    an ``UNRESOLVED`` decision and no identity, which is the conservative
    direction the resolver is built to fail in.
    """
    from app.catalog import entities as entity_store
    from app.knowledge.resolver import AMBIGUOUS, AUTO, PROVISIONAL, resolve_mentions

    with run.stage("resolution", skip=not run.o.with_mentions) as stage:
        if stage.skipped:
            return
        tally = {AUTO: 0, PROVISIONAL: 0, AMBIGUOUS: 0}
        unresolved = 0
        for chunk_id, mentions in run.mentions_by_chunk.items():
            if not mentions:
                continue
            try:
                decisions = resolve_mentions(mentions, run.index, run.context)
            except Exception as exc:
                logger.warning(
                    "Resolution failed for chunk %s: %s", chunk_id, exc,
                    exc_info=True,
                )
                stage.fail(chunk_id, exc)
                continue
            run.decisions_by_chunk[chunk_id] = decisions
            for decision in decisions:
                if decision.decision in tally:
                    tally[decision.decision] += 1
                else:
                    unresolved += 1
            if run.writes and decisions:
                try:
                    entity_store.save_decisions(decisions)
                except Exception as exc:
                    logger.warning(
                        "Could not save decisions for chunk %s: %s", chunk_id,
                        exc, exc_info=True,
                    )
                    stage.fail(chunk_id, exc)

        run.report.entities_auto = tally[AUTO]
        run.report.entities_provisional = tally[PROVISIONAL]
        run.report.entities_ambiguous = tally[AMBIGUOUS]
        run.report.entities_unresolved = unresolved
        stage.counts.update({
            "auto": tally[AUTO], "provisional": tally[PROVISIONAL],
            "ambiguous": tally[AMBIGUOUS], "unresolved": unresolved,
        })

        # Record the extraction cache only once a chunk has been fully
        # processed. Written here rather than in the mention stage so an
        # interruption between the two re-runs the chunk instead of marking it
        # done on a half-finished pass.
        if run.writes:
            _record_extraction_cache(run, stage)


def _record_extraction_cache(run: _Run, stage: Stage) -> None:
    from app.catalog import mentions as mention_store
    from app.knowledge.extract import EXTRACTOR_VERSION, extraction_key

    recorded = 0
    for chunk in run.doc.chunks:
        if chunk.chunk_id not in run.mentions_by_chunk or not chunk.content_hash:
            continue
        try:
            mention_store.record_extraction(
                chunk.content_hash,
                extraction_key(chunk.content_hash, run.gazetteer_fingerprint or ""),
                EXTRACTOR_VERSION,
                len(run.mentions_by_chunk[chunk.chunk_id]),
            )
            recorded += 1
        except Exception as exc:
            stage.fail(chunk.chunk_id, exc)
    stage.counts["cache_recorded"] = recorded


# --------------------------------------------------------------------------- #
# 4. Claim extraction
# --------------------------------------------------------------------------- #

def _claims(run: _Run) -> None:
    """Build claims from CMS metadata and, when enabled, from chunk text."""
    from app.knowledge.claims import extract_cms

    with run.stage("claims") as stage:
        built: list[Any] = []

        # --- 4a. CMS fields: deterministic, free, and the largest true source.
        if run.doc.bundle is None or extract_cms.is_project_bundle(run.doc.bundle):
            context = extract_cms.CmsClaimContext.from_index(run.index)
            if context.subject_for(run.doc.document_id) is None:
                if extract_cms.is_project_bundle(run.doc.bundle):
                    stage.notes.append(NOT_SEEDED)
            else:
                cms = extract_cms.claims_from_meta(
                    run.doc.document_id, run.doc.raw_meta, context=context
                )
                stage.counts["cms"] = len(cms)
                built.extend(cms)

        # --- 4b. Model-proposed, gated and budgeted.
        built.extend(_llm_claims(run, stage))

        run.claims_built = built
        run.report.claims_built = len(built)
        stage.counts["built"] = len(built)


def _llm_claims(run: _Run, stage: Stage) -> list[Any]:
    """Model-proposed claims for this document's chunks. [] when gated off.

    The model may only reference entities this document's own resolution marked
    canonical, so a provisional identity is unreachable from a prompt — the
    eligibility filter runs before the call, not after it.
    """
    if not run.o.with_llm_claims:
        return []
    from app.knowledge.claims.eligibility import eligible_from_decisions
    from app.knowledge.claims.extract_llm import extract_claims_for_chunk

    budget = run.o.llm_max_calls or 0
    if budget <= 0:
        return []

    out: list[Any] = []
    calls = 0
    texts = run.doc.chunk_texts
    for chunk_id, decisions in run.decisions_by_chunk.items():
        if calls >= budget or run.over_budget():
            stage.notes.append(
                f"model calls stopped at {calls}; the document's remaining "
                "chunks were not examined"
            )
            break
        eligible = eligible_from_decisions(decisions, run.index)
        if not eligible:
            continue
        calls += 1
        try:
            claims, unknown = extract_claims_for_chunk(
                texts.get(chunk_id, ""), chunk_id=chunk_id,
                document_id=run.doc.document_id, eligible=eligible,
                enabled=True, capture_unknown=True,
            )
        except Exception as exc:
            # extract_claims_for_chunk already swallows model failures; this is
            # defence for anything above it.
            stage.fail(chunk_id, exc)
            continue
        out.extend(claims)
        run.pending_candidates.extend(unknown)
    stage.counts["llm_calls"] = calls
    stage.counts["llm"] = len(out)
    stage.counts["unknown_predicates"] = len(run.pending_candidates)
    return out


# --------------------------------------------------------------------------- #
# 5. Validation
# --------------------------------------------------------------------------- #

def _validate(run: _Run) -> None:
    """The gate. Nothing reaches storage without passing every check in it.

    This module gets no say in the rules: a provisional PERSON is refused as
    ``object_not_claim_eligible`` here exactly as it is in the corpus builder,
    and the store — not the claim row — is re-asked whether each entity may
    still carry claims.
    """
    from app.knowledge.claims.validate import dedupe, validate

    with run.stage("validate") as stage:
        built = run.claims_built
        if not built:
            run.accepted = []
            return
        result = validate(
            built,
            index=run.index,
            chunk_texts=run.doc.chunk_texts,
            min_confidence=run.o.min_confidence or 0.0,
        )
        run.accepted = dedupe(result.accepted)
        run.rejected = result.rejected
        run.report.claims_rejected = len(result.rejected)
        run.report.rejection_counts = dict(result.counts)
        stage.counts["accepted"] = len(run.accepted)
        stage.counts["rejected"] = len(result.rejected)
        for code, count in sorted(result.counts.items()):
            stage.counts[f"rejected_{code}"] = count


# --------------------------------------------------------------------------- #
# 6. Persistence
# --------------------------------------------------------------------------- #

def _persist(run: _Run) -> None:
    """Stage accepted claims, record refusals, record pending predicates."""
    from app.catalog import assertions as assertion_store

    with run.stage("persist") as stage:
        candidates = run.pending_candidates
        stage.counts["accepted"] = len(run.accepted)
        stage.counts["pending_predicates"] = len(candidates)
        run.report.pending_predicates = len(candidates)
        run.touched_claims.update(a.claim_id for a in run.accepted)

        if not run.writes:
            run.report.claims_staged = len(run.accepted)
            return

        if run.accepted:
            try:
                run.report.claims_staged = assertion_store.stage(run.accepted)
                stage.counts["staged"] = run.report.claims_staged
            except Exception as exc:
                logger.warning(
                    "Could not stage %s's claims: %s", run.doc.document_id, exc,
                    exc_info=True,
                )
                stage.fail("stage", exc)
                # Nothing downstream can be trusted about claims that are not in
                # the store, so the conflict and projection stages are told to
                # stand down rather than acting on a phantom set.
                run.accepted = []
                # The retractions above committed on their own connection and
                # are still true, so their edges must still be retired; only
                # the claims that failed to stage drop out of scope.
                run.touched_claims = set(run.retracted_claims)

        rejected = run.rejected
        if rejected:
            try:
                stage.counts["rejections_recorded"] = (
                    assertion_store.record_rejections(rejected)
                )
            except Exception as exc:
                stage.fail("rejections", exc)

        if candidates:
            from app.catalog import predicate_candidates as candidate_store
            from app.knowledge.claims.pending import dedupe as dedupe_candidates

            try:
                stage.counts["candidates_recorded"] = candidate_store.record(
                    dedupe_candidates(candidates)
                )
            except Exception as exc:
                stage.fail("predicate_candidates", exc)


# --------------------------------------------------------------------------- #
# 7. Conflicts
# --------------------------------------------------------------------------- #

def _conflicts(run: _Run) -> None:
    """Supersession and dispute verdicts, over this document *and its siblings*.

    Scoping this to one document would be wrong, not merely incomplete. A
    functional predicate's contradictions are inherently cross-document — two
    documents naming different principal investigators for one project is the
    case ``conflicts.detect`` exists for — and a batch holding only this
    document's claims would never see the pair.

    So every ``(subject, predicate)`` this document touched is re-read from the
    store, and detection runs over the union. Statuses are applied **before**
    links are saved: if the run is interrupted between them, the safe residue is
    a suppressed claim missing its audit link, not an unsuppressed claim that
    projects an edge it should not.
    """
    from app.catalog import assertions as assertion_store
    from app.knowledge.claims import conflicts as detector
    from app.knowledge.claims import types as t

    with run.stage("conflicts", skip=not run.accepted) as stage:
        if stage.skipped:
            return

        pairs = {(a.subject_entity_id, a.predicate) for a in run.accepted}
        try:
            sibling_rows = assertion_store.for_subject_predicates(sorted(pairs))
        except Exception as exc:
            stage.fail("siblings", exc)
            sibling_rows = []

        # This run's freshly validated objects win over their stored rows: the
        # store may not have them yet under --dry-run, and where it does they
        # are identical by construction.
        by_id: dict[str, Any] = {
            row["claim_id"]: t.from_row(row) for row in sibling_rows
        }
        by_id.update({a.claim_id: a for a in run.accepted})
        scoped = sorted(by_id.values(), key=lambda a: a.claim_id)
        run.touched_claims.update(by_id)

        report = detector.detect(scoped)
        stage.counts["examined"] = report.examined
        stage.counts["siblings"] = max(0, len(scoped) - len(run.accepted))
        stage.counts["groups"] = report.groups
        stage.counts["disputed"] = len(report.disputed)
        stage.counts["superseded"] = len(report.superseded)
        run.report.conflicts_disputed = len(report.disputed)
        run.report.conflicts_superseded = len(report.superseded)

        if not run.writes:
            return
        if report.status_changes:
            try:
                stage.counts["status_applied"] = assertion_store.apply_status(
                    report.status_changes
                )
            except Exception as exc:
                stage.fail("status", exc)
        if report.links:
            try:
                stage.counts["links_saved"] = assertion_store.save_links(
                    report.links, detector=detector.DETECTOR_VERSION
                )
            except Exception as exc:
                stage.fail("links", exc)


# --------------------------------------------------------------------------- #
# 8. Projection
# --------------------------------------------------------------------------- #

def _project(run: _Run) -> None:
    """Project this document's claims into Neo4j. Fail-open in every direction.

    Scoped, never the whole-corpus pass: ``project()`` finishes by deleting
    every current-state edge it did not re-stamp, which per document would erase
    the rest of the corpus's graph. ``project_claims`` retires by name instead.

    Neo4j is a derived store — everything in it is re-derivable from MySQL — so
    an outage here is a lag, not a loss, and ``project_after_sweep`` or
    ``scripts.project_graph --rebuild`` closes it.
    """
    from app.config import get_settings

    enabled = run.o.with_projection and get_settings().knowledge_enabled
    with run.stage("project", skip=not enabled or not run.touched_claims) as stage:
        if stage.skipped:
            run.report.projection_status = "skipped"
            return
        if not run.writes:
            run.report.projection_status = "skipped"
            stage.notes.append("projection skipped under dry_run")
            return

        from app.core.clients import graph_available

        if not graph_available():
            run.report.projection_status = "unreachable"
            stage.notes.append(
                "Neo4j unreachable; MySQL is authoritative and the graph catches "
                "up at the next project_after_sweep"
            )
            stage.fail("neo4j", "unreachable")
            return

        try:
            from app.knowledge.graph.project import project_claims
            from app.knowledge.graph.schema import ensure_graph_schema

            # Constraints before the first MERGE, the same order
            # scripts.project_graph and build_knowledge use.
            ensure_graph_schema()
            report = project_claims(
                sorted(run.touched_claims), as_of=run.o.as_of
            )
        except Exception as exc:
            logger.warning(
                "Scoped projection failed for %s: %s", run.doc.document_id, exc,
                exc_info=True,
            )
            run.report.projection_status = "failed"
            stage.fail("project", exc)
            return

        edges = sum(
            count for name, count in report.relationships.items()
            if name.endswith("(current)")
        )
        run.report.projection_status = "ok"
        run.report.projection_version = report.projection_version
        run.report.projection_edges = edges
        stage.counts["claims"] = len(run.touched_claims)
        stage.counts["current_edges"] = edges
        for name, count in sorted(report.nodes.items()):
            stage.counts[f"node_{name}"] = count


# --------------------------------------------------------------------------- #
# 9. Observability
# --------------------------------------------------------------------------- #

def _record(run: _Run) -> None:
    """Write the run row. Last, and never fatal.

    Last because a document with no row is precisely what the catch-up sweep
    looks for, so the absence has to mean "did not finish". Never fatal because
    a report that cannot be written must not turn a successful knowledge run
    into a failed one.
    """
    if not run.writes:
        return
    from app.catalog import knowledge_runs

    knowledge_runs.record(run.report)
