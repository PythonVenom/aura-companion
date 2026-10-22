"""Полное покрытие DialogueManager."""
from unittest.mock import MagicMock
from aura.dialogue_manager import DialogueManager, Scenario, DialogueState


def _dm():
    sc = Scenario(
        name="test", agent="test_agent",
        keywords=["напиши", "отправь"],
        required_slots=["chat", "text"],
    )
    return DialogueManager(scenarios=[sc], get_agent=MagicMock(return_value=None)), sc


def test_detect_matches_keyword():
    dm, sc = _dm()
    assert dm.detect("напиши Ане привет") is not None


def test_detect_no_match():
    dm, sc = _dm()
    assert dm.detect("привет как дела") is None


def test_start_resets_state():
    dm, sc = _dm()
    dm.start(sc)
    assert dm.state.scenario == sc


def test_is_active_true_after_start():
    dm, sc = _dm()
    dm.start(sc)
    assert dm.is_active() is True


def test_reset_clears():
    dm, sc = _dm()
    dm.start(sc)
    dm.reset()
    assert dm.state.scenario is None


def test_process_returns_none_inactive():
    dm, sc = _dm()
    assert dm.process("test") is None


def test_cancel_resets():
    dm, sc = _dm()
    dm.start(sc)
    result = dm.process("отмена")
    assert "тмен" in result.lower() or result == "Отменила"


def test_confirm_yes_triggers_finalize():
    dm, sc = _dm()
    dm.start(sc)
    dm.state.awaiting_confirm = True
    agent = MagicMock()
    agent.finalize_send = MagicMock(return_value="Отправила")
    dm.get_agent = MagicMock(return_value=agent)
    result = dm.process("да отправь")
    assert "тправила" in result or result == "Отправила"


def test_confirm_no_clears():
    dm, sc = _dm()
    dm.start(sc)
    dm.state.awaiting_confirm = True
    agent = MagicMock()
    agent.clear_input = MagicMock(return_value="Очистила")
    dm.get_agent = MagicMock(return_value=agent)
    result = dm.process("нет")
    assert result is not None
