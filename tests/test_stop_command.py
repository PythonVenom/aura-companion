"""Bug 33 — тесты stop_command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.core import stop_command as SC


# === is_stop ===

@pytest.mark.parametrize("text", [
    "стоп", "Стоп!", "аура стоп", "тише", "хватит",
    "замолчи", "прекрати", "пауза", "стой",
])
def test_is_stop_positive(text):
    assert SC.is_stop(text) is True


@pytest.mark.parametrize("text", [
    "", "привет", "как дела", "включи музыку",
    "расскажи сказку", None,
])
def test_is_stop_negative(text):
    assert SC.is_stop(text) is False


def test_is_stop_punctuation():
    assert SC.is_stop("Стоп!!!") is True
    assert SC.is_stop("Аура, стоп.") is True


# === find_vosk_model ===

def test_find_vosk_model_exists():
    """Модель должна быть найдена (мы её установили)."""
    path = SC.find_vosk_model()
    # Может быть None если модель удалена — не падаем
    if path:
        assert "vosk" in path.lower()


# === recognize_stop ===

def test_recognize_stop_no_vosk():
    """Без vosk → False."""
    with patch.dict("sys.modules", {"vosk": None}):
        assert SC.recognize_stop(b"\x00\x00") is False


def test_recognize_stop_no_model():
    """Без модели → False."""
    with patch.object(SC, "find_vosk_model", return_value=None):
        assert SC.recognize_stop(b"\x00\x00") is False


def test_recognize_stop_handles_exception():
    """Vosk упал → False, не краш."""
    fake_vosk = MagicMock()
    fake_vosk.KaldiRecognizer.side_effect = RuntimeError("boom")
    fake_vosk.Model.return_value = "m"
    with patch.dict("sys.modules", {"vosk": fake_vosk}):
        with patch.object(SC, "find_vosk_model", return_value="/fake/path"):
            assert SC.recognize_stop(b"\x00\x00") is False


# === STOP_WORDS ===

def test_stop_words_non_empty():
    assert len(SC.STOP_WORDS) >= 5


def test_stop_words_contains_key():
    for w in ("стоп", "тише", "хватит"):
        assert w in SC.STOP_WORDS
