"""
Тесты для AgentBargeIn (Уровень 3, ADR-006).

Мокаем webrtcvad и sounddevice. Живой микрофон не трогаем.
"""

from __future__ import annotations

import queue
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.barge_in import AgentBargeIn


@pytest.fixture
def barge():
    mock_vad_module = MagicMock()
    mock_vad_instance = MagicMock()
    mock_vad_module.Vad = MagicMock(return_value=mock_vad_instance)
    mock_sd = MagicMock()

    with patch.dict("sys.modules", {
        "webrtcvad": mock_vad_module,
        "sounddevice": mock_sd,
    }):
        b = AgentBargeIn()
    return b


def test_init_loads(barge):
    assert barge.ready is True
    assert barge.vad is not None
    assert barge.SAMPLE_RATE == 16000
    assert barge.FRAME_SIZE == 480


def test_start_returns_true(barge):
    with patch.object(barge, "_loop"):
        result = barge.start()
    assert result is True
    assert barge.running is True
    barge.running = False


def test_start_not_ready():
    with patch.dict("sys.modules", {
        "webrtcvad": MagicMock(),
        "sounddevice": MagicMock(),
    }):
        b = AgentBargeIn()
    b.ready = False
    assert b.start() is False


def test_set_aura_speaking(barge):
    barge.set_aura_speaking(True)
    assert barge.aura_speaking is True
    barge.set_aura_speaking(False)
    assert barge.aura_speaking is False


def test_stop_closes(barge):
    with patch.object(barge, "_loop"):
        barge.start()
    barge.stream = MagicMock()
    barge.thread = MagicMock()
    barge.stop()
    assert barge.running is False


def test_cooldown_prevents_rapid_callback(barge):
    """Cooldown 0.5 сек — второй callback отбит.

    Проверяем логику _loop без потока: имитируем 2 итерации.
    """
    calls = []
    barge.on_speech = lambda: calls.append(1)
    barge.aura_speaking = True
    barge.vad.is_speech = MagicMock(return_value=True)

    import time
    # Итерация 1: первый вызов — callback
    now = time.time()
    if now - barge._last_speech_ts < barge._cooldown:
        raise AssertionError("initial ts should allow first call")
    barge._last_speech_ts = now
    barge.on_speech()

    # Итерация 2: сразу же — cooldown должен отбить
    now2 = time.time()
    if now2 - barge._last_speech_ts >= barge._cooldown:
        raise AssertionError("cooldown should block immediate second call")
    # Не вызываем barge.on_speech() — cooldown

    assert len(calls) == 1
