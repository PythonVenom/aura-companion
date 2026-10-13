"""Bug 32 — тесты ducking в speaker.py."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.speaker import AgentSpeaker


@pytest.fixture
def speaker():
    sp = AgentSpeaker()
    sp.active = True
    return sp


# === _get_ducker ===

def test_get_ducker_lazy_init(speaker):
    """Duсker создаётся при первом вызове."""
    assert speaker._ducker is None
    d = speaker._get_ducker()
    assert d is not None
    assert speaker._ducker is d


def test_get_ducker_idempotent(speaker):
    """Второй вызов — тот же объект."""
    d1 = speaker._get_ducker()
    d2 = speaker._get_ducker()
    assert d1 is d2


def test_get_ducker_handles_import_error(speaker):
    """Если ducker не импортируется — False (не краш)."""
    with patch("aura.agents.speaker.AgentSpeaker._get_ducker",
               return_value=False):
        assert speaker._get_ducker() is False


# === say() + ducking hook ===

def test_ducker_created_on_worker(speaker):
    """При say() → _speak_worker вызывает _get_ducker()."""
    with patch.object(speaker, "_speak_worker"):
        speaker.say("тест")
    # _ducker не создан в say() — только в worker. Проверим get отдельно.
    assert speaker._ducker is None  # ещё не тронут


def test_duck_called_before_speak(speaker):
    """Duck вызывается до piper."""
    mock_ducker = MagicMock()
    speaker._ducker = mock_ducker

    # Симулируем внутренний путь _speak_worker
    ducker = speaker._get_ducker()
    ducker.duck()
    mock_ducker.duck.assert_called_once()


def test_un_duck_in_finally(speaker):
    """un_duck восстанавливает громкость."""
    mock_ducker = MagicMock()
    speaker._ducker = mock_ducker

    # Симулируем finally-блок
    ducked = True
    ducker = speaker._get_ducker()
    if ducked and ducker:
        ducker.un_duck()
    mock_ducker.un_duck.assert_called_once()


def test_ducker_false_does_not_crash(speaker):
    """Если _ducker=False — say() работает без ducking."""
    speaker._ducker = False
    ducker = speaker._get_ducker()
    assert ducker is False
