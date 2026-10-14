"""#103 — тесты streaming в chat.py."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

from aura.chat import _split_sentences, _stream_and_speak


# === _split_sentences ===

def test_split_two_sentences():
    assert _split_sentences("Привет. Как дела?") == ["Привет.", "Как дела?"]


def test_split_keeps_incomplete():
    """Незавершённое предложение (без .!?) НЕ возвращается."""
    assert _split_sentences("Привет. Как дела? Хорошо") == ["Привет.", "Как дела?"]


def test_split_single_complete():
    assert _split_sentences("Одно предложение.") == ["Одно предложение."]


def test_split_empty():
    assert _split_sentences("") == []


def test_split_no_punctuation():
    """Без .!? — пусто."""
    assert _split_sentences("просто текст") == []


def test_split_with_exclamation():
    assert _split_sentences("Ого! Круто.") == ["Ого!", "Круто."]


# === _stream_and_speak ===

@pytest.mark.asyncio
async def test_stream_and_speak_fallback_no_brain():
    """Если у orch нет brain.stream → fallback на orch.process."""
    orch = MagicMock()
    del orch.brain  # нет атрибута

    async def fake_process(text):
        return "fallback"
    orch.process = fake_process

    text, spoke = await _stream_and_speak(orch, "привет", None)
    assert text == "fallback"
    assert spoke is False


@pytest.mark.asyncio
async def test_stream_and_speak_yields_chunks():
    """Стриминг + накопление полного текста."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["Привет. ", "Как ", "дела?"]))
    orch = MagicMock(brain=brain)
    speaker = MagicMock()

    text, spoke = await _stream_and_speak(orch, "привет", speaker)
    assert text == "Привет. Как дела?"
    assert spoke is True
    # 2 предложения → 2 say
    assert speaker.say.call_count == 2


@pytest.mark.asyncio
async def test_stream_and_speak_no_speaker():
    """Без speaker — просто собирает текст."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["A. ", "B."]))
    orch = MagicMock(brain=brain)

    text, spoke = await _stream_and_speak(orch, "test", None)
    assert text == "A. B."
    assert spoke is False


@pytest.mark.asyncio
async def test_stream_and_speak_handles_exception():
    """Ошибка стрима → error message."""
    brain = MagicMock()
    brain.stream = MagicMock(side_effect=RuntimeError("boom"))
    orch = MagicMock(brain=brain)

    text, spoke = await _stream_and_speak(orch, "test", None)
    assert "❌" in text
    assert spoke is False


@pytest.mark.asyncio
async def test_stream_and_speak_incomplete_last():
    """Последнее незавершённое озвучивается в _flush(force=True)."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["Привет. ", "Конец"]))
    orch = MagicMock(brain=brain)
    speaker = MagicMock()

    text, spoke = await _stream_and_speak(orch, "test", speaker)
    assert text == "Привет. Конец"
    # Оба предложения озвучены (второе через force)
    assert speaker.say.call_count == 2
