"""Observe the real pipeline without changing it.

Every hook below wraps a module attribute the pipeline resolves at call time,
calls the real implementation, and records what went in and what came out.
The wrappers never alter arguments or return values, so the pipeline's
behaviour is exactly what a production sweep would do.

The current document is tracked in a ``ContextVar`` set by the ``_handle``
wrapper; the run is sequential (``INGEST_WORKERS=1``), so every nested hook
can attribute its observation to the document being handled.
"""
from __future__ import annotations

import contextlib
import hashlib
import logging
import time
import traceback
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator
from unittest import mock

current_doc: ContextVar[str | None] = ContextVar("e2e_current_doc", default=None)


@dataclass
class DocCapture:
    record: Any
    order: int
    started_at: str | None = None
    finished_at: str | None = None
    elapsed_seconds: float | None = None
    outcome: str | None = None
    error: str | None = None
    traceback: str | None = None

    # Stage artifacts, in pipeline order.
    download: dict[str, Any] | None = None
    pdf_bytes: bytes | None = None
    extraction: Any = None
    extraction_seconds: float | None = None
    parent_date: Any = None
    resolved_date: Any = None
    doc: Any = None
    build_seconds: float | None = None
    chunks: list[Any] = field(default_factory=list)
    chunk_seconds: float | None = None
    index_points: int | None = None
    index_seconds: float | None = None
    delete_calls: list[dict[str, Any]] = field(default_factory=list)
    knowledge_report: dict[str, Any] | None = None
    knowledge_seconds: float | None = None
    log_lines: list[str] = field(default_factory=list)

    @property
    def document_id(self) -> str:
        return self.record.document_id


@dataclass
class Captures:
    by_id: dict[str, DocCapture] = field(default_factory=dict)
    run_log: list[str] = field(default_factory=list)
    progress: Any = None  # optional callable(DocCapture) invoked when a document finishes
    _order: int = 0

    def start(self, record: Any) -> DocCapture:
        self._order += 1
        cap = DocCapture(record=record, order=self._order)
        cap.started_at = datetime.now(timezone.utc).isoformat()
        # A document id can be yielded twice only by a bug in change detection;
        # keep the first capture and note the second so that is visible.
        if record.document_id in self.by_id:
            cap = self.by_id[record.document_id]
            cap.log_lines.append("!! this document_id was handled more than once")
        self.by_id[record.document_id] = cap
        return cap

    def current(self) -> DocCapture | None:
        doc_id = current_doc.get()
        return self.by_id.get(doc_id) if doc_id else None

    def ordered(self) -> list[DocCapture]:
        return sorted(self.by_id.values(), key=lambda c: c.order)


class _CaptureHandler(logging.Handler):
    """Every log line, kept per document and for the run."""

    def __init__(self, captures: Captures) -> None:
        super().__init__(level=logging.DEBUG)
        self.captures = captures
        self.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
        except Exception:  # pragma: no cover - formatting is not our concern
            line = f"{record.levelname} {record.name}: {record.getMessage()}"
        self.captures.run_log.append(line)
        cap = self.captures.current()
        if cap is not None:
            cap.log_lines.append(line)


@contextlib.contextmanager
def observed_pipeline(captures: Captures) -> Iterator[None]:
    """Install every observation hook for the duration of one run."""
    from app.ingestion import knowledge_sync, pipeline
    from app.ingestion.extractors import attachment, pdf_extractor

    real_handle = pipeline._handle
    real_build = pipeline._build_drupal_or_attachment
    real_chunk = pipeline.chunk_canonical
    real_index = pipeline.index_chunks
    real_delete = pipeline.delete_document
    real_fetch = attachment.fetch_attachment
    real_extract = pdf_extractor.extract_pdf
    real_parent_date = attachment.resolve_parent_date
    real_resolve_date = attachment._resolve_date
    real_knowledge = knowledge_sync.process_after_index

    def handle(record: Any, build_doc: Any, run_id: Any = None, **kwargs: Any) -> str:
        cap = captures.start(record)
        token = current_doc.set(record.document_id)
        started = time.perf_counter()
        try:
            outcome = real_handle(record, build_doc, run_id, **kwargs)
            cap.outcome = outcome
            return outcome
        except Exception as exc:
            cap.outcome = "error"
            cap.error = f"{type(exc).__name__}: {exc}"
            cap.traceback = traceback.format_exc()
            raise
        finally:
            cap.elapsed_seconds = round(time.perf_counter() - started, 3)
            cap.finished_at = datetime.now(timezone.utc).isoformat()
            current_doc.reset(token)
            if captures.progress is not None:
                try:
                    captures.progress(cap)
                except Exception:  # pragma: no cover - progress is cosmetic
                    pass

    def build(record: Any, session: Any) -> Any:
        started = time.perf_counter()
        doc = real_build(record, session)
        cap = captures.current()
        if cap is not None:
            cap.doc = doc
            cap.build_seconds = round(time.perf_counter() - started, 3)
        return doc

    def chunk(doc: Any, **kwargs: Any) -> list[Any]:
        started = time.perf_counter()
        chunks = real_chunk(doc, **kwargs)
        cap = captures.current()
        if cap is not None:
            cap.chunks = list(chunks)
            cap.chunk_seconds = round(time.perf_counter() - started, 3)
        return chunks

    def index(chunks: Any, **kwargs: Any) -> int:
        started = time.perf_counter()
        points = real_index(chunks, **kwargs)
        cap = captures.current()
        if cap is not None:
            cap.index_points = points
            cap.index_seconds = round(time.perf_counter() - started, 3)
        return points

    def delete(document_id: str, **kwargs: Any) -> None:
        cap = captures.current()
        if cap is not None:
            keep = kwargs.get("keep_ids")
            cap.delete_calls.append(
                {"document_id": document_id,
                 "keep_ids": None if keep is None else len(list(keep))}
            )
        return real_delete(document_id, **kwargs)

    def fetch(session: Any, url: str, timeout: float) -> tuple[bytes, str]:
        started = time.perf_counter()
        content, fetched_url = real_fetch(session, url, timeout)
        cap = captures.current()
        if cap is not None:
            cap.pdf_bytes = content
            cap.download = {
                "requested_url": url,
                "fetched_url": fetched_url,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "seconds": round(time.perf_counter() - started, 3),
                "upgraded_to_https": fetched_url != url,
            }
        return content, fetched_url

    def extract(content: bytes, filename: str) -> Any:
        started = time.perf_counter()
        result = real_extract(content, filename)
        cap = captures.current()
        if cap is not None:
            cap.extraction = result
            cap.extraction_seconds = round(time.perf_counter() - started, 3)
        return result

    def parent_date(node: Any) -> Any:
        resolved = real_parent_date(node)
        cap = captures.current()
        if cap is not None:
            cap.parent_date = resolved
        return resolved

    def resolve_date(record: Any, node: Any, file: Any, content: bytes, parent: Any) -> Any:
        resolved = real_resolve_date(record, node, file, content, parent)
        cap = captures.current()
        if cap is not None:
            cap.resolved_date = resolved
        return resolved

    def knowledge(**kwargs: Any) -> Any:
        started = time.perf_counter()
        report = real_knowledge(**kwargs)
        cap = captures.current()
        if cap is not None:
            cap.knowledge_report = report
            cap.knowledge_seconds = round(time.perf_counter() - started, 3)
        return report

    handler = _CaptureHandler(captures)
    root = logging.getLogger()
    previous_level = root.level
    root.addHandler(handler)
    if root.level > logging.INFO or root.level == logging.NOTSET:
        root.setLevel(logging.INFO)

    patches = [
        mock.patch.object(pipeline, "_handle", handle),
        mock.patch.object(pipeline, "_build_drupal_or_attachment", build),
        mock.patch.object(pipeline, "chunk_canonical", chunk),
        mock.patch.object(pipeline, "index_chunks", index),
        mock.patch.object(pipeline, "delete_document", delete),
        mock.patch.object(attachment, "fetch_attachment", fetch),
        mock.patch.object(pdf_extractor, "extract_pdf", extract),
        mock.patch.object(attachment, "resolve_parent_date", parent_date),
        mock.patch.object(attachment, "_resolve_date", resolve_date),
        mock.patch.object(knowledge_sync, "process_after_index", knowledge),
    ]
    try:
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            yield
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)
