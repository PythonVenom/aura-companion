"""Тесты для AuraOrchestrator — пауза/возобновление медиа.

Не тестируем listener/speaker/loop — это интеграция с реальным
железом. Тестируем только pause/resume логику в изоляции.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aura_main import AuraOrchestrator


def _make_orch_with_mocks(media_pause=True):
    """AuraOrchestrator без __init__ — только нужные атрибуты."""
    orch = AuraOrchestrator.__new__(AuraOrchestrator)
    orch.speaker = MagicMock()
    # is_speaking=False — цикл ожидания в _say_with_duck сразу выходит
    orch.speaker.is_speaking = False
    orch.media_pause = MagicMock() if media_pause else None
    return orch


def test_duck_on_calls_pause():
    orch = _make_orch_with_mocks()
    orch._duck_on()
    orch.media_pause.pause.assert_called_once()


def test_duck_off_calls_resume():
    orch = _make_orch_with_mocks()
    orch._duck_off()
    orch.media_pause.resume.assert_called_once()


def test_duck_on_no_media_pause():
    """Нет media_pause — не падает."""
    orch = _make_orch_with_mocks(media_pause=False)
    orch._duck_on()  # не должно упасть
    orch._duck_off()


def test_duck_on_swallows_exception():
    """Ошибка pause() не ломает цикл."""
    orch = _make_orch_with_mocks()
    orch.media_pause.pause.side_effect = RuntimeError("playerctl упал")
    orch._duck_on()  # не должно упасть


def test_duck_off_swallows_exception():
    orch = _make_orch_with_mocks()
    orch.media_pause.resume.side_effect = RuntimeError("playerctl упал")
    orch._duck_off()  # не должно упасть


def test_say_with_duck_order():
    """Порядок: pause → say → resume."""
    orch = _make_orch_with_mocks()
    calls = []
    orch.media_pause.pause.side_effect = lambda: calls.append("pause")
    orch.media_pause.resume.side_effect = lambda: calls.append("resume")
    orch.speaker.say.side_effect = lambda text: calls.append(f"say:{text}")

    orch._say_with_duck("привет")

    assert calls == ["pause", "say:привет", "resume"]


def test_say_with_duck_waits_for_is_speaking():
    """Ждём, пока speaker.is_speaking не станет False."""
    orch = _make_orch_with_mocks()
    # Три "тиктака" True, потом False — цикл должен отработать
    states = [True, True, False]
    def fake_get():
        return states.pop(0) if states else False
    type(orch.speaker).is_speaking = property(lambda self: fake_get())

    orch._say_with_duck("привет")

    orch.media_pause.pause.assert_called_once()
    orch.media_pause.resume.assert_called_once()
    orch.speaker.say.assert_called_once_with("привет")


def test_say_with_duck_immediate_exit():
    """is_speaking=False сразу — pause/say/resume всё равно вызываются."""
    orch = _make_orch_with_mocks()
    orch.speaker.is_speaking = False

    orch._say_with_duck("привет")

    orch.media_pause.pause.assert_called_once()
    orch.media_pause.resume.assert_called_once()
    orch.speaker.say.assert_called_once_with("привет")
