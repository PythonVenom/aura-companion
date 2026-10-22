"""Тесты для AuraOrchestrator — пауза/возобновление медиа.

Не тестируем listener/speaker/loop — это интеграция с реальным
железом. Тестируем только pause/resume логику в изоляции.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aura_main import AuraOrchestrator


def _make_orch_with_mocks(media_pause=True, barge_in=None):
    """AuraOrchestrator без __init__ — только нужные атрибуты."""
    orch = AuraOrchestrator.__new__(AuraOrchestrator)
    orch.speaker = MagicMock()
    # is_speaking=False — цикл ожидания в _say_with_duck сразу выходит
    orch.speaker.is_speaking = False
    orch.media_pause = MagicMock() if media_pause else None
    # barge_in=None по умолчанию: _set_barge_speaking просто вернётся
    orch.barge_in = barge_in
    orch._halted = False  # Bug 33: debounce
    # Bug 38: ducker для нового _duck_on
    orch.ducker = MagicMock()
    return orch


def test_duck_on_calls_pause():
    orch = _make_orch_with_mocks()
    orch._duck_on()
    orch.ducker.duck.assert_called_once()


def test_duck_off_calls_resume():
    orch = _make_orch_with_mocks()
    orch._duck_off()
    orch.ducker.un_duck.assert_called_once()


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
    """Bug 38: порядок duck → say → un_duck (music_ducker)."""
    orch = _make_orch_with_mocks()
    calls = []
    orch.ducker.duck.side_effect = lambda: calls.append("duck")
    orch.ducker.un_duck.side_effect = lambda: calls.append("un_duck")
    orch.speaker.say.side_effect = lambda text: calls.append(f"say:{text}")

    orch._say_with_duck("привет")

    assert calls == ["duck", "say:привет", "un_duck"]


def test_say_with_duck_waits_for_is_speaking():
    """Ждём, пока speaker.is_speaking не станет False."""
    orch = _make_orch_with_mocks()
    # Три "тиктака" True, потом False — цикл должен отработать
    states = [True, True, False]
    def fake_get():
        return states.pop(0) if states else False
    type(orch.speaker).is_speaking = property(lambda self: fake_get())

    orch._say_with_duck("привет")

    orch.ducker.duck.assert_called_once()
    orch.ducker.un_duck.assert_called_once()
    orch.speaker.say.assert_called_once_with("привет")


def test_say_with_duck_immediate_exit():
    """is_speaking=False сразу — pause/say/resume всё равно вызываются."""
    orch = _make_orch_with_mocks()
    orch.speaker.is_speaking = False

    orch._say_with_duck("привет")

    orch.ducker.duck.assert_called_once()
    orch.ducker.un_duck.assert_called_once()
    orch.speaker.say.assert_called_once_with("привет")


# --- barge-in (Фаза 10) ---

def test_set_barge_speaking_True():
    mock_barge = MagicMock()
    orch = _make_orch_with_mocks(barge_in=mock_barge)
    orch._set_barge_speaking(True)
    mock_barge.set_aura_speaking.assert_called_once_with(True)


def test_set_barge_speaking_no_barge():
    orch = _make_orch_with_mocks()
    orch.barge_in = None
    orch._set_barge_speaking(True)  # не падает


def test_on_barge_in_stops_speaker():
    orch = _make_orch_with_mocks()
    orch._on_barge_in()
    orch.speaker.stop_speaking.assert_called_once()


def test_on_barge_in_swallows_exception():
    orch = _make_orch_with_mocks()
    orch.speaker.stop_speaking.side_effect = RuntimeError("boom")
    orch._on_barge_in()  # не падает


# --- пауза (Фаза 9.3.1) ---

def test_is_paused_no_flag(tmp_path, monkeypatch):
    orch = _make_orch_with_mocks()
    from pathlib import Path
    monkeypatch.setattr(AuraOrchestrator, "PAUSE_FLAG", tmp_path / "aura_pause.flag")
    assert orch._is_paused() is False


def test_is_paused_flag_exists(tmp_path, monkeypatch):
    flag = tmp_path / "aura_pause.flag"
    flag.touch()
    monkeypatch.setattr(AuraOrchestrator, "PAUSE_FLAG", flag)
    orch = _make_orch_with_mocks()
    assert orch._is_paused() is True


# --- Ctrl+C без traceback (техдолг) ---

def test_main_catches_keyboard_interrupt():
    """KeyboardInterrupt из aura.run() не должен давать traceback."""
    from unittest.mock import patch as _patch
    import aura_main

    with _patch.object(aura_main.AuraOrchestrator, "__init__", return_value=None), \
         _patch.object(aura_main.AuraOrchestrator, "run",
                       side_effect=KeyboardInterrupt()):
        # Не должно бросить наружу
        result = aura_main.main()
        assert result == 0


def test_main_returns_zero_on_success():
    from unittest.mock import patch as _patch
    import aura_main

    with _patch.object(aura_main.AuraOrchestrator, "__init__", return_value=None), \
         _patch.object(aura_main.AuraOrchestrator, "run", return_value=None):
        assert aura_main.main() == 0
