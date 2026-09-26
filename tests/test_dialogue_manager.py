"""Тесты DialogueManager (ADR-013)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aura.dialogue_manager import (
    DialogueManager,
    Scenario,
    SCENARIOS,
    TIMEOUT_SEC,
)


def _dm():
    agent = MagicMock()
    agent.find_chat.return_value = "🌐 Открыла чат Петруха"
    agent.send_message.return_value = "🌐 Ввела текст"
    agent.finalize_send.return_value = "🌐 Отправила"
    agent.clear_input.return_value = "🌐 Очистила"

    def get_agent(name):
        return agent if name == "messenger" else None

    return DialogueManager(SCENARIOS, get_agent), agent


# --- detect ---

def test_detect_messenger_send():
    dm, _ = _dm()
    s = dm.detect("напиши Петруха привет")
    assert s is not None
    assert s.name == "messenger_send"


def test_detect_none():
    dm, _ = _dm()
    assert dm.detect("который час") is None


# --- start / is_active ---

def test_start_active():
    dm, _ = _dm()
    dm.start(SCENARIOS[0])
    assert dm.is_active() is True


def test_reset():
    dm, _ = _dm()
    dm.start(SCENARIOS[0])
    dm.reset()
    assert dm.is_active() is False


def test_timeout():
    dm, _ = _dm()
    dm.start(SCENARIOS[0])
    dm.state.started_at = 0  # давно
    assert dm.is_active() is False


# --- process: полный сценарий ---

def test_process_not_active():
    dm, _ = _dm()
    assert dm.process("что-то") is None


def test_process_full_scenario():
    """«напиши Петруха привет» → всё в одной фразе."""
    dm, agent = _dm()
    dm.start(SCENARIOS[0])

    # Все слоты в одной фразе.
    resp = dm.process("напиши Петруха привет")
    assert "Отправить?" in resp
    assert "привет" in resp
    agent.find_chat.assert_called_once_with("Петруха")
    agent.send_message.assert_called_once_with("Петруха", "привет")


def test_process_missing_text():
    """Только чат — спросит текст."""
    dm, _ = _dm()
    dm.start(SCENARIOS[0])

    resp = dm.process("Петруха")
    # chat=Петруха распознается, text не найден
    assert resp is not None


def test_process_confirm_yes():
    dm, agent = _dm()
    dm.start(SCENARIOS[0])
    dm.process("напиши Петруха привет")
    resp = dm.process("да")
    assert "Отправила" in resp
    agent.finalize_send.assert_called_once()


def test_process_confirm_no():
    dm, agent = _dm()
    dm.start(SCENARIOS[0])
    dm.process("напиши Петруха привет")
    resp = dm.process("нет")
    assert "Отменила" in resp
    agent.clear_input.assert_called_once()


def test_process_cancel():
    dm, _ = _dm()
    dm.start(SCENARIOS[0])
    resp = dm.process("отмена")
    assert "Отменила" in resp
    assert dm.is_active() is False


def test_process_confirm_garbage():
    dm, _ = _dm()
    dm.start(SCENARIOS[0])
    dm.process("напиши Петруха привет")
    resp = dm.process("не знаю")
    assert "да" in resp.lower() or "нет" in resp.lower()
