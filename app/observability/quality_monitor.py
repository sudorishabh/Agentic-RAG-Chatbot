"""Async answer-quality monitor: judges production answers off the request path.

A bounded in-process queue feeds a single daemon worker thread. Every fresh
grounded answer gets deterministic citation coverage; a configurable sample
(default 100%) also gets the claim-level faithfulness judge. Verdicts are
emitted as ``quality_metrics`` structured log lines, mirroring the
``rag_metrics`` format. Nothing here may ever slow or fail a request: enqueue
never blocks and never raises — a full queue simply drops the item.
"""

from __future__ import annotations

import logging
import queue
import random
import threading
from dataclasses import dataclass
from typing import Any, Sequence

from app.config import get_settings

logger = logging.getLogger(__name__)

_QUEUE_MAX = 256


@dataclass
class _Item:
    question: str
    answer: str
    block_texts: list[str]
    citations: list[dict[str, Any]]


_queue: "queue.Queue[_Item]" = queue.Queue(maxsize=_QUEUE_MAX)
_worker_started = False
_worker_lock = threading.Lock()


def enqueue(
    question: str,
    answer: str,
    block_texts: Sequence[str],
    citations: Sequence[dict[str, Any]],
) -> None:
    """Queue one answered query for judging. Never blocks, never raises."""
    try:
        if not get_settings().quality_monitor_enabled or not answer.strip():
            return
        _ensure_worker()
        _queue.put_nowait(
            _Item(question, answer, list(block_texts), list(citations))
        )
    except queue.Full:
        logger.debug("Quality queue full; dropping item.")
    except Exception:
        logger.debug("Quality enqueue failed; dropping item.", exc_info=True)


def _ensure_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    with _worker_lock:
        if _worker_started:
            return
        threading.Thread(target=_run, name="quality-monitor", daemon=True).start()
        _worker_started = True


def _run() -> None:  # pragma: no cover — loop plumbing; _process is tested
    while True:
        item = _queue.get()
        try:
            _process(item)
        except Exception:
            logger.warning("Quality judging failed for an item.", exc_info=True)
        finally:
            _queue.task_done()


def _process(item: _Item) -> None:
    from app.generation.faithfulness import citation_coverage

    metrics: dict[str, Any] = {
        "question_chars": len(item.question),  # lengths only; no query text in logs
        "answer_chars": len(item.answer),
        "blocks": len(item.block_texts),
        "citations": len(item.citations),
        "citation_coverage": round(citation_coverage(item.answer), 3),
    }
    sample = float(get_settings().quality_judge_sample)
    if item.block_texts and random.random() < sample:
        report = _judge(item)
        if report is not None:
            metrics["faithful"] = report.faithful
            metrics["unsupported_claims"] = len(report.unsupported)
    logger.info("quality_metrics %s", metrics)


def _judge(item: _Item) -> Any | None:
    from app.generation import faithfulness
    from app.retrieval.context_builder import ContextBlock

    blocks = [
        ContextBlock(n=i, text=text)
        for i, text in enumerate(item.block_texts, start=1)
    ]
    try:
        return faithfulness.verify(item.answer, blocks)
    except Exception:
        logger.warning("Quality faithfulness judge failed.", exc_info=True)
        return None
