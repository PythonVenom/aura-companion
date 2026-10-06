"""Тесты для aura/core/wake_word.py — openWakeWord (ADR-083)."""
from __future__ import annotations
from unittest.mock import MagicMock
import numpy as np
import pytest
from aura.core.wake_word import WakeWordDetector, WAKE_PHRASES


def test_wake_phrases_contains_aura():
    """Контракт (RICE 150): одна кастомная модель openWakeWord, обученная на 'aura'.
    Раньше было 2 фразы (aura + hey_aura), после обучения кастомной модели — 1.
    Проверяем не количество, а наличие ключевой фразы."""
    assert "aura" in WAKE_PHRASES


def test_detector_init():
    d = WakeWordDetector(threshold=0.5, _model=None)
    assert d.threshold == 0.5
    assert d.enabled is False


def test_detector_invalid_threshold():
    with pytest.raises(ValueError):
        WakeWordDetector(threshold=1.5, _model=None)


def test_detect_silence_false():
    d = WakeWordDetector(threshold=0.5, _model=MagicMock())
    d._model.predict.return_value = {"aura": 0.1}
    pcm = (np.zeros(16000, dtype=np.int16)).tobytes()
    assert d.detect(pcm) is False


def test_detect_aura_true():
    d = WakeWordDetector(threshold=0.5, _model=MagicMock())
    d._model.predict.return_value = {"aura": 0.9}
    pcm = (np.random.randint(-1000, 1000, 16000)).astype(np.int16).tobytes()
    assert d.detect(pcm) is True


def test_detect_respects_threshold():
    d = WakeWordDetector(threshold=0.7, _model=MagicMock())
    d._model.predict.return_value = {"aura": 0.65}
    pcm = (np.random.randint(-1000, 1000, 16000)).astype(np.int16).tobytes()
    assert d.detect(pcm) is False


def test_detect_bad_pcm_false():
    d = WakeWordDetector(threshold=0.5, _model=MagicMock())
    assert d.detect(b"") is False
    assert d.detect(b"\x00" * 100) is False


def test_reset_clears_state():
    d = WakeWordDetector(threshold=0.5, _model=MagicMock())
    d._last_score = 0.9
    d.reset()
    assert d._last_score == 0.0
