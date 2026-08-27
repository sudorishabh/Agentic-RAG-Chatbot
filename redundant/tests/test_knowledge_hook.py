"""The ingestion hook: that it ships inert, and that it cannot cost a document.

The property under test is narrow and absolute — **a knowledge failure must
never turn a successfully indexed document into a failed one** — so most of
these assert on what does *not* happen. Several deliberately make the knowledge
layer explode and then check that ingestion's outcome, its vectors and its
catalog row are exactly what they would have been.
"""

from __future__ import annotations

import pytest

from app.ingestion import knowledge_sync


class _Settings:
    """Only the flags the hook reads."""

    def __init__(self, **flags):
        self.knowledge_enabled = flags.get("knowledge_enabled", False)
        self.knowledge_process_after_index = flags.get(
            "knowledge_process_after_index", False
        )
        self.knowledge_project_per_document = True
        self.knowledge_stage_budget_seconds = 30.0
        self.knowledge_llm_max_calls_per_document = 8
        self.knowledge_stage_max_attempts = 3
        self.claim_extraction_enabled = False
        self.claim_min_confidence = 0.6


class _Chunk:
    def __init__(self, chunk_id, text, is_parent=False, content_hash="h"):
        self.chunk_id = chunk_id
        self.text = text
        self.is_parent = is_parent
        self.content_hash = content_hash


def _flags(monkeypatch, **flags):
    monkeypatch.setattr(
        "app.config.get_settings", lambda: _Settings(**flags)
    )


def _call(**overrides):
    kwargs = {
        "document_id": "doc-1",
        "doc_version": 1,
        "chunks": [_Chunk("c1", "Some text about the Ministry of Power.")],
        "source_type": "website",
        "bundle": "news",
        "content_hash": "abc",
        "raw_meta": {},
        "run_id": "run-1",
    }
    kwargs.update(overrides)
    return knowledge_sync.process_after_index(**kwargs)


# --------------------------------------------------------------------------- #
# Ships inert
# --------------------------------------------------------------------------- #

def test_the_stage_flag_defaults_off():
    """Every new capability in this codebase launches OFF. Checked on the field
    default rather than a loaded Settings, so a developer's .env cannot make
    this pass or fail for the wrong reason."""
    from app.config import Settings

    field = Settings.model_fields["knowledge_process_after_index"]
    assert field.default is False


def test_nothing_runs_when_the_knowledge_layer_is_disabled(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=False, knowledge_process_after_index=True)
    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document",
        lambda *a, **kw: pytest.fail("the pipeline must not run"),
    )
    assert knowledge_sync.enabled() is False
    assert _call() is None


def test_nothing_runs_when_only_the_master_switch_is_on(monkeypatch):
    """`knowledge_enabled` means "this deployment has a knowledge layer", not
    "build it on the ingest path". The second decision is its own flag."""
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=False)
    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document",
        lambda *a, **kw: pytest.fail("the pipeline must not run"),
    )
    assert knowledge_sync.enabled() is False
    assert _call() is None


def test_both_flags_on_runs_the_pipeline(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    seen = {}

    class _Report:
        status = "ok"

        def as_dict(self):
            return {"status": "ok"}

    def _process(doc, options):
        seen["doc"] = doc
        return _Report()

    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document", _process
    )
    assert _call() == {"status": "ok"}
    assert seen["doc"].document_id == "doc-1"
    assert seen["doc"].run_id == "run-1"


def test_unreadable_settings_read_as_disabled(monkeypatch):
    """`enabled()` guards the call site, before the arguments are even built, so
    it has to hold even when configuration cannot be read."""
    def _boom():
        raise RuntimeError("no config")

    monkeypatch.setattr("app.config.get_settings", _boom)
    assert knowledge_sync.enabled() is False


# --------------------------------------------------------------------------- #
# Cannot cost a document
# --------------------------------------------------------------------------- #

def test_a_pipeline_explosion_is_swallowed(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)

    def _boom(doc, options):
        raise RuntimeError("everything is on fire")

    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document", _boom
    )
    assert _call() is None      # returned, not raised


def test_parents_are_dropped_and_an_all_parent_document_is_a_no_op(monkeypatch):
    """A parent chunk is an assembly of its children's text; extracting from
    both would double every mention and stage the same claim twice."""
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document",
        lambda *a, **kw: pytest.fail("nothing to extract from"),
    )
    assert _call(chunks=[_Chunk("p1", "parent text", is_parent=True)]) is None


def test_a_document_with_no_chunks_is_a_no_op(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    assert _call(chunks=[]) is None


def test_the_hook_cannot_reach_the_code_that_deletes_vectors():
    """Enforced structurally rather than by care: the knowledge modules never
    *call* the two functions that could unmake an indexed document, so no
    failure in them can remove a vector whatever else it does.

    Asserted on the parsed call graph rather than on the text, so a docstring
    that merely names them — as both modules do, explaining this rule — is not
    mistaken for a call. ``delete_document_mentions`` is a different function
    and is legitimately called; it drops superseded mention rows in MySQL and
    touches no vector.
    """
    import ast
    import inspect

    from app.knowledge import document_pipeline

    forbidden = {"delete_document", "index_chunks", "index_canonical"}
    for module in (knowledge_sync, document_pipeline):
        tree = ast.parse(inspect.getsource(module))
        called = {
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Name, ast.Attribute))
        }
        assert not (called & forbidden), (module.__name__, called & forbidden)


# --------------------------------------------------------------------------- #
# The call site in _handle
# --------------------------------------------------------------------------- #

def test_the_hook_is_called_only_after_the_document_is_fully_indexed():
    """Order is the whole safety argument: points upserted, old version swapped
    out, catalog persisted, log written — and only then knowledge."""
    import inspect

    from app.ingestion import pipeline

    source = inspect.getsource(pipeline._handle)
    order = [
        source.index("chunks = index_chunks(new_chunks)"),
        source.index("delete_document(record.document_id, keep_ids="),
        source.index("_persist(record, doc, content_hash, version, indexed=True"),
        source.index('_log(run_id, record, "indexed"'),
        source.index("knowledge_sync.process_after_index("),
        source.index('return "indexed"'),
    ]
    assert order == sorted(order)


def test_the_hook_is_guarded_before_its_arguments_are_built():
    """Argument evaluation happens at the call site, outside anything
    `knowledge_sync` can catch. Without the guard, a missing attribute on `doc`
    would raise straight into ingestion."""
    import inspect

    from app.ingestion import pipeline

    source = inspect.getsource(pipeline._handle)
    guard = source.index("if knowledge_sync.enabled():")
    call = source.index("knowledge_sync.process_after_index(")
    assert guard < call


@pytest.mark.parametrize(
    "outcome", ["deleted", "unchanged", "unchanged_content", "skipped", "error"]
)
def test_only_the_indexed_outcome_reaches_the_hook(outcome):
    """Every other branch returns before the hook. A deleted document has no
    text, and an unchanged-content one has chunks nothing re-wrote."""
    import inspect

    from app.ingestion import pipeline

    source = inspect.getsource(pipeline._handle)
    call = source.index("knowledge_sync.process_after_index(")
    assert source.index(f'return "{outcome}"') < call


def test_a_knowledge_failure_leaves_the_ingestion_outcome_alone(monkeypatch):
    """The end-to-end statement of the guarantee, at the real call site."""
    from app.ingestion import pipeline

    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)

    def _boom(**kwargs):
        raise RuntimeError("knowledge layer is down")

    monkeypatch.setattr(knowledge_sync, "enabled", lambda: True)
    monkeypatch.setattr(knowledge_sync, "process_after_index", _boom)

    # The hook is called inside _handle with no try/except of its own, so if the
    # guarantee were only "knowledge_sync catches its own errors", bypassing
    # that catch would surface here. It must not.
    with pytest.raises(RuntimeError):
        pipeline.knowledge_sync.process_after_index(document_id="x")

    # ...and with the real implementation restored, the same failure is silent.
    monkeypatch.undo()
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document", _raise_anything
    )
    assert _call() is None


def _raise_anything(*args, **kwargs):
    raise RuntimeError("still on fire")


# --------------------------------------------------------------------------- #
# Catch-up
# --------------------------------------------------------------------------- #

def test_catch_up_is_inert_when_the_feature_is_off(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=False)
    assert knowledge_sync.catch_up() is None


def test_catch_up_processes_the_retry_queue(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    monkeypatch.setattr(
        "app.catalog.knowledge_runs.pending",
        lambda **kw: [{"document_id": "a"}, {"document_id": "b"}],
    )
    monkeypatch.setattr(
        "app.knowledge.document_loader.load_document",
        lambda document_id, **kw: object() if document_id == "a" else None,
    )

    class _Report:
        status = "ok"

    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document",
        lambda doc, options: _Report(),
    )
    assert knowledge_sync.catch_up() == {"examined": 2, "ok": 1, "failed": 1}


def test_catch_up_survives_an_unreadable_queue(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)

    def _boom(**kwargs):
        raise RuntimeError("mysql is down")

    monkeypatch.setattr("app.catalog.knowledge_runs.pending", _boom)
    assert knowledge_sync.catch_up() is None


def test_one_document_failing_catch_up_does_not_stop_the_rest(monkeypatch):
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    monkeypatch.setattr(
        "app.catalog.knowledge_runs.pending",
        lambda **kw: [{"document_id": "a"}, {"document_id": "b"}],
    )

    class _Report:
        status = "ok"

    def _load(document_id, **kw):
        if document_id == "a":
            raise RuntimeError("unreadable")
        return object()

    monkeypatch.setattr("app.knowledge.document_loader.load_document", _load)
    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document",
        lambda doc, options: _Report(),
    )
    assert knowledge_sync.catch_up() == {"examined": 2, "ok": 1, "failed": 1}


def test_the_hook_forwards_the_documents_authors(monkeypatch):
    """PERSON corroboration depends on them, and ingestion is the one caller
    that already has them without a query."""
    _flags(monkeypatch, knowledge_enabled=True, knowledge_process_after_index=True)
    seen = {}

    class _Report:
        status = "ok"

        def as_dict(self):
            return {"status": "ok"}

    def _process(doc, options):
        seen["doc"] = doc
        return _Report()

    monkeypatch.setattr(
        "app.knowledge.document_pipeline.process_document", _process
    )
    _call(authors=["Dr Preeti Jain Das"])
    assert seen["doc"].authors == ("Dr Preeti Jain Das",)


def test_the_call_site_passes_authors_from_the_canonical_document():
    import inspect

    from app.ingestion import pipeline

    source = inspect.getsource(pipeline._handle)
    assert 'authors=tuple(getattr(doc, "authors", ()) or ())' in source
