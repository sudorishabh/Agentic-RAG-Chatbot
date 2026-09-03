"""How the cross-encoder is cached, and what `rerank_max_seq_length` does to it.

The encoder is cached by model name because loading one is seconds and several
hundred MB. `max_seq_length` is mutable state *on that cached object*, which is
the whole difficulty: it has to be re-applied per call, and a setting of 0 has to
restore the model's own default rather than leave the last override standing.
Both failures are silent — the sequence length simply is not what the setting
says, and the only symptom is latency and ranking quality moving together for no
visible reason. `sentence_transformers` is stubbed; nothing is downloaded.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.retrieval.search import reranker


MODEL = "stub/cross-encoder"
MODEL_DEFAULT_SEQ = 512


@pytest.fixture
def encoder(monkeypatch):
    """A stub CrossEncoder, and a clean cache around each test."""
    monkeypatch.setattr(reranker, "_CROSS_ENCODER_CACHE", {})
    monkeypatch.setattr(reranker, "_MODEL_MAX_SEQ", {})
    built: list[SimpleNamespace] = []

    class _Stub:
        def __init__(self, name):
            self.name = name
            self.max_seq_length = MODEL_DEFAULT_SEQ
            built.append(self)

        def predict(self, pairs):
            return [0.0] * len(pairs)

    monkeypatch.setitem(
        __import__("sys").modules, "sentence_transformers",
        SimpleNamespace(CrossEncoder=_Stub),
    )
    return built


def _settings(max_seq: int):
    return SimpleNamespace(rerank_max_seq_length=max_seq, rerank_model=MODEL)


def test_the_encoder_is_built_once_and_reused(encoder, monkeypatch):
    monkeypatch.setattr(reranker, "get_settings", lambda: _settings(0))

    first = reranker._load_cross_encoder(MODEL)
    second = reranker._load_cross_encoder(MODEL)

    assert first is second
    assert len(encoder) == 1


def test_the_setting_is_applied_to_the_cached_encoder(encoder, monkeypatch):
    monkeypatch.setattr(reranker, "get_settings", lambda: _settings(0))
    reranker._load_cross_encoder(MODEL)  # cache it at the model default

    monkeypatch.setattr(reranker, "get_settings", lambda: _settings(128))
    assert reranker._load_cross_encoder(MODEL).max_seq_length == 128


def test_zero_restores_the_model_default_after_an_override(encoder, monkeypatch):
    """The regression: 0 means "the model's own length", not "keep the last one".

    Measured as two eval configurations that should have differed by 4x in
    sequence length returning identical per-category scores, because the config
    that set nothing inherited the previous config's 128.
    """
    monkeypatch.setattr(reranker, "get_settings", lambda: _settings(128))
    assert reranker._load_cross_encoder(MODEL).max_seq_length == 128

    monkeypatch.setattr(reranker, "get_settings", lambda: _settings(0))
    assert reranker._load_cross_encoder(MODEL).max_seq_length == MODEL_DEFAULT_SEQ
